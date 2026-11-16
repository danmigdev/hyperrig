# Finite budget of 32 writer recoveries

`tools/recover_mini_read_v6.py` exposes `BoundedCommandRecoveryTransport`, a
direct subclass of the v5 wrapper. It accepts integer `max_recoveries` from
1 to 32, defaulting to 32. It performs all original initialization with
`min(max_recoveries,8)`, then assigns the limit to the individual instance.
It changes no global variables, C writer, installer, or earlier wrapper.

This revision responds to actual exhaustion of the limit of 8 during the
eighth installation: the completed report
`analysis/hardware/mini-complete-install-run.json` records eight recoveries
(two reads, one query, five audits) and the subsequent Win32 31 that stops
the session, with `mutation_completion_unknown=false`. Its SHA256 is
`53ba43c881e1bd812dbe1c922214693573171a98213fd1653f73218a0b20c188`.
This motivates the increase; it is not hardware evidence for v6.

The limit of 32 covers one writer session, shared across preimage checking,
installation, final verification, and all families allowed by v5. It introduces
no new recoverable commands. `exchange`, all witnesses, recovery paths, and
`close` are inherited without overrides:

- The same command/state may use only one witness.
- Recovery still requires submitted Win32 31 and all v5 checks.
- A failed reopen, query, or reissue does not cause nested recovery.
- Executed or ambiguous commands are not repeated.
- Real ACKs and subsequent audits/readback remain mandatory.
- OUT/STAGE, ARM, jump, and reset gain no new retries.

The thirty-third recovery request terminates before another reopen. The
independent NOR reader retains its own limit of 8; a new v5 instance also
continues to have a maximum of 8.

The summary exposes version 6, `max_recoveries`, `recovery_limit_scope`,
`command_witness_policy_version=5`,
`command_witness_policy_unchanged_from_v5=true`, and
`separate_NOR_reader_budget_unchanged=8`.

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v6 tests.test_mini_final_install_runner
```

79 tests PASS: 66 on the wrapper, including the 59 v5 cases reapplied, and 13
on ninth-installer orchestration. One test traverses every phase with 32
distinct states: 12 recoveries during preimage checking, 10 during installation,
and 10 during the final read. Another stops at the thirty-third error before
new operations. Tests also verify parameter type/range, no effects on other
classes, rejection of witness reuse, terminal nested errors, and no repetition
of already executed PP/FINISH with a budget of 32.

`research/mini-read-recovery-v6.json` preserves hashes, results, and review.
V6 checks are offline with simulated NOR and handles. The larger limit does
not qualify the cause of Win32 31, guarantee that 32 recoveries will suffice,
or attest to flash completion, boot, or audio.
