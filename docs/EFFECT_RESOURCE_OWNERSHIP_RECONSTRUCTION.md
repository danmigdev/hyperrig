# Effect resource recovery and ownership integration

This offline milestone connects previously reconstructed parameter callers,
resource recovery and slot teardown. It adds no original function. The three C
translation units are mechanically checked derivatives of frozen sources; all
earlier implementations, images and reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre. The original input and its
required notices remain subject to
[the preserved UltraRig license](../third_party/ultrarig/LICENSE.md).

## Exact integration edges

| Layer | Original body or call site | Joined behavior |
| --- | --- | --- |
| Resource queue flush | `0x0202ed7e..0x0202edb8` | Runs the original queue loop and field writes |
| Direct slot-removal call | `0x0202edaa` to `0x0202eb4c` | Executes the recovered ownership body |
| Allocation recovery | `0x0202edb8..0x0202ee3c` and `0x0202eeba..0x0202eefa` | Real flush, retry and old-buffer restoration |
| Parameter lifecycle | Existing nineteen direct resource calls | Calls the new resource API through its existing explicit bridge |

Removal executes the complete recovered lookup, release, route-detach, capture
ownership and removal bodies, plus the reused reset-slot and request-counter
helpers. The decoder admits exactly that closure. It verifies the new incoming
direct edge against the pinned instruction bytes and rejects unexpected new
call sites. Global refresh and unrelated ownership helpers are not introduced
as implicit replacements for the lifecycle's external services.

Numeric target equality never identifies a platform callback as slot removal.
Allocator, free, mode, alternate-clear and notification callbacks retain their
original call-site argument counts, including tokens equal to reconstructed
entries and a callback token replaced with zero. The installed clear helper
retains its existing narrowly identified internal call site.

## Source derivatives

The new resource translation unit changes only its public symbol/header/type
prefix, inserts one fixed ownership bridge, and replaces the single flush
call with that bridge. The bridge borrows the current map and forwards platform
services through the outer access object; guards propagate to the caller.

The new lifecycle translation unit changes its public symbol/header/type
prefix, rebinds its existing explicit resource bridge to the new API, and uses
the guard-aware scene derivative described below. It
preserves parameter arithmetic, field access order, classification, recursive
tempo handling and private-view lifetimes verbatim. There is no target-only
callback interception.

