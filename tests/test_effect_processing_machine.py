"""Focused regressions for recovered effect control and shared original state."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_processing_machine import EffectProcessingProgram,REGIONS,TABLES,STATIC,SERVICES,offset
from verify_effect_processing import baseline,setword,EFFECTS,CONTROL,CONFIG,SAMPLES,ARENA,Script

class EffectProcessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectProcessingProgram()
    def fixture(self,phase=0,state=0):
        m=baseline();setword(m,EFFECTS,2,1);setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+2,1,1)
        setword(m,EFFECTS+10,phase,1);setword(m,EFFECTS+12,state,1);setword(m,EFFECTS+288,65536)
        setword(m,CONFIG+40,SAMPLES+2048);setword(m,CONFIG+44,SAMPLES+2048);return m
    def byte(self,result,address):return result['memory'][0][address-0x01c1f180]
    def test_four_embedded_tables_are_not_instructions(self):
        for start,end in TABLES.values():self.assertFalse(any(start<=pc<end for pc in self.program.code))
    def test_dispatch_table_targets_original_body(self):
        start,end=TABLES['dispatch_branches'];raw=self.program.data['dispatch_branches']
        for i in range(0,len(raw),2):self.assertIn(start+2*int.from_bytes(raw[i:i+2],'little'),self.program.code)
    def test_six_argument_estimator(self):
        m=self.fixture();setword(m,EFFECTS,5,1)
        no=self.program.execute(m,'extra_cost',(EFFECTS,1,100,1,0,1),Script())
        yes=self.program.execute(m,'extra_cost',(EFFECTS,1,100,1,1,1),Script())
        self.assertEqual(no['value'],0);self.assertEqual(yes['value'],1200);self.assertFalse(yes['calls'])
    def test_phase_three_counter_expiry(self):
        m=self.fixture(3);setword(m,EFFECTS+11,1,1)
        r=self.program.execute(m,'individual',(0,SAMPLES,16),Script())
        self.assertEqual(self.byte(r,EFFECTS+10),1);self.assertEqual(self.byte(r,EFFECTS+11),0)
    def test_phase_three_counter_continues(self):
        m=self.fixture(3);setword(m,EFFECTS+11,4,1)
        r=self.program.execute(m,'individual',(0,SAMPLES,16),Script())
        self.assertEqual(self.byte(r,EFFECTS+10),3);self.assertEqual(self.byte(r,EFFECTS+11),3)
    def test_completed_fade_retains_terminal_counter(self):
        m=self.fixture(1);setword(m,EFFECTS+11,3,1)
        r=self.program.execute(m,'individual',(0,SAMPLES,16),Script())
        self.assertEqual(self.byte(r,EFFECTS+10),0);self.assertEqual(self.byte(r,EFFECTS+11),3)
    def test_zero_divisor_preserves_original_zero_quotient(self):
        m=self.fixture();setword(m,EFFECTS+292,123)
        r=self.program.execute(m,'dispatch',(EFFECTS,SAMPLES,0,1),Script())
        at=EFFECTS+292-0x01c1f180;self.assertEqual(int.from_bytes(r['memory'][0][at:at+4],'little'),123)
        self.assertIn(0x01c0e2b4,r['visited'])
    def test_stereo_recursion_restores_primary_history(self):
        m=self.fixture();setword(m,CONTROL+10,3,1);setword(m,EFFECTS+292,64000)
        r=self.program.execute(m,'dispatch',(EFFECTS,SAMPLES,16,1),Script())
        self.assertEqual(r['real_calls'].count(REGIONS['dispatch'][0]),1);self.assertEqual(self.byte(r,CONTROL+10),3)
    def test_group_executes_real_resampling(self):
        m=self.fixture();setword(m,ARENA,0x100,4)
        for off,val in ((0,2),(1,1),(2,1),(6,1)):setword(m,EFFECTS+480+off,val,1)
        setword(m,EFFECTS+768,65536)
        r=self.program.execute(m,'grouped',(ARENA,2,SAMPLES,16),Script())
        for entry in (0x01c07986,0x01c08a76,REGIONS['individual'][0],REGIONS['dispatch'][0]):self.assertIn(entry,r['real_calls'])
    def test_stack_abis_are_explicit(self):
        self.assertEqual(SERVICES[0x01c08b3e],9);self.assertEqual(SERVICES[0x01c0ba14],8)
        self.assertEqual(SERVICES[0x01c0b524],5);self.assertEqual(SERVICES[0x01c0bbce],4)
    def test_ro_tables_bind_original_image(self):
        for name,(start,end) in STATIC.items():self.assertEqual(self.program.data[name],self.program.app[offset(start):offset(end)])
    def test_unmodeled_services_require_callback(self):
        m=self.fixture();setword(m,EFFECTS,5,1)
        with self.assertRaisesRegex(ValueError,'unmodeled effect call'):self.program.execute(m,'dispatch',(EFFECTS,SAMPLES,16,1))
    def test_ir_retry_executes_actual_reset_and_retains_countdown(self):
        m=self.fixture(state=2);setword(m,EFFECTS,7,1);setword(m,EFFECTS+13,32,1);setword(m,EFFECTS+288,ARENA)
        setword(m,ARENA,1);setword(m,ARENA+4,1);setword(m,ARENA+8,7);setword(m,ARENA+12,9)
        setword(m,ARENA+24,ARENA+1024);setword(m,ARENA+48,ARENA+4000);setword(m,0x01c34198,0x01c04862)
        for i in range(258):setword(m,ARENA+1024+4*i,0x12345678)
        for i in range(256):setword(m,ARENA+4000+4*i,0xabcdef01)
        r=self.program.execute(m,'individual',(0,SAMPLES,128),Script(clocks=(500,)))
        self.assertIn(0x01c11f76,r['real_calls']);self.assertEqual(r['value'],0xffffffff)
        self.assertEqual(self.byte(r,EFFECTS+13),31)
        self.assertEqual(r['memory'][2][1024:1024+258*4],bytes(258*4))
        self.assertEqual(r['memory'][2][4000:4000+256*4],bytes(256*4))
        self.assertEqual(r['memory'][2][8:16],bytes(8))
    def test_group_reloads_list_after_clock_callback(self):
        m=self.fixture();setword(m,ARENA,0x100)
        for slot,kind in ((1,5),(2,27)):
            for off,value in ((0,kind),(1,1),(2,1),(6,1)):setword(m,EFFECTS+480*slot+off,value,1)
        setword(m,0x01c34198,0x01c04862);setword(m,0x01c34444,1000000)
        r=self.program.execute(m,'grouped',(ARENA,2,SAMPLES,16),Script(((1,ARENA+1,2,1),),clocks=(200,300,400,500)))
        targets=[call[0] for call in r['calls']]
        self.assertNotIn(0x01c08f80,targets);self.assertIn(0x01c0a7aa,targets)

if __name__=='__main__':unittest.main()
