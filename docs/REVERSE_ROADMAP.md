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
| Native capture warm-up | One new function region; 216 further comparisons | Real four-frame numerical layer calls, history replication, optional pre-head output and reset fallback; 117/118 new instructions visited. One synthetic dispatch-only case is identified separately. |
| Startup input and four-section sample path | Six new function regions; 1,914 further comparisons | Both cached/input bodies, real startup without scripted services, transition copies, Q28 processing and signed gain ramp; all 335 new instructions visited. Transition-request producer and enclosing audio task remain open. |
| Loaded capture through warm-up and processing | Existing bodies joined; 695 further comparisons | Exact native context and history carried through numerical execution, including parser-sized small head rings, stored-slot reuse and real recovery. Coverage is 3,300/3,670 joined instructions; no new function entries or audio-task claim. |
| Four-section parameter transitions | Two new function regions; 1,812 further comparisons | Real clamping and requests generate staged coefficients/gain, then execute update and sample processing. All 122 new instructions visited, including one-step zero deltas and full 1,020-step convergence; the optional notification callback remains external. |
| IR convolution construction | Fourteen new function regions; 479 further comparisons | Actual resampling, windowing, complex FFT, real-spectrum conversion, quantization and object publication through 32 partitions. Coverage is 799/800 new instructions; runtime convolution and accelerator paths remain open. |
| Complete preset application | Seven new function regions; 1,775 further comparisons | Whole reuse/rebuild caller, actual asset/header/query helpers, independent capture/IR statuses and effect failure count. All 928 new instructions visited; downstream effects, capture/IR application and scheduling remain explicit services in this corpus. |
| Dynamics sample processing | Five new function regions; 756 further comparisons | Configuration/startup through actual 128-sample numerical processing, reset, cloning and both meter-updating callers. All 515 new instructions visited, including raw integer extremes and carried histories. |
| Complete audio task and helpers | Six new function regions; 317 further comparisons | All 1,399 new instructions visited through queue/wait/fatal boundaries, recording FIR, real filters, dynamics and capture warm-up on shared RAM. The original task never returns; asynchronous capture, other sample services and platform callbacks remain explicit dependencies. |
| IR runtime convolution | Sixteen new function regions; 399 further comparisons | Real constructor objects through software integer FFT, cyclic partition MAC, inverse/output stages and gains. All 2,266 new instructions visited; accelerator control uses explicitly simulated registers and transform output. |
| Installed transition notification | One new function region; 918 further comparisons | Original signed division/clamp and gain mixing through borrowed-state requests; all nine new instructions visited, with 302 installed callbacks and explicit alternate callback services. |
| Complete scene application | Three new function regions; 561 further comparisons | Direct/pending selection through both application passes, retries, failure accounting, actual transitions and report packing. All 370 new and 517 declared instructions visited; effect services remain explicit. |
| Asynchronous capture and worker | Four new function regions; 137 further comparisons | Shared-state wrapper/worker and numerical processing through the audio task, exact timeout/fallback replay and accelerator descriptors. All 550 new instructions visited; scheduling and accelerator completion remain controlled fixtures. |
| DSP stage and routing | Sixteen new function regions; 806 further comparisons | Automation, route masks, branch alignment/filtering, stereo mixing and real audio-task entries. Coverage is 1,996/2,003 new instructions; seven empty-group gaps are classified by entry invariants. Effect wrappers remain external. |
| Effect resampling | Six new function regions; 1,563 further comparisons | Actual up/down wrappers and four kernels, clipping, retained history and selector-dependent tap counts. All 612 instructions visited. |
| Effect enable and fades | Thirteen new function regions; 2,941 further comparisons | Immediate enable, fade state, installed clear callback, memory fill and IR reset. Coverage is 364/365 new instructions; one redundant instruction remains excluded by its entry invariant. |
| Parameter support | Nineteen new function regions; 4,250 further comparisons | Packing with aliases, selectors, tempo, size, overlapping memory moves and signed/unsigned division. All 449 new instructions visited. |
| Effect processing callers | Sixteen new function regions; 4,664 further comparisons | Dispatcher, individual/group processing, timing and numerical helpers through actual resampling, IR, stage and audio-task bodies. Coverage is 4,218/4,223 new instructions; five invariant gaps remain explicit. Effect-specific numerical leaves remain services. |
| Parameter changes and automation | Seven new function regions; 5,679 further comparisons | Immediate update, record producer, classifiers, wrapper and resource probe through actual scene/stage bodies. Coverage is 993/994 new instructions; one redundant type test remains unexecuted. Construction and allocation remain explicit mutable services. |
| Parameter resources | Nineteen new function regions; 2,850 further comparisons | Actual allocation/recovery, packed-history migration, fingerprints, mode changes and IR length selection. All 579 new instructions visited; eight inherited gaps are classified by caller invariants. Allocator internals and complete slot removal remain services; the preceding parameter corpus is unchanged. |
| Effect construction | Fourteen new function regions; 3,270 further comparisons | Main constructor, type-26 builder and mathematical/selector helpers. All 1,242 new instructions visited. Six larger builders remain services; the 72 parameter-caller fixtures use an explicitly restricted test bridge. |
| Parameter/resource integration | Existing bodies joined; 1,293 further comparisons | All nineteen direct resource call sites execute through the real parameter callers, including allocation recovery and history migration. Coverage is 1,334/1,573 joined instructions; no new original function. Indirect callback collisions and the allocation flag's borrowed lifetime are compared. |
| All-pass, gate and state-variable filter | Three new function regions; 555 further comparisons | All 708 new instructions visited through direct kernels, dispatch, real resampling, stage and carried audio-task observations. Native raw-count behavior and exact budget-stop prefixes are preserved. Constructor-produced parameters are a separate integration boundary. |
| Effect routing and ownership | Eight new function regions; 1,536 further comparisons | Route lookup/repair, group counting, buffer release and complete slot teardown. All 236 new and 264 loaded instructions visited; twenty fourth-read prefixes preserve prior writes and callbacks. Allocator/free effects and global refresh remain explicit. |
| Resource/ownership integration | Existing bodies joined; 1,284 further comparisons | Actual slot removal through resource flush, retry and parameter/scene/stage callers. All nineteen direct resource sites and the flush-to-removal edge execute. Coverage is 1,476/1,732 joined instructions; 35 fourth-read prefixes preserve nested state, including the scene busy flag. |
| Constructor-to-signal integration | Existing bodies joined; 681 further comparisons | Types 1, 13 and 38 carry actual constructor output into numerical kernels, stage and carried audio observations on 142 retained-allocation chains. Preparation is a separate synchronous invocation; no scheduler or new native call edge is claimed. |
| IR effect lifecycle | Nine new function regions; 808 further comparisons | Source/mode selection, temporary buffers, assignment and rollback, ownership query, copy wrapper and relocation. All 422 new and 537 loaded instructions visited, including full signed metadata and overlapping copies. Real prepare/construct bodies remain a separate integration boundary. |
| Effect model construction | 49 new function regions; 1,657 further comparisons | All six main-constructor numerical builder dependencies now execute recovered arithmetic. Coverage is 3,076/3,081 new and 3,441/4,775 loaded instructions; five static gaps remain explicit. Native aliases, sparse coefficient reads, object layouts and carried updates are compared. |
| Preset storage preparation | Eleven new function regions; 217 further comparisons | Discovery, pair replacement, record writes and header edits preserve original ordering and callback aliases. Coverage is 675/677 new and 938/940 loaded instructions, with two static gaps. Preparation changes block/pair metadata without directly writing availability masks; physical storage remains external. |
| IR numerical integration | Existing bodies joined; 128 further comparisons | Actual preparation and copy-construction sites execute recovered numerical code with native aliases, count arithmetic and retained allocation chains. Coverage is 1,418/1,453 loaded instructions; 35 inherited gaps remain explicit. No new function or data exclusion. |
| Parameter-constructor integration | Existing bodies joined; 625 further comparisons | Three direct sites execute the recovered constructor/model closure through parameter, resource, ownership and scene/stage callers. Temporary copies retain live object aliases. Coverage is 5,741/6,507 joined and 7,469/20,072 loaded instructions; all gaps remain explicit. No new function or data exclusion. |
| Storage control | 45 new function regions; 626 further comparisons | Actual read/program/control wrappers and command, status and cache bodies retain raw counts and native error ordering. Coverage is 1,164/1,165 instructions; the fatal loop is observed before execution, and full polling timeout outcomes remain unexecuted. MMIO and platform services use synthetic observations. |
| Storage coordination | Nine new function regions; 442 further comparisons | Timing gates, notification records, IRQ nesting and lock loops preserve raw counter/core arithmetic and callback-visible state. All 178 new and 184 combined instructions are visited. CPU events and clock/wait/poll services remain explicit observations; no hardware atomicity or IRQ-delivery claim. |
| Effect sample processing | Seven new function regions; 768 further comparisons | Ten dispatcher sites execute the actual cascade, mixer, width, ring/correlation and transition bodies. Types 25, 36 and 37 carry real constructor state through 432 retained allocation chains. Coverage is 1,304/1,324 new and 4,469/22,919 loaded instructions; twenty full-entry invariant gaps remain explicit. |
| Storage runtime integration | 75 existing bodies joined; 135 further comparisons | All eighteen original preparation-to-control/coordination sites execute on shared state. Private payload leases, actual-store initialization and first-fault ordering are preserved, including 66 matched failure prefixes. Coverage is 1,701/2,283 loaded instructions; no new function or data exclusion. Physical flash and scheduling remain external. |
| Effect creation, allocation and tempo | 45 new complete bodies; 4,229 further comparisons | Ten original joins execute recovered parameter, constructor and IR callees on shared RAM. Allocation failures, callback changes, raw segment indices and cost arithmetic retain native ordering. Coverage is 1,758/1,759 new and 8,518/22,289 loaded instructions; one fixed-input saturation assignment remains unexecuted. Preset callers and hardware execution remain separate work. |

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
[IR installation](IR_INSTALLATION_RECONSTRUCTION.md),
[capture warm-up](CAPTURE_WARMUP_RECONSTRUCTION.md) and
[startup input/four-section processing](DSP_AUDIO_PATH_RECONSTRUCTION.md) and
[live capture processing](CAPTURE_LIVE_RECONSTRUCTION.md) and
[parameter transitions](DSP_TRANSITION_RECONSTRUCTION.md) and
[IR convolution construction](IR_CONVOLUTION_RECONSTRUCTION.md),
[IR runtime convolution](IR_PROCESSING_RECONSTRUCTION.md),
[preset application](PRESET_APPLICATION_RECONSTRUCTION.md),
[dynamics sample processing](DSP_DYNAMICS_PROCESSING_RECONSTRUCTION.md) and
[the complete audio task](AUDIO_TASK_RECONSTRUCTION.md),
[installed transition notification](DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md),
[scene application](SCENE_APPLICATION_RECONSTRUCTION.md),
[asynchronous capture](CAPTURE_ASYNC_RECONSTRUCTION.md),
[DSP stage/routing](DSP_STAGE_RECONSTRUCTION.md),
[effect resampling](EFFECT_RESAMPLING_RECONSTRUCTION.md),
[effect enable/fades](EFFECT_ENABLE_RECONSTRUCTION.md),
[parameter support](EFFECT_PARAMETER_SUPPORT_RECONSTRUCTION.md),
[effect processing callers](EFFECT_PROCESSING_RECONSTRUCTION.md) and
[parameter updates](EFFECT_PARAMETERS_RECONSTRUCTION.md) and
[parameter resources](EFFECT_PARAMETER_RESOURCES_RECONSTRUCTION.md),
[effect construction](EFFECT_CONSTRUCTION_RECONSTRUCTION.md),
[parameter/resource integration](EFFECT_PARAMETER_LIFECYCLE_RECONSTRUCTION.md),
[signal kernels](EFFECT_SIGNAL_RECONSTRUCTION.md),
[effect ownership](EFFECT_OWNERSHIP_RECONSTRUCTION.md),
[resource/ownership integration](EFFECT_RESOURCE_OWNERSHIP_RECONSTRUCTION.md),
[constructor-to-signal integration](EFFECT_CONFIGURED_SIGNAL_RECONSTRUCTION.md),
[IR effect lifecycle](IR_EFFECT_LIFECYCLE_RECONSTRUCTION.md),
[effect model construction](EFFECT_MODEL_CONSTRUCTION_RECONSTRUCTION.md),
[preset storage preparation](PRESET_STORAGE_PREPARATION_RECONSTRUCTION.md),
[IR numerical integration](IR_EFFECT_NUMERICAL_RECONSTRUCTION.md),
[parameter-constructor integration](EFFECT_PARAMETER_CONSTRUCTION_RECONSTRUCTION.md),
[storage control](STORAGE_CONTROL_RECONSTRUCTION.md),
[storage coordination](STORAGE_COORDINATION_RECONSTRUCTION.md),
[effect sample processing](EFFECT_SAMPLE_PROCESSING_RECONSTRUCTION.md),
[storage runtime integration](STORAGE_RUNTIME_RECONSTRUCTION.md) and
[effect setup](EFFECT_SETUP_RECONSTRUCTION.md) for exact
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

