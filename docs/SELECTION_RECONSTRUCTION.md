# Reconstructed preset, scene and effect selection

The next control component reconstructs preset navigation, scene selection and
effect binding in portable C, and connects them to the existing edge, timer and
action model. This completes the four requested offline work items: reconstruct
the three selection paths, compare their combined behavior with the original
instructions, and compile the sources for the host and pi32v2.

Sources: [`hyperrig_selection.c`](../firmware/src/hyperrig_selection.c) and
[`hyperrig_selection.h`](../firmware/include/hyperrig/hyperrig_selection.h).
The previous [transition](CONTROL_RECONSTRUCTION.md) and
[action/timer](CONTROL_ACTIONS.md) source files and verification reports remain
unchanged. This is a hand reconstruction with the original Required Notice and
license retained, not recovery of original source files or a bootable firmware.

The later [preset storage component](PRESET_STORAGE_RECONSTRUCTION.md) replaces
the availability boundary with address/header/CRC/cache logic and integrates it
with this unchanged model. The results below remain the original selection-only
baseline, with scripted availability and load outcomes.

## Original functions and MINI binding

The reference G v2 M5.71 application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x02014952..0x0201499c` | Relative preset search | `663da2fad99307fdb6c38b904a98d6b1e0fcda34dfa616d27ac3149064c80c87` |
| `0x020148ba..0x02014952` | Pending scene-step selection | `a4be69b6d27cbe34c8e2fa9d8a2e5c9e8659ac764115efad52bde1b91bc4eb53` |
| `0x02014366..0x020143ae` | Direct scene selection and notification | `2de5a0218f0403369c22d8bd1421252783767729c717d141a43eadf91d7b9927` |
| `0x0201499c..0x020149b6` | Convert a matching chain position into an effect slot | `d7c1ad6413f40d6a223353551d3b941f9e172fa12ea2f3e9537f842773e192c2` |
| `0x0200c846..0x0200c89a` | Match an effect action against the flattened chain | `2c638d7bd66493d5b8acc7a8bc1af8325b019c36ca63215ffc02f8d5468c8b90` |
| `0x0200c77a..0x0200c7ce` | Flatten two chains and collect their effect types | `23f24a012927bdd2c93bba8d3c8dccb151dd1ee2a950e7122149b3f3a3b54d12` |
| `0x0203089a..0x020308cc` | Copy one chain's ordered slot IDs | `cae410e7919ab1d95ebd03b76d468b4aa6b632660f1a153eb6b6a211816df56d` |
| `0x020308cc..0x020308ea` | Read a present slot's effect type | `ee0bed8cadca66ab184d0b68966985cb5e0f0271e502ae3d514a9e1088c5f7b1` |
| `0x020308ea..0x02030906` | Read a present slot's enabled state | `b41a9a5bcb6ab014f7e3f1800aea8caf1c981bf21b476269b4d541aa27bdc81c` |

All nine new regions and the five previous control regions are byte-identical
in the published MINI v4 application, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Byte identity binds the analysis to that image; it is not a physical control test.

## Preset navigation

The current preset is the int32 bit pattern at global offset 92. The normal
action paths pass a step of +1 or -1. The search probes at most 32 candidates:

1. If there is no current preset (a negative value), start at 0 when moving
   forward or 31 when moving backward.
2. Otherwise compute the candidate from the current value and step, wrapping
   through the 32 slots. The original uses a wrapped addition followed by
   signed division/remainder; unusual input bit patterns preserve that behavior.
3. Query availability. A zero result skips loading. A nonzero result calls the
   loader, and **only a zero loader result ends the search successfully**.
4. A failed load advances from the attempted candidate, even if its callback
   modified the global current-preset field. The 32nd candidate can be the
   starting preset. No candidate succeeding means no further action.

The model retains all 32 slot IDs. Arbitrary 32-bit steps preserve the original
bounded search, including repeated candidates for zero/non-coprime steps.
This is individual preset navigation, not a change to bank grouping. The
separate original bank-index helper at `0x0200cba0` still divides by four.

Availability at `0x0200cf88` and loading at `0x0200ca7e` remain external services.
The tests supply availability and load outcomes; they do not read flash,
deserialize presets or apply their DSP state. Their handling is verified here;
their internal storage behavior belongs to the next reconstruction milestone.

## Scene selection

The current scene is at global offset 88. Availability is one byte per scene at
state offset `11936 + 260 * scene`. A direct selection accepts only IDs 0..3
with nonzero availability. Pending steps at state offset 956 are cleared before
selection or any external call. Each step advances to the next active scene in
the requested direction, checking at most four positions. With no current scene,
forward starts at 0 and backward at 3. No active scenes means no application call.

A successful selection performs these external calls in order:

1. `0x01c04862`: capture a clock value.
2. `0x0200a1d6`: apply the selected scene.
3. If state byte 740 is zero **after application**, call `0x0200a228` with the
   application result and the captured clock, then notify with
   `(8, selected_scene, report_result)` through `0x02002d10`.

The DSP application and timing/report implementation are not executed by this
component. Its clock values remain opaque; no physical time units are inferred.

The original scalar `abs` saturates `0x80000000` to `0x7fffffff`, as established
by the pinned ISA project's [hardware findings](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/hw/report-q.md).
The C reconstruction uses that magnitude. To avoid billions of iterations for
an extreme pending counter, it removes complete cycles of active scenes:
`effective_steps = (magnitude - 1) % active_count + 1`.
After the first step, selection cycles through the active set. There are no calls
inside the selection loop and concurrent mutation is excluded, so this preserves
the final selected scene and observable call/state behavior. It does not reproduce
the original instruction count or execution time. The instruction oracle retains
the original loop; large active-scene counts are checked separately as described below.

## Effect bindings and chain lookup

Additional RAM is represented as sparse caller-owned fields, not target pointers:

| Runtime field | Original location | Meaning |
| --- | --- | --- |
| `scene_active[4]` | State + `11936 + 260*i` | Scene availability bytes |
| `chain_count[2]` | `0x01c32db0 + 14 + i` | Entry count in each chain |
| `chain_order[2][10]` | `0x01c32db0 + 348 + 10*i + j` | Ordered raw effect-slot IDs |
| `effect_header[16][3]` | First three bytes of `0x01c2c220 + 480*i` | Type, enabled state, presence |

The resolver enumerates chain 0 followed by chain 1, retaining at most sixteen
entries. It preserves duplicate IDs, absent slots and invalid raw IDs in this
position list. Type lookup returns zero for an absent slot or an ID above 15.
For an action record `[type, argument, auxiliary]`:

- Type must be 8.
- Auxiliary 255 means **absolute position**: argument indexes the flattened
  list, and the corresponding raw slot ID is returned.
- Otherwise argument is a nonzero **effect type**, and auxiliary selects its
  zero-based occurrence across both chains. The corresponding slot ID is returned.
- A missing position or type occurrence returns -1, allowing the existing
  dispatcher to emit its original diagnostic notification.

Absolute bindings check list position, not slot presence or validity. They can
return an absent slot or ID 255. The reconstructed enabled-state getter returns
zero for absent/out-of-range slots; the subsequent set call remains an external
boundary. Type-based bindings cannot match absent entries as type zero. This
distinction is retained rather than silently changing original assignments.

## API and remaining boundaries

`hyperrig_selection_runtime` embeds the unchanged action runtime and the sparse
fields above. Entry points provide direct preset stepping, direct/pending scene
selection, effect resolution, and integrated action/tick/edge execution. The
adapter handles the newly reconstructed calls internally. It forwards eleven
remaining services: clock, notify, mode get/set, scene apply/report, tap,
preset availability/load, effect set and the disabled-control worker.

New API validation requires non-null runtime and required callback, chain counts
0..10, and current scene 0..3 or a negative int32 bit pattern. Counts above ten
would exceed the original flattening helper's local chain buffer. These checks
are new wrapper behavior, not a claim that the original validates corrupt state.
Invalid calls are side-effect-free: -1 for state/action entry points, -2 for the
effect resolver. A valid resolver returns the raw ID or -1 for a missing binding.
Record offsets must identify one of the twelve original three-byte records.
Callbacks must preserve the domain; re-entry and concurrent mutation are excluded.

The context is not a target ABI replacement, a full firmware state definition or
a preset serialization format. No flash writes, hardware access, three-switch
bank change or Alpha 13 feature is implemented by this component.

## Verification

The [restricted interpreter](../tools/selection_machine.py) executes the new
functions alongside the previous control functions. It adds signed division,
saturating scalar absolute value and checked local stack storage. Local reads
must follow initialization. Existing predication, table branches and parallel
packet semantics are reused. ISA/decoder source hashes accompany the report.

The completed run passed **14,631 C-versus-instruction comparisons**:

| Operation | Comparisons |
| --- | ---: |
| Preset search | 2,573 |
| Pending scene steps | 2,415 |
| Direct scene selection | 414 |
| Effect resolution | 7,305 |
| Integrated action / timer / edge | 300 / 644 / 980 |

These include 1,024 consecutive sequence steps and 1,027 cases supplied with
mutating service scripts; those are overlapping subsets, not extra comparisons
or proof of actual persistence. Checks compare all previously mapped bytes,
the sparse scene/chain/effect fields, binding results and ordered semantic
arguments plus state at every external boundary.

All **210 new decoded instructions** were visited. This run visited **504 of
522 combined instructions**, not all combined paths. The unchanged earlier
components retain their separate reports. All eleven remaining external service
boundaries were exercised. Twenty-one focused interpreter tests, 41 invalid-API
checks and four hand-calculated C checks for extreme scene counters passed.
The differential scene cases cover all availability masks, bounded magnitudes
through 64, no-current states, and extreme counters with no active scenes. Huge
active-scene counters are not claimed as full instruction-loop comparisons.

The combined host library builds with warnings as errors and UBSan. The new
pi32v2 relocatable object is 2,280 bytes; file size is not linked firmware size or
a runtime resource measurement. None of these objects has run on a pedal. There
is no new physical control, audio, persistence, DSP application or IRQ test.

## Reproduce and continue

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows, the builder runs through WSL Ubuntu:

```powershell
python -B tools/build_selection.py --output build/reverse-selection-new
```

Optionally supply `--mini-image` with the released `hyperrig-mini-v4.app.bin`
inside the workspace. Only the reviewed hash is accepted. Outputs include the
host library, three target objects, `verification.json` with source hashes and
`build-manifest.json`. Existing directories/reports are refused. Generated
artifacts remain outside Git. The completed run is `build/reverse-selection-01`.

Availability/cache validation is now covered by the
[preset storage extension](PRESET_STORAGE_RECONSTRUCTION.md). Next, reconstruct
preset preflight, version conversion and loading contracts, then connect their
results to scene/DSP application. The [roadmap](REVERSE_ROADMAP.md)
also retains scheduler/LED tracing and the eventual three-switch bank integration.
