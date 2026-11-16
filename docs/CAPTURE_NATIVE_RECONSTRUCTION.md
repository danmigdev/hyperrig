# Integrated native capture loading

Capture installation now executes the complete original parser and memory-reset
bodies through the recovered size, load, cleanup, container and stored-slot
callers. The reference model follows their actual original instructions; parser
results and reset writes are no longer scripted on these paths. This joins
existing reconstructions and adds no newly discovered original function.

The C adapter is [`hyperrig_capture_native.c`](../firmware/src/hyperrig_capture_native.c),
with its [public header](../firmware/include/hyperrig/hyperrig_capture_native.h).
Earlier [dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md),
[parser](CAPTURE_PARSER_RECONSTRUCTION.md), [reset](CAPTURE_RESET_RECONSTRUCTION.md),
[container](CAPTURE_CONTAINER_RECONSTRUCTION.md) and
[slot loader](CAPTURE_LOADER_RECONSTRUCTION.md) sources and reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre. The reconstruction retains
the [UltraRig license](../third_party/ultrarig/LICENSE.md). It is reconstructed
source and relocatable code, not a linked firmware image. No device or audio
test was performed.

## Original execution and state

The reference is the pinned Alpha 11/M5.71 G v2 image, SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The inherited model checks both that image and its decoded application before
execution. The 15 joined dispatch/parser/reset regions are byte-identical in
reviewed MINI v4, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The same check binds the embedded capture and reset-copy configuration word 12.

`hyperrig_capture_native_runtime` contains the unchanged dispatch runtime and
four bytes corresponding to `0x01c1fa18`. Its live parser context remains at
`dispatch.dsp+76`, using the original 228-byte layout and 80-byte descriptors.
The configuration is read afresh for every parse. Twelve is pinned reset-copy
evidence, not a claim that every runtime caller leaves it unchanged.

The public IO uses the container service interface, without a parser callback.
The adapter supplies the recovered parser internally and uses the reset adapter
to execute clearing loops. It retains uint32 address tokens and the original
allocation/status arithmetic. Mapping must be pure and consistent; source,
arena, runtime, IO and public output objects must be disjoint. The source and
configuration remain stable during each parse. Platform callbacks may change
public state between calls, without re-entry, retained private pointers,
concurrent mutation or IO mutation.

The original size wrapper uses private context scratch and a zero ledger. Only
its required-size result escapes. A live load uses the persistent context and
retains the parser's partial writes on failure. The new adapter leaves earlier
function interfaces intact and does not introduce an alternative context format.

## Recovered loading behavior

| Operation | Executed behavior |
| --- | --- |
| Size | Complete parser query, followed by eight bytes of wrapper allowance |
| Probe | Force-word update, size query and another sixteen-byte allowance |
| Context load | Arena alignment, complete parse, capacity check, dot callback setup and one real reset |
| Outer load | Context load, native statistics/dispatch initialization and a second real reset |
| Cleanup | Query and reload of the previous source, arena preparation and readiness restoration on success |
| Container installation | Ownership/preparation sequence, query, load, capabilities and publication or recovery |
| Stored-slot load | Header/identity/signature checks, real record reader and CRC, metadata application, container path and final slot state |

A failed parser query becomes zero in the size wrapper, but the probe still
adds sixteen. A nonzero probe result therefore does not prove valid capture
data. The complete installer can continue into load, receive the real parser
error, free the candidate allocation and invoke recovery. These paths are
compared with valid previous capture data as well as failed recovery.

The parser can also return zero after recording more required bytes than the
supplied capacity. Context load checks that condition before installing its dot
callback or resetting histories and returns original status `-5`. Descriptor
and coefficient writes already performed by the parser survive that failure.

Successful outer loading resets twice. The first reset follows parser/context
initialization; statistics and dispatch setup occur before the second. Both
passes execute their real loops, including writes to already cleared history.
The corpus compares resulting history buffers, persistent context and all
public snapshots at external service boundaries.

Capability rejection is distinct from parse failure. The container requires
the original optimized three-channel int32 path and supported kernel widths.
Other successfully parsed shapes can fail installation, followed by a reload
of the previous capture. A restored ready byte does not mean that the rejected
candidate was installed; source ownership and selected-slot publication are
checked separately.

The stored reader has additional native fallback behavior. An identity-trailer
read failure can leave identity unresolved until the complete payload reload
resolves it. A signature read error does not by itself reject the stored slot.
The comparisons include both continuations, failed initial/reloaded headers,
partial payload reads, CRC failures and carried-state reuse.

