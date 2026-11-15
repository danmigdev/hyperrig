"""Real MiniNorSession with fake NOR/handles; no discovery or device access."""
from dataclasses import replace
import struct
import unittest

from tools.mini_nor_read_recovery import NorReadRecoveryTransport,query
from tools.probe_mini_recovery import MiniNorSession,RomCommandError,nor_read_cdb
from tools.mini_windows_quiet import RomDiskAttestation
from tests.test_mini_recovery import FakeNor


def failure(code=31,submitted=True):return RomCommandError(code,'fake lost transfer',submitted=submitted)


class Handle:
    def __init__(self,device):
        self.device=device;self.slot=device.slot;self.profile='nor-reader'
        self.attestation=RomDiskAttestation(r'\\.\PhysicalDrive42',r'USBSTOR\MINI',
            r'USB\VID_4C4A&PID_8057\UNIT',(r'USBSTOR\MINI',r'USB\VID_4C4A&PID_8057\UNIT'),
            'WL82 UBOOT1.00',r'\\?\USBSTOR#MINI',1)
        self.disk=self.attestation.discovery_dict();self.inquiry={'vendor':'WL82','product':'UBOOT1.00'}
        self.closed=False;self.calls=[];self.fail_before=self.fail_after=self.reply_change=None
    def exchange(self,cdb,data_out=None,read_length=0):
        assert not self.closed
        op=int.from_bytes(cdb[:2],'big');self.calls.append((op,cdb,read_length))
        if self.fail_before:
            error=self.fail_before(op)
            if error:raise error
        raw=self.device.exchange(cdb,data_out,read_length)
        if self.fail_after:
            error=self.fail_after(op)
            if error:raise error
        return self.reply_change(op,raw) if self.reply_change else raw
    def close(self):self.closed=True


