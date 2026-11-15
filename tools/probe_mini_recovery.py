"""Inspect MINI recovery evidence and construct offline RAM protocol vectors.

The CLI is offline. WindowsRomTransport is an explicit library API, restricted
to an identified ROM disk and one RAM slot. Reviewed RAM/reset plugins use the
same bounded upload; no MIDI mode-change or NVM-write CDB is supplied.
Importing this module or running its CLI never opens a device. The MINI's USB entry branch is evidenced by stock bytes;
the mask-ROM callback ABI/slots remain AC791N reference evidence until observed
on the actual MINI. Do not turn a protocol vector into a readiness claim.
"""
from __future__ import annotations

import argparse
import binascii
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc, jlfs_entry
from tools.disassemble import codec, table

STOCK_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
RAM_SLOTS = (0x01C20000, 0x01C28000)
SLOT_BYTES = 0x8000
SOFT_KEY_SYSEX = bytes.fromhex("f0 22 24 35 7d f7")
SOFT_KEY_USB = bytes.fromhex("04 f0 22 24 07 35 7d f7")
MFLASHER_COMMIT = "8fbece7348d758ac284325eed455781675ac95ff"
MFLASHER_SOURCE_SHA = {
    "src/jl.rs": "874f589c2c49f30dae7ec25213d2c45d6ce40d349e5e66e174654a451b4de3ca",
    "src/usb.rs": "efc429fc1c957ba3d99fc3b1d0bd5cca76284c2c6300162389572f995bb0403f",
    "src/scsi.rs": "aaa28596096bb3aea5c0b00cd3af0eb794b0fb6c5964113ac78c34c824a50e9a",
    "src/midi.rs": "9e1dd61fdf59ea9c65d5d7d2f98319fef703bc7aa435c01e082e6d6ad4a05980",
}
USB_CRC_MAGIC = bytes.fromhex("c3 cf c0 e8 ce d2 b0 ae c4 e3 a3 ac d3 f1 c1 d6")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def usb_crc_transform(data: bytes, key: int = 0xFFFFFFFF) -> bytes:
    """CRC stream used by ROM FB06/FD07; NOT ENC/SFC or flash encryption.

    Restart the stream independently for each <=512-byte upload block.
    The operation is symmetric; it does not modify the supplied buffer.
    """
    if not 0 <= key <= 0xFFFFFFFF:
        raise ValueError("USB stream key must fit uint32")
    state = binascii.crc_hqx((key >> 16).to_bytes(2, "little"), key & 0xFFFF)
    out = bytearray()
    for index, byte in enumerate(data):
        state = binascii.crc_hqx(USB_CRC_MAGIC[index % 16:index % 16 + 1], state)
        out.append(byte ^ (state & 255))
    return bytes(out)


def _slot_range(address: int, length: int, slot: int, limit: int) -> None:
    if slot not in RAM_SLOTS or not 1 <= length <= limit:
        raise ValueError("require a known 32KiB reference slot and bounded nonempty transfer")
    if not slot <= address < slot + SLOT_BYTES or length > slot + SLOT_BYTES - address:
        raise ValueError("transfer exceeds the selected RAM slot")


def _cdb(opcode: int, arguments: bytes) -> bytes:
    # These are RAM upload, normal-call entry and OUR bounded plugin read only.
    # No generic arbitrary command/flash command helper is provided.
    if opcode not in (0xFB06, 0xFB08, 0xFD07, 0xFC60, 0xFD61, 0xFC70, 0xFD71, 0xFC72, 0xFC73) or len(arguments) > 14:
        raise ValueError("unsupported offline RAM command")
    return opcode.to_bytes(2, "big") + arguments + b"\xff" * (14 - len(arguments))


def ram_write_cdb(address: int, transmitted: bytes, *, slot: int) -> bytes:
    """FB06 OUT CDB; CRC covers already transformed bytes, not plain image."""
    _slot_range(address, len(transmitted), slot, 512)
    if address & 3:
        raise ValueError("upload address must be word aligned")
    args = struct.pack(">IH", address, len(transmitted)) + b"\0"
    args += binascii.crc_hqx(transmitted, 0).to_bytes(2, "little")
    return _cdb(0xFB06, args)


def ram_jump_cdb(entry: int) -> bytes:
    """FB08, target argument1, 16-byte IN reply; entry is FIRST flat byte."""
    if entry not in RAM_SLOTS:
        raise ValueError("entry must be the first byte of a reference plugin slot")
    return _cdb(0xFB08, struct.pack(">IH", entry, 1))


def ram_read_cdb(address: int, length: int, *, slot: int) -> bytes:
    """FD61 belongs to the uploaded plugin, not an established MINI ROM opcode."""
    _slot_range(address, length, slot, 4096)
    return _cdb(0xFD61, struct.pack(">IH", address, length))


def rom_read_cdb(address: int, length: int, *, slot: int) -> bytes:
    """FD07 reference ROM readback, <=512 bytes within selected plugin slot.

    FD07 returns CRC-stream-transformed bytes, restarted for each command.
    This is explicit in the original installer's reboot readback and matches
    all ten captured MINI readback block hashes. No flash/SFC read is supplied.
    """
    _slot_range(address, length, slot, 512)
    return _cdb(0xFD07, struct.pack(">IH", address, length))


