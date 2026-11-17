# Effect resampling reconstruction

This milestone reconstructs both complete effect resampling wrappers and their
four optimized numerical kernels. The portable wrappers execute real recovered
arithmetic. All source samples, retained history, output bytes and surrounding
mapped storage are compared with the original decoded instructions. No device,
firmware image, physical sample rate or audio output was tested.

This is reconstructed UltraRig code, not the author's original source.

Required Notice: Copyright (c) 2026 Manuel Aguirre

License: <https://polyformproject.org/licenses/noncommercial/1.0.0>

See [the preserved license](../third_party/ultrarig/LICENSE.md) and
[required notice](../third_party/ultrarig/NOTICE.md).

## Original evidence

The original Alpha 11 v2 `m571_g_app.bin` SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The verifier checks this exact image and requires its unpacked application to
match the decoded input, whose SHA-256 is
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
The RAM load at flash `0x02056780` maps to original RAM `0x01c00000`.

All six complete regions contain **2,176 bytes and 612 instructions**. There
are no embedded data spans inside them.

| Body | Original range, end exclusive | Instructions | SHA-256 |
| --- | --- | ---: | --- |
| Upsampling wrapper | `0x01c07986..0x01c07a4c` | 65 | `22e878796cf14574f11d501421c7fe2e0ce91bb336faa6524bcbc9980d786951` |
| Downsampling wrapper | `0x01c08a76..0x01c08b34` | 55 | `3770f5d212c8e7c127fccdad036e094a4b341af94cc12eaa95fc773a857d164d` |
| Five-tap upsampling kernel | `0x01c1ae86..0x01c1b056` | 127 | `0e283306316383042c0e60ccc86e94509edaaffea00dda4e5974ca8b9131fbdf` |
| Five-tap downsampling kernel | `0x01c1b056..0x01c1b23a` | 132 | `55ff5f59cdecfd5496ad8e28aded5c46050a4f058ce9ddd12fa1b7b227acb28b` |
| Four-tap upsampling kernel | `0x01c1b23a..0x01c1b3d4` | 114 | `a57b514951de21229b949460e9a98767e64b0f9884c666390968833549346bb1` |
| Four-tap downsampling kernel | `0x01c1b3d4..0x01c1b582` | 119 | `70ff2759b5341ed48dab70a494e3d627c8b651d93fa36f8d2316a08372cd251c` |

The five static windows below form the contiguous **72-byte** data interval
`0x0203b768..0x0203b7b0`. They are data, not candidate instructions. The
wrapper loads at `0x01c07998/0x01c079a2` and
`0x01c08a86/0x01c08a90` establish their pointer/count use.

| Original range | Contents |
| --- | --- |
| `0x0203b768..0x0203b774` | Three coefficient pointers: `0x0203b780`, `0x0203b794`, `0x0203b7a0` |
| `0x0203b774..0x0203b780` | Tap counts: 5, 3, 4 |
| `0x0203b780..0x0203b794` | `670538396, -191090179, 82421978, -34042030, 11421924` |
| `0x0203b794..0x0203b7a0` | `642179087, -126556346, 21758483` |
| `0x0203b7a0..0x0203b7b0` | `665320397, -177530276, 65670763, -20310474` |

