# Reverse engineering inventory

The current audited report set contains **331 reconstructed function regions**.
Five bodies are single RTS instructions; four carry the earlier reports' explicit
return-only annotation, while the asynchronous command no-op is declared as an
ordinary complete function. Four earlier parser/command fragments remain
linked to their complete parent functions as historical evidence; their bytes
and entries are not counted twice. Some complete reconstructed bodies still
have unexecuted instructions, listed below.

A reliable percentage of complete firmware recovery is **not yet available**:
the total function inventory, indirect call graph and division between code and
data remain incomplete. Function counts also do not measure the relative work
needed for small helpers, large parsers, drivers or DSP engines.

The baseline report set associated with commit
`1b235a5a284f100e47c66b6b4ab43c48cdff10cb` contains 88 function regions and two
parser fragments. Snapshot `-03` contains 106 function regions and four separate
fragments after journal, pipeline and dispatch work. Snapshot `-04`
adds DSP initialization, memory reset, the complete capture command and the
complete raw parser with its read helper, reaching 126 function regions. The
`-05` snapshot adds 19 regions for capture processing, dynamics
configuration and IR installation. Its integrated native capture-loading report
joins 15 existing regions and adds no function. Snapshot `-06` adds
23 regions for capture warm-up, the DSP audio path, transition requests and IR
convolution construction. A further integration report carries native loading
through warm-up and numerical processing across 29 existing regions without
adding a function. Snapshot `-07` adds 34 regions for preset
application, dynamics sample processing, IR processing and the complete
nonreturning audio task with its direct helpers. Snapshot `-08` adds
24 regions for scene application, the installed transition notification,
asynchronous capture and DSP stage processing. All 36 selected reports from
`-07` remain selected. Snapshot `-09` adds 61 regions for effect
resampling, enable/fade handling, parameter support, processing callers and
parameter updates. All 40 selected reports from `-08` remain selected. Snapshot
`-10` adds nineteen regions for parameter resources, retaining all 45 reports
from `-09`. The current `-11` snapshot adds 25 regions for effect construction,
three signal kernels and ownership. A separate parameter/resource integration
report adds no function. All 46 reports from `-10` remain selected; every earlier
snapshot remains unchanged.

The original [`inventory_reverse.py`](../tools/inventory_reverse.py) is unchanged.
The unchanged [`inventory_reverse_expanded.py`](../tools/inventory_reverse_expanded.py)
adapter audits the four exact fragment/parent relationships and preserves
module-level instruction gaps. The unchanged
[`inventory_reverse_runtime.py`](../tools/inventory_reverse_runtime.py) adds the
four-byte capture dispatch-table exclusion, validates its instruction targets,
and records joined-corpus coverage without counting the joined functions again.
The unchanged [`inventory_reverse_dsp.py`](../tools/inventory_reverse_dsp.py) adds the
verified 36-byte IR coefficient-table exclusion and describes joined corpora
containing both new and reused functions without treating them as integration-only
evidence. The unchanged
[`inventory_reverse_application.py`](../tools/inventory_reverse_application.py)
binds the exact effect-parameter metadata, accelerator tables and recording FIR
coefficients to their original consumer/caller instructions. It retains all
prior overlap, hash and coverage policies, including the distinction between
bounded executions of a nonreturning task and whole-firmware execution. The unchanged
[`inventory_reverse_stage.py`](../tools/inventory_reverse_stage.py) adds only the
40-byte stage-capability table, bound to both complete consumers and eleven
decoded index/field instructions. The unchanged
[`inventory_reverse_effects.py`](../tools/inventory_reverse_effects.py) adds 18
exact data exclusions from the five new modules and three previously verified
tables, binding each to complete consumers and original index instructions.
Embedded table targets must be decoded packet starts; padding remains distinct
from branch entries. The unchanged
[`inventory_reverse_resources.py`](../tools/inventory_reverse_resources.py)
adds three resource branch-table exclusions bound to two complete consumers,
their decoded index instructions and the frozen resource report. It preserves
all earlier reports and policies. The new
[`inventory_reverse_construction.py`](../tools/inventory_reverse_construction.py)
adds eight exact construction data exclusions and reauthenticates one existing
tempo table, binding five complete consumers and 72 distinct decoded proof sites.
It adapts the constructor report's original-image hash field in memory while
preserving its exact report and manifest bytes.
Generated reports remain outside Git: the unchanged baseline is
`build/reverse-inventory-01/inventory.json`, and the current snapshot is
`build/reverse-inventory-11/inventory.json`. Snapshots `-02` through `-10` are also
preserved. Each manifest records its report hash.
No device access, hardware/audio test, firmware build or installation is performed
by this inventory.

## What is counted

| Evidence class | Meaning | Baseline | Snapshot -03 | Snapshot -04 | Snapshot -05 | Snapshot -06 | Snapshot -07 | Snapshot -08 | Snapshot -09 | Snapshot -10 | Current -11 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Reconstructed function region | An exact original range with compilable C and recorded comparisons within the module's documented domain | 88 | 106 | 126 | 145 | 168 | 202 | 226 | 287 | 306 | 331 |
| Separate parser fragment | Compared parser subsection outside a reconstructed whole parent | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Separate command fragment | Compared command continuation outside a reconstructed whole parent | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Archived contained fragment | Prior fragment evidence inside a complete parent; adds no function or bytes | 0 | 0 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| Explicit return-only annotation | Report marks an exact single-RTS body; included in the function total | 0 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| Distinct active regions | Function regions plus separate fragments, with no overlapping bytes | 90 | 110 | 126 | 145 | 168 | 202 | 226 | 287 | 306 | 331 |
| Partial Ghidra entries | Automatic G v2 labels without a full endpoint inventory or semantic validation | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 |
| Linear direct-call target candidates | Distinct in-range targets after known-data and invalid-target exclusions | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 |
| Combined candidate entries | Union of call targets, partial Ghidra labels, reconstructed entries and reset entry | 2,218 | 2,218 | 2,219 | 2,220 | 2,222 | 2,223 | 2,225 | 2,226 | 2,226 | 2,226 |
| Candidates outside reconstructed regions | Candidate entries without a reconstructed range; **not** confirmed remaining functions | 2,130 | 2,112 | 2,093 | 2,075 | 2,054 | 2,021 | 1,999 | 1,939 | 1,920 | 1,895 |
| Unreconstructed direct dependency targets | Direct callees whose bodies are outside reconstructed ranges | 35 | 40 | 42 | 39 | 38 | 92 | 94 | 121 | 112 | 111 |
| Indirect call sites inside reconstructed regions | Call instructions whose targets require runtime context | 4 | 4 | 4 | 4 | 9 | 13 | 19 | 29 | 32 | 35 |

