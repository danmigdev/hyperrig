# USB editor qualification after the first boot

The [qualify_mini_app.py](../tools/qualify_mini_app.py) binder uses only local
files. It opens no ports, browsers or devices. The default command displays the
workflow without reading evidence. It does not modify the manifest, firmware
or app frozen in `build/hyperrig-mini-audio-v2`.

This work has not yet produced a physical qualification. The binder tests use
temporary fixtures, deleted afterward. All real commands below are for the
coordinator, after a successful installation and with the pedal in the same
application session; access must not overlap ROM, flashing or other serial clients.

## Required evidence and initial read

The final complete-installation run, the run with three buttons held, and the
subsequent run with buttons released are required. Paths are parameters:
the result of an interrupted installation attempt is not reused.
The independent inspector rechecks the full NOR, application, external regions,
commands and reconciliations. Both boots must be bound to that run's hash.
The required contrast is a new ROM enumeration/INQUIRY with buttons held and
CDC `3654:5155` with buttons released. These are resets through SPL, not
evidence of startup from power off.

The frozen manifest already permits reads: `hardware_verified` need not be set
to send PING. The boot wrapper can execute PING immediately; the following read
rechecks identity and captures the state needed for presets. Take the port from
the completed released run, without guessing a COM number. Use new output paths:

```powershell
python -B -X utf8 tools/probe_mini_app.py read --port ACTUAL_COM_PORT --firmware-manifest build/hyperrig-mini-audio-v2/firmware-manifest.json --log analysis/hardware/mini-app-qualified-read-01.jsonl --queries MODEL MEM LVL FXT FXS PLIST PSTAT SNAPS SNAPNAME
```

The binder requires `session_complete` followed by port closure, exact version
`tankm_fw M5.71 rel ble`, the same COM and VID/PID observed at boot, literal
commands without mutations, and the nine listed queries. It reruns the
read-only parser on retained RX bytes and compares the journal results;
it also parses FXT, FXS, PLIST and SNAPS. PING alone does not qualify these
reads. The parsers do not interpret LVL as an audio measurement.

Replace the three `RUN_*` paths with completed reports from the attempt that
actually succeeded:

```powershell
python -B -X utf8 tools/qualify_mini_app.py read --install-run COMPLETE_INSTALL_RUN --held-run RUN_HELD --released-run RUN_RELEASED --read-log analysis/hardware/mini-app-qualified-read-01.jsonl --output-dir build/hyperrig-mini-usb-qualified-01
```

Only after all checks pass is the new directory created, containing:

- `installation-inspection.json`: independent installation verification;
- `read-qualification.json`: evidence, hashes, responses and qualification limits;
- `firmware-manifest.json`: `hardware_verified=true` explicitly scoped to USB
  boot/reads, `read=true`, `write=false`, `panel=false`, and no families;
- `browser-evidence.json`: PONG, COM, timestamp and serial closure actually
  observed, in the already frozen browser helper's format.

The image hash comes from its binding to the installation and dump. PONG does
not cryptographically attest to the binary; logs are not device authentication.
Verification does not prove that no reset or other client intervened after
collection. Audio, BLE, power-cycle behavior, persistence and panel commands
remain outside this initial qualification.

## First preset without overwriting an existing slot

Read `read-qualification.json` → `read.PLIST`, `read.FXS`, `read.FXT`
and `read.SNAPS`. The `preset_trial_path` field indicates the permitted branch,
but the probe rereads everything before acting and does not trust an earlier
snapshot.

With a consistent PLIST and `current=-1`, the first-preset probe selects the
first free slot if `--slot` is omitted. Before PSAVE, it saves a state backup
and checks that the state has not changed. There is no need to invent an empty
bank export. The `auto` marker decreases a real parameter within FXT bounds
or decreases a gain by 1 dB; if no permitted change is available, it stops
before PSAVE. The test separately verifies PSAVE → marker → PLOAD and
SNAPSAVE → marker → PLOAD/SNAP.

