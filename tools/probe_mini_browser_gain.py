"""One real editor Output ArrowDown/ArrowUp trial; default is an offline plan.

Requires a separately qualified USB GAIN manifest and completed physical
first-preset proof. No serial/device enumeration occurs in Python. Execution
uses a new browser profile, localhost, and the frozen CDP/chooser helpers.
"""
from __future__ import annotations

import argparse
import copy
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
from tools import build_mini_app as app
from tools import probe_mini_app as readonly
from tools import probe_mini_app_mutation as mutation
from tools import probe_mini_browser_readonly as browser

require, sha = browser.require, browser.sha
GUARD = ROOT / 'tools/mini_browser_gain_guard.js'
OUTPUT_KNOB = '#gOut .knob[role="slider"]'
STATE = """(() => ({ready:window.__urOk===true,title:document.title,
 connected:typeof S!=='undefined'&&S.connected,fw:typeof S!=='undefined'?S.fw:null,
 gain:typeof S!=='undefined'?S.gain:null,profile:typeof HyperRigMini!=='undefined'?HyperRigMini.profile:null,
 initialReadsFinished:typeof lvlTimer!=='undefined'&&!!lvlTimer,
 gainPending:typeof ED!=='undefined'?ED.gainN:null,
 knob:(()=>{const k=document.querySelector('#gOut .knob[role="slider"]');return k?{
  value:k.getAttribute('aria-valuenow'),label:k.getAttribute('aria-label'),focused:document.activeElement===k}:null})(),
 guard:globalThis.__miniGainGuard?.state}))()"""


def reference(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'existing local evidence file required')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes())}


def validate_family_baseline(spec, profile, report, report_ref):
    """Additional narrow experiment constraints after the builder's raw replay."""
    require(spec.get('hardware_verified') is True and profile.get('hardware_verified') is True
            and profile['image_sha256'] == browser.IMAGE_SHA and profile['firmware_version'] == browser.VERSION,
            'physically qualified candidate image required')
    require(profile['capabilities']['read'] is True and profile['capabilities']['write'] is False
            and profile['capabilities']['panel'] is False
            and 'GAIN' in profile.get('family_capabilities', {}).get('usb-cdc', [])
            and not profile.get('family_capabilities', {}).get('ble-nus'),
            'USB GAIN family without blanket writes, panel or BLE grants required')
    require(report_ref in spec.get('family_validation', {}).get('usb-cdc', []),
            'first-preset proof must be one of the manifest-bound USB family reports')
    require(report.get('kind') == 'mini-app-first-preset-validation'
            and report.get('evidence_model') == 'representative-first-preset-v1'
            and report.get('hardware_executed') is True and report.get('transport') == 'usb-cdc'
            and report.get('image_sha256') == browser.IMAGE_SHA and report.get('firmware_version') == browser.VERSION
            and report.get('preset_intentionally_retained') is True and report.get('final_sound_verified') is True
            and report.get('physically_exercised_requests', {}).get('GAIN') and report.get('simulated_requests') == {},
            'completed physical first-preset GAIN roundtrip required')
    require(report.get('trial', {}).get('phase') == 'complete' and report['trial'].get('roundtrip_passed') is True,
            'first-preset trial must have completed')
    final = copy.deepcopy(report['trial']['final_state'])
    gain = final['extra']['gain_db']
    require(isinstance(gain, list) and len(gain) == 2 and all(type(v) is int and -30 <= v <= 12 for v in gain)
            and gain[1] > -30, 'actual restored output gain must be above -30 dB')
    require(final['plist']['ok'] is True and type(final['plist']['current']) is int
            and 0 <= final['plist']['current'] <= 31
            and any(p['slot'] == final['plist']['current'] for p in final['plist']['presets']),
            'actual retained current preset required')
    return {'gain': gain, 'fxs': final['fxs'], 'plist': final['plist'], 'snaps': final['snaps']}


