"""Expected control/data behavior of original capture DSP dispatch instructions."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class CaptureDispatchInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from capture_dispatch_machine import CaptureDispatchProgram
        from verify_capture_dispatch import baseline, Script, ParserScript, Reads, heap_first
        cls.program = CaptureDispatchProgram()
        cls.initial, cls.heap_first = staticmethod(baseline), staticmethod(heap_first)
        cls.Script, cls.ParserScript, cls.Reads = Script, ParserScript, Reads

    def execute(self, operation, *arguments, memory=None, plan=None, parses=None, reads=()):
        flash = self.Reads(reads)
        result = self.program.execute(memory or self.initial(), operation, *arguments, reader=flash.read,
            boundary=self.Script(plan, heap_first=self.heap_first(operation, arguments)), parser=self.ParserScript(parses))
        self.assertEqual(len(flash.requests), len(reads))
        return result

    @staticmethod
    def word(data, offset=0):
        return struct.unpack_from("<I", data, offset)[0]

    def test_busy_preparation_has_no_side_effects(self):
        memory = self.initial()
        struct.pack_into("<I", memory[1], 416, 1)
        result = self.execute("prepare", 1024, memory=memory)
        self.assertEqual(result["result"], (-110) & 0xFFFFFFFF)
        self.assertEqual(result["calls"], [])
        self.assertEqual(result["memory"][1], memory[1])

    def test_existing_capacity_is_reused_without_clearing_ready(self):
        result = self.execute("prepare", 512)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["calls"], [])
        self.assertEqual(result["memory"][1][500], 7)

    def test_failed_reallocation_clears_pointer_and_records_error(self):
        from capture_container_machine import ALLOCATE, FREE
        from capture_dispatch_machine import ARENA
        result = self.execute("prepare", 513, plan={ALLOCATE: (0, ())})
        self.assertEqual([(x[0], x[1][0]) for x in result["calls"]], [(FREE, ARENA), (ALLOCATE, 769)])
        self.assertEqual(result["memory"][1][436:444], bytes(8))
        self.assertEqual(self.word(result["memory"][21], 12), (-100) & 0xFFFFFFFF)

    def test_preparation_retains_unsigned_request_wrap(self):
        from capture_container_machine import ALLOCATE
        result = self.execute("prepare", 0xFFFFFF00)
        self.assertEqual(next(row[1][0] for row in result["calls"] if row[0] == ALLOCATE), 0)
        self.assertEqual(self.word(result["memory"][1], 440), 0)

    def test_failed_size_query_is_zero_but_probe_still_adds_sixteen(self):
        for op, expected in (("size", 0), ("probe", 16)):
            result = self.execute(op, 0x1234, 99, parses={0: (-7, (None, 42, None), ())})
            self.assertEqual(result["result"], expected)
            self.assertEqual(result["calls"][0][1], ("query", (0, 0, 0), 0x1234, 99))

    def test_probe_wrap_can_return_zero(self):
        result = self.execute("probe", 0, 0, parses={0: (0, (None, 0xFFFFFFE8, None), ())})
        self.assertEqual(result["result"], 0)
        self.assertEqual(self.word(result["memory"][24]), 1)

    def test_arena_alignment_uses_pre_packet_register_values(self):
        from capture_dispatch_machine import ARENA, CONTEXT
        result = self.execute("load_context", ARENA + 3, 100, 0x4321, 567)
        self.assertEqual(result["calls"][0][1], (CONTEXT, (ARENA + 8, 0, 95), 0x4321, 567))

    def test_null_or_insufficient_arena_fails_before_parser(self):
        from capture_dispatch_machine import ARENA
        for arena, size in ((0, 999), (ARENA + 1, 6)):
            result = self.execute("load_context", arena, size, 123, 456)
            self.assertEqual(result["result"], (-5) & 0xFFFFFFFF)
            self.assertEqual(result["calls"], [])

    def test_parser_overuse_preserves_partial_context_writes(self):
        from capture_dispatch_machine import ARENA, CONTEXT, RESET
        result = self.execute("load_context", ARENA, 64, 123, 456,
            parses={0: (0, (None, 65, None), ((CONTEXT + 32, 0x12345678, 4),))})
        self.assertEqual(result["result"], (-5) & 0xFFFFFFFF)
        self.assertEqual(self.word(result["memory"][22], 108), 0x12345678)
        self.assertNotIn(RESET, [row[0] for row in result["calls"]])

    def test_successful_context_keeps_layer_count_and_zeroes_correct_word(self):
        from capture_dispatch_machine import ARENA, DEFAULT_DOT
        result = self.execute("load_context", ARENA, 128, 1, 2)
        dsp = result["memory"][22]
        self.assertEqual(dsp[84:86], b"\x03\0")
        self.assertEqual(self.word(dsp, 184), DEFAULT_DOT)
        self.assertEqual(dsp[188:196], bytes(8))
        self.assertEqual(dsp[212], 0)

    def test_load_calls_reset_twice_with_statistics_between_them(self):
        from capture_dispatch_machine import ARENA, CONTEXT, RESET
        result = self.execute("load", ARENA, 128, 1, 2,
            plan={(RESET, 0): (0, ((CONTEXT + 8, 17, 2), (CONTEXT + 10, 128, 1), (CONTEXT + 13, 255, 1)))})
        resets = [row for row in result["calls"] if row[0] == RESET]
        self.assertEqual(len(resets), 2)
        self.assertEqual(resets[0][2][23], self.initial()[23])
        self.assertEqual(self.word(resets[1][2][23], 4), 17)
        self.assertEqual(self.word(resets[1][2][23], 20), 0xFFFFFF80)
        self.assertEqual(self.word(resets[1][2][23], 24), 0xFFFFFFFF)

    def test_load_failure_only_sets_status_in_statistics(self):
        from capture_dispatch_machine import ARENA
        result = self.execute("load", ARENA, 128, 1, 2, parses={0: (-9, (None, None, None), ())})
        self.assertEqual(self.word(result["memory"][23]), (-9) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][23][4:], self.initial()[23][4:])

    def test_capability_output_is_seventeen_bytes_and_written_on_failure(self):
        memory = self.initial()
        memory[22][90:107] = bytes(range(17))
        memory[22][78] = 2
        result = self.execute("capabilities", memory=memory)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][25], bytes(range(17)) + struct.pack("<II", 3, 2))

    def test_zero_layer_capability_does_not_dereference_pointer(self):
        memory = self.initial()
        struct.pack_into("<H", memory[22], 84, 0)
        struct.pack_into("<I", memory[22], 168, 0xFFFFFFFF)
        self.assertEqual(self.execute("capabilities", memory=memory)["result"], 1)

    def test_capability_rejects_type_sixteen_in_later_record(self):
        memory = self.initial()
        memory[26][160] = 16
        self.assertEqual(self.execute("capabilities", memory=memory)["result"], 0)

    def test_cleanup_probes_before_empty_source_check(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 64, 0)
        result = self.execute("cleanup", memory=memory)
        self.assertEqual(result["result"], (-2) & 0xFFFFFFFF)
        self.assertEqual(len(result["calls"]), 1)
        self.assertEqual(result["calls"][0][1][3], 0)
        self.assertEqual(result["memory"][1][500], 0)

    def test_cleanup_rereads_source_after_probe(self):
        from control_machine import GLOBAL
        result = self.execute("cleanup", parses={0: (0, (None, 64, None), ((GLOBAL + 60, 0x1234, 4), (GLOBAL + 64, 321, 4)))})
        self.assertEqual(result["calls"][1][1][2:], (0x1234, 321))
        self.assertEqual(result["memory"][1][500], 1)

    def test_full_slot_path_executes_wrappers_and_noop_helpers(self):
        from capture_dispatch_machine import REGIONS
        from verify_capture_container import slot_reads
        result = self.execute("slot", 2, reads=slot_reads())
        self.assertEqual(result["result"], 0)
        for name in ("prepare", "probe", "size", "load", "load_context", "capabilities", "select_dot", "noop_a", "noop_b", "noop_c", "noop_d"):
            self.assertIn(REGIONS[name][0], result["visited"])
        self.assertEqual(result["memory"][0][9], 2)

    def test_invalid_operation_and_arguments_are_rejected(self):
        for op, args in (("load", (0,)), ("probe", (-1, 0)), ("unknown", ()), ("install", (0, 8, 123))):
            with self.assertRaisesRegex(ValueError, "call domain"):
                self.program.execute(self.initial(), op, *args)


if __name__ == "__main__":
    unittest.main()
