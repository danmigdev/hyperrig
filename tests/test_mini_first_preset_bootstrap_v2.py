"""Offline bootstrap regression using original editor code; no browser/device."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from tools import run_mini_v3_first_preset_a2_v2 as adapter
from tools import probe_mini_browser_first_preset as trial
from tools.mini_host_journal import read_shared_bytes


class FirstPresetBootstrapV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = shutil.which('node')
        if not node: raise unittest.SkipTest('existing Node unavailable; no installation')
        def run(script, *args):
            result = subprocess.run([node,str(adapter.ROOT/script),*map(str,args)],capture_output=True,text=True)
            if result.returncode:
                raise AssertionError(result.stderr[-4000:])
            return json.loads(result.stdout)
        cls.bootstrap = run('tests/mini_browser_first_preset_bootstrap_v2_test.js', adapter.GUARD,
            trial.desktop.APP/'tankmini.html',trial.desktop.APP/'mini-profile.js')
        cls.sequence = run('tests/mini_browser_first_preset_guard_test.js',adapter.GUARD,
            trial.desktop.APP/'tankmini.html',trial.BLOB,'--emit-success')

    def test_default_has_no_evidence_device_or_browser_activity(self):
        with (patch.object(adapter,'verify_dependencies',side_effect=AssertionError('read')),
              patch.object(adapter.base,'main',side_effect=AssertionError('delegate')),
              contextlib.redirect_stdout(io.StringIO()) as out):
            self.assertEqual(adapter.main([]),0)
        result=json.loads(out.getvalue())
        self.assertFalse(result['device_io'] or result['browser_started'] or result['inputs_read'])
        self.assertFalse(result['BLE_key_on_wire_allowed'] or result['profile_modified'])

    def test_original_policy_queue_and_USB_bootstrap_continue_after_local_denial(self):
        result=self.bootstrap
        self.assertEqual(result['result'],'pass');self.assertGreaterEqual(result['checks'],22)
        self.assertEqual(result['bootstrap_wire'],['PING','BLE','FXT'])
        self.assertEqual(result['BLE_key_wire_count'],0)
        self.assertTrue(result['fake_native_serial_only'])
        self.assertFalse(result['device_io'] or result['browser_started'])
        self.assertIn('Pedal.cmd',result['original_functions'])
        self.assertIn('connect USB BLE branch',result['original_functions'])

    def test_original_complete_UI_sequence_and_native_RX_verifier_still_pass(self):
        self.assertEqual(self.sequence['result'],'pass')
        self.assertGreaterEqual(self.sequence['checks'],69)
        verified=trial.verify_wire(self.sequence['guard'])
        self.assertTrue(verified['completed_commands_checked_against_native_RX'])
        self.assertFalse(any(x['line']=='BLE key' for x in self.sequence['guard']['wire']))

    def test_historical_trial_failed_before_mutation_and_is_not_rewritten(self):
        raw=read_shared_bytes(adapter.ROOT/adapter.FAILURE_REFERENCE['path'])
        self.assertEqual(adapter.sha(raw),adapter.FAILURE_REFERENCE['sha256'])
        report=json.loads(raw);guard=report['guard']
        self.assertEqual(report['result'],'fail')
        self.assertFalse(report['ui_roundtrip_verified'] or report['save_reload_verified'])
        self.assertEqual([x['line'] for x in guard['wire']],['PING','BLE'])
        local=next(x for x in guard['commands'] if x['line']=='BLE key')
        self.assertIsNone(local['wire_id']);self.assertEqual(local['lines'],[adapter.LOCAL_REPLY])
        self.assertEqual(guard['captureMutations'],0);self.assertEqual(guard['mutations'],0)
        self.assertTrue(report['serial_port_closed']);self.assertEqual(guard['closes'],1)

    def test_pin_checks_leave_frozen_sources_exact_and_reject_changed_guard(self):
        adapter.verify_dependencies()
        with patch.object(adapter,'GUARD_SHA','0'*64),self.assertRaisesRegex(ValueError,'dependency changed'):
            adapter.verify_dependencies()
        self.assertEqual(adapter.sha(adapter.BASE_GUARD.read_bytes()),adapter.BASE_GUARD_SHA)
        self.assertEqual(adapter.sha(Path(adapter.base.__file__).read_bytes()),adapter.BASE_SHA)

    def test_report_records_actual_local_events_without_grants_or_input_changes(self):
        local={'kind':'local_editor_policy_rejection','line':'BLE key','lines':[adapter.LOCAL_REPLY],
               'local_only':True,'wire_command_observed':False,'seq':12}
        report={'kind':'mini-browser-first-preset-v3-trial','hardware_executed':False,
            'guard':{'events':[local]},'source_sha256':{},
            'profile':{'hardware_verified':False,'capabilities':{'write':False}},
            'general_capabilities_granted':{}}
        before=copy.deepcopy(report);published=[]
        writer=adapter.annotated_writer(lambda path,value,**kw:published.append((path,value,kw)),'a'*64)
        writer('new/report.json',report,attempts=2)
        value=published[0][1]
        self.assertEqual(report,before);self.assertEqual(value['profile'],before['profile'])
        self.assertFalse(value['hardware_executed']);self.assertEqual(value['general_capabilities_granted'],{})
        extension=value['bootstrap_guard_extension']
        self.assertEqual(extension.pop('observed_local_rejections'),[local])
        self.assertEqual(extension,adapter.description())
        self.assertEqual(value['source_sha256'][adapter.SOURCE_NAME],'a'*64)
        self.assertEqual(value['source_sha256'][adapter.GUARD.relative_to(adapter.ROOT).as_posix()],adapter.GUARD_SHA)
        with self.assertRaises(ValueError):writer('new/report.json',value)

    def test_nested_delegation_restores_every_adapter_after_failure(self):
        args=['--check-only','--boot','unread-fixture.json']
        old=(trial.GUARD,trial.atomic_write_json,trial.snapshot,trial.verify_processing_progress,
             trial.desktop.read_shared_bytes,trial.evidence.validate_v3_browser_evidence)
        def failed(received):
            self.assertEqual(received,args);self.assertEqual(trial.GUARD,adapter.GUARD)
            self.assertIsNot(trial.snapshot,old[2]);self.assertIsNot(trial.verify_processing_progress,old[3])
            raise RuntimeError('offline preflight fixture')
        with patch.object(trial,'main',side_effect=failed),self.assertRaises(RuntimeError):adapter.main(args)
        new=(trial.GUARD,trial.atomic_write_json,trial.snapshot,trial.verify_processing_progress,
             trial.desktop.read_shared_bytes,trial.evidence.validate_v3_browser_evidence)
        self.assertEqual(new,old)

    def test_real_closed_v3_preflight_reads_evidence_only(self):
        refs={
            'boot':('analysis/hardware/mini-first-boot-v11-released-run.json',
                    '8b91a906bd061952938ce54930eb8d5e0956ace4c4d4465fd8a57da735d88202'),
            'connected':('build/mini-desktop-v3-real-02/connected-proof.json',
                         '2fbf2463f86d7d72017f5127af83334e7c2fcd41d8c5bc74c7f2710dda16950a'),
            'session':('build/mini-desktop-v3-real-02/session.json',
                       'd4d6f052a2e042664a52fa117c514afd6c457447e9e308a9738e6725e394f22f')}
        args=['--check-only']
        for name,(path,digest) in refs.items():args.extend(['--'+name,path,'--'+name+'-sha256',digest])
        with patch.object(trial,'run',side_effect=AssertionError('browser/device')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(adapter.main(args),0)
        result=json.loads(out.getvalue())
        self.assertEqual(result['preflight'],'pass')
        self.assertFalse(result['device_io'] or result['browser_started'])


if __name__=='__main__':unittest.main()