| Frozen derivative input | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_effect_parameter_resources.c` | `856f0d4de80949a3e83fdb91c0e25bc16746ba29a308fb07d5f3a640f49480e7` |
| `firmware/src/hyperrig_effect_parameter_lifecycle.c` | `a5b3d20f5bdf214b7be0982b4bfff1e7de088a7a391636be4c4d3f0ffa159226` |
| `firmware/src/hyperrig_scene_application.c` | `22063984cc299b97bfc1bf4dd103ce76d251ac7a521e4fbfcf432e493b5ae717` |

`check_derivatives` reconstructs each permitted output from its hash-pinned
input and requires whole-file equality. Focused tests reject edits to ordinary
bodies, error propagation, direct-call substitution and private-flag consumption.
The required third-party notice remains intact in every derived file.

An added scene fallback witness exposed a guard propagation gap: the frozen
scene helper cached its callback window, so an inner ownership guard did not
prevent its later busy-byte clear at `0x01c34489`. The native prefix retained
one while that portable path wrote zero. The witness remains in the corpus.
The new scene derivative changes only its public prefix/header and the service
helper's return sequence: after the nested service returns, it observes a stable
pointer to the lifecycle's error and sets the scene's existing fault state.
The existing `CHECK()` then stops before any further cached-pointer mutation.
The outer lifecycle still returns its original guard status. A null error
pointer retains the frozen standalone behavior. Successful scene execution is
unchanged and remains independently compared.

This prefix claim is specific to the ownership fourth-read guard reached through
the scene's direct parameter calls. It does not establish exact stopping at
arbitrary mapping or budget failures inside inherited transition helpers, which
can retain their own cached-pointer writes before returning to the scene.

## Retained native state and private output

The original comparison model executes decoded instructions on one register,
stack and byte-memory image. Resource calls, ownership calls and their callers
share actual native frames; their output is not replayed as a service result.
Parameter, scene and stage entries remain the complete previously recovered
entries with their existing explicit external dependencies.

During allocation, the original caller's four-byte stack flag remains live
through the allocator, eviction callbacks, restoration and the caller's eventual
load. The portable caller exposes those same initialized bytes through its
borrowed canonical view at `0x31005000`. The comparison checks this flag before
and after each exposed callback, including mutation from nested ownership
release callbacks. It records successful consumption separately from an
unfinished allocation invocation.

The native release helper caches three extra pointers before callbacks. If it
reaches a fourth read at `0x0202df8a`, that read would consume saved caller
registers outside the supported data domain. The portable API returns `-202`
after retaining preceding writes and callbacks. The original model stops just
before that read with its actual frames and pending flag intact. This is a
comparison of an execution prefix, not a claim that original firmware returned
an error. No later flush count clear, allocation retry, IR release or result
publication is fabricated.

The queue behavior remains native: flush clears the slot's queued flag before
removal, rereads its queue count after removal, and clears the count at the end.
Consequently ordinary flush does not invoke removal's all-duplicate queue
compaction branch. Route removal still removes only the first matching route
entry. Callback changes to later list entries, counts, callback tokens, IR
pointers, effect types and capture state remain observable in their original
order. Repeated queue entries still increment the request counter, while
already inactive slots are not released again.

## API and limits

`hyperrig_effect_resource_ownership_execute` exposes the complete resource
entries. Distinct `lifecycle_execute`, `lifecycle_scene` and `lifecycle_stage`
APIs expose the original lifecycle entries. The two IO aliases inherit their
frozen mapping, work-budget and service-budget contracts.

Maps provide pure, stable little-endian storage preserving original address
relationships. Native aliases remain allowed; distinct native bytes must not
acquire additional host aliases. API, IO and result storage remains disjoint
from mapped firmware memory. Original stack `0x30000000..0x30001020` and canonical
private view `0x31005000..0x31005020` are reserved, with the latter available only
through the currently valid borrowed view. Callbacks may synchronously mutate
mapped bytes but cannot reenter, relocate storage or retain borrowed pointers.

Inherited guards retain preceding writes and skip later effects. Results publish
only after success. Work and service budgets bound portable execution, without
claiming a native timing model. Raw byte queue/route counts through 255 are
covered where all accesses map; the API does not limit these counts to ordinary
fixture sizes.

Construction at `0x0202cf62`, other unresolved coefficient/sample services and
platform allocation/free/mode remain explicit boundaries. The constructor's
scripted outputs are not presented as recovered coefficient production. `csync`
retains the existing single-threaded byte-memory model; no peripheral ordering,
concurrency, hardware audio or flashable-firmware claim is made.

## Reproduction and provenance

Use a fresh ignored output directory:

```powershell
python -B tools/build_effect_resource_ownership.py --output build/reverse-effect-resource-ownership-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder captures source hashes before the first compilation, then requires
the comparison report and final read-back to match those bytes. Sources include
the exact derivative inputs, dynamically loaded ISA modules, ISA TOML, input
manifest and recursively included C headers. No older generated report is
needed to reproduce the build.

The comparison checks full public memory, results, ordered callback arguments,
callback-time memory and exposed private flag bytes. The sanitizer replay uses
exact allocations for each public map, verifies all recorded callback mutations
and final bytes, and checks unchanged result sentinels for guarded prefixes.
The native and C sides execute real resource history conversion, clear and
ownership bodies throughout the joined path.

| Pinned input | SHA-256 |
| --- | --- |
| Original Alpha 11 container | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Extracted application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed MINI v4 container | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

All loaded instruction windows and declared static ranges are compared with
the exact MINI image. No new data exclusion is introduced. Independent read-only
review checked the source transformations, original direct-call and flag-load
sites, borrowed flag lifetime, callback collisions and retained fourth-read
prefix. The scene guard propagation received a separate focused review, which
confirmed the exact source difference and the ownership-prefix stop while
retaining the inherited transition-helper limitation above.

## Frozen result

The completed run is `build/reverse-effect-resource-ownership-03`. Its 172
source hashes and 47 artifact hashes were independently read back and matched.
All 38 reused target objects are byte-identical to the frozen lifecycle02 and
ownership01 objects. The ten owned maintained files passed the whitespace and
private-path check.

