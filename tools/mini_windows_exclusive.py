"""Request a non-shared ROM disk handle, keeping the frozen buffered exchange.

Import is offline. Only explicit construction opens the attested disk interface.
Share mode zero is a request to Windows, not proof that attribute-only opens,
kernel requests, or a raw-device stack's own polling have been excluded. There
is no shared-open fallback, device discovery, command retry, reset or service
configuration change. See docs/MINI_WINDOWS_EXCLUSIVE.md for the exact limits.
"""
from __future__ import annotations

import ctypes as c
import os
import threading
import time

from tools import mini_windows_quiet as quiet
from tools.mini_windows_spt import WindowsBufferedRomTransport

RomDiskAttestation = quiet.RomDiskAttestation
GENERIC_READ_WRITE = 0xC0000000
SHARE_NONE = 0
OPEN_EXISTING = 3
GENERIC_READ = 0x80000000
SHARE_READ_WRITE = 3
ERROR_SHARING_VIOLATION = 32


class ExclusiveBufferedRomTransport(WindowsBufferedRomTransport):
    """Quiet's attested constructor with CreateFile share mode zero.

    The caller must close its previous data handle before this attempt. A
    sharing violation is terminal for this constructor; it never falls back to
    FILE_SHARE_READ/WRITE. The separate attributes-only MCN handle is governed
    by its original owner and is not created or closed here.
    """

    def __init__(self, attestation: RomDiskAttestation, *, slot: int, profile: str = "ram-probe"):
        if os.name != "nt" or c.sizeof(c.c_void_p) != 8:
            raise OSError("exclusive buffered transport requires 64-bit Windows Python")
        quiet._require(type(attestation) is RomDiskAttestation, "immutable RomDiskAttestation required")
        quiet._require(type(slot) is int and slot in quiet.RAM_SLOTS, "known RAM plugin slot required")
        quiet.validate_profile_request(quiet.INQUIRY, None, 36, slot=slot, profile=profile)
        started = time.perf_counter_ns()
        self._handle = None
        self._c, self.slot, self.profile = c, slot, profile
        self.adapter_descriptor = self.last_transfer = None
        self.failed = False
        self._exchange_lock = threading.Lock()
        api = quiet._cfgmgr32()
        selected = quiet._metadata_snapshot(api, attestation)
        self.attestation, self.disk = selected, selected.discovery_dict()
        self.opened_interface = selected.interface_path
        self._kernel = kernel = quiet._kernel32()
        handle = kernel.CreateFileW(self.opened_interface, GENERIC_READ_WRITE, SHARE_NONE,
                                    None, OPEN_EXISTING, 0, None)
        if handle is None or handle == c.c_void_p(-1).value:
            error = c.get_last_error()
            raise OSError(error, "cannot open attested ROM disk with share mode0; no shared fallback")
        self._handle = handle
        try:
            self.storage_device_number = quiet._device_number(kernel, handle, selected.device_number)
            self.device_number = self.storage_device_number["device_number"]
            inquiry = self.exchange(quiet.INQUIRY, read_length=36)
            vendor = inquiry[8:16].decode("ascii").strip()
            product = inquiry[16:32].decode("ascii").strip()
            quiet._require((vendor, product) == ("WL82", "UBOOT1.00"), "unexpected attested disk INQUIRY")
            self.inquiry = {"vendor": vendor, "product": product, "raw_hex": inquiry.hex()}
            quiet._metadata_snapshot(api, selected)
            self.open_metadata = {"backend": "spt-buffered", "selection": "cfgmgr32-attested",
                "opened_interface": self.opened_interface, "attestation": selected.summary(),
                "storage_device_number": dict(self.storage_device_number),
                "started_monotonic_ns": started, "finished_monotonic_ns": time.perf_counter_ns(),
                "desired_access": GENERIC_READ_WRITE, "share_mode_requested": SHARE_NONE,
                "open_existing": OPEN_EXISTING, "exclusive_open_requested": True,
                "competing_data_open_tested": False, "polling_exclusion_proven": False,
                "attribute_only_opens_excluded": False, "kernel_IO_excluded": False,
                "win32_diskdrive_queries": 0, "discovery_fallback": False, "shared_open_fallback": False}
        except BaseException:
            self.close()
            raise


def probe_competing_data_open(transport: ExclusiveBufferedRomTransport):
    """Explicitly try one second read-data open; issue no IOCTL or CDB.

    A successful second open is closed immediately and disproves the requested
    sharing exclusion for this interface. Error32 observes a sharing denial;
    other errors are inconclusive. Even error32 does not exclude attributes-only
    handles, kernel polling, alternate named objects or filter-driver requests.
    CreateFile itself may cause driver activity; no physical-NOR claim is made.
    """
    quiet._require(type(transport) is ExclusiveBufferedRomTransport
                   and transport._handle is not None and not transport.failed,
                   "open nonfailed exclusive transport required")
    quiet._require(transport.inquiry.get("vendor") == "WL82"
                   and transport.inquiry.get("product") == "UBOOT1.00",
                   "identified MINI ROM transport required")
    quiet._require(transport._exchange_lock.acquire(blocking=False), "transport exchange is already active")
    try:
        handle = transport._kernel.CreateFileW(transport.opened_interface, GENERIC_READ, SHARE_READ_WRITE,
                                              None, OPEN_EXISTING, 0, None)
        invalid = handle is None or handle == c.c_void_p(-1).value
        error = c.get_last_error() if invalid else None
        result = {"opened_interface": transport.opened_interface, "desired_access": GENERIC_READ,
                  "share_mode_requested": SHARE_READ_WRITE, "second_open_succeeded": not invalid,
                  "win32_error": error, "sharing_denial_observed": invalid and error == ERROR_SHARING_VIOLATION,
                  "data_open_exclusion_result": ("denied32" if error == ERROR_SHARING_VIOLATION
                                                 else "inconclusive" if invalid else "not_enforced"),
                  "explicit_IOCTL_count": 0, "explicit_SCSI_count": 0, "open_attempts": 1,
                  "attribute_only_opens_excluded": False, "kernel_IO_excluded": False,
                  "polling_exclusion_proven": False, "second_handle_closed": None if invalid else False}
        if not invalid:
            ok = transport._kernel.CloseHandle(handle)
            if not ok:
                error = c.get_last_error()
                raise OSError(error, "cannot close competing diagnostic handle; no fallback or retry")
            result["second_handle_closed"] = True
        return result
    finally:
        transport._exchange_lock.release()
