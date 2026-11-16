"""Hand-checked cache, program, erase, rewrite and append instruction behavior."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class CaptureJournalInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from capture_journal_machine import CaptureJournalProgram
        from verify_capture_journal import baseline, SyntheticStorage
        cls.program, cls.initial, cls.Storage = CaptureJournalProgram(), staticmethod(baseline), SyntheticStorage

    def execute(self, operation, *args, memory=None, **script):
        storage = self.Storage(**script)
        result = self.program.execute(memory or self.initial(), operation, *args, boundary=storage)
        return result, storage

    @staticmethod
    def selected(result, service):
        return [row for row in result["calls"] if row[0] == service]

    def test_cache_invalidation_preserves_other_bytes(self):
        memory = self.initial()
        result, _ = self.execute("invalidate", 0xDF000, 8192, memory=memory)
        expected = bytearray(memory[15])
        expected[16] = 0
        self.assertEqual(result["memory"][15], bytes(expected))

    def test_zero_length_inside_slot_still_invalidates(self):
        result, _ = self.execute("invalidate", 0xDF001, 0)
        self.assertEqual(result["memory"][15][16], 0)
        boundary, _ = self.execute("invalidate", 0xDF000, 0)
        self.assertEqual(boundary["memory"][15][16], 1)

    def test_split_slot_ranges_and_adjacent_boundaries(self):
        result, _ = self.execute("invalidate", 0xCEFFF, 2)
        self.assertEqual(result["memory"][15][8*20+16], 0)
        self.assertEqual(result["memory"][15][16], 1)

    def test_unsigned_wrapping_range_is_preserved(self):
        result, _ = self.execute("invalidate", 0xFFFFFFF0, 32)
        self.assertEqual(result["memory"][15], bytes(self.initial()[15]))

    def test_compare_returns_first_unsigned_byte_difference(self):
        memory = self.initial()
        memory[17][1:5] = bytes((255, 2, 3, 4))
        memory[17][513:517] = bytes((1, 2, 3, 4))
        result, _ = self.execute("compare", 1, 513, 4, memory=memory)
        self.assertEqual(result["result"], 254)

    def test_write_rejection_leaves_cache_and_services_untouched(self):
        result, _ = self.execute("write", 0xBEFFF, 1, 0)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertFalse(result["calls"])
        self.assertEqual(result["memory"][15], bytes(self.initial()[15]))

    def test_programs_stop_at_page_boundaries(self):
        from capture_journal_machine import PROGRAM
        result, _ = self.execute("write", 0xDF0FF, 258, 0)
        calls = self.selected(result, PROGRAM)
        self.assertEqual([(r[1][0], len(r[1][3])) for r in calls], [(0xDF0FF, 1), (0xDF100, 256), (0xDF200, 1)])
        self.assertTrue(all(row[2][15][16] == 0 for row in calls))

    def test_short_program_stops_but_still_yields_and_reports(self):
        from capture_journal_machine import PROGRAM, YIELD, EVENT, ACTIVITY
        memory = self.initial()
        struct.pack_into("<I", memory[1], 280, 1)
        result, storage = self.execute("write", 0xDF000, 600, 0, memory=memory, programs={0: (1, 1)})
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
        self.assertEqual(len(self.selected(result, PROGRAM)), 1)
        self.assertEqual(len(self.selected(result, YIELD)), 1)
        self.assertEqual([row[0] for row in result["calls"]][-2:], [EVENT, ACTIVITY])
        self.assertEqual(len(storage.data), 1)
        self.assertEqual(result["memory"][15][16], 0)

    def test_zero_length_write_still_has_service_sequence(self):
        from capture_journal_machine import PROGRAM, PREPARE, MODE, ACTIVITY, CLOCK, EVENT
        result, _ = self.execute("write", 0xDF000, 0, 0)
        self.assertEqual(result["result"], 0)
        self.assertEqual([row[0] for row in result["calls"]], [PREPARE, MODE, ACTIVITY, CLOCK, EVENT, ACTIVITY])
        self.assertFalse(self.selected(result, PROGRAM))

    def test_write_adapter_wraps_base_plus_offset(self):
        from capture_journal_machine import PROGRAM
        result, _ = self.execute("write_offset", 0xFFFF0000, 0xF0000, 16, 0)
        self.assertEqual(self.selected(result, PROGRAM)[0][1][0], 0xE0000)

    def test_erase_ignores_raw_result_and_visits_each_sector(self):
        from capture_journal_machine import ERASE_SECTOR, GATE
        result, _ = self.execute("erase", 0xDF000, 2, results={(ERASE_SECTOR, 0): 0xFFFFFFFF})
        self.assertEqual(result["result"], 0)
        self.assertEqual([row[1] for row in self.selected(result, ERASE_SECTOR)], [(0, 200, 0xDF000), (0, 200, 0xE0000)])
        self.assertEqual([row[1][0] for row in self.selected(result, GATE)], [1, 0])

    def test_erase_alignment_failure_has_no_callbacks(self):
        result, _ = self.execute("erase", 0xDF001, 1)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertFalse(result["calls"])

    def test_rewrite_programs_payload_before_header_and_verifies_chunks(self):
        from capture_journal_machine import PROGRAM, RAW_READ
        result, _ = self.execute("rewrite", 0xDF000, 8192, 600, memory=self.initial(600))
        self.assertEqual(result["result"], 0)
        programs = self.selected(result, PROGRAM)
        self.assertEqual(programs[0][1][0], 0xDF028)
        self.assertEqual(programs[-1][1][0], 0xDF000)
        self.assertEqual([row[1][3] for row in self.selected(result, RAW_READ)], [40, 256, 256, 88])

    def test_rewrite_invalid_reservation_still_clocks_and_notifies(self):
        from capture_journal_machine import CLOCK, ELAPSED, NOTIFY
        result, _ = self.execute("rewrite", 0xDF000, 4095, 64)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual([row[0] for row in result["calls"]], [CLOCK, ELAPSED, NOTIFY])
        self.assertEqual(result["calls"][-1][1][2], 0x345678FF)

    def test_positive_raw_read_status_is_accepted(self):
        from capture_journal_machine import RAW_READ
        result, _ = self.execute("rewrite", 0xDF000, 8192, 64, reads={(RAW_READ, 0): (1, 40, None)})
        self.assertEqual(result["result"], 0)

    def test_payload_readback_mismatch_returns_minus_three(self):
        from capture_journal_machine import RAW_READ
        result, _ = self.execute("rewrite", 0xDF000, 8192, 64, reads={(RAW_READ, 1): (0, 64, 63)})
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)

    def test_rewrite_header_readback_compares_current_caller_bytes(self):
        from capture_journal_machine import RAW_READ, HEADER_BUFFER
        for match_changed in (False, True):
            with self.subTest(match_changed=match_changed):
                memory = self.initial(600)
                changed = memory[9][20] ^ 1
                reads = {(RAW_READ, 0): (0, 40, 20)} if match_changed else {}
                result, _ = self.execute("rewrite", 0xDF000, 8192, 600, memory=memory, reads=reads,
                    mutations={(RAW_READ, 0): ((HEADER_BUFFER + 20, changed, 1),)})
                self.assertEqual(result["result"], 0 if match_changed else (-3) & 0xFFFFFFFF)
                self.assertEqual(len(self.selected(result, RAW_READ)), 4 if match_changed else 1)
                self.assertEqual(result["memory"][9][20], changed)

    def test_rewrite_payload_readback_compares_current_caller_bytes(self):
        from capture_journal_machine import RAW_READ, PAYLOAD
        for read_index, offset in ((0, 0), (1, 17), (2, 256), (3, 599)):
            with self.subTest(read_index=read_index, offset=offset):
                memory = self.initial(600)
                changed = memory[17][offset] ^ 1
                result, _ = self.execute("rewrite", 0xDF000, 8192, 600, memory=memory,
                    mutations={(RAW_READ, read_index): ((PAYLOAD + offset, changed, 1),)})
                self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
                self.assertEqual(len(self.selected(result, RAW_READ)), max(2, read_index + 1))
                self.assertEqual(result["memory"][17][offset], changed)
        memory = self.initial(600)
        changed = memory[17][17] ^ 1
        result, _ = self.execute("rewrite", 0xDF000, 8192, 600, memory=memory,
            reads={(RAW_READ, 1): (0, 256, 17)},
            mutations={(RAW_READ, 1): ((PAYLOAD + 17, changed, 1),)})
        self.assertEqual(result["result"], 0)
        self.assertEqual(len(self.selected(result, RAW_READ)), 4)
        self.assertEqual(result["memory"][17][17], changed)

    def test_rewrite_does_not_recompare_previous_header_or_payload_chunks(self):
        from capture_journal_machine import RAW_READ, HEADER_BUFFER, PAYLOAD
        for read_index, base, region, offset in ((1, HEADER_BUFFER, 9, 20), (2, PAYLOAD, 17, 0)):
            with self.subTest(read_index=read_index):
                memory = self.initial(600)
                changed = memory[region][offset] ^ 1
                result, _ = self.execute("rewrite", 0xDF000, 8192, 600, memory=memory,
                    mutations={(RAW_READ, read_index): ((base + offset, changed, 1),)})
                self.assertEqual(result["result"], 0)
                self.assertEqual(len(self.selected(result, RAW_READ)), 4)
                self.assertEqual(result["memory"][region][offset], changed)

    def test_append_crc_record_and_success_details(self):
        from capture_journal_machine import PROGRAM, NOTIFY
        from verify_capture_metadata import record
        result, _ = self.execute("append", 0xDF000, 0x87654321, 23, 99)
        self.assertEqual(result["result"], 1)
        self.assertEqual(self.selected(result, PROGRAM)[0][1][3], record(metadata=23))
        self.assertEqual(struct.unpack("<IIII", result["memory"][16]), (23, 0, 1, 4))
        self.assertEqual(self.selected(result, NOTIFY)[0][1], (18, 0xDF070, 0x34567800))

    def test_append_retries_next_record_after_failed_readback(self):
        from capture_journal_machine import PROGRAM, WRAPPED_READ
        result, _ = self.execute("append", 0xDF000, 0x87654321, 23, 0,
                                 reads={(WRAPPED_READ, 0): (0, 16, 5)})
        self.assertEqual(result["result"], 1)
        self.assertEqual([row[1][0] for row in self.selected(result, PROGRAM)], [0xDF070, 0xDF080])
        self.assertEqual(struct.unpack_from("<II", result["memory"][16], 4), (1, 2))

    def test_append_stops_after_two_attempts_at_fallback(self):
        from capture_journal_machine import PROGRAM
        result, _ = self.execute("append", 0xDF000, 0x87654321, 23, 0,
                                 programs={0: (0, 0), 1: (0, 0)})
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["allocation"], 64)
        self.assertEqual(struct.unpack("<IIII", result["memory"][16]), (17, 0xFFFFFFFF, 2, 4))
        self.assertEqual(len(self.selected(result, PROGRAM)), 2)

    def test_second_program_failure_is_reached_and_skips_readback(self):
        from capture_journal_machine import PROGRAM, WRAPPED_READ
        result, storage = self.execute("append", 0xDF000, 0x87654321, 23, 0,
            programs={0: (0, 0), 1: (0xFFFFFFFF, 4)})
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["allocation"], 64)
        self.assertEqual([row[1][0] for row in self.selected(result, PROGRAM)], [0xDF070, 0xDF080])
        self.assertEqual(storage.counts[PROGRAM], 2)
        self.assertFalse(self.selected(result, WRAPPED_READ))
        self.assertEqual(set(storage.data), set(range(0xDF080, 0xDF084)))
        self.assertEqual(struct.unpack_from("<I", result["memory"][16], 8)[0], 2)

    def test_full_journal_requests_minimum_allocation_without_program(self):
        result, _ = self.execute("append", 0xDF000, 0x87654321, 23, 0, memory=self.initial(0, 0, 0))
        self.assertEqual((result["result"], result["allocation"]), (0, 4))
        self.assertFalse(result["calls"])

    def test_append_uses_captured_cursor_capacity_and_size(self):
        from capture_journal_machine import PROGRAM, DETAILS, HEADER_BUFFER
        result, _ = self.execute("append", 0xDF000, 0x87654321, 23, 0,
            programs={0: (0, 0), 1: (0, 0)}, mutations={(PROGRAM, 0):
                ((DETAILS + 8, 255, 4), (DETAILS + 12, 0, 4), (HEADER_BUFFER + 4, 8000, 4))})
        self.assertEqual(result["allocation"], 64)
        self.assertEqual(struct.unpack_from("<II", result["memory"][16], 8), (2, 0))
        self.assertEqual(len(self.selected(result, PROGRAM)), 2)

    def test_outside_reference_domain_rejected(self):
        for operation, args in (("write", (0, 8193, 0)), ("erase", (0, 65)), ("rewrite", (0, 8192, 8153))):
            with self.assertRaises(ValueError):
                self.program.execute(self.initial(), operation, *args)


if __name__ == "__main__":
    unittest.main()
