# Storage control reconstruction

This module reconstructs 45 complete M5.71 bodies from the pinned Alpha 11 image. The closure contains 3,444 original bytes, including 32 embedded branch-table and padding bytes, and 1,165 decoded instructions. It connects the public read, program and control wrappers to their actual command/address/status/cache routines. All peripheral registers, IRQ registration, synchronization, scheduling and cross-core services remain explicit offline boundaries. No device was opened, no firmware was changed, and no hardware, audio, power-loss or durability claim follows from these comparisons.

The C is a semantic reconstruction, not the original source. It retains the required notice for the original firmware: Copyright (c) 2026 Manuel Aguirre. See [the preserved license](../third_party/ultrarig/LICENSE.md).

## Complete function and ABI registry

Arguments are uint32 words in native argument order. Address arguments are original-address tokens. All entries fit the first four native argument registers. The generic API copies twelve words before callbacks, publishes the native word in result[0], and publishes zero in result[1]. Void bodies normalize both result words to zero; this does not assert a native return-register value for a void call.

| Name | Original complete range, end exclusive | Arguments | Return |
| --- | --- | --- | --- |
| `power2` | `0x020026d6..0x020026e8` | signed exponent | native uint32 word |
| `initialize` | `0x020026e8..0x02002772` | none | native uint32 word |
| `ensure` | `0x02002772..0x02002786` | none | void |
| `activity` | `0x02002786..0x020027e4` | activity word | void |
| `poll` | `0x020027e4..0x02002806` | none | void |
| `raw_read` | `0x02002806..0x02002810` | destination, device address, bytes | native uint32 word |
| `read` | `0x02002810..0x02002874` | device address, destination, bytes | native uint32 word |
| `range` | `0x02002994..0x020029b0` | device address, bytes | native uint32 word |
| `reject` | `0x020029b0..0x020029be` | device address | void |
| `control` | `0x020029be..0x02002b80` | command, argument word/token | native uint32 word |
| `ioctl` | `0x02002b80..0x02002bcc` | unused handle, command, argument word/token | native uint32 word |
| `mode` | `0x02002bcc..0x02002bd8` | none | native uint32 word |
| `program_pages` | `0x02002e6a..0x02002ef2` | source, bytes, device address | native uint32 word |
| `program` | `0x02002ef2..0x02002f16` | unused handle, source, bytes, device address | native uint32 word |
| `bus_enter` | `0x01c00000..0x01c00072` | none | void |
| `delay` | `0x01c00072..0x01c00088` | iteration word | void |
| `chip_select` | `0x01c00088..0x01c000a8` | nonzero means high | void |
| `transfer_wait` | `0x01c000a8..0x01c000d8` | none | native uint32 word |
| `send_byte` | `0x01c000d8..0x01c000f0` | word written to data register | native uint32 word |
| `leave_continuous` | `0x01c000f0..0x01c0012e` | none | native uint32 word |
| `receive_byte` | `0x01c0012e..0x01c0014c` | none | native uint32 word |
| `send_address` | `0x01c0014c..0x01c00170` | device address | void |
| `receive_fast` | `0x01c00170..0x01c00184` | none | native uint32 word |
| `receive_buffer` | `0x01c00184..0x01c00204` | destination, count (low 16 bits) | native uint32 word |
| `send_fast` | `0x01c00204..0x01c00214` | word written to data register | native uint32 word |
| `send_buffer` | `0x01c00214..0x01c00290` | source, count (low 16 bits) | native uint32 word |
| `transfer_read` | `0x01c00290..0x01c003d4` | destination, address, count, force command | native uint32 word |
| `restore_read` | `0x01c003d4..0x01c003e8` | none | void |
| `bus_leave` | `0x01c003e8..0x01c0044c` | state+66 byte | void |
| `identify` | `0x01c0044c..0x01c004d0` | none | void |
| `status_read` | `0x01c004d0..0x01c0050a` | none | native uint32 word |
| `status_capture` | `0x01c0050a..0x01c00536` | none | void |
| `bank_enter` | `0x01c00536..0x01c0056e` | device address | void |
| `bank_leave` | `0x01c0056e..0x01c005a4` | device address | void |
| `device_read` | `0x01c005a4..0x01c005d0` | destination, address, requested count | native uint32 word |
| `write_enable` | `0x01c005d0..0x01c005e6` | none | void |
| `translate` | `0x01c005e6..0x01c005f6` | device address | native uint32 word |
| `cache_forward` | `0x01c005f6..0x01c00600` | address, bytes | void |
| `busy_wait` | `0x01c00600..0x01c00640` | none | native uint32 word |
| `device_erase` | `0x01c00640..0x01c006d2` | command, address | native uint32 word |
| `status_write` | `0x01c006d2..0x01c0079e` | status/control word | native uint32 word |
| `status_apply` | `0x01c0079e..0x01c00822` | desired status/control word | native uint32 word |
| `cache_region` | `0x01c00822..0x01c00840` | device address, bytes | void |
| `device_program` | `0x01c00840..0x01c008b4` | source, address, bytes | native uint32 word |
| `cache_lines` | `0x01c00b80..0x01c00bb2` | address, bytes | void |

