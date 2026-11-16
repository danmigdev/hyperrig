"""Visible local MINI editor; no I/O by default, explicit real readonly launch.

Accepts the normal-boot CDC observation and a separately completed PING log.
Does not require or claim a held-footswitch recovery trial. No firmware/profile
is changed; a new Chromium profile and localhost server die with the window.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from functools import partial
import http.server
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_browser_readonly as browser
from tools import probe_mini_app as readonly
from tools import probe_mini_app_first_preset as first
from tools import build_mini_app as app
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

require, sha = browser.require, browser.sha
APP = browser.DEFAULT_APP
MANIFEST = ROOT / 'build/hyperrig-mini-audio-v2/firmware-manifest.json'
MANIFEST_SHA = 'f119ab571a6cb04c8ca72513b5d18d614e079e756d209ce5794fbaeb4fe77d12'
EDITOR_REPORT = ROOT / 'build/hyperrig-mini-audio-v2/editor-report.json'
EDITOR_REPORT_SHA = 'aefc0ae544bed74965511c53d7d5628b438004fbcd34e3f4a11add50acd8d21e'
GUARD = ROOT / 'tools/mini_desktop_readonly_guard.js'
FULL_SHA = 'a35868ab3a4beb42454070ce46d67efaf695615a670de177343860e88d107c47'
STATE = """(() => ({ready:window.__urOk===true,title:document.title,
 connected:typeof S!=='undefined'&&S.connected,fw:typeof S!=='undefined'?S.fw:null,
 demo:typeof DEMO!=='undefined'&&DEMO,
 initialReadsFinished:typeof lvlTimer!=='undefined'&&!!lvlTimer,
 types:typeof S!=='undefined'?Object.keys(S.types).length:0,
 chain:typeof S!=='undefined'?S.chain:null,model:typeof S!=='undefined'?S.model:null,
 status:document.getElementById('stat')?.textContent,guard:(()=>{const s=globalThis.__miniDesktopGuard?.state;
 return s?{appInstalled:s.appInstalled,opens:s.opens,closes:s.closes,closeError:s.closeError,pongMatched:s.pongMatched,
 fatal:s.fatal,stopped:s.stopped,observedPong:s.observedPong,queryCount:s.wire.length,replyCount:s.replyCount,
 retainedReplyCount:s.replies.length,commandCount:s.commandCount,
 lastQuery:s.wire.at(-1)?.line,portInfo:s.portInfo}:null})()}))()"""


def now(): return datetime.now(timezone.utc).isoformat()


def local(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'path must stay inside the workspace')
    return path


def pinned(path, expected):
    path = local(path); raw = read_shared_bytes(path)
    require(re.fullmatch(r'[a-f0-9]{64}', expected or '') and sha(raw) == expected, 'supplied evidence hash differs: ' + str(path))
    return raw


def ref(path, raw=None):
    path = local(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes() if raw is None else raw)}


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.utcoffset() is not None, 'UTC-aware evidence timestamp required')
    return result


def validate_normal_boot(boot):
    require(boot.get('finished_utc') and boot.get('boot_mode') == 'normal-software-boot'
            and boot.get('buttons_confirmed_by_user') is False and boot.get('buttons_assumed') == 'released'
            and boot.get('held_button_boot_trial_performed') is False
            and boot.get('cold_power_cycle_tested') is False and boot.get('guard_causality_confirmed') is False,
            'explicit normal software boot with held recovery untested required')
    require(boot.get('candidate_sha256') == browser.IMAGE_SHA and boot.get('application_USB_enumerated') is True
            and boot.get('candidate_CDC_absent_before_reset') is True and boot.get('reset_submitted') is True
            and boot.get('firmware_write') is False and boot.get('automatic_retry') is False,
            'actual candidate CDC observation after one normal boot required')
    if boot.get('error'):
        require(boot.get('phase') == boot.get('error_phase') == 'identify_application_PING'
                and boot.get('app_identity_verified') is False,
                'only a recorded PING failure after CDC enumeration may be superseded by a later successful PING')
    else:
        require(boot.get('phase') == 'application_PONG_verified' and boot.get('app_identity_verified') is True
                and boot.get('serial_port_closed') is True, 'completed normal boot/PONG required')
    ports = boot.get('application_ports')
    require(isinstance(ports, list) and len(ports) == 1
            and (ports[0].get('vid'), ports[0].get('pid')) == (readonly.VID, readonly.PID)
            and re.fullmatch(r'COM[1-9][0-9]{0,3}', ports[0].get('device', '')), 'one exact normal-boot MINI COM required')
    require(stamp(boot['started_utc']) <= stamp(boot['finished_utc']), 'boot timestamps out of order')
    return ports[0]


def validate_ping(raw, boot, port):
    """Replay real retained raw bytes; no serial transport is constructed."""
    rows = [json.loads(line) for line in raw.splitlines() if line]
    def one(event):
        found = [item for item in rows if item.get('event') == event]
        require(len(found) == 1, 'one ' + event + ' event required'); return found[0]
    require(rows and rows[0].get('event') == 'start' and rows[-1].get('event') == 'port_closed',
            'completed PING journal and successful native CLI close required')
    start, selected, summary = one('start'), one('port_selected'), one('session_complete')
    one('port_opened'); one('port_closed')
    require(not any(row.get('event') in ('failed','session_failed','identity_rejected','port_close_failed')
                    or row.get('hardware_executed') is False for row in rows), 'failed or simulated PING cannot open the desktop editor')
    require(start.get('expected_image_sha256') == browser.IMAGE_SHA and start.get('expected_firmware') == browser.VERSION
            and start.get('mutations_enabled') is False and start.get('source') == json.loads(json.dumps(readonly.source_contract())),
            'PING candidate and frozen protocol source binding differ')
    require((selected.get('device'),selected.get('vid'),selected.get('pid')) == (port['device'],port['vid'],port['pid'])
            and summary.get('port') == {k:v for k,v in selected.items() if k not in ('utc','monotonic','event')},
            'PING port differs from the actual normal-boot CDC')
    require(summary.get('commands') == ['PING'] and summary.get('read_only_session_completed') is True
            and summary.get('expected_image_sha256') == browser.IMAGE_SHA and summary.get('audio_verified') is False
            and summary.get('firmware_writes_tested') is False, 'one real PING-only session required')
    start_time, end_time = stamp(start['utc']), stamp(rows[-1]['utc'])
    require(stamp(boot['started_utc']) <= start_time <= end_time, 'PING precedes the normal boot')
    if boot.get('error'):
        require(stamp(boot['finished_utc']) <= start_time, 'replacement PING must occur after the failed boot helper has closed')
    tape = first._TraceReplay(raw); replay = []
    probe = readonly.ReadOnlyProbe(tape,browser.VERSION,clock=tape.clock,
                                  log=lambda event,**fields:replay.append({'event':event,**fields}))
    probe.identify()
    require(tape.position == len(tape.exchanges) and not tape.pending and not probe.buffer,
            'PING journal contains extra commands or unconsumed bytes')
    keys = {'tx':('command','hex','timeout_seconds'),'rx':('command','hex','bytes'),
            'line':('command','line'),'async_line':('command','line'),'complete':('command','lines'),
            'identity_accepted':('target','firmware_version','pong','binary_hash_attested_by_device')}
    projection = lambda items:[(item['event'],{key:item[key] for key in keys[item['event']]})
                              for item in items if item.get('event') in keys]
    require(projection(rows) == projection(replay) and summary['identity'] == probe.identity,
            'recorded PING interpretation differs from native raw-byte replay')
    return {'schema':1,'target':'tank-mini','transport':'usb-cdc','vid':readonly.VID,'pid':readonly.PID,
            'com':port['device'],'pong':probe.identity['pong'],'image_sha256':browser.IMAGE_SHA,
            'serial_port_closed':True,'observed_utc':rows[-1]['utc'],'boot_mode':'normal-software-boot',
            'held_button_boot_trial_performed':False,'cold_power_cycle_tested':False,'image_hash_attested_by_device':False}


def validate_prior_close(raw,boot,port):
    """A failed PING can prove close, never identity. This enables only first PING."""
    rows=[json.loads(line) for line in raw.splitlines() if line]
    require(rows and rows[0].get('event')=='start' and rows[-1].get('event')=='port_closed',
            'prior diagnostic must have completed native serial close')
    def one(event):
        found=[row for row in rows if row.get('event')==event]
        require(len(found)==1,'one prior '+event+' required');return found[0]
    start,selected=one('start'),one('port_selected');one('port_opened');one('port_closed')
    require(not any(row.get('event')=='port_close_failed' or row.get('hardware_executed') is False for row in rows),
            'prior diagnostic close failed or evidence is simulated')
    require(start.get('expected_image_sha256')==browser.IMAGE_SHA and start.get('expected_firmware')==browser.VERSION
            and start.get('mutations_enabled') is False and start.get('source')==json.loads(json.dumps(readonly.source_contract())),
            'prior readonly diagnostic must bind the same candidate and protocol')
    require((selected.get('device'),selected.get('vid'),selected.get('pid'))==(port['device'],port['vid'],port['pid']),
            'prior diagnostic port differs from enumerated CDC')
    tx=[row for row in rows if row.get('event')=='tx']
    require(len(tx)==1 and tx[0].get('command')=='PING' and tx[0].get('hex')==b'PING\n'.hex(),
            'one PING-only closed diagnostic required for first handshake')
    require(any(row.get('event') in ('session_complete','session_failed') for row in rows)
            and stamp(boot['started_utc'])<=stamp(start['utc'])<=stamp(rows[-1]['utc']),
            'prior diagnostic is incomplete or predates the normal boot')
    return {'schema':1,'target':'tank-mini','transport':'usb-cdc','vid':readonly.VID,'pid':readonly.PID,
            'com':port['device'],'pong':None,'image_sha256':browser.IMAGE_SHA,'serial_port_closed':True,
            'observed_utc':rows[-1]['utc'],'boot_mode':'normal-software-boot','identity_verified':False,
            'held_button_boot_trial_performed':False,'cold_power_cycle_tested':False,'image_hash_attested_by_device':False}


def prepare(boot_path, boot_sha, ping_path, ping_sha, *, first_handshake=False):
    require(type(first_handshake) is bool,'explicit boolean first-handshake mode required')
    boot_raw, ping_raw = pinned(boot_path,boot_sha), pinned(ping_path,ping_sha)
    boot = json.loads(boot_raw); port = validate_normal_boot(boot)
    pins = boot.get('source_pins')
    require(isinstance(pins,dict) and pins, 'normal-boot source pins required')
    for name,digest in pins.items():
        require(sha(local(ROOT/name).read_bytes()) == digest, 'normal-boot pinned source changed: ' + name)
    install_ref = {'path':boot['installation_evidence_path'],'sha256':boot['installation_evidence_sha256']}
    installation = json.loads(app.local_evidence(install_ref,'verified installation'))
    require(installation.get('installed_image_verified') is True and installation.get('full_NOR_verified') is True
            and not installation.get('error') and installation.get('finished_utc')
            and installation['installation']['candidate_sha256'] == browser.IMAGE_SHA
            and installation['independent_full_validation']['external_regions_unchanged'] is True
            and installation['independent_full_validation']['full_NOR_sha256'] == FULL_SHA,
            'completed verified candidate installation required')
    require(stamp(installation['finished_utc']) <= stamp(boot['started_utc']), 'normal boot predates completed installation')
    evidence = validate_prior_close(ping_raw,boot,port) if first_handshake else validate_ping(ping_raw,boot,port)
    require(sha(MANIFEST.read_bytes()) == MANIFEST_SHA, 'base readonly manifest changed')
    current_profile = app.load_profile(MANIFEST)
    require(current_profile['image_sha256']==browser.IMAGE_SHA,'base candidate differs')
    # This base editor predates family grants. Check its retained derivation,
    # rather than regenerating a newer editor into the frozen app directory.
    editor=json.loads(pinned(EDITOR_REPORT,EDITOR_REPORT_SHA))
    for path,digest in editor['files'].items():
        require(sha(local(ROOT/path).read_bytes())==digest,'frozen base editor file changed: '+path)
    profile=editor['profile']
    require(profile['capabilities']['read'] is True and profile['capabilities']['write'] is False
            and profile['capabilities']['panel'] is False and not profile.get('family_capabilities')
            and not profile['command_capabilities'] and profile['image_sha256']==browser.IMAGE_SHA
            and profile['firmware_version']==browser.VERSION, 'unchanged readonly base profile required')
    return {'evidence':evidence,'profile':profile,'first_handshake':first_handshake,
            'boot_observation_had_PING_error':bool(boot.get('error')),
            'inputs':{'normal_boot':ref(boot_path,boot_raw),'PING':ref(ping_path,ping_raw),'manifest':ref(MANIFEST),
                      'installation':install_ref},
            'held_recovery_verified':False,'audio_verified':False,'preset_mutations_enabled':False}


def browser_arguments(executable,profile):
    return [str(executable),'--no-first-run','--no-default-browser-check','--disable-background-networking',
            '--disable-component-update','--disable-sync','--disable-extensions','--disable-background-mode',
            '--disable-features=MediaRouter,OptimizationHints','--disable-default-apps','--disable-breakpad',
            '--noerrdialogs','--window-size=1440,1000','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0',
            '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
            '--user-data-dir='+str(profile),'--app=about:blank']


def close_serial(cdp):
    # Original app cleanup drains reads. No query, reset or mutation is sent here.
    result = cdp.evaluate("""(async()=>{
      if(typeof S!=='undefined'&&S.connected)await connect();
      else if(typeof SerialTransport!=='undefined'&&SerialTransport.isOpen()){
        clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;Pedal.abort();await Pedal.disconnect();}
      __miniDesktopGuard.stop();
      return {open:SerialTransport.isOpen(),closes:__miniDesktopGuard.state.closes,closeError:__miniDesktopGuard.state.closeError};
    })()""")
    return {**result,'native_close_verified':not result['open'] and result['closes']==1 and not result['closeError']}


def run(prepared,output):
    output = local(output)
    require(output.is_relative_to(ROOT/'build') and not output.exists(),'new output directory under build required')
    # Recheck evidence before starting the visible window, even for a prepared API call.
    refs=prepared['inputs']
    fresh=prepare(ROOT/refs['normal_boot']['path'],refs['normal_boot']['sha256'],ROOT/refs['PING']['path'],refs['PING']['sha256'],
                  first_handshake=prepared.get('first_handshake',False))
    require(fresh==prepared,'prepared desktop evidence changed')
    output.mkdir(parents=True);profile=output/'isolated-profile';profile.mkdir()
    report={'schema':1,'kind':'mini-desktop-readonly-session','phase':'prepare','started_utc':now(),
            'evidence':prepared,'visible_window':True,'personal_profile_used':False,'demo':False,
            'mutations_enabled':False,'held_recovery_verified':False,'audio_verified':False,
            'identity_verified':False,'first_handshake':prepared.get('first_handshake',False),
            'serial_port_closed':False,'automatic_reconnect':False,'server_address':'127.0.0.1',
            'source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
                [Path(__file__),GUARD,Path(browser.__file__),ROOT/'tools/verify_mini_browser.py',
                 *(p for p in APP.iterdir() if p.is_file())]}}
    save=lambda:atomic_write_json(output/'session.json',report)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(browser.LocalHandler,directory=str(APP),live=True))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    process=cdp=None;get=None
    try:
        with (output/'browser-stderr.txt').open('wb') as stream:
            # The user explicitly requested the visible application window.
            process=subprocess.Popen(browser_arguments(browser.browser_path(),profile),stdout=subprocess.DEVNULL,stderr=stream,
                                     creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        report['browser_process_id']=process.pid;save()
        endpoint=profile/'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file():break
            require(process.poll() is None,'visible browser exited before CDP');time.sleep(.1)
        require(endpoint.is_file(),'CDP unavailable')
        devtools='http://127.0.0.1:'+endpoint.read_text().splitlines()[0]
        get=lambda suffix:json.loads(urlopen(devtools+suffix,timeout=5).read())
        report['browser']=get('/json/version');report['CDP_http']=devtools
        require(any(d['domain']=='DeviceAccess' for d in get('/json/protocol')['domains']),'DeviceAccess unavailable')
        page=next(p for p in get('/json/list') if p['type']=='page')
        cdp=browser.CDP(page['webSocketDebuggerUrl']);report['CDP_page_websocket']=page['webSocketDebuggerUrl']
        for domain in ('Runtime','Page','Log'):cdp.call(domain+'.enable')
        config={'live':True,'image_sha256':browser.IMAGE_SHA,'pong':prepared['evidence']['pong'],
                'firstHandshake':prepared.get('first_handshake',False),'version':browser.VERSION}
        cdp.call('Page.addScriptToEvaluateOnNewDocument',{'source':GUARD.read_text('utf-8')+
            '\ninstallMiniDesktopReadonlyGuard('+json.dumps(config)+');'})
        url=f'http://127.0.0.1:{server.server_port}/tankmini.html?desktop_readonly=1'
        report['url']=url;cdp.call('Page.navigate',{'url':url})
        for _ in range(150):
            if cdp.evaluate('window.__urOk===true'):break
            time.sleep(.05)
        initial=cdp.evaluate(STATE)
        require(initial['ready'] and initial['title']=='HyperRig for TANK MINI','editor bootstrap failed')
        require(cdp.evaluate('HyperRigMini.profile')==prepared['profile'],'base readonly profile differs')
        cdp.evaluate('__miniDesktopGuard.installApp(SerialTransport,Pedal,HyperRigMini.profile)')
        # Explain actual scope without changing capability flags or app files.
        cdp.evaluate("""(()=>{const n=document.createElement('div');n.id='miniDesktopReadonlyNote';
          n.textContent='MINI USB · verifica collegamento · sola lettura';
          n.style.cssText='position:fixed;bottom:4px;left:50%;transform:translateX(-50%);z-index:99999;background:#202a30;color:#fff;padding:7px 14px;border-radius:7px;font:12px sans-serif;pointer-events:none';
          document.body.appendChild(n);})()""")
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"):cdp.click('.ccall .tskip')
        cdp.call('DeviceAccess.enable');cdp.evaluate('__miniDesktopGuard.allowRequest()');cdp.click('#connBtn')
        report['phase']='connecting';save();handled=set();cursor=0;deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            snapshot=cdp.evaluate(STATE)
            events,cursor=cdp.events[cursor:],len(cdp.events)
            for item in events:
                if item.get('method')!='DeviceAccess.deviceRequestPrompted':continue
                prompt=item['params']
                if prompt['id'] in handled:continue
                report.setdefault('chooser_prompts',[]).append(prompt)
                try:selection=browser.select_device(prompt,prepared['evidence']['com'],allow_missing=True)
                except Exception:
                    cdp.call('DeviceAccess.cancelPrompt',{'id':prompt['id']});raise
                if selection is None:continue
                require(not handled,'second device chooser prohibited');handled.add(prompt['id'])
                cdp.call('DeviceAccess.selectPrompt',selection)
            require(not snapshot['guard']['fatal'],snapshot['guard']['fatal'])
            if snapshot['guard']['pongMatched'] and not report['identity_verified']:
                report['actual_identity']=readonly.inspect_pong(snapshot['guard']['observedPong'],browser.VERSION)
                if not prepared.get('first_handshake',False):
                    require(snapshot['guard']['observedPong']==prepared['evidence']['pong'],'observed PONG differs from prior proof')
                report['identity_verified']=True;report['identity_verified_utc']=now();save()
            if snapshot['connected'] and snapshot['initialReadsFinished']:break
            time.sleep(.1)
        require(not snapshot['demo'] and snapshot['connected'] and snapshot['initialReadsFinished'] and snapshot['guard']['pongMatched']
                and snapshot['guard']['opens']==1 and snapshot['fw']==snapshot['guard']['observedPong'],
                'real editor handshake/read bootstrap failed')
        report['actual_identity']=readonly.inspect_pong(snapshot['guard']['observedPong'],browser.VERSION)
        if not prepared.get('first_handshake',False):
            require(snapshot['guard']['observedPong']==prepared['evidence']['pong'],'observed PONG differs from prior proof')
        report['identity_verified']=True
        full=cdp.evaluate('__miniDesktopGuard.state')
        answered={row['line'] for row in full['commands'] if row['lines'] and not any(line.startswith('ERR') for line in row['lines'])}
        require({'PING','MODEL','MEM','FXT','FXS','PLIST','SNAPS'}<=answered,'actual initial readonly responses incomplete')
        report['phase']='connected_readonly';report['connected_utc']=now();report['initial_state']=snapshot
        cdp.evaluate("document.getElementById('miniDesktopReadonlyNote').textContent='MINI USB reale · sola lettura · recupero con tasti e audio ancora da verificare'")
        report['connected_screenshot']=cdp.screenshot(output/'connected.png')
        with (output/'connected-proof.json').open('x',encoding='utf-8') as stream:
            json.dump({'observed_utc':now(),'state':snapshot,'guard':full,'inputs':prepared['inputs'],
                       'held_recovery_verified':False,'audio_verified':False,'mutations_enabled':False},stream,indent=2)
        save()
    except Exception as error:
        report['phase']='connection_failed';report['error']=repr(error)
        try:save()
        except Exception as publication_error:report['publication_error']=repr(publication_error)
        if cdp:
            try:report['disconnect']=close_serial(cdp);report['serial_port_closed']=report['disconnect']['native_close_verified']
            except Exception as close_error:report['disconnect_error']=repr(close_error)
            try:report['failed_guard']=cdp.evaluate('__miniDesktopGuard.state')
            except Exception:pass
            try:cdp.evaluate("document.getElementById('miniDesktopReadonlyNote').textContent='Collegamento non verificato: vedere il report locale. Nessun tentativo automatico.'")
            except Exception:pass
            try:save()
            except Exception as publication_error:report['publication_error']=repr(publication_error)
    try:
        # Keep the visible window and server until the user closes them. Monitoring
        # evaluates page state only; it sends no additional pedal commands.
        last_saved=0
        while process and process.poll() is None and not report.get('publication_error'):
            if (output/'close.request').exists():
                report['close_requested_utc']=now()
                if cdp:
                    report['disconnect']=close_serial(cdp);report['serial_port_closed']=report['disconnect']['native_close_verified']
                    report['last_guard']=cdp.evaluate('__miniDesktopGuard.state');save();cdp.call('Browser.close')
                break
            if cdp:
                try:
                    latest=cdp.evaluate(STATE);report['latest']=latest;report['demo']=latest['demo']
                    if latest['demo']:report['phase']='offline_demo_selected_by_user'
                    if latest.get('guard',{}).get('fatal') and report['phase']=='connected_readonly':
                        report['phase']='readonly_guard_stopped';report['error']=latest['guard']['fatal']
                        report['disconnect']=close_serial(cdp);report['serial_port_closed']=report['disconnect']['native_close_verified']
                    elif latest.get('guard',{}).get('closes')==1 and not latest['guard'].get('closeError'):
                        report['serial_port_closed']=not latest['connected']
                    if time.monotonic()-last_saved>=2:save();last_saved=time.monotonic()
                except Exception as error:
                    pages=[]
                    try:pages=[p for p in get('/json/list') if p['type']=='page'] if get else []
                    except Exception:pass
                    if not pages:
                        report['window_closed_utc']=now();break
                    report['monitor_error']=repr(error);save();break
            time.sleep(1)
    finally:
        if cdp:
            try:
                if process and process.poll() is None:
                    report['disconnect']=close_serial(cdp);report['serial_port_closed']=report['disconnect']['native_close_verified']
                    report['last_guard']=cdp.evaluate('__miniDesktopGuard.state')
            except Exception as error:report['final_close_observation_error']=repr(error)
            try:cdp.call('Browser.close')
            except Exception:pass
            cdp.ws.close()
        if process:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
        server.shutdown();server.server_close();thread.join(timeout=2)
        report['browser_process_stopped']=process is None or process.poll() is not None
        report['local_server_stopped']=True;report['finished_utc']=now();save()
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--boot-run',type=Path);parser.add_argument('--boot-sha256')
    parser.add_argument('--ping-log',type=Path);parser.add_argument('--ping-sha256')
    parser.add_argument('--first-handshake',action='store_true',help='allow a closed failed PING log; identity must be observed by WebSerial')
    parser.add_argument('--output',type=Path);parser.add_argument('--close-session',type=Path)
    args=parser.parse_args(argv)
    require(sum((args.execute,args.check_only,args.close_session is not None))<=1,'choose launch, preflight or local close request')
    if args.close_session:
        output=local(args.close_session);report=json.loads(read_shared_bytes(output/'session.json'))
        require(output.is_relative_to(ROOT/'build') and report.get('kind')=='mini-desktop-readonly-session'
                and not report.get('finished_utc'),'one active owned desktop session required')
        with (output/'close.request').open('x',encoding='utf-8') as stream:stream.write(now()+'\n')
        print(json.dumps({'close_requested':True,'device_io':False}));return 0
    if not args.execute and not args.check_only:
        print(json.dumps({'device_io':False,'browser_started':False,'inputs_read':False,
                          'plan':'Normal-boot CDC + later closed raw PING proof, visible isolated readonly editor; no held trial claim'}));return 0
    require(all((args.boot_run,args.boot_sha256,args.ping_log,args.ping_sha256)),'boot and completed PING paths with exact hashes required')
    prepared=prepare(args.boot_run,args.boot_sha256,args.ping_log,args.ping_sha256,first_handshake=args.first_handshake)
    if args.check_only:
        print(json.dumps({'preflight':'pass','device_io':False,'browser_started':False,'evidence':prepared['evidence']}));return 0
    require(args.output is not None,'new output directory required')
    result=run(prepared,args.output)
    print(json.dumps({key:result.get(key) for key in ('phase','error','serial_port_closed','browser_process_stopped','local_server_stopped')}))
    return 0 if result.get('connected_utc') and not result.get('error') else 1


if __name__=='__main__':raise SystemExit(main())
