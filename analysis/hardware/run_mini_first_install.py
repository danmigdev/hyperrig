"""One bounded stock-to-HyperRig installation; leave verified ROM active.

Fresh full NOR -> operational application writer -> independent full NOR.
Never reset, boot, retry or roll back automatically, including on failure.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT)]
from tools.build_mini_boot import verify_recorded_hashes
from tools.verify_mini_recovery_reader import inspect_reader
from tools.probe_mini_recovery import discover_windows_rom_disks, WindowsRomTransport, MiniNorSession
from tools.install_mini_app import prepare_installation, MiniAppInstallerSession
from hyperrig.device import ReadOnlyMini, ports
import rtmidi

A, B = 0x1c20000, 0x1c28000
PREFIX = 'analysis/hardware/mini-first-install'
OUT, TRACE, JOURNAL = (ROOT / (PREFIX + suffix) for suffix in ('-run.json', '-trace.jsonl', '-journal.jsonl'))
PINS = ROOT / (PREFIX + '-pins.json')
EXPECTED_PORTS = {'inputs': ['USB-Midi 0'], 'outputs': ['Microsoft GS Wavetable Synth 0', 'USB-Midi 1']}
FULL_BEFORE = ROOT / 'artifacts/my-mini-flash/first-install/full-before.bin'
FULL_AFTER = ROOT / 'artifacts/my-mini-flash/first-install/full-after.bin'
BACKUP = ROOT / 'artifacts/my-mini-flash/20261115-paced-resume/flash-a.bin'

def sha(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def require(condition, message):
    if not condition: raise ValueError(message)
def load(name): return json.loads((ROOT / name).read_text(encoding='utf-8'))
def append(path, item, durable=False):
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(item) + '\n')
        if durable:
            stream.flush()
            os.fsync(stream.fileno())

def prepare():
    pins = json.loads(PINS.read_text(encoding='utf-8'))
    verify_recorded_hashes(pins)
    installation = prepare_installation(slot=A)
    require(sha(installation.candidate) == '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff',
            'this one-shot runner is for the reviewed audio-v2 candidate only')
    backup = BACKUP.read_bytes()
    require(len(backup) == 0x100000 and sha(backup) == installation.backup_sha256,
            'full unit backup differs')
    reader = load('research/mini-flash-reader.json')
    verify_recorded_hashes(reader['sources_sha256'])
    require(sha((ROOT / 'tools/verify_mini_recovery_reader.py').read_bytes()) == reader['verifier_sha256'],
            'reader verifier changed')
    artifact = next(a for a in reader['artifacts'] if a['audit']['slot'] == B)
    elf = (ROOT / artifact['elf']).read_bytes()
    payload, audit = inspect_reader(elf, B)
    require(sha(elf) == artifact['elf_sha256'] and payload == (ROOT / artifact['flat']).read_bytes()
            and sha(payload) == artifact['flat_sha256'] and audit == artifact['audit'], 'reader artifact changed')
    observation = load('research/mini-writer-observer-hardware.json')
    require(observation['return_to_stock_verified'] and observation['frozen_page_echo_compared_byte_for_byte']
            and observation['WREN_attempts'] == observation['erase_attempts'] == observation['program_attempts'] == 0,
            'physical gate-zero observation missing')
    return pins, installation, backup, artifact, payload

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    pins, installation, backup, reader_artifact, reader_payload = prepare()
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'candidate': sha(installation.candidate),
                          'changed_sectors': len(installation.sector_order), 'automatic_reset': False}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'Windows SPTD requires the elevated bounded helper')
    require(not any(p.exists() for p in (OUT, TRACE, JOURNAL, FULL_BEFORE, FULL_AFTER)),
            'one-shot output exists; do not rerun')
    result = {'started_utc': now(), 'phase': 'prepare', 'source_pins': pins,
              'installation': installation.summary(), 'known_live_slot': None,
              'jump_outcome_unknown': False, 'jump_attempts': 0,
              'mutation_command_submitted': False, 'mutation_completion_unknown': False,
              'installed_image_verified': False, 'full_NOR_verified': False,
              'automatic_reset': False, 'automatic_retry': False, 'automatic_rollback': False,
              'power_loss_atomicity_proven': False}
    path, writer = None, None

    def save():
        temp = OUT.with_suffix('.json.tmp')
        with temp.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(result, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, OUT)

    def phase(value):
        result['phase'] = value
        save()

    def logged(transport, label):
        original = transport.exchange
        def exchange(cdb, data_out=None, read_length=0):
            time.sleep(0.005)
            entry = {'stage': label, 'state': 'before', 'started_utc': now(), 'cdb': cdb.hex(),
                     'out_bytes': len(data_out) if data_out is not None else 0, 'in_bytes': read_length}
            if cdb[:2] == b'\xfb\x08':
                result.update(known_live_slot=None, jump_outcome_unknown=True, jump_attempts=result['jump_attempts'] + 1)
                save()
            if cdb[:2] in (b'\xfc\x7b', b'\xfc\x7d'):
                result.update(mutation_command_submitted=True, mutation_completion_unknown=True)
                save()
            append(TRACE, entry, durable=cdb[:2] in (b'\xfb\x08', b'\xfc\x7b', b'\xfc\x7d'))
            start = time.monotonic()
            try:
                raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                entry.update(state='error', finished_utc=now(), error=repr(error),
                             details=getattr(error, 'details', {}))
                append(TRACE, entry, durable=True)
                raise
            entry.update(state='after', elapsed_ms=(time.monotonic() - start) * 1000,
                         response_bytes=len(raw), response_sha256=sha(raw))
            if len(raw) <= 128: entry['response_hex'] = raw.hex()
            append(TRACE, entry)
            return raw
        transport.exchange = exchange

    def journal(item):
        append(JOURNAL, {'utc': now(), **item}, durable=item['event'] in
               ('command_intent', 'terminal_error', 'sector_verified', 'application_verified'))
        if item['event'] in ('sector_verified', 'application_verified'):
            result['writer_progress'] = item
            save()

    def full_read(label, output):
        require(not result['jump_outcome_unknown'] and result['known_live_slot'] in (None, A),
                'reader B is not known inactive')
        with WindowsRomTransport(path, slot=B, profile='nor-reader') as transport:
            logged(transport, label)
            session = MiniNorSession(transport, slot=B, known_free_slot=True)
            result[label + '_session'] = session.upload_and_start(reader_payload, expected_sha256=reader_artifact['flat_sha256'])
            result.update(known_live_slot=B, jump_outcome_unknown=False)
            result[label + '_SPI'] = session.initialize_spi()
            require(result[label + '_SPI']['jedec_hex'] == 'eb6014', 'physical NOR identity changed')
            def progress(done, total):
                if done % 65536 == 0:
                    result[label + '_progress'] = {'bytes': done, 'total': total}
                    save()
            raw = session.read_flash(0, 0x100000, progress=progress)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
        result[label] = {'path': output.relative_to(ROOT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)}
        save()
        return raw

    save()
    try:
        require(not discover_windows_rom_disks() and ports() == EXPECTED_PORTS, 'fresh identified stock entry required')
        phase('stock_identity_and_presets')
        with ReadOnlyMini(0, 1) as device:
            require(device.identity == 'TANK MINI_009', 'unexpected stock identity')
            info = device.backup(ROOT / 'artifacts/my-mini-presets/usb-before-first-install-20261115')
            result['stock_before'] = {k: info[k] for k in ('identity', 'bytes', 'sha256', 'equal_reads')}
        phase('request_rom')
        require(ports() == EXPECTED_PORTS, 'MIDI ordering changed')
        output = rtmidi.MidiOut()
        try:
            output.open_port(1)
            result['rom_request'] = {'hex': 'f02224357df7', 'submitted_once_utc': now()}
            save()
            output.send_message([0xf0, 0x22, 0x24, 0x35, 0x7d, 0xf7])
            time.sleep(0.1)
        finally: output.close_port()
        time.sleep(3)
        candidates = []
        for _ in range(3):
            candidates = discover_windows_rom_disks()
            if candidates: break
            time.sleep(2)
        if not candidates:
            phase('restart_matching_failed_hub')
            helper = ROOT / 'analysis/hardware/restart-engine-hub.ps1'
            process = subprocess.run([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(helper)],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            result['hub_restart'] = {'returncode': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}
            save()
            require(process.returncode == 0 and json.loads(process.stdout)['exit_code'] == 0, 'matching hub restart failed')
            time.sleep(3)
            candidates = discover_windows_rom_disks()
        require(len(candidates) == 1, 'ROM disk not unique')
        path = candidates[0]['path']
        result['ROM_disk'] = candidates[0]
        phase('fresh_complete_NOR_read')
        require(full_read('full_before', FULL_BEFORE) == backup, 'fresh NOR differs from accepted unit backup')
        phase('operational_writer_upload')
        require(result['known_live_slot'] == B and not result['jump_outcome_unknown'], 'slot A is not known inactive')
        with WindowsRomTransport(path, slot=A, profile='app-writer-operational') as transport:
            logged(transport, 'writer')
            writer = MiniAppInstallerSession(transport, installation, journal=journal, known_free_slot=True)
            result['writer_session'] = writer.upload_and_start(installation.image, expected_sha256=installation.image_sha256)
            result.update(known_live_slot=A, jump_outcome_unknown=False)
            phase('initialize_writer_SPI')
            result['writer_SPI'] = writer.initialize_spi()
            phase('fresh_complete_application_preimage')
            result['application_preimage'] = writer.verify_complete_preimage()
            phase('install_and_verify_application')
            result['application_installation'] = writer.install_application()
            require(writer.image_verified and not writer.failed, 'application installation incomplete')
            result['installed_image_verified'] = True
            result['mutation_completion_unknown'] = writer.mutation_completion_unknown
        phase('independent_complete_NOR_readback')
        expected = backup[:0x4000] + installation.candidate + backup[0x82000:]
        require(full_read('full_after', FULL_AFTER) == expected, 'independent whole NOR comparison failed')
        result.update(full_NOR_verified=True, preserved_regions_unchanged=True, mutation_completion_unknown=False)
        phase('installed_verified_waiting_for_footswitch')
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error),
                      error_details=getattr(error, 'details', {}))
    finally:
        if writer is not None:
            result['mutation_completion_unknown'] = writer.mutation_completion_unknown
            result['writer_final'] = {'phase': writer.phase, 'failed': writer.failed,
                'image_verified': writer.image_verified, 'preimage_verified': writer.preimage_verified,
                'verified_sectors': writer.verified_sectors, 'last_audit': writer.last_audit,
                'last_status': writer.last_status, 'mutation_command_submitted': writer.mutation_command_submitted,
                'mutation_completion_unknown': writer.mutation_completion_unknown,
                'ambiguous_operation': writer.ambiguous_operation, 'journal_error': writer.journal_error}
        result['finished_utc'] = now()
        save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'installed_image_verified',
          'full_NOR_verified', 'known_live_slot', 'jump_outcome_unknown', 'mutation_command_submitted')}))

if __name__ == '__main__': main()
