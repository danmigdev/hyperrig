"""Fresh HYRX trial after journal failure; in-memory transports only."""
from contextlib import nullcontext
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
spec = importlib.util.spec_from_file_location('mini_receive_stress_v2',
    ROOT / 'analysis/hardware/run_mini_receive_stress_v2.py')
stress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)
from tests.test_mini_receive_protocol import make_record, TAG, FakeReceive
from tests.test_mini_recovery import FakeNor
from tests.test_mini_receive_stress import target_pointers
from tools.probe_mini_receive import MiniReceiveSession


def armed_record():
    payload, nonce, seed = stress.observation_vector(32)
    raw = bytearray(make_record(payload=payload, sequence=32, nonce=nonce,
                                seed=seed, sample=1, raw_return=-2147483648))
    initial = stress.poison(260, seed)
    raw[128:388] = initial
    for off, value in {28:1, 44:zlib.crc32(initial), 48:zlib.crc32(initial),
                       56:0, 60:0, 76:0, 80:0, 88:0}.items():
        struct.pack_into('<I', raw, off, value)
    return target_pointers(raw)


def changed(raw, offset, value):
    raw = bytearray(raw)
    struct.pack_into('<I', raw, offset, value)
    struct.pack_into('<I', raw, 504, zlib.crc32(raw[:504]))
    return bytes(raw)


class HandoffTests(unittest.TestCase):
    def run_handoff(self, *, record=None, bad_identity=False, failed_op=None,
                    bad_reader=False, sink_error=False, state_error=False):
        opened, known, records, calls = [], [], [], []
        raw = armed_record() if record is None else record
        class Prior:
            def exchange(self, cdb, data_out=None, read_length=0):
                opcode = int.from_bytes(cdb[:2], 'big')
                calls.append((stress.A, opcode))
                if opcode == failed_op: raise TimeoutError('no retry allowed')
                if opcode == 0xFC82:
                    return b'\xfc\x82' + (b'BAD!' if bad_identity else b'HYRX') + b'\1\0' + struct.pack('>II', stress.A, 32768)
                if opcode == 0xFD85: return raw
                raise AssertionError('unexpected command to old probe')
        nor = FakeNor();nor.slot = stress.B
        old = nor.exchange
        def reader_exchange(cdb, data_out=None, read_length=0):
            opcode = int.from_bytes(cdb[:2], 'big')
            calls.append((stress.B, opcode))
            if opcode == failed_op: raise TimeoutError('no retry allowed')
            result = old(cdb, data_out, read_length)
            if bad_reader and opcode == 0xFC70: return bytes(16)
            return result
        nor.exchange = reader_exchange
        def open_transport(slot, profile, label):
            opened.append((slot, profile, label))
            return nullcontext(Prior() if slot == stress.A else nor)
        def sink(record):
            if sink_error: raise OSError('record cannot be persisted')
            records.append(record)
        def mark(slot):
            if state_error: raise OSError('journal cannot be published')
            known.append(slot)
        self.opened, self.known, self.records, self.calls, self.nor = opened, known, records, calls, nor
        image = b'mock reader bytes'
        with patch('time.sleep'):
            return stress.retire_prior_probe(open_transport, build_tag=TAG,
                reader_payload=image, reader_sha256=stress.sha(image),
                record_sink=sink, known_slot=mark)

    def test_prior_armed_state_verified_before_reader_upload_and_no_SPI(self):
        result = self.run_handoff()
        self.assertEqual(self.calls, [(stress.A, 0xFC82), (stress.A, 0xFD85),
            (stress.B, 0xFB06), (stress.B, 0xFD07), (stress.B, 0xFB08), (stress.B, 0xFC70)])
        self.assertEqual(self.known, [stress.A, stress.B])
        self.assertEqual(self.records, [armed_record()])
        self.assertFalse(self.nor.initialized)
        self.assertEqual(self.nor.count, 0)
        self.assertFalse(result['prior_OUT_reissued'] or result['SPI_initialized'] or result['NOR_read'])

    def test_callback_entered_returned_calls_changed_phase_or_nonce_stops_before_B(self):
        for offset, value in ((28,3), (32,1), (52,260), (56,1), (60,1), (76,1),
                              (80,1), (88,1), (92,2), (20,1), (12,1), (96,1), (100,1)):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.run_handoff(record=changed(armed_record(), offset, value))
            self.assertEqual([slot for slot, _, _ in self.opened], [stress.A])
            self.assertFalse(self.known)

    def test_bad_poison_or_guard_or_checksum_stops_without_upload(self):
        for offset in (128, 388, 504):
            raw = bytearray(armed_record());raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.run_handoff(record=bytes(raw))
            self.assertEqual(len(self.opened), 1)

    def test_identity_error_does_not_even_sample_record(self):
        with self.assertRaises(ValueError): self.run_handoff(bad_identity=True)
        self.assertEqual(self.calls, [(stress.A, 0xFC82)])
        self.assertFalse(self.records or self.known)

    def test_any_transport_failure_stops_without_retry_or_followup(self):
        sequence = [0xFC82, 0xFD85, 0xFB06, 0xFD07, 0xFB08, 0xFC70]
        for opcode in sequence:
            with self.subTest(opcode=opcode), self.assertRaises(TimeoutError):
                self.run_handoff(failed_op=opcode)
            self.assertEqual([op for _, op in self.calls], sequence[:sequence.index(opcode)+1])
            self.assertNotIn(stress.B, self.known)

    def test_record_or_journal_failure_stops_before_reader_upload(self):
        for kwargs in ({'sink_error':True}, {'state_error':True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(OSError): self.run_handoff(**kwargs)
            self.assertEqual(len(self.opened), 1)
            self.assertFalse(self.known)

    def test_bad_reader_handshake_never_marks_B_known(self):
        with self.assertRaises(ValueError): self.run_handoff(bad_reader=True)
        self.assertEqual(self.known, [stress.A])
        self.assertEqual(self.calls[-1], (stress.B, 0xFC70))

    def test_fresh_v2_probe_then_runs_256_unique_OUT_with_512_records(self):
        fake = FakeReceive();fake.raw_return = 260;fake.record_mutator = target_pointers
        session = MiniReceiveSession(fake, slot=stress.A, build_tag=TAG,
                                      expected_raw_return=260, known_free_slot=True)
        with patch('time.sleep'):
            session.upload_and_start(b'mock HYRX bytes', expected_sha256=stress.sha(b'mock HYRX bytes'))
        fake.commands.clear();records=[];completed=[]
        result = stress.run_observations(session, before=lambda _:None,
            after=lambda seq, item:completed.append(seq), retain_records=lambda seq, pair:records.extend(pair))
        self.assertEqual(fake.commands, [0xFC83,0xFB84,0xFD85,0xFD85]*256)
        self.assertEqual(completed, list(range(1,257)))
        self.assertEqual(len(records), 512)
        self.assertTrue(result['all_observations_passed'])


if __name__ == '__main__': unittest.main()