Candidate categories overlap before taking their union. The 2,226 candidate
entries are **not a denominator for a completion percentage**. Some may be data
decoded as instructions, alternate/internal entry points or duplicate semantic
functions. Other real functions can be absent because they are reached through
callbacks, jump tables, interrupts, indirect calls or entry paths not yet mapped.
An apparent register-save prologue is recorded only as a hint. The
reconstructed decimal core at `0x020283ce` was absent from both the linear
direct-call target set and partial Ghidra export; its reviewed entry added the
new candidate in `-04`. The IR slot-read callback at `0x0201ad4c` adds another in
`-05`, again absent from both older candidate sources. The IR producer callbacks
at `0x02031542` and `0x020315b8` add two more in `-06`. The nonreturning audio-task
entry at `0x01c01e5e` adds another in `-07`; neither older candidate source
identified it. Snapshot `-08` adds the worker at `0x01c04588` and installed
notification at `0x0201a9ea`, also absent from both older candidate sources.
Snapshot `-09` adds the installed clear callback at `0x0201a9dc`, likewise
absent from both older candidate sources. Snapshots `-10` and `-11` add no
candidate entry.
These are concrete
examples of why the candidate count is not a complete function denominator.

The current 331 active ranges span 84,130 original bytes, including 498 bytes
of embedded branch tables/alignment. The tool decodes 27,011 instructions
after excluding those data bytes. The separate
36-byte IR coefficient table, 3,360-byte parameter metadata, 64-byte accelerator
tables, two FIR tables totaling 30 bytes and 40-byte stage-capability table add
no function or reconstructed-code bytes. Snapshot `-09` adds another 458
external data bytes from the new modules and 216 previously verified table
bytes; these likewise add no function or reconstructed-code bytes.
The four archived fragments span 394 bytes already included in their parents.
Snapshot `-10` spans 76,542 bytes and 24,825 instructions, including 414 embedded
data bytes. Snapshot `-11` adds 84 embedded data bytes and 89 external table bytes.
Snapshot `-09` spans 74,872 bytes and 24,246 instructions, including 366 embedded
data bytes. Snapshot `-10` adds 48 embedded data bytes and no external data span.
Snapshot `-08` spans 54,304 bytes and 17,603 instructions.
Snapshot `-07` spans 45,512 bytes and 14,671 instructions; snapshot `-06` spans
28,944 bytes and 9,563 instructions; snapshot `-05` spans
24,810 bytes and 8,188 instructions; snapshot `-04` spans
22,464 bytes and 7,383 instructions; snapshot `-03` spans 16,704 bytes and 5,380
instructions; the baseline
spans 15,176 bytes and 4,838 instructions.
These are inventory counts, not an additional verification run or a claim
that every decoded instruction was visited by one combined test. Coverage and
valid-domain restrictions remain in the individual milestone reports.

## Reconstructed baseline by module

| Module | Function regions | Fragments |
| --- | ---: | ---: |
| [A2 numerical kernels](NATIVE_RECONSTRUCTION.md) | 9 | 2 |
| [Switch transitions](CONTROL_RECONSTRUCTION.md) | 2 | 0 |
| [Action dispatch and timers](CONTROL_ACTIONS.md) | 3 | 0 |
| [Preset, scene and effect selection](SELECTION_RECONSTRUCTION.md) | 9 | 0 |
| [Preset availability and records](PRESET_STORAGE_RECONSTRUCTION.md) | 7 | 0 |
| [Preset preflight and conversion](PRESET_PREFLIGHT_RECONSTRUCTION.md) | 3 | 0 |
| [Preset loader, bindings and reports](PRESET_LOADER_RECONSTRUCTION.md) | 8 | 0 |
| [Preset asset/layout helpers](PRESET_ASSETS_RECONSTRUCTION.md) | 9 | 0 |
| [Q28 filter kernels](BIQUAD_RECONSTRUCTION.md) | 2 | 0 |
| [Filter chain](BIQUAD_CHAIN_RECONSTRUCTION.md) | 2 | 0 |
| [Coefficient staging and normalization](BIQUAD_COEFFICIENT_RECONSTRUCTION.md) | 5 | 0 |
| [Coefficient mathematical generator](BIQUAD_GENERATOR_RECONSTRUCTION.md) | 6 | 0 |
| [Capture loading and gain](CAPTURE_LOADER_RECONSTRUCTION.md) | 10 | 0 |
| [Capture container and reader](CAPTURE_CONTAINER_RECONSTRUCTION.md) | 2 | 0 |
| [Capture metadata lookup](CAPTURE_METADATA_RECONSTRUCTION.md) | 6 | 0 |
| [IR loader and ownership](IR_LOADER_RECONSTRUCTION.md) | 5 | 0 |
| **Total** | **88** | **2** |

The two baseline A2 fragments are bias-conversion subsections at
`0x02032586..0x02032618` and `0x020327de..0x0203280c`. Those fragment reports
alone did not recover the complete parser. The new whole-parser report supplies
that evidence separately. Portable engine orchestration and format parsing do
not add guessed original-function entries to the baseline table.

The current snapshot adds these completed reports to that baseline:

