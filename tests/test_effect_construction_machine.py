"""Focused native witnesses for effect-construction contracts and state order."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_construction_machine import EffectConstructionProgram,REGIONS,STATIC,MAPPED,RAM
from verify_effect_construction import initial,setword,EFFECT,CFG,ARENA,Script

def word(memory,address,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
    raise ValueError('test address')
class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectConstructionProgram()
    def run_entry(self,name,memory=None,args=(),mutations=()):
        return self.program.execute(initial() if memory is None else memory,name,args,Script(mutations))
    def test_complete_region_count(self):
        self.assertEqual(len(REGIONS),14)
        self.assertEqual(sum(any(a<=pc<b for a,b in REGIONS.values()) for pc in self.program.code),1242)
    def test_dispatch_targets_exclude_table_and_packet_second_halves(self):
        for name,width,count in (('construct_branches',2,39),('tempo_branches',1,5)):
            start,end=STATIC[name];data=self.program.data[name]
            for i in range(count):
                target=start+2*int.from_bytes(data[i*width:(i+1)*width],'little')
                self.assertIn(target,self.program.code);self.assertNotIn(target,self.program.parallel_seconds)
    def test_mode_fold_and_raw_shift_word(self):
        for value,expected in ((0,0),(1,1),(2,1),(3,1),(4,4),(0xffffffff,0xffffffff)):
            self.assertEqual(self.run_entry('mode_shift',args=(value,))['result'],(expected,0))
    def test_packed_bias_zero_encoding(self):
        for value,expected in ((0,0),(32,0),(1,-15),(15,-1),(16,0),(31,15),(0xffffffff,15)):
            self.assertEqual(self.run_entry('packed_bias',args=(value,))['result'][0],expected&0xffffffff)
    def test_size_is_capped_at_2048(self):
        m=initial();setword(m,CFG+8,0xffffffff)
        for type_ in (0,11,12,15):self.assertEqual(self.run_entry('size',m,(type_,))['result'][0],2048)
    def test_zero_tempo_uses_original_zero_division(self):
        m=initial();setword(m,CFG+12,0)
        self.assertEqual(self.run_entry('tempo_samples',m,(1,))['result'],(0,0))
    def test_tempo_parameter_indices(self):
        for type_,expected in ((10,-1),(11,3),(12,4),(13,3),(14,3),(15,2),(16,-1)):
            self.assertEqual(self.run_entry('tempo_parameter',args=(type_,))['result'][0],expected&0xffffffff)
    def test_logarithm_power_of_two_words(self):
        for value,result in ((0x3f800000,0),(0x40000000,0x3f800000),(0x3f000000,0xbf800000)):
            self.assertEqual(self.run_entry('logarithm',args=(value,))['result'][0],result)
    def test_q30_saturation_and_nan(self):
        for value,expected in ((0,0),(0x3f000000,0x20000000),(0xbf000000,0xe0000000),
            (0x40000000,0x7fffffff),(0xc0000000,0x80000000),(0xffc00000,0x7fffffff)):
            self.assertEqual(self.run_entry('q30',args=(value,))['result'][0],expected)
    def test_unknown_type_still_publishes_rate(self):
        m=initial(255);setword(m,EFFECT+6,255,1)
        out=self.run_entry('construct',m,(EFFECT,))
        self.assertEqual(word(out['memory'],CFG+36),(48000<<31)&0xffffffff)
        self.assertEqual(out['result'],(0,0));self.assertEqual(out['calls'],[])
    def test_builder_mutation_changes_final_gain_destination(self):
        m=initial(17);mutations=((0x0202b838,0,EFFECT,19,1),(0x0202b838,0,EFFECT+80,100,2))
        out=self.run_entry('construct',m,(EFFECT,),mutations)
        self.assertEqual(word(out['memory'],EFFECT+460),32768)
        self.assertEqual(out['service_sites'][0][2],1)
    def test_signature_service_receives_object_and_parameters(self):
        m=initial(30);setword(m,ARENA,0x53525631)
        out=self.run_entry('construct',m,(EFFECT,))
        self.assertEqual(out['calls'][0][0],0x0202cf5a)
        self.assertEqual(out['calls'][0][1][:2],(ARENA,EFFECT+70))
    def test_gain_history_initializes_only_when_both_words_zero(self):
        for left,right in ((0,0),(1,0),(0,1)):
            m=initial(30);setword(m,EFFECT+288,left);setword(m,EFFECT+296,right)
            out=self.run_entry('construct',m,(EFFECT,))['memory']
            if left or right:self.assertEqual((word(out,EFFECT+288),word(out,EFFECT+296)),(left,right))
            else:self.assertEqual((word(out,EFFECT+288),word(out,EFFECT+296)),(word(out,EFFECT+292),word(out,EFFECT+300)))
    def test_type36_zero_parameters_disable_six_real_generators(self):
        m=initial(36)
        for i in range(6):setword(m,EFFECT+70+2*i,0,2)
        out=self.run_entry('construct',m,(EFFECT,))
        self.assertEqual(len(out['coefficient_requests']),6)
        self.assertEqual(word(out['memory'],EFFECT+472),0)
        self.assertTrue(all(request[3]==0 for request in out['coefficient_requests']))
    def test_type37_packed_packet_preserves_full_middle_parameter(self):
        m=initial(37);setword(m,EFFECT+74,-7,2);setword(m,EFFECT+82,(31<<5)|1,2)
        out=self.run_entry('construct',m,(EFFECT,));requests=out['coefficient_requests']
        self.assertEqual(len(requests),7)
        self.assertEqual([requests[i][3] for i in (2,3,4)],
            [struct.unpack('<I',struct.pack('<f',v))[0] for v in (15.,-7.,-15.)])
    def test_type37_mode_change_clears_exact_history_span(self):
        m=initial(37);setword(m,EFFECT+476,1)
        out=self.run_entry('construct',m,(EFFECT,))['memory']
        self.assertEqual(out[0][EFFECT-RAM+388:EFFECT-RAM+464],bytes(76))
        self.assertEqual(word(out,EFFECT+476),0)
    def test_type37_unchanged_mode_keeps_history(self):
        m=initial(37);setword(m,EFFECT+476,0)
        out=self.run_entry('construct',m,(EFFECT,))['memory']
        self.assertEqual(out[0][EFFECT-RAM+388:EFFECT-RAM+464],m[0][EFFECT-RAM+388:EFFECT-RAM+464])
    def test_type26_disabling_retains_coefficients_and_residual(self):
        m=initial(26);setword(m,EFFECT+76,0,2)
        out=self.run_entry('type26',m,(EFFECT,))['memory']
        for i in range(4):
            self.assertEqual(word(out,EFFECT+328+44*i,1),0)
            for offset in (*range(40),41,42,43):
                self.assertEqual(word(out,EFFECT+288+44*i+offset,1),word(m,EFFECT+288+44*i+offset,1))
    def test_type13_all_pass_table_uses_real_math(self):
        out=self.run_entry('construct',initial(13),(EFFECT,))
        self.assertEqual(out['internal_calls'].count(0x02028646),33)
        self.assertEqual(out['internal_calls'].count(0x02028676),33)
        self.assertEqual(word(out['memory'],EFFECT+472),word(out['memory'],EFFECT+468))
    def test_rate_alias_is_read_again_for_next_generated_section(self):
        m=initial(4);e=CFG-280
        for i in range(480):setword(m,e+i,word(m,EFFECT+i,1),1)
        setword(m,CFG+8,48000)
        out=self.run_entry('construct',m,(e,))
        self.assertEqual(len(out['coefficient_requests']),3)
        self.assertNotEqual(word(out['memory'],CFG+8),48000)

if __name__=='__main__':unittest.main()
