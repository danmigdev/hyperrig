"""All Windows APIs are replaced; no device, enumeration or OS handle is used."""
from contextlib import ExitStack
import ctypes as c
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import mini_windows_aligned as aligned
from tools.probe_mini_recovery import RomCommandError

PATH = r"\\.\PhysicalDrive42"
SLOT = 0x01C20000
REAL_DESCRIPTOR = bytes.fromhex("2000000020000000000001001100000000000000000000000700010000000000")
INQUIRY = bytes(8) + b"WL82    " + b"UBOOT1.00       " + bytes(4)


def read_cdb(address=0x5000, count=256):
    return b"\xfd\x7f" + struct.pack(">IH", address, count) + b"\xff" * 8


class FakeKernel:
    def __init__(self, descriptor=REAL_DESCRIPTOR):
        self.descriptor = descriptor
        self.calls = []
        self.command_hook = None
        self.query_hook = None
        self.kernel = MagicMock()
        self.kernel.CreateFileW.return_value = 123
        self.kernel.DeviceIoControl.side_effect = self.exchange

    def exchange(self, handle, ioctl, inbound, in_size, outbound, out_size, returned, overlapped):
        assert handle == 123 and overlapped is None
        self.calls.append({"ioctl": ioctl})
        if ioctl == aligned.IOCTL_STORAGE_QUERY_PROPERTY:
            assert in_size == 12
            assert c.string_at(inbound, in_size) == struct.pack("<II4x", 1, 0)
            if self.query_hook:
                result = self.query_hook(self, outbound, out_size, returned)
                if result is not None:
                    return result
            outbound._obj[:] = self.descriptor[:out_size]
            returned._obj.value = out_size
            return 1
        assert ioctl == aligned.IOCTL_SCSI_PASS_THROUGH_DIRECT
        assert inbound._obj is outbound._obj and in_size == out_size == 88
        packet = inbound._obj
        s = packet.sptd
        assert (s.length, s.target_id, s.timeout_value, s.sense_info_offset) == (56, 1, 10, 56)
        assert s.data_buffer % 4096 == 0
        size = s.data_transfer_length
        data = (c.c_uint8 * size).from_address(s.data_buffer)
        cmd = bytes(s.cdb[:s.cdb_length])
        self.calls[-1].update({"cdb": cmd, "pointer": s.data_buffer, "length": size,
                               "direction": s.data_in, "out": bytes(data) if s.data_in == 0 else None})
        if self.command_hook:
            result = self.command_hook(packet, returned)
            if result is not None:
                return result
        if s.data_in:
            data[:] = INQUIRY if cmd[0] == 0x12 else bytes((i * 7) & 255 for i in range(size))
        returned._obj.value = 88
        return 1


