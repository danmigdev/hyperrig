"""Observe Windows sharing for the already verified MINI ROM reader.

One exclusive open, two reader identity/status checks and a competing CreateFile.
No NOR write, SPI initialization, RAM upload, jump, reset or command retry.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT)]
from tools.build_mini_boot import verify_recorded_hashes
from tools.probe_mini_recovery import discover_windows_rom_disks
from tools.mini_windows_exclusive import (RomDiskAttestation,
    ExclusiveBufferedRomTransport, probe_competing_data_open)
from tools.mini_windows_mcn import MiniMediaChangePause
from tools.mini_host_journal import atomic_write_json

B = 0x1C28000
PREFIX = ROOT / 'analysis/hardware/mini-exclusive-access'
OUT = Path(str(PREFIX) + '-run.json')
PINS = Path(str(PREFIX) + '-pins.json')
MCN_LOG = Path(str(PREFIX) + '-mcn.jsonl')
TRIAL = ROOT / 'analysis/hardware/mini-partial-inspect6-recovered-run.json'

def require(ok, message):
    if not ok: raise ValueError(message)

def now(): return datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()

def prepare():
    pins = json.loads(PINS.read_bytes()); verify_recorded_hashes(pins)
    trial = json.loads(TRIAL.read_bytes())
    require(trial.get('finished_utc') and not trial.get('error')
            and trial['phase'] == 'partial_image_verified' and trial['known_live_slot'] == B
            and trial['mutation_completion_unknown'] is False and trial['jump_outcome_unknown'] is False
            and trial['progress'] == {'bytes': 0x100000, 'total': 0x100000}
            and trial['matches_expected_partial'] is True, 'complete sixth inspection required')
    dump = (ROOT / trial['dump_path']).resolve()
    require(dump.is_relative_to(ROOT) and sha(dump.read_bytes()) == trial['dump_sha256'],
            'sixth physical readback differs')
    return pins, trial

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    require(not (args.execute and args.check_only), 'choose one action')
    pins, trial = prepare()
    if not args.execute:
        print(json.dumps({'preflight': 'pass', 'device_io': False, 'NOR_write': False}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'bounded access helper needs elevation')
    require(not any(p.exists() for p in (OUT, OUT.with_suffix('.json.tmp'), MCN_LOG)), 'one-shot evidence exists')
    result = {'started_utc': now(), 'phase': 'exclusive_open', 'source_pins': pins,
        'NOR_write': False, 'SPI_initialization': False, 'RAM_upload': False, 'reset': False,
        'automatic_retry': False, 'known_live_slot': B, 'jump_outcome_unknown': False,
        'MCN_pause_started': False, 'MCN_pause_closed': False, 'MCN_explicitly_reenabled': False,
        'reference_NOR_sha256': trial['dump_sha256'], 'polling_exclusion_proven': False}
    def save(): atomic_write_json(OUT, result)
    def mcn_log(item):
        with MCN_LOG.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(item) + '\n'); stream.flush(); os.fsync(stream.fileno())
        if item['event'] == 'mcn_disabled': result['MCN_pause_started'] = True
        if item['event'] == 'mcn_reenabled': result['MCN_explicitly_reenabled'] = True
        save()
    def reader_state(transport):
        identity = transport.exchange(b'\xfc\x70' + b'\xff' * 14, read_length=16)
        require(identity == b'\xfc\x70HYRN\1\3' + B.to_bytes(4, 'big') + (32768).to_bytes(4, 'big'),
                'retained reader B differs')
        status = transport.exchange(b'\xfc\x73' + b'\xff' * 14, read_length=16)
        require(status[:4] == b'\xfc\x73\0\1' and int.from_bytes(status[12:], 'big') == trial['final_reader_counter'],
                'retained completed read counter differs')
        return {'identity_hex': identity.hex(), 'status_hex': status.hex()}
    pause = None
    save()
    try:
        disks = discover_windows_rom_disks(); require(len(disks) == 1, 'one MINI ROM disk required')
        with ExclusiveBufferedRomTransport(RomDiskAttestation.from_discovery(disks[0]),
                slot=B, profile='nor-reader') as transport:
            result['open_metadata'] = transport.open_metadata
            result['reader_before'] = reader_state(transport); save()
            pause = MiniMediaChangePause(transport, log=mcn_log)
            try:
                result['competing_open'] = probe_competing_data_open(transport)
                result['reader_after'] = reader_state(transport)
                require(result['reader_before'] == result['reader_after'], 'reader state changed')
                result.update(phase='sharing_observation_complete', reader_state_unchanged=True)
            finally:
                pause.close()
                result['MCN_pause_closed'] = pause.closed
                require(not pause.disabled and result['MCN_explicitly_reenabled'], 'MCN enable not confirmed')
    except Exception as error:
        result.update(error=str(error), error_type=type(error).__name__)
    finally:
        result['finished_utc'] = now(); save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'competing_open', 'reader_state_unchanged')}))

if __name__ == '__main__': main()
