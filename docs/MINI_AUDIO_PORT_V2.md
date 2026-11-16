# MINI audio shim v2

v2 preserves the PC5 preparation observed on the MINI and continues after
a NACK on an individual record, like the original caller. The v1 code,
payload and manifest remain unchanged. This revision does not change the
22 codec records, OSR, ALNK or the nominal 48000 configuration; it does not
attest to ACKs, physical audio or a complete HyperRig boot on the MINI.

Sources: [audio_port_v2](../firmware/mini/audio_port_v2/).
Offline build and audit:

```powershell
python -B -X utf8 firmware/mini/audio_port_v2/verify.py
```

Results and preimages are in
[mini-audio-port-v2.json](../research/mini-audio-port-v2.json) and
`build/mini-audio-port-v2/manifest.json`. The XIP payload contains 2332 bytes,
occupies `[0x02076AAC, 0x020773C8)` and adds no BSS. SHA256:
`cd0d973b76f31afdb20bf591dedbf50b82984ee75fb615e38ce9829957530791`.
It exposes the same symbols and two hooks as the v1 manifest; the recovery
guard must be relinked at the actual end of the new appended code. This
build does not modify the integrated candidate or artifacts already run
on the pedal.

PC5 preparation precedes the clock getter, PA9 and the codec bus. The MINI
fragment `[0x02005BCE, 0x02005C62)` is checked by hash and instructions:

| Operation on bit5 only | G binding used |
|---|---|
| DIE = 1 | `0x0200187C(37, 1)` |
| OUT = 1, then DIR = 0 | `0x02004998(37, 1)` |
| HD = 0 | New ASM function using the original G lock |
| HD0 = 0 | `0x0201B1B6(37)`, one argument only |

HD0 and HD are different registers. No equivalent HD helper was identified
in the G audit; `0x0201E09A` modifies DIEH and is not used. The HD ASM
function modifies only bit5 of `0x5009C`, between calls to the G critical
section `0x01C00E2E` / `0x01C00E46` and under the PORTC byte lock
`0x01C25CE2`, acquired with `testset`. It preserves r4 and RETS and uses
8 bytes of stack. The remaining helpers acquire that same lock themselves:
no outer lock is added that would make them wait indefinitely.
PU, PD, DIEH and the other pins' bits remain unchanged.

These functions require the G runtime and its lock initialization; they
are not services callable from the ROM plugin. They inherit the original
lock wait without introducing an unproven termination guarantee. PC5 has
not been identified as audio power: its electrical purpose remains unknown.
The full reference is
[MINI_CODEC_AVAILABILITY.md](MINI_CODEC_AVAILABILITY.md).

NACK handling derives from the MINI bytes: `0x02006DCE` stops the record
at the first unacknowledged byte; the loop at `0x02006DEC` still advances
by four bytes and attempts all 22 records. The caller at `0x02007188`
continues without checking the result. v2 calls
`hyperrig_mini_codec_stock_record()` and `hyperrig_mini_codec_write()`
separately and continues only if the result is NACK, STOP was attempted,
cleanup returned zero and the bus remains initialized. Clock, timing,
sampling or cleanup errors remain fatal and prevent the subsequent G start.

The result distinguishes attempted records, fully acknowledged records,
NACKs, continuations after NACK and individual acknowledged bytes. A zero
return means that the policy permits continuation; it certifies no ACK.
The target binding does not retain these counters globally or add
persistent state to the firmware.

One explicit difference remains: the original writer does not emit STOP
when a record receives NACK; our writer always attempts STOP. In both cases
the next record begins with START and address byte `0x36`, followed by the
same data. Tests verify this sequence, but the new STOP changes the boundary
of the failed transaction: electrical equivalence and the device state
after that transaction are unproven.

The P33 latch audit separates application startup from the ROM context.
The MINI SPL in the physical backup clears D0..DF and AD/AE/AF at
`[0x01C040CE, 0x01C04142)`, before changing the clock and calling the app
at `0x01C0528C`. The G app retains an equivalent release in the normal
`0x020011CE -> 0x02000EE0` path, through RAM writer `0x01C00F0C`.
The stock MINI app also contains all 19 clears. The register meanings are
corroborated by
[SPEC §3.1 of the pinned reference](../upstream/m-bootloader/docs/SPEC.md).

The verifier compares the integrated candidate's bytes present at audit
time with G for the function, caller and RAM copy of the writer: they are
unchanged. The SPL lies outside the replaced app area. The probes' ROM path
does not pass through those two startup paths, but the actual latch state
was not observed: this difference does not prove the cause of the HYC3
NACKs. v2 adds no P33 writes. The report separately retains the hash of the
candidate checked; the integrator must recheck these ranges when generating
the next candidate.

Completed checks: host ASan/UBSan across all 110 individual NACK points,
all 22 consecutive address-NACKs, complete success and 35 timing/cleanup
errors; 640 configurations/results for PC5 ordering and unrelated bits;
576 cases on the actually linked HD ASM with the lock free/busy and
different critical-section depths; 42 hook paths compared with the vendor
disassembler. The compiled wrapper verifies order, arguments and RETS
preservation. The simulated hardware APIs in these tests do not constitute
proof of GPIO, multicore locks, clock or audio on the device.
