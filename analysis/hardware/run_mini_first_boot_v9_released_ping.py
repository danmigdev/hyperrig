"""Run the reviewed released-button boot, then one exact identity PING.

The caller must have received the user's immediate released-button confirmation.
This wrapper performs no retry; it never sends PING after a failed boot result.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / 'analysis/hardware/run_mini_first_boot_v9.py'
RUN = ROOT / 'analysis/hardware/mini-first-boot-v9-released-run.json'
PING = ROOT / 'analysis/hardware/mini-first-app-v9-ping.jsonl'
CANDIDATE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'

def require(ok, message):
    if not ok: raise ValueError(message)

def main():
    require(len(sys.argv) == 1, 'no command arguments accepted')
    require(not RUN.exists() and not PING.exists(), 'this one-shot boot/PING has evidence already')
    subprocess.run([sys.executable, '-B', '-X', 'utf8', str(BOOT), 'released'], cwd=ROOT, check=True)
    result = json.loads(RUN.read_bytes())
    require(result.get('finished_utc') and not result.get('error')
            and result['phase'] == 'application_USB_observed'
            and result['application_USB_enumerated'] is True
            and result['candidate_sha256'] == CANDIDATE_SHA, 'completed successful released boot required')
    ports = result['application_ports']
    require(isinstance(ports, list) and len(ports) == 1
            and (ports[0]['vid'], ports[0]['pid']) == (0x3654, 0x5155)
            and re.fullmatch(r'COM[1-9][0-9]{0,3}', ports[0]['device']), 'one exact MINI CDC port required')
    subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'tools/probe_mini_app.py'),
        'read', '--port', ports[0]['device'], '--firmware-manifest',
        str(ROOT / 'build/hyperrig-mini-audio-v2/firmware-manifest.json'),
        '--log', str(PING), '--queries'], cwd=ROOT, check=True)

if __name__ == '__main__': main()
