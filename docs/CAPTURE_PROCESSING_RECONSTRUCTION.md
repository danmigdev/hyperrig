# Native capture block processing reconstruction

This milestone recovers the original M5.71 capture runtime wrappers and executes
their numerical callees in the instruction model. It replaces another bounded
part of the native execution path with compilable C. It does not establish a
complete firmware build, audio quality, real-time performance or execution on
the MINI.

The C implementation is
[`hyperrig_capture_processing.c`](../firmware/src/hyperrig_capture_processing.c),
with its mapped-address contract in
[`hyperrig_capture_processing.h`](../firmware/include/hyperrig/hyperrig_capture_processing.h).
All original artifacts and earlier numerical sources remain unchanged. Required
UltraRig notices and the [third-party license](../third_party/ultrarig/LICENSE.md)
remain applicable.

## Recovered native bodies

Addresses below are CPU addresses; ends are exclusive.

| Entry | Start | End | Decoded instructions | Behavior |
| --- | --- | --- | ---: | --- |
| Rechannel setup | `0x01c129dc` | `0x01c12a54` | 42 | Constructs input expansion parameters and invokes the three-channel kernel |
| Layer setup | `0x01c12a54` | `0x01c12c32` | 162 | Builds tap pointers, biases, shifts and output geometry, then selects a numerical kernel |
| Layer iteration | `0x01c12c32` | `0x01c12cc2` | 56 | Processes a bounded layer interval, including the last layer's one-frame output ring |
| Head setup | `0x01c12cc2` | `0x01c12d34` | 40 | Constructs the head convolution parameters |
| Block processing | `0x01c12d34` | `0x01c12f20` | 156 | Expands input, evaluates layers and head, and advances the native sample position |
| Zero helper | `0x01c1452a` | `0x01c1453c` | 9 | Clears a word count rounded down to a multiple of four |

These six regions occupy 1,366 bytes. Four bytes at
`0x01c12bf2..0x01c12bf6` are the table `02 1a 0e 14`, not instructions.
The decoder excludes those bytes. Layer kinds 1, 2, 3 and 4 select
`0x01c1318e`, `0x01c1349c`, `0x01c13822` and `0x01c13d16`; other values use
`0x01c14282`. Specialized kinds must match their tap count and residual shift
within the C adapter's domain.

The instruction model also executes the complete original rechannel kernel at
`0x01c1453c`, head kernel at `0x01c130b4`, and all five previously reconstructed
layer kernels. These are reused regions and must not be counted as newly
recovered functions. The C adapter reuses the existing rechannel, head and
saturation code. Its new raw layer adapter preserves the native parameter
buffer cursors and supports the one-frame final output ring. The older portable
layer API and its ring-size restrictions remain unchanged.

## Context and state behavior

The context is the parser's 228-byte object. The main shared fields are:

| Context offset | Meaning used by these bodies |
| ---: | --- |
| 3 | Head kernel frame count |
| 8 | Unsigned 16-bit layer count |
| 56, 57 | Signed rechannel and head shifts |
| 60 | Three signed 16-bit rechannel weights |
| 68 | Head weight address |
| 72, 76 | Already converted 64-bit head bias |
| 80, 84 | Head history address and position mask |
| 88 | Native sample position |
| 92 | Layer descriptor table, with an 80-byte stride |

Each layer descriptor supplies its tap count, dilation, shifts, coefficients,
converted biases, kernel kind and history. History address and length are at
descriptor offsets 68 and 76. The wrapper reconstructs earlier tap addresses
by subtracting dilation and wrapping through that history.

The native fixed buffers are preserved as address tokens:

| Buffer | Address | Bytes used |
| --- | --- | ---: |
| Accumulated three-channel block | `0x01c33a00` | 768 |
| Rechannel parameters | `0x01c33d00` | 56 |
| Layer parameters, selector 0 | `0x01c33d38` | 200 |
| Layer parameters, selector 1 | `0x01c33e00` | 200 |
| Last layer output and mirror, selector 0 | `0x01c33f10` | 24 |
| Last layer output and mirror, selector 1 | `0x01c33f28` | 24 |
| Head parameters | `0x01c33f40` | 56 |
| Dry mono block | `0x01c33f78` | 256 |
| Bypass counter | `0x01c344b0` | 4 |

A loaded capture processes complete 64-frame blocks and leaves any remainder
untouched. Fewer than 64 frames leave its output and position unchanged. After
each completed block, context offset 88 increases by 64 with 32-bit wrap.

An unloaded capture copies all requested mono samples forward and increments
the bypass counter, even for a zero-length request. The original forward-copy
behavior is retained for overlapping bypass input and output. Loaded processing
requires disjoint logical buffers under the header's ownership contract.

Layer index zero clears `floor(frames * 3 / 4) * 4` words of the sum. The normal
64-frame path clears all 192 words. The smaller direct-call cases preserve the
original truncated tail. The bounded zero helper accepts 4 through 1,023 words;
zero-count REP and larger register-count REP behavior remain outside this work.

