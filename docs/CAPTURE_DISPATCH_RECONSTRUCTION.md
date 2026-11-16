# Reconstructed capture preparation and DSP dispatch

Capture installation now executes preparation, the size/probe wrappers, DSP
context loading, capability checks and recovery in both portable C and the
original-instruction model. It connects the unchanged
[container installer and record reader](CAPTURE_CONTAINER_RECONSTRUCTION.md)
to these newly reconstructed bodies. The complete raw parser and memory reset
routine remain explicit services; this is not complete native capture execution.

Sources: [`hyperrig_capture_dispatch.c`](../firmware/src/hyperrig_capture_dispatch.c)
and [`hyperrig_capture_dispatch.h`](../firmware/include/hyperrig/hyperrig_capture_dispatch.h).
Required notices and the third-party license remain intact. Earlier components,
completed evidence and tested firmware images are preserved.

## Original regions and image binding

The reference G v2 M5.71 image SHA256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
Flash address `a` maps to decoded offset `a - 0x02000120`; RAM address `a`
maps to `0x02056780 - 0x02000120 + a - 0x01c00000`. The inherited model checks
the reference image and decoded extraction before executing instructions.

| CPU range, end exclusive | Reconstructed behavior | Region SHA256 |
| --- | --- | --- |
| `0x020025ca..0x02002634` | Arena preparation and diagnostics | `212e5bc4ab7ca127549b3da9b5636acecd9fff8dee35f4fd3eecd0c7bc174a1d` |
| `0x02002634..0x0200268e` | Reload the previous capture during cleanup | `955e91c53a9c23a5b32b16e4eea86a1d6e75ad5f8f6acb3f554e9bd559c24c7e` |
| `0x01c04a7a..0x01c04a8e` | Probe wrapper | `bc1781c802e08534cf7dceff9b07b411719dcf2356ae5a0b27c68294f66155bb` |
| `0x01c12850..0x01c12878` | Query parser allocation size | `805b6c55d4faef59646612b15b665a32ff0b79ab38e63bc37deb7f3c8eb505af` |
| `0x01c04a8e..0x01c04b34` | Load context and publish statistics | `0640b7c49889f8bfba471a20171eb97d0f8683183a1e96a10fbd400fd8f25bc6` |
| `0x01c1296c..0x01c129ce` | Align arena, parse, check capacity and initialize dispatch | `99a10c7e122bb54631c5df4430e423d101a99b503e7d4c9cc7b4ce06a0d44a6a` |
| `0x01c04bac..0x01c04c42` | Export metadata and check layer capabilities | `571e1c70c99f26c6b97e111cffc173dffca457eb87a82d0771d5a8fbf7b2b98d` |
| `0x01c129ce..0x01c129dc` | Select dot callback or default | `33fab5d7d1798e530fc2888f860d699ef65dd2642f5def685c900fa53954f2c9` |
| `0x01c13082..0x01c13084` | RTS only | `8509b81230019d2ad970d970f791dfbdc8caf54f5c594fcd327cef9feed206c1` |
| `0x01c13084..0x01c13086` | RTS only | `8509b81230019d2ad970d970f791dfbdc8caf54f5c594fcd327cef9feed206c1` |
| `0x01c13086..0x01c13088` | RTS only | `8509b81230019d2ad970d970f791dfbdc8caf54f5c594fcd327cef9feed206c1` |
| `0x01c1308c..0x01c1308e` | RTS only | `8509b81230019d2ad970d970f791dfbdc8caf54f5c594fcd327cef9feed206c1` |

These are eight substantive functions and four exact return-only helpers. The
reference model executes all four helpers; omitting their effects in C is valid
because they have none. They do not represent four newly implemented effects.
All twelve ranges match the reviewed MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

## Allocation and size behavior

Preparation rejects nonzero state word 416 with -110. A nonzero arena token at
state 436 is reused when its capacity at state 440 meets the unsigned request.
Otherwise it clears state byte 500, frees the old token, and requests
`uint32(requested + 256)` bytes. It stores the returned token and capacity,
records success at state 4128, or records -100 at state 4140 on failure. The
allocator remains synthetic; wrapping requests are preserved, not allocated
by the host.

The size helper calls original parser `0x02031c64` with a private 228-byte
context and ledger `{0, 0, 0}`. Parser failure returns zero; success returns
`uint32(ledger.used + 8)`. The probe sets word `0x01c344a8` to one and adds 16
unconditionally. A failed parser therefore normally produces probe value 16,
not zero. A used size of `0xffffffe8` wraps the successful probe to zero.

The parser callback may write the private query context but may not read its
uninitialized contents or retain its address. That scratch context is not
part of the public memory comparison. The full parser body is neither emulated
nor replaced by the existing portable A2 parser in this milestone.

## Context setup, statistics and capability checks

Context load rejects a zero arena token with -5, rounds a nonzero token up to
eight-byte alignment and deducts skipped bytes from capacity. It calls the
parser with `{aligned_arena, 0, available_bytes}` and the fixed context at
`0x01c2c03c`. Parser failure passes through. A reported used count exceeding
capacity returns -5 while preserving any parser writes already made.

