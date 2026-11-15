"""Compose an experimental MINI application area from a checked diagnostic ELF.

Offline only. This is not a FWSC/update package or a full-flash image. It does
not contain a bootloader, unit keys, VM, BTIF or user data. A valid container
does not establish that its program can boot or be safely installed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import crc16, sfc, sha256, unpack_app, unpack_fwsc
from check_mini_image import (APP_END, APP_START, ENTRY, FLASH_BASE,
                              inspect_application, inspect_elf, inspect_stock, require)


def flatten_elf(raw: bytes) -> tuple[bytes, dict]:
    """Use flash load addresses, including the source of initialized RAM."""
    layout = inspect_elf(raw)
    end = layout["linker_symbols"]["__flash_image_end"]
    image = bytearray(b"\xff" * (end - ENTRY))
    for segment in layout["load_segments"]:
        size = segment["file_bytes"]
        if not size:
            continue  # BSS, noinit and stacks never become file payloads.
        offset = segment["offset"]
        start = segment["lma"] - ENTRY
        image[start:start + size] = raw[offset:offset + size]
    return bytes(image), layout


def stock_template(stock: bytes):
    evidence = inspect_stock(stock)  # Requires the pinned 009 package and CRCs.
    _, files = unpack_fwsc(stock)
    raw = files["flash.bin"][APP_START:APP_END]
    plain, entries, payloads = unpack_app(raw)
    require(set(payloads) == {"app.bin", "cfg_tool.bin"}, "unexpected stock payload set")
    directory = {entry.name: entry for entry in entries}
    require(directory["app.bin"].offset == ENTRY - FLASH_BASE, "unexpected stock app offset")
    return evidence, plain, entries, payloads, directory


def build_application(elf: bytes, stock: bytes) -> tuple[bytes, dict]:
    program, layout = flatten_elf(elf)
    stock_info, template, entries, payloads, directory = stock_template(stock)
    app, config, head = (directory[name] for name in ("app.bin", "cfg_tool.bin", "app_area_head"))
    require(app.offset + len(program) <= config.offset,
            "ELF load image overlaps the preserved MINI cfg_tool.bin")
    require(config.offset + config.size == head.size, "unexpected stock config/head extent")
    # Preserve the stock directory and opaque configuration at their original
    # offsets. Replace the complete old executable extent with erased fill.
    plain = bytearray(b"\xff" * len(template))
    plain[:app.offset] = template[:app.offset]
    plain[app.offset:app.offset + len(program)] = program
    plain[config.offset:config.offset + config.size] = payloads["cfg_tool.bin"]
    struct.pack_into("<I", plain, app.header_offset + 8, len(program))
    struct.pack_into("<H", plain, app.header_offset + 2, crc16(program))
    struct.pack_into("<H", plain, app.header_offset,
                     crc16(plain[app.header_offset + 2:app.header_offset + 32]))
    struct.pack_into("<H", plain, 2, crc16(plain[32:head.size]))
    struct.pack_into("<H", plain, 0, crc16(plain[2:32]))
    cipher_end = (head.size + 31) & ~31
    require(cipher_end <= len(plain), "aligned SFC extent exceeds MINI application area")
    packed = sfc(bytes(plain[:cipher_end])) + bytes(plain[cipher_end:])
    verified = verify_application(packed, elf, stock)
    return packed, {"project": "HyperRig", "target": "tank-mini",
                    "status": "experimental-offline-application-area",
                    "source_stock_sha256": stock_info["sha256"],
                    "source_elf_sha256": layout["sha256"],
                    "app_area_sha256": sha256(packed), "bytes": len(packed),
                    "physical_range": [APP_START, APP_END], "entry": ENTRY,
                    "app_payload_bytes": len(program), "app_payload_sha256": sha256(program),
                    "cfg_tool_sha256": sha256(payloads["cfg_tool.bin"]),
                    "preserved_directory_records": [entry.name for entry in entries[2:]],
                    "sfc_key_source": "pinned stock package 0x980f; not measured on this unit",
                    "checks": verified, "boot_verified_on_device": False,
                    "installable_update_package": False, "complete_flash_backup": False,
                    "hardware_write_performed": False,
                    "omitted_physical_ranges": {"boot": [0, APP_START],
                        "VM_BTIF_USR_key": [APP_END, 0x100000]},
                    "remaining": ["Verify actual unit backup and recovery transport.",
                        "Verify clock/watchdog/cache and bootloader handoff on the MINI.",
                        "Integrate and measure real codec/DMA/IRQ/DSP execution.",
                        "Validate MINI updater metadata and address semantics before any installation."]}


def verify_application(raw: bytes, elf: bytes, stock: bytes) -> dict:
    """Check CRCs, preserved records, all ELF load bytes and erased gaps."""
    area = inspect_application(raw)
    layout = inspect_elf(elf)
    _, template, entries, payloads, directory = stock_template(stock)
    decoded, new_entries, new_files = unpack_app(raw)
    require(len(new_entries) == len(entries), "application directory count changed")
    for entry in entries[2:]:
        start = entry.header_offset
        require(decoded[start:start + 32] == template[start:start + 32],
                f"preserved directory record changed: {entry.name}")
    require(new_entries[0].offset == entries[0].offset and new_entries[0].size == entries[0].size,
            "application head address/size changed")
    require(decoded[4:32] == template[4:32], "application head metadata changed")
    require(new_entries[1].offset == directory["app.bin"].offset, "app file offset changed")
    require(decoded[36:40] == template[36:40] and decoded[44:64] == template[44:64],
            "app file metadata changed")
    directory_end = entries[-1].header_offset + 32
    require(decoded[directory_end:directory["app.bin"].offset] ==
            template[directory_end:directory["app.bin"].offset], "directory padding changed")
    require(new_files["cfg_tool.bin"] == payloads["cfg_tool.bin"], "stock cfg_tool changed")
    image_end = layout["linker_symbols"]["__flash_image_end"]
    program = new_files["app.bin"]
    require(len(program) == image_end - ENTRY, "app length differs from ELF image end")
    ranges = []
    for segment in layout["load_segments"]:
        if not segment["file_bytes"]:
            continue
        start = segment["lma"] - ENTRY
        end = start + segment["file_bytes"]
        offset = segment["offset"]
        require(program[start:end] == elf[offset:offset + end - start],
                "packaged bytes differ from ELF load segment")
        ranges.append((start, end))
    cursor = 0
    for start, end in sorted(ranges):
        require(program[cursor:start] == b"\xff" * (start - cursor), "ELF alignment gap is not erased fill")
        cursor = end
    require(program[cursor:] == b"\xff" * (len(program) - cursor), "ELF tail is not erased fill")
    program_end = directory["app.bin"].offset + len(program)
    config = directory["cfg_tool.bin"]
    require(program_end <= config.offset, "app executable overlaps the preserved MINI cfg_tool.bin")
    require(decoded[program_end:config.offset] == b"\xff" * (config.offset - program_end),
            "old executable bytes remain after the new program")
    tail_start = config.offset + config.size
    require(decoded[tail_start:] == b"\xff" * (len(decoded) - tail_start), "unexpected bytes after cfg_tool")
    return {"all_jlfs_crcs_valid": area["application_crc_and_file_crcs_valid"],
            "all_elf_load_bytes_match": True, "initialized_ram_uses_lma": True,
            "nobits_not_serialized": True, "old_executable_removed": True,
            "mini_region_records_identical": True, "cfg_tool_identical": True,
            "erased_alignment_and_payload_gaps": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, required=True)
    parser.add_argument("--stock", type=Path, default=ROOT / "artifacts/tank-mini/TANK-MINI.fwsc")
    parser.add_argument("--output", type=Path, required=True,
                        help="experimental application-area slice; not a FWSC or full-flash image")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        require(args.output.resolve() not in (args.elf.resolve(), args.stock.resolve()),
                "output must not overwrite an input")
        if args.report:
            require(args.report.resolve() not in (args.output.resolve(), args.elf.resolve(), args.stock.resolve()),
                    "report must not overwrite an input or image")
        output, report = build_application(args.elf.read_bytes(), args.stock.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(output)
        # Verify the actual saved bytes as well.
        verify_application(args.output.read_bytes(), args.elf.read_bytes(), args.stock.read_bytes())
        report["artifact"] = args.output.name
        report["builder"] = {"source": "tools/package_mini_probe.py", "sha256": sha256(Path(__file__).read_bytes())}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({key: report[key] for key in ("artifact", "bytes", "app_payload_bytes",
                          "app_area_sha256", "status", "boot_verified_on_device")}, indent=2))
    except (ValueError, OSError, struct.error) as error:
        parser.exit(2, f"MINI composition refused: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
