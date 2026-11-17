# Stage scheduling and branch mixing reconstruction

This module reconstructs the complete stage entry at `0x01c10e06`, its immediate
branch routing helpers, and the original fixed-point mixer. It uses the existing
Q28 filter implementations and joins the unchanged audio task to the recovered
stage body. Individual and grouped effect execution remain explicit services.
This is an offline reconstruction and comparison, not a hardware or audio test.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
See [the preserved license](../third_party/ultrarig/LICENSE.md). The C is a new
reconstruction from the original instructions, not the original source code.

## Complete original bodies

All endpoints are exclusive. The report records the exact decoded bytes,
instruction counts and unvisited addresses for each body.

| Body | Start | End | Responsibility |
| --- | --- | --- | --- |
| Capability | `0x01c0558c` | `0x01c055a8` | Select two-bit capability field |
| Active-state selector | `0x01c055d2` | `0x01c05618` | Type-specific stored-parameter test |
| Route mask | `0x01c05618` | `0x01c05860` | Forward/backward branch eligibility |
| Optional clock | `0x01c10818` | `0x01c1082c` | Reload and invoke clock token |
| Stereo preparation | `0x01c1082c` | `0x01c10968` | Retain alternate samples/filter history |
| Five-word exchange | `0x01c10968` | `0x01c10984` | Swap filter history/coefficient words |
| Branch filters | `0x01c10984` | `0x01c10a4a` | Execute four actual Q28 sections |
| Branch preparation | `0x01c10a4a` | `0x01c10b58` | Advance coefficient transitions and release tail state |
| Ramped mix | `0x01c10b58` | `0x01c10cac` | Four interpolation segments |
| Mix selection | `0x01c10cac` | `0x01c10cdc` | Select ramped or fixed mix |
| Stereo completion | `0x01c10cdc` | `0x01c10de8` | Borrow descriptor and restore three pointer fields |
| Clear filter history | `0x01c10de8` | `0x01c10e06` | Clear history/residue of four sections |
| Stage | `0x01c10e06` | `0x01c11b00` | Automation, routing, branch latency and crossfades |
| IR delay query | `0x01c11f66` | `0x01c11f76` | Return 34 for a nonnull inactive object |
| Word copy | `0x01c1a14c` | `0x01c1a182` | Copy with four-word prefetch |
| Two-span mixer | `0x01c1a182` | `0x01c1a2c4` | Wrapped signed MAC, Q15 shift and saturation |

The new C uses named operations and state fields. Its numerical loops and
scheduling logic are independent from the Python oracle, which decodes and
executes the original instructions. Conditional packets use their encoded
THEN/ELSE counts, and both halves of a parallel packet read the prior register
state. Original-address comments identify the main stage control-flow joins.

## State and numerical behavior

The control block begins at `0x01c32db0`. Sixteen effect slots begin at
`0x01c2c220`, with a 480-byte stride. The stage route lists are control `+348`
and `+358`, each with a maximum of ten slot indices, and counts at `+14/+15`.
Stage one also consumes the supplemental list at `+88`, counted by byte `+8`.
The caller supplies stage 0 or 1, the sample address token and the frame count.
The recovered audio task supplies 128 frames at both original call sites,
`0x01c02420` and `0x01c026d4`.

Only stage zero advances the eight automation records at `0x01c2e5a0`, stride
448. Each has up to forty parameter descriptors, target words and cached
deltas. Integer addition wraps at 32 bits. Floating addition/subtraction uses
the already recovered binary32 operations, including their rounding and NaN
behavior. The two ratio modes retain the original 64-bit unsigned division and
signed-maximum clamp; no host floating-point arithmetic substitutes for them.

Each stage can own three branch groups. Two delay slots track branch latency
differences, capped at 127 samples. Their buffer indices and rolling histories
remain in the original mapped RAM. Grouping uses the original masks
`0x001fe0c1` and `0x6f03`; subsequent effects must share the branch and satisfy
the original mode/type conditions. Group eligibility, delay cost, actual
service execution and processed counters are separate operations.