The current verified components recover the effect dispatcher and individual/group
callers, actual resampling, enable/fade handling, parameter production and
consumption, resource management, the main effect constructor, three more
numerical engines and effect cleanup. The table above and linked module reports
record their exact comparison domains. Earlier notes that listed these bodies as tracing-only work
are superseded by that evidence.

The resource/ownership join and constructor-to-signal handoff are now verified
within their documented domains. These integrations preserve the borrowed
allocation flag, callback order and actual coefficient/history state. The
ownership guard also propagates through the scene before its cached busy-byte
write. Broader fault prefixes inside inherited transition helpers remain open.
The 49-body model reconstruction covers all six previously explicit constructor
builders and their numerical/layout dependencies. Its corpus retains five static
instruction gaps and does not establish every effect's sample processing.
IR lifecycle preparation and copy construction now execute recovered numerical
bodies at all three direct sites, including the mode-zero retry. The integration
retains native aliases, producer callbacks and wrapped count arithmetic. Its
35 inherited instruction gaps and C-only guards remain separately documented.
Parameter construction now joins the actual live-record, temporary-record and
object-builder calls. The corpus carries constructor output through resource
ownership and scene/stage callers, including live pointed-object aliases and
the established ownership failure prefix. Arbitrary constructor guard prefixes
and the remaining effect sample algorithms still require separate evidence.
Storage read, program and control wrappers now execute their recovered device
commands in the standalone comparison corpus. MMIO, cache/barrier events, IRQ
registration, scheduling and cross-core services remain explicit boundaries.
The runtime integration covers eighteen preparation/controller joins; further
caller and platform integration remains open.
Coordination now supplies the timing gates, notification ring, IRQ-nesting
counters and lock loops. The three rate-helper calls execute the existing body.
Initial IRQ words remain mutable runtime state, and synthetic CLI/STI/TESTSET
observations do not establish physical interrupt delivery or atomicity.

