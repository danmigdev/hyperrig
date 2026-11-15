"""Buffered SCSI contract tests. Every Windows API is fake; no device I/O."""
import ctypes as c
import struct
import threading
import unittest
from unittest.mock import MagicMock, patch

from tools import mini_windows_spt as spt
from tools import probe_mini_recovery as recovery
from tools.probe_mini_app_writer import read_cdb, stage_cdb, stage_packet


INQUIRY = bytes((0x12, 0, 0, 0, 36, 0))
DISK = r"\\.\PhysicalDrive17"
SLOT = recovery.RAM_SLOTS[0]
DESCRIPTOR = {"alignment_mask": 0, "maximum_transfer_length": 65536,
              "maximum_physical_pages": 17, "bus_type": 7, "version": 32, "size": 32}
IDENTITY = bytes(8) + b"WL82    " + b"UBOOT1.00       " + bytes(4)


class FakeKernel:
    def __init__(self):
        self.requests = []
        self.mode = "ok"
        self.inquiry = IDENTITY
        self.CreateFileW = MagicMock(return_value=42)
        self.CloseHandle = MagicMock(return_value=True)
        self.DeviceIoControl = MagicMock(side_effect=self.ioctl)

    def ioctl(self, handle, code, source, source_size, output, output_size, returned, overlapped):
        assert code == spt.IOCTL_SCSI_PASS_THROUGH  # Never DIRECT.
        assert handle == 42 and overlapped is None
        at = c.cast(source, c.c_void_p).value
        assert at == c.cast(output, c.c_void_p).value and source_size == output_size
        packet = (c.c_ubyte * source_size).from_address(at)
        header = spt.ScsiPassThrough64.from_buffer(packet)
        cdb = bytes(header.cdb[:header.cdb_length])
        start, size = header.data_buffer_offset, header.data_transfer_length
        assert start >= 88 and start + size == source_size
        self.requests.append({"code": code, "cdb": cdb, "length": size,
                              "data_in": header.data_in, "data_offset": start,
                              "packet_bytes": source_size,
                              "data": bytes(packet[start:start+size])})
        result_count = c.cast(returned, c.POINTER(c.c_uint32))
        if self.mode == "win31":
            result_count[0] = 0
            return False
        if header.data_in:
            data = self.inquiry if cdb == INQUIRY else bytes(i & 255 for i in range(size))
            assert len(data) == size
            packet[start:start+size] = data
            result_count[0] = source_size
        else:
            result_count[0] = 56  # Valid OUT reply need not echo the data.
        if self.mode == "short":
            header.data_transfer_length -= 1
        elif self.mode == "short_packet":
            result_count[0] -= 1
        elif self.mode == "sense":
            header.scsi_status, header.sense_info_length = 2, 4
            packet[56:60] = b"\x70\0\x05\0"
        elif self.mode == "offset":
            header.data_buffer_offset = 0xFFFFFFFFFFFFFFFF
        return True


def fake_transport(kernel=None, profile="ram-probe", with_descriptor=True):
    transport = spt.WindowsBufferedRomTransport.__new__(spt.WindowsBufferedRomTransport)
    transport.slot, transport.profile = SLOT, profile
    transport._handle, transport._kernel, transport._c = 42, kernel or FakeKernel(), c
    transport.adapter_descriptor, transport.last_transfer, transport.failed = None, None, False
    transport._exchange_lock = threading.Lock()
    if with_descriptor:
        transport.adapter_descriptor = dict(DESCRIPTOR)
    return transport


