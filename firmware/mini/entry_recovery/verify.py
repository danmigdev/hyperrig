"""Offline assembly, instruction-model and pinned-stock audit; no device API.

The instruction model evaluates the assembled bytes and all MMIO stores.
The two exact, side-effect-free delay loops are counted algebraically; this
does not model CPU cycles, cache, interrupts, GPIO voltages or switch bounce.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.audit_mini_boot_contract import instructions, stock_boot
from tools.audit_mini_ultrarig_port import G_PATH, G_SHA, MINI_PATH, MINI_SHA, BACKUP_PATH, BACKUP_SHA
from tools.audit_mini_panel_port import encode
from hyperrig.jieli import unpack_app, unpack_fwsc

BASE, HOOK, RESUME = 0x02078000, 0x0200018A, 0x02000196
SP, SSP = 0x01C350B8, 0x01C360B8
MASK, PORT, MAILBOX, RESET = 0x409, 0x50000, 0x01C7FD80, 0x10000
CONFIG = (PORT+8, PORT+12, PORT+16, PORT+20)
EXPECTED_PREIMAGE = bytes.fromhex("eeffb850c301edffb860c301")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def elf(raw):
    require(raw[:7] == b"\x7fELF\x01\x01\x01", "ELF32LE required")
    h = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    require(h[:4] == (2, 0xF1, 1, BASE) and h[8:11] == (32, 1, 40), "audit ELF header")
    p = struct.unpack_from("<8I", raw, h[4])
    require(p[0] == 1 and p[2] == p[3] == BASE and 0 < p[4] == p[5] < 1024 and p[6] == 5,
            "audit must have one file-backed executable segment without BSS")
    sections = [struct.unpack_from("<10I", raw, h[5]+40*i) for i in range(h[11])]
    symbols = {}
    for section in sections:
        require(not (section[1] == 8 and section[2] & 2 and section[5]), "allocated BSS is forbidden")
        if section[1] != 2:
            continue
        s = sections[section[6]]
        names = raw[s[4]:s[4]+s[5]]
        for off in range(section[4], section[4]+section[5], 16):
            name, value, size, info, other, ndx = struct.unpack_from("<IIIBBH", raw, off)
            label = names[name:names.index(0, name)].decode()
            require(not (ndx == 0 and label), "unresolved symbol: " + label)
            if label:
                symbols[label] = value
    return raw[p[1]:p[1]+p[4]], symbols


class Machine:
    """Narrow interpreter of the emitted scalar instructions, with fake MMIO."""
    def __init__(self, code, symbols, seed, levels, *, prefix=False, fault=None,
                 output_pin=False, change_unrelated=False, sp_alias_ssp=False):
        rng = random.Random(seed)
        self.code, self.symbols = code, symbols
        self.regs = {f"r{i}": rng.getrandbits(32) for i in range(16)}
        self.regs.update(sp=0x01C2FFF0, ssp=0x01C7FC00, psr=rng.getrandbits(32),
                         rets=0x12345678, reti=rng.getrandbits(32))
        self.sp_alias_ssp = sp_alias_ssp
        if sp_alias_ssp:
            self.regs["ssp"] = self.regs["sp"]
        self.original_regs = dict(self.regs)
        self.mmio = {p: rng.getrandbits(32) for p in CONFIG}
        self.mmio[PORT+8] |= MASK
        if output_pin:
            self.mmio[PORT+8] &= ~(1 << (0, 3, 10)[seed % 3])
        self.original_mmio = dict(self.mmio)
        self.reset_word = rng.getrandbits(32)
        self.memory, self.writes, self.reads = {}, [], []
        self.input_levels, self.samples = levels, 0
        self.delay_iterations, self.steps = 0, 0
        self.fault, self.fault_used = fault, False
        self.change_unrelated, self.changed = change_unrelated, False
        self.syncs, self.min_sp = [], self.regs["sp"]
        self.pc = BASE if prefix else symbols["hyperrig_mini_entry_recovery_check"]
        self.prefix = prefix
        self.stack_top = (SSP if sp_alias_ssp else SP) if prefix else self.regs["sp"]

    def set(self, name, value):
        self.regs[name] = value & 0xFFFFFFFF
        if self.sp_alias_ssp and name in ("sp", "ssp"):
            self.regs["sp"] = self.regs["ssp"] = value & 0xFFFFFFFF
            if self.prefix and self.steps <= 1:
                self.min_sp = value & 0xFFFFFFFF
        if name == "sp":
            # SP initialization switches away from the inherited SPL stack.
            self.min_sp = min(self.min_sp, self.regs[name]) if not self.prefix or self.steps else self.regs[name]

    def read(self, address):
        self.reads.append(address)
        if address == PORT+4:
            if self.change_unrelated and not self.changed:
                for p in CONFIG:
                    self.mmio[p] ^= 0x20000000  # outside the three owned bits
                self.changed = True
            value = self.input_levels[min(self.samples, len(self.input_levels)-1)]
            self.samples += 1
            return value
        if address in CONFIG:
            if address == self.fault and not self.fault_used and any(a == PORT+16 for a, _ in self.writes):
                self.fault_used = True
                return self.mmio[address] ^ 1
            return self.mmio[address]
        if address == RESET:
            return self.reset_word
        if address in self.memory:
            return self.memory[address]
        raise ValueError(f"unexpected memory read {address:#x}")

    def write(self, address, value):
        value &= 0xFFFFFFFF
        self.writes.append((address, value))
        if address in CONFIG:
            # Direction remains input for every write, including restoration.
            require(address != PORT+8 or value & MASK == MASK, "guard drives a key as output")
            require(((self.mmio[address] ^ value) & ~MASK) == 0, "unrelated GPIO bits changed")
            self.mmio[address] = value
        elif MAILBOX <= address < MAILBOX+16 and address % 4 == 0:
            self.memory[address] = value
        elif address == RESET:
            require(value == self.reset_word | 16, "reset changes more than stock bit4")
        elif self.stack_top-(100 if self.prefix else 24) <= address < self.stack_top:
            self.memory[address] = value
        else:
            raise ValueError(f"unexpected memory store {address:#x}")

    @staticmethod
    def registers(text):
        names = []
        for item in text.split(", "):
            if m := re.fullmatch(r"r(\d+)-r(\d+)", item):
                names.extend(f"r{i}" for i in range(int(m[1]), int(m[2])-1, -1))
            else:
                names.append(item)
        return names

    def run(self):
        while self.pc not in (RESUME, 0x12345678):
            require(self.pc in self.code and self.steps < 2000, "guard escaped its audited CFG/budget")
            row = self.code[self.pc]
            text, size = row["text"], row["size"]
            next_pc = self.pc+size
            if text == "goto -2":
                return "reset_wait"
            if text == "nop":
                # Accelerate ONLY the two emitted nop/decrement/branch loops.
                following = self.code[next_pc]
                branch = self.code[next_pc+following["size"]]
                require(following["text"] == "r2 += -1" and branch["text"] == "if (r2 != 0) goto -6"
                        and branch["target"] == self.pc and self.regs["r2"] == 100000,
                        "unrecognized delay loop")
                self.delay_iterations += self.regs["r2"]
                self.regs["r2"] = 0
                next_pc = branch["address"]+branch["size"]
            elif text == "csync":
                self.syncs.append(len(self.writes))
            elif text == "rts":
                next_pc = self.regs["rets"]
            elif m := re.fullmatch(r"\[--sp\] = \{(.+)\}", text):
                names = self.registers(m[1])
                self.set("sp", self.regs["sp"]-4*len(names))
                for i, name in enumerate(names):
                    self.write(self.regs["sp"]+4*i, self.regs[name])
            elif m := re.fullmatch(r"\{(.+)\} = \[sp\+\+\]", text):
                names = self.registers(m[1])
                for i, name in enumerate(names):
                    self.set(name, self.read(self.regs["sp"]+4*i))
                self.set("sp", self.regs["sp"]+4*len(names))
            elif m := re.fullmatch(r"(r\d+|sp|ssp) = (0x[0-9a-fA-F]+|-?\d+)", text):
                self.set(m[1], int(m[2], 0))
            elif m := re.fullmatch(r"(r\d+) = (r\d+)", text):
                self.set(m[1], self.regs[m[2]])
            elif m := re.fullmatch(r"(r\d+) = ~(r\d+)", text):
                self.set(m[1], ~self.regs[m[2]])
            elif m := re.fullmatch(r"(r\d+) ([&|+])= (r\d+|-?\d+)", text):
                a, b = self.regs[m[1]], self.regs[m[3]] if m[3].startswith("r") else int(m[3])
                self.set(m[1], a & b if m[2] == "&" else a | b if m[2] == "|" else a+b)
            elif m := re.fullmatch(r"(r\d+) = (r\d+) ([&|]) (r\d+)", text):
                a, b = self.regs[m[2]], self.regs[m[4]]
                self.set(m[1], a & b if m[3] == "&" else a | b)
            elif m := re.fullmatch(r"(r\d+) = \[(r\d+)\+(\d+)\]", text):
                self.set(m[1], self.read(self.regs[m[2]]+int(m[3])))
            elif m := re.fullmatch(r"\[(r\d+)\+(\d+)\] = (r\d+)", text):
                self.write(self.regs[m[1]]+int(m[2]), self.regs[m[3]])
            elif m := re.fullmatch(r"if \((r\d+) (==|!=) (r\d+|\d+)\) goto -?\d+", text):
                right = self.regs[m[3]] if m[3].startswith("r") else int(m[3])
                if (self.regs[m[1]] == right) == (m[2] == "=="):
                    next_pc = row["target"]
            elif text.startswith("call "):
                self.regs["rets"] = next_pc
                next_pc = row["target"]
            elif text.startswith("goto "):
                next_pc = row["target"]
            else:
                raise ValueError(f"unsupported emitted instruction {self.pc:#x}: {text}")
            self.pc = next_pc
            self.steps += 1
        return "startup_resume" if self.pc == RESUME else "returned"

    def check_gpio_restore(self):
        for address, value in self.original_mmio.items():
            expected = value ^ (0x20000000 if self.changed else 0)
            require(self.mmio[address] == expected, "GPIO restore mismatch")


def self_check(code, symbols):
    cases, max_stack, max_steps = 0, 0, 0
    for prefix, alias in ((False, False), (False, True), (True, False), (True, True)):
        for seed in range(16):
            for bits in range(8):
                levels = sum(((bits >> i) & 1) << pin for i, pin in enumerate((0, 3, 10))) | 0xA5000000
                machine = Machine(code, symbols, seed, [levels], prefix=prefix,
                                  change_unrelated=True, sp_alias_ssp=alias)
                result = machine.run()
                held = bits == 0
                require(result == ("reset_wait" if prefix and held else "startup_resume" if prefix else "returned"), "wrong guard outcome")
                machine.check_gpio_restore()
                if held:
                    require(machine.samples == 32 and machine.delay_iterations == 3300000, "held sample/loop counts")
                else:
                    require(machine.samples == 1 and machine.delay_iterations == 100000, "no-key fast return")
                if prefix and held:
                    marker = b"".join(struct.pack("<I", machine.memory[MAILBOX+i]) for i in range(0, 16, 4))
                    require(marker == b"usb_update_mode\0", "ROM marker differs")
                    require(machine.writes[-1] == (RESET, machine.reset_word | 16), "reset store order")
                    require(machine.syncs[-2:] == [len(machine.writes)-1, len(machine.writes)], "marker/reset ordering barriers")
                elif prefix:
                    for name in list(f"r{i}" for i in range(16))+["psr", "rets", "reti"]:
                        require(machine.regs[name] == machine.original_regs[name], "prefix register changed: " + name)
                    require((machine.regs["sp"], machine.regs["ssp"]) == (SSP if alias else SP, SSP), "G stack setup not reproduced")
                else:
                    require(machine.regs["r0"] == int(held), "callable result")
                    for name in [*(f"r{i}" for i in range(4, 16)), "rets", "sp", "ssp"]:
                        require(machine.regs[name] == machine.original_regs[name], "callee-saved register changed")
                if not (prefix and held):
                    require(not any(MAILBOX <= a < MAILBOX+16 or a == RESET for a, _ in machine.writes), "unexpected recovery side effect")
                max_stack = max(max_stack, machine.stack_top-machine.min_sp)
                max_steps = max(max_steps, machine.steps)
                cases += 1
    # A single released sample at any point rejects the chord, regardless of
    # the earlier LOW samples. No continuous-time debounce is claimed.
    for position in range(32):
        for pin in (0, 3, 10):
            machine = Machine(code, symbols, position, [0]*position+[1 << pin]+[0]*32, prefix=True)
            require(machine.run() == "startup_resume" and machine.samples == position+1, "bounce accepted")
            machine.check_gpio_restore()
            cases += 1
    for fault in CONFIG:
        machine = Machine(code, symbols, 11, [0], fault=fault)
        require(machine.run() == "returned" and machine.regs["r0"] == 2 and machine.samples == 0, "configuration readback fault")
        machine.check_gpio_restore()
        cases += 1
    for seed in range(24):
        machine = Machine(code, symbols, seed, [0], output_pin=True)
        require(machine.run() == "returned" and machine.regs["r0"] == 2 and machine.samples == 0, "initial output line accepted")
        require(not any(a in CONFIG for a, _ in machine.writes), "initial output direction touched")
        machine.check_gpio_restore()
        cases += 1
    return {"cases": cases, "maximum_stack_bytes": max_stack, "maximum_modeled_steps": max_steps,
            "maximum_delay_loop_iterations": 3300000, "delay_loop_method": "exact nop/decrement/branch loop counted algebraically",
            "push_pop_model": "matched saved-register frames; byte counts checked, physical stack ordering not independently executed",
            "active_SP_alias_cases": ["SP independent of explicit SSP", "SP aliases SSP"],
            "hardware_timing_or_electrical_simulation": False}


def main():
    out = ROOT / "build/mini-entry-recovery"
    out.mkdir(parents=True, exist_ok=True)
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    def run(args):
        r = subprocess.run(prefix+args, cwd=ROOT, capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise RuntimeError(r.stdout+r.stderr)
        return r.stdout
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    objects = []
    for name in ("check", "reset", "prefix"):
        obj = f"build/mini-entry-recovery/{name}.o"
        run([vendor+"clang", "-target", "pi32v2", "-mcpu=r3", "-c",
             f"firmware/mini/entry_recovery/{name}.S", "-o", obj])
        objects.append(obj)
    target = "build/mini-entry-recovery/entry-recovery-audit.elf"
    run([vendor+"ld", "-z", "max-page-size=0x20", "-z", "common-page-size=0x20",
         "-T", "firmware/mini/entry_recovery/audit.ld", *objects, "-o", target])
    raw = (ROOT / target).read_bytes()
    data, symbols = elf(raw)
    rows = instructions(data, BASE, BASE, BASE+len(data))
    code = {r["address"]: r for r in rows}
    require(data[:12] == EXPECTED_PREIMAGE and symbols["hyperrig_mini_g_startup_resume"] == RESUME, "prefix/resume ABI")
    tests = self_check(code, symbols)
    (out / "entry-recovery-audit.asm").write_text(run([vendor+"objdump", "-d", target]), encoding="utf-8")

    g_raw, m_raw, backup = (ROOT / G_PATH).read_bytes(), (ROOT / MINI_PATH).read_bytes(), (ROOT / BACKUP_PATH).read_bytes()
    require((sha(g_raw), sha(m_raw), sha(backup)) == (G_SHA, MINI_SHA, BACKUP_SHA), "pinned input changed")
    g, _, _ = unpack_app(g_raw)
    _, files = unpack_fwsc(m_raw)
    mini, _, _ = unpack_app(files["flash.bin"][0x4000:])
    boot, _ = stock_boot(backup)
    require(g[HOOK-0x02000000:RESUME-0x02000000] == EXPECTED_PREIMAGE, "G stack preimage changed")
    require(g[0x120:0x122] == bytes.fromhex("1494"), "G entry short branch changed")
    require(mini[0x3FD2A:0x3FD3A] == boot[0x3710:0x3720] == b"usb_update_mode\0", "stock marker changed")
    proposed_hook = encode("goto.l", n=(BASE-(HOOK+4))//2) + bytes(8)
    hook_rows = instructions(proposed_hook, HOOK, HOOK, RESUME)
    require(hook_rows[0]["target"] == BASE and all(r["text"] == "nop" for r in hook_rows[1:]), "proposed trampoline bytes")
    # The audit composes no application and emits no firmware or RAM plugin.
    report = {
        "schema": 1, "status": "offline_prefix_verified_hardware_unqualified",
        "device_access": False, "NVM_access": False, "candidate_modified": False,
        "flashable": False, "recovery_qualified": False,
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(Path(__file__).parent.iterdir()) if p.is_file()},
        "inputs": {G_PATH: G_SHA, MINI_PATH: MINI_SHA, BACKUP_PATH: BACKUP_SHA},
        "component": {"elf": target, "elf_sha256": sha(raw), "load_bytes": len(data),
                      "audit_link_base_not_allocation": BASE, "symbols": symbols,
                      "BSS_bytes": 0, "initialized_RAM_bytes": 0, "stack_bytes_callable": 24,
                      "stack_bytes_prefix": 100,
                      "possible_stack_ranges_prefix": [[SP-100, SP], [SSP-100, SSP]],
                      "active_SP_alias_physical_unmeasured": True,
                      "instructions": rows},
        "proposed_hook_not_applied": {"address": HOOK, "end_exclusive": RESUME,
                                      "before_hex": EXPECTED_PREIMAGE.hex(), "after_hex_at_audit_base": proposed_hook.hex(),
                                      "entry_02000120_unchanged": True, "instruction_rows": hook_rows,
                                      "resume": RESUME, "all_GPR_psr_rets_reti_preserved_on_continue": True},
        "gpio_policy": {"port_base": PORT, "mask": MASK, "pins": ["PA10", "PA0", "PA3"],
                        "chord": "all three active-low footswitch inputs", "label_order_required": False,
                        "initial_direction_requires_input": True, "readback_configuration_checked": True,
                        "owned_registers": {"DIR": PORT+8, "DIE": PORT+12, "PU": PORT+16, "PD": PORT+20},
                        "OUT_DIEH_drive_mux_written": False, "restores_selected_fields_on_every_return": True,
                        "samples_required_low": 32, "settle_iterations": 100000,
                        "iterations_after_each_low_sample": 100000, "physical_debounce_time_proven": False},
        "reset_policy": {"marker_address": MAILBOX, "marker_hex": b"usb_update_mode\0".hex(),
                         "reset_register": RESET, "OR_mask": 16, "barriers_before_and_after_reset_store": "csync",
                         "ROM_function_jump": False, "watchdog_modified": False},
        "pinned_stock_evidence": {
            "G_entry": instructions(g, 0x02000000, 0x02000120, 0x02000122),
            "G_stack_and_first_call": instructions(g, 0x02000000, HOOK, 0x0200019C),
            "MINI_key_init": instructions(mini, 0x02000000, 0x02006096, 0x020060BA),
            "MINI_key_read": instructions(mini, 0x02000000, 0x0200A060, 0x0200A080),
            "SPL_interrupt_disable": instructions(boot, 0x01C02000, 0x01C051C2, 0x01C051CC),
            "SPL_app_call": instructions(boot, 0x01C02000, 0x01C05284, 0x01C0528E),
            "SPL_reset": instructions(boot, 0x01C02000, 0x01C028F4, 0x01C028FE),
            "SPL_marker_copy": instructions(boot, 0x01C02000, 0x01C0529A, 0x01C052A8),
            "GPIO_layout_header": "upstream/ac79-sdk-reference/include_lib/driver/cpu/wl82/asm/WL82.h",
        },
        "verification": tests,
        "coverage": {
            "valid_app_hang_after_guard": "conditional: power cycle with chord held and intact SPL/app/header/guard",
            "app_header_or_entry_corruption": False, "interrupted_NOR_update": False,
            "SPL_or_ROM_failure": False, "physical_GPIO_fault": False,
            "cold_power_on_state_measured": False, "new_marker_reset_path_tested_in_RAM": False,
        },
        "qualification_before_relying_on_guard": [
            "RAM check-only plugin: released, each single, each pair, all three; verify raw levels and exact GPIO restoration",
            "Explicit RAM command invoking this marker/reset body; require fresh WL82 ROM enumeration, then verified return to stock",
            "Validate inherited input direction and GPIO settling at cold SPL-to-app handover; ROM callback state alone is not that state",
            "Integrate prefix only at validated preimage, allocate inside app.bin, rebuild all CRCs/encryption and verify full readback",
            "Keep SPL, staged OTA, complete backup and user-data regions; these remain separate recovery gates",
        ],
    }
    report_path = ROOT / "research/mini-entry-recovery.json"
    report_path.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "bytes": len(data), "cases": tests["cases"],
                      "stack_bytes": tests["maximum_stack_bytes"], "device_access": False,
                      "report": report_path.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
