"""Describe the concrete compatibility work remaining for the Tank Mini."""

import json
from pathlib import Path


def status(root: Path) -> dict:
    profile = json.loads((root / "firmware/targets/tank-mini.json").read_text(encoding="utf-8"))
    return {
        "project": "HyperRig", "target": profile["target"], "flashable": False,
        "confirmed_offline": ["AC791N/pi32v2", "SFC decoding and JLFS CRCs", "factory memory map",
                              "USB-MIDI framing", "preset record format", "A2L1 capture format",
                              "A2-Lite float reference compared with original converter"],
        "gpio_candidates": profile["gpio_candidates"],
        "remaining": [
            "Reconstruct or replace the native DSP implementation; Ghidra output is not buildable C.",
            "Confirm footswitch identity/polarity, LED pins, ADC/DAC routing and mute circuitry.",
            "Build a Mini-specific application and allocator/storage layout; never reuse the G/B image.",
            "Validate the unit's flash geometry, complete backup and recovery route.",
            "Measure audio timing, RAM/CPU budget and stable clock on the physical pedal."
        ]
    }
