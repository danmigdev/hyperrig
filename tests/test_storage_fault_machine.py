"""Independent diagnostic-format, alias, event and fatal-observation checks."""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from storage_fault_machine import *
from verify_storage_fault import Script,initial,setword,getword,packed_metadata

class FaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=StorageFaultProgram()
    def native(self,name,args=(),memory=None,cpu=(0,0x300),caller=INCOMING[1],events=10000,**options):
        fixture=Script(**options)
        result=self.program.execute(initial() if memory is None else memory,name,args,cpu,caller,fixture.event,events)
        return result,fixture
    def test_complete_registry_and_incoming_width(self):
        self.assertEqual((len(REGIONS),sum(b-a for a,b in REGIONS.values()),len(self.program.code)),(15,902,332))
        self.assertEqual(len(DIRECT_SITES),24);self.assertEqual(INCOMING[1]-INCOMING[0],4)
        self.assertEqual(INCOMING[1],0x02002b7e)
    def test_changed_primary_record_is_rejected(self):
        p=copy.copy(self.program);p.isa_records=copy.deepcopy(p.isa_records)
        p.isa_records[hex(0x01c00e92)]['notes']='changed'
        with self.assertRaises(ValueError):validate_cpu_evidence(p)
    def test_tags_match_twelve_bits_only(self):
        for word,expected in ((0xa5e00000,1),(0xa5efffff,1),(0xd06fffff,1),(0xe7cfffff,1),(0xa5ffffff,0)):
            r,_=self.native('tag',(word,));self.assertEqual(r['result'],(expected,0))
    def test_bad_count_header_is_native_zero(self):
        for word in (0,0xc7a40001,0xc7a50003,0xc7a5ffff):
            m=initial();setword(m,HEADER,word);r,_=self.native('record_count',memory=m)
            self.assertEqual(r['result'],(0,0));self.assertEqual(r['memory'],tuple(map(bytes,m)))
    def test_invalid_record_does_not_modify_history(self):
        m=initial();setword(m,CURRENT,0);r,_=self.native('append',(CURRENT,),m)
        self.assertEqual(r['memory'],tuple(map(bytes,m)))
    def test_duplicate_first_record_does_not_move_second(self):
        m=initial();setword(m,HEADER,0xc7a50002);setword(m,RECORDS,0xa5e00123)
        r,_=self.native('append',(RECORDS,),m);self.assertEqual(r['memory'],tuple(map(bytes,m)))
    def test_second_record_source_is_reread_after_shift(self):
        m=initial();setword(m,HEADER,0xc7a50002)
        for i in range(6):setword(m,RECORDS+4*i,0xa5e00000+i);setword(m,RECORDS+24+4*i,0xd0600000+i)
        r,_=self.native('append',(RECORDS+24,),m)
        for i in range(6):
            self.assertEqual(getword(r['memory'],RECORDS+4*i),0xa5e00000+i)
            self.assertEqual(getword(r['memory'],RECORDS+24+4*i),0xa5e00000+i)
    def test_decode_writes_only_eleven_bytes(self):
        m=initial();packed_metadata(m,(1,2,3,4),5,0x650f,0x12345678)
        old=getword(m,0x3300000c,1);r,_=self.native('decode',(0x33000001,),m)
        self.assertEqual(r['result'],(1,0));self.assertEqual(getword(r['memory'],0x33000001),0x12345678)
        self.assertEqual([getword(r['memory'],0x33000005+i,1) for i in range(7)],[1,2,3,4,5,15,0x65])
        self.assertEqual(getword(r['memory'],0x3300000c,1),old)
    def test_decode_null_still_validates_but_does_not_write(self):
        m=initial();packed_metadata(m);r,_=self.native('decode',(0,),m)
        self.assertEqual(r['result'],(1,0));self.assertEqual(r['memory'],tuple(map(bytes,m)))
    def test_checksum_and_high_tail_nibble_are_both_checked(self):
        for which in (0,1):
            m=initial();packed_metadata(m,tail=16 if which else 1)
            if not which:setword(m,METADATA,getword(m,METADATA)^1)
            r,_=self.native('decode',(0x33000001,),m);self.assertEqual(r['result'],(0,0))
            self.assertEqual(r['memory'],tuple(map(bytes,m)))
    def test_encoder_caps_mode_and_masks_counter_nibbles(self):
        m=initial()
        for i in range(11):setword(m,0x33000001+i,255,1)
        r,_=self.native('encode',(0x33000001,),m)
        self.assertEqual(getword(r['memory'],METADATA),0xffffffff)
        self.assertEqual(getword(r['memory'],METADATA+4),0x05ffffff)
    def test_update_saturates_selected_counter(self):
        for kind,alternate,offset in ((1,0,4),(2,0,5),(0,0,6),(1,1,7)):
            m=initial();packed_metadata(m,(254,254,14,14))
            r,_=self.native('update',(kind,alternate),m)
            z,_=self.native('decode',(0x33000001,),r['memory'])
            self.assertEqual(getword(z['memory'],0x33000001+offset,1),255 if offset<6 else 15)
            again,_=self.native('update',(kind,alternate),r['memory'])
            self.assertEqual(again['memory'],r['memory'])
    def test_once_sets_flag_even_when_metadata_is_invalid(self):
        m=initial();r,_=self.native('once',(1,),m)
        self.assertEqual(getword(r['memory'],STATE+8,1),1)
        self.assertEqual(getword(r['memory'],METADATA),0)
        again,_=self.native('once',(2,),r['memory']);self.assertEqual(again['memory'],r['memory'])
    def test_lock_branch_uses_old_bit_two_only(self):
        for old,expected_calls in ((1,1),(4,2),(5,2),(15,2)):
            m=initial();setword(m,LOCK,old,1)
            r,s=self.native('acquire',memory=m,mutations=(((TESTSET,LOCK),0,LOCK,0,1),))
            self.assertEqual(sum(e[0]==TESTSET for e in s.actions),expected_calls)
            self.assertEqual(getword(r['memory'],IRQ_COUNTS),1);self.assertEqual(r['cpu'][1],0x100)
    def test_event_stop_precedes_testset_store(self):
        r,s=self.native('acquire',events=4)
        self.assertEqual(r['status'],-203);self.assertEqual(getword(r['memory'],LOCK,1),0)
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),1);self.assertFalse(any(e[0]==TESTSET for e in s.actions))
    def test_underflow_keeps_interrupts_disabled(self):
        r,s=self.native('release',cpu=(0,0x100))
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),0xffffffff)
        self.assertEqual(r['cpu'][1],0x100);self.assertFalse(any(e[0]==STI for e in s.actions))
    def test_raw_core_wrap_preserves_address_arithmetic(self):
        r,_=self.native('acquire',cpu=(0x40000000,0x300))
        self.assertEqual(getword(r['memory'],IRQ_COUNTS),1)
    def test_private_counter_is_rejected_after_cli(self):
        number=((STACK-24-IRQ_COUNTS)&0xffffffff)>>2
        r,s=self.native('acquire',cpu=(number,0x300))
        self.assertEqual(r['status'],-202);self.assertEqual(r['cpu'][1],0x100)
        self.assertEqual([e[0] for e in s.actions],[CLI,CNUM])
    def test_register_write_forwards_raw_words(self):
        r,s=self.native('write_register',(0xffff1234,0xfedcba98))
        self.assertEqual(r['status'],0)
        self.assertEqual([e[3] for e in s.actions if e[:2]==(WRITE,DATA)],[2,0xffff0034,0xfedcba98])
    def test_signed_identifier_selects_control_path(self):
        _,positive=self.native('read_register',(0x7fff,));_,negative=self.native('read_register',(0x8000,))
        self.assertEqual(sum(e[:2]==(WRITE,CONTROL) for e in positive.actions),6)
        self.assertEqual(sum(e[:2]==(WRITE,CONTROL) for e in negative.actions),5)
    def test_zero_width_mask_uses_native_shift_modulo32(self):
        for width in (0,32):
            _,s=self.native('masked_register',(160,4,width,0xffffffff),returns={(READ,DATA):0x21})
            self.assertEqual([e[3] for e in s.actions if e[:2]==(WRITE,DATA)][-1],0x21)
    def test_fatal_archives_old_record_and_never_returns(self):
        m=initial();packed_metadata(m);setword(m,CURRENT,0xd0600123);setword(m,STATE+104,0x800)
        r,s=self.native('fatal',memory=m,caller=0xffffffff)
        self.assertEqual((r['status'],r['result'],r['stop_pc']),(1,None,HALT))
        self.assertEqual(getword(r['memory'],RECORDS),0xd0600123)
        self.assertEqual(getword(r['memory'],CURRENT),0xa5e00800)
        self.assertEqual(getword(r['memory'],CURRENT+12),0x07fffffe)
        self.assertEqual(getword(r['memory'],CURRENT+20),0x87654321)
        self.assertEqual(s.actions[0][:4],(RETS,0,4,0x07fffffe))
    def test_fatal_cpu_and_rets_event_mutations_precede_archive(self):
        r,_=self.native('fatal',mutations=(((RETS,0),0,CURRENT,0xe7c01234,4),))
        self.assertEqual(getword(r['memory'],RECORDS),0xe7c01234)
    def test_callback_cannot_borrow_active_private_buffer(self):
        r,s=self.native('fatal',probes=(((RETS,0),0,STACK-24,1,0),))
        self.assertEqual(r['status'],-202);self.assertEqual(len(s.actions),1);self.assertIsNone(r['result'])
    def test_event_callback_cannot_mutate_cpu_context(self):
        def wrong(op,a,n,v,m):m.cpu[0]=1;return 0
        with self.assertRaises(ValueError):self.program.execute(initial(),'fatal',events=wrong)

if __name__=='__main__':unittest.main()
