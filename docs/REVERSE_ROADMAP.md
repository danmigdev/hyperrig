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

See [native DSP reconstruction](NATIVE_RECONSTRUCTION.md) and
[control reconstruction](CONTROL_RECONSTRUCTION.md) for exact evidence and limits.

## Order of work

| Stage | Scope | Completion criterion |
| --- | --- | --- |
| R1. Controls and action dispatch | Physical-to-logical mapping, press/release state, timers, action records, preset/scene selection and LED state inputs | Documented state/ABI contracts and C functions compared against original instructions. The transition core is complete within its stated boundary; the action executor and timer worker are next. |
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

Continue from the recovered transition function at `0x02014c04` into:

- `0x020149b6`: action dispatcher entry, currently a recorded external boundary.
- `0x02014b3c`: timer-worker entry called by the panel loop; reconstruct its
  timing/state contract before assigning physical time units to counters.
- The original nine-byte per-switch action records beginning at
  `0x01c1f180 + 236`, and their downstream preset/scene/effect handlers.

The immediate deliverable is an executable control-state model and C source
covering event generation through action selection. Enabling Footswitches or
Stage and releasing a three-slot firmware bank change come after that baseline
and its physical validation.
