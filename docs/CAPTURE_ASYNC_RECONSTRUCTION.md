# Asynchronous capture reconstruction

HyperRig reconstructs the complete original asynchronous capture wrapper,
its worker, the accelerator submission helper and one exact return-only
command helper. The wrapper and worker share the original capture context,
layer histories, alternating work banks and timing counters. Previously
reconstructed layer, rechannel, head and synchronous fallback bodies execute
on that shared storage.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
The original evidence and this reconstruction retain the
[PolyForm Noncommercial 1.0.0 license](../third_party/ultrarig/LICENSE.md).
This is reconstructed C, not the original source.

## Scope and native entries

| Entry | Original interval, end excluded | Bytes | Instructions |
| --- | --- | ---: | ---: |
| Asynchronous 128-sample wrapper | `0x01c04cda..0x01c05118` | 1,086 | 327 |
| Capture worker | `0x01c04588..0x01c04774` | 492 | 163 |
| Accelerator descriptor submission | `0x01c12556..0x01c12608` | 178 | 59 |
| Alternate command no-op | `0x01c13080..0x01c13082` | 2 | 1 |
| Total new coverage | | 1,758 | 550 |

The accelerator wait at `0x01c1245c..0x01c124a8` was already recovered in
the IR runtime. This module provides a borrowed-memory adapter for that body;
it is not counted as a new function. Four other return-only setters,
the signed halfword dot product, capture numerical processing and the complete
audio task also remain inherited functions.

## Shared state and scheduling

The API is in
[`hyperrig_capture_async.h`](../firmware/include/hyperrig/hyperrig_capture_async.h),
with C in
[`hyperrig_capture_async.c`](../firmware/src/hyperrig_capture_async.c).

| Original address | Role |
| --- | --- |
| `0x01c2bff0` | Worker command, handshake, publication and capture state |
| `0x01c2c03c` | The same native 228-byte capture context used by loading and processing |
| `0x01c2b4e0` | Two 1,284-byte work banks: dry input, three-channel sum, head output, saved position |
| `0x01c2a8e0` | Two 1,524-byte histories, each containing 127 three-channel frames |
| `0x01c2bee8` | Pending accelerator output, 64 signed words |
| `0x01c2c120` | Optional software head comparison, 64 signed words |
| `0x01c339e0` | Eight-word accelerator descriptor |
| `0x01c34494..0x01c344a0` | Shared accelerator start/timeout counters and busy word |
| `0x01c340cc` and nearby counters | Capture, worker and elapsed-time statistics |

The wrapper consumes two 64-sample halves. It performs rechanneling and the
first configured layers in the active bank, waits for the previous command,
reads the previous bank's output, then publishes command `0xfc` with the bank
selector. The worker finishes the remaining layers. In software-head mode it
executes the recovered head kernel. In accelerator mode it assembles the
three-channel history; the wrapper submits that history on the next half.
The wrapper preserves cold-start silence and the original buffered ordering.
It is not an alias for the synchronous processor at `0x01c12d34`.

The worker runner retains its idle counter, control token and observation
phase between calls. Its public observations are:

| New result | Original location or event |
| ---: | --- |
| 0 | Iteration budget reached at poll `0x01c04666` |
| 1 | Original worker returned after its control word became zero |
| 2 | Handshake-read budget reached at `0x01c04688` |

Results 0 and 2 are new observation points, not native returns or RTOS waits.
The handshake is unbounded in the original. Command `0xfb` enters that
handshake, command `0xff` acknowledges readiness, and other command bytes
execute the exact no-op before updating the command counter. The worker's
generic job sequence, cancellation, completion and timing behavior are also
reconstructed.

The idle callback is zero or the observed watchdog target `0x01c02dbc`.
Its writer at `0x02005268..0x02005276` is bound to both pinned images.
The generic job callback uses the same target in the reviewed domain, with
its original one-word argument. The watchdog body remains an external
service. This does not establish every original writer or indirect target.

## Numerical and platform boundaries

The platform interface exposes timer and accelerator register reads/writes,
volatile command/handshake/control reads, synchronization, and interrupt
disable/enable instructions. A test scheduler can run the actual worker at
these boundaries on the same mapped bytes. It preserves separate CPU stack
and register state for the wrapper and worker. This controlled interleaving
does not implement hardware interrupts, memory ordering or a production
scheduler.

Accelerator completion is an explicit platform boundary. The numerical test
fixture runs the already recovered signed-halfword dot-product body in C and
the original instruction model, using the submitted buffers. The fixture's
interpretation of the descriptor is not a hardware validation. Descriptor
packing, command publication, polling, acknowledgement, timeout counters and
subsequent output/bias handling are compared against their actual original
instructions. No scripted replacement is used for the recovered layer,
head, rechannel, dot or fallback arithmetic.

