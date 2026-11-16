"""Build release artifacts from current sources and an immutable reviewed input set.

No device access, private hardware reports or developer workstation paths are
needed. Firmware bytes are packaged unchanged; this is not a firmware C build.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_installer_bundle as bundle
from tools.create_release_inputs import zip_bytes

LOCK = ROOT / "release/mini-v4-inputs.lock.json"
PROJECT = "https://github.com/danmigdev/hyperrig"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def version(value):
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-preview\.[1-9][0-9]*", value),
            "Use a developer preview version, for example 0.1.0-preview.1")
    return value


def code(value):
    require(2 <= int(value) <= 2_100_000_000, "Android version code must be 2..2100000000")
    return int(value)


def read_lock():
    lock = json.loads(LOCK.read_bytes())
    require(lock["schema"] == 1 and lock["repository"] == "danmigdev/hyperrig", "Unexpected input lock")
    return lock


def archive_files(raw, expected=None):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        require(len(names) == len(set(names)), "Duplicate archive entry")
        require(sum(e.file_size for e in entries) <= 150_000_000, "Oversized input archive")
        if expected is not None:
            require(set(names) == set(expected), "Archive inventory differs from reviewed input set")
        result = {}
        for entry in entries:
            name = entry.filename
            path = PurePosixPath(name)
            require(entry.orig_filename == name and not path.is_absolute() and path.as_posix() == name
                    and not any(p in ("", ".", "..") for p in path.parts)
                    and ":" not in name and "\\" not in name
                    and not stat.S_ISLNK(entry.external_attr >> 16), "Unsafe archive member")
            require(not entry.is_dir(), "Input archives contain files only")
            raw_file = archive.read(entry)
            if expected is not None:
                pin = expected[name]
                require(len(raw_file) == pin["bytes"] and bundle.sha(raw_file) == pin["sha256"],
                        "Input file differs: " + name)
            result[name] = raw_file
        return result


def load_inputs(path):
    lock = read_lock()
    raw = path.read_bytes()
    require(bundle.sha(raw) == lock["sha256"], "Reviewed input archive hash differs")
    files = archive_files(raw, lock["files"])
    require(bundle.sha(files["reference-release.json"]) == lock["reference_release_sha256"], "Reference seal differs")
    require(bundle.sha(files["assets/hyperrig-mini-v4.app.bin"]) == bundle.ONE_SWITCH_IMAGE_SHA,
            "Reviewed firmware image differs")
    return files, lock


def run(argv, *, cwd=None, env=None):
    # Do not echo command arguments or subprocess output: signing tools and
    # host toolchains can include sensitive environment values and local paths.
    result = subprocess.run([str(a) for a in argv], cwd=cwd or ROOT, env=env,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{Path(str(argv[0])).name} failed (exit {result.returncode})")
    return result.stdout


def fetch(destination):
    lock = read_lock()
    require(not destination.exists(), "Use a new input directory")
    destination.mkdir(parents=True)
    run(["gh", "release", "download", lock["tag"], "--repo", lock["repository"],
         "--pattern", lock["asset"], "--dir", destination])
    load_inputs(destination / lock["asset"])
    print("Reviewed input archive downloaded and verified.")


def provenance(release_version, lock, kind):
    commit = run(["git", "rev-parse", "HEAD"]).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "Source commit missing")
    return {"schema": 1, "version": version(release_version), "artifact": kind,
            "source_commit": commit,
            "source_tree_dirty": bool(run(["git", "status", "--porcelain", "--untracked-files=no"]).strip()),
            "release_builder_sha256": bundle.sha(Path(__file__).read_bytes()),
            "input_sha256": lock["sha256"],
            "reference_release_sha256": lock["reference_release_sha256"],
            "firmware_sha256": lock["firmware_sha256"],
            "firmware_rebuilt_from_C": False, "hardware_or_audio_test": False,
            "private_device_data_included": False,
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT")}


def write_zip(destination, prefix, files):
    require(not destination.exists(), "Preserve existing artifacts")
    destination.write_bytes(zip_bytes({prefix + "/" + n: raw for n, raw in files.items()}))


def check_editor(files):
    html = files["editor/web/tankmini.html"].decode("utf-8")
    scripts = [v.decode("utf-8") for n, v in files.items() if n.startswith("editor/web/") and n.endswith(".js")]
    scripts += re.findall(r"<script\b[^>]*>([\s\S]*?)</script>", html, re.I)
    payload = {"profile": json.loads(files["editor/profile.json"]), "scripts": scripts,
               "policy": files["editor/web/mini-profile.js"].decode("utf-8")}
    result = subprocess.run(["node", str(ROOT / "tools/release/check_editor.cjs")],
                            input=json.dumps(payload), capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "Editor syntax or transport policy checks failed: " + result.stderr[-1000:])


def build_windows(inputs, output, release_version):
    require(os.name == "nt" and sys.maxsize > 2**32, "Windows x64 build required")
    files, lock = load_inputs(inputs)
    folder = (output / "windows-work" / f"HyperRig-MINI-{release_version}-Windows-x64").resolve()
    folder.mkdir(parents=True)
    payload = {n: raw for n, raw in files.items() if n.startswith(("assets/", "editor/", "upstream/"))}
    for name in bundle.runtime_files("v4"):
        if not name.startswith("upstream/"):
            payload[name] = bundle.safe_file(ROOT, name).read_bytes()
    readme = f"""HyperRig MINI {release_version} - Windows x64 developer preview