class AlignedTests(unittest.TestCase):
    def fake_context(self, fake, *, last_error=31, profile="app-writer-operational"):
        stack = ExitStack()
        stack.enter_context(patch("os.name", "nt"))
        stack.enter_context(patch("ctypes.WinDLL", return_value=fake.kernel, create=True))
        stack.enter_context(patch("tools.probe_mini_recovery.discover_windows_rom_disks", return_value=[{"path": PATH}]))
        error = stack.enter_context(patch("ctypes.get_last_error", return_value=last_error, create=True))
        self.addCleanup(stack.close)
        transport = aligned.WindowsAlignedRomTransport(PATH, slot=SLOT, profile=profile)
        self.addCleanup(transport.close)
        return transport, error

    def test_actual_descriptor_parser_is_offline_and_mask_is_zero(self):
        result = aligned.parse_adapter_descriptor(REAL_DESCRIPTOR)
        self.assertEqual((result["version"], result["size"], result["alignment_mask"], result["bus_type"]), (32, 32, 0, 7))
        self.assertEqual((result["maximum_transfer_length"], result["maximum_physical_pages"]), (65536, 17))
        self.assertFalse(result["adapter_uses_pio"])

    def test_invalid_descriptors_fail_closed(self):
        vectors = [REAL_DESCRIPTOR[:-1], REAL_DESCRIPTOR + b"\0"]
        for offset, value in ((0, 16), (0, 33), (4, 33), (8, 0), (12, 0), (16, 2), (16, 0x1FFFFF)):
            raw = bytearray(REAL_DESCRIPTOR)
            struct.pack_into("<I", raw, offset, value)
            vectors.append(bytes(raw))
        raw = bytearray(REAL_DESCRIPTOR)
        raw[20] = 3
        vectors.append(bytes(raw))
        for raw in vectors:
            with self.subTest(raw=raw.hex()), self.assertRaises(ValueError):
                aligned.parse_adapter_descriptor(raw)

    def test_query_performs_only_two_metadata_calls(self):
        fake = FakeKernel()
        result = aligned.query_adapter_descriptor(fake.kernel, 123)
        self.assertEqual(result["query_output_sizes"], [8, 32])
        self.assertEqual(result["bytes_returned"], 32)
        self.assertEqual([item["ioctl"] for item in fake.calls], [aligned.IOCTL_STORAGE_QUERY_PROPERTY] * 2)

    def test_changed_truncated_and_oversized_query_fail(self):
        for mode in ("changed", "short-header", "short-full", "oversized", "huge-header"):
            fake = FakeKernel()
            def query_hook(_fake, out, size, returned):
                raw = bytearray(REAL_DESCRIPTOR[:size])
                if mode == "huge-header" and size == 8:
                    struct.pack_into("<I", raw, 4, 0x10000)
                if mode == "changed" and size == 32:
                    struct.pack_into("<I", raw, 0, 33)
                out._obj[:] = raw
                returned._obj.value = size - 1 if ((mode == "short-header" and size == 8) or
                                                  (mode == "short-full" and size == 32)) else size + (mode == "oversized")
                return 1
            fake.query_hook = query_hook
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                aligned.query_adapter_descriptor(fake.kernel, 123)
            self.assertLessEqual(len(fake.calls), 2)

    def test_failed_query_captures_last_error_and_submits_no_scsi(self):
        for failed_call in (1, 2):
            fake = FakeKernel()
            fake.query_hook = lambda f, out, n, ret: 0 if len(f.calls) == failed_call else None
            with patch("ctypes.get_last_error", return_value=31, create=True) as error:
                with self.assertRaises(RomCommandError) as caught:
                    aligned.query_adapter_descriptor(fake.kernel, 123)
                error.assert_called_once_with()
            self.assertEqual(caught.exception.errno, 31)
            self.assertFalse(caught.exception.submitted)
            self.assertEqual(caught.exception.details["phase"], "adapter-query")
            self.assertEqual(len(fake.calls), failed_call)

    def test_aligned_storage_bounds_and_lifetime_many_sizes(self):
        for size in (1, 16, 36, 128, 256, 260, 512, 4096, 4097):
            for alignment in (4096, 8192, 65536):
                with self.subTest(size=size, alignment=alignment):
                    buffer = aligned.AlignedBuffer(size, alignment)
                    self.assertEqual(buffer.address % alignment, 0)
                    self.assertEqual(c.addressof(buffer.view), buffer.address)
                    buffer.view[:] = b"\x73" * size
                    self.assertEqual(bytes(buffer.view), b"\x73" * size)
                    self.assertEqual(bytes(buffer.storage[:buffer.offset]), bytes(buffer.offset))
                    self.assertEqual(bytes(buffer.storage[buffer.offset + size:]), bytes(alignment - 1 - buffer.offset))
        for size, alignment in ((0, 4096), (1, 2048), (1, 4097), (1, 0x200000), (True, 4096), (0x100001, 4096)):
            with self.assertRaises(ValueError):
                aligned.AlignedBuffer(size, alignment)

    def test_constructor_and_exact_in_out_sizes_share_profile(self):
        fake = FakeKernel()
        transport, error = self.fake_context(fake)
        self.assertEqual(transport.inquiry["product"], "UBOOT1.00")
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual(transport.exchange(read_cdb(), read_length=256), bytes((i * 7) & 255 for i in range(256)))
        payload = bytes(range(256)) + struct.pack(">I", zlib.crc32(bytes(range(256))))
        stage = b"\xfb\x7c" + struct.pack(">IIIH", 1, 2, 0x5000, 256)
        self.assertEqual(transport.exchange(stage, data_out=payload), b"")
        self.assertEqual(fake.calls[-1]["out"], payload)
        self.assertEqual(fake.calls[-1]["length"], 260)
        self.assertEqual(transport.last_transfer["data_buffer_offset_4k"], 0)
        self.assertEqual(transport.last_transfer["span_pages_4k"], 1)
        self.assertEqual(transport.last_transfer["alignment_mask"], 0)
        error.assert_not_called()

    def test_larger_adapter_mask_is_honored(self):
        raw = bytearray(REAL_DESCRIPTOR)
        struct.pack_into("<I", raw, 16, 8191)
        fake = FakeKernel(bytes(raw))
        transport, _ = self.fake_context(fake)
        transport.exchange(read_cdb(), read_length=256)
        self.assertEqual(transport.last_transfer["data_buffer_alignment"], 8192)
        self.assertEqual(fake.calls[-1]["pointer"] % 8192, 0)

    def test_allowlist_and_transfer_limit_reject_before_ioctl(self):
        fake = FakeKernel()
        transport, _ = self.fake_context(fake, profile="app-writer-observer")
        before = len(fake.calls)
        erase = b"\xfc\x7b" + struct.pack(">III", 1, 3, 0x5000) + b"\xff\xff"
        with self.assertRaises(ValueError):
            transport.exchange(erase, read_length=16)
        with self.assertRaises(ValueError):
            transport.exchange(read_cdb(0x81F80, 512), read_length=512)
        transport.adapter_descriptor["maximum_transfer_length"] = 128
        with self.assertRaises(ValueError):
            transport.exchange(read_cdb(), read_length=256)
        self.assertEqual(len(fake.calls), before)
        with self.assertRaises(ValueError):
            aligned.validate_profile_request(read_cdb(), None, 256, slot=SLOT, profile="unknown")

    def test_win31_capture_is_immediate_terminal_and_has_no_payload(self):
        fake = FakeKernel()
        transport, error = self.fake_context(fake)
        order = []
        error.side_effect = lambda: order.append("last-error") or 31
        def fail(packet, returned):
            packet.sptd.scsi_status = 2
            packet.sptd.data_transfer_length = 128
            packet.sptd.sense_info_length = 18
            packet.sense[:] = bytes.fromhex("700005") + bytes(29)
            returned._obj.value = 74
            order.append("ioctl-failed")
            return 0
        fake.command_hook = fail
        before = len(fake.calls)
        with self.assertRaises(RomCommandError) as caught:
            transport.exchange(read_cdb(), read_length=256)
        self.assertEqual(order, ["ioctl-failed", "last-error"])
        self.assertEqual(caught.exception.errno, 31)
        self.assertTrue(caught.exception.submitted)
        details = caught.exception.details
        self.assertEqual((details["scsi_status"], details["data_transfer_length"], details["bytes_returned"]), (2, 128, 74))
        self.assertEqual(details["sense_info_length"], 18)
        self.assertEqual(details["sense_hex"], (bytes.fromhex("700005") + bytes(29)).hex())
        self.assertEqual(details["data_buffer_address"] % 4096, 0)
        self.assertNotIn("data", details)
        self.assertNotIn("response_hex", details)
        with self.assertRaises(OSError):
            transport.exchange(read_cdb(), read_length=256)
        self.assertEqual(len(fake.calls), before + 1)

    def test_bad_completions_fail_once_without_retry(self):
        for fault in ("short-transfer", "status", "sense-length", "short-packet", "large-packet"):
            fake = FakeKernel()
            transport, _ = self.fake_context(fake)
            def corrupt(packet, returned):
                returned._obj.value = 88
                if fault == "short-transfer": packet.sptd.data_transfer_length -= 1
                if fault == "status": packet.sptd.scsi_status = 2
                if fault == "sense-length": packet.sptd.sense_info_length = 33
                if fault == "short-packet": returned._obj.value = 0
                if fault == "large-packet": returned._obj.value = 89
                return 1
            fake.command_hook = corrupt
            before = len(fake.calls)
            with self.subTest(fault=fault), self.assertRaises(RomCommandError):
                transport.exchange(read_cdb(), read_length=256)
            self.assertTrue(transport.failed)
            self.assertEqual(len(fake.calls), before + 1)
            transport.close()

    def test_concurrent_exchange_and_closed_handle_send_nothing(self):
        fake = FakeKernel()
        transport, _ = self.fake_context(fake)
        before = len(fake.calls)
        transport._exchange_lock.acquire()
        try:
            with self.assertRaises(RuntimeError): transport.exchange(read_cdb(), read_length=256)
        finally:
            transport._exchange_lock.release()
        transport.close()
        with self.assertRaises(OSError): transport.exchange(read_cdb(), read_length=256)
        self.assertEqual(len(fake.calls), before)
        fake.kernel.CloseHandle.assert_called_once_with(123)

    def test_failed_constructor_query_closes_without_inquiry(self):
        fake = FakeKernel()
        fake.query_hook = lambda *args: 0
        with patch("os.name", "nt"), patch("ctypes.WinDLL", return_value=fake.kernel, create=True), \
                patch("tools.probe_mini_recovery.discover_windows_rom_disks", return_value=[{"path": PATH}]), \
                patch("ctypes.get_last_error", return_value=31, create=True):
            with self.assertRaises(RomCommandError):
                aligned.WindowsAlignedRomTransport(PATH, slot=SLOT)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0]["ioctl"], aligned.IOCTL_STORAGE_QUERY_PROPERTY)
        fake.kernel.CloseHandle.assert_called_once_with(123)

    def test_wrong_inquiry_closes_identified_handle(self):
        fake = FakeKernel()
        def wrong(packet, returned):
            data = (c.c_uint8 * 36).from_address(packet.sptd.data_buffer)
            data[:] = bytes(8) + b"WRONG   " + b"UBOOT1.00       " + bytes(4)
            returned._obj.value = 88
            return 1
        fake.command_hook = wrong
        with patch("os.name", "nt"), patch("ctypes.WinDLL", return_value=fake.kernel, create=True), \
                patch("tools.probe_mini_recovery.discover_windows_rom_disks", return_value=[{"path": PATH}]):
            with self.assertRaisesRegex(ValueError, "INQUIRY"):
                aligned.WindowsAlignedRomTransport(PATH, slot=SLOT)
        fake.kernel.CloseHandle.assert_called_once_with(123)

    def test_cli_default_is_offline(self):
        result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/mini_windows_aligned.py")],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn('"device_io": false', result.stdout)
        self.assertIn('"alignment_causality_proven": false', result.stdout)

    def test_all_frozen_profile_imports_work_in_fresh_python(self):
        script = ("from tools.mini_windows_aligned import validate_profile_request, _PROFILE_VALIDATORS; "
                  "[validate_profile_request(bytes.fromhex('120000002400'),None,36,slot=0x1C20000,profile=p) "
                  "for p in _PROFILE_VALIDATORS]; print('all profiles accepted INQUIRY')")
        result = subprocess.run([sys.executable, "-X", "utf8", "-c", script], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        self.assertIn("all profiles", result.stdout)


if __name__ == "__main__":
    unittest.main()
