"""Offline MINI entry-branch and bounded RAM transport tests; no device opened."""
import binascii
import ctypes as c
from pathlib import Path
import random
import struct
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from probe_mini_recovery import (MiniRamSession, MiniNorSession, WindowsRomTransport,
                                 RomCommandError, validate_reset_artifact,
                                 RAM_SLOTS, SLOT_BYTES, SOFT_KEY_USB,
                                 inspect_stock, offline_upload_plan, ram_jump_cdb, ram_read_cdb,
                                 ram_write_cdb, rom_read_cdb, sha, usb_crc_transform,
                                 usb_entry_branch_model, validate_ram_request, validate_nor_request)


def reference_transform(data, key=0xFFFFFFFF):
    """Independent bitwise CRC model, shared by the fake ROM wire protocol."""
    def crc(data, state):
        for byte in data:
            state ^= byte << 8
            for _ in range(8):
                state = ((state << 1) ^ (0x1021 if state & 0x8000 else 0)) & 0xFFFF
        return state
    magic = bytes.fromhex("c3cfc0e8ced2b0aec4e3a3acd3f1c1d6")
    state, result = crc((key >> 16).to_bytes(2, "little"), key & 0xFFFF), bytearray()
    for i, byte in enumerate(data):
        state = crc(bytes([magic[i % 16]]), state)
        result.append(byte ^ (state & 255))
    return bytes(result)


class FakeRom:
    """In-memory reference model; never a hardware transport fallback."""
    def __init__(self, slot=RAM_SLOTS[0]):
        self.slot, self.memory = slot, bytearray([0xA5] * SLOT_BYTES)
        self.commands, self.running = [], False
        self.corrupt_readback, self.lose_jump_reply, self.short_read = False, False, False
        self.plain_readback = False
        self.jump_error = None
        self.identity = bytes.fromhex("fc60 00000009 48595231 00000000 0001")

    def exchange(self, cdb, data_out=None, read_length=0):
        validate_ram_request(cdb, data_out, read_length, slot=self.slot)
        opcode = int.from_bytes(cdb[:2], "big")
        self.commands.append(opcode)
        address, length = struct.unpack_from(">IH", cdb, 2)
        offset = address - self.slot
        if opcode == 0xFB06:
            assert not self.running
            self.memory[offset:offset + length] = reference_transform(data_out)
            return b""
        if opcode == 0xFD07:
            data = bytes(self.memory[offset:offset + length])
            if not self.plain_readback:
                data = reference_transform(data)
            return (bytes([data[0] ^ 1]) + data[1:]) if self.corrupt_readback else data
        if opcode == 0xFB08:
            self.running = True
            if self.jump_error is not None:
                raise self.jump_error
            if self.lose_jump_reply:
                raise OSError("simulated lost jump reply")
            return b"\xfb\x08" + bytes(14)
        if opcode == 0xFC60:
            assert self.running
            return self.identity
        if opcode == 0xFD61:
            assert self.running
            data = bytes(self.memory[offset:offset + length])
            return data[:-1] if self.short_read else data
        raise AssertionError("unexpected fake command")


class FakeNor(FakeRom):
    def __init__(self):
        super().__init__()
        self.count, self.sticky, self.initialized = 0, 0, False
        self.capacity, self.bad_count = 0x100000, False

    def exchange(self, cdb, data_out=None, read_length=0):
        op = int.from_bytes(cdb[:2], "big")
        if op in (0xFB06, 0xFD07, 0xFB08):
            return super().exchange(cdb, data_out, read_length)
        validate_nor_request(cdb, data_out, read_length, slot=self.slot)
        self.commands.append(op)
        if op == 0xFC70:
            return b"\xfc\x70HYRN\x01\x03" + struct.pack(">II", self.slot, SLOT_BYTES)
        if op == 0xFC72:
            self.initialized = True
            return b"\xfc\x72\x00\x01\xeb\x60\x14\x0f" + struct.pack(">II", self.capacity, 0)
        if op == 0xFC73:
            return bytes((0xfc, 0x73, self.sticky, int(self.initialized))) + struct.pack(">III", 0, 0x80, self.count - int(self.bad_count))
        if op == 0xFD71:
            assert self.initialized
            address, length = struct.unpack_from(">IH", cdb, 2)
            self.count += length
            return bytes((address + i) & 255 for i in range(length))
        raise AssertionError("unexpected NOR command")


