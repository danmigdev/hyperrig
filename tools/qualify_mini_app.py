"""Bind completed offline installation/boot/USB evidence to a NEW app profile.

Default is a plan. No serial, USB, browser, reset or firmware-writing API is
used. Evidence consistency is checked; these logs are not device authentication.
The pinned audio-v2 manifest and distribution are never modified.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_app as app
from tools import inspect_mini_installed as installed
from tools import probe_mini_app as readonly
from tools import probe_mini_app_first_preset as first
from tools import probe_mini_app_mutation as mutation

BASE = ROOT / 'build/hyperrig-mini-audio-v2/firmware-manifest.json'
BASE_SHA = 'f119ab571a6cb04c8ca72513b5d18d614e079e756d209ce5794fbaeb4fe77d12'
IMAGE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
VERSION = 'tankm_fw M5.71 rel ble'
REQUIRED_READS = {'MODEL', 'MEM', 'LVL', 'FXT', 'FXS', 'PLIST', 'PSTAT', 'SNAPS', 'SNAPNAME'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def local(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'evidence/output must stay in the workspace')
    return path


def reference(path):
    path = local(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes())}


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.utcoffset() is not None, 'timezone-aware evidence timestamp required')
    return result


def verify_pins(report):
    require(isinstance(report.get('source_pins'), dict) and report['source_pins'], 'boot source pins missing')
    for name, digest in report['source_pins'].items():
        require(sha(local(ROOT / name).read_bytes()) == digest, 'boot source changed: ' + name)


def validate_boot(install, install_ref, held, released):
    for item, buttons in ((held, 'held'), (released, 'released')):
        require(item.get('finished_utc') and not item.get('error') and item['buttons_confirmed_by_user'] == buttons
                and item['candidate_sha256'] == IMAGE_SHA and item['reset_submitted'] is True
                and item['firmware_write'] is False and item['automatic_retry'] is False,
                'completed exact candidate/button boot observation required')
        require(item['installation_evidence_path'] == install_ref['path']
                and item['installation_evidence_sha256'] == install_ref['sha256'], 'boot is bound to another installation')
    require(held['phase'] == 'fresh_ROM_observed' and held['fresh_ROM_verified'] is True
            and len(held['arrival_after']) == 1
            and timestamp(held['arrival_after'][0]['arrival_utc']) > timestamp(held['arrival_before']['arrival_utc'])
            and held['fresh_inquiry']['vendor'] == 'WL82' and held['fresh_inquiry']['product'] == 'UBOOT1.00',
            'held buttons did not establish a fresh ROM arrival and INQUIRY')
    require(released['phase'] == 'application_USB_observed' and released['application_USB_enumerated'] is True
            and released['arrival_before'] == held['arrival_after'][0], 'released boot is not the observed held ROM continuation')
    ports = released['application_ports']
    require(len(ports) == 1 and (ports[0]['vid'], ports[0]['pid']) == (readonly.VID, readonly.PID)
            and re.fullmatch(r'COM[1-9][0-9]{0,3}', ports[0]['device']), 'one exact MINI CDC port required')
    require(timestamp(install['finished_utc']) <= timestamp(held['started_utc']) <= timestamp(held['finished_utc'])
            <= timestamp(released['started_utc']) <= timestamp(released['finished_utc']), 'boot chronology differs')
    return ports[0]


def validate_read_trace(raw, port, released):
    """Replay retained raw bytes with the frozen readonly parser, never a port."""
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line]
    def one(event):
        found = [x for x in rows if x.get('event') == event]
        require(len(found) == 1, 'one ' + event + ' event required')
        return found[0]
    require(rows and rows[0]['event'] == 'start' and rows[-1]['event'] == 'port_closed', 'completed closed readonly journal required')
    start, selected, summary = one('start'), one('port_selected'), one('session_complete')
    one('port_opened'); one('port_closed')
    require(not any(x.get('event') in ('failed', 'session_failed', 'identity_rejected', 'plist_incoherent',
                                     'port_close_failed') or x.get('hardware_executed') is False for x in rows),
            'failed/simulated readonly trace cannot qualify the app')
    require(start['expected_image_sha256'] == IMAGE_SHA and start['expected_firmware'] == VERSION
            and start['mutations_enabled'] is False
            and start['source'] == json.loads(json.dumps(readonly.source_contract())),
            'readonly candidate/source binding differs')
    require((selected['device'], selected['vid'], selected['pid']) == (port['device'], port['vid'], port['pid'])
            and summary['port'] == {k: v for k, v in selected.items() if k not in ('utc', 'monotonic', 'event')},
            'readonly port differs from released CDC')
    require(summary['read_only_session_completed'] is True and summary['firmware_writes_tested'] is False
            and summary['audio_verified'] is False and summary['expected_image_sha256'] == IMAGE_SHA,
            'readonly session summary differs')
    commands = [x['command'] for x in rows if x.get('event') == 'tx']
    require(commands == summary['commands'] and commands[0] == 'PING' and len(set(commands)) == len(commands)
            and set(commands[1:]) <= set(readonly.QUERIES) and REQUIRED_READS <= set(commands),
            'complete preset-read qualification queries required, with no mutations')
    require(timestamp(released['finished_utc']) <= timestamp(start['utc']) <= timestamp(rows[-1]['utc']),
            'readonly session predates released boot')
    tape = first._TraceReplay(raw)
    replay = []
    probe = readonly.ReadOnlyProbe(tape, VERSION, clock=tape.clock,
                                  log=lambda event, **fields: replay.append({'event': event, **fields}))
    answers = {'PING': probe.identify()}
    for command in commands[1:]: answers[command] = probe.query(command)
    require(tape.position == len(tape.exchanges) and not tape.pending and not probe.buffer,
            'readonly replay has unconsumed commands or bytes')
    keys = {'tx': ('command', 'hex', 'timeout_seconds'), 'rx': ('command', 'hex', 'bytes'),
            'line': ('command', 'line'), 'async_line': ('command', 'line'), 'complete': ('command', 'lines'),
            'identity_accepted': ('target', 'firmware_version', 'pong', 'binary_hash_attested_by_device')}
    def wire_projection(items):
        return [(x['event'], {k: x[k] for k in keys[x['event']]}) for x in items if x.get('event') in keys]
    require(wire_projection(rows) == wire_projection(replay) and summary['identity'] == probe.identity,
            'retained parsed replies differ from raw-byte replay')
    types = mutation.parse_fxt(answers['FXT']['lines'])
    fxs = mutation.parse_fxs(answers['FXS']['lines'])
    snaps = mutation.parse_snaps(answers['SNAPS']['lines'])
    plist = answers['PLIST']['parsed']
    return {'identity': probe.identity, 'commands': commands, 'port': port, 'serial_port_closed': True,
            'observed_utc': rows[-1]['utc'], 'FXT': types, 'FXS': fxs, 'PLIST': plist, 'SNAPS': snaps,
            'preset_trial_path': 'first-preset-free-slot' if plist['current'] == -1 else 'existing-preset-restore',
            'audio_verified': False, 'BLE_verified': False, 'preset_writes_verified': False}


def encode(value):
    return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def write_new(path, value):
    with local(path).open('xb') as stream:
        stream.write(encode(value))


def qualify_read(install_run, held_run, released_run, read_log, output):
    paths = [local(x) for x in (install_run, held_run, released_run, read_log)]
    output = local(output)
    require(not output.exists(), 'new output directory required; pinned artifacts cannot be overwritten')
    require(sha(BASE.read_bytes()) == BASE_SHA, 'pinned candidate manifest changed')
    base = json.loads(BASE.read_bytes())
    app.load_profile(BASE)
    inspection = installed.inspect_bundle(paths[0])  # Full independent offline NOR/writer proof.
    install, held, released = [json.loads(p.read_bytes()) for p in paths[:3]]
    verify_pins(held); verify_pins(released)
    port = validate_boot(install, reference(paths[0]), held, released)
    read = validate_read_trace(paths[3].read_bytes(), port, released)
    proof = {'schema': 1, 'kind': 'mini-app-usb-read-qualification', 'target': 'tank-mini',
             'firmware_version': VERSION, 'image_sha256': IMAGE_SHA, 'transport': 'usb-cdc',
             'boot_USB_read_verified': True, 'read': read,
             'evidence': {name: reference(p) for name, p in zip(('installation', 'held', 'released', 'read_log'), paths)},
             'base_manifest': reference(BASE), 'implementation': reference(Path(__file__)),
             'verifier_sources': [reference(Path(module.__file__)) for module in (installed, readonly, first, mutation, app)],
             'evidence_consistency_only': True, 'image_hash_attested_by_device': False,
             'cold_power_cycle_verified': False, 'audio_verified': False, 'BLE_verified': False,
             'preset_writes_verified': False, 'all_editor_mutations_verified': False,
             'limits': ['USB boot/read is the scope of hardware_verified in this derived manifest.',
                        'Logs bind the installed bytes to the observed session; PONG does not attest a binary hash.',
                        'Held/released SPL resets do not prove cold power-on or damaged-entry recovery.',
                        'No assertion about intervening resets or concurrent clients; operator must retain the same session.']}
    proof_ref = {'path': (output/'read-qualification.json').relative_to(ROOT).as_posix(), 'sha256': sha(encode(proof))}
    derived = copy.deepcopy(base)
    derived.update(hardware_verified=True, capabilities={'identity': True, 'read': True, 'write': False, 'panel': False},
                   hardware_validation=proof_ref, qualification_scope='observed USB boot and readonly protocol only',
                   command_capabilities={}, family_capabilities={}, family_validation={})
    derived['remaining_gates'] = ['Analog audio and actual sample-clock operation are not verified.',
        'Cold power-on and recovery with damaged header/entry/guard are not verified.',
        'Preset writes and transport-specific editor families need separate retained physical trials.',
        'BLE and physical LED/knob behavior are not qualified by USB reads.']
    browser = {'schema': 1, 'target': 'tank-mini', 'transport': 'usb-cdc', 'vid': readonly.VID, 'pid': readonly.PID,
               'com': port['device'], 'pong': read['identity']['pong'], 'image_sha256': IMAGE_SHA,
               'serial_port_closed': True, 'observed_utc': read['observed_utc'], 'qualification': proof_ref}
    output.mkdir(parents=True)
    for filename, value in (('installation-inspection.json', inspection), ('read-qualification.json', proof),
                            ('firmware-manifest.json', derived), ('browser-evidence.json', browser)):
        write_new(output/filename, value)
    app.load_profile(output/'firmware-manifest.json')
    return {'manifest': reference(output/'firmware-manifest.json'), 'browser_evidence': reference(output/'browser-evidence.json'),
            'preset_trial_path': read['preset_trial_path'], 'device_io': False}


def qualify_families(manifest, reports, output):
    manifest, output = local(manifest), local(output)
    require(not output.exists() and output.parent.is_dir(), 'new manifest path in an existing directory required')
    spec = json.loads(manifest.read_bytes()); app.load_profile(manifest)
    proof = json.loads(app.local_evidence(spec.get('hardware_validation'), 'USB read qualification'))
    require(proof.get('kind') == 'mini-app-usb-read-qualification' and proof.get('boot_USB_read_verified') is True
            and proof['image_sha256'] == IMAGE_SHA and spec['image_sha256'] == IMAGE_SHA
            and spec['hardware_verified'] is True and spec['capabilities']['write'] is False,
            'derived USB-read profile required')
    require(set(proof.get('evidence', {})) == {'installation', 'held', 'released', 'read_log'}
            and proof.get('base_manifest') == reference(BASE)
            and proof.get('implementation') == reference(Path(__file__))
            and proof.get('verifier_sources') == [reference(Path(module.__file__)) for module in (installed, readonly, first, mutation, app)],
            'complete pinned read qualification inputs and verifier sources required')
    for item in proof['evidence'].values(): app.local_evidence(item, 'retained USB qualification input')
    app.local_evidence(proof['implementation'], 'qualification implementation')
    references, families = [], set()
    for path in reports:
        ref = reference(path); evidence = json.loads(app.local_evidence(ref, 'USB trial'))
        require(evidence.get('transport') == 'usb-cdc' and evidence.get('hardware_executed') is True,
                'physical USB trial required; BLE and mock reports cannot grant USB families')
        actual = app.command_grants(evidence.get('physically_exercised_requests', {}))
        require(actual, 'trial has no physically exercised requests')
        families.update(actual); references.append(ref)
    require(references, 'at least one completed physical trial required')
    spec.update(command_capabilities={}, family_capabilities={'usb-cdc': sorted(families)},
                family_validation={'usb-cdc': references})
    app.load_family_validation(spec, spec['capabilities'])  # Includes original first-preset raw-trace replay.
    spec['remaining_gates'] = [x for x in spec['remaining_gates'] if not x.startswith('Preset writes')]
    spec['remaining_gates'].append('Only listed USB families have representative proof; power-cycle persistence and all values are not proved.')
    write_new(output, spec)
    return {'manifest': reference(output), 'usb_families': sorted(families), 'BLE_families': [],
            'blanket_write': False, 'device_io': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action')
    read = commands.add_parser('read', help='derive a new readonly manifest from completed retained evidence')
    for name in ('install-run', 'held-run', 'released-run', 'read-log', 'output-dir'):
        read.add_argument('--'+name, type=Path, required=True)
    families = commands.add_parser('families', help='grant only physically exercised USB families')
    families.add_argument('--manifest', type=Path, required=True)
    families.add_argument('--reports', type=Path, nargs='+', required=True)
    families.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action == 'read':
        result = qualify_read(args.install_run, args.held_run, args.released_run, args.read_log, args.output_dir)
    elif args.action == 'families':
        result = qualify_families(args.manifest, args.reports, args.output)
    else:
        result = {'device_io': False, 'inputs_read': False, 'sequence': [
            'completed full NOR install verification', 'held/released boot observations',
            'closed literal USB readonly session including FXT/FXS/PLIST/SNAPS',
            'new readonly manifest', 'explicit first-preset or restored existing-preset trial',
            'new USB family manifest', 'build app to a new output directory']}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
