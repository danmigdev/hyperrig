"""HYC3 exact protocol and staged lifecycle tests, exclusively mocked hardware."""
import contextlib
import io
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from tools import probe_mini_codec_rom as rom
from tools import probe_mini_recovery as recovery
from probe_mini_codec import validate_codec_request
from tools.probe_mini_codec_board import validate_codec_board_request
from probe_mini_engine import validate_engine_request
from tests.test_mini_recovery import FakeRom

TAG = 0x12345678
SLOT = recovery.RAM_SLOTS[0]


def record(*, sequence=1, phase=0, register=0xffff, slot=SLOT, mode='success', blocked=False):
    """Independent fixed record fixture for the recorded ROM48MHz tuple."""
    first = [0,0x1c1,0x10000,0x80,0x0940022b,0x3f5030ee,0,0,0,0,0x01580034,1,0,0,0,0,0]
    if blocked: first[1] = 0
    if mode == 'setup-with-unapproved': first[2] ^= 1
    last = first[:]
    if mode == 'clock-change': last[2] ^= 1
    gate,hz,scale = (4,0,0) if blocked else (0,48000000,12)
    if mode == 'clock-change': gate = 6
    setup = 7 if phase else 0
    if phase and mode == 'not-armed': setup, gate = 0, 7
    words = [0]*128
    def put(offset, value): words[offset//4] = value & 0xffffffff
    for offset,value in [(4,3),(8,slot),(12,TAG),(16,sequence),(20,phase),(24,register),
                         (32,gate),(36,hz),(40,(first[1]>>6)&7),(44,first[3]&15),(48,scale),
                         (52,first[10]&1),(60,setup),(64,-4),(68,65535),(96,int(first[:12]==last[:12])),
                         (100,160),(104,1),(396,sequence-1 if phase else 0)]: put(offset,value)
    words[28:45], words[45:62] = first,last
    status = -8 if gate == 6 else -3 if gate else 0
    if setup:
        a = [0x7654fedc,0x11223344,0xaabbccdd,0x91abcdef,0xfedcba98,0x12345678,0,0,0]
        c = [0x13579bdf,0x2468ace0,0x12345678,0x76543210,0,0,0x44556677,0x8899aabb,0]
        words[62:71] = a; words[71:80] = a
        words[80:89] = c; words[89:98] = c
        for offset,value in [(56,193),(64,0),(68,0x40),(72,4),(76,2),(80,20),(84,1),(88,0),
                             (92,3),(108,100000+690*scale),(392,100000)]: put(offset,value)
        if mode == 'nack':
            status = -2
            for offset,value in [(56,35),(64,-2),(68,65535),(72,0),(76,0),(80,1),(108,100000+135*scale)]: put(offset,value)
        if mode == 'restore-fault':
            words[71] ^= 2
            put(92,2); status = -6
    if mode == 'guards': put(104,0); status = -7
    put(28,status)
    raw = bytearray(struct.pack('<128I',*words))
    raw[:4], raw[508:] = b'HYC3',b'DONE'
    struct.pack_into('<I',raw,504,zlib.crc32(raw[:504]))
    return bytes(raw)


class FakeCodecRom(FakeRom):
    def __init__(self, slot=SLOT):
        super().__init__(slot)
        self.sequence, self.phase = 0, None
        self.blocked, self.mode = False, 'success'
        self.fail_opcode = None
        self.reply_mutator = self.record_mutator = None
        self.before_read = None
        self.record = None

    def exchange(self, cdb, data_out=None, read_length=0):
        opcode = int.from_bytes(cdb[:2],'big')
        if opcode in (0xfb06,0xfd07,0xfb08):
            return super().exchange(cdb,data_out,read_length)
        rom.validate_codec_rom_request(cdb,data_out,read_length,slot=self.slot)
        self.commands.append(opcode)
        assert self.running
        if opcode == self.fail_opcode: raise OSError('simulated ambiguous HYC3 transfer')
        if opcode == 0xfd6d:
            return self.record_mutator(self.record) if self.record_mutator else self.record
        if opcode == 0xfc6c:
            assert self.phase == 0 and int.from_bytes(cdb[4:6],'big') == self.sequence
            if self.before_read: self.before_read()
        self.sequence += 1
        self.phase = int(opcode == 0xfc6c)
        register = int.from_bytes(cdb[2:4],'big') if self.phase else 0xffff
        self.record = record(sequence=self.sequence,phase=self.phase,register=register,slot=self.slot,
                             blocked=self.blocked,mode=self.mode)
        gate = struct.unpack_from('<I',self.record,32)[0]
        status = struct.unpack_from('<i',self.record,28)[0]
        reply = (b'\xfc\x6bHYC3'+bytes((3,gate))+struct.pack('>IHH',self.slot,self.sequence,512) if not self.phase else
                 b'\xfc\x6cHYC3'+struct.pack('>HiH',self.sequence,status,register)+bytes((gate,1)))
        return self.reply_mutator(reply) if self.reply_mutator else reply


class CodecRomProtocolTests(unittest.TestCase):
    def session(self, **fake_options):
        fake = FakeCodecRom()
        for key,value in fake_options.items(): setattr(fake,key,value)
        session = rom.MiniCodecRomSession(fake,slot=fake.slot,build_tag=TAG,known_free_slot=True)
        with patch('time.sleep'):
            start = session.upload_and_start(b'ABCD',expected_sha256=recovery.sha(b'ABCD'))
        return fake,session,start

    def test_exact_cdb_and_no_cross_profile_or_fd61_commands(self):
        self.assertEqual(rom.codec_rom_read_cdb(0x58,0x1234).hex(),'fc6c00581234ffffffffffffffffffff')
        valid = [(rom.codec_rom_snapshot_cdb(),16),(rom.codec_rom_record_cdb(),512)]
        valid += [(rom.codec_rom_read_cdb(r,1),16) for r in rom.REGISTERS]
        for cdb,length in valid:
            rom.validate_codec_rom_request(cdb,None,length,slot=SLOT)
            for other in (recovery.validate_ram_request,recovery.validate_nor_request,validate_codec_request,validate_engine_request,validate_codec_board_request):
                with self.assertRaises(ValueError): other(cdb,None,length,slot=SLOT)
        for cdb,length in [(recovery.ram_read_cdb(SLOT,512,slot=SLOT),512)] + [
            (op.to_bytes(2,'big')+b'\xff'*14,16) for op in (0xfc60,0xfc62,0xfc64,0xfc65,0xfd66,0xfc68,0xfc69,0xfd6a,0xfc70,0xfc72,0xfd71,0xfb01,0xfb04)]:
            with self.assertRaises(ValueError): rom.validate_codec_rom_request(cdb,None,length,slot=SLOT)
        for reg in (-1,0,2,0x66,65536,True,'0x58'):
            with self.assertRaises(ValueError): rom.codec_rom_read_cdb(reg,1)
        for nonce in (0,-1,65535,65536,True,'1'):
            with self.assertRaises(ValueError): rom.codec_rom_read_cdb(0x58,nonce)

    def test_malformed_frames_direction_length_padding_and_slot_are_rejected(self):
        command = rom.codec_rom_read_cdb(0x58,1)
        for cdb,data,length,slot in [(command[:-1],None,16,SLOT),(command[:-1]+b'\0',None,16,SLOT),
                (command,None,512,SLOT),(command,b'',16,SLOT),(command,b'1234',0,SLOT),
                (command,None,16,0),(rom.codec_rom_record_cdb(),None,511,SLOT),
                (rom.codec_rom_snapshot_cdb(),None,True,SLOT)]:
            with self.assertRaises(ValueError): rom.validate_codec_rom_request(cdb,data,length,slot=slot)

    def test_default_imported_cli_has_no_device_operations(self):
        with (patch.object(recovery,'WindowsRomTransport',side_effect=AssertionError('opened')),
              patch.object(recovery,'discover_windows_rom_disks',side_effect=AssertionError('enumerated'))):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(rom.main([]),0)
        result = json.loads(out.getvalue())
        self.assertFalse(result['device_io'] or result['enumerated'] or result['automatic_retry'])
        fake = FakeCodecRom()
        session = rom.MiniCodecRomSession(fake,slot=SLOT,build_tag=TAG)
        with self.assertRaises(ValueError): session.snapshot()
        with self.assertRaises(ValueError): session.read_register(0x58)
        with self.assertRaises(ValueError): session.read(SLOT,512)
        self.assertEqual(fake.commands,[])

    def test_upload_handshake_snapshot_stops_before_gpio_when_clock_gate_blocks(self):
        fake,session,start = self.session(blocked=True)
        snapshot = start['codec_rom_snapshot']
        self.assertEqual((snapshot['phase'],snapshot['sequence'],snapshot['gate'],snapshot['status']),(0,1,4,-3))
        self.assertFalse(snapshot['can_read_register'] or snapshot['gpio_touched'] or session.failed)
        self.assertIs(session.last_snapshot,snapshot)
        self.assertEqual(len(session.last_record),512)
        self.assertEqual(fake.commands,[0xfb06,0xfd07,0xfb08,0xfc6b,0xfd6d])
        with self.assertRaises(ValueError): session.read_register(0x58)
        self.assertNotIn(0xfc6c,fake.commands)

    def test_each_explicit_read_consumes_snapshot_before_submission_success_and_nack(self):
        fake,session,start = self.session()
        self.assertTrue(start['can_read_register'])
        fake.before_read = lambda:self.assertFalse(session.armed or session.snapshot_sequence)
        result = session.read_register(0x58)
        self.assertTrue(result['read_successful'])
        self.assertEqual((result['sequence'],result['snapshot_sequence_consumed'],result['value']),(2,1,0x40))
        with self.assertRaises(ValueError): session.read_register(0x59)
        self.assertEqual(fake.commands.count(0xfc6c),1)
        session.snapshot()
        fake.mode = 'nack'
        result = session.read_register(0x59)
        self.assertEqual((result['sequence'],result['snapshot_sequence_consumed'],result['status']),(4,3,-2))
        self.assertTrue(result['nack_is_not_codec_absence'])
        self.assertFalse(result['read_successful'] or result['session_failed'] or session.armed)
        self.assertEqual(fake.commands.count(0xfc6b),2)
        self.assertEqual(fake.commands.count(0xfc6c),2)
        self.assertEqual(fake.commands.count(0xfb08),1)

    def test_snapshot_fault_preserves_record_but_is_terminal(self):
        for mode in ('guards','clock-change'):
            fake,session,start = self.session(mode=mode)
            with self.subTest(mode=mode):
                self.assertFalse(start['can_read_register'])
                self.assertTrue(start['codec_rom_snapshot']['session_failed'])
                self.assertEqual(len(session.last_record),512)
                with self.assertRaises(ValueError): session.snapshot()
                with self.assertRaises(ValueError): session.read_register(0x58)
                self.assertEqual(fake.commands.count(0xfc6b),1)
                self.assertNotIn(0xfc6c,fake.commands)

    def test_read_faults_keep_evidence_and_disable_all_further_operations(self):
        for mode,status in [('restore-fault',-6),('guards',-7),('clock-change',-8),('not-armed',-3)]:
            fake,session,_ = self.session(); fake.mode = mode
            result = session.read_register(0x58)
            with self.subTest(mode=mode):
                self.assertEqual(result['status'],status)
                self.assertTrue(result['session_failed'])
                self.assertFalse(result['read_successful'])
                self.assertEqual(len(session.last_record),512)
                with self.assertRaises(ValueError): session.snapshot()
                with self.assertRaises(ValueError): session.read_register(0x58)
                self.assertEqual(fake.commands.count(0xfc6c),1)

    def test_record_clock_tuple_must_match_the_observed_ROM_profile(self):
        fake,session,_ = self.session(); fake.mode = 'setup-with-unapproved'
        with self.assertRaises(ValueError): session.read_register(0x58)
        self.assertTrue(session.failed)
        self.assertEqual(fake.commands.count(0xfc6c),1)

    def test_ambiguous_transfers_and_malformed_replies_never_retry(self):
        for opcode in (0xfc6c,0xfd6d):
            fake,session,_ = self.session(); fake.fail_opcode = opcode
            with self.subTest(opcode=opcode),self.assertRaises(OSError): session.read_register(0x58)
            self.assertTrue(session.failed)
            self.assertFalse(session.armed)
            with self.assertRaises(ValueError): session.snapshot()
            self.assertEqual(fake.commands.count(0xfc6c),1)
        mutations = [lambda r:r[:-1], lambda r:r[:6]+b'\0\x05'+r[8:],
                     lambda r:r[:12]+b'\0\x59'+r[14:], lambda r:r[:-1]+b'\0']
        for mutate in mutations:
            fake,session,_ = self.session(); fake.reply_mutator = mutate
            with self.assertRaises(ValueError): session.read_register(0x58)
            self.assertTrue(session.failed)
            self.assertEqual(fake.commands.count(0xfc6c),1)

    def test_record_tag_crc_nonce_phase_restore_clock_and_padding_are_checked(self):
        for offset in (12,16,20,24,32,36,48,52,92,96,396,400):
            fake,session,_ = self.session()
            def changed(data):
                value = bytearray(data); value[offset] ^= 1
                struct.pack_into('<I',value,504,zlib.crc32(value[:504]))
                return bytes(value)
            fake.record_mutator = changed
            with self.subTest(offset=offset),self.assertRaises(ValueError): session.read_register(0x58)
            self.assertTrue(session.failed)
            self.assertEqual(len(session.last_record),512)
        fake,session,_ = self.session(); fake.record_mutator = lambda r:r[:504]+b'\0'*4+r[508:]
        with self.assertRaises(ValueError): session.read_register(0x58)

    def test_bad_upload_readback_cannot_reach_snapshot_or_gpio(self):
        fake = FakeCodecRom(); fake.corrupt_readback = True
        session = rom.MiniCodecRomSession(fake,slot=SLOT,build_tag=TAG,known_free_slot=True)
        with self.assertRaises(ValueError): session.upload_and_start(b'ABCD',expected_sha256=recovery.sha(b'ABCD'))
        self.assertFalse(any(op in fake.commands for op in (0xfb08,0xfc6b,0xfc6c)))

    def test_HYC2_and_HYC1_identity_or_records_are_never_accepted(self):
        fake,session,_ = self.session()
        fake.reply_mutator = lambda data:data[:5]+b'2'+data[6:]
        with self.assertRaises(ValueError): session.read_register(0x58)
        self.assertTrue(session.failed)
        for magic,version in ((b'HYC2',2),(b'HYC1',1)):
            fake,session,_ = self.session()
            def legacy(data):
                raw=bytearray(data); raw[:4]=magic
                struct.pack_into('<I',raw,4,version)
                struct.pack_into('<I',raw,504,zlib.crc32(raw[:504]))
                return bytes(raw)
            fake.record_mutator=legacy
            with self.subTest(magic=magic),self.assertRaises(ValueError): session.read_register(0x58)
            self.assertTrue(session.failed)
            self.assertEqual(session.last_record[:4],magic)

    def test_no_SPTD_backend_is_copied_or_instantiated_by_client(self):
        self.assertIs(rom.MiniCodecRomSession.__bases__[0],recovery.MiniRamSession)
        self.assertFalse(hasattr(rom,'WindowsRomTransport'))
        self.assertFalse(hasattr(rom,'SCSI_PASS_THROUGH_DIRECT'))


if __name__ == '__main__': unittest.main()
