# Reconstructed capture container installation

Capture container installation and its actual flash-record reader now have
compilable C and an original-instruction comparison model. The unchanged
[capture slot loader](CAPTURE_LOADER_RECONSTRUCTION.md) can call this installer,
which executes the record/CRC/identity reader internally. Allocation ownership,
failure cleanup and mode/priority restoration are reconstructed. Parser, DSP-load
and platform service bodies remain explicit callbacks.

Sources: [`hyperrig_capture_container.c`](../firmware/src/hyperrig_capture_container.c)
and [`hyperrig_capture_container.h`](../firmware/include/hyperrig/hyperrig_capture_container.h).
Original Required Notice and license are retained. Earlier sources, completed
reports and tested firmware images remain unchanged.

## Pinned executable evidence

The original G v2 M5.71 image has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
CPU flash address `a` maps to decoded `app.bin` offset `a - 0x02000120`.
The inherited verifier checks the original image and its decoded copy before
decoding the selected functions.

| CPU range, end exclusive | Reconstructed behavior | Function SHA256 |
| --- | --- | --- |
| `0x02008586..0x020087cc` | Container installation and ownership | `1c9d2d89fb43a34f37c8e67b5c0bc7e1917eddfee30a379b73f4c61734fcd512` |
| `0x0201acd8..0x0201ad4c` | Capture record and identity reader | `e13aff6f7693309ace941d25a32b03157ead67ea4994ba7678afe644ba1970c5` |

Both regions and the used slot/header/identity/CRC dependencies are byte-identical
in the reviewed MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Original helper calls execute inside the instruction model. Existing C helpers
remain unchanged; the reader reuses the incremental CRC implementation in bounded
chunks to cover the full 8152-byte capture record domain.

## Addresses and ownership

The C API uses explicit uint32 address tokens and a supplied mapping callback;
it never treats a device address as a host pointer. The mapper supplies bounded
buffers for source bytes, cached bytes and allocation results. Embedded source
bytes are read-only. Runtime, request and mapped buffers must not overlap.
Mappings remain valid during the synchronous operation, and callbacks may not
retain private pointers, re-enter the operation or mutate the IO structure.

| Original location | Observed use |
| --- | --- |
| `0x02033c8c` | Embedded source address |
| State +676 | Cached owned-buffer token |
| Global +60 / +64 | Published source token and payload length |
| State +500 | Byte cleared before DSP preparation, set after successful capability query |
| State +4120 | Published probe result, represented by a separate four-byte field in C |
| State +436 | Context token read after successful preparation |
| State +280 | Mode captured before installation and restored afterward |
| Global +24 / state +204 | Input clock word and completion stamp; physical units remain unassigned |

State base is `0x01c26890`; global base is `0x01c1f180`. The new portable runtime
contains the existing storage/control view plus the word corresponding to state
4120. It is not a binary-compatible copy of the complete original RAM state.

The installer accepts lengths 1..8192. Invalid lengths return -1 before firmware
service calls. If a reader callback is supplied, or the direct source equals
neither the embedded address nor the current cached token, it requests
`(size + 3) & ~3` bytes. Allocation failure returns -100 before capturing mode or
clock and before progress notifications. Actual allocation and freeing remain
external services; the verifier supplies fixed buffers and records ownership.

After successful DSP loading and capability query:

- A new allocation receives a bounded memmove when the source differs from it.
  The cached token is replaced before freeing the previous token, including zero.
  The cached word is then read again, so a synchronous free-callback change is
  reflected in the subsequently published source.
- A direct cached source requires neither allocation nor freeing.
- An embedded source frees a nonzero cached token and clears that word after
  the free callback. The published source remains the embedded address.

The published payload length uses the original installer argument. These pointer
transitions do not establish the omitted parser's ownership requirements or prove
that a live DSP worker has switched sources safely.

## Execution and failures

After allocation, the installer captures mode and clock, reports event `(29,1,size)`,
signals activity 7, raises the gate and calls mode zero. It queries priority;
values at or below 26 cause a temporary set to 27. It then signals activity zero.

When the loader argument is `0x0201acd8`, the reconstructed reader executes into
the new allocation. Other nonzero loader tokens are outside the new API domain.
With no reader, the source is used directly.

The in-memory signature gate follows the original checks. `A2L1` passes. For other
prefixes, lengths 6144 and 7808 are rejected with -2; at lengths of at least 64,
`AM2\0`, `AM3\0` and `AM4\0` are also rejected. Lengths below four and a zero
source skip the signature reads and reach the external probe. A passing signature
does not establish that the payload is valid.

The probe result is an opaque token. Zero produces -2. A nonzero state word 416
causes a compaction-service call whose nonzero result becomes the installation
status. Only after those checks succeed does the installer clear state byte 500,
call preparation, call DSP load with the current context token, and query
capabilities. Capability failure becomes -3. The original three capability output
pointers refer to unused private stack bytes; the comparison exposes only its
semantic return value and does not claim to reconstruct those outputs.

| Failure stage | Original cleanup |
| --- | --- |
| Length gate | Return -1 without service calls |
| Allocation | Return -100 after allocation callback |
| Reader, signature, probe or compaction | Free the allocation token, which may be zero; skip DSP cleanup |
| Preparation, DSP load or capability query | Free the allocation token; run cleanup; report `(29,3,cleanup_result)` |

The installation result and cleanup result remain distinct. On completed work
paths the installer stores the clock word at state 204 and reports:

