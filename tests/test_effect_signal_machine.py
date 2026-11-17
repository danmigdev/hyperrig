"""Focused observations from the three complete original numerical bodies."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_signal_machine import EffectSignalProgram,REGIONS,MAPPED
from verify_effect_signal import fixture,setword,SAMPLES,ARENA

class EffectSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectSignalProgram()
    def word(self,result,address):
        for (base,size),data in zip(MAPPED,result['memory']):
            if base<=address<base+size:return int.from_bytes(data[address-base:address-base+4],'little')
        self.fail('test read outside mapped original state')
    def run_gate(self,count=16,level=0,gain=0,smoothing=65536,budget=100):
        m,state=fixture('gate',1)
        for off,v in ((0,2000),(4,1000),(8,65536),(12,65536),(16,smoothing),(20,0),(24,gain)):
            setword(m,state+off,v)
        for i in range(544):setword(m,SAMPLES+4*i,level)
        return m,state,self.program.execute(m,'gate',(SAMPLES,count,state),block_budget=budget)
    def test_complete_body_decode_and_no_calls(self):
        code=[(pc,text) for pc,(text,*_) in self.program.code.items() if any(a<=pc<b for a,b in REGIONS.values())]
        self.assertEqual(len(code),708)
        self.assertFalse(any(text.startswith('call ') for _,text in code))
    def test_gate_partial_count_processes_whole_sixteen(self):
        _,_,r=self.run_gate(count=1,level=50)
        self.assertEqual([self.word(r,SAMPLES+4*i) for i in range(16)],[0]*16)
        self.assertEqual(self.word(r,SAMPLES+64),50)
    def test_gate_unity_preserves_samples_without_stores(self):
        _,state,r=self.run_gate(level=2001,gain=65536,smoothing=0)
        self.assertEqual({p for p,_,_ in r['writes']},{state+20,state+24})
        self.assertEqual(self.word(r,SAMPLES),2001)
    def test_absolute_int_min_saturates_positive(self):
        _,state,r=self.run_gate(level=0x80000000,gain=65536,smoothing=0)
        self.assertEqual(self.word(r,state+20),0x7fffffff)
    def test_upper_threshold_is_strict(self):
        _,state,at=self.run_gate(level=2000)
        _,_,above=self.run_gate(level=2001)
        self.assertEqual(self.word(at,state+24),0)
        self.assertEqual(self.word(above,state+24),65536)
    def test_lower_threshold_is_strict(self):
        _,state,at=self.run_gate(level=1000,gain=65536)
        _,_,below=self.run_gate(level=999,gain=65536)
        self.assertEqual(self.word(at,state+24),65536)
        self.assertEqual(self.word(below,state+24),0)
    def test_gain_half_is_initially_closed(self):
        _,state,at=self.run_gate(level=1500,gain=32768)
        _,_,above=self.run_gate(level=1500,gain=32769)
        self.assertEqual(self.word(at,state+24),0)
        self.assertEqual(self.word(above,state+24),65536)
    def test_count_above_512_is_supported(self):
        _,_,r=self.run_gate(count=513,level=1)
        self.assertEqual(len(r['blocks']),33)
        self.assertEqual(self.word(r,SAMPLES+527*4),0)
        self.assertEqual(self.word(r,SAMPLES+528*4),1)
    def test_zero_count_enters_and_budget_keeps_prefix(self):
        m,state,r=self.run_gate(count=0,level=50,budget=1)
        self.assertEqual(r['status'],-203)
        self.assertEqual(len(r['blocks']),1)
        self.assertEqual(self.word(r,SAMPLES),0)
        self.assertEqual(self.word(r,SAMPLES+64),50)
        self.assertEqual(r['memory'][2][state-ARENA:state-ARENA+28],m[2][state-ARENA:state-ARENA+28])
    def test_wrapped_block_count_is_not_noop(self):
        _,_,r=self.run_gate(count=0xfffffff1,level=50,budget=1)
        self.assertEqual(r['status'],-203);self.assertEqual(self.word(r,SAMPLES),0)
    def filter_fixture(self,dry=1<<26):
        m,state=fixture('variable_filter',7)
        for off in range(0,40,4):setword(m,state+off,0)
        setword(m,state+28,dry)
        for i in range(16):setword(m,SAMPLES+4*i,0x80000000)
        return m,state
    def test_filter_exact_int_min_is_retained(self):
        m,state=self.filter_fixture();r=self.program.execute(m,'variable_filter',(SAMPLES,4,state))
        self.assertEqual(self.word(r,SAMPLES),0x80000000)
    def test_filter_negative_overflow_clips_to_minus_int_max(self):
        m,state=self.filter_fixture(1<<27);r=self.program.execute(m,'variable_filter',(SAMPLES,4,state))
        self.assertEqual(self.word(r,SAMPLES),0x80000001)
    def test_filter_large_raw_count_can_have_short_effective_span(self):
        m,state=fixture('variable_filter',17)
        small=self.program.execute(m,'variable_filter',(SAMPLES,4,state))
        wrapped=self.program.execute(m,'variable_filter',(SAMPLES,0x40000004,state))
        self.assertEqual(small['memory'],wrapped['memory']);self.assertEqual(len(wrapped['blocks']),1)
    def test_filter_unreachable_endpoint_stops_after_full_blocks(self):
        m,state=self.filter_fixture(1<<27)
        r=self.program.execute(m,'variable_filter',(SAMPLES,1,state),block_budget=3)
        self.assertEqual(r['status'],-203);self.assertEqual(len(r['blocks']),3)
        self.assertEqual(self.word(r,SAMPLES+11*4),0x80000001)
        self.assertEqual(self.word(r,SAMPLES+12*4),0x80000000)
        self.assertEqual(r['memory'][2],m[2])
    def test_allpass_phase_publishes_before_budget_stop(self):
        m,state=fixture('allpass',31);setword(m,state,0xffffff00);setword(m,state+4,32)
        before=m[2][state-ARENA+8:state-ARENA+52]
        r=self.program.execute(m,'allpass',(SAMPLES,32,state),block_budget=1)
        self.assertEqual(r['status'],-203);self.assertEqual(self.word(r,state),0x100)
        self.assertEqual(r['memory'][2][state-ARENA+8:state-ARENA+52],before)
    def test_zero_budget_never_writes_public_data(self):
        for name in REGIONS:
            m,state=fixture(name,3);r=self.program.execute(m,name,(SAMPLES,16,state),block_budget=0)
            self.assertEqual(r['status'],-203);self.assertEqual(r['memory'],tuple(bytes(x) for x in m))

if __name__=='__main__':unittest.main()
