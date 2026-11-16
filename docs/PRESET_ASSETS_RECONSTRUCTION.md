# Reconstructed asset and application-layout dependencies

Nine dependencies of preset application are now reconstructed in portable C:
asset-header fallback, identity selection, trailer reading, routing metadata,
reuse-descriptor comparison and three small flag/arithmetic helpers. These build
on the unchanged [storage header reader](PRESET_STORAGE_RECONSTRUCTION.md).
They are independently executable components; the application handler at
`0x020092fa` remains outside the integrated [loader model](PRESET_LOADER_RECONSTRUCTION.md).

Sources: [`hyperrig_preset_assets.c`](../firmware/src/hyperrig_preset_assets.c) and
[`hyperrig_preset_assets.h`](../firmware/include/hyperrig/hyperrig_preset_assets.h).
The original Required Notice and license are retained. Original images, earlier
reconstructed sources and their verification reports remain unchanged.

## Pinned functions

The G v2 M5.71 reference application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x02006f3a..0x02006f70` | Probe J then I header | `d6492c5413bf4986c837143decd69505f8951c2ab661c3c02531d183d1c366db` |
| `0x02006f70..0x02006f8e` | Extended-identity predicate | `0464db3f23e3c7c0d277e734a7710dbcd0901589f8101c8e8859eb776a6760e6` |
| `0x02006f8e..0x02006fb0` | Select identity word | `8624af33a5d9b37cf41a04c1b1c313b7962f440c6ba4c847ef5ff5d0cf925c4a` |
| `0x02006fb0..0x02007008` | Resolve capture identity/trailer | `9cf3fca5f3e3b989dd7fc604a33f96b1f1489e024f11bce38cca2abc387ce0ed` |
| `0x02007b88..0x02007b9c` | Working-preset mode bit | `5b3693bd98f15af1e8ea2e1f65e61a2e2d205ef93305bb0c02e691fd15882494` |
| `0x02007b9c..0x02007c6a` | Placement/branch metadata | `e32c076eb7bee1db0da3a386cf9589ad9dac5123672e29ceb06d5456027959f8` |
| `0x02007c6a..0x02007c94` | Asset descriptor equality | `f27d999a97c387f6c1e88e656f630952214aa103ce303e6f86f0b144e4c57454` |
| `0x02007c94..0x02007ca6` | State word 416 is nonzero | `bbe95961d53d90bf04a3eadda898e081bc522f7a5dbc055c5d8486c68053b87e` |
| `0x02007ca6..0x02007cba` | Signed clamp to 400..3000 | `29728ecaa731edc77c22670cc35a205e733dc44d375c6456cfe8979fb50b6c66` |

All nine regions and the shared header helper are byte-identical in the reviewed
MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This establishes the byte binding, not target execution.

## Headers and identities

The dual-format probe clears its uint32 format output, then reads a 40-byte
header at `(0xef000 + (slot << 13)) modulo 2^32`. The existing header helper
accepts only a successful read, matching tag and unsigned length at most the
supplied maximum. The first tag is `0x4a474b54` (`TKGJ`). Acceptance sets format
to one and returns one. Any rejection, including a read failure, causes another
read at the same address using `0x49474b54` (`TKGI`). This second result is returned.

The format output is cleared only at entry. Synchronous reader changes to that
output remain on the fallback path; J acceptance overwrites them with one.
Rejected and partially completed header reads remain visible. No slot-range
guard or payload CRC validation occurs in this helper.

The identity predicate is true when the header word at offset 8 equals
`0x2144df1c` and its unsigned length at offset 4 exceeds seven. This is a format
predicate, not a checksum computation. When false, identity is the offset-8 word.
When true, identity is a little-endian uint32 from a supplied four-byte tail.

The trailer resolver starts with a zeroed local tail. Only the extended predicate
causes a read. It selects the address as follows, with uint32 wrapping throughout:

```text
if signed32(slot) >= 8:
    base = 0xcf000
    index = slot + 0x7fff8
else:
    base = 0xdf000
    index = slot
