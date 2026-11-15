"""Read-only inspection after MCN install stopped on its ninth FD88 Win31.

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
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis/hardware'), str(ROOT / 'tools'), str(ROOT)]
from run_mini_mcn_install import prepare as installation_prepare, require, A, B
from tools.build_mini_boot import verify_recorded_hashes
from tools.mini_host_journal import atomic_write_json
from run_mini_receive_stress import attach_native_diagnostic
from tools.probe_mini_recovery import discover_windows_rom_disks, MiniNorSession
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.build_mini_app_writer import validate_audit_record

PREFIX = 'analysis/hardware/mini-partial-inspect4'
OUT, TRACE, AUDIT = (ROOT / (PREFIX + suffix) for suffix in ('-run.json', '-trace.jsonl', '-writer-audit.bin'))
DUMP = ROOT / 'artifacts/my-mini-flash/first-install/full-partial4.bin'
PINS = ROOT / (PREFIX + '-pins.json')

def now(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()


def confirm_writer(transport, expected_raw, *, build_tag, retain):
    identity = transport.exchange(b'\xfc\x78' + b'\xff' * 14, read_length=16)
    require(identity == b'\xfc\x78HYW1\1\1' + A.to_bytes(4, 'big') + (32768).to_bytes(4, 'big'),
            'operational writer identity differs; no handoff')
    raw = transport.exchange(b'\xfd\x88' + b'\xff' * 14, read_length=128)
    retain(raw)
    record = validate_audit_record(raw, base=A, build_tag=build_tag, expected_mutations_enabled=True)
    require(record['error'] == 0 and record['rx_guards_ok'] == record['stack_guards_ok'] == 1
            and record['stack_observed_bytes'] > 0 and not record['sr1'] & 0x7f and not record['sr2'] & 0x40,
            'fresh writer audit reports error/guards/busy/protection; no handoff')
    require(raw == expected_raw, 'fresh writer differs from exact acknowledged-read state; no handoff')
    return record


def prepare_inspection():
    pins = json.loads(PINS.read_bytes());verify_recorded_hashes(pins)
    _, prepared, artifact, payload = installation_prepare()
    installation, backup = prepared.installation, prepared.stock_backup
    prior_raw = (ROOT / 'analysis/hardware/mini-mcn-install-run.json').read_bytes();prior = json.loads(prior_raw)
    require(prior.get('finished_utc') and prior['error_phase'] == 'install_and_verify_application'
            and prior['error_details']['cdb_hex'] == 'fd88ffffffffffffffffffffffffffff'
            and prior['error_details']['win32_error'] == 31 and prior['known_live_slot'] == A
            and not prior['jump_outcome_unknown'] and not prior['mutation_completion_unknown']
            and not prior['writer_final']['mutation_completion_unknown']
            and prior['MCN_pause_closed'] and prior['MCN_explicitly_reenabled']
            and prior['read_recovery_final']['recovery_attempts'] == 8, 'unexpected stopped fourth install')
    old = prior['writer_final']['last_audit']
    require((old['sector'],old['page'],old['sequence'],old['token'],old['erase_attempts'],old['program_attempts'],old['wren_attempts'],old['page_bitmap'],old['read_bytes'])
            == (0x4d000,0x4d900,22,71,71,1130,1201,0x3ff,3411200), 'last validated writer state differs')
    require(prior['writer_final']['verified_sectors'] == list(range(0x7000,0x4d000,4096)), 'completed sector history differs')
    trace = [json.loads(line) for line in (ROOT / 'analysis/hardware/mini-mcn-install-trace.jsonl').read_text().splitlines()]
    tail = trace[-8:]
    require([row['state'] for row in tail] == ['before','after']*3+['before','error']
            and [row['cdb'] for row in tail[::2]] == ['fd88ffffffffffffffffffffffffffff',
                'fd7f0004d9000100ffffffffffffffff','fc7effffffffffffffffffffffffffff','fd88ffffffffffffffffffffffffffff'],
            'acknowledged-read/status/audit-error ordering differs')
    old_raw = bytes.fromhex(tail[1]['response_hex'])
    require(sha(old_raw) == 'f6175849f2d136318d6b3dcc676f52fcb7867b3b6fd621a33e0a6bd125433298'
            and validate_audit_record(old_raw,base=A,build_tag=installation.build_tag,expected_mutations_enabled=True) == old,
            'last raw audit is not the validated target record')
    page = installation.candidate[0x4d900-0x4000:0x4da00-0x4000]
    require(tail[3]['response_bytes'] == 256 and tail[3]['response_sha256'] == sha(page)
            and tail[5]['response_hex'] == 'fc7e00030000004700000016af70a76d'
            and zlib.crc32(page) == old['last_crc32'] == 0xaf70a76d, 'last read/page/status differs')
    mutations = [row for row in trace if row['state'] == 'after' and row['cdb'][:4] in ('fc7b','fc7d')]
    for op, order in (('fc7b',list(range(0x7000,0x4e000,4096))),('fc7d',list(range(0x7000,0x4da00,256)))):
        rows = [row for row in mutations if row['cdb'].startswith(op)]
        require([int.from_bytes(bytes.fromhex(row['cdb'])[10:14],'big') for row in rows] == order
                and all(bytes.fromhex(row['response_hex'])[2] == 0 for row in rows), 'mutation address/ACK history differs')
    expected = bytearray(backup)
    expected[0x5000:0x4da00] = installation.candidate[0x1000:0x49a00]
    expected[0x4da00:0x4e000] = b'\xff' * 0x600
    expected = bytes(expected)
    require(sha(expected) == '568e4f7d2b4f048ea45bcc3b0fc7b87a705442ea91fee6d4572a1bf9716dc699', 'partial image prediction changed')
    expected_raw = bytearray(old_raw)
    struct.pack_into('<I',expected_raw,80,old['read_bytes']+256)
    struct.pack_into('<I',expected_raw,120,zlib.crc32(expected_raw[:120]))
    require(old['stack_observed_bytes'] == 112, 'expected read branch stack observation differs')
    # The last FD7F and FC7E are ACKNOWLEDGED. The failed FD88 is a RAM snapshot
    # with no state counter, so only read_bytes +256 and its envelope CRC differ.
    return pins, installation, backup, artifact, payload, prior_raw, expected, bytes(expected_raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check-only', action='store_true')
    action.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    pins, installation, backup, artifact, payload, prior_raw, expected, expected_raw = prepare_inspection()
    if not args.execute:
        print(json.dumps({'preflight': 'pass', 'writes': False, 'reset': False,
                          'expected_full_sha256': sha(expected), 'expected_read_bytes': 3411456, 'expected_audit_sha256': sha(expected_raw),
                          'device_io': False, 'failed_command': 'FD88', 'mutation_completion_unknown': False}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'bounded SPT helper requires elevation')
    require(not any(p.exists() for p in (OUT, OUT.with_suffix('.json.tmp'), TRACE, AUDIT, DUMP)), 'inspection already attempted')
    result = {'phase': 'inspect_writer', 'started_utc': now(), 'firmware_write_this_step': False,
        'reset_performed': False, 'automatic_retry': False, 'prior_run_sha256': sha(prior_raw),
        'known_live_slot': None, 'jump_outcome_unknown': False, 'jump_attempts': 0, 'source_pins': pins,
        'runner_sha256': sha(Path(__file__).read_bytes()), 'backend': 'spt-buffered'}

    def save():
        atomic_write_json(OUT, result)

    def append(event):
        with TRACE.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(event) + '\n')
            stream.flush(); os.fsync(stream.fileno())

    def logged(transport):
        native = attach_native_diagnostic(transport)
        original = transport.exchange
        def exchange(cdb, data_out=None, read_length=0):
            time.sleep(0.005)
            event = {'state': 'before', 'utc': now(), 'cdb': cdb.hex(), 'read_length': read_length,
                     'out_bytes': len(data_out) if data_out is not None else 0}
            allowed = (0xfc78,0xfd88) if transport.slot == A else (0xfb06,0xfd07,0xfb08,0xfc70,0xfc72,0xfc73,0xfd71)
            require(int.from_bytes(cdb[:2], 'big') in allowed, 'inspection allowlist only; no NOR mutation or retry')
            if transport.slot == B and cdb[:2] in (b'\xfb\x06', b'\xfd\x07'):
                require(result['known_live_slot'] == A and not result['jump_outcome_unknown'], 'reader RAM must be inactive')
            if cdb[:2] == b'\xfb\x08':
                require(result['known_live_slot'] == A and not result['jump_outcome_unknown'] and transport.slot == B,
                        'only inactive reader B may be started once')
                result.update(known_live_slot=None, jump_outcome_unknown=True, jump_attempts=result['jump_attempts']+1); save()
            append(event)
            try: raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                event.update(state='error', finished_utc=now(), error=repr(error), details=getattr(error, 'details', {}),
                             native_transfer=transport.last_transfer, native_failure_observation=native.last_failure)
                append(event); raise
            event.update(state='after', finished_utc=now(), response_bytes=len(raw), response_sha256=sha(raw), native_transfer=transport.last_transfer)
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
            def keep(raw):
                with AUDIT.open('xb') as stream:
                    stream.write(raw);stream.flush();os.fsync(stream.fileno())
            result['writer_audit'] = confirm_writer(transport, expected_raw,
                build_tag=installation.build_tag, retain=keep)
        result['known_live_slot'] = A
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
