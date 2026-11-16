# Native reconstruction of UltraRig TANK-G

A **three-channel, int32 A2-Lite capture engine in compilable C** is available,
with a loader, input stage, dilated layers, activations, residuals, and final
head. It reconstructs the optimized path observed in UltraRig alpha11/M5.71
TANK-G v2, within the shift domain described below. These are not the original
sources and do not constitute the complete firmware: effects/IR, audio frontend,
and drivers remain separate components. Boot on the MINI has not been verified.
The files retain the Required Notice and UltraRig license: see
[PROVENANCE.md](PROVENANCE.md).

Two additional [Q28 recursive filters](BIQUAD_RECONSTRUCTION.md) are reconstructed
separately, with 1,864 comparisons against their original instructions. They
provide shared numerical dependencies for effects beyond A2; coefficient
generation, complete effect behavior and audio integration remain separate work.
The [five-section chain](BIQUAD_CHAIN_RECONSTRUCTION.md) now connects those kernels
through the reconstructed original caller, adding 2,445 comparisons for staged
updates, history retention and timing-accounting behavior.
The [coefficient staging/conversion path](BIQUAD_COEFFICIENT_RECONSTRUCTION.md)
adds 11,071 comparisons for request ordering, normalization and binary32-to-Q28
conversion. The subsequent [bounded generator](BIQUAD_GENERATOR_RECONSTRUCTION.md)
executes the producer and all five mathematical dependencies, adding 5,542
instruction comparisons and 18,069 independent binary32 primitive checks.
The [integrated filter pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md) now joins
generation, staging and sample processing, with 1,698 comparisons and all 812
combined instructions visited. Static evidence identifies a reset divisor of
48000 and a guarded startup argument of 48077. The
[initializer and guarded startup](DSP_INITIALIZATION_RECONSTRUCTION.md) now
execute those paths through the recovered coefficient producer, adding 4,529
comparisons; platform service bodies and physical rate measurements remain open.
Separately,
the [capture slot loader](CAPTURE_LOADER_RECONSTRUCTION.md) adds 6,091 comparisons
for gain metadata, reuse and partial rollback. The [container installer/reader](CAPTURE_CONTAINER_RECONSTRUCTION.md)
adds 262 comparisons and the [journal/cache](CAPTURE_METADATA_RECONSTRUCTION.md)
adds 9,764. The [capture dispatch wrappers](CAPTURE_DISPATCH_RECONSTRUCTION.md)
add 1,847 comparisons through preparation, sizing, DSP setup and cleanup.
The separate [whole native parser](CAPTURE_PARSER_RECONSTRUCTION.md) adds 424
comparisons, and [memory reset](CAPTURE_RESET_RECONSTRUCTION.md) adds 253 through
direct and container-loading paths. Their complete integration with native audio
processing remains open. [Journal writes and readback](CAPTURE_JOURNAL_RECONSTRUCTION.md)
add 655 synthetic-storage comparisons. The
[complete metadata command](CAPTURE_COMMAND_RECONSTRUCTION.md) adds 1,114 through
text parsing, reload, retries and active gain updates; physical storage drivers
remain external. These modules do not yet form a complete firmware
replacement. Coverage is tracked in the [inventory](REVERSE_INVENTORY.md).

## Reconstructed functions

| Original CPU address | Exclusive endpoint | Implementation |
|---|---|---|
| `0x01C12608` | up to `0x01C126F4` | `hyperrig_dot_i16`: int32 activations, int16 weights |
| `0x01C126F4` | up to `0x01C127DE` | `hyperrig_dot_i32`: int32 activations and weights |
| `0x01C130B4` | up to `0x01C1318E` | `hyperrig_head3_process`: three-channel final convolution |
| `0x01C1453C` | up to `0x01C145FE` | `hyperrig_rechannel3_process`: mono/three-channel input and dry copy |
| `0x01C1318E` | up to `0x01C1349C` | 6-tap layer, zero residual shift |
| `0x01C1349C` | up to `0x01C13822` | 6-tap layer, nonzero residual shift |
| `0x01C13822` | up to `0x01C13D16` | 15-tap layer, zero residual shift |
| `0x01C13D16` | up to `0x01C14282` | 15-tap layer, nonzero residual shift |
| `0x01C14282` | up to `0x01C1452A` | generic layer; all five variants are covered by `hyperrig_layer3_process` |
| `0x02032586` | up to `0x02032618` | parser fragment for convolution-bias conversion/saturation |
| `0x020327DE` | up to `0x0203280C` | parser fragment for final-bias conversion |

