"""First WebSerial client after the separately verified v3 normal boot.

No prior PING is invented or required: v11 opens no COM. The original editor
must obtain a real PONG before its readonly queries. Lifecycle and query guard
reuse the frozen desktop implementation; no frozen profile or source changes.
Default/check-only does not start a browser or access any device.
"""
from __future__ import annotations
import argparse
from functools import partial
import http.server
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import launch_mini_desktop_readonly as base
from tools import probe_mini_browser_readonly as browser
from tools import probe_mini_app as readonly
from tools import build_mini_app as app
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

require, sha = browser.require, browser.sha
now, stamp, browser_arguments, close_serial, STATE = base.now, base.stamp, base.browser_arguments, base.close_serial, base.STATE
IMAGE_SHA = '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c'
VERSION = 'tankm_fw M5.71 rel ble'
APP = ROOT/'build/hyperrig-mini-audio-v3/app/web'
MANIFEST = ROOT/'build/hyperrig-mini-audio-v3/firmware-manifest.json'
MANIFEST_SHA = 'd901cc0d673b7f477bc9000be16d95d195b916ffb4e26f512ed00048b6c27deb'
EDITOR_REPORT = ROOT/'build/hyperrig-mini-audio-v3/editor-report.json'
EDITOR_REPORT_SHA = '0b34b808021c116b97cbb921caf428381b60d8a9ee24024e41941de575b1643e'
GUARD = ROOT/'tools/mini_desktop_readonly_guard.js'
GUARD_SHA = 'f192b65e1323458f6bc72f761047363337fa56ac4d297d3bb30554f87a569eff'
BASE_SHA = 'ffe876c4ab1ac0f4ea051056369dc70f124d5ba0a3168dff71aea9bc5425f412'
HANDSHAKE_TIMEOUT_SECONDS = 120
BOOT_RUNNER = ROOT/'analysis/hardware/run_mini_first_boot_v11.py'
_spec = importlib.util.spec_from_file_location('mini_v11_boot_for_desktop', BOOT_RUNNER)
boot_runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(boot_runner)


def local(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'path must stay inside the workspace')
    return path


def pinned(path, expected):
    path = local(path); raw = read_shared_bytes(path)
    require(re.fullmatch(r'[a-f0-9]{64}', expected or '') and sha(raw) == expected,
            'supplied evidence hash differs: '+str(path))
    return raw


def ref(path, raw=None):
    path = local(path)
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': sha(read_shared_bytes(path) if raw is None else raw)}


def validate_normal_boot(boot):
    require(boot.get('finished_utc') and not boot.get('error')
            and boot.get('phase') == 'application_USB_observed'
            and boot.get('boot_mode') == 'normal-software-boot'
            and boot.get('buttons_confirmed_by_user') is False and boot.get('buttons_assumed') == 'released'
            and boot.get('held_button_boot_trial_performed') is False
            and boot.get('cold_power_cycle_tested') is False and boot.get('guard_causality_confirmed') is False,
            'completed v11 normal boot with held/cold recovery untested required')
    require(boot.get('candidate_sha256') == IMAGE_SHA and boot.get('application_USB_enumerated') is True
            and boot.get('candidate_CDC_absent_before_reset') is True and boot.get('reset_submitted') is True
            and boot.get('slot_A_inactive_verified') is True and boot.get('known_live_slot_before_reset') == boot_runner.B
            and boot.get('firmware_write') is False and boot.get('automatic_retry') is False
            and boot.get('serial_port_opened') is False and boot.get('PING_attempted') is False
            and boot.get('app_identity_verified') is False and boot.get('audio_verified') is False,
            'actual v3 CDC observation without a Python COM/PING or invented app/audio proof required')
    ports = boot.get('application_ports')
    require(isinstance(ports, list) and len(ports) == 1
            and (ports[0].get('vid'), ports[0].get('pid')) == (readonly.VID, readonly.PID)
            and re.fullmatch(r'COM[1-9][0-9]{0,3}', ports[0].get('device', '')), 'one exact v3 MINI COM required')
    require(stamp(boot['started_utc']) <= stamp(boot['finished_utc']), 'boot timestamps out of order')
    return ports[0]


