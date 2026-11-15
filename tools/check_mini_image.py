"""Validate a MINI ELF and the pinned stock container entirely offline.

Successful checks establish file/layout consistency only. No package is built,
no transport is opened, and no artifact is ever marked flashable by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc

FLASH_BASE, FLASH_END, ENTRY = 0x02000000, 0x0207E000, 0x02000120
RAM_START, RAM_END = 0x01C00000, 0x01C7FD30
BOOT_RESERVED_END = 0x01C80000
APP_START, APP_END = 0x4000, 0x82000
MINI_SHA256 = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
REGIONS = {"VM": (0x82000, 0xBE000), "PRCT": (0, 0x82000),
           "BTIF": (0xBE000, 0xBF000), "USR": (0xBF000, 0xFF000)}
REQUIRED_SYMBOLS = ("__ram_start", "__ram_end", "__ram_load_start", "__ram_load_end",
                    "__bss_start", "__bss_end", "__stack_bottom", "__stack_top",
                    "__ssp_bottom", "__ssp_top", "__boot_reserved_start", "__boot_reserved_end",
                    "__flash_image_end", "__noinit_start", "__noinit_end",
                    "__ram_region_start", "__ram_region_end")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def within(start, size, low, high):
    return low <= start <= high and 0 <= size <= high - start


def overlap(a, b):
    return a[0] < a[1] and b[0] < b[1] and a[0] < b[1] and b[0] < a[1]


def covered(start, end, ranges):
    """Require every byte of a half-open span, including gaps, to be present."""
    cursor = start
    for low, high in sorted(ranges):
        if cursor >= end:
            return True
        if high <= cursor:
            continue
        if low > cursor:
            return False
        cursor = high
    return cursor >= end


def inspect_application(raw: bytes) -> dict:
    """Reject a CRC-valid G/B area as well as corrupt/truncated MINI areas."""
    require(len(raw) == APP_END - APP_START, "application slice does not have the MINI [0x4000,0x82000) size")
    plain, entries, files = unpack_app(raw, key=0x980F)
    directory = {e.name: e for e in entries}
    require(entries[0].offset == ENTRY, "unexpected MINI entrypoint in JLFS")
    require(directory["app.bin"].offset == 0x120, "app.bin must start at area offset 0x120")
    for name, (start, end) in REGIONS.items():
        require(name in directory, f"missing MINI region {name}")
        item = directory[name]
        require((item.offset, item.size) == (start, end - start), f"{name} differs from the MINI memory map (G/B images are incompatible)")
    require("OTP" not in directory, "G/B OTP layout is incompatible with MINI BTIF")
    return {"sha256": digest(raw), "physical_range": [APP_START, APP_END],
            "cpu_range": [FLASH_BASE, FLASH_END], "cpu_entry": entries[0].offset,
            "app_bytes": len(files["app.bin"]), "app_sha256": digest(files["app.bin"]),
            "application_crc_and_file_crcs_valid": True,
            "directory": [e.to_dict() for e in entries],
            "contains_stock_identity": b"TANK MINI_009" in plain}


def inspect_stock(raw: bytes) -> dict:
    fwsc, files = unpack_fwsc(raw)
    require(fwsc["chip"] == "AC791N", "FWSC chip is not AC791N")
    require("flash.bin" in files, "FWSC flash.bin is missing")
    require(len(files["flash.bin"]) == APP_END, "stock flash.bin does not end at MINI VM start")
    app = inspect_application(files["flash.bin"][APP_START:])
    require(digest(raw) == MINI_SHA256, "FWSC differs from the pinned TANK MINI_009 stock package")
    ota = files.get("ota.bin", b"")
    ota_name = ota[16:32].split(b"\0", 1)[0].decode("ascii", errors="replace") if len(ota) >= 32 else None
    return {"file_format": "FWSC", "sha256": digest(raw), "bytes": len(raw),
            "chip": fwsc["chip"], "pinned_stock_verified": True,
            "flash_bytes_in_package": len(files["flash.bin"]),
            "flash_sha256": digest(files["flash.bin"]),
            "pre_application_range": [0, APP_START],
            "pre_application_sha256": digest(files["flash.bin"][:APP_START]),
            "application": app, "entries": fwsc["entries"], "ota_payload_name": ota_name,
            "opaque_auxiliary_raw_crc_mismatches": [e["name"] for e in fwsc["entries"] if not e["raw_crc_ok"]],
            "complete_device_flash_backup": False,
            "not_in_flash_payload": {"VM": [0x82000, 0xBE000], "BTIF": [0xBE000, 0xBF000],
                                     "USR": [0xBF000, 0xFF000], "key_mac_candidate": [0xFF000, 0x100000]},
            "note": "Opaque auxiliary entries may use additional encoding; their raw CRC mismatch is not proof of corruption."}


def inspect_elf(raw: bytes) -> dict:
    require(len(raw) >= 52 and raw[:7] == b"\x7fELF\x01\x01\x01", "expected ELF32 little-endian version 1")
    (kind, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum,
     shsize, shnum, shstr) = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    require(kind == 2, "ELF must be a linked executable (ET_EXEC); a relocatable DSP object is incomplete")
    require(machine == 0xF1 and version == 1, "ELF machine/version is not JieLi pi32v2")
    require(ehsize == 52 and phsize == 32 and 1 <= phnum <= 64, "invalid ELF program-header table")
    require(within(phoff, phsize * phnum, 52, len(raw)), "truncated ELF program-header table")
    require(shsize == 40 and 1 <= shnum <= 4096 and shstr < shnum, "section/symbol tables required for static checks")
    require(within(shoff, shsize * shnum, 52, len(raw)), "truncated ELF section table")
    require(entry == ENTRY, "ELF entry is not the MINI application address 0x02000120")
    loads, file_ranges, virtual_ranges = [], [], []
    for i in range(phnum):
        typ, offset, vaddr, paddr, filesz, memsz, permissions, align = struct.unpack_from("<8I", raw, phoff + i * 32)
        require(typ not in (2, 3), "dynamic/interpreted ELF is not a standalone MINI target")
        if typ != 1 or memsz == 0:
            require(typ != 1 or filesz == 0, "empty PT_LOAD has file data")
            continue
        require(filesz <= memsz, "PT_LOAD file bytes exceed memory size")
        require(within(offset, filesz, 0, len(raw)), "PT_LOAD payload outside ELF")
        require(align in (0, 1) or (align & (align - 1) == 0 and offset % align == vaddr % align), "invalid PT_LOAD alignment")
        region = "flash" if within(vaddr, memsz, ENTRY, FLASH_END) else "ram" if within(vaddr, memsz, RAM_START, RAM_END) else None
        require(region is not None, "PT_LOAD VMA leaves MINI application/RAM or touches boot-reserved memory")
        require(not any(overlap((vaddr, vaddr + memsz), r) for r in virtual_ranges), "overlapping PT_LOAD virtual ranges")
        virtual_ranges.append((vaddr, vaddr + memsz))
        if region == "flash":
            require(filesz == memsz and paddr == vaddr, "flash PT_LOAD must have matching VMA/LMA and no zero-fill")
        if filesz:
            require(within(paddr, filesz, ENTRY, FLASH_END), "PT_LOAD initial bytes do not fit MINI flash LMA")
            require(not any(overlap((paddr, paddr + filesz), r) for r in file_ranges), "overlapping PT_LOAD flash LMAs")
            file_ranges.append((paddr, paddr + filesz))
        loads.append({"index": i, "offset": offset, "vaddr": vaddr, "lma": paddr,
                      "file_bytes": filesz, "memory_bytes": memsz, "flags": permissions, "region": region})
    require(loads, "ELF has no loadable content")
    require(any(s["region"] == "flash" and s["flags"] & 1 and
                within(entry, 2, s["vaddr"], s["vaddr"] + s["file_bytes"]) for s in loads), "entry is not backed by executable flash bytes")
    sections = [struct.unpack_from("<10I", raw, shoff + i * 40) for i in range(shnum)]
    require(sections[shstr][1] == 3, "section names are not a string table")
    for i, section in enumerate(sections):
        name, typ, attributes, address, offset, size, link, info, align, entsize = section
        if typ not in (0, 8):
            require(within(offset, size, 0, len(raw)), f"section {i} outside ELF")
        if attributes & 2 and size:
            require(any(within(address, size, s["vaddr"], s["vaddr"] + s["memory_bytes"]) and
                        (typ == 8 or (within(address, size, s["vaddr"], s["vaddr"] + s["file_bytes"]) and
                                      offset == s["offset"] + address - s["vaddr"])) for s in loads),
                    f"allocated section {i} is not covered by a PT_LOAD")
    symbols, undefined = {}, []
    for section in sections:
        _, typ, _, _, offset, size, link, _, _, entsize = section
        if typ not in (2, 11):
            continue
        require(entsize == 16 and size % 16 == 0 and link < shnum and sections[link][1] == 3, "malformed symbol table")
        strings = raw[sections[link][4]:sections[link][4] + sections[link][5]]
        for pos in range(offset, offset + size, 16):
            name_index, value, sym_size, sym_info, other, section_index = struct.unpack_from("<IIIBBH", raw, pos)
            require(name_index < len(strings), "symbol string offset outside table")
            end = strings.find(b"\0", name_index)
            require(end != -1, "unterminated ELF symbol name")
            name = strings[name_index:end].decode("ascii", errors="replace")
            if name and section_index == 0 and sym_info >> 4 in (1, 2):
                undefined.append(name)
            if name in REQUIRED_SYMBOLS and section_index != 0:
                require(name not in symbols or symbols[name] == value, f"conflicting values for symbol {name}")
                symbols[name] = value
    require(not undefined, "unresolved symbols: " + ", ".join(sorted(set(undefined))))
    require(all(name in symbols for name in REQUIRED_SYMBOLS), "missing MINI linker contract symbols: " +
            ", ".join(name for name in REQUIRED_SYMBOLS if name not in symbols))
    ram_start, ram_end = symbols["__ram_start"], symbols["__ram_end"]
    load_start, load_end = symbols["__ram_load_start"], symbols["__ram_load_end"]
    require(within(ram_start, ram_end - ram_start, RAM_START, RAM_END), "RAM copy destination outside allowed range")
    require(within(load_start, load_end - load_start, ENTRY, FLASH_END), "RAM copy source outside application")
    require(ram_end - ram_start == load_end - load_start, "RAM copy source/destination lengths differ")
    require(all(v % 4 == 0 for v in (ram_start, ram_end, load_start, load_end)), "RAM copy spans must be word-aligned")
    for s in loads:
        if s["region"] == "ram" and s["file_bytes"]:
            require(within(s["vaddr"], s["file_bytes"], ram_start, ram_end) and
                    s["lma"] - load_start == s["vaddr"] - ram_start,
                    "file-backed RAM PT_LOAD disagrees with startup copy symbols")
    ram_files = [s for s in loads if s["region"] == "ram" and s["file_bytes"]]
    require(covered(ram_start, ram_end, [(s["vaddr"], s["vaddr"] + s["file_bytes"]) for s in ram_files]) and
            covered(load_start, load_end, [(s["lma"], s["lma"] + s["file_bytes"]) for s in ram_files]),
            "startup RAM copy span is not fully backed by ELF load bytes")
    bss = (symbols["__bss_start"], symbols["__bss_end"])
    require(within(bss[0], bss[1] - bss[0], RAM_START, RAM_END) and bss[0] % 4 == bss[1] % 4 == 0,
            "BSS clear span outside RAM or not word-aligned")
    require(not overlap(bss, (ram_start, ram_end)), "BSS clear would erase initialized RAM")
    noinit = (symbols["__noinit_start"], symbols["__noinit_end"])
    require(within(noinit[0], noinit[1] - noinit[0], RAM_START, RAM_END), "noinit span outside allowed RAM")
    require(not overlap(noinit, bss) and not overlap(noinit, (ram_start, ram_end)), "noinit overlaps initialized/cleared RAM")
    stacks = []
    for prefix in ("__stack", "__ssp"):
        span = (symbols[prefix + "_bottom"], symbols[prefix + "_top"])
        require(span[1] > span[0] and within(span[0], span[1] - span[0], RAM_START, RAM_END), "stack leaves allowed RAM")
        require(span[0] % 4 == span[1] % 4 == 0, "stack is not word-aligned")
        require(not overlap(span, (ram_start, ram_end)) and not overlap(span, bss) and not overlap(span, noinit),
                "stack overlaps initialized data/BSS/noinit")
        require(not any(overlap(span, previous) for previous in stacks), "stack ranges overlap")
        stacks.append(span)
    require((symbols["__ram_region_start"], symbols["__ram_region_end"]) == (RAM_START, RAM_END),
            "RAM region contract differs from MINI")
    strings = raw[sections[shstr][4]:sections[shstr][4] + sections[shstr][5]]
    for i, section in enumerate(sections):
        name_index, typ, attributes, address, _, size, _, _, _, _ = section
        if typ != 8 or not attributes & 2 or not size:
            continue
        require(name_index < len(strings), "section name outside string table")
        end = strings.find(b"\0", name_index)
        require(end != -1, "unterminated section name")
        name = strings[name_index:end].decode("ascii", errors="replace")
        if name.startswith(".noinit"):
            accepted = within(address, size, *noinit)
        elif name.startswith((".stack", ".ssp")):
            accepted = covered(address, address + size, stacks)
        else:
            accepted = within(address, size, *bss)
        require(accepted, f"allocated NOBITS section {name or i} is outside its BSS/noinit/stack initialization contract")
    require((symbols["__boot_reserved_start"], symbols["__boot_reserved_end"]) == (RAM_END, BOOT_RESERVED_END),
            "boot-reserved RAM contract differs from MINI")
    require(max(end for _, end in file_ranges) <= symbols["__flash_image_end"] <= FLASH_END,
            "flash image end disagrees with load segments")
    return {"file_format": "ELF32-pi32v2", "sha256": digest(raw), "bytes": len(raw),
            "elf_type": kind, "machine": machine, "entry": entry, "elf_flags": flags,
            "layout_valid": True, "flashable": False, "boot_verified_on_device": False,
            "status": "linked-application-layout-only", "load_segments": loads,
            "linker_symbols": {name: symbols[name] for name in REQUIRED_SYMBOLS},
            "file_backed_flash_bytes": sum(s["file_bytes"] for s in loads),
            "limit": "Linking and layout checks do not establish startup, clock, interrupts, audio or update/recovery behavior."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, default=ROOT / "artifacts/tank-mini/TANK-MINI.fwsc")
    parser.add_argument("--elf", type=Path, action="append", default=[],
                        help="linked MINI ELF to validate; repeat for multiple probes; no firmware is generated")
    parser.add_argument("--report", type=Path, help="write JSON evidence, otherwise print it")
    args = parser.parse_args(argv)
    try:
        result = {"project": "HyperRig", "target": "tank-mini", "flashable": False,
                  "validator": {"source": "tools/check_mini_image.py", "sha256": digest(Path(__file__).read_bytes())},
                  "stock": inspect_stock(args.stock.read_bytes()),
                  "candidates": [{"artifact": path.name, **inspect_elf(path.read_bytes())} for path in args.elf],
                  "hardware_writes": False,
                  "remaining_for_device_boot": ["Validate bootloader-to-application handoff and board clock setup.",
                       "Integrate and verify IRQ/audio/DSP scheduling on the MINI.",
                       "Verify update transport and a complete unit-specific backup/recovery route.",
                       "Validate the composed MINI application with the board updater metadata/transport before installation."]}
    except (ValueError, OSError, struct.error) as error:
        result = {"project": "HyperRig", "target": "tank-mini", "flashable": False, "error": str(error)}
        code = 2
    else:
        code = 0
    encoded = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