Platform-boundary mutation is also significant. One case changes the parser
configuration after its query but before loading. The new history requirement
exceeds the queried load capacity, causing `-5`; cleanup then queries and loads
the previous source with the current configuration. This preserves the original
sequence instead of treating the earlier query as a permanent guarantee.

## New API guards and remaining services

New status `-200` rejects invalid public API arguments before effects. New
status `-201` propagates source, parser-arena, reset and capability mapping
failures. These guards are additional host API behavior outside the original
fully mapped comparison domain. Earlier writes and the existing recovery path
remain observable; they are not rolled back automatically.

The parser's minimum-length branch reads no source bytes. The adapter therefore
does not require a source mapping for lengths below 44, including a zero token.
For a mapping failure on a longer input, size/probe still produce their original
wrapper outputs zero/sixteen while the new public API returns `-201`. Candidate
ownership and slot publication remain unchanged on the tested installation guards.
Recovery can itself fail or restore the previous capture.

Allocation/free, metadata lookup, physical reads, compaction, scheduling,
notification, mode and priority bodies remain explicit service boundaries.
The real record reader and CRC execute internally; the underlying device read
does not. The independent journal and native processing reconstructions are
not silently substituted for these services in this milestone. There is no
physical persistence, power-loss, timing or audio claim.

## Verification and provenance

Final output is `build/reverse-capture-native-02`. Its **273 comparisons** execute
**460 parser entries**, **354 resets**, **684,784 reset word writes** and
20,307,105 decoded instruction steps. Cases cover format and CRC failures,
truncation, aligned/misaligned and insufficient arenas, accepted/rejected shapes,
allocation failure, busy-state handling, mode restoration, callback mutation,
stored reads, carried state and the pinned 4,892-byte embedded capture.

Results compare the return values, all 29 mapped regions including untouched
arena bytes, ordered service arguments and snapshots, and physical-read request
order. Each native parser/reset body executes in the same instruction machine
as its caller. The C model invokes the corresponding recovered source modules.

This integration corpus visits **1,410 of 1,551 joined instructions** and
**2,042 of 3,179 loaded instructions**. All 141 unvisited joined addresses are
listed explicitly. The loaded model includes additional inherited code not
reached by this corpus. Earlier standalone parser/reset/dispatch reports retain
their broader module-specific cases; these numbers are not added together or
presented as complete firmware coverage.

Fifteen focused instruction tests, **21 invalid-API checks**, **11 mapping-guard
cases** and **518 exact-runtime/source/arena ASan/UBSan cases** passed. Host
compilation uses warnings as errors and UBSan. Eleven objects compile for pi32v2
r3; all ten dependency objects are byte-identical to their earlier builds.
The new adapter object is **2,652 bytes**, SHA256
`c676e637fa7788333fc0ab123dd1f9e02126406aec7195d7d7fb07a0448c6ea1`.
This size is a relocatable object size, not total firmware size or memory use.

The verification report SHA256 is
`0d98fd98f1285e6dc9aeefd7799193d8f0ba596652e60fc1fcdc6b238c78304b`.
All **63 source hashes** and **15 generated artifact hashes** matched after
completion. The earlier development run and incomplete `-01` build are preserved
outside the selected final evidence set.

The model provides 131,072 arena bytes and 8,192 bytes for each source/storage
buffer. Mapping beyond these ranges is outside this corpus. Successful host
comparison and target compilation do not establish target execution.

With the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

The verifier also reads the source-name lists from the preserved
`build/reverse-capture-reset-03/verification.json` and
`build/reverse-capture-parser-03/verification.json`. Those earlier report inputs
must exist. A rebuild from only a fresh checkout is not established by this run;
removing that verification dependency is a separate build-workflow task.

```powershell
python -B tools/build_capture_native.py --output build/reverse-capture-native-new
```

Optionally pass `--mini-image` with the reviewed v4 application inside the
workspace. Output must be new and under ignored `build/`; originals and earlier
results are preserved. The builder creates no flashable image and opens no device.

The next integration is to carry the context and histories produced here through
the [native processing caller](CAPTURE_PROCESSING_RECONSTRUCTION.md), including
its fixed scratch buffers, warm-up and surrounding audio scheduling. The
remaining application/routing and physical services stay on the full
[reverse-engineering roadmap](REVERSE_ROADMAP.md).
