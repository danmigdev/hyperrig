# Reverse engineering inventory

The current audited report set contains **506 reconstructed function regions**.
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
from `-09`. Snapshot `-11` adds 25 regions for effect construction,
three signal kernels and ownership. A separate parameter/resource integration
report adds no function. All 46 reports from `-10` remain selected; every earlier
snapshot remains unchanged. Snapshot `-12` adds nine IR lifecycle
bodies and two integration reports without new functions. All fifty reports
from `-11` remain selected, giving 53 reports. Snapshot `-13` adds
49 model-construction bodies and retains all 53 prior reports, giving 54 reports
in total. Snapshot `-14` adds eleven storage-preparation bodies
and the IR numerical integration report, retaining all 54 prior reports for a
total of 56. Snapshot `-15` retains those reports and adds the
parameter-constructor integration, for 57 reports with no additional function.
Snapshot `-16` adds 45 storage-control bodies, retaining all 57 preceding reports
for a total of 58. Snapshot `-17` adds nine storage-coordination
bodies and retains all 58 reports, giving 59. Its reused rate helper and all
reused numerical bodies remain counted once.
Snapshot `-18` adds seven sample-processing bodies and retains all 59 reports,
giving 60. Constructor, dispatcher, stage, audio and numerical dependencies
remain existing functions, with separate coverage for the new joined corpus.
Snapshot `-19` retains those 60 reports and adds storage-runtime integration,
giving 61. Its 75 whole bodies were already reconstructed; the eighteen real
joins add integration evidence without new functions, code bytes or data spans.
Snapshot `-20` adds 45 complete effect-setup bodies and retains all 61 previous
reports, giving 62. Its parameter, constructor, resource and IR dependencies
remain existing functions; their named roles and loaded instructions are not
additional recovered entries.

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
all earlier reports and policies. The unchanged
[`inventory_reverse_construction.py`](../tools/inventory_reverse_construction.py)
adds eight exact construction data exclusions and reauthenticates one existing
tempo table, binding five complete consumers and 72 distinct decoded proof sites.
It adapts the constructor report's original-image hash field in memory while
preserving its exact report and manifest bytes. The unchanged
[`inventory_reverse_integrations.py`](../tools/inventory_reverse_integrations.py)
accepts the configured-signal report's intentionally empty function declaration
without inserting synthetic regions. Every loaded instruction must match the
canonical address and size decoded from an existing complete function. It also
binds the four named reused bodies and their individual execution gaps. Thirty
static spans retain prior data exclusions; reset configuration and the task
registration instruction witness retain their exact earlier audio-report
bindings without changing code/data classification. The unchanged
[`inventory_reverse_models.py`](../tools/inventory_reverse_models.py)
binds sixteen model tables to thirteen complete consumers and 93 independently
decoded use, index, field and caller sites. It authenticates all new and reused
model bodies before checking merged instruction windows and their separate
coverage gaps. The report's original hash field is adapted only in memory.
The unchanged [`inventory_reverse_lifecycle.py`](../tools/inventory_reverse_lifecycle.py)
authenticates the storage report's eleven new and ten reused bodies and every
declared instruction gap. The IR report retains its empty new-function schema;
an in-memory metadata adapter binds its 35 reused bodies to exactly 1,453
canonical instruction windows. Both reports retain the earlier data exclusions
without adding any. All 54 prior reports and their policies remain selected.
The unchanged
[`inventory_reverse_parameter_construction.py`](../tools/inventory_reverse_parameter_construction.py)
binds 107 reused declarations and the exact union of both parent instruction
corpora. It checks the three direct-call instructions and their executed target
entries, separate joined/loaded gaps and all inherited static roles, including
duplicates. Every prior code/data rule and all 56 preceding reports remain.
The unchanged [`inventory_reverse_storage_control.py`](../tools/inventory_reverse_storage_control.py)
adds five exact embedded data spans, bound to four complete consumers and sixteen
decoded proof sites. It authenticates all 45 whole bodies, direct platform-call
sites and coverage gaps. The reset witness stays auxiliary, BSS stays mutable,
and terminal polling timeouts remain distinct from instruction coverage. All
57 preceding reports and every earlier code/data rule remain selected.
The unchanged [`inventory_reverse_storage_coordination.py`](../tools/inventory_reverse_storage_coordination.py)
binds nine new and one reused complete body, every canonical visited PC, nine
direct platform sites and three calls to the existing rate helper. Five CPU
instructions and their complete primary ISA records are independently decoded
and authenticated. The eight-byte initial IRQ witness remains auxiliary mutable
state. No new data exclusion is added; all 58 preceding reports remain selected.
The unchanged [`inventory_reverse_sample_processing.py`](../tools/inventory_reverse_sample_processing.py)
binds seven new bodies and nine named reused bodies to complete canonical
decodings. Its 22,919 loaded instruction windows are the exact union of the
processing, construction and audio parents plus the seven new bodies. Ten
dispatcher joins and three internal numerical calls execute their real callees.
Three complete consumers and 45 decoded proof sites establish exactly two
twenty-word correlation blocks. Raw updater reads retain their previous data
roles without enlarging that table. All 59 preceding reports remain selected.
The unchanged [`inventory_reverse_storage_runtime.py`](../tools/inventory_reverse_storage_runtime.py)
retains the empty new-function declaration and authenticates 75 exact named
parent bodies. Its 2,283 windows match their complete canonical instruction
union. All eighteen joined call sites and callee entries are exercised;
35 remaining platform sites retain their original ABIs. Five existing tables,
five CPU/ISA records and two auxiliary witnesses retain their earlier roles.
All 60 preceding reports remain selected, with no new data exclusion.
The new [`inventory_reverse_effect_setup.py`](../tools/inventory_reverse_effect_setup.py)
authenticates 45 new bodies, 144 named reused roles and the exact loaded union
of the parameter and IR parents plus the newly loaded bodies. Eight complete
consumers and callers establish four precise table/alignment spans. The
four-halfword table supersedes exactly eight bytes of an earlier unknown prefix;
the adjacent two bytes and every other unknown span keep their earlier roles.
Ten direct calls and their callee entries execute, while eleven new indirect
sites retain their original external callback ABIs. All 61 previous reports,
their source bytes and their separate coverage results remain selected.
Generated reports remain outside Git: the unchanged baseline is
`build/reverse-inventory-01/inventory.json`, and the current snapshot is
`build/reverse-inventory-20/inventory.json`. Snapshots `-02` through `-19` are also
preserved. Each manifest records its report hash.
No device access, hardware/audio test, firmware build or installation is performed
by this inventory.

