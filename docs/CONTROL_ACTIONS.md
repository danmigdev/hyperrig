# Reconstructed action dispatcher and switch timers

The control reconstruction now executes switch edges, timer-generated events
and action selection in portable C. Downstream preset, scene, effect and mode
handlers remain explicit external services. This is a development component,
not a replacement firmware image or an implementation of the Alpha 13 backport.

This document describes the action/timer component's original verification
boundary. The separate [selection reconstruction](SELECTION_RECONSTRUCTION.md)
now executes preset stepping, scene selection and effect binding internally;
this component's source and reports remain unchanged.

Sources: [`hyperrig_control_actions.c`](../firmware/src/hyperrig_control_actions.c)
and [`hyperrig_control_actions.h`](../firmware/include/hyperrig/hyperrig_control_actions.h).
The [previous transition component](CONTROL_RECONSTRUCTION.md) is reused unchanged.
These are hand reconstructions, not recovered original source files. Original
Required Notices and licensing are retained.

## Reference and binding

The reference is the same original G v2 M5.71 application, SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| Original CPU range, end exclusive | Reconstructed behavior | Function SHA256 |
| --- | --- | --- |
| `0x020149b6..0x02014b3c` | Action dispatcher, including its ten-entry byte branch table | `dfdb7bb280ea52b054530f8ba3a8d041fa926459ef728a9635725bb11f277b6d` |
| `0x02014b3c..0x02014c04` | Four-slot timer worker | `ca1a67cc67f205b1c1fa79f3158293ae41f9c59e762914279e492e0a74b6bec9` |
| `0x0200c996..0x0200c9a4` | Read global counter and multiply by ten, with uint32 wrapping | `ad5a35d347d3b3b95d20f41fbe2671599ce8656b009699b392c0a6f49686937d` |

These three regions and the two previous control functions are byte-identical
in the published MINI v4 application, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This binds the analysis to that image, not to physical switch or audio behavior.

## Action records and state

Each of four logical slots has three records: event 0, 1 and 2. A record is
three bytes `[type, argument, auxiliary]` at global offset
`236 + 9 * logical + 3 * event`. This is a 36-byte table ending at offset 271.
The previous transition function needed only its first 34 bytes. The new
`hyperrig_control_runtime` embeds the unchanged transition context and adds
`action_tail[2]` for global offsets 270 and 271. It is portable storage, not the
original target ABI or a complete description of firmware RAM.

Additional observed fields, relative to the existing state/global bases:

| Location | Observed use |
| --- | --- |
| Global + 24, uint32 | Counter read by `0x0200c996`; its product with ten is stored in action timing fields. |
| State + 52, byte | Boolean toggle operated by action type 9; full product meaning remains unresolved here. |
| State + 812, uint32 | Most recent dispatched action time. |
| State + 924, four bytes | Per-slot action marker set to 1. |
| State + 928, uint32 | Second event stamp copied for action type 7. |
| State + 956, uint32 | Pending relative scene-step accumulator, with original wrapped arithmetic. |
| State + 968 / 972, uint32 each | Copies of the selected slot's two event stamps. |
| State + 1812, four uint32 | Per-slot action time. |

Every dispatch first calls the notification boundary with
`(9, logical, event | type << 8 | argument << 16)`, then reads the counter and
updates the action fields. The type is re-read after notification. If pending
steps exist, types other than 5 and 6 call the pending-step handler and then
re-read the type again. Callback order and these re-reads are significant.

| Type | Selection behavior inside this reconstruction |
| --- | --- |
| 0 or above 10 | Retain notification/bookkeeping; no selected action handler. |
| 1 | Call the scene handler with the argument byte. |
| 2 | Query preset availability; if nonzero, load it. A zero load result permits an optional scene call when auxiliary is 0..3. |
| 3 / 4 | Call the relative preset handler with +1 / -1. |
| 5 / 6 | Add +1 / -1 to the pending-step accumulator with uint32 wrapping. |
| 7 | Forward both stamps to the tap handler, except the held-event repeat-arm path described below. |
| 8 | Resolve an effect, read its state and request the opposite boolean state. A negative resolution emits a diagnostic notification. |
| 9 | Toggle state byte 52 between zero and one. |
| 10 | Read the mode boundary and request the opposite boolean value; a nonzero set result emits notification `(10, 511, 0)`. |

Names describe observed roles, not recovered symbols. Scene/preset availability,
loading, effect resolution and mode semantics require the original leaf handlers;
recording their calls does not reproduce their effects.

## Timers and repeat behavior

When state byte 74 is enabled, the worker examines all four logical mappings.
A held raw input with a clear event-1 flag advances its first uint16 timer.
At **1000 counter units**, a configured event-1 action sets its flag, clears
pending second-edge state and dispatches event 1. A released raw input with
pending second-edge state advances its second timer; at **301 units**, the
worker clears the pending flag and dispatches event 0.

