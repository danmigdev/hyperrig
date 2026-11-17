# Parameter, ownership and numerical construction integration

This offline checkpoint connects three previously explicit parameter calls to
the recovered model-construction closure. It adds no original function or
static data exclusion. Earlier sources, reports, images and licenses remain
unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

See [the preserved license](../third_party/ultrarig/LICENSE.md).

## Exact direct edges

| Original site | Original target | Input and resulting state |
| --- | --- | --- |
| `0x0202f37c` | `0x0202cf62` | Constructs the live effect after the committed parameter write |
| `0x0202f970` | `0x0202cf62` | Constructs the original `PROPOSED` record at `0x01c33610` before comparing its derived words |
| `0x0202f7ba` | `0x0202cd32` | Updates the live object's coefficients on the special fast path |

Each call supplies one effect token in `r0`; it is a void callee that writes
the mapped state.
The complete object builder is `0x0202cd32..0x0202cdba`. The main constructor's
six internal model-builder calls execute the unchanged numerical closure.

The new program decodes and merges the frozen ownership and constructor
programs. It rejects any incoming direct edge other than these three. Their
union contains 20,072 loaded instructions: 15,749 ownership-context instructions
plus 4,775 constructor instructions, with 452 shared instructions counted once.
The declared join contains 107 previously reconstructed whole regions. The
54 named immutable-data bindings cover 51 distinct exact spans, including
exactly the original portions of model tables. The bindings total 5,544 bytes;
their union is 5,380 bytes. Inherited role names repeat the selector range
`0x0203b880..0x0203b8d4` twice and capability range
`0x0203b480..0x0203b4a8` three times. These duplicate bindings do not expand
the known data extent. No adjacent gap, unread suffix or new data exclusion
is inferred, and none becomes a new reconstruction claim.

## Checked source derivative

Only the lifecycle translation unit is derived. Its parent is
`firmware/src/hyperrig_effect_resource_ownership_lifecycle.c`, SHA-256
`6c988de86e765ecec79cb72141b9af0d88994b8519caa76e7779a95fb6c322a2`.
The checker reconstructs the permitted output and requires whole-file equality:
public lifecycle prefix/header changes, one borrowed constructor bridge and
the three exact direct-call substitutions. All ordinary parameter expressions,
native copies, resource bridges, private-output lifetimes and scene error
wiring remain unchanged.

Numerical/model, resource, ownership and guarded-scene C units are linked
without editing them. Constructor address equality is never a platform
callback classifier. Allocator, free, mode, alternate-clear and scene
notification callbacks retain their original sites and argument counts,
including tokens equal to either constructor entry.

## Shared memory and ownership

The public `hyperrig_effect_parameter_construction_execute`, `scene` and
`stage` APIs retain the lifecycle IO and entry contracts. `PROPOSED` and
`PREVIOUS` are the original native 480-byte copies, not portable runtime
snapshots. Their embedded pointers still address the live mapped objects.
Writes through those pointers are visible to the caller and later services.

The native model uses one register file, return stack, original byte memory
and predicate/parallel-packet state. A numerical instruction view borrows
those objects; it neither reconstructs state from a host runtime nor injects
coefficient results. Shared support routines keep the existing caller's byte
mapping and live private-output handling.

Allocation recovery retains the complete queue flush, ownership teardown,
retry/restoration and migration behavior. The initialized four-byte flag at
the live original stack address remains exposed through canonical borrowed
view `0x31005000` until the caller consumes it. No other original stack bytes
become public data. Immutable original code/tables remain read-only. All prior
native-alias, stable-map, callback-lifetime and reached numerical requirements
remain in force.

## Guard and budget propagation

The first outer fault wins. Prior writes and callbacks remain visible, later
mapped work and external services stop, and results publish only on successful
completion. Statuses `-200`, `-201`, `-202` and `-203` mean invalid API, mapping
failure, reached domain boundary and budget exhaustion. Calls cannot resume
after a portable guard.
An inherited nested helper receiving a zero remaining work cap retains its
invalid-API `-200` result. The dedicated work-cap-16 witness reaches this
existing boundary before the parameter write and constructor call; the new
integration does not normalize it to `-203`.

