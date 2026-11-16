# Bounded FD87 echo recovery

`tools/recover_mini_read_v3.py` extends the v2 wrapper without modifying it.
Importing the module neither enumerates nor opens devices. The coordinator
must supply an already identified transport, durable logger, and explicit
reopening of the same backend; the class remains `ReadOnlyStateRecoveryTransport`.

The only newly recoverable operation is a 256-byte FD87 that fails with
Win32 31 after submission. It must immediately follow the validated staging
audit during an installation with a fully verified preimage. Token, staging
sequence, address, and CRC must match the immutable candidate page already
held by the installer.

The frozen C FD87 branch, `writer.c:257..265`, checks staging, phase, token,
sequence, address, RX guards, and the frozen copy's CRC. It then sends that copy
and may set `echoed=1`. It does not call `run_job`, access NOR, or consume a
sequence. The operational build derives the same branch by changing only the
gate macro; in ELF A, `0x01C207F6` calls `send_data`, followed by the `echoed`
store at `0x01C207FE`. Return is at `0x01C2081E`. No stack-watermark change is
allowed: `stack_used` is assigned inside `run_job`.

After reopening, FC78 must identify the same gate1 HYW1, and FD88 must return
a valid audit. All 128 bytes must be identical to the previous record except
for the `echoed` word at offset 104, which may be zero or one, and the record
CRC at offset 120. Guards, NOR state, counters, sequence, page CRC, and stack
usage remain unchanged. A negative send callback puts the writer in a failed
state: the new audit rejects it.

Only then is **the same FD87 CDB reissued once**. The response must be `bytes`,
256 bytes long, and identical to every byte of the candidate page; the CRC is
also rechecked. The wrapper neither updates the installer's expected state nor
generates responses: the original core compares the echo again and requires
its normal subsequent audit before continuing with erase/program.

`echoed=1` proves that the target branch accepted the result of its callback,
not that the host received the first response. That is precisely why the
second response must be checked in full.

The total budget remains at most 8, shared with v2 recovery of FC7E, FD88, and
FD7F. An identity, audit, or reissue error terminates recovery; the same CDB/state
cannot start a second recovery. OUT/STAGE, ARM, erase, program, FINISH, jump,
and reset are not repeated. An already executed FD7F retains v2's rejection
when the read counter has changed.

## Local checks

The suite uses the actual Python installer with simulated handles/NOR. It
includes echo loss before and after execution, before erase and mid-sector,
changes to each record word, short/corrupted responses, the core's subsequent
audit, logger failure, a mixed budget, and no repetition of mutating operations.
The report is `research/mini-read-recovery-v3.json`.

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v3 tests.test_mini_read_recovery_v2 tests.test_mini_read_recovery tests.test_mini_app_install tests.test_mini_quiet_install_runner
```

Result: 87 tests PASS, including 33 v3 tests. Separately, eight cases against
the frozen operational C under ASan/UBSan verify repeated echo, unchanged
state/audit except `echoed`, a negative send callback, incorrect sequence,
corrupted guard, and separation between RX and the frozen page. The mock counts
all NOR callbacks: none is called by echo. To reproduce this last check on
Windows using the WSL installation already used by the project:

```powershell
New-Item -ItemType Directory -Path build/mini-read-recovery-v3 -Force | Out-Null
wsl.exe --distribution Ubuntu --exec gcc -std=c99 -Wall -Wextra -Werror -O1 -g '-fsanitize=address,undefined' -fno-sanitize-recover=all -DHYPERRIG_WRITER_HOST_MUTATIONS -Ifirmware/mini/app_writer -Ibuild/mini-app-writer-operational build/mini-app-writer-operational/writer.c tests/test_mini_read_recovery_v3.c -o build/mini-read-recovery-v3/host-echo
wsl.exe --distribution Ubuntu --exec build/mini-read-recovery-v3/host-echo
```

These are offline checks. They do not prove the cause of Win32 31, guarantee
transport availability, or attest to installation completion, firmware boot,
or audio. No device command was executed during this revision; the writer,
v2, and installer remain frozen.
