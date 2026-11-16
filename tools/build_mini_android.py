"""Build a separate HyperRig MINI APK, preserving the original native bridges.

Offline packaging only. No adb, phone installation, server or device transport.
The pinned original APK editor is byte-identical to the original desktop one.
The already rebranded/pinned HyperRig APK supplies native code; its DEX files
are copied without decompiling/reassembling or changing their native APIs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_mini_app import (SOURCE, SOURCE_SHA, CONVERTER_SHA, LICENSES,
                                  checked, derive_html, load_profile, relative)
from hyperrig.branding import rename_text

ORIGINAL = ROOT / "artifacts/alpha11/UltraRig-alpha11-android.apk"
ORIGINAL_SHA = "cbf63092505bc77d8aa402f97374c9d8229f0794ba9cf1acc8d3489325a51717"
BASE = ROOT / "build/hyperrig/HyperRig-local-android.apk"
BASE_SHA = "ec88936a2994115f27989440ad8a9ad761abf2e30eb7a34c46307c6838c48438"
CERTIFICATE_SHA = "522da03967e456170850291fd9e29bf4a4e202a619aa17e4dd9efadef8958ee1"
PACKAGE = "com.hyperrig.app"
PROTECTED_ASSETS = ("assets/native-bridge.js", "assets/capacitor.plugins.json",
                    "assets/public/cordova.js", "assets/public/cordova_plugins.js",
                    "assets/public/nam2chip.js")
ANDROID = "{http://schemas.android.com/apk/res/android}"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_files(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("invalid/duplicate APK entries")
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}


def audit_inputs():
    checked(ORIGINAL, ORIGINAL_SHA)
    checked(BASE, BASE_SHA)
    original, base = archive_files(ORIGINAL), archive_files(BASE)
    editor = checked(SOURCE / "web/tankg.html", SOURCE_SHA)
    if original["assets/public/index.html"] != editor:
        raise ValueError("Android editor differs from the pinned desktop editor; specific derivation required")
    # tools/rebrand.py used read_text(), so the known G/B derivative normalized
    # the source CRLF to LF before applying the same branding function.
    normalized = editor.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if base["assets/public/index.html"] != rename_text(normalized).encode("utf-8"):
        raise ValueError("rebranded APK editor has unreviewed changes")
    if sha(original["assets/public/nam2chip.js"]) != CONVERTER_SHA:
        raise ValueError("Android model converter differs from pinned source")
    for name in PROTECTED_ASSETS:
        if base[name] != original[name]:
            raise ValueError("native/Capacitor/converter asset changed in rebrand: " + name)
    plugins = json.loads(base["assets/capacitor.plugins.json"])
    if plugins != [{"pkg":"@capacitor-community/bluetooth-le", "classpath":"com.capacitorjs.community.plugins.bluetoothle.BluetoothLe"},
                   {"pkg":"@capacitor/app", "classpath":"com.capacitorjs.plugins.app.AppPlugin"}]:
        raise ValueError("native plugin inventory changed")
    dex = sorted(n for n in base if re.fullmatch(r"classes(?:[2-9]\d*)?\.dex", n))
    if dex != ["classes.dex"] + [f"classes{i}.dex" for i in range(2, 9)]:
        raise ValueError("expected exactly the original eight DEX files")
    for token in (b"Lcom/hyperrig/app/MainActivity;", b"HyperRigNative", b"shareLast", b"saveFile"):
        if not any(token in base[name] for name in dex):
            raise ValueError("expected native file/share interface missing: " + repr(token))
    text = editor.decode("utf-8")
    if 'const pickTransport = () => (APP || !SerialTransport.available()) && BleTransport.available() ? BleTransport : SerialTransport;' not in text:
        raise ValueError("original Android transport selection changed")
    for name in LICENSES:
        if base["assets/hyperrig-licenses/" + name] != (SOURCE / name).read_bytes():
            raise ValueError("base APK attribution differs")
    return original, base, {"original_apk":relative(ORIGINAL), "original_apk_sha256":ORIGINAL_SHA,
            "rebranded_base_apk":relative(BASE), "rebranded_base_sha256":BASE_SHA,
            "original_android_html_sha256":sha(original["assets/public/index.html"]),
            "android_html_identical_to_desktop":True, "plugins":plugins,
            "base_editor_derivation":"rename_text(original editor with read_text LF normalization), exact match",
            "native_usb_serial_plugin_present":False, "android_default_transport":"Capacitor BluetoothLe / Nordic UART",
            "desktop_transport":"Web Serial / USB CDC 3654:5155",
            "native_file_share_bridge":"HyperRigNative, retained in DEX and HTML",
            "ble_pairing_may_persist_bond_state":True,
            "protected_assets":{n:sha(base[n]) for n in PROTECTED_ASSETS},
            "dex":{n:{"base_sha256":sha(base[n]), "original_sha256":sha(original[n])} for n in dex}}


def android_config(raw):
    config = json.loads(raw)
    if config.get("appId") != PACKAGE or config.get("appName") != "HyperRig":
        raise ValueError("base Capacitor identity changed")
    result = copy.deepcopy(config)
    result["appName"] = "HyperRig MINI"
    messages = result["plugins"]["BluetoothLe"]["displayStrings"]
    messages["noDeviceFound"] = ("No HyperRig MINI found. This app requires standalone tankm_fw firmware; "
                                "stock MINI and Tank-G/B firmware are incompatible. Offline demo remains available.")
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def android_manifest(raw):
    manifest = ET.fromstring(raw)
    if manifest.get("package") != PACKAGE:
        raise ValueError("Android namespace must stay com.hyperrig.app")
    app = manifest.find("application")
    if app is None or app.get(ANDROID+"label") != "@string/app_name":
        raise ValueError("Android label anchor changed")
    activities = [x.get(ANDROID+"name") for x in app.findall("activity")]
    if PACKAGE + ".MainActivity" not in activities:
        raise ValueError("native MainActivity missing")
    return {"package":PACKAGE, "application_label_resource":"app_name", "activities":activities,
            "usb_host_feature":any(x.get(ANDROID+"name") == "android.hardware.usb.host" for x in manifest.findall("uses-feature")),
            "permission_names":[x.get(ANDROID+"name") for x in manifest.findall("uses-permission")]}


def mini_labels(text):
    for name in ("app_name", "title_activity_main"):
        before = f'<string name="{name}">HyperRig</string>'
        if text.count(before) != 1:
            raise ValueError("Android label anchor changed: " + name)
        text = text.replace(before, f'<string name="{name}">HyperRig MINI</string>')
    return text


def check_javascript(html, profile, js_profile, js_ui):
    # Compile the actual asset scripts and execute only the pure policy. No
    # DOM, Bluetooth, Web Serial, native plugin or network object is supplied.
    code = r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
const scripts=[...v.html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
scripts.concat([v.profile_js,v.ui_js]).forEach(s=>new vm.Script(s));
const c=vm.createContext({HYPERRIG_MINI_BUILD:v.profile});vm.runInContext(v.profile_js,c);
const m=c.HyperRigMini,wrong=['TANK MINI_009','PONG tankg_fw M5.71 rel ble Nov 12 2026 16:05:32',
 'PONG tankb_fw M5.71 rel ble Nov 12 2026 16:05:32'];
if(wrong.some(p=>m.acceptPong(p,'ble-nus').ok))throw Error('wrong identity accepted');
const pong='PONG '+v.profile.firmware_version+' Nov 12 2026 16:05:32',r=m.acceptPong(pong,'ble-nus');
if(r.ok!==v.profile.capabilities.read)throw Error('MINI read capability changed');
if(m.commandPolicy('PLIST','ble-nus').allowed!==v.profile.capabilities.read)throw Error('PLIST gate mismatch');
const forbidden=['PSAVE 31 Scratch','FXP 1 0 51','LDBEGIN 8','IRBEGIN 256 0 48000','FSDO a','UBOOT'];
if(forbidden.some(l=>m.commandPolicy(l,'ble-nus').allowed))throw Error('unqualified BLE mutation allowed');
process.stdout.write(JSON.stringify({inline_scripts_parsed:scripts.length,profile_scripts_parsed:2,
 wrong_identities_rejected:wrong.length,ble_queries_require_matching_pong:true,
 ble_mutations_enabled:false,device_io:false}));
"""
    payload = {"html":html, "profile":profile, "profile_js":js_profile.decode("utf-8"), "ui_js":js_ui.decode("utf-8")}
    run = subprocess.run(["node", "-e", code], input=json.dumps(payload), text=True,
                         encoding="utf-8", capture_output=True, check=True, cwd=ROOT)
    return json.loads(run.stdout)


