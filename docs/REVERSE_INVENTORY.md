# Reverse engineering inventory

The current audited report set contains **202 reconstructed function regions**,
including four return-only helpers. Four earlier parser/command fragments remain
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
adding a function. The current `-07` snapshot adds 34 regions for preset
application, dynamics sample processing, IR processing and the complete
nonreturning audio task with its direct helpers. All earlier reports remain
unchanged.

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
evidence. The new
[`inventory_reverse_application.py`](../tools/inventory_reverse_application.py)
binds the exact effect-parameter metadata, accelerator tables and recording FIR
coefficients to their original consumer/caller instructions. It retains all
prior overlap, hash and coverage policies, including the distinction between
bounded executions of a nonreturning task and whole-firmware execution.
Generated reports remain outside Git: the unchanged baseline is
`build/reverse-inventory-01/inventory.json`, and the current snapshot is
`build/reverse-inventory-07/inventory.json`. Snapshots `-02` through `-06` are also
preserved. Each manifest records its report hash.
No device access, hardware/audio test, firmware build or installation is performed
by this inventory.

## What is counted

| Evidence class | Meaning | Baseline | Snapshot -03 | Snapshot -04 | Snapshot -05 | Snapshot -06 | Current -07 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Reconstructed function region | An exact original range with compilable C and recorded comparisons within the module's documented domain | 88 | 106 | 126 | 145 | 168 | 202 |
| Separate parser fragment | Compared parser subsection outside a reconstructed whole parent | 2 | 2 | 0 | 0 | 0 | 0 |
| Separate command fragment | Compared command continuation outside a reconstructed whole parent | 0 | 2 | 0 | 0 | 0 | 0 |
| Archived contained fragment | Prior fragment evidence inside a complete parent; adds no function or bytes | 0 | 0 | 4 | 4 | 4 | 4 |
| Explicit return-only helper | Exactly one RTS instruction; included in the function total | 0 | 4 | 4 | 4 | 4 | 4 |
| Distinct active regions | Function regions plus separate fragments, with no overlapping bytes | 90 | 110 | 126 | 145 | 168 | 202 |
| Partial Ghidra entries | Automatic G v2 labels without a full endpoint inventory or semantic validation | 260 | 260 | 260 | 260 | 260 | 260 |
| Linear direct-call target candidates | Distinct in-range targets after known-data and invalid-target exclusions | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 | 2,207 |
| Combined candidate entries | Union of call targets, partial Ghidra labels, reconstructed entries and reset entry | 2,218 | 2,218 | 2,219 | 2,220 | 2,222 | 2,223 |
| Candidates outside reconstructed regions | Candidate entries without a reconstructed range; **not** confirmed remaining functions | 2,130 | 2,112 | 2,093 | 2,075 | 2,054 | 2,021 |
| Unreconstructed direct dependency targets | Direct callees whose bodies are outside reconstructed ranges | 35 | 40 | 42 | 39 | 38 | 92 |
| Indirect call sites inside reconstructed regions | Call instructions whose targets require runtime context | 4 | 4 | 4 | 4 | 9 | 13 |

Candidate categories overlap before taking their union. The 2,223 candidate
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
identified it. These are concrete
examples of why the candidate count is not a complete function denominator.

The current 202 active ranges span 45,512 original bytes, including a ten-byte
action jump table and a four-byte capture-processing jump table. The tool
decodes 14,671 instructions after excluding those data bytes. The separate
36-byte IR coefficient table, 3,360-byte parameter metadata, 64-byte accelerator
tables and two FIR tables totaling 30 bytes add no function or reconstructed-code
bytes.
The four archived fragments span 394 bytes already included in their parents.
Snapshot `-06` spans 28,944 bytes and 9,563 instructions; snapshot `-05` spans
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
| **Current function total, including baseline** | **202** | |

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
stop the audit for explicit review. The 206 deduplicated evidence records therefore
describe 202 active regions and four archived fragments, not 206 functions.

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
| Joined native capture-loading instructions | 1,410 | 1,551 | 141 |
| Joined loading, warm-up and processing instructions | 3,300 | 3,670 | 370 |
| Joined IR construction and reused helpers | 907 | 916 | 9 |
| Joined IR processing and construction helpers | 2,869 | 3,182 | 313 |

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

