# Capture metadata text command reconstruction

This milestone reconstructs the complete original `CTRIM` command body at
`0x0200a888..0x0200ad06`. It connects text parsing to the previously recovered
metadata lookup, journal append, payload reload, complete rewrite and gain
application routines. The new C module is an offline reconstruction, not original
source, a linked firmware image or a command enabled in the shipped editor.

The command's allocation and retry paths execute original decoded instructions in
the comparison model. Allocation, storage access, clocks, notifications, scheduling
and text output are synthetic services. No device, flash, USB or audio test is
performed. Synthetic byte storage does not establish durable writes or behavior
during power loss.

Required Notice: Copyright (c) 2026 Manuel Aguirre

The reconstruction retains the original project's
[PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md) and required
notice. `CTRIM`, `TKGC`, `TKGT`, function addresses and original message tokens are
source/protocol evidence, not new product interface names.

## Inputs and original regions

The pinned M5.71 input is
`artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin`, SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The model checks that `analysis/firmware/m571_g_app/app.bin` is its actual unpacked
application before decoding. Existing input images, earlier reconstructed modules
and earlier reports are unchanged.

Ranges below have exclusive endpoints. The complete command range overlaps the
append continuation recovered previously; instruction coverage counts each address
once.

| Body | Start | End | Original bytes SHA-256 |
| --- | --- | --- | --- |
| Complete command | `0x0200a888` | `0x0200ad06` | `58caf568830127b1c6c3ca3ad7f0160dfcf72ac648f3f7a6ad8acf654a7a0f22` |
| Packing gain clamp | `0x0200a5e2` | `0x0200a5f6` | `1d2db9375cb992a88607359c1ab00f04fca9e0c9920d5134d06e2e39f0ff1b67` |
| Metadata pack | `0x0200a5f6` | `0x0200a622` | `45455ec151b74db856902c005c6aa6d9644fc0ea8dc0d03b77dee2a00ecf2aff` |
| Trim text parser | `0x0200a7de` | `0x0200a868` | `169a2599f4eadb77c6d9e42df144005b7b229f758b57238de1934c75bdd3f532` |
| Slot parser | `0x020072ea` | `0x02007324` | `675599f49bb4b8fac90266f3fb340f873324e9face5c65534ff130cd1196a918` |
| Prefix comparison | `0x020283b4` | `0x020283ce` | `531ed2c20edd5a3e52391f34119b5c3a8f7ec23908ae9e5e387bc2e9ee5184d3` |
| Decimal conversion core | `0x020283ce` | `0x020284be` | `8807fd9cbe6d52830a5dcd65d5894b78c59af149da7cca6e17a2cc52883cfc6f` |
| Decimal wrapper | `0x020284be` | `0x020284d6` | `e1f2a3fa9713faed30696f128bc39763bbd2822bdab8c63478ce73eb6e979051` |
| Status message selection | `0x02007976` | `0x020079bc` | `bfb4376b49790dcbb46b3673d91fe01795a1f5bc911be192f442b054237dddc5` |

The model also executes the unchanged original header validator, identity
resolver, scanner/cache, record reader, chunked CRC, append/write/erase/rewrite
wrappers, byte comparison and gain routines. See
[metadata reconstruction](CAPTURE_METADATA_RECONSTRUCTION.md),
[journal reconstruction](CAPTURE_JOURNAL_RECONSTRUCTION.md) and
[capture loader reconstruction](CAPTURE_LOADER_RECONSTRUCTION.md).

Decimal parsing executes the native base-ten path with the pinned character table
at `0x0203a343..0x0203a444`. The reset-copy words at
`0x01c1f39c..0x01c1f3a4` point to that table and the errno word at `0x01c1f3a4`.
The locale pointers/table are immutable model inputs; there is no claim about
runtime locale replacement. Overflow saturates to signed 32-bit limits, consumes
the remaining digits and writes `34` to errno. Successful conversion preserves
the previous errno value. Base-zero and hexadecimal conversion are outside the C
API and the command's call domain.

## Recovered command behavior

