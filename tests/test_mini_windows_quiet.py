"""Every native API is fake: no device, discovery, or Windows media query."""
import ctypes as c
from dataclasses import FrozenInstanceError, replace
import struct
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

from tools import mini_windows_quiet as q
from tools import mini_windows_spt as spt
from tools import probe_mini_recovery as recovery
from tools.probe_mini_app_writer import read_cdb


DISK = r"\\.\PhysicalDrive17"
CHAIN = (r"USBSTOR\DISK&VEN_WL82&PROD_UBOOT1.00\TEST&0",
         r"USB\VID_4C4A&PID_8057\TEST")
INTERFACE = r"\\?\USBSTOR#DISK&VEN_WL82&PROD_UBOOT1.00#TEST&0#{53f56307-b6bf-11d0-94f2-00a0c91efb8b}"
ARRIVAL = 134128224000000000
IDENTITY = bytes((0, 0x80)) + bytes(6) + b"WL82    " + b"UBOOT1.00       " + bytes(4)
SLOT = recovery.RAM_SLOTS[0]
DISCOVERY = {"path": DISK, "pnp_id": CHAIN[0], "usb_ancestor": CHAIN[-1],
             "chain": list(CHAIN), "model": "WL82 UBOOT1.00 USB Device"}
DESCRIPTOR = struct.pack("<5I4B2H4B", 32, 32, 65536, 17, 0, 0, 0, 0, 0,
                         7, 0, 0, 0, 0, 0)


def put32(ptr, value):
    c.cast(ptr, c.POINTER(c.c_uint32))[0] = value


class FakeCfg:
    def __init__(self):
        self.ids = list(CHAIN)
        self.states = [(q.DN_STARTED, 0)] * len(CHAIN)
        self.interface = INTERFACE + "\0\0"
        self.interface_size = None
        self.arrivals = [ARRIVAL]
        self.property_type, self.property_bytes = q.DEVPROP_TYPE_FILETIME, 8
        self.results, self.calls, self.property_reads = {}, [], 0
        names = ("CM_Locate_DevNodeW", "CM_Get_Parent", "CM_Get_Device_ID_Size", "CM_Get_Device_IDW",
                 "CM_Get_DevNode_Status", "CM_Get_Device_Interface_List_SizeW",
                 "CM_Get_Device_Interface_ListW", "CM_Get_DevNode_PropertyW")
        for name in names:
            setattr(self, name, MagicMock(side_effect=lambda *args, name=name: self.call(name, args)))

    def call(self, name, args):
        self.calls.append(name)
        if self.results.get(name):
            return self.results[name]
        if name == "CM_Locate_DevNodeW":
            output, instance, flags = args
            assert instance == CHAIN[0] and flags == 0
            put32(output, 100)
        elif name == "CM_Get_Parent":
            output, node, flags = args
            assert flags == 0
            put32(output, node + 1)
        elif name == "CM_Get_Device_ID_Size":
            output, node, flags = args
            assert flags == 0
            put32(output, len(self.ids[node - 100]))
        elif name == "CM_Get_Device_IDW":
            node, output, length, flags = args
            assert flags == 0 and length == len(self.ids[node - 100]) + 1
            output.value = self.ids[node - 100]
        elif name == "CM_Get_DevNode_Status":
            status, problem, node, flags = args
            assert flags == 0
            current = self.states[node - 100]
            put32(status, current[0])
            put32(problem, current[1])
        elif name == "CM_Get_DevNode_PropertyW":
            node, key_ptr, kind, output, length, flags = args
            key = c.cast(key_ptr, c.POINTER(q.DevPropKey)).contents
            assert bytes(key.fmtid) == UUID(q.ARRIVAL_PROPERTY_GUID).bytes_le
            assert key.pid == 102 and node == 101 and flags == 0
            assert c.cast(length, c.POINTER(c.c_uint32))[0] == 8
            arrival = self.arrivals[min(self.property_reads, len(self.arrivals) - 1)]
            self.property_reads += 1
            output[:] = arrival.to_bytes(8, "little")
            put32(kind, self.property_type)
            put32(length, self.property_bytes)
        elif name == "CM_Get_Device_Interface_List_SizeW":
            length, guid, instance, flags = args
            assert instance == CHAIN[0] and flags == 0
            assert bytes(c.cast(guid, c.POINTER(q.Guid)).contents) == UUID(q.DISK_INTERFACE_GUID).bytes_le
            put32(length, self.interface_size if self.interface_size is not None else len(self.interface))
        elif name == "CM_Get_Device_Interface_ListW":
            guid, instance, output, length, flags = args
            assert instance == CHAIN[0] and flags == 0
            assert length == len(self.interface)
            output[:] = self.interface
        else:
            raise AssertionError(name)
        return 0