For stock M-VAVE TANK MINI_009 only. No Python installation is needed.
Keep all extracted files together. Open HyperRig-MINI-Installer.exe.

1. Power on the MINI without pressing footswitches and connect a USB data cable.
2. Enable installation (Windows UAC), then Find connected devices. Select its MIDI input/output.
3. Create and verify backup. Keep USB/power connected and retain a separate private backup copy.
4. Install HyperRig. Wait for Ready to boot, then release all switches and click Boot HyperRig.
5. After HyperRig USB detected, open the editor. Connect > USB > the MINI serial port.
   Keep the installer window open while using the editor.

Already running HyperRig? Open launch_editor.cmd; do not reinstall firmware.
check.cmd validates this package without opening a device.

Illustrated guide: {PROJECT}/blob/v{release_version}/INSTALLATION.md
Support: {PROJECT}/issues

One assisted installation from restored stock completed. Independent installation,
interrupted-write recovery, v4 audio listening and complete panel mapping remain unqualified.
Return to stock only exits before firmware writing; it is not a post-install restore.
After a write error, retain power and the report and ask the maintainer before retrying.
Bluetooth mutations, routing, Footswitches and Stage remain disabled on the connected MINI.
No telemetry or automatic report uploads. Keep backups, presets and personal paths private.
Original component licenses and required notices are included in editor/ and runtime-licenses.txt.
"""
    payload.update({"README.txt": readme.encode("utf-8"),
                    "start.cmd": bundle.launch_script(), "check.cmd": bundle.launch_script("--check-only"),
                    "launch_editor.cmd": bundle.launch_script("--editor")})
    require(set(payload) == bundle.expected_files(variant="v4"), "Windows payload inventory differs")
    for name, raw in payload.items():
        bundle.write_file(folder, name, raw)
    bundle.compile_executable(folder)
    manifest = copy.deepcopy(json.loads(files["reference-release.json"]))
    manifest["release_version"] = release_version
    manifest["provenance"].update(provenance(release_version, lock, "windows-x64"))
    manifest["provenance"]["builder_sha256"] = bundle.sha(payload["tools/build_mini_installer_bundle.py"])
    manifest["files"] = {n: bundle.sha(bundle.safe_file(folder, n).read_bytes())
                         for n in sorted(bundle.expected_files(variant="v4", executable=True))}
    raw = bundle.encoded(manifest)
    bundle.write_file(folder, "release.json", raw)
    bundle.write_file(folder, "release.sha256", (bundle.sha(raw) + "\n").encode("ascii"))
    bundle.check_bundle(folder)
    checked = json.loads(run([folder / "HyperRig-MINI-Installer.exe", "--bundle", folder, "--check-only"]))
    require(checked["device_io"] is False and checked["package"]["result"] == "pass", "Executable validation failed")
    write_zip(output / f"{folder.name}.zip", folder.name,
              {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()})
    (output / "windows-provenance.json").write_bytes(bundle.encoded(manifest["provenance"]))
    print("Windows executable, sealed bundle and isolated package checks passed; no device access.")


def build_portable(inputs, output, release_version):
    files, lock = load_inputs(inputs)
    check_editor(files)
    prefix = f"HyperRig-MINI-{release_version}"
    firmware = {"hyperrig-mini-v4.app.bin": files["assets/hyperrig-mini-v4.app.bin"],
                "manifest.json": bundle.encoded(provenance(release_version, lock, "firmware")),
                "README.txt": ("HyperRig MINI v4 application-area image.\n"
                               "Use the matching HyperRig Windows installer and its verified per-pedal backup.\n"
                               "This is not a full device dump or an M-VAVE update file.\n"
                               "Do not flash it using a generic updater.\n"
                               f"Installation: {PROJECT}/blob/main/INSTALLATION.md\n").encode()}
    for name in ("LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md"):
        firmware[name] = files["editor/" + name]
    write_zip(output / f"{prefix}-firmware.zip", prefix + "-firmware", firmware)
    editor = {n.removeprefix("editor/"): raw for n, raw in files.items() if n.startswith("editor/")}
    editor["serve_editor.py"] = (ROOT / "tools/release/serve_editor.py").read_bytes()
    editor["release-provenance.json"] = bundle.encoded(provenance(release_version, lock, "web-editor"))
    editor["README.txt"] = ("HyperRig MINI v4 web editor\n\n"
                           "Windows users: the Windows installer ZIP already includes this editor and needs no Python.\n"
                           "Standalone use: install Python 3.12+, then run: python serve_editor.py\n"
                           "Open the displayed localhost URL in Edge or Chrome. Keep the terminal open.\n"
                           "Select Connect > USB and choose the MINI. Use Demo to explore without a pedal.\n"
                           "Preset banks show A/B/C; each preset has four scenes.\n"
                           "Bluetooth mutations, routing and panel remapping remain disabled.\n"
                           f"Guide: {PROJECT}/blob/main/INSTALLATION.md\n").encode()
    write_zip(output / f"{prefix}-web-editor.zip", prefix + "-web-editor", editor)
    print("Pinned firmware and web editor packages built; firmware and command policies unchanged.")


def android_tools(lock):
    sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "")
    tools = sdk / "build-tools" / lock["android"]["build_tools"]
    suffix = ".exe" if os.name == "nt" else ""
    paths = {n: tools / (n + suffix) for n in ("zipalign", "aapt")}
    paths["apksigner"] = tools / "lib/apksigner.jar"
    require(all(p.is_file() for p in paths.values()), "Install Android SDK Build Tools " + lock["android"]["build_tools"])
    return paths


def build_android(inputs, output, release_version, version_code):
    files, lock = load_inputs(inputs)
    check_editor(files)
    version_code = code(version_code)
    tools = android_tools(lock)
    required = ("HYPERRIG_ANDROID_KEYSTORE_BASE64", "HYPERRIG_ANDROID_KEY_ALIAS",
                "HYPERRIG_ANDROID_STORE_PASSWORD", "HYPERRIG_ANDROID_KEY_PASSWORD")
    require(all(os.environ.get(k) for k in required), "Configure all four Android signing secrets")
    native = archive_files(files["android/native-template.apk"])
    with tempfile.TemporaryDirectory(prefix="hyperrig-android-") as temporary:
        work = Path(temporary)
        key = work / "signing.p12"
        # Only this temporary file contains the private key; it is never an artifact.
        key.write_bytes(base64.b64decode(os.environ[required[0]], validate=True))
        key.chmod(0o600)
        source = work / "native.apk"
        source.write_bytes(files["android/native-template.apk"])
        pin = lock["android"]["apktool"]
        jar = work / "apktool.jar"
        local_jar = ROOT / "tools/vendor" / ("apktool_" + pin["version"] + ".jar")
        raw = local_jar.read_bytes() if local_jar.is_file() else urlopen(pin["url"], timeout=120).read()
        require(bundle.sha(raw) == pin["sha256"], "Apktool checksum differs")
        jar.write_bytes(raw)
        decoded = work / "decoded"
        run(["java", "-jar", jar, "d", "-s", "-o", decoded, "-p", work / "framework", source])
        config = decoded / "apktool.yml"
        text = config.read_text("utf-8")
        text, codes = re.subn(r"(?m)^(\s*versionCode:)\s*.*$", rf"\g<1> {version_code}", text)
        text, names = re.subn(r"(?m)^(\s*versionName:)\s*.*$", rf"\g<1> {release_version}", text)
        require(codes == names == 1, "APK version anchors changed")
        config.write_text(text, encoding="utf-8", newline="\n")
        public = decoded / "assets/public"
        public.mkdir(parents=True, exist_ok=True)
        for name, raw in files.items():
            if name.startswith("editor/web/") and name != "editor/web/index.html":
                target = "index.html" if name.endswith("/tankmini.html") else PurePosixPath(name).name
                (public / target).write_bytes(raw)
        # A separate presentation script leaves the pinned HTML, profile and
        # command policy byte-identical. Android's BLE policy still blocks writes.
        html = (public / "index.html").read_bytes()
        require(html.count(b"</body>") == 1, "Android HTML anchor changed")
        (public / "index.html").write_bytes(html.replace(b"</body>", b'<script src="android-preview.js"></script>\n</body>'))
        (public / "android-preview.js").write_bytes((ROOT / "tools/release/android-preview.js").read_bytes())
        metadata = provenance(release_version, lock, "android")
        metadata.update(android_version_code=version_code, package=lock["android"]["package"],
                        certificate_sha256=lock["android"]["certificate_sha256"],
                        bluetooth_mutations_enabled=False, native_dex_changed=False)
        (decoded / "assets/hyperrig-release.json").write_bytes(bundle.encoded(metadata))
        unsigned = work / "unsigned.apk"
        run(["java", "-jar", jar, "b", decoded, "-p", work / "framework", "-o", unsigned])
        aligned = work / "aligned.apk"
        run([tools["zipalign"], "-P", "16", "-f", "4", unsigned, aligned])
        signed = work / "signed.apk"
        signer = ["java", "-jar", tools["apksigner"]]
        run(signer + ["sign", "--ks", key, "--ks-key-alias", os.environ[required[1]],
                      "--ks-pass", "env:HYPERRIG_ANDROID_STORE_PASSWORD",
                      "--key-pass", "env:HYPERRIG_ANDROID_KEY_PASSWORD",
                      "--v4-signing-enabled", "false", "--out", signed, aligned])
        verification = run(signer + ["verify", "--verbose", "--print-certs", signed])
        require(lock["android"]["certificate_sha256"] in verification.lower()
                and "Verified using v2 scheme (APK Signature Scheme v2): true" in verification,
                "Android signing identity or v2 verification differs")
        run([tools["zipalign"], "-c", "-P", "16", "4", signed])
        badging = run([tools["aapt"], "dump", "badging", signed])
        require(f"name='{lock['android']['package']}'" in badging
                and f"versionName='{release_version}'" in badging and f"versionCode='{version_code}'" in badging,
                "Android application identity or release version differs")
        candidate = archive_files(signed.read_bytes())
        require({n: bundle.sha(v) for n, v in candidate.items() if n.endswith(".dex")} == lock["android"]["dex_sha256"],
                "Native Android DEX changed")
        for name in native:
            if name.startswith(("assets/", "META-INF/")):
                require(candidate.get(name) == native[name], "Native bridge or notice changed: " + name)
        for name in ("mini-profile.js", "mini-fx-ui.js", "nam2chip.js"):
            require(candidate["assets/public/" + name] == files["editor/web/" + name], "Android policy changed")
        shutil.copyfile(signed, output / f"HyperRig-MINI-{release_version}-Android.apk")
        metadata.update(signature_verified=True, alignment_verified=True, version_verified=True)
        (output / "android-provenance.json").write_bytes(bundle.encoded(metadata))
    print("Signed Android APK built; certificate, alignment, version, native DEX and policies verified. No phone test.")


def finish(output, release_version):
    lock = read_lock()
    prefix = f"HyperRig-MINI-{release_version}"
    expected = {f"{prefix}-Windows-x64.zip", f"{prefix}-firmware.zip", f"{prefix}-web-editor.zip",
                f"{prefix}-Android.apk", "windows-provenance.json", "android-provenance.json"}
    require({p.name for p in output.iterdir() if p.is_file()} == expected, "Release artifacts missing or unexpected")
    metadata = provenance(release_version, lock, "complete-release")
    for name in ("windows-provenance.json", "android-provenance.json"):
        record = json.loads((output / name).read_bytes())
        require(all(record.get(k) == metadata[k] for k in ("version", "source_commit", "input_sha256", "github_run_id", "github_run_attempt")),
                "Artifact provenance differs: " + name)
    source = output / f"HyperRig-{release_version}-source.zip"
    run(["git", "archive", "--format=zip", "--prefix", f"HyperRig-{release_version}/",
         "--output", source.resolve(), "HEAD"])
    metadata["artifacts"] = {p.name: {"sha256": bundle.sha(p.read_bytes()), "bytes": p.stat().st_size}
                             for p in sorted(output.iterdir()) if p.is_file()}
    (output / "release-manifest.json").write_bytes(bundle.encoded(metadata))
    notes = f"""HyperRig MINI {release_version} is a developer preview for stock M-VAVE TANK MINI_009.

