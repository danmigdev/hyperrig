"""Resolve a lost PROGRAM reply using fake RAM audits, never hardware I/O."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'analysis/hardware'),str(ROOT/'tools')]
spec=importlib.util.spec_from_file_location('mini_partial_inspect6',
    ROOT/'analysis/hardware/read_mini_partial_install6.py')
inspect=importlib.util.module_from_spec(spec);spec.loader.exec_module(inspect)
from tests.test_mini_app_writer_protocol import encoded_record,changed_record

TAG=3953063795


def prior_record():
    return encoded_record({4:1,8:inspect.A,12:TAG,16:4,20:0,24:6,28:33,
        32:0x54000,36:0x54F00,40:0xD64BF9A2,44:0x3E61397C,
        48:0x978A52DB,52:0x978A52DB,56:0xEB6014,60:0,64:2,
        68:101,72:6,76:95,80:752896,84:1067,88:260,92:1,
        96:0x7FFF,100:1,104:1,108:1,112:52,116:1})


def completed_record(polls=1074):
    return encoded_record({4:1,8:inspect.A,12:TAG,16:3,20:0,24:6,28:34,
        32:0x54000,36:0x54F00,40:0xD64BF9A2,44:0x3E61397C,
        48:0x978A52DB,52:0x978A52DB,56:0xEB6014,60:0,64:2,
        68:102,72:6,76:96,80:753408,84:polls,88:260,92:1,
        96:0xFFFF,100:0,104:0,108:1,112:112,116:1})


class FakeWriter:
    def __init__(self,raw,*,bad_identity=False,fail=None):
        self.raw,self.bad_identity,self.fail=raw,bad_identity,fail
        self.commands=[]

    def exchange(self,cdb,data_out=None,read_length=0):
        op=int.from_bytes(cdb[:2],'big');self.commands.append(op)
        assert data_out is None and cdb[2:]==b'\xff'*14
        if op==self.fail:raise TimeoutError('mock transport failure')
        if op==0xFC78:
            assert read_length==16
            return b'\xfc\x78'+(b'BAD!' if self.bad_identity else b'HYW1')+b'\1\1'+struct.pack('>II',inspect.A,32768)
        if op==0xFD88:
            assert read_length==128
            return self.raw
        raise AssertionError('inspector submitted non-audit command')


class Inspect6Tests(unittest.TestCase):
    def confirm(self,raw):
        fake,retained=FakeWriter(raw),[]
        result=inspect.confirm_writer(fake,prior_record(),build_tag=TAG,retain=retained.append)
        self.assertEqual(fake.commands,[0xFC78,0xFD88])
        self.assertEqual(retained,[raw])
        return result

    def test_prior_wire_fixture_matches_last_validated_hardware_record(self):
        self.assertEqual(inspect.sha(prior_record()),'61b502e93f80ba0a432067c173aaebab5d1b7d8c72ec2cc0e40c76ce0f6f755c')

    def test_unchanged_prior_state_retained_without_program_retry(self):
        record,outcome=self.confirm(prior_record())
        self.assertEqual(outcome,'prior_state_retained')
        self.assertEqual(record['program_attempts'],95)
        self.assertEqual(record['stack_observed_bytes'],52)

    def test_exact_successful_program_delta_with_bounded_poll_values(self):
        for polls in (1068,1074,1067+65536):
            with self.subTest(polls=polls):
                expected=completed_record(polls)
                self.assertEqual(inspect.completed_program_record(prior_record(),build_tag=TAG,polls=polls),expected)
                record,outcome=self.confirm(expected)
                self.assertEqual(outcome,'program_completed')
                self.assertEqual((record['sequence'],record['wren_attempts'],record['program_attempts'],
                                  record['read_bytes'],record['page_bitmap'],record['stack_observed_bytes']),
                                 (34,102,96,753408,65535,112))

    def test_no_zero_or_excessive_poll_increment_for_completed_program(self):
        for polls in (0,1066,1067,1067+65537,0xFFFFFFFF):
            fake=FakeWriter(completed_record(polls));retained=[]
            with self.subTest(polls=polls),self.assertRaises(ValueError):
                inspect.confirm_writer(fake,prior_record(),build_tag=TAG,retain=retained.append)
            self.assertEqual(fake.commands,[0xFC78,0xFD88]);self.assertEqual(len(retained),1)

    def test_every_other_completed_field_change_rejected_with_correct_crc(self):
        base=completed_record()
        for offset in range(4,120,4):
            if offset==84:continue
            value=struct.unpack_from('<I',base,offset)[0]^1
            fake=FakeWriter(changed_record(base,offset,value))
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                inspect.confirm_writer(fake,prior_record(),build_tag=TAG,retain=lambda _:None)
            self.assertEqual(fake.commands,[0xFC78,0xFD88])

    def test_partial_program_states_are_not_reconciled_as_completed(self):
        for changes in ({28:34},{28:34,80:753152},{28:34,100:0,104:0},
                        {28:34,100:0,104:0,68:102},
                        {28:34,100:0,104:0,68:102,76:96,80:753152},
                        {28:34,16:6,20:14}):
            raw=prior_record()
            for offset,value in changes.items():raw=changed_record(raw,offset,value)
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.confirm(raw)

    def test_stack_busy_wel_protection_error_or_guard_damage_stops_handoff(self):
        for offset,value in ((112,52),(112,108),(112,116),(60,1),(60,2),(60,4),(64,0x40),(92,0),(108,0)):
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):
                self.confirm(changed_record(completed_record(),offset,value))

    def test_old_state_cannot_change_one_field_and_claim_not_executed(self):
        for offset in range(4,120,4):
            value=struct.unpack_from('<I',prior_record(),offset)[0]^1
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                self.confirm(changed_record(prior_record(),offset,value))

    def test_identity_failure_does_not_read_audit_or_handoff(self):
        fake=FakeWriter(prior_record(),bad_identity=True)
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake,prior_record(),build_tag=TAG,retain=lambda _:None)
        self.assertEqual(fake.commands,[0xFC78])

    def test_transport_or_evidence_failure_never_retries(self):
        for fail in (0xFC78,0xFD88):
            fake=FakeWriter(prior_record(),fail=fail)
            with self.subTest(fail=fail),self.assertRaises(TimeoutError):
                inspect.confirm_writer(fake,prior_record(),build_tag=TAG,retain=lambda _:None)
            self.assertEqual(fake.commands.count(fail),1)
        fake=FakeWriter(completed_record())
        def blocked(_):raise OSError('raw evidence could not be saved')
        with self.assertRaises(OSError):
            inspect.confirm_writer(fake,prior_record(),build_tag=TAG,retain=blocked)
        self.assertEqual(fake.commands,[0xFC78,0xFD88])


if __name__=='__main__':unittest.main()
