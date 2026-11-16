"""Focused original-instruction witnesses for capture command semantics."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from capture_command_machine import CaptureCommandProgram, ERROR_WORD, ALLOCATE, FREE, PRINT, REPORT
from capture_journal_machine import WRAPPED_READ, RAW_READ, PROGRAM, ERASE_SECTOR, NOTIFY
from verify_capture_command import baseline, fixture, Environment
from verify_capture_metadata import slot_address, capacity, journal


class CommandInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = CaptureCommandProgram()

    def command(self, text, memory=None, **script):
        environment = Environment(**script)
        return self.program.execute(baseline() if memory is None else memory, "command", text,
                                    boundary=environment), environment

    def test_current_query_has_no_storage_calls(self):
        result, _ = self.command(b"")
        self.assertEqual([call[0] for call in result["calls"]], [REPORT])
        self.assertEqual(result["calls"][0][1], (0x02035C66, 2, 3, 1, 0xFFFFFFD1, 0, 0, 0, 0, 0))

    def test_current_invalid_slot_maps_to_negative_one(self):
        memory = baseline(); memory[0][9] = 255
        result, _ = self.command(b"live", memory)
        self.assertEqual(result["calls"][-1][1][1], 0xFFFFFFFF)

    def test_live_gain_uses_half_unit_steps_and_retains_auxiliary(self):
        result, _ = self.command(b"live -3.5")
        self.assertEqual(struct.unpack_from("<i", result["memory"][1], 696)[0], -7)
        self.assertEqual(struct.unpack_from("<i", result["memory"][1], 700)[0], -47)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 276)[0], 0xFFFFFFFF)
        self.assertEqual(result["memory"][1][16], 0)

    def test_clear_auxiliary_preserves_hidden_report_value(self):
        result, _ = self.command(b"live 1 -")
        self.assertEqual(result["memory"][1][700:708], bytes(8))
        self.assertEqual(result["calls"][-1][1][3:5], (0, 0xFFFFFFD1))

    def test_input_level_requires_complete_integer_token(self):
        for text in (b"live 1 20 ", b"live 1 - ", b"live 1 20.0", b"live 1 -201", b"live 1 401"):
            result, _ = self.command(text)
            self.assertEqual(result["calls"][-1][1], (0x02037440, 0xFFFFFF38, 400))
        result, _ = self.command(b"live 1 \t20")
        self.assertEqual(result["calls"][-1][0], REPORT)
        self.assertEqual(result["calls"][-1][1][4], 20)

    def test_trim_step_range_and_one_fraction_digit(self):
        for text in (b"live .5", b"live 0.1", b"live 1.50", b"live 12.5", b"live 1.5\t"):
            result, _ = self.command(text)
            self.assertEqual(result["calls"][-1][1], (0x02037760,))

    def test_native_decimal_overflow_saturates_and_sets_errno(self):
        for text, expected in ((b"2147483648", 0x7FFFFFFF), (b"-2147483649", 0x80000000)):
            result = self.program.execute(baseline(), "decimal", text)
            self.assertEqual(result["result"], expected)
            self.assertEqual(result["end"], len(text))
            self.assertEqual(int.from_bytes(result["memory"][-1], "little"), 34)

    def test_tenths_parallel_packet_uses_original_string_pointer(self):
        result = self.program.execute(baseline(), "tenths", b"-3.5 next")
        self.assertEqual(result["result"], 1)
        self.assertEqual(result["output"], (-35) & 0xFFFFFFFF)

    def test_metadata_pack_clamps_signed_fields(self):
        result = self.program.execute(baseline(), "pack", arguments=(0x80000000, 1, 0x7FFFFFFF))
        self.assertEqual(result["result"], 0x010190E8)

    def test_slot_bounds_and_keyword_are_exact(self):
        for text in (b"15", b"-1", b"LIVE", b"livel", b"live\t0"):
            result, _ = self.command(text)
            self.assertEqual(result["calls"][-1][1], (0x02036399,))

    def test_slot_parser_accepts_immediate_signed_gain_token(self):
        result, _ = self.command(b"2-1.0", regions=fixture())
        self.assertEqual(result["calls"][-1][1][2], 0xFFFFFFFE)

    def test_query_unpacks_version_one_auxiliary_metadata(self):
        result, _ = self.command(b"2", regions=fixture(metadata=0x010190FE))
        self.assertEqual(result["calls"][-1][1][2:5], (0xFFFFFFFE, 1, 400))

    def test_invalid_slot_header_has_specific_early_message(self):
        result, _ = self.command(b"2")
        self.assertEqual(result["calls"][-1][1], (0x02036CED,))

    def test_unchanged_metadata_skips_writes_but_updates_current_gain(self):
        result, env = self.command(b"2 1.5", regions=fixture(metadata=3))
        self.assertNotIn(PROGRAM, env.counts)
        self.assertEqual(result["calls"][-1][1][5:7], (1, 1))
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 276)[0], 0xFFFFFFFF)

    def test_append_invalidates_cache_and_reports_incremented_cursor(self):
        result, env = self.command(b"2 2.5", regions=fixture())
        self.assertEqual(env.counts[PROGRAM], 1)
        self.assertNotIn(ALLOCATE, env.counts)
        self.assertEqual(result["memory"][15][2*20 + 16], 0)
        self.assertEqual(result["calls"][-1][1][7:10], (1, capacity(64), 0))

    def test_append_short_program_retries_next_record(self):
        result, env = self.command(b"2 2.5", regions=fixture(), programs={0: (0, 0)})
        self.assertEqual(env.counts[PROGRAM], 2)
        self.assertEqual(result["calls"][-1][1][7], 2)

    def test_full_log_runs_reload_rewrite_and_matching_free(self):
        result, env = self.command(b"2 2.5", regions=fixture(size=8152))
        self.assertEqual(result["allocations"], result["releases"])
        self.assertEqual(result["allocations"], 1)
        self.assertEqual(env.counts[ERASE_SECTOR], 2)
        self.assertEqual(result["calls"][-1][1][7:10], (0, 0, 1))

    def test_allocation_failure_does_not_free_or_program(self):
        result, env = self.command(b"2 2.5", regions=fixture(size=8152), results={(ALLOCATE, 0): 0})
        self.assertEqual(result["calls"][-1][1], (0x02036120, 0x020360B0))
        self.assertNotIn(FREE, env.counts)
        self.assertNotIn(PROGRAM, env.counts)

    def test_reload_read_failure_frees_and_maps_minus_two_to_minus_one(self):
        result, env = self.command(b"2 2.5", regions=fixture(size=8152), reads={(WRAPPED_READ, 3): (1, 0, None)})
        self.assertEqual(env.counts[FREE], 1)
        self.assertEqual(result["calls"][-1][1], (0x02036120, 0x0203670A))
        self.assertNotIn(ERASE_SECTOR, env.counts)

    def test_two_rewrite_failures_free_without_changing_gain(self):
        result, env = self.command(b"2 2.5", regions=fixture(size=8152), programs={0: (0, 0), 1: (0, 0)})
        self.assertEqual(env.counts[ERASE_SECTOR], 4)
        self.assertEqual(env.counts[FREE], 1)
        self.assertEqual(result["calls"][-1][1], (0x02036120, 0x020365BA))
        self.assertEqual(result["memory"][1][696:708], baseline()[1][696:708])

    def test_noncurrent_slot_does_not_apply_gain(self):
        result, _ = self.command(b"8 2.5", regions=fixture(slot=8))
        self.assertEqual(result["memory"][1][264:280], baseline()[1][264:280])

    def test_native_model_rejects_allocation_growth(self):
        layout = fixture(size=0) + journal(0, [(i, bytes(16)) for i in range(capacity(0))], slot_address(2))
        index = 2 + 2*((capacity(0) + 15)//16)
        with self.assertRaisesRegex(ValueError, "reload exceeds allocation"):
            self.command(b"2 2.5", regions=layout, replacements={(WRAPPED_READ, index): fixture(size=5)[0][1]})


if __name__ == "__main__":
    unittest.main()
