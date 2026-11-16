"""Opt-in frozen first-preset trial with the audited A2 STAT activity gate.

Only in-memory snapshot/progress/report adapters differ. The original browser,
native byte recorder, mutation sequence, capability guard and close path remain.
STAT consumes diagnostic peaks/T.max, not configuration, NOR or T.nproc.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import run_mini_v3_editor as bridge
from tools import validate_mini_webserial_v3_close as close_evidence
from tools.mini_host_journal import read_shared_bytes

SOURCE_NAME = Path(__file__).relative_to(ROOT).as_posix()
BRIDGE_SHA = '98b7f8f69cc3bf14fef041281fea5ef9a3a861ee7ffebfcb58d752e789c1204b'
CLOSE_VALIDATOR_SHA = 'c31b85295c1a52d225ab62254aad1f847626b5a6d8078d26111264b526380d6f'
AUDIT = {'path': 'research/mini-a2-activity-audit.json',
         'sha256': '05eeaf855772a68d6cc6f91eb2eabeeff8231cb7bc43dbfaee3bbf5d15e530ae'}
FIXTURE = {'path': 'analysis/hardware/mini-v3-A2-STAT-read-01.json',
           'sha256': 'd989e61a73396bcaa889390c81fc503d8697d78e374a3e7b37978cbe4203ab76'}
FORMATS = {
    'AUD': 'AUD mode=%d in=%u out=%u blk=%u ovr=%u und=%u full=%u pk_in=%u pk_out=%u iis=%d/%d err=%d',
    'DSP': 'DSP rc=%d L=%u C=%u rf=%u fast=%u hw_ok=%u mism=%u hw_to=%u c1_ok=%u c1_to=%u jobs=%u split=%u/%u',
    'T': 'T nproc=%u last=%u max=%u avg=%u ticks; arena=%u tick_ms=%u/%u',
    'STG': 'STG win=%u in=%u/%u pre=%u/%u eng=%u/%u post=%u/%u out=%u/%u blk=%u/%u lat=%u/%u isr=%u/%u',
    'W': 'W espera_c0=%u max=%u split=%u',
    'RS_header': 'RS n=%u veces=%u lat/eng/blk us:',
    'RS_item': ' %u/%u/%u',
    'NIVEL_last': 'NIVEL pk_in=%ld.%ld pk_out=%ld.%ld dBFS clip_in=%u clip_out=%u gain=%d/%d dB lim_n=%u clip_eng=%u',
}
TERMINATOR = r'^NIVEL pk_in=-?\d+\.-?\d+ pk_out=-?\d+\.-?\d+ dBFS clip_in=\d+ clip_out=\d+ gain=-?\d+/-?\d+ dB lim_n=\d+ clip_eng=\d+$'
STAT_QUERY = 'Pedal.cmd("STAT",(l)=>new RegExp('+json.dumps(TERMINATOR)+').test(l)||/^ERR/.test(l),4000)'


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()


def fields(line, name):
    tokens = re.split(r'(%ld|%d|%u)', FORMATS[name])
    kinds = tokens[1::2]
    pattern = ''.join((r'([0-9]+)' if token == '%u' else r'(-?[0-9]+)')
                      if index % 2 else re.escape(token) for index, token in enumerate(tokens))
    match = re.fullmatch(pattern, line)
    require(match is not None, 'malformed STAT '+name+' line')
    values = list(map(int, match.groups()))
    for kind, value in zip(kinds, values):
        require(0 <= value <= 0xffffffff if kind == '%u' else -0x80000000 <= value <= 0x7fffffff,
                'STAT field exceeds its original 32-bit type')
    return values


def parse_stat(lines):
    require(isinstance(lines, list) and 7 <= len(lines) <= 23
            and all(isinstance(line, str) and 0 < len(line) <= 1024 for line in lines),
            'complete bounded STAT response required')
    aud = fields(lines[0], 'AUD'); dsp = fields(lines[1], 'DSP'); timing = fields(lines[2], 'T')
    fields(lines[3], 'STG'); fields(lines[4], 'W')
    count, repeats = fields(lines[5], 'RS_header')
    require(count <= 16 and len(lines) == 7+count, 'STAT RS count/framing differs')
    samples = [fields(line, 'RS_item') for line in lines[6:-1]]
    nivel = fields(lines[-1], 'NIVEL_last')
    return {'nproc': timing[0], 'timing': dict(zip(('nproc','last','max','avg','arena','tick_ms','tick_ms_aux'), timing)),
            'audio_mode': aud[0], 'dsp_rc': dsp[0], 'layers': dsp[1], 'channels': dsp[2],
            'gain': nivel[6:8], 'rs_count': count, 'rs_repeats': repeats, 'rs_samples': samples,
            'lines': list(lines)}


def checked_stat(state):
    value = state.get('a2_stat')
    require(isinstance(value, dict), 'fresh complete STAT observation missing')
    require(parse_stat(value.get('lines')) == value, 'STAT parsed values differ from actual retained reply')
    require(value['audio_mode'] == state['runtime']['mode'] and value['gain'] == state['gain'],
            'STAT and original snapshot mode/gain disagree')
    require(value['layers'] == 23 and value['channels'] == 3,
            'STAT DSP dimensions disagree with the required 23-layer/3-channel A2 model')
    return value


def progress(trial, first, second):
    trial.first_preset_gate(first); trial.first_preset_gate(second)
    trial.verify_state(second, first, gains=first['gain'], stage='live')
    a, b = checked_stat(first), checked_stat(second)
    require(a['nproc'] < b['nproc'], 'A2 T.nproc did not advance; wrap/reset is not inferred')
    before, after = first['runtime']['engine'], second['runtime']['engine']
    generic_progress = all(0 <= before[k] < after[k] <= 0xffffffff for k in ('posts','takes'))
    return {'before': copy.deepcopy(before), 'after': copy.deepcopy(after),
            'A2_nproc_before': a['nproc'], 'A2_nproc_after': b['nproc'], 'A2_nproc_delta': b['nproc']-a['nproc'],
            'A2_completion_progress_observed': True, 'core1_job_progress_observed': generic_progress,
            'generic_job_counters_required': False, 'clip_counters_used_as_samples': False,
            'run_duration_used_as_counter': False, 'physical_audio_output_verified': False}


def description():
    return {'kind': 'audited-A2-STAT-completion-gate-v1', 'audit': dict(AUDIT), 'parser_real_fixture': dict(FIXTURE),
            'replaces': 'generic FXS posts/takes growth prerequisite only',
            'requires': 'two complete ordered STAT replies with increasing uint32 T.nproc plus original A2/safe0/mode2/state gates',
            'STAT_per_original_snapshot': 1, 'STAT_terminator': TERMINATOR,
            'STAT_side_effects': 'consumes diagnostic peaks and T.max; does not reset nproc or modify configuration/NOR',
            'A2_path': 'dedicated dispatch and handshakes, not the generic FXS job mailbox',
            'frozen_files_modified': False, 'mutation_sequence_modified': False, 'capabilities_modified': False,
            'physical_audio_output_verified': False, 'power_cycle_verified': False}


def annotated_writer(original, driver_sha):
    def write(path, value, **kwargs):
        require(value.get('kind') == 'mini-browser-first-preset-v3-trial', 'only a new first-preset trial may be annotated')
        published = copy.deepcopy(value)
        require('A2_gate_extension' not in published, 'existing A2 extension cannot be replaced')
        sources = published.setdefault('source_sha256', {})
        require(SOURCE_NAME not in sources or sources[SOURCE_NAME] == driver_sha, 'A2 driver source pin conflict')
        sources[SOURCE_NAME] = driver_sha
        sources[Path(close_evidence.__file__).relative_to(ROOT).as_posix()] = CLOSE_VALIDATOR_SHA
        published['A2_gate_extension'] = description()
        published['desktop_close_observation'] = copy.deepcopy(
            value.get('prepared',{}).get('context',{}).get('desktop_close_observation'))
        return original(path, published, **kwargs)
    return write


@contextmanager
def activity_adapter(trial):
    old_snapshot, old_progress, old_writer = trial.snapshot, trial.verify_processing_progress, trial.atomic_write_json
    def snapshot(cdp):
        value = old_snapshot(cdp)
        lines = cdp.evaluate(STAT_QUERY)  # One queued original command; no retry.
        value['responses']['STAT'] = lines
        value['state']['a2_stat'] = parse_stat(lines)
        checked_stat(value['state'])
        return value
    trial.snapshot = snapshot
    trial.verify_processing_progress = lambda first, second: progress(trial, first, second)
    trial.atomic_write_json = annotated_writer(old_writer, sha(Path(__file__).read_bytes()))
    try:
        yield
    finally:
        trial.snapshot, trial.verify_processing_progress, trial.atomic_write_json = old_snapshot, old_progress, old_writer


def verify_dependencies():
    require(sha(Path(bridge.__file__).read_bytes()) == BRIDGE_SHA, 'frozen evidence-file adapter changed')
    require(sha(Path(close_evidence.__file__).read_bytes()) == CLOSE_VALIDATOR_SHA, 'close interpretation validator changed')
    for reference in (AUDIT, FIXTURE):
        require(sha(read_shared_bytes(ROOT/reference['path'])) == reference['sha256'], 'A2 evidence pin changed: '+reference['path'])
    audit = json.loads(read_shared_bytes(ROOT/AUDIT['path']))
    require(all(audit['formats'][name]['text'].rstrip('\n') == text for name, text in FORMATS.items()),
            'STAT parser differs from audited original format strings')
    require(audit['STAT_response_contract']['terminator_regex'] == TERMINATOR, 'STAT final-line contract differs')


@contextmanager
def closure_adapter(trial):
    require(trial.evidence is close_evidence.frozen, 'trial must use the same frozen evidence helpers')
    original = trial.evidence.validate_v3_browser_evidence
    trial.evidence.validate_v3_browser_evidence = close_evidence.validate_v3_browser_evidence
    try:
        yield
    finally:
        trial.evidence.validate_v3_browser_evidence = original


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(json.dumps({'device_io':False, 'browser_started':False, 'inputs_read':False,
                          'plan':'Frozen first-preset trial with complete STAT/A2 nproc activity evidence',
                          'automatic_retry':False, 'profile_modified':False})); return 0
    verify_dependencies()
    desktop, trial = bridge.modules('first-preset')
    with bridge.evidence_io_adapter(desktop, trial), closure_adapter(trial), activity_adapter(trial):
        return trial.main(args)


if __name__ == '__main__': raise SystemExit(main())
