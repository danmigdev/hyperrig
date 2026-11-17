"""Independent native witnesses for resource eviction and caller lifetimes."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_resource_ownership_machine import (EffectResourceOwnershipProgram,FLUSH_CALL,
    REMOVE,OWNED_CLOSURE,MAPPED,PRIVATE,ROOT)
from verify_effect_resource_ownership import (check_derivatives,teardown_fixture,Script,
    setword,EFFECTS,CONTROL,ALLOCATOR,RELEASE,MODE,NEW,RESTORED,ARENA,OWNERSHIP_REGIONS,RAM,AUTOMATION)

class ResourceOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectResourceOwnershipProgram()
    def run_case(self,name='resource_flush',args=(),memory=None,plan=None,mutations=(),stop=False):
        return self.program.execute(memory or teardown_fixture(),name,args,Script(plan,mutations),stop_extra_overread=stop)
    def word(self,result,address,size=4):
        for (base,n),data in zip(MAPPED,result['memory']):
            if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
        raise AssertionError('unmapped assertion')
    def test_exact_two_derivatives(self):
        proof=check_derivatives()
        self.assertEqual(proof['new_original_functions'],0)
        self.assertEqual(proof['original_direct_flush_call'],0x0202edaa)
    def test_resource_guard_and_bridge_edits_are_rejected(self):
        source=(ROOT/'firmware/src/hyperrig_effect_resource_ownership.c').read_text()
        for old,new in (('if(a->error)return 0;','if(a->error)return 1;'),
            ('(void)remove_slot(a,slot);','(void)call(a,0x0202eb4c,slot);'),
            ('a->error=status;','a->error=0;')):
            with self.assertRaises(ValueError):check_derivatives(joined=source.replace(old,new,1))
    def test_lifecycle_semantic_or_bridge_edits_are_rejected(self):
        source=(ROOT/'firmware/src/hyperrig_effect_resource_ownership_lifecycle.c').read_text()
        for old,new in (('if(slot>15)return UINT32_MAX;','if(slot>14)return UINT32_MAX;'),
            ('hyperrig_effect_resource_ownership_execute(entry,args,out,&io)',
             'hyperrig_effect_parameter_resources_execute(entry,args,out,&io)'),
            ('released=word(a,PRIVATE);a->private_live=0;','a->private_live=0;released=word(a,PRIVATE);')):
            with self.assertRaises(ValueError):check_derivatives(lifecycle_joined=source.replace(old,new,1))
    def test_scene_success_body_and_immediate_guard_are_checked(self):
        source=(ROOT/'firmware/src/hyperrig_effect_resource_ownership_scene.c').read_text()
        for old,new in (('c->callbacks[761]=0;','c->callbacks[761]=1;'),
            ('if(c->io->outer_error&&*c->io->outer_error)c->fault=-203;',''),
            ('return failures;','return failures+1;')):
            with self.assertRaises(ValueError):check_derivatives(scene_joined=source.replace(old,new,1))
    def test_only_required_whole_ownership_closure_is_added(self):
        self.assertEqual(set(OWNED_CLOSURE),{'lookup','release','detach','capture','remove'})
        self.assertNotIn(0x0202ec30,self.program.code)
        self.assertEqual(self.program.code[FLUSH_CALL][0],'call -610')
    def test_flush_runs_removal_and_preserves_queue_bytes_until_final_count_clear(self):
        r=self.run_case()
        self.assertEqual(r['ownership_sites'],[(FLUSH_CALL,REMOVE)]*3)
        self.assertEqual(self.word(r,CONTROL+8,1),0)
        self.assertEqual([self.word(r,CONTROL+88+i,1) for i in range(3)],[1,2,3])
        self.assertEqual(self.word(r,CONTROL+14,1),3)
        self.assertEqual([self.word(r,CONTROL+348+i,1) for i in range(3)],[1,2,3])
        self.assertEqual(self.word(r,CONTROL+15,1),6)
        for slot in (1,2,3):self.assertEqual(self.word(r,EFFECTS+480*slot+1,1),0)
        self.assertEqual(self.word(r,0x01c34468),1)
        self.assertNotIn(REMOVE,[x[0] for x in r['calls']])
    def test_duplicate_evictions_do_not_free_the_same_slot_twice(self):
        r=self.run_case(memory=teardown_fixture(15))
        self.assertEqual(len(r['ownership_sites']),15)
        self.assertEqual(len(r['calls']),15)
        self.assertEqual(self.word(r,0x01c34468),13)
    def test_callback_mutated_queue_count_controls_next_flush_iteration(self):
        r=self.run_case(mutations=((RELEASE,0,CONTROL+8,1,1),))
        self.assertEqual(len(r['ownership_sites']),1)
        self.assertEqual(self.word(r,EFFECTS+960+1,1),1)
        self.assertEqual(self.word(r,CONTROL+8,1),0)
    def test_missing_callback_large_count_does_not_reach_private_overread(self):
        m=teardown_fixture(extra=255);setword(m,CONTROL+56,0)
        r=self.run_case(memory=m,stop=True)
        self.assertEqual(r['status'],0);self.assertFalse(r['calls'])
    def test_lazy_prefix_keeps_preceding_slot_and_caller_writes(self):
        r=self.run_case(memory=teardown_fixture(extra=4),stop=True)
        self.assertEqual(r['status'],-202);self.assertEqual(r['stop_pc'],0x0202df8a)
        self.assertEqual(self.word(r,CONTROL+8,1),3)
        self.assertEqual(self.word(r,EFFECTS+480+84),0)
        self.assertEqual(self.word(r,EFFECTS+480+48),ARENA+8256)
        self.assertEqual(self.word(r,EFFECTS+960+1,1),1)
        self.assertEqual(len(r['calls']),4)
    def test_parameter_prefix_preserves_initialized_pending_flag(self):
        r=self.run_case('commit',(0,0,100),teardown_fixture(extra=4),{ALLOCATOR:(0,0,NEW)},stop=True)
        self.assertEqual(r['status'],-202);self.assertTrue(r['pending_flag_at_stop'])
        self.assertEqual(r['private_at_stop'],((PRIVATE,b'\1\0\0\0'),))
        self.assertEqual(sum(x[0]==ALLOCATOR for x in r['calls']),2)
        self.assertNotIn(0x0202cf62,[x[0] for x in r['calls']])
    def test_nested_callback_can_mutate_private_flag_until_prefix(self):
        r=self.run_case('commit',(0,0,100),teardown_fixture(extra=4),{ALLOCATOR:(0,0,NEW)},
            ((RELEASE,1,PRIVATE,0x76543210,4),),True)
        self.assertEqual(r['private_at_stop'],((PRIVATE,b'\x10\x32\x54\x76'),))
        self.assertEqual(r['calls'][-1][5],r['private_at_stop'])
    def test_scene_fallback_prefix_keeps_busy_byte_and_pending_flag(self):
        memory=teardown_fixture(extra=4);state=0x01c26890;scene=state+11936
        for address,value,width in ((RAM+8,1,1),(RAM+44,24,4),(state+280,2,4),(CONTROL+28,1,1),
            (scene,1,1),(scene+2,1,2),(scene+22,100,2),(RAM+88,0,4),(state+956,1,4)):
            setword(memory,address,value,width)
        for i in range(8):setword(memory,CONTROL+210+i,1,1);setword(memory,AUTOMATION+448*i+1,1,1)
        r=self.run_case('scene_inner',(0,),memory,{ALLOCATOR:(0,0,NEW)},stop=True)
        self.assertEqual(r['status'],-202);self.assertEqual(self.word(r,0x01c34489,1),1)
        self.assertTrue(r['pending_flag_at_stop']);self.assertEqual(self.word(r,CONTROL+8,1),3)
    def test_successful_retry_and_restore_have_real_teardown(self):
        for path,expected,capacity in (((0,0,NEW),NEW,None),((0,0,0,RESTORED),RESTORED,256)):
            r=self.run_case('commit',(0,0,100),plan={ALLOCATOR:path})
            self.assertEqual(r['status'],0);self.assertEqual(self.word(r,EFFECTS+84),expected)
            self.assertEqual(len(r['ownership_sites']),3)
            if capacity is not None:self.assertEqual(self.word(r,EFFECTS+88),capacity)
            self.assertFalse(r['private_at_stop']);self.assertFalse(r['pending_flag_at_stop'])
    def test_every_ownership_token_stays_a_one_word_release_callback(self):
        for token,_ in OWNERSHIP_REGIONS.values():
            m=teardown_fixture(1);setword(m,CONTROL+56,token)
            r=self.run_case(memory=m)
            self.assertEqual([x[0] for x in r['calls']],[token]*5)
            self.assertTrue(all(arity==1 for _,_,arity in r['service_sites']))
    def test_release_token_can_be_replaced_with_zero(self):
        r=self.run_case(memory=teardown_fixture(1),mutations=((RELEASE,0,CONTROL+56,0,4),))
        self.assertEqual([x[0] for x in r['calls']],[RELEASE,0,0,0])
    def test_late_ir_and_capture_reloads_remain_visible(self):
        r=self.run_case(memory=teardown_fixture(1),mutations=((RELEASE,0,EFFECTS+480+48,NEW,4),
            (RELEASE,0,EFFECTS+480,31,1),(RELEASE,0,EFFECTS+480+288,0x01c2fa38,4)))
        self.assertEqual(r['calls'][-1][1][0],NEW)
        self.assertEqual(self.word(r,CONTROL+6,1),254)
    def test_returned_results_have_original_void_resource_semantics(self):
        r=self.run_case(memory=teardown_fixture(0))
        self.assertEqual(r['result'],(0,0));self.assertEqual(r['status'],0)
    def test_native_argument_contracts(self):
        with self.assertRaises(ValueError):self.program.execute([],'resource_flush')
        with self.assertRaises(ValueError):self.program.execute(teardown_fixture(),'resource_flush',(1,))
        with self.assertRaises(ValueError):self.program.execute(teardown_fixture(),'commit',(0,0,-1))

if __name__=='__main__':unittest.main()
