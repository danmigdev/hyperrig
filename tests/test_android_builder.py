import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import build_android_editor as android


class AndroidBuilder(unittest.TestCase):
    def test_publishable_key_and_editor_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / 'key'
            key.write_text('t3k_pub_example123', encoding='utf-8')
            self.assertEqual(android.tone_key(key), 't3k_pub_example123')
            source = b'if (location.protocol !== "hyperrig:") return; src: "tone3000/picture?id=" + tone.id'
            adapted = android.mobile_tone(source, android.tone_key(key))
            self.assertIn(b't3k_pub_example123', adapted)
            self.assertIn(b'isNativePlatform', adapted)
            self.assertEqual(android.mobile_tone(source, None), source)
            key.write_text('t3k_cs_secret123', encoding='utf-8')
            with self.assertRaises(ValueError):
                android.tone_key(key)
            with self.assertRaises(ValueError):
                android.mobile_tone(b'unknown editor', 't3k_pub_example123')

    def test_stages_only_checked_matching_editor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'firmware/ultrarig/mini/product').mkdir(parents=True)
            (root / 'firmware/ultrarig/mini/product/VERSION').write_text('0.6.0', encoding='utf-8')
            (root / 'app/android').mkdir(parents=True)
            (root / 'app/android/package.json').write_text('{}', encoding='utf-8')
            (root / 'app/android/www').mkdir()
            (root / 'app/android/www/stale.html').write_text('old', encoding='utf-8')
            bundle = root / 'bundle'
            (bundle / 'editor/web').mkdir(parents=True)
            (bundle / 'editor/web/index.html').write_text('new', encoding='utf-8')
            for name in ('LICENSE.md', 'NOTICE.md', 'THIRD_PARTY_LICENSES.md'):
                (bundle / 'editor' / name).write_text(name, encoding='utf-8')
            (bundle / 'bundle.json').write_text(json.dumps({'area': {'product': {'version': '0.6.0'}}}), encoding='utf-8')
            with patch.object(android, 'ROOT', root), patch.object(android.editor, 'check') as check:
                out = root / 'build/android'
                self.assertEqual(android.prepare(bundle, out), '0.6.0')
                check.assert_called_once_with(bundle.resolve())
                self.assertEqual((out / 'www/index.html').read_text(), 'new')
                self.assertTrue((out / 'www/licenses/LICENSE.md').is_file())
                self.assertFalse((out / 'www/stale.html').exists())
                with self.assertRaises(Exception):
                    android.prepare(bundle, out)
                (root / 'firmware/ultrarig/mini/product/VERSION').write_text('0.7.0', encoding='utf-8')
                with self.assertRaises(Exception):
                    android.prepare(bundle, root / 'build/wrong-version')
                self.assertFalse((root / 'build/wrong-version').exists())

    def test_check_rejects_changed_editor_and_missing_bluetooth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            web = root / 'bundle/editor/web'
            web.mkdir(parents=True)
            (web / 'index.html').write_bytes(b'editor')
            (root / 'bundle/bundle.json').write_text(json.dumps({'area': {'product': {'version': '0.6.0'}}}), encoding='utf-8')
            (root / 'firmware/ultrarig/mini/product').mkdir(parents=True)
            (root / 'firmware/ultrarig/mini/product/VERSION').write_text('0.6.0', encoding='utf-8')
            apk = root / 'app.apk'
            def make(content, plugin):
                with zipfile.ZipFile(apk, 'w') as archive:
                    archive.writestr('assets/public/index.html', content)
                    archive.writestr('assets/capacitor.plugins.json', json.dumps(plugin))
                    archive.writestr('AndroidManifest.xml', b'manifest')
            plugin = [{'classpath': 'com.capacitorjs.community.plugins.bluetoothle.BluetoothLe'}]
            with patch.object(android, 'ROOT', root), patch.object(android.editor, 'check'), patch.object(android, 'inspect_manifest'):
                make(b'editor', plugin)
                self.assertEqual(android.check(root / 'bundle', apk), 'pass')
                make(b'other', plugin)
                with self.assertRaises(ValueError):
                    android.check(root / 'bundle', apk)
                make(b'editor', [])
                with self.assertRaises(ValueError):
                    android.check(root / 'bundle', apk)


if __name__ == '__main__':
    unittest.main()
