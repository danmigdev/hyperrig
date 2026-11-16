"""Opt-in v3 original-editor GAIN/save/reload trial; default is offline.

An exact diagnostic CSAVE/CREAD preamble persists/verifies the embedded A2.
The subsequent mutations originate only in the original editor controls.
No frozen profile is changed, no general write capability is granted, and no
failed command is retried. A created capture/preset intentionally remains.
"""
from __future__ import annotations

import argparse
import copy
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
from tools import validate_mini_webserial_v3 as evidence
from tools import launch_mini_desktop_v3 as desktop
from tools import probe_mini_browser_readonly as browser
from tools import probe_mini_app as readonly
from tools import probe_mini_app_mutation as mutation
from tools import mini_capture_persistence as capture
from tools import enter_mini_rom_webserial as selection
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

require, sha, now = browser.require, browser.sha, desktop.now
GUARD = ROOT/'tools/mini_browser_first_preset_guard.js'
BLOB = ROOT/'analysis/firmware/m571_g_app/embedded-0.a2l'
VALIDATOR_SHA = '4d01fe626e0d55a02e34a7fbe5b80d192caea57e8e53a2a27ec13a24c7a280c1'
CAPTURE_SHA = '6c248c90dfcddda96dcdff6a531bd026168e468aa81372b5621b040e7980416a'
OUTPUT_KNOB = '#gOut .knob[role="slider"]'
READS = ('GAIN', 'LVL', 'FXS', 'PLIST', 'SNAPS', 'CLIST', 'ILIST', 'MODEL', 'CLKSTATE',
         'AMPEQ', 'BPM', 'PCOLOR', 'STW', 'SNAPNAME')
STATE = """(()=>({ready:window.__urOk===true,title:document.title,
  demo:typeof DEMO!=='undefined'&&DEMO,connected:typeof S!=='undefined'&&S.connected,
  fw:typeof S!=='undefined'?S.fw:null,profile:typeof HyperRigMini!=='undefined'?HyperRigMini.profile:null,
  initialReadsFinished:typeof lvlTimer!=='undefined'&&!!lvlTimer,
  gainPending:typeof ED!=='undefined'&&ED.gainN||0,
  guard:window.__miniFirstPresetGuard?.state}))()"""


def reference(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'input must remain inside workspace')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(read_shared_bytes(path))}


def integer_field(line, key):
    values = re.findall(r'(?:^| )'+re.escape(key)+r'=(-?\d+)(?= |$)', line)
    require(len(values) == 1, 'missing/ambiguous field '+key)
    return int(values[0])


