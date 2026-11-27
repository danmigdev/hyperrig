"""Build the desktop program of HyperRig for the TANK-MINI, editor and installer, for Windows. No device is opened.

The program is Electron, pinned by the checksum of its official release, with app/desktop and the files of an editor bundle
(tools/build_mini_dev_editor.py). Every file of the bundle is listed by SHA-256 in the program's manifest and checked again
when it starts. The program file gets HyperRig's icon and name; the parts of Electron that run it as Node, read NODE_OPTIONS
or open its inspector are turned off in it. Only the English texts of Chromium are kept. HyperRig's notice and the licences
of everything in the program go into the folder licenses; UltraRig's own notice is kept there unchanged, in a folder of its own.

With --firmware and --loader the installer (app/installer) is in it: the page, the application area of a product build and
HyperRig's loader as the stock firmware is given it. The firmware must be the one the editor is made for.

Usage, from the repository root:
    python -B tools/build_desktop_editor.py --bundle build/hyperrig-mini-product-editor-NN --output build/hyperrig-desktop-NN [--zip]
        [--firmware build/product-NN --loader build/mini-stage-NN] [--patchstorage-platform NUMBER]
    python -B tools/build_desktop_editor.py --check build/hyperrig-desktop-NN
The release of Electron is read from build/electron-cache; its address is in ELECTRON below.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_dev_editor as editor  # noqa: E402

KIND = 'hyperrig-desktop-editor'
APP = ROOT / 'app/desktop'
CACHE = ROOT / 'build/electron-cache'
ELECTRON = {
    'version': '45.4.1',
    'win32-x64': {
        'url': 'https://github.com/electron/electron/releases/download/v45.4.1/electron-v45.4.1-win32-x64.zip',
        'sha256': '2ba6223afa9121f42831fefe92c434334907540165294fc56697449d12e7cfe9'}}
PROGRAM = 'HyperRig'
SOURCES = ['main.js', 'rules.js', 'store.js', 'tone3000.js', 'patchstorage.js']
INSTALLER = ROOT / 'app/installer'
INSTALLER_FILES = {**{n: n for n in ('wire.js', 'flash.js', 'pedal.js', 'views.js', 'flow.js', 'webmidi.js', 'serial.js')},
                   **{n: 'page/' + n for n in ('index.html', 'app.css', 'app.js', 'fonts/big-shoulders-display.woff2', 'fonts/public-sans.woff2', 'fonts/LICENSES.md')}}
TONE_KEY = ROOT / 'build/tone3000-key.txt'
# The folder licenses, by its files in the tree: the notice says what each is for. UltraRig's own come with the editor.
LICENSES = {'NOTICE.md': 'release/NOTICE.md', 'LICENSE.md': 'third_party/ultrarig/LICENSE.md', 'ac79-sdk-LICENSE.txt': 'third_party/ac79-sdk/LICENSE',
            'btstack-LICENSE.txt': 'third_party/btstack/LICENSE', 'm-bootloader.md': 'firmware/mini_stage/THIRD_PARTY.md',
            'fonts.md': 'app/installer/page/fonts/LICENSES.md', 'tone3000.md': 'app/mini/tone3000/README.md',
            'patchstorage.md': 'app/mini/patchstorage/README.md'}
ULTRARIG = ('NOTICE.md', 'THIRD_PARTY_LICENSES.md')
# The fuses of Electron, by their place: run as Node, NODE_OPTIONS, --inspect, and the extra rights of file: pages are off.
FUSE_WIRE, FUSES_OFF = b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX', (0, 2, 3, 7)
RT_ICON, RT_GROUP_ICON, RT_VERSION, LANGUAGE = 3, 14, 16, 0x0409
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

require = editor.require


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def electron(platform):
    """{path: bytes} of the pinned release, without what is not shipped."""
    pin = ELECTRON[platform]
    path = CACHE / pin['url'].rsplit('/', 1)[1]
    require(path.is_file(), f"{path.name} is not in {CACHE.relative_to(ROOT).as_posix()}; download it from {pin['url']}")
    raw = path.read_bytes()
    require(sha(raw) == pin['sha256'], 'the release of Electron is not the pinned one')
    out = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            name = info.filename
            require(not name.startswith('/') and '..' not in name.split('/'), f'a strange path: {name}')
            if info.is_dir() or name == 'resources/default_app.asar' or name.startswith('locales/') and name != 'locales/en-US.pak':
                continue
            out[name] = archive.read(info)
    require('electron.exe' in out and 'LICENSES.chromium.html' in out, 'the release of Electron is not complete')
    return out


def icon_pictures():
    """The editor's own mark, drawn at each size: {size: PNG bytes}."""
    from PIL import Image, ImageDraw
    out = {}
    for size in ICON_SIZES:
        scale = 8
        s = size * scale
        u = s / 64
        picture = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(picture)
        draw.rounded_rectangle((0, 0, s - 1, s - 1), radius=14 * u, fill='#071819')
        for x in (20, 44):
            draw.rectangle(((x - 5) * u, 13 * u, (x + 5) * u, 51 * u), fill='#63e0f5')
        draw.rectangle((20 * u, 27 * u, 44 * u, 37 * u), fill='#63e0f5')
        draw.ellipse((45.5 * u, 46.5 * u, 54.5 * u, 55.5 * u), fill='#ff7a1a')
        buffer = io.BytesIO()
        picture.resize((size, size), Image.LANCZOS).save(buffer, 'PNG', optimize=True)
        out[size] = buffer.getvalue()
    return out