The immediate work is to connect more recovered pieces while preserving the
original call sites, memory ownership and callback order:

1. Join the recovered effect creation/setup at `0x0202e710` and global tempo
   propagation at `0x0202f46c` to their actual preset-application callers.
   The setup module now executes allocation, resource, parameter, constructor
   and IR paths. Preserve shared byte storage, callback changes, failure
   effects and every original caller site when connecting the parent.
2. Recover the remaining effect sample-processing algorithms and their
   numerical dependencies, including the complete type-29 engine and public
   chunk wrapper. The seven recovered type-25/36/37 numerical bodies now join
   ten actual dispatcher sites. Keep remaining algorithms visible in the
   [dependency inventory](REVERSE_INVENTORY.md).
3. Carry more constructor branches through their actual numerical consumers,
   then join those paths to parameter/resource ownership. The completed
   synchronous preparation handoff covers types 1, 13, 25, 36, 37 and 38; it does not
   establish scheduling, concurrent state changes or every effect algorithm.
4. Recover remaining storage platform services for clocks, interrupt
   registration, critical sections and peer coordination. Preparation now
   executes the recovered controller and coordination bodies at all eighteen
   original sites, with private leases restricted to actual internal payload
   accesses. Further joins must preserve CPU/MMIO ordering, raw counters and
   failure effects; synthetic bus observations do not establish physical
   flash durability or interrupt scheduling.

