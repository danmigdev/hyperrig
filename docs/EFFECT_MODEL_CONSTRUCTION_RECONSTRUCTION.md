# Effect model construction reconstruction

This offline reconstruction closes the six numerical builder calls previously
left explicit by [effect construction](EFFECT_CONSTRUCTION_RECONSTRUCTION.md).
The joined `0x0202cf62` constructor executes the actual model builders, their
coefficient calculations, shared state changes and common final gain update.
No numerical return or coefficient array is supplied by a fixture. This does
not establish device operation, execution timing or audio equivalence.

This is reconstructed source, not recovered original source. Required Notice:
Copyright (c) 2026 Manuel Aguirre.
<https://polyformproject.org/licenses/noncommercial/1.0.0>
The preserved license is [third_party/ultrarig/LICENSE.md](../third_party/ultrarig/LICENSE.md).

## Scope and interfaces

The new module contains 49 complete original bodies, 10,818 bytes including one
eight-byte branch table, and 3,081 decoded instructions. The native model also
loads 27 previously reconstructed complete regions. Their 1,694 instructions
are reused, giving 4,775 loaded instructions; they are not new reconstruction
coverage. No frozen source or report is changed.

The public API is
[`hyperrig_effect_model_construction_execute`](../firmware/include/hyperrig/hyperrig_effect_model_construction.h).
It accepts an original entry token, twelve raw argument words, two result
words and a pure borrowed byte mapper. Scalars return in the low result word;
the unsigned quotient returns both words; construction and state-update
entries publish two zero words. Binary32 arguments and results are bit patterns.
The registry below records the number of meaningful arguments, including stack
arguments after the first four.

| Entry | End | Complete body | Arguments | Result |
| --- | --- | --- | ---: | --- |
| `0x01c05ed6` | `0x01c05eec` | `object_mode` | 1 | word |
| `0x01c06004` | `0x01c06028` | `object_record` | 1 | word |
| `0x01c0611a` | `0x01c0612a` | `percent` | 1 | word |
| `0x01c0612a` | `0x01c06148` | `level_exp` | 1 | word |
| `0x01c06148` | `0x01c061ce` | `curve_setup` | 4 | void |
| `0x01c061ce` | `0x01c06230` | `pole_exp` | 1 | word |
| `0x01c06230` | `0x01c0625a` | `curve_state` | 3 | void |
| `0x01c0625a` | `0x01c062d2` | `curve_sample` | 3 | word |
| `0x01c062d2` | `0x01c0636e` | `curve20_setup` | 5 | void |
| `0x01c0636e` | `0x01c0644a` | `frequency_response` | 2 | word |
| `0x01c0644a` | `0x01c06466` | `finite_clamp` | 1 | word |
| `0x01c06490` | `0x01c064d2` | `pitch_curve` | 4 | word |
| `0x01c064d2` | `0x01c064fe` | `pitch_increment` | 1 | void |
| `0x01c064fe` | `0x01c06514` | `pitch_limit_valid` | 0 | word |
| `0x02029e54` | `0x02029e7c` | `object_duration` | 1 | word |
| `0x02029e7c` | `0x02029e98` | `object_limit` | 1 | word |
| `0x02029e98` | `0x02029ec8` | `object_length` | 1 | word |
| `0x02029ec8` | `0x02029ed4` | `object_extra` | 1 | word |
| `0x0202a872` | `0x0202ab98` | `build39` | 1 | void |
| `0x0202ab98` | `0x0202abaa` | `pole_clamp` | 1 | word |
| `0x0202abaa` | `0x0202ac80` | `build16` | 1 | void |
| `0x0202ac80` | `0x0202ad60` | `build17` | 1 | void |
| `0x0202ad60` | `0x0202ae22` | `build18` | 1 | void |
| `0x0202ae22` | `0x0202af48` | `build19` | 1 | void |
| `0x0202af48` | `0x0202b01e` | `build20` | 1 | void |
| `0x0202b01e` | `0x0202b420` | `tone_polynomial` | 5 | void |
| `0x0202b420` | `0x0202b484` | `tone_response` | 1 | word |
| `0x0202b484` | `0x0202b5ac` | `tone_setup` | 5 | void |
| `0x0202b5ac` | `0x0202b616` | `tone_parameters` | 3 | void |
| `0x0202b616` | `0x0202b69e` | `build21` | 1 | void |
| `0x0202b69e` | `0x0202b762` | `build22` | 1 | void |
| `0x0202b762` | `0x0202b838` | `build23` | 1 | void |
| `0x0202b838` | `0x0202b87e` | `build16_to23` | 1 | void |
| `0x0202b87e` | `0x0202ba56` | `build25` | 1 | void |
| `0x0202ba56` | `0x0202ba90` | `pitch_ratio` | 1 | word |
| `0x0202ba90` | `0x0202beb2` | `build29` | 1 | void |
| `0x0202bffc` | `0x0202c0f6` | `object_filter` | 7 | void |
| `0x0202c0f6` | `0x0202c11c` | `odd_length` | 1 | word |
| `0x0202c11c` | `0x0202c1e2` | `object_feedback` | 6 | word |
| `0x0202c1e2` | `0x0202c248` | `object_mix` | 3 | void |
| `0x0202c248` | `0x0202c5a2` | `object_mode1` | 2 | void |
| `0x0202c5a2` | `0x0202c836` | `object_mode2` | 2 | void |
| `0x0202c836` | `0x0202cc9c` | `object_mode0` | 2 | void |
| `0x0202cc9c` | `0x0202cd32` | `object_reset` | 1 | void |
| `0x0202cd32` | `0x0202cdba` | `build_object` | 1 | void |
| `0x0202cdba` | `0x0202cde4` | `square_root30` | 1 | word |
| `0x0202cde4` | `0x0202cf5a` | `signature_coefficients` | 2 | void |
| `0x0202cf5a` | `0x0202cf62` | `build_signature` | 2 | void |
| `0x020331da` | `0x020331ec` | `unsigned_quotient` | 4 | uint64 |

