# Reconstructed coefficient conversion and staging

The upstream staging path for the [five-section filter chain](BIQUAD_CHAIN_RECONSTRUCTION.md)
now has a portable C reconstruction. It clamps and stores the requested parameter,
forms the original mathematical producer arguments, and publishes a pending
section. The downstream normalization and float-to-Q28 helpers are also recovered.
The mathematical producer at `0x02028734` remains an explicit scripted boundary;
these results do not establish that its coefficients have been regenerated.

Sources: [`hyperrig_biquad_coefficients.c`](../firmware/src/hyperrig_biquad_coefficients.c)
and [`hyperrig_biquad_coefficients.h`](../firmware/include/hyperrig/hyperrig_biquad_coefficients.h).
They retain the original Required Notice and license. Earlier reconstructed
sources, verification reports and firmware images are unchanged.

## Pinned executable and static evidence

The original G v2 M5.71 image has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The verifier checks the original manifest and requires the complete decoded
application to match that image before decoding these regions.

| CPU range, end exclusive | Executed behavior | Function SHA256 |
| --- | --- | --- |
| `0x01c05160..0x01c0516e` | Increment a shared counter word | `f7f4cd4a0cd2746ceaeb2dce985dcd735b858261feecdb33f72d329c3a001b17` |
| `0x01c05182..0x01c051a2` | Convert a binary32 value to Q28 | `a5a7bef9c9fd9c2cb9b1aa3e1a26322bf8721ebfe9f77131ac37a91882a2a00d` |
| `0x020286a0..0x0202870a` | Normalize/store five coefficients and two flags | `d57386a4861b9cc2927a62627e6ff440f84245cbb574e472909ef08c03d25cc8` |
| `0x02028892..0x020288d6` | Form table/mode/parameter arguments | `bf388a6f01fe1fc4b8bc43775729599503112bd34e115cc588c344ad58ebf3c6` |
| `0x020288d6..0x02028920` | Clamp a request and publish a pending section | `e4d5de92ac4b351c662d1ba5ccb31affc3dc3a27c111525ecb2693e45d9979b6` |