Sources are in `firmware/src/`; public headers are in
`firmware/include/hyperrig/`. They are not derived from incomplete Ghidra
output: ABI, addressing, and operations are reconstructed from pi32v2 disassembly.

The original sample has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
Reset copies `0x2030C` bytes from CPU flash `0x02056780` to RAM `0x01C00000`.
Thus, RAM address `a` corresponds to offset `0x56780 + (a - 0x01C00000)` in
the decoded application area, or that offset minus `0x120` in extracted `app.bin`.

Both dot functions receive output, output stride, input, and input stride in
`r0..r3`; weights, tap count, sample count, and shift are on the stack. Strides
count int32 elements. Weights remain the same for every sample. The 64-bit
accumulator can overflow and wrap: C preserves this with unsigned arithmetic,
avoiding undefined signed overflow.

Within the non-overflow domain, right shift rounds to nearest with ties away
from zero; left shift preserves 64-bit wrapping. Int32 saturation follows.
Overflow cases are not replaced with an idealized mathematical formula. The C
wrapper accepts shifts `[-62, 62]` and nonnegative counts and strides; buffer
ranges and non-overlap are the caller's responsibility.

## Capture loading and biases

The later [native-layout parser](CAPTURE_PARSER_RECONSTRUCTION.md) reconstructs
the complete original function and its read64 helper, including allocation order
and partial error writes. The portable loader described in this section remains
unchanged; its guarantees and deliberate format limits are specific to that API.

`hyperrig_a2l_size` and `hyperrig_a2l_load` reconstruct the A2L1 format, weight
reordering, and scaling identified in parser `0x02031C64..0x0203291C`. They use
a portable HyperRig context, caller-supplied memory, and no dynamic allocation.
The capture can be freed after loading. CRC, sizes, end of file, and shifts
are checked before writing the context or arena. The size query includes up
to seven bytes for arena alignment.

Differences from the original parser are explicit: at most 64 layers and 15
taps per layer; an independent context and allocation layout; and preservation
of all raw convolution biases. The firmware specializes int32 conversion for
at most three channels; HyperRig also exposes it for other channels accepted
by the format, without claiming a complete native runtime for them. Allocators
and all optional G paths have not been reconstructed.

The original parser transforms convolution weights from `[out][in][tap]` to
`[tap][in][out]` (`0x020324EE`), appends mix weights, and transposes the head
from `[channel][tap]` to `[tap][channel]` (`0x02032764`). It keeps linear
weights and biases in their serialized order/scale. The C loader does the same.

Bias scaling uses `(bias + 2^(shift-1)) >>> shift`, with 64-bit wrapping;
zero shift leaves the value unchanged. Ties go toward positive infinity when
there is no overflow: `-3` shifted by 1 becomes `-1`, whereas dot returns `-2`.
Convolution biases then saturate to int32; the final bias remains int64. In
the firmware's embedded A2 capture, `172478924063` shifted by 16 becomes
`2631820`. This converted value is connected to the head kernel.

The observed original ABI stores final bias at context offsets 72/76, weights
at 68, and shift at 57. In 80-byte layer records, convolution shift is at 6,
reordered weights at 44, and the three int32 biases at 52/56/60. These offsets
describe original G: the HyperRig C API does not reuse its RAM pointers.

## Three-channel input stage

Setup function `0x01C129DC` invokes `0x01C1453C` with a 56-byte context. Each
mono sample is copied to the dry buffer and multiplied by three int16 weights.
The MAC starts at `2^(shift-1)`, applies an arithmetic shift, and saturates to
int32: rounding matches the biases, without dot's sign correction. Triplets
are written into the first layer's circular memory, with a copy of the first
64 frames beyond the ring boundary.

`hyperrig_a2l_rechannel3_init` connects the loaded weights and clears memory;
it checks that the ring contains the first layer's dilated history plus 64
frames. `hyperrig_rechannel3_process` handles blocks of 1 to 64 samples and
shifts 1–31, retaining position between calls. The ring need not be a power
of two; tests include the 69 frames needed by the A2 capture's first layer.

