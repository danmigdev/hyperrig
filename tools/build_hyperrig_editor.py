"""Build the English HyperRig product UI from the sealed MINI FX editor.

This is an offline presentation derivation. Device command policies, firmware,
and historical hardware evidence are preserved; no hardware test is implied.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import qualify_mini_fx_editor as baseline

CONFIG = ROOT / 'app/project.json'
DERIVER = ROOT / 'tools/editor/derive.cjs'
BASELINE_VERIFIER_SHA = '63744b846ee08a3c928a91ffa96649e8174d8316c771e6ea50b69daf636a4612'
KIND = 'hyperrig-english-editor-bundle'
FAMILIES = ['GAIN', 'PLOAD', 'PSAVE', 'SNAPSAVE', 'FXA', 'FXP', 'FXE', 'FXR']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode('utf-8')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(path, within=ROOT):
    path = Path(path).resolve()
    require(path.is_relative_to(within.resolve()), 'Path leaves its permitted directory')
    return path


def reference(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes())}


def project():
    value = json.loads(CONFIG.read_bytes())
    require(value['name'] == 'HyperRig' and value['language'] == 'en'
            and value['repository'] == 'https://github.com/danmigdev/hyperrig'
            and value['issues'] == value['repository'] + '/issues/new/choose'
            and value['releases'] == value['repository'] + '/releases'
            and value['donations'] is False and value['telemetry'] is False
            and value['automatic_update_checks'] is False, 'Unexpected project configuration')
    return value


def english_board_ui(text):
    translations = {
        'aggiunta effetti seriali': 'add serial effects', 'rimozione effetti': 'remove effects',
        'parametri effetti': 'effect parameters', 'bypass effetti': 'effect bypass',
        'caricamento preset': 'load presets', 'salvataggio preset': 'save presets',
        'eliminazione preset': 'delete presets', 'selezione scene': 'select scenes',
        'salvataggio scene': 'save scenes', 'livelli ingresso e uscita': 'input and output levels',
        'Demo offline: nessun pedale collegato, nessun audio dal pedale.':
            'Offline demo: no pedal connected and no pedal audio.',
        'Profilo ': 'Profile ', 'controlli abilitati per questa build.': 'controls enabled for this build.',
        'via USB, prove limitate a ': 'USB testing limited to ',
        'Sono ammessi solo i preset e i valori gi\u00e0 verificati.': 'Only verified presets and values are allowed.',
        'verifica del port: sole letture, modifiche bloccate.': 'port verification: read only; changes blocked.',
        'Port in sviluppo. Collegamento limitato a PING finch\u00e9 non viene associata una build. Puoi provare l\u2019editor in Demo.':
            'Port in development. Connection limited to PING until a build is assigned. Explore the editor in Demo.',
    }
    for original, translated in translations.items():
        text = text.replace(original, translated)
    return text


def timeout_extension(method):
    anchor = ')), 5000); })]);'
    require(method.count(anchor) == 1, 'Serial timeout boundary changed')
    extended = method.replace(anchor, ')), 30000); })]);')
    info = {'kind': 'hyperrig-english-serial-open-timeout-v1', 'original_timeout_ms': 5000,
            'timeout_ms': 30000, 'original_source_sha256': sha(method.encode()),
            'extended_source_sha256': sha(extended.encode()), 'native_open_unchanged': True,
            'reconnect_added': False, 'runtime_only': True, 'CDP_socket_timeout_seconds': 45}
    source = '''/* Runtime timeout adjustment; no serial I/O occurs during installation. */
function installMiniSerialOpenTimeout(transport) {
  const expected = EXPECTED;
  const extended = EXTENDED;
  if (!transport || transport.port !== null || typeof transport.open !== "function")
    throw Error("Unopened HyperRig SerialTransport required");
  if (Function.prototype.toString.call(transport.open).replace(/\\r\\n/g, "\\n") !== expected)
    throw Error("SerialTransport.open differs from the reviewed English editor");
  const replacement = (0, eval)("({" + extended + "})").open;
  if (Function.prototype.toString.call(replacement) !== extended)
    throw Error("Derived serial timeout differs");
  transport.open = replacement;
  return INFO;
}
'''
    return source.replace('EXPECTED', json.dumps(method)).replace('EXTENDED', json.dumps(extended)).replace('INFO', json.dumps(info)), info


def build(base_directory, output_directory):
    require(sha(Path(baseline.__file__).read_bytes()) == BASELINE_VERIFIER_SHA, 'Historical FX verifier changed')
    base_directory = local(base_directory, ROOT / 'build')
    original = baseline.validate_bundle(base_directory)
    require(original['profile']['family_capabilities'] == {'usb-cdc': FAMILIES}, 'Expected eight qualified USB families')
    config = project()
    output = local(output_directory, ROOT / 'build')
    require(not output.exists(), 'Use a new output directory; previous bundles are preserved')
    output.mkdir(parents=True)
    shutil.copytree(base_directory / 'app', output / 'app')
    web = output / 'app/web'
    transformation = output / 'presentation-changes.json'
    subprocess.run(['node', str(DERIVER), str(base_directory / 'app/web/tankmini.html'),
                    str(web / 'tankmini.html'), str(CONFIG), str(transformation)], cwd=ROOT, check=True)
    changes = json.loads(transformation.read_bytes())
    for filename in ['mini-ui.js']:
        target = web / filename
        target.write_text(english_board_ui(target.read_text('utf-8')), encoding='utf-8', newline='\n')
    extension, info = timeout_extension(changes.pop('serialMethod'))
    (web / 'serial-open-timeout.js').write_text(extension, encoding='utf-8', newline='\n')
    changes['serial_timeout'] = info
    transformation.write_bytes(encoded(changes))
    # No protocol field, command family, converter, or physical control is added.
    for name in ['mini-profile.js', 'mini-fx-ui.js', 'nam2chip.js']:
        require((web / name).read_bytes() == (base_directory / 'app/web' / name).read_bytes(), 'Protected runtime changed: ' + name)
    (output / 'app/DERIVATION.txt').write_text(
        'HyperRig English editor for TANK MINI.\n'
        'Derived from the sealed, physically exercised UltraRig-based MINI FX editor.\n'
        'English UI, HyperRig GitHub links, no donations, and no automatic telemetry or update checks.\n'
        'GitHub reporting opens a page for the user to review and submit; nothing is posted automatically.\n'
        'Firmware, command policy and converter are unchanged. This UI derivation is checked offline.\n'
        'Original license notices and immutable source evidence are preserved verbatim.\n', encoding='utf-8')
    proof = copy.deepcopy(original)
    proof['app_directory'] = web.relative_to(ROOT).as_posix()
    metadata = {'schema': 1, 'kind': KIND, 'project': config, 'baseline': reference(base_directory / 'bundle.json'),
                'baseline_directory': base_directory.relative_to(ROOT).as_posix(), 'proof': proof,
                'serial_open_extension': (web / 'serial-open-timeout.js').relative_to(ROOT).as_posix(),
                'hardware_io': False, 'physical_UI_retest': False,
                'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
                                  [Path(__file__), DERIVER, CONFIG, ROOT / 'tools/editor/package-lock.json']},
                'files': {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()}}
    raw = encoded(metadata)
    (output / 'bundle.json').write_bytes(raw)
    (output / 'bundle.sha256').write_text(sha(raw) + '\n', encoding='ascii')
    return validate_bundle(output)


def validate_bundle(output_directory):
    output = local(output_directory, ROOT / 'build')
    raw = (output / 'bundle.json').read_bytes()
    require((output / 'bundle.sha256').read_text('ascii') == sha(raw) + '\n', 'Product bundle seal differs')
    meta = json.loads(raw)
    require(meta['schema'] == 1 and meta['kind'] == KIND and meta['project'] == project(), 'Product identity differs')
    for name, digest in meta['source_sha256'].items():
        require(sha(local(ROOT / name).read_bytes()) == digest, 'Product source differs: ' + name)
    require(set(meta['source_sha256']) == {p.relative_to(ROOT).as_posix() for p in
            [Path(__file__), DERIVER, CONFIG, ROOT / 'tools/editor/package-lock.json']}, 'Unexpected product source inventory')
    actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    require(actual == set(meta['files']) | {'bundle.json', 'bundle.sha256'}, 'Product file inventory differs')
    for name, digest in meta['files'].items():
        require(sha(local(output / name, output).read_bytes()) == digest, 'Product file differs: ' + name)
    require(sha(Path(baseline.__file__).read_bytes()) == BASELINE_VERIFIER_SHA, 'Historical FX verifier changed')
    base_directory = local(ROOT / meta['baseline_directory'], ROOT / 'build')
    require(reference(base_directory / 'bundle.json') == meta['baseline'], 'Historical bundle differs')
    original = baseline.validate_bundle(base_directory)
    expected = copy.deepcopy(original)
    expected['app_directory'] = (output / 'app/web').relative_to(ROOT).as_posix()
    require(meta['proof'] == expected, 'Product derivation changed the qualified capabilities or evidence')
    for name in ['mini-profile.js', 'mini-fx-ui.js', 'nam2chip.js']:
        require((output / 'app/web' / name).read_bytes() == (base_directory / 'app/web' / name).read_bytes(), 'Protected runtime differs')
    extension = output / 'app/web/serial-open-timeout.js'
    require(meta['serial_open_extension'] == extension.relative_to(ROOT).as_posix(), 'Unexpected serial extension path')
    proof = copy.deepcopy(expected)
    proof['product'] = meta['project']
    proof['serial_open_extension'] = meta['serial_open_extension']
    proof['product_bundle'] = reference(output / 'bundle.json')
    return proof


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'build/hyperrig-mini-fx-editor')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--build', type=Path)
    action.add_argument('--check-bundle', type=Path)
    args = parser.parse_args(argv)
    proof = build(args.baseline, args.build) if args.build else validate_bundle(args.check_bundle)
    print(json.dumps({'result': 'pass', 'app_directory': proof['app_directory'],
                      'project': proof['product'], 'device_io': False}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
