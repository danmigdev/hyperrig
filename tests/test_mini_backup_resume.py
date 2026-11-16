"""Interrupted stock entry continuation, using files and simulated USB only."""
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from hyperrig.installer import core, service, windows
from tests import test_mini_installer_service as service_fixture
from tests import test_mini_installer_windows as windows_fixture


def entry_fixture(root, timestamp=None):
    root.mkdir()
    (root / "stock-presets").mkdir()
    timestamp = time.time() if timestamp is None else timestamp
    events = [
        {"event": "session_created", "release_sha256": "a" * 64},
        {"event": "phase", "phase": "identifying"},
        {"event": "stock_midi_input_closed_before_transition"},
        {"event": "stock_to_rom_intent", "identity": core.STOCK_IDENTITY, "submitted_unix": timestamp,
         "stock_device": {"status": "OK", "instance_id": r"USB\VID_4C4A&PID_C755\UNIT"}},
        {"event": "session_failed", "failed_phase": "identifying", "message": "ROM detection timed out"},
    ]
    journal = root / "journal.jsonl"
    journal.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    presets = (b"\x46\0" + bytes(range(6)) + bytes(84)) * 21 + b"PATCHEND\0\0"
    (root / "stock-presets/presets.bin").write_bytes(presets)
    (root / "stock-presets/presets.json").write_text(json.dumps({"identity": core.STOCK_IDENTITY,
        "bytes": len(presets), "sha256": core._sha(presets), "equal_reads": 2}), encoding="utf-8")
    return events


class EntryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "old-entry"
        self.events = entry_fixture(self.root, timestamp=1000)

    def rewrite(self):
        (self.root / "journal.jsonl").write_text("\n".join(json.dumps(event) for event in self.events), encoding="utf-8")

    def test_valid_entry_keeps_source_unchanged(self):
        original = (self.root / "journal.jsonl").read_bytes()
        result = service.interrupted_stock_entry(self.root, timestamp=1200)
        self.assertEqual(result["identity"], core.STOCK_IDENTITY)
        self.assertEqual(result["source_journal_sha256"], core._sha(original))
        self.assertEqual((self.root / "journal.jsonl").read_bytes(), original)

    def test_any_ROM_access_rejects_continuation(self):
        self.events.insert(-1, {"event": "usb_command_intent", "opcode": "fb08"})
        self.rewrite()
        with self.assertRaisesRegex(ValueError, "no ROM access"):
            service.interrupted_stock_entry(self.root, timestamp=1200)

    def test_started_write_or_backup_is_not_an_entry_failure(self):
        for phase in ("installing", "backing_up", "verifying"):
            self.events[-1]["failed_phase"] = phase
            self.rewrite()
            with self.assertRaisesRegex(ValueError, "during stock entry"):
                service.interrupted_stock_entry(self.root, timestamp=1200)

    def test_stale_and_future_entries_are_rejected(self):
        for timestamp in (999, 2801):
            with self.assertRaisesRegex(ValueError, "fresh stock entry"):
                service.interrupted_stock_entry(self.root, timestamp=timestamp)

    def test_changed_preset_backup_is_rejected(self):
        path = self.root / "stock-presets/presets.bin"
        path.write_bytes(bytes(len(path.read_bytes())))
        with self.assertRaisesRegex(ValueError, "backup is incomplete or changed"):
            service.interrupted_stock_entry(self.root, timestamp=1200)

    def test_no_soft_key_or_two_soft_keys_are_rejected(self):
        original = list(self.events)
        for intents in ([], [original[3], original[3]]):
            self.events = original[:3] + intents + original[-1:]
            self.rewrite()
            with self.assertRaises(ValueError):
                service.interrupted_stock_entry(self.root, timestamp=1200)

    def test_invalid_USB_identifier_is_rejected(self):
        self.events[3]["stock_device"]["instance_id"] += "'; bad"
        self.rewrite()
        with self.assertRaisesRegex(ValueError, "USB identity"):
            service.interrupted_stock_entry(self.root, timestamp=1200)


