# Real MINI editor connection: session 03

On **16 November 2026 at 00:08:26 UTC**, the HyperRig editor in a visible Chromium
window communicated with the MINI through WebSerial on `COM3`, VID/PID
`3654:5155`. This test is separate from mocks and earlier attempts; it does not
change the app's frozen manifest.

The actual received response is:

```text
PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe
```

The stable snapshot records one port request, one completed native open,
**25 completed read-only writes and 302 response lines**.
The app is connected, demo mode is off, and initial `MODEL`, `MEM`,
`FXT`, `FXS`, `PLIST`, and `SNAPS` reads have finished. The interface shows
37 effect types and the reported `A2` model, 23 layers/3 channels. The effect chain
is empty; `PLIST end current=-1` and `SNAPS 0000 current=-1` describe the
read state without demonstrating preset saving or editing.

Preserved evidence:

| File | SHA256 |
|---|---|
| `build/mini-desktop-real-03/connected-proof.json` | `96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2` |
| `analysis/hardware/mini-desktop-real-03-selection.json` | `30dca427dc997818aa3888af948ee8df63fd5c4f20111e37f3bbce1c64d4dbba` |
| `build/mini-desktop-real-03/connected.png` | `ee8346b83431ed150c21ed3d0fba9fe60ff07e11f4d69dd90676193b4d199890` |
| `research/mini-desktop-readonly-hardware.json` | `7ecc81b7d4ca41a91e5dfd926c873a5b6c19a3c04aba61455765e03b2b5773af` |

The associated candidate remains application image
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`,
verified by the preceding NOR readback. PONG confirms version/build, not the
device image's hash. The proof contains RX lines that actually passed through
the app's reader, not a USB capture or a dump of every transfer's native bytes.

## Device selection

Chrome's native WebSerial chooser did not emit the expected CDP DeviceAccess
event. Root used **Windows UIAutomation SelectionItem and Invoke** to select the
unique `Tank-M HyperRig (COM3)` row in the session's window only, browser PID
`154888`, origin `http://127.0.0.1:2047`.
The guard then rechecked VID/PID before opening. This selection changes neither
the read-only allowlist nor fabricates a serial response.

The relevant procedure for this browser is: a new isolated session, verify the
PID/origin, find the exact unique COM row in the native chooser, use SelectionItem
on the row and Invoke on Connect. Selection must finish while the launcher is
waiting; an already stopped session must not be reactivated by altering the
guard. The CDP limitation and Chromium sources for the observed revision are in
[MINI_WEBSERIAL_CHOOSER.md](MINI_WEBSERIAL_CHOOSER.md).

Session **01** only had the chooser open: zero opens and zero TX/RX.
Session **02** stopped at preflight because of an incorrect hash, before the
browser. Session **03** is the actual communication test; the three results must
neither be merged nor counted as three firmware tests.

## Limits and diagnostics obtained

The `safe` suffix is present in PONG. `CLKSTATE` reports nominal
`mhz=360` and `safe=1`; `LIFE` records `boots=2`, `exc=1`, `wdg=0`.
The preserved `CRASH` response reports `reti=0x02076AAE`, `rets=0x020053AA`,
and an ETM trace starting at `0x02076AAC`. These data support analysis of entry
into the audio shim; this test alone does not attribute the exception's cause.

Read-only communication is proven. The following remain separate and unqualified:
normal stable audio startup, analogue audio, actual UI editing, preset
saving/reloading, BLE, footswitch recovery, and a cold power cycle.

At the snapshot, the port is intentionally open (`closes=0`) and the window is
left available to the user. The report does not claim a closure that did not
happen. A future CLI diagnostic or editing trial requires disconnection and its
closure evidence first. `session.json` is still an active report and must be
read with the shared-delete helper; its hash is not used as immutable evidence.

Only local files were read while sealing this evidence. The frozen launcher,
guard, editor, and firmware were not changed.