def validate_ram_request(cdb: bytes, data_out: bytes | None, read_length: int, *, slot: int) -> None:
    """Reject all commands outside INQUIRY and the bounded RAM protocol."""
    if slot not in RAM_SLOTS or read_length < 0 or (data_out is not None and read_length):
        raise ValueError("invalid slot or transfer direction")
    if cdb == bytes((0x12, 0, 0, 0, 36, 0)) and data_out is None and read_length == 36:
        return
    if len(cdb) != 16:
        raise ValueError("RAM private CDB must contain exactly 16 bytes")
    opcode = int.from_bytes(cdb[:2], "big")
    address, length = struct.unpack_from(">IH", cdb, 2)
    if opcode == 0xFB06 and data_out is not None and not read_length:
        expected = ram_write_cdb(address, data_out, slot=slot)
    elif opcode == 0xFB08 and data_out is None and read_length == 16 and address == slot:
        expected = ram_jump_cdb(slot)
    elif opcode in (0xFD07, 0xFD61) and data_out is None and read_length == length:
        expected = (rom_read_cdb if opcode == 0xFD07 else ram_read_cdb)(address, length, slot=slot)
    elif opcode == 0xFC60 and data_out is None and read_length == 16:
        expected = _cdb(0xFC60, b"")
    else:
        raise ValueError("command/direction not in the RAM-only allowlist")
    if cdb != expected:
        raise ValueError("malformed RAM request, length or transmitted-data CRC mismatch")


def nor_read_cdb(address: int, length: int) -> bytes:
    """Custom HYRN read; physical offsets, at most512 bytes, one-MiB MINI only."""
    if not 0 <= address < 0x100000 or not 1 <= length <= 512 or length > 0x100000 - address:
        raise ValueError("NOR read exceeds the MINI one-MiB range or512-byte transfer")
    return _cdb(0xFD71, struct.pack(">IH", address, length))


def validate_nor_request(cdb: bytes, data_out: bytes | None, read_length: int, *, slot: int) -> None:
    """Explicit reader profile: RAM upload + HYRN info/init/read/status only."""
    if cdb == bytes((0x12, 0, 0, 0, 36, 0)) or cdb[:2] in (b"\xfb\x06", b"\xfb\x08", b"\xfd\x07"):
        validate_ram_request(cdb, data_out, read_length, slot=slot)
        return
    if len(cdb) != 16 or data_out is not None:
        raise ValueError("NOR reader only accepts its bounded IN commands")
    opcode = int.from_bytes(cdb[:2], "big")
    if opcode in (0xFC70, 0xFC72, 0xFC73) and read_length == 16:
        expected = _cdb(opcode, b"")
    elif opcode == 0xFD71:
        address, length = struct.unpack_from(">IH", cdb, 2)
        if read_length != length:
            raise ValueError("NOR read length differs from data phase")
        expected = nor_read_cdb(address, length)
    else:
        raise ValueError("not a custom HYRN reader command")
    if cdb != expected:
        raise ValueError("malformed NOR reader request")


def discover_windows_rom_disks() -> list[dict]:
    """Read Windows disk/PnP metadata only; never probe arbitrary disk CDBs."""
    import os
    import subprocess
    if os.name != "nt":
        raise OSError("Windows PnP discovery is available only on Windows")
    script = r'''
$ErrorActionPreference = 'Stop'
$romDisks = @(foreach ($disk in Get-CimInstance Win32_DiskDrive) {
    $node = $disk.PNPDeviceID
    $chain = @()
    for ($depth = 0; $depth -lt 12 -and $node; $depth++) {
        $chain += $node
        if ($node -match '^USB\\VID_4C4A&PID_8057(?:&|\\)') {
            [pscustomobject]@{path=$disk.DeviceID; pnp_id=$disk.PNPDeviceID; usb_ancestor=$node; model=$disk.Model; chain=$chain}
            break
        }
        try { $node = (Get-PnpDeviceProperty -InstanceId $node -KeyName DEVPKEY_Device_Parent -ErrorAction Stop).Data }
        catch { break }
    }
})
ConvertTo-Json -InputObject $romDisks -Depth 5 -Compress
'''
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                            check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    disks = json.loads(result.stdout)
    if not isinstance(disks, list):
        raise ValueError("unexpected PnP discovery output")
    return disks


