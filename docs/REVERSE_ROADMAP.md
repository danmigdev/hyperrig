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
| Asset checks and application layout | Nine dependencies recovered; 3,938 further comparisons | Dual-format headers, extended identities/trailers, reuse descriptors and legacy/modern routing metadata; all 189 new instructions visited. Asset payload loading and the application caller remain external. |
| Shared Q28 recursive filters | Two kernels recovered; 1,864 further comparisons | Fixed rounding and fractional residue variants, including clipping, wraparound and persistent history; all 346 instructions visited. Complete effects remain external; coefficient generation is covered separately below. |
| IR loading and ownership | Five functions recovered; 541 further comparisons | Reuse, complete record/CRC checks up to 8152 bytes, buffer transfer and pending-slot refresh; all 229 new instructions visited. Allocator, locking and DSP service implementations remain external. |
| Five-section DSP chain | Two functions recovered; 2,445 further comparisons | Staged coefficient/flag updates, history retention, both numerical kernels and timing accounting; all 172 new and 518 combined instructions visited. The coefficient generator is covered separately below. |
| Capture loading and gain metadata | Ten functions recovered; 6,091 further comparisons | Packed metadata, gain table/mixing, signature rejection, reuse and partial rollback; all 307 new instructions visited. Journal and container orchestration are covered by later milestones below. |
| Coefficient staging and conversion | Five executed regions; 11,071 further instruction comparisons and 6,912 binary32 division checks | Request clamping/publication, producer argument setup, normalization and Q28 conversion; all 97 scoped instructions visited. The bounded generator below supplies the mathematical producer. |
| Capture container installation and reader | Two functions recovered; 262 further comparisons | Actual record/CRC/identity reader, allocation ownership, cleanup and mode/priority restoration, integrated with slot loading; all 229 new instructions visited. Parser/DSP/platform bodies remain external. |
| Capture journal and cache | Six regions recovered; 9,764 further comparisons | Last-valid-record selection, read-error fallback, cache reuse and forced scans; all 180 new instructions visited. Journal writes are covered separately below; physical reads remain external. |
| Bounded coefficient generator | Six regions recovered; 5,542 instruction comparisons and 18,069 binary32 arithmetic checks | All mathematical dependencies execute through staging, including 2,714 raw coefficient comparisons; all 190 new and 287 combined instructions visited. Pipeline integration is covered below. |
| Capture DSP dispatch | Eight functions and four RTS-only helpers; 1,847 further comparisons | Preparation, size/probe, DSP-load wrappers, capability query and recovery execute through container/slot loading; all 254 new instructions visited. Raw parser, memory reset and platform bodies remain external. |
| Journal append and rewrite | Six function regions and two command fragments; 655 further comparisons | Cache invalidation, page-write/erase wrappers, bounded append retries and complete rewrite/readback helper; all 302 new instructions visited. Complete command and physical storage remain external. |
| Generated-coefficient filter pipeline | One new getter and integration of earlier DSP modules; 1,698 further comparisons | Real generation/staging through both sample kernels with carried state; all 812 combined instructions visited. Reset divisor 48000 and guarded startup argument 48077 are pinned static evidence, not measured physical rates. |
| Whole native capture parser | Complete parser and read64 helper; 424 further comparisons | Native context/arena layout, error ordering, partial writes and reset-copy configuration; 1,136/1,213 instructions visited, with all 77 gaps classified by entry invariants. No history reset or audio processing in this module. |
| Capture memory reset | Complete reset function and new load/container adapters; 253 further comparisons | All 84 new instructions visited, with 62,562 ordered zero-word writes compared. Parser remains external in this adapter's corpus. |
| Complete capture metadata command | Nine new function regions; 1,114 further comparisons | Parsing, packing, allocation/reload, append/rewrite retries, cleanup and current-slot gain. All 399 command instructions visited; 14 helper instructions outside the stated domain remain unvisited. Physical storage and output services are boundaries. |
| DSP initialization and guarded startup | Eight new function regions; 4,529 further comparisons | All 220 new instructions visited, including resets, second coefficient table, initializer and guarded startup through the real mathematical producer. Two service bodies and surrounding audio scheduling remain external. |
| Integrated native capture loading | Existing bodies joined; 273 further comparisons | Actual parser/reset through size, load, recovery, container and stored-slot paths; 460 parser entries and 354 resets. Integration coverage is 1,410/1,551 joined instructions and adds no function entries. |
| Native capture processing | Six new function regions; 230 further comparisons | Rechannel, layer dispatch, iteration, head setup, block processing and zero helper; 323 actual numerical calls, with seven scripted dispatch cases reported separately. Coverage is 464/465 new instructions; warm-up remains open. |
| Dynamics configuration and startup | Three new function regions; 2,930 further comparisons | Real dynamics math/getters through guarded startup; 72/73 new instructions, with the remaining threshold branch excluded by all 201 clamped values. Platform input and sample processing remain open. |
| IR installation and stored reads | Ten new function regions; 1,143 further comparisons | Gain, tail trimming, length selection, direct/deferred installation and real read/CRC callback through ownership paths; all 267 new instructions visited. Convolution construction and processing remain open. |

