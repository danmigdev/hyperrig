"""Root-operated UI assistance for the frozen saved-reload probe.

Default/check-only never access a browser. Execute dismisses the real tour and
clicks Connect once, after hit-testing; it does not choose a port or send commands.
The original probe, guard, source chain and reports remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.mini_host_journal import atomic_write_json, read_shared_bytes
from tools.verify_mini_browser import CDP

PINS = {
    'tools/probe_mini_browser_saved_reload.py': '8f044dcd2ab5cc98521a02b972a473cb5a686c3f7f88ef47c1e1c7fcec300db4',
    'tools/mini_browser_saved_reload_guard.js': 'e0de0abe48c29ec28ba7c7a02ecfe1ce79225db8079786e1e34fc31c8c9982f9',
}
SKIP, CONNECT = '.ccall .tskip', '#connBtn'
STATE = """(() => {const g=globalThis.__miniSavedReloadGuard?.state;return {
 url:location.href,visibility:document.visibilityState,focused:document.hasFocus(),
 coach:!!document.querySelector('.coach'),connected:!!S.connected,connecting:!!S.connecting,
 serialOpen:SerialTransport.isOpen(),guard:g?{requests:g.requests,opens:g.opens,
 mutations:g.mutations,stopped:g.stopped,fatal:g.fatal,requestEnabled:g.requestEnabled,
 appInstalled:g.appInstalled}:null};})()"""
INSTALL_OBSERVER = """(() => {
 if(window.__miniTourOperator)throw Error('UI operator already installed; no replay');
 const value={clicks:[]};const listener=e=>{for(const selector of ['.ccall .tskip','#connBtn']){
   if(e.target.closest?.(selector))value.clicks.push({selector,trusted:e.isTrusted,
     utc:new Date().toISOString(),x:e.clientX,y:e.clientY});}};
 document.addEventListener('click',listener,true);
 value.remove=()=>document.removeEventListener('click',listener,true);
 Object.defineProperty(window,'__miniTourOperator',{value});return true;})()"""


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT/'build'), 'owned build report required')
    raw = read_shared_bytes(path); report = json.loads(raw)
    require(report.get('kind') == 'mini-browser-saved-reload-continuation'
            and report.get('result') == 'running'
            and report.get('phase') == 'awaiting_exact_UIA_selection'
            and not any(report.get(k) for k in ('finished_utc', 'error', 'cleanup_error')),
            'only the active frozen saved-reload chooser phase is supported')
    for name, expected in PINS.items():
        require(report.get('source_sha256', {}).get(name) == expected
                and digest(read_shared_bytes(ROOT/name)) == expected, 'probe/guard pin differs')
    for key in ('origin', 'CDP_http'):
        require(re.fullmatch(r'http://127\.0\.0\.1:[1-9]\d{0,4}', report.get(key, '')), 'owned local endpoint required')
    return {'report': {'path': path.relative_to(ROOT).as_posix(), 'sha256_at_prepare': digest(raw)},
            'origin': report['origin'], 'CDP_http': report['CDP_http'],
            'url': report['origin']+'/tankmini.html?saved_reload_continuation=1'}


def idle(state, url):
    require(state.get('url') == url and state.get('connected') is False
            and state.get('connecting') is False and state.get('serialOpen') is False,
            'original UI must be disconnected and idle on the exact page')
    g = state.get('guard') or {}
    require(all(g.get(k) == 0 for k in ('requests', 'opens', 'mutations'))
            and g.get('stopped') is False and g.get('fatal') is None
            and g.get('requestEnabled') is True and g.get('appInstalled') is True,
            'no request/open/mutation may already have happened; do not repeat Connect')


def target_script(selector):
    return """(() => {const e=document.querySelector(SELECTOR);if(!e)return null;
      const r=e.getBoundingClientRect(),s=getComputedStyle(e),x=r.x+r.width/2,y=r.y+r.height/2;
      const hit=document.elementFromPoint(x,y);return {x,y,width:r.width,height:r.height,
        okay:r.width>0&&r.height>0&&!e.disabled&&!e.closest('[inert]')&&
          s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0&&
          (hit===e||e.contains(hit)),hit:hit?.tagName||null};})()""".replace('SELECTOR', json.dumps(selector))


def stable_target(cdp, selector, *, clock=time.monotonic, sleep=time.sleep):
    cdp.evaluate('document.querySelector('+json.dumps(selector)+')?.scrollIntoView({block:"center"})')
    previous = None; count = 0; deadline = clock()+5
    while clock() < deadline:
        value = cdp.evaluate(target_script(selector))
        same = value and previous and all(abs(value[k]-previous[k]) <= .25 for k in ('x', 'y', 'width', 'height'))
        count = count+1 if value and value.get('okay') and same else (1 if value and value.get('okay') else 0)
        if count >= 3:
            return value
        previous = value; sleep(.1)
    raise ValueError('button layout/hit-test did not settle; no click')


def activate(cdp, prepared, output, *, publish=lambda value: None, clock=time.monotonic, sleep=time.sleep):
    """Only this function performs UI actions; tests supply a fake CDP object."""
    report = {'kind': 'mini-owned-tour-activation', 'result': 'running', 'prepared': prepared,
              'actions': [], 'automatic_retry': False, 'port_selection_performed': False,
              'direct_protocol_commands': [], 'connection_verified': False}
    observed = False
    try:
        idle(cdp.evaluate(STATE), prepared['url'])
        cdp.evaluate(INSTALL_OBSERVER); observed = True
        for selector in (SKIP, CONNECT):
            cdp.call('Page.bringToFront')
            report['before_'+('skip' if selector == SKIP else 'connect')] = cdp.screenshot(output/('skip.png' if selector == SKIP else 'connect.png'))
            state = cdp.evaluate(STATE); idle(state, prepared['url'])
            report['observed_state'] = state
            if selector == SKIP and not state['coach']:
                report['tour_already_absent'] = True; continue
            if selector == CONNECT:
                require(not state['coach'], 'tour must be absent before Connect')
            point = stable_target(cdp, selector, clock=clock, sleep=sleep)
            idle(cdp.evaluate(STATE), prepared['url'])
            # Consume this one action before dispatch. A lost CDP reply never permits another click.
            report['actions'].append({'selector': selector, 'point': point, 'dispatch_intent': True})
            publish(report)
            for kind in ('mousePressed', 'mouseReleased'):
                cdp.call('Input.dispatchMouseEvent', {'type': kind, 'x': point['x'], 'y': point['y'], 'button': 'left', 'clickCount': 1})
            deadline = clock()+5
            while clock() < deadline:
                clicks = cdp.evaluate('__miniTourOperator.clicks')
                matches = [c for c in clicks if c['selector'] == selector]
                require(len(matches) <= 1, 'duplicate observed UI click')
                state = cdp.evaluate(STATE)
                ready = not state['coach'] if selector == SKIP else state['guard']['requests'] == 1
                if matches and matches[0]['trusted'] is True and ready:
                    break
                sleep(.1)
            else:
                raise ValueError('trusted click/result not observed; do not retry')
            report['actions'][-1]['observed_click'] = matches[0]
            report['after'] = state; publish(report)
        report['result'] = 'request_observed'
    except Exception as error:
        report.update(result='fail', error=repr(error))
    finally:
        if observed:
            try:
                report['clicks'] = cdp.evaluate('__miniTourOperator.clicks')
                cdp.evaluate('__miniTourOperator.remove()')
            except Exception as error:
                report['observation_error'] = repr(error); report['result'] = 'fail'
        publish(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-only', action='store_true'); mode.add_argument('--execute', action='store_true')
    parser.add_argument('--report', type=Path); parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if not (args.check_only or args.execute):
        print(json.dumps({'browser_access': False, 'inputs_read': False})); return 0
    require(args.report is not None, 'active probe report required')
    prepared = prepare(args.report)
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'browser_access': False, 'prepared': prepared})); return 0
    output = args.output.resolve() if args.output else None
    require(output and output.is_relative_to(ROOT/'build') and not output.exists(), 'new independent build output required')
    output.mkdir(parents=True)
    pages = json.loads(urlopen(prepared['CDP_http']+'/json/list', timeout=5).read())
    exact = [p for p in pages if p.get('type') == 'page' and p.get('url') == prepared['url']]
    require(len(exact) == 1, 'one exact owned page required')
    ws = exact[0]['webSocketDebuggerUrl']
    require(ws.startswith(prepared['CDP_http'].replace('http:', 'ws:')+'/devtools/page/'), 'page websocket differs from owned endpoint')
    cdp = CDP(ws)
    def publish(value):
        value['source_sha256'] = {str(Path(__file__).relative_to(ROOT)).replace('\\', '/'): digest(Path(__file__).read_bytes())}
        atomic_write_json(output/'report.json', value)
    try:
        result = activate(cdp, prepared, output, publish=publish)
    finally:
        cdp.ws.close()  # Detach this observer only; do not close browser, port or probe.
    print(json.dumps({'result': result['result'], 'error': result.get('error')}))
    return 0 if result['result'] == 'request_observed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
