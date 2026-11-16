# Reconstructed capture loading and gain metadata

The capture slot loader now has compilable C and an instruction-level comparison
model. It uses the existing header, extended-identity and descriptor helpers,
reconstructs gain metadata and signature rejection, and preserves the original
reuse and partial rollback behavior. The metadata journal lookup and capture
container installation remain explicit external callbacks. A successful scripted
installation is not evidence that a capture has executed on the pedal.

Sources: [`hyperrig_capture_loader.c`](../firmware/src/hyperrig_capture_loader.c)
and [`hyperrig_capture_loader.h`](../firmware/include/hyperrig/hyperrig_capture_loader.h).
The original Required Notice and license are retained. Existing reconstructed
sources, completed reports and firmware images are unchanged.

## Pinned evidence

The original G v2 M5.71 image has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
CPU flash address `a` maps to decoded `app.bin` offset `a - 0x02000120`.
The inherited verifier checks the pinned original before decoding instructions.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x02007e62..0x02007e9e` | Validate packed metadata | `977e40bcc6ffa499a5f7ba54bc8e80e02f6d4b72ac00b54dfd43165ff844f69c` |
| `0x02007e9e..0x02007eac` | Extract gain or zero | `dcc2c7ce4fd995e11b6533fd13ce17623c3dd28660fb108b27cfdc5be84ba03d` |
| `0x02007eac..0x02007ece` | Extract optional signed auxiliary value | `a2dcdd40359de853cc0c5f37ae9fde9ca87d6eae000300f599c8b424f528ea5a` |
| `0x02007ece..0x02007ee2` | Signed clamp to -24..24 | `1d2db9375cb992a88607359c1ab00f04fca9e0c9920d5134d06e2e39f0ff1b67` |
| `0x02007ee2..0x02007ef2` | Gain table lookup | `1812e38ecb3f2cd29954b36dbaa6431ceb9a422ac3929c422ea4cd72ce964d09` |
| `0x02007ef2..0x02007f3a` | Combine primary/secondary gain and mark update | `e8e1dbddbc3ceb0fb35ea2e2f6e867392ccb0b5f268d6e7da4f2faf3dc747ca8` |
| `0x02007f3a..0x02007f50` | Set clamped primary gain and recompute | `8e3bc867bc49fc0b6a48ee177ffb3cc5d912f49d8e1f63a19238f8f8b3901f44` |
| `0x02007f50..0x02007f7e` | Apply packed metadata | `8dadc1abe4f072984b4b735a2f7fea8e95f27c9f9e636062ad32a2032531766e` |
| `0x02007f7e..0x02008016` | Reject unsupported capture signatures | `35c80c9564cab3eae445ff6552bc7090163b0ad3dc1355bfefa4fc9c4533e2e3` |
| `0x020087cc..0x02008972` | Capture load/reuse/rollback orchestration | `dacef25e4d770e3071c0c3b4db040a08ef17124838de91904f2489908ab965cb` |

The 49-word gain table occupies `0x02033bc8..0x02033c8c`, SHA256
`cd539f2ab0183841f5adecc529273af02213eeb221c7723ef556f9229aa620da`.
The lookup's zero-index address is `0x02033c28`; signed indices range from -24
through 24. All ten code regions, this table and the used asset/header dependencies
are byte-identical in the reviewed MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

## Metadata and gain state

The low byte is a signed gain parameter and must be between -24 and 24. Bits
8..23 form a signed auxiliary value; the high byte selects the encoding:

| High byte | Required auxiliary value | Auxiliary output |
| --- | --- | --- |
| 0 | Exactly zero | Absent |
| 1 | -200 through 400 inclusive | Present, sign-extended to 32 bits |
| Other | Invalid | Absent |

Invalid metadata produces gain zero. The standalone auxiliary helper leaves its
output untouched when no auxiliary value is present. The apply helper instead
clears the stored auxiliary value when absent. These are distinct contracts.

| Offset from state base `0x01c26890` | Observed use |
| --- | --- |
| 16 | Boolean update flag supplied by the caller |
| 264 / 268 | Primary and secondary signed gain words |
| 272 | Combined scale word |
| 276 | Update counter, incremented modulo 2^32 |
| 696 / 700 / 704 | Metadata gain, auxiliary value and presence word |
| 1780..1795 | Capture reuse descriptor |

The primary lookup is clamped to the table range. If the secondary word is
nonzero, its clamped lookup is multiplied by the primary scale with a 64-bit
accumulator initialized to `0x800000`, then shifted right by 24. A zero secondary
word skips the multiplication. The table's zero entry is `1 << 24`.
Every recomputation writes the boolean flag and increments the counter, including
rollback. These numerical observations do not establish physical gain units or
prove that an audio consumer has applied the result.

## Header, reuse and signature behavior

The loader calls activity with 6, raises the priority boundary, and reads a
40-byte `TKGC` header with maximum payload length 8152. Header rejection restores
priority and reports -1. Header acceptance invokes the existing extended-identity
resolver, then the external metadata lookup, then restores priority.

Slot addressing retains the original signed comparison and 32-bit wrapping:

```text
if signed32(slot) < 8:
    address = 0xdf000 + (slot << 13)
