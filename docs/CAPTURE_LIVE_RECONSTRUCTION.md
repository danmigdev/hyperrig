# Native capture loading, warm-up and processing

The native loader's context and arena now continue directly into the recovered
warm-up and block processor. The comparison runs the original entry points in
sequence using the same addresses and preserved bytes. It does not translate
the parsed model into the earlier portable engine format or invent an enclosing
audio task. This integration adds no original function to the inventory.

The new [C adapter](../firmware/src/hyperrig_capture_live.c) and
[header](../firmware/include/hyperrig/hyperrig_capture_live.h) use the unchanged
[native loader](CAPTURE_NATIVE_RECONSTRUCTION.md),
[warm-up](CAPTURE_WARMUP_RECONSTRUCTION.md) and
[processing caller](CAPTURE_PROCESSING_RECONSTRUCTION.md). Earlier source files,
images and completed reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre. The reconstructed source
retains the [UltraRig license](../third_party/ultrarig/LICENSE.md). These are
offline instruction comparisons and relocatable objects. No device, audio,
real-time performance or complete firmware image was tested.

## Integration behavior

The public runtime remains `hyperrig_capture_native_runtime`. Its 228-byte
context at `dispatch.dsp + 76` corresponds to original `0x01c2c03c`. The new
processing and warm-up APIs pass that exact context to the recovered bodies.
The parser's descriptor pointers, coefficient allocation, converted biases,
histories and position are used without relocation or reformatting.

Loading retains its original status and partial-failure behavior. The new
adapter supplies no readiness gate: a failed or partially written load does
not become safe to process merely because a process API exists. Sources and
arena must remain allocated, the processing map must resolve the same bytes as
the loading map, and the existing ownership and numerical-domain contracts
continue to apply. There is no concurrent use of the fixed scratch buffers.

Warm-up returns the original one for an eligible capture, or zero after the
actual reset fallback. Its optional three-word output is the accumulated signal
before head convolution. The following block processor evaluates complete
64-frame blocks and preserves the remainder. Unloaded processing retains the
original forward-copy bypass behavior and counter increment.

The reference maps all 29 loading regions plus three scratch gaps and two
4,096-byte sample buffers. The gaps exclude the existing statistics object at
`0x01c340cc..0x01c34114` and force word at `0x01c344a8..0x01c344ac`. Each original
address therefore has one backing location; overlapping views do not silently
duplicate state. All 34 regions are compared after each entry and at external
or numerical call boundaries.

## Small head rings found by integration

The first direct handoff exposed a domain gap in the earlier numerical adapter.
The native parser allocates a head ring of `next_power_of_two(head_frames)`,
followed by `min(ring_frames, 64)` mirrored frames. A three-frame head therefore
uses a four-frame ring plus four mirrored frames. The earlier head API accepted
only rings of at least 64 frames and rejected that valid native context.

`hyperrig_capture_live_kernel` reconstructs the original head body at
`0x01c130b4..0x01c1318e` for small as well as larger rings. The already recovered
body is counted once in the inventory. The new adapter preserves the biased
64-bit multiply-accumulate, post-accumulation sign correction, arithmetic shift,
first saturation, wrapping 64-bit bias addition and final saturation. It writes
the current frame and its native mirror, then updates the parameter cursor.
It neither expands the history allocation nor changes the parser's layout.

The raw parameter block must remain coherent with its wrapper: three channels,
64 input frames, 1..65 kernel frames, shift 1..31, ring at least the kernel,
and a ring byte count no greater than `INT32_MAX`. The map provides exactly
`ring_frames + min(ring_frames, 64)` history frames. Other numerical calls
delegate to the unchanged processing adapter.

With a null numerical callback, the live adapter executes the reconstructed
arithmetic. An observing callback can record the entry and delegate to
`hyperrig_capture_live_kernel`; delegating to the earlier processing kernel
would retain its old small-ring rejection. The corpus compares both observing
and null-callback execution.

## Verification design and limits

The instruction models execute original loading, parser/reset, numerical,
warm-up and processing bodies. Sequential entries carry complete memory rather
than reconstructing their expected state in the test. The C runs the separately
reconstructed modules and compares results, all mapped bytes, ordered external
calls, numerical-entry snapshots and physical-read request order.

