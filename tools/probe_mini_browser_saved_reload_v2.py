"""Opt-in two-command original-editor continuation after verified partial save.

Only Output ArrowDown and Enter on the already saved preset are authorized.
Previous save evidence remains an unchanged failed/partial report. No hardware
runs by default. No capture/preset save, deletion, mutation retry or rollback.
Only completely empty bootstrap PING timeouts may repeat, at most five PINGs.
Native CDC identity and exact PONG do not attest the chooser actor or COM name.
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_browser_first_preset as frozen
from tools import run_mini_v3_first_preset_a2 as activity
from tools import run_mini_v3_first_preset_ui_v3 as ui
from tools import mini_browser_windows as browser_windows
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

browser,desktop,selection=frozen.browser,frozen.desktop,frozen.selection
require,sha,now=frozen.require,frozen.sha,frozen.now
APP=ui.NEW_APP
GUARD=ROOT/'tools/mini_browser_saved_reload_guard_v2.js'
SERIAL_OPEN_EXTENSION=ROOT/'tools/mini_browser_serial_open.js'
V1=ROOT/'tools/probe_mini_browser_saved_reload.py'
V1_SHA='8f044dcd2ab5cc98521a02b972a473cb5a686c3f7f88ef47c1e1c7fcec300db4'
PONG='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'
STATE=frozen.STATE.replace('__miniFirstPresetGuard','__miniSavedReloadGuard')
UI_STATE="({gain:S.gain.slice(),capture:S.capSlot,scene:S.snap,preset:S.curPre??null,selected:curPreset})"
UI_SYNC_QUERY="""(async()=>{
  const command_id=__miniSavedReloadGuard.state.commands.length;
  const response=await Pedal.cmd('LVL','LVL',800);
  applyLvl(reply(response,'LVL'));
  await Pedal.chain;
  return {response,command_id};
})()"""
OUTPUT_KNOB=frozen.OUTPUT_KNOB
FROZEN_SHA='87b4063f8e50cabb2d0cd230b1db279770211636842698d7048f748080831c3b'
ACTIVITY_SHA='c234aa9d36f9b0c95e71a692881f81342773d6e237766f1a2d1ed49df65ac2ab'
UI_SHA='e502afdc2bf2c67c6c457f19d374b2e8fdcdedb3b976d923c3d80ae866daac5e'


def partial_validator():
    # The reviewed root execution pins this source. Recording its actual digest
    # avoids a circular source hash with the joint qualifier that consumes us.
    from tools import qualify_mini_browser_preset as module
    return module


def prepare(*,partial):
    require(sha(V1.read_bytes())==V1_SHA,'frozen continuation v1 changed')
    require(sha(Path(frozen.__file__).read_bytes())==FROZEN_SHA and
            sha(Path(activity.__file__).read_bytes())==ACTIVITY_SHA and
            sha(Path(ui.__file__).read_bytes())==UI_SHA,'frozen parser/activity/UI dependencies differ')
    ui.validate_ui_copy();activity.verify_dependencies()
    prior=partial_validator().validate_partial_saved_report(ROOT/partial['path'],partial['sha256'])
    require(prior['report_ref']==partial,'partial report reference differs')
    context=prior['context'];plan=copy.deepcopy(prior['plan'])
    saved=prior['saved_snapshot']
    verify_saved(saved['state'],saved['state'],plan['gain'],plan)
    require(plan['gain'][1]>-30 and plan['down']==[plan['gain'][0],plan['gain'][1]-1],
            'one downward output step must remain inside the original knob range')
    return {'schema':1,'kind':'mini-browser-saved-reload-plan-v2','inputs':{'partial':dict(partial)},
            'prior_partial':prior,'context':context,'plan':plan,'saved_snapshot':saved,
            'partial_validator_sha256':sha(Path(partial_validator().__file__).read_bytes()),
            'guard':{'path':GUARD.relative_to(ROOT).as_posix(),'sha256':sha(GUARD.read_bytes())},
            'app_directory':APP.relative_to(ROOT).as_posix(),'profile':context['profile'],
            'ui_compatibility_extension':ui.description(),'A2_gate_extension':activity.description(),
            'UI_mutations_max':2,'capture_mutations_max':0,'preset_save_max':0,
            'automatic_retry':True,'automatic_retry_scope':'bootstrap PING empty timeouts only',
            'mutation_retry_performed':False,'query_retry_performed':False,
            'firmware_write':False,'profile_modified':False,
            'general_capabilities_granted':{}}


def verify_saved(state,saved,gains,plan):
    frozen.verify_state(state,saved,gains=gains,stage='live')
    require(state['plist']['current']==plan['slot'] and state['snaps']=={'present':'1000','current':0}
            and state['clist']['current']==plan['capture_slot'] and state['ir_current']==plan['ir_slot'],
            'the already saved preset/scene/capture differs')
    activity.checked_stat(state)


def snapshot(cdp):
    value=frozen.snapshot(cdp)
    lines=cdp.evaluate(activity.STAT_QUERY)
    value['responses']['STAT']=lines;value['state']['a2_stat']=activity.parse_stat(lines)
    activity.checked_stat(value['state'])
    return value


def verify_initial_ui_sync(value,plan):
    require(value.get('request')=='LVL' and value.get('method')=='original applyLvl'
            and type(value.get('command_id')) is int and value['command_id']>=0,
            'original LVL UI synchronization metadata differs')
    lines=value.get('response',[])
    line=lines[0] if isinstance(lines,list) and len(lines)==1 and isinstance(lines[0],str) else ''
    gain=re.search(r'\bg=(-?\d+)/(-?\d+)(?: |$)',line)
    scene=re.search(r'\bs=(-?\d+)(?: |$)',line)
    preset=re.search(r'\bc=\d+ p=(-?\d+)(?: |$)',line)
    require(line.startswith('LVL ') and gain and scene and preset
            and list(map(int,gain.groups()))==plan['gain']
            and int(scene[1])==0 and int(preset[1])==plan['slot'],
            'fresh LVL does not describe the actual already-saved state')
    require(value.get('after')=={'gain':plan['gain'],'capture':plan['capture_slot'],
            'scene':0,'preset':plan['slot'],'selected':plan['slot']},
            'original applyLvl did not synchronize the actual editor state')


def refresh_original_ui(cdp,report,plan):
    value={'request':'LVL','method':'original applyLvl','before':cdp.evaluate(UI_STATE)}
    report['original_UI_initial_sync']=value  # Retain the observation even if the query fails.
    value.update(cdp.evaluate(UI_SYNC_QUERY))
    value['after']=cdp.evaluate(UI_STATE)
    verify_initial_ui_sync(value,plan)


def processing_progress(first,second,saved,plan):
    verify_saved(first,saved,plan['gain'],plan);verify_saved(second,saved,plan['gain'],plan)
    a,b=activity.checked_stat(first),activity.checked_stat(second)
    require(a['nproc']<b['nproc'],'A2 completion counter must advance; no wrap/reset inference')
    generic=lambda value:copy.deepcopy(value['runtime']['engine'])
    before,after=generic(first),generic(second)
    return {'A2_nproc_before':a['nproc'],'A2_nproc_after':b['nproc'],'A2_nproc_delta':b['nproc']-a['nproc'],
            'A2_completion_progress_observed':True,'generic_before':before,'generic_after':after,
            'core1_job_progress_observed':all(before[k]<after[k] for k in ('posts','takes')),
            'generic_job_counters_required':False,'physical_audio_output_verified':False}


def wait_state(cdp,predicate,timeout,message):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=cdp.evaluate(STATE)
        require(not value.get('guard',{}).get('fatal'),value.get('guard',{}).get('fatal'))
        if predicate(value):return value
        time.sleep(.1)
    raise ValueError(message)


def ui_key(cdp,action,target,timeout=15):
    require(action in ('marker','reload'),'only the two continuation actions are allowed')
    cdp.evaluate('document.querySelector('+json.dumps(target)+').focus()')
    cdp.evaluate('__miniSavedReloadGuard.arm('+json.dumps(action)+')')
    key,code=('Enter',13) if action=='reload' else ('ArrowDown',40)
    for kind in ('keyDown','keyUp'):
        cdp.call('Input.dispatchKeyEvent',{'type':kind,'key':key,'code':key,'windowsVirtualKeyCode':code})
    return wait_state(cdp,lambda value:value['guard']['phase']==action+'_ack' and not value['gainPending'],
                      timeout,'actual UI command ACK missing; no retry or automatic restoration')


def wait_reloaded_ui(cdp,plan,timeout=15):
    """Observe the original asynchronous UI readback; send no command or key."""
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=cdp.evaluate('({gain:S.gain.slice(),capture:S.capSlot,scene:S.snap,preset:S.curPre,fatal:__miniSavedReloadGuard.state.fatal})')
        require(not value.get('fatal'),value.get('fatal'))
        if (value.get('gain')==plan['gain'] and value.get('capture')==plan['capture_slot']
                and value.get('scene')==0 and value.get('preset')==plan['slot']):return value
        time.sleep(.1)
    raise ValueError('original UI did not finish the actual reload readback; no retry')


def close_serial(cdp):
    result=cdp.evaluate("""(async()=>{
      __miniSavedReloadGuard.stop();
      if(typeof S!=='undefined'&&S.connected)await connect();
      else if(typeof SerialTransport!=='undefined'&&SerialTransport.isOpen()){
        clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;Pedal.abort();await Pedal.disconnect();}
      return {open:SerialTransport.isOpen(),closes:__miniSavedReloadGuard.state.closes,
        closeError:__miniSavedReloadGuard.state.closeError};})()""")
    return {**result,'native_close_verified':not result['open'] and result['closes']==1 and not result['closeError']}


def native_identity_proof(guard,expected_pong):
    """Reconstruct identity/bootstrap from native records; no UIA/COM inference."""
    require(expected_pong==PONG and guard.get('pongMatched') is True and not guard.get('fatal'),
            'exact normal v3 PONG required')
    require(guard.get('requests')==guard.get('opens')==1 and
            guard.get('portInfo')=={'vid':0x3654,'pid':0x5155} and not guard.get('nativeErrors'),
            'one native matching CDC open without stream errors required')
    opened=[e for e in guard['events'] if e['kind']=='serial_open_complete']
    infos=[e for e in guard['events'] if e['kind']=='native_port_info']
    require(len(opened)==1 and len(infos)==2 and all(e['info']==guard['portInfo'] for e in infos)
            and infos[-1]['seq']<opened[0]['seq'],'native getInfo/open chronology differs')
    attempts=guard.get('bootstrap_attempts',[])
    pings=[c for c in guard['commands'] if c['line']=='PING']
    require(1<=len(attempts)<=5 and len(pings)==len(attempts), 'bounded bootstrap attempts required')
    require([c['id'] for c in pings]==list(range(len(attempts))), 'PING must precede all actual commands')
    for index,(a,c) in enumerate(zip(attempts,pings),1):
        wires=[w for w in guard['wire'] if w['id']==a['wire_id']]
        native=[n for n in guard.get('nativeWrites',[]) if n['id']==a['native_write_id']]
        completion=[e for e in guard.get('editorCompletions',[]) if e['id']==a['editor_completion_id']]
        require(len(wires)==len(native)==len(completion)==1,'unique native/editor bootstrap records required')
        w,n,e=wires[0],native[0],completion[0]
        require(a['index']==index and a['command_id']==c['id'] and a['timeout_ms']==700 and
                c['completed'] is True and c['wire_id']==w['id'] and w['command_id']==c['id'] and
                w['line']=='PING' and w['hex']==n['hex']=='50494e470a' and w['completed'] is True and
                n['wire_id']==w['id'] and n['bytes']==5 and n['completed'] is True and
                e['command_id']==c['id'] and e['line']=='PING' and e['lines']==c['lines'],
                'native full PING write/original completion binding differs')
        require(opened[0]['seq']<w['seq'] and a['start_seq']<w['seq']<n['seq']<n['completed_seq']
                <=a['completion_seq']==c['seq'] and w['seq']<e['seq']<c['seq'],
                'PING/native completion chronology differs')
        if index>1:
            prior=attempts[index-2]
            require(prior['completion_seq']<a['start_seq'] and prior['end_rx_bytes']==a['start_rx_bytes']
                    and prior['end_reply_count']==a['start_reply_count'],'late bytes before repeated PING')
        for cutoff,byte_key,reply_key in ((a['start_seq'],'start_rx_bytes','start_reply_count'),
                                         (a['completion_seq'],'end_rx_bytes','end_reply_count')):
            require(sum(len(bytes.fromhex(r['hex'])) for r in guard['rx'] if r['seq']<=cutoff)==a[byte_key]
                    and sum(r['seq']<=cutoff for r in guard['replies'])==a[reply_key],
                    'bootstrap native RX/decoded-line counters differ')
        native_lines=b''.join(bytes.fromhex(r['hex']) for r in guard['rx'] if w['seq']<r['seq']<c['seq'])
        if index<len(attempts):
            require(a['status']=='empty_timeout' and a['repeat_permitted'] is True and e['timed_out'] is True
                    and c['lines']==[] and not native_lines and a['start_rx_bytes']==a['end_rx_bytes']
                    and a['start_reply_count']==a['end_reply_count'], 'only genuine entirely empty PING timeouts repeat')
        else:
            require(a['status']=='pong' and a['repeat_permitted'] is False and e['timed_out'] is False
                    and c['lines']==[expected_pong]
                    and expected_pong in native_lines.decode('utf-8','strict').replace('\r\n','\n').splitlines(),
                    'last bootstrap attempt needs exact PONG in real native RX')
    return {'kind':'native-open-and-exact-pong','port_info':copy.deepcopy(guard['portInfo']),
            'port_info_source':'SerialPort.getInfo()','native_open_event':copy.deepcopy(opened[0]),
            'exact_pong':expected_pong,'pong_command_id':pings[-1]['id'],'pong_wire_id':pings[-1]['wire_id'],
            'bootstrap':{'attempt_count':len(attempts),'empty_timeout_count':len(attempts)-1,
                         'maximum_attempts':5,'attempts':copy.deepcopy(attempts)},
            'raw_RX_verified':True,'UIA_selection_attested':False,'selection_actor':'unattested',
            'COM_name_attested':False,'binary_hash_attested_by_device':False}


def verify_wire(guard,plan,expected_pong=PONG):
    identity=native_identity_proof(guard,expected_pong)
    empty_ids={a['command_id'] for a in identity['bootstrap']['attempts'] if a['status']=='empty_timeout'}
    require(guard.get('fatal') is None and guard.get('phase')=='complete' and guard.get('mutations')==2,
            'completed unpoisoned two-command continuation required')
    require(guard.get('requests')==guard.get('opens')==guard.get('closes')==1
            and not guard.get('closeError') and guard.get('stopped') is True,'one observed native connection/close required')
    plans=[e['plan'] for e in guard['events'] if e.get('kind')=='trial_plan']
    require(plans==[plan],'one actual continuation plan required')
    expected=['GAIN '+' '.join(map(str,plan['down'])),plan['load_request']]
    origins=['Output persistence marker ArrowDown','Original preset-row Enter']
    wire,commands,rx=guard['wire'],guard['commands'],guard['rx']
    require(wire and rx and len(wire)<=2000,'bounded retained native trace required')
    mutations=[item for item in wire if item['origin']!='query']
    require([(item['line'],item['origin']) for item in mutations]==list(zip(expected,origins)),
            'only one actual GAIN and one actual PLOAD may occur')
    actions=guard['ui'];acks=[e for e in guard['events'] if e.get('kind')=='mutation_ack']
    require(len(actions)==2 and [e.get('key') for e in actions]==['ArrowDown','Enter']
            and all(e.get('kind')=='keydown' and e.get('trusted') is True for e in actions),
            'exact trusted Output/preset keys required')
    require([e['line'] for e in acks]==expected,'actual ACK sequence differs')
    expected_gain=['GAIN in='+str(plan['down'][0])+' out='+str(plan['down'][1])+' dB']
    require(acks[0]['lines']==expected_gain,'actual gain ACK differs')
    # Original 020092FA output parameters are load result codes; library slots
    # remain independently checked by verify_saved using CLIST/ILIST/PRE.
    load_pattern="PLOAD ok "+str(plan['slot'])+" '"+re.escape(plan['name'])+r"' missing=0 capture=0 ir=0 ms=\d+"
    require(len(acks[1]['lines'])==1 and re.fullmatch(load_pattern,acks[1]['lines'][0]),'actual PLOAD ACK differs')
    for index,item in enumerate(mutations):
        require(actions[index]['seq']<item['seq']<acks[index]['seq']
                and (index==0 or acks[index-1]['seq']<actions[index]['seq']),'UI/wire/ACK chronology differs')
    for item in wire:
        if item['origin']=='query':require(frozen.evidence.is_query(item['line']),'mutation disguised as a query')
        require(item['hex']==(item['line']+'\n').encode('ascii').hex() and item['completed'] is True,'actual TX bytes differ')
        native=[n for n in guard['nativeWrites'] if n['wire_id']==item['id']]
        require(len(native)==1 and native[0]['completed'] is True and native[0]['hex']==item['hex']
                and native[0]['id']==item['native_write_id'],'native writer fulfillment differs')
        matches=[c for c in commands if c['id']==item['command_id'] and c.get('wire_id')==item['id']]
        require(len(matches)==1 and matches[0].get('completed') is True and matches[0]['line']==item['line'],
                'original command completion missing')
        command=matches[0]
        if command['id'] in empty_ids:continue  # Independently proved native empty bootstrap timeout above.
        require(command.get('lines') and all(isinstance(line,str) and not line.startswith('ERR') for line in command['lines']),
                'successful original command response required')
        if item in mutations:
            ack=acks[mutations.index(item)]
            require(command['lines']==ack['lines'] and command['seq']<ack['seq'],'ACK differs from original command completion')
        raw=b''.join(bytes.fromhex(r['hex']) for r in rx if item['seq']<r['seq']<command['seq'])
        lines=raw.decode('utf-8',errors='strict').replace('\r\n','\n').splitlines();cursor=0
        for line in command['lines']:
            try:cursor=lines.index(line,cursor)+1
            except ValueError:raise ValueError('completed response absent from native RX: '+item['line']) from None
    return {'wire_command_count':len(wire),'raw_RX_byte_count':sum(len(bytes.fromhex(r['hex'])) for r in rx),
            'completed_commands_checked_against_native_RX':True,'actual_UI_mutation_count':2,
            'empty_bootstrap_timeouts_verified':len(empty_ids),'selection_proof':identity}


def complete_proof(report,guard,disconnect):
    report.update(result='fail',retained_saved_reload_verified=False)
    require(report.get('UI_sequence_completed') is True and not report.get('error'),'completed actual observations required')
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes')==1 and not disconnect.get('closeError'),'actual native close required')
    report['raw_trace_verification']=verify_wire(guard,report['plan'],report['prepared']['context']['pong'])
    require(report['selection_proof']==native_identity_proof(guard,report['prepared']['context']['pong']),
            'native identity proof changed')
    report.update(result='pass',retained_saved_reload_verified=True)


serial_observation=frozen.serial_observation


def run(prepared, output):
    require(prepare(**prepared['inputs']) == prepared, 'prepared evidence changed')
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'build') and not output.exists(), 'new build directory required')
    output.mkdir(parents=True); profile_dir = output/'isolated-profile'; profile_dir.mkdir()
    report = {'schema':1, 'kind':'mini-browser-saved-reload-continuation-v2', 'result':'running', 'phase':'prepare',
        'started_utc':now(), 'prepared':prepared, 'image_sha256':desktop.IMAGE_SHA, 'transport':'usb-cdc',
        'hardware_executed':False, 'execution_status_unknown':False,
        'serial_port_closed':False, 'retained_saved_reload_verified':False,
        'prior_save_reperformed':False,'capture_write_performed':False, 'audio_quality_verified':False, 'power_cycle_verified':False,
        'held_recovery_verified':False, 'BLE_verified':False, 'firmware_write':False,
        'automatic_retry':True,'automatic_retry_scope':'bootstrap PING empty timeouts only',
        'mutation_retry_performed':False,'query_retry_performed':False,
        'profile_modified':False, 'general_capabilities_granted':{},
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
            [Path(__file__), V1, GUARD, SERIAL_OPEN_EXTENSION, Path(browser_windows.__file__), Path(partial_validator().__file__), Path(frozen.__file__), Path(activity.__file__),
             Path(ui.__file__), Path(selection.__file__), Path(frozen.readonly.__file__), Path(frozen.mutation.__file__),
             Path(browser.__file__), ROOT/'tools/verify_mini_browser.py', Path(desktop.__file__),
             ROOT/'tools/mini_host_journal.py', *(p for p in APP.iterdir() if p.is_file())]}}
    save = lambda:atomic_write_json(output/'report.json', report)
    save()
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0), partial(browser.LocalHandler, directory=str(APP), live=True))
    thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    process = cdp = None
    try:
        arguments = browser_windows.browser_arguments(browser_windows.browser_path(),profile_dir)
        report['browser_arguments'] = arguments
        report['browser_configuration'] = browser_windows.description(arguments)
        save()
        with (output/'browser-stderr.txt').open('wb') as stream:
            process = subprocess.Popen(arguments,
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
        cdp.ws.settimeout(45)
        report['browser'] = get('/json/version'); report['CDP_http'] = devtools
        for domain in ('Runtime','Page','Log'):cdp.call(domain+'.enable')
        config = {'live':True,'image_sha256':desktop.IMAGE_SHA,'pong':prepared['context']['pong'],'plan':prepared['plan']}
        cdp.call('Page.addScriptToEvaluateOnNewDocument',{'source':GUARD.read_text('utf-8')+
            '\ninstallMiniBrowserSavedReloadGuard('+json.dumps(config)+');'})
        origin = f'http://127.0.0.1:{server.server_port}'
        report['origin'] = origin; report['selection_path'] = (output/'selection.json').relative_to(ROOT).as_posix()
        cdp.call('Page.navigate',{'url':origin+'/tankmini.html?saved_reload_continuation=1'})
        initial = wait_state(cdp,lambda v:v['ready'],10,'original editor bootstrap failed')
        require(initial['profile'] == prepared['profile'] and not initial['demo'],'base profile or real-editor mode differs')
        report['serial_open_extension']=cdp.evaluate(SERIAL_OPEN_EXTENSION.read_text('utf-8')+
            '\ninstallMiniSerialOpenTimeout(SerialTransport);')
        require(report['serial_open_extension'].get('timeout_ms')==30000,'serial open timeout extension failed')
        save()
        cdp.evaluate('__miniSavedReloadGuard.installApp(SerialTransport,Pedal,HyperRigMini.profile)')
        cdp.evaluate("document.getElementById('miniPortStatus').textContent='Prova USB limitata: volume e ricaricamento del preset salvato.'")
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"):cdp.click('.ccall .tskip')
        # Once the chooser/open path is invoked, loss of CDP cannot prove that
        # no serial port opened. Only a later native guard observation resolves it.
        report.update(phase='awaiting_native_CDC_selection',hardware_executed=None,execution_status_unknown=True)
        save()
        cdp.evaluate('__miniSavedReloadGuard.allowRequest()');cdp.click('#connBtn')
        state = wait_state(cdp,lambda v:v['connected'] and v['initialReadsFinished'],120,'real WebSerial bootstrap failed')
        require(state['fw']==prepared['context']['pong'] and state['guard']['pongMatched'],'actual exact PONG differs')
        report['selection_proof']=native_identity_proof(state['guard'],prepared['context']['pong'])
        if (output/'selection.json').exists():
            chosen=json.loads(read_shared_bytes(output/'selection.json'))
            selection.validate_selection(chosen,browser_pid=process.pid,origin=origin,com=prepared['context']['com'],
                start=report['started_utc'],validated_at=now())
            report['selection']=chosen  # Optional independent UIA evidence; never invented.
        serial_observation(report,state['guard'])
        plan=prepared['plan'];report['plan']=copy.deepcopy(plan)
        saved=prepared['saved_snapshot']['state']
        # Connect applies only LVL gain; hidden-page polling need not initialize
        # S.curPre. Apply one fresh response with the original UI function first.
        refresh_original_ui(cdp,report,plan)
        report['before_activity']=snapshot(cdp)
        verify_saved(report['before_activity']['state'],saved,plan['gain'],plan)
        time.sleep(.2)
        report['before']=snapshot(cdp)
        report['processing']=processing_progress(report['before_activity']['state'],report['before']['state'],saved,plan)
        actual_ui=report['original_UI_before_plan']=cdp.evaluate(UI_STATE)
        require(actual_ui['capture']==plan['capture_slot'] and actual_ui['preset']==plan['slot']
                and actual_ui['scene']==0 and actual_ui['gain']==plan['gain'],
                'original editor does not reflect the actual already-saved state')
        cdp.evaluate('__miniSavedReloadGuard.configureTrial('+json.dumps(plan)+','+json.dumps(report['before']['responses'])+')')
        # Presets closes the meters popup. Open it explicitly before the marker;
        # do not force focus or inert flags and do not weaken the original knob check.
        if not cdp.evaluate("document.getElementById('meters').classList.contains('open')"):cdp.click('#meters')
        report['before_screenshot']=cdp.screenshot(output/'before.png')
        target='#pList [data-preset="'+str(plan['slot'])+'"]'
        report['phase']='persistence_marker_intent';save();ui_key(cdp,'marker',OUTPUT_KNOB)
        report['marker']=snapshot(cdp)
        verify_saved(report['marker']['state'],saved,plan['down'],plan)
        if not cdp.evaluate("document.querySelector('.side').classList.contains('open')"):cdp.click('#presetBtn')
        if cdp.evaluate('bank')!=plan['slot']//4:cdp.click('#banks [data-bank="'+str(plan['slot']//4)+'"]')
        report['phase']='original_UI_reload_intent';save();ui_key(cdp,'reload',target+' .n')
        report['original_UI_reload_observation']=wait_reloaded_ui(cdp,plan)
        report['reloaded']=snapshot(cdp)
        verify_saved(report['reloaded']['state'],saved,plan['gain'],plan)
        require(cdp.evaluate('S.capSlot') == plan['capture_slot'] and cdp.evaluate('S.gain') == plan['gain']
                and cdp.evaluate('S.snap') == 0, 'original editor state did not follow the actual reload')
        cdp.evaluate('__miniSavedReloadGuard.finish()')
        report['reloaded_screenshot']=cdp.screenshot(output/'reloaded.png')
        require(cdp.evaluate('HyperRigMini.profile')==prepared['profile'],'base profile changed')
        report.update(phase='UI_saved_preset_reload_complete',UI_sequence_completed=True,
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
                report['guard']=cdp.evaluate('__miniSavedReloadGuard.state')
                serial_observation(report,report['guard'])
                require(report['serial_port_closed'],'native serial closure not verified')
                if report.get('UI_sequence_completed') and not report.get('error'):
                    complete_proof(report,report['guard'],report['disconnect'])
            except Exception as error:
                report['cleanup_error']=repr(error);report['result']='fail'
                report['retained_saved_reload_verified']=False
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
    parser.add_argument('--partial-report',type=Path);parser.add_argument('--partial-report-sha256')
    parser.add_argument('--output',type=Path);args=parser.parse_args(argv)
    require(not(args.execute and args.check_only),'choose execution or offline preflight')
    if not args.execute and not args.check_only:
        print(json.dumps({'device_io':False,'browser_started':False,'inputs_read':False,
            'plan':'One Output ArrowDown then original preset-row Enter; no save or deletion',
            'automatic_retry':True,'automatic_retry_scope':'bootstrap PING empty timeouts only'}));return 0
    require(args.partial_report and args.partial_report_sha256,'actual partial-save report path/SHA required')
    path=args.partial_report.resolve();require(path.is_relative_to(ROOT),'partial report must remain in workspace')
    ref={'path':path.relative_to(ROOT).as_posix(),'sha256':args.partial_report_sha256}
    prepared=prepare(partial=ref)
    if args.check_only:
        print(json.dumps({'preflight':'pass','device_io':False,'browser_started':False,'inputs':prepared['inputs'],
                          'plan':prepared['plan']}));return 0
    require(args.output is not None,'new continuation directory required')
    result=run(prepared,args.output)
    print(json.dumps({key:result.get(key) for key in ('result','phase','error','hardware_executed','retained_saved_reload_verified','serial_port_closed')}))
    return 0 if result['result']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
