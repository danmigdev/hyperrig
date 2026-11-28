"""Build a debug Android editor from a checked HyperRig editor bundle.

    python tools/build_android_editor.py --bundle build/release-parts/editor --output build/android-editor

The output must be a new directory under build/. Android SDK, Java 21 and Node.js
are required. The editor bundle is the same one consumed by the desktop builder.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_dev_editor as editor  # noqa: E402


def tone_key(path):
    if path is None:
        return None
    key = Path(path).read_text(encoding='utf-8').strip()
    editor.require(re.fullmatch(r't3k_pub_[A-Za-z0-9_-]{6,200}', key), 'this is not a publishable TONE3000 key')
    return key


def mobile_tone(source, key):
    if key is None:
        return source
    old = b'if (location.protocol !== "hyperrig:") return;'
    editor.require(source.count(old) == 1, 'unexpected TONE3000 editor interface')
    picture = b'src: "tone3000/picture?id=" + tone.id'
    editor.require(source.count(picture) == 1, 'unexpected TONE3000 picture interface')
    adapter = (ROOT / 'app/android/tone3000-mobile.js').read_bytes()
    prefix = b'globalThis.HYPERRIG_TONE3000_KEY=' + json.dumps(key).encode('ascii') + b';\n'
    return prefix + adapter + b'\n' + source.replace(old, b'if (location.protocol !== "hyperrig:" && !window.Capacitor?.isNativePlatform?.()) return;').replace(
        picture, b'src: (globalThis.hyperrigTonePicture?.() || "tone3000/picture?id=" + tone.id)')


def prepare(bundle, output, key=None):
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    editor.require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    editor.check(bundle)
    meta = json.loads((bundle / 'bundle.json').read_bytes())
    product = meta['area'].get('product')
    version = (ROOT / 'firmware/ultrarig/mini/product/VERSION').read_text(encoding='utf-8').strip()
    editor.require(product and product.get('version') == version, 'the editor must match the product version')
    editor.require(re.fullmatch(r'\d+\.\d+\.\d+', version), 'the product version is not numeric')
    source = ROOT / 'app/android'
    shutil.copytree(source, output, ignore=shutil.ignore_patterns('node_modules', 'www', '.gradle', 'build', 'local.properties', 'assets'))
    shutil.copytree(bundle / 'editor/web', output / 'www')
    tone = output / 'www/product-tone3000.js'
    if key:
        tone.write_bytes(mobile_tone(tone.read_bytes(), key))
    licenses = output / 'www/licenses'
    licenses.mkdir()
    for name in ('LICENSE.md', 'NOTICE.md', 'THIRD_PARTY_LICENSES.md'):
        shutil.copy2(bundle / 'editor' / name, licenses / name)
    return version


def build(bundle, output, key=None):
    output = Path(output).resolve()
    version = prepare(bundle, output, key)
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    editor.require(npm, 'npm is required')
    subprocess.run([npm, 'ci'], cwd=output, check=True)
    subprocess.run([npm, 'exec', '--', 'cap', 'sync', 'android'], cwd=output, check=True)
    gradle = output / 'android' / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
    subprocess.run([str(gradle), ':app:assembleDebug', f'-PhyperrigVersion={version}', '--console', 'plain'], cwd=gradle.parent, check=True)
    apk = output / 'android/app/build/outputs/apk/debug/app-debug.apk'
    editor.require(apk.is_file(), 'Gradle did not produce an APK')
    check(bundle, apk, key)
    return apk


def check(bundle, apk, key=None):
    """Check that the APK contains the exact web files of a checked bundle."""
    bundle = Path(bundle).resolve()
    editor.check(bundle)
    meta = json.loads((bundle / 'bundle.json').read_bytes())
    version = (ROOT / 'firmware/ultrarig/mini/product/VERSION').read_text(encoding='utf-8').strip()
    editor.require(meta['area'].get('product', {}).get('version') == version, 'the editor must match the product version')
    with zipfile.ZipFile(apk) as archive:
        for path in (bundle / 'editor/web').rglob('*'):
            if path.is_file():
                name = 'assets/public/' + path.relative_to(bundle / 'editor/web').as_posix()
                expected = mobile_tone(path.read_bytes(), key) if path.name == 'product-tone3000.js' and path.parent == bundle / 'editor/web' else path.read_bytes()
                editor.require(archive.read(name) == expected, f'APK editor differs: {name}')
        plugins = json.loads(archive.read('assets/capacitor.plugins.json'))
        editor.require(any(p.get('classpath', '').endswith('.BluetoothLe') for p in plugins), 'Bluetooth plugin is missing')
        if key:
            for suffix in ('.BrowserPlugin', '.AppPlugin'):
                editor.require(any(p.get('classpath', '').endswith(suffix) for p in plugins), f'TONE3000 plugin is missing: {suffix}')
        editor.require('AndroidManifest.xml' in archive.namelist(), 'Android manifest is missing')
    inspect_manifest(apk, version, bool(key))
    return 'pass'


def inspect_manifest(apk, version, tone_enabled):
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    editor.require(sdk, 'ANDROID_HOME or ANDROID_SDK_ROOT must name the Android SDK')
    tool = 'aapt.exe' if os.name == 'nt' else 'aapt'
    aapt = Path(sdk) / 'build-tools' / '36.0.0' / tool
    editor.require(aapt.is_file(), 'Android build-tools 36.0.0 is required to check the APK')
    badging = subprocess.check_output([str(aapt), 'dump', 'badging', str(apk)], text=True, encoding='utf-8')
    manifest = subprocess.check_output([str(aapt), 'dump', 'xmltree', str(apk), 'AndroidManifest.xml'], text=True, encoding='utf-8')
    editor.require(f"name='com.hyperrig.editor'" in badging and f"versionName='{version}'" in badging, 'APK package or version differs')
    editor.require(re.search(r'android:allowBackup\([^\n]+\)=\(type 0x12\)0x0\b', manifest), 'Android backup must be disabled')
    if tone_enabled:
        for name, value in (('scheme', 'com.hyperrig.editor'), ('host', 'tone3000'), ('path', '/callback')):
            editor.require(re.search(r'android:' + name + r'\([^\n]+\)="' + re.escape(value) + r'"', manifest), 'TONE3000 callback is missing')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--tone3000-key', type=Path, help='file containing the publishable TONE3000 key')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--output', type=Path)
    action.add_argument('--check', type=Path)
    args = parser.parse_args()
    key = tone_key(args.tone3000_key)
    print(check(args.bundle, args.check, key) if args.check else build(args.bundle, args.output, key))


if __name__ == '__main__':
    main()