The complete-body decoder preserves live native registers across internal calls. This matters for the device address retained in r3 across the pure range helper and for values retained across power-of-two calculation. External platform calls are identified by their original call sites, with their audited arities; r0..r3 are poisoned after a scripted call except for its return word. Reconstructed internal helpers are never replaced by service results.

## Branch tables and immutable evidence

The five tables below are embedded in the corresponding complete bodies. They are excluded from instruction counts. The decoder authenticates each exact hash, unsigned or signed index check, TBB consumer, table base, active target and zero padding byte. Every active target must be a decoded packet start; no target may enter the second instruction of a parallel packet.

| Table | Exact data range | Active / padding bytes | Consumer | SHA-256 |
| --- | --- | --- | --- | --- |
| `control200` | `0x02002a2a..0x02002a32` | 7 / 1 | `0x02002a28` | `9836f1b872721858b1192da003e69649c3bbab55c3d27b6278eb8d944a7fac43` |
| `control100` | `0x02002a42..0x02002a46` | 4 / 0 | `0x02002a40` | `eb9d350e3bbbcf98dd77f5b8e02bd5c3b4ade52eb0d62f588a2f8033bf25fa3b` |
| `ioctl200` | `0x02002b90..0x02002b96` | 5 / 1 | `0x02002b8e` | `aa61f01dbc3bcf924f704acc5d907ff0a4775c9adf338f1ad979a90315f07dce` |
| `read_modes` | `0x01c002bc..0x01c002c4` | 8 / 0 | `0x01c002ba` | `d42e5576b24bc188b82926ddcc9f94ca173cce8ae306c8bff3714b1001c3d406` |
| `erase200` | `0x01c0065a..0x01c00660` | 5 / 1 | `0x01c00658` | `9dd98328868b63a856fcc63cf57942f4d7cf52619e525dfda5e4db2876e97145` |

The read-mode index is a four-bit signed extraction checked for negativity, followed by a four-bit unsigned extraction. Consequently modes 8..15 return failure before the table. The command tables subtract 200 or 100 using uint32 wrap and then use the original unsigned bound. The verifier records the exact decoded index instructions and resolved target list, rather than inferring table sizes from nearby bytes.

Original code and branch/static tables must remain immutable. The public borrowed map must not expose them as writable storage. The compared mapping excludes every owned code/table span, and API witnesses reject attempts to borrow or write those addresses. The native machine predecodes immutable instruction bytes; this module does not support self-modifying code.

## Runtime state and public mapping

The borrowed byte map preserves native address relationships and aliases, permits byte-aligned backing storage, and must remain pure and stable. Mapped state, API/IO/argument/result storage and callback bookkeeping are disjoint. Callbacks are synchronous; there is no reentry, concurrency, retained borrowed pointer or access to the private frame range `0x30000000..0x30001040`. Private four-byte command/dummy buffers remain internal and are never passed to external services.

The device record starts at `0x01c3743c`. Its first 16 bytes are mutable identification results; offsets 16/17 are initialization/critical-state flags, 20 a configuration word, 24 capacity, 28 the received ID, 32..55 address/configuration fields, 56/60 saved controller words, 64 configured bus mode, 68 desired/captured status and 72 status state whose remaining writers are outside this closure. Offset 80 is the extended-address flag. The byte at offset 81 is observed by an external critical service. These are BSS/runtime records, not immutable initialized tables. Synthetic identification values in fixtures are not captured device identifiers.

