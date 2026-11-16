# IR runtime convolution reconstruction

This milestone recovers the complete original 128-sample integer convolution
runtime and its numerical dependencies. Real constructor output is processed by
the recovered software FFT, frequency-history ring, complex multiply/accumulate,
inverse transform, output scaling and wet/dry gain code. The accelerator control
bodies also execute, but accelerator samples and register responses are explicit
synthetic inputs. No device, firmware image, USB stream or audio was tested.

This is reconstructed UltraRig code, not the author's original source.

Required Notice: Copyright (c) 2026 Manuel Aguirre

License: <https://polyformproject.org/licenses/noncommercial/1.0.0>

See [the preserved license](../third_party/ultrarig/LICENSE.md),
[the required notice](../third_party/ultrarig/NOTICE.md) and the preceding
[IR construction reconstruction](IR_CONVOLUTION_RECONSTRUCTION.md).

## Original evidence and function boundaries

The pinned original image is `m571_g_app.bin` from the Alpha 11 v2 archive:

`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`

The inherited loader verifies that original image and its entire decoded
`app.bin`. RAM instructions use the original flash load at `0x02056780`, mapped
to RAM `0x01c00000`. The following 16 complete bodies contain 7,480 bytes and
2,266 instructions. None contains embedded data.

| Function | Original range, end exclusive | Instructions |
| --- | --- | ---: |
| Wet/dry gain ramp | `0x01c11faa..0x01c12064` | 61 |
| Complete IR processing | `0x01c12064..0x01c123fa` | 304 |
| Accelerator wait and acknowledge | `0x01c1245c..0x01c124a8` | 26 |
| Accelerator descriptor and launch | `0x01c124a8..0x01c12556` | 58 |
| Input history and first radix stage | `0x01c145fe..0x01c1477e` | 119 |
| Integer complex FFT of 64 samples | `0x01c1477e..0x01c1508c` | 657 |
| Two-half FFT merge | `0x01c1508c..0x01c15148` | 51 |
| Real forward transform packing | `0x01c15148..0x01c1533e` | 150 |
| Cyclic partition convolution | `0x01c1533e..0x01c154a4` | 118 |
| Real inverse transform preparation | `0x01c154a4..0x01c15a42` | 444 |
| Inverse merge and output scaling | `0x01c15a42..0x01c15bc8` | 105 |
| Fixed-point wet/dry mix | `0x01c15bc8..0x01c15c8c` | 66 |
| Accelerator input history | `0x01c15c8c..0x01c15cf2` | 27 |
| Accelerator frequency packing | `0x01c15cf2..0x01c15d3a` | 22 |
| Accelerator accumulator scaling | `0x01c15d3a..0x01c15d7e` | 28 |
| Accelerator output scaling | `0x01c15d7e..0x01c15dec` | 30 |

Two adjacent tables occupy exactly `0x0203be50..0x0203be90`: eight command words
followed by eight size-index words. Their combined SHA-256 is
`29d78b7fdaf7dc950d337ff76fa49dcd4651295036bfafffc375d883ffc748d3`.
The launch body loads the indices at `0x01c124d2` and commands at `0x01c1251a`.
These 64 bytes are data, not candidate instructions. The report records both
word arrays and the byte binding under `accelerator_tables`.

The MINI v4 input is independently pinned to
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier compares all 36 declared runtime and inherited construction regions,
the preceding 36-byte resampling table and these 64 accelerator-table bytes.
Every transitive body actually visited by this corpus must belong to that bound
set; the verifier rejects an executed body omitted from it.

## Constructor connection and runtime state

The native ABI takes the object in `r0`, writable audio in `r1`, sample count in
`r2`, raw binary32 wet gain in `r3` and raw binary32 dry gain on the stack. A null
object, count other than 128 or inactive object returns without processing.

The original constructor sets the active word at object offset 0 to 1. The
software corpus does not add an activation write. Its fixture sets the global
selector at `0x01c1fa14` to zero before executing the actual constructor, which
copies that choice into object offset 548. The synthetic accelerator corpus
explicitly changes offset 548 to 1 after construction. Input audio and the
accelerator's output buffers are also deliberate fixture inputs.

This is direct constructor-to-runtime numerical integration. The comparison
does not execute installation, effect publication or the enclosing audio-task
callback that selects and schedules the IR object. Those callers remain
separate from this milestone even where an earlier reconstruction exists.

For `P` partitions, define `H = 2616 + 2064*P`. The recovered layout is:

| Object offset | Meaning |
| --- | --- |
| `0, 4, 8, 12, 16` | Active, partition count, cyclic index, alternating input half, coefficient exponent |
| `20` | Coefficients at object `+2616` |
| `24` | Frequency history at object `+2616+1032*P` |
| `28` | 129 complex signed64 accumulators at object `+552` |
| `32, 36` | FFT work at `+H`, canonical permutation at `+H+1024` |
| `40, 44` | Fixed-point phase tables at `+H+1536`, `+H+2048` |
| `48, 52` | Time history at `+H+3080`, wet output at `+H+4104` |
| `56..535` | Twenty groups of three complex FFT phase pairs |
| `536, 540, 544, 548` | Previous wet gain, previous dry gain, ramp-valid flag, accelerator selector |

