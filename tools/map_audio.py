"""Recover audio configuration evidence from the pinned G/Mini firmware samples.

All reads are offline. The report separates table values and decoded call
targets from inferred meanings; it is not a hardware driver or a flash patch.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.disassemble import codec, relative_target, table


def checked(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"sample differs from input-manifest: {path.name}")
    return raw


def recover():
    manifest = json.loads((ROOT / "research/input-manifest.json").read_text(encoding="utf-8"))
    g_entry = next(item for item in manifest["firmware_images"] if item["file"] == "m571_g_app.bin")
    g, _, _ = unpack_app(checked(ROOT / g_entry["path"], g_entry["sha256"]))
    mini_entry = manifest["tank_mini"]
    _, packed = unpack_fwsc(checked(ROOT / "artifacts/tank-mini/TANK-MINI.fwsc", mini_entry["sha256"]))
    mini, _, _ = unpack_app(packed["flash.bin"][0x4000:])
    isa = table.load()

    def call(raw, address, expected):
        instruction, fields, size = codec.decode(isa, raw, address - 0x02000000)
        text = codec.format(instruction, fields)
        target = relative_target(address, size, text)
        if not text.startswith("call ") or target != expected:
            raise ValueError(f"unexpected call at {address:#x}")
        return {"site": hex(address), "target": hex(target)}

    config_address = 0x02035E90
    config = mini[config_address - 0x02000000:config_address - 0x02000000 + 96]
    words = struct.unpack("<24I", config)
    if words[0] not in (0, 1, 2):
        raise ValueError("unsupported Mini pin group")
    pin_table = mini[0x35E20:0x35E20 + 21]
    row = list(pin_table[words[0] * 7:(words[0] + 1) * 7])
    channels = [{"index": n, "enabled": bool(words[1 + n * 4]),
                 "direction_code": words[2 + n * 4],
                 "buffer_address": hex(words[3 + n * 4]),
                 "callback_address": hex(words[4 + n * 4]),
                 "gpio_number": row[3 + n]} for n in range(4)]
    codec_table = mini[0x35E35:0x35E35 + 88]
    report = {
        "evidence_kind": "pinned binary tables and call sites; hardware timing unverified",
        "samples_sha256": {"tank_g_v2_m571": g_entry["sha256"], "tank_mini_009": mini_entry["sha256"]},
        "controller": {"name_from_sdk": "JL_ALNK0", "base": "0x00012e00", "irq_index": 11},
        "mini": {
            "config_address": hex(config_address), "config_sha256": hashlib.sha256(config).hexdigest(),
            "config_words": [hex(word) for word in words],
            "config_calls": [call(mini, 0x02007164, 0x02006F70),
                             call(mini, 0x02007170, 0x0200708C),
                             call(mini, 0x02007086, 0x02006E58)],
            "pin_table_address": "0x02035e20", "pin_group_index": words[0],
            "clock_gpio_numbers": row[:3], "channels": channels,
            "nominal_rate_in_config": words[23],
            "dma_bytes_per_channel": words[22],
            "alnk_len_register_value": words[22] >> 3,
            "audio_task": "0x01c03f24", "process_function": "0x01c03a18",
            "process_samples_argument": 64,
            "dma_callback": "0x01c03eee", "irq_handler": "0x01c0374a",
            "clock_setter": "0x02006e58", "has_48000_branch": True,
            "codec_init": {"function": "0x02006dec", "table_address": "0x02035e35",
                           "table_sha256": hashlib.sha256(codec_table).hexdigest(),
                           "writes": len(codec_table) // 4, "bytes_per_write": 4,
                           "bus_address_byte": "0x36", "control_gpio_candidates": [1, 2],
                           "chip_identity": None},
        },
        "ultrarig_g": {
            "audio_setup": "0x020051fc",
            "driver_calls": [call(g, 0x02005406, 0x02004D36), call(g, 0x02005412, 0x02005130)],
            "pin_table_address": "0x02035360", "selected_table_row": list(g[0x35360:0x35367]),
            "row_order": "channel data 0..3, then three clock pins",
            "input_channel_mask": 2, "output_channel_mask": 1, "width_24_mask": 3,
            "sr_points_parameter": 128, "sample_rate": 48000,
            "sample_rate_literal_address": "0x0200514c",
        },
        "interpretation": [
            "Both application paths configure ALNK0; presence of internal ADC/DAC library code does not establish the main audio route.",
            "Mini group 1 and G group 0 select the same GPIO numbers: PA4..PA6 clocks, PA7 output, PA8 input.",
            "Mini channels 0/1 use separate 1024-byte buffers split into 512-byte halves; the task consumes 64 frames with two 32-bit slots.",
            "Mini nominal 44100 Hz differs from UltraRig 48000 Hz; a stock driver branch accepts 48000, but codec/PLL behavior needs measurement.",
        ],
        "unverified": ["physical codec identity", "clock frequencies", "analog mute and gain",
                       "48 kHz operation on this Mini", "bootable HyperRig integration"],
    }
    return report


def main():
    result = recover()
    output = ROOT / "analysis/native/audio-map.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"ALNK0: Mini {result['mini']['nominal_rate_in_config']} Hz, UltraRig G 48000 Hz; static evidence only.")
    print(output)


if __name__ == "__main__":
    main()
