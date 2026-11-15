"""Open an attested ROM devnode without repeating Win32_DiskDrive discovery.

Import and attestation construction are offline. Explicit transport construction
uses bounded Configuration Manager metadata, storage device-number/adapter
metadata and one INQUIRY. Transfers inherit the frozen buffered implementation.
There is no command retry, reset, discovery fallback or global monkeypatch.
"""
from __future__ import annotations

import ctypes as c
from dataclasses import dataclass, replace
import hashlib
import json
import os
import re
import threading
import time
from uuid import UUID

from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.mini_windows_aligned import validate_profile_request
from tools.probe_mini_recovery import RAM_SLOTS

INQUIRY = bytes((0x12, 0, 0, 0, 36, 0))
DISK_INTERFACE_GUID = "53f56307-b6bf-11d0-94f2-00a0c91efb8b"
ARRIVAL_PROPERTY_GUID = "83da6326-97a6-4088-9453-a1923f573b29"
ARRIVAL_PROPERTY_ID = 102
IOCTL_STORAGE_GET_DEVICE_NUMBER = 0x002D1080
FILE_DEVICE_DISK = 7
DN_STARTED, DN_HAS_PROBLEM = 0x8, 0x400
DEVPROP_TYPE_FILETIME = 0x10
MAX_DEVICE_ID_CHARS, MAX_INTERFACE_CHARS, MAX_CHAIN = 200, 8192, 12


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value, *, maximum):
    return (isinstance(value, str) and 0 < len(value) <= maximum
            and all(ord(ch) >= 32 and ord(ch) != 127 for ch in value))


@dataclass(frozen=True)
class RomDiskAttestation:
    """Immutable selected discovery result; not cryptographic device identity.

    Reuse ``transport.attestation`` after the first successful quiet open: it
    additionally binds the disk interface and USB parent's LastArrivalDate.
    A USB re-enumeration requires a new, explicitly selected attestation.
    """
    path: str
    pnp_id: str
    usb_ancestor: str
    chain: tuple[str, ...]
    model: str
    interface_path: str | None = None
    last_arrival_filetime: int | None = None

    def __post_init__(self):
        _require(isinstance(self.path, str) and re.fullmatch(
            r"\\\\\.\\PhysicalDrive[0-9]{1,10}", self.path, re.I), "explicit PhysicalDrive alias required")
        _require(self.device_number <= 0xFFFFFFFF, "PhysicalDrive number exceeds ULONG")
        _require(type(self.chain) is tuple and 2 <= len(self.chain) <= MAX_CHAIN,
                 "bounded immutable disk-to-USB ancestry required")
        _require(all(_text(node, maximum=MAX_DEVICE_ID_CHARS - 1) for node in self.chain),
                 "invalid attested PnP instance ID")
        _require(len({node.casefold() for node in self.chain}) == len(self.chain),
                 "duplicate PnP nodes in attestation")
        _require(_text(self.pnp_id, maximum=MAX_DEVICE_ID_CHARS - 1)
                 and _text(self.usb_ancestor, maximum=MAX_DEVICE_ID_CHARS - 1)
                 and self.chain[0].casefold() == self.pnp_id.casefold()
                 and self.chain[-1].casefold() == self.usb_ancestor.casefold(),
                 "attested ancestry endpoints differ")
        _require(re.match(r"^USB\\VID_4C4A&PID_8057(?:&|\\)", self.usb_ancestor, re.I),
                 "attested USB ancestor is not 4C4A:8057")
        _require(_text(self.model, maximum=512), "bounded discovery model required")
        _require((self.interface_path is None) == (self.last_arrival_filetime is None),
                 "interface and arrival must be bound together")
        if self.interface_path is not None:
            _require(_valid_interface(self.interface_path), "invalid bound disk interface")
            _require(type(self.last_arrival_filetime) is int
                     and 0 < self.last_arrival_filetime <= 0xFFFFFFFFFFFFFFFF,
                     "invalid bound USB LastArrivalDate")

    @property
    def device_number(self):
        return int(self.path.lower().split("physicaldrive", 1)[1])

    @classmethod
    def from_discovery(cls, disk):
        """Copy one caller-selected descriptor. Does not discover or open it."""
        _require(isinstance(disk, dict) and all(key in disk for key in
                 ("path", "pnp_id", "usb_ancestor", "chain", "model")), "complete discovery descriptor required")
        _require(isinstance(disk["chain"], (list, tuple)), "discovery ancestry must be a sequence")
        return cls(disk["path"], disk["pnp_id"], disk["usb_ancestor"], tuple(disk["chain"]), disk["model"])

    def discovery_dict(self):
        return {"path": self.path, "pnp_id": self.pnp_id, "usb_ancestor": self.usb_ancestor,
                "chain": list(self.chain), "model": self.model}

    def summary(self):
        material = json.dumps(self.discovery_dict(), sort_keys=True, separators=(",", ":")).encode()
        return {**self.discovery_dict(), "discovery_sha256": hashlib.sha256(material).hexdigest(),
                "interface_path": self.interface_path, "last_arrival_filetime": self.last_arrival_filetime,
                "device_number": self.device_number}


