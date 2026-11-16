# Reverse engineering inventory

The current audited report set contains **126 reconstructed function regions**,
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
fragments after journal, pipeline and dispatch work. The current `-04` snapshot
adds DSP initialization, memory reset, the complete capture command and the
complete raw parser with its read helper. All earlier reports remain unchanged.

The original [`inventory_reverse.py`](../tools/inventory_reverse.py) is unchanged.
The new [`inventory_reverse_expanded.py`](../tools/inventory_reverse_expanded.py)
adapter audits the four exact fragment/parent relationships and preserves
module-level instruction gaps.
Generated reports remain outside Git: the unchanged baseline is
`build/reverse-inventory-01/inventory.json`, and the current snapshot is
`build/reverse-inventory-04/inventory.json`. Snapshots `-02` and `-03` are also
preserved. Each manifest records its report hash.
No device access, hardware/audio test, firmware build or installation is performed
by this inventory.

## What is counted

| Evidence class | Meaning | Baseline | Snapshot -03 | Current -04 |
| --- | --- | ---: | ---: | ---: |
| Reconstructed function region | An exact original range with compilable C and recorded comparisons within the module's documented domain | 88 | 106 | 126 |
| Separate parser fragment | Compared parser subsection outside a reconstructed whole parent | 2 | 2 | 0 |
| Separate command fragment | Compared command continuation outside a reconstructed whole parent | 0 | 2 | 0 |
| Archived contained fragment | Prior fragment evidence inside a complete parent; adds no function or bytes | 0 | 0 | 4 |
| Explicit return-only helper | Exactly one RTS instruction; included in the function total | 0 | 4 | 4 |
| Distinct active regions | Function regions plus separate fragments, with no overlapping bytes | 90 | 110 | 126 |
| Partial Ghidra entries | Automatic G v2 labels without a full endpoint inventory or semantic validation | 260 | 260 | 260 |
| Linear direct-call target candidates | Distinct in-range targets after known-data and invalid-target exclusions | 2,207 | 2,207 | 2,207 |
| Combined candidate entries | Union of call targets, partial Ghidra labels, reconstructed entries and reset entry | 2,218 | 2,218 | 2,219 |
| Candidates outside reconstructed regions | Candidate entries without a reconstructed range; **not** confirmed remaining functions | 2,130 | 2,112 | 2,093 |
| Unreconstructed direct dependency targets | Direct callees whose bodies are outside reconstructed ranges | 35 | 40 | 42 |
| Indirect call sites inside reconstructed regions | Call instructions whose targets require runtime context | 4 | 4 | 4 |

Candidate categories overlap before taking their union. The 2,219 candidate
entries are **not a denominator for a completion percentage**. Some may be data
decoded as instructions, alternate/internal entry points or duplicate semantic
functions. Other real functions can be absent because they are reached through
callbacks, jump tables, interrupts, indirect calls or entry paths not yet mapped.
An apparent register-save prologue is recorded only as a hint. The newly
reconstructed decimal core at `0x020283ce` was absent from both the linear
direct-call target set and partial Ghidra export; its reviewed entry adds the
new candidate. This is one concrete reason the previous candidate count was
not a complete function denominator.

The current 126 active ranges span 22,464 original bytes, including a ten-byte
action jump table. The tool decodes 7,383 instructions after excluding that known
table. The four archived fragments span 394 bytes already included in their
parents. Snapshot `-03` spans 16,704 bytes and 5,380 instructions; the baseline
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
| **Current function total, including baseline** | **126** | |

Journal evidence includes six function ranges, but its comparison helper at
`0x020282bc..0x020282f4` was already counted in the preset loader. Its append
ranges at `0x0200ab96..0x0200ac36` and `0x0200acb4..0x0200acde` remain command
fragments and are now archived inside the complete command. Pipeline evidence
reuses fifteen existing function ranges and adds
only the getter at `0x02028920..0x02028936`; its new batch adapter is not an
original firmware function. Dispatch includes eight substantive wrappers and
four two-byte RTS-only helpers. Parser and reset remain external services in the
unchanged dispatch report; their complete bodies are supplied by the new reports.
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
stop the audit for explicit review. The 130 deduplicated evidence records therefore
describe 126 active regions and four archived fragments, not 130 functions.

