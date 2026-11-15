"""Analytic checks of actual firmware instructions, independent of recovered C."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class NativeInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from dot_machine import DotProgram
        from head_machine import HeadProgram
        cls.dot16, cls.dot32, cls.head = DotProgram(16), DotProgram(32), HeadProgram()

    def test_dot_signed_halfway_rounding(self):
        for program in (self.dot16, self.dot32):
            self.assertEqual(program.execute([-3, -1, 0, 1, 3], [1], 5, shift=1), [-2, -1, 0, 1, 2])

    def test_dot_saturation_and_accumulator_wrap(self):
        self.assertEqual(self.dot16.execute([2147483647, -2147483648], [2], 2),
                         [2147483647, -2147483648])
        # Two positive 2**62 products wrap into signed -2**63 before saturation.
        self.assertEqual(self.dot32.execute([-2147483648] * 2, [-2147483648] * 2, 1), [-2147483648])

    def test_dot_strides_and_empty_weights(self):
        self.assertEqual(self.dot16.execute([1, 2, 3, 4], [2, -1], 2, 2, 3), [0, 2])
        self.assertEqual(self.dot16.execute([], [], 3, 0, 2), [0, 0, 0])
        self.assertEqual(self.dot32.execute([], [], 0), [])

    def test_interpreter_rejects_missing_memory_and_unsupported_shift(self):
        with self.assertRaisesRegex(ValueError, "uninitialized"):
            self.dot16.execute([1], [2, 3], 1)
        with self.assertRaisesRegex(ValueError, "domain"):
            self.dot32.execute([1], [1], 1, shift=63)

    def test_head_causal_kernel_across_ring_boundary(self):
        values = [value for x in (1, 2, -3, 5) for value in (x, 0, 0)]
        output, history, position = self.head.execute(values, [2, 0, 0, 4, 0, 0], [0] * 384, 63, 1, 0)
        self.assertEqual(output, [2, 5, -4, 7])
        self.assertEqual(position, 3)
        self.assertEqual(history[63 * 3:64 * 3], [1, 0, 0])
        self.assertEqual(history[64 * 3:67 * 3], [2, 0, 0, -3, 0, 0, 5, 0, 0])

    def test_head_rounding_then_bias_and_saturation(self):
        values = [-3, 0, 0, -1, 0, 0, 1, 0, 0, 3, 0, 0]
        output, _, _ = self.head.execute(values, [1, 0, 0], [0] * 384, 0, 1, 7)
        self.assertEqual(output, [5, 6, 8, 9])
        output, _, _ = self.head.execute([2147483647, 0, 0], [2, 0, 0], [0] * 384, 0, 1, 1)
        self.assertEqual(output, [2147483647])

    def test_head_state_continues_between_calls(self):
        weights = [2, 0, 0, 4, 0, 0]
        first, history, position = self.head.execute([1, 0, 0], weights, [0] * 384, 63, 1, 0)
        second, _, position = self.head.execute([2, 0, 0], weights, history, position, 1, 0)
        self.assertEqual(first + second, [2, 5])
        self.assertEqual(position, 1)


if __name__ == "__main__":
    unittest.main()
