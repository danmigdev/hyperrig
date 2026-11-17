# Reconstructed parameter requests and generated sample transitions

The four-section parameter-request producer now has compilable C and comparisons
against its complete original instruction body. Requests execute the recovered
mathematical coefficient generator, write their actual staged records, and then
feed the unchanged update and sample-processing path. Integration comparisons do
not supply fabricated coefficient or gain transitions.

The only optional external call is the sixth-parameter notification. Its token,
value and before/after state are compared explicitly. This milestone does not
execute that callback's body, the surrounding audio task or hardware. Earlier
sources, models, images and completed reports remain unchanged.

The later [notification reconstruction](DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md)
executes the installed callback, its signed division/clamp and the existing gain
mixer on borrowed native state. It adds separate comparisons and preserves the
external-callback boundary in this earlier report.

Required Notice: Copyright (c) 2026 Manuel Aguirre

The reconstruction retains the original project's
[PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md) and notice.
It is not original source code or a flashable firmware image.

## Complete bodies and evidence

The pinned original M5.71 G v2 image has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The inherited loader validates that image and its complete unpacked application.
Flash address `a` maps to decoded offset `a - 0x02000120`; RAM code uses the
reset copy at CPU flash `0x02056780` for RAM `0x01c00000`.

| CPU range, end exclusive | Complete body | Instructions | Original bytes SHA-256 |
| --- | --- | ---: | --- |
| `0x02028936..0x02028968` | Clamp and quantize one parameter | 18 | `8445c2041bbd22c4bceecf527cc4e5be5dbb04aab470611236ac0648c14307a7` |
| `0x02028a34..0x02028b6c` | Produce a four-section parameter transition | 104 | `a545f6b0edec0ad0c53d7c01edb12ae254ab6c31e0226675ddfe9ebb8d935fc6` |

Direct dependencies execute their original instructions: reset at `0x020289d4`,
request-counter increment at `0x01c05160`, four-section setup at `0x0202898e`,
gain conversion at `0x02028968`, the mathematical coefficient producer at
`0x02028734`, and the previously recovered normalization/float helpers. The
sample side executes the original update/caller/block/ramp bodies and both Q28
kernels from [the audio-path milestone](DSP_AUDIO_PATH_RECONSTRUCTION.md).

The callback installed by recovered startup is `0x0201a9ea`. Its complete static
body `0x0201a9ea..0x0201aa08` has SHA-256
`8a638ea84aa410b5e27a433f23716b1b20d13cefd4937dfe6cf094ff685332f8`.
It divides the supplied value by five, calls the capture gain clamp, stores a
state word and calls the capture mix helper. These are static observations;
this module keeps the notification as an explicit callback boundary.

## State and parameter contract

The new APIs reuse `hyperrig_dsp_audio_path` unchanged: eleven regions totaling
13,292 bytes. No new persistent memory bank or synthetic transition structure is
added. The caller supplies six signed16 input parameters in a separate array and
one uint32 bit pattern interpreted as a signed transition argument.

| Input index | Clamp | Additional operation |
| --- | --- | --- |
| 0 | -240..120 | None |
| 1..4 | -120..120 | None |
| 5 | -120..120 | Round to the nearest multiple of five |

The separate scalar clamp API accepts every signed32 bit pattern and every
uint32 index. Only index zero selects the wider lower bound, and only index five
selects quantization. Rounding computes `(value + sign_adjustment) / 5 * 5`,
where the adjustment is -2 for negative values and +2 otherwise, with signed
division truncating towards zero.

Stored parameters are six signed halfwords at control offsets 218..228. The
producer treats any nonzero control byte 28 as initialized, even if bit zero is
clear. This differs from the sample caller, which tests only bit zero. The
portable implementation preserves both original tests.

When control byte 28 is zero, the producer first runs the existing reset helper.
That path retains the earlier bound of -1280..1280 for the five old stored
parameters used by reset. All incoming signed16 values are supported because
the native clamps restrict them before coefficient generation. Existing stored
parameters are unrestricted when the reset path is skipped.

The signed transition argument clamps to 1..255. A clamped value of one selects
one transition step; other values select four times that value, giving 8..1020
steps. These integers are not assigned milliseconds or other physical units.

The request API returns the native 1 when it stages a new transition and native
0 when all six clamped parameters match. A zero return does not guarantee that
the initial reset left state unchanged. Invalid host pointers, a required but
missing notification callback, or an invalid old reset parameter return new -1
before writes. Inputs and IO must not overlap runtime, and input storage remains
immutable during the call. No re-entry, concurrent mutation or IO mutation is
supported.

## Original ordering and generated records

The producer first performs the conditional reset, clamps all six inputs into
private local storage, and compares them with the stored halfwords. If every
value matches, it returns zero without incrementing the request counter or
replacing any pending transition.

A changed request increments the uint32 counter at `0x01c34468`, with wrap,
then clears control byte 1. If the sixth value differs and the token at
`0x01c3446c` is nonzero, it calls that token with the signed clamped/quantized
value. This call happens before the six stored parameters are replaced.

The callback may synchronously mutate runtime within the documented domain.
Subsequent coefficient/gain reads observe those changes. The locally captured
six input values survive the callback and then replace the stored halfwords;
mutations to those same halfwords are overwritten in the original order. The
verifier compares the callback token, value and complete runtime immediately
before and after each call. Its mutation cases change the divisor, gain, active
coefficients, gate, stored parameters, counter and callback token. They never
provide staged coefficient records.

