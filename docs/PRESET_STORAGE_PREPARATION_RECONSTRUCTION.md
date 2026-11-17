# Preset storage discovery and transaction preparation

This offline reconstruction closes eleven complete storage discovery, paired
preset write, verification and invalidation bodies from the pinned M5.71
application. It executes the original decoded bodies against the maintained C
implementation, including the previously recovered journal, address, checksum,
comparison, timing and memory-copy dependencies. Physical storage drivers and
platform coordination remain explicit services.

Required Notice: Copyright (c) 2026 Manuel Aguirre. Original input artifacts and
required notices remain subject to
[the preserved UltraRig license](../third_party/ultrarig/LICENSE.md).

## Complete entries and ABI

Ranges are end exclusive. Arguments are unsigned 32-bit words or original
address tokens. The fifth pair-replacement argument occupies the original
incoming stack slot; the reference model executes that stack convention.

| Entry and end | Public operation | Native arguments | Instructions |
| --- | --- | --- | ---: |
| `0x020031d4..0x020034ce` | `prepare` | none; void | 250 |
| `0x02003040..0x020031be` | `replace_pair` | pair, left, left bytes, right, right bytes | 139 |
| `0x02002e08..0x02002e6a` | `erase_block` | block index | 35 |
| `0x02002874..0x0200287a` | `read_forward` | storage address, destination, bytes | 3 |
| `0x0200287a..0x020028c2` | `erased` | storage address | 27 |
| `0x02002fae..0x02002fb4` | `write_forward` | storage address, source, bytes | 3 |
| `0x02002fb4..0x02002ff6` | `ordered_write` | storage address, source, bytes | 30 |
| `0x02002ff6..0x02003040` | `readback` | storage address, source, bytes | 29 |
| `0x020077aa..0x020077ec` | `record_copy` | storage address, destination | 25 |
| `0x020077ec..0x02007966` | `preset_write` | preset, header, payload, payload bytes | 132 |
| `0x02007966..0x02007976` | `invalidate` | preset; void | 4 |

These entries contain 1,926 bytes and 677 instructions. They introduce no
embedded data table or new data exclusion. The ten reused complete bodies are
block addressing, preset addressing, CRC update, journal cache invalidation,
journal write, journal erase, unsigned-byte comparison, calibration scaling,
elapsed ratio and `memmove`. The complete loaded closure has 940 instructions.
Earlier bodies remain identified as reused, rather than counted again.

The generic API is
`hyperrig_preset_storage_preparation_execute(entry, arguments[12], result[2], io)`.
Void entries normalize both result words to zero. Other entries return their
native result in word zero and zero in word one. An original negative result
such as `0xfffffffd` is a completed execution, distinct from a portable guard.

## Native storage behavior

Storage state is based at `0x01c26890`. Discovery uses eighteen 4,096-byte
physical blocks: indices 0..15 map to `0x000bf000..0x000ce000`, index 16 to
`0x000dd000`, and index 17 to `0x000de000`. Each committed pair contains two
records separated by 2,048 bytes. The record header occupies 40 bytes; the
pair writer's native per-record limit is 1,920 bytes including that header.
These layout constants are original behavior, not claims about a physical
driver's storage guarantees.

| State offset | Observed role |
| --- | --- |
| 708 | Checked-preset bitmask |
| 712 | Preparation completed byte |
| 716 | Discovery completed byte |
| 732 | Available-preset bitmask |
| 3440..3457 | Eighteen block classification bytes |
| 3458..3475 | Per-block erase-verification strike bytes |
| 3476..3491 | Sixteen signed pair-to-block mapping bytes |
| 3492 | Next generation word, wrapping as unsigned arithmetic |
| 3496 | Most recently selected block byte |
| 3504 | Erase-fallback counter word |

Preparation returns immediately when byte 712 is set. Otherwise it captures
the clock, performs discovery if byte 716 is clear, allocates 3,840 bytes,
recovers a pending pair transaction when present, fills missing pair mappings,
releases the allocation, emits notification 18 and sets byte 712. Allocation
failure can leave discovery complete while preparation remains incomplete.