## What is counted

| Evidence class | Meaning | Baseline | Snapshot -03 | Snapshot -04 | Snapshot -05 | Snapshot -06 | Snapshot -07 | Snapshot -08 | Snapshot -09 | Snapshot -10 | Snapshot -11 | Snapshot -12 | Snapshot -13 | Snapshot -14 | Snapshot -15 | Snapshot -16 | Snapshot -17 | Snapshot -18 | Snapshot -19 | Current -20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Reconstructed function region | An exact original range with compilable C and recorded comparisons within the module's documented domain | 88 | 106 | 126 | 145 | 168 | 202 | 226 | 287 | 306 | 331 | 340 | 389 | 400 | 400 | 445 | 454 | 461 | 461 | 506 |
| Separate parser fragment | Compared parser subsection outside a reconstructed whole parent | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Separate command fragment | Compared command continuation outside a reconstructed whole parent | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Archived contained fragment | Prior fragment evidence inside a complete parent; adds no function or bytes | 0 | 0 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| Explicit return-only annotation | Report marks an exact single-RTS body; included in the function total | 0 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| Distinct active regions | Function regions plus separate fragments, with no overlapping bytes | 90 | 110 | 126 | 145 | 168 | 202 | 226 | 287 | 306 | 331 | 340 | 389 | 400 | 400 | 445 | 454 | 461 | 461 | 506 |
| Partial Ghidra entries | Automatic G v2 labels without a full endpoint inventory or semantic validation | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 | 260 |
| Linear direct-call target candidates | Distinct in-range targets after known-data and invalid-target exclusions | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 |
| Combined candidate entries | Union of call targets, partial Ghidra labels, reconstructed entries and reset entry | 2,218 | 2,218 | 2,219 | 2,220 | 2,222 | 2,223 | 2,225 | 2,226 | 2,226 | 2,226 | 2,227 | 2,227 | 2,227 | 2,227 | 2,227 | 2,227 | 2,227 | 2,227 | 2,227 |
| Candidates outside reconstructed regions | Candidate entries without a reconstructed range; **not** confirmed remaining functions | 2,130 | 2,112 | 2,093 | 2,075 | 2,054 | 2,021 | 1,999 | 1,939 | 1,920 | 1,895 | 1,887 | 1,838 | 1,827 | 1,827 | 1,782 | 1,773 | 1,766 | 1,766 | 1,721 |
| Unreconstructed direct dependency targets | Direct callees whose bodies are outside reconstructed ranges | 35 | 40 | 42 | 39 | 38 | 92 | 94 | 121 | 112 | 111 | 108 | 102 | 101 | 101 | 102 | 96 | 90 | 90 | 82 |
| Indirect call sites inside reconstructed regions | Call instructions whose targets require runtime context | 4 | 4 | 4 | 4 | 9 | 13 | 19 | 29 | 32 | 35 | 41 | 41 | 41 | 41 | 41 | 41 | 41 | 41 | 52 |

Candidate categories overlap before taking their union. The 2,227 candidate
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
candidate entry. Snapshot `-12` adds the copy-constructor wrapper at
`0x02031bf8`, which was absent from the older candidate sources.
These are concrete
examples of why the candidate count is not a complete function denominator.

