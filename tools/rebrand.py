"""Produce HyperRig-branded local copies of the original G/B packages and app.

No installer execution, device connection, firmware write or publication.
The Mini port is a separate, unfinished native firmware project.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.branding import rename_text, rename_fixed, rebrand_firmware, rebrand_installer
from bootstrap import download_checked

LICENSES = {"LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md"}
TEXT = {".html", ".js", ".json", ".txt", ".md", ".xml", ".smali", ".yml", ".properties"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_asset(entry):
    path = ROOT / "artifacts/alpha11" / entry["name"]
    if sha(path.read_bytes()) != entry["sha256"]:
        raise ValueError("original asset differs from pinned manifest")
    return path


def write_under(root, name, data):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("generated path escapes output directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def windows(entry, destination):
    original = checked_asset(entry)
    files, evidence = {}, {"source": entry["name"], "source_sha256": entry["sha256"], "firmware": []}
    with zipfile.ZipFile(original) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = rename_text(info.filename, network=False)
            payload = archive.read(info)
            suffix = Path(name).suffix.lower()
            if Path(name).name in LICENSES:
                pass  # Attribution and original licence text remain verbatim.
            elif name.endswith("_app.bin"):
                before = payload
                payload, changes = rebrand_firmware(payload)
                evidence["firmware"].append({"file": name, "source_sha256": sha(before),
                                             "sha256": sha(payload), "replacements": changes,
                                             "crc_verified": True, "mini_compatible": False})
            elif name.endswith("HyperRig-Installer.exe"):
                payload, evidence["installer"] = rebrand_installer(payload)
            elif suffix in TEXT:
                payload = rename_text(payload.decode("utf-8-sig")).encode("utf-8")
            files[name] = payload
    for firmware in evidence["firmware"]:
        name = firmware["file"][:-4] + ".json"
        metadata = json.loads(files[name])
        metadata["sha256"] = firmware["sha256"]
        metadata["source_sha256"] = firmware["source_sha256"]
        metadata.pop("flash_image_sha256", None)  # No complete derivative flash image was built.
        metadata["project"] = "HyperRig"
        files[name] = (json.dumps(metadata, indent=2) + "\n").encode()
    folder = next(iter(files)).split("/", 1)[0]
    note = ("HyperRig local derivative of UltraRig alpha11.\n"
            "This package still targets the original TANK-G/TANK-B board revision.\n"
            "It is NOT the TANK MINI port. Branding and package CRCs have been checked;\n"
            "device installation and runtime behavior have not been tested.\n"
            "Original LICENSE.md, NOTICE.md and THIRD_PARTY_LICENSES.md are retained.\n"
            "Author telemetry/update/donation URLs are disabled with hyperrig.invalid.\n")
    files[folder + "/DERIVATION.txt"] = note.encode()
    output = destination / "windows"
    for name, payload in files.items():
        write_under(output, name, payload)
    packed = destination / rename_text(entry["name"], network=False)
    with zipfile.ZipFile(packed, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    with zipfile.ZipFile(packed) as archive:
        if archive.testzip() is not None:
            raise ValueError("rebuilt Windows ZIP has a bad CRC")
    evidence.update(output=str(packed.relative_to(ROOT)), sha256=sha(packed.read_bytes()))
    print(f"Built {packed.name}; G/B package, not a Mini firmware", flush=True)
    return evidence


def android(entry, destination, java, keytool):
    source = checked_asset(entry)
    lock = json.loads((ROOT / "research/sources.lock.json").read_text(encoding="utf-8"))
    for name in ("apktool", "apk_signer"):
        tool = lock[name]
        download_checked(tool["url"], ROOT / "tools/vendor" / tool["name"], tool["sha256"])
    apktool = ROOT / "tools/vendor" / lock["apktool"]["name"]
    signer = ROOT / "tools/vendor" / lock["apk_signer"]["name"]
    project = ROOT / "build/android-hyperrig"
    framework = ROOT / "tools/vendor/apktool-framework"
    if not project.exists():
        subprocess.run([java, "-jar", str(apktool), "d", str(source), "-o", str(project),
                        "-p", str(framework)], cwd=ROOT, check=True)
    # Rewrite native class names and their references together, then let smali
    # rebuild DEX indices/checksums. Raw DEX string replacement is insufficient.
    changed = 0
    for path in sorted(project.rglob("*")):
        if not path.is_file() or path.relative_to(project).parts[0] in ("original", "build", "dist"):
            continue
        if path.name in LICENSES:
            continue
        if path.suffix.lower() in TEXT:
            text = path.read_text(encoding="utf-8")
            after = rename_text(text)
            if after != text:
                path.write_text(after, encoding="utf-8", newline="\n")
                changed += 1
        renamed = project / rename_text(path.relative_to(project).as_posix(), network=False)
        if renamed != path:
            if not renamed.resolve().is_relative_to(project.resolve()):
                raise ValueError("renamed Android path outside generated project")
            renamed.parent.mkdir(parents=True, exist_ok=True)
            if renamed.exists():
                raise ValueError("Android rename would overwrite another source")
            path.rename(renamed)
    # A new vector resource replaces the old launcher symbol without editing bitmaps.
    icon = '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
 <path android:fillColor="#071819" android:pathData="M0,0h108v108h-108z"/>
 <path android:fillColor="#63e0f5" android:pathData="M29,25h12v24h26v-24h12v58h-12v-22h-26v22h-12z"/>
 <path android:fillColor="#ff7a1a" android:pathData="M84,78h9v9h-9z"/>
</vector>
'''
    write_under(project, "res/drawable/hyperrig_icon.xml", icon.encode())
    manifest = project / "AndroidManifest.xml"
    text = manifest.read_text(encoding="utf-8").replace('android:icon="@mipmap/ic_launcher"',
                                                       'android:icon="@drawable/hyperrig_icon"')
    text = text.replace('android:roundIcon="@mipmap/ic_launcher_round"',
                        'android:roundIcon="@drawable/hyperrig_icon"')
    manifest.write_text(text, encoding="utf-8", newline="\n")
    for name in LICENSES:
        write_under(project, "assets/hyperrig-licenses/" + name,
                    (ROOT / "recovered/ultrarig-original" / name).read_bytes())
    unsigned = ROOT / "build/android/HyperRig-local-unsigned.apk"
    unsigned.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([java, "-jar", str(apktool), "b", str(project), "-o", str(unsigned),
                    "-p", str(framework)], cwd=ROOT, check=True)
    signing = ROOT / "build/signing"
    signing.mkdir(parents=True, exist_ok=True)
    keystore = signing / "hyperrig-release.p12"
    if not keystore.exists():
        subprocess.run([keytool, "-genkeypair", "-keystore", str(keystore), "-storetype", "PKCS12",
                        "-storepass", os.environ["HYPERRIG_ANDROID_STORE_PASSWORD"], "-keypass", os.environ["HYPERRIG_ANDROID_KEY_PASSWORD"], "-alias", "hyperrig",
                        "-keyalg", "RSA", "-keysize", "3072", "-validity", "3650",
                        "-dname", "CN=HyperRig Local Development", "-noprompt"], check=True)
    signed = ROOT / "build/android/signed"
    # Do not overwrite an APK while signing; use a new output directory per unsigned hash.
    signed = signed / sha(unsigned.read_bytes())[:16]
    if not list(signed.glob("*.apk")):
        subprocess.run([java, "-jar", str(signer), "--apks", str(unsigned), "--out", str(signed),
                        "--ks", str(keystore), "--ksAlias", "hyperrig", "--ksPass", os.environ["HYPERRIG_ANDROID_STORE_PASSWORD"],
                        "--ksKeyPass", os.environ["HYPERRIG_ANDROID_KEY_PASSWORD"]], check=True)
    apks = list(signed.glob("*.apk"))
    if len(apks) != 1:
        raise ValueError("expected exactly one signed derivative APK")
    subprocess.run([java, "-jar", str(signer), "--apks", str(apks[0]), "--onlyVerify"], check=True)
    target = destination / "HyperRig-local-android.apk"
    shutil.copyfile(apks[0], target)
    for name in LICENSES:
        shutil.copyfile(ROOT / "recovered/ultrarig-original" / name, destination / name)
    print(f"Built {target.name}, package com.hyperrig.app, signed with local development key", flush=True)
    return {"source": entry["name"], "source_sha256": entry["sha256"],
            "output": str(target.relative_to(ROOT)), "sha256": sha(target.read_bytes()),
            "package": "com.hyperrig.app", "label": "HyperRig", "source_files_changed": changed,
            "signature": "local development key; signature/alignment checked", "installed_on_device": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android", action="store_true", help="also rebuild and sign the Android app")
    parser.add_argument("--java", default="java")
    parser.add_argument("--keytool", default="keytool")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "research/input-manifest.json").read_text(encoding="utf-8"))
    destination = ROOT / "build/hyperrig"
    destination.mkdir(parents=True, exist_ok=True)
    report = {"project": "HyperRig", "originals_modified": False, "mini_port_complete": False,
              "windows": [], "android": None}
    for entry in manifest["release"]["assets"]:
        if entry["name"].endswith(".zip"):
            report["windows"].append(windows(entry, destination))
    # Convenient standalone editor, sourced from the just-generated v2 package.
    web = next((destination / "windows").glob("*v2*/web"))
    shutil.copytree(web, destination / "web", dirs_exist_ok=True)
    for name in LICENSES:
        shutil.copyfile(ROOT / "recovered/ultrarig-original" / name, destination / name)
    if args.android:
        apk = next(x for x in manifest["release"]["assets"] if x["name"].endswith(".apk"))
        report["android"] = android(apk, destination, args.java, args.keytool)
    output = destination / "rebranding-report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