The RAM functions execute from the copy based at `0x01c00000`, loaded from CPU
flash `0x02056780`. All five regions are byte-identical in the reviewed MINI v4
image, SHA256 `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

Two additional regions are checked for identity but are **not executed as code**:

- Mathematical producer `0x02028734..0x02028892`, SHA256
  `e9d849f6733af1988a38931495d2039c90586e8b759f1db5fd86ae5c3a6dc9eb`.
- Ten-byte table `0x0203a55c..0x0203a566`, SHA256
  `54f4a53a7dfc1bfa17702e31c5d031ce4f6e0dc2f6125463b53ffe00edb415c7`.
  Its five uint16 values are read by the executed setup instructions.

## Request ownership and ordering

The existing runtime retains independent staged and active sections. This module
adds an explicit view of the shared counter and five stored parameter bytes:

| CPU address | Recovered contents |
| --- | --- |
| `0x01c34468` | Counter incremented modulo 2^32 on entry |
| `0x01c32e59` | Five signed int8 parameter bytes |
| `0x01c32e54` | Five pending-update bytes |
| `0x01c32dc8` | Elapsed average reset by a valid staging request |
| `0x01c33240` | Five staged sections, 44 bytes each |

The counter increments before the unsigned index check, including for indices
outside zero through four. An out-of-range index then returns without changing
parameters, sections, pending bytes or the average, and without calling the
mathematical producer. The counter's meaning outside these calls is unassigned.

For an accepted section the original order is:

1. Clamp the full signed 32-bit parameter to -12 through 12.
2. Clear that section's pending byte and store its signed parameter byte.
3. Reset the elapsed average to zero.
4. Form the producer arguments and call the mathematical boundary.
5. Set the section's pending byte to one after the producer returns.

The packet at `0x02028902` computes a section offset in its A instruction while
its B instruction stores the **old** parameter register. The verifier executes
both halves with their original input registers. Serializing those instructions
would store an offset in place of the clamped parameter.

Neither the stage wrapper nor the setup helper changes active sections. The
existing chain caller applies pending sections later. This verifier checks all
active bytes and every staged history, residue and reserved byte for preservation.
It does not make an interrupt-safety or simultaneous reader/writer guarantee.

## Producer arguments and the explicit boundary

Setup loads the stored signed int8 parameter and forms this call:

| Section | Numeric mode | Table value converted to binary32 |
| --- | --- | --- |
| 0 | 0 | 100 |
| 1 | 1 | 400 |
| 2 | 1 | 1200 |
| 3 | 1 | 3200 |
| 4 | 2 | 7000 |

It passes the corresponding staged section as the destination, converts the
signed parameter to binary32, and passes a fifth word `0x3f666666`, the binary32
approximation to 0.9. The C request names that word `width` only to distinguish
the argument; this milestone does not certify a physical bandwidth or Q meaning.
No frequency units, sample rate or user-facing effect identity are established.

The standalone setup helper accepts every stored int8 value, including values
outside -12..12. Clamping belongs to the wrapper, not to setup itself. The test
corpus covers all 256 parameter byte values at every section position.

The callback replaces **the entire `0x02028734` function**, including its
transcendental dependencies. It may only write the destination's five coefficient
words and enabled/residual bytes. State re-entry, concurrent mutation, retained
pointers and changes to other storage are outside the API. Comparisons include
the exact argument words and all mapped state at the call boundary.

Scripted test producers either leave the destination unchanged or supply chosen
binary32 numerator/denominator words to the original normalization helper. In the
instruction model that helper and its five conversion calls actually execute;
the C callback calls the reconstructed normalizer. The supplied words are test
inputs, not claimed results of the omitted producer. Static tracing still points
to `0x01c0516e`, `0x020285d4`, `0x02028646`, `0x02028676` and `0x0202870a` as
upstream mathematical dependencies to recover next.

## Normalization and binary32 conversion

Given raw binary32 words `b0, b1, b2, a0, a1, a2`, the helper stores:

```text
Q28(binary32(b0 / a0))
Q28(binary32(b1 / a0))
Q28(binary32(b2 / a0))
Q28(binary32((-a1) / a0))
Q28(binary32((-a2) / a0))
```

Negation flips the sign bit before division, including for zero and NaN inputs.
The enabled flag takes the low byte of its input word. The residual flag becomes
zero for an input word of zero, otherwise one. Coefficients are stored in order;
history, residue and reserved bytes are preserved.

The conversion helper performs these three operations separately:

```text
scaled = binary32(value * 2^28)
adjusted = binary32(scaled + (-0.5 if value is negative or unordered, else +0.5))
result = saturating_int32_truncation(adjusted)
```

The sign comparison is the original unordered-or-less floating comparison.
Signed zeros both produce integer zero. Infinities saturate by sign. Arithmetic
canonicalizes either sign/class of NaN to positive `0x7f800001`, so **every NaN
input ultimately produces INT32_MAX**, including negative NaNs. This differs
from applying the integer-conversion instruction directly to a negative NaN.

Binary32 rounding before truncation is observable. For input `0x30ffffff`, the
scaled magnitude is just below 0.5. Adding 0.5 rounds to exactly 1 in binary32,
so the result is 1; the negative input produces -1. Replacing the original
sequence with exact-real `floor(abs(value) * 2^28 + 0.5)` would produce zero for
that case. The next smaller magnitude, `0x30fffffe`, does produce zero.

The reconstructed C uses integer operations on binary32 words. Its division
rounds nearest with ties to even, supports gradual underflow, handles signed
zeros/infinities and produces the measured arithmetic NaN word. Conversion uses
an exact dyadic sum with binary32 rounding before integer truncation. It does not
depend on host `float`, host rounding modes, compiler contraction or libm.

The instruction oracle independently imports the exact-rational arithmetic and
floating comparison models from the pinned [local ISA source](LOCAL_SOURCES.md),
commit `1f09804d36ddcba36dbd84cb6242ef88f35f15b7`. Their hardware evidence is in
`hw/report-s.md` and `hw/report5-b.md`; the existing MIT-0 notices remain in their
original files. These are upstream hardware observations, not new MINI tests.

## Verification and build limits

The completed run `build/reverse-biquad-coefficients-01` passed **11,071
C-versus-original-instruction comparisons**:

| Entry point | Comparisons |
| --- | ---: |
| Float-to-Q28 | 5,762 |
| Normalize/store | 2,560 |
| Setup | 1,280 |
| Stage request | 1,469 |

All **97 of 97** scoped instructions were visited. An additional **6,912** direct
binary32 division comparisons check the C primitive against the independent
exact-rational ISA model before Q28 conversion can hide rounding differences.
These are separate from the 11,071 instruction comparisons.

Cases include both signs across every binary32 exponent field, representative
significands, subnormals, zeros, infinities, NaN classes/payloads, rounding
boundaries and deterministic random words. Staging cases cover all int8 byte
values at all five positions, full int32 clamp endpoints, unsigned invalid
indices, counter wrap, 125 carried requests and 2,725 scripted producer calls.
Of the instruction comparisons, 5,309 check complete history/active preservation.

Fifteen focused tests, eleven invalid-API checks and one valid ignored-index call
with no IO passed. An ASan/UBSan executable passed **1,536 exact-buffer cases**.
The host library builds with warnings as errors and UBSan. The pi32v2 r3 object
builds successfully and is **1,860 bytes**, SHA256
`298ec4bd694d5f6daaa9a8b97c789e46c00b89ca3a31dc7f177e539015a4838a`.
That is a relocatable object size, not a firmware size, execution-time or RAM-use
measurement. The object references compiler runtime helpers `__udivdi3` and
`__umoddi3`; final firmware linkage and target execution are not established.

The C source SHA256 is
`07353e8002ff5b952604b0a71b96be185ad0089b273775b45b6b2d90d24d0d81`.
The completed verification report SHA256 is
`44058ed8ed30a0886dde3e17de14af630bb5d0529e75ba5945b44c65df472cd3`.
Its source hashes cover the reconstruction, verifier, tests, decoder and imported
ISA semantic models. No new hardware or audio test was performed. No firmware
was flashed or changed, and no filter stability or latency claim is made.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_biquad_coefficients.py --output build/reverse-biquad-coefficients-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the workspace.
The builder refuses existing output directories and writes the host library,
target object, sanitizer executable/report, comparison report and artifact
manifest under the new ignored build directory. Generated artifacts remain
outside Git. New APIs report -1 before writes or calls for invalid arguments;
stage returns 1 for an ignored index and 0 for a staged request. Those statuses
are a C API convention, not original return-register semantics.

The subsequent [bounded generator reconstruction](BIQUAD_GENERATOR_RECONSTRUCTION.md)
implements the mathematical producer and all five local dependencies, connecting
the unchanged staging/setup APIs to recovered math. Its separate report includes
raw coefficient comparisons before normalization. The callback-based baseline
above and its evidence retain their original scope.
