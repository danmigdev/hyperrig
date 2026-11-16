"""One explicit hub-port cycle for the recorded MINI descriptor-error devnode.

Import/default/check-only are offline. --execute requires administrator rights
and a NEW durable JSONL log. Only the fixed parent hub interface is opened;
there is no disk, serial, firmware, driver-package or whole-hub operation.
"""
from __future__ import annotations

import argparse
import ctypes as c
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
from uuid import UUID

LEAF = r"USB\VID_0000&PID_0002\A&89DE0B7&0&1"
HUB = r"USB\VID_1A40&PID_0101\9&F2E5FBE&0&2"
PORT, PROBLEM = 1, 43
HUB_GUID = "f18a0e88-c30c-11d0-8815-00a0c906bed8"
IOCTL_USB_HUB_CYCLE_PORT = (0x22 << 16) | (273 << 2)  # 0x220444
TIMEOUT_MS, CANCEL_WAIT_MS = 20000, 3000
ERROR_IO_PENDING, ERROR_IO_INCOMPLETE, WAIT_TIMEOUT = 997, 996, 258
_attempted = False
_attempt_lock = threading.Lock()
# An OVERLAPPED buffer must survive until its request completes. A driver that
# ignores cancellation leaves these objects alive until this process exits.
_pending = []
SOURCES = {
    "ioctl": "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ni-usbioctl-ioctl_usb_hub_cycle_port",
    "params": "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ns-usbioctl-_usb_cycle_port_params",
    "header": "https://raw.githubusercontent.com/microsoft/win32metadata/main/generation/WinSDK/RecompiledIdlHeaders/shared/usbioctl.h",
    "definitions": "https://raw.githubusercontent.com/microsoft/win32metadata/main/generation/WinSDK/RecompiledIdlHeaders/shared/usbiodef.h",
    "port_address": "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-device_registry_property",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


class Guid(c.Structure):
    _fields_ = [("a", c.c_uint32), ("b", c.c_uint16), ("d", c.c_uint16), ("e", c.c_ubyte*8)]


class PropertyKey(c.Structure):
    _fields_ = [("guid", Guid), ("pid", c.c_uint32)]


class CycleParams(c.Structure):
    _fields_ = [("ConnectionIndex", c.c_uint32), ("StatusReturned", c.c_uint32)]


class Overlapped(c.Structure):
    _fields_ = [("Internal", c.c_size_t), ("InternalHigh", c.c_size_t),
                ("Offset", c.c_uint32), ("OffsetHigh", c.c_uint32), ("hEvent", c.c_void_p)]


def guid(value):
    return Guid.from_buffer_copy(UUID(value).bytes_le)


def cfgmgr32():
    api = c.WinDLL("cfgmgr32", use_last_error=True)
    u, ptr = c.c_uint32, c.POINTER
    signatures = {
        "CM_Locate_DevNodeW": [ptr(u), c.c_wchar_p, u],
        "CM_Get_Parent": [ptr(u), u, u],
        "CM_Get_Device_ID_Size": [ptr(u), u, u],
        "CM_Get_Device_IDW": [u, c.c_wchar_p, u, u],
        "CM_Get_DevNode_Status": [ptr(u), ptr(u), u, u],
        "CM_Get_DevNode_PropertyW": [u, ptr(PropertyKey), ptr(u), ptr(c.c_ubyte), ptr(u), u],
        "CM_Get_Device_Interface_List_SizeW": [ptr(u), ptr(Guid), c.c_wchar_p, u],
        "CM_Get_Device_Interface_ListW": [ptr(Guid), c.c_wchar_p, c.c_wchar_p, u, u],
    }
    for name, args in signatures.items():
        method = getattr(api, name)
        method.argtypes, method.restype = args, u
    return api


def kernel32():
    api = c.WinDLL("kernel32", use_last_error=True)
    h, u, b, p = c.c_void_p, c.c_uint32, c.c_int32, c.POINTER
    signatures = {
        "CreateFileW": ([c.c_wchar_p, u, u, h, u, u, h], h),
        "CreateEventW": ([h, b, b, c.c_wchar_p], h),
        "DeviceIoControl": ([h, u, h, u, h, u, p(u), p(Overlapped)], b),
        "GetOverlappedResultEx": ([h, p(Overlapped), p(u), u, b], b),
        "CancelIoEx": ([h, p(Overlapped)], b),
        "CloseHandle": ([h], b),
        "GetLastError": ([], u),
    }
    for name, (args, result) in signatures.items():
        method = getattr(api, name)
        method.argtypes, method.restype = args, result
    return api


def cm(result, operation):
    if result:
        raise OSError(f"{operation}: CONFIGRET 0x{int(result):08x}; no retry")


def device_id(api, node):
    size = c.c_uint32()
    cm(api.CM_Get_Device_ID_Size(c.byref(size), node, 0), "device ID size")
    require(0 < size.value < 200, "invalid device ID extent")
    text = c.create_unicode_buffer(size.value+1)
    cm(api.CM_Get_Device_IDW(node, text, len(text), 0), "device ID")
    require(len(text.value) == size.value, "device ID changed during query")
    return text.value


def status(api, node):
    flags, problem = c.c_uint32(), c.c_uint32()
    cm(api.CM_Get_DevNode_Status(c.byref(flags), c.byref(problem), node, 0), "devnode status")
    return flags.value, problem.value


def metadata_snapshot(api):
    """Only exact leaf/parent CM metadata; no global PnP or disk enumeration."""
    leaf, parent = c.c_uint32(), c.c_uint32()
    cm(api.CM_Locate_DevNodeW(c.byref(leaf), LEAF, 0), "locate exact failed leaf")
    require(device_id(api, leaf.value).casefold() == LEAF.casefold(), "failed leaf identity changed")
    flags, problem = status(api, leaf.value)
    require(problem == PROBLEM and flags & 0x400, "leaf no longer reports Code 43")
    key = PropertyKey(guid("a45c254e-df1c-4efd-8020-67d146a850e0"), 30)
    kind, size, address = c.c_uint32(), c.c_uint32(4), (c.c_ubyte*4)()
    cm(api.CM_Get_DevNode_PropertyW(leaf.value, c.byref(key), c.byref(kind), address,
                                  c.byref(size), 0), "leaf USB port address")
    # SDK declares UINT32 (7); the property documentation also lists INT32 (6).
    require(size.value == 4 and kind.value in (6, 7) and int.from_bytes(address, "little") == PORT,
            "leaf USB port is not exactly port 1")
    cm(api.CM_Get_Parent(c.byref(parent), leaf.value, 0), "exact leaf parent")
    require(device_id(api, parent.value).casefold() == HUB.casefold(), "leaf has a different parent hub")
    hub_flags, hub_problem = status(api, parent.value)
    require(hub_flags & 8 and not hub_flags & 0x400 and hub_problem == 0, "parent hub is not healthy/started")
    interface_guid, count = guid(HUB_GUID), c.c_uint32()
    cm(api.CM_Get_Device_Interface_List_SizeW(c.byref(count), c.byref(interface_guid), HUB, 0),
       "present interfaces of exact hub")
    require(3 <= count.value <= 8192, "hub interface list missing or too large")
    buf = c.create_unicode_buffer("\uffff"*count.value, count.value)
    cm(api.CM_Get_Device_Interface_ListW(c.byref(interface_guid), HUB, buf, len(buf), 0),
       "hub interface list")
    multi = "".join(buf)
    require(multi.endswith("\0\0"), "unterminated hub interface list")
    interfaces = multi[:-2].split("\0")
    require(len(interfaces) == 1 and interfaces[0].startswith("\\\\?\\") and
            all(ord(ch) >= 32 for ch in interfaces[0]), "exact hub has no unique present interface")
    return {"leaf": LEAF, "leaf_devinst": leaf.value, "problem_code": problem,
            "leaf_status": flags, "parent": HUB, "parent_devinst": parent.value,
            "parent_status": hub_flags, "port": PORT, "hub_interface": interfaces[0]}


def plan():
    return {"kind": "mini-exact-hub-port-cycle-v1", "leaf": LEAF, "parent": HUB,
            "port": PORT, "required_problem_code": PROBLEM, "interface_guid": HUB_GUID,
            "ioctl": IOCTL_USB_HUB_CYCLE_PORT, "params_bytes": c.sizeof(CycleParams),
            "maximum_cycle_submissions": 1, "automatic_retry": False,
            "io_wait_ms": TIMEOUT_MS, "cancel_wait_ms": CANCEL_WAIT_MS,
            "firmware_write": False, "whole_hub_cycle": False, "driver_change": False,
            "sources": SOURCES,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def cycle_once(log, *, api=None, kernel=None):
    """Explicit execution API. A durable logger must complete before submission."""
    global _attempted
    require(callable(log), "durable event logger required")
    require(not _attempted, "this process already consumed its one cycle attempt")
    if api is None or kernel is None:
        require(os.name == "nt" and c.sizeof(c.c_void_p) == 8, "64-bit Windows required")
        api, kernel = cfgmgr32(), kernel32()
    result = {**plan(), "started_utc": utc(), "cycle_submitted": False,
              "ioctl_success": False, "operation_outcome_unknown": False,
              "reenumeration_verified": False, "ROM_verified": False, "error": None}
    handle = event = None
    params, overlap, returned = CycleParams(PORT, 0xFFFFFFFF), Overlapped(), c.c_uint32()
    pending = False

    def emit(event_name, **fields):
        log({"event": event_name, "utc": utc(), **fields})

    try:
        selected = metadata_snapshot(api)
        result["selected"] = selected
        emit("target_verified", **selected)
        handle = kernel.CreateFileW(selected["hub_interface"], 0x40000000, 3, None, 3, 0x40000000, None)
        require(handle not in (None, 0, c.c_void_p(-1).value), "cannot open exact hub interface")
        event = kernel.CreateEventW(None, 1, 0, None)
        require(event not in (None, 0, c.c_void_p(-1).value), "cannot create private completion event")
        overlap.hEvent = event
        require(metadata_snapshot(api) == selected, "target changed after opening hub")
        emit("cycle_intent", **selected, ioctl=IOCTL_USB_HUB_CYCLE_PORT,
             input_hex=bytes(params).hex(), attempt=1, automatic_retry=False)
        # Recheck after durable intent, immediately before the sole mutating call.
        require(metadata_snapshot(api) == selected, "target changed after cycle intent")
        with _attempt_lock:
            require(not _attempted, "another caller consumed this process's cycle attempt")
            _attempted = result["cycle_submitted"] = True
        result["submitted_utc"] = utc()
        ok = bool(kernel.DeviceIoControl(handle, IOCTL_USB_HUB_CYCLE_PORT,
                    c.byref(params), c.sizeof(params), c.byref(params), c.sizeof(params),
                    c.byref(returned), c.byref(overlap)))
        error = 0 if ok else int(kernel.GetLastError())
        if not ok and error == ERROR_IO_PENDING:
            pending = True
            ok = bool(kernel.GetOverlappedResultEx(handle, c.byref(overlap), c.byref(returned), TIMEOUT_MS, 0))
            error = 0 if ok else int(kernel.GetLastError())
            pending = not ok and error in (WAIT_TIMEOUT, ERROR_IO_INCOMPLETE, ERROR_IO_PENDING)
            if pending:
                result["wait_error"] = error
                cancelled = bool(kernel.CancelIoEx(handle, c.byref(overlap)))
                result["cancel_requested"] = cancelled
                result["cancel_error"] = 0 if cancelled else int(kernel.GetLastError())
                ok = bool(kernel.GetOverlappedResultEx(handle, c.byref(overlap), c.byref(returned), CANCEL_WAIT_MS, 0))
                error = 0 if ok else int(kernel.GetLastError())
                pending = not ok and error in (WAIT_TIMEOUT, ERROR_IO_INCOMPLETE, ERROR_IO_PENDING)
        result.update(ioctl_success=ok, win32_error=error, bytes_returned=returned.value,
                      status_returned=int(params.StatusReturned) if returned.value >= 8 else None,
                      status_returned_observed=returned.value >= 8,
                      operation_outcome_unknown=not ok)
        if returned.value > c.sizeof(params) or (returned.value >= 8 and params.ConnectionIndex != PORT):
            raise ValueError("unexpected cycle response extent or port")
        emit("cycle_result", **{k: result[k] for k in ("ioctl_success", "win32_error", "bytes_returned",
             "status_returned", "status_returned_observed", "operation_outcome_unknown")})
    except Exception as error:
        result["error"] = repr(error)
        if result["cycle_submitted"]:
            result["operation_outcome_unknown"] = True
    finally:
        if pending:
            _pending.append((kernel, handle, event, params, overlap, returned))
            result["pending_io_buffers_retained_until_process_exit"] = True
            result["handles_closed"] = False
        else:
            closed = []
            for value in (event, handle):
                if value not in (None, 0, c.c_void_p(-1).value):
                    closed.append(bool(kernel.CloseHandle(value)))
            result["handles_closed"] = all(closed)
        result["finished_utc"] = utc()
        emit("finished", **result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({**plan(), "mode": "offline-check-only", "device_access": False}, indent=2))
        return 0
    require(args.log is not None, "--execute requires a new --log path")
    # Exclusive creation also prevents accidental replay with the same command.
    with args.log.open("x", encoding="utf-8", newline="\n") as stream:
        def log(event):
            stream.write(json.dumps(event, sort_keys=True)+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        result = cycle_once(log)
    print(json.dumps(result, indent=2))
    return 0 if (result["ioctl_success"] and result["handles_closed"] and not result["error"]
                 and result.get("status_returned") in (None, 0)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