class RecoveryProtocolTests(unittest.TestCase):
    def test_primary_crc_stream_vector_and_independent_bitwise_model(self):
        self.assertEqual(usb_crc_transform(bytes.fromhex("0f98")), bytes.fromhex("203c"))
        rng = random.Random(0x4D494E49)
        for n in (0, 1, 2, 15, 16, 17, 511, 512, 513, 1024):
            data, key = rng.randbytes(n), rng.getrandbits(32)
            expected = reference_transform(data, key)
            self.assertEqual(usb_crc_transform(data, key), expected)
            self.assertEqual(usb_crc_transform(expected, key), data)

    def test_exact_cdb_endianness_and_scope(self):
        slot = RAM_SLOTS[0]
        transformed = bytes.fromhex("203c")
        write = ram_write_cdb(slot, transformed, slot=slot)
        self.assertEqual(write[:9], bytes.fromhex("fb06 01c20000 0002 00"))
        self.assertEqual(write[9:11], binascii.crc_hqx(transformed, 0).to_bytes(2, "little"))
        self.assertEqual(write[11:], b"\xff" * 5)
        self.assertEqual(ram_jump_cdb(slot).hex(), "fb0801c200000001ffffffffffffffff")
        self.assertEqual(ram_read_cdb(slot + 3, 17, slot=slot).hex(), "fd6101c200030011ffffffffffffffff")
        self.assertEqual(rom_read_cdb(slot + 3, 17, slot=slot)[:2], b"\xfd\x07")
        for opcode in (0xFB00, 0xFB01, 0xFB02, 0xFB04, 0xFD05, 0xFC09, 0xFC12, 0xFC43):
            with self.assertRaises(ValueError):
                validate_ram_request(opcode.to_bytes(2, "big") + b"\xff" * 14, None, 16, slot=slot)
        for address, length in ((slot - 1, 1), (slot + SLOT_BYTES, 1), (slot + SLOT_BYTES - 1, 2),
                                (slot, 0), (slot, 4097), (0x02000000, 16), (0x01C7FD80, 16)):
            with self.assertRaises(ValueError):
                ram_read_cdb(address, length, slot=slot)

    def test_wrong_crc_direction_and_extra_bytes_rejected(self):
        slot, data = RAM_SLOTS[0], b"ab"
        valid = ram_write_cdb(slot, data, slot=slot)
        validate_ram_request(valid, data, 0, slot=slot)
        malformed = bytearray(valid); malformed[9] ^= 1
        for cdb, outbound, count in ((bytes(malformed), data, 0), (valid, None, 2),
                                     (valid, data, 2), (valid + b"\0", data, 0),
                                     (ram_jump_cdb(slot), None, 15)):
            with self.assertRaises(ValueError):
                validate_ram_request(cdb, outbound, count, slot=slot)

    def test_offline_plan_boundaries_and_stream_restart(self):
        slot, image = RAM_SLOTS[0], bytes(range(256)) * 3 + b"z"
        plan = offline_upload_plan(image, slot)
        self.assertEqual([b["length"] for b in plan["blocks"]], [512, 257])
        self.assertEqual(plan["blocks"][1]["transmitted_sha256"], sha(usb_crc_transform(image[512:])))
        self.assertFalse(plan["live_slot_state_verified"])
        self.assertFalse(plan["flat_entry_and_workspace_validated"])
        for data, base, occupied in ((b"", slot, ()), (bytes(SLOT_BYTES + 1), slot, ()),
                                    (b"\x7fELF", slot, ()), (b"abcd", slot + 4, ()),
                                    (b"abcd", slot, (slot,))):
            with self.assertRaises(ValueError):
                offline_upload_plan(data, base, occupied)

    @patch("time.sleep")
    def test_ram_roundtrip_and_full_slot_read(self, _sleep):
        image = bytes(range(256)) * 4 + b"end"
        for slot in RAM_SLOTS:
            transport = FakeRom(slot)
            session = MiniRamSession(transport, slot=slot, known_free_slot=True)
            result = session.upload_and_start(image, expected_sha256=sha(image))
            self.assertEqual(result["rom_readback_sha256"], sha(image))
            self.assertEqual(result["selftest_count"], 9)
            self.assertEqual(session.read(slot, len(image)), image)
            self.assertEqual(len(session.read(slot, SLOT_BYTES)), SLOT_BYTES)
            self.assertEqual(transport.commands.count(0xFB08), 1)
            self.assertLessEqual(set(transport.commands), {0xFB06, 0xFD07, 0xFB08, 0xFC60, 0xFD61})
            before = len(transport.commands)
            with self.assertRaises(ValueError):
                session.upload_and_start(image, expected_sha256=sha(image))
            self.assertEqual(len(transport.commands), before)

    def test_no_jump_after_bad_readback_or_unknown_slot(self):
        transport, image = FakeRom(), b"a" * 513
        session = MiniRamSession(transport, slot=RAM_SLOTS[0])
        with self.assertRaises(ValueError):
            session.upload_and_start(image, expected_sha256=sha(image))
        self.assertFalse(transport.commands)
        transport.corrupt_readback = True
        session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
        with self.assertRaisesRegex(ValueError, "readback differs"):
            session.upload_and_start(image, expected_sha256=sha(image))
        self.assertNotIn(0xFB08, transport.commands)
        self.assertTrue(session.failed)

    @patch("time.sleep")
    def test_already_uploaded_slot_requires_history_and_new_transformed_readback(self, _sleep):
        transport, image = FakeRom(), bytes(range(256)) * 2 + b"last"
        uploader = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
        upload = uploader.upload_only(image, expected_sha256=sha(image))
        self.assertFalse(upload["jump_sent"])
        self.assertEqual(transport.commands, [0xFB06, 0xFB06])
        unknown = MiniRamSession(transport, slot=RAM_SLOTS[0])
        with self.assertRaisesRegex(ValueError, "never-started"):
            unknown.verify_and_start(image, expected_sha256=sha(image))
        resumed = MiniRamSession(transport, slot=RAM_SLOTS[0], known_uploaded_unstarted=True)
        self.assertTrue(resumed.verify_upload_only(image, expected_sha256=sha(image))["readback_verified"])
        self.assertNotIn(0xFB08, transport.commands)
        first_verify = len(transport.commands)
        result = resumed.verify_and_start(image, expected_sha256=sha(image))
        self.assertTrue(result["jump_sent"])
        self.assertEqual(transport.commands[first_verify:], [0xFD07, 0xFD07, 0xFB08, 0xFC60])
        self.assertEqual(result["rom_wire_sha256"], sha(reference_transform(image[:512]) + reference_transform(image[512:])))

    def test_plain_fd07_is_rejected_without_autodetection_fallback(self):
        transport, image = FakeRom(), b"a" * 513
        transport.plain_readback = True
        session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
        with self.assertRaisesRegex(ValueError, "readback differs"):
            session.upload_and_start(image, expected_sha256=sha(image))
        self.assertNotIn(0xFB08, transport.commands)

    @patch("time.sleep")
    def test_no_retry_after_lost_jump_or_invalid_plugin(self, _sleep):
        image = b"test image"
        for error in ("lost", "badmagic", "failed", "version", "zero"):
            transport = FakeRom()
            if error == "lost": transport.lose_jump_reply = True
            else:
                answer = bytearray(transport.identity)
                if error == "badmagic": answer[6] ^= 1
                if error == "failed": answer[13] = 1
                if error == "version": answer[15] = 2
                if error == "zero": answer[2:6] = bytes(4)
                transport.identity = bytes(answer)
            session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
            with self.assertRaises((ValueError, OSError)):
                session.upload_and_start(image, expected_sha256=sha(image))
            before = len(transport.commands)
            with self.assertRaises(ValueError):
                session.upload_and_start(image, expected_sha256=sha(image))
            self.assertEqual(len(transport.commands), before)
            self.assertEqual(transport.commands.count(0xFB08), 1)

    @patch("time.sleep")
    def test_read_failure_poisoned_session(self, _sleep):
        transport, image = FakeRom(), b"test"
        session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
        with self.assertRaises(ValueError): session.read(RAM_SLOTS[0], 1)
        session.upload_and_start(image, expected_sha256=sha(image))
        transport.short_read = True
        with self.assertRaisesRegex(ValueError, "short plugin read"):
            session.read(RAM_SLOTS[0], 16)
        before = len(transport.commands)
        with self.assertRaises(ValueError): session.read(RAM_SLOTS[0], 16)
        self.assertEqual(before, len(transport.commands))


