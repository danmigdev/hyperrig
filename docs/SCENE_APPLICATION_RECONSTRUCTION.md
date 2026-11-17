# Scene application reconstruction

The complete scene application, retry wrapper and report formatter now have
compilable C. The new adapter also executes the previously recovered direct and
pending scene-selection callers through these real bodies. An enabled scene
transition runs the actual coefficient generator and installed gain notification
on the same mapped state.

Effect probing, parameter updates, enable changes, routing, clock, scheduling
and outward notifications remain explicit external services. Their controlled
test results establish caller behavior, not the arithmetic of unrecovered
effects or physical audio behavior.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
The original evidence and reconstruction retain the
[PolyForm Noncommercial 1.0.0 license](../third_party/ultrarig/LICENSE.md).
This is reconstructed C, not the original source.

## Functions and shared state

| New complete function | Original range, end exclusive | Bytes | Instructions |
| --- | --- | ---: | ---: |
| Inner scene application | `0x02009e14..0x0200a1d6` | 962 | 329 |
| Application/retry wrapper | `0x0200a1d6..0x0200a228` | 82 | 27 |
| Result and elapsed-counter packing | `0x0200a228..0x0200a256` | 46 | 14 |

These three regions contain 1,090 original bytes and 370 instructions. The
selection entries `0x02014366..0x020143ae` and `0x020148ba..0x02014952`, type,
enabled-state and parameter queries, parameter order/metadata, notification and
rate helpers are reused. Their borrowed forms add integration evidence without
adding original functions to the inventory. The
[transition notification module](DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md)
supplies the new callback body separately.

The public API is in
[`hyperrig_scene_application.h`](../firmware/include/hyperrig/hyperrig_scene_application.h),
with implementation in
[`hyperrig_scene_application.c`](../firmware/src/hyperrig_scene_application.c).
The caller supplies a stable map from original integer address tokens to
borrowed storage, plus a synchronous service callback and positive call budget.
No duplicate firmware runtime is copied across an external call.

| Original address | Bytes | Purpose |
| --- | ---: | --- |
| `0x01c1f180` | 272 | Global configuration, current scene and rate input |
| `0x01c26890` | 12,976 | State prefix and all four complete scene records |
| `0x01c2c220` | 7,680 | Sixteen 480-byte effect objects |
| `0x01c1f7d4` | 68 | Transition duration, gain and generator divisor |
| `0x01c32db0` | 640 | Filter control and current transition parameters |
| `0x01c34190` | 768 | Callback tokens, counters and scene-busy byte |
| `0x01c33030` | 176 | Four active filter sections |
| `0x01c330e0` | 176 | Staged transition records |

The earlier preset-application API retains its original 4,100-byte state view.
This new map covers the larger scene storage without changing that frozen API.
Busy byte `0x01c34489` is offset 761 in the callbacks window.

A scene record begins at `state + 11936 + 260 * scene`:

| Offset | Meaning observed in the original |
| --- | --- |
| 0 | Availability byte, checked by selection but not by the inner application |
| 1 | Routing service argument |
| 2 | Unsigned 16-bit selected-slot mask |
| 4, 5 | Two sign-extended byte arguments to `0x02008de2` |
| 6 | Sixteen desired enable bytes |
| 22 | Sixteen groups of seven signed 16-bit parameters |
| 246 | Six signed 16-bit transition inputs |
| 258 | Transition-enable byte |
| 259 | Unchanged padding |

## Application order and partial failures

The inner body captures the initial mode, configured duration and global
transition flag. A clear flag changes its captured duration to one. It snapshots
parameter 2 for every present type-7 effect, then sets the busy byte.

The first pass compares and attempts parameter changes, and handles requested
disables. A failed probe marks the slot for another pass. Before the second
pass, the routing service receives the scene's current routing byte. This pass
revisits marked parameter slots and handles requested enables. Parameter order
for type 5 swaps indices 0 and 4; every metadata and live-parameter query executes
its recovered logic.

