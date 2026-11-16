# Reconstructed switch transition core

Two UltraRig TANK-G v2 M5.71 routines have been reconstructed in portable C:

| Original CPU range, end exclusive | Recovered implementation |
| --- | --- |
| `0x0200c9c2..0x0200c9f4` | `hyperrig_controls_immediate`: decide whether the primary action runs at the press edge. |
| `0x02014c04..0x02014d44` | `hyperrig_controls_transition`: record a raw transition, resolve the logical slot and update event state. |

Sources: [`hyperrig_controls.c`](../firmware/src/hyperrig_controls.c) and
[`hyperrig_controls.h`](../firmware/include/hyperrig/hyperrig_controls.h).
These are hand reconstructions from decoded instructions, not recovered original
source files. The original Required Notice and license are retained.

The reference application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The two function regions have SHA256:

- Transition: `6eeb3a4edea19533d3aeca6da629ca4434a7fd6a4889b2ea7ee84f1b329374e7`.
- Immediate policy: `70b59e201125da26dbfaec0984718a0701c3e5279caf40c8f8ac8fb9a3cb6b33`.

Both regions are byte-identical in the published MINI v4 application image,
SHA256 `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This binds the recovered code to that image; it does not establish physical
switch order, correct GPIO/LED behavior or a three-slot bank implementation.

## State contract

The original global base is `0x01c1f180`, the working-state base is `0x01c26890`,
and a separate one-byte repeat owner is at `0x01c26864`. The C API uses ordinary
caller-owned arrays for the bounded prefixes accessed by these functions. It
does not dereference original target addresses or claim a complete state layout.

| Base + offset | Width/count | Observed use |
| --- | --- | --- |
| Global + 11 | Byte | Per-logical-slot immediate-action mask. |
| Global + 116 | Four bytes | Logical-to-physical map; the last matching logical slot wins. |
| Global + 239 + 9 x slot | Byte | Event-1 action type, used by the immediate policy. |
| Global + 242 + 9 x slot | Byte | Event-2 action type, used by the policy and deferred edge path. |
| State + 74 | Byte | Action-processing enable gate. |
| State + 932 | Four bytes | Per-slot event-1/suppression state. |
| State + 960 | Four bytes | Per-slot suppression of the following release. |
| State + 964 | Four bytes | Per-slot pending second-edge state. |
| State + 1508 | uint32 | Shared repeat deadline. |
| State + 1567 | Five bytes | Last observed raw physical level. |
| State + 1608 | Four uint16 | First timer counters, cleared by a press edge. |
| State + 1616 | Four uint16 | Second timer counters, cleared when an edge becomes pending. |
| State + 1828 / 1844 | Four uint32 each | Two original event stamps retained per logical slot. |

The GPIO caller at `0x02015a6a..0x02015ac6` derives level 1 from a low input bit,
so the API names that level `pressed`. Electrical mapping and debounce scheduling
are outside this reconstruction.

Key observed behavior:

- Identical raw levels are ignored. A changed raw level is stored even when
  actions are disabled or no logical slot maps to the physical input.
- The original has five raw input slots and four logical action slots. The
  MINI port limits physical scanning and changes the map, while retaining the
  four-slot action representation. This component preserves that baseline.
- A nonzero event-2 action disables immediate execution. Otherwise a missing
  event-1 action permits immediate execution; a configured event-1 action uses
  the per-slot mask.
- The repeat path tests the sign bit of a **wrapped 32-bit subtraction** and
  extends the deadline by 2500 with wrapping. Equality expires the window. The
  units of the two stamps are not established by these functions alone.
- A pending second edge preserves the first stamps; a subsequent qualifying
  release emits original event code 2. The timer worker is a separate dependency.

Names such as repeat and pending describe observed roles. Event codes 0, 1 and 2
retain their original values. Their complete user-facing action semantics depend
on the unreconstructed dispatcher and timer worker.

## Execution boundary and API differences

The original action executor at `0x020149b6` is represented by an optional callback.
Verification records its logical-slot/event arguments and the complete bounded
state at the call, without executing preset, effect, LED or other side effects.
The immediate-policy helper is executed from its original bytes by the oracle.

The C wrapper validates non-null context, physical index 0..4 and level 0/1 before
writing. Invalid calls return -1 unchanged; this is a new API safety boundary,
not an assertion that the original firmware checks invalid callers. No context
initialization, timer advancement, hardware access or thread synchronization is
provided. The C storage/API is not a drop-in target ABI replacement.

## Verification

The [restricted interpreter](../tools/control_machine.py) extends the existing
DSP instruction interpreter for these two functions. It checks the reference
image, decodes original bytes, maintains bounded initialized RAM and callee-saved
register frames, and rejects unknown calls/instructions or escaping memory.
Its correctness still depends on the implemented instruction semantics.

The host C build passed **15,520 comparisons** against that interpreter:

- 6,144 immediate-policy comparisons covering masks, logical slots and all
  byte values of the relevant action fields.
- 7,328 transition comparisons covering maps, duplicates, absent inputs, flags,
  wrapped counter boundaries and 4,000 randomized initialized-state cases.
- 2,048 consecutive transition steps, carrying the prior result forward.

Comparisons include all bounded global/state bytes, repeat ownership and the
arguments/state at every action callback. All **119 decoded instructions** were
visited. This is instruction coverage, not proof of every path or every possible
firmware state. Five invalid-API checks and a null-callback state check passed.
Ten separate hand-calculated tests check the interpreter's behavioral boundaries.

The C source compiles with warnings as errors on the host with UBSan and to a
pi32v2 relocatable object using the pinned JieLi compiler. No target object has
been run on a pedal. There is no hardware, audio, IRQ-concurrency or complete
action-executor test, and no firmware image was changed or installed.

## Reproduce

Obtain the pinned originals, analysis and toolchain using the existing
[local-source workflow](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows, WSL Ubuntu provides GCC and the JieLi compiler.

```powershell
python -B -m unittest discover -s tests -p test_control_machine.py -v
python -B tools/build_controls.py --output build/reverse-controls-new
```

To additionally bind the recovered functions to the published v4, supply
`--mini-image` with the extracted release's `hyperrig-mini-v4.app.bin` inside the
workspace. Only the exact reviewed v4 hash is accepted. This optional check uses
the application image, never a device backup.

Outputs remain under the new build directory: host library, pi32v2 object,
`verification.json` with source/decoder hashes and a build manifest. Existing
output directories and reports are preserved. The completed local run is
`build/reverse-controls-02`.

Next: [action execution and timer reconstruction](REVERSE_ROADMAP.md#next-concrete-milestone).
