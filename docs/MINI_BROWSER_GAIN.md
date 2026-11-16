# MINI graphical GAIN trial

`tools/probe_mini_browser_gain.py` prepares a narrowly bounded trial of the
actual generated editor. With no options, it prints only the plan: it does not
read evidence, start a server or browser, or enumerate devices. Only offline
tests were run for this delivery; no physical GAIN-trial result exists.

When executed, the trial uses a new Chromium profile and the localhost server,
CDP, and chooser from the already frozen read-only modules. It selects only
the COM port from the supplied PONG evidence, requires VID:PID `3654:5155`
before the single open at 115200 baud, and does not allow reconnection. Direct
USB, Bluetooth, and MIDI are disabled. No editor file is modified.

## Prerequisites

- A **new** manifest for candidate `3b0eac3b…00a78ff`, with physical USB read
  qualification and the `GAIN` family, without general write, panel, or BLE
  family permission. The frozen `audio-v2` manifest remains unchanged.
- The physical first-preset report referenced by the manifest, with a completed
  GAIN roundtrip, an intentionally retained preset, and a trace ending in
  `port_closed`. The original family loader repeats the trace-byte replay;
  mock flags are insufficient.
- `browser-evidence.json` with exact COM/PONG and SHA256, referring to the same
  USB qualification. The preceding test must have closed the serial port, and
  no other program may have reopened it.
- An editor generated from that manifest: HTML and scripts are compared with
  the original derivation. The gain restored by the first-preset test must have
  an output greater than `-30 dB`.

The preceding binder requires held/released evidence. Any new normal-boot
binder must explicitly record that button recovery was not tested; this tool
does not fabricate a held test or change that binder. The already available
read-only USB editor is independent of this trial.

## Commands, to run only after actual qualification

The following paths are examples of new outputs; evidence files must already
exist and be real. Preflight does not start browsers or devices.

```powershell
python -B -X utf8 tools/probe_mini_browser_gain.py

$evidenceHash = (Get-FileHash -Algorithm SHA256 build/hyperrig-mini-usb-qualified-01/browser-evidence.json).Hash.ToLowerInvariant()
python -B -X utf8 tools/probe_mini_browser_gain.py --check-only `
  --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-families.json `
  --family-report build/mini-first-preset-01/report.json `
  --evidence build/hyperrig-mini-usb-qualified-01/browser-evidence.json `
  --evidence-sha256 $evidenceHash `
  --app-dir build/hyperrig-mini-usb-qualified-01/editor/web
```

For the physical test, replace `--check-only` with `--execute` and add a new
path, for example `--output build/mini-browser-gain-01`. Do not use this command
while another helper is communicating with the pedal.

## Sequence enforced by the guard

1. Exact PONG and the app's initial reads; fresh `GAIN`, `LVL`, `FXS`, `PLIST`,
   and `SNAPS` reads through the original queue.
2. Comparison with the final state of the first-preset test. `GAIN` and `LVL`
   must agree; chain, preset inventory, and scene must be unchanged. Check the
   value in `S.gain` and the ARIA attribute of the actual
   `#gOut .knob[role="slider"]` control.
3. Open the `#meters` popup, focus the Output control, and send CDP
   `keyDown`/`keyUp` `ArrowDown` events. The editor listener produces the only
   allowed `GAIN in out-1`. The guard requires a trusted event on the correct
   control and records its UI origin before allowing the write.
4. Exact real ACK and new complete reads. Only after these checks is `ArrowUp`
   armed; it sends `GAIN in out` through the same editor listener.
5. New reads must show the initial state. The app's normal disconnection must
   complete the port's native `close()`; checking only
   `SerialTransport.isOpen()` would be insufficient because the frontend
   catches some closure errors.

The write-function guard blocks every other mutation, duplicated or out-of-order
GAIN commands, additional framing, and attempts to repeat a failed command.
It does not execute `PSAVE`, `SNAPSAVE`, `PDEL`, or firmware commands. Automatic
editor attempts to use `LVLSUB`/`BLEKEY`, already denied locally by the MINI
profile, are recorded separately and are not treated as device responses.

`report.json`, written once after browser closure, contains input and source
hashes, screenshots before/during/after, UI events, ASCII writes and TX bytes,
RX bytes from the native reader, original queue lines and results, before/after
reads, and native closure evidence. An error interrupts the sequence: there
is no unverified automatic restoration. If the error follows the first change,
the report may therefore show an output still reduced by 1 dB.

Instrumentation establishes the editor→protocol→readback path; it is not
authentication against malicious page changes. Successful qualification does
not demonstrate analog audio, BLE, or persistence after power-off. Persistence
remains separately documented by the first-preset trial.

## Offline tests

```powershell
python -B -X utf8 -m unittest tests.test_mini_browser_gain -v
node tests/mini_browser_gain_guard_test.js tools/mini_browser_gain_guard.js
```

Ten Python tests and 120 JS guard conditions pass with fake ports and keys.
They cover evidence replay, exact app derivation, no-I/O defaults,
incomplete/inconsistent reads, UI origin, mutation order and duplicates,
incorrect ACKs, restoration without a fresh read, and failed closure. These
results are not published as hardware evidence.
