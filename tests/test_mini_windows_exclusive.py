"""Fake Windows APIs only; no disk, device, discovery, or hardware commands."""
import ctypes as c
from unittest.mock import MagicMock, patch
import unittest

from tools import mini_windows_exclusive as exclusive
from tools import mini_windows_mcn as mcn
from tools import mini_windows_spt as spt
from tools import mini_windows_quiet as quiet
from tools import probe_mini_recovery as recovery
from tests import test_mini_windows_quiet as previous


class ExclusiveTests(previous.QuietTests):
    """Reapply quiet's identity/failure tests to the new constructor."""

    def open(self, attestation=None, **kwargs):
        return exclusive.ExclusiveBufferedRomTransport(attestation or self.attestation,
                                                       slot=previous.SLOT, **kwargs)

    def test_constructor_inherits_exchange_and_opens_exact_interface(self):
        self.assertIs(exclusive.ExclusiveBufferedRomTransport.exchange, spt.WindowsBufferedRomTransport.exchange)
        self.assertIs(exclusive.ExclusiveBufferedRomTransport._exchange_once, spt.WindowsBufferedRomTransport._exchange_once)
        self.assertIs(exclusive.ExclusiveBufferedRomTransport.close, recovery.WindowsRomTransport.close)
        transport = self.open()
        self.kernel.CreateFileW.assert_called_once_with(previous.INTERFACE, 0xC0000000, 0, None, 3, 0, None)
        self.assertEqual(self.kernel.calls, [0x2D1080, 0x2D1400, 0x2D1400, 0x4D004])
        self.assertEqual(self.kernel.cdbs, [quiet.INQUIRY])
        self.assertEqual(self.cfg.property_reads, 2)
        self.assertEqual(transport.disk['path'], previous.DISK)
        self.assertEqual(transport.attestation.last_arrival_filetime, previous.ARRIVAL)
        self.assertEqual(transport.open_metadata['share_mode_requested'], 0)
        self.assertTrue(transport.open_metadata['exclusive_open_requested'])
        for key in ('competing_data_open_tested', 'polling_exclusion_proven',
                    'attribute_only_opens_excluded', 'kernel_IO_excluded', 'shared_open_fallback'):
            self.assertFalse(transport.open_metadata[key])
        transport.close(); transport.close()
        self.kernel.CloseHandle.assert_called_once_with(42)

    def test_profile_slot_validated_before_native_apis(self):
        for slot, profile in [(0, 'ram-probe'), (previous.SLOT, 'unknown')]:
            with self.subTest(slot=slot, profile=profile), self.assertRaises(ValueError):
                exclusive.ExclusiveBufferedRomTransport(self.attestation, slot=slot, profile=profile)
        self.assertEqual(self.cfg.calls, [])
        self.kernel.CreateFileW.assert_not_called()

    def test_sharing_violation_and_access_denied_never_fall_back(self):
        for error in (32, 5, 87):
            with self.subTest(error=error):
                self.kernel.CreateFileW.reset_mock()
                self.kernel.CreateFileW.return_value = c.c_void_p(-1).value
                with patch.object(exclusive.c, 'get_last_error', return_value=error, create=True):
                    with self.assertRaises(OSError) as caught:
                        self.open()
                self.assertEqual(caught.exception.errno, error)
                self.kernel.CreateFileW.assert_called_once_with(previous.INTERFACE, 0xC0000000, 0, None, 3, 0, None)
                self.assertEqual(self.kernel.calls, [])
                self.assertEqual(self.kernel.cdbs, [])
                self.kernel.CloseHandle.assert_not_called()

    def test_competing_open_reports_exact_denial_and_sends_no_ioctl(self):
        transport = self.open()
        before_calls, before_cdbs = list(self.kernel.calls), list(self.kernel.cdbs)
        self.kernel.CreateFileW.reset_mock()
        self.kernel.CreateFileW.return_value = c.c_void_p(-1).value
        with patch.object(exclusive.c, 'get_last_error', return_value=32, create=True):
            result = exclusive.probe_competing_data_open(transport)
        self.kernel.CreateFileW.assert_called_once_with(previous.INTERFACE, 0x80000000, 3, None, 3, 0, None)
        self.assertEqual(result['data_open_exclusion_result'], 'denied32')
        self.assertTrue(result['sharing_denial_observed'])
        self.assertFalse(result['second_open_succeeded'] or result['polling_exclusion_proven'])
        self.assertIsNone(result['second_handle_closed'])
        self.assertEqual(self.kernel.calls, before_calls)
        self.assertEqual(self.kernel.cdbs, before_cdbs)
        self.kernel.CloseHandle.assert_not_called()
        transport.close()

    def test_competing_open_success_is_closed_and_disproves_exclusion(self):
        transport = self.open()
        before = list(self.kernel.calls)
        self.kernel.CreateFileW.return_value = 43
        result = exclusive.probe_competing_data_open(transport)
        self.assertEqual(result['data_open_exclusion_result'], 'not_enforced')
        self.assertTrue(result['second_open_succeeded'] and result['second_handle_closed'])
        self.assertFalse(result['sharing_denial_observed'] or result['polling_exclusion_proven'])
        self.kernel.CloseHandle.assert_called_once_with(43)
        self.assertEqual(transport._handle, 42)
        self.assertEqual(self.kernel.calls, before)
        self.assertFalse(transport._exchange_lock.locked())
        transport.close()

    def test_competing_open_other_errors_are_inconclusive_and_never_retried(self):
        transport = self.open()
        before = list(self.kernel.calls)
        for error in (5, 31, 87):
            with self.subTest(error=error):
                self.kernel.CreateFileW.reset_mock()
                self.kernel.CreateFileW.return_value = c.c_void_p(-1).value
                with patch.object(exclusive.c, 'get_last_error', return_value=error, create=True):
                    result = exclusive.probe_competing_data_open(transport)
                self.assertEqual(result['data_open_exclusion_result'], 'inconclusive')
                self.assertFalse(result['sharing_denial_observed'])
                self.assertEqual(result['win32_error'], error)
                self.assertEqual(self.kernel.CreateFileW.call_count, 1)
                self.assertEqual(self.kernel.calls, before)
        transport.close()

    def test_competing_close_failure_is_reported_and_lock_is_released(self):
        transport = self.open()
        self.kernel.CreateFileW.return_value = 43
        self.kernel.CloseHandle.return_value = False
        with self.assertRaises(OSError):
            exclusive.probe_competing_data_open(transport)
        self.kernel.CloseHandle.assert_called_once_with(43)
        self.assertEqual(transport._handle, 42)
        self.assertFalse(transport._exchange_lock.locked())
        self.kernel.CloseHandle.return_value = True
        transport.close()

    def test_competing_probe_cannot_run_on_failed_closed_or_busy_transport(self):
        transport = self.open()
        self.kernel.CreateFileW.reset_mock()
        transport.failed = True
        with self.assertRaises(ValueError): exclusive.probe_competing_data_open(transport)
        transport.failed = False
        transport._exchange_lock.acquire()
        try:
            with self.assertRaisesRegex(ValueError, 'already active'):
                exclusive.probe_competing_data_open(transport)
        finally:
            transport._exchange_lock.release()
        transport.close()
        with self.assertRaises(ValueError): exclusive.probe_competing_data_open(transport)
        self.kernel.CreateFileW.assert_not_called()

    def test_attributes_only_MCN_keeps_its_separate_handle_and_balanced_cleanup(self):
        transport = self.open()
        opens, controls = [], []
        def opened(path, access, share, *tail):
            opens.append((path, access, share))
            # Attributes-only access has no data read/write/delete bits and
            # its share3 is compatible with the existing read+write handle.
            self.assertEqual((path, access, share), (previous.DISK, 0x80, 3))
            return 77
        original_ioctl = self.kernel.ioctl
        def ioctl(handle, code, source, source_size, output, output_size, returned, overlapped):
            if handle == 77:
                self.assertEqual((code, source_size, output, output_size, overlapped), (0x2D0944, 1, None, 0, None))
                controls.append(c.cast(source, c.POINTER(c.c_ubyte))[0])
                previous.put32(returned, 0)
                return True
            return original_ioctl(handle, code, source, source_size, output, output_size, returned, overlapped)
        self.kernel.CreateFileW.side_effect = opened
        self.kernel.DeviceIoControl.side_effect = ioctl
        with mcn.MiniMediaChangePause(transport, log=lambda event: None):
            self.assertEqual(transport._handle, 42)
        self.assertEqual(opens, [(previous.DISK, 0x80, 3)])
        self.assertEqual(controls, [1, 0])
        self.kernel.CloseHandle.assert_called_once_with(77)
        self.assertEqual(self.kernel.cdbs, [quiet.INQUIRY])
        transport.close()


if __name__ == '__main__':
    unittest.main()
