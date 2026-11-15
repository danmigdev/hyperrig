"""Offline G->MINI boot, clock, calibration and recovery contract.

Reads pinned application/package/backup bytes. Does not access a device, run
an updater or write a candidate. The one optional binary patch changes only
G's private copies of absent boot extensions, never the MINI SPL/mailbox.
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
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from tools.audit_mini_ultrarig_port import (
    BinaryPatch, G_PATH, MINI_PATH, BACKUP_PATH, BACKUP_SHA, BOOT_SHA,
    pinned_inputs, inspect_vm_geometry, audit_installer, require, sha,
)
from hyperrig.jieli import crc16, enc, jlfs_entry, unpack_fwsc
from pi32v2isa import codec, table
from tools.dot_machine import DotMachine

BASE, BOOT_BASE = 0x02000000, 0x01C02000
CONTEXT, PRIVATE = 0x01C7FE08, 0x01C7FD4C
G_PLAIN_SHA = "2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334"
EXTENSION_PATCH = BinaryPatch(
    "mini_absent_boot_extensions", 0x0200045C,
    bytes.fromhex("01e15040c0ff74fdc7014228618101e15840c0ff7cfdc7014224519a"),
    bytes.fromhex("c0ff74fdc7014120816081618162") + bytes(14),
    "MINI has no SDRAM or secondary application. Initialize G's private "
    "SDRAM_CFG_INFO/EX_APP_INFO to zero instead of copying unspecified "
    "incoming boot-context bytes+80..91. Preserve core boot info and mailbox.")


def instructions(raw, base, start, end):
    require(base <= start <= end <= base + len(raw), "fragment bounds")
    isa, rows, pc = table.load(), [], start
    while pc < end:
        result = codec.decode(isa, raw, pc - base)
        require(result is not None, f"unknown instruction at {pc:#x}")
        ins, fields, size = result
        require(pc + size <= end, "fragment splits instruction")
        text = codec.format(ins, fields)
        row = {"address": pc, "size": size, "id": ins.id, "fields": fields,
               "text": text, "bytes": raw[pc-base:pc-base+size].hex()}
        branch = re.search(r"\b(?:call|goto) (-?\d+)$", text)
        if branch:
            row["target"] = pc + size + int(branch[1])
        rows.append(row)
        pc += size
    return rows


def fragment(raw, base, start, end):
    return {"start": start, "end_exclusive": end,
            "sha256": sha(raw[start-base:end-base]),
            "instructions": instructions(raw, base, start, end)}


def boot_patches(g_plain: bytes) -> tuple[BinaryPatch, ...]:
    """Reusable formatter input; validates original G, returns no new image."""
    require(sha(g_plain) == G_PLAIN_SHA, "boot patch source is not pinned original G")
    patch = EXTENSION_PATCH
    off = patch.address - BASE
    require(g_plain[off:off+len(patch.before)] == patch.before, "boot extension preimage")
    return (patch,)


def stock_boot(flash):
    entries = {e.name: e for e in (jlfs_entry(enc(flash[o:o+32]), 0)
                                  for o in range(32, 160, 32))}
    entry = entries["uboot.boot"]
    require((entry.offset, entry.size) == (0xA0, 0x3830), "SPL directory geometry")
    container = enc(flash[entry.offset:entry.offset+16]) + enc(flash[entry.offset+16:entry.offset+entry.size])
    banks, length, address, offset, dc, hc = struct.unpack_from("<HHIIHH", container)
    require((banks, length, address, offset) == (1, 0x3820, BOOT_BASE, 16), "SPL BANKCB")
    payload = container[16:]
    require(crc16(container[:14]) == hc and crc16(payload) == dc and
            crc16(container) == entry.data_crc and sha(payload) == BOOT_SHA, "SPL integrity")
    entry = entries["isd_config.ini"]
    config = flash[entry.offset:entry.offset+entry.size]
    require(crc16(config) == entry.data_crc, "configuration CRC")
    values, p = {}, 34
    while p < len(config):
        n = config[p]
        p += 1
        if n in (0, 255):
            break
        end = config.index(0, p)
        name, p = config[p:end].decode("ascii"), end + 1
        require(p + n <= len(config) and name not in values, "configuration record")
        values[name], p = config[p:p+n], p+n
    require(values["ENABLE_SDRAM"] == bytes(4) and values["UPDATE_JUMP"] == bytes(4),
            "unsupported MINI boot profile")
    return payload, values


class GetterMachine(DotMachine):
    """Original leaf getter instructions; MMIO reads are supplied test words."""
    def __init__(self, rows, flag, cached, mux, pll):
        self.program = SimpleNamespace(code={r["address"]: (r["text"], r["size"], 0, 0) for r in rows})
        self.pc = rows[0]["address"]
        self.regs = {f"r{i}": 0xBADC0000+i for i in range(16)}
        self.memory, self.carry = {}, 0
        self.reads = []
        for address, value, width in ((0x01C26890+680, flag, 1), (0x01C1F1AC, cached, 4),
                                      (0x10014, mux, 4), (0x119AC, pll, 4)):
            DotMachine.write(self, address, value, width)

    def write(self, *_):
        raise ValueError("clock getter unexpectedly writes memory")

    def read(self, address, width):
        self.reads.append((address, width))
        return super().read(address, width)

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        if text == "rts":
            return False
        if m := re.fullmatch(r"(r\d+) = b\[(r\d+)\+(r\d+)\] \(u\)", text):
            self.set(m[1], self.read(self.value(m[2])+self.value(m[3]), 1))
        elif m := re.fullmatch(r"(r\d+) &= (r\d+)", text):
            self.set(m[1], self.value(m[1]) & self.value(m[2]))
        elif m := re.fullmatch(r"(r\d+) = (r\d+) & (0x[0-9A-Fa-f]+)", text):
            self.set(m[1], self.value(m[2]) & int(m[3], 16))
        elif m := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(u\)", text):
            require(self.value(m[3]) != 0, "getter divide by zero")
            self.set(m[1], self.value(m[2]) // self.value(m[3]))
        else:
            return super().step()
        self.pc += size
        return True

    def run(self):
        for _ in range(32):
            require(self.pc in self.program.code, "getter escaped verified fragment")
            if not self.step():
                return self.regs["r0"]
        raise ValueError("getter instruction budget")


def audit_clock(gp):
    rows = instructions(gp, BASE, 0x020057C6, 0x0200580C)
    cases = 0
    for flag in (0, 1, 255):
        for cached in (0, 120, 396, 0xFFFFFFFF):
            for mux in range(16):
                for pll in (0, 1, 268, 295, 0xFFF, 0x80000268, 0xFFFFFFFF):
                    machine = GetterMachine(rows, flag, cached, mux | 0x500, pll)
                    expected = cached if flag else (((pll & 0xFFF)*4+8)//3 if mux == 6 else 0)
                    require(machine.run() == expected, "original getter result differs")
                    require(all(machine.regs[f"r{i}"] == 0xBADC0000+i for i in range(2, 16)),
                            "getter changed a register outside r0/r1")
                    cases += 1
    initial = struct.unpack_from("<I", gp, 0x7592C)[0]
    require(initial == 396, "initial clock policy value changed")
    gram = gp[0x56780:0x76A8C]
    return {
        "getter": fragment(gp, BASE, 0x020057C6, 0x0200580C),
        "normal_call_abi": "No arguments; r0 returns unsigned nominal MHz; r1 clobbered; no lock or write.",
        "formula": "flag680 ? cached_MHz : (CLK_CON2&15)==6 ? (((PLL_NR&4095)*4+8)/3) : 0",
        "initialized_cache": {"vma": 0x01C1F1AC, "lma": 0x0207592C, "mhz": initial},
        "setter": {"entry": 0x020054F0, "cache_stores": [0x0200557E, 0x0200577C],
                   "physical_transition_call": 0x0200566A, "physical_transition_target": 0x01C0444E,
                   "enable_cached_result": 0x020057B6,
                   "whole_transaction_serialization_proven": False},
        "getter_instruction_cases": cases,
        "clock_measurement": False,
        "gpio_critical_enter": fragment(gram, 0x01C00000, 0x01C00E2E, 0x01C00E46),
        "gpio_critical_exit": fragment(gram, 0x01C00000, 0x01C00E46, 0x01C00E62),
        "gpio_bank_lock_address": 0x01C25CE0,
        "integration": ["Multiply nonzero MHz by 1000000 after checking <=2147 for signed-Hz delay arithmetic.",
                        "Use G GPIO helpers; do not recursively acquire their bank spinlock.",
                        "Require PA1/2 ownership and stable clocks for the complete codec transaction."]}


def elf_text(raw):
    require(raw[:7] == b"\x7fELF\x01\x01\x01", "assembler ELF32LE")
    h = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    require(h[1] == 0xF1 and h[10] == 40, "assembler machine/section size")
    sections = [struct.unpack_from("<10I", raw, h[5]+40*i) for i in range(h[11])]
    strings = sections[h[12]]
    names = raw[strings[4]:strings[4]+strings[5]]
    for s in sections:
        require(s[1] != 4 or s[5] == 0, "boot extension patch relocation")
        if names[s[0]:names.index(0, s[0])] == b".text":
            return raw[s[4]:s[4]+s[5]]
    raise ValueError("assembler missing .text")


def verify_patch(out):
    p = EXTENSION_PATCH
    rows = instructions(p.after, p.address, p.address, p.address+len(p.after))
    expected = ["r0 = 29883764", "r1 = 0", "[r0+0] = r1", "[r0+4] = r1", "[r0+8] = r1"] + ["nop"]*7
    require([r["text"] for r in rows] == expected and len(p.before) == len(p.after) == 28,
            "extension patch instruction contract")
    rng = random.Random(0xC7FD74)
    for _ in range(64):
        memory = {a: rng.randrange(256) for a in range(PRIVATE, CONTEXT+96)}
        before = dict(memory)
        regs = [rng.getrandbits(32) for _ in range(16)]
        saved = regs[:]
        stores = []
        for row in rows:
            f = row["fields"]
            if row["id"].startswith("li."):
                regs[f["r"]] = f["n"]
            elif row["id"] == "st.w":
                a = regs[f["b"]] + 4*f["n"]
                stores.append(a)
                for i, byte in enumerate(struct.pack("<I", regs[f["d"]])):
                    memory[a+i] = byte
            else:
                require(row["id"] == "nop", "unexpected patch side effect")
        require(stores == [PRIVATE+40, PRIVATE+44, PRIVATE+48], "extension patch destinations")
        require(all(memory[a] == (0 if PRIVATE+40 <= a < PRIVATE+52 else before[a])
                    for a in memory), "extension patch touched core/context/mailbox")
        require(regs[2:] == saved[2:], "extension patch corrupted saved registers")
    source = out / "extension_patch.S"
    source.write_text(".text\n.global extension_patch\nextension_patch:\n"
                      "r0 = 0x01c7fd74\nr1 = 0\n[r0+0] = r1\n[r0+4] = r1\n[r0+8] = r1\n" +
                      "nop\n"*7, encoding="utf-8")
    relative = lambda path: path.relative_to(ROOT).as_posix()
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    obj = out / "extension_patch.o"
    process = subprocess.run(prefix+[vendor+"clang", "-target", "pi32v2", "-mcpu=r3", "-c",
                                    relative(source), "-o", relative(obj)], cwd=ROOT,
                             capture_output=True, text=True)
    require(process.returncode == 0, "vendor assembler: " + process.stdout + process.stderr)
    require(elf_text(obj.read_bytes()) == p.after, "vendor assembler differs from patch bytes")
    return {"patch": p.record(), "decoded_instructions": rows,
            "randomized_store_bound_cases": 64, "vendor_assembler_bytes_identical": True,
            "object_sha256": sha(obj.read_bytes()), "hardware_execution": False}


def normalized_syscfg(raw, start, end, addresses):
    rows = instructions(raw, BASE, start, end)
    indices = {r["address"]: i for i, r in enumerate(rows)}
    normalized = []
    for row in rows:
        text = row["text"]
        if "target" in row:
            target = row["target"]
            label = f"instruction_{indices[target]}" if target in indices else addresses.get(target)
            require(label is not None, "unmapped syscfg branch/call")
            text = re.sub(r"\b(call|goto) -?\d+$", lambda m: m[1]+" "+label, text)
        if m := re.fullmatch(r"(r\d+) = (\d+)", text):
            value = int(m[2])
            if value in addresses:
                text = m[1]+" = "+addresses[value]
        normalized.append(text)
    return normalized


def audit_calibration(gp, mp, backup):
    gmap = {PRIVATE: "boot_info", 0x02001776: "crc16", 0x020558F4: "backends_begin", 0x02055948: "backends_end"}
    mmap = {0x01C7FD50: "boot_info", 0x02003E04: "crc16", 0x0206DDE8: "backends_begin", 0x0206DE3C: "backends_end"}
    gseq = normalized_syscfg(gp, 0x02024A78, 0x02024B10, gmap)
    mseq = normalized_syscfg(mp, 0x02003E3C, 0x02003ED2, mmap)
    require(gseq == mseq, "G/MINI syscfg reader semantics differ beyond explicit address/call mapping")
    geometry = inspect_vm_geometry(backup, 0x82000, 0x4000)
    require(geometry.get("no_maintenance_predicted"), "MINI active VM needs maintenance")
    p, end, latest = geometry["bank_start"]+4, geometry["write_pointer"], {}
    while p < end:
        h = int.from_bytes(backup[p:p+4], "little")
        size, ident = h >> 20, (h >> 8) & 0xFFF
        require(p+4+size <= end and (crc16(backup[p+4:p+4+size]) & 255) == (h & 255), "VM record CRC/bounds")
        latest[ident] = {"offset": p, "bytes": size}
        p += size+4
    consumers = []
    for ident, size, gsite, msite in ((106, 2, 0x02024B64, 0x02023B2E),
                                    (107, 7, 0x02024CB8, 0x02023B74),
                                    (108, 20, 0x02024F14, 0x02023D6C),
                                    (109, 34, 0x0205366A, 0x0206873C)):
        for raw, site in ((gp, gsite), (mp, msite)):
            rows = instructions(raw, BASE, site, site+4)
            require([r["text"] for r in rows] == [f"r0 = {ident}", f"r2 = {size}"], "calibration request changed")
        require(latest[ident]["bytes"] == size, "MINI calibration record width differs")
        consumers.append({"id": ident, "bytes": size, "G_request": gsite, "MINI_request": msite,
                          "backup_record": latest[ident], "width_and_id_match": True})
    tables = {}
    for name, raw, start in (("G", gp, 0x558F4), ("MINI", mp, 0x6DDE8)):
        tables[name] = [list(struct.unpack_from("<7I", raw, start+28*i)) for i in range(3)]
    # This observation is not a proof that no computed/indirect OTP consumer exists.
    require(b"OTP\0" not in gp[0x120:0x76AAC], "G app contains an OTP name")
    return {"core_boot_mac_reader_normalized_equal": True,
            "normalized_instructions": len(gseq),
            "normalized_sha256": sha("\n".join(gseq).encode()),
            "normalization": "Only explicitly listed absolute globals/callees and local branch instruction indices; no MMIO/register/opcode masks.",
            "normalization_G": gmap, "normalization_MINI": mmap,
            "syscfg_backend_tables": tables,
            "read_order": ["RAM cache, predicate table IDs102/104/110/111", "VM IDs1..255", "cfg_tool/BTIF IDs100..700 fallback"],
            "radio_records": consumers,
            "vm_other_record_metadata": {str(k): v for k, v in latest.items() if k not in (106, 107, 108, 109)},
            "btif": {"MINI_range": [0xBE000, 0xBF000], "G_name_open_call": 0x0201FB00,
                     "G_name": "mnt/sdfile/app/btif", "relative_factory_table_offset": 512,
                     "backup_factory_table_length": int.from_bytes(backup[0xBE200:0xBE204], "little"),
                     "factory_table_absent": backup[0xBE200:0xBE204] == bytes(4),
                     "G_rejects_zero_table_length_at": 0x0201FB26,
                     "preserve_entire_partition": True},
            "otp_partition": {"G_directory_range": [0xBE000, 0xBF000],
                              "MINI_has_directory": False, "same_range_is_MINI_BTIF": True,
                              "named_OTP_reference_in_G_app": False,
                              "all_indirect_consumers_excluded": False,
                              "physical_efuse_is_distinct_from_JLFS_OTP": True},
            "complete_calibration_semantics_proven": False,
            "unit_values_disclosed": False}


def inspect_recovery_record(backup, ota):
    """Inspect the exact SPL scan geometry; no decompression or execution."""
    records = []
    for sector in range(len(backup)-0x1000, 0x1000, -0x1000):
        offset = sector-0x100
        r = backup[offset:offset+80]
        if struct.unpack_from("<H", r, 6)[0] != 0x5441:
            continue
        require(crc16(r[2:]) == int.from_bytes(r[:2], "little"), "staged request CRC")
        address = int.from_bytes(r[72:76], "little")
        require(address < len(backup)-32, "staged loader outside flash")
        loader = jlfs_entry(backup, address)
        require(loader.name == "LOADER.BIN" and loader.offset == address and
                loader.size == len(ota) and address+loader.size <= len(backup), "staged loader geometry")
        body = backup[address+32:address+loader.size]
        require(body == ota[32:], "installed OTA differs from official package payload")
        packaged = jlfs_entry(ota, 0)
        require(packaged.offset == 32 and packaged.size == len(body) and
                crc16(body) == packaged.data_crc, "official OTA directory/payload CRC")
        require(crc16(body[2:32]) == int.from_bytes(body[:2], "little"), "compressed loader header CRC")
        records.append({"request_address": offset, "request_bytes": 80,
                        "request_sha256": sha(r), "request_crc16_valid": True,
                        "request_type": int.from_bytes(r[2:4], "little"),
                        "identity": r[8:40].split(b"\0", 1)[0].decode("ascii"),
                        "loader_address": address, "loader_bytes": loader.size,
                        "loader_end": address+loader.size,
                        "loader_directory_crc16_valid": True,
                        "official_payload_matches_exactly": True,
                        "payload_sha256": sha(body), "official_payload_crc16_valid": True,
                        "decompressed_bytes": int.from_bytes(body[4:8], "little"),
                        "decompressed_entry": int.from_bytes(body[8:12], "little")})
    require(len(records) == 1 and records[0]["request_address"] == 0xBCF00 and
            records[0]["loader_address"] == 0xB7000, "unexpected MINI staged updater inventory")
    return records


def audit_recovery(boot, config, backup, ota):
    records = inspect_recovery_record(backup, ota)
    require(boot[0x3710:0x3720] == b"usb_update_mode\0", "SPL USB marker")
    require(config["RESET"] == b"PB01_08_0", "MINI reset metadata")
    # Do not equate an unconfigured generic input with an absent ROM facility.
    missing = [key for key in ("PORT_INPUT", "PORT_OUTPUT", "ERR_PORT_OUTPUT", "BOOT_DELAY") if key not in config]
    require(len(missing) == 4, "MINI boot GPIO configuration changed")
    regions = {"header_validation": (0x01C033D0, 0x01C0340E),
               "validation_failure_clears_app_base": (0x01C04D56, 0x01C04D70),
               "failure_selects_staged_scan": (0x01C04DF8, 0x01C04E26),
               "staged_request_scan": (0x01C04E24, 0x01C04E64),
               "app_absent_branch": (0x01C04F94, 0x01C04F9E),
               "usb_marker_copy_and_reset": (0x01C0529A, 0x01C052A8),
               "no_request_clear_and_reset": (0x01C0531E, 0x01C0532C),
               "software_reset": (0x01C028F4, 0x01C028FE),
               "SPL_watchdog_disable": (0x01C0381E, 0x01C03868),
               "optional_input_config": (0x01C03A76, 0x01C03A84),
               "RESET_config_to_metadata": (0x01C03A9E, 0x01C03ADE)}
    fragments = {name: fragment(boot, BOOT_BASE, *bounds) for name, bounds in regions.items()}
    installer = audit_installer()  # Pin the recovered bytecode/constants too.
    functions = {f["name"]: f for f in json.loads((ROOT/"recovered/installer/tankg_install.constants.json").read_bytes())}
    evidence = []
    for name, function in functions.items():
        text = json.dumps(function, ensure_ascii=False)
        if "Si no, el SPL no salta" in text or ("modo OTA" in text and "leave_uboot" in text):
            evidence.append(name)
    require(evidence, "original installer invalid-app recovery evidence missing")
    return {"staged_updaters": records, "stock_fragments": fragments,
            "invalid_header_unconditionally_enters_ROM": False,
            "stock_OTA_recovery_present_offline": True,
            "stock_OTA_entry_hardware_verified": False,
            "valid_image_hang_recovery_verified": False,
            "factory_SPL_kept": True,
            "factory_OTA_must_be_kept": [[0xB7000, records[0]["loader_end"]], [0xBC000, 0xBD000]],
            "preservation_scope": "Keep the entire MINI VM region [0x82000,0xBE000), including the independent OTA VM/header sector at0xBC000.",
            "original_installer": installer,
            "original_installer_invalid_app_evidence_functions": evidence,
            "recovery_button_audit": {
                "config_RESET": "PB01_08_0", "configured_optional_boot_gpio_keys_absent": missing,
                "RESET_parser_stores": "Parsed pin, level, duration bytes into descriptor+48/+49/+50 at0x01C03AB6/3AC8/3ADC; this fragment does not sample GPIO or branch to recovery.",
                "foot_switch_to_ROM_branch_identified": False,
                "absence_of_all_ROM_pin_recovery_proven": False,
                "official_manual": "https://manualf.oss-cn-hongkong.aliyuncs.com/manual/Combined-Effect-Pedals/TANK-MINI.pdf",
                "manual_result": "No recovery/power-on combination found; A+B and B+C describe runtime BT/tuner controls.",
                "official_product": "https://www.m-vave.com/product?id=tank-mini",
                "official_updater": "https://www.m-vave.com/download"},
            "marker_guard": {"already_implemented": False,
                             "would_only_cover": "Failures after marker store followed by a reset retaining RAM.",
                             "does_not_cover": ["invalid entry/header before marker", "loss of retained RAM", "hang without reset"],
                             "SPL_disables_WDT": True,
                             "requires_verified_early_WDT_and_first_entry": True},
            "USB_KEY": {"reference": "https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#43-recovery-independent-of-a-valid-boot-image",
                        "documented_target": "SMK-37 Pro AC791N", "word": 0x16EF,
                        "MINI_hardware_verified": False},
            "next_proofs": [
                "Prove a MINI recovery trigger with stock flash intact before installing a full image.",
                "If using USB_KEY: force ROM at power-on, identify4C4A:8057, run read-only RAM diagnostics, then verify normal return and unchanged backup hashes.",
                "If using staged OTA: separately prove the MINI updater can start without the normal application and identify ota-TANK MINI; this is not the ROM SCSI protocol.",
                "Before any writer: review sector allowlist, verify preserved SPL/OTA/VM/BTIF/key_mac, and prepare exact readback/rollback for this unit.",
                "A valid-image hang additionally requires proven independent trigger or early retained marker plus a hardware-tested watchdog; a USB soft key is insufficient."]}


def main():
    out = ROOT/"build/mini-boot-contract"
    out.mkdir(parents=True, exist_ok=True)
    graw, package = (ROOT/G_PATH).read_bytes(), (ROOT/MINI_PATH).read_bytes()
    gp, _, _, mp, _, _, flash = pinned_inputs(graw, package)
    boot_patches(gp)
    boot, config = stock_boot(flash)
    backup = (ROOT/BACKUP_PATH).read_bytes()
    require(len(backup) == 0x100000 and sha(backup) == BACKUP_SHA, "unexpected unit backup")
    require(backup[:0x4000] == flash[:0x4000], "unit SPL differs from package")
    _, files = unpack_fwsc(package)
    report = {
        "schema": 1, "scope": "offline original-G to MINI full-application boot contract",
        "inputs": {"original_G": sha(graw), "G_plain": sha(gp), "MINI_package": sha(package),
                   "MINI_SPL_payload": sha(boot), "unit_backup": sha(backup)},
        "clock": audit_clock(gp),
        "handover": {"incoming_context": CONTEXT, "core_bytes": 24,
                     "fields": {"0": "decoded flash-header pointer", "4": "physical app base",
                                "8": "CPU logical app base", "12": "uint16 chip/SFC key",
                                "14": "uint16 trim", "16": "8-byte BT MAC+CRC carrier"},
                     "G_private_boot_info": PRIVATE,
                     "G_import": fragment(gp, BASE, 0x0200042E, 0x02000484),
                     "MINI_optional_extension_branch": fragment(boot, BOOT_BASE, 0x01C04F9E, 0x01C04FCE),
                     "MINI_core_handoff": fragment(boot, BOOT_BASE, 0x01C051A2, 0x01C051EE),
                     "G_extension_fields": [{"incoming_offset": 80, "bytes": 8, "destination": PRIVATE+40, "SDK_type": "SDRAM_CFG_INFO"},
                                            {"incoming_offset": 88, "bytes": 4, "destination": PRIVATE+48, "SDK_type": "EX_APP_INFO"}],
                     "MINI_no_SDRAM": True, "incoming_extensions_guaranteed_initialized": False,
                     "patch_verification": verify_patch(out)},
        "calibration": audit_calibration(gp, mp, backup),
        "recovery": audit_recovery(boot, config, backup, files["ota.bin"]),
        "references": [{"url": "https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/system/boot.h",
                        "sha256": "916e78a034b1bef599274f8faa936d75edd5e31caaa0d9e7c11be70433f157bf",
                        "role": "Documentary ABI field names/sizes; not needed for offline execution."}],
        "no_device_access": True, "candidate_emitted": False, "flashable": False,
        "full_G_on_MINI_boot_verified": False,
    }
    (ROOT/"research/mini-boot-contract.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "clock_cases": report["clock"]["getter_instruction_cases"],
                      "boot_extension_patch_bytes": 28, "patch_store_cases": 64,
                      "calibration_id_widths_match": [106, 107, 108, 109],
                      "stock_OTA_payload_matches": True, "flashable": False}))


if __name__ == "__main__":
    main()
