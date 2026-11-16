# Reconstructed capture memory reset

The later [native loading integration](CAPTURE_NATIVE_RECONSTRUCTION.md) joins
this reset with the complete parser through installation and recovery. This page
retains the earlier reset milestone's independent scope and evidence.

The complete memory-reset routine now has compilable C and original-instruction
comparisons. Context loading, the outer load wrapper, recovery, installation and
slot loading can execute these reset loops through a new adapter. The earlier
[capture dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md), container, slot loader,
models and completed reports remain unchanged. The raw parser remains an
explicit callback in this milestone; this is not complete capture execution.

Sources: [`hyperrig_capture_reset.c`](../firmware/src/hyperrig_capture_reset.c)
and [`hyperrig_capture_reset.h`](../firmware/include/hyperrig/hyperrig_capture_reset.h).
The Required Notice and third-party license are preserved. No device was opened,
no physical memory was accessed and no firmware or audio test was performed.

## Original region and mapping

The recovered function is `0x01c12878..0x01c1296c`, end exclusive: 244 original
bytes and 84 decoded instructions. It contains no calls to other functions.
Its SHA256 is
`cb4c31b1a65dae12f4905c22601b90199421463955196d9577b2f7d9e80f3a7c`.

The original G v2 M5.71 image SHA256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
RAM address `a` maps to decoded application offset
`0x02056780 - 0x02000120 + a - 0x01c00000`. The model verifies the pinned image
and decoded extraction through its unchanged dependencies before execution.
The complete reset region is byte-identical in the reviewed MINI v4 image,
SHA256 `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

The direct API receives 228 initialized context bytes and a mapping callback.
Original addresses are uint32 tokens, never host function pointers. The context
fields used by this function are:

| Context offset | Original use |
| --- | --- |
| 2 | Unsigned channel-count byte |
| 8 | Unsigned 16-bit layer count |
| 80 | Main ring pointer |
| 84 | Main ring span word |
| 88 | Cursor/state word cleared at the end |
| 92 | Layer descriptor table pointer; descriptors have an 80-byte stride |
| 140 | Optional auxiliary ring-pointer table |
| 144 | Auxiliary per-layer size table |
| 148 | Final auxiliary ring pointer |
| 152 | Final auxiliary size word |

These names describe observed accesses; they do not establish the meanings of
all context fields or the surrounding processing topology.

## Clearing order and wrapping arithmetic

The function retains the initial layer count and channel byte. For each layer,
it reads the descriptor size at offset 76 and, when the computed word count is
nonzero, the ring pointer at offset 68. It clears successive four-byte words in
that ring. The initial and repeated count is:

```text
uint32(uint32(descriptor_size + 64) * channels)
```

After every store, it rereads the descriptor size before deciding whether to
continue. Zero channels therefore prevent ring writes but do not skip descriptor
size reads when layers exist. Zero layers skip descriptor access entirely.

The main ring follows. With `n = uint32(context_span + 1)`, its word count is:

```text
uint32(uint32(n + min(n, 64)) * channels)
```

The main span is reread after each store. The padding reaches 64 when `n` reaches
64; additions and multiplication retain uint32 wrapping. Tests include nonzero
factors whose product wraps to zero or a small mapped span.

Auxiliary work runs only when channels equal three and the table at context
offset 140 is nonzero. Each layer obtains its size from the word table at offset
144 and its ring pointer from the table at offset 140. The word count is
`uint32(uint32(size * 3) + 192)`. A zero count skips the ring-pointer read.
The size word is reread after each store.

The final auxiliary ring uses context offsets 148 and 152 and the same count
formula. It can run even when layer count is zero. Only after all applicable
loops finish does the function clear context bytes 88 through 91.

Every word address advances modulo 2^32. A tested sequence starts at
`0xfffffffc`, continues at zero and then advances through the low address range.
The test mapping supplies ordinary host storage for those tokens. This does not
claim that a physical peripheral or memory bus supports those addresses.

Mapped buffers can overlap each other. In particular, a ring can overwrite its
own size word or a size table used later. Three comparisons exercise such
aliases, including the resulting change in loop length. A pointer retained in
an original register remains retained in C. The context and IO structures must
be disjoint from mapped storage, and mapping must be pure and consistent for
the operation. Concurrency and callback mutation during mapping are unsupported.

## Integration and new mapping guards

`hyperrig_capture_reset` returns zero after completing the original void body.
New status -200 rejects invalid API pointers before effects. New status -201
stops before the first unmapped four-byte read or write; already completed
stores remain, and the final context word is not cleared on that exit. These
guards are new API behavior outside the fully mapped comparison domain.

The load/context/cleanup adapters intercept the old reset service and execute
this C body. In the original-instruction model, the same call enters the entire
decoded function. Reset is no longer a scripted service on these paths. A
successful context load executes one reset; the successful outer load executes
two, with its original statistics and dispatch initialization between them.
Ordered word-address and pre-write-value comparisons verify the second pass,
including its repeated stores into already cleared memory.

The new installation adapter connects the unchanged container and slot loader
to reconstructed dispatch operations with reset interception. A reset mapping
failure becomes a load error before the container publishes source ownership
or a new slot. The container performs its existing free and recovery sequence.
If recovery itself encounters a reset mapping failure, the new guard clears
the ready byte at state offset 500 and reports the error. This readiness change
is explicitly guard behavior, not an original instruction-path claim.

The original load statistics can retain status zero when a new direct-wrapper
guard returns -201: the unchanged dispatch treats reset as void. Partial memory
effects are not rolled back. If recovery succeeds after a capability-mapping
failure, the previous capture can still become ready; the new capture and slot
remain unpublished. Capability mapping retains the established internal -3
failure path and public -201 result.

Parser, allocation, metadata lookup, physical reads, compaction, scheduling,
notification, mode and priority bodies remain external. The adapters themselves
are new orchestration and add no inferred original function entries. Only the
complete reset routine is newly reconstructed here.

## Verification and artifacts

The completed run is `build/reverse-capture-reset-03`:

| Entry | C/original comparisons |
| --- | ---: |
| Direct reset | 212 |
| Context load | 14 |
| Outer load | 14 |
| Recovery cleanup | 1 |
| Container installation | 9 |
| Slot loading | 3 |
| **Total** | **253** |

Those cases execute **267 original reset entries** and compare **62,562 ordered
zero-word writes**, including their previous contents. Results compare all 29
mapped regions, preserved neighbors, service/parser arguments and memory at
each external boundary. The reference executes all **84 new instructions** and
850 of 1,966 combined decoded instructions; inherited modules retain their own
broader verification reports.

Seventeen focused instruction tests, 18 invalid-API checks, 16 C-only mapping
guard checks and **180 ASan/UBSan cases with exact-sized buffers** passed. The
instruction verifier maps up to eight layers, 65,536 arena bytes and 4,096 bytes
across the uint32 address boundary. These are test bounds, not firmware limits.
It does not exhaust every large or self-modifying mapped layout. The native
interpreter has an explicit instruction budget.

The host library uses warnings as errors and UBSan. All nine source/dependency
objects compile for pi32v2 r3. The new relocatable object is **3,380 bytes**,
SHA256 `303026bf0b31035ec50d045c67933bf4d886e0f6b011e170cac5ce5ab113dc86`.
This is not a linked firmware size, RAM budget or measured latency.

The new C source SHA256 is
`1a5047b4dfc59054788c4fa84eca075d40297cd9505960e17a261522b5bafb0d`;
the comparison report SHA256 is
`d72bd2c9a1f970e3a5347b2ec7d89db36175efd91ed747961350f653d3925b7b`.
The report binds 49 source files, and the manifest binds 12 generated artifacts.
Earlier development runs remain preserved separately.

Use the [native prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_reset.py --output build/reverse-capture-reset-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder requires a new ignored directory under `build/`.
Libraries, target objects, sanitizer executables and reports stay outside Git.
No flashable image is produced or installed. Completing the native parser and
connecting real parsing to these reset loops remains separate work.
