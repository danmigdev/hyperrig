"""Independent expected spans and ordering in the original capture reset body."""
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
AVAILABLE=(ROOT/"analysis/firmware/m571_g_app/app.bin").is_file() and (ROOT/"upstream/pi32v2-isa/pi32v2isa").is_dir()


@unittest.skipUnless(AVAILABLE,"bootstrap and analyze the pinned firmware first")
class CaptureResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/"tools"))
        from capture_reset_machine import CaptureResetProgram
        from verify_capture_reset import baseline,put,Script,ParserScript
        cls.program=CaptureResetProgram()
        cls.initial,cls.put=staticmethod(baseline),staticmethod(put)
        cls.Script,cls.ParserScript=Script,ParserScript

    def execute(self,memory=None,operation="reset",*args,parses=None):
        return self.program.execute(memory or self.initial(),operation,*args,
            boundary=self.Script(),parser=self.ParserScript(parses))

    def test_zero_channels_clear_only_context_cursor(self):
        memory=self.initial(channels=0,auxiliary=True)
        result=self.execute(memory)
        self.assertEqual(result["clears"],[])
        self.assertEqual(result["memory"][26:],memory[26:])
        expected=bytearray(memory[22]);expected[164:168]=bytes(4)
        self.assertEqual(result["memory"][22],expected)

    def test_zero_layers_do_not_read_descriptors(self):
        from capture_reset_machine import ARENA
        memory=self.initial(0,1)
        self.put(memory[22],168,0xDEAD0000)
        result=self.execute(memory)
        self.assertEqual([a for a,_ in result["clears"]],[ARENA+0x4000,ARENA+0x4004])

    def test_layer_ring_preserves_both_neighbors(self):
        memory=self.initial(1,1,0,0xFFFFFFFF)
        result=self.execute(memory)
        before,after=memory[27],result["memory"][27]
        self.assertEqual(after[:0x1000],before[:0x1000])
        self.assertEqual(after[0x1000:0x1100],bytes(256))
        self.assertEqual(after[0x1100:],before[0x1100:])

    def test_three_channels_multiply_each_ring_size(self):
        result=self.execute(self.initial(2,3,1,0xFFFFFFFF))
        self.assertEqual(len(result["clears"]),2*65*3)

    def test_layer_unsigned_size_wrap_can_skip_pointer(self):
        memory=self.initial(1,3,0xFFFFFFC0,0xFFFFFFFF)
        self.put(memory[26],68,0xDEAD0000)
        self.assertEqual(self.execute(memory)["clears"],[])

    def test_layer_multiplication_wrap_can_skip_pointer(self):
        memory=self.initial(1,4,0x3FFFFFC0,0xFFFFFFFF)
        self.put(memory[26],68,0xDEAD0000)
        self.assertEqual(self.execute(memory)["clears"],[])

    def test_maximum_channel_byte_preserves_wrapping_product(self):
        self.assertEqual(len(self.execute(self.initial(1,255,0xFEFEFEBF,0xFFFFFFFF))["clears"]),1)

    def test_main_padding_saturates_at_sixty_four(self):
        for span,words in ((62,126),(63,128),(64,129),(0xFFFFFFFF,0),(0xFFFFFFBF,0)):
            self.assertEqual(len(self.execute(self.initial(0,1,span=span))["clears"]),words)

    def test_auxiliary_requires_three_channels_and_nonzero_table(self):
        for channels,enabled in ((1,True),(2,True),(3,False)):
            self.assertEqual(self.execute(self.initial(0,channels,span=0xFFFFFFFF,auxiliary=enabled))["clears"],[])

    def test_zero_layers_still_clear_final_auxiliary_ring(self):
        result=self.execute(self.initial(0,3,span=0xFFFFFFFF,auxiliary=True,final_length=1))
        self.assertEqual(len(result["clears"]),195)

    def test_auxiliary_size_wrap_zero_does_not_read_ring_pointer(self):
        memory=self.initial(1,3,0xFFFFFFC0,0xFFFFFFFF,True,0xFFFFFFC0,0xFFFFFFC0)
        self.put(memory[27],0x200,0xDEAD0000)
        self.assertEqual(self.execute(memory)["clears"],[])

    def test_layer_length_is_reread_after_overlapping_store(self):
        from capture_dispatch_machine import LAYERS
        memory=self.initial(1,1,0xFFFFFFFF,0xFFFFFFFF)
        self.put(memory[26],68,LAYERS+76)
        result=self.execute(memory)
        self.assertEqual(len(result["clears"]),64)
        self.assertEqual(result["clears"][0],(LAYERS+76,0xFFFFFFFF))

    def test_word_address_wrap_is_uint32(self):
        from capture_reset_machine import WRAP
        memory=self.initial(1,1,0xFFFFFFC2,0xFFFFFFFF)
        self.put(memory[26],68,WRAP)
        self.assertEqual([a for a,_ in self.execute(memory)["clears"]],[WRAP,0])

    def test_outer_load_executes_two_resets(self):
        from capture_dispatch_machine import ARENA
        result=self.execute(self.initial(),"load",ARENA,512,1,2)
        self.assertEqual(result["reset_entries"],2)
        middle=len(result["clears"])//2
        self.assertEqual([a for a,_ in result["clears"][:middle]],[a for a,_ in result["clears"][middle:]])
        self.assertTrue(all(value==0 for _,value in result["clears"][middle:]))

    def test_context_load_executes_one_reset(self):
        from capture_dispatch_machine import ARENA
        self.assertEqual(self.execute(self.initial(),"load_context",ARENA,512,1,2)["reset_entries"],1)

    def test_parser_failure_never_enters_reset(self):
        from capture_dispatch_machine import ARENA
        result=self.execute(self.initial(),"load",ARENA,512,1,2,parses={0:(-17,(None,64,None),())})
        self.assertEqual(result["reset_entries"],0)
        self.assertEqual(result["result"],(-17)&0xFFFFFFFF)

    def test_unsupported_calls_are_rejected(self):
        for operation,args in (("reset",(1,)),("probe",()),("load",(-1,512,1,2))):
            with self.assertRaisesRegex(ValueError,"call domain"):
                self.program.execute(self.initial(),operation,*args)


if __name__=="__main__":unittest.main()
