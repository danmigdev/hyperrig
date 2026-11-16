"""Cross-module instruction witnesses for generated-coefficient sample blocks."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from biquad_pipeline_machine import BiquadPipelineProgram, DIVISOR
from biquad_chain_machine import ACTIVE
from verify_biquad_pipeline import initial, clocked, DEFAULT_CLOCK
from pi32v2isa import codec, table


class PipelineInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = BiquadPipelineProgram()

    def block(self, memory=None, samples=(), changes=(), script=DEFAULT_CLOCK):
        return self.program.execute(clocked() if memory is None else memory, list(samples), changes, script)

    def test_signed_getter_and_ignored_index(self):
        for byte, expected in ((128, -128), (244, -12), (255, -1), (0, 0), (12, 12), (127, 127)):
            memory = initial()
            memory[8][3] = byte
            self.assertEqual(self.program.generator.parameter(memory, 3)["value"], expected)
        for index in (5, 0x80000000, 0xFFFFFFFF):
            self.assertEqual(self.program.generator.parameter(initial(), index)["value"], 0)

    def test_zero_frame_applies_generated_coefficients_and_preserves_history(self):
        memory = clocked()
        result = self.block(memory, changes=((0, 6),))
        self.assertNotEqual(result["memory"][1][:20], bytes(memory[1][:20]))
        self.assertEqual(result["memory"][1][:20], result["memory"][0][:20])
        self.assertEqual(result["memory"][1][20:40], bytes(memory[1][20:40]))
        self.assertFalse(result["kernel_calls"])
        self.assertEqual(result["memory"][5], bytes(5))
        self.assertEqual(len(result["clocks"]), 2)

    def test_duplicate_changes_publish_last_parameter_and_count_every_request(self):
        result = self.block(changes=((0, -12), (0, 12), (0, 0)))
        self.assertEqual(result["memory"][8][0], 0)
        self.assertEqual(int.from_bytes(result["memory"][7], "little"), 1)
        self.assertEqual(result["memory"][1][40], 0)
        self.assertEqual(len(result["stages"]), 3)

    def test_disabling_final_filter_keeps_history_and_skips_clock(self):
        seeded = self.block(samples=(1000000, 0, 0), changes=((0, 6),))["memory"]
        disabled = self.block(seeded, samples=(123, 456), changes=((0, 0),))
        self.assertEqual(disabled["samples"], [123, 456])
        self.assertEqual(disabled["memory"][1][20:40], seeded[1][20:40])
        self.assertFalse(disabled["clocks"])

    def test_clock_staging_waits_for_next_active_update(self):
        seeded = self.block(samples=(1000000,), changes=((0, 6),))["memory"]
        changed = self.block(seeded, samples=(0, 0), script=((100, ((0, -12),), ()), (500, (), ())))
        self.assertEqual(changed["memory"][5][0], 1)
        self.assertEqual(changed["memory"][1][:20], seeded[1][:20])
        self.assertNotEqual(changed["memory"][0][:20], seeded[0][:20])
        applied = self.block(changed["memory"], samples=())
        self.assertEqual(applied["memory"][5][0], 0)
        self.assertEqual(applied["memory"][1][:20], changed["memory"][0][:20])
        self.assertEqual(applied["memory"][1][20:40], changed["memory"][1][20:40])

    def test_end_clock_request_resets_average_before_accounting(self):
        seeded = self.block(samples=(1000000,), changes=((0, 6),))["memory"]
        changed = self.block(seeded, samples=(0,), script=((1000, (), ()), (1600, ((1, -6),), ())))
        self.assertEqual(int.from_bytes(changed["memory"][3], "little"), 600)
        self.assertEqual(changed["memory"][5][1], 1)
        self.assertEqual(changed["memory"][1][84], 0)

    def test_counter_and_elapsed_wrap_survive_integration(self):
        memory = clocked()
        memory[7][:] = bytes.fromhex("ffffffff")
        result = self.block(memory, samples=(1,), changes=((0, 6),),
                            script=((0xFFFFFFF0, (), ()), (0x20, (), ())))
        self.assertEqual(result["memory"][7], bytes(4))
        self.assertEqual(int.from_bytes(result["memory"][3], "little"), 48)
        self.assertEqual(int.from_bytes(result["memory"][4], "little"), 32)

    def test_ignored_request_does_not_generate_coefficients(self):
        result = self.block(samples=(1, -1), changes=((0xFFFFFFFF, 12),))
        self.assertFalse(result["math_calls"])
        self.assertFalse(result["kernel_calls"])
        self.assertEqual(result["samples"], [1, -1])
        self.assertEqual(len(result["stages"]), 1)

    def test_actual_generated_flags_choose_expected_kernels(self):
        result = self.block(samples=(1000000, 0, 0), changes=tuple((i, 6) for i in range(5)))
        self.assertEqual(result["kernel_calls"], [("residual", 0, 3),
                         *(('rounded', i, 3) for i in range(1, 5))])
        self.assertTrue(result["math_calls"])
        self.assertEqual(len(result["normalization_calls"]), 5)

    def test_clock_can_select_alternate_kernel_without_replacing_coefficients(self):
        result = self.block(samples=(1, -1, 0), changes=((0, 6),),
                            script=((100, (), ((ACTIVE+41, 0, 1),)), (500, (), ())))
        self.assertEqual(result["kernel_calls"], [("rounded", 0, 3)])
        self.assertEqual(result["memory"][0][:20], result["memory"][1][:20])

    def test_reset_and_startup_divisors_have_distinct_evidence(self):
        self.assertEqual(int.from_bytes(self.program.static["divisor_reset_word"], "little"), 48000)
        instructions = table.load()
        raw = self.program.static["startup_call_window"]
        instruction, fields, _ = codec.decode(instructions, raw, 0x02002504-0x020024EC)
        self.assertEqual(codec.format(instruction, fields), "r0 = 48077")
        raw = self.program.static["global_initializer"]
        instruction, fields, _ = codec.decode(instructions, raw, 0x0202911A-0x02029112)
        self.assertEqual(codec.format(instruction, fields), "[r2+8] = r0")

    def test_startup_word_changes_generated_coefficients(self):
        reset = self.block(clocked(48000), changes=((4, 12),))
        startup = self.block(clocked(48077), changes=((4, 12),))
        self.assertNotEqual(reset["memory"][0][176:196], startup["memory"][0][176:196])
        self.assertEqual(startup["memory"][-1], struct.pack("<I", 48077))

    def test_native_caller_window_passes_128_to_chain(self):
        raw = self.program.static["block_caller_window"]
        instructions = table.load()
        instruction, fields, _ = codec.decode(instructions, raw, 0x01C026DA-0x01C026CE)
        self.assertEqual(codec.format(instruction, fields), "r1 = 128")
        instruction, fields, size = codec.decode(instructions, raw, 0x01C026DE-0x01C026CE)
        displacement = int(codec.format(instruction, fields).split()[1])
        self.assertEqual(0x01C026DE + size + displacement, 0x01C051F0)

    def test_clock_cannot_write_immutable_divisor(self):
        with self.assertRaises(ValueError):
            self.block(samples=(0,), changes=((0, 6),), script=((0, (), ((DIVISOR, 0, 4),)),))

    def test_verifier_rejects_invalid_buffers_and_request_counts(self):
        for samples, changes in (([0]*129, ()), ([0], [(0, 0)]*17), ([1 << 31], ())):
            with self.assertRaises(ValueError):
                self.block(samples=samples, changes=changes)
        with self.assertRaises(ValueError):
            self.block(samples=(0,), changes=((0, 6),), script=())


if __name__ == "__main__":
    unittest.main()
