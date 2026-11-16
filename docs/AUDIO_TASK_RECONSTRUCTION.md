# Audio task reconstruction

HyperRig now has a compilable reconstruction of the complete original
`0x01c01e5e..0x01c02dbc` audio task and five direct helpers. The task is
nonreturning. Its new C runner exposes bounded observation points after an OS
wait, after a complete queued block, and at either original fatal spin. Those
observations are not native return values or a replacement RTOS scheduler.

This milestone combines the previously reconstructed four-section and
five-section filters, gain ramp, dynamics reset/clone/process callers, and
capture warm-up/reset/layer kernels in the task's original shared RAM layout.
It does not recover every external service or establish physical audio quality,
sample rates, latency, interrupt behavior, or hardware timing.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
The original evidence and this reconstruction retain the
[PolyForm Noncommercial 1.0.0 license](../third_party/ultrarig/LICENSE.md).
This is reconstructed C, not the original source.

## Complete new functions

| Function | Original interval, end excluded | Bytes |
| --- | --- | ---: |
| Nonreturning audio task | `0x01c01e5e..0x01c02dbc` | 3,934 |
| Symmetric recording FIR | `0x01c01234..0x01c01292` | 94 |
| Diagnostic sample tap | `0x01c01292..0x01c012d8` | 70 |
| Capture warm-up wrapper | `0x01c04c42..0x01c04cd8` | 150 |
| Effect-presence scan and dispatch | `0x01c05118..0x01c05160` | 72 |
| Input timing setter | `0x01c05d40..0x01c05d4a` | 10 |

The six entries contain 4,330 bytes and 1,399 instructions. The task itself
contains 1,264 instructions. The isolated return at `0x01c04cd8` belongs outside
the warm-up wrapper's complete body and is not counted as another function.
The registration window at `0x02005250..0x0200525e` is bound as caller evidence.

The FIR consumes signed halfwords from two authenticated data spans:
`0x020364d6..0x020364e0` contains five symmetric coefficients for nine taps;
`0x02036f24..0x02036f38` contains ten for nineteen taps. These 30 bytes are data,
not decoded functions. The complete report contains each span's hash and the
original consumers.

## Task state and routing

The new API is in
[`hyperrig_audio_task.h`](../firmware/include/hyperrig/hyperrig_audio_task.h),
with its implementation in
[`hyperrig_audio_task.c`](../firmware/src/hyperrig_audio_task.c).
Initialize `hyperrig_audio_task` to zero, retain it between calls, and supply a
consistent original-address map and an external-service callback. A positive
wait budget and frame budget bound each invocation.

| Observation | New return | Retained phase |
| --- | ---: | ---: |
| Wait at `0x02040d34` completed, continuation `0x01c02d7a` | 0 | 1 |
| Complete 128-sample block, queue poll `0x01c02d42` | 1 | 2 |
| Fatal spin `0x01c02da2` or `0x01c02dba` | 2 | 3 |

The original task keeps a 104-byte stack frame throughout its lifetime. Its
entry variables are fixed global addresses; its per-block scratch is dead at
the exposed boundaries. The instruction model preserves that stack and its
registers. The C runner retains observation state and mapped firmware state,
then reconstructs the next block's locals. A fatal observation executes one
original self-branch; it does not attempt to simulate an infinite spin.

Important mapped objects include:

| Address | Object and role |
| --- | --- |
| `0x01c1f180` | Input/output gain, mute ramp and timing controls |
| `0x01c26890` | Queue counters, routing state, recording histories, meters and statistics |
| `0x01c234a8` | Four input slots of 128 signed words |
| `0x01c224a8`, `0x01c22ca8` | Four output slots per channel |
| `0x01c23ca8`, `0x01c23f68` | Two 176-word dynamics work buffers; input begins at word 48 |
| `0x01c2bff0`, context at `+76` | Capture wrapper state and native 228-byte context |
| `0x01c2a8e0` | Two 127-triplet warm-up buffers |
| `0x01c32db0` | Shared filter/dynamics controls |
| `0x01c33030`, `0x01c33320` | Four-section and five-section active filter objects |

The task derives input/output slot addresses from masked queue counters. It
performs optional diagnostic playback, recording, input conditioning,
capture/dry routing, filters, dynamics, output service calls and final mute
ramps. It preserves the original dropped-output counter when the output queue
is too far ahead, and the separate periodic timing/statistics updates.

Recording performs three successive factor-two decimation stages. The first
uses the nine-tap FIR and a wrapped tracking/subtraction recurrence; the next
two reuse the nineteen-tap FIR. Symmetric sample pairs wrap at 32 bits before
signed multiplication, accumulators wrap at 64 bits, and the task clips the
stored halfwords after its final shift. No physical recording rate is inferred
from these ratios or from the offline integer timer values.

The diagnostic tap preserves forward-copy overlap behavior. The capture
wrapper executes actual recovered warm-up or reset, fills both triplet buffers,
and recomputes its eligibility word. The task also preserves the original
double reset around the first stereo dynamics clone and the original
left-only clearing path when manual mute is already active; its published
slot flag suppresses the second channel in that case.

## Numerical and platform boundaries

Recovered numerical implementations execute directly on borrowed mapped
objects; no copy of a separate DSP runtime is substituted. Four-section
transition chunks, filter histories/residue, five-section pending updates and
clock statistics, dynamics history/gain tables/meters, FIR arithmetic and
capture warm-up kernels all participate in the instruction comparisons.