def prepare(manifest, family_report, evidence_path, evidence_sha256, app_dir):
    manifest, family_report, app_dir = map(lambda p: Path(p).resolve(), (manifest, family_report, app_dir))
    spec = json.loads(app.local_evidence(reference(manifest), 'manifest'))
    # Includes full physical first-preset raw trace replay, not hand-set flags.
    profile = app.load_profile(manifest)
    family_ref = reference(family_report)
    report = json.loads(app.local_evidence(family_ref, 'first-preset report'))
    baseline = validate_family_baseline(spec, profile, report, family_ref)
    proof_ref = spec.get('hardware_validation')
    proof = json.loads(app.local_evidence(proof_ref, 'USB boot/read qualification'))
    require(proof.get('kind') == 'mini-app-usb-read-qualification' and proof.get('boot_USB_read_verified') is True
            and proof.get('image_sha256') == browser.IMAGE_SHA,
            'bound boot and USB read qualification required')
    for item in proof.get('evidence', {}).values():
        app.local_evidence(item, 'retained USB qualification input')
    require(set(proof.get('evidence', {})) == {'installation', 'held', 'released', 'read_log'},
            'complete installation/held/released/read evidence required')
    evidence = browser.load_evidence(evidence_path, evidence_sha256)
    require(evidence.get('qualification') == proof_ref, 'COM/PONG evidence must reference the same USB read qualification')
    trace = [json.loads(line) for line in app.local_evidence(report['trace'], 'first-preset trace').splitlines() if line]
    require(trace and trace[-1].get('event') == 'port_closed'
            and any(row.get('event') == 'first_preset_complete' for row in trace),
            'completed first-preset trial and closed CLI serial port required')
    require(app_dir.is_relative_to(ROOT) and app_dir.is_dir(), 'local generated editor required')
    source = app.checked(app.SOURCE / 'web/tankg.html', app.SOURCE_SHA).decode('utf-8')
    expected, _ = app.derive_html(source, profile)
    require((app_dir / 'tankmini.html').read_bytes() == expected.encode('utf-8'),
            'editor HTML must be the exact generated version for the qualified manifest')
    for name in ('mini-profile.js', 'mini-ui.js'):
        require((app_dir / name).read_bytes() == (ROOT / 'app/mini' / name).read_bytes(), 'editor support script differs: ' + name)
    require((app_dir / 'nam2chip.js').read_bytes() == app.rename_text(
        app.checked(app.SOURCE / 'web/nam2chip.js', app.CONVERTER_SHA).decode('utf-8')).encode('utf-8'),
        'editor converter differs')
    return {'profile': profile, 'baseline': baseline, 'evidence': evidence, 'app_directory': str(app_dir),
            'inputs': {'manifest': reference(manifest), 'family_report': family_ref,
                       'browser_evidence': reference(evidence_path)},
            'planned_mutations': [f'GAIN {baseline["gain"][0]} {baseline["gain"][1]-1}',
                                  f'GAIN {baseline["gain"][0]} {baseline["gain"][1]}']}


def parse_snapshot(responses):
    require(set(responses) == {'GAIN', 'LVL', 'FXS', 'PLIST', 'SNAPS'}, 'complete fresh query set required')
    for lines in responses.values():
        require(isinstance(lines, list) and lines and all(isinstance(x, str) and not x.startswith('ERR') for x in lines),
                'query response error or truncation')
    gain = re.fullmatch(r'GAIN in=(-?\d+) out=(-?\d+) dB', responses['GAIN'][0]) if len(responses['GAIN']) == 1 else None
    lvl = re.match(r'^LVL .*\bg=(-?\d+)/(-?\d+)(?: |$)', responses['LVL'][0]) if len(responses['LVL']) == 1 else None
    require(gain and lvl and gain.groups() == lvl.groups(), 'fresh GAIN and LVL must agree')
    values = list(map(int, gain.groups()))
    require(all(-30 <= v <= 12 for v in values), 'actual GAIN outside supported range')
    plist = readonly.parse_plist(responses['PLIST'])
    require(plist['ok'], 'coherent complete PLIST required')
    return {'gain': values, 'fxs': mutation.parse_fxs(responses['FXS']), 'plist': plist,
            'snaps': mutation.parse_snaps(responses['SNAPS'])}


