"""A TONE3000 of our own on this computer, for tools/check_desktop_editor.py: the sign-in page, the tokens, one tone and its files.
No request reaches the real one."""
from __future__ import annotations

import base64
import hashlib
import http.server
import json
import math
import random
import secrets
import struct
import threading
from urllib.parse import parse_qs, urlencode, urlsplit

PAGE = '''<!doctype html><meta charset="utf-8"><title>Simulated TONE3000</title><h1>Sign in and choose</h1>
<a id="use" href="{use}">Use this tone</a> <a id="cancel" href="{cancel}">Cancel</a> <a id="wrong" href="{wrong}">Wrong state</a>
<a id="out" href="http://127.0.0.1:9/elsewhere">Elsewhere</a> <a id="file" href="file:///C:/Windows/win.ini">File</a>'''


def wav():
    rng = random.Random(4)
    frames = b''.join(struct.pack('<h', round(rng.uniform(-1, 1) * 22000 * math.exp(-i / 500))) for i in range(3000))
    return b'RIFF' + struct.pack('<I', 36 + len(frames)) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, 1, 48000, 96000, 2, 16) + b'data' + struct.pack('<I', len(frames)) + frames


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFUlEQVR4nGNkYPjPwMDAxMDAwMDAAAAMHgEDsFAmvgAAAABJRU5ErkJggg==')


class Service:
    def __init__(self, nam):
        self.nam, self.asked, self.codes, self.access, self.refresh, self.problems = nam, [], {}, set(), set(), []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, body=b'', kind='application/json', **headers):
                raw = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                self.send_header('Content-Type', kind)
                self.send_header('Content-Length', str(len(raw)))
                for name, value in headers.items():
                    self.send_header(name.replace('_', '-'), value)
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', '0'))).decode()
                outer.asked.append(('POST', self.path, body, self.headers.get('Authorization')))
                q = {k: v[0] for k, v in parse_qs(body).items()}
                if self.path != '/api/v1/oauth/token' or q.get('client_id') != 't3k_pub_check0000' or 'client_secret' in q:
                    return self.reply(400, {'error': 'invalid_request'})
                if q.get('grant_type') == 'authorization_code':
                    challenge = outer.codes.pop(q.get('code'), None)
                    made = base64.urlsafe_b64encode(hashlib.sha256(q.get('code_verifier', '').encode()).digest()).rstrip(b'=').decode()
                    if challenge is None or challenge != made or q.get('redirect_uri') != 'http://localhost:3001/callback':
                        return self.reply(400, {'error': 'invalid_grant'})
                elif q.get('refresh_token') not in outer.refresh:
                    return self.reply(400, {'error': 'invalid_grant'})
                access, again = 'a' + secrets.token_hex(8), 'r' + secrets.token_hex(8)
                outer.access.add(access)
                outer.refresh = {again}
                return self.reply(200, {'access_token': access, 'refresh_token': again, 'token_type': 'bearer', 'expires_in': 3600, 'scope': 'read'})

            def do_GET(self):
                url = urlsplit(self.path)
                q = {k: v[0] for k, v in parse_qs(url.query).items()}
                outer.asked.append(('GET', self.path, '', self.headers.get('Authorization')))
                if url.path == '/api/v1/oauth/authorize':
                    want = {'client_id', 'redirect_uri', 'response_type', 'code_challenge', 'code_challenge_method', 'state', 'prompt', 'menubar', 'format'}
                    if not want <= set(q) or q['prompt'] != 'select_tone' or q['code_challenge_method'] != 'S256':
                        outer.problems.append(self.path)
                        return self.reply(400, b'bad request', 'text/plain')
                    code = secrets.token_hex(8)
                    outer.codes[code] = q['code_challenge']
                    back = lambda **more: q['redirect_uri'] + '?' + urlencode(more)
                    tone = '77' if q['format'] == 'nam' else '88'
                    page = PAGE.format(use=f'/go?to={urlencode({"x": back(code=code, state=q["state"], tone_id=tone)})[2:]}'.replace('&', '&amp;'),
                                       cancel=back(canceled='true', state=q['state']).replace('&', '&amp;'), wrong=back(code=code, state='other', tone_id=tone).replace('&', '&amp;'))
                    return self.reply(200, page.encode(), 'text/html; charset=utf-8')
                if url.path == '/go':                  # the service's own redirect at the end
                    return self.reply(302, b'', 'text/plain', Location=q['to'])
                if url.path == '/pictures/p.png':
                    return self.reply(200, PNG, 'image/png')
                if (self.headers.get('Authorization') or '').replace('Bearer ', '') not in outer.access:
                    return self.reply(401, {'error': 'unauthorized'})
                if url.path in ('/api/v1/tones/77', '/api/v1/tones/88'):
                    ir = url.path.endswith('88')
                    return self.reply(200, {'id': 88 if ir else 77, 'title': 'Greenback 4x12' if ir else 'Plexi Crunch', 'user': {'username': 'amp.maker'}, 'gear': 'cab' if ir else 'amp', 'format': 'ir' if ir else 'nam',
                                            'license': 'cc-by', 'description': 'A test tone.', 'images': [f'{outer.address}/pictures/p.png'.replace('http://', 'https://') if ir else 'https://127.0.0.1:1/none.png'],
                                            'makes': [{'name': 'Marshall'}], 'url': 'https://www.tone3000.com/tones/77'})
                if url.path == '/api/v1/models':
                    if q.get('tone_id') == '88':
                        return self.reply(200, {'data': [{'id': 5, 'name': 'SM57', 'size': '', 'architecture_version': None, 'model_url': f'{outer.address}/api/v1/models/5/download'}]})
                    return self.reply(200, {'data': [{'id': i, 'name': n, 'size': s, 'architecture_version': a, 'model_url': f'{outer.address}/api/v1/models/{i}/download'}
                                                     for i, n, s, a in ((1, 'Clean', 'standard', '2'), (2, 'Crunch', 'lite', '2'), (3, 'Old', 'standard', '1'))]})
                if url.path == '/api/v1/models/2/download':
                    return self.reply(302, b'', 'text/plain', Location=f'{outer.address}/api/v1/files/2')
                if url.path in ('/api/v1/files/2', '/api/v1/models/1/download'):
                    return self.reply(200, outer.nam)
                if url.path == '/api/v1/models/5/download':
                    return self.reply(200, wav(), 'audio/wav')
                return self.reply(404, {})

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.address = f'http://127.0.0.1:{self.server.server_port}'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
