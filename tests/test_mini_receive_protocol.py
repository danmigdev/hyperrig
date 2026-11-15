"""HYRX protocol/transport negative controls; all transports are in memory."""
import ctypes
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_receive as probe
from tools import probe_mini_recovery as recovery
from tools.build_mini_rom_receive import validate_record,poison
from tests import test_mini_recovery as reference

SLOT=0x1C20000
TAG=0x12345678
PAYLOAD=bytes(v^255 for v in poison(260,0x55))


def make_record(*,payload=PAYLOAD,sequence=1,nonce=0x1234ABCD,seed=0x55,sample=1,mode="complete",raw_return=0):
    result=bytearray(512)
    initial=poison(260,seed)
    observed=payload+initial[len(payload):]
    if mode=="partial": observed=payload[:-1]+initial[len(payload)-1:]
    if mode=="late": observed=bytes([observed[0]^1])+observed[1:]
    changed=sum(a!=b for a,b in zip(observed[:len(payload)],initial))
    words={4:1,8:SLOT,12:TAG,16:sequence,20:nonce,24:len(payload),28:4 if mode=="late" else 3,
        32:5 if mode=="late" else 0,36:seed,40:zlib.crc32(payload),
        44:zlib.crc32(payload if mode=="late" else observed[:len(payload)]),48:zlib.crc32(observed[:len(payload)]),
        52:raw_return&0xFFFFFFFF,56:1,60:1,64:3,68:3,72:1,76:len(payload) if mode=="late" else changed,
        80:changed,84:int(mode!="late"),88:1,92:sample,96:0x12AB3456,100:0xABCDEF00,104:0x98FEDCBA}
    for offset,value in words.items(): struct.pack_into("<I",result,offset,value)
    result[:4]=b"HYRX";result[128:388]=observed
    result[388:404]=bytes((0x69^i*11)&255 for i in range(16))
    result[404:420]=bytes((0xD3^i*11)&255 for i in range(16))
    result[508:]=b"DONE";struct.pack_into("<I",result,504,zlib.crc32(result[:504]))
    return bytes(result)


class FakeReceive(reference.FakeRom):
    def __init__(self):
        super().__init__(SLOT)
        self.sequence=self.nonce=self.seed=self.length=self.sample=0
        self.fail_opcode=None;self.mode="complete";self.raw_return=0;self.payload=None
        self.record_mutator=None;self.bad_arm=False;self.bad_identity=False

    def exchange(self,cdb,data_out=None,read_length=0):
        opcode=int.from_bytes(cdb[:2],"big")
        if opcode in (0xFB06,0xFD07,0xFB08): return super().exchange(cdb,data_out,read_length)
        probe.validate_receive_request(cdb,data_out,read_length,slot=SLOT)
        self.commands.append(opcode)
        if opcode==self.fail_opcode: raise TimeoutError("ambiguous mocked HYRX command")
        if opcode==0xFC82:
            return b"\xfc\x82"+(b"NOPE" if self.bad_identity else b"HYRX")+b"\1\0"+struct.pack(">II",SLOT,32768)
        if opcode==0xFC83:
            seq,n,nonce,_crc,seed,_=struct.unpack_from(">HHIIBB",cdb,2)
            self.sequence,self.length,self.nonce,self.seed,self.sample=seq,n,nonce,seed,0
            return b"\xfc\x83HYRX"+struct.pack(">HIHBB",seq,int(self.bad_arm),n,1,1)
        if opcode==0xFB84:
            self.payload=data_out;return b""
        if opcode==0xFD85:
            self.sample+=1
            mode="late" if self.mode=="late" and self.sample==2 else "complete" if self.mode=="late" else self.mode
            raw=make_record(payload=self.payload,sequence=self.sequence,nonce=self.nonce,seed=self.seed,
                            sample=self.sample,mode=mode,raw_return=self.raw_return)
            return self.record_mutator(raw) if self.record_mutator else raw
        raise AssertionError("unexpected command")