def verify_snapshot(actual, baseline, expected_gain):
    require(actual['gain'] == expected_gain, 'actual GAIN differs from the planned UI step')
    for key in ('fxs', 'plist', 'snaps'):
        require(actual[key] == baseline[key], 'unrelated state changed during GAIN trial: ' + key)


def read_snapshot(cdp):
    # These are reads through the original app queue. Mutations never use this path.
    responses = cdp.evaluate("""(async()=>{
      const r={};
      r.GAIN=await Pedal.cmd('GAIN','GAIN',1500);
      r.LVL=await Pedal.cmd('LVL','LVL',1500);
      r.FXS=await Pedal.cmd('FXS',l=>/^FXS (?:peak|pico)=/.test(l)||/^ERR/.test(l),2500);
      r.PLIST=await Pedal.cmd('PLIST',l=>/^PLIST (?:end|fin)\\b/.test(l)||/^ERR/.test(l),4000);
      r.SNAPS=await Pedal.cmd('SNAPS','SNAPS',1500);
      return r;
    })()""")
    return {'responses': responses, 'state': parse_snapshot(responses)}


def wait_state(cdp, predicate, timeout, message):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = cdp.evaluate(STATE)
        require(not state.get('guard', {}).get('fatal'), state.get('guard', {}).get('fatal'))
        if predicate(state):
            return state
        time.sleep(.1)
    raise ValueError(message)


def ui_step(cdp, direction, timeout):
    require(direction in ('down', 'up'), 'one down or restore step only')
    cdp.evaluate('document.querySelector(' + json.dumps(OUTPUT_KNOB) + ').focus()')
    cdp.evaluate('__miniGainGuard.arm(' + json.dumps(direction) + ')')
    key, code = ('ArrowDown', 40) if direction == 'down' else ('ArrowUp', 38)
    for kind in ('keyDown', 'keyUp'):
        cdp.call('Input.dispatchKeyEvent', {'type': kind, 'key': key, 'code': key, 'windowsVirtualKeyCode': code})
    return wait_state(cdp, lambda s: s['guard']['phase'] == direction + '_ack' and not s['gainPending'],
                      timeout, 'UI GAIN acknowledgement missing; no retry or automatic restore')


