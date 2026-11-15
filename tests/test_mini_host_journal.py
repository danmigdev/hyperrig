import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from tools import mini_host_journal as journal


class JournalTests(unittest.TestCase):
    def test_atomic_publication_and_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json'
            result=journal.atomic_write_json(p,{'generation':1})
            self.assertEqual(result['replace_attempts'],1)
            self.assertEqual(journal.read_shared_json(p),{'generation':1})
            self.assertFalse(p.with_suffix('.json.tmp').exists())

    def test_retry_only_local_rename_and_publish_exact_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json';p.write_text('{"generation":0}')
            real=os.replace;calls=[]
            def replace(a,b):
                calls.append(Path(a).read_bytes())
                if len(calls)<3:raise PermissionError(13,'sharing collision')
                real(a,b)
            with patch.object(journal.os,'replace',side_effect=replace),patch.object(journal.time,'sleep') as sleep:
                result=journal.atomic_write_json(p,{'generation':1})
            self.assertEqual(result['replace_attempts'],3)
            self.assertEqual(sleep.call_count,2)
            self.assertEqual(calls,[p.read_bytes()]*3)

    def test_exhaustion_retains_original_and_unpublished_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json';p.write_text('{"generation":0}')
            with patch.object(journal.os,'replace',side_effect=PermissionError(13,'locked')) as replace:
                with self.assertRaises(PermissionError):journal.atomic_write_json(p,{'generation':1},attempts=2,delay=0)
            self.assertEqual(replace.call_count,2)
            self.assertEqual(json.loads(p.read_text()),{'generation':0})
            self.assertEqual(json.loads(p.with_suffix('.json.tmp').read_text()),{'generation':1})

    def test_other_error_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json'
            with patch.object(journal.os,'replace',side_effect=OSError(28,'disk full')) as replace:
                with self.assertRaises(OSError):journal.atomic_write_json(p,{})
            self.assertEqual(replace.call_count,1)

    @unittest.skipUnless(os.name=='nt','Windows sharing contract')
    def test_real_reader_and_concurrent_atomic_replace_complete(self):
        # Publish concurrently while the real read handle is open, then release
        # the reader promptly so legacy Windows rename can complete on retry.
        import ctypes as c
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json';journal.atomic_write_json(p,{'generation':1})
            real=c.WinDLL;published=[];threads=[];errors=[]
            class Function:
                def __init__(self,fn,before=None):self.fn,self.before=fn,before
                def __call__(self,*args):
                    if self.before:self.before()
                    return self.fn(*args)
            class Kernel:
                def __init__(self):
                    kernel=real('kernel32',use_last_error=True)
                    self.CreateFileW=kernel.CreateFileW;self.GetFileSizeEx=kernel.GetFileSizeEx;self.CloseHandle=kernel.CloseHandle
                    kernel.ReadFile.argtypes=[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_void_p]
                    kernel.ReadFile.restype=c.c_int
                    def publish():
                        def writer():
                            try:published.append(journal.atomic_write_json(p,{'generation':2}))
                            except Exception as error:errors.append(error)
                        thread=threading.Thread(target=writer);threads.append(thread);thread.start()
                        time.sleep(.04)
                    self.ReadFile=Function(kernel.ReadFile,publish)
            with patch.object(journal.c,'WinDLL',return_value=Kernel()):
                observed=journal.read_shared_json(p)
            for thread in threads:thread.join(2)
            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(errors,[])
            self.assertEqual(len(published),1)
            self.assertEqual(observed,{'generation':1})
            self.assertEqual(journal.read_shared_json(p),{'generation':2})

if __name__=='__main__':unittest.main()
