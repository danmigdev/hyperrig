"""Explicit, aligned SCSI DIRECT transport for the identified MINI ROM disk.

Import and the CLI are offline. Only constructing WindowsAlignedRomTransport
opens the explicitly selected disk: the frozen parent still checks USB ancestry
and INQUIRY. No command is retried. This is an allocation experiment, not proof
that alignment caused the observed Win32 error31 (the actual adapter mask is 0).
"""
from __future__ import annotations

import ctypes
import importlib
import json
from pathlib import Path
import struct
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
# Older frozen probe modules use a tools-local import spelling. Preserve their
# import contract without editing them or performing discovery during import.
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools.probe_mini_recovery import RomCommandError, WindowsRomTransport

IOCTL_STORAGE_QUERY_PROPERTY = 0x002D1400
IOCTL_SCSI_PASS_THROUGH_DIRECT = 0x0004D014
PAGE_BYTES = 4096
MAX_DESCRIPTOR_BYTES = 4096
MAX_ALIGNMENT = 1024 * 1024
MAX_BUFFER_BYTES = 1024 * 1024
SOURCES = {
    "direct": "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through_direct",
    "sptd": "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ns-ntddscsi-_scsi_pass_through_direct",
    "adapter": "https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-storage_adapter_descriptor",
    "query": "https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-storage_property_query",
}

# Same operation validators as the frozen parent. Only dispatch is shared with
# the separate buffered experiment; none of these validators is broadened.
_PROFILE_VALIDATORS = {
    "ram-probe": ("tools.probe_mini_recovery", "validate_ram_request"),
    "nor-reader": ("tools.probe_mini_recovery", "validate_nor_request"),
    "ram-engine": ("tools.probe_mini_engine", "validate_engine_request"),
    "ram-codec": ("tools.probe_mini_codec", "validate_codec_request"),
    "ram-codec-board": ("tools.probe_mini_codec_board", "validate_codec_board_request"),
    "ram-receive": ("tools.probe_mini_receive", "validate_receive_request"),
    "ram-entry-recovery": ("tools.probe_mini_entry_recovery", "validate_entry_recovery_request"),
    "ram-codec-rom": ("tools.probe_mini_codec_rom", "validate_codec_rom_request"),
    "app-writer-observer": ("tools.probe_mini_app_writer", "validate_writer_observer_request"),
    "app-writer-operational": ("tools.install_mini_app", "validate_writer_operational_request"),
}


def validate_profile_request(cdb, data_out, read_length, *, slot, profile):
    if profile not in _PROFILE_VALIDATORS:
        raise ValueError("unknown transport profile")
    module, name = _PROFILE_VALIDATORS[profile]
    getattr(importlib.import_module(module), name)(cdb, data_out, read_length, slot=slot)


def parse_adapter_descriptor(raw: bytes) -> dict:
    """Parse one complete Windows8+ descriptor, without OS or device access."""
    if len(raw) < 32:
        raise ValueError("short STORAGE_ADAPTER_DESCRIPTOR")
    version, size, maximum_transfer_length, maximum_physical_pages, mask = struct.unpack_from("<5I", raw)
    if not 32 <= version <= size <= MAX_DESCRIPTOR_BYTES or size != len(raw):
        raise ValueError("unsupported/inconsistent adapter descriptor version or size")
    if mask & (mask + 1) or mask + 1 > MAX_ALIGNMENT:
        raise ValueError("unsupported adapter alignment mask")
    if not maximum_transfer_length or not maximum_physical_pages:
        raise ValueError("adapter did not declare usable transfer limits")
    if any(value not in (0, 1) for value in raw[20:24]):
        raise ValueError("invalid adapter boolean metadata")
    return {
        "version": version, "size": size,
        "maximum_transfer_length": maximum_transfer_length,
        "maximum_physical_pages": maximum_physical_pages,
        "alignment_mask": mask, "adapter_uses_pio": bool(raw[20]),
        "adapter_scans_down": bool(raw[21]), "command_queueing": bool(raw[22]),
        "accelerated_transfer": bool(raw[23]), "bus_type": raw[24],
        "bus_major_version": struct.unpack_from("<H", raw, 26)[0],
        "bus_minor_version": struct.unpack_from("<H", raw, 28)[0],
        "srb_type": raw[30], "address_type": raw[31], "raw_hex": raw.hex(),
    }


