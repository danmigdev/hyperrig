# Effect construction reconstruction

This offline checkpoint reconstructs the complete effect constructor at
`0x0202cf62..0x0202ddfc`, twelve shared scalar helpers, and the complete type-26
coefficient builder. It derives actual coefficients and preserves carried state.
Six larger type-specific builders remain explicit mutable service boundaries.
No device access, flashing, timing measurement, or audio validation is involved.

The source is a reconstruction, not recovered original source. Required Notice:
Copyright (c) 2026 Manuel Aguirre.
<https://polyformproject.org/licenses/noncommercial/1.0.0>
The preserved license is [third_party/ultrarig/LICENSE.md](../third_party/ultrarig/LICENSE.md).

## Complete functions and provenance

All endpoints are half-open. The fourteen new bodies contain 4,704 bytes,
including 84 bytes of embedded tables/alignment, and 1,242 decoded instructions.

| Entry | End | Purpose |
| --- | --- | --- |
| `0x01c060fa` | `0x01c0610a` | Mode-to-rate-shift mapping |
| `0x01c0610a` | `0x01c0611a` | Packed five-bit signed bias |
| `0x01c06514` | `0x01c06526` | `SRV1` signature check |
| `0x01c06526` | `0x01c06554` | Common final gain destination |
| `0x02029fc8` | `0x0202a00a` | Bounded size selection |
| `0x0202a680` | `0x0202a6aa` | Rate-dependent exponential transform |
| `0x0202a6aa` | `0x0202a6ca` | Binary32-to-Q30 conversion |
| `0x0202a6ca` | `0x0202a75e` | Original bit-level logarithm approximation |
| `0x0202a76c` | `0x0202a7a8` | Tempo-derived sample/count value |
| `0x0202a7b2` | `0x0202a7f6` | Exponential coefficient conversion |
| `0x0202a7f6` | `0x0202a814` | Tempo parameter index |
| `0x0202a814` | `0x0202a872` | Tempo parameter value |
| `0x0202beb2` | `0x0202bffc` | Type-26 four-section coefficient builder |
| `0x0202cf62` | `0x0202ddfc` | Complete effect constructor |

The 3,738-byte constructor has SHA-256
`6095a50f77b2e4e8301b568bd4b1240708fd8c27aba54a69a8ff64df6f76e717`.
Its 39-entry TBH is exactly `0x0202cfac..0x0202cffa`; the tempo-index helper
contains five TBB bytes at `0x0202a802..0x0202a807` and one alignment byte.
The model excludes these data bytes from decoded-instruction counts and verifies
every dispatch destination against a decoded packet start.