The full constructor allocation is `7248 + 2064*P` bytes, with `1 <= P <= 32`.
The API requires the exact pointer relationships above, an exponent at most 48,
an in-range cyclic index, an input-half index of 0 or 1 and the canonical
permutation. The constructor leaves the previous gain words unchanged but clears
the ramp-valid flag; their old values cannot trigger the first block's ramp.

The software path combines the previous and current 128-sample halves, executes
two 64-point complex FFTs and a merge, then stores 129 complex bins. Bin-major
storage interleaves all `P` partitions. Convolution visits history beginning at
the current cyclic slot and wraps once, while coefficient partitions advance
linearly. The cyclic slot decrements modulo `P` after each block. The inverse
path and overlap output produce the next 128 samples.

## Integer and gain semantics

All sample buffers contain raw signed32 little-endian words. The reconstruction
uses explicit unsigned wrapping, signed interpretation and arithmetic shifts;
host overflow behavior is not used to approximate the original processor.

- Input is shifted right by two and limited symmetrically to `2^25 - 1` before
  it enters software history. The accelerator input has its separate rounded
  shift and `2^18 - 1` symmetric limit.
- Complex phase multiplication takes the high word of the wrapped signed64
  sum or difference. It is not replaced by a floating-point FFT.
- The cyclic complex sum wraps modulo `2^64`. The original high-word magnitude
  reduction, optional low-word pass and resulting accumulator shift execute.
- Native multiply loops prefetch a final unused complex pair. Direct comparison
  buffers therefore include eight readable padding bytes. Their values do not
  enter the sum; the constructor's complete object also contains those reads.
- Accumulator rounding preserves the original shift/add/shift order, including
  ties toward positive infinity and wrapped intermediate words. Final shifts
  clamp to `-31..30` before output scaling.
- Saturation is symmetric: `[-2147483647, 2147483647]`. Exact `INT32_MIN` is
  clamped to `-INT32_MAX`, including the wet/dry mixing path.
- Gain ramps accumulate wrapped integer deltas over 128 samples and use signed
  division toward zero. The final sample reaches the new gain for ordinary
  bounded gains. Raw-word comparisons also exercise wrapped extreme deltas.

Binary32 gains use the unchanged pinned float semantic model and the previously
reconstructed C math helpers. The branch at `0x01c122ce` has two THEN instructions
and one ELSE instruction: gains greater than unity are divided by the maximum,
while the maximum is retained for later output scaling. The ELSE alone sets the
maximum to unity. This distinction preserves the separate final gain loop.
NaNs, infinities, signed zero, saturation and raw conversion behavior are kept
as instruction semantics; they are not replaced with host float assumptions.

## Accelerator boundary and recovery

The public interface never casts a peripheral address to a host pointer. A
synchronous callback receives a read, write or sync operation. The only register
addresses are `0x01ee0400` and `0x01ee0404`.

The 16-byte globals at `0x01c34490` hold recovery, launch and timeout counters,
then busy status. The 16-byte descriptor at `0x01c339d0` holds command, source,
destination and a cleared reserved word. Supported sizes are 256, 512, 1024 and
2048; the IR runtime requests 256.

Launch drains an existing busy operation, acknowledges it, publishes the new
descriptor, syncs, clears the control register, writes the descriptor address,
marks busy, increments the launch counter and writes control value 257. A
previous operation's timeout does not prevent this new launch. Wait polls at
most 200,001 times, increments the timeout counter if none was ready, then reads
once more for the acknowledge read/modify/write, syncs and clears busy. Counters
wrap as unsigned words. The full timeout loop executes in the comparison.

A failed forward or inverse wait disables acceleration on the object, clears
its frequency and time histories, resets both history indices and increments
the recovery counter. It leaves that block's audio unchanged. The next compared
block runs the actual software path using that carried recovery state.

At accelerator launch the fixture writes explicitly synthetic transform data
into the declared destination. This validates packing, subsequent arithmetic,
buffer ownership and callback order. It does not validate the accelerator's
FFT arithmetic, DMA, interrupts, execution timing or actual register behavior.

Synchronous callbacks may change data buffers, globals and descriptor words.
Object structural fields, permutation/phase tables, view and IO must remain
stable. Post-MMIO structural checks reject an invalid mapping before further
indexed access; these are API domain guards, not support for arbitrary
relocation or a promise of rollback. Runtime, object, audio, IO and parameter
storage are disjoint. Concurrency and asynchronous mutation are outside scope.

## Direct numerical comparison interface

`hyperrig_ir_processing_kernel` is a research adapter. Arguments are four raw
words and buffers are four pointer/capacity pairs. `MULTIPLY` returns its shift
through the result pointer; every other operation leaves that result unchanged.
Unlisted buffers and argument words are ignored.