def parse_snapshot(answers):
    require(isinstance(answers, dict) and set(answers) == set(READS), 'exact complete snapshot required')
    for key, lines in answers.items():
        require(isinstance(lines, list) and lines and all(isinstance(x, str) and not x.startswith('ERR') for x in lines),
                'successful complete response required: '+key)
    gain_line = answers['GAIN']
    match = re.fullmatch(r'GAIN in=(-?\d+) out=(-?\d+) dB', gain_line[0]) if len(gain_line) == 1 else None
    require(match is not None, 'bounded GAIN query required')
    gains = [int(match[1]), int(match[2])]
    require(all(-30 <= x <= 12 for x in gains), 'GAIN outside original UI range')
    require(len(answers['LVL']) == len(answers['CLKSTATE']) == 1, 'single LVL/CLKSTATE required')
    lvl, clock = answers['LVL'][0], answers['CLKSTATE'][0]
    lm = re.findall(r'(?:^| )g=(-?\d+)/(-?\d+)(?= |$)', lvl)
    require(len(lm) == 1 and list(map(int, lm[0])) == gains, 'fresh LVL and GAIN disagree')
    plist = readonly.parse_plist(answers['PLIST'])
    require(plist['ok'] and all(x.startswith(('PRE ', 'PLIST ')) for x in answers['PLIST']), 'strict complete PLIST required')
    clist = capture.parse_clist(answers['CLIST'])
    ir_end = re.fullmatch(r'ILIST end current=(-?\d+) slots=(\d+)', answers['ILIST'][-1])
    require(ir_end is not None and 1 <= int(ir_end[2]) <= 32, 'complete bounded ILIST required')
    ir_slots = []
    for line in answers['ILIST'][:-1]:
        item = re.fullmatch(r"IRS (\d+) (\d+) '[^']{0,23}'(?: fs=\d+)?", line)
        require(item is not None and int(item[1]) < int(ir_end[2]), 'malformed IR inventory')
        ir_slots.append(int(item[1]))
    require(ir_slots == sorted(set(ir_slots)), 'duplicate/unsorted IR inventory')
    ir_current = int(ir_end[1])
    require(ir_current == -1 or ir_current in ir_slots, 'current IR absent from inventory')
    engines = [x for x in answers['FXS'] if x.startswith('FXS eng=')]
    require(len(engines) == 1, 'one engine diagnostic response required')
    engine = re.fullmatch(r'FXS eng=(\d+) posts=(\d+) takes=(\d+) canc=(\d+) lat=(\d+)/(\d+) run=(\d+)', engines[0])
    require(engine is not None, 'engine diagnostic grammar differs')
    extra = mutation.parse_extra({key: {'lines': answers[key]} for key in mutation.EXTRA_READS})
    require(extra['color_preset'] == plist['current'], 'PCOLOR/PLIST current differs')
    return {'gain': gains, 'fxs': mutation.parse_fxs(answers['FXS']), 'plist': plist,
        'preset_rows': [line for line in answers['PLIST'] if line.startswith('PRE ')],
        'snaps': mutation.parse_snaps(answers['SNAPS']), 'clist': clist, 'ilist': list(answers['ILIST']),
        'ir_current': ir_current, 'model': list(answers['MODEL']), 'extra': extra,
        'runtime': {'safe': integer_field(clock, 'safe'), 'mode': integer_field(lvl, 'm'),
            'input_clips': integer_field(lvl, 'ci'), 'output_clips': integer_field(lvl, 'co'),
            'engine': dict(zip(('eng', 'posts', 'takes', 'canc', 'lat', 'lat_max', 'run'), map(int, engine.groups())))}}


def runtime_gate(snapshot):
    runtime = snapshot['runtime']
    require(runtime['safe'] == 0 and runtime['mode'] == 2, 'normal running mode2/safe0 required before any mutation')
    require(snapshot['fxs']['amp'] == {'present': 1, 'on': 1}, 'enabled original A2 engine required')
    require(snapshot['model'] == [capture.MODEL_LINE], 'unchanged default A2 model required')
    # Clips may correctly be zero. These diagnostics are not acoustic evidence.
    require(all(runtime[key] >= 0 for key in ('input_clips', 'output_clips')), 'invalid clip counters')


def first_preset_gate(snapshot):
    runtime_gate(snapshot)
    require(snapshot['plist']['current'] == -1, 'first-preset trial requires actual PLIST current=-1')
    require(snapshot['snaps'] == {'present': '0000', 'current': -1}, 'no preexisting RAM scenes allowed in this trial')
    require(snapshot['gain'][1] > -30, 'output cannot be decreased at its minimum')
    require(snapshot['ir_current'] == -1 and not any(b['type'] == 'ir' for b in snapshot['fxs']['blocks']),
            'this first-A2 trial does not qualify external IR dependencies')
    require(len(snapshot['plist']['presets']) < 32, 'no free preset slot')


def verify_processing_progress(first, second):
    """Audited producer/worker counters, not clips or instantaneous duration."""
    first_preset_gate(first); first_preset_gate(second)
    verify_state(second, first, gains=first['gain'], stage='live')
    before, after = first['runtime']['engine'], second['runtime']['engine']
    require(all(0 <= before[k] < after[k] <= 0xffffffff for k in ('posts', 'takes')),
            'audited core1 post/take counters did not advance; no mutation authorized')
    return {'before':before, 'after':after, 'core1_job_progress_observed':True,
            'clip_counters_used_as_samples':False, 'run_duration_used_as_counter':False,
            'physical_audio_output_verified':False}


