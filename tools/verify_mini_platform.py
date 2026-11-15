"""Compile MINI platform fragments and check them offline; never access a device."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from dot_machine import DotMachine
from pi32v2isa import codec, table

SNAPSHOT_FIELDS = ("sys_div clk_con0 clk_con1 clk_con2 pll_con0 pll_con1 pll2_con0 pll2_con1 "
                   "husb_con0 husb_con2 sfc_con sfc_baud cache_con cache_dways cache_iways sdram_con psram_con").split()
SNAPSHOT_ADDRESSES = (0x10008, 0x1000c, 0x10010, 0x10014, 0x119a0, 0x119a4, 0x119a8, 0x119ac,
                      0x16a00, 0x16a08, 0x40200, 0x40204, 0x1eee008, 0x1eee00c, 0x1eee010, 0x40400, 0x40500)


class Snapshot(c.Structure):
    _fields_ = [(name, c.c_uint32) for name in SNAPSHOT_FIELDS]


class Nominal(c.Structure):
    _fields_ = [(name, c.c_uint32) for name in
               "oscillator_hz pll2_hz sys_hz hsb_hz lsb_hz sfc_hz sdram_hz sys_selector main_selector alnk_mux".split()]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def decode(app, start, end):
    offset = start - 0x02000120 if start >= 0x02000120 else 0x0206ed20 - 0x02000120 + start - 0x01c00000
    raw, cursor, code = app[offset:offset + end - start], 0, {}
    isa = table.load()
    while cursor < len(raw):
        decoded = codec.decode(isa, raw, cursor)
        check(decoded is not None, f"unsupported platform instruction {start + cursor:#x}")
        instruction, fields, size = decoded
        then = otherwise = 0
        if instruction.block:
            check("then" in instruction.block, "unexpected loop in clock fragment")
            def count(kind):
                key = instruction.block[kind]
                field = instruction.fields[key]
                return fields[key] * field.scale + field.add
            then, otherwise = count("then"), count("else")
        code[start + cursor] = codec.format(instruction, fields), size, then, otherwise
        cursor += size
    return SimpleNamespace(start=start, end=end, code=code, raw=raw)


class StockClockMachine(DotMachine):
    """Execute only MINI 0x02002d76..2ec8, using supplied register snapshots.

    No physical peripheral model. Clock changes after 2ec8 are excluded. The
    parallel B operation reads the old registers, as documented by the ISA
    compiler audit; predicate then/else spans come from the decoder fields.
    """
    def __init__(self, program, app, snapshot):
        self.program, self.app = program, app
        self.memory, self.regs = {}, {f"r{i}": 0 for i in range(16)}
        self.pc, self.steps, self.carry = program.start, 0, 0
        self.skip_else = {}
        for name, address in zip(SNAPSHOT_FIELDS, SNAPSHOT_ADDRESSES):
            self.write(address, getattr(snapshot, name), 4)

    def read(self, address, width):
        if 0x02000120 <= address and address + width <= 0x02000120 + len(self.app):
            offset = address - 0x02000120
            return int.from_bytes(self.app[offset:offset + width], "little")
        return super().read(address, width)

    def groups_end(self, pc, count):
        for _ in range(count):
            text, size, _, _ = self.program.code[pc]
            pc += size
            if text.endswith("  #"):
                pc += self.program.code[pc][1]
        return pc

    def single(self):
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        match = re.fullmatch(r"if \((r\d+) (==|!=|<=|>=|<|>) (r\d+|\d+)\) \{", text)
        if match:
            a, b = self.value(match[1]), self.value(match[3])
            condition = {"==": a == b, "!=": a != b, "<=": a <= b, ">=": a >= b,
                         "<": a < b, ">": a > b}[match[2]]
            then_start = self.pc + size
            else_start = self.groups_end(then_start, then)
            end = self.groups_end(else_start, otherwise)
            if condition:
                if otherwise:
                    self.skip_else[else_start] = end
                self.pc = then_start
            else:
                self.pc = else_start
            return
        if match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(u\)", text):
            self.set(match[1], self.value(match[2]) // self.value(match[3]))
        elif match := re.fullmatch(r"(r\d+) = uextra\((r\d+), p:(\d+), l:(\d+)\)", text):
            self.set(match[1], (self.value(match[2]) >> int(match[3])) & ((1 << int(match[4])) - 1))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) & (0x[0-9a-fA-F]+)", text):
            self.set(match[1], self.value(match[2]) & int(match[3], 0))
        elif match := re.fullmatch(r"(r\d+) &= (r\d+)", text):
            self.set(match[1], self.value(match[1]) & self.value(match[2]))
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \(u\)", text):
            self.set(match[1], self.read(self.address(match[2]), 1))
        elif match := re.fullmatch(r"b\[(.+)\] = (r\d+)", text):
            self.write(self.address(match[1]), self.value(match[2]), 1)
        else:
            super().step()
            return
        self.pc += size

    def run(self):
        while self.pc != self.program.end:
            if self.pc in self.skip_else:
                self.pc = self.skip_else.pop(self.pc)
                continue
            check(self.pc in self.program.code and self.steps < 200, "clock interpreter escaped")
            text, size, _, _ = self.program.code[self.pc]
            if text.endswith("  #"):
                original, first_pc = dict(self.regs), self.pc
                self.single()
                first = dict(self.regs)
                self.regs = dict(original)
                self.pc = first_pc + size
                second_text = self.program.code[self.pc][0]
                check(not second_text.endswith("  #"), "nested parallel instruction")
                self.single()
                for register, value in first.items():
                    if value != original[register]:
                        check(self.regs[register] == original[register], "parallel register write collision")
                        self.regs[register] = value
            else:
                self.single()
            self.steps += 1
        return {"sys_hz": self.read(0x01c1e32c, 4), "hsb_hz": self.read(0x01c1e338, 4),
                "lsb_hz": self.read(0x01c1e334, 4), "sdram_hz": self.read(0x01c1e340, 4),
                "pll2_hz": self.regs["r13"]}


def evidence():
    package = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
    checksum = sha(package)
    check(checksum == "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209", "MINI firmware hash")
    _, files = unpack_fwsc(package)
    _, _, app_files = unpack_app(files["flash.bin"][0x4000:0x82000])
    app = app_files["app.bin"]
    check(app == (ROOT / "analysis/tank-mini/app.bin").read_bytes(), "decoded MINI differs")
    regions = {
        "watchdog_feed": (0x02000974, 0x0200098a),
        "watchdog_write": (0x02002b88, 0x02002b96),
        "watchdog_setup": (0x02002d42, 0x02002d6c),
        "p33_byte": (0x01c00fc8, 0x01c00fe2),
        "p33_write": (0x01c0104e, 0x01c0108c),
        "p33_or": (0x01c010b4, 0x01c010fe),
        "cache_flush_invalidate": (0x01c00d80, 0x01c00db2),
        "cache_global_maintenance_not_ported": (0x01c00db2, 0x01c00e8c),
        "cache_partition_init": (0x01c00e8c, 0x01c00f9c),
        "clock_read_decode": (0x02002d76, 0x02002ec8),
        "clock_switch_sfc_guard": (0x01c03352, 0x01c033ec),
    }
    fingerprints = {}
    for name, (start, end) in regions.items():
        offset = start - 0x02000120 if start >= 0x02000120 else 0x6ec00 + start - 0x01c00000
        fingerprints[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": sha(app[offset:offset + end - start])}
    byte_program = decode(app, *regions["p33_byte"])
    check([instruction[0] for instruction in byte_program.code.values()] == [
        "r1 = 81416", "[r1+4] = r0", "[r1+0] |= 0x10", "csync", "r0 = [r1+0]",
        "if ((r0 & 2) != 0) goto -6", "r0 = [r1+4]", "r0 = r0.b0 (u)", "rts"], "P33 byte sequence changed")
    offset = 0x0203b6d0 - 0x02000120
    check(app[offset + 66:offset + 74] == bytes((1,3,5,7,1,2,4,8)), "clock divider table changed")
    check(struct.unpack_from("<4I", app, offset + 1272) == (137000000,320000000,480000000,107000000), "clock source table changed")
    # Decode the setup itself; its calls are to the separately identified
    # write-control / OR-control / P33-OR wrappers, not executed SDK code.
    commands, registers = [], {}
    for pc, (text, size, _, _) in decode(app, *regions["watchdog_setup"]).code.items():
        if match := re.fullmatch(r"(r\d+) = (\d+)", text):
            registers[match[1]] = int(match[2])
        elif match := re.fullmatch(r"call (-?\d+)", text):
            destination = pc + size + int(match[1])
            check(destination in (0x02002b88, 0x02000974, 0x01c010b4), "unexpected WDT setup callee")
            commands.append([0 if destination == 0x02002b88 else 0x20,
                             registers["r0"] if destination == 0x01c010b4 else 0x80,
                             registers["r1"] if destination == 0x01c010b4 else registers["r0"]])
        else:
            raise ValueError("unknown watchdog setup instruction: " + text)
    check(commands == [[0,128,0], [0,128,12], [32,128,32], [32,128,64], [32,23,64], [32,128,16]],
          "stock watchdog setup command order changed")
    return app, {"stock_sha256": checksum, "application_sha256": sha(app), "native_fragments": fingerprints,
                 "watchdog_setup_commands_decoded": commands}


def clock_tests(library, app):
    lib = c.CDLL(str(library))
    lib.hyperrig_mini_clock_decode.argtypes = [c.POINTER(Snapshot), c.POINTER(Nominal)]
    lib.hyperrig_mini_clock_decode.restype = c.c_int
    program = decode(app, 0x02002d76, 0x02002ec8)
    rng, digest, count = random.Random(0x504c4154), hashlib.sha256(), 0
    for selector in range(10):
        for odd_index in range(4):
            for shift_index in range(4):
                for crystal_mode in range(4):
                    s = Snapshot(*[rng.getrandbits(32) for _ in SNAPSHOT_FIELDS])
                    s.clk_con2 = (s.clk_con2 & ~255) | selector | (odd_index << 4) | (shift_index << 6)
                    s.pll_con0 = (s.pll_con0 & ~0x0c000000) | (crystal_mode << 26)
                    s.sfc_baud = rng.randrange(16)
                    n = Nominal()
                    check(lib.hyperrig_mini_clock_decode(c.byref(s), c.byref(n)) == 0, "clock decode rejected supported source")
                    expected = StockClockMachine(program, app, s).run()
                    for field, value in expected.items():
                        check(getattr(n, field) == value, f"stock clock mismatch selector{selector} {field}: {getattr(n, field)} != {value}")
                    check(n.sfc_hz == expected["hsb_hz"] // (s.sfc_baud + 1), "SFC clock divisor")
                    check(n.oscillator_hz == (40000000 if crystal_mode == 2 else 24000000), "oscillator field")
                    check(n.sys_selector == selector and n.main_selector == (s.clk_con0 >> 6) & 7, "source reporting")
                    check(n.alnk_mux == s.clk_con2 & 0xf00, "ALNK mux reporting")
                    digest.update(bytes(n))
                    count += 1
    for selector in range(10, 16):
        s = Snapshot(); s.clk_con2 = selector
        n = Nominal(*([0xa5a5a5a5] * 10))
        check(lib.hyperrig_mini_clock_decode(c.byref(s), c.byref(n)) == -4, "unsupported clock selector")
        check(all(getattr(n, name) == 0xa5a5a5a5 for name, _ in n._fields_), "failed decode mutated output")
    return {"clock_instruction_cases": count, "clock_result_sha256": digest.hexdigest(),
            "parallel_issue": "B reads pre-A registers; compiler-established ISA semantics", "hardware_frequency_measured": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-only", action="store_true")
    args = parser.parse_args()
    out = ROOT / "build/mini-platform"
    out.mkdir(parents=True, exist_ok=True)
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    def run(command):
        result = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/mini/platform"]
    source = "firmware/mini/platform/hyperrig_mini_platform.c"
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    if not args.test_only:
        run(["gcc", *common, "-O2", "-shared", "-fPIC", "-fsanitize=undefined", "-fno-sanitize-recover=all",
             source, "-o", "build/mini-platform/libplatform.so"])
        objects = []
        for name in ("hyperrig_mini_platform", "target_io"):
            target = "build/mini-platform/" + name + ".o"
            run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin",
                 "-mllvm", "-pi32v2-large-program",
                 "-c", "firmware/mini/platform/" + name + ".c", "-o", target])
            objects.append(target)
        run([vendor + "ld", "-r", *objects, "-o", "build/mini-platform/hyperrig_mini_platform.pi32v2.o"])
        check(not run([vendor + "nm", "-u", "build/mini-platform/hyperrig_mini_platform.pi32v2.o"]).strip(), "target unresolved symbols")
        assembly = run([vendor + "objdump", "-d", "build/mini-platform/hyperrig_mini_platform.pi32v2.o"])
        (out / "platform.asm").write_text(assembly, encoding="utf-8", newline="\n")
        check("flush [" in assembly and "flushinv [" in assembly and "Disassembly of section .ramtext" in assembly,
              "target cache instructions/RAM section missing")
        run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", source,
             "firmware/mini/platform/test_platform.c", "-o", "build/mini-platform/sanitize"])
        (out / "sanitizers.json").write_text(run(["build/mini-platform/sanitize"]), encoding="utf-8", newline="\n")
        if os.name == "nt":
            print(run(["python3", "tools/verify_mini_platform.py", "--test-only"]), end="")
            return
    app, report = evidence()
    report.update(clock_tests(out / "libplatform.so", app))
    report["sanitizers"] = json.loads((out / "sanitizers.json").read_text())
    report["sanitizers"].update(address_sanitizer=True, undefined_behavior_sanitizer=True)
    target = (out / "hyperrig_mini_platform.pi32v2.o").read_bytes()
    check(target[:6] == b"\x7fELF\x01\x01" and int.from_bytes(target[18:20], "little") == 0xf1, "wrong target ELF")
    report["pi32v2_object_sha256"] = sha(target)
    report["target_codegen_flags"] = ["-mllvm", "-pi32v2-large-program"]
    header = struct.unpack_from("<HHIIIIIHHHHHH", target, 16)
    sections = [struct.unpack_from("<10I", target, header[5] + header[10] * i) for i in range(header[11])]
    strings = sections[header[12]]
    names = target[strings[4]:strings[4] + strings[5]]
    report["allocated_section_bytes"] = {names[s[0]:names.index(0, s[0])].decode(): s[5]
                                          for s in sections if s[2] & 2}
    report["sources_sha256"] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                                for p in sorted((ROOT / "firmware/mini/platform").glob("*.c"))}
    report["sources_sha256"]["firmware/mini/platform/hyperrig_mini_platform.h"] = sha((ROOT / "firmware/mini/platform/hyperrig_mini_platform.h").read_bytes())
    report["verifier_sha256"] = sha(Path(__file__).read_bytes())
    report["sdk_commit"] = "ffbb2a8d925682ba6880d643a83a63ee0691ec09"
    report["sdk_reference_sha256"] = {p.name: sha(p.read_bytes()) for p in sorted((ROOT / "analysis/mini-platform/sdk").glob("*"))}
    report["soc_reference"] = {"repository": "https://github.com/jvitkauskas/m-bootloader",
                                "commit": "3ac7651a019fa44daba061b05654278496477b64",
                                "hardware_scope": "FM1/SMK37 AC791N; not MINI validation",
                                "spec_sha256": sha((ROOT / "upstream/m-bootloader/docs/SPEC.md").read_bytes())}
    report.update(hardware_executed=False, clock_or_sfc_reconfigured=False, dma_coherence_validated=False,
                  watchdog_deadline_measured=False, flashable=False,
                  limitations=["P33 mode and clock inherited; unknown modes rejected", "poll counts are not time units",
                               "cache ownership and MMU mapping require target proof", "copied RAM code instruction visibility not established",
                               "CPU/audio frequencies are not measured",
                               "cache partition and PLL switch code deliberately not called or ported"])
    (ROOT / "research/mini-platform.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"clock_instruction_cases": report["clock_instruction_cases"], "sanitizers": report["sanitizers"]}, indent=2))
    print("MINI platform verified offline; no hardware accessed or clock changed.")


if __name__ == "__main__":
    main()