The current 506 active ranges span 111,404 original bytes, including 574 bytes
of embedded branch tables/alignment. The tool decodes 35,617 instructions
after excluding those data bytes. The separate
36-byte IR coefficient table, 3,360-byte parameter metadata, 64-byte accelerator
tables, two FIR tables totaling 30 bytes and 40-byte stage-capability table add
no function or reconstructed-code bytes. Snapshot `-09` adds another 458
external data bytes from the new modules and 216 previously verified table
bytes; these likewise add no function or reconstructed-code bytes.
The four archived fragments span 394 bytes already included in their parents.
Snapshot `-10` spans 76,542 bytes and 24,825 instructions, including 414 embedded
data bytes. Snapshot `-11` spans 84,130 bytes and 27,011 instructions, adding
84 embedded data bytes and 89 external table bytes. Snapshot `-12` adds 1,138
function bytes and 422 instructions, with no additional data exclusions.
Snapshot `-13` adds 10,818 function bytes and 3,081 instructions, with eight
embedded table bytes and 661 external data bytes. The 669 new data bytes form
sixteen exact spans; alignment and unread prefixes/suffixes remain unclassified.
Snapshot `-14` adds 1,926 function bytes and 677 instructions with no additional
data exclusions. Its IR integration contributes no new region or code bytes.
Snapshot `-15` adds integration evidence only, retaining all region, instruction
and data-exclusion counts from `-14`.
Snapshot `-16` adds 3,444 function bytes and 1,165 instructions, with 32 embedded
data bytes: 29 branch entries and three zero padding bytes across five spans.
All four complete consumers and sixteen index/dispatch proof sites are decoded
independently. The separate 22-byte BSS-reset witness adds no function or data
exclusion. That snapshot has 62 known data spans; the preceding 57 are unchanged.
Snapshot `-17` adds 578 function bytes and 178 instructions, with no new data
exclusion. The 62 data spans remain unchanged. Its eight initially zero IRQ bytes
are mutable runtime state and add neither immutable data nor function bytes.
Snapshot `-18` adds 4,082 function bytes and 1,324 instructions. The only new
data exclusion is the external 160-byte correlation-weight table, bringing the
total to 63 spans. Its two auxiliary raw-index witnesses preserve existing
classification and add no reconstructed-code or table bytes.
Snapshot `-19` adds no function or data bytes. Snapshot `-20` adds 5,288
function bytes and 1,759 decoded instructions. Its four new data spans add
36 embedded bytes and 68 external bytes, giving 67 spans in total. The
two-byte auxiliary raw-read tail remains outside those exclusions.
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
| [Resource recovery and ownership integration](EFFECT_RESOURCE_OWNERSHIP_RECONSTRUCTION.md) | 0 | `build/reverse-effect-resource-ownership-03/verification.json` |
| [Constructor-to-signal integration](EFFECT_CONFIGURED_SIGNAL_RECONSTRUCTION.md) | 0 | `build/reverse-effect-configured-signal-02/verification.json` |
| [IR effect lifecycle](IR_EFFECT_LIFECYCLE_RECONSTRUCTION.md) | 9 | `build/reverse-ir-effect-lifecycle-01/verification.json` |
| [Effect model construction](EFFECT_MODEL_CONSTRUCTION_RECONSTRUCTION.md) | 49 | `build/reverse-effect-model-construction-03/verification.json` |
| [Preset storage preparation](PRESET_STORAGE_PREPARATION_RECONSTRUCTION.md) | 11 | `build/reverse-preset-storage-preparation-02/verification.json` |
| [IR numerical integration](IR_EFFECT_NUMERICAL_RECONSTRUCTION.md) | 0 | `build/reverse-ir-effect-numerical-02/verification.json` |
| [Parameter-constructor integration](EFFECT_PARAMETER_CONSTRUCTION_RECONSTRUCTION.md) | 0 | `build/reverse-effect-parameter-construction-02/verification.json` |
| [Storage control](STORAGE_CONTROL_RECONSTRUCTION.md) | 45 | `build/reverse-storage-control-01/verification.json` |
| [Storage coordination](STORAGE_COORDINATION_RECONSTRUCTION.md) | 9 | `build/reverse-storage-coordination-01/verification.json` |
| [Effect sample processing](EFFECT_SAMPLE_PROCESSING_RECONSTRUCTION.md) | 7 | `build/reverse-effect-sample-processing-01/verification.json` |
| [Storage runtime integration](STORAGE_RUNTIME_RECONSTRUCTION.md) | 0 | `build/reverse-storage-runtime-01/verification.json` |
| [Effect creation, allocation and tempo](EFFECT_SETUP_RECONSTRUCTION.md) | 45 | `build/reverse-effect-setup-03/verification.json` |
| **Current function total, including baseline** | **506** | |

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
stop the audit for explicit review. The 465 deduplicated evidence records therefore
describe 506 active regions and four archived fragments, not 510 functions.

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

Resource/ownership integration visits 1,476/1,732 joined and 3,131/15,749
loaded instructions, preserving all 256 joined gaps in its appendix. Its 35
fourth-read prefixes include the scene busy flag and live allocation flag.
Constructor-to-signal integration visits 3,120/19,023 loaded instructions;
constructor 264/971, all-pass 395/415, gate 113/117 and filter 176/176 remain
separate per-body observations. These integrations add no functions and do not
add previous execution counts to their own coverage.

IR lifecycle visits all 422 new and all 537 loaded instructions. Its three
fixed-PC observations compare finite execution prefixes; twelve other API
guards are C-only checks. Preparation and construction remain explicit direct
services, so their ABI-only byte bindings add no new functions or execution
coverage. No hardware or audio test is inferred.

Model construction visits 3,076/3,081 new and 3,441/4,775 loaded instructions.
Its five new gaps retain explicit static arguments: nonnegative pole rounding,
the earlier count bound of 33 before a clamp at 48, and three group-one paths
excluded by the pinned record group bytes `[0, 2, 0, 0]`. The 1,329 inherited
gaps remain separate. All six formerly external numerical builder calls execute
recovered code in this corpus; that is distinct from every effect's numerical
sample processing or parameter-caller integration.

