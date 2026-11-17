"""Focused native evidence and domain checks for storage control."""
import copy
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from storage_control_machine import (StorageControlProgram,REGIONS,TABLES,TABLE_PROOFS,DIRECT_SITES,
 validate_registry,READ,WRITE,FLUSH,DEVICE,STATE,ARENA)
from verify_storage_control import initial,setword,getword,Script

class StorageControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=StorageControlProgram()
    def run_native(self,name,args=(),memory=None,**kw):
        budget=kw.pop('event_budget',1000000);script=Script(**kw)
        result=self.program.execute(initial() if memory is None else memory,name,args,script.call,script.event,budget)
        return result,script
    def test_complete_registry(self):
        self.assertEqual(len(REGIONS),45);self.assertEqual(len(self.program.code),1165)
        self.assertEqual(sum(e-s for s,e in REGIONS.values()),3444)
        self.assertEqual(self.program.service_sites,DIRECT_SITES)
    def test_authenticated_tables(self):
        self.assertEqual(sum(e-s for s,e,*_ in TABLES.values()),32)
        self.assertEqual(sum(count for _,_,count,*_ in TABLES.values()),29)
        validate_registry(self.program)
    def test_reject_changed_table_bytes(self):
        p=copy.copy(self.program);p.data=dict(p.data);p.data['control200']=bytes([0])+p.data['control200'][1:]
        with self.assertRaises(ValueError):validate_registry(p)
    def test_reject_changed_index(self):
        p=copy.copy(self.program);p.code=dict(p.code);entry=0x01c002ae
        p.code[entry]=('r0 = uextra(r5, p:8, l:4)',)+p.code[entry][1:]
        with self.assertRaises(ValueError):validate_registry(p)
    def test_reject_decoded_table_data(self):
        p=copy.copy(self.program);p.code=dict(p.code);p.code[0x02002a2a]=('nop',2,0,0)
        with self.assertRaises(ValueError):validate_registry(p)
    def test_reject_packet_interior_target(self):
        p=copy.copy(self.program);p.parallel_seconds=set(p.parallel_seconds)|{0x02002a32}
        with self.assertRaises(ValueError):validate_registry(p)
    def test_reject_changed_platform_site(self):
        p=copy.copy(self.program);p.service_sites=dict(p.service_sites);p.service_sites[0x0200271e]=(0x020005ac,3)
        with self.assertRaises(ValueError):validate_registry(p)
    def test_power_and_signed_negative(self):
        for n,want in ((0,1),(31,0x80000000),(32,0),(0xffffffff,1)):
            r,_=self.run_native('power2',(n,));self.assertEqual(r['result'],(want,0))
    def test_wrapped_native_range(self):
        r,_=self.run_native('range',(0xffffffff,1));self.assertEqual(r['result'],(1,0))
        r,_=self.run_native('range',(0xbf000,0x40001));self.assertEqual(r['result'],(0,0))
    def test_invalid_read_has_no_events(self):
        r,_=self.run_native('read',(0,ARENA,0));self.assertEqual(r['result'],(0xffffffff,0))
        self.assertEqual(r['events'],[]);self.assertEqual(r['calls'],[])
    def test_ignored_mode_failure_retains_requested_length(self):
        r,_=self.run_native('device_read',(ARENA,0xbf000,0x10001),memory=initial(8),registers={0x40200:0x800})
        self.assertEqual(r['result'],(0x10001,0));self.assertEqual(r['memory'][2],bytes(initial(8)[2]))
    def test_low_halfword_length(self):
        r,_=self.run_native('device_read',(ARENA,0xbf000,0x10001),reads={0x11c08:0xa5})
        self.assertEqual(r['result'],(0x10001,0));self.assertEqual(r['memory'][2][0],0xa5)
        self.assertEqual(r['memory'][2][1:],bytes(initial()[2][1:]))
    def test_page_split_commands(self):
        r,_=self.run_native('program_pages',(ARENA,257,0xbf0ff))
        self.assertEqual(r['internal_calls'].count(0x01c00840),2);self.assertEqual(r['result'],(257,0))
    def test_identification_uses_received_bytes(self):
        r,_=self.run_native('identify',reads={0x11c08:[0x12,0x34,0x56]+list(range(16))})
        self.assertEqual(getword(r['memory'],DEVICE+28),0x123456)
        self.assertEqual(r['memory'][1][:16],bytes(range(16)))
    def test_initialization_interrupt_arguments(self):
        m=initial();setword(m,DEVICE+16,0,1);r,_=self.run_native('initialize',memory=m)
        calls=[x for x in r['calls'] if x[0]==0x020005ac]
        self.assertEqual([x[1][:4] for x in calls],[(125,7,0x01c041dc,0),(124,7,0x01c041dc,1)])
    def test_fatal_is_observation(self):
        r,_=self.run_native('control',(205,0));self.assertEqual(r['status'],-204)
        self.assertIsNone(r['result']);self.assertEqual(r['stop_pc'],0x02002b7e)
        self.assertEqual(getword(r['memory'],STATE+67,1),1)
        self.assertEqual([x[0] for x in r['calls']], [0x02040614,0x0203e742,0x0200096e])
    def test_cache_wrap_and_signed_length(self):
        r,_=self.run_native('cache_lines',(0xfffffff1,64))
        self.assertEqual([e[1] for e in r['events'] if e[0]==FLUSH],[0xffffffe0,0])
        r,_=self.run_native('cache_lines',(0,0x80000000));self.assertFalse(any(e[0]==FLUSH for e in r['events']))
    def test_busy_read_prefix_preserves_constant_loop(self):
        r,_=self.run_native('busy_wait',reads={0x11c08:1},event_budget=70)
        self.assertEqual(r['status'],-203);self.assertEqual(len(r['events']),70);self.assertIsNone(r['result'])
    def test_callback_reloads_bus_flag(self):
        r,_=self.run_native('bus_leave',(0,),mutations=(((READ,0x40200),0,DEVICE+17,1,1),))
        self.assertFalse(any(x[0]==0x01c011da for x in r['calls']))
    def test_activity_raw_byte_depth(self):
        m=initial();setword(m,STATE+22,255,1);setword(m,STATE+392+254,0x5a,1);setword(m,STATE+1732+4*254,1234)
        r,_=self.run_native('activity',(0,),memory=m)
        self.assertEqual(getword(r['memory'],STATE+22,1),254);self.assertEqual(getword(r['memory'],STATE+23,1),0x5a)
        self.assertEqual(getword(r['memory'],STATE+396),1234)

if __name__=='__main__':unittest.main()
