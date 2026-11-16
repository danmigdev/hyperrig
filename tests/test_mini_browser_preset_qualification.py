"""Explicit synthetic transcript tests. No physical result or grant is emitted."""
import base64
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from tools import qualify_mini_browser_preset as q


def answers(*, gain=(0, 0), preset=-1, capture_slot=0, scene=-1):
    return {'GAIN': [f'GAIN in={gain[0]} out={gain[1]} dB'],
        'LVL': [f'LVL in=-1440 out=-1440 ci=0 co=0 m=2 g={gain[0]}/{gain[1]} p={preset}'],
        'FXS': ['FXS amp=1 on=1', 'FXS cpu=100/1000 ticks (10%) mem_fx=0 B',
                'FXS eng=0 posts=0 takes=0 canc=0 lat=0/0 run=0', 'FXS peak=100 ticks skipped=0'],
        'PLIST': ([f"PRE {preset} 0 {capture_slot} -1 'Preset 1A' t=- s=1 amp=1"] if preset >= 0 else []) + [f'PLIST end current={preset}'],
        'SNAPS': [f"SNAPS {'1000' if scene == 0 else '0000'} current={scene}"],
        'CLIST': ([f"CAP {capture_slot} 4892 'A2' trim=0.0"] if capture_slot >= 0 else []) + [f'CLIST end current={capture_slot} slots=15'],
        'ILIST': ['ILIST end current=-1 slots=15'], 'MODEL': [q.trial.capture.MODEL_LINE],
        'CLKSTATE': ['CLKSTATE mhz=360 safe=0'],
        'AMPEQ': ['AMPEQ volume=0 bass=0 mid=0 treble=0 presence=0 drive=0'],
        'BPM': ['BPM 120.0'], 'PCOLOR': [f'PCOLOR none preset={preset}'],
        'STW': ['STW w=0 cur=0 live=0 cpu=0/1 deg=0'], 'SNAPNAME': ['SNAPNAME end']}


def stat(nproc, gains):
    return ['AUD mode=2 in=100 out=100 blk=10 ovr=0 und=0 full=0 pk_in=1 pk_out=1 iis=1/1 err=0',
        'DSP rc=0 L=23 C=3 rf=1 fast=1 hw_ok=1 mism=0 hw_to=0 c1_ok=1 c1_to=0 jobs=1 split=0/0',
        f'T nproc={nproc} last=1 max=1 avg=1 ticks; arena=1 tick_ms=360000/360000',
        'STG win=1 in=1/1 pre=1/1 eng=1/1 post=1/1 out=1/1 blk=1/1 lat=1/1 isr=1/1',
        'W espera_c0=0 max=0 split=0', 'RS n=0 veces=0 lat/eng/blk us:',
        f'NIVEL pk_in=-90.0 pk_out=-90.0 dBFS clip_in=0 clip_out=0 gain={gains[0]}/{gains[1]} dB lim_n=0 clip_eng=0']