- All 202 active region hashes and four archived fragment hashes against the pinned image.
- **263 distinct source hashes** recorded by the 36 selected reports.
- **343 generated artifact hashes** from the completed build manifests.
- Exact bytes and contiguous addresses in both linear disassembly listings.
- All selected report/input hashes, recorded as relative paths in the inventory.

The preserved baseline audit checked 90 region hashes, 115 source hashes and
95 artifact hashes. Snapshot `-03` checked 110 regions, 135 source hashes and
123 artifact hashes. Snapshot `-04` checked 130 region/fragment hashes,
164 source hashes and 160 artifact hashes. Snapshot `-05` checked 149
region/fragment hashes, 192 source hashes and 204 artifacts. Snapshot `-06`
checked 172 region/fragment hashes, 234 source hashes and 279 artifacts. The
current report captures all five inventory-tool hashes;
earlier tools and snapshots remain unchanged. Older development reports stay
outside the selected current set. Twenty-two read-only adapter checks cover
containment order, evidence deduplication, rejected unknown overlaps, bad hashes
and contradictory instruction-count/classification records. Thirteen additional
read-only runtime-adapter checks cover exact table boundaries/bytes, missing or
invalid dispatch targets, data decoded as code, and contradictory joined
instruction counts/addresses. Nineteen read-only DSP-adapter checks cover
rejected table ranges, hashes, signed words, consumer evidence and exclusion
boundaries. The new application adapter adds 113 checks for altered report
status/image binding, table ranges/hashes, metadata presence bits, complete
consumer/caller hashes, each required decoded proof site, exclusion endpoints
and the gaps between FIR tables. The final snapshot records **657 input hashes**; an independent
read-back audit checked every input and the generated manifest. The manifests
and report hashes of snapshots `-01` through `-06` also remain valid.

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
| Scene application | Scene bridges `0x0200a1d6` / `0x0200a228`; preset application `0x020092fa` is now recovered |
| Command output | Formatting `0x02007010`, report helper `0x0200a768` |
| IR effect refresh and ownership | `0x020298ce`, `0x02029afc`; direct and deferred installation are now recovered |
| Effect construction and parameter changes | `0x0202e710`, `0x0202f07e`, `0x0202f46c`, `0x02030602` and other effect-specific services exposed by preset application |
| Audio processing and routing | `0x01c012d8`, `0x01c01de4`, `0x01c04cda`, `0x01c10e06` and other signal helpers called by the task |
| Physical storage and scheduling | Program `0x02002ef2`, erase dispatch `0x02002b80`, reads `0x02002806` / `0x02002810`, polling/priority and clock helpers |
| Memory/platform services | Allocator/free, bounded memory-library contracts, notification and mode services |

This list is a snapshot. A subsequent report can replace some of these boundaries
with reconstructed code while exposing new dependencies. An indirect call site
can correspond to multiple targets, and a function body can depend on hardware
or concurrency beyond its immediate call graph. The list therefore does not
mean only 92 functions remain to finish the firmware. Earlier snapshots counted
35, 40, 42, 39 and 38 targets. Snapshot `-07` closes the old direct boundary at
`0x020092fa` while exposing 55 additional direct targets through the newly
reconstructed callers. The four additional indirect sites are all within preset
application, at `0x020097b0`, `0x020098e8`, `0x02009a52` and `0x02009ab0`.
The current 13 indirect sites also include the transition callback, IR
allocation/free services and producer dispatch; individual corpora resolve some
targets within their stated domain. These changing counts describe the explored
call graph.

An outside target means its body has no separately declared reconstructed
whole-function region in this inventory. For example, the dynamics clone
executes and binds the original copy helper at `0x01c1a14c` for its 61-word copy,
but that helper has no separate whole-function report and adds no function to
the total. Its narrower integration evidence is preserved by the dynamics
report. Conversely, a dependency absent from the direct-target list may still
be reached through an indirect callback.
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

The application adapter adds the metadata, accelerator and FIR table exclusions.
To reproduce the current `-07` evidence set with a fresh output directory:

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
The current `-07` inventory report SHA256 is
`948464bf96c4d09837537d09716ea2f95cfab78f5d0e41a0aa91d21c33b0b716`.
Its build-manifest SHA256 is
`570df7d70261e651fa39d47ee7d74c2e73599ea7c339aa80407382e67be790e2`.
