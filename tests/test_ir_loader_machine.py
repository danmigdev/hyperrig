"""Hand-checked IR ownership/failure expectations for the instruction model."""
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
AVAILABLE=((ROOT/'analysis/firmware/m571_g_app/app.bin').is_file() and
           (ROOT/'upstream/pi32v2-isa/pi32v2isa').is_dir())

@unittest.skipUnless(AVAILABLE,'bootstrap and analyze the pinned firmware first')
class IrLoaderInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'tools'))
        from ir_loader_machine import IrLoaderProgram
        from verify_ir_loader import baseline,record,load_reads,Reads,Script
        cls.program=IrLoaderProgram()
        cls.initial,cls.record,cls.load_reads=staticmethod(baseline),staticmethod(record),staticmethod(load_reads)
        cls.Reads,cls.Script=Reads,Script

    def execute(self,op,*args,memory=None,reads=(),plan=None):
        source=self.Reads(reads)
        result=self.program.execute(memory or self.initial(),op,*args,reader=source.read,boundary=self.Script(plan))
        return result,source.requests

    @staticmethod
    def word(data,offset=0): return struct.unpack_from('<I',data,offset)[0]

    def test_attach_commits_after_unlock_and_frees_previous(self):
        from ir_loader_machine import HEAP,LOCK,UNLOCK,INSTALL,FREE
        memory=self.initial(); struct.pack_into('<I',memory[1],164,0x12340000)
        result,_=self.execute('attach',HEAP,17,48000,5,memory=memory)
        self.assertEqual([row[0] for row in result['calls']],[LOCK,INSTALL,UNLOCK,FREE])
        self.assertEqual(result['calls'][1][1],(HEAP,17,48000,5))
        self.assertEqual(self.word(result['calls'][2][2][1],164),0x12340000)
        self.assertEqual(self.word(result['calls'][3][2][1],164),HEAP)
        self.assertEqual(struct.unpack_from('<II',result['memory'][1],152),(17,48000))
        self.assertEqual(self.word(result['memory'][1],168),1)
        self.assertEqual(self.word(result['memory'][1],172),0)

    def test_attach_same_handle_does_not_free(self):
        from ir_loader_machine import HEAP,FREE
        memory=self.initial(); struct.pack_into('<I',memory[1],164,HEAP)
        result,_=self.execute('attach',HEAP,0,0,0,memory=memory)
        self.assertNotIn(FREE,[row[0] for row in result['calls']])

    def test_pending_requires_presence_without_live_handle(self):
        for present,handle,expected in ((0,0,0),(1,0,8),(1,99,0),(255,0,8)):
            memory=self.initial(); memory[1][160]=present
            struct.pack_into('<I',memory[1],164,handle); struct.pack_into('<I',memory[1],172,8)
            result,_=self.execute('pending',memory=memory)
            self.assertEqual(result['result'],expected)

    def test_query_outputs_order_and_presence(self):
        memory=self.initial(); memory[1][160]=1
        struct.pack_into('<II',memory[1],152,123,456); struct.pack_into('<I',memory[1],164,789)
        result,_=self.execute('query',memory=memory)
        self.assertEqual(struct.unpack_from('<II',result['memory'][9]),(123,456))
        self.assertEqual(result['result'],789)

    def test_refresh_always_sets_callback(self):
        result,_=self.execute('refresh')
        self.assertEqual(result['calls'],[])
        self.assertEqual(self.word(result['memory'][15]),0x0201AD4C)

    def test_refresh_moves_live_handle_to_slot_identity(self):
        from ir_loader_machine import HEAP,INSTALL_SLOT,FREE
        memory=self.initial(); memory[0][10]=7; memory[1][160]=1
        struct.pack_into('<I',memory[1],164,HEAP); struct.pack_into('<I',memory[1],744,1234)
        result,_=self.execute('refresh',memory=memory)
        self.assertEqual([row[1] for row in result['calls'] if row[0]==INSTALL_SLOT],[(8,1234,0,0)])
        self.assertEqual([row[1] for row in result['calls'] if row[0]==FREE],[(HEAP,0,0,0)])
        self.assertEqual(self.word(result['memory'][1],164),0)
        self.assertEqual(struct.unpack_from('<II',result['memory'][1],172),(8,1234))

    def test_refresh_install_failure_retains_handle(self):
        from ir_loader_machine import HEAP,INSTALL_SLOT,FREE
        memory=self.initial(); memory[0][10]=1; memory[1][160]=1
        struct.pack_into('<I',memory[1],164,HEAP)
        result,_=self.execute('refresh',memory=memory,plan={INSTALL_SLOT:(1,())})
        self.assertEqual(self.word(result['memory'][1],164),HEAP)
        self.assertNotIn(FREE,[row[0] for row in result['calls']])

    def test_reuse_does_not_allocate_or_refresh(self):
        from ir_loader_machine import ALLOCATE,NOTIFY
        memory=self.initial(); memory[0][10]=2
        result,reads=self.execute('load',2,1,memory=memory,reads=[(0,self.record(),())])
        self.assertEqual(result['result'],0)
        self.assertEqual(reads,[(0xF3000,40)])
        self.assertNotIn(ALLOCATE,[row[0] for row in result['calls']])
        self.assertEqual([row[1] for row in result['calls'] if row[0]==NOTIFY],[(20,0x602,0,0)])
        self.assertEqual(result['memory'][15],memory[15])

    def test_record_payload_read_and_transfer(self):
        from ir_loader_machine import HEAP,INSTALL,OWNS,REFRESH
        result,reads=self.execute('load',2,0,reads=self.load_reads(b'12345'))
        self.assertEqual(result['result'],0)
        self.assertEqual(reads,[(0xF3000,40),(0xF3000,40),(0xF3028,5)])
        self.assertEqual([row[1] for row in result['calls'] if row[0]==INSTALL],[(HEAP,2,48000,1)])
        self.assertEqual([row[1][0] for row in result['calls'] if row[0]==OWNS],[0,1,0])
        self.assertEqual([row[1][0] for row in result['calls'] if row[0]==REFRESH],[0,1,0])
        self.assertEqual(result['memory'][16][:5],b'12345')
        self.assertEqual(result['memory'][0][10],2)
        self.assertEqual(result['memory'][0][19],255)

    def test_old_format_probes_twice_and_installs_zero_format(self):
        from ir_loader_machine import INSTALL
        result,reads=self.execute('load',0,0,reads=self.load_reads(tag=0x49474B54))
        self.assertEqual(len(reads),4)
        self.assertEqual([row[1][3] for row in result['calls'] if row[0]==INSTALL],[0])

    def test_allocation_failure_restores_priority_without_activity(self):
        from ir_loader_machine import ALLOCATE,PRIORITY,ACTIVITY
        result,_=self.execute('load',1,0,reads=[(0,self.record(),())],plan={ALLOCATE:(0,())})
        self.assertEqual(result['result'],(-100)&0xFFFFFFFF)
        self.assertEqual(result['calls'][-1][0:2],(PRIORITY,(0,0,0,0)))
        self.assertNotIn(ACTIVITY,[row[0] for row in result['calls']])

    def test_crc_failure_frees_without_committing(self):
        from ir_loader_machine import FREE,INSTALL,NOTIFY,ACTIVITY
        memory=self.initial(); reads=self.load_reads(); reads[-1]=(0,b'xxxx',())
        result,_=self.execute('load',1,0,memory=memory,reads=reads)
        self.assertEqual(result['result'],(-3)&0xFFFFFFFF)
        self.assertEqual(result['memory'][0],memory[0])
        self.assertEqual(result['memory'][1],memory[1])
        self.assertEqual([row[0] for row in result['calls']][-3:],[FREE,NOTIFY,ACTIVITY])
        self.assertNotIn(INSTALL,[row[0] for row in result['calls']])

    def test_partial_payload_failure_preserves_prefix(self):
        reads=self.load_reads(); reads[-1]=(1,b'xy',())
        result,_=self.execute('load',0,0,reads=reads)
        self.assertEqual(result['result'],(-2)&0xFFFFFFFF)
        self.assertEqual(result['memory'][16][:4],b'xy\xa6\xa6')

    def test_out_of_allocation_domain_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'allocated request'):
            self.execute('load',0,0,reads=[(0,self.record(b'12'),()),(0,self.record(b'1234'),()),(0,b'1234',())])

if __name__=='__main__': unittest.main()
