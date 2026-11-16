"""Product presentation, sealed capabilities, and offline launcher behavior."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import build_hyperrig_editor as product
from tools import launch_hyperrig_editor as launcher


class HyperRigProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = product.ROOT / 'build/hyperrig-mini-english-editor'
        cls.proof = product.validate_bundle(cls.folder)

    def test_launcher_default_has_no_side_effects(self):
        with patch.object(launcher, 'prepare', side_effect=AssertionError('unexpected read')):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(launcher.main([]), 0)
        self.assertFalse(json.loads(output.getvalue())['browser_started'])

    def test_preflight_retains_exact_hardware_scope(self):
        prepared = launcher.prepare(self.folder)
        self.assertEqual(prepared['enabled_families'], {'usb-cdc': product.FAMILIES})
        self.assertFalse(prepared['profile']['capabilities']['panel'])
        self.assertFalse(prepared['profile']['capabilities']['write'])
        self.assertEqual(prepared['image_sha256'], product.baseline.IMAGE)
        self.assertFalse(prepared['qualification_UI_FX_interactions_physically_tested'])

    def clone(self, folder):
        shutil.copytree(self.folder, folder, dirs_exist_ok=True)
        meta = json.loads((folder / 'bundle.json').read_bytes())
        meta['proof']['app_directory'] = (folder / 'app/web').relative_to(product.ROOT).as_posix()
        meta['serial_open_extension'] = (folder / 'app/web/serial-open-timeout.js').relative_to(product.ROOT).as_posix()
        self.seal(folder, meta)
        product.validate_bundle(folder)
        return meta

    def seal(self, folder, meta):
        raw = product.encoded(meta)
        (folder / 'bundle.json').write_bytes(raw)
        (folder / 'bundle.sha256').write_text(product.sha(raw) + '\n', encoding='ascii')

    def test_modified_runtime_file_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=product.ROOT / 'build') as name:
            folder = Path(name)
            self.clone(folder)
            with (folder / 'app/web/mini-profile.js').open('a', encoding='utf-8') as stream:
                stream.write('\n// changed\n')
            with self.assertRaisesRegex(ValueError, 'Product file differs'):
                product.validate_bundle(folder)

    def test_resealed_scope_expansion_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=product.ROOT / 'build') as name:
            folder = Path(name)
            meta = self.clone(folder)
            meta['proof']['profile']['family_capabilities']['ble-nus'] = ['FXP']
            self.seal(folder, meta)
            with self.assertRaisesRegex(ValueError, 'qualified capabilities'):
                product.validate_bundle(folder)

    def test_original_notices_and_converter_are_byte_identical(self):
        baseline = product.ROOT / 'build/hyperrig-mini-fx-editor/app'
        for filename in ['LICENSE.md', 'NOTICE.md', 'THIRD_PARTY_LICENSES.md', 'web/nam2chip.js']:
            self.assertEqual((self.folder / 'app' / filename).read_bytes(), (baseline / filename).read_bytes())


if __name__ == '__main__':
    unittest.main()
