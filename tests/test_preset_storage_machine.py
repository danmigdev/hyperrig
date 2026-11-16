"""Hand-calculated preset validation checks using synthetic data only."""
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class PresetStorageInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from preset_storage_machine import PresetStorageProgram
        from verify_preset_storage import baseline, Flash, record
        cls.program = PresetStorageProgram()
        cls.initial = staticmethod(baseline)
        cls.flash = Flash
        cls.record = staticmethod(record)

    def calls(self, result):
        return [call[:2] for call in result["calls"]]

    def test_block_mapping_preserves_the_two_special_locations(self):
        for block, expected in ((0, 0xBF000), (15, 0xCE000), (16, 0xDD000),
                                (17, 0xDE000), (127, 0xDE000), (0xFFFFFFFF, 0xDE000)):
            result = self.program.execute(self.initial(), "block", block)
            self.assertEqual(result["result"], expected)

    def test_preset_pairs_and_signed_missing_mapping(self):
        for preset, expected in ((0, 0xBF000), (1, 0xBF800), (30, 0xCE000), (31, 0xCE800), (32, 0)):
            self.assertEqual(self.program.execute(self.initial(), "address", preset)["result"], expected)
        for mapping in (128, 255):
            memory = self.initial()
            memory[7][0] = mapping
            self.assertEqual(self.program.execute(memory, "address", 1)["result"], 0)

    def test_crc_known_vector_and_raw_state(self):
        memory = self.initial()
        memory[10][:9] = b"123456789"
        self.assertEqual(self.program.execute(memory, "crc_update", 0xFFFFFFFF, 9)["result"], 0x340BC6D9)
        self.assertEqual(self.program.execute(memory, "checksum", 9)["result"], 0xCBF43926)

    def test_empty_crc_does_not_read_or_poll(self):
        for operation, arguments, expected in (("checksum", (0,), 0),
                                               ("crc_update", (0x12345678, 0), 0x12345678)):
            result = self.program.execute(self.initial(), operation, *arguments)
            self.assertEqual(result["result"], expected)
            self.assertEqual(result["calls"], [])

    def test_checksum_polls_only_between_chunks(self):
        for size, polls in ((255, 0), (256, 0), (257, 1), (512, 1), (513, 2)):
            memory = self.initial()
            memory[10][:size] = bytes(size)
            result = self.program.execute(memory, "checksum", size)
            self.assertEqual(result["result"], zlib.crc32(bytes(size)))
            self.assertEqual(self.calls(result), [(0x20027E4, (0, 0, 0))] * polls)

    def test_header_checks_tag_and_upper_bound_but_not_crc(self):
        for tag, declared, maximum, expected in ((0, 3, 1490, 0), (0x51474B54, 1491, 1490, 0),
                (0x51474B54, 0, 1490, 1), (0x51474B54, 1490, 1490, 1)):
            flash = self.flash(((0xBF000, self.record(b"", tag=tag, size=declared, crc=0xBAD)),))
            result = self.program.execute(self.initial(), "header", 0xBF000, 0x51474B54, maximum, reader=flash.read)
            self.assertEqual(result["result"], expected)
            self.assertEqual(flash.requests, [(0xBF000, 40)])

    def test_valid_availability_updates_cache_after_priority_release(self):
        flash = self.flash(((0xBF000, self.record(b"abc")),))
        result = self.program.execute(self.initial(), "available", 0, reader=flash.read)
        self.assertEqual(result["result"], 1)
        self.assertEqual(self.calls(result), [(0x20031D4, (0, 0, 0)), (0x20054A8, (1, 0, 0)),
            (0x2002810, (0xBF000, "local_header", 0, 40)),
            (0x2002810, (0xBF028, "scratch", 0, 3)), (0x20054A8, (0, 0, 0))])
        self.assertEqual(struct.unpack_from("<I", result["calls"][-1][2][1], 708)[0], 0)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 708)[0], 1)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 732)[0], 1)
        self.assertEqual(result["memory"][8], b"abc" + bytes([0xA5] * 253))

    def test_cache_hit_calls_prepare_but_does_not_read(self):
        for available in (0, 1):
            memory = self.initial()
            struct.pack_into("<I", memory[1], 708, 1 << 31)
            struct.pack_into("<I", memory[1], 732, available << 31)
            result = self.program.execute(memory, "available", 31)
            self.assertEqual(result["result"], available)
            self.assertEqual(self.calls(result), [(0x20031D4, (0, 0, 0))])
            self.assertEqual(result["writes"], [])

    def test_invalid_preset_has_no_calls_or_writes(self):
        for preset in (32, 0xFFFFFFFF):
            result = self.program.execute(self.initial(), "available", preset)
            self.assertEqual(result["result"], 0)
            self.assertEqual(result["calls"], [])
            self.assertEqual(result["writes"], [])

    def test_crc_failure_is_cached_and_preserves_other_bits(self):
        memory = self.initial()
        struct.pack_into("<I", memory[1], 708, 0x80000000)
        struct.pack_into("<I", memory[1], 732, 0x80000001)
        flash = self.flash(((0xBF000, self.record(b"bad", crc=0)),))
        result = self.program.execute(memory, "available", 0, reader=flash.read)
        self.assertEqual(result["result"], 0)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 708)[0], 0x80000001)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 732)[0], 0x80000000)

    def test_payload_is_checked_in_256_byte_chunks(self):
        payload = bytes(range(256)) * 2 + b"end"
        flash = self.flash(((0xBF000, self.record(payload)),))
        result = self.program.execute(self.initial(), "available", 0, reader=flash.read)
        self.assertEqual(result["result"], 1)
        self.assertEqual(flash.requests, [(0xBF000, 40), (0xBF028, 256), (0xBF128, 256), (0xBF228, 3)])
        self.assertEqual(result["memory"][8], b"end" + bytes(range(3, 256)))

    def test_partial_payload_failure_keeps_written_scratch_bytes(self):
        payload = b"ABCDEFGHIJ"
        flash = self.flash(((0xBF000, self.record(payload)),), {2: (0xFFFFFFFE, 4)})
        result = self.program.execute(self.initial(), "available", 0, reader=flash.read)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][8], b"ABCD" + bytes([0xA5] * 252))
        self.assertEqual(self.calls(result)[-1], (0x20054A8, (0, 0, 0)))

    def test_transient_read_failure_stays_cached(self):
        regions = ((0xBF000, self.record(b"valid")),)
        failed = self.flash(regions, {1: (1, 0)})
        first = self.program.execute(self.initial(), "available", 0, reader=failed.read)
        restored = self.flash(regions)
        second = self.program.execute(first["memory"], "available", 0, reader=restored.read)
        self.assertEqual(second["result"], 0)
        self.assertEqual(restored.requests, [])

    def test_missing_mapping_still_reaches_the_read_boundary(self):
        memory = self.initial()
        memory[7][0] = 255
        flash = self.flash()
        result = self.program.execute(memory, "available", 0, reader=flash.read)
        self.assertEqual(flash.requests, [(0, 40)])
        self.assertEqual(result["result"], 0)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 708)[0], 1)

    def test_record_distinguishes_header_read_and_crc_failures(self):
        for encoded, failures, expected in ((self.record(b"abc", tag=0), {}, 0xFFFFFFFF),
                (self.record(b"abc"), {2: (1, 1)}, 0xFFFFFFFE),
                (self.record(b"abc", crc=0), {}, 0xFFFFFFFD),
                (self.record(b"abc"), {}, 0)):
            flash = self.flash(((0xBF000, encoded),), failures)
            result = self.program.execute(self.initial(), "record", 0xBF000, 0x51474B54, 1490, reader=flash.read)
            self.assertEqual(result["result"], expected)

    def test_record_fifth_abi_argument_receives_payload_without_overwriting_tail(self):
        flash = self.flash(((0xBF000, self.record(b"payload")),))
        result = self.program.execute(self.initial(), "record", 0xBF000, 0x51474B54, 1490, reader=flash.read)
        self.assertEqual(result["result"], 0)
        self.assertEqual(result["memory"][10], b"payload" + bytes([0x5A] * (1490 - 7)))
        self.assertEqual(self.calls(result)[1], (0x2002810, (0xBF028, "payload", 0, 7)))

    def test_failed_header_keeps_its_partial_output(self):
        encoded = self.record(b"abc")
        flash = self.flash(((0xBF000, encoded),), {1: (1, 12)})
        result = self.program.execute(self.initial(), "record", 0xBF000, 0x51474B54, 1490, reader=flash.read)
        self.assertEqual(result["result"], 0xFFFFFFFF)
        self.assertEqual(result["memory"][9], encoded[:12] + bytes([0xC3] * 28))
        self.assertEqual(result["memory"][10], bytes([0x5A] * 1490))

    def test_empty_record_reads_zero_bytes_but_availability_skips_payload_read(self):
        for operation, args, requests in (("available", (0,), [(0xBF000, 40)]),
                ("record", (0xBF000, 0x51474B54, 1490), [(0xBF000, 40), (0xBF028, 0)])):
            flash = self.flash(((0xBF000, self.record(b"")),))
            result = self.program.execute(self.initial(), operation, *args, reader=flash.read)
            self.assertEqual(result["result"], int(operation == "available"))
            self.assertEqual(flash.requests, requests)

    def test_poll_mutation_affects_only_subsequent_checksum_bytes(self):
        from preset_storage_machine import PAYLOAD_BUFFER
        memory = self.initial()
        memory[10][:257] = bytes(257)
        def poll(service, args, machine):
            self.assertEqual(service, 0x20027E4)
            machine.write(PAYLOAD_BUFFER, 99, 1)
            machine.write(PAYLOAD_BUFFER + 256, 77, 1)
            return 0
        result = self.program.execute(memory, "checksum", 257, boundary=poll)
        self.assertEqual(result["result"], zlib.crc32(bytes(256) + bytes((77,))))

    def test_integrated_navigation_queries_real_validation(self):
        flash = self.flash(((0xC0000, self.record(b"preset 2")),))
        result = self.program.execute(self.initial(), "preset_step", 1, reader=flash.read)
        self.assertEqual(self.calls(result)[-1], (0x200CA7E, (2, 0, 0)))
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 708)[0], 6)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 732)[0], 4)

    def test_missing_reader_and_invalid_crc_domain_fail(self):
        with self.assertRaisesRegex(ValueError, "no read boundary"):
            self.program.execute(self.initial(), "available", 0)
        with self.assertRaisesRegex(ValueError, "CRC domain"):
            self.program.execute(self.initial(), "checksum", 1491)
        with self.assertRaisesRegex(ValueError, "buffer contract"):
            self.program.execute(self.initial(), "available", 0, reader=lambda address, size: (0, b""))


if __name__ == "__main__":
    unittest.main()