The model data audit binds record field offset 58 to its actual load through
the cached record pointer. Only sixteen halfword lengths and two feedback
words are reached by the non-single group. Twenty bytes of unused suffix,
the unused mode-two index-zero entries and ten alignment bytes remain
unclassified. The separate sixteen-byte group-one table has a static original
consumer but is not dynamically validated.

Storage preparation visits 675/677 new and 938/940 loaded instructions. The two
new gaps are statically excluded by the actual block mapper and paired-address
invariant. All ten reused bodies are fully visited in this corpus. Its invalid
footer no-store behavior and original private-buffer initialization are retained
through callback mutations; the comparisons do not establish physical storage.

IR numerical integration visits 1,418/1,453 loaded instructions, including
507/537 lifecycle/shared instructions and 911/916 numerical instructions. All
35 gaps remain inherited corpus observations. The three lifecycle call sites
execute actual preparation and convolution construction, including the retry.
Known producers execute their original bodies; other callback tokens remain
explicit services. The nine API/mapping/work guards are C-only checks, with no
new native failure-prefix claim. No function or data exclusion is added.

Parameter construction visits 5,741/6,507 named joined instructions and
7,469/20,072 loaded instructions. The 766 joined and 12,603 loaded gaps remain
separate, with no inherited execution counts added. Its 625 comparisons cover
all three actual direct constructor sites, temporary-record live pointers,
resource recovery, scene/stage callers and callback-token collisions. The
35 ownership failure-prefix comparisons retain their earlier exact boundary;
27 API guards and eight additional sanitizer scene guards are C-only checks.
The 54 named static bindings cover 51 distinct spans and 5,380 union bytes;
duplicate roles do not add data exclusions or function entries.

Storage control visits 1,164/1,165 new instructions in 626 comparisons. The sole
gap is the fatal self-loop at `0x02002b7e`, observed before execution after both
fatal services return. The 50,000,000-iteration transfer timeout and
5,000,000-iteration busy timeout are not run to exhaustion. Shared instruction
coverage does not establish those outcomes. Original counters, raw address/count
arithmetic and ignored error results are retained. MMIO, cache/barrier,
scheduling, IRQ and cross-core behavior remain synthetic observations; event
prefix comparisons do not establish physical completion or durability.

Storage coordination visits all 178 new and 184 combined instructions in 442
comparisons, including the existing rate helper. Twenty-eight finite event/service
prefix cases retain earlier CPU/RAM effects and untouched outputs. CLI/STI change
only ICFG bit 9; TESTSET writes one byte and derives flags from its old low nibble;
CNUM remains a supplied context word with wrapped counter-address arithmetic.
Those explicit observations do not establish atomicity, interrupt delivery,
scheduler progress or real-time behavior. No code/data classification is inferred
from the auxiliary initial IRQ values.

Sample processing visits 1,304/1,324 new and 4,469/22,919 loaded instructions
in 768 comparisons. All ten direct dispatcher sites and three numerical calls
execute. Twenty transition instructions remain excluded by reviewed full-entry
invariants: three signed-magnitude gates, a positive-energy requirement and the
pinned model's nonfinite floating conversion followed by its rejecting phase
gate. The 18,450 loaded gaps are preserved without borrowing earlier execution
counts. Constructor preparation is a separate invocation; 148 actual constructor
calls feed 432 retained allocation chains and 336 carried calls. Raw byte-mapped
counts, aliases, callback-visible writes and private Q28 caches retain their
documented domains. Finite work/mapping guards and controlled platform services
do not establish physical audio, timing or arbitrary native stop prefixes.

Storage runtime visits 1,701/2,283 existing instructions in 135 comparisons.
All eighteen direct joins execute in one original register, stack, RAM and CPU
context. Its 582 unvisited instructions remain explicit at instruction and
complete-function level; no parent execution counts are borrowed. Sixty-six
matched portable-failure cases preserve earlier public effects and observation
order. Internal read/program arguments grant bounded private payload leases;
platform, MMIO and CPU callbacks retain public-only views. Only completed driver
stores establish private-byte initialization. A native read can report success
without writing its destination, so a later unknown private read stops at an
explicit knowledge guard. Shared service/event allowances and first-fault
preservation remain distinct from the C-only work limits. Synthetic bus behavior
does not establish physical transfer completion, durability or scheduling.

Effect setup visits 1,758/1,759 new instructions in 4,229 comparisons. Its
189 named new/reused roles cover 9,761 distinct instructions, of which 8,164
execute. The complete loaded corpus visits 8,518/22,289 instructions. The
1,597 joined and 13,771 loaded gaps remain explicit and are not filled by
coverage from earlier corpora. All ten actual direct joins execute their
complete callees; all eleven new indirect sites remain external callbacks,
including numeric tokens equal to reconstructed entries.

