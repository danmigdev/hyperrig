"""Offline qualification of one retained original-editor preset roundtrip.

All explicit models retain one preset: one reload, no delete or power cycle.
A stopped four-write save plus a separate two-write reload remain two reports.
Continuation v2 separately proves native USB identity and bounded PING bootstrap.
Only a completed real browser report can create the four-family USB bundle.
The expensive provenance replay runs at build time. Normal launch checks the
sealed local bundle only; historical dumps are not runtime dependencies.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
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
from tools import probe_mini_browser_first_preset as trial
from tools import run_mini_v3_first_preset_a2 as a2
from tools.mini_host_journal import read_shared_bytes

IMAGE = '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c'
VERSION = 'tankm_fw M5.71 rel ble'
MODEL = 'browser-retained-one-reload-v1'
JOINT_MODEL = 'browser-retained-save-and-reload-two-sessions-v1'
JOINT_MODEL_V2 = 'browser-retained-save-and-reload-two-sessions-v2'
MODELS = (MODEL, JOINT_MODEL, JOINT_MODEL_V2)
PARTIAL_REF = {'path': 'build/mini-first-preset-ui-04/report.json',
               'sha256': '0eb9836638dd2025d9e75f380db4cc9c765c53dcc7ff4e0316ab810c3d2479ff'}
FAMILIES = ['GAIN', 'PLOAD', 'PSAVE', 'SNAPSAVE']
BASE_MANIFEST = 'build/hyperrig-mini-audio-v3/firmware-manifest.json'
PINS = {
    'tools/build_mini_app.py': '529e9be717919c52659249d1732ba7e1c7916cfd35ba94562f59104c4f7f8176',
    'tools/probe_mini_browser_first_preset.py': '87b4063f8e50cabb2d0cd230b1db279770211636842698d7048f748080831c3b',
    'tools/run_mini_v3_first_preset_a2.py': 'c234aa9d36f9b0c95e71a692881f81342773d6e237766f1a2d1ed49df65ac2ab',
    'tools/mini_browser_first_preset_guard.js': '4157be429799c27b404f9d8762866515492af595cbbe432ba6e17d3298d394ce',
    'tools/mini_capture_persistence.py': '6c248c90dfcddda96dcdff6a531bd026168e468aa81372b5621b040e7980416a',
    'app/mini/mini-profile.js': '237d6db737a23a24b91417c47d08c40b69f30556197b6de5e3ffb08d3cd04e23',
    'app/mini/mini-ui.js': 'b54aa4258391102ed66b06aeab21aa0936466d51c9e56afbaffb990837046007',
    BASE_MANIFEST: 'd901cc0d673b7f477bc9000be16d95d195b916ffb4e26f512ed00048b6c27deb',
}
BOOTSTRAP_PINS = {
    'tools/run_mini_v3_first_preset_a2_v2.py': '9dec40a7b14a3c07bc5a556779902dcb32d713868518da97177c3abeefca17c9',
    'tools/mini_browser_first_preset_guard_v2.js': 'af14b3c7a71e72dffa23228e252b88053a075f0bdeffb024b22783761fc49367',
}
UI_PINS = {
    'tools/run_mini_v3_first_preset_ui_v3.py': 'e502afdc2bf2c67c6c457f19d374b2e8fdcdedb3b976d923c3d80ae866daac5e',
    'app/mini/mini-ui-v2.js': 'd12cfa13ed3e414b600f23ec6cb8be3989632f4990d50079855b5beebaea663d',
}
UI_EXTENSION_SHA = 'eb9027fe0d2a45133682b949adf9b093f2636032aeade548561ac8c0575fff90'
RESUME_PINS = {
    'tools/probe_mini_browser_saved_reload.py': '8f044dcd2ab5cc98521a02b972a473cb5a686c3f7f88ef47c1e1c7fcec300db4',
    'tools/mini_browser_saved_reload_guard.js': 'e0de0abe48c29ec28ba7c7a02ecfe1ce79225db8079786e1e34fc31c8c9982f9',
}
RESUME_V2_PINS = {
    'tools/probe_mini_browser_saved_reload_v2.py': '4a2bc7fe885442db181cf49cbcb8ea688f4844d41c25493adff011735ff9ff82',
    'tools/mini_browser_saved_reload_guard_v2.js': 'ed25540b9195b3a948c8cc076867ba8c7cb62c71a966b70604293dc29ed9849e',
    'tools/mini_browser_windows.py': '92b6e259da3ff7eb79d38d4b290a2ea5372310bc1a8993cdbfe2af9296467410',
}
SNAPSHOTS = ('initial_activity_before', 'initial', 'before_activity', 'before',
             'down1', 'up', 'saved', 'marker', 'reloaded')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def local(path, *, within=ROOT):
    value = Path(path)
    if not value.is_absolute():
        value = ROOT / value
    resolved = value.resolve()
    require(resolved.is_relative_to(within.resolve()), 'path leaves its permitted directory')
    # No reparse/symlink indirection in the file or any existing parent.
    cursor = value.absolute()
    while cursor != ROOT.parent and cursor != cursor.parent:
        if cursor.exists():
            require(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(),
                    'reparse path is not accepted')
        cursor = cursor.parent
    return resolved


def reference(path):
    path = local(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(read_shared_bytes(path))}


def read_ref(ref):
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}
            and isinstance(ref['path'], str) and re.fullmatch('[0-9a-f]{64}', str(ref['sha256'])),
            'an exact local path/SHA-256 reference is required')
    data = read_shared_bytes(local(ref['path']), maximum=32*1024*1024)
    require(0 < len(data) <= 32*1024*1024 and sha(data) == ref['sha256'], 'evidence bytes/hash differ')
    return data


def stamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timestamp needs timezone')
    return parsed


def one_event(guard, name):
    rows = [row for row in guard['events'] if row.get('kind') == name]
    require(len(rows) == 1, 'exactly one '+name+' event required')
    return rows[0]


def replay_responses(guard, answers, *, low, high, epoch):
    """Bind an ordered snapshot to distinct actual exchanges in its UI interval.

    Periodic readonly exchanges may be interleaved. Responses from an earlier
    epoch or another command cannot stand in for the snapshot being checked.
    """
    cursor = low
    matched = []
    for request, lines in answers.items():
        matches = []
        for wire in guard['wire']:
            if not (wire['line'] == request and cursor < wire['seq'] < high):
                continue
            command = next(c for c in guard['commands'] if c['id'] == wire['command_id'])
            if command['seq'] < high and command.get('lines') == lines and command.get('epoch') == epoch:
                matches.append((wire, command))
        require(matches, 'snapshot lacks its fresh native exchange: '+request)
        wire, command = min(matches, key=lambda pair: pair[0]['seq'])
        cursor = command['seq']
        matched.append(command['id'])
    return cursor, matched


def verify_partial_wire(guard):
    """Verify the four real writes of the stopped session, without padding it."""
    require(guard.get('fatal') == 'Actual focused Output knob and S.gain differ'
            and guard.get('phase') == 'scene_ack' and guard.get('mutations') == 4
            and guard.get('requests') == guard.get('opens') == guard.get('closes') == 1
            and guard.get('stopped') is True and not guard.get('closeError'), 'unexpected partial guard outcome')
    wire, commands, rx = guard['wire'], guard['commands'], guard['rx']
    require(0 < len(wire) <= 2000 and rx, 'bounded native partial trace required')
    plan = one_event(guard, 'trial_plan')['plan']; cp = one_event(guard, 'capture_plan')['plan']
    require(guard.get('captureVerified') is True, 'capture not byte-verified')
    expected = ['GAIN '+' '.join(map(str, plan['down'])), 'GAIN '+' '.join(map(str, plan['gain'])),
                plan['save_request'], 'SNAPSAVE 0']
    origins = ['Output ArrowDown', 'Output ArrowUp', 'Original empty-row Save', 'Original sceneAOnSave']
    ui_wire = [w for w in wire if w['origin'] not in ('query', 'diagnostic capture persistence', 'diagnostic capture byte read')]
    require([(w['line'], w['origin']) for w in ui_wire] == list(zip(expected, origins)), 'partial UI writes differ')
    diagnostic = [w['line'] for w in wire if w['origin'].startswith('diagnostic capture ')]
    require(diagnostic == cp['requests'] and guard['captureMutations'] == sum(x.startswith('CSAVE ') for x in diagnostic),
            'partial capture read/write sequence differs')
    require([(u['kind'], u.get('key')) for u in guard['ui']] ==
            [('keydown', 'ArrowDown'), ('keydown', 'ArrowUp'), ('click', None)]
            and all(u.get('trusted') is True for u in guard['ui']), 'partial trusted UI sequence differs')
    acks = [e for e in guard['events'] if e.get('kind') == 'mutation_ack']
    require([a['line'] for a in acks] == expected, 'partial ACK sequence differs')
    for index, item in enumerate(ui_wire):
        require(guard['ui'][min(index, 2)]['seq'] < item['seq'] < acks[index]['seq']
                and (index == 0 or acks[index-1]['seq'] < item['seq']), 'partial UI/ACK chronology differs')
    for item in wire:
        require(item['hex'] == (item['line']+'\n').encode('ascii').hex() and item.get('completed') is True, 'partial write framing/completion differs')
        if item['origin'] == 'query': require(trial.evidence.is_query(item['line']), 'mutation disguised as query')
        matches = [c for c in commands if c['id'] == item['command_id'] and c.get('wire_id') == item['id']]
        require(len(matches) == 1 and matches[0].get('completed') is True and matches[0]['line'] == item['line'], 'partial command completion missing')
        cmd = matches[0]
        if item in ui_wire:
            ack = acks[ui_wire.index(item)]
            require(cmd['lines'] == ack['lines'] and cmd['seq'] < ack['seq'], 'partial actual ACK differs')
        native = b''.join(bytes.fromhex(r['hex']) for r in rx if item['seq'] < r['seq'] < cmd['seq'])
        lines = native.decode('utf-8').replace('\r\n', '\n').splitlines(); cursor = 0
        for line in cmd['lines']:
            try: cursor = lines.index(line, cursor)+1
            except ValueError: raise ValueError('partial response absent from native RX: '+item['line']) from None
    return {'raw_RX_byte_count': sum(len(bytes.fromhex(r['hex'])) for r in rx), 'wire_command_count': len(wire),
            'completed_commands_checked_against_native_RX': True}


def inspect_trial(report, blob, *, _partial=False):
    """Pure transcript consistency, also testable with labelled synthetic data.

    This function alone never grants capabilities or attests physical execution.
    validate_trial_report adds source, file, installation and browser provenance.
    """
    require(report.get('schema') == 1 and report.get('kind') == 'mini-browser-first-preset-v3-trial'
            and report.get('result') == ('fail' if _partial else 'pass')
            and report.get('phase') == ('persistence_marker_intent' if _partial else 'UI_save_reload_complete'),
            'only a completed original-editor retained-preset trial is supported')
    complete_claims = ('UI_sequence_completed', 'ui_roundtrip_verified', 'save_reload_verified',
                       'preset_intentionally_retained', 'capture_intentionally_retained')
    for key in ('serial_port_closed', 'browser_process_stopped', 'local_server_stopped') + (() if _partial else complete_claims):
        require(report.get(key) is True, 'missing completed observation: '+key)
    for key in ('audio_quality_verified', 'power_cycle_verified', 'held_recovery_verified',
                'BLE_verified', 'firmware_write', 'automatic_retry', 'profile_modified'):
        require(report.get(key) is False, 'unproved/unexpected operation claim: '+key)
    require(not any(report.get(k) for k in (('cleanup_error', 'publication_error') if _partial else ('error', 'cleanup_error', 'publication_error')))
            and report.get('general_capabilities_granted') == {}, 'trial failed or granted unrelated capabilities')
    if _partial:
        require(report.get('failed_phase') == 'persistence_marker_intent'
                and 'NotAllowedError: Actual focused Output knob and S.gain differ' in str(report.get('error'))
                and all(not report.get(k) for k in complete_claims) and 'marker' not in report and 'reloaded' not in report,
                'partial report claims an unperformed reload or a different failure')
    require(report.get('image_sha256') == IMAGE and report.get('transport') == 'usb-cdc',
            'wrong image or transport')
    guard = report['guard']
    require(guard.get('live') is True and guard.get('appInstalled') is True
            and guard.get('pongMatched') is True and guard.get('portInfo') == {'vid': 0x3654, 'pid': 0x5155},
            'native USB and original-editor connection evidence required')
    disconnect = report['disconnect']
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes') == 1 and not disconnect.get('closeError'), 'native port did not close')
    raw = verify_partial_wire(guard) if _partial else trial.verify_wire(guard)
    if not _partial: require(raw == report.get('raw_trace_verification'), 'raw trace summary differs')
    require(0 < raw['raw_RX_byte_count'] <= 2*1024*1024
            and guard.get('rxBytes') == raw['raw_RX_byte_count'], 'native RX extent differs')
    require([u.get('target') for u in guard['ui']] ==
            (['Output', 'Output', 'empty-row Save'] if _partial else
             ['Output', 'Output', 'empty-row Save', 'Output', 'preset-row']), 'trusted UI target differs')
    commands = guard['commands']
    require(len({c['id'] for c in commands}) == len(commands)
            and len({w['id'] for w in guard['wire']}) == len(guard['wire']), 'duplicate command/wire identifiers')
    require(all(c.get('completed') is True and c.get('wire_id') is not None for c in commands)
            and len(commands) == len(guard['wire']), 'unbound or unfinished original command')
    require(all(c['seq'] > 0 for c in commands), 'invalid completion sequence')
    seqs = [row['seq'] for name in ('events', 'ui', 'wire', 'rx', 'commands') for row in guard[name]]
    require(len(seqs) == len(set(seqs)) and all(type(s) is int and s > 0 for s in seqs), 'duplicate/invalid chronology')
    for name in ('events', 'ui', 'wire', 'rx'):
        require([r['seq'] for r in guard[name]] == sorted(r['seq'] for r in guard[name]), 'unordered '+name)

    installed = one_event(guard, 'experimental_guard_installed')
    requested = one_event(guard, 'serial_request_intent')
    open_intent = one_event(guard, 'serial_open_intent')
    opened = one_event(guard, 'serial_open_complete')
    capture_event = one_event(guard, 'capture_plan')
    capture_done = one_event(guard, 'capture_verified_by_host')
    trial_event = one_event(guard, 'trial_plan')
    stopped = one_event(guard, 'guard_stopped')
    finished = stopped if _partial else one_event(guard, 'trial_complete')
    if _partial: require(not any(e.get('kind') == 'trial_complete' for e in guard['events']), 'partial session cannot be marked complete')
    close_intent = one_event(guard, 'serial_close_intent')
    closed = one_event(guard, 'serial_close_complete')
    require(installed['seq'] < requested['seq'] < open_intent['seq'] < opened['seq']
            < capture_event['seq'] < capture_done['seq'] < trial_event['seq']
            < finished['seq'] <= stopped['seq'] < close_intent['seq'] < closed['seq'], 'lifecycle/phase chronology differs')
    states = {}
    for name in (SNAPSHOTS[:7] if _partial else SNAPSHOTS):
        item = report[name]
        require(set(item) == {'responses', 'state'} and set(item['responses']) == {*trial.READS, 'STAT'},
                'complete original snapshot plus one STAT required: '+name)
        answers = item['responses']
        state = trial.parse_snapshot({key: answers[key] for key in trial.READS})
        state['a2_stat'] = a2.parse_stat(answers['STAT'])
        a2.checked_stat(state)
        require(state == item['state'], 'stored snapshot differs from retained answers: '+name)
        states[name] = state
    require(report['initial_processing'] == a2.progress(trial, states['initial_activity_before'], states['initial'])
            and report['UI_processing'] == a2.progress(trial, states['before_activity'], states['before']),
            'A2 processing progression differs from complete STAT observations')

    cp = trial.capture.plan_capture(report['initial']['responses'], blob)
    require(report['capture_plan'] == cp, 'capture plan differs from initial actual inventory')
    cap_answers = report['capture_verification']['command_responses']
    verified_capture = trial.capture.verify_capture(cp, cap_answers, blob)
    require(verified_capture == report['capture_verification'], 'capture readback verification differs')
    requests = ([cp['request']] if cp['request'] else [])+[cp['header_request'], *cp['chunk_requests']]
    require(capture_event['plan'] == {'slot': cp['slot'], 'requests': requests}, 'wire capture plan differs')
    require(states['before_activity']['clist'] == verified_capture['clist']
            and states['before']['clist'] == verified_capture['clist'], 'capture is not current before the UI trial')
    # CSAVE may change only the capture inventory/current pointer, not the live
    # preset, FX, gain, IR or tone state that will subsequently be saved.
    preserved = copy.deepcopy(states['before_activity'])
    preserved['clist'] = copy.deepcopy(states['initial']['clist'])
    trial.verify_state(preserved, states['initial'], gains=states['initial']['gain'], stage='live')
    plan = trial.make_plan(states['before'], report['plan']['name'])
    require(report['plan'] == plan and trial_event['plan'] == plan, 'UI plan differs from original free-slot state')
    for name, gain, phase in (('down1', plan['down'], 'live'), ('up', plan['gain'], 'live'),
                              ('saved', plan['gain'], 'saved'), ('marker', plan['down'], 'saved'),
                              ('reloaded', plan['gain'], 'reloaded')):
        if _partial and name in ('marker', 'reloaded'): continue
        trial.verify_state(states[name], states['before'], gains=gain, stage=phase, plan=plan)

    ui_wire = [w for w in guard['wire'] if w['origin'] not in
               ('query', 'diagnostic capture persistence', 'diagnostic capture byte read')]
    acks = [e for e in guard['events'] if e.get('kind') == 'mutation_ack']
    expected_acks = [
        [f"GAIN in={plan['down'][0]} out={plan['down'][1]} dB"],
        [f"GAIN in={plan['gain'][0]} out={plan['gain'][1]} dB"],
        [f"PSAVE ok {plan['slot']} '{plan['name']}' {plan['blocks']} blocks capture={plan['capture_slot']} ir={plan['ir_slot']}"],
        [f"SNAPSAVE ok 0 preset={plan['slot']}"],
        [f"GAIN in={plan['down'][0]} out={plan['down'][1]} dB"],
    ]
    require([x['lines'] for x in acks[:5]] == (expected_acks[:4] if _partial else expected_acks), 'mutation ACK content differs')
    if not _partial:
        require(len(acks[5]['lines']) == 1 and re.fullmatch(
            r"PLOAD ok "+str(plan['slot'])+r" '"+re.escape(plan['name'])+r"' missing=0 capture="+
            str(plan['capture_slot'])+r" ir="+str(plan['ir_slot'])+r" ms=\d+", acks[5]['lines'][0]), 'PLOAD ACK differs')
    require([event.get('epoch') for event in acks] == list(range(2, 6 if _partial else 8))
            and guard.get('epoch') == (5 if _partial else 7),
            'capture/ACK epoch history differs')
    ranges = [
        ('initial_activity_before', opened['seq'], capture_event['seq'], 0),
        ('initial', None, capture_event['seq'], 0),
        ('before_activity', capture_done['seq'], trial_event['seq'], 1),
        ('before', None, trial_event['seq'], 1),
        ('down1', acks[0]['seq'], ui_wire[1]['seq'], 2),
        ('up', acks[1]['seq'], ui_wire[2]['seq'], 3),
        ('saved', acks[3]['seq'], stopped['seq'] if _partial else ui_wire[4]['seq'], 5),
    ]
    if not _partial:
        ranges += [('marker', acks[4]['seq'], ui_wire[5]['seq'], 6), ('reloaded', acks[5]['seq'], finished['seq'], 7)]
    matched = {}
    cursor = 0
    for name, low, high, epoch in ranges:
        ordered = {k: report[name]['responses'][k] for k in (*trial.READS, 'STAT')}
        cursor, matched[name] = replay_responses(guard, ordered, low=cursor if low is None else low, high=high, epoch=epoch)
    ordered_cap = {key: cap_answers[key] for key in (*requests, 'MODEL', 'CLIST')}
    _, matched['capture'] = replay_responses(guard, ordered_cap, low=capture_event['seq'], high=capture_done['seq'], epoch=0)
    used = [cid for ids in matched.values() for cid in ids]
    require(len(used) == len(set(used)), 'one response was reused for different observations')
    pongs = [line for c in commands if c['line'] == 'PING' for line in c['lines']]
    pong = report['prepared']['context']['pong']
    require(pongs and all(p == pong for p in pongs) and pong.startswith('PONG '+VERSION+' ')
            and not re.search(r'\bsafe\b', pong), 'actual normal-mode PONG required')
    exercised = {
        'GAIN': list(dict.fromkeys(w['line'] for w in ui_wire if w['line'].startswith('GAIN '))),
        'PSAVE': [plan['save_request']], 'SNAPSAVE': ['SNAPSAVE 0']}
    if not _partial: exercised['PLOAD'] = [plan['load_request']]
    return {'evidence_model': 'browser-retained-save-partial-v1' if _partial else MODEL,
            'transcript_consistent': True, 'hardware_execution_attested': False,
            'raw_trace': raw, 'snapshot_command_ids': matched,
            'physically_exercised_requests': app.command_grants(exercised),
            'plan': plan, 'capture_sha256': verified_capture['capture_sha256'],
            'A2_initial_progress': report['initial_processing'], 'A2_UI_progress': report['UI_processing'],
            'saved_state_sha256': sha(encoded(states['saved'])),
            'reloaded_state_sha256': None if _partial else sha(encoded(states['reloaded'])),
            'one_reload_verified': not _partial, 'scene_A_selected_by_PLOAD': not _partial,
            'preset_intentionally_retained': True, 'capture_intentionally_retained': True,
            'preexisting_state_preserved': True, 'cold_power_retention_verified': False,
            'audio_quality_verified': False, 'every_value_physically_tested': False}


def validate_report_provenance(report):
    """Shared installation, source and closed-browser provenance, not success."""
    require(report.get('hardware_executed') is True and report.get('execution_status_unknown') is False,
            'a real completed execution is required')
    require(not any(report.get(k) for k in ('synthetic_fixture', 'mock', 'simulated', 'offline_schema_test')),
            'synthetic fixtures cannot grant capabilities')
    require(report.get('A2_gate_extension') == a2.description(), 'audited A2 activity extension differs')
    for name, digest in PINS.items():
        require(sha(read_shared_bytes(ROOT/name)) == digest, 'qualification dependency changed: '+name)
    sources = report.get('source_sha256')
    require(isinstance(sources, dict) and sources, 'actual source pins required')
    for name, digest in sources.items():
        read_ref({'path': name, 'sha256': digest})
    required = {name: PINS[name] for name in ('tools/probe_mini_browser_first_preset.py',
                'tools/run_mini_v3_first_preset_a2.py', 'tools/mini_capture_persistence.py')}
    required.update(a2.bridge.FROZEN)
    required.update({'tools/run_mini_v3_editor.py': a2.BRIDGE_SHA,
                     'tools/validate_mini_webserial_v3_close.py': a2.CLOSE_VALIDATOR_SHA})
    require(all(sources.get(name) == digest for name, digest in required.items()), 'trial core source pins differ')
    for path in trial.desktop.APP.iterdir():
        if path.is_file():
            require(sources.get(path.relative_to(ROOT).as_posix()) == sha(path.read_bytes()), 'trial original app pin missing/different')
    if 'bootstrap_guard_extension' in report:
        from tools import run_mini_v3_first_preset_a2_v2 as bootstrap
        require(all(sources.get(name) == digest and sha((ROOT/name).read_bytes()) == digest
                    for name, digest in BOOTSTRAP_PINS.items()), 'bootstrap extension source pin differs')
        extension = report['bootstrap_guard_extension']
        require({k: v for k, v in extension.items() if k != 'observed_local_rejections'} == bootstrap.description(),
                'bootstrap extension changes more than the exact local BLE-key rejection')
        observed = [e for e in report['guard']['events'] if e.get('kind') == 'local_editor_policy_rejection'
                    and e.get('line') == 'BLE key']
        require(extension.get('observed_local_rejections') == observed
                and all(e.get('lines') == [bootstrap.LOCAL_REPLY] for e in observed)
                and all(w['line'] != 'BLE key' for w in report['guard']['wire']), 'local rejection differs or BLE key reached the wire')
        read_ref(bootstrap.FAILURE_REFERENCE)
    else:
        require(sources.get('tools/mini_browser_first_preset_guard.js') == PINS['tools/mini_browser_first_preset_guard.js'],
                'trial guard source pin differs')
    from tools import run_mini_v3_first_preset_ui_v3 as ui
    require(all(sources.get(name) == digest and sha((ROOT/name).read_bytes()) == digest
                for name, digest in UI_PINS.items()), 'reviewed UI node-preservation source pin differs')
    ui_extension = ui.validate_ui_copy()
    require(canonical_sha(ui_extension) == UI_EXTENSION_SHA
            and report.get('ui_compatibility_extension') == ui_extension,
            'trial did not use the exact reviewed original-help-node fix')
    require(all(sources.get((ui.NEW_APP/name).relative_to(ROOT).as_posix()) == digest
                for name, digest in ui_extension['served_files'].items()), 'served trial app source pins differ')
    a2.verify_dependencies()
    desktop, delegated = a2.bridge.modules('first-preset')
    with a2.bridge.evidence_io_adapter(desktop, delegated), a2.closure_adapter(delegated), ui.ui_adapter(delegated):
        prepared = delegated.prepare(**report['prepared']['inputs'])
    # Original FXT dictionaries use integer keys in memory; JSON report keys
    # are strings. Compare the actual publication representation, not Python's
    # non-JSON key types. No field/value is dropped or otherwise normalized.
    prepared = json.loads(json.dumps(prepared))
    require(prepared == report['prepared'], 'installation/browser context replay differs')
    require(report.get('desktop_close_observation') == prepared['context'].get('desktop_close_observation'),
            'prior desktop closure interpretation differs')
    extension = copy.deepcopy(report.get('evidence_io_extension'))
    require(isinstance(extension, dict), 'bounded evidence-file extension missing')
    for value in extension.get('exceptions', {}).values():
        count = value.pop('successful_verified_reads', None)
        require(type(count) is int and count > 0, 'historical trace was not verified by the bounded adapter')
    expected_extension = a2.bridge.ExactTraceReader(None).description()
    for value in expected_extension['exceptions'].values(): value.pop('successful_verified_reads')
    require(extension == expected_extension, 'evidence-file extension exceeds the two frozen exceptions')
    selection = json.loads(read_shared_bytes(local(report['selection_path'])))
    require(selection == report['selection'], 'retained chooser evidence differs')
    trial.selection.validate_selection(selection, browser_pid=report['browser_process_id'], origin=report['origin'],
        com=prepared['context']['com'], start=report['started_utc'], validated_at=report['finished_utc'])
    require(stamp(prepared['context']['closed_utc']) <= stamp(report['started_utc']) < stamp(report['finished_utc']),
            'trial does not follow the closed prior connection')
    return prepared, ui_extension


def validate_partial_saved_report(path=None, expected_sha256=None):
    """Attest only the real four-write prefix of stopped report04; no grant."""
    ref = {'path': local(path or PARTIAL_REF['path']).relative_to(ROOT).as_posix(),
           'sha256': expected_sha256 or PARTIAL_REF['sha256']}
    require(ref == PARTIAL_REF, 'only the reviewed immutable partial04 is accepted')
    report = json.loads(read_ref(ref))
    prepared, ui_extension = validate_report_provenance(report)
    summary = inspect_trial(report, read_ref(prepared['blob']), _partial=True)
    return {'schema': 1, 'kind': 'mini-retained-preset-saved-partial-validation',
            'verified_partial': True, 'original_trial_result': 'fail', 'reload_verified': False,
            'capabilities_granted': {}, 'report_ref': ref, 'prepared': prepared,
            'context': prepared['context'], 'plan': copy.deepcopy(report['plan']),
            'saved_snapshot': copy.deepcopy(report['saved']), 'summary': summary,
            'ui_compatibility_extension': ui_extension,
            'serial_port_closed': True, 'closed_utc': report['finished_utc'],
            'validator_sha256': sha(Path(__file__).read_bytes())}


def continuation_backend(report):
    """Select an explicit transcript version; never reinterpret old evidence."""
    kind = report.get('kind')
    if kind == 'mini-browser-saved-reload-continuation':
        from tools import probe_mini_browser_saved_reload as resume
        return resume, RESUME_PINS, JOINT_MODEL
    require(kind == 'mini-browser-saved-reload-continuation-v2', 'unknown continuation transcript version')
    from tools import probe_mini_browser_saved_reload_v2 as resume
    return resume, RESUME_V2_PINS, JOINT_MODEL_V2


def inspect_continuation(report, partial):
    """Replay the separate two-command session, preserving the failed prefix."""
    resume, _, model = continuation_backend(report)
    require(report.get('schema') == 1
            and report.get('result') == 'pass' and report.get('phase') == 'UI_saved_preset_reload_complete',
            'completed retained-preset continuation required')
    for key in ('UI_sequence_completed', 'retained_saved_reload_verified', 'serial_port_closed',
                'preset_intentionally_retained', 'capture_intentionally_retained', 'browser_process_stopped', 'local_server_stopped'):
        require(report.get(key) is True, 'continuation missing completion: '+key)
    for key in ('prior_save_reperformed', 'capture_write_performed', 'audio_quality_verified', 'power_cycle_verified',
                'held_recovery_verified', 'BLE_verified', 'firmware_write', 'profile_modified'):
        require(report.get(key) is False, 'unexpected continuation claim: '+key)
    if model == JOINT_MODEL_V2:
        require(report.get('automatic_retry') is True
                and report.get('automatic_retry_scope') == 'bootstrap PING empty timeouts only'
                and report.get('mutation_retry_performed') is False
                and report.get('query_retry_performed') is False,
                'v2 permits only the original bounded bootstrap PING repetition')
    else:
        require(report.get('automatic_retry') is False, 'v1 continuation cannot claim retries')
    require(not any(report.get(k) for k in ('error', 'cleanup_error', 'publication_error'))
            and report.get('general_capabilities_granted') == {}, 'failed or overbroad continuation')
    require(report.get('image_sha256') == IMAGE and report.get('transport') == 'usb-cdc'
            and report.get('plan') == partial['plan'], 'continuation image/transport/plan differs')
    require(report['prepared']['prior_partial'] == partial, 'continuation is not bound to the verified saved state')
    guard, plan = report['guard'], partial['plan']
    require(report.get('original_UI_reload_observation') == {
        'gain': plan['gain'], 'capture': plan['capture_slot'], 'scene': 0, 'preset': plan['slot'], 'fatal': None},
        'original UI did not observe the actual reloaded gain/capture/scene/preset')
    if model == JOINT_MODEL_V2:
        connection = resume.native_identity_proof(guard, partial['context']['pong'])
        require(connection == report.get('selection_proof'), 'native identity proof differs from actual events/bytes')
        raw = resume.verify_wire(guard, plan, expected_pong=partial['context']['pong'])
    else:
        connection = None
        raw = resume.verify_wire(guard, plan)
    require(raw == report.get('raw_trace_verification') and guard.get('live') is True
            and guard.get('appInstalled') is True and guard.get('pongMatched') is True
            and guard.get('portInfo') == {'vid': 0x3654, 'pid': 0x5155}
            and guard.get('rxBytes') == raw['raw_RX_byte_count'] and 0 < guard['rxBytes'] <= 2*1024*1024,
            'continuation native connection/raw extent differs')
    disconnect = report['disconnect']
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes') == 1 and not disconnect.get('closeError'), 'continuation port did not close')
    require([u.get('target') for u in guard['ui']] == ['Output', 'preset-row'], 'continuation UI targets differ')
    seqs = [r['seq'] for kind in ('events', 'ui', 'wire', 'rx', 'commands') for r in guard[kind]]
    if model == JOINT_MODEL_V2:
        seqs += [r[key] for r in guard['nativeWrites'] for key in ('seq', 'completed_seq')]
        seqs += [r['seq'] for kind in ('editorCompletions', 'replies') for r in guard[kind]]
    require(len(seqs) == len(set(seqs)) and all(type(s) is int and s > 0 for s in seqs), 'continuation chronology reused')
    require(len(guard['commands']) == len(guard['wire'])
            and len({c['id'] for c in guard['commands']}) == len(guard['commands'])
            and len({w['id'] for w in guard['wire']}) == len(guard['wire'])
            and all(c.get('completed') is True and c.get('wire_id') is not None for c in guard['commands']),
            'continuation has an unbound/unfinished exchange')
    lifecycle = [one_event(guard, name)['seq'] for name in
        ('experimental_guard_installed', 'serial_request_intent', 'serial_open_intent', 'serial_open_complete',
         'trial_plan', 'trial_complete', 'guard_stopped', 'serial_close_intent', 'serial_close_complete')]
    require(lifecycle == sorted(set(lifecycle)), 'continuation lifecycle differs')
    states = {}
    for name in ('before_activity', 'before', 'marker', 'reloaded'):
        item = report[name]
        require(set(item) == {'responses', 'state'} and set(item['responses']) == {*trial.READS, 'STAT'}, 'continuation snapshot incomplete')
        state = trial.parse_snapshot({key: item['responses'][key] for key in trial.READS})
        state['a2_stat'] = a2.parse_stat(item['responses']['STAT'])
        a2.checked_stat(state)
        require(state == item['state'], 'continuation parsed snapshot differs')
        resume.verify_saved(state, partial['saved_snapshot']['state'], plan['down'] if name == 'marker' else plan['gain'], plan)
        states[name] = state
    processing = resume.processing_progress(states['before_activity'], states['before'], partial['saved_snapshot']['state'], plan)
    require(processing == report['processing'], 'continuation A2 processing proof differs')
    acks = [e for e in guard['events'] if e.get('kind') == 'mutation_ack']
    require([e.get('epoch') for e in acks] == [1, 2] and guard.get('epoch') == 2, 'continuation epoch history differs')
    mutations = [w for w in guard['wire'] if w['origin'] != 'query']
    ranges = [('before_activity', lifecycle[3], lifecycle[4], 0), ('before', None, lifecycle[4], 0),
              ('marker', acks[0]['seq'], mutations[1]['seq'], 1), ('reloaded', acks[1]['seq'], lifecycle[5], 2)]
    cursor = 0; matches = {}
    for name, low, high, epoch in ranges:
        ordered = {k: report[name]['responses'][k] for k in (*trial.READS, 'STAT')}
        cursor, matches[name] = replay_responses(guard, ordered, low=cursor if low is None else low, high=high, epoch=epoch)
    used = [c for values in matches.values() for c in values]
    require(len(used) == len(set(used)), 'continuation response reused for multiple snapshots')
    pongs = [line for c in guard['commands'] if c['line'] == 'PING' for line in c['lines']]
    require(pongs and all(p == partial['context']['pong'] for p in pongs), 'continuation actual PONG differs')
    exercised = copy.deepcopy(partial['summary']['physically_exercised_requests'])
    exercised['PLOAD'] = [plan['load_request']]
    require('GAIN '+' '.join(map(str, plan['down'])) in exercised['GAIN'], 'marker differs from prior gain range')
    summary = {'evidence_model': model, 'transcript_consistent': True, 'hardware_execution_attested': False,
            'physically_exercised_requests': app.command_grants(exercised), 'session_count': 2,
            'partial_session': copy.deepcopy(partial['summary']), 'continuation_raw_trace': raw,
            'continuation_snapshot_command_ids': matches, 'continuation_processing': processing,
            'saved_state_sha256': partial['summary']['saved_state_sha256'],
            'reloaded_state_sha256': sha(encoded(states['reloaded'])),
            'one_reload_verified': True, 'scene_A_selected_by_PLOAD': True, 'plan': plan,
            'preset_intentionally_retained': True, 'capture_intentionally_retained': True,
            'preexisting_state_preserved': True, 'cold_power_retention_verified': False,
            'audio_quality_verified': False, 'every_value_physically_tested': False}
    if connection is not None:
        summary['continuation_connection_proof'] = connection
    return summary


def validate_continuation_selection(report, partial, model):
    """Keep actual UIA evidence separate from the v2 native identity proof."""
    selected = report.get('selection')
    path = local(report['selection_path']) if report.get('selection_path') else None
    if selected is None:
        require(model == JOINT_MODEL_V2 and (path is None or not path.exists()),
                'UIA evidence is missing or omitted from the report')
        return None
    require(path is not None and json.loads(read_shared_bytes(path)) == selected,
            'continuation chooser record differs')
    trial.selection.validate_selection(selected, browser_pid=report['browser_process_id'], origin=report['origin'],
        com=partial['context']['com'], start=report['started_utc'], validated_at=report['finished_utc'])
    return reference(path)


def validate_continuation_browser(report, report_ref):
    """Check the recorded process-local configuration without launching it."""
    from tools import mini_browser_windows as browser_windows
    arguments = report.get('browser_arguments')
    require(isinstance(arguments, list) and arguments and all(isinstance(x, str) for x in arguments),
            'actual browser argument list required')
    executable = Path(arguments[0])
    require(executable.is_absolute() and executable.name.lower() in ('chrome.exe', 'msedge.exe'),
            'recorded native browser executable differs')
    profile = local(report_ref['path']).parent/'isolated-profile'
    require(arguments == browser_windows.browser_arguments(executable, profile)
            and report.get('browser_configuration') == browser_windows.description(arguments)
            and report['browser_configuration']['platform'] == 'win32'
            and report['browser_configuration']['disabled_for_this_process'] is True,
            'recorded browser configuration differs from the process-local chooser adjustment')


def validate_joined_reports(partial_path, partial_sha256, resume_path, resume_sha256):
    """Two actual sessions, one retained preset; never convert partial04 to pass."""
    ref = {'path': local(resume_path).relative_to(ROOT).as_posix(), 'sha256': resume_sha256}
    report = json.loads(read_ref(ref))
    require(report.get('result') == 'pass' and report.get('hardware_executed') is True
            and report.get('execution_status_unknown') is False
            and not any(report.get(k) for k in ('synthetic_fixture', 'mock', 'simulated', 'offline_schema_test')),
            'a real successful continuation is required')
    resume, pins, model = continuation_backend(report)
    require(pins, 'continuation verifier/guard have not been frozen')
    for name, digest in pins.items():
        require(sha((ROOT/name).read_bytes()) == digest, 'continuation source differs: '+name)
    partial = validate_partial_saved_report(partial_path, partial_sha256)
    sources = report.get('source_sha256')
    require(isinstance(sources, dict) and all(sources.get(n) == d for n, d in pins.items())
            and sources.get(Path(__file__).relative_to(ROOT).as_posix()) == sha(Path(__file__).read_bytes()),
            'continuation source pins differ from the reviewed validators')
    required_sources = {name: PINS[name] for name in
                        ('tools/probe_mini_browser_first_preset.py', 'tools/run_mini_v3_first_preset_a2.py')}
    required_sources['tools/run_mini_v3_first_preset_ui_v3.py'] = UI_PINS['tools/run_mini_v3_first_preset_ui_v3.py']
    require(all(sources.get(name) == digest for name, digest in required_sources.items()), 'continuation parser/UI source pins missing')
    for name, digest in sources.items(): read_ref({'path': name, 'sha256': digest})
    prepared = json.loads(json.dumps(resume.prepare(partial=partial['report_ref'])))
    require(prepared == report['prepared'], 'continuation saved-state preparation differs')
    if model == JOINT_MODEL_V2:
        validate_continuation_browser(report, ref)
    validate_continuation_selection(report, partial, model)
    require(stamp(partial['closed_utc']) < stamp(report['started_utc']) < stamp(report['finished_utc']),
            'continuation does not follow the native close of partial04')
    summary = inspect_continuation(report, partial)
    # Reuse the same narrow qualification shape, with a distinct model and two
    # immutable report references. No synthetic six-write trace is produced.
    result = qualification_record(ref, report, partial['prepared'], partial['ui_compatibility_extension'], summary, model)
    result.update(saved_partial_report=partial['report_ref'], reloaded_report=ref,
                  reloaded_snapshot=copy.deepcopy(report['reloaded']),
                  sessions=[{'role': 'save', 'report': partial['report_ref'], 'original_result': 'fail', 'verified_UI_writes': 4},
                            {'role': 'reload', 'report': ref, 'original_result': 'pass', 'verified_UI_writes': 2}])
    validate_qualification(result)
    return result


def validate_trial_report(path, expected_sha256):
    """One-time full local provenance and native-transcript replay; never I/O."""
    ref = {'path': local(path).relative_to(ROOT).as_posix(), 'sha256': expected_sha256}
    report = json.loads(read_ref(ref))
    require(report.get('kind') == 'mini-browser-first-preset-v3-trial' and report.get('result') == 'pass'
            and report.get('phase') == 'UI_save_reload_complete', 'a completed successful UI trial is required')
    prepared, ui_extension = validate_report_provenance(report)
    summary = inspect_trial(report, read_ref(prepared['blob']))
    result = qualification_record(ref, report, prepared, ui_extension, summary, MODEL)
    result.update(reloaded_report=ref, reloaded_snapshot=copy.deepcopy(report['reloaded']),
                  sessions=[{'role': 'save-and-reload', 'report': ref, 'original_result': 'pass', 'verified_UI_writes': 6}])
    validate_qualification(result)
    return result


def qualification_record(ref, report, prepared, ui_extension, summary, model):
    refs = {**prepared['inputs'], 'base_manifest': {'path': BASE_MANIFEST, 'sha256': PINS[BASE_MANIFEST]},
            'blob': prepared['blob']}
    if model == JOINT_MODEL_V2:
        if report.get('selection') is not None:
            refs['selection'] = reference(report['selection_path'])
    else:
        refs['selection'] = reference(report['selection_path'])
    result = {'schema': 1, 'kind': 'mini-browser-retained-preset-qualification', 'evidence_model': model,
        'target': 'tank-mini', 'architecture': 'standalone-ultrarig-port', 'image_sha256': IMAGE,
        'firmware_version': VERSION, 'transport': 'usb-cdc', 'com': prepared['context']['com'],
        'pong': prepared['context']['pong'], 'hardware_executed': True, 'qualified': True,
        'editor_source_sha256': app.SOURCE_SHA, 'protocol_binding': copy.deepcopy(app.PROTOCOL_BINDING),
        'enabled_families': FAMILIES.copy(), 'physically_exercised_requests': summary['physically_exercised_requests'],
        'every_value_physically_tested': False, 'simulated_requests': {}, 'restoration_verified': False,
        'preset_intentionally_retained': True, 'capture_intentionally_retained': True,
        'one_reload_verified': True, 'two_reload_cycles_verified': False, 'temporary_slot_deleted': False,
        'power_cycle_verified': False, 'audio_quality_verified': False, 'BLE_verified': False,
        'serial_port_closed': True, 'image_hash_attested_by_PONG': False,
        'full_provenance_checked_at_build': True, 'trial': ref, 'summary': summary,
        'ui_compatibility_extension': copy.deepcopy(ui_extension),
        'refs': refs,
        'trial_source_sha256': copy.deepcopy(report['source_sha256']), 'validator_sha256': sha(Path(__file__).read_bytes()),
        'observed_utc': report['finished_utc']}
    if model == JOINT_MODEL_V2:
        result['connection_proof'] = copy.deepcopy(summary['continuation_connection_proof'])
    return result


def validate_qualification(value):
    """Validate the sealed, narrow claim without opening historical evidence."""
    require(not any(value.get(k) for k in ('synthetic_fixture', 'mock', 'simulated', 'offline_schema_test')),
            'synthetic qualification cannot grant capabilities')
    require(value.get('schema') == 1 and value.get('kind') == 'mini-browser-retained-preset-qualification'
            and value.get('evidence_model') in MODELS and value.get('target') == 'tank-mini'
            and value.get('image_sha256') == IMAGE and value.get('firmware_version') == VERSION
            and value.get('transport') == 'usb-cdc' and value.get('enabled_families') == FAMILIES,
            'qualification identity/model/subset differs')
    for key in ('hardware_executed', 'qualified', 'serial_port_closed', 'one_reload_verified',
                'preset_intentionally_retained', 'capture_intentionally_retained', 'full_provenance_checked_at_build'):
        require(value.get(key) is True, 'missing sealed claim: '+key)
    for key in ('every_value_physically_tested', 'restoration_verified', 'two_reload_cycles_verified',
                'temporary_slot_deleted', 'power_cycle_verified', 'audio_quality_verified', 'BLE_verified',
                'image_hash_attested_by_PONG'):
        require(value.get(key) is False, 'unsupported sealed claim: '+key)
    require(value.get('simulated_requests') == {} and value.get('protocol_binding') == app.PROTOCOL_BINDING
            and value.get('editor_source_sha256') == app.SOURCE_SHA, 'qualification protocol/source differs')
    requests = app.command_grants(value.get('physically_exercised_requests'))
    require(sorted(requests) == FAMILIES and requests == value['summary']['physically_exercised_requests'],
            'qualified families lack their representative requests')
    require(re.fullmatch(r'COM[1-9][0-9]{0,3}', str(value.get('com')))
            and str(value.get('pong')).startswith('PONG '+VERSION+' ')
            and not re.search(r'\bsafe\b', value['pong']), 'sealed normal-mode identity differs')
    require(value['validator_sha256'] == sha(Path(__file__).read_bytes()), 'qualification verifier changed')
    require(canonical_sha(value.get('ui_compatibility_extension')) == UI_EXTENSION_SHA,
            'qualification lacks the reviewed UI node-preservation version')
    require(value['summary'].get('evidence_model') == value['evidence_model']
            and value.get('reloaded_report') == value.get('trial'), 'qualification report/model linkage differs')
    snapshot = value.get('reloaded_snapshot')
    require(isinstance(snapshot, dict) and set(snapshot) == {'responses', 'state'}
            and sha(encoded(snapshot['state'])) == value['summary']['reloaded_state_sha256'], 'sealed reloaded snapshot differs')
    if value['evidence_model'] in (JOINT_MODEL, JOINT_MODEL_V2):
        require(value.get('saved_partial_report') == PARTIAL_REF and value['summary'].get('session_count') == 2
                and value.get('sessions') == [
                    {'role': 'save', 'report': PARTIAL_REF, 'original_result': 'fail', 'verified_UI_writes': 4},
                    {'role': 'reload', 'report': value['trial'], 'original_result': 'pass', 'verified_UI_writes': 2}],
                'two-session qualification must retain the failed save report separately')
    else:
        require(value.get('sessions') == [{'role': 'save-and-reload', 'report': value['trial'],
                                         'original_result': 'pass', 'verified_UI_writes': 6}], 'one-session qualification differs')
    if value['evidence_model'] == JOINT_MODEL_V2:
        proof = value.get('connection_proof')
        require(isinstance(proof, dict) and proof == value['summary'].get('continuation_connection_proof')
                and proof.get('kind') == 'native-open-and-exact-pong'
                and proof.get('port_info') == {'vid': 0x3654, 'pid': 0x5155}
                and proof.get('port_info_source') == 'SerialPort.getInfo()'
                and proof.get('exact_pong') == value['pong'] and proof.get('raw_RX_verified') is True
                and proof.get('UIA_selection_attested') is False and proof.get('selection_actor') == 'unattested'
                and proof.get('COM_name_attested') is False and proof.get('binary_hash_attested_by_device') is False,
                'sealed v2 native identity claim differs')
        bootstrap = proof.get('bootstrap', {})
        require(bootstrap.get('maximum_attempts') == 5
                and type(bootstrap.get('attempt_count')) is int and 1 <= bootstrap['attempt_count'] <= 5
                and bootstrap.get('empty_timeout_count') == bootstrap['attempt_count'] - 1
                and len(bootstrap.get('attempts', [])) == bootstrap['attempt_count'],
                'sealed bootstrap extent differs')
    return value


def family_metadata(qualification):
    return {'supported_by_protocol': FAMILIES.copy(), 'enabled_families': FAMILIES.copy(),
            'physically_exercised_requests': copy.deepcopy(qualification['physically_exercised_requests']),
            'every_value_physically_tested': False, 'protocol_binding': copy.deepcopy(app.PROTOCOL_BINDING),
            'image_hash_attested_by_device': False, 'evidence_model': qualification['evidence_model'],
            'one_reload_verified': True, 'preset_intentionally_retained': True,
            'power_cycle_verified': False}


@contextmanager
def family_adapter(qualification, proof_ref):
    """Extend only the new model in memory; frozen builder/policy stay intact."""
    validate_qualification(qualification)
    original = app.load_family_validation
    def load(spec, caps):
        if spec.get('family_evidence_model') not in MODELS:
            return original(spec, caps)
        require(spec.get('family_capabilities') == {'usb-cdc': FAMILIES}
                and spec.get('family_validation') == {'usb-cdc': [proof_ref]}
                and spec.get('hardware_verified') is True and caps == {'identity': True, 'read': True, 'write': False, 'panel': False}
                and not spec.get('command_capabilities') and not spec.get('write_validation')
                and spec.get('image_sha256') == IMAGE and spec.get('firmware_version') == VERSION
                and spec.get('family_evidence_model') == qualification['evidence_model'],
                'new evidence model permits only the four qualified USB families')
        require(json.loads(read_ref(proof_ref)) == qualification, 'sealed proof changed during build')
        return {'usb-cdc': FAMILIES.copy()}, {'usb-cdc': [copy.deepcopy(proof_ref)]}, {'usb-cdc': family_metadata(qualification)}
    app.load_family_validation = load
    try:
        yield
    finally:
        app.load_family_validation = original


def build_qualified_bundle(report_path, sha256, output_dir, *, partial_report_path=None, partial_sha256=None):
    require(bool(partial_report_path) == bool(partial_sha256), 'partial report requires its explicit SHA-256')
    qualification = (validate_joined_reports(partial_report_path, partial_sha256, report_path, sha256)
                     if partial_report_path else validate_trial_report(report_path, sha256))
    output = local(output_dir, within=ROOT/'build')
    require(not output.exists(), 'new bundle directory required; existing artifacts are never overwritten')
    output.mkdir(parents=True)
    proof_path = output/'qualification.json'; proof_path.write_bytes(encoded(qualification))
    proof_ref = reference(proof_path)
    spec = json.loads(read_ref({'path': BASE_MANIFEST, 'sha256': PINS[BASE_MANIFEST]}))
    spec.update(hardware_verified=True, family_evidence_model=qualification['evidence_model'],
                capabilities={'identity': True, 'read': True, 'write': False, 'panel': False},
                command_capabilities={}, family_capabilities={'usb-cdc': FAMILIES.copy()},
                family_validation={'usb-cdc': [proof_ref]},
                qualification_scope='Observed v3 boot/read/A2 processing and one original-editor USB gain/save/reload trial',
                remaining_gates=['Other mutation families, BLE/Android, physical panel, cold-power retention and acoustic quality remain separate qualifications.'])
    spec.pop('write_validation', None); spec.pop('command_validation', None)
    manifest = output/'firmware-manifest.json'; manifest.write_bytes(encoded(spec))
    with family_adapter(qualification, proof_ref):
        built = app.build(output/'app', manifest, output/'editor-report.json')
    # The original builder and policy remain frozen. Apply exactly the same
    # one-file UI fix that was exercised by this report, only in the new output.
    ui_path = output/'app/web/mini-ui.js'
    require(sha(ui_path.read_bytes()) == PINS['app/mini/mini-ui.js'], 'unexpected base UI before overlay')
    ui_bytes = (ROOT/'app/mini/mini-ui-v2.js').read_bytes()
    require(sha(ui_bytes) == UI_PINS['app/mini/mini-ui-v2.js'], 'qualified UI overlay changed')
    ui_path.write_bytes(ui_bytes)
    built['qualified_bundle_extension'] = {'evidence_model': qualification['evidence_model'], 'qualification': proof_ref,
        'UI_source': {'path': 'app/mini/mini-ui-v2.js', 'sha256': UI_PINS['app/mini/mini-ui-v2.js']},
        'UI_before_sha256': PINS['app/mini/mini-ui.js'], 'changed_output_files': ['web/mini-ui.js'],
        'original_command_policy_changed': False, 'frozen_sources_modified': False}
    built['implementation_files'].update(UI_PINS)
    built['implementation_files'][Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__).read_bytes())
    built['files'] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted((output/'app').rglob('*')) if p.is_file()}
    (output/'editor-report.json').write_bytes(encoded(built))
    metadata = {'schema': 1, 'kind': 'mini-qualified-editor-bundle', 'evidence_model': qualification['evidence_model'],
        'image_sha256': IMAGE, 'com': qualification['com'], 'pong': qualification['pong'],
        'app_directory': (output/'app/web').relative_to(ROOT).as_posix(), 'profile': built['profile'],
        'manifest': reference(manifest), 'qualification': proof_ref,
        'qualification_verifier_sha256': sha(Path(__file__).read_bytes()),
        'runtime_validation': 'local sealed files only; full historical evidence replay was performed once at build',
        'files': {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()}}
    data = encoded(metadata)
    (output/'bundle.json').write_bytes(data)
    (output/'bundle.sha256').write_text(sha(data)+'\n', encoding='ascii')
    return validate_bundle(output)


def validate_bundle(output_dir):
    """Lightweight normal-launch integrity check; no historical files or I/O.

    A hash seal detects local changes. It is not a cryptographic signature from
    hardware or an independent authority; the build's reviewed evidence is the
    source of the narrow qualification claim.
    """
    output = local(output_dir, within=ROOT/'build')
    raw = (output/'bundle.json').read_bytes()
    require(len(raw) < 2*1024*1024 and (output/'bundle.sha256').read_text('ascii') == sha(raw)+'\n', 'bundle seal differs')
    metadata = json.loads(raw)
    require(metadata.get('schema') == 1 and metadata.get('kind') == 'mini-qualified-editor-bundle'
            and metadata.get('evidence_model') in MODELS and metadata.get('image_sha256') == IMAGE
            and metadata.get('qualification_verifier_sha256') == sha(Path(__file__).read_bytes()), 'bundle identity/verifier differs')
    files = metadata.get('files')
    require(isinstance(files, dict) and 8 <= len(files) <= 32, 'bounded bundle file manifest required')
    actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    require(actual == set(files) | {'bundle.json', 'bundle.sha256'}, 'bundle file inventory changed')
    for name, digest in files.items():
        path = local(output/name, within=output)
        require(path.relative_to(output).as_posix() == name and re.fullmatch('[a-f0-9]{64}', str(digest))
                and path.stat().st_size <= 8*1024*1024 and sha(path.read_bytes()) == digest, 'bundle file changed: '+name)
    def bundled(ref):
        path = local(ROOT/ref['path'], within=output)
        require(files.get(path.relative_to(output).as_posix()) == ref['sha256'], 'bundle reference is not sealed')
        return json.loads(path.read_bytes())
    qualification = validate_qualification(bundled(metadata['qualification']))
    spec = bundled(metadata['manifest'])
    profile = metadata['profile']
    require(spec.get('family_evidence_model') == metadata['evidence_model'] == qualification['evidence_model']
            and spec.get('image_sha256') == IMAGE
            and spec.get('firmware_version') == VERSION and spec.get('hardware_verified') is True,
            'manifest does not match the qualified build')
    for value in (spec, profile):
        require(value.get('image_sha256') == IMAGE and value.get('firmware_version') == VERSION
                and value.get('hardware_verified') is True
                and value.get('capabilities') == {'identity': True, 'read': True, 'write': False, 'panel': False}
                and value.get('family_capabilities') == {'usb-cdc': FAMILIES}
                and value.get('family_validation') == {'usb-cdc': [metadata['qualification']]}
                and not value.get('command_capabilities') and not value.get('write_validation'),
                'runtime profile expands beyond the four qualified USB families')
    require(profile.get('family_qualification') == {'usb-cdc': family_metadata(qualification)}, 'family qualification differs')
    web = local(ROOT/metadata['app_directory'], within=output)
    require(web == output/'app/web' and files.get('app/web/mini-profile.js') == PINS['app/mini/mini-profile.js']
            and files.get('app/web/mini-ui.js') == UI_PINS['app/mini/mini-ui-v2.js'], 'original policy/qualified UI version changed')
    html = (web/'tankmini.html').read_text('utf-8')
    config = json.dumps(profile, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    require('<script>globalThis.HYPERRIG_MINI_BUILD='+config+';</script>' in html,
            'HTML does not contain the exact qualified runtime profile')
    require(metadata['com'] == qualification['com'] and metadata['pong'] == qualification['pong'], 'bundle connection context differs')
    return {'app_directory': metadata['app_directory'], 'profile': copy.deepcopy(profile),
            'manifest': metadata['manifest'], 'image_sha256': IMAGE, 'com': metadata['com'], 'pong': metadata['pong'],
            'qualification': qualification, 'refs': {'bundle': {'path': (output/'bundle.json').relative_to(ROOT).as_posix(), 'sha256': sha(raw)},
                'qualification': metadata['qualification'], 'manifest': metadata['manifest']},
            'historical_evidence_replayed_on_launch': False, 'device_io': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path); parser.add_argument('--report-sha256')
    parser.add_argument('--build', type=Path); parser.add_argument('--check-bundle', type=Path)
    parser.add_argument('--partial-report', type=Path); parser.add_argument('--partial-report-sha256')
    args = parser.parse_args(argv)
    if args.check_bundle:
        result = validate_bundle(args.check_bundle)
    elif args.report:
        require(args.report_sha256, 'explicit completed report SHA-256 required')
        require(bool(args.partial_report) == bool(args.partial_report_sha256), 'partial report requires explicit SHA-256')
        if args.build:
            result = build_qualified_bundle(args.report, args.report_sha256, args.build,
                partial_report_path=args.partial_report, partial_sha256=args.partial_report_sha256)
        elif args.partial_report:
            result = validate_joined_reports(args.partial_report, args.partial_report_sha256, args.report, args.report_sha256)
        else:
            result = validate_trial_report(args.report, args.report_sha256)
    else:
        require(not any((args.build, args.report_sha256, args.partial_report, args.partial_report_sha256)), 'build requires a real completed report')
        result = {'device_io': False, 'inputs_read': False, 'capabilities_granted': {}, 'evidence_model': MODEL}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