class WindowsRomTransport:
    """Explicit SPTD handle, only after PnP USB ancestry AND INQUIRY checks.

    Constructor performs read-only INQUIRY. The calling root workflow must
    choose the physical disk explicitly; no elevation, reset or retries occur.
    This class is never constructed by the CLI; tests replace every Windows API.
    """
    def __init__(self, path: str, *, slot: int, profile: str = "ram-probe"):
        import ctypes as c
        from ctypes import wintypes as w
        import os
        if os.name != "nt" or c.sizeof(c.c_void_p) != 8:
            raise OSError("this reviewed SPTD layout requires 64-bit Windows Python")
        if profile not in ("ram-probe", "ram-engine", "ram-codec", "ram-codec-board",
                           "ram-receive", "ram-entry-recovery", "nor-reader"):
            raise ValueError("unknown transport profile")
        if slot not in RAM_SLOTS or not re.fullmatch(r"\\\\\.\\PhysicalDrive\d+", path, re.I):
            raise ValueError("select an explicit PhysicalDrive and known plugin slot")
        candidates = [disk for disk in discover_windows_rom_disks() if disk["path"].lower() == path.lower()]
        if len(candidates) != 1:
            raise ValueError("disk is not uniquely under USB 4C4A:8057; refusing to open it")
        self.slot, self.disk, self._handle, self.profile = slot, candidates[0], None, profile

        class Sptd(c.Structure):
            _fields_ = [("length", c.c_uint16), ("scsi_status", c.c_uint8), ("path_id", c.c_uint8),
                        ("target_id", c.c_uint8), ("lun", c.c_uint8), ("cdb_length", c.c_uint8),
                        ("sense_info_length", c.c_uint8), ("data_in", c.c_uint8),
                        ("data_transfer_length", c.c_uint32), ("timeout_value", c.c_uint32),
                        ("data_buffer", c.c_void_p), ("sense_info_offset", c.c_uint32), ("cdb", c.c_uint8 * 16)]

        class WithSense(c.Structure):
            _fields_ = [("sptd", Sptd), ("sense", c.c_uint8 * 32)]

        if c.sizeof(Sptd) != 56 or Sptd.data_buffer.offset != 24 or Sptd.cdb.offset != 36 or WithSense.sense.offset != 56:
            raise ValueError("unexpected native SCSI_PASS_THROUGH_DIRECT layout")
        self._c, self._sptd, self._packet = c, Sptd, WithSense
        kernel = c.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
        kernel.CreateFileW.restype = w.HANDLE
        kernel.DeviceIoControl.argtypes = [w.HANDLE, w.DWORD, c.c_void_p, w.DWORD, c.c_void_p,
                                           w.DWORD, c.POINTER(c.c_uint32), c.c_void_p]
        kernel.DeviceIoControl.restype = w.BOOL
        kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [w.HANDLE], w.BOOL
        self._kernel = kernel
        handle = kernel.CreateFileW(path, 0xC0000000, 3, None, 3, 0, None)
        if handle == c.c_void_p(-1).value:
            raise OSError(c.get_last_error(), "cannot open identified ROM disk (administrator access may be needed)")
        self._handle = handle
        try:
            inquiry = self.exchange(bytes((0x12, 0, 0, 0, 36, 0)), read_length=36)
            vendor, product = inquiry[8:16].decode("ascii").strip(), inquiry[16:32].decode("ascii").strip()
            if (vendor, product) != ("WL82", "UBOOT1.00"):
                raise ValueError(f"unexpected disk INQUIRY: {vendor!r} {product!r}")
            self.inquiry = {"vendor": vendor, "product": product, "raw_hex": inquiry.hex()}
        except Exception:
            self.close()
            raise

    def exchange(self, cdb: bytes, data_out: bytes | None = None, read_length: int = 0) -> bytes:
        if self.profile == "ram-engine":
            from probe_mini_engine import validate_engine_request
            validator = validate_engine_request
        elif self.profile == "ram-codec":
            from probe_mini_codec import validate_codec_request
            validator = validate_codec_request
        elif self.profile == "ram-codec-board":
            from tools.probe_mini_codec_board import validate_codec_board_request
            validator = validate_codec_board_request
        elif self.profile == "ram-receive":
            from tools.probe_mini_receive import validate_receive_request
            validator = validate_receive_request
        elif self.profile == "ram-entry-recovery":
            from tools.probe_mini_entry_recovery import validate_entry_recovery_request
            validator = validate_entry_recovery_request
        else:
            validator = validate_ram_request if self.profile == "ram-probe" else validate_nor_request
        validator(cdb, data_out, read_length, slot=self.slot)
        if self._handle is None:
            raise OSError("ROM transport is closed")
        c = self._c
        size = len(data_out) if data_out is not None else read_length
        if not size:
            raise ValueError("no empty USB data phase is emitted")
        buffer = (c.c_ubyte * size)()
        if data_out is not None:
            buffer[:] = data_out
        packet = self._packet()
        s = packet.sptd
        s.length, s.target_id, s.cdb_length = c.sizeof(self._sptd), 1, len(cdb)
        s.sense_info_length, s.sense_info_offset = 32, self._packet.sense.offset
        s.timeout_value, s.data_in = 10, 0 if data_out is not None else 1
        s.data_transfer_length, s.data_buffer = size, c.addressof(buffer)
        s.cdb[:len(cdb)] = cdb
        returned = c.c_uint32()
        ok = self._kernel.DeviceIoControl(self._handle, 0x4D014, c.byref(packet), c.sizeof(packet),
                                         c.byref(packet), c.sizeof(packet), c.byref(returned), None)
        if not ok:
            # Capture thread-local Win32 status before any other Windows API.
            # SPTD output fields may be incomplete when the ioctl fails: retain
            # them as diagnostic evidence, without accepting any data payload.
            win32_error = c.get_last_error()
            details = {"scsi_status": int(s.scsi_status),
                       "data_transfer_length": int(s.data_transfer_length),
                       "bytes_returned": int(returned.value),
                       "sense_info_length": int(s.sense_info_length),
                       "sense_hex": bytes(packet.sense).hex()}
            raise RomCommandError(win32_error, "SCSI command failed; no automatic retry",
                                  submitted=True, details=details)
        if s.scsi_status:
            raise RomCommandError(f"SCSI status {int(s.scsi_status):02x}, sense={bytes(packet.sense).hex()}", submitted=True)
        if s.data_transfer_length != size:
            raise RomCommandError(f"short SCSI transfer: {s.data_transfer_length}/{size}; no retry", submitted=True)
        return bytes(buffer) if data_out is None else b""

    def close(self) -> None:
        if self._handle is not None:
            self._kernel.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class RomCommandError(OSError):
    """A transport error annotated only after DeviceIoControl was invoked."""
    def __init__(self, *args, submitted: bool = False, details: dict | None = None):
        super().__init__(*args)
        self.submitted = submitted
        self.details = dict(details) if details is not None else {}


