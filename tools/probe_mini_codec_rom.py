"""HYC3 staged host API: clock snapshot, then one explicit bounded codec read.

Import and the default CLI are offline and never enumerate/open a device. The
root runner supplies a reviewed ROM transport/slot and owns all device I/O.
The target's FC6C can touch PA1/2/9 and PC5, restoring their recorded fields;
FC6B only reads clocks. No automatic retries, codec-data writes or FD61 reads.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.probe_mini_recovery import MiniRamSession, RAM_SLOTS, validate_ram_request
from tools.build_mini_rom_codec_rom import ALLOWED_REGISTERS, RECORD_BYTES, validate_record

REGISTERS = tuple(ALLOWED_REGISTERS)


def codec_rom_snapshot_cdb():
    return b'\xfc\x6b' + b'\xff' * 14


def codec_rom_record_cdb():
    return b'\xfd\x6d' + b'\xff' * 14


def codec_rom_read_cdb(register, snapshot_sequence):
    if type(register) is not int or register not in REGISTERS:
        raise ValueError('register outside HYC3 read-only diagnostic allowlist')
    if type(snapshot_sequence) is not int or not 1 <= snapshot_sequence <= 65534:
        raise ValueError('HYC3 requires an unconsumed snapshot sequence in 1..65534')
    return b'\xfc\x6c' + struct.pack('>HH', register, snapshot_sequence) + b'\xff' * 10


def validate_codec_rom_request(cdb, data_out, read_length, *, slot):
    # Reuse only the upload/readback/jump and INQUIRY paths, never the base
    # plugin's FC60/FD61 commands or another plugin's peripheral opcodes.
    if cdb == bytes((0x12, 0, 0, 0, 36, 0)) or cdb[:2] in (b'\xfb\x06', b'\xfb\x08', b'\xfd\x07'):
        validate_ram_request(cdb, data_out, read_length, slot=slot)
        return
    if slot not in RAM_SLOTS or len(cdb) != 16 or data_out is not None or type(read_length) is not int:
        raise ValueError('HYC3 requires a known slot and bounded IN command')
    if cdb[:2] == b'\xfc\x6b' and read_length == 16:
        expected = codec_rom_snapshot_cdb()
    elif cdb[:2] == b'\xfd\x6d' and read_length == RECORD_BYTES:
        expected = codec_rom_record_cdb()
    elif cdb[:2] == b'\xfc\x6c' and read_length == 16:
        expected = codec_rom_read_cdb(int.from_bytes(cdb[2:4], 'big'), int.from_bytes(cdb[4:6], 'big'))
    else:
        raise ValueError('not an HYC3 staged diagnostic command')
    if cdb != expected:
        raise ValueError('malformed HYC3 request or padding')


class MiniCodecRomSession(MiniRamSession):
    """Reuse the reviewed RAM lifecycle; handshake captures clocks only.

    upload_and_start()/verify_and_start() perform FD07 verification, one FB08,
    then FC6B + FD6D. They never send FC6C. A valid unsupported-clock snapshot
    is returned with can_read_register=False so the runner can stop safely.
    Every read_register() consumes its snapshot before submitting FC6C. The
    caller must request capture_snapshot() explicitly before any later read.
    """
    def __init__(self, transport, *, slot, build_tag, known_free_slot=False, known_uploaded_unstarted=False):
        super().__init__(transport, slot=slot, known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        if type(build_tag) is not int or not 0 <= build_tag <= 0xffffffff:
            raise ValueError('expected pinned HYC3 build tag')
        self.build_tag, self.sequence = build_tag, 0
        self.armed = False
        self.snapshot_sequence = None
        self.last_snapshot, self.last_snapshot_record, self.last_record = None, None, None

    def _handshake(self):
        if not self.started or self.sequence or self.failed:
            raise ValueError('HYC3 handshake requires the newly started plugin')
        result = self._capture_snapshot()
        return {'codec_rom_snapshot': result, 'snapshot_sequence': result['sequence'],
                'clock_gate': result['gate'], 'can_read_register': self.armed,
                'gpio_touched_on_entry_or_snapshot': False, 'codec_register_writes_available': False}

    def read(self, address, length):
        raise ValueError('HYC3 exposes snapshot/read_register records, never arbitrary FD61 memory reads')

    def _record(self, *, phase, register):
        raw = self.transport.exchange(codec_rom_record_cdb(), read_length=RECORD_BYTES)
        self.last_record = raw  # Preserve even malformed bytes for the runner's journal.
        result = validate_record(raw, base=self.slot, build_tag=self.build_tag,
                                 sequence=self.sequence, phase=phase, reg=register, target=True)
        result.update(record_hex=raw.hex(), snapshot_sequence_consumed=struct.unpack_from('<I',raw,396)[0],
                      clock_words_first=list(struct.unpack_from('<17I',raw,112)),
                      clock_words_last=list(struct.unpack_from('<17I',raw,180)),
                      stack_guards_ok=struct.unpack_from('<I',raw,104)[0] == 1,
                      clocks_equal=struct.unpack_from('<I',raw,96)[0] == 1,
                      automatic_retry=False, nonce_is_snapshot_sequence_not_random=True)
        return result

    def _capture_snapshot(self):
        if self.failed or self.sequence >= 65534:
            raise ValueError('unfailed HYC3 session with available sequence required')
        # Clear the prior token before any exchange, including an ambiguous
        # snapshot transfer. No retry may reuse the previously approved state.
        self.armed, self.snapshot_sequence = False, None
        self.sequence += 1
        try:
            reply = self.transport.exchange(codec_rom_snapshot_cdb(), read_length=16)
            if (len(reply) != 16 or reply[:7] != b'\xfc\x6bHYC3\x03'
                    or reply[7] > 7 or int.from_bytes(reply[8:12],'big') != self.slot
                    or int.from_bytes(reply[12:14],'big') != self.sequence or reply[14:] != b'\x02\x00'):
                raise ValueError('HYC3 snapshot identity/slot/sequence/length mismatch')
            result = self._record(phase=0, register=0xffff)
            if result['gate'] != reply[7]:
                raise ValueError('HYC3 snapshot gate differs from record')
            self.last_snapshot_record = self.last_record
            self.armed = result['gate'] == 0 and result['status'] == 0 and result['stack_guards_ok'] and result['clocks_equal']
            self.snapshot_sequence = self.sequence if self.armed else None
            # Unsupported, stable clock configurations are valid snapshot-only
            # results. Clock changes/guard failures instead end the session.
            if result['status'] not in (0, -3) or not result['stack_guards_ok'] or not result['clocks_equal']:
                self.failed = True
            result.update(can_read_register=self.armed, gpio_touched=False, session_failed=self.failed)
            self.last_snapshot = result
            return result
        except Exception:
            self.failed, self.armed = True, False
            self.snapshot_sequence = None
            raise

    def capture_snapshot(self):
        if not self.ready or self.failed:
            raise ValueError('identified, unfailed HYC3 session required before another snapshot')
        return self._capture_snapshot()

    def snapshot(self):
        """Explicit snapshot; never called automatically by read_register()."""
        return self.capture_snapshot()

    def read_register(self, register):
        if not self.ready or self.failed or not self.armed or self.snapshot_sequence != self.sequence or self.sequence >= 65535:
            raise ValueError('one fresh successful HYC3 clock snapshot is required before each register read')
        token = self.snapshot_sequence
        cdb = codec_rom_read_cdb(register, token)
        approved = struct.unpack_from('<12I', self.last_snapshot_record, 112)
        self.armed, self.snapshot_sequence = False, None
        self.sequence += 1  # Consume before submission, even if the reply is lost.
        try:
            reply = self.transport.exchange(cdb, read_length=16)
            if (len(reply) != 16 or reply[:6] != b'\xfc\x6cHYC3'
                    or int.from_bytes(reply[6:8],'big') != self.sequence
                    or int.from_bytes(reply[12:14],'big') != register or reply[14] > 7 or reply[15] != 1):
                raise ValueError('HYC3 read reply identity/sequence/register/phase mismatch')
            status = int.from_bytes(reply[8:12], 'big', signed=True)
            result = self._record(phase=1, register=register)
            if result['status'] != status or result['gate'] != reply[14] or result['snapshot_sequence_consumed'] != token:
                raise ValueError('HYC3 read reply/record status, gate or consumed nonce mismatch')
            if result['setup_flags'] and tuple(result['clock_words_first'][:12]) != approved:
                raise ValueError('GPIO setup occurred with clocks different from the approved snapshot')
            if (status not in (0,-2) or result['gate'] != 0 or result['restoration_flags'] != 3
                    or not result['stack_guards_ok'] or not result['clocks_equal']):
                self.failed = True
            result.update(can_read_register=False, requires_new_snapshot=True, session_failed=self.failed,
                          gpio_touched=bool(result['setup_flags']), nack_is_not_codec_absence=status == -2)
            return result
        except Exception:
            self.failed = True
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', type=lambda v:int(v,0), default=0x58, help='offline CDB example only')
    parser.add_argument('--snapshot-sequence', type=int, default=1, help='offline CDB example only')
    args = parser.parse_args(argv)
    read = codec_rom_read_cdb(args.register, args.snapshot_sequence)
    print(json.dumps({'device_io':False, 'enumerated':False, 'magic':'HYC3', 'version':3,
                      'transport_profile':'ram-codec-rom', 'record_bytes':RECORD_BYTES,
                      'snapshot_cdb':codec_rom_snapshot_cdb().hex(), 'record_cdb':codec_rom_record_cdb().hex(),
                      'read_cdb_example':read.hex(), 'read_requires_valid_snapshot':True,
                      'one_read_per_snapshot':True, 'automatic_retry':False,
                      'gpio_pins_touched_only_by_explicit_read':['PA1','PA2','PA9','PC5'],
                      'codec_data_writes':False, 'clock_writes':False, 'NOR_access':False,
                      'physical_PC5_role_known':False, 'calibrated_timing':False}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
