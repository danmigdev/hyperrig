"""Audit whole-function replacements while preserving earlier fragment evidence.

The original inventory tool and historical outputs remain unchanged. Only four
explicitly reviewed fragment/parent relationships are accepted by this adapter.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from inventory_reverse import Inventory, ROOT, address, hex_address, sha

EXPANSION_RUNS = (
    "reverse-capture-journal-02", "reverse-capture-dispatch-03", "reverse-biquad-pipeline-01",
    "reverse-dsp-initialization-01", "reverse-capture-reset-03", "reverse-capture-command-01",
)
CONTAINED = {
    (0x02032586, 0x02032618): ((0x02031C64, 0x0203291C), "parser_fragment"),
    (0x020327DE, 0x0203280C): ((0x02031C64, 0x0203291C), "parser_fragment"),
    (0x0200AB96, 0x0200AC36): ((0x0200A888, 0x0200AD06), "command_fragment"),
    (0x0200ACB4, 0x0200ACDE): ((0x0200A888, 0x0200AD06), "command_fragment"),
}


def coverage_summary(report):
    """Normalize declared counters without inventing a combined execution run."""
    coverage = report.get("instruction_coverage", {})
    decoded = visited = None
    missing_addresses = None
    scope = "newly added instructions"
    if "new_decoded" in coverage:
        decoded, visited = coverage["new_decoded"], coverage["new_visited"]
        missing_addresses = coverage.get("unvisited_new")
    elif "decoded" in coverage:
        decoded, visited = coverage["decoded"], coverage["visited"]
        missing_addresses = coverage.get("unvisited")
        scope = "module instructions"
    elif coverage and all(isinstance(value, dict) and "decoded" in value for value in coverage.values()):
        decoded = sum(value["decoded"] for value in coverage.values())
        visited = sum(value["visited"] for value in coverage.values())
        if all("unvisited" in value for value in coverage.values()):
            missing_addresses = [pc for value in coverage.values() for pc in value["unvisited"]]
        scope = "sum of the module's named instruction regions"
    else:
        for decoded_key, visited_key in (
                ("new_decoded_instructions", "new_visited_instructions"),
                ("new_instructions_decoded", "new_instructions_visited"),
                ("all_new_instructions", "visited_new_instructions")):
            if decoded_key in report:
                decoded, visited = report[decoded_key], report[visited_key]
                break
    if decoded is None:
        return {"status": "not_recorded_in_report", "decoded": None, "visited": None,
                "unvisited": None, "unvisited_addresses": None,
                "note": "Recorded comparisons do not supply an instruction-coverage count."}
    if not isinstance(decoded, int) or not isinstance(visited, int) or not 0 <= visited <= decoded:
        raise ValueError("invalid module instruction counters")
    missing = decoded - visited
    if missing_addresses is not None:
        missing_addresses = [address(value) for value in missing_addresses]
        if len(missing_addresses) != len(set(missing_addresses)) or len(missing_addresses) != missing:
            raise ValueError("module missing-instruction list disagrees with its counters")
    combined_decoded = coverage.get("all_decoded", coverage.get("combined_decoded"))
    combined_visited = coverage.get("all_visited", coverage.get("combined_visited"))
    for decoded_key, visited_key in (("combined_decoded_instructions", "combined_visited_instructions"),
                                     ("combined_instructions_decoded", "combined_instructions_visited")):
        if decoded_key in report:
            combined_decoded, combined_visited = report[decoded_key], report[visited_key]
    if combined_decoded is not None and (not isinstance(combined_decoded, int)
            or not isinstance(combined_visited, int) or not 0 <= combined_visited <= combined_decoded):
        raise ValueError("invalid combined instruction counters")
    classifications = coverage.get("unvisited_by_entry_invariant")
    classified = set()
    if classifications is not None:
        normalized = {}
        for reason, values in classifications.items():
            values = [address(value) for value in values]
            if len(values) != len(set(values)) or classified.intersection(values):
                raise ValueError("overlapping missing-instruction classifications")
            classified.update(values)
            normalized[reason] = list(map(hex_address, values))
        if missing_addresses is None or not classified.issubset(missing_addresses):
            raise ValueError("classified instruction is not listed as unvisited")
        classifications = normalized
    unclassified = coverage.get("unclassified_unvisited")
    if unclassified is not None:
        unclassified = [address(value) for value in unclassified]
        if (missing_addresses is None or len(unclassified) != len(set(unclassified))
                or set(unclassified) != set(missing_addresses) - classified):
            raise ValueError("unclassified instruction list disagrees with its classifications")
    return {"status": "recorded", "scope": scope, "decoded": decoded, "visited": visited,
            "unvisited": missing,
            "unvisited_addresses": None if missing_addresses is None else list(map(hex_address, missing_addresses)),
            "reported_entry_invariant_classifications": classifications,
            "reported_unclassified_unvisited": None if unclassified is None else list(map(hex_address, unclassified)),
            "combined_decoded": combined_decoded, "combined_visited": combined_visited,
            "combined_unvisited": None if combined_decoded is None else combined_decoded - combined_visited,
            "note": "Counts belong to this report's corpus; inherited instructions overlap other reports."}


class ExpandedInventory(Inventory):
    def __init__(self, parser_report=None, additional_reports=()):
        self.archived_fragments = {}
        additions = [f"build/{run}/verification.json" for run in EXPANSION_RUNS]
        if parser_report:
            additions.append(parser_report)
        super().__init__([*additions, *additional_reports])

    def archive(self, key, region):
        if key in self.archived_fragments:
            old = self.archived_fragments[key]
            if (old["sha256"], old["kind"]) != (region["sha256"], region["kind"]):
                raise ValueError("conflicting archived fragment evidence")
            old["evidence"].extend(region["evidence"])
        else:
            self.archived_fragments[key] = region

    def add_region(self, module, name, start, end, digest, kind="function_region", return_only=False):
        key = address(start), address(end)
        if key in CONTAINED:
            parent, expected_kind = CONTAINED[key]
            if kind != expected_kind or return_only:
                raise ValueError("known interior fragment must not be declared a whole function")
            if parent in self.regions:
                if self.regions[parent]["kind"] != "function_region" or sha(self.raw(*key)) != digest:
                    raise ValueError("fragment/parent byte or kind evidence disagrees")
                self.archive(key, {"start": hex_address(key[0]), "end_exclusive": hex_address(key[1]),
                    "bytes": key[1] - key[0], "sha256": digest, "kind": kind, "return_only": False,
                    "evidence": [{"module": module, "name": name}]})
                return
        for old in self.regions:
            if old == key or old[1] <= key[0] or key[1] <= old[0]:
                continue
            if old not in CONTAINED or CONTAINED[old][0] != key or kind != "function_region":
                raise ValueError(f"unknown overlapping regions: {old[0]:#x}..{old[1]:#x}, {key[0]:#x}..{key[1]:#x}")
        super().add_region(module, name, *key, digest, kind, return_only)
        for child, (parent, expected_kind) in CONTAINED.items():
            if parent == key and child in self.regions:
                if self.regions[child]["kind"] != expected_kind:
                    raise ValueError("contained fragment classification changed")
                self.archive(child, self.regions.pop(child))

    def reports(self):
        omitted = super().reports()
        if set(self.archived_fragments) != set(CONTAINED):
            raise ValueError("expanded inventory requires both complete parents and all four prior fragments")
        for key, region in self.archived_fragments.items():
            parent = CONTAINED[key][0]
            record = self.regions[parent]
            if not parent[0] < key[0] < key[1] < parent[1]:
                raise ValueError("reviewed fragment is not strictly inside its parent")
            region["parent"] = {"start": record["start"], "end_exclusive": record["end_exclusive"],
                "sha256": record["sha256"], "evidence": list(record["evidence"])}
            region["counted_as_additional_region"] = False
            region["decoded_instructions"] = len(self.decode(*key))
        for module in self.modules:
            report = json.loads(self.read(module["report"]))
            module["instruction_coverage"] = coverage_summary(report)
            module["reported_region_coverage"] = {}
            for name, region in report.get("functions", report.get("regions", {})).items():
                if "decoded" not in region or "visited" not in region:
                    continue
                decoded, visited = region["decoded"], region["visited"]
                if not isinstance(decoded, int) or not isinstance(visited, int) or not 0 <= visited <= decoded:
                    raise ValueError("invalid reported region coverage")
                module["reported_region_coverage"][name] = {
                    "decoded": decoded, "visited": visited, "unvisited": decoded - visited}
        return omitted

    def run(self):
        result = super().run()
        self.read("tools/inventory_reverse_expanded.py")
        result["schema"] = 2
        result["inventory_adapter"] = "tools/inventory_reverse_expanded.py"
        archived = [self.archived_fragments[key] for key in sorted(self.archived_fragments)]
        result["archived_contained_fragments"] = archived
        kinds = Counter(region["kind"] for region in archived)
        result["summary"].update({"archived_contained_fragments": len(archived),
            "archived_parser_fragments": kinds["parser_fragment"],
            "archived_command_fragments": kinds["command_fragment"],
            "fragment_bytes_already_counted_in_parents": sum(region["bytes"] for region in archived),
            "total_reported_region_records_after_exact_deduplication": len(self.regions) + len(archived)})
        coverage = [{"module": module["module"], "report": module["report"],
                     **module["instruction_coverage"]} for module in self.modules]
        result["instruction_coverage_by_report"] = coverage
        result["instruction_coverage_limits"] = {
            "reports_with_unvisited_new_or_module_instructions": [row["report"] for row in coverage if row.get("unvisited")],
            "reports_without_instruction_counts": [row["report"] for row in coverage if row["status"] != "recorded"],
            "aggregate_execution_coverage": None,
            "note": "Different corpora and inherited regions overlap; their counts are not summed into a global execution percentage."}
        result["audits"].update({"known_containments_audited": len(archived),
            "unknown_overlaps": False, "archived_fragment_hashes_match": True})
        result["scope_policy"].extend([
            "exactly four known fragments are archived under their complete parents and never counted twice",
            "all other differing overlapping ranges are rejected for explicit review",
            "whole reconstructed function boundaries do not imply every instruction or path has been exercised",
            "module execution gaps and missing counters remain explicit; no global coverage percentage is inferred"])
        result["input_sha256"] = dict(sorted(self.sources.items()))
        return result


def self_test():
    """Check ordering, deduplication and overlap rejection against pinned bytes."""
    inventory = ExpandedInventory()
    checks = 0
    def clear():
        inventory.regions, inventory.entries, inventory.archived_fragments = {}, {}, {}
    def add(bounds, kind):
        inventory.add_region("self-test", "region", *bounds, sha(inventory.raw(*bounds)), kind)
    for child, (parent, kind) in CONTAINED.items():
        for parent_first in (False, True):
            clear()
            for bounds, classification in ((parent, "function_region"), (child, kind)) if parent_first else ((child, kind), (parent, "function_region")):
                add(bounds, classification)
            add(child, kind)
            if set(inventory.regions) != {parent} or set(inventory.archived_fragments) != {child}:
                raise AssertionError("known fragment was not archived exactly once")
            if len(inventory.archived_fragments[child]["evidence"]) != 2:
                raise AssertionError("duplicate fragment provenance was lost")
            checks += 1
        for bad, bad_kind in (((parent[0] + 2, parent[0] + 4), "function_region"), (child, "function_region")):
            clear()
            add(parent, "function_region")
            try:
                add(bad, bad_kind)
            except ValueError:
                checks += 1
            else:
                raise AssertionError("unknown overlap or fragment misclassification accepted")
    clear()
    child, (parent, kind) = next(iter(CONTAINED.items()))
    add(parent, "function_region")
    try:
        inventory.add_region("self-test", "bad-hash", *child, "0" * 64, kind)
    except ValueError:
        checks += 1
    else:
        raise AssertionError("bad archived-fragment hash accepted")
    for decoded, visited, missing in ((5, 4, [0x02000120]), (5, 5, [])):
        row = coverage_summary({"instruction_coverage": {"new_decoded": decoded, "new_visited": visited, "unvisited_new": missing}})
        if row["unvisited"] != len(missing):
            raise AssertionError("coverage normalization failed")
        checks += 1
    try:
        coverage_summary({"instruction_coverage": {"new_decoded": 5, "new_visited": 4, "unvisited_new": []}})
    except ValueError:
        checks += 1
    else:
        raise AssertionError("contradictory instruction coverage accepted")
    row = coverage_summary({"instruction_coverage": {"new_decoded": 5, "new_visited": 4,
        "unvisited_new": [0x02000120], "unvisited_by_entry_invariant": {"bounded-entry": [0x02000120]},
        "unclassified_unvisited": []}})
    if row["reported_unclassified_unvisited"] != []:
        raise AssertionError("reported coverage classification was not preserved")
    checks += 1
    try:
        coverage_summary({"instruction_coverage": {"new_decoded": 5, "new_visited": 4,
            "unvisited_new": [0x02000120], "unvisited_by_entry_invariant": {"bad": [0x02000124]}}})
    except ValueError:
        checks += 1
    else:
        raise AssertionError("classification outside missing-instruction list accepted")
    print(json.dumps({"self_test_checks": checks, "result": "pass"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new report directory under build/")
    parser.add_argument("--check", action="store_true", help="audit without writing files")
    parser.add_argument("--self-test", action="store_true", help="check exact containment and coverage policies")
    parser.add_argument("--parser-report", help="explicit frozen whole-parser verification.json under build/")
    parser.add_argument("--add-report", action="append", default=[], help="additional frozen verification.json under build/")
    args = parser.parse_args()
    if args.self_test:
        if args.output or args.check or args.parser_report or args.add_report:
            parser.error("--self-test is a separate read-only operation")
        self_test()
        return
    if bool(args.output) == bool(args.check) or not args.parser_report:
        parser.error("choose --output or --check, and provide --parser-report")
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT / "build")):
        parser.error("use a new output directory under build/")
    report = ExpandedInventory(args.parser_report, args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output / "inventory.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
        manifest = {"component": "expanded-reverse-engineering-inventory", "device_access": False,
                    "files": {"inventory.json": sha((output / "inventory.json").read_bytes())}}
        (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "audits": report["audits"],
                      "instruction_coverage_limits": report["instruction_coverage_limits"]}, indent=2))


if __name__ == "__main__":
    main()
