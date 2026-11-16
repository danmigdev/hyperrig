"""Offline trial/parser/real-editor-function tests. No browser or device opens."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from tools import probe_mini_browser_first_preset as trial


class BrowserFirstPresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = shutil.which('node')
        if not node: raise unittest.SkipTest('existing Node unavailable; no installation')
        result = subprocess.run([node,str(trial.ROOT/'tests/mini_browser_first_preset_guard_test.js'),
            str(trial.GUARD),str(trial.desktop.APP/'tankmini.html'),str(trial.BLOB),'--emit-success'],
            capture_output=True,text=True,check=True)
        cls.node_result = json.loads(result.stdout)

    def answers(self, *, gain=(0,0), preset=-1, capture_slot=0, scene=-1, posts=100, takes=99):
        return {'GAIN':[f'GAIN in={gain[0]} out={gain[1]} dB'],
            'LVL':[f'LVL in=-1440 out=-1440 ci=0 co=0 m=2 g={gain[0]}/{gain[1]} p={preset}'],
            'FXS':['FXS amp=1 on=1','FXS cpu=100/1000 ticks (10%) mem_fx=0 B',
                   f'FXS eng=0 posts={posts} takes={takes} canc=0 lat=0/0 run=0','FXS peak=100 ticks skipped=0'],
            'PLIST':([f"PRE {preset} 0 {capture_slot} -1 'Preset 1A' t=- s=1 amp=1"] if preset>=0 else [])+[f'PLIST end current={preset}'],
            'SNAPS':[f"SNAPS {'1000' if scene==0 else '0000'} current={scene}"],
            'CLIST':([f"CAP {capture_slot} 4892 'A2' trim=0.0"] if capture_slot>=0 else [])+[f'CLIST end current={capture_slot} slots=15'],
            'ILIST':['ILIST end current=-1 slots=15'], 'MODEL':[trial.capture.MODEL_LINE],
            'CLKSTATE':['CLKSTATE mhz=360 safe=0'],
            'AMPEQ':['AMPEQ volume=0 bass=0 mid=0 treble=0 presence=0 drive=0'],
            'BPM':['BPM 120.0'],'PCOLOR':[f'PCOLOR none preset={preset}'],
            'STW':['STW w=0 cur=0 live=0 cpu=0/1 deg=0'],'SNAPNAME':['SNAPNAME end']}

    def state(self, **kwargs): return trial.parse_snapshot(self.answers(**kwargs))

    def test_default_does_not_read_evidence_or_start_any_browser(self):
        with (patch.object(trial,'prepare',side_effect=AssertionError('read')),
              patch.object(trial,'run',side_effect=AssertionError('browser')),
              contextlib.redirect_stdout(io.StringIO()) as stream):
            self.assertEqual(trial.main([]),0)
        result=json.loads(stream.getvalue())
        self.assertFalse(result['device_io'] or result['browser_started'] or result['inputs_read'])

    def test_prepare_preserves_false_profile_and_requires_real_v3_context(self):
        context={'pong':'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11',
            'runtime':{'clock':{'safe':0},'lvl':{'mode':2},'plist':{'current':-1}},
            'profile':{'hardware_verified':False,'capabilities':{'read':True,'write':False}}}
        refs={name:{'path':name+'.json','sha256':'a'*64} for name in ('boot','connected','session')}
        with patch.object(trial.evidence,'validate_v3_browser_evidence',return_value=context) as validate:
            got=trial.prepare(**refs)
        validate.assert_called_once_with(**refs)
        self.assertFalse(got['profile']['hardware_verified'] or got['profile']['capabilities']['write'])
        self.assertEqual(got['general_capabilities_granted'],{})
        for change in ('safe','mode','current','pong'):
            bad=copy.deepcopy(context)
            if change=='safe':bad['runtime']['clock']['safe']=1
            elif change=='mode':bad['runtime']['lvl']['mode']=0
            elif change=='current':bad['runtime']['plist']['current']=0
            else:bad['pong']+=' safe'
            with self.subTest(change=change),patch.object(trial.evidence,'validate_v3_browser_evidence',return_value=bad),self.assertRaises(ValueError):
                trial.prepare(**refs)

    def test_explicit_malformed_gain_fails_as_validation_error(self):
        for lines in ([],['GAIN bad'],['GAIN in=0 out=0 dB','GAIN in=0 out=0 dB'],['GAIN in=0 out=13 dB']):
            answers=self.answers();answers['GAIN']=lines
            with self.subTest(lines=lines),self.assertRaises(ValueError):trial.parse_snapshot(answers)

    def test_zero_clips_and_zero_instantaneous_engine_duration_are_valid(self):
        before=self.state(posts=10,takes=9);after=self.state(posts=13,takes=12)
        evidence=trial.verify_processing_progress(before,after)
        self.assertTrue(evidence['core1_job_progress_observed'])
        self.assertFalse(evidence['physical_audio_output_verified'])
        self.assertEqual(before['runtime']['input_clips'],0)
        self.assertEqual(before['runtime']['engine']['run'],0)
        self.assertEqual(before['runtime']['engine']['eng'],0)

    def test_only_audited_job_counters_qualify_progress(self):
        first=self.state(posts=10,takes=9)
        for posts,takes in ((10,9),(11,9),(10,10),(2,1)):
            with self.subTest(posts=posts,takes=takes),self.assertRaises(ValueError):
                trial.verify_processing_progress(first,self.state(posts=posts,takes=takes))

    def test_first_preset_preconditions_stop_before_any_plan(self):
        baseline=self.state()
        changes=[('gain',[0,-30]),('snaps',{'present':'1000','current':0}),
                 ('ir_current',1),('model',["MODEL 'Other'"])]
        for field,value in changes:
            bad=copy.deepcopy(baseline);bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):trial.make_plan(bad,'Preset 1A')
        for key,value in (('safe',1),('mode',0)):
            bad=copy.deepcopy(baseline);bad['runtime'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):trial.make_plan(bad,'Preset 1A')
        with self.assertRaises(ValueError):trial.make_plan(self.state(preset=0,scene=0),'Preset 1A')
        with self.assertRaises(ValueError):trial.make_plan(self.state(capture_slot=-1),'Preset 1A')

    def test_first_free_preset_preserves_original_generated_name(self):
        state=self.state();state['plist']['presets']=[{'slot':0,'name':'Existing'},{'slot':2,'name':'Other'}]
        plan=trial.make_plan(state,'Preset 1B')
        self.assertEqual(plan['slot'],1)
        self.assertEqual(plan['save_request'],'PSAVE 1 Preset 1B')
        self.assertEqual(plan['load_request'],'PLOAD 1')
        self.assertEqual(plan['down'],[0,-1])
        self.assertNotIn('HyperRig_Test',json.dumps(plan))

    def test_save_and_reload_require_original_gain_capture_model_scene_and_inventory(self):
        before=self.state();plan=trial.make_plan(before,'Preset 1A')
        saved=self.state(preset=0,scene=0)
        trial.verify_state(saved,before,gains=[0,0],stage='saved',plan=plan)
        marker=self.state(preset=0,scene=0,gain=(0,-1))
        trial.verify_state(marker,before,gains=[0,-1],stage='saved',plan=plan)
        trial.verify_state(saved,before,gains=[0,0],stage='reloaded',plan=plan)
        changes=[('gain',[0,-1]),('snaps',{'present':'1000','current':-1}),
            ('model',["MODEL 'Other'"]),('clist',{'current':-1}),('ilist',['ILIST changed'])]
        for key,value in changes:
            bad=copy.deepcopy(saved);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):trial.verify_state(bad,before,gains=[0,0],stage='reloaded',plan=plan)
        bad=copy.deepcopy(saved);bad['plist']['presets'].append({'slot':7,'name':'Unexpected'})
        with self.assertRaises(ValueError):trial.verify_state(bad,before,gains=[0,0],stage='reloaded',plan=plan)
        bad=copy.deepcopy(saved);bad['preset_rows'][0]=bad['preset_rows'][0].replace('PRE 0 0 0 -1','PRE 0 0 4 -1')
        with self.assertRaises(ValueError):trial.verify_state(bad,before,gains=[0,0],stage='reloaded',plan=plan)
        baseline=copy.deepcopy(before);baseline['preset_rows']=["PRE 7 0 2 -1 'Existing' t=- s=0 amp=1"]
        unchanged=copy.deepcopy(saved);unchanged['preset_rows'].extend(baseline['preset_rows'])
        trial.verify_state(unchanged,baseline,gains=[0,0],stage='reloaded',plan=plan)
        unchanged['preset_rows'][-1]=unchanged['preset_rows'][-1].replace('0 2 -1','0 3 -1')
        with self.assertRaises(ValueError):trial.verify_state(unchanged,baseline,gains=[0,0],stage='reloaded',plan=plan)

    def test_UI_key_path_has_no_direct_mutation_command(self):
        class CDP:
            def __init__(self):self.calls=[];self.expressions=[]
            def call(self,name,args):self.calls.append((name,args))
            def evaluate(self,source):
                self.expressions.append(source)
                return {'guard':{'phase':'down1_ack','fatal':None},'gainPending':0} if source==trial.STATE else None
        cdp=CDP();trial.ui_key(cdp,'down1',trial.OUTPUT_KNOB,1)
        self.assertEqual([x[0] for x in cdp.calls],['Input.dispatchKeyEvent']*2)
        self.assertEqual([x[1]['type'] for x in cdp.calls],['keyDown','keyUp'])
        self.assertFalse(any('Pedal.cmd' in x or 'S.gain=' in x for x in cdp.expressions))

    def test_original_editor_functions_guard_and_raw_byte_trace(self):
        result=self.node_result
        self.assertEqual(result['result'],'pass');self.assertGreaterEqual(result['checks'],69)
        self.assertFalse(result['device_io'] or result['browser_started'])
        self.assertEqual(result['actual_editor_functions_tested'],['buildGains','savePreset','sceneAOnSave','loadPreset'])
        checked=trial.verify_wire(result['guard'])
        self.assertTrue(checked['completed_commands_checked_against_native_RX'])
        self.assertGreater(checked['raw_RX_byte_count'],4892)

    def test_raw_trace_missing_response_duplicate_command_or_fake_ACK_rejected(self):
        original=self.node_result['guard']
        for kind in ('rx','psave_rx','gain_rx','wire','ack','ack_event','ack_sequence','ui','capture'):
            bad=copy.deepcopy(original)
            if kind=='rx':bad['rx'][0]['hex']=''
            elif kind in ('psave_rx','gain_rx'):
                prefix=b'PSAVE ok' if kind=='psave_rx' else b'GAIN in=0 out=-1'
                chunk=next(x for x in bad['rx'] if bytes.fromhex(x['hex']).startswith(prefix))
                chunk['hex']=b'RX_CORRUPTED\r\n'.hex()
            elif kind=='wire':bad['wire'][0]['hex']='00'
            elif kind=='ack':next(x for x in bad['commands'] if x['line']=='PSAVE 0 Preset 1A')['lines']=['PSAVE invented']
            elif kind=='ack_event':next(x for x in bad['events'] if x.get('kind')=='mutation_ack')['lines']=['GAIN invented']
            elif kind=='ack_sequence':
                event=next(x for x in bad['events'] if x.get('kind')=='mutation_ack')
                command=next(x for x in bad['commands'] if x['line']==event['line'])
                event['seq']=command['seq']
            elif kind=='ui':bad['ui'][0]['trusted']=False
            else:bad['wire'].insert(3,copy.deepcopy(next(x for x in bad['wire'] if x['line']=='CSAVE 0 A2')))
            with self.subTest(kind=kind),self.assertRaises(ValueError):trial.verify_wire(bad)

    def test_completion_flags_stay_false_after_native_close_or_raw_trace_failure(self):
        good={'native_close_verified':True,'open':False,'closes':1,'closeError':None}
        for kind in ('close_failed','open','ack'):
            report={'UI_sequence_completed':True,'ui_roundtrip_verified':True,'save_reload_verified':True}
            guard=copy.deepcopy(self.node_result['guard']);disconnect=copy.deepcopy(good)
            if kind=='close_failed':disconnect['native_close_verified']=False;disconnect['closeError']='native close failed'
            elif kind=='open':disconnect['open']=True
            else:next(x for x in guard['events'] if x.get('kind')=='mutation_ack')['lines']=['GAIN invented']
            with self.subTest(kind=kind),self.assertRaises(ValueError):trial.complete_proof(report,guard,disconnect)
            self.assertEqual(report['result'],'fail')
            self.assertFalse(report['ui_roundtrip_verified'] or report['save_reload_verified'])
        report={'UI_sequence_completed':True};trial.complete_proof(report,self.node_result['guard'],good)
        self.assertEqual(report['result'],'pass')
        self.assertTrue(report['ui_roundtrip_verified'] and report['save_reload_verified'])

    def test_lost_CDP_after_open_intent_cannot_claim_no_hardware_execution(self):
        report={'hardware_executed':None,'execution_status_unknown':True}
        # An attempted native open without a completion observation stays unknown.
        trial.serial_observation(report,{'opens':1,'events':[{'kind':'serial_open_intent'}]})
        self.assertIsNone(report['hardware_executed']);self.assertTrue(report['execution_status_unknown'])
        trial.serial_observation(report,{'opens':0,'events':[]})
        self.assertIs(report['hardware_executed'],False);self.assertFalse(report['execution_status_unknown'])
        trial.serial_observation(report,{'opens':1,'events':[{'kind':'serial_open_complete'}]})
        self.assertIs(report['hardware_executed'],True);self.assertFalse(report['execution_status_unknown'])


if __name__=='__main__':unittest.main()
