"""Build a separate usable FX editor from retained real protocol evidence.

Default/import are offline. The baseline four-family bundle is never modified.
FX protocol roundtrips are not represented as physical UI or acoustic tests.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import qualify_mini_browser_preset as baseline

require, local, reference, read_ref = baseline.require, baseline.local, baseline.reference, baseline.read_ref
sha, encoded = baseline.sha, baseline.encoded
BASELINE_SHA = '744015157f7061f518c31e975e7bff7d23e547f7b803d2452ac16d51ef29f636'
MODEL = 'mini-representative-FX-protocol-v1'
IMAGE = baseline.IMAGE
VERSION = baseline.VERSION
CORE_FAMILIES = ['GAIN', 'PLOAD', 'PSAVE', 'SNAPSAVE']
FX_FAMILIES = ['FXA', 'FXP', 'FXE']
POLICY = ROOT/'app/mini/mini-profile-fx.js'
UI = ROOT/'app/mini/mini-fx-ui.js'
BENCHMARK = {'path': 'build/mini-fx-latency-02/report.json',
             'sha256': '9e3278a5cd5bfae31fc1cf4e60729511008c1a8f18a62c30f0f9206f0b6beb08'}
ARCHIVE = ROOT/'analysis/hardware/source-snapshots/latency-02'
BENCHMARK_PINS = {
    'tools/probe_mini_browser_latency.py': '108cd5308e5e29518ce719b1f9cd6162f04c1d5d092d708a87001eb09efd0f9a',
    'tools/mini_browser_latency_guard.js': 'f1a0299ffad740c5d0bc8fd581c4cacd17c2bb18e18738ef69a20f1d08603cae',
    'tools/mini_latency_observation.py': '46794440387f472cd3e08fb1c430e9b8bd39bdc839ec636ebc50d8db8c168b7a',
    'tools/probe_mini_browser_first_preset.py': '87b4063f8e50cabb2d0cd230b1db279770211636842698d7048f748080831c3b',
    'tools/run_mini_v3_first_preset_a2.py': 'c234aa9d36f9b0c95e71a692881f81342773d6e237766f1a2d1ed49df65ac2ab',
}
# The reviewed exact-removal runner is ready. A completed real report remains
# mandatory; having its implementation alone grants no FXR.
REMOVAL_PINS = {
    'tools/probe_mini_browser_fx_remove.py': '6b2e856b7ab939cfbb7a67da27cc5efd4894d5962fdb0eecd3dc74ecb8f1d237',
    'tools/mini_browser_fx_remove_guard.js': '9c4c5a827eed94137285e5abac3b23b2f22f1e7b504b1232def0905f9e421e27',
    'tools/probe_mini_browser_latency.py': 'a80460f4dacdc2ca4c496b79ed58699e0074cbd7ddc50b1cf639a4cd57b43a37',
    'tools/probe_mini_browser_first_preset.py': '87b4063f8e50cabb2d0cd230b1db279770211636842698d7048f748080831c3b',
    'tools/mini_latency_observation.py': '46794440387f472cd3e08fb1c430e9b8bd39bdc839ec636ebc50d8db8c168b7a',
}


def check_baseline():
    require(sha(Path(baseline.__file__).read_bytes()) == BASELINE_SHA, 'frozen baseline qualifier changed')


def frozen_benchmark():
    """Load the reviewed archived parser, never the subsequently edited runner."""
    modules = {}
    for name, digest in BENCHMARK_PINS.items():
        path = ARCHIVE/name
        require(sha(path.read_bytes()) == digest, 'archived benchmark source differs: '+name)
        if path.suffix == '.py':
            spec = importlib.util.spec_from_file_location('_mini_fx_archive_'+path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.ROOT = ROOT
            modules[path.stem] = module
    runner = modules['probe_mini_browser_latency']
    timing = modules['mini_latency_observation']
    timing.a2 = modules['run_mini_v3_first_preset_a2']
    timing.verify_sources()
    runner.timing = timing
    runner.original = modules['probe_mini_browser_first_preset']
    runner.a2 = timing.a2
    return runner


def inspect_benchmark(report, bundle):
    """Pure replay; callers cannot promote a synthetic report to a grant here."""
    runner = frozen_benchmark()
    require(report.get('kind') == 'mini-exact-browser-FX-timing-trial-v1'
            and report.get('result') == 'pass' and report.get('phase') == 'complete'
            and report.get('hardware_executed') is True
            and report.get('baseline_restoration_verified') is True
            and report.get('temporary_wrapper_removed') is True
            and not any(report.get(k) for k in ('error', 'cleanup_error', 'restoration_error')),
            'completed real FX trial and restoration required')
    require(report.get('source_sha256') == BENCHMARK_PINS, 'benchmark source provenance differs')
    prepared = report['prepared']
    require(prepared['bundle'] == bundle and prepared['image_sha256'] == IMAGE
            and prepared['pong'] == bundle['pong'] and prepared['profile'] == bundle['profile']
            and not prepared['families_granted_by_this_experiment']
            and report['mutation_families_granted'] == []
            and report['automatic_retry'] is False
            and report['preset_save_or_delete_performed'] is False,
            'benchmark build/profile/scope differs')
    trace = runner.verify_trace(report['guard'], prepared['restore_ack_prefix'], prepared['pong'])
    observations = runner.verify_observations(report, report['guard'])
    require(trace == report['raw_trace_verification'] and observations == report['observation_verification'],
            'recorded verification differs from independent replay')
    commands = report['guard']['commands']
    catalog = runner.timing.protocol.parse_fxt(report['plan']['actual_catalog'])
    succeeded = {family: [] for family in FX_FAMILIES}
    rejected = []
    for command in commands:
        family = command['line'].split(' ')[0]
        if family not in succeeded:
            continue
        if any(line.startswith('ERR ') for line in command['lines']):
            rejected.append({'request': command['line'], 'response': command['lines']})
        else:
            succeeded[family].append(command['line'])
    require(all(succeeded.values()), 'each new FX family requires a successful actual exchange')
    require(any(line.endswith(' 0') for line in succeeded['FXE'])
            and any(line.endswith(' 1') for line in succeeded['FXE']), 'both bypass values need actual ACKs')
    admitted = report['last_admitted_state']
    matches = [c for c in commands if c['line'] == 'FXS' and c['lines'] == admitted['FXS']
               and c.get('completed') and c.get('native_RX_verified')]
    require(matches, 'admitted FXS is absent from native trace')
    state = runner.verify_added_state(admitted['FXS'], report['plan'], admitted['created'], catalog)
    require(state['blocks'], 'at least one admitted effect must be read back')
    return {'replay_verified': True, 'hardware_execution_attested_by_this_pure_function': False,
            'physically_exercised_successful_requests': succeeded,
            'rejected_requests_not_claimed_as_success': rejected,
            'actual_readback_instances': copy.deepcopy(state['blocks']),
            'catalog_types': sorted(catalog), 'trace': trace, 'observations': observations,
            'baseline_restoration_verified': True, 'UI_FX_interactions_physically_tested': False,
            'every_type_or_parameter_value_tested': False, 'effect_chain_persistence_tested': False,
            'analog_latency_measured': False, 'maximum_chain_proven': False,
            'measurement_instance_counts': [m['instances'] for m in report['measurements']]}


def inspect_removal(report, bundle):
    require(REMOVAL_PINS, 'the exact FXR proof source is not reviewed yet')
    for name, digest in REMOVAL_PINS.items():
        require(sha(local(name).read_bytes()) == digest, 'reviewed FXR verifier changed')
    from tools import probe_mini_browser_fx_remove as removal
    require(report.get('source_sha256') == REMOVAL_PINS, 'FXR proof sources differ')
    require(report.get('kind') == 'mini-exact-FXR-removal-trial-v1'
            and report.get('result') == 'pass' and report.get('phase') == 'complete'
            and all(report.get(k) is True for k in ('hardware_executed', 'temporary_effect_removal_verified',
                    'baseline_restoration_verified', 'temporary_wrapper_removed'))
            and all(report.get(k) is False for k in ('automatic_retry', 'preset_save_or_delete_performed',
                    'serial_open_performed', 'serial_close_performed', 'effect_removal_UI_physically_exercised'))
            and not report.get('general_family_grants')
            and not any(report.get(k) for k in ('error', 'cleanup_error', 'restoration_error')),
            'completed narrow actual FXR trial required')
    require(report['prepared']['bundle'] == bundle and report['prepared']['image_sha256'] == IMAGE
            and report['prepared']['pong'] == bundle['pong'],
            'FXR proof baseline/build differs')
    replay = removal.verify_report(report)
    require(replay == report.get('verification'), 'FXR independent replay differs from retained verification')
    return replay


def qualify(base_directory, *, removal_ref=None):
    check_baseline()
    bundle = baseline.validate_bundle(base_directory)
    report = json.loads(read_ref(BENCHMARK))
    summary = inspect_benchmark(report, bundle)
    removal = None
    if removal_ref:
        removal_report = json.loads(read_ref(removal_ref))
        require(not any(removal_report.get(k) for k in ('fixture', 'synthetic', 'offline_fixture')),
                'an offline fixture cannot qualify or build an editor')
        removal = inspect_removal(removal_report, bundle)
    families = CORE_FAMILIES+FX_FAMILIES+(['FXR'] if removal is not None else [])
    return {'kind': 'mini-FX-editor-qualification', 'schema': 1, 'evidence_model': MODEL,
            'image_sha256': IMAGE, 'firmware_version': VERSION, 'transport': 'usb-cdc',
            'com': bundle['com'], 'pong': bundle['pong'], 'enabled_families': families,
            'hardware_protocol_exercised': True, 'UI_FX_interactions_physically_tested': False,
            'whole_editor_qualified': False, 'blanket_write': False,
            'baseline_qualification': bundle['qualification'], 'baseline_bundle': bundle['refs']['bundle'],
            'benchmark': BENCHMARK, 'benchmark_replay': summary,
            'removal_evidence': removal_ref, 'removal_replay': removal,
            'removal_source_sha256': copy.deepcopy(REMOVAL_PINS) if removal is not None else {},
            'source_sha256': {str(ARCHIVE.relative_to(ROOT)/k).replace('\\', '/'): v for k, v in BENCHMARK_PINS.items()},
            'runtime_scope': 'current FXT types/ranges and FXS IDs; serial append and optional single-instance remove; no routing',
            'all_values_physically_tested': False, 'FX_persistence_physically_tested': False,
            'binary_hash_attested_by_device': False, 'full_evidence_replayed_at_build': True}


def validate_qualification(value):
    require(value.get('kind') == 'mini-FX-editor-qualification' and value.get('schema') == 1
            and value.get('evidence_model') == MODEL and value.get('image_sha256') == IMAGE
            and value.get('firmware_version') == VERSION and value.get('transport') == 'usb-cdc'
            and value.get('hardware_protocol_exercised') is True
            and value.get('UI_FX_interactions_physically_tested') is False
            and value.get('whole_editor_qualified') is False and value.get('blanket_write') is False,
            'FX qualification model/scope differs')
    baseline.validate_qualification(value['baseline_qualification'])
    expected = CORE_FAMILIES+FX_FAMILIES+(['FXR'] if value.get('removal_evidence') else [])
    require(value['enabled_families'] == expected
            and bool(value.get('removal_evidence')) == bool(value.get('removal_replay'))
            and value['benchmark'] == BENCHMARK and value['benchmark_replay']['replay_verified'] is True
            and value['benchmark_replay']['baseline_restoration_verified'] is True
            and value['pong'] == value['baseline_qualification']['pong'], 'FX families or evidence differ')
    if value.get('removal_replay'):
        replay = value['removal_replay']
        require(value.get('removal_source_sha256') == REMOVAL_PINS
                and replay.get('temporary_effect_added_then_removed') is True
                and replay.get('saved_baseline_restored') is True
                and replay.get('observations_bound_to_native_commands') is True
                and replay.get('effect_removal_UI_physically_exercised') is False
                and replay.get('general_family_grants') == [], 'FXR scope/replay differs')
    return value


def derive_html(html, old_profile, profile):
    """Small anchored edits of the existing complete editor, not a new UI."""
    changes = []
    def replace(old, new, name):
        nonlocal html
        require(html.count(old) == 1, 'original editor anchor changed: '+name)
        html = html.replace(old, new)
        changes.append({'name': name, 'before_sha256': sha(old.encode()), 'after_sha256': sha(new.encode())})
    def config(value):
        return json.dumps(value, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    replace('globalThis.HYPERRIG_MINI_BUILD='+config(old_profile)+';',
            'globalThis.HYPERRIG_MINI_BUILD='+config(profile)+';', 'new narrow FX profile')
    replace('async function addFx(type, loc) {', '''async function addFx(type, loc) {
  if (!DEMO) {
    const gate = HyperRigMiniFX.add(type, curSegs(), loc, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");
    if (!gate.allowed) { toast(gate.reason, "err"); return null; }
  }''', 'preflight location before any addition')
    replace('async function replaceFx(id, type) {', '''async function replaceFx(id, type) {
  if (!DEMO) { toast("Replace is not enabled. Add or remove individual serial effects instead.", "err"); return; }''',
            'do not remove an old block before an unsupported replacement')
    replace('  if (o.optimistic !== false) {', '''  if (!DEMO) {
    const required = gone.map(id => `FXR ${id}`).concat(xoPre, cmds, mixCmds, xoCmds);
    const gate = HyperRigMiniFX.compound(required, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");
    if (!gate.allowed) { toast("Chain edit unavailable: " + gate.reason, "err"); return false; }
  }
  if (o.optimistic !== false) {''', 'preflight all topology commands before removals or optimistic UI')
    replace('<script src="mini-ui.js"></script>',
            '<script src="mini-ui.js"></script>\n<script src="mini-fx-ui.js"></script>', 'pure FX UI preflight helper')
    return html, changes


def build_bundle(base_directory, output_directory, *, removal_ref=None):
    base = baseline.validate_bundle(base_directory)
    qualification = qualify(base_directory, removal_ref=removal_ref)
    output = local(output_directory, within=ROOT/'build')
    require(not output.exists(), 'new output directory required; live/frozen bundles are never overwritten')
    output.mkdir(parents=True)
    shutil.copytree(local(base['app_directory']), output/'app/web')
    # Preserve converter and all original attribution files, not just the HTML.
    source_app = local(base['app_directory']).parent
    for item in source_app.iterdir():
        if item.name != 'web':
            if item.is_dir(): shutil.copytree(item, output/'app'/item.name)
            else: shutil.copy2(item, output/'app'/item.name)
    proof_path = output/'qualification.json'
    proof_path.write_bytes(encoded(qualification))
    proof_ref = reference(proof_path)
    profile = copy.deepcopy(base['profile'])
    families = qualification['enabled_families']
    profile.update(family_evidence_model=MODEL, family_capabilities={'usb-cdc': families},
                   family_validation={'usb-cdc': [proof_ref]},
                   family_qualification={'usb-cdc': {'enabled_families': families,
                       'evidence_model': MODEL, 'protocol_binding': baseline.app.PROTOCOL_BINDING,
                       'UI_FX_interactions_physically_tested': False, 'every_value_physically_tested': False}})
    spec = copy.deepcopy(profile)
    manifest_path = output/'firmware-manifest.json'
    manifest_path.write_bytes(encoded(spec))
    web = output/'app/web'
    html, patches = derive_html((web/'tankmini.html').read_text('utf-8'), base['profile'], profile)
    (web/'tankmini.html').write_text(html, encoding='utf-8', newline='\n')
    (web/'mini-profile.js').write_bytes(POLICY.read_bytes())
    (web/'mini-fx-ui.js').write_bytes(UI.read_bytes())
    ui = (web/'mini-ui.js').read_text('utf-8')
    require(ui.count('const commandNames = {FXP:') == 1, 'baseline UI labels changed')
    ui = ui.replace('const commandNames = {FXP:', 'const commandNames = {FXA: "aggiunta effetti seriali", FXR: "rimozione effetti", FXP:')
    (web/'mini-ui.js').write_text(ui, encoding='utf-8', newline='\n')
    derivation = output/'app/DERIVATION.txt'
    derivation.write_text(derivation.read_text('utf-8')+
        '\nThis separate FX bundle enables only the USB families listed in qualification.json.\n'
        'The retained preset/UI evidence and the FX protocol evidence have distinct scopes.\n'
        'FX UI actions and persistence of a nonempty FX chain are not claimed as physically tested by this build.\n'
        'The original editor handles admission failures; routing, bulk operations and firmware commands remain outside this profile.\n',
        encoding='utf-8', newline='\n')
    sources = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in (Path(__file__), POLICY, UI)}
    metadata = {'schema': 1, 'kind': 'mini-qualified-FX-editor-bundle', 'evidence_model': MODEL,
                'image_sha256': IMAGE, 'qualification_verifier_sha256': sha(Path(__file__).read_bytes()),
                'app_directory': (web.relative_to(ROOT)).as_posix(), 'profile': profile,
                'manifest': reference(manifest_path), 'qualification': proof_ref,
                'com': base['com'], 'pong': base['pong'], 'source_sha256': sources,
                'editor_patches': patches, 'baseline_bundle': base['refs']['bundle'],
                'runtime_validation': 'local bundle files and qualification seal only; no historical report replay',
                'files': {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()}}
    raw = encoded(metadata)
    (output/'bundle.json').write_bytes(raw)
    (output/'bundle.sha256').write_text(sha(raw)+'\n', encoding='ascii')
    return validate_bundle(output)


def validate_bundle(output_directory):
    """Normal launch: local hashes only. No report replay, browser or device I/O."""
    check_baseline()
    output = local(output_directory, within=ROOT/'build')
    raw = (output/'bundle.json').read_bytes()
    require(len(raw) < 2*1024*1024 and (output/'bundle.sha256').read_text('ascii') == sha(raw)+'\n', 'FX bundle seal differs')
    meta = json.loads(raw)
    require(meta.get('kind') == 'mini-qualified-FX-editor-bundle' and meta.get('schema') == 1
            and meta.get('evidence_model') == MODEL and meta.get('image_sha256') == IMAGE
            and meta.get('qualification_verifier_sha256') == sha(Path(__file__).read_bytes()), 'FX bundle identity/verifier differs')
    files = meta['files']
    require(8 <= len(files) <= 40 and {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
            == set(files) | {'bundle.json', 'bundle.sha256'}, 'FX bundle inventory differs')
    for name, digest in files.items():
        path = local(output/name, within=output)
        require(path.relative_to(output).as_posix() == name and path.stat().st_size <= 8*1024*1024
                and sha(path.read_bytes()) == digest, 'FX bundle file differs: '+name)
    def bundled(ref):
        path = local(ref['path'], within=output)
        require(files.get(path.relative_to(output).as_posix()) == ref['sha256'], 'unsealed FX bundle reference')
        return json.loads(path.read_bytes())
    qualification = validate_qualification(bundled(meta['qualification']))
    spec = bundled(meta['manifest'])
    profile = meta['profile']
    require(profile == spec and profile['capabilities'] == {'identity': True, 'read': True, 'write': False, 'panel': False}
            and profile['image_sha256'] == IMAGE and profile['firmware_version'] == VERSION
            and profile['hardware_verified'] is True
            and profile['family_capabilities'] == {'usb-cdc': qualification['enabled_families']}
            and profile['family_validation'] == {'usb-cdc': [meta['qualification']]}
            and not profile.get('command_capabilities') and not profile.get('write_validation'), 'FX bundle expands capabilities')
    web = local(meta['app_directory'], within=output)
    require(web == output/'app/web' and files['app/web/mini-profile.js'] == sha(POLICY.read_bytes())
            and files['app/web/mini-fx-ui.js'] == sha(UI.read_bytes()), 'FX runtime policy/helpers differ')
    config = json.dumps(profile, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    require('globalThis.HYPERRIG_MINI_BUILD='+config+';' in (web/'tankmini.html').read_text('utf-8'), 'FX HTML profile differs')
    require(meta['pong'] == qualification['pong'] and meta['com'] == qualification['com'], 'FX connection evidence differs')
    return {'app_directory': meta['app_directory'], 'profile': profile, 'manifest': meta['manifest'],
            'image_sha256': IMAGE, 'com': meta['com'], 'pong': meta['pong'], 'qualification': qualification,
            'refs': {'bundle': reference(output/'bundle.json'), 'qualification': meta['qualification'], 'manifest': meta['manifest']},
            'historical_evidence_replayed_on_launch': False, 'device_io': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=Path('build/hyperrig-mini-qualified-editor'))
    parser.add_argument('--build', type=Path)
    parser.add_argument('--check-bundle', type=Path)
    parser.add_argument('--removal-report', type=Path)
    parser.add_argument('--removal-sha256')
    args = parser.parse_args(argv)
    require(bool(args.removal_report) == bool(args.removal_sha256), 'removal report requires exact SHA-256')
    removal = {'path': args.removal_report.as_posix(), 'sha256': args.removal_sha256} if args.removal_report else None
    result = (validate_bundle(args.check_bundle) if args.check_bundle else
              build_bundle(args.baseline, args.build, removal_ref=removal) if args.build else
              {'device_io': False, 'inputs_read': False, 'capabilities_granted': []})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
