"""Build a release of HyperRig for the TANK-MINI from the source of a commit. No device is opened and nothing is published.

Everything that is not in the repository is pinned in release/product.lock.json: JieLi's compiler, the instruction tables and the
assembler of pi32v2-isa, the tools of m-bootloader, the editor's base (sealed, release/mini-v4-inputs.lock.json), and Electron in
tools/build_desktop_editor.py. The firmware is built twice and must be the same; with the product option off it must be the MINI v4
area, byte for byte. The tree must be clean and firmware/ultrarig/mini/product/VERSION must be the version that is asked for.

Usage, from the repository root:
    python -B tools/build_product_release.py fetch [--editor-base HyperRig-MINI-v4-inputs-02.zip]
    python -B tools/build_product_release.py parts --version X.Y.Z --output build/release-parts      (Linux, or Windows with WSL)
    python -B tools/build_product_release.py finish --version X.Y.Z --parts build/release-parts --output build/release-X.Y.Z
        [--tone3000-key FILE]                                                                         (Windows: the program's file)
    python -B tools/build_product_release.py verify --output build/release-X.Y.Z
    python -B tools/build_product_release.py draft --output build/release-X.Y.Z                      (the workflow only: GitHub)
fetch downloads what is missing and checks it; a part that is there is checked too. The editor's base comes from --editor-base, or with
GitHub's gh from the draft release that keeps it. finish makes
    HyperRig-X.Y.Z-Windows-x64.zip   the program: editor, installer, firmware and loader in it
    HyperRig-X.Y.Z-firmware.zip      the firmware and the loader by themselves, with their records and licences
    provenance.json, SHA256SUMS, NOTES.md
draft puts them into a draft release of GitHub, which nobody sees until a person publishes it, and runs only in the workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LOCK = ROOT / 'release/product.lock.json'
V4_AREA = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
LICENSES = {'NOTICE.md': 'release/NOTICE.md', 'LICENSE.md': 'third_party/ultrarig/LICENSE.md', 'ac79-sdk-LICENSE.txt': 'third_party/ac79-sdk/LICENSE',
            'btstack-LICENSE.txt': 'third_party/btstack/LICENSE', 'm-bootloader.md': 'firmware/mini_stage/THIRD_PARTY.md'}
STAMP = (2026, 1, 1, 0, 0, 0)                # one time for every file of an archive, so that it is the same when it is made again


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def version_of(text):
    require(re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:dev|beta)\.\d+)?', text), 'a version is X.Y.Z, X.Y.Z-beta.N or X.Y.Z-dev.N')
    return text


def run(*argv, cwd=ROOT):
    done = subprocess.run([str(a) for a in argv], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if done.returncode:
        raise SystemExit(f'{" ".join(str(a) for a in argv)}\n{(done.stdout + done.stderr)[-3000:]}')
    return done.stdout.strip()


def git(*argv, cwd=ROOT):
    return run('git', *argv, cwd=cwd)


# ---- what is not in the repository

def download(url, wanted, limit=400_000_000):
    with urlopen(url, timeout=300) as response:
        raw = response.read(limit + 1)
    require(len(raw) <= limit and sha(raw) == wanted, f'{url.rsplit("/", 1)[1]} is not the pinned file')
    return raw


def fetch_toolchain(lock):
    pin, target = lock['toolchain'], ROOT / lock['toolchain']['directory']
    if target.is_dir():
        return 'there'
    archive = target.parent / pin['url'].rsplit('/', 1)[1]
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = archive.read_bytes() if archive.is_file() and sha(archive.read_bytes()) == pin['sha256'] else download(pin['url'], pin['sha256'])
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:xz') as tar:
        tar.extractall(target.parent, filter='data')
    require(target.is_dir(), 'the toolchain archive has another folder')
    return 'fetched'


def fetch_repository(path, pin):
    target = ROOT / path
    if not target.is_dir():
        target.parent.mkdir(parents=True, exist_ok=True)
        git('clone', '--quiet', '--no-checkout', pin['url'], target)
        git('checkout', '--quiet', '--detach', pin['commit'], cwd=target)
    require(git('rev-parse', 'HEAD', cwd=target) == pin['commit'], f'{path} is not at its pinned commit')
    require(not git('status', '--porcelain', '--untracked-files=no', cwd=target), f'{path} was changed')
    return 'at ' + pin['commit'][:7]


def sealed_files(raw, seal, prefix):
    """{name: bytes} of the archive's files under a prefix: the archive and each file as the seal has them, no path out of the folder."""
    require(sha(raw) == seal['sha256'], 'the archive is not the sealed one')
    out = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for info in z.infolist():
            name = info.filename
            if not name.startswith(prefix):
                continue
            parts_of = name.split('/')
            require(not info.is_dir() and '\\' not in name and ':' not in name and not any(p in ('', '.', '..') for p in parts_of), f'a strange path: {name}')
            body, pin = z.read(info), seal['files'][name]
            require(len(body) == pin['bytes'] and sha(body) == pin['sha256'], f'{name} is not the sealed one')
            out[name[len(prefix):]] = body
    require(out, 'the archive has none of it')
    return out


