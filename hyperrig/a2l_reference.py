"""Offline Float64 reference for dequantized A2L1 captures.

Mathematics reconstructed from UltraRig's distributed nam2chip.js (measure).
Required Notice: Copyright (c) 2026 Manuel Aguirre
https://polyformproject.org/licenses/noncommercial/1.0.0
See third_party/ultrarig/LICENSE.md and docs/PROVENIENZA.md.

This is NOT the original fixed-point DSP: rounding, saturation, integer
overflow and hardware timing are deliberately not claimed to be equivalent.
"""

from array import array
import math
from pathlib import Path
import struct
import wave

from .a2l import inspect


def engine_from_capture(data: bytes) -> dict:
    model = inspect(data)
    if model["channels"] != 3 or model["sample_rate"] != 48000:
        raise ValueError("reference engine supports three-channel A2L1 at 48 kHz")

    def dequantize(values, fraction):
        return [math.ldexp(float(v), -fraction) for v in values]

    previous = model["initial_residual_fraction"]
    layers = []
    for layer in model["layer_parameters"]:
        layers.append({
            "K": layer["kernel"], "dil": layer["dilation"],
            "slope": math.ldexp(layer["slope_q24"], -24),
            "convW": dequantize(layer["conv_weights"], layer["conv_fraction"]),
            "convB": dequantize(layer["conv_bias"], layer["conv_fraction"] + previous),
            "mixW": dequantize(layer["mix_weights"], layer["mix_fraction"]),
            "l1W": dequantize(layer["linear_weights"], layer["linear_fraction"]),
            "l1B": dequantize(layer["linear_bias"], layer["linear_fraction"] + layer["activation_fraction"]),
        })
        previous = layer["residual_fraction"]
    return {
        "C": 3, "hk": model["head_kernel"], "layers": layers, "headScale": 1.0,
        "rech": dequantize(model["rechannel_weights"], model["rechannel_fraction"]),
        "hW": dequantize(model["head_weights"], model["head_fraction"]),
        "hB": math.ldexp(float(model["head_bias"]), -(model["head_fraction"] + model["head_sum_fraction"])),
    }


class History:
    def __init__(self, length):
        self.length, self.position = length, -1
        self.channels = [array("d", [0.0]) * length for _ in range(3)]

    def put(self, values):
        self.position = (self.position + 1) % self.length
        for channel, value in zip(self.channels, values):
            channel[self.position] = value


class ReferenceA2L:
    """Causal streaming float model with bounded delay buffers and zero pre-roll.

    Ranges match the original converter's valid-convolution calibration
    intervals. They include the relevant part of the zero pre-roll.
    """

    def __init__(self, capture: bytes):
        self.engine = engine_from_capture(capture)
        self.lengths = [(layer["K"] - 1) * layer["dil"] + 1 for layer in self.engine["layers"]]
        self.receptive_field = 1 + sum(n - 1 for n in self.lengths) + self.engine["hk"] - 1
        if 3 * (sum(self.lengths) + self.engine["hk"]) > 2_000_000:
            raise ValueError("reference model exceeds the host delay-buffer limit")
        self.reset()

    def reset(self):
        self.histories = [History(n) for n in self.lengths]
        self.head = History(self.engine["hk"])
        self.seen = 0
        self.ranges = {"rech": 0.0, "z": [0.0] * len(self.lengths),
                       "x3": [0.0] * len(self.lengths), "head": 0.0, "out": 0.0}
        for _ in range(self.receptive_field - 1):
            self._step(0.0)

    def _step(self, sample):
        engine, ranges = self.engine, self.ranges
        residual = [w * sample for w in engine["rech"]]
        ranges["rech"] = max(ranges["rech"], *(abs(v) for v in residual))
        summed = [0.0, 0.0, 0.0]
        valid_from = 0
        for i, (layer, history) in enumerate(zip(engine["layers"], self.histories)):
            history.put(residual)
            kernel, dilation, weights = layer["K"], layer["dil"], layer["convW"]
            valid_from += history.length - 1
            z, activation = [], []
            for output in range(3):
                value = layer["convB"][output]
                base = output * 3 * kernel
                for tap in range(kernel):
                    index = (history.position - (kernel - 1 - tap) * dilation) % history.length
                    value += (weights[base + tap] * history.channels[0][index]
                              + weights[base + kernel + tap] * history.channels[1][index]
                              + weights[base + 2 * kernel + tap] * history.channels[2][index])
                value += layer["mixW"][output] * sample
                z.append(value)
                activation.append(value if value >= 0 else layer["slope"] * value)
            a, b, c = activation
            weights = layer["l1W"]
            residual = [residual[channel] + (weights[channel * 3] * a + weights[channel * 3 + 1] * b
                        + weights[channel * 3 + 2] * c + layer["l1B"][channel]) for channel in range(3)]
            if self.seen >= valid_from:
                ranges["z"][i] = max(ranges["z"][i], *(abs(v) for v in z))
                ranges["x3"][i] = max(ranges["x3"][i], *(abs(v) for v in residual))
            summed = [total + current for total, current in zip(summed, activation)]
        if self.seen >= valid_from:
            ranges["head"] = max(ranges["head"], *(abs(v) for v in summed))
        self.head.put(summed)
        output, kernel, weights = engine["hB"], engine["hk"], engine["hW"]
        for tap in range(kernel):
            index = (self.head.position - (kernel - 1 - tap)) % kernel
            output += (weights[tap] * self.head.channels[0][index]
                       + weights[kernel + tap] * self.head.channels[1][index]
                       + weights[2 * kernel + tap] * self.head.channels[2][index])
        if not math.isfinite(output):
            raise ValueError("non-finite reference output")
        if self.seen >= self.receptive_field - 1:
            ranges["out"] = max(ranges["out"], abs(output))
        self.seen += 1
        return output

    def process(self, samples) -> list[float]:
        output = []
        for sample in samples:
            if not math.isfinite(sample):
                raise ValueError("non-finite input sample")
            output.append(self._step(float(sample)))
        return output


def render_wave(capture: Path, source: Path, destination: Path) -> dict:
    """Render mono PCM16/48k to a new WAV file; report output clipping."""
    if destination.exists():
        raise ValueError("output already exists; choose a new WAV filename")
    with wave.open(str(source), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 48000, "NONE"):
            raise ValueError("input must be uncompressed mono PCM16 at 48000 Hz")
        frames = wav.getnframes()
        raw = wav.readframes(frames)
        if len(raw) != frames * 2:
            raise ValueError("truncated input WAV")
    engine = ReferenceA2L(capture.read_bytes())
    output = engine.process(value[0] / 32768 for value in struct.iter_unpack("<h", raw))
    clipped = sum(value < -1 or value > 32767 / 32768 for value in output)
    pcm = b"".join(struct.pack("<h", max(-32768, min(32767, round(value * 32768)))) for value in output)
    with destination.open("xb") as file, wave.open(file, "wb") as wav:
        wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        wav.writeframes(pcm)
    return {"mode": "dequantized float reference, not firmware-equivalent fixed point",
            "samples": len(output), "peak": max((abs(v) for v in output), default=0),
            "clipped_samples": clipped, "output": str(destination)}
