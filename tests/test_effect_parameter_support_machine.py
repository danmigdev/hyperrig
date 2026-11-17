"""Focused native witnesses for parameter primitive ABI and arithmetic."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from effect_parameter_support_machine import (EffectParameterSupportProgram, REGIONS,
    MAPPED, ARENA, CONTROL, CALLBACKS, MASK32, MASK64)
from verify_effect_parameter_support import initial, put, Script

class ParameterSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.program = EffectParameterSupportProgram()
    def run_case(self, name, arguments, memory=None, mutations=()):
        return self.program.execute(initial() if memory is None else memory, name, *arguments, boundary=Script(mutations))
    def quotient(self, name, numerator, denominator, remainder=0):
        args = (numerator&MASK32,numerator>>32,denominator&MASK32,denominator>>32)
        if name == 'unsigned_divide': args += (remainder,)
        return self.run_case(name,args)
    def test_unsigned_endpoint_includes_both_post_return_tails(self):
        self.assertEqual(REGIONS['unsigned_divide'][1],0x02033412)
        for pc in (0x020333c2,0x020333f2,0x02033410): self.assertIn(pc,self.program.code)
    def test_selector_outside_domain_returns_without_table_read(self):
        for value in (0,1,2,24,0xffffffff):
            r=self.run_case('selector',(value,));self.assertEqual(r['result'],(0xffffffff,0))
            self.assertNotIn(0x01c060f4,r['visited'])
    def test_signed_clamps_include_int_min(self):
        for value,three,two in ((0,0,0),(1,1,2),(2,3,2),(0x7fffffff,3,2),(0x80000000,0,0),(0xffffffff,0,0)):
            self.assertEqual(self.run_case('clamp3',(value,))['result'][0],three)
            self.assertEqual(self.run_case('clamp2',(value,))['result'][0],two)
    def test_packing_reloads_halfword_after_aliased_output(self):
        m=initial();put(m[3],8,2,2);put(m[3],12,0,2)
        r=self.run_case('pack',(ARENA,ARENA+8,ARENA+100),m)
        self.assertEqual(r['memory'][3][8],100);self.assertEqual(r['memory'][3][100],0)
    def test_packing_second_selector_is_cached_before_output(self):
        m=initial();put(m[3],8,2,2);put(m[3],12,2,2);m[3][10]=0
        r=self.run_case('pack',(ARENA,ARENA+12,ARENA+100),m)
        self.assertEqual(r['memory'][3][100],0)
        self.assertEqual(r['result'],(0,0))
    def test_extra_primary_is_required_even_for_separate_buffer(self):
        m=initial();put(m[3],84,0);m[3][7]=1;put(m[3],92,0x12345678)
        self.assertEqual(self.run_case('extra',(ARENA,),m)['result'][0],0)
    def test_extra_threshold_and_pointer_wrap(self):
        m=initial();put(m[3],84,0xfffffff0);m[3][7]=0;put(m[3],88,2021*16)
        self.assertEqual(self.run_case('extra',(ARENA,),m)['result'][0],0x1ff0)
    def test_memmove_overlap_and_neighbors(self):
        for destination,source in ((3,8),(8,3),(4,4),(2,3),(3,2)):
            m=initial();expected=bytearray(m[3]);expected[destination:destination+39]=bytes(expected[source:source+39])
            r=self.run_case('memmove',(ARENA+destination,ARENA+source,39),m)
            self.assertEqual(r['memory'][3],expected);self.assertEqual(r['result'],(ARENA+destination,0))
    def test_memmove_zero_does_not_access_source_or_destination(self):
        r=self.run_case('memmove',(0xffffffff,0,0))
        self.assertEqual(r['result'],(0xffffffff,0));self.assertFalse(r['writes'])
    def test_installed_clear_executes_complete_memory_body(self):
        m=initial();put(m[2],4,0x0201a9dc)
        r=self.run_case('clear_halfwords',(ARENA+3,1025),m)
        self.assertIn(0x0201a9dc,r['internal_calls']);self.assertIn(0x02033412,r['internal_calls'])
        self.assertEqual(r['memory'][3][3:2055],bytes(2052));self.assertEqual(r['calls'],[])
    def test_alternate_loaded_token_keeps_two_word_callback_abi(self):
        m=initial();put(m[2],4,REGIONS['selector'][0])
        r=self.run_case('clear_halfwords',(ARENA,1024),m)
        self.assertEqual(r['calls'][0][:2],(REGIONS['selector'][0],(ARENA,2048)+(0,)*10))
        self.assertNotIn(REGIONS['selector'][0],r['internal_calls'])
    def test_wrapped_clear_count_zero(self):
        m=initial();put(m[2],4,0)
        r=self.run_case('clear_halfwords',(0xffffffff,0xffffffff),m)
        self.assertEqual(r['memory'],tuple(map(bytes,m)));self.assertEqual(r['result'],(0,0))
    def test_unsigned_remainder_store_and_neighbor_preservation(self):
        r=self.quotient('unsigned_divide',0x123456789abcdef0,333,ARENA+3)
        q=0x123456789abcdef0//333;rem=0x123456789abcdef0%333
        self.assertEqual(r['result'],(q&MASK32,q>>32))
        self.assertEqual(int.from_bytes(r['memory'][3][3:11],'little'),rem)
        self.assertEqual(r['memory'][3][:3],initial()[3][:3])
    def test_unsigned_zero_divisor_has_two_remainder_paths(self):
        for numerator,remainder in ((7,7),(0x100000007,0)):
            r=self.quotient('unsigned_divide',numerator,0,ARENA)
            self.assertEqual(r['result'],(0,0));self.assertEqual(int.from_bytes(r['memory'][3][:8],'little'),remainder)
    def test_signed_min_overflow_wraps_and_zero_returns_zero(self):
        self.assertEqual(self.quotient('signed_divide',1<<63,MASK64)['result'],(0,0x80000000))
        self.assertEqual(self.quotient('signed_divide',MASK64,0)['result'],(0,0))
    def test_signed_division_truncates_towards_zero(self):
        self.assertEqual(self.quotient('signed_divide',(-11)&MASK64,3)['result'],(0xfffffffd,0xffffffff))
    def test_ratio_preserves_negative_high_word(self):
        self.assertEqual(self.run_case('ratio',(0,0,0))['result'],(0xffffffff,0xffffffff))
        self.assertEqual(self.run_case('ratio',(0xffffffff,0xffffffff,1))['result'],(0xfffeffff,0xffffffff))
    def test_ratio_positive_upper_clamp(self):
        self.assertEqual(self.run_case('ratio',(0x10000,0,1))['result'],(0x7fffffff,0))
    def test_tempo_invalid_id_and_zero_divisor(self):
        for args in ((0,12000),(10,12000),(1,0)):
            self.assertEqual(self.run_case('tempo',args)['result'],(0,0))
    def test_time_rule_shift_uses_low_five_bits(self):
        m=initial();put(m[1],40,1)
        self.assertEqual(self.run_case('time_rule',(100,0,32),m)['result'],(1200,0))
        self.assertEqual(self.run_case('time_rule',(100,1,32),m)['result'],(2350,0))

if __name__ == '__main__': unittest.main()