| Added evidence | New function regions | Report |
| --- | ---: | --- |
| [Capture journal](CAPTURE_JOURNAL_RECONSTRUCTION.md) | 5 | `build/reverse-capture-journal-02/verification.json` |
| [Generated-coefficient pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md) | 1 | `build/reverse-biquad-pipeline-01/verification.json` |
| [Capture DSP dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md) | 12 | `build/reverse-capture-dispatch-03/verification.json` |
| [DSP initialization](DSP_INITIALIZATION_RECONSTRUCTION.md) | 8 | `build/reverse-dsp-initialization-01/verification.json` |
| [Capture memory reset](CAPTURE_RESET_RECONSTRUCTION.md) | 1 | `build/reverse-capture-reset-03/verification.json` |
| [Complete capture command](CAPTURE_COMMAND_RECONSTRUCTION.md) | 9 | `build/reverse-capture-command-01/verification.json` |
| [Complete capture parser and reader](CAPTURE_PARSER_RECONSTRUCTION.md) | 2 | `build/reverse-capture-parser-03/verification.json` |
| [Capture sample-processing orchestration](CAPTURE_PROCESSING_RECONSTRUCTION.md) | 6 | `build/reverse-capture-processing-03/verification.json` |
| [Dynamics configuration](DSP_DYNAMICS_RECONSTRUCTION.md) | 3 | `build/reverse-dsp-dynamics-01/verification.json` |
| [IR preparation and installation](IR_INSTALLATION_RECONSTRUCTION.md) | 10 | `build/reverse-ir-installation-01/verification.json` |
| [Integrated native capture loading](CAPTURE_NATIVE_RECONSTRUCTION.md) | 0 | `build/reverse-capture-native-02/verification.json` |
| [Capture warm-up](CAPTURE_WARMUP_RECONSTRUCTION.md) | 1 | `build/reverse-capture-warmup-02/verification.json` |
| [DSP audio path](DSP_AUDIO_PATH_RECONSTRUCTION.md) | 6 | `build/reverse-dsp-audio-path-01/verification.json` |
| [DSP transition requests](DSP_TRANSITION_RECONSTRUCTION.md) | 2 | `build/reverse-dsp-transition-03/verification.json` |
| [IR convolution construction and FFT](IR_CONVOLUTION_RECONSTRUCTION.md) | 14 | `build/reverse-ir-convolution-02/verification.json` |
| [Native loading, warm-up and processing](CAPTURE_LIVE_RECONSTRUCTION.md) | 0 | `build/reverse-capture-live-02/verification.json` |
| [Preset application](PRESET_APPLICATION_RECONSTRUCTION.md) | 7 | `build/reverse-preset-application-01/verification.json` |
| [Dynamics sample processing](DSP_DYNAMICS_PROCESSING_RECONSTRUCTION.md) | 5 | `build/reverse-dsp-dynamics-processing-02/verification.json` |
| [IR processing](IR_PROCESSING_RECONSTRUCTION.md) | 16 | `build/reverse-ir-processing-01/verification.json` |
| [Nonreturning audio task and helpers](AUDIO_TASK_RECONSTRUCTION.md) | 6 | `build/reverse-audio-task-03/verification.json` |
| [Scene application and selection integration](SCENE_APPLICATION_RECONSTRUCTION.md) | 3 | `build/reverse-scene-application-03/verification.json` |
| [Installed transition notification and gain integration](DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md) | 1 | `build/reverse-dsp-transition-notification-05/verification.json` |
| [Asynchronous capture and worker](CAPTURE_ASYNC_RECONSTRUCTION.md) | 4 | `build/reverse-capture-async-03/verification.json` |
| [DSP stage, routing and branch processing](DSP_STAGE_RECONSTRUCTION.md) | 16 | `build/reverse-dsp-stage-02/verification.json` |
| [Effect resampling](EFFECT_RESAMPLING_RECONSTRUCTION.md) | 6 | `build/reverse-effect-resampling-02/verification.json` |
| [Effect enable and fades](EFFECT_ENABLE_RECONSTRUCTION.md) | 13 | `build/reverse-effect-enable-03/verification.json` |
| [Parameter support](EFFECT_PARAMETER_SUPPORT_RECONSTRUCTION.md) | 19 | `build/reverse-effect-parameter-support-01/verification.json` |
| [Effect processing callers](EFFECT_PROCESSING_RECONSTRUCTION.md) | 16 | `build/reverse-effect-processing-02/verification.json` |
| [Parameter updates and automation](EFFECT_PARAMETERS_RECONSTRUCTION.md) | 7 | `build/reverse-effect-parameters-03/verification.json` |
| [Parameter resources](EFFECT_PARAMETER_RESOURCES_RECONSTRUCTION.md) | 19 | `build/reverse-effect-parameter-resources-01/verification.json` |
| [Effect construction](EFFECT_CONSTRUCTION_RECONSTRUCTION.md) | 14 | `build/reverse-effect-construction-02/verification.json` |
| [Parameter/resource integration](EFFECT_PARAMETER_LIFECYCLE_RECONSTRUCTION.md) | 0 | `build/reverse-effect-parameter-lifecycle-02/verification.json` |
| [Signal kernels and caller integration](EFFECT_SIGNAL_RECONSTRUCTION.md) | 3 | `build/reverse-effect-signal-01/verification.json` |
| [Effect routing and ownership](EFFECT_OWNERSHIP_RECONSTRUCTION.md) | 8 | `build/reverse-effect-ownership-01/verification.json` |
| **Current function total, including baseline** | **331** | |

Journal evidence includes six function ranges, but its comparison helper at
`0x020282bc..0x020282f4` was already counted in the preset loader. Its append
ranges at `0x0200ab96..0x0200ac36` and `0x0200acb4..0x0200acde` remain command
fragments and are now archived inside the complete command. Pipeline evidence
reuses fifteen existing function ranges and adds
only the getter at `0x02028920..0x02028936`; its new batch adapter is not an
original firmware function. Dispatch includes eight substantive wrappers and
four two-byte RTS-only helpers. Parser and reset remain external services in the
unchanged dispatch report; their complete bodies are supplied by the new reports.
The native loading report executes the real parser and reset through those
callers, retaining their original ranges. IR installation similarly reuses five
ownership/load functions and two mathematical functions while adding ten new
bodies. These reused ranges add evidence, not entries or bytes.
IR convolution declares 20 regions: 14 new bodies and six reused helpers.
The live-capture report joins 29 existing regions and keeps the context, arena
and source buffers at their original addresses across calls. Its new portable
adapter and additional small-head-ring support do not add an original function.
Preset application declares 21 regions, including seven new bodies and 14 reused
helpers. IR processing declares 36 regions, including 16 new bodies and 20 reused
construction/preparation helpers. Dynamics processing declares five new bodies;
its loaded interpreter also executes previously reconstructed configuration,
initialization and mathematical dependencies. The audio-task report declares six
new bodies and binds the reused DSP/capture bodies separately. These integrations
do not add duplicate entries for their dependencies.
Scene application declares twelve regions: three new bodies and nine reused
selection/query helpers. Its numerical dependencies are bound separately and
already declared by the selected DSP reports. Transition notification declares
37 regions, adding only the installed callback. Asynchronous capture declares
four new bodies; its worker's command no-op at `0x01c13080..0x01c13082` is an
exact single RTS, although that report does not set the older `rts_only`
annotation. The stage report declares sixteen bodies, including the complete
copy helper at `0x01c1a14c..0x01c1a182`. Earlier dynamics evidence executed and
bound that copy but did not declare it as a separately counted whole function.
It is now counted once. The five new effect reports declare only their 61 new
bodies. Their loaded resampling, IR, audio, scene, metadata and support
dependencies retain their previously declared regions. Integration adapters,
source-level wrappers and reused bodies add no duplicate functions. The resource
report declares nineteen new bodies and executes ten previously counted helpers.
Construction declares fourteen new bodies and eleven reused helpers. Its larger
loaded instruction set and seven ABI-only evidence bodies add no extra function.
The signal and ownership reports declare only their three and eight new bodies;
their loaded dependencies retain existing entries. Parameter/resource lifecycle
joins the seven parameter and nineteen resource bodies without adding a function.
This inventory does not imply that every component is already integrated into
one complete executable firmware image.

Regions with identical boundaries are deduplicated. The expanded adapter accepts
only these four explicit containments:

| Archived fragment, end exclusive | Complete parent, end exclusive |
| --- | --- |
| `0x02032586..0x02032618` | Parser `0x02031c64..0x0203291c` |
| `0x020327de..0x0203280c` | Parser `0x02031c64..0x0203291c` |
| `0x0200ab96..0x0200ac36` | Command `0x0200a888..0x0200ad06` |
| `0x0200acb4..0x0200acde` | Command `0x0200a888..0x0200ad06` |

Each archived record retains its original hash, module evidence and a parent
link with the complete parent's hash and evidence. All other differing overlaps
stop the audit for explicit review. The 335 deduplicated evidence records therefore
describe 331 active regions and four archived fragments, not 335 functions.

The capture layer dispatch table occupies exactly
`0x01c12bf2..0x01c12bf6` inside `0x01c12a54..0x01c12c32`. Its pinned bytes are
`02 1a 0e 14`, interpreted by `tbb [r1]` at `0x01c12bf0`. The four targets are
`0x01c12bf6`, `0x01c12c26`, `0x01c12c0e` and `0x01c12c1a`. The adapter checks
the table range and bytes against both the original image and processing
report, then verifies that every target starts a decoded instruction packet
inside the parent. The four data bytes remain part of the parent's byte count
but are excluded from instruction counts and linear candidate call sources.

