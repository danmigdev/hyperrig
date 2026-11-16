"""Build/check a private-data-free MINI installer preview from local pinned assets.

No downloads, browser launch, elevation, device enumeration or device I/O occur.
The explicit inventory is intentional: never copy the workspace, build tree,
historical evidence, personal presets or unit backups into a release.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_OUTPUT = ROOT / "build/hyperrig-mini-installer-preview"
DEFAULT_EDITOR = ROOT / "build/hyperrig-mini-english-editor"
KIND = "hyperrig-mini-installer-preview"
FAMILIES = ["GAIN", "PLOAD", "PSAVE", "SNAPSAVE", "FXA", "FXP", "FXE", "FXR"]
IMAGE_SHA = "9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c"
# Reviewed static v4 derivation; this pin is not a hardware qualification.
ONE_SWITCH_IMAGE_SHA = "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
ONE_SWITCH_REPORT_SHA = "437b45f89b2a92b2228b7658f40a16e6f5cbab095daace32c42553396ae2d2c5"
ONE_SWITCH_IMAGE = "build/hyperrig-mini-audio-v4/hyperrig-mini.app-area.bin"
ONE_SWITCH_REPORT = "build/hyperrig-mini-audio-v4/integration-report.json"
PRODUCT_BUILDER_SHA = "35ffb85d56d8a9821b9943ff63e3d58a874b9672680eec5ce0815fa0130d0234"
PROTECTED_EDITOR_SHA = {
    "mini-profile.js": "5a9de5e93ffbefda575864c996dab76955f783a81e5dbfec21feb9c1bfcd2a5c",
    "mini-fx-ui.js": "e11c95735bb57ef6d694844dd1163574b86c21c58a9f1b1984a68ec02b2d0b20",
    "nam2chip.js": "af584a732fa8a0b03a388871947d490a383c5094d9391fed0f48b6336f255183",
}

# Source, destination, exact immutable input SHA256. No historical manifest is copied.
ASSETS = (
    ("build/hyperrig-mini-audio-v3/hyperrig-mini.app-area.bin", "assets/hyperrig-mini-v3.app.bin", IMAGE_SHA),
    ("build/mini-app-writer-operational/hyperrig-writer-operational-01c20000.bin", "assets/writer-a.bin", "09e0772b1c4f2087f6864fd16f09fa48ac5b0d2d46ab3e408e3d839447d51749"),
    ("build/mini-app-writer-operational/hyperrig-writer-operational-01c20000.elf", "assets/writer-a.elf", "39880f9272d2714d73bd165258288e5a63c9de305364cf8b723e59ee639835cd"),
    ("build/mini-flash-reader/hyperrig-reader-01c28000.bin", "assets/reader-b.bin", "7a492bf17d98f0f5ca5d2fb0d0da7d369937169075507676bfb51b88c9bb2b83"),
    ("build/mini-flash-reader/hyperrig-reader-01c28000.elf", "assets/reader-b.elf", "c59cff25df5c3e3bfe0d85392d9aa861e1fe287dc1f7d8afcf40e5f7575acf72"),
    ("build/mini-rom-reset/hyperrig-reset-01c20000.bin", "assets/reset-a.bin", "cf3526d914eef007649f88f1f22e085a908359b9ad0e9f4743427b4757c0540f"),
    ("build/mini-rom-reset/hyperrig-reset-01c20000.elf", "assets/reset-a.elf", "3a9aa6ba1c5043b548df3e521ffc82b2c2b58a4378d51d6eb3807feb51f0a081"),
)

# Dependency closure for the selected writer/reader/reset profiles only. Other
# diagnostic plugins in the historical dispatch table are deliberately absent.
RUNTIME_FILES = (
    "hyperrig/__init__.py", "hyperrig/jieli.py", "hyperrig/mini.py", "hyperrig/device.py",
    "hyperrig/installer/__init__.py", "hyperrig/installer/core.py",
    "hyperrig/installer/service.py", "hyperrig/installer/windows.py", "hyperrig/installer/gui.py",
    "tools/launch_mini_installer.py", "tools/build_mini_installer_bundle.py",
    "tools/build_mini_installer_one_switch_bundle.py",
    "tools/install_mini_app.py", "tools/build_mini_app_writer.py",
    "tools/build_mini_app_writer_operational.py", "tools/probe_mini_app_writer.py",
    "tools/probe_mini_recovery.py", "tools/verify_mini_recovery_reader.py",
    "tools/verify_mini_rom_stack.py", "tools/disassemble.py",
    "tools/mini_host_journal.py", "tools/mini_windows_aligned.py",
    "tools/mini_windows_spt.py", "tools/mini_windows_quiet.py", "tools/mini_windows_mcn.py",
    "tools/mini_nor_read_recovery.py", "tools/recover_mini_read_v2.py",
    "tools/recover_mini_read_v3.py", "tools/recover_mini_read_v4.py", "tools/recover_mini_read_v5.py",
    "tools/recover_mini_read_v6.py",
    "upstream/pi32v2-isa/pi32v2isa/__init__.py",
    "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
    "upstream/pi32v2-isa/isa/pi32v2.toml", "upstream/pi32v2-isa/docs/SOURCES.md",
    "upstream/pi32v2-isa/LICENSE", "upstream/pi32v2-isa/LICENSES/MIT-0.txt",
)
EDITOR_FILES = (
    "web/index.html", "web/tankmini.html", "web/mini-profile.js", "web/mini-ui.js",
    "web/mini-fx-ui.js", "web/nam2chip.js", "web/serial-open-timeout.js",
    "LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md",
)
GENERATED_FILES = (
    "README.txt", "start.cmd", "launch_editor.cmd", "check.cmd",
    "editor/profile.json", "editor/qualification.json", "editor/DERIVATION.txt",
    "editor/web/portable-startup.js",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")


def safe_file(root, name, *, exists=True):
    """Reject traversal and Windows junction/symlink hops before reading/copying."""
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            "Expected a portable relative path")
    parts = PurePosixPath(name)
    require(not parts.is_absolute() and parts.as_posix() == name and
            all(p not in ("", ".", "..") for p in parts.parts), "Unsafe relative path")
    root = Path(root).resolve(strict=True)
    path = root.joinpath(*parts.parts)
    current = root
    for part in parts.parts:
        current /= part
        if current.exists() or current.is_symlink():
            info = current.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400),
                    "Reparse points are not package inputs")
    require(path.resolve(strict=exists).is_relative_to(root), "Path escapes package root")
    if exists:
        require(path.is_file(), "Missing package file: " + name)
    return path


def write_file(root, name, raw):
    path = safe_file(root, name, exists=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def release_variant(name="v3"):
    require(name in ("v3", "v4"), "Unknown release variant")
    if name == "v3":
        return {"name": name, "image_sha256": IMAGE_SHA, "assets": ASSETS,
                "direct_stock_flag": "direct_stock_to_v3", "read_only_editor": False}
    require(isinstance(ONE_SWITCH_IMAGE_SHA, str) and isinstance(ONE_SWITCH_REPORT_SHA, str),
            "The reviewed one-switch candidate/report has not been pinned")
    return {"name": name, "image_sha256": ONE_SWITCH_IMAGE_SHA,
            "assets": ((ONE_SWITCH_IMAGE, "assets/hyperrig-mini-v4.app.bin", ONE_SWITCH_IMAGE_SHA),) + ASSETS[1:],
            "direct_stock_flag": "direct_stock_to_v4", "read_only_editor": True}


def qualification_flags(variant):
    return {variant["direct_stock_flag"]: False, "cold_boot_recovery": False,
            "interrupted_write_recovery": False}


def runtime_files(variant):
    # The v3 baseline predates this separate entry. Do not require an extra file
    # in its immutable inventory merely because a v4 entry now exists.
    return tuple(name for name in RUNTIME_FILES if variant == "v4" or
                 name != "tools/build_mini_installer_one_switch_bundle.py")


def static_inheritance():
    """Build-only static provenance. Never substitute it for v4 hardware evidence."""
    variant = release_variant("v4")
    raw = safe_file(ROOT, ONE_SWITCH_REPORT).read_bytes()
    require(sha(raw) == ONE_SWITCH_REPORT_SHA, "One-switch integration report differs")
    report = json.loads(raw)
    audit = report["validation"]
    require(report["revision"] == 4 and report["composition"]["sha256"] == variant["image_sha256"]
            and report["boot_verified_on_mini"] is False and report["audio_verified_on_mini"] is False
            and report["cold_boot_recovery_verified"] is False and report["device_access_performed"] is False
            and audit["baseline_image_sha256"] == IMAGE_SHA
            and all(audit[key] is True for key in (
                "baseline_reproduced_byte_exactly", "reset_body_byte_identical", "entry_hook_byte_identical",
                "original_RAM_copy_sources_unchanged", "JLFS_CRC_and_SFC_roundtrip_passed",
                "partition_geometry_unchanged", "inverse_guard_and_PC_change_recovers_v3_exactly",
                "inverse_headers_CRC_and_SFC_recovers_complete_v3_image")),
            "One-switch static inheritance does not match the reviewed revision")
    return {"kind": "v3-to-v4-static-derivation", "source_image_sha256": IMAGE_SHA,
            "target_image_sha256": variant["image_sha256"], "report_sha256": sha(raw),
            "unchanged_executable_ranges": audit["unchanged_executable_ranges"],
            "audio_payload_sha256": audit["audio_payload_sha256"],
            "reset_body_byte_identical": True, "entry_hook_byte_identical": True,
            "inverse_revision_recovers_v3_exactly": True,
            "hardware_observations_inherited_as_v4_proof": False}


def expected_files(*, executable=False, variant="v3"):
    names = {dst for _, dst, _ in release_variant(variant)["assets"]} | set(runtime_files(variant)) | set(GENERATED_FILES)
    names |= {"editor/" + name for name in EDITOR_FILES}
    if executable:
        names |= {"HyperRig-MINI-Installer.exe", "runtime-licenses.txt"}
    return names


def editor_assets(editor_directory, *, variant="v3"):
    """Build-time full seal check; return only sanitized runtime assets."""
    from tools import build_hyperrig_editor as product
    require(sha(Path(product.__file__).read_bytes()) == PRODUCT_BUILDER_SHA, "English editor builder changed")
    original = product.validate_bundle(editor_directory)
    profile = copy.deepcopy(original["profile"])
    spec = release_variant(variant)
    require(profile["image_sha256"] == IMAGE_SHA and profile["firmware_version"] == "tankm_fw M5.71 rel ble"
            and profile["family_capabilities"] == {"usb-cdc": FAMILIES}
            and profile["capabilities"] == {"identity": True, "read": True, "write": False, "panel": False},
            "Editor profile differs from the reviewed eight-family v3 profile")
    old_config = "globalThis.HYPERRIG_MINI_BUILD=" + json.dumps(profile, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c") + ";"
    qualification = {
        "schema": 1, "kind": "hyperrig-mini-portable-editor-scope",
        "image_sha256": IMAGE_SHA, "firmware_version": profile["firmware_version"],
        "transport": "usb-cdc", "enabled_families": FAMILIES,
        "representative_protocol_operations_previously_exercised": True,
        "portable_presentation_hardware_retested": False,
        "all_values_or_all_effects_hardware_qualified": False,
        "blanket_write": False, "routing_enabled": False, "BLE_write_enabled": False,
        "device_binary_hash_attestation": False,
    }
    if spec["read_only_editor"]:
        inheritance = static_inheritance()
        require(inheritance["source_image_sha256"] == IMAGE_SHA and inheritance["target_image_sha256"] == spec["image_sha256"]
                and inheritance["report_sha256"] == ONE_SWITCH_REPORT_SHA
                and inheritance["hardware_observations_inherited_as_v4_proof"] is False, "Wrong static inheritance")
        qualification = {"schema": 1, "kind": "hyperrig-mini-v4-read-only-editor-scope",
            "image_sha256": spec["image_sha256"], "firmware_version": profile["firmware_version"],
            "transport": "usb-cdc", "enabled_families": [], "hardware_verified": False,
            "qualification_pending": True, "current_image_mutations_physically_retested": False,
            "source_image_protocol_families": FAMILIES, "source_image_sha256": IMAGE_SHA,
            "source_observations_apply_to_target_image": False, "static_inheritance": inheritance,
            "blanket_write": False, "device_binary_hash_attestation": False}
        profile.update(image_sha256=spec["image_sha256"], hardware_verified=False,
                       family_capabilities={}, family_validation={}, family_qualification={},
                       family_evidence_model="v4-pending-static-inheritance", derived_from=inheritance)
    qraw = encoded(qualification)
    if not spec["read_only_editor"]:
        profile["family_validation"] = {"usb-cdc": [{"path": "editor/qualification.json", "sha256": sha(qraw)}]}
    new_config = "globalThis.HYPERRIG_MINI_BUILD=" + json.dumps(profile, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c") + ";"
    files = {"editor/" + name: safe_file(Path(editor_directory) / "app", name).read_bytes() for name in EDITOR_FILES}
    for name, digest in PROTECTED_EDITOR_SHA.items():
        require(sha(files["editor/web/" + name]) == digest, "Protected editor policy differs: " + name)
    original_html = files["editor/web/tankmini.html"].decode("utf-8")
    require(original_html.count(old_config) == 1 and original_html.count("</body>") == 1, "English HTML anchors differ")
    html = original_html.replace(old_config, new_config)
    injection = '<script src="serial-open-timeout.js"></script>\n<script src="portable-startup.js"></script>\n'
    html = html.replace("</body>", injection + "</body>")
    require(html.replace(injection, "").replace(new_config, old_config) == original_html,
            "Unexpected editor transformation")
    files["editor/web/tankmini.html"] = html.encode("utf-8")
    files["editor/web/portable-startup.js"] = (
        '/* Same reviewed 30-second open timeout; no automatic connection. */\n'
        '"use strict";\n'
        'globalThis.HYPERRIG_PORTABLE_SERIAL_TIMEOUT = installMiniSerialOpenTimeout(SerialTransport);\n'
    ).encode("utf-8")
    files["editor/profile.json"] = encoded(profile)
    files["editor/qualification.json"] = qraw
    files["editor/DERIVATION.txt"] = (
        "HyperRig MINI portable English editor preview.\n"
        "Derived from the sealed English editor; original license notices remain unchanged.\n"
        "The profile metadata and reviewed serial timeout activation are derived for this package.\n" +
        ("The original command policy is unchanged; v4 identity/read are enabled and every write family is disabled.\n"
         "V3 protocol observations remain evidence for v3; static derivation is not v4 hardware qualification.\n"
         if spec["read_only_editor"] else "The eight USB command families and their original policy are unchanged.\n") +
        "No private reports, device dumps, user presets, COM binding or session timestamps are included.\n"
        "This packaging step is not a physical installer or editor retest.\n"
    ).encode("utf-8")
    return files, {
        "entry": "editor/web/tankmini.html", "profile": "editor/profile.json",
        "qualification": "editor/qualification.json", "transport": "usb-cdc",
        "families": [] if spec["read_only_editor"] else FAMILIES, "firmware_version": profile["firmware_version"],
        "image_sha256": spec["image_sha256"], "read_only": spec["read_only_editor"], "automatic_connection_added": False,
        "serial_open_timeout_ms": 30000,
        "input_bundle_sha256": original["product_bundle"]["sha256"],
        "original_html_sha256": sha(original_html.encode("utf-8")),
        "protected_files_sha256": {n: sha(files["editor/web/" + n]) for n in
                                   ("mini-profile.js", "mini-fx-ui.js", "nam2chip.js")},
    }


def launch_script(option=""):
    return ("@echo off\r\nsetlocal\r\ncd /d \"%~dp0\"\r\n"
            "if exist \"%~dp0HyperRig-MINI-Installer.exe\" (\r\n"
            f'  "%~dp0HyperRig-MINI-Installer.exe" --bundle "%~dp0." {option}\r\n'
            ") else (\r\n"
            f'  python -B -X utf8 "%~dp0tools\\launch_mini_installer.py" --bundle "%~dp0." {option}\r\n'
            ")\r\nif errorlevel 1 pause\r\n").encode("ascii")


README = """HyperRig MINI installer preview

