"""Isolated editor browser: offline by default, explicit evidence-gated live mode.

No package installation or personal browser profile. Live mode only connects
after root has supplied a matching PONG/COM evidence file and its exact hash.
This module never opens a serial port from Python or probes devices itself.
"""
from __future__ import annotations

import argparse
from functools import partial
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.verify_mini_browser import CDP, browser_path

GUARD = ROOT / "tools/mini_browser_readonly_guard.js"
DEFAULT_APP = ROOT / "build/hyperrig-mini-audio-v2/app/web"
IMAGE_SHA = "3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff"
VERSION = "tankm_fw M5.71 rel ble"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_evidence(path, expected_sha256):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "local workspace evidence required")
    raw = path.read_bytes()
    require(re.fullmatch(r"[a-f0-9]{64}", expected_sha256 or "") and sha(raw) == expected_sha256,
            "physical evidence SHA256 differs")
    item = json.loads(raw)
    require(item.get("schema") == 1 and item.get("target") == "tank-mini" and item.get("transport") == "usb-cdc",
            "MINI USB physical evidence required")
    require(item.get("vid") == 0x3654 and item.get("pid") == 0x5155
            and re.fullmatch(r"COM[1-9][0-9]{0,3}", item.get("com", "")), "exact MINI VID/PID and Windows COM required")
    require(item.get("serial_port_closed") is True and item.get("image_sha256") == IMAGE_SHA,
            "reviewed image and closed diagnostic serial port required")
    pong = item.get("pong", "")
    require(isinstance(pong, str) and len(pong) <= 512 and not re.search(r"[\r\n\0]", pong)
            and re.match(r"^PONG " + re.escape(VERSION) + r" [A-Z][a-z]{2} [ 0-9][0-9] [0-9]{4}(?: |$)", pong),
            "exact observed MINI PONG line required")
    require(isinstance(item.get("observed_utc"), str) and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|\+00:00)", item["observed_utc"]),
        "UTC observation timestamp required")
    return item


def select_device(prompt, com, *, allow_missing=False):
    """CDP exposes names, not VID/PID. Exact COM token must be unique."""
    require(isinstance(prompt.get("id"), str) and isinstance(prompt.get("devices"), list), "malformed DeviceAccess prompt")
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(com) + r"(?![A-Za-z0-9])", re.IGNORECASE)
    matches = [item for item in prompt["devices"] if isinstance(item.get("id"), str)
               and isinstance(item.get("name"), str) and pattern.search(item["name"])]
    if not matches and allow_missing:
        return None
    require(len(matches) == 1, "chooser must contain exactly one entry with reviewed COM; no first-device fallback")
    return {"id": prompt["id"], "deviceId": matches[0]["id"]}


class LocalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, live=False, **kwargs):
        self.live = live
        super().__init__(*args, **kwargs)

    def end_headers(self):
        serial = "(self)" if self.live else "()"
        self.send_header("Permissions-Policy", f"serial={serial}, usb=(), bluetooth=(), midi=(), camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "connect-src 'self'; frame-src 'none'; object-src 'none'; font-src 'self' data:; img-src 'self' data: blob:")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_):
        pass


STATE = """(() => ({
 ready:window.__urOk===true, title:document.title, connected:typeof S!=='undefined'&&S.connected,
 connecting:typeof S!=='undefined'&&!!S.connecting, fw:typeof S!=='undefined'?S.fw:null,
 profile:typeof HyperRigMini!=='undefined'?HyperRigMini.profile:null,
 initialReadsFinished:typeof lvlTimer!=='undefined'&&!!lvlTimer,
 types:typeof S!=='undefined'?Object.keys(S.types).length:0,
 chain:typeof S!=='undefined'?S.chain:null, model:typeof S!=='undefined'?S.model:null,
 presets:[...document.querySelectorAll('.pslot')].map(x=>({id:x.dataset.preset,text:x.innerText})),
 status:document.getElementById('stat')?.textContent,
 guard:globalThis.__miniReadonlyGuard?.state
}))()"""


def run(app_dir, output, *, evidence=None, timeout=45):
    app_dir, output = Path(app_dir).resolve(), Path(output).resolve()
    require(app_dir.is_relative_to(ROOT) and (app_dir / "tankmini.html").is_file(), "local generated app required")
    require(output.is_relative_to(ROOT / "build") and not output.exists(), "new output directory under build required")
    require(type(timeout) is int and 10 <= timeout <= 60, "browser timeout must be10..60seconds")
    live = evidence is not None
    output.mkdir(parents=True)
    profile = output / "isolated-profile"
    profile.mkdir()
    report = {"schema": 1, "live_opt_in": live, "result": "running", "personal_profile_used": False,
              "app_directory": app_dir.relative_to(ROOT).as_posix(), "source_sha256": {
                  p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in [Path(__file__), GUARD,
                      ROOT / "tools/verify_mini_browser.py", *(p for p in app_dir.iterdir() if p.is_file())]},
              "hardware_evidence": evidence, "device_chooser_selected": False,
              "serial_port_opened": False, "mutating_commands_sent": False,
              "browser_guard_instrumented_in_memory": True, "app_files_modified": False}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(LocalHandler, directory=str(app_dir), live=live))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    process = cdp = None
    try:
        args = [str(browser_path()), "--headless=new", "--no-first-run", "--no-default-browser-check",
                "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-extensions",
                "--disable-features=MediaRouter,OptimizationHints", "--disable-default-apps", "--disable-breakpad",
                "--noerrdialogs", "--window-size=1440,1000", "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost",
                "--user-data-dir=" + str(profile), "about:blank"]
        with (output / "browser-stderr.txt").open("wb") as stream:
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=stream,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        endpoint = profile / "DevToolsActivePort"
        for _ in range(100):
            if endpoint.is_file(): break
            require(process.poll() is None, "browser exited before CDP")
            time.sleep(.1)
        require(endpoint.is_file(), "CDP unavailable")
        port = int(endpoint.read_text().splitlines()[0])
        devtools = f"http://127.0.0.1:{port}"
        get = lambda suffix: json.loads(urlopen(devtools + suffix, timeout=5).read())
        report["browser"] = get("/json/version")
        protocol = get("/json/protocol")
        report["device_access_schema"] = next((d for d in protocol["domains"] if d["domain"] == "DeviceAccess"), None)
        page = next(p for p in get("/json/list") if p["type"] == "page")
        cdp = CDP(page["webSocketDebuggerUrl"])
        for domain in ("Runtime", "Page", "Log"):
            cdp.call(domain + ".enable")
        config = {"live": live, "image_sha256": IMAGE_SHA, "pong": evidence["pong"] if live else None}
        cdp.call("Page.addScriptToEvaluateOnNewDocument", {"source": GUARD.read_text(encoding="utf-8")
                 + "\ninstallMiniBrowserReadonlyGuard(" + json.dumps(config) + ");"})
        origin = f"http://127.0.0.1:{server.server_port}"
        cdp.call("Page.navigate", {"url": origin + "/tankmini.html?readonly_browser_probe=1"})
        for _ in range(150):
            if cdp.evaluate("window.__urOk===true"): break
            time.sleep(.05)
        initial = cdp.evaluate(STATE)
        require(initial["ready"] and initial["title"] == "HyperRig for TANK MINI", "editor bootstrap failed")
        require(initial["profile"]["image_sha256"] == IMAGE_SHA and initial["profile"]["firmware_version"] == VERSION,
                "app firmware profile changed")
        cdp.evaluate("__miniReadonlyGuard.installApp(SerialTransport,Pedal,HyperRigMini.profile)")
        time.sleep(.55)
        if cdp.evaluate("!!document.querySelector('.ccall .tskip')"):
            cdp.click(".ccall .tskip")
        report["initial"] = cdp.evaluate(STATE)
        report["initial_screenshot"] = cdp.screenshot(output / "initial.png")
        if live:
            require(report["device_access_schema"] is not None, "DeviceAccess unavailable; no manual/fallback port selection")
            cdp.call("DeviceAccess.enable")
            cdp.evaluate("__miniReadonlyGuard.allowRequest()")
            cdp.click("#connBtn")
            deadline = time.monotonic() + timeout
            handled = set()
            event_cursor = 0
            while time.monotonic() < deadline:
                snapshot = cdp.evaluate(STATE)
                pending_events = cdp.events[event_cursor:]
                event_cursor = len(cdp.events)
                for event in pending_events:
                    if event.get("method") != "DeviceAccess.deviceRequestPrompted": continue
                    prompt = event["params"]
                    if prompt["id"] in handled: continue
                    report.setdefault("chooser_prompts", []).append(prompt)
                    try:
                        selection = select_device(prompt, evidence["com"], allow_missing=True)
                    except Exception:
                        cdp.call("DeviceAccess.cancelPrompt", {"id": prompt["id"]})
                        raise
                    if selection is None:
                        continue  # Device lists may be populated by a later event for this prompt.
                    handled.add(prompt["id"])
                    cdp.call("DeviceAccess.selectPrompt", selection)
                    report["device_chooser_selected"] = True
                require(not snapshot["guard"]["fatal"], snapshot["guard"]["fatal"])
                if snapshot["connected"] and snapshot["initialReadsFinished"]:
                    break
                time.sleep(.1)
            snapshot = cdp.evaluate(STATE)
            if not report["device_chooser_selected"]:
                for prompt in report.get("chooser_prompts", []):
                    if prompt["id"] not in handled:
                        handled.add(prompt["id"])
                        cdp.call("DeviceAccess.cancelPrompt", {"id": prompt["id"]})
            require(snapshot["connected"] and snapshot["initialReadsFinished"] and snapshot["fw"] == evidence["pong"]
                    and snapshot["guard"]["pongMatched"] and snapshot["guard"]["opens"] == 1,
                    "editor did not complete the exact MINI handshake and initial reads")
            required = {"PING", "MODEL", "MEM", "FXT", "FXS", "PLIST", "SNAPS"}
            answered = {item["line"] for item in snapshot["guard"]["commands"] if item["lines"]
                        and not any(line.startswith("ERR") for line in item["lines"])}
            require(required <= answered, "required initial app queries lacked valid responses: " + str(sorted(required - answered)))
            time.sleep(2)
            cdp.click("#presetBtn")
            report["connected"] = cdp.evaluate(STATE)
            report["connected_screenshot"] = cdp.screenshot(output / "connected-presets.png")
            require(not report["connected"]["guard"]["fatal"], "read-only guard stopped the session")
            report["serial_port_opened"] = True
            cdp.evaluate("connect()")  # App's disconnect path drains pending reads before closing.
            require(cdp.evaluate("!S.connected && !SerialTransport.isOpen()"), "serial disconnect did not complete")
            report["serial_port_closed"] = True
        else:
            snapshot = cdp.evaluate(STATE)
            require(not snapshot["guard"]["requests"] and not snapshot["guard"]["opens"]
                    and not snapshot["guard"]["wire"] and not snapshot["connected"], "offline browser attempted serial access")
        report["final"] = cdp.evaluate(STATE)
        report["javascript_exceptions"] = [e["params"] for e in cdp.events if e.get("method") == "Runtime.exceptionThrown"]
        require(not report["javascript_exceptions"], "uncaught JavaScript error")
        report["result"] = "pass"
    except Exception as error:
        report["result"], report["error"] = "fail", repr(error)
        if cdp:
            try: report["failure_snapshot"] = cdp.evaluate(STATE)
            except Exception: pass
    finally:
        if cdp:
            try:
                latest = cdp.evaluate(STATE)
                report["serial_port_open_attempted"] = latest["guard"]["opens"] > 0
                report["serial_port_opened"] = any(e["kind"] == "serial_open_complete" for e in latest["guard"]["events"])
                cdp.evaluate("(async()=>{__miniReadonlyGuard.stop();if(typeof S!=='undefined'){S.connected=false;clearInterval(lvlTimer);clearInterval(tuTimer);autoRe=null;Pedal.abort();await Pedal.disconnect();}})()")
                report["cleanup_serial_closed"] = cdp.evaluate("!SerialTransport.isOpen()")
            except Exception as error:
                report["page_cleanup_error"] = repr(error)
            try: cdp.call("Browser.close")
            except Exception: pass
            cdp.ws.close()
        if process:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate(); process.wait(timeout=5)
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        report["isolated_browser_stopped"] = process is None or process.poll() is not None
        report["local_server_stopped"] = True
        # Written once, after browser exit; monitoring cannot block an active report replacement.
        with (output / "report.json").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--app-dir", type=Path, default=DEFAULT_APP)
    parser.add_argument("--execute-readonly", action="store_true")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--evidence-sha256")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    evidence = None
    if args.execute_readonly:
        require(args.evidence is not None, "live browser requires reviewed COM/PONG evidence")
        evidence = load_evidence(args.evidence, args.evidence_sha256)
        evidence = {**evidence, "evidence_path": str(args.evidence), "evidence_sha256": args.evidence_sha256}
    else:
        require(args.evidence is None and args.evidence_sha256 is None, "evidence arguments require explicit --execute-readonly")
    report = run(args.app_dir, args.output, evidence=evidence, timeout=args.timeout)
    print(json.dumps({"result": report["result"], "live_opt_in": report["live_opt_in"],
                      "serial_port_opened": report["serial_port_opened"], "error": report.get("error")}))
    if report["result"] != "pass": raise SystemExit(1)


if __name__ == "__main__":
    main()
