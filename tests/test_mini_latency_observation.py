import copy
import json
from pathlib import Path
import re
import unittest

from tools import mini_latency_observation as latency
from tools.mini_host_journal import read_shared_json


def replace_field(line, key, value):
    return re.sub(r'(?<!\S)'+re.escape(key)+r'=-?\d+(?= |$)', key+'='+str(value), line)


class LatencyObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = read_shared_json(Path('analysis/hardware/mini-v3-latency-baseline-01.json'))
        report = read_shared_json(Path('build/mini-first-preset-ui-02/report.json'))
        commands = report['guard']['commands']
        cls.fxt = next(c['lines'] for c in commands if c['line'] == 'FXT' and c['completed'])
        cls.clock = [c['lines'] for c in commands if c['line'] == 'CLKSTATE' and c['completed']][-1]

    def state(self):
        return {'FXS': list(self.actual['FXS']), 'MEM': list(self.actual['MEM']),
                'CLKSTATE': list(self.clock), 'GAIN': ['GAIN in=0 out=0 dB'],
                'MODEL': ["MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=0.0"]}

    def bundle(self):
        # The additional windows are explicitly host fixtures, never emitted
        # as physical evidence. Keep the real 23-line framing and RS history.
        raw = self.actual['observations'][0]['lines']
        samples = []
        for i in range(5):
            row = list(raw)
            for k in ('in', 'out'):
                row[0] = replace_field(row[0], k, 2455686+1200*i)
            row[0] = replace_field(row[0], 'blk', 1227842+600*i)
            row[1] = replace_field(row[1], 'jobs', 2455686+1200*i)
            row[2] = replace_field(row[2], 'nproc', 1227844+600*i)
            row[3] = replace_field(row[3], 'win', 2398+i)
            samples.append({'elapsed_ms': 1600*i, 'lines': row})
        return {'before': self.state(), 'after': self.state(), 'samples': samples}

    def test_real_baseline_parser_and_conversion(self):
        latency.verify_sources()
        got = [latency.stat(x['lines']) for x in self.actual['observations']]
        self.assertEqual([x['STG']['window'] for x in got], [2398, 2399, 2400])
        self.assertEqual([x['STG']['stages']['blk']['avg_ticks'] for x in got], [128708, 128731, 128706])
        self.assertAlmostEqual(max(x['STG']['stages']['blk']['max_ticks'] for x in got)/60000, 2.258366666666667)
        self.assertEqual(got[0]['clips'], {'input': 0, 'output': 0, 'limiter': 0, 'engine': 0})
        self.assertEqual(got[0]['rs_samples'], got[-1]['rs_samples'])

    def test_fresh_windows_exclude_settling_and_never_claim_analog(self):
        got = latency.analyze_measurement(self.bundle())
        self.assertTrue(got['measurement_complete'])
        self.assertEqual([w['window'] for w in got['eligible_windows']], [2400, 2401, 2402])
        self.assertEqual(got['A2_nproc_delta'], 2400)
        self.assertEqual(got['AUD_counter_delta']['blk'], 2400)
        self.assertEqual(got['DSP_counter_delta']['jobs'], 4800)
        self.assertEqual(got['FXS_counter_delta']['posts'], 0)
        self.assertFalse(got['analog_latency_measured'])
        self.assertFalse(got['hardware_transcript_authenticated_by_this_module'])
        self.assertFalse(got['RS_used_for_measurement'])
        self.assertEqual(got['capabilities_granted'], [])

    def test_repeated_stg_does_not_create_new_windows(self):
        value = self.bundle()
        for i, s in enumerate(value['samples']):
            s['lines'][3] = replace_field(s['lines'][3], 'win', 2398+i//2)
        got = latency.analyze_measurement(value)
        self.assertFalse(got['measurement_complete'])
        self.assertEqual([w['window'] for w in got['eligible_windows']], [2400])

    def test_isr_can_change_in_same_separate_window_but_stage_cannot(self):
        value = self.bundle()
        value['samples'][1]['lines'][3] = replace_field(value['samples'][1]['lines'][3], 'win', 2398)
        value['samples'][1]['lines'][3] = value['samples'][1]['lines'][3].replace('isr=404/1197', 'isr=405/1198')
        latency.analyze_measurement(value)
        value['samples'][1]['lines'][3] = value['samples'][1]['lines'][3].replace('blk=128708/133440', 'blk=128709/133440')
        with self.assertRaisesRegex(ValueError, 'same STG window changed'):
            latency.analyze_measurement(value)

    def test_changed_gain_or_clock_rejected(self):
        for key, new in [('GAIN', ['GAIN in=0 out=-1 dB']),
                         ('CLKSTATE', [self.clock[0].replace('mhz=360 ', 'mhz=372 ')])]:
            value = self.bundle(); value['after'][key] = new
            with self.assertRaisesRegex(ValueError, 'configuration changed'):
                latency.analyze_measurement(value)

    def test_fault_deltas_reported_without_discarding_measurement(self):
        value = self.bundle()
        value['samples'][-1]['lines'][0] = replace_field(value['samples'][-1]['lines'][0], 'und', 7)
        value['samples'][-1]['lines'][1] = replace_field(value['samples'][-1]['lines'][1], 'hw_to', 1)
        value['after']['FXS'][2] = value['after']['FXS'][2].replace(' to=0 ', ' to=2 ')
        got = latency.analyze_measurement(value)
        self.assertTrue(got['measurement_complete'])
        self.assertEqual(got['nonzero_fault_counter_deltas'], {'AUD.und': 7, 'DSP.hw_to': 1, 'FXS.to': 2})
        self.assertFalse(got['no_reported_faults_in_supplied_observations'])

    def test_intermediate_counter_reset_is_not_hidden_by_later_recovery(self):
        value = self.bundle()
        value['samples'][2]['lines'][0] = replace_field(value['samples'][2]['lines'][0], 'in', 1)
        with self.assertRaisesRegex(ValueError, 'counter regressed'):
            latency.analyze_measurement(value)

    def test_zero_clips_are_valid_but_clips_do_not_prove_progress(self):
        self.assertTrue(latency.analyze_measurement(self.bundle())['measurement_complete'])
        value = self.bundle()
        value['samples'][1]['lines'][2] = replace_field(value['samples'][1]['lines'][2], 'nproc', 1227844)
        value['samples'][1]['lines'][-1] = replace_field(value['samples'][1]['lines'][-1], 'clip_in', 200)
        with self.assertRaisesRegex(ValueError, 'completion progress'):
            latency.analyze_measurement(value)

    def test_full_stat_framing_required(self):
        value = self.bundle(); value['samples'][1]['lines'].pop(7)
        with self.assertRaisesRegex(ValueError, 'RS count/framing'):
            latency.analyze_measurement(value)

    def test_bounds_and_regression(self):
        for kind in ('time', 'sample_count', 'backwards', 'nonfinite'):
            value = self.bundle()
            if kind == 'time': value['samples'][-1]['elapsed_ms'] = 20001
            elif kind == 'sample_count': value['samples'] *= 3
            elif kind == 'backwards': value['samples'][1]['elapsed_ms'] = 0
            else: value['samples'][-1]['elapsed_ms'] = float('nan')
            with self.assertRaises(ValueError): latency.analyze_measurement(value)

    def test_actual_catalog_gradual_plan_and_conservative_parameters(self):
        got = latency.plan_stress(self.fxt, self.actual['FXS'], self.actual['MEM'], ['GAIN in=0 out=0 dB'])
        self.assertEqual(len(got['steps']), 13)
        self.assertEqual(got['steps'][-1]['published_cumulative_ticks'], 20095)
        self.assertEqual(got['measurement_after_counts'], [4, 8, 12, 13])
        self.assertEqual(got['setup_requests'], ['GAIN 0 -12'])
        self.assertEqual(got['restore_request'], 'PLOAD 0')
        self.assertFalse(got['executed'])
        self.assertFalse(got['save_or_delete_during_stress'])
        self.assertEqual(got['capabilities_granted'], [])
        for step in got['steps']:
            self.assertEqual(step['add_request'], f"FXA {step['bank']} 99 {step['type']}")
            self.assertEqual(step['configure_after_actual_id'][0]['request_template'], 'FXE {id} 0')
            self.assertEqual(step['configure_after_actual_id'][-1]['request_template'], 'FXE {id} 1')
            for change in step['configure_after_actual_id'][1:-1]:
                p = change['parameter']
                self.assertLessEqual(p['value'], p['default'])
                self.assertLessEqual(p['min'], p['value']); self.assertLessEqual(p['value'], p['max'])
        self.assertLessEqual(max(sum(s['bank'] == b for s in got['steps']) for b in ('P', 'Q')), 10)

    def test_plan_respects_smaller_budget_and_already_lower_gain(self):
        fxs = [s.replace('0/21364 ticks', '0/5000 ticks') for s in self.actual['FXS']]
        got = latency.plan_stress(self.fxt, fxs, self.actual['MEM'], ['GAIN in=0 out=-20 dB'])
        self.assertTrue(got['skipped'])
        self.assertLessEqual(got['steps'][-1]['published_cumulative_ticks'], 5000)
        self.assertEqual(got['setup_requests'], [])

    def test_plan_rejects_existing_chain_and_incomplete_catalog(self):
        fxs = ['FX P0 id=0 gate on=1 p=-90,120,0,0,0,0,0 ticks=490']+self.actual['FXS']
        with self.assertRaisesRegex(ValueError, 'saved A2-only baseline'):
            latency.plan_stress(self.fxt, fxs, self.actual['MEM'], ['GAIN in=0 out=0 dB'])
        with self.assertRaises(Exception):
            latency.plan_stress(self.fxt[:-1], self.actual['FXS'], self.actual['MEM'], ['GAIN in=0 out=0 dB'])

    def test_overbudget_observation_is_retained_as_observation(self):
        value = self.bundle()
        value['after']['FXS'][1] = 'FXS cpu=22000/21364 ticks (103%) mem_fx=0 B'
        got = latency.analyze_measurement(value)
        self.assertEqual(got['after']['resources']['cost_ticks'], 22000)
        self.assertEqual(got['after']['resources']['budget_ticks'], 21364)


if __name__ == '__main__':
    unittest.main()
