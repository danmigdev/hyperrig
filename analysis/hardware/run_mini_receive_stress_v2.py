"""New HYRX trial after a local journal failure; default/import are offline.

Use the frozen RAM-only plugin for 256 OUT260 observations. Each needs two
stable records. Only complete success permits reloading reader B and comparing
the full NOR with inspect3. Any error stops; no retry, reset or fallback.
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
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT)]
from tools.build_mini_boot import verify_recorded_hashes
from tools.mini_host_journal import atomic_write_json
from tools.build_mini_rom_receive import inspect_elf, poison, validate_record
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.probe_mini_receive import MiniReceiveSession
from tools.probe_mini_recovery import discover_windows_rom_disks, MiniNorSession

A, B, COUNT, LENGTH, PACE = 0x1C20000, 0x1C28000, 256, 260, 0.005
EXPECTED_SHA = '74095e9ae0f69878dd5d708150b419548e28db0cf1dabc0e3076c27cd8873406'
CALLBACKS = {'send': 0x01E008E4, 'receive': 0x01E0089A, 'handler_slot': 0x01C01264}
PREFIX = 'analysis/hardware/mini-receive-stress-v2'
OUT, TRACE, RECORDS, OBSERVATIONS, PINS = (ROOT / (PREFIX + suffix) for suffix in
    ('-run.json', '-trace.jsonl', '-records.bin', '-observations.jsonl', '-pins.json'))
PRIOR = ROOT / 'analysis/hardware/mini-partial-inspect3-run.json'
BEFORE = ROOT / 'artifacts/my-mini-flash/first-install/full-partial3.bin'
AFTER = ROOT / 'artifacts/my-mini-flash/first-install/full-after-receive-stress-v2.bin'
PRIOR_FAILURE = ROOT / 'analysis/hardware/mini-receive-stress-run.json.tmp'
PRIOR_ARMED_RECORD = ROOT / (PREFIX + '-prior-armed-record.bin')
LEGACY_DISPATCHER_SHA = '1d512173776f5f87424e7870731df2871cdf1f9293636765a6371c7bb44191e8'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def load(path): return json.loads(Path(path).read_bytes())


def observation_vector(sequence):
    require(type(sequence) is int and 1 <= sequence <= COUNT, 'bounded observation sequence required')
    seed = (0x55 + (sequence - 1) * 17) & 255
    nonce = 0x48590000 | sequence
    payload = bytes(value ^ 255 for value in poison(LENGTH, seed))
    return payload, nonce, seed


def run_observations(session, *, before, after, retain_records):
    """Pure orchestration against an explicitly supplied, identified session.

    Logging/retention callbacks are mandatory. A failure in them also stops the
    loop. No hardware class is constructed and no post-error action exists here.
    """
    require(session.ready and not session.failed and session.sequence == 0
            and session.expected_raw_return == LENGTH, 'fresh HYRX session with observed return260 required')
    for sequence in range(1, COUNT + 1):
        payload, nonce, seed = observation_vector(sequence)
        before({'sequence': sequence, 'nonce': nonce, 'seed': seed, 'bytes': LENGTH,
                'payload_sha256': sha(payload)})
        try:
            result = session.receive_once(payload, nonce=nonce, seed=seed)
        finally:
            # Preserve one returned record even if the second sample fails.
            retain_records(sequence, tuple(session.last_records))
        require(not session.failed and not session.ambiguous_receive and not result['session_failed']
                and result['observed_complete_and_stable'] and result['records_stable']
                and result['raw_return'] == LENGTH and result['sequence'] == sequence
                and result['canary_mask'] == 3 and result['sample_count'] == 2
                and result['rom_pointer_observations'] == CALLBACKS
                and len(session.last_records) == 2,
                'HYRX repeated receive/guards/pointers/stability failed; no next command')
        after(sequence, {k: v for k, v in result.items() if k != 'record_hex'})
    return {'observations': COUNT, 'OUT260_commands': COUNT, 'stable_records': COUNT * 2,
            'all_observations_passed': True, 'automatic_retry': False,
            'general_receive_semantics_proven': False}


class DiagnosticKernelProxy:
    """Observe optional thread NTSTATUS while preserving ctypes' Win32 error.

    RtlGetLastNtStatus is an optional diagnostic export, not an IO_STATUS_BLOCK
    or authoritative root-cause result. It never changes retries or acceptance.
    The real buffered transport remains frozen and captures GetLastError itself.
    """
    def __init__(self, kernel, *, get_error, set_error, ntstatus=None):
        self.kernel, self.get_error, self.set_error = kernel, get_error, set_error
        self.ntstatus, self.last_failure = ntstatus, None

    def __getattr__(self, name): return getattr(self.kernel, name)

    def DeviceIoControl(self, *args):
        self.last_failure = None
        ok = self.kernel.DeviceIoControl(*args)
        if not ok:
            win32 = self.get_error()
            status, error = None, None
            try:
                if self.ntstatus is not None:
                    status = int(self.ntstatus()) & 0xFFFFFFFF
            except Exception as cause:
                error = repr(cause)
            finally:
                self.set_error(win32)
            self.last_failure = {'win32_error': win32,
                'ntstatus_hex': None if status is None else f'{status:08x}',
                'ntstatus_export_available': self.ntstatus is not None,
                'diagnostic_error': error, 'ntstatus_is_diagnostic_only': True}
        return ok


def attach_native_diagnostic(transport):
    # Explicit execution path only, after identified-handle construction.
    status = None
    try:
        library = ctypes.WinDLL('ntdll', use_last_error=False)
        status = library.RtlGetLastNtStatus
        status.argtypes, status.restype = [], ctypes.c_int32
    except (AttributeError, OSError):
        pass
    proxy = DiagnosticKernelProxy(transport._kernel, get_error=ctypes.get_last_error,
                                 set_error=ctypes.set_last_error, ntstatus=status)
    transport._kernel = proxy
    return proxy


def prepare():
    pins = load(PINS)
    verify_recorded_hashes(pins)
    failure = load(PRIOR_FAILURE)
    require(failure['error_type'] == 'PermissionError' and failure.get('finished_utc')
            and failure['completed_observations'] == 31 and failure['raw_records_retained'] == 62
            and failure['known_live_slot'] == A and not failure['jump_outcome_unknown']
            and failure['pending_observation']['sequence'] == 32
            and failure['receive_final'] == {'failed': True, 'sequence': 32,
                                            'ambiguous_receive': True, 'out_submitted': True},
            'expected the preserved local-journal failure after ARM32')
    prior_trace = [json.loads(line) for line in
        (ROOT / 'analysis/hardware/mini-receive-stress-trace.jsonl').read_text().splitlines()]
    require(len(prior_trace) == 278 and all(row['state'] == ('before' if index % 2 == 0 else 'after')
            for index, row in enumerate(prior_trace))
            and sum(row['state'] == 'before' and row['cdb'].startswith('fb84') for row in prior_trace) == 31
            and prior_trace[-1]['cdb'] == 'fc83002001044859002035fb92d864ff'
            and prior_trace[-1]['response_hex'] == 'fc834859525800200000000001040101',
            'prior trace must end after ARM32 and before any OUT32 exchange')
    prior = load(PRIOR)
    require(prior['phase'] == 'partial_image_verified' and not prior.get('error')
            and prior['known_live_slot'] == B and not prior['jump_outcome_unknown']
            and prior['matches_expected_partial'] is True and prior['dump_sha256'] == EXPECTED_SHA
            and prior['changed_sectors'] == [0x5000, 0x6000]
            and prior['progress'] == {'bytes': 0x100000, 'total': 0x100000},
            'inspect3 must establish retained HYRN B and a complete partial image')
    full = BEFORE.read_bytes()
    require(len(full) == 0x100000 and sha(full) == EXPECTED_SHA, 'retained full-partial3 bytes changed')
    manifest = load(ROOT / 'research/mini-rom-receive.json')
    sources = dict(manifest['source_sha256'])
    require(sources.pop('tools/probe_mini_recovery.py') == LEGACY_DISPATCHER_SHA,
            'unexpected historical HYRX host-dispatcher dependency')
    # The frozen target, builder, client and tests must match. The one historic
    # host dispatcher was superseded before this trial; the CURRENT dispatcher
    # and separate buffered backend are explicitly bound by this runner's pins.
    verify_recorded_hashes(sources)
    require('tools/probe_mini_recovery.py' in pins and 'tools/mini_windows_spt.py' in pins,
            'current separate host transport must be pinned')
    artifact = next(a for a in manifest['artifacts'] if a['base'] == A)
    payload, elf = (ROOT / artifact['file']).read_bytes(), (ROOT / artifact['elf']).read_bytes()
    inspected, _, metadata = inspect_elf(elf, A)
    require(inspected == payload and all(artifact[k] == v for k, v in metadata.items())
            and sha(payload) == artifact['payload_sha256'] and sha(elf) == artifact['elf_sha256'],
            'frozen HYRX ELF/payload differs')
    original = load(ROOT / 'analysis/hardware/mini-receive-run.json')
    require(original['observation_passed'] is True and original['receive_observation']['raw_return'] == LENGTH,
            'prior physical return260 observation missing')
    initial_payload = bytes(value ^ 255 for value in poison(LENGTH, 0x55))
    for number in (1, 2):
        record = (ROOT / f'analysis/hardware/mini-receive-record-{number}.bin').read_bytes()
        item = validate_record(record, base=A, build_tag=manifest['build_tag'], sequence=1,
                               nonce=0x1234ABCD, payload=initial_payload, seed=0x55)
        require(item['raw_return'] == LENGTH and item['observed_complete_and_stable']
                and item['sample_count'] == number and item['rom_pointer_observations'] == CALLBACKS,
                'physical receive evidence differs')
    reader_manifest = load(ROOT / 'research/mini-flash-reader.json')
    verify_recorded_hashes(reader_manifest['sources_sha256'])
    reader = next(a for a in reader_manifest['artifacts'] if a['audit']['slot'] == B)
    reader_payload = (ROOT / reader['flat']).read_bytes()
    require(sha(reader_payload) == reader['flat_sha256']
            and sha((ROOT / reader['elf']).read_bytes()) == reader['elf_sha256'], 'reader B artifact changed')
    return pins, full, manifest, artifact, payload, reader, reader_payload



def validate_prior_armed_record(raw, *, build_tag):
    # Sequence32 was armed by the failed runner, but its OUT was never submitted.
    payload, nonce, seed = observation_vector(32)
    item = validate_record(raw, base=A, build_tag=build_tag, sequence=32,
                           nonce=nonce, payload=payload, seed=seed)
    words = struct.unpack_from('<27I', raw)
    require(item['state'] == 1 and item['error'] == 0 and item['sample_count'] == 1
            and item['raw_return'] == -2147483648 and not item['callback_entered']
            and not item['callback_returned'] and item['canary_mask'] == 3
            and item['changed_bytes'] == 0 and item['rom_pointer_observations'] == CALLBACKS
            and words[16] == 3 and words[18] == words[21] == 1
            and words[19] == words[22] == 0
            and raw[128:388] == poison(LENGTH, seed)
            and words[11] == zlib.crc32(poison(LENGTH, seed)),
            'prior HYRX state is not untouched ARMED32; no reader upload permitted')
    return item


def retire_prior_probe(open_transport, *, build_tag, reader_payload, reader_sha256,
                       record_sink, known_slot):
    # No OUT32 or ARM33 is issued. Only a confirmed inactive B can be replaced.
    with open_transport(A, 'ram-receive', 'prior-receive') as transport:
        identity = transport.exchange(b'\xfc\x82' + b'\xff' * 14, read_length=16)
        require(identity == b'\xfc\x82HYRX\1\0' + struct.pack('>II', A, 32768),
                'retained HYRX A identity differs')
        raw = transport.exchange(b'\xfd\x85' + b'\xff' * 14, read_length=512)
        record_sink(raw)
        record = validate_prior_armed_record(raw, build_tag=build_tag)
    known_slot(A)
    with open_transport(B, 'nor-reader', 'retire-prior-probe') as transport:
        reader = MiniNorSession(transport, slot=B, known_free_slot=True)
        identified = reader.upload_and_start(reader_payload, expected_sha256=reader_sha256)
    known_slot(B)
    return {'prior_record': record, 'reader_identity': identified,
            'prior_OUT_reissued': False, 'SPI_initialized': False, 'NOR_read': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check-only', action='store_true')
    action.add_argument('--execute', action='store_true', help='explicitly run the already reviewed RAM-only trial')
    args = parser.parse_args()
    pins, expected, manifest, artifact, payload, reader_artifact, reader_payload = prepare()
    if not args.execute:
        print(json.dumps({'preflight': 'pass', 'device_io': False, 'OUT260_observations': COUNT,
            'records_per_observation': 2, 'source_NOR_sha256': EXPECTED_SHA,
            'target_SPI_during_HYRX': False, 'NVM_writes': False, 'reset': False, 'automatic_retry': False,
            'polling_policy_changed': False, 'historical_dispatcher_sha256': LEGACY_DISPATCHER_SHA}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'Windows SPT helper requires elevation')
    require(not any(p.exists() for p in (OUT, OUT.with_suffix('.json.tmp'), TRACE, RECORDS, OBSERVATIONS, AFTER, PRIOR_ARMED_RECORD)), 'one-shot trial already attempted')
    result = {'phase': 'prepare', 'started_utc': now(), 'source_pins': pins, 'known_live_slot': None,
        'jump_outcome_unknown': False, 'receive_outcome_unknown': False, 'completed_observations': 0,
        'jump_attempts': 0, 'out_commands_submitted': 0, 'raw_records_retained': 0,
        'NVM_writes': False, 'reset_performed': False, 'automatic_retry': False,
        'post_error_fallback': False, 'polling_policy_changed': False, 'command_spacing_seconds': PACE,
        'backend': 'IOCTL_SCSI_PASS_THROUGH buffered', 'source_NOR_sha256': EXPECTED_SHA,
        'scope': 'Verify prior ARMED32 without receive; retire through reader B; fresh RAM trial256; success-only full NOR read',
        'local_json_replace_retry': {'attempts': 20, 'delay_seconds': .025, 'device_retry': False},
        'historical_dispatcher_sha256': LEGACY_DISPATCHER_SHA}
    session, path = None, None

    def save():
        atomic_write_json(OUT, result)

    def append(path, event):
        with path.open('a', encoding='utf8', newline='\n') as stream:
            stream.write(json.dumps(event) + '\n');stream.flush();os.fsync(stream.fileno())

    def phase(value): result.update(phase=value);save()

    def open_logged(slot, profile, label):
        transport = WindowsBufferedRomTransport(path, slot=slot, profile=profile)
        try:
            native = attach_native_diagnostic(transport)
            result.setdefault('transport_handles', []).append({'label': label, 'slot': slot, 'profile': profile,
                'inquiry': transport.inquiry, 'adapter_descriptor': transport.adapter_descriptor,
                'ntstatus_export_available': native.ntstatus is not None})
            save()
            original_exchange = transport.exchange
            def exchange(cdb, data_out=None, read_length=0):
                time.sleep(PACE)
                require(cdb[:2] not in (b'\xfc\x7b', b'\xfc\x7d', b'\xfc\x80'), 'no NOR mutation allowed')
                if cdb[:2] == b'\xfb\x08':
                    require(result['known_live_slot'] in (A, B) and result['known_live_slot'] != slot
                            and not result['jump_outcome_unknown'], 'jump needs a known inactive slot')
                    result.update(known_live_slot=None, jump_outcome_unknown=True,
                                  jump_attempts=result['jump_attempts'] + 1);save()
                if cdb[:2] == b'\xfb\x84':
                    result.update(receive_outcome_unknown=True,
                                  out_commands_submitted=result['out_commands_submitted'] + 1);save()
                entry = {'stage': label, 'state': 'before', 'utc': now(), 'cdb': cdb.hex(),
                    'out_bytes': len(data_out) if data_out is not None else 0, 'in_bytes': read_length,
                    'out_sha256': sha(data_out) if data_out is not None else None}
                append(TRACE, entry)
                try:
                    raw = original_exchange(cdb, data_out=data_out, read_length=read_length)
                except Exception as error:
                    entry.update(state='error', finished_utc=now(), error=repr(error),
                        details=getattr(error, 'details', {}), native_transfer=transport.last_transfer,
                        native_failure_observation=native.last_failure)
                    append(TRACE, entry);raise
                entry.update(state='after', finished_utc=now(), response_bytes=len(raw),
                    response_sha256=sha(raw), native_transfer=transport.last_transfer)
                if len(raw) <= 512: entry['response_hex'] = raw.hex()
                append(TRACE, entry)
                return raw
            transport.exchange = exchange
            return transport
        except BaseException:
            transport.close();raise

    def before(item):
        result['pending_observation'] = item;save()
        append(OBSERVATIONS, {'state': 'before', 'utc': now(), **item})

    def retain(sequence, records):
        if records:
            require(all(len(raw) == 512 for raw in records), 'invalid record extent')
            with RECORDS.open('ab') as stream:
                for raw in records: stream.write(raw)
                stream.flush();os.fsync(stream.fileno())
            result['raw_records_retained'] += len(records)
            append(OBSERVATIONS, {'state': 'records_retained', 'sequence': sequence,
                                  'record_sha256': [sha(raw) for raw in records]})
            save()

    def after(sequence, observed):
        result.update(completed_observations=sequence, receive_outcome_unknown=False,
                      last_observation=observed, pending_observation=None)
        append(OBSERVATIONS, {**observed, 'event': 'after', 'utc': now()});save()

    save()
    try:
        phase('confirm_prior_HYRX_A_ARMED32')
        disks = discover_windows_rom_disks();require(len(disks) == 1, 'one retained ROM disk required')
        path = disks[0]['path']
        def keep_prior_record(raw):
            with PRIOR_ARMED_RECORD.open('xb') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
        def known_slot(slot):
            result.update(known_live_slot=slot, jump_outcome_unknown=False);save()
        result['prior_probe_retirement'] = retire_prior_probe(open_logged,
            build_tag=manifest['build_tag'], reader_payload=reader_payload,
            reader_sha256=reader_artifact['flat_sha256'], record_sink=keep_prior_record,
            known_slot=known_slot)
        phase('HYRX_upload_verify_start_A')
        with open_logged(A, 'ram-receive', 'receive') as transport:
            session = MiniReceiveSession(transport, slot=A, build_tag=manifest['build_tag'],
                                         expected_raw_return=LENGTH, known_free_slot=True)
            result['receive_session'] = session.upload_and_start(payload, expected_sha256=artifact['payload_sha256'])
            result.update(known_live_slot=A, jump_outcome_unknown=False);phase('receive_256_OUT260')
            result['receive_trial'] = run_observations(session, before=before, after=after, retain_records=retain)
        require(result['completed_observations'] == COUNT and result['raw_records_retained'] == COUNT * 2
                and not result['receive_outcome_unknown'] and not result['jump_outcome_unknown'],
                'incomplete receive trial; reader reload forbidden')
        phase('success_only_reload_reader_B')
        with open_logged(B, 'nor-reader', 'final-reader') as transport:
            reader = MiniNorSession(transport, slot=B, known_free_slot=True)
            result['reader_session'] = reader.upload_and_start(reader_payload, expected_sha256=reader_artifact['flat_sha256'])
            result.update(known_live_slot=B, jump_outcome_unknown=False)
            result['reader_SPI'] = reader.initialize_spi()
            require(result['reader_SPI']['jedec_hex'] == 'eb6014', 'NOR identity changed')
            phase('independent_full_NOR_read')
            def progress(done, total):
                if done % 65536 == 0: result['full_read_progress'] = {'bytes': done, 'total': total};save()
            full = reader.read_flash(0, 0x100000, progress=progress)
        with AFTER.open('xb') as stream:
            stream.write(full);stream.flush();os.fsync(stream.fileno())
        require(full == expected, 'NOR changed during RAM-only receive trial')
        result.update(full_NOR_unchanged=True, full_NOR_sha256=sha(full),
                      phase='receive_stress_complete_NOR_unchanged', trial_passed=True)
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error),
                      error_details=getattr(error, 'details', {}), trial_passed=False)
    finally:
        if session is not None:
            result['receive_final'] = {'failed': session.failed, 'sequence': session.sequence,
                'ambiguous_receive': session.ambiguous_receive, 'out_submitted': session.out_submitted}
            if session.ambiguous_receive: result['receive_outcome_unknown'] = True
        result['finished_utc'] = now();save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'completed_observations',
        'raw_records_retained', 'trial_passed', 'known_live_slot', 'jump_outcome_unknown', 'receive_outcome_unknown')}))


if __name__ == '__main__': main()