address = ((base + (index << 13)) | 0x28) + length - 4
```

For length eight, slots 0, 7, 8 and 14 read addresses `0xdf02c`, `0xed02c`,
`0xcf02c` and `0xdb02c`. Negative int32 slot bit patterns select the `0xdf000` base;
there is no additional slot validation. The original read wrapper remains an
external contract responsible for actual address acceptance.

A failed trailer read returns **-1** and leaves the caller's identity output
unchanged, even if a prefix of the private tail was written. After a successful
read, the resolver reloads both length and marker from the header before selecting
the identity. Callback changes can therefore make it choose the updated header
word instead of the tail. Success writes the selected identity and returns zero.

## Working-preset routing metadata

The layout helper receives a 1490-byte converted working preset. It clears all
16 placement bytes and 12 branch bytes before populating them, and caps the
effect count in working byte 1 at sixteen.

For working versions above three, each placement comes from byte `15 + 18*i`:
values zero through two are retained, larger values become zero. All twelve
branch bytes are copied verbatim from working offsets 1348..1359.

For versions zero through three, each of two chains is handled separately. Its
effect membership is byte `12 + 18*i`. If any effect in that chain has placement
byte one, all its effects receive placement two when their old value is one,
or placement one otherwise. A chain with no such effect keeps zero placements.
Records belonging to neither chain are left zero. Version three additionally
copies working bytes 1340/1341 to branch bytes 0/1 and bytes 1342/1343 to branch
bytes 6/7; all other branch bytes remain zero. Versions zero through two retain
twelve zero branch bytes. The working input is unchanged.

These names describe the observed layout and caller use. They do not establish
that live routing has been applied. In particular, no effect allocation, branch
creation or audio processing is executed by the layout helper.

## Reuse checks and remaining application path

The 16-byte descriptor helper returns true only when byte 0 is nonzero, words at
4/8/12 equal the three supplied words, and byte 1 equals the full uint32 fourth
argument. High argument bits are not discarded. In the application caller,
descriptors at state offsets 1780 and 1796 participate in capture/IR reuse decisions.

The mode helper returns one when the high bit of working byte 1347 is clear.
Another helper tests state word 416 for nonzero. The arithmetic helper interprets
its argument as signed int32 and clamps to 400..3000. Its caller supplies the
signed halfword at working offset 8. Physical units and deeper ownership meanings
are not assigned by these tests.

Static inspection of `0x020092fa..0x02009dd0`, SHA256
`9e48e0dcb71a39bee2c7d05a1d064859d5f419642ef58422cff306f5ad6232ee`,
connects the recovered helpers to the remaining work:

- Entry obtains the mode flag, clears both output words, and derives the local
  placement/branch arrays. Capture and IR header/identity checks feed descriptor
  comparisons before the reuse/rebuild decision.
- The capture path calls `0x020087cc`; the IR path calls `0x02008a62`. Their results
  are stored in distinct output words, as previously traced in
  [the preset-load acknowledgment analysis](MINI_PLOAD_ACK.md).
- The reuse path compares existing effect types, placement and parameters.
  `0x0202fee4` participates in parameter application; `0x02030068` and
  `0x02030110` participate in the reuse decision before possible rebuilding.
- Later code reads the derived branch bytes as signed values and calls
  `0x02030b66` for three entries per chain. Actual routing/effect changes remain
  external to this reconstruction.

These are static caller observations, not an executed application handler. The
[IR extension](IR_LOADER_RECONSTRUCTION.md) now reconstructs the IR payload loader
and ownership sequence, retaining explicit allocator and DSP service boundaries.
Capture loading and the effect-state reuse/rebuild contracts remain next. The separate
[recursive-filter reconstruction](BIQUAD_RECONSTRUCTION.md) supplies numerical
DSP dependencies without claiming this application path has been integrated.

## API and verification

The APIs use caller-owned buffers and explicit synchronous read callbacks.
The header API requires both existing storage callbacks because it reuses the
unchanged storage API; the resolver requires only the read callback. Buffer sizes,
nonoverlap, no retained pointers, no re-entry and no concurrent mutation are caller
contracts. Original predicates and statuses are preserved. New invalid-API errors
occur before calls/writes: **-1** for header, identity and pointer-based pure helpers,
and **-2** for the resolver. Identity/layout expose new status returns; incidental
original layout return-register contents are not treated as results.

The completed run passed **3,938 C-versus-instruction comparisons**:

| Operation | Comparisons |
| --- | ---: |
| Dual-format header | 555 |
| Extended predicate / identity selection | 54 / 216 |
| Trailer resolver | 251 |
| Mode bit | 256 |
| Layout conversion | 2,048 |
| Descriptor match | 280 |
| State word predicate / signed clamp | 139 / 139 |

Checks compare semantic results, all previously mapped bytes, the new placement,
branch and result buffers, and ordered read addresses/destinations/sizes with
mapped state at each call. The four-byte private trailer is normalized as a local
buffer; its failed-read contents are not persistent output. Eighteen callback
mutation cases are included in the total. Eighteen focused instruction tests and
17 invalid-API checks also passed.

All **189 new instructions** were visited, including all three bounded REP bodies
and the parallel byte-insertion packets. This run visited 205 of 1,092 combined
instructions; earlier component coverage remains in its own reports. The host
library builds with warnings as errors and UBSan. Five dependency objects compile
for pi32v2 r3; the new asset object is **1,580 bytes**. It is a relocatable object,
not firmware size or a runtime budget. No new hardware, audio or durable-write
test was performed, and these objects have not run on the pedal.

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_preset_assets.py --output build/reverse-preset-assets-new
```

Optionally pass `--mini-image` with the reviewed `hyperrig-mini-v4.app.bin` inside
the workspace. The builder refuses existing output directories and produces the
host library, five target objects, source-hashed `verification.json` and artifact
`build-manifest.json`. Generated files remain outside Git. The completed run is
`build/reverse-preset-assets-01`.
