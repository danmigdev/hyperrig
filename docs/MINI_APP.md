# HyperRig MINI: full editor for the UltraRig port

This document describes historical artifacts. The current product bundle is built
by `tools/build_hyperrig_editor.py` using `app/project.json`. It is English-only,
has no donation features, and directs reports to
[HyperRig GitHub issues](https://github.com/danmigdev/hyperrig/issues/new/choose).

The derived app retains the original UltraRig alpha11 editor: chains and parallel
routing, presets and four scenes, capture/IR libraries, NAM/A2-Lite conversion,
EQ, metering, tuner and audio controls. The target is **UltraRig adapted to the
MINI as standalone firmware**, completely replacing the stock application.
It does not use the six modules or 21 presets of the M-VAVE firmware as the
product architecture. It contains no stock USB-MIDI/SysEx bridge.

## Local interface preview

```powershell
python -X utf8 tools/build_mini_app.py
python -m http.server 8765 --bind 127.0.0.1 --directory build/hyperrig-mini/web
```

Open <http://127.0.0.1:8765/tankmini.html#demo>. The original demo remains
complete and is marked **offline, no pedal connected**. It does not generate
audio on the MINI. The editor retains eight banks of four slots and four scenes:
compatibility with this persistent storage must be verified in the port,
without silently replacing it with the stock 21 × 92-byte layout.

Without `#demo`, the default build can send only `PING`; it does not claim
a connection to working firmware. The expected identity is
`PONG tankm_fw M5.xx ...`, with the rest of the UltraRig format unchanged.
The identities `tankg_fw`, `tankb_fw` and `TANK MINI_009` are rejected before
initial queries or changes. The Bluetooth name or USB VID alone does not
identify a valid MINI port.

The existing APK,
`build/hyperrig/HyperRig-local-android.apk`, remains the G/B variant and has not
been changed. A separate
[`HyperRig-MINI-local-android.apk`](../build/hyperrig-mini-integrated/android/HyperRig-MINI-local-android.apk)
now also exists, derived using the integrated candidate's manifest. It retains
Capacitor, BLE, the file/share bridge and original licenses. No installation on
a phone or physical connection was performed to develop this app.

## Local MINI APK

```powershell
python -X utf8 tools/build_mini_android.py --check-only
python -X utf8 tools/build_mini_android.py
python -X utf8 -m unittest tests.test_mini_android -v
```

The builder defaults to
`build/hyperrig-mini-integrated/firmware-manifest.json`; it also accepts
`--firmware-manifest` and `--output`. The candidate associated with this
delivery is `f8835a7fd45b1b324d66c457434c7943d70525ed5eb98b514aaac1095031f068`.
The resulting APK has SHA-256
`194431db62554d0d286de9bb1e2b27b863f8593efbf16193192ab5565b4597cc`;
input, toolchain and asset hashes, logs and checks are in
[`android-report.json`](../build/hyperrig-mini-integrated/android/android-report.json).
Rebuilding may change the APK hash: use the report from the actual build.

`assets/public/index.html` in the original UltraRig APK is **byte-identical**
to the pinned web frontend. The same MINI derivation is therefore used, without
substituting a different Android frontend. The eight DEX files from the existing
locally rebranded HyperRig package and five Capacitor/Cordova/converter assets are
preserved byte for byte. Apktool 3.0.3 and uber-apk-signer 1.3.0 are checked against
the pinned local hashes; the final manifest is decoded again. The six offline
tests verify provenance, the BLE gate, bridge preservation, labels, certificate
and plan behavior without building.

The package uses the display name **HyperRig MINI**, the
`com.hyperrig.app` namespace and the existing local HyperRig key; v2/v3 signing
and alignment are verified. Installing it would therefore replace the HyperRig
G/B app with the same namespace, rather than install alongside it.
The builder does not start adb, installations, servers or transports.

The original Android transport is the native Capacitor **BluetoothLe** plugin;
the other components are App and `HyperRigNative` for files/sharing.
There is no native USB serial plugin, and none has been added.
USB CDC/Web Serial belongs to the desktop path. The APK profile permits queries
after a correct MINI PONG, with writes and panel controls disabled;
any scoped USB evidence does not authorize BLE. Original pairing can save bonds
independently of the command gate, so "queries permitted" does not mean that
the transport performs no persistent writes of any kind. Android startup,
pairing, NUS and firmware operation still require verification on the real device.

## Provenance and transformations

`tools/build_mini_app.py` derives directly from
`recovered/ultrarig-original/web/tankg.html`, SHA-256
`247d152045a9d8f987281e7e943c1ea359ccc2db1392f6a0cb439587717e88e6`.
The original `nam2chip.js` converter has SHA-256
`af584a732fa8a0b03a388871947d490a383c5094d9391fed0f48b6336f255183`.
The builder checks these hashes and the uniqueness of every anchored change;
a new frontend version requires review, rather than a permissive patch.
`LICENSE.md`, `NOTICE.md` and `THIRD_PARTY_LICENSES.md` are copied unchanged.
Rebranding uses the existing local module; the original external update,
telemetry and support links remain replaced with `hyperrig.invalid`.

`app/mini/mini-profile.js` adds identity and capabilities without replacing
the original command or transport implementations. The check is inserted at
the start of `Pedal.cmd`, before the queue and any write.
`ERR MINI_APP ...` is a local rejection, clearly distinguishable from a
firmware response. Connection state and Bluetooth keys have a namespace
separate from G/B. Losing the connection clears the verified identity;
a new connection must perform the PONG check again.

The physical panel uses a MINI profile with **three switches**, while its pins,
LEDs and knobs are still unknown. The G/B design with 15 knobs and four switches
is not reused. The commands `FSA`, `FSMODE`, `FSPRESS`, `FSDO`, `FSLED`,
`LEDCFG` and views that assume the G/B panel remain blocked. This does not
convert the four software scenes into three scenes: these are separate concepts.

The app gate prevents host commands; it does not stop firmware tasks. In
particular, the port's audio audit identified the G writer at
`0x02015858..0x020158C2` on PA0..PA3, overlapping the MINI codec's PA1/PA2.
Removing or remapping it remains a firmware requirement even when the editor
only reads. A correct app profile alone does not make a G image bootable on
the MINI.

## Required firmware contract

The local primary sources are the original frontend and the bytes of
`analysis/firmware/m571_g_app/app.bin` (SHA-256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`).
The upstream project is pinned in `research/sources.lock.json` to commit
`658c89c2bcb2743c19c5caf0fb9704a8ce68212c` of
[UltraRig](https://github.com/manuaguirre9/ultrarig/tree/658c89c2bcb2743c19c5caf0fb9704a8ce68212c).
`research/mini-app-protocol.json` preserves **168 call sites**, the exact
request expressions, completion predicate, timeout and original line.
68 command names resolve directly; 102 call sites have dynamic arguments,
of which 14 do not statically resolve the name. The inventory does not present
these JavaScript expressions as fully resolved commands.

| Function | UltraRig requests | Completion required by the frontend |
|---|---|---|
| Identity | `PING` | `PONG <version> <date> <time>...`; MINI token `tankm_fw` |
| Effect catalog | `FXT` | type/parameter lines, then `FXT end` (legacy `fin`) |
| Chain and resources | `FXS`, `MEM`, `MODEL`, `LVL` | `FXS peak=...` ends the chain; other responses begin with the command name |
| Effect changes | `FXA`, `FXR`, `FXM`, `FXE`, `FXP`, `FXL`, `FXOS` | original prefixes/predicates and `ERR` errors; not a MINI binary ACK |
| Routing and capture EQ | `FXMIX`, `FXXO`, `FXIR`, `AMP`, `AMPX`, `AMPEQ` | `FXMIX end`, `FXXO end` terminators; `AMPEQ volume=` or `gain=` |
| Presets and scenes | `PLIST`, `PLOAD`, `PSAVE`, `PNEW`, `PDEL`, `PNAME`, `SNAP*` | `PLIST end current=...`; `SNAPS dddd current=...`; original save/load responses |
| NAM/A2-Lite captures | `LDBEGIN n`, `LDB off hex`, `LDEND crc32`, `CLIST/CLOAD/CSAVE/CREAD/CDEL` | `OK LDBEGIN`, `OK LDB off n`, `LOAD ...`; `CLIST end` |
| IR | `IRBEGIN samples gain rate`, `IRB off hex`, `IREND crc32`, `ILIST/ILOAD/ISAVE/IREAD/IDEL` | `OK IRBEGIN`, `OK IRB off n`, `IR ok ...`; `ILIST end` |
| Audio and globals | `AUDIO`, `GEQ`, `GAIN`, `HPF`, `LIM`, `SPUR`, `GLIDE`, `SPILL`, `STW`, `GSAVE` | arguments distinguish queries from changes; `GSAVE` persists data |
| Tempo/tuner | `BPM`, `TAP`, `TUNER`, `TUNE` | original protocol; no stock substitute |
| Events and diagnostics | `EVT`, `CRASH`, `LIFE`, `CLKSTATE`, `LVLSUB` | individual terminators; `@L` and `@K` are asynchronous |
| Bluetooth | `BLE`, `AUTH` | original bonding/MTU/keys; changes disabled in the read-only profile |
| Physical panel | `FSA`, `FSMODE`, `FSPRESS`, `FSDO`, `FSLED`, `LEDCFG` | requires a new MINI mapping; blocked |

All requests are text terminated by `\n`; the client also accepts CRLF
responses. Only one ordinary request is pending at a time. Lines beginning
`@L`/`@K` do not complete a request. `NOISE ms=`, `CALIB` and
`ERR CALIB stopped` have special asynchronous paths already present in the frontend.
The USB limit is 31 characters through M4.82 and 190 from M4.83, excluding newline.
Capture/IR blocks use offsets, hexadecimal data and a final IEEE CRC32.
The original parser and upload functions are retained, including their differing
timeout behavior: this work does not certify recovery of every original
transaction after a lost connection.

The port must retain the original handlers and semantics, not just the strings
in the table. A first read-only connection needs at least PING, FXT, MODEL, CLIST,
MEM, FXXO, LVL, FXS, PLIST, SNAPS, SNAPNAME and the EQ/global queries.
`LVLSUB` remains disabled in the read-only profile; the frontend falls back
to `LVL` polling. Uploading, editing and saving require subsequent validation
of storage and the engine on the MINI.

## USB and BLE evidence in the original firmware

The USB template at `0x02035085` contains VID `3654`, PID `4155`. Code at
`0x0201B9E2` copies 18 bytes, then the instructions at
`0x0201B9F0` (`51 31 89 4B`) write `0x51` to byte 11:
the **returned PID is `5155`**. The static template alone would have led to
an incorrect conclusion. The original UTF-16 product string is
`Tank-G UltraRig` at `0x0203A264`; rebranding/targeting the new image must
verify it separately.

The configuration template at `0x020350B9` describes CDC ACM: control
interface 0, class 02/subclass 02/protocol 01, 8-byte interrupt IN `82`;
data interface 1, class 0A, 64-byte bulk OUT `02` and IN `83`.
The firmware fills in the total length and interface count.
The original editor opens Web Serial at 115200 baud and filters VID `3654`.

The four NUS UUIDs are also verified in the firmware bytes:

- service `6e400001-b5a3-f393-e0a9-e50e24dcca9e`;
- RX `6e400002-b5a3-f393-e0a9-e50e24dcca9e`;
- TX `6e400003-b5a3-f393-e0a9-e50e24dcca9e`;
- pairing `6e400004-b5a3-f393-e0a9-e50e24dcca9e`.

The initial BLE fragment is 20 bytes; the frontend increases it to 244 after
the firmware's MTU response. The Android bridge uses the existing Capacitor
plugin, while the desktop page uses Web Bluetooth. The stock MINI AE40 app
and USB-MIDI `4C4A:C755` do not replace these transports. Sharing the same SoC
makes these bytes relevant to the audit, but does not prove that the USB/BLE
stacks, clocks, IRQs, buffers or radio work after the port. This document
claims no CDC/NUS enumeration of a MINI build.

## Progressive profiles without circular prerequisites

The base build is `identity=true, read=false, write=false, panel=false`.
Once a standalone image is available for verification, the builder accepts
`--firmware-manifest <file.json>` with this contract:

```json
{
  "target": "tank-mini",
  "architecture": "standalone-ultrarig-port",
  "firmware_version": "tankm_fw M5.71 rel ble",
  "image_path": "build/image-to-verify.bin",
  "image_sha256": "ACTUAL_ARTIFACT_SHA256",
  "capabilities": {"read": true, "write": false, "panel": false},
  "hardware_verified": false
}
```

The builder checks the file and its hash; the PONG string must match
`firmware_version` exactly. **Reads do not require prior hardware evidence**:
their purpose is to validate the new build. PONG does not carry SHA-256:
this is a constraint on the distributed configuration and test procedure,
not a cryptographic attestation from the pedal.

The old full `write=true` profile requires `hardware_verified=true` and
`write_validation` with the `path`/`sha256` of a local report containing
`target=tank-mini`, the same `image_sha256` and
`all_required_editor_mutations_verified=true`. No report of that kind has
been produced here. The limited profile described below is now available
to qualify the first preset: it does not require NAM/IR uploads or every
other feature to be qualified first. `panel=true` is always rejected until
the real MINI mapping is implemented. This state does not hide UltraRig
features: it distinguishes what the interface retains from what can already
run on the device.

## Writes qualified for exact requests

The manifest may retain `write=false` and add `command_capabilities`.
Each key is an original command and each value is a list of complete requests:
qualifying `FXP 1 0 50` does not authorize another value, index or ID;
`PSAVE 31 Scratch` does not authorize another slot or name. There are no
wildcards, prefixes, ranges or implicit permissions. The distributed profile
remains `command_capabilities={}`, with no hardware evidence or enabled writes.

| Supported command | Scope | Evidence required for the specific request |
|---|---|---|
| `FXP id index value` | Live parameter of an existing block | ACK with the effective value, FXS and restoration |
| `FXE id 0/1` | Block bypass/enable | ACK, FXS and restoration; optional for the first trial |
| `PLOAD slot` | Loading, which changes the current sound | ACK, state readback and return to the previous state |
| `PSAVE slot name` | Preset saving and slot selection | ACK, PLIST, PLOAD and state readback |
| `PDEL slot` | Deleting the temporary slot | ACK and consistent PLIST without that slot |
| `SNAP 0..3` | Scene selection | ACK, SNAPS/FXS and restoration of the previous scene |
| `SNAPSAVE 0..3` | Saving the scene in the current preset | ACK with the expected preset, reload and state readback |

Block IDs and the current preset are not immutable properties. The request
list limits the transmitted protocol; it does not prevent panel scene changes
or automatically attest to the same parameter in another effect type.
The trial must also record and verify that context. Operations are not enabled
solely by the command name or USB/PONG identity.

For example, **after real trials**, a manifest may request:

```json
{
  "command_capabilities": {
    "FXP": ["FXP 1 0 50", "FXP 1 0 51"],
    "PLOAD": ["PLOAD 0", "PLOAD 31"],
    "PSAVE": ["PSAVE 31 Scratch"],
    "PDEL": ["PDEL 31"],
    "SNAP": ["SNAP 0"],
    "SNAPSAVE": ["SNAPSAVE 0"]
  },
  "command_validation": {"path": "research/specific-physical-trial.json", "sha256": "ACTUAL_REPORT_HASH"}
}
```

This is an illustrative fragment, not a valid report or enabled build.
The lists must match the report's `verified_requests` **exactly**.
The builder checks `hardware_verified=true`, `read=true`, `write=false` and:

- `schema=1`, `kind=mini-app-command-validation`, `target=tank-mini`, and
  version/image hash identical to the manifest;
- `editor_source_sha256` equal to the pinned original frontend,
  `hardware_executed=true`, `transport=usb-cdc`;
- `trace` and `backup` references, each with the `path` and `sha256` of a
  retained, nonempty local file; the report's own hash is checked separately;
- `restoration_verified=true` and an observation for every exact request,
  with `request`, `ack_verified=true`, `readback_verified=true`;
- for PSAVE/PDEL/SNAPSAVE, also `persistence_readback_verified=true`, attested
  after reload or verification of deletion, not solely by the ACK.

These fields are assertions from a reviewed trial. The builder checks constraints
and file integrity; it does not turn a simulated log into a hardware measurement.
Tests use explicitly synthetic temporary fixtures; none is published as real
evidence. This schema cannot yet be used for BLE: transport evidence must be
added separately. The gate checks the transport both when accepting PONG and
before each command; BLE, unknown transports and transport changes do not
inherit USB permissions. Documented queries remain available after identity
verification.

The gate applies within the original queue before writing. Panel, capture/NAM
upload, IR, global settings and unlisted commands remain denied. The app shows
the limited operations enabled by the profile. The `savePreset` preflight
also requires `SNAPSAVE 0` to create scene A automatically and, if needed,
SNAPSAVE for the current scene. The toolbar Save similarly checks every planned
command before starting. The "All scenes" workflow and full export, which may
use TUNER, traverse scenes and reload presets, remain excluded from the limited
profile. The original code and demo remain available. Preflight prevents a
predictable local rejection after PSAVE; it does not make device changes atomic.

### First minimal app, persistence and restoration cycle

Before the trial, retain a reviewed backup of the port's firmware/data and
the starting preset/scene state. A PLIST/FXS read alone is not a backup of all
scenes and resources. Choose a saved preset without pending live changes and
with a simple parameter already identified; a complete PLIST must show the
temporary slot as free.

1. Record identity, FXT, FXS, SNAPS, PLIST, PSTAT and capture/IR references.
   Try PLOAD of the starting preset and SNAP of the scene to restore,
   checking that the state remains as expected.
2. Execute FXP with the trial value and read FXS again; also try the original
   value, then reapply the trial value. Every request must have a consistent
   ACK and state, without unexpected changes to other blocks.
3. Use the app's real save operation on the temporary slot, including its
   required SNAPSAVE commands. Read PLIST/SNAPS again, change the parameter
   only in RAM and reload with PLOAD/SNAP: the saved value must return.
   This exercises reloading; it does not yet prove persistence after a power cycle.
4. Return to the initial preset/scene and verify the entire captured state;
   delete only the temporary slot using PDEL and verify PLIST. An error or
   timeout is not proof of restoration and does not authorize blind retries.

This cycle needs only FXP, PLOAD, PSAVE, SNAP, SNAPSAVE and PDEL with the
arguments actually tested. FXA/FXR, import, IRBEGIN, LDBEGIN, CSAVE, GSAVE
and update commands are unnecessary. Restoration is logical: it does not
undo NOR memory wear or sequence numbers. The report may enable only these
requests without setting `all_required_editor_mutations_verified`.

## Offline checks

```powershell
python -X utf8 -m unittest tests.test_mini_app_protocol -v
```

The 19 tests check rejection of stock/G/B, version binding, boundaries between
identity/read/write/panel, identity reset, prevention of chained commands,
gate placement before I/O, complete-script syntax, derivation when the source
changes, descriptor hashes and unchanged license copies. One test also runs
the original `Pedal` queue with a fake transport: only `PING` and `FXT`
reach the wire; save and panel commands never reach `write()`.
Limited-profile tests check parameter/slot/name variations, missing or altered
evidence, trace/backup hashes, persistent readback and restoration.
The original `savePreset` function is also run with a fake pedal:
without SNAPSAVE it sends no PSAVE; with exact grants it sends
`PSAVE 31 Scratch`, `SNAPS` and `SNAPSAVE 0`. The CDC CLI has another
14 tests in [`MINI_APP_PROTOCOL_PROBE.md`](MINI_APP_PROTOCOL_PROBE.md).
The complete page was also rendered in headless Edge from a local file with
`#demo` and networking blocked: the DOM shows `TANK MINI demo` and the offline
notice. The screenshot is `build/mini-app-browser-check/demo.png`.
This verifies the adapted original interface, not firmware or APK execution.
