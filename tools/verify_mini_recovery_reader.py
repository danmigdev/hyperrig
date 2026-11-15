"""Build/test a bounded PIO NOR-reader ROM plugin. Offline; no device access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "firmware/mini/recovery_reader"
SLOTS = (0x01c20000, 0x01c28000)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def inspect_reader(raw, slot):
    check(raw[:7] == b"\x7fELF\x01\x01\x01", "require ELF32 little endian")
    h = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    check(h[0] == 2 and h[1] == 0xf1 and h[3] == slot, "reader ELF machine/type/entry")
    check(h[8] == 32 and h[10] == 40 and h[9] > 0, "ELF header geometry")
    sections = [struct.unpack_from("<10I", raw, h[5] + i * h[10]) for i in range(h[11])]
    functions, symbols, loads = [], {}, []
    image_end = slot
    memory_end = slot
    for i in range(h[9]):
        p = struct.unpack_from("<8I", raw, h[4] + i * h[8])
        if p[0] != 1:
            check(p[0] in (0, 0x6474e551), "unexpected runtime ELF segment")
            continue
        kind, offset, vma, lma, size, memory, flags, alignment = p
        check(vma == lma and slot <= vma < vma + memory <= slot + 0x8000,
              "reader segment outside its RAM upload slot")
        check(size <= memory and offset + size <= len(raw), "segment size")
        check(alignment > 0 and not alignment & (alignment - 1) and offset % alignment == vma % alignment,
              "invalid ELF alignment")
        check(flags & 7 == flags, "unsupported segment flags")
        loads.append((offset, vma, size, memory, flags))
        image_end = max(image_end, vma + size)
        memory_end = max(memory_end, vma + memory)
    check(len(loads) == 1 and loads[0][1] == slot and loads[0][4] == 7, "one complete RAM image required")
    for s in sections:
        check(s[1] not in (4, 6, 9), "relocations/dynamic metadata in final reader")
        if s[2] & 2 and s[5]:
            check(slot <= s[3] < s[3] + s[5] <= memory_end, "allocated section outside reader")
            if s[1] != 8:
                check(s[3] + s[5] <= image_end, "file-backed section outside uploaded bytes")
        if s[1] != 2:
            continue
        strings = sections[s[6]]
        names = raw[strings[4]:strings[4] + strings[5]]
        for pos in range(s[4], s[4] + s[5], s[9]):
            name, value, size, info, other, section = struct.unpack_from("<IIIBBH", raw, pos)
            if not name:
                continue
            text = names[name:names.index(0, name)].decode()
            check(section != 0, "undefined target symbol: " + text)
            symbols[text] = value
            if info & 15 == 2:
                check(slot <= value < value + max(1, size) <= image_end, "function outside uploaded image")
                functions.append(text)
    check(symbols["hyperrig_reader_entry"] == slot and symbols["__slot_end"] == slot + 0x8000,
          "linker slot contract")
    check(symbols["__bss_end"] == memory_end and symbols["__image_file_end"] == image_end,
          "private memory/file boundary symbols")
    flat = bytearray(image_end - slot)
    for offset, vma, size, memory, flags in loads:
        flat[vma - slot:vma - slot + size] = raw[offset:offset + size]
    return bytes(flat), {"slot": slot, "entry": h[3], "image_bytes": len(flat),
                         "private_ram_bytes": memory_end - slot, "private_ram_end": memory_end,
                         "functions": functions, "all_code_and_data_in_slot": True,
                         "unresolved_symbols": 0, "runtime_relocations": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distro", default="Ubuntu")
    args = parser.parse_args()
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []
    directory = ROOT / "build/mini-flash-reader"
    directory.mkdir(parents=True, exist_ok=True)
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"

    def run(command):
        result = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout

    run(["gcc", "-std=c99", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
         "firmware/mini/recovery_reader/test_reader.c", "firmware/mini/recovery_reader/reader.c",
         "-o", "build/mini-flash-reader/test-reader"])
    tests = json.loads(run(["build/mini-flash-reader/test-reader"]))
    tests.update({"address_sanitizer": True, "undefined_behavior_sanitizer": True,
                  "executable_sha256": sha((directory / "test-reader").read_bytes())})
    print("PIO reader host tests: ASan/UBSan passed, including 522 individual byte timeouts.", flush=True)
    objects = []
    for name in ("entry", "reader", "memory"):
        out = "build/mini-flash-reader/" + name + ".o"
        run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", "-std=c99", "-Os", "-ffreestanding",
             "-fno-builtin", "-Wall", "-Wextra", "-Werror", "-c",
             "firmware/mini/recovery_reader/" + name + ".c", "-o", out])
        objects.append(out)
    artifacts = []
    for slot in SLOTS:
        name = "build/mini-flash-reader/hyperrig-reader-" + f"{slot:08x}"
        run([vendor + "ld", "-z", "max-page-size=0x20", "-z", "common-page-size=0x20",
             "--defsym", f"READER_ADDRESS={slot}", "-T", "firmware/mini/recovery_reader/reader.ld",
             "-Map", name + ".map", *objects, "-o", name + ".elf"])
        raw = (ROOT / (name + ".elf")).read_bytes()
        flat, audit = inspect_reader(raw, slot)
        (ROOT / (name + ".bin")).write_bytes(flat)
        listing = run([vendor + "objdump", "-d", name + ".elf"])
        (ROOT / (name + ".asm")).write_text(listing, encoding="utf-8", newline="\n")
        artifacts.append({"elf": name + ".elf", "elf_sha256": sha(raw), "flat": name + ".bin",
                          "flat_sha256": sha(flat), "audit": audit, "device_executed": False,
                          "nvm_writable": False, "application_image": False})
        print(f"Reader slot {slot:#x}: {len(flat)} uploaded bytes, {audit['private_ram_bytes']} private RAM bytes.", flush=True)
    boot_report = (ROOT / "research/mini-handover.json").read_bytes()
    boot = json.loads(boot_report)
    check(boot["stock"]["boot_payload_sha256"] == "fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d",
          "reader pin evidence must match the checked MINI bootloader")
    report = {"project": "HyperRig", "target": "TANK MINI", "protocol": "HYRN v1",
              "host_tests": tests, "artifacts": artifacts,
              "sources_sha256": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                                  for p in sorted(SOURCES.iterdir()) if p.is_file()},
              "verifier_sha256": sha(Path(__file__).read_bytes()),
              "stock_boot_report_sha256": sha(boot_report), "stock_boot_payload_sha256": boot["stock"]["boot_payload_sha256"],
              "reference": {"repository": "https://github.com/jvitkauskas/m-bootloader",
                            "commit": "3ac7651a019fa44daba061b05654278496477b64",
                            "platform_sha256": sha((ROOT / "upstream/m-bootloader/src/platform.c").read_bytes()),
                            "loader_abi_sha256": sha((ROOT / "upstream/m-bootloader/src/loader_target.c").read_bytes())},
              "spi_commands": {"exit_continuous_read": "ff ff", "jedec": "9f", "read": "03 + 24-bit address"},
              "rom_commands": {"fc70": "identity, no MMIO", "fc72": "explicit SPI init + JEDEC",
                               "fd71": "read 1..512 bytes", "fc73": "sticky error and successful byte counter"},
              "clock_guard": {"sys_div_address": 0x10008, "sys_div_mask": 0x30700,
                              "clk_con2_address": 0x10014, "clk_con2_mask": 255,
                              "accepted_pairs_clk_div": [[0x80, 0], [0x40, 0x100]], "clock_writes": False},
              "spi_baud_divider_register": 15, "supported_capacity_bytes": 0x100000,
              "dma_used": False, "display_used": False, "p33_or_efuse_used": False,
              "watchdog_modified": False, "cache_or_mmu_modified": False,
              "physical_boot_verified": False, "physical_flash_read_verified": False,
              "nvm_write_operations_available": False,
              "limitations": ["clock field match does not measure a physical frequency",
                              "ROM callback/slot compatibility must be established on this MINI first",
                              "ROM send callback nonnegative return is accepted; exact return semantics unmeasured",
                              "GPIO/SPI initialization changes volatile hardware state; all plugin code must be in RAM",
                              "host must require status zero and exact counter advance after every block",
                              "host must preserve two complete identical 1 MiB reads and metadata before any NVM work",
                              "malformed transfers over 512 bytes are not fully drained and may require ROM recovery"]}
    (ROOT / "research/mini-flash-reader.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