def version_numbers(version):
    digits = [int(''.join(c for c in part if c.isdigit()) or 0) for part in version.replace('-', '.').split('.')]
    return tuple((digits + [0, 0, 0, 0])[:4])


def version_resource(version, revision):
    """VS_VERSIONINFO with HyperRig's names."""
    def block(key, value, text, children=b''):
        name = key.encode('utf-16-le') + b'\0\0'
        head = 6 + len(name)
        pad = -head % 4
        body = value + b'\0' * (-len(value) % 4 if children else 0) + children
        size = head + pad + len(body)
        count = len(value) // 2 if text else len(value)
        return struct.pack('<HHH', size, count, 1 if text else 0) + name + b'\0' * pad + body

    def aligned(blocks):
        out = b''
        for item in blocks:
            out += b'\0' * (-len(out) % 4) + item
        return out
    a, b, c, d = version_numbers(version)
    fixed = struct.pack('<13I', 0xFEEF04BD, 0x10000, a << 16 | b, c << 16 | d, a << 16 | b, c << 16 | d, 0x3F, 0x2 if '-' in version else 0,
                        0x40004, 1, 0, 0, 0)
    texts = {'FileDescription': 'HyperRig for TANK-MINI', 'ProductName': 'HyperRig', 'InternalName': PROGRAM, 'OriginalFilename': PROGRAM + '.exe',
             'FileVersion': version, 'ProductVersion': version, 'Comments': revision,
             'LegalCopyright': 'See the folder licenses. Includes Electron (c) OpenJS Foundation and Electron contributors.'}
    strings = aligned([block(k, v.encode('utf-16-le') + b'\0\0', True) for k, v in texts.items()])
    children = aligned([block('StringFileInfo', b'', True, block('040904b0', b'', True, strings)),
                        block('VarFileInfo', b'', True, block('Translation', struct.pack('<HH', LANGUAGE, 1200), False))])
    return block('VS_VERSION_INFO', fixed, False, children)


def brand(path, pictures, version, revision):
    """HyperRig's icon and names in the program file, with the system's own resource update."""
    import pefile
    pe = pefile.PE(str(path), fast_load=True)
    pe.parse_data_directories([pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
    groups, icons, versions = [], [], []
    for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        for entry in kind.directory.entries:
            name = str(entry.name) if entry.name is not None else entry.struct.Id
            for language in entry.directory.entries:
                {RT_GROUP_ICON: groups, RT_ICON: icons, RT_VERSION: versions}.get(kind.struct.Id, []).append((name, language.struct.Id))
    pe.close()
    require(groups and versions, 'the program has no icon or version to replace')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.BeginUpdateResourceW.restype = wintypes.HANDLE
    kernel.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
    kernel.UpdateResourceW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD, ctypes.c_char_p, wintypes.DWORD]
    kernel.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]

    def identity(name):
        if isinstance(name, int):
            return ctypes.c_void_p(name)
        buffer = ctypes.create_unicode_buffer(name)
        kept.append(buffer)
        return ctypes.cast(buffer, ctypes.c_void_p)
    kept = []
    handle = kernel.BeginUpdateResourceW(str(path), False)
    require(handle, 'the program file cannot be changed')

    def put(kind, name, language, data):
        ok = kernel.UpdateResourceW(handle, ctypes.c_void_p(kind), identity(name), language, data, len(data) if data else 0)
        require(ok, f'a resource was refused: {ctypes.get_last_error()}')
    for name, language in icons:
        put(RT_ICON, name, language, None)
    for name, language in versions:
        put(RT_VERSION, name, language, None)
    directory = struct.pack('<HHH', 0, 1, len(pictures))
    for number, (size, png) in enumerate(sorted(pictures.items()), 1):
        put(RT_ICON, number, LANGUAGE, png)
        directory += struct.pack('<BBBBHHIH', size & 255, size & 255, 0, 0, 1, 32, len(png), number)
    for name, language in groups:
        put(RT_GROUP_ICON, name, language, directory)
    put(RT_VERSION, 1, LANGUAGE, version_resource(version, revision))
    require(kernel.EndUpdateResourceW(handle, False), f'the program file was not written: {ctypes.get_last_error()}')


