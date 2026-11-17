# IR lifecycle and numerical construction join

This checkpoint joins previously recovered original bodies; it adds no new
original function or data discovery. Original notices, images and earlier
reconstruction sources and reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

See [the preserved license](../third_party/ultrarig/LICENSE.md).

## Public API and exact closure

`hyperrig_ir_effect_numerical_execute(entry, arguments[12], result[2], io)` uses
the existing lifecycle IO: a stable byte mapper, synchronous twelve-word service
callback, opaque context and finite service/work budgets. The original result
is separate from the portable status. Public entry argument order remains the
nine entries in [the lifecycle reconstruction](IR_EFFECT_LIFECYCLE_RECONSTRUCTION.md),
with two additions:

- `0x0202962a`: original effect address, mode.
- `0x020318a8`: original object address, raw count, producer token, producer argument.

The mechanically checked lifecycle derivative substitutes only direct calls
at `0x02029744`, `0x02029762` and `0x02031c10`, plus API names, declarations and
the two new entry cases. The service function is unchanged; coincident indirect
tokens remain external. All numerical code shares the same access object and
budgets. The native model shares original registers, stack, conditional packet
state and public bytes, without typed-runtime conversion.

The closure comprises 35 existing regions and 1,453 decoded instructions:

| Existing body | Start | End exclusive |
| --- | --- | --- |
| lifecycle_mode_prepare | `0x02029728` | `0x0202976a` |
| lifecycle_temporary | `0x0202976a` | `0x0202983a` |
| lifecycle_select_source | `0x0202983a` | `0x020298ce` |
| lifecycle_refresh | `0x020298ce` | `0x02029920` |
| lifecycle_assign | `0x02029920` | `0x02029ae6` |
| lifecycle_assign_direct | `0x02029ae6` | `0x02029afc` |
| lifecycle_owns | `0x02029afc` | `0x02029b2e` |
| lifecycle_construct_copy | `0x02031bf8` | `0x02031c16` |
| lifecycle_relocate | `0x02031c16` | `0x02031c64` |
| mode_callback | `0x01c05ec6` | `0x01c05ed6` |
| clamp | `0x01c05eb0` | `0x01c05ec6` |
| trim | `0x020294ce` | `0x0202957e` |
| counter | `0x01c05160` | `0x01c0516e` |
| scaled_exp | `0x01c0516e` | `0x01c05182` |
| exp | `0x020285d4` | `0x02028646` |
| size | `0x01c123fa` | `0x01c12414` |
| reset | `0x01c12414` | `0x01c12446` |
| prepare | `0x0202962a` | `0x02029728` |
| sample | `0x020313dc` | `0x02031404` |
| resample | `0x02031404` | `0x02031542` |
| produce | `0x02031542` | `0x020315b8` |
| copy | `0x020315b8` | `0x020315c8` |
| cosine | `0x020315c8` | `0x02031626` |
| sine | `0x02031626` | `0x0203167a` |
| phase | `0x0203167a` | `0x020316f4` |
| fft128 | `0x020316f4` | `0x020317c8` |
| real256 | `0x020317c8` | `0x0203187c` |
| q31 | `0x0203187c` | `0x020318a8` |
| construct | `0x020318a8` | `0x02031bf8` |
| window_cosine | `0x02028646` | `0x02028676` |
| budget | `0x02029248` | `0x02029268` |
| convert | `0x02029268` | `0x0202928a` |
| limit | `0x0202928a` | `0x020292ee` |
| effective | `0x020292ee` | `0x0202930e` |
| raw_length | `0x02029604` | `0x0202962a` |

## Constructor-derived FFT disjointness proof

Let `B` be the object token and `P = min(((raw_count + 127) mod 2^32) >> 7, 32)`.
Zero raw count exits before construction; nonzero raw counts can still yield
`P=0`. Let `H=2616+2064*P`. The constructor's private permutation occupies 128
private bytes and remains inaccessible to public callbacks. For each partition
`i` with `0 <= i < P`, the real-FFT call receives these half-open offsets from B:

| Span | Offsets | Bytes |
| --- | --- | --- |
| Real input | `[552,1576)` | 1024 |
| Output spectrum | `[2616+1032*P+1032*i, 2616+1032*P+1032*(i+1))` | 1032 |
| Complex scratch | `[H,H+1024)` | 1024 |
| Real phase table | `[H+2048,H+3080)` | 1032 |
| Complex phase table | `[H+4104,H+4616)` | 512 |

For P>=1, the first spectrum starts at or above 3648. The last spectrum ends
exactly at H. Scratch ends at H+1024, before the real table; the real table ends
at H+3080, before the complex table. Thus these five spans are pairwise disjoint.
For P=0 no producer or real-FFT call occurs. The maximum total offset is 73296,
far below 2^32; adding any B modulo 2^32 preserves disjointness even when a span
wraps. Individual word accesses still must fit their mapped bytes.

The adapter gathers the three input spans needed by the unchanged recovered
real256/fft128 routines into disjoint private arrays, runs those routines, then
scatters scratch followed by output. The real routine writes every scratch and
output word before return. There are no service callbacks or concurrent
observers inside this operation. Constructor call arguments are cached native
locals, not pointers reread from a callback-mutable header. Consequently this
preserves complete successful public state even when object bytes overlap
source or control bytes, or the logical object wraps across address zero.
No arbitrary mapping/work-failure prefix inside the staged call is claimed.

## Domains and boundaries

