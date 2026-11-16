# Reconstructed startup input and four-section sample path

The remaining input service in the recovered startup helper now executes its
original integer bodies. A new adapter connects it to the unchanged initializer
and dynamics configuration. The compared startup path therefore has no scripted
service calls. The sample processor for the initializer's separate four-section
filter bank also has compilable C, including transition copies, coefficient
steps, bypass histories and the signed Q16 gain-ramp kernel.

This is an offline instruction comparison. No device, firmware, physical sample
rate, timing or audio behavior was tested. The complete audio task and dynamics
sample processor remain outside this module. Previous sources, models, tested
images and completed reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre

The reconstruction retains the original project's
[PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md) and notice.
It is not original source code or a flashable firmware image.

## Executable scope and provenance

The pinned original M5.71 G v2 image has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The inherited loader verifies the original image and checks that its actual
unpacked application equals `analysis/firmware/m571_g_app/app.bin`. Flash address
`a` maps to decoded offset `a - 0x02000120`. RAM code maps through the reset copy
at CPU flash `0x02056780` for RAM `0x01c00000`.

| CPU range, end exclusive | Complete body | Instructions | Original bytes SHA-256 |
| --- | --- | ---: | --- |
| `0x01c01058..0x01c010a6` | Cached integer computation | 20 | `35697c33f7751116663146514c82bd21423b5fbaddf9c872b8325406e5570db1` |
| `0x01c010a6..0x01c010e4` | Startup input word | 20 | `a296f969e17ecae76ff7a977701140fb8ee0f50544ff41a63e0d342b23f5495b` |
| `0x01c053bc..0x01c05406` | Copy a pending four-section transition | 23 | `7489837c2b1807907dea1dbd0df4cd11ea175cea30723bf9e628e1dd9842dff7` |
| `0x01c05406..0x01c054a6` | Four-section block and gain ramp | 54 | `3cc067d4196bd0b456bc96fb426ef0e9bb7bd609cd96013eaa27826c45519e9f` |
| `0x01c054a6..0x01c0558c` | Guarded sample processing and transition steps | 72 | `09a291f5c5163bfe56afa583965fac0b6a531957158ee32ac5305d3d483b0aca` |
| `0x01c19d36..0x01c19ede` | Gain-ramp numerical kernel, including overflow tails | 146 | `2f4468f541d308d04987f2bc613e8a36b4325d423efc6b24cc29f6e2c3454d72` |

The reference model also executes the unchanged original rounded and residual
Q28 kernels at `0x01c15dec..0x01c15fdc` and `0x01c15fdc..0x01c16222`. Startup
executes the earlier initializer, dynamics configuration, coefficient producer
and their mathematical dependencies. Those calls are internal decoded code.
No idealized mathematical result, filter result or platform return is scripted.

Two separately hashed static call windows establish the surrounding relationship:

| Static window | Observed call | SHA-256 |
| --- | --- | --- |
| `0x01c02632..0x01c0263c` | Pass 128 samples to `0x01c054a6` | `602632b8d21ef0559e5d4a05cc2f7c2e10a3489e7acc2e854343a2372501e446` |
| `0x01c026da..0x01c026e4` | Pass 128 samples to the previously recovered five-section caller `0x01c051f0` | `1b11ec8dc5bba93678a9ba0425ad9c9840445886744c4cbeb33ed9fd17ec376f` |

These windows are static evidence only. Their enclosing task, its conditions and
the code between the two calls are not executed in this module. The verifier
sequences complete startup and processing entries on carried memory; it does
not invent a single native entry joining them.

## Runtime and API contract

The new `hyperrig_dsp_audio_path` embeds the unchanged
`hyperrig_dsp_initialization_runtime` and adds four mapped byte arrays. All eleven
regions total 13,292 bytes. The prior seven-region map is documented in
[DSP initialization](DSP_INITIALIZATION_RECONSTRUCTION.md).

| Added original RAM location | Bytes | Portable field |
| --- | ---: | --- |
| `0x01c1f1ac` | 12 | `platform`: source word, preserved neighbor word, subtractand |
| `0x01c26a88` | 8 | `cache`: cached source and computed word |
| `0x01c330e0` | 176 | `staged`: pending transition bytes |
| `0x01c33190` | 176 | `transition`: active transition bytes |

The four 44-byte filter sections remain at original `0x01c33030`; the gain word
remains at `0x01c1f7d4`. Control byte `+1` is the pending-copy flag, control word
`+32` is the remaining transition count, and bit zero of control byte `+28`
enables this processing caller. These are distinct from the recovered
[five-section chain](BIQUAD_CHAIN_RECONSTRUCTION.md).