See [native DSP reconstruction](NATIVE_RECONSTRUCTION.md),
[control reconstruction](CONTROL_RECONSTRUCTION.md),
[action dispatch and timers](CONTROL_ACTIONS.md),
[selection reconstruction](SELECTION_RECONSTRUCTION.md),
[preset storage validation](PRESET_STORAGE_RECONSTRUCTION.md),
[preset preflight and conversion](PRESET_PREFLIGHT_RECONSTRUCTION.md),
[preset loader, bindings and reports](PRESET_LOADER_RECONSTRUCTION.md),
[asset/application dependencies](PRESET_ASSETS_RECONSTRUCTION.md),
[recursive DSP filters](BIQUAD_RECONSTRUCTION.md),
[IR loading and ownership](IR_LOADER_RECONSTRUCTION.md),
[the five-section DSP chain](BIQUAD_CHAIN_RECONSTRUCTION.md),
[capture loading and gain metadata](CAPTURE_LOADER_RECONSTRUCTION.md),
[coefficient staging/conversion](BIQUAD_COEFFICIENT_RECONSTRUCTION.md),
[capture container installation](CAPTURE_CONTAINER_RECONSTRUCTION.md),
[capture journal/cache](CAPTURE_METADATA_RECONSTRUCTION.md),
[bounded coefficient generation](BIQUAD_GENERATOR_RECONSTRUCTION.md),
[capture DSP dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md),
[journal writes and verification](CAPTURE_JOURNAL_RECONSTRUCTION.md),
[the integrated filter pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md),
[the whole native capture parser](CAPTURE_PARSER_RECONSTRUCTION.md),
[capture memory reset](CAPTURE_RESET_RECONSTRUCTION.md),
[the complete metadata command](CAPTURE_COMMAND_RECONSTRUCTION.md) and
[DSP initialization](DSP_INITIALIZATION_RECONSTRUCTION.md),
[integrated native loading](CAPTURE_NATIVE_RECONSTRUCTION.md),
[native capture processing](CAPTURE_PROCESSING_RECONSTRUCTION.md),
[dynamics configuration](DSP_DYNAMICS_RECONSTRUCTION.md) and
[IR installation](IR_INSTALLATION_RECONSTRUCTION.md) for exact
evidence and limits. The [inventory](REVERSE_INVENTORY.md) records reconstructed
regions separately from unresolved candidates; it does not use candidate counts
as a completion denominator.

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

## Reserved branches

These branches reserve future work. Creation does not imply implementation or
feature validation; the three newer branches start from `20fe29d`.

| Branch | Intended scope |
| --- | --- |
| `backport/ultrarig-alpha13` | Placeholder for the announced Alpha 13 backport; implementation is deferred. |
| `feature/tone3000-integration` | Future Tone3000 integration. |
| `feature/zoomable-ui` | Future UI zoom support. |
| `comparison/ultrarig-alpha11-parity` | Compare all UltraRig Alpha 11 features with HyperRig after complete reverse engineering. |

## Next concrete milestone