The only unvisited new instruction, `0x0202e3b6`, assigns positive saturation
after a fixed sine calculation. The initializer uses all 256 fixed indices;
every recorded original result is below 1.0. Independent review reproduced
the exact results through the earlier frozen sine machine in 19,968 original
steps, with no external calls or mapped-state changes. This establishes the
fixed-input exclusion under pinned execution semantics, not executed coverage
or a new hardware floating-point test. Raw segment indices retain their signed
native behavior and do not acquire an artificial normal-caller count limit.

Four new data spans total 104 bytes: 35 branch-table bytes, one alignment byte,
fifteen words and four halfwords. The exact proof uses eight complete consumers,
41 report use-site records and seven additional decoded mode/count/loop sites.
The halfwords at `0x0203b4ae..0x0203b4b6` replace eight bytes of inventory `-13`'s
previous unknown prefix. Its `0x0203b4b6..0x0203b4b8` tail stays unclassified;
a raw index-13 read binds those bytes only as auxiliary evidence. The current
report explicitly records this supersession and scopes the older model-policy
audit to its original snapshot. No frozen earlier report or tool is rewritten.

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

- All 506 active region hashes and four archived fragment hashes against the pinned image.
- **464 distinct source hashes** recorded by the 62 selected reports.
- **1,089 generated artifact hashes** from the completed build manifests.
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
source hashes and 582 artifacts. The current report captures all eighteen inventory-tool hashes;
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
branch packet starts, padding and known-data boundaries. The integration adapter
adds 89 checks for empty declarations, loaded-window bounds, canonical parent
instruction starts/sizes, complete-function parents, coverage consistency, prior
auxiliary bindings and retention of all fifty previous reports. Its independent
review caught and closed acceptance of a decodable mid-instruction window and a
fragment-only parent; every actual configured-signal window also passed the
stronger canonical check. The model adapter adds 404 checks for exact table
declarations, complete consumer hashes and decoded use sites, branch packet
starts, immutable record fields, untouched surrounding bytes, canonical merged
windows, new/reused coverage and retention of every prior report. Independent
review found no further issue.
The lifecycle adapter adds 101 checks for exact new/reused body identity,
canonical instruction windows, coverage/gap consistency, the unchanged IR table,
empty new-function declarations and retention of all 54 prior reports.
Independent review reproduced both modules' counts against prior regions and
found no further issue.

The parameter-constructor adapter adds 83 checks for parent body identity,
the exact loaded instruction union, separate joined gaps, inherited static
roles, decoded direct calls and preservation of all 56 reports. Independent
review caught a consistency gap between positive call counts and unvisited
call/entry PCs. Both conditions are now rejected, including fixtures whose
other coverage counters remain internally consistent; the recheck passed.

The storage-control adapter adds 192 checks for exact tables, complete consumers,
packet-start targets, all sixteen direct service sites, retained reports,
coverage gaps, timeout outcomes and the auxiliary reset witness. Independent
review found no further provenance, overlap or coverage inconsistency.

The storage-coordination adapter adds 200 checks for exact new/reused bodies,
canonical visited addresses, all platform/rate sites, original CPU instructions,
primary ISA records, auxiliary initial-state bytes and all 58 retained reports.
Independent review found no further provenance or classification gap.

The sample-processing adapter adds 176 checks for canonical windows, complete
body coverage, exact parent unions, static roles, all thirteen direct calls,
twenty invariant gaps and preservation of all 59 earlier reports. Independent
review caught an overly broad rejection of the raw index-2 witness, which
overlaps the existing selector table at `0x0203b880..0x0203b8d4`. The corrected
audit preserves that exact earlier classification; index 255 remains
unclassified. Neither raw witness adds or enlarges a data exclusion.

The storage-runtime adapter adds 564 checks for exact inherited body identities,
canonical instruction windows, visited/gap consistency, all eighteen direct
joins and their visited callee entries, remaining platform ABIs, table/CPU
provenance and unchanged auxiliary roles. Independent review found no further
semantic audit gap. The first full inventory run caught a missing module
coverage-notes field required by the older adapter chain; adding that metadata
preserves the existing sources and report. All 60 earlier reports are retained.

The effect-setup adapter passes 375 checks for complete-body identity, exact
loaded unions, distinct new/joined/loaded coverage, direct calls and executed
callee entries, source ancestry, table extents, consumer proofs and retained
unknown spans. Its consistent missing-callee negative case keeps positive call
counters and all other coverage counts valid. Independent review found no
further gap in the audit. All 61 preceding reports remain selected.

This mixed new/reused report is inserted explicitly after the older report
readers. Their original integration schema equates the joined instruction
domain with declared new functions. The new adapter records the larger joined
domain and its gaps without changing those readers or the frozen report.

Snapshot `-12` records **1,276 input hashes**; a separate read-back audit
checked every input and the generated manifest. All **1,149 prior input bindings**
from snapshot `-11` are retained unchanged. That preceding snapshot checked
362 source hashes and 718 artifact hashes. The manifests and report hashes of
snapshots `-01` through `-11` also remain valid.
Snapshot `-13` records **1,331 input hashes**, independently read
back after the audit, and preserves all **1,276 prior bindings**. It adds the
model sources, completed artifacts and new adapter. All thirteen inventory
manifests still match their report hashes. The new target object and all 39
unchanged reused target objects were independently checked against the preceding
model candidate and frozen construction evidence respectively.

