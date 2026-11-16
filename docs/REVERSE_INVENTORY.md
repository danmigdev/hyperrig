# Reverse engineering inventory

The current audited report set contains **106 reconstructed function regions and
four fragments**: two parser fragments and two command continuations. Four of
the function regions contain only a return instruction. A reliable percentage
of complete firmware recovery is **not yet available**: the total function
inventory, indirect call graph and division
between code and data are incomplete. Function counts also do not measure the
relative work needed for small helpers, large parsers, drivers or DSP engines.

The baseline report set associated with commit
`1b235a5a284f100e47c66b6b4ab43c48cdff10cb` contains 88 function regions and two
parser fragments. The current snapshot explicitly adds completed capture journal,
filter pipeline and capture dispatch evidence. New milestones can be added
without changing old reports; these counts describe those named snapshots.

The audit tool is [`inventory_reverse.py`](../tools/inventory_reverse.py).
Generated reports remain outside Git: the unchanged baseline is
`build/reverse-inventory-01/inventory.json`, and the current snapshot is
`build/reverse-inventory-03/inventory.json`. The intermediate `-02` snapshot is
also preserved. Each manifest records its report hash.
No device access, hardware/audio test, firmware build or installation is performed
by this inventory.

## What is counted

| Evidence class | Meaning | Baseline | Current |
| --- | --- | ---: | ---: |
| Reconstructed function region | An exact original byte range with compilable C and recorded instruction comparisons within the module's documented domain | 88 | 106 |
| Parser fragment | A compared subsection of a larger original parser, counted separately from whole functions | 2 | 2 |
| Command fragment | A compared continuation inside a larger command, counted separately from whole functions | 0 | 2 |
| Explicit return-only helper | A function containing exactly one RTS instruction; included in the function total | 0 | 4 |
| Distinct reconstructed regions | Function regions plus fragments, deduplicated by exact start/end address | 90 | 110 |
| Partial Ghidra entries | Automatically exported G v2 entry labels; no endpoint inventory or full semantic validation | 260 | 260 |
| Linear direct-call target candidates | Distinct in-range targets after excluding identified data sources and invalid targets | 2,207 | 2,207 |
| Combined candidate entries | Union of linear call targets, partial Ghidra entries, reconstructed function entries and reset entry | 2,218 | 2,218 |
| Candidates outside reconstructed regions | Entries in that union without a reconstructed region; **not** a confirmed count of remaining functions | 2,130 | 2,112 |
| Unreconstructed direct dependency targets | Distinct direct callees found inside reconstructed regions whose bodies are outside those regions | 35 | 40 |
| Indirect call sites inside reconstructed regions | Call instructions whose destinations require runtime context | 4 | 4 |

Candidate categories overlap before taking their union. The 2,218 candidate
entries are **not a denominator for a completion percentage**. Some may be data
decoded as instructions, alternate/internal entry points or duplicate semantic
functions. Other real functions can be absent because they are reached through
callbacks, jump tables, interrupts, indirect calls or entry paths not yet mapped.
An apparent register-save prologue is recorded only as a hint.

The current 110 reconstructed ranges span 16,704 original bytes, including a
ten-byte action jump table. The tool decodes 5,380 instructions after excluding
that known table. The baseline spans 15,176 bytes and 4,838 instructions.
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

The two A2 fragments are bias-conversion subsections at
`0x02032586..0x02032618` and `0x020327de..0x0203280c`. They do not count as a
reconstructed whole parser at `0x02031c64`. Portable engine orchestration and
format parsing also do not add guessed original-function entries to this table.

The current snapshot adds these completed reports to that baseline:

| Added evidence | New function regions | New fragments | Report |
| --- | ---: | ---: | --- |
| [Capture journal](CAPTURE_JOURNAL_RECONSTRUCTION.md) | 5 | 2 | `build/reverse-capture-journal-02/verification.json` |
| [Generated-coefficient pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md) | 1 | 0 | `build/reverse-biquad-pipeline-01/verification.json` |
| [Capture DSP dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md) | 12 | 0 | `build/reverse-capture-dispatch-03/verification.json` |
| **Current total, including baseline** | **106** | **4** | |

