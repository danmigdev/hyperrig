"""Focused joined original constructor, alias, producer and ownership evidence."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ir_effect_numerical_machine import IrEffectNumericalProgram,ALL_REGIONS,MAPPED
from verify_ir_effect_numerical import (initial,setword,window_setup,Script,check_derivative,
    EFFECT,CONTROL,SOURCE,OLD,NEW,TEMP,PARAMETERS,GAIN,ALLOCATE,READ,RELEASE,MODE,PREPARE,CONSTRUCT,PRODUCER)


class NumericalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=IrEffectNumericalProgram()
    def run_case(self,name,args,memory=None,returns=None,mutations=()):
        return self.program.execute(initial() if memory is None else memory,name,args,Script(returns,mutations))
    def word(self,memory,address,size=4):
        for (base,n),data in zip(MAPPED,memory):
            if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
        raise AssertionError('unmapped test word')
    def test_exact_35_region_closure_and_derivative(self):
        self.assertEqual(len(ALL_REGIONS),35);self.assertEqual(len(self.program.code),1453)
        self.assertEqual(check_derivative()['direct_call_replacements'],3)
    def test_direct_prepare_publishes_constructed_object(self):
        m=initial();window_setup(m,16)
        r=self.run_case('prepare',(EFFECT,1),m,{ALLOCATE:NEW})
        self.assertEqual(r['result'],(0,0));self.assertEqual(self.word(r['memory'],NEW+4),1)
        self.assertEqual(self.word(r['memory'],EFFECT+288),NEW)
        self.assertEqual(self.word(r['memory'],EFFECT+84),NEW)
        self.assertIn(CONSTRUCT,r['internal_calls']);self.assertIn(0x020317c8,r['internal_calls'])
        self.assertNotIn(PREPARE,[t for t,*_ in r['calls']])
    def test_mode_zero_retry_is_internal_and_frees_allocation(self):
        m=initial();window_setup(m,16)
        r=self.run_case('mode_prepare',(EFFECT,),m,{ALLOCATE:(0,NEW)})
        self.assertEqual(r['result'],(0xffffffff,0))
        self.assertEqual([x[1][0] for x in r['calls'] if x[0]==ALLOCATE],[9312,0])
        self.assertEqual([x[1][0] for x in r['calls'] if x[0]==RELEASE],[NEW])
        self.assertEqual(r['internal_calls'].count(PREPARE),2)
    def test_high_bit_source_count_produces_zero_spectrum(self):
        m=initial();window_setup(m,0x80000000)
        r=self.run_case('prepare',(EFFECT,1),m,{ALLOCATE:NEW})
        self.assertEqual(self.word(r['memory'],NEW+4),1)
        self.assertTrue(all(self.word(r['memory'],NEW+2616+4*i)==0 for i in range(258)))
    def test_source_4077_is_not_rejected(self):
        m=initial();window_setup(m,4077)
        r=self.run_case('prepare',(EFFECT,1),m,{ALLOCATE:NEW})
        self.assertEqual(r['result'],(0,0));self.assertEqual(self.word(r['memory'],EFFECT+292),128)
    def test_wrapped_raw_count_has_zero_partitions(self):
        r=self.run_case('construct_copy',(NEW,SOURCE,0xffffffff))
        self.assertEqual(r['result'],(NEW,0));self.assertEqual(self.word(r['memory'],NEW+4),0)
        self.assertNotIn(0x020315b8,r['internal_calls']);self.assertNotIn(0x020317c8,r['internal_calls'])
        self.assertEqual(self.word(r['memory'],NEW+48),NEW+5696)
    def test_sample_source_pointer_reloads_after_header_alias(self):
        m=initial();window_setup(m,128);setword(m,0,32767,2);object_=CONTROL+64-552
        r=self.run_case('prepare',(EFFECT,1),m,{ALLOCATE:object_})
        self.assertEqual(r['result'],(0,0))
        self.assertEqual(self.word(r['memory'],CONTROL+60),1)
        # The reloaded pointer is 1, so the signed16 read sees 127 from the high
        # byte of our sample at address zero. Normalization stores 127/2^22.
        self.assertEqual(self.word(r['memory'],CONTROL+64),0x37fe0000)
    def test_temporary_restores_globals_after_real_construction(self):
        m=initial();window_setup(m,16)
        r=self.run_case('temporary',(EFFECT,SOURCE,16,12,0x40000000,0,0,0),m,{ALLOCATE:NEW})
        for address in (CONTROL+60,CONTROL+64,CONTROL+80,GAIN,CONTROL+68):
            self.assertEqual(self.word(r['memory'],address),self.word(m,address))
        self.assertEqual(self.word(r['memory'],EFFECT+288),NEW)
    def test_unknown_producer_collision_remains_external(self):
        r=self.run_case('construct',(NEW,16,PREPARE,PARAMETERS))
        self.assertEqual([x[:3] for x in r['service_sites']],[(0x02031a00,PREPARE,4)])
        self.assertNotIn(PREPARE,r['internal_calls'])
    def test_reset_reloads_mutable_time_history_pointer(self):
        r=self.run_case('construct',(NEW,16,PRODUCER,PARAMETERS),mutations=((PRODUCER,0,NEW+48,NEW+4,4),))
        self.assertEqual(self.word(r['memory'],NEW),1)
        self.assertTrue(all(self.word(r['memory'],NEW+4+4*i)==0 for i in range(256)))
    def test_allocation_change_is_visible_to_sample_getter(self):
        m=initial();window_setup(m,128)
        r=self.run_case('prepare',(EFFECT,1),m,{ALLOCATE:NEW},((ALLOCATE,0,CONTROL+64,0x80000000,4),))
        self.assertEqual(r['result'],(0,0));self.assertEqual(self.word(r['memory'],EFFECT+292),128)
        self.assertEqual(self.word(r['memory'],NEW+2616),0)
    def test_publication_overwrites_free_callback_fields(self):
        m=initial();window_setup(m,16);setword(m,EFFECT+84,OLD)
        r=self.run_case('prepare',(EFFECT,1),m,{ALLOCATE:NEW},((RELEASE,0,EFFECT+288,0x12345678,4),))
        self.assertEqual(r['calls'][-1][1][0],OLD)
        self.assertEqual(self.word(r['memory'],EFFECT+288),NEW)
    def test_wrapped_object_has_native_pointer_words(self):
        r=self.run_case('construct_copy',(0xfffff000,SOURCE,129))
        self.assertEqual(self.word(r['memory'],0xfffff004),2)
        self.assertEqual(self.word(r['memory'],0xfffff030),(0xfffff000+5696+2*2064)&0xffffffff)
    def test_fft_intervals_are_disjoint_for_every_partition(self):
        for p in range(1,33):
            h=2616+2064*p
            for i in range(p):
                spans=((552,1576),(2616+1032*p+1032*i,2616+1032*p+1032*(i+1)),
                    (h,h+1024),(h+2048,h+3080),(h+4104,h+4616))
                for n,(a,b) in enumerate(spans):
                    self.assertLess(b,1<<32)
                    for x,y in spans[n+1:]:self.assertTrue(b<=x or y<=a)


if __name__=='__main__':unittest.main()