## Instruction execution gaps

Complete C bodies and reviewed function boundaries do not establish exhaustive
input or instruction-path coverage. The current reports explicitly leave these
new instructions unvisited:

| Report scope | Visited | Decoded | Unvisited |
| --- | ---: | ---: | ---: |
| Complete parser and read helper | 1,136 | 1,213 | 77 |
| New command/helper instructions | 531 | 545 | 14 |

The parser report classifies its 77 unvisited instructions by dominating entry
invariants: 51 guarded by minimum header length, four by minimum length for the
rechannel fraction, one by validated nonzero channels, 19 by validated convolution
shift bounds and two by validated nonzero layer count. These classifications
remain reported evidence; the inventory does not relabel those instructions
as executed or claim exhaustive input coverage.

The complete command body itself visited all 399 decoded instructions. Its 14
remaining new-helper gaps comprise four status-text instructions, two prefix
instructions and eight decimal-core instructions. Every address is retained in
the generated inventory. Other current reports with recorded new/module counts
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

- All 126 active region hashes and four archived fragment hashes against the pinned image.
- **164 distinct source hashes** recorded by the completed module reports.
- **160 generated artifact hashes** from the completed build manifests.
- Exact bytes and contiguous addresses in both linear disassembly listings.
- All selected report/input hashes, recorded as relative paths in the inventory.

The preserved baseline audit checked 90 region hashes, 115 source hashes and
95 artifact hashes. Snapshot `-03` checked 110 regions, 135 source hashes and
123 artifact hashes. The current report captures both inventory-tool hashes;
earlier tools and snapshots remain unchanged. Older development reports stay
outside the selected current set. Twenty-two read-only adapter checks cover
containment order, evidence deduplication, rejected unknown overlaps, bad hashes
and contradictory instruction-count/classification records.

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
| Preset/live application | `0x020092fa`, scene bridges `0x0200a1d6` / `0x0200a228` |
| DSP startup services | Platform input `0x01c010a6`, dynamics configuration `0x02030f8e` |
| Command output | Formatting `0x02007010`, report helper `0x0200a768` |
| IR installation and effects | `0x0202957e`, `0x020295d8`, `0x020298ce`, `0x02029afc` |
| Physical storage and scheduling | Program `0x02002ef2`, erase dispatch `0x02002b80`, reads `0x02002806` / `0x02002810`, polling/priority and clock helpers |
| Memory/platform services | Allocator/free, bounded memory-library contracts, notification and mode services |

This list is a snapshot. A subsequent report can replace some of these boundaries
with reconstructed code while exposing new dependencies. An indirect call site
can correspond to multiple targets, and a function body can depend on hardware
or concurrency beyond its immediate call graph. The list therefore does not
mean only 42 functions remain to finish the firmware. The count grew from 35 to
40 and then 42 as new bodies exposed additional dependencies while older ones
were reconstructed. Those changing counts describe the explored call graph.

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

The expanded adapter adds the seven final report sets listed above and requires
an explicit frozen parser report. To reproduce the current snapshot with a new
output directory:

```powershell
python -B tools/inventory_reverse_expanded.py --self-test
python -B tools/inventory_reverse_expanded.py --output build/reverse-inventory-current-new --parser-report build/reverse-capture-parser-03/verification.json
```

Use `--check` instead of `--output` for a read-only audit. Additional frozen
reports can be supplied with repeated `--add-report` arguments; unknown overlaps
still require explicit policy work. All generated reports stay under ignored
`build/`, and existing directories are refused.

The current inventory report SHA256 is
`6681171220c3e1c3063b8f9136aaaf806257c803d907f3d0e419a26afb72956e`.
