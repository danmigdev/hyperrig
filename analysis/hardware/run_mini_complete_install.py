"""Eighth installation: resume with exact-state reconciliation of unexecuted commands.

The full NOR read after the seventh interruption is the current preimage.
An explicit --recover-audited-commands enables bounded, exact-state recovery.
An erase/program request is reissued only if its prior audit is unchanged.
Executed commands, OUT, ARM, jump and reset commands are not repeated.
FINISH is reissued only after an unchanged prior audit proves non-execution.
MCN is restored on exit.
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
import site

# The persistent administrator runs Python -I. Reuse the existing rtMidi
# dependency imported by historical prepare(), without executing .pth files.
sys.path.append(site.getusersitepackages())

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis/hardware'), str(ROOT / 'tools'), str(ROOT)]
from tools.build_mini_boot import verify_recorded_hashes
from tools.probe_mini_recovery import discover_windows_rom_disks, MiniNorSession
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.mini_windows_quiet import RomDiskAttestation, QuietBufferedRomTransport
from tools.install_mini_app import MiniAppInstallerSession
from tools.recover_mini_read_v5 import FinishCommandRecoveryTransport
from tools.mini_windows_mcn import MiniMediaChangePause
from tools.mini_host_journal import atomic_write_json
from tools.mini_nor_read_recovery import NorReadRecoveryTransport
from run_mini_receive_stress import attach_native_diagnostic
from tools.resume_mini_install import prepare_resume, validate_completed_full
from run_mini_first_install import prepare as original_prepare

A, B = 0x1C20000, 0x1C28000
PREFIX = 'analysis/hardware/mini-complete-install'
OUT, TRACE, JOURNAL, RECOVERY = (ROOT / (PREFIX + suffix) for suffix in
    ('-run.json', '-trace.jsonl', '-journal.jsonl', '-read-recovery.jsonl'))
PINS = ROOT / (PREFIX + '-pins.json')
TRIAL = ROOT / 'analysis/hardware/mini-partial-inspect7-run.json'
MCN_PROBE = ROOT / 'analysis/hardware/mini-mcn-probe-run.json'
MCN_LOG = ROOT / (PREFIX + '-mcn.jsonl')
NOR_RECOVERY_LOG = ROOT / (PREFIX + '-nor-read-recovery.jsonl')
FULL_BEFORE = ROOT / 'artifacts/my-mini-flash/first-install/full-partial7.bin'
FULL_AFTER = ROOT / 'artifacts/my-mini-flash/first-install/full-complete-after.bin'
PLAN = ROOT / 'build/mini-install-complete/resume-plan.json'
EXPECTED_PREIMAGE_SHA = '56187d88750d5b9fb5de5fa34be52769b9612d5063f81ed1933964be81c959e5'
EXPECTED_RETAINED_READER_BYTES = 1048576  # Actual completed read7 FC73.
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
    require(trial['phase'] == 'partial_image_verified' and not trial.get('error')
            and trial['known_live_slot'] == B and trial['jump_outcome_unknown'] is False and trial['mutation_completion_unknown'] is False
            and trial['matches_expected_partial'] is True
            and trial['firmware_write_this_step'] is False and trial['reset_performed'] is False
            and trial['progress'] == {'bytes': 0x100000, 'total': 0x100000}
            and trial['final_reader_counter'] == EXPECTED_RETAINED_READER_BYTES
            and trial['dump_sha256'] == EXPECTED_PREIMAGE_SHA,
            'seventh-install fresh inspection/readback did not pass')
    mcn_probe = json.loads(MCN_PROBE.read_text(encoding='utf-8'))
    verify_recorded_hashes(mcn_probe['source_sha256'])
    require(mcn_probe['phase'] == 'MCN_pause_control_completed' and not mcn_probe.get('error')
            and mcn_probe['MCN_explicitly_reenabled'] is True
            and mcn_probe['reader_status_unchanged'] is True
            and mcn_probe['identity_queries'] >= 200,
            'temporary per-device MCN control has not been physically observed')
    prepared = prepare_resume(FULL_BEFORE, expected_partial_sha256=EXPECTED_PREIMAGE_SHA,
                              expected_modified_sectors=tuple(range(0x5000, 0x5f000, 4096)), slot=A)
    require(PLAN.read_bytes() == prepared.plan_bytes, 'retained complete-install plan differs')
    require(prepared.installation.candidate == original.candidate,
            'eighth installation must retain the exact reviewed candidate')
    require(prepared.stock_backup == backup, 'stock backup provenance differs')
    return pins, prepared, reader_artifact, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--recover-audited-commands', action='store_true',
        help='enable up to eight Win31 recoveries of reads/queries and proven-unexecuted FC7B/FC7D/FC80 with exact target state')
    args = parser.parse_args()
    pins, prepared, reader_artifact, reader_payload = prepare()
    installation = prepared.installation
    recovery_policy = {'enabled': args.recover_audited_commands,
        'max_reopens': 8 if args.recover_audited_commands else 0,
        'only_commands': ['FD7F', 'FC7E', 'FD88', 'FD87', 'FC7B', 'FC7D', 'FC80'], 'only_Windows_error': 31,
        'FD7F_requires_identical_prior_validated_audit': True,
        'FD87_requires_same_staged_page_and_exact_audit_except_echoed_and_record_CRC': True,
        'FD87_reissue_requires_exact_candidate_page_bytes': True,
        'queries_require_current_expected_state_reconciliation': True,
        'one_recovery_per_command_and_expected_state': True,
        'mutation_retries_allowed': args.recover_audited_commands,
        'mutation_request_reissue_requires_exact_prior_audit': True,
        'FINISH_reissue_requires_exact_prior_audit_and_complete_candidate_sector': True,
        'executed_mutation_retries_allowed': False, 'OUT_retries_allowed': False,
        'jump_or_reset_retries_allowed': False, 'backend_fallback_allowed': False}
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'candidate': sha(installation.candidate),
            'preimage_full_NOR_sha256': EXPECTED_PREIMAGE_SHA, 'plan_sha256': installation.plan_sha256,
            'changed_sectors': len(installation.sector_order), 'backend': 'spt-buffered',
            'read_recovery_policy': recovery_policy, 'temporary_MCN_pause': True, 'automatic_reset': False}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'Windows SPT requires the elevated bounded helper')
    require(not any(p.exists() for p in (OUT, OUT.with_suffix('.json.tmp'), TRACE, JOURNAL, RECOVERY, MCN_LOG, NOR_RECOVERY_LOG, FULL_AFTER)),
            'one-shot output exists; do not rerun')
    result = {'started_utc': now(), 'phase': 'prepare', 'source_pins': pins,
              'installation': installation.summary(), 'known_live_slot': None,
              'jump_outcome_unknown': False, 'jump_attempts': 0,
              'mutation_command_submitted': False, 'mutation_completion_unknown': False,
              'installed_image_verified': False, 'full_NOR_verified': False,
              'automatic_reset': False, 'automatic_rollback': False,
              'automatic_mutation_retry': args.recover_audited_commands,
              'mutation_retry_scope': 'Only a request proven unexecuted by exact prior audit and unconsumed sequence.',
              'automatic_backend_fallback': False,
              'read_recovery_policy': recovery_policy,
              'retry_policy_scope': 'Installer core retries no commands; optional v5 wrapper recovers bounded reads/queries and reissues only proven-unexecuted erase/program/FINISH requests with unchanged audited state.',
              'power_loss_atomicity_proven': False,
              'continuation_of': 'analysis/hardware/mini-reconciled-install-run.json',
              'MCN_pause_started': False, 'MCN_pause_closed': False, 'MCN_explicitly_reenabled': False,
              'transport_trial': TRIAL.relative_to(ROOT).as_posix(),
              'transport_trial_sha256': sha(TRIAL.read_bytes()),
              'new_preimage_plan': PLAN.relative_to(ROOT).as_posix(),
              'command_spacing_seconds': PACE, 'backend': 'IOCTL_SCSI_PASS_THROUGH buffered',
              'discovery_policy': 'One initial disk discovery; attested PnP/interface checks for subsequent handles.'}
    path, writer, wrapper, writer_transport, mcn_pause, attestation = None, None, None, None, None, None

    def save():
        atomic_write_json(OUT, result)

    def phase(value):
        result['phase'] = value
        save()

    def logged(transport, label):
        require(isinstance(transport, WindowsBufferedRomTransport), 'every handle must use the qualified buffered backend')
        result.setdefault('transport_handles', []).append({'label': label, 'path': transport.disk['path'],
            'slot': transport.slot, 'profile': transport.profile, 'inquiry': transport.inquiry,
            'adapter_descriptor': transport.adapter_descriptor, 'backend': 'spt-buffered',
            'opened_interface': getattr(transport, 'opened_interface', None),
            'device_number': getattr(transport, 'device_number', None),
            'open_metadata': getattr(transport, 'open_metadata', None)})
        save()
        native = attach_native_diagnostic(transport)
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
                             native_transfer=getattr(transport, 'last_transfer', None),
                             native_failure_observation=native.last_failure)
                append(TRACE, entry, durable=True)
                raise
            entry.update(state='after', finished_utc=now(), elapsed_ms=(time.monotonic() - start) * 1000,
                         response_bytes=len(raw), response_sha256=sha(raw),
                         native_transfer=getattr(transport, 'last_transfer', None))
            if len(raw) <= 128: entry['response_hex'] = raw.hex()
            append(TRACE, entry)
            if cdb[:2] == b'\xfc\x73':
                transport.last_reader_status_raw = raw
            return raw
        transport.exchange = exchange

    def open_logged(slot, profile, label):
        nonlocal attestation
        transport = QuietBufferedRomTransport(attestation, slot=slot, profile=profile)
        attestation = transport.attestation
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
        # Every recovery decision and witness is durable before any allowed query/read recovery.
        append(RECOVERY, item, durable=True)

    def mcn_log(item):
        append(MCN_LOG, item, durable=True)
        if item['event'] == 'mcn_disabled': result['MCN_pause_started'] = True
        if item['event'] == 'mcn_reenabled': result['MCN_explicitly_reenabled'] = True
        save()

    def reopen_writer():
        require(result['known_live_slot'] == A and not result['jump_outcome_unknown'],
                'read recovery cannot reopen after a changed/unknown callback lifecycle')
        return open_logged(A, 'app-writer-operational', 'writer-read-recovery-reopen')

    def reopen_reader():
        require(result['known_live_slot'] == B and not result['jump_outcome_unknown'],
                'NOR read recovery requires the retained reader B')
        return open_logged(B, 'nor-reader', 'full-read-recovery-reopen')

    def nor_recovery_log(item):
        append(NOR_RECOVERY_LOG, item, durable=True)

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
            nor_wrapper = None
            try:
                if args.recover_audited_commands:
                    nor_wrapper = NorReadRecoveryTransport(transport, log=nor_recovery_log,
                        reopen_factory=reopen_reader, max_recoveries=8)
                    nor_wrapper.bind_session(reader, status_raw=transport.last_reader_status_raw)
                raw = reader.read_flash(0, 0x100000, progress=progress)
                result[label + '_target_read_counter'] = reader.successful_bytes
            finally:
                if nor_wrapper is not None:
                    nor_wrapper.close()
                    result[label + '_read_recovery'] = nor_wrapper.summary()
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
        attestation = RomDiskAttestation.from_discovery(candidates[0])
        with open_logged(B, 'nor-reader', 'retained-reader') as transport:
            identity = transport.exchange(b'\xfc\x70' + b'\xff' * 14, read_length=16)
            require(identity == b'\xfc\x70HYRN\x01\x03' + B.to_bytes(4, 'big') + (32768).to_bytes(4, 'big'),
                    'reader B is not the retained active plugin')
            status = transport.exchange(b'\xfc\x73' + b'\xff' * 14, read_length=16)
            require(status[:4] == b'\xfc\x73\0\1' and int.from_bytes(status[12:16], 'big') == EXPECTED_RETAINED_READER_BYTES,
                    'retained complete buffered-read counter changed')
            result['retained_reader_identity_hex'], result['retained_reader_status_hex'] = identity.hex(), status.hex()
            mcn_pause = MiniMediaChangePause(transport, log=mcn_log)
        result.update(known_live_slot=B, jump_outcome_unknown=False, ROM_disk=candidates[0])
        result['full_before'] = {'path': FULL_BEFORE.relative_to(ROOT).as_posix(),
                                'sha256': sha(prepared.full_preimage), 'bytes': len(prepared.full_preimage)}
        phase('operational_writer_upload')
        require(result['known_live_slot'] == B and not result['jump_outcome_unknown'], 'slot A is not known inactive')
        writer_transport = open_logged(A, 'app-writer-operational', 'writer')
        try:
            if args.recover_audited_commands:
                wrapper = FinishCommandRecoveryTransport(writer_transport, log=recovery_log,
                                                         reopen_factory=reopen_writer, max_recoveries=8)
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
        try:
            if wrapper is not None:
                # Idempotent and necessary if the wrapper replaced its inner handle.
                wrapper.close()
                result['read_recovery_final'] = wrapper.summary()
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
        except Exception as writer_cleanup_error:
            result['writer_cleanup_error'] = repr(writer_cleanup_error)
            result.setdefault('error', 'Writer cleanup/diagnostics failed: ' + str(writer_cleanup_error))
        if mcn_pause is not None:
            try:
                mcn_pause.close()
                result['MCN_pause_closed'] = mcn_pause.closed
                require(not mcn_pause.disabled and result['MCN_explicitly_reenabled'], 'MCN cleanup not confirmed')
            except Exception as cleanup_error:
                result['MCN_cleanup_error'] = repr(cleanup_error)
                result.setdefault('error', 'MCN cleanup failed: ' + str(cleanup_error))
        result['finished_utc'] = now()
        save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'installed_image_verified',
          'full_NOR_verified', 'known_live_slot', 'jump_outcome_unknown', 'read_recovery_final')}))


if __name__ == '__main__': main()