```powershell
python -B -X utf8 tools/probe_mini_app_first_preset.py create --port ACTUAL_COM_PORT --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-manifest.json --log analysis/hardware/mini-app-first-preset-01.jsonl --backup analysis/hardware/mini-app-first-preset-01-before.json --report analysis/hardware/mini-app-first-preset-01-proof.json
```

The new `HyperRig_Test` and scene A remain saved and selected. No PDEL is sent.
Other slots are compared through PLIST metadata, not every internal payload.
An active unsaved capture, unselected RAM scenes that cannot be restored,
a NACK/error, inconsistency or timeout stops the trial without retries or
blind restoration. An incomplete report identifies writes that may already
have occurred: do not restart automatically.

With `current>=0`, **do not use first-preset or falsify current=-1**.
A `probe_mini_app_mutation.py live` trial can verify a real parameter and
restore its value without persistent writes. The ID, index and value must
come from FXS/FXT; the probe rechecks state before sending.

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py live --port ACTUAL_COM_PORT --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-manifest.json --operation FXP --block OBSERVED_ID --parameter OBSERVED_INDEX --value ALLOWED_VALUE --log analysis/hardware/mini-app-live-01.jsonl --backup analysis/hardware/mini-app-live-01-before.json --report analysis/hardware/mini-app-live-01-proof.json
```

The persistent `mutation.py save` path instead requires a real bank export
in the original format matching the current preset, as well as a free slot
and a marker. A NOR dump does not replace that document. Full export in the
limited frontend is blocked because it changes scenes and other settings:
do not enable it implicitly to bypass the prerequisite. Without a real marker
or the required backup, the editor remains read-only for that branch;
no arbitrary preset is deleted or loaded.

## Actually tested families and a new build

After a complete physical report, the binder derives the list solely from
`physically_exercised_requests`; it ignores `supported_by_protocol` as a
source of permissions. The existing builder verifies all evidence and fully
replays the first-preset trace. Mocks, incomplete trials or BLE trials do not
enable USB families. With an empty chain, the expected result is GAIN, PLOAD,
PSAVE, SNAP and SNAPSAVE; FXP/FXE require their own real trials.

```powershell
python -B -X utf8 tools/qualify_mini_app.py families --manifest build/hyperrig-mini-usb-qualified-01/firmware-manifest.json --reports analysis/hardware/mini-app-first-preset-01-proof.json --output build/hyperrig-mini-usb-qualified-01/firmware-families.json
python -B -X utf8 tools/build_mini_app.py --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-families.json --output build/hyperrig-mini-usb-qualified-01/editor --report build/hyperrig-mini-usb-qualified-01/app-protocol.json
```

Multiple physical reports may be supplied to `--reports`. The result still
has `write=false`: it enables qualified families within their syntax,
FXT ranges and observed context, not arbitrary commands. No BLE capability,
NAM/IR upload, FXAdd, general deletion or full export is added.
Reload/readback does not prove persistence after a power cycle or audio quality.

For the read-only UI trial, the isolated helper can target the new
`editor/web` directory. Calculate the generated `browser-evidence.json` hash
and use it as `--evidence-sha256`; the port must still be closed and the pedal
session unchanged. The helper remains read-only even if the app has families:
it tests connection and display, not a write through the UI.

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --app-dir build/hyperrig-mini-usb-qualified-01/editor/web --output build/mini-browser-qualified-01 --execute-readonly --evidence build/hyperrig-mini-usb-qualified-01/browser-evidence.json --evidence-sha256 ACTUAL_HASH --timeout 45
```

Before preset trials, the same editor can be built from
`firmware-manifest.json` in another new directory for a read-only connection.
APK/Android and the BLE transport require separate trials and builds.

Binder tests, all offline:

```powershell
python -B -X utf8 -m unittest tests.test_mini_app_qualification -q
```
