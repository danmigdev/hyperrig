"""Exercise the generated MINI editor in an isolated local Chromium browser.

No hardware, device chooser, personal profile or external network access.
Requires an already installed Chromium browser and websocket-client. The local
server and browser are stopped on exit; screenshots/reports stay in build/.
"""
from __future__ import annotations

import argparse
import base64
from functools import partial
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from urllib.request import urlopen

import websocket

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Permissions-Policy", "serial=(), usb=(), bluetooth=(), midi=(), camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "connect-src 'self'; frame-src 'none'; object-src 'none'; font-src 'self' data:; img-src 'self' data: blob:")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *_):
        pass

    def do_POST(self):
        # Original editor can submit diagnostics to its own local origin.
        # Never persist or forward their contents.
        self.send_response(204)
        self.end_headers()


GUARD = r"""(() => {
  const calls = [];
  const record = (name, value) => async () => { calls.push(name); return value; };
  const reject = name => async () => { calls.push(name); throw new DOMException('Offline browser probe blocks hardware', 'NotAllowedError'); };
  const events = {addEventListener(){}, removeEventListener(){}};
  Object.defineProperty(navigator, 'serial', {configurable:true, value:{...events, getPorts:record('serial.getPorts:stub', []), requestPort:reject('serial.requestPort:blocked')}});
  Object.defineProperty(navigator, 'usb', {configurable:true, value:{...events, getDevices:record('usb.getDevices:stub', []), requestDevice:reject('usb.requestDevice:blocked')}});
  Object.defineProperty(navigator, 'bluetooth', {configurable:true, value:{...events, getAvailability:record('bluetooth.getAvailability:stub', false), getDevices:record('bluetooth.getDevices:stub', []), requestDevice:reject('bluetooth.requestDevice:blocked')}});
  Object.defineProperty(navigator, 'requestMIDIAccess', {configurable:true, value:reject('midi.requestMIDIAccess:blocked')});
  window.__miniBrowserProbe = {calls, hardwareAPIsStubbed:true};
  localStorage.setItem('hyperrig.updateOff', '1');
})();"""


SNAPSHOT = r"""(() => {
 const visible = e => !!e && !e.hidden && e.getBoundingClientRect().width > 0 && e.getBoundingClientRect().height > 0 && getComputedStyle(e).visibility !== 'hidden';
 return {title:document.title,url:location.href,ready:window.__urOk===true,secure:isSecureContext,
  width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,
  status:document.getElementById('miniPortStatus')?.textContent,
  demo:typeof DEMO!=='undefined'&&DEMO,connected:typeof S!=='undefined'&&S.connected,
  profile:typeof HyperRigMini!=='undefined'?HyperRigMini.profile:null,
  hardware:window.__miniBrowserProbe,
  buttons:[...document.querySelectorAll('button')].filter(visible).map(e=>({id:e.id,text:e.innerText.trim(),label:e.getAttribute('aria-label'),disabled:e.disabled,cls:e.className})).slice(0,90),
  chain:[...document.querySelectorAll('#chain [data-id]')].map(e=>({id:e.dataset.id,text:e.innerText,cls:e.className})),
  editor:document.getElementById('editor')?.innerText,
  dialogs:[...document.querySelectorAll('[role=dialog],dialog,.tour-call,.mdlg-back')].filter(visible).map(e=>({id:e.id,cls:e.className,text:e.innerText.slice(0,1000)}))};
})()"""


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=12, suppress_origin=True)
        self.next_id = 1
        self.events = []

    def call(self, method, params=None):
        message_id = self.next_id
        self.next_id += 1
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            value = json.loads(self.ws.recv())
            if value.get("id") == message_id:
                if "error" in value:
                    raise ValueError(f"{method}: {value['error']}")
                return value.get("result", {})
            self.events.append(value)

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
        require("exceptionDetails" not in result, f"browser evaluation failed: {result}")
        return result.get("result", {}).get("value")

    def click(self, selector):
        box = self.evaluate("(() => {const e=document.querySelector(" + json.dumps(selector) + "); if(!e)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,width:r.width,height:r.height,disabled:!!e.disabled}})()")
        require(box and box["width"] > 0 and box["height"] > 0 and not box["disabled"], f"unavailable button {selector}")
        for kind in ("mousePressed", "mouseReleased"):
            self.call("Input.dispatchMouseEvent", {"type": kind, "x": box["x"], "y": box["y"], "button": "left", "clickCount": 1})
        time.sleep(0.15)

    def screenshot(self, path):
        data = self.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        path.write_bytes(base64.b64decode(data["data"]))
        return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path.read_bytes())}


