# FINISH recovery with an unconsumed sequence

`tools/recover_mini_read_v5.py` exposes `FinishCommandRecoveryTransport`,
with a constructor and `bind_session` compatible with v4. It adds only
FC80/FINISH after a submitted Win32 31 failure. The eight-recovery budget
remains shared with inherited reads, queries, echo, and erase/program requests.
Importing the module opens no devices. The writer, installer, and v1–v4
are unchanged.

FINISH emits no WREN, erase, or page program. The writer dispatcher consumes
the sequence before `run_job`; the FC80 branch checks NOR status, rereads
4096 bytes, compares the sector CRC, and only then sets `phase=5`, `token=0`,
`erased=0`. Even a status error or partial read leaves the sequence consumed.
The WIP counter does not increase.

In frozen operational ELF A, the sequence write is at `0x01C2097C`, before
the `run_job` call at `0x01C20980`. The C origin is
`firmware/mini/app_writer/writer.c:268`; the FINISH branch is at line183.
Hashes of the C source, operational derivation, and ELF are in the associated
report.

The client increments only `expected.sequence` before FC80. The last PP has
already been verified: `mutation_completion_unknown` must be false.
FINISH is not reclassified as a NOR mutation.

Recovery requires:

- an active installer, verified preimage, and the current plan sector;
- an immediately preceding FD88 identical to the already validated audit;
- previous sequence 34 and requested sequence 35, `phase=3`, bitmapFFFF,
  staged0/echoed0, intact guards, and identified NOR;
- host state identical to the audit except for the sequence increment;
- the last page in plan order, echo and readback identical to the candidate,
  and consistent page CRC and old/new sector CRCs;
- the same CDB, token, and address as the pending FINISH.

Reopening uses the already selected backend, the same slot/path, FC78, and
FD88. All 128 fresh bytes must match the previous audit, including stack, CRC,
and counters. Any difference stops recovery, even if it shows a fully
successful FINISH. The wrapper changes no client sequence, flag, or counter.

Only then is the original CDB resent once. A real FC80 ACK is required with
error 0, phase 5, token 0, sequence 35, and the expected sector CRC. The original
client then performs its own audit: +4096 bytes read, unchanged
WREN/erase/program/poll counters, and consistent state. Sector reread and final
application verification follow. A wrong response, failure during recovery,
or discrepancy in the subsequent audit terminates the session; no second
recovery starts.

The summary distinguishes `finish_request_reissues` from
`mutation_request_reissues`. `completed_FINISH_requests_repeated=0` and
`synthetic_FINISH_ACK=false` describe the allowed behaviour.
OUT/STAGE, ARM, jump, and reset receive no new retry paths.

## Reproducible offline checks

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v5 tests.test_mini_complete_install_runner
```

72 tests PASS: 59 on the wrapper, including all 47 v4 cases reapplied,
and 13 on orchestration of the eighth installer. They cover unexecuted
FINISH on a normal sector and the header sector, an already completed request,
a consumed sequence with a partial read, every changed audit word, wrong CRC,
changed plan/state, real ACK, subsequent audit, shared budget, and
logging/reopen failures without replay.

The test also contains `NATIVE_FINISH_HARNESS`, which directly includes the
frozen operational C. Simulated status and read callbacks require sequence 35
to be already consumed. Seven ASan/UBSan cases check completion, rejected
replay, and failures of status, first read, intermediate read, CRC, and bitmap;
none emits new mutating NOR operations during FINISH.

```powershell
python -B -X utf8 -c "from pathlib import Path; from tests.test_mini_read_recovery_v5 import NATIVE_FINISH_HARNESS; p=Path('build/mini-read-recovery-v5'); p.mkdir(exist_ok=True); (p/'verify_finish.c').write_text(NATIVE_FINISH_HARNESS,encoding='utf-8')"
wsl.exe --distribution Ubuntu --exec gcc -std=c99 -Wall -Wextra -Werror -O1 -g '-fsanitize=address,undefined' -fno-sanitize-recover=all -DHYPERRIG_WRITER_HOST_MUTATIONS -Ifirmware/mini/app_writer -Ibuild/mini-app-writer-operational build/mini-read-recovery-v5/verify_finish.c -o build/mini-read-recovery-v5/host-finish
wsl.exe --distribution Ubuntu --exec ./build/mini-read-recovery-v5/host-finish
```

This requires the original operational build already generated, and GCC with
sanitizers in WSL Ubuntu. It neither recompiles nor changes the target payload.
`research/mini-read-recovery-v5.json` preserves hashes and results.

These tests are offline. The audit attests the observed state after failure,
assuming the same identified writer and serialised host requests; it proves
neither the cause of Win32 31 nor the absence of a pending driver queue.
No executed or ambiguous FINISH is reconstructed as an ACK.
These are not tests of completed flashing, boot, or audio.
