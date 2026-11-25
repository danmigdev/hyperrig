"""The desktop editor's rules, builder and program settings, offline. The program itself: tools/check_desktop_editor.py."""
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from tools import build_desktop_editor as desktop

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'app/desktop/main.js').read_text(encoding='utf-8')


@pytest.mark.skipif(not shutil.which('node'), reason='no node')
def test_rules():
    done = subprocess.run(['node', 'app/desktop/test_rules.js'], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0 and 'all tests passed' in done.stdout, done.stderr


@pytest.mark.skipif(not shutil.which('node'), reason='no node')
def test_tone3000():
    done = subprocess.run(['node', 'app/desktop/test_tone3000.js'], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0 and 'all tests passed' in done.stdout, done.stderr


@pytest.mark.skipif(not shutil.which('node'), reason='no node')
def test_patchstorage():
    done = subprocess.run(['node', 'app/desktop/test_patchstorage.js'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0 and 'all tests passed' in done.stdout, done.stderr


def test_patchstorage_is_only_read():
    """No account, no password, nothing but GET; without a platform of the builder it is not there."""
    source = (ROOT / 'app/desktop/patchstorage.js').read_text(encoding='utf-8')
    code = re.sub(r'/\*.*?\*/|//[^\n]*', ' ', source, flags=re.S)
    assert re.findall(r'method: "(\w+)"', code) == ['GET'] and 'body:' not in code
    for word in ('token', 'authorization', 'bearer', 'cookie', 'require('):
        assert word not in code.lower(), word
    assert 'if (!share.isPlatform(platform)) return;' in MAIN
    page = (ROOT / 'app/mini/product-share.js').read_text(encoding='utf-8')
    assert 'password' not in page.lower() and 'innerHTML' not in page


@pytest.mark.skipif(not shutil.which('node'), reason='no node')
def test_store():
    done = subprocess.run(['node', 'app/desktop/test_store.js'], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0 and 'tests passed' in done.stdout, done.stderr


def test_the_installer_has_all_its_files():
    """Every file of the installer's page is shipped, and nothing of its tests."""
    page = (ROOT / 'app/installer/page/index.html').read_text(encoding='utf-8')
    for name in re.findall(r'(?:src|href)="([^"]+)"', page):
        assert name in desktop.INSTALLER_FILES, name
    for name in re.findall(r'url\(([^)]+)\)', (ROOT / 'app/installer/page/app.css').read_text(encoding='utf-8')):
        assert name in desktop.INSTALLER_FILES, name
    for source in desktop.INSTALLER_FILES.values():
        assert (desktop.INSTALLER / source).is_file() and 'test' not in source and 'simulated' not in source, source
    assert not re.search(r'<script[^>]*>[^<]', page) and 'onclick=' not in page, 'no script in the page itself'
    script = (ROOT / 'app/installer/page/app.js').read_text(encoding='utf-8')
    for name in re.findall(r'\$\("([A-Za-z]+)"\)', script):
        assert f'id="{name}"' in page, name


def test_the_firmware_must_be_the_editors(tmp_path):
    firmware, loader = tmp_path / 'firmware', tmp_path / 'loader'
    firmware.mkdir()
    loader.mkdir()
    image = bytes(0x7E000)
    product = {'version': '1', 'build_id': 'x'}
    record = {'product': product, 'area_sha256': hashlib.sha256(image).hexdigest()}
    (firmware / 'hyperrig-mini.app-area.bin').write_bytes(image)
    (firmware / 'build-manifest.json').write_text(json.dumps(record))
    for name in ('stage-package.bin', 'stage-code.bin', 'stage-ota.bin'):
        (loader / name).write_bytes(name.encode())
    digest = {n: hashlib.sha256(n.encode()).hexdigest() for n in ('stage-package.bin', 'stage-code.bin', 'stage-ota.bin')}
    report = {'build': 'HRS1-x', 'package_sha256': digest['stage-package.bin'], 'padded_sha256': digest['stage-code.bin'], 'stored_sha256': digest['stage-ota.bin']}
    (loader / 'report.json').write_text(json.dumps(report))
    files = desktop.installer(firmware, loader, product)
    about = json.loads(files['firmware/firmware.json'])
    assert about['version'] == '1' and about['stored'] == len('stage-ota.bin') and files['firmware/image.bin'] == image
    with pytest.raises(ValueError, match='not the one'):
        desktop.installer(firmware, loader, {'version': '1', 'build_id': 'y'})
    (loader / 'stage-code.bin').write_bytes(b'other')
    with pytest.raises(ValueError, match='loader differs'):
        desktop.installer(firmware, loader, product)
    (firmware / 'hyperrig-mini.app-area.bin').write_bytes(image[:-1] + b'x')
    with pytest.raises(ValueError, match='image differs'):
        desktop.installer(firmware, loader, product)


def test_the_key_is_the_publishable_one(tmp_path):
    assert desktop.tone_key(None) is None and desktop.tone_key(tmp_path / 'none.txt') is None
    path = tmp_path / 'key.txt'
    path.write_text(' t3k_pub_abcdef123 \n', encoding='utf-8')
    assert desktop.tone_key(path) == 't3k_pub_abcdef123'
    for bad in ('t3k_cs_abcdef123', 'abc', '', 't3k_pub_', 't3k_pub_a b'):
        path.write_text(bad, encoding='utf-8')
        with pytest.raises(ValueError, match='publishable'):
            desktop.tone_key(path)


def test_no_key_is_in_the_sources():
    for name in subprocess.run(['git', 'ls-files', 'app', 'tools', 'tests', 'hyperrig', 'docs'], cwd=ROOT, capture_output=True, text=True).stdout.split():
        path = ROOT / name
        if path.is_file() and path.stat().st_size < 3_000_000:
            for key in re.findall(rb't3k_(?:pub|cs)_[A-Za-z0-9_-]{20,}', path.read_bytes()):
                assert False, f'{name}: a key of TONE3000 ({key[:12]!r}...)'


def test_the_page_is_locked_in():
    for setting in ('sandbox: true', 'contextIsolation: true', 'nodeIntegration: false', 'webviewTag: false', 'spellcheck: false', 'devTools: false'):
        assert setting in MAIN, setting
    assert 'preload' not in MAIN, 'the page gets nothing from the program'
    for word in ('autoUpdater', 'crashReporter', 'ipcMain', 'child_process', 'net.request'):
        assert not re.search(rf'\b{re.escape(word)}\b(?!s://github\.com/danmigdev/hyperrig)', MAIN.replace('https://github.com/danmigdev/hyperrig', '')), word
    assert 'setWindowOpenHandler' in MAIN and 'will-navigate' in MAIN and 'onBeforeRequest' in MAIN
    assert 'requestSingleInstanceLock' in MAIN


def test_only_the_projects_own_pages_open_outside():
    opened = re.findall(r'openExternal\(([^)]*)\)', MAIN)
    assert sorted(opened) == ['"https://github.com/danmigdev/hyperrig"', 'url', 'url', 'url']
    for line in MAIN.splitlines():
        if 'openExternal(url)' in line:
            assert 'rules.mayOpen(url)' in line


def test_the_release_of_electron_is_pinned():
    pin = desktop.ELECTRON['win32-x64']
    assert re.fullmatch(r'[0-9a-f]{64}', pin['sha256']) and desktop.ELECTRON['version'] in pin['url']
    assert pin['url'].startswith('https://github.com/electron/electron/releases/download/v')


def test_another_release_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop, 'CACHE', tmp_path)
    monkeypatch.setattr(desktop, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='download it from'):
        desktop.electron('win32-x64')
    (tmp_path / desktop.ELECTRON['win32-x64']['url'].rsplit('/', 1)[1]).write_bytes(b'something else')
    with pytest.raises(ValueError, match='not the pinned one'):
        desktop.electron('win32-x64')


def test_fuses():
    wire = desktop.FUSE_WIRE + bytes([1, 8]) + b'10110011'
    raw = b'x' * 50 + wire + b'y' * 50
    done = desktop.fuse(raw)
    assert done[:50] == raw[:50] and done[-50:] == raw[-50:] and len(done) == len(raw)
    states = done[50 + len(desktop.FUSE_WIRE) + 2:][:8]
    assert states == b'00000010', states            # run as Node, NODE_OPTIONS, --inspect and file rights off; the others as they were
    for broken in (raw.replace(desktop.FUSE_WIRE, b'z' * 32), raw + raw, b'x' * 9 + desktop.FUSE_WIRE + bytes([2, 8]) + b'10110011',
                   b'x' * 9 + desktop.FUSE_WIRE + bytes([1, 8]) + b'r0110011'):
        with pytest.raises(ValueError):
            desktop.fuse(broken)


def test_versions():
    assert desktop.version_numbers('0.2.0-dev.1') == (0, 2, 0, 0)
    assert desktop.version_numbers('1.4') == (1, 4, 0, 0)
    raw = desktop.version_resource('0.2.0-dev.1', 'mini-product-04')
    size, value, text = struct.unpack_from('<HHH', raw)
    assert (size, value, text) == (len(raw), 52, 0)
    words = raw.decode('utf-16-le', 'replace')
    for word in ('VS_VERSION_INFO', 'HyperRig for TANK-MINI', '0.2.0-dev.1', 'mini-product-04', 'StringFileInfo', 'Translation'):
        assert word in words, word
    assert struct.unpack_from('<I', raw, 40)[0] == 0xFEEF04BD


def test_icons():
    pytest.importorskip('PIL')
    pictures = desktop.icon_pictures()
    assert sorted(pictures) == sorted(desktop.ICON_SIZES)
    for size, png in pictures.items():
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', png[16:24]) == (size, size)
    assert desktop.icon_pictures() == pictures, 'the same every time'


def test_text_for_the_person():
    text = desktop.README.format(version='0.2.0-dev.1')
    assert 'TANK-MINI' in text and 'TANK MINI' not in text and 'nothing over the network' in text and 'not signed' in text
    assert '{' not in text and text.isascii()


def newest():
    found = sorted((ROOT / 'build').glob('hyperrig-desktop-*/desktop.json'), key=lambda p: p.stat().st_mtime)
    return found[-1].parent if found else None


@pytest.mark.skipif(os.name != 'nt' or newest() is None, reason='no built program here')
def test_a_built_program_is_as_its_record_says(tmp_path):
    made = newest()
    result = desktop.check(made)
    assert result['result'] == 'pass' and result['files'] > 20
    folder = made / desktop.PROGRAM
    manifest = json.loads((folder / 'resources/app/manifest.json').read_bytes())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((folder / 'resources/app/editor' / name).read_bytes()).hexdigest() == digest
    assert (folder / 'licenses/LICENSE.md').is_file() and (folder / 'licenses/CHROMIUM-LICENSES.html').is_file()
    assert not (folder / 'resources/default_app.asar').exists()