def fuse(raw):
    """The program with the fuses of FUSES_OFF turned off."""
    at = raw.find(FUSE_WIRE)
    require(at > 0 and raw.find(FUSE_WIRE, at + 1) < 0, 'the fuses of Electron are not where they were')
    start = at + len(FUSE_WIRE) + 2
    require(raw[start - 2] == 1 and raw[start - 1] >= 8, 'the fuses of Electron have another form')
    out = bytearray(raw)
    for index in FUSES_OFF:
        require(chr(out[start + index]) in '01', 'a fuse is not there any more')
        out[start + index] = ord('0')
    return bytes(out)


def tone_key(path):
    """The publishable key of TONE3000, from a file that is not in Git; None when there is none. A secret one is refused."""
    if path is None or not Path(path).is_file():
        return None
    key = Path(path).read_text(encoding='utf-8').strip()
    require(re.fullmatch(r't3k_pub_[A-Za-z0-9_-]{6,200}', key) is not None, 'this is not a publishable TONE3000 key (t3k_pub_...)')
    return key


def installer(firmware, loader, product):
    """{path in the installer's folder: bytes}: the page, its parts, the firmware and the loader."""
    out = {name: (INSTALLER / source).read_bytes() for name, source in INSTALLER_FILES.items()}
    record = json.loads((Path(firmware) / 'build-manifest.json').read_bytes())
    image = (Path(firmware) / 'hyperrig-mini.app-area.bin').read_bytes()
    require(record.get('product') == product, 'the firmware is not the one the editor is made for')
    require(sha(image) == record['area_sha256'] and len(image) == 0x7E000, 'the firmware image differs from its record')
    report = json.loads((Path(loader) / 'report.json').read_bytes())
    package, code, stream = ((Path(loader) / n).read_bytes() for n in ('stage-package.bin', 'stage-code.bin', 'stage-ota.bin'))
    require(sha(package) == report['package_sha256'] and sha(code) == report['padded_sha256'] and sha(stream) == report['stored_sha256'],
            'the loader differs from its report')
    about = {'version': product['version'], 'build': product['build_id'], 'area_sha256': sha(image), 'loader': report['build'], 'stored': len(stream),
             'sha256': {'image.bin': sha(image), 'stage-package.bin': sha(package), 'stage-code.bin': sha(code)}}
    out.update({'firmware/firmware.json': editor.encoded(about), 'firmware/image.bin': image, 'firmware/stage-package.bin': package, 'firmware/stage-code.bin': code})
    return out


