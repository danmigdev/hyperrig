"""Independent expected native-parser layout, failure and allocation behavior."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class CaptureParserInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from capture_parser_machine import CaptureParserProgram
        from verify_capture_parser import fixture, crc_blob, initial
        cls.program = CaptureParserProgram()
        cls.fixture, cls.crc_blob, cls.initial = staticmethod(fixture), staticmethod(crc_blob), staticmethod(initial)

    def execute(self, blob=None, *, capacity=0, configuration=0xFFFFFFFF, used=0):
        from capture_parser_machine import ARENA
        if blob is None:
            blob = self.fixture(channels=1, kernel=1, head=1)
        return self.program.execute(self.initial(), [ARENA if capacity else 0, used, capacity],
            blob, bytes([0xB7]) * capacity, configuration)

    @staticmethod
    def word(data, offset=0):
        return struct.unpack_from("<I", data, offset)[0]

    def test_short_input_preserves_context_and_ledger(self):
        result = self.execute(b"x" * 43, used=17)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual(result["memory"][0], self.initial())
        self.assertEqual(struct.unpack("<III", result["memory"][1]), (0, 17, 0))

    def test_bad_crc_precedes_header_or_arena_writes(self):
        blob = bytearray(self.fixture(channels=1, kernel=1, head=1))
        blob[6] = 8
        result = self.execute(bytes(blob), capacity=640)
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][0], self.initial())
        self.assertEqual(result["memory"][3], bytes([0xB7] * 640))

    def test_magic_error_preserves_context(self):
        body = bytearray(self.fixture()[:-4])
        body[0] = ord("X")
        result = self.execute(self.crc_blob(body))
        self.assertEqual(result["result"], (-2) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][0], self.initial())

    def test_unsupported_precision_retains_header_writes(self):
        result = self.execute(self.fixture(abits=8))
        self.assertEqual(result["result"], (-4) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][0][:4], bytes([16, 8, 3, 3]))
        self.assertEqual(result["memory"][0][30], 0)
        self.assertEqual(result["memory"][0][31:], self.initial()[31:])

    def test_query_has_native_size_and_null_tokens(self):
        result = self.execute()
        self.assertEqual(result["result"], 0)
        self.assertEqual(self.word(result["memory"][1], 4), 640)
        for offset in (60, 68, 80, 92):
            self.assertEqual(self.word(result["memory"][0], offset), 0)

    def test_sixteen_bit_activation_has_signed_sixteen_bit_limits(self):
        result = self.execute(self.fixture(channels=1, kernel=1, head=1, abits=16))
        self.assertEqual(result["result"], 0)
        self.assertEqual(struct.unpack_from("<q", result["memory"][0], 40)[0], -32768)
        self.assertEqual(struct.unpack_from("<q", result["memory"][0], 48)[0], 32767)

    def test_rechannel_truncation_precedes_layer_rejection(self):
        result = self.execute(self.crc_blob(self.fixture()[:41]), capacity=4096)
        self.assertEqual(result["result"], (-1) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][3][0], 0)
        self.assertEqual(self.word(result["memory"][1], 4), 86)

    def test_insufficient_capacity_still_returns_success_and_required_size(self):
        from capture_parser_machine import ARENA
        result = self.execute(capacity=80)
        self.assertEqual(result["result"], 0)
        self.assertEqual(self.word(result["memory"][1], 4), 640)
        self.assertEqual(self.word(result["memory"][0], 92), ARENA)
        for offset in (60, 68, 80):
            self.assertEqual(self.word(result["memory"][0], offset), 0)
        self.assertEqual(self.word(result["memory"][3], 44), 0)

    def test_native_allocation_order_and_reserved_padding(self):
        from capture_parser_machine import ARENA
        result = self.execute(capacity=640)
        context, arena = result["memory"][0], result["memory"][3]
        self.assertEqual(self.word(context, 92), ARENA)
        self.assertEqual(self.word(context, 60), ARENA + 80)
        self.assertEqual(self.word(arena, 32), ARENA + 88)
        self.assertEqual(self.word(arena, 36), ARENA + 96)
        self.assertEqual(self.word(arena, 44), ARENA + 104)
        self.assertEqual(self.word(arena, 68), ARENA + 112)
        self.assertEqual(self.word(context, 68), ARENA + 624)
        self.assertEqual(self.word(context, 80), ARENA + 632)
        self.assertEqual(arena[108:112], bytes([0xB7] * 4))
        self.assertEqual(arena[1], 0xB7)
        self.assertEqual(arena[65:68], bytes([0xB7] * 3))

    def test_history_is_allocated_but_not_reset(self):
        result = self.execute(capacity=640)
        arena = result["memory"][3]
        self.assertEqual(arena[112:624], bytes([0xB7] * 512))
        self.assertEqual(arena[632:640], bytes([0xB7] * 8))

    def test_matching_configuration_reserves_sixty_four_extra_frames(self):
        normal, extra = self.execute(), self.execute(configuration=0)
        self.assertEqual(self.word(extra["memory"][1], 4) - self.word(normal["memory"][1], 4), 256)
        result = self.execute(capacity=896, configuration=0)
        self.assertEqual(self.word(result["memory"][3], 76), 128)
        self.assertEqual(self.word(result["memory"][0], 32), 1)

    def test_short_layer_header_keeps_partial_descriptor(self):
        body = self.fixture(channels=1, kernel=1, head=1)[:40]
        result = self.execute(self.crc_blob(body), capacity=640)
        self.assertEqual(result["result"], (-1) & 0xFFFFFFFF)
        self.assertEqual(self.word(result["memory"][1], 4), 82)
        self.assertEqual(result["memory"][3][0], 1)
        self.assertEqual(result["memory"][3][2:4], bytes(2))
        self.assertEqual(result["memory"][3][12:16], bytes(4))
        self.assertEqual(result["memory"][3][4:12], bytes([0xB7] * 8))

    def test_read64_consumes_valid_low_word_before_truncated_high_word(self):
        body = bytearray(self.fixture(channels=1, kernel=1, head=1, final=0)[:-4])
        body[76:80] = struct.pack("<I", 0x87654321)
        result = self.execute(self.crc_blob(body[:80]), capacity=640)
        self.assertEqual(result["result"], (-1) & 0xFFFFFFFF)
        self.assertEqual(self.word(result["memory"][0], 72), 0x87654321)
        self.assertEqual(self.word(result["memory"][0], 76), 0)

    def test_kernel_and_layer_counts_exceed_portable_loader_limits(self):
        for blob in (self.fixture(channels=1, kernel=16, head=1), self.fixture(channels=1, layers=65, kernel=1, head=1)):
            self.assertEqual(self.execute(blob)["result"], 0)

    def test_four_channels_leave_embedded_bias_slots_untouched(self):
        result = self.execute(self.fixture(channels=4, kernel=1, head=1), capacity=8192)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][3][52:64], bytes([0xB7] * 12))

    def test_fraction_fields_retain_byte_wrap_before_rechannel_range_check(self):
        blob = self.fixture(channels=1, kernel=1, head=1, rechannel=-1)
        result = self.execute(blob)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][0][56], 255)
        self.assertEqual(result["memory"][0][164], 0)

    def test_optimized_flag_and_zero_shift_fallback(self):
        fast = self.execute(self.fixture(channels=3, kernel=6, head=3), capacity=4096)
        slow = self.execute(self.fixture(channels=3, kernel=6, head=3, conv=0), capacity=4096)
        self.assertEqual(fast["memory"][0][164], 1)
        self.assertEqual(slow["memory"][0][164], 0)

    def test_extra_trailing_bytes_fail_after_final_context_initialization(self):
        blob = self.fixture(channels=1, kernel=1, head=1)
        result = self.execute(self.crc_blob(blob[:-4] + b"x"), capacity=640)
        self.assertEqual(result["result"], (-1) & 0xFFFFFFFF)
        self.assertEqual(self.word(result["memory"][0], 32), 1)
        self.assertEqual(result["memory"][0][212:228], bytes(16))

    def test_context_padding_and_reset_owned_fields_are_preserved(self):
        result = self.execute()
        for start, stop in ((31, 32), (58, 60), (88, 92), (106, 120), (136, 140), (165, 168), (206, 208)):
            self.assertEqual(result["memory"][0][start:stop], self.initial()[start:stop])

    def test_wrapping_query_allocation_still_finishes(self):
        result = self.execute(used=0xFFFFFFFF)
        self.assertEqual(result["result"], 0)
        self.assertEqual(self.word(result["memory"][1], 4), 640)


if __name__ == "__main__":
    unittest.main()