The pinned original image SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`;
its extracted application is
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
The reviewed MINI v4 image is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier authenticates the original, re-extracts it, and compares every
declared body, ABI-evidence body, loaded instruction window and immutable table
against that exact MINI image. Earlier reports are not build prerequisites.

Eleven previously reconstructed bodies execute internally: scaled exponential,
exponential, sine, cosine, square root, coefficient generation/normalization,
Q28/Q16 conversion, tempo selection and logical-size conversion. Reused bodies
are declared for byte binding and counted separately from the fourteen new ones.
The original native model executes their instructions rather than supplying
mathematical callback results.

## State and arithmetic contracts

The constructor accepts one original effect token. It reads byte `effect+6`
and the word at `0x01c1f7f8`, folds mode 2/3 to shift 1, performs the native
masked shift, then writes `0x01c1f814`. Only after that write does it read the
effect type. The common finalizer rereads the type after a builder can mutate
it, selects the original destination, and applies signed division to the
shifted halfword. Original incidental return-register contents are not exposed
for constructor/type26: the public API returns two zero result words.

Type 36 generates six real 44-byte coefficient objects. Type 37 generates seven
or five, preserving the dependent parallel packet at `0x0202d12e/0x0202d130`.
It clears exactly `effect+388..effect+464` only when the normalized mode changes.
Type 13 builds all 33 coefficient lookup words with the original exponential,
sine and cosine approximations, retains history, and preserves the duplicate
last table word. Type 26 updates four enable flags and leaves coefficients and
residual flags intact for disabled sections. Type 5 retains the original delay
transition scheduling, including the existing pending/count/history fields.

Every binary32 operation uses the existing integer implementations and pinned
ISA semantics. There is no host `float` or `libm` substitution. Wrapped integer
products, masked shifts, signed versus unsigned comparisons, sign-directed
conversion saturation and division-by-zero results remain explicit. The
logarithm helper is the original exponent/mantissa approximation for all raw
words; no claim of an ideal mathematical logarithm is made. The size selector
always stops at 2048, independently of the requested threshold.

The new exponential adapter extends only original range reduction and repeated
rescaling around the unchanged bounded polynomial API. Reached input must be
finite with magnitude at most 65536. Each reduction and scale application is
performed separately with binary32 rounding under a finite work budget. This
extension has its own comparisons and does not revise the earlier bounded
exponential report. Reached coefficient-generator parameters retain the prior
finite magnitude limit of 128. A violation stops further effects, retains
earlier writes, and leaves public result storage unchanged. These reached-call
guards are part of the new API; they are not asserted to exist in the firmware.

The borrowed map preserves original address relationships and may supply
unaligned host byte views. Native aliases, including coefficient output that
overwrites the divisor read by a later section, are covered. The map must be
pure and stable; distinct native windows cannot gain extra host aliases.
API/IO/result storage is disjoint from mapped memory. The original private
stack reservation `0x30000000..0x30001020` is excluded from data tokens, and local
coefficient objects cannot alias public memory. No reentry, concurrent mutation,
relocation or retained views are supported. Status values are documented in
[the public header](../firmware/include/hyperrig/hyperrig_effect_construction.h).

## Remaining services and data

Each boundary retains its original direct-call arity, synchronous mutation
ordering, and callee-saved register contract. These are boundaries rather than
claims of reconstructed type-specific numerical behavior.

| Target | Arguments | Complete ABI evidence |
| --- | --- | --- |
| `0x0202b838` | effect | `0x0202b838..0x0202b87e` |
| `0x0202b87e` | effect | `0x0202b87e..0x0202ba56` |
| `0x0202ba90` | effect | `0x0202ba90..0x0202beb2` |
| `0x0202a872` | effect | `0x0202a872..0x0202ab98` |
| `0x0202cd32` | effect | `0x0202cd32..0x0202cdba` |
| `0x0202cf5a` | object, parameter-halfword pointer | wrapper `0x0202cf5a..0x0202cf62` and callee `0x0202cde4..0x0202cf5a` |

Six newly bound external table spans total 89 bytes:
`0x0203a550..0x0203a55c`, `0x0203b608..0x0203b616`,
`0x0203b618..0x0203b634`, `0x0203b634..0x0203b639`,
`0x0203b63a..0x0203b644` and `0x0203b644..0x0203b658`.
They supply the type-36/type-37 frequency, width and clamp values. Their gaps
are not inferred to be data. The 26-byte tempo tables at
`0x0203b658..0x0203b672` are reused. Thus this module introduces 173 exact known
data bytes when its two embedded table/alignment spans are included.

## Verification and caller integration

The standalone corpus compares every returned word, every mapped byte, ordered
service arguments, callback boundaries and partial/carried state. It includes
all 256 type bytes, mode shifts, raw binary32 words, signed halfword extremes,
zero-divisor arithmetic, filter-mode changes, builder mutations and native
memory aliases. Twenty focused tests assert specific state and ABI properties.

A separate test-only bridge executes the frozen parameter commit/fast/wrapper
callers into this constructor. The native side shares the original registers,
stack, return frames and memory. The C test bridge intercepts the constructor
service only within fixtures that explicitly leave indirect callback slots
zero and reject construction-token callbacks. Native call sites `0x0202f37c`
and `0x0202f970` are recorded, and sanitizer replay independently counts the
same direct constructor executions. This bridge is not a generally correct
public integration API: an indirect callback can otherwise have the same token
and arity as the constructor. A direct-call-aware lifecycle integration is a
separate milestone.

The replay harness allocates exact input spans, including deliberately unaligned
views, and compares complete expected memory bytes rather than only hashes.
It replays callback mutations and arguments under AddressSanitizer and
UndefinedBehaviorSanitizer. Additional guard witnesses check private-stack
exclusion, mappings, budgets, missing callbacks and preservation of earlier
rate writes when coefficient generation is rejected.

To reproduce, use a new output directory and the reviewed local MINI image:

```text
python tools/build_effect_construction.py --output build/reverse-effect-construction-repro --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles strict host and pi32v2 objects, runs the focused tests,
compares original instructions, replays exact allocations under sanitizers,
and checks that all source bytes remained fixed throughout. Its source manifest
includes recursively referenced headers, the instruction TOML, and the dynamic
ISA semantics files omitted by ordinary module enumeration. Generated fixtures,
objects, binaries and reports stay in the ignored build directory.

