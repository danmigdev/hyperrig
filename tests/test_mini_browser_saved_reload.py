"""Offline only. The native browser, device, UI events and replies are fakes."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import probe_mini_browser_saved_reload as probe
from tools.mini_host_journal import read_shared_json


PARTIAL={'path':'build/mini-first-preset-ui-04/report.json',
         'sha256':'0eb9836638dd2025d9e75f380db4cc9c765c53dcc7ff4e0316ab810c3d2479ff'}


def changed(snapshot,*,output=None,advance=0):
    value=copy.deepcopy(snapshot)
    state=value['state'];stat=state['a2_stat'];lines=stat['lines']
    if output is not None:
        state['gain'][1]=output;state['extra']['gain_db'][1]=output
        lines[-1]=lines[-1].replace('gain=0/0','gain=0/'+str(output))
    n=stat['nproc'];lines[2]=lines[2].replace('nproc='+str(n),'nproc='+str(n+advance))
    state['a2_stat']=probe.activity.parse_stat(lines)
    return value


class SavedReloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior=read_shared_json(probe.ROOT/PARTIAL['path'])
        cls.plan=cls.prior['plan'];cls.saved=cls.prior['saved']
        node=shutil.which('node')
        if not node:raise unittest.SkipTest('existing Node unavailable; no installation')
        result=subprocess.run([node,'tests/mini_browser_saved_reload_guard_test.js',str(probe.GUARD),
            str(probe.APP/'tankmini.html'),str(probe.frozen.BLOB),'--emit-success'],
            cwd=probe.ROOT,check=True,capture_output=True,text=True)
        cls.node=json.loads(result.stdout);cls.guard=cls.node['guard']

    def test_default_does_not_read_inputs_or_start_browser(self):
        with patch.object(probe,'prepare',side_effect=AssertionError('read')),contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(probe.main([]),0)
        value=json.loads(stream.getvalue())
        self.assertFalse(value['device_io'] or value['browser_started'] or value['inputs_read'])

    def test_real_partial_preflight_keeps_prior_failure_and_zero_new_saves(self):
        prepared=probe.prepare(partial=PARTIAL)
        self.assertEqual(prepared['prior_partial']['report_ref'],PARTIAL)
        self.assertEqual(prepared['saved_snapshot'],self.saved)
        self.assertEqual(prepared['plan'],self.plan)
        self.assertEqual(prepared['UI_mutations_max'],2)
        self.assertEqual(prepared['capture_mutations_max'],0)
        self.assertEqual(prepared['preset_save_max'],0)
        self.assertEqual(self.prior['result'],'fail')
        self.assertEqual(prepared['profile'],self.prior['prepared']['profile'])

    def test_original_gain_and_load_functions_under_bounded_guard(self):
        self.assertEqual(self.node['result'],'pass');self.assertGreaterEqual(self.node['checks'],80)
        self.assertEqual(self.node['actual_editor_functions_tested'],['buildGains','loadPreset'])
        self.assertFalse(self.node['device_io'] or self.node['browser_started'])
        self.assertEqual(self.guard['mutations'],2)

    def test_native_wire_verification_rejects_ack_or_rx_substitution_and_extra_writes(self):
        result=probe.verify_wire(self.guard,self.plan)
        self.assertEqual(result['actual_UI_mutation_count'],2)
        for fault in ('ack','rx','extra','untrusted','wire','close'):
            bad=copy.deepcopy(self.guard)
            if fault=='ack':next(e for e in bad['events'] if e['kind']=='mutation_ack')['lines']=['GAIN in=0 out=0 dB']
            elif fault=='rx':
                load=next(w for w in bad['wire'] if w['line']=='PLOAD 0')
                command=next(c for c in bad['commands'] if c['id']==load['command_id'])
                bad['rx']=[r for r in bad['rx'] if not load['seq']<r['seq']<command['seq']]
            elif fault=='extra':bad['wire'].append({**bad['wire'][-1],'line':'PSAVE 0 Preset 1A','origin':'query'})
            elif fault=='untrusted':bad['ui'][0]['trusted']=False
            elif fault=='wire':next(w for w in bad['wire'] if w['line']=='PLOAD 0')['hex']='00'
            else:bad['closes']=0
            with self.subTest(fault=fault),self.assertRaises(ValueError):probe.verify_wire(bad,self.plan)

    def test_saved_state_and_A2_progress_are_fresh_without_generic_counter_requirement(self):
        before=changed(self.saved,advance=1)['state'];after=changed(self.saved,advance=2)['state']
        value=probe.processing_progress(before,after,self.saved['state'],self.plan)
        self.assertTrue(value['A2_completion_progress_observed'])
        self.assertFalse(value['physical_audio_output_verified'])
        for fault in ('nproc','preset','gain','scene','safe','capture','model'):
            bad=copy.deepcopy(after)
            if fault=='nproc':bad=copy.deepcopy(before)
            elif fault=='preset':bad['plist']['current']=1
            elif fault=='gain':bad['gain'][1]=-1
            elif fault=='scene':bad['snaps']['current']=1
            elif fault=='safe':bad['runtime']['safe']=1
            elif fault=='capture':bad['clist']['current']=1
            else:bad['model']=['MODEL wrong']
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                probe.processing_progress(before,bad,self.saved['state'],self.plan)

    def test_success_is_promoted_only_after_native_close_and_raw_verification(self):
        disconnect={'native_close_verified':True,'open':False,'closes':1,'closeError':None}
        report={'UI_sequence_completed':True,'plan':self.plan}
        probe.complete_proof(report,self.guard,disconnect)
        self.assertEqual(report['result'],'pass');self.assertTrue(report['retained_saved_reload_verified'])
        for fault in ('close','raw','error'):
            value=copy.deepcopy(report);guard=copy.deepcopy(self.guard);close=copy.deepcopy(disconnect)
            if fault=='close':close['native_close_verified']=False
            elif fault=='raw':guard['rx']=[]
            else:value['error']='offline failure'
            with self.subTest(fault=fault),self.assertRaises(ValueError):probe.complete_proof(value,guard,close)
            self.assertFalse(value['retained_saved_reload_verified']);self.assertEqual(value['result'],'fail')

    def test_check_only_cannot_run_browser(self):
        with patch.object(probe,'run',side_effect=AssertionError('browser')),contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(probe.main(['--check-only','--partial-report',PARTIAL['path'],
                                        '--partial-report-sha256',PARTIAL['sha256']]),0)
        self.assertEqual(json.loads(stream.getvalue())['preflight'],'pass')

    def test_reload_UI_wait_only_observes_until_original_readback_finishes(self):
        values=[{'gain':[0,-1],'capture':0,'scene':0,'preset':0,'fatal':None},
                {'gain':[0,0],'capture':0,'scene':0,'preset':0,'fatal':None}]
        sources=[]
        cdp=SimpleNamespace(evaluate=lambda source:(sources.append(source),values.pop(0))[1])
        with patch.object(probe.time,'sleep'):
            value=probe.wait_reloaded_ui(cdp,self.plan)
        self.assertEqual(value['gain'],[0,0]);self.assertEqual(len(sources),2)
        self.assertTrue(all('Pedal' not in source and '.arm' not in source for source in sources))
        cdp=SimpleNamespace(evaluate=lambda source:{'gain':[0,-1],'capture':0,'scene':0,'preset':0,'fatal':None})
        with patch.object(probe.time,'monotonic',side_effect=[0,0,16]),patch.object(probe.time,'sleep'),self.assertRaises(ValueError):
            probe.wait_reloaded_ui(cdp,self.plan)

    def test_fake_lifecycle_opens_meters_then_presets_and_closes_native_port(self):
        prepared={'inputs':{'partial':PARTIAL},'context':self.prior['prepared']['context'],
            'profile':self.prior['prepared']['profile'],'plan':self.plan,'saved_snapshot':self.saved}
        calls=[]
        with tempfile.TemporaryDirectory(dir=probe.ROOT/'build',prefix='TEST-saved-reload-') as folder:
            output=Path(folder)/'session';process=SimpleNamespace(pid=999,code=None)
            process.poll=lambda:process.code;process.wait=lambda timeout:process.code
            process.terminate=lambda:None
            def popen(args,**kwargs):
                profile=Path(next(v.split('=',1)[1] for v in args if v.startswith('--user-data-dir=')))
                (profile/'DevToolsActivePort').write_text('12345\n/fake\n');return process
            parent=self
            class CDP:
                def __init__(self,*args):
                    self.phase='initial';self.connected=False;self.meters=False;self.side=False
                    self.ws=SimpleNamespace(close=lambda:None)
                def call(self,name,args=None):
                    calls.append((name,args))
                    if name=='Input.dispatchKeyEvent' and args['type']=='keyDown':self.phase='reload_ack' if args['key']=='Enter' else 'marker_ack'
                    if name=='Browser.close':process.code=0
                def click(self,selector):
                    calls.append(('click',selector))
                    if selector=='#connBtn':self.connected=True;(output/'selection.json').write_text('{"test":true}')
                    if selector=='#meters':self.meters=True
                    if selector=='#presetBtn':self.side=True;self.meters=False
                def screenshot(self,path):return str(path)
                def evaluate(self,source):
                    calls.append(('evaluate',source))
                    if source==probe.STATE:
                        return {'ready':True,'profile':prepared['profile'],'demo':False,'connected':self.connected,
                            'initialReadsFinished':self.connected,'fw':prepared['context']['pong'],'gainPending':0,
                            'guard':{**copy.deepcopy(parent.guard),'phase':self.phase}}
                    if source=="document.getElementById('meters').classList.contains('open')":return self.meters
                    if source=="document.querySelector('.side').classList.contains('open')":return self.side
                    if source=='bank':return 0
                    if source in ('S.capSlot','S.curPre','S.snap'):return 0
                    if source=='S.gain':return prepared['plan']['gain']
                    if source.startswith('({gain:S.gain.slice()'):return {'gain':[0,0],'capture':0,'scene':0,'preset':0,'fatal':None}
                    if source=='HyperRigMini.profile':return prepared['profile']
                    if source=='__miniSavedReloadGuard.state':return copy.deepcopy(parent.guard)
                    if '__miniSavedReloadGuard.arm("marker")' in source:
                        if not self.meters:raise AssertionError('marker without visible gain popup')
                    if '__miniSavedReloadGuard.arm("reload")' in source:
                        if not self.side:raise AssertionError('reload without preset panel')
                    if source.startswith('(async()=>{') and '__miniSavedReloadGuard.stop()' in source:
                        return {'open':False,'closes':1,'closeError':None}
                    if 'return Pedal.busy' in source:return 0
                    return False
            class Server:
                server_port=1234
                def __init__(self,*args,**kwargs):pass
                def serve_forever(self):pass
                def shutdown(self):pass
                def server_close(self):pass
            def get(url,timeout):
                value=[{'type':'page','webSocketDebuggerUrl':'ws://offline'}] if url.endswith('/json/list') else {'test':True}
                return io.BytesIO(json.dumps(value).encode())
            snapshots=[changed(self.saved,advance=1),changed(self.saved,advance=2),
                       changed(self.saved,output=-1,advance=3),changed(self.saved,advance=4)]
            with (patch.object(probe,'prepare',return_value=prepared),patch.object(probe.subprocess,'Popen',side_effect=popen),
                  patch.object(probe.browser,'browser_path',return_value=Path('FAKE.exe')),patch.object(probe.browser,'CDP',CDP),
                  patch.object(probe.http.server,'ThreadingHTTPServer',Server),patch.object(probe,'urlopen',side_effect=get),
                  patch.object(probe.selection,'validate_selection') as choose,patch.object(probe.time,'sleep'),
                  patch.object(probe,'snapshot',side_effect=snapshots)):
                result=probe.run(prepared,output)
            self.assertEqual(result.get('error'),None);self.assertEqual(result.get('cleanup_error'),None)
            self.assertEqual(result['result'],'pass');self.assertTrue(result['retained_saved_reload_verified'])
            self.assertTrue(result['serial_port_closed'] and result['browser_process_stopped'] and result['local_server_stopped'])
            self.assertFalse(result['prior_save_reperformed'] or result['capture_write_performed'])
            choose.assert_called_once()
            def index(kind,text):return next(n for n,(k,v) in enumerate(calls) if k==kind and v==text)
            self.assertLess(index('click','#meters'),index('evaluate','__miniSavedReloadGuard.arm("marker")'))
            self.assertLess(index('click','#presetBtn'),index('evaluate','__miniSavedReloadGuard.arm("reload")'))
            self.assertEqual(sum(k=='Browser.close' for k,v in calls),1)


if __name__=='__main__':unittest.main()