The separate original reset witness `0x0200019c..0x020001b2` has SHA-256 `05221f085384369277a7fbdc7eefa5a1e46770c9c0f3ccb24b4d2e735267e930` and clears `0x01c2030c..0x01c38050`. It authenticates the BSS origin of the device record, the ensure byte at `0x01c24228` and synchronization storage at `0x01c27734`. It adds neither a reconstructed function nor an immutable-data exclusion. External startup/device-selection writers are still outside this closure.

## Explicit platform and register events

| Service target | Audited words | Boundary |
| --- | --- | --- |
| `0x020005ac` | 4 | IRQ registration |
| `0x0203fb92` | 1 | synchronization object initialization |
| `0x01c04862` | 0 | clock |
| `0x0203ea6e` | 0 | scheduler/poll service |
| `0x02040614` / `0x0204074c` | 1 / 1 | synchronization enter/leave |
| `0x01c01108` / `0x01c011da` | 2 / 0 | cross-core critical enter/leave |
| `0x0203e742` / `0x0200096e` | 0 / 0 | fatal/reset boundaries |

The exact 16 direct call sites are recorded in the verifier. All calls are direct in this closure. A service target cannot be selected merely because a callback token numerically matches a reconstructed entry. The IRQ handler token `0x01c041dc` is passed through unchanged and is not executed or claimed recovered.

Explicit MMIO windows are `0x00011c00..0x00011c0c`, `0x000500c0..0x000500cc`, `0x0005101c..0x00051020`, `0x00040200..0x00040204`, `0x00040300..0x00040310`, and `0x01eee008..0x01eee00c`. READ supplies the synthetic value; WRITE records its exact byte width and uint64 value. Ordinary accesses can be 1, 2, 4 or 8 bytes where the native instruction specifies that size. Memory RMW instructions emit ordered word READ and WRITE events. Accesses straddling windows and borrowed pointers into windows are rejected. Callbacks may mutate public RAM through the scoped view; later loads observe those mutations at native points.

`csync` and `flushinv` are explicit BARRIER and FLUSH_INVALIDATE events. They carry no assertion of real peripheral completion, cache coherency, memory ordering between cores or hardware scheduling. The host simulator uses an independent scripted register image, ready/busy sequences and mutations. It is not a flash-device or electrical model.

## Preserved result and failure behavior

- The public read guard retains uint32 address wrapping. Reads advance their offset by 256 even for the last short block. A low-level invalid read mode can leave the destination untouched while the device wrapper still returns the requested length; the enclosing public read can therefore return zero.
- Program pages retain the first partial-page size, signed remaining-count selection, synchronization nesting and the original ignored low-level status. A returned length does not establish successful transfer or persistence.
- Erase retains the original equality check between aligned address and aligned capacity; it is not silently replaced by a greater-than range check. Extended-address mode and cache-address translation are retained.
- Status application retains the three attempts, alternate command format, current desired/captured words and original status-write error propagation. Busy-wait results ignored by the native caller remain ignored.
- Command 205 retains its word/word-pair configuration copy, parallel byte-store snapshot, cached cache-region address and subsequent callback-visible reloads. Byte-copy commands retain native overlap ordering.
- Activity depth is the raw stored byte, including pop behavior for values above four; only the native push guard limits new entries.

API guards are separate from native return words: -200 invalid API/entry; -201 missing, wrapping or forbidden MMIO map; -202 private-memory access; -203 finite work/service/event budget. Earlier writes and events remain, and result words remain untouched. Work counts portable operations rather than native instructions, so arbitrary work-budget stops are not presented as matched original instruction prefixes. Event-budget witnesses stop both executions immediately before the same next event and compare the retained prefix.

Null configuration for command 205 invokes both explicit fatal services and reaches the original fixed-PC loop at `0x02002b7e`. Status -204 reports that observation, without asserting a native return or performing cleanup that the original loop does not reach.