class ResetProtocolTests(unittest.TestCase):
    def artifact(self, slot=RAM_SLOTS[0]):
        image = bytes(range(32))
        elf = bytearray(96 + len(image))
        elf[:7] = b"\x7fELF\x01\x01\x01"
        struct.pack_into("<HHIIIIIHHHHHH", elf, 16,
                         2, 0xF1, 1, slot, 52, 0, 0, 52, 32, 1, 0, 0, 0)
        struct.pack_into("<8I", elf, 52, 1, 96, slot, slot, len(image), len(image), 5, 32)
        elf[96:] = image
        manifest = {"kind": "mini-ram-reset", "slot": slot, "entry": slot,
                    "image_bytes": len(image), "image_sha256": sha(image),
                    "elf_sha256": sha(elf), "no_flash_writes": True}
        return image, bytes(elf), manifest

    def test_manifest_and_elf_binding_reject_mismatches_before_io(self):
        image, elf, manifest = self.artifact()
        validate_reset_artifact(image, elf, manifest, slot=RAM_SLOTS[0])
        for key, value in (("kind", "other"), ("slot", RAM_SLOTS[1]), ("entry", RAM_SLOTS[0] + 2),
                           ("image_bytes", 33), ("image_sha256", "0" * 64),
                           ("elf_sha256", "0" * 64), ("no_flash_writes", False)):
            transport = FakeRom()
            session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_uploaded_unstarted=True)
            with self.assertRaisesRegex(ValueError, "manifest"):
                session.start_reset_once(image, elf=elf, manifest={**manifest, key: value})
            self.assertFalse(transport.commands)
        for offset, value in ((24, RAM_SLOTS[0] + 2), (52 + 12, RAM_SLOTS[1]), (52 + 20, 33)):
            invalid = bytearray(elf)
            struct.pack_into("<I", invalid, offset, value)
            with self.assertRaises(ValueError):
                validate_reset_artifact(image, bytes(invalid), {**manifest, "elf_sha256": sha(invalid)}, slot=RAM_SLOTS[0])

    def test_reset_verifies_and_jumps_once_without_plugin_handshake(self):
        image, elf, manifest = self.artifact()
        for mode in ("echo", "disconnect"):
            transport = FakeRom()
            session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
            session.upload_only(image, expected_sha256=sha(image))
            if mode == "disconnect":
                transport.jump_error = RomCommandError(1167, "simulated disconnect", submitted=True)
            result = session.start_reset_once(image, elf=elf, manifest=manifest)
            self.assertEqual(transport.commands, [0xFB06, 0xFD07, 0xFB08])
            self.assertFalse(result["reset_completion_verified"])
            self.assertTrue(result["normal_mini_usb_identity_required"])
            self.assertEqual(result["jump_outcome"], "fb08_echo_received" if mode == "echo" else "post_submit_transport_error")
            with self.assertRaises(ValueError):
                session.start_reset_once(image, elf=elf, manifest=manifest)
            self.assertEqual(transport.commands.count(0xFB08), 1)

    def test_reset_preserves_readback_and_pre_submission_errors(self):
        image, elf, manifest = self.artifact()
        for mode in ("readback", "pre_submit", "unknown_io"):
            transport = FakeRom()
            session = MiniRamSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
            session.upload_only(image, expected_sha256=sha(image))
            if mode == "readback": transport.corrupt_readback = True
            elif mode == "pre_submit": transport.jump_error = RomCommandError("not submitted", submitted=False)
            else: transport.jump_error = OSError("unknown transport phase")
            with self.assertRaises((ValueError, OSError)):
                session.start_reset_once(image, elf=elf, manifest=manifest)
            self.assertNotIn(0xFC60, transport.commands)
            if mode == "readback": self.assertNotIn(0xFB08, transport.commands)


