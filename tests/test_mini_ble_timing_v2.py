"""Offline checks for LVL-derived gain context; no BLE discovery or open."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'analysis/hardware/read_mini_ble_timing_after_restart_v2.py'
spec = importlib.util.spec_from_file_location('ble_timing_v2', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Actual closed BLE read01 response; test execution remains entirely offline.
LVL = 'LVL in=-367 out=-319 ci=0 co=0 fx=0/22368 mem=0 sk=0 m=2 g=0/0 b=1200 s=0 a=1 e=132082/154950 am=118688 c=11 p=0 tu=0 lim=0 ce=0 und=0 ovl=0 cin=-536 ctg=-180 fm=0,0,1,0 stuck=0 bat=-1,0,1'


class TimingV2Tests(unittest.TestCase):
    def test_actual_lvl_context_sends_only_lvl_and_records_derivation(self):
        class Probe:
            def __init__(self):
                self.calls, self.events = [], []
            def query(self, name):
                self.calls.append(name)
                return {'lines': [LVL]}
            def log(self, event, **fields):
                self.events.append((event, fields))
        probe = Probe()
        editor = module.ReadEditor(probe)
        self.assertEqual(editor.query('GAIN'), ['GAIN in=0 out=0 dB'])
        self.assertEqual(probe.calls, ['LVL'])
        self.assertNotIn('GAIN', module.SPECS)
        self.assertNotIn(b'GAIN\n', module.ALLOWED)
        event, record = probe.events[0]
        self.assertEqual(event, 'derived_gain_from_LVL')
        self.assertEqual(record['raw_reply'], [LVL])
        self.assertFalse(record['raw_GAIN_reply'])
        self.assertEqual(editor.derived_gain_from_LVL, [record])

    def test_exact_field_and_gain_bounds(self):
        self.assertEqual(module.gain_context_from_lvl(['LVL g=-30/12'])['gain'], [-30, 12])
        for raw in ([], [LVL, LVL], ['GAIN in=0 out=0 dB'], ['LVL m=2'],
                    ['LVL g=0/0 g=1/1'], ['LVL g=0/0junk'], ['LVL g=-31/0'],
                    ['LVL g=0/13'], ['LVL g=0/0\n'], ['LVL g=0/0'+('x'*8192)]):
            with self.subTest(raw=raw):
                with self.assertRaises(module.protocol.AppProbeError):
                    module.gain_context_from_lvl(raw)

    def test_prefix_terminators_use_query_word_boundary_once(self):
        self.assertTrue(module.SPECS['STAT'].complete('NIVEL pk_in=-90.0 clip_eng=0'))
        self.assertFalse(module.SPECS['STAT'].complete('T nproc=10'))
        self.assertFalse(module.SPECS['STAT'].complete('NIVELx clip_eng=0'))
        self.assertTrue(module.SPECS['CRASH'].complete('TRAP cpu=0'))
        self.assertTrue(module.SPECS['CRASH'].complete('CRASH end'))
        self.assertFalse(module.SPECS['CRASH'].complete('CRASH none cpu=0'))


if __name__ == '__main__':
    unittest.main()