class ReceiveProtocolTests(unittest.TestCase):
    def session(self,expected_raw_return=None):
        fake=FakeReceive()
        session=probe.MiniReceiveSession(fake,slot=SLOT,build_tag=TAG,expected_raw_return=expected_raw_return,
                                        known_free_slot=True)
        with patch("time.sleep"):
            result=session.upload_and_start(b"test RAM payload",expected_sha256=recovery.sha(b"test RAM payload"))
        return fake,session,result

    def test_exact_cdb_lengths_padding_and_separate_profile(self):
        arm=probe.arm_cdb(1,260,0x1234ABCD,0x11223344,0x55)
        out=probe.receive_cdb(1,260,0x1234ABCD)
        self.assertEqual(arm.hex(),"fc83000101041234abcd1122334455ff")
        self.assertEqual(out.hex(),"fb8400011234abcd0104ffffffffffff")
        vectors=[(probe.identity_cdb(),None,16),(arm,None,16),(out,PAYLOAD,0),(probe.record_cdb(),None,512)]
        for cdb,data,count in vectors:
            probe.validate_receive_request(cdb,data,count,slot=SLOT)
            with self.assertRaises(ValueError): recovery.validate_ram_request(cdb,data,count,slot=SLOT)
            for index in (-1,):
                if cdb[:2]==b"\xfc\x83": continue
                broken=bytearray(cdb);broken[index]^=1
                with self.assertRaises(ValueError): probe.validate_receive_request(bytes(broken),data,count,slot=SLOT)
        for opcode in (0xFC60,0xFD61,0xFC72,0xFB01,0xFC7B,0xFC7D):
            with self.assertRaises(ValueError): probe.validate_receive_request(opcode.to_bytes(2,"big")+b"\xff"*14,None,16,slot=SLOT)

    def test_start_only_identifies_and_first_observation_closes(self):
        fake,session,result=self.session()
        self.assertFalse(result["receive_called_on_entry"])
        self.assertEqual(fake.commands[-1],0xFC82)
        observed=session.receive_once(PAYLOAD,nonce=0x1234ABCD)
        self.assertEqual(fake.commands[-4:],[0xFC83,0xFB84,0xFD85,0xFD85])
        self.assertTrue(observed["observed_complete_and_stable"])
        self.assertTrue(observed["observation_session_closed"])
        self.assertFalse(observed["return_semantics_qualified"])
        before=len(fake.commands)
        with self.assertRaises(ValueError):session.receive_once(PAYLOAD,nonce=7)
        with self.assertRaises(ValueError):session.read(SLOT,32)
        self.assertEqual(len(fake.commands),before)

    def test_explicit_observed_return_allows_new_sequence_not_repeated_out(self):
        fake,session,_=self.session(0)
        for seq in (1,2):
            result=session.receive_once(PAYLOAD,nonce=seq)
            self.assertEqual(result["sequence"],seq)
            self.assertFalse(result["session_failed"])
        self.assertEqual(fake.commands.count(0xFB84),2)

    def test_every_transport_timeout_is_terminal_and_no_retry(self):
        for op in (0xFC83,0xFB84,0xFD85):
            fake,session,_=self.session(0);fake.fail_opcode=op
            with self.assertRaises(TimeoutError):session.receive_once(PAYLOAD,nonce=1)
            self.assertTrue(session.failed)
            self.assertEqual(session.ambiguous_receive,op!=0xFC83)
            before=len(fake.commands)
            with self.assertRaises(ValueError):session.receive_once(PAYLOAD,nonce=1)
            self.assertEqual(len(fake.commands),before)

    def test_negative_or_unexpected_return_preserved_stops_before_resample(self):
        for value in (-1,-2147483648,1,260):
            fake,session,_=self.session(0);fake.raw_return=value
            result=session.receive_once(PAYLOAD,nonce=7)
            self.assertEqual(result["raw_return"],value)
            self.assertTrue(result["session_failed"])
            self.assertEqual(fake.commands.count(0xFD85),1)

    def test_partial_and_late_buffer_stop(self):
        for mode in ("partial","late"):
            fake,session,_=self.session(0);fake.mode=mode
            result=session.receive_once(PAYLOAD,nonce=7)
            self.assertTrue(result["session_failed"])
            self.assertEqual(fake.commands.count(0xFD85),1 if mode=="partial" else 2)

    def test_bad_arm_never_calls_receive(self):
        fake,session,_=self.session();fake.bad_arm=True
        with self.assertRaises(ValueError):session.receive_once(PAYLOAD,nonce=1)
        self.assertNotIn(0xFB84,fake.commands)

    def test_record_checksum_nonce_build_and_guards_rejected(self):
        for offset in (12,20,48,96,108,388,504):
            fake,session,_=self.session()
            def mutate(raw):
                data=bytearray(raw);data[offset]^=1;return bytes(data)
            fake.record_mutator=mutate
            with self.assertRaises(ValueError):session.receive_once(PAYLOAD,nonce=1)
            self.assertTrue(session.failed)

    def test_payload_boundaries_and_poison_rejected_before_io(self):
        fake,session,_=self.session()
        before=len(fake.commands)
        for value in (b"",bytes(261),bytearray(PAYLOAD),poison(260,0x55)):
            with self.assertRaises(ValueError):session.receive_once(value,nonce=1)
        self.assertEqual(len(fake.commands),before)
        for length in (1,63,64,65,255,256,260):
            fake,session,_=self.session()
            payload=bytes(v^255 for v in poison(length,0x55))
            self.assertTrue(session.receive_once(payload,nonce=1)["observed_complete_and_stable"])

    def test_callback_pointers_are_observed_not_constrained_to_invented_map(self):
        raw=make_record()
        item=validate_record(raw,base=SLOT,build_tag=TAG,sequence=1,nonce=0x1234ABCD,payload=PAYLOAD,seed=0x55)
        self.assertEqual(item["rom_pointer_observations"],{"send":0x12AB3456,"receive":0xABCDEF00,"handler_slot":0x98FEDCBA})
        self.assertFalse(item["pointer_address_map_validated"])

    def test_default_cli_is_offline(self):
        result=subprocess.run([sys.executable,"-X","utf8",str(ROOT/"tools/probe_mini_receive.py")],
                              cwd=ROOT,capture_output=True,text=True,check=True)
        data=json.loads(result.stdout)
        self.assertFalse(data["device_io"]);self.assertFalse(data["enumerated"])

    def test_windows_adapter_error_details_and_allowlist_mock_only(self):
        path=r"\\.\PhysicalDrive42"
        kernel=reference.WindowsTransportTests().fake_kernel()
        with patch("os.name","nt"),patch("ctypes.WinDLL",return_value=kernel,create=True), \
             patch("tools.probe_mini_recovery.discover_windows_rom_disks",return_value=[{"path":path}]), \
             patch("ctypes.get_last_error",return_value=121,create=True) as get_error:
            with probe.WindowsReceiveTransport(path,slot=SLOT) as transport:
                self.assertEqual(transport.inquiry["product"],"UBOOT1.00")
                with self.assertRaises(ValueError):transport.exchange(b"\xfb\x01"+b"\xff"*14,read_length=16)
                self.assertEqual(kernel.DeviceIoControl.call_count,1)
                def fail(_h,_io,p,_size,_out,_os,returned,_ov):
                    s=p._obj.sptd;s.data_transfer_length=64;s.scsi_status=2
                    returned._obj.value=88;return 0
                kernel.DeviceIoControl.side_effect=fail
                with self.assertRaises(probe.RomCommandError) as caught:
                    transport.exchange(probe.receive_cdb(1,260,1),data_out=PAYLOAD)
                self.assertTrue(caught.exception.submitted)
                self.assertEqual(caught.exception.errno,121)
                self.assertEqual(caught.exception.details["data_transfer_length"],64)
                self.assertEqual(caught.exception.details["scsi_status"],2)
                get_error.assert_called_once_with()
            kernel.CloseHandle.assert_called_once_with(123)


if __name__=="__main__":unittest.main()