| Check | Result |
| --- | --- |
| Original/C comparisons | 1,284 |
| Original instruction steps | 1,417,388 |
| Actual flush-to-removal calls | 2,315 at the single approved direct site |
| Parameter-to-resource calls | 2,536 across all nineteen direct sites |
| Completed native allocation-flag lifetimes | 208 |
| Callback mutation cases / carried calls | 112 / 34 |
| Original fourth-read prefix comparisons | 35, including scene fallback |
| Focused native and derivative tests | 19 passed |
| C-only API guard checks | 32 passed |
| ASan/UBSan replays | All 1,284, including all 35 prefixes; six additional API checks |
| Host and pi32v2 builds | Passed; 41 target objects |
| MINI v4 binding | 15,749 instruction windows and 30 static windows identical |

Comparisons include 651 immediate parameter updates, 326 fast updates, one fast
wrapper, 140 probes, 28 stage calls, 41 scene calls, 73 direct flushes, twenty
direct delay allocations and four extra-state allocations. Initial histories
are fixtures; the reached resource migration, clear and teardown code executes
its recovered bodies. Platform responses remain explicit service fixtures.

| Frozen artifact | SHA-256 |
| --- | --- |
| `verification.json` | `b876adaa7a7dbd23108f8d943058e9fd39d12a9a6d77d088ffded8473f2806fd` |
| `build-manifest.json` | `474fdd9c95a2ba8baf80d9422ca33c0a0855f482415d98831f2f3096d2d1cbed` |
| Resource derivative target object | `f3bb4a7fdf2654d48a82a4569a3e9155909e53d82e3d39173e8d588cad1bc0ba` |
| Lifecycle derivative target object | `68c12b24faee55dc3cee46ccd49840e7e43f0512be87a79641802d6592511837` |
| Scene derivative target object | `7f0e71fbceedffa70256a946c2ab08dc1a968e321fffc99bd9885fd60ba6a1e1` |

Incomplete candidates `-01` and `-02` remain preserved without verification
reports. The first stopped during compilation for an EOF formatting correction;
the second stopped when the sanitizer harness passed a lifecycle IO object to
the separately typed resource API. The final harness uses the proper resource
IO type. These packaging corrections did not change the reviewed semantic C
or native model.

## Integration coverage limits

This corpus visits **1,476 of 1,732** instructions in the joined scope:
769/994 parameter instructions, 564/579 resource instructions and 143/159
ownership instructions. The larger inherited decoder visits 3,131/15,749.
These are this corpus's counts, not a sum with historical coverage and not an
overall firmware completion measure. The report lists every missing address.

The 256 unvisited joined instructions have these boundaries:

| Missing instructions | Reason |
| --- | --- |
| 139 in the three classifier helpers | The integration's supplied constructor outputs exercise a limited subset of automation word classes. |
| 73 reachable fast-update instructions | Additional readiness, boolean, timing, existing-record reuse, delta, duration and fallback paths are not selected. |
| One at `0x0202f960` | The previously established type-five entry invariant excludes the contrary assignment. |
| Nine immediate-update instructions | Other normalization, available-state, IR rollback and stored-logical-value alternatives are not selected. |
| Three probe instructions | The increased-cost arithmetic alternative is not selected. |
| Three resource fingerprint instructions | The type36/type37 unity-gain alternatives and type8 signed derived value at least 65,536 are not selected. |
| Eleven global IR-source instructions | These fixtures do not select the nonzero global-count source/callback path. |
| One at `0x0202ee7a` | The history cursor fixtures do not wrap a decoded source index past the old logical count before switching to the tail. |
| One at `0x0202de8a` | Detach supplies a nonnull output-index pointer to lookup; the null-output return is outside this joined call path. |
| Fifteen at `0x0202eb88..0x0202ebac` | Flush clears the queued flag before removal, so the all-duplicate queue-compaction branch is not entered on this direct path. |

The standalone resources01 and ownership01 reports exercised all of their
complete bodies. Their earlier evidence remains separate. Parameter03 retains
its broader caller and classifier evidence. Reaching every direct integration
edge does not imply that every callee branch was reached in this corpus.