The native transfer poll retains 50,000,000 iterations and the status-busy poll retains 5,000,000 iterations. The corpus compares ready, delayed-ready and interrupted waiting paths without shortening these constants. Terminal timeout paths are reported separately from executed coverage; external events do not establish wall-clock durations.

## Independent instruction model and validation

The model decodes the pinned original bytes with the local pi32v2 ISA tables. New handlers cover word memory AND/OR RMW, logical memory shift, low-halfword sign extension, NOP and explicit cache/barrier events. The pinned ISA records authenticate RMW widths and flag preservation; no loaded branch in this closure consumes implicit N/Z flags from the low-halfword extension. Existing parallel-packet, REP and register semantics are reused unchanged. Only the newly owned machine/source/test files change.

The verifier compares native return/observation status, every mapped byte, ordered platform arguments/results, MMIO widths/values/results, callback-state hashes before and after each boundary, and a combined chronological stream across services and register events. The ASan/UBSan executable replays those original streams with exact-sized allocations and compares the original final memory and untouched output sentinels for incomplete observations. Focused tests also assert independently derived native behaviors and reject corrupted table/index/packet evidence.

The complete build binds sources before its first compilation, recursively captures local C headers, records loaded Python modules, and includes the ISA TOML and dynamically loaded semantics sources. It checks the source set and bytes again after verification, authenticates the host library, emits one pi32v2 object and hashes every final artifact. No earlier ignored report is needed to reproduce this standalone module.

Original packed image SHA-256: `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`. Extracted application SHA-256: `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`. Reviewed MINI v4 packed image SHA-256: `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`. The MINI check compares all 45 complete bodies, all 32 table/padding bytes and the separate 22-byte reset witness.

Build with a fresh ignored directory:

```text
python tools/build_storage_control.py --output build/reverse-storage-control-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

## Frozen result

The completed evidence is in ignored `build/reverse-storage-control-01/`. The host library, pi32v2 object and complete original-fixture ASan/UBSan replay all passed. The independent root review inspected all C functions and the API against the original listings, including the retained r3 values, MMIO parallel byte store, cache/range behavior and callback boundaries. It found no in-domain semantic mismatch. The review's immutable-code/table contract clarification is included in the tested header and negative corpus.

| Check | Frozen result |
| --- | --- |
| Complete new original bodies | 45 / 3,444 bytes |
| C/original comparisons | 626 |
| Decoded original steps | 557,338 |
| New/all instruction coverage | 1,164 / 1,165 |
| Focused native/evidence tests | 20 passed |
| C API/domain checks | 81 passed |
| ASan/UBSan original fixture replays | 626 passed |
| Additional sanitizer guards | 13 passed |
| pi32v2 objects | 1 |
| Read-back source/artifact bindings | 64 / 7, all matched |
| MINI binding | 45 bodies, 32 table bytes, separate 22-byte reset witness |

The sole unexecuted instruction is `0x02002b7e: goto -2`. Its entry is observed after the two fatal services return; the original does not return from that self-loop. The report records this as an incomplete observation, not a reconstructed native return. Instruction coverage does not establish every branch outcome: the 50,000,000-iteration transfer timeout and 5,000,000-iteration busy timeout were not run to exhaustion. Their original constants and result propagation remain in both bodies, and shorter event-boundary prefixes are compared without manufacturing a timeout.

Report SHA-256: `333bf4a506f550afea10d660cb1700a4c5f0b7b5794da17681df44d970d293d8`.

Build manifest SHA-256: `7795e4410720ca5a7cfa481e3b9e0e7ed2decf83a1d22a45a6964d19501d9321`.

The development directory is preserved separately. Its first replay exposed a verifier fixture ownership issue: a later case changed an input array retained by reference. The final verifier snapshots each original input as immutable bytes before subsequent cases; all 626 final replays pass. No reconstructed C behavior was changed for that fixture correction.

The eight owned maintained files passed a local privacy/path-pattern audit with no findings. Original input artifacts, previously completed sources/reports and the device remained unchanged. Further work can compose these actual storage routines with the already reconstructed preparation/journal layer, while retaining the MMIO, OS, IRQ and cross-core services as explicit boundaries until those services are separately recovered.
