"""Offline UI copy/old-evidence/new-runtime adapter checks, no device I/O."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import run_mini_v3_first_preset_ui_v3 as driver
from tools import probe_mini_browser_first_preset as trial


class FirstPresetUIV3Tests(unittest.TestCase):
    def test_default_does_not_read_or_start_browser(self):
        with patch.object(driver,'verify_dependencies',side_effect=AssertionError('read')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(driver.main([]),0)
        self.assertFalse(json.loads(out.getvalue())['device_io'])

    def test_only_mini_UI_file_differs_in_actual_derived_copy(self):
        value=driver.validate_ui_copy()
        changed=[name for name in driver.BASE_FILES if (driver.OLD_APP/name).read_bytes()!=(driver.NEW_APP/name).read_bytes()]
        self.assertEqual(changed,['mini-ui.js']);self.assertEqual(value,driver.description())
        self.assertEqual((driver.NEW_APP/'mini-ui.js').read_bytes(),driver.UI_SOURCE.read_bytes())
        self.assertFalse(value['protocol_or_capabilities_changed'] or value['focus_guard_changed'])

    def test_original_setLock_failure_and_preserved_node_fix(self):
        node=shutil.which('node')
        if not node:self.skipTest('existing Node unavailable; no installation')
        result=subprocess.run([node,str(driver.ROOT/'tests/mini_ui_v2_setlock_test.js'),
            str(driver.OLD_APP/'tankmini.html'),str(driver.OLD_APP/'mini-ui.js'),str(driver.UI_SOURCE)],
            capture_output=True,text=True,check=True)
        value=json.loads(result.stdout);self.assertEqual(value['result'],'pass');self.assertGreaterEqual(value['checks'],17)
        self.assertTrue(value['original_UI_failure_reproduced'] and value['original_nodes_preserved'])
        self.assertFalse(value['device_io'] or value['browser_started'])

    def test_historical_prepare_uses_old_app_then_runtime_and_sources_use_new(self):
        calls=[]
        desktop=SimpleNamespace(APP=driver.OLD_APP)
        def old_prepare(**refs):calls.append(desktop.APP);return {'inputs':refs,'app_directory':'old','profile':{'write':False}}
        old_writer=lambda *args,**kwargs:None
        fake=SimpleNamespace(desktop=desktop,prepare=old_prepare,atomic_write_json=old_writer)
        with driver.ui_adapter(fake):
            self.assertEqual(desktop.APP,driver.NEW_APP)
            prepared=fake.prepare(boot={'exact':'ref'})
            self.assertEqual(calls,[driver.OLD_APP]);self.assertEqual(desktop.APP,driver.NEW_APP)
            self.assertEqual(prepared['app_directory'],driver.NEW_APP.relative_to(driver.ROOT).as_posix())
            self.assertEqual(prepared['profile'],{'write':False})
        self.assertEqual(desktop.APP,driver.OLD_APP);self.assertIs(fake.prepare,old_prepare);self.assertIs(fake.atomic_write_json,old_writer)
        with self.assertRaises(RuntimeError),driver.ui_adapter(fake):raise RuntimeError('test')
        self.assertEqual(desktop.APP,driver.OLD_APP);self.assertIs(fake.prepare,old_prepare)

    def test_report_keeps_truthful_base_and_served_sources(self):
        report={'kind':'mini-browser-first-preset-v3-trial','prepared':{'exact':True},'source_sha256':{}}
        original=copy.deepcopy(report);written=[]
        driver.annotated_writer(lambda path,value:written.append(value),'a'*64)('new.json',report)
        value=written[0];self.assertEqual(report,original)
        self.assertEqual(value['ui_compatibility_extension'],driver.description())
        self.assertEqual(value['source_sha256'][driver.SOURCE_NAME],'a'*64)
        self.assertEqual(value['source_sha256'][driver.UI_SOURCE.relative_to(driver.ROOT).as_posix()],driver.UI_SHA)
        for name,digest in driver.BASE_FILES.items():
            self.assertEqual(value['source_sha256'][(driver.OLD_APP/name).relative_to(driver.ROOT).as_posix()],digest)

    def test_actual_historical_refs_preflight_with_new_runtime_app(self):
        refs={'boot':('analysis/hardware/mini-first-boot-v11-released-run.json','8b91a906bd061952938ce54930eb8d5e0956ace4c4d4465fd8a57da735d88202'),
              'connected':('build/mini-desktop-v3-real-02/connected-proof.json','2fbf2463f86d7d72017f5127af83334e7c2fcd41d8c5bc74c7f2710dda16950a'),
              'session':('build/mini-desktop-v3-real-02/session.json','d4d6f052a2e042664a52fa117c514afd6c457447e9e308a9738e6725e394f22f')}
        args=['--check-only']
        for key,(path,digest) in refs.items():args+=['--'+key,str(driver.ROOT/path),'--'+key+'-sha256',digest]
        original=(trial.desktop.APP,trial.prepare,trial.GUARD,trial.atomic_write_json,trial.evidence.validate_v3_browser_evidence)
        with patch.object(trial,'run',side_effect=AssertionError('browser/device')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(driver.main(args),0)
        self.assertEqual(json.loads(out.getvalue())['preflight'],'pass')
        self.assertEqual((trial.desktop.APP,trial.prepare,trial.GUARD,trial.atomic_write_json,trial.evidence.validate_v3_browser_evidence),original)


if __name__=='__main__':unittest.main()
