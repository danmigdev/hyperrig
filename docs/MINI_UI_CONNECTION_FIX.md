# Introductory nodes and unlocking the editor

The previous adaptation replaced `#firstUse ol` and removed `#fuB` and `#fuC`. The original code had already stored their text in `fuTxt`; on connection, `setLock()` tried to update them and threw an error before removing `inert` from the knobs. The actual DOM diagnosis and error are retained in `analysis/hardware/mini-v3-knob-DOM-01.json` and `mini-v3-setLock-diagnostic-01.json`.

`app/mini/mini-ui-v2.js` preserves the two original nodes and their text, replacing only the firmware-related step. It does not change `setLock`, `fuTxt`, `S.connected`, `inert`, or the guard. A Node test runs the original `setLock` and `phInert` functions: it reproduces the previous error, verifies that the nodes are preserved, and checks normal unlocking and locking during connection and disconnection.

`tools/run_mini_v3_first_preset_ui_v3.py` delegates to the frozen A2 driver and v2 guard. The copy in `build/hyperrig-mini-ui-v2/app/web` differs from the previous app only in `mini-ui.js`. Historical evidence continues to be validated against the original app; the new trial declares and serves the corrected copy, with separate hashes and `ui_compatibility_extension`. This correction alone does not qualify any functionality.

Build or verify the copy with `--build-ui-copy`. For the trial, use the same three boot/connected/session references as the previous driver and run `--check-only` first, followed by an authorized `--execute`, if applicable, with a new result directory. All focus checks and the command sequence remain unchanged.