All raw state words and transition bytes are accepted by the new cached/input,
update and sample-processing APIs. Samples are bounded to 0..128 signed int32
words, except the direct block API which requires 1..128. Sample storage and
runtime must be disjoint; output pointers must not alias runtime. Calls have no
external callbacks, re-entry or concurrent mutation. The verifier's mutations
occur between complete calls.

The direct native block can read `samples[-1]` when a section is bypassed and
the count is zero; some gain paths also execute division with that count. The
portable block API rejects zero before writing. Its enclosing native caller has
an explicit zero-count return, which is supported and compared independently.
The standalone gain kernel also supports zero, without accessing sample storage.

The startup adapter retains the earlier five signed parameter bounds
`-1280..1280` when its guard is zero. A nonzero guard returns without inspecting
those parameters or changing any state. Invalid host API calls return new `-1`
before writes. Other successful APIs return new zero status; the cached/input
APIs separately return the native result word through their output pointer.
Incidental native return registers are not exposed as invented API results.

## Cached startup input

The first helper compares the source word at `0x01c1f1ac` with its cached copy.
If equal, it returns the stored computed word without recomputation, even if that
word is arbitrary. Otherwise it performs the following original unsigned steps:

1. Multiply the uint32 source by 1,000,000 into 64 bits.
2. Divide by 6, shift left by 7, then divide by 48,077.
3. Take the low 32 bits, multiply by 97 with uint32 wrap, then divide by 100.
4. Store the computed word, then the source word, and return the computed word.

The wrapper subtracts the word at `0x01c1f1b4`, saturating at zero. When the
original computed word is at least 154,951, it also subtracts
`((computed * 50 + 0xff89c854) mod 2^32) / 100`, again saturating at zero.
All divisions here are unsigned and truncate. These operations and constants
do not establish physical units for the source, subtractand or result.

The wrapper includes a dependent parallel packet: the register receiving the
computed result is also the old base of the subtractand load. The interpreter
uses pre-packet register values for that load. Tests distinguish that behavior
from an incorrect sequential execution.

The new startup adapter supplies this real helper to the unchanged recovered
dynamics-startup adapter. Original startup sets its guard, obtains the word,
initializes with divisor 48,077, generates four filter sections, configures
dynamics and writes the original callback tokens. The instruction model follows
the corresponding original calls internally. Callback-token consumers and the
writers of the platform/cache inputs remain outside the executable scope.

## Four-section transition and sample behavior

Both transition arrays have this recovered layout:

| Byte offset | Meaning in these bodies |
| --- | --- |
| 0..79 | Four groups of five target coefficient words |
| 80..159 | Corresponding signed step bit patterns |
| 160 | Target gain word |
| 164 | Gain step word |
| 168..171 | Four target enable bytes |
| 172..175 | Transition count |

The update helper copies all 176 bytes into the active transition, ORs each
target enable byte into the corresponding current enable byte, copies the count
to control `+32`, and clears the pending flag. It preserves histories, residues,
residual-selection bytes and section padding.

The sample caller preserves all state and samples when the count is zero or the
enable bit is clear. Otherwise it performs a pending update first. If the
transition count is zero, it calls the four-section block once for the complete
buffer. A nonzero count selects chunks of at most 32 samples. Each chunk captures
the old gain before advancing the transition. Nonfinal steps add each stored
coefficient and gain increment with uint32 wrap. The final step copies exact
target coefficients, gain and enable bytes. After the count reaches zero, any
remaining chunks continue with the final state.

For each block, enabled sections execute the actual rounded or residual Q28
kernel according to their flag. Bypassed sections still update state: both first
histories receive the final sample, both second histories receive the preceding
sample, and residue becomes zero. For one sample, the previous first input
history supplies the missing preceding sample. This happens in section order,
before applying the block's gain.

When current and old gain are both 65,536, the block skips gain processing.
Otherwise it uses zero increment if they are equal, or the signed wrapped
difference divided by the positive block length, truncating towards zero. The
gain kernel increments before each multiplication. Each signed 32-by-32 product
is arithmetically shifted by 16, with no added rounding constant. Overflow clips
to positive or negative `INT32_MAX`; exactly representable `INT32_MIN` remains
`INT32_MIN`. The C avoids signed overflow and implementation-defined negative
right shifts.

