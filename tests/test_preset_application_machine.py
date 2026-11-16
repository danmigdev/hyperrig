"""Behavioral expectations for original preset application, not generated C formulas."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from preset_application_machine import PresetApplicationProgram,GLOBAL,STATE,WORKING,LOCAL,CALLBACKS
from verify_preset_application import initial,put,Script

class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=PresetApplicationProgram()
    def run_case(self,m=None,preset=0,plan=None,records=None,mutations=None):
        self.script=Script(plan,records,mutations)
        self.last=self.program.execute(initial() if m is None else m,'apply',preset,boundary=self.script)
        return self.last
    def test_preset_marker_clamps_at_127(self):
        for value,expected in ((0,0),(126,126),(127,255),(0xffffffff,255)):
            self.assertEqual(self.run_case(preset=value)['memory'][0][20],expected)
    def test_capture_ir_statuses_are_not_effect_failure_count(self):
        m=initial();m[2][2:4]=b'\x01\x02'
        r=self.run_case(m,plan={0x020087cc:0xfffffffe,0x02008a62:0xfffffffd})
        self.assertEqual(r['result'],0);self.assertEqual(r['memory'][-1],bytes.fromhex('fefffffffdffffff'))
    def test_allocation_minus_two_skips_fallback(self):
        r=self.run_case(initial([5]),plan={0x0202e710:0xfffffffe})
        self.assertEqual(r['result'],1);self.assertNotIn(0x0202ea90,self.script.seen)
    def test_minus_three_retries_after_compaction(self):
        r=self.run_case(initial([5]),plan={0x0202e710:[0xfffffffd,0]})
        self.assertEqual(r['result'],0);self.assertEqual(self.script.seen[0x0202e710],2)
        self.assertEqual(self.script.seen[0x0202ed7e],1)
    def test_minus_four_also_retries(self):
        self.run_case(initial([5]),plan={0x0202e710:[0xfffffffc,0]})
        self.assertEqual(self.script.seen[0x0202e710],2)
    def test_other_allocation_failure_calls_fallback(self):
        r=self.run_case(initial([5]),plan={0x0202e710:0xffffffff,0x0202ea90:0xfffffffe})
        self.assertEqual(r['result'],1);self.assertEqual(self.script.seen[0x0202ea90],1)
    def test_activation_retry_success_is_not_counted(self):
        r=self.run_case(initial([1]),plan={0x0203060a:[1,0]})
        self.assertEqual(r['result'],0);self.assertEqual(self.script.seen[0x0203060a],2)
    def test_activation_retry_failure_is_counted(self):
        self.assertEqual(self.run_case(initial([1]),plan={0x0203060a:1})['result'],1)
    def test_fast_reuse_does_not_allocate(self):
        self.run_case(initial([1,5],fast=True))
        self.assertNotIn(0x0202e710,self.script.seen);self.assertEqual(self.script.seen[0x0202fee4],4)
    def test_fast_apply_failure_keeps_completed_service_effects(self):
        def apply(args,m,index):
            m.write(STATE+100,index+1,4)
            return int(args[4]==0)
        r=self.run_case(initial([1],fast=True),plan={0x0202fee4:apply})
        self.assertEqual(int.from_bytes(r['memory'][1][100:104],'little'),2)
        self.assertIn(0x020306ee,self.script.seen)
    def test_cleanup_failure_preserves_minus_110(self):
        m=initial();put(m[1],416,1)
        r=self.run_case(m,plan={0x0200907a:1})
        self.assertEqual(int.from_bytes(r['memory'][-1][:4],'little'),0xffffff92)
    def test_embedded_capture_skips_installation(self):
        m=initial();m[2][2]=1;put(m[0],60,0x02033c8c)
        self.run_case(m,plan={0x020087cc:0xffffff91})
        self.assertNotIn(0x02008586,self.script.seen);self.assertIn(0x02009082,self.script.seen)
    def test_mode_service_before_outputs_clear(self):
        m=initial();m[2][1347]=128;put(m[-1],0,123)
        r=self.run_case(m)
        self.assertEqual(r['calls'][0][0],0x0202902a)
        self.assertEqual(int.from_bytes(r['calls'][0][2][-1][:4],'little'),123)
    def test_notification_packet_retains_original_tag(self):
        m=initial();put(m[6],24,0x87654321)
        r=self.run_case(m,plan={0x02028eb2:2})
        self.assertEqual(r['calls'][-1][:2],(0x02002d10,(30,0x4ffff,0,0,0)))
        r=self.run_case(m,plan={0x02028eb2:1})
        self.assertEqual(r['calls'][-1][:2],(0x02002d10,(30,0x3ffff,0x87654321,0,0)))
    def test_type_five_swaps_only_parameter_zero_and_four(self):
        for index,expected in enumerate((4,1,2,3,0,5,6)):
            r=self.program.execute(initial(),'parameter_order',5,index)
            self.assertEqual(r['result'],expected)
    def test_absent_metadata_and_invalid_indices_return_zero(self):
        for type_,index in ((0,0),(6,0),(24,6),(40,0),(5,7),(0xffffffff,0)):
            self.assertEqual(self.program.execute(initial(),'metadata',type_,index)['result'],0)
    def test_parameter_getter_sign_extends_and_requires_presence(self):
        m=initial([7],fast=True);put(m[3],74,0x8001,2)
        self.assertEqual(self.program.execute(m,'parameter',0,2)['result'],0xffff8001)
        m[3][2]=0;self.assertEqual(self.program.execute(m,'parameter',0,2)['result'],0)
    def test_raw_effect_enable_byte_is_not_normalized_by_getter(self):
        m=initial([1],fast=True);m[3][1]=7;m[2][14]=1
        self.run_case(m)
        calls=[x for x in self.last['calls'] if x[0]==0x02030602]
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][1][:2],(0,1))

if __name__=='__main__':unittest.main()
