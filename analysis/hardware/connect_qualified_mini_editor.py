"""Root UI operator: dismiss the tour and click Connect on an owned editor.

No protocol commands or port selection. Native selection is a separate UI action.
"""
from pathlib import Path
import sys
import json
import time
import hashlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mini_host_journal import read_shared_json, atomic_write_json
from tools.verify_mini_browser import CDP
from tools.activate_mini_editor_ui import stable_target, INSTALL_OBSERVER

folder = Path(sys.argv[1]).resolve()
assert folder.is_relative_to(ROOT/'build')
session = read_shared_json(folder/'session.json')
assert session['phase'] == 'awaiting_USB_selection' and not session.get('finished_utc')
out = folder/'root-ui-activation.json'
assert not out.exists(), 'Do not repeat an uncertain click'
cdp = CDP(session['CDP_page_websocket'])
cdp.ws.settimeout(45)
record = {'kind': 'qualified-editor-root-UI-activation', 'origin': session['origin'],
          'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'actions': []}

def state():
    return cdp.evaluate('({url:location.href,coach:!!document.querySelector(".coach"),connected:!!S.connected,connecting:!!S.connecting,open:SerialTransport.isOpen(),observation:__miniEditorObservation.state})')

try:
    s = state()
    assert s['url'].startswith(session['origin']+'/tankmini.html?')
    assert not s['connected'] and not s['connecting'] and not s['open'] and s['observation']['opens'] == 0
    cdp.evaluate(INSTALL_OBSERVER)
    for selector in ['.ccall .tskip', '#connBtn']:
        cdp.call('Page.bringToFront')
        cdp.screenshot(folder/('root-skip.png' if selector.startswith('.') else 'root-connect.png'))
        s = state()
        assert not s['connected'] and not s['connecting'] and not s['open']
        if selector.startswith('.') and not s['coach']:
            continue
        if selector == '#connBtn':
            assert not s['coach']
        point = stable_target(cdp, selector)
        record['actions'].append({'selector': selector, 'dispatch_intent': True, 'point': point})
        atomic_write_json(out, record)
        for kind in ['mousePressed', 'mouseReleased']:
            cdp.call('Input.dispatchMouseEvent', {'type': kind, 'x': point['x'], 'y': point['y'], 'button': 'left', 'clickCount': 1})
        time.sleep(.25)
        clicks = cdp.evaluate('__miniTourOperator.clicks')
        assert any(x['selector'] == selector and x['trusted'] for x in clicks)
    record['clicks'] = cdp.evaluate('__miniTourOperator.clicks')
    record['after'] = state()
    record['result'] = 'trusted_UI_clicks_observed'
    cdp.evaluate('__miniTourOperator.remove()')
except Exception as error:
    record.update(result='fail', error=repr(error))
finally:
    atomic_write_json(out, record)
    cdp.ws.close()
print(json.dumps({k: record.get(k) for k in ('result', 'origin', 'clicks', 'error')}))
