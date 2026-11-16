# Build the first HyperRig MINI release

The [Build release artifacts workflow](https://github.com/danmigdev/hyperrig/actions/workflows/release.yml)
builds all preview downloads from one Git commit. It runs only when explicitly
started on `main`. It never publishes a release automatically.

## Run on GitHub

1. Open **Actions > Build release artifacts > Run workflow**.
2. Select `main` and a version such as `0.1.0-preview.1`.
3. Set the Android version code, initially `10001`. Increase it for each APK
   distributed to users, including subsequent preview versions.
4. Leave **Attach all artifacts to a draft prerelease** selected to prepare a
   release for review. Clear it to build Actions artifacts only.
5. Wait for `prepare`, `windows`, `android`, `assemble`, and, if selected, `draft`.
   Download the complete `HyperRig-MINI-<version>` artifact from the run, or open
   the draft under **Releases**. Review its notes and files before publishing.

The source archive and all generated artifacts refer to the same commit.
The workflow refuses stable version numbers while this installer is a developer
preview. A published release is never overwritten. An existing draft can be
refreshed only when it targets the same commit; use a new preview version for a
changed source commit.

## Outputs

| Artifact | Contents |
| --- | --- |
| `HyperRig-MINI-<version>-Windows-x64.zip` | Standalone Windows executable, firmware, bounded RAM tools, USB editor and licenses. No Python installation needed by the user. |
| `HyperRig-MINI-<version>-Android.apk` | Signed Android 7+ editor. Preserves native DEX and bridges; BLE mutations remain disabled. |
| `HyperRig-MINI-<version>-web-editor.zip` | Pinned v4 editor and Python localhost launcher. |
| `HyperRig-MINI-<version>-firmware.zip` | Pinned v4 application-area image, provenance and licenses. Not a full flash dump. |
| `HyperRig-<version>-source.zip` | Exact `git archive` of the checkout. |
| `windows-provenance.json`, `android-provenance.json` | Source/input identity and packaging checks. |
| `release-manifest.json`, `SHA256SUMS`, `RELEASE_NOTES.md` | Artifact hashes, build provenance and user-facing release instructions. |

The Windows executable is currently unsigned. The Android APK uses the existing
HyperRig signing identity; its expected certificate SHA256 is pinned in the
input lock. Checksums detect corruption; they are not a Windows publisher
signature or a claim of device compatibility.

## Reviewed inputs

The original complete firmware C project has not been recovered. This workflow
**packages the reviewed v4 binary unchanged**, rather than claiming to compile a
new firmware from C. The Windows executable is compiled from the current checkout;
the Android resources and web assets are rebuilt around the preserved native shell.

[`release/mini-v4-inputs.lock.json`](../release/mini-v4-inputs.lock.json) pins the
archive and every input file. `HyperRig-MINI-v4-inputs-02.zip` is stored as an
asset of the private draft `build-inputs-mini-v4-02`. It contains only:

- The reviewed application image, reader/writer/reset binaries and ELF files.
- The sealed preview 05 editor, profile, qualification summary and licenses.
- The minimal licensed instruction decoder used by package validation.
- A reference release manifest and an Android native shell with old web assets
  and old APK signatures removed.

No full device dumps, user presets, raw hardware reports, executable from a
developer workstation, signing keys or credentials are included. The input
archive and generated outputs are release assets, never tracked Git files.

To create a new reviewed input set, use `tools/create_release_inputs.py` with the
reviewed sealed bundle, native APK and **new** output/lock paths. Review the
allowlist, provenance, licenses and privacy audit before uploading. Do not
replace an asset or lock silently: a changed input set requires a new revision
and review. The current creator deliberately accepts only the recorded preview
05 seal.

## Signing and permissions

Configure these four **repository Actions secrets** before the first run:

| Secret | Value |
| --- | --- |
| `HYPERRIG_ANDROID_KEYSTORE_BASE64` | Base64 of the private PKCS#12 signing keystore. |
| `HYPERRIG_ANDROID_KEY_ALIAS` | Alias of the existing signing key. |
| `HYPERRIG_ANDROID_STORE_PASSWORD` | Keystore password. |
| `HYPERRIG_ANDROID_KEY_PASSWORD` | Private key password. |

Keep an independent private backup of the signing key. Do not generate a new
key for each run: users need the same signing identity to update the app.
The builder writes the keystore only into a temporary directory, removes it on
exit, and passes password environment-variable names to `apksigner`. It does not
print signing arguments or upload the temporary directory.

Only the Android build step receives signing secrets. The workflow has no PR
trigger. Build jobs have read-only repository permission. The preparation job
needs `contents: write` to read a **draft** input release (GitHub restricts draft
visibility to push-capable callers); it receives no signing secrets. The optional
draft job needs `contents: write` to upload outputs. Checkout credentials are not
persisted. Official actions use full commit pins, and packaging dependency
versions, Apktool checksum and Android Build Tools version are fixed.

Actions artifacts expire after 30 days; the internal input transfer expires
after 7 days. Draft release assets persist until explicitly removed.

## Verification and local use

CI checks source privacy, archive membership and hashes, traversal/symlink
rejection, sealed Windows inventory, isolated Python loading and the executable's
`--check-only` mode. Android checks the certificate, signature, ZIP alignment,
version, native DEX, service registrations and protected policy bytes. The actual
editor scripts are parsed and the pure policy rejects BLE mutations and wrong
device identities. Assembly checks both builds refer
to the same source, input set and run, then verifies `SHA256SUMS`.

These are offline packaging checks. They do not test a pedal, phone, audio,
Bluetooth writes, physical switches or recovery from an interrupted flash write.

For a local build, use Python 3.12+, a Git checkout, GitHub CLI authentication to
download the input asset, and a new output directory:

```powershell
python tools/build_release.py fetch --output build/ci-inputs
python -m pip install -r tools/release/requirements-windows.txt
python tools/build_release.py windows --inputs build/ci-inputs/HyperRig-MINI-v4-inputs-02.zip --output build/local-windows --version 0.1.0-preview.1
python tools/build_release.py portable --inputs build/ci-inputs/HyperRig-MINI-v4-inputs-02.zip --output build/local-portable --version 0.1.0-preview.1
```

The portable and Android modes need Node.js 20+ for offline editor policy checks.
The Android mode additionally needs Java 21+, Android SDK Build Tools 36.0.0,
`ANDROID_HOME`, and the four signing variables in the process environment. Do
not put their values in scripts, shell history, tracked files or build artifacts.
`finish` accepts only the complete expected Windows, Android and portable output
set; `publish_release_draft.py` rechecks its checksums before attaching files.