class PacketTests(unittest.TestCase):
    def packet(self, out=None, size=256, mask=0):
        return spt.build_buffered_packet(read_cdb(0x5000, size), out, 0 if out is not None else size,
                                         alignment_mask=mask, maximum_transfer_length=65536)

    def test_native_layout_matches_independent_header_offsets(self):
        packet = self.packet()
        expected = bytearray(56)
        struct.pack_into("<H", expected, 0, 56)
        expected[4], expected[6], expected[7], expected[8] = 1, 16, 32, 1
        struct.pack_into("<II", expected, 12, 256, 10)
        struct.pack_into("<Q", expected, 24, 88)
        struct.pack_into("<I", expected, 32, 56)
        expected[36:52] = read_cdb(0x5000, 256)
        self.assertEqual(c.sizeof(spt.ScsiPassThrough64), 56)
        self.assertEqual(bytes(packet.buffer[:56]), expected)
        self.assertEqual(bytes(packet.buffer[56:]), bytes(32 + 256))
        self.assertEqual(packet.total_length, 344)

    def test_offsets_are_relative_aligned_nonoverlapping_bounded(self):
        for mask in (0, 1, 3, 7, 15, 511, 4095):
            with self.subTest(mask=mask):
                packet = spt.build_buffered_packet(INQUIRY, None, 4096,
                    alignment_mask=mask, maximum_transfer_length=65536)
                self.assertEqual(packet.data_offset & mask, 0)
                self.assertGreaterEqual(packet.data_offset, 88)
                self.assertLessEqual(packet.total_length, 8192)
                self.assertLess(packet.header.data_buffer_offset, 8192)

    def test_out_payload_exact_no_block_padding(self):
        payload = bytes(range(256)) + b"CRC!"
        packet = self.packet(out=payload)
        self.assertEqual(packet.data_in, 0)
        self.assertEqual(packet.data_length, 260)
        self.assertEqual(bytes(packet.buffer[packet.data_offset:]), payload)
        self.assertEqual(spt.parse_buffered_response(packet, 56), b"")

    def test_invalid_packet_input_rejected(self):
        examples = [(b"", None, 1, 0, 65536), (bytes(17), None, 1, 0, 65536),
                    (INQUIRY, b"x", 1, 0, 65536), (INQUIRY, None, 0, 0, 65536),
                    (INQUIRY, None, -1, 0, 65536), (INQUIRY, None, 4097, 0, 65536),
                    (INQUIRY, None, 256, 0, 255), (INQUIRY, None, 1, 2, 65536),
                    (INQUIRY, None, 1, 4096, 65536), (INQUIRY, None, True, 0, 65536)]
        for cdb, out, size, mask, maximum in examples:
            with self.subTest(cdb=cdb, size=size, mask=mask, maximum=maximum):
                with self.assertRaises(ValueError):
                    spt.build_buffered_packet(cdb, out, size,
                        alignment_mask=mask, maximum_transfer_length=maximum)

    def test_in_payload_requires_returned_bytes_covering_data(self):
        packet = self.packet()
        payload = bytes(range(256))
        packet.buffer[packet.data_offset:] = payload
        self.assertEqual(spt.parse_buffered_response(packet, packet.total_length), payload)
        for returned in (0, 55, packet.total_length-1, packet.total_length+1):
            with self.subTest(returned=returned):
                with self.assertRaises(recovery.RomCommandError):
                    spt.parse_buffered_response(packet, returned)

    def test_untrusted_response_offsets_and_layout_never_followed(self):
        changes = {"length": 55, "data_buffer_offset": 2**64-1,
                   "sense_info_offset": 2**32-1, "sense_info_length": 33,
                   "cdb_length": 255, "data_in": 0}
        for field, value in changes.items():
            with self.subTest(field=field):
                packet = self.packet()
                setattr(packet.header, field, value)
                with self.assertRaisesRegex(recovery.RomCommandError, "altered packet layout"):
                    spt.parse_buffered_response(packet, packet.total_length)
        packet = self.packet()
        packet.header.cdb[0] ^= 1
        with self.assertRaises(recovery.RomCommandError):
            spt.parse_buffered_response(packet, packet.total_length)

    def test_sense_is_bounded_by_returned_bytes(self):
        packet = self.packet()
        packet.header.scsi_status = 2
        packet.buffer[56:60] = b"\x70\0\x05\0"
        with self.assertRaises(recovery.RomCommandError) as caught:
            spt.parse_buffered_response(packet, 60)
        self.assertEqual(caught.exception.details["sense_hex"], "70000500")
        self.assertEqual(caught.exception.details["sense_bytes_returned"], 4)

    def test_short_and_oversize_transfer_rejected(self):
        for length in (0, 255, 257, 2**32-1):
            with self.subTest(length=length):
                packet = self.packet()
                packet.header.data_transfer_length = length
                with self.assertRaisesRegex(recovery.RomCommandError, "short/invalid"):
                    spt.parse_buffered_response(packet, packet.total_length)