The five- and four-tap optimized kernels embed their coefficients as immediate
instructions. Their exact instruction bytes and corresponding scalar tables
are both bound by the report. MINI v4 is independently pinned to SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`;
all six regions and all five static windows must match that image.

## Native contract and arithmetic

Both wrappers receive source, output, count and selector in `r0..r3`.
Source points to the first current input word, after caller-owned history.
Count is measured on the lower-rate side: upsampling writes twice that many
signed 32-bit words; downsampling writes that many words from twice-rate input.
These are relative ratios, without a claim about the device's physical clocks.

For positive counts divisible by four, selector 2 selects the four-tap kernel;
every other selector selects the five-tap kernel. For other positive counts,
selectors 0, 1 and 2 select five, three and four taps. In particular, selector 1
changes its coefficients at the divisible-by-four boundary. The reconstruction
preserves this native behavior.

For `T` taps, upsampling needs `2*T-1` preceding source words and `count` current
words. Downsampling needs `4*T-2` preceding words and `2*count-1` current words.
These bodies leave all input and history bytes unchanged; history copying and
retention belong to the enclosing effect callers.

Upsampling forms each even output from two symmetric products per coefficient,
accumulated with wrapped 64-bit arithmetic. It then arithmetic-shifts by 30.
The odd output is the delayed source word without clipping, so `INT_MIN` can
survive that lane. Downsampling begins with a delayed word multiplied by
`2^30`, adds the symmetric products and arithmetic-shifts by 31. Neither path
adds a rounding constant. Overflow clips to `INT_MAX` or `-INT_MAX`, rather
than changing the original negative endpoint to `INT_MIN`.

The optimized bodies process four lower-rate samples per loop. Under disjoint
input/output storage, the portable implementation can use the same scalar
numerical loop without exposing their register scheduling. The comparison
model still executes every original unrolled instruction, prefetch and store.

## API and instruction model

[The C API](../firmware/include/hyperrig/hyperrig_effect_resampling.h) accepts
the original entry address and borrowed original-address buffers through the
existing audio-task map type. It uses no service callback or hidden state.
The mapper must be pure, stable and preserve address relationships. Storage is
accessed as bytes, permitting unaligned host backing for aligned original
tokens. Input/history, output and the IO object must be disjoint; overlapping
original spans, host aliases, invalid mappings and wrapping extents are rejected
before any sample write.

The new status values `-200`, `-201` and `-202` describe adapter failures, not
original return-register values. Raw optimized kernels require a positive
multiple of four. The native wrappers return immediately for negative signed
counts not divisible by four; those no-op executions are compared. Zero and
negative multiples of four enter an unguarded native loop, so the portable API
rejects them explicitly. There is no invented zero-count no-op.

The numerical domain admits every signed 32-bit sample pattern and positive
counts whose required spans are representable, mapped and disjoint. The corpus
exercises positive counts from 1 through 256, including nonmultiples of four;
it does not enumerate every larger valid buffer length.

[The instruction model](../tools/effect_resampling_machine.py) decodes the
original bytes and executes the complete bodies without numerical callbacks.
It preserves old register values across parallel packets, including the scalar
coefficient pointer stored while its source register changes. Callee-saved
registers and stack footprints are tracked; saved stack bytes themselves are
not materialized because these bodies never inspect them. Unknown instructions,
unmapped reads, escaping writes and unbalanced frames fail verification.

## Frozen validation

Final evidence is in ignored `build/reverse-effect-resampling-02/`:

- **1,563 C/original comparisons**, including all scalar selectors, all four
  kernels, positive and negative clipping in every unrolled lane, impulses at
  every tested history/current position, full-range random words and unaligned
  host backing.
- **72 consecutive carried-history calls** reuse the same C allocations and
  complete prior original memory. Source tokens advance through the same long
  stream; block counts alternate 31, 32, 7 and 8. Unwritten output bytes retain
  prior call state, and selector 1 crosses its coefficient-selection boundary.
- **526 actual optimized kernel calls** from the recovered wrappers, in
  addition to direct kernel cases. No numerical results are scripted.
- **2,471,317 original instruction steps**, reaching **612/612 instructions**.
  There are no unvisited instructions in these six regions.
- **15 focused instruction tests** and **17 C-only API/domain guard checks**.
- ASan/UBSan replays all **1,563 original-comparison fixtures** with exact
  allocation sizes and expected full memory, plus two invalid-API checks.
- The host library and **one pi32v2 object** compile with warnings as errors.
  The target object is 1,608 bytes and is not a flashable image.
- All **23 source bindings and six artifact bindings** were rechecked. The
  source manifest includes imported repository Python, the ISA TOML, explicit
  ISA semantic source files and recursive project C headers. It does not depend
  on a preceding ignored report to establish provenance.

| Evidence | SHA-256 |
| --- | --- |
| `verification.json` | `bdd750cd782b8332e44aadfaba25dd34aa3371f9c25b289c057301dff4b3d067` |
| `build-manifest.json` | `e5521e325b3dde32c44c34f166c9c643b248173527bcc2cdcfc733d7e276326d` |
| `hyperrig_effect_resampling.pi32v2.o` | `9e52f77b26c7d3bea435e25e3959570257b69cc33a2291064d84e0e1127e3fc0` |
| Complete state/output digest | `2a28488ded9d56a5d0b1341f8f2da2c2ccd799372d9e469f33f2bf99245d28e3` |

Snapshot 01 is preserved. It also passed, but its carried-history fixtures
slid windows at a fixed token. Snapshot 02 strengthens those cases to reuse
the full mapped memory and advance source tokens across calls. The C, header,
instruction model and pi32v2 object are unchanged between snapshots.

Independent read-only integration review checked selector dispatch, exact
history/current spans, wrapped arithmetic, saturation, pass-through `INT_MIN`
and the borrowed map contract. No in-domain mismatch was found. Disjointness
is necessary because the native optimized read/write order is otherwise
observable when input and output overlap.

The enclosing effect dispatcher, individual/grouped wrappers and their
history-copy orchestration are separate work. This module supplies their real
resampling dependency without claiming that those enclosing paths executed in
this corpus.

To reproduce, provide the preserved MINI image and choose a new ignored folder:

```text
python -B tools/build_effect_resampling.py --output build/reverse-effect-resampling-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```