def validate_reset_artifact(image: bytes, elf: bytes, manifest: dict, *, slot: int) -> dict:
    """Bind a reviewed tiny reset manifest to its linked pi32v2 bytes.

    This validates identity/layout, not the MMIO semantics of arbitrary code.
    The manifest must come from the separately reviewed reset-only build.
    """
    if (manifest.get("kind") != "mini-ram-reset" or manifest.get("slot") != slot or
            manifest.get("entry") != slot or manifest.get("no_flash_writes") is not True or
            manifest.get("image_bytes") != len(image) or manifest.get("image_sha256") != sha(image) or
            manifest.get("elf_sha256") != sha(elf)):
        raise ValueError("reset manifest does not bind this slot, image and ELF")
    offline_upload_plan(image, slot)
    if not 1 <= len(image) <= 512 or len(elf) < 52 or elf[:7] != b"\x7fELF\x01\x01\x01":
        raise ValueError("reset requires a tiny linked ELF32 little-endian image")
    h = struct.unpack_from("<HHIIIIIHHHHHH", elf, 16)
    if (h[:4] != (2, 0xF1, 1, slot) or h[7:10] != (52, 32, 1) or
            h[4] < 52 or h[4] + 32 > len(elf)):
        raise ValueError("reset ELF has wrong target, first-byte entry or load table")
    typ, offset, va, pa, size, memory, flags, align = struct.unpack_from("<8I", elf, h[4])
    if (typ != 1 or va != slot or pa != slot or size != len(image) or memory != size or not flags & 1 or
            offset + size > len(elf) or elf[offset:offset + size] != image or
            align not in (0, 1) and (align & (align - 1) or offset % align != va % align)):
        raise ValueError("reset ELF payload differs, has BSS, or leaves its slot")
    if h[11]:
        if h[10] != 40 or h[5] < 52 or h[5] + 40 * h[11] > len(elf):
            raise ValueError("reset ELF has a malformed section table")
        for index in range(h[11]):
            section = struct.unpack_from("<10I", elf, h[5] + index * 40)
            if section[1] in (4, 9) and section[5]:
                raise ValueError("reset ELF retains relocation records")
            if section[2] & 2 and section[5]:
                if not (va <= section[3] and section[5] <= va + size - section[3] and
                        section[1] != 8 and section[4] == offset + section[3] - va):
                    raise ValueError("reset allocated section is not backed by its flat payload")
    return {"kind": "mini-ram-reset", "slot": slot, "entry": slot,
            "image_bytes": len(image), "image_sha256": sha(image), "elf_sha256": sha(elf),
            "no_flash_writes": True, "elf_layout_verified": True}


