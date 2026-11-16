"""Hand-checked capture gain, signature, reuse and failure expectations."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class CaptureLoaderInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from capture_loader_machine import CaptureLoaderProgram
        from verify_capture_loader import baseline, record, load_reads, Reads, Script
        cls.program = CaptureLoaderProgram()
        cls.initial, cls.record, cls.load_reads = staticmethod(baseline), staticmethod(record), staticmethod(load_reads)
        cls.Reads, cls.Script = Reads, Script

    def execute(self, operation, *arguments, memory=None, reads=(), plan=None):
        source = self.Reads(reads)
        result = self.program.execute(memory or self.initial(), operation, *arguments,
                                      reader=source.read, boundary=self.Script(plan))
        self.assertEqual(len(source.requests), len(reads))
        return result, source.requests

    @staticmethod
    def word(data, offset=0):
        return struct.unpack_from("<I", data, offset)[0]

    def test_metadata_versions_and_signed_boundaries(self):
        for value, expected in ((0, 1), (24, 1), (0xE8, 1), (25, 0), (0xE7, 0),
                                (0x100, 0), (0x01019018, 1), (0x01FF38E8, 1),
                                (0x01019100, 0), (0x01FF3700, 0), (0x02000000, 0)):
            result, _ = self.execute("valid", value)
            self.assertEqual(result["result"], expected, hex(value))

    def test_invalid_aux_does_not_write_output(self):
        memory = self.initial()
        result, _ = self.execute("aux", 0, memory=memory)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][14], memory[14])

    def test_aux_sign_extends(self):
        result, _ = self.execute("aux", 0x01FF3800)
        self.assertEqual(result["result"], 1)
        self.assertEqual(self.word(result["memory"][14]), (-200) & 0xFFFFFFFF)

    def test_clamp_and_unity_table(self):
        for value, expected in ((0x80000000, -24), (0xFFFFFFFF, -1), (0, 0), (0x7FFFFFFF, 24)):
            result, _ = self.execute("clamp", value)
            self.assertEqual(result["result"], expected & 0xFFFFFFFF)
        result, _ = self.execute("scale", 0)
        self.assertEqual(result["result"], 1 << 24)

    def test_mix_rounding_flag_and_counter_wrap(self):
        memory = self.initial()
        struct.pack_into("<IIII", memory[1], 264, 1, 1, 0, 0xFFFFFFFF)
        result, _ = self.execute("mix", 99, memory=memory)
        self.assertEqual(self.word(result["memory"][1], 272), (0x010F2B41 ** 2 + 0x800000) >> 24)
        self.assertEqual(self.word(result["memory"][1], 276), 0)
        self.assertEqual(result["memory"][1][16], 1)

    def test_invalid_metadata_clears_aux_and_uses_zero_gain(self):
        result, _ = self.execute("apply_metadata", 0x02000000, 0)
        state = result["memory"][1]
        self.assertEqual(struct.unpack_from("<III", state, 696), (0, 0, 0))
        self.assertEqual(self.word(state, 264), 0)
        self.assertEqual(self.word(state, 272), 1 << 24)
        self.assertEqual(state[16], 0)

    def test_signature_reads_before_short_length_check(self):
        memory = self.initial()
        memory[9][:] = self.record(0)
        result, reads = self.execute("signature", 8, memory=memory, reads=[(0, b"AM2\0", ())])
        self.assertEqual(reads, [(0xCF028, 4)])
        self.assertEqual(result["result"], 0)

    def test_a2_signature_exempts_legacy_lengths(self):
        for size in (6144, 7808):
            memory = self.initial()
            memory[9][:] = self.record(size)
            good, _ = self.execute("signature", 0, memory=memory, reads=[(0, b"A2L1", ())])
            bad, _ = self.execute("signature", 0, memory=memory, reads=[(0, b"xxxx", ())])
            self.assertEqual((good["result"], bad["result"]), (0, 1))

    def test_header_failure_exits_after_priority_restore(self):
        from capture_loader_machine import ACTIVITY, PRIORITY, NOTIFY
        from preset_storage_machine import READ
        result, _ = self.execute("load", 2, reads=[(1, b"", ())])
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual([x[0] for x in result["calls"]], [ACTIVITY, PRIORITY, READ, PRIORITY, NOTIFY, ACTIVITY])
        self.assertEqual(result["calls"][-2][1], (20, 2, 0xFFFFFFFF))

    def test_current_slot_reuses_despite_failed_identity_read(self):
        from verify_capture_loader import MARKER
        from capture_loader_machine import INSTALL, NOTIFY
        memory = self.initial()
        memory[0][9] = 2
        result, reads = self.execute("load", 2, memory=memory,
            reads=self.load_reads(marker=MARKER, reuse=True, trailer_status=1))
        self.assertEqual(result["result"], 0)
        self.assertEqual(len(reads), 2)
        self.assertNotIn(INSTALL, [row[0] for row in result["calls"]])
        self.assertEqual(result["memory"][1][1780:1796], memory[1][1780:1796])
        self.assertEqual([row[1] for row in result["calls"] if row[0] == NOTIFY], [(20, 0x502, 0)])

    def test_descriptor_reuse_commits_current_slot(self):
        from capture_loader_machine import INSTALL
        memory = self.initial()
        memory[1][1780:1796] = struct.pack("<BB2xIII", 1, 0, 0x12345678, 64, 0)
        result, _ = self.execute("load", 2, memory=memory, reads=self.load_reads(reuse=True))
        self.assertEqual((result["memory"][0][9], result["memory"][0][18]), (2, 255))
        self.assertNotIn(INSTALL, [row[0] for row in result["calls"]])

    def test_signature_rejection_does_not_apply_metadata(self):
        from capture_loader_machine import INSTALL, METADATA
        memory = self.initial()
        result, _ = self.execute("load", 2, memory=memory, reads=self.load_reads(signature=b"AM2\0"),
                                 plan={METADATA: (0x01019018, ())})
        self.assertEqual(result["result"], (-111) & 0xFFFFFFFF)
        self.assertEqual(result["memory"], tuple(bytes(x) if i != 2 else x for i, x in enumerate(memory)))
        self.assertNotIn(INSTALL, [row[0] for row in result["calls"]])

    def test_install_observes_metadata_and_exact_request(self):
        from capture_loader_machine import INSTALL, METADATA, LOADER, NOTIFY
        result, _ = self.execute("load", 2, reads=self.load_reads(), plan={METADATA: (0x01019018, ())})
        calls = [row for row in result["calls"] if row[0] == INSTALL]
        self.assertEqual(calls[0][1], (0, 64, LOADER, struct.pack("<IIIIB", 2, 64, 0x12345678, 0x12345678, 1)))
        self.assertEqual(struct.unpack_from("<III", calls[0][2][1], 696), (24, 400, 1))
        self.assertEqual([row[1] for row in result["calls"] if row[0] == NOTIFY], [(20, 2, 0)])

    def test_request_identity_changes_but_captured_size_survives(self):
        from capture_loader_machine import INSTALL, REQUEST
        result, _ = self.execute("load", 2, reads=self.load_reads(),
            plan={INSTALL: (0, ((REQUEST + 4, 999, 4), (REQUEST + 12, 1234, 4)))})
        self.assertEqual(struct.unpack_from("<III", result["memory"][1], 1784), (1234, 64, 0))

    def test_request_invalidates_descriptor_presence_only(self):
        from capture_loader_machine import INSTALL, REQUEST
        memory = self.initial()
        result, _ = self.execute("load", 2, memory=memory, reads=self.load_reads(),
                                 plan={INSTALL: (0, ((REQUEST + 16, 0, 1),))})
        self.assertEqual(result["memory"][1][1780], 0)
        self.assertEqual(result["memory"][1][1781:1796], memory[1][1781:1796])

    def test_failure_rollback_is_partial(self):
        from capture_loader_machine import INSTALL, METADATA
        from control_machine import STATE
        memory = self.initial()
        result, _ = self.execute("load", 2, memory=memory, reads=self.load_reads(),
            plan={METADATA: (0x01019018, ()), INSTALL: (-3, ((STATE + 268, 4, 4),))})
        state = result["memory"][1]
        self.assertEqual(result["result"], (-3) & 0xFFFFFFFF)
        self.assertEqual(state[696:708], memory[1][696:708])
        self.assertEqual(self.word(state, 276), 12)
        self.assertEqual(self.word(state, 264), 2)
        self.assertEqual(self.word(state, 268), 4)
        self.assertEqual(self.word(state, 272), (0x011F3C9A * 0x014248F0 + 0x800000) >> 24)
        self.assertEqual(state[16], 1)
        self.assertEqual(result["memory"][0][9], 255)

    def test_full_slot_word_is_compared_before_byte_commit(self):
        from capture_loader_machine import INSTALL
        memory = self.initial()
        memory[0][9] = 255
        result, _ = self.execute("load", 0xFFFFFFFF, memory=memory, reads=self.load_reads())
        self.assertIn(INSTALL, [row[0] for row in result["calls"]])
        self.assertEqual(result["memory"][0][9], 255)

    def test_outside_argument_domain_is_rejected(self):
        for operation, args in (("unknown", (0,)), ("load", (-1,)), ("set_gain", (1,)), ("scale", (1 << 32,))):
            with self.assertRaisesRegex(ValueError, "call domain"):
                self.program.execute(self.initial(), operation, *args)


if __name__ == "__main__":
    unittest.main()
