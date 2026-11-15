"""Hand-computed cases for original layer instructions, independent of C."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


def parameters(kernel=1):
    return {"kernel": kernel, "dilation": 2, "conv_shift": 1, "mix_shift": 1,
            "linear_shift": 1, "sum_shift": 1, "residual_shift": 0, "slope_q24": 1 << 23,
            "conv_weights": [0] * (9 * (kernel - 1)) + [2, 0, 0, 0, 2, 0, 0, 0, 2],
            "mix_weights": [0, 0, 0], "conv_bias": [0, 0, 0],
            "linear_weights": [2, 0, 0, 0, 2, 0, 0, 0, 2], "linear_bias": [0, 0, 0]}


def preload(ring, position, values):
    history = [0] * (ring * 3)
    for i in range(len(values) // 3):
        index = (position + i) % ring
        history[index * 3:index * 3 + 3] = values[i * 3:i * 3 + 3]
    return history + history[:192]


@unittest.skipUnless(AVAILABLE, "bootstrap/analyze the pinned firmware first")
class NativeLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from layer_machine import LayerProgram
        cls.programs = {kind: LayerProgram(kind) for kind in ("generic", "6", "6_shift", "15", "15_shift")}

    def test_activation_ties_and_residual(self):
        p = parameters()
        history = preload(64, 63, [-3, 4, -1])
        sums, result, position = self.programs["generic"].execute(p, history, 63, [0], [0] * 3, [0] * 399, 68)
        self.assertEqual(sums, [-1, 2, 0])
        self.assertEqual(result[204:207], [-4, 8, -1])
        self.assertEqual(position, 0)

    def test_intermediate_wrap_is_not_saturation(self):
        p = parameters()
        p.update(slope_q24=1 << 24, conv_bias=[1, 0, 0], linear_weights=[0] * 9)
        history = preload(64, 0, [(1 << 31) - 1, 0, 0])
        sums, result, _ = self.programs["generic"].execute(p, history, 0, [0], [-(1 << 31), 0, 0], [0] * 384, 0)
        self.assertEqual(sums, [1 << 30, 0, 0])
        self.assertEqual(result[:3], [(1 << 31) - 1, 0, 0])

    def test_residual_scaling_both_directions_and_linear_bias_wrap(self):
        p = parameters()
        p.update(conv_weights=[0] * 9, linear_weights=[0] * 9)
        history = preload(64, 0, [-3, 3, (1 << 31) - 1])
        for shift, expected in ((1, [-1, 2, 1 << 30]), (-1, [-6, 6, (1 << 31) - 1])):
            p["residual_shift"] = shift
            _, result, _ = self.programs["generic"].execute(p, history, 0, [0], [0] * 3, [0] * 384, 0)
            self.assertEqual(result[:3], expected)
        p.update(residual_shift=0, linear_bias=[(1 << 63) - 1] * 3)
        _, result, _ = self.programs["generic"].execute(p, [0] * 384, 0, [0], [0] * 3, [0] * 384, 0)
        self.assertEqual(result[:3], [-(1 << 31)] * 3)

    def test_optimized_kernels_match_generic_across_ring_boundary(self):
        for kernel in (6, 15):
            p = parameters(kernel)
            ring = 64 + 2 * (kernel - 1)
            history = preload(ring, ring - 1, [-3, 4, -1, 2, -7, 3])
            for shift in (-2, 0, 3):
                p["residual_shift"] = shift
                args = (p, history, ring - 1, [0, 0], [0] * 6, [0] * 399, 68)
                expected = self.programs["generic"].execute(*args)
                variant = f"{kernel}_shift" if shift else str(kernel)
                self.assertEqual(self.programs[variant].execute(*args), expected)
                wrong = str(kernel) if shift else f"{kernel}_shift"
                with self.assertRaisesRegex(ValueError, "specialization"):
                    self.programs[wrong].execute(*args)
