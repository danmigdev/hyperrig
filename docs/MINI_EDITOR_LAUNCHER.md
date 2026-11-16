# Opening the HyperRig MINI editor

For the current English product, use `tools/launch_hyperrig_editor.cmd` and
follow [the current launcher guide](MINI_FX_EDITOR_LAUNCHER.md). The remainder
of this document records the earlier four-family editor and its physical test.

The verified bundle is available in `build/hyperrig-mini-qualified-editor`.
With the MINI powered on and connected through a USB data cable, double-click
`tools/launch_mini_editor.cmd`. UAC is not required. On Windows, it uses the
already installed Microsoft Edge with a separate profile.

If the introductory guide appears, press **Skip**, then **Connect**, and select
**Tank-M HyperRig (COM3)** in the USB chooser. Native opening on this PC has
taken as long as 15–20 seconds; the editor timeout is extended to 30 seconds.
Wait for the connection without opening a second window.

To adjust volume, open the meter and use the Output knob. In the Presets panel,
Save saves the preset; select its row to recall it. The physical test on
16 November confirmed volume adjustment and restoration of “Preset 1A”, the
A2 capture, and scene A.

A window of the original editor opens with a separate browser profile. The app profile enables only the qualified USB families `GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`: volume, preset loading/saving, and scene saving. The launcher adds neither a read-only guard nor a single-operation limit and does not send mutation commands. The banner reads “USB: volume and presets” (translated from the recorded interface text).

Each launch verifies only the bundle seal and app files. Full validation of the physical evidence occurs when the bundle is created; it is not repeated on launch. The launcher does not create a qualified bundle.

Close the window before opening a second session. The localhost server stops with the window; no service is installed. To request an orderly close from a terminal, use the current session directory recorded under `build/mini-editor-session-*`:

```powershell
python tools/launch_mini_editor.py --close-session build/mini-editor-session-<identifier>
```

The local request lets the original queue finish, closes the port, and then closes the browser/server. If window closure prevents the final observation, closure is reported as unobserved; no serial confirmation is invented.

Local check without a browser or device:

```powershell
python tools/launch_mini_editor.py --check-only --bundle build/hyperrig-mini-qualified-editor
```

Sessions preserve bundle references, the actual PONG, native open/close observations, and any errors. These data do not attest to audio quality or new functionality beyond the qualification already present in the bundle.