class MiniRamSession:
    """Small stateful RAM-only workflow, with a mockable exchange transport.

    known_free_slot is caller evidence from a fresh ROM re-enumeration or an
    independently tracked live slot. It cannot be inferred from INQUIRY alone.
    No callback plugin / FM1 loader is automatically selected or downloaded.
    """
    def __init__(self, transport, *, slot: int, known_free_slot: bool = False,
                 known_uploaded_unstarted: bool = False):
        if slot not in RAM_SLOTS or (known_free_slot and known_uploaded_unstarted):
            raise ValueError("invalid RAM slot or conflicting slot history")
        self.transport, self.slot = transport, slot
        self.known_free_slot, self.started, self.failed, self.ready = known_free_slot, False, False, False
        self.known_uploaded_unstarted = known_uploaded_unstarted

    def _handshake(self) -> dict:
        identity = self.transport.exchange(_cdb(0xFC60, b""), read_length=16)
        if len(identity) != 16 or identity[:2] != b"\xfc\x60" or identity[6:10] != b"HYR1":
            raise ValueError("uploaded HyperRig plugin identity was not confirmed")
        count, status, version = struct.unpack_from(">I", identity, 2)[0], struct.unpack_from(">I", identity, 10)[0], int.from_bytes(identity[14:16], "big")
        if status or version != 1 or count == 0:
            raise ValueError(f"RAM plugin selftest failed/unsupported: count={count},status={status},version={version}")
        return {"selftest_answer_hex": identity.hex(), "selftest_count": count,
                "selftest_status": status, "selftest_version": version}

    def upload_only(self, image: bytes, *, expected_sha256: str) -> dict:
        """FB06 only: no verification, jump, selftest or peripheral setup."""
        if not self.known_free_slot or self.started or self.failed:
            raise ValueError("need a known free slot and a fresh, nonfailed session")
        if sha(image) != expected_sha256:
            raise ValueError("flat plugin hash differs from reviewed build manifest")
        plan = offline_upload_plan(image, self.slot)
        self.known_free_slot = False
        try:
            for offset in range(0, len(image), 512):
                block = usb_crc_transform(image[offset:offset + 512])
                cdb = ram_write_cdb(self.slot + offset, block, slot=self.slot)
                self.transport.exchange(cdb, data_out=block)
            self.known_uploaded_unstarted = True
            return {"slot": self.slot, "image_sha256": plan["image_sha256"],
                    "image_bytes": len(image), "upload_completed": True, "jump_sent": False,
                    "readback_verified": False, "flash_write_commands_sent": False}
        except Exception:
            self.failed = True
            raise

    def verify_upload_only(self, image: bytes, *, expected_sha256: str) -> dict:
        """Read an already uploaded, never-executed slot; emit FD07 only.

        The caller must have a complete command history proving no FB08 was
        issued to this image. A fresh object does not reset that device fact.
        Decoding is mandatory, not guessed from whichever comparison passes.
        """
        if not self.known_uploaded_unstarted or self.started or self.failed:
            raise ValueError("need a known uploaded but never-started slot")
        if sha(image) != expected_sha256:
            raise ValueError("flat plugin hash differs from reviewed build manifest")
        plan = offline_upload_plan(image, self.slot)
        try:
            readback, wire = bytearray(), bytearray()
            for offset in range(0, len(image), 512):
                length = min(512, len(image) - offset)
                reply = self.transport.exchange(rom_read_cdb(self.slot + offset, length, slot=self.slot), read_length=length)
                if len(reply) != length:
                    raise ValueError("short ROM FD07 readback; refusing to jump")
                wire.extend(reply)
                readback.extend(usb_crc_transform(reply))
            if bytes(readback) != image:
                raise ValueError("ROM FD07 readback differs; refusing to jump")
            return {"slot": self.slot, "image_sha256": plan["image_sha256"],
                    "rom_readback_sha256": sha(readback), "rom_wire_sha256": sha(wire),
                    "rom_readback_transform": "jl_crc_cipher keyffffffff, restart per FD07 command",
                    "image_bytes": len(image), "readback_verified": True, "jump_sent": False,
                    "flash_write_commands_sent": False}
        except Exception:
            self.failed = True
            raise

    def verify_and_start(self, image: bytes, *, expected_sha256: str) -> dict:
        """Verify a never-executed upload again, then issue exactly one FB08."""
        verified = self.verify_upload_only(image, expected_sha256=expected_sha256)
        try:
            self.started = True  # set BEFORE exchange: a lost reply must not cause another jump
            self.known_uploaded_unstarted = False
            reply = self.transport.exchange(ram_jump_cdb(self.slot), read_length=16)
            if len(reply) != 16 or reply[:2] != b"\xfb\x08":
                raise ValueError("FB08 did not echo; execution state is ambiguous")
            # Match the primary host's settling interval, without masking errors.
            import time
            time.sleep(0.1)
            identity = self._handshake()
            self.ready = True
            return {**verified, "jump_sent": True, "jump_answer_hex": reply.hex(), **identity,
                    "flash_write_commands_sent": False, "spi_initialized": False}
        except Exception:
            self.failed = True
            raise

    def upload_and_start(self, image: bytes, *, expected_sha256: str) -> dict:
        self.upload_only(image, expected_sha256=expected_sha256)
        return self.verify_and_start(image, expected_sha256=expected_sha256)

    def start_reset_once(self, image: bytes, *, elf: bytes, manifest: dict) -> dict:
        """Verify a reviewed reset-only upload; one jump, no plugin handshake.

        A post-submission transport error is recorded as ambiguous, never as a
        successful reset. Pre-submission and readback errors still raise.
        The caller must independently observe normal MINI USB re-enumeration.
        """
        artifact = validate_reset_artifact(image, elf, manifest, slot=self.slot)
        verified = self.verify_upload_only(image, expected_sha256=artifact["image_sha256"])
        self.started, self.known_uploaded_unstarted = True, False
        result = {**verified, "reset_artifact": artifact, "jump_sent": True,
                  "reset_completion_verified": False, "normal_mini_usb_identity_required": True,
                  "automatic_retry": False, "spi_initialized": False}
        try:
            reply = self.transport.exchange(ram_jump_cdb(self.slot), read_length=16)
        except RomCommandError as error:
            self.failed = True
            if not error.submitted:
                raise
            return {**result, "jump_outcome": "post_submit_transport_error",
                    "error_type": type(error).__name__, "error": str(error),
                    "transport_details": error.details}
        except Exception:
            self.failed = True
            raise
        valid_echo = len(reply) == 16 and reply[:2] == b"\xfb\x08"
        if not valid_echo:
            self.failed = True
        return {**result, "jump_outcome": "fb08_echo_received" if valid_echo else "unexpected_reply",
                "jump_answer_hex": reply.hex()}

    def read(self, address: int, length: int) -> bytes:
        _slot_range(address, length, self.slot, SLOT_BYTES)
        if not self.ready or self.failed:
            raise ValueError("plugin handshake required before FD61 reads")
        result = bytearray()
        try:
            for offset in range(0, length, 4096):
                size = min(4096, length - offset)
                reply = self.transport.exchange(ram_read_cdb(address + offset, size, slot=self.slot), read_length=size)
                if len(reply) != size:
                    raise ValueError("short plugin read")
                result.extend(reply)
        except Exception:
            self.failed = True
            raise
        return bytes(result)