Snapshot `-14` records **1,396 input hashes**, independently read
back after generation, and retains all **1,331 prior input bindings** unchanged.
All fourteen inventory manifests still match their reports. The 57 data
exclusions are identical to snapshot `-13`. All 22 inherited target objects
from the two new module builds match their frozen predecessors; all thirteen
IR numerical target objects also match the preserved candidate build. The
combined module evidence contains 345 original/C comparisons, 345 sanitizer
replays and 30 focused tests, within the two modules' separate domains.

Snapshot `-15` records **1,455 input hashes**, independently read
back after generation, and retains all **1,396 prior input bindings** unchanged.
All fifteen inventory manifests match their reports. Its dependency graph,
candidate entries and 57 data exclusions are unchanged from `-14`. All 43
inherited target objects match the frozen parents; all 44 target objects and
the numerical library also match the unselected earlier candidate. The new
integration contributes 625 comparisons and sanitizer replays, with 18 focused
tests and its separately documented guard checks.

Snapshot `-16` records **1,471 input hashes**, independently read
back after generation, and retains all **1,455 prior input bindings** unchanged.
All sixteen inventory manifests match their reports. The 57 previous data spans
are retained exactly, with five new embedded spans. The new module's 64 source
and seven artifact bindings also passed independent read-back. Its 626 original
comparisons and sanitizer replays, twenty focused tests, 81 API checks and
thirteen additional sanitizer guards passed within the documented domain.

Snapshot `-16` report SHA-256:
`fcf6d314599f8d9cc6a9e835b121c9db9f633bb09bb6206e22ead9c026d9a53c`.
Snapshot `-16` manifest SHA-256:
`89a1e510012508a141cfa6afb7acc56851e93efea9d7042b9f37f8b05af0e5bf`.
Storage-control inventory adapter SHA-256:
`38674dc56a964dbf2d1e82e50769375a4e9cb1c67d64fdc0799d2ce9e9af3486`.

Snapshot `-17` records **1,493 input hashes**, independently read
back after generation, and retains all **1,471 prior input bindings** unchanged.
All seventeen inventory manifests match their reports. The 62 data spans,
candidate-address union and 41 indirect sites are unchanged. The coordination
module's 78 source and thirteen artifact bindings passed independent read-back;
all six reused target objects match storage-preparation `-02`. Its 442 comparisons
and sanitizer replays, 24 focused tests, 51 API checks and thirteen additional
sanitizer guards passed within the documented domain.

Snapshot `-17` report SHA-256:
`8ff55f38329c5721a5197b5029af8f89e26a792439f66e1c124eab255275b7d7`.
Snapshot `-17` manifest SHA-256:
`ad0848dc8edb8bb062896697e817f1032ff7ca5c0fa1f250cf1f093ca75dfb86`.
Storage-coordination inventory adapter SHA-256:
`033417b8bef843423b119e37585fad74e7226e846c87206af001ac7bb78d4cb4`.

The current `-18` snapshot records **1,549 input hashes**, independently read
back after generation, and retains all **1,493 prior input bindings** unchanged.
All eighteen inventory manifests match their reports. The 62 prior data spans
are retained exactly; only the 160-byte correlation-weight table is added.
Candidate addresses and the 41 indirect sites are unchanged. All 162 source
and 47 artifact bindings in the new module passed independent read-back, and
all forty reused pi32v2 objects match their frozen predecessors. The module's
768 comparisons and sanitizer replays, fifteen focused tests and twenty
separate C-only guard checks passed within the documented domain.

Snapshot `-18` report SHA-256:
`03e9489b508087620abd3bc43c211f740cf6511444fa06ea07d359900c1c7c16`.
Snapshot `-18` manifest SHA-256:
`94c555e3fd16ddb7b58b9d340daa6f26f6b8285809641e8d4831bb85912db44c`.
Sample-processing inventory adapter SHA-256:
`4b5e9047193fd6226567d7e8245a7028cbc2788aefd70951d6baa3023ee98c25`.

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
Snapshot `-12` adds configured-signal `-02`, resource/ownership `-03` and IR
lifecycle `-01`. The first two add integration evidence only. The IR report adds
nine complete bodies, with six helpers reused and two callee ranges bound only
as ABI evidence. Snapshot `-13` adds model-construction `-03`, whose 76
declared bodies contain 49 new and 27 exact reused regions. Its thirteen merged
instruction windows are authenticated against complete-function decoding.
Snapshot `-14` adds storage-preparation `-02` and IR numerical `-02`. The former
adds eleven bodies and reuses ten; the latter declares no new function and
reuses 35. Its metadata names are adapted only in memory, with every loaded
window checked against complete original functions. Snapshot `-15` adds
parameter-constructor `-02`, retaining its empty new-function declaration and
107 exact reused bodies. Its 20,072 loaded windows equal the exact union of the
two frozen parent corpora. Candidate `-01` remains unselected because its extra
sanitizer fixture lacked immutable table mappings; `-02` corrects that fixture
with no change to the numerical library or target objects. Snapshot `-16` adds
storage-control `-01`, including all 45 complete bodies and only the five proved
embedded table/padding spans. Further storage integration, coordination and
sample-processing work remain outside that snapshot. Snapshot `-17` adds
storage-coordination `-01`, with nine new bodies and the exact existing rate
helper. Initial IRQ bytes remain auxiliary, and storage integration and further
sample-processing work remain outside that snapshot. Snapshot `-18` adds
sample-processing `-01`, with seven new numerical bodies and exact existing
constructor, processing and audio dependencies. Storage-runtime integration,
effect setup and the complete type-29 engine remain outside the current set.

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
| Command output | Formatting `0x02007010`, report helper `0x0200a768` |
| Audio and effect numerical processing | `0x01c012d8`, `0x01c01de4`, `0x01c0ddae`, `0x01c11d06` and other numerical leaves; dispatcher, individual/group wrappers and stage orchestration are now recovered |
| Storage/platform services | Clock `0x01c04862`, polling `0x0203ea6e`, wait `0x0203feb8` and device-facing platform bodies; controller and coordination bodies now have standalone evidence |
| Memory/platform services | Allocator/free, bounded memory-library contracts, notification and mode services |

