"""Repeated receive orchestration and NTSTATUS proxy; no Windows/device I/O."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
spec = importlib.util.spec_from_file_location('mini_receive_stress', ROOT / 'analysis/hardware/run_mini_receive_stress.py')
stress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)
from tests.test_mini_receive_protocol import FakeReceive, TAG, SLOT
from tools.probe_mini_receive import MiniReceiveSession
from tools.probe_mini_recovery import sha


def target_pointers(raw):
    raw = bytearray(raw)
    struct.pack_into('<III', raw, 96, *stress.CALLBACKS.values())
    struct.pack_into('<I', raw, 504, zlib.crc32(raw[:504]))
    return bytes(raw)


class StressTests(unittest.TestCase):
    def session(self):
        fake = FakeReceive();fake.raw_return = 260;fake.record_mutator = target_pointers
        session = MiniReceiveSession(fake, slot=SLOT, build_tag=TAG, expected_raw_return=260, known_free_slot=True)
        with patch('time.sleep'):
            session.upload_and_start(b'pure mock RAM image', expected_sha256=sha(b'pure mock RAM image'))
        fake.commands.clear()
        return fake, session

    def observe(self, session, *, before=None, after=None):
        records, started, completed = [], [], []
        def retain(sequence, raw): records.append((sequence, raw))
        result = stress.run_observations(session, before=before or started.append,
            after=after or (lambda seq, item: completed.append((seq, item))), retain_records=retain)
        return result, records, started, completed

    def test_256_exact_sequences_nonces_seeds_two_records_each(self):
        fake, session = self.session()
        cdbs = []
        original = fake.exchange
        def track(cdb, data_out=None, read_length=0):
            cdbs.append(cdb)
            return original(cdb, data_out=data_out, read_length=read_length)
        fake.exchange = track
        result, records, started, completed = self.observe(session)
        self.assertEqual(len(started), 256)
        self.assertEqual(len(completed), 256)
        self.assertEqual(len({x['nonce'] for x in started}), 256)
        self.assertEqual(len({x['seed'] for x in started}), 256)
        self.assertEqual(sum(len(raw) for _, raw in records), 512)
        self.assertEqual(fake.commands, [0xFC83, 0xFB84, 0xFD85, 0xFD85] * 256)
        self.assertEqual([int.from_bytes(cmd[2:4], 'big') for cmd in cdbs if cmd[:2] == b'\xfb\x84'], list(range(1, 257)))
        self.assertEqual(session.sequence, 256)
        self.assertTrue(result['all_observations_passed'])
        self.assertFalse(result['general_receive_semantics_proven'])
        for number, raw in records:
            self.assertEqual([int.from_bytes(r[92:96], 'little') for r in raw], [1, 2])
            self.assertTrue(all(int.from_bytes(r[16:20], 'little') == number for r in raw))

    def test_out_failure_at_fourteenth_is_terminal_and_never_reissued(self):
        fake, session = self.session()
        original = fake.exchange;records = []
        def fail(cdb, data_out=None, read_length=0):
            if cdb[:2] == b'\xfb\x84' and int.from_bytes(cdb[2:4], 'big') == 14:
                fake.fail_opcode = 0xFB84
            return original(cdb, data_out=data_out, read_length=read_length)
        fake.exchange = fail
        with self.assertRaises(TimeoutError):
            stress.run_observations(session, before=lambda x: None, after=lambda *x: None,
                                    retain_records=lambda seq, raw: records.append((seq, raw)))
        self.assertEqual(fake.commands.count(0xFB84), 14)
        self.assertEqual(fake.commands[-1], 0xFB84)
        self.assertEqual(sum(len(raw) for _, raw in records), 26)
        self.assertTrue(session.failed and session.ambiguous_receive)
        self.assertNotIn(0xFB08, fake.commands)
        self.assertNotIn(0xFC72, fake.commands)

    def test_second_record_failure_retains_first_and_stops(self):
        fake, session = self.session()
        original = fake.exchange;records = []
        def fail(cdb, data_out=None, read_length=0):
            if cdb[:2] == b'\xfd\x85' and fake.sequence == 14 and fake.sample == 1:
                fake.fail_opcode = 0xFD85
            return original(cdb, data_out=data_out, read_length=read_length)
        fake.exchange = fail
        with self.assertRaises(TimeoutError):
            stress.run_observations(session, before=lambda x: None, after=lambda *x: None,
                                    retain_records=lambda seq, raw: records.append((seq, raw)))
        self.assertEqual(fake.commands.count(0xFB84), 14)
        self.assertEqual(sum(len(raw) for _, raw in records), 27)
        self.assertEqual(len(records[-1][1]), 1)
        self.assertTrue(session.failed)

    def test_partial_return_and_late_data_stop_before_next_out(self):
        for mode in ('short-return', 'partial', 'late'):
            fake, session = self.session()
            def before(item):
                if item['sequence'] == 14:
                    if mode == 'short-return': fake.raw_return = 259
                    else: fake.mode = mode
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.observe(session, before=before)
            self.assertEqual(fake.commands.count(0xFB84), 14)
            self.assertTrue(session.failed)

    def test_logging_failure_cannot_trigger_next_observation(self):
        for where in ('before', 'after'):
            fake, session = self.session()
            def before(item):
                if where == 'before' and item['sequence'] == 14: raise OSError('mock disk failure')
            def after(sequence, item):
                if where == 'after' and sequence == 14: raise OSError('mock disk failure')
            with self.subTest(where=where), self.assertRaises(OSError):
                self.observe(session, before=before, after=after)
            self.assertEqual(fake.commands.count(0xFB84), 13 if where == 'before' else 14)

    def test_pointer_mismatch_rejected_even_when_payload_is_stable(self):
        fake, session = self.session()
        fake.record_mutator = None
        with self.assertRaises(ValueError): self.observe(session)
        self.assertEqual(fake.commands, [0xFC83, 0xFB84, 0xFD85, 0xFD85])

    def test_bounded_vectors_and_fresh_session_required(self):
        for number in (0, 257, True, -1):
            with self.assertRaises(ValueError): stress.observation_vector(number)
        fake, session = self.session();session.sequence = 1
        with self.assertRaises(ValueError): self.observe(session)
        self.assertEqual(fake.commands, [])


class NativeDiagnosticTests(unittest.TestCase):
    def test_failure_preserves_ctypes_private_last_error(self):
        order = [];state = {'error': 0}
        class Kernel:
            def DeviceIoControl(self, *args): order.append('ioctl');state['error'] = 31;return 0
        def get(): order.append('get-private');return state['error']
        def put(value): order.append('set-private');state['error'] = value
        def ntstatus(): order.append('ntstatus');state['error'] = 999;return -1073741435
        proxy = stress.DiagnosticKernelProxy(Kernel(), get_error=get, set_error=put, ntstatus=ntstatus)
        self.assertEqual(proxy.DeviceIoControl('mock'), 0)
        self.assertEqual(order, ['ioctl', 'get-private', 'ntstatus', 'set-private'])
        self.assertEqual(state['error'], 31)
        self.assertEqual(proxy.last_failure['ntstatus_hex'], 'c0000185')
        self.assertTrue(proxy.last_failure['ntstatus_is_diagnostic_only'])

    def test_unavailable_or_throwing_ntstatus_never_masks_win32(self):
        for callback in (None, lambda: (_ for _ in ()).throw(OSError('unavailable getter'))):
            class Kernel:
                def DeviceIoControl(self, *args): return 0
            restored = []
            proxy = stress.DiagnosticKernelProxy(Kernel(), get_error=lambda: 31,
                                                set_error=restored.append, ntstatus=callback)
            self.assertEqual(proxy.DeviceIoControl(), 0)
            self.assertEqual(restored, [31])
            self.assertEqual(proxy.last_failure['win32_error'], 31)
            self.assertIsNone(proxy.last_failure['ntstatus_hex'])

    def test_success_performs_no_error_api_or_ntstatus_call(self):
        class Kernel:
            def DeviceIoControl(self, *args): return 1
        def forbidden(*args): raise AssertionError('unexpected diagnostic call')
        proxy = stress.DiagnosticKernelProxy(Kernel(), get_error=forbidden, set_error=forbidden, ntstatus=forbidden)
        self.assertEqual(proxy.DeviceIoControl(), 1)
        self.assertIsNone(proxy.last_failure)


if __name__ == '__main__': unittest.main()
