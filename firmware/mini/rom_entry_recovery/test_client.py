"""Offline client tests using C-host records and a non-device transport.

The target stack observation is synthesized only to exercise the wire parser;
these records and exchanges provide no physical GPIO/reset evidence.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_entry_recovery as client
from tools.probe_mini_recovery import RomCommandError, usb_crc_transform

BASE=0x01c20000
SAVED=json.loads((ROOT/'build/mini-rom-entry-recovery/host-records.json').read_text())
TAG=struct.unpack_from('<I',bytes.fromhex(SAVED[0]),12)[0]


def record(index,sequence,*,base=BASE):
    data=bytearray.fromhex(SAVED[index])
    struct.pack_into('<I',data,8,base)
    struct.pack_into('<I',data,16,sequence)
    struct.pack_into('<I',data,36,60)  # Synthetic parser input, not a target measurement.
    phase=struct.unpack_from('<I',data,20)[0]
    struct.pack_into('<I',data,236,0 if phase==0 else sequence-1)
    struct.pack_into('<I',data,248,zlib.crc32(data[:248]))
    return bytes(data)


class FakeTransport:
    def __init__(self,*,base=BASE,check_index=1,snapshot_index=0):
        self.base=base;self.check_index=check_index;self.snapshot_index=snapshot_index
        self.calls=[];self.sequence=0;self.last=None;self.memory=bytearray(32768)
        self.identity_delta=None;self.record_delta=None;self.reply_delta=None
        self.reset_error=RomCommandError('mock disconnect',submitted=True,details={'mock':True})
        self.operation_error=None;self.identity_count=0

    def exchange(self,cdb,*,data_out=None,read_length=0):
        client.validate_entry_recovery_request(cdb,data_out,read_length,slot=self.base)
        self.calls.append((bytes(cdb),data_out,read_length))
        op=cdb[:2]
        if op==b'\xfb\x06':
            address,length=struct.unpack_from('>IH',cdb,2)
            self.memory[address-self.base:address-self.base+length]=usb_crc_transform(data_out)
            return b''
        if op==b'\xfd\x07':
            address,length=struct.unpack_from('>IH',cdb,2)
            return usb_crc_transform(self.memory[address-self.base:address-self.base+length])
        if op==b'\xfb\x08':return op+bytes(14)
        if op==b'\xfc\x74':
            self.identity_count+=1
            data=bytearray(b'\xfc\x74HYK1\x01\x07'+struct.pack('>IHH',self.base,32768,256))
            if self.identity_delta is not None:data[self.identity_delta]^=1
            return bytes(data)
        if op in (b'\xfc\x75',b'\xfc\x76'):
            if self.operation_error:raise self.operation_error
            phase=int(op==b'\xfc\x76')
            if phase:
                assert self.last is not None
                assert struct.unpack_from('>II',cdb,2)==(self.sequence,struct.unpack_from('<I',self.last,248)[0])
            self.sequence+=1
            self.last=record(self.check_index if phase else self.snapshot_index,self.sequence,base=self.base)
            status=struct.unpack_from('<i',self.last,24)[0]
            armed=int(not phase and not status and struct.unpack_from('<I',self.last,72)[0]&0x409==0x409)
            data=bytearray(op+b'HYK1'+struct.pack('>IiBB',self.sequence,status,phase,armed))
            if self.reply_delta is not None:data[self.reply_delta]^=1
            return bytes(data)
        if op==b'\xfd\x77':
            assert int.from_bytes(cdb[2:6],'big')==self.sequence and self.last is not None
            data=bytearray(self.last)
            if self.record_delta is not None:data[self.record_delta]^=1
            return bytes(data)
        if op==b'\xfc\x81':
            assert self.last is not None
            assert struct.unpack_from('>II',cdb,2)==(self.sequence,struct.unpack_from('<I',self.last,248)[0])
            if self.reset_error:raise self.reset_error
            return b'mock unexpected!'
        raise AssertionError('unhandled mock command')


def active(**kwargs):
    transport=FakeTransport(**kwargs)
    session=client.MiniEntryRecoverySession(transport,slot=transport.base,build_tag=TAG)
    session.started=True
    session._handshake()
    session.ready=True
    return session,transport


class ClientTests(unittest.TestCase):
    def test_actual_upload_readback_jump_lifecycle(self):
        transport=FakeTransport();image=bytes(range(256))*3
        session=client.MiniEntryRecoverySession(transport,slot=BASE,build_tag=TAG,known_free_slot=True)
        self.assertEqual(transport.calls,[])
        digest=hashlib.sha256(image).hexdigest()
        session.upload_only(image,expected_sha256=digest)
        with patch('time.sleep'):
            started=session.verify_and_start(image,expected_sha256=digest)
        self.assertTrue(session.ready)
        self.assertTrue(started['readback_verified'])
        self.assertFalse(started['snapshot_performed'])
        self.assertEqual([c[0][:2] for c in transport.calls],
                         [b'\xfb\x06']*2+[b'\xfd\x07']*2+[b'\xfb\x08',b'\xfc\x74'])
        with self.assertRaises(ValueError):session.verify_and_start(image,expected_sha256=digest)

    def test_identity_is_passive_and_exact(self):
        for offset in range(16):
            transport=FakeTransport();transport.identity_delta=offset
            session=client.MiniEntryRecoverySession(transport,slot=BASE,build_tag=TAG)
            session.started=True
            with self.assertRaises(ValueError):session._handshake()
            self.assertEqual([c[0][:2] for c in transport.calls],[b'\xfc\x74'])

    def test_check_requires_and_consumes_one_snapshot(self):
        session,transport=active()
        for operation in (session.check,session.request_rom_reset_once):
            with self.assertRaises(ValueError):operation()
        self.assertEqual(len(transport.calls),1)
        self.assertTrue(session.snapshot()['can_check'])
        result=session.check()
        self.assertEqual(result['check_result'],0)
        self.assertFalse(result['can_check'])
        count=len(transport.calls)
        with self.assertRaises(ValueError):session.check()
        with self.assertRaises(ValueError):session.read(BASE,4)
        self.assertEqual(len(transport.calls),count)
        self.assertTrue(session.snapshot()['can_check'])
        self.assertEqual(session.check()['sequence'],4)
        self.assertFalse(any(c[0][:2]==b'\xfc\x81' for c in transport.calls))

    def test_positive_check_never_resets(self):
        session,transport=active(base=0x01c28000,check_index=3)
        session.snapshot();result=session.check()
        self.assertTrue(result['all_three_observed'])
        self.assertFalse(result['ROM_reset_verified'])
        self.assertFalse(result['cold_SPL_state_verified'])
        self.assertFalse(any(c[0][:2]==b'\xfc\x81' for c in transport.calls))

    def test_direction_snapshot_does_not_arm(self):
        session,transport=active(snapshot_index=9)
        self.assertFalse(session.snapshot()['can_check'])
        count=len(transport.calls)
        with self.assertRaises(ValueError):session.check()
        self.assertEqual(len(transport.calls),count)

    def test_valid_fault_records_fail_session_without_reset(self):
        for index,status in ((4,-3),(5,-6),(6,-8),(7,-7),(8,-10)):
            session,transport=active(check_index=index)
            session.snapshot();result=session.check()
            self.assertEqual(result['status'],status)
            self.assertEqual(session.failed,status!=-3)
            self.assertFalse(any(c[0][:2]==b'\xfc\x81' for c in transport.calls))

    def test_malformed_record_reply_and_io_fail_closed(self):
        for kind,offsets in (('record_delta',(0,4,8,12,16,20,24,36,248,252)),
                             ('reply_delta',(0,1,2,6,9,10,13,14,15))):
            for offset in offsets:
                session,transport=active();setattr(transport,kind,offset)
                with self.assertRaises(ValueError):session.snapshot()
                self.assertTrue(session.failed)
                self.assertFalse(session.armed)
                count=len(transport.calls)
                with self.assertRaises(ValueError):session.request_rom_reset_once()
                self.assertEqual(len(transport.calls),count)
        session,transport=active();session.snapshot()
        transport.operation_error=RomCommandError('mock GPIO-check timeout',submitted=True)
        with self.assertRaises(RomCommandError):session.check()
        self.assertTrue(session.failed)
        self.assertFalse(session.armed)
        count=len(transport.calls)
        with self.assertRaises(ValueError):session.check()
        self.assertEqual(len(transport.calls),count)

    def test_explicit_reset_is_terminal_before_transport(self):
        for error in (RomCommandError('mock post',submitted=True,details={'test':1}),
                      RomCommandError('mock pre',submitted=False),RuntimeError('mock unexpected'),None):
            session,transport=active();session.snapshot();transport.reset_error=error
            original=transport.exchange
            def exchange(cdb,**kwargs):
                if cdb[:2]==b'\xfc\x81':
                    self.assertTrue(session.reset_submitted)
                    self.assertTrue(session.failed)
                    self.assertFalse(session.ready)
                return original(cdb,**kwargs)
            transport.exchange=exchange
            if error is not None and (not isinstance(error,RomCommandError) or not error.submitted):
                with self.assertRaises(type(error)):session.request_rom_reset_once()
            else:
                result=session.request_rom_reset_once()
                self.assertFalse(result['reset_completion_verified'])
                self.assertFalse(result['automatic_retry'])
                self.assertTrue(result['request_attempted'])
            count=len(transport.calls)
            for operation in (session.snapshot,session.check,session.request_rom_reset_once):
                with self.assertRaises(ValueError):operation()
            self.assertEqual(len(transport.calls),count)
            self.assertEqual(sum(c[0][:2]==b'\xfc\x81' for c in transport.calls),1)

    def test_sequence_limit_and_wrong_build(self):
        session,transport=active();session.sequence=65534
        with self.assertRaises(ValueError):session.snapshot()
        self.assertEqual(len(transport.calls),1)
        session,transport=active();session.build_tag^=1
        with self.assertRaises(ValueError):session.snapshot()
        self.assertTrue(session.failed)

    def test_request_allowlist(self):
        requests=[(client.entry_recovery_identity_cdb(),16,range(2,16)),
                  (client.entry_recovery_snapshot_cdb(),16,range(2,16)),
                  (client.entry_recovery_record_cdb(1),256,range(6,16)),
                  (client.entry_recovery_check_cdb(1,0),16,range(10,16)),
                  (client.entry_recovery_reset_cdb(1,0),16,range(10,16))]
        for cdb,length,padding in requests:
            client.validate_entry_recovery_request(cdb,None,length,slot=BASE)
            for index in (0,1,*padding):
                bad=bytearray(cdb);bad[index]^=0x80
                with self.assertRaises(ValueError):
                    client.validate_entry_recovery_request(bytes(bad),None,length,slot=BASE)
            for size in (0,1,length-1,length+1,True):
                with self.assertRaises(ValueError):client.validate_entry_recovery_request(cdb,None,size,slot=BASE)
            with self.assertRaises(ValueError):client.validate_entry_recovery_request(cdb,b'',length,slot=BASE)
            with self.assertRaises(ValueError):client.validate_entry_recovery_request(cdb,None,length,slot=BASE+4)
        for opcode in (0xfc60,0xfd61,0xfc70,0xfd71,0xfc72,0xfc73,0xfc78,0xfc82,0xfb84,0xfd85,0xfb03):
            with self.assertRaises(ValueError):
                client.validate_entry_recovery_request(opcode.to_bytes(2,'big')+b'\xff'*14,None,16,slot=BASE)
        for number in (0,-1,65535,True):
            with self.assertRaises(ValueError):client.entry_recovery_check_cdb(number,0)
            with self.assertRaises(ValueError):client.entry_recovery_reset_cdb(number,0)
        for crc in (-1,0x100000000,True):
            with self.assertRaises(ValueError):client.entry_recovery_reset_cdb(1,crc)

    def test_default_cli_is_offline(self):
        run=subprocess.run([sys.executable,str(ROOT/'tools/probe_mini_entry_recovery.py')],
                           capture_output=True,text=True,check=True,timeout=10)
        data=json.loads(run.stdout)
        self.assertFalse(data['device_io'])
        self.assertFalse(data['enumerated'])
        self.assertFalse(data['NOR_access'])
        self.assertFalse(data['automatic_retry'])


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ClientTests))
    if not result.wasSuccessful():
        for test,detail in result.failures+result.errors:print(test,detail,file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({'tests':result.testsRun,'result':'PASS','transport':'mock only',
                      'record_stack_observation':'synthetic parser fixture','hardware_access':False}))
