# Effect parameter reconstruction

This module reconstructs the complete immediate parameter update, automation
producer, fast-update wrapper and resource probe. It also reconstructs the
three complete helpers that classify derived state words. The original scene
application calls these parameter bodies, and the recovered DSP stage consumes
their actual shared automation records.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

This is reconstructed UltraRig code, not the author's original source. The
[original license](../third_party/ultrarig/LICENSE.md) and
[required notice](../third_party/ultrarig/NOTICE.md) remain applicable. Verification
is offline. No firmware was flashed and no hardware, audio quality, latency or
physical-unit result is claimed.

## Complete original bodies

All intervals below are half-open. Together they contain 3,100 bytes and 994
decoded instructions. The 78-byte branch table belongs to the word classifier's
byte range but is excluded from instruction decoding.

| Entry | End | Purpose | Instructions |
| --- | --- | --- | ---: |
| `0x0202f07e` | `0x0202f46c` | Immediate update, allocation and failure handling | 316 |
| `0x0202f4e8` | `0x0202f502` | Eleven-word section classifier | 10 |
| `0x0202f502` | `0x0202f6b4` | Effect-specific derived-word classifier | 130 |
| `0x0202f6b4` | `0x0202f6d4` | Coupled-word reference index | 12 |
| `0x0202f6d4` | `0x0202fba6` | Shared automation-record producer | 403 |
| `0x0202fba6` | `0x0202fbd6` | Fast update and conditional global refresh | 15 |
| `0x0202fd18` | `0x0202fe58` | Prospective resource check | 108 |

The branch table is exactly `0x0202f518..0x0202f566`. All 39 entries select
decoded instruction starts. The pinned 40-by-seven parameter metadata table
at `0x0203a614..0x0203b334` is reused. Its signed halfword bounds are derived
into the C include and checked against every original record. The existing
metadata helper supplies the original presence bits and address tokens.

The reused request-counter body `0x01c05160..0x01c0516e` increments the word
at `0x01c34468`; it is not a synchronization barrier. Slot reset
`0x020290cc..0x02029112` is adapted to the borrowed address map with its same
ordered writes. These helpers are not counted as new functions.

## Recovered behavior

Immediate updates increment the request counter before checking the slot.
For a valid slot, automation reset precedes metadata validation. Signed input
clamping, type-specific selector conversion, bypass transition state, delay
capacity growth, release flags, compressed-history migration arguments and
recursive tempo-linked updates retain their native ordering. Failure paths
can leave partial changes; the reconstruction does not add rollback.

Fast updates keep the original eight-record allocation policy and the limit
of 40 changed derived words. They copy the live 480-byte effect through the
previous and proposed work areas, invoke the explicit construction service,
then produce integer or binary32 deltas and publish the record in native
order. The DSP stage reads this actual record on subsequent calls. No
replacement record is fabricated for the integration check.

The packet at `0x0202fa1a/0x0202fa1c` stores the old derived-word index while
updating the register to the changed-entry count. The coupled-word helper
therefore receives the original word index. A development comparison and
independent instruction review caught and corrected the first C draft's
use of the changed-entry count. The focused native test retains a witness
where those two indices differ.

The resource probe copies and clamps parameters before mutable cost services
run. It then executes the actual parameter-packing helper, active-state query
and both calls to the six-argument processing estimator. The final resource limit is
reloaded after the total-cost service. Unsigned additions and division by
zero retain the pinned instruction semantics; division by zero returns zero.

## Dependencies and boundaries

Parameter support executes actual selector, packing, clearing, size, tempo,
memmove and ratio/division arithmetic. Processing executes the recovered
timing helpers. Scene transitions retain the real installed notification,
and the stage adapter enters the recovered individual/grouped callers.

The following services are still explicit boundaries in this module. Their
test scripts provide mutable results, not reconstructed implementations.

| Target | Semantic arguments |
| --- | --- |
| `0x01c05ec6` | mode |
| `0x0202edb8` | effect token, requested capacity, release-flag output |
| `0x0202ee3c` | effect token, old buffer, old logical count, new buffer, new logical count |
| `0x0202eeba` | effect token |
| `0x0202eefa` | effect token |
| `0x0202efe2` | effect token, new mode |
| `0x0202cf62` | effect token |
| `0x0202cd32` | effect token |
| `0x0202e328` | effect token |
| `0x02028cb2` | slot index, comparison flag |
| `0x02028de8` | none |
| `0x0202ec30` | none |
| `0x0202f014` | effect token |
| `0x0202f02e` | effect token, length, desired value |
| `0x0202983a` | effect token |

An installed release callback receives one buffer argument. Its address can
coincide with a known entry without changing that call site's argument
contract. The release-flag output is normalized only for the direct,
three-argument allocation call, not for unrelated callback tokens. Further
scene or DSP services retain their respective inherited contracts.

An alternate scene-transition notification likewise retains its one-argument
contract when its token matches a parameter entry. Only direct scene calls
with the original three- or four-argument contract enter the reconstructed
parameter body. All four scene entry paths compare these token collisions.

