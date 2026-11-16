# HyperRig goal

Explicit user requirements, updated on 15 November 2026.

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

## Implementation decisions

The complete candidate uses the UltraRig G application as its base. Changes
for the MINI target are explicit, checked against the original bytes, and
documented. The experimental branch that would have inserted the DSP into the
stock MINI firmware was abandoned at the user's direction; it is not an
acceptable alternative product for this goal.

The final app retains the UltraRig protocol. The MINI target is identified by
`tankm_fw`; the stock MINI MIDI protocol remains a diagnostic and access tool
for the original firmware during development.

Work proceeds with parallel agents. The result is declared complete only after
checks on the pedal and the app, with any remaining reverse-engineering
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