def make_plan(snapshot, name):
    first_preset_gate(snapshot)
    slot = next(n for n in range(32) if n not in {p['slot'] for p in snapshot['plist']['presets']})
    require(re.fullmatch(r'[A-Za-z0-9 _.-]{1,23}', name or '') is not None, 'original UI name is not a bounded ASCII name')
    require(snapshot['clist']['current'] >= 0, 'capture must be byte-verified and persistent before UI trial')
    original = list(snapshot['gain']); down = [original[0], original[1]-1]
    return {'slot': slot, 'name': name, 'gain': original, 'down': down,
            'capture_slot': snapshot['clist']['current'], 'ir_slot': snapshot['ir_current'],
            'blocks': len(snapshot['fxs']['blocks']), 'save_request': f'PSAVE {slot} {name}',
            'load_request': f'PLOAD {slot}'}


def verify_state(actual, before, *, gains, stage, plan=None):
    runtime_gate(actual)
    require(actual['gain'] == gains, 'actual gain does not match UI step')
    require(mutation.logical_fxs(actual['fxs']) == mutation.logical_fxs(before['fxs']), 'unrelated FX state changed')
    for key in ('clist', 'ilist', 'ir_current', 'model'):
        require(actual[key] == before[key], 'unrelated state changed: '+key)
    a, b = copy.deepcopy(actual['extra']), copy.deepcopy(before['extra'])
    a['gain_db'] = b['gain_db']
    if stage in ('saved', 'reloaded'):
        require(plan is not None, 'saved state needs exact plan')
        require(actual['plist']['current'] == plan['slot'] and actual['snaps'] == {'present':'1000', 'current':0},
                'new preset/scene A not selected')
        retained = [x for x in actual['plist']['presets'] if x['slot'] != plan['slot']]
        require(retained == before['plist']['presets'], 'preexisting preset inventory changed')
        retained_rows = [line for line in actual['preset_rows'] if int(line.split()[1]) != plan['slot']]
        require(retained_rows == before['preset_rows'], 'preexisting preset references/metadata changed')
        new = [x for x in actual['plist']['presets'] if x['slot'] == plan['slot']]
        require(len(new) == 1 and new[0]['name'] == plan['name'] and new[0]['blocks'] == plan['blocks']
                and new[0]['snapshots'] == 1 and new[0]['amp'] == 1, 'new preset metadata differs')
        new_rows = [line for line in actual['preset_rows'] if int(line.split()[1]) == plan['slot']]
        prefix = f"PRE {plan['slot']} {plan['blocks']} {plan['capture_slot']} {plan['ir_slot']} '{plan['name']}'"
        require(len(new_rows) == 1 and new_rows[0].startswith(prefix+' '), 'new PRE capture/IR references differ')
        require(a['color_preset'] == plan['slot'], 'saved preset color association differs')
        a['color_preset'] = b['color_preset']
    else:
        require(actual['plist'] == before['plist'] and actual['preset_rows'] == before['preset_rows']
                and actual['snaps'] == before['snaps'], 'preset/scene changed during live gain')
    require(a == b, 'tone/tempo/color/stereo/model/scene names changed unexpectedly')


def prepare(*, boot, connected, session):
    require(sha(Path(evidence.__file__).read_bytes()) == VALIDATOR_SHA, 'frozen v3 evidence validator changed')
    require(sha(Path(capture.__file__).read_bytes()) == CAPTURE_SHA, 'frozen A2 persistence verifier changed')
    context = evidence.validate_v3_browser_evidence(boot=boot, connected=connected, session=session)
    require(not re.search(r'\bsafe\b', context['pong']), 'safe-mode PONG cannot authorize this trial')
    require(context['runtime']['clock']['safe'] == 0 and context['runtime']['lvl']['mode'] == 2,
            'prior real v3 normal-mode observations required; fresh observations will be required again')
    require(context['runtime']['plist']['current'] == -1, 'historical first-preset context required')
    blob = read_shared_bytes(BLOB); capture.validate_blob(blob)
    return {'schema': 1, 'kind': 'mini-browser-first-preset-v3-plan', 'context': context,
            'inputs': {'boot': boot, 'connected': connected, 'session': session}, 'blob': reference(BLOB),
            'app_directory': desktop.APP.relative_to(ROOT).as_posix(), 'profile': context['profile'],
            'automatic_retry': False, 'firmware_write': False, 'profile_modified': False,
            'general_capabilities_granted': {}, 'capture_save_max': 1, 'UI_mutations_max': 6}