This package contains a reviewed TANK MINI application and bounded RAM tools.
The new portable installation flow has not been hardware qualified. Direct
stock-to-v3 installation, cold-boot recovery and interrupted-write recovery
remain unqualified. The existing image's earlier unit tests are not a claim
that this package has been installed successfully on another unit.

Double-click start.cmd to open the installer. It does not request elevation
until an explicit installation/backup action requires administrator access.
Double-click check.cmd for local file/ELF checks without hardware access.
Double-click launch_editor.cmd to open the English editor on localhost.
Connect from the editor's original port chooser. Its existing reconnect behavior
can resume a previously authorized port when that browser origin has saved intent.
This package adds no automatic connection or command retry.

If the executable is absent, use 64-bit Python 3.12 or newer with tkinter,
python-rtmidi and pyserial already installed. No dependency is downloaded.
The editor uses an installed Microsoft Edge or Google Chrome browser.

Only the application range [0x4000,0x82000) may be written. Each device needs a
new full backup before installation; never use another device's dump. Backups
and operation journals are generated separately on your computer, not shipped
with this package. An interrupted update is not atomic and must not be treated
as safe to boot. The app header sector/page is written last. There is no
automatic reset or mutation retry after an ambiguous operation.

The editor enables USB GAIN/PLOAD/PSAVE/SNAPSAVE/FXA/FXP/FXE/FXR, using the
firmware's live catalog and state. Firmware updates, routing, panel remapping,
bulk/delete and BLE writes are outside this editor profile. Demo is explicitly
labelled and is not a real connection. The app does not attest a binary hash
from PONG alone. Local file hashes detect changes; they are not a publisher
signature or a guarantee of device compatibility.

