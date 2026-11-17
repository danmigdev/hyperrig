# IR effect lifecycle reconstruction

This checkpoint recovers nine complete original M5.71 bodies that select an IR
source, install it temporarily, assign it to an effect, restore ownership on
failure, forward a copy construction request, and relocate an existing object.
It adds no firmware features or hardware evidence. The portable implementation
is reconstructed source, not the original source code.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

See [the preserved license](../third_party/ultrarig/LICENSE.md).

## Scope and original ABI

Addresses are original addresses, and upper bounds are exclusive. The first
four argument words use `r0` through `r3`; later words use the caller's stack.
The portable API accepts twelve words, using only the listed entry's arguments.
It returns a portable status separately from the original scalar result.

| Entry | End | Arguments | Behavior |
| --- | --- | --- | --- |
| `0x02029728` | `0x0202976a` | effect | Mode notification, preparation, optional mode-zero retry, final notification |
| `0x0202976a` | `0x0202983a` | effect, direct source, count, length, gain word, format, stored slot, identity | Temporary global source installation and restoration; optional read allocation |
| `0x0202983a` | `0x020298ce` | effect | Select local or global source; evaluate the local signed gain metadata |
| `0x020298ce` | `0x02029920` | slot | Validate and refresh one active type-7 effect |
| `0x02029920` | `0x02029ae6` | slot, source, count, gain metadata, format, stored slot, identity | Copy or reference source, trim, prepare, commit or restore ownership |
| `0x02029ae6` | `0x02029afc` | slot, source, count, gain metadata, format | Assignment with zero stored slot and identity |
| `0x02029afc` | `0x02029b2e` | slot | Query whether the active type-7 effect has a local pointer or stored slot |
| `0x02031bf8` | `0x02031c16` | destination, source, count | Call construction with destination, count, copy producer `0x020315b8`, and source |
| `0x02031c16` | `0x02031c64` | object, previous base | Relocate nine pointer words at offsets 20 through 52 if object word zero is nonzero |

Relocation has no defined scalar return; the portable observer returns zero.
The second result word is always zero. Other native result words, including
negative error values represented as unsigned words, are preserved.

Six previously reconstructed bodies execute original instructions inside this
checkpoint: the mode callback `0x01c05ec6..0x01c05ed6`, signed metadata clamp
`0x01c05eb0..0x01c05ec6`, tail trim `0x020294ce..0x0202957e`, counter increment
`0x01c05160..0x01c0516e`, scaled exponential `0x01c0516e..0x01c05182`, and
exponential `0x020285d4..0x02028646`. They are reused dependencies, not new
original function entries. There are no new embedded data exclusions.

## State and ordering

The control object is at `0x01c32db0`, effect slots start at `0x01c2c220` with
480-byte spacing, the sample reader token is at `0x01c3441c`, and the global
gain word is at `0x01c1f7dc`.

Temporary installation snapshots the five global fields after any allocation
and sample-reader callback. It installs source, count, length, gain and the
normalized format flag in their original order. Preparation may mutate public
memory. The caller then restores the five saved fields before reloading the
release callback and freeing its temporary allocation. Reader failure releases
the allocation without installing those global fields.

Assignment validates unsigned slot indices 0 through 15, a nonzero active
byte, and effect type 7. It clamps signed gain metadata to -60000 through 20000.
A nonzero source can remain associated with a stored slot only when that slot
is 1 through 255 and a reader token exists. Otherwise allocation and the
original forward halfword copy run before the old effect fields are saved.
Forward overlap intentionally propagates earlier writes; this is not a
`memmove` substitution.

The new fields are installed before trimming the original source. Consequently,
source aliases with those fields observe the new bytes, exactly as the native
load order specifies. Preparation failure reloads the current new source
pointer, restores all seven saved fields, and then releases that reloaded
pointer when a release callback exists. Success releases the cached old
pointer, then reloads and increments the global counter modulo 2^32. Callback
mutations to the current pointer, release token or counter are therefore
visible at different, tested points.

The mode wrapper rereads `0x01c1f7d0` after a preparation result of -3. A nonzero
value causes exactly one retry with mode zero. The installed mode callback is
reloaded for each notification. Indirect tokens remain external even if their
numeric value equals a loaded reconstructed function or a direct service.

## Numerical and mapping domains

The implementation uses stable byte mappings, including unaligned host backing.
Individual spans must fit the 32-bit address space, but pointer arithmetic
between accesses wraps modulo 2^32. The corpus includes samples crossing from
the final mapped bytes to low addresses, odd sample tokens, overlapping copies
in both directions, counts through 4096, and large raw counts that wrap the
allocation byte expression `((count << 1) + 2) & 0xfffffffc`.

Local signed gain metadata is not limited to the assignment clamp. Every signed
32-bit value is accepted: conversion, division by the binary32 word for 1000,
multiplication by `0x3debc8e3`, repeated reduction by the original binary32
logarithm-of-two words, the eight-term polynomial, and repeated scaling retain
the original rounding order. The signed extrema are compared directly with
native execution, including underflow to zero and overflow to infinity. The
portable polynomial is borrowed unchanged from the earlier recovered math
module only after the input has been reduced into its supported interval.

