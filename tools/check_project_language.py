"""Flag likely Italian prose in maintained Markdown; source records are exempt.

This is a focused regression check, not a general language detector. Code,
paths, captured output, and third-party legal notices retain their original
identifiers and bytes. The editor's English-only behavior has separate tests.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ITALIAN = re.compile(
    r'\b(?:della|delle|dello|degli|dalla|dalle|nella|nelle|sulla|sulle|'
    r'questa|questo|verificato|verificata|lettura|scrittura|rimane|restano|'
    r'senza|richiamo|salvataggio|sorgenti|collegamento|riavvio|nessuna|'
    r'perch\u00e9|pu\u00f2|pi\u00f9)\b', re.IGNORECASE)


def check():
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
                                    cwd=ROOT, text=True).splitlines()
    checked, issues = [], []
    for name in sorted(set(names)):
        path = ROOT / name
        if path.suffix != '.md' or name.startswith(('third_party/', 'analysis/')) or not path.is_file():
            continue
        text = path.read_text(encoding='utf-8-sig')
        checked.append(name)
        fenced = False
        for number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith(('```', '~~~')):
                fenced = not fenced
                continue
            if fenced:
                continue
            prose = re.sub(r'`[^`]*`|https?://\S+', '', line)
            match = ITALIAN.search(prose)
            if match:
                issues.append(f'{name}:{number}: likely non-English prose ({match.group()})')
    return checked, issues


if __name__ == '__main__':
    checked, issues = check()
    for issue in issues:
        print(issue)
    print(f'Checked {len(checked)} maintained Markdown files; {len(issues)} findings.')
    sys.exit(bool(issues))
