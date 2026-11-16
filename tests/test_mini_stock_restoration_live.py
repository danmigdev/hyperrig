"""Restoration orchestration with synthetic current data and no device I/O."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from hyperrig.installer import core, restoration
from tests.test_mini_installer_service import FakeBackend
from tools import restore_mini_stock_live as runner

ROOT = Path(__file__).resolve().parents[1]


class RestorationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release, cls.stock, cls.preflight = runner.prepare(runner.stages.DEFAULT_BUNDLE)
        raw = bytearray(cls.stock[:core.APP_START] + cls.release.firmware + cls.stock[core.APP_END:])
        raw[0xBF001] ^= 0x5A
        cls.current = bytes(raw)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="stock-restore-test-", dir=ROOT / "build")
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "session"
        self.backend = FakeBackend(self.current)
        self.backend.enter_hyperrig_rom = Mock()
        self.workflow = restoration.RestorationWorkflow(self.release, self.backend, self.output, self.stock)
        self.addCleanup(self.workflow.close)

    def plan(self, first=None, second=None, stock=None):
        first = self.current if first is None else first
        return restoration.prepare_restoration(self.release, first, first if second is None else second,
                                                self.stock if stock is None else stock, jedec_hex=core.JEDEC_HEX)

    def test_sealed_payload_restores_stock_application_and_preserves_current_data(self):
        with patch.object(restoration.frozen.installer, "prepare_installation",
                          side_effect=AssertionError("historical source pins must not be bypassed")):
            plan = self.plan()
        self.assertEqual(plan.installation.purpose, "restore-stock")
        self.assertEqual(core._sha(plan.installation.candidate), core.STOCK_APP_SHA256)
        self.assertEqual(plan.installation.sector_order[-1], core.APP_START)
        expected = plan.expected_full_readback()
        self.assertEqual(expected[:core.APP_START], self.current[:core.APP_START])
        self.assertEqual(expected[core.APP_END:], self.current[core.APP_END:])
        self.assertNotEqual(expected, self.stock)
        result = restoration.frozen.validate_restored_full(plan, expected)
        self.assertTrue(result["stock_application_verified"])
        self.assertFalse(result["whole_NOR_equals_historical_stock_backup"])
        self.assertFalse(result["stock_boot_verified"])

    def test_changed_or_foreign_backup_is_rejected(self):
        for address in (0x10, 0xFF100):
            raw = bytearray(self.current)
            raw[address] ^= 1
            with self.subTest(address=address), self.assertRaisesRegex(ValueError, "original unit backup"):
                self.plan(bytes(raw))
        with self.assertRaises(ValueError):
            self.plan(stock=self.stock[:-1])

    def test_wrong_application_and_incomplete_or_unequal_reads_are_rejected(self):
        other = self.current[:0xBF000] + bytes([self.current[0xBF000] ^ 1]) + self.current[0xBF001:]
        for first, second in ((self.stock, self.stock), (self.current[:-1], self.current),
                              (bytearray(self.current), self.current), (self.current, other)):
            with self.subTest(length=len(first)), self.assertRaises(ValueError):
                self.plan(first, second)

    def test_full_workflow_saves_fresh_reads_and_boots_only_stock_after_verification(self):
        with self.assertRaises(ValueError):
            self.workflow.boot()
        self.workflow.backup("COM3")
        self.backend.enter_hyperrig_rom.assert_called_once()
        self.assertEqual(self.backend.installations, [])
        self.assertEqual((self.output / "hyperrig-flash-a.bin").read_bytes(), self.current)
        self.assertEqual((self.output / "hyperrig-flash-b.bin").read_bytes(), self.current)
        with self.assertRaises(ValueError):
            self.workflow.boot()
        result = self.workflow.install()
        self.assertTrue(result["stock_application_verified"])
        self.assertEqual(self.backend.boot_requests, [])
        self.assertEqual(self.backend.installations[0].purpose, "restore-stock")
        self.workflow.boot()
        self.assertEqual(self.backend.boot_requests, ["stock"])
        self.assertEqual(self.workflow.phase, "stock_usb_detected")

    def test_second_read_change_prevents_restoration(self):
        self.backend.read_results["backup-b"] = self.current[:-1] + bytes([self.current[-1] ^ 1])
        with self.assertRaises(ValueError):
            self.workflow.backup("COM3")
        self.assertEqual(self.backend.installations, [])
        self.assertEqual(self.backend.boot_requests, [])
        self.assertEqual(self.workflow.phase, "failed")

    def test_changed_third_read_never_writes_and_is_retained(self):
        self.workflow.backup("COM3")
        self.backend.read_results["pre-install"] = self.stock
        with self.assertRaisesRegex(ValueError, "Flash changed"):
            self.workflow.install()
        self.assertEqual((self.output / "full-before.bin").read_bytes(), self.stock)
        self.assertEqual(self.backend.installations, [])
        self.assertEqual(self.backend.boot_requests, [])

    def test_uncertain_program_failure_stops_without_retry_or_reset(self):
        self.workflow.backup("COM3")
        self.backend.write_error = OSError("unknown page result")
        with self.assertRaises(OSError):
            self.workflow.install()
        for action in (self.workflow.install, self.workflow.boot, self.workflow.cancel_to_stock):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(len(self.backend.installations), 1)
        self.assertEqual(self.backend.boot_requests, [])

    def test_wrong_final_application_blocks_stock_boot(self):
        self.workflow.backup("COM3")
        self.backend.read_results["full-after"] = self.current
        with self.assertRaises(ValueError):
            self.workflow.install()
        self.assertEqual((self.output / "full-after.bin").read_bytes(), self.current)
        with self.assertRaises(ValueError):
            self.workflow.boot()
        self.assertEqual(self.backend.boot_requests, [])

    def test_changed_preserved_data_blocks_stock_boot(self):
        self.workflow.backup("COM3")
        self.backend.read_results["full-after"] = self.stock
        with self.assertRaisesRegex(ValueError, "USR"):
            self.workflow.install()
        self.assertEqual(self.backend.boot_requests, [])

    def test_stage_requests_revalidate_saved_reads_and_bind_stock_boot(self):
        self.workflow.store.save_json("preflight.json", self.preflight)
        self.workflow.backup("COM3")
        self.workflow.store.save_json("status.json", {"phase": "backed_up"})
        with self.assertRaises(ValueError):
            runner.request(self.output, "boot")
        request = runner.request(self.output, "restore")
        self.assertEqual(request["binding"]["plan_sha256"], self.workflow.prepared.installation.plan_sha256)
        with self.assertRaises(ValueError):
            runner.request(self.output, "restore")
        result = self.workflow.install()
        (self.output / "status.json").write_text(json.dumps({"phase": "verified"}))
        request = runner.request(self.output, "boot")
        self.assertEqual(request["binding"]["full_after_sha256"], result["full_readback_sha256"])
        self.assertEqual(self.backend.boot_requests, [])

    def test_tampered_saved_plan_cannot_request_a_write(self):
        self.workflow.store.save_json("preflight.json", self.preflight)
        self.workflow.backup("COM3")
        self.workflow.store.save_json("status.json", {"phase": "backed_up"})
        (self.output / "restoration-plan.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "plan changed"):
            runner.request(self.output, "restore")
        self.assertFalse((self.output / "restore.request").exists())


if __name__ == "__main__":
    unittest.main()