class MiniNorSession(MiniRamSession):
    """Separate HYRN read-only NOR session; init SPI is an explicit later step.

    Upload/start only registers the reader and checks FC70. initialize_spi()
    performs the driver's bounded PIO/JEDEC setup. No flash write/erase/status
    register command exists. All-FF reads are trusted only after FC73 success.
    """
    def __init__(self, transport, *, slot: int, known_free_slot: bool = False,
                 known_uploaded_unstarted: bool = False):
        super().__init__(transport, slot=slot, known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        self.initialized, self.capacity, self.successful_bytes = False, 0, 0

    def _handshake(self) -> dict:
        reply = self.transport.exchange(_cdb(0xFC70, b""), read_length=16)
        if (len(reply) != 16 or reply[:6] != b"\xfc\x70HYRN" or reply[6:8] != b"\x01\x03" or
                int.from_bytes(reply[8:12], "big") != self.slot or int.from_bytes(reply[12:16], "big") != SLOT_BYTES):
            raise ValueError("HYRN reader identity/slot/version mismatch")
        return {"reader_identity_hex": reply.hex(), "reader_version": 1, "reader_read_only_pio": True}

    def _status(self, expected_bytes: int) -> dict:
        reply = self.transport.exchange(_cdb(0xFC73, b""), read_length=16)
        if (len(reply) != 16 or reply[:4] != b"\xfc\x73\x00\x01" or
                int.from_bytes(reply[12:16], "big") != expected_bytes):
            raise ValueError(f"NOR reader error/stale byte count; block discarded: {reply.hex()}")
        return {"sys_div": int.from_bytes(reply[4:8], "big"), "clk_con2": int.from_bytes(reply[8:12], "big"),
                "successful_read_bytes": expected_bytes}

    def initialize_spi(self) -> dict:
        if not self.ready or self.failed or self.initialized:
            raise ValueError("need a fresh identified HYRN reader before SPI initialization")
        try:
            reply = self.transport.exchange(_cdb(0xFC72, b""), read_length=16)
            if (len(reply) != 16 or reply[:4] != b"\xfc\x72\x00\x01" or reply[7] != 15 or
                    reply[4:7] in (bytes(3), b"\xff" * 3) or reply[6] != 20 or
                    int.from_bytes(reply[8:12], "big") != 0x100000 or reply[12:16] != bytes(4)):
                raise ValueError(f"MINI JEDEC/one-MiB capacity/initialization mismatch: {reply.hex()}")
            status = self._status(0)
            self.capacity, self.initialized = 0x100000, True
            return {"jedec_hex": reply[4:7].hex(), "capacity": self.capacity, "baud_divisor": 15, **status}
        except Exception:
            self.failed = True
            raise

    def read(self, address: int, length: int) -> bytes:
        raise ValueError("HYRN uses read_flash() with physical offsets, not FD61 RAM reads")

    def read_flash(self, address: int, length: int, progress=None) -> bytes:
        if not self.initialized or self.failed:
            raise ValueError("identified/initialized HYRN reader required")
        if not 0 <= address < self.capacity or not 1 <= length <= self.capacity - address:
            raise ValueError("flash range outside confirmed physical capacity")
        result = bytearray()
        try:
            for offset in range(0, length, 512):
                size = min(512, length - offset)
                reply = self.transport.exchange(nor_read_cdb(address + offset, size), read_length=size)
                if len(reply) != size:
                    raise ValueError("short NOR read; block discarded")
                total = self.successful_bytes + size
                self._status(total)
                self.successful_bytes = total
                result.extend(reply)
                if progress is not None:
                    progress(len(result), length)
        except Exception:
            self.failed = True
            raise
        return bytes(result)


def offline_upload_plan(image: bytes, slot: int, occupied_slots: tuple[int, ...] = ()) -> dict:
    """Pure plan, no transport or proof that any slot is free on a real MINI.

    A caller must separately validate the ELF's first-byte entry, complete
    initialized image, BSS/private workspace and live slot before execution.
    An absent occupied slot list does not prove fresh ROM state.
    """
    _slot_range(slot, len(image), slot, SLOT_BYTES)
    if image.startswith(b"\x7fELF"):
        raise ValueError("ROM requires a validated flat image, not an ELF file")
    if any(value not in RAM_SLOTS for value in occupied_slots):
        raise ValueError("unknown occupied slot")
    if slot in occupied_slots:
        raise ValueError("refusing to overwrite an occupied plugin slot")
    blocks = []
    for offset in range(0, len(image), 512):
        plain = image[offset:offset + 512]
        transmitted = usb_crc_transform(plain)
        blocks.append({"address": slot + offset, "length": len(plain), "direction": "out",
                       "cdb_hex": ram_write_cdb(slot + offset, transmitted, slot=slot).hex(),
                       "plain_sha256": sha(plain), "transmitted_sha256": sha(transmitted)})
    return {"offline_only": True, "hardware_execution_authorized_by_this_plan": False,
            "mini_rom_slots_observed": False, "live_slot_state_verified": False,
            "flat_entry_and_workspace_validated": False, "image_sha256": sha(image),
            "image_bytes": len(image), "slot": slot, "blocks": blocks,
            "jump": {"cdb_hex": ram_jump_cdb(slot).hex(), "direction": "in", "bytes": 16,
                     "reference_settle_ms": 100, "retry_after_ambiguous_failure": False}}


@lru_cache(maxsize=1)
def _isa():
    return table.load()


def _decode(raw: bytes, address: int) -> dict[int, tuple[str, int]]:
    isa = _isa()
    decoded, offset = {}, 0
    while offset < len(raw):
        item = codec.decode(isa, raw, offset)
        if item is None:
            raise ValueError(f"unknown stock instruction at {address + offset:#x}")
        instruction, fields, size = item
        decoded[address + offset] = (codec.format(instruction, fields), size)
        offset += size
    return decoded


def _fragment(app: bytes, start: int, end: int) -> bytes:
    offset = start - 0x02000000 if start >= 0x02000000 else 0x6ED20 + start - 0x01C00000
    return app[offset:offset + end - start]


def usb_entry_branch_model(app: bytes, packet: bytes) -> bool:
    """Execute the decoded MINI command guard until the recovery call.

    This is a narrow control-flow model: stack saves are skipped and the
    independently inspected stock memcmp is modeled. No reset/MMIO executes.
    """
    start, end = 0x0200869A, 0x020086DE
    code = _decode(_fragment(app, start, end), start)
    registers = {f"r{i}": 0 for i in range(16)}
    registers.update(r0=0x1000, r1=len(packet))
    prefix = _fragment(app, 0x01C0AFC4, 0x01C0AFCA)
    pc = start
    for _ in range(32):
        if pc == end:
            return False
        text, size = code[pc]
        following = pc + size
        if text.startswith("[--sp]"):
            pass
        elif match := re.fullmatch(r"(r\d+) = (r\d+|\d+)", text):
            dst, value = match.groups()
            registers[dst] = registers[value] if value.startswith("r") else int(value)
        elif match := re.fullmatch(r"r0 = b\[r5\+(\d+)\] \(u\)", text):
            if registers["r5"] != 0x1000:
                raise ValueError("unexpected stock packet pointer")
            registers["r0"] = packet[int(match[1])]
        elif match := re.fullmatch(r"if \((r\d+) (!=|==) (\d+)\) goto (-?\d+)", text):
            register, comparison, value, displacement = match.groups()
            taken = registers[register] == int(value)
            if comparison == "!=":
                taken = not taken
            if taken:
                following += int(displacement)
        elif text.startswith("call "):
            target = following + int(text.split()[1])
            if target == 0x02034344:
                if registers["r0"] != 0x1000 or registers["r1"] != 0x01C0AFC4 or registers["r2"] != 6:
                    raise ValueError("stock memcmp arguments changed")
                registers["r0"] = 0 if packet[:6] == prefix else 1
            elif target == 0x01C02332:
                return True
            elif target == 0x02043FCC:
                return False  # different 7F command, not recovery
            else:
                raise ValueError(f"unexpected stock call {target:#x}")
        else:
            raise ValueError(f"unmodeled command guard instruction: {text}")
        pc = following
    raise ValueError("stock guard instruction budget exceeded")


def inspect_stock(raw: bytes) -> tuple[dict, bytes]:
    if sha(raw) != STOCK_SHA:
        raise ValueError("firmware is not the pinned MINI_009 sample")
    fwsc, files = unpack_fwsc(raw)
    app, _, _ = unpack_app(files["flash.bin"][0x4000:])
    if _fragment(app, 0x01C0AFC4, 0x01C0AFCC) != SOFT_KEY_USB:
        raise ValueError("MINI USB soft-key table changed")
    if _fragment(app, 0x0203FD2A, 0x0203FD3A) != b"usb_update_mode\0":
        raise ValueError("MINI retained marker changed")
    reset = _decode(_fragment(app, 0x01C02332, 0x01C02382), 0x01C02332)
    expected_tail = ["r0 = 29883776", "r1 = 33815850", "rep 4 16 {", "r2 = b[r1++=1] (u)",
                     "b[r0++=1] = r2", "r0 = 160", "r1 = 4", "r2 = 1", "r3 = 1", "call -4852", "goto -2"]
    if [text for text, _ in reset.values()][-11:] != expected_tail:
        raise ValueError("marker copy/P33 reset sequence changed")
    compare = _decode(_fragment(app, 0x02034344, 0x0203437C), 0x02034344)
    if compare[0x02034356][0] != "r3 = b[r1++=1] (u)" or compare[0x02034360][0] != "r0 = r4 - r3":
        raise ValueError("stock byte comparison function changed")
    if not usb_entry_branch_model(app, SOFT_KEY_USB):
        raise ValueError("stock USB branch did not reach recovery")
    variants = [SOFT_KEY_USB[:i] for i in range(8)] + [SOFT_KEY_USB + b"\0"]
    for byte in range(8):
        for bit in range(8):
            wrong = bytearray(SOFT_KEY_USB)
            wrong[byte] ^= 1 << bit
            variants.append(bytes(wrong))
    if any(usb_entry_branch_model(app, packet) for packet in variants):
        raise ValueError("modified USB packet unexpectedly enters recovery")
    ranges = {"usb_endpoint_callback_registration": (0x02007ED0, 0x02007EDE),
              "usb_read_dispatch": (0x02008864, 0x02008880),
              "usb_command_guard": (0x0200869A, 0x020086DE),
              "memcmp": (0x02034344, 0x0203437C),
              "retained_marker_and_reset": (0x01C02332, 0x01C02382),
              "p33_bitfield_helper": (0x01C0108C, 0x01C010B4)}
    ota = files["ota.bin"]
    ota_entry = jlfs_entry(ota, 0)
    return {"package_sha256": STOCK_SHA, "fwsc_chip": fwsc["chip"],
            "mini_usb_recovery_command_static_support": True,
            "sysex_hex": SOFT_KEY_SYSEX.hex(), "usb_midi_event_packets_hex": SOFT_KEY_USB.hex(),
            "transport": "USB MIDI cable0, two event packets received together (8 bytes)",
            "guard_model_positive_cases": 1, "guard_model_negative_cases": len(variants),
            "marker_source": "0x0203fd2a", "marker_destination": "0x01c7fd80", "marker_bytes": 16,
            "reset_path": "P33 bitfield helper(0xa0,4,1,1), then wait loop; never executed by this tool",
            "ble_route_to_usb_handler_verified": False,
            "fragments": {name: {"start": hex(start), "end_exclusive": hex(end),
                                    "sha256": sha(_fragment(app, start, end)),
                                    "instructions": [text for text, _ in _decode(_fragment(app, start, end), start).values()]}
                          for name, (start, end) in ranges.items()},
            "stock_updater": {"fwsc_name": "ota.bin", "bytes": len(ota), "sha256": sha(ota),
                              "inner_entry": ota_entry.to_dict(),
                              "is_rom_callback_plugin": False,
                              "reason": "staged usb_hid_ota.bin container, not the normal-call flat ROM plugin ABI"}}, app


def report() -> dict:
    stock, _ = inspect_stock((ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes())
    sources = ["upstream/m-bootloader/docs/SPEC.md", "upstream/m-bootloader/src/loader_target.c",
               "upstream/pi32v2-isa/tools/hwtest/runner.S", "upstream/pi32v2-isa/tools/hwtest/README.md",
               "recovered/installer/jltech.uboot.dis.txt", "recovered/installer/jltech.cipher.dis.txt",
               "recovered/installer/tankg_install.dis.txt",
               "recovered/installer/tankg_install.constants.json"]
    sample = bytes(range(32))
    transformed = usb_crc_transform(sample)
    return {"target": "TANK MINI_009", "offline_only": True, "stock": stock,
            "reference_rom_abi": {"entry": "first byte of flat image; normal C call, r0 points to params",
                "parameters": {"0": "send callback", "4": "receive callback", "8": "handler-pointer slot address"},
                "handler": "int handler(CBW31 *r0, answer16 *r1): 1 handled, 0 defer to ROM",
                "cbw": {"signature_le": "0x43425355", "tag_offset": 4, "transfer_count_le_offset": 8,
                        "flags_offset": 12, "cdb_length_offset": 14, "cdb_offset": 15},
                "callbacks": "pointer,length in r0/r1; chunks<=512; short/error return semantics unknown",
                "response": "plugin sends reply using supplied answer buffer; ROM sends CSW",
                "slots": [hex(slot) for slot in RAM_SLOTS], "slot_bytes": SLOT_BYTES,
                "known_source_devices": ["FM-1", "SMK-37"], "mini_observed": False,
                "preserve": ["ROM stack", "clocks", "interrupt state", "USB service", "other RAM"],
                "initialize": "own BSS/state explicitly; no application startup or global RAM clearing"},
            "protocol": {"upload": "FB06, <=512 bytes transformed independently, CRC16/XMODEM over transmitted data",
                "jump": "FB08 entryBE32,targetBE16=1; IN16; ambiguous result must not trigger blind retry",
                "plugin_read": "FD61, addressBE32,lengthBE16; own slot only; <=4096 command, <=512 callback",
                "rom_read": "FD07 returns jl_crc_cipher transformed bytes; keyffffffff restarts per command; full plain comparison required",
                "rom_read_evidence": "installer reboot lines2786/2791 and all10 captured MINI block hashes on2026-11-15",
                "flash_read": "FD05 requires initialized flash loader; RAM/SFC reads are not a raw flash backup"},
            "host_library": {"profiles": ["ram-probe", "nor-reader"],
                "ram": ["upload_only", "verify_upload_only", "verify_and_start", "upload_and_start", "read"],
                "existing_upload_requires": "explicit known_uploaded_unstarted history, full fresh FD07 readback before jump",
                "nor": {"identity": "FC70/HYRN", "explicit_init": "FC72", "read": "FD71 physical1MiB/max512B",
                        "status": "FC73 after each read; sticky error or incorrect byte count discards data"},
                "reset": "start_reset_once binds manifest+ELF+flat, rereads RAM, one FB08, no HYR1; USB normal identity must be verified separately",
                "all_device_io_requires_explicit_api_construction": True,
                "cli_opens_device": False},
            "windows": {"vid": "4c4a", "pid": "8057", "inquiry_vendor": "WL82", "inquiry_product": "UBOOT1.00",
                "transport": "SCSI_PASS_THROUGH_DIRECT via IOCTL0x4d014 on identified PhysicalDrive; no manual CBW",
                "descriptor_error43_is_usable_transport": False},
            "vectors": {"plain_hex": sample.hex(), "transformed_hex": transformed.hex(),
                "write_cdb_hex": ram_write_cdb(RAM_SLOTS[0], transformed, slot=RAM_SLOTS[0]).hex(),
                "jump_cdb_hex": ram_jump_cdb(RAM_SLOTS[0]).hex(),
                "read_cdb_hex": ram_read_cdb(RAM_SLOTS[0], 16, slot=RAM_SLOTS[0]).hex()},
            "mflasher_primary_sources": {"commit": MFLASHER_COMMIT, "source_sha256": MFLASHER_SOURCE_SHA,
                "url": f"https://github.com/jvitkauskas/m-flasher/tree/{MFLASHER_COMMIT}",
                "read_only_source_inspection": True, "binaries_used": False,
                "mini_in_midi_allowlist": False},
            "local_source_sha256": {path: sha((ROOT / path).read_bytes()) for path in sources},
            "tool_sha256": sha(Path(__file__).read_bytes()),
            "device_command_sent": False, "mode_changed": False, "hardware_execution_verified": False,
            "raw_flash_backup_acquired": False, "recovery_after_corrupt_flash_verified": False,
            "boot_ready": False, "flashable": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "research/mini-recovery.json")
    parser.add_argument("--ram-image", type=Path, help="inspect an already validated flat plugin; never uploads it")
    parser.add_argument("--slot", type=lambda value: int(value, 0), choices=RAM_SLOTS, default=RAM_SLOTS[0])
    args = parser.parse_args()
    result = report()
    if args.ram_image:
        result["offline_upload_plan"] = offline_upload_plan(args.ram_image.read_bytes(), args.slot)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("MINI_009 USB recovery command confirmed from stock instructions; no command sent.")
    print("ROM ABI/slots remain reference evidence; no hardware boot or complete backup claimed.")
    print(f"Offline report: {args.report}")


if __name__ == "__main__":
    main()
