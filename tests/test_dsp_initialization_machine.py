"""Focused original-instruction checks for DSP initialization and guarded startup."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class DspInitializationInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from dsp_initialization_machine import DspInitializationProgram
        from verify_dsp_initialization import baseline, StartupScript
        cls.program, cls.initial, cls.Script = DspInitializationProgram(), staticmethod(baseline), StartupScript

    def execute(self, operation, *args, memory=None, **script):
        return self.program.execute(memory or self.initial(), operation, *args, boundary=self.Script(**script))

    def test_q16_zero_halfway_sign_and_special_values(self):
        for value, expected in ((0, 0), (0x80000000, 0), (0x37000000, 1), (0xB7000000, 0xFFFFFFFF),
            (0x3F800000, 65536), (0xBF800000, 0xFFFF0000), (0x7F800000, 0x7FFFFFFF),
            (0xFF800000, 0x80000000), (0x7FC00000, 0x7FFFFFFF), (0xFFC00000, 0x7FFFFFFF)):
            with self.subTest(value=hex(value)):
                self.assertEqual(self.execute("q16", value)["value"], expected)

    def test_zero_gain_takes_exact_fast_path(self):
        result = self.execute("gain", 0)
        self.assertEqual(result["value"], 65536)
        self.assertFalse(result["math_calls"])
        self.assertEqual(result["memory"], tuple(bytes(x) for x in self.initial()))

    def test_second_table_setup_modes_and_frequencies(self):
        from biquad_coefficients_machine import FLOAT
        from fractions import Fraction
        for index, mode, frequency in ((1, 0, 150), (2, 1, 650), (3, 2, 2000), (4, 2, 4500)):
            result = self.execute("setup", index, 120, 3)
            section, request, _ = result["production_calls"][0]
            self.assertEqual(section, 3)
            self.assertEqual(request, (mode, FLOAT.encode(Fraction(frequency)), 0x41400000, 0x3F333333))

    def test_setup_preserves_history_residue_and_reserved_bytes(self):
        memory = self.initial()
        result = self.execute("setup", 2, 60, 1, memory=memory)
        self.assertEqual(result["memory"][5][44+20:44+40], memory[5][44+20:44+40])
        self.assertEqual(result["memory"][5][44+42:44+44], memory[5][44+42:44+44])
        self.assertEqual(result["memory"][5][:44], memory[5][:44])
        self.assertEqual(result["memory"][5][88:], memory[5][88:])

    def test_filter_reset_clears_histories_and_keeps_parameter_storage(self):
        memory = self.initial(parameters=(10, -120, 0, 120, 60))
        result = self.execute("reset_filters", memory=memory)
        self.assertEqual(len(result["production_calls"]), 4)
        for i in range(4):
            self.assertEqual(result["memory"][5][44*i+20:44*i+40], bytes(20))
            self.assertEqual(result["memory"][5][44*i+42:44*i+44], memory[5][44*i+42:44*i+44])
        self.assertEqual(result["memory"][4][218:228], memory[4][218:228])
        self.assertEqual(result["memory"][4][1], 0)
        self.assertEqual(result["memory"][4][28], 1)
        self.assertEqual(result["memory"][4][32:36], bytes(4))

    def test_route_reset_matches_enabled_ids_and_wraps_counter(self):
        memory = self.initial()
        memory[3][1] = 3
        memory[3][4] = 255
        memory[3][449] = 3
        memory[4][211] = 0
        result = self.execute("reset_slot", 3, memory=memory)
        self.assertEqual(result["memory"][3][0], 0)
        self.assertEqual(result["memory"][3][4], 0)
        self.assertEqual(result["memory"][4][210], 0)
        self.assertEqual(result["memory"][3][448:896], memory[3][448:896])
        self.assertEqual(result["memory"][4][319], 0)
        self.assertEqual(result["memory"][2], memory[2])

    def test_unsigned_out_of_range_slot_changes_nothing(self):
        memory = self.initial()
        for slot in (256, 0x80000000, 0xFFFFFFFF):
            result = self.execute("reset_slot", slot, memory=memory)
            self.assertEqual(result["memory"], tuple(bytes(x) for x in memory))

    def test_initializer_resets_only_routes_assigned_to_slots_zero_through_fifteen(self):
        memory = self.initial()
        memory[3][1] = 16
        result = self.execute("initialize", 48077, 0, memory=memory)
        self.assertEqual(result["memory"][3][:448], memory[3][:448])
        self.assertEqual(result["memory"][4][210], 1)
        self.assertEqual(result["memory"][4][211:218], bytes(7))
        self.assertEqual(result["memory"][4][316:332], bytes(16))
        for i in range(16):
            self.assertEqual(result["memory"][2][480*i+2], 0)
            self.assertEqual(result["memory"][2][480*i+3:480*(i+1)], memory[2][480*i+3:480*(i+1)])

    def test_initializer_writes_divisor_before_generating_four_sections(self):
        memory = self.initial(48000, (12, 20, -40, 60, -80))
        result = self.execute("initialize", 48077, 0xF1E2D3C4, memory=memory)
        for _, _, snapshot in result["production_calls"]:
            self.assertEqual(struct.unpack_from("<I", snapshot[0], 36)[0], 48077)
            self.assertEqual(struct.unpack_from("<I", snapshot[4], 48)[0], 0xF1E2D3C4)
        self.assertEqual(len(result["production_calls"]), 4)
        self.assertEqual(result["memory"][4][218:228], memory[4][218:228])

    def test_initializer_six_lane_defaults_and_two_index_fields(self):
        result = self.execute("initialize", 48077, 0)
        control = result["memory"][4]
        self.assertEqual(control[368:416], bytes(48))
        self.assertEqual(struct.unpack_from("<12I", control, 496), (0x8000,)*12)
        self.assertEqual(control[180:186], bytes([255])*6)
        for offset in (174, 186, 192, 198, 204):
            self.assertEqual(control[offset:offset+6], bytes(6))
        self.assertEqual(control[230:242], bytes(12))
        self.assertEqual(control[16:22], bytes((0, 0, 0, 0, 1, 2)))

    def test_guard_precedes_service_and_initializer_precedes_dynamics(self):
        from dsp_initialization_machine import PLATFORM_INPUT, DYNAMICS_CONFIGURE
        result = self.execute("startup", memory=self.initial(48000, (12, 20, -40, 60, -80)))
        first, second = result["boundary_calls"]
        self.assertEqual((first[0], first[1]), (PLATFORM_INPUT, (0, 0, 0)))
        self.assertEqual(first[2][1][0], 1)
        self.assertEqual(struct.unpack_from("<I", first[2][0], 36)[0], 48000)
        self.assertEqual((second[0], second[1]), (DYNAMICS_CONFIGURE, (1, 0xFFFFFFFD, 100)))
        self.assertEqual(struct.unpack_from("<I", second[2][0], 36)[0], 48077)
        self.assertEqual(second[2][4][28], 1)
        self.assertEqual(struct.unpack_from("<II", result["memory"][4], 52), (0x0201A864, 0x0201A96A))
        self.assertEqual(struct.unpack_from("<I", result["memory"][6], 8)[0], 0x01C04862)

    def test_repeated_startup_skips_services_and_preserves_memory(self):
        result = self.execute("startup")
        repeated = self.program.execute(result["memory"], "startup")
        self.assertEqual(repeated["memory"], result["memory"])
        self.assertFalse(repeated["boundary_calls"])
        self.assertFalse(repeated["production_calls"])

    def test_startup_boundary_mutations_obey_subsequent_read_and_write_order(self):
        from dsp_initialization_machine import PLATFORM_INPUT, DYNAMICS_CONFIGURE, CONTROL, CALLBACKS, DIVISOR
        result = self.execute("startup", mutations={PLATFORM_INPUT: ((CONTROL+220, 120, 2),),
            DYNAMICS_CONFIGURE: ((DIVISOR, 44100, 4), (CONTROL+52, 0x12345678, 4),
                                (CALLBACKS+8, 0x12345678, 4), (CONTROL+180, 31, 1))})
        self.assertEqual(result["production_calls"][0][1][2], 0x41400000)
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 36)[0], 44100)
        self.assertEqual(struct.unpack_from("<I", result["memory"][4], 52)[0], 0x0201A864)
        self.assertEqual(struct.unpack_from("<I", result["memory"][6], 8)[0], 0x01C04862)
        self.assertEqual(result["memory"][4][180], 31)

    def test_stored_parameter_domain_is_checked_only_for_entered_reset_paths(self):
        memory = self.initial()
        struct.pack_into("<h", memory[4], 220, 1281)
        for operation, arguments in (("initialize", (48077, 0)), ("reset_filters", ()), ("startup", ())):
            with self.assertRaises(ValueError):
                self.execute(operation, *arguments, memory=memory)
        memory[1][0] = 255
        result = self.program.execute(memory, "startup")
        self.assertEqual(result["memory"], tuple(bytes(x) for x in memory))

    def test_reset_copy_divisor_and_second_table_are_bound_to_original_bytes(self):
        self.assertEqual(self.program.divisor_reset, struct.pack("<I", 48000))
        self.assertEqual(self.program.initialization_table, struct.pack("<5H", 0, 150, 650, 2000, 4500))


if __name__ == "__main__":
    unittest.main()
