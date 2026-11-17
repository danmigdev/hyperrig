# Complete all-pass, gate and state-variable signal leaves

This is a readable C reconstruction of three complete M5.71 numerical bodies,
compared with independently decoded original instructions. It replaces their
explicit service boundaries in the unchanged effect-processing reconstruction
and reaches them through the actual dispatcher, individual/grouped effect
wrappers, stage and audio-task bodies. It is not original source, a firmware
image, a physical audio test or evidence that every effect has been recovered.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

See [the preserved license](../third_party/ultrarig/LICENSE.md).

## Original bodies and ABI

All three bodies receive `(samples, count, state)` in `r0`, `r1` and `r2`.
Their complete bodies have no direct/indirect calls, stack arguments, MMIO or
embedded static data. Original state and samples are mutable little-endian
mapped bytes; the reconstruction does not replace them with generated answers.

| Body | Original half-open range | Instructions | Actual dispatcher sites |
| --- | --- | ---: | --- |
| Four-stage all-pass | `0x01c1958e..0x01c19a8a` | 415 | Type 13 at `0x01c0e4f8` and `0x01c0ef2c` |
| Envelope/hysteresis gate | `0x01c19a8a..0x01c19bee` | 117 | Type 1 at `0x01c0e28c` |
| State-variable filter core | `0x01c1ee40..0x01c1f088` | 176 | Type 38 at `0x01c0eae0` and `0x01c0eb0a` |

The new module contains numerical C loops and named operations. The independent
Python model decodes the pinned original bytes using the preserved pi32v2 ISA
table and executes their register, stack, predicate and memory semantics. The C
does not contain a second instruction interpreter.

## State, arithmetic and ordering

The all-pass body caches its current coefficient at state `+8`, feedback at
`+12`, preceding input at `+20`, and four history words at `+36..+48`.
Each 16-sample block reloads phase/increment at `+0/+4`, publishes the advanced
phase, folds and curves it, and interpolates two adjacent entries from the
33-word Q30 coefficient table at `+52..+180`. It interpolates the working
coefficient across the block, including the original terminal assignment.
Each sample traverses the four rounded Q30 all-pass stages with Q16 feedback.
The final history publication also writes `+24/+28/+32` in native order.
The table is mutable effect state, not an immutable firmware-data exclusion.

The gate caches thresholds, envelope coefficients, smoothing coefficient,
envelope and gain at `+0..+24`. It scans 16 samples before any sample write.
Native absolute value maps `INT_MIN` to `INT_MAX`. Envelope attack/release and
strict threshold comparisons update the open state, which initially depends on
whether signed gain exceeds 32768. The native unity shortcut does not write
samples; the zero-gain path clears 16 words; other paths apply a wrapping Q16
gain ramp. Only the final envelope and gain words are published to state.

The state-variable body caches two integrators, two residual words, three
coefficients and three output gains at `+0..+36`. Residuals enter the wide
accumulators as unsigned low words, as in the original instructions. It keeps
the low 30 residual bits and updates both integrators for every sample. Output
mixing shifts the signed wide accumulator by 26. It prefetches the next input
before the current store within each four-sample group. Its final publication
updates only the two integrators and two residuals.

All word and wide accumulator operations preserve modulo `2^32`/`2^64`
arithmetic, explicit arithmetic shifts and the original truncation points.
Overflow clipping produces `INT_MAX` or `-INT_MAX`; an exactly representable
`INT_MIN` remains `INT_MIN`. These are distinct from the gate's saturating
absolute-value rule. Sample/state overlap, including writes into the all-pass
phase and coefficient table, is preserved by cached versus fresh native reads
and ordered stores.

## Counts, storage and finite execution

The all-pass and gate compute `((count + 15) modulo 2^32) >> 4`, then enter
their 16-sample loop before decrementing that block count. Counts 1 through 16
therefore process 16 samples. A computed block count of zero does not skip the
loop: its counter requires `2^32` iterations to return to zero.

The filter computes `end = samples + (count << 2)` modulo `2^32`. It processes
four samples, advances the pointer by 16 and tests equality with the endpoint.
A nonmultiple-of-four count can produce an unreachable endpoint. An endpoint
equal to the starting pointer requires a complete address-space walk, while a
large raw count such as `0x40000004` has the same short endpoint as count 4.
These native rules are not replaced by a zero-count no-op or a 512-sample cap.

The public `block_budget` is shared across all new leaf calls in one API
invocation. One unit permits a native 16-sample all-pass/gate block or a
four-sample filter block. Budget exhaustion returns `-203` before the next
block's writes, preserving the public-memory prefix. Initial cached state
reads happen before that check, matching native entry order. A stopped call
does not publish histories that the original only writes on normal exit.
The instruction model imposes a separate verification step limit; it does not
claim to have executed billion-block walks to completion.

