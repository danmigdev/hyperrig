"""HYC1 allowlist, exact record validation and no-retry lifecycle; no hardware."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from probe_mini_codec import (MiniCodecSession, REGISTERS, codec_identity_cdb, codec_record_cdb,
                              codec_read_cdb, validate_codec_request, validate_codec_record)
from probe_mini_recovery import RAM_SLOTS, validate_ram_request, validate_nor_request, sha
from probe_mini_engine import validate_engine_request
from tests.test_mini_recovery import FakeRom
from tests import test_mini_recovery as reference

TAG = 0x12345678


def record(sequence=1, register=0x58, status=0):
    words = [0] * 32
    words[1:8] = [1, RAM_SLOTS[0], TAG, sequence, register, status & 0xffffffff,
                  0x40 if status == 0 else 0xffff]
    words[8:14] = [4, 2, 20, 1, 0, 1] if status == 0 else [0, 0, 1, 1, 0, 1]
    words[16:21] = words[21:26] = [0x7654fedc, 0x11223344, 0xaabbccdd, 0x91abcdef, 0xfedcba98]
    words[26:30] = [193 if status == 0 else 33, status & 0xffffffff, 160, 1]
    data = bytearray(struct.pack('<32I', *words))
    data[:4] = b'HYC1'; data[124:] = b'DONE'
    struct.pack_into('<I', data, 120, zlib.crc32(data[:120]))
    return bytes(data)


class FakeCodec(FakeRom):
    def __init__(self):
        super().__init__()
        self.sequence, self.status, self.bad_reply, self.bad_record = 0, 0, False, False

    def exchange(self, cdb, data_out=None, read_length=0):
        op = int.from_bytes(cdb[:2], 'big')
        if op in (0xfb06, 0xfd07, 0xfb08):
            return super().exchange(cdb, data_out, read_length)
        validate_codec_request(cdb, data_out, read_length, slot=self.slot)
        self.commands.append(op)
        assert self.running
        if op == 0xfc64:
            return b'\xfc\x64HYC1\x01\x00' + struct.pack('>II', self.slot, 32768)
        if op == 0xfc65:
            self.sequence += 1
            self.register = int.from_bytes(cdb[2:4], 'big')
            reply = b'\xfc\x65HYC1' + struct.pack('>HiH', self.sequence, self.status, self.register) + b'\x00\x01'
            return reply[:-1] if self.bad_reply else reply
        data = record(self.sequence, self.register, self.status)
        return data[:-1] if self.bad_record else data


class CodecProtocolTests(unittest.TestCase):
    def session(self):
        fake = FakeCodec()
        session = MiniCodecSession(fake, slot=fake.slot, build_tag=TAG, known_free_slot=True)
        session.upload_and_start(b'ABCD', expected_sha256=sha(b'ABCD'))
        return fake, session

    def test_all_registers_are_bounded_and_other_profiles_reject_commands(self):
        valid = [(codec_identity_cdb(), 16), (codec_record_cdb(), 128)]
        valid += [(codec_read_cdb(r), 16) for r in REGISTERS]
        for command, length in valid:
            validate_codec_request(command, None, length, slot=RAM_SLOTS[0])
            for other in (validate_ram_request, validate_nor_request, validate_engine_request):
                with self.assertRaises(ValueError): other(command, None, length, slot=RAM_SLOTS[0])
        for r in (-1, 0, 2, 0x66, 0x10000, True, '0x58'):
            with self.assertRaises(ValueError): codec_read_cdb(r)
        for op in (0xfc60, 0xfc62, 0xfc70, 0xfc72, 0xfd61, 0xfd63, 0xfd71, 0xfb01, 0xfb04):
            with self.assertRaises(ValueError):
                validate_codec_request(op.to_bytes(2, 'big') + b'\xff'*14, None, 16, slot=RAM_SLOTS[0])

    def test_malformed_requests_are_rejected(self):
        command = codec_read_cdb(0x58)
        for cdb, data, length, slot in ((command[:-1], None, 16, RAM_SLOTS[0]),
                (command[:-1] + b'\x00', None, 16, RAM_SLOTS[0]), (command, None, 128, RAM_SLOTS[0]),
                (command, b'1234', 0, RAM_SLOTS[0]), (command, None, 16, 0),
                (codec_record_cdb(), None, 127, RAM_SLOTS[0])):
            with self.assertRaises(ValueError): validate_codec_request(cdb, data, length, slot=slot)

    def test_record_all_fields_reject_corruption_even_with_recomputed_crc(self):
        original = record()
        for offset in (4, 8, 12, 16, 20, 24, 32, 36, 40, 44, 48, 52, 104, 108, 116):
            changed = bytearray(original)
            changed[offset] ^= 1
            struct.pack_into('<I', changed, 120, zlib.crc32(changed[:120]))
            with self.assertRaises(ValueError):
                validate_codec_record(changed, base=RAM_SLOTS[0], build_tag=TAG, sequence=1, register=0x58)
        for offset, value in ((28, 65536), (112, 0), (112, 4097), (84, 0)):
            changed = bytearray(original)
            struct.pack_into('<I', changed, offset, value)
            struct.pack_into('<I', changed, 120, zlib.crc32(changed[:120]))
            with self.assertRaises(ValueError):
                validate_codec_record(changed, base=RAM_SLOTS[0], build_tag=TAG, sequence=1, register=0x58)

    def test_success_and_nack_do_not_retry_and_preserve_gpio(self):
        fake, session = self.session()
        self.assertEqual(session.read_register(0x58)['value'], 0x40)
        fake.status = -2
        result = session.read_register(0x59)
        self.assertIsNone(result['value'])
        self.assertTrue(result['nack_is_not_codec_absence'])
        self.assertTrue(result['gpio_restored'])
        self.assertEqual(fake.commands.count(0xfc65), 2)
        self.assertEqual(fake.commands.count(0xfb08), 1)
        with self.assertRaises(ValueError): session.read(fake.slot, 128)

    def test_failed_or_stale_transfer_poisoning(self):
        for attribute in ('bad_reply', 'bad_record'):
            fake, session = self.session()
            setattr(fake, attribute, True)
            with self.assertRaises(ValueError): session.read_register(0x58)
            with self.assertRaises(ValueError): session.read_register(0x58)
            self.assertEqual(fake.commands.count(0xfc65), 1)
        fake, session = self.session()
        fake.sequence = 4
        with self.assertRaises(ValueError): session.read_register(0x58)
        self.assertTrue(session.failed)

    def test_windows_codec_dispatch_with_mocked_native_api(self):
        import ctypes
        from probe_mini_recovery import WindowsRomTransport
        kernel = reference.WindowsTransportTests().fake_kernel()
        path = r'\\.\PhysicalDrive42'
        with patch('os.name', 'nt'), patch('ctypes.WinDLL', return_value=kernel, create=True), \
                patch('probe_mini_recovery.discover_windows_rom_disks', return_value=[{'path': path}]):
            with WindowsRomTransport(path, slot=RAM_SLOTS[0], profile='ram-codec') as transport:
                def exchange(_handle, _code, incoming, _size, _outgoing, _outsize, returned, _overlap):
                    sptd = incoming._obj.sptd
                    self.assertEqual(bytes(sptd.cdb), codec_identity_cdb())
                    data = b'\xfc\x64HYC1\x01\x00' + struct.pack('>II', RAM_SLOTS[0], 32768)
                    (ctypes.c_ubyte * 16).from_address(sptd.data_buffer)[:] = data
                    returned._obj.value = 88
                    return 1
                kernel.DeviceIoControl.side_effect = exchange
                self.assertEqual(transport.exchange(codec_identity_cdb(), read_length=16)[2:6], b'HYC1')
                with self.assertRaises(ValueError): transport.exchange(b'\xfc\x72' + b'\xff'*14, read_length=16)
                self.assertEqual(kernel.DeviceIoControl.call_count, 2)
