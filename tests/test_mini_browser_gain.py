"""Offline tests. Physical-schema fixtures are fake, temporary and never retained."""
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

from tools import probe_mini_browser_gain as gain
from tools import qualify_mini_app as q
from tools import probe_mini_app_first_preset as first
from tools import build_mini_app as app
from tests.test_mini_app_first_preset import FirstPedal


class BrowserGainTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=gain.ROOT/'build', prefix='TEST-browser-gain-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def fixture(self):
        proof_path = self.directory/'read-proof.json'
        proof = {'kind':'mini-app-usb-read-qualification', 'boot_USB_read_verified':True, 'image_sha256':q.IMAGE_SHA,
            'evidence':{k:q.reference(q.BASE) for k in ('installation','held','released','read_log')},
            'implementation':q.reference(Path(q.__file__)), 'base_manifest':q.reference(q.BASE),
            'verifier_sources':[q.reference(Path(m.__file__)) for m in (q.installed,q.readonly,first,q.mutation,app)]}
        q.write_new(proof_path, proof)
        spec=json.loads(q.BASE.read_bytes());spec['hardware_verified']=True;spec['hardware_validation']=q.reference(proof_path)
        read_manifest=self.directory/'read-manifest.json';q.write_new(read_manifest,spec)
        pedal=FirstPedal(empty_chain=True)
        args=argparse.Namespace(firmware_manifest=read_manifest,port='COM123',slot=0,operation='auto',block=None,parameter=None,
            log=self.directory/'first.jsonl',backup=self.directory/'before.json',report=self.directory/'first.json')
        result=first.run_create(args,enumerate_fn=lambda:[{'device':'COM123','vid':0x3654,'pid':0x5155}],
                               open_fn=lambda _:pedal,clock=pedal.clock)
        self.assertFalse(result['hardware_executed'])
        # Temporary schema fixture only: no mocked result is published as physical proof.
        rows=[json.loads(line) for line in args.log.read_bytes().splitlines()]
        rows[0]['hardware_executed']=True
        args.log.write_bytes(b'\n'.join(json.dumps(row).encode() for row in rows)+b'\n')
        backup=json.loads(args.backup.read_bytes());backup['hardware_executed']=True
        args.backup.write_text(json.dumps(backup))
        result=first.first_evidence(result['trial'],app.load_profile(read_manifest),trace=q.reference(args.log),
            backup=q.reference(args.backup),hardware_executed=True)
        args.report.write_text(json.dumps(result))
        manifest=self.directory/'families.json';q.qualify_families(read_manifest,[args.report],manifest)
        profile=app.load_profile(manifest)
        app_dir=self.directory/'web';app_dir.mkdir()
        source=app.checked(app.SOURCE/'web/tankg.html',app.SOURCE_SHA).decode('utf-8')
        html,_=app.derive_html(source,profile);(app_dir/'tankmini.html').write_bytes(html.encode())
        for name in ('mini-profile.js','mini-ui.js'):
            (app_dir/name).write_bytes((gain.ROOT/'app/mini'/name).read_bytes())
        (app_dir/'nam2chip.js').write_bytes(app.rename_text(app.checked(app.SOURCE/'web/nam2chip.js',app.CONVERTER_SHA).decode()).encode())
        evidence={'schema':1,'target':'tank-mini','transport':'usb-cdc','vid':0x3654,'pid':0x5155,
            'com':'COM123','pong':'PONG tankm_fw M5.71 rel ble Nov 15 2026 20:00:00','image_sha256':q.IMAGE_SHA,
            'serial_port_closed':True,'observed_utc':'2026-11-16T00:00:00Z','qualification':q.reference(proof_path)}
        evidence_path=self.directory/'browser.json';q.write_new(evidence_path,evidence)
        return {'manifest':manifest,'family_report':args.report,'evidence_path':evidence_path,
                'evidence_sha256':gain.sha(evidence_path.read_bytes()),'app_dir':app_dir}

    def test_default_does_not_read_evidence_start_server_or_browser(self):
        with (patch.object(gain,'prepare',side_effect=AssertionError('inputs read')),
              patch.object(gain,'run',side_effect=AssertionError('browser')),contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(gain.main([]),0)
        result=json.loads(output.getvalue())
        self.assertFalse(result['device_io'] or result['browser_started'] or result['inputs_read'])
        self.assertEqual(result['persistent_commands'],[])

    def test_full_fixture_preflight_raw_replay_and_exact_generated_app(self):
        inputs=self.fixture()
        prepared=gain.prepare(**inputs)
        self.assertEqual(prepared['baseline']['gain'],[0,0])
        self.assertEqual(prepared['planned_mutations'],['GAIN 0 -1','GAIN 0 0'])
        self.assertFalse(prepared['profile']['capabilities']['write'])
        args=['--check-only','--firmware-manifest',str(inputs['manifest']),'--family-report',str(inputs['family_report']),
              '--evidence',str(inputs['evidence_path']),'--evidence-sha256',inputs['evidence_sha256'],'--app-dir',str(inputs['app_dir'])]
        with patch.object(gain,'run',side_effect=AssertionError('browser')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(gain.main(args),0)
        self.assertFalse(json.loads(out.getvalue())['device_io'])

    def test_stale_app_cannot_bypass_new_profile(self):
        inputs=self.fixture();path=inputs['app_dir']/'tankmini.html'
        path.write_bytes(path.read_bytes()+b'\n<!-- modified -->')
        with self.assertRaisesRegex(ValueError,'exact generated'):gain.prepare(**inputs)

    def test_wrong_qualification_or_open_port_blocks_before_browser(self):
        inputs=self.fixture()
        for field,value in [('qualification',q.reference(q.BASE)),('serial_port_closed',False),('com','COM0')]:
            evidence=json.loads(inputs['evidence_path'].read_bytes());evidence[field]=value
            inputs['evidence_path'].write_text(json.dumps(evidence))
            inputs['evidence_sha256']=gain.sha(inputs['evidence_path'].read_bytes())
            with self.subTest(field=field),self.assertRaises(ValueError):gain.prepare(**inputs)

    def test_changed_first_trace_is_rejected_by_original_replay(self):
        inputs=self.fixture();report=json.loads(inputs['family_report'].read_bytes())
        trace=gain.ROOT/report['trace']['path'];trace.write_bytes(trace.read_bytes().replace(b'4741494e',b'4741494f',1))
        with self.assertRaises(ValueError):gain.prepare(**inputs)

    def test_baseline_blocks_unqualified_mock_low_output_or_unretained_preset(self):
        inputs=self.fixture();spec=json.loads(inputs['manifest'].read_bytes());profile=app.load_profile(inputs['manifest'])
        report=json.loads(inputs['family_report'].read_bytes());ref=gain.reference(inputs['family_report'])
        changes=[('hardware_executed',False),('final_sound_verified',False),('preset_intentionally_retained',False),
                 ('transport','ble-nus'),('physically_exercised_requests',{}),('simulated_requests',{'GAIN':['GAIN 0 -1']})]
        for key,value in changes:
            broken=copy.deepcopy(report);broken[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):gain.validate_family_baseline(spec,profile,broken,ref)
        for value in (-30,13,False):
            broken=copy.deepcopy(report);broken['trial']['final_state']['extra']['gain_db'][1]=value
            with self.subTest(value=value),self.assertRaises(ValueError):gain.validate_family_baseline(spec,profile,broken,ref)
        for field,value in [('phase','failed'),('roundtrip_passed',False)]:
            broken=copy.deepcopy(report);broken['trial'][field]=value
            with self.assertRaises(ValueError):gain.validate_family_baseline(spec,profile,broken,ref)
        with self.assertRaises(ValueError):gain.validate_family_baseline(spec,profile,report,{'path':'different','sha256':'0'*64})

    def responses(self):
        return {'GAIN':['GAIN in=0 out=0 dB'],'LVL':['LVL in=-700 out=-800 g=0/0 amp=0'],
                'FXS':['FXS amp=0 on=0','FXS cpu=10/100 ticks (10%) mem_fx=0 B','FXS peak=5 ticks skipped=0'],
                'PLIST':["PRE 0 0 -1 -1 'HyperRig_Test' t=- s=1 amp=0",'PLIST end current=0'],
                'SNAPS':['SNAPS 1000 current=0']}

    def test_fresh_read_requires_real_gain_lvl_and_complete_metadata(self):
        original=self.responses();parsed=gain.parse_snapshot(original)
        gain.verify_snapshot(parsed,parsed,[0,0])
        for key,lines in [('GAIN',['GAIN in=0 out=1 dB']),('LVL',['LVL in=0 out=0']),
                          ('FXS',['FXS amp=0 on=0']),('PLIST',['PLIST end current=1']),('SNAPS',['SNAPS 0000 current=0'])]:
            broken=copy.deepcopy(original);broken[key]=lines
            with self.subTest(key=key),self.assertRaises((ValueError,mutation_error())):gain.parse_snapshot(broken)

    def test_gain_step_cannot_change_chain_inventory_or_scene(self):
        baseline=gain.parse_snapshot(self.responses())
        for key in ('fxs','plist','snaps'):
            changed=copy.deepcopy(baseline);changed[key]['unexpected']=True
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'unrelated state'):gain.verify_snapshot(changed,baseline,[0,0])
        with self.assertRaises(ValueError):gain.verify_snapshot(baseline,baseline,[0,-1])

    def test_ui_step_uses_only_focus_arm_and_native_keyboard_events(self):
        class FakeCDP:
            def __init__(self):self.expressions=[];self.calls=[]
            def evaluate(self,text):
                self.expressions.append(text)
                return {'guard':{'fatal':None,'phase':'down_ack'},'gainPending':0} if text==gain.STATE else None
            def call(self,name,args):self.calls.append((name,args))
        fake=FakeCDP();gain.ui_step(fake,'down',1)
        self.assertIn('.focus()',fake.expressions[0]);self.assertEqual(fake.expressions[1],'__miniGainGuard.arm("down")')
        self.assertEqual([args['type'] for name,args in fake.calls],['keyDown','keyUp'])
        self.assertTrue(all(name=='Input.dispatchKeyEvent' and args['key']=='ArrowDown' and args['windowsVirtualKeyCode']==40
                            for name,args in fake.calls))
        self.assertFalse(any('Pedal.cmd' in expression or 'S.gain=' in expression for expression in fake.expressions))

    def test_javascript_guard_fake_serial_and_events(self):
        node=shutil.which('node');self.assertIsNotNone(node,'existing Node required; no installation')
        result=subprocess.run([node,str(gain.ROOT/'tests/mini_browser_gain_guard_test.js'),str(gain.GUARD)],
                              check=True,capture_output=True,text=True)
        value=json.loads(result.stdout);self.assertEqual(value['result'],'pass')
        self.assertGreaterEqual(value['checks'],120);self.assertFalse(value['device_io'] or value['browser_started'])


def mutation_error():
    return gain.mutation.Error


if __name__=='__main__':unittest.main()
