# Reconstructed capture metadata journal and cache

The capture metadata lookup now has compilable C and an independent instruction
comparison model. It scans the journal, checks record CRCs and preserves the
original cache behavior, including caching a header fallback after a read error.
Physical flash reads remain an explicit callback. This component never writes
flash and does not implement durable metadata updates.

Sources: [`hyperrig_capture_metadata.c`](../firmware/src/hyperrig_capture_metadata.c)
and [`hyperrig_capture_metadata.h`](../firmware/include/hyperrig/hyperrig_capture_metadata.h).
The Required Notice and third-party license are retained. The earlier
[capture loader](CAPTURE_LOADER_RECONSTRUCTION.md), tested firmware images and
completed reports remain unchanged.

## Pinned evidence

The original G v2 M5.71 image has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
CPU flash address `a` maps to decoded `app.bin` offset `a - 0x02000120`.
The inherited loader validates both the original image and its decoded copy.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x02007cba..0x02007ce0` | Journal capacity | `83f162c32e8a329b8b2afdd19253155b03bccb5898a6110a9291224c3984a8df` |
| `0x02007ce0..0x02007dbe` | Journal scan | `5997923906405d44fc21728496b1c759055a11a98490f5e69e554cbd89779b91` |
| `0x02007dbe..0x02007e62` | Cache lookup and scan fallback | `ba7660a8035a805ba7dcc14932097811f8dc7e3707861f185b78b1f736ed0ad2` |
| `0x020034da..0x020034f2` | Check every byte for 255 | `84499f5376300a6dc7c60478093d06c4fb78df117c4c2bef2867dc2c49c7a7cb` |
| `0x020034f2..0x02003502` | Finalized CRC wrapper | `c18fcf858d16634120dc59915d7cc02fef4530229d9ec3d51a68bd708955b1a5` |
| `0x0200a878..0x0200a888` | Read adapter adding base and offset | `4bc6d1293ff2d7165241eee768238bf387b0b390981a4da7037d0f1aa0c6c16b` |

The CRC wrapper executes the previously recovered update instructions at
`0x020028c2..0x020028f2`. It starts at `0xffffffff` and complements the final
state, without polling between bytes. The polynomial is the existing reflected
`0xedb88320`. The new C wrapper reuses that unchanged CRC implementation.

All six regions and the CRC-update dependency are byte-identical in the reviewed
MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

## Journal placement and selection

For header payload size `n`, unsigned values above 8152 have capacity zero.
Otherwise the original calculation is:

```text
start = (n + 55) & 0xfffffff0
end = (n + 4135) & 0xfffff000
capacity = end > start ? (end - start) >> 4 : 0
```

Capacity ranges from zero through 255 records. It can drop to zero near a sector
boundary and then increase in the next sector: sizes 4041..4056 have zero
capacity, while size 4057 has 255. This is layout arithmetic, not a claim about
which payload sizes are valid capture models.

The scanner initializes four little-endian output words:

| Output offset | Initial value | Subsequent use |
| --- | --- | --- |
| 0 | Header word 12 | Most recent matching metadata, or fallback |
| 4 | `0xffffffff` | Selected zero-based record index |
| 8 | Zero | One past the last non-erased record inspected |
| 12 | Capacity | Loop bound, reloaded between read chunks |

The zero at output offset 8 is significant. At `0x02007d02`, the parallel ALU
instruction computes `size + 55` while its paired store reads the previous
register value, zero. Serializing the printed disassembly would give the wrong
initial cursor. The inherited instruction engine reads both halves from their
shared pre-packet register state; a focused test checks this case.

Reads cover at most sixteen 16-byte records, using a private 256-byte buffer.
The physical read address is wrapping `base + start + 16 * chunk_index`.
The real read adapter instructions execute before the boundary at `0x02002810`.
Successful callbacks must fill every requested byte; failed reads may fill a
prefix, which is discarded without examining records from that chunk.

Each record contains:

| Record offset | Required interpretation |
| --- | --- |
| 0 | Tag `0x54474b54`, bytes `TKGT` |
| 4 | Identity matching either the supplied resolved identity or current header word 8 |
| 8 | Packed metadata word, retained without validity checks |
| 12 | CRC of the preceding twelve bytes |

All-255 records are skipped. Every other record advances the output cursor even
if its tag, identity or CRC is rejected. A valid record replaces the selected
metadata and index. Scanning continues across erased gaps and after a match, so
the last valid matching record wins. Packed gain validity is checked later by
the existing capture loader, not by this journal component.

On any read error, the scanner returns -1, rereads header word 12 as the fallback,
sets the selected index to `0xffffffff`, and copies the current capacity into
the cursor. Any earlier valid selection is discarded. A completed scan returns
zero even when no valid record exists or capacity is zero.

The conditional register-mask store at `0x02007d94` places metadata from `r0` at
output offset 0 and the index from `r8` at offset 4. It uses the confirmed
`stm.post1` ordering, lowest numbered register at the lowest address, without
base writeback.

## Cache behavior and callback mutation

The cache occupies 300 bytes at original RAM address `0x01c2422c`, with fifteen
20-byte entries:

| Entry offset | Value |
| --- | --- |
| 0 | Header identity from word 8 |
| 4 | Header payload length |
| 8 | Resolved identity argument |
| 12 | Selected or fallback metadata |
| 16 | Nonzero validity byte |
| 17..19 | Preserved padding |

Only unsigned slot values 0..14 can use or update the cache. A hit requires a
nonzero validity byte and all three key words to match. The lookup then returns
the cached metadata without reading flash. Header fallback word 12 is not part
of the cache key.

A non-null details pointer forces a fresh scan even for a matching cache entry.
Without details, the scanner uses a private local result. The lookup ignores the
scanner's return status and caches its metadata for slots 0..14, including the
fallback after a failed read. A later hit can therefore reuse that fallback
without retrying the flash read. This reproduces the original behavior and does
not imply that a failed read became a validated journal.

Slot addressing retains the original signed comparison and wrapping arithmetic:

```text
if signed32(slot) < 8:
    base = 0xdf000 + (slot << 13)
