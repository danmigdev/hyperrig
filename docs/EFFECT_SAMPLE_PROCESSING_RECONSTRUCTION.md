# Complete sample engines and their original callers

This offline milestone reconstructs seven complete original bodies used by the
existing dispatcher. It adds no effect, backport, firmware image or hardware
claim. Types are identified by their original numeric values; these results do
not assign product or marketed model names to them.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

See [the preserved license](../third_party/ultrarig/LICENSE.md).

## Exact scope

All endpoints are exclusive. The seven bodies contain 4,082 original bytes and
1,324 decoded instructions, with no embedded data inside their boundaries.

| Entry | End | Original role | Incoming argument words |
| --- | --- | --- | --- |
| `01c08b3e` | `01c08c76` | Q28 section cascade | Samples, count, coefficients, coefficient stride, histories, residues, sections, enabled mask, residual mask |
| `01c0b5d6` | `01c0ba14` | Correlation-driven state transition | Effect token |
| `01c0ba14` | `01c0bbce` | Gain/width mixer | First buffer, second buffer, count, initial gain, gain step, two mix coefficients, mode |
| `01c0bbce` | `01c0bd8c` | Width coefficient polynomial | Width, mode, first output token, second output token |
| `01c0bd8c` | `01c0be92` | Correlation accumulation update | Effect token |
| `01c18f90` | `01c19448` | Ring interpolation and crossfade | Token for the 68-byte descriptor |
| `01c19448` | `01c1958e` | Paired correlation accumulation | Token for the 56-byte descriptor |

The only calls inside these bodies are the cascade's existing Q28 kernels at
`01c08c22` and `01c08c38`, and the updater's correlation call at `01c0be30`.
The C cascade uses the already recovered Q28 implementation. Every other new
sample calculation is reconstructed directly in C with explicit wrapped
integer arithmetic and the recovered binary32 operations.

The frozen processing caller is a mechanically checked derivative of SHA-256
`f4e475acc0f797673740ac0428811d3b83129b4356878606484c1b54c81421b2`.
Nine textual replacements cover exactly these ten original direct calls:

| Original caller PCs | Real callee |
| --- | --- |
| `01c0e6a2`, `01c0e706` | `01c08b3e` |
| `01c0f2e2`, `01c0f37c` | `01c18f90` |
| `01c0f3ae` | `01c0b5d6` |
| `01c0f45c`, `01c0f4f4` | `01c0ba14` |
| `01c0f480`, `01c0f492` | `01c0bbce` |
| `01c0f630` | `01c0bd8c` |

Other differences are the new IO/work-budget plumbing, entry dispatch, public
symbol names and publishing the portable result only after success. The
verifier checks this derivative before compilation and again in the report.
Numeric callback tokens do not select new internal callees. Existing clock
target guards remain; a focused native-model test also retains the zero-word
clock ABI when its token collides with a loaded numerical entry.

## Public state and count semantics

The new API uses borrowed original-address byte maps. Unaligned host backing,
overlapping native sample/state views and wrapped address increments are
supported. Each individual reached access must fit its mapped span. Original
instructions and ROM data remain immutable. Different original bytes may not
acquire additional host aliases. The original private stack
`30000000..30001020` is excluded from ordinary public storage; temporary
descriptors supplied by the real caller use its private borrowed map.

Raw helpers have no fixture-sized sample limit. The unchanged dispatcher and
other reused typed interfaces retain their documented bounds. A finite shared
work budget stops pathological raw walks after preceding C writes. Guard
results are portable API checks, not original firmware error returns, native
fault-prefix comparisons or resumable observations.

- The cascade reads the final source sample even when count is zero. With
  zero sections it still publishes a history pair. Its masks select bit
  `section & 31`; coefficient stride is a raw word count.
- The mixer returns for zero count. It advances its gain at each group of
  four samples, including the first partial group. Buffer aliasing preserves
  the original read and two-output store order.
- The raw ring consumes sixteen samples per descriptor block. Its block
  decrement is modulo 32 bits, so zero is a very long walk. The dispatcher
  supplies the rounded-up block count, including partial final blocks.
- Correlation consumes two samples per decrement. Zero requests a very long
  walk; odd counts never reach zero. The initial ring index is raw, while
  subsequent indices use the original 8 KiB mask.
- Width is not clamped to 0..100. The polynomial uses the original unsigned
  64-bit products and wrapped intermediate values. Its output tokens may alias.