The full reverse-engineering objective also requires these broader areas:

- Complete protocol, command and persistent-state coverage. Discovery at
  `0x020031d4` and pair replacement at `0x02003040` now have complete bodies:
  they update flags 712/716 and block/pair metadata, with no direct store to
  availability masks 708/732. The recovered invalidator clears mask 708;
  validation updates both masks. Trace the remaining command writer/invalidation
  sequences. Read/write/erase bodies at `0x02002810`, `0x02002ef2` and
  `0x02002b80` now have standalone comparison evidence. Their caller integration,
  remaining platform/coordination helpers and power-loss behavior remain open.
- Complete IR, capture and preset application through their actual ownership
  and scheduling callers. IR mode selection, copy wrapper, relocation,
  temporary-state paths and effect refresh now have complete reconstructed
  bodies, and their numerical preparation/copy-construction join is now verified
  within its documented domain. Wider ownership and scheduling integration
  remains open. Recovered runtime convolution already executes through the effect
  dispatcher; accelerator MMIO and transform behavior are still simulated.
- Recover remaining input/output, USB, scheduler, clock and control services.
  Trace state word 4092, calibration word 44, and their writers before assigning
  physical time or sample-rate meanings. Existing 48000/48077 arithmetic evidence
  does not establish a measured physical rate. LED and physical control behavior
  remain unqualified.
- Finish the executable entry/dependency inventory, including callbacks,
  interrupts and code/data boundaries. The candidate-entry union is not a
  complete function denominator or a completion percentage.
- Produce a complete reproducible source build and integrated comparison path.
  Some older composed verifiers obtain transitive source lists from earlier
  ignored reports, including native capture loading and IR installation. Remove
  that dependency or explicitly regenerate and verify every prerequisite. Newer
  module builders enumerate their own source inputs, but still require the
  pinned original images and local toolchain. Target objects are not a bootable
  reconstructed firmware image.

The reserved Alpha 13, Tone3000, zoom and parity branches remain future work.
This goal continues the pinned Alpha 11 reconstruction; product backports and
physical validation require their own implementation and qualification evidence.
