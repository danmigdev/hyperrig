# MINI desktop editor with real WebSerial

Only with `--execute`, `tools/launch_mini_desktop_readonly.py` opens a visible
Chromium window on the complete editor already present in
`build/hyperrig-mini-audio-v2/app/web`. It uses a new browser profile, a temporary
server on `127.0.0.1`, and the COM port observed during normal boot. It does not
use the personal profile, install dependencies, or change the frozen app or
manifest. With no options, it prints the plan without reading evidence or
opening a browser.

The launcher neither requires nor claims a footswitch-recovery test. The base
manifest retains `hardware_verified=false`: any real connection is recorded
separately, without promoting audio, presets, BLE, or boot recovery.

## Two identity modes

- **Previously verified PONG:** a normalboot v10 report with enumerated CDC and
  a complete, closed PING-only log on the same COM port. The original parser
  replays RX bytes and checks the recorded version, date, and interpretation.
  The browser's PONG must then be identical to the log's PONG.
- **First WebSerial handshake:** add `--first-handshake`. The normalboot report
  must still establish that CDC appeared; the previous log may contain a failed
  PING but must prove native serial open and close on the same COM port, with
  no other writes. That log does not qualify identity. The guard allows only
  `PING` until it actually receives `PONG tankm_fw M5.71 rel ble` with a
  structured date. The report starts with `identity_verified=false` and
  preserves PONG only when it arrives.

The v10 PING error remains in the reference to the original evidence. It can
be superseded only by an identity actually received later; the presence of
`COM3` alone does not enable other reads. Every other program using the serial
port must be closed before starting the launcher.

## Preflight and opening

First-handshake example; replace the two SHA values with those of the completed
files, and use the latest closed diagnostic log as evidence.

```powershell
python -B -X utf8 tools/launch_mini_desktop_readonly.py --check-only --first-handshake `
  --boot-run analysis/hardware/mini-first-boot-v10-released-run.json `
  --boot-sha256 SHA256_COMPLETED_BOOT_REPORT `
  --ping-log analysis/hardware/mini-first-app-v10-ping.jsonl `
  --ping-sha256 SHA256_CLOSED_PING_LOG
```

To actually open the window, replace `--check-only` with `--execute` and add
`--output build/mini-desktop-real-01`, choosing a new directory. The process
must remain running while the window is in use. It can be started through
Python/PowerShell in the background with a hidden console: the app window
remains visible. WebSerial does not require Windows elevation.

To use a previously successful PONG, omit `--first-handshake` and supply the
complete successful PING log. There is no automatic fallback between the modes.

The CDP chooser selects only the attested COM port, with an exact, unique
match. Before opening, the guard rechecks VID/PID `3654:5155`. Only one open
at `115200` is allowed; there is no reconnection. After identity verification,
the app must receive real `MODEL`, `MEM`, `FXT`, `FXS`, `PLIST`, and `SNAPS`
responses before reaching `connected_readonly`.

## Window and closure

The editor remains visible and normal reads continue. The desktop guard derives
from the frozen read-only allowlist; it blocks every mutation even if an
interface control attempts to send one. The session is limited to 50,000 queries
and 90 minutes; at the limit, the serial port closes while the window remains
available. Direct USB, Bluetooth, and MIDI are blocked. Serial connect events
are disabled to prevent automatic reconnection.

Closing the window also stops the local server. To obtain explicit native-close
evidence first, use the editor's normal Disconnect control or:

```powershell
python -B -X utf8 tools/launch_mini_desktop_readonly.py --close-session build/mini-desktop-real-01
```

This command writes only a local request. The active launcher performs the
original disconnection, observes the return from `port.close()`, then closes
the browser and server. If the window was closed before that result could be
observed, the report distinguishes `browser_process_stopped=true` from an
unobserved native close: it does not invent `serial_port_closed=true`.

`session.json` is published atomically and can be monitored using
`tools.mini_host_journal.read_shared_bytes`. Do not read the active report with
ordinary `Get-Content`, which could block a replacement on Windows.
`connected-proof.json` and `connected.png` are created once, after successful
reads. The report preserves entry evidence, source hashes, the actual PONG,
counters, and a bounded command/response history. Any manual selection of demo
mode is recorded as such and is not considered real communication.

## Local verification

```powershell
python -B -X utf8 -m unittest tests.test_mini_desktop_readonly -v
node tests/mini_desktop_readonly_guard_test.js tools/mini_desktop_readonly_guard.js
```

Tests use only fake serial ports, evidence, and browsers. They verify both
PONG modes, closure, a window configured without headless mode, read-only
limits, and server cleanup after a startup error. They are not physical
evidence of a WebSerial connection.
