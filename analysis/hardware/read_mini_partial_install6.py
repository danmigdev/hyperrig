"""Read-only inspection after the sixth install lost a PROGRAM reply (FC7D).

Reconcile the prior state or a complete PROGRAM, then switch inactive B to
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
from run_mini_echo_install import prepare as installation_prepare, require, A, B
from tools.build_mini_boot import verify_recorded_hashes
from tools.mini_host_journal import atomic_write_json
from run_mini_receive_stress import attach_native_diagnostic
from tools.probe_mini_recovery import discover_windows_rom_disks, MiniNorSession
from tools.mini_windows_quiet import RomDiskAttestation, QuietBufferedRomTransport
from tools.build_mini_app_writer import validate_audit_record

PREFIX = 'analysis/hardware/mini-partial-inspect6'
OUT, TRACE, AUDIT = (ROOT / (PREFIX + suffix) for suffix in ('-run.json', '-trace.jsonl', '-writer-audit.bin'))
DUMP = ROOT / 'artifacts/my-mini-flash/first-install/full-partial6.bin'
PINS = ROOT / (PREFIX + '-pins.json')

def now(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()


def prior_program_witness(old_raw, *, build_tag):
    old = validate_audit_record(old_raw, base=A, build_tag=build_tag, expected_mutations_enabled=True)
    require(old['error'] == 0 and old['phase'] == 4 and old['staged'] == old['echoed'] == 1
            and old['rx_guards_ok'] == old['stack_guards_ok'] == 1
            and old['stack_observed_bytes'] == 52 and old['raw_receive_return'] == 260
            and not old['sr1'] & 0x7f and not old['sr2'] & 0x40
            and (old['token'],old['sequence'],old['sector'],old['page'],old['page_bitmap'])
                == (6,33,0x54000,0x54f00,0x7fff),
            'prior audit is not the exact guarded final-page PROGRAM precondition')
    return old


def completed_program_record(old_raw, *, build_tag, polls):
    """Exact successful frozen-core delta; poll count is bounded by its loop."""
    old = prior_program_witness(old_raw, build_tag=build_tag)
    require(type(polls) is int and 1 <= polls-old['status_polls'] <= 65536,
            'PROGRAM WIP poll increment outside frozen target bound')
    raw = bytearray(old_raw)
    changes = {16:3,28:34,68:old['wren_attempts']+1,76:old['program_attempts']+1,
               80:old['read_bytes']+512,84:polls,96:0xffff,100:0,104:0,112:112}
    for offset,value in changes.items(): struct.pack_into('<I',raw,offset,value)
    struct.pack_into('<I',raw,120,zlib.crc32(raw[:120]))
    return bytes(raw)


def confirm_writer(transport, old_raw, *, build_tag, retain):
    prior_program_witness(old_raw, build_tag=build_tag)
    identity = transport.exchange(b'\xfc\x78' + b'\xff' * 14, read_length=16)
    require(identity == b'\xfc\x78HYW1\1\1' + A.to_bytes(4,'big') + (32768).to_bytes(4,'big'),
            'operational writer identity differs; no handoff')
    raw = transport.exchange(b'\xfd\x88' + b'\xff' * 14, read_length=128)
    retain(raw)
    record = validate_audit_record(raw,base=A,build_tag=build_tag,expected_mutations_enabled=True)
    require(record['error'] == 0 and record['rx_guards_ok'] == record['stack_guards_ok'] == 1
            and not record['sr1'] & 0x7f and not record['sr2'] & 0x40,
            'fresh writer audit reports error/guards/busy/protection; no handoff')
    if raw == old_raw:
        return record, 'prior_state_retained'
    expected = completed_program_record(old_raw,build_tag=build_tag,polls=record['status_polls'])
    require(raw == expected, 'fresh writer is neither prior state nor exact completed PROGRAM; no handoff')
    return record, 'program_completed'


def prepare_inspection():
    pins = json.loads(PINS.read_bytes()); verify_recorded_hashes(pins)
    _, prepared, artifact, payload = installation_prepare()
    installation, backup = prepared.installation, prepared.stock_backup
    prior_raw = (ROOT / 'analysis/hardware/mini-echo-install-run.json').read_bytes(); prior = json.loads(prior_raw)
    require(prior.get('finished_utc') and prior['error_phase'] == 'install_and_verify_application'
            and prior['error_details']['cdb_hex'] == 'fc7d000000060000002200054f00ffff'
            and prior['error_details']['win32_error'] == 31 and prior['known_live_slot'] == A
            and not prior['jump_outcome_unknown'] and prior['mutation_completion_unknown'] is True
            and prior['writer_final']['mutation_completion_unknown'] is True
            and prior['MCN_pause_closed'] and prior['MCN_explicitly_reenabled']
            and prior['read_recovery_final']['recovery_attempts'] == 1
            and prior['read_recovery_final']['audit_reconciliations'] == 1
            and prior['read_recovery_final']['echo_reissues'] == 0, 'unexpected stopped sixth install')
    old = prior['writer_final']['last_audit']
    require((old['sector'],old['page'],old['sequence'],old['token'],old['erase_attempts'],
             old['program_attempts'],old['wren_attempts'],old['page_bitmap'],old['read_bytes'],
             old['status_polls'],old['phase'],old['staged'],old['echoed'],old['stack_observed_bytes'])
            == (0x54000,0x54f00,33,6,6,95,101,0x7fff,752896,1067,4,1,1,52),
            'last validated writer state differs')
    require(prior['writer_final']['verified_sectors'] == list(range(0x4f000,0x54000,4096)),
            'completed sector history differs')
    trace = [json.loads(line) for line in (ROOT / 'analysis/hardware/mini-echo-install-trace.jsonl').read_text().splitlines()]
    tail = trace[-12:]
    require([row['state'] for row in tail] == ['before','after']*5+['before','error']
            and [row['cdb'] for row in tail[::2]] == ['fb7c000000060000002100054f000100',
                'fc7effffffffffffffffffffffffffff','fd88ffffffffffffffffffffffffffff',
                'fd87000000060000002100054f00ffff','fd88ffffffffffffffffffffffffffff',
                'fc7d000000060000002200054f00ffff'], 'stage/echo/audit/PROGRAM-error ordering differs')
    errors = [row for row in trace if row['state']=='error']
    require(len(errors)==2 and errors[0]['cdb'].startswith('fd88') and errors[-1]==tail[-1]
            and all(row['native_transfer']['win32_error']==31 for row in errors),
            'unexpected command failure history')
    old_raw = bytes.fromhex(tail[9]['response_hex'])
    require(sha(old_raw) == '61b502e93f80ba0a432067c173aaebab5d1b7d8c72ec2cc0e40c76ce0f6f755c'
            and prior_program_witness(old_raw,build_tag=installation.build_tag) == old,
            'last raw audit is not the validated target record')
    page = installation.candidate[0x54f00-0x4000:0x55000-0x4000]
    require(tail[1]['response_bytes']==0 and tail[1]['out_bytes']==260
            and tail[3]['response_hex']=='fc7e00040000000600000021978a52db'
            and tail[7]['response_bytes']==256 and tail[7]['response_sha256']==sha(page)
            and zlib.crc32(page)==old['page_crc32']==old['last_crc32']==0x978a52db,
            'last staging/echo/page/status differs')
    mutations = [row for row in trace if row['state']=='after' and row['cdb'][:4] in ('fc7b','fc7d')]
    for op,order in (('fc7b',list(range(0x4f000,0x55000,4096))),
                     ('fc7d',list(range(0x4f000,0x54f00,256)))):
        rows = [row for row in mutations if row['cdb'].startswith(op)]
        require([int.from_bytes(bytes.fromhex(row['cdb'])[10:14],'big') for row in rows]==order
                and all(bytes.fromhex(row['response_hex'])[2]==0 for row in rows),
                'mutation address/ACK history differs')
    pp_audits=[]
    for index,row in enumerate(trace):
        if row['state']=='after' and row['cdb'].startswith('fc7d'):
            following=trace[index+1:index+3]
            require(len(following)==2 and following[0]['cdb']=='fd88'+'ff'*14
                    and following[1]['state']=='after','preceding PP lacks its immediate complete audit')
            record=validate_audit_record(bytes.fromhex(following[1]['response_hex']),base=A,
                build_tag=installation.build_tag,expected_mutations_enabled=True)
            require(record['error']==0 and record['phase']==3 and record['staged']==record['echoed']==0
                    and record['stack_guards_ok']==1 and record['stack_observed_bytes']==112,
                    'physically observed successful PROGRAM stack differs')
            pp_audits.append(record)
    require(len(pp_audits)==95,'all95 preceding PROGRAM audit witnesses required')
    require(sha(prepared.full_preimage)=='6caadab79b35c5ad257f465ecd2a864646cb23e6f2093453bf749949fde7c1c3',
            'sixth installation preimage differs')
    missing=bytearray(prepared.full_preimage)
    missing[0x4f000:0x54f00]=installation.candidate[0x4b000:0x50f00]
    missing[0x54f00:0x55000]=b'\xff'*256
    complete=bytearray(missing);complete[0x54f00:0x55000]=page
    expected={'prior_state_retained':bytes(missing),'program_completed':bytes(complete)}
    require(sha(expected['prior_state_retained'])=='af52c13f74df88b417cff00dd1e0536f37a00a163808375ae2d11f8c7e43da0d'
            and sha(expected['program_completed'])=='614f19f3b5a6b526cd20f7111cc9a87266255affff454ccc94c4854ff743d7f1',
            'partial image predictions changed')
    return pins,installation,backup,artifact,payload,prior_raw,expected,old_raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check-only', action='store_true')
    action.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    pins, installation, backup, artifact, payload, prior_raw, expected_images, old_raw = prepare_inspection()
    if not args.execute:
        print(json.dumps({'preflight': 'pass', 'writes': False, 'reset': False,
                          'expected_full_sha256': {key:sha(value) for key,value in expected_images.items()},
                          'prior_audit_sha256': sha(old_raw), 'complete_PROGRAM_poll_delta': [1,65536],
                          'device_io': False, 'failed_command': 'FC7D', 'mutation_completion_unknown': True}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'bounded SPT helper requires elevation')
    require(not any(p.exists() for p in (OUT, OUT.with_suffix('.json.tmp'), TRACE, AUDIT, DUMP)), 'inspection already attempted')
    result = {'phase': 'inspect_writer', 'started_utc': now(), 'firmware_write_this_step': False,
        'reset_performed': False, 'automatic_retry': False, 'prior_run_sha256': sha(prior_raw),
        'known_live_slot': None, 'jump_outcome_unknown': False, 'jump_attempts': 0, 'source_pins': pins,
        'runner_sha256': sha(Path(__file__).read_bytes()), 'backend': 'spt-buffered', 'constructor': 'quiet-attested',
        'MCN_pause_requested': False, 'prior_audit_sha256': sha(old_raw),
        'prior_mutation_completion_unknown': True, 'mutation_completion_unknown': True,
        'expected_full_sha256': {key:sha(value) for key,value in expected_images.items()}}

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
        attestation = RomDiskAttestation.from_discovery(candidates[0])
        with QuietBufferedRomTransport(attestation, slot=A, profile='app-writer-operational') as transport:
            attestation = transport.attestation
            result['writer_open_metadata'] = transport.open_metadata
            logged(transport)
            result['adapter_descriptor'] = transport.adapter_descriptor
            def keep(raw):
                with AUDIT.open('xb') as stream:
                    stream.write(raw);stream.flush();os.fsync(stream.fileno())
            result['writer_audit'], outcome = confirm_writer(transport, old_raw,
                build_tag=installation.build_tag, retain=keep)
            result['program_outcome'] = outcome
            result['writer_software_state_reconciled'] = True
            expected = expected_images[outcome]
            result['selected_expected_full_sha256'] = sha(expected)
        result['known_live_slot'] = A
        result['phase'] = 'full_NOR_read'; save()
        with QuietBufferedRomTransport(attestation, slot=B, profile='nor-reader') as transport:
            result['reader_open_metadata'] = transport.open_metadata
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
            result['reader_successful_bytes'] = reader.successful_bytes
        with DUMP.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        result.update(dump_path=DUMP.relative_to(ROOT).as_posix(), dump_sha256=sha(data),
            matches_expected_partial=data == expected,
            changed_sectors=[a for a in range(0, 0x100000, 4096) if data[a:a+4096] != backup[a:a+4096]],
            phase='read_complete')
        require(data == expected, 'fresh dump differs from confirmed completed mutations')
        result['phase'] = 'partial_image_verified'
        result['mutation_completion_unknown'] = False
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error))
    finally:
        result['finished_utc'] = now(); save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'dump_sha256', 'matches_expected_partial', 'known_live_slot')}))

if __name__ == '__main__': main()