Reports: https://github.com/danmigdev/hyperrig/issues
Project: https://github.com/danmigdev/hyperrig
Nothing is uploaded automatically. There are no donations or telemetry.
Original third-party licenses and required notices are included verbatim.
"""


def preview_readme(variant):
    if not variant["read_only_editor"]:
        return README
    text = README.replace("stock-to-v3", "stock-to-v4")
    text = text.replace("This package contains a reviewed TANK MINI application and bounded RAM tools.",
        "This package contains a statically reviewed v4 TANK MINI application and bounded RAM tools.\n"
        "Planned recovery: hold any ONE footswitch while powering on. This behavior\n"
        "has not been verified on hardware. It is application-level recovery and\n"
        "does not cover a damaged application header, entry point or guard.")
    text = text.replace("The existing image's earlier unit tests are not a claim\n"
                        "that this package has been installed successfully on another unit.",
                        "V3 boot/audio/editor observations remain historical. Static inheritance\n"
                        "does not establish v4 boot, audio, USB operation or recovery.")
    text = text.replace("The editor enables USB GAIN/PLOAD/PSAVE/SNAPSAVE/FXA/FXP/FXE/FXR, using the\n"
                        "firmware's live catalog and state. Firmware updates, routing, panel remapping,\n"
                        "bulk/delete and BLE writes are outside this editor profile.",
                        "The v4 editor permits PING and read queries only. All mutation families\n"
                        "remain disabled until v4 has its own reviewed target evidence. Historical\n"
                        "v3 protocol observations are recorded as provenance, not as v4 results.")
    return text


def build(output=DEFAULT_OUTPUT, *, editor=DEFAULT_EDITOR, executable=False, variant="v3"):
    spec = release_variant(variant)
    output, editor = Path(output).resolve(), Path(editor).resolve()
    require(not output.exists(), "Use a new output directory; existing packages are preserved")
    require(output.parent.is_dir(), "Output parent must already exist")
    # Read and validate every allowed input before creating an output package.
    files = {}
    for source, destination, digest in spec["assets"]:
        raw = safe_file(ROOT, source).read_bytes()
        require(sha(raw) == digest, "Pinned payload changed: " + source)
        files[destination] = raw
    for name in runtime_files(variant):
        files[name] = safe_file(ROOT, name).read_bytes()
    web, editor_info = editor_assets(editor, variant=variant)
    files.update(web)
    files.update({"README.txt": preview_readme(spec).encode("utf-8"), "start.cmd": launch_script(),
                  "launch_editor.cmd": launch_script("--editor"), "check.cmd": launch_script("--check-only")})
    require(set(files) == expected_files(variant=variant), "Unexpected build inventory")
    output.mkdir()
    for name, raw in files.items():
        write_file(output, name, raw)
    if executable:
        compile_executable(output)
        files["HyperRig-MINI-Installer.exe"] = (output / "HyperRig-MINI-Installer.exe").read_bytes()
        files["runtime-licenses.txt"] = (output / "runtime-licenses.txt").read_bytes()

    def artifact(path, **extra):
        return {"path": path, "sha256": sha(files[path]), "bytes": len(files[path]), **extra}

    manifest = {
        "schema": 1, "kind": KIND, "variant": variant, "project": "HyperRig", "target": "tank-mini",
        "stock_identity": "TANK MINI_009", "stock_usb": [0x4c4a, 0xc755], "rom_usb": [0x4c4a, 0x8057],
        "jedec_hex": "eb6014", "application_range": [0x4000, 0x82000],
        "firmware": artifact(spec["assets"][0][1]),
        "writer": artifact("assets/writer-a.bin", slot=0x1c20000, build_tag=3953063795,
                           elf_path="assets/writer-a.elf", elf_sha256=sha(files["assets/writer-a.elf"])),
        "reader": artifact("assets/reader-b.bin", slot=0x1c28000,
                           elf_path="assets/reader-b.elf", elf_sha256=sha(files["assets/reader-b.elf"])),
        "reset": artifact("assets/reset-a.bin", slot=0x1c20000,
                          elf_path="assets/reset-a.elf", elf_sha256=sha(files["assets/reset-a.elf"])),
        "qualification": qualification_flags(spec),
        "recovery": {"policy": "any-one-footswitch" if variant == "v4" else "all-three-footswitches",
            "description": ("Planned: hold any ONE footswitch while powering on; not hardware verified."
                            if variant == "v4" else "Historical all-three-switch guard; cold-boot recovery not verified."),
            "hardware_verified": False, "damaged_application_covered": False},
        "editor": editor_info, "runtime": {"source_entry": "tools/launch_mini_installer.py",
            "executable": "HyperRig-MINI-Installer.exe" if executable else None,
            "platform": "Windows x64", "python_minimum": "3.12", "automatic_elevation": False},
        "provenance": {"builder_sha256": sha(files["tools/build_mini_installer_bundle.py"]),
            "application_kind": "full-port-application-area", "writer_embeds_unit_plan": False,
            "writer_rom_callbacks": {"send": 0x1e008e4, "receive": 0x1e0089a, "handler_slot": 0x1c01264},
            "private_unit_data_included": False, "historical_evidence_required_at_runtime": False},
        "files": {name: sha(raw) for name, raw in sorted(files.items())},
    }
    raw = encoded(manifest)
    write_file(output, "release.json", raw)
    write_file(output, "release.sha256", (sha(raw) + "\n").encode("ascii"))
    return check_bundle(output)


def check_bundle(output, *, isolated=True):
    output = Path(output).resolve(strict=True)
    raw = safe_file(output, "release.json").read_bytes()
    require(len(raw) < 1024 * 1024, "Oversized release manifest")
    require(safe_file(output, "release.sha256").read_bytes() == (sha(raw) + "\n").encode("ascii"),
            "Release seal differs")
    manifest = json.loads(raw)
    require(manifest.get("schema") == 1 and manifest.get("kind") == KIND, "Wrong release kind")
    spec = release_variant(manifest.get("variant", "v3"))
    require(manifest.get("firmware", {}).get("sha256") == spec["image_sha256"]
            and manifest["firmware"].get("path") == spec["assets"][0][1], "Release variant/firmware binding differs")
    executable = manifest.get("runtime", {}).get("executable")
    require(executable in (None, "HyperRig-MINI-Installer.exe"), "Unexpected runtime executable")
    require(set(manifest["files"]) == expected_files(executable=bool(executable), variant=spec["name"]), "Release inventory differs from explicit allowlist")
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    require(actual == set(manifest["files"]) | {"release.json", "release.sha256"}, "Unexpected or missing package file")
    for name, digest in manifest["files"].items():
        require(re.fullmatch(r"[0-9a-f]{64}", digest) and sha(safe_file(output, name).read_bytes()) == digest,
                "Package file hash differs: " + name)
    for _, name, digest in spec["assets"]:
        require(manifest["files"][name] == digest, "Known payload pin differs")
    require(manifest["qualification"] == qualification_flags(spec), "Preview qualification flags changed")
    for name, digest in PROTECTED_EDITOR_SHA.items():
        require(manifest["files"]["editor/web/" + name] == digest, "Protected editor policy differs: " + name)
    profile = json.loads(safe_file(output, "editor/profile.json").read_bytes())
    qualification_raw = safe_file(output, "editor/qualification.json").read_bytes()
    editor = manifest.get("editor", {})
    require(editor.get("image_sha256") == spec["image_sha256"]
            and editor.get("families") == ([] if spec["read_only_editor"] else FAMILIES)
            and (editor.get("read_only", False) is spec["read_only_editor"])
            and editor.get("entry") == "editor/web/tankmini.html"
            and editor.get("profile") == "editor/profile.json"
            and editor.get("qualification") == "editor/qualification.json",
            "Editor release metadata differs from its variant")
    require(profile["image_sha256"] == spec["image_sha256"] and profile["firmware_version"] == "tankm_fw M5.71 rel ble"
            and profile["capabilities"] == {"identity": True, "read": True, "write": False, "panel": False}
            and profile["command_capabilities"] == {} and profile["command_validation"] is None
            and profile["write_validation"] is None, "Portable editor capability scope differs")
    if spec["read_only_editor"]:
        qualification = json.loads(qualification_raw)
        require(profile["hardware_verified"] is False and profile["family_capabilities"] == {}
                and profile["family_validation"] == {} and profile["family_qualification"] == {}
                and profile["derived_from"]["report_sha256"] == ONE_SWITCH_REPORT_SHA
                and profile["derived_from"]["source_image_sha256"] == IMAGE_SHA
                and profile["derived_from"]["target_image_sha256"] == spec["image_sha256"]
                and profile["derived_from"]["hardware_observations_inherited_as_v4_proof"] is False
                and qualification["kind"] == "hyperrig-mini-v4-read-only-editor-scope"
                and qualification["image_sha256"] == spec["image_sha256"]
                and qualification["enabled_families"] == [] and qualification["hardware_verified"] is False
                and qualification["qualification_pending"] is True
                and qualification["source_observations_apply_to_target_image"] is False
                and qualification["current_image_mutations_physically_retested"] is False
                and qualification["static_inheritance"] == profile["derived_from"],
                "V4 editor must remain read-only with explicit historical inheritance")
    else:
        require(profile["hardware_verified"] is True and profile["family_capabilities"] == {"usb-cdc": FAMILIES}
                and profile["family_validation"] == {"usb-cdc": [{"path": "editor/qualification.json", "sha256": sha(qualification_raw)}]},
                "V3 editor capability scope differs")
    html = safe_file(output, "editor/web/tankmini.html").read_text("utf-8")
    marker = "globalThis.HYPERRIG_MINI_BUILD="
    require(html.count(marker) == 1, "Editor HTML profile count differs")
    tail = html.split(marker, 1)[1]
    embedded, end = json.JSONDecoder().raw_decode(tail)
    require(embedded == profile and tail[end:end + 1] == ";", "Editor HTML/profile binding differs")
    # Existing pure ELF validators execute from only this copy, outside the
    # repository import path. -I also excludes the current user's site packages.
    if isolated:
        program = ("import sys,json;sys.path.insert(0,sys.argv[1]);"
                   "from hyperrig.installer.core import load_release;"
                   "r=load_release(sys.argv[1]);"
                   "print(json.dumps({'result':'pass','device_io':False}))")
        result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", program, str(output)],
                                cwd=output, capture_output=True, text=True, timeout=60)
        require(result.returncode == 0, "Isolated release check failed: " + result.stderr[-3000:])
        require(json.loads(result.stdout) == {"result": "pass", "device_io": False}, "Unexpected isolated result")
    return {"result": "pass", "directory": str(output), "release_sha256": sha(raw),
            "files": len(manifest["files"]), "bytes": sum(safe_file(output, n).stat().st_size for n in manifest["files"]),
            "isolated_check": isolated, "device_io": False, "hardware_qualified": False}


def compile_executable(output):
    """Use the already installed PyInstaller; no dependency installation."""
    import importlib.metadata
    require(os.name == "nt" and sys.maxsize > 2**32, "Windows x64 executable build required")
    importlib.metadata.version("pyinstaller")
    licenses = runtime_licenses(output)
    with tempfile.TemporaryDirectory(prefix="hyperrig-mini-pyinstaller-") as temporary:
        temp = Path(temporary)
        command = [sys.executable, "-B", "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
                   "--console", "--name", "HyperRig-MINI-Installer", "--distpath", str(temp / "dist"),
                   "--workpath", str(temp / "work"), "--specpath", str(temp),
                   "--paths", str(output), "--paths", str(output / "upstream/pi32v2-isa"),
                   "--hidden-import", "tools.install_mini_app", "--hidden-import", "tools.probe_mini_app_writer",
                   "--hidden-import", "rtmidi", "--hidden-import", "rtmidi._rtmidi",
                   "--hidden-import", "serial.tools.list_ports", "--hidden-import", "serial.tools.list_ports_windows",
                   "--add-data", str(output / "upstream/pi32v2-isa/isa/pi32v2.toml") + os.pathsep + "isa",
                   "--add-data", str(output / "upstream/pi32v2-isa/docs/SOURCES.md") + os.pathsep + "docs",
                   str(output / "tools/launch_mini_installer.py")]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(command, cwd=output, env=environment, capture_output=True, text=True, timeout=300)
        require(result.returncode == 0, "PyInstaller failed: " + (result.stdout + result.stderr)[-6000:])
        shutil.copyfile(temp / "dist/HyperRig-MINI-Installer.exe", output / "HyperRig-MINI-Installer.exe")
    (output / "runtime-licenses.txt").write_text(licenses, encoding="utf-8", newline="\n")


def runtime_licenses(output):
    # Preserve licenses from the installed distributions, not arbitrary files
    # from the environment. These are the runtime additions, not private inputs.
    import importlib.metadata
    sections = ["Standalone runtime components. No packages were downloaded.\n"]
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    require(python_license.is_file(), "Installed Python license is missing")
    sections.append("CPython\n" + python_license.read_text("utf-8"))
    for name in ("pyinstaller", "python-rtmidi", "pyserial"):
        dist = importlib.metadata.distribution(name)
        license_paths = [f for f in (dist.files or ()) if any(word in Path(str(f)).name.lower() for word in ("license", "copying")) and
                         ".dist-info/" in str(f).replace("\\", "/")]
        sections.append(name + " " + dist.version)
        if not license_paths and name == "pyserial":
            require(dist.version == "3.5", "No reviewed license for this pyserial version")
            notice = (output / "editor/THIRD_PARTY_LICENSES.md").read_text("utf-8")
            heading = "## 8. pyserial 3.5: BSD 3-Clause License"
            require(notice.count(heading) == 1, "Original pyserial license section differs")
            section = notice.split(heading, 1)[1].split("\n## ", 1)[0]
            match = re.search(r"```text\n(.*?)\n```", section, re.S)
            require(match is not None and "Copyright (c) 2001-2020 Chris Liechti" in match[1],
                    "Original pyserial license text is missing")
            sections.append(match[1])
            continue
        require(license_paths, "Installed distribution license missing: " + name)
        for item in license_paths:
            sections.append(dist.locate_file(item).read_text("utf-8"))
    # The Windows Python distribution supplies the shared Tcl/Tk license here.
    path = Path(sys.base_prefix) / "tcl/tk8.6/license.terms"
    require(path.is_file(), "Installed Tcl/Tk license missing")
    sections.append("Tcl/Tk 8.6\n" + path.read_text("utf-8"))
    return "\n\n".join(sections)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build", type=Path)
    action.add_argument("--check-only", type=Path)
    parser.add_argument("--editor", type=Path, default=DEFAULT_EDITOR)
    parser.add_argument("--executable", action="store_true")
    parser.add_argument("--variant", choices=("v3", "v4"), default="v3")
    args = parser.parse_args(argv)
    require(not args.executable or args.build, "--executable is a build option")
    result = build(args.build, editor=args.editor, executable=args.executable, variant=args.variant) if args.build else check_bundle(args.check_only)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
