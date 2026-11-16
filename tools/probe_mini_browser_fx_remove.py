"""One explicit temporary-effect removal on an already connected USB editor.

Default/check-only never access a browser or device. The five mutations are
GAIN0/-12, FXA boost, FXP its actual ID to-1, FXR that ID, and one PLOAD0.
No preset save/delete, serial open/close, retry or general app-family grant.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_browser_latency as bench
from tools.mini_host_journal import atomic_write_json

BENCH_SHA = 'a80460f4dacdc2ca4c496b79ed58699e0074cbd7ddc50b1cf639a4cd57b43a37'
GUARD = ROOT/'tools/mini_browser_fx_remove_guard.js'
require, original, timing = bench.require, bench.original, bench.timing
PLAN = {'kind': 'mini-exact-FXR-removal-plan-v1', 'executed': False,
        'setup_requests': ['GAIN 0 -12'],
        'steps': [{'type': 'boost', 'bank': 'Q', 'add_request': 'FXA Q 99 boost'}],
        'restore_request': 'PLOAD 0'}


def prepare(session_path):
    require(bench.digest(Path(bench.__file__).read_bytes()) == BENCH_SHA,
            'reviewed baseline/session helper differs')
    prepared = bench.prepare(session_path)
    require(prepared['baseline']['gain'] == [0, 0], 'this exact removal trial requires saved gain0/0')
    prepared['kind'] = 'mini-exact-FXR-removal-preparation-v1'
    prepared['plan'] = copy.deepcopy(PLAN)
    prepared['prior_detached_latency_guard_allowed'] = True
    return prepared


class ExistingEditor(bench.ExistingEditor):
    def install(self, prepared):
        value = self.cdp.evaluate("({origin:location.origin,connected:S.connected,demo:DEMO,fw:S.fw,profile:HyperRigMini.profile,transport:Pedal.tr===SerialTransport})")
        require(value == {'origin': prepared['origin'], 'connected': True, 'demo': False,
                          'fw': prepared['pong'], 'profile': prepared['profile'], 'transport': True},
                'live owned page/identity/profile differs')
        self.cdp.evaluate('(async()=>{await Pedal.chain;return Pedal.busy;})()')
        config = {k: prepared[k] for k in ('profile', 'pong', 'restore_ack_prefix')}
        self.cdp.evaluate(GUARD.read_text('utf8')+'\ninstallMiniFXRemovalGuard('+json.dumps(config)+')')

    def prime(self): self.cdp.evaluate('__miniFXRemovalGuard.prime()')
    def state(self): return self.cdp.evaluate('__miniFXRemovalGuard.state')
    def configure(self): self.cdp.evaluate('__miniFXRemovalGuard.configure('+json.dumps(PLAN)+')')
    def next(self): return self.cdp.evaluate('__miniFXRemovalGuard.executeNext()')
    def remove(self):
        self.cdp.evaluate('__miniFXRemovalGuard.remove()')
        return self.next()
    def restore(self):
        self.cdp.evaluate('__miniFXRemovalGuard.restore()')
        return self.next()
    def detach(self, restored):
        return self.cdp.evaluate('__miniFXRemovalGuard.detach('+json.dumps(restored)+')')


def check_catalog(rows):
    types = timing.protocol.parse_fxt(rows)
    require('boost' in types and set(types['boost']['params']) == {0}, 'original one-parameter boost required')
    p = types['boost']['params'][0]
    require(p['name'] == 'ganancia_db' and p['min'] <= -1 <= p['max'] and p['default'] == 6,
            'fresh boost range/default differs')
    return types


def verify_added(added, before, instance_id):
    actual = added['state']; blocks = actual['fxs']['blocks']
    require(type(instance_id) is int and 0 <= instance_id < 16 and len(blocks) == 1,
            'one actual temporary effect ID required')
    b = blocks[0]
    require(b['id'] == instance_id and b['type'] == 'boost' and b['bank'] == 'Q' and b['position'] == 0
            and b['on'] == 1 and b['params'] == [-1, 0, 0, 0, 0, 0, 0],
            'temporary boost identity/enable/effective parameter differs')
    expected = copy.deepcopy(before)
    expected['fxs']['blocks'] = copy.deepcopy(blocks)
    original.verify_state(actual, expected, gains=[0, -12], stage='live')


def verify_trace(guard, prepared):
    require(guard.get('detached') is True and guard.get('healthy') is True and not guard.get('fatal')
            and guard.get('restoreIssued') is True and guard.get('phase') == 'restored_ack',
            'healthy detached trial with actual restoration required')
    commands, wire, rx = guard['commands'], guard['wire'], guard['rx']
    require(len(commands) == len(wire) <= 2000 and rx, 'complete bounded native trace required')
    require([w['id'] for w in wire] == list(range(len(wire)))
            and [c['id'] for c in commands] == list(range(len(commands))), 'nonunique wire/command IDs')
    priming = []
    for w, c in zip(wire, commands):
        require(w['command_id'] == c['id'] and c['wire_id'] == w['id'] and c['line'] == w['line']
                and w['completed'] is True and c['completed'] is True
                and w['hex'] == (w['line']+'\n').encode('ascii').hex(), 'native full-write/command binding differs')
        require(w['mutation'] == (not original.evidence.is_query(w['line'])), 'query/mutation binding differs')
        if c['priming']:
            require(not w['mutation'], 'mutation cannot use the priming exception')
            priming.append(w['line']); continue
        require(c['native_RX_verified'] is True, 'native reply unverified')
        raw = b''.join(bytes.fromhex(r['hex']) for r in rx if w['seq'] < r['seq'] < c['completed_seq'])
        lines = raw.decode('utf8', 'strict').replace('\r\n', '\n').splitlines(); cursor = 0
        for line in c['lines']:
            require(line in lines[cursor:], 'reply absent from native RX: '+w['line'])
            cursor = lines.index(line, cursor)+1
    pongs = [c for c in commands if c['line'] == 'PING' and not c['priming']]
    require(pongs and all(c['lines'] == [prepared['pong']] for c in pongs), 'fresh native PONG differs')
    plans = [event['plan'] for event in guard['events'] if event['kind'] == 'plan']
    require(plans == [PLAN], 'one exact removal plan required')
    mutations = [c for w, c in zip(wire, commands) if w['mutation']]
    require(len(mutations) == guard['mutations'] == 5, 'exactly five native mutations required')
    add = mutations[1]['lines']
    match = re.fullmatch(r'FXA id=(\d+) boost', add[0]) if len(add) == 2 else None
    require(match is not None and 0 <= int(match[1]) < 16
            and re.fullmatch(r'FX cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+ B', add[1]), 'actual FXA ACK differs')
    instance_id = int(match[1])
    expected = ['GAIN 0 -12', 'FXA Q 99 boost', f'FXP {instance_id} 0 -1', f'FXR {instance_id}', 'PLOAD 0']
    require([c['line'] for c in mutations] == expected and [c['epoch'] for c in mutations] == list(range(5)),
            'actual mutation order/ID/epoch differs; no replay or other mutation allowed')
    require(mutations[0]['lines'] == ['GAIN in=0 out=-12 dB']
            and mutations[2]['lines'] == ['FXP ok -1'], 'actual GAIN/FXP ACK differs')
    require(len(mutations[3]['lines']) == 1 and re.fullmatch(
        r'FXR ok cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+ B', mutations[3]['lines'][0]), 'actual FXR resource ACK differs')
    require(len(mutations[4]['lines']) == 1 and re.fullmatch(re.escape(prepared['restore_ack_prefix'])+
        r' missing=0 capture=0 ir=0 ms=\d+', mutations[4]['lines'][0]), 'actual PLOAD0 loader-status ACK differs')
    return {'temporary_instance_id': instance_id, 'native_RX_bytes': sum(len(bytes.fromhex(r['hex'])) for r in rx),
            'wire_commands': len(wire), 'actual_mutation_requests': expected,
            'reader_hook_priming_queries_not_claimed_as_raw_RX_proof': priming,
            'no_save_delete_firmware_or_repeated_mutation': True}


def verify_report(report, prepared=None):
    """Pure replay: real native replies, all four snapshots, and actual temporary ID."""
    prepared = report['prepared'] if prepared is None else prepared
    require(prepared == report['prepared'] and prepared['plan'] == PLAN, 'prepared evidence differs')
    proof = verify_trace(report['guard'], prepared)
    require(report['temporary_instance_id'] == proof['temporary_instance_id'], 'reported actual ID differs')
    commands = report['guard']['commands']; cursor = 0; matched = []

    def consume(line, rows, epoch):
        nonlocal cursor
        for index in range(cursor, len(commands)):
            c = commands[index]
            if c['line'] == line and c.get('completed') and not c.get('priming') and c['lines'] == rows:
                require(c['epoch'] == epoch, 'snapshot/query crosses its actual mutation epoch')
                cursor = index+1; matched.append(c['id']); return
        raise ValueError('snapshot absent from chronological native trace: '+line)

    for name, epoch in (('before', 0), ('added', 3), ('removed', 4), ('restored', 5)):
        value = report[name]
        require(original.parse_snapshot(value['responses']) == value['state'], 'snapshot parser result differs')
        for key in original.READS: consume(key, value['responses'][key], epoch)
        if name == 'before':
            consume('FXT', report['actual_catalog'], 0); check_catalog(report['actual_catalog'])
        if name in ('added', 'removed'): consume('MEM', report[name+'_memory'], epoch)
    baseline = prepared['baseline']
    require(baseline['gain'] == [0, 0] and not baseline['fxs']['blocks'], 'exact empty saved baseline required')
    original.verify_state(report['before']['state'], baseline, gains=[0, 0], stage='live')
    verify_added(report['added'], report['before']['state'], proof['temporary_instance_id'])
    original.verify_state(report['removed']['state'], baseline, gains=[0, -12], stage='live')
    original.verify_state(report['restored']['state'], baseline, gains=[0, 0], stage='live')
    ui = report['restored_editor_state']
    require(ui['gain'] == [0, 0] and ui['chain'] == {'P': [], 'Q': []} and ui['model'] == 'A2'
            and ui['capture'] == ui['scene'] == ui['preset'] == ui['firmwarePreset'] == 0
            and ui['scenes'] == [1, 0, 0, 0] and ui['amp'] == ui['ampPresent'] == 1,
            'original UI readback not restored')
    return {**proof, 'observations_bound_to_native_commands': True, 'snapshot_command_ids': matched,
            'temporary_effect_added_then_removed': True, 'saved_baseline_restored': True,
            'general_family_grants': [], 'effect_removal_UI_physically_exercised': False}


def experiment(prepared, editor, *, publish=lambda value: None):
    report = {'kind': 'mini-exact-FXR-removal-trial-v1', 'prepared': prepared, 'result': 'running',
              'hardware_executed': False, 'temporary_effect_removal_verified': False,
              'baseline_restoration_verified': False, 'temporary_wrapper_removed': False,
              'automatic_retry': False, 'serial_open_performed': False, 'serial_close_performed': False,
              'preset_save_or_delete_performed': False, 'audio_quality_verified': False,
              'general_family_grants': [], 'effect_removal_UI_physically_exercised': False}
    installed = restored = False
    def save():
        if installed:
            try:
                report['guard'] = editor.state()
                if report['guard'].get('wire'): report['hardware_executed'] = True
            except Exception as error: report['guard_observation_error'] = repr(error)
        publish(copy.deepcopy(report))
    try:
        editor.install(prepared); installed = True
        report['phase'] = 'priming'; report['hardware_executed'] = None; save(); editor.prime()
        require(editor.query('PING') == [prepared['pong']], 'fresh native PONG differs')
        report['before'] = editor.snapshot()
        original.verify_state(report['before']['state'], prepared['baseline'], gains=[0, 0], stage='live')
        report['actual_catalog'] = editor.query('FXT'); check_catalog(report['actual_catalog'])
        editor.configure()
        for phase in ('attenuate', 'add', 'configure'):
            require(editor.state()['phase'] == phase, 'unexpected exact mutation phase')
            report['phase'] = phase+'_intent'; save()
            reply = editor.next(); report['last_mutation'] = reply; save()
            require(not reply['rejected'], 'actual firmware rejected temporary effect step')
        report['temporary_instance_id'] = editor.state()['created'][0]['id']
        report['added'] = editor.snapshot(); report['added_memory'] = editor.query('MEM')
        verify_added(report['added'], report['before']['state'], report['temporary_instance_id'])
        report['phase'] = 'remove_intent'; save(); report['last_mutation'] = editor.remove(); save()
        require(not report['last_mutation']['rejected'], 'actual firmware rejected removal')
        report['removed'] = editor.snapshot(); report['removed_memory'] = editor.query('MEM')
        original.verify_state(report['removed']['state'], prepared['baseline'], gains=[0, -12], stage='live')
        report['phase'] = 'restoration_intent'; save(); editor.restore()
        report['restored'] = editor.snapshot()
        original.verify_state(report['restored']['state'], prepared['baseline'], gains=[0, 0], stage='live')
        report['restored_editor_state'] = editor.refresh(prepared['baseline']); restored = True
    except Exception as error:
        report['error'] = repr(error); report['failed_phase'] = report.get('phase')
        if installed:
            try:
                state = editor.state()
                if state['healthy'] and not state['restoreIssued'] and any(w['mutation'] for w in state['wire']):
                    report['error_restoration'] = editor.restore(); report['restored'] = editor.snapshot()
                    original.verify_state(report['restored']['state'], prepared['baseline'], gains=[0, 0], stage='live')
                    report['restored_editor_state'] = editor.refresh(prepared['baseline']); restored = True
            except Exception as restore_error: report['restoration_error'] = repr(restore_error)
    finally:
        if installed:
            try:
                report['guard'] = editor.detach(restored)
                report['temporary_wrapper_removed'] = report['guard']['detached'] is True
                if restored and not report.get('error'):
                    report['verification'] = verify_report(report)
                    report['temporary_effect_removal_verified'] = report['baseline_restoration_verified'] = True
            except Exception as error: report['cleanup_error'] = repr(error)
        report['result'] = 'pass' if report['temporary_effect_removal_verified'] and not report.get('cleanup_error') else 'fail'
        report['phase'] = 'complete' if report['result'] == 'pass' else 'stopped_for_diagnosis'
        save()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true'); parser.add_argument('--execute', action='store_true')
    parser.add_argument('--session', type=Path); parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    require(not (args.check_only and args.execute), 'choose check-only or execute')
    if not args.check_only and not args.execute:
        print(json.dumps({'hardware_io': False, 'browser_access': False, 'capabilities_granted': []})); return 0
    require(args.session is not None, 'owned connected editor session required')
    prepared = prepare(args.session)
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'hardware_io': False, 'browser_access': False, 'prepared': prepared})); return 0
    require(args.output is not None, 'new explicit build directory required')
    output = bench.local(args.output)
    require(output.is_relative_to(ROOT/'build') and not output.exists(), 'new build output required')
    output.mkdir(parents=True)
    sources = {p.relative_to(ROOT).as_posix(): bench.digest(p.read_bytes()) for p in
               (Path(__file__), GUARD, Path(bench.__file__), Path(original.__file__), Path(timing.__file__))}
    def publish(value):
        value['source_sha256'] = sources; atomic_write_json(output/'report.json', value)
    cdp = bench.CDP(prepared['websocket'])
    try: report = experiment(prepared, ExistingEditor(cdp), publish=publish)
    finally: cdp.ws.close()  # Only this observer socket; the original editor/serial session remains.
    print(json.dumps({k: report.get(k) for k in ('result', 'phase', 'error', 'cleanup_error',
          'temporary_effect_removal_verified', 'baseline_restoration_verified', 'temporary_wrapper_removed')}))
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
