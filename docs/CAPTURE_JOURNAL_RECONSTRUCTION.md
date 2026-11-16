# Reconstructed capture journal writes and verification

The journal append attempt, complete record rewrite helper, storage wrappers and
metadata cache invalidation now have compilable C and decoded-instruction
comparisons. Tests use synthetic storage held in RAM. No device was opened and
no physical write, erase, firmware installation or durability test occurred.

Sources: [`hyperrig_capture_journal.c`](../firmware/src/hyperrig_capture_journal.c)
and [`hyperrig_capture_journal.h`](../firmware/include/hyperrig/hyperrig_capture_journal.h).
The Required Notice and third-party license are retained. The earlier
[metadata journal/cache reconstruction](CAPTURE_METADATA_RECONSTRUCTION.md),
tested firmware images and completed reports remain unchanged.

## Scope and pinned evidence

The original G v2 M5.71 image has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
CPU flash address `a` maps to decoded `app.bin` offset `a - 0x02000120`.
The inherited loader validates the original and its decoded copy before execution.

| CPU range, end exclusive | Recovered behavior | Region SHA256 |
| --- | --- | --- |
| `0x0200294e..0x02002994` | Invalidate overlapping capture-cache entries | `bf96060ba69d58201cbd558f34f3c1041bb05bd057f2efac59131426f26f2c61` |
| `0x02002f16..0x02002fae` | Split writes into page-sized program requests | `bf2a2b4ef8b9d34c34f39ad6d2f5ceaa47c367b6ffaa84d566b71df1d00b9156` |
| `0x02002d9e..0x02002e08` | Sector erase orchestration | `fb32f714e6d4f9c75d30ce1a09506f6ff5f1a107fa1e0a6054404d74fb9dd679` |
| `0x0200a868..0x0200a878` | Add base and offset, then invoke write wrapper | `54f6555cc0983c1494f5101a137aa0348d4cbff74d71b675e723d916bb4ed228` |
| `0x0200a622..0x0200a72e` | Rewrite header/payload and compare readback | `2b0ee8d72dd7f09f71e4e9555f61531603cfc891f54e2e0437b08f336b9c3229` |
| `0x020282bc..0x020282f4` | Byte/word memory comparison | `2629c8815cb3dadd1bab28610ac721b12a5b55978ed3cb68a8190d30da6a8c23` |
| `0x0200ab96..0x0200ac36` | Command continuation: prepare record and try append | `f0191274bcb2f98be9915ed0b3f6334c9c3f6a99b43b38215b7d58dc31e7e0f9` |
| `0x0200acb4..0x0200acde` | Append success output and notification | `29cdd899428a541cb47a811df169e29218dc203011d11db66c5ad8445d2a787f` |

All eight regions, the used CRC dependencies and the inherited read adapter are
byte-identical in the reviewed MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The read adapter at `0x0200a878..0x0200a888` has SHA256
`4bc6d1293ff2d7165241eee768238bf387b0b390981a4da7037d0f1aa0c6c16b`
and is explicitly bound to MINI v4 in the final comparison report.
The existing finalized CRC wrapper and update instructions execute internally.
Memory comparison executes its original instructions too; it is not replaced by
a scripted equality result in the reference model.

The complete text command starts at `0x0200a888` and includes parsing, argument
conversion, header loading, identity resolution, scanning, allocation, error
formatting and active gain application. Those surrounding paths are not claimed
as recovered here. The append API deliberately exposes a bounded continuation,
not a native ABI replacement for the complete command.

## Cache invalidation and write wrapper

For each of the fifteen capture slots, the invalidator computes the original
8 KiB slot interval and clears only cache entry byte 16 when both conditions hold:

```text
uint32(address + size) > slot_base
slot_base + 8192 > address
```

All other entry bytes, including metadata and padding, survive. The arithmetic
retains unsigned wrapping. There is no special empty-range case: a zero-length
range strictly inside a slot still invalidates that slot, while a zero-length
range at its starting boundary does not. Tests preserve this distinction.

The write wrapper first rejects `address < 0xbf000` or wrapping
`address + size > 0xff000` with -1. Accepted requests invalidate overlapping
cache entries before any program attempt, then call prepare, mode, activity 2
and the clock boundary. Each request is split at the next 256-byte address
boundary, regardless of source alignment.

