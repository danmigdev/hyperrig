"""HYW1 gate-zero observer checks. Every transport is an in-memory fake."""
from dataclasses import replace
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_app_writer as probe
from tools import probe_mini_recovery as recovery
from tests.test_mini_recovery import FakeRom

SLOT=0x1C20000
TAG=0x12345678
IMAGE=bytes((i*29+17)&255 for i in range(600))
OLD=bytes((i*13+(i>>8))&255 for i in range(4096))
NEW=bytes((i*19+7+(i>>5))&255 for i in range(4096))


def fixture():
    return probe.WriterObservation(SLOT,TAG,IMAGE,probe.sha(IMAGE),*("1"*64,)*5,OLD,NEW)


def encoded_record(fields):
    """Independent LE wire fixture, using the published offsets in writer.h/docs."""
    raw=bytearray(128);raw[:4]=b"HYW1";raw[124:]=b"DONE"
    for offset,value in fields.items():struct.pack_into("<I",raw,offset,value&0xFFFFFFFF)
    struct.pack_into("<I",raw,120,zlib.crc32(raw[:120]))
    return bytes(raw)


def changed_record(raw,offset,value):
    changed=bytearray(raw);struct.pack_into("<I",changed,offset,value&0xFFFFFFFF)
    struct.pack_into("<I",changed,120,zlib.crc32(changed[:120]))
    return bytes(changed)


class FakeWriter(FakeRom):
    def __init__(self,observation):
        super().__init__(observation.slot)
        self.observation=observation;self.nor=observation.preimage
        self.fields={4:1,8:self.slot,12:observation.build_tag,88:0x80000000,92:1,108:1}
        self.identity_gate=0;self.record_mutator=None;self.reply_mutator=None;self.echo_mutator=None
        self.fail_before=None;self.fail_after=None;self.staged_packet=None;self.requests=[]

    def status(self,op):
        f=self.fields
        return op.to_bytes(2,"big")+bytes((f.get(20,0),f.get(16,0)))+struct.pack(
            ">III",f.get(24,0),f.get(28,0),f.get(52,0))

    def exchange(self,cdb,data_out=None,read_length=0):
        opcode=int.from_bytes(cdb[:2],"big")
        if opcode in (0xFB06,0xFD07,0xFB08):return super().exchange(cdb,data_out,read_length)
        probe.validate_writer_observer_request(cdb,data_out,read_length,slot=self.slot)
        self.commands.append(opcode);self.requests.append((cdb,data_out,read_length))
        if opcode==self.fail_before:raise TimeoutError("mock pre-reply timeout; submission unknown")
        f=self.fields
        if opcode==0xFC78:
            raw=b"\xfc\x78HYW1"+bytes((1,self.identity_gate))+struct.pack(">II",self.slot,32768)
        elif opcode==0xFC79:
            assert f.get(16,0)==0
            f.update({16:1,52:0xEB6014,56:0xEB6014,112:96});raw=self.status(opcode)
        elif opcode==0xFD7F:
            address,n=struct.unpack_from(">IH",cdb,2);offset=address-0x4000
            raw=self.nor[offset:offset+n];assert len(raw)==n
            f[80]=f.get(80,0)+n;f[52]=zlib.crc32(raw)
        elif opcode==0xFC7A:
            address,oldcrc,newcrc=struct.unpack_from(">III",cdb,2)
            assert address==0x4000 and oldcrc==zlib.crc32(self.nor)
            f.update({16:2,24:1,28:1,32:address,40:oldcrc,44:newcrc,52:oldcrc,80:f[80]+4096})
            raw=self.status(opcode)
        elif opcode==0xFB7C:
            token,seq,address,n=struct.unpack_from(">IIIH",cdb,2)
            assert (token,seq,address,n)==(1,2,0x4000,256)
            self.staged_packet=data_out
            f.update({16:4,28:seq,36:address,48:zlib.crc32(data_out[:256]),52:zlib.crc32(data_out[:256]),
                      88:260,100:1,104:0});raw=b""
        elif opcode==0xFD87:
            assert self.staged_packet is not None
            f[104]=1;raw=self.staged_packet[:256]
            if self.echo_mutator:raw=self.echo_mutator(raw)
        elif opcode==0xFC7E:raw=self.status(opcode)
        elif opcode==0xFD88:
            raw=encoded_record(f)
            if self.record_mutator:raw=self.record_mutator(raw)
        else:raise AssertionError("unexpected fake writer opcode")
        if self.reply_mutator:raw=self.reply_mutator(opcode,raw)
        if opcode==self.fail_after:raise TimeoutError("mock lost reply after command was accepted")
        return raw