def query(cdp, command):
    # Only the diagnostic preamble and reads use this method. UI mutations do not.
    verb = command.split()[0]
    if command in ('FXS', 'PLIST', 'CLIST', 'ILIST', 'SNAPNAME'):
        expression = {'FXS': r'/^FXS (?:peak|pico)=/.test(l)||/^ERR/.test(l)',
                      'PLIST': r'/^PLIST (?:end|fin)\b/.test(l)||/^ERR/.test(l)',
                      'CLIST': r'/^CLIST end\b/.test(l)||/^ERR/.test(l)',
                      'ILIST': r'/^ILIST end\b/.test(l)||/^ERR/.test(l)',
                      'SNAPNAME': r'/^SNAPNAME end$/.test(l)||/^ERR/.test(l)'}[command]
        until = '(l)=>'+expression
    else:
        until = json.dumps(verb)
    timeout = 8000 if verb == 'CSAVE' else 4000
    return cdp.evaluate('Pedal.cmd('+json.dumps(command)+','+until+','+str(timeout)+')')


def snapshot(cdp):
    answers = {name: query(cdp, name) for name in READS}
    return {'responses': answers, 'state': parse_snapshot(answers)}


def wait_state(cdp, predicate, timeout, message):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        value = cdp.evaluate(STATE)
        require(not value.get('guard', {}).get('fatal'), value.get('guard', {}).get('fatal'))
        if predicate(value): return value
        time.sleep(.1)
    raise ValueError(message)


def ui_key(cdp, action, target, timeout=15):
    require(action in ('down1', 'up', 'marker', 'reload'), 'unknown bounded key action')
    cdp.evaluate('document.querySelector('+json.dumps(target)+').focus()')
    cdp.evaluate('__miniFirstPresetGuard.arm('+json.dumps(action)+')')
    key, code = ('Enter', 13) if action == 'reload' else ('ArrowUp', 38) if action == 'up' else ('ArrowDown', 40)
    for kind in ('keyDown', 'keyUp'):
        cdp.call('Input.dispatchKeyEvent', {'type':kind, 'key':key, 'code':key, 'windowsVirtualKeyCode':code})
    return wait_state(cdp, lambda v:v['guard']['phase'] == action+'_ack' and not v['gainPending'],
                      timeout, 'UI command ACK absent; no retry or automatic restoration')


def close_serial(cdp):
    result = cdp.evaluate("""(async()=>{
      __miniFirstPresetGuard.stop();
      if(typeof S!=='undefined'&&S.connected)await connect();
      else if(typeof SerialTransport!=='undefined'&&SerialTransport.isOpen()){
        clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;Pedal.abort();await Pedal.disconnect();}
      return {open:SerialTransport.isOpen(),closes:__miniFirstPresetGuard.state.closes,
        closeError:__miniFirstPresetGuard.state.closeError};})()""")
    return {**result, 'native_close_verified':not result['open'] and result['closes']==1 and not result['closeError']}


