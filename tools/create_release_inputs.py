"""Create reviewed CI inputs from a sealed MINI bundle and the native APK shell.

Offline only. Explicit inventories exclude executables, dumps, presets, keys and
private reports. Generated inputs belong in release storage, never in Git.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_installer_bundle as bundle

REFERENCE_SEAL = "52554a680596dddc5aff0ad215cd8356f45c1e8be61055d08dcd36c7efddb9cb"
APK_ASSETS = {
    "assets/native-bridge.js", "assets/capacitor.config.json",
    "assets/capacitor.plugins.json", "assets/public/cordova.js",
    "assets/public/cordova_plugins.js",
    "assets/hyperrig-licenses/LICENSE.md", "assets/hyperrig-licenses/NOTICE.md",
    "assets/hyperrig-licenses/THIRD_PARTY_LICENSES.md",
}


def zip_bytes(files):
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(files.items()):
            item = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, raw)
    return result.getvalue()


def native_template(apk):
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        bundle.require(len(names) == len(set(names)) and archive.testzip() is None, "Invalid APK")
        files = {n: archive.read(n) for n in names if not n.endswith("/")
                 and not re.fullmatch(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))", n, re.I)
                 and (not n.startswith("assets/") or n in APK_ASSETS)}
    bundle.require(APK_ASSETS <= files.keys(), "Native Android bridges or licenses missing")
    dex = {n: bundle.sha(raw) for n, raw in files.items() if n.endswith(".dex")}
    bundle.require(set(dex) == {"classes.dex"} | {f"classes{i}.dex" for i in range(2, 9)}, "DEX inventory differs")
    # The packaged editor and all historical derivation metadata are omitted.
    return zip_bytes(files), dex


def create(source, apk, output, lock_path):
    bundle.require(not output.exists() and not lock_path.exists(), "Preserve existing input sets and locks")
    checked = bundle.check_bundle(source)
    bundle.require(checked["release_sha256"] == REFERENCE_SEAL, "Use the reviewed preview 05")
    manifest = json.loads((source / "release.json").read_bytes())
    names = {n for n in manifest["files"] if n.startswith(("assets/", "editor/", "upstream/"))}
    files = {n: bundle.safe_file(source, n).read_bytes() for n in names}
    files["reference-release.json"] = (source / "release.json").read_bytes()
    template, dex = native_template(apk)
    files["android/native-template.apk"] = template
    raw = zip_bytes(files)
    revision = re.fullmatch(r"HyperRig-MINI-v4-inputs-([0-9]{2})\.zip", output.name)
    bundle.require(revision is not None, "Use a numbered input archive name")
    lock = {
        "schema": 1, "repository": "danmigdev/hyperrig", "tag": "build-inputs-mini-v4-" + revision[1],
        "asset": output.name, "sha256": bundle.sha(raw),
        "reference_release_sha256": REFERENCE_SEAL,
        "firmware_sha256": bundle.ONE_SWITCH_IMAGE_SHA,
        "files": {n: {"sha256": bundle.sha(v), "bytes": len(v)} for n, v in sorted(files.items())},
        "android": {"source_apk_sha256": bundle.sha(apk.read_bytes()), "dex_sha256": dex,
                    "certificate_sha256": "522da03967e456170850291fd9e29bf4a4e202a619aa17e4dd9efadef8958ee1",
                    "package": "com.hyperrig.app", "min_sdk": 24, "build_tools": "36.0.0",
                    "apktool": {"version": "3.0.3", "sha256": "dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423",
                                "url": "https://github.com/iBotPeaches/Apktool/releases/download/v3.0.3/apktool_3.0.3.jar"}},
        "scope": {"firmware_rebuilt_from_C": False, "private_device_data_included": False,
                  "signing_material_included": False, "android_old_web_assets_included": False},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    lock_path.write_bytes(bundle.encoded(lock))
    return {"files": len(files), "sha256": lock["sha256"], "bytes": len(raw)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(create(args.bundle, args.apk, args.output, args.lock)))
