"""Validate retained v3 normal-boot/WebSerial read evidence, offline only.

The desktop guard retained decoded lines and completed writes, not native RX
bytes. This module never labels those lines a raw-byte replay and grants no
write family. A mutation trial must collect its own fresh state and raw RX.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re

from tools import launch_mini_desktop_v3 as desktop
from tools import probe_mini_app as readonly
from tools import probe_mini_app_mutation as mutation
from tools.mini_host_journal import read_shared_bytes

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SHA, VERSION = desktop.IMAGE_SHA, desktop.VERSION
LAUNCHER_SHA = '4bb838dd9a18839685ee5211af64ce014ac858975d9b3faca61ffa984a25d754'
require, sha, stamp = desktop.require, desktop.sha, desktop.stamp
REQUIRED_READS = ('PING', 'MODEL', 'MEM', 'LVL', 'FXT', 'FXS', 'PLIST', 'PSTAT', 'SNAPS', 'SNAPNAME', 'CLKSTATE')
QUERY_WORDS = set(('PING STAT MEM MODEL FXT FXS FXMIX FXXO AMPEQ PLIST SNAPS SNAPNAME CLIST ILIST '
    'LVL GEQ HPF SPILL GLIDE SPUR LIM PSTAT STW BLE LIFE CRASH CLKSTATE GAIN BPM PCOLOR').split())


def local_reference(reference):
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
            and isinstance(reference['path'], str)
            and re.fullmatch(r'[a-f0-9]{64}', str(reference['sha256'])), 'exact local path/SHA reference required')
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'evidence leaves the workspace')
    raw = read_shared_bytes(path)
    require(raw and sha(raw) == reference['sha256'], 'retained evidence hash differs: '+reference['path'])
    return path, raw


def is_query(line):
    return isinstance(line, str) and (line in QUERY_WORDS or line == 'AMPEQ info'
                                     or re.fullmatch(r'EVT [0-9]{1,10}', line) is not None)


def finite_time(value):
    return type(value) in (int, float) and 0 <= value < 1e12


def check_guard(guard, *, closed):
    require(isinstance(guard, dict) and guard.get('live') is True and guard.get('appInstalled') is True
            and guard.get('requests') == 1 and guard.get('opens') == 1
            and guard.get('closes') == int(closed) and guard.get('closeError') is None
            and guard.get('fatal') is None and guard.get('pongMatched') is True
            and guard.get('portInfo') == {'vid': readonly.VID, 'pid': readonly.PID}
            and not guard.get('hardwareStubCalls'), 'one real readonly WebSerial guard session required')
    require(guard.get('stopped') is closed, 'guard stop state differs from native-close phase')
    wire = guard.get('wire')
    require(isinstance(wire, list) and 1 <= len(wire) <= 50000 and wire[0].get('line') == 'PING',
            'bounded retained WebSerial writes required')
    for item in wire:
        require(isinstance(item, dict) and is_query(item.get('line')) and type(item.get('completed')) is bool
                and finite_time(item.get('started')), 'non-query or malformed retained WebSerial write')
        if item['completed']:
            require(finite_time(item.get('finished')) and item['finished'] >= item['started'], 'write completion time differs')
    events = guard.get('events')
    require(isinstance(events, list) and all(isinstance(e, dict) and finite_time(e.get('time')) for e in events),
            'bounded guard event times required')
    kinds = [e.get('kind') for e in events]
    for kind in ('serial_request_intent', 'serial_open_intent', 'serial_open_complete'):
        require(kinds.count(kind) == 1, 'one '+kind+' required')
    require(kinds.index('serial_request_intent') < kinds.index('serial_open_intent') < kinds.index('serial_open_complete'),
            'native serial lifecycle order differs')
    if closed:
        require(kinds.count('serial_close_intent') == kinds.count('serial_close_complete') == 1
                and kinds.index('serial_open_complete') < kinds.index('serial_close_intent') < kinds.index('serial_close_complete'),
                'one successful native close required')
    return guard


def retained_replies(guard):
    """Cross-check completed app requests against the guard's decoded input lines."""
    check_guard(guard, closed=False)
    commands, replies = guard.get('commands'), guard.get('replies')
    require(isinstance(commands, list) and len(commands) <= 2000 and guard.get('commandCount') == len(commands)
            and isinstance(replies, list) and len(replies) <= 6000 and guard.get('replyCount') == len(replies)
            and all(isinstance(line, str) and len(line) < 2048 and not re.search(r'[\r\n\0]', line) for line in replies),
            'initial command/decoded-line evidence is absent or truncated')
    answers = {}
    for name in REQUIRED_READS:
        found = [item['lines'] for item in commands if isinstance(item, dict) and item.get('line') == name]
        require(found and any(row.get('line') == name and row.get('completed') is True for row in guard['wire']),
                'required query lacks an actual completed write: '+name)
        lines = found[-1]
        require(isinstance(lines, list) and lines and all(isinstance(line, str) and not line.startswith('ERR') for line in lines),
                'required query has no successful app reply: '+name)
        # A command's lines must occur in order in the retained onLine input.
        cursor = 0
        for line in lines:
            try: cursor = replies.index(line, cursor)+1
            except ValueError: raise ValueError('app reply absent from retained serial lines: '+name) from None
        if name == 'PING':
            require(len(lines) == 1 and readonly.PING.complete(lines[0]), 'PING lacks one complete PONG')
        elif name in readonly.QUERIES:
            require(readonly.QUERIES[name].complete(lines[-1]), 'query terminator missing: '+name)
        else:
            require(len(lines) == 1 and lines[0].startswith(name+' '), 'single-line query framing differs: '+name)
        answers[name] = list(lines)
    return answers


