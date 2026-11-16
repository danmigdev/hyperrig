"""Offline v3 normal boot: current-data preservation, one reset, no serial I/O."""
from contextlib import ExitStack, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.probe_mini_recovery import RomCommandError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('normal_boot_v11_test', ROOT/'analysis/hardware/run_mini_first_boot_v11.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
PORT = {'device': 'COM123', 'vid': 0x3654, 'pid': 0x5155, 'description': 'OFFLINE FIXTURE'}
PARENT = r'USB\VID_4C4A&PID_8057\OFFLINE'


class NormalBootV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = (ROOT/'build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin').read_bytes()
        cls.new = runner.CANDIDATE.read_bytes()

    def run_fake(self, fault=None, *, check_only=False, bootmode='released'):
        handles, calls, resets, serial = [], [], [], []
        arrival_count = enum_count = 0

        class Transport:
            def __init__(self, path, *, slot, profile='ram-probe'):
                self.slot, self.profile, self.closed = slot, profile, False
                self.disk = {'path': path}; self.inquiry = {'vendor': 'WL82', 'product': 'UBOOT1.00'}
                self.adapter_descriptor = {'alignment_mask': 0}; handles.append(self)
            def exchange(self, cdb, data_out=None, read_length=0):
                assert not self.closed
                op = int.from_bytes(cdb[:2], 'big'); calls.append((self.slot, op))
                if self.slot == runner.B:
                    assert data_out is None and read_length == 16
                    if op == 0xFC70:
                        if fault == 'identity': return bytes(16)
                        return b'\xfc\x70HYRN\1\3'+struct.pack('>II', runner.B, 32768)
                    assert op == 0xFC73
                    count = 0x100200 if fault in ('counter', 'valid_lost_read') else 0x100000
                    return b'\xfc\x73\0\1'+bytes(8)+count.to_bytes(4, 'big')
                assert self.slot == runner.A and op == 0xFB08
                if fault in ('reset_presubmit', 'reset_postsubmit'):
                    raise RomCommandError(31, 'offline transfer failure', submitted=fault=='reset_postsubmit')
                return b'\xfb\x08'+bytes(14)
            def close(self): self.closed = True
            def __enter__(self): return self
            def __exit__(self, *_): self.close()

        class ResetSession:
            def __init__(self, transport, *, slot, known_free_slot):
                assert slot == runner.A and known_free_slot
                assert calls[:2] == [(runner.B, 0xFC70), (runner.B, 0xFC73)]
                self.transport = transport
            def upload_only(self, payload, *, expected_sha256):
                resets.append('upload')
                assert payload == b'fake-reset' and runner.sha(payload) == expected_sha256
                if fault == 'upload': raise ValueError('offline upload failure')
                return {'uploaded': True, 'offline_mock': True}
            def start_reset_once(self, payload, *, elf, manifest):
                resets.append('verify_and_jump')
                assert elf == b'fake-elf' and manifest['slot'] == runner.A
                if fault == 'reset_readback': raise ValueError('offline reset readback failure')
                try: self.transport.exchange(b'\xfb\x08'+bytes(14), read_length=16)
                except RomCommandError as error:
                    if not error.submitted: raise
                    return {'jump_sent': True, 'jump_outcome': 'post_submit_transport_error', 'automatic_retry': False}
                return {'jump_sent': True, 'jump_outcome': 'fb08_echo_received', 'automatic_retry': False}

        def arrivals():
            nonlocal arrival_count
            arrival_count += 1
            stamp = '2026-11-16T00:00:02Z' if fault=='arrival_changed' and arrival_count>1 else '2026-11-16T00:00:01Z'
            return [{'instance_id': PARENT if fault!='parent' else PARENT+'DIFFERENT', 'arrival_utc': stamp}]

        def enumerate_ports():
            nonlocal enum_count
            enum_count += 1
            if not any(op==0xFB08 for _, op in calls): return [PORT] if fault=='existing_CDC' else []
            if fault=='missing_CDC': return []
            if fault=='multiple_CDC': return [PORT, {**PORT, 'device': 'COM124'}]
            if fault=='wrong_COM': return [{**PORT, 'device': 'not-a-COM'}]
            return [PORT]

        def no_serial(*args, **kwargs):
            serial.append((args, kwargs))
            raise AssertionError('normal boot must never open a serial port or PING')

        with tempfile.TemporaryDirectory(prefix='TEST-normal-boot-v11-', dir=ROOT/'build') as name:
            folder = Path(name); hardware = folder/'analysis/hardware'; hardware.mkdir(parents=True)
            research = folder/'research'; research.mkdir()
            output = hardware/'mini-first-boot-v11-released-run.json'
            trace = hardware/'mini-first-boot-v11-released-trace.jsonl'
            paths = {key: folder/path.relative_to(ROOT) for key, path in (
                ('INSTALL_RUN', runner.INSTALL_RUN), ('INDEPENDENT', runner.INDEPENDENT),
                ('PLAN', runner.PLAN), ('FULL_BEFORE', runner.FULL_BEFORE), ('FULL_AFTER', runner.FULL_AFTER),
                ('CANDIDATE', runner.CANDIDATE), ('MCN_LOG', runner.MCN_LOG), ('BASE_PROFILE', runner.BASE_PROFILE),
                ('PINS', runner.PINS))}
            for path in paths.values(): path.parent.mkdir(parents=True, exist_ok=True)
            def put(key, value):
                raw = value if isinstance(value, bytes) else (json.dumps(value)+'\n').encode()
                paths[key].write_bytes(raw)
                return {'path': paths[key].relative_to(folder).as_posix(), 'sha256': runner.sha(raw)}
            before = bytearray(b'\xC7'*0x100000)
            before[0x4000:0x82000] = self.old
            for address in (0x82020, 0xBE020, 0xBF020): before[address:address+8] = b'RUNTIME!'
            after = bytearray(before); after[0x4000:0x82000] = self.new
            if fault=='preimage': before[0x4820] ^= 1
            if fault=='outside_changed': after[0xBE020] ^= 1
            before_ref, after_ref = put('FULL_BEFORE', bytes(before)), put('FULL_AFTER', bytes(after))
            candidate_ref = put('CANDIDATE', self.new)
            plan = {'kind': 'mini-v2-v3-pc-limit-upgrade', 'target_app_sha256': runner.EXPECTED_CANDIDATE_SHA,
                'preimage_app_sha256': runner.EXPECTED_PREVIOUS_SHA, 'sector_order': [0x4000],
                'expected_full_readback_sha256': after_ref['sha256'], 'fresh_full_read': before_ref, 'candidate': candidate_ref}
            if fault=='plan': plan['sector_order'] = [0x5000]
            plan_ref = put('PLAN', plan)
            install = {'phase': 'upgraded_verified_waiting_for_normal_boot', 'full_NOR_verified': True,
                'installed_image_verified': True, 'known_live_slot': runner.B, 'jump_outcome_unknown': False,
                'mutation_completion_unknown': False, 'backend': 'IOCTL_SCSI_PASS_THROUGH buffered',
                'installation': {'candidate_sha256': runner.EXPECTED_CANDIDATE_SHA},
                'independent_full_validation': {'application_verified': True, 'external_regions_unchanged_from_fresh_read': True,
                    'external_regions_restored_to_stock': False, 'full_NOR_sha256': after_ref['sha256']},
                'full_before': before_ref, 'full_after': after_ref, 'full_after_target_read_counter': 0x100000,
                'full_after_lost_read_bytes': 0, 'full_after_read_recovery': {'lost_read_bytes': 0},
                'MCN_pause_started': True, 'MCN_pause_closed': True, 'MCN_explicitly_reenabled': True,
                'started_utc': '2026-11-16T00:00:00Z', 'finished_utc': '2026-11-16T00:00:01Z',
                'ROM_disk': {'path': 'OFFLINE-DISK'}}
            if fault=='incomplete_install': install['full_NOR_verified'] = False
            if fault=='MCN': install['MCN_explicitly_reenabled'] = False
            if fault=='recorded_counter': install['full_after_target_read_counter'] += 512
            if fault=='valid_lost_read':
                install.update(full_after_target_read_counter=0x100200, full_after_lost_read_bytes=512,
                               full_after_read_recovery={'lost_read_bytes': 512})
            if fault=='missing_lost_audit': install.pop('full_after_read_recovery')
            if fault=='contradictory_lost_audit': install['full_after_read_recovery']['lost_read_bytes'] = 512
            if fault=='restored_stock': install['independent_full_validation']['external_regions_restored_to_stock'] = True
            install_ref = put('INSTALL_RUN', install)
            independent = {'kind': 'mini-pc-limit-upgrade-independent', 'verified': True, 'application_exact': True,
                'external_regions_unchanged_from_fresh_read': True, 'boot_attempted': False, 'audio_verified': False,
                'final_reader_counter': 0x100000, 'final_read_lost_bytes': 0, 'run': install_ref, 'plan': plan_ref,
                'full_before': before_ref, 'full_after': after_ref, 'candidate': candidate_ref}
            if fault=='independent': independent['verified'] = False
            if fault=='independent_ref': independent['run'] = {**install_ref, 'sha256': '0'*64}
            if fault=='independent_counter': independent['final_reader_counter'] = True
            if fault=='valid_lost_read': independent.update(final_reader_counter=0x100200, final_read_lost_bytes=512)
            if fault=='unbounded_lost': independent.update(final_reader_counter=0x101200, final_read_lost_bytes=4608)
            put('INDEPENDENT', independent)
            events = [{'event': event, 'path': 'OFFLINE-DISK', 'utc': '2026-11-16T00:00:00Z'} for event in (
                'mcn_open_intent', 'mcn_disable_intent', 'mcn_disabled', 'mcn_enable_intent', 'mcn_reenabled', 'mcn_handle_closed')]
            events[-1].update(close_ok=True, explicit_enable_succeeded=True, windows_file_object_cleanup_required=False, error=None)
            if fault=='MCN_log': events.pop()
            put('MCN_LOG', ('\n'.join(json.dumps(row) for row in events)+'\n').encode())
            put('BASE_PROFILE', {})
            pins = {path.relative_to(folder).as_posix(): runner.sha(path.read_bytes())
                    for key, path in paths.items() if key!='PINS'}
            if fault=='unpinned': pins.pop(paths['INDEPENDENT'].relative_to(folder).as_posix())
            put('PINS', pins)
            if fault=='changed_dump': paths['FULL_AFTER'].write_bytes(bytes(0x100000))
            (folder/'reset.bin').write_bytes(b'fake-reset'); (folder/'reset.elf').write_bytes(b'fake-elf')
            reset = {'slot': runner.A, 'file': 'reset.bin', 'elf': 'reset.elf', 'image_sha256': runner.sha(b'fake-reset')}
            (research/'mini-rom-reset.json').write_text(json.dumps({'source_sha256': {}, 'artifacts': [reset]}))
            profile = {'capabilities': {'read': True}, 'firmware_version': runner.EXPECTED_VERSION,
                       'image_sha256': runner.EXPECTED_CANDIDATE_SHA}
            if fault=='profile': profile['firmware_version'] = 'tankg_fw wrong'
            if fault=='existing_run': output.write_text('{}')
            stdout, thrown = io.StringIO(), None
            with ExitStack() as stack:
                changes = {'ROOT': folder, **paths, 'EXPECTED_PROFILE_SHA': runner.sha(paths['BASE_PROFILE'].read_bytes()),
                    'WindowsBufferedRomTransport': Transport, 'MiniRamSession': ResetSession,
                    'discover_windows_rom_disks': lambda: [{'path': 'OFFLINE-DISK', 'usb_ancestor': PARENT}],
                    'arrivals': arrivals, 'verify_recorded_hashes': lambda _: None, 'validate_reset_artifact': lambda *a, **k: None}
                for key, value in changes.items(): stack.enter_context(patch.object(runner, key, value))
                stack.enter_context(patch.object(runner.readonly, 'load_profile', return_value=profile))
                stack.enter_context(patch.object(runner.readonly, 'source_contract', return_value={'offline_fixture': True}))
                stack.enter_context(patch.object(runner.readonly, 'enumerate_ports', side_effect=enumerate_ports))
                stack.enter_context(patch.object(runner.readonly, 'run_read', side_effect=no_serial))
                stack.enter_context(patch.object(runner.readonly.SerialTransport, 'open', side_effect=no_serial))
                stack.enter_context(patch.object(runner.ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 1)), create=True))
                stack.enter_context(patch.object(runner.time, 'sleep'))
                stack.enter_context(patch('sys.argv', ['offline-v11-test', bootmode]+(['--check-only'] if check_only else [])))
                stack.enter_context(redirect_stdout(stdout))
                try: runner.main()
                except (ValueError, SystemExit) as error: thrown = error
            result = json.loads(output.read_bytes()) if output.exists() else None
            rows = [json.loads(x) for x in trace.read_text().splitlines()] if trace.exists() else []
        self.assertTrue(all(handle.closed for handle in handles))
        self.assertLessEqual(sum(op==0xFB08 for _, op in calls), 1)
        self.assertFalse(serial)
        return SimpleNamespace(result=result, calls=calls, handles=handles, resets=resets, rows=rows,
            enum_count=enum_count, thrown=thrown, stdout=stdout.getvalue())

    def test_current_runtime_data_preserved_and_one_reset_then_CDC_without_serial(self):
        r = self.run_fake()
        self.assertIsNone(r.thrown)
        self.assertEqual(r.result['phase'], 'application_USB_observed')
        self.assertEqual(r.calls, [(runner.B, 0xFC70), (runner.B, 0xFC73), (runner.A, 0xFB08)])
        self.assertEqual(r.resets, ['upload', 'verify_and_jump'])
        self.assertTrue(r.result['slot_A_inactive_verified'] and r.result['reset_submitted'])
        self.assertTrue(r.result['upgrade_verification']['external_regions_preserved_from_current_read'])
        self.assertFalse(r.result['upgrade_verification']['external_regions_assumed_stock'])
        self.assertEqual(r.result['buttons_assumed'], 'released')
        for key in ('buttons_confirmed_by_user', 'held_button_boot_trial_performed', 'cold_power_cycle_tested',
                    'guard_causality_confirmed', 'audio_verified', 'app_identity_verified', 'serial_port_opened',
                    'PING_attempted', 'firmware_write', 'automatic_retry'):
            self.assertIs(r.result[key], False)

    def test_incomplete_or_incoherent_installation_stops_before_any_device(self):
        for fault in ('incomplete_install', 'MCN', 'MCN_log', 'recorded_counter', 'restored_stock',
                      'preimage', 'outside_changed', 'plan', 'independent', 'independent_ref',
                      'independent_counter', 'unpinned', 'changed_dump', 'profile',
                      'missing_lost_audit', 'contradictory_lost_audit', 'unbounded_lost'):
            with self.subTest(fault=fault):
                r = self.run_fake(fault)
                self.assertIsInstance(r.thrown, ValueError)
                self.assertFalse(r.calls or r.handles or r.resets)

    def test_wrong_reader_identity_counter_or_USB_parent_never_uploads_A(self):
        for fault in ('identity', 'counter', 'arrival_changed', 'parent'):
            with self.subTest(fault=fault):
                r = self.run_fake(fault)
                self.assertIn('error', r.result)
                self.assertFalse(r.resets or r.result['reset_submitted'])
                self.assertFalse(any(handle.slot==runner.A for handle in r.handles))

    def test_one_lost_read_is_allowed_only_with_matching_independent_audit_and_live_counter(self):
        r = self.run_fake('valid_lost_read')
        self.assertIsNone(r.thrown)
        self.assertNotIn('error', r.result)
        self.assertEqual(r.result['phase'], 'application_USB_observed')
        self.assertEqual(r.result['upgrade_verification']['final_reader_counter'], 0x100200)
        self.assertEqual(r.result['upgrade_verification']['final_read_lost_bytes'], 512)

    def test_CDC_must_be_absent_before_and_unique_after_reset(self):
        for fault in ('existing_CDC', 'missing_CDC', 'multiple_CDC', 'wrong_COM'):
            with self.subTest(fault=fault):
                r = self.run_fake(fault)
                self.assertIn('error', r.result)
                self.assertFalse(r.result['application_USB_enumerated'])
                self.assertEqual(r.result['reset_submitted'], fault!='existing_CDC')
                self.assertLessEqual(r.enum_count, 31)

    def test_upload_or_reset_readback_failure_never_jumps(self):
        for fault in ('upload', 'reset_readback'):
            r = self.run_fake(fault)
            self.assertIn('error', r.result)
            self.assertFalse(r.result['reset_submitted'])

    def test_reset_error_never_retries_and_CDC_does_not_claim_PONG(self):
        before = self.run_fake('reset_presubmit')
        self.assertIn('error', before.result)
        after = self.run_fake('reset_postsubmit')
        self.assertEqual(after.result['reset_request']['jump_outcome'], 'post_submit_transport_error')
        self.assertEqual(after.result['phase'], 'application_USB_observed')
        self.assertFalse(after.result['app_identity_verified'] or after.result['audio_verified'])

    def test_existing_output_check_only_and_held_mode_open_nothing(self):
        r = self.run_fake('existing_run')
        self.assertIsInstance(r.thrown, ValueError); self.assertFalse(r.calls or r.handles)
        r = self.run_fake(check_only=True)
        self.assertFalse(r.calls or r.handles)
        self.assertFalse(json.loads(r.stdout)['serial_port_opened'])
        r = self.run_fake(bootmode='held')
        self.assertIsInstance(r.thrown, SystemExit); self.assertFalse(r.calls or r.handles)


if __name__ == '__main__': unittest.main()