Success installs default dot callback `0x01c12608` at context offset 108, clears
offsets 112 and 116 and byte 136, then calls memory reset `0x01c12878`. The reset
body remains external. Parallel packets matter: the store paired with moving
the context pointer writes offset 116, not offset 8. Layer count at offset 8
must survive this initialization.

The outer load wrapper records status at `0x01c340cc`. On success it copies
layer count, channels, a context word, a flag and two sign-extended bytes into
statistics; it clears selected counters, reinstalls the default dot callback,
executes the four return-only helpers and calls reset again. There are two
reset calls on this successful path. Tests compare state at both boundaries,
including changes made by the first reset that later appear in statistics.

Capability query writes 17 metadata bytes plus layer/channel counts before
deciding its result. It requires channels equal to 3, nonzero DSP byte 240,
and context byte 1 equal to 32. Zero layers then succeeds without dereferencing
the layer pointer. Otherwise it walks descriptors with an 80-byte stride and
requires each descriptor's first byte to be below 16. The verifier supplies
up to 64 descriptors; this is its mapped test domain, not an inferred firmware
limit on model size.

Cleanup clears state byte 500 and probes the previous source before checking
whether the global source length is zero. It rereads that length after the
probe and rereads both source fields after preparation, so synchronous callback
changes remain visible. It stores the probe result, runs the reconstructed load
wrapper, and sets byte 500 only on success. It does not query capabilities.

## Interfaces and explicit boundaries

The portable runtime extends the existing container state with allocation
diagnostics, DSP context bytes, statistics and the force word. Original addresses
are opaque integer tokens; no original hardware address is called as a host
function pointer. Public outputs, runtime, IO and mapped storage must be disjoint.
Mapping must be pure. Callbacks may change public memory synchronously within
the mapped domain, without re-entry, concurrency or retained private pointers.

New status -200 rejects invalid API arguments. New status -201 rejects an
unmapped capability descriptor. In integrated install/slot calls, that guard
returns capability failure to the unchanged container, which performs its
normal free, cleanup and state restoration. Internal notifications retain its
original -3 capability status; the outer portable API reports -201. Tests check
that the failed capture and slot are not published. This guard-only behavior
is not attributed to original instructions outside the mapped domain.

The complete parser, memory reset, allocator, compaction, metadata lookup,
scheduler, physical reads, mode and priority implementations remain external.
The whole native parser and reset are the next capture dependencies to recover.
Integration with the independently reconstructed metadata journal is separate
work. No sample processing, physical storage operation or device access occurs
in this dispatch comparison.

## Verification and reproduction

The completed final run is `build/reverse-capture-dispatch-03`. It passed
**1,847 comparisons**, including 45 integrated installer/slot cases:

| Entry point | Comparisons |
| --- | ---: |
| Prepare | 506 |
| Cleanup | 18 |
| Size query | 30 |
| Probe | 30 |
| Load wrapper | 404 |
| Context load | 306 |
| Dot selection | 4 |
| Capabilities | 504 |
| Container installation | 40 |
| Slot loading | 5 |

All **254 new instructions** were visited; the integrated run visited 798 of
1,882 decoded instructions. Earlier modules retain their own wider verification
reports. Comparisons check semantic results, all 27 mapped memory regions,
ordered service/parser arguments and state at every boundary, and synthetic
read requests. Private stack context addresses are normalized; a void dot
selection result is not treated as a semantic return value.

Nineteen focused instruction tests, 47 invalid-API checks and three new mapping
guard checks passed. The host shared library uses warnings as errors and UBSan;
all eight pi32v2 r3 objects compiled. The new relocatable object is 3,120 bytes,
SHA256 `ea81740c23a9ef9de2a28c5f38538ce99e0aeebf57771d78d31160832369a802`.
This is not a linked firmware size or latency measurement.

The C source SHA256 is
`01780028f3722182e29ddc070e77de75d377b28ef8f914a79347f04d01b8a8a2`;
the final verification report SHA256 is
`c191eaffa8a0f80a9bbb116039321bf2e36311d1aad1cac6f318b241baf62473`.
The report binds 42 source files and the manifest binds generated artifacts.
The earlier `-01` and `-02` reports are retained. The final run includes the
integrated mapping-guard checks, interface clarifications and source whitespace
cleanup; the instruction behavior is unchanged from `-02`.

Use the [native prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_dispatch.py --output build/reverse-capture-dispatch-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder requires a new ignored directory under `build/`.
Libraries, objects and reports remain outside Git. No hardware/audio test was
performed, and no firmware image was produced, changed or installed.

## Subsequent parser and reset evidence

The complete [native parser](CAPTURE_PARSER_RECONSTRUCTION.md) now has a separate
comparison against its original context, allocation and error behavior. The
[memory-reset module](CAPTURE_RESET_RECONSTRUCTION.md) executes the original
clearing loops through new load, cleanup, container and slot adapters. These
later modules preserve this milestone's sources and reports. Joining both bodies
in one complete native capture-loading comparison remains the next integration.