class Guid(c.Structure):
    _fields_ = [("data1", c.c_uint32), ("data2", c.c_uint16), ("data3", c.c_uint16),
                ("data4", c.c_ubyte * 8)]


class DevPropKey(c.Structure):
    _fields_ = [("fmtid", Guid), ("pid", c.c_uint32)]


def _guid(value):
    return Guid.from_buffer_copy(UUID(value).bytes_le)


def _valid_interface(value):
    # Device-interface names are opaque. Selection comes from the exact instance
    # ID supplied to CM_Get_Device_Interface_ListW, never a global enumeration.
    return _text(value, maximum=MAX_INTERFACE_CHARS - 2) and value.startswith("\\\\?\\")


def _cfgmgr32():
    api = c.WinDLL("cfgmgr32", use_last_error=True)
    u32, ptr = c.c_uint32, c.POINTER
    signatures = {
        "CM_Locate_DevNodeW": [ptr(u32), c.c_wchar_p, u32],
        "CM_Get_Parent": [ptr(u32), u32, u32],
        "CM_Get_Device_ID_Size": [ptr(u32), u32, u32],
        "CM_Get_Device_IDW": [u32, c.c_wchar_p, u32, u32],
        "CM_Get_DevNode_Status": [ptr(u32), ptr(u32), u32, u32],
        "CM_Get_Device_Interface_List_SizeW": [ptr(u32), ptr(Guid), c.c_wchar_p, u32],
        "CM_Get_Device_Interface_ListW": [ptr(Guid), c.c_wchar_p, c.c_wchar_p, u32, u32],
        "CM_Get_DevNode_PropertyW": [u32, ptr(DevPropKey), ptr(u32), ptr(c.c_ubyte), ptr(u32), u32],
    }
    for name, args in signatures.items():
        method = getattr(api, name)
        method.argtypes, method.restype = args, u32
    return api


def _cm_result(result, operation):
    if result:
        raise OSError(f"{operation} failed with CONFIGRET 0x{int(result):08x}; no retry")


def _device_id(api, node):
    size = c.c_uint32()
    _cm_result(api.CM_Get_Device_ID_Size(c.byref(size), node, 0), "CM_Get_Device_ID_Size")
    _require(0 < size.value < MAX_DEVICE_ID_CHARS, "PnP instance ID exceeds bound")
    buffer = c.create_unicode_buffer(size.value + 1)
    _cm_result(api.CM_Get_Device_IDW(node, buffer, len(buffer), 0), "CM_Get_Device_IDW")
    _require(len(buffer.value) == size.value and _text(buffer.value, maximum=MAX_DEVICE_ID_CHARS - 1),
             "PnP instance ID length changed")
    return buffer.value


def _metadata_snapshot(api, attestation):
    """Check only this live disk devnode, its fixed parents and disk interface."""
    node = c.c_uint32()
    _cm_result(api.CM_Locate_DevNodeW(c.byref(node), attestation.pnp_id, 0), "CM_Locate_DevNodeW")
    for index, expected in enumerate(attestation.chain):
        _require(_device_id(api, node.value).casefold() == expected.casefold(),
                 "live PnP ancestry differs from attested disk")
        status, problem = c.c_uint32(), c.c_uint32()
        _cm_result(api.CM_Get_DevNode_Status(c.byref(status), c.byref(problem), node.value, 0),
                   "CM_Get_DevNode_Status")
        _require(status.value & DN_STARTED and not status.value & DN_HAS_PROBLEM and not problem.value,
                 "attested devnode is not started or reports a problem")
        if index + 1 < len(attestation.chain):
            parent = c.c_uint32()
            _cm_result(api.CM_Get_Parent(c.byref(parent), node.value, 0), "CM_Get_Parent")
            node = parent
    key = DevPropKey(_guid(ARRIVAL_PROPERTY_GUID), ARRIVAL_PROPERTY_ID)
    kind, size, value = c.c_uint32(), c.c_uint32(8), (c.c_ubyte * 8)()
    _cm_result(api.CM_Get_DevNode_PropertyW(node.value, c.byref(key), c.byref(kind),
                value, c.byref(size), 0), "CM_Get_DevNode_PropertyW(LastArrivalDate)")
    arrival = int.from_bytes(bytes(value), "little")
    _require(kind.value == DEVPROP_TYPE_FILETIME and size.value == 8 and arrival > 0,
             "USB LastArrivalDate must be a complete nonzero FILETIME")
    interface_guid, count = _guid(DISK_INTERFACE_GUID), c.c_uint32()
    _cm_result(api.CM_Get_Device_Interface_List_SizeW(c.byref(count), c.byref(interface_guid),
                attestation.pnp_id, 0), "CM_Get_Device_Interface_List_SizeW")
    _require(3 <= count.value <= MAX_INTERFACE_CHARS, "disk interface list missing or exceeds bound")
    buffer = c.create_unicode_buffer("\uffff" * count.value, count.value)
    _cm_result(api.CM_Get_Device_Interface_ListW(c.byref(interface_guid), attestation.pnp_id,
                buffer, len(buffer), 0), "CM_Get_Device_Interface_ListW")
    multi = "".join(buffer)
    _require(multi.endswith("\0\0"), "unterminated disk interface list")
    items = multi[:-2].split("\0")
    _require(len(items) == 1 and _valid_interface(items[0]), "disk interface is not unique and present")
    interface = items[0]
    if attestation.interface_path is not None:
        _require(interface.casefold() == attestation.interface_path.casefold()
                 and arrival == attestation.last_arrival_filetime,
                 "attested interface or USB arrival changed; explicit new selection required")
    return replace(attestation, interface_path=interface, last_arrival_filetime=arrival)


