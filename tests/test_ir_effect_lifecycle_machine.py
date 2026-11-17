"""Focused native IR ownership, restore-order, ABI and alias witnesses."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ir_effect_lifecycle_machine import IrEffectLifecycleProgram,REGIONS,REUSED,MAPPED
from verify_ir_effect_lifecycle import (initial,setword,samples,Script,EFFECT,CONTROL,
    SOURCE,OLD,NEW,READER,GAIN,ALLOCATE,READ,RELEASE,REPLACEMENT,MODE,PREPARE,CONSTRUCT)


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=IrEffectLifecycleProgram()
    def run_case(self,name,args,memory=None,returns=None,mutations=(),stop=None):
        return self.program.execute(initial() if memory is None else memory,name,args,Script(returns,mutations),stop)
    def word(self,memory,address,size=4):
        for (base,n),data in zip(MAPPED,memory):
            if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
        raise AssertionError('unmapped native test read')
    def test_nine_complete_bodies(self):
        self.assertEqual(len(REGIONS),9)
        self.assertEqual(sum(any(a<=pc<b for a,b in REGIONS.values()) for pc in self.program.code),422)
    def test_retry_rereads_mode_after_failure(self):
        r=self.run_case('mode_prepare',(EFFECT,),returns={PREPARE:(-3,17)})
        self.assertEqual([x[1][:2] for x in r['calls'] if x[0]==PREPARE],[(EFFECT,1),(EFFECT,0)])
        self.assertEqual(r['result'],(17,0))
        r=self.run_case('mode_prepare',(EFFECT,),returns={PREPARE:-3},mutations=((PREPARE,0,0x01c1f7d0,0,4),))
        self.assertEqual(sum(x[0]==PREPARE for x in r['calls']),1)
    def test_zero_temporary_count_has_no_side_effects(self):
        m=initial();r=self.run_case('temporary',(EFFECT,SOURCE,0,7,9,1,3,55),m)
        self.assertEqual(r['result'],(0xffffffff,0));self.assertEqual(r['memory'],tuple(map(bytes,m)))
        self.assertFalse(r['calls'])
    def test_eight_argument_stack_and_reader_abi(self):
        r=self.run_case('temporary',(EFFECT,0,17,0xabc,0x3f800000,255,0x12345678,0x87654321),returns={ALLOCATE:NEW})
        read=next(x for x in r['calls'] if x[0]==READ)
        self.assertEqual(read[1],(0x12345678,0x87654321,NEW,17)+(0,)*8)
        prepare=next(x for x in r['calls'] if x[0]==PREPARE)
        self.assertEqual([self.word(prepare[2],a) for a in (CONTROL+60,CONTROL+64,CONTROL+80,GAIN,CONTROL+68)],
            [NEW,17,0xabc,0x3f800000,1])
    def test_globals_restore_before_free(self):
        m=initial();r=self.run_case('temporary',(EFFECT,0,8,5,0x80000000,0,3,44),m,{ALLOCATE:NEW,PREPARE:-1},
            ((PREPARE,0,CONTROL+60,0x11223344,4),(PREPARE,0,GAIN,0x7f800001,4)))
        free=r['calls'][-1];self.assertEqual(free[0],RELEASE)
        for address in (CONTROL+60,CONTROL+64,CONTROL+80,GAIN,CONTROL+68):
            self.assertEqual(self.word(free[2],address),self.word(m,address))
    def test_reader_failure_frees_without_installing_globals(self):
        m=initial();r=self.run_case('temporary',(EFFECT,0,8,5,1,1,3,44),m,{ALLOCATE:NEW,READ:1})
        self.assertEqual(r['result'],(0xffffffff,0));self.assertNotIn(PREPARE,[x[0] for x in r['calls']])
        self.assertEqual(self.word(r['memory'],CONTROL+60),self.word(m,CONTROL+60))
        self.assertEqual(r['calls'][-1][1][0],NEW)
    def test_temporary_snapshots_after_reader_callback(self):
        r=self.run_case('temporary',(EFFECT,0,8,5,1,1,3,44),returns={ALLOCATE:NEW},
            mutations=((READ,0,CONTROL+60,0x12345678,4),))
        self.assertEqual(self.word(r['memory'],CONTROL+60),0x12345678)
    def test_assignment_seven_arguments_preserve_identity(self):
        r=self.run_case('assign',(0,SOURCE,8,25000,255,255,0x87654321))
        for offset,expected,width in ((48,0,4),(52,8,4),(60,20000,4),(68,1,1),(69,255,1),(64,0x87654321,4)):
            self.assertEqual(self.word(r['memory'],EFFECT+offset,width),expected)
        self.assertNotIn(ALLOCATE,[x[0] for x in r['calls']])
    def test_rollback_restores_fields_then_frees_mutated_new_pointer(self):
        m=initial();r=self.run_case('assign',(0,SOURCE,8,1234,1,0,0),m,{ALLOCATE:NEW,PREPARE:-1},
            ((PREPARE,0,EFFECT+48,NEW+128,4),(PREPARE,0,EFFECT+60,9999,4)))
        self.assertEqual(r['calls'][-1][1][0],NEW+128)
        for offset,width in ((48,4),(52,4),(56,4),(60,4),(64,4),(68,1),(69,1)):
            self.assertEqual(self.word(r['calls'][-1][2],EFFECT+offset,width),self.word(m,EFFECT+offset,width))
        self.assertEqual(self.word(r['memory'],0x01c34468),0)
    def test_success_frees_cached_old_pointer_then_wraps_counter(self):
        r=self.run_case('assign',(0,SOURCE,8,0,1,0,0),returns={ALLOCATE:NEW},
            mutations=((PREPARE,0,EFFECT+48,NEW+128,4),(RELEASE,0,0x01c34468,0xffffffff,4)))
        self.assertEqual(r['calls'][-1][1][0],OLD)
        self.assertEqual(self.word(r['memory'],EFFECT+48),NEW+128)
        self.assertEqual(self.word(r['memory'],0x01c34468),0)
    def test_forward_overlapping_copy_is_not_memmove(self):
        m=initial()
        for i in range(8):setword(m,SOURCE+2*i,i+1,2)
        r=self.run_case('assign',(0,SOURCE,8,0,1,0,0),m,{ALLOCATE:SOURCE+2})
        self.assertEqual([self.word(r['memory'],SOURCE+2*i,2) for i in range(9)],[1]*9)
    def test_trim_strict_threshold_and_signed_minimum(self):
        for tail,expected in ((10,1),(11,8),(-32768,8)):
            m=initial();setword(m,SOURCE+14,tail,2)
            r=self.run_case('assign',(0,SOURCE,8,0,1,3,44),m)
            self.assertEqual(self.word(r['memory'],EFFECT+56),expected)
    def test_count_wrap_reaches_allocator_without_new_limit(self):
        for count,expected in ((0x80000000,0),(0xffffffff,0),(0x80000001,4)):
            r=self.run_case('assign',(0,SOURCE,count,0,1,0,0))
            self.assertEqual(next(x[1][0] for x in r['calls'] if x[0]==ALLOCATE),expected)
            self.assertEqual(r['result'],(0xfffffffd,0))
    def test_indirect_colliding_tokens_stay_external(self):
        for target,_ in (REGIONS|REUSED).values():
            m=initial();setword(m,0x01c34458,target)
            r=self.run_case('mode_prepare',(EFFECT,),m)
            self.assertEqual(r['calls'][0][0],target)
            self.assertEqual(r['service_sites'][0],(0x01c05ed2,target,1))
    def test_construct_wrapper_argument_order_and_null_source(self):
        r=self.run_case('construct_copy',(NEW,SOURCE,129),returns={CONSTRUCT:OLD})
        self.assertEqual(r['calls'][0][1],(NEW,129,0x020315b8,SOURCE)+(0,)*8)
        self.assertEqual(r['result'],(OLD,0))
        self.assertFalse(self.run_case('construct_copy',(NEW,0,129))['calls'])
    def test_relocation_wraps_and_keeps_nonpointer_fields(self):
        m=initial();setword(m,NEW,1);setword(m,NEW+4,0x12345678)
        for offset in range(20,56,4):setword(m,NEW+offset,0xffffffff)
        r=self.run_case('relocate',(NEW,0xfffffffe),m)
        self.assertEqual(self.word(r['memory'],NEW+4),0x12345678)
        self.assertTrue(all(self.word(r['memory'],NEW+offset)==NEW+1 for offset in range(20,56,4)))
        self.assertEqual(r['result'],(0,0))
    def test_original_prefix_observation_is_specific_pc(self):
        r=self.run_case('assign',(0,SOURCE,0xffffffff,0,1,0,0),returns={ALLOCATE:NEW},stop=(0x020299a4,3))
        self.assertEqual(r['status'],-203);self.assertEqual(r['stop_pc'],0x020299a4)
        self.assertEqual(len([w for w in r['writes'] if NEW<=w[0]<NEW+32]),3)
        self.assertEqual(self.word(r['memory'],EFFECT+48),OLD)
    def test_public_model_rejects_wrong_argument_count(self):
        with self.assertRaises(ValueError):self.program.execute(initial(),'temporary',(EFFECT,))
        with self.assertRaises(ValueError):self.program.execute(initial(),'owns',(-1,))


if __name__=='__main__':unittest.main()
