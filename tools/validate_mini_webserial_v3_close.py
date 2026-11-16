"""Offline v3 context validator for one proved post-native-close CDP race.

Reuses every frozen parser/check. The retained session is never rewritten or
sanitized: its exact final observation error and close request remain evidence.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_mini_webserial_v3 as frozen

ROOT, desktop, readonly = frozen.ROOT, frozen.desktop, frozen.readonly
require, sha, stamp = frozen.require, frozen.sha, frozen.stamp
FROZEN_SHA = '4d01fe626e0d55a02e34a7fbe5b80d192caea57e8e53a2a27ec13a24c7a280c1'
EXACT_POST_CLOSE_ERROR = "WebSocketConnectionClosedException('Connection to remote host was lost.')"
OTHER_ERRORS = ('error','disconnect_error','monitor_error','publication_error')


def classify_post_close(finished, session_path, final_guard):
    """Called only after identity, sources, native close and chronology pass."""
    require(not any(finished.get(key) for key in OTHER_ERRORS), 'desktop session has unresolved errors')
    error = finished.get('final_close_observation_error')
    if not error: return None
    require(error == EXACT_POST_CLOSE_ERROR, 'unrecognized final close observation error')
    require(finished['source_sha256'].get('tools/launch_mini_desktop_v3.py') == frozen.LAUNCHER_SHA,
            'post-close classification applies only to the frozen v3 launcher')
    frozen.check_guard(final_guard, closed=True)
    disconnect = finished.get('disconnect', {})
    require(finished.get('serial_port_closed') is True and disconnect.get('native_close_verified') is True
            and disconnect.get('open') is False and disconnect.get('closes') == 1 and disconnect.get('closeError') is None
            and finished.get('browser_process_stopped') is True and finished.get('local_server_stopped') is True,
            'post-close observation cannot establish an unobserved native close')
    events = final_guard['events']
    require(events and all(a['time'] <= b['time'] for a,b in zip(events,events[1:])),
            'native lifecycle timestamps out of order')
    stopped = [e for e in events if e.get('kind') == 'guard_stopped']
    complete = next(e for e in events if e.get('kind') == 'serial_close_complete')
    intent = next(e for e in events if e.get('kind') == 'serial_close_intent')
    require(len(stopped) == 1 and events[-1] == stopped[0]
            and intent['time'] <= complete['time'] <= stopped[0]['time'], 'native close must precede the final stopped guard')
    require(all(row['started'] <= intent['time'] and
                (not row['completed'] or row['finished'] <= complete['time']) for row in final_guard['wire']),
            'serial write observed after native closure began')
    request_path = session_path.parent/'close.request'
    require(request_path.is_file(), 'retained local close request missing')
    raw = frozen.read_shared_bytes(request_path, maximum=128)
    text = raw.decode('ascii',errors='strict')
    require(text.endswith('\n') and len(text.splitlines()) == 1, 'one retained local close request required')
    requested = text.strip()
    require(stamp(finished['connected_utc']) <= stamp(requested) <= stamp(finished['close_requested_utc'])
            <= stamp(finished['finished_utc']), 'close request and completed session chronology differs')
    return {'classification': 'redundant-CDP-observation-after-observed-native-close',
            'original_error': error, 'original_report_preserved': True, 'native_close_inferred_from_CDP_loss': False,
            'close_request': {'path': request_path.relative_to(ROOT).as_posix(), 'sha256': sha(raw), 'requested_utc': requested},
            'close_requested_utc': finished['close_requested_utc'],
            'native_close_complete_browser_time': complete['time'], 'guard_stopped_browser_time': stopped[0]['time'],
            'launcher': {'path':'tools/launch_mini_desktop_v3.py','sha256':frozen.LAUNCHER_SHA},
            'source_order': 'close.request branch observes native close and stopped guard before Browser.close; finally redundantly observes CDP'}


def validate_v3_browser_evidence(*, boot, connected, session):
    """Frozen top-level checks with only the final CDP error classified separately."""
    require(sha(Path(frozen.__file__).read_bytes()) == FROZEN_SHA, 'frozen evidence helpers changed')
    boot_path, _ = frozen.local_reference(boot)
    proof_path, proof_raw = frozen.local_reference(connected)
    session_path, session_raw = frozen.local_reference(session)
    require(proof_path.name == 'connected-proof.json' and session_path.name == 'session.json'
            and proof_path.parent == session_path.parent, 'connected proof and closed session must be from one desktop run')
    require(sha(Path(desktop.__file__).read_bytes()) == frozen.LAUNCHER_SHA, 'frozen v3 launcher changed')
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
    require(not any(finished.get(key) for key in OTHER_ERRORS), 'desktop session has unresolved errors')
    disconnect = finished.get('disconnect', {})
    require(disconnect.get('native_close_verified') is True and disconnect.get('open') is False
            and disconnect.get('closes') == 1 and disconnect.get('closeError') is None, 'native close is not established')
    require(finished.get('evidence') == prepared and proof.get('inputs') == prepared['inputs'], 'v3 evidence chain differs')
    sources = finished.get('source_sha256')
    require(isinstance(sources, dict) and sources, 'desktop implementation/source hashes required')
    for name, digest in sources.items(): frozen.local_reference({'path':name,'sha256':digest})
    for path in (Path(desktop.__file__), desktop.GUARD, desktop.APP/'tankmini.html'):
        require(sources.get(path.relative_to(ROOT).as_posix()) == sha(path.read_bytes()), 'required desktop source not pinned')
    state = proof.get('state', {})
    require(state.get('ready') is True and state.get('connected') is True and state.get('demo') is False
            and state.get('initialReadsFinished') is True and proof.get('held_recovery_verified') is False
            and proof.get('audio_verified') is False and proof.get('mutations_enabled') is False,
            'connected proof does not record the real readonly editor')
    guard = proof.get('guard'); answers = frozen.retained_replies(guard)
    identity = readonly.inspect_pong(answers['PING'][0], frozen.VERSION); pong = identity['pong']
    require(guard.get('observedPong') == state.get('fw') == pong and finished.get('actual_identity') == identity,
            'actual PONG does not match connected and closed observations')
    final_guard = frozen.check_guard(finished.get('last_guard'), closed=True)
    require(final_guard.get('observedPong') == pong and len(final_guard['wire']) >= len(guard['wire'])
            and [x['line'] for x in final_guard['wire'][:len(guard['wire'])]] == [x['line'] for x in guard['wire']],
            'closed guard is not a continuation of the connected proof')
    require(stamp(prepared['evidence']['observed_utc']) <= stamp(finished['started_utc'])
            <= stamp(finished['connected_utc']) <= stamp(proof['observed_utc']) <= stamp(finished['finished_utc']),
            'boot/connected/closed chronology differs')
    close_note = classify_post_close(finished,session_path,final_guard)
    runtime = frozen.parse_runtime(answers)
    return {'schema':1, 'kind':'mini-v3-webserial-read-validation', 'target':'tank-mini', 'transport':'usb-cdc',
        'image_sha256':frozen.IMAGE_SHA, 'firmware_version':frozen.VERSION, 'com':prepared['evidence']['com'],
        'pong':pong, 'profile':copy.deepcopy(prepared['profile']), 'runtime':runtime, 'answers':answers,
        'read_verified':True, 'serial_port_closed':True, 'capabilities_granted':{},
        'observed_utc':proof['observed_utc'], 'closed_utc':finished['finished_utc'],
        'references':{'boot':copy.deepcopy(boot), 'connected':copy.deepcopy(connected), 'session':copy.deepcopy(session),
                      **copy.deepcopy(prepared['inputs'])},
        'evidence_format':'completed WebSerial writes, decoded onLine replies and original Pedal.cmd results',
        'raw_RX_bytes_retained':False, 'raw_byte_replay_performed':False,
        'current_state_requires_fresh_read':True, 'image_hash_attested_by_device':False,
        'held_recovery_verified':False, 'cold_power_cycle_verified':False, 'audio_verified':False,
        'BLE_verified':False, 'preset_writes_verified':False,
        'COM_binding':'normal-boot unique CDC observation; UIA chooser attribution is separate',
        'desktop_close_observation':close_note,
        'frozen_helpers':{'path':Path(frozen.__file__).relative_to(ROOT).as_posix(),'sha256':FROZEN_SHA},
        'implementation':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(Path(__file__).read_bytes())}}