IR preparation and convolution construction now execute recovered code through
the numerical integration corpus. The earlier lifecycle report retains its
explicit service boundaries as frozen evidence; the new report supplies the
join without counting existing functions again.

This list is a snapshot. A subsequent report can replace some of these boundaries
with reconstructed code while exposing new dependencies. An indirect call site
can correspond to multiple targets, and a function body can depend on hardware
or concurrency beyond its immediate call graph. The list therefore does not
enumerate every function still needed to finish the firmware. Earlier snapshots counted
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
`0x0202df84`, `0x0202df90` and `0x0202ebcc`, giving 35 sites in that snapshot.

Snapshot `-12` closes the direct boundaries at `0x0202983a`, `0x020298ce` and
`0x02029afc`, bringing the total to 108 without exposing a new direct target.
The IR bodies add six indirect sites: `0x020297ac`, `0x020297c8`, `0x020297d2`,
`0x02029996`, `0x02029ac8` and `0x02029ad6`. Their current total is 41.
Both integration reports retain their existing regions and dependencies;
separate constructor/process invocations do not invent a native call edge.

Snapshot `-13` closes six direct targets: `0x0202b838`, `0x0202b87e`,
`0x0202ba90`, `0x0202a872`, `0x0202cd32` and `0x0202cf5a`. It exposes
no new direct dependency or indirect call site, giving 102 and 41 respectively.
Every one of the 49 new entries was already a candidate, so the candidate union
remains 2,227; candidates outside reconstructed ranges fall to 1,838.

Snapshot `-14` closes the direct preparation target at `0x020031d4` and exposes
no new direct dependency or indirect call site, giving 101 and 41 respectively.
All eleven new entries were already candidates; the union remains 2,227 and
candidates outside reconstructed ranges fall to 1,827. The IR integration adds
call-path evidence without changing the region-based dependency counts.

Snapshot `-15` joins the direct parameter-constructor calls at `0x0202f37c`,
`0x0202f970` and `0x0202f7ba`. Their targets already had complete reconstructed
bodies. The inventory therefore retains 101 unresolved direct targets and
41 indirect sites, with no new function or candidate entry.

Snapshot `-16` closes eight direct targets: `0x02002772`, `0x02002786`,
`0x020027e4`, `0x02002806`, `0x02002810`, `0x02002b80`, `0x02002bcc`
and `0x02002ef2`. It exposes nine platform targets: `0x01c01108`, `0x01c011da`,
`0x020005ac`, `0x0200096e`, `0x0203e742`, `0x0203ea6e`, `0x0203fb92`,
`0x02040614` and `0x0204074c`. The remaining direct-target count is therefore
102. The 41 indirect sites and 2,227 candidate addresses are unchanged;
candidates outside reconstructed ranges fall to 1,782. These counts describe
the current graph, not a complete set of remaining firmware functions.

Snapshot `-17` closes six direct targets: `0x02002920`, `0x02002bec`,
`0x02002bf6`, `0x02002d06`, `0x02002d10` and `0x02002d70`. It exposes
no new direct dependency, leaving 96. All nine new entries were already
candidates, so the union remains 2,227 and candidates outside reconstructed
ranges fall to 1,773. The 41 indirect call sites remain unchanged.

Snapshot `-18` closes six direct targets: `0x01c08b3e`, `0x01c0b5d6`,
`0x01c0ba14`, `0x01c0bbce`, `0x01c0bd8c` and `0x01c18f90`. The seventh
new body, correlation at `0x01c19448`, is reached by the newly reconstructed
updater. No new unresolved target is exposed, leaving 90. All seven entries
were already candidates: the union remains 2,227 and candidates outside
reconstructed ranges fall to 1,766. The 41 indirect sites remain unchanged.

Snapshot `-19` retains exactly the same regions, data spans, candidates and
dependency graph. Its new evidence joins existing storage bodies rather than
adding function declarations. All 1,579 input hashes read back successfully;
the 1,549 prior input bindings and all nineteen snapshot manifests are unchanged
and valid.

Snapshot `-20` closes eight direct targets: `0x02028cb2`, `0x02028de8`,
`0x0202def2`, `0x0202e328`, `0x0202e3ce`, `0x0202e710`, `0x0202ea90` and
`0x0202f46c`. It exposes no new unresolved direct target, leaving 82. All 45
new entries were already candidates, so the address union stays at 2,227 and
the number outside reconstructed ranges falls to 1,721. Eleven new indirect
sites bring that count to 52: eight progress calls, two allocation queries and
one failure notification. Their callback arities remain explicit.