Next, the producer generates four complete sets of five coefficient words using
the recovered second table and current divisor. Each generated section occupies
a private 44-byte local object in the original stack frame; only its coefficients
and enable byte are copied into staged storage. Histories, residue and active
coefficient/enable bytes remain unchanged by the request, except for the earlier
conditional reset or an explicit notification mutation.

For a multi-step transition, each coefficient delta is the signed wrapped
32-bit target-minus-active difference divided by the positive step count,
truncating towards zero. For a one-step transition, all coefficient deltas are
zero. The original conditional at `0x02028b02` encloses the load, subtraction
and division together; skipping the complete block leaves the initial zero.

The gain target comes from the recovered gain helper. For multiple steps, the
producer divides the signed wrapped target-minus-current gain by `steps * 32`,
truncates, then shifts the resulting bit pattern left by five. The one-step gain
delta is zero. It stores the target enable bytes and count, sets control byte 1,
and returns one. Thus the complete 176-byte staged record comes from executed
producer logic.

The unchanged sample path copies that record when it observes the pending flag.
It advances coefficients and gain in chunks of at most 32 samples and copies
exact target values on the final step. The new integration comparisons execute
startup, request and processing as separate complete native entries on carried
state. They check full convergence for transition arguments 1, 2, 3, 31 and 255,
including the entire 1020-step case, as well as replacing pending requests and
interrupting active transitions. No enclosing native scheduler is invented.

## Independent comparison and limits

The instruction model subclasses the frozen audio-path model and adds the two
complete producer bodies. Original calls to the coefficient producer use the
original stack-local destination and private request frame. The portable C uses
the unchanged recovered setup API on a separate local C object. Both sides
compare all eleven state regions, all sample words, native request/clamp results,
the immutable six input halfwords, and notification snapshots.

The corpus covers the complete effective scalar clamp intervals, signed32
extremes, incoming signed16 extremes, all 255 clamped transition arguments,
zero/positive/extreme divisors, request-counter wrap, one-step zero deltas,
signed wrapped deltas, initialized/disabled gates, unchanged requests, optional
notifications and carried histories. Full-instruction coverage is reported for
the two new bodies, without claiming exhaustive whole-firmware input coverage.

Processing retains the earlier 0..128 samples per call domain and all earlier
buffer-disjointness requirements. Callback bodies, physical platform writers,
the audio scheduler and dynamics sample processor remain outside this milestone.
The existing pinned ISA/binary32 semantics remain shared assumptions; this is
not a new processor, timing or audio measurement.

Run the standalone builder with a fresh output directory:

```text
python tools/build_dsp_transition.py --output build/reverse-dsp-transition-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder produces a warning-clean UBSan host library, seven freestanding
pi32v2 r3 objects, focused instruction tests and an exact-buffer ASan/UBSan
harness. It does not depend on earlier ignored build reports. MINI binding
requires the reviewed v4 image SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`
and compares every loaded code region, both coefficient tables, the dynamics
reset-copy bytes, the prior audio caller windows and the static installed
callback body locally.

## Recorded validation

Final output is `build/reverse-dsp-transition-03`, an ignored build directory.
The partial `-01` and `-02` build directories remain preserved. All 122 new
instructions are visited; the combined loaded model visits 1,293 of 1,383
instructions. The remaining instructions belong to reused regions and do not
represent omitted new producer instructions.

| Evidence | Result |
| --- | ---: |
| Original-instruction comparisons | 1,812 |
| Clamp / request / startup / process comparisons | 963 / 530 / 6 / 313 |
| Changed / unchanged native request results | 460 / 70 |
| New instructions visited / decoded | 122 / 122 |
| Complete mathematical coefficient-producer calls | 1,876 |
| Actual Q28 numerical kernel calls | 4,836 |
| Sample inputs checked | 39,040 |
| Notifications / mutating notification cases | 22 / 4 |
| Carried calls | 366 |
| Completely converged transitions / maximum steps | 5 / 1,020 |
| Maximum instruction packets per compared entry | 11,889 |
| Focused instruction tests / invalid-API checks | 14 / 26 |
| ASan/UBSan exact-buffer cases / notifications | 261 / 261 |
| Locally bound loaded code regions | 32 |
| Source hashes / generated artifact hashes | 58 / 11 |

The seven pi32v2 objects compile without warnings. The six reused objects are
byte-identical to the preceding audio-path build; its source and artifact hashes
remain unchanged. The new target object is 1,476 bytes.

| Output | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_dsp_transition.c` | `794e835125ce662f82ae604b0f741e22f6d0eb0a7c8163fbedf698843f6cf344` |
| `verification.json` | `2a0bf1c3e65708f1e2f6bb1633543b74417339177a062f90f6fec0a1a629a422` |
| `hyperrig_dsp_transition.pi32v2.o` | `de3b24dfb8cc7a755e0fe0a35a0e294303fbc30397409c6490d6f796699180aa` |
| `sanitizers.json` | `f7fbf11a693588801a8618e8bc4627d6b2d87ef4d7f50f90790421abdd7dc078` |
| `build-manifest.json` | `37e9ef0896cc88149f6aaf6da243c07fdb04734c548a12c74fbe48f98c9b08c2` |

The deterministic compared output/state stream has SHA-256
`88f275592e33207ccfb4b6ccf3bdd2cb101f0074bb158d26ed479a680b4aedf6`.
