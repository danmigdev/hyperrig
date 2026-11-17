"""Focused original-instruction witnesses for enable ordering and state arithmetic."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_enable_machine import (EffectEnableProgram, EFFECTS, CONTROL, CALLBACKS,
    ARENA, TABLE_START, TABLE_END, ALIGNMENT_END)
from verify_effect_enable import initial, put, Script, INSTALLED

class EffectEnableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.program=EffectEnableProgram()
    def run_case(self,operation,args,memory=None,**script):
        return self.program.execute(initial() if memory is None else memory,operation,*args,boundary=Script(**script))
    def test_table_and_padding_are_data(self):
        self.assertEqual(len(self.program.table),29)
        self.assertFalse(any(pc in self.program.code for pc in range(TABLE_START,ALIGNMENT_END)))
        self.assertEqual(TABLE_END+1,ALIGNMENT_END)
        for type_,target in ((11,0x01c06a68),(12,0x01c06a68),(15,0x01c06a68),
                             (29,0x01c06aa4),(30,0x01c06af4),(38,0x01c06ac6),(39,0x01c06a68)):
            self.assertEqual(TABLE_START+2*self.program.table[type_-11],target)
    def test_predicate_raw_types(self):
        expected={5,27,30,31,32,33,34,35}
        found={x for x in range(256) if self.run_case('tail_type',(x,))['result']}
        self.assertEqual(found,expected)
    def test_commit_invalid_increments_counter_fast_does_not(self):
        for op,expected in (('commit',1),('fast',0)):
            result=self.run_case(op,(16,1))
            self.assertEqual(result['result'],0xffffffff)
            self.assertEqual(int.from_bytes(result['memory'][3][728:732],'little'),expected)
            self.assertEqual(result['calls'],[])
    def test_counter_wrap(self):
        m=initial();put(m[3],728,0xffffffff)
        self.assertEqual(self.run_case('counter',(),m)['memory'][3][728:732],bytes(4))
    def test_external_resource_order_and_arguments(self):
        commit=self.run_case('commit',(15,255))['calls'];fast=self.run_case('fast',(15,255))['calls']
        self.assertEqual([(x[0],x[1][:2]) for x in commit],
            [(0x0203023c,(15,0)),(0x02028de8,(0,0)),(0x0203033c,(EFFECTS+15*480,0)),(0x0202ec30,(0,0))])
        self.assertEqual([(x[0],x[1][:2]) for x in fast],
            [(0x0202def2,(EFFECTS+15*480,0)),(0x02028de8,(0,0)),(0x0203023c,(15,0)),(0x0202ec30,(0,0))])
    def test_unchecked_commit_still_calls_cost(self):
        r=self.run_case('commit_unchecked',(0,1))
        self.assertEqual([x[0] for x in r['calls']],[0x0203023c,0x0203033c])
    def test_unsigned_sum_wrap(self):
        m=initial();put(m[2],48,0)
        r=self.run_case('commit',(0,1),m,plan={0x0203023c:0xffffffff,0x02028de8:1})
        self.assertEqual(r['result'],0);self.assertEqual(r['memory'][0][1],1)
    def test_construct_error_preserves_status_and_skips_finish(self):
        r=self.run_case('commit',(0,1),plan={0x0203033c:0xfffffffd})
        self.assertEqual(r['result'],0xfffffffd);self.assertEqual(r['memory'][0][1],0)
        self.assertNotIn(0x0202ec30,[x[0] for x in r['calls']])
    def test_finish_ignores_service_return(self):
        self.assertEqual(self.run_case('finish',(0,),plan={0x0202ec30:123})['result'],0)
    def test_duration_signed_sum_wrap(self):
        m=initial(11);put(m[0],304,0x7fffffff);put(m[0],308,1)
        self.assertEqual(self.run_case('duration',(EFFECTS,),m)['result'],0)
        put(m[0],304,1);put(m[0],308,0)
        self.assertEqual(self.run_case('duration',(EFFECTS,),m)['result'],1)
        put(m[0],304,0x7fffffff)
        self.assertEqual(self.run_case('duration',(EFFECTS,),m)['result'],16)
    def test_duration_signed_max_and_arithmetic_shift(self):
        m=initial(25);put(m[0],320,1);put(m[0],324,0xffffffff);put(m[0],332,0xffffffff)
        self.assertEqual(self.run_case('duration',(EFFECTS,),m)['result'],0)
    def test_fade_reversal_wraps_byte(self):
        m=initial();m[0][10:12]=bytes((2,255))
        self.assertEqual(self.run_case('fade',(EFFECTS,1),m)['memory'][0][10:12],bytes((1,5)))
    def test_tail_keeps_count_and_selects_mode_five(self):
        m=initial(31);put(m[0],8,9,2);m[0][11]=77
        self.assertEqual(self.run_case('fade',(EFFECTS,1),m)['memory'][0][10:12],bytes((5,77)))
    def test_actual_installed_clear(self):
        m=initial(11);put(m[0],88,1025);put(m[3],4,INSTALLED)
        r=self.run_case('fade',(EFFECTS,1),m)
        self.assertEqual(r['calls'],[]);self.assertIn(INSTALLED,r['internal_calls'])
        self.assertIn(0x02033412,r['internal_calls'])
        self.assertEqual(r['memory'][4][4096:4096+2052],bytes(2052))
        self.assertEqual(r['memory'][4][4096+2052:],m[4][4096+2052:])
    def test_memset_preserves_neighbours_and_returns_original(self):
        for alignment in range(4):
            m=initial();r=self.run_case('memset',(ARENA+alignment,0x12345678,1031),m)
            self.assertEqual(r['result'],ARENA+alignment)
            expected=bytearray(m[4]);expected[alignment:alignment+1031]=bytes([0x78])*1031
            self.assertEqual(r['memory'][4],expected)
    def test_ir_reset_cached_count_and_actual_buffers(self):
        m=initial();put(m[4],4,pow(129,-1,2**32));put(m[4],24,ARENA+4)
        r=self.run_case('ir_reset',(ARENA,),m)
        self.assertEqual(r['memory'][4][4:16],bytes(12))
        self.assertEqual(r['memory'][4][2048:3072],bytes(1024))
        self.assertEqual(r['memory'][4][16:24],m[4][16:24])
    def test_callback_limit_reload(self):
        r=self.run_case('fast',(0,1),plan={0x0203023c:1},
            mutations={(0x0203023c,0):[(CONTROL+48,0,4)]})
        self.assertEqual(r['result'],0xfffffffc);self.assertEqual(r['memory'][0][1],0)
    def test_construct_enabled_reload(self):
        r=self.run_case('commit',(0,1),mutations={(0x0203033c,0):[(EFFECTS+1,1,1)]})
        self.assertNotIn(0x01c069e4,r['internal_calls']);self.assertEqual(r['memory'][0][1],1)
    def test_alternate_clear_stays_external_when_token_is_loaded(self):
        m=initial(11);put(m[0],88,1024);put(m[3],4,0x020305f8)
        r=self.run_case('fade',(EFFECTS,1),m)
        self.assertEqual([(t,a[:2]) for t,a,*_ in r['calls']],[(0x020305f8,(ARENA+4096,2048))])
        self.assertNotIn(0x020305f8,r['internal_calls'])
        self.assertEqual(r['memory'][4],m[4])
    def test_indirect_arity_follows_callsite_when_target_is_direct_service(self):
        m=initial(11);put(m[0],88,1024);put(m[3],4,0x0203023c)
        r=self.run_case('fade',(EFFECTS,1),m)
        self.assertEqual(r['service_sites'],[(0x01c06af0,0x0203023c,2)])
        self.assertEqual(r['calls'][0][1],(ARENA+4096,2048,0,0,0,0))

if __name__=='__main__':unittest.main()