The constructor receives the outer remaining work allowance as a local cap.
Its mapped accesses also consume the caller's work budget. Numerical iterations
consume the constructor's local cap; the frozen constructor does not return a
remaining-work counter. This is nested portable accounting, not a unified
operation counter or native timing measurement. Only actual external services
consume the outer service budget.

The unchanged guarded-scene API observes `outer_error` immediately after each
nested service. Its existing `CHECK()` therefore stops before later cached
pointer writes, including the busy-byte clear. Dedicated zero-rate fault checks
exercise inner/apply/select/flush and unchanged result sentinels. These are
C-only guard checks. Four additional mapping-fault witnesses reject the exact
four-byte mapping request for the second constructor output after the scene
has obtained its larger cached byte view. They retain the first output and
all untouched later words while preventing the scene busy-byte clear. This
injected mapping failure is a portable guard check outside the fully mapped
native execution domain. Only the previously established ownership fourth cached
pointer read has an explicit original execution-prefix comparison; this module
does not generalize that claim to arbitrary constructor fault prefixes.

## Evidence and reproduction

The corpus compares scalar results, all public mapped bytes, ordered external
services with their before/after states and arities, original private flag
observations, actual construction/resource/ownership entries and carried stage
state. Coverage records every joined and loaded gap separately. Existing
standalone numerical coverage is not added to this integration's executed
counts. This is neither a full-firmware runtime proof nor a hardware/audio test.

The standalone builder binds local transitive sources, recursive headers,
dynamic ISA helpers, ISA TOML and exact original/MINI instruction/data windows.
It does not require an earlier ignored report list to discover compilation
inputs. It produces strict host and pi32v2 objects, focused tests and
exact-allocation ASan/UBSan replays in a fresh ignored output directory:

```powershell
python tools/build_effect_parameter_construction.py --output build/reverse-effect-parameter-construction-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

## Frozen results

The selected build is `build/reverse-effect-parameter-construction-02`.
All 625 C/original comparisons pass in 3,377,747 decoded instruction steps.
The corpus includes 160 calls with carried state, 60 actual processing frames,
12 live object/field overlap cases, eight callback-mutation cases and 47
observed allocation-flag lifetimes. The three direct sites execute 307 live
constructor calls, 229 `PROPOSED` constructor calls and 85 object-builder
calls. The numerical model observes 164 coefficient requests and 8,263
exponential calls; their outputs are executed rather than supplied by fixtures.

| Instruction scope | Decoded | Visited | Unvisited |
| --- | ---: | ---: | ---: |
| 31 inherited parameter/resource/ownership declarations | 1,732 | 1,356 | 376 |
| 76 inherited constructor/math declarations | 4,775 | 4,385 | 390 |
| All 107 named joined bodies | 6,507 | 5,741 | 766 |
| Full loaded caller/dependency context | 20,072 | 7,469 | 12,603 |

The report retains every unvisited address both per body and in the complete
joined/loaded lists. These gaps are unexecuted by this corpus; earlier
standalone observations are not merged into these counts. No original
function or instruction is newly reconstructed by this integration.

Strict host and pi32v2 builds pass, producing 44 target objects. All 43
inherited objects match the frozen parent builds byte for byte. The 18 focused
native tests and 27 C-only API/guard checks pass. Exact-allocation ASan/UBSan
replay passes all 625 comparison records, including 35 established ownership
execution-prefix stops, plus eight C-only scene guards and six invalid-API
checks. The full 20,072 instruction windows and all 54 named static bindings
match the pinned MINI v4 image locally.

All 194 source bindings and 50 artifact bindings were independently read back.
The final report SHA-256 is
`5221f339f3dffbac52b461cc9531c2c39eff8109e2a95a168959e53fc8127427`;
the build-manifest SHA-256 is
`bc6ddb5fbdfd52bd281009edeee0184a3595dc669f700fa0ddd7e88cb5312d19`.
The new C source SHA-256 is
`b337edb670dc6585e331eaf9c1550bc03ce3f1367f34c8ef297fd3cf36c73033`.
Build `-01` remains preserved but is not selected: its additional sanitizer
fixture omitted the immutable helper-table mappings after its successful
comparison replays. Build `-02` binds the corrected fixture; the numerical
library, all 44 target objects and comparison outcomes are unchanged.
