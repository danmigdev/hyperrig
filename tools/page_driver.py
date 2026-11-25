"""What the checks of the page use: the installed Microsoft Edge, and a client of its DevTools protocol.

No device, personal profile or network is used. Needs the package websocket-client."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def browser_path():
    """The installed Microsoft Edge; nothing is downloaded or installed."""
    for variable, usual in (('PROGRAMFILES(X86)', 'C:/Program Files (x86)'), ('PROGRAMFILES', 'C:/Program Files')):
        candidate = Path(os.environ.get(variable, usual)) / 'Microsoft/Edge/Application/msedge.exe'
        if candidate.is_file():
            return candidate
    raise FileNotFoundError('Microsoft Edge is not installed')


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=12, suppress_origin=True)
        self.next_id = 1
        self.events = []

    def call(self, method, params=None):
        message_id = self.next_id
        self.next_id += 1
        self.ws.send(json.dumps({'id': message_id, 'method': method, 'params': params or {}}))
        while True:
            value = json.loads(self.ws.recv())
            if value.get('id') == message_id:
                if 'error' in value:
                    raise ValueError(f"{method}: {value['error']}")
                return value.get('result', {})
            self.events.append(value)

    def evaluate(self, expression):
        result = self.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
        require('exceptionDetails' not in result, f'browser evaluation failed: {result}')
        return result.get('result', {}).get('value')

    def click(self, selector):
        box = self.evaluate("(() => {const e=document.querySelector(" + json.dumps(selector) + "); if(!e)return null;e.scrollIntoView({block:'center'});"
                            "const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,width:r.width,height:r.height,disabled:!!e.disabled}})()")
        require(box and box['width'] > 0 and box['height'] > 0 and not box['disabled'], f'unavailable button {selector}')
        for kind in ('mousePressed', 'mouseReleased'):
            self.call('Input.dispatchMouseEvent', {'type': kind, 'x': box['x'], 'y': box['y'], 'button': 'left', 'clickCount': 1})
        time.sleep(0.15)

    def screenshot(self, path):
        data = base64.b64decode(self.call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})['data'])
        path.write_bytes(data)
        return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(data).hexdigest()}
