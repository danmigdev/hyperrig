"""Lost FINISH reply reconciliation: local fixtures/fakes only, no device I/O."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'analysis/hardware'), str(ROOT / 'tools')]
spec = importlib.util.spec_from_file_location('mini_partial_inspect7',
    ROOT / 'analysis/hardware/read_mini_partial_install7.py')
inspect = importlib.util.module_from_spec(spec); spec.loader.exec_module(inspect)
from tests.test_mini_app_writer_protocol import encoded_record, changed_record

TAG = 3953063795


def prior_record():
    return encoded_record({4: 1, 8: inspect.A, 12: TAG, 16: 3, 20: 0, 24: 11, 28: 34,
        32: 0x5e000, 36: 0x5ef00, 40: 300459554, 44: 4169052368,
        48: 2134959085, 52: 2134959085, 56: 0xeb6014, 60: 0, 64: 2,
        68: 187, 72: 11, 76: 176, 80: 958464, 84: 1987, 88: 260, 92: 1,
        96: 0xffff, 100: 0, 104: 0, 108: 1, 112: 112, 116: 1})


def completed_record():
    return encoded_record({4: 1, 8: inspect.A, 12: TAG, 16: 5, 20: 0, 24: 0, 28: 35,
        32: 0x5e000, 36: 0x5ef00, 40: 300459554, 44: 4169052368,
        48: 2134959085, 52: 4169052368, 56: 0xeb6014, 60: 0, 64: 2,
        68: 187, 72: 11, 76: 176, 80: 962560, 84: 1987, 88: 260, 92: 1,
        96: 0xffff, 100: 0, 104: 0, 108: 1, 112: 144, 116: 1})


class FakeWriter:
    def __init__(self, raw, *, bad_identity=False, fail=None):
        self.raw, self.bad_identity, self.fail = raw, bad_identity, fail
        self.commands = []

    def exchange(self, cdb, data_out=None, read_length=0):
        op = int.from_bytes(cdb[:2], 'big'); self.commands.append(op)
        assert data_out is None and cdb[2:] == b'\xff' * 14
        if op == self.fail: raise TimeoutError('mock transport failure')
        if op == 0xfc78:
            assert read_length == 16
            return b'\xfc\x78' + (b'BAD!' if self.bad_identity else b'HYW1') + b'\1\1' + struct.pack('>II', inspect.A, 32768)
        if op == 0xfd88:
            assert read_length == 128
            return self.raw
        raise AssertionError('inspector submitted a command other than identity/audit')


class Inspect7Tests(unittest.TestCase):
    def confirm(self, raw):
        fake, retained = FakeWriter(raw), []
        result = inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=retained.append)
        self.assertEqual(fake.commands, [0xfc78, 0xfd88]); self.assertEqual(retained, [raw])
        return result

    def test_pinned_prior_fixture_is_exact_physical_record(self):
        self.assertEqual(inspect.sha(prior_record()), inspect.OLD_SHA)

    def test_unchanged_state_is_retained_without_finish_reissue(self):
        record, outcome = self.confirm(prior_record())
        self.assertEqual(outcome, 'prior_state_retained')
        self.assertEqual((record['token'], record['sequence'], record['read_bytes']), (11, 34, 958464))

    def test_completed_finish_has_only_exact_readonly_delta(self):
        self.assertEqual(inspect.completed_finish_record(prior_record(), build_tag=TAG), completed_record())
        record, outcome = self.confirm(completed_record())
        self.assertEqual(outcome, 'finish_completed')
        self.assertEqual((record['wren_attempts'], record['erase_attempts'], record['program_attempts'],
            record['status_polls'], record['read_bytes'], record['stack_observed_bytes']),
            (187, 11, 176, 1987, 962560, 144))

    def test_every_prior_or_completed_field_change_is_rejected_with_correct_crc(self):
        for raw in (prior_record(), completed_record()):
            for offset in range(4, 120, 4):
                value = struct.unpack_from('<I', raw, offset)[0] ^ 1
                with self.subTest(raw=inspect.sha(raw), offset=offset), self.assertRaises(ValueError):
                    self.confirm(changed_record(raw, offset, value))

    def test_partial_finish_or_changed_status_cannot_trigger_handoff(self):
        for changes in ({28: 35}, {28: 35, 80: 958976}, {28: 35, 80: 962560},
                        {28: 35, 16: 5, 24: 0}, {60: 1}, {60: 2}, {60: 4}, {64: 0x40},
                        {20: 14}, {92: 0}, {108: 0}, {112: 140}, {112: 148}):
            raw = prior_record()
            for offset, value in changes.items(): raw = changed_record(raw, offset, value)
            with self.subTest(changes=changes), self.assertRaises(ValueError): self.confirm(raw)

    def test_bad_crc_or_truncated_record_is_retained_but_rejected(self):
        for raw in (completed_record()[:-1], completed_record() + b'\0',
                    completed_record()[:120] + b'\0' * 4 + b'DONE'):
            fake, retained = FakeWriter(raw), []
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=retained.append)
            self.assertEqual(retained, [raw])

    def test_invalid_prior_witness_performs_no_io(self):
        fake = FakeWriter(prior_record())
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake, changed_record(prior_record(), 84, 1988), build_tag=TAG, retain=lambda _: None)
        self.assertEqual(fake.commands, [])

    def test_identity_failure_does_not_read_audit(self):
        fake = FakeWriter(prior_record(), bad_identity=True)
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=lambda _: None)
        self.assertEqual(fake.commands, [0xfc78])

    def test_transport_or_journal_failure_never_retries(self):
        for op in (0xfc78, 0xfd88):
            fake = FakeWriter(prior_record(), fail=op)
            with self.subTest(op=op), self.assertRaises(TimeoutError):
                inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=lambda _: None)
            self.assertEqual(fake.commands.count(op), 1)
        def fail(_): raise OSError('cannot preserve raw evidence')
        fake = FakeWriter(completed_record())
        with self.assertRaises(OSError):
            inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=fail)
        self.assertEqual(fake.commands, [0xfc78, 0xfd88])

    def test_real_completed_seventh_trace_has_all176_readbacks_and10_finish_witnesses(self):
        prior = json.loads(inspect.PRIOR.read_bytes())
        rows = [json.loads(line) for line in inspect.PRIOR_TRACE.read_text().splitlines()]
        candidate = (ROOT / 'build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin').read_bytes()
        installation = SimpleNamespace(build_tag=TAG, candidate=candidate)
        self.assertEqual(inspect.validate_stopped_trace(prior, rows, installation), prior_record())
        for selector in ('page', 'finish_stack', 'terminal_cdb'):
            bad = copy.deepcopy(rows)
            if selector == 'page':
                next(r for r in bad if r['state'] == 'after' and r['cdb'] == 'fd7f0005ef000100ffffffffffffffff')['response_sha256'] = '0' * 64
            elif selector == 'finish_stack':
                i = next(i for i, r in enumerate(bad) if r['state'] == 'after' and r['cdb'].startswith('fc80'))
                bad[i+2]['response_hex'] = changed_record(bytes.fromhex(bad[i+2]['response_hex']), 112, 140).hex()
            else:
                bad[-2]['cdb'] = bad[-1]['cdb'] = 'fc800000000b000000240005e000ffff'
            with self.subTest(change=selector), self.assertRaises(ValueError):
                inspect.validate_stopped_trace(prior, bad, installation)


if __name__ == '__main__': unittest.main()
