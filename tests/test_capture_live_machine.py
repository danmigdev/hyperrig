"""Behavioral checks for original loaded-context processing and small head rings."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from capture_live_machine import CaptureLiveProgram, EXTRA, INPUT, OUTPUT
from capture_dispatch_machine import STATS, FORCE
from verify_capture_live import (baseline, fixture, ARENA, ARENA_BYTES, SOURCE,
    HEAD, HEAD_RING, head_fixture, mutable, put, Script, Reads, heap_first, slot_reads)


class LiveCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = CaptureLiveProgram()

    def execute(self, memory, operation, *arguments, reads=()):
        flash = Reads(reads)
        result = self.program.execute(memory, operation, *arguments, reader=flash.read,
            boundary=Script(heap_first=heap_first(operation, arguments)))
        self.assertEqual(len(flash.requests), len(reads))
        return result

    def load(self, head=3, layers=1):
        blob = fixture(head=head, layers=layers)
        result = self.execute(baseline(blob), "load", ARENA, ARENA_BYTES, SOURCE, len(blob))
        self.assertEqual(result["result"], 0)
        return result["memory"]

    def test_scratch_has_one_storage_location_per_original_address(self):
        addresses = [set(range(base, base + n)) for base, n in EXTRA]
        for i, left in enumerate(addresses):
            for right in addresses[i + 1:]:
                self.assertFalse(left & right)
            self.assertFalse(left & set(range(STATS, STATS + 72)))
            self.assertFalse(left & set(range(FORCE, FORCE + 4)))

    def test_parser_head_ring_is_smaller_than_block(self):
        memory = self.load()
        self.assertEqual(struct.unpack_from("<I", memory[22], 76 + 84)[0], 3)
        result = self.execute(memory, "process", INPUT, OUTPUT, 64)
        self.assertEqual(len(result["calls"]), 3)
        self.assertEqual(struct.unpack_from("<I", result["memory"][22], 76 + 88)[0], 64)
        self.assertNotEqual(result["memory"][33][:256], memory[33][:256])

    def test_loaded_context_and_arena_keep_original_addresses(self):
        memory = self.load(layers=2)
        descriptor = struct.unpack_from("<I", memory[22], 76 + 92)[0]
        result = self.execute(memory, "process", INPUT, OUTPUT, 64)
        self.assertEqual(struct.unpack_from("<I", result["memory"][22], 76 + 92)[0], descriptor)
        self.assertEqual(result["memory"][27][:160], memory[27][:160])
        self.assertEqual(result["memory"][18], memory[18])

    def test_loaded_partial_block_preserves_everything(self):
        memory = self.load()
        for count in (0, 1, 63):
            result = self.execute(memory, "process", INPUT, OUTPUT, count)
            self.assertEqual(result["memory"], memory)
            self.assertFalse(result["calls"])

    def test_remainder_stays_untouched(self):
        memory = self.load()
        result = self.execute(memory, "process", INPUT, OUTPUT, 129)
        self.assertEqual(result["memory"][33][512:], memory[33][512:])
        self.assertEqual(struct.unpack_from("<I", result["memory"][22], 76 + 88)[0], 128)

    def test_two_calls_equal_two_blocks(self):
        memory = self.load(layers=2)
        first = self.execute(memory, "process", INPUT, OUTPUT, 64)["memory"]
        split = self.execute(first, "process", INPUT + 256, OUTPUT + 256, 64)["memory"]
        joined = self.execute(memory, "process", INPUT, OUTPUT, 128)["memory"]
        self.assertEqual(split, joined)

    def test_position_wrap(self):
        memory = mutable(self.load()); put(memory[22], 76 + 88, 0xFFFFFFC0)
        result = self.execute(memory, "process", INPUT, OUTPUT, 128)
        self.assertEqual(struct.unpack_from("<I", result["memory"][22], 76 + 88)[0], 64)

    def test_bypass_overlap_copies_forward(self):
        memory = baseline(); memory[22][76:] = bytes(228)
        result = self.execute(memory, "process", INPUT, INPUT + 4, 64)
        self.assertEqual(result["memory"][32][:260], bytes(memory[32][:4]) * 65)

    def test_zero_bypass_still_increments_counter(self):
        memory = baseline(); memory[22][76:] = bytes(228)
        before = struct.unpack_from("<I", memory[31], 4)[0]
        result = self.execute(memory, "process", INPUT, OUTPUT, 0)
        self.assertEqual(struct.unpack_from("<I", result["memory"][31], 4)[0], (before + 1) & 0xFFFFFFFF)

    def test_small_head_writes_exact_mirrored_extent(self):
        for ring in (1, 2, 4, 8, 16, 32):
            memory = head_fixture(ring, min(ring, 3), ring - 1)
            result = self.execute(memory, "head_kernel", HEAD)
            offset = HEAD_RING - ARENA
            self.assertEqual(result["memory"][27][offset:offset + ring * 12],
                             result["memory"][27][offset + ring * 12:offset + ring * 24])
            self.assertEqual(result["memory"][27][offset + ring * 24:], bytes(memory[27][offset + ring * 24:]))

    def test_slot_reuse_preserves_active_history(self):
        blob = fixture()
        loaded = self.execute(baseline(blob), "slot", 2, reads=slot_reads(blob))["memory"]
        active = self.execute(loaded, "process", INPUT, OUTPUT, 64)["memory"]
        reused = self.execute(active, "slot", 2, reads=slot_reads(blob, reuse=True))["memory"]
        self.assertEqual(reused[22], active[22])
        self.assertEqual(reused[27], active[27])

    def test_crc_failure_keeps_previous_processing_context(self):
        memory = mutable(self.load()); blob = fixture(); memory[18][len(blob) - 1] ^= 1
        failed = self.execute(memory, "load", ARENA, ARENA_BYTES, SOURCE, len(blob))
        self.assertEqual(failed["result"], 0xFFFFFFFD)
        self.assertEqual(failed["memory"][22], bytes(memory[22]))
        self.assertEqual(failed["memory"][27], bytes(memory[27]))
        self.execute(failed["memory"], "process", INPUT, OUTPUT, 64)

    def test_warmup_uses_loaded_histories_and_returns_pre_head_triplet(self):
        memory = self.load(head=3, layers=2)
        result = self.execute(memory, "warmup", OUTPUT)
        self.assertEqual(result["result"], 1)
        self.assertEqual(result["memory"][33][:12], result["memory"][29][0x4e0:0x4ec])
        self.assertEqual(len(result["calls"]), 2)
        self.assertEqual(result["memory"][22][76 + 88:76 + 92], bytes(4))
        self.execute(result["memory"], "process", INPUT, OUTPUT, 64)

    def test_warmup_fallback_executes_actual_reset(self):
        memory = mutable(self.load()); memory[22][76 + 164] = 0
        result = self.execute(memory, "warmup", OUTPUT)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["reset_entries"], 1)
        self.assertGreater(result["reset_words"], 0)
        self.assertEqual(result["memory"][33], bytes(memory[33]))


if __name__ == "__main__":
    unittest.main()