The allocation service receives canonical private token `0x31005000` for
exactly four bytes and must initialize all four before returning. The native
instruction model retains the actual stack pointer internally. No
uninitialized private padding is compared. Other internal parameter scratch
is private to the call. Borrowed views cannot be retained or used concurrently.

Only the supplied service argument count is readable. Inherited processing
services can pass shorter arrays than the maximum public entry buffer.
Public entry arguments are copied before callbacks, preserving the native
input registers even when the argument array resides in mutable mapped RAM.

## Public map and guard contract

The comparison uses shared RAM `0x01c1f180..0x01c344b4`, 4,096 sample bytes
at `0x35010000` and a 131,072-byte arena at `0x33000000`. These are comparison
views, not claims about hardware heap placement. Every actually accessed
span must be mapped; immutable helper tables are read-only.

Native no-op and failure results remain separate from new API statuses.
The adapter uses `-200` for invalid API or an absent reached service,
`-201` for missing mappings, `-202` for a dependency domain violation and
`-203` for exhausted work or service budget. Results are published only on
success; partial native writes survive a guard failure. Scene budget and
domain statuses are translated to these meanings.

Maps are pure and stable. Distinct native spans retain their address
relationships. IO and result objects must be disjoint from mapped state.
The work guard counts borrowed map requests and immediate-update entries;
each support invocation also applies its own bounded arithmetic work guard.
Scene orchestration consumes service budget for its parameter entries as
well as the outer explicit services. These guards are not cycle estimates.

## Unexecuted original instruction

The instruction at `0x0202f960` remains unexecuted. The type load at
`0x0202f934` is followed by the branch at `0x0202f942`, which admits only
`r0 == 5`. The intervening instructions change only `r1` or memory and make
no calls. The conditional block at `0x0202f95c` requires `r0 != 5` before
executing the assignment at `0x0202f960`, contradicting that dominating
condition. Independent instruction review confirmed the one-instruction
block and absence of another internal entry. This classification applies
to the complete public entry and its documented private-stack contract;
the instruction is retained and is never relabeled as executed.

## Reproduction

With the preserved original inputs and reviewed MINI image available, choose
a fresh ignored output directory from the repository root:

```powershell
python -B tools/build_effect_parameters.py --output build/reverse-effect-parameters-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder runs strict host and pi32v2 builds, focused original-instruction
tests, complete-memory and ordered-service comparisons, then ASan/UBSan
fixture replay. The manifest records the completed artifacts. Source hashes
include recursive C headers/includes, imported Python and dynamically loaded
ISA semantics. Final reports reject source changes during verification.

`--build-only` is a development option and produces no verification report.
The verifier's `--part` option also produces development results only.
Neither option establishes a completed reconstruction checkpoint.

## Frozen validation

The selected final run is `build/reverse-effect-parameters-03`.

| Check | Result |
| --- | ---: |
| C/original comparisons | 5,679 |
| Original instruction steps | 1,388,565 |
| New instructions visited/decoded | 993 / 994 |
| Loaded instructions visited/decoded | 2,712 / 15,011 |
| Focused original-instruction tests | 23 |
| C API/domain/budget guard checks | 14 |
| ASan/UBSan original-fixture replays | 3,139 |
| Additional sanitizer invalid-API checks | 6 |
| Calls with carried state | 43 |
| Callback-mutation cases | 230 |
| Private allocation-output calls | 29 |
| Compiled pi32v2 objects | 38 |
| Source bindings independently read back | 150 |
| Artifact bindings independently read back | 44 |

All 2,540 classifier cases execute in the host UBSan comparison. The remaining
3,139 cases additionally replay their original results, complete state and
ordered callback mutations under ASan/UBSan with exact allocations. Seventy
scene/stage integration calls include the actual parameter bodies, the shared
automation producer/consumer and alternate notification-token collisions.
Sixty-one targeted edge cases cover allocated delay capacity, capture/IR
readiness, mode changes and increasing resource costs.

All 15,011 loaded instruction windows and 25 immutable data windows match the
pinned original and reviewed MINI v4 image. All 38 target objects are identical
to run 02; run 03 strengthens verification without changing the C implementation.
Earlier outputs remain preserved. Run 01 rejected a changing model source and
did not produce final evidence; run 02 passed its narrower corpus but is not
selected for the maintained verifier. Independent review checked the complete
caller contracts, parallel-packet behavior, callback collisions and the sole
remaining instruction-gap proof.

| Evidence | SHA-256 |
| --- | --- |
| `verification.json` | `fd7eaa18164826d4ef8b9fbf216cef8378c947e790bd4feb19a10d6fae8010a1` |
| `build-manifest.json` | `e58f674c48ecc4a5c0cfbf30b31c85a1946b4faa9c2a80d1c187498cde0cff25` |
| `hyperrig_effect_parameters.pi32v2.o` | `cffc167e730b64a3d91967404e2eb2f0748b150a100cb9aa3f8f987f0567c823` |

These are finite offline comparisons and relocatable objects, not a complete
firmware build or a hardware/audio result.
