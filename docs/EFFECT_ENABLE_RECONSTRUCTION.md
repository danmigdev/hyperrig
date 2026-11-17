# Effect enable, fade and installed clear reconstruction

This milestone reconstructs the complete effect-enable cores and their public
wrappers, fade/tail state selection, duration calculation, guarded IR reset,
and the installed memory-clear callback. The original decoded instructions and
portable C share the same borrowed native-address state in the comparison.
Allocation, resource estimation, configuration notification and type-specific
refresh services remain explicit synchronous boundaries.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

The original [UltraRig license](../third_party/ultrarig/LICENSE.md) and preserved
input notices continue to apply. This is offline reconstruction evidence. No
firmware was flashed, and no hardware, audio, latency or physical-unit result is
claimed.

## Complete boundaries

All intervals are half-open. The fade function contains a 29-byte TBB table and
one alignment byte; these 30 bytes are included in its byte binding but are
excluded from instruction decoding.

| Entry | End | Purpose | Decoded instructions |
| --- | --- | --- | ---: |
| `0x020303f4` | `0x02030466` | Duration selection | 40 |
| `0x02030466` | `0x02030520` | Enable with construction | 72 |
| `0x02030520` | `0x02030530` | Successful-result finish | 7 |
| `0x02030530` | `0x0203053a` | Checked construction wrapper | 5 |
| `0x0203053a` | `0x020305f8` | Enable using available resources | 68 |
| `0x020305f8` | `0x02030602` | Checked fast wrapper | 5 |
| `0x02030602` | `0x0203060a` | Unchecked fast wrapper | 4 |
| `0x0203060a` | `0x02030614` | Unchecked construction wrapper | 4 |
| `0x01c069c6` | `0x01c069e4` | Tail-support type predicate | 8 |
| `0x01c069e4` | `0x01c06b2c` | Fade/tail state and buffer reset | 108 |
| `0x01c11f76` | `0x01c11faa` | Guarded IR state reset | 22 |
| `0x0201a9dc` | `0x0201a9ea` | Installed clear callback | 5 |
| `0x02033412` | `0x0203343e` | Memory-fill routine | 17 |

These thirteen complete bodies contain 1,012 bytes and 365 instructions. The
reused request-counter helper `0x01c05160..0x01c0516e` adds 14 bytes and five
instructions. It increments `0x01c34468` modulo 2^32; it is not a wait or barrier.

The table begins at `0x01c06a4a`, ends at `0x01c06a67`, and is followed by one
zero alignment byte. The `tbb` at `0x01c06a48` indexes effect type minus eleven
after an unsigned upper-bound check. Targets are `table_start + 2*entry`.
All 29 indices are compared, and every target is required to be decoded code.
The fixed-length clear belongs to type 29, the refresh-only branch to type 30,
and the eight-word state clear to type 38. Types 11, 12, 15 and 39 select the
length-dependent clear. Other entries proceed directly to duration selection.

## Borrowed state and exact behavior

The public [header](../firmware/include/hyperrig/hyperrig_effect_enable.h) and
[C implementation](../firmware/src/hyperrig_effect_enable.c) expose
`hyperrig_effect_enable_execute(entry, arguments, result, io)` and the direct
`hyperrig_effect_enable_ir_reset(object_token, io)` adapter. The callback
interface carries native address tokens, six argument words and a semantic
argument count. The two enable cores accept slot, desired state and resource
check flag. Their wrappers accept slot and desired state.

The central views are sixteen 480-byte effects at `0x01c2c220`, the 68-byte
configuration at `0x01c1f7d4`, 640-byte control at `0x01c32db0`, and 768-byte
callback area at `0x01c34190`. Pointed-to effect and IR storage is borrowed on
demand. IO, arguments and result storage must be disjoint from mapped firmware
bytes. Mappings preserve native address relationships and stable storage;
unrelated native windows cannot be arbitrary host aliases. The same native
address may alias an effect record or an IR object, and forward writes retain
their original order. Mapping only borrows storage and cannot mutate firmware
bytes; synchronous service callbacks can mutate them. Byte access avoids host
alignment and type-punning UB.

API errors are separate from native results: `-200` invalid interface/entry,
`-201` unavailable or wrapping access span, `-202` exhausted service/bulk-store
budget, and `-203` absent service implementation. An error preserves native
writes already performed and leaves the scalar result untouched. The bulk
budget counts word or byte stores in variable clear loops; it does not count
the fixed state-field writes. Void fade, IR-reset and counter results normalize
to zero. Memory fill and its installed wrapper return the original buffer token.

The construction core increments the request counter before slot/presence
validation. The fast core increments it only on an accepted enable/disable
path. The construction core queries slot cost before current total and still
queries cost when checking is disabled. The fast core queries current total
before cost. Both compare a wrapped unsigned sum against the freshly loaded
control limit. Their public checked wrappers invoke the finish service only on
zero native status, preserving that status even if the service returns another
value. Unchecked wrappers skip the finish service.

Construction success reloads enabled state before deciding whether to fade.
Fast availability reloads the working-buffer token after its demand callback.
Callbacks can change limits, effect fields, buffer tokens and counters, and the
comparison records state before and after every explicit service. The original
callback mutation points are retained rather than replaced with copied runtime
objects.

Duration uses the original signed maximums, arithmetic right shift, wrapped
32-bit sums and unsigned final shifts. It returns zero for a nonpositive signed
intermediate or missing working buffer, otherwise caps the derived value at
sixteen. Fade reversal writes `4 - old_count` modulo 256. A nonzero tail count
takes the separate type-mask path and can select mode five without clearing
the stored count. These are recovered raw fields; their physical meanings or
timing units are not inferred.