def command(argv, log_path):
    run = subprocess.run([str(a) for a in argv], cwd=ROOT, text=True, encoding="utf-8",
                         errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log_path.write_text(run.stdout, encoding="utf-8", newline="\n")
    if run.returncode:
        raise RuntimeError(f"build command failed; see {relative(log_path)}")
    return run.stdout


def verify_signature_log(text):
    if ("zipalign verified" not in text or "signature verified [v2, v3]" not in text
            or f"SHA256: {CERTIFICATE_SHA}" not in text or "0 errors" not in text):
        raise ValueError("APK signature/alignment/local certificate verification failed")
    return {"certificate_sha256":CERTIFICATE_SHA, "schemes":["v2","v3"], "alignment_verified":True}


def validate_payload(candidate, base, *, html, config, profile_js, ui_js):
    if {n for n in candidate if n.endswith(".dex")} != {n for n in base if n.endswith(".dex")}:
        raise ValueError("native DEX inventory changed")
    for name in [n for n in base if n.endswith(".dex")] + list(PROTECTED_ASSETS):
        if candidate.get(name) != base[name]:
            raise ValueError("native/converter payload changed: " + name)
    expected = {"assets/public/index.html":html.encode("utf-8"), "assets/capacitor.config.json":config,
                "assets/public/mini-profile.js":profile_js, "assets/public/mini-ui.js":ui_js}
    for name, data in expected.items():
        if candidate.get(name) != data:
            raise ValueError("derived APK asset differs: " + name)
    for name in LICENSES:
        path = "assets/hyperrig-licenses/" + name
        if candidate.get(path) != base[path]:
            raise ValueError("attribution changed: " + name)
    return {"dex_files_byte_identical":8, "native_assets_byte_identical":len(PROTECTED_ASSETS),
            "licences_byte_identical":len(LICENSES), "derived_assets_verified":list(expected)}


def build(output, manifest, *, java="java", check_only=False):
    output = output.resolve()
    if not output.is_relative_to(ROOT / "build") or output == ROOT / "build":
        raise ValueError("Android output must be a dedicated directory under build/")
    for forbidden in (ROOT/"build/hyperrig", ROOT/"build/android", ROOT/"build/android-hyperrig", ROOT/"build/android-hyperrig-verified"):
        if output.is_relative_to(forbidden):
            raise ValueError("MINI APK must not modify the G/B Android output directories")
    original, base, audit = audit_inputs()
    profile = load_profile(manifest)
    if profile["capabilities"]["write"]:
        raise ValueError("Android BLE has no qualified full-write profile; USB evidence is insufficient")
    html, patches = derive_html(original["assets/public/index.html"].decode("utf-8"), profile)
    js_profile = (ROOT/"app/mini/mini-profile.js").read_bytes()
    js_ui = (ROOT/"app/mini/mini-ui.js").read_bytes()
    config = android_config(base["assets/capacitor.config.json"])
    javascript = check_javascript(html, profile, js_profile, js_ui)
    lock = json.loads((ROOT/"research/sources.lock.json").read_text("utf-8"))
    tools = {}
    for name in ("apktool", "apk_signer"):
        item = lock[name]; path = ROOT/"tools/vendor"/item["name"]
        checked(path, item["sha256"])
        tools[name] = {"path":relative(path), "sha256":item["sha256"], "version":item["version"]}
    report = {"project":"HyperRig", "target":"tank-mini", "kind":"standalone-port-android-editor",
              "firmware_manifest":relative(manifest), "firmware_manifest_sha256":sha(manifest.read_bytes()),
              "firmware_image_sha256":profile["image_sha256"], "profile":profile, "source_audit":audit,
              "implementation_files":{relative(p):sha(p.read_bytes()) for p in
                  [Path(__file__), ROOT/"tools/build_mini_app.py", ROOT/"app/mini/mini-profile.js", ROOT/"app/mini/mini-ui.js"]},
              "tools":tools, "html_patches":patches, "javascript_checks":javascript,
              "installed_on_phone":False, "android_runtime_verified":False, "firmware_runtime_verified":False,
              "device_io":False, "native_usb_serial_added":False, "native_ble_bridge_preserved":True,
              "android_ble_write_capability":False, "check_only":check_only}
    if check_only:
        return report
    keystore = ROOT/"build/signing/hyperrig-release.p12"
    if not keystore.is_file():
        raise ValueError("the existing HyperRig local signing key is required; no replacement key generated")
    output.mkdir(parents=True, exist_ok=True)
    work_root = ROOT/"build/mini-android-work"
    work_root.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=profile["image_sha256"][:12]+"-", dir=work_root)).resolve()
    if not work.is_relative_to(work_root.resolve()):
        raise ValueError("Android work directory escaped build/")
    project, framework = work/"decoded", ROOT/"tools/vendor/apktool-framework"
    apktool, signer = ROOT/tools["apktool"]["path"], ROOT/tools["apk_signer"]["path"]
    command([java,"-jar",apktool,"d","-s",BASE,"-o",project,"-p",framework], work/"decode.log")
    manifest_before = (project/"AndroidManifest.xml").read_bytes()
    report["manifest"] = android_manifest(manifest_before)
    if report["manifest"]["usb_host_feature"]:
        raise ValueError("unexpected native USB feature requires review")
    strings = project/"res/values/strings.xml"
    strings.write_text(mini_labels(strings.read_text("utf-8")), encoding="utf-8", newline="\n")
    for name, data in {"assets/public/index.html":html.encode("utf-8"), "assets/capacitor.config.json":config,
                       "assets/public/mini-profile.js":js_profile, "assets/public/mini-ui.js":js_ui}.items():
        (project/name).write_bytes(data)
    note = ("HyperRig MINI: full original editor derived for standalone tankm_fw firmware.\n"
            "Native Capacitor BLE and file/share bridges are preserved. No native USB serial driver was added.\n"
            "This APK has not been installed or tested on a phone or running MINI port.\n"
            "Stock MINI and Tank-G/B firmware are incompatible. Offline demo remains available.\n"
            "The local firmware hash is a build association, not a device PONG attestation.\n"
            "BLE pairing can persist bond information independently of the command capability gate.\n"
            "Package com.hyperrig.app and local signing key match the existing HyperRig G/B APK; installing would replace that app.\n")
    (project/"assets/hyperrig-mini-derivation.txt").write_text(note, encoding="utf-8", newline="\n")
    unsigned = work/"HyperRig-MINI-local-unsigned.apk"
    command([java,"-jar",apktool,"b",project,"-o",unsigned,"-p",framework], work/"build.log")
    signed_dir = work/"signed"
    command([java,"-jar",signer,"--apks",unsigned,"--out",signed_dir,"--ks",keystore,"--ksAlias","hyperrig",
             "--ksPass",os.environ["HYPERRIG_ANDROID_STORE_PASSWORD"],"--ksKeyPass",os.environ["HYPERRIG_ANDROID_KEY_PASSWORD"]], work/"sign.log")
    signed = list(signed_dir.glob("*.apk"))
    if len(signed) != 1:
        raise ValueError("expected one signed MINI APK")
    verify = command([java,"-jar",signer,"--apks",signed[0],"--onlyVerify"], work/"signature-verify.log")
    report["signature"] = verify_signature_log(verify)
    packaged = archive_files(signed[0])
    report["payload_checks"] = validate_payload(packaged, base, html=html, config=config, profile_js=js_profile, ui_js=js_ui)
    # Re-decode the final APK to inspect its actual manifest/resources, not just
    # the source XML supplied to the packaging tool. DEX remains untouched.
    verified = work/"verified"
    command([java,"-jar",apktool,"d","-s",signed[0],"-o",verified,"-p",framework], work/"redecode.log")
    report["manifest_redecoded"] = android_manifest((verified/"AndroidManifest.xml").read_bytes())
    labels = ET.fromstring((verified/"res/values/strings.xml").read_bytes())
    values = {x.get("name"):x.text for x in labels.findall("string")}
    if any(values.get(n) != "HyperRig MINI" for n in ("app_name", "title_activity_main")):
        raise ValueError("final MINI launcher label did not survive packaging")
    checked(ORIGINAL, ORIGINAL_SHA); checked(BASE, BASE_SHA)
    target = output/"HyperRig-MINI-local-android.apk"
    shutil.copyfile(signed[0], target)
    for name in LICENSES:
        shutil.copyfile(SOURCE/name, output/name)
    (output/"DERIVATION.txt").write_text(note, encoding="utf-8", newline="\n")
    report.update(output=relative(target), apk_sha256=sha(target.read_bytes()), apk_bytes=target.stat().st_size,
                  package=PACKAGE, label="HyperRig MINI", work_directory=relative(work),
                  original_and_gb_apks_unchanged=True,
                  bundled_assets={n:sha(data) for n,data in packaged.items() if n.startswith("assets/")},
                  logs={relative(p):sha(p.read_bytes()) for p in sorted(work.glob("*.log"))})
    (output/"android-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--firmware-manifest", type=Path, default=ROOT/"build/hyperrig-mini-integrated/firmware-manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT/"build/hyperrig-mini-integrated/android")
    parser.add_argument("--java", default="java")
    parser.add_argument("--check-only", action="store_true", help="audit input assets/profile and JS only; no APK build")
    args = parser.parse_args(argv)
    result = build(args.output, args.firmware_manifest.resolve(), java=args.java, check_only=args.check_only)
    print(json.dumps({k:result.get(k) for k in ("target","check_only","output","apk_sha256","firmware_image_sha256",
                       "package","native_usb_serial_added","android_ble_write_capability","installed_on_phone","device_io")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
