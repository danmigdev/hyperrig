"""Read-only inspection after buffered install stopped on FC7E.

Confirm the live operational writer and completed read, switch inactive B to
the pinned reader and retain a full NOR dump. No NOR write, reset or retry.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis/hardware'), str(ROOT / 'tools'), str(ROOT)]
from run_mini_buffered_install import prepare, require, A, B
from tools.probe_mini_recovery import discover_windows_rom_disks, MiniNorSession
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.build_mini_app_writer import validate_audit_record

PREFIX = 'analysis/hardware/mini-partial-inspect3'
OUT, TRACE, AUDIT = (ROOT / (PREFIX + suffix) for suffix in ('-run.json', '-trace.jsonl', '-writer-audit.bin'))
DUMP = ROOT / 'artifacts/my-mini-flash/first-install/full-partial3.bin'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    pins, prepared, artifact, payload = prepare()
    installation, backup = prepared.installation, prepared.stock_backup
    prior_raw = (ROOT / 'analysis/hardware/mini-buffered-install-run.json').read_bytes()
    prior = json.loads(prior_raw)
    require(prior.get('finished_utc') and prior['error_phase'] == 'install_and_verify_application'
            and prior['error_details']['cdb_hex'] == 'fc7effffffffffffffffffffffffffff'
            and prior['error_details']['win32_error'] == 31
            and prior['known_live_slot'] == A and not prior['jump_outcome_unknown']
            and not prior['writer_final']['mutation_completion_unknown'], 'unexpected stopped install')
    old = prior['writer_final']['last_audit']
    require((old['sector'], old['sequence'], old['erase_attempts'], old['program_attempts'], old['page_bitmap'])
            == (0x6000, 35, 2, 32, 0xffff), 'last validated writer state differs')
    expected = bytearray(backup)
    expected[0x5000:0x7000] = installation.candidate[0x1000:0x3000]
    expected = bytes(expected)
    expected_crc = zlib.crc32(expected[0x6e00:0x7000]) & 0xffffffff
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'writes': False, 'reset': False,
                          'expected_full_sha256': sha(expected), 'expected_read_bytes': old['read_bytes'] + 512,
                          'expected_last_crc32': expected_crc}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'bounded SPT helper requires elevation')
    require(not any(p.exists() for p in (OUT, TRACE, AUDIT, DUMP)), 'inspection already attempted')
    result = {'phase': 'inspect_writer', 'started_utc': now(), 'firmware_write_this_step': False,
        'reset_performed': False, 'automatic_retry': False, 'prior_run_sha256': sha(prior_raw),
        'known_live_slot': A, 'jump_outcome_unknown': False, 'source_pins': pins,
        'runner_sha256': sha(Path(__file__).read_bytes()), 'backend': 'spt-buffered'}

    def save():
        temp = OUT.with_suffix('.json.tmp')
        with temp.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(result, indent=2) + '\n')
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, OUT)

    def append(event):
        with TRACE.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(event) + '\n')
            stream.flush(); os.fsync(stream.fileno())

    def logged(transport):
        original = transport.exchange
        def exchange(cdb, data_out=None, read_length=0):
            time.sleep(0.005)
            event = {'state': 'before', 'utc': now(), 'cdb': cdb.hex(), 'read_length': read_length,
                     'out_bytes': len(data_out) if data_out is not None else 0}
            require(cdb[:2] not in (b'\xfc\x7b', b'\xfc\x7d', b'\xfc\x80'), 'no NOR mutation')
            if cdb[:2] == b'\xfb\x08':
                require(result['known_live_slot'] == A and not result['jump_outcome_unknown'] and transport.slot == B,
                        'only inactive reader B may be started once')
                result.update(known_live_slot=None, jump_outcome_unknown=True); save()
            append(event)
            try: raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                event.update(state='error', error=repr(error), details=getattr(error, 'details', {}))
                append(event); raise
            event.update(state='after', response_sha256=sha(raw))
            if len(raw) <= 128: event['response_hex'] = raw.hex()
            append(event)
            return raw
        transport.exchange = exchange

    save()
    try:
        candidates = discover_windows_rom_disks()
        require(len(candidates) == 1, 'ROM disk not unique')
        path = candidates[0]['path']
        with WindowsBufferedRomTransport(path, slot=A, profile='app-writer-operational') as transport:
            logged(transport)
            result['adapter_descriptor'] = transport.adapter_descriptor
            identity = transport.exchange(b'\xfc\x78' + b'\xff' * 14, read_length=16)
            require(identity == b'\xfc\x78HYW1\1\1' + A.to_bytes(4, 'big') + (32768).to_bytes(4, 'big'), 'writer identity differs')
            result['writer_status_hex'] = transport.exchange(b'\xfc\x7e' + b'\xff' * 14, read_length=16).hex()
            raw = transport.exchange(b'\xfd\x88' + b'\xff' * 14, read_length=128)
            record = validate_audit_record(raw, base=A, build_tag=installation.build_tag, expected_mutations_enabled=True)
            result['writer_audit'] = record
            with AUDIT.open('xb') as stream: stream.write(raw)
            unchanged = ('version', 'base', 'build_tag', 'phase', 'error', 'token', 'sequence', 'sector', 'page',
                         'preimage_crc32', 'target_crc32', 'page_crc32', 'jedec', 'sr1', 'sr2', 'wren_attempts',
                         'erase_attempts', 'program_attempts', 'status_polls', 'raw_receive_return', 'rx_guards_ok',
                         'page_bitmap', 'staged', 'echoed', 'stack_guards_ok', 'stack_observed_bytes', 'mutations_enabled')
            require(all(record[k] == old[k] for k in unchanged), 'writer mutation/state changed after stop')
            require(record['read_bytes'] == old['read_bytes'] + 512 and record['last_crc32'] == expected_crc,
                    'last acknowledged read does not explain the fresh audit')
            require(record['error'] == 0 and record['rx_guards_ok'] == record['stack_guards_ok'] == 1, 'target error/guard damage')
        result['phase'] = 'full_NOR_read'; save()
        with WindowsBufferedRomTransport(path, slot=B, profile='nor-reader') as transport:
            logged(transport)
            reader = MiniNorSession(transport, slot=B, known_free_slot=True)
            result['reader_session'] = reader.upload_and_start(payload, expected_sha256=artifact['flat_sha256'])
            result.update(known_live_slot=B, jump_outcome_unknown=False)
            result['reader_SPI'] = reader.initialize_spi()
            require(result['reader_SPI']['jedec_hex'] == 'eb6014', 'NOR identity differs')
            def progress(done, total):
                if done % 65536 == 0:
                    result['progress'] = {'bytes': done, 'total': total}; save()
            data = reader.read_flash(0, 0x100000, progress=progress)
        with DUMP.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        result.update(dump_path=DUMP.relative_to(ROOT).as_posix(), dump_sha256=sha(data),
            matches_expected_partial=data == expected,
            changed_sectors=[a for a in range(0, 0x100000, 4096) if data[a:a+4096] != backup[a:a+4096]],
            phase='read_complete')
        require(data == expected, 'fresh dump differs from confirmed completed mutations')
        result['phase'] = 'partial_image_verified'
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error))
    finally:
        result['finished_utc'] = now(); save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'dump_sha256', 'matches_expected_partial', 'known_live_slot')}))

if __name__ == '__main__': main()
