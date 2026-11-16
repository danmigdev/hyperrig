# HyperRig goal

Explicit user requirements, updated on 16 November 2026.

HyperRig is the port of the UltraRig firmware to TANK MINI, together with its
adapted applications. The final firmware replaces the stock MINI firmware.
The stock MINI application is not the product's foundation, does not host the
HyperRig engine, and is not retained as a backend. The stock sample and the
dump from the user's unit serve to reconstruct the board's characteristics and
provide a restoration source.

## Local copies and ability to modify the project

- Keep verified original copies of the UltraRig firmware and its apps,
  identifying their version, provenance, and SHA-256.
- Keep the reverse-engineering material: extractions, disassemblies,
  decompilation, formats, protocols, maps, and evidence supporting the reconstructions.
- Make the firmware and applications editable through recovered or
  reconstructed sources and reproducible compilation, reconstruction, and patch tools.
- Distinguish compilable sources from inferred pseudocode and components that
  remain binary. A binary copy or partial decompilation does not establish
  complete recovery of the original sources.
- Keep the originals separate from the HyperRig copies and preserve the
  attribution and licenses of derived components.

## Minimum working result to demonstrate

1. The TANK MINI reliably boots the HyperRig port of the UltraRig application.
2. The MINI's physical audio path processes the signal through the adapted
   firmware and UltraRig DSP components.
3. The HyperRig app recognizes the MINI target and reads and edits the adapted
   firmware's presets, with verification of responses and actual state.
4. The local repository preserves everything needed to repeat the build and
   make further changes, with an accurate description of the reconstructed
   parts and the components that still need analysis.

RAM probes, synthetic tests, simulations, and interface demos are intermediate
checks. They do not, by themselves, meet the minimum working result.

## Minimum operational result achieved on 16 November 2026

The v3 port of the UltraRig G application was installed on the MINI. Normal
boot, A2 processing, and retention of the first preset after the user's restart
have been verified; the user reported normal audio (paraphrased). Through USB,
the HyperRig editor actually added an effect, changed its parameter, bypassed
and re-enabled it, saved it to 1B, removed it, and recalled 1B: the Post Noise
Gate returned enabled with a −71 dB threshold. Finally, the original 1A preset
was recalled, with gain 0/0 and an empty FX chain.

The evidence is in `build/mini-saved-reload-ui-v2-07/report.json`,
`build/mini-fx-ui-smoke-01/report.json`, and the installation checks linked from
the README. The v3 app bundle is `build/hyperrig-mini-english-editor`,
an English presentation derived from
the preserved `build/hyperrig-mini-fx-editor` hardware-test baseline.
A separate test with nine active effects
measured approximately 2.395 ms mean internal processing time and a 2.526 ms
observed maximum, with no reported faults; total analog latency was not measured.

This completion covers the minimum defined above. The complete original C
source has not been recovered: inferred pseudocode and binary components
remain, alongside compilable reconstructions and local patch/build tools.
Testing all physical controls, routing and other editor commands not yet
enabled, and complete mobile/BLE write support remain separate work items.

The later v3-to-v4 development upgrade has complete flash readback and normal
USB boot/read evidence. A user-assisted cold start with the left footswitch
alone reached ROM and answered INQUIRY. The other individual switches, audio
listening remain untested. A later native trial verified nine USB mutation
families and preset/scene persistence on v4, then restored the original state.
The main launcher opens preview 05 with those bounded controls, A/B/C preset
banks and the MINI v4 label. See [MINI_V4_EDITOR.md](MINI_V4_EDITOR.md).
The qualified v3 bundle is preserved.
See [MINI_ONE_SWITCH_UPGRADE.md](MINI_ONE_SWITCH_UPGRADE.md).

## Current priority: reverse engineering for backports

The user prioritizes reconstructing firmware source and module contracts before
further installer feature work, to make future backports easier to integrate.
The sequence is controls/action dispatch, protocol and persistence, remaining
audio/DSP integration, and incremental source integration into the MINI port.
See the [reverse engineering roadmap](REVERSE_ROADMAP.md).

The user explicitly set completion of reverse engineering as the active goal.
Completion requires an accounted function/dependency inventory and maintainable,
compilable reconstructions of controls, protocol/persistence, capture/IR/effects,
DSP and platform/audio integration, with reproducible builds and original-code
comparisons. Individual milestones do not complete that goal. The
[inventory](REVERSE_INVENTORY.md) records measured coverage and unresolved
dependencies without inventing an overall percentage. Offline work preserves
tested firmware and does not authorize implementation of the reserved features.