Mapping is byte-based and supports unaligned host backing and ordinary
unaligned native tokens. Distinct native bytes must not alias host storage.
Mappings are pure and consistent; API/IO/result/control storage is disjoint
from mapped data. The native private stack `0x30000000..0x30001020` is reserved,
and a four-byte access cannot cross the 32-bit address boundary. The inherited
processing/stage/audio contracts still apply to their own typed storage and
bounded caller inputs. New raw-leaf counts have no arbitrary sample ceiling.

Errors `-200`, `-201` and `-202` describe API/service, mapping and access-domain
failures. They retain preceding C writes. Only block-budget stops are compared
as exact original public-memory prefixes; general missing-map failures are not
claimed to model native faults. Errors are not resumable task observations.
Successful audio observations continue to use the unchanged task resume API.

## Joined execution and remaining boundaries

The signal adapter replaces only the three audited numerical service targets,
requiring their exact three-word ABI and borrowing the original caller's map.
Other explicit services keep their original arguments, callback order and
mutation behavior. The shared block budget spans nested leaf calls. The
original model merges identical frozen instructions and uses the same original
register/stack/RAM state through the audio-task and effect caller chain.

The corpus exercises direct leaves, overlapping sample/state layouts, retained
histories, native counts above 512, wrap-short counts, budget-stop prefixes,
strict gate thresholds, unity/mute paths and raw signed coefficient extremes.
It also exercises the real type 38 coefficient-update caller, type 13 stereo
routing, actual grouped up/down resampling, clock-callback parameter mutation
and carried audio-task observations. The audio fixture's remaining output and
platform services are explicit scripts; they are not recovered output
arithmetic or physical audio.

Parameter values in this checkpoint are synthetic mutable fixtures, including
the all-pass lookup words. The newly recovered construction module is a
separate checkpoint and is not silently invoked here. Matching original
producers are type 1 at `0x0202d2d8..0x0202d350`, type 13 at
`0x0202d6fa..0x0202d7ea`, and type 38 at `0x0202d9b0` with the tail at
`0x0202dc7a..0x0202ddfc`. Constructor-to-signal execution is an explicit next
integration boundary. Other effect-specific numerical leaves and platform
services remain unresolved where the existing processing reconstruction lists
them.

## Evidence and reproduction

The pinned original image SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The decoded payload SHA-256 is
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
The preserved MINI v4 image SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

Final evidence is frozen in ignored `build/reverse-effect-signal-01/`:

- 555 original/C comparisons and 2,722,431 original instruction steps.
- All 708 new instructions visited, with no new instruction gaps.
- 3,131 of 17,772 loaded instructions visited in this corpus. All remaining
  loaded addresses are listed; previous report coverage is not added.
- 6,814 original signal blocks, including 72 actual leaf entries from 36
  carried audio-task observations.
- 16 focused tests, 22 C API guards and 555 ASan/UBSan comparison replays.
- 33 pi32v2 objects built. All 32 inherited objects match the preceding frozen
  processing build byte for byte; the new signal object is 4,120 bytes.
- 146 source bindings and 39 artifact bindings independently rehashed after
  completion. The MINI binding covers all 17,772 loaded instruction windows
  and 23 inherited static windows, including unvisited loaded code.

`verification.json` SHA-256:
`be0b926e5869b782024f93168d32deba8e7f345fd79265bdc8c15c584f4000ef`.

`build-manifest.json` SHA-256:
`175adf4c5ef872cdc47f3c878eb2fbf810abc57b8aa04b0c0ac96973779bde87`.

Prior completed reports and images remain unchanged. The final report binds
every loaded instruction window and inherited static range to both pinned
payloads and lists loaded but unvisited code explicitly. These are bounded
corpus measurements, not an overall firmware completion percentage.

The source manifest includes the new C/header/model/verifier/builder/tests,
all transitive C headers and Python modules, dynamically loaded ISA helpers and
the ISA TOML. It asserts those inputs stayed unchanged during comparisons.
The builder compiles the host library with UndefinedBehaviorSanitizer, builds
each C input for pi32v2, and replays every original comparison under both
AddressSanitizer and UndefinedBehaviorSanitizer. Direct-kernel sanitizer replay
deliberately uses host backing offset by one byte.

From the repository root in WSL, choose a fresh output directory:

```sh
python3 -B tools/build_effect_signal.py \
  --output build/reverse-effect-signal-new \
  --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The preserved firmware inputs and compiler distribution are required local
evidence. No previous ignored verification report is needed as an input.

Independent read-only review compared all three complete numerical bodies and
their API contracts against the original listings. It found no arithmetic
mismatch, and identified the need to reserve the original private stack and
retain filter prefetch order. Both changes were made and independently
rereviewed before the final run. The reviewer did not alter files or rerun the
suite.

Maintained files for this checkpoint are the new `hyperrig_effect_signal.h/.c`,
`effect_signal_machine.py`, `verify_effect_signal.py`,
`build_effect_signal.py`, `test_effect_signal_machine.py`,
`effect_signal_sanitize.c` and this document. All generated evidence stays
under ignored `build/` storage. No device was accessed or flashed.
