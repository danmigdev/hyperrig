"""Focused original-instruction witnesses for startup input and sample state."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from dsp_audio_path_machine import DspAudioPathProgram, REGIONS
from verify_dsp_audio_path import baseline


class AudioPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.program=DspAudioPathProgram()

    def run_native(self,state,operation,samples=(),*args):
        return self.program.execute(state,operation,samples,*args)

    def test_cached_reuses_word_when_source_matches(self):
        state=baseline();struct.pack_into("<2I",state[8],0,600,0xFFFFFFFF)
        result=self.run_native(state,"cached")
        self.assertEqual(result["value"],0xFFFFFFFF)
        self.assertEqual(result["memory"],tuple(map(bytes,state)))

    def test_cached_source_and_result_update(self):
        state=baseline();result=self.run_native(state,"cached")
        self.assertEqual(struct.unpack("<2I",result["memory"][8]),(600,258251))
        self.assertEqual(result["value"],258251)

    def test_input_parallel_load_uses_platform_pointer(self):
        state=baseline();struct.pack_into("<2I",state[8],0,600,1000)
        struct.pack_into("<I",state[7],8,999)
        self.assertEqual(self.run_native(state,"input")["value"],1)
        struct.pack_into("<I",state[7],8,1000)
        self.assertEqual(self.run_native(state,"input")["value"],0)

    def test_input_second_subtraction_boundary(self):
        state=baseline();struct.pack_into("<I",state[7],8,0)
        for base,expected in ((154950,154950),(154951,154951),(154952,154951)):
            struct.pack_into("<2I",state[8],0,600,base)
            self.assertEqual(self.run_native(state,"input")["value"],expected)

    def test_startup_has_no_scripted_services(self):
        result=self.run_native(baseline(),"startup")
        self.assertFalse(result["boundary_calls"])
        self.assertEqual(len(result["dynamics_calls"]),1)
        self.assertEqual(len(result["production_calls"]),4)
        self.assertEqual(struct.unpack_from("<I",result["memory"][0],36)[0],48077)
        self.assertEqual(struct.unpack_from("<I",result["memory"][4],48)[0],206101)
        self.assertEqual(result["memory"][1][0],1)

    def test_guard_skips_invalid_stored_parameters(self):
        state=baseline();state[1][0]=255
        struct.pack_into("<h",state[4],218,-32768)
        result=self.run_native(state,"startup")
        self.assertEqual(result["memory"],tuple(map(bytes,state)))
        self.assertFalse(result["audio_calls"])

    def test_update_ors_enable_without_resetting_histories(self):
        state=baseline()
        for i in range(4): state[5][44*i+40]=1;state[9][168+i]=2
        result=self.run_native(state,"update")
        self.assertEqual(result["memory"][10],bytes(state[9]))
        self.assertEqual(result["memory"][4][1],0)
        for i in range(4):
            self.assertEqual(result["memory"][5][44*i+40],3)
            self.assertEqual(result["memory"][5][44*i:44*i+40],bytes(state[5][44*i:44*i+40]))
            self.assertEqual(result["memory"][5][44*i+41:44*i+44],bytes(state[5][44*i+41:44*i+44]))

    def test_bypass_one_sample_preserves_previous_x1(self):
        result=self.run_native(baseline(),"block",(123,),65536)
        for i in range(4):
            self.assertEqual(struct.unpack_from("<4iI",result["memory"][5],44*i+20),(123,300+i,123,300+i,0))
        self.assertEqual(result["samples"],(123,))

    def test_bypass_many_samples_tracks_last_two(self):
        result=self.run_native(baseline(),"block",(7,-9,11),65536)
        for i in range(4):
            self.assertEqual(struct.unpack_from("<4iI",result["memory"][5],44*i+20),(11,-9,11,-9,0))

    def test_both_kernels_execute_after_startup(self):
        state=tuple(bytearray(x) for x in self.run_native(baseline(parameters=(0,20,0,-20,0)),"startup")["memory"])
        for i in range(4): state[5][44*i+40]=1;state[5][44*i+41]=i&1
        result=self.run_native(state,"process",(123,-456,789))
        self.assertEqual([call[0] for call in result["kernel_calls"]],["rounded","residual","rounded","residual"])

    def test_ramp_increments_before_multiplication(self):
        self.assertEqual(self.run_native(baseline(),"ramp",(65536,65536,65536),0,1)["samples"],(1,2,3))

    def test_ramp_arithmetic_shift_and_native_saturation(self):
        self.assertEqual(self.run_native(baseline(),"ramp",(-1,1),32768,0)["samples"],(-1,0))
        self.assertEqual(self.run_native(baseline(),"ramp",(-2147483648,2147483647),65536,0)["samples"],(-2147483648,2147483647))
        self.assertEqual(self.run_native(baseline(),"ramp",(-2147483648,2147483647),131072,0)["samples"],(-2147483647,2147483647))

    def test_ramp_wraps_gain_word(self):
        self.assertEqual(self.run_native(baseline(),"ramp",(65536,65536,65536),0xFFFFFFFE,1)["samples"],(-1,0,1))

    def test_zero_and_disabled_process_preserve_pending(self):
        for frames,gate in ((0,1),(3,0),(3,2)):
            state=baseline();state[4][1]=255;state[4][28]=gate
            samples=(31,)*frames;result=self.run_native(state,"process",samples)
            self.assertEqual(result["memory"],tuple(map(bytes,state)))
            self.assertEqual(result["samples"],samples)

    def test_transition_counts_chunks_and_then_holds(self):
        state=baseline();state[4][1]=1
        for i in range(4):
            struct.pack_into("<5i",state[9],i*20,1<<28,0,0,0,0)
            struct.pack_into("<5i",state[9],80+i*20,0,0,0,0,0)
            state[9][168+i]=0
        struct.pack_into("<2I",state[9],160,131072,32768)
        struct.pack_into("<I",state[9],172,2)
        result=self.run_native(state,"process",(65536,)*65)
        self.assertEqual(struct.unpack_from("<I",result["memory"][4],32)[0],0)
        self.assertEqual(result["samples"][0],66560)
        self.assertEqual(result["samples"][31],98304)
        self.assertEqual(result["samples"][63:],(131072,131072))
        blocks=[args[1] for target,args in result["audio_calls"] if target==REGIONS["block"][0]]
        self.assertEqual(blocks,[32,32,1])

    def test_final_transition_copies_exact_coefficient_words(self):
        state=baseline();state[4][1]=1;struct.pack_into("<I",state[9],172,1)
        result=self.run_native(state,"process",(0,))
        for i in range(4):
            self.assertEqual(result["memory"][5][44*i:44*i+20],bytes(state[9][20*i:20*i+20]))
            self.assertEqual(result["memory"][5][44*i+40],state[9][168+i])

    def test_invalid_model_domain_rejected(self):
        state=baseline()
        for operation,samples,args in (("block",(),(65536,)),("ramp",(0,)*129,(0,0)),
            ("process",(1<<31,),()),("ramp",(),(-1,0))):
            with self.assertRaises(ValueError): self.run_native(state,operation,samples,*args)
        struct.pack_into("<h",state[4],218,1281)
        with self.assertRaises(ValueError): self.run_native(state,"startup")


if __name__=="__main__": unittest.main()
