"""Temporary synthetic line-evidence fixtures only; no browser or device I/O."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import validate_mini_webserial_v3 as proof


class WebSerialEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=proof.ROOT/'build', prefix='TEST-webserial-v3-evidence-')
        self.addCleanup(temporary.cleanup); self.folder = Path(temporary.name)
        self.path_boot = self.folder/'boot.json'; self.path_boot.write_text('{"offline_fixture":true}')
        self.boot_ref = self.ref(self.path_boot)
        self.prepared = {'evidence': {'com': 'COM123', 'observed_utc': '2020-01-01T00:00:00Z'},
            'profile': {'image_sha256': proof.IMAGE_SHA, 'firmware_version': proof.VERSION,
                        'hardware_verified': False, 'capabilities': {'read': True, 'write': False, 'panel': False}},
            'inputs': {'normal_boot': self.boot_ref, 'independent': {'path': 'OFFLINE FIXTURE', 'sha256': '0'*64}}}
        pong = 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'
        self.answers = {
            'PING': [pong], 'MODEL': ["MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=0.0"],
            'MEM': ['MEM free=1000'], 'LVL': ['LVL in=-1440 out=-1440 ci=0 co=0 m=2 g=0/0'],
            'FXT': ['FXT 2 boost cost=340 cat=drive mem=64', 'FXT  0 ganancia_db -12..24 (6)', 'FXT end'],
            'FXS': ['FXS amp=1 on=1', 'FXS eng=1 posts=4 takes=4 canc=0 lat=1/2 run=0',
                    'FXS cpu=1/18950 ticks (0%) mem_fx=0 B', 'FXS peak=1 ticks skipped=0'],
            'PLIST': ['PLIST end current=-1'], 'PSTAT': ['PSTAT live=1 erased=0'],
            'SNAPS': ['SNAPS 0000 current=-1'], 'SNAPNAME': ["SNAPNAME 0 ''", 'SNAPNAME end'],
            'CLKSTATE': ['CLKSTATE mhz=360 state=untested safe=0 eng=1']}
        commands = [{'line': name, 'lines': lines} for name, lines in self.answers.items()]
        replies = [line for lines in self.answers.values() for line in lines]
        wire = [{'line': name, 'started': 10+i, 'completed': True, 'finished': 10.1+i}
                for i, name in enumerate(self.answers)]
        events = [{'kind': kind, 'time': i+1} for i, kind in enumerate(
            ('app_guard_installed', 'serial_request_intent', 'serial_open_intent', 'serial_open_complete', 'expected_pong_received'))]
        guard = {'live': True, 'appInstalled': True, 'requests': 1, 'opens': 1, 'closes': 0,
            'closeError': None, 'fatal': None, 'pongMatched': True, 'observedPong': pong,
            'portInfo': {'vid': proof.readonly.VID, 'pid': proof.readonly.PID}, 'hardwareStubCalls': [],
            'stopped': False, 'wire': wire, 'events': events, 'commands': commands, 'replies': replies,
            'commandCount': len(commands), 'replyCount': len(replies)}
        self.connected = {'observed_utc': '2020-01-01T00:00:03Z', 'inputs': copy.deepcopy(self.prepared['inputs']),
            'state': {'ready': True, 'connected': True, 'demo': False, 'initialReadsFinished': True, 'fw': pong},
            'guard': guard, 'held_recovery_verified': False, 'audio_verified': False, 'mutations_enabled': False}
        final = copy.deepcopy(guard); final.update(stopped=True, closes=1)
        final['events'] += [{'kind': 'serial_close_intent', 'time': 30}, {'kind': 'serial_close_complete', 'time': 31},
                            {'kind': 'guard_stopped', 'time': 32}]
        self.session = {'kind': 'mini-desktop-readonly-v3-session', 'phase': 'connected_readonly',
            'started_utc': '2020-01-01T00:00:01Z', 'connected_utc': '2020-01-01T00:00:02Z', 'finished_utc': '2020-01-01T00:00:04Z',
            'identity_verified': True, 'first_handshake': True, 'demo': False, 'mutations_enabled': False,
            'held_recovery_verified': False, 'audio_verified': False, 'serial_port_closed': True,
            'local_server_stopped': True, 'browser_process_stopped': True,
            'disconnect': {'native_close_verified': True, 'open': False, 'closes': 1, 'closeError': None},
            'evidence': copy.deepcopy(self.prepared), 'actual_identity': proof.readonly.inspect_pong(pong, proof.VERSION),
            'last_guard': final, 'source_sha256': {path.relative_to(proof.ROOT).as_posix(): proof.sha(path.read_bytes()) for path in
                (Path(proof.desktop.__file__), proof.desktop.GUARD, proof.desktop.APP/'tankmini.html')}}

    @staticmethod
    def ref(path):
        return {'path': path.relative_to(proof.ROOT).as_posix(), 'sha256': proof.sha(path.read_bytes())}

    def validate(self):
        connected_path = self.folder/'connected-proof.json'; session_path = self.folder/'session.json'
        connected_path.write_text(json.dumps(self.connected)); session_path.write_text(json.dumps(self.session))
        with patch.object(proof.desktop, 'prepare', return_value=self.prepared) as prepare:
            result = proof.validate_v3_browser_evidence(boot=self.boot_ref,
                connected=self.ref(connected_path), session=self.ref(session_path))
            prepare.assert_called_once_with(self.path_boot, self.boot_ref['sha256'])
            return result

    def test_completed_v3_read_context_returns_actual_state_but_no_write_grants(self):
        result = self.validate()
        self.assertTrue(result['read_verified'] and result['serial_port_closed'])
        self.assertEqual(result['com'], 'COM123')
        self.assertEqual(result['runtime']['gain'], [0, 0])
        self.assertEqual(result['runtime']['clock']['safe'], 0)
        self.assertEqual(result['runtime']['lvl']['input_clips'], 0)
        self.assertEqual(result['runtime']['lvl']['output_clips'], 0)
        self.assertNotIn('input_samples', result['runtime']['lvl'])
        self.assertEqual(result['runtime']['preset_trial_path'], 'first-preset-free-slot')
        self.assertEqual(result['runtime']['types']['boost']['params'][0]['min'], -12)
        self.assertFalse(result['profile']['hardware_verified'] or result['profile']['capabilities']['write'])
        self.assertFalse(result['capabilities_granted'])
        for key in ('raw_RX_bytes_retained', 'raw_byte_replay_performed', 'image_hash_attested_by_device',
                    'audio_verified', 'held_recovery_verified', 'cold_power_cycle_verified', 'BLE_verified', 'preset_writes_verified'):
            self.assertIs(result[key], False)

    def test_safe_mode_is_an_observation_not_rejected_read_proof_or_audio_pass(self):
        old = self.answers['CLKSTATE'][0]; new = old.replace('safe=0', 'safe=1')
        self.connected['guard']['commands'][-1]['lines'] = [new]
        self.connected['guard']['replies'][-1] = new
        result = self.validate()
        self.assertEqual(result['runtime']['clock']['safe'], 1)
        self.assertTrue(result['read_verified']); self.assertFalse(result['audio_verified'])

    def test_active_failed_or_unclosed_session_cannot_become_trial_context(self):
        for key, value in (('finished_utc', None), ('serial_port_closed', False), ('phase', 'connection_failed'),
                           ('error', 'failure'), ('monitor_error', 'unknown connection'), ('demo', True),
                           ('audio_verified', True), ('mutations_enabled', True), ('local_server_stopped', False)):
            saved = copy.deepcopy(self.session); self.session[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate()
            self.session = saved
        self.session['disconnect']['native_close_verified'] = False
        with self.assertRaises(ValueError): self.validate()

    def test_report_links_source_and_chronology_must_match(self):
        for fault in ('links', 'source', 'missing_source', 'chronology', 'identity'):
            saved = copy.deepcopy(self.session)
            if fault=='links': self.session['evidence']['inputs']['normal_boot']['sha256'] = '0'*64
            if fault=='source': self.session['source_sha256'][str(Path(proof.desktop.__file__).relative_to(proof.ROOT)).replace('\\', '/')] = '0'*64
            if fault=='missing_source': self.session['source_sha256'].pop(proof.desktop.GUARD.relative_to(proof.ROOT).as_posix())
            if fault=='chronology': self.session['started_utc'] = '2019-01-01T00:00:00Z'
            if fault=='identity': self.session['actual_identity']['pong'] = 'PONG wrong'
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.validate()
            self.session = saved

    def test_required_replies_need_wire_completion_and_retained_input_lines(self):
        for fault in ('missing_wire', 'incomplete_write', 'missing_input', 'truncated', 'bad_terminator', 'error'):
            saved = copy.deepcopy(self.connected)
            if fault=='missing_wire': self.connected['guard']['wire'] = [x for x in self.connected['guard']['wire'] if x['line']!='FXT']
            if fault=='incomplete_write': next(x for x in self.connected['guard']['wire'] if x['line']=='FXT')['completed'] = False
            if fault=='missing_input': self.connected['guard']['replies'].remove('FXT end'); self.connected['guard']['replyCount'] -= 1
            if fault=='truncated': self.connected['guard']['commandCount'] += 1
            if fault in ('bad_terminator', 'error'):
                next(x for x in self.connected['guard']['commands'] if x['line']=='FXT')['lines'] = ['ERR refused' if fault=='error' else 'FXT partial']
                self.connected['guard']['replies'].append('FXT partial'); self.connected['guard']['replyCount'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.validate()
            self.connected = saved

    def test_nonquery_during_later_session_or_unknown_close_is_rejected(self):
        self.session['last_guard']['wire'].append({'line': 'GAIN 0 -1', 'started': 40, 'completed': True, 'finished': 41})
        with self.assertRaises(ValueError): self.validate()
        self.session['last_guard']['wire'].pop()
        self.session['last_guard']['events'].pop(6)  # Native close completion.
        with self.assertRaises(ValueError): self.validate()

    def test_wrong_hash_or_cross_directory_evidence_fails_before_context_preparation(self):
        connected = self.folder/'connected-proof.json'; connected.write_text(json.dumps(self.connected))
        other = self.folder/'other'; other.mkdir(); session = other/'session.json'; session.write_text(json.dumps(self.session))
        with patch.object(proof.desktop, 'prepare', side_effect=AssertionError('must not prepare')):
            with self.assertRaises(ValueError): proof.validate_v3_browser_evidence(
                boot=self.boot_ref, connected={**self.ref(connected), 'sha256': '0'*64}, session=self.ref(session))
            with self.assertRaises(ValueError): proof.validate_v3_browser_evidence(
                boot=self.boot_ref, connected=self.ref(connected), session=self.ref(session))


if __name__ == '__main__': unittest.main()