class NorReadRecoveryTests(unittest.TestCase):
    def live(self,*,base=0,new_configure=None,budget=8):
        device=FakeNor();device.initialized=True;device.count=base
        old=Handle(device);handles=[old];events=[]
        def reopen():
            new=Handle(device);handles.append(new)
            if new_configure:new_configure(new)
            return new
        wrapper=NorReadRecoveryTransport(old,log=events.append,reopen_factory=reopen,max_recoveries=budget)
        reader=MiniNorSession(wrapper,slot=device.slot)
        wrapper.attach_retained(reader,expected_counters=(base,),expected_clock=(0,128))
        self.addCleanup(wrapper.close)
        return device,old,handles,wrapper,reader,events

    def test_binding_owns_transport_assignment_after_real_status(self):
        device=FakeNor();old=Handle(device);reader=MiniNorSession(old,slot=device.slot)
        reader.ready=True;status=reader.initialize_spi()
        raw=query(0xfc73)[:2]+b'\0\1'+struct.pack('>III',status['sys_div'],status['clk_con2'],0)
        wrapper=NorReadRecoveryTransport(old,log=lambda _:None,reopen_factory=lambda:Handle(device))
        wrapper.bind_session(reader,status_raw=raw)
        self.assertIs(reader.transport,wrapper)
        self.assertEqual(reader.read_flash(10,513),bytes((10+i)&255 for i in range(513)))
        self.assertEqual(reader.successful_bytes,513);wrapper.close()

    def test_lost_read_before_or_after_execution_reissues_once_with_real_counter(self):
        for executed in (False,True):
            device,old,handles,wrapper,reader,events=self.live(base=0xE3600)
            lose=lambda op:failure() if op==0xFD71 else None
            if executed:old.fail_after=lose
            else:old.fail_before=lose
            raw=reader.read_flash(0,1025)
            self.assertEqual(raw,bytes(i&255 for i in range(1025)))
            self.assertEqual(reader.successful_bytes,device.count)
            self.assertEqual(device.count,0xE3600+1025+512*executed)
            self.assertEqual((wrapper.recovery_attempts,wrapper.read_reissues,wrapper.lost_read_bytes),(1,1,512*executed))
            self.assertEqual([x[0] for x in handles[1].calls[:4]],[0xFC70,0xFC73,0xFD71,0xFC73])
            self.assertFalse(wrapper.failed or reader.failed)

    def test_lost_status_after_received_read_returns_actual_status_without_new_read(self):
        for executed in (False,True):
            device,old,handles,wrapper,reader,events=self.live(base=1234)
            lose=lambda op:failure() if op==0xFC73 else None
            if executed:old.fail_after=lose
            else:old.fail_before=lose
            raw=reader.read_flash(20,512)
            self.assertEqual(raw,bytes((20+i)&255 for i in range(512)))
            self.assertEqual(device.commands.count(0xFD71),1)
            self.assertEqual(reader.successful_bytes,1746)
            self.assertEqual(wrapper.status_reconciliations,1)
            self.assertEqual([x[0] for x in handles[1].calls],[0xFC70,0xFC73])
            self.assertEqual(wrapper.last_status_raw,query(0xfc73)[:2]+b'\0\1'+struct.pack('>III',0,128,1746))

    def test_wrong_counter_clock_error_initialized_or_identity_never_reissues(self):
        for kind in ('counter','sys_div','clk_con2','sticky','uninitialized','identity'):
            def configure(handle):
                def mutate(op,raw):
                    data=bytearray(raw)
                    if op==0xFC70 and kind=='identity':data[2]^=1
                    if op==0xFC73:
                        if kind=='counter':data[15]^=1
                        elif kind=='sys_div':data[7]^=1
                        elif kind=='clk_con2':data[11]^=1
                        elif kind=='sticky':data[2]=2
                        elif kind=='uninitialized':data[3]=0
                    return bytes(data)
                handle.reply_change=mutate
            device,old,handles,wrapper,reader,_=self.live(new_configure=configure)
            old.fail_before=lambda op:failure() if op==0xFD71 else None
            with self.subTest(kind=kind),self.assertRaises(ValueError):reader.read_flash(0,512)
            self.assertNotIn(0xFD71,[x[0] for x in handles[1].calls])
            self.assertTrue(reader.failed and wrapper.failed)

    def test_changed_class_or_attestation_stops_before_plugin_queries(self):
        def configure(handle):handle.attestation=replace(handle.attestation,last_arrival_filetime=2)
        device,old,handles,wrapper,reader,_=self.live(new_configure=configure)
        old.fail_before=lambda op:failure() if op==0xFD71 else None
        with self.assertRaises(ValueError):reader.read_flash(0,512)
        self.assertFalse(handles[1].calls)

    def test_error_during_recovery_or_reissue_is_terminal_no_recursion(self):
        for failed_op in (0xFC70,0xFC73,0xFD71):
            def configure(handle):handle.fail_before=lambda op:failure() if op==failed_op else None
            device,old,handles,wrapper,reader,_=self.live(new_configure=configure)
            old.fail_before=lambda op:failure() if op==0xFD71 else None
            with self.subTest(failed_op=failed_op),self.assertRaises(RomCommandError):reader.read_flash(0,512)
            self.assertEqual(len(handles),2);self.assertEqual(wrapper.recovery_attempts,1)

    def test_non31_timeout_or_not_submitted_never_reopens(self):
        for error in (failure(121),failure(submitted=False),TimeoutError('fake timeout')):
            device,old,handles,wrapper,reader,_=self.live()
            old.fail_before=lambda op:error if op==0xFD71 else None
            with self.subTest(error=error),self.assertRaises((OSError,ValueError)):reader.read_flash(0,512)
            self.assertEqual(len(handles),1)

    def test_no_init_lifecycle_out_or_idle_status_recovery(self):
        for op in (0xFC70,0xFC72,0xFC73):
            device,old,handles,wrapper,reader,_=self.live()
            old.fail_before=lambda actual:failure() if actual==op else None
            with self.subTest(op=op),self.assertRaises((OSError,ValueError)):wrapper.exchange(query(op),read_length=16)
            self.assertEqual(len(handles),1)

    def test_overflow_is_rejected_before_any_read(self):
        device,old,handles,wrapper,reader,_=self.live(base=0xFFFFFF00)
        with self.assertRaises(ValueError):reader.read_flash(0,512)
        self.assertNotIn(0xFD71,device.commands)

    def test_budget_exhaustion_never_reopens_again(self):
        device,old,handles,wrapper,reader,_=self.live(budget=1)
        old.fail_before=lambda op:failure() if op==0xFD71 else None
        reader.read_flash(0,512)
        handles[-1].fail_before=lambda op:failure() if op==0xFD71 else None
        with self.assertRaises(ValueError):reader.read_flash(512,512)
        self.assertEqual(len(handles),2);self.assertEqual(wrapper.recovery_attempts,1)

    def test_pending_read_cannot_be_overwritten_before_its_status(self):
        device,old,handles,wrapper,reader,_=self.live()
        wrapper.exchange(nor_read_cdb(0,512),read_length=512)
        with self.assertRaises(ValueError):wrapper.exchange(nor_read_cdb(512,512),read_length=512)
        self.assertEqual(device.count,512)

    def test_host_counter_cannot_change_between_data_and_status(self):
        device,old,handles,wrapper,reader,_=self.live()
        wrapper.exchange(nor_read_cdb(0,512),read_length=512)
        reader.successful_bytes=512
        calls=len(old.calls)
        with self.assertRaises(ValueError):wrapper.exchange(query(0xFC73),read_length=16)
        self.assertEqual(len(old.calls),calls)

    def test_durable_recovery_log_failure_prevents_reopen(self):
        device,old,handles,wrapper,reader,_=self.live()
        def blocked(_):raise OSError('fake log failure')
        wrapper.log=blocked;old.fail_before=lambda op:failure() if op==0xFD71 else None
        with self.assertRaises(OSError):reader.read_flash(0,512)
        self.assertEqual(len(handles),1)


if __name__=='__main__':unittest.main()
