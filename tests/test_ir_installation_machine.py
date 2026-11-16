"""Hand-checked IR numerical, ownership and read-failure expectations."""
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
AVAILABLE=(ROOT/'analysis/firmware/m571_g_app/app.bin').is_file() and (ROOT/'upstream/pi32v2-isa/pi32v2isa').is_dir()

@unittest.skipUnless(AVAILABLE,'bootstrap and analyze the pinned firmware first')
class IrInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'tools'))
        from ir_installation_machine import IrInstallationProgram
        from verify_ir_installation import baseline,read_script,Reads,Script,load_reads,record
        cls.program=IrInstallationProgram()
        cls.initial,cls.read_script,cls.load_reads,cls.record=map(staticmethod,(baseline,read_script,load_reads,record))
        cls.Reads,cls.Script=Reads,Script

    def execute(self,operation,*args,memory=None,reads=(),plan=None,stack_byte=0xA7):
        source=self.Reads(reads)
        result=self.program.execute(memory or self.initial(),operation,*args,reader=source.read,
            boundary=self.Script(plan),stack_byte=stack_byte)
        self.assertEqual(len(source.requests),len(reads))
        return result,source.requests
    @staticmethod
    def word(data,offset=0): return struct.unpack_from('<I',data,offset)[0]
    def trim(self,samples):
        from ir_installation_machine import HEAP
        return self.execute('trim',HEAP,len(samples),memory=self.initial(samples))[0]['result']

    def test_null_samples_keep_count_without_reading(self):
        self.assertEqual(self.execute('trim',0,0xFFFFFFFF)[0]['result'],0xFFFFFFFF)
    def test_empty_and_silent_samples_keep_count(self):
        self.assertEqual(self.trim([]),0);self.assertEqual(self.trim([0]*4076),4076)
    def test_trailing_zeroes_trim_to_last_impulse(self):
        self.assertEqual(self.trim([0,0,32767,0,0]),3)
    def test_full_scale_negative_sample_has_unsigned_absolute_32768(self):
        self.assertEqual(self.trim([-32768]+[0]*128),1)
    def test_64_bit_energy_carries_above_four_billion(self):
        self.assertEqual(self.trim([32767]*8+[0]*32),8)
    def test_peak_threshold_equality_is_removed(self):
        self.assertEqual(self.trim([31620,10]),1);self.assertEqual(self.trim([31619,10]),2)
    def test_cumulative_tail_energy_stops_at_first_excess(self):
        self.assertEqual(self.trim([32767]+[1]*1100),78)
    def test_gain_zero_is_binary32_one_and_metadata_is_signed(self):
        zero=self.execute('configure',0,4,0,1)[0]
        self.assertEqual(self.word(zero['memory'][18]),0x3F800000)
        low=self.execute('configure',0,4,(-60000)&0xFFFFFFFF,0)[0]['memory'][18]
        clamped=self.execute('configure',0,4,0x80000000,0)[0]['memory'][18]
        self.assertEqual(low,clamped)
        self.assertLess(self.word(low),0x3F800000)
    def test_configure_clears_deferred_identity_and_preserves_unowned_bytes(self):
        from ir_installation_machine import HEAP
        memory=self.initial([32767,0,0]);old=bytes(memory[15])
        result,_=self.execute('configure',HEAP,3,0,255,memory=memory)
        self.assertEqual(struct.unpack_from('<6I',result['memory'][17],0),(HEAP,3,1,0,0,1))
        self.assertEqual(result['memory'][15],old)
    def test_slot_gates_on_nonzero_count_callback_and_slot(self):
        for where in (None,'count','callback','slot'):
            memory=self.initial([1]);slot=1
            if where=='count':struct.pack_into('<I',memory[17],4,0)
            if where=='callback':memory[15][:]=bytes(4)
            if where=='slot':slot=0
            result,_=self.execute('slot',slot,123,memory=memory)
            self.assertEqual(result['result'],0 if where is None else 0xFFFFFFFF)
            if where is not None:self.assertEqual(result['memory'],tuple(memory))
    def test_slot_setter_accepts_out_of_range_token_but_reader_rejects_it(self):
        result,_=self.execute('slot',9,123,memory=self.initial([1]))
        self.assertEqual(result['result'],0)
        read,_=self.execute('read',9,123,1,memory=result['memory'])
        self.assertEqual(read['result'],0xFFFFFFFF);self.assertEqual(read['calls'],[])
    def test_budget_rounding_clamping_signedness_and_wraparound(self):
        for value,expected in ((0,0),(1,128),(21,1024),(86,4096),(0xFFFFFFFF,0),(0x5555555,128)):
            self.assertEqual(self.execute('budget',value)[0]['result'],expected)
    def test_format_conversion_includes_the_original_padding(self):
        for args,expected in (((100,0,0),100),((100,0,1),218),((101,1,0),60),((0xFFFFFFFF,1,0),9)):
            self.assertEqual(self.execute('convert',*args)[0]['result'],expected)
    def test_length_uses_budget_and_aligned_trim_in_both_modes(self):
        for args,expected in (((4076,129,0,0,0),192),((4076,129,0,1,0),384),
                              ((4076,0,1,0,21),512),((4076,0,0,1,0),4096)):
            self.assertEqual(self.execute('limit',*args)[0]['result'],expected)
    def test_callback_reads_in_2048_byte_chunks_then_crc_polls(self):
        from ir_loader_machine import READ,PRIORITY,POLL
        payload=bytes(4098)
        result,requests=self.execute('read',8,zlib.crc32(payload),2049,reads=self.read_script(payload))
        self.assertEqual(result['result'],0)
        self.assertEqual(requests,[(0xFD000,40),(0xFD028,2048),(0xFD828,2048),(0xFE028,2)])
        services=[row[0] for row in result['calls']]
        self.assertEqual(services,[PRIORITY]+[READ]*4+[POLL]*16+[PRIORITY])
    def test_old_tag_probes_the_same_header_twice(self):
        payload=b'12';result,requests=self.execute('read',1,zlib.crc32(payload),1,reads=self.read_script(payload,0x49474B54))
        self.assertEqual(result['result'],0);self.assertEqual(requests[:2],[(0xEF000,40)]*2)
    def test_header_identity_or_size_mismatch_never_reads_payload(self):
        for identity,count in ((0,1),(zlib.crc32(b'12'),2)):
            result,requests=self.execute('read',1,identity,count,reads=[(0,self.record(b'12'),())])
            self.assertEqual(result['result'],0xFFFFFFFF);self.assertEqual(len(requests),1)
    def test_failed_unwritten_header_frame_has_no_observable_effect(self):
        first=None
        for seed in (0,1,0xA7,255):
            result,_=self.execute('read',1,0,1,reads=[(1,b'',())]*2,stack_byte=seed)
            relevant=(result['result'],result['memory'],result['calls'])
            if first is None:first=relevant
            self.assertEqual(relevant,first)
    def test_partial_payload_failure_retains_bytes_and_restores_priority(self):
        from ir_loader_machine import PRIORITY
        payload=b'1234';script=self.read_script(payload);script[-1]=(1,b'xy',())
        result,_=self.execute('read',1,zlib.crc32(payload),2,reads=script)
        self.assertEqual(result['result'],0xFFFFFFFE)
        self.assertEqual(result['memory'][16][:4],b'xy\xA6\xA6')
        self.assertEqual(result['calls'][-1][:2],(PRIORITY,(0,0,0,0)))
    def test_crc_failure_is_distinct_from_read_failure(self):
        result,_=self.execute('read',1,123,1,reads=self.read_script(b'12',identity=123))
        self.assertEqual(result['result'],0xFFFFFFFD)
    def test_attach_finishes_configuration_before_unlock_and_commit(self):
        from ir_loader_machine import HEAP,LOCK,UNLOCK,FREE
        memory=self.initial([32767,0,0]);struct.pack_into('<I',memory[1],164,0x12340000)
        result,_=self.execute('attach',HEAP,3,0,1,memory=memory)
        self.assertEqual([row[0] for row in result['calls']],[LOCK,UNLOCK,FREE])
        unlock=result['calls'][1][2]
        self.assertEqual(self.word(unlock[17],20),1);self.assertEqual(self.word(unlock[1],164),0x12340000)
        self.assertEqual(self.word(result['calls'][2][2][1],164),HEAP)
    def test_full_load_defers_and_frees_after_actual_slot_installation(self):
        from ir_loader_machine import HEAP,FREE,INSTALL,INSTALL_SLOT
        payload=struct.pack('<hhhh',32767,0,0,0)
        result,_=self.execute('load',3,1,reads=self.load_reads(payload))
        self.assertEqual(result['result'],0)
        self.assertEqual(struct.unpack_from('<6I',result['memory'][17],0),(0,4,1,4,zlib.crc32(payload),1))
        self.assertEqual(self.word(result['memory'][1],164),0)
        self.assertEqual([row[1][0] for row in result['calls'] if row[0]==FREE],[HEAP])
        self.assertFalse({INSTALL,INSTALL_SLOT}&{row[0] for row in result['calls']})
    def test_out_of_domain_storage_is_rejected_before_native_execution(self):
        from ir_installation_machine import HEAP
        for operation,args in (('trim',(HEAP,4077)),('configure',(HEAP+2,1,0,0)),('read',(1,0,4077))):
            with self.assertRaises(ValueError):self.execute(operation,*args)

if __name__=='__main__':unittest.main()