| Operation | Buffers and minimum sizes in bytes | Arguments |
| --- | --- | --- |
| `INPUT` | Audio 512; new history 512; old history 512; work 1536 | None; first 32 permutation words must be canonical |
| `FFT64` | Data 512; phases 480 | Skip first radix stage: 0 or 1 |
| `MERGE` | Data 1024; phases 512 | None |
| `FORWARD` | Input 1024; frequency `1032*P`; phases 1032 | `P`, current slot |
| `MULTIPLY` | Frequency `1032*P+8`; coefficients `1032*P+8`; accumulator 2064 | `P`, current slot |
| `INVERSE` | Accumulator 2064; work 1536; phases 1032 | Shift `0..63`; all 128 permutation words canonical |
| `OUTPUT` | Work 1024; output 512; phases 512 | Signed shift `-31..30` |
| `MIX` | Wet 512; output 512; dry 512 or null | Low16 wet gain, high16 dry gain |
| `CROSSFADE` | Output 512; wet 512; dry 512 | Old wet, old dry, new wet, new dry |
| `HARDWARE_INPUT` | History 1024; audio 512 | None |
| `HARDWARE_FORWARD` | Input 1032; frequency `1032*P` | `P`, current slot |
| `HARDWARE_SCALE` | Accumulator 2064, shrunk in place to 1032 | Shift `0..63` |
| `HARDWARE_OUTPUT` | Input 512; output 512 | Signed shift `-31..30` |

For partitioned kernels, `1 <= P <= 32` and the current slot is less than `P`.
Buffers are distinct except that the complete `MIX` or `CROSSFADE` output span
may equal either complete input span. Partial overlap is outside the contract.
Those alias preconditions are caller requirements, not runtime overlap checks.
The buffer descriptor, argument array and result word occupy separate storage,
disjoint from every accessed buffer and from each other.

## Reproduction and validation

Run from the repository root with the pinned input, decoded analysis and local
toolchains available. Select a fresh output directory:

```powershell
python -B tools/build_ir_processing.py --output build/reverse-ir-processing-NEW --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The build uses an explicit maintained source manifest. It does not load earlier
ignored verification reports. Previous C files, models, verifiers and completed
reports remain unchanged. The new instruction model decodes the original
functions and executes their control flow, predication, parallel packets,
positive repeat loops, arithmetic, memory effects and internal calls. It does
not obtain expected results from the reconstructed C.

The final evidence is stored in `build/reverse-ir-processing-01/`. Host and
pi32v2 builds use strict warnings. The host comparison library also uses UBSan.
The 23 focused tests independently check FFT impulses, cyclic complex products,
64-bit wrap, prefetch padding, symmetric limits, rounding, gain-ramp endpoints,
zero-IR dry behavior, no-op entries, register descriptors and the exact timeout
read limit.

ASan/UBSan exact-buffer validation passed 64 real constructions, 1,376 software
blocks, 256 synthetic accelerator blocks, 128 timeout recoveries and 17 direct
numerical cases. Both original coefficient producers construct objects for all
partition counts from 1 through 32. Each software sequence crosses its cyclic
history boundary; accelerator recovery is followed by actual software execution.

The verifier compares all 30 mapped storage regions, semantic return values and
every ordered MMIO boundary with a complete-state digest. Fixtures include zero,
signed extrema, random words, full-span aliases, all supported transform sizes,
counter and descriptor mutations, both transform timeout positions and carried
gain/history state. It records all unvisited inherited paths separately; no
whole-firmware completion percentage is inferred from loaded instruction count.

The final run passed 399 original-instruction comparisons and 9,303,863 executed
instruction steps. It includes four actual constructor calls, 84 runtime calls,
77 carried-state calls, 18 cases with scripted MMIO mutations and four complete
timeout cases. The ordered register trace contains 800,300 events. All 2,266 new
instructions were visited. Joined coverage is 2,869 of 3,182 declared runtime
and construction instructions; all loaded coverage is 2,869 of 4,708. The
remaining 313 declared instructions belong to inherited construction and
preparation paths, not omitted runtime bodies. Their exact addresses remain in
the report. Invalid API checks passed 118 cases, with three additional guards
for forbidden structural changes at MMIO boundaries.

All 66 recorded source hashes and 15 artifact hashes match. The 59 inherited
source inputs and all ten inherited pi32v2 objects match the preceding frozen
construction evidence. The new target object is 10,260 bytes, SHA-256
`6cc11645eb1daeafb22b52d78b1337ccdbcd7446ca91997dfb3b1e5fe51b97eb`.

Final report SHA-256:
`c396513e475ddc38dc5b486b682fc4c466ee403e7a67e7234aa6f7538e365532`

Build manifest SHA-256:
`279275a2b51a5b973c6ac3e87f51778d729546a8533b1eb5e35c102df0d3c240`

An independent numerical review checked cyclic MAC/prefetch behavior, 64-bit
wrapping, processor-status saturation, decoded gain predication and MMIO
operation order. A separate API review checked constructor-layout and buffer
guards. Neither reported a remaining blocker. These were code reviews and
offline comparisons, not hardware or audio validation.

This component is a research reconstruction and produces no flashable firmware.
The next integration boundary is the actual effect/audio caller that owns and
schedules this object, together with measured peripheral and audio behavior.
