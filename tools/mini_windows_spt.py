"""Bounded Windows buffered SCSI transport; import never accesses a device.

The inherited constructor retains the reviewed PhysicalDrive/USB-ancestry
selection and exact WL82 / UBOOT1.00 INQUIRY. Only the transfer mechanism
changes: IOCTL_SCSI_PASS_THROUGH with a relative in-packet data offset.
No command retry, backend fallback, elevation or automatic reset is supplied.

Microsoft sources and limits: docs/MINI_WINDOWS_SPT.md.
"""
from __future__ import annotations

import ctypes as c
from dataclasses import dataclass
import threading
import time

from tools.probe_mini_recovery import RomCommandError, WindowsRomTransport
from tools.mini_windows_aligned import query_adapter_descriptor, validate_profile_request

# CTL_CODE(FILE_DEVICE_CONTROLLER, 0x0401, METHOD_BUFFERED,
#          FILE_READ_ACCESS | FILE_WRITE_ACCESS), ntddscsi.h.
IOCTL_SCSI_PASS_THROUGH = 0x0004D004
MAX_DATA_BYTES = 4096
MAX_PACKET_BYTES = 8192
SENSE_BYTES = 32
TIMEOUT_SECONDS = 10


class ScsiPassThrough64(c.Structure):
    """Native 64-bit SCSI_PASS_THROUGH; ULONG remains 32 bits on Windows."""
    _fields_ = [
        ("length", c.c_uint16), ("scsi_status", c.c_uint8),
        ("path_id", c.c_uint8), ("target_id", c.c_uint8), ("lun", c.c_uint8),
        ("cdb_length", c.c_uint8), ("sense_info_length", c.c_uint8),
        ("data_in", c.c_uint8), ("data_transfer_length", c.c_uint32),
        ("timeout_value", c.c_uint32), ("data_buffer_offset", c.c_uint64),
        ("sense_info_offset", c.c_uint32), ("cdb", c.c_uint8 * 16),
    ]


def _check_layout() -> None:
    expected = {"length": 0, "scsi_status": 2, "data_in": 8,
                "data_transfer_length": 12, "timeout_value": 16,
                "data_buffer_offset": 24, "sense_info_offset": 32, "cdb": 36}
    if c.sizeof(ScsiPassThrough64) != 56 or any(
            getattr(ScsiPassThrough64, name).offset != at for name, at in expected.items()):
        raise ValueError("unexpected 64-bit SCSI_PASS_THROUGH layout")


@dataclass
class BufferedPacket:
    """Own the allocation until the synchronous DeviceIoControl has returned."""
    buffer: c.Array
    header: ScsiPassThrough64
    data_offset: int
    sense_offset: int
    data_length: int
    total_length: int
    cdb: bytes
    data_in: int


def build_buffered_packet(cdb: bytes, data_out: bytes | None, read_length: int,
                          *, alignment_mask: int, maximum_transfer_length: int) -> BufferedPacket:
    """Build a packet only; the profile validator remains mandatory before I/O."""
    _check_layout()
    if (not isinstance(cdb, bytes) or not 1 <= len(cdb) <= 16 or
            not isinstance(read_length, int) or isinstance(read_length, bool) or read_length < 0 or
            data_out is not None and (not isinstance(data_out, bytes) or read_length)):
        raise ValueError("invalid buffered CDB or unidirectional data phase")
    if (not isinstance(alignment_mask, int) or isinstance(alignment_mask, bool) or
            not 0 <= alignment_mask <= 4095 or alignment_mask & (alignment_mask + 1)):
        raise ValueError("unsupported bounded adapter alignment mask")
    size = len(data_out) if data_out is not None else read_length
    if (not isinstance(maximum_transfer_length, int) or maximum_transfer_length < 1 or
            not 1 <= size <= min(MAX_DATA_BYTES, maximum_transfer_length)):
        raise ValueError("buffered transfer exceeds the nonempty 4096-byte/adapter bound")
    sense_at = c.sizeof(ScsiPassThrough64)
    data_at = (sense_at + SENSE_BYTES + alignment_mask) & ~alignment_mask
    total = data_at + size
    if data_at < sense_at + SENSE_BYTES or total > MAX_PACKET_BYTES:
        raise ValueError("buffered SCSI packet is outside its allocation bound")
    buffer = (c.c_ubyte * total)()  # Zero header padding, sense, gap, and IN data.
    header = ScsiPassThrough64.from_buffer(buffer)
    header.length, header.cdb_length = sense_at, len(cdb)
    # Match the established disk transport. The class/port driver fills the
    # actual path, target, and LUN; these are not trusted response pointers.
    header.target_id = 1
    header.sense_info_length, header.sense_info_offset = SENSE_BYTES, sense_at
    header.timeout_value = TIMEOUT_SECONDS
    header.data_in = int(data_out is None)
    header.data_transfer_length, header.data_buffer_offset = size, data_at
    header.cdb[:len(cdb)] = cdb
    if data_out is not None:
        buffer[data_at:total] = data_out
    return BufferedPacket(buffer, header, data_at, sense_at, size, total, cdb, header.data_in)


