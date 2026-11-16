# MINI v3 first-preset UI test

`tools/probe_mini_browser_first_preset.py` prepares and, only with
`--execute`, runs a test of the original editor in a new visible Chrome
window with a temporary profile. The frozen v3 firmware/app profile remains
read-only and is not modified. The temporary guard permits only the exact
experimental plan; the result does not automatically grant command families.

The code and tests are ready for a future run. **This test has not been
executed on the pedal.** The v2 connection observed in safe mode does not
meet the v3 prerequisites.

## Prerequisites

- Completed and verified v3 installation: app SHA256
  `9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c`.
- Normal v11 boot, an actual exact PONG and a closed read-only v3 WebSerial
  session, verified by `validate_mini_webserial_v3.py`. No held-footswitch
  test, device-measured hash or successful Python PING is invented.
- Fresh complete responses: PONG without `safe`, `CLKSTATE safe=0`,
  `LVL m=2`, the unchanged enabled A2 model, `PLIST current=-1`,
  `SNAPS 0000 current=-1`, output above −30 dB, a free preset slot and no
  active IR dependency.
- Two observations show progress in the core1 `posts` and `takes` counters,
  before capture preparation and before the UI actions. `ci/co` are clipping
  counters and may be zero. `run` is a duration; `eng` is recorded without
  treating it as a counter. These observations do not prove an analog signal
  or audio quality.

## Exact sequence

1. The native serial chooser must select the unique
   `Tank-M HyperRig (COMn)` row in the newly created browser. CDP DeviceAccess
   is not used for the WebSerial chooser. The coordinator writes
   `selection.json` before any modification, with the actual PID, origin
   and timestamp.
2. If the current capture is the embedded A2 without a persistent slot, a
   single `CSAVE k A2` stores it in the first free capture slot. This is an
   explicitly declared diagnostic command, not a UI event. If the current
   A2 already occupies a slot, the preamble does not rewrite it. `CREAD k`
   and 51 `CREAD k offset` requests verify all 4892 bytes against the original
   A2, its CRC and the inventory. No upload is performed. The original
   `loadModelName()` updates the UI from a fresh CLIST read; no hidden `S`
   field is assigned.
3. On the original Output knob: ArrowDown by 1 dB, verification read,
   ArrowUp to restore, and another read. Input remains unchanged.
4. Click Save on the first free preset row, not its empty name, which would
   invoke `PNEW`. The name is the one chosen by the original editor,
   normally `Preset 1A`. `savePreset` sends `PSAVE`, and its
   `sceneAOnSave` sends `SNAPSAVE 0`. The ACK, inventory and scene are verified.
5. A second ArrowDown on Output leaves a temporary marker. Enter on the
   newly saved row's name invokes the original `loadPreset` and a single
   `PLOAD`. The saved gain, capture reference, MODEL, chain, parameters and
   scene A must return. `SNAP 0` is not sent to correct a different outcome.
6. The original queue is drained, polling is stopped and the native port is
   closed. Success flags are set only after verification of actual RX bytes,
   UI/TX/ACK order and closure. The browser and local server terminate.

If a response, inventory or ACK does not match, the test stops. It does not
retry commands, reconnect the port, send a blind restoration or delete the
capture/preset. An error after a write may therefore leave an already
completed modification: the report retains intent and observations without
claiming success. The capture and new preset intentionally remain stored
when the test succeeds. Reload does not prove persistence after power-off
and may use the internal capture cache.

## Future command

Replace paths and SHA values with actual completed v3 evidence. Without
`--execute`, no browser or device is started. `--check-only` reads only
evidence files; only tests have been run during the current work.

```powershell
python -X utf8 tools/probe_mini_browser_first_preset.py --check-only `
  --boot analysis/hardware/mini-first-boot-v11-released-run.json --boot-sha256 <SHA-BOOT> `
  --connected build/<SESSION-V3>/connected-proof.json --connected-sha256 <SHA-CONNECTED> `
  --session build/<SESSION-V3>/session.json --session-sha256 <SHA-CLOSED>
```

For the authorized test, use the same arguments with `--execute` and
`--output build/mini-first-preset-ui-01`, a directory that does not yet
exist. The coordinator waits for `awaiting_exact_UIA_selection` in the
shared report and provides an atomic sidecar using the schema already
used for WebSerial recovery:

```json
{
  "observed_utc": "<actual UTC>",
  "browser_pid": 12345,
  "origin": "http://127.0.0.1:<port from report>",
  "selected_row": "Tank-M HyperRig (COM3)",
  "exact_unique_row_verified": true,
  "no_other_device_selected": true,
  "method": "Windows UIAutomation SelectionItem and Invoke"
}
```

`report.json` includes boot/installation/identity/closure references, source
hashes, snapshots, capture evidence, TX/RX bytes, trusted UI events, ACKs
actually received, screenshots and the closure observation. It uses a new
`mini-browser-first-preset-v3-trial` model: it must not be passed off as
the older `representative-first-preset-v1`, which verifies a different
sequence. If CDP disconnects after the open intent without being able to
read native events, `hardware_executed` remains `null` and
`execution_status_unknown` is true: this is not evidence that the device
was not opened.

## Offline verification

```powershell
python -X utf8 -m unittest tests.test_mini_browser_first_preset -v
```

Thirteen Python tests include the Node test with 69 conditions: the
`buildGains`, `savePreset`, `sceneAOnSave` and `loadPreset` functions are
extracted from the original v3 HTML and executed with fake UI/serial
dependencies. Regression tests reject invented ACKs, corrupted native
PSAVE/GAIN RX, duplicates, incorrect order, untrusted events and failed
closure. No test opens a browser, serial port or device; no fake result is
published as hardware qualification.