**Start here:** download `{prefix}-Windows-x64.zip`, extract everything, and open `HyperRig-MINI-Installer.exe`.
The Windows ZIP includes the firmware and USB editor. No Python installation is needed.

[Installation guide with screenshots]({PROJECT}/blob/v{release_version}/INSTALLATION.md)

| Download | Purpose |
| --- | --- |
| Windows-x64.zip | Back up this pedal, install firmware and open the USB editor. |
| Android.apk | Android 7+ editor; Bluetooth reads only. Does not install firmware. |
| web-editor.zip | Standalone browser editor; Python 3.12+ localhost launcher included. |
| firmware.zip | Exact v4 application image and licenses; use the matching installer. |
| source.zip | Source snapshot for this build. |
| SHA256SUMS / release-manifest.json | File integrity and build provenance. |

The firmware is the pinned binary port, packaged unchanged; the original full C project is not available.
One assisted installation from restored stock completed. Independent installation, interrupted-write recovery,
v4 audio listening and complete physical switch/LED mapping remain unqualified.
The editor shows A/B/C preset banks and four scenes per preset. Footswitches and Stage remain disabled.
Android signing, packaging and policy checks are offline checks, not a phone or Bluetooth hardware test.
Keep your own pedal's verified backup private. No telemetry or automatic report uploads.

Source commit: `{metadata['source_commit']}`
Input SHA256: `{lock['sha256']}`
"""
    (output / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8", newline="\n")
    sums = "".join(f"{bundle.sha(p.read_bytes())}  {p.name}\n" for p in sorted(output.iterdir()) if p.is_file())
    (output / "SHA256SUMS").write_text(sums, encoding="ascii", newline="\n")
    print("All release artifacts collected; source archive, provenance and SHA256SUMS generated.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fetch", "windows", "portable", "android", "finish"))
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", type=version, default="0.1.0-preview.1")
    parser.add_argument("--android-version-code", type=code, default=10001)
    args = parser.parse_args()
    if args.mode == "fetch":
        fetch(args.output)
        return
    args.output.mkdir(parents=True, exist_ok=True)
    if args.mode == "finish":
        finish(args.output, args.version)
    else:
        require(args.inputs is not None, "--inputs is required")
        if args.mode == "android":
            build_android(args.inputs, args.output, args.version, args.android_version_code)
        else:
            {"windows": build_windows, "portable": build_portable}[args.mode](args.inputs, args.output, args.version)


if __name__ == "__main__":
    main()
