"""Temporarily suspend Windows media-change polling for one identified MINI.

Uses a separate FILE_READ_ATTRIBUTES handle and IOCTL_STORAGE_MCN_CONTROL.
No registry change, disk write, SCSI request, reset, or device enumeration on
import. Close restores the matched disable count; Windows also owns cleanup
if the process exits. The caller retains its separate identified SPT handle.
"""
from __future__ import annotations

import ctypes as c
from datetime import datetime, timezone
from tools.probe_mini_recovery import WindowsRomTransport

IOCTL_STORAGE_MCN_CONTROL = 0x002D0944
FILE_READ_ATTRIBUTES = 0x80
SHARE_READ_WRITE = 3
OPEN_EXISTING = 3


class MiniMediaChangePause:
    """One per-handle disable/enable pair, with cleanup on every exit path."""
    def __init__(self, transport, *, log):
        if not isinstance(transport, WindowsRomTransport) or transport._handle is None:
            raise ValueError('an open identified Windows MINI ROM transport is required')
        if transport.inquiry.get('vendor') != 'WL82' or transport.inquiry.get('product') != 'UBOOT1.00':
            raise ValueError('MINI ROM inquiry differs')
        if not callable(log):
            raise ValueError('an event logger is required')
        self.path = transport.disk['path']
        self._kernel, self.log = transport._kernel, log
        self._handle, self.disabled, self.closed = None, False, False
        try:
            self._event('mcn_open_intent', access=FILE_READ_ATTRIBUTES, registry_write=False,
                        SCSI_command=False, reset=False)
            handle = self._kernel.CreateFileW(self.path, FILE_READ_ATTRIBUTES, SHARE_READ_WRITE,
                                              None, OPEN_EXISTING, 0, None)
            if handle == c.c_void_p(-1).value:
                raise OSError(c.get_last_error(), 'cannot open MINI attributes handle for MCN')
            self._handle = handle
            self._event('mcn_disable_intent', ioctl=IOCTL_STORAGE_MCN_CONTROL)
            self._control(True)
            self.disabled = True
            self._event('mcn_disabled', cleanup_owned_by_handle=True)
        except BaseException:
            self.close()
            raise

    def _event(self, event, **details):
        self.log({'event': event, 'utc': datetime.now(timezone.utc).isoformat(), 'path': self.path, **details})

    def _control(self, disable):
        # PREVENT_MEDIA_REMOVAL is a BOOLEAN (one byte), not Win32 BOOL.
        flag, returned = c.c_ubyte(int(disable)), c.c_uint32()
        ok = self._kernel.DeviceIoControl(self._handle, IOCTL_STORAGE_MCN_CONTROL,
            c.byref(flag), c.sizeof(flag), None, 0, c.byref(returned), None)
        error = c.get_last_error() if not ok else None
        if not ok:
            raise OSError(error, 'MINI MCN control failed')
        if returned.value:
            raise OSError('MCN control unexpectedly returned data')

    def close(self):
        if self.closed:
            return
        self.closed = True
        handle = self._handle
        if handle is None:
            return
        failure = None
        try:
            if self.disabled:
                try:
                    self._event('mcn_enable_intent')
                    self._control(False)
                    self.disabled = False
                    self._event('mcn_reenabled')
                except BaseException as error:
                    failure = error
        finally:
            self._handle = None
            closed = self._kernel.CloseHandle(handle)
            if not closed and failure is None:
                failure = OSError(c.get_last_error(), 'cannot close MINI MCN attributes handle')
            self._event('mcn_handle_closed', close_ok=bool(closed),
                        explicit_enable_succeeded=not self.disabled,
                        windows_file_object_cleanup_required=self.disabled,
                        error=repr(failure) if failure else None)
        if failure is not None:
            raise failure

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
