"""Exact post-STAGE audit reconciliation, local traces and fake transport only."""
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
spec = importlib.util.spec_from_file_location('mini_partial_inspect8',
    ROOT / 'analysis/hardware/read_mini_partial_install8.py')
inspect = importlib.util.module_from_spec(spec); spec.loader.exec_module(inspect)
from tests.test_mini_app_writer_protocol import encoded_record, changed_record

TAG = 3953063795


def prior_record():
    return encoded_record({4: 1, 8: inspect.A, 12: TAG, 16: 3, 20: 0, 24: 21, 28: 22,
        32: 0x73000, 36: 0x73900, 40: 3009462001, 44: 4040395266,
        48: 3386429108, 52: 3386429108, 56: 0xeb6014, 60: 0, 64: 2,
        68: 351, 72: 21, 76: 330, 80: 1363456, 84: 3715, 88: 260, 92: 1,
        96: 0x3ff, 100: 0, 104: 0, 108: 1, 112: 112, 116: 1})


def staged_record():
    return encoded_record({4: 1, 8: inspect.A, 12: TAG, 16: 4, 20: 0, 24: 21, 28: 23,
        32: 0x73000, 36: 0x73a00, 40: 3009462001, 44: 4040395266,
        48: 0xfbf194f8, 52: 0xfbf194f8, 56: 0xeb6014, 60: 0, 64: 2,
        68: 351, 72: 21, 76: 330, 80: 1363456, 84: 3715, 88: 260, 92: 1,
        96: 0x3ff, 100: 1, 104: 0, 108: 1, 112: 52, 116: 1})


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


class Inspect8Tests(unittest.TestCase):
    def confirm(self, raw):
        fake, retained = FakeWriter(raw), []
        result = inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=retained.append)
        self.assertEqual(fake.commands, [0xfc78, 0xfd88]); self.assertEqual(retained, [raw])
        return result

    def test_prior_fixture_is_exact_last_validated_physical_audit(self):
        self.assertEqual(inspect.sha(prior_record()), inspect.OLD_SHA)

    def test_only_exact_acknowledged_stage_passes_with_no_NOR_delta(self):
        self.assertEqual(inspect.completed_stage_record(prior_record(), build_tag=TAG), staged_record())
        record, outcome = self.confirm(staged_record())
        self.assertEqual(outcome, 'acknowledged_stage_confirmed')
        self.assertEqual((record['wren_attempts'], record['erase_attempts'], record['program_attempts'],
            record['status_polls'], record['read_bytes'], record['stack_observed_bytes']),
            (351, 21, 330, 3715, 1363456, 52))

    def test_unchanged_old_audit_is_stale_and_rejected(self):
        with self.assertRaises(ValueError): self.confirm(prior_record())

    def test_every_fresh_word_change_rejected_even_with_correct_crc(self):
        raw = staged_record()
        for offset in range(4, 120, 4):
            value = struct.unpack_from('<I', raw, offset)[0] ^ 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.confirm(changed_record(raw, offset, value))

    def test_echoed_programmed_or_changed_stack_rejected(self):
        for changes in ({104: 1}, {28: 24}, {76: 331}, {68: 352}, {80: 1363712},
                        {112: 112}, {112: 48}, {112: 56}, {60: 1}, {60: 2}, {60: 4},
                        {64: 0x40}, {20: 14}, {92: 0}, {108: 0}, {88: 259}):
            raw = staged_record()
            for offset, value in changes.items(): raw = changed_record(raw, offset, value)
            with self.subTest(changes=changes), self.assertRaises(ValueError): self.confirm(raw)

    def test_bad_crc_or_truncated_audit_is_retained_but_rejected(self):
        for raw in (staged_record()[:-1], staged_record() + b'\0', staged_record()[:120] + b'\0' * 4 + b'DONE'):
            fake, retained = FakeWriter(raw), []
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=retained.append)
            self.assertEqual(retained, [raw])

    def test_invalid_prior_performs_no_io(self):
        fake = FakeWriter(staged_record())
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake, changed_record(prior_record(), 84, 3716), build_tag=TAG, retain=lambda _: None)
        self.assertEqual(fake.commands, [])

    def test_identity_failure_stops_before_audit(self):
        fake = FakeWriter(staged_record(), bad_identity=True)
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=lambda _: None)
        self.assertEqual(fake.commands, [0xfc78])

    def test_transport_or_journal_failure_never_retries(self):
        for op in (0xfc78, 0xfd88):
            fake = FakeWriter(staged_record(), fail=op)
            with self.subTest(op=op), self.assertRaises(TimeoutError):
                inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=lambda _: None)
            self.assertEqual(fake.commands.count(op), 1)
        def fail(_): raise OSError('cannot preserve raw evidence')
        fake = FakeWriter(staged_record())
        with self.assertRaises(OSError):
            inspect.confirm_writer(fake, prior_record(), build_tag=TAG, retain=fail)
        self.assertEqual(fake.commands, [0xfc78, 0xfd88])

    def test_real_trace_proves330_readbacks_and_stages_and_final_RAM_ack(self):
        prior = json.loads(inspect.PRIOR.read_bytes())
        rows = [json.loads(line) for line in inspect.PRIOR_TRACE.read_text().splitlines()]
        candidate = (ROOT / 'build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin').read_bytes()
        installation = SimpleNamespace(build_tag=TAG, candidate=candidate)
        self.assertEqual(inspect.validate_stopped_trace(prior, rows, installation), prior_record())
        for selector in ('page', 'stage_status', 'stage_stack', 'terminal_cdb'):
            bad = copy.deepcopy(rows)
            if selector == 'page':
                next(r for r in bad if r['state'] == 'after' and r['cdb'] == 'fd7f000739000100ffffffffffffffff')['response_sha256'] = '0' * 64
            elif selector == 'stage_status': bad[-3]['response_hex'] = 'fc7e00030000001500000016c9d8ceb4'
            elif selector == 'stage_stack':
                i = next(i for i, r in enumerate(bad) if r['state'] == 'after' and r['cdb'].startswith('fb7c'))
                j = next(j for j in range(i+1, len(bad)) if bad[j]['state'] == 'after' and bad[j]['cdb'] == 'fd88' + 'ff' * 14)
                bad[j]['response_hex'] = changed_record(bytes.fromhex(bad[j]['response_hex']), 112, 112).hex()
            else: bad[-2]['cdb'] = bad[-1]['cdb'] = 'fc7e' + 'ff' * 14
            with self.subTest(change=selector), self.assertRaises(ValueError):
                inspect.validate_stopped_trace(prior, bad, installation)


if __name__ == '__main__': unittest.main()