The program boundary at `0x02002ef2` returns a byte count. A chunk is complete only
if that count exactly equals the requested length. A short or oversized result
stops further programming and eventually returns -3. The wrapper advances its
attempted offset before inspecting the runtime word at state offset 280: when
bytes remain and that word is nonzero, it calls the yield boundary with 1 even
after a failed chunk. Callback changes to that state word take effect immediately.

Every accepted request ends with event `(1, original_address, saved_clock)` and
activity zero, including failed and zero-length writes. Success returns zero.
Cache invalidation and synthetic partial writes are not rolled back on failure.
The offset adapter adds its base and offset modulo 2^32, then executes this same
wrapper.

## Erase wrapper and complete rewrite helper

The erase wrapper rejects a base below `0xbf000`, a base not aligned to 4096, or
wrapping `base + (pages << 12) > 0xff000`. Accepted calls invalidate the affected
cache range and issue prepare, mode and gate 1. For each ascending sector it
calls activity 3, clock, erase dispatch `(0, 200, sector_address)`, event
`(2, sector_address, saved_clock)` and activity zero. It finishes with gate zero.
The original code ignores the erase dispatch's return value and returns zero
after this sequence. A synthetic success here is not evidence of physical erase.

The complete rewrite helper accepts an address, reserved span, 40-byte header,
payload pointer and payload length. It computes the number of sectors as
`(payload_length + 4135) >> 12`, then captures a clock value. It rejects an
insufficient reservation, invalid range or unaligned address/reservation with -1.
Even rejection calls elapsed and sends its final notification.

For an accepted rewrite, it calls the wait-ready boundary, executes the erase
wrapper, writes the payload at `base + 40` when nonempty, and finally writes the
40-byte header at the base. Header bytes are copied verbatim. This helper does
not construct header CRCs or identities.

Verification first reads and compares the complete header, then reads and
compares the payload in chunks of at most 256 bytes. Payload readback uses the
original shared buffer at `0x01c24420`. The raw read boundary at `0x02002806`
rejects negative results; a positive result is accepted if the callback supplied
all bytes. This differs from the append path's wrapped reader, where any nonzero
result rejects the read.

Program failure, read failure or comparison mismatch returns -3. Success returns
zero. Every exit calls elapsed with the saved clock and sends notification
`(18, base, (status & 255) | (elapsed << 8))`, retaining 32-bit wrapping. Time units
are not established. Callback changes to caller-owned header/payload are visible
to later comparisons; private buffer pointers cannot be retained. Tests also
preserve the original behavior when callbacks change bytes after their header
or payload chunk was verified: those earlier bytes are not compared again.

## Bounded append continuation

The entry at `0x0200ab96` is reached after the command has loaded a valid header,
resolved its identity, scanned the journal and decided that metadata differs.
The independent model supplies the documented live inputs: base in `r4`, packed
metadata in `r6`, resolved identity in `r7`, prior clock in `r12`, the scanner's
four result words, and the 40-byte header. The saved auxiliary register is opaque
within this scope. The model allocates the existing command frame and aliases
only its header/result fields to the portable API's public buffers.

The continuation constructs a sixteen-byte `TKGT` record containing identity,
metadata and CRC of its first twelve bytes. It captures the scanner cursor,
capacity and header payload size before calling external services. It calculates
the first relative offset as:

```text
(cursor << 4) + ((payload_size + 55) & 0xfffffff0)
```

It attempts at most two successive record positions, stopping sooner at the
captured capacity. Each attempt executes the write adapter/wrapper, then reads
sixteen bytes through the wrapped reader and compares them with the intended
record. Failed programming skips that read. Any failure advances the attempted
cursor and offset to the next record.

Matching readback writes metadata, selected index and next cursor into the
scanner result, then calls elapsed and sends `(18, absolute_record_address,
elapsed << 8)`. The portable API returns 1 at the success exit `0x0200acde` and
leaves its separate allocation output unchanged.

When no attempt succeeds, the continuation updates the scanner cursor and
reaches `0x0200ac36`, immediately before allocation. The API returns zero and
reports the captured payload size rounded up to four bytes, with a four-byte
minimum for an empty payload. It does not allocate or automatically call the
rewrite helper. Callback changes to public cursor/capacity/header cannot alter
the already captured attempt bounds or allocation calculation; later result
writes and unrelated callback changes are preserved.

These API returns classify the two continuation exits. They are not the original
complete command's return value. Resuming the full command will require its
remaining live state, allocation/error handling and report formatting.

## Synthetic service boundaries and API limits

