# First-preset UI test: A2 activity

`tools/run_mini_v3_first_preset_a2.py` delegates to the frozen trial and the evidence reader in `run_mini_v3_editor.py`. It changes neither those files, the application, profile, guard, nor the sequence of six UI commands. Execution remains explicit; without arguments, it opens neither browser nor device.

Each original snapshot is followed by a single `STAT` in the original `Pedal.cmd` queue, terminated by the complete `NIVEL` line. The parser checks the original formats and `7+n` lines, with `n≤16`. Before capture preparation and before UI edits, it requires two strictly increasing uint32 `T.nproc` values, preserving the original identity, A2, state, `safe=0`, and mode 2 checks. DSP dimensions must match A2 (23 layers, 3 channels). A counter reset or overflow is not interpreted as progress.

The [firmware audit](../research/mini-a2-activity-audit.json) distinguishes A2 completion from the generic mailbox represented by `FXS posts/takes`. Those remain observations and may be zero; the real fixture contains `nproc=328986→329126`. `STAT` consumes diagnostic peaks and `T.max`, without clearing `nproc` or writing configuration/NOR. The result proves neither audio quality, analogue output, nor persistence after a power cycle.

The report preserves STAT responses and native RX through the original guard, plus `A2_gate_extension`, audit/fixture SHA256 values, and the new driver's hash. Native closure and RX comparison remain necessary to qualify the final result.

For the already closed desktop session, the new `validate_mini_webserial_v3_close.py` preserves the frozen validator's checks and classifies only the exact `WebSocketConnectionClosedException('Connection to remote host was lost.')` from the second CDP observation in the v3 launcher. It requires one successful native serial closure, a stopped guard without errors, a local close request with a hash and consistent chronology, terminated browser/server, and exact sources. The original error remains in the context and report as `desktop_close_observation`; losing CDP is not evidence of serial closure. No earlier evidence or SHA is rewritten.

Use three real, closed references: boot v11, the v3 desktop session's connected-proof, and its `session.json` after verified closure. First run:

```powershell
python tools/run_mini_v3_first_preset_a2.py --check-only --boot <boot.json> --boot-sha256 <SHA> --connected <connected-proof.json> --connected-sha256 <SHA> --session <session.json> --session-sha256 <SHA>
```

For the authorised test, replace `--check-only` with `--execute` and add `--output build/<new-directory>`. The UIA selector, `selection.json`, retained capture/preset, absence of retries, and final closure follow the [original trial](MINI_BROWSER_FIRST_PRESET.md). No physical test was performed during development of this adapter.

Offline verification: `python -m unittest tests.test_mini_v3_first_preset_a2`.