def run(prepared, output, *, timeout=45):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'new output directory under build required')
    require(type(timeout) is int and 10 <= timeout <= 60, 'bounded timeout10..60seconds required')
    # Revalidate all input files before creating browser/chooser; no silent stale prepared plan.
    for item in prepared['inputs'].values(): app.local_evidence(item, 'prepared input')
    verified = prepare(ROOT / prepared['inputs']['manifest']['path'], ROOT / prepared['inputs']['family_report']['path'],
                       ROOT / prepared['inputs']['browser_evidence']['path'], prepared['inputs']['browser_evidence']['sha256'],
                       prepared['app_directory'])
    require(verified == prepared, 'prepared trial changed')
    app_dir, evidence, baseline = Path(prepared['app_directory']), prepared['evidence'], prepared['baseline']
    output.mkdir(parents=True); profile_dir = output / 'isolated-profile'; profile_dir.mkdir()
    report = {'schema': 1, 'kind': 'mini-browser-output-gain-trial', 'result': 'running',
              'started_utc': datetime.now(timezone.utc).isoformat(), 'hardware_executed': False,
              'transport': 'usb-cdc', 'inputs': prepared['inputs'], 'planned_mutations': prepared['planned_mutations'],
              'serial_port_closed': False, 'ui_roundtrip_verified': False, 'preset_save_sent': False,
              'audio_verified': False, 'BLE_verified': False, 'persistence_verified': False,
              'personal_profile_used': False, 'app_files_modified': False, 'automatic_retry': False,
              'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
                  [Path(__file__), GUARD, Path(browser.__file__), ROOT / 'tools/verify_mini_browser.py',
                   *(p for p in app_dir.iterdir() if p.is_file())]}}
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(browser.LocalHandler, directory=str(app_dir), live=True))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    process = cdp = None
    try:
        args = [str(browser.browser_path()), '--headless=new', '--no-first-run', '--no-default-browser-check',
                '--disable-background-networking', '--disable-component-update', '--disable-sync', '--disable-extensions',
                '--disable-features=MediaRouter,OptimizationHints', '--disable-default-apps', '--disable-breakpad',
                '--noerrdialogs', '--window-size=1440,1000', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
                '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
                '--user-data-dir=' + str(profile_dir), 'about:blank']
        with (output / 'browser-stderr.txt').open('wb') as stream:
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=stream,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        endpoint = profile_dir / 'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file(): break
            require(process.poll() is None, 'browser exited before CDP'); time.sleep(.1)
        require(endpoint.is_file(), 'CDP unavailable')
        origin = 'http://127.0.0.1:' + endpoint.read_text().splitlines()[0]
        get = lambda suffix: json.loads(urlopen(origin + suffix, timeout=5).read())
        report['browser'] = get('/json/version')
        require(any(d['domain'] == 'DeviceAccess' for d in get('/json/protocol')['domains']), 'DeviceAccess is required')
        page = next(p for p in get('/json/list') if p['type'] == 'page')
        cdp = browser.CDP(page['webSocketDebuggerUrl'])
        for domain in ('Runtime', 'Page', 'Log'): cdp.call(domain + '.enable')
        config = {'live': True, 'image_sha256': browser.IMAGE_SHA, 'pong': evidence['pong'], 'gain': baseline['gain']}
        cdp.call('Page.addScriptToEvaluateOnNewDocument', {'source': GUARD.read_text('utf-8') +
                 '\ninstallMiniBrowserGainGuard(' + json.dumps(config) + ');'})
        cdp.call('Page.navigate', {'url': f'http://127.0.0.1:{server.server_port}/tankmini.html?gain_ui_trial=1'})
        initial = wait_state(cdp, lambda s: s['ready'], 10, 'editor bootstrap failed')
        require(initial['title'] == 'HyperRig for TANK MINI' and initial['profile'] == prepared['profile'], 'editor profile differs')
        cdp.evaluate('__miniGainGuard.installApp(SerialTransport,Pedal,HyperRigMini.profile)')
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"): cdp.click('.ccall .tskip')
        cdp.call('DeviceAccess.enable'); cdp.evaluate('__miniGainGuard.allowRequest()'); cdp.click('#connBtn')
        deadline, handled, cursor = time.monotonic() + timeout, set(), 0
        while time.monotonic() < deadline:
            snapshot = cdp.evaluate(STATE)
            events, cursor = cdp.events[cursor:], len(cdp.events)
            for item in events:
                if item.get('method') != 'DeviceAccess.deviceRequestPrompted': continue
                prompt = item['params']
                if prompt['id'] in handled: continue
                report.setdefault('chooser_prompts', []).append(prompt)
                try: selection = browser.select_device(prompt, evidence['com'], allow_missing=True)
                except Exception:
                    cdp.call('DeviceAccess.cancelPrompt', {'id': prompt['id']}); raise
                if selection is None: continue
                require(not handled, 'a second serial chooser is prohibited')
                handled.add(prompt['id']); cdp.call('DeviceAccess.selectPrompt', selection)
            require(not snapshot['guard']['fatal'], snapshot['guard']['fatal'])
            if snapshot['connected'] and snapshot['initialReadsFinished']: break
            time.sleep(.1)
        require(snapshot['connected'] and snapshot['initialReadsFinished'] and snapshot['fw'] == evidence['pong']
                and snapshot['guard']['pongMatched'] and snapshot['guard']['opens'] == 1, 'exact USB handshake did not complete')
        report['hardware_executed'] = True
        report['before'] = read_snapshot(cdp)
        verify_snapshot(report['before']['state'], baseline, baseline['gain'])
        if not cdp.evaluate("document.getElementById('meters').classList.contains('open')"): cdp.click('#meters')
        report['before_screenshot'] = cdp.screenshot(output / 'before.png')
        report['down_ui'] = ui_step(cdp, 'down', timeout)
        report['down'] = read_snapshot(cdp)
        verify_snapshot(report['down']['state'], baseline, [baseline['gain'][0], baseline['gain'][1] - 1])
        report['down_screenshot'] = cdp.screenshot(output / 'down.png')
        report['restored_ui'] = ui_step(cdp, 'up', timeout)
        report['restored'] = read_snapshot(cdp)
        verify_snapshot(report['restored']['state'], baseline, baseline['gain'])
        cdp.evaluate('__miniGainGuard.finish()')
        report['restored_screenshot'] = cdp.screenshot(output / 'restored.png')
        report['ui_roundtrip_verified'] = True
        cdp.evaluate('connect()')  # Only the original disconnect path; no command injected here.
        latest = cdp.evaluate(STATE)
        require(cdp.evaluate('!S.connected && !SerialTransport.isOpen()') and latest['guard']['closes'] == 1
                and not latest['guard']['closeError'] and not latest['guard']['fatal'], 'native serial close did not complete')
        report['serial_port_closed'] = True
        report['javascript_exceptions'] = [e['params'] for e in cdp.events if e.get('method') == 'Runtime.exceptionThrown']
        require(not report['javascript_exceptions'], 'uncaught JavaScript error')
        report['result'] = 'pass'
    except Exception as error:
        report['result'], report['error'] = 'fail', repr(error)
    finally:
        if cdp:
            try:
                cdp.evaluate("(async()=>{__miniGainGuard.stop();if(typeof S!=='undefined'){S.connected=false;clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;Pedal.abort();if(SerialTransport.isOpen())await Pedal.disconnect();}})()")
                latest = cdp.evaluate(STATE); report['final'] = latest
                report['serial_port_open_attempted'] = latest['guard']['opens'] > 0
                report['hardware_executed'] = latest['guard']['opens'] > 0
                report['serial_port_opened'] = any(e['kind'] == 'serial_open_complete' for e in latest['guard']['events'])
                report['serial_port_closed'] = bool(cdp.evaluate('!SerialTransport.isOpen()') and latest['guard']['closes'] == 1
                                                    and not latest['guard']['closeError'])
                report['actual_mutations'] = [x for x in latest['guard']['wire'] if x['origin'] != 'query']
                if not report['serial_port_closed'] and latest['guard']['opens']:
                    report['result'] = 'fail'; report.setdefault('error', 'Native port close not proven')
            except Exception as error:
                report['page_cleanup_error'] = repr(error); report['result'] = 'fail'
            try: cdp.call('Browser.close')
            except Exception: pass
            cdp.ws.close()
        if process:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.terminate(); process.wait(timeout=5)
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        report['isolated_browser_stopped'] = process is None or process.poll() is not None
        report['local_server_stopped'] = True
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        with (output / 'report.json').open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(report, indent=2, ensure_ascii=False) + '\n'); stream.flush(); os.fsync(stream.fileno())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    for name in ('firmware-manifest', 'family-report', 'evidence', 'app-dir', 'output'): parser.add_argument('--' + name, type=Path)
    parser.add_argument('--evidence-sha256'); parser.add_argument('--timeout', type=int, default=45)
    args = parser.parse_args(argv)
    require(not (args.execute and args.check_only), 'choose execution or offline preflight')
    if not args.execute and not args.check_only:
        print(json.dumps({'device_io': False, 'browser_started': False, 'inputs_read': False,
            'plan': 'Qualified USB GAIN, fresh app GAIN/LVL/PLIST, Output ArrowDown, readback, ArrowUp, readback, native close',
            'persistent_commands': [], 'requires': 'Actual boot/read and physical first-preset GAIN evidence; separate qualified app'}))
        return 0
    require(all(getattr(args, name) is not None for name in ('firmware_manifest','family_report','evidence','evidence_sha256','app_dir')),
            'manifest, first-preset report, COM/PONG evidence+hash and matching generated app required')
    prepared = prepare(args.firmware_manifest, args.family_report, args.evidence, args.evidence_sha256, args.app_dir)
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'device_io': False, 'browser_started': False,
                          'inputs': prepared['inputs'], 'planned_mutations': prepared['planned_mutations']})); return 0
    require(args.output is not None, 'new output directory required for execution')
    report = run(prepared, args.output, timeout=args.timeout)
    print(json.dumps({key: report.get(key) for key in ('result','hardware_executed','ui_roundtrip_verified','serial_port_closed','error')}))
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__': raise SystemExit(main())
