"""A Patchstorage of our own on this computer, for tools/check_desktop_editor.py: the list of a platform, the records of its presets and their files, in the form
of the public API. It notes what it is asked. No request reaches the real one."""
from __future__ import annotations

import http.server
import json
import threading
from urllib.parse import parse_qs, urlsplit

PLATFORM = 9001


class Service:
    def __init__(self, preset):
        """preset: the text of a HyperRig preset file."""
        self.asked, self.problems = [], []
        self.files = {701: ('crunch.hyperrig.json', preset), 702: ('broken.json', '{"format": "other"}'), 703: ('read-me.txt', 'x'), 801: ('moved.json', preset), 901: ('away.json', preset)}
        self.records = {70: self.record(70, 'Edge of breakup', [701, 702, 703]), 80: self.record(80, 'Moved', [801]), 90: self.record(90, 'Sent away', [901]),
                        60: self.record(60, 'Nothing &amp; <b>inside</b> &lt;img src=x onerror=__errors.push(1)&gt;', [])}
        for k in range(30):
            self.records[1000 + k] = self.record(1000 + k, f'Clean {k + 1}', [701])
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, body=b'', kind='application/json', **headers):
                raw = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                self.send_header('Content-Type', kind)
                self.send_header('Content-Length', str(len(raw)))
                self.send_header('Set-Cookie', 'PHPSESSID=check; path=/')
                for name, value in headers.items():
                    self.send_header(name.replace('_', '-'), value)
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                outer.problems.append('POST ' + self.path)
                self.reply(400, {})

            do_PUT = do_DELETE = do_POST

            def do_GET(self):
                url = urlsplit(self.path)
                q = {k: v[0] for k, v in parse_qs(url.query).items()}
                outer.asked.append(self.path)
                for name in ('Authorization', 'Cookie', 'Referer', 'Origin'):
                    if self.headers.get(name):
                        outer.problems.append(f'{name}: {self.headers[name]}')
                if not (self.headers.get('User-Agent') or '').startswith('HyperRig/'):
                    outer.problems.append(f"User-Agent: {self.headers.get('User-Agent')}")
                parts = [p for p in url.path.split('/') if p]
                if parts == ['api', 'beta', 'patches']:
                    if q.get('platforms[]') != str(PLATFORM) or not q.get('per_page', '').isdigit():
                        outer.problems.append(self.path)
                        return self.reply(400, {'code': 'rest_invalid_param'})
                    found = [r for r in outer.records.values() if q.get('search', '').lower() in r['title'].lower()]
                    n, at = int(q['per_page']), int(q.get('page', '1'))
                    return self.reply(200, [{k: v for k, v in r.items() if k not in ('files', 'license', 'content')} for r in found[(at - 1) * n:at * n]],
                                      X_WP_Total=str(len(found)), X_WP_TotalPages=str(-(-len(found) // n)))
                if len(parts) == 4 and parts[:3] == ['api', 'beta', 'patches'] and parts[3].isdigit() and int(parts[3]) in outer.records:
                    return self.reply(200, outer.records[int(parts[3])])
                if len(parts) == 7 and parts[4] == 'files' and parts[6] == 'download' and parts[5].isdigit():
                    fid = int(parts[5])
                    if fid == 801 and not url.path.startswith('/moved'):
                        return self.reply(302, b'', Location='/uploads/801.json')
                    if fid == 901:
                        return self.reply(302, b'', Location='https://example.com/away.json')
                    return self.reply(200, outer.files[fid][1].encode(), 'application/octet-stream')
                if url.path == '/uploads/801.json':
                    return self.reply(200, outer.files[801][1].encode(), 'application/octet-stream')
                return self.reply(404, {'code': 'rest_no_route'})

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.address = f'http://127.0.0.1:{self.server.server_port}'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def record(self, number, title, files):
        return {'id': number, 'uids': [], 'url': f'https://patchstorage.com/preset-{number}/', 'created_at': '2026-11-01T10:00:00+00:00', 'updated_at': '2026-11-02T10:00:00+00:00', 'slug': f'preset-{number}',
                'title': title, 'excerpt': 'A test preset...', 'content': '<p>A test preset.</p><p>For a check.</p>', 'code': '', 'preview_url': '', 'revision': '1.0', 'download_count': 3, 'like_count': 1,
                'author': {'id': 2, 'slug': 'preset-maker', 'name': 'Preset Maker'}, 'categories': [], 'tags': [], 'license': {'id': 4190, 'name': 'Creative Commons Attribution 4.0', 'slug': 'cc-by-4-0', 'custom_license_text': ''},
                'platform': {'id': PLATFORM, 'name': 'HyperRig', 'slug': 'hyperrig'}, 'targets': [], 'state': {'id': 151, 'name': 'Ready to Go'},
                'files': [{'id': f, 'url': f'https://patchstorage.com/api/beta/patches/{number}/files/{f}/download/', 'filesize': len(self.files[f][1]), 'filename': self.files[f][0], 'target': None} for f in files]}

    def close(self):
        self.server.shutdown()
        self.server.server_close()
