# Effect routing and ownership reconstruction

This module reconstructs eight complete Alpha 11 M5.71 routines for route
lookup, neighboring group flags, buffer release, slot teardown, capture-pool
ownership and global refresh. Their C implementations compare against decoded
original instructions on shared synthetic byte-addressed memory. The two
previously recovered reset/counter helpers are reused through faithful borrowed
storage adaptations and original instructions.

This is reconstructed C, not the original source. Preserve the required
copyright notice and [third-party license](../third_party/ultrarig/LICENSE.md).
No original firmware image, earlier reconstruction or prior report is changed.

## Complete scope

| Entry | End, exclusive | Operation |
| --- | --- | --- |
| `0x0202de50` | `0x0202de8c` | Find the first route occurrence and optionally store its index |
| `0x0202de8c` | `0x0202def2` | Repair a slot's group flag from its neighbors |
| `0x0202df38` | `0x0202df9a` | Detach and release the main and cached extra buffers |
| `0x0202eabc` | `0x0202eb0c` | Remove the first matching route occurrence |
| `0x0202eb0c` | `0x0202eb4c` | Release the selected capture-pool ownership bit |
| `0x0202eb4c` | `0x0202ebe2` | Remove a live slot, its route/queue state and owned resources |
| `0x0202ebe2` | `0x0202ec30` | Count consecutive groups of nonzero route flags |
| `0x0202ec30` | `0x0202ec54` | Conditionally request the global refresh service |

These bodies contain **668 bytes and 236 instructions**. Reused complete helpers
are slot reset `0x020290cc..0x02029112` and counter update
`0x01c05160..0x01c0516e`, adding 28 decoded instructions. There are no embedded
data tables in this new scope. The public scalar returns belong to lookup,
removal and group counting; void results and the second output word are zero.

## Ordering that remains visible

Lookup searches the first chain before the second and writes the optional
output index only after finding a match. The output pointer can alias route or
count bytes. Neighbor repair retains an unusual original distinction: lookup
finds the slot's index, but the supplied caller chain selects the neighbors.
The C does not substitute the chain returned by lookup.

Route detachment removes only the first occurrence. Slot teardown separately
removes every occurrence from the pending queue when its queued flag is set.
Queue count is cached before compaction. Byte counts up to 255 retain their
original reads and writes, including overlap with other fields in the mapped
control block; the API does not impose fixture-sized route or queue limits.

Buffer release caches the main pointer, extra count and exactly three extra
pointers before any callback. It clears the corresponding published fields,
then checks the configured release callback. The main pointer uses that cached
callback token. Every nonzero extra pointer reloads the current callback token,
even if an earlier callback changed it to zero. Numeric tokens equal to any
recovered entry remain explicit indirect calls with one argument.

Zero is tested as an external callback token after the original nonzero check;
this establishes ordered callback forwarding, not that address zero is a valid
function in a running device. Platform memory ownership, actual deallocation
and callback execution remain outside the reconstruction.

Complete slot removal increments the request counter even for an invalid or
already-disabled slot. For a live slot it resets automation, detaches its first
route occurrence, compacts the queue and clears enabled/live fields before
releasing buffers. It then reloads the IR source pointer and callback. Later
type/capture fields are also read after callbacks, allowing their synchronous
mutations to affect the remaining teardown.

Capture ownership uses the wrapped pointer difference from `0x01c2fa38`, signed
division by 888, and the low five bits of the quotient for the inverse-bit
operation. The ISA model binds that shift-index behavior to the pinned
`and.invbit.rrr` semantics. The original `csync` instruction has no additional
effect in this synchronous byte-memory model; no peripheral or inter-core
ordering claim is made.

## Private-stack boundary and guards

The extra-pointer count is a byte, but the original routine caches only three
pointer words in its private stack array. If a fourth read is actually reached
at `0x0202df8a`, it would read saved caller state beyond that array. The portable
API returns `-202` at that point, after preserving all earlier writes and
callbacks. The native verifier stops before the same instruction and compares
the full public-memory and callback prefix. This is an observation boundary,
not an original firmware return.

The guard is lazy. A count of 255 with no initial release callback clears the
fields and returns normally because the pointer loop is never entered. A
callback that changes the current count does not alter the cached count.
Changes to callback tokens likewise do not bypass a reached fourth read.

