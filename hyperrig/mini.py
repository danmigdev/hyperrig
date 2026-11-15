"""Tank Mini stock protocol, with a strictly read-only request interface.

Evidence: viniciusapl97/tankmini-linux docs/protocol and captured test vectors;
UltraRig alpha11 installer bytecode independently confirms the frame format.
No firmware compatibility follows from sharing this control protocol.
"""

from __future__ import annotations

import struct
from dataclasses import asdict, dataclass


def pack7(raw: bytes) -> bytes:
    accumulator = bits = 0
    packed = bytearray()
    for byte in raw:
        accumulator |= byte << bits
        bits += 8
        while bits >= 7:
            packed.append(accumulator & 127)
            accumulator >>= 7
            bits -= 7
    packed.append(accumulator & 127)  # Includes the aligned final flush byte.
    return bytes(packed)


def unpack7(packed: bytes) -> bytes:
    accumulator = bits = 0
    raw = bytearray()
    for byte in packed:
        if byte > 127:
            raise ValueError("non-SysEx data byte")
        accumulator |= byte << bits
        bits += 7
        while bits >= 8:
            raw.append(accumulator & 255)
            accumulator >>= 8
            bits -= 8
    return bytes(raw)


@dataclass(frozen=True)
class Frame:
    command: int
    body: bytes = b""

    def encode(self) -> bytes:
        if not 0 <= self.command <= 255 or len(self.body) >= 1 << 24:
            raise ValueError("frame field out of range")
        raw = b"\x00\x59" + bytes([self.command]) + len(self.body).to_bytes(3, "little")
        raw += self.body + bytes([(~sum(self.body)) & 255])
        return b"\xf0" + pack7(raw) + b"\xf7"

    @classmethod
    def decode(cls, wire: bytes) -> "Frame":
        if len(wire) < 3 or wire[0] != 0xF0 or wire[-1] != 0xF7:
            raise ValueError("incomplete SysEx envelope")
        raw = unpack7(wire[1:-1])
        if len(raw) < 7 or raw[:2] != b"\0Y":
            raise ValueError("invalid frame header")
        size = int.from_bytes(raw[3:6], "little")
        if len(raw) != size + 7:
            raise ValueError("frame length mismatch")
        body = raw[6:6 + size]
        if raw[-1] != ((~sum(body)) & 255):
            raise ValueError("frame checksum mismatch")
        frame = cls(raw[2], body)
        if frame.encode() != wire:
            raise ValueError("noncanonical SysEx padding")
        return frame


# Known logical addresses, not physical NOR addresses. Each has its own bound.
READ_WINDOWS = {
    "presets": (4, 0x00000000, 1942),
    "active": (4, 0x10000000, 92),
    "global": (4, 0x20000000, 4),
    "cab_names": (5, 0x80000000, 280),
    "amp_names": (5, 0x90000000, 280),
}


def read_request(window: str, offset: int = 0, length: int | None = None) -> Frame:
    kind, base, span = READ_WINDOWS[window]
    length = span - offset if length is None else length
    if offset < 0 or length <= 0 or offset + length > span:
        raise ValueError("read outside the documented Tank Mini window")
    return Frame(0x23, bytes([kind]) + struct.pack("<I", base + offset)
                 + length.to_bytes(3, "little"))


def validate_readonly(frame: Frame) -> None:
    if frame.command == 0x11 and frame.body == b"":
        return
    if frame.command == 0x23 and len(frame.body) == 8:
        kind = frame.body[0]
        address = int.from_bytes(frame.body[1:5], "little")
        length = int.from_bytes(frame.body[5:8], "little")
        if any(kind == k and base <= address and 0 < length
               and address + length <= base + size
               for k, base, size in READ_WINDOWS.values()):
            return
    raise ValueError("only identity and bounded documented reads are enabled")


@dataclass(frozen=True)
class Preset:
    volume: int
    chain: tuple[int, ...]
    enabled: tuple[int, ...]
    units: tuple[int, ...]
    parameters: tuple[tuple[int, ...], ...]

    @classmethod
    def decode(cls, raw: bytes) -> "Preset":
        if len(raw) != 92:
            raise ValueError("a Tank Mini preset is exactly 92 bytes")
        volume = int.from_bytes(raw[:2], "little", signed=True)
        chain = tuple(raw[2:8])
        if sorted(chain) != list(range(6)):
            raise ValueError("effect order is not a permutation of 0..5")
        return cls(volume, chain, tuple(raw[8:14]), tuple(raw[14:20]),
                   tuple(struct.unpack_from("<6h", raw, 20 + i * 12) for i in range(6)))

    def to_dict(self) -> dict:
        return asdict(self)


def decode_table(raw: bytes) -> list[Preset]:
    if len(raw) != 1942 or raw[-10:] != b"PATCHEND\0\0":
        raise ValueError("invalid Tank Mini preset bank size or trailer")
    return [Preset.decode(raw[i * 92:(i + 1) * 92]) for i in range(21)]
