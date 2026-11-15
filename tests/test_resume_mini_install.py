"""New plans from reviewed partial snapshots: local files/fake NOR only."""
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import resume_mini_install as resume
from tools import install_mini_app as install
from tests.test_mini_app_install import FakeOperational

ROOT = Path(__file__).resolve().parents[1]


class ResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = install.prepare_installation()
        cls.stock = (ROOT / resume.BACKUP_PATH).read_bytes()
        assert resume.sha(cls.stock) == resume.BACKUP_SHA
        cls.complete = cls.stock[:0x4000] + cls.base.candidate + cls.stock[0x82000:]
        current = bytearray(cls.stock)
        current[0x5000:0x5A00] = cls.complete[0x5000:0x5A00]
        current[0x5A00:0x6000] = b"\xff" * 0x600
        cls.partial = bytes(current)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mini-resume-test-", dir=ROOT / "build")
        self.directory = Path(self.tmp.name).resolve()
        self.assertTrue(self.directory.is_relative_to((ROOT / "build").resolve()))
        self.addCleanup(self.tmp.cleanup)
        self.path = self.directory / "partial.bin"

    def prepare(self, current=None, modified=None):
        current = self.partial if current is None else current
        modified = resume.modified_sectors(current, self.stock) if modified is None else modified
        self.path.write_bytes(current)
        return resume.prepare_resume(self.path, expected_partial_sha256=resume.sha(current),
                                     expected_modified_sectors=modified)

    def session(self, plan):
        fake = FakeOperational(plan.installation)
        fake.flash = bytearray(plan.full_preimage)
        fake.original = bytes(fake.flash)
        journal = []
        session = install.MiniAppInstallerSession(fake, plan.installation,
            journal=journal.append, known_free_slot=True)
        with patch("time.sleep"):
            session.upload_and_start(plan.installation.image, expected_sha256=plan.installation.image_sha256)
        session.initialize_spi()
        session.verify_complete_preimage()
        return fake, session, journal

    def test_first_incident_shape_and_current_sector_crc(self):
        plan = self.prepare(modified=(0x5000,))
        self.assertEqual(plan.installation.preimage, self.partial[0x4000:0x82000])
        self.assertEqual(plan.installation.candidate, self.base.candidate)
        self.assertEqual(plan.installation.sector_order, self.base.sector_order)
        self.assertNotEqual(plan.installation.plan_sha256, self.base.plan_sha256)
        self.assertEqual(plan.installation.fresh_full_read_sha256, resume.sha(self.partial))
        rows = plan.plan()["partial_sector_pages"][0]["pages"]
        self.assertTrue(all(r["matches_candidate"] for r in rows[:10]))
        self.assertTrue(all(r["all_FF"] for r in rows[10:]))
        sector = next(r for r in plan.plan()["sectors"] if r["physical_address"] == 0x5000)
        self.assertEqual(sector["preimage_crc32"], install.crc(self.partial[0x5000:0x6000]))
        self.assertNotEqual(sector["preimage_crc32"], install.crc(self.stock[0x5000:0x6000]))
        self.assertFalse(plan.plan()["previous_session_tokens_or_bitmap_reused"])

    def test_reviewed_hash_and_exact_modified_sector_list_are_required(self):
        self.path.write_bytes(self.partial)
        for expected, modified in (("0" * 64, (0x5000,)), (resume.sha(self.partial), ()),
                                   (resume.sha(self.partial), (0x5000, 0x6000))):
            with self.subTest(modified=modified), self.assertRaises(ValueError):
                resume.prepare_resume(self.path, expected_partial_sha256=expected,
                                      expected_modified_sectors=modified)

    def test_malformed_modified_sets_rejected(self):
        self.path.write_bytes(self.partial)
        for modified in ([0x5000], (0x5000, 0x5000), (0x6000, 0x5000), (0x3000,),
                         (0x82000,), (0x5100,), (True,)):
            with self.subTest(modified=modified), self.assertRaises(ValueError):
                resume.prepare_resume(self.path, expected_partial_sha256=resume.sha(self.partial),
                                      expected_modified_sectors=modified)

    def test_each_external_region_must_still_equal_backup(self):
        for address in (0, 0x82000, 0xB7000, 0xBCF00, 0xBE000, 0xBF000, 0xFF000):
            current = bytearray(self.partial)
            current[address] ^= 1
            self.path.write_bytes(current)
            with self.subTest(address=address), self.assertRaisesRegex(ValueError, "external regions changed"):
                resume.prepare_resume(self.path, expected_partial_sha256=resume.sha(current),
                                      expected_modified_sectors=(0x5000,))

    def test_snapshot_and_plan_are_immutable_after_file_change(self):
        plan = self.prepare()
        self.path.write_bytes(self.stock)
        self.assertEqual(plan.full_preimage, self.partial)
        with self.assertRaises(FrozenInstanceError):
            plan.full_preimage = self.stock
        detached = plan.plan()
        detached["sector_order"].clear()
        self.assertEqual(len(plan.plan()["sector_order"]), 126)
        path = self.directory / "new-plan.json"
        plan.retain_plan(path)
        self.assertEqual(path.read_bytes(), plan.plan_bytes)
        with self.assertRaises(FileExistsError):
            plan.retain_plan(path)

    def test_already_complete_has_zero_mutations_and_keeps_target_hash(self):
        plan = self.prepare(self.complete)
        self.assertEqual(plan.installation.sector_order, ())
        self.assertEqual(plan.expected_full_readback(), self.complete)
        fake, session, _ = self.session(plan)
        result = session.install_application()
        self.assertTrue(result["application_verified"])
        self.assertFalse(fake.erase_addresses or fake.program_addresses)
        self.assertTrue(resume.validate_completed_full(plan, bytes(fake.flash))["external_regions_unchanged"])

    def test_new_session_erases_current_sector_not_old_page_sequence(self):
        plan = self.prepare()
        fake, session, journal = self.session(plan)
        fake.fail_after = (0xFC7D, 1)
        with self.assertRaises(TimeoutError):
            session.install_application()
        self.assertTrue(session.failed and session.mutation_completion_unknown)
        self.assertEqual(fake.erase_addresses, [0x5000])
        self.assertEqual(fake.program_addresses, [0x5000])
        # A fresh writer starts token1/sequence1; the old token1/sequence22
        # cannot be replayed because the current sector was freshly compared.
        arm = next(e for e in journal if e["event"] == "command_intent" and e.get("opcode") == "fc7a")
        self.assertIn(f"{install.crc(self.partial[0x5000:0x6000]):08x}", arm["cdb_hex"])
        before = len(fake.commands)
        with self.assertRaises(ValueError):
            session.install_application()
        self.assertEqual(len(fake.commands), before)
        self.assertEqual(fake.commands.count(0xFB08), 1)

    def test_complete_remaining_sector_restores_exact_candidate_leaves_rom(self):
        current = bytearray(self.complete)
        current[0x5000] ^= 1
        plan = self.prepare(bytes(current))
        self.assertEqual(plan.installation.sector_order, (0x5000,))
        fake, session, _ = self.session(plan)
        result = session.install_application()
        self.assertEqual(bytes(fake.flash), self.complete)
        self.assertEqual(fake.erase_addresses, [0x5000])
        self.assertEqual(fake.program_addresses, list(range(0x5000, 0x6000, 256)))
        self.assertTrue(result["rom_session_remains_active"])
        self.assertFalse(result["application_boot_attempted"])
        verified = resume.validate_completed_full(plan, bytes(fake.flash))
        self.assertEqual(verified["candidate_sha256"], resume.CANDIDATE_SHA)

    def test_full_postread_rejects_application_or_external_difference(self):
        plan = self.prepare()
        for address in (0, 0x4000, 0x5900, 0x81000, 0x82000, 0xBF000, 0xFF000):
            readback = bytearray(plan.expected_full_readback())
            readback[address] ^= 1
            with self.subTest(address=address), self.assertRaises(ValueError):
                resume.validate_completed_full(plan, bytes(readback))

    def test_default_cli_never_loads_inputs_or_constructs_transport(self):
        out = io.StringIO()
        with patch.object(install, "prepare_installation", side_effect=AssertionError("load")), \
                patch.object(install, "WindowsAppWriterTransport", side_effect=AssertionError("device")), \
                redirect_stdout(out):
            result = resume.main([])
        self.assertFalse(result["device_io"] or result["automatic_resume"] or result["CLI_executes_installation"])
        self.assertEqual(result, json.loads(out.getvalue()))


if __name__ == "__main__":
    unittest.main()
