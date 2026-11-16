"""Offline exact-file exception/delegation checks; never starts a browser."""
import contextlib
import copy
import inspect
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import run_mini_v3_editor as driver
from tools.mini_host_journal import read_shared_bytes


class EditorDriverTests(unittest.TestCase):
    def test_default_does_not_import_delegate_or_read_evidence(self):
        with (patch.object(driver,'modules',side_effect=AssertionError('delegate')),
              contextlib.redirect_stdout(io.StringIO()) as stream):
            self.assertEqual(driver.main([]),0)
        data=json.loads(stream.getvalue())
        self.assertFalse(data['device_io'] or data['browser_started'] or data['inputs_read'])

    def test_two_actual_closed_traces_require_exact_size_and_hash(self):
        reader=driver.ExactTraceReader(read_shared_bytes)
        for name,expected in driver.EXACT_TRACES.items():
            raw=reader(driver.ROOT/name)
            self.assertEqual(len(raw),expected['bytes']);self.assertEqual(driver.sha(raw),expected['sha256'])
            self.assertEqual(reader.verified_reads[name],1)

    def test_wrong_hash_truncated_and_extra_bytes_rejected_for_each_trace(self):
        for name,expected in driver.EXACT_TRACES.items():
            for kind in ('hash','truncated','extra'):
                size=expected['bytes']+{'hash':0,'truncated':-1,'extra':1}[kind]
                calls=[]
                def fake(path,**kwargs):calls.append(kwargs);return b'X'*size
                reader=driver.ExactTraceReader(fake)
                with self.subTest(name=name,kind=kind),self.assertRaises(ValueError):reader(driver.ROOT/name)
                self.assertEqual(calls,[{'maximum':32*1024*1024}]);self.assertEqual(reader.verified_reads[name],0)

    def test_other_reads_keep_original_default_and_explicit_bounds(self):
        self.assertEqual(inspect.signature(read_shared_bytes).parameters['maximum'].default,8*1024*1024)
        calls=[]
        def original(path,**kwargs):calls.append((path,kwargs));return b'unchanged'
        reader=driver.ExactTraceReader(original)
        name=driver.ROOT/'other-trace.jsonl'
        self.assertEqual(reader(name),b'unchanged')
        self.assertEqual(reader(name,maximum=7),b'unchanged')
        self.assertEqual(calls,[(name,{}),(name,{'maximum':7})])
        with self.assertRaises(ValueError):reader(driver.ROOT/next(iter(driver.EXACT_TRACES)),maximum=7)

    def test_identical_filename_elsewhere_does_not_gain_exception(self):
        calls=[]
        def original(path,**kwargs):calls.append(kwargs);raise ValueError('original size bound')
        name=driver.ROOT/'build'/Path(next(iter(driver.EXACT_TRACES))).name
        with self.assertRaises(ValueError):driver.ExactTraceReader(original)(name)
        self.assertEqual(calls,[{}])

    def test_report_annotation_preserves_frozen_inputs_and_records_driver(self):
        publications=[]
        original=lambda path,value,**kwargs:publications.append((path,value,kwargs))
        reader=driver.ExactTraceReader(lambda path:b'')
        report={'kind':'mini-desktop-readonly-v3-session','evidence':{'inputs':{'unchanged':True}},
                'source_sha256':{'frozen.py':'b'*64}}
        before=copy.deepcopy(report)
        driver.annotated_writer(original,reader,'a'*64)('new/session.json',report,attempts=3)
        self.assertEqual(report,before)
        published=publications[0][1]
        self.assertEqual(published['evidence'],before['evidence'])
        self.assertEqual(published['source_sha256'][driver.SOURCE_NAME],'a'*64)
        self.assertEqual(published['source_sha256']['frozen.py'],'b'*64)
        self.assertEqual(published['evidence_io_extension']['unchanged_other_default_maximum_bytes'],8*1024*1024)
        self.assertEqual(publications[0][2],{'attempts':3})
        with self.assertRaises(ValueError):driver.annotated_writer(original,reader,'a'*64)('old.json',published)

    def test_local_module_references_restore_even_on_failure(self):
        original_reader=lambda path:b'x';original_writer=lambda *a,**k:None
        desktop=SimpleNamespace(read_shared_bytes=original_reader,atomic_write_json=original_writer)
        delegated=SimpleNamespace(atomic_write_json=original_writer)
        with self.assertRaisesRegex(RuntimeError,'test'):
            with driver.evidence_io_adapter(desktop,delegated):
                self.assertIsInstance(desktop.read_shared_bytes,driver.ExactTraceReader)
                self.assertIs(desktop.atomic_write_json,original_writer)
                self.assertIsNot(delegated.atomic_write_json,original_writer)
                raise RuntimeError('test')
        self.assertIs(desktop.read_shared_bytes,original_reader)
        self.assertIs(delegated.atomic_write_json,original_writer)

    def test_actual_boot_preflight_delegates_without_browser_or_device(self):
        from tools import launch_mini_desktop_v3 as desktop
        boot=driver.ROOT/'analysis/hardware/mini-first-boot-v11-released-run.json'
        expected='8b91a906bd061952938ce54930eb8d5e0956ace4c4d4465fd8a57da735d88202'
        self.assertEqual(driver.sha(read_shared_bytes(boot)),expected)
        with (patch.object(desktop,'run',side_effect=AssertionError('browser')),
              contextlib.redirect_stdout(io.StringIO()) as stream):
            result=driver.main(['desktop','--check-only','--boot-run',str(boot),'--boot-sha256',expected])
        self.assertEqual(result,0);data=json.loads(stream.getvalue())
        self.assertEqual(data['preflight'],'pass');self.assertEqual(data['evidence']['com'],'COM3')
        self.assertFalse(data['device_io'] or data['browser_started'])
        self.assertIs(desktop.read_shared_bytes,read_shared_bytes)

    def test_trial_and_validator_share_only_the_desktop_reader_adapter(self):
        desktop,trial=driver.modules('first-preset')
        direct_trial,validator=trial.read_shared_bytes,trial.evidence.read_shared_bytes
        with driver.evidence_io_adapter(desktop,trial):
            self.assertIs(trial.desktop.read_shared_bytes,trial.evidence.desktop.read_shared_bytes)
            self.assertIs(trial.read_shared_bytes,direct_trial)
            self.assertIs(trial.evidence.read_shared_bytes,validator)


if __name__=='__main__':unittest.main()
