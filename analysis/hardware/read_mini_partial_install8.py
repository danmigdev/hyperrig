"""Inspect the eighth install's lost FD88 after accepted RAM staging.

Default is offline. Writer reconciliation requires the exact completed STAGE acknowledged by
FC7E. The preceding audit is stale. There is no STAGE reissue, NOR write
or reset. The reader's bounded recovery accounts for real physical reads.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import site
import struct
import sys
import time
import zlib

user_site = site.getusersitepackages()
if isinstance(user_site, str) and user_site not in sys.path:
    sys.path.append(user_site)  # Explicit dependency directory for broker -I; no .pth execution.
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis/hardware'), str(ROOT / 'tools'), str(ROOT)]
from run_mini_complete_install import prepare as installation_prepare, require, A, B
from tools.build_mini_boot import verify_recorded_hashes
from tools.build_mini_app_writer import validate_audit_record
from tools.mini_host_journal import atomic_write_json
from tools.mini_nor_read_recovery import NorReadRecoveryTransport
from tools.mini_windows_quiet import RomDiskAttestation, QuietBufferedRomTransport
from tools.probe_mini_recovery import MiniNorSession
from run_mini_receive_stress import attach_native_diagnostic

PREFIX = 'analysis/hardware/mini-partial-inspect8'
OUT, TRACE, AUDIT, RECOVERY = (ROOT / (PREFIX + suffix) for suffix in
    ('-run.json', '-trace.jsonl', '-writer-audit.bin', '-read-recovery.jsonl'))
PINS = ROOT / (PREFIX + '-pins.json')
DUMP = ROOT / 'artifacts/my-mini-flash/first-install/full-partial8.bin'
PRIOR = ROOT / 'analysis/hardware/mini-complete-install-run.json'
PRIOR_TRACE = ROOT / 'analysis/hardware/mini-complete-install-trace.jsonl'
OLD_SHA = '8457d9dd3a62e5b002d2ba1fa230f6e63df487c5bd4837064a814081ea1b81ad'
EXPECTED_SHA = '5e2e50052118a279b9790478b18e7c846a067d2d4f5945665db65811bd35fa8a'


def now(): return datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()


def prior_stage_witness(raw, *, build_tag):
    record = validate_audit_record(raw, base=A, build_tag=build_tag, expected_mutations_enabled=True)
    require(sha(raw) == OLD_SHA and record['error'] == 0
        and record['rx_guards_ok'] == record['stack_guards_ok'] == 1
        and not record['sr1'] & 0x7f and not record['sr2'] & 0x40
        and (record['phase'], record['token'], record['sequence'], record['sector'], record['page'],
             record['page_bitmap'], record['staged'], record['echoed'], record['stack_observed_bytes'],
             record['wren_attempts'], record['erase_attempts'], record['program_attempts'],
             record['read_bytes'], record['status_polls'])
            == (3, 21, 22, 0x73000, 0x73900, 0x3ff, 0, 0, 112, 351, 21, 330, 1363456, 3715),
        'prior audit is not the pinned guarded record before STAGE')
    return record


def completed_stage_record(old_raw, *, build_tag):
    """Frozen FB7C + successful FC7E: copy260, CRC check, stage; no NOR IO.

    The accepted sequence23/page0x73A00 and CRC are in the real FC7E reply.
    Every preceding immediate STAGE audit in this session reports stack52.
    """
    prior_stage_witness(old_raw, build_tag=build_tag)
    raw = bytearray(old_raw)
    for offset, value in {16: 4, 28: 23, 36: 0x73a00, 48: 0xfbf194f8,
                          52: 0xfbf194f8, 100: 1, 104: 0, 112: 52}.items():
        struct.pack_into('<I', raw, offset, value)
    struct.pack_into('<I', raw, 120, zlib.crc32(raw[:120]))
    return bytes(raw)


def confirm_writer(transport, old_raw, *, build_tag, retain):
    expected = completed_stage_record(old_raw, build_tag=build_tag)
    identity = transport.exchange(b'\xfc\x78' + b'\xff' * 14, read_length=16)
    require(identity == b'\xfc\x78HYW1\1\1' + struct.pack('>II', A, 32768),
            'operational writer identity differs; no handoff')
    raw = transport.exchange(b'\xfd\x88' + b'\xff' * 14, read_length=128)
    retain(raw)
    require(raw == expected, 'fresh writer differs from the exact acknowledged STAGE; no handoff')
    record = validate_audit_record(raw, base=A, build_tag=build_tag, expected_mutations_enabled=True)
    return record, 'acknowledged_stage_confirmed'


def validate_stopped_trace(prior, rows, installation):
    require(prior.get('finished_utc') and prior['error_phase'] == 'install_and_verify_application'
        and prior['error_details']['cdb_hex'] == 'fd88' + 'ff' * 14
        and prior['error_details']['win32_error'] == 31 and prior['known_live_slot'] == A
        and not prior['jump_outcome_unknown'] and prior['mutation_completion_unknown'] is False
        and prior['writer_final']['mutation_completion_unknown'] is False
        and prior['MCN_pause_closed'] and prior['MCN_explicitly_reenabled'], 'unexpected stopped eighth install')
    require(prior['writer_final']['verified_sectors'] == list(range(0x5f000, 0x73000, 4096)),
            'completed sector history differs')
    require(len(rows) % 2 == 0, 'unpaired prior trace')
    for before, after in zip(rows[::2], rows[1::2]):
        require(before['state'] == 'before' and after['state'] in ('after', 'error')
                and before['cdb'] == after['cdb'], 'prior trace pairing differs')
    tail = rows[-12:]
    require([r['state'] for r in tail] == ['before', 'after'] * 5 + ['before', 'error']
        and [r['cdb'] for r in tail[::2]] == ['fd7f000739000100ffffffffffffffff',
            'fc7e' + 'ff' * 14, 'fd88' + 'ff' * 14, 'fb7c000000150000001700073a000100',
            'fc7e' + 'ff' * 14, 'fd88' + 'ff' * 14],
        'last PROGRAM readback/audit/STAGE/status/fault ordering differs')
    old_raw = bytes.fromhex(tail[5]['response_hex'])
    old = prior_stage_witness(old_raw, build_tag=installation.build_tag)
    require(old == prior['writer_final']['last_audit'], 'prior raw audit differs from validated host state')
    last_page = installation.candidate[0x6f900:0x6fa00]
    staged_page = installation.candidate[0x6fa00:0x6fb00]
    require(tail[1]['response_bytes'] == 256 and tail[1]['response_sha256'] == sha(last_page)
        and zlib.crc32(last_page) == old['page_crc32'] == old['last_crc32']
        and tail[3]['response_hex'] == 'fc7e00030000001500000016c9d8ceb4'
        and tail[7]['out_bytes'] == 260 and tail[7]['response_bytes'] == 0
        and tail[9]['response_hex'] == 'fc7e00040000001500000017fbf194f8'
        and zlib.crc32(staged_page) == 0xfbf194f8
        and prior['writer_final']['last_status'] == {'error': 0, 'phase': 4, 'token': 21,
            'sequence': 23, 'last_crc32': 0xfbf194f8}, 'acknowledged STAGE or prior page readback differs')
    errors = [r for r in rows if r['state'] == 'error']
    require([r['cdb'] for r in errors] == ['fd88' + 'ff' * 14] * 3 + [
        'fd7f0006a6000200ffffffffffffffff', 'fd7f0006c1000100ffffffffffffffff'] + [
        'fd88' + 'ff' * 14] * 2 + ['fc7e' + 'ff' * 14, 'fd88' + 'ff' * 14]
        and all(r['native_transfer']['win32_error'] == 31 for r in errors), 'prior failure history differs')
    recovery = prior['read_recovery_final']
    require(recovery['version'] == 5 and recovery['recovery_attempts'] == 8
        and (recovery['read_reissues'], recovery['query_reissues'], recovery['audit_reconciliations']) == (2, 1, 5)
        and recovery['mutation_request_reissues'] == recovery['finish_request_reissues'] == 0
        and recovery['completed_NOR_mutations_repeated'] == 0, 'prior bounded recovery outcomes differ')
    for opcode, order in (('fc7b', list(range(0x5f000, 0x74000, 4096))),
                          ('fc7d', list(range(0x5f000, 0x73a00, 256))),
                          ('fc80', list(range(0x5f000, 0x73000, 4096)))):
        successful = [r for r in rows if r['state'] == 'after' and r['cdb'].startswith(opcode)]
        require([int.from_bytes(bytes.fromhex(r['cdb'])[10:14], 'big') for r in successful] == order
            and all(bytes.fromhex(r['response_hex'])[2] == 0 for r in successful),
            'mutation/FINISH address or ACK history differs')
    page_reads = [r for r in rows if r['state'] == 'after' and r['cdb'].startswith('fd7f')
                  and int.from_bytes(bytes.fromhex(r['cdb'])[6:8], 'big') == 256]
    require(len(page_reads) == 330, 'all330 page readbacks required')
    for address, row in zip(range(0x5f000, 0x73a00, 256), page_reads):
        require(int.from_bytes(bytes.fromhex(row['cdb'])[2:6], 'big') == address
            and row['response_bytes'] == 256
            and row['response_sha256'] == sha(installation.candidate[address-0x4000:address-0x3f00]),
            'preceding programmed page readback differs from candidate')
    stage_records = []
    for index, row in enumerate(rows):
        if row['state'] == 'after' and row['cdb'].startswith('fb7c'):
            following = rows[index+1:]
            audit_index = next((i for i, r in enumerate(following)
                if r['state'] == 'after' and r['cdb'] == 'fd88' + 'ff' * 14), None)
            if audit_index is None:
                require(row == tail[7], 'only the last STAGE may lack its audit'); continue
            require(not any(r['cdb'].startswith(('fb7c', 'fc7b', 'fc7d', 'fc80', 'fd87'))
                for r in following[:audit_index]), 'STAGE audit follows another state-changing command')
            record = validate_audit_record(bytes.fromhex(following[audit_index]['response_hex']), base=A,
                build_tag=installation.build_tag, expected_mutations_enabled=True)
            require(record['error'] == 0 and record['phase'] == 4 and record['staged'] == 1 and record['echoed'] == 0
                and record['stack_guards_ok'] == 1 and record['stack_observed_bytes'] == 52,
                'physical STAGE stack/state witness differs')
            stage_records.append(record)
    require(len(stage_records) == 330, 'all330 preceding STAGE audit witnesses required')
    return old_raw


def prepare_inspection():
    pins = json.loads(PINS.read_bytes()); verify_recorded_hashes(pins)
    _, prepared, artifact, payload = installation_prepare()
    installation, backup = prepared.installation, prepared.stock_backup
    prior_raw = PRIOR.read_bytes(); prior = json.loads(prior_raw)
    rows = [json.loads(line) for line in PRIOR_TRACE.read_text(encoding='utf-8').splitlines()]
    old_raw = validate_stopped_trace(prior, rows, installation)
    require(sha(prepared.full_preimage) == '56187d88750d5b9fb5de5fa34be52769b9612d5063f81ed1933964be81c959e5',
            'eighth installation preimage differs')
    expected = bytearray(prepared.full_preimage)
    expected[0x5f000:0x73a00] = installation.candidate[0x5b000:0x6fa00]
    expected[0x73a00:0x74000] = b'\xff' * 0x600
    direct = backup[:0x5000] + installation.candidate[0x1000:0x6fa00] + b'\xff' * 0x600 + backup[0x74000:]
    require(expected == direct and sha(expected) == EXPECTED_SHA, 'partial NOR prediction differs')
    metadata = prior['transport_handles'][-1]
    require(metadata['slot'] == A and metadata['profile'] == 'app-writer-operational', 'last handle is not writerA')
    binding = metadata['open_metadata']['attestation']
    attestation = RomDiskAttestation(binding['path'], binding['pnp_id'], binding['usb_ancestor'],
        tuple(binding['chain']), binding['model'], binding['interface_path'], binding['last_arrival_filetime'])
    require(attestation.summary() == binding, 'retained PnP/arrival attestation differs')
    return pins, installation, backup, artifact, payload, prior_raw, bytes(expected), old_raw, attestation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check-only', action='store_true'); action.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    pins, installation, backup, artifact, payload, prior_raw, expected, old_raw, attestation = prepare_inspection()
    if not args.execute:
        print(json.dumps({'preflight': 'pass', 'device_io': False, 'NOR_writes': False, 'reset': False,
            'expected_full_sha256': sha(expected), 'prior_audit_sha256': sha(old_raw),
            'acknowledged_STAGE_audit_sha256': sha(completed_stage_record(old_raw, build_tag=installation.build_tag)),
            'complete_candidate_sectors': 110, 'remaining_sectors': 16, 'discovery': 'retained-attestation',
            'max_read_recoveries': 8}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'bounded SPT helper requires elevation')
    require(not any(p.exists() for p in (OUT, OUT.with_suffix('.json.tmp'), TRACE, AUDIT, RECOVERY, DUMP)),
            'inspection already attempted')
    result = {'phase': 'inspect_writer', 'started_utc': now(), 'source_pins': pins,
        'runner_sha256': sha(Path(__file__).read_bytes()), 'prior_run_sha256': sha(prior_raw),
        'firmware_write_this_step': False, 'reset_performed': False, 'mutation_completion_unknown': False,
        'known_live_slot': None, 'jump_outcome_unknown': False, 'jump_attempts': 0,
        'backend': 'spt-buffered', 'constructor': 'quiet-attested', 'MCN_pause_requested': False,
        'prior_audit_sha256': sha(old_raw), 'expected_full_sha256': sha(expected), 'max_read_recoveries': 8}
    wrapper = reader = None

    def save(): atomic_write_json(OUT, result)
    def append(path, event):
        with path.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(event) + '\n'); stream.flush(); os.fsync(stream.fileno())

    def open_logged(slot, profile):
        nonlocal attestation
        current = QuietBufferedRomTransport(attestation, slot=slot, profile=profile)
        attestation = current.attestation
        try:
            result.setdefault('transport_handles', []).append({'slot': slot, 'profile': profile,
                'open_metadata': current.open_metadata}); save()
            native = attach_native_diagnostic(current); original = current.exchange
            def exchange(cdb, data_out=None, read_length=0):
                allowed = (0xfc78, 0xfd88) if slot == A else (0xfb06, 0xfd07, 0xfb08, 0xfc70, 0xfc72, 0xfc73, 0xfd71)
                op = int.from_bytes(cdb[:2], 'big')
                require(op in allowed, 'inspection command allowlist; no NOR mutation/FINISH/reset')
                if op in (0xfb06, 0xfd07, 0xfb08):
                    require(slot == B and result['known_live_slot'] == A and not result['jump_outcome_unknown'],
                            'reader RAM must be known inactive')
                if op == 0xfb08:
                    require(result['jump_attempts'] == 0, 'single reader start only')
                    result.update(known_live_slot=None, jump_outcome_unknown=True, jump_attempts=1); save()
                time.sleep(.005)
                event = {'state': 'before', 'utc': now(), 'cdb': cdb.hex(), 'read_length': read_length,
                         'out_bytes': len(data_out) if data_out is not None else 0, 'slot': slot}
                append(TRACE, event)
                try: raw = original(cdb, data_out=data_out, read_length=read_length)
                except Exception as error:
                    event.update(state='error', finished_utc=now(), error=repr(error), details=getattr(error, 'details', {}),
                        native_transfer=current.last_transfer, native_failure_observation=native.last_failure)
                    append(TRACE, event); raise
                event.update(state='after', finished_utc=now(), response_bytes=len(raw), response_sha256=sha(raw),
                             native_transfer=current.last_transfer)
                if len(raw) <= 128: event['response_hex'] = raw.hex()
                append(TRACE, event)
                if op == 0xfc73: current.last_reader_status_raw = raw
                return raw
            current.exchange = exchange
            return current
        except BaseException:
            current.close(); raise

    def reopen_reader():
        require(result['known_live_slot'] == B and not result['jump_outcome_unknown'], 'readerB lifecycle changed')
        return open_logged(B, 'nor-reader')

    save()
    try:
        with open_logged(A, 'app-writer-operational') as transport:
            def retain(raw):
                with AUDIT.open('xb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            result['writer_audit'], result['stage_outcome'] = confirm_writer(transport, old_raw,
                build_tag=installation.build_tag, retain=retain)
            result['writer_software_state_reconciled'] = True
        result.update(known_live_slot=A, phase='full_NOR_read'); save()
        with open_logged(B, 'nor-reader') as transport:
            reader = MiniNorSession(transport, slot=B, known_free_slot=True)
            result['reader_session'] = reader.upload_and_start(payload, expected_sha256=artifact['flat_sha256'])
            result.update(known_live_slot=B, jump_outcome_unknown=False)
            result['reader_SPI'] = reader.initialize_spi()
            require(result['reader_SPI']['jedec_hex'] == 'eb6014', 'NOR identity differs')
            wrapper = NorReadRecoveryTransport(transport, log=lambda event: append(RECOVERY, event),
                reopen_factory=reopen_reader, max_recoveries=8)
            wrapper.bind_session(reader, status_raw=transport.last_reader_status_raw)
            def progress(done, total):
                if done % 65536 == 0: result['progress'] = {'bytes': done, 'total': total}; save()
            data = reader.read_flash(0, 0x100000, progress=progress)
            require(reader.successful_bytes == len(data) + wrapper.lost_read_bytes,
                    'final physical counter must include all received and lost reads')
            result['final_reader_counter'] = reader.successful_bytes
            result['final_reader_status_hex'] = wrapper.last_status_raw.hex()
        with DUMP.open('xb') as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        result.update(dump_path=DUMP.relative_to(ROOT).as_posix(), dump_sha256=sha(data),
            matches_expected_partial=data == expected,
            changed_sectors=[a for a in range(0, 0x100000, 4096) if data[a:a+4096] != backup[a:a+4096]],
            phase='read_complete')
        require(data == expected, 'fresh NOR differs from completed PROGRAM/readback witnesses')
        result.update(phase='partial_image_verified', complete_candidate_sectors=110, candidate_pages_in_partial_sector=10,
                      remaining_sectors=16, mutation_completion_unknown=False)
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error))
    finally:
        if wrapper is not None: wrapper.close(); result['read_recovery_final'] = wrapper.summary()
        if reader is not None: result['last_confirmed_reader_counter'] = reader.successful_bytes
        result['finished_utc'] = now(); save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'dump_sha256', 'matches_expected_partial', 'final_reader_counter')}))


if __name__ == '__main__': main()
