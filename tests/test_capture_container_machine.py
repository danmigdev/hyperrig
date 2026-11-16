"""Independent expected behavior for capture installation, ownership and record loading."""
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class CaptureContainerInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from capture_container_machine import CaptureContainerProgram
        from verify_capture_container import baseline, record, request, record_reads, slot_reads, Reads, Script
        cls.program = CaptureContainerProgram()
        for name, value in (("initial", baseline), ("record", record), ("request", request),
                            ("record_reads", record_reads), ("slot_reads", slot_reads)):
            setattr(cls, name, staticmethod(value))
        cls.Reads, cls.Script = Reads, Script

    def execute(self, operation, *arguments, memory=None, reads=(), plan=None):
        flash = self.Reads(reads)
        result = self.program.execute(memory or self.initial(), operation, *arguments,
                                      reader=flash.read, boundary=self.Script(plan))
        self.assertEqual(len(flash.requests), len(reads))
        return result, flash.requests

    @staticmethod
    def word(data, offset=0):
        return struct.unpack_from("<I", data, offset)[0]

    def test_size_gate_has_no_services_or_writes(self):
        from capture_container_machine import SOURCE
        memory = self.initial()
        for size in (0, 8193, 0xFFFFFFFF):
            result, _ = self.execute("install", SOURCE, size, 0, memory=memory)
            self.assertEqual(result["result"], 0xFFFFFFFF)
            self.assertEqual(result["calls"], [])
            self.assertEqual(result["memory"], tuple(bytes(x) if i != 2 else x for i, x in enumerate(memory)))

    def test_allocation_is_aligned_and_failure_is_early(self):
        from capture_container_machine import ALLOCATE, SOURCE
        result, _ = self.execute("install", SOURCE, 5, 0, plan={ALLOCATE: (0, ())})
        self.assertEqual(result["result"], (-100) & 0xFFFFFFFF)
        self.assertEqual([(x[0], x[1]) for x in result["calls"]], [(ALLOCATE, (8, 0, 0, 0))])

    def test_source_copy_commits_before_free(self):
        from capture_container_machine import SOURCE, HEAP, CACHED, FREE
        result, _ = self.execute("install", SOURCE, 7, 0)
        free = next(row for row in result["calls"] if row[0] == FREE)
        self.assertEqual(free[1], (CACHED, 0, 0, 0))
        self.assertEqual(self.word(free[2][1], 676), HEAP)
        self.assertEqual(free[2][17][:7], free[2][18][:7])
        self.assertEqual(self.word(result["memory"][0], 60), HEAP)
        self.assertEqual(result["memory"][17][7:], bytes([0xA6] * (8192 - 7)))

    def test_free_mutation_is_reread_for_published_pointer(self):
        from capture_container_machine import SOURCE, CACHED, FREE
        from control_machine import STATE
        result, _ = self.execute("install", SOURCE, 8, 0, plan={FREE: (0, ((STATE + 676, CACHED, 4),))})
        self.assertEqual(self.word(result["memory"][0], 60), CACHED)

    def test_embedded_success_releases_cached_pointer(self):
        from capture_container_machine import EMBEDDED, ALLOCATE, FREE, CACHED
        result, _ = self.execute("install", EMBEDDED, 8, 0)
        self.assertNotIn(ALLOCATE, [row[0] for row in result["calls"]])
        self.assertEqual([row[1][0] for row in result["calls"] if row[0] == FREE], [CACHED])
        self.assertEqual(self.word(result["memory"][1], 676), 0)
        self.assertEqual(self.word(result["memory"][0], 60), EMBEDDED)

    def test_cached_source_is_not_allocated_or_freed(self):
        from capture_container_machine import CACHED, ALLOCATE, FREE
        result, _ = self.execute("install", CACHED, 8, 0)
        self.assertFalse({ALLOCATE, FREE} & {row[0] for row in result["calls"]})

    def test_early_failure_does_not_run_dsp_cleanup(self):
        from capture_container_machine import SOURCE, FREE, PROBE, CLEANUP, HEAP, PREPARE
        result, _ = self.execute("install", SOURCE, 8, 0, plan={PROBE: (0, ())})
        self.assertEqual(result["result"], (-2) & 0xFFFFFFFF)
        self.assertEqual([row[1][0] for row in result["calls"] if row[0] == FREE], [HEAP])
        self.assertFalse({CLEANUP, PREPARE} & {row[0] for row in result["calls"]})
        self.assertEqual(result["memory"][1][500], 7)

    def test_late_failure_reports_cleanup_result_separately(self):
        from capture_container_machine import SOURCE, PROCESS_LOAD, CLEANUP, NOTIFY
        result, _ = self.execute("install", SOURCE, 8, 0, plan={PROCESS_LOAD: (-7, ()), CLEANUP: (123, ())})
        self.assertEqual(result["result"], (-7) & 0xFFFFFFFF)
        self.assertEqual([row[1] for row in result["calls"] if row[0] == NOTIFY],
                         [(29, 1, 8, 0), (29, 3, 123, 0), (29, 2, 249, 0)])
        self.assertEqual(result["memory"][1][500], 0)

    def test_failed_capability_query_becomes_minus_three(self):
        from capture_container_machine import SOURCE, CAPABILITIES, CLEANUP
        result, _ = self.execute("install", SOURCE, 8, 0, plan={CAPABILITIES: (0, ())})
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
        self.assertIn(CLEANUP, [row[0] for row in result["calls"]])

    def test_priority_and_failed_mode_restore(self):
        from capture_container_machine import SOURCE, MODE, PRIORITY_GET, PRIORITY_SET, GATE, ACTIVITY
        result, _ = self.execute("install", SOURCE, 8, 0, plan={PRIORITY_GET: (26, ()), (MODE, 1): (-9, ())})
        self.assertEqual([row[1][0] for row in result["calls"] if row[0] == PRIORITY_SET], [27, 26])
        self.assertEqual([row[1][0] for row in result["calls"] if row[0] == MODE], [0, 2, 1])
        self.assertEqual([(x[0], x[1][0]) for x in result["calls"][-2:]], [(GATE, 0), (ACTIVITY, 0)])
        self.assertEqual(result["result"], 0)

    def test_clock_report_retains_unsigned_wrap(self):
        from capture_container_machine import SOURCE, CAPABILITIES, NOTIFY
        from control_machine import GLOBAL
        memory = self.initial()
        struct.pack_into("<I", memory[0], 24, 0xFFFFFFFE)
        result, _ = self.execute("install", SOURCE, 8, 0, memory=memory,
                                 plan={CAPABILITIES: (1, ((GLOBAL + 24, 3, 4),))})
        self.assertIn((29, 2, 5 * 0xA00, 0), [row[1] for row in result["calls"] if row[0] == NOTIFY])
        self.assertEqual(self.word(result["memory"][1], 204), 3)

    def test_reader_zero_length_still_reads_payload(self):
        memory = self.initial()
        memory[16][:] = self.request(b"", slot=8, valid=0)
        result, reads = self.execute("read", 8192, memory=memory, reads=self.record_reads(b""))
        self.assertEqual(reads, [(0xCF000, 40), (0xCF028, 0)])
        self.assertEqual(result["result"], 0)
        self.assertEqual(self.word(result["memory"][16], 12), 0)
        self.assertEqual(result["memory"][16][16], 1)

    def test_extended_reader_fills_missing_identity(self):
        body = b"A2L1test"
        crc = zlib.crc32(body)
        payload = body + struct.pack("<I", crc)
        memory = self.initial()
        memory[16][:] = self.request(payload, valid=0)
        struct.pack_into("<I", memory[16], 12, 99)
        result, _ = self.execute("read", 8192, memory=memory, reads=self.record_reads(payload))
        self.assertEqual(result["result"], 0)
        self.assertEqual(self.word(result["memory"][16], 12), crc)
        self.assertEqual(result["memory"][16][16], 1)

    def test_reader_rejects_changed_header_after_valid_crc(self):
        for field in (4, 8, 12):
            memory = self.initial()
            memory[16][:] = self.request()
            memory[16][field] ^= 1
            result, reads = self.execute("read", 8192, memory=memory, reads=self.record_reads())
            self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
            self.assertEqual(len(reads), 2)
            self.assertEqual(result["memory"][16], memory[16])

    def test_partial_payload_failure_preserves_written_prefix(self):
        memory = self.initial()
        memory[16][:] = self.request()
        result, _ = self.execute("read", 8192, memory=memory,
                                 reads=[(0, self.record(), ()), (1, b"xy", ())])
        self.assertEqual(result["result"], (-2) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][17][:4], b"xy\xa6\xa6")
        self.assertEqual(result["memory"][16], memory[16])

    def test_integrated_slot_executes_reader_and_commits_both_states(self):
        from capture_container_machine import HEAP, PROCESS_LOAD, LOADER
        result, reads = self.execute("slot", 2, reads=self.slot_reads())
        self.assertEqual(reads, [(0xE3000, 40), (0xE3028, 4), (0xE3000, 40), (0xE3028, 8)])
        self.assertEqual(result["result"], 0)
        self.assertIn(LOADER, result["visited"])
        self.assertEqual(result["memory"][0][9], 2)
        self.assertEqual(self.word(result["memory"][1], 676), HEAP)
        self.assertEqual(result["memory"][1][1780], 1)
        self.assertIn(PROCESS_LOAD, [row[0] for row in result["calls"]])

    def test_integrated_failure_restores_slot_gain_metadata(self):
        from capture_container_machine import PROCESS_LOAD, METADATA
        memory = self.initial()
        result, _ = self.execute("slot", 2, memory=memory, reads=self.slot_reads(),
                                 plan={PROCESS_LOAD: (-7, ()), METADATA: (0x01019018, ())})
        self.assertEqual(result["result"], (-7) & 0xFFFFFFFF)
        self.assertEqual(result["memory"][1][696:708], memory[1][696:708])
        self.assertEqual(self.word(result["memory"][1], 276), 12)
        self.assertEqual(result["memory"][1][1780], 0)

    def test_payload_growth_is_outside_native_domain(self):
        memory = self.initial()
        memory[16][:] = self.request()
        with self.assertRaisesRegex(ValueError, "allocated request"):
            self.execute("read", 4, memory=memory, reads=self.record_reads())

    def test_invalid_operation_and_loader_are_rejected(self):
        from capture_container_machine import SOURCE
        for operation, args in (("install", (SOURCE, 8, 123)), ("read", (8193,)), ("slot", (-1,)), ("unknown", (0,))):
            with self.assertRaisesRegex(ValueError, "call domain"):
                self.program.execute(self.initial(), operation, *args)


if __name__ == "__main__":
    unittest.main()
