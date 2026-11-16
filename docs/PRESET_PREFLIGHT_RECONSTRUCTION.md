# Reconstructed preset preflight and legacy conversion

Three more original functions are reconstructed in portable C: preset preflight,
the legacy-effect predicate and its parameter converter. Preflight reuses the
[record reader](PRESET_STORAGE_RECONSTRUCTION.md), then converts supported old
layouts into the working preset buffer. It does not apply that buffer to DSP
state or commit the current preset.

Sources: [`hyperrig_preset_preflight.c`](../firmware/src/hyperrig_preset_preflight.c)
and [`hyperrig_preset_preflight.h`](../firmware/include/hyperrig/hyperrig_preset_preflight.h).
The original Required Notice and license are retained. All earlier reconstructed
sources and verification reports remain unchanged. These are development
components; no firmware image is produced or installed.

The later [loader component](PRESET_LOADER_RECONSTRUCTION.md) integrates this
unchanged preflight into control navigation and reconstructs its caller's commit,
binding and report sequence. The results below remain the preflight baseline.

## Original functions and MINI binding

The G v2 M5.71 reference application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x020079f6..0x02007b88` | Read, preflight and convert a preset | `8359a35551b62d4a887581bc6f312ea9210ff085b5a813064662f55c2e32583b` |
| `0x0202a43c..0x0202a452` | Identify legacy effect IDs | `baa81814a8b890510137c1867ef17d6fc7b7c348c67474eb344c2b9b4612589b` |
| `0x0202a452..0x0202a50a` | Convert an ID and its parameter words | `b9003b85b03e5c2e621fff2b5c53a5c1b4bc4aae896bd340224cc981dab321e0` |

The eleven-byte curve at `0x0203b334` is
`16, 19, 22, 25, 28, 32, 37, 43, 50, 61, 81`, SHA256
`778e066d4dd51f134accc9984ad145947997ded8cf60c0839191933d2e88d848`.

All three new regions, all twenty-one earlier function regions, the curve and
the two library regions below are byte-identical in the released MINI v4
application, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Byte identity does not establish target execution of the reconstructed C.

## Preflight order and error state

The original working buffer is 1,490 bytes at `0x01c24790`. Preflight receives a
uint32 preset ID and caller-owned 40-byte header buffer, then:

1. Clear the entire working buffer.
2. Call storage preparation and acquire the priority helper, in that order.
3. Reject IDs outside 0..31, releasing priority first. Otherwise resolve the
   preset address and use the shared header/payload/CRC reader.
4. Release priority before examining the record-reader result or converting bytes.
5. If reading succeeded, reread the header length, perform the layout conversions
   below and convert legacy effect parameters.

| Original result | Meaning and retained output |
| --- | --- |
| 0 | Reading and applicable conversions completed. |
| -1 | Out-of-range preset, header rejection or header-read failure. Working bytes were already cleared. Header reads can leave partial header output. |
| -2 | Body-read failure. Its written prefix remains in the cleared working buffer. |
| -3 | CRC mismatch. The raw body remains, with no layout or effect conversion. |
| -4 | Version byte below 5 with declared length above 1,200. The special 1,474-byte tail conversion may already have occurred. |

Preflight does not use or update the availability cache itself. A cache hit or
cached failure does not bypass this read. Preparation and other callbacks can
still change storage state through their external contracts.

This function is not complete schema validation: empty records and some short
records can succeed because the unread part of the working buffer was cleared.
Effect count is bounded by the loop at sixteen, without rejecting a larger byte.
These original behaviors are preserved.

## Layout conversion

All offsets in this section are bytes relative to the working buffer. Field names
describe observed access patterns; they are not recovered original C symbols.

For a declared length of **1,474**, five trailing groups at offset 1,424 grow
from five little-endian halfwords to six. Group `g` moves its ten bytes from
`1424 + 10*g` to `1424 + 12*g`, then has a zero halfword at `1434 + 12*g`.
The original works backward through groups and words to preserve overlapping
input. It performs this conversion before checking the version byte.

If the byte at offset 0 is **below 5**, lengths above 1,200 return -4. Otherwise
the old layout expands in this order:

| Part | Old offset/stride | New offset/stride | Operation |
| --- | --- | --- | --- |
| Trailing twenty bytes | 1180 | 1340 | Copy all twenty bytes. |
| Four scene blocks | `268 + 228*s` | `300 + 260*s` | Preserve the leading four bytes; expand each of sixteen 14-byte entries to sixteen bytes with two trailing zeros. |
| Sixteen effect records | `12 + 16*i` | `12 + 18*i` | Copy sixteen bytes and append a zero halfword. |

Scene and effect loops run backward. The first twelve bytes are retained. The
original does not rewrite the version byte, header length or header CRC after
conversion: the header continues to describe the record that was read. This
output is an intermediate working representation, not a newly serialized record.

## Legacy effect conversion

After layout conversion, the function scans at most sixteen effects, stopping
earlier at the count byte at offset 1. The type byte is at `13 + 18*i`.
Only original IDs **6** and **24** are converted. Other IDs and their parameters
are retained. These are numeric protocol IDs; effect model names are not inferred
from this function alone.

For either recognized ID, parameters are converted first at `16 + 18*i`, then
for each of four scenes at `306 + 260*s + 16*i`. Each call operates on seven
little-endian signed 16-bit words. The record type is replaced by the returned
ID; the original ID is retained for all four scene conversion calls.

For **ID 6 to 27**, let `a`, `b` and `c` be the first three input words clamped
to 0..100. The seven outputs are:

```text
[a / 2 + 40, interpolated_curve(a), b * 7 / 10, 0, c, 0, 40]
```

Integer division truncates. For the curve, `i = min(a / 10, 9)` and the output is
`curve[i] + ((a - 10*i) * (curve[i+1] - curve[i]) + 5) / 10`.
The endpoint 100 uses segment 9 and produces 81. Negative inputs clamp to zero.

For **ID 24 to 29**, the first four words are preserved. Word 4 is capped at 27
only when it is at least 28; negative values remain negative. Word 5 becomes 50
and word 6 becomes zero. A null parameter pointer maps the ID without writes.
Unrecognized uint32 IDs are returned unchanged, including values above 255.

## API and explicit boundaries

`hyperrig_preset_runtime` embeds the unchanged storage runtime and adds the
1,490-byte working buffer. The caller provides a separate 40-byte header buffer
and both storage callbacks. Missing runtime, header or required callbacks return
the new API error **-5**, before any writes/calls. This is distinct from the four
original failure statuses. A non-null effect parameter pointer must reference
fourteen writable bytes; null is an original supported ID-only query.

Header and runtime storage must not overlap. The existing storage callback
domain applies: synchronous mutations must stay within buffer bounds, and no
re-entry or interrupt concurrency is modeled. In particular, the priority-release
callback observes raw bytes and can change the length/version consumed by the
subsequent conversion. There is no second CRC check after release.

Physical reads, storage preparation, priority and polling remain external.
The instruction oracle also uses explicit bounded memory-library contracts:

| Library region, end exclusive | Contract used here | Region SHA256 |
| --- | --- | --- |
| `0x02033412..0x0203343e` | Zero exactly the 1,490-byte working buffer | `a8119bcb0ef6f337215381ded40bd4a66cb7e774a12230f5da572358311c18b3` |
| `0x02032b2e..0x02032bf0` | Overlap-safe moves of fourteen or sixteen bytes within that buffer | `7c3346543954e137b7503cc91cd5238d5e6fc5e91861bca749e85e6f9c2ededc` |

Their original instruction bodies are **not executed by this verifier** and do
not contribute to its instruction coverage. The C uses byte clearing and backward
copies for these operations. The immediate `rep 4 5` in preflight itself is
interpreted as five iterations of its original two-instruction word-copy body.
This restricted repeat interpretation uses the pinned ISA project's
[block/loop findings](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/hw/fm1-2026-10-24-v3/README.md).

## Verification

The [verifier](../tools/verify_preset_preflight.py) passed **1,754
C-versus-instruction comparisons**: 437 preflight cases, 259 predicate cases and
1,058 parameter-conversion cases. It compares return values, all prior mapped
storage/control/public-buffer bytes, the entire working buffer and ordered
semantic arguments plus mapped state at each external read/service call.

The corpus includes every version byte and serialized type ID, invalid preset
IDs, signed parameter extremes, every curve input from 0 through 100, layout and
length boundaries, all effect slots/four scenes, partial reads and CRC errors.
Three consecutive preflights and five mutating-boundary cases are subsets of the
total. Five invalid-API checks and 21 focused interpreter tests also passed.
The focused tests independently construct expected layouts and parameter values.

All **204 new instructions** were visited. This run visited **314 of 903 combined
instructions**, not every path of the earlier components. Earlier reports retain
their separate coverage. The new host library builds with warnings as errors and
UBSan; all five components compile for pi32v2. The new relocatable object is
1,684 bytes, which is not a linked firmware size or a runtime measurement.
None of these target objects has run on the pedal. There is no new hardware,
audio, persistence-write or DSP application test.

## Original loader trace and later reconstruction

Static inspection of the caller at `0x0200ca7e..0x0200cb3c`, SHA256
`f396922c03e8dfd2024e76975bd5af03c91ebcb37969e32503579a66e92a87e2`, establishes
the boundary used for the subsequent loader reconstruction:

- Any nonzero preflight result branches to return -1 before the caller's
  application call and current-preset write. Detailed preflight errors are lost.
- Successful preflight reaches `0x020092fa` with the preset ID and two local
  output pointers. This application dependency is not reconstructed here.
- On return, the caller writes the preset ID to global offset 92 without testing
  the application return value. It later passes that value to a notification
  when the notification path is enabled, and returns zero.
- Snapshot/comparison and reporting services occur between application and
  return. Their state effects are now covered by the loader component.

These were static observations in this milestone. The
[loader extension](PRESET_LOADER_RECONSTRUCTION.md) now compares the caller and
its binding/report helpers against the original instructions. Working-state/DSP
application remains external, so those comparisons do not establish live state
application or persistence. Storage preparation/cache invalidation also remains
on the [roadmap](REVERSE_ROADMAP.md).

## Reproduce

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows the builder runs through WSL Ubuntu:

```powershell
python -B tools/build_preset_preflight.py --output build/reverse-preset-preflight-new
```

Optionally supply `--mini-image` with the reviewed `hyperrig-mini-v4.app.bin`
inside the workspace. Outputs include the host library, five target objects,
`verification.json` with source hashes and `build-manifest.json`. Existing output
directories are refused. Generated artifacts remain outside Git. The completed
local run is `build/reverse-preset-preflight-01`.