The existing `0x0202cf62..0x0202ddfc` main constructor is an additional supported
entry with one argument. Its private bridge accepts only the six audited direct
targets `0x0202b838`, `0x0202b87e`, `0x0202ba90`, `0x0202a872`, `0x0202cd32` and
`0x0202cf5a`. That original caller contains no indirect call site. This bridge
does not reinterpret arbitrary callback tokens and exposes no platform service
callback through the new public API.

## Numerical and state behavior

The C source preserves individual binary32 rounding steps using the previously
reconstructed arithmetic. It uses no host floating-point expressions or host
transcendental library. Exponential evaluation retains the original repeated
range reduction, polynomial and repeated scaling. This extended use is separate
from the earlier bounded exponential report. Reused whole-function math regions
remain separately identified in the manifest.

The tone polynomial retains its original expression order, the search capped
at 120 expansions, all 30 bisection steps and the final use of the endpoint
sum. Scheduled local intermediate words make the rounding sequence explicit.
The seven-word result feeds the original response calculation and Q28
normalizer. The normalizer's flags reside at native offsets 40 and 41; the
intervening history bytes remain untouched.

The object builders retain native cached values and later reloads. They update
the existing object through its native token; no second runtime or detached
state snapshot is installed. Reset retains its original guarded copies and
four deterministic phase seeds. The signature builder writes all 257 table
entries and 256 deterministic sine/cosine pairs. Its final parameter read occurs
after the table writes, including when those writes alias parameter storage.

The type-29 filter branches both return to the shared phase initialization at
`0x0202bce2`. Cold-state comparisons exercise that path, the negative-pitch
filter, frequency-limit boundaries, coefficient copying, and later carried
calls. Model 25 is also tested with independently zero/nonzero pending and
active state.