The IR resampling table occupies `0x0203be2c..0x0203be50`. Its nine signed
32-bit coefficients have SHA256
`5e4544bfe9c57a8a3dc7f9db243232a0362dca09497be8503c418e379879165c`.
The DSP adapter binds that range, hash and every signed word to the final IR
report and original image, then checks the exact table-address load at
`0x0203143c` inside the recovered resampler. These 36 bytes are excluded from
linear call sources and targets. The pinned listing has no call encoding in
this table, so the exclusion improves data classification without changing the
2,207 direct-call target candidates.

The application adapter adds four narrowly bound data ranges:

| Original range, end exclusive | Bytes | Consumer/caller evidence |
| --- | ---: | --- |
| `0x0203a614..0x0203b334` | 3,360 | Metadata getter `0x0202921e..0x02029248`: 84-byte type stride, 12-byte parameter stride and presence word at record offset 8 |
| `0x0203be50..0x0203be90` | 64 | Accelerator start `0x01c124a8..0x01c12556`: command/index address loads at `0x01c1251a` and `0x01c124d2` |
| `0x020364d6..0x020364e0` | 10 | Audio task: base load `0x01c01e72`, nine taps and mask 15 at `0x01c0200a..0x01c02016` |
| `0x02036f24..0x02036f38` | 20 | Audio task: the same base plus 2638, nineteen taps and mask 31 at `0x01c02066..0x01c02076` |

Each exclusion requires a passing report for the pinned image, its exact original
bytes and digest, the complete consumer/caller hashes and the decoded proof
sites. Metadata presence bits are recomputed from all seven records for types
1..39; the type-zero records remain part of the exact 40-type table. Both FIR
ranges also bind the complete helper `0x01c01234..0x01c01292`, its signed
halfword coefficient loads and half-count loop. Only the two coefficient spans
are excluded; the gap between them retains its independent classification.
The generated report records metadata presence bits, accelerator words, FIR
coefficients and each full SHA256.
None of these four ranges contributes a linear call encoding or target, so the
2,207 linear target candidates remain unchanged.

The stage adapter additionally excludes exactly `0x0203b480..0x0203b4a8`,
40 bytes with SHA256
`ad42fb64992b7995f180484ba717298b55c46909537d0e9a01ee333cf4662362`.
Both complete consumers are bound: capability selection at
`0x01c0558c..0x01c055a8` and active-state selection at
`0x01c055d2..0x01c05618`. Eleven decoded sites establish the type-byte loads,
table bases, indexed byte accesses, two-bit field selection and upper-bit
parameter index. The compared type domain is 0..39; it is not an inferred
guarantee for arbitrary firmware memory. The table adds no linear call source
or target. Bytes immediately before and after it remain independently classified.

The effects adapter adds the following individually authenticated spans. Exact
endpoints, hashes, consumers and decoded proof instructions remain in the report
and the linked module documentation.

| Evidence group | Spans | Bytes |
| --- | ---: | ---: |
| Resampling pointers, counts and three tap arrays | 5 | 72 |
| Enable/fade branch table and its separate alignment byte | 2 | 30 |
| Parameter selector and tempo tables | 2 | 110 |
| Processing branch tables, state-copy descriptors and cost tables | 8 | 520 |
| Parameter word-classification branch table | 1 | 78 |
| Previously verified coefficient, initialization and gain tables | 3 | 216 |

The 18 new-module spans total 810 bytes: 352 embedded bytes inside new function
ranges and 458 external bytes. The three earlier tables occupy exactly
`0x0203a55c..0x0203a566`, `0x0203a566..0x0203a570` and
`0x02033bc8..0x02033c8c`. Those 216 bytes were bound by earlier reports but had
not yet been excluded from the inventory scan. Their original reports remain
unchanged. All 21 spans bind 83 decoded proof sites and their complete consumers.
The extra-cost table has 35 one-byte entries and one zero alignment byte;
the fade table's 29 entries and its following byte remain separate spans.
Resampling pointers and counts must identify the exact three tap arrays.
None of these exclusions changes the 2,207 linear direct-call candidates.

The resource adapter adds three embedded spans totaling 48 bytes:
`0x01c068ee..0x01c06904`, `0x0202ef12..0x0202ef22` and
`0x0202ef3e..0x0202ef48`. They contain 46 branch entries and two separate
alignment bytes. The reset and fingerprint consumers contain 18 and 78 decoded
instructions respectively; the adapter binds their complete original hashes,
table declarations, index instructions and packet-aligned destinations. These
exclusions likewise add no function or linear direct-call candidate.

The construction adapter adds eight exact spans totaling 173 bytes. The embedded
tables at `0x0202cfac..0x0202cffa` and `0x0202a802..0x0202a808` contain 39
halfword entries, five byte entries and one zero alignment byte, totaling 84
bytes. Six external arrays occupy exactly `0x0203a550..0x0203a55c`,
`0x0203b608..0x0203b616`, `0x0203b618..0x0203b634`,
`0x0203b634..0x0203b639`, `0x0203b63a..0x0203b644` and
`0x0203b644..0x0203b658`, totaling 89 bytes. Their two intervening gaps remain
unclassified. The existing 26-byte tempo exclusion is authenticated again
through its new complete consumers and is not duplicated. These declarations
bind five complete consumers and 72 distinct decoded use sites; no new linear
call candidate is inferred. Signal, lifecycle and ownership add no data span.

## Instruction execution gaps

Complete C bodies and reviewed function boundaries do not establish exhaustive
input or instruction-path coverage. The current reports explicitly leave these
instructions unvisited in their respective corpora:

| Report scope | Visited | Decoded | Unvisited |
| --- | ---: | ---: | ---: |
| Complete parser and read helper | 1,136 | 1,213 | 77 |
| New command/helper instructions | 531 | 545 | 14 |
| New capture-processing instructions | 464 | 465 | 1 |
| New capture warm-up instructions | 117 | 118 | 1 |
| New dynamics instructions | 72 | 73 | 1 |
| New IR convolution instructions | 799 | 800 | 1 |
| New DSP stage/helper instructions | 1,996 | 2,003 | 7 |
| New enable/fade instructions | 364 | 365 | 1 |
| New effect-processing instructions | 4,218 | 4,223 | 5 |
| New parameter-update instructions | 993 | 994 | 1 |
| Joined native capture-loading instructions | 1,410 | 1,551 | 141 |
| Joined loading, warm-up and processing instructions | 3,300 | 3,670 | 370 |
| Joined IR construction and reused helpers | 907 | 916 | 9 |
| Joined IR processing and construction helpers | 2,869 | 3,182 | 313 |
| Joined installed notification, requests and processing | 1,287 | 1,437 | 150 |
| Loaded parameter resources and reused helpers | 737 | 745 | 8 |
| Declared construction and reused helpers | 1,494 | 1,495 | 1 |
| Joined parameter/resource lifecycle | 1,334 | 1,573 | 239 |

