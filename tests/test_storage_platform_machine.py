"""Independent entry, IRQ frame, ordering and evidence assertions."""
from pathlib import Path
import copy
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from storage_platform_machine import *
from verify_storage_platform import Script,initial,setword,getword,context

class PlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=StoragePlatformProgram()
    def native(self,name,args=(),memory=None,cpu=(0,0x01090700),irq_context=None,services=10000,events=10000,**script):
        fixture=Script(**script)
        if name=='interrupt' and irq_context is None:irq_context=context(15)
        result=self.program.execute(initial() if memory is None else memory,name,args,cpu,irq_context,fixture.call,fixture.event,services,events)
        return result,fixture
    def test_complete_registry(self):
        self.assertEqual(len(REGIONS),9);self.assertEqual(sum(b-a for a,b in REGIONS.values()),580)
        self.assertEqual(len(self.program.code),217);self.assertEqual(len(DIRECT_SITES),9)
    def test_altered_primary_ISA_record_rejected(self):
        p=copy.copy(self.program);p.isa_records=copy.deepcopy(p.isa_records)
        p.isa_records[hex(0x01c041dc)]['notes']='changed'
        with self.assertRaises(ValueError):validate_cpu_evidence(p)
    def test_cpu_preserved_bits(self):
        r,_=self.native('gate_disable',cpu=(0,0xffffffff));self.assertEqual(r['cpu'][1],0xfffffeff)
        r,_=self.native('gate_enable',cpu=(0,0x12345678));self.assertEqual(r['cpu'][1],0x12345778)
    def test_register_writes_vector_before_masking(self):
        r,s=self.native('register',(125,7,0x01c041dc,0),cpu=(1,0))
        self.assertEqual(getword(r['memory'],0x01c7fff4),0x01c041dc)
        self.assertEqual(r['cpu'][1],0x100)
        self.assertEqual([e[0] for e in s.actions],[ICFG_READ,ICFG_WRITE,READ,WRITE,ICFG_READ,ICFG_WRITE])
        self.assertEqual(s.actions[2][1],0x01eef13c)
    def test_zero_handler_preserves_vector(self):
        m=initial();old=getword(m,0x01c7fff0)
        r,_=self.native('register',(124,7,0,1),memory=m)
        self.assertEqual(getword(r['memory'],0x01c7fff0),old)
    def test_core255_reads_CNUM_but256_selects_bank_zero(self):
        _,s=self.native('register',(8,1,0,255),cpu=(1,0));self.assertEqual(next(e[1] for e in s.actions if e[0]==READ),0x01eef304)
        _,s=self.native('register',(8,1,0,256),cpu=(1,0));self.assertFalse(any(e[0]==CNUM for e in s.actions))
        self.assertEqual(next(e[1] for e in s.actions if e[0]==READ),0x01eef104)
    def test_peer_resume_real_else_block(self):
        for selector,address in ((0,0x01eee000),(1,0x01eee004),(0xffffffff,0x01eee004)):
            _,s=self.native('peer_resume',(selector,));self.assertEqual(s.actions[0][:3],(READ,address,4))
            self.assertEqual(s.registers[address],24)
    def test_clock_is_actual_MMIO_read(self):
        r,s=self.native('clock',returns={(READ,0x10704):0xffffffff})
        self.assertEqual(r['result'],(0xffffffff,0));self.assertEqual(len(s.actions),1)
    def test_raw_nesting_underflow_does_not_unlock(self):
        r,s=self.native('leave');self.assertEqual(getword(r['memory'],LOCK_COUNTS),0xffffffff)
        self.assertFalse(any(e[0]==LOCKCLR for e in s.actions))
    def test_enter_keeps_interrupts_masked_until_leave(self):
        r,_=self.native('enter',(0,0),cpu=(0,0x300));self.assertEqual(r['cpu'][1],0x100)
        self.assertEqual(getword(r['memory'],LOCK_COUNTS),1);self.assertEqual(getword(r['memory'],IRQ_COUNTS),1)
        z,_=self.native('leave',memory=r['memory'],cpu=r['cpu']);self.assertEqual(z['cpu'][1],0x300)
        self.assertEqual(getword(z['memory'],LOCK_COUNTS),0)
    def test_irq_preserves_context_and_uses_RTI(self):
        incoming=context(0xffffffff);r,s=self.native('interrupt',irq_context=incoming)
        expected=incoming[:16]+(15,incoming[17]&0x07fffffe,incoming[18]&0x07fffffe)
        self.assertEqual(r['context'],expected);self.assertEqual(r['stop_pc'],expected[-1])
        self.assertEqual(s.actions[0][:4],(PUSH,STACK-12,12,0x10029))
        self.assertEqual(s.actions[1][:4],(PUSH,STACK-32,20,31));self.assertEqual(s.actions[-1][:4],(RTI,expected[-1],0,0))
        self.assertEqual(r['interrupt_frame'],struct.pack('<8I',*incoming[:5],expected[-1],expected[-2],expected[-3]))
    def test_IRQ_context_is_mandatory_and_separate(self):
        with self.assertRaises(ValueError):self.program.execute(initial(),'interrupt')
        with self.assertRaises(ValueError):self.program.execute(initial(),'clock',context=context())
    def test_IRQ_callback_uses_one_word_even_for_loaded_token(self):
        m=initial();setword(m,COMMAND,0x020005ac);setword(m,ARGUMENT,0x99887766)
        r,_=self.native('interrupt',memory=m);self.assertEqual(len(r['calls']),1)
        self.assertEqual(r['calls'][0][:2],(0x020005ac,(0x99887766,)+(0,)*11))
        self.assertEqual(r['service_sites'],[(0x01c04248,0x020005ac,1)])
    def test_callback_ABI_rejects_callee_saved_change(self):
        m=initial();setword(m,COMMAND,7);s=Script()
        def wrong(target,args,machine):machine.set('r4',3);return 0
        with self.assertRaises(ValueError):self.program.execute(m,'interrupt',context=context(),boundary=wrong,events=s.event)
    def test_event_guard_does_not_publish_IRQ_context(self):
        r,s=self.native('interrupt',events=1);self.assertEqual(r['status'],-203);self.assertIsNone(r['context'])
        self.assertEqual(len(s.actions),1)
    def test_service_guard_keeps_native_ACK_and_CPU(self):
        m=initial(1);setword(m,COMMAND,1)
        r,_=self.native('interrupt',memory=m,services=0,clear_irq=False)
        self.assertEqual(r['status'],-203);self.assertEqual(getword(r['memory'],ACK,1),1)
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),1);self.assertEqual(r['cpu'][1],0x01090500)
    def test_callback_cannot_borrow_private_frame(self):
        m=initial();setword(m,COMMAND,5)
        r,_=self.native('interrupt',memory=m,probes=((('call',5),0,STACK-32,4,0),))
        self.assertEqual(r['status'],-202);self.assertIsNone(r['context']);self.assertEqual(len(r['calls']),1)
    def test_raw_core_cannot_reuse_saved_IRQ_frame_as_nesting_word(self):
        incoming=context(0xffffffff);number=((STACK-32-IRQ_COUNTS)&0xffffffff)>>2
        r,s=self.native('interrupt',cpu=(number,0x300),irq_context=incoming)
        self.assertEqual(r['status'],-202);self.assertIsNone(r['context'])
        self.assertEqual(r['cpu'],(number,0x100))
        expected=incoming[:5]+(incoming[18]&0x07fffffe,incoming[17]&0x07fffffe,15)
        self.assertEqual(r['interrupt_frame'],struct.pack('<8I',*expected))
        self.assertFalse(any(e[0] in (POP,RTI) for e in s.actions))
    def test_missing_vector_map_fails_before_CPU_mask(self):
        r,s=self.native('register',(128,1,7,0));self.assertEqual(r['status'],-201);self.assertEqual(s.actions,[])
    def test_initial_ACK_spin_is_only_equal_one(self):
        m=initial(1);setword(m,ACK,2,1);r,_=self.native('enter',(1,2),memory=m)
        self.assertNotIn(0x01c0113a,r['visited'])
    def test_mutable_startup_is_not_initialized_by_entry(self):
        m=initial();setword(m,COMMAND,0x12345678);r,_=self.native('clock',memory=m)
        self.assertEqual(r['memory'],tuple(map(bytes,m)))

if __name__=='__main__':unittest.main()