Mapped storage must preserve original address aliases and provide each accessed
span without crossing 32-bit address wrap. Address arithmetic between separate
accesses may wrap. Native effect/output tokens and host byte storage may be
unaligned. The original private stack `0x30000000..0x30001020` is reserved and
cannot be supplied as ordinary mapped data. API, IO and result objects are
disjoint from mapped bytes.

Maps are pure and stable. External services may synchronously mutate mapped
bytes but cannot relocate storage, retain views, alter API objects, reenter or
run concurrently. Guards retain prior writes and leave the result sentinel
unchanged: `-200` invalid API or missing reached service, `-201` missing/wrapped
mapping, `-202` private-stack domain, and `-203` finite budget exhaustion. The
work budget is a portable bound, not a cycle estimate.

## Comparison and reproduction

Only release callbacks and global refresh `0x02028eb2` remain explicit external
services. Direct calls among all eight routines and the two reused helpers
execute decoded original bodies. Source/target callback-token collisions are
resolved by the actual call site rather than by recognizing target values.

The corpus covers lookup output aliases, first duplicates, differing caller and
found chains, all 256 eight-slot group-flag patterns on both chains, route/queue
counts through 255, pointer/count combinations, unaligned and wrapped native
tokens, callback replacement and zero tokens, delayed mutable fields, invalid
and repeated removal, and reached fourth-read prefixes. Focused assertions
check the intended original outcomes independently of the portable C.

The sanitizer replay allocates each mapped region exactly, with separate host
alignment offsets where requested. It replays the native callback mutations,
checks ordered arguments and return values, and verifies the complete final or
guard-prefix state. Guard replays also require unchanged output sentinels.

Use a fresh directory:

```powershell
python -B tools/build_effect_ownership.py --output build/reverse-effect-ownership-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The build is independent of earlier ignored reports. It compiles host and
pi32v2 C, runs focused original witnesses, performs full original/C comparisons,
and replays them under ASan/UBSan. Provenance includes dynamically loaded ISA
Python modules, ISA TOML, the input manifest, and recursively included C headers.

| Pinned input | SHA-256 |
| --- | --- |
| Original Alpha 11 container | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Extracted original application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed MINI v4 container | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

All decoded instruction windows are compared with the reviewed MINI image.
Independent review checked the native bodies and the expanded corpus, including
cached pointers, callback replacement, queue/route ordering and partial-write
guards. No semantic C or native-model correction was needed after that review.
This remains offline evidence, with no hardware, physical audio, scheduling or
flashable-firmware claim.

## Frozen verification

The completed run is `build/reverse-effect-ownership-01`. All 49 recorded source
hashes and seven artifact hashes were independently read back and matched after
the build. The eight maintained files passed the whitespace and private-path
check. Earlier sources, reports and firmware images were unchanged.

| Check | Result |
| --- | --- |
| Original/C comparisons | 1,536 |
| Original instruction steps | 162,551 |
| New instruction coverage | 236 / 236 |
| Combined instruction coverage | 264 / 264 |
| Focused native tests | 20 |
| C-only API guards | 17 |
| ASan/UBSan original-fixture replays | 1,536, including 20 fourth-read prefixes |
| Callback-mutation cases | 32 |
| Carried calls after the initial invocation | 3 |
| Host and pi32v2 builds | Passed |
| MINI v4 instruction windows | All 264 identical |

The comparison counts by entry are: lookup 184, neighbor repair 97, release 177,
detach 64, capture ownership 370, removal 96, group count 542 and refresh 6.
There are no unvisited instructions in this corpus. Instruction coverage does
not establish every possible state or callback interaction; the mapping,
private-stack, budget and external-service limits above still apply.

| Frozen artifact | SHA-256 |
| --- | --- |
| `verification.json` | `7bd5c7db71a52144579e7ef8747f9d93535a2ee93605e6b26eb5253a6e5f995b` |
| `build-manifest.json` | `34b2b0a5d970ac8e2d35de9e7a1407180abf5a34dd436ce862c17bf8535a158c` |
| `hyperrig_effect_ownership.pi32v2.o` | `b34df3a438d9e730278009e1fd7bc3552160c1bec9f351899f34a3084fcb1caa` |

The manifest binds the verification report, host library, target object, focused
test log, sanitizer executable/result and complete native replay fixtures. The
report separately binds source inputs and the ordered output, memory and service
comparison digest. No report or generated binary belongs in Git.
