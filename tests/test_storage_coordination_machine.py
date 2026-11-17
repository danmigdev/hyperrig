"""Independent native witnesses for CPU/lock and coordination boundaries."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from storage_coordination_machine import (StorageCoordinationProgram,REGIONS,REUSED,validate_cpu_evidence,
 GLOBAL,STATE,IRQ_COUNTS,RECORDS,CLI,STI,CNUM,TESTSET,YIELD,POLL,CLOCK)
from verify_storage_coordination import initial,setword,getword,Script

class StorageCoordinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=StorageCoordinationProgram()
    def native(self,name,args=(),memory=None,cpu=(0,0x01090700),services=10000,events=10000,**kw):
        script=Script(**kw)
        return self.program.execute(initial() if memory is None else memory,name,args,cpu,script.call,script.event,services,events)
    def test_complete_registry(self):
        self.assertEqual(len(REGIONS),9);self.assertEqual(sum(e-s for s,e in REGIONS.values()),578)
        self.assertEqual(len(self.program.code),184);self.assertEqual(len(REUSED),1)
    def test_cpu_primary_evidence(self):validate_cpu_evidence(self.program)
    def test_changed_CPU_notes_rejected(self):
        p=copy.copy(self.program);p.isa_records=copy.deepcopy(p.isa_records);p.isa_records['0x2002d30']['notes']='different'
        with self.assertRaises(ValueError):validate_cpu_evidence(p)
    def test_changed_CPU_branch_rejected(self):
        p=copy.copy(self.program);p.code=dict(p.code);p.code[0x02002d32]=('ifne goto -6',4,0,0)
        with self.assertRaises(ValueError):validate_cpu_evidence(p)
    def test_raw_zero_initialized_witness(self):self.assertEqual(self.program.initial_counters,bytes(8))
    def test_threshold_wrapped_product(self):
        m=initial();setword(m,STATE+4076,0xffffffff);setword(m,STATE+404,0)
        r=self.native('ready_threshold',(4294966,),memory=m);self.assertEqual(r['result'],(0,0))
        r=self.native('ready_threshold',(4294965,),memory=m);self.assertEqual(r['result'],(1,0))
    def test_wait_has_thirty_attempts(self):
        r=self.native('wait_ready');self.assertEqual(len(r['calls']),30)
        self.assertTrue(all(x[0]==YIELD and x[1][0]==1 for x in r['calls']))
        self.assertEqual(getword(r['memory'],STATE+204),0x12345678)
    def test_wait_observes_yield_mutation(self):
        r=self.native('wait_ready',mutations=((('call',YIELD),0,STATE+4076,114,4),))
        self.assertEqual(len(r['calls']),1)
    def test_cli_preserves_other_icfg_bits(self):
        r=self.native('irq_enter',cpu=(1,0xffffffff));self.assertEqual(r['cpu'],(1,0xfffffdff))
        self.assertEqual(getword(r['memory'],IRQ_COUNTS+4),1)
    def test_sti_preserves_other_icfg_bits(self):
        m=initial();setword(m,IRQ_COUNTS,1);r=self.native('irq_leave',memory=m,cpu=(0,0x12345000))
        self.assertEqual(r['cpu'],(0,0x12345200))
    def test_nested_leave_keeps_disabled(self):
        m=initial();setword(m,IRQ_COUNTS,2);r=self.native('irq_leave',memory=m,cpu=(0,0))
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),1);self.assertEqual(r['cpu'],(0,0))
        self.assertFalse(any(x[0]==STI for x in r['events']))
    def test_counter_zero_underflows(self):
        r=self.native('irq_leave');self.assertEqual(getword(r['memory'],IRQ_COUNTS),0xffffffff)
    def test_core_index_wrap(self):
        r=self.native('irq_enter',cpu=(0xffffffff,0));self.assertEqual(getword(r['memory'],IRQ_COUNTS-4),1)
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),0)
    def test_core_counter_can_end_at_uint32_boundary(self):
        core=((0xfffffffc-IRQ_COUNTS)&0xffffffff)>>2
        r=self.native('irq_enter',cpu=(core,0));self.assertEqual(getword(r['memory'],0xfffffffc),1)
        self.assertEqual(getword(r['memory'],0),0)
    def test_stop_before_testset(self):
        m=initial();setword(m,STATE+55,0x74,1);r=self.native('notify',(1,2,3),memory=m,events=4)
        self.assertEqual(r['status'],-203);self.assertEqual(r['stop_pc'],0x02002d30)
        self.assertEqual(getword(r['memory'],STATE+55,1),0x74);self.assertEqual(getword(r['memory'],STATE+1196),0)
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),1)
    def test_testset_uses_old_bit_two(self):
        for old,count in ((0,1),(1,1),(0x80,1),(4,2),(0x74,2),(255,2)):
            m=initial();setword(m,STATE+55,old,1)
            r=self.native('notify',(1,2,3),memory=m,mutations=(((TESTSET,STATE+55),0,STATE+55,0,1),))
            events=[x for x in r['events'] if x[0]==TESTSET];self.assertEqual(len(events),count)
            self.assertEqual(events[0][3],old)
    def test_record_packing_and_preserved_gap(self):
        m=initial();setword(m,STATE+1196,0xffffffff);setword(m,GLOBAL+24,0xffffffff)
        old=bytes(m[0][RECORDS-GLOBAL+6:RECORDS-GLOBAL+8]);r=self.native('notify',(0x12345678,0xaabbccdd,0x88776655),memory=m)
        self.assertEqual(getword(r['memory'],RECORDS),0xfffffff6)
        self.assertEqual(getword(r['memory'],RECORDS+4,2),0x5678)
        self.assertEqual(r['memory'][0][RECORDS-GLOBAL+6:RECORDS-GLOBAL+8],old)
        self.assertEqual(getword(r['memory'],RECORDS+8),0xaabbccdd)
        self.assertEqual(getword(r['memory'],RECORDS+12),0x88776655)
    def test_stamp_precedes_cli_callback(self):
        r=self.native('notify',(1,2,3),mutations=(((CLI,0),0,GLOBAL+24,3,4),))
        self.assertEqual(getword(r['memory'],RECORDS+16),(0x12345678*10)&0xffffffff)
    def test_event_zero_divisor_and_byte_kind(self):
        m=initial();setword(m,GLOBAL+44,0);r=self.native('event',(0x123,0xfedcba98,9),memory=m)
        self.assertEqual(getword(r['memory'],RECORDS+16+4,2),24)
        self.assertEqual(getword(r['memory'],RECORDS+16+8),0x23dcba98)
        self.assertEqual(getword(r['memory'],RECORDS+16+12),0)
    def test_raw_depth_wrap_is_nested(self):
        m=initial();setword(m,STATE+37,255,1);setword(m,STATE+34,37,1)
        r=self.native('gate',(1,),memory=m);self.assertEqual(getword(r['memory'],STATE+37,1),0)
        self.assertEqual(getword(r['memory'],STATE+34,1),37);self.assertFalse(r['calls'])
    def test_unentered_release_is_noop(self):
        m=initial();r=self.native('gate',(0,),memory=m);self.assertEqual(r['memory'],tuple(map(bytes,m)));self.assertFalse(r['calls'])
    def test_acknowledged_gate_final_wait(self):
        m=initial();setword(m,STATE+280,2);setword(m,STATE+29,1,1);setword(m,STATE+36,1,1)
        r=self.native('gate',(1,),memory=m);self.assertEqual([x[0] for x in r['calls']],[CLOCK,YIELD])
    def test_callback_cannot_change_CPU(self):
        def wrong(op,a,n,v,m):m.cpu[0]=1
        with self.assertRaises(ValueError):self.program.execute(initial(),'irq_enter',events=wrong)
    def test_CPU_event_return_is_ignored(self):
        a=self.native('notify',(3,5,7));b=self.native('notify',(3,5,7),event_return=0xffffffffffffffff)
        self.assertEqual(a['memory'],b['memory']);self.assertEqual(a['cpu'],b['cpu']);self.assertEqual(a['result'],b['result'])

if __name__=='__main__':unittest.main()
