"""Exercise the new buffered runner orchestration with fake handles/NOR only."""
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

from tests.test_mini_app_install import FakeOperational, fixture
from tools.probe_mini_recovery import RomCommandError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('buffered_runner_test', ROOT / 'analysis/hardware/run_mini_buffered_install.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class BufferedRunnerTests(unittest.TestCase):
    def run_fake(self, failure=None, recover=False):
        installation = fixture()
        core = FakeOperational(installation)
        old = bytes(core.flash)
        prepared = SimpleNamespace(installation=installation, full_preimage=old)
        handles, calls, recovery_events = [], [], []
        failed_reads = 0

        class BufferedFake:
            def __init__(self, path, *, slot, profile='ram-probe'):
                self.slot, self.profile = slot, profile
                self.disk = {'path': path}
                self.inquiry = {'vendor': 'WL82', 'product': 'UBOOT1.00'}
                self.adapter_descriptor = {'alignment_mask': 0}
                self.last_transfer = {'backend': 'spt-buffered-fake'}
                self.closed = self.failed = False
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
                        return b'\xfc\x73\0\1' + bytes(8) + (0x100000).to_bytes(4, 'big')
                    if op == 0xFB08:
                        return bytes(16)
                    raise AssertionError('unexpected fake reader opcode')
                assert self.slot == runner.A and self.profile == 'app-writer-operational'
                if (failure in ('unexecuted_read', 'two_unexecuted_reads') and op == 0xFD7F
                        and core.program_addresses and failed_reads < (2 if failure == 'two_unexecuted_reads' else 1)):
                    failed_reads += 1
                    self.failed = True
                    raise RomCommandError(31, 'fake unexecuted read', submitted=True,
                                          details={'backend': 'spt-buffered-fake'})
                return core.exchange(cdb, data_out, read_length)

            def close(self):
                self.closed = True

            def __enter__(self): return self
            def __exit__(self, *_): self.close()

        class ReaderFake:
            def __init__(self, transport, *, slot, known_free_slot):
                assert slot == runner.B and known_free_slot
                self.transport = transport

            def upload_and_start(self, payload, *, expected_sha256):
                assert payload == b'reader' and expected_sha256 == runner.sha(payload)
                self.transport.exchange(b'\xfb\x08' + bytes(14), read_length=16)
                return {'readback_verified': True, 'jump_sent': True, 'fake_only': True}

            def initialize_spi(self):
                return {'jedec_hex': 'eb6014'}

            def read_flash(self, address, size, progress):
                assert address == 0 and size == 0x100000
                progress(size, size)
                return bytes(core.flash)

        if failure == 'lost_program':
            core.fail_after = (0xFC7D, 1)
        expected = old[:0x4000] + installation.candidate + old[0x82000:]

        def validate(plan, raw):
            assert plan is prepared and raw == expected
            return {'full_NOR_sha256': runner.sha(raw), 'external_regions_unchanged': True}

        def log(path, item, durable=False):
            if path.name.endswith('recovery.jsonl'):
                assert durable
                recovery_events.append(item)

        with tempfile.TemporaryDirectory(prefix='mini-buffered-runner-test-', dir=ROOT / 'build') as name:
            folder = Path(name).resolve()
            self.assertTrue(folder.is_relative_to((ROOT / 'build').resolve()))
            trial = folder / 'trial.json'
            trial.write_text('{}', encoding='utf-8')
            out = folder / 'run.json'
            full_after = folder / 'full-after.bin'
            with ExitStack() as stack:
                overrides = {'ROOT': folder, 'OUT': out, 'TRACE': folder / 'trace.jsonl',
                    'JOURNAL': folder / 'journal.jsonl', 'RECOVERY': folder / 'read-recovery.jsonl',
                    'FULL_AFTER': full_after, 'FULL_BEFORE': folder / 'before.bin',
                    'TRIAL': trial, 'PLAN': folder / 'plan.json',
                    'WindowsBufferedRomTransport': BufferedFake, 'MiniNorSession': ReaderFake,
                    'validate_completed_full': validate, 'append': log}
                for key, value in overrides.items():
                    stack.enter_context(patch.object(runner, key, value))
                stack.enter_context(patch.object(runner, 'prepare', return_value=({}, prepared,
                    {'flat_sha256': runner.sha(b'reader')}, b'reader')))
                stack.enter_context(patch.object(runner, 'discover_windows_rom_disks', return_value=[{'path': 'FAKE-DISK'}]))
                stack.enter_context(patch.object(runner.ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 1))))
                stack.enter_context(patch.object(runner.time, 'sleep'))
                stack.enter_context(patch.object(runner.os, 'fsync'))
                stack.enter_context(patch('sys.argv', ['fake-runner'] + (['--recover-read-once'] if recover else [])))
                stack.enter_context(redirect_stdout(io.StringIO()))
                runner.main()
            result = json.loads(out.read_text(encoding='utf-8'))
            post = full_after.read_bytes() if full_after.exists() else None
        self.assertTrue(all(h.closed for h in handles), 'every initial and reopened handle must close')
        self.assertNotIn('automatic_retry', result, 'global retry flag would hide optional read recovery')
        return result, core, calls, handles, recovery_events, post, expected

    def test_complete_flow_uses_buffered_B_A_B_and_independent_read(self):
        result, core, calls, handles, _, post, expected = self.run_fake()
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertTrue(result['full_NOR_verified'] and result['installed_image_verified'])
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.B])
        self.assertEqual(post, expected)
        self.assertEqual(core.erase_addresses, [0x5000, 0x4000])
        self.assertEqual(core.program_addresses[-1], 0x4000)
        self.assertFalse(result['automatic_reset'] or result['automatic_mutation_retry'])
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 2)

    def test_one_explicit_unexecuted_read_reopens_same_buffered_writer_then_finishes(self):
        result, core, _, handles, events, post, expected = self.run_fake('unexecuted_read', recover=True)
        self.assertEqual(result['phase'], 'installed_verified_waiting_for_footswitch')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.A, runner.B])
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['read_reissues'], 1)
        self.assertTrue(result['read_recovery_final']['closed'])
        self.assertIn('read_recovery_unchanged_audit', [e['event'] for e in events])
        self.assertEqual(len(core.erase_addresses), 2)
        self.assertEqual(len(core.program_addresses), 32)
        self.assertEqual(post, expected)

    def test_lost_program_reply_never_reopens_retries_resets_or_uploads_reader(self):
        result, core, calls, handles, _, post, _ = self.run_fake('lost_program', recover=True)
        self.assertEqual(result['error_phase'], 'install_and_verify_application')
        self.assertTrue(result['writer_final']['failed'] and result['mutation_completion_unknown'])
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A])
        self.assertEqual(core.erase_addresses, [0x5000])
        self.assertEqual(core.program_addresses, [0x5000])
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 1)
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 0)
        self.assertIsNone(post)

    def test_second_read_error_is_terminal_without_second_reopen(self):
        result, core, calls, handles, _, post, _ = self.run_fake('two_unexecuted_reads', recover=True)
        self.assertEqual(result['error_phase'], 'install_and_verify_application')
        self.assertEqual([h.slot for h in handles], [runner.B, runner.A, runner.A])
        self.assertEqual(result['read_recovery_final']['recovery_attempts'], 1)
        self.assertEqual(result['read_recovery_final']['read_reissues'], 1)
        self.assertTrue(result['read_recovery_final']['failed'])
        self.assertEqual(core.program_addresses, [0x5000])
        self.assertEqual(sum(op == 0xFB08 for _, _, op in calls), 1)
        self.assertIsNone(post)


if __name__ == '__main__': unittest.main()
