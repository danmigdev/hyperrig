"""Visible English HyperRig editor with the existing qualified MINI USB policy.

Derived from the previously tested MINI FX launcher. The product bundle adds
English presentation and HyperRig GitHub reporting to its sealed FX baseline.

The original mini-profile is the command policy. No readonly or one-shot guard
is installed. The observer records native lifecycle/PONG without authorizing,
blocking or retrying any command. Default/check-only performs no device I/O.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import partial
import http.server
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import launch_mini_desktop_readonly as window
from tools import probe_mini_browser_readonly as browser
from tools import mini_browser_windows as browser_windows
from tools import activate_mini_editor_ui as activation
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

require, sha, now = browser.require, browser.sha, window.now
FAMILIES = ['GAIN','PLOAD','PSAVE','SNAPSAVE','FXA','FXP','FXE','FXR']
QUALIFIER_SHA = '35ffb85d56d8a9821b9943ff63e3d58a874b9672680eec5ce0815fa0130d0234'
SERIAL_OPEN_EXTENSION = ROOT/'tools/mini_browser_serial_open.js'
OBSERVER = r"""(()=>{
 const state={opens:0,closes:0,activePorts:0,closeError:null,events:[],pongs:[],lastPort:null};
 const active=new WeakSet();
 const event=(kind,data={})=>{state.events.push({kind,time:performance.now(),utc:new Date().toISOString(),...data});
   if(state.events.length>256)state.events.shift();};
 if(typeof SerialPort==='undefined')throw Error('Native WebSerial unavailable');
 for(const method of ['open','close']){
   const original=SerialPort.prototype[method];
   SerialPort.prototype[method]=async function(...args){
     event('serial_'+method+'_intent');
     try{const value=await original.apply(this,args);
       if(method==='open'){state.opens++;if(!active.has(this)){active.add(this);state.activePorts++;}
         try{const info=this.getInfo();state.lastPort={vid:info.usbVendorId,pid:info.usbProductId};}
         catch(error){state.observationError=String(error);}}
       else{state.closes++;if(active.has(this)){active.delete(this);state.activePorts--;}
         state.closeError=null;}
       event('serial_'+method+'_complete');return value;
     }catch(error){if(method==='close')state.closeError=String(error);
       event('serial_'+method+'_error',{error:String(error)});throw error;}
   };
 }
 Object.defineProperty(window,'__miniEditorObservation',{value:{state,install(pedal){
   const original=pedal.onLine;
   pedal.onLine=function(line){if(/^PONG /.test(line)){state.pongs.push({line,utc:new Date().toISOString()});
     if(state.pongs.length>32)state.pongs.shift();}return original.call(this,line);};
 }}});
})()"""
STATE = """(()=>({ready:window.__urOk===true,title:document.title,
 connected:typeof S!=='undefined'&&S.connected,demo:typeof DEMO!=='undefined'&&DEMO,
 fw:typeof S!=='undefined'?S.fw:null,initialReadsFinished:typeof lvlTimer!=='undefined'&&!!lvlTimer,
 transport:typeof Pedal!=='undefined'&&Pedal.tr===SerialTransport?'usb-cdc':'other',
 profile:typeof HyperRigMini!=='undefined'?HyperRigMini.profile:null,
 observation:window.__miniEditorObservation?.state}))()"""
CLOSE = """(async()=>{
 document.body.inert=true;clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;
 await Pedal.chain;await Pedal.disconnect();
 return {open:SerialTransport.isOpen(),observation:__miniEditorObservation.state};
})()"""


def local(path):
    path=Path(path).resolve();require(path.is_relative_to(ROOT),'path leaves workspace');return path


def qualifier():
    module=importlib.import_module('tools.build_hyperrig_editor')
    require(QUALIFIER_SHA is not None and sha(Path(module.__file__).read_bytes())==QUALIFIER_SHA,
            'qualification verifier is not frozen or its source differs')
    return module


def prepare(bundle):
    global SERIAL_OPEN_EXTENSION
    folder=local(bundle)
    proof=qualifier().validate_bundle(folder)
    SERIAL_OPEN_EXTENSION=local(ROOT/proof['serial_open_extension'])
    profile=proof['profile'];caps=profile['capabilities']
    qualification=proof['qualification']
    require(qualification.get('kind')=='mini-FX-editor-qualification'
            and qualification.get('evidence_model')=='mini-representative-FX-protocol-v1'
            and qualification.get('hardware_protocol_exercised') is True
            and qualification.get('removal_evidence') and qualification.get('removal_replay'),
            'real FX and removal protocol evidence required')
    require(profile.get('hardware_verified') is True and caps.get('read') is True
            and caps.get('write') is False and caps.get('panel') is False
            and not profile.get('command_capabilities')
            and profile.get('family_capabilities')=={'usb-cdc':FAMILIES},
            'only the eight qualified USB families may be enabled')
    require(profile['image_sha256']==proof['image_sha256']
            and re.fullmatch(r'COM[1-9][0-9]{0,3}',proof['com'])
            and isinstance(proof['pong'],str) and not re.search(r'\bsafe\b',proof['pong']),
            'matching normal-mode image, COM and actual PONG required')
    app_dir=local(ROOT/proof['app_directory'])
    require(app_dir.is_relative_to(folder) and (app_dir/'tankmini.html').is_file(), 'qualified bundle app directory differs')
    return {'bundle_directory':folder.relative_to(ROOT).as_posix(),'bundle':proof,
            'app_directory':app_dir.relative_to(ROOT).as_posix(),'profile':profile,
            'com':proof['com'],'pong':proof['pong'],'image_sha256':proof['image_sha256'],
            'enabled_families':{'usb-cdc':FAMILIES},'profile_modified_by_launcher':False,
            'qualification_UI_FX_interactions_physically_tested':qualification['UI_FX_interactions_physically_tested']}


def connected_identity(value,prepared):
    require(value['profile']==prepared['profile'],'runtime profile differs from qualified bundle')
    if not (value.get('connected') and value.get('initialReadsFinished')):return False
    observation=value.get('observation') or {}
    require(value.get('demo') is False and value.get('transport')=='usb-cdc'
            and value.get('fw')==prepared['pong'] and observation.get('pongs')
            and observation['pongs'][-1]['line']==prepared['pong']
            and observation.get('activePorts')==1 and observation.get('lastPort')=={'vid':0x3654,'pid':0x5155},
            'actual USB/PONG differs from the qualified editor context')
    return True


def close_serial(cdp):
    value=cdp.evaluate(CLOSE);observation=value['observation']
    return {**value,'native_close_verified':value.get('open') is False and observation.get('activePorts')==0
            and observation.get('opens',0)>0 and observation.get('closes')==observation.get('opens')
            and observation.get('closeError') is None}


def activate_connection(cdp,report,output,publish):
    """Dismiss the tour and click Connect once; the user chooses the port."""
    state_script="({coach:!!document.querySelector('.coach'),connected:!!S.connected,connecting:!!S.connecting,open:SerialTransport.isOpen()})"
    report['connection_activation']={'actions':[],'port_selection_performed':False,'automatic_retry':False}
    observed=False
    try:
        cdp.evaluate(activation.INSTALL_OBSERVER);observed=True
        for selector,name in ((activation.SKIP,'skip'),(activation.CONNECT,'connect')):
            cdp.call('Page.bringToFront')
            report['connection_activation'][name+'_screenshot']=cdp.screenshot(output/(name+'.png'))
            state=cdp.evaluate(state_script)
            require(not(state['connected'] or state['connecting'] or state['open']),
                    'connection already started; do not click Connect twice')
            if name=='skip' and not state['coach']:
                report['connection_activation']['tour_already_absent']=True;continue
            if name=='connect':require(not state['coach'],'tour still covers Connect')
            point=activation.stable_target(cdp,selector)
            report['connection_activation']['actions'].append({'selector':selector,'point':point,'dispatch_intent':True})
            publish()
            for kind in ('mousePressed','mouseReleased'):
                cdp.call('Input.dispatchMouseEvent',{'type':kind,'x':point['x'],'y':point['y'],'button':'left','clickCount':1})
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                clicks=cdp.evaluate('__miniTourOperator.clicks')
                matches=[c for c in clicks if c['selector']==selector]
                require(len(matches)<=1,'duplicate observed connection click')
                if matches and matches[0]['trusted'] is True and (
                    name=='connect' or not cdp.evaluate(state_script)['coach']):
                    report['connection_activation']['actions'][-1]['observed_click']=matches[0];break
                time.sleep(.1)
            else:raise ValueError('trusted connection click was not observed; no retry')
        publish()
    finally:
        if observed:cdp.evaluate('__miniTourOperator.remove()')


def run(prepared,output):
    require(prepare(ROOT/prepared['bundle_directory'])==prepared,'qualified bundle changed before launch')
    output=local(output);require(output.is_relative_to(ROOT/'build') and not output.exists(),'new build session directory required')
    output.mkdir(parents=True);profile_dir=output/'isolated-profile';profile_dir.mkdir()
    app_dir=ROOT/prepared['app_directory']
    report={'schema':1,'kind':'mini-qualified-FX-editor-session','phase':'prepare','started_utc':now(),
            'prepared':prepared,'visible_window':True,'personal_profile_used':False,'profile_modified':False,
            'command_policy':'qualified original mini-profile','readonly_guard_installed':False,
            'one_shot_guard_installed':False,'passive_native_observer':True,'identity_verified':False,
            'serial_port_closed':None,'hardware_executed':None,'firmware_write':False,
            'preset_mutations_enabled':True,'enabled_families':prepared['enabled_families'],
            'audio_quality_verified':False,'held_recovery_verified':False,
            'source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
                (Path(__file__),SERIAL_OPEN_EXTENSION,Path(activation.__file__),Path(browser_windows.__file__),Path(qualifier().__file__),Path(window.__file__),Path(browser.__file__),
                 ROOT/'tools/verify_mini_browser.py',ROOT/'tools/mini_host_journal.py')}}
    save=lambda:atomic_write_json(output/'session.json',report)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(browser.LocalHandler,directory=str(app_dir),live=True))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    process=cdp=None;native_closed=False;browser_close_sent=False
    try:
        arguments=browser_windows.browser_arguments(browser_windows.browser_path(),profile_dir)
        report['browser_arguments']=arguments
        report['browser_configuration']=browser_windows.description(arguments)
        save()
        with (output/'browser-stderr.txt').open('wb') as stream:
            process=subprocess.Popen(arguments,stdout=subprocess.DEVNULL,
                stderr=stream,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        report['browser_process_id']=process.pid;save()
        endpoint=profile_dir/'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file():break
            require(process.poll() is None,'browser exited before CDP');time.sleep(.1)
        require(endpoint.is_file(),'CDP unavailable')
        devtools='http://127.0.0.1:'+endpoint.read_text().splitlines()[0]
        get=lambda suffix:json.loads(urlopen(devtools+suffix,timeout=5).read())
        page=next(p for p in get('/json/list') if p['type']=='page')
        cdp=browser.CDP(page['webSocketDebuggerUrl']);report['CDP_http']=devtools
        cdp.ws.settimeout(45)
        report['CDP_page_websocket']=page['webSocketDebuggerUrl'];report['browser']=get('/json/version')
        for domain in ('Runtime','Page','Log'):cdp.call(domain+'.enable')
        cdp.call('Page.addScriptToEvaluateOnNewDocument',{'source':OBSERVER})
        origin=f'http://127.0.0.1:{server.server_port}';report['origin']=origin
        cdp.call('Page.navigate',{'url':origin+'/tankmini.html?qualified_fx_editor=1'})
        for _ in range(150):
            if cdp.evaluate('window.__urOk===true'):break
            time.sleep(.05)
        value=cdp.evaluate(STATE)
        require(value['ready'] and value['profile']==prepared['profile'] and value['demo'] is False,'qualified editor bootstrap differs')
        report['serial_open_extension']=cdp.evaluate(SERIAL_OPEN_EXTENSION.read_text('utf-8')+
            '\ninstallMiniSerialOpenTimeout(SerialTransport);')
        require(report['serial_open_extension'].get('timeout_ms')==30000,'serial open timeout extension failed')
        save()
        cdp.evaluate('__miniEditorObservation.install(Pedal)')
        cdp.evaluate("(()=>{const n=document.getElementById('miniPortStatus');if(n)n.textContent='HyperRig MINI · USB: effects, volume and presets';})()")
        time.sleep(.55)
        report['phase']='awaiting_USB_selection'
        report['chooser_policy']={'previously_observed_COM':prepared['com'],'suggested_row':'Tank-M HyperRig ('+prepared['com']+')',
            'origin':origin,'browser_PID':process.pid,'automatic_CDP_selection':False}
        save();activate_connection(cdp,report,output,save)
        while process.poll() is None:
            if (output/'close.request').exists():
                report['close_requested_utc']=now();report['disconnect']=close_serial(cdp)
                native_closed=report['disconnect']['native_close_verified'];report['serial_port_closed']=native_closed
                save();browser_close_sent=True;cdp.call('Browser.close');break
            try:
                value=cdp.evaluate(STATE);report['latest']=value
                observation=value['observation']
                report['hardware_executed']=True if observation['opens']>0 else (
                    None if any(e['kind']=='serial_open_intent' for e in observation['events']) else False)
                if connected_identity(value,prepared) and not report['identity_verified']:
                    report.update(phase='connected_qualified_FX_USB',identity_verified=True,connected_utc=now())
                    atomic_write_json(output/'connected-proof.json',{'observed_utc':now(),'state':value,'prepared':prepared,
                        'qualified_families':prepared['enabled_families'],'audio_quality_verified':False})
                save()
            except Exception as error:
                report['observation_error']=repr(error);break
            time.sleep(1)
    except Exception as error:
        report['error']=repr(error)
    finally:
        if cdp and not browser_close_sent:
            try:
                report['disconnect']=close_serial(cdp);native_closed=report['disconnect']['native_close_verified']
                report['serial_port_closed']=native_closed
            except Exception as error:report['close_observation_error']=repr(error)
            try:browser_close_sent=True;cdp.call('Browser.close')
            except Exception:pass
        if cdp:cdp.ws.close()
        if process:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
        server.shutdown();server.server_close();thread.join(timeout=2)
        report.update(browser_process_stopped=process is None or process.poll() is not None,
                      local_server_stopped=True,finished_utc=now());save()
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only',action='store_true');parser.add_argument('--execute',action='store_true')
    parser.add_argument('--bundle',type=Path,default=ROOT/'build/hyperrig-mini-english-editor');parser.add_argument('--output',type=Path);parser.add_argument('--close-session',type=Path)
    args=parser.parse_args(argv)
    require(sum((args.check_only,args.execute,args.close_session is not None))<=1,'choose preflight, launch or local close request')
    if args.close_session:
        folder=local(args.close_session);report=json.loads(read_shared_bytes(folder/'session.json'))
        require(folder.is_relative_to(ROOT/'build') and report.get('kind')=='mini-qualified-FX-editor-session'
                and not report.get('finished_utc'),'one active owned qualified-editor session required')
        with (folder/'close.request').open('x',encoding='utf-8') as stream:stream.write(now()+'\n')
        print(json.dumps({'close_requested':True,'device_io':False}));return 0
    if not args.check_only and not args.execute:
        print(json.dumps({'device_io':False,'browser_started':False,'inputs_read':False,'enabled_without_real_evidence':False}));return 0
    require(args.bundle is not None,'qualified bundle required');prepared=prepare(args.bundle)
    if args.check_only:
        print(json.dumps({'preflight':'pass','device_io':False,'browser_started':False,'prepared':prepared}));return 0
    output=args.output or ROOT/'build'/('mini-fx-editor-session-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    report=run(prepared,output)
    print(json.dumps({k:report.get(k) for k in ('phase','error','observation_error','close_observation_error',
        'identity_verified','serial_port_closed','browser_process_stopped','local_server_stopped')}))
    return 1 if report.get('error') or report.get('observation_error') else 0


if __name__=='__main__':raise SystemExit(main())