def build(bundle, output, platform='win32-x64', make_zip=False, key=None, firmware=None, loader=None, share=None):
    require(os.name == 'nt', 'the program file is finished with Windows')
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    bundle = Path(bundle).resolve()
    meta = editor.check(bundle)
    area = json.loads((bundle / 'bundle.json').read_bytes())['area']
    product = area.get('product')
    require(product, 'the desktop editor is made for a product build')
    release = electron(platform)
    folder = output / PROGRAM
    pictures = icon_pictures()
    files = {name: raw for name, raw in release.items() if name not in ('electron.exe', 'LICENSE', 'LICENSES.chromium.html', 'version')}
    files['licenses/ELECTRON-LICENSE.txt'] = release['LICENSE']
    files['licenses/CHROMIUM-LICENSES.html'] = release['LICENSES.chromium.html']
    inner = {}
    for path in sorted((bundle / 'editor').rglob('*')):
        if path.is_file():
            inner[path.relative_to(bundle / 'editor').as_posix()] = path.read_bytes()
    require(inner['LICENSE.md'].split() == (ROOT / LICENSES['LICENSE.md']).read_bytes().split(), "the editor's licence is not the one of the tree")
    for name, path in LICENSES.items():
        files['licenses/' + name] = (ROOT / path).read_bytes()
    for path in sorted((ROOT / 'app/mini/factory').iterdir()):      # the presets to start with and HyperRig's cab, made by tools/make_factory_presets.py
        files['presets/' + path.name] = path.read_bytes()
    for name in ULTRARIG:
        files['licenses/ultrarig/' + name] = inner[name]
    named = set(re.findall(r'`([\w./-]+\.(?:md|txt|html))`', files['licenses/NOTICE.md'].decode('utf-8')))
    require(named == {n.removeprefix('licenses/') for n in files if n.startswith('licenses/')} - {'NOTICE.md'}, 'the notice does not name the licences that are there')
    manifest = {'schema': 1, 'kind': KIND, 'version': product['version'], 'firmware': f"{product['version']} {product['build_id']}",
                'revision': meta['revision'], 'electron': ELECTRON['version'], 'files': {name: sha(raw) for name, raw in inner.items()}}
    if key:
        manifest['tone3000'] = {'client_id': key}
    if share:
        require(isinstance(share, int) and share > 0, 'the platform of Patchstorage is a number')
        manifest['patchstorage'] = {'platform': share}
    inside = 'resources/app/'
    files.update({inside + 'editor/' + name: raw for name, raw in inner.items()})
    if firmware:
        more = installer(firmware, loader, product)
        manifest['installer'] = {name: sha(raw) for name, raw in more.items()}
        manifest['firmware_carried'] = json.loads(more['firmware/firmware.json'])
        files.update({inside + 'installer/' + name: raw for name, raw in more.items()})
    for name in SOURCES:
        files[inside + name] = (APP / name).read_bytes()
    files[inside + 'icon.png'] = pictures[256]
    files[inside + 'manifest.json'] = editor.encoded(manifest)
    files[inside + 'package.json'] = editor.encoded({'name': 'hyperrig', 'productName': 'HyperRig', 'version': product['version'], 'main': 'main.js', 'private': True,
                                                     'description': 'HyperRig for TANK-MINI'})
    files['README.txt'] = (README_INSTALLER if firmware else README).format(version=product['version']).replace('\n', '\r\n').encode('utf-8')
    for name, raw in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    program = folder / (PROGRAM + '.exe')
    program.write_bytes(fuse(release['electron.exe']))
    brand(program, pictures, product['version'], meta['revision'])
    record = {'schema': 1, 'kind': KIND, 'version': product['version'], 'revision': meta['revision'], 'platform': platform, 'electron': ELECTRON['version'],
              'electron_sha256': ELECTRON[platform]['sha256'], 'bundle': bundle.relative_to(ROOT).as_posix(),
              'sources': {name: sha((APP / name).read_bytes()) for name in SOURCES}, 'device_io': False, 'signed': False, 'tone3000': bool(key), 'patchstorage': bool(share),
              'installer': manifest.get('firmware_carried'),
              'files': {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}}
    if make_zip:
        archive = output / f"HyperRig-{product['version']}-{platform}.zip"
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name in sorted(record['files']):
                z.write(folder / name, f'{PROGRAM}/{name}')
        record['archive'] = {'name': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive.read_bytes())}
    (output / 'desktop.json').write_bytes(editor.encoded(record))
    return check(output)


README = '''HyperRig {version} - editor for the M-VAVE TANK-MINI

Start HyperRig.exe. Connect the pedal with a USB cable: the editor finds it by itself.
The pedal must run HyperRig {version}; with another HyperRig the editor only reads.

It is not signed: Windows may ask before it starts the first time.
It sends nothing over the network, unless you press Browse TONE3000 or Browse
Patchstorage: then it talks to that service and to nobody else. What it writes down about a session stays in
%APPDATA%\\HyperRig\\logs on this computer.

To remove it, delete this folder and %APPDATA%\\HyperRig.

The folder presets has HyperRig's presets to start with, Clean, Crunch and Lead, and its own cab
IR: Try from files... in the editor plays them.

Questions and problems: https://github.com/danmigdev/hyperrig/issues
Not affiliated with M-VAVE. Licences are in the folder licenses.
'''


