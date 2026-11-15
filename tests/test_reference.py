"""Analytic DSP cases and comparison with the recovered original JS converter."""

import base64
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
import zlib

from hyperrig.a2l_reference import ReferenceA2L, render_wave

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l"


def analytic_capture(fraction=0, bias=0):
    """One nonlinear channel: a[t]=leaky(x[t-2]+2*x[t]+bias), y[t]=a[t-1]+a[t]+bias."""
    scale = 1 << fraction
    data = struct.pack("<4sHBBIHBB4b16s", b"A2L1", 1, 16, 32, 48000, 1, 3, 2,
                       4, 4, 4, 4, b"analytic")
    data += struct.pack("<b3h", fraction, scale, 0, 0)
    data += struct.pack("<BHbbi", 2, 2, 4, 4, 1 << 23)
    data += struct.pack("<b18h3q", fraction, scale, scale * 2, *([0] * 16), bias * scale * 16, 0, 0)
    data += struct.pack("<b3h", fraction, 0, 0, 0)
    data += struct.pack("<b9h3q", fraction, *([0] * 12))
    data += struct.pack("<b6hq", fraction, scale, scale, 0, 0, 0, 0, bias * scale * 16)
    return data + struct.pack("<I", zlib.crc32(data))


class ReferenceMathTests(unittest.TestCase):
    def test_known_dilated_convolution_and_negative_slope(self):
        engine = ReferenceA2L(analytic_capture())
        self.assertEqual(engine.process([1, 2, -3, 4, -1, 0]), [2, 6, 1.5, 7.5, 7.5, 1.5])

    def test_fractional_weights_and_accumulator_bias_scaling(self):
        engine = ReferenceA2L(analytic_capture(fraction=3, bias=1))
        self.assertEqual(engine.process([0, 0, 0]), [3, 3, 3])

    def test_chunk_boundaries_preserve_stream_state(self):
        capture = analytic_capture()
        whole, chunks = ReferenceA2L(capture), ReferenceA2L(capture)
        samples = [1, 2, -3, 4, -1, 0]
        self.assertEqual(whole.process(samples), chunks.process(samples[:2]) + chunks.process(samples[2:5]) + chunks.process(samples[5:]))
        chunks.reset()
        self.assertEqual(chunks.process(samples), [2, 6, 1.5, 7.5, 7.5, 1.5])

    def test_wave_render_reports_clipping_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            capture, source, output = directory / "test.a2l", directory / "in.wav", directory / "out.wav"
            capture.write_bytes(analytic_capture())
            with wave.open(str(source), "wb") as wav:
                wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                wav.writeframes(struct.pack("<4h", 16384, 16384, 16384, 16384))
            result = render_wave(capture, source, output)
            self.assertEqual(result["samples"], 4)
            self.assertEqual(result["clipped_samples"], 4)
            with wave.open(str(output), "rb") as wav:
                self.assertEqual(wav.readframes(4), struct.pack("<4h", *([32767] * 4)))
            before = output.read_bytes()
            with self.assertRaises(ValueError):
                render_wave(capture, source, output)
            self.assertEqual(output.read_bytes(), before)


@unittest.skipUnless(CAPTURE.exists() and shutil.which("node")
                     and (ROOT / "recovered/ultrarig-original/web/nam2chip.js").exists(),
                     "run analyze and install Node for the original-converter cross-check")
class OriginalConverterComparison(unittest.TestCase):
    def test_embedded_capture_ranges_match_original_javascript(self):
        capture = CAPTURE.read_bytes()
        signals = [[0.0] * 64, [0.75] + [0.0] * 127,
                   [0.4 * math.sin(i * 0.31) + (0.15 if i % 2 else -0.15) for i in range(256)]]
        engine = ReferenceA2L(capture)
        request = {"capture": base64.b64encode(capture).decode(), "engine": engine.engine, "signals": signals}
        result = subprocess.run(["node", str(ROOT / "tools/a2l_js_reference.cjs")],
                                input=json.dumps(request), text=True, encoding="utf-8",
                                capture_output=True, check=True, timeout=60)
        expected = json.loads(result.stdout)
        for signal, reference in zip(signals, expected):
            with self.subTest(samples=len(signal)):
                engine.reset()
                output = engine.process(signal)
                self.assertEqual(len(output), len(signal))
                self.assertTrue(all(math.isfinite(value) for value in output))
                for key in reference:
                    actual_values = engine.ranges[key] if isinstance(engine.ranges[key], list) else [engine.ranges[key]]
                    expected_values = reference[key] if isinstance(reference[key], list) else [reference[key]]
                    self.assertEqual(len(actual_values), len(expected_values))
                    for actual, expected_value in zip(actual_values, expected_values):
                        self.assertTrue(math.isclose(actual, expected_value, rel_tol=1e-11, abs_tol=1e-12),
                                        f"{key}: {actual} != {expected_value}")


if __name__ == "__main__":
    unittest.main()