```text
(29, 2, ((current_clock - saved_clock) * 0xa00) | (status & 255))
```

Arithmetic wraps at 32 bits. This reproduces report arithmetic without assigning
time units. It signals activity 7, restores priority if it raised it, and restores
the captured mode if nonzero. A failed mode restore reports `(29,7,mode_result)`
and calls mode one as a fallback; that failure does not replace the installation
status. Gate zero and activity zero finish the sequence.

## Actual capture reader

The reader uses the same signed slot mapping as the existing slot loader. It
reads a 40-byte `TKGC` header with maximum payload length 8152, then the complete
payload. Its original record reader checks reflected CRC32 and polls between
256-byte CRC chunks. A failed payload read may leave a written prefix.

After record validation, it compares the reread length and header identity with
request words 4 and 8. It derives the resolved identity through the existing
extended-identity helper, using the last four payload bytes when applicable.
If request byte 16 is nonzero, that identity must equal request word 12. A mismatch
returns -3 without changing the request. Otherwise the reader stores the identity
at request offset 12, sets byte 16 to one and returns zero.

Request values are read at the original points, so synchronous read/poll callbacks
can affect the later comparisons. CRC polling can also change later payload bytes;
both models observe those changes. Length zero is valid for this standalone
reader: it still makes a zero-length payload read and validates the empty CRC.
The container installer separately rejects length zero.

The original reader can reread a larger accepted record than the allocation size
chosen by its caller. Such an out-of-buffer case is outside the instruction
comparison domain. The new C API checks capacity before the payload read and
returns -201 for insufficient capacity or unavailable mapped bytes. It also
returns new -200 for invalid API pointers/callbacks before service calls or writes.
These guards are new API behavior, not recovered firmware status semantics.

## Integrated slot path and remaining callbacks

`hyperrig_capture_container_slot` connects the unchanged slot loader to the real
reconstructed installer and reader. Thus the successful test path performs the
initial header/identity/signature checks, second header read, complete payload/CRC
check, request identity update, ownership transition and slot descriptor commit.
Failure tests also exercise the original slot loader's partial gain rollback.

The independently reconstructed [metadata journal/cache](CAPTURE_METADATA_RECONSTRUCTION.md)
is available as a separate component. This container comparison still supplies
metadata lookup through its explicit callback; it does not claim a combined
journal-to-installation proof. No flash writes occur in either component.

These service implementations remain external:

| Address | Boundary |
| --- | --- |
| `0x01c04a7a` | Payload probe |
| `0x020083d6` | Compaction |
| `0x020025ca` | Preparation |
| `0x01c04a8e` | Parser/DSP load |
| `0x01c04bac` | Capability query |
| `0x02002634` | Cleanup |
| `0x0203c15c` / `0x0203d218` | Allocation/free |
| `0x02002d06` / `0x020051fc` | Gate/mode |
| `0x02040850` / `0x020408d6` | Priority query/set |
| `0x02002810` | Physical read wrapper |

Progress notification, activity, CRC polling and outer priority helpers also
remain service boundaries. Memmove at `0x02032b2e` is a bounded memory-library
contract, not an interpreted library body. A scripted success result is not
evidence of successful capture processing on a device.

## Verification and reproduction

The completed `build/reverse-capture-container-01` run passed **262 comparisons**:
200 direct installations, 46 direct record reads and 16 integrated slot loads.
All **229 of 229 new instructions** were visited; the integrated run visited
630 of 1,628 combined instructions. Prior milestones retain their own coverage.

The comparison covers results, all 21 mapped memory regions, ordered semantic
service arguments and state at every boundary, read addresses/destinations/counts,
request identity updates, copied payload bytes and untouched buffer tails. It
includes 21 mutating-boundary cases and 110 bounded memmove executions. Private
stack padding and incidental caller-saved arguments are excluded.

Cases exercise allocation rounding/failure, embedded and cached sources, all
signature branches, every major failure stage, low/high priority, failed mode
restoration, unsigned clock wrap, record sizes through 8152, partial reads,
CRC and requested-identity mismatches, extended identities and integrated rollback.
Nineteen focused instruction tests, nineteen invalid-API checks and three new
mapping/capacity guard checks passed. Independent review found no correctness
mismatches and separately checked pointer publication and representative reader
lengths, including 8152.

The host library builds with warnings as errors and UBSan. Seven component and
dependency objects compile for pi32v2 r3. The new object is **3,200 bytes**, SHA256
`dcce7cedaf96166b341b6d12a153d70e87f992627293fa916dc9d3e3b3c6da6a`.
This is relocatable object size, not linked firmware size, RAM use or latency.
The C source SHA256 is
`3afbde31bf40454fa64fa4119ddd3e2ad131448a50a00a817ebf3a3cc582181e`;
the comparison report SHA256 is
`3ab7bad89e375344c3fcce1f075c8ca647fc60ffcfece450cdda7d21f83120f1`.
No hardware, audio, timing or durable-write test was performed.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_container.py --output build/reverse-capture-container-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the workspace.
The builder refuses existing output directories. A host library, seven target
objects, source-hashed comparison report and artifact manifest are stored in the
new ignored directory. Generated artifacts remain outside Git.

Next, recover probe, preparation, parser dispatch and cleanup ownership, and join
the metadata journal and container components into one comparison. Journal writes
and the top-level preset application handler remain separate work.
