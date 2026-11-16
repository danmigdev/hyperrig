"""Installer orchestration with an in-memory device and durable temporary files.

The shared fixture uses official stock code, approved public release artifacts,
and synthetic unit data. No transport is opened and no real reset is invoked.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from hyperrig.installer import core, service
from tests import test_portable_mini_installer_core as public_fixture


class FakeBackend:
    """Record explicit actions; apply only the supplied application in memory."""

    jedec_hex = core.JEDEC_HEX

    def __init__(self, flash):
        self.flash = flash
        self.original = flash
        self.identity = core.STOCK_IDENTITY
        self.calls = []
        self.read_results = {}
        self.installations = []
        self.boot_requests = []
        self.close_count = 0
        self.write_error = None
        self.boot_error = None
        self.before_write = None
        self.before_read = None

    def enter_stock_rom(self, selection, release, store):
        self.calls.append(("enter_stock_rom", selection))
        return self.identity

    def read_full(self, release, store, progress, stage):
        self.calls.append(("read_full", stage))
        if self.before_read is not None:
            self.before_read(stage)
        result = self.read_results.get(stage, self.flash)
        if isinstance(result, Exception):
            raise result
        if callable(result):
            result = result(self.flash)
        progress(stage, len(result), core.CAPACITY)
        return result

    def write_application(self, installation, store, progress):
        self.calls.append(("write_application", installation.plan_sha256))
        self.installations.append(installation)
        if self.before_write is not None:
            self.before_write(installation, store)
        if installation.preimage != self.flash[core.APP_START:core.APP_END]:
            raise AssertionError("Service sent a writer with a different preimage")
        if self.write_error is not None:
            # A mutation may already have happened when the transport fails.
            address = installation.sector_order[0]
            page = installation.page(address)
            self.flash = self.flash[:address] + page + self.flash[address + len(page):]
            raise self.write_error
        self.flash = self.flash[:core.APP_START] + installation.candidate + self.flash[core.APP_END:]
        progress("write_application", len(installation.sector_order), len(installation.sector_order))

    def boot(self, release, store, *, expected):
        self.calls.append(("boot", expected))
        self.boot_requests.append(expected)
        if self.boot_error is not None:
            raise self.boot_error
        return {"kind": "fake-boot-observation", "expected": expected, "usb_observed": True,
                "device_access_performed": False, "audio_verified": False}

    def close(self):
        self.calls.append(("close",))
        self.close_count += 1


class InstallWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        public_fixture.PortableCoreTests.setUpClass()

    def setUp(self):
        self.fixture = public_fixture.PortableCoreTests("test_public_stock_pins_and_release_ELF_validation")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.release = core.load_release(self.fixture.bundle)
        self.backend = FakeBackend(self.fixture.backup)
        self.destination = Path(self.fixture.temp.name) / "unit-session"
        self.notifications = []
        self.workflow = service.InstallWorkflow(self.release, self.backend, self.destination,
                                                notify=self.notifications.append)
        self.addCleanup(self.workflow.close)

    def journal(self):
        return [json.loads(line) for line in (self.destination / "journal.jsonl").read_text(encoding="utf-8").splitlines()]

    def backup(self):
        return self.workflow.backup({"id": "synthetic-stock-MINI"})

    def assert_no_writer_or_boot(self):
        self.assertEqual(self.backend.installations, [])
        self.assertEqual(self.backend.boot_requests, [])

    def assert_terminal(self):
        self.assertEqual(self.workflow.phase, "failed")
        prior_calls = list(self.backend.calls)
        for action in (self.workflow.install, self.workflow.boot, self.workflow.cancel_to_stock,
                       lambda: self.workflow.backup({"id": "same-device"})):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(self.backend.calls, prior_calls)
        self.assertEqual(self.workflow.phase, "failed")

    def test_success_retains_exact_backups_and_verifies_before_explicit_boot(self):
        def inspect_before_write(installation, store):
            self.assertEqual((store.root / "stock-flash-a.bin").read_bytes(), self.backend.original)
            self.assertEqual((store.root / "stock-flash-b.bin").read_bytes(), self.backend.original)
            self.assertEqual((store.root / "full-before.bin").read_bytes(), self.backend.original)
            plan = json.loads((store.root / "installation-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["plan_sha256"], installation.plan_sha256)
            self.assertEqual(installation.preimage, self.backend.original[core.APP_START:core.APP_END])
            self.assertEqual(installation.sector_order[-1], core.APP_START)
            self.assertEqual(self.workflow.phase, "installing")

        self.backend.before_write = inspect_before_write
        plan = self.backup()
        self.assertEqual(self.workflow.phase, "backed_up")
        self.assert_no_writer_or_boot()
        verified = self.workflow.install()
        self.assertEqual(self.workflow.phase, "verified")
        self.assertEqual(len(self.backend.installations), 1)
        self.assertEqual(self.backend.boot_requests, [])
        self.assertEqual((self.destination / "full-after.bin").read_bytes(), self.workflow.prepared.expected_full)
        self.assertEqual(json.loads((self.destination / "verification.json").read_text()), verified)
        self.assertEqual(verified["plan_sha256"], plan["plan_sha256"])
        self.assertTrue(verified["external_regions_unchanged"])
        self.assertFalse(verified["boot_verified"])
        self.assertEqual(self.backend.flash[:core.APP_START], self.backend.original[:core.APP_START])
        self.assertEqual(self.backend.flash[core.APP_END:], self.backend.original[core.APP_END:])
        boot = self.workflow.boot()
        self.assertEqual(self.backend.boot_requests, ["hyperrig"])
        self.assertEqual(self.workflow.phase, "usb_detected")
        self.assertEqual(json.loads((self.destination / "boot-observation.json").read_text()), boot)
        self.assertEqual([entry[1] for entry in self.backend.calls if entry[0] == "read_full"],
                         ["backup-a", "backup-b", "pre-install", "full-after"])
        self.assertEqual([item["phase"] for item in self.journal() if item["event"] == "phase"],
                         ["identifying", "backing_up", "backed_up", "checking_preimage", "installing",
                          "verifying", "verified", "booting", "usb_detected"])

    def test_different_backup_is_retained_but_blocks_the_writer(self):
        self.backend.read_results["backup-b"] = self.fixture.unit_backup(38)
        with self.assertRaisesRegex(ValueError, "two full backups differ"):
            self.backup()
        self.assert_no_writer_or_boot()
        self.assertEqual((self.destination / "stock-flash-a.bin").read_bytes(), self.fixture.backup)
        self.assertEqual((self.destination / "stock-flash-b.bin").read_bytes(), self.fixture.unit_backup(38))
        self.assertFalse((self.destination / "installation-plan.json").exists())
        self.assertEqual(self.backend.close_count, 1)
        self.assert_terminal()

    def test_changed_third_read_blocks_writer_even_when_only_private_data_changed(self):
        self.backup()
        self.backend.read_results["pre-install"] = self.fixture.unit_backup(39)
        with self.assertRaisesRegex(ValueError, "Flash changed after backup"):
            self.workflow.install()
        self.assert_no_writer_or_boot()
        self.assertFalse((self.destination / "full-before.bin").exists())
        self.assertEqual(self.backend.close_count, 1)
        self.assert_terminal()

    def test_short_third_read_also_blocks_writer(self):
        self.backup()
        self.backend.read_results["pre-install"] = self.fixture.backup[:-1]
        with self.assertRaises(ValueError):
            self.workflow.install()
        self.assert_no_writer_or_boot()
        self.assert_terminal()

    def test_outside_application_damage_is_saved_as_evidence_and_blocks_boot(self):
        self.backup()
        def damaged(raw):
            return raw[:0xFF000] + bytes([raw[0xFF000] ^ 1]) + raw[0xFF001:]
        self.backend.read_results["full-after"] = damaged
        with self.assertRaisesRegex(ValueError, "preserved region: key_mac"):
            self.workflow.install()
        self.assertEqual(len(self.backend.installations), 1)
        self.assertEqual((self.destination / "full-after.bin").read_bytes(), damaged(self.backend.flash))
        self.assertFalse((self.destination / "verification.json").exists())
        self.assertEqual(self.backend.boot_requests, [])
        self.assert_terminal()

    def test_failed_or_short_final_read_never_permits_boot(self):
        self.backup()
        self.backend.read_results["full-after"] = lambda raw: raw[:-1]
        with self.assertRaisesRegex(ValueError, "Final full 1 MiB"):
            self.workflow.install()
        self.assertEqual(len(self.backend.installations), 1)
        self.assertEqual(len((self.destination / "full-after.bin").read_bytes()), core.CAPACITY - 1)
        self.assertEqual(self.backend.boot_requests, [])
        self.assert_terminal()

    def test_uncertain_write_failure_is_terminal_without_rollback_or_reset(self):
        self.backup()
        self.backend.write_error = OSError("simulated lost program reply")
        with self.assertRaisesRegex(OSError, "lost program reply"):
            self.workflow.install()
        self.assertEqual(len(self.backend.installations), 1)
        self.assertNotEqual(self.backend.flash, self.backend.original)
        self.assertEqual(self.backend.boot_requests, [])
        self.assertEqual([x[1] for x in self.backend.calls if x[0] == "read_full"],
                         ["backup-a", "backup-b", "pre-install"])
        self.assertFalse((self.destination / "verification.json").exists())
        failure = self.journal()[-1]
        self.assertEqual(failure["event"], "session_failed")
        self.assertEqual(failure["failed_phase"], "installing")
        self.assertIs(failure["automatic_reset"], False)
        self.assertIs(failure["automatic_retry"], False)
        self.assert_terminal()

    def test_boot_is_unavailable_until_complete_verification(self):
        with self.assertRaises(ValueError):
            self.workflow.boot()
        self.assertEqual(self.workflow.phase, "created")
        self.backup()
        with self.assertRaises(ValueError):
            self.workflow.boot()
        self.assertEqual(self.workflow.phase, "backed_up")
        self.assertEqual(self.backend.boot_requests, [])
        self.workflow.install()
        self.workflow.boot()
        with self.assertRaises(ValueError):
            self.workflow.boot()
        self.assertEqual(self.backend.boot_requests, ["hyperrig"])

    def test_cancel_to_stock_requires_verified_unchanged_backups_and_no_writer(self):
        with self.assertRaises(ValueError):
            self.workflow.cancel_to_stock()
        self.assertEqual(self.backend.calls, [])
        self.backup()
        result = self.workflow.cancel_to_stock()
        self.assertEqual(self.backend.installations, [])
        self.assertEqual(self.backend.boot_requests, ["stock"])
        self.assertEqual(self.backend.flash, self.backend.original)
        self.assertEqual(self.workflow.phase, "stock_usb_detected")
        self.assertEqual(json.loads((self.destination / "stock-return-observation.json").read_text()), result)
        self.assertEqual([x[1] for x in self.backend.calls if x[0] == "read_full"],
                         ["backup-a", "backup-b", "cancel-check"])
        with self.assertRaises(ValueError):
            self.workflow.install()
        self.assertEqual(self.backend.installations, [])

    def test_cancel_changed_stock_blocks_reset(self):
        self.backup()
        self.backend.read_results["cancel-check"] = self.fixture.unit_backup(40)
        with self.assertRaisesRegex(ValueError, "automatic boot is blocked"):
            self.workflow.cancel_to_stock()
        self.assert_no_writer_or_boot()
        self.assert_terminal()

    def test_cancel_is_not_a_rollback_after_installation(self):
        self.backup()
        self.workflow.install()
        prior_calls = list(self.backend.calls)
        with self.assertRaises(ValueError):
            self.workflow.cancel_to_stock()
        self.assertEqual(self.backend.calls, prior_calls)
        self.assertEqual(self.backend.boot_requests, [])
        self.assertEqual(self.workflow.phase, "verified")

    def test_failure_persisting_first_backup_blocks_second_read_and_writer(self):
        with patch.object(self.workflow.store, "save_bytes", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.backup()
        self.assertEqual([x[1] for x in self.backend.calls if x[0] == "read_full"], ["backup-a"])
        self.assert_no_writer_or_boot()
        self.assert_terminal()

    def test_failure_persisting_plan_keeps_backups_but_blocks_writer(self):
        with patch.object(self.workflow.store, "save_json", side_effect=OSError("plan fsync failed")):
            with self.assertRaisesRegex(OSError, "plan fsync failed"):
                self.backup()
        self.assertTrue((self.destination / "stock-flash-a.bin").exists())
        self.assertTrue((self.destination / "stock-flash-b.bin").exists())
        self.assert_no_writer_or_boot()
        self.assert_terminal()

    def test_failure_persisting_fresh_preimage_blocks_writer(self):
        self.backup()
        with patch.object(self.workflow.store, "save_bytes", side_effect=OSError("preimage fsync failed")):
            with self.assertRaisesRegex(OSError, "preimage fsync failed"):
                self.workflow.install()
        self.assert_no_writer_or_boot()
        self.assert_terminal()

    def test_journal_failure_before_installing_blocks_writer(self):
        self.backup()
        original = self.workflow.store.event
        def failing_event(event, **fields):
            if event == "phase" and fields.get("phase") == "installing":
                raise OSError("journal fsync failed")
            return original(event, **fields)
        with patch.object(self.workflow.store, "event", side_effect=failing_event):
            with self.assertRaisesRegex(OSError, "journal fsync failed"):
                self.workflow.install()
        self.assert_no_writer_or_boot()
        self.assertTrue((self.destination / "full-before.bin").exists())
        self.assert_terminal()

    def test_failure_persisting_verification_does_not_allow_boot(self):
        self.backup()
        with patch.object(self.workflow.store, "save_json", side_effect=OSError("verification fsync failed")):
            with self.assertRaisesRegex(OSError, "verification fsync failed"):
                self.workflow.install()
        self.assertEqual(self.backend.flash, self.workflow.prepared.expected_full)
        self.assertEqual(len(self.backend.installations), 1)
        self.assertEqual(self.backend.boot_requests, [])
        self.assert_terminal()

    def test_boot_failure_is_not_retried_and_ends_session(self):
        self.backup()
        self.workflow.install()
        self.backend.boot_error = OSError("reset outcome unknown")
        with self.assertRaisesRegex(OSError, "reset outcome unknown"):
            self.workflow.boot()
        self.assertEqual(self.backend.boot_requests, ["hyperrig"])
        self.assert_terminal()

    def test_busy_action_rejects_reentry_and_close(self):
        def during_read(stage):
            if stage != "backup-a":
                return
            before = list(self.backend.calls)
            with self.assertRaisesRegex(ValueError, "already running"):
                self.workflow.boot()
            with self.assertRaisesRegex(ValueError, "Wait for the current operation"):
                self.workflow.close()
            self.assertEqual(self.backend.calls, before)
        self.backend.before_read = during_read
        self.backup()
        self.assertEqual(self.workflow.phase, "backed_up")
        self.assert_no_writer_or_boot()

    def test_close_holds_action_lock_until_backend_and_store_cleanup_complete(self):
        self.backup()
        cleanup = []
        backend_close, store_close = self.backend.close, self.workflow.store.close

        def close_backend():
            self.assertTrue(self.workflow._busy.locked())
            self.assertTrue(self.workflow._closed)
            cleanup.append("backend")
            with self.assertRaisesRegex(ValueError, "already running"):
                self.workflow.install()
            backend_close()

        def close_store():
            self.assertTrue(self.workflow._busy.locked())
            self.assertEqual(cleanup, ["backend"])
            cleanup.append("store")
            with self.assertRaisesRegex(ValueError, "already running"):
                self.workflow.cancel_to_stock()
            store_close()

        with patch.object(self.backend, "close", side_effect=close_backend) as bc, \
             patch.object(self.workflow.store, "close", side_effect=close_store) as sc:
            self.workflow.close()
            self.workflow.close()
            bc.assert_called_once()
            sc.assert_called_once()
        self.assertEqual(cleanup, ["backend", "store"])
        self.assertFalse(self.workflow._busy.locked())
        self.assert_no_writer_or_boot()

    def test_closed_session_rejects_every_action_without_backend_reuse(self):
        self.backup()
        self.workflow.close()
        calls = list(self.backend.calls)
        for action in (self.workflow.install, self.workflow.boot, self.workflow.cancel_to_stock,
                       lambda: self.workflow.backup({"id": "another-attempt"})):
            with self.assertRaisesRegex(ValueError, "session is closed"):
                action()
        self.assertEqual(self.backend.calls, calls)
        self.assertEqual((self.destination / "stock-flash-a.bin").read_bytes(), self.backend.original)
        self.assertEqual((self.destination / "stock-flash-b.bin").read_bytes(), self.backend.original)
        self.assert_no_writer_or_boot()

    def test_existing_session_directory_is_never_overwritten(self):
        original_journal = (self.destination / "journal.jsonl").read_bytes()
        other_backend = FakeBackend(self.fixture.backup)
        with self.assertRaises(FileExistsError):
            service.InstallWorkflow(self.release, other_backend, self.destination)
        self.assertEqual((self.destination / "journal.jsonl").read_bytes(), original_journal)
        self.assertEqual(other_backend.calls, [])


if __name__ == "__main__":
    unittest.main()
