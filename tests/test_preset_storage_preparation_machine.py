"""Independent native witnesses for pair storage and discovery contracts."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from verify_preset_storage_preparation import (PresetStoragePreparationProgram,Script,initial,STATE,
 GLOBAL,INPUT,OTHER,READ,PROGRAM,ERASE,ALLOCATE,HEAP,FLASH,FLASH_BYTES,record,
 setword,getword,write_data,populated_flash,pending_flash,block,check_derivatives)

class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=PresetStoragePreparationProgram()
    def run_native(self,name,args=(),memory=None,**options):
        script=Script(**options);result=self.program.execute(memory or initial(),name,args,script)
        return result,script
    def test_complete_closure(self):
        self.assertEqual(len(self.program.code),940);self.assertEqual(len(self.program.service_sites),28)
    def test_exact_frozen_derivatives(self):
        self.assertEqual(check_derivatives()['bodies'],['invalidate','write','erase'])
    def test_cached_prepare_calls_nothing(self):
        result,script=self.run_native('prepare');self.assertEqual(script.events,[]);self.assertEqual(result['result'],(0,0))
    def test_native_invalid_pair_precedes_io(self):
        for args in ((16,INPUT,0,OTHER,0),(0,INPUT,1921,OTHER,0),(0,INPUT,0,OTHER,1921)):
            result,script=self.run_native('replace_pair',args)
            self.assertEqual(result['result'],(0xffffffff,0));self.assertEqual(script.events,[])
    def test_short_record_still_writes_full_header(self):
        memory=initial();write_data(memory,INPUT,record(1))
        _,script=self.run_native('ordered_write',(FLASH,INPUT,1),memory)
        chunks=[e['args'][2:4] for e in script.events if e['target']==PROGRAM]
        self.assertEqual(chunks,[(36,FLASH+4),(4,FLASH)])
    def test_zero_record_calls_nothing(self):
        result,script=self.run_native('ordered_write',(FLASH,0,0));self.assertEqual(result['result'],(0,0));self.assertFalse(script.events)
    def test_pair_publication_follows_readback(self):
        result,script=self.run_native('replace_pair',(0,0,0,0,0))
        self.assertEqual(getword(result['memory'],STATE+3476,1),1)
        self.assertEqual(getword(result['memory'],STATE+3441,1),3)
        self.assertEqual(script.events[-1]['target'],READ)
    def test_two_failed_attempts_do_not_publish_pair(self):
        result,script=self.run_native('replace_pair',(0,0,0,0,0),returns={READ:1})
        self.assertEqual(result['result'],(0xfffffffd,0));self.assertEqual(getword(result['memory'],STATE+3476,1),255)
        self.assertEqual(getword(result['memory'],STATE+3441,1),2);self.assertEqual(getword(result['memory'],STATE+3442,1),2)
    def test_erase_ignored_result_then_verifies(self):
        memory=initial();setword(memory,STATE+3458,2,1)
        result,_=self.run_native('erase_block',(0,),memory,flash=bytes([0])*FLASH_BYTES,returns={ERASE:7})
        self.assertEqual(result['result'],(0xfffffffe,0));self.assertEqual(getword(result['memory'],STATE+3440,1),5)
    def test_erase_strike_byte_wrap(self):
        memory=initial();setword(memory,STATE+3458,255,1)
        result,_=self.run_native('erase_block',(0,),memory,flash=bytes([0])*FLASH_BYTES,returns={ERASE:7})
        self.assertEqual(getword(result['memory'],STATE+3458,1),0)
    def test_factory_pair_footer(self):
        result,_=self.run_native('prepare',memory=initial(False),flash=populated_flash())
        self.assertEqual([getword(result['memory'],STATE+3476+i,1) for i in range(16)],list(range(16)))
    def test_bad_footer_does_not_overwrite_callback(self):
        flash=populated_flash();flash[4092:4096]=bytes(4)
        result,_=self.run_native('prepare',memory=initial(False),flash=flash,mutations=((READ,0,STATE+3440,5,1),))
        self.assertEqual(getword(result['memory'],STATE+3440,1),5)
    def test_pending_recovery_marks_journal_only_after_success(self):
        result,script=self.run_native('prepare',memory=initial(False),flash=pending_flash())
        self.assertEqual(getword(result['memory'],STATE+3457,1),2)
        self.assertEqual(script.flash[0xdeff8-FLASH:0xdeffc-FLASH],bytes(4))
    def test_failed_allocation_keeps_prepared_flag_clear(self):
        result,_=self.run_native('prepare',memory=initial(False),returns={ALLOCATE:0})
        self.assertEqual(getword(result['memory'],STATE+712,1),0)
        self.assertEqual(getword(result['memory'],STATE+716,1),1)
    def test_invalidation_only_clears_checked_bit(self):
        memory=initial();setword(memory,STATE+708,0xffffffff);setword(memory,STATE+732,0xa5a5a5a5)
        result,_=self.run_native('invalidate',(31,),memory)
        self.assertEqual(getword(result['memory'],STATE+708),0x7fffffff)
        self.assertEqual(getword(result['memory'],STATE+732),0xa5a5a5a5)
    def test_zero_rate_elapsed_is_zero(self):
        memory=initial();setword(memory,GLOBAL+44,0);setword(memory,STATE+712,0,1)
        for i in range(16):setword(memory,STATE+3476+i,i,1)
        _,script=self.run_native('prepare',memory=memory)
        self.assertEqual(script.events[-1]['args'][2],0)

if __name__=='__main__':unittest.main()