def query_adapter_descriptor(kernel, handle, *, c=ctypes) -> dict:
    """Two bounded read-only metadata IOCTLs; no SCSI command and no fallback.

    The caller owns an explicitly opened handle. The first query obtains the
    header, the second the complete declared descriptor. A failed/truncated or
    changing response aborts before INQUIRY or any plugin command is submitted.
    """
    class Query(c.Structure):
        _fields_ = [("property_id", c.c_uint32), ("query_type", c.c_uint32),
                    ("additional_parameters", c.c_uint8 * 1)]

    if c.sizeof(Query) != 12:
        raise ValueError("unexpected STORAGE_PROPERTY_QUERY layout")
    query = Query(1, 0)  # StorageAdapterProperty / PropertyStandardQuery.

    def fetch(size):
        response = (c.c_uint8 * size)()
        returned = c.c_uint32()
        ok = kernel.DeviceIoControl(handle, IOCTL_STORAGE_QUERY_PROPERTY,
                                    c.byref(query), c.sizeof(query), c.byref(response), size,
                                    c.byref(returned), None)
        if not ok:
            error = c.get_last_error()  # First operation after the failed API.
            raise RomCommandError(error, "adapter property query failed; no SCSI command submitted",
                                  submitted=False, details={"phase": "adapter-query", "requested_bytes": size,
                                                            "bytes_returned": int(returned.value)})
        if returned.value != size:
            raise ValueError("incomplete/oversized adapter property response")
        return bytes(response)

    header = fetch(8)
    version, size = struct.unpack("<II", header)
    if not 32 <= version <= size <= MAX_DESCRIPTOR_BYTES:
        raise ValueError("unsupported/bounds-invalid adapter descriptor header")
    raw = fetch(size)
    if raw[:8] != header:
        raise ValueError("adapter descriptor changed between queries")
    result = parse_adapter_descriptor(raw)
    result["bytes_returned"] = size
    result["query_output_sizes"] = [8, size]
    return result


class AlignedBuffer:
    """Own the backing allocation and aligned ctypes view until synchronous I/O ends."""
    def __init__(self, size: int, alignment: int):
        if (type(size) is not int or not 1 <= size <= MAX_BUFFER_BYTES or
                type(alignment) is not int or not PAGE_BYTES <= alignment <= MAX_ALIGNMENT or
                alignment & (alignment - 1)):
            raise ValueError("bounded size and power-of-two alignment >=4096 required")
        self.size, self.alignment = size, alignment
        self.storage = (ctypes.c_uint8 * (size + alignment - 1))()
        self.raw_address = ctypes.addressof(self.storage)
        self.address = (self.raw_address + alignment - 1) & -alignment
        self.offset = self.address - self.raw_address
        self.view = (ctypes.c_uint8 * size).from_buffer(self.storage, self.offset)
        if self.address % alignment or self.offset + size > ctypes.sizeof(self.storage):
            raise AssertionError("aligned buffer bounds")


