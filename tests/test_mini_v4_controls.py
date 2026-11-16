import copy
import unittest

from tools import qualify_mini_v4_controls as controls


class ControlsPlanTests(unittest.TestCase):
    def setUp(self):
        self.state = {'plist': {'ok': True, 'current': 0, 'presets': [{'slot': 0}, {'slot': 31}]},
                      'fxs': {'blocks': [], 'mix': [], 'xo': []},
                      'snaps': {'current': 3, 'present': '1111'},
                      'extra': {'gain_db': [0, 0]}}
        self.types = {'gate': {'params': {0: {'name': 'umbral_db', 'min': -90, 'max': 0, 'default': -70}}}}

    def test_temporary_slot_never_overwrites_existing_presets(self):
        original = copy.deepcopy(self.state)
        result = controls.plan(self.state, self.types)
        self.assertEqual(result['slot'], 30)
        self.assertEqual(result['trial_gain'], [0, -1])
        self.assertEqual(self.state, original)

    def test_full_bank_rejected(self):
        self.state['plist']['presets'] = [{'slot': n} for n in range(32)]
        with self.assertRaisesRegex(controls.protocol.Error, 'free temporary'):
            controls.plan(self.state, self.types)

    def test_unknown_live_chain_rejected(self):
        self.state['fxs']['blocks'] = [{'id': 0}]
        with self.assertRaisesRegex(controls.protocol.Error, 'empty serial'):
            controls.plan(self.state, self.types)

    def test_scene_zero_cannot_be_the_original_scene(self):
        self.state['snaps']['current'] = 0
        with self.assertRaisesRegex(controls.protocol.Error, 'other than zero'):
            controls.plan(self.state, self.types)

    def test_changed_catalog_rejected(self):
        self.types['gate']['params'][0]['max'] = -80
        with self.assertRaisesRegex(controls.protocol.Error, 'catalog differs'):
            controls.plan(self.state, self.types)

    def test_add_response_waits_for_resource_line(self):
        query = controls.FxQuery('FXA Q 99 gate', 4, ())
        self.assertFalse(query.complete('FXA id=0 gate'))
        self.assertTrue(query.complete('FX cpu=490/23040 ticks (2%) mem_fx=0 B'))


if __name__ == '__main__':
    unittest.main()
