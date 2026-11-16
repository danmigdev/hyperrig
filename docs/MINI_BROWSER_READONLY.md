# Connecting the MINI editor with an isolated browser

The new [probe_mini_browser_readonly.py](../tools/probe_mini_browser_readonly.py)
helper prepares a trial of the real generated editor without modifying the
candidate or using a personal profile. It uses the already installed
Chrome/Edge and `websocket-client`, a new profile under `build/`, and a
temporary localhost server. The browser and server close afterward.
The report is written once, after closure, rather than replacing a JSON file
during device operations.

Default mode opens only the offline UI. Web Serial is also denied by HTTP policy;
enumeration returns an empty list and requesting a port is blocked.
USB, Bluetooth and MIDI are blocked in both modes.
No chooser is opened in offline mode.

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --output build/mini-browser-offline-new
```

Live mode uses `--execute-readonly` and an explicit evidence file produced
after root has verified boot and PONG. The JSON file must contain:

| Field | Required value |
| --- | --- |
| `schema`, `target`, `transport` | `1`, `"tank-mini"`, `"usb-cdc"` |
| `vid`, `pid` | `13908`, `20821`, meaning `3654:5155` |
| `com` | The Windows port actually observed, for example `"COM12"` |
| `pong` | The complete received PONG line, without its terminator |
| `image_sha256` | `3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff` |
| `serial_port_closed` | `true`, after closing the client that read PONG |
| `observed_utc` | UTC timestamp of the physical verification |

The line must identify exactly `tankm_fw M5.71 rel ble`, followed by the
original date. The file must be local and its SHA256 must match
`--evidence-sha256`. This format gathers evidence already checked by the runner;
it is not cryptographic authentication of firmware on the pedal.

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --output build/mini-browser-live-new --execute-readonly --evidence analysis/hardware/mini-browser-evidence.json --evidence-sha256 VERIFIED_FILE_HASH
```

The live path is prepared for root's go-ahead after PONG/COM, without serial
access overlapping ROM tests or installation. Only tests with simulated ports
were executed in this task; no browser connection to the MINI is yet qualified.

Before live execution, root must have completed installation and application
boot, observed `3654:5155` and the COM port, received the complete PONG line,
and closed the serial client that read it. The pedal must remain in the same
app session: no ROM, reset or concurrent serial opening.
The `serial_port_closed` field attests to that closure; the helper does not
query other ports to verify it. Even an offline browser opening at this stage
awaits root's explicit go-ahead.

The proposed command, after those checks and pinning the evidence file, is:

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --app-dir build/hyperrig-mini-audio-v2/app/web --output build/mini-browser-live-01 --execute-readonly --evidence analysis/hardware/mini-browser-evidence.json --evidence-sha256 ACTUAL_EVIDENCE_SHA256 --timeout 45
```

Replace `ACTUAL_EVIDENCE_SHA256` with the approved hash of the file actually
produced, not a synthetic example. The output directory must be new;
the helper refuses to reuse a previous profile. It retains `report.json`,
`initial.png`, `connected-presets.png` when obtainable, and Chromium stderr.
On failure, it does not reconnect or modify the candidate.

The helper enables the `DeviceAccess` domain from the CDP schema of the
browser actually launched, then presses the real `#connBtn` button.
It selects an entry only when the name contains one unambiguous COM token
matching the evidence. `COM2` does not match `COM12`; a name without a COM
or a duplicate does not authorize choosing the first entry. Initially empty
lists may update within the timeout. The CDP chooser does not expose VID/PID,
so a second check uses `SerialPort.getInfo()` before `open()` and requires
both exact values. The native `requestPort` filter already includes VID and PID.
If the Web Serial request does not produce the expected event in this Chrome
version, the trial stops without an alternative selection.

The separate instrumentation,
[mini_browser_readonly_guard.js](../tools/mini_browser_readonly_guard.js),
permits one request and one opening at 115200 baud. It neither reuses previously
authorized ports nor reconnects automatically. Before the exact PONG, it permits
only `PING`, up to five attempts as in the original app. Afterward,
`SerialTransport.write` accepts only one query line from the explicit list,
with a total budget of 1000. This check is separate from the app profile:
PSAVE, PLOAD, FXP, GSAVE, BLEKEY and panel commands are not sent.
No write data is added to the app files.

The live trial must complete the initial MODEL, MEM, FXT, FXS, PLIST and SNAPS
reads with valid responses, display the accepted MINI identity and preset bank,
record a screenshot, and disconnect through the app path that waits for pending
reads. It records port information, commands actually sent, responses and UI
state. Clicking in the chooser alone does not count as success.

The independent tests can run without a browser or hardware:

```powershell
python -B -X utf8 -m unittest tests.test_mini_browser_readonly -v
```

Five Python tests include 47 JavaScript checks with a simulated port:
unambiguous COM selection, hashes and identity, blocking before PONG, wrong PID,
a single opening, rejection of mutation commands and multiple lines, the PING
budget, and explicit stopping. Future write-family verification will require
a separate helper; this path remains read-only.

The preparatory freeze is recorded in
[mini-browser-readonly.json](../research/mini-browser-readonly.json), with hashes
of the helper, instrumentation, tests, CDP dependency and five app files.
The earlier real-Chrome UI trial is recorded separately in
`research/mini-browser.json`: all hardware APIs were disabled, so it does not
qualify the Web Serial chooser or this future connection.