def prepare(boot_path, boot_sha):
    boot_raw = pinned(boot_path, boot_sha)
    boot = json.loads(boot_raw); port = validate_normal_boot(boot)
    pins = boot.get('source_pins')
    require(isinstance(pins, dict) and pins, 'normal-boot source and evidence pins required')
    require(pins.get(BOOT_RUNNER.relative_to(ROOT).as_posix()) == sha(BOOT_RUNNER.read_bytes()),
            'actual v11 runner source must be pinned')
    for name, digest in pins.items():
        pinned(ROOT/name, digest)
    installation, verification = boot_runner.validate_upgrade(pins)
    require(boot.get('upgrade_verification') == verification
            and boot.get('installation_evidence_path') == verification['run']['path']
            and boot.get('installation_evidence_sha256') == verification['run']['sha256']
            and boot.get('MCN_cleanup_evidence_path') == verification['MCN']['path']
            and boot.get('MCN_cleanup_evidence_sha256') == verification['MCN']['sha256'],
            'normal boot does not bind the independently verified v3 upgrade')
    require(stamp(installation['finished_utc']) <= stamp(boot['started_utc']), 'boot predates completed upgrade')
    pinned(MANIFEST, MANIFEST_SHA); pinned(GUARD, GUARD_SHA); pinned(Path(base.__file__), BASE_SHA)
    profile = app.load_profile(MANIFEST)
    require(profile['image_sha256'] == IMAGE_SHA, 'base v3 candidate differs')
    editor = json.loads(pinned(EDITOR_REPORT, EDITOR_REPORT_SHA))
    for path, digest in editor['files'].items(): pinned(ROOT/path, digest)
    profile = editor['profile']
    require(profile['capabilities']['read'] is True and profile['capabilities']['write'] is False
            and profile['capabilities']['panel'] is False and not profile.get('family_capabilities')
            and not profile['command_capabilities'] and profile['image_sha256'] == IMAGE_SHA
            and profile['firmware_version'] == VERSION, 'unchanged readonly v3 profile required')
    evidence = {'schema': 1, 'target': 'tank-mini', 'transport': 'usb-cdc', 'vid': readonly.VID, 'pid': readonly.PID,
        'com': port['device'], 'pong': None, 'image_sha256': IMAGE_SHA, 'observed_utc': boot['finished_utc'],
        'boot_mode': 'normal-software-boot', 'identity_verified': False,
        'serial_port_opened_by_boot': False, 'prior_PING_evidence_required': False,
        'held_button_boot_trial_performed': False, 'cold_power_cycle_tested': False, 'image_hash_attested_by_device': False}
    return {'evidence': evidence, 'profile': profile, 'first_handshake': True,
        'inputs': {'normal_boot': ref(boot_path, boot_raw), 'manifest': ref(MANIFEST),
                   'installation': verification['run'], 'independent': verification['independent']},
        'held_recovery_verified': False, 'audio_verified': False, 'preset_mutations_enabled': False}


