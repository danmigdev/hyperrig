"""Behavioral original-instruction tests for generated coefficient transitions."""
import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from dsp_transition_machine import DspTransitionProgram,CONTROL,CALLBACKS,CONFIGURATION
from verify_dsp_transition import initial


class TransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=DspTransitionProgram()

    def request(self,state,parameters,duration=1,boundary=None):
        return self.program.execute(state,"request",(),duration,parameters=parameters,boundary=boundary)

    def test_index_zero_has_distinct_lower_clamp(self):
        for index,expected in ((0,-240),(1,-120),(4,-120),(6,-120),(0xFFFFFFFF,-120)):
            result=self.program.execute(initial(),"clamp",(),index,0x80000000)
            self.assertEqual(result["value"],expected&0xFFFFFFFF)

    def test_sixth_parameter_rounds_symmetrically(self):
        for value,expected in ((-8,-10),(-7,-5),(-3,-5),(-2,0),(2,0),(3,5),(7,5),(8,10)):
            self.assertEqual(self.program.execute(initial(),"clamp",(),5,value&0xFFFFFFFF)["value"],expected&0xFFFFFFFF)

    def test_unchanged_request_preserves_pending_transition(self):
        state=initial();state[4][1]=255
        result=self.request(state,(0,)*6,255)
        self.assertEqual(result["value"],0)
        self.assertEqual(result["memory"],tuple(map(bytes,state)))
        self.assertFalse(result["production_calls"])

    def test_unchanged_request_can_still_reset_disabled_bank(self):
        state=initial();state[4][28]=0;state[4][1]=255
        result=self.request(state,(0,)*6)
        self.assertEqual(result["value"],0);self.assertEqual(result["memory"][4][28],1)
        self.assertEqual(result["memory"][4][1],0)
        self.assertEqual(len(result["production_calls"]),4)

    def test_new_request_executes_four_generators_and_preserves_active_filters(self):
        state=initial();result=self.request(state,(10,20,-30,40,-50,0))
        self.assertEqual(result["value"],1)
        self.assertEqual(len(result["production_calls"]),4)
        self.assertEqual(result["memory"][5],bytes(state[5]))
        self.assertEqual(result["memory"][0],bytes(state[0]))
        self.assertEqual(result["memory"][4][1],1)

    def test_one_step_stores_zero_coefficient_and_gain_deltas(self):
        result=self.request(initial(),(10,20,-30,40,-50,0),1)
        self.assertEqual(result["memory"][9][80:160],bytes(80))
        self.assertEqual(result["memory"][9][164:168],bytes(4))
        self.assertEqual(struct.unpack_from("<I",result["memory"][9],172)[0],1)

    def test_duration_one_and_two_have_different_step_rule(self):
        for duration,steps in ((0,1),(1,1),(2,8),(255,1020),(256,1020),(0x80000000,1),(0xFFFFFFFF,1)):
            result=self.request(initial(),(1,0,0,0,0,0),duration)
            self.assertEqual(struct.unpack_from("<I",result["memory"][9],172)[0],steps)

    def test_counter_wrap_and_notification_order(self):
        state=initial();state[4][1]=255
        struct.pack_into("<2I",state[6],728,0xFFFFFFFF,0x0201A9EA)
        seen=[]
        def callback(token,value,view):
            snapshot=view.snapshot();seen.append((token,value,snapshot))
            self.assertEqual(struct.unpack_from("<I",snapshot[6],728)[0],0)
            self.assertEqual(snapshot[4][1],0)
            self.assertEqual(struct.unpack_from("<h",snapshot[4],228)[0],0)
            self.assertEqual(snapshot[9],bytes(state[9]))
        result=self.request(state,(1,0,0,0,0,8),2,callback)
        self.assertEqual(len(seen),1);self.assertEqual(seen[0][:2],(0x0201A9EA,10))
        self.assertEqual(struct.unpack_from("<6h",result["memory"][4],218),(1,0,0,0,0,10))

    def test_quantized_no_change_avoids_callback(self):
        state=initial();struct.pack_into("<I",state[6],732,0x0201A9EA)
        result=self.request(state,(0,0,0,0,0,2))
        self.assertEqual(result["value"],0);self.assertFalse(result["notification_calls"])

    def test_callback_mutated_gain_changes_generated_gain_step(self):
        state=initial();struct.pack_into("<I",state[6],732,0x0201A9EA)
        def callback(_token,_value,view):view.mutate(CONFIGURATION,0,4)
        result=self.request(state,(0,0,0,0,0,5),2,callback)
        self.assertEqual(struct.unpack_from("<2I",result["memory"][9],160),(65536,8192))

    def test_callback_parameter_mutation_is_overwritten_by_captured_inputs(self):
        state=initial();struct.pack_into("<I",state[6],732,1)
        def callback(_token,_value,view):view.mutate(CONTROL+218,32767,2);view.mutate(CONTROL+228,32768,2)
        result=self.request(state,(7,0,0,0,0,5),2,callback)
        self.assertEqual(struct.unpack_from("<6h",result["memory"][4],218),(7,0,0,0,0,5))

    def test_real_request_then_samples_consumes_exact_targets(self):
        state=self.program.execute(initial(),"startup")["memory"]
        requested=self.request(state,(-24,12,-36,48,-60,0),1)["memory"]
        processed=self.program.execute(requested,"process",(123,-456,789))["memory"]
        for i in range(4):
            self.assertEqual(processed[5][44*i:44*i+20],requested[9][20*i:20*i+20])
            self.assertEqual(processed[5][44*i+40],requested[9][168+i])
        self.assertEqual(processed[0][:4],requested[9][160:164])
        self.assertEqual(struct.unpack_from("<I",processed[4],32)[0],0)

    def test_request_interrupts_active_transition_without_clearing_histories(self):
        state=self.program.execute(initial(),"startup")["memory"]
        state=self.request(state,(0,60,-60,60,-60,0),255)["memory"]
        state=self.program.execute(state,"process",tuple(range(128)))["memory"]
        changed=self.request(state,(0,-60,60,-60,60,0),2)["memory"]
        self.assertEqual(changed[5],state[5])
        self.assertEqual(struct.unpack_from("<I",changed[9],172)[0],8)
        self.assertEqual(changed[4][1],1)

    def test_domain_and_missing_notification_rejected(self):
        with self.assertRaises(ValueError):self.request(initial(),(0,)*5)
        with self.assertRaises(ValueError):self.request(initial(),(32768,0,0,0,0,0))
        state=initial();state[4][28]=0;struct.pack_into("<h",state[4],218,1281)
        with self.assertRaises(ValueError):self.request(state,(0,)*6)
        state=initial();struct.pack_into("<I",state[6],732,1)
        with self.assertRaises(ValueError):self.request(state,(0,0,0,0,0,3))


if __name__=="__main__":unittest.main()
