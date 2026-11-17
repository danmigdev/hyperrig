"""Focused original-instruction setup contracts and derivative boundaries."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import verify_effect_setup as v
from effect_setup_machine import EffectSetupProgram,REGIONS,STATIC,ARITIES,PARAMETER_JOINS,CREATION_JOINS

class SetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectSetupProgram()
    def execute(self,name,args=(),m=None,plan=None,changes=()):
        return self.program.execute(v.initial() if m is None else m,name,args,boundary=v.Script(plan,changes))
    def word(self,result,address,n=4):
        for (a,size),data in zip(v.MAPPED,result['memory']):
            if a<=address<=address+n<=a+size:return int.from_bytes(data[address-a:address-a+n],'little')
        self.fail('test address outside mapped image')
    def test_exact_registry(self):
        self.assertEqual((len(REGIONS),sum(b-a for a,b in REGIONS.values()),len(self.program.new_code)),(45,5288,1759))
        self.assertEqual(sum(b-a for a,b in STATIC.values()),104)
        self.assertNotIn(0x01c060c9,self.program.code)
    def test_six_argument_neighbor_and_second_estimator_word(self):
        self.assertEqual(ARITIES['neighbor_group'],6);self.assertEqual(ARITIES['estimate_slot'],2)
        with self.assertRaises(ValueError):self.execute('neighbor_group',(0,0,0,0,9))
        with self.assertRaises(ValueError):self.execute('estimate_slot',(v.EFFECTS,))
    def test_exact_direct_sites(self):
        for pc,target in (PARAMETER_JOINS|CREATION_JOINS).items():
            text,size,*_=self.program.code[pc];self.assertEqual(text,f'call {target-pc-size}')
    def test_checked_derivative(self):
        v.check_derivative()
        with self.assertRaises(ValueError):v.derivative((v.ROOT/v.PARENT).read_text()+'\n')
    def test_stereo_return_only_target(self):
        self.assertEqual(self.execute('stereo_extra_cost',(11,))['value'],2400)
        self.assertEqual(self.execute('stereo_extra_cost',(39,))['value'],1140)
    def test_short_length_table_end(self):
        self.assertEqual([self.execute('object_segment',(33,i))['value'] for i in range(9,13)],[116,88,308,226])
        self.assertEqual(STATIC['object1_short_lengths'],(0x0203b4ae,0x0203b4b6))
    def test_greedy_is_not_subset_optimization(self):
        m=v.initial()
        for i,n in enumerate((8,7,6)):v.setword(m,v.ARENA+4*i,n)
        self.assertEqual(self.execute('partition_pack',(v.ARENA,3,7,13),m)['value'],1)
    def test_raw_count32_and_modulo_bit33(self):
        m=v.initial();v.setword(m,v.ARENA+31*4,8);v.setword(m,v.ARENA,7);v.setword(m,v.ARENA+32*4,13)
        self.assertEqual(self.execute('partition_pack',(v.ARENA,32,0x80000000,8),m)['value'],0x80000000)
        self.assertEqual(self.execute('partition_pack',(v.ARENA,33,1,13),m)['value'],1)
    def test_layout_and_extended_demand(self):
        self.assertEqual(self.execute('layout29',(0,1))['value'],56480)
        self.assertEqual(self.execute('demand_by_type',(29,0,1))['value'],32336)
        self.assertEqual(self.execute('demand_by_type',(29,0,0))['value'],4096)
    def test_wrapped_partition_count(self):
        self.assertEqual(self.execute('ir_partition_cost',(0xffffffff,0))['value'],6327)
        self.assertEqual(self.execute('ir_partition_cost',(0xffffffff,1))['value'],3727)
    def test_signed_saturation(self):
        for value,expected in ((0x40000000,0x7fffffff),(0xc0000000,0x80000000),(0x3fffffff,0x7ffffffe),(0xc0000001,0x80000002)):
            self.assertEqual(self.execute('saturating_double',(value,))['value'],expected)
    def test_estimator_preserves_raw_second_word(self):
        for kind,delta in ((5,305),(27,485),(31,485),(32,485),(33,485),(35,485)):
            m=v.initial(kind);a=self.execute('estimate_slot',(v.EFFECTS,0),m);b=self.execute('estimate_slot',(v.EFFECTS,0x80000000),m)
            self.assertEqual((b['value']-a['value'])&0xffffffff,delta)
            self.assertEqual(b['estimate_words'],[(v.EFFECTS,0x80000000)])
    def test_creation_validation_retains_counter(self):
        m=v.initial();v.setword(m,0x01c34468,0xffffffff);v.setword(m,0x01c3448b,7,1)
        r=self.execute('create',(2,0,1),m);self.assertEqual(r['value'],0xffffffff)
        self.assertEqual(self.word(r,0x01c34468),0);self.assertEqual(self.word(r,0x01c3448b,1),0)
    def test_progress_arity_and_phase_payloads(self):
        m=v.initial();v.setword(m,0x01c343c4,v.PROGRESS);v.setword(m,v.CONTROL+14,2,1)
        r=self.execute('create',(0,0,1),m);calls=[x for x in r['calls'] if x[0]==v.PROGRESS]
        self.assertEqual([x[1][1]>>16 for x in calls],[1,2,3,4,8,9]);self.assertEqual(calls[0][1][:3],(0,0x10001,2))
        self.assertTrue(all(n==3 for _,target,n in r['service_sites'] if target==v.PROGRESS))
    def test_disabled_wrapper_resets_override(self):
        m=v.initial();v.setword(m,v.CONTROL+84,7,1)
        r=self.execute('create_disabled',(0,0,1),m)
        self.assertEqual(self.word(r,v.CONTROL+84,1),0);self.assertEqual(self.word(r,v.EFFECTS+1,1),0)
        self.assertEqual(self.word(r,v.EFFECTS+2,1),1)
    def test_ir_creation_preserves_failed_preparation_status(self):
        m=v.initial();v.setword(m,v.CONTROL+60,v.MAPPED[1][0]);v.setword(m,v.CONTROL+64,16)
        v.setword(m,v.CONTROL+68,1);v.setword(m,0x01c1f7dc,0x3f800000)
        r=self.execute('create',(0,0,7),m,{v.ALLOC:0})
        self.assertEqual(r['value'],0xfffffffd);self.assertEqual(self.word(r,v.EFFECTS,1),0)
    def test_callback_token_is_not_loaded_entry(self):
        m=v.initial();v.setword(m,0x01c343c4,REGIONS['tempo'][0])
        r=self.execute('create',(0,0,1),m)
        self.assertTrue(any(target==REGIONS['tempo'][0] and count==3 for _,target,count in r['service_sites']))
        self.assertNotIn(REGIONS['tempo'][0],r['real_calls'])
    def test_pool_full_uses_four_low_bits(self):
        for mask,expected in ((15,1),(31,1),(255,1)):
            m=v.initial();v.setword(m,v.CONTROL+6,mask,1)
            self.assertEqual(self.execute('pool_full',(),m)['value'],expected)
    def test_sparse_replay_keeps_zero_gaps(self):
        import io
        raw=bytes(31)+b'abc'+bytes(12)+b'de'+bytes(40)+b'f';stream=io.BytesIO();v.write_sparse(stream,raw)
        stream.seek(0);count=struct.unpack('<I',stream.read(4))[0];out=bytearray(len(raw))
        for _ in range(count):a,n=struct.unpack('<2I',stream.read(8));out[a:a+n]=stream.read(n)
        self.assertEqual(out,raw);self.assertEqual(count,2)
    def test_all_new_table_proof_sites_are_decoded(self):
        for info in v.TABLE_PROOFS.values():
            for pc in info['sites']:self.assertTrue(pc in self.program.code,hex(pc))

if __name__=='__main__':unittest.main()
