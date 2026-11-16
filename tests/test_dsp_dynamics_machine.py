"""Focused original-instruction witnesses for dynamics setup and state access."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class DspDynamicsInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from dsp_dynamics_machine import DspDynamicsProgram
        from verify_dsp_initialization import baseline
        from verify_dsp_dynamics import Platform
        cls.program, cls.initial, cls.Platform = DspDynamicsProgram(), staticmethod(baseline), Platform

    def execute(self, operation, *args, memory=None, **script):
        return self.program.execute(self.initial() if memory is None else memory,
                                    operation, *args, boundary=self.Platform(**script))

    def test_startup_arguments_produce_original_integer_words(self):
        result = self.execute("configure", 1, 0xFFFFFFFD, 100, memory=self.initial(48077))
        self.assertEqual(struct.unpack_from("<II", result["memory"][0], 52), (8103821, 3484))
        self.assertEqual(struct.unpack_from("<hh", result["memory"][0], 30), (-3, 100))
        self.assertEqual(result["value"], 1)

    def test_signed_threshold_clamp_handles_both_extremes(self):
        for value, expected in ((0x80000000, -200), (0xFFFFFF37, -200), (0xFFFFFF38, -200),
                                (0xFFFFFFFF, -1), (0, 0), (1, 0), (0x7FFFFFFF, 0)):
            result = self.execute("configure", 1, value, 100)
            self.assertEqual(struct.unpack_from("<h", result["memory"][0], 30)[0], expected)

    def test_signed_time_clamp_handles_both_extremes(self):
        for value, expected in ((0x80000000, 10), (0xFFFFFFFF, 10), (0, 10), (9, 10), (10, 10),
                                (11, 11), (1999, 1999), (2000, 2000), (2001, 2000), (0x7FFFFFFF, 2000)):
            result = self.execute("configure", 1, 0, value)
            self.assertEqual(struct.unpack_from("<h", result["memory"][0], 32)[0], expected)

    def test_every_nonzero_enable_normalizes_to_one(self):
        for value in (0, 1, 2, 255, 0x80000000, 0xFFFFFFFF):
            result = self.execute("configure", value, 0, 100)
            self.assertEqual(result["value"], bool(value))
            self.assertEqual(result["memory"][6][764], bool(value))

    def test_configuration_write_order_and_reserved_bytes(self):
        from dsp_dynamics_machine import CONFIGURATION, CONTROL, CALLBACKS
        memory = self.initial(48077)
        result = self.execute("configure", 1, 0xFFFFFFFD, 100, memory=memory)
        public = [(address, size) for address, _, size in result["writes"] if address < 0x30000000]
        self.assertEqual(public, [(CONFIGURATION+30, 2), (CONFIGURATION+32, 2), (CONFIGURATION+52, 4),
                                 (CONFIGURATION+56, 4), (CONTROL+108, 4), (CALLBACKS+764, 1)])
        for region in (1, 2, 3, 5):
            self.assertEqual(result["memory"][region], memory[region])
        self.assertEqual(result["memory"][0][34:52], memory[0][34:52])
        self.assertEqual(result["memory"][0][60:], memory[0][60:])
        self.assertEqual(result["memory"][4][112:], memory[4][112:])

    def test_minimum_positive_divisor_runs_extended_original_exp(self):
        result = self.execute("configure", 1, 0xFFFFFF38, 10, memory=self.initial(1))
        self.assertEqual(struct.unpack_from("<II", result["memory"][0], 52), (838860, 1048576))
        self.assertGreater(result["steps"], 10000)
        self.assertFalse(result["boundary_calls"])

    def test_large_divisor_reaches_coefficient_minimum(self):
        result = self.execute("configure", 1, 0, 2000, memory=self.initial(0xFFFFFFFF))
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 56)[0], 1)

    def test_zero_divisor_is_outside_terminating_domain(self):
        with self.assertRaisesRegex(ValueError, "zero divisor"):
            self.execute("configure", 1, 0, 100, memory=self.initial(0))

    def test_getter_reads_raw_byte_and_sign_extended_halfwords(self):
        memory = self.initial()
        memory[6][764] = 255
        struct.pack_into("<HH", memory[0], 30, 0x8000, 0x7FFF)
        result = self.execute("get", memory=memory)
        self.assertEqual(result["outputs"], (255, 0xFFFF8000, 0x7FFF))
        self.assertEqual(result["memory"], tuple(bytes(x) for x in memory))

    def test_meter_first_output_is_optional_and_does_not_reset(self):
        memory = self.initial()
        struct.pack_into("<I", memory[4], 112, 0xDEADBEEF)
        for mask in (0, 1):
            result = self.execute("meter", mask, memory=memory)
            self.assertEqual(result["value"], 48)
            self.assertEqual(result["memory"], tuple(bytes(x) for x in memory))
            self.assertEqual(result["outputs"][0], 0xDEADBEEF if mask else 0xA5A5A500)

    def test_meter_second_output_copies_then_resets_and_carries(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 60, 0xFFFF0001)
        first = self.execute("meter", 2, memory=memory)
        self.assertEqual(first["outputs"][1], 0xFFFF0001)
        second = self.execute("meter", 2, memory=first["memory"])
        self.assertEqual(second["outputs"][1], 0x1000000)
        self.assertEqual(first["memory"], second["memory"])

    def test_integrated_startup_executes_dynamics_internally(self):
        from dsp_dynamics_machine import PLATFORM_INPUT
        result = self.execute("startup", memory=self.initial(0))
        self.assertEqual([call[0] for call in result["boundary_calls"]], [PLATFORM_INPUT])
        self.assertEqual(len(result["production_calls"]), 4)
        self.assertEqual(len(result["dynamics_calls"]), 1)
        arguments, at_entry = result["dynamics_calls"][0]
        self.assertEqual(arguments, (1, 0xFFFFFFFD, 100))
        self.assertEqual(struct.unpack_from("<I", at_entry[0], 36)[0], 48077)
        self.assertEqual(struct.unpack_from("<II", result["memory"][0], 52), (8103821, 3484))
        self.assertEqual(result["memory"][6][764], 1)

    def test_platform_callback_runs_after_guard_before_initialization(self):
        from dsp_dynamics_machine import CONFIGURATION, CONTROL
        memory = self.initial(44100)
        result = self.execute("startup", memory=memory, result=0x89ABCDEF,
            mutations=((CONFIGURATION+36, 0, 4), (CONTROL+108, 0xDEADBEEF, 4)))
        _, _, before, after = result["boundary_calls"][0]
        self.assertEqual(before[1][0], 1)
        self.assertEqual(struct.unpack_from("<I", before[0], 36)[0], 44100)
        self.assertEqual(struct.unpack_from("<I", after[0], 36)[0], 0)
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 36)[0], 48077)
        self.assertEqual(struct.unpack_from("<I", result["memory"][4], 48)[0], 0x89ABCDEF)
        self.assertEqual(result["memory"][4][108:112], bytes(4))

    def test_guarded_startup_preserves_everything_without_services(self):
        memory = self.initial(0)
        memory[1][0] = 255
        result = self.program.execute(memory, "startup")
        self.assertEqual(result["memory"], tuple(bytes(x) for x in memory))
        self.assertFalse(result["boundary_calls"])
        self.assertFalse(result["dynamics_calls"])

    def test_original_reset_copy_is_evidence_not_current_computed_state(self):
        raw = self.program.reset_configuration
        self.assertEqual(struct.unpack_from("<hhI", raw, 2), (-3, 100, 0xBB800201))
        self.assertEqual(struct.unpack_from("<I", raw, 8)[0], 48000)
        self.assertEqual(struct.unpack_from("<III", raw, 24), (8388607, 1, 16777216))


if __name__ == "__main__":
    unittest.main()
