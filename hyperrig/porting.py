"""Describe the concrete compatibility work remaining for the Tank Mini."""

import json
from pathlib import Path


def status(root: Path) -> dict:
    profile = json.loads((root / "firmware/targets/tank-mini.json").read_text(encoding="utf-8"))
    return {
        "project": "HyperRig", "target": profile["target"], "flashable": False,
        "confirmed_offline": ["AC791N/pi32v2", "SFC decoding and JLFS CRCs", "factory memory map",
                              "USB-MIDI framing", "preset record format", "A2L1 capture format",
                              "A2-Lite float reference compared with original converter",
                              "complete three-channel int32 A2L capture path, "
                              f"{profile['native_dsp']['instruction_level_comparisons']} instruction-level comparisons",
                              "pi32v2 relocatable object compiled with JieLi toolchain",
                              "MINI linked diagnostic ELFs, startup memory simulation and strict layout validation",
                              "MINI ALNK driver, DMA sample adapter and MMIO behavior tested offline",
                              "P33 watchdog/cache primitives and stock clock decoder verified offline",
                              "MINI codec bus traces and IRQ/worker fault handling verified offline",
                              "integrated worker-to-A2 probe passed host ASan/UBSan using fake DMA",
                              "experimental MINI application area composed from ELF and CRC-checked",
                              "ALNK0 audio path, DMA buffers and 64-frame processing",
                              "Mini nominal 44100 Hz versus UltraRig G 48000 Hz"],
        "observed_on_device": profile["device_observation"],
        "native_dsp": profile["native_dsp"],
        "boot": profile["boot"],
        "audio_driver": profile["audio_driver"],
        "platform": profile["platform"],
        "codec": profile["codec"],
        "audio_runtime": profile["audio_runtime"],
        "application_container": profile["application_container"],
        "audio": profile["audio"],
        "gpio_candidates": profile["gpio_candidates"],
        "remaining": [
            "Reconstruct IR/effects, gain/frontend and A2L paths outside the verified three-channel int32 profile.",
            "Validate Mini ALNK/codec clock setup at 48000 Hz, sample packing and analog mute.",
            "Confirm physical footswitch identity/polarity and LED pins.",
            "Validate actual MINI boot handoff, instruction caches, IRQ/audio scheduling and updater metadata/transport.",
            "Validate the unit's flash geometry, complete backup and recovery route.",
            "Measure audio timing, RAM/CPU budget and stable clock on the physical pedal."
        ]
    }