In initial mode 2, the fast parameter service considers every result except
`-6` handled. The fast enable service distinguishes zero success, `-6` fallback,
and other failures. Other modes request the fallback directly. Repeated probe
failures count once per slot; enable failures have their own increments.

The fallback acquires the original lock service, revisits selected effects and
parameters, applies ordinary setters/toggles, then releases the lock. It does
not roll back changes already completed during either pass. Hazard handling
preserves the original conditions for type 7, type-5 parameters 0/4, type-37
parameter 6 and mode-2 enable fallback. The mode-2 mute pair encloses the later
fallback/finalization phase at its original points.

Callbacks can change mapped bytes. The C keeps captured mode/duration/type
values where the original keeps registers, and rereads masks, desired values,
live effect headers and later scene fields where the original reloads them.
The comparison checks state before and after every external call.

The busy byte is cleared before the final type-7 scan. This scan includes slots
outside the current scene mask: it compares each current parameter 2 against
its original signed snapshot, and invokes the finalization service when changed.
The body then restores mute when required, applies the signed byte pair,
executes an enabled transition, retries a previously failed routing operation,
and always publishes the selected scene. The result counts failures; it is not
a Boolean transaction status.

## Wrapper, selection and reporting

The wrapper passes the first failure count to selector `0x02028eb2`. Selector
one emits tag 3 with the current callback payload and applies the scene again.
If the first result is nonzero and the signed second result is not smaller, it
invokes `0x02028f96` and emits tag 5 with that second result. Selector one returns
the second result in all cases. Selector two emits tag 4 with zero payload and
returns the first result. Other selector values return the first result.

The reused notification helper converts these tags into its original event 30
arguments, including the tag in the upper halfword and `0xffff` in the lower
halfword. It does not substitute the outward scene-selection event 8.

Direct selection checks scene range and availability, captures the clock,
executes the actual wrapper, then optionally formats and emits the report.
Pending selection clears its counter and walks available scenes in the original
direction. The portable C reduces complete cycles after the first step; no
callback occurs within that selection loop. The original model still executes
the loop directly for comparison cases. Extreme signed counters are additionally
exercised by the C sanitizer harness.

The report preserves wrapped subtraction and multiplication. Its divisor is
`((global_word_44 * 1000) modulo 2^32) / 6 / 10`. Unsigned division by zero
produces zero under the pinned ISA model. The quotient is capped at `0x7fffff`,
shifted by eight and combined with the low result byte. These are counter
operations; no physical time unit is asserted.

## Real transition execution and API domain

Scene transitions invoke the borrowed request adapter directly. It reads the
six scene inputs after a required disabled-bank reset, retains the clamped
values across notification, generates actual coefficients/gain and publishes
staged records. Installed callback `0x0201a9ea` executes its recovered division,
clamp and gain mixer internally. Other callback tokens remain explicit services.
The corpus includes a callback that changes the input record, generator divisor
and active filter coefficient while the request is in progress.

Inner/application entries accept scene IDs 0..3. Selection accepts every
unsigned word and ignores IDs above three. Pending-scene flushing retains its
previous current-scene domain: 0..3 or a negative signed word. Disabled-bank
reset retains the earlier stored-parameter bound of -1280..1280. Other scene
parameter words, enabled bytes, masks, durations and status values retain their
original raw domains.

Mappings preserve original address relationships. Distinct native windows must
not become arbitrary host aliases. IO and result objects are disjoint from
mapped storage; mapping/IO objects and allocation lifetimes remain stable.
Callbacks can synchronously change permitted mapped bytes, with no re-entry,
concurrency or retained pointers. The active filter storage has the alignment
and compatible typed little-endian backing required by the transition adapter.

New API statuses are `-200` for invalid arguments, `-201` for a missing initial
mapping, `-202` for the external-call budget and `-203` for an inherited
transition mapping/domain guard. They can follow partial native writes, and
do not introduce rollback. The separate result output is written only when the
operation completes. Selection/flush incidental native return registers are
not exposed as results by their void-behavior APIs.

