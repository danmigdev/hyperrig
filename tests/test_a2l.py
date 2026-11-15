from pathlib import Path
import unittest

from hyperrig.a2l import inspect

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l"


@unittest.skipUnless(CAPTURE.exists(), "run hyperrig analyze first")
class EmbeddedCaptureTests(unittest.TestCase):
    def test_real_default_capture(self):
        model = inspect(CAPTURE.read_bytes())
        self.assertEqual((model["name"], model["layers"], model["channels"], model["head_kernel"]), ("A2", 23, 3, 16))
        self.assertEqual(model["sample_rate"], 48000)
        self.assertEqual(model["bytes"], 4892)

    def test_corruption_rejected(self):
        data = bytearray(CAPTURE.read_bytes())
        data[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC32"):
            inspect(data)
