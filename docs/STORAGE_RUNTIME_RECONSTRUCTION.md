# Storage runtime integration

This module joins the recovered preset preparation, journal byte-view,
storage-control and storage-coordination bodies at their original direct call
sites. The complete closure contains 75 existing bodies and 2,283 decoded
instructions. It adds no original function and no immutable-data exclusion.
The original side executes one shared register, stack, RAM and CPU context;
the C side uses checked derivatives of the frozen preparation and driver sources
and the unchanged coordination implementation.

This is offline reconstruction. The serial-flash fixture responds to actual
decoded MMIO transactions, but is synthetic. No pedal, USB interface or physical
storage was accessed. Returned lengths do not establish persistence, durability,
physical timing, atomicity, interrupt delivery, scheduling or inter-core ordering.
The required third-party notice is retained; see
[the license](../third_party/ultrarig/LICENSE.md). The code is reconstructed from
the pinned binary, not recovered original source.

## Public entries and direct joins

`hyperrig_storage_runtime_execute(entry, arguments[12], result[2], cpu, io)`
exposes the same eleven preparation entries. All address ends below are exclusive.
The first four incoming words occupy native argument registers; the fifth
`replace_pair` word is the first native stack argument. The portable API copies
all incoming words before any callback. The second result word is zero; void
entries publish zero in both result words.

| Entry | Complete original range | Arguments |
| --- | --- | --- |
| `read_forward` | `02002874..0200287a` | address, destination, bytes |
| `erased` | `0200287a..020028c2` | block address |
| `erase_block` | `02002e08..02002e6a` | block index |
| `write_forward` | `02002fae..02002fb4` | address, source, bytes |
| `ordered_write` | `02002fb4..02002ff6` | address, source, bytes |
| `readback` | `02002ff6..02003040` | address, expected bytes, length |
| `replace_pair` | `02003040..020031be` | pair index, first record, first size, second record, second size |
| `prepare` | `020031d4..020034ce` | none |
| `record_copy` | `020077aa..020077ec` | address, destination |
| `preset_write` | `020077ec..02007966` | preset index, header, payload, payload bytes |
| `invalidate` | `02007966..02007976` | preset index |

The report enumerates all 75 complete ranges, hashes and instruction counts.
They comprise eleven preparation bodies, ten existing dependencies, 45 driver
bodies and nine coordination bodies. The coordination rate helper is already
among the ten dependencies and is counted once.

Every join authenticates both the original direct instruction and its target
and arity before dispatch. No target-only or indirect callback replacement is
used. All eighteen sites are exercised in the joined corpus.

| Original call site(s) | Actual recovered target | Arguments |
| --- | --- | --- |
| `02002876` | `02002810`, storage read | address, destination, bytes |
| `02002dc2`, `02002f36` | `02002772`, ensure device | none |
| `02002dc6`, `02002f3a` | `02002bcc`, read mode | none |
| `02002dd2`, `02002df2`, `02002f40`, `02002fa2` | `02002786`, activity | value |
| `02002de4` | `02002b80`, device control | unused handle, command 200, page address |
| `02002f74` | `02002ef2`, storage program | unused handle, source, bytes, address |
| `02002dcc`, `02002e02` | `02002d06`, coordination gate | enter/release |
| `02002e12` | `02002920`, ready wait | none |
| `02002dee`, `02002f9a` | `02002d70`, timed event | kind, address, earlier timestamp |
| `020034bc`, `0200795c` | `02002d10`, notification | kind, first payload, second payload |

The remaining 35 direct platform sites and their argument counts are retained
explicitly in the report. The reused driver and coordination modules also retain
their MMIO/cache and CLI/STI/CNUM/TESTSET observations. Callback mutation remains
visible at original reload points. Initial BSS records and IRQ words are runtime
state supplied by the caller, not implicitly reset by this API.

## Checked source derivatives

The model checks exact frozen parent hashes and reconstructs each complete new
source text from a restricted transformation before decoding or verification.
Focused tests deliberately alter an unchanged preparation condition and a driver
polling constant and require rejection.

