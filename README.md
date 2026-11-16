# HyperRig

Independently maintained UltraRig-derived firmware and editor for the
M-VAVE TANK MINI.

[Repository](https://github.com/danmigdev/hyperrig) ·
[Report an issue](https://github.com/danmigdev/hyperrig/issues/new/choose)

## Current status

The minimum working system was verified on November 16, 2026:

- The UltraRig-derived v3 application is installed on the MINI, replacing its
  stock application. A complete NOR readback verified the installed bytes.
- Normal boot, A2 capture retention, preset retention after restart, and
  communication over USB and Bluetooth were observed.
- The owner reported normal audio with the instrument and output connected.
- The desktop editor was physically tested for volume, effect addition,
  parameter changes, bypass, removal, preset saving, and preset loading.
- With nine active effects, internal processing averaged about **2.40 ms per
  block**, with **2.53 ms maximum observed**. Analog input-to-output latency
  has not been measured.

The original buildable UltraRig firmware C project has **not** been recovered.
This working firmware is a port of the distributed binary, with reconstructed
MINI-specific components. The separate C reconstruction remains incomplete.
Full panel/LED mapping and the integrated held-switch cold-start recovery test
remain outstanding.

The [agreed objective](docs/HYPERRIG_GOAL.md) and
[integrated port](docs/MINI_INTEGRATED_PORT.md) document the scope and evidence.

## Launch the editor

With the MINI powered on and connected by a USB data cable, open
[launch_hyperrig_editor.cmd](tools/launch_hyperrig_editor.cmd).
No UAC prompt is needed.

The launcher dismisses the first-use tour and opens the USB selector. Choose
**Tank-M HyperRig (COM3)** on the development PC. Opening USB can take about
15–21 seconds on this PC. Use one connected editor window at a time.

The current product bundle is `build/hyperrig-mini-english-editor`.
It has an English-only interface, HyperRig GitHub links, and a **Report an
issue on GitHub** action. GitHub lets the user review and submit the issue.
Donation controls and automatic online update checks have been removed.

The English presentation changes are checked offline, separately from the
original hardware tests. They preserve the firmware binding, command policy,
converter, and eight qualified USB command families:

`GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`, `FXA`, `FXP`, `FXE`, `FXR`.

Use **+** at the end of Pre or Post to add an effect. Select a block for its
parameters, Bypass, and Remove. Use Presets to save or load. The firmware
enforces CPU and memory limits. Parallel routing, moving/replacing blocks,
AMP controls, and Bluetooth writes are outside the qualified scope.

The real UI test created **1B**, with the copied name **Preset 1A**, the A2
capture, and an enabled Post Noise Gate at **−71 dB**. Loading 1B restored the
effect after it had been removed in the editor. The pedal was left on the
original **1A**, with gain 0/0 and an empty FX chain. A further physical restart
of preset 1B was not part of that test.
[UI evidence](docs/MINI_FX_UI.md) · [Timing measurements](docs/MINI_LATENCY.md)

## Build the English editor

Python 3.12 and Node.js are required. The local, sealed
`build/hyperrig-mini-fx-editor` bundle is the input; it is not included in Git.

```powershell
npm.cmd ci --prefix tools/editor --ignore-scripts --no-audit --no-fund
python tools/build_hyperrig_editor.py --build build/hyperrig-mini-english-editor-new
python tools/verify_hyperrig_editor.py --bundle build/hyperrig-mini-english-editor-new --output build/hyperrig-english-check-new
```

Use new output directories. The builder preserves historical bundles and
hardware reports. The offline browser check blocks device access, verifies
English behavior with a non-English browser preference, checks GitHub issue
navigation without sending a report, and exercises the demo controls.

Project destinations are defined in [app/project.json](app/project.json).
All maintained documentation, UI text, comments, and new contributions use
English; see [AGENTS.md](AGENTS.md). Required third-party notices, protocol
identifiers, original inputs, and immutable evidence retain their original
wording and bytes.

## Development and reverse engineering

The repository includes parsers for SFC/JLFS/FWSC and A2L1, extracted-protocol
analysis, binary port builders, reconstructed C components, tests, board
profiles, and hardware investigation records.

Python 3.12 is needed to read the original installer's Python 3.12 bytecode.
Offline parsers use only the standard library.

```powershell
python tools/bootstrap.py
python tools/fetch_artifacts.py
python -m hyperrig analyze
python tools/disassemble.py
python tools/map_audio.py
python -m hyperrig port-status
```

Ghidra decompilation requires Java 21 or later and Ghidra 12.2. The optional
bootstrap downloads about 570 MB and installs the JieLi processor module into
the local Ghidra copy:

```powershell
python tools/bootstrap.py --decompiler
powershell -NoProfile -ExecutionPolicy Bypass -File tools/decompile.ps1 -Target tank-mini
```

Other targets are `tank-g-v1`, `tank-g-v2`, `tank-b-v1`, and `tank-b-v2`.
ExecutionPolicy applies only to that process. Analysis tools do not run the
pedal installers.

Building the reconstructed C components on Windows requires WSL Ubuntu with
GCC and Python 3:

```powershell
python tools/bootstrap.py --toolchain
python tools/build_native.py
```

This produces `build/native/hyperrig_dsp.pi32v2.o` and local verification
evidence, not a flashable firmware image. Documented DSP checks include
**7,509 comparisons against interpreted original instructions**. The working
binary port and the separate portable C engine have different completion
states; their evidence is documented separately.

Historical hardware-proof builders pin the exact source bytes used for their
tests. Reproduce those results from the recorded Git revision; translations
and later UI changes do not rewrite historical evidence.

## Local artifacts

| Path | Contents |
|---|---|
| `recovered/ultrarig-original/web/` | Original editor HTML/JavaScript and NAM converter |
| `recovered/android/` | Original APK assets and configuration |
| `recovered/installer/` | Installer bytecode, disassembly, and constants |
| `recovered/ghidra/<target>/decompiled.c` | Inferred, non-buildable C pseudocode |
| `analysis/firmware/<image>/` | Decoded binaries, maps, assembly, and captures |
| `analysis/tank-mini/` | Official MINI firmware analysis |
| `artifacts/` | Original packages and local device backups |
| `upstream/` | Reference repositories and SDK headers |
| `build/` | Generated firmware, editors, and test artifacts |

Recovered binaries, full device dumps, user presets, and generated builds
remain local and are excluded from Git. The repository versions tools,
tests, profiles, documentation, and selected evidence/source snapshots.
Historical G/B packages in `build/hyperrig/` are separate from the current
MINI product and must not be used as MINI installers.

## Documentation

- [Goal and remaining work](docs/HYPERRIG_GOAL.md)
- [Reverse engineering and verified results](docs/REVERSE_ENGINEERING.md)
- [Local sources and modification paths](docs/LOCAL_SOURCES.md)
- [Integrated MINI port](docs/MINI_INTEGRATED_PORT.md)
- [MINI board profile and porting constraints](docs/PORTING_TANK_MINI.md)
- [Reconstructed native C and numerical verification](docs/NATIVE_RECONSTRUCTION.md)
- [MINI audio path](docs/TANK_MINI_AUDIO.md)
- [MINI audio driver](docs/MINI_AUDIO_DRIVER.md)
- [Startup, linker, and diagnostics](docs/MINI_BOOT.md)
- [ROM probe](docs/MINI_ROM_PROBE.md)
- [Synthetic A2L engine in RAM](docs/MINI_ROM_ENGINE.md)
- [Complete UltraRig application port](docs/MINI_ULTRARIG_PORT.md)
- [Editor architecture](docs/MINI_APP.md)
- [ROM recovery](docs/MINI_RECOVERY.md)
- [Complete NOR backup](docs/MINI_FLASH_BACKUP.md)
- [Bootloader handover](docs/MINI_HANDOVER.md)
- [Clocks and sampling](docs/MINI_CLOCK.md)
- [Image validation](docs/MINI_IMAGE.md)
- [Watchdog, clocks, and cache](docs/MINI_PLATFORM.md)
- [Codec and mute](docs/MINI_CODEC.md)
- [Interrupts and audio worker](docs/MINI_RUNTIME.md)
- [Historical package branding](docs/REBRANDING.md)
- [Provenance and licenses](docs/PROVENANCE.md)
- [Pinned tools and sources](research/sources.lock.json)

HyperRig is a derivative project. Original authorship, required notices, and
component licenses are preserved. The new name does not change those licenses.
