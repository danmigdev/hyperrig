# Parameter primitives, division and memory support

This module reconstructs 19 complete M5.71 functions used by parameter updates:
selectors, byte packing, buffer lookup and clearing, size and tempo arithmetic,
an upper-clamped Q16 ratio, `memmove`, signed 64-bit division, and unsigned
64-bit division with an optional remainder. The C implementation operates on
borrowed original-address storage. The comparison model executes the decoded
original instructions, including the complete division cores and the installed
clear callback. Alternate clear callbacks remain explicit services.

This is an offline reconstruction. It does not establish hardware, audio,
physical sample-rate or timing behavior, and it does not produce a flashable
firmware image. The enclosing parameter-application bodies are a separate
module.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
Preserve [the upstream license](../third_party/ultrarig/LICENSE.md) and its
[PolyForm Noncommercial terms](https://polyformproject.org/licenses/noncommercial/1.0.0).
These files are reconstructed implementations, not the original source.

## Source and complete boundaries

The original packaged Alpha11 M5.71 image has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
Its extracted application has SHA-256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
The model authenticates both through the preserved input manifest and unpacker.
Each decoded function and static-data window is also compared with the unpacked
reviewed MINI v4 image, whose whole-image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

All endpoints below are exclusive. The 19 new functions contain 1,308 bytes and
449 decoded instructions. Two unchanged enable-module functions add 58 bytes
and 22 instructions to the loaded comparison program.

| Function | Original range | Instructions |
| --- | --- | ---: |
| Selector lookup | `01c060e6..01c060fa` | 6 |
| Parameter packing | `01c06466..01c06490` | 19 |
| Clear halfword capacity | `01c06554..01c06582` | 17 |
| Extra-state pointer | `01c06582..01c065a4` | 14 |
| Signed three-state clamp | `01c065b4..01c065c4` | 6 |
| Signed two-state clamp | `01c065c4..01c065d0` | 5 |
| Capability selector | `01c065d0..01c065e2` | 6 |
| Active-state word | `01c067e0..01c067ea` | 3 |
| Signed Q16 ratio | `01c06926..01c0696a` | 21 |
| Timing rule selection | `01c0696a..01c069b0` | 24 |
| Base capacity | `02029e12..02029e32` | 9 |
| Expanded capacity | `02029e32..02029e3c` | 5 |
| Tempo selector predicate | `0202a75e..0202a76c` | 5 |
| Encoded-to-logical capacity | `0202a7a8..0202a7b2` | 4 |
| Tempo division | `0202ed38..0202ed70` | 18 |
| Tempo from configuration | `0202ed70..0202ed7e` | 5 |
| Complete `memmove` | `02032b2e..02032bf0` | 74 |
| Signed 64-bit division | `02033172..020331ce` | 28 |
| Unsigned 64-bit division/remainder | `020331ec..02033412` | 180 |
| Reused installed clear callback | `0201a9dc..0201a9ea` | 5 |
| Reused `memset` | `02033412..0203343e` | 17 |

The unsigned core continues after its first return at `0x020333c0`. Its
power-of-two denominator tail starts at `0x020333c2`, and its large-shift setup
tail starts at `0x020333f2`; both branch back into the earlier body. The complete
boundary is `0x02033412`. The adjacent unsigned-division wrapper at
`0x020331da` is outside this module. No fragment is counted as a complete
function here.

Static data is authenticated separately from instructions:

| Data | Original range | SHA-256 |
| --- | --- | --- |
| 21 selector words | `0203b880..0203b8d4` | `3d558f81b50146dd3006396db32da015bd93e4df55bf01c78d52e76cdda324a4` |
| Two 13-byte tempo tables | `0203b658..0203b672` | `51c8bacfb9be4ddf3d0f1324e14593277b2bda2ee71a584dbe06ce3653369f51` |
| Reused 40-byte capability table | `0203b480..0203b4a8` | `ad42fb64992b7995f180484ba717298b55c46909537d0e9a01ee333cf4662362` |

## Public contract and retained behavior

The API is declared in
[`hyperrig_effect_parameter_support.h`](../firmware/include/hyperrig/hyperrig_effect_parameter_support.h).
`hyperrig_effect_parameter_support_execute` takes an original entry address,
twelve ABI words, two result words, and a map/service interface with finite
budgets. Arguments after the fourth word represent the original stack
arguments. Only the unsigned division core uses an incoming fifth word: its
optional eight-byte remainder destination.

Packing and clearing are void operations with a normalized zero result. The
two division functions and Q16 ratio return the original low/high result words;
other scalar results have a zero high word. The instruction model retains all
actual register effects internally, including the `r2`/`r3` preservation of
`0x0202a7a8` needed by the enclosing commit caller.

Notable retained details:

- Packing reads the first two halfwords, writes its first output byte, then
  rereads the selected halfword before writing the second byte. Outputs may
  alias the input, so caching that final read would change behavior.
- The extra-state pointer requires a primary buffer even when a separate
  extra buffer is selected. Its in-buffer threshold is 2,021 blocks of sixteen
  halfwords, and the returned pointer adds 8,192 with uint32 wrapping.
- Halfword clearing uses `(capacity + 1) >> 1` word stores on the scalar path.
  At capacities of at least 1,024, a nonzero callback receives the buffer and
  `(2 * capacity + 2) & ~3` bytes, with original uint32 wrapping. Target
  `0x0201a9dc` executes the unchanged clear/memset reconstruction. Other tokens
  retain their two-word callback ABI, even if they collide with a loaded entry.
- `memmove` preserves the original forward/backward overlap decision,
  alignment prefixes, aligned word copies, and unaligned byte-assembly order.
  Reverse unaligned copies read the high byte first. The original destination
  token is returned. Zero-length copies access neither source nor destination.
- Division accepts all raw 64-bit numerator and denominator patterns. Signed
  division truncates toward zero; `INT64_MIN / -1` retains the wrapped minimum
  bit pattern. A zero denominator produces a zero quotient. The unsigned
  core's optional zero-divisor remainder is the numerator when its high word
  is zero, and zero when its high word is nonzero. These are original body
  paths, not a host-language divide-by-zero operation.
- The Q16 ratio wraps `(numerator << 16) - 1`, coerces signed32 denominators
  at or below one to one, performs the complete signed division, and clamps
  only the upper side to `INT32_MAX`. Negative 64-bit results retain their high
  word. Capacity and tempo calculations retain their uint32 multiplication
  and addition wrapping; native unsigned32 division by zero returns zero.

The C division uses bounded unsigned magnitude/restoring arithmetic to avoid
undefined signed overflow. The original comparison executes all 208 division
instructions. Its PSR and carry handling follows the pinned ISA descriptions,
including no-borrow carry for subtraction and `N xor V` for signed comparison.
Conditional-block counts and old-register parallel packets are decoded from
the original bytes.

The memory-library model captures a REP iteration count before executing the
body. Some original copy loops overwrite the count source register with a
loaded byte, so reading that changed register as the loop count is incorrect.
The model uses zero iterations for zero counts and clears the count register on
completion. The pinned ISA records hardware tests for positive counts 1..7;
zero counts, large counts, interrupt interaction and timing are not new
hardware measurements. Complete copy/clear comparisons therefore remain
conditional on this documented REP interpretation.

Maps must be pure, stable byte views and preserve original address
relationships. Native aliases are supported, while distinct native spans must
not become aliases in host storage. API objects are disjoint from mapped
memory. Callbacks may mutate mapped memory synchronously, but cannot relocate
maps, modify API objects, retain views, reenter or race the invocation. Host
byte storage may be unaligned. Every accessed span must be mapped, and an
individual access cannot cross the uint32 address boundary; pointers can wrap
between separate valid accesses.

The capability helper is limited to the authenticated types 0..39. Other
scalar inputs retain all raw bit patterns. Memory operations are bounded by
the provided mapping and work budget. Budget units are mapped accesses and
portable division iterations, not instruction counts or CPU cycles. New API
errors distinguish invalid arguments/missing reached services (`-200`), absent
mapping (`-201`), unsupported domain (`-202`), and exhausted budgets (`-203`).
Prior writes remain on failure; result words are published only on success.

## Reproduction and frozen evidence

From the repository root, with the preserved local original inputs and reviewed
MINI image available, choose a fresh ignored output directory:

```powershell
python -B tools/build_effect_parameter_support.py --output build/reverse-effect-parameter-support-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles a host UBSan library and both pi32v2 objects, runs focused
native tests, compares complete mapped memory and original result words, then
replays every comparison fixture under ASan/UBSan with separate exact trailing
allocations. Callback order, arguments and before/after memory are compared.
Fixture replay additionally checks full-memory FNV64 and returned words; the
primary comparison checks complete bytes directly.

The final run is `build/reverse-effect-parameter-support-01`:

| Evidence | Result |
| --- | ---: |
| C/original comparisons | 4,250 |
| New instruction coverage | 449 / 449 |
| Loaded instruction coverage | 471 / 471 |
| Decoded execution steps | 554,829 |
| Focused native tests | 20 |
| Invalid API/domain/budget checks | 11 |
| ASan/UBSan original-fixture replays | 4,250 |
| Additional sanitizer invalid-API check | 1 |
| Carried overlapping-copy calls | 20 |
| Callback mutation comparisons | 72 |
| Source hash bindings | 31 |
| Manifest artifact bindings | 7 |

The corpus covers 1,172 memory moves across alignment, overlap, short and
longer spans; 145 clear calls; 100 packing/alias cases; all capability entries;
raw size/tempo overflow and zero division; and 1,349 direct division/ratio
comparisons. No new or loaded instruction gaps remain. Full instruction
coverage is a finite-corpus result, not proof of all possible inputs or device
execution.

The report binds imported repository Python, dynamically loaded ISA modules,
the decoder TOML and recursively included C headers, without relying on a
previous ignored report. Independent read-back confirmed all 31 source and
seven artifact bindings. Independent source review checked packing, clearing,
extra-state lookup, ratio, signed-magnitude arithmetic, overlap ordering and the
original memory-copy directions; no in-domain mismatch was found. The complete
division tails and REP interpretation are documented above.

- `verification.json` SHA-256:
  `ef851841a59f69148d1b855080e66baf125f0a1d867a8c3885af9edefe66a290`.
- `build-manifest.json` SHA-256:
  `b06ae6038a0804d2b3a34f4bd8f1cec7f2391b6c16656330e15a0371345bc3e4`.
- `hyperrig_effect_parameter_support.pi32v2.o` SHA-256:
  `5b7d21619f4ac55fe2f9a6e3546789c270fa6d453abb7bbf21b4a47a49fcf795`.
- Reused `hyperrig_effect_enable.pi32v2.o` SHA-256:
  `1d4cc3a8016e5a6d370e0eda479bc8574e708f89b8f4295508f3baa1e09d71dd`.

Original images, prior reconstruction sources and generated reports remain
unchanged. Reports, fixture binaries and compiled artifacts remain ignored.