## Dilated layers, activation, and residuals

`hyperrig_layer3_process` reconstructs the combined operation of the five
original kernels. Setup function `0x01C12A54` passes a 200-byte context: tap
pointers at 0 through 56, residual sample at 60, linear biases with half an LSB
already added at 64/72/80, convolution weights at 88, dry at 92, sum at 96,
output at 100, linear weights at 104, convolution rounding/shift at 108/112,
convolution biases at 116/120/124, Q24 slope at 128, sum shift at 132, linear
shift at 140, residual shift at 144, and mix/conv difference at 148. Buffer
geometry and cursors follow. The verifier constructs this context; it does
not emulate the wrapper.

The convolution accumulator starts at half an LSB and includes dry input,
first arithmetically shifted by the difference between mix and convolution
shifts. After shifting, the low 32-bit word is used and bias is added with
wrapping: the firmware **does not saturate** here. Negative activation uses
Q24 slope and half an LSB, then again retains the low word. The contribution
to the final sum is shifted without rounding and added with 32-bit wrapping.
The linear pass accumulates in 64 bits, adds the rescaled residual, and only
then saturates to int32. C uses unsigned arithmetic to preserve these behaviors
without undefined signed overflow.

The original dispatcher selects different variants when residual shift is
zero: forcing the shifted variant in the zero case produces different results
for negative values. The verifier respects this contract and rejects the wrong
variant; it does not treat routines outside their domains as interchangeable.

The reconstructed path accepts 1–15 taps, positive dilation, convolution/mix/
linear/sum shifts of 1–31, a mix-conv difference of 0–31, and residual shifts
from -31 to 31. The original A2 capture satisfies all these constraints. Other
A2L profiles accepted by the parser may be rejected by the runtime: no
unverified numerical fallback is introduced.

## Three-channel final stage

Original setup function `0x01C12CC2` builds a 56-byte context and invokes
`0x01C130B4`. The routine writes each triplet into the circular buffer and
duplicates the first 64 frames beyond the ring's end. This allows contiguous
reading of the convolution window when it crosses the boundary.

The MAC starts at `2^(shift-1)-1`, adds the sign correction, applies an
arithmetic shift, and saturates to int32. It then adds the int64 bias already
converted by the native loader and saturates again. **That bias must not
automatically be equated with the raw value in the A2L1 file**:
`hyperrig_a2l_head3_init` now connects the value converted by the C loader.

The reconstructed API uses its own portable context. It supports 1–64 frames
per call, shifts 1–31, kernels of 1–65 frames, and a ring of at least 64 frames
and at least the kernel length. The observed actual context invokes 64-frame
blocks. The API neither reuses G RAM pointers nor accesses peripherals. A2L
integration uses a 64-frame ring plus 64 duplicated frames, totaling 384 int32
words. This stage's input is the sum of the layer results.

## Complete capture engine within the verified domain

`hyperrig_a2l3_size/init/reset/process` in `hyperrig_engine.h` connect the loader
and every stage without heap allocation during processing. Orchestration is
new and portable: it does not reproduce G's RTOS scheduler, allocator, double
buffers, or frontend. The model and its arena remain immutable; the runtime
uses a separate arena, initially zero history, and blocks of 1 to 64 samples.

Input is int32 in the capture's declared fractional format, and output is int32
in its output fractional format. For A2, these are Q30 and Q31. This excludes
codec conversion, gain adjustments, resampling, and IR/effects. Reset restores
all rings and cursors; changing block subdivision does not change the signal
or final state.

On a 64-bit PC, A2 requires approximately 115.4 KB for the runtime arena,
approximately 7 KB for the loaded model, and 1,128 bytes of context. These
measurements do not certify RAM or latency on the pedal: the target's complete
ABI and budgets remain to be checked.

## Building and comparing

Windows requires WSL Ubuntu with `gcc`, Python 3, and ASan/UBSan runtimes.
Artifacts and the ISA table are obtained through the bootstrap and analysis
described in the README. The JieLi toolchain remains in the local directory
ignored by Git; its URL, version `20260730.1`, and SHA-256 are pinned in the lock.

```powershell
python tools/bootstrap.py --toolchain
python tools/build_native.py
```

The build produces:

