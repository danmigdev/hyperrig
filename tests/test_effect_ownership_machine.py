"""Focused original-instruction ownership, alias and partial-prefix witnesses."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from effect_ownership_machine import EffectOwnershipProgram, REGIONS, REUSED, MAPPED
from verify_effect_ownership import initial,setword,routes,Script,EFFECT,CONTROL,OUT,OLD,NEW,RELEASE,REPLACEMENT


class OwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=EffectOwnershipProgram()
    def run_case(self,name,args=(),memory=None,mutations=(),stop=False):
        return self.program.execute(memory or initial(),name,args,Script(mutations=mutations),stop_extra_overread=stop)
    def word(self,r,address,size=4):
        for (base,n),data in zip(MAPPED,r['memory']):
            if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
        raise AssertionError('unmapped test read')
    def test_complete_region_scope(self):
        self.assertEqual(sum(b-a for a,b in REGIONS.values()),668)
        self.assertEqual(len(self.program.code),264)
    def test_lookup_first_duplicate_and_output_alias(self):
        m=initial();routes(m,(2,0,3,0),(0,4))
        r=self.run_case('lookup',(0,CONTROL+14),m)
        self.assertEqual(r['result'],(0,0));self.assertEqual(self.word(r,CONTROL+14),1)
    def test_lookup_null_output_uses_original_second_return(self):
        m=initial();routes(m,(),(3,0))
        r=self.run_case('lookup',(0,0),m)
        self.assertEqual(r['result'],(1,0));self.assertIn(0x0202de8a,r['visited'])
    def test_lookup_does_not_write_when_absent(self):
        r=self.run_case('lookup',(257,OUT))
        self.assertEqual(r['result'],(0xffffffff,0));self.assertEqual(self.word(r,OUT),0xa5a5a5a5)
    def test_neighbors_use_caller_chain_after_other_chain_lookup(self):
        m=initial();routes(m,(1,0,2),(3,4,5))
        setword(m,EFFECT+480*3+4,128,1);setword(m,EFFECT+480*5+4,2,1)
        r=self.run_case('neighbors',(1,0),m)
        self.assertEqual(self.word(r,EFFECT+4,1),128)
    def test_detach_removes_only_first_duplicate(self):
        m=initial();routes(m,(2,0,3,0),(0,4))
        r=self.run_case('detach',(0,),m)
        self.assertEqual(self.word(r,CONTROL+14,1),3)
        self.assertEqual([self.word(r,CONTROL+348+i,1) for i in range(3)],[2,3,0])
        self.assertEqual(self.word(r,CONTROL+15,1),2)
    def test_group_count_counts_runs_of_nonzero_flags(self):
        m=initial();routes(m,range(8),())
        for i,value in enumerate((1,128,0,255,0,2,3,4)):setword(m,EFFECT+480*i+4,value,1)
        self.assertEqual(self.run_case('groups',(0,),m)['result'],(3,0))
    def test_route_count_255_is_preserved(self):
        m=initial();routes(m,[i%2 for i in range(255)],());setword(m,EFFECT+4,1,1)
        self.assertEqual(self.run_case('groups',(0,),m)['result'],(128,0))
    def test_cached_pointers_survive_mutations(self):
        r=self.run_case('release',(EFFECT,),mutations=((RELEASE,0,EFFECT+7,0,1),
            (RELEASE,0,EFFECT+92,NEW,4)))
        self.assertEqual([x[1][0] for x in r['calls']],[OLD,OLD+512,OLD+576,OLD+640])
        self.assertEqual(self.word(r,EFFECT+92),NEW)
    def test_callback_reloads_zero_token_without_skipping(self):
        r=self.run_case('release',(EFFECT,),mutations=((RELEASE,0,CONTROL+56,0,4),))
        self.assertEqual([x[0] for x in r['calls']],[RELEASE,0,0,0])
        self.assertEqual([x[2] for x in r['service_sites']],[1,1,1,1])
    def test_callbacks_colliding_with_recovered_entries_remain_external(self):
        for target,_ in (REGIONS|REUSED).values():
            m=initial();setword(m,CONTROL+56,target)
            r=self.run_case('release',(EFFECT,),m)
            self.assertEqual([x[0] for x in r['calls']],[target]*4)
            self.assertEqual(r['internal_calls'],[])
    def test_missing_initial_callback_skips_large_extra_count(self):
        m=initial();setword(m,EFFECT+7,255,1);setword(m,CONTROL+56,0)
        r=self.run_case('release',(EFFECT,),m)
        self.assertEqual(r['status'],0);self.assertFalse(r['calls'])
        self.assertEqual(self.word(r,EFFECT+7,1),0)
    def test_lazy_fourth_read_stops_after_three_extra_callbacks(self):
        m=initial();setword(m,EFFECT+7,4,1)
        r=self.run_case('release',(EFFECT,),m,stop=True)
        self.assertEqual(r['status'],-202);self.assertEqual(r['stop_pc'],0x0202df8a)
        self.assertEqual(len(r['calls']),4);self.assertEqual(self.word(r,EFFECT+84),0)
    def test_full_remove_retains_later_ir_fields_at_guard(self):
        m=initial();setword(m,EFFECT+7,255,1)
        r=self.run_case('remove',(0,),m,stop=True)
        self.assertEqual(r['status'],-202);self.assertEqual(self.word(r,EFFECT+48),OLD+256)
        self.assertEqual(self.word(r,EFFECT+2,1),0)
    def test_capture_signed_division_and_shift_index(self):
        for offset,expected in ((-1,254),(-888,255),(888*32,254),(888*7,127)):
            m=initial();setword(m,EFFECT+288,(0x01c2fa38+offset)&0xffffffff)
            r=self.run_case('capture',(EFFECT,),m)
            self.assertEqual(self.word(r,CONTROL+6,1),expected);self.assertEqual(self.word(r,EFFECT+288),0)
    def test_remove_clears_all_queue_duplicates_after_one_route_duplicate(self):
        m=initial();routes(m,(0,1,0),(0,2));setword(m,CONTROL+8,5,1)
        for i,value in enumerate((0,1,0,2,0)):setword(m,CONTROL+88+i,value,1)
        r=self.run_case('remove',(0,),m)
        self.assertEqual(self.word(r,CONTROL+8,1),2)
        self.assertEqual([self.word(r,CONTROL+88+i,1) for i in range(2)],[1,2])
        self.assertEqual([self.word(r,CONTROL+348+i,1) for i in range(2)],[1,0])
    def test_later_ir_and_capture_fields_reload_after_callbacks(self):
        r=self.run_case('remove',(0,),mutations=((RELEASE,0,EFFECT+48,NEW,4),
            (RELEASE,0,EFFECT,31,1),(RELEASE,0,EFFECT+288,0x01c2fa38+1776,4)))
        self.assertEqual(r['calls'][-1][1][0],NEW)
        self.assertEqual(self.word(r,EFFECT+48),0);self.assertEqual(self.word(r,EFFECT+288),0)
        self.assertEqual(self.word(r,CONTROL+6,1),251)
    def test_invalid_and_repeated_remove_still_increment_counter(self):
        first=self.run_case('remove',(0,))
        second=self.run_case('remove',(0,),first['memory'])
        self.assertEqual(first['result'],(0,0));self.assertEqual(second['result'],(0xffffffff,0))
        self.assertEqual(self.word(second,0x01c34468),2)
    def test_refresh_is_a_one_word_direct_service(self):
        r=self.run_case('refresh')
        self.assertEqual(r['calls'][0][0],0x02028eb2);self.assertEqual(r['calls'][0][1],(0,)*12)
        self.assertEqual(r['service_sites'],[(0x0202ec4e,0x02028eb2,1)])
    def test_public_native_argument_domain(self):
        with self.assertRaises(ValueError):self.program.execute([], 'remove',(0,))
        with self.assertRaises(ValueError):self.program.execute(initial(),'lookup',(0,))
        with self.assertRaises(ValueError):self.program.execute(initial(),'remove',(-1,))


if __name__=='__main__':unittest.main()
