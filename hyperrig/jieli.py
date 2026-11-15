"""Offline parsers for JieLi ENC, SFC, JLFS and FWSC.

References and independent validation are recorded in docs/REVERSE_ENGINEERING.md.
This module never accesses a USB device or writes firmware to hardware.
"""

from __future__ import annotations

import binascii
import hashlib
import struct
from dataclasses import asdict, dataclass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc16(data: bytes) -> int:
    return binascii.crc_hqx(data, 0)


def enc(data: bytes, key: int = 0xFFFF) -> bytes:
    out = bytearray(data)
    for i in range(len(out)):
        out[i] ^= key & 255
        key = ((key << 1) ^ (0x1021 if key & 0x8000 else 0)) & 0xFFFF
    return bytes(out)


def sfc(data: bytes, key: int = 0x980F) -> bytes:
    """Transform an application area starting at its own offset zero."""
    return b"".join(enc(data[o:o + 32], key ^ (o >> 2))
                    for o in range(0, len(data), 32))


@dataclass(frozen=True)
class Entry:
    name: str
    header_offset: int
    offset: int
    size: int
    flags: int
    reserved: int
    index: int
    data_crc: int

    def to_dict(self) -> dict:
        return asdict(self)


def jlfs_entry(data: bytes, offset: int) -> Entry:
    if offset < 0 or offset + 32 > len(data):
        raise ValueError("truncated JLFS directory entry")
    hcrc, dcrc, addr, size, flags, reserved, index, name = struct.unpack_from(
        "<HHIIBBH16s", data, offset)
    if crc16(data[offset + 2:offset + 32]) != hcrc:
        raise ValueError(f"JLFS header CRC mismatch at 0x{offset:x}")
    name = name.split(b"\0", 1)[0].decode("ascii")
    if not name or any(c in name for c in "/\\:") or name in (".", ".."):
        raise ValueError("invalid JLFS filename")
    return Entry(name, offset, addr, size, flags, reserved, index, dcrc)


def unpack_app(raw: bytes, key: int = 0x980F) -> tuple[bytes, list[Entry], dict[str, bytes]]:
    """Decode an application-area slice, validating all directory and payload CRCs.

    Entry offsets with flags 0x82 are relative to this slice. VM/BTIF/USR
    offsets are physical flash addresses. The head offset is a CPU address.
    They are intentionally not treated as one address space.
    """
    if len(raw) < 32:
        raise ValueError("application area too short")
    head = jlfs_entry(enc(raw[:32], key), 0)
    if head.name != "app_area_head" or head.flags != 0x83:
        raise ValueError("not an app_area_head")
    if not 32 <= head.size <= len(raw):
        raise ValueError("application size outside supplied slice")
    cipher_end = min((head.size + 31) & ~31, len(raw))
    plain = sfc(raw[:cipher_end], key) + raw[cipher_end:]
    if crc16(plain[32:head.size]) != head.data_crc:
        raise ValueError("application-area data CRC mismatch")
    entries, files = [head], {}
    for off in range(32, min(head.size, 4096), 32):
        e = jlfs_entry(plain, off)
        entries.append(e)
        if e.flags == 0x82:
            if e.offset < off + 32 or e.offset + e.size > head.size:
                raise ValueError(f"{e.name}: payload outside application")
            payload = plain[e.offset:e.offset + e.size]
            if crc16(payload) != e.data_crc:
                raise ValueError(f"{e.name}: data CRC mismatch")
            if e.name in files:
                raise ValueError("duplicate JLFS filename")
            files[e.name] = payload
        if e.index:
            break
    else:
        raise ValueError("unterminated JLFS directory")
    if "app.bin" not in files:
        raise ValueError("app.bin missing")
    return plain, entries, files


def unpack_fwsc(raw: bytes) -> tuple[dict, dict[str, bytes]]:
    """Read a FWSC directory; report raw CRC status for opaque auxiliary entries.

    Auxiliary entries may carry an additional encoding. A raw CRC mismatch
    on those is retained as evidence, not described as proven corruption.
    The application-bearing flash.bin must pass its CRC.
    """
    directory = b"".join(raw[o:o + 47] for o in range(0, 1392, 48))[:1344]
    if len(directory) != 1344:
        raise ValueError("truncated FWSC directory")
    header = enc(directory[:64])
    hcrc, list_crc, size, count, a, b, chip = struct.unpack("<HHIHHI48s", header)
    if crc16(header[2:]) != hcrc:
        raise ValueError("FWSC header CRC mismatch")
    if not 1 <= count <= 16 or size + 20 != len(raw):
        raise ValueError("FWSC length or entry count mismatch")
    files, records = {}, []
    for i in range(count):
        e = enc(directory[64 + i * 80:144 + i * 80])
        kind, index, dcrc, w1, off, length, length2, w2, name = struct.unpack(
            "<HHHHIII44s16s", e)
        name = name.split(b"\0", 1)[0].decode("ascii")
        if not name or any(c in name for c in "/\\:") or name in (".", ".."):
            raise ValueError("invalid FWSC filename")
        if name in files or off + length > size:
            raise ValueError("FWSC duplicate name or bounds error")
        payload = raw[20 + off:20 + off + length]
        valid = crc16(payload) == dcrc
        if name == "flash.bin" and not valid:
            raise ValueError("FWSC flash.bin CRC mismatch")
        records.append(dict(name=name, type=kind, offset=off + 20, size=length,
                            raw_crc_ok=valid, sha256=sha256(payload)))
        files[name] = payload
    return {"chip": chip.split(b"\0", 1)[0].decode("ascii"),
            "sha256": sha256(raw), "entries": records}, files
