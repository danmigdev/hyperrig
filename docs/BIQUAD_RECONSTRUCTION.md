# Reconstructed Q28 recursive filters

Two shared numerical filter kernels are now available in portable C, separately
from the existing [A2 engine](NATIVE_RECONSTRUCTION.md). Both process an int32
buffer in place using five Q28 coefficients and two input/output history samples.
The first adds a fixed rounding term; the second carries the fractional residue
between samples. This is a numerical dependency for further effect reconstruction,
not a complete effect, coefficient generator or audio pipeline.

Sources: [`hyperrig_biquad.c`](../firmware/src/hyperrig_biquad.c) and
[`hyperrig_biquad.h`](../firmware/include/hyperrig/hyperrig_biquad.h).
The original Required Notice and license are retained. Earlier reconstructed
sources, verification reports and firmware images remain unchanged.

## Pinned functions and callers

The original G v2 M5.71 application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Behavior | Function SHA256 |
| --- | --- | --- |
| `0x01c15dec..0x01c15fdc` | Q28 recursive filter with fixed rounding | `55d13a24da7edc35428cfb5787fb2a34d4c32ad39a6becb03d168030afca1421` |
| `0x01c15fdc..0x01c16222` | Q28 recursive filter with fractional residue | `0629abebad5de14d3dc7ed2c267911322f5d72eaa0aa85371a82347525df86c8` |

These functions execute from the RAM copy starting at `0x01c00000`, loaded from
CPU flash `0x02056780`. The verifier obtains their bytes from the pinned decoded
application and decodes them through the existing pi32v2 instruction table.

A representative caller segment, `0x01c05280..0x01c05362`, SHA256
`0958daff8674996cb9d88e72b4b3e72731b27a52f29289c86efd653f708f41de`,
selects these kernels for five consecutive 44-byte sections. Each section's byte
40 controls whether its filter runs; byte 41 selects the residue variant when
nonzero. The same sample pointer/count are passed through each enabled section.
That caller is a static trace, not part of the executed verification or evidence
for a specific user-facing effect name.

Both kernels and the caller segment are byte-identical in the reviewed MINI v4
image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This binds the numerical reconstruction to the released image without establishing
target execution or audio behavior.

## State and arithmetic

Original entry arguments are sample pointer in `r0`, sample count in `r1`, and
state pointer in `r2`. The recovered state fields are:

| Byte offset | Content |
| --- | --- |
| 0, 4, 8 | Signed Q28 feedforward coefficients `b0`, `b1`, `b2` |
| 12, 16 | Signed Q28 feedback coefficients `f1`, `f2`, added as stored |
| 20, 24 | Previous inputs `x[n-1]`, `x[n-2]` |
| 28, 32 | Previous outputs `y[n-1]`, `y[n-2]` |
| 36 | Unsigned residue used by the second kernel only |

For each sample the signed products contribute to:

```text
accumulator = bias + b2*x[n-2] + b1*x[n-1]
                   + f1*y[n-1] + f2*y[n-2] + b0*x[n]
```

The MAC accumulates modulo `2^64`. The result is then interpreted as signed and
arithmetically shifted right by 28. Positive overflow clips to `2147483647`;
negative overflow clips to **`-2147483647`**. An exactly representable result of
`-2147483648` is retained, so this is not interchangeable with a conventional
int32 clamp. Saturated output becomes the subsequent output history.

The rounded kernel starts each MAC at `2^27`. Without accumulator overflow this
rounds to nearest with ties toward positive infinity: applying a half-gain
coefficient to `[-3, -1, 1, 3]` yields `[-1, 0, 1, 2]`. It leaves the residue
field unchanged.

The residue kernel starts each MAC at the previous unsigned residue and saves
the accumulator's low 28 bits before shifting. It does this even when the output
saturates. The first residue is zero-extended from its entire uint32 word; it is
not masked until a sample has been processed. A half-gain coefficient with zero
initial residue maps four inputs of `1` to `[0, 1, 0, 1]`, and four inputs of `-1`
to `[-1, 0, -1, 0]`. The carry persists between processing calls.

The original kernels process the low count bits first, then groups of four.
Their swaps preserve the same canonical history order after odd/even block sizes.
The C loops use that canonical order directly. Block subdivision was checked for
both variants, including residue carried across calls.

## API and verification boundary

`hyperrig_biquad_q28` is a 40-byte structure containing five coefficients, four
history words and residue. Both functions use this structure; the rounded
function ignores its final word. Coefficients are immutable during processing.

The new C API accepts zero through 128 samples per call. A valid state is required
even for an empty block; a null sample pointer is allowed only for zero samples.
Invalid arguments return the new status **-1** before writes; success returns
**0**. Incidental original register return values are not treated as semantic
results. Buffers must be sufficiently sized and must not overlap the state.
No allocation or concurrent mutation is supported.

All signed int32 coefficients, histories and samples, and all uint32 initial
residues are admitted by this bounded numerical model. This does not establish
filter stability, a sample rate, a particular input Q format or safe gain for a
complete signal chain. Coefficient design, reset/enable policy, the five-section
caller, effect routing, IR processing and audio scheduling remain separate work.

The restricted interpreter executes the original arithmetic, branches and memory
accesses. Unknown instructions, escaping branches, uninitialized reads and writes
outside sample/history/residue/private-stack ranges fail. Saved-register frames
are represented by their ABI footprint because the kernels do not inspect those
saved bytes. Neither function calls an external service or accesses a peripheral.

## Results

The completed run passed **1,864 C-versus-instruction comparisons**:

| Variant | Comparisons | Instructions visited / decoded |
| --- | ---: | ---: |
| Fixed rounding | 932 | 162 / 162 |
| Fractional residue | 932 | 184 / 184 |

Comparisons check every output sample, all five coefficient words, four history
words, the residue word, and guard words around the state/sample buffers. Cases
cover every block length from zero to 128, each independent coefficient position,
positive and negative saturation, exact `INT32_MIN`, 64-bit wraparound, random
full-range states, unusual initial residues and block subdivision. The 384
successive sub-block comparisons are included in the total, not additional cases.

Twelve analytic instruction tests passed. Ten invalid-API checks and two valid
empty/null-buffer checks also passed. The host library builds with warnings as
errors and UBSan. A separate ASan/UBSan executable passed **258 exact-buffer
cases**, covering every supported count for both variants.

The pi32v2 r3 build produces a **628-byte relocatable object**. That is an object
file size, not a linked firmware size, RAM budget or latency measurement. This
component has not run on the pedal, and no hardware or audio test was performed.

## Reproduce

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows the builder uses WSL Ubuntu:

```powershell
python -B tools/build_biquad.py --output build/reverse-biquad-new
```

Optionally supply `--mini-image` with the reviewed `hyperrig-mini-v4.app.bin`
inside the workspace. The builder refuses an existing output directory and
produces a host library, target object, sanitizer executable/report, source-hashed
verification report and artifact manifest. Generated files remain outside Git.
The completed local run is `build/reverse-biquad-01`.

The [five-section chain](BIQUAD_CHAIN_RECONSTRUCTION.md) now reconstructs section
updates and the complete caller, executing both kernels internally. Coefficient
generation is traced to its floating-point producer and remains the next bounded
DSP step toward a complete effect or shared equalization path.
