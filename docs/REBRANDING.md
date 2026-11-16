# Local HyperRig packages

This document describes historical artifacts. The current product bundle is built
by `tools/build_hyperrig_editor.py` using `app/project.json`. It is English-only,
has no donation features, and directs reports to
[HyperRig GitHub issues](https://github.com/danmigdev/hyperrig/issues/new/choose).

The request to rename firmware and applications is applied to the
derived copies produced in `build/hyperrig/`. Samples published by the
original project remain in `artifacts/` for verifying hashes, addresses,
and reverse-engineering results. Licenses, attributions, and provenance
references remain identifiable as such.

## Results

| Local file/folder | Contents |
|---|---|
| `build/hyperrig/HyperRig-alpha11-v1-win.zip` | G/B v1 package, renamed Windows installer and firmware |
| `build/hyperrig/HyperRig-alpha11-v2-win.zip` | G/B v2 package, renamed Windows installer and firmware |
| `build/hyperrig/HyperRig-local-android.apk` | `com.hyperrig.app` app, HyperRig label, and H icon |
| `build/hyperrig/web/tankg.html` | HyperRig web editor |
| `build/hyperrig/windows/` | Already extracted Windows packages |
| `build/hyperrig/rebranding-report.json` | SHA-256 of copies and source samples |

These packages derive from UltraRig for **TANK-G/TANK-B**. They are not
the TANK MINI port. The native port is separate in `firmware/src/hyperrig_dot.c`
and `hyperrig_head.c`, with the `hyperrig_*` API; it remains incomplete.

## What changes

The firmware is decoded first. ASCII/UTF-16 replacements preserve length:
UltraRig and HyperRig both have eight characters. CRCs for each modified
payload, the JLFS directory, and the application area are recalculated;
the area is then SFC-encoded again and read back for checking.
Addresses, sizes, and the flash map remain those of the respective G/B sample.
JSON metadata receives the new hashes. No hash is invented for a
complete flash image that has not been produced.

The Windows installer is processed as a PyInstaller archive: Python
3.12 code and constants are read as data, names and text are renamed,
and PYZ and CArchive are rebuilt. Module opcodes and exception tables
are compared with the originals. The installer was not launched for
this verification, and its operation with a pedal has not been tested.

The Android app is decoded and rebuilt with
[Apktool](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3): the manifest,
package, Smali classes, resources, native bridge, and web page use HyperRig.
Rebuilding DEX updates string indices and checksums. A new H vector
serves as the icon. The APK also includes LICENSE, NOTICE, and original
component licenses among its assets.

The signature is created with a **local development key**, distinct from
the original producer's key, and verified with
[Uber APK Signer](https://github.com/patrickfav/uber-apk-signer/releases/tag/v1.3.0).
Verification confirmed alignment and APK v2/v3 signatures. The key is in
`build/signing/`, excluded from Git; it is not a release-signing key.
The app was not installed on a phone during this session.

File prefixes, application keys, and format identifiers containing
the original name are also renamed: compatibility with files exported
by UltraRig is not automatically guaranteed. The old project's telemetry,
update, and donation endpoints are replaced with the reserved
`hyperrig.invalid` domain; the fork is not attributed a nonexistent
website or support service. M-VAVE recovery references and component
licenses remain the originals.

## Reproducing the packages

The packages pinned in `research/input-manifest.json`, Python 3.12,
and, for Android, Java with `keytool` are required. Tool versions and
their hashes are in `research/sources.lock.json`.

```powershell
python tools/rebrand.py
python tools/rebrand.py --android --keytool "C:/Program Files/Android/Android Studio/jbr/bin/keytool.exe"
python -m unittest discover -s tests -v
```

The first command produces Windows and web packages; the second adds Android.
The `build/android-hyperrig` directory retains rebuildable Smali and resources.
The script does not publish packages, run installers, or access the pedal.

Local validation: 54 tests passed, including CRCs of the four images,
Windows bytecode integrity, DEX checksums, and Android identity and resources.
The four inline scripts in the two checked web pages pass `node --check`.
Decoding the final APK confirms `com.hyperrig.app` and the new icon.
Searching the produced payloads for the old name finds no product
occurrences; attributions and derivation documentation remain.