Discovery clears the original 68-byte state interval, initializes the sixteen
pair-map bytes to `0xff`, and scans all eighteen footers. A committed footer
contains the pair identifier, generation, invalidation marker and magic word.
For duplicate pairs the unsigned generation comparison chooses the newer
mapping and marks the superseded block as reusable. The factory sentinel pair
`0xffffffff` selects the physical index with generation zero. Generation wrap,
out-of-range pair identifiers and callback changes remain observable.

Invalid footer magic or invalidation marker takes a no-store branch. It does
not overwrite the current classification byte after the read callback. The
comparison corpus retains witnesses where that callback changes the byte to
five, which survives and controls the second scan. A failed footer read has
its own explicit store of five. The second scan examines only classification
zero, recognizes the pending transaction block, and otherwise checks whether
every byte is erased before classifying the block.

Pending recovery reads the transaction header at `0x000de000`, with payloads
at offsets 32 and 1,952. It computes the actual reflected CRC over the pair and
length fields followed by both payloads. A successful pair replacement is
followed by the journal marker write at `0x000deff8`. Read, CRC, pair-write and
marker-write outcomes retain their distinct native paths and notification
packing. A synchronous byte-store fixture exercises these paths; it does not
establish recovery after real power loss.

Pair replacement first performs its native pair/length checks, before any
callback. It searches erased blocks from the current cursor, then tries reusable
blocks with real erase and byte verification. At most two candidate writes are
attempted. It writes record payloads before headers, and header words 4..39
before the magic word. Pair/generation and footer magic follow. It reads back
both records and both footer fields before publishing the new pair mapping.
A failed candidate receives a zero invalidation marker and classification two.
Old mappings and callback changes are read at their original points.

The ordered-record helper preserves a native edge: any nonzero byte count below
40 still writes the 36 trailing header bytes and the four-byte magic. No early
portable rejection replaces that behavior. `preset_write` retains native
allocation, preparation and notification order for invalid preset IDs and
invalid payload lengths. It supports replacement, header-only editing and
deletion while preserving the neighbor record. The existing byte-accurate
`memmove` executes actual overlapping copies; native source, destination and
state aliases are not removed to fit a typed runtime.

## Cache masks and the former preparation boundary

The complete preparation body does not directly write either mask at offsets
708 or 732. It updates discovery state and the pair map. The complete helper at
`0x02007966` clears only the requested checked bit at 708 for IDs 0..31; it leaves
the available mask at 732 unchanged. The previously recovered availability
body at `0x0200cf88` remains the writer that updates both masks after validation.
Unrecovered protocol command callers still determine when writing a preset is
followed by invalidation.

The earlier [storage reconstruction](PRESET_STORAGE_RECONSTRUCTION.md) treated
`0x020031d4` as an external service and allowed it to invalidate cached bits.
The new whole-body evidence supersedes that unproved internal-behavior
assumption. Platform callbacks can still mutate mapped state synchronously;
those effects are distinct from direct stores in preparation. Earlier sources,
captured reports and images remain unchanged.

## Reused journal bodies and borrowed maps

The original instruction model executes the existing journal bodies directly.
The new C translation unit contains narrowly derived byte-map versions of the
frozen journal invalidate, write and erase functions. `check_derivatives()`
recreates their exact source text from the pinned input and permits only native
map accesses, explicit service sites, private-frame accounting and finite-work
guards. It removes earlier typed-API bounds without replacing native checks.
It preserves all other control flow and arithmetic.

The derivative input is `firmware/src/hyperrig_capture_journal.c`, SHA-256
`a3517ca130212467a049d0948cc4c77cf1288f86fb8d8e5bc062b35a21a5e78b`.
This derivative adds no original function. Using maps retains source aliases
with journal cache bytes and callback changes to state offset 280 before the
next page/yield decision.

