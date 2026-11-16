"""Open the existing HyperRig MINI editor as a local desktop demo window.

No device access: the localhost server denies hardware permissions and a new
browser profile receives the same API guard used by offline browser tests.
Closing this isolated browser window also closes the temporary local server.
"""
import argparse
from functools import partial
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.verify_mini_browser import CDP, GUARD, SNAPSHOT, browser_path
from tools.probe_mini_browser_readonly import LocalHandler, IMAGE_SHA
from tools.mini_host_journal import atomic_write_json


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT/'build') and not output.exists(), 'new build output directory required')
    app = ROOT/'build/hyperrig-mini-audio-v2/app/web'
    require((app/'tankmini.html').is_file(), 'generated MINI editor is missing')
    output.mkdir(parents=True)
    profile = output/'profile'; profile.mkdir()
    status = {'phase': 'starting', 'mode': 'demo', 'physical_device_tested': False,
              'hardware_permissions': False, 'host_pid': os.getpid(), 'personal_profile_used': False,
              'app_files_modified': False, 'app_directory': app.relative_to(ROOT).as_posix(),
              'sources': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__), ROOT/'tools/verify_mini_browser.py',
                                    ROOT/'tools/probe_mini_browser_readonly.py', app/'tankmini.html')}}
    def save(): atomic_write_json(output/'status.json', status)
    save()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(LocalHandler, directory=str(app), live=False))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    process = cdp = None
    try:
        command = [str(browser_path()), '--app=about:blank', '--no-first-run', '--no-default-browser-check',
                   '--disable-background-networking', '--disable-background-mode', '--disable-component-update',
                   '--disable-sync', '--disable-extensions', '--disable-default-apps', '--disable-breakpad',
                   '--disable-features=MediaRouter,OptimizationHints', '--noerrdialogs', '--window-size=1440,1000',
                   '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
                   '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
                   '--user-data-dir='+str(profile)]
        with (output/'browser-stderr.txt').open('wb') as stream:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stream)
        status['browser_pid'] = process.pid; save()
        endpoint = profile/'DevToolsActivePort'
        for _ in range(100):
            if endpoint.is_file(): break
            require(process.poll() is None, 'desktop browser exited during startup')
            time.sleep(.1)
        require(endpoint.is_file(), 'desktop browser startup timed out')
        debug_origin = f'http://127.0.0.1:{int(endpoint.read_text().splitlines()[0])}'
        pages = json.loads(urlopen(debug_origin+'/json/list', timeout=5).read())
        page = next(p for p in pages if p['type'] == 'page')
        cdp = CDP(page['webSocketDebuggerUrl'])
        for domain in ('Runtime', 'Page', 'Log'): cdp.call(domain+'.enable')
        cdp.call('Page.addScriptToEvaluateOnNewDocument', {'source': GUARD})
        url = origin+'/tankmini.html?desktop_demo=1#demo'
        cdp.call('Page.navigate', {'url': url})
        for _ in range(150):
            if cdp.evaluate("window.__urOk===true && !!document.getElementById('miniPortStatus')"): break
            time.sleep(.05)
        state = cdp.evaluate(SNAPSHOT)
        require(state['ready'] and state['demo'] and state['title'] == 'HyperRig for TANK MINI'
                and state['profile']['image_sha256'] == IMAGE_SHA and not state['hardware']['calls'],
                'desktop demo did not initialize with the expected MINI profile')
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"): cdp.click('.ccall .tskip')
        errors = [e for e in cdp.events if e.get('method') == 'Runtime.exceptionThrown']
        require(not errors, 'desktop demo raised a JavaScript exception')
        with urlopen(url, timeout=5) as response:
            policy = response.headers.get('Permissions-Policy', '')
        require(all(f'{name}=()' in policy for name in ('serial', 'usb', 'bluetooth', 'midi')),
                'desktop demo server must deny hardware permissions')
        status.update(phase='ready', title=state['title'], url=url, initial_state=state,
                      permissions_policy=policy, screenshot=cdp.screenshot(output/'desktop-demo.png'),
                      javascript_exceptions=0)
        save()
        cdp.ws.close(); cdp = None
        # No services, scheduled tasks or startup entries. The browser owns this lifetime.
        process.wait()
        status['phase'] = 'closed'
    except BaseException as error:
        status.update(phase='failed', error=repr(error))
        if cdp:
            try: cdp.call('Browser.close')
            except Exception: pass
        if process and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: pass
        raise
    finally:
        if cdp:
            try: cdp.ws.close()
            except Exception: pass
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        status['local_server_closed'] = True
        status['browser_stopped'] = process is None or process.poll() is not None
        save()


if __name__ == '__main__': main()