## Independent verification and remaining boundaries

The new model subclasses the completed dynamics/initialization model, decodes the
six complete bodies from the pinned original bytes and adds the original Q28
kernel instructions. It retains original branches, unrolled gain loops, overflow
tails, saved-register footprints, parallel packets and native calls. Wide
multiply and division use the pinned ISA arithmetic semantics. The portable C
uses ordinary loops and the unchanged reconstructed Q28 implementation, providing
a separate implementation from the original instruction control flow.

Every comparison checks all eleven state regions and every sample word; the
cached/input operations additionally compare the returned word. The corpus covers
all gain-kernel lengths 0..128, signed sample/gain extremes, overflow paths,
wrapped platform arithmetic, cache reuse, all four-filter enable combinations,
both numerical kernels, single-sample bypass history, raw transition fields,
chunk boundaries, final-step copies, disabled and zero-length gates, guarded
startup, actual coefficient generation and repeated calls on carried state.

All 335 new instructions are visited. This is instruction coverage in the stated
domain, not exhaustive firmware input coverage or complete branch coverage.
The combined model also loads earlier helpers outside the called path, so its
remaining 77 unvisited instructions do not represent missing new bodies.

The parameter-request producer at `0x02028a34..0x02028b6c` is not recovered by
this module. Its later [transition reconstruction](DSP_TRANSITION_RECONSTRUCTION.md)
executes real requests and mathematical coefficient generation through this
unchanged sample processor. Transition records in this earlier module remain
deliberate fixture inputs. The surrounding
audio task, platform-input writers, peripheral behavior, dynamics sample kernel
at `0x01c1a636`, and execution of installed callback tokens remain separate work.
The earlier shared ISA/binary32 model assumptions remain in force; no processor
or audio measurement is added by these comparisons.

Run the standalone builder with a fresh directory:

```text
python tools/build_dsp_audio_path.py --output build/reverse-dsp-audio-path-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles a warning-clean UBSan host library, six freestanding pi32v2
r3 objects, the focused instruction tests and an exact-allocation ASan/UBSan
harness. It produces hashed comparison and build reports. Source manifests come
from maintained Python declarations; no previous ignored build report is needed.

MINI binding requires the exact reviewed v4 image SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
It verifies byte identity for all 30 loaded code regions, both coefficient tables,
the dynamics reset-copy bytes and both static caller windows. Static reset-copy
bytes do not establish later physical runtime values.

## Recorded validation

Final output is `build/reverse-dsp-audio-path-01`, an ignored build directory.

| Evidence | Result |
| --- | ---: |
| Original-instruction comparisons | 1,914 |
| Cached / input / startup / update comparisons | 224 / 210 / 100 / 24 |
| Ramp / block / process comparisons | 666 / 279 / 411 |
| New instructions visited / decoded | 335 / 335 |
| Combined loaded instructions visited / decoded | 1,184 / 1,261 |
| Sample inputs compared | 74,338 |
| Actual Q28 kernel calls | 1,869 |
| Internal gain-ramp / block calls | 500 / 473 |
| Internal startup input / dynamics calls | 52 / 52 |
| Complete coefficient-producer calls | 208 |
| Scripted service calls | 0 |
| Carried calls / between-call mutation cases | 385 / 20 |
| Maximum instruction packets in corpus | 13,474 |
| Focused instruction tests / invalid-API checks | 17 / 35 |
| ASan/UBSan exact-buffer cases, each including startup | 645 |
| Source hashes / generated artifact hashes | 51 / 10 |

The new pi32v2 object is 2,236 bytes.

| Output | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_dsp_audio_path.c` | `7963ffa4d863e09f4cec4ddeb51036eebe1270af7e43503ac5ad3f79e6b4e8d3` |
| `verification.json` | `bb4a07aea9212ffce5dd50b421217aa89065d07677b4d54abea324c7f81a77df` |
| `hyperrig_dsp_audio_path.pi32v2.o` | `d3f5976ffd0a9e2bb2f452bef9ffc9b8f39911c1191c8c94f1498473695dd895` |
| `sanitizers.json` | `eaa1d604566cebb4566a0269dd2e11e77666cec16517d5d672c474f37a145133` |
| `build-manifest.json` | `53057a3b7320d0afb66fb73836a00c8ecf54df6f707ed22da829136bde9de6e7` |

The deterministic compared output/state stream has SHA-256
`b96e413301c774eedcaab8fb36ad9f2dfc4f71093ada0ed17012a2051ab482a6`.
