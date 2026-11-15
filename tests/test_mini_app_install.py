"""Operational HYW1 installer tests; fake NOR only, no hardware transport."""
from dataclasses import replace
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import install_mini_app as install
from tools import build_mini_app_writer_operational as builder
from tools import build_mini_app_writer as frozen
from tools import probe_mini_app_writer as observer
from tests.test_mini_recovery import FakeRom
from tests.test_mini_app_writer_protocol import encoded_record,changed_record

SLOT,TAG=0x1C20000,0x12345678
IMAGE=b"operational mock RAM image"
APP_BYTES=install.APP_END-install.APP_START
OLD=bytes((i*73+(i>>9))&255 for i in range(APP_BYTES))
NEW=bytes(value^0xA6 for value in OLD[:8192])+OLD[8192:]


def fixture():
    return install.Installation(SLOT,TAG,IMAGE,install.sha(IMAGE),*("1"*64,)*3,
                                NEW,OLD,"2"*64,(0x5000,0x4000))


class FakeOperational(FakeRom):
    def __init__(self,plan):
        super().__init__(plan.slot);self.plan=plan
        self.flash=bytearray(b"\x79"*0x4000+plan.preimage+b"\xA6"*(0x100000-0x82000))
        self.original=bytes(self.flash);self.fields={4:1,8:self.slot,12:plan.build_tag,88:0x80000000,92:1,108:1,116:1}
        self.next_token=1;self.staged=b"";self.stage_sequence=0;self.erased=False
        self.program_addresses=[];self.erase_addresses=[];self.echo_addresses=[];self.counts={}
        self.fail_after=None;self.before=None;self.reply_mutator=None;self.record_mutator=None
        self.trace=[]

    def status(self,op):
        f=self.fields
        return op.to_bytes(2,"big")+bytes((f.get(20,0),f.get(16,0)))+struct.pack(">III",f.get(24,0),f.get(28,0),f.get(52,0))

    def exchange(self,cdb,data_out=None,read_length=0):
        op=int.from_bytes(cdb[:2],"big")
        if op in (0xFB06,0xFD07,0xFB08):return super().exchange(cdb,data_out,read_length)
        install.validate_writer_operational_request(cdb,data_out,read_length,slot=self.slot)
        self.commands.append(op);self.counts[op]=self.counts.get(op,0)+1
        if self.before:self.before(self,op,cdb)
        f=self.fields
        if op==0xFC78:raw=b"\xfc\x78HYW1\1\1"+struct.pack(">II",self.slot,32768)
        elif op==0xFC79:
            f.update({16:1,52:0xEB6014,56:0xEB6014,60:0,64:2,112:88});raw=self.status(op)
        elif op==0xFD7F:
            a,n=struct.unpack_from(">IH",cdb,2);raw=bytes(self.flash[a:a+n]);f[80]=f.get(80,0)+n;f[52]=install.crc(raw)
        elif op==0xFC7A:
            a,oldcrc,newcrc=struct.unpack_from(">III",cdb,2)
            assert f[16] in (1,5) and install.crc(self.flash[a:a+4096])==oldcrc
            f.update({16:2,24:self.next_token,28:1,32:a,40:oldcrc,44:newcrc,52:oldcrc,80:f[80]+4096,96:0,100:0,104:0})
            self.next_token+=1;self.erased=False;raw=self.status(op)
        elif op in (0xFB7C,0xFC7B,0xFC7D,0xFC80):
            token,seq,a=struct.unpack_from(">III",cdb,2)
            assert token==f[24] and seq==f[28]+1;f[28]=seq
            if op==0xFB7C:
                assert not f.get(100,0) and f[16] in (2,3) and f[32]<=a<f[32]+4096
                self.staged=bytes(data_out[:256]);self.stage_sequence=seq
                f.update({16:4,36:a,48:install.crc(self.staged),52:install.crc(self.staged),88:260,100:1,104:0})
                raw=b""
            elif op==0xFC7B:
                assert f[16]==4 and f[100] and f[104] and a==f[32] and not self.erased
                assert install.crc(self.flash[a:a+4096])==f[40]
                self.flash[a:a+4096]=b"\xff"*4096;self.erased=True;self.erase_addresses.append(a)
                f.update({52:install.crc(b"\xff"*4096),68:f.get(68,0)+1,72:f.get(72,0)+1,80:f[80]+8192,84:f.get(84,0)+2})
                raw=self.status(op)
            elif op==0xFC7D:
                bit=1<<((a-f[32])//256)
                assert self.erased and f[16]==4 and f[100] and f[104] and a==f[36] and not f[96]&bit
                assert self.flash[a:a+256]==b"\xff"*256
                self.flash[a:a+256]=self.staged;self.program_addresses.append(a)
                f.update({16:3,100:0,104:0,52:install.crc(self.staged),68:f.get(68,0)+1,76:f.get(76,0)+1,
                          80:f[80]+512,84:f.get(84,0)+2,96:f[96]|bit});raw=self.status(op)
            else:
                assert f[96]==65535 and not f[100] and a==f[32] and install.crc(self.flash[a:a+4096])==f[44]
                f.update({16:5,24:0,52:f[44],80:f[80]+4096});self.erased=False;raw=self.status(op)
        elif op==0xFD87:
            token,seq,a=struct.unpack_from(">III",cdb,2)
            assert token==f[24] and seq==self.stage_sequence and a==f[36] and f[100]
            f[104]=1;self.echo_addresses.append(a);raw=self.staged
        elif op==0xFC7E:raw=self.status(op)
        elif op==0xFD88:
            raw=encoded_record(f)
            if self.record_mutator:raw=self.record_mutator(raw)
        else:raise AssertionError("unexpected opcode")
        self.trace.append((op,f.get(28,0),len(self.erase_addresses),len(self.program_addresses)))
        if self.reply_mutator:raw=self.reply_mutator(op,raw)
        if self.fail_after==(op,self.counts[op]):raise TimeoutError("reply lost after accepted fake command")
        return raw


class InstallerTests(unittest.TestCase):
    def session(self,preflight=True):
        plan=fixture();fake=FakeOperational(plan);journal=[]
        session=install.MiniAppInstallerSession(fake,plan,journal=journal.append,known_free_slot=True)
        with patch("time.sleep"):session.upload_and_start(IMAGE,expected_sha256=install.sha(IMAGE))
        session.initialize_spi()
        if preflight:session.verify_complete_preimage()
        return fake,session,journal

    def terminal(self,fake,session):
        before=len(fake.commands)
        self.assertTrue(session.failed)
        with self.assertRaises(ValueError):session.install_application()
        self.assertEqual(before,len(fake.commands))
        self.assertEqual(fake.commands.count(0xFB08),1)

    def test_operational_opcodes_are_separate_and_exact(self):
        for op,a in ((0xFC7B,0x4000),(0xFC7D,0x4100),(0xFC80,0x4000)):
            cdb=install.mutation_cdb(op,1,3,a)
            install.validate_writer_operational_request(cdb,None,16,slot=SLOT)
            with self.assertRaises(ValueError):observer.validate_writer_observer_request(cdb,None,16,slot=SLOT)
            for c,d,n in ((cdb,b"",16),(cdb,None,15),(cdb[:-1]+b"\0",None,16),(cdb+b"\0",None,16)):
                with self.assertRaises(ValueError):install.validate_writer_operational_request(c,d,n,slot=SLOT)
        for op in (0xFB01,0xFB04,0xFD61,0xFC81):
            with self.assertRaises(ValueError):install.validate_writer_operational_request(op.to_bytes(2,"big")+b"\xff"*14,None,16,slot=SLOT)
        for op,a in ((0xFC7B,0x3000),(0xFC7B,0x4100),(0xFC7D,0x82000),(0xFC80,0x82000)):
            with self.assertRaises(ValueError):install.mutation_cdb(op,1,2,a)

    def test_fixture_order_cannot_publish_header_first_or_drop_changed_sector(self):
        for order in ((0x4000,0x5000),(0x5000,),(),(0x5000,0x5000,0x4000)):
            with self.assertRaises(ValueError):replace(fixture(),sector_order=order)
        for a in range(0x4000,0x82000,4096):
            order=builder.page_order(a)
            self.assertEqual(set(order),set(range(a,a+4096,256)))
        self.assertEqual(builder.page_order(0x4000),list(range(0x4100,0x5000,256))+[0x4000])

    def test_full_install_reads_whole_preimage_and_final_app_leaves_rom(self):
        fake,session,journal=self.session();result=session.install_application()
        self.assertEqual(bytes(fake.flash[0x4000:0x82000]),NEW)
        self.assertEqual(bytes(fake.flash[:0x4000]),fake.original[:0x4000])
        self.assertEqual(bytes(fake.flash[0x82000:]),fake.original[0x82000:])
        self.assertEqual(fake.erase_addresses,[0x5000,0x4000])
        expected=list(range(0x5000,0x6000,256))+list(range(0x4100,0x5000,256))+[0x4000]
        self.assertEqual(fake.program_addresses,expected);self.assertEqual(fake.echo_addresses,expected)
        self.assertEqual(bytes(session.initial_readback),OLD);self.assertEqual(bytes(session.final_readback),NEW)
        self.assertEqual((result["wren_attempts"],result["erase_attempts"],result["program_attempts"]),(34,2,32))
        self.assertTrue(result["rom_session_remains_active"])
        self.assertFalse(result["application_boot_attempted"] or result["hardware_runtime_qualified"])
        self.assertFalse(session.mutation_completion_unknown)
        self.assertEqual(fake.commands.count(0xFB08),1)
        for index,event in enumerate(journal):
            if event["event"]=="command_intent" and event.get("opcode") in ("fc7b","fc7d"):
                self.assertTrue(any(e["event"]=="page_echo_verified" for e in journal[:index]))
        before=len(fake.commands)
        with self.assertRaises(ValueError):session.install_application()
        with self.assertRaises(ValueError):session.start_reset_once()
        self.assertEqual(before,len(fake.commands))

    def test_no_whole_preimage_no_mutation(self):
        fake,session,_=self.session(False)
        with self.assertRaises(ValueError):session.install_application()
        self.assertFalse(fake.erase_addresses or fake.program_addresses)
        self.assertNotIn(0xFC7A,fake.commands)

    def test_changed_preimage_blocks_first_wren(self):
        fake,session,_=self.session(False);fake.flash[0x81000]^=1
        with self.assertRaises(ValueError):session.verify_complete_preimage()
        self.assertFalse(session.mutation_command_submitted)
        self.terminal(fake,session)

    def test_preimage_is_rechecked_for_sector_immediately_before_arm(self):
        fake,session,_=self.session();fake.flash[0x5000]^=1
        with self.assertRaises(ValueError):session.install_application()
        self.assertNotIn(0xFC7A,fake.commands);self.assertFalse(fake.erase_addresses)
        self.terminal(fake,session)

    def test_echo_mismatch_stops_before_first_erase(self):
        fake,session,_=self.session()
        fake.reply_mutator=lambda op,raw:bytes([raw[0]^1])+raw[1:] if op==0xFD87 else raw
        with self.assertRaises(ValueError):session.install_application()
        self.assertFalse(session.mutation_command_submitted)
        self.assertFalse(fake.erase_addresses or fake.program_addresses)
        self.terminal(fake,session)

    def test_lost_erase_or_program_reply_is_terminal_ambiguous_no_reset(self):
        for op in (0xFC7B,0xFC7D):
            fake,session,_=self.session();fake.fail_after=(op,1)
            with self.subTest(op=op),self.assertRaises(TimeoutError):session.install_application()
            self.assertTrue(session.mutation_command_submitted and session.mutation_completion_unknown)
            self.assertEqual(fake.erase_addresses,[0x5000])
            self.assertEqual(len(fake.program_addresses),op==0xFC7D)
            self.assertEqual(fake.counts[op],1);self.terminal(fake,session)

    def test_lost_stage_echo_status_audit_do_not_repeat_commands(self):
        for op in (0xFB7C,0xFD87,0xFC7A):
            fake,session,_=self.session();fake.fail_after=(op,1)
            with self.subTest(op=op),self.assertRaises(TimeoutError):session.install_application()
            self.assertFalse(fake.erase_addresses or fake.program_addresses)
            self.assertEqual(fake.counts[op],1);self.terminal(fake,session)

    def test_post_erase_audit_counter_or_wip_poll_failure_stops_before_program(self):
        for offset,value in ((68,0),(72,2),(76,1),(84,0),(84,65537),(92,0),(108,0),(116,0)):
            fake,session,_=self.session()
            fake.record_mutator=lambda raw,o=offset,v=value:changed_record(raw,o,v) if fake.erase_addresses else raw
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):session.install_application()
            self.assertEqual(fake.erase_addresses,[0x5000]);self.assertFalse(fake.program_addresses)
            self.assertTrue(session.mutation_completion_unknown);self.terminal(fake,session)

    def test_page_readback_corruption_stops_before_next_page(self):
        fake,session,_=self.session()
        def corrupt(op,raw):
            if op==0xFD7F and fake.program_addresses:
                broken=bytes([raw[0]^1])+raw[1:]
                fake.fields[52]=install.crc(broken);return broken
            return raw
        fake.reply_mutator=corrupt
        with self.assertRaises(ValueError):session.install_application()
        self.assertEqual(fake.program_addresses,[0x5000])
        self.assertFalse(session.image_verified);self.terminal(fake,session)

    def test_final_full_read_detects_changed_unchanged_sector(self):
        fake,session,_=self.session()
        def corrupt_before_final(target,op,cdb):
            if op==0xFD7F and len(target.program_addresses)==32 and target.fields[24]==0:
                target.flash[0x81000]^=1;target.before=None
        fake.before=corrupt_before_final
        with self.assertRaises(ValueError):session.install_application()
        self.assertEqual(len(fake.program_addresses),32)
        self.assertFalse(session.image_verified);self.terminal(fake,session)

    def test_durable_journal_failure_prevents_the_pending_mutating_exchange(self):
        fake,session,journal=self.session()
        def fail(event):
            journal.append(event)
            if event["event"]=="command_intent" and event.get("opcode")=="fc7b":raise OSError("journal cannot be persisted")
        session.journal=fail
        with self.assertRaises(OSError):session.install_application()
        self.assertNotIn(0xFC7B,fake.commands);self.assertFalse(session.mutation_command_submitted)
        self.terminal(fake,session)

    def test_gate1_elf_is_separate_and_gate0_parser_refuses_it(self):
        manifest=json.loads(builder.REPORT.read_text())
        for item in manifest["executable_artifacts"]:
            raw=(ROOT/item["elf"]).read_bytes();payload,metadata=builder.inspect_operational_elf(raw,item["base"])
            self.assertEqual(payload,(ROOT/item["file"]).read_bytes())
            self.assertEqual(metadata["mutation_gate_value"],1)
            with self.assertRaises(ValueError):frozen.inspect_writer_elf(raw,item["base"])
            offset=builder._gate_location(raw)
            changed=raw[:offset]+bytes(4)+raw[offset+4:]
            with self.assertRaises(ValueError):builder.inspect_operational_elf(changed,item["base"])

    def test_derivation_is_exact_reversible_and_current_plan_pinned(self):
        source=(ROOT/"firmware/mini/app_writer/writer.c").read_bytes()
        derived=builder.derive_core(source).decode()
        self.assertEqual(derived.replace(builder.OPERATIONAL_BLOCK,builder.ORIGINAL_BLOCK),source.decode().replace("\r\n","\n"))
        with self.assertRaises(ValueError):builder.derive_core(source.replace(b"mutations_enabled=1",b"mutations_enabled=2"))
        pio=(ROOT/"firmware/mini/app_writer/nor_pio.c").read_bytes()
        changed=builder.derive_pio(pio).decode()
        self.assertEqual(changed.replace(builder.PIO_DELAY_NEW,builder.PIO_DELAY_OLD),pio.decode().replace("\r\n","\n"))
        plan=install.prepare_installation()
        self.assertEqual(plan.summary()["candidate_sha256"],"3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff")
        self.assertEqual(plan.sector_order[-1],0x4000)

    def test_default_cli_never_opens_or_enumerates_device(self):
        result=subprocess.run([sys.executable,"-X","utf8",str(ROOT/"tools/install_mini_app.py")],
                              cwd=ROOT,capture_output=True,text=True,check=True)
        item=json.loads(result.stdout)
        self.assertFalse(item["device_io"] or item["enumerated"] or item["CLI_executes_installation"])


if __name__=="__main__":unittest.main()