The input is the argument tail after `CTRIM`, including a terminating NUL within
1..256 bytes. An empty tail reports the current values. Exact lowercase `live`
followed by space or NUL selects the current-state path. Otherwise the original
decimal slot parser accepts slots 0..14. Its end pointer skips ordinary spaces,
but does not require a separator: `2-1.0` reaches slot 2 with trim -1.0.

Without a new trim, a stored-slot query validates its header and resolved identity,
forces a metadata scan, updates the cache and reports the decoded fields. A scan
failure on this lookup path retains the earlier routine's fallback/cache behavior.
Invalid versioned metadata yields zero trim and no auxiliary value. The command's
stack initializes that auxiliary output to zero before decoding it.

Trim accepts an optional sign, an integer part and at most one fractional digit.
The command then requires -12.0..12.0 in 0.5 steps, stored as -24..24 integer
steps. The optional auxiliary input accepts a complete decimal integer from
-200..400 or a single `-` to clear its presence. The integer parser accepts its
native leading whitespace, but trailing spaces after the auxiliary integer are
rejected. Omission preserves the previous auxiliary field. The original error
message labels it as input level in `dBu x10`; no physical calibration is inferred.

The metadata packer clamps trim to -24..24 and auxiliary input to -200..400.
Absent auxiliary input produces only the signed low trim byte. Present auxiliary
input uses the signed middle 16 bits and version byte one. The standalone packing
API compares extreme uint32 bit patterns as signed values.

For a stored update, the command reloads and resolves the header again, obtains a
clock stamp and scans the journal. Scan failure here is an error. Equal packed
metadata skips storage writes. Otherwise it attempts at most two append records,
advancing past failed program/readback attempts. A verified append retains the
existing notification and cache-invalidation behavior.

When append space or retries are exhausted, it:

1. Requests the old payload length rounded to four bytes, with a minimum of four.
2. Reloads the header and payload through `0x020079bc`, including native payload
   CRC computation and scheduler calls between 256-byte chunks.
3. Replaces the header word at byte offset 12 with the new packed metadata.
4. Calls the complete `0x0200a622` erase/write/readback helper, retrying it once on
   failure with the same saved payload length and allocation.
5. Frees the allocation on every post-allocation exit. Successful compaction
   reports cursor zero, the capacity recalculated from that payload length, and
   the rewrite flag.

An allocation failure maps to `-100` internally. Reload payload-read failure
`-2` is reported as `-1`; header failure and CRC/write verification failures retain
their original error categories. Every unsuccessful stored operation exits before
applying the requested gain. Successful stored operations, including unchanged
metadata, apply the gain only if their slot matches the current slot at the final
comparison. The `live` path always applies it. Gain application updates the
previously recovered state words and scale table calculation; it is not an audio
test.

## Service contracts and new API limits

[The header](../firmware/include/hyperrig/hyperrig_capture_command.h) defines
separate allocation/free/text callbacks and composes the existing journal IO.
Callbacks can synchronously mutate caller-owned runtime state. They cannot retain
private stack/input pointers, change IO, inspect beyond a borrowed buffer or
re-enter the command. A read initializes only its documented destination. Program
sources and input text are immutable. Buffers are disjoint.

The text service receives original argument words, with addresses represented as
tokens rather than host pointers. `0x0200a768` receives ten words: mode token,
slot, trim steps, auxiliary presence/value, saved flag, journal visibility,
cursor, capacity and rewrite flag. `0x02007010` receives its format token and zero,
one or two arguments. The actual report helper, formatting and transport bodies
remain external. Comparisons verify their exact argument selection, order,
callback-visible state and raw returned word. They do not claim to compare rendered
text. The public C function returns API status separately from that raw native
return word.

New `-200` rejects invalid pointers, missing services and input bounds before
calls or writes. New `-201` handles a safety boundary absent from the original:
the reloaded header could request more payload bytes than the earlier allocation
request. C frees that allocation and stops before the oversized payload read,
preserving the raw output argument. The instruction model rejects this domain;
the new guard has a separate C check, not an original-equivalence claim.