def parse_runtime(answers):
    lvl, clock = answers['LVL'][0], answers['CLKSTATE'][0]
    def integer_field(line, key):
        found = re.findall(r'(?:^| )'+re.escape(key)+r'=(-?\d+)(?= |$)', line)
        require(len(found) == 1, 'missing/ambiguous observed field: '+key)
        return int(found[0])
    gain = re.findall(r'(?:^| )g=(-?\d+)/(-?\d+)(?= |$)', lvl)
    require(len(gain) == 1 and all(-30 <= int(x) <= 12 for x in gain[0]), 'LVL lacks bounded observed gain')
    safe = integer_field(clock, 'safe'); require(safe in (0, 1), 'unknown observed safe mode')
    # Original parseLvl/level UI maps ci/co to clipIn/clipOut. Zero is normal
    # for unclipped or silent audio; these counters do not prove processing.
    clips = {name: integer_field(lvl, name) for name in ('ci', 'co')}
    require(all(value >= 0 for value in clips.values()), 'negative observed clip count')
    plist = readonly.parse_plist(answers['PLIST']); require(plist['ok'], 'incoherent PLIST')
    engine = [line for line in answers['FXS'] if line.startswith('FXS eng=')]
    require(len(engine) <= 1, 'ambiguous engine observation')
    return {'types': mutation.parse_fxt(answers['FXT']), 'fxs': mutation.parse_fxs(answers['FXS']),
        'plist': plist, 'snaps': mutation.parse_snaps(answers['SNAPS']), 'gain': list(map(int, gain[0])),
        'lvl': {'line': lvl, 'mode': integer_field(lvl, 'm'), 'input_clips': clips['ci'], 'output_clips': clips['co']},
        'clock': {'line': clock, 'safe': safe, 'nominal_MHz': integer_field(clock, 'mhz')},
        'engine_lines': engine, 'model_lines': answers['MODEL'],
        'preset_trial_path': 'first-preset-free-slot' if plist['current'] == -1 else 'existing-preset-restore'}


