"""Extend the immutable reverse inventory with the native capture dispatch table."""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path

from inventory_reverse import ROOT, address, hex_address, local, sha, REFERENCE_SHA, codec
from inventory_reverse_expanded import ExpandedInventory


def joined_coverage(coverage, instructions):
    """Bind the joined corpus to its already reconstructed instruction set."""
    decoded, visited = coverage["joined_decoded"], coverage["joined_visited"]
    missing = [address(value) for value in coverage["unvisited_joined"]]
    if (not isinstance(decoded, int) or not isinstance(visited, int) or not 0 <= visited <= decoded
            or len(missing) != len(set(missing)) or len(missing) != decoded - visited
            or decoded != len(instructions) or not set(missing).issubset(instructions)):
        raise ValueError("inconsistent joined-region instruction counts or addresses")
    return {"decoded": decoded, "visited": visited,
        "unvisited": len(missing), "unvisited_addresses": list(map(hex_address, missing)),
        "note": "An integration corpus reuses already counted functions; it adds no original function."}


def processing_dispatch(bounds, raw, decoded, parallel_seconds):
    """Review the exact embedded table and its executable packet destinations."""
    if bounds != (0x01C12BF2, 0x01C12BF6) or raw != bytes((2, 26, 14, 20)):
        raise ValueError("unreviewed capture processing table bytes or range")
    instructions = {pc: (size, text) for pc, size, text in decoded}
    site = bounds[0] - 2
    if instructions.get(site) != (2, "tbb [r1]"):
        raise ValueError("capture processing table lacks its reviewed dispatch instruction")
    targets = [bounds[0] + 2 * value for value in raw]
    if (any(target not in instructions or target in parallel_seconds for target in targets)
            or any(bounds[0] <= pc < bounds[1] for pc in instructions)):
        raise ValueError("capture table bytes or targets are not valid instruction packets")
    return site, targets