The parser report classifies its 77 unvisited instructions by dominating entry
invariants: 51 guarded by minimum header length, four by minimum length for the
rechannel fraction, one by validated nonzero channels, 19 by validated convolution
shift bounds and two by validated nonzero layer count. These classifications
remain reported evidence; the inventory does not relabel those instructions
as executed or claim exhaustive input coverage.

The complete command body itself visited all 399 decoded instructions. Its 14
remaining new-helper gaps comprise four status-text instructions, two prefix
instructions and eight decimal-core instructions.

The processing report identifies `0x01c12f1e` as a redundant loop fall-through:
the final index branches to the head stage before reaching it, and the count is
preserved by the callee ABI. The dynamics report leaves `0x02030fee`, which
would force the computed threshold to 1024, unvisited. Its preceding clamp
admits 201 threshold values; exhaustive original execution produces values
from 838860 through 8388607 for all of them. The adapter preserves both reported
explanations and does not relabel either instruction as executed.

The warm-up report leaves `0x01c12ff0` unvisited: the final-layer branch reaches
the head-history fill before that redundant loop fall-through. The IR constructor
leaves `0x020319be` unvisited: index 128 branches to the fixed Nyquist pair before
the loop can reach index 129. Both reports retain the original instructions and
record their control-flow explanations. The audio-path and transition reports
visit all 335 and 122 new instructions respectively.

The joined native-loading corpus adds no new original instructions. Of its
141 unvisited joined instructions, 110 are in the parser and 31 in memory reset.
The broader standalone parser/reset/dispatch reports retain their own cases.
The inventory binds the joined count and each missing address to the 15
declared original ranges, records its loaded-model coverage separately
(2,042/3,179), and never adds either count to other corpora.

The live-capture corpus leaves 370 of its 3,670 joined instructions unvisited:
173 parser/read-helper instructions, 31 reset instructions, 23 preparation,
cleanup and capability instructions, 138 separate rechannel/iteration/head
wrapper instructions, three rechannel-kernel instructions and one each in
processing and warm-up. Its loaded-model count is 3,873/5,298. Separate module
corpora remain the evidence for paths not exercised by this integration run.

The IR joined corpus leaves nine instructions unvisited: the one new constructor
gap and eight reused budget/conversion/limit-helper instructions. Its larger
loaded-model count is 907/2,442. The inventory binds the joined set to all 20
declared regions and counts only the 14 new regions as additions. It does not
sum the joined, new or inherited counts into a global execution figure.

All four additions in snapshot `-07` visit every new instruction in their own
corpus: preset application 928/928, dynamics processing 515/515, IR processing
2,266/2,266 and audio task/helpers 1,399/1,399. Their loaded-model counts are
respectively 1,173/1,176, 1,079/1,800, 2,869/4,708 and 3,518/5,574. Preset
application leaves three reused helper instructions unvisited at `0x02006f36`,
`0x02006f86` and `0x02007c90`. The IR joined corpus's 313 gaps are in inherited
construction/preparation paths. Dynamics and audio retain their separate
inherited-code gaps; coverage from prior standalone reports is not added to
these corpora.

Snapshot `-08` adds scene application with 370/370 new instructions and
517/517 instructions across its twelve declared regions; its larger loaded
model visits 996/1,954. The installed notification visits all nine new
instructions and 1,287/1,437 joined/loaded instructions. Its 150 gaps remain
in inherited coefficient setup/staging, biquad, initialization, dynamics and
audio paths. Asynchronous capture visits 550/550 new instructions and
2,488/6,241 loaded instructions. It compares actual worker scheduling and
software numerical completion fixtures; these do not establish accelerator
or interrupt equivalence.

DSP stage processing visits 1,996/2,003 new instructions and 2,828/7,553 loaded
instructions. Its seven listed gaps are `0x01c11530`, `0x01c11532`,
`0x01c11536`, `0x01c11538`, `0x01c1153a`, `0x01c1172e` and `0x01c11730`.
The report classifies them as empty-group fallbacks: a valid route scan creates
a nonempty group, and its retained group length cannot reach those tests.
The inventory preserves that classification without marking the instructions
executed. Individual/grouped effect services and their sample outputs remain
explicit fixtures. Twenty-four joined task observations include eight original
stage entries; this is a bounded integration corpus.

Snapshot `-09` visits all 612 new resampling and all 449 new parameter-support
instructions. Enable/fade handling visits 364/365 new and 369/370 loaded
instructions. Its gap at `0x020304fc` is the zero-only assignment after a
construction branch entered with a nonzero callee-saved desired value.

Effect processing visits 4,218/4,223 new and 8,808/17,064 loaded instructions.
Its five gaps are `0x01c05ce4`, `0x01c05ce6`, `0x01c05ce8`, `0x01c0e816` and
`0x01c0fcac`. They are respectively excluded by the immutable type/capability
table, the positive remaining block count and the saved positive stereo mode.
Parameter updates visit 993/994 new and 2,712/15,011 loaded instructions.
The sole gap at `0x0202f960` contradicts the preceding type-five guard on the
same unchanged register. Independent reviews confirmed these proofs within
the documented entry, callback and mapping domains. All seven addresses stay
explicitly unexecuted. The processing and parameter corpora now execute actual
previously recovered stage, scene, audio, resampling and IR bodies; their
remaining numerical, construction and platform services remain explicit.

Parameter resources visit all 579 new instructions and 737/745 loaded
instructions. Six inherited active-helper instructions at `0x01c055da`,
`0x01c055de`, `0x01c055e2`, `0x01c055e4`, `0x01c055e6` and `0x01c055e8`
cannot be reached because fingerprint returns directly for type 25. The two
IR-active instructions at `0x01c11f62` and `0x01c11f64` require a zero object,
whereas the recovered wrapper calls that helper only with a nonzero object.
These are caller-invariant gaps in this corpus, not missing new resource code.

Construction visits all 1,242 new instructions and 1,494/1,495 declared
instructions. The inherited generator's mode-two zero-parameter enable
assignment at `0x02028842` remains unvisited in this corpus. Its full loaded-model count is
2,197/16,253; those additional unvisited addresses remain listed in that report.
The 72 parameter-caller fixtures execute the actual constructor only under an
explicit restriction that excludes callback-token collisions. They do not
establish a general public parameter/constructor integration API.

The separate lifecycle report visits 1,334/1,573 joined and 2,984/15,590 loaded
instructions. Its scoped appendix classifies all 239 joined gaps: 225 inherited
parameter paths and fourteen resource alternatives. Wider prior coverage is
retained separately, not added to this integration's executed count. All
nineteen direct resource sites execute; indirect numeric-token collisions remain
external callbacks. This integration contributes no new original body.

Signal processing visits all 708 new instructions and 3,131/17,772 loaded
instructions, including actual stage/audio callers. Constructor-derived values
are not claimed by its synthetic parameter fixtures. Ownership visits all 236
new and all 264 loaded instructions. Its twenty guarded fourth-pointer-read
cases compare original public-memory/callback prefixes; the portable guard is
not an original firmware return. No broader fault or hardware behavior is inferred.

