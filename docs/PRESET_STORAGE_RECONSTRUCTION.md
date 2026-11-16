# Reconstructed preset availability and record validation

Seven more original functions are reconstructed in portable C: preset address
mapping, header reading, incremental CRC, complete checksum, record reading and
the preset availability cache. The cache is connected to the existing
[selection model](SELECTION_RECONSTRUCTION.md), so integrated navigation now
executes these checks against synthetic flash bytes before calling the loader.

Sources: [`hyperrig_preset_storage.c`](../firmware/src/hyperrig_preset_storage.c)
and [`hyperrig_preset_storage.h`](../firmware/include/hyperrig/hyperrig_preset_storage.h).
This is a hand reconstruction with the original Required Notice and license
retained. The earlier transition, action and selection sources and reports are
unchanged. No firmware image is produced or installed by this component.

The later [preflight component](PRESET_PREFLIGHT_RECONSTRUCTION.md) reuses this
unchanged reader and adds legacy layout and effect-parameter conversion. The
results below remain the original storage-validation baseline.

## Original functions and MINI binding

The reference G v2 M5.71 application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x0200cf88..0x0200d060` | Cached preset availability | `bc6ed2f98c1a6e9b38324d6872caf1f0657a97aaaa44e9681358abb95b80d292` |
| `0x0200777a..0x020077aa` | Preset ID to flash address | `65f85a8ba4e47f08851e436f389f273b390fae2a3c1ba12c2090ee49c65a5ea2` |
| `0x020026ba..0x020026d6` | Block index to flash address | `b16d5d7bd5f4656c5d576a8edf21fb8fdd038bc16fb8f052f0e06424befa12d3` |
| `0x02006f14..0x02006f3a` | Read and check a record header | `5d678df31bc1d5326d23e38bbcaaac2c2b22c8e93a4757585743f033e1e1a42b` |
| `0x020028c2..0x020028f2` | Incremental reflected CRC | `9305d3a538c77bc62e405ea2cca07d4d6584138eae0c5d1eadeda1cb7be7f0e1` |
| `0x0200704e..0x020070a4` | Chunked complete checksum | `1eaa7a679ab6d7f2a0772ed63dc638332e611241874770a7e22002ef42d2ebc0` |
| `0x020079bc..0x020079f6` | Read and validate a complete record | `c55976a3e1f77c6cc93262c31601390b20dc209dac1d8bbb1739319d5d38e88f` |

These seven regions and all fourteen earlier control/selection regions are
byte-identical in the released MINI v4 application, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This binds the analysis to that image; it does not establish execution of the
reconstructed C on hardware.

## Addresses, header and CRC

The original signed-byte mapping at state offset `3476 + preset / 2` assigns
each pair of presets to a block. Preset IDs outside 0..31 and negative mapping
bytes return address zero. For a nonnegative mapping, even presets occupy the
block start and odd presets add 2,048 bytes:

| Block index | Base flash address |
| --- | --- |
| 0..15 | `0xbf000 + block * 4096` |
| 16 | `0xdd000` |
| Above 16 | `0xde000` |

The last row preserves the original aliasing behavior, including unusual
nonnegative mapping bytes. The availability function still calls the read
boundary if address resolution returns zero; it does not invent an earlier exit.

The header reader requests exactly 40 bytes. It accepts a header only when the
read returns zero, the little-endian uint32 tag at offset 0 matches its caller's
tag, and the uint32 payload length at offset 4 is at most the caller's maximum.
It does not inspect the other fields. Availability supplies tag `0x51474b54`
and maximum 1,490; the expected payload CRC is the uint32 at offset 8.
The remaining 28 header bytes are copied but have no validation meaning in
these functions. A valid tag and CRC do not establish valid preset contents.

The CRC update uses the reflected polynomial `0xedb88320`, eight shifts per
input byte, and retains the supplied initial state without a final XOR. The
complete checksum starts with `0xffffffff` and XORs the result with the same
value. For `123456789`, raw state is `0x340bc6d9` and the complete checksum is
`0xcbf43926`. An empty complete checksum is zero.

## Availability cache and failures

The two independent bitmasks at state offsets 708 and 732 mean **checked** and
**available**, respectively. For an in-range preset:

1. Call storage preparation at `0x020031d4`, even on a cache hit. Preparation
   may refresh the mapping or invalidate cached bits.
2. If the checked bit is set, return the corresponding available bit without
   priority changes or reads.
3. On a miss, call `0x020054a8(1)`, resolve the address and read the header.
4. If the header is accepted, read its payload in chunks of at most 256 bytes,
   starting at `address + 40`. Update the raw CRC after each successful read.
5. Call `0x020054a8(0)` on every miss outcome. Only then set the checked bit
   and set or clear the available bit according to the result.

The priority helper's role is inferred from its calls to OS priority services;
its implementation remains outside this component. Both masks are read again
after the release call, preserving other bits changed by that callback.

Header rejection, nonzero payload-read results and CRC mismatch all cache the
preset as unavailable. A transient read failure therefore stays cached until
preparation or another writer invalidates that bit. A previously accepted result
also stays cached when the supplied flash bytes change without invalidation.
These behaviors are reproduced, without claiming that storage preparation has
yet been reconstructed.

The scratch area at state offset 5812 retains writes from successful reads and
partially completed failed reads. A short final chunk leaves its unused tail
unchanged. An accepted empty payload performs no body read and requires CRC zero.
Availability calls the raw CRC directly; the underlying read wrapper may perform
its own polling, which is outside the modeled read boundary.

## Shared record reader

The record reader accepts an address, tag, maximum length, 40-byte header buffer
and payload buffer. In the original ABI, the fifth argument is passed on the
caller's stack. The reader performs one header read and, if accepted, one body
read at `address + 40`, including a zero-length body read for an empty record.

| Original return | Meaning |
| --- | --- |
| 0 | Header accepted, payload read succeeded and CRC matched |
| -1 | Header read failed, tag differed or length exceeded the maximum |
| -2 | Payload read returned nonzero |
| -3 | Payload CRC differed |

Output buffers retain completed and partial writes on failure. There is no
rollback or implicit clearing. The payload length is read again after the body
read. Its checksum runs in 256-byte chunks, calling `0x020027e4` between chunks,
but never after the final chunk. It rereads the expected CRC after checksumming.
Consequently, a synchronous poll callback can change future input bytes or the
expected CRC; this is not an atomic snapshot of a record.

This reader validates bytes. Preset decoding, version migration, current-preset
updates, DSP application and durable writes remain separate operations.

## API domain and service boundaries

`hyperrig_preset_storage` embeds the unchanged selection runtime and adds the
sixteen mapping bytes and 256 scratch bytes. The public header and payload
buffers belong to the caller. Integrated preset-step, action, timer and edge
entry points intercept availability internally and forward the remaining
selection services, including the actual preset loader.

The read callback represents the entire original wrapper at `0x02002810`,
including range checks, physical reads and error handling. Zero means that all
requested bytes were written; a nonzero result may leave a written prefix.
Pointers are borrowed for the duration of the call, including size zero.
The verifier uses synthetic byte regions and injected failures, not device dumps
or an implementation of the physical flash driver.

Preparation (`0x020031d4`), priority (`0x020054a8`) and polling (`0x020027e4`)
remain synchronous external services. Their return values are ignored here.
Callbacks may mutate mapped state, but must preserve the selection domain and
buffer bounds. No re-entry, interrupt concurrency, retained buffer pointers or
overlapping header, payload and runtime storage are supported.

New wrapper validation requires both callbacks, even for a cached/no-I/O path.
Incremental and complete CRC APIs accept 0..1,490 bytes; a null data pointer is
allowed only for zero length. The record API requires maximum at most 1,490,
capacity at least maximum, and non-null header/payload pointers. If a callback
changes header length, it must remain within capacity and the 1,490-byte domain.
The header-only API retains the original uint32 maximum range. Invalid API
calls perform no writes or callbacks, returning -1, or -4 for the record API
to distinguish this new check from the original statuses. Address lookup returns
zero for a null runtime. These guards are new API behavior, not recovered
original input validation.

## Verification

The [instruction interpreter](../tools/preset_storage_machine.py) extends the
previous selection model with the seven original regions. It handles the signed
mapping byte, bitwise operations, unsigned maximum, register-pair moves and the
record reader's stack argument. Existing packet, predication and checked-stack
semantics are reused. The pinned decoder and ISA sources are recorded alongside
all source hashes in the report.

The completed run passed **2,312 C-versus-instruction comparisons**:

| Operation | Comparisons |
| --- | ---: |
| Block mapping / preset address | 259 / 1,060 |
| Availability cache | 235 |
| Header / complete record | 95 / 93 |
| Incremental CRC / complete checksum | 540 / 15 |
| Integrated preset step / action / timer / edge | 9 / 4 / 1 / 1 |

The checks compare return values, all previously mapped runtime bytes, the new
mapping and scratch fields, public header/payload buffers, and ordered semantic
arguments, destinations and mapped state at every service/read call. Stack-local
header addresses are normalized; their uninitialized bytes are not compared.
Coverage includes all mapping byte values, chunk boundaries, malformed headers,
CRC mismatch, failed and partial reads, cached outcomes and failed-load navigation.
Four stateful queries and eight mutating-boundary cases are subsets of the total.

All **177 new decoded instructions** were visited; the combined run visited
**405 of 699 instructions**, not every earlier control path. The unchanged
earlier components retain their separate coverage reports. There are also
554 zlib reference comparisons, 21 focused interpreter tests, 17 invalid-API
checks and two null-data/empty-CRC checks.

The combined host library builds with warnings as errors and UBSan. All four
components compile for pi32v2; the new relocatable object is 2,480 bytes.
This file size is not linked firmware size or a runtime resource measurement.
None of these target objects has run on the pedal. Hardware, audio, real flash
persistence and interrupt behavior were not tested in this milestone.

## Reproduce and continue

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows, the builder uses WSL Ubuntu:

```powershell
python -B tools/build_preset_storage.py --output build/reverse-preset-storage-new
```

Optionally pass `--mini-image` with the released `hyperrig-mini-v4.app.bin`
inside the workspace; only the reviewed hash is accepted. Outputs are the host
library, four target objects, `verification.json` and `build-manifest.json`.
Existing output directories are refused and generated artifacts stay outside
Git. The completed local run is `build/reverse-preset-storage-01`.

Preset preflight at `0x020079f6` is now covered by the
[preflight extension](PRESET_PREFLIGHT_RECONSTRUCTION.md), including layout and
legacy effect conversion. The [loader extension](PRESET_LOADER_RECONSTRUCTION.md)
now covers `0x0200ca7e`, keeping error returns, current-preset commit and the
remaining DSP application boundary distinct.
Storage preparation/cache invalidation and the underlying read/priority/poll
implementations also remain dependencies.
The [roadmap](REVERSE_ROADMAP.md) retains three-switch bank integration and
physical validation; Alpha 13 remains a placeholder.
