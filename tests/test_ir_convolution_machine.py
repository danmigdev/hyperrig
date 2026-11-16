"""Independent expectations for original IR construction and numerical behavior."""
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
AVAILABLE=(ROOT/'analysis/firmware/m571_g_app/app.bin').is_file() and (ROOT/'upstream/pi32v2-isa/pi32v2isa').is_dir()

@unittest.skipUnless(AVAILABLE,'bootstrap and analyze the pinned firmware first')
class IrConvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'tools'))
        from ir_convolution_machine import IrConvolutionProgram,OBJECT,REGIONS
        from verify_ir_convolution import baseline,fft_fixture,Script,put,words
        cls.program=IrConvolutionProgram()
        cls.initial,cls.fixture,cls.put,cls.words=map(staticmethod,(baseline,fft_fixture,put,words));cls.Script=Script
        memory=baseline();put(memory[25],0,*([0]*129))
        cls.zero=cls.program.execute(memory,'construct',129,REGIONS['copy'][0],OBJECT)
        put(memory[25],0,*([0x3F800000]+[0]*127+[0x3F000000]))
        cls.impulses=cls.program.execute(memory,'construct',129,REGIONS['copy'][0],OBJECT)

    def execute(self,operation,*args,memory=None,plan=None):
        return self.program.execute(memory or self.initial(),operation,*args,boundary=self.Script(plan))

    def test_size_wraparound_and_partition_cap(self):
        for count,size in ((0,9312),(1,9312),(128,9312),(129,11376),(4096,73296),(4097,73296),(0xFFFFFFFF,9312)):
            self.assertEqual(self.execute('size',count)['result'],size)
    def test_phase_axes_keep_the_original_signed_zero(self):
        for index,expected in ((0,(0x3F800000,0x80000000)),(16,(0x80000000,0xBF800000)),
                              (32,(0xBF800000,0)),(48,(0,0x3F800000))):
            self.assertEqual(self.words(self.execute('phase',index,64)['memory'][24],0,2),expected)
    def test_phase_period_and_wrapped_numerator(self):
        for index in (0,1,17,63):
            self.assertEqual(self.execute('phase',index,64)['memory'][24],
                             self.execute('phase',index+64,64)['memory'][24])
        self.assertEqual(self.execute('phase',0,64)['memory'][24],self.execute('phase',0x40000000,64)['memory'][24])
    def test_q31_saturates_both_endpoints_and_truncates(self):
        for value,expected in ((0x3F800000,0x7FFFFFFF),(0xBF800000,0x80000000),(0x3F000000,0x40000000),
                               (0xBF000000,0xC0000000),(1,0),(0x7F800000,0x7FFFFFFF),(0xFF800000,0x80000000)):
            self.assertEqual(self.execute('q31',value)['result'],expected)
    def test_sample_sign_extension_and_out_of_range_zero(self):
        memory=self.initial([-32768,32767])
        for index,expected in ((0,0xBF800000),(1,0x3F7FFE00),(2,0),(0xFFFFFFFF,0)):
            self.assertEqual(self.execute('sample',index,0x38000000,memory=memory)['result'],expected)
    def test_matching_formats_copy_scaled_signed_samples(self):
        memory=self.initial([-32768,0,16384],255)
        result=self.execute('resample',0,5,1,memory=memory)
        self.assertEqual(self.words(result['memory'][24],0,5),(0xBF800000,0,0x3F000000,0,0))
    def test_upsampling_even_positions_include_half_gain(self):
        result=self.execute('resample',0,5,1,memory=self.initial([-32768,0,16384],0))
        self.assertEqual(self.words(result['memory'][24],0)[0],0xBF000000)
        self.assertEqual(self.words(result['memory'][24],16)[0],0x3E800000)
    def test_zero_length_producers_preserve_destination(self):
        memory=self.initial([1])
        for operation,args in (('resample',(0,0,1)),('produce',(0,0)),('copy',(4096,0))):
            self.assertEqual(self.execute(operation,*args,memory=memory)['memory'],tuple(memory))
    def test_copy_preserves_nan_payloads_and_signed_zero(self):
        memory=self.initial();values=(0x7F812345,0xFFC12345,0x80000000,0xDEADBEEF);self.put(memory[25],8,*values)
        result=self.execute('copy',2,4,memory=memory)
        self.assertEqual(self.words(result['memory'][24],0,4),values)
    def test_complex_fft_impulse_has_unit_spectrum(self):
        result=self.execute('fft128',memory=self.fixture(self.initial()))
        self.assertEqual(self.words(result['memory'][24],0,256),(0x3F800000,0)*128)
    def test_real_fft_impulse_has_129_unit_bins(self):
        from ir_convolution_machine import OUTPUT,WORK
        result=self.execute('real256',memory=self.fixture(self.initial()))
        values=self.words(result['memory'][24],OUTPUT-WORK,258)
        self.assertTrue(all(values[i]==0x3F800000 for i in range(0,258,2)))
        self.assertTrue(all(values[i]&0x7FFFFFFF==0 for i in range(1,258,2)))
    def test_zero_kernel_exhausts_48_scaling_steps(self):
        object=self.zero['memory'][23]
        self.assertEqual(self.words(object,16)[0],48)
        self.assertEqual(object[2616:2616+2064],bytes(2064))
    def test_coefficients_are_bin_major_across_two_partitions(self):
        self.assertEqual(self.words(self.impulses['memory'][23],16)[0],36)
        self.assertEqual(self.words(self.impulses['memory'][23],2616,516),(0x20000000,0,0x10000000,0)*129)
    def test_constructor_preserves_reserved_bytes_and_allocation_tail(self):
        object=self.zero['memory'][23]
        self.assertEqual(object[536:544],bytes([0xD6])*8)
        self.assertEqual(object[1576:2616],bytes([0xD6])*1040)
        self.assertEqual(object[11360:],bytes([0xD6])*(len(object)-11360))
    def test_constructor_resets_frequency_history_and_time_history(self):
        from ir_convolution_machine import OBJECT
        object=self.impulses['memory'][23];frequency=self.words(object,24)[0]-OBJECT;history=self.words(object,48)[0]-OBJECT
        self.assertEqual(object[frequency:frequency+2064],bytes(2064));self.assertEqual(object[history:history+1024],bytes(1024))
        self.assertEqual(self.words(object,8,2),(0,0))
    def test_constructor_executes_the_real_copy_callback_with_partition_arguments(self):
        from ir_convolution_machine import COPY,OBJECT
        self.assertEqual(self.zero['producer_calls'],[(COPY,OBJECT+552,0,128),(COPY,OBJECT+552,128,1)])
    def test_null_constructor_inputs_leave_every_region_unchanged(self):
        from ir_convolution_machine import OBJECT,REGIONS
        memory=self.initial([1])
        for args in ((0,REGIONS['produce'][0],OBJECT),(1,0,OBJECT),(1,REGIONS['produce'][0],0)):
            result=self.execute('construct',*args,memory=memory)
            self.assertEqual(result['result'],0);self.assertEqual(result['memory'],tuple(memory))
    def test_allocation_failure_does_not_free_or_publish(self):
        from ir_convolution_machine import ALLOCATE
        memory=self.initial([1]);result=self.execute('prepare',0,1,memory=memory,plan={ALLOCATE:(0,())})
        self.assertEqual(result['result'],0xFFFFFFFD);self.assertEqual(result['memory'],tuple(memory))
        self.assertEqual(len(result['calls']),1)
    def test_mode_zero_and_empty_ir_free_the_new_allocation(self):
        from ir_convolution_machine import ALLOCATE,FREE,OBJECT
        for samples,mode,size in (([1],0,0),([],1,9312)):
            result=self.execute('prepare',0,mode,memory=self.initial(samples))
            self.assertEqual(result['result'],0xFFFFFFFF)
            self.assertEqual([(a,b) for a,b,_ in result['calls']],[(ALLOCATE,size),(FREE,OBJECT)])
    def test_previous_object_is_freed_before_publication(self):
        from ir_convolution_machine import FREE,OBJECT
        memory=self.initial([1]);self.put(memory[21],8,0x12345678)
        result=self.execute('prepare',0,1,memory=memory)
        self.assertEqual(result['calls'][-1][:2],(FREE,0x12345678))
        self.assertEqual(self.words(result['calls'][-1][2][21],8)[0],0x12345678)
        self.assertEqual(self.words(result['memory'][21],8)[0],OBJECT)
        self.assertEqual(result['memory'][22][:4],bytes(4));self.assertEqual(result['memory'][22][4:],memory[22][4:])
    def test_allocation_callback_trim_reload_can_remove_the_fade(self):
        from ir_convolution_machine import ALLOCATE,DSP,OBJECT
        memory=self.initial([32767]*513);self.put(memory[17],20,1)
        result=self.execute('prepare',0,1,memory=memory,plan={ALLOCATE:(OBJECT,((DSP+80,512,4),))})
        self.assertEqual(self.words(result['memory'][21],20)[0],128)
        self.assertEqual(self.words(result['memory'][23],552,128),(0x3BFFFE00,)*128)
    def test_unmapped_source_and_unknown_producer_are_rejected(self):
        from ir_convolution_machine import OBJECT
        memory=self.initial([1]);self.put(memory[17],0,0)
        with self.assertRaises(ValueError):self.execute('sample',0,0x3F800000,memory=memory)
        with self.assertRaises(ValueError):self.execute('construct',1,0x12345678,OBJECT)
    def test_phase_zero_denominator_and_output_growth_are_rejected(self):
        with self.assertRaises(ValueError):self.execute('phase',1,0)
        with self.assertRaises(ValueError):self.execute('resample',4096,1,1)

if __name__=='__main__':unittest.main()