| Original address | Boundary retained |
| --- | --- |
| `0x02002ef2` | Page-program request, returning byte count |
| `0x02002b80` | Sector-erase dispatch |
| `0x02002806` / `0x02002810` | Raw / wrapped physical read implementations |
| `0x01c04862` / `0x020031be` | Clock / elapsed conversion |
| `0x02002772` / `0x02002bcc` | Prepare / mode |
| `0x02002786` / `0x02002d06` | Activity / gate |
| `0x02002d70` / `0x02002d10` | Event / notification |
| `0x02002920` / `0x0203feb8` | Wait-ready / yield |

The new runtime contains the existing control bytes, separate metadata cache and
256-byte verification scratch area. Tokens identify original boundaries; no
original hardware address is called as a host function pointer. The test storage
script changes Python dictionary or C array bytes and records transfers. It does
not model NOR programming restrictions, wear, erase timing, power-loss recovery,
atomicity or physical durability.

New status -200 rejects invalid pointers/callbacks before effects. The bounded
write API accepts at most 8192 bytes, erase at most 64 pages, rewrite at most
8152 payload bytes and standalone comparison at most 256 bytes. Append requires
payload size at most 8152 and cursor/capacity at most 255. Empty source buffers may
be null where documented. Buffers must be disjoint. Callbacks may change
caller-owned state synchronously within those bounds, but not the IO structure,
borrowed program source or private stack storage. Re-entry, concurrency and
retained borrowed pointers are excluded.

## Verification and reproduction

The completed `build/reverse-capture-journal-02` run passed **655 comparisons**.
The earlier `build/reverse-capture-journal-01` artifacts and report are preserved.

| Entry point | Comparisons |
| --- | ---: |
| Cache invalidation | 253 |
| Write wrapper | 69 |
| Write offset adapter | 21 |
| Erase wrapper | 36 |
| Byte comparison | 136 |
| Complete rewrite | 87 |
| Append continuation | 53 |

All **302 of 302 new instructions** were visited, including byte/word comparison,
the two append exits and write/erase cache effects. The run visited 334 of 1,574
combined instructions. Previous components retain their separate reports.
Comparisons check semantic statuses or continuation exits, nineteen mapped RAM
regions, ordered services and state at every boundary, programmed bytes, read
addresses/destinations/sizes, final synthetic storage bytes and allocation output.

Cases cover boundary/wrapping addresses, zero-length behavior, page splitting,
short/oversized program results, ignored erase results, raw versus wrapped read
statuses, readback corruption, retry limits, exhausted journals and twenty-seven
cases with mutating callbacks. Nine added readback cases mutate header/payload
bytes before, during or after the corresponding comparison; two provide matching
changed readback to prove the current caller bytes are used. The second program
failure is reached after a failed first attempt, and every scripted program
result must be reached. Thirty-four invalid-API checks and a null-empty
comparison check passed. Twenty-six focused instruction tests and 263 exact-buffer
ASan/UBSan rewrite/append cases passed. The host library uses warnings as errors
and UBSan; all six source/dependency objects compile for pi32v2 r3.

The new target object is **2,556 bytes**, SHA256
`d075adb2cd3a8a4ecfcc90912b85c2f76869804139057de99f131561302d00da`.
This is relocatable object size, not linked firmware size, memory use or latency.
The older metadata object remains byte-identical to its completed report.
The new C source SHA256 is
`a3517ca130212467a049d0948cc4c77cf1288f86fb8d8e5bc062b35a21a5e78b`;
the comparison report SHA256 is
`0091121eb4d4125e7a476a09d3005a4facf63b1e4746f04915e3e1de8a62c6ac`.
All 35 recorded source hashes and nine artifact hashes matched after completion.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_journal.py --output build/reverse-capture-journal-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder refuses existing output directories. Host/target outputs,
sanitizer executable, comparison report and manifest stay in the new ignored
directory. It produces no flashable firmware and accesses no device.

## Remaining command work

At `0x0200ac36`, the omitted command allocates a payload buffer, reloads and checks
the source record, replaces header metadata, and invokes the rewrite helper.
It can invoke rewrite a second time before freeing the buffer, then recomputes
journal capacity. Failure formatting, current-slot comparison and active gain
application occur after these paths. Those caller branches remain unexecuted in
this milestone, as does the text parser and metadata packer before the append
entry. Recovering them is separate from proving the physical flash driver or
power-loss behavior, both of which remain outside these synthetic tests.
