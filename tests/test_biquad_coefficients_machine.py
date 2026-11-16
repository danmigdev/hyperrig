"""Focused instruction witnesses for coefficient staging and Q28 conversion."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from biquad_coefficients_machine import (BiquadCoefficientsProgram, BiquadCoefficientsMachine,
    PARAMETERS, PENDING, STAGED, AVERAGE, REQUESTS, STACK)
from verify_biquad_coefficients import initial


class CoefficientInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = BiquadCoefficientsProgram()

    def q28(self, value):
        return self.program.execute(initial(), "q28", value=value)["value"]

    def test_unit_and_signed_zeros(self):
        for value, expected in ((0, 0), (0x80000000, 0), (0x3F800000, 1 << 28), (0xBF800000, -(1 << 28))):
            self.assertEqual(self.q28(value), expected)

    def test_half_unit_and_double_rounding_neighbor(self):
        # 0x30ffffff * 2^28 is just below 0.5; binary32 addition of 0.5
        # rounds to 1 before truncation. Exact real arithmetic would give 0.
        for value, expected in ((0x30FFFFFE, 0), (0x30FFFFFF, 1), (0x31000000, 1),
                                (0xB0FFFFFE, 0), (0xB0FFFFFF, -1), (0xB1000000, -1)):
            self.assertEqual(self.q28(value), expected)

    def test_nan_sign_and_payload_do_not_reach_integer_saturation(self):
        for value in (0x7F800001, 0x7FC00000, 0x7FFFFFFF, 0xFF800001, 0xFFC00000, 0xFFFFFFFF):
            self.assertEqual(self.q28(value), 0x7FFFFFFF)

    def test_infinities_and_integer_limits(self):
        for value, expected in ((0x7F800000, 0x7FFFFFFF), (0xFF800000, -0x80000000),
                                (0x40FFFFFF, 2147483520), (0x41000000, 0x7FFFFFFF),
                                (0xC0FFFFFF, -2147483520), (0xC1000000, -0x80000000)):
            self.assertEqual(self.q28(value), expected)

    def test_normalization_negates_feedback_before_division(self):
        memory = initial()
        words = [0x3F800000, 0xBF000000, 0x3E800000, 0x40000000, 0x3F000000, 0xBE800000, 0x1234, 0x100]
        result = self.program.execute(memory, "normalize", section=2, input_words=words)
        section = result["memory"][0][88:132]
        self.assertEqual(struct.unpack("<5i", section[:20]), (1 << 27, -(1 << 26), 1 << 25, -(1 << 26), 1 << 25))
        self.assertEqual(section[40:42], b"\x34\x01")
        self.assertEqual(section[20:40] + section[42:44], memory[0][108:128] + memory[0][130:132])

    def test_zero_denominator_retains_measured_special_values(self):
        words = [0, 0x3F800000, 0xBF800000, 0, 0, 0, 1, 0]
        result = self.program.execute(initial(), "normalize", input_words=words)
        self.assertEqual(struct.unpack("<5i", result["memory"][0][:20]),
                         (0x7FFFFFFF, 0x7FFFFFFF, -0x80000000, 0x7FFFFFFF, 0x7FFFFFFF))

    def test_setup_table_mode_width_and_signed_parameter(self):
        expected = ((0, 0x42C80000), (1, 0x43C80000), (1, 0x44960000), (1, 0x45480000), (2, 0x45DAC000))
        for section, (mode, table) in enumerate(expected):
            memory = initial()
            memory[-1][section] = 0x80
            result = self.program.execute(memory, "setup", section=section, producer=lambda *_: None)
            self.assertEqual(result["calls"][0][1], (mode, table, 0xC3000000, 0x3F666666))
            self.assertEqual(result["memory"], tuple(bytes(part) for part in memory))

    def test_stage_clamps_full_signed_word(self):
        for value, expected in ((0x80000000, 244), (0xFFFFFFF3, 244), (0xFFFFFFF4, 244),
                                (0xFFFFFFF5, 245), (11, 11), (12, 12), (13, 12), (0x7FFFFFFF, 12)):
            result = self.program.execute(initial(), "stage", section=3, value=value, producer=lambda *_: None)
            self.assertEqual(result["memory"][-1][3], expected)
            self.assertEqual(result["memory"][5][3], 1)

    def test_callback_observes_ordered_state_changes(self):
        memory = initial()
        memory[5][:] = bytes((5, 6, 7, 8, 9))
        result = self.program.execute(memory, "stage", section=2, value=0xFFFFFFFF, producer=lambda *_: None)
        snapshot = result["calls"][0][2]
        self.assertEqual(snapshot[5], bytes((5, 6, 0, 8, 9)))
        self.assertEqual(snapshot[-1], bytes((1, 2, 255, 4, 5)))
        self.assertEqual(snapshot[3], bytes(4))
        self.assertEqual(snapshot[7], bytes.fromhex("ffffffff"))
        self.assertEqual(result["memory"][5], bytes((5, 6, 1, 8, 9)))

    def test_invalid_index_still_counts_and_wraps(self):
        memory = initial()
        memory[7][:] = bytes.fromhex("ffffffff")
        result = self.program.execute(memory, "stage", section=0xFFFFFFFF, value=7)
        self.assertFalse(result["calls"])
        self.assertEqual(result["memory"][7], bytes(4))
        self.assertEqual(result["memory"][:7], tuple(bytes(part) for part in memory[:7]))
        self.assertEqual(result["memory"][-1], bytes(memory[-1]))

    def test_parallel_store_uses_old_parameter_register(self):
        machine = BiquadCoefficientsMachine(self.program, initial(), "stage", 2, 0, None, None)
        machine.pc = 0x02028902
        machine.regs.update(r0=244, r2=2, r4=PENDING+2)
        self.assertTrue(machine.step())
        self.assertEqual(machine.regs["r0"], 88)
        self.assertEqual(machine.read(PARAMETERS+2, 1), 244)

    def test_scripted_normalizer_executes_native_conversion(self):
        words = [0x3F800000, 0, 0, 0x3F800000, 0, 0, 1, 1]
        result = self.program.execute(initial(), "stage", section=4, value=6,
            producer=lambda section, _request, machine: machine.normalize_script(section, words))
        self.assertIn(0x01C0519C, result["visited"])
        self.assertIn(0x020286A0, result["visited"])
        self.assertNotIn(0x02028734, result["visited"])

    def test_script_cannot_modify_unreconstructed_state(self):
        def bad_script(_section, _request, machine):
            machine.write(AVERAGE, 5, 4)
        with self.assertRaisesRegex(ValueError, "outside its boundary"):
            self.program.execute(initial(), "setup", producer=bad_script)

    def test_memory_and_stack_guards(self):
        machine = BiquadCoefficientsMachine(self.program, initial(), "stage", 0, 0, None, None)
        for address in (STAGED+220, TABLE_ADDRESS := 0x0203A55C, STACK):
            with self.assertRaises(ValueError):
                machine.write(address, 1, 4)
        with self.assertRaises(ValueError):
            machine.read(STACK-4, 4)
        with self.assertRaises(ValueError):
            machine.read(TABLE_ADDRESS+10, 1)

    def test_invalid_verifier_domain_and_packet_entry(self):
        for kwargs in ({"operation": "setup", "section": 5}, {"operation": "q28", "value": -1},
                       {"operation": "normalize", "input_words": [0]*7}):
            with self.assertRaises(ValueError):
                self.program.execute(initial(), **kwargs)
        machine = BiquadCoefficientsMachine(self.program, initial(), "stage", 0, 0, None, None)
        machine.pc = 0x02028906
        with self.assertRaises(ValueError):
            machine.step()


if __name__ == "__main__":
    unittest.main()
