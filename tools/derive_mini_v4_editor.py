"""Derive a v4 editor from preserved assets and the completed USB controls trial."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'build/mini-v4-controls-01/report.json'
REPORT_SHA = '7c8bc584e240c053fc3b5e901d65528b7dcc749f8c258dfd4c809ccc46191db8'
WIRE_SHA = '52ad0f2367c45ad92fc5e59fe24febfbdbfe8c334d6c211e00d6516e6d4468bd'
IMAGE = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
REVISION = 'mini-v4-usb-01'
FAMILIES = ['GAIN', 'PLOAD', 'PSAVE', 'SNAPSAVE', 'FXA', 'FXP', 'FXE', 'FXR', 'SNAP']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode('utf-8')


def qualification():
    raw = REPORT.read_bytes()
    require(sha(raw) == REPORT_SHA, 'The completed real v4 report differs')
    report = json.loads(raw)
    wire_raw = (REPORT.parent / 'wire.jsonl').read_bytes()
    require(sha(wire_raw) == WIRE_SHA == report['wire_sha256'], 'The retained native USB transcript differs')
    require(report['result'] == 'pass' and report['hardware_executed'] is True
            and report['baseline_restoration_verified'] is True and report['temporary_slot_deleted'] is True
            and report['preexisting_presets_written'] is False
            and report['baseline_sha256'] == report['final_sha256']
            and report['image_sha256'] == IMAGE and report['enabled_families'] == FAMILIES,
            'A restored, successful trial of this exact installed build is required')
    exchanges, current = [], None
    identified, ping_repetitions = False, 0
    for row in map(json.loads, wire_raw.splitlines()):
        if row['event'] == 'tx':
            require(current is None or current['complete'], 'Overlapping native command exchanges')
            current = {'command': row['command'], 'response': [], 'complete': False}
            exchanges.append(current)
        elif row['event'] == 'line':
            require(current is not None and current['command'] == row['command'], 'Unassociated native response')
            current['response'].append(row['line'])
        elif row['event'] == 'complete':
            require(current is not None and current['command'] == row['command'], 'Unassociated native completion')
            current['complete'] = True
        elif row['event'] == 'identity_accepted':
            identified = True
        elif row['event'] == 'failed':
            require(not identified and current['command'] == 'PING' and not current['response']
                    and row['error'] == 'response timeout for PING' and not row['partial_hex'],
                    'A command failed after identification or received an ambiguous response')
        elif row['event'] == 'handshake_attempt_failed':
            require(not identified and current['command'] == 'PING'
                    and row['outcome'] == 'empty_timeout' and row['native_RX_bytes'] == 0
                    and row['native_write_results'] == [5] and not row['native_transport_errors']
                    and row['repeat_permitted'] is True, 'Unqualified handshake repetition')
            current['complete'] = True
            ping_repetitions += 1
        require(row['event'] not in ('async_line', 'native_tx_error', 'native_rx_error'), 'Native trial contains a failure')
    mutations = [x for x in exchanges if ' ' in x['command']]
    observations = report['observations']
    require(len(mutations) == len(observations), 'Native mutation coverage differs')
    for actual, recorded in zip(mutations, observations):
        require(actual['complete'] and actual['command'] == recorded['command']
                and actual['response'] == recorded['response'] and recorded['readback_verified'] is True,
                'Observed mutation does not match the native transcript')
    require(all(x.get('persistence_readback_verified') is True for x in observations
                if x['command'].startswith(('PSAVE ', 'SNAPSAVE '))), 'Save persistence was not read back')
    return {'schema': 1, 'kind': 'hyperrig-mini-v4-USB-controls-scope', 'revision': REVISION,
            'image_sha256': IMAGE, 'firmware_version': report['firmware_version'],
            'transport': 'usb-cdc', 'enabled_families': FAMILIES, 'hardware_verified': True,
            'current_image_mutations_physically_retested': True,
            'representative_protocol_operations_exercised': True,
            'baseline_restoration_verified': True, 'temporary_preset_removed': True,
            'preexisting_presets_written': False,
            'all_values_or_all_effects_hardware_qualified': False,
            'physical_editor_UI_tested': False, 'physical_switch_banks_tested': False, 'audio_tested': False,
            'blanket_write': False, 'routing_enabled': False, 'BLE_write_enabled': False,
            'device_binary_hash_attestation': False,
            'mutation_retries': 0, 'empty_PING_handshake_repetitions': ping_repetitions,
            'source_report_automatic_retry_field_scope': 'Mutations only; the native transcript records bounded PING repetition.',
            'evidence_sha256': {'native_report': REPORT_SHA, 'native_transcript': WIRE_SHA},
            'installation_readback_sha256': report['installation_association']['verified_flash_sha256'],
            'baseline_state_sha256': report['baseline_sha256']}


def derive(files, info):
    files, info = dict(files), copy.deepcopy(info)
    old_profile = json.loads(files['editor/profile.json'])
    require(old_profile['image_sha256'] == IMAGE and not old_profile['hardware_verified'],
            'Derive from the sealed v4 read-only profile')
    scope = qualification()
    qraw = encoded(scope)
    profile = copy.deepcopy(old_profile)
    profile.update(hardware_verified=True, family_capabilities={'usb-cdc': FAMILIES},
        family_validation={'usb-cdc': [{'path': 'editor/qualification.json', 'sha256': sha(qraw)}]},
        family_qualification={'usb-cdc': {'model': 'v4-representative-USB-controls-v1',
            'families': FAMILIES, 'evidence_sha256': scope['evidence_sha256'],
            'representative_operations_only': True, 'audio_tested': False}},
        family_evidence_model='v4-representative-USB-controls-v1')
    html = files['editor/web/tankmini.html'].decode('utf-8')
    before_html_sha = sha(html.encode('utf-8'))
    marker = 'globalThis.HYPERRIG_MINI_BUILD='
    def embedded(value):
        return marker + json.dumps(value, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c') + ';'
    require(html.count(marker) == 1, 'Expected one previous profile')
    tail = html.split(marker, 1)[1]
    previous, end = json.JSONDecoder().raw_decode(tail)
    require(previous == old_profile and tail[end:end + 1] == ';', 'Previous profile binding differs')
    html = html.replace(marker + tail[:end + 1], embedded(profile))
    with tempfile.TemporaryDirectory(prefix='mini-v4-presentation-', dir=ROOT / 'build') as temp:
        temp = Path(temp).resolve()
        require(temp.is_relative_to((ROOT / 'build').resolve()), 'Temporary output leaves the build directory')
        (temp / 'input.html').write_bytes(html.encode('utf-8'))
        subprocess.run(['node', str(ROOT / 'tools/editor/derive_mini_v4.cjs'), str(temp / 'input.html'),
                        str(temp / 'output.html'), str(temp / 'report.json')], check=True, cwd=ROOT)
        files['editor/web/tankmini.html'] = (temp / 'output.html').read_bytes()
        presentation = json.loads((temp / 'report.json').read_bytes())
    ui = files['editor/web/mini-ui.js'].decode('utf-8')
    start, end = ui.index('  note.textContent = demo ?'), ui.index('  const top =')
    ui = ui[:start] + ('  note.textContent = demo ? "HyperRig MINI · Offline demo" :\n'
                      '    "HyperRig MINI · v4 preview · Connect by USB to edit effects, presets and scenes.";\n') + ui[end:]
    ui = ui.replace('MINI firmware port in development', 'HyperRig MINI installation guide')
    files['editor/web/mini-ui.js'] = ui.encode('utf-8')
    files['editor/profile.json'] = encoded(profile)
    files['editor/qualification.json'] = qraw
    files['editor/DERIVATION.txt'] = (
        'HyperRig MINI v4 preview.\n'
        'Derived from the preserved English editor with unchanged firmware and command policy.\n'
        'Nine USB command families were exercised on the installed v4 image; original state was restored.\n'
        'Qualification covers representative protocol operations, not all effects, audio or physical switches.\n'
        'The editor groups the same 32 device slots into A/B/C banks; four scenes remain available per preset.\n'
        'Physical switch dispatch is unchanged and its bank behavior is not qualified by the UI change.\n'
        'No personal paths, raw reports, presets or device dumps are included.\n'
        'Original license notices are preserved.\n'
    ).encode('utf-8')
    info.update(revision=REVISION, read_only=False, families=FAMILIES,
                qualification_sha256=sha(qraw), previous_portable_html_sha256=before_html_sha,
                presentation=presentation, presentation_deriver_sha256=sha((ROOT / 'tools/editor/derive_mini_v4.cjs').read_bytes()))
    return files, info