Journal evidence includes six function ranges, but its comparison helper at
`0x020282bc..0x020282f4` was already counted in the preset loader. Its append
ranges at `0x0200ab96..0x0200ac36` and `0x0200acb4..0x0200acde` are explicitly
classified as command fragments. They do not recover the entire command at
`0x0200a888`. Pipeline evidence reuses fifteen existing function ranges and adds
only the getter at `0x02028920..0x02028936`; its new batch adapter is not an
original firmware function. Dispatch includes eight substantive wrappers and
four two-byte RTS-only helpers. The original parser and memory reset remain
external services in that module.

Regions with identical boundaries are deduplicated, so inherited dependencies
are not counted again in later modules. Overlapping regions with different
boundaries stop the audit for explicit classification; adding a whole parser
must account for any already counted fragments.

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

- All 110 distinct reported region hashes against the pinned image.
- **135 distinct source hashes** recorded by the completed module reports.
- **123 generated artifact hashes** from the completed build manifests.
- Exact bytes and contiguous addresses in both linear disassembly listings.
- All selected report/input hashes, recorded as relative paths in the inventory.

The preserved baseline audit checked 90 region hashes, 115 source hashes and
95 artifact hashes. Each report captures its own inventory-tool hash. Older
journal and dispatch development runs remain preserved outside the selected
current set. The final journal report adds boundary cases and MINI read-adapter
binding; the final dispatch report binds the normalized model source. These
report updates do not add function regions or change the current counts.

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
| Capture parser and memory reset | `0x02031c64`, `0x01c12878`; preparation/dispatch wrappers now execute internally |
| IR installation and effects | `0x0202957e`, `0x020295d8`, `0x020298ce`, `0x02029afc` |
| Physical storage and scheduling | Program `0x02002ef2`, erase dispatch `0x02002b80`, reads `0x02002806` / `0x02002810`, polling/priority and clock helpers |
| Memory/platform services | Allocator/free, bounded memory-library contracts, notification and mode services |

This list is a snapshot. A subsequent report can replace some of these boundaries
with reconstructed code while exposing new dependencies. An indirect call site
can correspond to multiple targets, and a function body can depend on hardware
or concurrency beyond its immediate call graph. The list therefore does not
mean only 40 functions remain to finish the firmware. The count grew from 35 as
the new bodies exposed additional parser, reset and physical-storage edges;
that increase does not mean reconstructed work was lost.

The next inventory work is to trace entry points and callback tables from known
code, classify constant/data spans, and establish function extents with callers
and control-flow evidence. Preserve uncertain candidates until that evidence
exists. The [roadmap](REVERSE_ROADMAP.md) tracks implementation priorities.

## Reproduce or extend

With the pinned [local inputs](LOCAL_SOURCES.md), completed baseline reports and
their generated artifacts available:

```powershell
python -B tools/inventory_reverse.py --check
python -B tools/inventory_reverse.py --output build/reverse-inventory-new
```

`--check` performs the audit and prints counts without writing files. An output
directory must be new and inside `build/`; an existing result is never overwritten.
The default report set stays pinned to the named baseline commit. To include a
later module, add its completed report explicitly:

```powershell
python -B tools/inventory_reverse.py --output build/reverse-inventory-extended --add-report build/reverse-new-module-01/verification.json
```

An added report must have passing evidence for the same original image, matching
source/artifact hashes and an explicit region schema. The generated inventory
records exactly which reports were selected and which other local reports were
left outside that snapshot.

To reproduce the current snapshot with a new output directory:

```powershell
python -B tools/inventory_reverse.py --output build/reverse-inventory-current-new --add-report build/reverse-capture-journal-02/verification.json --add-report build/reverse-biquad-pipeline-01/verification.json --add-report build/reverse-capture-dispatch-03/verification.json
```
