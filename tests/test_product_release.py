"""The release of the product: its pins, its archives, and what it refuses. Nothing is built or downloaded here."""
import io
import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_product_release as release  # noqa: E402


class Release(unittest.TestCase):
    def setUp(self):
        (ROOT / 'build').mkdir(exist_ok=True)
        holder = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(holder.cleanup)
        self.out = Path(holder.name)

    def test_the_pins(self):
        lock = json.loads(release.LOCK.read_bytes())
        self.assertRegex(lock['toolchain']['sha256'], '^[0-9a-f]{64}$')
        self.assertTrue(lock['toolchain']['url'].startswith('https://') and lock['toolchain']['directory'].startswith('tools/vendor/'))
        for path, pin in lock['repositories'].items():
            self.assertTrue(path.startswith('upstream/'))
            self.assertRegex(pin['commit'], '^[0-9a-f]{40}$')
        for tool in ('tools/build_hyperrig_mini_image.py', 'tools/build_mini_stage.py'):
            self.assertIn(lock['toolchain']['directory'], (ROOT / tool).read_text(encoding='utf-8'))
        sealed = json.loads((ROOT / lock['editor_base']['lock']).read_bytes())
        from tools import build_mini_dev_editor as editor
        self.assertEqual(editor.BASE, ROOT / lock['editor_base']['directory'])
        for name, wanted in editor.INPUTS.items():
            self.assertEqual(sealed['files'][lock['editor_base']['prefix'] + name]['sha256'], wanted)

    def test_the_versions(self):
        for good in ('0.2.0', '1.10.3', '0.2.0-beta.1', '0.2.0-dev.6'):
            self.assertEqual(release.version_of(good), good)
        for bad in ('', '0.2', 'v0.2.0', '0.2.0 ', '0.2.0-rc1', '0.2.0-beta', '../0.2.0'):
            with self.assertRaises(ValueError):
                release.version_of(bad)

    def test_a_tree_with_changes_or_of_another_version_is_refused(self):
        with mock.patch.object(release, 'git', side_effect=lambda *a, **k: ' M file' if a[0] == 'status' else 'c' * 40):
            with self.assertRaisesRegex(ValueError, 'changes'):
                release.source('0.2.0')
        here = (ROOT / 'firmware/ultrarig/mini/product/VERSION').read_text(encoding='ascii').strip()
        with mock.patch.object(release, 'git', side_effect=lambda *a, **k: '' if a[0] == 'status' else 'c' * 40):
            self.assertEqual(release.source(here), 'c' * 40)
            with self.assertRaisesRegex(ValueError, 'version'):
                release.source('9.9.9')

    def test_a_download_is_what_is_pinned_or_nothing(self):
        with mock.patch.object(release, 'urlopen', return_value=io.BytesIO(b'other')):
            with self.assertRaisesRegex(ValueError, 'not the pinned file'):
                release.download('https://example.invalid/x.zip', release.sha(b'wanted'))
        with mock.patch.object(release, 'urlopen', return_value=io.BytesIO(b'wanted')):
            self.assertEqual(release.download('https://example.invalid/x.zip', release.sha(b'wanted')), b'wanted')

    def test_the_editor_base_is_the_sealed_one(self):
        def packed(files):
            raw = io.BytesIO()
            with zipfile.ZipFile(raw, 'w') as z:
                for name, body in files.items():
                    z.writestr(name, body)
            return raw.getvalue()
        files = {'editor/web/a.js': b'a', 'other/x': b'x'}
        raw = packed(files)
        seal = {'sha256': release.sha(raw), 'files': {n: {'bytes': len(b), 'sha256': release.sha(b)} for n, b in files.items()}}
        self.assertEqual(release.sealed_files(raw, seal, 'editor/'), {'web/a.js': b'a'})
        with self.assertRaisesRegex(ValueError, 'archive is not'):
            release.sealed_files(raw + b' ', seal, 'editor/')
        other = {**seal, 'files': {**seal['files'], 'editor/web/a.js': {'bytes': 1, 'sha256': release.sha(b'b')}}}
        with self.assertRaisesRegex(ValueError, 'not the sealed one'):
            release.sealed_files(raw, other, 'editor/')
        for name in ('editor/../x', 'editor//x', 'editor/a:b'):
            raw = packed({name: b'a'})
            with self.assertRaisesRegex(ValueError, 'strange path'):
                release.sealed_files(raw, {'sha256': release.sha(raw), 'files': {name: {'bytes': 1, 'sha256': release.sha(b'a')}}}, 'editor/')

    def test_an_archive_is_the_same_when_it_is_made_again(self):
        files = {'b/two.txt': b'2' * 4000, 'a.txt': b'1'}
        for name in ('one.zip', 'again.zip'):
            release.archive(self.out / name, files)
        self.assertEqual((self.out / 'one.zip').read_bytes(), (self.out / 'again.zip').read_bytes())
        with zipfile.ZipFile(self.out / 'one.zip') as z:
            self.assertEqual({n: z.read(n) for n in z.namelist()}, files)

    def made(self, extra=None, image=b'image', carried=b'image'):
        out = self.out / 'release'
        out.mkdir()
        inside = 'HyperRig/resources/app/installer/firmware/'
        program = {inside + 'image.bin': carried, inside + 'stage-package.bin': b'loader', 'HyperRig/licenses/NOTICE.md': b'n', **(extra or {})}
        release.archive(out / 'HyperRig-0.2.0-Windows-x64.zip', program)
        release.archive(out / 'HyperRig-0.2.0-firmware.zip', {'firmware/hyperrig-mini.app-area.bin': image, 'loader/stage-package.bin': b'loader', 'licenses/NOTICE.md': b'n'})
        about = {'version': '0.2.0', 'commit': 'c' * 40, 'firmware': {}, 'area_sha256': release.sha(b'image'), 'loader_package_sha256': release.sha(b'loader'),
                 'artifacts': {p.name: {'sha256': release.sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in out.glob('*.zip')}}
        (out / 'provenance.json').write_text(json.dumps(about), encoding='ascii')
        (out / 'SHA256SUMS').write_text(''.join(f'{release.sha(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir())), encoding='ascii')
        return out

    def test_a_release_is_verified(self):
        self.assertEqual(release.verify(self.made())['result'], 'pass')

    def test_the_checksums_name_what_is_attached(self):
        out = self.made()
        (out / 'NOTES.md').write_bytes(b'the text of the page')
        self.assertEqual(release.attached(out), ['HyperRig-0.2.0-Windows-x64.zip', 'HyperRig-0.2.0-firmware.zip', 'provenance.json'])
        self.assertEqual(release.verify(out)['result'], 'pass')
        (out / 'more.txt').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'checksums'):
            release.verify(out)

    def test_a_changed_file_another_firmware_and_a_key_are_refused(self):
        out = self.made()
        (out / 'provenance.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'checksums'):
            release.verify(out)
        for p in out.iterdir():
            p.unlink()
        out.rmdir()
        with self.assertRaisesRegex(ValueError, 'another one'):
            release.verify(self.made(carried=b'another'))
        for p in out.iterdir():
            p.unlink()
        out.rmdir()
        with self.assertRaisesRegex(ValueError, 'must not be shipped'):
            release.verify(self.made({'HyperRig/signing.key': b'x'}))

    def test_the_notice_names_the_licences_of_the_firmware_archive(self):
        notice = (ROOT / 'release/NOTICE.md').read_text(encoding='utf-8')
        named = set(re.findall(r'`([\w./-]+\.(?:md|txt|html))`', notice))
        self.assertTrue(set(release.LICENSES) - {'NOTICE.md'} <= named)
        self.assertIn('Required Notice: Copyright (c) 2026 Manuel Aguirre', notice)
        for path in release.LICENSES.values():
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == '__main__':
    unittest.main()
