"""One guarded FD7F/Win31 reissue, tested only against fake ROM/NOR handles."""
import unittest
from unittest.mock import patch

from tools import recover_mini_read as recovery
from tools import install_mini_app as installer
from tools.probe_mini_recovery import RomCommandError
from tools.probe_mini_app_writer import simple_cdb,read_cdb
from tests.test_mini_app_install import FakeOperational,fixture,IMAGE
from tests.test_mini_app_writer_protocol import changed_record


def failure(code=31,submitted=True):
    return RomCommandError(code,"mock SCSI failure",submitted=submitted,
        details={"scsi_status":0,"data_transfer_length":256,"bytes_returned":0,"sense_info_length":32,"sense_hex":"00"*32})


class Handle:
    def __init__(self,device):
        self.device=device;self.slot=device.slot;self.profile="app-writer-operational"
        self.disk={"path":r"\\.\PhysicalDrive42"};self.inquiry={"vendor":"WL82","product":"UBOOT1.00"}
        self.closed=False;self.calls=[];self.fail_before=None;self.fail_after=None;self.reply_change=None

    def exchange(self,cdb,data_out=None,read_length=0):
        assert not self.closed
        op=int.from_bytes(cdb[:2],"big");self.calls.append((op,cdb,data_out,read_length))
        if self.fail_before is not None:
            error=self.fail_before(op)
            if error:raise error
        raw=self.device.exchange(cdb,data_out,read_length)
        if self.fail_after is not None:
            error=self.fail_after(op)
            if error:raise error
        return self.reply_change(op,raw) if self.reply_change else raw

    def close(self):self.closed=True