else:
    address = 0xcf000 + ((slot + 0x7fff8) << 13)
```

This arithmetic is compared even for nonphysical slot values. It does not claim
that the underlying flash reader accepts those addresses.

Reuse succeeds if the full supplied slot word equals the current byte at global
offset 9, or if identity resolution succeeded and the capture descriptor matches.
The same-slot case succeeds even when the extended-identity trailer read failed.
It then leaves the old descriptor unchanged. Otherwise a successful identity
updates presence, identity and size, clears the descriptor's format byte and
auxiliary word, and preserves its two padding bytes.

Reuse commits the low slot byte and sets global offset 18 to 255, applies metadata
with update flag zero, and reports `(20, slot | 0x500, 0)`. It does not perform
the signature check or call the installer.

For a fresh load the signature helper always reads four bytes at
`capture_address | 0x28` before inspecting the header length. A read failure or
length below four returns zero. Exact `A2L1` also returns zero, including at
lengths 6144 and 7808. Otherwise either of those two lengths is rejected. At
other lengths of at least 64, `AM2\0`, `AM3\0` and `AM4\0` are rejected.
The caller reports -111 for rejection without applying metadata or installing.
A zero signature result means only that this gate did not reject the input;
validation inside the omitted installer still matters.

## Installation request and partial rollback

Before installation, the loader saves state words 696/700/704 and applies the new
metadata with update flag one. It passes `(0, captured_size, 0x0201acd8, request)`
to the external installation callback. The loader token is opaque to the C API.
Exactly 17 initialized request bytes are exposed:

| Request offset | Value |
| --- | --- |
| 0 | Slot word |
| 4 | Header payload size |
| 8 | Header word at offset 8 |
| 12 | Resolved identity, or initial zero if resolution failed |
| 16 | One for successful resolution, otherwise zero |

The callback may synchronously change these request bytes and caller-owned
runtime state. It may not inspect adjacent stack storage, retain pointers,
re-enter the loader or modify the borrowed header. The verifier normalizes the
native and C pointers while comparing all 17 input bytes and all mapped runtime
bytes at the call boundary.

After success, request byte 16 decides whether a descriptor is present; its
identity comes from the possibly changed request word at 12. Descriptor size
comes from the loader's saved size, even if the callback changed request word 4.
An absent identity clears only the presence byte. The loader then commits the
current slot and reports `(20, slot, 0)` without the reuse flag.

After a nonzero installation result, the loader restores metadata words
696/704/700, recomputes primary gain from the restored metadata gain with flag
one, and clears descriptor presence. It passes through the installation status.
This is a **partial rollback**:

- The update counter normally advances twice, once before installation and once
  during rollback. Callback counter changes are also retained before increment.
- Secondary gain is not restored. Recomputed scale uses its current value.
- Primary gain is restored from saved metadata word 696 and clamped; it is not a
  saved copy of word 264.
- Other callback writes and the descriptor's nonpresence bytes survive.

Notifications precede the final activity-zero call on every path. A caller must
not infer an atomic transaction from the original error handling.

## Verification

The completed `build/reverse-capture-loader-01` run passed **6,091 comparisons**:

| Entry point | Comparisons |
| --- | ---: |
| Metadata validity / gain / auxiliary | 820 each |
| Signed clamp / table lookup | 54 each |
| Gain mixing | 2,405 |
| Primary gain update | 162 |
| Metadata application | 118 |
| Signature gate | 533 |
| Capture load | 305 |

All **307 of 307 new instructions** were visited; this run visited 401 of 1,399
combined instructions. Earlier components retain their separate coverage reports.
The model executes header validation, identity resolution and descriptor helpers
internally. It compares semantic results, all 15 mapped memory regions, read
addresses/destinations/sizes, semantic callback arguments and state at every
callback. Private stack padding and incidental return registers are not treated
as public outputs.

Cases include all low metadata bytes in both supported versions, signed auxiliary
boundaries, all 49-by-49 table combinations, wraparound, header/trailer/signature
read failures, current-slot and descriptor reuse, install errors and **15 mutating
boundary cases**. Eighteen focused instruction tests and thirteen invalid-API
checks passed. Invalid C pointers/callbacks produce new status -200 before writes
or calls. The mix/set/apply functions return new API status zero on success;
their original return registers are incidental.

The host library builds with warnings as errors and UBSan. All six component and
dependency objects compile for pi32v2 r3. The new target object is **3,008 bytes**,
SHA256 `1eafd18b0bb340eff85fd4f0d5b6e670eedd30ab9a8895043da2698b5e2f095c`.
This is relocatable object size, not linked firmware size, memory use or latency.
The C source SHA256 is
`d129347bc2a73a408cd59bc0b1cc1a6b5d2319a17841894879e22274c90f478f`;
the comparison report SHA256 is
`06a8a95b755be9b4bd0e4583e3e9d53ae3584a8fa2a2be1feae79eb980371566`.
No hardware, audio, timing or durable-storage test was performed.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_loader.py --output build/reverse-capture-loader-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the workspace.
The builder refuses existing output directories. It writes a host library, six
target objects, source-hashed comparison report and artifact manifest into the
new ignored directory. Generated artifacts remain outside Git.

## Remaining installation and persistence boundaries

Metadata lookup `0x02007dbe..0x02007e62`, SHA256
`ba7660a8035a805ba7dcc14932097811f8dc7e3707861f185b78b1f736ed0ad2`,
is statically traced but not executed here. It uses cached 20-byte entries and
the journal scanner at `0x02007ce0`. Journal selection, CRC handling and persistence
remain to be reconstructed before treating metadata lookup as verified storage.

Container installation `0x02008586..0x020087cc`, SHA256
`1c9d2d89fb43a34f37c8e67b5c0bc7e1917eddfee30a379b73f4c61734fcd512`,
also remains a callback. Static tracing identifies a size gate of 1..8192,
conditional allocation, mode/priority changes, invocation of callback
`0x0201acd8`, payload probing, parser/DSP setup, ownership transfer and cleanup.
Its downstream calls include `0x01c04a7a`, `0x020083d6`, `0x01c04a8e` and
`0x01c04bac`. None of those bodies are executed by this milestone.

Recover installation and the journal next, then connect this loader and the
[IR loader](IR_LOADER_RECONSTRUCTION.md) to complete preset application. In
parallel, [coefficient staging/conversion](BIQUAD_COEFFICIENT_RECONSTRUCTION.md)
has a verified baseline while its mathematical producer remains unfinished.

Subsequent milestones now reconstruct [container installation and its reader](CAPTURE_CONTAINER_RECONSTRUCTION.md)
and the [metadata journal/cache](CAPTURE_METADATA_RECONSTRUCTION.md). The former
executes the slot loader together with the installer and record reader; the latter
retains a separate comparison. The [bounded coefficient generator](BIQUAD_GENERATOR_RECONSTRUCTION.md)
also executes its mathematical dependencies. Results above retain their original
scope and immutable evidence.
