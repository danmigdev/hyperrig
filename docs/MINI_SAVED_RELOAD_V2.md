# Saved-preset continuation: native connection

`tools/probe_mini_browser_saved_reload_v2.py` and its v2 guard are new
files. They leave partial trial 04 and previous attempts unchanged.
The only mutations remain one ArrowDown on the original Output knob and one
Enter on the preset 0 row, which sends PLOAD 0. There is no new save,
deletion, upload, profile change, or mutation retry.

Bootstrap retains the original loop of five 700 ms PING attempts within the same
open connection. Only an empty reply concluded by a real `Pedal.cmd` timeout
may be retried. The guard observes `Log.cmd`, the native five-byte write and
its fulfilled promise, all RX bytes, and the decoded replies. Any
partial or late byte, stream error, pending write, or different reply
prevents repetition. The Python parser rechecks this evidence in the report.
Expected closure through reader.cancel after guard.stop is distinguished from
an unexpected end of the reader while connected.

The `native-open-and-exact-pong` proof binds `SerialPort.getInfo()` 3654:5155,
one native open, and the exact normal PONG to the RX bytes. It does not identify
who selected the port, infer the COM name, or attest to the firmware hash
from the device. A UIA `selection.json`, if present, remains separate,
optional, verified evidence; its absence is not replaced with invented data.

The report sets `automatic_retry=true` exclusively for PING bootstrap,
with the actual number of attempts and empty timeouts. `mutation_retry_performed`
and `query_retry_performed` remain false. The qualifier joins this new
evidence to the earlier save trial; it does not rewrite the partial result.

```powershell
python tools/probe_mini_browser_saved_reload_v2.py --check-only --partial-report build/mini-first-preset-ui-04/report.json --partial-report-sha256 0eb9836638dd2025d9e75f380db4cc9c765c53dcc7ff4e0316ab810c3d2479ff
```

Execution requires `--execute --output <new-build-directory>` and remains
an operator action. Automated tests use simulated streams and browsers;
their success does not constitute a physical trial. Operating the introductory
tour remains separate from the protocol and requires no change to the old helper.