Tail trimming retains unsigned 64-bit energy and tail accumulation, signed
16-bit magnitudes, strict energy comparison, and the original 3162 multiplier.
No sample-count ceiling is imposed by this API. Finite work budgets can stop
long copy, trim or exponential loops while retaining preceding public effects.

Work charges one entry unit, each mapped access and each exponential reduction
or scaling iteration. Services have a separate call budget. These are portable
guards, not original clock or instruction counts. The original private stack
reservation `0x30000000..0x30001020` cannot be public input storage. API objects,
arguments, results and mapping storage must remain disjoint. Callbacks may
synchronously mutate public bytes through a borrowed view, but cannot reenter,
retain that view, replace backing allocations, or mutate the API objects. Maps
themselves have no side effects. A stopped invocation is not resumable.

Three selected stops compare against explicit native PC observations rather
than deriving the native stopping point from portable access counts. Two stop
at the fourth copy load `0x020299a4`, after three halfword stores, with ordinary
and `UINT32_MAX` counts. The third stops at the first direct preparation call
`0x02029744`, after the mode notification. Other API, missing-map, wrapping-span,
private-stack and budget guards are labeled C-only. No universal equivalence
of arbitrary mapping-failure prefixes is asserted. The stopped model's -203
status identifies the observer boundary; it is not a native firmware return.

## Explicit boundaries

Preparation `0x0202962a` remains a two-argument direct service. Construction
`0x020318a8` remains a four-argument direct service. Their complete callee ranges
are byte-bound ABI evidence and are not counted as executed here. Their earlier
numerical reconstructions are separate evidence; this checkpoint does not join
selection and assignment through actual convolution construction or runtime.

Mode notification, allocation, sample reading and release remain explicit
synchronous callbacks. Reader ABI is `(stored slot, identity, allocation,
sample count)`; allocation and release each receive one word. Callback arities
and reload points are checked by original call site. No allocator, physical
storage, concurrent task, MMIO, hardware or audio behavior is simulated as
recovered implementation.

## Verification and provenance

The independent model decodes pinned original bytes and executes the original
instructions, stack arguments, parallel packets and shared byte memory. It
does not use portable C output to form expected state. Comparisons check
defined results, all mapped public bytes, ordered callback arguments and
complete callback before/after state. Eighteen focused native tests assert ABI,
rollback, alias, trim, relocation, retry and stop properties separately.

The sanitizer corpus records original state and callback mutations. Its C
replayer retains the same allocations across carried transitions, applies only
recorded fixture edits, and checks complete public-state hashes before and
after each callback and at return. ASan and UBSan replay the recorded cases.
Strict host and freestanding pi32v2 builds link the recovered math sources.

The original image SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The decoded application SHA-256 is
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
The MINI-v4 image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier binds each loaded instruction window and both unexecuted callee
ABI ranges to matching MINI bytes. Original inputs and prior reports remain
unchanged.

The builder captures the complete maintained source manifest before compiling
and checks it against the verifier's final manifest. The manifest includes
recursive C headers, imported models, dynamic ISA semantics, ISA tables and
the pinned input manifest. It does not require ignored prior verification
reports. Fresh ignored build output contains the verification report, exact
original replay corpus, focused tests, sanitizer result, host library, target
objects and their artifact manifest. No generated artifact belongs in Git.

The reviewed, frozen final output is `build/reverse-ir-effect-lifecycle-01`:

- 808 original/C comparisons and 10,291,356 original instruction steps.
- All 422 new instructions and all 537 loaded instructions visited; no
  instruction gaps. This is the declared offline corpus, not all possible
  states or firmware-wide completion.
- 21 callback mutation cases, 112 carried calls, and 696 allocation sets.
  Eight sets each carry fifteen calls; the other 688 are single calls.
- Three fixed-PC prefix comparisons and twelve separate C-only API guards.
- Eighteen focused native tests, 808 ASan/UBSan replays, and one additional
  invalid-API check in the sanitizer harness.
- Five pi32v2 objects. The new lifecycle object is 4,280 bytes; all four reused
  math objects are byte-identical to `reverse-effect-construction-02`.
- 537 instruction windows and two unexecuted callee ABI ranges match MINI-v4.
- All 63 maintained source bindings and all 11 generated artifact bindings
  were rehashed after completion and match their manifests.

The verification report SHA-256 is
`a2ed741717c2c217cacc0bba9f60853f8791b0f2790c49e56f86ee79deae6577`.
The artifact manifest SHA-256 is
`d278d05a21df473a5d907001db3369d698624064a2f4aabefc3a922dd1d37cff`.

The independent review checked the original lifecycle and math listings before
corpus expansion, then reviewed the completed API, rollback and restore order,
callback reloads, full-range gain reduction, prefix observations and retained
replay before the final build. No semantic C change was needed. Earlier
development checks and their replay output remain separate from this final
candidate. All prior reconstruction sources and completed reports remain
unchanged.
