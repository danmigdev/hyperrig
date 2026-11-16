# Completing reload of the saved preset

Trial `mini-first-preset-ui-04` actually executed GAIN down/restore, PSAVE, and SNAPSAVE 0. Its report remains a partial failure: opening the Presets panel had closed the volume popup, so the focus check stopped the next marker before sending it.

`tools/probe_mini_browser_saved_reload.py` accepts that report as verified by `validate_partial_saved_report`. A new session rereads the complete state and two STAT responses; it requires the same preset/scene/capture, saved gain, active A2 in mode 2 and safe=0, with increasing T.nproc. It does not repeat CSAVE, PSAVE, or SNAPSAVE.

The separate guard allows exactly two commands originating from the original controls:

1. Open the meters popup and send ArrowDown to the Output knob: saved volume minus 1 dB.
2. Open Presets and send Enter to the already saved row: PLOAD of the same slot.

The second step must restore the saved gain, model, capture, and scene 0. Waiting for the UI update only observes JavaScript state; it repeats no commands or key presses. ACKs and responses must be present in native RX bytes. Success is recorded only after native port closure; the previous report is not altered, and six commands are not simulated in the new session.

Offline check:

```powershell
python tools/probe_mini_browser_saved_reload.py --check-only --partial-report build/mini-first-preset-ui-04/report.json --partial-report-sha256 0eb9836638dd2025d9e75f380db4cc9c765c53dcc7ff4e0316ab810c3d2479ff
```

Explicit execution uses `--execute` instead of `--check-only` and requires a new `--output`. USB selection must be attested in `selection.json`, as in previous tests. The program does not authorise general command families, retry writes, or certify acoustic quality, the physical panel, BLE, or retention after power-off.

Tests execute original `buildGains` and `loadPreset` functions with simulated serial/DOM; they check order, focus, trusted events, ACK/RX, closure, and preflight against real files. No software test here opens a browser or the pedal.

## Real attempts on 16 November 2026

Sessions `mini-saved-reload-ui-01` and `02` did not call `requestPort`:
the introductory tour covered Connect after Skip was clicked too early.
An offline diagnosis with hardware APIs blocked checked the Skip/Connect
sequence using trusted events. Bringing the page to the foreground, taking
a screenshot, and checking the click target distinguishes this problem from
the USB protocol.

In session `03`, actual Skip and Connect actions opened the native chooser,
which remained on “Finding devices…” until timeout. No port was opened,
no command transmitted, and no preset changed. At 06:47–06:48 UTC, two direct
serial sessions outside the browser also failed: first no PING response,
then a write timeout. Both closed the port. Windows continued to list COM3
with VID `3654` and PID `5155`. These observations do not identify the
cause of the stall; a physical power cycle was requested and remains to
be verified.

The three failed reports and direct logs are preserved at the paths listed
in `analysis/hardware/CURRENT_STATE.json`. No qualified bundle was issued
on the basis of these attempts.
