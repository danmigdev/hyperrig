"""Third, separately reviewed installation using the qualified buffered backend.

The full NOR read after the buffered trial is the immutable current preimage.
An explicit --recover-read-once can enable one FD7F Win31 recovery after an
identical target audit. No mutation, jump, reset or other command is retried.
No reset, boot, rollback or backend fallback is performed, including on error.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis/hardware'), str(ROOT / 'tools'), str(ROOT)]
from tools.build_mini_boot import verify_recorded_hashes
from tools.probe_mini_recovery import discover_windows_rom_disks, MiniNorSession
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.install_mini_app import MiniAppInstallerSession
from tools.recover_mini_read import ReadOnlyFailureRecoveryTransport
from tools.resume_mini_install import prepare_resume, validate_completed_full
from run_mini_first_install import prepare as original_prepare

A, B = 0x1C20000, 0x1C28000
PREFIX = 'analysis/hardware/mini-buffered-install'
OUT, TRACE, JOURNAL, RECOVERY = (ROOT / (PREFIX + suffix) for suffix in
    ('-run.json', '-trace.jsonl', '-journal.jsonl', '-read-recovery.jsonl'))
PINS = ROOT / (PREFIX + '-pins.json')
TRIAL = ROOT / 'analysis/hardware/mini-buffered-transport-run.json'
FULL_BEFORE = ROOT / 'artifacts/my-mini-flash/first-install/full-after-buffered-probe.bin'
FULL_AFTER = ROOT / 'artifacts/my-mini-flash/first-install/full-buffered-after.bin'
PLAN = ROOT / 'build/mini-install-buffered/resume-plan.json'
EXPECTED_PREIMAGE_SHA = '7fd0c32e295758fe8a3fdff40f5315cb83fa31091920c5b7f99fdd49aa05e4fc'
PACE = 0.005


def sha(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def require(condition, message):
    if not condition: raise ValueError(message)


def append(path, item, durable=False):
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(item) + '\n')
        if durable:
            stream.flush()
            os.fsync(stream.fileno())


def prepare():
    pins = json.loads(PINS.read_text(encoding='utf-8'))
    verify_recorded_hashes(pins)
    _, original, backup, reader_artifact, payload = original_prepare()
    trial = json.loads(TRIAL.read_text(encoding='utf-8'))
    verify_recorded_hashes(trial['source_pins'])
    require(trial['phase'] == 'buffered_transport_qualified_without_NOR_writes'
            and trial['transport_trial_passed'] is True and trial['full_NOR_unchanged'] is True
            and trial['known_live_slot'] == B and trial['jump_outcome_unknown'] is False
            and trial['NOR_writes_performed'] is False and trial['reset_performed'] is False
            and trial['page_reads_verified'] == 2016 and not trial.get('error')
            and trial['full_read_progress'] == {'bytes': 0x100000, 'total': 0x100000}
            and trial['full_NOR_sha256'] == EXPECTED_PREIMAGE_SHA
            and trial['backend'] == 'IOCTL_SCSI_PASS_THROUGH buffered',
            'buffered transport trial or complete read did not pass')
    prepared = prepare_resume(FULL_BEFORE, expected_partial_sha256=EXPECTED_PREIMAGE_SHA,
                              expected_modified_sectors=(0x5000,), slot=A)
    require(PLAN.read_bytes() == prepared.plan_bytes, 'retained buffered-install plan differs')
    require(prepared.installation.candidate == original.candidate,
            'third installation must retain the exact reviewed candidate')
    require(prepared.stock_backup == backup, 'stock backup provenance differs')
    return pins, prepared, reader_artifact, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--recover-read-once', action='store_true',
        help='explicitly enable one FD7F Win31 reopen/reissue after an identical validated audit')
    args = parser.parse_args()
    pins, prepared, reader_artifact, reader_payload = prepare()
    installation = prepared.installation
    recovery_policy = {'enabled': args.recover_read_once,
        'max_reopens': 1 if args.recover_read_once else 0,
        'max_read_reissues': 1 if args.recover_read_once else 0,
        'only_command': 'FD7F', 'only_Windows_error': 31,
        'exact_unchanged_previous_validated_audit_required': True,
        'other_command_retries_allowed': False, 'mutation_retries_allowed': False,
        'backend_fallback_allowed': False}
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'candidate': sha(installation.candidate),
            'preimage_full_NOR_sha256': EXPECTED_PREIMAGE_SHA, 'plan_sha256': installation.plan_sha256,
            'changed_sectors': len(installation.sector_order), 'backend': 'spt-buffered',
            'read_recovery_policy': recovery_policy, 'automatic_reset': False}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'Windows SPT requires the elevated bounded helper')
    require(not any(p.exists() for p in (OUT, TRACE, JOURNAL, RECOVERY, FULL_AFTER)),
            'one-shot output exists; do not rerun')
    result = {'started_utc': now(), 'phase': 'prepare', 'source_pins': pins,
              'installation': installation.summary(), 'known_live_slot': None,
              'jump_outcome_unknown': False, 'jump_attempts': 0,
              'mutation_command_submitted': False, 'mutation_completion_unknown': False,
              'installed_image_verified': False, 'full_NOR_verified': False,
              'automatic_reset': False, 'automatic_rollback': False,
              'automatic_mutation_retry': False, 'automatic_backend_fallback': False,
              'read_recovery_policy': recovery_policy,
              'retry_policy_scope': 'Installer core retries no commands; optional wrapper can reissue one proven-unexecuted FD7F only.',
              'power_loss_atomicity_proven': False,
              'continuation_of': 'analysis/hardware/mini-first-resume-run.json',
              'transport_trial': TRIAL.relative_to(ROOT).as_posix(),
              'transport_trial_sha256': sha(TRIAL.read_bytes()),
              'new_preimage_plan': PLAN.relative_to(ROOT).as_posix(),
              'command_spacing_seconds': PACE, 'backend': 'IOCTL_SCSI_PASS_THROUGH buffered'}
    path, writer, wrapper, writer_transport = None, None, None, None

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
        require(isinstance(transport, WindowsBufferedRomTransport), 'every handle must use the qualified buffered backend')
        result.setdefault('transport_handles', []).append({'label': label, 'path': transport.disk['path'],
            'slot': transport.slot, 'profile': transport.profile, 'inquiry': transport.inquiry,
            'adapter_descriptor': transport.adapter_descriptor, 'backend': 'spt-buffered'})
        save()
        original = transport.exchange
        def exchange(cdb, data_out=None, read_length=0):
            time.sleep(PACE)
            entry = {'stage': label, 'state': 'before', 'started_utc': now(), 'cdb': cdb.hex(),
                     'out_bytes': len(data_out) if data_out is not None else 0, 'in_bytes': read_length,
                     'backend': 'spt-buffered'}
            if cdb[:2] == b'\xfb\x08':
                require(result['known_live_slot'] != transport.slot and not result['jump_outcome_unknown'],
                        'jump requires a known inactive slot and no previous uncertain jump')
                result.update(known_live_slot=None, jump_outcome_unknown=True,
                              jump_attempts=result['jump_attempts'] + 1)
                save()
            if cdb[:2] in (b'\xfc\x7b', b'\xfc\x7d'):
                result.update(mutation_command_submitted=True, mutation_completion_unknown=True)
                save()
            append(TRACE, entry, durable=cdb[:2] in (b'\xfb\x08', b'\xfc\x7b', b'\xfc\x7d'))
            start = time.monotonic()
            try:
                raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                entry.update(state='error', finished_utc=now(), elapsed_ms=(time.monotonic() - start) * 1000,
                             error=repr(error), details=getattr(error, 'details', {}),
                             native_transfer=getattr(transport, 'last_transfer', None))
                append(TRACE, entry, durable=True)
                raise
            entry.update(state='after', finished_utc=now(), elapsed_ms=(time.monotonic() - start) * 1000,
                         response_bytes=len(raw), response_sha256=sha(raw),
                         native_transfer=getattr(transport, 'last_transfer', None))
            if len(raw) <= 128: entry['response_hex'] = raw.hex()
            append(TRACE, entry)
            return raw
        transport.exchange = exchange

    def open_logged(slot, profile, label):
        transport = WindowsBufferedRomTransport(path, slot=slot, profile=profile)
        try:
            logged(transport, label)
            return transport
        except BaseException:
            transport.close()
            raise

    def journal(item):
        append(JOURNAL, {'utc': now(), **item}, durable=item['event'] in
               ('command_intent', 'terminal_error', 'sector_verified', 'application_verified'))
        if item['event'] in ('sector_verified', 'application_verified'):
            result['writer_progress'] = item
            save()

    def recovery_log(item):
        # This separate log is durable for every event, including the decision
        # and audit proof BEFORE the one possible read reissue.
        append(RECOVERY, item, durable=True)

    def reopen_writer():
        require(result['known_live_slot'] == A and not result['jump_outcome_unknown'],
                'read recovery cannot reopen after a changed/unknown callback lifecycle')
        return open_logged(A, 'app-writer-operational', 'writer-read-recovery-reopen')

    def full_read(label, output):
        require(not result['jump_outcome_unknown'] and result['known_live_slot'] == A,
                'reader B is not known inactive')
        with open_logged(B, 'nor-reader', label) as transport:
            reader = MiniNorSession(transport, slot=B, known_free_slot=True)
            result[label + '_session'] = reader.upload_and_start(reader_payload, expected_sha256=reader_artifact['flat_sha256'])
            result.update(known_live_slot=B, jump_outcome_unknown=False)
            result[label + '_SPI'] = reader.initialize_spi()
            require(result[label + '_SPI']['jedec_hex'] == 'eb6014', 'physical NOR identity changed')
            def progress(done, total):
                if done % 65536 == 0:
                    result[label + '_progress'] = {'bytes': done, 'total': total}
                    save()
            raw = reader.read_flash(0, 0x100000, progress=progress)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        result[label] = {'path': output.relative_to(ROOT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)}
        save()
        return raw

    save()
    try:
        phase('confirm_retained_reader_B')
        candidates = discover_windows_rom_disks()
        require(len(candidates) == 1, 'retained ROM disk not unique')
        path = candidates[0]['path']
        with open_logged(B, 'nor-reader', 'retained-reader') as transport:
            identity = transport.exchange(b'\xfc\x70' + b'\xff' * 14, read_length=16)
            require(identity == b'\xfc\x70HYRN\x01\x03' + B.to_bytes(4, 'big') + (32768).to_bytes(4, 'big'),
                    'reader B is not the retained active plugin')
            status = transport.exchange(b'\xfc\x73' + b'\xff' * 14, read_length=16)
            require(status[:4] == b'\xfc\x73\0\1' and int.from_bytes(status[12:16], 'big') == 0x100000,
                    'retained complete buffered-read counter changed')
            result['retained_reader_identity_hex'], result['retained_reader_status_hex'] = identity.hex(), status.hex()
        result.update(known_live_slot=B, jump_outcome_unknown=False, ROM_disk=candidates[0])
        result['full_before'] = {'path': FULL_BEFORE.relative_to(ROOT).as_posix(),
                                'sha256': sha(prepared.full_preimage), 'bytes': len(prepared.full_preimage)}
        phase('operational_writer_upload')
        require(result['known_live_slot'] == B and not result['jump_outcome_unknown'], 'slot A is not known inactive')
        writer_transport = open_logged(A, 'app-writer-operational', 'writer')
        try:
            if args.recover_read_once:
                wrapper = ReadOnlyFailureRecoveryTransport(writer_transport, log=recovery_log,
                                                           reopen_factory=reopen_writer)
                active = wrapper
            else:
                active = writer_transport
            writer = MiniAppInstallerSession(active, installation, journal=journal, known_free_slot=True)
            if wrapper is not None:
                wrapper.bind_session(writer)
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
        finally:
            if wrapper is not None:
                wrapper.close()
            else:
                writer_transport.close()
        phase('independent_complete_NOR_readback')
        observed = full_read('full_after', FULL_AFTER)
        result['independent_full_validation'] = validate_completed_full(prepared, observed)
        result.update(full_NOR_verified=True, preserved_regions_unchanged=True, mutation_completion_unknown=False)
        phase('installed_verified_waiting_for_footswitch')
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error),
                      error_details=getattr(error, 'details', {}))
    finally:
        if wrapper is not None:
            # Idempotent and necessary if the wrapper replaced its inner handle.
            wrapper.close()
            result['read_recovery_final'] = {'recovery_attempts': wrapper.recovery_attempts,
                'read_reissues': wrapper.read_reissues, 'failed': wrapper.failed, 'closed': wrapper.closed}
        else:
            result['read_recovery_final'] = {'recovery_attempts': 0, 'read_reissues': 0, 'enabled': False}
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
          'full_NOR_verified', 'known_live_slot', 'jump_outcome_unknown', 'read_recovery_final')}))


if __name__ == '__main__': main()
