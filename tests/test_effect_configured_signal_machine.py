"""Focused producer/consumer state and invocation-boundary observations."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_configured_signal_machine import EffectConfiguredSignalProgram,carry_preparation_into_audio,MAPPED,CONSTRUCTOR
from verify_effect_configured_signal import initialize,baseline,setword,EFFECTS,CONFIG,SAMPLES,Script

class EffectConfiguredSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectConfiguredSignalProgram()
    def fixture(self,kind,seed=1):
        m=baseline(seed);initialize(m,EFFECTS,kind,seed);return m
    def word(self,m,address):
        for (base,n),data in zip(MAPPED,m):
            if base<=address<=address+4<=base+n:return int.from_bytes(data[address-base:address-base+4],'little')
        self.fail('test word outside public map')
    def mutable(self,r):return list(map(bytearray,r['memory']))
    def test_shared_instruction_definitions_are_identical(self):
        p=self.program
        for pc in p.signal.code.keys()&p.construction.code.keys():self.assertEqual(p.signal.code[pc],p.construction.code[pc])
    def test_real_allpass_table_and_duplicate_endpoint(self):
        r=self.program.prepare(self.fixture(13),EFFECTS)
        self.assertFalse(r['calls']);self.assertIn(0x020285d4,r['internal_calls'])
        self.assertEqual(self.word(r['memory'],EFFECTS+468),self.word(r['memory'],EFFECTS+472))
        table=[self.word(r['memory'],EFFECTS+340+4*i) for i in range(33)]
        self.assertGreater(len(set(table)),16)
    def test_cold_allpass_coefficient_comes_from_real_midpoint(self):
        r=self.program.prepare(self.fixture(13),EFFECTS)
        self.assertEqual(self.word(r['memory'],EFFECTS+296),self.word(r['memory'],EFFECTS+404))
    def test_allpass_reprepare_retains_current_history_and_coefficient(self):
        a=self.program.prepare(self.fixture(13),EFFECTS)
        b=self.program.execute(a['memory'],'allpass',(SAMPLES,32,EFFECTS+288))
        m=self.mutable(b);setword(m,EFFECTS+72,85,2);r=self.program.prepare(m,EFFECTS)
        for off in (288,296,308,312,316,320,324,328,332,336):
            self.assertEqual(self.word(r['memory'],EFFECTS+off),self.word(b['memory'],EFFECTS+off))
        self.assertNotEqual(self.word(r['memory'],EFFECTS+404),self.word(b['memory'],EFFECTS+404))
    def test_gate_reprepare_preserves_envelope_and_gain(self):
        m=self.fixture(1);setword(m,EFFECTS+308,0x12345678);setword(m,EFFECTS+312,45678)
        r=self.program.prepare(m,EFFECTS)
        self.assertEqual(self.word(r['memory'],EFFECTS+308),0x12345678)
        self.assertEqual(self.word(r['memory'],EFFECTS+312),45678)
    def test_gate_thresholds_are_actual_constructor_results(self):
        m=self.fixture(1);a=self.program.prepare(m,EFFECTS)
        m=self.mutable(a);setword(m,EFFECTS+70,-12,2);b=self.program.prepare(m,EFFECTS)
        self.assertGreater(self.word(a['memory'],EFFECTS+288),self.word(a['memory'],EFFECTS+292))
        self.assertGreater(self.word(b['memory'],EFFECTS+288),self.word(a['memory'],EFFECTS+288))
    def test_state_variable_coefficients_are_produced_by_dispatch(self):
        a=self.program.prepare(self.fixture(38),EFFECTS)
        self.assertEqual(self.word(a['memory'],EFFECTS+304),0)
        b=self.program.execute(a['memory'],'dispatch',(EFFECTS,SAMPLES,32,1),Script())
        self.assertNotEqual(self.word(b['memory'],EFFECTS+304),0)
        self.assertIn(0x01c1ee40,b['real_calls'])
    def test_filter_reprepare_retains_integrators_and_residuals(self):
        a=self.program.prepare(self.fixture(38),EFFECTS)
        b=self.program.execute(a['memory'],'dispatch',(EFFECTS,SAMPLES,32,1),Script())
        m=self.mutable(b);setword(m,EFFECTS+72,900,2);r=self.program.prepare(m,EFFECTS)
        for off in (288,292,296,300):self.assertEqual(self.word(r['memory'],EFFECTS+off),self.word(b['memory'],EFFECTS+off))
        self.assertNotEqual(self.word(r['memory'],EFFECTS+380),self.word(b['memory'],EFFECTS+380))
    def test_rate_change_preserves_phase_and_changes_increment(self):
        m=self.fixture(13);setword(m,EFFECTS+288,0x12345678);a=self.program.prepare(m,EFFECTS)
        m=self.mutable(a);setword(m,CONFIG+8,96000);b=self.program.prepare(m,EFFECTS)
        self.assertEqual(self.word(b['memory'],EFFECTS+288),0x12345678)
        self.assertEqual(self.word(b['memory'],EFFECTS+292),self.word(a['memory'],EFFECTS+292)//2)
    def test_mode_two_and_three_publish_same_effective_rate(self):
        for mode in (2,3):
            m=self.fixture(1);setword(m,EFFECTS+6,mode,1);r=self.program.prepare(m,EFFECTS)
            self.assertEqual(self.word(r['memory'],CONFIG+36),96000)
    def test_constructed_filter_preserves_raw_short_wrap_count(self):
        a=self.program.prepare(self.fixture(38),EFFECTS)
        b=self.program.execute(a['memory'],'dispatch',(EFFECTS,SAMPLES,32,1),Script())
        small=self.program.execute(b['memory'],'variable_filter',(SAMPLES,4,EFFECTS+288))
        wrapped=self.program.execute(b['memory'],'variable_filter',(SAMPLES,0x40000004,EFFECTS+288))
        self.assertEqual(small['memory'],wrapped['memory'])
    def test_external_builders_remain_audited_call_sites(self):
        p=self.program
        self.assertTrue(p.external_sites)
        self.assertTrue(all(pc in p.construction.code and target!=CONSTRUCTOR for pc,(target,_) in p.external_sites.items()))
        self.assertEqual({arity for _,arity in p.external_sites.values()},{1,2})
    def test_audio_handoff_keeps_suspended_private_frames(self):
        import verify_audio_task as task
        m=task.baseline();initialize(m,EFFECTS,13)
        audio=self.program.audio.machine(m,Script(audio=True))
        audio.resume(1,1)
        control=(audio.pc,dict(audio.regs),list(audio.returns),repr(audio.frames),dict(audio.else_skips))
        old_stack={p:v for p,v in audio.memory.items() if 0x30000000<=p<0x30001020}
        prepared=self.program.prepare(audio.snapshot(),EFFECTS,mapped=task.MAPPED)
        carry_preparation_into_audio(audio,prepared['memory'])
        self.assertEqual(control,(audio.pc,dict(audio.regs),list(audio.returns),repr(audio.frames),dict(audio.else_skips)))
        self.assertEqual(old_stack,{p:v for p,v in audio.memory.items() if 0x30000000<=p<0x30001020})
        self.assertEqual(audio.snapshot(),prepared['memory'])

if __name__=='__main__':unittest.main()