The comparator tracks a logical allocation inside its larger synthetic memory
map and rejects reads/writes beyond the actual request. The sanitizer harness
separately uses exact-size `malloc` allocations and actual `free`, checking the
command's ownership and use-after-free behavior. No allocator implementation or
physical storage driver is supplied.

## Verification method

[The instruction model](../tools/capture_command_machine.py) derives a new wrapper
around the unchanged earlier models. It decodes original bytes and executes
individual native instructions independently of the C control flow. Inherited
ISA semantics remain a shared assumption; this is not a general emulator or new
hardware validation.

Dependent parallel instructions retain pre-packet register values. In particular,
the fractional trim parser's load uses the old text pointer, the auxiliary decode
output begins at zero, and report stack words retain their pre-packet values.
The `{r6,r4}` register-mask load uses ascending register order without base
writeback. Decimal wrapper tail-call handling restores its frame while preserving
the caller's return address.

[The verifier](../tools/verify_capture_command.py) compares the C and native models'
20 mapped regions at each external service boundary, exact program bytes, read
addresses/lengths, all text argument words, parser end offsets/errno, allocation
requests/free order and final synthetic storage. It includes carried commands,
runtime callback mutations, current/noncurrent slots, versioned metadata,
extended identities, short programs, failed and corrupted reads, full journals,
reload failures and both rewrite attempts. The source manifest is independent of
earlier generated build directories.

Run the standalone build from the repository root, choosing a new output directory:

```text
python tools/build_capture_command.py --output build/reverse-capture-command-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder produces a warning-clean UBSan host library, nine freestanding pi32v2
objects, the ASan/UBSan harness, focused tests, instruction comparisons and hashed
reports. It refuses to overwrite an existing output directory. The optional MINI
binding checks the reviewed v4 image SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`
and byte identity of all executed dependency regions, static configuration and
the gain table. It does not create or modify a firmware image.

## Completed validation

The final immutable output is `build/reverse-capture-command-01`:

| Check | Result |
| --- | --- |
| C/native comparisons | 1,114: 209 complete commands, 418 trim parses, 271 decimal parses, 216 metadata packs |
| Complete command instructions | 399/399 visited |
| Newly decoded instructions | 531/545 visited |
| All loaded instructions, including inherited modules | 1,226/2,206 visited |
| Focused instruction tests | 22 passed |
| Sanitizers | 65 exact storage/allocation cases and 256 exact input buffers, with 768 input API calls |
| Invalid API checks | 21 passed before calls/writes |
| New allocation-growth guard | 1 independent C check passed |
| Callback mutation cases / carried commands | 8 / 6 |
| Successful allocations / matching releases | 25 / 25 |
| MINI v4 binding | 37 named code regions plus static configuration and gain table match |
| Hash audit | All 46 source hashes and 13 artifact hashes match |

Coverage is instruction visitation, not exhaustive path coverage. Four unvisited
status-helper instructions handle statuses `-110`/`-111` that this command does
not generate. Two prefix-comparison instructions handle count zero; the command
always compares four bytes. Eight decimal-core instructions handle automatic or
hexadecimal prefixes; the command always passes base ten. The report lists all
14 addresses explicitly. Earlier modules contain additional unvisited entry
points outside this command's dependency path.

The new freestanding pi32v2 object is 3,948 bytes. Its SHA-256 is
`5ceaf9984ebaf81986df338963c213810efef7704fda79ff24fbc15f7eb28b2e`.
The new C source SHA-256 is
`c80921f86795877f93b479667c86e5d3bb24776408acf0170cdd4cdd95b4f14d`.
The final `verification.json` SHA-256 is
`0cd2c25f458ebb074e73002a16986d7f38c6075b9837ce26365fb5ec5481f54e`.

The earlier journal and metadata object hashes remain
`d075adb2cd3a8a4ecfcc90912b85c2f76869804139057de99f131561302d00da`
and `f739de0d65039b38e8fe2a0689c43379231cc2218125f30993f1022f1e930b53`.
Development probes used `build/reverse-capture-command-dev-01`; those preliminary
artifacts are retained separately and are not the final validation record.
