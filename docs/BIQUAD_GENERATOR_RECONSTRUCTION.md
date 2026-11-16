# Reconstructed bounded coefficient generator

The mathematical producer at `0x02028734` and all five local mathematical
dependencies now have a C reconstruction. The new verifier executes their
original instructions together with the previously recovered setup, staging,
normalization and Q28 conversion helpers. **No scripted mathematical callback
remains in this module's comparisons.**

Sources: [`hyperrig_biquad_generator.c`](../firmware/src/hyperrig_biquad_generator.c)
and [`hyperrig_biquad_generator.h`](../firmware/include/hyperrig/hyperrig_biquad_generator.h).
The implementation uses integer operations on binary32 words and preserves the
original Required Notice and license. The earlier
[coefficient staging module](BIQUAD_COEFFICIENT_RECONSTRUCTION.md), its sources
and its report remain unchanged; new adapters connect it to the recovered math.

This is a bounded numerical reconstruction ending at staged coefficients.
Initialization and physical meaning of the producer's runtime divisor word,
integration into a complete firmware build, and hardware/audio behavior remain
outside this milestone.

## Pinned functions

The original G v2 M5.71 application SHA256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Executed behavior | Function SHA256 |
| --- | --- | --- |
| `0x01c0516e..0x01c05182` | Scale input, then call exponential approximation | `91c119674a597c2c819c416f7a8941353da32dae1bda535afb3b37a517ff6f3c` |
| `0x020285d4..0x02028646` | Reduced exponential series and power-of-two scaling | `6a9734c4493c0f37e0b119d3fe6c8694e85323407aab9023fcf7472f1af43f8b` |
| `0x02028646..0x02028676` | Cosine polynomial | `c3f8b0ff539b4de43e485e735f0da977bf3eb21da4120e554d95b4134a4c6fe4` |
| `0x02028676..0x020286a0` | Sine polynomial | `e60ce1c9aa16f8b454b57119a48b9e355e11a64ec0c2f5accd1d81266472bad2` |
| `0x0202870a..0x02028734` | Twenty-iteration square-root approximation | `e6ca07e2d6293db53a8c9074338f0224d8cb5ad203873bd139d43cf10a5381c9` |
| `0x02028734..0x02028892` | Complete three-branch coefficient producer | `e9d849f6733af1988a38931495d2039c90586e8b759f1db5fd86ae5c3a6dc9eb` |

The RAM helper uses the same reset copy as the previous DSP work: RAM base
`0x01c00000`, CPU flash source `0x02056780`. All six new regions, all five
previously recovered coefficient regions and the setup table are byte-identical
in reviewed MINI v4, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

The verifier validates the original image and complete decoded application
before decoding. Function hashes and source/model hashes are recorded in its
new report. No original image or earlier report is modified.

## Arithmetic and approximations

Every arithmetic operation rounds separately to binary32 with nearest-even
rounding, gradual underflow and the pinned pi32v2 NaN semantics. The portable C
does not use host `float`, libm or the host floating-point environment.

Addition represents finite inputs exactly as nine uint32 limbs in units of
2^-149, adds or subtracts their magnitudes, then rounds once. This retains distant
exponents, cancellation, ties and signed-zero behavior. Multiplication uses a
uint64 significand product plus an explicit exponent and rounder. Unsigned
integer conversion uses the same rounder. Division and float-to-Q28 conversion
reuse the unchanged previous module.

The original exponential approximation operates as follows:

1. Subtract binary32 `0x3f317218` while the input exceeds +0.5, counting upward.
2. Add that same constant while the reduced input is below -0.5, counting down.
3. Starting with term=1 and sum=1, perform eight iterations of
   `term = term * (reduced / i)` and `sum = sum + term`, for i=1..8.
4. Double the sum repeatedly for a positive count, or multiply repeatedly by
   0.5 for a negative count.

The scaling wrapper first multiplies its input by `0x3debc8e3`. Both constants
are retained as original bit patterns. Replacing the series with a host
exponential, or changing operation order, would define a different numerical
implementation.