The tests keep native long-walk observations distinct from C-only budget
checks. They do not make the original model stop according to C access counts.

## Q28 alias preservation

The original cascade builds a private section and calls a kernel that caches
all five coefficients, the four histories and the initial residue. The new C
adapter loads them into one private `hyperrig_biquad_q28` object once per whole
native call. It processes one private sample at a time with the recovered
kernel, retaining that same private object across all samples.

Each source sample is read immediately before its calculation, and its output
is stored immediately afterward. Both original kernels store the current
sample before reading the next. No public coefficient, history or residue is
reread or published between samples. After the entire call, the wrapper
publishes residue and history at the original final sites and in their original
order. The next section then loads its public inputs afresh.

Consequently, output may overwrite the current section's coefficients without
changing its later samples; future sections see those writes. Future samples
may overlap public history or residue without seeing premature state stores.
The corpus covers these cases, combined overlaps, disabled sections, mask-bit
wrap and source-pointer wrap. The adapter imposes no new public disjointness
restriction to reuse the typed kernel.

## Constructor and caller integration

`hyperrig_effect_sample_processing_prepare` executes the existing complete
constructor `0202cf62` for types 25, 36 and 37. The original instruction model
executes the corresponding real builders and coefficient producers. Their
actual output bytes feed the new sample bodies through the existing dispatcher,
individual/grouped wrappers, stage and audio task.

Initial sample/history bytes, existing ownership tokens and routing state are
fixtures. Generated coefficients are not substituted. Parameter changes run
the real constructor again while retaining prior stream state and allocations.
Preparation is a separate synchronous invocation; this does not claim a newly
recovered scheduler or resource-allocation edge. Preparation between audio
observations transfers public bytes while preserving the suspended original
task's registers, stack, return frames and conditional-packet state.

The constructor retains its existing finite-math and work-budget domains from
[model construction](EFFECT_MODEL_CONSTRUCTION_RECONSTRUCTION.md). No new
arbitrary sample ceiling is introduced by this join. Type 29's different
enclosing wrapper and other unjoined numerical leaves remain outside this
milestone.

## Authenticated table and raw ROM reads

The only newly classified data is `0203b7e0..0203b880`: two twenty-word weight
blocks, exactly 160 bytes, SHA-256
`1e8b8aa3482ac62ae54fcaf6b4dd11b104b34129c7308ad7cae9114f4e9c7cd8`.
The second block reverses the first.

The dispatcher loads the iteration byte at `01c0f626`, rejects values above
one at `01c0f62a` and calls the updater at `01c0f630`. The updater reloads that
byte at `01c0bd94`, multiplies it by 80 at `01c0bdf8`, and loads the original
base at `01c0bdfe`. The parallel packet at `01c0be1c..01c0be26` preserves a
twenty-sample count independently of the mode byte.

The raw updater API retains the full byte index. Cases for indices 2 and 255
authenticate their exact additional original ROM reads separately. These
auxiliary byte bindings do not enlarge the weight-table classification or
declare additional functions. The final report checks the MINI image against
new and inherited instruction windows, declared static windows and these
additional reached ROM bytes.

## Unvisited transition paths

Twenty instructions in five blocks remain unvisited through the complete
entry. They are retained as decoded code, with the following invariant proofs;
they are not counted as executed.

1. Energy bypass `01c0b718..01c0b728` contains six instructions. The preceding
   test `01c0b668..01c0b698` accepts the direct signed32 conversion exactly when
   `T = (V + 0x7fffffff) mod 2^64 <= 0xfffffffe`. The slow path therefore has
   unsigned magnitude at least `0x80000000`. The exact magnitude calculation at
   `01c0b6aa..01c0b6bc` and carry comparison at `01c0b6c2..01c0b6ce` cannot take
   the smaller-magnitude bypass.
2. Difference bypass `01c0b800..01c0b816` contains eight instructions. Its
   corresponding range test is `01c0b760..01c0b77a`, magnitude formation is
   `01c0b78c..01c0b79e`, and comparison is `01c0b7a2..01c0b7ae`. The same
   unsigned64 argument applies, including negative values.
3. Curvature bypass `01c0b8ea..01c0b8f6` contains four instructions. The range
   test is `01c0b85a..01c0b878`, magnitude formation `01c0b884..01c0b896`, and
   comparison `01c0b89a..01c0b8a6`. Wrapped arithmetic, including the magnitude
   of `INT64_MIN`, does not create a smaller magnitude on this slow path.
