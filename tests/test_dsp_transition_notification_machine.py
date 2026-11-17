"""Focused original-instruction checks for the installed notification."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from dsp_transition_notification_machine import DspTransitionNotificationProgram,STATE,INPUT,NOTIFICATION
from verify_dsp_transition_notification import initial


class NotificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=DspTransitionNotificationProgram()

    def notify(self,value,base=0):
        memory=initial();struct.pack_into("<I",memory[-2],264,base&0xFFFFFFFF)
        return self.program.execute(memory,"notify",(),value&0xFFFFFFFF)

    def test_signed_division_truncates_toward_zero(self):
        self.assertEqual(struct.unpack_from("<i",self.notify(-4)["memory"][-2],268)[0],0)
        self.assertEqual(struct.unpack_from("<i",self.notify(-9)["memory"][-2],268)[0],-1)

    def test_raw_signed_extremes_clamp(self):
        self.assertEqual(struct.unpack_from("<i",self.notify(-(1<<31))["memory"][-2],268)[0],-24)
        self.assertEqual(struct.unpack_from("<i",self.notify((1<<31)-1)["memory"][-2],268)[0],24)

    def test_counter_wrap_and_deferred_flag(self):
        memory=self.notify(0)["memory"][-2]
        self.assertEqual(memory[16],0);self.assertEqual(struct.unpack_from("<I",memory,276)[0],0)
        self.assertEqual(struct.unpack_from("<I",memory,272)[0],0x01000000)

    def test_table_product_uses_rounding_bias(self):
        memory=self.notify(5,1)["memory"][-2]
        expected=(0x010F2B41*0x010F2B41+0x800000)>>24
        self.assertEqual(struct.unpack_from("<I",memory,272)[0],expected)

    def test_callback_is_executed_internally(self):
        result=self.program.execute(initial(parameters=(0,0,0,0,0,25)),"request",(),INPUT,1)
        self.assertEqual(len(result["real_notifications"]),1);self.assertFalse(result["notification_calls"])
        self.assertEqual(struct.unpack_from("<i",result["memory"][-2],268)[0],5)

    def test_quantized_no_change_skips_callback(self):
        result=self.program.execute(initial(parameters=(0,0,0,0,0,2)),"request",(),INPUT,1)
        self.assertEqual(result["value"],0);self.assertFalse(result["real_notifications"])

    def test_unknown_token_retains_explicit_boundary(self):
        calls=[]
        def boundary(token,value,view):calls.append((token,value));view.mutate(STATE+264,24,4)
        result=self.program.execute(initial(parameters=(0,0,0,0,0,25),token=1),"request",(),INPUT,1,boundary=boundary)
        self.assertEqual(calls,[(1,25)]);self.assertFalse(result["real_notifications"])
        self.assertEqual(struct.unpack_from("<I",result["memory"][-2],264)[0],24)

    def test_callback_local_values_survive_source_mutation(self):
        def boundary(token,value,view):view.mutate(INPUT+10,120,2)
        result=self.program.execute(initial(parameters=(0,0,0,0,0,25),token=1),"request",(),INPUT,1,boundary=boundary)
        self.assertEqual(struct.unpack_from("<h",result["memory"][4],228)[0],25)
        self.assertEqual(struct.unpack_from("<h",result["memory"][-1],10)[0],120)

    def test_standalone_callback_has_exact_nine_instructions(self):
        self.assertEqual(sum(0x0201A9EA<=pc<0x0201AA08 for pc in self.program.code),9)

    def test_input_alias_observes_reset_before_reading(self):
        memory=initial();memory[4][28]=0;struct.pack_into("<I",memory[0],0,0x7FFFFFFF)
        result=self.program.execute(memory,"request",(),0x01C1F7D4,1)
        self.assertEqual(struct.unpack_from("<2h",result["memory"][4],218),(0,1))

    def test_invalid_domain_is_rejected(self):
        with self.assertRaises(ValueError):self.program.execute(initial(),"notify",(),-1)
        with self.assertRaises(ValueError):self.program.execute(initial(),"request",(),INPUT)


if __name__=="__main__":unittest.main()