class NorProtocolTests(unittest.TestCase):
    @patch("time.sleep")
    def test_init_explicit_and_status_after_every_read(self, _sleep):
        transport, image = FakeNor(), b"reader image"
        session = MiniNorSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
        session.upload_and_start(image, expected_sha256=sha(image))
        self.assertFalse(transport.initialized)
        self.assertNotIn(0xFC72, transport.commands)
        with self.assertRaises(ValueError): session.read_flash(0, 1)
        self.assertEqual(session.initialize_spi()["capacity"], 0x100000)
        start = len(transport.commands)
        self.assertEqual(session.read_flash(5, 1025), bytes((5 + i) & 255 for i in range(1025)))
        self.assertEqual(transport.commands[start:], [0xFD71, 0xFC73] * 3)
        self.assertEqual(session.successful_bytes, 1025)
        self.assertEqual(session.read_flash(0xFFFFF, 1), b"\xff")
        with self.assertRaises(ValueError): session.read_flash(0xFFFFF, 2)

    @patch("time.sleep")
    def test_error_or_wrong_counter_discards_read_and_poisoned_session(self, _sleep):
        for mode in ("sticky", "count"):
            transport, image = FakeNor(), b"reader"
            session = MiniNorSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
            session.upload_and_start(image, expected_sha256=sha(image)); session.initialize_spi()
            if mode == "sticky": transport.sticky = 2
            else: transport.bad_count = True
            with self.assertRaisesRegex(ValueError, "block discarded"):
                session.read_flash(0, 512)
            self.assertTrue(session.failed)
            before = len(transport.commands)
            with self.assertRaises(ValueError): session.read_flash(0, 512)
            self.assertEqual(before, len(transport.commands))

    @patch("time.sleep")
    def test_other_capacity_and_legacy_flash_commands_rejected(self, _sleep):
        transport, image = FakeNor(), b"reader"
        session = MiniNorSession(transport, slot=RAM_SLOTS[0], known_free_slot=True)
        session.upload_and_start(image, expected_sha256=sha(image))
        transport.capacity = 0x200000
        with self.assertRaisesRegex(ValueError, "capacity"):
            session.initialize_spi()
        for opcode in (0xFB00, 0xFB01, 0xFB02, 0xFB04, 0xFD05, 0xFC12, 0xFC43, 0xFC60, 0xFD61):
            with self.assertRaises(ValueError):
                validate_nor_request(opcode.to_bytes(2, "big") + b"\xff" * 14, None, 16, slot=RAM_SLOTS[0])


