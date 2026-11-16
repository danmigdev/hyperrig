"""Root UI operation for an actual, already running saved-reload v2 trial."""
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mini_host_journal import read_shared_json, atomic_write_json
from tools.verify_mini_browser import CDP
from tools.activate_mini_editor_ui import STATE, activate

report_path = Path(sys.argv[1]).resolve()
assert report_path.is_relative_to(ROOT / 'build')
report = read_shared_json(report_path)
assert report['kind'] == 'mini-browser-saved-reload-continuation-v2'
assert report['result'] == 'running'
assert report['phase'] == 'awaiting_native_CDC_selection'
for name in ('tools/probe_mini_browser_saved_reload_v2.py',
             'tools/mini_browser_saved_reload_guard_v2.js'):
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == report['source_sha256'][name]
url = report['origin'] + '/tankmini.html?saved_reload_continuation=1'
pages = json.loads(urlopen(report['CDP_http'] + '/json/list', timeout=5).read())
exact = [p for p in pages if p.get('type') == 'page' and p.get('url') == url]
assert len(exact) == 1
cdp = CDP(exact[0]['webSocketDebuggerUrl'])
output = report_path.parent
try:
    state = cdp.evaluate(STATE)
    print(json.dumps({'observed_state': state}), flush=True)
    if state['guard']['requests'] == 0 and not state['connected'] and not state['connecting']:
        prepared = {'url': url, 'origin': report['origin'], 'CDP_http': report['CDP_http']}
        def publish(value):
            value['operator_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            value['operator_helper_sha256'] = hashlib.sha256((ROOT / 'tools/activate_mini_editor_ui.py').read_bytes()).hexdigest()
            atomic_write_json(output / 'root-ui-activation.json', value)
        result = activate(cdp, prepared, output, publish=publish)
        print(json.dumps({'result': result['result'], 'error': result.get('error')}), flush=True)
        if result['result'] != 'request_observed':
            raise SystemExit(1)
    else:
        print(json.dumps({'action': 'none', 'reason': 'chooser or connection already started'}))
finally:
    cdp.ws.close()
