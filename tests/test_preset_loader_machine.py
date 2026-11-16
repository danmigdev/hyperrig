"""Independent loader ordering, binding and report checks on original instructions."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class PresetLoaderInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from preset_loader_machine import PresetLoaderProgram
        from verify_preset_loader import baseline, record, payload_case, Flash, Script, route
        cls.program = PresetLoaderProgram()
        cls.initial, cls.record, cls.payload = staticmethod(baseline), staticmethod(record), staticmethod(payload_case)
        cls.flash, cls.script, cls.route = Flash, Script, staticmethod(route)

    def execute(self, operation, *arguments, memory=None, regions=(), failures=None, plan=None,
                clocks=(100, 500, 600, 1000), outputs=(0, 0)):
        flash = self.flash(regions, failures)
        return self.program.execute(memory or self.initial(), operation, *arguments, reader=flash.read,
            boundary=self.script(plan, clocks), application_outputs=outputs)

    def load(self, *, memory=None, plan=None, **kwargs):
        return self.execute("load", 0, memory=memory, regions=((0xBF000, self.record(b"\x05")),), plan=plan, **kwargs)

    def notifications(self, result):
        return [args for service, args, _ in result["calls"] if service == 0x2002D10]

    def test_rate_wraps_multiplication_before_dividing(self):
        for calibration, expected in ((0, 0), (1, 166), (6, 1000), (240, 40000),
                                       (4294968, 117), (0xFFFFFFFF, 715827716)):
            memory = self.initial()
            struct.pack_into("<I", memory[0], 44, calibration)
            self.assertEqual(self.execute("rate", memory=memory)["result"], expected)

    def test_elapsed_uses_unsigned_clock_wrap(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 44, 6)
        result = self.execute("elapsed", 0xFFFFFFF0, memory=memory, clocks=(984,))
        self.assertEqual(result["result"], 1)

    def test_elapsed_reads_calibration_after_clock_callback(self):
        result = self.execute("elapsed", 0,
            plan={0x1C04862: (80000, ((0x1C1F180 + 44, 480, 4),))})
        self.assertEqual(result["result"], 1)

    def test_report_captures_counter_before_clock_and_saturates_duration(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 44, 1)
        struct.pack_into("<I", memory[13], 0, 10)
        result = self.execute("report", 3, 0x01000001, 0, 8, memory=memory,
            plan={0x1C04862: (166 * 65536, ((0x1C26890 + 4092, 999, 4),))})
        self.assertEqual(self.notifications(result), [(26, 0x103, 0x2FFFF)])

    def test_report_counter_underflow_saturates_unsigned_difference(self):
        result = self.execute("report", 0, 0, 0, 1, clocks=(0,))
        self.assertEqual(self.notifications(result), [(26, 0, 0x7FFF0000)])

    def test_snapshot_encodes_type_bindings_and_includes_last_record(self):
        memory = self.initial()
        memory[0][236:245] = bytes((8, 77, 2, 8, 4, 255, 7, 8, 9))
        memory[0][269:272] = bytes((8, 55, 130))
        result = self.execute("snapshot", memory=memory)
        self.assertEqual(result["memory"][9][:9], bytes((8, 130, 77, 8, 4, 255, 7, 8, 9)))
        self.assertEqual(result["memory"][9][33:36], bytes((8, 130, 55)))
        self.assertEqual(result["memory"][9][36:], bytes([0xC3] * 4))
        self.assertEqual(result["memory"][0], memory[0])

    def test_binding_counts_previous_duplicates_including_type_zero(self):
        for position, expected in enumerate(((6, 0), (24, 0), (6, 1), (0, 0), (24, 1), (0, 1))):
            memory = self.initial()
            memory[10][:7] = bytes((6, 6, 24, 6, 0, 24, 0))
            result = self.execute("binding", position, memory=memory)
            self.assertEqual(result["memory"][9][:2], bytes(expected))

    def test_binding_invalid_positions_clear_outputs(self):
        for position in (0, 16, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            result = self.execute("binding", position)
            self.assertEqual(result["memory"][9][:2], bytes(2))

    def test_rebind_without_absolute_effect_actions_has_no_writes(self):
        result = self.execute("rebind")
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["writes"], [])
        self.assertEqual(result["library_calls"], [])

    def test_rebind_preserves_missing_positions_and_counts_zero_types(self):
        memory = self.initial()
        self.route(memory, (3, 3, 255, 5), types={3: 6})
        for i, position in enumerate((0, 1, 2, 3, 9)):
            memory[0][236 + 3 * i:239 + 3 * i] = bytes((8, position, 255))
        result = self.execute("rebind", memory=memory)
        self.assertEqual(result["result"], 4)
        self.assertEqual(result["memory"][0][236:251], bytes((8, 6, 0, 8, 6, 1, 8, 0, 0, 8, 0, 1, 8, 9, 255)))

    def test_rebind_flattens_two_chains_and_caps_at_sixteen(self):
        memory = self.initial()
        self.route(memory, range(10), second=range(6, 16))
        memory[0][266:272] = bytes((8, 16, 255, 8, 15, 255))
        result = self.execute("rebind", memory=memory)
        self.assertEqual(result["result"], 1)
        self.assertEqual(result["memory"][0][266:272], bytes((8, 16, 255, 8, 6, 7)))

    def test_byte_comparison_returns_first_unsigned_byte_difference(self):
        for a, b, expected in ((0, 255, 0xFFFFFF01), (255, 0, 255)):
            memory = self.initial()
            memory[9][:36] = memory[10][:36] = bytes(36)
            memory[9][35], memory[10][35] = a, b
            self.assertEqual(self.execute("compare", 0, 0, 36, memory=memory)["result"], expected)
        self.assertEqual(self.execute("compare", 1, 3, 0)["result"], 0)

    def test_preflight_failures_collapse_to_minus_one_before_application(self):
        variants = ((self.record(b"", tag=0), None), (self.record(b"\x05"), {2: (1, 0)}),
                    (self.record(b"\x05", crc=0xBAD), None), (self.record(self.payload(1201, 4)), None))
        for encoded, failures in variants:
            memory = self.initial()
            struct.pack_into("<I", memory[0], 92, 9)
            result = self.execute("load", 0, memory=memory, regions=((0xBF000, encoded),), failures=failures)
            self.assertEqual(result["result"], 0xFFFFFFFF)
            self.assertEqual(struct.unpack_from("<I", result["memory"][0], 92)[0], 9)
            self.assertEqual(sum(call[0] == 0x1C04862 for call in result["calls"]), 1)
            self.assertFalse(any(call[0] == 0x20092FA for call in result["calls"]))
            self.assertEqual(self.notifications(result), [])

    def test_invalid_preset_clears_working_after_initial_clock(self):
        result = self.execute("load", 32)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual(result["calls"][0][0], 0x1C04862)
        self.assertEqual(result["calls"][0][2][11], bytes([0x77] * 1490))
        self.assertEqual(result["calls"][1][2][11], bytes(1490))

    def test_nonzero_application_result_is_reported_after_commit(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 92, 9)
        result = self.load(memory=memory, plan={0x20092FA: (0xFFFFFFFF, ())})
        self.assertEqual(result["result"], 0)
        application = next(call for call in result["calls"] if call[0] == 0x20092FA)
        self.assertEqual(application[1], (0, 4, 0))
        self.assertEqual(struct.unpack_from("<I", application[2][0], 92)[0], 9)
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 92)[0], 0)
        self.assertEqual(self.notifications(result)[-1], (6, 0, 0xFFFFFFFF))

    def test_saved_snapshot_updates_only_when_tracking_match_and_rewrite(self):
        for tracking, matches, position in ((1, True, 1), (0, True, 1), (1, False, 1), (1, True, 255)):
            memory = self.initial()
            self.route(memory, (0, 1))
            memory[0][236:239] = bytes((8, position, 255))
            memory[1][736] = tracking
            if matches:
                memory[12][:] = memory[0][236:272]
            result = self.load(memory=memory)
            if tracking and matches and position == 1:
                self.assertEqual(result["memory"][12][:3], bytes((8, 128, 6)))
                self.assertEqual(result["memory"][0][236:239], bytes((8, 6, 0)))
            else:
                self.assertEqual(result["memory"][12], memory[12])

    def test_snapshot_uses_actions_written_by_application(self):
        memory = self.initial()
        self.route(memory, (0, 1))
        memory[1][736] = 1
        memory[12][:3] = bytes((8, 1, 255))
        result = self.load(memory=memory,
            plan={0x20092FA: (0, ((0x1C1F180 + 236, 0xFF0108, 3),))})
        self.assertEqual(result["memory"][12][:3], bytes((8, 128, 6)))

    def test_report_notification_can_change_final_notification_suppression(self):
        for before, after in ((0, 1), (1, 0)):
            memory = self.initial()
            memory[1][740] = before
            result = self.load(memory=memory,
                plan={(0x2002D10, 26): (0, ((0x1C26890 + 740, after, 1),))})
            self.assertEqual([args[0] for args in self.notifications(result)], [26] if after else [26, 6])

    def test_load_uses_captured_preflight_rate_and_later_report_rate(self):
        result = self.load(clocks=(100, 500, 600, 80600), plan={
            (0x1C04862, "call", 3): (600, ((0x1C1F180 + 44, 480, 4), (0x1C26890 + 4092, 4, 4))),
            0x20092FA: (0, ((0x1C26890 + 4092, 5, 4),)),
            (0x1C04862, "call", 4): (80600, ((0x1C26890 + 4092, 100, 4),))})
        self.assertEqual(self.notifications(result)[0], (26, 10 << 8, 0x10001))

    def test_application_output_words_are_not_read_by_loader(self):
        with_outputs = self.load(outputs=(0x12345678, 0x87654321))
        without_outputs = self.load(outputs=(None, None))
        self.assertEqual(with_outputs["memory"], without_outputs["memory"])
        self.assertEqual(with_outputs["calls"], without_outputs["calls"])
        self.assertEqual(without_outputs["result"], 0)

    def test_notification_changes_are_not_overwritten_by_a_second_commit(self):
        result = self.load(plan={(0x2002D10, 6): (0xFFFFFFFF, ((0x1C1F180 + 92, 23, 4),))})
        self.assertEqual(result["result"], 0)
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 92)[0], 23)

    def test_navigation_skips_crc_valid_but_unsupported_old_layout(self):
        regions = ((0xBF800, self.record(self.payload(1201, 4))), (0xC0000, self.record(b"\x05")))
        result = self.execute("preset_step", 1, regions=regions)
        self.assertEqual([args[0] for service, args, _ in result["calls"] if service == 0x20092FA], [2])
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 92)[0], 2)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 732)[0], 6)

    def test_press_edge_reaches_real_validation_preflight_and_loader(self):
        memory = self.initial()
        memory[0][236] = 3
        result = self.execute("edge", 0, 1, 100, 200, memory=memory,
                              regions=((0xBF800, self.record(b"\x05")),))
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 92)[0], 1)
        self.assertTrue(any(call[0] == 0x20092FA for call in result["calls"]))

    def test_hold_timer_reaches_loader(self):
        memory = self.initial()
        memory[0][239:242] = bytes((2, 1, 255))
        memory[1][1567] = 1
        result = self.execute("tick", 1000, memory=memory, regions=((0xBF800, self.record(b"\x05")),))
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 92)[0], 1)
        self.assertTrue(any(call[0] == 0x20092FA for call in result["calls"]))

    def test_oracle_rejects_zero_timing_divisors_and_unbounded_lists(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 44, 0)
        with self.assertRaisesRegex(ValueError, "calibration domain"):
            self.execute("load", 0, memory=memory)
        memory = self.initial()
        memory[10][0] = 17
        with self.assertRaisesRegex(ValueError, "type-list domain"):
            self.execute("binding", 0, memory=memory)


if __name__ == "__main__":
    unittest.main()
