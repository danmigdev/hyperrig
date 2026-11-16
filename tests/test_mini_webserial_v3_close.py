"""Offline validation of the exact redundant CDP-close observation race."""
import contextlib
import copy
import io
import json
from pathlib import Path
from unittest.mock import patch
import unittest

from tests import test_mini_webserial_v3_evidence as previous
from tools import validate_mini_webserial_v3_close as closed
from tools import run_mini_v3_first_preset_a2 as driver
from tools import probe_mini_browser_first_preset as trial
from tools.mini_host_journal import read_shared_bytes


class ClosedEvidenceTests(previous.WebSerialEvidenceTests):
    def validate(self):
        connected_path=self.folder/'connected-proof.json';session_path=self.folder/'session.json'
        connected_path.write_text(json.dumps(self.connected));session_path.write_text(json.dumps(self.session))
        with patch.object(closed.desktop,'prepare',return_value=self.prepared):
            return closed.validate_v3_browser_evidence(boot=self.boot_ref,
                connected=self.ref(connected_path),session=self.ref(session_path))

    def race(self):
        self.session['final_close_observation_error']=closed.EXACT_POST_CLOSE_ERROR
        self.session['close_requested_utc']='2020-01-01T00:00:03.6Z'
        (self.folder/'close.request').write_text('2020-01-01T00:00:03.5Z\n')

    def test_exact_post_close_error_is_retained_with_actual_close_provenance(self):
        self.race();before=copy.deepcopy(self.session)
        result=self.validate();note=result['desktop_close_observation']
        self.assertEqual(self.session,before)
        self.assertEqual(note['original_error'],closed.EXACT_POST_CLOSE_ERROR)
        self.assertTrue(note['original_report_preserved']);self.assertFalse(note['native_close_inferred_from_CDP_loss'])
        self.assertEqual(result['references']['session'],self.ref(self.folder/'session.json'))
        self.assertEqual(note['close_request']['sha256'],self.ref(self.folder/'close.request')['sha256'])
        self.assertFalse(result['profile']['capabilities']['write'] or result['audio_verified'])

    def test_missing_native_close_or_guard_stop_never_qualifies(self):
        self.race();baseline=copy.deepcopy(self.session)
        for fault in ('native','open','count','nativeerror','event','stopped','fatal','stop_event','event_time','write_after'):
            self.session=copy.deepcopy(baseline)
            if fault=='native':self.session['disconnect']['native_close_verified']=False
            elif fault=='open':self.session['disconnect']['open']=True
            elif fault=='count':self.session['last_guard']['closes']=0
            elif fault=='nativeerror':self.session['disconnect']['closeError']='failure'
            elif fault=='event':self.session['last_guard']['events'].pop(6)
            elif fault=='stopped':self.session['last_guard']['stopped']=False
            elif fault=='fatal':self.session['last_guard']['fatal']='guard failure'
            elif fault=='stop_event':self.session['last_guard']['events'].pop()
            elif fault=='event_time':self.session['last_guard']['events'][-1]['time']=29
            else:self.session['last_guard']['wire'][-1]['finished']=33
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.validate()

    def test_all_other_errors_are_rejected_even_with_proved_native_close(self):
        self.race();baseline=copy.deepcopy(self.session)
        for key in closed.OTHER_ERRORS:
            self.session=copy.deepcopy(baseline);self.session[key]='real other failure'
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate()
        for error in ('TimeoutError()',closed.EXACT_POST_CLOSE_ERROR+' extra',"WebSocketConnectionClosedException('other')"):
            self.session=copy.deepcopy(baseline);self.session['final_close_observation_error']=error
            with self.subTest(error=error),self.assertRaises(ValueError):self.validate()

    def test_close_request_is_real_local_complete_and_chronological(self):
        for fault in ('missing','late','early','multiline','no_request_time'):
            self.race()
            if fault=='missing':(self.folder/'close.request').unlink()
            elif fault=='late':(self.folder/'close.request').write_text('2020-01-01T00:00:05Z\n')
            elif fault=='early':(self.folder/'close.request').write_text('2019-01-01T00:00:00Z\n')
            elif fault=='multiline':(self.folder/'close.request').write_text('2020-01-01T00:00:03.5Z\nextra\n')
            else:self.session['close_requested_utc']='2020-01-01T00:00:01Z'
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.validate()

    def test_clean_session_keeps_previous_interpretation_without_close_request(self):
        result=self.validate()
        self.assertIsNone(result['desktop_close_observation'])


class RealClosedPreflightTests(unittest.TestCase):
    def test_real_closed_v3_preflight_without_browser_or_device_and_no_report_changes(self):
        refs={
            'boot':{'path':'analysis/hardware/mini-first-boot-v11-released-run.json','sha256':'8b91a906bd061952938ce54930eb8d5e0956ace4c4d4465fd8a57da735d88202'},
            'connected':{'path':'build/mini-desktop-v3-real-02/connected-proof.json','sha256':'2fbf2463f86d7d72017f5127af83334e7c2fcd41d8c5bc74c7f2710dda16950a'},
            'session':{'path':'build/mini-desktop-v3-real-02/session.json','sha256':'d4d6f052a2e042664a52fa117c514afd6c457447e9e308a9738e6725e394f22f'}}
        args=['--check-only']
        for key,ref in refs.items():args+=['--'+key,str(driver.ROOT/ref['path']),'--'+key+'-sha256',ref['sha256']]
        before={k:read_shared_bytes(driver.ROOT/v['path']) for k,v in refs.items()}
        old=trial.evidence.validate_v3_browser_evidence
        with patch.object(trial,'run',side_effect=AssertionError('hardware/browser')),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(driver.main(args),0)
        result=json.loads(output.getvalue())
        self.assertEqual(result['preflight'],'pass');self.assertFalse(result['device_io'] or result['browser_started'])
        self.assertIs(trial.evidence.validate_v3_browser_evidence,old)
        for key,ref in refs.items():self.assertEqual(before[key],read_shared_bytes(driver.ROOT/ref['path']))

    def test_function_adapter_restores_on_exception_and_new_report_records_source_and_note(self):
        old=trial.evidence.validate_v3_browser_evidence
        with self.assertRaises(RuntimeError),driver.closure_adapter(trial):
            self.assertIs(trial.evidence.validate_v3_browser_evidence,closed.validate_v3_browser_evidence)
            raise RuntimeError('test')
        self.assertIs(trial.evidence.validate_v3_browser_evidence,old)
        note={'classification':'offline unit fixture','original_error':closed.EXACT_POST_CLOSE_ERROR}
        report={'kind':'mini-browser-first-preset-v3-trial','prepared':{'context':{'desktop_close_observation':note}}}
        published=[]
        driver.annotated_writer(lambda path,value:published.append(value),'a'*64)('new/report.json',report)
        self.assertEqual(published[0]['desktop_close_observation'],note)
        name=Path(closed.__file__).relative_to(driver.ROOT).as_posix()
        self.assertEqual(published[0]['source_sha256'][name],driver.CLOSE_VALIDATOR_SHA)
        self.assertNotIn('source_sha256',report)


if __name__=='__main__':unittest.main()