The wrapper preserves signed 32-bit saturation after wrapping 64-bit bias
addition. Its accelerator comparison path retains its separate diagnostic
counters. A worker timeout falls back to the actual synchronous processor;
it does not erase the rechannel/layer work already performed before timeout.
Elapsed and maximum-time counters remain native integer values. Physical
sample rates, latency and audio quality are not inferred from them.

`hyperrig_capture_async_audio_resume` joins the unchanged audio-task runner
by replacing its asynchronous capture and accelerator-wait boundaries.
The other sample services and OS/platform boundaries remain those documented
in [the audio-task reconstruction](AUDIO_TASK_RECONSTRUCTION.md).

## Supported mapping domain

Addresses are original 32-bit tokens. Maps are pure, stable and consistent,
and preserve the original address relationships,
with naturally aligned, compatible little-endian storage. The adapter checks
host alignment before delegating to numerical functions. Worker runner, IO
and output-argument objects stay stable and disjoint from mapped storage
throughout platform and service callbacks. Numerical
contexts, coefficients, scratch and histories retain the disjointness and
bounded channel/tap/shift contracts of
[capture processing](CAPTURE_PROCESSING_RECONSTRUCTION.md) and
[live capture](CAPTURE_LIVE_RECONSTRUCTION.md).

The active work-bank index is zero or one. Accelerator history paths support
one through 64 head taps; software heads also use the small native rings
supported by the live adapter. Platform callbacks may synchronously mutate
state at exposed boundaries, but must preserve consistent mappings and valid
numerical objects. A callback must prevent recursive scheduling of the same
worker. New statuses `-200`, `-201` and `-202` identify invalid API, missing
mapping and unsupported domains. They may follow partial writes and are not
resumable native states.

## Evidence and reproduction

[`capture_async_machine.py`](../tools/capture_async_machine.py) decodes every
new body and binds inherited instructions. The comparison preserves packet
read-before-write semantics, processor carry/overflow flags, full mapped
memory and carried state. Ordered platform events include exact volatile
poll counts and results; other platform boundaries and external service
calls additionally include a SHA-256 snapshot of every mapped byte.

The full timeout corpus executes all 4,000,001 original busy reads. Four
frequently executed poll instructions have an exact decoded-text dispatch
to avoid repeated regular-expression searches. Every instruction still
executes and counts individually; focused tests compare this dispatch with
the general instruction handlers. No timeout counter or branch is shortened.

The pinned original application SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The reviewed MINI v4 image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Every loaded instruction window and inherited static table used by this
corpus is checked against both images. Source manifests include imported
repository Python modules, dynamically loaded ISA semantics, the instruction
table and transitive local C headers. Earlier sources,
images and completed reports remain unchanged.

Reproduce into a fresh ignored directory:

```text
python tools/build_capture_async.py --output build/reverse-capture-async-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

Outputs are offline research artifacts. The build does not access a device,
flash firmware or change a release.

The final run is preserved at `build/reverse-capture-async-03`:

| Check | Result |
| --- | ---: |
| C/original comparisons | 137 passed |
| New instruction coverage | 550 / 550 |
| All loaded instruction coverage | 2,488 / 6,241 |
| Original instruction steps | 25,519,279 |
| Actual recovered numerical kernel entries | 609 |
| Recovered dot completions in the software accelerator fixture | 68 |
| Compared platform events | 4,605,157 |
| Focused unit tests | 15 passed |
| ASan/UBSan cases | 289 passed |
| C-only API, mapping and domain checks | 27 passed |
| pi32v2 objects | 26 built |

All four new functions have complete instruction coverage. Inherited gaps
belong to regions outside this corpus's exercised caller and numerical paths;
coverage from prior reports is not added to these totals. The corpus includes
one through three layers and every corresponding work split, several layer
and head sizes, carried banks and histories, signed bias extremes, worker
commands and returns, handshake observations, watchdog callbacks, cancelled
jobs, callback mutations, both timeout paths and the unchanged audio-task
caller using the actual asynchronous wrapper.

The final `verification.json` SHA-256 is
`18cfa9c7e0ae48e1002cd5ba9e899092426c9da8ee625816799a8088bfa392d3`.
The final `build-manifest.json` SHA-256 is
`08e386f3ed8ea885f1d5e4c3b523e56633b53d1a16215e037a369b04e4683897`.
All 115 source and 30 artifact bindings were rechecked after completion.
Both image bindings cover 6,241 instruction windows and eight static
provenance windows. All 25 inherited pi32v2 objects match earlier completed
milestones byte for byte. Earlier candidate directories remain unchanged.

Independent read-only review checked all new bodies and the reused wait,
including polling limits, reload order, command completion, history endpoints,
wrapped bias arithmetic, descriptor packing and timing updates. No mismatch
was found within the documented domain. The API now explicitly states the
required stable, disjoint callback storage and preservation of original
address relationships. The scoped source privacy and whitespace checks pass.