def _details(packet: BufferedPacket, returned: int) -> dict:
    s = packet.header
    # Never follow returned offsets. On error output can be incomplete; retain
    # bounded diagnostics only and do not accept any payload.
    present = max(0, min(SENSE_BYTES, int(s.sense_info_length), returned - packet.sense_offset))
    return {"transport": "spt-buffered", "ioctl": IOCTL_SCSI_PASS_THROUGH,
            "scsi_status": int(s.scsi_status), "data_transfer_length": int(s.data_transfer_length),
            "bytes_returned": returned, "packet_bytes": packet.total_length,
            "sense_info_length": int(s.sense_info_length), "sense_bytes_returned": present,
            "sense_hex": bytes(packet.buffer[packet.sense_offset:packet.sense_offset+present]).hex(),
            "data_buffer_offset": int(s.data_buffer_offset),
            "sense_info_offset": int(s.sense_info_offset)}


def parse_buffered_response(packet: BufferedPacket, returned: int) -> bytes:
    """Reject malformed offsets/status/underruns before returning IN bytes."""
    s, details = packet.header, _details(packet, returned)

    def fail(message):
        raise RomCommandError(message + "; no retry", submitted=True, details=details)

    if not c.sizeof(ScsiPassThrough64) <= returned <= packet.total_length:
        fail("invalid buffered SCSI bytes_returned")
    if (s.length != c.sizeof(ScsiPassThrough64) or
            s.data_buffer_offset != packet.data_offset or s.sense_info_offset != packet.sense_offset or
            s.cdb_length != len(packet.cdb) or bytes(s.cdb[:s.cdb_length]) != packet.cdb or
            s.sense_info_length > SENSE_BYTES or s.data_in != packet.data_in):
        fail("buffered SCSI response altered packet layout")
    if s.scsi_status:
        fail(f"SCSI status {int(s.scsi_status):02x}, sense={details['sense_hex']}")
    if s.data_transfer_length != packet.data_length:
        fail(f"short/invalid SCSI transfer: {int(s.data_transfer_length)}/{packet.data_length}")
    if packet.data_in:
        end = packet.data_offset + packet.data_length
        if returned < end:
            fail("buffered SCSI IN payload not covered by bytes_returned")
        return bytes(packet.buffer[packet.data_offset:end])
    return b""  # OUT need not echo the submitted data in the returned packet.


class WindowsBufferedRomTransport(WindowsRomTransport):
    """Explicit opt-in buffered backend with unchanged command validators.

    Construction opens the selected disk, reads its adapter descriptor, and
    performs the inherited identity check. It is never constructed on import
    and does not select itself following a failed DIRECT command.
    """

    def __init__(self, path: str, *, slot: int, profile: str = "ram-probe"):
        self.adapter_descriptor = None
        self.last_transfer = None
        self.failed = False
        self._exchange_lock = threading.Lock()
        super().__init__(path, slot=slot, profile=profile)

    def exchange(self, cdb: bytes, data_out: bytes | None = None, read_length: int = 0) -> bytes:
        validate_profile_request(cdb, data_out, read_length, slot=self.slot, profile=self.profile)
        if self._handle is None:
            raise OSError("ROM transport is closed")
        if self.failed:
            raise RomCommandError("buffered transport failed previously; no retry on this handle", submitted=False)
        if not self._exchange_lock.acquire(blocking=False):
            raise RuntimeError("only one synchronous exchange per transport")
        try:
            return self._exchange_once(cdb, data_out, read_length)
        finally:
            self._exchange_lock.release()

    def _exchange_once(self, cdb, data_out, read_length):
        # Preflight the local size/direction/layout before even a property query.
        build_buffered_packet(cdb, data_out, read_length, alignment_mask=0,
                              maximum_transfer_length=MAX_DATA_BYTES)
        if self.adapter_descriptor is None:
            try:
                self.adapter_descriptor = query_adapter_descriptor(self._kernel, self._handle, c=self._c)
            except Exception:
                self.failed = True
                raise
        packet = build_buffered_packet(
            cdb, data_out, read_length,
            alignment_mask=self.adapter_descriptor["alignment_mask"],
            maximum_transfer_length=self.adapter_descriptor["maximum_transfer_length"])
        returned = self._c.c_uint32()
        details = {"backend": "spt-buffered", "cdb_hex": cdb.hex(),
                   "requested_bytes": packet.data_length, "direction": "in" if packet.data_in else "out",
                   "packet_bytes": packet.total_length, "data_buffer_offset": packet.data_offset,
                   "sense_info_offset": packet.sense_offset, "timeout_seconds": TIMEOUT_SECONDS,
                   "alignment_mask": self.adapter_descriptor["alignment_mask"],
                   "started_monotonic_ns": time.perf_counter_ns()}
        self.last_transfer = details
        try:
            ok = self._kernel.DeviceIoControl(
                self._handle, IOCTL_SCSI_PASS_THROUGH,
                self._c.byref(packet.buffer), packet.total_length,
                self._c.byref(packet.buffer), packet.total_length,
                self._c.byref(returned), None)
            win32_error = self._c.get_last_error() if not ok else None
        except Exception:
            self.failed = True
            raise
        details.update(_details(packet, returned.value))
        details.update({"finished_monotonic_ns": time.perf_counter_ns(),
                        "ioctl_ok": bool(ok), "win32_error": win32_error})
        if not ok:
            self.failed = True
            raise RomCommandError(win32_error, "buffered SCSI command failed; no automatic retry",
                                  submitted=True, details=details)
        try:
            return parse_buffered_response(packet, returned.value)
        except RomCommandError as error:
            self.failed = True
            error.details.update(details)
            raise