4. Sign flip `01c0b744` requires negative energy. The entry's signed64
   subtraction and `N xor V` test at `01c0b63e..01c0b65a` already require energy
   at least positive `0x40000000` or `0x400000`. Its cached high word remains
   unchanged through the sign test at `01c0b740`.
5. Store-source assignment `01c0ba0c` requires a zero candidate. That candidate
   becomes positive floating zero at `01c0b9c2`. Division at `01c0b9ca` and
   multiplication at `01c0b9ce` then yield infinity or NaN. The pinned comparison
   semantics in `upstream/pi32v2-isa/tools/hwtest/semantics/s.py`, function
   `convert`, map nonfinite `ftoi` inputs to `INTMAX` or `INTMIN` according to
   the sign bit. This is explicitly a bound of the comparison model, not a new
   physical FPU measurement. Adding
   `0x0a000000` modulo 32 bits exceeds `0x14000000` in both cases, so the unsigned
   acceptance test at `01c0b9da` returns before the zero-candidate branch.

Focused witnesses cover the reachable normalization paths at one, sixteen and
other shift counts, negative differences, boundary saturation and lower-bound
toggle. The new instruction model explicitly preserves carry and PSR for
hex-immediate subtraction consumed by these normalization comparisons; it does
not modify any frozen earlier model.

## Evidence and review

The implementation and instruction model received an independent read-only
review of the cascade cache, sample/publication order, ring descriptor reloads,
paired correlation arithmetic, mixer, updater, width polynomial and transition normalization.
The reviewer found no remaining mismatch in those inspected areas.
An independent review also confirmed all five unvisited-path invariants and
matched the pinned conversion-semantics and instruction-table hashes. Explicit
full-entry witnesses exercise the zero candidate, nonfinite conversion and
rejecting phase gate while leaving the downstream zero-candidate block unvisited.

The frozen evidence directory is
`build/reverse-effect-sample-processing-01`. Its fresh build passed:

- 768 independent original/C comparisons and 1,928,099 original instructions
  executed, including 148 real constructor invocations.
- 432 retained allocation chains and 336 subsequent calls on their retained
  storage, with callback order and public state compared.
- 1,304 of 1,324 new instructions visited. The twenty instructions above remain
  unvisited under their independently reviewed invariants; there are no
  unclassified new gaps. All ten direct dispatcher join sites execute.
- 4,469 of 22,919 loaded instructions visited in this corpus. The larger loaded
  closure includes existing constructor, stage, audio and numerical bodies;
  its 18,450 unvisited instructions are listed, not borrowed from old coverage.
- Fifteen focused native tests, twenty separately labeled C-only API/mapping/
  budget checks, and 768 exact ASan/UBSan replays with retained allocations and
  before/after public-state hashes at scripted services.
- Strict host compilation and 41 pi32v2 objects. The new joined module's target
  object is 36,688 bytes.
- MINI byte identity for all 22,919 instruction windows, 49 static windows and
  the two auxiliary raw-updater windows `0203b880..0203b8d0` and
  `02040790..020407e0`.

The [verification report](../build/reverse-effect-sample-processing-01/verification.json)
has SHA-256
`ee7486a6df065262f121e9c05527dc7ab237af64f7af290af959a02aaac3afa3`.
The [artifact manifest](../build/reverse-effect-sample-processing-01/build-manifest.json)
has SHA-256
`6bb7c58f5a9a2519d7ae7a32810f54990eee57841e38b920c2be558b49711ef2`.
All 162 source bindings and 47 artifact bindings were independently rehashed
after the build. These ignored local artifacts and input images stay out of Git.
All forty reused pi32v2 objects also match their previously frozen counterparts.
The raw index-2 witness overlaps the existing selector-table classification
at `0203b880..0203b8d4`; that earlier role is preserved. The index-255 witness
remains unclassified. Neither witness enlarges the correlation-weight table.

The [builder](../tools/build_effect_sample_processing.py) captures source files
before its first compiler call, verifies the same bindings after original/C
comparisons and sanitizer replay, and records complete artifact hashes. Its
source manifest includes recursive C headers, the decoded instruction model,
dynamically loaded ISA semantics and TOML. It requires the pinned local images,
but no ignored prior verification report. Reproduction must use a fresh output
directory; completed evidence is never overwritten.

```powershell
python -B tools/build_effect_sample_processing.py --output build/reverse-effect-sample-processing-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

All validation is offline. No hardware, audio, USB or firmware installation
test was performed for this milestone.
