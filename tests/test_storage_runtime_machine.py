"""Independent original witnesses for joined storage and private-byte knowledge."""
import sys
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from storage_runtime_machine import StorageRuntimeProgram,JOINS,ALL_REGIONS,derivative_sources
from verify_storage_runtime import initial,Script,SERVICES,STATE,INPUT,FLASH,record,populated_flash,getword


class StorageRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program=StorageRuntimeProgram();SERVICES.update({t:n for t,n in cls.program.service_sites.values()})
    def native(self,name,args=(),memory=None,services=10000,events=1000000,**kw):
        script=Script(**kw)
        result=self.program.execute(initial() if memory is None else memory,name,args,boundary=script.call,events=script.event,
            services=services,event_budget=events)
        return result,script
    def test_no_new_original_bodies(self):
        self.assertEqual(len(ALL_REGIONS),75);self.assertEqual(len(self.program.code),2283)
        self.assertEqual(len(JOINS),18);self.assertEqual(len(self.program.service_sites),35)
    def test_exact_derivatives(self):self.assertEqual(derivative_sources()['checked_complete_derivatives'],2)
    def test_unapproved_parent_algorithm_change_rejected(self):
        original=Path.read_text
        def changed(path,*a,**kw):
            text=original(path,*a,**kw)
            return text.replace('if(pair>15u','if(pair>14u') if path.name=='hyperrig_storage_runtime.c' else text
        with mock.patch.object(Path,'read_text',changed):
            with self.assertRaises(ValueError):derivative_sources()
    def test_unapproved_driver_count_change_rejected(self):
        original=Path.read_text
        def changed(path,*a,**kw):
            text=original(path,*a,**kw)
            return text.replace('UINT32_C(50000000)','UINT32_C(5000000)') if path.name=='hyperrig_storage_runtime_control.c' else text
        with mock.patch.object(Path,'read_text',changed):
            with self.assertRaises(ValueError):derivative_sources()
    def test_cached_prepare_needs_no_external_allowance(self):
        r,s=self.native('prepare',services=0,events=0);self.assertEqual(r['status'],0);self.assertEqual(s.actions,[])
    def test_internal_read_join_does_not_spend_service_allowance(self):
        r,_=self.native('read_forward',(FLASH,INPUT,0),services=3,events=0)
        self.assertEqual(r['status'],0);self.assertEqual(len(r['calls']),3);self.assertEqual(r['services_remaining'],0)
    def test_shared_service_exhaustion(self):
        r,_=self.native('record_copy',(FLASH,INPUT),services=2)
        self.assertEqual(r['status'],-203);self.assertEqual(len(r['calls']),2)
        self.assertEqual(r['result'],None);self.assertTrue(r['active_leases'])
    def test_shared_event_exhaustion(self):
        r,_=self.native('record_copy',(FLASH,INPUT),events=20)
        self.assertEqual(r['status'],-203);self.assertEqual(len(r['events']),20)
        self.assertEqual(getword(r['memory'],STATE+22,1),1)
    def test_actual_read_initializes_private_header(self):
        r,_=self.native('record_copy',(FLASH,INPUT),flash=populated_flash())
        self.assertEqual(r['status'],0);self.assertEqual(r['result'],(48,0))
        for i,b in enumerate(record(8)[:40]):self.assertEqual(r['private_known'][hex(0x30000fc8+i)],b)
    def test_success_without_data_is_not_initialization(self):
        r,s=self.native('record_copy',(FLASH,INPUT),mode=8)
        self.assertEqual(r['status'],-202);self.assertEqual(r['stop_pc'],0x020077be)
        self.assertEqual(r['private_known'],{});self.assertFalse(r['active_leases'])
        self.assertEqual(len(s.actions),25)
    def test_partial_private_read_has_only_written_prefix(self):
        r,_=self.native('record_copy',(FLASH,INPUT),events=120,flash=populated_flash())
        known=[a for a in map(lambda x:int(x,16),r['private_known']) if 0x30000fc8<=a<0x30000ff0]
        self.assertGreater(len(known),0);self.assertLess(len(known),40)
        self.assertEqual(known,list(range(0x30000fc8,0x30000fc8+len(known))))
    def test_platform_callback_cannot_borrow_private_lease(self):
        r,_=self.native('record_copy',(FLASH,INPUT),probes=((('call',0x02040614),0,0x30000fc8,40,1),))
        self.assertEqual(r['status'],-202);self.assertEqual(len(r['calls']),3);self.assertEqual(r['private_known'],{})
    def test_MMIO_callback_cannot_borrow_private_lease(self):
        r,_=self.native('record_copy',(FLASH,INPUT),probes=(((1,0x11c00),0,0x30000fc8,40,1),))
        self.assertEqual(r['status'],-202);self.assertEqual(r['private_known'],{})
    def test_TESTSET_callback_guard_retains_effect_without_cleanup(self):
        r,_=self.native('write_forward',(FLASH,INPUT,1),probes=(((8,STATE+55),0,0x30000fc4,1,0),))
        self.assertEqual(r['status'],-202);self.assertEqual(r['cpu'][1],0x01090500)
        self.assertEqual(getword(r['memory'],STATE+55,1),255)
        self.assertEqual(getword(r['memory'],STATE+1196),0)
        self.assertEqual(getword(r['memory'],STATE+22,1),1)
    def test_program_length_does_not_replace_readback(self):
        r,s=self.native('replace_pair',(0,INPUT,52,0,0),ignore_program=True)
        self.assertEqual(r['result'],(0xfffffffd,0))
        self.assertEqual(s.flash,bytearray([255])*0x40000)
        self.assertEqual(getword(r['memory'],STATE+3492),3)
        self.assertEqual(getword(r['memory'],STATE+3441,1),2)
        self.assertEqual(getword(r['memory'],STATE+3442,1),2)
    def test_destination_wraps_between_byte_stores(self):
        r,_=self.native('read_forward',(FLASH,0xffffffff,2),flash=populated_flash())
        self.assertEqual(r['status'],0)
        self.assertEqual(getword(r['memory'],0xffffffff,1),0x54)
        self.assertEqual(getword(r['memory'],0,1),0x4b)


if __name__=='__main__':unittest.main()