The response helper preserves sparse mappings. It first reads words at
offsets 24, 20 and 0. It reads numerator words 16, 12 and 8 only after a positive
denominator result, and never reads offset 4. The public response sweep repeats
those native reads. Four comparison cases omit the unused word and, for the
gated return, the numerator words as well. Sanitizer fixtures split those
mappings into separately allocated spans.

## Borrowed storage and reached guards

The mapper must preserve native address relationships and provide stable byte
storage. Unaligned views and native aliases are supported; unrelated native
windows must not acquire extra host aliases. API, argument and result objects
remain disjoint from firmware storage. No relocation, concurrency or reentry
is permitted. The private stack interval `0x30000000..0x30001020` and private
coefficient arrays cannot alias public data tokens.

Every reached span must be mapped without crossing address wrap. Immutable
tables must contain the pinned original bytes. Additional reached bounds are:

- Exponential inputs are finite and have magnitude at most 65,536. The reused
  coefficient generator retains its finite parameter magnitude limit of 128.
- Direct object-length indices are 0..7; tone selectors are 0..2.
- The reached feedback interpolation interval is 0..3. A negative parameter
  that still truncates to interval zero retains the original extrapolation.
- The immutable object records determine branch groups. No test substitutes
  different record bytes to make an otherwise unreachable branch execute.

Errors are `-200` for invalid API, `-201` for mapping, `-202` for a reached domain
guard, and `-203` for exhausted work. Earlier writes survive; later effects are
skipped and output results remain unpublished. The work budget counts portable
operations, not original cycles. Focused guards check the cache-reset prefix,
the first curve coefficient before a later mapping failure, and the same
coefficient before work exhaustion.

## Exact static data

The new evidence binds 16 spans totaling 669 bytes. Complete consumers, their
original byte hashes, decoded base/index/stride sites and execution distinctions
are included in `table_proofs` in the report. Endpoints are exclusive.

| Start | End | Bytes | Meaning and bound |
| --- | --- | ---: | --- |
| `0x0202b846` | `0x0202b84e` | 8 | Eight model-dispatch byte entries; no added padding |
| `0x0203b4a8` | `0x0203b4ae` | 6 | Three mode-2 halfword lengths |
| `0x0203b4b8` | `0x0203b608` | 336 | Four 84-byte object records |
| `0x0203b674` | `0x0203b6bc` | 72 | Two model-19 records |
| `0x0203b6bc` | `0x0203b710` | 84 | Three tone polynomial records |
| `0x0203b710` | `0x0203b718` | 8 | Eight mode-1 route indices |
| `0x0203b718` | `0x0203b72c` | 20 | Five interpolation values for four intervals |
| `0x0203b72c` | `0x0203b74c` | 32 | Sixteen reached mode-0 lengths |
| `0x0203b75c` | `0x0203b764` | 8 | Two reached mode-0 feedback values |
| `0x0203bdc8` | `0x0203bdd8` | 16 | Eight object-length values |
| `0x0203bdd8` | `0x0203bde8` | 16 | Four model-39 time constants |
| `0x0203bde8` | `0x0203bdf8` | 16 | Eight mode-1 lengths |
| `0x0203bdfc` | `0x0203be08` | 12 | Mode-2 float indices 1..3 |
| `0x0203be08` | `0x0203be18` | 16 | Statically identified group-one lengths; unreachable |
| `0x0203be18` | `0x0203be28` | 16 | Four model-31 values |
| `0x0203be29` | `0x0203be2c` | 3 | Mode-2 byte indices 1..3 |

The complete selector `0x01c06004..0x01c06028` returns record indices 0..3.
Their group bytes at record offset 58 are exactly `[0, 2, 0, 0]`. This narrows
the reached length and feedback spans by 20 bytes from the earlier development
allocation estimates. The suffixes `0x0203b74c..0x0203b75c` and
`0x0203b764..0x0203b768`, and the unused prefixes at `0x0203bdf8` and
`0x0203be28`, remain unclassified and are omitted from data exclusions. The
16-byte group-one table has an explicit static base and bounded consumer, but is not dynamically
validated under the immutable-record contract.

## Instruction coverage limits