def run(prepared,output):
    output = local(output)
    require(output.is_relative_to(ROOT/'build') and not output.exists(),'new output directory under build required')
    # Recheck evidence before starting the visible window, even for a prepared API call.
    refs=prepared['inputs']
    fresh=prepare(ROOT/refs['normal_boot']['path'],refs['normal_boot']['sha256'])
    require(fresh==prepared,'prepared desktop evidence changed')
    output.mkdir(parents=True);profile=output/'isolated-profile';profile.mkdir()
    report={'schema':1,'kind':'mini-desktop-readonly-v3-session','phase':'prepare','started_utc':now(),
            'evidence':prepared,'visible_window':True,'personal_profile_used':False,'demo':False,
            'mutations_enabled':False,'held_recovery_verified':False,'audio_verified':False,
            'identity_verified':False,'first_handshake':prepared.get('first_handshake',False),
            'handshake_timeout_seconds':HANDSHAKE_TIMEOUT_SECONDS,
            'serial_port_closed':False,'automatic_reconnect':False,'server_address':'127.0.0.1',
            'source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
                [Path(__file__),GUARD,Path(base.__file__),BOOT_RUNNER,Path(browser.__file__),ROOT/'tools/verify_mini_browser.py',
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
        page=next(p for p in get('/json/list') if p['type']=='page')
        cdp=browser.CDP(page['webSocketDebuggerUrl']);report['CDP_page_websocket']=page['webSocketDebuggerUrl']
        for domain in ('Runtime','Page','Log'):cdp.call(domain+'.enable')
        config={'live':True,'image_sha256':IMAGE_SHA,'pong':prepared['evidence']['pong'],
                'firstHandshake':prepared.get('first_handshake',False),'version':VERSION}
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
          n.textContent='MINI USB · connection check · read only';
          n.style.cssText='position:fixed;bottom:4px;left:50%;transform:translateX(-50%);z-index:99999;background:#202a30;color:#fff;padding:7px 14px;border-radius:7px;font:12px sans-serif;pointer-events:none';
          document.body.appendChild(n);})()""")
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"):cdp.click('.ccall .tskip')
        report['chooser_policy']={'method':'external Windows UI Automation',
            'expected_COM':prepared['evidence']['com'], 'expected_origin':f'http://127.0.0.1:{server.server_port}',
            'owned_browser_PID':process.pid, 'automatic_CDP_selection':False,
            'selection_sidecar_required_for_UIA_attribution':True, 'selection_verified_by_adapter':False}
        cdp.evaluate('__miniDesktopGuard.allowRequest()');cdp.click('#connBtn')
        report['phase']='awaiting_exact_UIA_selection';save()
        deadline=time.monotonic()+HANDSHAKE_TIMEOUT_SECONDS
        while time.monotonic()<deadline:
            snapshot=cdp.evaluate(STATE)
            require(not snapshot['guard']['fatal'],snapshot['guard']['fatal'])
            if snapshot['guard']['pongMatched'] and not report['identity_verified']:
                report['actual_identity']=readonly.inspect_pong(snapshot['guard']['observedPong'],VERSION)
                if not prepared.get('first_handshake',False):
                    require(snapshot['guard']['observedPong']==prepared['evidence']['pong'],'observed PONG differs from prior proof')
                report['identity_verified']=True;report['identity_verified_utc']=now();save()
            if snapshot['connected'] and snapshot['initialReadsFinished']:break
            time.sleep(.1)
        require(not snapshot['demo'] and snapshot['connected'] and snapshot['initialReadsFinished'] and snapshot['guard']['pongMatched']
                and snapshot['guard']['opens']==1 and snapshot['fw']==snapshot['guard']['observedPong'],
                'real editor handshake/read bootstrap failed')
        report['actual_identity']=readonly.inspect_pong(snapshot['guard']['observedPong'],VERSION)
        if not prepared.get('first_handshake',False):
            require(snapshot['guard']['observedPong']==prepared['evidence']['pong'],'observed PONG differs from prior proof')
        report['identity_verified']=True
        full=cdp.evaluate('__miniDesktopGuard.state')
        answered={row['line'] for row in full['commands'] if row['lines'] and not any(line.startswith('ERR') for line in row['lines'])}
        require({'PING','MODEL','MEM','FXT','FXS','PLIST','SNAPS'}<=answered,'actual initial readonly responses incomplete')
        report['phase']='connected_readonly';report['connected_utc']=now();report['initial_state']=snapshot
        cdp.evaluate("document.getElementById('miniDesktopReadonlyNote').textContent='Live MINI USB · read only · footswitch recovery and audio still require verification'")
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
            try:cdp.evaluate("document.getElementById('miniDesktopReadonlyNote').textContent='Connection not verified: see the local report. No automatic retry.'")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true'); parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--boot-run', type=Path); parser.add_argument('--boot-sha256')
    parser.add_argument('--output', type=Path); parser.add_argument('--close-session', type=Path)
    args = parser.parse_args(argv)
    require(sum((args.execute, args.check_only, args.close_session is not None)) <= 1,
            'choose launch, preflight or local close request')
    if args.close_session:
        output = local(args.close_session); report = json.loads(read_shared_bytes(output/'session.json'))
        require(output.is_relative_to(ROOT/'build') and report.get('kind') == 'mini-desktop-readonly-v3-session'
                and not report.get('finished_utc'), 'one active owned v3 desktop session required')
        with (output/'close.request').open('x', encoding='utf-8') as stream: stream.write(now()+'\n')
        print(json.dumps({'close_requested': True, 'device_io': False})); return 0
    if not args.execute and not args.check_only:
        print(json.dumps({'device_io': False, 'browser_started': False, 'inputs_read': False,
            'plan': 'Verified v3 normal boot/CDC; first real PONG in the visible readonly WebSerial editor'})); return 0
    require(args.boot_run and args.boot_sha256, 'actual v11 boot observation path and exact hash required')
    prepared = prepare(args.boot_run, args.boot_sha256)
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'device_io': False, 'browser_started': False,
                          'evidence': prepared['evidence']})); return 0
    require(args.output is not None, 'new output directory required')
    result = run(prepared, args.output)
    print(json.dumps({key: result.get(key) for key in
        ('phase', 'error', 'serial_port_closed', 'browser_process_stopped', 'local_server_stopped')}))
    return 0 if result.get('connected_utc') and not result.get('error') else 1


if __name__ == '__main__': raise SystemExit(main())