class GuardedReadRecoveryTests(unittest.TestCase):
    def live(self,*,preflight=False,new_configure=None):
        device=FakeOperational(fixture());old=Handle(device);handles=[old];events=[];journal=[]
        def reopen():
            new=Handle(device);handles.append(new)
            if new_configure:new_configure(new)
            return new
        wrapper=recovery.ReadOnlyFailureRecoveryTransport(old,log=events.append,reopen_factory=reopen)
        session=installer.MiniAppInstallerSession(wrapper,fixture(),journal=journal.append,known_free_slot=True)
        wrapper.bind_session(session)
        with patch("time.sleep"):session.upload_and_start(IMAGE,expected_sha256=installer.sha(IMAGE))
        session.initialize_spi()
        if preflight:session.verify_complete_preimage()
        return device,old,handles,wrapper,session,events

    def test_one_unexecuted_read_can_be_reissued_after_exact_identity_and_audit(self):
        device,old,handles,wrapper,session,events=self.live()
        old.fail_before=lambda op:failure() if op==0xFD7F else None
        session.verify_complete_preimage()
        self.assertTrue(session.preimage_verified)
        self.assertEqual((wrapper.recovery_attempts,wrapper.read_reissues),(1,1))
        self.assertEqual(len(handles),2);self.assertTrue(old.closed)
        self.assertEqual([row[0] for row in handles[1].calls[:3]],[0xFC78,0xFD88,0xFD7F])
        old_read=next(row for row in old.calls if row[0]==0xFD7F)
        self.assertEqual(old_read[1:],handles[1].calls[2][1:])
        self.assertEqual(device.fields[80],len(session.installation.preimage))
        self.assertTrue(any(e["event"]=="read_recovery_unchanged_audit" for e in events))
        self.assertEqual(device.commands.count(0xFB08),1)
        wrapper.close();self.assertTrue(handles[1].closed)

    def test_failed_read_that_executed_changes_counter_and_cannot_be_reissued(self):
        device,old,handles,wrapper,session,events=self.live()
        old.fail_after=lambda op:failure() if op==0xFD7F else None
        with self.assertRaisesRegex(ValueError,"audit changed"):session.verify_complete_preimage()
        self.assertEqual(device.fields[80],512)
        self.assertEqual(wrapper.read_reissues,0)
        self.assertEqual([r[0] for r in handles[1].calls],[0xFC78,0xFD88])
        self.assertTrue(session.failed and wrapper.failed)

    def test_actual_install_recovers_only_post_program_read_and_never_repeats_mutations(self):
        device,old,handles,wrapper,session,events=self.live(preflight=True)
        old.fail_before=lambda op:failure() if op==0xFD7F and len(device.program_addresses)==10 else None
        result=session.install_application()
        self.assertTrue(result["application_verified"])
        self.assertEqual(device.erase_addresses,[0x5000,0x4000])
        self.assertEqual(len(device.program_addresses),32)
        self.assertEqual(len(set(device.program_addresses)),32)
        self.assertEqual((result["wren_attempts"],result["erase_attempts"],result["program_attempts"]),(34,2,32))
        self.assertEqual(wrapper.read_reissues,1)
        self.assertFalse(session.mutation_completion_unknown)

    def test_mutation_stage_finish_jump_or_other_opcode_never_reopens(self):
        for op in (0xFC7B,0xFC7D,0xFB7C,0xFC80):
            device,old,handles,wrapper,session,_events=self.live(preflight=True)
            old.fail_before=lambda actual,wanted=op:failure() if actual==wanted else None
            with self.subTest(op=op),self.assertRaises(RomCommandError):session.install_application()
            self.assertEqual(len(handles),1);self.assertEqual(wrapper.recovery_attempts,0)
            self.assertTrue(session.failed and wrapper.failed)
        for op in (0xFC78,0xFD88,0xFB08):
            device=FakeOperational(fixture());old=Handle(device)
            wrapper=recovery.ReadOnlyFailureRecoveryTransport(old,log=lambda e:None,reopen_factory=lambda:self.fail("reopened"))
            session=installer.MiniAppInstallerSession(wrapper,fixture(),journal=lambda e:None,known_free_slot=True);wrapper.bind_session(session)
            old.fail_before=lambda actual,wanted=op:failure() if actual==wanted else None
            with self.subTest(op=op),patch("time.sleep"),self.assertRaises(RomCommandError):
                session.upload_and_start(IMAGE,expected_sha256=installer.sha(IMAGE))
            self.assertEqual(wrapper.recovery_attempts,0)

    def test_other_win32_errors_or_presubmission_error31_are_terminal(self):
        for code,submitted in ((121,True),(5,True),(31,False)):
            _device,old,handles,wrapper,session,_events=self.live()
            old.fail_before=lambda op:failure(code,submitted) if op==0xFD7F else None
            with self.subTest(code=code,submitted=submitted),self.assertRaises(RomCommandError):session.verify_complete_preimage()
            self.assertEqual(len(handles),1);self.assertTrue(wrapper.failed)

    def test_audit_must_be_immediately_previous_and_validated_by_bound_installer(self):
        for mode in ("intervening","raw_only","wrong_expected","unbound"):
            _device,old,handles,wrapper,session,_events=self.live()
            if mode=="intervening":wrapper.exchange(simple_cdb(0xFC78),read_length=16)
            elif mode=="raw_only":session.last_audit=None
            elif mode=="wrong_expected":session.expected["read_bytes"]=1
            else:wrapper.session=None
            old.fail_before=lambda op:failure() if op==0xFD7F else None
            with self.subTest(mode=mode),self.assertRaises(RomCommandError):session.verify_complete_preimage()
            self.assertEqual(len(handles),1);self.assertEqual(wrapper.read_reissues,0)

    def test_reopened_identity_path_slot_and_gate_must_match(self):
        for mode in ("path","slot","profile","inquiry","gate"):
            def configure(handle):
                if mode=="path":handle.disk={"path":r"\\.\PhysicalDrive43"}
                elif mode=="slot":handle.slot+=32768
                elif mode=="profile":handle.profile="nor-reader"
                elif mode=="inquiry":handle.inquiry={"vendor":"wrong","product":"UBOOT1.00"}
                else:handle.reply_change=lambda op,raw:raw[:7]+b"\0"+raw[8:] if op==0xFC78 else raw
            _device,old,handles,wrapper,session,_events=self.live(new_configure=configure)
            old.fail_before=lambda op:failure() if op==0xFD7F else None
            with self.subTest(mode=mode),self.assertRaises(ValueError):session.verify_complete_preimage()
            self.assertEqual(wrapper.read_reissues,0)
            self.assertNotIn(0xFD7F,[r[0] for r in handles[1].calls])

    def test_changed_build_tag_corrupt_or_sticky_audit_blocks_reissue(self):
        for offset,value in ((12,1),(20,1),(80,512),(120,0)):
            def configure(handle):
                def change(op,raw):
                    if op!=0xFD88:return raw
                    if offset==120:return raw[:120]+bytes([raw[120]^1])+raw[121:]
                    return changed_record(raw,offset,value)
                handle.reply_change=change
            _device,old,handles,wrapper,session,_events=self.live(new_configure=configure)
            old.fail_before=lambda op:failure() if op==0xFD7F else None
            with self.subTest(offset=offset),self.assertRaises(ValueError):session.verify_complete_preimage()
            self.assertEqual(wrapper.read_reissues,0)

    def test_second_failure_during_reissued_read_does_not_recurse(self):
        def configure(handle):handle.fail_before=lambda op:failure() if op==0xFD7F else None
        _device,old,handles,wrapper,session,_events=self.live(new_configure=configure)
        old.fail_before=lambda op:failure() if op==0xFD7F else None
        with self.assertRaises(RomCommandError):session.verify_complete_preimage()
        self.assertEqual((len(handles),wrapper.recovery_attempts,wrapper.read_reissues),(2,1,1))
        self.assertTrue(session.failed and wrapper.failed)
        count=len(handles[1].calls)
        with self.assertRaises(ValueError):wrapper.exchange(read_cdb(0x4000,512),read_length=512)
        self.assertEqual(len(handles[1].calls),count)

    def test_one_total_recovery_budget_not_reset_after_success(self):
        def configure(handle):
            attempts=[0]
            def fail(op):
                if op==0xFD7F:
                    attempts[0]+=1
                    if attempts[0]==2:return failure()
            handle.fail_before=fail
        _device,old,handles,wrapper,session,_events=self.live(new_configure=configure)
        old.fail_before=lambda op:failure() if op==0xFD7F else None
        with self.assertRaises(RomCommandError):session.verify_complete_preimage()
        self.assertEqual((len(handles),wrapper.recovery_attempts,wrapper.read_reissues),(2,1,1))

    def test_journal_failure_prevents_recovery_device_operations(self):
        _device,old,handles,wrapper,session,_events=self.live()
        old.fail_before=lambda op:failure() if op==0xFD7F else None
        def fail(_event):raise OSError("recovery log cannot be persisted")
        wrapper.log=fail
        with self.assertRaises(OSError):session.verify_complete_preimage()
        self.assertEqual(len(handles),1);self.assertFalse(old.closed)
        self.assertEqual(wrapper.read_reissues,0)


if __name__=="__main__":unittest.main()
