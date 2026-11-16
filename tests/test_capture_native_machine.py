"""Behavioral checks against original native capture loading instructions."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from capture_native_machine import CaptureNativeProgram, ARENA, ARENA_BYTES, CONFIG
from capture_container_machine import SOURCE, CACHED, HEAP, EMBEDDED, FREE
from control_machine import STATE
from verify_capture_native import baseline, fixture, put, Script, Reads, heap_first, slot_reads


class NativeCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = CaptureNativeProgram()

    def execute(self, operation, *args, memory=None, reads=(), plan=None):
        memory = baseline() if memory is None else memory
        flash = Reads(reads)
        result = self.program.execute(memory, operation, *args, reader=flash.read,
            boundary=Script(plan, heap_first=heap_first(operation, args)))
        self.assertEqual(len(flash.requests), len(reads))
        return result

    def test_size_query_preserves_runtime_and_arena(self):
        memory = baseline()
        result = self.execute("size", SOURCE, len(fixture()), memory=memory)
        self.assertGreater(result["result"], 8)
        self.assertEqual(result["memory"], tuple(bytes(x) if i != 2 else x for i, x in enumerate(memory)))
        self.assertEqual(len(result["parser_entries"]), 1)
        self.assertEqual(result["reset_entries"], 0)

    def test_failed_parser_probe_retains_sixteen_byte_result(self):
        result = self.execute("probe", SOURCE, 43)
        self.assertEqual(result["result"], 16)
        self.assertEqual(result["memory"][24], struct.pack("<I", 1))

    def test_short_input_needs_no_source_mapping(self):
        result = self.execute("size", 0, 43)
        self.assertEqual(result["result"], 0)
        self.assertFalse(result["calls"])

    def test_load_context_uses_native_descriptor_and_resets_history(self):
        result = self.execute("load_context", ARENA, ARENA_BYTES, SOURCE, len(fixture()))
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["reset_entries"], 1)
        context, arena = result["memory"][22][76:], result["memory"][27]
        descriptors = struct.unpack_from("<I", context, 92)[0] - ARENA
        history, span = struct.unpack_from("<I", arena, descriptors + 68)[0], struct.unpack_from("<I", arena, descriptors + 76)[0]
        offset, size = history - ARENA, (span + 64) * context[2] * 4
        self.assertEqual(arena[offset:offset + size], bytes(size))
        self.assertEqual(context[88:92], bytes(4))
        self.assertEqual(context[108:112], struct.pack("<I", 0x01C12608))

    def test_outer_load_resets_twice_and_publishes_statistics(self):
        result = self.execute("load", ARENA, ARENA_BYTES, SOURCE, len(fixture()))
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["reset_entries"], 2)
        self.assertEqual(struct.unpack_from("<III", result["memory"][23]), (0, 1, 3))

    def test_capacity_failure_keeps_parser_writes_without_reset(self):
        blob = fixture()
        needed = self.execute("size", SOURCE, len(blob))["result"] - 8
        before = baseline(blob)
        result = self.execute("load_context", ARENA, needed - 1, SOURCE, len(blob), memory=before)
        self.assertEqual(result["result"], (-5) & 0xFFFFFFFF)
        self.assertEqual(result["reset_entries"], 0)
        self.assertNotEqual(result["memory"][27], bytes(before[27]))

    def test_crc_failure_records_status_without_rewriting_context(self):
        memory = baseline()
        blob = fixture(); memory[18][len(blob) - 1] ^= 1
        result = self.execute("load", ARENA, ARENA_BYTES, SOURCE, len(blob), memory=memory)
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][22], bytes(memory[22]))
        self.assertEqual(result["reset_entries"], 0)

    def test_install_transfers_source_only_after_native_load(self):
        result = self.execute("install", SOURCE, len(fixture()), 0)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][1][500], 1)
        self.assertEqual(struct.unpack_from("<I", result["memory"][0], 60)[0], HEAP)
        self.assertEqual(result["memory"][17][:len(fixture())], fixture())
        self.assertEqual(len(result["parser_entries"]), 2)

    def test_capability_failure_reloads_previous_capture(self):
        blob = fixture(channels=1)
        memory = baseline(); memory[18][:len(blob)] = blob
        result = self.execute("install", SOURCE, len(blob), 0, memory=memory)
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
        self.assertEqual(len(result["parser_entries"]), 4)
        self.assertEqual(result["reset_entries"], 4)
        self.assertEqual(result["memory"][22][78], 3)
        self.assertEqual(result["memory"][0][60:68], bytes(memory[0][60:68]))
        self.assertEqual(result["memory"][1][500], 1)

    def test_configuration_mutation_can_invalidate_queried_capacity(self):
        blob = fixture(layers=3)
        memory = baseline(blob); put(memory[1], 440, 0)
        result = self.execute("install", SOURCE, len(blob), 0, memory=memory,
            plan={(FREE, 0): (0, ((CONFIG, 0, 4),))})
        self.assertEqual(result["result"], (-5) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][28], bytes(4))
        self.assertEqual(result["memory"][1][500], 1)

    def test_empty_previous_capture_fails_cleanup_after_probe(self):
        memory = baseline(); put(memory[0], 64, 0)
        result = self.execute("cleanup", memory=memory)
        self.assertEqual(result["result"], (-2) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][1][500], 0)
        self.assertEqual(len(result["parser_entries"]), 1)

    def test_slot_reader_reaches_real_parser_and_reset(self):
        blob = fixture()
        result = self.execute("slot", 2, reads=slot_reads(blob))
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][0][9], 2)
        self.assertEqual(len(result["parser_entries"]), 2)
        self.assertEqual(result["reset_entries"], 2)

    def test_failed_identity_read_is_resolved_by_payload_reload(self):
        blob = fixture()
        reads = slot_reads(blob)
        self.assertEqual(len(reads), 5)
        reads[1] = (1, b"", ())
        result = self.execute("slot", 2, reads=reads)
        self.assertEqual(result["result"], 0)
        self.assertEqual(len(result["parser_entries"]), 2)
        self.assertEqual(result["memory"][1][1780], 1)

    def test_signature_read_failure_still_runs_full_loader(self):
        blob = fixture()
        reads = slot_reads(blob)
        self.assertEqual(len(reads), 5)
        reads[2] = (1, b"", ())
        result = self.execute("slot", 2, reads=reads)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["reset_entries"], 2)

    def test_unaligned_arena_keeps_leading_bytes(self):
        result = self.execute("load", ARENA + 1, ARENA_BYTES - 1, SOURCE, len(fixture()))
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][27][:8], bytes([0xB7] * 8))
        self.assertEqual(struct.unpack_from("<I", result["memory"][22], 76 + 92)[0], ARENA + 8)


if __name__ == "__main__":
    unittest.main()
