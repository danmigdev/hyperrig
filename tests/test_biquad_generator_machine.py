"""Focused original-instruction witnesses for the bounded coefficient generator."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from biquad_generator_machine import BiquadGeneratorProgram, DIVISOR
from verify_biquad_generator import initial


class GeneratorInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = BiquadGeneratorProgram()

    def value(self, operation, value):
        return self.program.execute(initial(), operation, value=value)["value"]

    def test_exponential_identity_and_reduction_branches(self):
        self.assertEqual(self.value("exp", 0), 0x3F800000)
        self.assertEqual(self.value("exp", 0x80000000), 0x3F800000)
        positive = self.program.execute(initial(), "exp", value=0x3F800000)
        negative = self.program.execute(initial(), "exp", value=0xBF800000)
        self.assertIn(0x020285E6, positive["visited"])
        self.assertIn(0x0202862C, positive["visited"])
        self.assertIn(0x020285FE, negative["visited"])
        self.assertIn(0x0202863C, negative["visited"])

    def test_scaled_exponential_executes_inner_exp(self):
        result = self.program.execute(initial(), "scaled_exp", value=0x41400000)
        self.assertIn(("exp", 0x3FB0D6AA), result["math_calls"])
        self.assertEqual(self.value("scaled_exp", 0), 0x3F800000)

    def test_trigonometric_zero_and_parity(self):
        self.assertEqual(self.value("cosine", 0), 0x3F800000)
        self.assertEqual(self.value("sine", 0), 0)
        for word in (0x3F000000, 0x3F800000, 0x40000000):
            self.assertEqual(self.value("cosine", word), self.value("cosine", word ^ 0x80000000))
            self.assertEqual(self.value("sine", word), self.value("sine", word ^ 0x80000000) ^ 0x80000000)

    def test_square_root_nonpositive_and_nan(self):
        for word in (0, 0x80000000, 0xBF800000, 0xFF800000):
            self.assertEqual(self.value("square_root", word), 0)
        for word in (0x7F800001, 0x7FC00000, 0xFF800001, 0xFFC00000):
            self.assertEqual(self.value("square_root", word), 0x7F800001)

    def test_square_root_is_twenty_iterations_not_libm(self):
        self.assertEqual(self.value("square_root", 1), 0x35800000)
        self.assertEqual(self.value("square_root", 0x7F800000), 0x7F800001)
        self.assertEqual(self.value("square_root", 0x40000000), 0x3FB504F3)

    def test_all_mathematics_execute_without_scripted_callbacks(self):
        result = self.program.execute(initial(), "stage", section=0, value=6)
        self.assertEqual(result["calls"], [])
        self.assertEqual({name for name, _ in result["math_calls"]},
                         {"generate", "scaled_exp", "exp", "cosine", "sine", "square_root"})
        self.assertEqual(len(result["normalization_calls"]), 1)
        self.assertIn(0x02028734, result["visited"])
        self.assertIn(0x01C0519C, result["visited"])

    def test_zero_parameter_disables_all_modes(self):
        for mode in (0, 1, 2, 0xFFFFFFFF):
            result = self.program.execute(initial(), "generate", request=(mode, 0x42C80000, 0, 0x3F666666))
            self.assertEqual(result["memory"][0][40:42], bytes((0, int(mode == 0))))
            raw = result["normalization_calls"][0][1]
            self.assertEqual(raw[0], raw[3])
            self.assertEqual(raw[1], raw[4])
            self.assertEqual(raw[2], raw[5])

    def test_only_mode_one_reads_width_mathematically(self):
        for mode in (0, 1, 2):
            a = self.program.execute(initial(), "generate", request=(mode, 0x44960000, 0x40C00000, 0x3F666666))
            b = self.program.execute(initial(), "generate", request=(mode, 0x44960000, 0x40C00000, 0x7FC00000))
            self.assertEqual(a["normalization_calls"] == b["normalization_calls"], mode != 1)

    def test_nonzero_modes_other_than_one_share_last_branch(self):
        request = (2, 0x45DAC000, 0xC0C00000, 0x3F666666)
        a = self.program.execute(initial(), "generate", request=request)
        b = self.program.execute(initial(), "generate", request=(0xFFFFFFFF, *request[1:]))
        self.assertEqual(a["memory"], b["memory"])
        self.assertEqual(a["normalization_calls"], b["normalization_calls"])

    def test_divisor_uint32_rounds_before_float_division(self):
        request = (1, 0x45DAC000, 0x40C00000, 0x3F666666)
        a = self.program.execute(initial(16777216), "generate", request=request)
        b = self.program.execute(initial(16777217), "generate", request=request)
        self.assertEqual(a["normalization_calls"], b["normalization_calls"])
        c = self.program.execute(initial(16777219), "generate", request=request)
        d = self.program.execute(initial(16777220), "generate", request=request)
        self.assertEqual(c["normalization_calls"], d["normalization_calls"])

    def test_zero_divisor_reaches_original_special_value_path(self):
        result = self.program.execute(initial(0), "stage", section=1, value=6)
        self.assertEqual(struct.unpack("<5i", result["memory"][0][44:64]), (0x7FFFFFFF,)*5)
        self.assertEqual(result["memory"][-1], bytes(4))

    def test_invalid_section_does_not_execute_math(self):
        result = self.program.execute(initial(), "stage", section=0xFFFFFFFF, value=6)
        self.assertFalse(result["math_calls"])
        self.assertFalse(result["production_calls"])
        self.assertFalse(result["normalization_calls"])
        self.assertEqual(result["memory"][-3], bytes.fromhex("ffffffff"))

    def test_staging_preserves_divisor_and_history(self):
        memory = initial(0xFFFFFFFF)
        result = self.program.execute(memory, "stage", section=4, value=0x80000000)
        self.assertEqual(result["memory"][-1], bytes(memory[-1]))
        self.assertEqual(result["memory"][1], bytes(memory[1]))
        for i in range(5):
            self.assertEqual(result["memory"][0][44*i+20:44*i+40], bytes(memory[0][44*i+20:44*i+40]))
        self.assertEqual(result["memory"][-2][4], 244)
        self.assertEqual(result["memory"][5][4], 1)

    def test_bounded_domain_rejects_unbounded_range_reduction(self):
        for operation, value in (("exp", 0x41800001), ("exp", 0x7F800000),
                                 ("exp", 0xFF800000), ("exp", 0x7FC00000),
                                 ("scaled_exp", 0x43000001)):
            with self.assertRaises(ValueError):
                self.program.execute(initial(), operation, value=value)
        with self.assertRaises(ValueError):
            self.program.execute(initial(), "generate", request=(0, 0, 0x43000001, 0))


if __name__ == "__main__":
    unittest.main()
