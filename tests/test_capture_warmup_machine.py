"""Focused original warm-up control flow, storage and dependency checks."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from capture_warmup_machine import CaptureWarmupProgram,CaptureWarmupMachine,ARENA,SCRATCH,WRAP
from verify_capture_warmup import baseline,put,WORK,OUTPUT,HEAD_RING


class CaptureWarmupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=CaptureWarmupProgram()

    def test_complete_body_count(self):self.assertEqual(len(self.program.warmup_code),118)

    def test_parallel_stack_argument_reads_old_value(self):
        m=CaptureWarmupMachine(self.program,baseline(),0,None)
        m.pc=0x01C12FB6;m.regs.update(r0=74,r11=WORK)
        m.step()
        self.assertEqual(m.read(m.value("sp")+12,4),74)
        self.assertEqual(m.value("r0"),WORK+16)

    def test_warmed_status_and_position(self):
        r=self.program.execute(baseline(position=0xFFFFFFFF),OUTPUT)
        self.assertEqual(r["result"],1);self.assertEqual(r["reset_entries"],0)
        self.assertEqual(r["memory"][0][88:92],bytes(4))

    def test_optional_output_is_accumulated_triplet(self):
        r=self.program.execute(baseline(),OUTPUT)
        self.assertEqual(r["memory"][1][OUTPUT-ARENA:OUTPUT-ARENA+12],r["memory"][2][WORK-SCRATCH+16:WORK-SCRATCH+28])

    def test_no_output_preserves_output_buffer(self):
        memory=baseline();r=self.program.execute(memory)
        self.assertEqual(r["memory"][1][OUTPUT-ARENA:OUTPUT-ARENA+12],memory[1][OUTPUT-ARENA:OUTPUT-ARENA+12])

    def test_output_alias_uses_sequential_loads(self):
        r=self.program.execute(baseline(),WORK+20)
        offset=WORK-SCRATCH+16
        self.assertEqual(r["memory"][2][offset:offset+16],r["memory"][2][offset:offset+4]*4)

    def test_first_history_is_cleared(self):
        r=self.program.execute(baseline(layers=3))
        self.assertEqual(r["memory"][1][0x1000:0x1000+(74+64)*12],bytes((74+64)*12))

    def test_following_histories_repeat_first_triplet(self):
        r=self.program.execute(baseline(layers=3))
        for offset in (0x3000,0x5000):
            data=r["memory"][1][offset:offset+(74+64)*12]
            self.assertEqual(data,data[:12]*(74+64))

    def test_small_head_uses_only_matching_mirror_extent(self):
        memory=baseline();put(memory[0],84,2)
        r=self.program.execute(memory)
        offset=HEAD_RING-ARENA;data=r["memory"][1][offset:offset+72]
        self.assertEqual(data,data[:12]*6)
        self.assertEqual(r["memory"][1][offset+72:offset+84],memory[1][offset+72:offset+84])

    def test_wrapped_empty_head_extent(self):
        for span in (0xFFFFFFFF,0xFFFFFFBF):
            memory=baseline();put(memory[0],84,span);r=self.program.execute(memory)
            self.assertEqual(r["memory"][1][HEAD_RING-ARENA:HEAD_RING-ARENA+2304],memory[1][HEAD_RING-ARENA:HEAD_RING-ARENA+2304])

    def test_wrapped_first_clear_zero_count(self):
        memory=baseline(layers=1,taps=1);put(memory[1],76,0xFFFFFFC0)
        r=self.program.execute(memory)
        self.assertEqual(r["memory"][1][0x1000:0x1100],memory[1][0x1000:0x1100])

    def test_first_history_address_wrap(self):
        memory=baseline(layers=1,taps=1);put(memory[1],76,0xFFFFFFC2);put(memory[1],68,WRAP)
        r=self.program.execute(memory)
        self.assertEqual(r["memory"][4],bytes(16));self.assertEqual(r["memory"][3][:8],bytes(8))

    def test_flag_zero_executes_reset(self):
        memory=baseline();memory[0][164]=0;r=self.program.execute(memory,OUTPUT)
        self.assertEqual((r["result"],r["reset_entries"]),(0,1));self.assertFalse(r["calls"])
        self.assertEqual(r["memory"][1][OUTPUT-ARENA:OUTPUT-ARENA+12],memory[1][OUTPUT-ARENA:OUTPUT-ARENA+12])

    def test_any_nonzero_flag_is_eligible(self):
        memory=baseline();memory[0][164]=255
        self.assertEqual(self.program.execute(memory)["result"],1)

    def test_only_three_channels_and_32_bits_are_eligible(self):
        for channels,bits in ((0,32),(1,32),(2,32),(4,32),(3,0),(3,16),(3,64)):
            memory=baseline();memory[0][2]=channels;memory[0][1]=bits
            self.assertEqual(self.program.execute(memory)["result"],0)

    def test_zero_tokens_use_mapped_reset_objects(self):
        for field in ("table","ring"):
            memory=baseline()
            put(memory[0] if field=="table" else memory[1],92 if field=="table" else 68,0)
            self.assertEqual(self.program.execute(memory)["result"],0)

    def test_invalid_model_shape(self):
        with self.assertRaises(ValueError):self.program.execute(baseline()[:3])
        with self.assertRaises(ValueError):self.program.execute(baseline(),-1)


if __name__=="__main__":unittest.main()