Timer addition is uint32 wrapping followed by a cap of 60000, then a uint16
store. Thus `65535 + 0xffff0001` becomes zero before the cap. Changing this to
a wide saturating addition would change the original behavior. Physical time
units remain unassigned until the scheduler and counter update paths are traced.

Type 7 on event 1 with a nonzero first timer arms the repeat owner and sets its
deadline to the current counter product plus 2500. That invocation returns
without calling the tap handler. A later qualifying press is handled by the
existing transition routine, which clears that timer before dispatch.

Duplicate mappings still advance each logical slot separately. The worker
captures a slot's physical index before dispatch and re-reads the raw state
at that same index afterward. Mapping bytes above 4 address other bytes inside
the bounded state prefix; they are retained for comparison, not interpreted as
additional real switches. If byte 74 is zero, the worker delegates to the
unreconstructed routine at `0x020146ae`.

## External service contract

The required callback receives a service identifier and three uint32 values.
Unused values are zero; signed arguments/results retain their bit patterns.
Original incidental values in unused caller-saved registers are not API arguments.

| Service identifier | Supplied arguments | Used return value |
| --- | --- | --- |
| `0x02002d10`, notify | Event category, code/slot, payload | Ignored |
| `0x020148ba`, flush pending steps | None | Ignored |
| `0x02014366`, scene | Scene argument | Ignored |
| `0x0200cf88`, preset exists | Preset argument | Nonzero permits load |
| `0x0200ca7e`, preset load | Preset argument, re-read after query | Zero permits optional scene |
| `0x02014952`, preset step | +1 or `0xffffffff` | Ignored |
| `0x0200a4b2`, tap | First stamp, second stamp | Ignored |
| `0x0201499c`, effect resolve | Global action-record offset, replacing a target pointer | Nonnegative effect index or negative failure |
| `0x020308ea`, effect get | Resolved index | Zero/nonzero state |
| `0x0200d060`, effect set | Resolved index, requested boolean | Ignored |
| `0x0200733e`, mode get | None | Zero/nonzero state |
| `0x02008ca2`, mode set | Requested boolean | Nonzero requests notification |
| `0x020146ae`, disabled tick | Forwarded delta | Ignored |

Callbacks may synchronously modify the runtime through their opaque context.
Re-entry, interrupts and concurrent mutation are outside the contract. New C API
checks reject null contexts/callbacks, logical slots outside 0..3, events outside
0..2 and invalid physical edge arguments before changing memory or calling out.

## Verification and limits

The [instruction verifier](../tools/control_action_machine.py) decodes the
original bytes, excludes the inline branch-table data and executes the original
clock helper. It models exclusive then/else blocks, packet counting and parallel
pairs reading pre-packet register values. Those rules follow the pinned ISA
project's [compiler observations](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/docs/COMPILER.md)
and [FM-1 instruction experiments](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/hw/fm1-2026-10-24-v3/README.md).
Those upstream experiments are not HyperRig MINI hardware tests.

The completed run passed **10,101 instruction-versus-C comparisons**:

- 4,836 direct action-dispatch calls, covering all action bytes, slots and events.
- 3,089 timer calls, including threshold, cap, overflow and duplicate-map cases.
- 2,176 integrated edge calls, including repeat-window and wraparound cases.

These counts include 2,048 consecutive sequence steps and five scripted
callback-mutation cases; those are subsets, not additional comparisons. All 193
new decoded instructions were visited, and all 312 including the reused
transition/policy functions. All 13 external service boundaries were exercised.
Full byte snapshots and ordered semantic call arguments match. Eleven invalid
API checks and 14 separate hand-calculated interpreter tests also passed.

The host library builds with warnings as errors and UBSan. The unchanged
transition object is 932 bytes and the new pi32v2 relocatable object is 1,856
bytes. Object file size is not linked firmware size or a measured resource budget.
The objects have not run on the pedal. Leaf services use supplied return values
and mutations, not original leaf instructions. Coverage is not proof of every
path. There is no audio, physical control, scheduling, IRQ or transport validation.
Four logical slots remain; no firmware, editor control or backport is released.

## Reproduce

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native compiler prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows the builder uses WSL Ubuntu:

```powershell
python -B tools/build_control_actions.py --output build/reverse-control-actions-new
```

Optionally add `--mini-image` with the extracted released
`hyperrig-mini-v4.app.bin` inside the workspace. Only its reviewed hash is accepted.
The builder runs the focused tests and comparisons, producing host/target
objects, `verification.json` with source/decoder hashes and a build manifest.
Existing output directories are refused. Generated evidence remains ignored by
Git; the completed local run is `build/reverse-control-actions-01`.

Continue with the completed [selection reconstruction](SELECTION_RECONSTRUCTION.md)
and the [next roadmap milestone](REVERSE_ROADMAP.md#next-concrete-milestone).