class TransportTests(unittest.TestCase):
    def test_fd7f_256_and_hyrn_256_are_unchanged(self):
        for profile, cdb in [("app-writer-observer", read_cdb(0x5000,256)),
                             ("app-writer-operational", read_cdb(0x5000,256)),
                             ("nor-reader", recovery.nor_read_cdb(0x5000,256))]:
            with self.subTest(profile=profile):
                transport = fake_transport(profile=profile)
                self.assertEqual(transport.exchange(cdb, read_length=256), bytes(range(256)))
                request = transport._kernel.requests[0]
                self.assertEqual((request["cdb"],request["length"],request["data_in"]), (cdb,256,1))
                self.assertEqual(transport._kernel.DeviceIoControl.call_count, 1)
                self.assertEqual(transport.last_transfer["backend"], "spt-buffered")
                self.assertGreaterEqual(transport.last_transfer["finished_monotonic_ns"],
                                        transport.last_transfer["started_monotonic_ns"])

    def test_out_upload512_and_stage260_keep_original_wire_bytes(self):
        upload = bytes(i & 255 for i in range(512))
        stage = stage_packet(bytes(range(256)))
        cases = [("ram-probe", recovery.ram_write_cdb(SLOT, upload, slot=SLOT), upload),
                 ("app-writer-observer", stage_cdb(1,2,0x5000), stage)]
        for profile, cdb, payload in cases:
            with self.subTest(profile=profile):
                transport = fake_transport(profile=profile)
                self.assertEqual(transport.exchange(cdb, data_out=payload), b"")
                request = transport._kernel.requests[0]
                self.assertEqual((request["data"],request["length"],request["data_in"]),
                                 (payload,len(payload),0))

    def test_invalid_profile_commands_have_no_io_or_adapter_query(self):
        transport = fake_transport(with_descriptor=False)
        bad = [(bytes(16),None,16), (read_cdb(0x5000,256),None,256),
               (recovery.rom_read_cdb(SLOT,16,slot=SLOT),b"x",16)]
        with patch.object(spt,"query_adapter_descriptor") as query:
            for cdb, out, count in bad:
                with self.assertRaises(ValueError):
                    transport.exchange(cdb,data_out=out,read_length=count)
            transport.profile = "unknown"
            with self.assertRaises(ValueError):
                transport.exchange(INQUIRY,read_length=36)
            query.assert_not_called()
        self.assertEqual(transport._kernel.DeviceIoControl.call_count, 0)

    def test_adapter_query_once_and_adapter_limit_enforced(self):
        transport = fake_transport(with_descriptor=False)
        with patch.object(spt,"query_adapter_descriptor",return_value=dict(DESCRIPTOR)) as query:
            self.assertEqual(transport.exchange(INQUIRY,read_length=36), IDENTITY)
            transport.exchange(INQUIRY,read_length=36)
            query.assert_called_once_with(transport._kernel,42,c=c)
        transport.adapter_descriptor["maximum_transfer_length"] = 35
        with self.assertRaises(ValueError): transport.exchange(INQUIRY,read_length=36)
        self.assertEqual(transport._kernel.DeviceIoControl.call_count, 2)

    def test_submitted_error_is_terminal_with_no_retry_or_fallback(self):
        for mode in ("win31","short","short_packet","sense","offset"):
            with self.subTest(mode=mode):
                kernel = FakeKernel(); kernel.mode = mode
                transport = fake_transport(kernel)
                with patch.object(c,"get_last_error",return_value=31,create=True):
                    with self.assertRaises(recovery.RomCommandError) as caught:
                        transport.exchange(INQUIRY,read_length=36)
                self.assertTrue(caught.exception.submitted)
                self.assertEqual(caught.exception.details["transport"],"spt-buffered")
                if mode == "win31": self.assertEqual(caught.exception.errno,31)
                with self.assertRaises(recovery.RomCommandError) as again:
                    transport.exchange(INQUIRY,read_length=36)
                self.assertFalse(again.exception.submitted)
                self.assertEqual(kernel.DeviceIoControl.call_count,1)

    def test_closed_handle_has_no_io(self):
        transport = fake_transport()
        transport.close(); transport.close()
        with self.assertRaises(OSError): transport.exchange(INQUIRY,read_length=36)
        transport._kernel.CloseHandle.assert_called_once_with(42)
        transport._kernel.DeviceIoControl.assert_not_called()

    def test_concurrent_exchange_rejected_without_io(self):
        transport = fake_transport()
        transport._exchange_lock.acquire()
        try:
            with self.assertRaises(RuntimeError): transport.exchange(INQUIRY,read_length=36)
        finally:
            transport._exchange_lock.release()
        transport._kernel.DeviceIoControl.assert_not_called()

    def test_failed_adapter_query_prevents_scsi_and_poisons_handle(self):
        transport = fake_transport(with_descriptor=False)
        failure = recovery.RomCommandError(31,"fake query failed",submitted=False)
        with patch.object(spt,"query_adapter_descriptor",side_effect=failure) as query:
            with self.assertRaises(recovery.RomCommandError) as caught:
                transport.exchange(INQUIRY,read_length=36)
            self.assertFalse(caught.exception.submitted)
            with self.assertRaises(recovery.RomCommandError):
                transport.exchange(INQUIRY,read_length=36)
            query.assert_called_once()
        transport._kernel.DeviceIoControl.assert_not_called()

    def test_inherited_constructor_keeps_ancestry_and_inquiry_identity(self):
        kernel = FakeKernel()
        disk = {"path": DISK, "usb_ancestor": r"USB\VID_4C4A&PID_8057\fake"}
        with patch.object(recovery,"discover_windows_rom_disks",return_value=[disk]) as discover, \
             patch.object(c,"WinDLL",return_value=kernel,create=True), \
             patch.object(spt,"query_adapter_descriptor",return_value=dict(DESCRIPTOR)), \
             patch("os.name","nt"):
            transport = spt.WindowsBufferedRomTransport(DISK,slot=SLOT,profile="nor-reader")
            self.assertEqual(transport.inquiry["vendor"],"WL82")
            self.assertEqual(transport.inquiry["product"],"UBOOT1.00")
            discover.assert_called_once()
            self.assertEqual(kernel.requests[0]["cdb"],INQUIRY)
            self.assertEqual(len(kernel.requests),1)
            transport.close()

    def test_wrong_ancestry_never_opens_and_wrong_inquiry_closes(self):
        kernel = FakeKernel()
        with patch.object(recovery,"discover_windows_rom_disks",return_value=[]), \
             patch.object(c,"WinDLL",return_value=kernel,create=True), patch("os.name","nt"):
            with self.assertRaises(ValueError):
                spt.WindowsBufferedRomTransport(DISK,slot=SLOT)
            kernel.CreateFileW.assert_not_called()
        kernel.inquiry = bytes(36)
        with patch.object(recovery,"discover_windows_rom_disks",return_value=[{"path":DISK}]), \
             patch.object(c,"WinDLL",return_value=kernel,create=True), \
             patch.object(spt,"query_adapter_descriptor",return_value=dict(DESCRIPTOR)), \
             patch("os.name","nt"):
            with self.assertRaisesRegex(ValueError,"unexpected disk INQUIRY"):
                spt.WindowsBufferedRomTransport(DISK,slot=SLOT)
        kernel.CloseHandle.assert_called_once_with(42)


if __name__ == "__main__":
    unittest.main()