The branch filters execute the original rounded/residual Q28 kernels through
their frozen C implementations. The two-span mixer accumulates signed products
modulo 2^64 and shifts by 15. Positive overflow clips to `INT32_MAX`; negative
overflow clips to `-INT32_MAX`. An exactly representable `INT32_MIN` survives.
The native pair prefetch and four-word copy prefetch are preserved, including
their observable behavior when source and destination sample ranges overlap.
The final Q16 crossfades wrap their arithmetic and do not introduce a new clip.

The 40-byte capability table at `0x0203b480..0x0203b4a8` has SHA-256
`ad42fb64992b7995f180484ba717298b55c46909537d0e9a01ee333cf4662362`.
Its direct consumers are the complete capability and active-state bodies above.
Only these exact forty bytes are authenticated as this table. No larger ROM
range is inferred to be data, and no embedded tables occur in the sixteen
declared new function bodies.

## Callback contracts and the actual effect boundary

The standalone stage has exactly three external targets:

| Target | Arguments | Meaning |
| --- | --- | --- |
| `0x01c04862` | none | Clock service |
| `0x01c0f678` | slot index, sample token, frame count | Individual effect wrapper |
| `0x01c10446` | route-byte-list token, effect count, sample token, frame count | Grouped effect wrapper |

These arities were checked against the original callee bodies. The individual
wrapper preserves the slot at `0x01c0f67c`, forms `slot*480` at `0x01c0f67e`,
preserves the frame count/sample token at `0x01c0f690/692`, and reads the sample
tail through those saved arguments at `0x01c0f802..0x01c0f818`. The grouped
wrapper preserves its list/count in the register pair at `0x01c1044a`, reads
the first byte at `0x01c1044c`, and saves frame count/sample token at
`0x01c10450/452`. Neither wrapper loads incoming stack arguments beyond its
saved-register and local frame. These contracts are not inferred only from
the call sites or the shared test service dictionary.

The clock pointer at `0x01c34198` must be zero or `0x01c04862` at every read.
Callbacks can synchronously modify mapped state and samples within the declared
domain. The stage revalidates route/type/index bounds after each callback;
invalid changes return a new guard error with prior effects retained.

For the direct stereo-completion helper, a mapped mix descriptor is reloaded
after the first clock call. Only its destination, first-source and second-source
pointer fields are temporarily changed and restored. Changes made by the second
clock callback survive. This was independently reviewed and is covered by
mutation witnesses. Direct mix descriptors must be disjoint from sample writes;
source and destination sample ranges may overlap with the documented original
prefetch ordering. Distinct address ranges must represent distinct host storage.

The joined adapter replaces the frozen audio task's stage service with the
actual new C body. The Python adapter executes the original stage at the same
call sites, sharing registers, call frames and address-state bytes with the
frozen audio-task interpreter. Observation/resume state is compared at the
original waits and queue boundaries. Other audio-task services retain their
explicit synthetic contracts. This integration does not claim those remaining
services' arithmetic has been recovered.

## IR caller evidence and next boundary

The actual IR numerical call is `0x01c0e334 -> 0x01c12064`. It lies in the larger
effect dispatcher `0x01c0deb6..0x01c0f678`, reached beneath the individual wrapper
`0x01c0f678..0x01c10446` and grouped wrapper `0x01c10446..0x01c10818`.
The dispatcher uses a 39-entry halfword branch table at
`0x01c0e0a8..0x01c0e0f6`. The type-7 entry is `0x013a`, selecting
`0x01c0e31c`. That path reads the convolution object at effect `+288`, wet gain
at `+296` and dry gain at `+300`, then passes them to the recovered IR runtime.
The packet at `0x01c0e32e/330` replaces the sample argument while storing the
prior dry-gain word as the fifth argument.

Construction preparation at `0x0202962a` is already recovered separately.
Its next enclosing ownership wrapper is `0x02029728..0x0202976a`, which calls
`0x01c05ec6(1)`, chooses a mode from `0x01c1f7d0`, retries preparation with zero
mode after status `-3` while that global remains nonzero, and calls
`0x01c05ec6(0)` before returning. The temporary-source wrapper starting
`0x0202976a` is also outside this milestone.

These dispatcher and ownership observations define the next coherent IR
integration boundary. They are static trace evidence, not executed or newly
inventoried function/table coverage. No synthetic effect output is presented
as a recovered IR result, and this milestone does not connect installation to
effect publication through those still-unrecovered wrappers.

## Reproduction and evidence