The executable C model now connects controls/selection, preset availability,
record validation, legacy conversion and loader commit/binding/report behavior.
The application handler at `0x020092fa` remains external. A zero loader result
does not establish successful DSP application or persistence. See the
[documented offline boundary](PRESET_LOADER_RECONSTRUCTION.md).
Its asset-header/identity, reuse-descriptor and routing-layout dependencies now
have independent C/instruction comparisons. The IR loader now executes those
metadata/record dependencies and the ownership sequence, with explicit allocator
and DSP service boundaries. In parallel, the five-section DSP caller now executes
both Q28 kernels and preserves their live history during staged updates.
Capture loading now executes the container installer and record reader, including
ownership, mode restoration and the original partial rollback. Journal/cache
reading has an independent verified component, ready to join that path. Capture
dispatch now executes preparation, sizing, DSP-load wrappers, capability queries
and cleanup. The bounded coefficient generator executes through staging and the
active five-section chain with carried sample/history state. Journal writes,
erase orchestration, append retries and rewrite/readback now have a separate
synthetic-storage comparison.
The whole native parser and its read64 helper now have separate complete-body
comparisons, including the native allocation layout and partial failures. Reset
executes through new container/slot adapters. The complete metadata command now
connects parsing and packing through reload/retries to active gain changes. DSP
initialization and guarded startup execute the recovered coefficient producer.
Native loading now executes the complete parser/reset in that caller chain.
Separately, native block processing executes its actual numerical kernels,
including the final one-frame output ring. Dynamics configuration now executes
inside startup, and IR load/attach/refresh now execute the recovered installation,
gain/trimming and read/CRC bodies.

Continue into preset storage and application contracts:

- `0x020092fa`: application of the converted working buffer and the meanings
  of its result and output pointers. Slot loading, container orchestration and
  its reader, dispatch, raw parser and memory reset now execute together. Carry
  that native context and history into the recovered block processor, add warm-up
  `0x01c12f20..0x01c13072`, then join journal/cache and effect-state reuse/routing.
  The portable engine remains separate evidence.
- Metadata persistence: connect the complete `0x0200a888` command to its protocol
  dispatcher and reporting bodies. Allocation/reload/retry, lookup and active
  gain handling are now reconstructed within the command's bounded service domain.
  Physical write/read/erase drivers and power-loss behavior remain open.
- IR convolution construction at `0x0202962a`, size helper `0x01c123fa`,
  constructor `0x020318a8` and coefficient producer `0x02031542`: recover kernel
  objects, allocation layout and processing. Direct/deferred installation and
  the stored-read callback at `0x0201ad4c` are now reconstructed. Mode selection,
  temporary-state paths and effect refresh remain open.
- `0x020031d4`: storage discovery/preparation and cache invalidation. Map the
  writers of state words 708/732 and the pair mapping at offset 3476.
- `0x0200a1d6`: bridge selected scenes into their DSP application dependencies.
- State word 4092 and global calibration word 44: trace writers and clock
  configuration before assigning physical meanings to load-report arithmetic.

Continue the application path by connecting native capture loading, warm-up and
block processing with carried contexts, scratch and histories. On the DSP path,
recover the remaining startup service at `0x01c010a6`, dynamics sample processing,
the separate four-section processing path and the audio caller around `0x01c026de`.
The broader initializer, its reset helpers and guarded startup now execute in
their comparison model. The normal modeled startup supplies 48077 after the
reset-copy divisor 48000; an exhaustive writer map and physical units remain open.
Establish those units from configuration and hardware evidence before assigning
sample-rate or frequency meanings.
IR convolution and complete effect/routing application remain separate components.
The read wrapper at `0x02002810`, its physical I/O and the priority/poll helpers
also remain external. Scheduler and counter tracing remain prerequisites for
physical time-unit claims; LED behavior remains unqualified. Enabling
Footswitches or Stage and changing the four-slot bank grouping to three also
require integration and physical validation.
Some composed verifiers still obtain transitive source-name lists from earlier
ignored build reports, including native capture loading and IR installation.
Their required inputs are documented in those milestones. A complete clean-build
workflow must remove that dependency or explicitly regenerate and verify every
prerequisite; the current reports do not establish a fresh-checkout build by themselves.
The Alpha 13 branch remains a placeholder pending an explicit implementation request.