def fetch_editor_base(lock, archive):
    pin, target = lock['editor_base'], ROOT / lock['editor_base']['directory']
    seal = json.loads((ROOT / pin['lock']).read_bytes())
    from tools import build_mini_dev_editor as editor
    if not target.is_dir():
        if not archive:                                   # an asset of a draft release: only those who may write to the repository have it
            holder = ROOT / 'build/release-inputs'
            if not (holder / seal['asset']).is_file():
                holder.mkdir(parents=True, exist_ok=True)
                run('gh', 'release', 'download', seal['tag'], '--repo', seal['repository'], '--pattern', seal['asset'], '--dir', holder)
            archive = holder / seal['asset']
        for name, raw in sealed_files(Path(archive).read_bytes(), seal, pin['prefix']).items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    for name, wanted in editor.INPUTS.items():
        require(sha((target / name).read_bytes()) == wanted, f'{name} of the editor base differs')
    return 'as sealed'


def fetch_electron():
    from tools import build_desktop_editor as desktop
    pin = desktop.ELECTRON['win32-x64']
    path = desktop.CACHE / pin['url'].rsplit('/', 1)[1]
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(download(pin['url'], pin['sha256']))
    require(sha(path.read_bytes()) == pin['sha256'], 'the release of Electron is not the pinned one')
    return desktop.ELECTRON['version']


def fetch(editor_base=None, electron=True):
    lock = json.loads(LOCK.read_bytes())
    out = {'toolchain': fetch_toolchain(lock)}
    out.update({path: fetch_repository(path, pin) for path, pin in lock['repositories'].items()})
    out['editor_base'] = fetch_editor_base(lock, editor_base)
    if electron:
        out['electron'] = fetch_electron()
    return out


# ---- the build

def source(version):
    """The commit of a clean tree that is the version's."""
    require(not git('status', '--porcelain', '--untracked-files=no'), 'the tree has changes: a release is of a commit')
    here = (ROOT / 'firmware/ultrarig/mini/product/VERSION').read_text(encoding='ascii').strip()
    require(here == version, f'the tree is version {here}')
    return git('rev-parse', 'HEAD')


def fresh(path):
    out = (ROOT / path).resolve()
    require(out.is_relative_to(ROOT / 'build') and not out.exists(), 'use a fresh directory under build/')
    out.mkdir(parents=True)
    return out


def tool(name, *argv):
    return run(sys.executable, '-B', f'tools/{name}.py', *argv)


def area_of(directory):
    image = (directory / 'hyperrig-mini.app-area.bin').read_bytes()
    record = json.loads((directory / 'build-manifest.json').read_bytes())
    require(sha(image) == record['area_sha256'], 'a firmware differs from its record')
    return image, record


def parts(version, output):
    commit, out = source(version), fresh(output)
    rel = out.relative_to(ROOT).as_posix()
    for name, option in (('firmware', ['--product']), ('firmware-again', ['--product']), ('v4', ['--expect', V4_AREA])):
        tool('build_hyperrig_mini_image', '--output', f'{rel}/{name}', *option)
    (image, record), (again, _) = area_of(out / 'firmware'), area_of(out / 'firmware-again')
    require(image == again, 'the firmware is not the same when it is built again')
    require(record['product']['version'] == version, 'the firmware is another version')
    tool('build_mini_stage', '--output', f'{rel}/loader')
    tool('build_mini_stage', '--output', f'{rel}/loader-again')
    loader = json.loads((out / 'loader/report.json').read_bytes())
    require(loader['package_sha256'] == json.loads((out / 'loader-again/report.json').read_bytes())['package_sha256'], 'the loader is not the same when it is built again')
    tool('build_mini_dev_editor', '--output', f'{rel}/editor', '--area', f'{rel}/firmware')
    for name in ('firmware-again', 'loader-again', 'v4'):
        shutil.rmtree(out / name)
    about = {'schema': 1, 'kind': 'hyperrig-release-parts', 'version': version, 'commit': commit, 'firmware': record['product'], 'area_sha256': record['area_sha256'],
             'loader': loader['build'], 'loader_package_sha256': loader['package_sha256'], 'built_twice': ['firmware', 'loader'], 'v4_area_without_the_option': V4_AREA,
             'inputs': json.loads(LOCK.read_bytes()), 'device_io': False}
    (out / 'parts.json').write_bytes(json.dumps(about, indent=1, sort_keys=True).encode() + b'\n')
    return about


