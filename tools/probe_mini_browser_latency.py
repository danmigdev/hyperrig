"""Explicit bounded FX timing experiment on an already connected owned editor.

Default/check-only are file-only. Execute attaches to the exact normal editor
session after a real saved-preset reload proof. It neither opens a serial port
nor creates a browser. A temporary exact-request guard records native TX/RX;
the installed app profile and its general command families remain unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import mini_latency_observation as timing
from tools import probe_mini_browser_first_preset as original
from tools import run_mini_v3_first_preset_a2 as a2
from tools.verify_mini_browser import CDP
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

GUARD = ROOT/'tools/mini_browser_latency_guard.js'
QUALIFIER_SHA = 'a1def5b08c85efc83e55679d49bc9b55432d487be5dc7a4515da0449e8158287'
ORIGINAL_SHA = '87b4063f8e50cabb2d0cd230b1db279770211636842698d7048f748080831c3b'
IMAGE = '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c'
require = timing.require


def digest(value):
    return hashlib.sha256(value).hexdigest()


def local(path):
    p = Path(path).resolve()
    require(p.is_relative_to(ROOT), 'workspace path required')
    return p


def prepare(session_path):
    timing.verify_sources()
    require(digest(Path(original.__file__).read_bytes()) == ORIGINAL_SHA, 'frozen snapshot/queue helper differs')
    qualifier = importlib.import_module('tools.qualify_mini_browser_preset')
    require(digest(Path(qualifier.__file__).read_bytes()) == QUALIFIER_SHA, 'reviewed qualifier differs')
    path = local(session_path); raw = read_shared_bytes(path); session = json.loads(raw)
    require(session.get('kind') == 'mini-qualified-editor-session' and session.get('phase') == 'connected_qualified_USB'
            and session.get('identity_verified') is True and not session.get('finished_utc')
            and not any(session.get(k) for k in ('error', 'observation_error', 'close_observation_error')),
            'one currently connected qualified editor session required')
    require(not (path.parent/'close.request').exists(), 'editor close is already requested')
    prior = session['prepared']; bundle = qualifier.validate_bundle(local(ROOT/prior['bundle_directory']))
    require(bundle == prior['bundle'] and bundle['profile'] == prior['profile'] and bundle['image_sha256'] == IMAGE,
            'session/bundle/image differ')
    require(isinstance(session.get('source_sha256'), dict)
            and {'tools/launch_mini_editor.py', 'tools/qualify_mini_browser_preset.py'} <= set(session['source_sha256']),
            'qualified launcher/verifier source provenance required')
    for name, expected in session['source_sha256'].items():
        require(digest(read_shared_bytes(local(ROOT/name))) == expected, 'live editor source differs: '+name)
    q = bundle['qualification']
    require(q['one_reload_verified'] is True and q['hardware_executed'] is True
            and q['preset_intentionally_retained'] is True and 'PLOAD 0' in q['physically_exercised_requests']['PLOAD'],
            'actual baseline PLOAD0 proof required; global restoration is not required')
    snapshot = q['reloaded_snapshot']
    parsed = original.parse_snapshot({k: snapshot['responses'][k] for k in original.READS})
    require(all(snapshot['state'][k] == v for k, v in parsed.items()), 'sealed reloaded state parsing differs')
    require(parsed['plist']['current'] == 0 and parsed['snaps'] == {'present': '1000', 'current': 0}
            and parsed['clist']['current'] == 0 and parsed['ir_current'] == -1 and not parsed['fxs']['blocks'],
            'this plan restores the proven A2-only preset0/sceneA/capture0')
    original.runtime_gate(parsed)
    entry = next(p for p in parsed['plist']['presets'] if p['slot'] == 0)
    require(re.fullmatch(r'[A-Za-z0-9 _.-]{1,23}', entry['name']), 'bounded saved preset name required')
    websocket = session.get('CDP_page_websocket', '')
    require(re.fullmatch(r'ws://127\.0\.0\.1:[1-9]\d{0,4}/devtools/page/[A-Za-z0-9-]+', websocket),
            'exact owned local page websocket required')
    require(re.fullmatch(r'http://127\.0\.0\.1:[1-9]\d{0,4}', session['origin']), 'owned local origin required')
    return {'kind': 'mini-exact-latency-preparation-v1', 'session': {'path': path.relative_to(ROOT).as_posix(),
            'sha256_at_prepare': digest(raw)}, 'bundle': bundle, 'baseline': parsed,
            'reload_evidence': q['reloaded_report'], 'saved_evidence': q.get('saved_partial_report'),
            'websocket': websocket, 'origin': session['origin'], 'profile': bundle['profile'],
            'pong': bundle['pong'], 'image_sha256': IMAGE, 'restore_ack_prefix': "PLOAD ok 0 '"+entry['name']+"'",
            'families_granted_by_this_experiment': [], 'serial_open_performed': False}


class ExistingEditor:
    def __init__(self, cdp):
        self.cdp = cdp

    def install(self, prepared):
        value = self.cdp.evaluate("({origin:location.origin,connected:S.connected,demo:DEMO,fw:S.fw,profile:HyperRigMini.profile,transport:Pedal.tr===SerialTransport})")
        require(value == {'origin': prepared['origin'], 'connected': True, 'demo': False,
                          'fw': prepared['pong'], 'profile': prepared['profile'], 'transport': True},
                'live owned page/identity/profile differs')
        self.cdp.evaluate('(async()=>{await Pedal.chain;return Pedal.busy;})()')
        config = {k: prepared[k] for k in ('profile', 'pong', 'restore_ack_prefix')}
        self.cdp.evaluate(GUARD.read_text('utf-8')+'\ninstallMiniLatencyGuard('+json.dumps(config)+')')

    def prime(self):
        self.cdp.evaluate('__miniLatencyGuard.prime()')

    def query(self, line):
        if line == 'STAT':
            return self.cdp.evaluate(a2.STAT_QUERY)
        if line == 'FXT':
            return self.cdp.evaluate('Pedal.cmd("FXT",l=>/^FXT (?:end|fin)$/.test(l)||/^ERR/.test(l),4000)')
        if line == 'PING':
            return self.cdp.evaluate('Pedal.cmd("PING","PONG",3000)')
        return original.query(self.cdp, line)

    def snapshot(self):
        answers = {k: self.query(k) for k in original.READS}
        return {'responses': answers, 'state': original.parse_snapshot(answers)}

    def context(self):
        return {k: self.query(k) for k in ('CLKSTATE', 'MODEL', 'GAIN', 'FXS', 'MEM')}

    def configure(self, plan):
        self.cdp.evaluate('__miniLatencyGuard.configure('+json.dumps(plan)+')')

    def state(self):
        return self.cdp.evaluate('__miniLatencyGuard.state')

    def next(self):
        return self.cdp.evaluate('__miniLatencyGuard.executeNext()')

    def advance(self):
        return self.cdp.evaluate('__miniLatencyGuard.advance()')

    def restore(self):
        self.cdp.evaluate('__miniLatencyGuard.restore()')
        return self.next()

    def refresh(self, baseline):
        value = self.cdp.evaluate("""(async()=>{
          applyLvl(reply(await Pedal.cmd('LVL','LVL',1500),'LVL'));
          await loadChain();await loadSnaps();await loadModelName();await Pedal.chain;
          return {gain:S.gain,chain:S.chain,model:S.model,capture:S.capSlot,
            scene:S.snap,scenes:S.snaps,preset:curPreset,firmwarePreset:S.curPre,amp:S.amp,ampPresent:S.ampPresent};
        })()""")
        require(value['gain'] == baseline['gain'] and value['chain'] == {'P': [], 'Q': []}
                and value['model'] == 'A2' and value['capture'] == 0 and value['scene'] == 0
                and value['scenes'] == [1, 0, 0, 0] and value['preset'] == value['firmwarePreset'] == 0
                and value['amp'] == value['ampPresent'] == 1,
                'original readonly UI refresh differs from the restored saved state')
        return value

    def detach(self, restored):
        return self.cdp.evaluate('__miniLatencyGuard.detach('+json.dumps(restored)+')')


def measure(editor, *, clock=time.monotonic, sleep=time.sleep, publish=lambda value: None):
    before = editor.context(); timing.context(before)
    start = clock(); samples = []; result = None
    for index in range(timing.MAX_SAMPLES):
        if index:
            if clock()-start+1.5+4 > 20:
                break  # Reserve the original command's full 4-second timeout.
            sleep(1.5)
        rows = editor.query('STAT')
        elapsed = (clock()-start)*1000
        require(elapsed <= timing.MAX_ELAPSED_MS, 'bounded measurement elapsed time exceeded')
        samples.append({'elapsed_ms': elapsed, 'lines': rows})
        publish({'phase': 'timing_sample', 'samples': copy.deepcopy(samples)})
        if len(samples) >= 2:
            # This interim calculation only controls the finite read loop. A
            # fresh after-state is obtained and checked before returning.
            result = timing.analyze_measurement({'before': before, 'after': before, 'samples': samples})
            if result['measurement_complete']:
                break
    require(result is not None and result['measurement_complete'], 'finite read budget lacked three fresh STG windows')
    after = editor.context()
    return timing.analyze_measurement({'before': before, 'after': after, 'samples': samples})


def verify_added_state(fxs, plan, created, types):
    state = timing.protocol.parse_fxs(fxs)
    require(state['amp'] == {'present': 1, 'on': 1} and len(state['blocks']) == len(created), 'FX readback count/amp differs')
    for step, instance in zip(plan['steps'], created):
        block = next((x for x in state['blocks'] if x['id'] == instance['id']), None)
        require(block is not None and block['type'] == step['type'] and block['bank'] == step['bank'] and block['on'] == 1,
                'actual new effect identity/bank/enable differs')
        targets = {x['parameter']['index']: x['parameter']['value'] for x in step['configure_after_actual_id'] if 'parameter' in x}
        for i, rule in types[step['type']]['params'].items():
            value = block['params'][i]
            if rule['name'] == 'os_n':
                require(value in (0, 1, 3), 'actual oversampling outside original discrete tiers')
            else:
                require(value == targets.get(i, rule['default']), 'actual effect parameter differs from bounded plan')
    return state


def verify_trace(guard, restore_ack_prefix, pong):
    require(guard.get('detached') is True and guard.get('healthy') is True and not guard.get('fatal'),
            'healthy detached experiment required before a positive result')
    require(guard.get('restoreIssued') is True and guard.get('phase') == 'restored_ack', 'actual restoration ACK required')
    commands, wire, rx = guard['commands'], guard['wire'], guard['rx']
    require(len(commands) == len(wire) <= 2000 and rx, 'complete bounded native trace required')
    require([w['id'] for w in wire] == list(range(len(wire)))
            and [c['id'] for c in commands] == list(range(len(commands))), 'wire/command IDs are not unique and contiguous')
    verified_pongs = [c['lines'] for c in commands if c['line'] == 'PING' and not c['priming']]
    require(verified_pongs and all(r == [pong] for r in verified_pongs), 'fresh actual PONG differs')
    priming = []
    for item in wire:
        require(item['id'] >= 0 and item['hex'] == (item['line']+'\n').encode('ascii').hex()
                and item['completed'] is True, 'native TX differs or incomplete')
        found = [c for c in commands if c['id'] == item['command_id'] and c.get('wire_id') == item['id']]
        require(len(found) == 1 and found[0]['completed'] is True and found[0]['line'] == item['line'], 'command binding differs')
        command = found[0]
        require(item['mutation'] == (not original.evidence.is_query(item['line'])),
                'mutation/query classification differs')
        if command['priming']:
            require(not item['mutation'], 'mutation cannot use the reader-hook priming exception')
            priming.append(item['line']); continue
        require(command['native_RX_verified'] is True, 'guard did not verify the native reply')
        native = b''.join(bytes.fromhex(r['hex']) for r in rx if item['seq'] < r['seq'] < command['completed_seq'])
        retained = native.decode('utf-8', 'strict').replace('\r\n', '\n').splitlines(); cursor = 0
        for response in command['lines']:
            try:
                cursor = retained.index(response, cursor)+1
            except ValueError:
                raise ValueError('response absent from native bytes: '+item['line']) from None
    mutations = [w['line'] for w in wire if w['mutation']]
    require(guard['mutations'] == len(mutations), 'mutation count differs from actual wire')
    require(mutations and mutations[-1] == 'PLOAD 0' and mutations.count('PLOAD 0') == 1,
            'one final baseline PLOAD0 required')
    require(all(line.startswith(('GAIN ', 'FXA ', 'FXP ', 'FXE ')) or line == 'PLOAD 0' for line in mutations),
            'unplanned mutation family in raw trace')
    last_wire = [w for w in wire if w['mutation']][-1]
    last_reply = next(c['lines'] for c in commands if c['id'] == last_wire['command_id'])
    require(len(last_reply) == 1 and re.fullmatch(re.escape(restore_ack_prefix)+r' missing=0 capture=0 ir=-1 ms=\d+', last_reply[0]),
            'native PLOAD0 ACK does not match the proven saved preset')
    plans = [e['plan'] for e in guard['events'] if e['kind'] == 'plan']
    require(len(plans) == 1, 'one exact plan required')
    plan = plans[0]; pending = list(plan['setup_requests']); step = 0; created = set(); rejected = False
    for item in [w for w in wire if w['mutation']][:-1]:
        require(not rejected, 'mutation followed a protocol rejection instead of restoration')
        if not pending:
            require(step < len(plan['steps']), 'mutation exceeds finite plan')
            pending = [plan['steps'][step]['add_request']]
        require(item['line'] == pending.pop(0), 'actual mutation is not the next exact plan request')
        cmd = next(c for c in commands if c['id'] == item['command_id'])
        reply = cmd['lines']; line = item['line']
        if any(re.match(r'^ERR (FXA|FXP|FXE)\b', r) for r in reply):
            rejected = True; continue
        if line.startswith('GAIN '):
            require(reply == ['GAIN in='+line.split()[1]+' out='+line.split()[2]+' dB'], 'GAIN ACK differs')
        elif line.startswith('FXA '):
            matches = [re.fullmatch(r'FXA id=(\d+) '+re.escape(plan['steps'][step]['type']), r) for r in reply]
            matches = [m for m in matches if m]
            require(len(matches) == 1 and 0 <= int(matches[0][1]) < 16 and int(matches[0][1]) not in created,
                    'new actual FXA id differs')
            bid = int(matches[0][1]); created.add(bid)
            pending = [c['request_template'].replace('{id}', str(bid)) for c in plan['steps'][step]['configure_after_actual_id']]
            step += 1
        elif line.startswith('FXP '):
            require(reply == ['FXP ok '+line.split()[3]], 'FXP ACK differs')
        else:
            require(reply == ['FXE ok'], 'FXE ACK differs')
    return {'native_RX_bytes': sum(len(bytes.fromhex(r['hex'])) for r in rx), 'wire_commands': len(wire),
            'reader_hook_priming_queries_not_claimed_as_raw_RX_proof': priming,
            'actual_mutation_requests': mutations, 'no_NOR_save_delete_or_firmware_commands': True}


def verify_observations(report, guard):
    """Bind reported measurements and snapshots to the authenticated command log.

    Background readonly polling may occur between requests, but each retained
    response must match a distinct completed command in chronological order.
    A whole timing interval must stay within one mutation epoch.
    """
    commands = guard['commands']; cursor = 0; matched = []

    def consume(line, rows):
        nonlocal cursor
        for index in range(cursor, len(commands)):
            c = commands[index]
            if c['line'] == line and c.get('completed') and not c.get('priming') and c.get('lines') == rows:
                cursor = index+1; matched.append(c['id']); return c
        raise ValueError('reported observation absent from chronological native trace: '+line)

    def snapshot(value):
        parsed = original.parse_snapshot(value['responses'])
        require(value['state'] == parsed, 'reported snapshot parser result differs')
        return [consume(k, value['responses'][k]) for k in original.READS]

    snapshot(report['before'])
    original.verify_state(report['before']['state'], report['prepared']['baseline'],
                          gains=report['prepared']['baseline']['gain'], stage='live')
    consume('FXT', report['plan']['actual_catalog'])
    for observation in report['measurements']:
        value = observation['measurement']
        derived = timing.analyze_measurement({'before': value['before']['raw'],
            'after': value['after']['raw'], 'samples': value['raw_samples']})
        require(derived == value and derived['measurement_complete'], 'reported timing derivation differs')
        items = [consume(k, value['before']['raw'][k]) for k in ('CLKSTATE', 'MODEL', 'GAIN', 'FXS', 'MEM')]
        items += [consume('STAT', sample['lines']) for sample in value['raw_samples']]
        items += [consume(k, value['after']['raw'][k]) for k in ('CLKSTATE', 'MODEL', 'GAIN', 'FXS', 'MEM')]
        require(len({c['epoch'] for c in items}) == 1, 'mutation crossed a reported timing interval')
        blocks = derived['before']['configuration']['blocks']
        require(len(blocks) == observation['instances'] and all(b['on'] == 1 for b in blocks),
                'reported enabled-instance count differs from actual FXS')
    restored = snapshot(report['restored'])
    final_load = next(w for w in guard['wire'] if w['line'] == 'PLOAD 0')
    require(all(c['seq'] > final_load['seq'] for c in restored), 'restored snapshot predates actual PLOAD0')
    original.verify_state(report['restored']['state'], report['prepared']['baseline'],
                          gains=report['prepared']['baseline']['gain'], stage='live')
    return {'observations_bound_to_native_commands': True, 'command_ids': matched,
            'timing_derivations_recomputed': len(report['measurements'])}


def experiment(prepared, editor, *, publish=lambda value: None, clock=time.monotonic, sleep=time.sleep):
    report = {'kind': 'mini-exact-browser-FX-timing-trial-v1', 'result': 'running', 'prepared': prepared,
              'measurements': [], 'mutation_families_granted': [], 'analog_latency_measured': False,
              'audio_quality_verified': False, 'stimulus_controlled': False, 'worst_case_latency_proven': False,
              'serial_open_performed': False, 'serial_close_performed': False,
              'automatic_retry': False, 'preset_save_or_delete_performed': False, 'hardware_executed': False,
              'baseline_restoration_verified': False, 'temporary_wrapper_removed': False}
    installed = False; restored = False
    def save():
        if installed:
            try:
                report['guard'] = editor.state()
                if report['guard'].get('wire'):
                    report['hardware_executed'] = True
            except Exception as observation_error:
                report['guard_observation_error'] = repr(observation_error)
        publish(copy.deepcopy(report))
    try:
        editor.install(prepared); installed = True
        report['phase'] = 'reader_hook_priming_intent'; report['hardware_executed'] = None; save()
        editor.prime()
        require(editor.query('PING') == [prepared['pong']], 'fresh native verified identity differs')
        report['before'] = editor.snapshot()
        original.verify_state(report['before']['state'], prepared['baseline'], gains=prepared['baseline']['gain'], stage='live')
        fxt, mem = editor.query('FXT'), editor.query('MEM')
        plan = timing.plan_stress(fxt, report['before']['responses']['FXS'], mem, report['before']['responses']['GAIN'])
        require(plan['steps'], 'no effect admitted by the current declared estimates')
        report['plan'] = plan; report['phase'] = 'plan_ready'; save()
        baseline_measurement = measure(editor, clock=clock, sleep=sleep)
        report['measurements'].append({'instances': 0, 'measurement': baseline_measurement})
        require(baseline_measurement['no_reported_faults_in_supplied_observations'],
                'baseline processing faults; no effect mutation was armed')
        editor.configure(plan)
        while editor.state()['phase'] not in ('stress_done', 'rejected'):
            state = editor.state()
            if state['phase'] == 'between':
                actual_fxs, actual_mem = editor.query('FXS'), editor.query('MEM')
                verify_added_state(actual_fxs, plan, state['created'], timing.protocol.parse_fxt(fxt))
                report['last_admitted_state'] = {'FXS': actual_fxs, 'MEM': actual_mem, 'created': state['created']}
                count = len(state['created'])
                if count in plan['measurement_after_counts']:
                    report['phase'] = 'measuring_'+str(count); save()
                    m = measure(editor, clock=clock, sleep=sleep)
                    report['measurements'].append({'instances': count, 'measurement': m}); save()
                    if not m['no_reported_faults_in_supplied_observations']:
                        report['stop_reason'] = 'observed processing faults'; break
                editor.advance(); continue
            report['phase'] = 'mutation_intent'; report['next_request'] = state['phase']; save()
            result = editor.next(); report['last_mutation'] = result; save()
            if result['rejected']:
                report['stop_reason'] = 'actual firmware resource/control rejection'; break
        state = editor.state()
        if state['phase'] == 'rejected' and report['last_mutation']['line'].startswith('FXA '):
            # No more additions. Measure only the last complete admitted chain
            # after its actual unchanged FXS readback, then restore the preset.
            count = len(state['created'])
            if count and report['measurements'][-1]['instances'] != count:
                actual_fxs, actual_mem = editor.query('FXS'), editor.query('MEM')
                verify_added_state(actual_fxs, plan, state['created'], timing.protocol.parse_fxt(fxt))
                report['last_admitted_state'] = {'FXS': actual_fxs, 'MEM': actual_mem, 'created': state['created']}
                report['measurements'].append({'instances': count, 'measurement': measure(editor, clock=clock, sleep=sleep)})
        report['phase'] = 'restoration_intent'; save()
        editor.restore()
        report['restored'] = editor.snapshot()
        original.verify_state(report['restored']['state'], prepared['baseline'], gains=prepared['baseline']['gain'], stage='live')
        report['restored_editor_state'] = editor.refresh(prepared['baseline'])
        restored = True
    except Exception as error:
        report['error'] = repr(error); report['failed_phase'] = report.get('phase')
        if installed:
            try:
                status = editor.state()
                # A real successful exchange keeps the connection healthy.
                # Never issue another request after timeout/write uncertainty.
                if status['healthy'] and not status['restoreIssued'] and any(w['mutation'] for w in status['wire']):
                    report['error_restoration'] = editor.restore()
                    report['restored'] = editor.snapshot()
                    original.verify_state(report['restored']['state'], prepared['baseline'], gains=prepared['baseline']['gain'], stage='live')
                    report['restored_editor_state'] = editor.refresh(prepared['baseline'])
                    restored = True
            except Exception as restore_error:
                report['restoration_error'] = repr(restore_error)
    finally:
        if installed:
            try:
                report['guard'] = editor.detach(restored)
                report['temporary_wrapper_removed'] = report['guard']['detached'] is True
                if restored:
                    report['raw_trace_verification'] = verify_trace(report['guard'], prepared['restore_ack_prefix'], prepared['pong'])
                    report['observation_verification'] = verify_observations(report, report['guard'])
                    report['baseline_restoration_verified'] = True
            except Exception as cleanup_error:
                report['cleanup_error'] = repr(cleanup_error)
                report['baseline_restoration_verified'] = False
        report['maximum_admitted_instances_observed'] = len(report.get('last_admitted_state', {}).get('created', []))
        report['global_maximum_chain_proven'] = False
        report['all_catalog_types_enabled'] = False
        report['processing_faults_observed'] = any(not x['measurement']['no_reported_faults_in_supplied_observations']
                                                  for x in report['measurements'])
        report['result'] = 'pass' if report['baseline_restoration_verified'] and not any(report.get(k) for k in ('error', 'cleanup_error')) else 'fail'
        report['phase'] = 'complete' if report['result'] == 'pass' else 'stopped_for_diagnosis'
        save()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true'); parser.add_argument('--execute', action='store_true')
    parser.add_argument('--session', type=Path); parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    require(not (args.check_only and args.execute), 'choose check-only or explicit execute')
    if not args.check_only and not args.execute:
        print(json.dumps({'hardware_io': False, 'browser_access': False, 'inputs_read': False,
                          'capabilities_granted': []})); return 0
    require(args.session is not None, 'owned connected editor session required')
    prepared = prepare(args.session)
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'hardware_io': False, 'browser_access': False, 'prepared': prepared})); return 0
    require(args.output is not None, 'new explicit output directory required')
    output = local(args.output); require(output.is_relative_to(ROOT/'build') and not output.exists(), 'new build output required')
    output.mkdir(parents=True)
    sources = {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in
               (Path(__file__), GUARD, Path(timing.__file__), Path(original.__file__), Path(a2.__file__))}
    def publish(value):
        value['source_sha256'] = sources
        atomic_write_json(output/'report.json', value)
    cdp = CDP(prepared['websocket'])
    try:
        report = experiment(prepared, ExistingEditor(cdp), publish=publish)
    finally:
        cdp.ws.close()  # Only this CDP socket. The owned browser/serial port remain.
    print(json.dumps({k: report.get(k) for k in ('result', 'phase', 'error', 'baseline_restoration_verified', 'temporary_wrapper_removed')}))
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