The first new control milestone reconstructs the switch transition function and
immediate-action policy in C, with instruction-level comparisons and a byte
binding to the published MINI v4. The next milestone adds the action dispatcher,
timer worker and integrated event sequences, with 10,101 further comparisons.
The third milestone reconstructs preset navigation, direct/pending scene selection
and effect binding across both chains, with nine new functions and 14,631
comparisons. The fourth adds preset availability/cache validation, address
mapping, CRCs and the shared record reader: seven functions and 2,312 further
comparisons. The fifth reconstructs preset preflight and legacy layout/effect
conversion, with three functions and 1,754 comparisons. The sixth adds loader
orchestration, action snapshots/rebinding and report arithmetic, with eight
functions and 4,635 comparisons integrated with controls and preflight.
The seventh adds nine independently verified asset and routing-layout dependencies
of application, with 3,938 comparisons. In parallel, two shared recursive DSP
filters add 1,864 comparisons beyond the A2 engine, including rounding, clipping,
fractional residue and persistent history.
The eighth application milestone adds the IR loader and ownership helpers:
five functions and 541 comparisons, including payload CRCs, reuse and cleanup.
The parallel DSP chain adds two functions and 2,445 comparisons, applying staged
updates and executing all five sections with the verified numerical kernels.
The capture loader adds ten functions and 6,091 comparisons, covering packed
metadata, gain scaling, signature rejection, reuse and partial rollback. Parallel
coefficient work adds five executed regions and 11,071 comparisons for staging,
normalization and float-to-Q28 conversion, plus 6,912 binary32 division checks.
The next capture milestone reconstructs container installation and the actual
record reader, with 262 comparisons including complete slot-loader sequences.
Parallel journal/cache work adds six regions and 9,764 comparisons. The bounded
coefficient generator adds six regions and 5,542 instruction comparisons, executing
all local mathematical dependencies through staging, plus 18,069 binary32
primitive checks. Capture preparation, size/probe, DSP-load wrappers, capability
query and cleanup now add 1,847 comparisons, including integrated container/slot
paths. Journal append/rewrite adds 655 synthetic-storage comparisons. The filter
pipeline joins generation, staging and active numerical processing with 1,698
comparisons. The whole capture parser/reset bodies, complete metadata command,
broader divisor initializer and surrounding audio caller remain separate work.
Physical storage I/O and DSP application remain explicit boundaries.
These milestones do not modify the installed/released firmware or enable
unqualified editor controls; see [CONTROL_RECONSTRUCTION.md](CONTROL_RECONSTRUCTION.md),
[CONTROL_ACTIONS.md](CONTROL_ACTIONS.md),
[SELECTION_RECONSTRUCTION.md](SELECTION_RECONSTRUCTION.md),
[PRESET_STORAGE_RECONSTRUCTION.md](PRESET_STORAGE_RECONSTRUCTION.md),
[PRESET_PREFLIGHT_RECONSTRUCTION.md](PRESET_PREFLIGHT_RECONSTRUCTION.md),
[PRESET_LOADER_RECONSTRUCTION.md](PRESET_LOADER_RECONSTRUCTION.md),
[PRESET_ASSETS_RECONSTRUCTION.md](PRESET_ASSETS_RECONSTRUCTION.md),
[BIQUAD_RECONSTRUCTION.md](BIQUAD_RECONSTRUCTION.md),
[IR_LOADER_RECONSTRUCTION.md](IR_LOADER_RECONSTRUCTION.md),
[BIQUAD_CHAIN_RECONSTRUCTION.md](BIQUAD_CHAIN_RECONSTRUCTION.md),
[CAPTURE_LOADER_RECONSTRUCTION.md](CAPTURE_LOADER_RECONSTRUCTION.md),
[BIQUAD_COEFFICIENT_RECONSTRUCTION.md](BIQUAD_COEFFICIENT_RECONSTRUCTION.md),
[CAPTURE_CONTAINER_RECONSTRUCTION.md](CAPTURE_CONTAINER_RECONSTRUCTION.md),
[CAPTURE_METADATA_RECONSTRUCTION.md](CAPTURE_METADATA_RECONSTRUCTION.md),
[BIQUAD_GENERATOR_RECONSTRUCTION.md](BIQUAD_GENERATOR_RECONSTRUCTION.md),
[CAPTURE_DISPATCH_RECONSTRUCTION.md](CAPTURE_DISPATCH_RECONSTRUCTION.md),
[CAPTURE_JOURNAL_RECONSTRUCTION.md](CAPTURE_JOURNAL_RECONSTRUCTION.md) and
[BIQUAD_PIPELINE_RECONSTRUCTION.md](BIQUAD_PIPELINE_RECONSTRUCTION.md).

The user also reserved separate branches for Tone3000 integration, a zoomable UI,
and a complete UltraRig Alpha 11 versus HyperRig feature comparison after reverse
engineering. These branches are placeholders; they do not implement those changes.
Their names and scope are recorded in the [roadmap](REVERSE_ROADMAP.md#reserved-branches).

## Implementation decisions

The complete candidate uses the UltraRig G application as its base. Changes
for the MINI target are explicit, checked against the original bytes, and
documented. The experimental branch that would have inserted the DSP into the
stock MINI firmware was abandoned at the user's direction; it is not an
acceptable alternative product for this goal.

The final app retains the UltraRig protocol. The MINI target is identified by
`tankm_fw`; the stock MINI MIDI protocol remains a diagnostic and access tool
for the original firmware during development.

Work proceeds through bounded, reproducible reconstructions with explicit
dependencies and verification domains. Product behavior is declared complete
only after checks on the pedal and the app, with remaining reverse-engineering
limitations stated explicitly.

## Selected recovery method and the user's Raspberry Pi

The user ruled out USB_KEY with GPIO wiring and selected footswitch recovery.
The initial guard required all three switches; v4 accepts any single switch,
with the left-switch cold-start sequence now observed on hardware. This path
uses the verified RAM switch/reset work and a guard at the entry point of the
adapted UltraRig application. USB_KEY and its tools remain archived experimental
material, not a prerequisite imposed on the user. The guard does not cover a
damaged header or damage to its own code; this limitation is distinct from
recovery when execution hangs after entry.

The available Raspberry Pi 3 already has an operating system installed and is
used as a MIDI hub. The user requires that installation to be preserved.
Read-only compatibility checks and a build with simulation were performed in
a dedicated directory. No reinstallation, changes to MIDI services or boot
configuration, or requests for GPIO lines were made. The Pi is not needed for
the selected footswitch recovery path.
