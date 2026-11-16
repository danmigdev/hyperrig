"""One PING + one UBOOT through a new isolated WebSerial window. Offline default.

Requires the previous real desktop proof, its completed native-close report,
and a fresh exact-row UIAutomation selection record before the UBOOT intent.
Never calls a ROM transport or writes NOR; the caller verifies fresh ROM
arrival/INQUIRY independently after this session has stopped.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from functools import partial
import http.server
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
from tools import probe_mini_browser_readonly as browser
from tools import launch_mini_desktop_readonly as desktop
from tools import audit_mini_cdc_recovery as audit
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

PAGE = ROOT / 'tools/mini_rom_webserial'
require, sha = browser.require, browser.sha
FROZEN_DESKTOP = {
    'tools/launch_mini_desktop_readonly.py': 'ffe876c4ab1ac0f4ea051056369dc70f124d5ba0a3168dff71aea9bc5425f412',
    'tools/mini_desktop_readonly_guard.js': 'f192b65e1323458f6bc72f761047363337fa56ac4d297d3bb30554f87a569eff',
}


def now(): return datetime.now(timezone.utc).isoformat()


def local(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'evidence/output must stay inside workspace')
    return path


def stamp(text):
    value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    require(value.utcoffset() is not None, 'aware timestamp required')
    return value


def pinned(path, expected, *, parse_json=True):
    path = local(path); raw = read_shared_bytes(path)
    require(re.fullmatch(r'[0-9a-f]{64}', expected or '') and sha(raw) == expected,
            'evidence hash differs: '+str(path))
    return (json.loads(raw) if parse_json else raw), {'path': path.relative_to(ROOT).as_posix(), 'sha256': expected}


def validate_prior(proof, closed):
    state, guard = proof.get('state', {}), proof.get('guard', {})
    pong = state.get('fw')
    require(isinstance(pong, str) and re.fullmatch(
        r'PONG tankm_fw M5\.71 rel ble Nov 12 2026 16:04:11(?: safe)?', pong), 'prior exact MINI PONG required')
    require(state.get('connected') is True and state.get('demo') is False and state.get('initialReadsFinished') is True
            and guard.get('live') is True and guard.get('requests') == guard.get('opens') == 1
            and guard.get('pongMatched') is True and guard.get('observedPong') == pong and not guard.get('fatal')
            and guard.get('portInfo') == {'vid': 0x3654, 'pid': 0x5155}, 'actual one-port desktop connection required')
    require(pong in guard.get('replies', []), 'PONG missing from actual RX records')
    require(closed.get('kind') == 'mini-desktop-readonly-session' and closed.get('phase') == 'connected_readonly'
            and closed.get('finished_utc') and not closed.get('error') and closed.get('identity_verified') is True
            and closed.get('serial_port_closed') is True and closed.get('browser_process_stopped') is True
            and closed.get('local_server_stopped') is True, 'previous desktop must have finished and released native port')
    disconnect = closed.get('disconnect', {})
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes') == 1 and not disconnect.get('closeError'), 'actual native close proof required')
    latest = closed.get('last_guard', {})
    require(latest.get('closes') == 1 and latest.get('opens') == 1 and latest.get('observedPong') == pong
            and not latest.get('closeError') and latest.get('stopped') is True, 'final guard differs or was not stopped')
    inputs = closed.get('evidence', {}).get('inputs')
    require(isinstance(inputs, dict) and inputs == proof.get('inputs')
            and inputs.get('manifest', {}).get('sha256') == desktop.MANIFEST_SHA,
            'desktop proof/close not tied to installed v2 manifest')
    com = closed.get('evidence', {}).get('evidence', {}).get('com')
    require(re.fullmatch(r'COM[1-9][0-9]{0,3}', com or ''), 'exact prior COM required')
    require(stamp(closed['started_utc']) <= stamp(proof['observed_utc']) <= stamp(closed['finished_utc']),
            'proof/close chronology differs')
    return {'pong': pong, 'com': com}


def validate_selection(selection, *, browser_pid, origin, com, start, validated_at):
    require(selection.get('browser_pid') == browser_pid and selection.get('origin') == origin,
            'UIA selection belongs to another browser/origin')
    require(selection.get('selected_row') == f'Tank-M HyperRig ({com})'
            and selection.get('exact_unique_row_verified') is True
            and selection.get('no_other_device_selected') is True
            and selection.get('method') == 'Windows UIAutomation SelectionItem and Invoke',
            'exact unique COM row selection required')
    selected_at = stamp(selection.get('observed_utc', ''))
    require(stamp(start) <= selected_at <= stamp(validated_at), 'selection is stale or future-dated')
    return True


def prepare(proof_path, proof_sha, closed_path, closed_sha):
    proof_path, closed_path = local(proof_path), local(closed_path)
    require(proof_path.parent == closed_path.parent and proof_path.name == 'connected-proof.json'
            and closed_path.name == 'session.json', 'one desktop session directory required')
    proof, proof_ref = pinned(proof_path, proof_sha); closed, close_ref = pinned(closed_path, closed_sha)
    identity = validate_prior(proof, closed)
    for name, expected in FROZEN_DESKTOP.items():
        require(closed.get('source_sha256', {}).get(name) == expected and sha((ROOT/name).read_bytes()) == expected,
                'desktop executed source changed: '+name)
    for name, expected in closed.get('source_sha256', {}).items():
        require(sha(read_shared_bytes(local(ROOT/name))) == expected, 'desktop dependency changed: '+name)
    for ref in proof['inputs'].values(): pinned(ROOT/ref['path'], ref['sha256'], parse_json=False)
    static = audit.inspect()
    return {'schema': 1, **identity, 'installed_image_sha256': static['installed_candidate_sha256'],
            'inputs': {'desktop_connection': proof_ref, 'desktop_closed': close_ref},
            'command': 'UBOOT', 'command_hex': '55424f4f540a', 'max_PING': 1, 'max_UBOOT': 1,
            'automatic_retry': False, 'firmware_write': False, 'ROM_verified': False,
            'safe_mode_dispatch_supported_statically': static['safe_flag_not_read_on_audited_UBOOT_dispatch_path']}


def apply_observation(report, state):
    """Only project actual browser state; neither ACK nor detach proves ROM."""
    commands = [row for row in state.get('tx', []) if row.get('line') == 'UBOOT\n']
    require(len(commands) <= 1, 'duplicate UBOOT observation')
    if commands:
        require(commands[0].get('hex') == '55424f4f540a' and state.get('ubootAttempted') is True,
                'command observation differs from exact native TX intent')
        stamp(commands[0]['utc'])
        report['command_submitted_utc'] = commands[0]['utc']
    report['browser_state'] = state
    report['command_submitted_once'] = state.get('ubootAttempted') is True
    report['command_write_completed'] = state.get('ubootWriteCompleted') is True
    report['ack_observed'] = state.get('actualACKObserved') is True
    report['native_disconnect_observed'] = state.get('disconnectObserved') is True
    report['native_close_verified'] = state.get('nativeCloseVerified') is True
    report['serial_port_closed'] = report['native_close_verified']
    report['ROM_verified'] = False


def run(prepared, output):
    refs = prepared['inputs']
    fresh = prepare(ROOT/refs['desktop_connection']['path'], refs['desktop_connection']['sha256'],
                    ROOT/refs['desktop_closed']['path'], refs['desktop_closed']['sha256'])
    require(fresh == prepared, 'prepared evidence changed')
    output = local(output)
    require(output.is_relative_to(ROOT/'build') and not output.exists(), 'new build output directory required')
    output.mkdir(); profile = output/'isolated-profile'; profile.mkdir()
    report = {'schema': 1, 'kind': 'mini-webserial-enter-ROM', 'started_utc': now(), 'phase': 'prepare',
              'evidence': prepared, 'command': 'UBOOT', 'prior_port': prepared['com'], 'pong': None,
              'command_submitted_once': False, 'command_submitted_utc': None, 'command_invocations': 0,
              'serial_port_closed': False, 'native_close_verified': False, 'ack_observed': False,
              'automatic_retry': False, 'firmware_write': False, 'ROM_verified': False,
              'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
                  [Path(__file__), PAGE/'guard.js', PAGE/'index.html', Path(audit.__file__),
                   Path(browser.__file__), Path(desktop.__file__), ROOT/'tools/verify_mini_browser.py',
                   ROOT/'tools/mini_host_journal.py']}}
    save = lambda: atomic_write_json(output/'recovery.json', report)
    selection_path = output/'selection.json'
    report['selection_path'] = selection_path.relative_to(ROOT).as_posix(); save()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(browser.LocalHandler, directory=str(PAGE), live=True))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    process = cdp = None
    try:
        with (output/'browser-stderr.txt').open('wb') as stream:
            process = subprocess.Popen(desktop.browser_arguments(browser.browser_path(), profile),
                                       stdout=subprocess.DEVNULL, stderr=stream,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        report['browser_process_id'] = process.pid; save()
        endpoint = profile/'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file(): break
            require(process.poll() is None, 'browser exited'); time.sleep(.1)
        require(endpoint.is_file(), 'CDP endpoint missing')
        devtools = 'http://127.0.0.1:'+endpoint.read_text().splitlines()[0]
        get = lambda suffix: json.loads(urlopen(devtools+suffix, timeout=5).read())
        report['CDP_http'] = devtools; report['browser'] = get('/json/version')
        page = next(p for p in get('/json/list') if p['type'] == 'page')
        cdp = browser.CDP(page['webSocketDebuggerUrl']); report['CDP_page_websocket'] = page['webSocketDebuggerUrl']
        for domain in ('Runtime', 'Page', 'Log'): cdp.call(domain+'.enable')
        config = {'execute': True, 'com': prepared['com'], 'pong': prepared['pong']}
        cdp.call('Page.addScriptToEvaluateOnNewDocument', {'source': 'globalThis.__miniRomConfig='+json.dumps(config)+';'})
        origin = f'http://127.0.0.1:{server.server_port}'; report['origin'] = origin
        cdp.call('Page.navigate', {'url': origin+'/index.html'})
        for _ in range(100):
            if cdp.evaluate('!!globalThis.miniRomSession'): break
            time.sleep(.05)
        require(cdp.evaluate('!!globalThis.miniRomSession'), 'isolated recovery page did not load')
        report['phase'] = 'awaiting_exact_UIA_selection'; save()
        cdp.click('#connect'); deadline = time.monotonic()+120; opened_at = None
        while time.monotonic() < deadline:
            state = cdp.evaluate('miniRomSession.state'); apply_observation(report, state)
            require(not state['error'], state['error'])
            if state['opens'] and opened_at is None: opened_at = time.monotonic()
            if state['identityVerified'] and state['pingWriteCompleted']:
                require(prepared['pong'] in state['lines'], 'matched PONG absent from actual RX log')
                report['pong'] = next(line for line in state['lines'] if line == prepared['pong'])
                report.setdefault('fresh_PONG_observed_utc', now())
                report['phase'] = 'awaiting_selection_record'; save()
                if selection_path.is_file():
                    selection_raw = read_shared_bytes(selection_path)
                    selection = json.loads(selection_raw)
                    validate_selection(selection, browser_pid=process.pid, origin=origin, com=prepared['com'],
                                       start=report['started_utc'], validated_at=now())
                    report['selection'] = selection; report['selection_sha256'] = sha(selection_raw); break
            require(opened_at is None or state['identityVerified'] or time.monotonic()-opened_at < 15,
                    'one WebSerial PING produced no exact PONG; no command sent')
            time.sleep(.1)
        else: raise ValueError('chooser/PONG/selection deadline; no UBOOT sent')
        # Publication/fsync must succeed BEFORE the sole browser command invocation.
        report['phase'] = 'UBOOT_intent'; report['command_invocations'] = 1
        report['command_intent_utc'] = now(); save()
        try: cdp.evaluate('miniRomSession.enterROM().then(()=>true)')
        except Exception as error: report['command_call_error'] = repr(error)
        deadline = time.monotonic()+8
        while time.monotonic() < deadline:
            state = cdp.evaluate('miniRomSession.state'); apply_observation(report, state); save()
            if state.get('disconnectObserved') or state.get('readError'):
                break
            time.sleep(.1)
        report['phase'] = 'UBOOT_attempted_ROM_unverified' if report['command_submitted_once'] else 'command_submission_unverified'
        save()
    except Exception as error:
        report['error'] = repr(error); report['error_phase'] = report['phase']; report['phase'] = 'stopped_on_error'
        try: save()
        except Exception as publication_error: report['publication_error'] = repr(publication_error)
    finally:
        if cdp:
            try: apply_observation(report, cdp.evaluate('miniRomSession.close()'))
            except Exception as error: report['cleanup_observation_error'] = repr(error)
            try: cdp.call('Browser.close')
            except Exception: pass
            cdp.ws.close()
        if process:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.terminate(); process.wait(timeout=5)
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        report['browser_process_stopped'] = process is None or process.poll() is not None
        report['local_server_stopped'] = True; report['finished_utc'] = now(); save()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(); mode.add_argument('--check-only', action='store_true'); mode.add_argument('--execute', action='store_true')
    parser.add_argument('--connected-proof', type=Path); parser.add_argument('--proof-sha256')
    parser.add_argument('--closed-session', type=Path); parser.add_argument('--closed-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if not args.check_only and not args.execute:
        print(json.dumps({'device_io': False, 'browser_started': False, 'inputs_read': False,
                          'planned_commands': ['PING', 'UBOOT'], 'command_retry': False,
                          'required': ['closed real desktop proof', 'exact fresh UIA row', 'fresh exact PONG',
                                       'independent ROM arrival and INQUIRY afterward']})); return 0
    require(args.connected_proof and args.proof_sha256 and args.closed_session and args.closed_sha256,
            'explicit evidence files and hashes required')
    prepared = prepare(args.connected_proof, args.proof_sha256, args.closed_session, args.closed_sha256)
    if args.check_only: print(json.dumps({'device_io': False, 'prepared': prepared}, indent=2)); return 0
    require(args.output, 'new output directory required')
    result = run(prepared, args.output); print(json.dumps(result, indent=2))
    return 1 if result.get('error') or not result['command_submitted_once'] else 0


if __name__ == '__main__': raise SystemExit(main())
