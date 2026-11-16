"""Build a separate v4 application with any-one-footswitch entry recovery.

Only the small entry guard is assembled. The original G program, audio shim,
board patches and reset body retain their bytes except for required branch
relocations and the exact flash PC upper bound. This tool performs no device
I/O and does not change the portable installer's approved firmware pin.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from firmware.mini.entry_recovery_one import verify
from firmware.mini.pc_limit_port.patches import pc_limit_patches, verify_candidate
from hyperrig.jieli import crc16, sfc, unpack_app
from tools import build_mini_entry_recovery_v2 as guard_v2
from tools import build_mini_ultrarig_v3 as previous
from tools.audit_mini_ultrarig_port import (
    BinaryPatch, ENTRY, FLASH_BASE, IDENTITY_PATCHES, MINI_START, VM_PATCH,
    compose_candidate, pinned_inputs, repack_header,
)

BASELINE = "build/hyperrig-mini-audio-v3"
BASELINE_SHA = "9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c"
BASELINE_PINS = {
    BASELINE+"/hyperrig-mini.app-area.bin": BASELINE_SHA,
    BASELINE+"/integration-report.json": "ac8fcb9c5ebf93268f1698a58312ddebd11f45bfafd57a748b6a8c0d988ec74f",
    BASELINE+"/firmware-manifest.json": "d901cc0d673b7f477bc9000be16d95d195b916ffb4e26f512ed00048b6c27deb",
    BASELINE+"/entry-recovery-manifest.json": "7477a0a10ae9ad7c5459432535873eb05105dc9b1065c76a1eb6f1c7cd4ca729",
    "tools/build_mini_ultrarig_v3.py": "0c8deffe0bdddce8d61592c21b5f7e5799867df82d1431cfdf2122b0e6f77a09",
    "tools/build_mini_entry_recovery_v2.py": "50f7fdcfa528a30bef115d39a31a6286b27028cdc1566bf390a21fa4881eaba1",
    "firmware/mini/pc_limit_port/patches.py": "d3b1c7ebb21342d27673cd54494a8fb50e528dd6e046ff9d7ee3961e0fe7d5b3",
    "hyperrig/jieli.py": "112309b398056da7ac4e4e8e10525fe7f858afc511f952887c97463e5fbe3620",
}
SOURCES = (
    "tools/build_mini_entry_recovery_one.py",
    "tools/build_mini_one_switch_v4.py",
    "firmware/mini/entry_recovery_one/check.S",
    "firmware/mini/entry_recovery_one/verify.py",
)
CHECK_SOURCE = "firmware/mini/entry_recovery_one/check.S"
POLICY = {
    "PORTA_input_mask": 0x409,
    "GPIO_inputs": ["PA10", "PA0", "PA3"],
    "active_low": True,
    "predicate": "(PORTA.IN & 0x409) != 0x409 at each of 32 samples",
    "samples_required": 32,
    "settle_loop_iterations": 100000,
    "hold_loop_iterations_per_accepted_sample": 100000,
    "held_subset_may_change_between_samples": True,
    "continuously_held_individual_pin_required": False,
    "physical_left_middle_right_mapping_assumed": False,
    "delay_duration_measured": False,
    "direction_permanently_input": True,
    "other_selected_GPIO_configuration_restored": True,
    "reset_body_changed": False,
}
require = verify.require
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def checked(name, digest):
    raw = (ROOT/name).read_bytes()
    require(sha(raw) == digest, "pinned input changed: "+name)
    return raw


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8", newline="\n")


def load_baseline():
    raw = {name: checked(name, digest) for name, digest in BASELINE_PINS.items()}
    # The English migration changed one README listed by the old audio build.
    # Keep the historical manifest intact; it is not an executable input.
    # Every other historical source and compiled artifact must still match.
    v2_raw = {name: checked(name, digest) for name, digest in previous.BASELINE_PINS.items()}
    audio = json.loads(v2_raw["build/mini-audio-port-v2/manifest.json"])
    recovery = json.loads(raw[BASELINE+"/entry-recovery-manifest.json"])
    pins, documentation = dict(previous.BASELINE_PINS), []
    for item in (audio, recovery):
        for name, digest in item["source_sha256"].items():
            if name == "firmware/mini/audio_port/README.md":
                documentation.append({"path": name, "historical_sha256": digest,
                                      "current_sha256": sha((ROOT/name).read_bytes()),
                                      "used_as_build_input": False})
            else:
                checked(name, digest)
                pins[name] = digest
    component = recovery["component"]
    for name, digest in ((audio["payload"]["path"], audio["payload"]["sha256"]),
                         (audio["elf"]["path"], audio["elf"]["sha256"]),
                         (component["file"], component["payload_sha256"]),
                         (component["elf"], component["elf_sha256"])):
        checked(name, digest)
        pins[name] = digest
    baseline = {"image": v2_raw[previous.BASELINE_IMAGE],
                "integration": json.loads(v2_raw[previous.BASELINE+"/integration-report.json"]),
                "manifest": json.loads(v2_raw[previous.BASELINE+"/firmware-manifest.json"]),
                "audio": audio, "recovery": recovery,
                "audio_bytes": checked(audio["payload"]["path"], audio["payload"]["sha256"]),
                "guard_bytes": checked(component["file"], component["payload_sha256"]), "pins": pins}
    g, mini = (ROOT/previous.G_PATH).read_bytes(), (ROOT/previous.MINI_PATH).read_bytes()
    rebuilt, composition, _ = previous.compose_revision(baseline, g, mini)
    require(rebuilt == raw[BASELINE+"/hyperrig-mini.app-area.bin"], "v3 does not reproduce exactly")
    recorded = json.loads(raw[BASELINE+"/integration-report.json"])
    require(recorded["composition"] == composition, "v3 composition audit differs")
    require(baseline["recovery"]["component"]["address"] == verify.ADDRESS and
            sha(baseline["guard_bytes"]) == verify.OLD_SHA, "unexpected v3 guard allocation")
    return {"v2": baseline, "image": rebuilt, "composition": composition,
            "manifest": json.loads(raw[BASELINE+"/firmware-manifest.json"]),
            "g": g, "mini": mini, "pins": {**baseline["pins"], **BASELINE_PINS},
            "historical_documentation_not_used_as_build_input": documentation}


def compile_guard(output: Path, baseline: dict) -> tuple[bytes, dict]:
    """Compile only the new check plus the two unchanged prefix/reset sources."""
    output.mkdir(parents=True, exist_ok=False)
    original_source = (ROOT/"firmware/mini/entry_recovery/check.S").read_text(encoding="utf-8")
    new_source = (ROOT/CHECK_SOURCE).read_text(encoding="utf-8")
    # Verify the source as well as the emitted instruction semantics. Comments
    # may explain the new predicate, but no other assembly statement may change.
    strip_comments = lambda text: re.sub(r"/\*.*?\*/", "", text, flags=re.S).split()
    old_tokens = strip_comments(original_source)
    new_tokens = strip_comments(new_source)
    expected_source = original_source.replace(
        "r0 = [r4+4]\n    r0 &= r5\n    if (r0 != 0) goto .Lrestore",
        "r0 = [r4+4]\n    r0 &= r5\n    if (r0 == r5) goto .Lrestore")
    require(old_tokens != new_tokens and strip_comments(expected_source) == new_tokens,
            "assembly changes more than the sample predicate")
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"

    def run(args):
        result = subprocess.run(prefix+args, cwd=ROOT, capture_output=True, text=True, timeout=60)
        require(result.returncode == 0, result.stdout+result.stderr)
        return result.stdout

    objects = []
    for name in ("firmware/mini/entry_recovery_v2/prefix.S", CHECK_SOURCE,
                 "firmware/mini/entry_recovery/reset.S"):
        target = output/(Path(name).stem+".o")
        run([vendor+"clang", "-target", "pi32v2", "-mcpu=r3", "-c", name, "-o", relative(target)])
        objects.append(relative(target))
    elf_path = output/"entry-recovery-one.elf"
    run([vendor+"ld", "-z", "max-page-size=0x20", "-z", "common-page-size=0x20",
         "--defsym", f"HYPERRIG_ENTRY_GUARD_ADDRESS={verify.ADDRESS}",
         "-T", "firmware/mini/entry_recovery_v2/append.ld", *objects, "-o", relative(elf_path)])
    raw = elf_path.read_bytes()
    payload, symbols, delta = verify.inspect_elf(raw, baseline["v2"]["guard_bytes"])
    g_plain, _, _ = unpack_app(baseline["g"])
    hook = guard_v2.patches(g_plain, verify.ADDRESS)[0]
    model = verify.verify_flow(payload, symbols, hook)
    disassembly = run([vendor+"objdump", "-d", relative(elf_path)])
    vendor_rows = {}
    for line in disassembly.splitlines():
        match = re.match(r"\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(.*)", line)
        if match:
            vendor_rows[int(match[1], 16)] = (bytes.fromhex(match[2]), match[3].split(" <", 1)[0].strip())
    rows = verify.original.instructions(payload, verify.ADDRESS, verify.ADDRESS, verify.NEW_END)
    for row in rows:
        require(vendor_rows.get(row["address"]) == (bytes.fromhex(row["bytes"]), row["text"]),
                "vendor and independent instruction decoders disagree")
    binary = output/"entry-recovery-one.bin"
    binary.write_bytes(payload)
    (output/"entry-recovery-one.asm").write_text(disassembly, encoding="utf-8", newline="\n")
    return payload, {"schema": 1, "kind": "mini-entry-recovery-any-one",
                     "component": {"address": verify.ADDRESS, "end_exclusive": verify.NEW_END,
                                   "payload_bytes": len(payload), "payload_sha256": sha(payload),
                                   "file": relative(binary), "elf": relative(elf_path),
                                   "elf_sha256": sha(raw), "symbols": symbols,
                                   "BSS_bytes": 0, "initialized_RAM_bytes": 0, "stack_bytes": 100},
                     "policy": POLICY, "instruction_delta": delta, "model_tests": model,
                     "entry_hook_unchanged": hook.record(), "instructions": rows,
                     "vendor_disassembly_matches_independent_decoder": True,
                     "hardware_executed": False, "cold_boot_recovery_verified": False,
                     "USB_enumeration_verified": False}


def reverse_revision(image: bytes, baseline: dict) -> bytes:
    """Reverse the new bytes/relocations and regenerate v3 headers from them."""
    require(sha(baseline["image"]) == BASELINE_SHA, "not the approved v3 baseline")
    plain, entries, files = unpack_app(image)
    old_plain, old_entries, old_files = unpack_app(baseline["image"])
    guard = files["app.bin"][verify.ADDRESS-ENTRY:]
    verify.verify_minimal_delta(baseline["v2"]["guard_bytes"], guard)
    app = bytearray(files["app.bin"][:-len(guard)]+baseline["v2"]["guard_bytes"])
    pc_offset = 0x0200067E-ENTRY
    require(app[pc_offset:pc_offset+6] == b"\xc1\xff"+verify.NEW_END.to_bytes(4, "little"),
            "reverse PC preimage differs")
    app[pc_offset:pc_offset+6] = old_files["app.bin"][pc_offset:pc_offset+6]
    require(files["cfg_tool.bin"] == old_files["cfg_tool.bin"], "reverse cfg contents differ")
    app_offset, cfg_offset = entries[1].offset, old_entries[2].offset
    head_end = cfg_offset+len(files["cfg_tool.bin"])
    require(app_offset == old_entries[1].offset and app_offset+len(app) == cfg_offset and
            entries[2].offset == cfg_offset+2 and entries[0].size == head_end+2,
            "reverse file extents differ")
    reverse = bytearray(plain)
    reverse[app_offset:cfg_offset] = app
    reverse[cfg_offset:head_end] = files["cfg_tool.bin"]
    reverse[head_end:head_end+2] = b"\xff\xff"
    reverse[32:64] = repack_header(plain[32:64], size=len(app), data_crc=crc16(app))
    reverse[64:96] = repack_header(plain[64:96], offset=cfg_offset, data_crc=crc16(files["cfg_tool.bin"]))
    reverse[:32] = repack_header(plain[:32], size=head_end, data_crc=crc16(reverse[32:head_end]))
    cipher_end = (head_end+31) & ~31
    encoded = sfc(bytes(reverse[:cipher_end]))+bytes(reverse[cipher_end:])
    require(bytes(reverse) == old_plain and encoded == baseline["image"],
            "inverse changes do not recover the entire decoded/encoded v3")
    return encoded


def changed_ranges(before: bytes, after: bytes) -> list[dict]:
    require(len(before) == len(after), "range comparison needs equal application areas")
    ranges, start = [], None
    for index in range(len(before)+1):
        different = index < len(before) and before[index] != after[index]
        if different and start is None:
            start = index
        elif not different and start is not None:
            ranges.append({"area_offset": start, "physical_start": MINI_START+start,
                           "physical_end_exclusive": MINI_START+index, "bytes": index-start,
                           "before_hex": before[start:index].hex(), "after_hex": after[start:index].hex()})
            start = None
    return ranges


def compose_revision(baseline: dict, payload: bytes) -> tuple[bytes, dict, dict]:
    require(sha(baseline["image"]) == BASELINE_SHA, "not the approved v3 baseline")
    previous_guard = baseline["v2"]["guard_bytes"]
    guard_delta = verify.verify_minimal_delta(previous_guard, payload)
    gp, _, gf, *_ = pinned_inputs(baseline["g"], baseline["mini"])
    old_plain, old_entries, old_files = unpack_app(baseline["image"])
    original_size = len(gf["app.bin"])
    prefix = old_files["app.bin"][original_size:-len(previous_guard)]
    audio = baseline["v2"]["audio_bytes"]
    require(prefix == audio+b"\0"*((-len(audio)) & 3) and
            ENTRY+original_size+len(prefix) == verify.ADDRESS and
            old_files["app.bin"][-len(previous_guard):] == previous_guard,
            "actual preceding audio/guard allocation differs")
    old_rows = baseline["v2"]["integration"]["composition"]["patches"]
    builtins = (*IDENTITY_PATCHES, VM_PATCH)
    require(old_rows[:len(builtins)] == [p.record() for p in builtins], "v2 builtin patches differ")
    extra = tuple(BinaryPatch(p["name"], p["cpu_address"], bytes.fromhex(p["before_hex"]),
                              bytes.fromhex(p["after_hex"]), p["rationale"])
                  for p in old_rows[len(builtins):])
    require([p.record() for p in extra] == old_rows[len(builtins):], "v2 patch metadata differs")
    old_pc = pc_limit_patches(gp, verify.OLD_END)
    reproduced, old_composition = compose_candidate(baseline["g"], baseline["mini"],
                                                    additional_patches=extra+old_pc,
                                                    append_code=prefix+previous_guard)
    require(reproduced == baseline["image"] and old_composition == baseline["composition"],
            "v3 cannot be reproduced before the condition-only change")
    new_pc = pc_limit_patches(gp, verify.NEW_END)
    image, composition = compose_candidate(baseline["g"], baseline["mini"],
                                           additional_patches=extra+new_pc, append_code=prefix+payload)
    pc_audit = verify_candidate(image, executable_end=verify.NEW_END, g_plain=gp)
    plain, entries, files = unpack_app(image)
    restored = bytearray(files["app.bin"][:-len(payload)]+previous_guard)
    for a, b in zip(old_pc, new_pc):
        offset = b.address-ENTRY
        require(restored[offset:offset+len(b.after)] == b.after, "new PC patch bytes differ")
        restored[offset:offset+len(b.after)] = a.after
    require(bytes(restored) == old_files["app.bin"], "undeclared application change outside guard/PC bound")
    require(files["cfg_tool.bin"] == old_files["cfg_tool.bin"], "cfg_tool content changed")
    require(len(files["app.bin"]) == len(old_files["app.bin"])+2 and
            composition["cfg_tool_area_offset"] == old_composition["cfg_tool_area_offset"]+2 and
            composition["head_end"] == old_composition["head_end"]+2 and
            composition["encoding_end"] == old_composition["encoding_end"], "unexpected extent change")
    require([e.to_dict() for e in entries[3:]] == [e.to_dict() for e in old_entries[3:]],
            "partition directory changed")
    for start in (0x1B8, 0x1DC):
        require(plain[start:start+6] == old_plain[start:start+6], "original RAM-copy source changed")
    sectors = []
    for offset in range(0, len(image), 4096):
        a, b = baseline["image"][offset:offset+4096], image[offset:offset+4096]
        if a != b:
            sectors.append({"physical_address": MINI_START+offset, "bytes": len(b),
                            "before_sha256": sha(a), "after_sha256": sha(b),
                            "changed_bytes": sum(x != y for x, y in zip(a, b))})
    require([s["physical_address"] for s in sectors] == [0x4000, 0x7B000], "unexpected changed sectors")
    reverse_revision(image, baseline)
    unchanged = []
    for label, start, end in (("original application before PC instruction", ENTRY, 0x0200067E),
                               ("original application after PC instruction", 0x02000684, ENTRY+original_size),
                               ("audio shim and alignment padding", ENTRY+original_size, verify.ADDRESS)):
        before = old_files["app.bin"][start-ENTRY:end-ENTRY]
        after = files["app.bin"][start-ENTRY:end-ENTRY]
        require(before == after, "unchanged executable region differs")
        unchanged.append({"label": label, "cpu_start": start, "cpu_end_exclusive": end,
                          "bytes": len(before), "sha256": sha(before)})
    return image, composition, {
        "baseline_reproduced_byte_exactly": True, "baseline_image_sha256": BASELINE_SHA,
        "instruction_delta": guard_delta, "audio_payload_byte_identical": True,
        "audio_payload_sha256": sha(audio), "reset_body_byte_identical": True,
        "entry_hook_byte_identical": True, "original_RAM_copy_sources_unchanged": True,
        "PC_limit_before": verify.OLD_END, "PC_limit_after": verify.NEW_END,
        "PC_limit_setup": pc_audit, "PC_patch_before": [p.record() for p in old_pc],
        "PC_patch_after": [p.record() for p in new_pc],
        "app_bytes_before": len(old_files["app.bin"]), "app_bytes_after": len(files["app.bin"]),
        "cfg_tool_before": old_composition["cfg_tool_area_offset"],
        "cfg_tool_after": composition["cfg_tool_area_offset"],
        "cfg_tool_bytes_unchanged": len(files["cfg_tool.bin"]),
        "head_end_before": old_composition["head_end"], "head_end_after": composition["head_end"],
        "SFC_encoding_end_unchanged": composition["encoding_end"],
        "app_data_CRC_before": crc16(old_files["app.bin"]), "app_data_CRC_after": crc16(files["app.bin"]),
        "JLFS_CRC_and_SFC_roundtrip_passed": True, "partition_geometry_unchanged": True,
        "inverse_guard_and_PC_change_recovers_v3_exactly": True,
        "inverse_headers_CRC_and_SFC_recovers_complete_v3_image": True,
        "inverse_original_G_patches_recovers_G_exactly": True,
        "unchanged_executable_ranges": unchanged,
        "decoded_changed_ranges": changed_ranges(old_plain, plain),
        "encoded_changed_ranges": changed_ranges(baseline["image"], image),
        "JLFS_headers": [{"area_offset": offset, "before_hex": old_plain[offset:offset+32].hex(),
                          "after_hex": plain[offset:offset+32].hex()} for offset in (0, 32, 64)],
        "changed_sectors_vs_v3": sectors, "hardware_verified": False}


def build(output: Path) -> dict:
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/"build") and not output.exists(),
            "choose a new output directory under build; historical artifacts cannot be overwritten")
    baseline = load_baseline()
    sources = {p: sha((ROOT/p).read_bytes()) for p in SOURCES}
    payload, recovery = compile_guard(output/"guard", baseline)
    image, composition, audit = compose_revision(baseline, payload)
    recovery["source_sha256"] = sources
    recovery["frozen_input_sha256"] = baseline["pins"]
    recovery_path = output/"entry-recovery-manifest.json"
    write_json(recovery_path, recovery)
    image_path = output/"hyperrig-mini.app-area.bin"
    image_path.write_bytes(image)
    gates = [
        "Any-one-footswitch application recovery has not been executed on hardware.",
        "The identical reset body does not establish cold-SPL-to-ROM USB enumeration.",
        "The any-one policy cannot fix a descriptor failure already reached with all three switches held.",
        "A damaged application header, entry or guard can prevent this application-level recovery.",
        "The instruction-count hold window is not a measured physical duration or same-pin debounce.",
        "Audio and editor observations for v3 remain historical; v4 requires its own boot qualification.",
    ]
    old_manifest = baseline["manifest"]
    manifest = {"project": "HyperRig", "target": "tank-mini", "revision": 4,
                "architecture": old_manifest["architecture"],
                "firmware_version": old_manifest["firmware_version"],
                "image_path": relative(image_path), "image_sha256": sha(image),
                "image_kind": "MINI application area, not complete NOR or FWSC",
                "original_application": old_manifest["original_application"],
                "stock_MINI_application_used": False, "SPL_and_unit_partitions_included": False,
                "audio_shim": copy.deepcopy(old_manifest["audio_shim"]),
                "entry_recovery": {"version": "any-one-1", "mandatory": True,
                                   "manifest": relative(recovery_path),
                                   "manifest_sha256": sha(recovery_path.read_bytes()),
                                   **recovery["component"], "policy": POLICY,
                                   "actual_preceding_payload_validated": True,
                                   "cold_entry_verified_on_mini": False,
                                   "valid_image_hang_recovery_verified": False,
                                   "damaged_header_entry_or_guard_covered": False},
                "PC_limit_correction": audit["PC_limit_setup"],
                "previous_revision": {"image_sha256": BASELINE_SHA,
                                      "historical_observations_are_not_v4_qualification": True},
                "capabilities": {"identity": True, "read": True, "write": False, "panel": False},
                "command_capabilities": {}, "family_capabilities": {},
                "hardware_verified": False, "flashable": False, "remaining_gates": gates}
    manifest_path = output/"firmware-manifest.json"
    write_json(manifest_path, manifest)
    report = {"project": "HyperRig", "target": "tank-mini", "revision": 4,
              "kind": "offline any-one-footswitch condition-only revision",
              "composition": composition, "validation": audit, "policy": POLICY,
              "source_sha256": sources, "frozen_input_sha256": baseline["pins"],
              "historical_documentation_not_used_as_build_input": baseline["historical_documentation_not_used_as_build_input"],
              "entry_recovery": manifest["entry_recovery"],
              "firmware_manifest": relative(manifest_path),
              "firmware_manifest_sha256": sha(manifest_path.read_bytes()),
              "boot_verified_on_mini": False, "audio_verified_on_mini": False,
              "cold_boot_recovery_verified": False, "device_access_performed": False,
              "installer_approved_firmware_changed": False, "flashable": False,
              "remaining_gates": gates}
    for name, digest in {**baseline["pins"], **sources}.items():
        checked(name, digest)
    write_json(output/"integration-report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"build/hyperrig-mini-audio-v4")
    args = parser.parse_args(argv)
    report = build(args.output)
    print(json.dumps({"result": "PASS", "firmware_manifest": report["firmware_manifest"],
                      "image_sha256": report["composition"]["sha256"],
                      "guard_bytes": report["entry_recovery"]["payload_bytes"],
                      "PC_limit_upper": report["validation"]["PC_limit_after"],
                      "changed_sectors_vs_v3": report["validation"]["changed_sectors_vs_v3"],
                      "hardware_verified": False, "installer_approved_firmware_changed": False}, indent=2))


if __name__ == "__main__":
    main()
