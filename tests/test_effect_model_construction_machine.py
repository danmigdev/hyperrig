"""Focused original-instruction contracts, table bounds and state witnesses."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_model_construction_machine import EffectModelConstructionProgram,REGIONS,STATIC,MAPPED,ARITIES
from verify_effect_model_construction import initial,setword,EFFECT,CFG,ARENA,floating,TABLE_PROOFS

def read(memory,address,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
    raise ValueError('test address')

class ModelConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectModelConstructionProgram()
    def run_entry(self,name,args=(),memory=None):
        return self.program.execute(initial()if memory is None else memory,name,args)
    def test_complete_scope(self):
        self.assertEqual(len(REGIONS),49)
        self.assertEqual(sum(any(a<=pc<b for a,b in REGIONS.values())for pc in self.program.code),3081)
    def test_table_bytes_are_not_instructions(self):
        a,b=STATIC['model_branches'];self.assertEqual(b-a,8)
        self.assertFalse(any(a<=pc<b for pc in self.program.code))
        for byte in self.program.data['model_branches']:
            self.assertIn(a+2*byte,self.program.code);self.assertNotIn(a+2*byte,self.program.parallel_seconds)
    def test_all_static_tables_have_whole_consumer_evidence(self):
        self.assertEqual(set(TABLE_PROOFS),set(STATIC))
        for name,(function,sites,_)in TABLE_PROOFS.items():
            a,b=REGIONS[function]
            self.assertTrue(all(a<=pc<b and pc in self.program.code for pc in sites),name)
    def test_unused_prefixes_and_suffixes_remain_excluded(self):
        for address in (0x0203bdf8,0x0203be28,0x0203b74c,0x0203b764):
            self.assertFalse(any(a<=address<b for a,b in STATIC.values()))
        self.assertEqual(sum(b-a for a,b in STATIC.values()),669)
    def test_pinned_record_groups(self):
        self.assertEqual([self.program.data['object_records'][84*i+58]for i in range(4)],[0,2,0,0])
    def test_object_selector_returns_only_four_records(self):
        expected={31:2,32:1,35:3}
        for value in (*range(40),0xffffffff):
            self.assertEqual(self.run_entry('object_record',(value,))['result'],(0x0203b4b8+84*expected.get(value,0),0))
    def test_exact_percent_words(self):
        for value,expected in ((0,0),(100,0x3f800000),(0xffffff9c,0xbf800000)):
            self.assertEqual(self.run_entry('percent',(value,))['result'],(expected,0))
    def test_gain_upper_clamp(self):
        self.assertEqual(self.run_entry('level_exp',(6,))['result'],self.run_entry('level_exp',(32767,))['result'])
    def test_pole_helper_is_a_signed_clamp(self):
        args=(floating(100000),)
        self.assertGreater(self.run_entry('pole_exp',args)['result'][0],32767)
        self.assertEqual(self.run_entry('pole_clamp',args)['result'],(32767,0))
    def test_wide_zero_division_and_identity(self):
        self.assertEqual(self.run_entry('unsigned_quotient',(0xffffffff,0xffffffff,0,0))['result'],(0,0))
        self.assertEqual(self.run_entry('unsigned_quotient',(0xffffffff,0x80000000,1,0))['result'],(0xffffffff,0x80000000))
    def test_pitch_limit_unsigned_subtraction(self):
        for value,expected in ((0,0),(19,0),(20,1),(54,1),(55,0),(0xffffffff,0)):
            m=initial();setword(m,CFG+16,value)
            self.assertEqual(self.run_entry('pitch_limit_valid',(),m)['result'],(expected,0))
    def test_invalid_model_type_does_not_mutate(self):
        m=initial(255);out=self.run_entry('build16_to23',(EFFECT,),m)
        self.assertEqual(out['memory'],tuple(map(bytes,m)));self.assertFalse(out['calls'])
    def test_real_join_has_no_external_numerical_calls(self):
        out=self.run_entry('construct',(EFFECT,),initial(17))
        self.assertFalse(out['calls']);self.assertIn(0x0202b838,out['internal_calls'])
        self.assertIn(0x0202ac80,out['internal_calls'])
    def test_reset_hot_state_is_untouched(self):
        m=initial();setword(m,ARENA+628,1)
        self.assertEqual(self.run_entry('object_reset',(ARENA,),m)['memory'],tuple(map(bytes,m)))
    def test_reset_publishes_four_phase_seeds(self):
        out=self.run_entry('object_reset',(ARENA,))['memory']
        self.assertEqual([read(out,ARENA+512+4*i)for i in range(4)],[0,0x55555555,0x80000000,0xd5555555])
    def test_signature_bypass_and_zero_phase(self):
        m=initial();setword(m,EFFECT+70,100,2);setword(m,EFFECT+74,0,2)
        out=self.run_entry('build_signature',(ARENA,EFFECT+70),m)['memory']
        self.assertEqual(read(out,ARENA+64),1);self.assertEqual(read(out,ARENA+60),0)
        self.assertTrue(all(read(out,ARENA+17328+4*i)==0x40000000 for i in range(257)))
        self.assertTrue(all(read(out,ARENA+18356+8*i)==0x40000000 and read(out,ARENA+18360+8*i)==0 for i in range(256)))
    def test_cold_pitch_initialization_follows_filter_selection(self):
        m=initial(29)
        for i,x in enumerate((-12,0,50,0,50,0,0)):setword(m,EFFECT+70+2*i,x,2)
        for offset in (365,366,371):setword(m,EFFECT+offset,0,1)
        out=self.run_entry('build29',(EFFECT,),m)['memory']
        self.assertEqual(read(out,EFFECT+366,1),1);self.assertEqual(read(out,EFFECT+350,2),65535)
        self.assertEqual(read(out,EFFECT+372,1),2)
    def test_signatures_include_stack_arguments(self):
        self.assertEqual(ARITIES['curve20_setup'],5);self.assertEqual(ARITIES['object_filter'],7)
        self.assertEqual(ARITIES['object_feedback'],6);self.assertEqual(ARITIES['tone_parameters'],3)

if __name__=='__main__':unittest.main()