else:
    base = 0xcf000 + ((slot + 0x7fff8) << 13)
```

The scanner captures the initial payload size and chunk count, but rereads header
identity during record matching and header fallback after errors. Cache updates
use the header identity and size after the scan. A supplied result's capacity is
reread between chunks; changing it during a read does not change the already
requested chunk's record count. These distinctions are exercised with synchronous
callback mutations.

The API permits those changes to caller-owned header/cache/result storage,
provided result capacity remains 0..255. It excludes re-entry, concurrent changes,
overlapping buffers, mutation of private context/stack storage and retained read
pointers. Invalid pointers or missing read callbacks return new status -200
before calls or writes. Pure erased/CRC APIs are bounded to 0..256 bytes and
accept null data only at length zero. Lookup writes the original metadata return
through an output argument and uses new API status zero on success; this avoids
reserving any metadata bit pattern for an error code.

## Verification and reproduction

The completed `build/reverse-capture-metadata-01` run passed **9,764 comparisons**:

| Entry point | Comparisons |
| --- | ---: |
| Capacity | 8,286 |
| Erased-byte detection | 530 |
| Finalized CRC | 514 |
| Journal scan | 234 |
| Cache lookup | 200 |

All **180 of 180 new instructions** were visited, including the original read
adapter and both small byte-copy REP loops. The run visited 198 of 1,272 combined
instructions; inherited components retain their separate coverage reports.
The comparison checks semantic results, all seventeen mapped memory regions,
ordered read addresses, sizes and normalized destinations, and public state at
every read. Private stack padding is not an output contract.

Coverage includes every payload size 0..8153 for the capacity helper, randomized
uint32 sizes, erased gaps, both identity keys, bad tags/CRCs, chunk boundaries,
read failures with partial destinations, cache misses/hits and forced scans.
The counts include 23 cases with mutating callbacks, twelve stateful cache
lookups and 514 CRC results also checked against Python's `zlib.crc32`.
Fourteen invalid-API and two null-empty checks passed.

The builder compiles the new C and unchanged dependencies for the host with
warnings as errors and UBSan, and for pi32v2 r3. A separate ASan/UBSan executable
uses exact-size public buffers and exercises every payload size 0..8153, edge
slots, and helper lengths 0..256. Its 8,418 cases passed with 68,608 synthetic
reads. Twenty-one focused instruction tests also passed.

The new pi32v2 object is **1,888 bytes**, SHA256
`f739de0d65039b38e8fe2a0689c43379231cc2218125f30993f1022f1e930b53`.
This is relocatable object size, not linked firmware size, runtime RAM use or
latency. The C source SHA256 is
`26e4fc3fce467cdd3bf570aa0c6d5218f4248f2c951ec8823cd24f262d89d0e7`;
the comparison report SHA256 is
`9512d7d49abcaaaea5641553b5b2a8fd52d9c3786361a71948669c7953aa0ae9`.
All 31 source hashes and eight artifact hashes matched after completion.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_metadata.py --output build/reverse-capture-metadata-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder refuses existing output directories and writes a host
library, five target objects, sanitizer executable, source-hashed comparison
report and artifact manifest into a new ignored directory. Generated artifacts
remain outside Git. No hardware, audio, timing or durable-storage test is made.

## Next persistence boundary

The original lookup constructs both read and write function pointers, but the
scanner uses only the read pointer at offset zero. The unused write adapter
`0x0200a868..0x0200a878` adds base and offset and calls `0x02002f16`. Its body and
the physical read wrapper remain outside this reconstruction.

Static inspection identifies a later command path that calls the scanner at
`0x0200ab62`, constructs a `TKGT` record and CRC at `0x0200aba0..0x0200abb8`, calls
the write adapter at `0x0200abee`, and rereads and compares the record around
`0x0200ac00..0x0200ac16`. Its retry, erase/compaction and cache-update behavior
must be recovered separately before claiming durable writes. None of those
write operations are called or emulated by this milestone.