def synthetic_trial(*, existing_capture=False):
    """Construct raw exchanges, not a declaration that any device was used."""
    blob = q.trial.BLOB.read_bytes()
    guard = dict(live=True, appInstalled=True, pongMatched=True, portInfo={'vid': 0x3654, 'pid': 0x5155},
        fatal=None, phase='complete', mutations=6, requests=1, opens=1, closes=1,
        closeError=None, stopped=True, captureVerified=True, captureMutations=0 if existing_capture else 1,
        epoch=0, events=[], ui=[], wire=[], commands=[], rx=[])
    seq = 0
    def tick():
        nonlocal seq
        seq += 1
        return seq
    def event(kind, **fields):
        value = dict(seq=tick(), kind=kind, **fields); guard['events'].append(value); return value
    def exchange(line, lines, origin='query'):
        cid = len(guard['commands']); wid = len(guard['wire'])
        guard['wire'].append(dict(id=wid, command_id=cid, line=line, origin=origin,
            hex=(line+'\n').encode().hex(), seq=tick(), completed=True))
        guard['rx'].append(dict(seq=tick(), hex=('\r\n'.join(lines)+'\r\n').encode().hex()))
        guard['commands'].append(dict(id=cid, wire_id=wid, line=line, lines=lines,
                                      seq=tick(), epoch=guard['epoch'], completed=True))
    report = dict(schema=1, kind='mini-browser-first-preset-v3-trial', result='pass', phase='UI_save_reload_complete',
        synthetic_fixture=True, hardware_executed=False, execution_status_unknown=False,
        image_sha256=q.IMAGE, transport='usb-cdc', UI_sequence_completed=True, ui_roundtrip_verified=True,
        save_reload_verified=True, serial_port_closed=True, preset_intentionally_retained=True,
        capture_intentionally_retained=True, browser_process_stopped=True, local_server_stopped=True,
        audio_quality_verified=False, power_cycle_verified=False, held_recovery_verified=False,
        BLE_verified=False, firmware_write=False, automatic_retry=False, profile_modified=False,
        general_capabilities_granted={}, disconnect=dict(native_close_verified=True, open=False, closes=1, closeError=None),
        prepared={'context': {'pong': 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'}})
    event('experimental_guard_installed'); event('serial_request_intent')
    event('serial_open_intent'); event('serial_open_complete')
    exchange('PING', [report['prepared']['context']['pong']])
    nproc = 10
    def snapshot(name, **params):
        nonlocal nproc
        nproc += 10
        response = answers(**params)
        state = q.trial.parse_snapshot(response)
        response['STAT'] = stat(nproc, state['gain'])
        state['a2_stat'] = q.a2.parse_stat(response['STAT'])
        report[name] = {'responses': response, 'state': state}
        for line, lines in response.items(): exchange(line, lines)
    snapshot('initial_activity_before', capture_slot=0 if existing_capture else -1)
    snapshot('initial', capture_slot=0 if existing_capture else -1)
    report['initial_processing'] = q.a2.progress(q.trial, report['initial_activity_before']['state'], report['initial']['state'])
    cp = q.trial.capture.plan_capture(report['initial']['responses'], blob)
    report['capture_plan'] = cp
    requests = ([cp['request']] if cp['request'] else [])+[cp['header_request'], *cp['chunk_requests']]
    event('capture_plan', plan={'slot': cp['slot'], 'requests': requests})
    cap = {cp['header_request']: [f"CREAD 0 len=4892 crc={zlib.crc32(blob):08x} id={q.trial.capture.A2_CONTENT_ID:08x} aux=0 fs=0 name='A2'"]}
    if cp['request']: cap[cp['request']] = ["CSAVE ok 0 'A2' 4892 B"]
    for offset, line in zip(range(0, len(blob), 96), cp['chunk_requests']):
        chunk = blob[offset:offset+96]
        cap[line] = [f'CREAD 0 {offset} {len(chunk)} {zlib.crc32(chunk):08x} {base64.b64encode(chunk).decode()}']
    for line in requests:
        exchange(line, cap[line], 'diagnostic capture persistence' if line.startswith('CSAVE') else 'diagnostic capture byte read')
    for line in ('MODEL', 'CLIST'):
        cap[line] = answers()[line]; exchange(line, cap[line])
    report['capture_verification'] = q.trial.capture.verify_capture(cp, cap, blob)
    guard['epoch'] = 1; event('capture_verified_by_host')
    snapshot('before_activity'); snapshot('before')
    report['UI_processing'] = q.a2.progress(q.trial, report['before_activity']['state'], report['before']['state'])
    plan = q.trial.make_plan(report['before']['state'], 'Preset 1A'); report['plan'] = plan
    event('trial_plan', plan=plan)
    def mutation(index, line, reply, kind, key, origin):
        if index != 3:
            ui = dict(seq=tick(), trusted=True, kind=kind,
                      target='empty-row Save' if kind == 'click' else 'preset-row' if key == 'Enter' else 'Output')
            if key is not None: ui['key'] = key
            guard['ui'].append(ui)
        exchange(line, [reply], origin)
        guard['epoch'] += 1
        event('mutation_ack', line=line, lines=[reply], epoch=guard['epoch'])
    mutation(0, 'GAIN 0 -1', 'GAIN in=0 out=-1 dB', 'keydown', 'ArrowDown', 'Output ArrowDown')
    snapshot('down1', gain=(0, -1))
    mutation(1, 'GAIN 0 0', 'GAIN in=0 out=0 dB', 'keydown', 'ArrowUp', 'Output ArrowUp')
    snapshot('up')
    mutation(2, 'PSAVE 0 Preset 1A', "PSAVE ok 0 'Preset 1A' 0 blocks capture=0 ir=-1", 'click', None, 'Original empty-row Save')
    mutation(3, 'SNAPSAVE 0', 'SNAPSAVE ok 0 preset=0', None, None, 'Original sceneAOnSave')
    snapshot('saved', preset=0, scene=0)
    mutation(4, 'GAIN 0 -1', 'GAIN in=0 out=-1 dB', 'keydown', 'ArrowDown', 'Output persistence marker ArrowDown')
    snapshot('marker', gain=(0, -1), preset=0, scene=0)
    mutation(5, 'PLOAD 0', "PLOAD ok 0 'Preset 1A' missing=0 capture=0 ir=-1 ms=2", 'keydown', 'Enter', 'Original preset-row Enter')
    snapshot('reloaded', preset=0, scene=0)
    event('trial_complete'); event('guard_stopped'); event('serial_close_intent'); event('serial_close_complete')
    guard['rxBytes'] = sum(len(bytes.fromhex(r['hex'])) for r in guard['rx'])
    report['guard'] = guard; report['raw_trace_verification'] = q.trial.verify_wire(guard)
    return report, blob


def synthetic_continuation(*, v2=False, empty_timeouts=0):
    """Two distinct labelled sessions, never a repaired/padded hardware report."""
    first, blob = synthetic_trial(existing_capture=True)
    g = first['guard']; marker_ui = g['ui'][3]['seq']
    for key in ('events', 'ui', 'wire', 'commands', 'rx'):
        g[key] = [r for r in g[key] if r['seq'] < marker_ui]
    seq = max(r['seq'] for key in ('events', 'ui', 'wire', 'commands', 'rx') for r in g[key])
    for kind in ('guard_stopped', 'serial_close_intent', 'serial_close_complete'):
        seq += 1; g['events'].append({'kind': kind, 'seq': seq})
    g.update(fatal='Actual focused Output knob and S.gain differ', phase='scene_ack', mutations=4, epoch=5,
             rxBytes=sum(len(bytes.fromhex(r['hex'])) for r in g['rx']))
    first.update(result='fail', phase='persistence_marker_intent', failed_phase='persistence_marker_intent',
        error='NotAllowedError: Actual focused Output knob and S.gain differ',
        ui_roundtrip_verified=False, save_reload_verified=False)
    for key in ('marker', 'reloaded', 'UI_sequence_completed', 'preset_intentionally_retained',
                'capture_intentionally_retained', 'raw_trace_verification'): first.pop(key)
    partial = {'synthetic_fixture': True, 'context': first['prepared']['context'], 'plan': first['plan'],
               'saved_snapshot': first['saved'], 'summary': q.inspect_trial(first, blob, _partial=True)}
    if v2:
        from tools import probe_mini_browser_saved_reload_v2 as resume
    else:
        from tools import probe_mini_browser_saved_reload as resume
    guard = dict(live=True, appInstalled=True, pongMatched=True, portInfo={'vid': 0x3654, 'pid': 0x5155},
        fatal=None, phase='complete', mutations=2, requests=1, opens=1, closes=1, closeError=None,
        stopped=True, epoch=0, events=[], ui=[], wire=[], commands=[], rx=[])
    if v2:
        guard.update(nativeWrites=[], nativeErrors=[], replies=[], editorCompletions=[], bootstrap_attempts=[])
    seq = 0
    def tick():
        nonlocal seq
        seq += 1; return seq
    def event(kind, **fields): guard['events'].append(dict(seq=tick(), kind=kind, **fields))
    def exchange(line, lines, origin='query'):
        cid = len(guard['commands']); wid = len(guard['wire'])
        start_seq = seq
        start_bytes = sum(len(bytes.fromhex(r['hex'])) for r in guard['rx'])
        start_replies = len(guard.get('replies', []))
        wire = dict(id=wid, command_id=cid, line=line, origin=origin,
                    hex=(line+'\n').encode().hex(), seq=tick(), completed=True)
        guard['wire'].append(wire)
        if v2:
            native = dict(id=len(guard['nativeWrites']), wire_id=wid, hex=wire['hex'],
                          bytes=len(line)+1, seq=tick(), completed=True, completed_seq=tick())
            wire['native_write_id'] = native['id']; guard['nativeWrites'].append(native)
        if lines:
            guard['rx'].append(dict(seq=tick(), hex=('\r\n'.join(lines)+'\r\n').encode().hex()))
        if v2:
            for value in lines: guard['replies'].append(dict(seq=tick(), line=value))
            completion = dict(id=len(guard['editorCompletions']), command_id=cid, line=line,
                              lines=lines, timed_out=not lines, seq=tick())
            guard['editorCompletions'].append(completion)
        command = dict(id=cid, wire_id=wid, line=line, lines=lines,
                       seq=tick(), epoch=guard['epoch'], completed=True)
        guard['commands'].append(command)
        if v2 and line == 'PING':
            index = len(guard['bootstrap_attempts']) + 1
            attempt = dict(index=index, command_id=cid, wire_id=wid, native_write_id=native['id'],
                editor_completion_id=completion['id'], start_seq=start_seq, start_rx_bytes=start_bytes,
                start_reply_count=start_replies, timeout_ms=700, completion_seq=command['seq'],
                end_rx_bytes=sum(len(bytes.fromhex(r['hex'])) for r in guard['rx']),
                end_reply_count=len(guard['replies']), status='pong' if lines else 'empty_timeout',
                repeat_permitted=not lines and index < 5)
            guard['bootstrap_attempts'].append(attempt)
            event('bootstrap_pong' if lines else 'bootstrap_empty_timeout', attempt=copy.deepcopy(attempt))
    report = dict(schema=1, kind='mini-browser-saved-reload-continuation', result='pass',
        phase='UI_saved_preset_reload_complete', image_sha256=q.IMAGE, transport='usb-cdc',
        synthetic_fixture=True, hardware_executed=False, execution_status_unknown=False,
        UI_sequence_completed=True, retained_saved_reload_verified=True, serial_port_closed=True,
        preset_intentionally_retained=True, capture_intentionally_retained=True,
        browser_process_stopped=True, local_server_stopped=True, prior_save_reperformed=False,
        capture_write_performed=False, audio_quality_verified=False, power_cycle_verified=False,
        held_recovery_verified=False, BLE_verified=False, firmware_write=False, automatic_retry=False,
        profile_modified=False, general_capabilities_granted={}, plan=copy.deepcopy(partial['plan']),
        prepared={'prior_partial': partial},
        disconnect=dict(native_close_verified=True, open=False, closes=1, closeError=None))
    if v2:
        report.update(kind='mini-browser-saved-reload-continuation-v2', automatic_retry=True,
            automatic_retry_scope='bootstrap PING empty timeouts only',
            mutation_retry_performed=False, query_retry_performed=False)
    for kind in ('experimental_guard_installed', 'serial_request_intent', 'serial_open_intent', 'serial_open_complete'):
        if v2 and kind == 'serial_open_intent':
            event('native_port_info', info=guard['portInfo'].copy())
            event('native_port_info', info=guard['portInfo'].copy())
        event(kind)
    if v2:
        for _ in range(empty_timeouts): exchange('PING', [])
    exchange('PING', [partial['context']['pong']])
    nproc = 1000
    def snapshot(name, gain):
        nonlocal nproc
        nproc += 10; response = answers(gain=gain, preset=0, capture_slot=0, scene=0)
        state = q.trial.parse_snapshot(response); response['STAT'] = stat(nproc, gain)
        state['a2_stat'] = q.a2.parse_stat(response['STAT'])
        report[name] = {'responses': response, 'state': state}
        for line, lines in response.items(): exchange(line, lines)
    snapshot('before_activity', (0, 0)); snapshot('before', (0, 0))
    report['processing'] = resume.processing_progress(report['before_activity']['state'], report['before']['state'],
                                                     partial['saved_snapshot']['state'], partial['plan'])
    event('trial_plan', plan=partial['plan'])
    for key, line, response, origin, name, gains in (
        ('ArrowDown', 'GAIN 0 -1', 'GAIN in=0 out=-1 dB', 'Output persistence marker ArrowDown', 'marker', (0, -1)),
        ('Enter', 'PLOAD 0', "PLOAD ok 0 'Preset 1A' missing=0 capture=0 ir=-1 ms=2", 'Original preset-row Enter', 'reloaded', (0, 0))):
        guard['ui'].append(dict(seq=tick(), kind='keydown', key=key, trusted=True, target='Output' if key == 'ArrowDown' else 'preset-row'))
        exchange(line, [response], origin); guard['epoch'] += 1
        event('mutation_ack', line=line, lines=[response], epoch=guard['epoch'])
        snapshot(name, gains)
    for kind in ('trial_complete', 'guard_stopped', 'serial_close_intent', 'serial_close_complete'): event(kind)
    guard['rxBytes'] = sum(len(bytes.fromhex(r['hex'])) for r in guard['rx'])
    report['guard'] = guard; report['raw_trace_verification'] = resume.verify_wire(guard, partial['plan'])
    if v2:
        report['selection_proof'] = resume.native_identity_proof(guard, partial['context']['pong'])
    report['original_UI_reload_observation'] = {'gain': [0, 0], 'capture': 0, 'scene': 0, 'preset': 0, 'fatal': None}
    return report, partial


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.report, self.blob = synthetic_trial()

    def test_default_performs_no_file_read_or_hardware(self):
        with patch.object(q, 'validate_trial_report', side_effect=AssertionError('read')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(q.main([]), 0)
        self.assertEqual(json.loads(out.getvalue())['capabilities_granted'], {})

    def test_complete_synthetic_transcript_checks_consistency_without_grant(self):
        got = q.inspect_trial(self.report, self.blob)
        self.assertTrue(got['transcript_consistent'] and got['one_reload_verified'])
        self.assertFalse(got['hardware_execution_attested'] or got['cold_power_retention_verified'])
        self.assertEqual(sorted(got['physically_exercised_requests']), q.FAMILIES)
        self.assertFalse(got['A2_UI_progress']['core1_job_progress_observed'])
        self.assertGreater(got['A2_UI_progress']['A2_nproc_delta'], 0)

    def test_existing_current_capture_is_read_fully_without_any_csave(self):
        report, blob = synthetic_trial(existing_capture=True)
        got = q.inspect_trial(report, blob)
        self.assertTrue(got['one_reload_verified'])
        self.assertIsNone(report['capture_plan']['request'])
        self.assertEqual(report['guard']['captureMutations'], 0)
        self.assertFalse(any(w['line'].startswith('CSAVE') for w in report['guard']['wire']))
        self.assertEqual(len(report['capture_plan']['chunk_requests']), 51)

    def test_synthetic_file_is_rejected_before_any_provenance_replay(self):
        with tempfile.TemporaryDirectory(dir=q.ROOT/'build') as tmp:
            path = Path(tmp)/'synthetic.json'; path.write_bytes(q.encoded(self.report))
            with patch.object(q.a2.bridge, 'modules', side_effect=AssertionError('provenance')), self.assertRaisesRegex(ValueError, 'real completed'):
                q.validate_trial_report(path, q.sha(path.read_bytes()))
            fake = copy.deepcopy(self.report); fake['hardware_executed'] = True
            path.write_bytes(q.encoded(fake))
            with self.assertRaisesRegex(ValueError, 'synthetic'):
                q.build_qualified_bundle(path, q.sha(path.read_bytes()), Path(tmp)/'must-not-exist')
            self.assertFalse((Path(tmp)/'must-not-exist').exists())

    def test_failed_real_ping_trial_cannot_qualify_or_start_provenance_replay(self):
        path = q.ROOT/'build/mini-first-preset-ui-03/report.json'
        if not path.is_file(): self.skipTest('private closed hardware evidence is not distributed')
        digest = '1473acc819228ee5f980e13b8f3df2d0fe94ac24dea91c0f93cf9511efb73527'
        self.assertEqual(q.sha(path.read_bytes()), digest)
        with patch.object(q.a2.bridge, 'modules', side_effect=AssertionError('unnecessary replay')):
            with self.assertRaisesRegex(ValueError, 'completed successful'):
                q.validate_trial_report(path, digest)

    def test_real_partial04_proves_only_save_and_preserves_failure(self):
        path = q.ROOT/q.PARTIAL_REF['path']
        if not path.is_file(): self.skipTest('private closed hardware evidence is not distributed')
        raw = path.read_bytes(); self.assertEqual(q.sha(raw), q.PARTIAL_REF['sha256'])
        value = q.validate_partial_saved_report()
        self.assertTrue(value['verified_partial'])
        self.assertEqual(value['original_trial_result'], 'fail')
        self.assertFalse(value['reload_verified'])
        self.assertEqual(value['capabilities_granted'], {})
        self.assertEqual(sorted(value['summary']['physically_exercised_requests']), ['GAIN', 'PSAVE', 'SNAPSAVE'])
        self.assertEqual(path.read_bytes(), raw)
        report = json.loads(raw)
        for key, change in [('marker', {}), ('save_reload_verified', True), ('cleanup_error', 'lost close')]:
            altered = copy.deepcopy(report); altered[key] = change
            with self.subTest(key=key), self.assertRaises(ValueError): q.inspect_trial(altered, self.blob, _partial=True)
        altered = copy.deepcopy(report); altered['guard']['fatal'] = 'other failure'
        with self.assertRaises(ValueError): q.inspect_trial(altered, self.blob, _partial=True)
        with self.assertRaises(ValueError): q.validate_trial_report(path, q.PARTIAL_REF['sha256'])

    def test_wrong_or_misleading_completion_claims_fail(self):
        for key, value in [('result', 'fail'), ('power_cycle_verified', True), ('audio_quality_verified', True),
                           ('serial_port_closed', False), ('preset_intentionally_retained', False),
                           ('image_sha256', '0'*64), ('transport', 'ble-nus')]:
            bad = copy.deepcopy(self.report); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): q.inspect_trial(bad, self.blob)

    def test_matching_raw_data_required_for_every_completed_response(self):
        bad = copy.deepcopy(self.report)
        target = next(w for w in bad['guard']['wire'] if w['line'] == 'PSAVE 0 Preset 1A')
        native = next(r for r in bad['guard']['rx'] if r['seq'] == target['seq']+1)
        native['hex'] = b'PSAVE error\r\n'.hex()
        with self.assertRaisesRegex(ValueError, 'native RX'): q.inspect_trial(bad, self.blob)

    def test_snapshot_cannot_reuse_same_state_from_an_earlier_epoch(self):
        bad = copy.deepcopy(self.report)
        # All values match the original gain, but this response precedes its ACK.
        commands = bad['guard']['commands']
        saved_gain = next(c for c in commands if c['line'] == 'GAIN' and c['epoch'] == 5)
        saved_gain['epoch'] = 3
        with self.assertRaisesRegex(ValueError, 'fresh native exchange'): q.inspect_trial(bad, self.blob)

    def test_snapshot_cannot_claim_a_mutated_stat_or_hidden_state(self):
        for mode in ('raw', 'parsed', 'nproc'):
            bad = copy.deepcopy(self.report)
            if mode == 'raw': bad['saved']['responses']['GAIN'] = ['GAIN in=0 out=1 dB']
            elif mode == 'parsed': bad['saved']['state']['gain'] = [0, 1]
            else: bad['UI_processing']['A2_nproc_delta'] += 1
            with self.subTest(mode=mode), self.assertRaises(ValueError): q.inspect_trial(bad, self.blob)

    def test_epoch_and_command_identity_are_not_interchangeable(self):
        for mode in ('id', 'epoch', 'seq'):
            bad = copy.deepcopy(self.report)
            if mode == 'id': bad['guard']['commands'][1]['id'] = bad['guard']['commands'][0]['id']
            elif mode == 'epoch': bad['guard']['epoch'] = 8
            else: bad['guard']['rx'][1]['seq'] = bad['guard']['rx'][0]['seq']
            with self.subTest(mode=mode), self.assertRaises(ValueError): q.inspect_trial(bad, self.blob)

    def test_missing_close_and_capture_byte_corruption_fail(self):
        bad = copy.deepcopy(self.report); bad['disconnect']['native_close_verified'] = False
        with self.assertRaises(ValueError): q.inspect_trial(bad, self.blob)
        bad = copy.deepcopy(self.report)
        bad['capture_verification']['command_responses']['CREAD 0 0'][0] += 'A'
        with self.assertRaises(ValueError): q.inspect_trial(bad, self.blob)

    def test_header_and_chunk_reads_cannot_appear_after_ui_started(self):
        bad = copy.deepcopy(self.report)
        event = next(e for e in bad['guard']['events'] if e['kind'] == 'capture_verified_by_host')
        event['seq'] = next(e['seq'] for e in bad['guard']['events'] if e['kind'] == 'trial_plan') + 1
        with self.assertRaises(ValueError): q.inspect_trial(bad, self.blob)

    def test_all_frozen_dependencies_remain_exact(self):
        for name, digest in {**q.PINS, **q.BOOTSTRAP_PINS, **q.UI_PINS, **q.RESUME_PINS, **q.RESUME_V2_PINS}.items():
            with self.subTest(name=name): self.assertEqual(q.sha((q.ROOT/name).read_bytes()), digest)
        from tools import run_mini_v3_first_preset_ui_v3 as ui
        self.assertEqual(q.canonical_sha(ui.description()), q.UI_EXTENSION_SHA)

    def test_two_synthetic_sessions_are_joined_without_padding_or_grant(self):
        report, partial = synthetic_continuation()
        before = copy.deepcopy(partial)
        value = q.inspect_continuation(report, partial)
        self.assertEqual(value['evidence_model'], q.JOINT_MODEL)
        self.assertEqual(value['session_count'], 2)
        self.assertTrue(value['one_reload_verified'])
        self.assertFalse(value['hardware_execution_attested'])
        self.assertEqual(partial, before)
        self.assertEqual(sorted(value['physically_exercised_requests']), q.FAMILIES)
        self.assertNotIn('PLOAD', partial['summary']['physically_exercised_requests'])

    def test_unknown_continuation_version_is_not_reinterpreted(self):
        report, partial = synthetic_continuation()
        report['kind'] += '-unknown'
        with self.assertRaisesRegex(ValueError, 'unknown continuation'):
            q.inspect_continuation(report, partial)

    def test_v2_native_identity_and_bounded_empty_bootstrap_do_not_invent_uia(self):
        for empty in (0, 4):
            report, partial = synthetic_continuation(v2=True, empty_timeouts=empty)
            value = q.inspect_continuation(report, partial)
            proof = value['continuation_connection_proof']
            with self.subTest(empty=empty):
                self.assertEqual(value['evidence_model'], q.JOINT_MODEL_V2)
                self.assertEqual(proof['bootstrap']['attempt_count'], empty+1)
                self.assertEqual(proof['bootstrap']['empty_timeout_count'], empty)
                self.assertFalse(proof['UIA_selection_attested'] or proof['COM_name_attested'])
                self.assertEqual(proof['selection_actor'], 'unattested')
                self.assertEqual(value['continuation_raw_trace']['actual_UI_mutation_count'], 2)
                self.assertFalse(value['hardware_execution_attested'])
                self.assertIsNone(q.validate_continuation_selection(report, partial, q.JOINT_MODEL_V2))
                with self.assertRaises(ValueError):
                    q.validate_continuation_selection(report, partial, q.JOINT_MODEL)

    def test_v2_rejects_timeout_bytes_partial_write_wrong_identity_and_extra_attempt(self):
        for what in ('RX', 'write', 'native_error', 'native_id', 'pong', 'late_bytes', 'timeout', 'reopen',
                     'proof_actor', 'mutation_retry', 'query_retry', 'read_empty', 'chronology'):
            report, partial = synthetic_continuation(v2=True, empty_timeouts=1)
            guard = report['guard']
            if what == 'RX': guard['rx'].append({'seq': guard['commands'][0]['seq']-1, 'hex': '00'})
            elif what == 'write': guard['nativeWrites'][0]['bytes'] = 4
            elif what == 'native_error': guard['nativeErrors'] = [{'kind': 'native_read_error'}]
            elif what == 'native_id': guard['events'][2]['info']['pid'] = 1
            elif what == 'pong': guard['commands'][1]['lines'] = ['PONG tankg_fw M5.71 rel ble']
            elif what == 'late_bytes': guard['bootstrap_attempts'][1]['start_rx_bytes'] += 1
            elif what == 'timeout': guard['editorCompletions'][0]['timed_out'] = False
            elif what == 'reopen': guard['opens'] = 2
            elif what == 'proof_actor': report['selection_proof']['selection_actor'] = 'user'
            elif what == 'mutation_retry': report['mutation_retry_performed'] = True
            elif what == 'query_retry': report['query_retry_performed'] = True
            elif what == 'read_empty': guard['commands'][2]['lines'] = []
            else: guard['nativeWrites'][2]['seq'] = guard['wire'][2]['seq']
            with self.subTest(what=what), self.assertRaises(ValueError):
                q.inspect_continuation(report, partial)
        with self.assertRaisesRegex(ValueError, 'bounded bootstrap'):
            synthetic_continuation(v2=True, empty_timeouts=5)

    def test_v2_optional_uia_file_cannot_be_omitted_or_fabricated(self):
        report, partial = synthetic_continuation(v2=True)
        partial['context']['com'] = 'COM3'
        with tempfile.TemporaryDirectory(dir=q.ROOT/'build') as tmp:
            path = Path(tmp)/'selection.json'
            report['selection_path'] = path.relative_to(q.ROOT).as_posix()
            self.assertIsNone(q.validate_continuation_selection(report, partial, q.JOINT_MODEL_V2))
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'omitted'):
                q.validate_continuation_selection(report, partial, q.JOINT_MODEL_V2)
            report.update(selection={}, browser_process_id=10, origin='http://127.0.0.1:1234',
                          started_utc='2026-11-16T08:00:00Z', finished_utc='2026-11-16T08:01:00Z')
            with self.assertRaises(ValueError):
                q.validate_continuation_selection(report, partial, q.JOINT_MODEL_V2)

    def test_v2_synthetic_file_cannot_create_a_qualification_or_bundle(self):
        report, _ = synthetic_continuation(v2=True, empty_timeouts=1)
        with tempfile.TemporaryDirectory(dir=q.ROOT/'build') as tmp:
            path = Path(tmp)/'synthetic-v2.json'; path.write_bytes(q.encoded(report))
            with self.assertRaisesRegex(ValueError, 'real successful continuation'):
                q.build_qualified_bundle(path, q.sha(path.read_bytes()), Path(tmp)/'must-not-exist',
                    partial_report_path=q.PARTIAL_REF['path'], partial_sha256=q.PARTIAL_REF['sha256'])
            self.assertFalse((Path(tmp)/'must-not-exist').exists())

    def test_recorded_browser_configuration_is_exact_and_does_not_launch(self):
        from tools import mini_browser_windows as config
        with tempfile.TemporaryDirectory(dir=q.ROOT/'build') as tmp:
            folder = Path(tmp)
            ref = {'path': (folder/'report.json').relative_to(q.ROOT).as_posix(), 'sha256': '0'*64}
            executable = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
            args = config.browser_arguments(executable, folder/'isolated-profile')
            report = {'browser_arguments': args, 'browser_configuration': config.description(args)}
            q.validate_continuation_browser(report, ref)
            edge_args = config.browser_arguments(Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'),
                                                 folder/'isolated-profile')
            q.validate_continuation_browser({'browser_arguments': edge_args,
                                            'browser_configuration': config.description(edge_args)}, ref)
            for what in ('missing', 'feature', 'profile', 'extra', 'description'):
                bad = copy.deepcopy(report)
                if what == 'missing': bad.pop('browser_arguments')
                elif what == 'feature':
                    index = next(i for i, value in enumerate(args) if value.startswith('--disable-features='))
                    bad['browser_arguments'][index] = bad['browser_arguments'][index].replace(',SerialUsbDisplayNameWin', '')
                elif what == 'profile': bad['browser_arguments'][-2] = '--user-data-dir=C:/unrelated'
                elif what == 'extra': bad['browser_arguments'].append('--disable-web-security')
                else: bad['browser_configuration']['causality_proven'] = True
                with self.subTest(what=what), self.assertRaises(ValueError):
                    q.validate_continuation_browser(bad, ref)

    def test_v2_sealed_shape_preserves_native_proof_without_selection_file(self):
        # Synthetic in-memory post-boundary shape only: no evidence file or
        # bundle is emitted. The public evidence boundary rejects this fixture
        # in test_v2_synthetic_file_cannot_create_a_qualification_or_bundle.
        report, partial = synthetic_continuation(v2=True, empty_timeouts=1)
        summary = q.inspect_continuation(report, partial)
        from tools import run_mini_v3_first_preset_ui_v3 as ui
        report.update(source_sha256={}, finished_utc='2026-11-16T08:01:00Z')
        ref = {'path': 'synthetic-not-a-file', 'sha256': '0'*64}
        prepared = {'context': {**partial['context'], 'com': 'COM3'}, 'inputs': {}, 'blob': ref}
        with patch.object(q, 'reference', side_effect=AssertionError('no UIA file exists')):
            value = q.qualification_record(ref, report, prepared, ui.description(), summary, q.JOINT_MODEL_V2)
        value.update(saved_partial_report=q.PARTIAL_REF, reloaded_report=ref, reloaded_snapshot=report['reloaded'],
            sessions=[{'role': 'save', 'report': q.PARTIAL_REF, 'original_result': 'fail', 'verified_UI_writes': 4},
                      {'role': 'reload', 'report': ref, 'original_result': 'pass', 'verified_UI_writes': 2}])
        self.assertNotIn('selection', value['refs'])
        self.assertEqual(q.validate_qualification(value)['evidence_model'], q.JOINT_MODEL_V2)
        for what in ('actor', 'COM', 'PONG', 'scope', 'bootstrap', 'model'):
            bad = copy.deepcopy(value)
            if what == 'actor': bad['connection_proof']['selection_actor'] = 'user'
            elif what == 'COM': bad['connection_proof']['COM_name_attested'] = True
            elif what == 'PONG': bad['connection_proof']['exact_pong'] = 'PONG tankg_fw'
            elif what == 'scope': bad['enabled_families'] += ['FXE']
            elif what == 'bootstrap': bad['connection_proof']['bootstrap']['attempt_count'] = 6
            else: bad['evidence_model'] = q.JOINT_MODEL
            with self.subTest(what=what), self.assertRaises(ValueError): q.validate_qualification(bad)
        value['synthetic_fixture'] = True
        with self.assertRaisesRegex(ValueError, 'synthetic'): q.validate_qualification(value)

    def test_closed_failed_saved_reload_sessions_cannot_qualify(self):
        found = False
        for attempt in ('05', '06'):
            path = q.ROOT/f'build/mini-saved-reload-ui-{attempt}/report.json'
            if not path.is_file(): continue
            found = True
            raw = path.read_bytes()
            report = json.loads(raw)
            self.assertEqual(report['result'], 'fail')
            with self.subTest(attempt=attempt), \
                 patch.object(q, 'validate_partial_saved_report', side_effect=AssertionError('unnecessary replay')):
                with self.assertRaisesRegex(ValueError, 'real successful continuation'):
                    q.validate_joined_reports(q.PARTIAL_REF['path'], q.PARTIAL_REF['sha256'], path, q.sha(raw))
            self.assertEqual(path.read_bytes(), raw)
        if not found: self.skipTest('private closed hardware evidence is not distributed')

    def test_continuation_rejects_changed_saved_state_wrong_epoch_and_missing_rx(self):
        for what in ('before', 'plan', 'epoch', 'RX', 'close', 'extra_save'):
            report, partial = synthetic_continuation()
            if what == 'before': report['before']['state']['gain'] = [1, 0]
            elif what == 'plan': report['plan']['slot'] = 1
            elif what == 'epoch': report['guard']['epoch'] = 3
            elif what == 'RX': report['guard']['rx'][-1]['hex'] = b'bad\r\n'.hex()
            elif what == 'close': report['disconnect']['native_close_verified'] = False
            else: report['prior_save_reperformed'] = True
            with self.subTest(what=what), self.assertRaises(ValueError): q.inspect_continuation(report, partial)

    def test_in_memory_adapter_denies_other_families_or_blanket_write(self):
        # Isolate the adapter after its qualification boundary. No proof file,
        # app artifact or grant is emitted by this fixture.
        qualification = {'synthetic_fixture': True, 'physically_exercised_requests': {}, 'evidence_model': q.JOINT_MODEL_V2}
        proof = {'path': 'synthetic-not-a-file', 'sha256': '0'*64}
        spec = {'family_evidence_model': q.JOINT_MODEL_V2, 'family_capabilities': {'usb-cdc': q.FAMILIES},
            'family_validation': {'usb-cdc': [proof]}, 'hardware_verified': True,
            'image_sha256': q.IMAGE, 'firmware_version': q.VERSION}
        caps = {'identity': True, 'read': True, 'write': False, 'panel': False}
        original = q.app.load_family_validation
        with patch.object(q, 'validate_qualification', return_value=qualification), \
             patch.object(q, 'read_ref', return_value=q.encoded(qualification)):
            with q.family_adapter(qualification, proof):
                self.assertEqual(q.app.load_family_validation(spec, caps)[0], {'usb-cdc': q.FAMILIES})
                for changed in ('BLE', 'FXE', 'panel', 'write', 'literal'):
                    bad, policy = copy.deepcopy(spec), copy.deepcopy(caps)
                    if changed == 'BLE': bad['family_capabilities']['ble-nus'] = ['GAIN']
                    elif changed == 'FXE': bad['family_capabilities']['usb-cdc'] += ['FXE']
                    elif changed == 'literal': bad['command_capabilities'] = {'GAIN': ['GAIN 0 0']}
                    else: policy[changed] = True
                    with self.subTest(changed=changed), self.assertRaises(ValueError):
                        q.app.load_family_validation(bad, policy)
        self.assertIs(q.app.load_family_validation, original)

    def test_runtime_seal_is_local_and_detects_edits_without_evidence_replay(self):
        # The qualification boundary is mocked only for this labelled fixture;
        # public validate_trial_report rejects it. No real bundle is produced.
        with tempfile.TemporaryDirectory(dir=q.ROOT/'build') as tmp:
            folder = Path(tmp); web = folder/'app/web'; web.mkdir(parents=True)
            qualified = {'synthetic_fixture': True, 'com': 'COM3', 'evidence_model': q.JOINT_MODEL_V2,
                'pong': self.report['prepared']['context']['pong'], 'physically_exercised_requests': {}}
            proof_path = folder/'qualification.json'; proof_path.write_bytes(q.encoded(qualified))
            proof = q.reference(proof_path)
            profile = q.app.load_profile(q.ROOT/q.BASE_MANIFEST)
            profile.update(hardware_verified=True, family_capabilities={'usb-cdc': q.FAMILIES},
                family_validation={'usb-cdc': [proof]}, family_qualification={'usb-cdc': q.family_metadata(qualified)})
            spec = {**profile, 'family_evidence_model': q.JOINT_MODEL_V2}
            manifest = folder/'firmware-manifest.json'; manifest.write_bytes(q.encoded(spec))
            (web/'mini-profile.js').write_bytes((q.ROOT/'app/mini/mini-profile.js').read_bytes())
            (web/'mini-ui.js').write_bytes((q.ROOT/'app/mini/mini-ui-v2.js').read_bytes())
            config = json.dumps(profile, separators=(',', ':'), ensure_ascii=True).replace('<', '\\u003c')
            (web/'tankmini.html').write_text('<script>globalThis.HYPERRIG_MINI_BUILD='+config+';</script>', encoding='utf-8')
            for name in ('index.html', 'nam2chip.js', 'fixture.txt'): (web/name).write_text('synthetic fixture', encoding='utf-8')
            metadata = {'schema': 1, 'kind': 'mini-qualified-editor-bundle', 'evidence_model': q.JOINT_MODEL_V2,
                'image_sha256': q.IMAGE, 'com': qualified['com'], 'pong': qualified['pong'],
                'app_directory': web.relative_to(q.ROOT).as_posix(), 'profile': profile,
                'manifest': q.reference(manifest), 'qualification': proof,
                'qualification_verifier_sha256': q.sha(Path(q.__file__).read_bytes()),
                'files': {p.relative_to(folder).as_posix(): q.sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file()}}
            raw = q.encoded(metadata)
            (folder/'bundle.json').write_bytes(raw); (folder/'bundle.sha256').write_text(q.sha(raw)+'\n', encoding='ascii')
            with self.assertRaisesRegex(ValueError, 'synthetic'): q.validate_bundle(folder)
            with patch.object(q, 'validate_qualification', return_value=qualified), \
                 patch.object(q, 'validate_trial_report', side_effect=AssertionError('historical replay')), \
                 patch.object(q, 'read_ref', side_effect=AssertionError('historical read')):
                value = q.validate_bundle(folder)
                self.assertFalse(value['historical_evidence_replayed_on_launch'])
                self.assertEqual(value['profile']['family_capabilities'], {'usb-cdc': q.FAMILIES})
                (web/'tankmini.html').write_text('changed', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'bundle file changed'): q.validate_bundle(folder)

    def test_derived_html_retains_original_policy_and_four_family_profile(self):
        profile = q.app.load_profile(q.ROOT/q.BASE_MANIFEST)
        profile.update(hardware_verified=True, family_capabilities={'usb-cdc': q.FAMILIES},
                       family_validation={'usb-cdc': [{'path': 'synthetic-not-an-artifact', 'sha256': '0'*64}]})
        html, _ = q.app.derive_html(q.app.checked(q.app.SOURCE/'web/tankg.html', q.app.SOURCE_SHA).decode(), profile)
        self.assertIn('globalThis.HYPERRIG_MINI_BUILD=', html)
        self.assertIn('HyperRigMini.commandPolicy', html)
        self.assertIn('HyperRigMini.observeReply', html)
        self.assertFalse(profile['capabilities']['write'] or profile['capabilities']['panel'])
        self.assertEqual(profile['family_capabilities'], {'usb-cdc': q.FAMILIES})


if __name__ == '__main__': unittest.main()