## Reproduction and evidence

[`scene_application_machine.py`](../tools/scene_application_machine.py) decodes
the whole original bodies and joins the unchanged numerical instruction models.
One memory dictionary, register file and live stack carry the scene into the
transition and notification. Parallel packets use their original register
snapshots; unknown instructions, calls, uninitialized reads and memory escapes
stop verification.

[`verify_scene_application.py`](../tools/verify_scene_application.py) compares
all eight mapped windows, native inner/wrapper/report results, ordered service
arguments and state on both sides of every external call. Its fixtures exercise
fast/rebuild paths, failures, callback mutations, all effect metadata types,
selection availability/direction, wrapped reporting and carried scenes. Recovered
transition arithmetic is never replaced by scripted coefficient/gain results.

Every external service's argument count was reviewed against its original
callee, separately from the caller comparison. Parameter probing receives the
signed desired value as its third argument; both enable services receive the
raw desired byte as their second argument. The probe sees the value loaded
before its call, while fast update and commit reload the scene value afterward.
Focused tests and comparison fixtures assert those values directly.

```text
python tools/build_scene_application.py --output build/reverse-scene-application-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder requires a fresh ignored output directory, pinned local inputs and
the pi32v2 toolchain. It compiles a warning-clean host library, target objects,
focused instruction tests and an ASan/UBSan executable. Its source manifest is
derived from loaded repository modules and included C headers, without earlier
ignored build reports as prerequisites.

Every loaded instruction window, all declared complete regions and the exact
metadata, gain and coefficient tables are bound to the original application
and reviewed MINI v4. Earlier sources, reports and tested images are preserved.
No device access, physical audio test, flashable firmware or release is produced.

## Recorded validation

The development report `build/reverse-scene-application-01` is preserved but is
not selected as final evidence. Subsequent callee review found that its shared
service table omitted the probe's desired value and both enable services'
desired bytes. The C and original-instruction boundary shared that omission,
so their earlier agreement did not verify the complete calling contract.
The corrected source and independent argument checks are recorded in the
final evidence at `build/reverse-scene-application-03`. Development report
`-02` has the same numerical results, but omitted three dynamically loaded ISA
helper files from its manifest. Report `-03` explicitly binds those files and
preserves all sixteen target objects byte for byte:

- 561 C/original comparisons: 182 inner applications, 86 wrappers, 39 direct
  selections, 55 reports and 199 pending-scene flushes.
- All 370 new instructions and all 517 instructions in the twelve declared
  regions visited. Loaded-model coverage is 996/1,954; the 958 inherited gaps
  remain explicit and are not filled using other reports' coverage.
- 41 actual installed gain notifications, sixteen callback-mutation cases and
  twelve carried scene selections.
- Twenty-one focused tests, eighteen C-only guard checks and 704 exact-allocation
  ASan/UBSan cases passed.
- Sixteen pi32v2 objects built; all fifteen reused objects are byte-identical to
  their prior milestone outputs. The new object is 4,060 bytes, not a firmware
  image or an estimate of final linked flash usage.
- All 67 source and twenty artifact hashes were independently read back. A
  separate review checked the complete new bodies, both selection callers and
  every external callee contract. The three argument omissions were corrected;
  no further in-domain mismatch was identified in that review.

The C source SHA-256 is
`22063984cc299b97bfc1bf4dd103ce76d251ac7a521e4fbfcf432e493b5ae717`.
The verification report SHA-256 is
`1d09de1c1359f3392ff6185564f8cb5900d3cc08e8312e66b39695713e828f65`.
The build-manifest SHA-256 is
`5e321dd395f2a64f4082ce970863e6f0ce4163be2b78a8fc936ecb9b65964dd3`.
The target-object SHA-256 is
`c83d14d8bb1b71a9bfcff2fa28e46a6d9f4721b3c6788b6206fdd376aeacefac`.
