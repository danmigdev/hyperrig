# Reverse engineering roadmap

Priority agreed on 16 November 2026: reconstruct firmware modules and their
interfaces so that future backports can be integrated through understandable,
testable source code. Installer feature work follows this effort; installation
regressions and data-loss bugs still receive immediate attention.

The published MINI firmware remains the working reference. A new reconstruction
does not replace it until integration and physical tests have passed. Complete
original firmware C sources have not been recovered.

## Current foundation

| Area | What is available | What it establishes |
| --- | --- | --- |
| Images and formats | Pinned originals, SFC/JLFS/FWSC decoding, A2L1 parser and memory maps | Repeatable access to the original bytes and their address spaces. |
| A2 DSP | Compilable three-channel int32 engine and 7,509 instruction-level comparisons | Equivalence within the documented DSP domain, not complete firmware equivalence. |
| MINI port | Working binary port with explicit board patches and v4 release input hashes | A reference that can be retained while modules are reconstructed. |
| Switch transition core | Two functions recovered in C; 15,520 comparisons against original instructions | Raw transitions, immediate-action policy and emitted event boundaries, with all 119 decoded instructions visited. |
| Action dispatch and timers | Dispatcher, timer worker and clock helper recovered; 10,101 further comparisons | Event generation through action selection, with all 312 combined decoded instructions visited; downstream services remain explicit boundaries. |
| Preset/scene/effect selection | Nine more functions recovered; 14,631 further comparisons | Preset search and load-outcome handling, active-scene selection and effect binding across two chains; all 210 new instructions visited. Storage/loading and DSP application remain external. |
| Preset availability and record validation | Seven more functions recovered; 2,312 further comparisons | Address mapping, header/CRC checks, cache behavior and shared record reading integrated with navigation; all 177 new instructions visited. Physical I/O, preparation and preset decoding/loading remain external. |
| Preset preflight and conversion | Three more functions recovered; 1,754 further comparisons | Two legacy layout migrations, effect IDs 6/24 and their parameter conversion, with all 204 new instructions visited. Loader orchestration and DSP application remain external. |
| Preset loader, bindings and reports | Eight more functions recovered; 4,635 further comparisons | Controls now reach availability, preflight and loader commit/rebind/report sequencing; all 227 new instructions visited. The application handler remains a scripted boundary. |

See [native DSP reconstruction](NATIVE_RECONSTRUCTION.md),
[control reconstruction](CONTROL_RECONSTRUCTION.md),
[action dispatch and timers](CONTROL_ACTIONS.md),
[selection reconstruction](SELECTION_RECONSTRUCTION.md),
[preset storage validation](PRESET_STORAGE_RECONSTRUCTION.md),
[preset preflight and conversion](PRESET_PREFLIGHT_RECONSTRUCTION.md) and
[preset loader, bindings and reports](PRESET_LOADER_RECONSTRUCTION.md) for exact evidence and limits.

## Order of work

| Stage | Scope | Completion criterion |
| --- | --- | --- |
| R1. Controls and action dispatch | Physical-to-logical mapping, press/release state, timers, action records, preset/scene selection and LED state inputs | Transition, timer, action selection and preset/scene/effect binding baselines are verified within stated boundaries. Scheduler/time units, remaining leaf services and physical LED behavior still need tracing/integration. |
| R2. Protocol and persistence | Command parsing and dispatch, preset/scene serialization, versioning, CRCs and storage interfaces | Commands map to named handlers; synthetic round trips and failure cases preserve the original format and distinguish acknowledgments from durable state. |
| R3. Audio integration and remaining DSP | Frontend scaling, effect/routing state, IR processing, memory ownership and audio scheduling | Each reconstructed component has explicit sample formats, numerical/behavioral comparisons and resource budgets. Existing A2 work is reused. |
| R4. Integration and backports | Link reconstructed modules to the MINI adaptation layer; introduce requested feature changes | Build an isolated candidate, prove its intended change and preservation of unrelated behavior, then test on the pedal before release. |

R4 proceeds incrementally as individual modules become ready. It does not require
waiting for complete firmware recovery. A three-switch bank implementation must
change and verify the relevant firmware behavior; relabeling the editor is not
its completion criterion.

## Work product for each module

1. Identify the exact upstream image/version and function byte hashes.
2. Map entry points, callers, structures, external calls and state ownership.
3. Recover compilable C with original notices and explicit API differences.
4. Compare against original instructions, including boundary values, state
   transitions, errors and preserved memory. Record unresolved dependencies.
5. Compile for the host and pi32v2. Keep relocatable objects distinct from
   bootable firmware and target execution distinct from host verification.
6. Integrate a specific backport only after establishing the baseline, then
   verify it offline and on the device with a recovery plan appropriate to it.

Recovered names are interpretations, not original symbols. Decompiled pseudocode,
compilable reconstruction, host comparison, target execution and complete product
validation are separate statuses. No percentage of total source recovery is
claimed without a defensible function inventory.

## Next concrete milestone

The executable C model now connects controls/selection, preset availability,
record validation, legacy conversion and loader commit/binding/report behavior.
The application handler at `0x020092fa` remains external. A zero loader result
does not establish successful DSP application or persistence. See the
[documented offline boundary](PRESET_LOADER_RECONSTRUCTION.md).

Continue into preset storage and application contracts:

- `0x020092fa`: application of the converted working buffer and the meanings
  of its result and output pointers. Split asset loading, working-to-live state
  conversion and effect/routing dependencies into bounded components.
- `0x020031d4`: storage discovery/preparation and cache invalidation. Map the
  writers of state words 708/732 and the pair mapping at offset 3476.
- `0x0200a1d6`: bridge selected scenes into their DSP application dependencies.
- State word 4092 and global calibration word 44: trace writers and clock
  configuration before assigning physical meanings to load-report arithmetic.

Start with the application handler's asset-loading and state-conversion
dependencies as the next bounded component.
The read wrapper at `0x02002810`, its physical I/O and the priority/poll helpers
also remain external. Scheduler and counter tracing remain prerequisites for
physical time-unit claims; LED behavior remains unqualified. Enabling
Footswitches or Stage and changing the four-slot bank grouping to three also
require integration and physical validation.
The Alpha 13 branch remains a placeholder pending an explicit implementation request.
