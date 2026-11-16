"""Extend the immutable reverse inventory with the verified IR coefficient table."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import struct

from inventory_reverse import ROOT, REFERENCE_SHA, address, hex_address, local, sha
from inventory_reverse_runtime import RuntimeInventory

TABLE_START, TABLE_END = 0x0203BE2C, 0x0203BE50
CONSUMER_START, CONSUMER_END = 0x02031404, 0x02031542
ADDRESS_LOAD = (0x0203143C, 6, f"r2 = {TABLE_START}")
TABLE_WORDS = (338786260, 0xF9A9ECD2, 56405688, 0xFE033D22, 19931383,
               0xFF505ACC, 6180000, 0xFFD30C28, 1235701)
TABLE_BYTES = struct.pack("<9I", *TABLE_WORDS)


def ir_table_evidence(report, raw, consumer_raw, decoded):
    """Bind the exact data words and their decoded original address load."""
    if report.get("result") != "pass" or report.get("original_image_sha256") != REFERENCE_SHA:
        raise ValueError("IR coefficient table requires a passing pinned-image report")
    try:
        record = report["resampling_coefficients"]
        bounds = address(record["start"]), address(record["end_exclusive"])
        consumer = report.get("functions", report.get("regions"))["resample"]
        consumer_bounds = address(consumer["start"]), address(consumer["end_exclusive"])
        digest, words = record["sha256"], record["signed_words"]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("missing or malformed IR table evidence") from error
    if bounds != (TABLE_START, TABLE_END) or raw != TABLE_BYTES:
        raise ValueError("unreviewed IR coefficient table range or bytes")
    if digest != sha(raw) or words != list(struct.unpack("<9i", raw)):
        raise ValueError("IR coefficient hash or signed words disagree with original bytes")
    if (consumer_bounds != (CONSUMER_START, CONSUMER_END)
            or consumer.get("bytes_sha256", consumer.get("sha256")) != sha(consumer_raw)
            or ADDRESS_LOAD not in decoded):
        raise ValueError("IR table lacks its reviewed resampling consumer and address load")
    return {"start": hex_address(TABLE_START), "end_exclusive": hex_address(TABLE_END),
        "bytes": len(raw), "sha256": sha(raw), "signed_words": words,
        "consumer": list(map(hex_address, consumer_bounds)),
        "consumer_sha256": sha(consumer_raw), "address_load_site": hex_address(ADDRESS_LOAD[0]),
        "address_load_instruction": ADDRESS_LOAD[2], "kind": "ir_resampling_coefficients"}


class DspInventory(RuntimeInventory):
    def __init__(self, parser_report, processing_report, ir_report, additional_reports=()):
        self.ir_report = local(ir_report).relative_to(ROOT).as_posix()
        self.ir_coefficients = None
        super().__init__(parser_report, processing_report, [self.ir_report, *additional_reports])

    def add_known_data(self):
        super().add_known_data()
        report = json.loads(self.read(self.ir_report))
        self.ir_coefficients = ir_table_evidence(report, self.raw(TABLE_START, TABLE_END),
            self.raw(CONSUMER_START, CONSUMER_END), self.decode(CONSUMER_START, CONSUMER_END))
        self.ir_coefficients["report"] = self.ir_report
        if any(start < TABLE_END and TABLE_START < end for start, end, _ in self.data_ranges):
            raise ValueError("IR coefficient table overlaps an existing data exclusion")
        self.data_ranges.append((TABLE_START, TABLE_END, "ir_resampling_coefficients"))

    def reports(self):
        omitted = super().reports()
        for module in self.modules:
            if module.get("joined_region_coverage") and module["instruction_coverage"].get("decoded"):
                # The older adapter's integration-only note is too narrow for
                # a joined corpus containing both new and reused functions.
                module["joined_region_coverage"]["note"] = (
                    "Joined corpus covers this report's declared original regions; "
                    "new functions are counted once and reused functions add no entries.")
        return omitted

    def run(self):
        report = super().run()
        self.read("tools/inventory_reverse_dsp.py")
        report["schema"] = 4
        report["dsp_inventory_adapter"] = "tools/inventory_reverse_dsp.py"
        report["ir_resampling_coefficients"] = self.ir_coefficients
        report["audits"].update({"ir_resampling_table_matches_original_and_report": True,
                                "ir_resampling_address_load_verified": True})
        report["scope_policy"].append(
            "the verified 36-byte IR coefficient table is data, excluded from linear call sources and targets")
        report["input_sha256"] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Exercise new evidence and exclusion checks without changing reports."""
    consumer_raw = b"self-test consumer bytes"
    valid = {"result": "pass", "original_image_sha256": REFERENCE_SHA,
        "resampling_coefficients": {"start": TABLE_START, "end_exclusive": TABLE_END,
            "sha256": sha(TABLE_BYTES), "signed_words": list(struct.unpack("<9i", TABLE_BYTES))},
        "functions": {"resample": {"start": CONSUMER_START, "end_exclusive": CONSUMER_END,
            "bytes_sha256": sha(consumer_raw)}}}
    if ir_table_evidence(valid, TABLE_BYTES, consumer_raw, [ADDRESS_LOAD])["bytes"] != 36:
        raise AssertionError("valid IR table evidence rejected")
    checks = 1
    mutations = (((), "result", "fail"), ((), "original_image_sha256", "0" * 64),
        (("resampling_coefficients",), "start", TABLE_START + 2),
        (("resampling_coefficients",), "end_exclusive", TABLE_END - 2),
        (("resampling_coefficients",), "sha256", "0" * 64),
        (("resampling_coefficients",), "signed_words", list(TABLE_WORDS)),
        (("functions", "resample"), "start", CONSUMER_START + 2),
        (("functions", "resample"), "bytes_sha256", "0" * 64),
        ((), "resampling_coefficients", {}))
    for path, key, value in mutations:
        bad = copy.deepcopy(valid)
        node = bad
        for part in path:
            node = node[part]
        node[key] = value
        try:
            ir_table_evidence(bad, TABLE_BYTES, consumer_raw, [ADDRESS_LOAD])
        except ValueError:
            checks += 1
        else:
            raise AssertionError("invalid IR table evidence accepted")
    for raw, consumer, decoded in ((TABLE_BYTES[:-1], consumer_raw, [ADDRESS_LOAD]),
        (b"\x00" * 36, consumer_raw, [ADDRESS_LOAD]), (TABLE_BYTES, b"wrong", [ADDRESS_LOAD]),
        (TABLE_BYTES, consumer_raw, []), (TABLE_BYTES, consumer_raw, [(ADDRESS_LOAD[0], 6, "r2 = 0")])):
        try:
            ir_table_evidence(valid, raw, consumer, decoded)
        except ValueError:
            checks += 1
        else:
            raise AssertionError("unbound IR bytes or consumer accepted")
    # Exercise the inherited source/target classifier at both table endpoints.
    inventory = object.__new__(DspInventory)
    inventory.flash_start, inventory.flash_end = 0x02000120, 0x02080000
    inventory.ram_source, inventory.ram_size = 0x02056780, 0x2030C
    inventory.ram_start, inventory.ram_end = 0x01C00000, 0x01C2030C
    inventory.data_ranges = [(TABLE_START, TABLE_END, "ir_resampling_coefficients")]
    for pc, expected in ((TABLE_START - 2, "flash_outside_known_data"),
        (TABLE_START, "ir_resampling_coefficients"), (TABLE_END - 1, "ir_resampling_coefficients"),
        (TABLE_END, "flash_outside_known_data")):
        if inventory.classification(pc) != expected:
            raise AssertionError("IR data exclusion boundary changed")
        checks += 1
    print(json.dumps({"self_test_checks": checks, "result": "pass"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parser-report")
    parser.add_argument("--processing-report")
    parser.add_argument("--ir-report")
    parser.add_argument("--add-report", action="append", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.output or args.check or args.parser_report or args.processing_report or args.ir_report or args.add_report:
            parser.error("--self-test is a separate read-only operation")
        self_test()
        return
    if bool(args.output) == bool(args.check) or not all((args.parser_report, args.processing_report, args.ir_report)):
        parser.error("choose --output or --check and provide parser, processing and IR reports")
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT / "build")):
        parser.error("use a new output directory under build/")
    report = DspInventory(args.parser_report, args.processing_report, args.ir_report, args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output / "inventory.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
        manifest = {"component": "dsp-reverse-engineering-inventory", "device_access": False,
            "files": {"inventory.json": sha((output / "inventory.json").read_bytes())}}
        (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "audits": report["audits"],
        "instruction_coverage_limits": report["instruction_coverage_limits"]}, indent=2))


if __name__ == "__main__":
    main()