Source count retains the original signed comparison at `0x020313f0`: a count
with its high bit set does not admit a nonnegative sample index. There is no
4,076-sample source bound. The original constructor limits partitions to 32;
it does not reject raw counts above 4096. Counts `0xffffff81..0xffffffff` yield
zero partitions, while the separate allocation-size helper still has a
minimum-one-partition allocation. These are explicit native arithmetic cases.

Preparation receives an actual effect address. The original signed quotient
for its status address is retained rather than imposing a slot-index bound.
It reads lengths before allocation, reloads fade inputs afterward, executes
the actual constructor, reloads the old object pointer and frees it when applicable, then
publishes the new object fields in original order. A zero-mode successful
allocation is freed and produces the original failure result.

Sample, producer and reset reads use the shared native byte map at their
original points. The window producer reads mode before resampling and length
and fade afterward. Reset reads its time-history pointer after clearing
frequency history. Original source/object/control overlaps, callback mutations,
unaligned host storage and per-access address wrap are retained. Only the
already excluded private stack and ordinary API/mapping/lifetime requirements
remain. Math is reused from the frozen recovered integer binary32, phase, Q31,
length and FFT implementations; no host libm result or coefficient fixture
replaces original execution.

Original instructions and static input data remain immutable, including the
36-byte resampling coefficient table at `0x0203be2c..0x0203be50`. Source reads
may overlap those bytes, but writable object/control storage may not replace
them. This preserves the original table while allowing arbitrary overlaps
among writable source, object and control regions.

At constructor site `0x02031a00`, WINDOW `0x02031542` and COPY `0x020315b8`
execute recovered code. Other targets stay explicit four-word services with
`(producer argument, output, start, count)`. Mode, allocation, reading and free
callbacks remain external by original site, including numeric token collisions.
The existing 36-byte resampling coefficient table is bound as prior evidence;
no new exclusion or original function count is requested.

Guard statuses are portable and nonresumable. Complete successful results are
compared. Mapping, private-stack and work failures around staged FFT work are
C-only checks. This join declares no native-prefix comparison; the earlier
lifecycle observations remain separate evidence. This is offline evidence;
no allocator implementation,
physical storage, scheduling, runtime convolution, MMIO or audio is tested.

## Validation

The comparison corpus exercises raw counts beyond 4096, signed high-bit
source counts, wrapped count-plus-127 partition arithmetic, zero partitions,
allocation failure followed by the real mode-zero retry, forward-copy aliases,
source/header/control overlaps, wrapped object addresses and unaligned host
backing. Callback witnesses change source count, source pointer, format, gain,
old-object ownership, release callback and constructor header fields. Numeric
callback collisions remain external at their original sites. Three nine-call
sequences retain actual mapped allocations and public state across assignment,
ownership, relocation, failure and replacement operations.

Independent review found a missing mode-zero retry substitution in the first
draft. The new derivative and its mechanical proof were corrected together,
and allocation-failure/fallback witnesses execute that actual constructor
path. Subsequent review found no in-domain mismatch in preparation,
construction, resampling, windowing, reset or the FFT interval proof. The
immutable input-table contract was then made explicit in both the public
header and this document. Frozen lifecycle and numerical sources were not
changed.

The builder captures source hashes before its first compiler invocation and
checks them against the comparison report. Its maintained source manifest
includes dynamic ISA semantics, the ISA TOML, imported models, recursively
included C headers and the unchanged lifecycle derivative input. No earlier
ignored verification report is required to construct the source manifest.
All comparisons are serialized from original execution and replayed under
AddressSanitizer and UndefinedBehaviorSanitizer, including complete mapped
state hashes before and after callbacks and retained-allocation transitions.

The frozen result is `build/reverse-ir-effect-numerical-02/verification.json`.
It passed 128 original/C comparisons over 8,485,371 original instruction
steps, 14 focused tests, nine C-only API/mapping/work guards and 128 complete
ASan/UBSan replays. Fifteen cases mutate public memory through callbacks.
The 104 allocation groups comprise 101 independent cases and three nine-call
sequences, retaining 24 calls after their initial allocation. The sanitizer
also checks invalid API entry; it claims no native guard-prefix replay.

The joined corpus visited 1,418 of its 1,453 loaded instructions: 507/537 in
the lifecycle and its earlier helpers, and 911/916 in the numerical closure.
All 35 unvisited addresses remain listed per body and in `unvisited_all`.
They are inherited paths, including lifecycle failure alternatives, length
branches and phase/constructor alternatives; this report does not present
them as executed or automatically import earlier coverage. It declares no
new original functions, instructions or data exclusions. These corpus counts
are not a firmware completion percentage.

All 1,453 instruction windows and the existing 36-byte resampling table match
the pinned MINI image. The table SHA-256 is
`5e4544bfe9c57a8a3dc7f9db243232a0362dca09497be8503c418e379879165c`.
A separate final file audit matched all 82 source hashes and 19 artifact
hashes. Host and pi32v2 builds passed; the new pi32v2 object is 9,380 bytes.
All 12 inherited target objects equal their earlier frozen objects. All 13
target objects also equal candidate 01, which passed the same corpus before
the public-header contract clarification. Candidate 01 remains preserved.

- Verification SHA-256:
  `3b032c2821356276b29771b825e72ea74aabefd045fd46b61a8aae264728aeb3`.
- Build manifest SHA-256:
  `0f26a47a2abecfd1a9f85ad21ec38fb4c46c8471acdb19094057d2b7d53e71d4`.

With the preserved ignored inputs and toolchains available, reproduce into a
fresh output directory using:

```text
python tools/build_ir_effect_numerical.py --output build/reverse-ir-effect-numerical-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```
