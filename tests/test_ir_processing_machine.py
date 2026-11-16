"""Independent fixed-point, ring, gain and synthetic-register expectations."""
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
AVAILABLE=(ROOT/'analysis/firmware/m571_g_app/app.bin').is_file() and (ROOT/'upstream/pi32v2-isa/pi32v2isa').is_dir()

@unittest.skipUnless(AVAILABLE,'bootstrap and analyze the pinned firmware first')
class IrProcessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'tools'))
        from ir_processing_machine import IrProcessingProgram,OBJECT,CONSTRUCTION_REGIONS
        from verify_ir_processing import baseline,put,words,put_permutation,Trace
        cls.program=IrProcessingProgram();cls.initial=staticmethod(baseline)
        cls.put,cls.words,cls.permutation=map(staticmethod,(put,words,put_permutation));cls.Trace=Trace
        memory=baseline();put(memory[25],0,*([0]*129));put(memory[26],0,129,0,1)
        cls.zero=cls.program.execute(memory,'construct',129,CONSTRUCTION_REGIONS['copy'][0],OBJECT)['memory']

    def execute(self,operation,*args,memory=None,trace=None):
        return self.program.execute(memory if memory is not None else self.initial(),operation,*args,mmio=trace or self.Trace())
    def mutable(self,memory):return tuple(bytearray(x) if i!=2 else x for i,x in enumerate(memory))

    def test_integer_fft_impulse_has_quarter_scale_unit_bins(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,4,*([0]*127));self.put(memory[25],0,*([0]*120))
        result=self.execute('fft64',WORK,COPY,memory=memory)
        self.assertEqual(self.words(result['memory'][24],0,128),(1,0)*64)
    def test_skip_flag_uses_the_precomputed_first_radix_stage(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,*((4,0)*4),*([0]*120));self.put(memory[25],0,*([0]*120))
        result=self.execute('fft64',WORK,COPY|1,memory=memory)
        self.assertEqual(self.words(result['memory'][24],0,128),(1,0)*64)
    def test_input_uses_symmetric_25_bit_history_limits(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,*((0x7FFFFFFF,0x80000000)*64));self.permutation(memory[25])
        result=self.execute('input',WORK,WORK+512,WORK+1024,COPY,memory=memory)
        self.assertEqual(self.words(result['memory'][24],512,128),(0x1FFFFFF,0xFE000001)*64)
    def test_two_partition_complex_product_uses_cyclic_history(self):
        from ir_processing_machine import OBJECT,WORK,COPY
        memory=self.initial();self.put(memory[23],0,*((2,3,5,7)*129));self.put(memory[25],0,*((11,13,17,19)*129))
        for current,real,imag in ((0,-65,273),(1,-59,231)):
            result=self.execute('multiply',OBJECT,COPY,2|(current<<16),WORK,memory=memory)
            self.assertEqual(result['result'],0)
            self.assertEqual(struct.unpack_from('<'+'q'*258,result['memory'][24]),(real,imag)*129)
    def test_complex_accumulator_wraps_modulo_64_bits(self):
        from ir_processing_machine import OBJECT,WORK,COPY
        memory=self.initial();self.put(memory[23],0,*([0x80000000]*516));self.put(memory[25],0,*([0x80000000]*516))
        result=self.execute('multiply',OBJECT,COPY,2,WORK,memory=memory)
        self.assertEqual(result['memory'][24][:2064],bytes(2064));self.assertEqual(result['result'],0)
    def test_mac_prefetch_padding_is_read_but_does_not_change_the_sum(self):
        from ir_processing_machine import OBJECT,WORK,COPY
        memory=self.initial();self.put(memory[23],0,*([0]*258));self.put(memory[25],0,*([0]*258))
        self.put(memory[23],1032,0xDEADBEEF,0xFFFFFFFF);self.put(memory[25],1032,0x80000000,0x7FFFFFFF)
        result=self.execute('multiply',OBJECT,COPY,1,WORK,memory=memory)
        self.assertEqual(result['memory'][24][:2064],bytes(2064))
    def test_output_saturates_to_minus_int_max(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,*((0x80000000,0x7FFFFFFF)*64))
        result=self.execute('hardware_output',WORK,COPY,0,memory=memory)
        self.assertEqual(self.words(result['memory'][25],0,128),(0x80000001,0x7FFFFFFF)*64)
    def test_output_shift_clamps_before_left_shift(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,*((2,0xFFFFFFFE)*64))
        result=self.execute('hardware_output',WORK,COPY,30,memory=memory)
        self.assertEqual(self.words(result['memory'][25],0,128),(0x40000000,0xC0000000)*64)
    def test_negative_output_shift_preserves_the_arithmetic_sign(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,*((0x80000000,0x7FFFFFFF)*64))
        result=self.execute('hardware_output',WORK,COPY,(-31)&0xFFFFFFFF,memory=memory)
        self.assertEqual(self.words(result['memory'][25],0,128),(0xFFFFFFFF,0)*64)
    def test_q15_mix_clamps_exact_negative_endpoint(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],0,*([0x80000000]*128))
        result=self.execute('mix',WORK,COPY,0,32768,memory=memory)
        self.assertEqual(self.words(result['memory'][25],0,128),(0x80000001,)*128)
    def test_crossfade_reaches_the_new_gain_on_sample_128(self):
        from ir_processing_machine import WORK,COPY,OBJECT
        memory=self.initial();self.put(memory[24],0,*([32768]*128));self.put(memory[25],0,*([0]*128))
        result=self.execute('crossfade',OBJECT,WORK,COPY,0,0,32768,0,memory=memory)
        self.assertEqual(self.words(result['memory'][23],0,128),tuple(256*i for i in range(1,129)))
    def test_negative_crossfade_slope_divides_toward_zero(self):
        from ir_processing_machine import WORK,COPY,OBJECT
        memory=self.initial();self.put(memory[24],0,*([32768]*128));self.put(memory[25],0,*([0]*128))
        result=self.execute('crossfade',OBJECT,WORK,COPY,127,0,0,0,memory=memory)
        expected=tuple(127-int(127*i/128) for i in range(1,129))
        self.assertEqual(self.words(result['memory'][23],0,128),expected)
    def test_hardware_input_rounds_half_up_and_copies_previous_half(self):
        from ir_processing_machine import WORK,COPY
        memory=self.initial();self.put(memory[24],512,*range(128))
        self.put(memory[25],0,*((256,0xFFFFFF00,0xFFFFFEFF,0x7FFFFFFF)*32))
        result=self.execute('hardware_input',WORK,COPY,memory=memory)
        self.assertEqual(self.words(result['memory'][24],0,128),tuple(range(128)))
        self.assertEqual(self.words(result['memory'][24],512,128),(1,0,0xFFFFFFFF,0x3FFFF)*32)
    def test_accumulator_rounding_ties_go_toward_positive_infinity(self):
        from ir_processing_machine import WORK
        memory=self.initial();struct.pack_into('<'+'q'*258,memory[24],0,*((3,-3,1,-1)*64+(3,-3)))
        result=self.execute('hardware_scale',WORK,1,memory=memory)
        self.assertEqual(self.words(result['memory'][24],0,258),(2,0xFFFFFFFF,1,0)*64+(2,0xFFFFFFFF))
    def test_zero_ir_produces_silence_and_advances_both_history_indices(self):
        from ir_processing_machine import OBJECT
        memory=self.mutable(self.zero);self.put(memory[29],0,*range(128))
        first=self.execute('process',OBJECT,128,0x3F800000,0,memory=memory)['memory']
        second=self.execute('process',OBJECT,128,0x3F800000,0,memory=first)['memory']
        self.assertEqual(first[29],bytes(512));self.assertEqual(second[29],bytes(512))
        self.assertEqual(self.words(first[23],8,2),(1,1));self.assertEqual(self.words(second[23],8,2),(0,0))
    def test_zero_ir_with_unity_dry_gain_preserves_safe_input_words(self):
        from ir_processing_machine import OBJECT
        memory=self.mutable(self.zero);self.put(memory[29],0,*range(128))
        result=self.execute('process',OBJECT,128,0,0x3F800000,memory=memory)
        self.assertEqual(result['memory'][29],memory[29])
    def test_noop_entries_preserve_all_state(self):
        from ir_processing_machine import OBJECT
        for token,count,active in ((0,128,1),(OBJECT,127,1),(OBJECT,128,0)):
            memory=self.initial();self.put(memory[23],0,active)
            self.assertEqual(self.execute('process',token,count,0,0,memory=memory)['memory'],tuple(memory))
    def test_supported_accelerator_descriptors_and_order(self):
        from ir_processing_machine import MMIO,DESCRIPTOR,WRITE,SYNC
        commands={256:(0x31000732,0x31000706),512:(0x32000832,0x42000806),
                  1024:(0x34000942,0x34000906),2048:(0x38000A42,0x48000A06)}
        for size,pair in commands.items():
            for reverse,command in enumerate(pair):
                trace=self.Trace();result=self.execute('start',size,reverse,123,456,trace=trace)
                self.assertEqual(result['result'],0);self.assertEqual(self.words(result['memory'][28],0,4),(command,123,456,0))
                self.assertEqual([event[:3] for event in trace.prefix],[(SYNC,0,0),(WRITE,MMIO,0),(WRITE,MMIO+4,DESCRIPTOR),(WRITE,MMIO,257)])
                self.assertEqual(self.words(result['memory'][27],0,4),(0,1,0,1))
    def test_unsupported_transform_sizes_have_no_register_effects(self):
        for size in (0,1,255,257,768,1280,1536,1792,4096,0xFFFFFFFF):
            trace=self.Trace();memory=self.initial();result=self.execute('start',size,0,0,0,memory=memory,trace=trace)
            self.assertEqual(result['result'],0xFFFFFFFF);self.assertEqual(result['memory'],tuple(memory));self.assertEqual(trace.events,0)
    def test_idle_wait_has_no_register_effects(self):
        trace=self.Trace();memory=self.initial();result=self.execute('wait',memory=memory,trace=trace)
        self.assertEqual(result['result'],0);self.assertEqual(result['memory'],tuple(memory));self.assertEqual(trace.events,0)
    def test_timeout_reads_exact_limit_then_acknowledges_and_clears_busy(self):
        from ir_processing_machine import MMIO,WRITE,SYNC
        memory=self.initial();self.put(memory[27],8,0xFFFFFFFF,1);trace=self.Trace(timeout_launch=0)
        result=self.execute('wait',memory=memory,trace=trace)
        self.assertEqual(result['result'],0xFFFFFFFF);self.assertEqual(trace.reads,200002);self.assertEqual(trace.events,200004)
        self.assertEqual(trace.counts[(WRITE,MMIO)],1);self.assertEqual(trace.counts[(SYNC,0)],1)
        self.assertEqual(self.words(result['memory'][27],8,2),(0,0))
    def test_original_numeric_domain_rejects_bad_ring_and_permutation(self):
        from ir_processing_machine import OBJECT,WORK,COPY
        for packed in (0,33,1<<16|1):
            with self.assertRaises(ValueError):self.execute('multiply',OBJECT,COPY,packed,WORK)
        with self.assertRaises(ValueError):self.execute('inverse',WORK,COPY,OBJECT,1)
        with self.assertRaises(ValueError):self.execute('hardware_output',WORK,COPY,31)
        with self.assertRaises(ValueError):self.execute('fft64',WORK+2,COPY)
    def test_active_runtime_requires_constructor_layout(self):
        from ir_processing_machine import OBJECT
        with self.assertRaises(ValueError):self.execute('process',OBJECT,128,0,0)

if __name__=='__main__':unittest.main()