def archive(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(info, files[name])


FIRMWARE_README = '''HyperRig {version}: the firmware and the loader of the M-VAVE TANK-MINI, by themselves.

Most people want the program instead, HyperRig-{version}-Windows-x64.zip: it puts this firmware on the
pedal, saves what is on it first, and brings the original back.

firmware/hyperrig-mini.app-area.bin   the application area, 0x4000 to 0x82000 of the flash
firmware/build-manifest.json          how it was built: sources, tools, addresses
loader/stage-package.bin              the loader as the original firmware takes it
loader/report.json                    how it was built
licenses/                             the notices and licences; noncommercial use only

Build {build}, commit {commit}.
'''


def notes(about):
    version, docs = about['version'], f"https://github.com/danmigdev/hyperrig/blob/v{about['version']}"
    return ('Firmware, editor and installer for the **M-VAVE TANK-MINI**.\n\n'
            f'**To install it** you need a TANK-MINI with the original firmware **011** and a Windows PC. Download `HyperRig-{version}-Windows-x64.zip`, extract the whole of it, '
            f'start `HyperRig.exe` and follow the [installation guide]({docs}/INSTALLATION.md). Then the [manual]({docs}/docs/MANUAL.md); what is not there and what was not tried is in '
            f'its [limits]({docs}/docs/MANUAL.md#limits).\n\n'
            'Installing it replaces the firmware of the pedal, at your own risk and without any warranty. The whole pedal is saved on your computer first, and the original comes back from that '
            'copy. It was tried on one TANK-MINI. The program is not signed: Windows may ask before it starts.\n\n'
            f'- `HyperRig-{version}-Windows-x64.zip`: the program: editor, installer, firmware.\n'
            f'- `HyperRig-{version}-firmware.zip`: the firmware and the loader by themselves; most people do not need it.\n'
            '- `SHA256SUMS`, `provenance.json`: checksums, and where everything comes from.\n\n'
            f"Noncommercial use only: [licence]({docs}/LICENSE.md), [notice]({docs}/release/NOTICE.md). Firmware build `{about['firmware']['build_id']}`, commit `{about['commit']}`.\n")


def finish(version, parts_dir, output, key=None):
    commit = source(version)
    made = (ROOT / parts_dir).resolve()
    about = json.loads((made / 'parts.json').read_bytes())
    require(about['version'] == version and about['commit'] == commit, 'the parts are of another commit')
    image, record = area_of(made / 'firmware')
    require(record['area_sha256'] == about['area_sha256'], 'the firmware is not the one of the parts')
    out = fresh(output)
    rel, parts_rel = out.relative_to(ROOT).as_posix(), made.relative_to(ROOT).as_posix()
    tool('build_desktop_editor', '--bundle', f'{parts_rel}/editor', '--output', f'{rel}/program', '--firmware', f'{parts_rel}/firmware', '--loader', f'{parts_rel}/loader',
         *(['--tone3000-key', Path(key).resolve()] if key else []))
    folder = out / 'program/HyperRig'
    program = {f'HyperRig/{p.relative_to(folder).as_posix()}': p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    archive(out / f'HyperRig-{version}-Windows-x64.zip', program)
    inner = made / 'editor/editor'
    files = {'README.txt': FIRMWARE_README.format(version=version, build=record['product']['build_id'], commit=commit).replace('\n', '\r\n').encode(),
             'firmware/hyperrig-mini.app-area.bin': image, 'firmware/build-manifest.json': (made / 'firmware/build-manifest.json').read_bytes(),
             **{f'loader/{n}': (made / 'loader' / n).read_bytes() for n in ('stage-package.bin', 'report.json')},
             **{f'licenses/{n}': (ROOT / p).read_bytes() for n, p in LICENSES.items()},
             **{f'licenses/ultrarig/{n}': (inner / n).read_bytes() for n in ('NOTICE.md', 'THIRD_PARTY_LICENSES.md')}}
    archive(out / f'HyperRig-{version}-firmware.zip', files)
    shutil.rmtree(out / 'program')
    (out / 'NOTES.md').write_bytes(notes(about).encode())
    about = {**about, 'kind': 'hyperrig-release', 'tone3000': bool(key), 'signed': False,
             'artifacts': {p.name: {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(out.glob('*.zip'))}}
    (out / 'provenance.json').write_bytes(json.dumps(about, indent=1, sort_keys=True).encode() + b'\n')
    names = sorted(p.name for p in out.iterdir() if p.is_file())
    (out / 'SHA256SUMS').write_bytes(''.join(f'{sha((out / n).read_bytes())}  {n}\n' for n in names).encode())
    return verify(output)


def verify(output):
    out = (ROOT / output).resolve()
    sums = dict(reversed(line.split('  ', 1)) for line in (out / 'SHA256SUMS').read_text(encoding='ascii').splitlines())
    here = {p.name for p in out.iterdir() if p.is_file()} - {'SHA256SUMS'}
    require(here == set(sums) and all(sha((out / n).read_bytes()) == v for n, v in sums.items()), 'a file differs from the checksums')
    about = json.loads((out / 'provenance.json').read_bytes())
    for name, pin in about['artifacts'].items():
        require(sums[name] == pin['sha256'], 'the record and the checksums differ')
    with zipfile.ZipFile(out / f"HyperRig-{about['version']}-Windows-x64.zip") as z, zipfile.ZipFile(out / f"HyperRig-{about['version']}-firmware.zip") as f:
        names = z.namelist()
        inside = 'HyperRig/resources/app/installer/firmware/'
        require(sha(z.read(inside + 'image.bin')) == about['area_sha256'] == sha(f.read('firmware/hyperrig-mini.app-area.bin')), 'the firmware in the archives is another one')
        require(sha(z.read(inside + 'stage-package.bin')) == about['loader_package_sha256'] == sha(f.read('loader/stage-package.bin')), 'the loader in the archives is another one')
        for archive_names in (names, f.namelist()):
            require(not any(n.lower().endswith(('.pem', '.key', '.pfx', '.jsonl', '.log')) or 'backup' in n.lower() or '..' in n for n in archive_names), 'a file that must not be shipped')
        require('HyperRig/licenses/NOTICE.md' in names and 'licenses/NOTICE.md' in f.namelist(), 'the notice is missing')
    return {'result': 'pass', 'version': about['version'], 'commit': about['commit'], 'firmware': about['firmware'], 'artifacts': about['artifacts'], 'device_io': False}


def draft(output):
    """A draft release of these files on GitHub. A release that was published is never touched."""
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'the draft is made by the workflow')
    about = verify(output)
    out, tag = (ROOT / output).resolve(), 'v' + about['version']
    require(git('rev-parse', 'HEAD') == about['commit'], 'the files are of another commit')
    found = subprocess.run(['gh', 'release', 'view', tag, '--json', 'isDraft'], cwd=ROOT, capture_output=True, text=True)
    require(found.returncode != 0, f'{tag} is there already: a release is not changed, and a draft is deleted by a person first')
    files = sorted(str(p) for p in out.iterdir() if p.is_file() and p.name != 'NOTES.md')
    run('gh', 'release', 'create', tag, '--draft', *(['--prerelease'] if '-' in about['version'] else []), '--target', about['commit'], '--title', f"HyperRig {about['version']}",
        '--notes-file', out / 'NOTES.md', *files)
    return {'draft': tag, 'files': len(files)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    one = commands.add_parser('fetch')
    one.add_argument('--editor-base', type=Path)
    one.add_argument('--no-electron', action='store_true')
    for name in ('parts', 'finish', 'verify', 'draft'):
        one = commands.add_parser(name)
        one.add_argument('--output', type=Path, required=True)
        if name in ('parts', 'finish'):
            one.add_argument('--version', type=version_of, required=True)
        if name == 'finish':
            one.add_argument('--parts', type=Path, required=True)
            one.add_argument('--tone3000-key', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'fetch':
            result = fetch(args.editor_base, not args.no_electron)
        elif args.command == 'parts':
            result = parts(args.version, args.output)
        elif args.command == 'finish':
            require(os.name == 'nt', 'the program is finished on Windows')
            result = finish(args.version, args.parts, args.output, args.tone3000_key)
        elif args.command == 'verify':
            result = verify(args.output)
        else:
            result = draft(args.output)
    except ValueError as e:
        raise SystemExit(str(e))
    print(json.dumps(result, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
