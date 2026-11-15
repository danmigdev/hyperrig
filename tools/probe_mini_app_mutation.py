"""One reversible FXP/FXE experiment on the standalone MINI USB CDC app.

Default/import are offline. Only ``live`` or ``save`` opens a selected port.
The frozen read-only probe supplies framing, logging and terminal transport
errors; its command allowlist is unchanged. No BLE, ROM, NAM, IR, firmware,
arbitrary-command interface is provided here. The separate save experiment
can delete only the new temporary slot that it created and rechecked.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_app as readonly
from tools.build_mini_app import (
    FW_SHA, FW_SOURCE, SOURCE, SOURCE_SHA, checked, command_grants,
    load_profile, local_evidence,
)

Error = readonly.AppProbeError
INT = r'-?(?:0|[1-9]\d*)'
UINT = r'(?:0|[1-9]\d*)'
# These continuous controls are present in the original editor. The small
# experiment excludes the resource-sensitive EQ gains and comp/rotary mix.
CONTINUOUS = {'nivel_db', 'ganancia_db', 'mezcla_pct'}
SUPPORTED_FAMILIES = ('FXP', 'FXE', 'PLOAD', 'PSAVE', 'SNAP', 'SNAPSAVE')


def require(ok, message):
    if not ok:
        raise Error(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def integer(value, low=-(1 << 31), high=(1 << 31)-1):
    require(type(value) is int and low <= value <= high, 'integer outside the bounded protocol domain')
    return value


def source_contract():
    evidence = readonly.source_contract()
    source = checked(SOURCE/'web/tankg.html', SOURCE_SHA).decode('utf-8')
    anchors = ('cmd(line, until, timeout = 1500)', 'function parseFxs(lines)',
               'function fxpRes(type, name)', 'const okv = r.match(/^FXP ok (-?\\d+)/);',
               'Pedal.cmd(`FXE ${id} ${f.inst.on ? 0 : 1}`, "FXE")',
               'Pedal.cmd(`PSAVE ${n} ${name}`, "PSAVE", 8000)')
    require(all(a in source for a in anchors), 'original mutation call sites changed')
    firmware = checked(FW_SOURCE, FW_SHA)
    strings = {0x35a51: b'FXE ok\0', 0x35cd1: b'FXP ok %d\n\0',
               0x35de8: b'PDEL ok %d\n\0', 0x36824: b'SNAPSAVE ok %d preset=%d\n\0',
               0x36b4a: b'SNAP ok %d missing=%d ms=%lu%s\n\0',
               0x3704d: b"PSAVE ok %d '%s' %d blocks capture=%d ir=%d\n\0",
               0x37584: b"PLOAD ok %d '%s' missing=%d capture=%d ir=%d ms=%lu%s%s%s%s\n\0",
               0x39ed1: b'%s cpu=%u/%u ticks (%u%%) mem_fx=%u B\n\0'}
    for offset, value in strings.items():
        require(firmware[offset:offset+len(value)] == value, 'original firmware reply string changed')
    return {**evidence, 'original_firmware_sha256': FW_SHA,
            'reply_strings': {hex(k): v[:-1].decode('ascii') for k, v in strings.items()},
            'mutation_timeout_seconds': 1.5, 'PSAVE_timeout_seconds': 8,
            'transport': 'usb-cdc', 'BLE_qualified': False,
            'live_operations': ['FXP single continuous integer step', 'FXE explicit toggle'],
            'PSAVE_execution_implemented': True,
            'PSAVE_requires': 'separate explicit experiment, free slot, coherent PLIST and matching bank backup',
            'NVM_automatic_writes_excluded': False}


def parse_fxt(lines):
    require(lines and lines[-1] in ('FXT end', 'FXT fin'), 'incomplete FXT')
    types, ids, current = {}, set(), None
    for line in lines[:-1]:
        head = re.fullmatch(r'FXT (\d+) (\S+) cost[o]?=(\d+)((?: [^\s=]+=[^\s]+)*)', line)
        param = re.fullmatch(r'FXT\s+(\d+) (\S+) (-?\d+)\.\.(-?\d+) \((-?\d+)\)', line)
        if head:
            tid, name = int(head[1]), head[2]
            integer(tid, 0, 65535)
            require(tid not in ids and name not in types, 'duplicate FXT type')
            current = {'id': tid, 'name': name, 'params': {}}
            types[name] = current
            ids.add(tid)
        elif param:
            require(current is not None, 'FXT parameter before type')
            index, name, low, high, default = int(param[1]), param[2], *map(int, param.groups()[2:])
            integer(index, 0, 6)
            for value in (low, high, default): integer(value)
            require(low <= default <= high and index not in current['params'], 'invalid FXT limits or duplicate index')
            require(name not in (p['name'] for p in current['params'].values()), 'duplicate FXT parameter name')
            current['params'][index] = {'index': index, 'name': name, 'min': low, 'max': high, 'default': default}
        elif re.fullmatch(r'FXT\s+os tiers=\d+,\d+,\d+(?: cost=\d+,\d+,\d+)?', line) or re.fullmatch(r'FXT\s+pp modes=\d+(?:,\d+)*', line):
            require(current is not None, 'FXT mode metadata before type')
        else:
            raise Error('unrecognized or truncated FXT line: '+line)
    require(types and all(t['params'] for t in types.values()), 'FXT lacks parameter metadata')
    return types


def parse_fxs(lines):
    """Original FXS state, with bounded stricter parsing and dynamic stats apart."""
    require(lines and re.fullmatch(r'FXS (?:peak|pico)=\d+ ticks skipped=\d+', lines[-1]), 'incomplete FXS peak record')
    result = {'blocks': [], 'amp': None, 'mix': [], 'xo': []}
    ids, positions, keys = set(), {'P': 0, 'Q': 0}, set()
    for line in lines[:-1]:
        block = re.fullmatch(r'FX ([PQ])(\d+) id=(\d+) (\S+) on=([01]) p=(-?\d+(?:,-?\d+)*) ticks=(\d+)((?: [^\s=]+=[^\s]+)*)', line)
        amp = re.fullmatch(r'FXS amp=([01])(?: on=([01]))?', line)
        mix = re.fullmatch(r'FXMIX ([PQ]) (\d+) (-?\d+) (-?\d+)', line)
        old_mix = re.fullmatch(r'FXMIX (-?\d+) (-?\d+) (-?\d+) (-?\d+)', line)
        xo = re.fullmatch(r'FXXO ([PQ]) (\d+) (\d+)(?: ([01]))?', line)
        if block:
            bank, pos, bid = block[1], int(block[2]), int(block[3])
            require(pos == positions[bank] and bid not in ids, 'FXS duplicate ID or missing chain position')
            integer(bid, 0, 65535)
            params = [integer(int(v)) for v in block[6].split(',')]
            require(len(params) == 7, 'this M5.71 experiment requires all seven FXS parameter words')
            extra = {}
            for token in block[8].split():
                key, value = token.split('=', 1)
                require(key in ('l', 'g', 'fu', 'irlen', 'mem', 'pcs') and key not in extra,
                        'unknown or duplicate FXS structural field')
                pattern = r'\d+/\d+' if key == 'irlen' else INT if key == 'g' else UINT
                require(re.fullmatch(pattern, value), 'invalid FXS structural field')
                extra[key] = value
            if 'l' in extra: require(extra['l'] in ('0', '1', '2'), 'invalid FXS lane')
            result['blocks'].append({'bank': bank, 'position': pos, 'id': bid, 'type': block[4],
                                     'on': int(block[5]), 'params': params, 'fields': extra})
            ids.add(bid)
            positions[bank] += 1
        elif amp:
            require(result['amp'] is None, 'duplicate FXS amp')
            result['amp'] = {'present': int(amp[1]), 'on': int(amp[2]) if amp[2] is not None else None}
        elif mix or xo:
            found, kind = (mix, 'mix') if mix else (xo, 'xo')
            values = [found[1], *[int(v) if v is not None else None for v in found.groups()[1:]]]
            key = (kind, values[0], values[1])
            require(key not in keys, 'duplicate FXS routing metadata')
            keys.add(key)
            result[kind].append(values)
        elif old_mix:
            require(not result['mix'], 'mixed old/new FXMIX encodings')
            result['mix'] = [['P', 0, int(old_mix[1]), int(old_mix[2])], ['Q', 0, int(old_mix[3]), int(old_mix[4])]]
            keys.update({('mix', 'P', 0), ('mix', 'Q', 0)})
        elif re.fullmatch(r'FXS cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+(?: B)?', line):
            pass  # instantaneous workload is not preset state
        elif re.fullmatch(r'FXS (?:eng|c1|lockq)=.*', line):
            pass  # documented counters, retained verbatim in the backup/trace
        else:
            raise Error('unrecognized or truncated FXS line: '+line)
    require(result['amp'] is not None, 'FXS lacks amp state')
    return result


def parse_snaps(lines):
    require(len(lines) == 1, 'SNAPS must have one complete response')
    match = re.fullmatch(r'SNAPS ([01]{4}) (?:current|actual)=(-?\d+)', lines[0])
    require(match is not None, 'malformed SNAPS')
    current = int(match[2])
    require(-1 <= current <= 3 and (current < 0 or match[1][current] == '1'), 'SNAPS current scene missing')
    return {'present': match[1], 'current': current}


def block_in(snapshot, bid):
    found = [b for b in snapshot['fxs']['blocks'] if b['id'] == bid]
    require(len(found) == 1, 'selected block is absent or ambiguous in actual FXS')
    return found[0]


@dataclass(frozen=True)
class LivePlan:
    operation: str
    block_id: int
    block_type: str
    parameter_index: int | None
    parameter_name: str
    original: int
    requested: int
    before_sha256: str
    request: str
    restore_request: str


def plan_live(snapshot, types, *, block_id, operation='FXP', parameter_index=None, value=None):
    integer(block_id, 0, 65535)
    block = block_in(snapshot, block_id)
    require(block['type'] in types, 'FXS type absent from actual FXT')
    if operation == 'FXP':
        integer(parameter_index, 0, 6)
        params = types[block['type']]['params']
        require(parameter_index in params, 'selected parameter absent from actual FXT')
        param = params[parameter_index]
        name = param['name']
        require(name in CONTINUOUS and not (block['type'] in ('eq', 'geq', 'basseq') and name.endswith('_db'))
                and not (block['type'] in ('comp', 'rotary') and name == 'mezcla_pct'),
                'first experiment excludes routing, memory, mode and resource-sensitive parameters')
        old = block['params'][parameter_index]
        require(param['min'] <= old <= param['max'] and param['min'] < param['max'], 'current value outside FXT limits')
        new = old+1 if old < param['max'] else old-1
        if value is not None: new = integer(value)
        require(param['min'] <= new <= param['max'] and abs(new-old) == 1, 'FXP experiment requires one valid integer step')
        prefix = f'FXP {block_id} {parameter_index}'
    elif operation == 'FXE':
        require(parameter_index is None, 'FXE has no parameter index')
        name, old = 'on', block['on']
        new = 1-old if value is None else integer(value, 0, 1)
        require(new != old, 'FXE experiment must toggle the observed enable state')
        prefix = f'FXE {block_id}'
    else:
        raise Error('only FXP and FXE are implemented for live mutation')
    return LivePlan(operation, block_id, block['type'], parameter_index, name, old, new, digest(snapshot),
                    f'{prefix} {new}', f'{prefix} {old}')


def changed(snapshot, plan, value):
    result = copy.deepcopy(snapshot)
    block = block_in(result, plan.block_id)
    if plan.operation == 'FXP': block['params'][plan.parameter_index] = value
    else: block['on'] = value
    return result


class MutationProbe:
    """Caller-owned transport; construction performs no I/O. One trial per session."""
    def __init__(self, transport, expected_version, *, log=None, clock=time.monotonic):
        self.log = log or (lambda event, **fields: None)
        self.wire = readonly.ReadOnlyProbe(transport, expected_version, log=self.log, clock=clock)
        self.baseline = self.types = self.backup = None
        self.finished = False
        self.result = {'roundtrip_passed': False, 'restoration_verified': False,
                       'mutation_submitted': False, 'automatic_retry': False, 'observations': []}

    def _fail(self, message):
        self.wire.failed = True
        raise Error(message)

    def _query(self, name):
        answer = self.wire.query(name)
        if answer['asynchronous_lines']:
            self._fail('unsolicited activity during the single-owner mutation experiment')
        return answer

    def _snapshot(self):
        answers = {name: self._query(name) for name in ('FXS', 'PLIST', 'SNAPS')}
        return {'fxs': parse_fxs(answers['FXS']['lines']), 'plist': answers['PLIST']['parsed'],
                'snaps': parse_snaps(answers['SNAPS']['lines'])}, answers

    def capture(self):
        require(self.baseline is None and not self.finished, 'baseline already captured')
        self.wire.identify()
        fxt = self._query('FXT')
        self.types = parse_fxt(fxt['lines'])
        self.baseline, answers = self._snapshot()
        self.backup = {'schema': 1, 'kind': 'mini-app-live-state-backup', 'target': 'tank-mini',
                       'firmware_version': self.wire.version, 'identity': self.wire.identity,
                       'state': copy.deepcopy(self.baseline), 'FXT': fxt, 'responses': answers,
                       'full_preset_bank_backup': False,
                       'scope': 'observed FXS plus active preset/scene; excludes hidden DSP history and other preset fields'}
        return copy.deepcopy(self.backup)

    def plan(self, **selection):
        require(self.baseline is not None and not self.finished and not self.wire.failed, 'capture a valid baseline first')
        return plan_live(self.baseline, self.types, **selection)

    def _mutate(self, request, plan):
        answer = self.wire._exchange(readonly.Query(request, 1.5, (plan.operation,)))
        require(len(answer['lines']) == 1 and not answer['asynchronous_lines'], 'ambiguous mutation response')
        line = answer['lines'][0]
        if plan.operation == 'FXP':
            match = re.fullmatch(r'FXP ok ('+INT+r')', line)
            require(match is not None, 'FXP reply lacks its exact effective value')
            actual = integer(int(match[1]))
            limits = self.types[plan.block_type]['params'][plan.parameter_index]
            require(limits['min'] <= actual <= limits['max'], 'FXP effective value is outside observed FXT limits')
        else:
            require(re.fullmatch(r'FXE ok(?: cpu=\d+/\d+ ticks \(\d+%\)(?: mem_fx=\d+ B)?)?', line), 'malformed FXE acknowledgement')
            actual = None  # FXE does not echo its enable state: only FXS proves it.
        self.log('mutation_ack', request=request, effective_value=actual, response=line)
        return actual, answer

    def roundtrip(self, plan):
        require(isinstance(plan, LivePlan) and self.baseline is not None and not self.finished and not self.wire.failed,
                'one prepared live trial required')
        expected_plan = self.plan(block_id=plan.block_id, operation=plan.operation,
                                  parameter_index=plan.parameter_index, value=plan.requested)
        require(plan == expected_plan, 'plan differs from captured FXS/FXT')
        self.result.update(plan=asdict(plan), phase='preflight')
        try:
            current, _ = self._snapshot()
            require(current == self.baseline, 'preset, scene or chain changed before mutation')
            self.result.update(phase='apply', mutation_submitted=True, restore_request=plan.restore_request)
            actual, reply = self._mutate(plan.request, plan)
            observed, _ = self._snapshot()
            if plan.operation == 'FXE': actual = block_in(observed, plan.block_id)['on']
            require(observed == changed(self.baseline, plan, actual), 'readback differs from ACK or unrelated state changed; no blind restoration')
            applied = actual == plan.requested
            self.result['observations'].append({'request': plan.request, 'ack_verified': applied,
                'readback_verified': applied, 'ack': reply['lines'][0], 'effective_value': actual,
                'state_sha256': digest(observed)})
            self.result.update(phase='restore', observed_after_apply=observed)
            restored_value, reply = self._mutate(plan.restore_request, plan)
            restored, _ = self._snapshot()
            require((plan.operation != 'FXP' or restored_value == plan.original) and restored == self.baseline,
                    'original observed state was not restored; no retry')
            self.result['observations'].append({'request': plan.restore_request, 'ack_verified': True,
                'readback_verified': True, 'ack': reply['lines'][0], 'effective_value': plan.original,
                'state_sha256': digest(restored)})
            self.result.update(phase='complete', restoration_verified=True, roundtrip_passed=applied,
                               observed_after_restore=restored)
            if not applied:
                self.result['error'] = 'firmware effective value differed from the request; restored, no capability qualified'
            return copy.deepcopy(self.result)
        except Exception as exc:
            self.wire.failed = True
            self.result.update(error=str(exc), failed_phase=self.result['phase'], phase='failed')
            self.log('mutation_trial_failed', **self.result)
            raise
        finally:
            self.finished = True


EXTRA_READS = ('GAIN', 'AMPEQ', 'BPM', 'PCOLOR', 'STW', 'MODEL', 'SNAPNAME')


def parse_extra(answers):
    def one(name, pattern):
        lines = answers[name]['lines']
        require(len(lines) == 1, name+' must have one response')
        match = re.fullmatch(pattern, lines[0])
        require(match is not None, 'unrecognized '+name+' response')
        return match
    gain = one('GAIN', r'GAIN in=(-?\d+) out=(-?\d+) dB')
    tone = one('AMPEQ', r'AMPEQ volume=(-?\d+) bass=(-?\d+) mid=(-?\d+) treble=(-?\d+) presence=(-?\d+) drive=(-?\d+)')
    bpm = one('BPM', r'BPM (\d+)\.(\d)')
    color = one('PCOLOR', r'PCOLOR (none|[0-9a-f]{6}) preset=(-?\d+)')
    stereo = one('STW', r'STW w=(\d+) cur=\d+ live=\d+ cpu=\d+/\d+ deg=\d+')
    model = answers['MODEL']['lines']
    require(len(model) == 1 and model[0].startswith('MODEL '), 'invalid MODEL response')
    names = ['']*4
    seen = set()
    require(answers['SNAPNAME']['lines'][-1:] == ['SNAPNAME end'], 'SNAPNAME incomplete')
    for line in answers['SNAPNAME']['lines'][:-1]:
        match = re.fullmatch(r"SNAPNAME ([0-3]) '(.*)'", line)
        require(match is not None and int(match[1]) not in seen, 'invalid or duplicate scene name')
        seen.add(int(match[1])); names[int(match[1])] = match[2]
    return {'gain_db': list(map(int, gain.groups())), 'tone': list(map(int, tone.groups())),
            'bpm10': int(bpm[1])*10+int(bpm[2]), 'color': None if color[1] == 'none' else color[1],
            'color_preset': int(color[2]), 'stereo_width': int(stereo[1]), 'model': model[0], 'scene_names': names}


def logical_fxs(fxs):
    result = copy.deepcopy(fxs)
    for block in result['blocks']:
        block.pop('id')  # PLOAD can allocate new runtime IDs.
        for name in ('mem', 'pcs', 'fu'): block['fields'].pop(name, None)
    return result


def sound_equal(left, right):
    a, b = copy.deepcopy(left), copy.deepcopy(right)
    a.pop('plist'); b.pop('plist')
    a['fxs'], b['fxs'] = logical_fxs(a['fxs']), logical_fxs(b['fxs'])
    a['extra'].pop('color_preset'); b['extra'].pop('color_preset')
    return a == b


def validate_saved_baseline(snapshot, types, bank):
    """The first save trial begins from a represented saved preset/scene.

    Reject unrepresented live edits before PSAVE: loading the original slot
    must be a complete restoration route, not a guess about hidden settings.
    The minimal trial supports a serial chain without an external cab IR.
    """
    current = snapshot['plist']['current']
    listed = snapshot['plist']['presets']
    require(current >= 0, 'persistent trial needs a saved current preset')
    index = next(i for i,p in enumerate(listed) if p['slot'] == current)
    sound = bank['presets'][index]['sound']
    require(sound.get('cab_ir') is None, 'first persistence trial excludes external cab IR references')
    require(snapshot['extra']['color_preset'] == current, 'PCOLOR preset disagrees with PLIST')
    scenes = sound.get('scenes')
    require(isinstance(scenes, list), 'bank backup lacks scenes')
    by_scene = {}
    for scene in scenes:
        require(isinstance(scene, dict) and type(scene.get('index')) is int and 0 <= scene['index'] <= 3
                and scene['index'] not in by_scene, 'invalid scene in backup')
        by_scene[scene['index']] = scene
    require(snapshot['snaps']['present'] == ''.join('1' if i in by_scene else '0' for i in range(4)), 'scene inventory differs from backup')
    active = snapshot['snaps']['current']
    require((active >= 0 and active in by_scene) or (active == -1 and not scenes),
            'cannot restore a no-scene selection while saved scenes exist')
    scene = by_scene.get(active)
    require(snapshot['extra']['scene_names'] == [by_scene.get(i, {}).get('name', '') for i in range(4)],
            'scene names differ from backup')
    bank_name, pos, expected_blocks = 'P', 0, []
    amp_markers = 0
    for entry in sound['chain']:
        require(isinstance(entry, dict), 'invalid backup chain')
        if entry.get('amp') is True:
            amp_markers += 1; bank_name, pos = 'Q', 0
            continue
        require('split' not in entry and entry.get('type') != 'ir', 'first persistence trial requires a serial chain without IR blocks')
        require(entry.get('type') in types and isinstance(entry.get('params'), dict)
                and isinstance(entry.get('id'), str), 'backup lacks effect metadata')
        effective = scene.get('blocks', {}).get(entry['id']) if scene else entry
        require(isinstance(effective, dict) and type(effective.get('on')) is bool
                and isinstance(effective.get('params'), dict), 'backup scene lacks effect state')
        params = [0]*7
        for param in types[entry['type']]['params'].values():
            value = effective['params'].get(param['name'])
            integer(value, param['min'], param['max']); params[param['index']] = value
        expected_blocks.append((bank_name, pos, entry['type'], int(effective['on']), params))
        pos += 1
    require(amp_markers == 1, 'backup needs one amp boundary')
    observed = [(b['bank'], b['position'], b['type'], b['on'], b['params']) for b in snapshot['fxs']['blocks']]
    require(observed == expected_blocks and not snapshot['fxs']['mix'] and not snapshot['fxs']['xo']
            and all(b['fields'].get('l', '0') == '0' for b in snapshot['fxs']['blocks']),
            'live chain/values differ from the backed-up saved preset/scene')
    amp = sound.get('amp', {})
    expected_amp = {'present': int(bool(amp.get('present'))),
                    'on': int(bool(scene.get('amp_on'))) if scene else int(bool(amp.get('on')))}
    require(snapshot['fxs']['amp'] == expected_amp, 'amp state differs from backup')
    gain = (scene or sound).get('gain_db', {})
    require(snapshot['extra']['gain_db'] == [gain.get('in'), gain.get('out')], 'live gains differ from backup')
    tone = scene.get('amp_tone') if scene else amp.get('tone')
    require(isinstance(tone, dict) and snapshot['extra']['tone'] == [tone.get(k) for k in ('volume','bass','mid','treble','presence','drive')],
            'live amp tone differs from backup')
    expected_color = sound.get('color')
    require(expected_color is None or isinstance(expected_color, str), 'invalid backup color')
    require(snapshot['extra']['bpm10'] == sound.get('tempo_bpm_x10')
            and snapshot['extra']['color'] == (expected_color.lstrip('#') if expected_color else None),
            'tempo/color differ from backup')
    require(type(sound.get('stereo')) is bool and snapshot['extra']['stereo_width'] == (100 if sound['stereo'] else 0),
            'stereo state differs from backup')
    capture = amp.get('capture')
    if amp.get('present'):
        require(isinstance(capture, dict) and snapshot['extra']['model'].startswith("MODEL '"+str(capture.get('name'))+"' "),
                'loaded capture name differs from backup')


class PresetMutationProbe(MutationProbe):
    """Separate PSAVE/PLOAD/cleanup trial; no persistent command in live mode."""
    def _snapshot(self):
        state, answers = super()._snapshot()
        extra = {}
        for name in EXTRA_READS:
            if name in readonly.QUERIES:
                extra[name] = self._query(name)
            else:
                extra[name] = self.wire._exchange(readonly.Query(name, 1.5, (name,)))
                require(not extra[name]['asynchronous_lines'], 'unsolicited activity during preset capture')
        state['extra'] = parse_extra(extra)
        require(state['extra']['color_preset'] == state['plist']['current'], 'active preset changed during capture')
        answers.update(extra)
        return state, answers

    def _ack(self, request, pattern, timeout=1.5):
        verb = request.split()[0]
        answer = self.wire._exchange(readonly.Query(request, timeout, (verb,)))
        require(len(answer['lines']) == 1 and not answer['asynchronous_lines'], 'ambiguous '+verb+' response')
        match = re.fullmatch(pattern, answer['lines'][0])
        require(match is not None, 'unexpected '+verb+' acknowledgement; no retry')
        return answer['lines'][0], match

    def _observe(self, request, ack, state, *, persistent=False):
        self.result['observations'].append({'request': request, 'ack': ack, 'ack_verified': True,
            'readback_verified': True, 'persistence_readback_verified': persistent, 'state_sha256': digest(state)})

    def _assert_listing(self, state, created=None):
        baseline = self.baseline['plist']['presets']
        entries = state['plist']['presets']
        require([e for e in entries if created is None or e['slot'] != created['slot']] == baseline,
                'preexisting preset inventory changed')
        if created is not None:
            require([e for e in entries if e['slot'] == created['slot']] == [created], 'temporary slot identity changed')

    def _load(self, slot, name, scene, created, *, expected_state=None):
        expected_state = self.baseline if expected_state is None else expected_state
        request = f'PLOAD {slot}'
        ack, match = self._ack(request, rf"PLOAD ok {slot} '{re.escape(name)}' missing=0 capture=(-?\d+) ir=(-?\d+) ms=\d+", 8)
        state, _ = self._snapshot()
        self._assert_listing(state, created)
        require(state['plist']['current'] == slot, 'PLOAD current slot differs')
        if scene >= 0:
            snap_request = f'SNAP {scene}'
            snap_ack, _ = self._ack(snap_request, rf'SNAP ok {scene} missing=0 ms=\d+')
            state, _ = self._snapshot()
            self._assert_listing(state, created)
            require(state['plist']['current'] == slot and state['snaps']['current'] == scene,
                    'SNAP did not restore the selected scene')
            require(sound_equal(state, expected_state), 'loaded scene/values differ from expected state')
            self._observe(snap_request, snap_ack, state)
        require(sound_equal(state, expected_state), 'loaded preset/values differ from expected state')
        self._observe(request, ack, state)
        return state, tuple(map(int, match.groups()))

    def save_roundtrip(self, *, slot, bank_backup, marker_plan):
        require(self.baseline is not None and not self.finished and not self.wire.failed, 'one captured persistent trial required')
        plan = plan_save_free_slot(self.baseline, slot=slot, name='HyperRig_Test', bank_backup=bank_backup)
        bank = json.loads(local_evidence(bank_backup, 'bank backup'))
        validate_saved_baseline(self.baseline, self.types, bank)
        require(marker_plan == self.plan(block_id=marker_plan.block_id, operation=marker_plan.operation,
                parameter_index=marker_plan.parameter_index, value=marker_plan.requested), 'marker differs from initial FXS')
        self.result.update(plan={'operation': 'PSAVE', 'request': plan['request'], 'before_sha256': digest(self.baseline)},
                           phase='preflight', temporary_slot=slot, temporary_slot_created=False,
                           temporary_slot_deleted=False, bank_backup=copy.deepcopy(bank_backup))
        created = None
        try:
            current, _ = self._snapshot()
            require(current == self.baseline, 'state changed before PSAVE')
            self.result.update(phase='save', mutation_submitted=True)
            ack, match = self._ack(plan['request'], rf"PSAVE ok {slot} 'HyperRig_Test' (\d+) blocks capture=(-?\d+) ir=(-?\d+)", 8)
            require(int(match[1]) == len(self.baseline['fxs']['blocks']), 'PSAVE block count differs')
            saved, _ = self._snapshot()
            require(saved['plist']['current'] == slot and sound_equal(saved, self.baseline), 'PSAVE changed the observed sound/scene')
            extra = [p for p in saved['plist']['presets'] if p['slot'] == slot]
            require(len(extra) == 1 and extra[0]['name'] == 'HyperRig_Test' and extra[0]['blocks'] == int(match[1]), 'PSAVE slot missing or inconsistent in PLIST')
            created = extra[0]
            self._assert_listing(saved, created)
            self.result.update(temporary_slot_created=True, created_entry=copy.deepcopy(created), phase='persistence_marker')
            actual, reply = self._mutate(marker_plan.request, marker_plan)
            marked, _ = self._snapshot()
            require(marked == changed(saved, marker_plan, marker_plan.requested)
                    and (marker_plan.operation != 'FXP' or actual == marker_plan.requested), 'persistence marker readback differs')
            self._observe(marker_plan.request, reply['lines'][0], marked)
            self.result['phase'] = 'reload_saved'
            loaded, references = self._load(slot, 'HyperRig_Test', self.baseline['snaps']['current'], created)
            require(references == (int(match[2]), int(match[3])), 'saved capture/IR references differ after PLOAD')
            self._observe(plan['request'], ack, loaded, persistent=True)
            self.result.update(persistence_readback_verified=True, phase='save_snapshot_zero')
            # Qualify the original editor's mandatory scene-A step separately.
            # PSAVE has already been reloaded, so SNAPSAVE cannot mask a failed
            # PSAVE persistence result. Only the newly created slot is changed.
            snap_request = 'SNAPSAVE 0'
            snap_ack, _ = self._ack(snap_request, rf'SNAPSAVE ok 0 preset={slot}')
            snap_saved, _ = self._snapshot()
            expected_saved = copy.deepcopy(loaded)
            expected_saved['snaps'] = {'present': '1'+loaded['snaps']['present'][1:], 'current': 0}
            created = {**created, 'snapshots': created['snapshots'] | 1}
            expected_saved['plist']['presets'] = [created if p['slot'] == slot else p for p in expected_saved['plist']['presets']]
            require(snap_saved == expected_saved, 'SNAPSAVE changed unrelated state or did not select scene zero')
            self._assert_listing(snap_saved, created)
            old_block = block_in(self.baseline, marker_plan.block_id)
            live_block = next(b for b in snap_saved['fxs']['blocks']
                              if (b['bank'], b['position']) == (old_block['bank'], old_block['position']))
            second_marker = plan_live(snap_saved, self.types, block_id=live_block['id'],
                operation=marker_plan.operation, parameter_index=marker_plan.parameter_index, value=marker_plan.requested)
            self.result['phase'] = 'snapshot_persistence_marker'
            effective, reply = self._mutate(second_marker.request, second_marker)
            marked_scene, _ = self._snapshot()
            require(marked_scene == changed(snap_saved, second_marker, second_marker.requested)
                    and (second_marker.operation != 'FXP' or effective == second_marker.requested),
                    'snapshot persistence marker readback differs')
            self._observe(second_marker.request, reply['lines'][0], marked_scene)
            self.result['phase'] = 'reload_snapshot_zero'
            reloaded_scene, _ = self._load(slot, 'HyperRig_Test', 0, created, expected_state=snap_saved)
            self._observe(snap_request, snap_ack, reloaded_scene, persistent=True)
            self.result.update(snapshot_persistence_readback_verified=True, phase='restore_original')
            original_slot = self.baseline['plist']['current']
            original_name = next(p['name'] for p in self.baseline['plist']['presets'] if p['slot'] == original_slot)
            restored, _ = self._load(original_slot, original_name, self.baseline['snaps']['current'], created)
            self.result['original_sound_restored'] = True
            # A new full read must still identify exactly the slot created by
            # this trial. No caller-supplied PDEL or preexisting slot can enter.
            self.result['phase'] = 'cleanup'
            fresh, _ = self._snapshot()
            require(fresh == restored and sound_equal(fresh, self.baseline), 'state changed before temporary-slot cleanup')
            self._assert_listing(fresh, created)
            require(slot != original_slot and all(p['slot'] != slot for p in self.baseline['plist']['presets']),
                    'refusing deletion of a preexisting slot')
            delete_request = f'PDEL {slot}'
            delete_ack, _ = self._ack(delete_request, rf'PDEL ok {slot}')
            final, _ = self._snapshot()
            require(final['plist'] == self.baseline['plist'] and sound_equal(final, self.baseline), 'final PLIST/sound/scene differs after cleanup')
            self._observe(delete_request, delete_ack, final, persistent=True)
            self.result.update(phase='complete', temporary_slot_deleted=True, restoration_verified=True,
                               roundtrip_passed=True, observed_after_restore=final)
            return copy.deepcopy(self.result)
        except Exception as exc:
            self.wire.failed = True
            self.result.update(error=str(exc), failed_phase=self.result['phase'], phase='failed')
            self.log('preset_trial_failed', **self.result)
            raise
        finally:
            self.finished = True


def file_reference(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'evidence must be a retained file inside the workspace')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def command_evidence(result, profile, *, trace, backup, hardware_executed=False):
    require(result.get('roundtrip_passed') is True and result.get('restoration_verified') is True,
            'only a verified apply/readback/restore/readback trial qualifies exact requests')
    local_evidence(trace, 'command trace')
    retained = json.loads(local_evidence(backup, 'state backup'))
    require(retained.get('kind') == 'mini-app-live-state-backup'
            and retained.get('image_sha256') == profile['image_sha256']
            and retained.get('firmware_version') == profile['firmware_version']
            and digest(retained['state']) == result['plan']['before_sha256'], 'backup does not bind the observed initial state')
    # Helpers remain in the trial. The legacy exact-request adapter includes
    # the editor's PSAVE + SNAPSAVE pair, not deletion or its load helpers.
    verb = result['plan']['operation']
    selected = ('PSAVE', 'SNAPSAVE') if verb == 'PSAVE' else (verb,)
    observations = [copy.deepcopy(o) for o in result['observations'] if o['request'].split()[0] in selected]
    if verb == 'PSAVE':
        local_evidence(result.get('bank_backup'), 'persistent trial bank backup')
        require(result.get('persistence_readback_verified') is True
                and result.get('snapshot_persistence_readback_verified') is True and result.get('temporary_slot_deleted') is True,
                'PSAVE evidence requires reload and confirmed temporary-slot cleanup')
    grants = command_grants({command: [o['request'] for o in observations if o['request'].split()[0] == command]
                             for command in selected})
    exercised = {}
    representative = []
    for observation in result['observations']:
        family = observation['request'].split()[0]
        if family in SUPPORTED_FAMILIES:
            exercised.setdefault(family, set()).add(observation['request'])
            representative.append(copy.deepcopy(observation))
    exercised = {k: sorted(v) for k,v in sorted(exercised.items())}
    return {'schema': 1, 'kind': 'mini-app-command-validation', 'target': 'tank-mini',
            'firmware_version': profile['firmware_version'], 'image_sha256': profile['image_sha256'],
            'hardware_executed': hardware_executed is True, 'transport': 'usb-cdc',
            'editor_source_sha256': SOURCE_SHA, 'verified_requests': grants,
            'trace': trace, 'backup': backup, 'restoration_verified': True, 'observations': observations,
            'all_required_editor_mutations_verified': False, 'BLE_verified': False,
            'evidence_model': 'representative-families-v1',
            'supported_by_protocol': list(SUPPORTED_FAMILIES),
            'physically_exercised_requests': exercised if hardware_executed is True else {},
            'simulated_requests': exercised if hardware_executed is not True else {},
            'representative_observations': representative,
            'every_value_physically_tested': False,
            'protocol_binding': {'dialect': 'ultrarig-ascii-v1', 'editor_sha256': SOURCE_SHA,
                                 'original_firmware_sha256': FW_SHA},
            'image_hash_attested_by_device': False, 'trial': copy.deepcopy(result),
            'bank_backup': result.get('bank_backup'),
            'limits': ['Exact wire requests only; no range or other block/scene is qualified.',
                       'Restoration covers observed FXS/preset/scene, not DSP history or all hidden state.',
                       'No protocol lock prevents external changes between the observed snapshots.',
                       'No absence of automatic NOR writes, audio quality or power-cycle retention is established.']}


def plan_save_free_slot(snapshot, *, slot, name, bank_backup):
    """Offline proposal only. A bank file is checked, not assumed to be a NOR image.

    PSAVE changes the active preset. Its ACK/PLIST alone cannot establish reload
    or restoration. PresetMutationProbe executes the separate complete trial;
    no save, load or delete command is sent by this planner.
    """
    integer(slot, 0, 31)
    require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9 _.-]{1,23}', name)
            and name == name.strip(), 'use a bounded ASCII preset name')
    plist = snapshot['plist']
    require(plist.get('ok') is True and not plist.get('bad'), 'coherent complete PLIST required')
    require(slot not in [p['slot'] for p in plist['presets']], 'PSAVE destination is occupied')
    bank = json.loads(local_evidence(bank_backup, 'pre-save bank backup'))
    require(bank.get('format') in ('ultrarig-preset', 'hyperrig-preset') and bank.get('version') == 1
            and bank.get('kind') == 'bank' and isinstance(bank.get('presets'), list), 'original-format preset bank backup required')
    presets = bank['presets']
    require(len(presets) == len(plist['presets']) and all(isinstance(p, dict) and isinstance(p.get('sound'), dict)
            and isinstance(p['sound'].get('chain'), list) for p in presets), 'backup does not cover the listed bank')
    require([p.get('meta', {}).get('name') for p in presets] == [p['name'] for p in plist['presets']],
            'backup order/names differ from current PLIST')
    return {'request': f'PSAVE {slot} {name}', 'timeout_seconds': 8, 'slot_free_in_captured_PLIST': True,
            'bank_backup': copy.deepcopy(bank_backup), 'backup_structure_checked': True,
            'backup_content_attested_by_device': False, 'snapshot_sha256': digest(snapshot),
            'execution_implemented': True, 'executor': 'PresetMutationProbe.save_roundtrip',
            'verified_requests': {}, 'restoration_verified': False,
            'requires': ['fresh unchanged PLIST immediately before an explicit save',
                         'ACK slot/name and new PLIST plus FXS',
                         'separate qualified reload and restoration of preset, scene and live state'],
            'preexisting_slot_deletion_available': False, 'cleanup': 'only the new slot owned by the explicit trial'}


def run_live(args, *, enumerate_fn=None, open_fn=None, clock=time.monotonic):
    contract = source_contract()
    profile = load_profile(args.firmware_manifest)
    require(profile['capabilities']['read'] and profile['hardware_verified'],
            'live qualification requires the already boot-verified candidate manifest with read capability')
    paths = [Path(p).resolve() for p in (args.log, args.backup, args.report)]
    require(len(set(paths)) == 3 and all(p.is_relative_to(ROOT) and p.parent.is_dir() and not p.exists() for p in paths),
            'three distinct new trace/backup/report files inside the workspace are required')
    integer(args.block, 0, 65535)
    if args.operation == 'FXP': integer(args.parameter, 0, 6)
    else: require(args.parameter is None, 'FXE has no parameter index')
    if args.value is not None: integer(args.value)
    persistent = getattr(args, 'action', 'live') == 'save'
    bank_reference = None
    if persistent:
        integer(args.slot, 0, 31)
        bank_reference = {'path': args.bank_backup, 'sha256': args.bank_sha256}
        local_evidence(bank_reference, 'bank backup')
    transport = probe = None
    journal = readonly.Journal(paths[0], clock)
    summary = {'roundtrip_passed': False, 'restoration_verified': False, 'automatic_retry': False}
    hardware = open_fn is None  # injected transports never produce hardware evidence
    try:
        journal('mutation_start', expected_image_sha256=profile['image_sha256'],
                image_hash_attested_by_device=False, protocol=contract, hardware_executed=hardware)
        selected = readonly.select_port((enumerate_fn or readonly.enumerate_ports)(), args.port)
        transport = (open_fn or readonly.SerialTransport.open)(selected['device'])
        probe_class = PresetMutationProbe if persistent else MutationProbe
        probe = probe_class(transport, profile['firmware_version'], log=journal, clock=clock)
        backup = probe.capture()
        backup.update(image_sha256=profile['image_sha256'], transport='usb-cdc', hardware_executed=hardware)
        with paths[1].open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(backup, stream, indent=2); stream.write('\n'); stream.flush()
        plan = probe.plan(block_id=args.block, operation=args.operation, parameter_index=args.parameter, value=args.value)
        journal('live_plan', **asdict(plan))
        summary = probe.save_roundtrip(slot=args.slot, bank_backup=bank_reference, marker_plan=plan) if persistent else probe.roundtrip(plan)
        journal('mutation_complete', **summary)
    except Exception as exc:
        summary = copy.deepcopy(probe.result) if probe else summary
        summary['error'] = str(exc)
        journal('mutation_failed', **summary)
    finally:
        try:
            if transport is not None:
                try:
                    transport.close()
                    journal('port_closed')
                except Exception as exc:
                    summary.update(roundtrip_passed=False, close_error=str(exc))
                    journal('port_close_failed', error=str(exc))
        finally:
            journal.close()
    hardware = hardware and probe is not None and probe.wire.identity is not None
    report = command_evidence(summary, profile, trace=file_reference(paths[0]), backup=file_reference(paths[1]),
                              hardware_executed=hardware) if summary.get('roundtrip_passed') else {
        'schema': 1, 'kind': 'mini-app-mutation-incomplete', 'target': 'tank-mini', 'transport': 'usb-cdc',
        'hardware_executed': hardware, 'verified_requests': {}, 'trial': summary,
        'trace': file_reference(paths[0]), 'backup': file_reference(paths[1]) if paths[1].exists() else None,
        'restoration_verified': summary.get('restoration_verified', False)}
    with paths[2].open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action')
    sub.add_parser('plan', help='show the offline original-protocol contract')
    for action, help_text in (('live', 'one live mutation/readback/restoration'),
                              ('save', 'separate PSAVE/reload/restore/temporary-slot-cleanup trial')):
        command = sub.add_parser(action, help=help_text+' on a boot-verified USB candidate')
        command.add_argument('--port', required=True)
        command.add_argument('--firmware-manifest', type=Path, required=True)
        for name in ('log', 'backup', 'report'): command.add_argument('--'+name, type=Path, required=True)
        command.add_argument('--operation', choices=('FXP', 'FXE'), default='FXP')
        command.add_argument('--block', type=int, required=True)
        command.add_argument('--parameter', type=int)
        command.add_argument('--value', type=int)
        if action == 'save':
            command.add_argument('--slot', type=int, required=True)
            command.add_argument('--bank-backup', required=True, help='original-format bank JSON retained inside workspace')
            command.add_argument('--bank-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.action in (None, 'plan'):
            result = {'device_io': False, 'enumerated': False, 'contract': source_contract(),
                      'sequence': ['PING', 'FXT + FXS + PLIST + SNAPS; retain backup',
                                   'fresh FXS + PLIST + SNAPS must match', 'one FXP or FXE + ACK',
                                   'FXS + PLIST + SNAPS readback', 'restore original + ACK',
                                   'FXS + PLIST + SNAPS must match the initial state'],
                      'PSAVE': 'separate explicit save subcommand; HyperRig_Test on a verified free slot only',
                      'all_required_editor_mutations_verified': False}
        else:
            result = run_live(args)
        print(json.dumps(result, indent=2))
        return 0 if args.action in (None, 'plan') or result.get('kind') == 'mini-app-command-validation' else 1
    except (Error, ValueError, OSError, KeyError) as exc:
        print(json.dumps({'error': str(exc), 'automatic_retry': False}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