The audio task is nonreturning. Its comparisons resume at completed waits or
frame boundaries and observe both fatal spins. Covering every instruction
across these bounded cases does not establish every path combination, indefinite
operation, scheduler behavior, peripheral execution or physical audio behavior.
External services and MMIO remain explicit boundaries in their respective
reports. No global execution or firmware-completion percentage is inferred.

Missing addresses for new/module and declared joined regions are retained in
the generated inventory. Loaded-model gaps remain per-report evidence. Other current
reports with recorded new/module counts
report zero gaps in their respective new regions. The older native-A2 report
records comparison cases but no aggregate instruction-execution count; the
inventory marks that count as unavailable.

Combined interpreter counts include inherited code and can contain additional
unvisited instructions. They are recorded per report alongside the new/module
counts. Overlapping regions and different corpora prevent adding those numbers
into a single global execution-coverage percentage.

## Reference and audit provenance

The original reference is Alpha11/M5.71 TANK-G v2, SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The tool verifies that the entire decoded `app.bin` equals the application
unpacked from that pinned image before inspecting any range.

The original memory mapping is flash base `0x02000120`, RAM-copy source
`0x02056780`, RAM destination `0x01c00000`, and copy length `0x2030c`. A RAM
function is inventoried at its runtime RAM address; the stored flash copy is
not a second function.

The current audit checked:

- All 331 active region hashes and four archived fragment hashes against the pinned image.
- **362 distinct source hashes** recorded by the 50 selected reports.
- **718 generated artifact hashes** from the completed build manifests.
- Exact bytes and contiguous addresses in both linear disassembly listings.
- All selected report/input hashes, recorded as relative paths in the inventory.

The preserved baseline audit checked 90 region hashes, 115 source hashes and
95 artifact hashes. Snapshot `-03` checked 110 regions, 135 source hashes and
123 artifact hashes. Snapshot `-04` checked 130 region/fragment hashes,
164 source hashes and 160 artifact hashes. Snapshot `-05` checked 149
region/fragment hashes, 192 source hashes and 204 artifacts. Snapshot `-06`
checked 172 region/fragment hashes, 234 source hashes and 279 artifacts.
Snapshot `-07` checked 206 region/fragment hashes, 263 source hashes and 343
artifacts. Snapshot `-08` checked 230 region/fragment hashes, 291 source hashes
and 442 artifacts. Snapshot `-09` checked 291 region/fragment hashes, 327 source
hashes and 542 artifacts. Snapshot `-10` checked 310 region/fragment hashes, 334
source hashes and 582 artifacts. The current report captures all nine inventory-tool hashes;
earlier tools and snapshots remain unchanged. Older development reports stay
outside the selected current set. Twenty-two read-only adapter checks cover
containment order, evidence deduplication, rejected unknown overlaps, bad hashes
and contradictory instruction-count/classification records. Thirteen additional
read-only runtime-adapter checks cover exact table boundaries/bytes, missing or
invalid dispatch targets, data decoded as code, and contradictory joined
instruction counts/addresses. Nineteen read-only DSP-adapter checks cover
rejected table ranges, hashes, signed words, consumer evidence and exclusion
boundaries. The application adapter adds 113 checks for altered report
status/image binding, table ranges/hashes, metadata presence bits, complete
consumer/caller hashes, each required decoded proof site, exclusion endpoints
and the gaps between FIR tables. The stage adapter adds 33 checks for altered
status/image/table bindings, complete consumer bounds/hashes, required decoded
sites and exact exclusion endpoints. Its consumer sites were also checked
against the actual original instruction decoder. The effects adapter adds 649
checks for exact declarations, report status/image/hash bindings, complete
consumer bodies, required proof sites, branch entries, packet boundaries,
padding, pointer/count relationships and exclusion endpoints. The resource
adapter adds 179 checks for exact declarations, frozen report bindings, complete
consumer bodies, index instructions, branch packet starts, padding and exclusion
endpoints. The construction adapter adds 489 checks for report/image binding,
exact declarations and table bytes, complete consumers, original use sites,
branch packet starts, padding and known-data boundaries. The final snapshot
records **1,149 input hashes**; a separate read-back audit checked every input
and the generated manifest. All **980 prior input bindings** are
retained unchanged. The manifests and report hashes of snapshots `-01` through
`-10` also remain valid.

The selected scene report is `-03`: `-01` omitted three external-service
arguments, corrected and independently asserted in `-02`; `-03` additionally
binds inherited dynamically loaded instruction-semantics sources. Asynchronous
capture `-03` and stage `-02` likewise include their full inherited-source
bindings. Earlier generated versions are preserved but are not selected for
this snapshot. Their preservation does not make them current verification
evidence for the maintained sources.

The effect report versions selected in `-09` are resampling `-02`, enable
`-03`, parameter support `-01`, processing `-02` and parameters `-03`.
Earlier runs remain preserved and unselected. Snapshot `-10` retains those exact
versions and adds resource `-01`. Snapshot `-11` adds construction `-02`,
lifecycle `-02`, signal `-01` and ownership `-01`. The constructor report's
`original_sha256` field is normalized only in memory by a narrowly scoped
loader; its original bytes, source hashes, artifacts and manifest remain bound.
Ongoing configured-signal, resource/ownership integration and model-construction
work contributes no entries to this snapshot.

The baseline flash listing ends at `0x02056780`, before the stored RAM copy, so
this input already avoids duplicate decoding of that copy. The inventory also
contains an explicit exclusion for it. The RAM listing ends at `0x01c2030c`.
These listing extents are recorded; they do not establish that every application
byte is executable code.

The linear listings contain 10,350 direct-call encodings in total. Six occur
inside the identified embedded A2 capture and are excluded; one targets outside
the application mappings. The remaining 10,343 call sites supply the 2,207
distinct linear target candidates. The tool re-decodes each call from its original
bytes, but this does not prove that the containing bytes execute as code.
Unidentified constants, strings, pointer tables and other data still prevent a
complete code/data classification.

The G v2 Ghidra export contains 260 entries and explicitly declares partial
automatic recovery. Its `ok` status means a decompiler export completed, not
that inferred C is correct, buildable or validated. Counts aggregated across
G/B versions or the stock MINI cannot serve as the function total for this image.

## Remaining dependencies

The generated dependency list is more directly actionable than a percentage:
it names each direct call site, its source reconstructed region and its target.
In the current snapshot, examples include:

| Area | Original targets still outside the reconstructed regions |
| --- | --- |
| Parameter resources and construction | Constructor `0x0202cf62`, object update `0x0202cd32`, allocation `0x0202edb8`, migration `0x0202ee3c`, fingerprint `0x0202eefa` and mode service `0x0202efe2` |
| Command output | Formatting `0x02007010`, report helper `0x0200a768` |
| IR effect refresh and ownership | `0x020298ce`, `0x02029afc`; direct and deferred installation are now recovered |
| Effect setup and refresh | `0x0202e710`, `0x0202f46c`, `0x0202e328`, `0x0202ec30` and other services exposed by preset application and the recovered callers |
| Audio and effect numerical processing | `0x01c012d8`, `0x01c01de4`, `0x01c08b3e`, `0x01c0ba14`, `0x01c18f90` and other numerical leaves; dispatcher, individual/group wrappers and stage orchestration are now recovered |
| Physical storage and scheduling | Program `0x02002ef2`, erase dispatch `0x02002b80`, reads `0x02002806` / `0x02002810`, polling/priority and clock helpers |
| Memory/platform services | Allocator/free, bounded memory-library contracts, notification and mode services |