Maps return pure, stable byte storage preserving original address aliases.
Native and host byte alignment are allowed. Distinct native ranges must not
acquire extra aliases through the host mapper. API, IO, arguments and result
objects remain stable and disjoint from mapped data. Callbacks are synchronous;
reentry, concurrent mutation and retained private pointers are outside the API.

Public and allocated tokens exclude `0x30000000..0x30001040`. The reference uses
the original stack there. The portable API exposes only the original argument
buffer for the current callback: READ destinations permit writes, PROGRAM
sources permit reads, and unrelated private-frame bytes remain inaccessible.
Every private byte read must previously have been initialized. Requesting a
writable map commits the callback to initializing every requested byte; a
failed read may instead request a shorter initialized prefix. Failed reads with
untouched or partially initialized private buffers return through the original
error paths without fabricated reads of the remaining bytes.

Portable guards are `-200` for API/entry errors, `-201` for missing/wrapping
mapped spans, `-202` for private/initialized-memory domain violations and `-203`
for finite work or service budgets. Results publish only after success. Guards
retain previous writes and callbacks and suppress subsequent map/service
effects; they are not original return codes or a proof of identical instruction
prefixes for arbitrary invalid memory. The native valid-input checks retain
their original precedence over these lazy memory checks.

## Explicit platform boundaries and ISA evidence

The decoder verifies all 28 direct external call sites and their argument
counts. There are no indirect calls in this closure.

| Target | Arguments | Boundary |
| --- | ---: | --- |
| `0x02002810` | 3 | Storage read |
| `0x02002ef2` | 4 | Storage program |
| `0x02002b80` | 3 | Storage sector erase |
| `0x0203c15c` / `0x0203d218` | 1 / 1 | Allocation / release |
| `0x01c04862` | 0 | Clock |
| `0x02002d10` | 3 | Notification |
| `0x02002772` / `0x02002bcc` | 0 / 0 | Storage preparation / mode coordination |
| `0x02002786` / `0x02002d06` | 1 / 1 | Activity / gate coordination |
| `0x02002d70` | 3 | Storage event |
| `0x02002920` / `0x0203feb8` | 0 / 1 | Wait / yield |

The fixture program models synchronous byte reads, erase-to-`0xff`, program by
bit clearing, allocation returns and callback mutations. The native and C paths
each execute those services independently and compare their ordered arguments,
results, public memory at every service boundary, borrowed buffer bytes, final
public memory and resulting fixture storage. These callbacks do not substitute
for the recovered journal, CRC, comparison, address or copy algorithms.

The original model preserves actual register and stack calls and parallel
packet snapshots. Constant `REP` executes its decoded count. The local unsigned
division handler returns zero for a zero divisor, including nonzero/zero. This
is supported by `upstream/pi32v2-isa/tools/hwtest/semantics/s.py`, whose divide
model covers all four integer forms; its bytes are included in provenance.
The timing corpus includes both zero calibration and `0x20000000`, whose native
multiply-by-1,000 wraps to zero before division by six. The frozen loader model's
older restricted zero-divisor domain is unchanged. No physical timing units,
execution latency, hardware test or audio result is inferred from this evidence.

## Reproduction and provenance

From the workspace root, use a new output directory:

