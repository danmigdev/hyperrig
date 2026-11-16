"""Independent byte-layout and failure checks for the preflight instruction oracle."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class PresetPreflightInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from preset_preflight_machine import PresetPreflightProgram
        from verify_preset_preflight import baseline, payload_case, record, Flash
        cls.program = PresetPreflightProgram()
        cls.initial = staticmethod(baseline)
        cls.payload = staticmethod(payload_case)
        cls.record = staticmethod(record)
        cls.flash = Flash

    def preflight(self, data, *, failures=None, encoded=None, memory=None, boundary=None):
        flash = self.flash(((0xBF000, encoded if encoded is not None else self.record(data)),), failures)
        return self.program.execute(memory or self.initial(), "preflight", 0,
                                    reader=flash.read, boundary=boundary)

    def convert(self, type_id, values, present=1):
        memory = self.initial()
        struct.pack_into("<7h", memory[10], 0, *values)
        return self.program.execute(memory, "convert_effect", type_id, present)

    @staticmethod
    def expanded_tail(data):
        expected = bytearray(data) + bytearray(1490 - len(data))
        for group in range(5):
            expected[1424 + 12 * group:1434 + 12 * group] = data[1424 + 10 * group:1434 + 10 * group]
            expected[1434 + 12 * group:1436 + 12 * group] = b"\0\0"
        return bytes(expected)

    def test_only_two_ids_need_conversion(self):
        for type_id in (0, 5, 6, 7, 23, 24, 25, 27, 29, 255, 0xFFFFFFFF):
            self.assertEqual(self.program.execute(self.initial(), "needs_conversion", type_id)["result"],
                             int(type_id in (6, 24)))

    def test_null_parameters_only_map_the_id(self):
        for type_id, expected in ((6, 27), (24, 29), (27, 27), (0xFFFFFFFF, 0xFFFFFFFF)):
            memory = self.initial()
            result = self.program.execute(memory, "convert_effect", type_id, 0)
            self.assertEqual(result["result"], expected)
            self.assertEqual(result["memory"], tuple(bytes(v) if i != 2 else v for i, v in enumerate(memory)))
            self.assertEqual(result["writes"], [])

    def test_unrelated_effect_parameters_are_preserved(self):
        values = (-32768, -1, 0, 1, 100, 101, 32767)
        result = self.convert(27, values)
        self.assertEqual(result["memory"][10][:14], struct.pack("<7h", *values))
        self.assertEqual(result["writes"], [])

    def test_effect6_signed_clamps_and_outputs(self):
        for inputs, expected in (((-32768, -1, -101), (40, 16, 0, 0, 0, 0, 40)),
                ((49, 70, 99), (64, 32, 49, 0, 99, 0, 40)),
                ((32767, 101, 100), (90, 81, 70, 0, 100, 0, 40))):
            result = self.convert(6, (*inputs, 77, 88, 99, 111))
            self.assertEqual(result["result"], 27)
            self.assertEqual(struct.unpack_from("<7h", result["memory"][10]), expected)
            self.assertEqual(result["memory"][10][14:], bytes([0x5A] * (1490 - 14)))

    def test_effect6_curve_rounding_and_endpoint(self):
        for value, expected in ((0, 16), (4, 17), (5, 18), (9, 19), (10, 19),
                                (50, 32), (90, 61), (99, 79), (100, 81)):
            result = self.convert(6, (value, 0, 0, 0, 0, 0, 0))
            self.assertEqual(struct.unpack_from("<h", result["memory"][10], 2)[0], expected)

    def test_effect24_preserves_negative_parameter_and_caps_only_upper_bound(self):
        for value, expected in ((-32768, -32768), (-1, -1), (0, 0), (27, 27), (28, 27), (32767, 27)):
            result = self.convert(24, (1, 2, 3, 4, value, 88, 99))
            self.assertEqual(result["result"], 29)
            self.assertEqual(struct.unpack_from("<7h", result["memory"][10]), (1, 2, 3, 4, expected, 50, 0))

    def test_out_of_range_preset_still_clears_and_prepares(self):
        memory = self.initial()
        result = self.program.execute(memory, "preflight", 32)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual([call[:2] for call in result["calls"]],
                         [(0x20031D4, (0, 0, 0)), (0x20054A8, (1, 0, 0)), (0x20054A8, (0, 0, 0))])
        self.assertEqual(result["calls"][0][2][11], bytes(1490))
        self.assertEqual(result["memory"][11], bytes(1490))
        self.assertEqual(result["memory"][9], bytes(memory[9]))

    def test_header_failure_retains_partial_header_but_zero_working(self):
        data = self.payload(1200, 4)
        result = self.preflight(data, failures={1: (1, 12)})
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual(result["memory"][9], self.record(data)[:12] + bytes([0xC3] * 28))
        self.assertEqual(result["memory"][11], bytes(1490))

    def test_failed_body_read_keeps_partial_raw_data(self):
        data = self.payload(1200, 4, 16, types=(6, 24), seed=12)
        result = self.preflight(data, failures={2: (1, 257)})
        self.assertEqual(result["result"], 0xFFFFFFFE)
        self.assertEqual(result["memory"][11], data[:257] + bytes(1490 - 257))
        self.assertEqual(result["calls"][-1][:2], (0x20054A8, (0, 0, 0)))

    def test_crc_failure_keeps_raw_unconverted_payload(self):
        data = self.payload(1474, 4, 16, types=(6, 24), seed=12)
        result = self.preflight(data, encoded=self.record(data, crc=0xBAD))
        self.assertEqual(result["result"], 0xFFFFFFFD)
        self.assertEqual(result["memory"][11], data + bytes(16))

    def test_modern_layout_without_aliases_preserves_bytes(self):
        data = self.payload(1490, 5, 16, types=(27, 29), seed=10)
        result = self.preflight(data)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][11], data)
        self.assertEqual(result["memory"][9], self.record(data)[:40])

    def test_1474_layout_expands_five_tail_groups(self):
        data = self.payload(1474, 5, seed=10)
        result = self.preflight(data)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][11], self.expanded_tail(data))
        self.assertEqual(result["memory"][11][1484:], bytes(6))

    def test_tail_migration_happens_before_old_format_rejection(self):
        data = self.payload(1474, 4, seed=10)
        result = self.preflight(data)
        self.assertEqual(result["result"], 0xFFFFFFFC)
        self.assertEqual(result["memory"][11], self.expanded_tail(data))

    def test_legacy_layout_relocates_every_effect_scene_and_tail_byte(self):
        data = self.payload(1200, 4, seed=20)
        expected = bytearray(1490)
        expected[:12] = data[:12]
        for slot in range(16):
            expected[12 + 18 * slot:28 + 18 * slot] = data[12 + 16 * slot:28 + 16 * slot]
        for scene in range(4):
            old, new = 268 + 228 * scene, 300 + 260 * scene
            expected[new:new + 4] = data[old:old + 4]
            for slot in range(16):
                source, destination = old + 4 + 14 * slot, new + 4 + 16 * slot
                expected[destination:destination + 14] = data[source:source + 14]
        expected[1340:1360] = data[1180:1200]
        result = self.preflight(data)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][11], expected)
        self.assertEqual(result["memory"][11][0], 4)  # Original version byte is not rewritten.
        self.assertEqual(result["memory"][9], self.record(data)[:40])

    def test_old_format_above_1200_is_rejected_before_effect_conversion(self):
        data = self.payload(1201, 4, 16, types=(6, 24), seed=20)
        result = self.preflight(data)
        self.assertEqual(result["result"], 0xFFFFFFFC)
        self.assertEqual(result["memory"][11], data + bytes(289))

    def test_effect_alias_conversion_covers_all_slots_and_four_scenes(self):
        data = bytearray(1490)
        data[0:2] = bytes((5, 255))
        for slot in range(16):
            data[13 + 18 * slot] = 6
        result = self.preflight(data)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][11][1], 255)
        expected = (40, 16, 0, 0, 0, 0, 40)
        for slot in range(16):
            self.assertEqual(result["memory"][11][13 + 18 * slot], 27)
            self.assertEqual(struct.unpack_from("<7h", result["memory"][11], 16 + 18 * slot), expected)
            for scene in range(4):
                self.assertEqual(struct.unpack_from("<7h", result["memory"][11], 306 + 260 * scene + 16 * slot), expected)

    def test_alias_conversion_uses_parameters_after_legacy_expansion(self):
        data = bytearray(1200)
        data[0:2] = bytes((4, 1))
        data[13] = 6
        struct.pack_into("<3h", data, 16, 0, 100, 50)
        for scene in range(4):
            struct.pack_into("<3h", data, 274 + 228 * scene, 10, 20, 30)
        result = self.preflight(data)
        self.assertEqual(result["memory"][11][13], 27)
        self.assertEqual(struct.unpack_from("<7h", result["memory"][11], 16), (40, 16, 70, 0, 50, 0, 40))
        for scene in range(4):
            self.assertEqual(struct.unpack_from("<7h", result["memory"][11], 306 + 260 * scene),
                             (45, 19, 14, 0, 30, 0, 40))

    def test_short_and_empty_records_can_pass_without_schema_validation(self):
        for data in (b"", b"\x05"):
            result = self.preflight(data)
            self.assertEqual(result["result"], 0)
            self.assertEqual(result["memory"][11], data + bytes(1490 - len(data)))

    def test_priority_release_observes_raw_bytes_before_conversion(self):
        data = self.payload(1200, 4, seed=12)
        result = self.preflight(data)
        self.assertEqual(result["calls"][-1][:2], (0x20054A8, (0, 0, 0)))
        self.assertEqual(result["calls"][-1][2][11], data + bytes(290))
        self.assertNotEqual(result["memory"][11], data + bytes(290))

    def test_cache_words_do_not_control_or_change_preflight(self):
        memory = self.initial()
        struct.pack_into("<I", memory[1], 708, 0xFFFFFFFF)
        struct.pack_into("<I", memory[1], 732, 0)
        result = self.preflight(b"\x05", memory=memory)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][1], memory[1])
        self.assertEqual(sum(call[0] == 0x2002810 for call in result["calls"]), 2)

    def test_oracle_rejects_invalid_memory_and_parameter_presence(self):
        with self.assertRaisesRegex(ValueError, "domain"):
            self.program.execute(self.initial()[:11], "preflight", 0)
        with self.assertRaisesRegex(ValueError, "absent or present"):
            self.program.execute(self.initial(), "convert_effect", 6, 2)


if __name__ == "__main__":
    unittest.main()
