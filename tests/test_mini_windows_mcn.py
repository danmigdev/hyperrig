"""Verify MCN handle scope and exceptional cleanup without Windows/device I/O."""
import ctypes as c
import unittest
from unittest.mock import patch
from tools import mini_windows_mcn as mcn


class FakeKernel:
    def __init__(self, failures=()):
        self.calls, self.failures = [], set(failures)
    def CreateFileW(self, *args):
        self.calls.append(('open', args))
        return c.c_void_p(-1).value if 'open' in self.failures else 77
    def DeviceIoControl(self, handle, code, flag, length, output, size, returned, overlapped):
        value = c.cast(flag, c.POINTER(c.c_ubyte)).contents.value
        self.calls.append(('control', handle, code, value, length, output, size, overlapped))
        return int(('disable' if value else 'enable') not in self.failures)
    def CloseHandle(self, handle):
        self.calls.append(('close', handle))
        return 1


class MCNTests(unittest.TestCase):
    def fixture(self, failures=()):
        transport = object.__new__(mcn.WindowsRomTransport)
        transport._handle = 12
        transport._kernel = FakeKernel(failures)
        transport.disk = {'path': r'\\.\PHYSICALDRIVE4'}
        transport.inquiry = {'vendor': 'WL82', 'product': 'UBOOT1.00'}
        return transport

    def test_exact_attributes_access_and_matched_single_byte_controls(self):
        t = self.fixture(); events = []
        with mcn.MiniMediaChangePause(t, log=events.append) as pause:
            self.assertTrue(pause.disabled)
        pause.close()
        self.assertEqual(t._kernel.calls, [
            ('open', (t.disk['path'], 0x80, 3, None, 3, 0, None)),
            ('control', 77, 0x2d0944, 1, 1, None, 0, None),
            ('control', 77, 0x2d0944, 0, 1, None, 0, None), ('close', 77)])
        self.assertEqual(t._handle, 12)
        self.assertFalse(events[-1]['windows_file_object_cleanup_required'])

    def test_body_exception_still_enables_and_closes(self):
        t = self.fixture()
        with self.assertRaisesRegex(RuntimeError, 'body'):
            with mcn.MiniMediaChangePause(t, log=lambda e: None):
                raise RuntimeError('body')
        self.assertEqual([v[0] for v in t._kernel.calls], ['open', 'control', 'control', 'close'])

    def test_disable_failure_closes_without_unbalanced_enable(self):
        t = self.fixture(('disable',))
        with patch.object(mcn.c, 'get_last_error', return_value=87, create=True):
            with self.assertRaises(OSError): mcn.MiniMediaChangePause(t, log=lambda e: None)
        self.assertEqual([v[0] for v in t._kernel.calls], ['open', 'control', 'close'])

    def test_enable_failure_still_closes_for_driver_cleanup(self):
        t = self.fixture(('enable',)); events=[]
        with patch.object(mcn.c, 'get_last_error', return_value=87, create=True):
            with self.assertRaises(OSError):
                with mcn.MiniMediaChangePause(t, log=events.append): pass
        self.assertEqual(t._kernel.calls[-1], ('close', 77))
        self.assertTrue(events[-1]['windows_file_object_cleanup_required'])

    def test_open_failure_sends_no_control(self):
        t = self.fixture(('open',))
        with patch.object(mcn.c, 'get_last_error', return_value=5, create=True):
            with self.assertRaises(OSError): mcn.MiniMediaChangePause(t, log=lambda e: None)
        self.assertEqual(len(t._kernel.calls), 1)

    def test_logger_failure_after_disable_still_closes(self):
        t=self.fixture()
        def log(event):
            if event['event']=='mcn_disabled': raise RuntimeError('log')
        with self.assertRaisesRegex(RuntimeError,'log'):mcn.MiniMediaChangePause(t,log=log)
        self.assertEqual(t._kernel.calls[-1],('close',77))
        self.assertEqual(t._kernel.calls[-2][3],0)

    def test_unidentified_or_closed_transport_rejected(self):
        t=self.fixture();t.inquiry['product']='OTHER'
        with self.assertRaises(ValueError):mcn.MiniMediaChangePause(t,log=lambda e:None)
        self.assertEqual(t._kernel.calls,[])
        t=self.fixture();t._handle=None
        with self.assertRaises(ValueError):mcn.MiniMediaChangePause(t,log=lambda e:None)
        self.assertEqual(t._kernel.calls,[])

if __name__=='__main__':unittest.main()