Five new instructions have static reasons for remaining unexecuted:

- `0x01c06216`: negative rounding of `1-exp(x)`. An admitted nonpositive finite
  exponent performs no positive scaling. A positive reduced remainder can only
  follow a negative reduction, remains below `ln(2)-0.5`, and is halved at least
  once. A nonpositive reduced remainder uses decreasing alternating terms; near
  zero the first rounded term may reach one while later positive terms remain
  below an ULP. The result cannot exceed one, so the pole value is nonnegative.
- `0x0202bb7c`: the window is at most 1,300; the earlier minimum limits the
  rounded count to 33. The later signed clamp at 48 cannot be selected.
- `0x0202cb02`, `0x0202cb2e`, `0x0202cb32`: group-one table/level paths cannot be
  selected by the four pinned records whose group bytes are 0 or 2.

These are static numerical/control arguments, not extra executed cases. The
report keeps them separate from visited instructions and lists inherited gaps
separately. Full function reconstruction does not mean every original path was
executed or the whole firmware has been validated.

## Inputs, reproduction and evidence

The verifier unpacks and authenticates the original container locally:

- Original container SHA-256:
  `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
- Decoded application SHA-256:
  `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
- Tested MINI v4 container SHA-256:
  `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

Every declared whole body, every loaded instruction window, and every loaded
data span is compared with the decoded MINI image. Source provenance includes
recursive C headers, the instruction TOML and the dynamically imported `s.py`,
`b2.py` and `r.py` semantics. No earlier ignored report is a build prerequisite.

Run from the repository root with the pinned inputs available locally:

```powershell
python -B tools/build_effect_model_construction.py --output build/reverse-effect-model-construction-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder requires a fresh ignored output directory. It builds strict host
code, all pi32v2 objects, focused original-instruction tests and exact-allocation
ASan/UBSan replays. Generated evidence and firmware artifacts remain outside Git.

The frozen evidence is `build/reverse-effect-model-construction-03`:

- 1,657 C/original comparisons and 4,560,397 original instruction steps.
- 3,076 of 3,081 new instructions visited; the five static gaps above remain
  explicit. Loaded coverage is 3,441 of 4,775 instructions, with 1,329 inherited
  instructions unvisited in this corpus.
- 72 joined main-constructor calls, 116 cases marked as carried state, 31 native
  alias cases and four sparse coefficient mappings.
- 18 focused tests, 1,657 exact-allocation ASan/UBSan replays and 16 API guards.
- Strict host compilation and 40 pi32v2 objects. All 39 reused objects match the
  earlier construction checkpoint; all 40 match the preceding candidate.
- All 162 source hashes and 46 artifact hashes were independently read back.
  The 76 declared complete regions, 13 coalesced loaded instruction windows and
  25 loaded data spans are locally bound to the pinned MINI image.

| Evidence | SHA-256 |
| --- | --- |
| `verification.json` | `f36d4654d4517242cc988490fa921ac894140314ca450c36a4cbad2dd64b9c03` |
| `build-manifest.json` | `810d7b415de78ad895a4973dd276907bfc8e3b2f5db9919fdffb8f5ade66d1d9` |
| Numerical comparison digest | `a913cd0eb059955f19bdda7146c1b14b0b3a69ed3e7db15740a6eda18f095bc5` |
| Portable C | `a46af0f146b872340e082fde67e62f27526f15843e972d4e8c9041a13c56eaf5` |
| Public header | `30658f09378ec0b2a1391e38166fe98e2941d7646d23fb4ed6de60fccac63598` |
| Original-instruction model | `1396623c53cebb0ed76b70e2743d12342663ea927b4421b6a13bb0245bdb527e` |

Independent review checked numerical ordering, native aliases, wide arithmetic,
object records, reset copies, the signature loop and the direct constructor
bridge. The response mapping finding was fixed by preserving lazy reads and
verified with omitted-word mappings. The numerical invariant behind the pole
gap was reviewed separately from executed coverage. No device test or complete
firmware reconstruction claim follows from this bounded result.
