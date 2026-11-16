"""Hand-checked journal selection, cursor, cache and read-failure expectations."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class CaptureMetadataInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from capture_metadata_machine import CaptureMetadataProgram
        from verify_capture_metadata import baseline, record, journal, Flash
        cls.program = CaptureMetadataProgram()
        cls.initial, cls.record, cls.journal = staticmethod(baseline), staticmethod(record), staticmethod(journal)
        cls.Flash = Flash

    def execute(self, operation, *args, memory=None, regions=(), failures=None, plan=None):
        flash = self.Flash(regions, failures, plan)
        result = self.program.execute(memory or self.initial(), operation, *args, reader=flash.read)
        return result, flash.requests

    def scan(self, size=8000, entries=(), **kwargs):
        return self.execute("scan", 0xDF000, 0x87654321, memory=self.initial(size),
                            regions=self.journal(size, entries), **kwargs)

    @staticmethod
    def details(result):
        return struct.unpack("<IIII", result["memory"][16])

    def test_capacity_boundaries_and_sector_wrap(self):
        for size, expected in ((0, 253), (64, 249), (4040, 1), (4041, 0), (4056, 0),
                               (4057, 255), (8000, 9), (8152, 0), (8153, 0), (0xFFFFFFFF, 0)):
            result, _ = self.execute("capacity", size)
            self.assertEqual(result["result"], expected)

    def test_standard_crc_check_value(self):
        memory = self.initial()
        memory[10][:9] = b"123456789"
        result, _ = self.execute("crc", 9, memory=memory)
        self.assertEqual(result["result"], 0xCBF43926)

    def test_erased_zero_and_last_byte(self):
        memory = self.initial()
        memory[10][:16] = bytes([255] * 16)
        for size in (0, 16):
            result, _ = self.execute("erased", size, memory=memory)
            self.assertEqual(result["result"], 1)
        memory[10][15] = 0
        result, _ = self.execute("erased", 16, memory=memory)
        self.assertEqual(result["result"], 0)

    def test_all_erased_keeps_zero_cursor_from_parallel_store(self):
        result, reads = self.scan()
        self.assertEqual(self.details(result), (17, 0xFFFFFFFF, 0, 9))
        self.assertEqual(reads, [(0xDF000 + 8048, 144)])

    def test_zero_capacity_still_initializes_details(self):
        result, reads = self.scan(8152)
        self.assertEqual(self.details(result), (17, 0xFFFFFFFF, 0, 0))
        self.assertFalse(reads)

    def test_invalid_tag_advances_cursor_without_selecting(self):
        result, _ = self.scan(entries=((5, bytes(16)),))
        self.assertEqual(self.details(result), (17, 0xFFFFFFFF, 6, 9))

    def test_last_valid_identity_or_header_identity_wins(self):
        result, _ = self.scan(entries=((0, self.record(metadata=21)),
            (4, self.record(0x12345678, 31)), (8, self.record(7, 91))))
        self.assertEqual(self.details(result), (31, 4, 9, 9))

    def test_bad_crc_advances_cursor_but_preserves_prior_record(self):
        result, _ = self.scan(entries=((0, self.record(metadata=21)), (8, self.record(metadata=99, corrupt=True))))
        self.assertEqual(self.details(result), (21, 0, 9, 9))

    def test_scan_continues_after_erased_gap(self):
        result, _ = self.scan(entries=((8, self.record(metadata=72)),))
        self.assertEqual(self.details(result), (72, 8, 9, 9))

    def test_selection_does_not_validate_packed_gain(self):
        result, _ = self.scan(entries=((0, self.record(metadata=0xDEADBEEF)),))
        self.assertEqual(self.details(result)[:2], (0xDEADBEEF, 0))

    def test_indices_and_sizes_cross_chunk_boundary(self):
        result, reads = self.scan(3769, ((0, self.record(metadata=19)), (16, self.record(metadata=23))))
        self.assertEqual(self.details(result), (23, 16, 17, 17))
        self.assertEqual(reads, [(0xDF000 + 3824, 256), (0xDF000 + 4080, 16)])

    def test_second_read_failure_discards_selected_record(self):
        result, reads = self.scan(3769, ((0, self.record(metadata=19)),), failures={1: (7, 16)})
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual(self.details(result), (17, 0xFFFFFFFF, 17, 17))
        self.assertEqual(len(reads), 2)

    def test_failed_partial_chunk_is_not_scanned(self):
        result, _ = self.scan(entries=((0, self.record(metadata=99)),), failures={0: (1, 16)})
        self.assertEqual(self.details(result), (17, 0xFFFFFFFF, 9, 9))

    def test_failure_rereads_header_fallback(self):
        from capture_metadata_machine import HEADER_BUFFER
        result, _ = self.scan(failures={0: (1, 0)}, plan={0: ((HEADER_BUFFER + 12, 73, 4),)})
        self.assertEqual(self.details(result), (73, 0xFFFFFFFF, 9, 9))

    def test_cache_hit_skips_read_and_preserves_details(self):
        memory = self.initial()
        memory[15][:17] = struct.pack("<IIIIB", 0x12345678, 8000, 0x87654321, 91, 255)
        result, reads = self.execute("lookup", 0, 0x87654321, 0, memory=memory)
        self.assertEqual(result["result"], 91)
        self.assertEqual(result["memory"][15:], tuple(bytes(x) for x in memory[15:]))
        self.assertFalse(reads)

    def test_details_forces_scan_even_for_matching_cache(self):
        memory = self.initial()
        memory[15][:17] = struct.pack("<IIIIB", 0x12345678, 8000, 0x87654321, 91, 1)
        result, reads = self.execute("lookup", 0, 0x87654321, 1, memory=memory)
        self.assertEqual(result["result"], 17)
        self.assertEqual(self.details(result), (17, 0xFFFFFFFF, 0, 9))
        self.assertEqual(len(reads), 1)

    def test_failed_lookup_populates_cache_and_future_hit_reuses_fallback(self):
        memory = self.initial()
        result, _ = self.execute("lookup", 0, 0x87654321, 0, memory=memory, failures={0: (1, 0)})
        self.assertEqual(result["result"], 17)
        self.assertEqual(result["memory"][15][:17], struct.pack("<IIIIB", 0x12345678, 8000, 0x87654321, 17, 1))
        self.assertEqual(result["memory"][15][17:20], memory[15][17:20])
        second, reads = self.execute("lookup", 0, 0x87654321, 0, memory=result["memory"])
        self.assertEqual(second["result"], 17)
        self.assertFalse(reads)

    def test_out_of_cache_slots_and_wrapping_addresses(self):
        from verify_capture_metadata import slot_address
        for slot in (7, 8, 14, 15, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            memory = self.initial()
            result, reads = self.execute("lookup", slot, 0x87654321, 0, memory=memory)
            self.assertEqual(reads[0][0], (slot_address(slot) + 8048) & 0xFFFFFFFF)
            if slot > 14:
                self.assertEqual(result["memory"][15], bytes(memory[15]))

    def test_cache_uses_header_values_after_read_callback(self):
        from capture_metadata_machine import HEADER_BUFFER
        result, _ = self.execute("lookup", 0, 0x87654321, 0,
            plan={0: ((HEADER_BUFFER + 4, 4041, 4), (HEADER_BUFFER + 8, 7, 4))})
        self.assertEqual(struct.unpack_from("<IIII", result["memory"][15]), (7, 4041, 0x87654321, 17))

    def test_capacity_mutation_changes_next_batch_only(self):
        from capture_metadata_machine import DETAILS
        result, reads = self.scan(entries=((8, self.record(metadata=72)),), plan={0: ((DETAILS + 12, 0, 4),)})
        self.assertEqual(self.details(result), (72, 8, 9, 0))
        self.assertEqual(len(reads), 1)

    def test_outside_reference_domain_rejected(self):
        for operation, args in (("other", (0,)), ("crc", (257,)), ("capacity", (-1,)), ("lookup", (0, 0, 2))):
            with self.assertRaisesRegex(ValueError, "call domain"):
                self.program.execute(self.initial(), operation, *args)


if __name__ == "__main__":
    unittest.main()