The callback at `0x01c34198` is restricted to zero or the reviewed clock
`0x01c04862` at both reads. The new adapter rejects other tokens with `-202`,
including a token changed by the first clock callback. This does not establish
an inventory of every original indirect-call target or configuration writer.

The following sample-related services remain explicit external boundaries:
`0x01c012d8`, `0x01c0158a`, `0x01c01690`, `0x01c01722`, `0x01c0174e`,
`0x01c0179e`, `0x01c01800`, `0x01c0198a`, `0x01c019d8`, `0x01c01de4`,
`0x01c04cda`, `0x01c10e06`, `0x01c11d06` and `0x01c19efa`.
Their test callbacks provide controlled results and mapped mutations to verify
the caller. Those results are not recovered service arithmetic.

In particular, the asynchronous capture wrapper `0x01c04cda` is not aliased to
the recovered numerical processor `0x01c12d34`. Its accelerator coordination
and publication behavior need their own reconstruction. The five-section
entry `0x01c051f0` is the known filter chain; it is not the IR runtime. The
stage-processing boundary `0x01c10e06` is a separate integration dependency.
The OS wait, clock, readiness, accelerator flush, notification, idle and fatal
reporting services also remain callback boundaries.

Mappings and callbacks are synchronous, stable and non-reentrant. Returned
pointers must meet the token's natural alignment up to four bytes, which is
checked before access. Mapped filter/sample objects need compatible typed,
little-endian storage. Task, IO and output argument objects must be disjoint
from mapped memory. Numerical objects retain their earlier disjointness and
bounded channel/tap/shift domains. Diagnostic playback requires a nonempty
mapped halfword sequence and an index within it.

New `-200`, `-201` and `-202` results identify invalid API, missing mapping and
unsupported numerical/alignment/clock domains. They may follow partial writes
and are not resumable original observation states. There is no rollback or
claim of native error behavior for an invalid mapping.

## Verification and provenance

[`audio_task_machine.py`](../tools/audio_task_machine.py) decodes the original
task and helpers and joins unchanged instruction regions for every recovered
dependency. It models packet register ordering, predicated then/else blocks,
signed and wrapped arithmetic, retained stack state and bounded REP operations.
Unknown calls, instruction escapes and uninitialized memory reads fail.

[`verify_audio_task.py`](../tools/verify_audio_task.py) compares all four mapped
buffers, including unchanged neighbors and carried state, plus observation
states and ordered external target/argument lists. At every external call it
also compares a SHA-256 snapshot of all 226,612 mapped bytes. Private CPU
registers and stack bytes are not presented as portable C output objects.

The corpus covers queue wrap/drop behavior, both fatal paths, watchdog
notifications, diagnostic interpolation/fades, recording counter wrap, signed
gain extremes, pending and active filter chains, stereo dynamics lifecycle,
actual capture warm-up with multiple layer kinds, overlap taps, callback
mutations and periodic timing/statistics. The original warm-up busy-loop
counter edge has a focused instruction test; the complete persistent-busy
timeout runs in the C sanitizer harness. The original four-million-iteration
timeout is not replayed in the full instruction comparison.

The pinned original application SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The reviewed MINI v4 image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier binds every loaded instruction window, both FIR tables, the
capture dispatch table, inherited coefficient/configuration constants and the
task registration window against both images. Original input images and all
earlier reports remain unchanged.

Reproduce with a fresh ignored output directory:

```text
python tools/build_audio_task.py --output build/reverse-audio-task-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles a host shared library with undefined-behavior checks,
pi32v2 objects, a separate address/undefined-behavior sanitizer executable,
focused instruction tests, and the comparison report. Outputs are research
artifacts, not flashable firmware. No device, hardware-audio, or release test
is claimed.

The final run is preserved in the ignored directory
`build/reverse-audio-task-03`. Its results are:

| Check | Result |
| --- | ---: |
| C/original instruction comparisons | 317 passed |
| New instruction coverage | 1,399 / 1,399 |
| All loaded instruction coverage | 3,518 / 5,574 |
| Original instruction steps | 661,494 |
| Actual recovered numerical kernel entries | 238 |
| Focused unit tests | 18 passed |
| ASan/UBSan cases | 835 passed |
| C-only API, mapping and domain guards | 31 passed |
| pi32v2 objects | 24 built |

All six new functions have complete instruction coverage in this corpus.
Unvisited instructions belong to inherited dependencies; this task corpus
does not replace their separate verification reports. Sanitizer coverage
contains 768 task prefixes and 67 helper or adapter calls. The C-only guards
include three unaligned host mappings and four unreviewed clock-token cases,
including mutation between the two callback reads.

The final `verification.json` SHA-256 is
`e383931e13906f35d3a34304c09717dfd635086636477fe843e0d2a45f32a5e9`.
The final `build-manifest.json` SHA-256 is
`ed1e0445071bdcaba17472dee49a04fa9c407fe185a787226f6fd40423a1724b`.
All 107 source bindings and 28 artifact bindings were rechecked after the
build. Both image bindings cover all 5,574 loaded instruction windows and
seven static windows. Earlier incomplete build directories remain unchanged.

Independent review checked the full task control flow, continuation points,
FIR and tap helpers, capture transition, borrowed dynamics, and final gain
and statistics packets. The review identified host-alignment and indirect
clock-domain contract gaps; the final guards and focused cases resolve them.
No instruction mismatch remains within the documented domain. The report
counts zero scripted replacements of recovered kernels and separately lists
the unresolved numerical service boundaries above.
