"""Analytic expectations for the original Q28 filter instructions."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())
sys.path.insert(0, str(ROOT / "tools"))


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class BiquadInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from biquad_machine import BiquadProgram
        cls.rounded, cls.residual = BiquadProgram("rounded"), BiquadProgram("residual")

    def test_identity_and_exact_negative_endpoint(self):
        values = [-(1 << 31), -3, -1, 0, 1, 3, (1 << 31) - 1]
        state = [1 << 28, 0, 0, 0, 0, 10, 20, 30, 40, 0]
        for program in (self.rounded, self.residual):
            output, after = program.execute(values, state)
            self.assertEqual(output, values)
            self.assertEqual(after[5:9], [values[-1], values[-2]] * 2)

    def test_rounded_ties_toward_positive_infinity(self):
        output, _ = self.rounded.execute([-3, -1, 1, 3], [1 << 27] + [0] * 9)
        self.assertEqual(output, [-1, 0, 1, 2])

    def test_feedback_coefficients_are_added(self):
        output, state = self.rounded.execute([1, 2, 3], [1 << 28] * 5 + [10, 20, 30, 40, 123])
        self.assertEqual(output, [101, 144, 251])
        self.assertEqual(state[5:], [3, 2, 251, 144, 123])

    def test_overflow_saturation_is_not_standard_int32_clamp(self):
        output, _ = self.rounded.execute([-(1 << 31), (1 << 31) - 1], [1 << 29] + [0] * 9)
        self.assertEqual(output, [-2147483647, 2147483647])

    def test_accumulator_wrap_precedes_saturation(self):
        for count, expected in ((3, -2147483647), (4, 0), (5, 2147483647)):
            coefficients = [-(1 << 31)] * count + [0] * (5 - count)
            state = coefficients + [-(1 << 31)] * 4 + [0]
            for program in (self.rounded, self.residual):
                output, _ = program.execute([-(1 << 31)], state)
                self.assertEqual(output, [expected])

    def test_residual_alternates_half_samples(self):
        state = [1 << 27] + [0] * 9
        self.assertEqual(self.residual.execute([1] * 4, state)[0], [0, 1, 0, 1])
        self.assertEqual(self.residual.execute([-1] * 4, state)[0], [-1, 0, -1, 0])

    def test_initial_residue_is_zero_extended_uint32(self):
        output, state = self.residual.execute([0], [0] * 9 + [0xFFFFFFFF])
        self.assertEqual(output, [15])
        self.assertEqual(state[9], 0x0FFFFFFF)

    def test_residue_is_preserved_through_saturation(self):
        output, state = self.residual.execute([2147483647], [(1 << 29) + 1] + [0] * 9)
        self.assertEqual(output, [2147483647])
        self.assertEqual(state[9], 0x0FFFFFFF)

    def test_empty_block_preserves_all_state(self):
        state = list(range(10))
        for program in (self.rounded, self.residual):
            self.assertEqual(program.execute([], state), ([], state))

    def test_rounded_preserves_unused_residue(self):
        state = [1 << 28] + [0] * 8 + [0xFEDCBA98]
        self.assertEqual(self.rounded.execute([1, 2, 3], state)[1][9], 0xFEDCBA98)

    def test_odd_block_history_and_subdivision(self):
        values = [3, -4, 5, -6, 7, -8, 9]
        state = [1 << 27, 1 << 26, 0, 1 << 26, 0, 1, 2, 3, 4, 11]
        for program in (self.rounded, self.residual):
            whole = program.execute(values, state)
            output = []
            current = state
            cursor = 0
            for count in (1, 2, 4):
                block, current = program.execute(values[cursor:cursor + count], current)
                output.extend(block)
                cursor += count
            self.assertEqual((output, current), whole)

    def test_domain_and_memory_guards(self):
        from biquad_machine import BiquadMachine
        for values, state in (([0] * 129, [0] * 10), ([], [0] * 9),
                              ([1 << 31], [0] * 10), ([], [0] * 9 + [-1])):
            with self.assertRaises(ValueError):
                self.rounded.execute(values, state)
        machine = BiquadMachine(self.rounded, [0], [0] * 10)
        with self.assertRaises(ValueError):
            machine.read(machine.BUFFER + 4, 4)
        with self.assertRaises(ValueError):
            machine.write(machine.CONTEXT, 1, 4)
        with self.assertRaises(ValueError):
            machine.write(machine.BUFFER + 4, 1, 4)


if __name__ == "__main__":
    unittest.main()
