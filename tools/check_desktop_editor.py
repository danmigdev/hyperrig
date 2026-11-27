"""Use the desktop editor's program with a simulated pedal, and try its locks. No device is opened.

The built program runs outside the screens, with a profile of its own and --no-pedal, so that it never gets the port of a real
pedal. First its locks, from inside the page: no Node, no network, no other page, no file but the editor's, no port, no
permission it does not use; one instance; the settings and the log kept; a changed file refused at the start. Then the session
of tools/check_mini_dev_editor.py runs in it: connect, tempo, tuner, amp, presets, blocks, scenes, captures, cab IRs, panel
and stage, against the same simulated pedal. Last, Browse TONE3000 and Browse Patchstorage against simulated ones on this computer.

Usage, from the repository root:
    python -B tools/check_desktop_editor.py --program build/hyperrig-desktop-NN --output build/CHECK-NN
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_desktop_editor as desktop  # noqa: E402
from tools import check_mini_dev_editor as page_check  # noqa: E402
from tools import check_mini_try  # noqa: E402
from tools import simulated_patchstorage  # noqa: E402
from tools import simulated_tone3000  # noqa: E402
from tools import page_driver as browser  # noqa: E402

require = desktop.require
START = 'hyperrig://editor/tank-mini.html'


def command(program, profile, *more):
    return [str(program), '--no-pedal', '--off-screen', f'--profile={profile}', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0', *more]


class Window(page_check.Page):
    """The program's window, driven over its debugging port."""
    program = None
    more = ()

    def __init__(self, bundle, output, identity=None, *, simulated=True, profile=None):
        self.profile = profile or output / ('profile-' + str(len(list(output.glob('profile-*')))))
        self.profile.mkdir(exist_ok=True)
        endpoint = self.profile / 'DevToolsActivePort'
        endpoint.unlink(missing_ok=True)
        self.process = subprocess.Popen(command(self.program, self.profile, *self.more), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 40
        while not (endpoint.is_file() and endpoint.read_text().strip()):
            require(self.process.poll() is None, 'the program ended')
            require(time.monotonic() < deadline, 'the program does not open its debugging port')
            time.sleep(0.1)
        port = self.port = int(endpoint.read_text().splitlines()[0])
        page = None
        while page is None:
            with urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as response:
                page = next((p for p in json.load(response) if p['type'] == 'page' and p['url'].startswith(START)), None)
            require(time.monotonic() < deadline, 'the program does not open the editor')
            time.sleep(0.1)
        self.cdp = browser.CDP(page['webSocketDebuggerUrl'])
        for domain in ('Page', 'Runtime'):
            self.cdp.call(domain + '.enable')
        if simulated:
            self.cdp.call('Page.addScriptToEvaluateOnNewDocument', {'source': page_check.pedal_source(identity)})
            self.cdp.call('Page.navigate', {'url': START})

    def other(self, start, what, seconds=20):
        """Another window of the program, by the start of its address."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            with urlopen(f'http://127.0.0.1:{self.port}/json/list', timeout=5) as response:
                page = next((p for p in json.load(response) if p['type'] == 'page' and p['url'].startswith(start)), None)
            if page:
                cdp = browser.CDP(page['webSocketDebuggerUrl'])
                cdp.call('Runtime.enable')
                while time.monotonic() < deadline:
                    if cdp.evaluate('document.readyState === "complete" && location.href !== "about:blank"'):
                        return cdp
                    time.sleep(0.1)
            time.sleep(0.1)
        raise ValueError(f'no window: {what}')

    def others(self, start):
        with urlopen(f'http://127.0.0.1:{self.port}/json/list', timeout=5) as response:
            return [p['url'] for p in json.load(response) if p['type'] == 'page' and p['url'].startswith(start)]

    def close(self):
        try:
            self.cdp.call('Browser.close')
        except Exception:
            pass
        try:
            self.process.wait(15)
        except subprocess.TimeoutExpired:
            self.process.kill()


LOCKS = '''(async () => {
  const out = {}, no = async (name, f) => { try { const v = await f(); out[name] = v === undefined ? "done" : "done: " + String(v).slice(0, 60); } catch (e) { out[name] = "refused"; } };
  out.node = [typeof require, typeof process, typeof module, typeof Buffer, typeof global].join();
  out.secure = isSecureContext; out.origin = origin; out.serial = typeof navigator.serial;
  out.ports = (await navigator.serial.getPorts()).length;
  await no("https", () => fetch("https://github.com/"));
  await no("http", () => fetch("http://127.0.0.1:8765/"));
  await no("file", () => fetch("file:///C:/Windows/win.ini"));
  await no("image", () => new Promise((ok, bad) => { const i = new Image(); i.onload = ok; i.onerror = bad; i.src = "https://github.com/favicon.ico"; }));
  await no("script", () => new Promise((ok, bad) => { const s = document.createElement("script"); s.onload = ok; s.onerror = bad; s.src = "https://cdn.jsdelivr.net/npm/x"; document.head.append(s); }));
  await no("frame", () => new Promise((ok, bad) => { const f = document.createElement("iframe"); let seen = false; document.addEventListener("securitypolicyviolation", () => { seen = true; });
    f.src = "https://example.com"; document.body.append(f); setTimeout(() => { f.remove(); seen ? bad() : ok(); }, 800); }));
  await no("socket", () => new Promise((ok, bad) => { const w = new WebSocket("ws://127.0.0.1:9"); w.onopen = ok; w.onerror = bad; }));
  await no("beacon", () => { if (!navigator.sendBeacon("https://example.com/x", "x")) throw 0; return new Promise((ok, bad) => setTimeout(() => bad(), 300)); });
  out.outside = [];
  for (const path of ["main.js", "../main.js", "manifest.json", "..%2fmanifest.json", "%2e%2e/manifest.json", "package.json", "profile.json", "x/../../main.js"])
    try { out.outside.push((await fetch(path)).status); } catch (e) { out.outside.push(0); }
  out.own = (await fetch("nam2chip.js")).status;
  out.ctl = (await fetch("ctl.json")).status;
  await no("camera", () => navigator.mediaDevices.getUserMedia({video: true}));
  await no("microphone", () => navigator.mediaDevices.getUserMedia({audio: true}));
  await no("place", () => new Promise((ok, bad) => navigator.geolocation.getCurrentPosition(ok, bad)));
  await no("midi", () => navigator.requestMIDIAccess({sysex: true}));
  await no("read clipboard", () => navigator.clipboard.readText());
  await no("notify", async () => { if (await Notification.requestPermission() !== "granted") throw 0; });
  await no("usb", () => navigator.usb.requestDevice({filters: []}));
  await no("hid", () => navigator.hid.requestDevice({filters: []}));
  out.window = window.open("https://example.com/") === null;
  await no("worker", () => new Promise((ok, bad) => { const w = new Worker("nam2chip.js"); w.onerror = e => bad(e); setTimeout(() => { w.terminate(); ok("a worker of the editor"); }, 600); }));
  await no("converter", () => new Promise((ok, bad) => { const w = new Worker("product-parametric.js"); w.onerror = e => bad(e); w.onmessage = e => { w.terminate(); ok(e.data.msg); }; w.postMessage({text: "{}"}); }));
  await no("kept", () => { const v = localStorage.getItem("check"); localStorage.setItem("check", "kept"); return v; });
  return out;
})()'''


def sizes(window):
    """The size of everything: the buttons, the keys, what is shown, and that it stays."""
    cdp, out = window.cdp, {}
    cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
    time.sleep(0.5)
    state = 'fetch("zoom", {cache: "no-store"}).then(r => r.json())'
    first = cdp.evaluate(state)
    require(first['auto'] is True and cdp.evaluate('document.querySelector(".hrzoom .hrz")?.textContent') == f"{first['percent']} %", f'at the start: {first}')
    width = cdp.evaluate('innerWidth')

    def after(what, good):
        deadline = time.monotonic() + 5
        while True:
            now = cdp.evaluate(state)
            if good(now) and cdp.evaluate('document.querySelector(".hrzoom .hrz")?.textContent') == f"{now['percent']} %":
                return now
            require(time.monotonic() < deadline, f'{what}: {now}')
            time.sleep(0.1)
    cdp.click('.hrzoom button:last-child')
    out['larger'] = after('larger', lambda s: s['percent'] > first['percent'] and not s['auto'])
    require(cdp.evaluate('innerWidth') < width, 'nothing became larger')
    cdp.click('.hrzoom button:first-child')
    after('smaller', lambda s: s['percent'] < out['larger']['percent'])
    key = {'modifiers': 2, 'key': '+', 'code': 'BracketRight', 'windowsVirtualKeyCode': 187, 'text': ''}
    cdp.call('Input.dispatchKeyEvent', {'type': 'rawKeyDown', **key})
    out['key'] = after('Ctrl +', lambda s: s['percent'] == out['larger']['percent'])
    cdp.call('Input.dispatchKeyEvent', {'type': 'keyUp', **key})
    place = {'x': 300, 'y': 400, 'modifiers': 2}
    cdp.call('Input.dispatchMouseEvent', {'type': 'mouseWheel', **place, 'deltaX': 0, 'deltaY': 120})
    out['wheel'] = after('Ctrl and the wheel', lambda s: s['percent'] < out['larger']['percent'])
    cdp.call('Input.dispatchMouseEvent', {'type': 'mouseWheel', **place, 'deltaX': 0, 'deltaY': -120})
    after('Ctrl and the wheel back', lambda s: s['percent'] == out['larger']['percent'])
    kept = out['key']['percent']
    cdp.call('Page.reload')
    time.sleep(1.5)
    window.wait('window.__urOk === true && !!document.querySelector(".hrzoom")', 'the page again', 20)
    after('after a reload', lambda s: s['percent'] == kept and not s['auto'])
    return out, kept


def locks(program, output):
    window = Window(None, output, simulated=False)
    cdp, out = window.cdp, {}
    window.wait('window.__urOk === true', 'the page', 40)
    seen = cdp.evaluate(LOCKS)
    out['page'] = seen
    require(seen['node'] == 'undefined,undefined,undefined,undefined,undefined', f"Node in the page: {seen['node']}")
    require(seen['secure'] is True and seen['origin'] == 'hyperrig://editor' and seen['serial'] == 'object' and seen['ports'] == 0, f'the page: {seen}')
    for name in ('https', 'http', 'file', 'image', 'script', 'frame', 'socket', 'beacon', 'camera', 'microphone', 'place', 'midi', 'read clipboard', 'notify', 'usb', 'hid'):
        require(seen[name] == 'refused', f'{name}: {seen[name]}')
    require(set(seen['outside']) <= {404, 0} and seen['own'] == 200 and seen['ctl'] == 404, f"files: {seen['outside']} {seen['own']}")
    require(seen['window'] is True and seen['worker'].startswith('done') and seen['converter'].startswith('done: This is not a parametric') and seen['kept'] == 'done: null', f'the rest: {seen}')
    for address in ('https://example.com/', 'file:///C:/Windows/win.ini', 'http://127.0.0.1:8765/'):
        cdp.evaluate(f'void (location.href = {json.dumps(address)})')
        time.sleep(0.8)
        require(cdp.evaluate('location.href') == START, f'the window went to {address}')
    cdp.evaluate('Log.ev("check", {row: 1}); typeof Log.flush === "function" && Log.flush()')
    out['title'] = cdp.evaluate('document.title')
    out['sizes'], kept = sizes(window)
    # one instance
    second = subprocess.run(command(program, window.profile), capture_output=True, timeout=30)
    require(second.returncode == 0 and window.process.poll() is None and cdp.evaluate('1 + 1') == 2, 'a second instance')
    out['second_instance'] = 'ended by itself'
    deadline = time.monotonic() + 20
    rows = []
    while time.monotonic() < deadline and not any('"check"' in r for r in rows):
        rows = [r for f in sorted((window.profile / 'logs').glob('editor-*.jsonl')) for r in f.read_text(encoding='utf-8').splitlines()]
        time.sleep(0.3)
    require(any('app_start' in r for r in rows) and any('"check"' in r for r in rows), f'the log: {rows[:3]}')
    out['log_rows'] = len(rows)
    window.close()
    require(window.process.poll() is not None, 'the program does not end')
    # the settings are there after a restart
    window = Window(None, output, simulated=False, profile=window.profile)
    window.wait('window.__urOk === true', 'the page', 40)
    require(window.cdp.evaluate('localStorage.getItem("check")') == 'kept', 'the settings are not kept')
    require(window.cdp.evaluate('fetch("zoom").then(r => r.json())')['percent'] == kept, 'the size is not kept')
    key = {'modifiers': 2, 'key': '0', 'code': 'Digit0', 'windowsVirtualKeyCode': 48, 'text': ''}
    window.cdp.call('Input.dispatchKeyEvent', {'type': 'rawKeyDown', **key})
    time.sleep(0.5)
    require(window.cdp.evaluate('fetch("zoom").then(r => r.json())')['auto'] is True, 'Ctrl 0 does not fit it to the window')
    require(len(list((window.profile / 'logs').glob('editor-*.jsonl'))) == 2, 'a log of its own for each start')
    window.close()
    # a file the page makes is saved, under its name without a path; one from anywhere else is not
    window = Window(None, output, simulated=False)
    window.wait('window.__urOk === true', 'the page', 40)
    saved = window.profile / 'saved'
    window.cdp.evaluate('(() => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["{\\"check\\": 1}"], {type: "application/json"})); a.download = "../../Check è.hyperrig.json"; a.click(); })()')
    deadline = time.monotonic() + 20
    while not (saved.is_dir() and [p for p in saved.iterdir() if p.suffix == '.json' and p.stat().st_size]):
        require(time.monotonic() < deadline, 'a file of the page is not saved')
        time.sleep(0.2)
    files = [(p.name, p.read_bytes()) for p in saved.iterdir()]
    require(len(files) == 1 and files[0][1] == b'{"check": 1}' and files[0][0].endswith('Check \u00e8.hyperrig.json') and '/' not in files[0][0], f'the saved file: {files}')
    window.cdp.evaluate('(() => { const a = document.createElement("a"); a.href = "nam2chip.js"; a.download = "x.js"; a.click(); })()')
    time.sleep(1.5)
    require(len(list(saved.iterdir())) == 1, 'a file that the page did not make was saved')
    out['saved'] = files[0][0]
    window.close()
    # a changed file
    copy = output / 'damaged'
    shutil.copytree(program.parent, copy)
    changed = copy / 'resources/app/editor/web/mini-dev-rules.js'
    changed.write_bytes(changed.read_bytes().replace(b'Math.abs', b'Math.max', 1))
    done = subprocess.run([str(copy / program.name), '--no-pedal', '--off-screen', f"--profile={output / 'profile-damaged'}"], capture_output=True, timeout=40)
    require(done.returncode == 3 and b'damaged (web/mini-dev-rules.js)' in done.stdout + done.stderr, f'a changed file: {done.returncode} {done.stderr[-200:]}')
    out['damaged'] = 'refused'
    # run as Node, and NODE_OPTIONS, are off in the program file
    for environment in ({'ELECTRON_RUN_AS_NODE': '1'}, {'NODE_OPTIONS': '--require=./evil.js'}):
        import os
        done = subprocess.Popen([str(copy / program.name), '--no-pedal', '--off-screen', f"--profile={output / 'profile-damaged'}", '-e', 'process.exit(77)'],
                                env={**os.environ, **environment}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        require(done.wait(40) == 3, f'{environment}: {done.returncode}')
    out['as_node'] = 'refused'
    shutil.rmtree(copy, ignore_errors=True)
    return out


def tone3000(program, bundle, output):
    """Browse TONE3000 as a person does, against a simulated one: sign in, choose, load a capture and an IR, cancel, sign out."""
    product = json.loads((Path(bundle) / 'editor/profile.json').read_bytes())['development']['product']
    identity = f"HRID 1 {product['version']} {product['build_id']} banks=3"
    service = simulated_tone3000.Service(b'')
    Window.more = (f'--tone3000={service.address}',)
    window = Window(bundle, output, identity)
    cdp, out, quiet = window.cdp, {}, 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'
    toasts = page_check.TOASTS
    authorize = service.address + '/api/v1/oauth/authorize'
    try:
        window.wait('window.__urOk === true && !!document.getElementById("t3kBrowse")', 'the page', 40)
        service.nam = cdp.evaluate('(' + page_check.NAM.replace('__NAME__', 'Plexi') + ').text()').encode()
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        cdp.evaluate('void connect()')
        window.wait(quiet + ' && typeof lvlTimer !== "undefined" && !!lvlTimer', 'the connection', 60)
        time.sleep(1.2)
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        if cdp.evaluate('fetch("zoom").then(r => r.json()).then(s => !!s.installer)'):
            # with a pedal connected the line that asks for one is gone; the way to the installer is in the settings
            seen = cdp.evaluate('!!document.querySelector("#hrFirmware button") && !document.getElementById("hrFwBtn") && document.getElementById("miniPortStatus").hidden')
            require(seen, 'the way to the installer is not in the settings with a pedal connected')
        # the whole row of a preset is pressed, not only its name, and the buttons of the row keep their own place
        row = cdp.evaluate('(() => { const r = document.querySelector(".pslot"), b = r.getBoundingClientRect(), at = (x, y) => document.elementFromPoint(x, y);'
                           ' const k = r.querySelector(".k").getBoundingClientRect(), a = r.querySelector(".acts").getBoundingClientRect();'
                           ' const left = at(k.left + 4, k.top + 4), mid = at(b.left + b.width * .75 > a.left ? a.left - 8 : b.left + b.width * .6, b.top + b.height / 2), btn = at(a.left + a.width / 2, a.top + a.height / 2);'
                           ' return [getComputedStyle(left).cursor, left.closest(".n") ? "name" : left.className, mid && mid.closest(".n") ? "name" : String(mid && mid.className), [...r.querySelectorAll(".acts .btn")].some(e => e.offsetParent) ? !!(btn && btn.closest(".acts")) : true]; })()')
        require(row[0] == 'pointer' and row[1] == 'name' and row[2] == 'name' and row[3] is True, f'the row of a preset: {row}')

        def library(kind):
            cdp.evaluate(f'void openLib("{kind}")')
            window.wait('document.getElementById("lib").classList.contains("on") && !document.getElementById("t3kBrowse").hidden && !document.getElementById("t3kBrowse").disabled', 'Browse TONE3000')

        def shut():
            cdp.evaluate('if (document.getElementById("lib").classList.contains("on")) closeLib()')
            time.sleep(0.4)
        library('cap')
        time.sleep(0.5)
        cdp.screenshot(output / 't3k-library.png')
        require(not service.asked, 'TONE3000 was asked before the button was pressed')
        # the first word, and no
        cdp.evaluate('document.getElementById("t3kBrowse").click()')
        window.wait('!!document.querySelector("dialog.t3k[open]")', 'the first word')
        cdp.screenshot(output / 't3k-hello.png')
        cdp.evaluate('[...document.querySelectorAll("dialog.t3k button")].find(b => b.textContent === "Not now").click()')
        time.sleep(0.6)
        require(not service.asked and not window.others(authorize), 'Not now went on')
        # yes: the sign-in window, locked in as the page is, and only for the web
        cdp.evaluate('document.getElementById("t3kBrowse").click()')
        window.wait('!!document.querySelector("dialog.t3k[open]")', 'the first word')
        cdp.evaluate('[...document.querySelectorAll("dialog.t3k button")].find(b => b.textContent === "Continue to TONE3000").click()')
        tone = window.other(authorize, 'the sign-in window')
        out['address'] = tone.evaluate('[origin, document.title, !!document.getElementById("use")]')
        out['window'] = tone.evaluate("""(async () => [typeof require, typeof process, typeof navigator.serial === "undefined" ? -1 : (await navigator.serial.getPorts()).length,
            await fetch("hyperrig://editor/tone3000/status").then(() => "answered", () => "refused"), localStorage.getItem("hr.t3k.hello")])()""")
        require(out['window'] == ['undefined', 'undefined', 0, 'refused', None], f"the sign-in window: {out['window']}")
        for link in ('out', 'file'):
            tone.evaluate(f'document.getElementById("{link}").click()')
            time.sleep(0.6)
            require(tone.evaluate('location.href').startswith(authorize), f'the sign-in window went {link}')
        tone.evaluate('document.getElementById("use").click()')
        window.wait('!!document.querySelector("dialog.t3k[open] .thead")', 'the tone that was chosen', 30)
        require(not window.others(authorize), 'the sign-in window stayed open')
        out['shown'] = cdp.evaluate('[document.querySelector("dialog.t3k h2").textContent, document.querySelector("dialog.t3k .tmeta").innerText.replace(/\\n+/g, " | "), [...document.querySelectorAll("dialog.t3k .tlist label")].map(l => l.innerText.trim().replace(/\\s+/g, " "))]')
        require(out['shown'][0] == 'Plexi Crunch' and 'amp.maker' in out['shown'][1] and 'CC BY' in out['shown'][1] and out['shown'][2] == ['Clean standard', 'Crunch lite'], f"shown: {out['shown']}")
        time.sleep(0.5)
        cdp.screenshot(output / 't3k-choose.png')
        cdp.evaluate('document.querySelectorAll("dialog.t3k input[type=radio]")[1].click()')
        cdp.evaluate('[...document.querySelectorAll("dialog.t3k button")].find(b => b.textContent === "Load into the pedal").click()')
        window.wait('!!__pedal.caps[0] && capJobs === null && ' + quiet, 'the capture on the pedal', 180)
        window.wait('!!document.querySelector("#libL .lslot[data-slot=\\"0\\"] .t3kline")', 'the creator beside the slot', 15)
        out['capture'] = cdp.evaluate('[__pedal.caps[0].name, document.querySelector("#libL .t3kline").innerText.trim(), document.querySelector("#libL .t3kline").href]')
        require('amp.maker' in out['capture'][1] and 'CC BY' in out['capture'][1] and out['capture'][2] == 'https://www.tone3000.com/tones/77', f"beside the slot: {out['capture']}")
        cdp.screenshot(output / 't3k-loaded.png')
        shut()
        window.wait('!!document.querySelector("#chain .amp .t3kmark")', 'the mark on the amp', 15)
        cdp.click('[data-id="amp"]')
        window.wait('!!document.querySelector("#editor .t3kcard")', 'the tone in the amp panel', 15)
        time.sleep(0.4)
        cdp.screenshot(output / 't3k-amp.png')
        # tried without a slot: the models of the tone one after the other, each fetched once when it is asked for; back; then kept, with its creator beside it
        shut()
        cdp.evaluate('void loadPresets()')
        window.wait(quiet, 'a quiet page')
        slots, n = cdp.evaluate('Object.keys(__pedal.caps).join()'), len(service.asked)
        cdp.evaluate('__pedal.sent.length = 0; window.__said = []; { const f = toast; toast = (m, ...more) => { __said.push(String(m)); return f(m, ...more); }; }')
        library('cap')
        cdp.evaluate('document.getElementById("t3kBrowse").click()')
        window.other(authorize, 'the window to try one').evaluate('document.getElementById("use").click()')
        window.wait('!!document.querySelector("dialog.t3k[open] .thead")', 'the tone to try', 30)
        cdp.screenshot(output / 't3k-try.png')
        cdp.evaluate('[...document.querySelectorAll("dialog.t3k button")].find(b => b.textContent === "Try it").click()')
        playing = 'hrTry.state === "playing" && !hrTry.volume.rising && ' + quiet
        window.wait(playing, 'the first model', 180)
        seen = cdp.evaluate('[document.getElementById("hrTry").innerText.replace(/\\s+/g, " "), document.querySelector("#hrTry a").href, __pedal.cap_slot]')
        require('Plexi Crunch Clean' in seen[0] and 'amp.maker' in seen[0] and 'CC BY' in seen[0] and seen[1] == 'https://www.tone3000.com/tones/77' and seen[2] == -1, f'the first model: {seen}')
        cdp.screenshot(output / 't3k-trying.png')
        for label, at in (('Next', 1), ('Previous', 0), ('Next', 1)):
            cdp.evaluate(f'[...document.querySelectorAll("#hrTry button")].find(b => b.textContent === "{label}").click()')
            window.wait(f'hrTry.at === {at} && ' + playing, label, 120)
        fetched = [a[1] for a in service.asked[n:] if '/download' in a[1]]
        require(fetched == ['/api/v1/models/1/download', '/api/v1/models/2/download'], f'a model is fetched more than once, or before it is asked for: {fetched}')
        require(cdp.evaluate('Object.keys(__pedal.caps).join()') == slots and not cdp.evaluate('__pedal.sent.some(c => /^(CSAVE|PSAVE|ISAVE|CDEL)/.test(c))'), 'a try wrote to the pedal')
        cdp.evaluate('void hrTry.back()')
        window.wait('hrTry.state === "off" && ' + quiet, 'back', 60)
        require(cdp.evaluate('__pedal.cap_slot') == 0 and any('as it was' in x for x in cdp.evaluate('__said')), f"back: {cdp.evaluate('[__pedal.cap_slot, __said]')}")
        library('ir')
        cdp.evaluate('document.getElementById("t3kBrowse").click()')
        window.other(authorize, 'the window to try an IR').evaluate('document.getElementById("use").click()')
        window.wait('!!document.querySelector("dialog.t3k[open] .thead")', 'the IR to try', 30)
        cdp.evaluate('[...document.querySelectorAll("dialog.t3k button")].find(b => b.textContent === "Try it").click()')
        window.wait(playing, 'the IR that is tried', 120)
        require(cdp.evaluate('Object.keys(__pedal.irs).length') == 0 and cdp.evaluate('__pedal.ir.n') > 1000, 'the IR that is tried')
        cdp.evaluate('void hrTry.keep()')
        window.wait('!!document.querySelector(".mdlg .mdlg-ok")', 'where to keep it', 15)
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok").click()')
        window.wait('hrTry.state === "off" && !!__pedal.irs[0] && ' + quiet, 'kept', 30)
        kept = cdp.evaluate('JSON.parse(localStorage.getItem("hr.t3k.slots"))["ir:0"]')
        require(kept['creator'] == 'amp.maker' and kept['name'] == cdp.evaluate('__pedal.irs[0].name'), f'what is noted beside it: {kept}')
        cdp.evaluate('void (async () => { await Pedal.cmd("IDEL 0", "IDEL", 5000); window.__t3kdel = true; })()')
        window.wait('window.__t3kdel === true && ' + quiet, 'the IR of the try taken away')
        out['tried'] = {'fetched': fetched, 'bar': seen[0]}
        downloads = [a for a in service.asked[:n] if '/download' in a[1] or '/files/' in a[1]]
        require([d[1] for d in downloads] == ['/api/v1/models/2/download', '/api/v1/files/2'], f'more was fetched than was asked for: {downloads}')
        # an impulse response: signed in already, no first word
        library('ir')
        cdp.evaluate('document.getElementById("t3kBrowse").click()')
        window.other(authorize, 'the window for IRs').evaluate('document.getElementById("use").click()')
        window.wait('!!document.querySelector("dialog.t3k[open] .thead")', 'the IR that was chosen', 30)
        cdp.evaluate('[...document.querySelectorAll("dialog.t3k button")].find(b => b.textContent === "Load into the pedal").click()')
        window.wait('!!__pedal.irs[0] && capJobs === null && ' + quiet, 'the IR on the pedal', 60)
        window.wait('!!document.querySelector("#libL .t3kline")', 'the creator beside the IR', 15)
        out['ir'] = cdp.evaluate('[__pedal.irs[0].name, __pedal.irs[0].n]')
        require(out['ir'][0] == 'Greenback 4x12' and out['ir'][1] > 1000, f"the IR: {out['ir']}")
        # cancel, another state, and the window closed: nothing is loaded
        before = cdp.evaluate('Object.keys(__pedal.irs).length')
        for how, say in (('cancel', None), ('wrong', 'came back with something else'), ('close', None)):
            cdp.evaluate(toasts + '.forEach(e => e.remove())')
            window.wait('!document.getElementById("t3kBrowse").disabled', 'the button again')
            cdp.evaluate('document.getElementById("t3kBrowse").click()')
            tone = window.other(authorize, how)
            if how == 'close':
                tone.call('Page.close')
            else:
                tone.evaluate(f'document.getElementById("{how}").click()')
            window.wait('!document.getElementById("t3kBrowse").disabled', how, 20)
            time.sleep(0.4)
            require(not cdp.evaluate('!!document.querySelector("dialog.t3k[open]")') and not window.others(authorize), f'{how}: something stayed open')
            if say:
                require(cdp.evaluate(toasts + f'.some(e => e.innerText.includes({json.dumps(say)}))'), f'{how}: it was not said')
        require(cdp.evaluate('Object.keys(__pedal.irs).length') == before, 'something was loaded')
        # sign out: the tokens are gone, the notes beside the slots stay
        kept = window.profile / 'tone3000.bin'
        require(kept.is_file() and b'refresh' not in kept.read_bytes() and not any(r.encode() in kept.read_bytes() for r in service.refresh), 'the sign-in is kept as it is')
        shut()
        cdp.evaluate('document.getElementById("setBtn").click()')
        window.wait('!document.getElementById("t3kOut").hidden', 'the sign-out')
        time.sleep(0.4)
        cdp.screenshot(output / 't3k-settings.png')
        cdp.evaluate('document.getElementById("t3kOut").click()')
        window.wait('document.getElementById("t3kOut").hidden', 'signed out')
        require(not kept.exists(), 'the sign-in stayed on the disk')
        require(not service.problems and all(a[3] is None or a[3].startswith('Bearer a') for a in service.asked), f'what was asked: {service.problems}')
        out['requests'] = len(service.asked)
        errors = cdp.evaluate('__errors')
        require(not errors, f'page errors: {errors}')
        return out
    finally:
        Window.more = ()
        window.close()
        service.close()


def patchstorage(program, bundle, output):
    """Browse Patchstorage as a person does, against a simulated one: look, search, more, one preset; try it, save its file, keep it; what is wrong there; the way to share."""
    product = json.loads((Path(bundle) / 'editor/profile.json').read_bytes())['development']['product']
    text, _, _ = check_mini_try.document()
    service = simulated_patchstorage.Service(text)
    Window.more = (f'--patchstorage={service.address}',)
    window = Window(bundle, output, f"HRID 1 {product['version']} {product['build_id']} banks=3")
    cdp, out, s = window.cdp, {}, check_mini_try.Steps(window, output)
    dialog = 'document.querySelector("dialog.hrsh[open]")'

    def press(label):
        done = cdp.evaluate(f'(() => {{ const b = [...{dialog}.querySelectorAll("button, a.btn")].find(e => e.offsetParent && e.textContent.trim() === {json.dumps(label)} && !e.disabled); if (b && b.tagName === "BUTTON") b.click(); return !!b; }})()')
        require(done, f"no button {label}: {cdp.evaluate(dialog + '?.innerText')}")

    def shown(words, what):
        s.wait(f'!!{dialog} && {dialog}.innerText.includes({json.dumps(words)})', what, 20)
    try:
        window.wait('window.__urOk === true && !!document.getElementById("hrShare")', 'the page', 40)
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        cdp.evaluate(check_mini_try.MORE)
        cdp.evaluate('window.__said = []; { const f = toast; toast = (m, ...more) => { __said.push(String(m)); return f(m, ...more); }; }')
        cdp.evaluate('void connect()')
        window.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer', 'the connection', 60)
        time.sleep(1.5)
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        s.ready()
        height = cdp.evaluate('[...document.querySelectorAll("#hrWays button")].map(b => [b.getAttribute("aria-label") || b.innerText, Math.round(b.getBoundingClientRect().height)])')
        require([h[0] for h in height] == ['Try from files\u2026', 'Browse Patchstorage'] and all(38 <= h[1] <= 46 for h in height), f'the ways in: {height}')
        logo = cdp.evaluate('(i => i ? [i.complete && i.naturalWidth, Math.round(i.getBoundingClientRect().height), i.alt] : null)(document.querySelector("#hrShare img"))')
        require(logo == [456, 15, ''], f"Patchstorage's logo on its button: {logo}")
        cdp.screenshot(output / 'share-way-in.png')
        require(not service.asked, 'Patchstorage was asked before the button was pressed')
        mark = s.mark()
        # the list, a page at a time; a search
        cdp.evaluate('document.getElementById("hrShare").click()')
        shown('Edge of breakup', 'the list')
        out['first'] = cdp.evaluate(f'[{dialog}.querySelectorAll(".hrshrow").length, {dialog}.querySelector(".hrshn").textContent, {dialog}.querySelector(".hrshrow").innerText]')
        require(out['first'][0] == 20 and out['first'][1] == '20 of 34' and 'by Preset Maker' in out['first'][2] and len(service.asked) == 1, f"the list: {out['first']}, {service.asked}")
        require(not cdp.evaluate(f'!!{dialog}.querySelector("img")') and 'Nothing & inside <img' in cdp.evaluate(dialog + '.innerText'), 'a title became part of the page')
        cdp.screenshot(output / 'share-list.png')
        press('More')
        s.wait(f'{dialog}.querySelectorAll(".hrshrow").length === 34', 'more')
        require(not cdp.evaluate(f'[...{dialog}.querySelectorAll("button")].some(b => b.offsetParent && b.textContent === "More")'), 'More after the last')
        cdp.evaluate(f'{dialog}.querySelector("input[type=search]").value = "edge"; {dialog}.querySelector("form").requestSubmit()')
        s.wait(f'{dialog}.querySelectorAll(".hrshrow").length === 1', 'a search')
        # one preset: who, which licence; nothing is fetched yet
        cdp.evaluate(f'{dialog}.querySelector(".hrshrow").click()')
        shown('Creative Commons Attribution 4.0', 'one preset')
        out['one'] = cdp.evaluate(dialog + '.innerText')
        require(all(x in out['one'] for x in ('Edge of breakup', 'Preset Maker', 'A test preset.', 'crunch.hyperrig.json', 'broken.json')) and 'read-me' not in out['one'] and not any('/files/' in a for a in service.asked), f"one preset: {out['one']}")
        require(cdp.evaluate(f'[...{dialog}.querySelectorAll("a")].map(a => a.href)') == ['https://patchstorage.com/preset-70/'], 'its address')
        cdp.screenshot(output / 'share-one.png')
        s.same(mark, 'looking')
        # a file that is no preset, then the right one: what it lacks is shown, and it is tried
        cdp.evaluate(f'{dialog}.querySelectorAll("input[type=radio]")[1].click()')
        press('Try it')
        shown('This file is not a HyperRig preset.', 'a wrong file')
        cdp.evaluate(f'{dialog}.querySelectorAll("input[type=radio]")[0].click()')
        press('Try it')
        listed = s.dialog('Try 3 presets')
        require('by Preset Maker' in listed and 'Creative Commons' in listed and 'wonderfx' in listed, f'the list before trying: {listed}')
        s.ev('document.querySelectorAll(".mdlg input[type=radio]")[1].click()')
        s.press('Try')
        s.playing('a preset from there')
        bar = cdp.evaluate('[document.getElementById("hrTry").innerText.replace(/\\s+/g, " "), document.querySelector("#hrTry a").href]')
        require('With its files' in bar[0] and 'Preset Maker' in bar[0] and 'Creative Commons' in bar[0] and bar[1] == 'https://patchstorage.com/preset-70/', f'the bar: {bar}')
        cdp.screenshot(output / 'share-trying.png')
        s.same(mark, 'a preset from there', heard=False)
        require(sum('/files/' in a for a in service.asked) == 2, f'more files than were asked for: {service.asked}')
        # kept, with its creator beside it
        s.bar('Keep\u2026')
        s.dialog('Save this preset')
        slot = s.ev('+document.querySelector(".mdlg select").value')
        s.press('Save')
        s.dialog('Keep the cab IR too')
        s.press('Only the preset')
        s.dialog('Keep the capture too')
        s.press('Only the preset')
        s.off('kept')
        s.wait(f'curPreset === {slot} && !!document.querySelector("#pList .pslot[data-preset=\\"{slot}\\"] .hrfrom")', 'its creator beside it', 20)
        out['beside'] = cdp.evaluate('[document.querySelector("#pList .hrfrom").innerText, document.querySelector("#pList .hrfrom").href]')
        require(out['beside'] == ['by Preset Maker \u00b7 Creative Commons Attribution 4.0', 'https://patchstorage.com/preset-70/'], f"beside it: {out['beside']}")
        cdp.screenshot(output / 'share-kept.png')
        # the file, with where it comes from inside, and it can be read back
        cdp.evaluate('document.getElementById("hrShare").click()')
        shown('Moved', 'the list again')
        cdp.evaluate(f'[...{dialog}.querySelectorAll(".hrshrow")].find(b => b.innerText.startsWith("Moved")).click()')
        shown('Creative Commons Attribution 4.0', 'a preset whose file is moved')
        press('Save the file\u2026')
        shown('Saved, with its creator', 'saved')
        saved = window.profile / 'saved'
        deadline = time.monotonic() + 15
        while not (saved.is_dir() and [p for p in saved.iterdir() if p.suffix == '.json' and p.stat().st_size]):
            require(time.monotonic() < deadline, 'the file is not saved')
            time.sleep(0.2)
        path = next(saved.iterdir())
        doc = json.loads(path.read_bytes())
        out['saved'] = [path.name, doc['presets'][0]['meta']['origin'], sorted(doc['attachments'])]
        require(path.name == 'Moved.hyperrig.json' and out['saved'][1] == {'title': 'Moved', 'creator': 'Preset Maker', 'license': 'Creative Commons Attribution 4.0', 'address': 'https://patchstorage.com/preset-80/'} and out['saved'][2] == ['cap1', 'ir1'],
                f"the file: {out['saved']}")
        back = cdp.evaluate(f'(() => {{ const r = hrTry.presetItems({json.dumps(path.read_text(encoding="utf-8"))}); return [r.items.length, r.items[0].by, r.items[0].license, r.items[0].address]; }})()')
        require(back == [3, 'Preset Maker', 'Creative Commons Attribution 4.0', 'https://patchstorage.com/preset-80/'], f'read back: {back}')
        press('To the list')
        # sent away to another place, nothing inside: said, and nothing is loaded
        cdp.evaluate(f'[...{dialog}.querySelectorAll(".hrshrow")].find(b => b.innerText.startsWith("Sent away")).click()')
        shown('To the list', 'a preset that is sent away')
        press('Try it')
        shown('Patchstorage has a problem', 'a file elsewhere')
        press('To the list')
        cdp.evaluate(f'[...{dialog}.querySelectorAll(".hrshrow")].find(b => b.innerText.startsWith("Nothing")).click()')
        shown('It has no HyperRig preset file.', 'a preset without a file')
        press('To the list')
        # the way to share one's own: their page, in the browser
        press('Share your own\u2026')
        shown('does not see your account', 'the way to share')
        links = cdp.evaluate(f'[...{dialog}.querySelectorAll("a")].map(a => [a.href, a.target])')
        require(links == [['https://patchstorage.com/upload-a-patch/', '_blank']] * 2 and not cdp.evaluate(f'!!{dialog}.querySelector("input[type=password]")'), f'the links: {links}')
        cdp.screenshot(output / 'share-own.png')
        press('To the list')
        press('Close')
        s.wait('!document.querySelector("dialog.hrsh")', 'closed')
        # no answer
        service.close()
        cdp.evaluate('document.getElementById("hrShare").click()')
        shown('could not be reached', 'no Patchstorage')
        press('Close')
        require(not service.problems, f'what was asked: {service.problems}')
        out['requests'] = len(service.asked)
        errors = cdp.evaluate('__errors')
        require(not errors, f'page errors: {errors}')
        return out
    except Exception:
        cdp.screenshot(output / 'share-failure.png')
        raise
    finally:
        Window.more = ()
        window.close()


def way_to_the_update(bundle, output):
    """A pedal with an older HyperRig: the notice of the page leads to the installer, and the pedal's port is closed first."""
    window = Window(bundle, output, 'HRID 1 0.0.1 0123456789abcdef banks=3')
    cdp = window.cdp
    try:
        window.wait('window.__urOk === true && !!document.getElementById("hrFirmware")', 'the page', 40)
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        cdp.evaluate('void connect()')
        window.wait('!!document.querySelector(".mdlg-ok") && S.connected', 'the notice', 60)
        seen = cdp.evaluate('[document.querySelector(".mdlg-ok").textContent, document.querySelector(".mdlg-cancel").textContent]')
        require(seen == ['Update now', 'Not now'], f'the buttons of the notice: {seen}')
        window.wait('document.querySelector("#hrOther button")?.textContent === "Update now"', 'the button of the bar', 10)
        cdp.evaluate('localStorage.removeItem("check_closed"); { const d = Pedal.disconnect; Pedal.disconnect = async function () { await d.call(Pedal); localStorage.setItem("check_closed", String(!Pedal.tr.isOpen())); }; }')
        cdp.evaluate('document.querySelector(".mdlg-ok").click()')
        window.wait('location.href.startsWith("hyperrig://installer/")', 'the installer', 20)
        cdp.call('Page.navigate', {'url': START})
        window.wait('location.href.startsWith("hyperrig://editor/") && window.__urOk === true', 'the editor again', 20)
        require(cdp.evaluate('localStorage.getItem("check_closed")') == 'true', 'the port is not closed before the installer opens')
        return {'buttons': seen, 'port_closed': True}
    finally:
        window.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--program', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--locks-only', action='store_true')
    parser.add_argument('--only', choices=('tone3000', 'patchstorage'))
    args = parser.parse_args(argv)
    made = desktop.check(args.program)
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    output.mkdir(parents=True)
    program = Path(made['directory']) / (desktop.PROGRAM + '.exe')
    Window.program = program
    for test in ('test_rules.js', 'test_tone3000.js', 'test_patchstorage.js'):
        rules = subprocess.run(['node', 'app/desktop/' + test], cwd=ROOT, capture_output=True, text=True)
        require(rules.returncode == 0, rules.stderr)
    if args.only:
        print(json.dumps({'tone3000': tone3000, 'patchstorage': patchstorage}[args.only](program, ROOT / json.loads((Path(args.program) / 'desktop.json').read_bytes())['bundle'], output), indent=1))
        return 0
    report = {'kind': 'hyperrig-desktop-editor-check', 'program': str(args.program), 'device_io': False, 'rules': rules.stdout.strip(),
              'locks': locks(program, output)}
    if not args.locks_only:
        bundle = ROOT / json.loads((Path(args.program) / 'desktop.json').read_bytes())['bundle']
        session = page_check.run(bundle, output / 'session', Window)
        report['session'] = {k: v for k, v in session.items() if k != 'sent'}
    if not args.locks_only:
        if json.loads((Path(args.program) / 'desktop.json').read_bytes()).get('installer'):
            report['way_to_the_update'] = way_to_the_update(bundle, output)
        report['tone3000'] = tone3000(program, bundle, output)
        report['patchstorage'] = patchstorage(program, bundle, output)
    report['result'] = 'pass'
    (output / 'desktop-report.json').write_bytes(desktop.editor.encoded(report))
    print(json.dumps({'result': 'pass', 'locks': report['locks'], 'session_steps': sorted(report.get('session', {}).get('steps', {})), 'tone3000': report.get('tone3000'), 'patchstorage': report.get('patchstorage')}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
