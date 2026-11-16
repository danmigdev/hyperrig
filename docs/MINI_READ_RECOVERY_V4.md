# Reconciling unexecuted NOR commands

`tools/recover_mini_read_v4.py` exposes `AuditedCommandRecoveryTransport`,
with the same construction interface and `bind_session` as the v3 wrapper.
It adds only FC7B/erase and FC7D/program when they fail with Win32 31 after
submission and a fresh read proves that the sequence was not consumed. The
writer, installer, and v1..v3 wrappers remain unchanged. Importing the module
opens no devices.

The writer consumes `state.sequence` in the dispatcher before `run_job`, thus
before NOR checks and WREN. An error before WREN may leave counters unchanged,
but the sequence is already different. Comparing WREN/erase/program is
therefore insufficient: all 128 bytes of the preceding audit must be identical.

Before reopening, the following are required:

- An active installer, fully verified preimage, pending sector, and a mutating
  operation marked uncertain.
- An immediately preceding FD88 identical to the record already validated by
  the core.
- STAGED state, verified echo, intact guards, and the candidate page CRC.
- The same token/address and a requested sequence equal to the preceding one+1.
- Host expected state unchanged from the audit except for that single increment.

The first PP after erase keeps the CRC of the last erased-NOR read in
`last_crc32`: it is not confused with the frozen page's CRC, which remains
separately checked against the candidate.

Reopening uses the same backend/slot/path, FC78, and FD88. The fresh record
must be byte-for-byte identical to the previous one, including CRC, stack,
counters, and flags. Any delta terminates the procedure, even if it appears
to indicate a successfully completed operation. No ACK is inferred from the
audit or synthesized.

Only with identical state is the same CDB reissued once. The result must be
a real ACK with the correct opcode, phase, token, new sequence, and CRC.
The original core then updates its counters and requires the normal completion
audit, including WIP polls. The wrapper does not clear
`mutation_completion_unknown`: only the core does so after that verification.
A reissue error does not start another recovery.

The total budget remains 8, shared with v3 paths. OUT/STAGE, ARM, FINISH, jump,
and reset are not reissued. Counter `mutation_request_reissues` describes
requests determined not to have executed; `completed_NOR_mutations_repeated=0`
describes completed mutations this wrapper does not repeat.
`mutation_retries_allowed=true` is now declared together with the exact
condition, without reusing v3's earlier absolute claim.

## Offline tests

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v4 tests.test_mini_read_recovery_v3 tests.test_mini_read_recovery_v2 tests.test_mini_read_recovery tests.test_mini_app_install tests.test_mini_quiet_install_runner
```

134 tests PASS, including 47 on v4, with earlier cases reapplied. They verify
unexecuted erase and PP, header last, real ACKs, mandatory subsequent audits,
rejection of an already executed operation, sequence consumption without WREN,
changes to every word, corrupted CRCs, a different candidate, shared budget,
and logger/reopen errors without replay.

Eight additional ASan/UBSan cases directly include the frozen operational C.
Simulated WREN callbacks read the internal sequence and require that it was
incremented before the call. Tests also cover preimage failure before WREN,
WREN failure, simulated partial programming, and reissuing an already executed
CDB: the latter is rejected without a second WREN.

```powershell
New-Item -ItemType Directory -Path build/mini-read-recovery-v4 -Force | Out-Null
wsl.exe --distribution Ubuntu --exec gcc -std=c99 -Wall -Wextra -Werror -O1 -g '-fsanitize=address,undefined' -fno-sanitize-recover=all -DHYPERRIG_WRITER_HOST_MUTATIONS -Ifirmware/mini/app_writer -Ibuild/mini-app-writer-operational tests/test_mini_read_recovery_v4.c -o build/mini-read-recovery-v4/host-sequence
wsl.exe --distribution Ubuntu --exec build/mini-read-recovery-v4/host-sequence
```

`research/mini-read-recovery-v4.json` preserves hashes and checks. This revision
performed no hardware test. Reconciliation establishes the state observed
after failure; it assumes the same identified writer and synchronous requests
without concurrent host operations. It does not prove the cause of Win32 31
or the absence of driver interference, guarantee USB availability or flash
completion, or qualify boot/audio. An executed or uncertain mutation still
requires separate inspection.