```text
python -B tools/build_preset_storage_preparation.py --output build/reverse-preset-storage-preparation-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder authenticates the pinned original and extracted application,
captures the complete source set before compilation, builds host and pi32v2
objects, runs focused native tests, compares original execution, and replays
the original fixtures under AddressSanitizer and UndefinedBehaviorSanitizer.
Both the builder and verifier reject source changes during their run. The
manifest binds all generated outputs; generated fixtures and binaries remain
under ignored `build/`.

Provenance includes the transitive local Python modules, dynamically loaded ISA
semantics, ISA TOML files, every compiled C source and recursive local C header.
It does not rely on an earlier ignored report to discover those inputs. The
MINI comparison authenticates the whole packed v4 image, decodes it, and checks
all 21 loaded regions against the pinned original bytes.

| Input | SHA-256 |
| --- | --- |
| Original packed M5.71 application | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Extracted original application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed packed MINI v4 application | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

The first packaging directory is retained as incomplete. Its host build, target
objects and focused tests passed; sanitizer-harness compiler warnings stopped
packaging before a verification report. The fresh final directory binds the
corrected harness and explicit packed-MINI decoder. This bookkeeping change did
not alter the recovered storage semantics.

## Final offline evidence

The final evidence is in `build/reverse-preset-storage-preparation-02`.
Independent semantic review checked all eleven bodies, mapped journal
derivatives, direct service bindings, stack depths, private byte initialization
and zero-divisor handling. The invalid-footer no-store regression found during
review is retained in the comparison corpus and focused tests.

| Check | Result |
| --- | --- |
| Original-instruction/C comparisons | 217 passed |
| Executed original instructions | 3,031,052 steps |
| New instruction coverage | 675 / 677 |
| Complete loaded instruction coverage | 938 / 940 |
| Focused native tests | 16 passed |
| API/domain witnesses | 26 passed, including four native-success cases |
| ASan/UBSan fixture replays | All 217 passed with exact-size public allocations |
| Additional sanitizer checks | Nine private-buffer witnesses and one null-API guard |
| Host and target compilation | Host UBSan library and eleven pi32v2 objects passed |
| Source and artifact read-back | All 84 source and 17 output hashes matched |
| Reused target object read-back | All ten byte-identical to prior frozen outputs |

The comparisons include lengths 0, 1, header boundaries, page/chunk boundaries
and native maxima; odd and even preset sides; factory and duplicate generation
footers; both retry failures; erase strike wrapping; partial and failed reads;
program prefixes; transaction CRC and marker failures; allocation failure;
callbacks that replace state fields; source aliases with native cache/state;
unaligned host and native byte addresses; overlapping `memmove`; actual yield
paths; and six carried pair writes with an intervening rescan. Replays compare
the same original borrowed-buffer effects under both sanitizers.

Only two new instructions remain unvisited, and no inherited instruction is
unvisited:

| Instruction | Static classification |
| --- | --- |
| `0x02002e22` | Erase-block's early return after journal rejection cannot occur: its actual block mapper always supplies an aligned in-range address and it passes one page. Platform callbacks cannot change those cached arguments. |
| `0x0200791c` | Header-only editing's zero-neighbor fallback cannot occur: both addresses are resolved through the same pair-map byte without an intervening callback. A nonzero current address implies a nonzero neighbor; a zero current address takes an earlier exit. |

These are static in-domain arguments, not executed coverage. The report lists
the precise missing PCs. Compilation and instruction comparisons do not prove
the physical driver, durable flash behavior, real reset recovery, live hardware
execution or the complete preset command lifecycle.

| Frozen evidence | SHA-256 |
| --- | --- |
| `verification.json` | `50e4c3d0d19e2911ee629718489f395674a4e2e5d6695063a86ab21b571f8860` |
| `build-manifest.json` | `ebde7c602e271ccce2657fc18a770489f05caf2ab3b9f56c027a7c0cd9d3772a` |
| New C translation unit | `553d68066bc3337883cb02025c139dcdedc59f4649c60dba98e0e2629b8257cf` |
| New original instruction model | `8e28cc882048036eb2c43a5e8a8f6a4f98d0643f2b55f234a2925a82dae7bf6b` |

The owned implementation and validation files are
`firmware/include/hyperrig/hyperrig_preset_storage_preparation.h`,
`firmware/src/hyperrig_preset_storage_preparation.c`,
`tools/preset_storage_preparation_machine.py`,
`tools/verify_preset_storage_preparation.py`,
`tools/build_preset_storage_preparation.py`,
`tests/test_preset_storage_preparation_machine.py`, and
`tests/preset_storage_preparation_sanitize.c`. This document is the only new
maintained documentation file for the module.
