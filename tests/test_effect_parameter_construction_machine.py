"""Native call-site, shared-state and derivative witnesses for parameter construction."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from verify_effect_parameter_construction import (EffectParameterConstructionProgram,
    DIRECT_JOINS,REGIONS,MAPPED,ROOT,SOURCE,check_derivative,fixture,scene_fixture,
    teardown_fixture,Script,setword,EFFECTS,CONTROL,CONFIG,AUTOMATION,ARENA,
    ALLOCATOR,RELEASE,NEW,PRIVATE)

class ParameterConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectParameterConstructionProgram()
    def execute(self,name,args,memory=None,plan=None,mutations=(),stop=False):
        return self.program.execute(memory or fixture(),name,args,Script(plan,mutations),stop_extra_overread=stop)
    def word(self,result,address,size=4):
        for (base,n),data in zip(MAPPED,result['memory']):
            if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
        raise AssertionError('assertion address is unmapped')
    def test_exact_derivative(self):
        p=check_derivative();self.assertEqual(len(p['direct_sites']),3)
        self.assertTrue(p['resource_ownership_numerical_and_guarded_scene_sources_unchanged'])
    def test_ordinary_caller_semantics_cannot_change(self):
        s=(ROOT/SOURCE).read_text()
        with self.assertRaises(ValueError):check_derivative(s.replace('if(slot>15)','if(slot>14)',1))
    def test_each_direct_bridge_is_required(self):
        s=(ROOT/SOURCE).read_text()
        for before in ('construction(a,0x0202cf62,effect);','construction(a,0x0202cf62,PROPOSED);',
                       'construction(a,0x0202cd32,effect);'):
            with self.subTest(before=before),self.assertRaises(ValueError):check_derivative(s.replace(before,';',1))
    def test_first_fault_and_scene_guard_wiring_cannot_change(self):
        s=(ROOT/SOURCE).read_text()
        for before in ('if(status&&!a->error)a->error=status;','joined.outer_error=&a.error;'):
            with self.assertRaises(ValueError):check_derivative(s.replace(before,'',1))
    def test_closure_has_only_original_evidence(self):
        self.assertEqual(len(REGIONS),107);self.assertEqual(len(self.program.code),20072)
        self.assertEqual(len(self.program.static_regions),54)
        self.assertNotIn(0x0202ec30,self.program.code)
    def test_three_exact_incoming_call_packets(self):
        for pc,target in DIRECT_JOINS.items():
            text,size,*_=self.program.code[pc]
            self.assertEqual(pc+size+int(text.split()[1]),target)
            self.assertNotIn(pc,self.program.parallel_seconds)
    def test_commit_constructs_live_effect(self):
        r=self.execute('commit',(0,0,0xffffffe2))
        self.assertIn((0x0202f37c,0x0202cf62,EFFECTS),r['construction_sites'])
        self.assertNotIn(0x0202cf62,[x[0] for x in r['calls']])
        self.assertEqual(self.word(r,EFFECTS+70,2),0xffe2)
    def test_fast_constructs_native_proposed_copy(self):
        r=self.execute('fast',(0,0,30,8))
        self.assertIn((0x0202f970,0x0202cf62,0x01c33610),r['construction_sites'])
        self.assertEqual(self.word(r,0x01c33610+84),self.word(r,EFFECTS+84))
        self.assertGreater(self.word(r,AUTOMATION+3,1),0)
    def test_object_special_path_uses_live_effect(self):
        m=fixture(31);setword(m,ARENA+8192+628,1)
        r=self.execute('fast',(0,0,30,7),m)
        self.assertEqual(r['construction_sites'],[(0x0202f7ba,0x0202cd32,EFFECTS)])
    def test_proposed_pointer_retains_live_alias_writes(self):
        m=fixture(30);pointer=EFFECTS+480
        setword(m,EFFECTS+84,pointer);setword(m,pointer,0x53525631)
        setword(m,pointer+64,0xdeadbeef)
        r=self.execute('fast',(0,0,25,5),m)
        self.assertIn((0x0202f970,0x0202cf62,0x01c33610),r['construction_sites'])
        self.assertEqual(self.word(r,pointer+64),0)
        self.assertNotEqual(self.word(r,pointer+17328),0)
    def test_object_builder_writes_adjacent_live_fields(self):
        m=fixture(31);pointer=EFFECTS+480
        setword(m,EFFECTS+288,pointer);setword(m,pointer+628,1)
        for i in range(9):setword(m,pointer+80+4*i,3000)
        r=self.execute('fast',(0,0,25,5),m)
        self.assertNotEqual(self.word(r,pointer+308),0)
        self.assertEqual(r['construction_sites'],[(0x0202f7ba,0x0202cd32,EFFECTS)])
    def test_unready_object_stops_before_builder(self):
        r=self.execute('fast',(0,0,30,7),fixture(31))
        self.assertEqual(r['value'],0xfffffffa);self.assertFalse(r['construction_sites'])
    def test_free_callback_constructor_collisions_stay_external(self):
        for token in (0x0202cf62,0x0202cd32):
            m=teardown_fixture();setword(m,CONFIG+36,48000);setword(m,CONTROL+56,token)
            r=self.execute('commit',(0,0,100),m,{ALLOCATOR:(0,0,NEW)})
            self.assertTrue(any(t==token and n==1 for _,t,n in r['service_sites']))
            self.assertTrue(r['construction_sites']);self.assertTrue(r['ownership_sites'])
    def test_clear_callback_same_target_keeps_two_word_abi(self):
        m=teardown_fixture();setword(m,CONFIG+36,48000);setword(m,0x01c34194,0x0202cf62)
        r=self.execute('commit',(0,0,100),m,{ALLOCATOR:NEW})
        self.assertTrue(any(t==0x0202cf62 and n==2 for _,t,n in r['service_sites']))
    def test_scene_reaches_actual_producer(self):
        r=self.execute('scene_inner',(0,),scene_fixture())
        self.assertTrue(r['construction_sites']);self.assertEqual(self.word(r,0x01c34489,1),0)
    def test_scene_notification_collision_is_not_construction(self):
        r=self.execute('scene_inner',(0,),scene_fixture(notification=0x0202cf62))
        self.assertTrue(any(t==0x0202cf62 and n==1 for _,t,n in r['service_sites']))
        self.assertTrue(all(pc in DIRECT_JOINS for pc,_,_ in r['construction_sites']))
    def test_ownership_prefix_retains_pending_private_flag(self):
        m=teardown_fixture(extra=4);setword(m,CONFIG+36,48000)
        r=self.execute('commit',(0,0,100),m,{ALLOCATOR:(0,0,NEW)},stop=True)
        self.assertEqual(r['status'],-202);self.assertTrue(r['pending_flag_at_stop'])
        self.assertEqual(r['private_at_stop'],((PRIVATE,b'\1\0\0\0'),));self.assertFalse(r['construction_sites'])
    def test_entry_arguments_remain_original_words(self):
        with self.assertRaises(ValueError):self.program.execute(fixture(),'commit',(0,0,-1))
        with self.assertRaises(ValueError):self.program.execute([],'commit',(0,0,1))

if __name__=='__main__':unittest.main()