All 1,642 current input hashes read back successfully, including every one of
the 1,579 prior bindings unchanged. All twenty inventory manifests are valid.
Every earlier whole-function record and all 63 preceding data-span records are
unchanged. The four new spans bring the data-span total to 67; the separate
supersession record explains exactly which formerly unknown bytes now have
consumer evidence.

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

The effect-setup adapter retains the entire inventory `-19` report set
and requires frozen effect-setup `-03`. Configured-signal `-02`, IR
numerical `-02` and parameter-constructor `-02` retain their empty function schemas;
model-construction `-03` retains its original hash field. Use a fresh output
directory to reproduce the current `-20` evidence:

```powershell
python -B tools/inventory_reverse_effect_setup.py --self-test
$inventoryArguments = @(
    "--output", "build/reverse-inventory-effect-setup-new",
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
    "--add-report", "build/reverse-effect-ownership-01/verification.json",
    "--add-report", "build/reverse-effect-resource-ownership-03/verification.json",
    "--add-report", "build/reverse-ir-effect-lifecycle-01/verification.json",
    "--configured-signal-report", "build/reverse-effect-configured-signal-02/verification.json",
    "--model-report", "build/reverse-effect-model-construction-03/verification.json",
    "--add-report", "build/reverse-preset-storage-preparation-02/verification.json",
    "--ir-numerical-report", "build/reverse-ir-effect-numerical-02/verification.json",
    "--parameter-construction-report", "build/reverse-effect-parameter-construction-02/verification.json",
    "--storage-control-report", "build/reverse-storage-control-01/verification.json",
    "--storage-coordination-report", "build/reverse-storage-coordination-01/verification.json",
    "--sample-processing-report", "build/reverse-effect-sample-processing-01/verification.json",
    "--storage-runtime-report", "build/reverse-storage-runtime-01/verification.json",
    "--effect-setup-report", "build/reverse-effect-setup-03/verification.json"
)
python -B tools/inventory_reverse_effect_setup.py @inventoryArguments
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
The preserved `-11` inventory report SHA256 is
`4801cbbfd78ff73cf4b836bc412840775e1d4e1ddbfffaba704f182ea7ca3e36`.
Its build-manifest SHA256 is
`485b6dadc1ea6abe06bf54cc820dcd3e3414cb4a303dd4424f54f75d7d81259a`.

The preserved `-12` inventory report SHA256 is
`b9649858ebb416d7ea68f9b1d483e58c95913301350124bbd3e79948ad15ec89`.
Its build-manifest SHA256 is
`6c2183833524a8edaf2f42aaa494ea353c2ef71b1628b675f98747f01c54e1d6`.

The preserved `-13` inventory report SHA256 is
`df8e23238dd7c6f954c49079cc84482d8b767d560c967ab2fc3d1bd56ece30f3`.
Its build-manifest SHA256 is
`9fc44af83636e1272897d0f3c925270bbf9f9902d6ff8194ee498bd1577c57a7`.

The preserved `-14` inventory report SHA256 is
`461c01eea74878f0889a1629efd2f530defef8b5c175fd0f586040641c35fac2`.
Its build-manifest SHA256 is
`264503e51cfb7512c31bb2ac74cf35589300a230a5b592f22681d734d98c188e`.

The preserved `-15` inventory report SHA256 is
`2c5c04ec3dc74bdf83512f32fcaf04aca105f9737ff7151e5055a748469f4b94`.
Its build-manifest SHA256 is
`c14757305e18b38cf9962164998c8e8852f278c724be822f66c4144539ccabb1`.

The preserved `-16` inventory report SHA256 is
`fcf6d314599f8d9cc6a9e835b121c9db9f633bb09bb6206e22ead9c026d9a53c`.
Its build-manifest SHA256 is
`89a1e510012508a141cfa6afb7acc56851e93efea9d7042b9f37f8b05af0e5bf`.

The preserved `-17` inventory report SHA256 is
`8ff55f38329c5721a5197b5029af8f89e26a792439f66e1c124eab255275b7d7`.
Its build-manifest SHA256 is
`ad0848dc8edb8bb062896697e817f1032ff7ca5c0fa1f250cf1f093ca75dfb86`.

The preserved `-18` inventory report SHA256 is
`03e9489b508087620abd3bc43c211f740cf6511444fa06ea07d359900c1c7c16`.
Its build-manifest SHA256 is
`94c555e3fd16ddb7b58b9d340daa6f26f6b8285809641e8d4831bb85912db44c`.

The preserved `-19` inventory report SHA256 is
`36cd3a5cb2fc1054689accbe9eb5afd36bb9fe5ca40fee3545c045c3b52bc379`.
Its build-manifest SHA256 is
`083c4c492253daa947467fe797496aa6cf17b995a7dd53b8aac861063763aec9`.

The current `-20` inventory report SHA256 is
`8214efe32dd11aff4b363feca19a64b07a3da44768fa249cfe4acbb9fbe8bc32`.
Its build-manifest SHA256 is
`e539b830ce0a977f192301dce638030eb9293cbcaf0d3cde99e457fe1908bdcb`.