## Frozen result

The selected evidence is `build/reverse-effect-construction-02`. Candidate 01
stopped at a target-compiler aggregate-initializer warning; its existing files
are preserved. Candidate 02 uses explicit, fully nested zero initializers and
passes the complete build. Independent source/API review found no remaining
semantic mismatch after the test-only integration limitation was made explicit.

| Check | Result |
| --- | --- |
| C/original comparisons | 3,270 |
| Complete constructor calls compared directly | 1,019 |
| Separate type-26 calls | 63 |
| Original instruction steps | 3,209,234 |
| New instruction coverage | 1,242 / 1,242 |
| Declared new and reused instruction coverage | 1,494 / 1,495 |
| All loaded instruction coverage | 2,197 / 16,253 |
| Actual coefficient requests in standalone cases | 699 |
| Extended exponential calls beyond the previous magnitude-16 API | 14 |
| Largest compared exponential magnitude | Binary32 `0x47800000`, exactly 65,536 |
| Mutable builder cases / carried calls | 24 / 60 |
| Parameter caller comparisons / actual direct constructor calls | 72 / 72 |
| Direct constructor sites in those fixtures | 24 at `0x0202f37c`; 48 at `0x0202f970` |
| Focused native tests | 20 passed |
| Exact-allocation ASan/UBSan replays | 3,270 passed |
| Additional API/partial-write guards | 14 passed |
| Strict pi32v2 objects | 39 |
| Source/header/ISA hashes read back | 155 matched |
| Artifact hashes read back | 45 matched |
| Earlier same-source parameter target objects compared | 38 byte-identical |

The one unvisited instruction in the declared reused bodies is `0x02028842`,
the mode-2 generator's zero-parameter enable assignment. It is an inherited
coverage gap in this corpus, not missing constructor code. The report also
lists every unvisited address in the much larger loaded parameter/scene/stage
closure. Loading or binding those functions does not claim that this corpus
executes their complete paths. MINI binding covers all 73 loaded instruction
windows, all 34 loaded table declarations, the 25 declared complete bodies,
and seven complete bodies used as service-ABI evidence.

The verification report SHA-256 is
`5a4a64c7598fc2ac4809dcd8fd1cba7cdb577270a9333f6a59c38390c38a5479`.
The build manifest SHA-256 is
`9cae1c3f1db3c5eea5d509c6265d7062fbfc07255eb47134b753ab426ece8fc5`.
The reconstructed C SHA-256 is
`f4931857baaa1cee59a8c002f8630f0227913411efca3b9f0701eaf9ee780dff`.
The replay fixture contains 1,010,194,763 bytes of original inputs, ordered
service effects and complete expected output memory; it remains outside Git.

The six larger builder services, full-firmware runtime coverage, peripheral
behavior, scheduling and audio equivalence remain outside this checkpoint.