class ResumeWindowsTests(unittest.TestCase):
    def setUp(self):
        self.case = windows_fixture.WindowsBackendTests("test_fresh_stock_entry_binds_identity_and_same_open_MIDI_then_new_ROM")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        c = self.case
        c.backend.attestation = None
        c.attestation.usb_ancestor = r"USB\VID_4C4A&PID_8057\ROM"
        c.patch("is_admin", lambda: True)
        c.patch("stock_devices", lambda: [])
        c.patch("hyperrig_ports", lambda: [])
        c.patch("discover_windows_rom_disks", lambda: [{"path": "ROM"}])
        c.patch("RomDiskAttestation", SimpleNamespace(from_discovery=lambda _: c.attestation))
        c.patch("ReadOnlyMini", Mock(side_effect=AssertionError("MIDI must not reopen")))
        self.locations = c.patch("usb_location_paths", Mock(return_value=[{"paths": ["same-physical-port"]}] * 2))
        self.entry = {"identity": core.STOCK_IDENTITY, "stock_instance_id": r"USB\VID_4C4A&PID_C755\UNIT",
                      "submitted_unix": c.clock.now(), "source_journal_sha256": "a" * 64}

    def resume(self):
        c = self.case
        return c.backend.continue_stock_rom(self.entry, c.release, c.store)

    def test_resume_checks_fresh_ROM_without_sending_MIDI_or_loading_RAM(self):
        self.assertEqual(self.resume(), core.STOCK_IDENTITY)
        self.locations.assert_called_once()
        self.assertIsNone(self.case.backend.live_slot)
        self.assertFalse(windows_fixture.Transport.created[0].calls)
        self.assertFalse(self.case.store.events[-1]["repeated_soft_key"])

    def test_different_connection_stops_before_ROM_open(self):
        self.locations.side_effect = ValueError("different USB connection")
        with self.assertRaisesRegex(ValueError, "different USB"):
            self.resume()
        self.assertFalse(windows_fixture.Transport.created)

    def test_stale_ROM_arrival_stops_before_reader(self):
        self.case.attestation.last_arrival_filetime -= 20 * 10_000_000
        with self.assertRaisesRegex(ValueError, "arrival predates"):
            self.resume()
        self.assertIsNone(self.case.backend.mcn)

    def test_normal_app_or_ambiguous_ROM_cannot_continue(self):
        with patch.object(windows, "stock_devices", return_value=[{"id": "stock"}]):
            with self.assertRaisesRegex(ValueError, "Only the recovered ROM"):
                self.resume()
        with patch.object(windows, "discover_windows_rom_disks", return_value=[{}, {}]):
            with self.assertRaisesRegex(ValueError, "Recover the USB"):
                self.resume()


class ResumeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        service_fixture.InstallWorkflowTests.setUpClass()

    def setUp(self):
        self.case = service_fixture.InstallWorkflowTests("test_boot_is_unavailable_until_complete_verification")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.source = Path(self.case.fixture.temp.name) / "previous-entry"
        entry_fixture(self.source)
        self.case.backend.continue_stock_rom = Mock(return_value=core.STOCK_IDENTITY)

    def test_continuation_creates_fresh_matching_backups_and_keeps_original_evidence(self):
        old = (self.source / "journal.jsonl").read_bytes()
        self.case.workflow.continue_backup(self.source)
        self.assertEqual(self.case.workflow.phase, "backed_up")
        self.assertEqual((self.source / "journal.jsonl").read_bytes(), old)
        self.assertEqual((self.case.destination / "source-entry-journal.jsonl").read_bytes(), old)
        self.case.assert_no_writer_or_boot()
        self.assertEqual([call[0] for call in self.case.backend.calls], ["read_full", "read_full"])

    def test_differing_full_reads_still_block_installation(self):
        self.case.backend.read_results["backup-b"] = self.case.fixture.unit_backup(47)
        with self.assertRaisesRegex(ValueError, "two full backups differ"):
            self.case.workflow.continue_backup(self.source)
        self.case.assert_no_writer_or_boot()
        self.assertEqual(self.case.workflow.phase, "failed")


if __name__ == "__main__":
    unittest.main()