| Frozen parent source | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_preset_storage_preparation.c` | `553d68066bc3337883cb02025c139dcdedc59f4649c60dba98e0e2629b8257cf` |
| `firmware/src/hyperrig_storage_control.c` | `7a7fdf7fcfb6bb4af30101694f0dd4a5dfd613661c9a097e59f3aeba0b026238` |
| `firmware/src/hyperrig_storage_coordination.c` | `8b38e68971db73c27c54eae0fbfe6daf6fef59c1c335c9780d0f713cf0db5aa3` |

The preparation derivative renames the API, adds retained CPU/event bookkeeping,
replaces its former external bridge with site-authenticated child execution,
and shares external service/event allowances. The driver derivative renames its
API, adds an internal private-buffer lease and completed-store notification,
and keeps callback maps public-only. The original preparation algorithms,
journal byte-view algorithms, 45 driver bodies and nine coordination bodies are
otherwise preserved by the exact checks. Original notices remain intact.

One explicit first-fault substitution is also checked. After an allocator
callback, the private-token rejection runs only if no earlier error exists.
Without this condition, an allocator that first faults through its borrowed map
and then returns a private token could replace the first `-201` or `-203` with
`-202`. A matched original/C mapping witness and a separate C-only work-budget
witness preserve the first fault and leave output results untouched. Frozen
parent files remain unchanged.

## Private-buffer leases and initialized bytes

Maps are pure, stable borrowed byte storage preserving original address
relationships and aliases. Individual accesses cannot cross the uint32 address
boundary; successive byte accesses may wrap between mapped spans. Original code
and branch/static tables are immutable. IO, CPU, arguments, results and callback
bookkeeping are disjoint from mapped RAM. Callbacks cannot reenter, retain views,
relocate memory or mutate CPU state.

The original private stack `30000000..30001040` is never public memory. Only the
active native read or program argument grants the internal driver a lease.
The lease covers exactly the original argument span within the live parent
frame, expires when the child returns or faults, and cannot expose adjacent
locals or saved registers. Program source leases are read-only. Platform,
MMIO/cache and CPU-observation callbacks keep public-only maps even while an
internal lease exists.

| Parent frame | Private payload evidence |
| --- | --- |
| Preparation, 220 bytes | footer `sp+68/16`, record header `sp+28/40`, recovery headers `sp+8/20` and `sp+152/20`, explicitly initialized four-byte markers at `sp+4` and `sp+148` |
| Pair replacement, 84 bytes | eight-byte pair/generation at `sp+24`, four-byte magic at `sp+20`, four-byte invalidation at `sp+16`, then actual readback comparisons |
| Erased check, 272 bytes | 256-byte private read buffer at `sp` |
| Readback, 160 bytes | private read buffer at `sp`, bounded by the smaller of remaining bytes and 128 |
| Record copy, 56 bytes | 40-byte private header at `sp`; at a top-level entry its address is `30000fc8` |

The table describes original frame sizes including saved state; it grants no
access to the rest of a frame. Read/write forwarders, journal writes and journal
erases preserve their original four-, 36- and 16-byte frame depths.

Obtaining a writable private pointer does not initialize bytes. Only completed
internal driver stores mark the exact written bytes; adjacent bytes remain
unproven. Read leases require initialization already established by parent or
driver stores. The native model retains proven payload bytes across stack-depth
changes because the original CPU does not erase the stack on return. Existing
save-register abstraction is retained; it is not promoted to arbitrary known
payload bytes.

For read modes at least eight, the original low-level branch may perform no
destination stores while its outer wrapper still reports the requested length.
The integration preserves that returned value. If the caller then reads an
unavailable private payload byte, verification stops at a portable knowledge
guard; it neither invents data nor labels the original call a failed read. The
top-level record-copy witness reaches `020077be` with no known header bytes.
Partial-read budget witnesses retain only the actually written private prefix.

## Error and budget boundaries

Portable statuses are `-200` for invalid API, `-201` for an unavailable or
individually wrapping mapped span, `-202` for forbidden/private/uninitialized
data, `-203` for a finite budget, and `-204` for observing the original fixed-PC
fatal loop. They preserve earlier public RAM/CPU effects and suppress subsequent
parent cleanup, writes and output publication. They are not native return codes
or resumable execution states. Native returned words publish only after a
successful complete return.

External service and event allowances are shared across every child. An internal
join consumes no external service allowance. Admission occurs before the next
observed boundary effect; CPU effects and their callbacks follow the unchanged
coordination event contract. Matched service/event limits compare the resulting
original instruction prefixes, memory, CPU state and full observation timeline.

The separate portable work limit counts preparation operations and borrowed
maps. Each unchanged child additionally applies its local work ceiling equal to
the parent's remaining work at child entry. This is not one native instruction
counter or a cycle estimate. Work failures are C-only safety evidence unless a
specific original stop is independently matched. No arbitrary work-prefix
equivalence is claimed.

The full 50,000,000-iteration transfer and 5,000,000-iteration busy constants
remain unchanged. Their complete timeout outcomes are not executed by this
corpus. The driver fatal self-loop remains a fixed-PC observation and is not
reached through these preparation entries.

## Comparison fixture and remaining boundaries

The fixture parses serial commands from actual chip-select, control and data
register events. It supplies synthetic flash reads and publishes synthetic
program/erase operations on chip-select transitions. Neither the native nor C
side replaces the recovered high-level read, program, erase, wait, notification
or coordination bodies with scripted results. Both sides use separate fixture
instances and compare final fixture state, pending transactions and observations.
This demonstrates agreement under the specified bus behavior, not hardware
equivalence.

The corpus covers cached and cold discovery, actual footer/header reads,
replacement and readback, carried writes and preparation, recovery with valid
and invalid CRC, zero-length records, capacity failures, callback changes to
later reads, raw gate and CPU state, overlapping public buffers, wrapped byte
destinations, invalid-input ordering and shared service/event exhaustion. A
stale free-slot classification drives a real failed readback and retry; a
separate recovery case supplies an actually erased free slot. A fixture that
accepts program commands but does not persist them preserves reported lengths
and makes the original later readback reject the replacement.

Synthetic read modes zero through five and unsupported modes eight, nine and
fifteen are exercised. Other raw driver commands remain loaded but are not all
reachable from these eleven public callers. Joined instruction coverage and
every missing PC are reported separately from the frozen standalone driver and
coordination coverage. No claim of complete physical-storage recovery follows
from this integration. Typed journal rewrite/append entry integration and the
remaining platform services are outside this module.

## Reproducibility and provenance

Run from the repository root with the available host and pi32v2 toolchains:

```text
python -B tools/build_storage_runtime.py --output build/reverse-storage-runtime-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The output directory must be new and remain under ignored `build/`. The builder
captures all source hashes before the first compiler call, builds the host
library and target objects, runs focused tests, writes original/C fixtures,
and replays those fixtures under ASan/UBSan with exact-allocation maps. It then
checks the source set and bytes again and records artifact hashes. Recursive C
headers, dynamically loaded Python decoders, local ISA TOML/semantics and input
manifests are included; earlier ignored reports are not required inputs.

