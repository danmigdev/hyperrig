"""v3 first WebSerial handshake adapter, exclusively local fake evidence."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import launch_mini_desktop_v3 as desk

PORT = {'device': 'COM123', 'vid': 0x3654, 'pid': 0x5155, 'description': 'OFFLINE FIXTURE'}


class DesktopV3Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=desk.ROOT/'build', prefix='TEST-desktop-v3-')
        self.addCleanup(temporary.cleanup); self.folder = Path(temporary.name)

    def boot(self):
        return {'started_utc': '2020-01-01T00:00:01Z', 'finished_utc': '2020-01-01T00:00:02Z',
            'phase': 'application_USB_observed', 'boot_mode': 'normal-software-boot',
            'buttons_confirmed_by_user': False, 'buttons_assumed': 'released',
            'held_button_boot_trial_performed': False, 'cold_power_cycle_tested': False, 'guard_causality_confirmed': False,
            'candidate_sha256': desk.IMAGE_SHA, 'application_USB_enumerated': True,
            'candidate_CDC_absent_before_reset': True, 'reset_submitted': True, 'slot_A_inactive_verified': True,
            'known_live_slot_before_reset': desk.boot_runner.B, 'firmware_write': False, 'automatic_retry': False,
            'application_ports': [PORT], 'app_identity_verified': False, 'audio_verified': False,
            'serial_port_opened': False, 'PING_attempted': False}

    def fixture(self, *, fault=None):
        install_path = self.folder/'install.json'
        install = {'finished_utc': '2020-01-01T00:00:00Z'}
        if fault=='chronology': install['finished_utc'] = '2020-01-01T00:00:03Z'
        install_path.write_text(json.dumps(install))
        independent_path = self.folder/'independent.json'; independent_path.write_text('{"offline_fixture":true}')
        mcn_path = self.folder/'mcn.jsonl'; mcn_path.write_text('{"offline_fixture":true}\n')
        verification = {'run': desk.ref(install_path), 'independent': desk.ref(independent_path), 'MCN': desk.ref(mcn_path),
            'final_reader_counter': 0x100000, 'final_read_lost_bytes': 0,
            'external_regions_assumed_stock': False}
        boot = self.boot()
        boot.update(source_pins={desk.BOOT_RUNNER.relative_to(desk.ROOT).as_posix(): desk.sha(desk.BOOT_RUNNER.read_bytes())},
            upgrade_verification=copy.deepcopy(verification), installation_evidence_path=verification['run']['path'],
            installation_evidence_sha256=verification['run']['sha256'], MCN_cleanup_evidence_path=verification['MCN']['path'],
            MCN_cleanup_evidence_sha256=verification['MCN']['sha256'])
        if fault=='source': boot['source_pins'][desk.BOOT_RUNNER.relative_to(desk.ROOT).as_posix()] = '0'*64
        if fault=='no_source': boot['source_pins'] = {'tools/probe_mini_app.py': desk.sha(Path(desk.readonly.__file__).read_bytes())}
        if fault=='verification': boot['upgrade_verification']['final_read_lost_bytes'] = 512
        if fault=='run_ref': boot['installation_evidence_sha256'] = '0'*64
        if fault=='mcn_ref': boot['MCN_cleanup_evidence_sha256'] = '0'*64
        path = self.folder/'boot.json'; path.write_text(json.dumps(boot))
        return path, install, verification

    def test_default_does_not_read_evidence_or_start_browser(self):
        with (patch.object(desk, 'prepare', side_effect=AssertionError('evidence')),
              patch.object(desk, 'run', side_effect=AssertionError('browser')),
              contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(desk.main([]), 0)
        self.assertFalse(any(json.loads(output.getvalue())[key] for key in ('device_io', 'browser_started', 'inputs_read')))

    def test_boot_is_CDC_only_without_invented_PONG_or_held_trial(self):
        self.assertEqual(desk.validate_normal_boot(self.boot()), PORT)
        for field, value in (('candidate_sha256', desk.browser.IMAGE_SHA), ('serial_port_opened', True),
                            ('PING_attempted', True), ('app_identity_verified', True), ('audio_verified', True),
                            ('held_button_boot_trial_performed', True), ('buttons_confirmed_by_user', True),
                            ('candidate_CDC_absent_before_reset', False), ('slot_A_inactive_verified', False),
                            ('known_live_slot_before_reset', desk.boot_runner.A), ('application_ports', [PORT, PORT]),
                            ('phase', 'application_PONG_verified'), ('finished_utc', None), ('error', 'offline error')):
            with self.subTest(field=field):
                boot = self.boot(); boot[field] = value
                with self.assertRaises(ValueError): desk.validate_normal_boot(boot)

    def test_prepare_uses_actual_v3_editor_and_no_prior_PING_evidence(self):
        path, install, verification = self.fixture()
        before = desk.MANIFEST.read_bytes()
        with patch.object(desk.boot_runner, 'validate_upgrade', return_value=(install, verification)) as validate:
            prepared = desk.prepare(path, desk.sha(path.read_bytes()))
        validate.assert_called_once()
        self.assertTrue(prepared['first_handshake'])
        self.assertIsNone(prepared['evidence']['pong'])
        self.assertFalse(prepared['evidence']['identity_verified'])
        self.assertFalse(prepared['evidence']['serial_port_opened_by_boot'])
        self.assertNotIn('serial_port_closed', prepared['evidence'])
        self.assertNotIn('PING', prepared['inputs'])
        self.assertEqual(prepared['profile']['image_sha256'], desk.IMAGE_SHA)
        self.assertFalse(prepared['profile']['capabilities']['write'])
        self.assertEqual(desk.MANIFEST.read_bytes(), before)

    def test_prepare_rejects_changed_source_refs_audit_or_chronology(self):
        for fault in ('source', 'no_source', 'verification', 'run_ref', 'mcn_ref', 'chronology'):
            with self.subTest(fault=fault):
                path, install, verification = self.fixture(fault=fault)
                with patch.object(desk.boot_runner, 'validate_upgrade', return_value=(install, verification)):
                    with self.assertRaises(ValueError): desk.prepare(path, desk.sha(path.read_bytes()))
        path, _, _ = self.fixture()
        with self.assertRaises(ValueError): desk.prepare(path, '0'*64)

    def test_browser_failure_shuts_server_without_starting_device_handshake(self):
        calls = []
        class Server:
            server_port = 12345
            def __init__(self, *args, **kwargs): calls.append(('directory', kwargs.get('directory')))
            def serve_forever(self): calls.append('serve')
            def shutdown(self): calls.append('shutdown')
            def server_close(self): calls.append('close')
        prepared = {'inputs': {'normal_boot': {'path': 'unused', 'sha256': '0'*64}}, 'first_handshake': True}
        with (patch.object(desk, 'prepare', return_value=prepared),
              patch.object(desk.http.server, 'ThreadingHTTPServer', Server),
              patch.object(desk.browser, 'browser_path', side_effect=ValueError('OFFLINE no browser'))):
            result = desk.run(prepared, self.folder/'session')
        self.assertEqual(result['phase'], 'connection_failed')
        self.assertTrue(result['local_server_stopped'] and result['browser_process_stopped'])
        self.assertFalse(result['identity_verified'] or result['serial_port_closed'])
        self.assertEqual(calls[-3:], ['serve', 'shutdown', 'close'])

    def test_changed_prepared_evidence_is_rejected_before_server_start(self):
        prepared = {'inputs': {'normal_boot': {'path': 'unused', 'sha256': '0'*64}}, 'first_handshake': True}
        with (patch.object(desk, 'prepare', return_value={**prepared, 'changed': True}),
              patch.object(desk.http.server, 'ThreadingHTTPServer', side_effect=AssertionError('server'))):
            with self.assertRaises(ValueError): desk.run(prepared, self.folder/'never-created')
        self.assertFalse((self.folder/'never-created').exists())

    def test_fake_full_lifecycle_waits_for_UIA_without_DeviceAccess_or_prior_PING(self):
        output = self.folder/'connected-session'
        profile = json.loads(desk.EDITOR_REPORT.read_bytes())['profile']
        prepared = {'inputs': {'normal_boot': {'path': 'unused', 'sha256': '0'*64}},
            'evidence': {'com': PORT['device'], 'pong': None}, 'profile': profile, 'first_handshake': True}
        methods, phases, configs, server_calls = [], [], [], []
        process = None
        pong = 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'
        class Server:
            server_port = 12345
            def __init__(self, *a, **k): pass
            def serve_forever(self): server_calls.append('serve')
            def shutdown(self): server_calls.append('shutdown')
            def server_close(self): server_calls.append('close')
        class Process:
            pid = 123456
            def __init__(self, args, **kwargs):
                nonlocal process
                process = self; self.finished = False
                profile_path = Path(next(x.split('=', 1)[1] for x in args if x.startswith('--user-data-dir=')))
                (profile_path/'DevToolsActivePort').write_text('12345\n')
                (output/'close.request').write_text('OFFLINE closure request\n')
            def poll(self): return 0 if self.finished else None
            def wait(self, timeout): self.finished = True; return 0
            def terminate(self): self.finished = True
        class Socket:
            def close(self): pass
        class CDP:
            def __init__(self, endpoint): self.ws = Socket(); self.connected = False
            def call(self, method, params=None):
                methods.append(method)
                if method.startswith('DeviceAccess'): raise AssertionError('unsupported CDP serial chooser')
                if method == 'Page.addScriptToEvaluateOnNewDocument':
                    import re
                    configs.append(json.loads(re.search(r'\ninstallMiniDesktopReadonlyGuard\((.*)\);$', params['source'])[1]))
                if method == 'Browser.close': process.finished = True
                return {}
            def click(self, selector):
                if selector == '#connBtn': self.connected = True  # Fake external chooser completion, no device.
            def evaluate(self, expression):
                if expression == 'window.__urOk===true': return True
                if expression == 'HyperRigMini.profile': return profile
                if expression == desk.STATE:
                    return {'ready': True, 'title': 'HyperRig for TANK MINI', 'connected': self.connected,
                        'initialReadsFinished': self.connected, 'demo': False, 'fw': pong if self.connected else None,
                        'guard': {'fatal': None, 'pongMatched': self.connected, 'observedPong': pong,
                                  'opens': int(self.connected), 'closes': 0, 'closeError': None}}
                if expression == '__miniDesktopGuard.state':
                    return {'commands': [{'line': name, 'lines': [pong if name=='PING' else name+' offline']} for name in
                        ('PING', 'MODEL', 'MEM', 'FXT', 'FXS', 'PLIST', 'SNAPS')], 'opens': 1, 'closes': 1, 'pongMatched': True}
                if expression.startswith('(async()=>{'): return {'open': False, 'closes': 1, 'closeError': None}
                return False
            def screenshot(self, path): path.write_bytes(b'OFFLINE'); return str(path)
        def urlopen(url, timeout):
            if url.endswith('/json/version'): return io.BytesIO(b'{"Browser":"offline fixture"}')
            if url.endswith('/json/list'): return io.BytesIO(b'[{"type":"page","webSocketDebuggerUrl":"ws://offline"}]')
            raise AssertionError('unexpected network metadata request: '+url)
        original_save = desk.atomic_write_json
        def save(path, report):
            phases.append(report['phase']); return original_save(path, report)
        with (patch.object(desk, 'prepare', return_value=prepared),
              patch.object(desk.http.server, 'ThreadingHTTPServer', Server),
              patch.object(desk.subprocess, 'Popen', Process), patch.object(desk.browser, 'browser_path', return_value=Path('offline.exe')),
              patch.object(desk.browser, 'CDP', CDP), patch.object(desk, 'urlopen', side_effect=urlopen),
              patch.object(desk, 'atomic_write_json', side_effect=save), patch.object(desk.time, 'sleep')):
            result = desk.run(prepared, output)
        self.assertNotIn('error', result)
        self.assertIn('awaiting_exact_UIA_selection', phases)
        self.assertEqual(result['phase'], 'connected_readonly')
        self.assertEqual(configs, [{'live': True, 'image_sha256': desk.IMAGE_SHA, 'pong': None,
                                    'firstHandshake': True, 'version': desk.VERSION}])
        self.assertEqual(result['chooser_policy']['expected_COM'], PORT['device'])
        self.assertFalse(result['chooser_policy']['automatic_CDP_selection'] or result['chooser_policy']['selection_verified_by_adapter'])
        self.assertTrue(result['identity_verified'] and result['serial_port_closed'])
        self.assertTrue(result['local_server_stopped'] and result['browser_process_stopped'])
        self.assertFalse(result['audio_verified'] or result['held_recovery_verified'] or result['mutations_enabled'])
        self.assertEqual(server_calls, ['serve', 'shutdown', 'close'])

    def test_close_request_is_separate_local_action_and_does_not_accept_v2_session(self):
        output = self.folder/'active'; output.mkdir()
        path = output/'session.json'; path.write_text(json.dumps({'kind': 'mini-desktop-readonly-session'}))
        with self.assertRaises(ValueError): desk.main(['--close-session', str(output)])
        path.write_text(json.dumps({'kind': 'mini-desktop-readonly-v3-session'}))
        with patch.object(desk, 'run', side_effect=AssertionError('browser')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(desk.main(['--close-session', str(output)]), 0)
        self.assertTrue((output/'close.request').is_file())

    def test_frozen_guard_binds_actual_v3_profile_and_first_real_PONG(self):
        node = shutil.which('node'); self.assertIsNotNone(node)
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const source=fs.readFileSync(process.argv[1],'utf8');
const profile=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).profile;
function setup(p=profile){
 const writes=[];const ctx={navigator:{serial:{}},performance:{now:()=>0},DOMException,localStorage:{setItem(){}}};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 const g=ctx.installMiniDesktopReadonlyGuard({live:true,image_sha256:profile.image_sha256,pong:null,
   firstHandshake:true,version:'tankm_fw M5.71 rel ble'});
 const transport={write:async s=>writes.push(s)},pedal={onLine(){},cmd:async()=>[]};
 g.installApp(transport,pedal,p);return {g,transport,pedal,writes};
}
(async()=>{
 assert.equal(profile.image_sha256,'9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c');
 const blocked=setup();await assert.rejects(blocked.transport.write('MEM\n'));assert.equal(blocked.writes.length,0);
 assert.throws(()=>setup({...profile,image_sha256:'3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'}));
 const x=setup();await x.transport.write('PING\n');assert.equal(x.g.state.pongMatched,false);
 x.pedal.onLine('PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11');
 assert.equal(x.g.state.pongMatched,true);await x.transport.write('MEM\n');
 await assert.rejects(x.transport.write('GAIN 0 -1\n'));assert.deepEqual(x.writes,['PING\n','MEM\n']);
 console.log(JSON.stringify({passed:true,device_io:false}));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        done = subprocess.run([node, '-e', script, str(desk.GUARD), str(desk.EDITOR_REPORT)],
                              capture_output=True, text=True, check=True)
        result = json.loads(done.stdout); self.assertTrue(result['passed']); self.assertFalse(result['device_io'])


if __name__ == '__main__': unittest.main()