class WriterObserverProtocolTests(unittest.TestCase):
    def fresh(self):
        observation=fixture();fake=FakeWriter(observation)
        session=probe.MiniAppWriterObserverSession(fake,observation,known_free_slot=True)
        return fake,session

    def started(self,phase="identified"):
        fake,session=self.fresh()
        with patch("time.sleep"):
            session.upload_and_start(IMAGE,expected_sha256=probe.sha(IMAGE))
        for target,method in (("initialized",session.initialize_spi),("preimage_verified",session.read_first_sector),
                              ("armed",session.arm_first_sector),("observed",session.stage_first_page)):
            if session.phase==phase:break
            method()
        self.assertEqual(session.phase,phase)
        return fake,session

    def assert_terminal(self,fake,session,method):
        count=len(fake.commands)
        self.assertTrue(session.failed)
        with self.assertRaises(ValueError):method()
        self.assertEqual(len(fake.commands),count)

    def test_exact_wire_vectors_and_ram_lifecycle(self):
        page=NEW[:256];packet=probe.stage_packet(page)
        vectors=[(probe.simple_cdb(0xFC78),None,16),(probe.simple_cdb(0xFC79),None,16),
            (probe.arm_cdb(0x4000,0x12345678,0xAABBCCDD),None,16),
            (probe.stage_cdb(1,2,0x4000),packet,0),(probe.echo_cdb(1,2,0x4000),None,256),
            (probe.simple_cdb(0xFC7E),None,16),(probe.read_cdb(0x4000,512),None,512),
            (probe.simple_cdb(0xFD88),None,128)]
        self.assertEqual(vectors[2][0].hex(),"fc7a0000400012345678aabbccddffff")
        self.assertEqual(vectors[3][0].hex(),"fb7c0000000100000002000040000100")
        self.assertEqual(vectors[4][0].hex(),"fd87000000010000000200004000ffff")
        self.assertEqual(vectors[6][0].hex(),"fd7f000040000200ffffffffffffffff")
        self.assertEqual(packet[-4:],zlib.crc32(page).to_bytes(4,"big"))
        for cdb,data,n in vectors:
            probe.validate_writer_observer_request(cdb,data,n,slot=SLOT)
            with self.assertRaises(ValueError):recovery.validate_ram_request(cdb,data,n,slot=SLOT)
        lifecycle=[(bytes((0x12,0,0,0,36,0)),None,36),
            (recovery.ram_write_cdb(SLOT,b"ab",slot=SLOT),b"ab",0),
            (recovery.rom_read_cdb(SLOT,2,slot=SLOT),None,2),(recovery.ram_jump_cdb(SLOT),None,16)]
        for cdb,data,n in lifecycle:probe.validate_writer_observer_request(cdb,data,n,slot=SLOT)

    def test_all_mutators_arbitrary_read_and_legacy_commands_rejected(self):
        for op in (0xFC7B,0xFC7D,0xFC80,0xFD61,0xFC70,0xFD71,0xFC72,0xFB01,0xFC12,0xFC60):
            with self.subTest(op=hex(op)),self.assertRaises(ValueError):
                probe.validate_writer_observer_request(op.to_bytes(2,"big")+b"\xff"*14,None,16,slot=SLOT)

    def test_directions_lengths_padding_and_stage_crc_are_strict(self):
        stage=probe.stage_cdb(1,2,0x4000);packet=probe.stage_packet(NEW[:256])
        vectors=[(stage,None,260),(stage,packet,16),(stage,packet[:-1],0),
            (stage,packet[:-1]+bytes([packet[-1]^1]),0),(stage,bytearray(packet),0),
            (probe.simple_cdb(0xFC78),b"",16),(probe.simple_cdb(0xFC78),None,128),
            (probe.simple_cdb(0xFD88),None,16),(probe.echo_cdb(1,2,0x4000),None,255),
            (probe.read_cdb(0x4000,512),None,511)]
        for cdb,data,n in vectors:
            with self.subTest(cdb=cdb.hex(),n=n),self.assertRaises(ValueError):
                probe.validate_writer_observer_request(cdb,data,n,slot=SLOT)
        for cdb,n in ((probe.simple_cdb(0xFC78),16),(probe.arm_cdb(0x4000,0,0),16),
                      (probe.echo_cdb(1,2,0x4000),256),(probe.read_cdb(0x4000,1),1)):
            for bad in (cdb[:-1]+b"\0",cdb+b"\xff",cdb[:-1]):
                with self.assertRaises(ValueError):probe.validate_writer_observer_request(bad,None,n,slot=SLOT)

    def test_address_boundaries_and_sequence_do_not_wrap(self):
        for address,length in ((0x3fff,1),(0x82000,1),(0x81fff,2),(0x4000,0),(0x4000,513)):
            with self.assertRaises(ValueError):probe.read_cdb(address,length)
        for address in (0x4001,0x81f00,0x82000):
            with self.assertRaises(ValueError):probe.arm_cdb(address,0,0)
        for args in ((0,2,0x4000),(1,1,0x4000),(1,0x100000000,0x4000),(1,2,0x4001),(True,2,0x4000)):
            with self.assertRaises(ValueError):probe.stage_cdb(*args)
        probe.read_cdb(0x81fff,1);probe.arm_cdb(0x81000,0,0);probe.stage_cdb(1,2,0x81f00)

    def test_upload_handshake_has_no_spi_and_uses_only_pinned_payload(self):
        fake,session=self.fresh()
        for payload in (b"another image",IMAGE[:-1]):
            with self.assertRaises(ValueError):session.upload_and_start(payload,expected_sha256=probe.sha(payload))
        self.assertEqual(fake.commands,[])
        with patch("time.sleep"):
            result=session.upload_and_start(IMAGE,expected_sha256=probe.sha(IMAGE))
        self.assertEqual(fake.commands[-3:],[0xFB08,0xFC78,0xFD88])
        self.assertNotIn(0xFC79,fake.commands)
        self.assertFalse(result["SPI_initialized_on_entry"])
        self.assertFalse(result["target_mutations_enabled"])
        self.assertEqual(session.audit_records[-1]["raw_receive_return"],-2147483648)
        with self.assertRaises(ValueError):session.read(SLOT,16)
        with self.assertRaises(ValueError):session.start_reset_once(b"any",elf=b"",manifest={})

    def test_full_gate_zero_observation_matches_backup_echo_and_counters(self):
        fake,session=self.started("observed")
        result=session.last_result
        self.assertTrue(result["observation_passed"])
        self.assertFalse(result["operational_writer_qualified"])
        self.assertEqual(session.last_sector,OLD);self.assertEqual(session.last_echo,NEW[:256])
        self.assertEqual(session.read_bytes,8192)
        self.assertEqual((session.token,session.sequence),(1,2))
        self.assertTrue(session.arm_consumed_for_stage and session.stage_submitted and session.echo_verified)
        self.assertEqual(fake.commands.count(0xFB7C),1)
        self.assertEqual(fake.commands.count(0xFC7A),1)
        self.assertEqual(fake.commands.count(0xFD7F),8)
        self.assertEqual(fake.commands[-5:],[0xFB7C,0xFC7E,0xFD88,0xFD87,0xFD88])
        self.assertEqual(len(session.raw_records),13)
        for item in session.audit_records:
            self.assertEqual((item["wren_attempts"],item["erase_attempts"],item["program_attempts"]),(0,0,0))
        count=len(fake.commands)
        for method in (session.initialize_spi,session.read_first_sector,session.arm_first_sector,session.stage_first_page):
            with self.assertRaises(ValueError):method()
        self.assertEqual(len(fake.commands),count)

    def test_identity_requires_exact_gate_zero_before_init(self):
        fake,session=self.fresh();fake.identity_gate=1
        with patch("time.sleep"),self.assertRaises(ValueError):
            session.upload_and_start(IMAGE,expected_sha256=probe.sha(IMAGE))
        self.assertTrue(session.failed);self.assertNotIn(0xFC79,fake.commands)
        self.assertNotIn(0xFD88,fake.commands)

    def test_entry_audit_requires_no_preexisting_initialization_or_arm(self):
        for offset,value in ((56,0xEB6014),(32,0x4000),(40,1),(44,1),(80,1),(112,8),(88,260)):
            fake,session=self.fresh();fake.fields[offset]=value
            with self.subTest(offset=offset),patch("time.sleep"),self.assertRaises(ValueError):
                session.upload_and_start(IMAGE,expected_sha256=probe.sha(IMAGE))
            self.assertTrue(session.failed);self.assertNotIn(0xFC79,fake.commands)
            self.assertIsNotNone(session.last_record)

    def test_init_rejects_wrong_jedec_protection_busy_wel_or_missing_stack_use(self):
        for offset,value in ((56,0xEF6014),(60,1),(60,2),(60,4),(60,0x40),(64,0x40),(112,0)):
            fake,session=self.started();fake.record_mutator=lambda raw,o=offset,v=value:changed_record(raw,o,v)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):session.initialize_spi()
            self.assert_terminal(fake,session,session.initialize_spi)
            self.assertNotIn(0xFD7F,fake.commands)

    def test_read_checks_status_crc_and_counter_for_each_block(self):
        for offset,value in ((80,0),(52,0),(84,1)):
            fake,session=self.started("initialized")
            fake.record_mutator=lambda raw,o=offset,v=value:changed_record(raw,o,v)
            with self.subTest(offset=offset),self.assertRaises(ValueError):session.read_first_sector()
            self.assertEqual(fake.commands.count(0xFD7F),1)
            self.assertEqual(session.last_sector,b"")
            self.assert_terminal(fake,session,session.read_first_sector)

    def test_all_bytes_compared_before_arm_even_if_block_checksums_are_valid(self):
        fake,session=self.started("initialized");fake.nor=bytes([OLD[0]^1])+OLD[1:]
        with self.assertRaisesRegex(ValueError,"differ from accepted backup"):session.read_first_sector()
        self.assertEqual(len(session.last_sector),4096)
        self.assertNotIn(0xFC7A,fake.commands)
        self.assert_terminal(fake,session,session.arm_first_sector)

    def test_short_read_stops_without_status_or_retry(self):
        fake,session=self.started("initialized")
        fake.reply_mutator=lambda op,raw:raw[:-1] if op==0xFD7F else raw
        with self.assertRaises(ValueError):session.read_first_sector()
        self.assertEqual(fake.commands[-1],0xFD7F)
        self.assert_terminal(fake,session,session.read_first_sector)

    def test_arm_status_and_audit_are_bound_to_exact_first_sector_plan(self):
        for offset,value in ((24,2),(28,2),(32,0x5000),(40,0),(44,0),(80,4096)):
            fake,session=self.started("preimage_verified")
            fake.record_mutator=lambda raw,o=offset,v=value:changed_record(raw,o,v)
            with self.subTest(offset=offset),self.assertRaises(ValueError):session.arm_first_sector()
            self.assertTrue(session.arm_submitted)
            self.assertNotIn(0xFB7C,fake.commands)
            self.assert_terminal(fake,session,session.arm_first_sector)

    def test_lost_arm_reply_cannot_rearm_or_stage(self):
        fake,session=self.started("preimage_verified");fake.fail_after=0xFC7A
        with self.assertRaises(TimeoutError):session.arm_first_sector()
        self.assertEqual(fake.fields[24],1);self.assertTrue(session.arm_submitted)
        self.assertEqual(session.ambiguous_operation,"arm_first_sector")
        self.assert_terminal(fake,session,session.arm_first_sector)
        self.assert_terminal(fake,session,session.stage_first_page)

    def test_stage_timeout_consumes_sequence_before_submission_no_retry(self):
        for side in ("fail_before","fail_after"):
            fake,session=self.started("armed");setattr(fake,side,0xFB7C)
            with self.subTest(side=side),self.assertRaises(TimeoutError):session.stage_first_page()
            self.assertEqual(session.sequence,2)
            self.assertTrue(session.arm_consumed_for_stage and session.stage_submitted)
            self.assertFalse(session.stage_confirmed or session.echo_requested)
            self.assertEqual(fake.commands[-1],0xFB7C)
            self.assertEqual(session.ambiguous_operation,"stage_and_echo_first_page")
            self.assert_terminal(fake,session,session.stage_first_page)

    def test_status_error_is_retained_and_does_not_fall_through_to_echo(self):
        fake,session=self.started("armed")
        def bad_status(op,raw):
            if op==0xFC7E:return raw[:2]+bytes((13,6))+raw[4:]
            return raw
        fake.reply_mutator=bad_status
        with self.assertRaises(ValueError):session.stage_first_page()
        self.assertEqual(session.last_status["error"],13)
        self.assertEqual(session.last_status_raw[2],13)
        self.assertNotIn(0xFD87,fake.commands)
        self.assert_terminal(fake,session,session.stage_first_page)

    def test_staging_requires_exact_receive_count_guards_crc_and_phase(self):
        for offset,value in ((88,0),(88,259),(88,261),(88,0xFFFFFFFF),(92,0),(108,0),
                             (36,0x4100),(48,0),(100,0),(104,1),(16,2)):
            fake,session=self.started("armed")
            fake.record_mutator=lambda raw,o=offset,v=value:changed_record(raw,o,v)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):session.stage_first_page()
            self.assertNotIn(0xFD87,fake.commands)
            self.assertIsNotNone(session.last_record)
            self.assert_terminal(fake,session,session.stage_first_page)

    def test_echo_exact_bytes_and_post_echo_record_are_both_required(self):
        for mode in ("short","changed","unmarked","late_guard"):
            fake,session=self.started("armed")
            if mode=="short":fake.echo_mutator=lambda raw:raw[:-1]
            elif mode=="changed":fake.echo_mutator=lambda raw:bytes([raw[0]^1])+raw[1:]
            else:
                def mutate(raw):
                    if fake.fields.get(104):return changed_record(raw,104 if mode=="unmarked" else 92,0)
                    return raw
                fake.record_mutator=mutate
            with self.subTest(mode=mode),self.assertRaises(ValueError):session.stage_first_page()
            self.assertEqual(fake.commands.count(0xFD87),1)
            self.assertTrue(session.echo_requested);self.assertFalse(session.echo_verified)
            self.assertIsNotNone(session.last_echo)
            self.assert_terminal(fake,session,session.stage_first_page)

    def test_mutation_counters_gate_build_tag_and_record_crc_reject(self):
        for offset,value in ((68,1),(72,1),(76,1),(116,1),(12,TAG^1),(8,SLOT+32768)):
            fake,session=self.started("initialized")
            fake.record_mutator=lambda raw,o=offset,v=value:changed_record(raw,o,v)
            with self.subTest(offset=offset),self.assertRaises(ValueError):session.read_first_sector()
            self.assertEqual(session.last_record,session.raw_records[-1])
            self.assert_terminal(fake,session,session.read_first_sector)
        fake,session=self.started("initialized")
        fake.record_mutator=lambda raw:raw[:120]+bytes([raw[120]^1])+raw[121:]
        with self.assertRaisesRegex(ValueError,"CRC differs"):session.read_first_sector()
        self.assertEqual(len(session.raw_records),3)
        self.assertEqual(len(session.audit_records),2)

    def test_each_remaining_transport_timeout_is_terminal_without_retry(self):
        for phase,op,method_name in (("identified",0xFC79,"initialize_spi"),("identified",0xFD88,"initialize_spi"),
            ("initialized",0xFD7F,"read_first_sector"),("initialized",0xFC7E,"read_first_sector"),
            ("armed",0xFC7E,"stage_first_page"),("armed",0xFD88,"stage_first_page"),
            ("armed",0xFD87,"stage_first_page")):
            fake,session=self.started(phase);fake.fail_after=op;method=getattr(session,method_name)
            with self.subTest(phase=phase,op=hex(op)),self.assertRaises(TimeoutError):method()
            self.assertEqual(fake.commands[-1],op)
            self.assert_terminal(fake,session,method)

    def test_local_preflight_validates_real_frozen_artifact_and_current_plan(self):
        observation=probe.prepare_observation()
        self.assertEqual(observation.slot,SLOT)
        self.assertEqual(len(observation.preimage),4096)
        self.assertEqual(len(observation.page),256)
        self.assertFalse(observation.summary()["NVM_commands_available"])
        with self.assertRaises(ValueError):replace(observation,image=observation.image+b"\0")

    def test_tampered_manifest_plan_source_or_artifact_is_refused_offline(self):
        manifest=json.loads((ROOT/"research/mini-app-writer.json").read_text())
        with tempfile.TemporaryDirectory(dir=ROOT/"build",prefix="test-writer-observer-") as directory:
            path=Path(directory)/"writer.json"
            for change in (lambda m:m.update(target_mutations_enabled=True),
                           lambda m:m["install_plan"].update(sha256="0"*64),
                           lambda m:m["source_sha256"].update({next(iter(m["source_sha256"])):"0"*64}),
                           lambda m:m["executable_artifacts"][0].update(payload_sha256="0"*64)):
                altered=json.loads(json.dumps(manifest));change(altered);path.write_text(json.dumps(altered))
                with self.assertRaises(ValueError):probe.prepare_observation(writer_manifest_path=path)

    def test_default_cli_is_offline_and_constructor_uses_separate_profile(self):
        run=subprocess.run([sys.executable,"-X","utf8",str(ROOT/"tools/probe_mini_app_writer.py")],
                           cwd=ROOT,capture_output=True,text=True,check=True)
        result=json.loads(run.stdout)
        self.assertFalse(result["device_io"]);self.assertFalse(result["enumerated"])
        self.assertFalse(result["erase_program_finish_commands_available"])
        with patch.object(recovery.WindowsRomTransport,"__init__",return_value=None) as init:
            probe.WindowsWriterObserverTransport("fake-device-never-opened",slot=SLOT)
        init.assert_called_once_with("fake-device-never-opened",slot=SLOT,profile="app-writer-observer")


if __name__=="__main__":unittest.main()
