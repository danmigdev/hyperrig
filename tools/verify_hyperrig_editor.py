"""Check English UI and GitHub reporting in isolated Edge without device access."""
from __future__ import annotations

import argparse
from functools import partial
import http.server
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_hyperrig_editor as product
from tools import verify_mini_browser as browser
from tools import mini_browser_windows as windows


def run(bundle, output):
    proof = product.validate_bundle(bundle)
    output = product.local(output, ROOT / 'build')
    product.require(not output.exists(), 'New verification directory required')
    output.mkdir(parents=True)
    profile = output / 'isolated-profile'
    app = ROOT / proof['app_directory']
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(browser.Handler, directory=str(app)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    report = {'kind': 'hyperrig-english-ui-verification', 'device_io': False,
              'hardware_apis_stubbed': True, 'outbound_navigation_stubbed': True,
              'bundle': proof['product_bundle'], 'scenarios': [], 'result': 'fail'}
    process = cdp = None
    try:
        args = [str(windows.browser_path()), '--headless=new', '--no-first-run', '--no-default-browser-check',
                '--disable-background-networking', '--disable-sync', '--disable-extensions',
                '--disable-component-update', '--disable-features=MediaRouter,OptimizationHints,SerialUsbDisplayNameWin',
                '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0', '--window-size=1440,1000',
                '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
                '--user-data-dir=' + str(profile), 'about:blank']
        with (output / 'browser-stderr.txt').open('wb') as stderr:
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=stderr,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        endpoint = profile / 'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file():
                break
            product.require(process.poll() is None, 'Browser exited before CDP')
            time.sleep(.1)
        product.require(endpoint.is_file(), 'CDP did not become available')
        port = int(endpoint.read_text().splitlines()[0])
        with urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as response:
            pages = json.load(response)
        page = next(page for page in pages if page['type'] == 'page')
        cdp = browser.CDP(page['webSocketDebuggerUrl'])
        for domain in ['Page', 'Runtime', 'Log', 'Network']:
            cdp.call(domain + '.enable')
        guard = browser.GUARD + '''
Object.defineProperty(navigator, 'language', {configurable:true,value:'es-AR'});
Object.defineProperty(navigator, 'languages', {configurable:true,value:['es-AR','it-IT']});
localStorage.setItem('hyperrig.lang','es');
window.__hyperrigOpened=[];
window.open=(url,target,features)=>{__hyperrigOpened.push({url,target,features});return null;};
'''
        cdp.call('Page.addScriptToEvaluateOnNewDocument', {'source': guard})
        for mode in ['disconnected', 'demo']:
            cdp.call('Page.navigate', {'url': f'http://127.0.0.1:{server.server_port}/tankmini.html?english_check={mode}' + ('#demo' if mode == 'demo' else '')})
            for _ in range(100):
                if cdp.evaluate('window.__urOk===true && !!document.getElementById("miniPortStatus")'):
                    break
                time.sleep(.05)
            state = cdp.evaluate('''(()=>({ready:window.__urOk===true,language:document.documentElement.lang,
              runtimeLanguage:LANG,browserLanguage:navigator.language,storedLanguage:localStorage.getItem('hyperrig.lang'),
              status:document.getElementById('miniPortStatus')?.textContent,
              removed:['support','langPick','langSel','updChk'].every(id=>!document.getElementById(id)),
              reportLabel:document.getElementById('reportBtn')?.textContent,
              links:[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')),
              profile:HyperRigMini.profile,hardware:__miniBrowserProbe.calls}))()''')
            product.require(state['ready'] and state['language'] == state['runtimeLanguage'] == 'en', 'Editor did not start in English')
            product.require(state['storedLanguage'] == 'es' and state['browserLanguage'] == 'es-AR', 'Foreign-locale precondition missing')
            product.require(state['removed'] and state['reportLabel'] == 'Report an issue on GitHub…', 'Obsolete controls remain')
            product.require(state['profile'] == proof['profile'] and not state['hardware'], 'Profile changed or hardware API called')
            product.require(all('hyperrig.invalid' not in value and 'ultrarig.app' not in value and 'manuaguirre9' not in value for value in state['links']), 'Original product link remains')
            timeout = cdp.evaluate((app / 'serial-open-timeout.js').read_text('utf-8') + '\ninstallMiniSerialOpenTimeout(SerialTransport)')
            product.require(timeout['timeout_ms'] == 30000 and timeout['native_open_unchanged'], 'Serial timeout adapter failed')
            time.sleep(.6)
            if cdp.evaluate('!!document.querySelector(".ccall .tskip")'):
                cdp.click('.ccall .tskip')
            cdp.click('#setBtn')
            cdp.screenshot(output / (mode + '-settings.png'))
            cdp.click('#reportBtn')
            opened = cdp.evaluate('__hyperrigOpened')
            product.require(len(opened) == 1 and opened[0]['url'] == proof['product']['issues'], 'Report button did not open HyperRig issues')
            product.require(cdp.evaluate('!document.querySelector(".rep")'), 'Old report upload form appeared')
            cdp.click('#setX')
            if mode == 'demo':
                cdp.click('#chain [data-id="0"]')
                before = cdp.evaluate('Number(document.querySelector("#editor [role=slider]").getAttribute("aria-valuenow"))')
                cdp.evaluate('document.querySelector("#editor [role=slider]").focus()')
                for kind in ['keyDown', 'keyUp']:
                    cdp.call('Input.dispatchKeyEvent', {'type': kind, 'key': 'ArrowUp', 'code': 'ArrowUp', 'windowsVirtualKeyCode': 38})
                time.sleep(.15)
                after = cdp.evaluate('Number(document.querySelector("#editor [role=slider]").getAttribute("aria-valuenow"))')
                product.require(after == before + 1, 'Demo effect knob stopped working')
                cdp.click('#edOn')
                product.require(cdp.evaluate('S.chain.P.find(e=>e.id===0).on===false'), 'Demo bypass stopped working')
                cdp.click('#edOn')
            product.require(not cdp.evaluate('__miniBrowserProbe.calls'), 'Offline test attempted hardware access')
            report['scenarios'].append({'mode': mode, 'state': state, 'issue_navigation': opened,
                                        'serial_timeout': timeout, 'demo_knob_checked': mode == 'demo'})
        # Exercise the independent startup-failure path without injecting an error
        # or allowing a real GitHub navigation.
        cdp.evaluate('window.__urOk=false; window.dispatchEvent(new Event("load"));')
        time.sleep(1.7)
        selector = 'div[role="alert"][style*="2147483647"] button'
        product.require(cdp.evaluate('document.querySelector(' + json.dumps(selector) + ')?.textContent')
                        == 'Report this error on GitHub', 'English startup-error report button missing')
        cdp.click(selector)
        opened = cdp.evaluate('__hyperrigOpened')
        product.require(len(opened) == 2 and opened[-1]['url'] == proof['product']['issues'],
                        'Startup-error reporting did not use HyperRig issues')
        report['startup_error_reporting'] = {'checked': True, 'destination': opened[-1]['url']}
        exceptions = [e['params'] for e in cdp.events if e.get('method') == 'Runtime.exceptionThrown']
        requests = [e['params']['request'] for e in cdp.events if e.get('method') == 'Network.requestWillBeSent']
        report['javascript_exceptions'] = exceptions
        report['external_requests'] = [r['url'] for r in requests if not r['url'].startswith(('http://127.0.0.1:', 'data:', 'blob:'))]
        report['POST_requests'] = [r['url'] for r in requests if r.get('method') == 'POST']
        product.require(not exceptions and not report['external_requests'], 'Unexpected script error or external request')
        report['result'] = 'pass'
    except Exception as error:
        report['error'] = repr(error)
        if cdp:
            try:
                report['failure'] = cdp.evaluate(browser.SNAPSHOT)
                cdp.screenshot(output / 'failure.png')
            except Exception:
                pass
        raise
    finally:
        if cdp:
            try:
                cdp.call('Browser.close')
            except Exception:
                pass
            cdp.ws.close()
        if process:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        report['isolated_browser_stopped'] = process is None or process.poll() is not None
        report['local_server_stopped'] = True
        (output / 'report.json').write_bytes(product.encoded(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=ROOT / 'build/hyperrig-mini-english-editor')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.bundle, args.output)
    print(json.dumps({key: result[key] for key in ['result', 'device_io', 'external_requests', 'POST_requests', 'isolated_browser_stopped']}))
