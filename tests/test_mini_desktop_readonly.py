"""Temporary fake protocol evidence; never launches a browser or device."""
import argparse
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

from tools import launch_mini_desktop_readonly as desk
from tests.test_mini_app_mutation import Pedal

PORT={'device':'COM123','vid':0x3654,'pid':0x5155,'description':'TEST FIXTURE'}


class DesktopReadonlyTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(dir=desk.ROOT/'build',prefix='TEST-desktop-readonly-')
        self.addCleanup(temporary.cleanup);self.directory=Path(temporary.name)

    def boot(self,failed=False):
        result={'started_utc':'2020-01-01T00:00:00Z','finished_utc':'2020-01-01T00:00:01Z',
            'boot_mode':'normal-software-boot','buttons_confirmed_by_user':False,'buttons_assumed':'released',
            'held_button_boot_trial_performed':False,'cold_power_cycle_tested':False,'guard_causality_confirmed':False,
            'candidate_sha256':desk.browser.IMAGE_SHA,'application_USB_enumerated':True,'candidate_CDC_absent_before_reset':True,
            'reset_submitted':True,'firmware_write':False,'automatic_retry':False,'application_ports':[PORT],
            'phase':'application_PONG_verified','app_identity_verified':True,'serial_port_closed':True}
        if failed:result.update(phase='identify_application_PING',error_phase='identify_application_PING',
            error='TEST timeout',app_identity_verified=False,serial_port_closed=False)
        return result

    def ping(self):
        pedal=Pedal();path=self.directory/'ping.jsonl'
        desk.readonly.run_read(argparse.Namespace(firmware_manifest=desk.MANIFEST,log=path,port=PORT['device'],queries=[]),
                               enumerate_fn=lambda:[PORT],open_fn=lambda _:pedal,clock=pedal.clock)
        self.assertTrue(pedal.closed);return path

    def test_default_never_reads_evidence_or_starts_browser(self):
        with (patch.object(desk,'prepare',side_effect=AssertionError('evidence')),patch.object(desk,'run',side_effect=AssertionError('browser')),
              contextlib.redirect_stdout(io.StringIO()) as stream):
            self.assertEqual(desk.main([]),0)
        result=json.loads(stream.getvalue());self.assertFalse(result['device_io'] or result['browser_started'] or result['inputs_read'])

    def test_normal_boot_and_later_real_format_ping_are_separate(self):
        path=self.ping()
        for failed in (False,True):
            boot=self.boot(failed);port=desk.validate_normal_boot(boot)
            evidence=desk.validate_ping(path.read_bytes(),boot,port)
            self.assertEqual(evidence['com'],'COM123');self.assertTrue(evidence['serial_port_closed'])
            self.assertFalse(evidence['held_button_boot_trial_performed'] or evidence['cold_power_cycle_tested'])

    def test_first_handshake_prior_failed_ping_proves_close_only(self):
        rows=[json.loads(line) for line in self.ping().read_bytes().splitlines()]
        # An explicit failed diagnostic schema fixture: no PONG/identity is retained.
        rows=[row for row in rows if row['event'] not in ('rx','line','complete','identity_accepted','session_complete')]
        rows.insert(-1,{'event':'session_failed','error':'TEST timeout'})
        evidence=desk.validate_prior_close(self.ping_bytes(rows),self.boot(True),PORT)
        self.assertIsNone(evidence['pong']);self.assertFalse(evidence['identity_verified']);self.assertTrue(evidence['serial_port_closed'])
        with self.assertRaises(ValueError):desk.validate_prior_close(self.ping_bytes(rows[:-1]),self.boot(True),PORT)
        with self.assertRaises(ValueError):desk.validate_ping(self.ping_bytes(rows),self.boot(True),PORT)

    def test_boot_cannot_claim_held_or_skip_actual_CDC_observation(self):
        for field,value in [('buttons_confirmed_by_user','released'),('held_button_boot_trial_performed',True),
            ('application_USB_enumerated',False),('candidate_CDC_absent_before_reset',False),('candidate_sha256','0'*64),
            ('firmware_write',True),('application_ports',[PORT,PORT]),('finished_utc',None)]:
            boot=self.boot();boot[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):desk.validate_normal_boot(boot)
        boot=self.boot(True);boot['error_phase']='reset_once'
        with self.assertRaises(ValueError):desk.validate_normal_boot(boot)

    def test_ping_raw_replay_close_port_identity_and_failure_checks(self):
        rows=[json.loads(line) for line in self.ping().read_bytes().splitlines()]
        variants=[rows[:-1]]
        for event,key,value in [('port_selected','device','COM999'),('start','expected_image_sha256','0'*64),
            ('session_complete','commands',['PING','GAIN']),('identity_accepted','pong','PONG false')]:
            broken=copy.deepcopy(rows);next(x for x in broken if x['event']==event)[key]=value;variants.append(broken)
        broken=copy.deepcopy(rows);next(x for x in broken if x['event']=='rx')['hex']=b'WRONG\n'.hex();variants.append(broken)
        broken=copy.deepcopy(rows);broken.insert(-1,{'event':'session_failed'});variants.append(broken)
        broken=copy.deepcopy(rows);broken[0]['hardware_executed']=False;variants.append(broken)
        for index,items in enumerate(variants):
            with self.subTest(index=index),self.assertRaises((ValueError,desk.readonly.AppProbeError,desk.first.Error)):
                desk.validate_ping(b'\n'.join(json.dumps(row).encode() for row in items),self.boot(),PORT)
        boot=self.boot(True);boot['finished_utc']='2999-01-01T00:00:00Z'
        with self.assertRaises(ValueError):desk.validate_ping(self.ping_bytes(rows),boot,PORT)

    @staticmethod
    def ping_bytes(rows):return b'\n'.join(json.dumps(row).encode() for row in rows)

    def test_full_prepare_keeps_base_readonly_manifest_unchanged(self):
        ping=self.ping();boot=self.boot(True)
        install={'finished_utc':'2019-12-31T00:00:00Z','installed_image_verified':True,'full_NOR_verified':True,
            'installation':{'candidate_sha256':desk.browser.IMAGE_SHA},
            'independent_full_validation':{'external_regions_unchanged':True,'full_NOR_sha256':desk.FULL_SHA}}
        install_path=self.directory/'install.json';install_path.write_text(json.dumps(install))
        boot.update(source_pins={'tools/probe_mini_app.py':desk.sha(Path(desk.readonly.__file__).read_bytes())},
            installation_evidence_path=desk.ref(install_path)['path'],installation_evidence_sha256=desk.ref(install_path)['sha256'])
        boot_path=self.directory/'boot.json';boot_path.write_text(json.dumps(boot))
        before=desk.MANIFEST.read_bytes()
        result=desk.prepare(boot_path,desk.sha(boot_path.read_bytes()),ping,desk.sha(ping.read_bytes()))
        self.assertTrue(result['boot_observation_had_PING_error']);self.assertFalse(result['profile']['hardware_verified'])
        self.assertEqual(desk.MANIFEST.read_bytes(),before);self.assertFalse(result['profile']['capabilities']['write'])

    def test_browser_is_visible_isolated_and_local(self):
        args=desk.browser_arguments('chrome.exe',self.directory/'new-profile')
        self.assertFalse(any('headless' in arg for arg in args));self.assertIn('--app=about:blank',args)
        self.assertIn('--remote-debugging-address=127.0.0.1',args)
        self.assertIn('--user-data-dir='+str(self.directory/'new-profile'),args)

    def test_native_close_success_is_required_not_just_transport_null(self):
        class FakeCDP:
            def __init__(self,value):self.value=value
            def evaluate(self,expression):
                self.expression=expression;return self.value
        for raw,expected in [({'open':False,'closes':1,'closeError':None},True),
                             ({'open':False,'closes':0,'closeError':None},False),
                             ({'open':False,'closes':1,'closeError':'failed'},False)]:
            fake=FakeCDP(raw);self.assertEqual(desk.close_serial(fake)['native_close_verified'],expected)
            self.assertNotIn('Pedal.cmd',fake.expression)

    def test_browser_start_failure_shuts_server_without_device(self):
        calls=[]
        class Server:
            server_port=12345
            def __init__(self,*args,**kwargs):pass
            def serve_forever(self):calls.append('serve')
            def shutdown(self):calls.append('shutdown')
            def server_close(self):calls.append('server_close')
        prepared={'inputs':{'normal_boot':{'path':'unused','sha256':'0'*64},'PING':{'path':'unused','sha256':'0'*64}}}
        with (patch.object(desk,'prepare',return_value=prepared),patch.object(desk.http.server,'ThreadingHTTPServer',Server),
              patch.object(desk.browser,'browser_path',side_effect=ValueError('TEST no browser'))):
            result=desk.run(prepared,self.directory/'session')
        self.assertEqual(result['phase'],'connection_failed');self.assertTrue(result['local_server_stopped'])
        self.assertEqual(calls,['serve','shutdown','server_close'])

    def test_close_request_is_only_a_new_local_file(self):
        output=self.directory/'active';output.mkdir()
        (output/'session.json').write_text(json.dumps({'kind':'mini-desktop-readonly-session'}))
        with patch.object(desk,'run',side_effect=AssertionError('browser')),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(desk.main(['--close-session',str(output)]),0)
        self.assertTrue((output/'close.request').is_file())
        with self.assertRaises(FileExistsError):desk.main(['--close-session',str(output)])

    def test_guard_serial_is_fake_and_queries_remain_bounded(self):
        node=shutil.which('node');self.assertIsNotNone(node)
        result=subprocess.run([node,str(desk.ROOT/'tests/mini_desktop_readonly_guard_test.js'),str(desk.GUARD)],
                              capture_output=True,text=True,check=True)
        parsed=json.loads(result.stdout);self.assertGreaterEqual(parsed['checks'],50)
        self.assertFalse(parsed['device_io'] or parsed['browser_started'])


if __name__=='__main__':unittest.main()