Cases include every parser head size from 1 through 64; generic and specialized
layer kernels; aligned and misaligned arenas; parser configurations; complete
blocks and untouched tails; wrapped sample positions; repeated histories;
stored-slot reuse; failed parsing; real installation recovery; warm-up and
repeat warm-up; reset fallback; and the pinned 4,892-byte embedded capture.
Standalone head cases exercise non-power-of-two rings, signed shift/bias limits
and exact mirrored extents. Sanitizers use exact runtime, source, arena, history,
weight and sample allocations.

The synthetic allocator has one candidate heap region. Recovery cases keep the
previous owned source in a distinct mapped cached region. Allocating a replacement
over the still-live previous source would violate that ownership contract and
destroy the bytes needed for recovery. An early development case exposed this
invalid fixture; it was corrected by separating the allocations, without changing
the recovered loading behavior. This does not model a complete heap allocator.

New statuses `-200`, `-201` and `-202` identify invalid API arguments, missing
mapping and unsupported numerical domains. They are additional host safeguards,
not original firmware statuses. Earlier writes may survive a later guard.
Valid-domain comparisons and C-only rejection checks are reported separately.

The surrounding audio task, scheduling, physical allocation/storage, metadata
lookup and mode/priority implementations remain separate dependencies. The
test supplies those external services explicitly. Warm-up and block processing
themselves use actual recovered numerical bodies. Instruction coverage and
unvisited addresses remain in the report; sequential execution does not establish
all firmware paths or a hardware/audio result.

## Reproduction and provenance

The pinned original application image has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The loader checks that image and its decoded extraction. MINI binding requires
the reviewed v4 image with SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The local check covers all loaded instruction byte windows, the joined function
ranges, both dispatch tables, the gain and legacy-conversion tables, the reset
configuration word and embedded capture. It does not infer hardware equivalence
from byte identity.

The verifier builds its source manifest from imported repository modules,
recursive C includes, explicit builder/test inputs and the pinned ISA data.
It needs no previous ignored comparison report. The original images, decoded
application and embedded capture remain required local inputs under the
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).

```powershell
python -B tools/build_capture_live.py --output build/reverse-capture-live-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

Use a new ignored output directory. The builder compiles a warning-clean UBSan
host library, freestanding pi32v2 r3 objects, focused tests and an ASan/UBSan
harness. It creates no flashable image and opens no device.

## Recorded validation

Final evidence is `build/reverse-capture-live-02`. The earlier development
directories and incomplete `-01` run are preserved outside the final evidence set.

| Evidence | Result |
| --- | ---: |
| C versus original-instruction comparisons | 695 |
| Load / install / slot / cleanup comparisons | 32 / 71 / 41 / 1 |
| Block-processing / warm-up / direct head comparisons | 251 / 37 / 262 |
| Actual numerical calls | 1,996 |
| Native parser entries / resets | 262 / 289 |
| Reset word stores | 417,096 |
| Explicit carried steps / null-callback comparisons | 155 / 9 |
| Decoded instruction steps | 28,855,397 |
| Joined instructions visited / decoded | 3,300 / 3,670 |
| All loaded instructions visited / decoded | 3,873 / 5,298 |
| Focused tests | 14 |
| Invalid-API / missing-map / numerical-domain checks | 6 / 5 / 11 |
| Exact-buffer ASan/UBSan cases | 2,376 |
| Sanitizer cases loading and processing the embedded capture | 54 |
| Audited source hashes / generated artifact hashes | 76 / 22 |

All 370 unvisited joined addresses are listed in the report. Earlier standalone
module corpora retain their own broader instruction coverage; this integration
does not add those counters together or mark unvisited instructions as executed.
The local MINI check binds all 5,298 loaded instruction windows and the stated
immutable data inputs.

All eighteen source objects compile for pi32v2 r3. The seventeen reused objects
are byte-identical to their earlier builds. The new live adapter is a 2,192-byte
relocatable object, not a linked image or a total memory/latency measurement.

| Output | SHA-256 |
| --- | --- |
| C source | `01fe2b22af97f20c6e5c3a4e3a9d6859c80372bca5af8c669ad4e473537f34da` |
| Verification report | `959afdb82601614bfaa53bf31b64ce6c3c50592130ba4a0ec332a65be722576e` |
| Build manifest | `329774ded7e5ce67c5e16d696280d1a261d6409c97fa6ccb77ee587e09b567ed` |
| New target object | `e100ba9b679c23e27b22619cb25e1ebcf1acfbc1193a64801e5021f8c8d8e464` |
