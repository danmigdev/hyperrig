"""Focused instruction-model and runtime behavior checks."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from capture_processing_machine import (CaptureProcessingProgram,CaptureProcessingMachine,
    TABLE_START,TABLE_END,SCRATCH,ARENA,CONTEXT)
from verify_capture_processing import baseline,put,INPUT,OUTPUT,DRY,SUM


class CaptureProcessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=CaptureProcessingProgram()

    def test_dispatch_table_is_data(self):
        self.assertEqual(self.program.table,bytes((2,26,14,20)))
        self.assertFalse(any(pc in self.program.code for pc in range(TABLE_START,TABLE_END)))

    def test_new_instruction_count(self):self.assertEqual(len(self.program.new_code),465)

    def test_parallel_store_reads_old_register(self):
        m=CaptureProcessingMachine(self.program,baseline(),"process",(INPUT,OUTPUT,64),None)
        m.pc=0x01C12DFE;m.regs.update(r0=64,r1=0x01C33F40,r2=5)
        m.step()
        self.assertEqual(m.read(0x01C33F60,4),64)
        self.assertEqual(m.value("r0"),15)

    def test_reject_packet_second_entry(self):
        m=CaptureProcessingMachine(self.program,baseline(),"process",(INPUT,OUTPUT,64),None)
        m.pc=0x01C12E02
        with self.assertRaises(ValueError):m.step()

    def test_reject_api_shape(self):
        with self.assertRaises(ValueError):self.program.execute(baseline(),"process",INPUT)
        with self.assertRaises(ValueError):self.program.execute(baseline(),"process",INPUT,OUTPUT,-1)

    def test_zero_rounds_word_count_down(self):
        before=baseline();r=self.program.execute(before,"zero",SUM,7)
        offset=SUM-ARENA
        self.assertEqual(r["memory"][1][offset:offset+16],bytes(16))
        self.assertEqual(r["memory"][1][offset+16:offset+28],before[1][offset+16:offset+28])

    def test_zero_rep_zero_is_excluded(self):
        with self.assertRaises(ValueError):self.program.execute(baseline(),"zero",SUM,3)

    def test_bypass_forward_overlap(self):
        memory=baseline(layers=0)
        first=bytes(memory[1][INPUT-ARENA:INPUT-ARENA+4])
        r=self.program.execute(memory,"process",INPUT,INPUT+4,9)
        self.assertEqual(r["memory"][1][INPUT-ARENA:INPUT-ARENA+40],first*10)
        self.assertFalse(r["calls"])

    def test_bypass_counter_wrap_even_without_samples(self):
        memory=baseline(layers=0);put(memory[2],0x01C344B0-SCRATCH,0xFFFFFFFF)
        r=self.program.execute(memory,"process",INPUT,OUTPUT,0)
        self.assertEqual(r["memory"][2][0xAB0:0xAB4],bytes(4))

    def test_loaded_partial_block_is_untouched(self):
        memory=baseline();r=self.program.execute(memory,"process",INPUT,OUTPUT,63)
        self.assertEqual(r["memory"],tuple(map(bytes,memory)))

    def test_empty_iteration_is_untouched(self):
        for first,end in ((2,3),(1,1),(3,2)):
            memory=baseline();r=self.program.execute(memory,"iterate",first,end,DRY,0,SUM,0)
            self.assertEqual(r["memory"],tuple(map(bytes,memory)))

    def test_selector_uses_low_bit(self):
        r=self.program.execute(baseline(),"layer",1,DRY,0,64,SUM,ARENA+0x5000,64,0xFFFFFFFF,kernel=lambda *_:None)
        self.assertEqual(r["calls"][0][1],0x01C33D38+200)

    def test_dispatch_all_kinds(self):
        expected=(0x01C14282,0x01C1318E,0x01C1349C,0x01C13822,0x01C13D16,0x01C14282)
        for kind,target in enumerate(expected):
            r=self.program.execute(baseline(kind=kind),"layer",1,DRY,0,64,SUM,ARENA+0x5000,64,0,kernel=lambda *_:None)
            self.assertEqual(r["calls"][0][0],target)

    def test_first_layer_truncated_zero_span(self):
        memory=baseline();r=self.program.execute(memory,"layer",0,DRY,0,2,SUM,ARENA+0x5000,64,0,kernel=lambda *_:None)
        offset=SUM-ARENA
        self.assertEqual(r["memory"][1][offset:offset+16],bytes(16))
        self.assertEqual(r["memory"][1][offset+16:offset+24],memory[1][offset+16:offset+24])

    def test_last_layer_one_frame_mirror(self):
        memory=baseline(layers=1);r=self.program.execute(memory,"iterate",0,1,DRY,67,SUM,0)
        offset=0x01C33F10-SCRATCH
        self.assertEqual(r["memory"][2][offset:offset+12],r["memory"][2][offset+12:offset+24])
        self.assertEqual(r["memory"][2][offset+24:offset+32],memory[2][offset+24:offset+32])

    def test_unmapped_descriptor_is_rejected(self):
        memory=baseline();put(memory[0],92,0xDEAD0000)
        with self.assertRaises(ValueError):self.program.execute(memory,"process",INPUT,OUTPUT,64)

    def test_position_wrap_and_remainder(self):
        memory=baseline(layers=1,position=0xFFFFFFE0)
        r=self.program.execute(memory,"process",INPUT,OUTPUT,65)
        self.assertEqual(int.from_bytes(r["memory"][0][88:92],"little"),32)
        offset=OUTPUT-ARENA+256
        self.assertEqual(r["memory"][1][offset:offset+4],memory[1][offset:offset+4])


if __name__=="__main__":unittest.main()