This list is a snapshot. A subsequent report can replace some of these boundaries
with reconstructed code while exposing new dependencies. An indirect call site
can correspond to multiple targets, and a function body can depend on hardware
or concurrency beyond its immediate call graph. The list therefore does not
mean only 111 functions remain to finish the firmware. Earlier snapshots counted
35, 40, 42, 39, 38, 92 and 94 targets. Snapshot `-07` closes the old direct boundary at
`0x020092fa` while exposing 55 additional direct targets through the newly
reconstructed callers. The four additional indirect sites are all within preset
application, at `0x020097b0`, `0x020098e8`, `0x02009a52` and `0x02009ab0`.
Snapshot `-08` closes five older direct boundaries: asynchronous capture
`0x01c04cda`, stage processing `0x01c10e06`, word copy `0x01c1a14c`, scene apply
`0x0200a1d6` and scene report `0x0200a228`. It exposes seven more targets:
`0x01c0f678`, `0x01c10446`, `0x02028f96`, `0x0202fba6`, `0x0202fd18`,
`0x02030530` and `0x020305f8`. Six additional indirect sites occur at
`0x01c045de`, `0x01c04616`, `0x01c10824`, `0x01c10ff2`, `0x01c115d0` and
`0x01c118e2`. Those 19 sites also retain the transition callback, IR
allocation/free services and producer dispatch. Individual corpora resolve
some targets within their stated domain. These changing counts describe the
explored call graph.

Snapshot `-09` closes eleven earlier direct boundaries: the individual/group
callers, commit/fast/probe parameters, four enable/status entries and the complete
memory move/fill helpers. It exposes 38 additional direct targets through the
new bodies, giving 121 in total. Ten additional indirect sites occur at
`0x01c0656e`, `0x01c06af0`, `0x01c06b28`, `0x01c0f940`, `0x01c10100`,
`0x01c101ac`, `0x01c1041a`, `0x01c10632`, `0x01c10796` and `0x0202f2aa`.
Those 29 indirect sites include installed callbacks executed within some
module corpora and alternate tokens kept as explicit services.

Snapshot `-10` closes nine direct boundaries: mode callback `0x01c05ec6`, queue
flush `0x0202ed7e`, delay allocation `0x0202edb8`, migration `0x0202ee3c`, extra
allocation `0x0202eeba`, fingerprint `0x0202eefa`, mode change `0x0202efe2`, IR
state `0x0202f014` and IR length `0x0202f02e`. No new direct target appears, so
112 remain. The new bodies expose three additional indirect sites at
`0x01c05ed2`, `0x0202df16` and `0x0202edfc`, bringing their total to 32.

Snapshot `-11` closes six earlier direct targets: `0x01c1958e`, `0x01c19a8a`,
`0x01c1ee40`, `0x0202cf62`, `0x0202eb4c` and `0x0202ec30`. It exposes five
more through construction: `0x0202a872`, `0x0202b838`, `0x0202b87e`,
`0x0202ba90` and `0x0202cf5a`; `0x0202cd32` was already unresolved. The total
therefore moves from 112 to 111. Ownership introduces three indirect sites at
`0x0202df84`, `0x0202df90` and `0x0202ebcc`, giving 35 sites in the current set.

An outside target means its body has no separately declared reconstructed
whole-function region in this inventory. Executing a dependency inside another
comparison does not automatically declare its complete body. The word-copy
helper illustrates this distinction: dynamics processing supplied narrower
integration evidence in `-07`, while the stage report supplies its first
separately declared whole-body evidence in `-08`. A dependency absent from the
direct-target list may still be reached through an indirect callback.
Bodies beyond unreconstructed dependencies are not automatically enumerated.

The next inventory work is to trace entry points and callback tables from known
code, classify constant/data spans, and establish function extents with callers
and control-flow evidence. Preserve uncertain candidates until that evidence
exists. The [roadmap](REVERSE_ROADMAP.md) tracks implementation priorities.

## Reproduce or extend

With the pinned [local inputs](LOCAL_SOURCES.md), completed baseline reports and
their generated artifacts available, the unchanged original tool reproduces the
historical baseline:

```powershell
python -B tools/inventory_reverse.py --check
python -B tools/inventory_reverse.py --output build/reverse-inventory-new
```

`--check` performs the audit and prints counts without writing files. An output
directory must be new and inside `build/`; an existing result is never overwritten.
The default report set stays pinned to the named baseline commit. It can add
completed reports whose ranges do not introduce differing overlaps:

```powershell
python -B tools/inventory_reverse.py --output build/reverse-inventory-extended --add-report build/reverse-new-module-01/verification.json
```

An added report must have passing evidence for the same original image, matching
source/artifact hashes and an explicit region schema. The generated inventory
records exactly which reports were selected and which other local reports were
left outside that snapshot.

The unchanged expanded adapter reproduces the `-04` snapshot's selected report
set and requires an explicit frozen parser report:

```powershell
python -B tools/inventory_reverse_expanded.py --self-test
python -B tools/inventory_reverse_expanded.py --output build/reverse-inventory-expanded-new --parser-report build/reverse-capture-parser-03/verification.json
```

The unchanged runtime adapter adds the processing report, its data-table policy
and the three other frozen runtime reports. To reproduce the historical `-05` evidence set
with a fresh output directory:

```powershell
python -B tools/inventory_reverse_runtime.py --self-test
python -B tools/inventory_reverse_runtime.py --output build/reverse-inventory-runtime-new --parser-report build/reverse-capture-parser-03/verification.json --processing-report build/reverse-capture-processing-03/verification.json --add-report build/reverse-capture-native-02/verification.json --add-report build/reverse-dsp-dynamics-01/verification.json --add-report build/reverse-ir-installation-01/verification.json
```

The unchanged DSP adapter adds the checked IR data exclusion. To reproduce the historical
`-06` evidence set with a fresh output directory:

```powershell
python -B tools/inventory_reverse_dsp.py --self-test
python -B tools/inventory_reverse_dsp.py --output build/reverse-inventory-dsp-new --parser-report build/reverse-capture-parser-03/verification.json --processing-report build/reverse-capture-processing-03/verification.json --ir-report build/reverse-ir-convolution-02/verification.json --add-report build/reverse-capture-native-02/verification.json --add-report build/reverse-dsp-dynamics-01/verification.json --add-report build/reverse-ir-installation-01/verification.json --add-report build/reverse-capture-warmup-02/verification.json --add-report build/reverse-dsp-audio-path-01/verification.json --add-report build/reverse-dsp-transition-03/verification.json --add-report build/reverse-capture-live-02/verification.json
```

