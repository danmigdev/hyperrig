"""Offline native-stream replay and five-command removal orchestration."""
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

from tools import probe_mini_browser_fx_remove as runner
from tools.mini_host_journal import read_shared_json
from tests.test_mini_browser_latency import FakeEditor


def ui_state():
    return dict(gain=[0, 0], chain={'P': [], 'Q': []}, model='A2', capture=0, scene=0,
                scenes=[1, 0, 0, 0], preset=0, firmwarePreset=0, amp=1, ampPresent=1)


class FakeRemoval(FakeEditor):
    def __init__(self, responses, fxt, stat, mem, *, ack, lost=False, wrong_removed=False, cleanup_failure=False):
        super().__init__(responses, fxt, stat, mem)
        self.ack, self.lost, self.wrong_removed, self.cleanup_failure = ack, lost, wrong_removed, cleanup_failure

    def query(self, line):
        if line != 'FXS': return super().query(line)
        rows = list(self.responses[line])
        if self.block:
            rows.insert(1, f"FX Q0 id=5 boost on=1 p={self.block['p']},0,0,0,0,0,0 ticks=346 l=0 g=-1 fu=0")
        return self.record(line, rows)

    def configure(self):
        self.plan = copy.deepcopy(runner.PLAN)
        self.g['events'].append(dict(kind='plan', seq=self.seq(), plan=self.plan))
        self.g['phase'] = 'attenuate'

    def next(self):
        phase = self.g['phase']
        if phase == 'attenuate':
            line, rows = 'GAIN 0 -12', ['GAIN in=0 out=-12 dB']; self.gain = [0, -12]
            following = 'add'
        elif phase == 'add':
            line, rows = 'FXA Q 99 boost', ['FXA id=5 boost', 'FX cpu=346/23018 ticks (1%) mem_fx=0 B']
            self.block = {'p': 6}; self.g['created'] = [dict(id=5, type='boost', bank='Q')]; following = 'configure'
        elif phase == 'configure':
            line, rows = 'FXP 5 0 -1', ['FXP ok -1']; self.block['p'] = -1; following = 'added_ack'
        elif phase == 'removing':
            line, rows = 'FXR 5', ['FXR ok cpu=0/23018 ticks (0%) mem_fx=0 B']
            if not self.wrong_removed: self.block = None
            following = 'removed_ack'
        elif phase == 'restoring':
            line, rows = 'PLOAD 0', [self.ack+' missing=0 capture=0 ir=0 ms=3']
            self.gain, self.block = [0, 0], None; following = 'restored_ack'
        else: raise AssertionError(phase)
        self.record(line, rows, lost=self.lost and phase == 'removing')
        self.g['phase'] = following; self.g['epoch'] += 1; self.g['mutations'] += 1
        return dict(line=line, reply=rows, rejected=False)

    def remove(self): self.g['phase'] = 'removing'; return self.next()
    def refresh(self, baseline): return ui_state()
    def detach(self, restored):
        if self.cleanup_failure: raise RuntimeError('synthetic detach failure')
        return super().detach(restored)


class RemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        real = read_shared_json(Path('build/mini-fx-latency-03/report.json'))
        cls.prepared = copy.deepcopy(real['prepared'])
        cls.prepared.update(kind='mini-exact-FXR-removal-preparation-v1', plan=copy.deepcopy(runner.PLAN))
        cls.responses = real['before']['responses']; cls.fxt = real['plan']['actual_catalog']
        cls.mem = real['measurements'][0]['measurement']['before']['raw']['MEM']
        cls.stat = real['measurements'][0]['measurement']['raw_samples'][0]['lines']
        fixture = dict(pong=cls.prepared['pong'], ack=cls.prepared['restore_ack_prefix'], fxt=cls.fxt,
                       mem=cls.mem, responses=cls.responses, reads=list(runner.original.READS))
        proc = subprocess.run(['node', 'tests/mini_browser_fx_remove_guard_test.js'],
                              input=json.dumps(fixture), capture_output=True, text=True, check=True)
        cls.node = json.loads(proc.stdout)
        cls.native = cls.node['report']; cls.native['prepared'] = cls.prepared
        for name in ('before', 'added', 'removed', 'restored'):
            cls.native[name]['state'] = runner.original.parse_snapshot(cls.native[name]['responses'])
        cls.native['restored_editor_state'] = ui_state()

    def fake(self, **options):
        return FakeRemoval(self.responses, self.fxt, self.stat, self.mem,
                           ack=self.prepared['restore_ack_prefix'], **options)

    def test_original_queue_and_native_reader_replayed_with_nonzero_actual_id(self):
        self.assertGreaterEqual(self.node['checks'], 20)
        result = runner.verify_report(self.native)
        self.assertEqual(result['temporary_instance_id'], 5)
        self.assertEqual(result['actual_mutation_requests'],
                         ['GAIN 0 -12', 'FXA Q 99 boost', 'FXP 5 0 -1', 'FXR 5', 'PLOAD 0'])
        self.assertTrue(result['saved_baseline_restored'])
        self.assertEqual(result['general_family_grants'], [])
        self.assertFalse(result['effect_removal_UI_physically_exercised'])

    def test_firmware_FXR_uses_common_resource_formatter_in_installed_v3(self):
        from hyperrig.jieli import unpack_app
        original = runner.original.mutation.checked(runner.original.mutation.FW_SOURCE, runner.original.mutation.FW_SHA)
        raw = Path('build/hyperrig-mini-audio-v3/hyperrig-mini.app-area.bin').read_bytes()
        self.assertEqual(runner.bench.digest(raw), runner.bench.IMAGE)
        decoded, _, _ = unpack_app(raw)
        for begin, end in ((0x02012A28, 0x02012A62), (0x02012BD6, 0x02012BEC), (0x0200EB78, 0x0200EBEA)):
            self.assertEqual(original[begin-0x02000120:end-0x02000120], decoded[begin-0x02000000:end-0x02000000])
        for address, value in ((0x02035B6A, b'FXR ok\0'),
                               (0x02039FF1, b'%s cpu=%u/%u ticks (%u%%) mem_fx=%u B\n\0')):
            self.assertEqual(original[address-0x02000120:address-0x02000120+len(value)], value)
            self.assertEqual(decoded[address-0x02000000:address-0x02000000+len(value)], value)

    def test_raw_RX_cannot_be_missing_when_decoded_removal_ack_exists(self):
        value = copy.deepcopy(self.native); g = value['guard']
        command = next(c for c in g['commands'] if c['line'] == 'FXR 5'); wire = g['wire'][command['wire_id']]
        g['rx'] = [r for r in g['rx'] if not wire['seq'] < r['seq'] < command['completed_seq']]
        with self.assertRaisesRegex(ValueError, 'absent from native RX'): runner.verify_report(value)

    def test_wrong_removal_format_with_coherent_RX_is_rejected(self):
        for wrong in ('FXR ok', 'FXR ok cpu=0/23018 ticks (0%)', 'FXR ok cpu=0/23018 ticks (0%) mem_fx=0 B extra'):
            value = copy.deepcopy(self.native); g = value['guard']
            command = next(c for c in g['commands'] if c['line'] == 'FXR 5'); wire = g['wire'][command['wire_id']]
            before = command['lines'][0]; command['lines'] = [wrong]
            for chunk in g['rx']:
                if wire['seq'] < chunk['seq'] < command['completed_seq']:
                    chunk['hex'] = bytes.fromhex(chunk['hex']).replace(before.encode(), wrong.encode()).hex()
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'FXR resource ACK'): runner.verify_report(value)

    def test_snapshot_relabel_or_wrong_ID_is_not_accepted(self):
        for change in ('id', 'epoch', 'removed'):
            value = copy.deepcopy(self.native)
            if change == 'id': value['temporary_instance_id'] = 0
            elif change == 'epoch':
                next(c for c in value['guard']['commands'] if c['line'] == 'FXS' and c['epoch'] == 4)['epoch'] = 3
            else: value['removed'] = copy.deepcopy(value['added'])
            with self.subTest(change=change), self.assertRaises(ValueError): runner.verify_report(value)

    def test_five_mutation_orchestration_restores_and_detaches_only_after_native_replay(self):
        updates = []; report = runner.experiment(copy.deepcopy(self.prepared), self.fake(), publish=updates.append)
        self.assertEqual(report['result'], 'pass', report.get('error') or report.get('cleanup_error'))
        self.assertTrue(report['temporary_effect_removal_verified'] and report['baseline_restoration_verified'])
        self.assertTrue(report['temporary_wrapper_removed'])
        self.assertTrue(all(not r['temporary_effect_removal_verified'] for r in updates[:-1]))
        self.assertEqual(report['restored']['state']['ir_current'], -1)

    def test_lost_removal_is_never_repeated_and_uncertain_UI_stays_blocked(self):
        report = runner.experiment(copy.deepcopy(self.prepared), self.fake(lost=True))
        self.assertEqual(report['result'], 'fail'); self.assertFalse(report['temporary_wrapper_removed'])
        lines = [w['line'] for w in report['guard']['wire']]
        self.assertEqual(lines.count('FXR 5'), 1); self.assertNotIn('PLOAD 0', lines)

    def test_valid_ack_but_effect_remaining_restores_once_without_success(self):
        report = runner.experiment(copy.deepcopy(self.prepared), self.fake(wrong_removed=True))
        self.assertEqual(report['result'], 'fail'); self.assertFalse(report['temporary_effect_removal_verified'])
        self.assertEqual([w['line'] for w in report['guard']['wire']].count('PLOAD 0'), 1)
        self.assertTrue(report['temporary_wrapper_removed'])

    def test_cleanup_error_cannot_promote_success(self):
        report = runner.experiment(copy.deepcopy(self.prepared), self.fake(cleanup_failure=True))
        self.assertEqual(report['result'], 'fail'); self.assertFalse(report['temporary_effect_removal_verified'])
        self.assertFalse(report['baseline_restoration_verified'])

    def test_default_cli_does_not_read_or_create_browser(self):
        with patch.object(runner, 'prepare', side_effect=AssertionError('read')), patch.object(runner.bench, 'CDP', side_effect=AssertionError('browser')):
            self.assertEqual(runner.main([]), 0)


if __name__ == '__main__': unittest.main()