README_INSTALLER = '''HyperRig {version} for the M-VAVE TANK-MINI

Start HyperRig.exe and connect the pedal with a USB cable, straight to the computer.

 - A pedal with M-VAVE's firmware 011: Pedal > Install, update or restore. The pedal
   is saved on this computer first, whole, and can be put back as it was at any time.
 - A pedal with HyperRig {version}: the editor finds it by itself.

No administrator rights, no download mode, no switch to hold. Leave the cable and the power
alone while the pedal is written: it takes about a minute.

It is not signed: Windows may ask before it starts the first time.
It sends nothing over the network, unless you press Browse TONE3000 or Browse
Patchstorage: then it talks to that service and to nobody else. What it writes down about a session stays in
%APPDATA%\\HyperRig\\logs on this computer, and the copies of your pedal in
%APPDATA%\\HyperRig\\pedals: keep them, they are the way back to the original firmware.

To remove it, delete this folder; delete %APPDATA%\\HyperRig only when you do not need those
copies any more.

The folder presets has HyperRig's presets to start with, Clean, Crunch and Lead, and its own cab
IR: Try from files... in the editor plays them.

Questions and problems: https://github.com/danmigdev/hyperrig/issues
Not affiliated with M-VAVE. Licences are in the folder licenses.
'''


def check(output):
    """The program is as its record says, with the app's and the editor's files of today's sources."""
    output = Path(output).resolve()
    record = json.loads((output / 'desktop.json').read_bytes())
    folder = output / PROGRAM
    require(record.get('kind') == KIND and record['electron_sha256'] == ELECTRON[record['platform']]['sha256'], 'not a desktop editor of this builder')
    here = {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}
    require(here == record['files'], 'a file of the program differs from its record')
    manifest = json.loads((folder / 'resources/app/manifest.json').read_bytes())
    require({n: h for n, h in here.items() if n.startswith('resources/app/editor/')} ==
            {'resources/app/editor/' + n: h for n, h in manifest['files'].items()}, 'the editor differs from the manifest')
    require({n: h for n, h in here.items() if n.startswith('resources/app/installer/')} ==
            {'resources/app/installer/' + n: h for n, h in manifest.get('installer', {}).items()}, 'the installer differs from the manifest')
    raw = (folder / (PROGRAM + '.exe')).read_bytes()
    start = raw.find(FUSE_WIRE) + len(FUSE_WIRE) + 2
    require(all(raw[start + i] == ord('0') for i in FUSES_OFF), 'a fuse is on')
    require(not any('private' in n.lower() or n.endswith(('.pem', '.key', '.pfx', '.jsonl')) for n in here), 'a file that must not be shipped')
    total = sum((folder / n).stat().st_size for n in here)
    return {'result': 'pass', 'directory': str(folder), 'version': record['version'], 'revision': record['revision'], 'files': len(here),
            'megabytes': round(total / 1e6, 1), 'archive': record.get('archive', {}).get('name'), 'signed': False, 'device_io': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--zip', action='store_true')
    parser.add_argument('--tone3000-key', type=Path, default=TONE_KEY, help='file with the publishable key; without it TONE3000 is left out')
    parser.add_argument('--patchstorage-platform', type=int, help="the number of HyperRig's platform on Patchstorage; without it Patchstorage is left out")
    parser.add_argument('--firmware', type=Path, help='output directory of tools/build_hyperrig_mini_image.py --product')
    parser.add_argument('--loader', type=Path, help='output directory of tools/build_mini_stage.py')
    parser.add_argument('--check', type=Path)
    args = parser.parse_args(argv)
    if args.check:
        result = check(args.check)
    else:
        if not (args.bundle and args.output) or bool(args.firmware) != bool(args.loader):
            parser.error('--bundle and --output, with --firmware and --loader together, or --check')
        result = build(args.bundle, args.output, make_zip=args.zip, key=tone_key(args.tone3000_key), firmware=args.firmware, loader=args.loader,
                       share=args.patchstorage_platform)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
