"""Offline only: original JS queue/streams and synthetic host orchestration."""
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import Mock, patch

from tools import probe_mini_browser_latency as runner
from tools.mini_host_journal import read_shared_json
from tests.test_mini_latency_observation import replace_field


PONG = 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'
ACK = "PLOAD ok 0 'Preset 1A'"


class Clock:
    def __init__(self): self.now = 0
    def __call__(self): return self.now
    def sleep(self, seconds): self.now += seconds


class FakeEditor:
    """A one-gate synthetic firmware; never opens a device or browser."""
    def __init__(self, responses, fxt, stat, mem, *, reject=False, timeout=False,
                 bad_readback=False, refresh_failure=False, baseline_fault=False, stale=False):
        self.responses = copy.deepcopy(responses)
        self.fxt, self.stat_rows, self.mem = fxt, stat, mem
        self.reject, self.timeout, self.bad_readback = reject, timeout, bad_readback
        self.refresh_failure, self.baseline_fault, self.stale = refresh_failure, baseline_fault, stale
        self.gain, self.block, self.samples, self.refreshed, self.configured = [0, 0], None, 0, False, False
        self.g = dict(detached=False, healthy=True, fatal=None, phase='observing', epoch=0,
                      seq=0, commands=[], wire=[], rx=[], events=[], created=[], mutations=0, restoreIssued=False)

    def seq(self):
        self.g['seq'] += 1
        return self.g['seq']

    def record(self, line, rows, *, priming=False, lost=False):
        c = dict(id=len(self.g['commands']), line=line, epoch=self.g['epoch'],
                 seq=self.seq(), completed=False, priming=priming)
        self.g['commands'].append(c)
        w = dict(id=len(self.g['wire']), command_id=c['id'], line=line,
                 hex=(line+'\n').encode().hex(), seq=self.seq(), completed=not lost,
                 mutation=not runner.original.evidence.is_query(line))
        self.g['wire'].append(w); c['wire_id'] = w['id']
        if lost:
            self.g.update(healthy=False, fatal='synthetic write timeout')
            raise TimeoutError('synthetic write timeout; no retry')
        if not priming:
            self.g['rx'].append(dict(seq=self.seq(), hex=('\n'.join(rows)+'\n').encode().hex()))
        c.update(lines=list(rows), completed=True, completed_seq=self.seq(), native_RX_verified=not priming)
        return rows

    def install(self, prepared): self.installed = True
    def prime(self): self.record('PING', [PONG], priming=True)
    def state(self): return copy.deepcopy(self.g)

    def query(self, line):
        if line == 'PING': rows = [PONG]
        elif line == 'FXT': rows = self.fxt
        elif line == 'MEM': rows = self.mem
        elif line == 'GAIN': rows = [f'GAIN in={self.gain[0]} out={self.gain[1]} dB']
        elif line == 'LVL': rows = [re.sub(r' g=-?\d+/-?\d+ ', f' g={self.gain[0]}/{self.gain[1]} ', self.responses[line][0])]
        elif line == 'FXS':
            rows = list(self.responses[line])
            if self.block:
                on = 0 if self.bad_readback and self.g['phase'] == 'between' else self.block['on']
                rows.insert(1, f'FX P0 id=0 gate on={on} p={self.block["p"]},120,0,0,0,0,0 ticks=490')
                rows = [x.replace('cpu=0/490', 'cpu=490/490') for x in rows]
        elif line == 'STAT':
            rows = list(self.stat_rows); i = self.samples; self.samples += 1
            for key in ('in', 'out'): rows[0] = replace_field(rows[0], key, 3000000+1200*i)
            rows[0] = replace_field(rows[0], 'blk', 1500000+600*i)
            if self.baseline_fault: rows[0] = replace_field(rows[0], 'und', i)
            rows[1] = replace_field(rows[1], 'jobs', 3000000+1200*i)
            rows[2] = replace_field(rows[2], 'nproc', 1500000+600*i)
            rows[3] = replace_field(rows[3], 'win', 3000+(0 if self.stale else i))
            rows[-1] = re.sub(r' gain=-?\d+/-?\d+ ', f' gain={self.gain[0]}/{self.gain[1]} ', rows[-1])
        else: rows = self.responses[line]
        return self.record(line, list(rows))

    def snapshot(self):
        rows = {k: self.query(k) for k in runner.original.READS}
        return dict(responses=rows, state=runner.original.parse_snapshot(rows))

    def context(self):
        return {k: self.query(k) for k in ('CLKSTATE', 'MODEL', 'GAIN', 'FXS', 'MEM')}

    def configure(self, plan):
        self.configured = True; self.plan = plan; self.substep = 0
        self.g['events'].append(dict(kind='plan', seq=self.seq(), plan=copy.deepcopy(plan)))
        self.g['phase'] = 'attenuate' if plan['setup_requests'] else 'add'

    def next(self):
        phase = self.g['phase']; rejected = False
        if phase == 'attenuate':
            line = self.plan['setup_requests'][0]; self.gain = list(self.plan['trial_gain'])
            rows = [f'GAIN in={self.gain[0]} out={self.gain[1]} dB']; next_phase = 'add'
        elif phase == 'add':
            line = self.plan['steps'][0]['add_request']
            if self.reject:
                rows = ['ERR FXA not enough CPU']; next_phase = 'rejected'; rejected = True
            else:
                rows = ['FXA id=0 gate', 'FX cpu=490/490 ticks (100%) mem_fx=0 B']; next_phase = 'configure'
                self.block = dict(on=1, p=-70)
        elif phase == 'configure':
            changes = self.plan['steps'][0]['configure_after_actual_id']
            line = changes[self.substep]['request_template'].replace('{id}', '0')
            if line.startswith('FXE'): self.block['on'] = int(line.split()[2]); rows = ['FXE ok']
            else: self.block['p'] = int(line.split()[3]); rows = ['FXP ok '+line.split()[3]]
            self.substep += 1
            next_phase = 'between' if self.substep == len(changes) else 'configure'
        elif phase == 'restoring':
            line, rows, next_phase = 'PLOAD 0', [ACK+' missing=0 capture=0 ir=-1 ms=2'], 'restored_ack'
            self.gain, self.block = [0, 0], None
        else: raise AssertionError('unexpected fake phase '+phase)
        self.record(line, rows, lost=self.timeout and phase == 'add')
        if phase == 'add' and not rejected: self.g['created'] = [dict(id=0, type='gate', bank='P')]
        self.g['mutations'] += 1; self.g['epoch'] += 1; self.g['phase'] = next_phase
        return dict(line=line, reply=rows, rejected=rejected)

    def advance(self): self.g['phase'] = 'stress_done'
    def restore(self):
        assert self.g['healthy'] and not self.g['restoreIssued']
        self.g['restoreIssued'] = True; self.g['phase'] = 'restoring'
        return self.next()

    def refresh(self, baseline):
        if self.refresh_failure: raise RuntimeError('synthetic UI readback mismatch')
        self.refreshed = True
        return {'gain': list(self.gain), 'capture': 0, 'preset': 0, 'scene': 0, 'chain': {'P': [], 'Q': []}}

    def detach(self, restored):
        unchanged = self.g['healthy'] and not any(w['mutation'] for w in self.g['wire'])
        self.g['detached'] = restored or unchanged
        if not self.g['detached']: self.g['healthy'] = False
        return self.state()


class BrowserLatencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        saved = read_shared_json(Path('build/mini-first-preset-ui-04/report.json'))['saved']
        cls.responses = {k: saved['responses'][k] for k in runner.original.READS}
        cls.responses['FXS'] = [re.sub(r'/\d+ ticks', '/490 ticks', x) for x in cls.responses['FXS']]
        cls.baseline = runner.original.parse_snapshot(cls.responses)
        real = read_shared_json(Path('analysis/hardware/mini-v3-latency-baseline-01.json'))
        cls.stat, cls.mem = real['observations'][0]['lines'], real['MEM']
        rows = read_shared_json(Path('build/mini-first-preset-ui-02/report.json'))['guard']['commands']
        cls.fxt = next(c['lines'] for c in rows if c['line'] == 'FXT' and c['completed'])
        cls.prepared = dict(baseline=cls.baseline, pong=PONG, restore_ack_prefix=ACK)
        plan = runner.timing.plan_stress(cls.fxt, real['FXS'], real['MEM'], ['GAIN in=0 out=0 dB'])
        command = ['node', 'tests/mini_browser_latency_guard_test.js', 'tools/mini_browser_latency_guard.js',
                   'build/hyperrig-mini-audio-v3/app/web/tankmini.html', 'app/mini/mini-profile.js', '--catalog-from-stdin']
        result = subprocess.run(command, input=json.dumps({'fxt': cls.fxt, 'plan': plan}),
                                capture_output=True, text=True, check=True)
        cls.node = json.loads(result.stdout)

    def fake(self, **kwargs): return FakeEditor(self.responses, self.fxt, self.stat, self.mem, **kwargs)

    def run_experiment(self, editor):
        clock = Clock(); saved = []
        report = runner.experiment(copy.deepcopy(self.prepared), editor, clock=clock, sleep=clock.sleep,
                                   publish=lambda value: saved.append(value))
        return report, saved

    def test_original_node_native_trace_replayed_in_python(self):
        self.assertGreaterEqual(self.node['checks'], 37)
        for name in ('success_trace', 'rejected_trace'):
            out = runner.verify_trace(self.node[name], ACK, PONG)
            self.assertEqual(out['actual_mutation_requests'][-1], 'PLOAD 0')
            self.assertEqual(out['reader_hook_priming_queries_not_claimed_as_raw_RX_proof'], ['PING'])

    def test_native_rx_cannot_be_omitted_with_decoded_ack_retained(self):
        value = copy.deepcopy(self.node['success_trace'])
        command = next(c for c in value['commands'] if c['line'].startswith('FXP '))
        wire = value['wire'][command['wire_id']]
        value['rx'] = [r for r in value['rx'] if not wire['seq'] < r['seq'] < command['completed_seq']]
        with self.assertRaisesRegex(ValueError, 'absent from native bytes'):
            runner.verify_trace(value, ACK, PONG)

    def test_trace_plan_identity_ids_and_restore_are_not_advisory(self):
        for change in ('plan', 'id', 'pong', 'restore', 'priming_mutation'):
            value = copy.deepcopy(self.node['success_trace'])
            if change == 'plan':
                next(e for e in value['events'] if e['kind'] == 'plan')['plan']['steps'][0]['add_request'] = 'FXA Q 99 gate'
            elif change == 'id': value['wire'][1]['id'] = 0
            elif change == 'pong': value['commands'][1]['lines'] = ['PONG other']
            elif change == 'restore': value['restoreIssued'] = False
            else: next(c for c in value['commands'] if c['line'].startswith('FXP '))['priming'] = True
            with self.subTest(change=change), self.assertRaises(ValueError): runner.verify_trace(value, ACK, PONG)

    def test_success_restores_native_state_then_original_ui_and_no_grants(self):
        editor = self.fake(); report, updates = self.run_experiment(editor)
        self.assertEqual(report['result'], 'pass', report)
        self.assertEqual([x['instances'] for x in report['measurements']], [0, 1])
        self.assertTrue(report['baseline_restoration_verified']); self.assertTrue(editor.refreshed)
        self.assertTrue(report['temporary_wrapper_removed'])
        self.assertTrue(report['observation_verification']['observations_bound_to_native_commands'])
        self.assertEqual(report['maximum_admitted_instances_observed'], 1)
        self.assertEqual([w['line'] for w in report['guard']['wire'] if w['mutation']],
                         ['GAIN 0 -12', 'FXA P 99 gate', 'FXE 0 0', 'FXP 0 0 -90', 'FXE 0 1', 'PLOAD 0'])
        self.assertFalse(report['analog_latency_measured']); self.assertEqual(report['mutation_families_granted'], [])
        self.assertTrue(all(not v['baseline_restoration_verified'] for v in updates[:-1]))

    def test_resource_rejection_is_real_reply_and_restores_once(self):
        editor = self.fake(reject=True); report, _ = self.run_experiment(editor)
        self.assertEqual(report['result'], 'pass', report)
        self.assertIn('resource/control rejection', report['stop_reason'])
        self.assertEqual(report['maximum_admitted_instances_observed'], 0)
        self.assertEqual([w['line'] for w in report['guard']['wire'] if w['mutation']],
                         ['GAIN 0 -12', 'FXA P 99 gate', 'PLOAD 0'])

    def test_timeout_has_no_retry_or_restoration_and_leaves_ui_blocked(self):
        report, _ = self.run_experiment(self.fake(timeout=True))
        self.assertEqual(report['result'], 'fail'); self.assertFalse(report['baseline_restoration_verified'])
        self.assertFalse(report['temporary_wrapper_removed'])
        lines = [w['line'] for w in report['guard']['wire']]
        self.assertEqual(lines.count('FXA P 99 gate'), 1); self.assertNotIn('PLOAD 0', lines)

    def test_valid_communication_with_bad_effect_readback_restores_but_is_not_success(self):
        report, _ = self.run_experiment(self.fake(bad_readback=True))
        self.assertEqual(report['result'], 'fail')
        self.assertTrue(report['baseline_restoration_verified'], report)
        self.assertEqual([w['line'] for w in report['guard']['wire']].count('PLOAD 0'), 1)

    def test_ui_refresh_failure_cannot_claim_restoration_or_repeat_pload(self):
        report, _ = self.run_experiment(self.fake(refresh_failure=True))
        self.assertEqual(report['result'], 'fail'); self.assertFalse(report['baseline_restoration_verified'])
        self.assertFalse(report['temporary_wrapper_removed'])
        self.assertEqual([w['line'] for w in report['guard']['wire']].count('PLOAD 0'), 1)

    def test_baseline_fault_stops_before_configure_or_any_mutation(self):
        editor = self.fake(baseline_fault=True); report, _ = self.run_experiment(editor)
        self.assertEqual(report['result'], 'fail'); self.assertFalse(editor.configured)
        self.assertIn('baseline processing faults', report['error'])
        self.assertFalse(any(w['mutation'] for w in report['guard']['wire']))
        self.assertTrue(report['temporary_wrapper_removed'])

    def test_stale_windows_stop_at_finite_read_budget_without_mutation(self):
        editor = self.fake(stale=True); report, _ = self.run_experiment(editor)
        self.assertEqual(report['result'], 'fail'); self.assertLessEqual(editor.samples, 12)
        self.assertFalse(any(w['mutation'] for w in report['guard']['wire']))
        self.assertIn('finite read budget', report['error'])

    def test_report_cannot_replace_measurement_or_claim_another_epoch(self):
        report, _ = self.run_experiment(self.fake())
        for change in ('ticks', 'epoch', 'instance_count', 'restore_snapshot'):
            value = copy.deepcopy(report)
            if change == 'ticks': value['measurements'][0]['measurement']['eligible_windows'][0]['stages']['blk']['avg_ticks'] += 1
            elif change == 'epoch': next(c for c in value['guard']['commands'] if c['line'] == 'STAT')['epoch'] += 1
            elif change == 'instance_count': value['measurements'][1]['instances'] = 16
            else: value['restored']['responses']['GAIN'] = ['GAIN in=0 out=-1 dB']
            with self.subTest(change=change), self.assertRaises((ValueError, runner.original.mutation.Error)):
                runner.verify_observations(value, value['guard'])

    def test_default_cli_does_not_prepare_or_create_cdp(self):
        with (patch.object(runner, 'prepare', side_effect=AssertionError('file read')),
              patch.object(runner, 'CDP', side_effect=AssertionError('browser access'))):
            self.assertEqual(runner.main([]), 0)

    def preflight_fixture(self):
        from tools import qualify_mini_browser_preset as qualifier
        proof = dict(profile={'test': 'synthetic qualified bundle'}, image_sha256=runner.IMAGE, pong=PONG,
            qualification=dict(one_reload_verified=True, hardware_executed=True, preset_intentionally_retained=True,
                restoration_verified=False, physically_exercised_requests={'PLOAD': ['PLOAD 0']},
                reloaded_snapshot=dict(responses=copy.deepcopy(self.responses), state=copy.deepcopy(self.baseline)),
                reloaded_report={'path': 'synthetic-only.json', 'sha256': '0'*64}))
        sources = {name: runner.digest((runner.ROOT/name).read_bytes()) for name in
                   ('tools/launch_mini_editor.py', 'tools/qualify_mini_browser_preset.py')}
        session = dict(kind='mini-qualified-editor-session', phase='connected_qualified_USB', identity_verified=True,
            prepared=dict(bundle_directory='build/synthetic-qualification', bundle=proof, profile=proof['profile']),
            source_sha256=sources, CDP_page_websocket='ws://127.0.0.1:9222/devtools/page/fake-123', origin='http://127.0.0.1:8080')
        path = runner.ROOT/'build/synthetic-latency-session/session.json'
        def read(p):
            return json.dumps(session).encode() if p == path else Path(p).read_bytes()
        return qualifier, proof, session, path, read

    def test_preflight_accepts_retained_preset_without_fabricated_global_restoration(self):
        qualifier, proof, session, path, read = self.preflight_fixture()
        with (patch.object(qualifier, 'validate_bundle', return_value=proof),
              patch.object(runner, 'read_shared_bytes', side_effect=read),
              patch.object(runner, 'CDP', side_effect=AssertionError('no browser'))):
            got = runner.prepare(path)
        self.assertFalse(proof['qualification']['restoration_verified'])
        self.assertEqual(got['restore_ack_prefix'], ACK)
        self.assertEqual(got['families_granted_by_this_experiment'], [])

    def test_preflight_refuses_partial_save_missing_reload_and_unowned_session(self):
        for change in ('reload', 'physical', 'request', 'source', 'websocket', 'finished'):
            qualifier, proof, session, path, read = self.preflight_fixture()
            if change == 'reload': proof['qualification']['one_reload_verified'] = False
            elif change == 'physical': proof['qualification']['hardware_executed'] = False
            elif change == 'request': proof['qualification']['physically_exercised_requests']['PLOAD'] = []
            elif change == 'source': session['source_sha256'] = {}
            elif change == 'websocket': session['CDP_page_websocket'] = 'ws://example.com/devtools/page/remote'
            else: session['finished_utc'] = '2026-11-16T00:00:00Z'
            with (self.subTest(change=change), patch.object(qualifier, 'validate_bundle', return_value=proof),
                  patch.object(runner, 'read_shared_bytes', side_effect=read), self.assertRaises(ValueError)):
                runner.prepare(path)

    def test_original_ui_refresh_requires_both_preset_variables_and_fresh_gain(self):
        good = dict(gain=[0, 0], chain={'P': [], 'Q': []}, model='A2', capture=0, scene=0,
                    scenes=[1, 0, 0, 0], preset=0, firmwarePreset=0, amp=1, ampPresent=1)
        cdp = Mock(); cdp.evaluate.return_value = good
        self.assertEqual(runner.ExistingEditor(cdp).refresh(self.baseline), good)
        expression = cdp.evaluate.call_args.args[0]
        for call in ('applyLvl(', 'loadChain()', 'loadSnaps()', 'loadModelName()', 'preset:curPreset', 'firmwarePreset:S.curPre'):
            self.assertIn(call, expression)
        for key, bad in (('preset', 1), ('firmwarePreset', -1), ('gain', [0, -12]), ('scene', 1)):
            cdp.evaluate.return_value = {**good, key: bad}
            with self.subTest(key=key), self.assertRaises(ValueError): runner.ExistingEditor(cdp).refresh(self.baseline)


if __name__ == '__main__': unittest.main()
