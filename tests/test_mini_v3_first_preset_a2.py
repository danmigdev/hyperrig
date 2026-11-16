"""Offline A2 activity adapter tests. No browser, serial port or device opens."""
import contextlib
import copy
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import run_mini_v3_first_preset_a2 as adapter
from tools import probe_mini_browser_first_preset as trial
from tools.mini_host_journal import read_shared_bytes
from tests import test_mini_browser_first_preset as existing


class A2FirstPresetAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = read_shared_bytes(adapter.ROOT/adapter.FIXTURE['path'])
        if adapter.sha(raw) != adapter.FIXTURE['sha256']: raise AssertionError('real STAT fixture changed')
        cls.fixture = json.loads(raw)
        cls.lines = [x['lines'] for x in cls.fixture['STAT_observations']]
        cls.helper = existing.BrowserFirstPresetTests()

    def state(self, observation=0, **kwargs):
        state = self.helper.state(posts=0,takes=0,**kwargs)
        state['a2_stat'] = adapter.parse_stat(copy.deepcopy(self.lines[observation]))
        return state

    def test_default_has_no_evidence_browser_or_device_activity(self):
        with (patch.object(adapter,'verify_dependencies',side_effect=AssertionError('read')),
              patch.object(adapter.bridge,'modules',side_effect=AssertionError('delegate')),
              contextlib.redirect_stdout(io.StringIO()) as stream):
            self.assertEqual(adapter.main([]),0)
        result=json.loads(stream.getvalue())
        self.assertFalse(result['device_io'] or result['browser_started'] or result['inputs_read'])

    def test_pinned_audit_and_all_frozen_dependencies_remain_exact(self):
        adapter.verify_dependencies()
        desktop, delegated = adapter.bridge.modules('first-preset')
        self.assertIs(delegated,trial);self.assertIs(desktop,trial.desktop)
        self.assertEqual(trial.READS,('GAIN','LVL','FXS','PLIST','SNAPS','CLIST','ILIST','MODEL','CLKSTATE',
                                    'AMPEQ','BPM','PCOLOR','STW','SNAPNAME'))

    def test_real_23_line_responses_and_zero_generic_counters_show_A2_progress(self):
        self.assertEqual([len(x) for x in self.lines],[23,23])
        a,b=self.state(0),self.state(1)
        self.assertEqual([a['a2_stat']['nproc'],b['a2_stat']['nproc']],[328986,329126])
        result=adapter.progress(trial,a,b)
        self.assertEqual(result['A2_nproc_delta'],140)
        self.assertTrue(result['A2_completion_progress_observed'])
        self.assertFalse(result['core1_job_progress_observed'] or result['generic_job_counters_required'])
        self.assertFalse(result['physical_audio_output_verified'] or result['run_duration_used_as_counter'])
        self.assertEqual(result['before']['posts'],0);self.assertEqual(result['after']['takes'],0)

    def test_only_complete_original_STAT_grammar_and_uint32_values_are_accepted(self):
        for kind in ('short','duplicateT','wrongorder','badcount','extra','badterminal','overflow','signeduint','badRS'):
            lines=copy.deepcopy(self.lines[0])
            if kind=='short':lines.pop()
            elif kind=='duplicateT':lines[3]=lines[2]
            elif kind=='wrongorder':lines[0],lines[1]=lines[1],lines[0]
            elif kind=='badcount':lines[5]=lines[5].replace('n=16','n=17')
            elif kind=='extra':lines.append('ERR extra')
            elif kind=='badterminal':lines[-1]=lines[-1].replace('clip_eng=0','clip_eng=0 extra')
            elif kind=='overflow':lines[2]=lines[2].replace('nproc=328986','nproc=4294967296')
            elif kind=='signeduint':lines[2]=lines[2].replace('nproc=328986','nproc=-1')
            else:lines[6]='1/2/3'
            with self.subTest(kind=kind),self.assertRaises(ValueError):adapter.parse_stat(lines)
        # Unit grammar fixture for the separately proved n=0 branch, not a real observation.
        zero=self.lines[0][:6]+[self.lines[0][-1]];zero[5]=zero[5].replace('n=16','n=0')
        self.assertEqual(adapter.parse_stat(zero)['rs_count'],0)

    def test_nproc_stagnation_reset_and_forged_parsed_counter_are_rejected(self):
        before=self.state(0)
        for count in (328986,328985,0):
            after=self.state(1)
            lines=after['a2_stat']['lines'];lines[2]=lines[2].replace('nproc=329126',f'nproc={count}')
            after['a2_stat']=adapter.parse_stat(lines)
            with self.subTest(count=count),self.assertRaises(ValueError):adapter.progress(trial,before,after)
        after=self.state(1);after['a2_stat']['nproc']+=1
        with self.assertRaises(ValueError):adapter.progress(trial,before,after)

    def test_original_model_safe_mode_gain_and_state_gates_remain_required(self):
        for change in ('safe','mode','model','gain','amp','preset','statmode','statgain','layers','channels'):
            after=self.state(1)
            if change=='safe':after['runtime']['safe']=1
            elif change=='mode':after['runtime']['mode']=0
            elif change=='model':after['model']=["MODEL 'other'"]
            elif change=='gain':after['gain']=[0,-1]
            elif change=='amp':after['fxs']['amp']['on']=0
            elif change=='preset':after['plist']['current']=0
            else:
                lines=after['a2_stat']['lines']
                if change=='statmode':lines[0]=lines[0].replace('mode=2','mode=0')
                elif change=='statgain':lines[-1]=lines[-1].replace('gain=0/0','gain=0/-1')
                elif change=='layers':lines[1]=lines[1].replace('L=23','L=22')
                else:lines[1]=lines[1].replace('C=3','C=1')
                after['a2_stat']=adapter.parse_stat(lines)
            with self.subTest(change=change),self.assertRaises(ValueError):adapter.progress(trial,self.state(0),after)

    def test_snapshot_adds_exactly_one_STAT_after_original_snapshot_without_retries(self):
        events=[]
        def original(cdp):events.append('original14');return {'responses':self.helper.answers(posts=0,takes=0),'state':self.helper.state(posts=0,takes=0)}
        class CDP:
            def evaluate(_self,expr):events.append(expr);return copy.deepcopy(self.lines[0])
        oldprogress=lambda *_:None;oldwriter=lambda *_:None
        delegate=SimpleNamespace(snapshot=original,verify_processing_progress=oldprogress,atomic_write_json=oldwriter)
        with adapter.activity_adapter(delegate):
            value=delegate.snapshot(CDP())
            self.assertEqual(events,['original14',adapter.STAT_QUERY])
            self.assertEqual(set(value['responses']),set(trial.READS)|{'STAT'})
            self.assertEqual(value['state']['a2_stat']['nproc'],328986)
        self.assertIs(delegate.snapshot,original);self.assertIs(delegate.verify_processing_progress,oldprogress)
        self.assertIs(delegate.atomic_write_json,oldwriter)
        events.clear()
        class Broken:
            def evaluate(_self,expr):events.append(expr);raise RuntimeError('lost command')
        with self.assertRaises(RuntimeError),adapter.activity_adapter(delegate):delegate.snapshot(Broken())
        self.assertEqual(events,['original14',adapter.STAT_QUERY]);self.assertIs(delegate.snapshot,original)

    def test_STAT_original_queue_predicate_waits_for_final_NIVEL_not_T(self):
        node=shutil.which('node')
        if not node:self.skipTest('existing Node unavailable; no installation')
        script='''const d=JSON.parse(require('fs').readFileSync(0,'utf8'));let calls=0;
global.Pedal={cmd:(command,until,timeout)=>{calls++; if(command!=='STAT'||timeout!==4000)throw Error('command');
for(let i=0;i<d.lines.length-1;i++)if(until(d.lines[i]))throw Error('early terminal');
if(!until(d.lines.at(-1))||!until('ERR failed'))throw Error('terminal');return d.lines;}};
const result=eval(d.expression);if(calls!==1||result.length!==23)throw Error('count');console.log('pass');'''
        result=subprocess.run([node,'-e',script],input=json.dumps({'lines':self.lines[0],'expression':adapter.STAT_QUERY}),
                              capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),'pass')

    def test_both_report_annotations_preserve_inputs_profile_and_original_report(self):
        publications=[]
        report={'kind':'mini-browser-first-preset-v3-trial','evidence':{'unchanged':True},
                'profile':{'hardware_verified':False,'write':False},'source_sha256':{'frozen.py':'f'*64}}
        original=copy.deepcopy(report)
        writer=lambda path,value,**kwargs:publications.append((path,value,kwargs))
        reader=adapter.bridge.ExactTraceReader(lambda path:b'')
        bridge_writer=adapter.bridge.annotated_writer(writer,reader,adapter.BRIDGE_SHA)
        adapter.annotated_writer(bridge_writer,'a'*64)('new/report.json',report,attempts=2)
        published=publications[0][1]
        self.assertEqual(report,original);self.assertEqual(published['profile'],original['profile'])
        self.assertEqual(published['evidence'],original['evidence'])
        self.assertEqual(published['source_sha256'][adapter.SOURCE_NAME],'a'*64)
        self.assertEqual(published['source_sha256'][adapter.bridge.SOURCE_NAME],adapter.BRIDGE_SHA)
        self.assertEqual(published['A2_gate_extension']['audit'],adapter.AUDIT)
        self.assertIn('evidence_io_extension',published)
        self.assertFalse(published['A2_gate_extension']['physical_audio_output_verified'])
        with self.assertRaises(ValueError):adapter.annotated_writer(writer,'a'*64)('new/report.json',published)

    def test_main_delegates_same_args_and_restores_adapters_on_failure(self):
        args=['--check-only','--boot','exact-boot.json']
        reader,writer=trial.desktop.read_shared_bytes,trial.atomic_write_json
        snap,gate=trial.snapshot,trial.verify_processing_progress
        def failed(received):
            self.assertEqual(received,args);self.assertIsNot(trial.snapshot,snap)
            self.assertIsNot(trial.verify_processing_progress,gate);raise RuntimeError('preflight rejection')
        with patch.object(trial,'main',side_effect=failed),self.assertRaises(RuntimeError):adapter.main(args)
        self.assertIs(trial.desktop.read_shared_bytes,reader);self.assertIs(trial.atomic_write_json,writer)
        self.assertIs(trial.snapshot,snap);self.assertIs(trial.verify_processing_progress,gate)

    def test_frozen_native_RX_verifier_checks_the_added_STAT_reply(self):
        existing.BrowserFirstPresetTests.setUpClass()
        guard=copy.deepcopy(existing.BrowserFirstPresetTests.node_result['guard'])
        # Construct an offline native-wire fixture from the existing guard test;
        # it makes no hardware claim. The STAT lines themselves are the real fixture.
        wire=next(x for x in guard['wire'] if x['origin']=='query' and x['line']=='FXS')
        command=next(x for x in guard['commands'] if x['id']==wire['command_id'])
        chunks=[x for x in guard['rx'] if wire['seq']<x['seq']<command['seq']]
        self.assertTrue(chunks)
        wire.update(line='STAT',hex=b'STAT\n'.hex());command.update(line='STAT',lines=copy.deepcopy(self.lines[0]))
        for chunk in chunks:chunk['hex']=''
        raw=('\r\n'.join(self.lines[0])+'\r\n').encode()
        chunks[0]['hex']=raw.hex()
        self.assertTrue(trial.verify_wire(guard)['completed_commands_checked_against_native_RX'])
        chunks[0]['hex']=raw.replace(b'T nproc=328986',b'T nproc=328985').hex()
        with self.assertRaisesRegex(ValueError,'absent from native RX: STAT'):trial.verify_wire(guard)


if __name__=='__main__':unittest.main()
