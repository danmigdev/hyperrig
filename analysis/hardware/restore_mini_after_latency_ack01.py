"""Root-operated, single PLOAD recovery after the completed FXE ACK mismatch.

This recovery is separate from the failed timing trial. Responses are observed
through the original app queue; this report does not claim a native-byte audit.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mini_host_journal import read_shared_json, atomic_write_json
from tools.verify_mini_browser import CDP
from tools.probe_mini_browser_first_preset import snapshot, verify_state
from tools.probe_mini_browser_latency import ExistingEditor

folder = ROOT/'build/mini-qualified-editor-live-02'
output = folder/'recovery.json'
assert not output.exists(), 'No repeat of this recovery command'
session = read_shared_json(folder/'session.json')
assert session['identity_verified'] and not session.get('finished_utc')
failed = read_shared_json(ROOT/'build/mini-fx-latency-01/report.json')
assert failed['result'] == 'fail' and failed['guard']['restoreIssued'] is False
assert [w['line'] for w in failed['guard']['wire'] if w['mutation']] == ['GAIN 0 -12', 'FXA P 99 gate', 'FXE 0 0']
baseline = failed['prepared']['baseline']
record = {'kind': 'mini-explicit-PLOAD-recovery', 'result': 'running',
          'started_utc': datetime.now(timezone.utc).isoformat(),
          'failed_trial_unchanged': True, 'native_RX_audit': False,
          'automatic_retry': False, 'firmware_write': False,
          'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
cdp = CDP(session['CDP_page_websocket'])
cdp.ws.settimeout(45)
try:
    live = cdp.evaluate('({origin:location.origin,connected:S.connected,fw:S.fw,guard:!!window.__miniLatencyGuard})')
    assert live == {'origin': session['origin'], 'connected': True, 'fw': session['prepared']['pong'], 'guard': False}
    record['before'] = snapshot(cdp)
    before = record['before']['state']
    assert before['gain'] == [0, -12] and before['plist'] == baseline['plist']
    assert before['fxs']['blocks'] == [{'bank': 'P', 'position': 0, 'id': 0, 'type': 'gate', 'on': 0,
                                      'params': [-70, 120, 0, 0, 0, 0, 0],
                                      'fields': {'l': '0', 'g': '-1', 'fu': '0', 'mem': '0'}}]
    record['request_intent'] = 'PLOAD 0'
    atomic_write_json(output, record)
    record['reply'] = cdp.evaluate("Pedal.cmd('PLOAD 0','PLOAD',8000)")
    atomic_write_json(output, record)
    assert len(record['reply']) == 1 and re.fullmatch(r"PLOAD ok 0 'Preset 1A' missing=0 capture=0 ir=0 ms=\d+", record['reply'][0])
    record['after'] = snapshot(cdp)
    verify_state(record['after']['state'], baseline, gains=baseline['gain'], stage='live')
    record['UI'] = ExistingEditor(cdp).refresh(baseline)
    record['result'] = 'pass'
except Exception as error:
    record['error'] = repr(error)
    record['result'] = 'fail'
finally:
    cdp.ws.close()
    record['finished_utc'] = datetime.now(timezone.utc).isoformat()
    atomic_write_json(output, record)
print(json.dumps({k: record.get(k) for k in ('result', 'reply', 'UI', 'error')}))
raise SystemExit(0 if record['result'] == 'pass' else 1)
