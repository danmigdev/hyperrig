"""Independent layout, ABI and failure expectations for the asset instruction oracle."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class PresetAssetsInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from preset_assets_machine import PresetAssetsProgram
        from verify_preset_assets import baseline, header, Reads
        cls.program = PresetAssetsProgram()
        cls.initial, cls.header, cls.reads = staticmethod(baseline), staticmethod(header), Reads

    def run_original(self, operation, *args, memory=None, script=()):
        reads = self.reads(script)
        result = self.program.execute(memory or self.initial(), operation, *args, reader=reads.read)
        return result, reads.requests

    def test_new_format_reads_once_and_marks_format(self):
        result, reads = self.run_original("header", 2, 8152, script=[(0, self.header(), ())])
        self.assertEqual((result["result"], result["memory"][14]), (1, b"\x01\0\0\0"))
        self.assertEqual(reads, [(0xF3000, 40)])

    def test_old_format_retries_same_address(self):
        data = self.header(tag=0x49474B54)
        result, reads = self.run_original("header", 7, 8152, script=[(0, data, ()), (0, data, ())])
        self.assertEqual((result["result"], result["memory"][14]), (1, bytes(4)))
        self.assertEqual(reads, [(0xFD000, 40)] * 2)

    def test_rejected_second_read_preserves_partial_header(self):
        data = self.header(tag=0)
        result, _ = self.run_original("header", 0, 8152,
            script=[(0, data, ()), (1, b"ABCD", ())])
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][9], b"ABCD" + data[4:])
        self.assertEqual(result["memory"][14], bytes(4))

    def test_read_failure_still_attempts_fallback(self):
        data = self.header(tag=0x49474B54, size=16)
        result, reads = self.run_original("header", 0, 16, script=[(1, b"", ()), (0, data, ())])
        self.assertEqual(result["result"], 1)
        self.assertEqual(reads, [(0xEF000, 40)] * 2)

    def test_capacity_rejection_and_unsigned_wrap(self):
        data = self.header(size=8)
        result, reads = self.run_original("header", 0xFFFFFFFF, 7,
            script=[(0, data, ()), (0, data, ())])
        self.assertEqual(result["result"], 0)
        self.assertEqual(reads, [(0xED000, 40)] * 2)

    def test_extended_boundary_is_size_eight(self):
        for size, expected in ((0, 0), (7, 0), (8, 1), (0xFFFFFFFF, 1)):
            result, _ = self.run_original("extended", 0x2144DF1C, size)
            self.assertEqual(result["result"], expected)

    def test_identity_uses_little_endian_tail_only_for_sentinel(self):
        memory = self.initial()
        memory[10][:4] = b"\x12\x34\x56\x78"
        for marker, size, expected in ((0x2144DF1C, 8, 0x78563412),
                                       (0x2144DF1C, 7, 0x2144DF1C), (9, 8, 9)):
            result, _ = self.run_original("identity", marker, size, memory=memory)
            self.assertEqual(result["result"], expected)

    def test_resolve_no_trailer_read_for_plain_identity(self):
        memory = self.initial()
        memory[9][:] = self.header(marker=0x12345678)
        result, reads = self.run_original("resolve", 8, memory=memory)
        self.assertEqual(reads, [])
        self.assertEqual(result["memory"][14], b"\x78\x56\x34\x12")

    def test_resolve_slot_split_and_signed_negative(self):
        for slot, address in ((0, 0xDF02C), (7, 0xED02C), (8, 0xCF02C),
                              (14, 0xDB02C), (0xFFFFFFFF, 0xDD02C), (0x80000000, 0xDF02C)):
            memory = self.initial()
            memory[9][:] = self.header(size=8)
            result, reads = self.run_original("resolve", slot, memory=memory, script=[(0, b"\x11\x22\x33\x44", ())])
            self.assertEqual(reads, [(address, 4)])
            self.assertEqual(result["memory"][14], b"\x11\x22\x33\x44")

    def test_trailer_failure_preserves_output_even_after_prefix(self):
        memory = self.initial()
        memory[9][:] = self.header()
        result, _ = self.run_original("resolve", 8, memory=memory, script=[(1, b"\x11\x22", ())])
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual(result["memory"][14], memory[14])

    def test_header_is_reread_after_successful_trailer(self):
        memory = self.initial()
        memory[9][:] = self.header(size=8)
        result, _ = self.run_original("resolve", 0, memory=memory,
            script=[(0, b"\x11\x22\x33\x44", ((0x31000008, 0xDEADBEEF, 4),))])
        self.assertEqual(result["memory"][14], b"\xef\xbe\xad\xde")

    def test_mode_uses_only_top_bit(self):
        for value, expected in ((0, 1), (127, 1), (128, 0), (255, 0)):
            memory = self.initial()
            memory[11][1347] = value
            result, _ = self.run_original("mode", memory=memory)
            self.assertEqual(result["result"], expected)

    def test_modern_layout_clamps_position_and_copies_twelve_bytes(self):
        memory = self.initial()
        memory[11][0:2] = bytes((4, 4))
        for i, value in enumerate((0, 1, 2, 255)):
            memory[11][15 + 18*i] = value
        memory[11][1348:1360] = bytes(range(12))
        result, _ = self.run_original("layout", memory=memory)
        self.assertEqual(result["memory"][12], b"\0\x01\x02" + bytes(13))
        self.assertEqual(result["memory"][13], bytes(range(12)))

    def test_legacy_layout_converts_each_chain_independently(self):
        memory = self.initial()
        memory[11][0:2] = bytes((3, 5))
        for i, (chain, position) in enumerate(((0, 1), (0, 9), (1, 2), (1, 0), (2, 1))):
            memory[11][12 + 18*i], memory[11][15 + 18*i] = chain, position
        memory[11][1340:1344] = b"ABCD"
        result, _ = self.run_original("layout", memory=memory)
        self.assertEqual(result["memory"][12], b"\x02\x01" + bytes(14))
        self.assertEqual(result["memory"][13], b"AB" + bytes(4) + b"CD" + bytes(4))

    def test_versions_zero_to_two_clear_branch_metadata(self):
        for version in (0, 1, 2):
            memory = self.initial()
            memory[11][0:2] = bytes((version, 0))
            result, _ = self.run_original("layout", memory=memory)
            self.assertEqual(result["memory"][12:14], (bytes(16), bytes(12)))

    def test_layout_caps_count_at_sixteen(self):
        memory = self.initial()
        memory[11][0:2] = bytes((4, 255))
        for i in range(16):
            memory[11][15 + 18*i] = 2
        result, _ = self.run_original("layout", memory=memory)
        self.assertEqual(result["memory"][12], bytes([2] * 16))
        self.assertEqual(result["memory"][11], memory[11])

    def test_descriptor_requires_presence_and_full_kind_argument(self):
        memory = self.initial()
        memory[10][:16] = struct.pack("<BB2xIII", 1, 255, 11, 22, 33)
        for args, expected in (((11, 22, 33, 255), 1), ((11, 22, 33, 511), 0), ((11, 22, 34, 255), 0)):
            result, _ = self.run_original("matches", *args, memory=memory)
            self.assertEqual(result["result"], expected)
        memory[10][0] = 0
        result, _ = self.run_original("matches", 11, 22, 33, 255, memory=memory)
        self.assertEqual(result["result"], 0)

    def test_signed_clamp_and_state_word(self):
        for value, expected in ((0x80000000, 400), (0xFFFFFFFF, 400), (399, 400),
                                (400, 400), (1500, 1500), (3000, 3000), (3001, 3000)):
            result, _ = self.run_original("clamp", value)
            self.assertEqual(result["result"], expected)
            memory = self.initial()
            struct.pack_into("<I", memory[1], 416, value)
            result, _ = self.run_original("state416", memory=memory)
            self.assertEqual(result["result"], int(value != 0))


if __name__ == "__main__":
    unittest.main()
