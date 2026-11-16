"""Audit reconstructed regions and inventory candidate entries in pinned M5.71.

This is an offline evidence inventory, not a function-discovery proof or a
firmware-completion percentage. Generated reports belong only under build/.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "upstream/pi32v2-isa"))
from hyperrig.jieli import unpack_app
from pi32v2isa import codec, table

REFERENCE = "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
REFERENCE_SHA = "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
APP = "analysis/firmware/m571_g_app/app.bin"
LAYOUT = "analysis/firmware/m571_g_app/memory-layout.json"
NATIVE_REPORT = "research/native-verification.json"
GHIDRA = "recovered/ghidra/tank-g-v2/functions.tsv"
BASELINE_COMMIT = "1b235a5a284f100e47c66b6b4ab43c48cdff10cb"
BASELINE_RUNS = (
    "reverse-biquad-01", "reverse-biquad-chain-01", "reverse-biquad-coefficients-01",
    "reverse-biquad-generator-01", "reverse-capture-container-01", "reverse-capture-loader-01",
    "reverse-capture-metadata-01", "reverse-control-actions-01", "reverse-controls-02",
    "reverse-ir-loader-02", "reverse-preset-assets-01", "reverse-preset-loader-01",
    "reverse-preset-preflight-01", "reverse-preset-storage-01", "reverse-selection-01",
)
# These exact ranges are continuations inside the command at 0x0200a888.
# A passing comparison report does not turn an interior entry into a function.
COMMAND_FRAGMENTS = {(0x0200AB96, 0x0200AC36), (0x0200ACB4, 0x0200ACDE)}
LINE = re.compile(r"^([0-9a-f]{8})\s+((?:[0-9a-f]{2}\s+)*[0-9a-f]{2})\s{2,}(.*)$")
DIRECT_CALL = re.compile(r"call (-?\d+)$")
BRANCH = re.compile(r"(?:^| )goto (-?\d+)$")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def address(value):
    return int(value, 0) if isinstance(value, str) else value


def hex_address(value):
    return f"0x{value:08x}"


def local(name):
    path = (ROOT / name).resolve(strict=True)
    if not path.is_relative_to(ROOT):
        raise ValueError("an inventory input escaped the workspace")
    return path


class Inventory:
    def __init__(self, additional_reports=()):
        self.additional_reports = additional_reports
        self.sources = {}
        self.audited_sources, self.audited_artifacts = set(), set()
        self.instructions = table.load()
        original = self.read(REFERENCE)
        if sha(original) != REFERENCE_SHA:
            raise ValueError("reference differs from pinned Alpha11 G v2 M5.71")
        self.app = self.read(APP)
        if unpack_app(original)[2]["app.bin"] != self.app:
            raise ValueError("decoded application differs from pinned original")
        self.layout = json.loads(self.read(LAYOUT))
        expected = (0x02000120, 0x02056780, 0x01C00000, 0x2030C)
        actual = tuple(self.layout[key] for key in ("flash_base", "ram_source", "ram_destination", "ram_size"))
        if actual != expected:
            raise ValueError("unreviewed executable mapping")
        self.flash_start, self.ram_source, self.ram_start, self.ram_size = actual
        self.flash_end = self.flash_start + len(self.app)
        self.ram_end = self.ram_start + self.ram_size
        self.entries = {}
        self.modules = []
        self.regions = {}
        self.data_ranges = []
        self.add_known_data()

    def read(self, name):
        data = local(name).read_bytes()
        self.sources[Path(name).as_posix()] = sha(data)
        return data

    def raw(self, start, end):
        if self.flash_start <= start < end <= self.flash_end:
            offset = start - self.flash_start
        elif self.ram_start <= start < end <= self.ram_end:
            offset = self.ram_source - self.flash_start + start - self.ram_start
        else:
            raise ValueError(f"range outside pinned image: {hex_address(start)}..{hex_address(end)}")
        return self.app[offset:offset + end - start]

    def add_known_data(self):
        # This artifact has a recorded original hash. Match its bytes in the
        # decoded image, rather than infer an address from decompiler labels.
        capture_name = "analysis/firmware/m571_g_app/embedded-0.a2l"
        capture = self.read(capture_name)
        native = json.loads(self.read(NATIVE_REPORT))
        expected = native["a2l_loader"]["embedded_capture_sha256"]
        if sha(capture) != expected:
            raise ValueError("embedded A2 capture differs from native evidence")
        offset = self.app.find(capture)
        if offset < 0 or self.app.find(capture, offset + 1) >= 0:
            raise ValueError("embedded capture does not have a unique original location")
        self.data_ranges.append((self.flash_start + offset, self.flash_start + offset + len(capture), "embedded_A2_capture"))
        # This data span sits inside a reviewed function range. Its bytes must
        # not become instructions or extra function candidates in the audit.
        tree = ast.parse(self.read("tools/control_action_machine.py").decode("utf-8"))
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Tuple) and [item.id for item in target.elts] == ["TABLE_START", "TABLE_END"]
                    for target in node.targets))
        start, end = ast.literal_eval(assignment.value)
        self.data_ranges.append((start, end, "action_jump_table"))

    def classification(self, location):
        if self.ram_source <= location < self.ram_source + self.ram_size:
            return "flash_copy_of_initialized_ram"
        for start, end, name in self.data_ranges:
            if start <= location < end:
                return name
        if self.ram_start <= location < self.ram_end:
            return "initialized_ram"
        if self.flash_start <= location < self.flash_end:
            return "flash_outside_known_data"
        return "outside_application_mappings"

    def candidate(self, location, evidence):
        item = self.entries.setdefault(location, {"address": hex_address(location),
            "mapping": self.classification(location), "evidence": set(),
            "direct_call_sites": [], "ghidra_status": None})
        item["evidence"].add(evidence)
        return item

    def audit_sources(self, expected):
        for filename, digest in expected.items():
            if sha(self.read(filename)) != digest:
                raise ValueError(f"reconstructed source no longer matches its report: {filename}")
            self.audited_sources.add(filename)

    def add_region(self, module, name, start, end, digest, kind="function_region", return_only=False):
        start, end = address(start), address(end)
        if sha(self.raw(start, end)) != digest:
            raise ValueError(f"region bytes differ from report: {module}/{name}")
        if return_only and (kind != "function_region" or self.decode(start, end) != [(start, 2, "rts")]):
            raise ValueError("return-only function declaration differs from its original instruction")
        key = (start, end)
        if key in self.regions:
            region = self.regions[key]
            if (region["sha256"], region["kind"], region["return_only"]) != (digest, kind, return_only):
                raise ValueError("conflicting region evidence")
            region["evidence"].append({"module": module, "name": name})
        else:
            self.regions[key] = {"start": hex_address(start), "end_exclusive": hex_address(end),
                "bytes": end - start, "sha256": digest, "kind": kind, "return_only": return_only,
                "evidence": [{"module": module, "name": name}]}
        if kind == "function_region":
            self.candidate(start, "reconstructed_function_region")

    def reports(self):
        names = [f"build/{run}/verification.json" for run in BASELINE_RUNS]
        for name in self.additional_reports:
            path = local(name)
            if not path.is_relative_to(ROOT / "build") or path.name != "verification.json":
                raise ValueError("additional reports must be verification.json files under build/")
            names.append(path.relative_to(ROOT).as_posix())
        selected = [local(name) for name in sorted(set(names))]
        omitted = [path.relative_to(ROOT).as_posix()
                   for path in sorted((ROOT / "build").glob("reverse-*/verification.json")) if path not in selected]
        for path in selected:
            filename = path.relative_to(ROOT).as_posix()
            report = json.loads(self.read(filename))
            if report.get("result") != "pass" or report.get("original_image_sha256") != REFERENCE_SHA:
                raise ValueError(f"report is not passing evidence for the pinned image: {filename}")
            functions = report.get("functions", report.get("regions"))
            if not isinstance(functions, dict) or not functions:
                raise ValueError(f"completed report needs an explicit region schema: {filename}")
            source_hashes = report.get("source_sha256", report.get("sources_sha256"))
            if not source_hashes:
                raise ValueError(f"completed report lacks source hashes: {filename}")
            self.audit_sources(source_hashes)
            manifest_name = (path.parent / "build-manifest.json").relative_to(ROOT).as_posix()
            manifest = json.loads(self.read(manifest_name))
            for name, digest in manifest["files"].items():
                artifact = (path.parent / name).relative_to(ROOT).as_posix()
                if sha(self.read(artifact)) != digest:
                    raise ValueError(f"artifact differs from completed manifest: {artifact}")
                self.audited_artifacts.add(artifact)
            module = path.parent.name
            for name, function in functions.items():
                bounds = address(function["start"]), address(function["end_exclusive"])
                kind = "command_fragment" if bounds in COMMAND_FRAGMENTS else "function_region"
                self.add_region(module, name, function["start"], function["end_exclusive"],
                                function.get("bytes_sha256", function.get("sha256")), kind,
                                function.get("rts_only", False))
            self.modules.append({"module": module, "report": filename,
                "report_sha256": self.sources[filename], "declared_regions": len(functions),
                "source_hashes_checked": len(source_hashes),
                "scope_limits": report.get("limitations", report.get("boundaries", []))})
        # Older A2 evidence includes true function regions and two fragments.
        # Recover their exact endpoints from the maintained literal registry.
        native = json.loads(self.read(NATIVE_REPORT))
        self.audit_sources(native["reconstruction_source_sha256"])
        tree = ast.parse(self.read("tools/dot_machine.py").decode("utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "NativeProgram")
        assignment = next(node for node in cls.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "REGIONS" for target in node.targets))
        bounds = {start: (name, end) for name, (start, end) in ast.literal_eval(assignment.value).items()}
        for function in native["native_functions"]:
            start = address(function["cpu_address"])
            name, end = bounds[start]
            fragment = "original_fragment_sha256" in function
            if fragment and address(function["cpu_end_exclusive"]) != end:
                raise ValueError("native fragment endpoint changed")
            self.add_region("native-A2", name, start, end,
                function.get("original_fragment_sha256", function.get("original_function_sha256")),
                "parser_fragment" if fragment else "function_region")
        self.modules.append({"module": "native-A2", "report": NATIVE_REPORT,
            "report_sha256": self.sources[NATIVE_REPORT], "declared_regions": len(native["native_functions"]),
            "source_hashes_checked": len(native["reconstruction_source_sha256"]),
            "scope_limits": [native["limitation"], "two parser fragments are not whole parser functions",
                "portable A2 orchestration is not an original scheduler reconstruction"]})
        # Count physical bytes once. This assertion also catches accidental
        # whole-parser/fragment double counting in a future inventory run.
        spans = sorted(self.regions)
        for (start, end), (next_start, next_end) in zip(spans, spans[1:]):
            if next_start < end:
                raise ValueError(f"overlapping reported regions require explicit classification: {start:#x}, {next_start:#x}")
        return omitted

    def decode(self, start, end):
        raw, cursor = self.raw(start, end), 0
        result = []
        while cursor < len(raw):
            data = next(((a, b) for a, b, _ in self.data_ranges if a <= start + cursor < b), None)
            if data:
                if start + cursor != data[0] or data[1] > end:
                    raise ValueError("reconstructed region cuts through a known data span")
                cursor = data[1] - start
                continue
            decoded = codec.decode(self.instructions, raw, cursor)
            if decoded is None:
                raise ValueError(f"unknown instruction in reconstructed region at {start + cursor:#x}")
            instruction, fields, size = decoded
            if cursor + size > len(raw):
                raise ValueError("instruction crosses reconstructed region boundary")
            result.append((start + cursor, size, codec.format(instruction, fields).removesuffix("  #")))
            cursor += size
        return result

    def region_at(self, location):
        for (start, end), region in self.regions.items():
            if start <= location < end:
                return region, location == start
        return None, False

    def trusted_dependencies(self):
        calls, indirect, escaping = [], [], []
        missing = defaultdict(list)
        for (start, end), region in sorted(self.regions.items()):
            decoded = self.decode(start, end)
            region["decoded_instructions"] = len(decoded)
            region["embedded_data_bytes"] = sum(b - a for a, b, _ in self.data_ranges if start <= a < b <= end)
            for pc, size, text in decoded:
                if match := DIRECT_CALL.fullmatch(text):
                    target = pc + size + int(match[1])
                    destination, entry = self.region_at(target)
                    status = ("reconstructed_function_entry" if destination["kind"] == "function_region" and entry
                              else "reconstructed_region_interior_or_fragment") if destination else "unreconstructed_dependency"
                    item = {"site": hex_address(pc), "source_region": hex_address(start),
                            "target": hex_address(target), "status": status}
                    calls.append(item)
                    self.candidate(target, "direct_call_from_reconstructed_region")
                    if not destination:
                        missing[target].append(item)
                elif text.startswith("call "):
                    indirect.append({"site": hex_address(pc), "source_region": hex_address(start), "instruction": text,
                                     "status": "indirect_target_requires_context"})
                elif match := BRANCH.search(text):
                    target = pc + size + int(match[1])
                    if not start <= target < end:
                        escaping.append({"site": hex_address(pc), "source_region": hex_address(start),
                                         "target": hex_address(target), "instruction": text,
                                         "status": "branch_edge_not_automatically_a_function_entry"})
        outstanding = [{"address": hex_address(target), "mapping": self.classification(target),
                        "direct_call_sites": len(items), "callers": sorted({item["source_region"] for item in items})}
                       for target, items in sorted(missing.items())]
        return {"direct_calls": calls, "unreconstructed_direct_targets": outstanding,
                "indirect_call_sites": indirect, "out_of_region_branches": escaping}

    def scans(self):
        results = {}
        for area in ("flash", "ram"):
            name = f"analysis/firmware/m571_g_app/{area}.asm"
            lines = self.read(name).decode("utf-8").splitlines()
            counts, excluded, outside = Counter(), Counter(), []
            begin = expected_pc = self.flash_start if area == "flash" else self.ram_start
            for line in lines:
                if not line.strip() or line.startswith(";"):
                    continue
                match = LINE.fullmatch(line)
                if not match:
                    raise ValueError(f"unrecognized linear listing line in {name}: {line[:90]}")
                pc, raw, rendered = int(match[1], 16), bytes.fromhex(match[2]), match[3]
                if pc != expected_pc:
                    raise ValueError("linear listing has an address gap or duplicate")
                expected_pc = pc + len(raw)
                if self.raw(pc, pc + len(raw)) != raw:
                    raise ValueError(f"linear listing bytes differ from pinned firmware at {pc:#x}")
                counts["listed_words_or_instructions"] += 1
                printed = rendered.split(" ; ", 1)[0].removesuffix("  #")
                if not printed.startswith("call "):
                    continue
                decoded = codec.decode(self.instructions, raw, 0)
                if decoded is None:
                    raise ValueError("listed call does not decode")
                instruction, fields, size = decoded
                text = codec.format(instruction, fields).removesuffix("  #")
                if text != printed or size != len(raw):
                    raise ValueError("listed call text differs from current pinned decoder")
                direct = DIRECT_CALL.fullmatch(text)
                if not direct:
                    counts["raw_indirect_call_encodings"] += 1
                    continue
                counts["raw_direct_call_encodings"] += 1
                origin = self.classification(pc)
                if origin not in ("initialized_ram", "flash_outside_known_data"):
                    excluded[origin] += 1
                    continue
                target = pc + size + int(direct[1])
                target_mapping = self.classification(target)
                if target_mapping not in ("initialized_ram", "flash_outside_known_data") or target & 1:
                    excluded["target_" + target_mapping + ("_odd" if target & 1 else "")] += 1
                    outside.append({"site": hex_address(pc), "target": hex_address(target), "mapping": target_mapping})
                    continue
                counts["included_direct_call_candidates"] += 1
                self.candidate(target, "linear_scan_direct_call_candidate")["direct_call_sites"].append(hex_address(pc))
            results[area] = {**dict(counts), "excluded_direct_call_encodings": dict(excluded),
                             "start": hex_address(begin), "end_exclusive": hex_address(expected_pc),
                             "rejected_target_examples": outside[:32],
                             "warning": "linear decoding includes unidentified data; remaining call targets are candidates only"}
        return results

    def ghidra(self):
        rows = list(csv.DictReader(self.read(GHIDRA).decode("utf-8").splitlines(), delimiter="\t"))
        statuses = Counter()
        for row in rows:
            location = int(row["address"], 16)
            self.candidate(location, "partial_ghidra_export")["ghidra_status"] = row["status"]
            statuses[row["status"]] += 1
        status_name = "recovered/ghidra/tank-g-v2/status.txt"
        status_text = self.read(status_name).decode("utf-8").strip()
        if "Partial automatic recovery" not in status_text:
            raise ValueError("unreviewed Ghidra export status")
        # Record why the map is partial without running a decompiler or using
        # pseudocode as a numerical oracle.
        self.read("tools/ghidra/MapFirmware.java")
        self.read("tools/ghidra/ExportRecovered.java")
        return {"rows": len(rows), "unique_entries": len({row["address"] for row in rows}),
                "statuses": dict(statuses), "status_record": status_text,
                "scope": "only tank-g-v2; other images' exports are not part of this denominator",
                "function_endpoints_available": False, "complete_function_inventory": False}

    def run(self):
        omitted = self.reports()
        dependencies = self.trusted_dependencies()
        scans = self.scans()
        ghidra = self.ghidra()
        self.candidate(self.flash_start, "reset_entry_from_memory_mapping")
        for location, item in self.entries.items():
            item["evidence"] = sorted(item["evidence"])
            item["direct_call_sites"] = sorted(set(item["direct_call_sites"]))
            region, entry = self.region_at(location)
            item["reconstruction"] = ("function_region_entry" if entry and region["kind"] == "function_region"
                else "region_interior_or_fragment") if region else "not_in_reconstructed_regions"
            if region:
                item["region_start"] = region["start"]
            if item["mapping"] in ("initialized_ram", "flash_outside_known_data"):
                end = min(location + 16, self.ram_end if location < self.flash_start else self.flash_end)
                prefix = self.raw(location, end)
                decoded = codec.decode(self.instructions, prefix, 0)
                item["prefix16_sha256"] = sha(prefix)
                item["first_decoded_instruction"] = codec.format(decoded[0], decoded[1]) if decoded else None
                item["prologue_hint"] = bool(decoded and item["first_decoded_instruction"].startswith("[--sp] = "))
        counts = Counter(region["kind"] for region in self.regions.values())
        categories = Counter(item["reconstruction"] for item in self.entries.values())
        evidence_counts = Counter(evidence for item in self.entries.values() for evidence in item["evidence"])
        current_report_paths = [item["report"] for item in self.modules]
        for name in ("tools/inventory_reverse.py", "upstream/pi32v2-isa/pi32v2isa/codec.py",
                     "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"):
            self.read(name)
        return {
            "schema": 1, "project": "HyperRig", "result": "pass",
            "purpose": "audited region inventory and candidate/dependency triage; not completion measurement",
            "reference": {"file": REFERENCE, "sha256": REFERENCE_SHA, "decoded_sha256": sha(self.app),
                "decoded_bytes": len(self.app), "mapping": self.layout},
            "baseline_commit": BASELINE_COMMIT,
            "summary": {"function_regions": counts["function_region"], "parser_fragments": counts["parser_fragment"],
                "command_fragments": counts["command_fragment"],
                "return_only_function_regions": sum(region["return_only"] for region in self.regions.values()),
                "distinct_reconstructed_regions": len(self.regions),
                "reconstructed_region_bytes": sum(item["bytes"] for item in self.regions.values()),
                "decoded_instructions_in_reconstructed_regions": sum(item["decoded_instructions"] for item in self.regions.values()),
                "evidence_modules": len(self.modules), "candidate_entries": len(self.entries),
                "candidate_reconstruction_categories": dict(categories),
                "candidate_evidence_counts": dict(evidence_counts),
                "unreconstructed_direct_dependency_targets": len(dependencies["unreconstructed_direct_targets"]),
                "indirect_call_sites_in_reconstructed_regions": len(dependencies["indirect_call_sites"]),
                "ghidra_partial_entries": ghidra["unique_entries"],
                "completion_percentage": None, "total_firmware_function_count": None},
            "audits": {"original_and_decoded_image_match": True, "all_region_hashes_match": True,
                "reported_source_hashes_checked": len(self.audited_sources),
                "completed_artifact_hashes_checked": len(self.audited_artifacts),
                "reconstructed_regions_overlap": False, "linear_listing_bytes_match_image": True},
            "scope_policy": ["function_region means a reviewed bounded C reconstruction, not unconstrained equivalence",
                "parser and command fragments are separate entries and are not counted as whole functions",
                "return-only functions are counted separately within the function total; function size is not work weighting",
                "baseline report set is pinned to a named commit; later reports require explicit --add-report",
                "linear call encodings inside stored RAM copy and identified data spans are excluded from candidate sources",
                "remaining linear call targets and partial Ghidra entries are hypotheses, not verified function boundaries",
                "indirect calls, callbacks, jump tables, uncalled entries and code/data separation keep the denominator open",
                "decoded-byte and call-target proportions are not firmware completion percentages"],
            "selected_reports": current_report_paths, "other_local_reports_not_selected": omitted,
            "modules": self.modules, "reconstructed_regions": [self.regions[key] for key in sorted(self.regions)],
            "known_data_ranges": [{"start": hex_address(start), "end_exclusive": hex_address(end), "kind": name}
                                  for start, end, name in self.data_ranges],
            "linear_scans": scans, "ghidra_partial_map": ghidra, "dependencies": dependencies,
            "candidate_entries": [self.entries[key] for key in sorted(self.entries)],
            "input_sha256": dict(sorted(self.sources.items())),
            "device_access": False, "hardware_test": False, "audio_test": False,
            "firmware_changed": False,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new report directory under build/")
    parser.add_argument("--check", action="store_true", help="audit and print counts without writing a report")
    parser.add_argument("--add-report", action="append", default=[], help="explicit additional completed verification.json under build/")
    args = parser.parse_args()
    if bool(args.output) == bool(args.check):
        parser.error("choose --output or --check")
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT / "build")):
        parser.error("use a new output directory under build/")
    report = Inventory(args.add_report).run()
    if output:
        output.mkdir(parents=True)
        text = json.dumps(report, indent=2) + "\n"
        (output / "inventory.json").write_bytes(text.encode("utf-8"))
        manifest = {"component": "reverse-engineering-inventory", "device_access": False,
                    "files": {"inventory.json": sha((output / "inventory.json").read_bytes())}}
        (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "audits": report["audits"],
                      "linear_scans": {name: {key: value for key, value in values.items()
                                        if key != "rejected_target_examples"} for name, values in report["linear_scans"].items()}}, indent=2))


if __name__ == "__main__":
    main()