class WindowsTransportTests(unittest.TestCase):
    def fake_kernel(self, *, wrong_identity=False):
        kernel = MagicMock()
        kernel.CreateFileW.return_value = 123
        def exchange(handle, ioctl, inbound, in_size, outbound, out_size, returned, overlapped):
            self.assertEqual((handle, ioctl, in_size, out_size), (123, 0x4D014, 88, 88))
            self.assertIs(inbound._obj, outbound._obj)
            s = inbound._obj.sptd
            self.assertEqual((s.length, s.target_id, s.sense_info_offset, s.data_in), (56, 1, 56, 1))
            self.assertEqual(bytes(s.cdb[:6]), bytes((0x12, 0, 0, 0, 36, 0)))
            data = (c.c_ubyte * 36).from_address(s.data_buffer)
            data[:] = bytes(8) + (b"WRONG   " if wrong_identity else b"WL82    ") + b"UBOOT1.00       " + bytes(4)
            returned._obj.value = 88
            return 1
        kernel.DeviceIoControl.side_effect = exchange
        return kernel

    def test_windows_layout_identity_and_allowlist_without_real_api(self):
        path = r"\\.\PhysicalDrive42"
        kernel = self.fake_kernel()
        with patch("os.name", "nt"), patch("ctypes.WinDLL", return_value=kernel, create=True), \
                patch("probe_mini_recovery.discover_windows_rom_disks", return_value=[{"path": path}]):
            with WindowsRomTransport(path, slot=RAM_SLOTS[0]) as transport:
                self.assertEqual(transport.inquiry["product"], "UBOOT1.00")
                with self.assertRaises(ValueError): transport.exchange(b"\xfb\x01" + b"\xff" * 14, read_length=16)
                self.assertEqual(kernel.DeviceIoControl.call_count, 1)
            kernel.CloseHandle.assert_called_once_with(123)

    def test_failed_ioctl_preserves_win32_and_sptd_diagnostics_without_payload(self):
        path, kernel = r"\\.\PhysicalDrive42", self.fake_kernel()
        sense = bytes.fromhex("700005000000000a00000000200000000000") + bytes(14)
        with patch("os.name", "nt"), patch("ctypes.WinDLL", return_value=kernel, create=True), \
                patch("probe_mini_recovery.discover_windows_rom_disks", return_value=[{"path": path}]), \
                patch("ctypes.get_last_error", return_value=31, create=True) as last_error:
            with WindowsRomTransport(path, slot=RAM_SLOTS[0]) as transport:
                def fail(_handle, _code, input_buffer, _input_size, _output, _output_size, returned, _overlap):
                    packet = input_buffer._obj
                    packet.sptd.scsi_status = 2
                    packet.sptd.data_transfer_length = 256
                    packet.sptd.sense_info_length = 18
                    packet.sense[:] = sense
                    returned._obj.value = 74
                    return 0
                kernel.DeviceIoControl.side_effect = fail
                before = kernel.DeviceIoControl.call_count
                with self.assertRaises(RomCommandError) as caught:
                    transport.exchange(rom_read_cdb(RAM_SLOTS[0], 512, slot=RAM_SLOTS[0]), read_length=512)
                error = caught.exception
                self.assertEqual(error.errno, 31)
                self.assertTrue(error.submitted)
                self.assertEqual(error.details, {"scsi_status": 2, "data_transfer_length": 256,
                                                "bytes_returned": 74, "sense_info_length": 18,
                                                "sense_hex": sense.hex()})
                self.assertEqual(kernel.DeviceIoControl.call_count, before + 1)
                last_error.assert_called_once_with()
                # Later Win32 calls changing the thread-local value cannot
                # change the already captured exception or expose its buffer.
                last_error.return_value = 121
                self.assertEqual(error.errno, 31)
                self.assertNotIn("data", error.details)

    def test_wrong_or_unidentified_disk_never_becomes_ram_session(self):
        path, kernel = r"\\.\PhysicalDrive42", self.fake_kernel(wrong_identity=True)
        with patch("os.name", "nt"), patch("ctypes.WinDLL", return_value=kernel, create=True), \
                patch("probe_mini_recovery.discover_windows_rom_disks", return_value=[]):
            with self.assertRaisesRegex(ValueError, "not uniquely"):
                WindowsRomTransport(path, slot=RAM_SLOTS[0])
            kernel.CreateFileW.assert_not_called()
        with patch("os.name", "nt"), patch("ctypes.WinDLL", return_value=kernel, create=True), \
                patch("probe_mini_recovery.discover_windows_rom_disks", return_value=[{"path": path}]):
            with self.assertRaisesRegex(ValueError, "INQUIRY"):
                WindowsRomTransport(path, slot=RAM_SLOTS[0])
            kernel.CloseHandle.assert_called_once_with(123)


class MiniStockEvidenceTests(unittest.TestCase):
    def test_mini_command_branch_and_wrong_firmware(self):
        raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
        report, app = inspect_stock(raw)
        self.assertTrue(report["mini_usb_recovery_command_static_support"])
        self.assertEqual(report["guard_model_negative_cases"], 73)
        self.assertTrue(usb_entry_branch_model(app, SOFT_KEY_USB))
        self.assertFalse(usb_entry_branch_model(app, bytes.fromhex("04f0222407357ff7")))
        self.assertFalse(report["ble_route_to_usb_handler_verified"])
        with self.assertRaisesRegex(ValueError, "pinned MINI"):
            inspect_stock(raw[:-1] + bytes([raw[-1] ^ 1]))


if __name__ == "__main__":
    unittest.main()
