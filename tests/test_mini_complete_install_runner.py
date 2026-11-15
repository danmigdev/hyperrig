"""Audited-command installer orchestration; fake handles/NOR only, no hardware."""
from contextlib import ExitStack, redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.test_mini_buffered_install_runner import FakeOperational, fixture
from tools.probe_mini_recovery import RomCommandError

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


runner = module('complete_runner_test', 'analysis/hardware/run_mini_complete_install.py')


class CompleteRunnerTests(unittest.TestCase):
    def run_fake(self, failure=None, recover=False):
        installation = fixture()
        core = FakeOperational(installation)
        old = bytes(core.flash)
        prepared = SimpleNamespace(installation=installation, full_preimage=old)
        handles, pauses, calls, recovery_events, mcn_events = [], [], [], [], []
        readers, nor_wrappers, nor_events = [], [], []
        failed_reads = 0
        attestations, selections, native_diagnostics = [], [], []

        class AttestationFake:
            def __init__(self, generation):
                self.generation = generation

            @classmethod
            def from_discovery(cls, disk):
                assert disk == {'path': 'FAKE-DISK'}
                selections.append(copy.deepcopy(disk))
                chosen = cls(0)
                attestations.append(chosen)
                return chosen

        class BufferedFake:
            def __init__(self, path, *, slot, profile='ram-probe'):
                self.slot, self.profile = slot, profile
                self.disk = {'path': path}
                self.inquiry = {'vendor': 'WL82', 'product': 'UBOOT1.00'}
                self.adapter_descriptor = {'alignment_mask': 0}
                self.last_transfer = {'backend': 'offline-mcn-runner-test'}
                self.closed = self.failed = False
                self.reader_counter = 0x100000
                handles.append(self)

            def exchange(self, cdb, data_out=None, read_length=0):
                nonlocal failed_reads
                assert not self.closed and not self.failed
                op = int.from_bytes(cdb[:2], 'big')
                calls.append((self.slot, self.profile, op))
                if self.profile == 'nor-reader':
                    if op == 0xFC70:
                        return b'\xfc\x70HYRN\1\3' + struct.pack('>II', runner.B, 32768)
                    if op == 0xFC73:
                        return b'\xfc\x73\0\1' + bytes(8) + self.reader_counter.to_bytes(4, 'big')
                    if op == 0xFB08:
                        assert pauses[0].disabled
                        self.reader_counter = 0
                        return bytes(16)
                    raise AssertionError('unexpected fake reader opcode')
                assert self.slot == runner.A and self.profile == 'app-writer-operational'
                assert pauses[0].disabled and not pauses[0].closed
                if failure in ('unexecuted_read', 'reopen_rejected') and op == 0xFD7F and core.program_addresses and not failed_reads:
                    failed_reads += 1
                    self.failed = True
                    raise RomCommandError(31, 'fake unexecuted read', submitted=True)
                if failure in ('lost_program', 'unexecuted_program') and op == 0xFC7D and not failed_reads:
                    failed_reads += 1
                    if failure == 'lost_program': core.exchange(cdb, data_out, read_length)
                    self.failed = True
                    raise RomCommandError(31, 'fake program request failure', submitted=True)
                if failure in ('lost_finish', 'unexecuted_finish') and op == 0xFC80 and not failed_reads:
                    failed_reads += 1
                    if failure == 'lost_finish': core.exchange(cdb, data_out, read_length)
                    self.failed = True
                    raise RomCommandError(31, 'fake FINISH request failure', submitted=True)
                return core.exchange(cdb, data_out, read_length)

            def close(self): self.closed = True
            def __enter__(self): return self
            def __exit__(self, *_): self.close()

        def open_quiet(attestation, *, slot, profile='ram-probe'):
            # Every open must receive the object returned by the preceding open,
            # including recovery. Rebuilding the unbound discovery is rejected.
            self.assertIs(attestation, attestations[-1])
            self.assertEqual(attestation.generation, len(handles))
            if failure == 'reopen_rejected' and len(handles) == 2:
                raise ValueError('fake changed arrival during attested reopen')
            transport = BufferedFake('FAKE-DISK', slot=slot, profile=profile)
            chosen = AttestationFake(attestation.generation + 1)
            attestations.append(chosen)
            transport.attestation = chosen
            transport.opened_interface = 'OFFLINE-INTERFACE'
            transport.device_number = 4
            return transport

        def attach_diagnostic(transport):
            native_diagnostics.append(transport)
            if failure == 'open_logging' and transport.slot == runner.A:
                raise RuntimeError('fake post-open diagnostic failure')
            return SimpleNamespace(last_failure=None)

        class PauseFake:
            def __init__(self, transport, *, log):
                assert transport.slot == runner.B and not transport.closed
                self.closed, self.disabled, self.log = False, True, log
                self.close_calls = 0
                pauses.append(self)
                for event in ('mcn_open_intent', 'mcn_disable_intent', 'mcn_disabled'):
                    log({'event': event, 'path': transport.disk['path'], 'offline_mock': True})

            def close(self):
                if self.closed: return
                self.close_calls += 1
                self.log({'event': 'mcn_enable_intent', 'offline_mock': True})
                self.disabled = False
                self.log({'event': 'mcn_reenabled', 'offline_mock': True})
                self.closed = True
                self.log({'event': 'mcn_handle_closed', 'close_ok': True,
                    'explicit_enable_succeeded': True, 'windows_file_object_cleanup_required': False,
                    'error': None, 'offline_mock': True})

        class ReaderFake:
            def __init__(self, transport, *, slot, known_free_slot):
                assert slot == runner.B and known_free_slot
                self.transport = transport
                self.successful_bytes = 0
                self.initialized = False
                readers.append(self)

            def upload_and_start(self, payload, *, expected_sha256):
                assert payload == b'reader' and expected_sha256 == runner.sha(payload)
                self.transport.exchange(b'\xfb\x08' + bytes(14), read_length=16)
                return {'readback_verified': True, 'jump_sent': True, 'offline_mock': True}

            def initialize_spi(self):
                # Capture the actual raw status through the runner's logger,
                # just as the frozen MiniNorSession does before wrapper binding.
                raw = self.transport.exchange(b'\xfc\x73' + b'\xff' * 14, read_length=16)
                assert raw == b'\xfc\x73\0\1' + bytes(12)
                self.successful_bytes = 0
                self.initialized = True
                return {'jedec_hex': 'eb6014'}

            def read_flash(self, address, size, progress):
                assert address == 0 and size == 0x100000 and pauses[0].disabled
                assert self.initialized
                if recover:
                    assert isinstance(self.transport, NorRecoveryFake)
                    assert self.transport.reader is self
                if failure in ('full_read_reopened', 'full_read_recovered'):
                    self.transport.reopen_for_test()
                if failure in ('full_read', 'full_read_reopened'):
                    self.transport.failed = True
                    raise RomCommandError(31, 'fake final full read failed', submitted=True)
                self.successful_bytes = size
                progress(size, size)
                return bytes(core.flash)

        class NorRecoveryFake:
            """Fake only the separately tested HYRN recovery, not orchestration."""
            def __init__(self, transport, *, log, reopen_factory, max_recoveries):
                assert transport.profile == 'nor-reader' and transport.slot == runner.B
                assert max_recoveries == 8 and not transport.closed
                self.current, self.log, self.reopen_factory = transport, log, reopen_factory
                self.reader = None
                self.closed = self.failed = False
                self.close_calls = self.summary_calls = self.recovery_attempts = 0
                nor_wrappers.append(self)

            def bind_session(self, reader, *, status_raw):
                assert self.reader is None and reader.transport is self.current
                assert reader.initialized and reader.successful_bytes == 0
                assert status_raw is self.current.last_reader_status_raw
                assert status_raw == b'\xfc\x73\0\1' + bytes(12)
                self.reader = reader
                reader.transport = self
                self.log({'event': 'nor_reader_bound', 'status_hex': status_raw.hex(),
                          'transport_assigned': True, 'offline_mock': True})

            def reopen_for_test(self):
                assert self.reader.transport is self and not self.closed
                self.current.close()
                self.current = self.reopen_factory()
                self.recovery_attempts += 1
                self.log({'event': 'nor_recovery_reopen_intent', 'offline_mock': True})

            def close(self):
                self.close_calls += 1
                self.current.close()
                self.closed = True

            def summary(self):
                self.summary_calls += 1
                return {'recovery_attempts': self.recovery_attempts,
                        'closed': self.closed, 'failed': self.failed,
                        'current_handle_closed': self.current.closed,
                        'bound_reader': self.reader is not None, 'offline_mock': True}

        class RecoveryFake(runner.FinishCommandRecoveryTransport):
            def summary(self):
                if failure == 'writer_summary': raise RuntimeError('fake writer diagnostic failure')
                return super().summary()

        expected = old[:0x4000] + installation.candidate + old[0x82000:]

        def validate(plan, raw):
            assert plan is prepared and raw == expected
            return {'full_NOR_sha256': runner.sha(raw), 'external_regions_unchanged': True}

        def log(path, item, durable=False):
            if path.name == 'nor-read-recovery.jsonl':
                assert durable
                nor_events.append(item)
            elif path.name.endswith('recovery.jsonl'):
                assert durable
                recovery_events.append(item)
            if path.name.endswith('mcn.jsonl'):
                assert durable
                mcn_events.append(item)

        with tempfile.TemporaryDirectory(prefix='mini-reconciled-runner-test-', dir=ROOT / 'build') as name:
            folder = Path(name).resolve()
            self.assertTrue(folder.is_relative_to((ROOT / 'build').resolve()))
            trial = folder / 'trial.json'; trial.write_text('{}', encoding='utf-8')
            out, full_after = folder / 'run.json', folder / 'full-after.bin'
            with ExitStack() as stack:
                overrides = {'ROOT': folder, 'OUT': out, 'TRACE': folder / 'trace.jsonl',
                    'JOURNAL': folder / 'journal.jsonl', 'RECOVERY': folder / 'read-recovery.jsonl',
                    'NOR_RECOVERY_LOG': folder / 'nor-read-recovery.jsonl',
                    'MCN_LOG': folder / 'mcn.jsonl', 'FULL_AFTER': full_after,
                    'FULL_BEFORE': folder / 'before.bin', 'TRIAL': trial, 'PLAN': folder / 'plan.json',
                    'WindowsBufferedRomTransport': BufferedFake, 'MiniNorSession': ReaderFake,
                    'QuietBufferedRomTransport': open_quiet, 'RomDiskAttestation': AttestationFake,
                    'MiniMediaChangePause': PauseFake, 'FinishCommandRecoveryTransport': RecoveryFake,
                    'NorReadRecoveryTransport': NorRecoveryFake,
                    'EXPECTED_RETAINED_READER_BYTES': 0x100000,
                    'validate_completed_full': validate, 'append': log,
                    'attach_native_diagnostic': attach_diagnostic}
                for key, value in overrides.items(): stack.enter_context(patch.object(runner, key, value))
                stack.enter_context(patch.object(runner, 'prepare', return_value=({}, prepared,
                    {'flat_sha256': runner.sha(b'reader')}, b'reader')))
                discovery = stack.enter_context(patch.object(runner, 'discover_windows_rom_disks', return_value=[{'path': 'FAKE-DISK'}]))
                stack.enter_context(patch.object(runner.ctypes, 'windll',
                    SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 1)), create=True))
                stack.enter_context(patch.object(runner.time, 'sleep'))
                stack.enter_context(patch.object(runner.os, 'fsync'))
                stack.enter_context(patch('sys.argv', ['offline-quiet-test'] + (['--recover-audited-commands'] if recover else [])))
                stack.enter_context(redirect_stdout(io.StringIO()))
                runner.main()
                self.assertEqual(discovery.call_count, 1, 'no WMI discovery on subsequent opens/reopens')
            result = json.loads(out.read_text(encoding='utf-8'))
            post = full_after.read_bytes() if full_after.exists() else None
        self.assertEqual(len(selections), 1)
        self.assertEqual(len(attestations), len(handles) + 1)
        self.assertEqual([a.generation for a in attestations], list(range(len(handles) + 1)))
        self.assertTrue(all(h.closed for h in handles))
        self.assertEqual(len(pauses), 1)
        self.assertTrue(pauses[0].closed and not pauses[0].disabled)
        self.assertEqual(pauses[0].close_calls, 1)
        self.assertTrue(result['MCN_pause_started'] and result['MCN_pause_closed'] and result['MCN_explicitly_reenabled'])
        self.assertNotIn('MCN_cleanup_error', result)
        self.assertEqual(mcn_events[-1]['event'], 'mcn_handle_closed')
        self.assertFalse(result['automatic_reset'])
        self.assertEqual(result['automatic_mutation_retry'], recover)
        self.assertTrue(result['finished_utc'])
        self.assertEqual(len(nor_wrappers), int(bool(readers) and recover))
        for wrapper in nor_wrappers:
            self.assertIs(wrapper.reader, readers[0])
            self.assertIs(wrapper.reader.transport, wrapper)
            self.assertEqual((wrapper.close_calls, wrapper.summary_calls), (1, 1))
            self.assertTrue(wrapper.closed and wrapper.current.closed)
            self.assertEqual(nor_events[0]['event'], 'nor_reader_bound')
            self.assertTrue(result['full_after_read_recovery']['closed'])
            self.assertTrue(result['full_after_read_recovery']['bound_reader'])
            self.assertEqual(result['full_after_read_recovery']['failed'], wrapper.failed)
        if post is not None:
            self.assertEqual(result['full_after_target_read_counter'], 0x100000)
        return result, core, calls, handles, recovery_events, post, expected

    def test_success_B_A_B_keeps_MCN_paused_until_full_read_then_closes(self):
        result, core, calls, handles, _, post, expected = self.run_fake()
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertTrue(result['full_NOR_verified'] and result['installed_image_verified'])
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.B])
        self.assertEqual(result['known_live_slot'], runner.B)
        self.assertEqual(post, expected)
        self.assertEqual(core.erase_addresses, [0x5000, 0x4000])
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 2)

    def test_readonly_failure_recovers_without_repeated_mutations_and_closes_MCN(self):
        result, core, _, handles, _, post, expected = self.run_fake('unexecuted_read', recover=True)
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.A, runner.B])
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['read_reissues'], 1)
        self.assertEqual(len(core.erase_addresses), 2)
        self.assertEqual(len(core.program_addresses), 32)
        self.assertEqual(post, expected)

    def test_PP_error_is_not_retried_but_MCN_closes(self):
        result, core, calls, handles, _, post, _ = self.run_fake('lost_program', recover=True)
        self.assertEqual(result['error_phase'], 'install_and_verify_application')
        self.assertTrue(result['mutation_completion_unknown'])
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.A])
        self.assertEqual(core.program_addresses, [0x5000])
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 1)
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['mutation_request_reissues'], 0)
        self.assertEqual(sum(op == 0xFC7D for _, _, op in calls), 1)
        self.assertIsNone(post)

    def test_unexecuted_PP_reissues_request_once_and_programs_each_page_once(self):
        result, core, calls, handles, events, post, expected = self.run_fake('unexecuted_program', recover=True)
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.A, runner.B])
        self.assertTrue(result['full_NOR_verified'] and result['installed_image_verified'])
        self.assertFalse(result['mutation_completion_unknown'])
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['mutation_request_reissues'], 1)
        self.assertEqual(result['read_recovery_final']['completed_NOR_mutations_repeated'], 0)
        self.assertEqual(len(core.program_addresses), 32)
        self.assertEqual(len(set(core.program_addresses)), 32)
        self.assertEqual(core.erase_addresses, [0x5000, 0x4000])
        self.assertEqual(sum(op == 0xFC7D for _, _, op in calls), 33)
        self.assertEqual(sum(op == 0xFB7C for _, _, op in calls), 32)
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 2)
        self.assertTrue(any(e['event'] == 'unexecuted_mutation_recovery_reissue_intent'
                            and e['raw_audit_identical'] and e['sequence_unconsumed'] for e in events))
        self.assertEqual(post, expected)

    def test_final_full_read_error_keeps_image_verified_but_no_full_verification(self):
        result, core, calls, handles, _, post, _ = self.run_fake('full_read', recover=True)
        self.assertEqual(result['error_phase'], 'independent_complete_NOR_readback')
        self.assertTrue(result['installed_image_verified'])
        self.assertFalse(result['full_NOR_verified'] or result['mutation_completion_unknown'])
        self.assertEqual(result['known_live_slot'], runner.B)
        self.assertEqual(len(core.program_addresses), 32)
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 2)
        self.assertIsNone(post)
        self.assertTrue(result['full_after_read_recovery']['closed'])
        self.assertTrue(result['full_after_read_recovery']['failed'])
        self.assertNotIn('full_after_target_read_counter', result)

    def test_reopened_final_read_handle_closes_after_terminal_read_error(self):
        result, core, calls, handles, _, post, _ = self.run_fake('full_read_reopened', recover=True)
        self.assertEqual(result['error_phase'], 'independent_complete_NOR_readback')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.B, runner.B])
        self.assertTrue(result['installed_image_verified'])
        self.assertFalse(result['full_NOR_verified'] or result['mutation_completion_unknown'])
        self.assertEqual(result['known_live_slot'], runner.B)
        self.assertEqual(result['full_after_read_recovery']['recovery_attempts'], 1)
        self.assertTrue(result['full_after_read_recovery']['current_handle_closed'])
        self.assertTrue(result['full_after_read_recovery']['failed'])
        self.assertEqual(len(core.program_addresses), 32)
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 2)
        self.assertIsNone(post)

    def test_reopened_final_read_handle_closes_on_success_and_records_real_counter(self):
        result, _, calls, handles, _, post, expected = self.run_fake('full_read_recovered', recover=True)
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.B, runner.B])
        self.assertTrue(result['full_NOR_verified'])
        self.assertEqual(result['full_after_read_recovery']['recovery_attempts'], 1)
        self.assertTrue(result['full_after_read_recovery']['current_handle_closed'])
        self.assertFalse(result['full_after_read_recovery']['failed'])
        self.assertEqual(result['full_after_target_read_counter'], 0x100000)
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 2)
        self.assertEqual(post, expected)

    def test_baseline_final_read_error_without_wrapper_still_closes_MCN(self):
        result, _, _, handles, _, post, _ = self.run_fake('full_read', recover=False)
        self.assertEqual(result['error_phase'], 'independent_complete_NOR_readback')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.B])
        self.assertTrue(result['installed_image_verified'])
        self.assertFalse(result['full_NOR_verified'])
        self.assertNotIn('full_after_read_recovery', result)
        self.assertNotIn('full_after_target_read_counter', result)
        self.assertIsNone(post)

    def test_writer_diagnostic_exception_still_closes_MCN_and_finishes_report(self):
        result, _, _, _, _, post, expected = self.run_fake('writer_summary', recover=True)
        self.assertIn('writer_cleanup_error', result)
        self.assertIn('fake writer diagnostic failure', result['error'])
        self.assertEqual(post, expected)


    def test_reopen_rejects_changed_attestation_without_discovery_or_fallback(self):
        result, core, calls, handles, _, post, _ = self.run_fake('reopen_rejected', recover=True)
        self.assertEqual(result['error_phase'], 'install_and_verify_application')
        self.assertIn('fake changed arrival', result['error'])
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A])
        self.assertEqual(core.program_addresses, [0x5000])
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 1)
        self.assertTrue(result['read_recovery_final']['failed'])
        self.assertIsNone(post)

    def test_post_open_logging_error_closes_new_handle_and_MCN_before_any_writer_jump(self):
        result, core, calls, handles, _, post, _ = self.run_fake('open_logging')
        self.assertEqual(result['error_phase'], 'operational_writer_upload')
        self.assertIn('fake post-open diagnostic failure', result['error'])
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A])
        self.assertFalse(core.erase_addresses or core.program_addresses)
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 0)
        self.assertIsNone(post)


    def test_unexecuted_finish_reissues_once_without_repeating_NOR_mutations(self):
        result, core, calls, handles, events, post, expected = self.run_fake('unexecuted_finish', recover=True)
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.A, runner.B])
        self.assertTrue(result['full_NOR_verified'] and result['installed_image_verified'])
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['finish_request_reissues'], 1)
        self.assertEqual(core.erase_addresses, [0x5000, 0x4000])
        self.assertEqual(len(core.program_addresses), len(set(core.program_addresses)))
        self.assertEqual(len(core.program_addresses), 32)
        self.assertEqual(sum(op == 0xFC80 for _, _, op in calls), 3)
        self.assertEqual(post, expected)

    def test_executed_finish_with_lost_ACK_stops_without_repeating_request(self):
        result, core, calls, handles, events, post, expected = self.run_fake('lost_finish', recover=True)
        self.assertEqual(result['error_phase'], 'install_and_verify_application')
        self.assertFalse(result['full_NOR_verified'] or result['installed_image_verified'])
        self.assertFalse(result['mutation_completion_unknown'])
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['finish_request_reissues'], 0)
        self.assertEqual(sum(op == 0xFC80 for _, _, op in calls), 1)
        self.assertEqual(core.erase_addresses, [0x5000])
        self.assertEqual(len(core.program_addresses), 16)
        self.assertIsNone(post)


if __name__ == '__main__': unittest.main()
