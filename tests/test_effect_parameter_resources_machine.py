"""Focused original-body witnesses for resource ownership and history semantics."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_parameter_resources_machine import EffectParameterResourcesProgram,REGIONS,MAPPED,STATIC,TABLES
from verify_effect_parameter_resources import initial,setword,Script,EFFECT,CONTROL,CALLBACKS,OLD,NEW,SOURCE,OUT,ALLOCATOR,RELEASE,MODE

def read(memory,address,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
    raise ValueError('unmapped expected word')

class Resources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectParameterResourcesProgram()
    def run_case(self,name,args=(),memory=None,returns=None,mutations=()):
        return self.program.execute(initial() if memory is None else memory,name,args,Script(returns,mutations))
    def test_complete_body_and_table_counts(self):
        self.assertEqual(len(REGIONS),19)
        new={pc for pc in self.program.code if any(a<=pc<b for a,b in REGIONS.values())}
        self.assertEqual(len(new),579)
        self.assertTrue(all(not any(a<=pc<b for a,b in TABLES.values()) for pc in new))
        self.assertEqual(sum(b-a for a,b in TABLES.values()),48)
    def test_extra_size_constant(self):self.assertEqual(self.run_case('extra_size')['result'],(56480,0))
    def test_read_signed_halfword_and_masked_exponent(self):
        m=initial();setword(m,OLD,0xffff,2);setword(m,OLD+32,255,1)
        self.assertEqual(self.run_case('decode_sample',(OLD,16,0),m)['result'][0],0x80000000)
    def test_read_address_wrap_between_accesses(self):
        m=initial();setword(m,0xfffffffe,0x8001,2);setword(m,0,4,1)
        self.assertEqual(self.run_case('decode_sample',(0xfffffffe,1,0),m)['result'][0],0xfff80010)
    def test_read_cannot_cross_address_wrap(self):
        with self.assertRaisesRegex(ValueError,'address wrap'):
            self.run_case('decode_sample',(0xffffffff,0,0))
    def test_zero_group_preserves_other_exponent_lanes(self):
        m=initial()
        for i in range(16):setword(m,SOURCE+4*i,0)
        out=self.run_case('encode_group',(OLD,64,2,SOURCE),m)['memory']
        self.assertEqual(read(out,OLD+128),0xa700a7a7)
        self.assertEqual(read(out,OLD+64),0)
        self.assertEqual(read(out,OLD+96),0xa7a7a7a7)
    def test_positive_rounding_wrap_is_retained(self):
        m=initial()
        for i in range(16):setword(m,SOURCE+4*i,0x7fffffff)
        out=self.run_case('encode_group',(OLD,16,0,SOURCE),m)['memory']
        self.assertEqual(read(out,OLD),0x80008000)
        self.assertEqual(read(out,OLD+32,1),16)
    def test_negative_full_scale_remains_exact(self):
        m=initial()
        for i in range(16):setword(m,SOURCE+4*i,0x80000000)
        out=self.run_case('encode_group',(OLD,16,0,SOURCE),m)['memory']
        self.assertEqual(read(out,OLD),0x80008000)
        self.assertEqual(read(out,OLD+32,1),16)
    def test_migration_joins_ring_and_pending_tail(self):
        m=initial();setword(m,EFFECT+288,5)
        for i in range(32):setword(m,OLD+2*i,i,2)
        for i in range(2):setword(m,OLD+64+i,0,1)
        for i in range(5):setword(m,EFFECT+328+4*i,100+i)
        out=self.run_case('migrate',(EFFECT,OLD,32,NEW,64),m)
        self.assertEqual([read(out['memory'],NEW+2*i,2) for i in range(32)],list(range(5,32))+list(range(100,105)))
        self.assertEqual(read(out['memory'],EFFECT+288),32)
        self.assertEqual(out['internal_calls'].count(REGIONS['encode_group'][0]),2)
    def test_incomplete_group_is_not_written(self):
        m=initial();setword(m,EFFECT+288,0)
        out=self.run_case('migrate',(EFFECT,OLD,15,NEW,64),m)
        self.assertEqual(read(out['memory'],NEW),0xa7a7a7a7)
        self.assertNotIn(REGIONS['encode_group'][0],out['internal_calls'])
        self.assertEqual(read(out['memory'],EFFECT+288),15)
    def test_zero_count_needs_no_sample_buffers(self):
        out=self.run_case('migrate',(EFFECT,0xdead0000,0,0xdead8000,0))
        self.assertEqual(read(out['memory'],EFFECT+288),0)
        self.assertEqual(out['internal_calls'],[])
    def test_allocated_trailer_and_request_size(self):
        out=self.run_case('allocate',(7,),returns={ALLOCATOR:NEW})
        self.assertEqual(out['calls'][0][1][0],23)
        self.assertEqual([read(out['memory'],NEW+7+4*i) for i in range(4)],
            [0xc0de5eed^i for i in range(4)])
    def test_allocator_failure_without_release_retains_old_buffer(self):
        m=initial();setword(m,CONTROL+56,0)
        out=self.run_case('allocate_delay',(EFFECT,256,OUT),m)
        self.assertEqual(read(out['memory'],EFFECT+84),OLD)
        self.assertEqual(read(out['memory'],OUT),0)
        self.assertEqual(len(out['calls']),1)
    def test_release_publishes_null_before_callback(self):
        out=self.run_case('allocate_delay',(EFFECT,256,OUT),returns={ALLOCATOR:(0,NEW)})
        free=next(event for event in out['calls'] if event[0]==RELEASE)
        self.assertEqual(free[1][0],OLD)
        self.assertEqual(read(free[2],EFFECT+84),0)
        self.assertEqual(read(free[2],EFFECT+88),0)
        self.assertEqual(read(out['memory'],OUT),1)
        self.assertEqual(out['result'][0],NEW)
    def test_failed_growth_restores_cleared_old_capacity(self):
        out=self.run_case('allocate_delay',(EFFECT,256,OUT),returns={ALLOCATOR:(0,0,0,OLD)})
        self.assertEqual(out['result'][0],0)
        self.assertEqual(read(out['memory'],EFFECT+84),OLD)
        self.assertEqual(read(out['memory'],EFFECT+88),128)
        self.assertEqual(read(out['memory'],OLD),0)
        self.assertEqual(read(out['memory'],OUT),1)
    def test_total_allocation_failure_disables_only_native_flags(self):
        m=initial();setword(m,EFFECT+5,1,1)
        out=self.run_case('allocate_delay',(EFFECT,256,OUT),m)
        self.assertEqual(read(out['memory'],EFFECT+1,1),0)
        self.assertEqual(read(out['memory'],EFFECT+5,1),0)
        self.assertEqual(read(out['memory'],EFFECT+2,1),1)
    def test_free_token_collision_is_one_argument_service(self):
        m=initial();setword(m,CONTROL+56,0x0201a9dc)
        out=self.run_case('allocate_delay',(EFFECT,256,OUT),m,{ALLOCATOR:(0,NEW)})
        site=next(event for event in out['service_sites'] if event[0]==0x0202edfc)
        self.assertEqual(site,(0x0202edfc,0x0201a9dc,1))
        self.assertNotIn(0x0201a9dc,out['internal_calls'])
    def test_mode_callback_collision_is_one_argument_service(self):
        m=initial();setword(m,0x01c34458,0x0201a9dc)
        out=self.run_case('mode_callback',(7,),m)
        self.assertEqual(out['service_sites'],[(0x01c05ed2,0x0201a9dc,1)])
    def test_flush_reloads_count_and_slot_after_callback(self):
        m=initial();setword(m,CONTROL+8,1,1);setword(m,CONTROL+88,3,1)
        out=self.run_case('flush',memory=m,mutations=((0x0202eb4c,0,CONTROL+8,2,1),(0x0202eb4c,0,CONTROL+89,7,1)))
        self.assertEqual([call[1][0] for call in out['calls']],[3,7])
        self.assertEqual(read(out['memory'],CONTROL+8,1),0)
    def test_extra_state_fields_and_original_clear(self):
        out=self.run_case('allocate_extra',(EFFECT,),returns={ALLOCATOR:NEW})
        self.assertEqual(read(out['memory'],EFFECT+92),NEW)
        self.assertEqual(read(out['memory'],EFFECT+104,2),14120)
        self.assertEqual(read(out['memory'],EFFECT+7,1),1)
        self.assertIn(0x02033412,out['internal_calls'])
    def test_type39_parallel_threshold_reads_original_field(self):
        m=initial();setword(m,EFFECT,39,1);setword(m,EFFECT+412,0);setword(m,EFFECT+416,1)
        setword(m,EFFECT+352,4136)
        self.assertEqual(self.run_case('fingerprint',(EFFECT,),m)['result'][0],3)
        setword(m,EFFECT+352,0xffffffff)
        self.assertEqual(self.run_case('fingerprint',(EFFECT,),m)['result'][0],1)
    def test_type25_fingerprint_does_not_merge_active_bit(self):
        m=initial();setword(m,EFFECT,25,1);setword(m,EFFECT+420,100,1);setword(m,EFFECT+421,3,1)
        out=self.run_case('fingerprint',(EFFECT,),m)
        self.assertEqual(out['result'][0],7)
        self.assertNotIn(0x01c055d2,out['internal_calls'])
    def test_mode_preserves_neighbors_and_clears_derived_state(self):
        m=initial();setword(m,EFFECT,3,1)
        for i in range(70,330):setword(m,EFFECT+i,0x5a,1)
        out=self.run_case('change_mode',(EFFECT,2),m)['memory']
        self.assertEqual(read(out,EFFECT+111,1),0x5a)
        self.assertEqual(read(out,EFFECT+112),0)
        self.assertEqual(read(out,EFFECT+284),0)
        self.assertEqual(read(out,EFFECT+288),0x5a5a5a5a)
        self.assertEqual(read(out,EFFECT+308),0)
        self.assertEqual(read(out,EFFECT+6,1),2)
    def test_ir_state_global_is_raw_word(self):
        m=initial();setword(m,EFFECT+288,0);setword(m,0x01c1f7d0,0x12345678)
        self.assertEqual(self.run_case('ir_state',(EFFECT,),m)['result'][0],0x12345678)
    def test_ir_direct_length_uses_stack_budget(self):
        m=initial();setword(m,EFFECT+48,OLD);setword(m,EFFECT+52,4096);setword(m,EFFECT+56,0);setword(m,EFFECT+68,0,1)
        self.assertEqual(self.run_case('ir_length',(EFFECT,1,1),m)['result'][0],128)
        self.assertEqual(self.run_case('ir_length',(EFFECT,0,1),m)['result'][0],64)

if __name__=='__main__':unittest.main()
