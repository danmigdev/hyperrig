"""Focused original-instruction witnesses for the joined resource lifecycle."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_parameter_lifecycle_machine import (EffectParameterLifecycleProgram, DIRECT_RESOURCES,
    RESOURCE_REGIONS, PRIVATE, MAPPED, ROOT)
from verify_effect_parameter_lifecycle import (check_derivative, DERIVATIVE_SOURCE, Script,
    delay_fixture, initial, setword, EFFECTS, CONTROL, ALLOCATOR, RELEASE, MODE, OLD, NEW, RESTORED)


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectParameterLifecycleProgram()
    def run_case(self,memory=None,plan=None,mutations=(),operation='commit',args=(0,0,100)):
        return self.program.execute(memory or delay_fixture(),operation,args,Script(plan,mutations))
    def word(self,result,address,size=4):
        for (base,n),data in zip(MAPPED,result['memory']):
            if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
        raise AssertionError('test address unmapped')
    def test_derivative_is_exact_narrow_substitution(self):
        proof=check_derivative()
        self.assertEqual(sum(proof['direct_call_substitutions'].values()),19)
    def test_derivative_rejects_body_edit(self):
        source=(ROOT/DERIVATIVE_SOURCE).read_text().replace('if(slot>15)return UINT32_MAX;','if(slot>14)return UINT32_MAX;',1)
        with self.assertRaises(ValueError):check_derivative(derived=source)
    def test_derivative_rejects_resource_call_reverted(self):
        source=(ROOT/DERIVATIVE_SOURCE).read_text().replace('RESOURCE3(a,0x0202edb8,','CALL3(a,0x0202edb8,',1)
        with self.assertRaises(ValueError):check_derivative(derived=source)
    def test_complete_resource_entries_loaded(self):
        self.assertEqual(len(RESOURCE_REGIONS),19)
        for start,_ in RESOURCE_REGIONS.values():self.assertIn(start,self.program.code)
        for start,end in ((0x01c068ee,0x01c06904),(0x0202ef12,0x0202ef22),(0x0202ef3e,0x0202ef48)):
            self.assertFalse(any(start<=pc<end for pc in self.program.code))
    def test_allocation_runs_real_migration_and_encoder(self):
        result=self.run_case(plan={ALLOCATOR:NEW})
        for entry in (0x0202edb8,0x0202ee3c,0x01c065e2,0x01c065f6):self.assertIn(entry,result['real_calls'])
        self.assertEqual(self.word(result,EFFECTS+84),NEW)
        self.assertEqual(result['private_events'][0][1],((PRIVATE,b'\0'*4),))
    def test_failure_runs_release_flush_and_restore_attempt(self):
        memory=delay_fixture();setword(memory,CONTROL+8,1,1);setword(memory,CONTROL+88,1,1)
        result=self.run_case(memory,{ALLOCATOR:0})
        self.assertEqual(result['value'],0xfffffffd)
        self.assertEqual(self.word(result,EFFECTS+84),0)
        self.assertEqual(self.word(result,EFFECTS+1,1),0)
        self.assertEqual(self.word(result,CONTROL+8,1),0)
        self.assertEqual(sum(t==ALLOCATOR for _,t,_ in result['service_sites']),4)
        self.assertEqual(result['private_events'][0][1],((PRIVATE,b'\1\0\0\0'),))
    def test_restoration_reinstalls_old_capacity(self):
        result=self.run_case(delay_fixture(capacity=2048),{ALLOCATOR:(0,0,0,RESTORED)})
        self.assertEqual(result['value'],0xfffffffd)
        self.assertEqual(self.word(result,EFFECTS+84),RESTORED)
        self.assertEqual(self.word(result,EFFECTS+88),2048)
        self.assertIn(0x0201a9dc,result['real_calls'])
    def test_private_flag_mutation_changes_real_migration_gate(self):
        result=self.run_case(plan={ALLOCATOR:NEW},mutations=((ALLOCATOR,0,PRIVATE,1,4),))
        self.assertNotIn(0x0202ee3c,result['real_calls'])
        call=next(x for x in result['calls'] if x[0]==ALLOCATOR)
        self.assertEqual(call[4],((PRIVATE,b'\0'*4),));self.assertEqual(call[5],((PRIVATE,b'\1\0\0\0'),))
    def test_failure_mode_callback_sees_initialized_live_flag(self):
        result=self.run_case(plan={ALLOCATOR:0},mutations=((MODE,1,PRIVATE,0,4),))
        calls=[x for x in result['calls'] if x[0]==MODE]
        self.assertEqual(calls[1][4],((PRIVATE,b'\1\0\0\0'),))
        self.assertEqual(calls[1][5],((PRIVATE,b'\0'*4),))
    def test_parent_clear_callback_sees_flag_before_success_load(self):
        memory=delay_fixture();setword(memory,0x01c34194,0x0202eefa)
        result=self.run_case(memory,{ALLOCATOR:NEW},((0x0202eefa,0,PRIVATE,1,4),))
        self.assertNotIn(0x0202ee3c,result['real_calls'])
        clear=next(x for x in result['calls'] if x[0]==0x0202eefa)
        self.assertEqual(clear[4],((PRIVATE,b'\0'*4),))
        self.assertEqual(clear[5],((PRIVATE,b'\1\0\0\0'),))
    def test_every_resource_token_remains_one_word_free_callback(self):
        for token in DIRECT_RESOURCES:
            memory=delay_fixture();setword(memory,CONTROL+56,token)
            result=self.run_case(memory,{ALLOCATOR:NEW})
            self.assertIn((0x0202f2aa,token,1),result['service_sites'])
    def test_allocator_token_collision_does_not_reenter_constructor(self):
        memory=delay_fixture();setword(memory,CONTROL+52,0x0202edb8)
        result=self.run_case(memory,{0x0202edb8:NEW})
        self.assertIn((0x0202df16,0x0202edb8,1),result['service_sites'])
        self.assertEqual(sum(t==0x0202edb8 for t in result['real_calls']),1)
    def test_alternate_clear_is_two_words_even_for_loaded_resource(self):
        memory=delay_fixture();setword(memory,0x01c34194,0x0202eefa)
        result=self.run_case(memory,{ALLOCATOR:NEW})
        self.assertIn((0x01c0656e,0x0202eefa,2),result['service_sites'])
    def test_native_callers_supply_real_fifth_migration_word(self):
        result=self.run_case(delay_fixture(47,15),{ALLOCATOR:NEW})
        self.assertIn((0x0202f276,0x0202ee3c),result['resource_sites'])
        self.assertEqual(self.word(result,EFFECTS+288),47)
        self.assertGreater(self.word(result,EFFECTS+324),47)
    def test_ir_wrapper_calls_real_size_helpers(self):
        memory=initial(7)
        for address,value in ((EFFECTS+48,OLD),(EFFECTS+52,4096),(EFFECTS+288,OLD+8192),(OLD+8192,1)):
            setword(memory,address,value)
        result=self.run_case(memory,operation='commit',args=(0,3,8))
        self.assertIn(0x0202f014,result['real_calls']);self.assertIn(0x0202f02e,result['real_calls'])
        self.assertNotIn(0x0202f014,[x[0] for x in result['calls']])
    def test_extra_state_allocation_is_reached_from_complete_caller(self):
        memory=initial(29)
        for address,value in ((EFFECTS+84,OLD),(EFFECTS+88,256),(CONTROL+52,ALLOCATOR),
            (0x01c34458,MODE),(0x01c34194,0x0201a9dc)):
            setword(memory,address,value)
        setword(memory,EFFECTS+369,255,1)
        result=self.run_case(memory,{ALLOCATOR:NEW},operation='commit',args=(0,6,2))
        self.assertIn(0x0202eeba,result['real_calls']);self.assertIn(0x01c05ff2,result['real_calls'])
        self.assertEqual(self.word(result,EFFECTS+92),NEW)
        self.assertEqual(self.word(result,EFFECTS+7,1),1)
    def test_mode_reset_is_real_and_constructor_remains_explicit(self):
        result=self.run_case(initial(3),operation='commit',args=(0,3,2))
        self.assertIn(0x0202efe2,result['real_calls'])
        self.assertIn(0x0202cf62,[x[0] for x in result['calls']])
    def test_input_contracts(self):
        with self.assertRaises(ValueError):self.program.execute([], 'commit',(0,0,1))
        with self.assertRaises(ValueError):self.program.execute(initial(),'commit',(0,0))


if __name__=='__main__':unittest.main()
