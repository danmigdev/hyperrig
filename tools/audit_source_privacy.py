"""Report possible personal paths or embedded credentials without printing values."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'personal_windows_path': r'(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s"\x27]+',
    'personal_unix_path': r'/(?:home|Users)/[A-Za-z0-9_.-]+/',
    'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'provider_key': r'(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{20,})',
    'credential_literal': r'(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key|password|passwd|report[_-]?key)\s*[:=]\s*[\x22\x27]([^\x22\x27\r\n]{8,})[\x22\x27]',
    'url_credentials': r'https?://[^/\s:@]+:[^/\s@]+@',
}


def scan():
    raw = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
    files = sorted(set(n for n in raw.decode('utf-8').split('\0') if n))
    findings = []
    for name in files:
        path = ROOT / name
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text('utf-8')
        except (UnicodeError, OSError):
            continue
        if '\0' in text:
            continue
        for kind, pattern in PATTERNS.items():
            for match in re.finditer(pattern, text):
                findings.append({'file': name, 'line': text.count('\n', 0, match.start()) + 1, 'kind': kind})
    return {'files_examined': len(files), 'findings': findings, 'values_redacted': True}


if __name__ == '__main__':
    print(json.dumps(scan(), indent=2))
