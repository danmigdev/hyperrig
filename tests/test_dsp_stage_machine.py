"""Focused original-instruction witnesses for stage routing and fixed-point mix."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from dsp_stage_machine import DspStageProgram,REGIONS,RAM,SAMPLES,ARENA
from verify_dsp_stage import baseline,put,CONTROL,EFFECTS,AUTOMATION,Script

def word(data,p):return int.from_bytes(data[p:p+4],"little")
class StageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=DspStageProgram()
    def execute(self,name,args=(),memory=None,script=None):return self.program.execute(memory or baseline(),name,args,script or Script())
    def test_zero_clock_has_no_service(self):self.assertEqual(self.execute('clock')['calls'],[])
    def test_unreviewed_clock_rejected(self):
        memory=baseline();put(memory[0],0x01c34198-RAM,1)
        with self.assertRaisesRegex(ValueError,'unmodeled stage call'):self.execute('clock',memory=memory)
    def test_ir_delay_is_only_for_inactive_object(self):
        memory=baseline();self.assertEqual(self.execute('ir_delay',(ARENA,),memory)['value'],34)
        put(memory[2],0,1);self.assertEqual(self.execute('ir_delay',(ARENA,),memory)['value'],0)
        self.assertEqual(self.execute('ir_delay',(0,),memory)['value'],0)
    def test_clear_preserves_coefficients_and_flags(self):
        memory=baseline();before=bytes(memory[0]);after=self.execute('clear',(0x01c2f3a0,),memory)['memory'][0]
        for i in range(4):
            p=0x01c2f3a0-RAM+44*i;self.assertEqual(after[p:p+20],before[p:p+20]);self.assertEqual(after[p+20:p+40],bytes(20));self.assertEqual(after[p+40:p+44],before[p+40:p+44])
    def test_copy_prefetches_four_words_before_writing(self):
        memory=baseline()
        for i in range(9):put(memory[1],4*i,i+1)
        out=self.execute('copy',(SAMPLES+4,SAMPLES,8),memory)['memory'][1]
        self.assertEqual([word(out,4*i) for i in range(9)],[1,1,2,3,4,4,6,7,8])
    def test_mix_exact_int_min_is_representable(self):
        memory=baseline();put(memory[1],0,0x80000000)
        for i,v in enumerate((SAMPLES,SAMPLES+512,1,SAMPLES,0,32768,0)):put(memory[2],4*i,v)
        self.assertEqual(word(self.execute('mix',(ARENA,),memory)['memory'][1],0),0x80000000)
    def test_mix_negative_overflow_uses_negative_int_max(self):
        memory=baseline();put(memory[1],0,0x80000000)
        for i,v in enumerate((SAMPLES,SAMPLES+512,1,SAMPLES,0,65536,0)):put(memory[2],4*i,v)
        self.assertEqual(word(self.execute('mix',(ARENA,),memory)['memory'][1],0),0x80000001)
    def test_mix_positive_overflow_saturates(self):
        memory=baseline();put(memory[1],0,0x7fffffff)
        for i,v in enumerate((SAMPLES,SAMPLES+512,1,SAMPLES,0,65536,0)):put(memory[2],4*i,v)
        self.assertEqual(word(self.execute('mix',(ARENA,),memory)['memory'][1],0),0x7fffffff)
    def test_automation_last_step_caches_delta(self):
        memory=baseline();r=memory[0];p=AUTOMATION-RAM
        for off,v in ((0,1),(3,1),(5,0),(45,1)):put(r,p+off,v,1)
        put(r,p+128,100);put(r,EFFECTS-RAM+288,25)
        out=self.execute('stage',(0,SAMPLES,128),memory)['memory'][0]
        self.assertEqual(word(out,p+288),75);self.assertEqual(word(out,EFFECTS-RAM+288),100);self.assertEqual(out[p],0)
    def test_automation_stage_one_does_not_advance(self):
        memory=baseline();put(memory[0],AUTOMATION-RAM,2,1)
        self.assertEqual(self.execute('stage',(1,SAMPLES,128),memory)['memory'][0][AUTOMATION-RAM],2)
    def test_empty_route_releases_delay_slot(self):
        memory=baseline();put(memory[0],CONTROL-RAM+180,1,1);put(memory[0],CONTROL-RAM+17,1,1)
        out=self.execute('stage',(0,SAMPLES,128),memory)['memory'][0]
        self.assertEqual(out[CONTROL-RAM+180],255);self.assertEqual(out[CONTROL-RAM+17],0)
    def test_stage_frame_counter_wraps(self):
        memory=baseline();put(memory[0],CONTROL-RAM+92,0xffffffff)
        self.assertEqual(word(self.execute('stage',(0,SAMPLES,128),memory)['memory'][0],CONTROL-RAM+92),0)
    def test_descriptor_mutation_survives_second_clock(self):
        memory=baseline();r=memory[0];put(r,0x01c34198-RAM,0x01c04862);put(r,0x01c32dac-RAM,1,1)
        for i,v in enumerate((SAMPLES,SAMPLES,0,SAMPLES,0,0,0)):put(memory[2],4*i,v)
        script=Script(((2,ARENA+20,123,4),))
        result=self.execute('stereo_finish',(ARENA,SAMPLES,0,0,0),memory,script)
        self.assertEqual(word(result['memory'][2],20),123)
    def test_regions_decode_exactly_to_end(self):
        for name,(start,end) in REGIONS.items():
            pcs=[p for p in self.program.code if start<=p<end]
            self.assertEqual(max(pcs)+self.program.code[max(pcs)][1],end)

if __name__=='__main__':unittest.main()
