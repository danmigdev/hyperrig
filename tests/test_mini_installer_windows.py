"""Windows installer orchestration with fake MIDI, PnP and ROM transports.

No test opens a device. The optional PowerShell check parses captured source;
it never invokes that source or queries PnP.
"""
from contextlib import ExitStack
import base64
import hashlib
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from hyperrig.installer import windows


class Store:
    root = Path("private-test-session")

    def __init__(self):
        self.events = []
        self.fail_event = None

    def event(self, event, **fields):
        if event == self.fail_event:
            raise OSError("simulated journal failure")
        self.events.append({"event": event, **fields})


class Transport:
    created = []

    def __init__(self, attestation, *, slot, profile):
        self.attestation, self.slot, self.profile = attestation, slot, profile
        self.disk = {"path": r"\\.\PhysicalDrive7"}
        self.inquiry = {"vendor": "WL82", "product": "UBOOT1.00"}
        self.calls = []
        self.closed = False
        self.failure = None
        self.reply = None
        self.created.append(self)

    def exchange(self, cdb, data_out=None, read_length=0):
        self.calls.append((bytes(cdb), data_out, read_length))
        if self.failure:
            raise self.failure
        return self.reply if self.reply is not None else bytes(read_length)

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class Pause:
    def __init__(self, transport, *, log):
        self.transport, self.closed = transport, False

    def close(self):
        self.closed = True


class Midi:
    identity = "TANK MINI_009"
    instances = []

    def __init__(self, incoming, outgoing):
        self.indices = incoming, outgoing
        self.midi_in = SimpleNamespace(close_port=Mock())
        self.midi_out = SimpleNamespace(send_message=Mock())
        self.closed = False
        self.backups = []
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def backup(self, destination):
        self.backups.append(destination)
        return {"equal_reads": 2}


class Clock:
    def __init__(self):
        self.value = 1_800_000_000.0

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class Reader:
    def __init__(self, raw=None):
        self.successful_bytes = windows.CAPACITY
        self.raw = raw if raw is not None else bytes(windows.CAPACITY)
        self.calls = []
        self.failure = None
        self.counter_delta = windows.CAPACITY

    def _handshake(self):
        self.calls.append("identity")

    def _status(self, expected):
        self.calls.append(("status", expected))
        if self.failure:
            raise self.failure

    def read_flash(self, address, length, *, progress):
        self.calls.append(("read", address, length))
        self.successful_bytes += self.counter_delta
        progress(length, length)
        return self.raw


class WindowsBackendTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        Transport.created = []
        Midi.instances = []
        self.clock = Clock()
        self.store = Store()
        self.attestation = SimpleNamespace(
            last_arrival_filetime=int((self.clock.now() + 11644473600) * 10_000_000),
            summary=lambda: {"instance": "fake-ROM", "arrival": "fresh"})
        self.release = SimpleNamespace(
            manifest={"stock_identity": "TANK MINI_009", "jedec_hex": "eb6014",
                      "reader": {"sha256": "reader-pin"}, "reset": {"sha256": "reset-pin"}},
            reader=b"reader", reset=b"reset", reset_elf=b"ELF", reset_contract={"slot": windows.A})
        self.backend = windows.WindowsBackend()
        self.backend.store = self.store
        self.backend.attestation = self.attestation
        self.stack.enter_context(patch.object(self.backend, "_claim_host_session", Mock()))
        self.patch("QuietBufferedRomTransport", Transport)
        self.patch("MiniMediaChangePause", Pause)
        self.stack.enter_context(patch.object(windows.time, "sleep", self.clock.sleep))
        self.stack.enter_context(patch.object(windows.time, "monotonic", self.clock.now))
        self.stack.enter_context(patch.object(windows.time, "time", self.clock.now))

    def patch(self, name, value):
        return self.stack.enter_context(patch.object(windows, name, value))

    def entry_setup(self):
        self.backend.attestation = None
        self.patch("is_admin", lambda: True)
        self.patch("ReadOnlyMini", Midi)
        self.patch("ports", lambda: {"inputs": ["MINI input"], "outputs": ["MINI output"]})
        self.patch("hyperrig_ports", lambda: [])
        stock = [{"instance_id": r"USB\VID_4C4A&PID_C755\UNIT", "status": "OK"}]
        self.stock_mock = self.patch("stock_devices", Mock(side_effect=[stock, stock, []]))
        self.rom_mock = self.patch("discover_windows_rom_disks", Mock(side_effect=[[], [], [{"path": "ROM"}]]))
        self.patch("RomDiskAttestation", SimpleNamespace(from_discovery=lambda _: self.attestation))
        return {"input_index": 0, "output_index": 0,
                "input_name": "MINI input", "output_name": "MINI output"}

    def retained_reader(self):
        self.backend.live_slot = windows.B
        self.backend.reader = Reader()
        self.backend.reader_wrapper = SimpleNamespace(lost_read_bytes=0, close=Mock())
        self.backend.reader_transport = SimpleNamespace(close=Mock())
        return self.backend.reader

    def test_fresh_stock_entry_binds_identity_and_same_open_MIDI_then_new_ROM(self):
        selection = self.entry_setup()
        result = self.backend.enter_stock_rom(selection, self.release, self.store)
        self.assertEqual(result, "TANK MINI_009")
        device = Midi.instances[0]
        self.assertEqual(device.indices, (0, 0))
        self.assertEqual(device.backups, [self.store.root / "stock-presets"])
        device.midi_out.send_message.assert_called_once_with(list(windows.SOFT_KEY_SYSEX))
        self.assertTrue(device.closed)
        self.assertIs(self.backend.attestation, self.attestation)
        self.assertTrue(Transport.created[0].closed)
        self.assertFalse(self.backend.mcn.closed)
        self.assertIsNone(self.backend.live_slot)
        self.assertFalse(self.backend.jump_unknown)
        self.assertEqual([e["event"] for e in self.store.events],
                         ["stock_midi_input_closed_before_transition", "stock_to_rom_intent", "fresh_rom_verified"])

    def test_input_closes_before_soft_key_on_the_same_identified_output(self):
        selection = self.entry_setup()

        def enter(device):
            def send(_):
                device.midi_in.close_port.assert_called_once_with()
                self.assertFalse(device.closed)
            device.midi_out.send_message.side_effect = send
            return device

        with patch.object(Midi, "__enter__", enter):
            self.backend.enter_stock_rom(selection, self.release, self.store)
        Midi.instances[-1].midi_out.send_message.assert_called_once_with(list(windows.SOFT_KEY_SYSEX))

    def test_failed_input_close_stops_before_soft_key(self):
        selection = self.entry_setup()

        def enter(device):
            device.midi_in.close_port.side_effect = SystemError("cannot release input")
            return device

        with patch.object(Midi, "__enter__", enter):
            with self.assertRaisesRegex(SystemError, "cannot release input"):
                self.backend.enter_stock_rom(selection, self.release, self.store)
        Midi.instances[-1].midi_out.send_message.assert_not_called()
        self.assertTrue(Midi.instances[-1].closed)
        self.assertFalse(Transport.created)

    def test_existing_ROM_and_changed_MIDI_selection_stop_before_soft_key(self):
        selection = self.entry_setup()
        self.rom_mock.side_effect = [[{"path": "already-ROM"}]]
        with self.assertRaisesRegex(ValueError, "already in ROM"):
            self.backend.enter_stock_rom(selection, self.release, self.store)
        self.assertFalse(Midi.instances)
        self.rom_mock.side_effect = [[], []]
        selection["input_name"] = "another port"
        with self.assertRaisesRegex(ValueError, "port list changed"):
            self.backend.enter_stock_rom(selection, self.release, self.store)
        self.assertFalse(Midi.instances)
        self.assertFalse(Transport.created)

    def test_wrong_stock_identity_closes_MIDI_without_backup_or_soft_key(self):
        selection = self.entry_setup()
        with patch.object(Midi, "identity", "TANK MINI_008"):
            with self.assertRaisesRegex(ValueError, "Unsupported stock"):
                self.backend.enter_stock_rom(selection, self.release, self.store)
        device = Midi.instances[0]
        self.assertTrue(device.closed)
        self.assertFalse(device.backups)
        device.midi_out.send_message.assert_not_called()
        self.assertFalse(Transport.created)

    def test_changed_stock_device_and_journal_error_cannot_send_soft_key(self):
        selection = self.entry_setup()
        self.stock_mock.side_effect = [
            [{"instance_id": "first", "status": "OK"}],
            [{"instance_id": "second", "status": "OK"}],
        ]
        with self.assertRaisesRegex(ValueError, "selection changed"):
            self.backend.enter_stock_rom(selection, self.release, self.store)
        Midi.instances[-1].midi_out.send_message.assert_not_called()
        self.stock_mock.side_effect = [[{"instance_id": "same", "status": "OK"}]] * 2
        self.rom_mock.side_effect = [[], []]
        self.store.fail_event = "stock_to_rom_intent"
        with self.assertRaisesRegex(OSError, "journal"):
            self.backend.enter_stock_rom(selection, self.release, self.store)
        Midi.instances[-1].midi_out.send_message.assert_not_called()
        self.assertTrue(Midi.instances[-1].closed)

    def test_stale_ROM_arrival_cannot_start_reader_or_suspend_polling(self):
        selection = self.entry_setup()
        self.attestation.last_arrival_filetime -= 20 * 10_000_000
        with self.assertRaisesRegex(ValueError, "arrival predates"):
            self.backend.enter_stock_rom(selection, self.release, self.store)
        self.assertTrue(Transport.created[0].closed)
        self.assertFalse(Transport.created[0].calls)
        self.assertIsNone(self.backend.mcn)

    def test_no_jump_into_live_slot_and_ambiguous_jump_is_never_repeated(self):
        self.backend.live_slot = windows.B
        transport = self.backend._open(windows.B, "nor-reader")
        jump = b"\xfb\x08" + bytes(14)
        with self.assertRaisesRegex(ValueError, "inactive slot"):
            transport.exchange(jump, read_length=16)
        self.assertFalse(transport.calls)
        target = self.backend._open(windows.A, "app-writer-operational")
        target.failure = OSError("lost jump reply")
        with self.assertRaisesRegex(OSError, "lost jump"):
            target.exchange(jump, read_length=16)
        self.assertIsNone(self.backend.live_slot)
        self.assertTrue(self.backend.jump_unknown)
        with self.assertRaisesRegex(ValueError, "inactive slot"):
            target.exchange(jump, read_length=16)
        self.assertEqual(len(target.calls), 1)

    def test_journal_failure_before_exchange_prevents_native_submission(self):
        transport = self.backend._open(windows.A, "app-writer-operational")
        self.store.fail_event = "usb_command_intent"
        with self.assertRaisesRegex(OSError, "journal"):
            transport.exchange(b"\xfc\x7d" + bytes(14), read_length=16)
        self.assertFalse(transport.calls)

    def test_large_payload_hashes_and_command_numbers_survive_handle_reopen(self):
        payload = bytes(range(256))
        first = self.backend._open(windows.A, "app-writer-operational")
        first.reply = payload
        first.exchange(b"\xfd\x87" + bytes(14), data_out=payload, read_length=256)
        second = self.backend._open(windows.A, "app-writer-operational")
        second.reply = bytes(16)
        second.exchange(b"\xfc\x7e" + bytes(14), read_length=16)
        intent_a, reply_a, intent_b, reply_b = self.store.events
        self.assertEqual([e["command_number"] for e in self.store.events], [1, 1, 2, 2])
        self.assertEqual(intent_a["data_out_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(reply_a["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertIsNone(reply_a["response_hex"])
        self.assertIsNone(intent_b["data_out_sha256"])
        self.assertEqual(reply_b["response_hex"], bytes(16).hex())

    def test_reopens_keep_the_bound_attestation_and_require_live_callback(self):
        self.backend.live_slot = windows.A
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            self.backend._reopen_reader()
        self.backend.live_slot = windows.B
        first = self.backend._reopen_reader()
        second = self.backend._reopen_reader()
        self.assertIs(first.attestation, self.attestation)
        self.assertIs(second.attestation, first.attestation)
        self.backend.jump_unknown = True
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            self.backend._reopen_reader()

    def test_retained_reader_is_reused_and_physical_counter_is_verified(self):
        reader = self.retained_reader()
        progress = Mock()
        with patch.object(self.backend, "_start_reader", side_effect=AssertionError("must retain B")):
            for label in ("backup-b", "pre-install"):
                raw = self.backend.read_full(self.release, self.store, progress, label)
                self.assertEqual(len(raw), windows.CAPACITY)
        self.assertEqual(reader.successful_bytes, 3 * windows.CAPACITY)
        self.assertEqual(reader.calls[:3], ["identity", ("status", windows.CAPACITY),
                                           ("read", 0, windows.CAPACITY)])
        self.assertEqual(progress.call_count, 2)
        reader.counter_delta = windows.CAPACITY - 512
        with self.assertRaisesRegex(ValueError, "counter"):
            self.backend.read_full(self.release, self.store, progress, "bad-counter")

    def test_counter_accepts_only_explicit_lost_read_reconciliation(self):
        reader = self.retained_reader()
        original = reader.read_flash

        def read(*args, **kwargs):
            reader.counter_delta = windows.CAPACITY + 512
            self.backend.reader_wrapper.lost_read_bytes += 512
            return original(*args, **kwargs)

        reader.read_flash = read
        self.backend.read_full(self.release, self.store, Mock(), "reconciled")
        self.assertEqual(self.store.events[-1]["reconciled_lost_bytes"], 512)
        reader.read_flash = original
        with self.assertRaisesRegex(ValueError, "counter"):
            self.backend.read_full(self.release, self.store, Mock(), "unexplained")

    def test_reader_status_failure_stops_before_read_or_writer_upload(self):
        reader = self.retained_reader()
        reader.failure = ValueError("stale reader status")
        with self.assertRaisesRegex(ValueError, "stale"):
            self.backend.read_full(self.release, self.store, Mock(), "failed")
        self.assertFalse(any(isinstance(c, tuple) and c[0] == "read" for c in reader.calls))
        with self.assertRaisesRegex(ValueError, "stale"):
            self.backend.write_application(SimpleNamespace(), self.store, Mock())
        self.assertFalse(Transport.created)

    def test_writer_constructor_failure_closes_already_open_A_transport(self):
        self.retained_reader()
        self.patch("BoundedCommandRecoveryTransport", Mock(side_effect=ValueError("wrapper rejected")))
        with self.assertRaisesRegex(ValueError, "wrapper rejected"):
            self.backend.write_application(SimpleNamespace(), self.store, Mock())
        self.assertEqual(len(Transport.created), 1)
        self.assertTrue(Transport.created[0].closed)

    def test_writer_preimage_failure_has_no_install_or_reset_and_preserves_terminal_state(self):
        reader = self.retained_reader()
        wrappers = []
        stages = []
        outer = self

        class Wrapper:
            def __init__(self, transport, *, log, reopen_factory, max_recoveries):
                outer.assertEqual(max_recoveries, 32)
                self.transport, self.closed = transport, False
                self.reopen = reopen_factory
                wrappers.append(self)

            def bind_session(self, writer):
                self.session = writer

            def close(self):
                self.closed = True
                self.transport.close()

        class Writer:
            def __init__(self, wrapper, installation, *, journal, known_free_slot):
                outer.assertTrue(known_free_slot)
                self.wrapper = wrapper
                self.phase, self.failed = "created", False
                self.image_verified = self.preimage_verified = False
                self.verified_sectors, self.last_audit, self.last_status = [], {"sequence": 0}, {"phase": 1}
                self.mutation_command_submitted = self.mutation_completion_unknown = False
                self.ambiguous_operation = None

            def upload_and_start(self, payload, *, expected_sha256):
                stages.append("upload")
                outer.assertEqual((payload, expected_sha256), (b"writer", "writer-pin"))
                self.wrapper.transport.exchange(b"\xfb\x08" + bytes(14), read_length=16)

            def initialize_spi(self):
                stages.append("initialize")
                outer.assertEqual(outer.backend.live_slot, windows.A)
                outer.assertFalse(outer.backend.jump_unknown)
                self.phase = "initialized"

            def verify_complete_preimage(self):
                stages.append("preimage")
                self.failed = True
                self.ambiguous_operation = "verify_complete_application_preimage"
                raise ValueError("full application preimage differs")

            def install_application(self):
                raise AssertionError("must not erase or program after a failed preimage")

        self.patch("BoundedCommandRecoveryTransport", Wrapper)
        self.patch("MiniAppInstallerSession", Writer)
        installation = SimpleNamespace(image=b"writer", image_sha256="writer-pin", sector_order=(0x5000, 0x4000))
        with self.assertRaisesRegex(ValueError, "preimage differs"):
            self.backend.write_application(installation, self.store, Mock())
        self.assertEqual(stages, ["upload", "initialize", "preimage"])
        self.assertEqual(reader.calls, ["identity", ("status", windows.CAPACITY)])
        self.assertTrue(wrappers[0].closed)
        self.assertTrue(Transport.created[0].closed)
        self.assertEqual(len(Transport.created), 1)
        self.assertEqual([int.from_bytes(c[0][:2], "big") for c in Transport.created[0].calls], [0xFB08])
        terminal = self.store.events[-1]
        self.assertEqual(terminal["event"], "writer_terminal_state")
        self.assertTrue(terminal["failed"])
        self.assertFalse(terminal["mutation_command_submitted"])
        self.assertFalse(terminal["mutation_completion_unknown"])
        self.assertEqual(terminal["last_audit"], {"sequence": 0})
        self.assertEqual(terminal["live_slot"], windows.A)

    def test_backend_close_restores_MCN_even_if_reader_close_fails(self):
        self.retained_reader()
        pause = self.backend.mcn = Pause(None, log=None)
        self.backend.reader_wrapper.close.side_effect = OSError("reader close failed")
        with self.assertRaisesRegex(OSError, "reader close failed"):
            self.backend.close()
        self.assertTrue(pause.closed)
        self.assertIsNone(self.backend.mcn)

    def test_host_session_reservation_is_released_even_if_MCN_cleanup_fails(self):
        self.backend.mcn = SimpleNamespace(close=Mock(side_effect=OSError("MCN close failed")))
        self.backend._mutex, self.backend._mutex_api = 123, SimpleNamespace(CloseHandle=Mock(return_value=1))
        with self.assertRaisesRegex(OSError, "MCN close failed"):
            self.backend.close()
        self.backend._mutex_api.CloseHandle.assert_called_once_with(123)
        self.assertIsNone(self.backend._mutex)

    def test_reset_requires_retained_known_reader_and_no_application_beforehand(self):
        self.patch("hyperrig_ports", lambda: [{"device": "COM3"}])
        self.patch("stock_devices", lambda: [])
        with self.assertRaisesRegex(ValueError, "retained"):
            self.backend.boot(self.release, self.store, expected="hyperrig")
        reader = self.retained_reader()
        with self.assertRaisesRegex(ValueError, "Unexpected application"):
            self.backend.boot(self.release, self.store, expected="hyperrig")
        self.assertIs(self.backend.reader, reader)
        self.assertFalse(Transport.created)

    def test_reset_once_in_inactive_A_only_after_B_identity_and_MCN_cleanup(self):
        reader = self.retained_reader()
        retained_wrapper = self.backend.reader_wrapper
        pause = self.backend.mcn = Pause(None, log=None)
        self.patch("hyperrig_ports", Mock(side_effect=[[], [{"device": "COM3"}]]))
        self.patch("stock_devices", lambda: [])
        outer = self

        class Reset:
            def __init__(self, transport, *, slot, known_free_slot):
                outer.assertEqual(slot, windows.A)
                outer.assertTrue(known_free_slot)
                outer.assertTrue(pause.closed)
                retained_wrapper.close.assert_called_once()
                self.transport = transport

            def upload_only(self, payload, *, expected_sha256):
                outer.assertEqual(payload, b"reset")
                outer.assertEqual(expected_sha256, "reset-pin")

            def start_reset_once(self, payload, *, elf, manifest):
                outer.assertEqual((payload, elf, manifest), (b"reset", b"ELF", {"slot": windows.A}))
                self.transport.exchange(b"\xfb\x08" + bytes(14), read_length=16)
                return {"reset_submitted": True, "reset_verified": False}

        self.patch("MiniRamSession", Reset)
        result = self.backend.boot(self.release, self.store, expected="hyperrig")
        self.assertEqual(reader.calls, ["identity", ("status", windows.CAPACITY)])
        self.assertTrue(Transport.created[0].closed)
        self.assertEqual(len(Transport.created[0].calls), 1)
        self.assertEqual(result["reset_attempts"], 1)
        self.assertTrue(result["USB_observed"])
        for key in ("firmware_handshake_verified", "audio_verified", "cold_boot_recovery_tested"):
            self.assertIs(result[key], False)
        self.assertIsNone(self.backend.live_slot)
        self.assertFalse(self.backend.jump_unknown)

    def test_stock_metadata_script_is_valid_PowerShell_without_running_it(self):
        completed = SimpleNamespace(stdout="[]")
        actual_run = subprocess.run
        with patch.object(windows.subprocess, "run", return_value=completed) as run:
            self.assertEqual(windows.stock_devices(), [])
        args = run.call_args.args[0]
        self.assertEqual(args[:4], ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"])
        script = args[-1]
        self.assertTrue(script.startswith("$ErrorActionPreference = 'Stop'"))
        executable = shutil.which("powershell.exe")
        if executable is None:
            return
        source_b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
        parse_only = (
            "$s=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + source_b64 + "'));"
            "$t=$null;$e=$null;"
            "$null=[System.Management.Automation.Language.Parser]::ParseInput($s,[ref]$t,[ref]$e);"
            "if($e.Count){$e|ForEach-Object{$_.Message};exit 1}"
        )
        encoded = base64.b64encode(parse_only.encode("utf-16-le")).decode("ascii")
        parsed = actual_run([executable, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                            capture_output=True, text=True, timeout=15)
        self.assertEqual(parsed.returncode, 0, parsed.stdout + parsed.stderr)


if __name__ == "__main__":
    unittest.main()