The maintained entry points are `tools/build_dsp_stage.py`,
`tools/verify_dsp_stage.py` and `tests/test_dsp_stage_machine.py`. The builder
requires a fresh output directory under ignored `build/`. It builds a host
UBSan library and all pi32v2 objects, runs the focused tests, compares original
instructions, and replays the complete standalone comparison inputs and
expected mapped outputs under ASan/UBSan. The binary replay is generated evidence
and remains outside Git. The standalone source manifest does not require any
prior ignored verification report.

Every loaded original instruction window, including transitive audio/filter
dependencies, and all referenced static tables are bound to the pinned original
and MINI-v4 bytes. The final report records exact source hashes, and the build
manifest binds the library, objects, tests, sanitizer replay, sanitizer results
and comparison report. No firmware image is changed or generated by this build.

The frozen snapshot is `build/reverse-dsp-stage-02`:

- **806 comparisons**, comprising 782 standalone stage/helper comparisons and
  24 audio-task observation/resume segments. The joined original task enters
  the actual stage eight times.
- **2,085,441 original instruction steps**, 96 cases with callback mutation,
  24 carried stage calls, and 1,436 standalone entries into the real Q28 kernels.
- **1,996 of 2,003 instructions** in the sixteen declared bodies are reached.
  The seven unvisited addresses are `0x01c11530`, `0x01c11532`, `0x01c11536`,
  `0x01c11538`, `0x01c1153a`, `0x01c1172e` and `0x01c11730`. They are the two
  empty-group fallback paths: the valid route scan starts with one selected
  effect and produces a group length of at least one; the callee-saved length
  remains positive. These instructions are explicitly unvisited, not added to
  the executed count.
- The combined corpus reaches **2,828 of 7,553 loaded instructions**. This is
  the union of this corpus's stage and inherited task/filter paths. Coverage
  from previous reports is not added, and no overall reverse-engineering
  completion percentage is inferred.
- **14 focused instruction tests** and **35 C API/domain guard checks** pass.
  ASan/UBSan replays all **782 complete standalone original comparisons**,
  including their exact expected mapped memory, plus five invalid-API checks.
  The 24 joined task segments run in the host UBSan library.
- The host library and **25 pi32v2 objects** build with warnings as errors.
  All 24 inherited audio-task objects are byte-identical to their prior build.
  The new stage object is **11,992 bytes** and is not a flashable image.
- All **126 source hashes and 31 artifact hashes** have been rechecked. The
  source manifest includes dynamically loaded ISA `r.py`, `s.py`, `b2.py`,
  `_r_util.py`, the ISA TOML, imported repository Python modules and recursive
  project C headers.
- The original/MINI comparison binds **all 7,553 decoded instruction windows
  and eight static-data windows**, including the exact new capability table.

| Frozen evidence | SHA-256 |
| --- | --- |
| `verification.json` | `b061f17e1ff186a7a30b216aec488a0f0a1946fce7c858eee7b87e1dbf9d5111` |
| `build-manifest.json` | `7e1d02483cb1a99ebe276039ad5d42e3a9d23f855b40bc42425c29b0348c3861` |
| `hyperrig_dsp_stage.pi32v2.o` | `e32dc753d53d06708b6baeec77f1af080c5b5a9e1af87b49704371324f135fe0` |
| Ordered state/output/service digest | `c857bc7b7b878853dcfcb7c0f6de4765a081e5b35c3d218afeb812795b74cb9d` |

The earlier `reverse-dsp-stage-01` snapshot remains unchanged. Its numerical
comparisons and sanitizer replay passed, but its source manifest omitted the
dynamically loaded `r.py` file. Snapshot 02 corrects that provenance boundary
with explicit dynamic-module and recursive-header discovery. All 25 target
objects and the complete replay input/output artifact are identical between
the two builds; the numerical C and instruction model did not change.

Independent read-only review checked sample prefetch order, saturation, stereo
pointer restoration, crossfades and history rotation. Its descriptor-reload and
struct-member-access findings were fixed before snapshot 01; mutation witnesses
remain in snapshot 02. The public descriptor contract preserves permitted clock
mutations rather than concealing them with an eager state copy.

To reproduce, supply the preserved MINI image and choose a new ignored output
directory:

```text
python -B tools/build_dsp_stage.py --output build/reverse-dsp-stage-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```
