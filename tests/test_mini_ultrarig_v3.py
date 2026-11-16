"""Offline revision3 composition: exact v2 preservation and one PC-bound fix."""
import copy
from pathlib import Path
import tempfile
import unittest

from hyperrig.jieli import unpack_app
from tools import build_mini_ultrarig_v3 as v3


class Revision3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = v3.load_baseline()
        cls.g = (v3.ROOT/v3.G_PATH).read_bytes()
        cls.mini = (v3.ROOT/v3.MINI_PATH).read_bytes()
        cls.image, cls.composition, cls.audit = v3.compose_revision(cls.baseline, cls.g, cls.mini)

    def test_new_image_has_valid_CRC_and_exactly_one_changed_sector(self):
        self.assertNotEqual(v3.sha(self.image), v3.BASELINE_SHA)
        plain, entries, files = unpack_app(self.image)
        self.assertEqual(len(self.image), 0x7E000)
        self.assertEqual([s['physical_address'] for s in self.audit['changed_sectors_vs_v2']], [0x4000])
        self.assertEqual(self.composition['app_bytes'], len(files['app.bin']))
        self.assertTrue(self.audit['JLFS_CRC_SFC_roundtrip_passed'])
        for entry in entries[3:]:
            self.assertEqual(entry.to_dict(), next(e for e in self.baseline['integration']['composition']['directory'] if e['name']==entry.name))
        self.assertEqual(plain[0x67E:0x684], bytes.fromhex(self.audit['new_PC_patches'][0]['after_hex']))

    def test_exact_audio_guard_and_original_RAM_source_are_preserved(self):
        old_plain, _, old_files = unpack_app(self.baseline['image'])
        plain, _, files = unpack_app(self.image)
        original_length = self.baseline['integration']['composition']['original_application_bytes_retained']
        self.assertEqual(files['app.bin'][original_length:], self.baseline['audio_bytes']+self.baseline['guard_bytes'])
        self.assertEqual(files['app.bin'][original_length:], old_files['app.bin'][original_length:])
        self.assertEqual(files['cfg_tool.bin'], old_files['cfg_tool.bin'])
        for offset in (0x1B8, 0x1DC): self.assertEqual(plain[offset:offset+6], old_plain[offset:offset+6])
        self.assertEqual(self.audit['PC_limit_new_upper'], self.baseline['recovery']['component']['address']+len(self.baseline['guard_bytes']))
        self.assertEqual(self.audit['PC_limit_new_upper'], 0x020774F2)
        self.assertEqual(self.audit['PC_limit_RAM_unchanged'], [0x01C00000, 0x01C1F088])
        self.assertGreater(self.baseline['audio']['payload']['base'], self.audit['PC_limit_old_upper'])
        self.assertLess(self.baseline['recovery']['component']['address'], self.audit['PC_limit_new_upper'])

    def test_inverse_new_patch_recovers_entire_v2_application(self):
        _, _, old_files = unpack_app(self.baseline['image'])
        _, _, files = unpack_app(self.image)
        restored = bytearray(files['app.bin'])
        for patch in self.audit['new_PC_patches']:
            offset = patch['cpu_address']-v3.ENTRY
            restored[offset:offset+patch['bytes']] = bytes.fromhex(patch['before_hex'])
        self.assertEqual(bytes(restored), old_files['app.bin'])
        self.assertTrue(self.composition['original_application_recovered_exactly_by_reversing_patches'])
        self.assertEqual(len(self.composition['patches']), len(self.baseline['integration']['composition']['patches'])+1)

    def test_changed_or_truncated_components_and_stale_end_are_rejected(self):
        for fault in ('audio', 'guard', 'end', 'address', 'base_image'):
            with self.subTest(fault=fault):
                data = copy.deepcopy(self.baseline)
                if fault == 'audio': data['audio_bytes'] = bytes([data['audio_bytes'][0]^1])+data['audio_bytes'][1:]
                elif fault == 'guard': data['guard_bytes'] = data['guard_bytes'][:-2]
                elif fault == 'end': data['recovery']['component']['end_exclusive'] += 2
                elif fault == 'address': data['recovery']['component']['address'] += 4
                else: data['image'] = data['image'][:-1]+bytes([data['image'][-1]^1])
                with self.assertRaises(ValueError): v3.compose_revision(data, self.g, self.mini)

    def test_unlisted_baseline_patch_cannot_be_silently_retained(self):
        data = copy.deepcopy(self.baseline)
        row = data['integration']['composition']['patches'][-1]
        row['after_hex'] = '00'+row['after_hex'][2:]
        with self.assertRaises(ValueError): v3.compose_revision(data, self.g, self.mini)

    def test_full_build_binds_new_editor_and_does_not_overwrite_frozen_inputs(self):
        with tempfile.TemporaryDirectory(dir=v3.ROOT/'build', prefix='TEST-mini-v3-') as folder:
            output = Path(folder)/'candidate'
            report = v3.build(output)
            self.assertEqual((output/'hyperrig-mini.app-area.bin').read_bytes(), self.image)
            self.assertEqual(report['composition'], self.composition)
            self.assertFalse(report['boot_verified_on_mini'] or report['audio_verified_on_mini'])
            import json
            editor = json.loads((output/'editor-report.json').read_text())
            profile = editor['profile']
            self.assertEqual(profile['image_sha256'], v3.sha(self.image))
            self.assertTrue(profile['capabilities']['read'])
            self.assertFalse(profile['hardware_verified'] or profile['capabilities']['write'] or profile['capabilities']['panel'])
            self.assertFalse(profile['family_capabilities'] or profile['command_capabilities'])
            self.assertIn(v3.sha(self.image), (output/'app/web/tankmini.html').read_text(encoding='utf-8'))
            self.assertEqual((output/'entry-recovery-manifest.json').read_bytes(),
                             (v3.ROOT/v3.BASELINE/'entry-recovery-manifest.json').read_bytes())
            with self.assertRaises(ValueError): v3.build(output)
        for name, digest in self.baseline['pins'].items(): self.assertEqual(v3.sha((v3.ROOT/name).read_bytes()), digest)

    def test_existing_v2_directory_is_refused_before_build(self):
        with self.assertRaises(ValueError): v3.build(v3.ROOT/v3.BASELINE)


if __name__ == '__main__': unittest.main()