An active IR reset computes `partitions * 129` modulo 2^32, clears that many
pairs of words through object +24, then reloads object +48 and clears 256 words.
Only after those writes does it clear object indices +8/+12. A null object or
zero first word returns immediately. The count is cached before clear writes;
the later buffer pointer is reloaded, which matters when native storage aliases.

The installed callback `0x0201a9dc` passes zero fill and its byte-count argument
to the actual decoded `0x02033412` routine. This performs alignment byte writes,
replicates the low fill byte, executes word stores and finishes with byte stores.
The portable code implements that sequence without delegating it to host
`memset`. Other callback tokens remain explicit services, including a token that
collides with another loaded entry. Focused witnesses check that distinction
and a token colliding with a direct service: the indirect call still has two
semantic arguments. Comparison arity follows the decoded call site.
Register REP follows
the pinned ISA model, including zero and larger counts; the upstream measured
v3 examples cover positive small counts. This milestone adds offline comparisons
for zero, alignment and larger lengths, not new hardware evidence for REP.

## Audited service contracts and remaining scope

Every direct boundary's complete callee bytes are bound to the original and
MINI images. They are ABI evidence, not reconstructed function declarations.
No incoming stack arguments are consumed by these direct callees.

| Target | Semantic inputs | Purpose left external |
| --- | --- | --- |
| `0x0203023c` | slot | Resource cost |
| `0x02028de8` | none | Current resource total |
| `0x0203033c` | effect token | Resource construction/allocation |
| `0x0202def2` | effect token | Resource demand |
| `0x0202ec30` | none | Successful-change notification |
| `0x0202e328` | effect token | Type 29 refresh |
| `0x0202e3ce` | effect token | Type 30 refresh |
| Alternate clear token | buffer token, byte count | Replacement clear implementation |

The installed clear writer at `0x0200254a..0x02002558` is bound separately. Its
destination is `0x01c34194` and value is `0x0201a9dc`. The comparison executes the
installed callback body; it does not execute the entire surrounding startup.

The only unvisited new instruction is `0x020304fc`. The construction branch is
entered with nonzero desired `r4`. Conforming callees preserve that register,
so the test at `0x020304fa` always skips the zero-only move at `0x020304fc`.
The report retains this instruction as decoded and unexecuted. It is never
counted as a successful runtime witness.

## Reproduction and evidence

The [instruction model](../tools/effect_enable_machine.py) decodes the preserved
image. The [verifier](../tools/verify_effect_enable.py) compares full mapped
state, native results, callback arguments, callback order and both callback
snapshots against C. Focused [instruction tests](../tests/test_effect_enable_machine.py)
independently assert important constants and forwarding contracts. The
[sanitizer harness](../tests/effect_enable_sanitize.c) uses exact allocations for
effect views, memory-fill destinations, 52-byte IR objects and their separate
spectral/tail buffers, including partial budget/mapping failures.

Run the [builder](../tools/build_effect_enable.py) with a fresh output folder:

```powershell
python -B tools/build_effect_enable.py `
  --output build/reverse-effect-enable-new `
  --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder performs strict host C compilation, a strict freestanding pi32v2 r3
object build, focused instruction tests, exact-allocation ASan/UBSan checks and
the original-instruction comparison. The manifest binds its generated artifacts;
the verifier independently records recursively loaded local source files, C and
header sources, explicit dynamic ISA helper sources, the instruction TOML and
the source input manifest. No earlier ignored verification report is needed.

The original image SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The reviewed MINI v4 image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
All complete decoded regions, the embedded table/alignment, external ABI windows
and installed-callback writer must match locally. The region hashes in the
verification JSON bind exact original bytes; generated objects are not firmware
images and are not suitable for flashing.

The final evidence is frozen in `build/reverse-effect-enable-03`. Earlier
development and build-01/build-02 outputs remain unchanged. Independent review
checked the complete enable/fade bodies against the original instructions and
found no in-domain C mismatch. The final version also clarifies pure mapping
and verifies both alternate-token collision cases.

| Final check | Result |
| --- | ---: |
| C/original comparisons | 2,941 |
| Original instruction packets executed | 315,924 |
| New instructions executed/decoded | 364 / 365 |
| All loaded instructions executed/decoded | 369 / 370 |
| Focused instruction tests | 20 |
| Exact-allocation ASan/UBSan cases | 1,478 |
| Sanitizer partial-failure guards | 3 |
| C API guard checks | 11 |
| Callback-mutation cases | 24 |
| Carried calls | 72 |
| Installed clear calls from fade | 36 |
| Actual nested memory-fill entries | 100 |
| Actual nested IR-reset entries | 13 |

The direct memory-fill, clear and IR-reset entry cases are additional to the
nested-entry counters. All 26 recorded source hashes and all five artifact
hashes were independently read back and matched. The original image was also
hashed directly and matched the pinned value above. Host and pi32v2 builds pass;
the target object is unchanged across the three completed builds because the
later changes affect interface documentation and verification boundaries.

| Evidence | SHA-256 |
| --- | --- |
| Final `verification.json` | `36dc61dfa6c598c78cb2629f4a9ac6668e5bc9060b2b8d592633f895d3373071` |
| Final `build-manifest.json` | `3701c76751711b51b7dc048c8a4c6a5126eeccc08462e4b27829a4035f31e7ac` |
| Reconstructed C | `2468b91505829c2fd7d9d12154527ec534a393c8b5659425f492e9a3b4f90169` |
| pi32v2 object | `1d4cc3a8016e5a6d370e0eda479bc8574e708f89b8f4295508f3baa1e09d71dd` |
| Fade table, exactly 29 bytes | `b938b1435b794419e01db5cff039782e3016382ba2ad689a0035d9c81d8319bb` |
| Following zero alignment byte | `6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d` |