class FakeKernel:
    def __init__(self):
        self.calls, self.cdbs = [], []
        self.number = (q.FILE_DEVICE_DISK, 17, 0)
        self.number_bytes = 12
        self.number_error = False
        self.inquiry = IDENTITY
        self.scsi_error = False
        self.CreateFileW = MagicMock(return_value=42)
        self.CloseHandle = MagicMock(return_value=True)
        self.DeviceIoControl = MagicMock(side_effect=self.ioctl)

    def ioctl(self, handle, code, source, source_size, output, output_size, returned, overlapped):
        assert handle == 42 and overlapped is None
        self.calls.append(code)
        if code == q.IOCTL_STORAGE_GET_DEVICE_NUMBER:
            assert source is None and source_size == 0 and output_size == 12
            c.memmove(output, struct.pack("<3I", *self.number), 12)
            put32(returned, self.number_bytes)
            return not self.number_error
        if code == 0x2D1400:
            assert source_size == 12 and output_size in (8, 32)
            assert bytes(c.cast(source, c.POINTER(c.c_ubyte * 12)).contents)[:8] == struct.pack("<2I", 1, 0)
            c.memmove(output, DESCRIPTOR[:output_size], output_size)
            put32(returned, output_size)
            return True
        assert code == spt.IOCTL_SCSI_PASS_THROUGH  # Never DIRECT/geometry/media IOCTL.
        at = c.cast(source, c.c_void_p).value
        assert at == c.cast(output, c.c_void_p).value and source_size == output_size
        packet = (c.c_ubyte * source_size).from_address(at)
        header = spt.ScsiPassThrough64.from_buffer(packet)
        command = bytes(header.cdb[:header.cdb_length])
        self.cdbs.append(command)
        if self.scsi_error:
            put32(returned, 0)
            return False
        start, size = header.data_buffer_offset, header.data_transfer_length
        data = self.inquiry if command == q.INQUIRY else bytes(i & 255 for i in range(size))
        assert len(data) == size
        packet[start:start + size] = data
        put32(returned, source_size)
        return True


class QuietTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.kernel = FakeCfg(), FakeKernel()
        self.attestation = q.RomDiskAttestation.from_discovery(DISCOVERY)
        self.contexts = [
            patch.object(q.os, "name", "nt"),
            patch.object(q.c, "WinDLL", side_effect=lambda name, **kw:
                {"cfgmgr32": self.cfg, "kernel32": self.kernel}[name], create=True),
            patch.object(q.c, "get_last_error", return_value=31, create=True),
            patch.object(recovery, "discover_windows_rom_disks", side_effect=AssertionError("discovery forbidden")),
            patch.object(recovery.WindowsRomTransport, "__init__", side_effect=AssertionError("parent constructor forbidden")),
            patch.object(spt.WindowsBufferedRomTransport, "__init__", side_effect=AssertionError("parent constructor forbidden")),
        ]
        for context in self.contexts:
            context.start()
            self.addCleanup(context.stop)

    def open(self, attestation=None, **kwargs):
        return q.QuietBufferedRomTransport(attestation or self.attestation, slot=SLOT, **kwargs)

    def test_attestation_is_offline_deeply_immutable_and_bounded(self):
        copied = dict(DISCOVERY, chain=list(CHAIN))
        att = q.RomDiskAttestation.from_discovery(copied)
        copied["chain"][0] = "changed"
        self.assertEqual(att.chain, CHAIN)
        with self.assertRaises(FrozenInstanceError):
            att.path = "changed"
        self.assertIsNone(att.interface_path)
        self.assertEqual(att.summary()["device_number"], 17)
        self.assertEqual(len(att.summary()["discovery_sha256"]), 64)
        self.assertEqual(self.cfg.calls, [])
        self.kernel.CreateFileW.assert_not_called()

    def test_reject_bad_attestations_before_any_api(self):
        changes = [{"path": r"\\.\PhysicalDrive4294967296"}, {"path": "C:"},
                   {"pnp_id": "other"}, {"chain": [*CHAIN, CHAIN[-1]]},
                   {"chain": "not a list"}, {"usb_ancestor": "USB\\VID_0000&PID_0000\\X"},
                   {"model": "bad\0model"}, {"chain": ["X" * 200, CHAIN[-1]]}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                q.RomDiskAttestation.from_discovery(dict(DISCOVERY, **change))
        with self.assertRaises(ValueError):
            replace(self.attestation, interface_path=INTERFACE)
        self.assertEqual(self.cfg.calls, [])

    def test_constructor_inherits_exchange_and_opens_exact_interface(self):
        self.assertIs(q.QuietBufferedRomTransport.exchange, spt.WindowsBufferedRomTransport.exchange)
        self.assertIs(q.QuietBufferedRomTransport._exchange_once, spt.WindowsBufferedRomTransport._exchange_once)
        self.assertIs(q.QuietBufferedRomTransport.close, recovery.WindowsRomTransport.close)
        transport = self.open()
        self.kernel.CreateFileW.assert_called_once_with(INTERFACE, 0xC0000000, 3, None, 3, 0, None)
        self.assertEqual(self.kernel.calls, [0x2D1080, 0x2D1400, 0x2D1400, 0x4D004])
        self.assertEqual(self.kernel.cdbs, [q.INQUIRY])
        self.assertEqual(self.cfg.property_reads, 2)
        self.assertEqual(transport.disk["path"], DISK)
        self.assertEqual(transport.opened_interface, INTERFACE)
        self.assertEqual(transport.device_number, 17)
        self.assertEqual(transport.attestation.last_arrival_filetime, ARRIVAL)
        self.assertEqual(transport.open_metadata["win32_diskdrive_queries"], 0)
        transport.close()
        transport.close()
        self.kernel.CloseHandle.assert_called_once_with(42)

    def test_profile_slot_validated_before_native_apis(self):
        for slot, profile in [(0, "ram-probe"), (SLOT, "unknown")]:
            with self.subTest(slot=slot, profile=profile), self.assertRaises(ValueError):
                q.QuietBufferedRomTransport(self.attestation, slot=slot, profile=profile)
        self.assertEqual(self.cfg.calls, [])
        self.kernel.CreateFileW.assert_not_called()

    def test_bound_attestation_reopens_same_enumeration(self):
        initial = self.open()
        att = initial.attestation
        initial.close()
        with self.open(att) as reopened:
            self.assertEqual(reopened.attestation, att)
            self.assertEqual(type(reopened), type(initial))
        self.assertEqual(len(self.kernel.cdbs), 2)

    def test_changed_arrival_rejected_before_open(self):
        bound = replace(self.attestation, interface_path=INTERFACE, last_arrival_filetime=ARRIVAL - 1)
        with self.assertRaisesRegex(ValueError, "arrival changed"):
            self.open(bound)
        self.kernel.CreateFileW.assert_not_called()

    def test_changed_interface_rejected_before_open(self):
        bound = replace(self.attestation, interface_path=INTERFACE + "other", last_arrival_filetime=ARRIVAL)
        with self.assertRaisesRegex(ValueError, "arrival changed"):
            self.open(bound)
        self.kernel.CreateFileW.assert_not_called()

    def test_removal_during_inquiry_closes_handle(self):
        self.cfg.arrivals = [ARRIVAL, ARRIVAL + 100]
        with self.assertRaisesRegex(ValueError, "arrival changed"):
            self.open()
        self.assertEqual(self.kernel.cdbs, [q.INQUIRY])
        self.kernel.CloseHandle.assert_called_once_with(42)

    def test_absent_devnode_and_api_errors_never_fallback(self):
        for name in ("CM_Locate_DevNodeW", "CM_Get_Parent", "CM_Get_Device_IDW",
                     "CM_Get_DevNode_PropertyW", "CM_Get_Device_Interface_ListW"):
            with self.subTest(name=name):
                self.cfg.results = {name: 13}
                with self.assertRaises(OSError):
                    self.open()
        self.kernel.CreateFileW.assert_not_called()
        self.assertEqual(self.kernel.cdbs, [])

    def test_unstarted_or_problem_nodes_rejected(self):
        for state in ((0, 0), (q.DN_STARTED | q.DN_HAS_PROBLEM, 0), (q.DN_STARTED, 10)):
            with self.subTest(state=state):
                self.cfg.states = [state, (q.DN_STARTED, 0)]
                with self.assertRaisesRegex(ValueError, "not started"):
                    self.open()
        self.kernel.CreateFileW.assert_not_called()

    def test_changed_parent_rejected(self):
        self.cfg.ids[1] = r"USB\VID_4C4A&PID_8057\OTHER"
        with self.assertRaisesRegex(ValueError, "ancestry differs"):
            self.open()
        self.kernel.CreateFileW.assert_not_called()

    def test_interface_bounds_ambiguity_and_termination_rejected(self):
        for text in ("\0\0", INTERFACE + "\0" + INTERFACE + "\0\0",
                     INTERFACE + "\0X", "bad\0\0"):
            with self.subTest(text=text):
                self.cfg.interface = text
                with self.assertRaises(ValueError):
                    self.open()
        self.cfg.interface_size = 8193
        with self.assertRaisesRegex(ValueError, "exceeds bound"):
            self.open()
        self.kernel.CreateFileW.assert_not_called()

    def test_invalid_arrival_property_rejected(self):
        for kind, length, arrival in ((0, 8, ARRIVAL), (16, 7, ARRIVAL), (16, 8, 0)):
            with self.subTest(kind=kind, length=length, arrival=arrival):
                self.cfg.property_type, self.cfg.property_bytes = kind, length
                self.cfg.arrivals = [arrival]
                with self.assertRaisesRegex(ValueError, "FILETIME"):
                    self.open()
        self.kernel.CreateFileW.assert_not_called()

    def test_failed_createfile_no_inquiry_or_close_of_invalid_handle(self):
        self.kernel.CreateFileW.return_value = c.c_void_p(-1).value
        with self.assertRaises(OSError):
            self.open()
        self.assertEqual(self.kernel.cdbs, [])
        self.kernel.CloseHandle.assert_not_called()

    def test_device_number_mismatch_or_partition_closes_before_inquiry(self):
        for number in ((7, 18, 0), (8, 17, 0), (7, 17, 1)):
            with self.subTest(number=number):
                self.kernel.number = number
                with self.assertRaisesRegex(ValueError, "PhysicalDrive"):
                    self.open()
        self.assertEqual(self.kernel.cdbs, [])
        self.assertEqual(self.kernel.CloseHandle.call_count, 3)

    def test_short_or_failed_device_number_query_closes(self):
        self.kernel.number_bytes = 8
        with self.assertRaises(ValueError):
            self.open()
        self.kernel.number_bytes, self.kernel.number_error = 12, True
        with self.assertRaises(OSError):
            self.open()
        self.assertEqual(self.kernel.cdbs, [])
        self.assertEqual(self.kernel.CloseHandle.call_count, 2)

    def test_wrong_inquiry_closes_handle(self):
        self.kernel.inquiry = bytes(36)
        with self.assertRaisesRegex(ValueError, "INQUIRY"):
            self.open()
        self.kernel.CloseHandle.assert_called_once_with(42)

    def test_inquiry_error_no_retry(self):
        self.kernel.scsi_error = True
        with self.assertRaises(recovery.RomCommandError) as context:
            self.open()
        self.assertTrue(context.exception.submitted)
        self.assertEqual(self.kernel.cdbs, [q.INQUIRY])
        self.kernel.CloseHandle.assert_called_once_with(42)

    def test_inherited_profile_rejects_program_without_native_io(self):
        with self.open(profile="nor-reader") as transport:
            before = list(self.kernel.calls)
            with self.assertRaises(ValueError):
                transport.exchange(b"\xfc\x7d" + bytes(14), read_length=16)
            self.assertEqual(self.kernel.calls, before)

    def test_operational_read_uses_frozen_buffered_backend_without_new_pnp_queries(self):
        with self.open(profile="app-writer-operational") as transport:
            before = list(self.cfg.calls)
            result = transport.exchange(read_cdb(0x5000, 256), read_length=256)
            self.assertEqual(result, bytes(range(256)))
            self.assertEqual(self.cfg.calls, before)
            self.assertEqual(self.kernel.calls[-1], 0x4D004)
            self.assertEqual(self.kernel.cdbs, [q.INQUIRY, read_cdb(0x5000, 256)])


if __name__ == "__main__":
    unittest.main()