- `build/native/libhyperrig_dsp.so`: C executed on the PC with UBSan;
- `build/native/hyperrig_dsp.pi32v2.o`: relocatable ELF32 pi32v2 object,
  compiled with JieLi clang `-target pi32v2 -mcpu=r3`;
- `analysis/native/verification.json`: hashes and comparison results.
- `build/native/a2l_sanitize`: standalone loader memory-bound checks;
  its report is `analysis/native/a2l-sanitizers.json`.

The target compiler is used as a tool, without extracting its code. The object
still contains relocations and references to `memcpy`/`memset` that must be
resolved in the target runtime. It is not a flash image: an application linker
with MINI startup, IRQs, memory, and drivers is missing.

Verification compares host C with a limited interpreter that decodes and
executes **the original bytes of nine routines and two parser fragments**.
It does not emulate the entire original parser. It first checks the firmware
hash and that `app.bin` matches its decoded form. Unknown instructions are
not accepted; reads of uninitialized memory fail. The head's REP uses positive
counts; zero-count behavior is excluded. REP semantics are corroborated by the
[pi32v2-isa hardware account](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/hw/fm1-2026-10-24-v3/README.md).

Local result: **7,509 comparisons passed**: 629 per dot, 402 for the head,
367 for input, 1,146 per bias fragment, and 2,770 comparisons of biases and
both stages connected to loaded captures, 240 on the five layer kernels, and
180 kernel invocations in two complete capture engines. They cover signs,
ties, saturation, 64-bit wrapping, strides, circular windows, and consecutive
calls. Input and head comparisons also check memory and position. Fourteen
separate tests verify interpreters against hand-calculated results and compare
optimized variants within their respective domains.

For A2 (23 layers) and a synthetic network (3 layers), comparisons cover six
blocks each, 230 samples, final output, sum, all rings, and all cursors. The
oracle executes individual original-kernel instructions with a reconstructed
coordinator; it does not execute the complete stock audio process. Further C
tests on 7,001 samples per capture, beyond A2's 6,347-sample receptive field,
verify identical output and memory after reset and different subdivisions.
These are C continuity tests, not comparisons against emulated firmware.

The loader is compared with the Python decoder derived from the original
packer: 14 captures, eight alignments each, all weights and parameters checked.
It rejects 4,905 files with invalid CRC/structure, including every truncation
of the A2 capture with a recalculated CRC, and checks insufficient arenas and
untouched destinations on error. A separate C harness exercises 6,942 inputs
with exact allocations under AddressSanitizer and UndefinedBehaviorSanitizer,
including deterministic payload/header mutations, plus 400 blocks of the
complete A2 engine across eight arena alignments.

This verification still depends on the semantics implemented in the interpreter.
It does not execute the newly compiled target object on a real processor,
measure timing, or demonstrate whole-firmware equivalence. The versioned
report is [native-verification.json](../research/native-verification.json).

## Native capture orchestration

The following names are code interpretations, not original symbols:

| Address | Reconstructed/inferred role |
|---|---|
| `0x02031C64` | Complete parser reconstructed in [native parser](CAPTURE_PARSER_RECONSTRUCTION.md); full-path integration remains open |
| `0x01C12850` | Size wrapper reconstructed in [capture dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md) |
| `0x01C12878` | Complete [memory reset](CAPTURE_RESET_RECONSTRUCTION.md), including container adapters |
| `0x01C1296C` | Dot-callback installation reconstructed in [capture dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md) |
| `0x01C129DC` | specialized three-channel rechannel setup |
| `0x01C12A54` | layer-kernel setup/dispatch |
| `0x01C12C32` | layer iteration in 64-frame blocks |
| `0x01C12CC2` | head-context setup |
| `0x01C12D34` | probable processing-path wrapper |

Paths outside the verified domain, the audio frontend, IR and effects, and
scheduler integration with the MINI board remain to be reconstructed. The
existing Float64 reference helps verify mathematical structure but does not
replace this work.

## Jump-address correction

Relative pi32v2 destinations are calculated from **PC + actual instruction
length + displacement**. The first local disassembler always used PC+2:
annotations for 4/6-byte instructions were incorrect. It was corrected, listings
were regenerated, and three real encodings were added to tests, cross-checked
with the JieLi disassembler. Linear scanning still includes data: this does
not turn it into a complete, verified control-flow graph.