| Input | SHA-256 |
| --- | --- |
| Original packed Alpha11 M5.71 application | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Original decoded application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed MINI v4 packed image | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

Verification binds every one of the 75 complete ranges and all 2,283 loaded
instruction windows to the pinned image. MINI binding compares those same
ranges, the existing 32 branch-table/padding bytes, the 22-byte BSS reset witness
and eight initial IRQ-counter bytes. The last two are auxiliary evidence, not
new immutable data. Five exact CPU/ISA records and the existing branch table
proofs are inherited and hashed with their source inputs.

An independent reviewer checked the source transformations, bridge/lease design,
initialization rules, shared budgets and first-fault correction before final
packaging. Frozen preparation, control and coordination sources and all earlier
firmware and evidence remain unchanged.

## Frozen validation result

The final evidence is in ignored `build/reverse-storage-runtime-01/`.

| Check | Result |
| --- | --- |
| Original/C comparisons | 135 passing |
| Original instruction steps | 1,110,907 |
| Authenticated direct joins exercised | 18 of 18 |
| Joined instruction coverage | 1,701 of 2,283 |
| Matched portable-failure cases | 66 |
| Focused native/model tests | 16 passing |
| Separate C-only API checks | 31 passing |
| ASan/UBSan original-fixture replays | 135 passing, five exact-allocation maps |
| Additional sanitizer lease/first-fault guards | 15 passing |
| pi32v2 target objects | 13 compiled |
| Frozen dependency target objects | all eleven byte-identical to prior outputs |
| Source/artifact read-back | all 96 source and 19 artifact hashes match |

The remaining 582 loaded instructions are listed individually and grouped by
complete function in the report. They include raw control/status commands not
selected by preparation, unused banking/read branches, preparation failure
branches, memmove alternatives and coordination wait/gate paths. They are not
counted as executed by borrowing prior standalone coverage. The complete driver
timeout outcomes and fatal self-loop remain outside this joined execution
corpus as stated above.

The verification report SHA-256 is
`dc170cdf97207efa912e242a03f712ccc7cfd5ceafd9fda22283bfb6524b5454`.
The build manifest SHA-256 is
`03ae57ab91eeb21583cd47b668677305b4832e2fd08c5bf559ce4a451d593b16`.
The final read-back compares each of the eleven reused target objects with its
frozen preparation02 or coordination01 counterpart. The privacy scan of this
module's ten maintained files found no local user path, credential or key.
No original firmware image or earlier report was changed.
