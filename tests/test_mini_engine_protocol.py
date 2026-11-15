"""Offline protocol separation, handshakes and bounded read lifecycle."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from probe_mini_engine import (MiniEngineSession, engine_selftest_cdb,
                               engine_read_cdb, validate_engine_request)
from probe_mini_recovery import RAM_SLOTS, validate_ram_request, validate_nor_request, sha
from tests.test_mini_recovery import FakeRom
from tests import test_mini_recovery as reference


class FakeEngine(FakeRom):
    def __init__(self):
        super().__init__()
        self.engine_answer = bytes.fromhex('fc62 000000e6 48594531 00000000 0001')

    def exchange(self, cdb, data_out=None, read_length=0):
        op = int.from_bytes(cdb[:2], 'big')
        if op in (0xFB06, 0xFD07, 0xFB08):
            return super().exchange(cdb, data_out, read_length)
        validate_engine_request(cdb, data_out, read_length, slot=self.slot)
        self.commands.append(op)
        assert self.running
        if op == 0xFC62:
            return self.engine_answer
        address, length = struct.unpack_from('>IH', cdb, 2)
        reply = bytes(self.memory[address-self.slot:address-self.slot+length])
        return reply[:-1] if self.short_read else reply


class EngineProtocolTests(unittest.TestCase):
    def test_windows_profile_dispatch_isolated_from_legacy_commands(self):
        import ctypes
        from probe_mini_recovery import WindowsRomTransport
        kernel = reference.WindowsTransportTests().fake_kernel()
        path = r'\\.\PhysicalDrive42'
        with patch('os.name', 'nt'), patch('ctypes.WinDLL', return_value=kernel, create=True), \
                patch('probe_mini_recovery.discover_windows_rom_disks', return_value=[{'path': path}]):
            with WindowsRomTransport(path, slot=RAM_SLOTS[0], profile='ram-engine') as transport:
                def exchange(_handle, _code, incoming, _size, _outgoing, _outsize, returned, _overlap):
                    sptd = incoming._obj.sptd
                    self.assertEqual(bytes(sptd.cdb), engine_selftest_cdb())
                    buffer = (ctypes.c_ubyte * 16).from_address(sptd.data_buffer)
                    buffer[:] = bytes.fromhex('fc62 000000e6 48594531 00000000 0001')
                    returned._obj.value = 88
                    return 1
                kernel.DeviceIoControl.side_effect = exchange
                self.assertEqual(transport.exchange(engine_selftest_cdb(), read_length=16)[6:10], b'HYE1')
                with self.assertRaises(ValueError):
                    transport.exchange(b'\xfc\x72' + b'\xff'*14, read_length=16)
                self.assertEqual(kernel.DeviceIoControl.call_count, 2)

    def test_profiles_do_not_accept_each_others_protocol(self):
        for cdb, length in ((engine_selftest_cdb(), 16), (engine_read_cdb(RAM_SLOTS[0], 128, slot=RAM_SLOTS[0]), 128)):
            validate_engine_request(cdb, None, length, slot=RAM_SLOTS[0])
            for validator in (validate_ram_request, validate_nor_request):
                with self.assertRaises(ValueError): validator(cdb, None, length, slot=RAM_SLOTS[0])
        for op in (0xFC60, 0xFD61, 0xFC70, 0xFC72, 0xFC73, 0xFD71, 0xFB01, 0xFB04):
            with self.assertRaises(ValueError):
                validate_engine_request(op.to_bytes(2, 'big') + b'\xff'*14, None, 16, slot=RAM_SLOTS[0])

    def test_bounds_direction_and_padding_rejected(self):
        slot = RAM_SLOTS[0]
        for address, length in ((slot-1, 1), (slot+32768, 1), (slot+32767, 2), (slot, 0), (slot, 4097)):
            with self.assertRaises(ValueError): engine_read_cdb(address, length, slot=slot)
        good = engine_read_cdb(slot, 128, slot=slot)
        for cdb, data, length in ((good, None, 127), (good, bytes(128), 0), (good[:-1]+b'\x00', None, 128),
                                  (engine_selftest_cdb(), None, 15)):
            with self.assertRaises(ValueError): validate_engine_request(cdb, data, length, slot=slot)

    def test_valid_engine_and_read_lifecycle(self):
        fake = FakeEngine()
        session = MiniEngineSession(fake, slot=fake.slot, known_free_slot=True)
        with self.assertRaises(ValueError): session.read(fake.slot, 128)
        payload = bytes(range(256)) * 18
        result = session.upload_and_start(payload, expected_sha256=sha(payload))
        self.assertEqual(result['engine_frames'], 230)
        self.assertEqual(session.read(fake.slot, len(payload)), payload)
        self.assertEqual(fake.commands.count(0xFB08), 1)
        self.assertEqual(fake.commands[-2:], [0xFD63, 0xFD63])
        self.assertNotIn(0xFC60, fake.commands)
        self.assertNotIn(0xFD61, fake.commands)

    def test_wrong_frames_status_magic_version_stop_after_one_jump(self):
        for offset, mask in ((5, 1), (10, 1), (6, 1), (15, 1)):
            fake = FakeEngine()
            answer = bytearray(fake.engine_answer)
            answer[offset] ^= mask
            fake.engine_answer = bytes(answer)
            session = MiniEngineSession(fake, slot=fake.slot, known_free_slot=True)
            with self.assertRaises(ValueError): session.upload_and_start(b'ABCD', expected_sha256=sha(b'ABCD'))
            with self.assertRaises(ValueError): session.read(fake.slot, 128)
            with self.assertRaises(ValueError): session.upload_and_start(b'ABCD', expected_sha256=sha(b'ABCD'))
            self.assertEqual(fake.commands.count(0xFB08), 1)

    def test_short_read_poisoning_does_not_retry(self):
        fake = FakeEngine()
        session = MiniEngineSession(fake, slot=fake.slot, known_free_slot=True)
        session.upload_and_start(b'ABCD', expected_sha256=sha(b'ABCD'))
        fake.short_read = True
        with self.assertRaises(ValueError): session.read(fake.slot, 128)
        with self.assertRaises(ValueError): session.read(fake.slot, 128)
        self.assertEqual(fake.commands.count(0xFD63), 1)