Cosine starts with sum=term=1 and negative_square=-(x*x). For even i=2..18,
it computes `term *= negative_square / ((i-1)*i)` and adds that term to the sum.
Sine starts with sum=term=x and uses odd i=3..19. Integer denominators are
converted to binary32 before division. These helpers perform **no argument
range reduction**, and their names describe their polynomial form rather than
an accuracy guarantee across all input words.

Square root returns positive zero for ordered inputs <=0. Otherwise it starts
with `max(input, 1)` and performs exactly twenty iterations of
`estimate = (estimate + input/estimate) * 0.5`. The original fixed iteration
count is observable: input `0x00000001` returns `0x35800000`, while positive
infinity returns arithmetic NaN `0x7f800001`. Both differ from correctly rounded
mathematical square root. The reconstruction preserves these results.

The instruction oracle imports the independent exact-rational arithmetic and
branch models from the pinned [local ISA source](LOCAL_SOURCES.md), commit
`1f09804d36ddcba36dbd84cb6242ef88f35f15b7`. Its original MIT-0 notices and hardware
evidence remain unchanged. Reusing that evidence is not a new MINI hardware test.

## Producer inputs and branch formulas

The producer receives numeric mode, binary32 table value, binary32 signed
parameter and the binary32 width word already recovered in the staging module.
It also reads an unsigned word from **`0x01c1f7f8`**, converts it to binary32 and
uses that result as a divisor. The new C API supplies this word explicitly and
treats it as immutable for the call. Its initialization, physical unit and
possible changes elsewhere have not been recovered here.

The common calculations, retaining the original operation order, are:

```text
A = scaled_exp(parameter * 0.5)
angle = (table_value * binary32_word(0x40c90fdb)) / binary32(unsigned_divisor)
C = cosine_polynomial(angle)
S = sine_polynomial(angle)
```

The formulas below denote a separately rounded binary32 operation at every
operator. They explain the recovered branches; the C source and raw-word
comparisons retain the exact evaluated sequence.

For **mode 1**:

```text
alpha = S / (width + width)
t = alpha / A
a0 = t + 1
a1 = C * (-2)
a2 = 1 - t
u = A * alpha
b0 = u + 1
b1 = a1
b2 = 1 - u
```

The other branches first compute:

```text
p = A + 1
m = A - 1
mc = m * C
v = ((S * 0.5) * square_root_20(2)) *
    (square_root_20(A) + square_root_20(A))
pc = p * C
```

The original evaluates square_root_20(A) once and doubles that result; the
notation above expresses its value. For **mode 0**:

```text
t = p + mc
a0 = t + v
a1 = (m + pc) * (-2)
a2 = t - v
u = p - mc
b0 = A * (u + v)
b1 = (A + A) * (m - pc)
b2 = A * (u - v)
```

For **every other mode**, including unsigned values beyond two:

```text
t = p - mc
a0 = t + v
a1 = (m - pc) + (m - pc)
a2 = t - v
u = p + mc
b0 = A * (u + v)
b1 = (A * (-2)) * (m + pc)
b2 = A * (u - v)
```

The enabled flag is zero for either signed parameter zero and one otherwise.
The residual flag is one only for mode zero. Width affects the mode-one branch;
the other branches ignore its value. The original normalizer then stores Q28
values for `b0/a0`, `b1/a0`, `b2/a0`, `-a1/a0`, and `-a2/a0` as previously
recovered. No equation here certifies effect routing, frequency units, physical
sample rate or filter stability on a pedal.

The new `generate_input` API returns the six raw numerator/denominator words and
two flag words passed to normalization. These are compared directly with the
original call arguments, before division or Q28 conversion can hide differences.
`generate` then invokes the unchanged normalizer. `generate_setup` and
`generate_stage` connect the existing setup/staging code to this real producer.
They preserve the prior clamp, counter, pending-byte and elapsed-average order.

## Bounded domain and remaining limits

The standalone exponential API accepts finite binary32 input with magnitude
at most 16. Its scaled wrapper and the direct producer parameter accept finite
magnitude at most 128. Invalid values return the new status -1 before output
writes. These are explicit C/verifier bounds: the original exponential's
range-reduction loops have no iteration cap and need not progress for infinity
or sufficiently large finite values.

