"""Bounded offline analysis and exact planning from retained MINI replies.

No serial, USB, browser, clock, sleep or hardware execution is provided. The
caller owns real reply provenance and the save/reload restoration experiment.
Plans never grant application capabilities and never establish analog latency.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_app_mutation as protocol
from tools import run_mini_v3_first_preset_a2 as a2
from tools.mini_host_journal import read_shared_bytes

MAX_SAMPLES, MAX_ELAPSED_MS, MAX_INSTANCES, MAX_PER_BANK = 12, 20000, 16, 10
STAGES = ('in', 'pre', 'eng', 'post', 'out', 'blk', 'lat', 'isr')
ORDER = ('gate', 'comp', 'eq', 'boost', 'overdrive', 'hum', 'envfilter',
         'tremolo', 'chorus', 'flanger', 'phaser', 'vibrato', 'delay',
         'doubler', 'reverb2', 'pitchpro')
P_BANK_TYPES = frozenset(ORDER[:7])
PROTOCOL_SHA = 'b8c4f7bba180c756e951a45a3be49b95f44e68553870cc47cf41538c40b18e20'
A2_PARSER_SHA = 'c234aa9d36f9b0c95e71a692881f81342773d6e237766f1a2d1ed49df65ac2ab'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def lines(value, *, maximum=400):
    require(isinstance(value, list) and 0 < len(value) <= maximum
            and all(isinstance(x, str) and 0 < len(x) <= 4096
                    and all(32 <= ord(c) <= 126 for c in x) for x in value),
            'bounded complete ASCII reply lines required')
    return value


def integer_field(line, key):
    found = re.findall(r'(?:^| )'+re.escape(key)+r'=(-?\d+)(?= |$)', line)
    require(len(found) == 1, 'missing or duplicate field: '+key)
    return int(found[0])


def resources(fxs, mem):
    protocol.parse_fxs(lines(fxs))
    cpu = [re.fullmatch(r'FXS cpu=(\d+)/(\d+) ticks \(\d+%\) mem_fx=(\d+) B', s)
           for s in fxs if s.startswith('FXS cpu=')]
    require(len(cpu) == 1 and cpu[0] is not None, 'one complete FXS CPU/memory line required')
    mem = lines(mem, maximum=1)[0]
    require(mem.startswith('MEM heap='), 'complete MEM response required')
    used, limit, fx_bytes = map(int, cpu[0].groups())
    result = {'cost_ticks': used, 'budget_ticks': limit, 'effects_bytes': fx_bytes,
              **{k: integer_field(mem, k) for k in ('fxcap', 'pool_largest', 'pool_used', 'pool_bad')}}
    require(limit > 0 and all(v >= 0 for v in result.values()), 'invalid observed resource bounds')
    return result


def context(reply):
    require(isinstance(reply, dict), 'retained state replies required')
    fxs = protocol.parse_fxs(lines(reply['FXS']))
    clock = lines(reply['CLKSTATE'], maximum=1)[0]
    require(clock.startswith('CLKSTATE ') and integer_field(clock, 'safe') == 0, 'safe0 CLKSTATE required')
    mhz = integer_field(clock, 'mhz')
    require(0 < mhz <= 2147, 'positive bounded nominal clock required')
    gain_line = lines(reply['GAIN'], maximum=1)[0]
    gain = re.fullmatch(r'GAIN in=(-?\d+) out=(-?\d+) dB', gain_line)
    require(gain is not None and all(-30 <= int(x) <= 12 for x in gain.groups()), 'bounded GAIN reply required')
    model = lines(reply['MODEL'], maximum=1)[0]
    require(re.fullmatch(r"MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=-?\d+(?:\.\d+)?", model),
            'this measurement requires the current 23-layer/3-channel A2 path')
    configuration = copy.deepcopy(fxs)
    for block in configuration['blocks']:
        # Placement and allocated-piece count are observations, not controls.
        for name in ('mem', 'pcs'):
            block['fields'].pop(name, None)
    return {'configuration': configuration, 'nominal_MHz': mhz,
            'gain': list(map(int, gain.groups())), 'model': model,
            'resources': resources(reply['FXS'], reply['MEM']),
            'raw': copy.deepcopy(reply)}


def stat(lines_value):
    raw = lines(lines_value, maximum=23)
    parsed = a2.parse_stat(raw)
    aud = a2.fields(raw[0], 'AUD'); dsp = a2.fields(raw[1], 'DSP')
    stg = a2.fields(raw[3], 'STG'); nivel = a2.fields(raw[-1], 'NIVEL_last')
    parsed['AUD'] = dict(zip(('mode', 'in', 'out', 'blk', 'ovr', 'und', 'full',
                             'pk_in', 'pk_out', 'iis0', 'iis1', 'err'), aud))
    parsed['DSP'] = dict(zip(('rc', 'L', 'C', 'rf', 'fast', 'hw_ok', 'mism', 'hw_to',
                             'c1_ok', 'c1_to', 'jobs', 'split0', 'split1'), dsp))
    parsed['STG'] = {'window': stg[0], 'stages': {
        name: {'avg_ticks': stg[1+2*i], 'max_ticks': stg[2+2*i]} for i, name in enumerate(STAGES)}}
    parsed['clips'] = {'input': nivel[4], 'output': nivel[5], 'limiter': nivel[8], 'engine': nivel[9]}
    require(all(0 <= pair['avg_ticks'] <= pair['max_ticks'] for pair in parsed['STG']['stages'].values()),
            'STG average exceeds its maximum')
    return parsed


def _delta(first, last, keys):
    out = {}
    for key in keys:
        require(0 <= first[key] <= last[key] <= 0xffffffff,
                'counter regressed; wrap/reset is not inferred: '+key)
        out[key] = last[key]-first[key]
    return out


def _fx_counters(fxs):
    result = {}
    for prefix, keys in (('FXS c1=', ('jobs', 'to', 'skip')),
                         ('FXS eng=', ('posts', 'takes', 'canc')),
                         ('FXS peak=', ('skipped',))):
        found = [x for x in fxs if x.startswith(prefix)]
        require(len(found) == 1, 'one complete FX counter record required: '+prefix)
        for key in keys:
            result[key] = integer_field(found[0], key)
    return result


def analyze_measurement(bundle):
    """Analyze at most 12 supplied STAT replies spanning at most 20 seconds.

    The first sample is the settling origin. Only windows at least two newer
    than it are eligible, with three distinct windows needed for completion.
    No local-file analysis authenticates a hardware transcript by itself.
    """
    require(isinstance(bundle, dict), 'measurement bundle required')
    before, after = context(bundle['before']), context(bundle['after'])
    for key in ('configuration', 'nominal_MHz', 'gain', 'model'):
        require(before[key] == after[key], 'configuration changed across measurement: '+key)
    samples = bundle['samples']
    require(isinstance(samples, list) and 2 <= len(samples) <= MAX_SAMPLES, 'need 2..12 bounded STAT samples')
    parsed, elapsed = [], []
    for sample in samples:
        t = sample['elapsed_ms']
        require(type(t) in (int, float) and math.isfinite(t) and 0 <= t <= MAX_ELAPSED_MS,
                'elapsed time must be finite and within 20 seconds')
        require(not elapsed or t > elapsed[-1], 'sample times must strictly advance')
        elapsed.append(t)
        s = stat(sample['lines'])
        require(s['audio_mode'] == 2 and (s['layers'], s['channels']) == (23, 3)
                and s['gain'] == before['gain'], 'STAT mode/model/gain changed')
        require(not parsed or s['STG']['window'] >= parsed[-1]['STG']['window'],
                'STG window regressed; wrap/reset is not inferred')
        require(not parsed or s['nproc'] > parsed[-1]['nproc'], 'fresh A2 completion progress required')
        if parsed and s['STG']['window'] == parsed[-1]['STG']['window']:
            # isr uses a different window and may legitimately advance.
            require(all(s['STG']['stages'][k] == parsed[-1]['STG']['stages'][k] for k in STAGES[:-1]),
                    'same STG window changed contents; torn/racing observation')
        if parsed:
            _delta(parsed[-1]['AUD'], s['AUD'], ('in', 'out', 'blk', 'ovr', 'und', 'full'))
            _delta(parsed[-1]['DSP'], s['DSP'], ('hw_ok', 'mism', 'hw_to', 'c1_ok', 'c1_to', 'jobs'))
        parsed.append(s)
    ticks_per_ms = before['nominal_MHz']*1000//6
    first, last = parsed[0], parsed[-1]
    minimum_window = first['STG']['window']+2
    chosen, seen = [], set()
    for sample in parsed:
        w = sample['STG']['window']
        if w >= minimum_window and w not in seen:
            chosen.append({'window': w, 'stages': {
                k: {**v, 'avg_ms_nominal': v['avg_ticks']/ticks_per_ms,
                    'max_ms_nominal': v['max_ticks']/ticks_per_ms}
                for k, v in sample['STG']['stages'].items()}})
            seen.add(w)
    aud_delta = _delta(first['AUD'], last['AUD'], ('in', 'out', 'blk', 'ovr', 'und', 'full'))
    dsp_delta = _delta(first['DSP'], last['DSP'], ('hw_ok', 'mism', 'hw_to', 'c1_ok', 'c1_to', 'jobs'))
    fx_delta = _delta(_fx_counters(before['raw']['FXS']), _fx_counters(after['raw']['FXS']),
                      ('jobs', 'to', 'skip', 'posts', 'takes', 'canc', 'skipped'))
    faults = {f'AUD.{k}': v for k, v in aud_delta.items() if k in ('ovr', 'und', 'full') and v}
    faults.update({f'DSP.{k}': v for k, v in dsp_delta.items() if k in ('mism', 'hw_to', 'c1_to') and v})
    faults.update({f'FXS.{k}': v for k, v in fx_delta.items() if k in ('to', 'skip', 'canc', 'skipped') and v})
    statuses = {'AUD.err': [s['AUD']['err'] for s in parsed], 'DSP.rc': [s['DSP']['rc'] for s in parsed]}
    return {'kind': 'mini-retained-internal-timing-v1', 'hardware_io': False,
            'hardware_transcript_authenticated_by_this_module': False, 'analog_latency_measured': False,
            'capabilities_granted': [], 'configuration_readback_consistent': True,
            'nominal_MHz': before['nominal_MHz'], 'ticks_per_ms_nominal': ticks_per_ms,
            'timer_physically_calibrated': False, 'sample_count': len(parsed), 'elapsed_ms': elapsed[-1]-elapsed[0],
            'settling_origin_window': first['STG']['window'], 'minimum_eligible_window': minimum_window,
            'eligible_windows': chosen, 'measurement_complete': len(chosen) >= 3,
            'STG_window_list': [s['STG']['window'] for s in parsed],
            'A2_nproc_delta': last['nproc']-first['nproc'], 'AUD_counter_delta': aud_delta,
            'DSP_counter_delta': dsp_delta, 'FXS_counter_delta': fx_delta, 'nonzero_fault_counter_deltas': faults,
            'observed_status_values': statuses, 'observed_clipping': [s['clips'] for s in parsed],
            'no_reported_faults_in_supplied_observations': not faults and all(v == 0 for vs in statuses.values() for v in vs),
            'RS_used_for_measurement': False, 'RS_identical': all(s['rs_samples'] == first['rs_samples'] for s in parsed),
            'before': before, 'after': after, 'raw_samples': copy.deepcopy(samples)}


def plan_stress(fxt, fxs, mem, gain):
    """Plan one finite ordered chain; actual admission/readback remains required.

    This plan contains no execution code. Each symbolic instance must be bound
    from its real FXA acknowledgement before formatting any FXP/FXE request.
    """
    types = protocol.parse_fxt(lines(fxt))
    state, budget = protocol.parse_fxs(lines(fxs)), resources(fxs, mem)
    gain_match = re.fullmatch(r'GAIN in=(-?\d+) out=(-?\d+) dB', lines(gain, maximum=1)[0])
    require(gain_match and all(-30 <= int(x) <= 12 for x in gain_match.groups()), 'fresh bounded GAIN required')
    input_gain, output_gain = map(int, gain_match.groups())
    trial_output_gain = min(output_gain, -12)
    require(not state['blocks'] and state['amp'] == {'present': 1, 'on': 1},
            'this gradual plan starts from the saved A2-only baseline')
    estimates = {}
    for row in fxt:
        m = re.fullmatch(r'FXT (\d+) (\w+) cost=(\d+) cat=\w+ mem=(\d+)(?: .*)?', row)
        if m:
            estimates[m[2]] = {'ticks': int(m[3]), 'bytes': int(m[4])}
    require(all(name in types and name in estimates for name in ORDER), 'required types/ranges missing from real FXT')
    cost, memory, counts, steps, skipped = budget['cost_ticks'], budget['effects_bytes'], {'P': 0, 'Q': 0}, [], []
    for name in ORDER:
        estimate = estimates[name]; bank = 'P' if name in P_BANK_TYPES else 'Q'
        reason = ('instance limit' if len(steps) >= MAX_INSTANCES or counts[bank] >= MAX_PER_BANK else
                  'published CPU estimate' if cost+estimate['ticks'] > budget['budget_ticks'] else
                  'published memory estimate' if memory+estimate['bytes'] > budget['fxcap']
                  or estimate['bytes'] > budget['pool_largest'] else None)
        if reason:
            skipped.append({'type': name, 'reason': reason}); continue
        targets = []
        for index, p in types[name]['params'].items():
            value = p['default']
            if p['name'] in ('nivel_db', 'ganancia_db'):
                value = min(value, 0)
                if name == 'boost' and p['name'] == 'ganancia_db':
                    value = -1  # Exercise a non-unity control without adding level.
            elif name == 'eq' and p['name'] in ('graves_db', 'medios_db', 'agudos_db'):
                value = -3  # Zero EQ bands may skip processing in the original.
            elif p['name'] == 'mezcla_pct':
                value = min(value, 25)
            elif p['name'] == 'umbral_db' and name == 'gate':
                value = p['min']
            elif p['name'] == 'realim_pct' and name == 'delay':
                value = min(value, 20)
            require(p['min'] <= value <= p['max'], 'planned conservative value outside actual FXT')
            if value != p['default']:
                targets.append({'index': index, 'name': p['name'], 'value': value, 'default': p['default'],
                                'min': p['min'], 'max': p['max']})
        cost += estimate['ticks']; memory += estimate['bytes']; counts[bank] += 1
        steps.append({'number': len(steps)+1, 'type': name, 'bank': bank,
                      'add_request': f'FXA {bank} 99 {name}', 'add_terminal': 'FX cpu= or ERR FXA',
                      'ack_prefix': 'FXA id=', 'new_instance_only': True,
                      'configure_after_actual_id': [{'request_template': 'FXE {id} 0'},
                        *[{'request_template': f"FXP {{id}} {p['index']} {p['value']}", 'parameter': p} for p in targets],
                        {'request_template': 'FXE {id} 1'}],
                      'published_cumulative_ticks': cost, 'published_cumulative_bytes': memory,
                      'requires_actual_FXS_and_MEM_readback': True})
    return {'kind': 'mini-exact-FX-stress-plan-v1', 'executed': False, 'hardware_io': False,
            'capabilities_granted': [], 'not_a_proof_of_admission': True,
            'prerequisite': 'actual baseline PSAVE/SNAPSAVE/PLOAD 0 save/reload proof, retained sound snapshot',
            'setup_requests': [] if output_gain == trial_output_gain else [f'GAIN {input_gain} {trial_output_gain}'],
            'baseline_gain': [input_gain, output_gain], 'trial_gain': [input_gain, trial_output_gain],
            'restore_request': 'PLOAD 0', 'save_or_delete_during_stress': False,
            'steps': steps, 'skipped': skipped, 'resources_observed': budget,
            'measurement_after_counts': sorted(set([n for n in (4, 8, 12) if n <= len(steps)]+[len(steps)])),
            'stop_on_rejection': True, 'automatic_retry': False,
            'level_policy': 'FXA starts enabled at defaults, so first attenuate output to at most -12dB. Then disable each new instance: positive makeup to0dB, boost -1dB, EQ bands -3dB, wet mix at most25%, gate threshold minimum, delay feedback at most20%; retain other defaults. Restore saved gain with PLOAD0 and verify. This is not a promise against clipping or worst-case cost for every input.',
            'limits': {'instances': MAX_INSTANCES, 'per_bank': MAX_PER_BANK, 'STAT_samples': MAX_SAMPLES,
                       'measurement_ms': MAX_ELAPSED_MS}, 'actual_catalog': list(fxt)}


def verify_sources():
    for module, expected in ((protocol, PROTOCOL_SHA), (a2, A2_PARSER_SHA)):
        require(hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() == expected,
                'frozen parser source changed: '+module.__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('analyze', 'plan'))
    parser.add_argument('input', type=Path, help='retained replies JSON, never a device path')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    verify_sources()
    raw = read_shared_bytes(args.input)
    value = json.loads(raw)
    result = analyze_measurement(value) if args.operation == 'analyze' else plan_stress(value['FXT'], value['FXS'], value['MEM'], value['GAIN'])
    result['input_file'] = {'path': args.input.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    rendered = json.dumps(result, indent=2, ensure_ascii=False)+'\n'
    if args.output:
        require(args.output.resolve() != args.input.resolve(), 'input evidence may not be overwritten')
        args.output.write_text(rendered, encoding='utf-8')
    else:
        print(rendered, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
