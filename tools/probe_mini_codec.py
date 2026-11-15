"""HYC1 host API: explicit bounded codec reads, no automatic hardware IO.

The target toggles only PA1/2 and restores their GPIO state. It never writes
codec data registers or changes audio clocks. NACK is retained, not retried.
"""
from __future__ import annotations
import struct
import zlib

from probe_mini_recovery import MiniRamSession, RAM_SLOTS, validate_ram_request

REGISTERS = (0x01, 0x03, 0x1c, 0x1d, 0x2b, 0x2c, 0x31, 0x32, 0x58, 0x59)


def codec_identity_cdb(): return b'\xfc\x64' + b'\xff' * 14
def codec_record_cdb(): return b'\xfd\x66' + b'\xff' * 14
def codec_read_cdb(register):
    if type(register) is not int or register not in REGISTERS:
        raise ValueError('register outside read-only diagnostic allowlist')
    return b'\xfc\x65' + struct.pack('>H', register) + b'\xff' * 12


def validate_codec_request(cdb, data_out, read_length, *, slot):
    if cdb == bytes((0x12, 0, 0, 0, 36, 0)) or cdb[:2] in (b'\xfb\x06', b'\xfb\x08', b'\xfd\x07'):
        validate_ram_request(cdb, data_out, read_length, slot=slot)
        return
    if slot not in RAM_SLOTS or len(cdb) != 16 or data_out is not None:
        raise ValueError('HYC1 requires a known slot and bounded IN command')
    if cdb[:2] == b'\xfc\x64' and read_length == 16:
        expected = codec_identity_cdb()
    elif cdb[:2] == b'\xfd\x66' and read_length == 128:
        expected = codec_record_cdb()
    elif cdb[:2] == b'\xfc\x65' and read_length == 16:
        expected = codec_read_cdb(int.from_bytes(cdb[2:4], 'big'))
    else:
        raise ValueError('not an HYC1 diagnostic command')
    if cdb != expected: raise ValueError('malformed HYC1 request')


def validate_codec_record(record, *, base, build_tag, sequence, register, target=True):
    def need(condition, message):
        if not condition: raise ValueError(message)
    need(len(record) == 128 and record[:4] == b'HYC1' and record[124:] == b'DONE', 'HYC1 record length/signatures')
    w = struct.unpack('<32I', record)
    status, cleanup, read_status = (struct.unpack_from('<i', record, offset)[0] for offset in (24, 48, 108))
    need(base in RAM_SLOTS and w[1:6] == (1, base, build_tag, sequence, register), 'HYC1 record identity')
    need(register in REGISTERS and 1 <= sequence <= 65535, 'HYC1 sequence/register')
    need(w[30] == zlib.crc32(record[:120]), 'HYC1 record CRC')
    need(w[13] == 1 and all((w[16+i] ^ w[21+i]) & 6 == 0 for i in range(5)), 'PA1/2 restoration failed')
    need(w[29] == 1 and (1 <= w[28] <= 4096 if target else w[28] == 0), 'HYC1 private stack')
    need(cleanup == 0 and w[11] == 1 and 1 <= w[26] <= 193, 'HYC1 STOP/delay bound')
    need(status == read_status and status in (0, -2), 'HYC1 execution or restoration error')
    if status == 0:
        need(w[7] <= 65535 and w[8:11] == (4, 2, 20) and w[26] == 193, 'HYC1 incomplete successful read')
    else:
        need(w[7] == 65535 and w[8] <= 3 and w[9] == 0 and w[10] == w[8] + 1, 'HYC1 invalid NACK record')
    return {'register': register, 'status': status, 'value': w[7] if status == 0 else None,
            'sequence': sequence, 'acknowledged': w[8], 'samples': w[10], 'stop_attempted': True,
            'gpio_restored': True, 'stack_guards_ok': True, 'stack_observed_bytes': w[28],
            'delay_calls': w[26], 'record_hex': record.hex(),
            'nack_is_not_codec_absence': status == -2}


class MiniCodecSession(MiniRamSession):
    def __init__(self, transport, *, slot, build_tag, known_free_slot=False, known_uploaded_unstarted=False):
        super().__init__(transport, slot=slot, known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        if type(build_tag) is not int or not 0 <= build_tag <= 0xffffffff:
            raise ValueError('expected pinned build tag')
        self.build_tag, self.sequence, self.last_record = build_tag, 0, None

    def _handshake(self):
        reply = self.transport.exchange(codec_identity_cdb(), read_length=16)
        expected = b'\xfc\x64HYC1\x01\x00' + struct.pack('>II', self.slot, 32768)
        if reply != expected: raise ValueError('HYC1 identity/slot/version mismatch')
        return {'codec_identity_hex': reply.hex(), 'gpio_touched_on_entry': False,
                'codec_register_writes_available': False}

    def read(self, address, length):
        raise ValueError('HYC1 exposes only read_register(), not arbitrary memory reads')

    def read_register(self, register):
        cdb = codec_read_cdb(register)
        if not self.ready or self.failed or self.sequence >= 65535:
            raise ValueError('identified, unfailed HYC1 session required')
        try:
            self.sequence += 1  # Never replay a possibly submitted transaction.
            reply = self.transport.exchange(cdb, read_length=16)
            if (len(reply) != 16 or reply[:6] != b'\xfc\x65HYC1' or
                    int.from_bytes(reply[6:8], 'big') != self.sequence or
                    int.from_bytes(reply[12:14], 'big') != register or reply[14:] != b'\x00\x01'):
                raise ValueError('HYC1 register reply mismatch')
            status = int.from_bytes(reply[8:12], 'big', signed=True)
            self.last_record = self.transport.exchange(codec_record_cdb(), read_length=128)
            result = validate_codec_record(self.last_record, base=self.slot, build_tag=self.build_tag,
                                           sequence=self.sequence, register=register)
            if status != result['status']: raise ValueError('HYC1 handshake/record status mismatch')
            return result
        except Exception:
            self.failed = True
            raise
