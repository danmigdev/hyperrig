"""Focused native control-flow, packet and numerical-domain regressions."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_resampling_machine import EffectResamplingProgram, REGIONS, STATIC
from verify_effect_resampling import fixture, parameters, SOURCE, OUTPUT

class EffectResamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectResamplingProgram()
    def execute(self,name,n,mode=0,values=None):
        _,_,prefix,count=parameters(name,n,mode)
        values=[0]*(prefix+count) if values is None else values
        return self.program.execute(fixture(name,n,mode,values),name,SOURCE,OUTPUT,n,mode)
    def test_complete_regions(self):
        self.assertEqual(len(self.program.code),612)
        self.assertEqual(sum(b-a for a,b in REGIONS.values()),2176)
    def test_tables(self):
        self.assertEqual(sum(b-a for a,b in STATIC.values()),72)
        self.assertEqual(struct.unpack('<3I',self.program.data['tap_counts']),(5,3,4))
    def test_all_zero(self):
        for name in REGIONS:
            result=self.execute(name,8)
            self.assertEqual(set(result['memory'][1][1]),{0})
    def test_history_is_not_written(self):
        memory=fixture('down',7,0,list(range(31)))
        result=self.program.execute(memory,'down',SOURCE,OUTPUT,7,0)
        self.assertEqual(memory[0],result['memory'][0])
    def test_mode1_fast_uses_five_taps(self):
        for name,kernel in (('up','up5'),('down','down5')):
            self.assertEqual(self.execute(name,4,1)['calls'][0][0],REGIONS[kernel][0])
    def test_mode2_fast_uses_four_taps(self):
        for name,kernel in (('up','up4'),('down','down4')):
            self.assertEqual(self.execute(name,4,2)['calls'][0][0],REGIONS[kernel][0])
    def test_fast_ignores_other_selectors(self):
        self.assertEqual(self.execute('up',4,0xffffffff)['calls'][0][0],REGIONS['up5'][0])
    def test_scalar_has_no_external_calls(self):
        for mode in range(3):self.assertEqual(self.execute('up',3,mode)['calls'],[])
    def test_negative_nonmultiple_noop(self):
        memory=((SOURCE,b'\xa5'*16),(OUTPUT,b'\x5a'*16))
        for name in ('up','down'):
            result=self.program.execute(memory,name,SOURCE,OUTPUT,0xffffffff,0xffffffff)
            self.assertEqual(result['memory'],memory)
    def test_native_nonterminating_inputs_rejected(self):
        for count in (0,0x80000000,0xfffffffc):
            with self.assertRaisesRegex(ValueError,'nonterminating'):
                self.program.execute((),'up',SOURCE,OUTPUT,count,0)
    def test_raw_requires_multiple_four(self):
        with self.assertRaisesRegex(ValueError,'nonterminating'):self.execute('up5',3)
    def test_missing_history_fails(self):
        with self.assertRaisesRegex(ValueError,'uninitialized'):
            self.program.execute(((SOURCE,bytes(16)),(OUTPUT,bytes(32))),'up',SOURCE,OUTPUT,4,0)
    def test_odd_lane_preserves_int_min(self):
        result=self.execute('up5',4,values=[-0x80000000]*13)
        self.assertEqual(struct.unpack('<8i',result['memory'][1][1])[1::2],(-0x80000000,)*4)
    def test_scalar_packet_preserves_table_pointer(self):
        result=self.execute('up',1,0,list(range(10)))
        reads={address for address,_ in result['reads']}
        self.assertTrue(set(range(0x0203b780,0x0203b794,4))<=reads)
    def test_scalar_fast_agree_in_shared_mode(self):
        values=[(i-8)*999999 for i in range(14)]
        scalar=self.execute('up',5,0,values)['memory'][1][1]
        fast=self.execute('up5',4,0,values[:13])['memory'][1][1]
        self.assertEqual(scalar[:len(fast)],fast)

if __name__=='__main__':unittest.main()
