"""Offline bundle validation and trusted-click orchestration; no native browser."""
import contextlib
import copy
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import launch_mini_fx_editor as launcher


class FXEditorLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=launcher.ROOT/'build/hyperrig-mini-fx-editor'
        cls.proof=launcher.qualifier().validate_bundle(cls.folder)

    def test_default_never_reads_or_opens(self):
        with patch.object(launcher,'prepare',side_effect=AssertionError('unexpected read')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(launcher.main([]),0)
        self.assertFalse(json.loads(out.getvalue())['browser_started'])

    def test_real_bundle_check_only_enables_exact_eight_without_claiming_UI_test(self):
        prepared=launcher.prepare(self.folder)
        self.assertEqual(prepared['enabled_families'],{'usb-cdc':launcher.FAMILIES})
        self.assertEqual(len(launcher.FAMILIES),8)
        self.assertFalse(prepared['qualification_UI_FX_interactions_physically_tested'])
        with patch.object(launcher,'run',side_effect=AssertionError('browser')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(launcher.main(['--check-only']),0)
        self.assertFalse(json.loads(out.getvalue())['browser_started'])

    def test_scope_expansion_or_missing_removal_evidence_is_rejected(self):
        for fault in ('write','panel','BLE','routing','missing_FXR','no_removal'):
            proof=copy.deepcopy(self.proof)
            if fault in ('write','panel'):proof['profile']['capabilities'][fault]=True
            elif fault=='BLE':proof['profile']['family_capabilities']['ble-nus']=['FXP']
            elif fault=='routing':proof['profile']['family_capabilities']['usb-cdc'].append('FXM')
            elif fault=='missing_FXR':proof['profile']['family_capabilities']['usb-cdc'].remove('FXR')
            else:proof['qualification']['removal_replay']=None
            with self.subTest(fault=fault),patch.object(launcher,'qualifier',return_value=SimpleNamespace(validate_bundle=lambda folder:proof)),self.assertRaises(ValueError):
                launcher.prepare(self.folder)

    def activate(self,*,coach=True,blocked=False,observed=True):
        calls=[];clicks=[];report={};current={'coach':coach,'connected':False,'connecting':False,'open':False}
        target={'value':None}
        class CDP:
            def call(self,name,args=None):
                calls.append((name,args))
                if name=='Input.dispatchMouseEvent' and args['type']=='mouseReleased':
                    selector=target['value']
                    if observed:clicks.append({'selector':selector,'trusted':True})
                    if selector==launcher.activation.SKIP:current['coach']=False
                    else:current['connecting']=True
            def screenshot(self,path):calls.append(('screenshot',path.name));return {'path':path.name}
            def evaluate(self,expression):
                calls.append(('evaluate',expression))
                if expression.startswith('({coach:'):return copy.deepcopy(current)
                if expression=='__miniTourOperator.clicks':return copy.deepcopy(clicks)
                return True
        def stable(cdp,selector):
            calls.append(('stable',selector));target['value']=selector
            if blocked:raise ValueError('button blocked')
            return {'x':4,'y':5,'width':10,'height':10,'okay':True}
        with patch.object(launcher.activation,'stable_target',side_effect=stable),patch.object(launcher.time,'sleep'):
            try:launcher.activate_connection(CDP(),report,Path('unused'),lambda:calls.append(('publish',None)))
            except ValueError as error:report['error']=str(error)
        return report,calls

    def test_tour_and_connect_have_stable_hit_tests_and_single_trusted_clicks(self):
        report,calls=self.activate()
        self.assertNotIn('error',report)
        actions=report['connection_activation']['actions']
        self.assertEqual([a['selector'] for a in actions],[launcher.activation.SKIP,launcher.activation.CONNECT])
        self.assertTrue(all(a['observed_click']['trusted'] for a in actions))
        self.assertEqual(sum(n=='Input.dispatchMouseEvent' for n,_ in calls),4)
        self.assertEqual(sum(n=='Page.bringToFront' for n,_ in calls),2)
        self.assertEqual(sum(n=='screenshot' for n,_ in calls),2)
        self.assertFalse(report['connection_activation']['port_selection_performed'])
        self.assertEqual(calls[-1],('evaluate','__miniTourOperator.remove()'))

    def test_absent_tour_clicks_only_connect_and_blocked_layout_never_clicks(self):
        report,calls=self.activate(coach=False)
        self.assertTrue(report['connection_activation']['tour_already_absent'])
        self.assertEqual(sum(n=='Input.dispatchMouseEvent' for n,_ in calls),2)
        report,calls=self.activate(blocked=True)
        self.assertIn('error',report)
        self.assertFalse(any(n=='Input.dispatchMouseEvent' for n,_ in calls))

    def test_cmd_targets_only_new_bundle_and_launcher(self):
        text=(launcher.ROOT/'tools/launch_mini_fx_editor.cmd').read_text()
        self.assertIn('launch_mini_fx_editor.py',text)
        self.assertIn('build\\hyperrig-mini-fx-editor',text)
        self.assertNotIn('hyperrig-mini-qualified-editor',text)


if __name__=='__main__':unittest.main()