def _kernel32():
    # Fixed-width types avoid host-platform LONG differences in the fake tests.
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [c.c_wchar_p, c.c_uint32, c.c_uint32, c.c_void_p,
                                  c.c_uint32, c.c_uint32, c.c_void_p]
    kernel.CreateFileW.restype = c.c_void_p
    kernel.DeviceIoControl.argtypes = [c.c_void_p, c.c_uint32, c.c_void_p, c.c_uint32,
        c.c_void_p, c.c_uint32, c.POINTER(c.c_uint32), c.c_void_p]
    kernel.DeviceIoControl.restype = c.c_int32
    kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [c.c_void_p], c.c_int32
    return kernel


def _device_number(kernel, handle, expected):
    response, returned = (c.c_uint32 * 3)(), c.c_uint32()
    ok = kernel.DeviceIoControl(handle, IOCTL_STORAGE_GET_DEVICE_NUMBER, None, 0,
                               c.byref(response), c.sizeof(response), c.byref(returned), None)
    error = c.get_last_error() if not ok else None
    if not ok:
        raise OSError(error, "storage device-number query failed; no retry")
    _require(returned.value == 12 and response[0] == FILE_DEVICE_DISK
             and response[1] == expected and response[2] in (0, 0xFFFFFFFF),
             "disk interface no longer matches the attested PhysicalDrive alias")
    return {"device_type": int(response[0]), "device_number": int(response[1]),
            "partition_number": int(response[2]), "bytes_returned": int(returned.value)}


class QuietBufferedRomTransport(WindowsBufferedRomTransport):
    """Same buffered exchanges, with explicit cached selection and live PnP checks.

    No parent constructor is called: that constructor runs disk/media discovery.
    Higher-level callers must still verify their RAM plugin identity and audit.
    Construction emits only INQUIRY; it does not retry, install, or reset.
    """
    def __init__(self, attestation: RomDiskAttestation, *, slot: int, profile: str = "ram-probe"):
        if os.name != "nt" or c.sizeof(c.c_void_p) != 8:
            raise OSError("quiet buffered transport requires 64-bit Windows Python")
        _require(type(attestation) is RomDiskAttestation, "immutable RomDiskAttestation required")
        _require(type(slot) is int and slot in RAM_SLOTS, "known RAM plugin slot required")
        validate_profile_request(INQUIRY, None, 36, slot=slot, profile=profile)
        started = time.perf_counter_ns()
        self._handle = None
        self._c, self.slot, self.profile = c, slot, profile
        self.adapter_descriptor = self.last_transfer = None
        self.failed = False
        self._exchange_lock = threading.Lock()
        api = _cfgmgr32()
        selected = _metadata_snapshot(api, attestation)
        self.attestation, self.disk = selected, selected.discovery_dict()
        self.opened_interface = selected.interface_path
        self._kernel = kernel = _kernel32()
        handle = kernel.CreateFileW(self.opened_interface, 0xC0000000, 3, None, 3, 0, None)
        if handle is None or handle == c.c_void_p(-1).value:
            raise OSError(c.get_last_error(), "cannot open attested ROM disk interface (administrator access required)")
        self._handle = handle
        try:
            self.storage_device_number = _device_number(kernel, handle, selected.device_number)
            self.device_number = self.storage_device_number["device_number"]
            inquiry = self.exchange(INQUIRY, read_length=36)
            vendor = inquiry[8:16].decode("ascii").strip()
            product = inquiry[16:32].decode("ascii").strip()
            _require((vendor, product) == ("WL82", "UBOOT1.00"), "unexpected attested disk INQUIRY")
            self.inquiry = {"vendor": vendor, "product": product, "raw_hex": inquiry.hex()}
            # Detect removal/re-enumeration while CreateFile/metadata/INQUIRY ran.
            _metadata_snapshot(api, selected)
            self.open_metadata = {"backend": "spt-buffered", "selection": "cfgmgr32-attested",
                "opened_interface": self.opened_interface, "attestation": selected.summary(),
                "storage_device_number": dict(self.storage_device_number),
                "started_monotonic_ns": started, "finished_monotonic_ns": time.perf_counter_ns(),
                "win32_diskdrive_queries": 0, "discovery_fallback": False}
        except Exception:
            self.close()
            raise
