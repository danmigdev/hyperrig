"""Explicit stock restoration: local retained files and fake NOR only."""
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError, replace
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import restore_mini_stock as restore
from tools import install_mini_app as install
from tests.test_mini_app_install import FakeOperational

ROOT = Path(__file__).resolve().parents[1]
SLOT, TAG = 0x01C20000, 0x13579BDF
IMAGE = b"mock operational RAM writer for restoration"


class RestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock_path = ROOT / restore.BACKUP_PATH
        cls.stock = cls.stock_path.read_bytes()
        assert restore.sha(cls.stock) == restore.BACKUP_SHA
        cls.app = cls.stock[0x4000:0x82000]
        candidate = bytes([cls.app[0] ^ 1]) + cls.app[1:]
        cls.base = install.Installation(SLOT, TAG, IMAGE, restore.sha(IMAGE),
            *("1" * 64,) * 3, candidate, cls.app, restore.BACKUP_SHA, (0x4000,))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mini-restore-test-", dir=ROOT / "build")
        self.directory = Path(self.tmp.name).resolve()
        self.assertTrue(self.directory.is_relative_to((ROOT / "build").resolve()))
        self.addCleanup(self.tmp.cleanup)
        self.fresh_path = self.directory / "fresh.bin"

    def prepare(self, current=None, **kwargs):
        current = self.stock if current is None else current
        self.fresh_path.write_bytes(current)
        with patch.object(install, "prepare_installation", return_value=self.base) as verified:
            plan = restore.prepare_stock_restoration(self.fresh_path,
                expected_sha256=restore.sha(current), stock_backup_path=self.stock_path, **kwargs)
        self.assertEqual(verified.call_count, 1)
        return plan

    def altered(self, *addresses):
        data = bytearray(self.stock)
        for address in addresses:
            data[address] ^= 0x5A
        return bytes(data)

    def fake_session(self, current=None, *, preflight=True):
        plan = self.prepare(self.altered(0x418A, 0x5000) if current is None else current)
        fake = FakeOperational(plan.installation)
        fake.flash = bytearray(plan.full_preimage)
        fake.original = bytes(fake.flash)
        journal = []
        session = restore.MiniStockRestorationSession(fake, plan,
            journal=journal.append, known_free_slot=True)
        with patch("time.sleep"):
            session.upload_and_start(IMAGE, expected_sha256=restore.sha(IMAGE))
        session.initialize_spi()
        if preflight:
            session.verify_complete_preimage()
        return plan, fake, session, journal

    def test_already_stock_zero_changes_no_mutations(self):
        plan, fake, session, _ = self.fake_session(self.stock)
        self.assertEqual(plan.installation.sector_order, ())
        result = session.restore_application()
        self.assertTrue(result["stock_application_restored"])
        self.assertFalse(fake.erase_addresses or fake.program_addresses)
        self.assertEqual(bytes(fake.flash), self.stock)
        self.assertFalse(result["external_regions_verified_after_write"])
        verified = restore.validate_restored_full(plan, bytes(fake.flash))
        self.assertTrue(verified["whole_NOR_equals_historical_stock_backup"])
        self.assertFalse(verified["stock_boot_verified"])

    def test_unbootable_header_and_last_sector_are_valid_recovery_preimages(self):
        current = bytearray(self.stock)
        current[0x4000:0x4200] = b"\xff" * 512
        current[0x81000:0x82000] = b"\xff" * 4096
        plan = self.prepare(bytes(current))
        self.assertEqual(plan.installation.sector_order, (0x81000, 0x4000))
        self.assertEqual(plan.installation.preimage[:512], b"\xff" * 512)
        self.assertEqual(plan.installation.candidate, self.app)
        self.assertEqual(plan.plan()["sectors"][0]["program_page_order"][-1], 0x4000)

    def test_completely_unknown_application_can_be_restored_without_parsing_it(self):
        current = self.stock[:0x4000] + b"\x55" * len(self.app) + self.stock[0x82000:]
        plan = self.prepare(current)
        self.assertEqual(len(plan.installation.sector_order), 126)
        self.assertEqual(plan.installation.sector_order[-1], 0x4000)
        self.assertTrue(all(0x4000 <= a <= 0x81000 for a in plan.installation.sector_order))
        self.assertEqual(plan.expected_full_readback(), self.stock)

    def test_vm_btif_usr_and_ota_differences_identified_and_preserved(self):
        current = self.altered(0x5000, 0x82000, 0xB7000, 0xBCF00, 0xBE000, 0xBF000)
        plan = self.prepare(current)
        external = plan.plan()["preserved_regions"]
        self.assertEqual([r["name"] for r in external if r["differs_from_stock_backup"]],
                         ["VM_including_factory_staged_updater", "BTIF", "USR"])
        self.assertTrue(all(not r["write_allowed"] for r in external))
        self.assertTrue(all(r["differs_from_stock_backup"] for r in plan.plan()["factory_OTA_regions"]))
        self.assertEqual(plan.expected_full_readback()[0x82000:], current[0x82000:])
        verified = restore.validate_restored_full(plan, plan.expected_full_readback())
        self.assertTrue(verified["all_external_regions_equal_fresh_preimage"])
        self.assertFalse(verified["whole_NOR_equals_historical_stock_backup"])
        self.assertFalse(verified["historical_presets_restored_claimed"])

    def test_foreign_spl_or_unit_identity_refused_before_artifact_loading(self):
        for address, message in ((0x20, "SPL/configuration"), (0xFF000, "key_mac")):
            current = self.altered(address)
            self.fresh_path.write_bytes(current)
            with self.subTest(address=address), patch.object(install, "prepare_installation") as verified:
                with self.assertRaisesRegex(ValueError, message):
                    restore.prepare_stock_restoration(self.fresh_path, expected_sha256=restore.sha(current))
                verified.assert_not_called()

    def test_fresh_extent_hash_and_stock_backup_are_checked(self):
        for current, digest in ((self.stock[:-1], restore.sha(self.stock[:-1])),
                                (self.stock, "0" * 64), (self.stock, "F" * 64)):
            self.fresh_path.write_bytes(current)
            with self.subTest(length=len(current)), self.assertRaises(ValueError):
                restore.prepare_stock_restoration(self.fresh_path, expected_sha256=digest)
        bad_stock = self.directory / "other-backup.bin"
        bad_stock.write_bytes(self.altered(0x5000))
        self.fresh_path.write_bytes(self.stock)
        with self.assertRaisesRegex(ValueError, "same-unit stock backup"):
            restore.prepare_stock_restoration(self.fresh_path, expected_sha256=restore.BACKUP_SHA,
                                               stock_backup_path=bad_stock)

    def test_operational_reference_must_bind_the_exact_stock_preimage(self):
        self.fresh_path.write_bytes(self.stock)
        bad = replace(self.base, backup_sha256="3" * 64)
        with patch.object(install, "prepare_installation", return_value=bad), \
                self.assertRaisesRegex(ValueError, "another stock preimage"):
            restore.prepare_stock_restoration(self.fresh_path, expected_sha256=restore.BACKUP_SHA)

    def test_plan_and_bytes_are_immutable_and_detached_from_input_file(self):
        plan = self.prepare(self.altered(0x5000))
        original = plan.installation.preimage
        self.fresh_path.write_bytes(self.stock)
        self.assertEqual(plan.installation.preimage, original)
        with self.assertRaises(FrozenInstanceError):
            plan.full_preimage = self.stock
        detached = plan.plan()
        detached["sector_order"].clear()
        self.assertEqual(plan.installation.sector_order, (0x5000,))
        self.assertEqual(plan.plan()["sector_order"], [0x5000])
        self.assertEqual(plan.installation.plan_sha256, restore.sha(plan.plan_bytes))
        self.assertEqual(plan.installation.purpose, "restore-stock")

    def test_plan_retention_is_exact_and_exclusive(self):
        plan = self.prepare()
        path = self.directory / "restoration-plan.json"
        evidence = plan.retain_plan(path)
        self.assertEqual(path.read_bytes(), plan.plan_bytes)
        self.assertEqual(evidence["sha256"], plan.installation.plan_sha256)
        with self.assertRaises(FileExistsError):
            plan.retain_plan(path)

    def test_full_verifier_rejects_app_or_external_changes(self):
        plan = self.prepare(self.altered(0x5000))
        expected = plan.expected_full_readback()
        for address, name in ((0x5000, "application"), (0, "factory_SPL"), (0x82000, "VM"),
                              (0xBE000, "BTIF"), (0xBF000, "USR"), (0xFF000, "key_mac")):
            raw = bytearray(expected)
            raw[address] ^= 1
            with self.subTest(address=address), self.assertRaisesRegex(ValueError, name):
                restore.validate_restored_full(plan, bytes(raw))
        for raw in (expected[:-1], bytearray(expected)):
            with self.assertRaises(ValueError):
                restore.validate_restored_full(plan, raw)

    def test_restore_fake_nor_exact_stock_app_and_current_external_data(self):
        current = self.altered(0x418A, 0x5000, 0x82000, 0xBE000, 0xBF000)
        plan, fake, session, journal = self.fake_session(current)
        self.assertEqual(journal[0]["event"], "stock_restoration_plan")
        result = session.restore_application()
        self.assertEqual(bytes(fake.flash), plan.expected_full_readback())
        self.assertEqual(fake.erase_addresses, [0x5000, 0x4000])
        self.assertEqual(fake.program_addresses[-16:], list(range(0x4100, 0x5000, 256)) + [0x4000])
        self.assertEqual(fake.commands.count(0xFB08), 1)
        self.assertTrue(result["stock_application_restored"] and result["rom_session_remains_active"])
        self.assertFalse(result["application_boot_attempted"] or result["automatic_reset"])
        self.assertFalse(result["historical_presets_restored_claimed"])
        self.assertFalse(restore.validate_restored_full(plan, bytes(fake.flash))["whole_NOR_equals_historical_stock_backup"])
        before = len(fake.commands)
        with self.assertRaises(ValueError):
            session.restore_application()
        with self.assertRaises(ValueError):
            session.start_reset_once()
        self.assertEqual(before, len(fake.commands))

    def test_restoration_requires_fresh_app_comparison_before_mutation(self):
        _, fake, session, _ = self.fake_session(preflight=False)
        with self.assertRaises(ValueError):
            session.restore_application()
        self.assertFalse(fake.erase_addresses or fake.program_addresses)
        fake.flash[0x81000] ^= 1
        with self.assertRaises(ValueError):
            session.verify_complete_preimage()
        self.assertTrue(session.failed)
        self.assertFalse(session.mutation_command_submitted)

    def test_lost_mutation_reply_leaves_rom_and_does_not_retry(self):
        for op in (0xFC7B, 0xFC7D):
            _, fake, session, _ = self.fake_session()
            fake.fail_after = (op, 1)
            with self.subTest(op=op), self.assertRaises(TimeoutError):
                session.restore_application()
            self.assertTrue(session.failed and session.mutation_completion_unknown)
            before = len(fake.commands)
            with self.assertRaises(ValueError):
                session.restore_application()
            self.assertEqual(before, len(fake.commands))
            self.assertEqual(fake.commands.count(0xFB08), 1)
            self.assertEqual(fake.counts[op], 1)

    def test_journal_failure_before_first_restore_command_has_no_nvm_effect(self):
        _, fake, session, _ = self.fake_session()
        def bad_journal(item):
            if item["event"] == "command_intent" and item.get("opcode") == "fc7b":
                raise OSError("journal unavailable")
        session.journal = bad_journal
        with self.assertRaises(OSError):
            session.restore_application()
        self.assertTrue(session.failed)
        self.assertFalse(fake.erase_addresses or fake.program_addresses)
        self.assertFalse(session.mutation_command_submitted)

    def test_final_journal_failure_remains_terminal_after_verified_app(self):
        plan, fake, session, _ = self.fake_session(self.stock)
        def bad_journal(item):
            if item["event"] == "stock_application_verified":
                raise OSError("final journal unavailable")
        session.journal = bad_journal
        with self.assertRaises(OSError):
            session.restore_application()
        self.assertTrue(session.failed and session.image_verified)
        self.assertFalse(session.mutation_completion_unknown)
        before = len(fake.commands)
        with self.assertRaises(ValueError):
            session.restore_application()
        self.assertEqual(before, len(fake.commands))

    def test_cli_default_is_offline_without_enumeration_or_file_reads(self):
        output = io.StringIO()
        with patch.object(install, "prepare_installation", side_effect=AssertionError("unexpected load")), \
                patch.object(install, "WindowsAppWriterTransport", side_effect=AssertionError("unexpected transport")), \
                redirect_stdout(output):
            result = restore.main([])
        self.assertFalse(result["device_io"] or result["CLI_executes_restoration"] or result["enumerated"])
        self.assertEqual(result, json.loads(output.getvalue()))


if __name__ == "__main__":
    unittest.main()