class WindowsAlignedRomTransport(WindowsRomTransport):
    """Same profile/identity checks and 10s timeout; query + page-aligned DIRECT.

    `adapter_descriptor` and `last_transfer` contain diagnostic metadata only.
    The runner should persist last_transfer after each exchange or error. A
    failed I/O poisons this handle; a subsequent command requires an explicit
    new identified transport. No reopen, retry, reset or timing policy is here.
    """
    def __init__(self, path: str, *, slot: int, profile: str = "ram-probe"):
        self.adapter_descriptor = None
        self.last_transfer = None
        self.failed = False
        self._exchange_lock = threading.Lock()
        super().__init__(path, slot=slot, profile=profile)

    def exchange(self, cdb: bytes, data_out: bytes | None = None, read_length: int = 0) -> bytes:
        validate_profile_request(cdb, data_out, read_length, slot=self.slot, profile=self.profile)
        if self._handle is None or self.failed:
            raise OSError("aligned ROM transport is closed or terminal after an I/O failure")
        if not self._exchange_lock.acquire(blocking=False):
            raise RuntimeError("only one synchronous exchange per transport")
        try:
            return self._exchange_once(cdb, data_out, read_length)
        finally:
            self._exchange_lock.release()

    def _exchange_once(self, cdb, data_out, read_length):
        c = self._c
        if self.adapter_descriptor is None:
            try:
                self.adapter_descriptor = query_adapter_descriptor(self._kernel, self._handle, c=c)
            except Exception:
                self.failed = True
                raise
        adapter = self.adapter_descriptor
        size = len(data_out) if data_out is not None else read_length
        if not 1 <= size <= min(MAX_BUFFER_BYTES, adapter["maximum_transfer_length"]):
            raise ValueError("transfer exceeds declared adapter limit")
        # A page-aligned start makes this a conservative upper bound on the
        # physical pages needed, independent of physical contiguity.
        pages = (size + PAGE_BYTES - 1) // PAGE_BYTES
        if pages > adapter["maximum_physical_pages"]:
            raise ValueError("transfer exceeds declared physical-page count")
        alignment = max(PAGE_BYTES, adapter["alignment_mask"] + 1)
        buffer = AlignedBuffer(size, alignment)
        if data_out is not None:
            buffer.view[:] = data_out
        packet = self._packet()
        s = packet.sptd
        s.length, s.target_id, s.cdb_length = c.sizeof(self._sptd), 1, len(cdb)
        s.sense_info_length, s.sense_info_offset = 32, self._packet.sense.offset
        s.timeout_value, s.data_in = 10, 0 if data_out is not None else 1
        s.data_transfer_length, s.data_buffer = size, buffer.address
        s.cdb[:len(cdb)] = cdb
        returned = c.c_uint32()
        details = {
            "backend": "sptd-page-aligned", "cdb_hex": cdb.hex(), "requested_bytes": size,
            "direction": "out" if data_out is not None else "in",
            "data_buffer_address": buffer.address, "allocation_address": buffer.raw_address,
            "allocation_bytes": c.sizeof(buffer.storage), "allocation_offset": buffer.offset,
            "data_buffer_alignment": alignment, "alignment_mask": adapter["alignment_mask"],
            "data_buffer_offset_4k": buffer.address % PAGE_BYTES, "span_pages_4k": pages,
            "sptd_bytes": c.sizeof(self._sptd), "packet_bytes": c.sizeof(packet),
            "timeout_seconds": 10, "started_monotonic_ns": time.perf_counter_ns(),
        }
        self.last_transfer = details
        try:
            ok = self._kernel.DeviceIoControl(self._handle, IOCTL_SCSI_PASS_THROUGH_DIRECT,
                                              c.byref(packet), c.sizeof(packet), c.byref(packet),
                                              c.sizeof(packet), c.byref(returned), None)
            win32_error = c.get_last_error() if not ok else None  # Capture immediately.
        except Exception:
            self.failed = True
            raise
        details.update({"finished_monotonic_ns": time.perf_counter_ns(), "ioctl_ok": bool(ok),
                        "win32_error": win32_error, "scsi_status": int(s.scsi_status),
                        "data_transfer_length": int(s.data_transfer_length),
                        "bytes_returned": int(returned.value), "sense_info_length": int(s.sense_info_length),
                        "sense_hex": bytes(packet.sense).hex()})
        details["elapsed_ns"] = details["finished_monotonic_ns"] - details["started_monotonic_ns"]
        if not ok:
            self.failed = True
            raise RomCommandError(win32_error, "aligned SCSI command failed; no retry",
                                  submitted=True, details=details)
        if (s.scsi_status or s.data_transfer_length != size or s.sense_info_length > 32 or
                not c.sizeof(self._sptd) <= returned.value <= c.sizeof(packet)):
            self.failed = True
            raise RomCommandError("invalid/short aligned SCSI completion; no retry", submitted=True, details=details)
        return bytes(buffer.view) if data_out is None else b""


if __name__ == "__main__":
    print(json.dumps({"mode": "offline", "device_io": False, "backend": "sptd-page-aligned",
                      "minimum_alignment": PAGE_BYTES, "adapter_query_required": True,
                      "automatic_retries": 0, "alignment_causality_proven": False,
                      "sources": SOURCES}, indent=2))