def verify_wire(guard):
    """Check retained native RX against completed commands; no fabricated ACKs."""
    require(guard.get('fatal') is None and guard.get('phase') == 'complete' and guard.get('mutations') == 6,
            'completed unpoisoned six-command UI trial required')
    require(guard.get('requests') == guard.get('opens') == guard.get('closes') == 1 and not guard.get('closeError')
            and guard.get('stopped') is True,
            'one native connection and observed close required')
    wire, commands, rx = guard['wire'], guard['commands'], guard['rx']
    require(wire and rx and len(wire) <= 2000, 'bounded actual raw trace required')
    trials = [e['plan'] for e in guard['events'] if e.get('kind') == 'trial_plan']
    captures = [e['plan'] for e in guard['events'] if e.get('kind') == 'capture_plan']
    require(len(trials) == len(captures) == 1 and guard.get('captureVerified') is True, 'one capture and UI plan required')
    plan, cp = trials[0], captures[0]
    gain = lambda values:'GAIN '+' '.join(map(str,values))
    expected = [gain(plan['down']),gain(plan['gain']),plan['save_request'],'SNAPSAVE 0',gain(plan['down']),plan['load_request']]
    origins = ['Output ArrowDown','Output ArrowUp','Original empty-row Save','Original sceneAOnSave',
               'Output persistence marker ArrowDown','Original preset-row Enter']
    ui_wire = [x for x in wire if x['origin'] not in ('query','diagnostic capture persistence','diagnostic capture byte read')]
    require([(x['line'],x['origin']) for x in ui_wire] == list(zip(expected,origins)), 'actual UI command order/count differs')
    diagnostic = [x['line'] for x in wire if x['origin'].startswith('diagnostic capture ')]
    require(diagnostic == cp['requests'] and guard['captureMutations'] == sum(x.startswith('CSAVE ') for x in diagnostic),
            'diagnostic capture order/count differs')
    require([x['kind'] for x in guard['ui']] == ['keydown','keydown','click','keydown','keydown']
            and all(x.get('trusted') is True for x in guard['ui'])
            and [x.get('key') for x in guard['ui']] == ['ArrowDown','ArrowUp',None,'ArrowDown','Enter'],
            'actual trusted UI event sequence differs')
    acknowledgements = [e for e in guard['events'] if e.get('kind') == 'mutation_ack']
    require([e['line'] for e in acknowledgements] == expected, 'actual mutation ACK sequence differs')
    for index, item in enumerate(ui_wire):
        ui = guard['ui'][[0,1,2,2,3,4][index]]
        require(ui['seq'] < item['seq'] < acknowledgements[index]['seq']
                and (index == 0 or acknowledgements[index-1]['seq'] < item['seq']), 'UI/write/ACK chronology differs')
    for item in wire:
        if item['origin'] == 'query':
            require(evidence.is_query(item['line']), 'unqualified mutation disguised as a query')
        require(item['hex'] == (item['line']+'\n').encode('ascii').hex() and item['completed'] is True,
                'wire bytes differ or write did not complete')
        matches = [c for c in commands if c['id'] == item['command_id'] and c.get('wire_id') == item['id']]
        require(len(matches) == 1 and matches[0]['completed'] is True and matches[0]['line'] == item['line'],
                'actual original command completion missing')
        cmd = matches[0]
        if item in ui_wire:
            ack = acknowledgements[ui_wire.index(item)]
            require(cmd['lines'] == ack['lines'] and cmd['seq'] < ack['seq'], 'guard ACK differs from actual command response')
        raw = b''.join(bytes.fromhex(r['hex']) for r in rx if item['seq'] < r['seq'] < cmd['seq'])
        rx_lines = raw.decode('utf-8', errors='strict').replace('\r\n','\n').splitlines()
        cursor = 0
        for line in cmd['lines']:
            try: cursor = rx_lines.index(line, cursor)+1
            except ValueError: raise ValueError('completed response is absent from native RX: '+item['line']) from None
    return {'raw_RX_byte_count':sum(len(bytes.fromhex(r['hex'])) for r in rx), 'wire_command_count':len(wire),
            'completed_commands_checked_against_native_RX':True}


def complete_proof(report, guard, disconnect):
    """Promote only a finished UI sequence, observed native close and raw trace."""
    report.update(result='fail',ui_roundtrip_verified=False,save_reload_verified=False)
    require(report.get('UI_sequence_completed') is True and not report.get('error'), 'completed UI observations required')
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes') == 1 and not disconnect.get('closeError'), 'actual native close required')
    report['raw_trace_verification']=verify_wire(guard)
    report.update(result='pass',ui_roundtrip_verified=True,save_reload_verified=True)


def serial_observation(report, guard):
    opened = any(e.get('kind') == 'serial_open_complete' for e in guard.get('events', []))
    unknown = not opened and guard.get('opens') != 0
    report.update(hardware_executed=None if unknown else opened, execution_status_unknown=unknown)