## Verification and limits

Final evidence is in the ignored directory
`build/reverse-capture-processing-03`. Earlier development and build reports
remain unchanged. The final builder passed:

- 230 C versus original-instruction comparisons: 11 rechannel, 83 layer,
  29 iteration, 25 head, 70 block processing and 12 zero-helper cases.
- 323 actual numerical kernel calls. Seven additional cases use explicitly
  scripted numerical boundaries to isolate dispatch parameter construction;
  those cases are counted separately and do not demonstrate numerical execution.
- 3,450,873 decoded instruction steps, covering 464 of 465 new instructions
  and 2,000 of 2,001 instructions across the new and reused regions.
- 17 focused tests for packet ordering, table data, selector parity, ring
  mirroring, bypass overlap, position wrap and partial-block behavior.
- 19 invalid-API, 13 missing-mapping and 23 numerical-domain guard checks.
- Host compilation with undefined-behavior checks, pi32v2 object compilation,
  and 189 exact-buffer cases under AddressSanitizer and UndefinedBehaviorSanitizer.

The single unvisited instruction is the redundant process-loop fall-through
jump at `0x01c12f1e`. The final layer index branches to the head path at
`0x01c12ee8` before reaching that instruction. The loop count is preserved by
the callee ABI. The report lists this gap explicitly; it does not claim full
instruction coverage.

Comparisons include complete mapped context, arena and scratch contents, plus
numerical-call targets, parameter addresses and their entry snapshots. They
cover all five layer kernels, the one-frame output ring, positive and negative
residual shifts through the supported extremes, saturation, wrapped positions,
multiple blocks, output remainders and counter wrap. Internal C memory-store
ordering is not asserted to match every numerical instruction. Mapping is
required to be pure and stable, and concurrent access is outside the contract.

The supported numerical shapes remain bounded: three channels, 1 through 15
layer taps, shifts 1 through 31, residual shifts -31 through 31, and head kernels
up to 65 frames. Layer index zero requires at least two frames because its zero
helper must receive a positive REP count. Head and layer output ring byte
counts cannot exceed `INT32_MAX`; focused guard cases reject larger synthetic
blocks. This limit avoids claiming equivalence for the original signed-index
behavior beyond the reused head implementation's reviewed domain.

The raw numerical entry requires an unchanged wrapper-constructed parameter
block, including dependent tap-end, shift and mirror fields. It is not an API
for arbitrary parameter-buffer mutations. The optional numerical callback may
observe or implement that boundary; with a null callback, the C adapter runs
the reconstructed arithmetic. It must preserve the context, descriptors,
coefficients and unrelated memory.

The original wrappers return void. The C APIs add status 0 for completion,
`-200` for invalid API pointers, `-201` for missing mapping, and `-202` for an
unsupported numerical domain. These guards are new behavior. Writes made
before a later failure may remain; the APIs do not promise rollback.

The separate [warm-up body](CAPTURE_WARMUP_RECONSTRUCTION.md) at
`0x01c12f20..0x01c13072` now has its own reconstruction and comparison report.
Platform scheduling, audio-device integration and real-time behavior remain
outside this milestone.
This evidence does not turn the previously portable engine orchestration into
an assertion that the whole original engine has executed.

## Provenance and reproduction

The original application SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The loader checks that artifact and its decoded extraction before execution.
All 13 new and reused regions are byte-identical in the reviewed MINI v4 image,
whose required whole-image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

The final report binds 25 source inputs, and the build manifest binds eight
generated artifacts. All bindings were checked after completion.

| Final item | SHA-256 |
| --- | --- |
| `verification.json` | `f2d0676d730cb98c84595c10bde7ab4b3cd108b333d185fcd9bb1f176b0c8fd5` |
| `build-manifest.json` | `f35433a27f1125a0f66401bbc70fcde050034d9b7a44d6dcc1ec738e2f208b4b` |
| Processing C source | `131a0a08f487b03a3205d3687500e16c8f189902a1b34fc22bac5761e739f4fe` |
| Processing pi32v2 object, 6,768 bytes | `a9e530487ac66ae49c7802f2902abbb0c49a6196919d596150c26f05ffd2becc` |

Run the builder from the repository root with an unused output directory:

```powershell
python -B tools/build_capture_processing.py --output build/reverse-capture-processing-check --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

On Windows this uses the configured Ubuntu WSL distribution. The original
decoded application and reviewed MINI image are local ignored inputs. The
builder produces host and target objects, comparison evidence and sanitizer
results; it does not access a device or produce a flashable release.

The later [live capture integration](CAPTURE_LIVE_RECONSTRUCTION.md) carries
actual parser/loader output through warm-up and this processor. Its separate
numerical adapter handles the parser's head rings below 64 frames, preserving
the smaller native mirror allocation. This module's earlier source, numerical
domain and report remain unchanged.