def browser_path():
    roots = (os.environ.get("PROGRAMFILES", "C:/Program Files"), os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
    for root in roots:
        for suffix in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
            candidate = Path(root) / suffix
            if candidate.is_file():
                return candidate
    raise FileNotFoundError("No existing Chrome/Edge found; nothing is installed automatically")


def run(app_dir, output, browser=None):
    app_dir, output = Path(app_dir).resolve(), Path(output).resolve()
    require(app_dir.is_relative_to(ROOT) and (app_dir / "tankmini.html").is_file(), "local generated editor required")
    require(output.is_relative_to(ROOT / "build") and not output.exists(), "new output directory under build/ required")
    output.mkdir(parents=True)
    profile = output / "browser-profile"
    profile.mkdir()
    browser = browser_path() if browser is None else Path(browser).resolve()
    report = {"schema": 1, "browser_executable": str(browser), "app_directory": app_dir.relative_to(ROOT).as_posix(),
              "source_sha256": {p.name: digest(p.read_bytes()) for p in app_dir.iterdir() if p.is_file()},
              "browser_personal_profile_used": False, "device_access": False,
              "hardware_permissions_denied_by_server": True, "hardware_methods_stubbed_before_page_script": True,
              "external_network_blocked": True, "scenarios": [], "errors": []}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(app_dir)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    process, cdp = None, None
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        args = [str(browser), "--headless=new", "--no-first-run", "--no-default-browser-check",
                "--disable-background-networking", "--disable-component-update", "--disable-sync",
                "--disable-features=MediaRouter,OptimizationHints", "--disable-extensions",
                "--disable-default-apps", "--disable-breakpad", "--noerrdialogs", "--window-size=1440,1000",
                "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost",
                "--user-data-dir=" + str(profile), "about:blank"]
        with (output / "browser-stderr.txt").open("wb") as stderr:
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=stderr,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        endpoint = profile / "DevToolsActivePort"
        for _ in range(100):
            if endpoint.is_file():
                break
            require(process.poll() is None, "browser exited before CDP")
            time.sleep(0.1)
        require(endpoint.is_file(), "CDP did not become available")
        port = int(endpoint.read_text().splitlines()[0])
        devtools = f"http://127.0.0.1:{port}"
        get = lambda tail: json.loads(urlopen(devtools + tail, timeout=5).read())
        report["browser_version"] = get("/json/version")
        protocol = get("/json/protocol")
        report["device_access_protocol"] = next((d for d in protocol["domains"] if d["domain"] == "DeviceAccess"), None)
        page = next(p for p in get("/json/list") if p["type"] == "page")
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.call("Runtime.enable")
        cdp.call("Page.enable")
        cdp.call("Log.enable")
        cdp.call("Page.addScriptToEvaluateOnNewDocument", {"source": GUARD})
        for mode in ("readonly", "demo"):
            cdp.call("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
            # A changed query forces a new document; changing only #demo would
            # keep the previous page's const DEMO and skip the demo bootstrap.
            cdp.call("Page.navigate", {"url": origin + "/tankmini.html?browser_probe=" + mode + ("#demo" if mode == "demo" else "")})
            for _ in range(100):
                if cdp.evaluate("window.__urOk===true && !!document.getElementById('miniPortStatus') && location.search===" + json.dumps("?browser_probe=" + mode)):
                    break
                time.sleep(0.05)
            snapshot = cdp.evaluate(SNAPSHOT)
            require(snapshot["ready"], f"editor failed to finish boot: {mode}")
            require(snapshot["title"] == "HyperRig for TANK MINI", "unexpected editor title")
            require(snapshot["profile"]["image_sha256"] == "3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff", "unexpected firmware binding")
            scenario = {"name": mode, "initial": snapshot}
            # The stock editor schedules first-use onboarding at 400 ms.
            time.sleep(0.55)
            if cdp.evaluate("!!document.querySelector('.ccall .tskip')"):
                scenario["onboarding_visible"] = True
                cdp.click(".ccall .tskip")
                require(cdp.evaluate("!document.body.classList.contains('touring')"), "tour did not close")
            scenario["desktop"] = cdp.evaluate(SNAPSHOT)
            scenario["desktop_screenshot"] = cdp.screenshot(output / f"{mode}-desktop.png")
            cdp.click("#setBtn")
            require(cdp.evaluate("document.getElementById('settings').getAttribute('aria-hidden')==='false'"), "settings drawer did not open")
            scenario["settings_opened"] = True
            cdp.click("#setX")
            # Preserve DOM state for review before selecting a safe offline control.
            if mode == "demo":
                cdp.click("#chain [data-id='0']")
                edited = cdp.evaluate(SNAPSHOT)
                require(edited.get("editor") and "DRIVE" in edited["editor"].upper(), "demo FX editor did not open")
                scenario["selected_effect"] = edited
                scenario["effect_screenshot"] = cdp.screenshot(output / "demo-effect-desktop.png")
                before = cdp.evaluate("Number(document.querySelector('#editor [role=slider]').getAttribute('aria-valuenow'))")
                cdp.evaluate("document.querySelector('#editor [role=slider]').focus()")
                for kind in ("keyDown", "keyUp"):
                    cdp.call("Input.dispatchKeyEvent", {"type": kind, "key": "ArrowUp", "code": "ArrowUp", "windowsVirtualKeyCode": 38})
                time.sleep(0.15)
                after = cdp.evaluate("({ui:Number(document.querySelector('#editor [role=slider]').getAttribute('aria-valuenow')),state:S.chain.P.find(e=>e.id===0).p[0]})")
                require(after["ui"] == before + 1 and after["state"] == after["ui"], "demo knob did not update displayed and model values")
                scenario["keyboard_knob_change"] = {"before": before, "after": after}
                cdp.click("#edOn")
                require(cdp.evaluate("S.chain.P.find(e=>e.id===0).on===false"), "demo bypass did not change model")
                cdp.click("#edOn")
                require(cdp.evaluate("S.chain.P.find(e=>e.id===0).on===true"), "demo re-enable did not change model")
                scenario["effect_bypass_and_restore"] = True
                cdp.click("#snaps [data-snap='1']")
                require(cdp.evaluate("S.snap===1 && document.querySelector('#snaps [data-snap=\"1\"]').classList.contains('on')"), "demo scene did not change")
                scenario["scene_switch"] = {"selected": 1, "displayed": "Crunch"}
                cdp.click("#chain [data-id='amp']")
                cdp.click("#ampLoad")
                require(cdp.evaluate("document.getElementById('lib').classList.contains('on') && document.getElementById('libL').children.length>0"), "capture library did not render")
                scenario["capture_library"] = cdp.evaluate("({title:document.getElementById('libT').innerText,rows:document.getElementById('libL').children.length})")
                scenario["library_screenshot"] = cdp.screenshot(output / "demo-library.png")
                cdp.click("#libX")
                cdp.click("#presetBtn")
                require(cdp.evaluate("document.querySelectorAll('.pslot').length===4"), "demo preset bank not rendered")
                scenario["preset_bank"] = cdp.evaluate("[...document.querySelectorAll('.pslot')].map(e=>({preset:e.dataset.preset,text:e.innerText}))")
                # Close the sidebar via the same button before responsive checks.
                cdp.click("#presetBtn")
                cdp.click("#chain [data-id='0']")
            cdp.call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": False})
            time.sleep(0.25)
            scenario["mobile"] = cdp.evaluate(SNAPSHOT)
            require(scenario["mobile"]["scrollWidth"] <= scenario["mobile"]["width"], "mobile document has horizontal overflow")
            require(not scenario["mobile"]["hardware"]["calls"], "page attempted a hardware API during offline UI checks")
            scenario["mobile_screenshot"] = cdp.screenshot(output / f"{mode}-mobile.png")
            report["scenarios"].append(scenario)
        report["javascript_exceptions"] = [e["params"] for e in cdp.events if e.get("method") == "Runtime.exceptionThrown"]
        report["console_errors"] = [e["params"] for e in cdp.events if e.get("method") == "Runtime.consoleAPICalled" and e.get("params", {}).get("type") == "error"]
        report["browser_log"] = [e["params"] for e in cdp.events if e.get("method") == "Log.entryAdded"]
        require(not report["javascript_exceptions"], "uncaught JavaScript exception")
        report["result"] = "pass"
    except Exception as error:
        report["result"] = "fail"
        report["errors"].append(repr(error))
        if cdp:
            report["events_on_failure"] = cdp.events[-60:]
            try:
                report["failure_snapshot"] = cdp.evaluate(SNAPSHOT)
                report["failure_screenshot"] = cdp.screenshot(output / "failure.png")
            except Exception:
                pass
        raise
    finally:
        if cdp:
            try:
                cdp.call("Browser.close")
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
        report["local_server_stopped"] = True
        report["isolated_browser_stopped"] = process is None or process.poll() is not None
        (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", type=Path, default=ROOT / "build/hyperrig-mini-audio-v2/app/web")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser", type=Path)
    args = parser.parse_args()
    result = run(args.app_dir, args.output, args.browser)
    print(json.dumps({"result": result["result"], "output": str(args.output),
                      "javascript_exceptions": len(result["javascript_exceptions"]),
                      "device_access": False, "server_stopped": result["local_server_stopped"]}))


if __name__ == "__main__":
    main()