The bounds cover every signed int8 stored parameter and every staging request
after the original -12..12 clamp. Direct cosine, sine and square-root helpers
accept all binary32 words, including NaNs and infinities. Mode, table-value word,
width word and unsigned divisor accept all uint32 patterns. A zero divisor
follows the original special-value arithmetic; it is not silently replaced.

Buffers must be distinct and sufficiently sized. No concurrent mutation,
callback re-entry or retained pointers are supported. The new generator adapters
have no external mathematical callback. The complete active-chain sample
processor remains the separately verified [earlier module](BIQUAD_CHAIN_RECONSTRUCTION.md);
this report does not claim a complete firmware or physical audio pipeline test.

## Verification and artifacts

The completed run `build/reverse-biquad-generator-01` passed **5,542 original
instruction comparisons**:

| Entry point | Comparisons |
| --- | ---: |
| Scaled exponential | 262 |
| Exponential approximation | 528 |
| Cosine polynomial | 678 |
| Sine polynomial | 678 |
| Twenty-step square root | 678 |
| Complete producer | 464 |
| Setup with complete producer | 1,280 |
| Stage with complete producer | 974 |

All **190 new instructions** and **287 combined instructions** were visited.
Every mathematical dependency executes from decoded original bytes. There are
**2,714 raw pre-normalization comparisons**, zero scripted mathematical calls,
75 carried staging requests, and 2,718 full staged-history/active-state
preservation checks. The maximum observed run was 612 interpreter packets;
that count is not a target timing measurement.

An additional **18,069 primitive comparisons** test integer C arithmetic against
the independent rational model: 8,432 additions, 8,432 multiplications and
1,205 unsigned conversions. Cases include both signs, every exponent field,
subnormals, cancellation, normal/subnormal rounding boundaries, signed zeros,
infinities, NaN signs/classes and deterministic random words. Production tests
cover all stored int8 bytes at every section, every clamped parameter across
seven divisor words, full int32 clamp endpoints, ignored unsigned indices,
divisor-conversion ties, all numeric branches and unusual width/table words.

Fourteen focused tests and **35 invalid-API checks** passed. The host library
build uses warnings as errors and UBSan. An ASan/UBSan executable passed
**450 exact-buffer cases**. Both pi32v2 r3 objects compile successfully:

- New generator: **3,556 bytes**, SHA256
  `98a630219104bd868a5d528c08f0a4bf610f8a25089c8ca3c6e8b2d0ca573f12`.
- Unchanged coefficient dependency: **1,860 bytes**, SHA256
  `298ec4bd694d5f6daaa9a8b97c789e46c00b89ca3a31dc7f177e539015a4838a`,
  identical to its earlier build.

These are relocatable object sizes. The generator references the coefficient
module and `memset`; the coefficient dependency retains its compiler-runtime
`__udivdi3` and `__umoddi3` references. Final firmware linking and execution,
stack use and latency on the target have not been established.

The new C source SHA256 is
`68d682d1e9cb7f0042d1f5f474fb4eb0d186d3577cf8c78ef7199061427a6cde`.
The completed report SHA256 is
`006bd6116ae8cd6648f3aa0954168f0c58515fcbe278e4454f682659d4c46042`.
Its 27 source hashes include the previous dependency sources and independent
decoder/semantic models. Earlier chain and coefficient source hashes still
match their immutable reports. No device was accessed, no firmware was changed
or flashed, and no new hardware or audio test was performed.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_biquad_generator.py --output build/reverse-biquad-generator-new
```

Optionally provide `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder requires a new output directory under ignored `build/`
and writes the host library, target objects, sanitizer executable/report,
comparison report and artifact manifest there. Generated artifacts remain
outside Git.

The subsequent [filter pipeline milestone](BIQUAD_PIPELINE_RECONSTRUCTION.md)
connects this unchanged generator through staging to active sample processing,
including carried history and requests made inside clock callbacks. It also pins
the reset divisor 48000 and guarded startup argument 48077 as static evidence.
Complete initialization, physical rate and surrounding audio scheduling remain
outside that integration.
