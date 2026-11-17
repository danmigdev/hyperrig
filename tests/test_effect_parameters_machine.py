"""Independent original-instruction witnesses for parameter mutation and ABI."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_parameters_machine import (EffectParametersProgram, EffectParametersMachine,
    REGIONS, REUSED, TABLE_START, TABLE_END, MAPPED, RAM, EFFECTS, CONFIG, CONTROL,
    CALLBACKS, ROUTES, SAMPLES, ARENA, PRIVATE, ALLOCATE)

def put(memory,address,value,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:
            data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');return
    raise ValueError('test write outside borrowed map')
def get(memory,address,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
    raise ValueError('test read outside borrowed map')
def initial(type_=1):
    memory=[bytearray(n) for _,n in MAPPED]
    put(memory,EFFECTS,type_,1);put(memory,EFFECTS+2,1,1)
    put(memory,CONFIG+36,48077);put(memory,CONFIG+40,1000);put(memory,CONTROL+48,100000)
    return memory

class ParameterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectParametersProgram()
    def run_case(self,name,args,memory=None,boundary=None):
        return self.program.execute(initial() if memory is None else memory,name,args,
            boundary=boundary or (lambda target,args,m:0))
    def test_complete_endpoints_and_embedded_table(self):
        self.assertEqual(len(REGIONS),7);self.assertEqual(TABLE_END-TABLE_START,78)
        self.assertFalse(any(pc in self.program.code for pc in range(TABLE_START,TABLE_END)))
        self.assertEqual(REGIONS['fast'],(0x0202f6d4,0x0202fba6))
        self.assertEqual(REGIONS['commit'],(0x0202f07e,0x0202f46c))
    def test_classification_bitmaps_and_section_boundaries(self):
        cases=((4,0,1),(4,4,1),(4,5,0),(4,10,6),(4,11,1),(4,21,6),(4,32,6),
               (16,4,4),(16,8,5),(16,42,6),(39,17,3),(39,29,1),(39,35,1),(39,36,0),
               (0,0,0),(40,0,0),(0xffffffff,0,0),(7,2,2),(7,3,2),(7,4,0))
        for type_,index,result in cases:
            self.assertEqual(self.run_case('word_kind',(type_,index))['value'],result)
    def test_section_unsigned_wrap(self):
        self.assertEqual(self.run_case('section_kind',(0xffffffff,0xfffffffe))['value'],0)
        self.assertEqual(self.run_case('section_kind',(8,0xfffffffe))['value'],6)
    def test_auxiliary_index_wrap(self):
        for type_,index,expected in ((3,99,0),(39,0,16),(9,3,0),(10,3,0),(1,0,0xfffffffc)):
            self.assertEqual(self.run_case('auxiliary_index',(type_,index))['value'],expected)
    def test_invalid_slot_counter_order(self):
        for operation,args,expected in (('commit',(16,0,1),1),('fast',(16,0,1,2),0),('probe',(16,0,1),0)):
            r=self.run_case(operation,args)
            self.assertEqual(get(r['memory'],CALLBACKS+728),expected)
            self.assertEqual(r['calls'],[])
    def test_reset_precedes_missing_metadata(self):
        m=initial();put(m,ROUTES,7,1);put(m,ROUTES+4,255,1);put(m,CONTROL+210,1,1)
        r=self.run_case('commit',(0,6,12),m)
        self.assertEqual(r['value'],0xffffffff);self.assertIn(REUSED['reset_slot'][0],r['real_calls'])
        self.assertEqual(get(r['memory'],ROUTES,1),0);self.assertEqual(get(r['memory'],ROUTES+4,1),0)
        self.assertEqual(get(r['memory'],CONTROL+210,1),0)
    def test_commit_clamps_signed_argument_and_publishes_halfword(self):
        r=self.run_case('commit',(0,0,0x80000000))
        self.assertEqual(r['value'],0);self.assertEqual(get(r['memory'],EFFECTS+70,2),(-90)&65535)
    def test_probe_executes_real_pack_and_both_estimators(self):
        m=initial(11);put(m,EFFECTS+1,1,1)
        r=self.run_case('probe',(0,5,1),m)
        self.assertEqual(r['real_calls'].count(0x01c05c08),2)
        self.assertIn(0x01c06466,r['real_calls']);self.assertIn(0x01c055d2,r['real_calls'])
        self.assertNotIn(0x01c05c08,[t for t,*_ in r['calls']])
    def test_probe_routes_extra_cost_table_to_its_original_handler(self):
        m=initial(5);put(m,CONFIG+28,100,1);put(m,EFFECTS+1,1,1)
        for offset in (36,40,44):put(m,CONTROL+offset,0xffff)
        r=self.run_case('probe',(0,6,0),m)
        self.assertIn(0x01c05ca0,r['visited'])
        self.assertIn(0x01c05c08,r['real_calls'])
    def test_private_allocation_output_is_canonical_and_fully_initialized(self):
        m=initial(5);put(m,EFFECTS+84,ARENA);seen=[]
        def boundary(target,args,vm):
            if target==ALLOCATE:
                seen.append(args);self.assertEqual(args[2],PRIVATE)
                with self.assertRaisesRegex(ValueError,'uninitialized'):vm.read(PRIVATE,4)
                vm.write(PRIVATE,1,4)
            return 0
        r=self.run_case('commit',(0,0,10),m,boundary)
        self.assertEqual(len(seen),1);self.assertEqual(r['value'],0xfffffffd)
        event=next(event for event in r['calls'] if event[0]==ALLOCATE)
        self.assertEqual(event[4],());self.assertEqual(event[5],((PRIVATE,b'\1\0\0\0'),))
    def test_missing_private_output_is_rejected(self):
        m=initial(5);put(m,EFFECTS+84,ARENA)
        with self.assertRaisesRegex(ValueError,'initialize all four'):
            self.run_case('commit',(0,0,10),m)
    def test_divide_zero_on_allocation_failure_retains_original_minimum(self):
        m=initial(5);put(m,EFFECTS+84,ARENA);put(m,EFFECTS+324,70);put(m,CONFIG+36,0)
        def boundary(target,args,vm):
            if target==ALLOCATE:vm.write(PRIVATE,0,4)
            return 0
        r=self.run_case('commit',(0,0,10),m,boundary)
        self.assertEqual(r['value'],0xfffffffd)
        self.assertEqual(get(r['memory'],EFFECTS+70,2),10)
        self.assertIn(0x0202f230,r['visited'])
    def test_migration_stack_argument_and_free_token_collision(self):
        m=initial(5)
        for address,value in ((EFFECTS+84,ARENA+8192),(EFFECTS+88,1),(EFFECTS+324,16),(CONTROL+56,ALLOCATE)):
            put(m,address,value)
        def boundary(target,args,vm):
            if target==ALLOCATE and args[2]==PRIVATE:vm.write(PRIVATE,0,4);return ARENA+4096
            return 0
        r=self.run_case('commit',(0,0,10),m,boundary)
        migration=next(args for target,args,*_ in r['calls'] if target==0x0202ee3c)
        self.assertEqual(migration[:5],(EFFECTS,ARENA+8192,16,ARENA+4096,576))
        sites=[(pc,count) for pc,target,count in r['service_sites'] if target==ALLOCATE]
        self.assertEqual(sites,[(0x0202f1ec,3),(0x0202f2aa,1)])
        self.assertEqual(len(r['private_events']),1)
        self.assertIn(0x0202a7a8,r['real_calls'])
    def test_fast_produces_wide_signed_delta_from_actual_word_difference(self):
        m=initial(1);put(m,EFFECTS+288,0x80000000)
        def boundary(target,args,vm):
            if target==0x0202cf62:vm.write(args[0]+288,0x7fffffff,4)
            return 0
        r=self.run_case('fast',(0,0,0xffffffd3,7),m,boundary)
        self.assertEqual(r['value'],0);self.assertEqual(get(r['memory'],ROUTES,1),7)
        self.assertEqual(get(r['memory'],ROUTES+3,1),1);self.assertEqual(get(r['memory'],ROUTES+45,1),1)
        self.assertEqual(get(r['memory'],ROUTES+288),0xffffffff//7)
        self.assertEqual(get(r['memory'],ROUTES+128),0x7fffffff)
        self.assertIn(0x0202fa98,r['visited']);self.assertEqual(r['real_calls'].count(0x02032b2e),2)
    def test_free_callback_collision_with_installed_clear_stays_external(self):
        m=initial(5)
        for address,value in ((EFFECTS+84,ARENA+8192),(EFFECTS+88,1),(EFFECTS+324,16),(CONTROL+56,0x0201a9dc)):
            put(m,address,value)
        def boundary(target,args,vm):
            if target==ALLOCATE:vm.write(PRIVATE,0,4);return ARENA+4096
            return 0
        r=self.run_case('commit',(0,0,10),m,boundary)
        self.assertIn((0x0202f2aa,0x0201a9dc,1),r['service_sites'])
        self.assertNotIn(0x0201a9dc,r['real_calls'])
        self.assertEqual(len(r['private_events']),1)
    def test_fast_auxiliary_reference_uses_original_word_index(self):
        m=initial(16);put(m,EFFECTS+292,1<<26)
        def boundary(target,args,vm):
            if target==0x0202cf62:vm.write(args[0]+288+4*5,0x12345678,4)
            return 0
        r=self.run_case('fast',(0,0,1,7),m,boundary)
        self.assertEqual(get(r['memory'],ROUTES+3,1),1)
        self.assertEqual(get(r['memory'],ROUTES+5,1),5)
        self.assertEqual(get(r['memory'],ROUTES+85,1),1)
        self.assertTrue({0x0202fa1a,0x0202fa1c,0x0202f9ae}<=r['visited'])
    def test_fast_produces_float_delta_with_packet_snapshot(self):
        m=initial(7);put(m,EFFECTS+296,0x3f000000)
        def boundary(target,args,vm):
            if target==0x0202cf62:vm.write(args[0]+296,0x3f800000,4)
            return 0
        r=self.run_case('fast',(0,0,1,2),m,boundary)
        self.assertEqual(get(r['memory'],ROUTES+45,1),2)
        self.assertEqual(get(r['memory'],ROUTES+288),0x3e800000)
        self.assertIn(0x0202faac,r['visited'])
    def test_callee_saved_register_mutation_is_rejected(self):
        def boundary(target,args,vm):vm.set('r4',0xdeadbeef);return 0
        with self.assertRaisesRegex(ValueError,'callee-saved'):
            self.run_case('commit',(0,0,0),boundary=boundary)
    def test_full_scene_calls_parameter_fast_without_a_scripted_parameter_result(self):
        m=initial(1);state=0x01c26890;scene=state+11936
        put(m,RAM+8,1,1);put(m,RAM+44,24);put(m,state+280,2);put(m,CONTROL+28,1,1)
        put(m,scene,1,1);put(m,scene+2,1,2);put(m,scene+22,0xffffffe2,2)
        r=self.run_case('scene_inner',(0,),m)
        self.assertIn(REGIONS['fast_wrapper'][0],r['real_calls'])
        self.assertNotIn(REGIONS['fast_wrapper'][0],[t for t,*_ in r['calls']])
        self.assertEqual(get(r['memory'],EFFECTS+70,2),(-30)&65535)
    def test_full_scene_falls_back_to_actual_commit(self):
        m=initial(1);state=0x01c26890;scene=state+11936
        put(m,RAM+8,1,1);put(m,RAM+44,24);put(m,state+280,2);put(m,CONTROL+28,1,1)
        put(m,scene,1,1);put(m,scene+2,1,2);put(m,scene+22,0xffffffe2,2)
        for i in range(8):put(m,CONTROL+210+i,1,1);put(m,ROUTES+448*i+1,1,1)
        r=self.run_case('scene_inner',(0,),m)
        self.assertIn(REGIONS['commit'][0],r['real_calls'])
        self.assertEqual(get(r['memory'],EFFECTS+70,2),(-30)&65535)
    def test_scene_transition_keeps_actual_installed_notification(self):
        m=initial(1);state=0x01c26890;scene=state+11936
        put(m,RAM+8,1,1);put(m,RAM+44,24);put(m,state+280,2);put(m,CONTROL+28,1,1)
        put(m,scene,1,1);put(m,scene+2,1,2);put(m,scene+22,0xffffffe2,2)
        put(m,scene+258,1,1);put(m,scene+256,25,2);put(m,CALLBACKS+732,0x0201a9ea)
        r=self.run_case('scene_inner',(0,),m)
        self.assertTrue(r['real_notifications'])
        self.assertNotIn(0x0201a9ea,[t for t,*_ in r['calls']])
        self.assertEqual(self.program.static_regions['scene_coefficient_selector'],(0x0203a55c,0x0203a566))
        self.assertEqual(self.program.static_regions['scene_initialization_coefficients'],(0x0203a566,0x0203a570))
        self.assertEqual(self.program.static_regions['scene_gain_table'],(0x02033bc8,0x02033c8c))
        self.assertFalse(any(a<=0x01c1f7f0<b for a,b in self.program.static_regions.values()))
    def test_real_stage_consumes_parameter_produced_record(self):
        m=initial(1)
        def boundary(target,args,vm):
            if target==0x0202cf62:vm.write(args[0]+288,700,4)
            return 0
        r=self.run_case('fast',(0,0,0xffffffd3,7),m,boundary)
        m=list(map(bytearray,r['memory']))
        for i in range(6):put(m,CONTROL+180+i,255,1)
        put(m,CONTROL+20,1,1);put(m,CONTROL+21,2,1)
        put(m,CONFIG+28+6,1,1);put(m,CONFIG+28+7,2,1);put(m,CONFIG+28+40,0x01c341c4)
        r=self.run_case('stage',(0,SAMPLES,128),m)
        self.assertEqual(get(r['memory'],EFFECTS+288),100)
        self.assertEqual(get(r['memory'],ROUTES,1),6)
        self.assertIn(0x01c10e06,r['visited'])
        m=list(map(bytearray,r['memory']));put(m,CONTROL+14,1,1);put(m,CONTROL+348,0,1);put(m,EFFECTS+1,1,1)
        r=self.run_case('stage',(0,SAMPLES,128),m)
        self.assertEqual(get(r['memory'],EFFECTS+288),200)
        self.assertIn(0x01c0f678,r['real_calls'])
    def test_scene_alternate_notification_collision_retains_one_argument(self):
        for token in (0x0202f07e,0x0202fba6,0x020305f8):
            m=initial(1);state=0x01c26890;scene=state+11936
            put(m,RAM+8,1,1);put(m,RAM+44,24);put(m,state+280,2);put(m,CONTROL+28,1,1)
            put(m,scene,1,1);put(m,scene+2,1,2);put(m,scene+22,0xffffffe2,2)
            put(m,scene+258,1,1);put(m,scene+256,25,2);put(m,CALLBACKS+732,token)
            r=self.run_case('scene_inner',(0,),m)
            self.assertIn((0x02028a9e,token,1),r['service_sites'])
            event=next(row for row,site in zip(r['calls'],r['service_sites']) if site[0]==0x02028a9e)
            self.assertEqual(event[1],(25,)+(0,)*11)
            self.assertFalse(r['real_notifications'])

if __name__=='__main__':unittest.main()