class RuntimeInventory(ExpandedInventory):
    def __init__(self, parser_report, processing_report, additional_reports=()):
        self.processing_report = local(processing_report).relative_to(ROOT).as_posix()
        self.processing_table = None
        super().__init__(parser_report, [self.processing_report, *additional_reports])

    def add_known_data(self):
        super().add_known_data()
        report = json.loads(self.read(self.processing_report))
        if report.get("result") != "pass" or report.get("original_image_sha256") != REFERENCE_SHA:
            raise ValueError("capture processing table needs a passing pinned-image report")
        record = report["table"]
        bounds = address(record["start"]), address(record.get("end_exclusive", record.get("end")))
        tree = ast.parse(self.read("tools/capture_processing_machine.py").decode("utf-8"))
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Tuple) and [item.id for item in target.elts] == ["TABLE_START", "TABLE_END"]
                    for target in node.targets))
        if bounds != (0x01C12BF2, 0x01C12BF6) or ast.literal_eval(assignment.value) != bounds:
            raise ValueError("unreviewed capture processing table range")
        raw = self.raw(*bounds)
        if raw != bytes((2, 26, 14, 20)) or record["hex"] != raw.hex():
            raise ValueError("capture processing table differs from pinned bytes")
        parent = report.get("functions", report.get("regions"))["layer"]
        parent_bounds = address(parent["start"]), address(parent["end_exclusive"])
        if parent_bounds != (0x01C12A54, 0x01C12C32):
            raise ValueError("capture table lacks the reviewed whole dispatch parent")
        self.data_ranges.append((*bounds, "capture_processing_jump_table"))
        decoded = self.decode(*parent_bounds)
        parallel_seconds = set()
        for pc, size, _ in decoded:
            instruction, fields, decoded_size = codec.decode(self.instructions, self.raw(pc, pc + size), 0)
            if decoded_size != size:
                raise ValueError("capture instruction length changed during packet audit")
            if codec.format(instruction, fields).endswith("  #"):
                parallel_seconds.add(pc + size)
        site, targets = processing_dispatch(bounds, raw, decoded, parallel_seconds)
        self.processing_table = {"start": hex_address(bounds[0]), "end_exclusive": hex_address(bounds[1]),
            "sha256": sha(raw), "hex": raw.hex(), "targets": list(map(hex_address, targets)),
            "dispatch_site": hex_address(site), "dispatch_instruction": "tbb [r1]",
            "targets_are_packet_starts": True,
            "parent": list(map(hex_address, parent_bounds)), "report": self.processing_report}

    def reports(self):
        omitted = super().reports()
        for module in self.modules:
            report = json.loads(self.read(module["report"]))
            coverage = report.get("instruction_coverage", {})
            module["reported_coverage_notes"] = {
                key: value for key, value in coverage.items()
                if any(word in key for word in ("reason", "proof", "invariant", "classification"))}
            instructions = set()
            for function in report.get("functions", report.get("regions", {})).values():
                decoded = self.decode(address(function["start"]), address(function["end_exclusive"]))
                instructions.update(pc for pc, _, _ in decoded)
                for key in ("decoded", "instructions"):
                    if key in function and function[key] != len(decoded):
                        raise ValueError("reported function instruction count differs from pinned decoding")
            classifications = coverage.get("missing_classification", {})
            if classifications:
                missing = {address(value) for key in ("unvisited_new", "unvisited_all", "unvisited")
                           for value in coverage.get(key, [])}
                classified = {address(value) for value in classifications}
                if not classified.issubset(missing & instructions):
                    raise ValueError("reported classification does not identify an unvisited module instruction")
            if "joined_decoded" in coverage:
                module["joined_region_coverage"] = joined_coverage(coverage, instructions)
        return omitted

    def run(self):
        report = super().run()
        self.read("tools/inventory_reverse_runtime.py")
        report["schema"] = 3
        report["runtime_inventory_adapter"] = "tools/inventory_reverse_runtime.py"
        report["capture_processing_table"] = self.processing_table
        report["audits"]["capture_table_targets_are_parent_instructions"] = True
        report["audits"]["capture_table_targets_are_packet_starts"] = True
        report["audits"]["joined_coverage_bound_to_declared_instructions"] = True
        modules = {module["report"]: module for module in self.modules}
        for row in report["instruction_coverage_by_report"]:
            module = modules[row["report"]]
            row["reported_coverage_notes"] = module["reported_coverage_notes"]
            if "joined_region_coverage" in module:
                row["joined_region_coverage"] = module["joined_region_coverage"]
        report["instruction_coverage_limits"]["reports_with_unvisited_joined_instructions"] = [
            module["report"] for module in self.modules if module.get("joined_region_coverage", {}).get("unvisited")]
        report["scope_policy"].append(
            "capture dispatch table bytes belong to their enclosing function but are excluded from decoded instructions and candidate call sources")
        report["input_sha256"] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Exercise new audit policies without changing or rerunning old reports."""
    bounds = 0x01C12BF2, 0x01C12BF6
    raw = bytes((2, 26, 14, 20))
    targets = [bounds[0] + 2 * value for value in raw]
    decoded = [(bounds[0]-2, 2, "tbb [r1]")] + [(target, 2, "r0 = r9") for target in targets]
    site, actual = processing_dispatch(bounds, raw, decoded, set())
    assert site == bounds[0]-2 and actual == targets
    checks = 1
    for args in ((bounds, raw[:-1], decoded, set()), ((bounds[0],bounds[1]+2),raw,decoded,set()),
                 (bounds,raw,decoded[1:],set()), (bounds,raw,decoded[:-1],set()),
                 (bounds,raw,decoded,{targets[0]}), (bounds,raw,decoded+[(bounds[0],2,"r2 <<= r0")],set())):
        try: processing_dispatch(*args)
        except ValueError: checks += 1
        else: raise AssertionError("invalid processing table evidence accepted")
    instructions = {0x100, 0x104, 0x108}
    valid = {"joined_decoded": 3, "joined_visited": 2, "unvisited_joined": [0x104]}
    assert joined_coverage(valid,instructions)["unvisited_addresses"] == ["0x00000104"]
    checks += 1
    for changes in ({"joined_decoded":4}, {"joined_visited":4}, {"unvisited_joined":[]},
                    {"unvisited_joined":[0x102]}, {"joined_visited":1,"unvisited_joined":[0x104,0x104]}):
        try: joined_coverage(valid | changes,instructions)
        except ValueError: checks += 1
        else: raise AssertionError("invalid joined-corpus evidence accepted")
    print(json.dumps({"self_test_checks": checks, "result": "pass"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parser-report")
    parser.add_argument("--processing-report")
    parser.add_argument("--add-report", action="append", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.output or args.check or args.parser_report or args.processing_report or args.add_report:
            parser.error("--self-test is a separate read-only operation")
        self_test()
        return
    if bool(args.output) == bool(args.check) or not args.parser_report or not args.processing_report:
        parser.error("choose --output or --check and provide both parser/processing reports")
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT / "build")):
        parser.error("use a new output directory under build/")
    report = RuntimeInventory(args.parser_report, args.processing_report, args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output / "inventory.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
        manifest = {"component": "runtime-reverse-engineering-inventory", "device_access": False,
                    "files": {"inventory.json": sha((output / "inventory.json").read_bytes())}}
        (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "audits": report["audits"],
                      "instruction_coverage_limits": report["instruction_coverage_limits"]}, indent=2))


if __name__ == "__main__":
    main()