The unchanged application adapter adds the metadata, accelerator and FIR table
exclusions. To reproduce the historical `-07` evidence set with a fresh output
directory:

```powershell
python -B tools/inventory_reverse_application.py --self-test
$inventoryArguments = @(
    "--output", "build/reverse-inventory-application-new",
    "--parser-report", "build/reverse-capture-parser-03/verification.json",
    "--processing-report", "build/reverse-capture-processing-03/verification.json",
    "--ir-report", "build/reverse-ir-convolution-02/verification.json",
    "--application-report", "build/reverse-preset-application-01/verification.json",
    "--ir-processing-report", "build/reverse-ir-processing-01/verification.json",
    "--audio-report", "build/reverse-audio-task-03/verification.json",
    "--add-report", "build/reverse-capture-native-02/verification.json",
    "--add-report", "build/reverse-dsp-dynamics-01/verification.json",
    "--add-report", "build/reverse-ir-installation-01/verification.json",
    "--add-report", "build/reverse-capture-warmup-02/verification.json",
    "--add-report", "build/reverse-dsp-audio-path-01/verification.json",
    "--add-report", "build/reverse-dsp-transition-03/verification.json",
    "--add-report", "build/reverse-capture-live-02/verification.json",
    "--add-report", "build/reverse-dsp-dynamics-processing-02/verification.json"
)
python -B tools/inventory_reverse_application.py @inventoryArguments
```

The stage adapter adds the exact capability-table exclusion. To reproduce the
preserved `-08` evidence set with a fresh output directory:

```powershell
python -B tools/inventory_reverse_stage.py --self-test
$inventoryArguments = @(
    "--output", "build/reverse-inventory-stage-new",
    "--parser-report", "build/reverse-capture-parser-03/verification.json",
    "--processing-report", "build/reverse-capture-processing-03/verification.json",
    "--ir-report", "build/reverse-ir-convolution-02/verification.json",
    "--application-report", "build/reverse-preset-application-01/verification.json",
    "--ir-processing-report", "build/reverse-ir-processing-01/verification.json",
    "--audio-report", "build/reverse-audio-task-03/verification.json",
    "--stage-report", "build/reverse-dsp-stage-02/verification.json",
    "--add-report", "build/reverse-capture-native-02/verification.json",
    "--add-report", "build/reverse-dsp-dynamics-01/verification.json",
    "--add-report", "build/reverse-ir-installation-01/verification.json",
    "--add-report", "build/reverse-capture-warmup-02/verification.json",
    "--add-report", "build/reverse-dsp-audio-path-01/verification.json",
    "--add-report", "build/reverse-dsp-transition-03/verification.json",
    "--add-report", "build/reverse-capture-live-02/verification.json",
    "--add-report", "build/reverse-dsp-dynamics-processing-02/verification.json",
    "--add-report", "build/reverse-scene-application-03/verification.json",
    "--add-report", "build/reverse-dsp-transition-notification-05/verification.json",
    "--add-report", "build/reverse-capture-async-03/verification.json"
)
python -B tools/inventory_reverse_stage.py @inventoryArguments
```

The construction adapter retains the entire inventory `-10` report set and
requires frozen construction `-02`. To reproduce the current `-11` evidence set,
also select the completed signal, lifecycle and ownership reports in a fresh
output directory:

```powershell
python -B tools/inventory_reverse_construction.py --self-test
$inventoryArguments = @(
    "--output", "build/reverse-inventory-construction-new",
    "--parser-report", "build/reverse-capture-parser-03/verification.json",
    "--processing-report", "build/reverse-capture-processing-03/verification.json",
    "--ir-report", "build/reverse-ir-convolution-02/verification.json",
    "--application-report", "build/reverse-preset-application-01/verification.json",
    "--ir-processing-report", "build/reverse-ir-processing-01/verification.json",
    "--audio-report", "build/reverse-audio-task-03/verification.json",
    "--stage-report", "build/reverse-dsp-stage-02/verification.json",
    "--resampling-report", "build/reverse-effect-resampling-02/verification.json",
    "--enable-report", "build/reverse-effect-enable-03/verification.json",
    "--support-report", "build/reverse-effect-parameter-support-01/verification.json",
    "--effect-processing-report", "build/reverse-effect-processing-02/verification.json",
    "--parameters-report", "build/reverse-effect-parameters-03/verification.json",
    "--resources-report", "build/reverse-effect-parameter-resources-01/verification.json",
    "--construction-report", "build/reverse-effect-construction-02/verification.json",
    "--add-report", "build/reverse-effect-signal-01/verification.json",
    "--add-report", "build/reverse-effect-parameter-lifecycle-02/verification.json",
    "--add-report", "build/reverse-effect-ownership-01/verification.json"
)
python -B tools/inventory_reverse_construction.py @inventoryArguments
```

Use `--check` instead of `--output` for a read-only audit. Additional frozen
reports can be supplied with repeated `--add-report` arguments; unknown overlaps
still require explicit policy work. All generated reports stay under ignored
`build/`, and existing directories are refused.

The preserved `-04` inventory report SHA256 is
`6681171220c3e1c3063b8f9136aaaf806257c803d907f3d0e419a26afb72956e`.
The preserved `-05` inventory report SHA256 is
`9706295d22ea69753fff622b7d3b61a53384a6033aabe9f904c9e4caae88a09c`.
The preserved `-06` inventory report SHA256 is
`4993a801e4c0ee1c45735f8ba4960f0a1fcb86285ae3080dffe91e543a8d26c0`.
The preserved `-07` inventory report SHA256 is
`948464bf96c4d09837537d09716ea2f95cfab78f5d0e41a0aa91d21c33b0b716`.
Its preserved build-manifest SHA256 is
`570df7d70261e651fa39d47ee7d74c2e73599ea7c339aa80407382e67be790e2`.
The preserved `-08` inventory report SHA256 is
`3515ea5877dd8334fa6ab87c28244d24418387bad15a8a8b6907909685d30b3b`.
Its build-manifest SHA256 is
`a89e99ae75585537d4cd7865fbbb463bfebb1757fc2f6b9f15884528de3d85df`.
The preserved `-09` inventory report SHA256 is
`8e0497f6ad3f7a15bf59d8e64e89ee52a7d03bfb8fb0f5efe630bc0d689885e9`.
Its build-manifest SHA256 is
`b4f8991f4f56c4f32795dfcf27237418e0f186d7cabc3318dc52cbdc93ef771e`.
The preserved `-10` inventory report SHA256 is
`25699e77c4fa45ae8d6a6b9144117f96b4ee9ab7bec62d4ba9e567e8c50dc740`.
Its build-manifest SHA256 is
`85959829ee0db2764e187eb396b532ec37685c037ede044a77d326f5c881e275`.
The current `-11` inventory report SHA256 is
`4801cbbfd78ff73cf4b836bc412840775e1d4e1ddbfffaba704f182ea7ca3e36`.
Its build-manifest SHA256 is
`485b6dadc1ea6abe06bf54cc820dcd3e3414cb4a303dd4424f54f75d7d81259a`.
