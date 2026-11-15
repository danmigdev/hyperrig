"""Bounded host API for the synthetic A2 engine RAM probe; no automatic IO.

HYE1 is a diagnostic protocol, distinct from the final UltraRig-derived app.
Use WindowsRomTransport(..., profile='ram-engine') after explicit discovery.
No USB mode switch, clock/peripheral command, flash write or retry is provided.
"""
from __future__ import annotations
import struct

from probe_mini_recovery import MiniRamSession, _slot_range, validate_ram_request

ENGINE_FRAMES = 230


def engine_selftest_cdb() -> bytes:
    return b'\xfc\x62' + b'\xff' * 14


def engine_read_cdb(address: int, length: int, *, slot: int) -> bytes:
    _slot_range(address, length, slot, 4096)
    return b'\xfd\x63' + struct.pack('>IH', address, length) + b'\xff' * 8


def validate_engine_request(cdb: bytes, data_out: bytes | None, read_length: int, *, slot: int) -> None:
    if cdb == bytes((0x12, 0, 0, 0, 36, 0)) or cdb[:2] in (b'\xfb\x06', b'\xfb\x08', b'\xfd\x07'):
        validate_ram_request(cdb, data_out, read_length, slot=slot)
        return
    if len(cdb) != 16 or data_out is not None:
        raise ValueError('engine probe requires a bounded IN command')
    if cdb[:2] == b'\xfc\x62' and read_length == 16:
        _slot_range(slot, 1, slot, 1)
        expected = engine_selftest_cdb()
    elif cdb[:2] == b'\xfd\x63':
        address, length = struct.unpack_from('>IH', cdb, 2)
        if read_length != length:
            raise ValueError('engine read CDB and data phase lengths differ')
        expected = engine_read_cdb(address, length, slot=slot)
    else:
        raise ValueError('not an HYE1 diagnostic command')
    if cdb != expected:
        raise ValueError('malformed HYE1 request')


class MiniEngineSession(MiniRamSession):
    """Same audited upload/verify/one-jump lifecycle, separate HYE1 commands."""
    def _handshake(self) -> dict:
        answer = self.transport.exchange(engine_selftest_cdb(), read_length=16)
        if (len(answer) != 16 or answer[:2] != b'\xfc\x62' or answer[6:10] != b'HYE1' or
                answer[14:16] != b'\x00\x01'):
            raise ValueError('uploaded engine probe identity/version mismatch')
        frames = int.from_bytes(answer[2:6], 'big')
        status = int.from_bytes(answer[10:14], 'big')
        if frames != ENGINE_FRAMES or status:
            raise ValueError(f'engine selftest failed: frames={frames}, status={status:#x}')
        return {'engine_answer_hex': answer.hex(), 'engine_frames': frames,
                'engine_status': status, 'engine_protocol_version': 1,
                'model_scope': 'synthetic three-layer fixture, not original 23-layer A2 capture'}

    def read(self, address: int, length: int) -> bytes:
        _slot_range(address, length, self.slot, 32768)
        if not self.ready or self.failed:
            raise ValueError('HYE1 handshake required before FD63 reads')
        result = bytearray()
        try:
            for offset in range(0, length, 4096):
                size = min(4096, length - offset)
                answer = self.transport.exchange(engine_read_cdb(address + offset, size, slot=self.slot), read_length=size)
                if len(answer) != size:
                    raise ValueError('short HYE1 RAM read')
                result.extend(answer)
        except Exception:
            self.failed = True
            raise
        return bytes(result)
