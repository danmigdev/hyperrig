"""Inspect a local 1 MiB MINI NOR dump against pinned stock 009, read-only.

This never opens a device, decrypts in place, repairs a dump or writes firmware.
It preserves the distinction between two-read consistency and stock identity.
VM/BTIF/USR/key_mac are absent from FWSC flash.bin and MUST still match between
the two reads of the same unit. No field inside the package extent is silently
ignored, including configuration/key-prefix or erased padding differences.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import crc16, enc, jlfs_entry, unpack_app, unpack_fwsc

STOCK_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
NOR_BYTES = 0x100000
APP_BASE, APP_LIMIT = 0x4000, 0x82000
REGIONS = {"boot": (0, APP_BASE), "application": (APP_BASE, APP_LIMIT),
           "VM": (0x82000, 0xbe000), "BTIF": (0xbe000, 0xbf000),
           "USR": (0xbf000, 0xff000), "key_mac": (0xff000, 0x100000)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def difference(a, b, base=0):
    require(len(a) == len(b), "difference requires equal lengths")
    count, first = 0, []
    for index, (left, right) in enumerate(zip(a, b)):
        if left != right:
            count += 1
            if len(first) < 16:
                first.append(base + index)
    return {"equal": count == 0, "different_bytes": count, "first_different_physical_offsets": first}


def top_directory(raw):
    header = enc(raw[:32])
    require(crc16(header[2:]) == struct.unpack_from("<H", header)[0], "flash header CRC mismatch")
    entries = [replace(jlfs_entry(enc(raw[off:off + 32]), 0), header_offset=off)
               for off in range(32, 160, 32)]
    records = {record.name: record for record in entries}
    require(set(records) == {"uboot.boot", "isd_config.ini", "app_dir_head", "key_mac"},
            "top-level directory is not the supported MINI layout")
    require(records["app_dir_head"].offset == APP_BASE and records["app_dir_head"].size in (0, 0xffffffff),
            "unsupported application base/banked directory")
    return header, records


def boot_container(raw, record):
    require(record.flags == 0 and 16 < record.size and 0xa0 <= record.offset < APP_BASE and
            record.size <= APP_BASE - record.offset, "unsupported boot container bounds/attributes")
    encoded = raw[record.offset:record.offset + record.size]
    plain = enc(encoded[:16]) + enc(encoded[16:])
    banks, length, load, offset, payload_crc, header_crc = struct.unpack_from("<HHIIHH", plain)
    require((banks, load, offset) == (1, 0x01c02000, 16) and length + 16 == len(plain), "BANKCB geometry")
    require(crc16(plain[:14]) == header_crc, "BANKCB header CRC mismatch")
    require(crc16(plain[16:]) == payload_crc, "BANKCB payload CRC mismatch")
    require(crc16(plain) == record.data_crc, "boot directory payload CRC mismatch")
    return plain


def configuration(raw, record):
    require(record.flags == 2 and 34 <= record.size <= 4096 and 0xa0 <= record.offset < APP_BASE and
            record.size <= APP_BASE - record.offset, "unsupported configuration bounds/attributes")
    plain = raw[record.offset:record.offset + record.size]
    require(crc16(plain) == record.data_crc, "plain boot configuration CRC mismatch")
    require(crc16(plain[:32]) == struct.unpack_from("<H", plain, 32)[0], "configuration key-prefix CRC mismatch")
    threshold = sum(plain[:16]) & 255
    if threshold >= 0xe0:
        threshold = 0xaa
    elif threshold <= 0x10:
        threshold = 0x55
    key = sum((1 << i) for i in range(16) if (plain[16 + i] ^ plain[15 - i]) < threshold)
    return plain, key


def inspect_backup(dump: bytes, stock_package: bytes, second: bytes | None = None) -> dict:
    require(len(dump) == NOR_BYTES, "first dump must be exactly 1 MiB, never a FWSC/application slice")
    if second is not None:
        require(len(second) == NOR_BYTES, "second dump must be exactly 1 MiB")
    require(sha(stock_package) == STOCK_SHA, "stock FWSC differs from pinned MINI 009")
    _, stock_files = unpack_fwsc(stock_package)
    stock = stock_files["flash.bin"]
    require(len(stock) == APP_LIMIT, "stock flash.bin extent changed")
    stock_header, stock_records = top_directory(stock)
    stock_boot = boot_container(stock, stock_records["uboot.boot"])
    stock_config, stock_key = configuration(stock, stock_records["isd_config.ini"])
    stock_plain, stock_app_entries, stock_app_files = unpack_app(stock[APP_BASE:APP_LIMIT], stock_key)
    result = {"dump_bytes": len(dump), "dump_sha256": sha(dump), "stock_package_sha256": STOCK_SHA,
              "stock_flash_bytes": len(stock), "stock_flash_sha256": sha(stock),
              "reads_identical": second == dump if second is not None else None,
              "second_sha256": sha(second) if second is not None else None,
              "read_difference": difference(dump, second) if second is not None else None,
              "stock_prefix_comparison": difference(dump[:APP_LIMIT], stock),
              "regions": {}, "errors": [], "physical_efuse_read": False,
              "hardware_accessed": False, "restoration_authorized_or_verified": False}
    for name, (start, end) in REGIONS.items():
        data = dump[start:end]
        region = {"physical_range": [start, end], "bytes": len(data), "sha256": sha(data),
                  "stock_reference_available": end <= len(stock), "all_ff": all(v == 255 for v in data)}
        if end <= len(stock):
            region["stock_comparison"] = difference(data, stock[start:end], start)
        else:
            region["policy"] = "preserve exact unit bytes; absent from stock FWSC, still require equality between reads"
        if second is not None:
            region["between_reads"] = difference(data, second[start:end], start)
        result["regions"][name] = region
    records, candidate_keys = None, [(stock_key, "pinned stock configuration prefix")]
    try:
        header, records = top_directory(dump)
        result["top_directory"] = {"crc_valid": True, "header_plain_equal_to_stock": header == stock_header,
                                   "entries": [record.to_dict() for record in records.values()]}
    except (ValueError, struct.error, UnicodeDecodeError) as error:
        result["errors"].append("top_directory: " + str(error))
    if records:
        try:
            boot = boot_container(dump, records["uboot.boot"])
            result["boot"] = {"all_crcs_valid": True, "container_sha256": sha(boot),
                              "payload_sha256": sha(boot[16:]), "payload_bytes": len(boot) - 16,
                              "equal_to_stock": boot == stock_boot}
        except (ValueError, struct.error) as error:
            result["errors"].append("boot: " + str(error))
        try:
            config, key = configuration(dump, records["isd_config.ini"])
            result["configuration"] = {"all_crcs_valid": True, "sha256": sha(config),
                                       "equal_to_stock": config == stock_config,
                                       "key_prefix_equal_to_stock": config[:34] == stock_config[:34],
                                       "settings_equal_to_stock": config[34:] == stock_config[34:],
                                       "sfc_key_candidate": f"{key:04x}", "physical_efuse_key_established": False}
            candidate_keys = [(key, "CRC-valid dump configuration prefix")]
            if key != stock_key:
                candidate_keys.append((stock_key, "pinned stock configuration prefix"))
        except (ValueError, struct.error) as error:
            result["errors"].append("configuration: " + str(error))
    attempts = []
    for key, source in candidate_keys:
        try:
            # The app base must be its own cipher origin. It is NOT correct to
            # decrypt the whole NOR using absolute offsets in the SFC seed.
            plain, entries, files = unpack_app(dump[APP_BASE:], key)
        except (ValueError, struct.error, UnicodeDecodeError) as error:
            attempts.append({"key": f"{key:04x}", "source": source, "error": str(error)})
            continue
        file_checks = {name: {"bytes": len(data), "sha256": sha(data),
                              "present_in_stock": name in stock_app_files,
                              "equal_to_stock": data == stock_app_files.get(name)}
                       for name, data in files.items()}
        result["application"] = {"all_directory_and_payload_crcs_valid": True,
                                 "sfc_key_used": f"{key:04x}", "key_source": source,
                                 "entry": entries[0].offset, "declared_area_bytes": entries[0].size,
                                 "declared_area_plain_sha256": sha(plain[:entries[0].size]),
                                 "declared_area_plain_equal_to_stock":
                                     plain[:entries[0].size] == stock_plain[:stock_app_entries[0].size],
                                 "directory_equal_to_stock": [e.to_dict() for e in entries] ==
                                                               [e.to_dict() for e in stock_app_entries],
                                 "files": file_checks, "entries": [e.to_dict() for e in entries]}
        break
    else:
        result["errors"].append("application: no tested key passed all JLFS CRCs; possible key/layout difference or bad data")
    result["application_decode_attempts"] = attempts
    result["two_complete_reads_identical"] = second is not None and second == dump
    result["stock_content_checks_passed"] = not result["errors"]
    result["decoded_firmware_matches_stock_009"] = (
        result.get("boot", {}).get("equal_to_stock", False) and
        result.get("configuration", {}).get("settings_equal_to_stock", False) and
        result.get("application", {}).get("declared_area_plain_equal_to_stock", False))
    result["raw_package_extent_identical_to_stock"] = dump[:APP_LIMIT] == stock
    result["backup_consistency_and_content_validated"] = result["two_complete_reads_identical"] and not result["errors"]
    result["notes"] = ["Two identical reads are necessary but do not prove the reader's physical mapping by themselves.",
                       "FWSC flash.bin ends at 0x82000. Its outer isd_config.ini is an opaque auxiliary file, not the plain on-flash boot configuration.",
                       "No bytes inside the stock package extent are automatically excluded from comparison.",
                       "VM, BTIF, USR and key_mac have no stock reference here; preserve their full unit-specific contents.",
                       "A configuration-prefix SFC key is not a measurement of physical efuse.",
                       "This report is not authorization or an automatic restoration recipe."]
    return result


def self_test(stock_package):
    _, files = unpack_fwsc(stock_package)
    stock = files["flash.bin"]
    baseline = stock + bytes((i * 73 + 19) & 255 for i in range(NOR_BYTES - len(stock)))
    first = inspect_backup(baseline, stock_package, baseline)
    require(first["backup_consistency_and_content_validated"] and first["raw_package_extent_identical_to_stock"], "baseline check")
    changed_tail = bytearray(baseline)
    changed_tail[0xfff40] ^= 1
    different = inspect_backup(baseline, stock_package, bytes(changed_tail))
    require(not different["two_complete_reads_identical"] and different["read_difference"]["different_bytes"] == 1,
            "unit data difference must not be ignored between reads")
    identical_changed_tail = inspect_backup(bytes(changed_tail), stock_package, bytes(changed_tail))
    require(identical_changed_tail["backup_consistency_and_content_validated"], "unit data must not be compared to absent stock")
    bad_app = bytearray(baseline)
    bad_app[0x4120] ^= 1
    invalid = inspect_backup(bytes(bad_app), stock_package, bytes(bad_app))
    require(invalid["two_complete_reads_identical"] and not invalid["stock_content_checks_passed"], "CRC must reject consistent bad app bytes")
    try:
        inspect_backup(baseline[:-1], stock_package)
    except ValueError:
        pass
    else:
        raise ValueError("truncated dump accepted")
    return {"offline_synthetic_cases": 5, "passed": True, "physical_dump_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path, nargs="?")
    parser.add_argument("--second", type=Path)
    parser.add_argument("--stock", type=Path, default=ROOT / "artifacts/tank-mini/TANK-MINI.fwsc")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    package = args.stock.read_bytes()
    if args.self_test:
        require(args.dump is None and args.second is None and args.report is None, "self-test does not accept dump/output paths")
        print(json.dumps(self_test(package), indent=2))
        return 0
    if args.dump is None:
        parser.error("provide a local dump or --self-test")
    result = inspect_backup(args.dump.read_bytes(), package, args.second.read_bytes() if args.second else None)
    result["inputs"] = {"dump": str(args.dump), "second": str(args.second) if args.second else None, "stock": str(args.stock)}
    if args.report:
        inputs = {p.resolve() for p in (args.dump, args.second, args.stock) if p}
        require(args.report.resolve() not in inputs, "report cannot overwrite an input")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["stock_content_checks_passed"] and (args.second is None or result["two_complete_reads_identical"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
