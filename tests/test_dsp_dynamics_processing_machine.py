"""Focused native witnesses for fixed-block dynamics and caller state contracts."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from dsp_dynamics_processing_machine import DspDynamicsProcessingProgram,REGIONS,STATES
from verify_dsp_dynamics_processing import initial,block,UNITY


def word(data,offset):return struct.unpack_from("<I",data,offset)[0]


class DynamicsProcessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=DspDynamicsProcessingProgram()
    def native(self,memory,operation,work=(),*args):return self.program.execute(memory,operation,work,*args)

    def test_reset_preserves_both_meters_and_second_bank(self):
        memory=initial();result=self.native(memory,"reset")["memory"]
        self.assertEqual(result[-1][:192],bytes(192))
        self.assertEqual(struct.unpack_from("<11I",result[-1],192),tuple([UNITY]*9+[0,0]))
        self.assertEqual(result[-1][236:],bytes(memory[-1][236:]))
        self.assertEqual(result[:-1],tuple(map(bytes,memory[:-1])))

    def test_clone_copies_exactly61_words(self):
        memory=initial();result=self.native(memory,"clone")
        self.assertEqual(result["memory"][-1][:256],bytes(memory[-1][:256]))
        self.assertEqual(result["memory"][-1][256:],bytes(memory[-1][:244]))

    def test_fast_path_delays48_and_retains48(self):
        memory=initial();result=self.native(memory,"kernel",block(range(128)),0,0xFFFFFFFF,0)
        history=struct.unpack_from("<48i",memory[-1])
        self.assertEqual(result["samples"][:128],history+tuple(range(80)))
        self.assertEqual(result["samples"][128:],tuple(range(80,128)))
        self.assertEqual(struct.unpack_from("<48i",result["memory"][-1]),tuple(range(80,128)))
        self.assertEqual(word(result["memory"][-1],236),0)
        self.assertEqual(word(result["memory"][-1],240),UNITY)

    def test_fast_path_preserves_raw_gain_slots(self):
        memory=initial();struct.pack_into("<9I",memory[-1],192,*range(9))
        result=self.native(memory,"kernel",block([0]*128),0,0,0)
        self.assertEqual(result["memory"][-1][192:228],bytes(memory[-1][192:228]))
        self.assertNotIn(0x01C1A798,result["visited"])

    def test_int_min_peak_uses_unsigned_magnitude(self):
        result=self.native(initial(),"kernel",block([-0x80000000]*128),0,0x7FFFFFFF,0)
        self.assertIn(0x01C1AA3A,result["visited"])
        result=self.native(initial(),"kernel",block([-0x80000000]*128),0,0x80000000,0)
        self.assertNotIn(0x01C1A798,result["visited"])

    def test_gain_is_used_before_increment_and_minimum_release_is_one(self):
        memory=initial();struct.pack_into("<48i",memory[-1],0,*([UNITY]*48))
        struct.pack_into("<I",memory[-1],224,UNITY//2);struct.pack_into("<I",memory[-1],232,1)
        result=self.native(memory,"kernel",block([UNITY]*128),0,0xFFFFFFFF,0)
        self.assertEqual(result["samples"][:16],(UNITY//2,)*16)
        self.assertEqual(result["samples"][16:32],(UNITY//2+1,)*16)
        self.assertEqual(word(result["memory"][-1],224),UNITY//2+8)
        self.assertEqual(word(result["memory"][-1],236),128)
        self.assertEqual(word(result["memory"][-1],240),UNITY//2)

    def test_negative_products_shift_down(self):
        memory=initial();struct.pack_into("<48i",memory[-1],0,*([-1]*48))
        struct.pack_into("<I",memory[-1],224,UNITY//2);struct.pack_into("<I",memory[-1],232,1)
        result=self.native(memory,"kernel",block([0]*128),0,0,0)
        self.assertEqual(result["samples"][:16],(-1,)*16)

    def test_skip_condition_is_bitwise_and(self):
        memory=initial();struct.pack_into("<8I",memory[-1],192,*([UNITY|4]*8))
        struct.pack_into("<I",memory[-1],224,UNITY|8);struct.pack_into("<I",memory[-1],232,1)
        result=self.native(memory,"kernel",block([0]*128),0,0xFFFFFFFF,0)
        self.assertEqual(result["samples"][:16],struct.unpack_from("<16i",memory[-1]))
        self.assertIn(0x01C1AA2A,result["visited"])

    def test_raw_gain_product_wraps_without_clipping(self):
        memory=initial();struct.pack_into("<48i",memory[-1],0,*([0x7FFFFFFF]*48))
        struct.pack_into("<9I",memory[-1],192,*([0x7FFFFFFF]*9));struct.pack_into("<I",memory[-1],232,1)
        result=self.native(memory,"kernel",block([0]*128),0,0xFFFFFFFF,0)
        self.assertEqual(result["samples"][0],-256)

    def test_counter_wraps_on_fast_and_slow_paths(self):
        for active in (0,1):
            memory=initial();struct.pack_into("<2I",memory[-1],228,0xFFFFFFFC,active)
            result=self.native(memory,"kernel",block([0]*128),0,0,0)
            self.assertEqual(word(result["memory"][-1],228),4)

    def test_scale_cache_reuses_existing_threshold(self):
        memory=initial();struct.pack_into("<3I",memory[4],108,256,0,0xFFFFFFFF)
        result=self.native(memory,"single",block([0x7FFFFFFF]*128),256)
        self.assertEqual(word(result["memory"][4],116),0xFFFFFFFF)
        self.assertEqual(word(result["memory"][4],112),0)

    def test_zero_scale_uses_original_divide_zero_result(self):
        memory=initial();struct.pack_into("<I",memory[4],108,1)
        result=self.native(memory,"single",block([1]*128),0)
        self.assertEqual(word(result["memory"][4],116),0)

    def test_threshold_overflow_check_uses_low_quotient_word(self):
        memory=initial();struct.pack_into("<I",memory[0],52,0x10000)
        result=self.native(memory,"single",block([0]*128),1)
        self.assertEqual(word(result["memory"][4],116),0)
        struct.pack_into("<I",memory[0],52,0x100)
        result=self.native(memory,"single",block([0]*128),1)
        self.assertEqual(word(result["memory"][4],116),0x07FFFFF8)

    def test_dual_first_bank_only_runs_on_scale_change(self):
        for cached,calls in ((256,1),(255,2)):
            memory=initial();struct.pack_into("<I",memory[4],108,cached)
            result=self.native(memory,"dual",block([0]*128),256)
            actual=[args[0] for pc,args in result["processing_calls"] if pc==REGIONS["kernel"][0]]
            self.assertEqual(actual,([STATES] if calls==2 else [])+[STATES+256])

    def test_second_bank_does_not_update_shared_meters(self):
        memory=initial();struct.pack_into("<3I",memory[4],108,256,123,0)
        struct.pack_into("<I",memory[0],60,456)
        result=self.native(memory,"dual",block([0x7FFFFFFF]*128),256)
        self.assertNotEqual(word(result["memory"][-1],256+236),0)
        self.assertEqual(word(result["memory"][4],112),123)
        self.assertEqual(word(result["memory"][0],60),456)

    def test_meter_optional_reset(self):
        memory=initial();struct.pack_into("<I",memory[0],60,123)
        unchanged=self.native(memory,"meter",(),1)
        self.assertEqual(word(unchanged["memory"][0],60),123)
        changed=self.native(memory,"meter",(),2)
        self.assertEqual(changed["outputs"][1],123)
        self.assertEqual(word(changed["memory"][0],60),UNITY)
        self.assertEqual(changed["value"],48)


if __name__=="__main__":unittest.main()