def run(prepared, output):
    require(prepare(**prepared['inputs']) == prepared, 'prepared evidence changed')
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'build') and not output.exists(), 'new build directory required')
    output.mkdir(parents=True); profile_dir = output/'isolated-profile'; profile_dir.mkdir()
    report = {'schema':1, 'kind':'mini-browser-first-preset-v3-trial', 'result':'running', 'phase':'prepare',
        'started_utc':now(), 'prepared':prepared, 'image_sha256':desktop.IMAGE_SHA, 'transport':'usb-cdc',
        'hardware_executed':False, 'execution_status_unknown':False,
        'serial_port_closed':False, 'ui_roundtrip_verified':False,
        'save_reload_verified':False, 'audio_quality_verified':False, 'power_cycle_verified':False,
        'held_recovery_verified':False, 'BLE_verified':False, 'firmware_write':False,
        'automatic_retry':False, 'profile_modified':False, 'general_capabilities_granted':{},
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
            [Path(__file__), GUARD, Path(evidence.__file__), Path(capture.__file__), Path(selection.__file__),
             Path(readonly.__file__), Path(mutation.__file__),
             Path(browser.__file__), ROOT/'tools/verify_mini_browser.py', Path(desktop.__file__),
             ROOT/'tools/mini_host_journal.py', *(p for p in desktop.APP.iterdir() if p.is_file())]}}
    save = lambda:atomic_write_json(output/'report.json', report)
    save()
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0), partial(browser.LocalHandler, directory=str(desktop.APP), live=True))
    thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    process = cdp = None
    try:
        with (output/'browser-stderr.txt').open('wb') as stream:
            process = subprocess.Popen(desktop.browser_arguments(browser.browser_path(),profile_dir),
                stdout=subprocess.DEVNULL,stderr=stream,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        report['browser_process_id'] = process.pid; save()
        endpoint = profile_dir/'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file():break
            require(process.poll() is None,'browser exited before CDP');time.sleep(.1)
        require(endpoint.is_file(),'CDP unavailable')
        devtools = 'http://127.0.0.1:'+endpoint.read_text().splitlines()[0]
        get = lambda suffix:json.loads(urlopen(devtools+suffix,timeout=5).read())
        page = next(p for p in get('/json/list') if p['type']=='page'); cdp = browser.CDP(page['webSocketDebuggerUrl'])
        report['browser'] = get('/json/version'); report['CDP_http'] = devtools
        for domain in ('Runtime','Page','Log'):cdp.call(domain+'.enable')
        config = {'live':True,'image_sha256':desktop.IMAGE_SHA,'pong':prepared['context']['pong']}
        cdp.call('Page.addScriptToEvaluateOnNewDocument',{'source':GUARD.read_text('utf-8')+
            '\ninstallMiniBrowserFirstPresetGuard('+json.dumps(config)+');'})
        origin = f'http://127.0.0.1:{server.server_port}'
        report['origin'] = origin; report['selection_path'] = (output/'selection.json').relative_to(ROOT).as_posix()
        cdp.call('Page.navigate',{'url':origin+'/tankmini.html?first_preset_trial=1'})
        initial = wait_state(cdp,lambda v:v['ready'],10,'original editor bootstrap failed')
        require(initial['profile'] == prepared['profile'] and not initial['demo'],'base profile or real-editor mode differs')
        cdp.evaluate('__miniFirstPresetGuard.installApp(SerialTransport,Pedal,HyperRigMini.profile)')
        cdp.evaluate("document.getElementById('miniPortStatus').textContent='Prova USB limitata: A2, volume e primo preset. Profilo di base invariato.'")
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"):cdp.click('.ccall .tskip')
        # Once the chooser/open path is invoked, loss of CDP cannot prove that
        # no serial port opened. Only a later native guard observation resolves it.
        report.update(phase='awaiting_exact_UIA_selection',hardware_executed=None,execution_status_unknown=True)
        save()
        cdp.evaluate('__miniFirstPresetGuard.allowRequest()');cdp.click('#connBtn')
        state = wait_state(cdp,lambda v:v['connected'] and v['initialReadsFinished'],120,'real WebSerial bootstrap failed')
        require(state['fw']==prepared['context']['pong'] and state['guard']['pongMatched'],'actual exact PONG differs')
        chosen = json.loads(read_shared_bytes(output/'selection.json'))
        selection.validate_selection(chosen,browser_pid=process.pid,origin=origin,com=prepared['context']['com'],
            start=report['started_utc'],validated_at=now())
        report['selection'] = chosen; serial_observation(report,state['guard'])
        report['initial_activity_before'] = snapshot(cdp); first_preset_gate(report['initial_activity_before']['state'])
        time.sleep(.2)
        report['initial'] = snapshot(cdp)
        report['initial_processing'] = verify_processing_progress(report['initial_activity_before']['state'],report['initial']['state'])
        blob = read_shared_bytes(BLOB)
        capture_plan = capture.plan_capture(report['initial']['responses'],blob)
        requests = ([capture_plan['request']] if capture_plan['request'] else []) + [capture_plan['header_request'],*capture_plan['chunk_requests']]
        report['capture_plan'] = capture_plan;report['phase']='capture_preparation_intent';save()
        cdp.evaluate('__miniFirstPresetGuard.configureCapture('+json.dumps({'slot':capture_plan['slot'],'requests':requests})+')')
        answers = {command:query(cdp,command) for command in requests}
        answers.update({name:query(cdp,name) for name in ('MODEL','CLIST')})
        report['capture_verification'] = capture.verify_capture(capture_plan,answers,blob)
        cdp.evaluate('__miniFirstPresetGuard.captureDone()')
        # Original readonly updater synchronizes S.capSlot/model from CLIST.
        # Never assign hidden editor state to manufacture an observed capture.
        cdp.evaluate('loadModelName()')
        require(cdp.evaluate('S.capSlot') == capture_plan['slot'], 'original capture UI did not synchronize')
        report['before_activity'] = snapshot(cdp); first_preset_gate(report['before_activity']['state'])
        time.sleep(.2)
        report['before'] = snapshot(cdp)
        report['UI_processing'] = verify_processing_progress(report['before_activity']['state'],report['before']['state'])
        free = next(n for n in range(32) if n not in {p['slot'] for p in report['before']['state']['plist']['presets']})
        name = cdp.evaluate('(S.pendName||presetName()||`Preset ${Math.floor('+str(free)+'/4)+1}${SLOT('+str(free)+')}`).slice(0,23)')
        plan = make_plan(report['before']['state'],name);report['plan']=plan;report['phase']='UI_trial_planned';save()
        cdp.evaluate('__miniFirstPresetGuard.configureTrial('+json.dumps(plan)+','+json.dumps(report['before']['responses'])+')')
        if not cdp.evaluate("document.getElementById('meters').classList.contains('open')"):cdp.click('#meters')
        report['before_screenshot']=cdp.screenshot(output/'before.png')
        for action,values in (('down1',plan['down']),('up',plan['gain'])):
            report['phase']=action+'_intent';save();ui_key(cdp,action,OUTPUT_KNOB)
            report[action]=snapshot(cdp);verify_state(report[action]['state'],report['before']['state'],gains=values,stage='live')
            report[action+'_screenshot']=cdp.screenshot(output/(action+'.png'))
        # Open/navigate the actual preset panel, never click its empty-name action (PNEW).
        if not cdp.evaluate("document.querySelector('.side').classList.contains('open')"):cdp.click('#presetBtn')
        bank = plan['slot']//4
        if cdp.evaluate('bank') != bank:cdp.click('#banks [data-bank="'+str(bank)+'"]')
        target = '#pList [data-preset="'+str(plan['slot'])+'"]'
        report['phase']='original_UI_save_intent';save()
        cdp.evaluate('__miniFirstPresetGuard.arm("save")');cdp.click(target+' [data-a="s"]')
        wait_state(cdp,lambda v:v['guard']['phase']=='scene_ack',20,'PSAVE/automatic scene A failed; no retry')
        report['saved']=snapshot(cdp)
        verify_state(report['saved']['state'],report['before']['state'],gains=plan['gain'],stage='saved',plan=plan)
        report['saved_screenshot']=cdp.screenshot(output/'saved.png')
        report['phase']='persistence_marker_intent';save();ui_key(cdp,'marker',OUTPUT_KNOB)
        report['marker']=snapshot(cdp)
        verify_state(report['marker']['state'],report['before']['state'],gains=plan['down'],stage='saved',plan=plan)
        if not cdp.evaluate("document.querySelector('.side').classList.contains('open')"):cdp.click('#presetBtn')
        report['phase']='original_UI_reload_intent';save();ui_key(cdp,'reload',target+' .n')
        report['reloaded']=snapshot(cdp)
        verify_state(report['reloaded']['state'],report['before']['state'],gains=plan['gain'],stage='reloaded',plan=plan)
        require(cdp.evaluate('S.capSlot') == plan['capture_slot'] and cdp.evaluate('S.gain') == plan['gain']
                and cdp.evaluate('S.snap') == 0, 'original editor state did not follow the actual reload')
        cdp.evaluate('__miniFirstPresetGuard.finish()')
        report['reloaded_screenshot']=cdp.screenshot(output/'reloaded.png')
        require(cdp.evaluate('HyperRigMini.profile')==prepared['profile'],'base profile changed')
        report.update(phase='UI_save_reload_complete',UI_sequence_completed=True,
            preset_intentionally_retained=True,capture_intentionally_retained=True)
    except Exception as error:
        report.update(result='fail',error=repr(error),failed_phase=report['phase'])
    finally:
        if cdp:
            try:
                # Stop periodic readonly polling, then let the already queued
                # original commands finish before closing the native stream.
                if report.get('UI_sequence_completed') and not report.get('error'):
                    busy = cdp.evaluate('(async()=>{clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;await Pedal.chain;return Pedal.busy;})()')
                    require(busy == 0, 'original command queue is not idle before close')
                report['disconnect']=close_serial(cdp);report['serial_port_closed']=report['disconnect']['native_close_verified']
                report['guard']=cdp.evaluate('__miniFirstPresetGuard.state')
                serial_observation(report,report['guard'])
                require(report['serial_port_closed'],'native serial closure not verified')
                if report.get('UI_sequence_completed') and not report.get('error'):
                    complete_proof(report,report['guard'],report['disconnect'])
            except Exception as error:
                report['cleanup_error']=repr(error);report['result']='fail'
                report['ui_roundtrip_verified']=report['save_reload_verified']=False
            try:cdp.call('Browser.close')
            except Exception:pass
            cdp.ws.close()
        if process:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
        server.shutdown();server.server_close();thread.join(timeout=2)
        report.update(browser_process_stopped=process is None or process.poll() is not None,
                      local_server_stopped=True,finished_utc=now())
        save()
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--check-only',action='store_true')
    for name in ('boot','connected','session'):
        parser.add_argument('--'+name,type=Path);parser.add_argument('--'+name+'-sha256')
    parser.add_argument('--output',type=Path);args=parser.parse_args(argv)
    require(not(args.execute and args.check_only),'choose execution or offline preflight')
    if not args.execute and not args.check_only:
        print(json.dumps({'device_io':False,'browser_started':False,'inputs_read':False,
            'plan':'Exact v3 proof; bounded A2 persistence/readback; original UI gain down/restore, save, marker, reload',
            'automatic_retry':False,'profile_modified':False}));return 0
    refs={}
    for name in ('boot','connected','session'):
        path,digest=getattr(args,name),getattr(args,name+'_sha256')
        require(path and digest,'three actual path/SHA evidence pairs required')
        refs[name]={'path':Path(path).resolve().relative_to(ROOT).as_posix(),'sha256':digest}
    prepared=prepare(**refs)
    if args.check_only:
        print(json.dumps({'preflight':'pass','device_io':False,'browser_started':False,'inputs':refs}));return 0
    require(args.output is not None,'new trial directory required')
    result=run(prepared,args.output)
    print(json.dumps({key:result.get(key) for key in ('result','phase','error','hardware_executed','save_reload_verified','serial_port_closed')}))
    return 0 if result['result']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
