# First-preset bootstrap revision 2

The first physical UI trial stopped before any capture, gain or preset change.
Its native wire contains only `PING` and `BLE`. The original editor then asked
for `BLE key`; the unchanged MINI profile denied that request locally with
`ERR MINI_APP firmware mutations are not validated for this MINI build`.
The first trial guard did not recognize that exact spelling as an optional
local rejection and stopped. Native serial close was observed.

The historical report remains unchanged at
`build/mini-first-preset-ui-01/report.json`, SHA-256
`292bfed0f1aeea5cfae969ccfe0aaf98535d0403ba52ecb992e56820e88bbd4a`.
It is a failed trial, not evidence of capture persistence, preset saving or
reload.

`tools/mini_browser_first_preset_guard_v2.js` recognizes only the exact local
`BLE key` denial above, requires no matching wire command, and records a
`local_editor_policy_rejection` event. A direct serial write of `BLE key`
remains forbidden. The original profile, BLE capability and UI mutation
sequence are unchanged.

`tools/run_mini_v3_first_preset_a2_v2.py` temporarily selects that guard and
delegates to the frozen A2 driver. It restores the in-memory bindings even on
failure. Each new trial report records the new source hashes and
`bootstrap_guard_extension`; its `observed_local_rejections` list is copied
from the actual guard events. The static extension fields come from the
driver's `description()` function. No historical report or frozen source is
rewritten. This revision grants no command family or audio capability.

Offline validation:

```powershell
python -m unittest tests.test_mini_first_preset_bootstrap_v2 -v
```

Eight Python tests pass, including the real closed-session preflight. The Node
bootstrap fixture executes the original policy, `Pedal.cmd`, `Pedal.feed`,
`bleKeyFetch` and USB BLE branch against fake native serial (22 checks). The
existing full UI sequence fixture also passes with the new guard (69 checks),
including the frozen native-RX verifier. Wrong local replies, other forbidden
commands and direct `BLE key` writes fail. These are offline checks; they do
not certify another physical trial. Exact hashes are recorded in
`research/mini-first-preset-bootstrap-v2.json`.
