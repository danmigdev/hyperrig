"""Explicit root UI operations for the one owned FX editor smoke test."""
from pathlib import Path
import sys
import json
import time
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mini_host_journal import read_shared_json, atomic_write_json
from tools.verify_mini_browser import CDP
from tools.activate_mini_editor_ui import stable_target
from tools.probe_mini_browser_first_preset import snapshot, query

session_dir = ROOT/'build/mini-fx-editor-live-01'
output = ROOT/'build/mini-fx-ui-smoke-01'
session = read_shared_json(session_dir/'session.json')
assert session['identity_verified'] and not session.get('finished_utc')
action = sys.argv[1]
cdp = CDP(session['CDP_page_websocket'])
cdp.ws.settimeout(45)
report = None

def save():
    atomic_write_json(output/'report.json', report)

try:
    live = cdp.evaluate('({url:location.href,connected:S.connected,demo:DEMO,fw:S.fw})')
    assert live == {'url': session['origin']+'/tankmini.html?qualified_fx_editor=1',
                    'connected': True, 'demo': False, 'fw': session['prepared']['pong']}
    if action == 'init':
        output.mkdir(exist_ok=False)
        report = {'kind': 'mini-real-FX-UI-smoke', 'result': 'running', 'actions': [], 'snapshots': {},
                  'session': str(session_dir.relative_to(ROOT)), 'bundle': session['prepared']['bundle']['refs'],
                  'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in [Path(__file__), ROOT/'analysis/hardware/observe_mini_fx_ui.js']},
                  'started_utc': datetime.now(timezone.utc).isoformat(), 'automatic_retry': False}
        save()
        report['observer'] = cdp.evaluate((ROOT/'analysis/hardware/observe_mini_fx_ui.js').read_text())
        report['priming'] = query(cdp, 'PING')
        report['pong'] = query(cdp, 'PING')
        assert report['pong'] == [session['prepared']['pong']]
        cdp.evaluate("(async()=>{applyLvl(reply(await Pedal.cmd('LVL','LVL',1500),'LVL'));await Pedal.chain;})()")
        report['snapshots']['baseline'] = snapshot(cdp)
        assert report['snapshots']['baseline']['state']['gain'] == [0, 0]
        assert not report['snapshots']['baseline']['state']['fxs']['blocks']
        assert [p['slot'] for p in report['snapshots']['baseline']['state']['plist']['presets']] == [0]
    else:
        report = read_shared_json(output/'report.json')
        assert report['result'] == 'running'
        if action in ('click', 'key', 'text'):
            selector = sys.argv[2]
            cdp.call('Page.bringToFront')
            cdp.screenshot(output/f"action-{len(report['actions']):02}-before.png")
            point = stable_target(cdp, selector)
            item = {'action': action, 'selector': selector, 'value': sys.argv[3] if len(sys.argv)>3 else None,
                    'utc': datetime.now(timezone.utc).isoformat(), 'dispatch_intent': True}
            report['actions'].append(item); save()
            if action == 'click':
                for kind in ('mousePressed', 'mouseReleased'):
                    cdp.call('Input.dispatchMouseEvent', {'type':kind,'x':point['x'],'y':point['y'],'button':'left','clickCount':1})
            else:
                cdp.evaluate('document.querySelector('+json.dumps(selector)+').focus()')
                if action == 'text':
                    for kind in ('keyDown','keyUp'):
                        cdp.call('Input.dispatchKeyEvent', {'type':kind,'key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2})
                    cdp.call('Input.insertText', {'text':sys.argv[3]})
                else:
                    key = sys.argv[3]
                    code = {'ArrowDown':40,'ArrowUp':38,'Enter':13,'Escape':27,'Home':36,'End':35}[key]
                    for kind in ('keyDown','keyUp'):
                        cdp.call('Input.dispatchKeyEvent', {'type':kind,'key':key,'code':key,'windowsVirtualKeyCode':code})
            time.sleep(.35)
            cdp.evaluate('(async()=>{await Pedal.chain;return true;})()')
            item['dispatch_returned'] = True
        elif action == 'snapshot':
            report['snapshots'][sys.argv[2]] = snapshot(cdp)
            value = report['snapshots'][sys.argv[2]]['state']
            print(json.dumps({k:value[k] for k in ['gain','fxs','plist','snaps']},ensure_ascii=False))
        elif action == 'inspect':
            print(json.dumps(cdp.evaluate(sys.argv[2]),ensure_ascii=False))
        elif action == 'finish':
            report['audit'] = cdp.evaluate('__miniFXUIAudit.detach()')
            report['finished_utc'] = datetime.now(timezone.utc).isoformat()
            report['result'] = 'recorded_pending_independent_validation'
            cdp.screenshot(output/'final.png')
        else:
            raise ValueError('Unknown explicit operation')
    if action != 'finish':
        report['audit'] = cdp.evaluate('__miniFXUIAudit.state')
    save()
    print(json.dumps({'operation':action,'actions':len(report['actions']),'commands':len(report.get('audit',{}).get('commands',[]))}))
finally:
    cdp.ws.close()
