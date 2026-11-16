"""Offline launcher and passive observer tests; all browser/device calls are fake."""
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

from tools import launch_mini_editor as launcher


class QualifiedEditorLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=launcher.ROOT/'build',prefix='TEST-qualified-editor-')
        self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)
        self.bundle=self.folder/'bundle';self.app=self.bundle/'app'/'web';self.app.mkdir(parents=True)
        (self.app/'tankmini.html').write_text('OFFLINE TEST FIXTURE; NOT A QUALIFIED BUNDLE')
        self.profile={'hardware_verified':True,'capabilities':{'read':True,'write':False,'panel':False},
                      'command_capabilities':{},'family_capabilities':{'usb-cdc':launcher.FAMILIES},'image_sha256':'a'*64}
        self.metadata={'profile':self.profile,'app_directory':self.app.relative_to(launcher.ROOT).as_posix(),
            'image_sha256':'a'*64,'com':'COM123','pong':'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11',
            'manifest':{'path':'OFFLINE TEST ONLY','sha256':'b'*64},'qualification':{'offline_fixture':True},'refs':{}}
        self.fake=SimpleNamespace(__file__=launcher.__file__,validate_bundle=lambda path:copy.deepcopy(self.metadata))

    def prepared(self):
        with patch.object(launcher,'qualifier',return_value=self.fake):return launcher.prepare(self.bundle)

    def test_default_performs_no_evidence_read_browser_or_device_IO(self):
        with patch.object(launcher,'prepare',side_effect=AssertionError('read')),contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(launcher.main([]),0)
        value=json.loads(stream.getvalue());self.assertFalse(value['device_io'] or value['browser_started'] or value['inputs_read'])

    def test_preflight_uses_only_bundle_verifier_and_preserves_exact_USB_scope(self):
        calls=[]
        def validate(path):calls.append(path);return copy.deepcopy(self.metadata)
        self.fake.validate_bundle=validate
        with patch.object(launcher,'qualifier',return_value=self.fake):prepared=launcher.prepare(self.bundle)
        self.assertEqual(calls,[self.bundle]);self.assertEqual(prepared['enabled_families'],{'usb-cdc':launcher.FAMILIES})
        self.assertFalse(prepared['profile_modified_by_launcher'])
        for fault in ('BLE','extra','missing','write','panel','unqualified','safe','image','outside'):
            before=copy.deepcopy(self.metadata)
            if fault=='BLE':self.metadata['profile']['family_capabilities']['ble-nus']=['GAIN']
            elif fault=='extra':self.metadata['profile']['family_capabilities']['usb-cdc']=launcher.FAMILIES+['PDEL']
            elif fault=='missing':self.metadata['profile']['family_capabilities']['usb-cdc']=['GAIN']
            elif fault in ('write','panel'):self.metadata['profile']['capabilities'][fault]=True
            elif fault=='unqualified':self.metadata['profile']['hardware_verified']=False
            elif fault=='safe':self.metadata['pong']+=' safe'
            elif fault=='image':self.metadata['image_sha256']='b'*64
            else:self.metadata['app_directory']='tools'
            with self.subTest(fault=fault),patch.object(launcher,'qualifier',return_value=self.fake),self.assertRaises(ValueError):
                launcher.prepare(self.bundle)
            self.metadata=before

    def test_check_only_never_starts_browser(self):
        with (patch.object(launcher,'qualifier',return_value=self.fake),
              patch.object(launcher,'run',side_effect=AssertionError('browser')),
              contextlib.redirect_stdout(io.StringIO()) as stream):
            self.assertEqual(launcher.main(['--check-only','--bundle',str(self.bundle)]),0)
        self.assertEqual(json.loads(stream.getvalue())['preflight'],'pass')

    def test_observation_failure_is_reported_and_has_nonzero_exit(self):
        report={'phase':'connected_qualified_USB','error':None,'observation_error':'offline monitor failure',
                'close_observation_error':'close not observed','serial_port_closed':None}
        with (patch.object(launcher,'qualifier',return_value=self.fake),
              patch.object(launcher,'run',return_value=report),contextlib.redirect_stdout(io.StringIO()) as stream):
            self.assertEqual(launcher.main(['--execute','--bundle',str(self.bundle)]),1)
        summary=json.loads(stream.getvalue())
        self.assertEqual(summary['observation_error'],'offline monitor failure')
        self.assertEqual(summary['close_observation_error'],'close not observed')
        self.assertIsNone(summary['serial_port_closed'])

    def test_actual_identity_requires_native_USB_and_real_observed_PONG(self):
        prepared=self.prepared()
        value={'profile':prepared['profile'],'connected':True,'initialReadsFinished':True,'demo':False,
               'transport':'usb-cdc','fw':prepared['pong'],
               'observation':{'pongs':[{'line':prepared['pong']}],'activePorts':1,'lastPort':{'vid':0x3654,'pid':0x5155}}}
        self.assertTrue(launcher.connected_identity(value,prepared))
        for fault in ('demo','transport','fw','pong','native','pid'):
            bad=copy.deepcopy(value)
            if fault=='demo':bad['demo']=True
            elif fault=='transport':bad['transport']='ble-nus'
            elif fault=='fw':bad['fw']='PONG wrong'
            elif fault=='pong':bad['observation']['pongs']=[]
            elif fault=='native':bad['observation']['activePorts']=0
            else:bad['observation']['lastPort']['pid']=0
            with self.subTest(fault=fault),self.assertRaises(ValueError):launcher.connected_identity(bad,prepared)

    def test_passive_observer_changes_no_policy_or_write_and_propagates_native_errors(self):
        node=shutil.which('node')
        if not node:self.skipTest('existing Node unavailable; no installation')
        program=r"""const source=JSON.parse(require('fs').readFileSync(0,'utf8'));
global.window=global;global.SerialPort=class {async open(){if(this.active)throw Error('already open');this.active=true;}
 async close(){if(!this.active)throw Error('not open');this.active=false;}write(s){return s;}
 getInfo(){return {usbVendorId:0x3654,usbProductId:0x5155};}};
const write=SerialPort.prototype.write;eval(source);
(async()=>{const p=new SerialPort();const pedal={onLine(line){return 'original '+line;}};
__miniEditorObservation.install(pedal);
if(pedal.onLine('PONG actual')!=='original PONG actual')throw Error('original handler');
for(let i=0;i<2;i++){await p.open();await p.close();}
if(SerialPort.prototype.write!==write||p.write('arbitrary')!=='arbitrary')throw Error('policy');
let rejected=false;try{await p.close();}catch(e){rejected=true;}
const s=__miniEditorObservation.state;
if(!rejected||s.opens!==2||s.closes!==2||s.activePorts!==0||!s.closeError||s.pongs[0].line!=='PONG actual')throw Error('audit');
console.log('pass');})().catch(e=>{console.error(e);process.exitCode=1;});"""
        result=subprocess.run([node,'-e',program],input=json.dumps(launcher.OBSERVER),capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),'pass')

    def test_clean_close_requires_actual_native_completion_not_null_app_port(self):
        good={'open':False,'observation':{'activePorts':0,'opens':2,'closes':2,'closeError':None}}
        cdp=SimpleNamespace(evaluate=lambda script:good)
        self.assertTrue(launcher.close_serial(cdp)['native_close_verified'])
        for key,value in (('activePorts',1),('closes',1),('closeError','native error'),('opens',0)):
            bad=copy.deepcopy(good);bad['observation'][key]=value
            with self.subTest(key=key):self.assertFalse(launcher.close_serial(SimpleNamespace(evaluate=lambda script:bad))['native_close_verified'])

    def test_local_close_request_sends_no_device_command(self):
        folder=self.folder/'session';folder.mkdir()
        (folder/'session.json').write_text(json.dumps({'kind':'mini-qualified-editor-session','finished_utc':None}))
        with patch.object(launcher,'qualifier',side_effect=AssertionError('unneeded verification')),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(launcher.main(['--close-session',str(folder)]),0)
        self.assertTrue((folder/'close.request').is_file())

    def test_fake_lifecycle_keeps_editor_until_close_and_does_not_reobserve_closed_CDP(self):
        prepared=self.prepared();output=self.folder/'run';calls=[]
        process=SimpleNamespace(pid=12345,code=None)
        process.poll=lambda:process.code
        process.wait=lambda timeout:process.code
        process.terminate=lambda:calls.append(('unexpected_terminate',None))
        def popen(args,**kwargs):
            profile=Path(next(x.split('=',1)[1] for x in args if x.startswith('--user-data-dir=')))
            (profile/'DevToolsActivePort').write_text('12345\n/fake\n')
            return process
        observer={'opens':1,'closes':0,'activePorts':1,'closeError':None,'lastPort':{'vid':0x3654,'pid':0x5155},
                  'pongs':[{'line':prepared['pong']}],'events':[{'kind':'serial_open_complete'}]}
        class CDP:
            def __init__(self,*args):
                self.connected=False;self.closed=False
                self.ws=SimpleNamespace(close=lambda:calls.append(('wsclose',None)),
                    settimeout=lambda seconds:calls.append(('socket_timeout',seconds)))
            def call(self,name,args=None):
                calls.append((name,args))
                if name=='Browser.close':self.closed=True;process.code=0
            def click(self,selector):calls.append(('click',selector));self.connected=True
            def evaluate(self,source):
                if self.closed:raise AssertionError('CDP queried after Browser.close')
                if source.endswith('installMiniSerialOpenTimeout(SerialTransport);'):return {'timeout_ms':30000}
                if source=='window.__urOk===true':return True
                if source==launcher.STATE:
                    if self.connected:(output/'close.request').write_text('offline test close request')
                    return {'ready':True,'profile':prepared['profile'],'demo':False,'connected':self.connected,
                        'initialReadsFinished':self.connected,'transport':'usb-cdc','fw':prepared['pong'],
                        'observation':copy.deepcopy(observer)}
                if source==launcher.CLOSE:
                    observer.update(closes=1,activePorts=0)
                    calls.append(('native_close_observed',None))
                    return {'open':False,'observation':copy.deepcopy(observer)}
                return False
        class Server:
            server_port=12000
            def __init__(self,*args,**kwargs):pass
            def serve_forever(self):pass
            def shutdown(self):calls.append(('server_shutdown',None))
            def server_close(self):calls.append(('server_close',None))
        def urlopen(url,timeout):
            value=[{'type':'page','webSocketDebuggerUrl':'ws://offline-test'}] if url.endswith('/json/list') else {'Browser':'offline fixture'}
            return io.BytesIO(json.dumps(value).encode())
        with (patch.object(launcher,'qualifier',return_value=self.fake),patch.object(launcher.subprocess,'Popen',side_effect=popen),
              patch.object(launcher.browser_windows,'browser_path',return_value=Path('OFFLINE-fake.exe')),
              patch.object(launcher.browser,'CDP',CDP),patch.object(launcher.http.server,'ThreadingHTTPServer',Server),
              patch.object(launcher,'urlopen',side_effect=urlopen),patch.object(launcher.time,'sleep')):
            report=launcher.run(prepared,output)
        self.assertEqual(report['phase'],'connected_qualified_USB')
        self.assertTrue(report['identity_verified'] and report['serial_port_closed'])
        self.assertTrue(report['local_server_stopped'] and report['browser_process_stopped'])
        self.assertFalse(report['readonly_guard_installed'] or report['one_shot_guard_installed'])
        self.assertEqual(sum(name=='Browser.close' for name,_ in calls),1)
        self.assertFalse(any(name=='unexpected_terminate' for name,_ in calls))
        self.assertNotIn('close_observation_error',report)
        self.assertEqual(report['browser_configuration'],launcher.browser_windows.description(report['browser_arguments']))
        self.assertIn('tools/mini_browser_windows.py',report['source_sha256'])
        self.assertIn('tools/mini_browser_serial_open.js',report['source_sha256'])
        self.assertIn(('socket_timeout',45),calls)
        self.assertEqual(report['serial_open_extension']['timeout_ms'],30000)


if __name__=='__main__':unittest.main()