def validate_v3_browser_evidence(*, boot, connected, session):
    """Return exact v3 context from completed local files; never open a device.

    Arguments are path/SHA references to v11's boot result and the new desktop
    directory's connected-proof.json and completed session.json. Current state
    must be read again by the later trial; these are historical observations.
    """
    boot_path, _ = local_reference(boot)
    proof_path, proof_raw = local_reference(connected)
    session_path, session_raw = local_reference(session)
    require(proof_path.name == 'connected-proof.json' and session_path.name == 'session.json'
            and proof_path.parent == session_path.parent, 'connected proof and closed session must be from one desktop run')
    require(sha(Path(desktop.__file__).read_bytes()) == LAUNCHER_SHA, 'frozen v3 launcher changed')
    prepared = desktop.prepare(boot_path, boot['sha256'])
    proof, finished = json.loads(proof_raw), json.loads(session_raw)
    require(finished.get('kind') == 'mini-desktop-readonly-v3-session'
            and finished.get('phase') == 'connected_readonly' and finished.get('finished_utc')
            and finished.get('connected_utc') and finished.get('identity_verified') is True
            and finished.get('first_handshake') is True and finished.get('demo') is False
            and finished.get('mutations_enabled') is False and finished.get('held_recovery_verified') is False
            and finished.get('audio_verified') is False and finished.get('serial_port_closed') is True
            and finished.get('local_server_stopped') is True and finished.get('browser_process_stopped') is True,
            'completed readonly v3 WebSerial session with native close required')
    require(not any(finished.get(key) for key in ('error', 'disconnect_error', 'monitor_error', 'publication_error',
                                                'final_close_observation_error')), 'desktop session has unresolved errors')
    disconnect = finished.get('disconnect', {})
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes') == 1 and disconnect.get('closeError') is None, 'native close is not established')
    require(finished.get('evidence') == prepared and proof.get('inputs') == prepared['inputs'], 'v3 evidence chain differs')
    sources = finished.get('source_sha256')
    require(isinstance(sources, dict) and sources, 'desktop implementation/source hashes required')
    for name, digest in sources.items(): local_reference({'path': name, 'sha256': digest})
    for path in (Path(desktop.__file__), desktop.GUARD, desktop.APP/'tankmini.html'):
        require(sources.get(path.relative_to(ROOT).as_posix()) == sha(path.read_bytes()), 'required desktop source not pinned')
    state = proof.get('state', {})
    require(state.get('ready') is True and state.get('connected') is True and state.get('demo') is False
            and state.get('initialReadsFinished') is True and proof.get('held_recovery_verified') is False
            and proof.get('audio_verified') is False and proof.get('mutations_enabled') is False,
            'connected proof does not record the real readonly editor')
    guard = proof.get('guard'); answers = retained_replies(guard)
    identity = readonly.inspect_pong(answers['PING'][0], VERSION)
    pong = identity['pong']
    require(guard.get('observedPong') == state.get('fw') == pong and finished.get('actual_identity') == identity,
            'actual PONG does not match connected and closed observations')
    final_guard = check_guard(finished.get('last_guard'), closed=True)
    require(final_guard.get('observedPong') == pong and len(final_guard['wire']) >= len(guard['wire'])
            and [x['line'] for x in final_guard['wire'][:len(guard['wire'])]] == [x['line'] for x in guard['wire']],
            'closed guard is not a continuation of the connected proof')
    require(stamp(prepared['evidence']['observed_utc']) <= stamp(finished['started_utc'])
            <= stamp(finished['connected_utc']) <= stamp(proof['observed_utc']) <= stamp(finished['finished_utc']),
            'boot/connected/closed chronology differs')
    runtime = parse_runtime(answers)
    return {'schema': 1, 'kind': 'mini-v3-webserial-read-validation', 'target': 'tank-mini', 'transport': 'usb-cdc',
        'image_sha256': IMAGE_SHA, 'firmware_version': VERSION, 'com': prepared['evidence']['com'],
        'pong': pong, 'profile': copy.deepcopy(prepared['profile']), 'runtime': runtime, 'answers': answers,
        'read_verified': True, 'serial_port_closed': True, 'capabilities_granted': {},
        'observed_utc': proof['observed_utc'], 'closed_utc': finished['finished_utc'],
        'references': {'boot': copy.deepcopy(boot), 'connected': copy.deepcopy(connected), 'session': copy.deepcopy(session),
                       **copy.deepcopy(prepared['inputs'])},
        'evidence_format': 'completed WebSerial writes, decoded onLine replies and original Pedal.cmd results',
        'raw_RX_bytes_retained': False, 'raw_byte_replay_performed': False,
        'current_state_requires_fresh_read': True, 'image_hash_attested_by_device': False,
        'held_recovery_verified': False, 'cold_power_cycle_verified': False, 'audio_verified': False,
        'BLE_verified': False, 'preset_writes_verified': False,
        'COM_binding': 'normal-boot unique CDC observation; UIA chooser attribution is separate',
        'implementation': {'path': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': sha(Path(__file__).read_bytes())}}
