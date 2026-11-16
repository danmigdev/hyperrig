# Bounded recovery of writer queries

`tools/recover_mini_read_v2.py` adds a separate wrapper around the frozen
operational client. It does not change the RAM firmware, installer core, or
v1 recovery. Importing the module opens no devices. Execution requires an
explicit transport, reopen factory, durable journal, and session.

The third installation lost an `FC7E` response after a successful `FD7F` read.
At that point, `session.expected` already contains the new read counter and
the CRC of received bytes; the preceding audit still has the old counter.
Always comparing against the preceding audit would be incorrect.

| Command failing with Win32 31 | Evidence required after reopening | Result |
| --- | --- | --- |
| `FD7F` NOR read | HYW1 identity, all 128 audit bytes identical to the immediately preceding, already validated audit; all fields equal to `expected` | One read reissue; counters prove the first had no effect |
| `FC7E` status | HYW1 identity and a fresh audit matching every current `expected` field | One query reissue, with no NOR or counter effects |
| `FD88` audit | HYW1 identity and a fresh audit matching `expected` | The fresh record is returned directly to the installer's normal validator |
| `FD88` immediately after a validated erase/program response | As above, allowing only the `status_polls` increase within 1..65536 already required by the core | The installer receives and validates the record; the wrapper does not change expected counters |

CRC, build tag, slot, operational gate, state, token, sequence, counters,
bitmap, guards, and NOR state must be valid. An error during recovery terminates
the session. An executed `FD7F` whose response was lost changes the audit and
remains a terminal error: this tool does not hide a read already counted.

The overall budget is explicit, from 1 to 8 recoveries. Each CDB/expected-state
combination may use it only once. The same call never recursively enters
recovery; an identity, audit, or reissue error terminates the path. Reopening
must use the same transport class, path, slot, and profile. The runner must
also apply logging and pacing to the new instance.

Erase, program, arm, stage, echo, finish, upload, jump, and reset cannot be
repeated by this wrapper. Any other exception, Win32 error other than 31,
unsubmitted command, different identity, incompatible audit, or journal that
cannot be persisted terminates the session. The frozen installer remains
responsible for exact data comparisons and all subsequent checks.

`python -B -m unittest tests.test_mini_read_recovery_v2 -v` runs 20 tests with
the actual Python core and simulated NOR: response loss before/after queries,
audits after erase/PP, delta constraints, guard and identity errors, budget
exhaustion, errors during recovery, and no duplicated mutations. These are
not device tests. The separate `research/mini-read-recovery-v2.json` report
binds the sources and frozen dependencies.

The Windows cause and correlation with automatic requests are described in
[MINI_WINDOWS_FAILURES.md](MINI_WINDOWS_FAILURES.md). Recovery does not claim
to fix the driver or establish the reliability of a future installation.
