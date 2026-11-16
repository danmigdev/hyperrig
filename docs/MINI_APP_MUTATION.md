# MINI app editing and save tests

[probe_mini_app_mutation.py](../tools/probe_mini_app_mutation.py) is separate
from the historical read-only client. Its default command prints the offline
plan: it does not enumerate devices, import pyserial, or open ports. The current
tests use only a simulated pedal. They do not establish a booted application
port, a real desktop connection, or an Android test.

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py
python -B -X utf8 -m unittest tests.test_mini_app_mutation tests.test_mini_app_transport tests.test_mini_app_protocol
```

All 55 tests passed: 22 new tests and 33 regressions. The simulator keeps
presets and live state separate, changes runtime IDs on load, and can simulate
timeouts, inconsistent responses, external changes, and failed persistence.
One test also runs the original JavaScript parsers in Node.

## Sources and responses

The client checks the hashes of the original frontend and G firmware already
pinned by `build_mini_app.py`. The original call sites use 1.5 seconds for
FXP/FXE/SNAP/SNAPSAVE/PDEL and 8 seconds for PSAVE/PLOAD. The response strings
are checked in the G bytes, including these offsets relative to `app.bin`:

| Operation | Normal response | Offset |
|---|---|---:|
| FXP | `FXP ok <effective value>` | `0x35CD1` |
| FXE | `FXE ok`, with CPU statistics | `0x35A51`, `0x39ED1` |
| PSAVE | slot, name, blocks, capture/IR references | `0x3704D` |
| PLOAD | slot, name, `missing`, references, time | `0x37584` |
| SNAP | index, `missing`, time | `0x36B4A` |
| SNAPSAVE | index and modified preset | `0x36824` |
| PDEL | deleted index | `0x35DE8` |

FXP returns the effective value, which may differ from the requested value.
FXE does not return the on/off state: FXS is required. The client accepts only
the reconstructed normal responses; `missing`, capture errors, or unrecognized
suffixes do not become a successful test. An `ERR … kept …` error, a malformed
response, or a timeout stops the session without a retry.

## Live cycle

`live` requires the local image verified by the manifest, the exact MINI
version, `hardware_verified=true`, and the `read=true` capability. This qualifies
the booted candidate; it does not assert that every mutation has already been
tested. PONG does not read the image hash from the device.

The client obtains FXT, FXS, PLIST, and SNAPS, saves a backup of the observed
state, and repeats the reads before making a change. FXP uses an existing
parameter and its FXT range; the first experiment changes a single step of
`nivel_db`, `ganancia_db`, or `mezcla_pct`, excluding the resource-sensitive cases
identified in the frontend. FXE is an explicit alternative for the on/off state
of a block that is actually present. These restrictions define the scope of the
representative test; they do not describe every parameter the app supports.

After an ACK and a new FXS, the client restores the initial value and requires
a consistent ACK, FXS, preset, and scene. If a valid FXP ACK reports a different
value but readback is consistent and no other state changed, the original is
restored; the test does not qualify the initial request. An ambiguous error
does not trigger a blind restoration attempt. The report preserves the phase,
the restoration request, and the status of its verification.

Operational example, to use only after the candidate actually boots and after
replacing the port, manifest, ID, and index with the observed values:

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py live --port COM8 --firmware-manifest build/mini-app-manifest.json --block 7 --parameter 0 --log build/live-001.jsonl --backup build/live-001-before.json --report build/live-001-proof.json
```

For FXE, use `--operation FXE --block <id>` without `--parameter`. The three
output files must be new and distinct. The example has not been run on hardware.
The live backup covers the observed state, not the whole bank or the internal
history of delay/reverb effects.

## Separate persistence cycle

`save` also requires an exported bank in the original `ultrarig-preset` format
or the renamed `hyperrig-preset` variant, version 1, with a hash and inventory
consistent with PLIST. It does not perform the export: the original export can
load presets and scenes. Before PSAVE, it checks that the backup preset/scene
represents the initial state, avoiding the loss of unrepresented live changes
when the original is reloaded.

The first test supports a serial chain without IR blocks or an external cab IR.
It also reads GAIN, AMPEQ, BPM, PCOLOR, STW, MODEL, and SNAPNAME. It sends no
NAM/IR or firmware commands. A preset with scenes must have a valid current
scene: the protocol here offers no command to restore selection `-1` when saved
scenes exist.

The concrete sequence is:

1. Obtain a new snapshot and an unchanged PLIST; the selected slot must be free.
2. Send `PSAVE <slot> HyperRig_Test`; check the ACK, PLIST, and live state.
3. Change a live parameter as a marker; `PLOAD <slot>` and selection of the
   initial scene demonstrate that the saved values replace the marker.
4. Send `SNAPSAVE 0` only to the temporary slot; verify the index and preset in
   the response, the new scene, and the absence of other changes.
5. A second live marker, followed by PLOAD and SNAP 0, separately verifies
   scene persistence. SNAPSAVE cannot hide a failed PSAVE: PSAVE has already
   been read back before this phase.
6. PLOAD the original preset and restore its initial scene; compare the
   observed values and settings, allowing new runtime IDs.
7. A new check identifies the temporary slot created by this test; only then
   does PDEL delete that slot. The final PLIST and state must match the initial ones.

Example, using a real backup hash in place of the placeholder:

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py save --port COM8 --firmware-manifest build/mini-app-manifest.json --slot 31 --bank-backup artifacts/my-bank.hyperrig.json --bank-sha256 <SHA256> --block 7 --parameter 0 --log build/save-001.jsonl --backup build/save-001-before.json --report build/save-001-proof.json
```

The client cannot delete pre-existing slots. If the temporary slot's name or
inventory changes, or a response is ambiguous, it does not delete the slot and
preserves the incomplete result. Returning to the logical state does not undo
NOR wear. Loading after saving demonstrates readback through that firmware
path; it is not a retention test after power-off or a complete comparison of
all pre-existing NOR contents.

## Evidence and operational app

The report retains the `mini-app-command-validation` format, bound to the image,
version, protocol sources, trace, and backup. The legacy `verified_requests`
field contains the exact requests tested; for saving, it includes PSAVE and
SNAPSAVE 0 without granting the cleanup commands.

The new `representative-families-v1` model separates `supported_by_protocol`
from `physically_exercised_requests`. In tests, the latter is empty and
`hardware_executed=false`; simulated requests are kept in a separate field.
The operational families are FXP, FXE, PLOAD, PSAVE, SNAP, and SNAPSAVE.
Representative tests do not assert that every value was physically tested.
`all_required_editor_mutations_verified` remains false.

The historical exact-request gate is insufficient for a usable app: it blocks
other values or names, and the original save flow also requires SNAPSAVE. The
new gate revision must use qualified families, with syntax and ranges from
current FXT/FXS/PLIST/SNAPS data, while retaining the original confirmations for
overwriting presets. This probe does not regenerate the candidate and audio v2
APK that have already been built.

The real desktop test still requires the port to boot, CDC `3654:5155`, a
matching MINI PONG, and physical roundtrips. Android uses the original
BluetoothLe/NUS transport, with separate pairing/authentication and
fragmentation: a USB test does not enable BLE. The original footswitch pairing
control also requires the appropriate hardware mapping; HYK1 verified the three
inputs together, not that Android operating combination.
