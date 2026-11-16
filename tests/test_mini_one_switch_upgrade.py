"""Offline upgrade checks: public code, synthetic unit data, fake transports."""
from contextlib import ExitStack
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from hyperrig.installer import core, upgrade, upgrade_windows
from tests.test_mini_installer_service import FakeBackend
from tests import test_portable_mini_installer_core as fixture_module
from tests.test_mini_installer_windows import Clock, Store, Transport, Pause
from tools import upgrade_mini_one_switch as runner


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_module.PortableCoreTests.setUpClass()

    def setUp(self):
        fixture = self.fixture = fixture_module.PortableCoreTests("test_public_stock_pins_and_release_ELF_validation")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.use_one_switch_release()
        self.release = core.load_release(fixture.bundle)
        self.before = self.unit(37)

    def unit(self, seed):
        raw = self.fixture.unit_backup(seed)
        return raw[:core.APP_START] + self.fixture.payloads["firmware"] + raw[core.APP_END:]

    def plan(self, raw=None):
        raw = self.before if raw is None else raw
        return upgrade.plan_upgrade(self.release, raw, raw, jedec_hex=core.JEDEC_HEX)

    def workflow(self):
        backend = FakeBackend(self.before)
        backend.enter_hyperrig_rom = Mock()
        output = Path(self.fixture.temp.name) / "upgrade"
        workflow = upgrade.UpgradeWorkflow(self.release, backend, output)
        self.addCleanup(workflow.close)
        return workflow, backend, output

    def test_two_sectors_and_header_page_last_preserve_distinct_current_units(self):
        a, b = self.plan(), self.plan(self.unit(98))
        self.assertNotEqual(a.installation.plan_sha256, b.installation.plan_sha256)
        for plan in (a, b):
            self.assertEqual(plan.installation.sector_order, (0x7B000, 0x4000))
            self.assertEqual(plan.record["sectors"][-1]["page_order"][-1], 0x4000)
            self.assertEqual(plan.expected_full[:core.APP_START], plan.backup[:core.APP_START])
            self.assertEqual(plan.expected_full[core.APP_END:], plan.backup[core.APP_END:])
            result = upgrade.validate_completed(plan, plan.expected_full)
            self.assertTrue(result["verified"])
            self.assertFalse(result["boot_verified"])
            self.assertFalse(result["audio_verified"])
            self.assertFalse(result["cold_boot_recovery_verified"])

    def test_wrong_or_incomplete_backup_is_rejected(self):
        wrong_app = self.before[:0x5000] + bytes([self.before[0x5000] ^ 1]) + self.before[0x5001:]
        wrong_spl = bytes([self.before[0] ^ 1]) + self.before[1:]
        for bad in (self.before[:-1], bytearray(self.before), wrong_app, wrong_spl, self.fixture.backup):
            with self.subTest(kind=type(bad), length=len(bad)), self.assertRaises(ValueError):
                self.plan(bad)
        with self.assertRaisesRegex(ValueError, "backups differ"):
            upgrade.plan_upgrade(self.release, self.before, self.unit(38), jedec_hex=core.JEDEC_HEX)
        with self.assertRaisesRegex(ValueError, "JEDEC"):
            upgrade.plan_upgrade(self.release, self.before, self.before, jedec_hex="ffffff")

    def test_tampered_release_or_plan_never_validates(self):
        plan = self.plan()
        bad_release = replace(self.release, firmware=self.release.firmware[:-1] + b"x")
        with self.assertRaises(ValueError):
            upgrade.plan_upgrade(bad_release, self.before, self.before, jedec_hex=core.JEDEC_HEX)
        for bad in (replace(plan, expected_full=self.before), replace(plan, _record_raw=b"{}"),
                    replace(plan, installation=replace(plan.installation, plan_sha256="0" * 64))):
            with self.assertRaises(ValueError):
                upgrade.validate_completed(bad, plan.expected_full)

    def test_damage_to_every_preserved_region_or_application_blocks_completion(self):
        plan = self.plan()
        for _, start, _ in core.PRESERVED_REGIONS:
            after = plan.expected_full
            after = after[:start] + bytes([after[start] ^ 1]) + after[start + 1:]
            with self.subTest(start=start), self.assertRaisesRegex(ValueError, "preserved region"):
                upgrade.validate_completed(plan, after)
        with self.assertRaises(ValueError):
            upgrade.validate_completed(plan, self.before)
        with self.assertRaises(ValueError):
            upgrade.validate_completed(plan, plan.expected_full[:-1])

    def test_workflow_retains_all_reads_and_requires_separate_verified_boot(self):
        workflow, backend, output = self.workflow()
        with self.assertRaises(ValueError):
            workflow.boot()
        plan = workflow.backup("COM3")
        backend.enter_hyperrig_rom.assert_called_once_with("COM3", self.release, workflow.store)
        self.assertEqual(backend.installations, [])
        self.assertEqual((output / "v3-flash-a.bin").read_bytes(), self.before)
        self.assertEqual((output / "v3-flash-b.bin").read_bytes(), self.before)
        with self.assertRaises(ValueError):
            workflow.boot()
        result = workflow.install()
        self.assertEqual(len(backend.installations), 1)
        self.assertEqual(backend.boot_requests, [])
        self.assertEqual(result["plan_sha256"], plan["plan_sha256"])
        self.assertEqual((output / "full-before.bin").read_bytes(), self.before)
        self.assertEqual((output / "full-after.bin").read_bytes(), backend.flash)
        workflow.boot()
        self.assertEqual(backend.boot_requests, ["hyperrig"])

    def test_mismatched_second_backup_blocks_writer(self):
        workflow, backend, _ = self.workflow()
        backend.read_results["backup-b"] = self.unit(38)
        with self.assertRaisesRegex(ValueError, "backups differ"):
            workflow.backup("COM3")
        self.assertEqual(backend.installations, [])
        self.assertEqual(backend.boot_requests, [])
        self.assertEqual(workflow.phase, "failed")

    def test_changed_private_data_before_install_blocks_writer(self):
        workflow, backend, output = self.workflow()
        workflow.backup("COM3")
        backend.read_results["pre-install"] = self.unit(38)
        with self.assertRaisesRegex(ValueError, "Flash changed"):
            workflow.install()
        self.assertEqual((output / "full-before.bin").read_bytes(), self.unit(38))
        self.assertEqual(backend.installations, [])
        self.assertEqual(backend.boot_requests, [])

    def test_unknown_mutation_result_is_terminal_without_boot_or_repetition(self):
        workflow, backend, _ = self.workflow()
        workflow.backup("COM3")
        backend.write_error = OSError("lost page response")
        with self.assertRaises(OSError):
            workflow.install()
        for action in (workflow.install, workflow.boot, workflow.cancel_to_stock):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(len(backend.installations), 1)
        self.assertEqual(backend.boot_requests, [])

    def test_incorrect_full_readback_is_retained_and_blocks_boot(self):
        workflow, backend, output = self.workflow()
        workflow.backup("COM3")
        backend.read_results["full-after"] = self.before
        with self.assertRaises(ValueError):
            workflow.install()
        self.assertEqual((output / "full-after.bin").read_bytes(), self.before)
        with self.assertRaises(ValueError):
            workflow.boot()
        self.assertEqual(backend.boot_requests, [])

    def test_stage_requests_recompute_backups_and_final_bytes(self):
        workflow, backend, output = self.workflow()
        prepared = {"bundle": str(self.release.root), "test": "offline"}
        workflow.store.save_json("preflight.json", prepared)
        workflow.backup("COM3")
        workflow.store.save_json("status.json", {"phase": "backed_up"})
        with patch.object(runner, "session_path", lambda p: Path(p)), \
             patch.object(runner, "prepare", return_value=(self.release, prepared)):
            with self.assertRaises(ValueError):
                runner.request_stage(output, "boot")
            runner.request_stage(output, "install")
            with self.assertRaises(ValueError):
                runner.request_stage(output, "install")
            runner.wait_request(workflow, "install.request", {"plan_sha256": workflow.prepared.installation.plan_sha256})
            result = workflow.install()
            (output / "status.json").write_text(json.dumps({"phase": "verified"}))
            runner.request_stage(output, "boot")
            runner.wait_request(workflow, "boot.request", {"full_after_sha256": result["full_after_sha256"]})
        self.assertEqual(backend.boot_requests, [])

    def test_mismatched_request_and_stop_never_advance_worker(self):
        workflow, backend, output = self.workflow()
        workflow.store.save_json("install.request", {"plan_sha256": "wrong"})
        with self.assertRaisesRegex(ValueError, "binding differs"):
            runner.wait_request(workflow, "install.request", {"plan_sha256": "right"})
        (output / "stop.request").touch()
        with self.assertRaisesRegex(ValueError, "Stopped"):
            runner.wait_request(workflow, "boot.request", {})
        self.assertEqual(backend.installations, [])
        self.assertEqual(backend.boot_requests, [])


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.clock, self.store = Clock(), Store()
        self.backend = upgrade_windows.UpgradeWindowsBackend()
        self.addCleanup(self.backend.close)
        self.release = SimpleNamespace(manifest={"firmware": {"sha256": core.ONE_SWITCH_FIRMWARE_SHA256}})
        self.port = [{"device": "COM3", "vid": 0x3654, "pid": 0x5155}]
        self.transport = Mock()
        self.transport.write.return_value = 6
        self.attestation = SimpleNamespace(
            last_arrival_filetime=int((self.clock.now() + 11644473600) * 10_000_000),
            summary=lambda: {"arrival": "fresh"})
        self.patch(upgrade_windows.windows, "is_admin", Mock(return_value=True))
        self.patch(upgrade_windows.windows, "stock_devices", Mock(return_value=[]))
        self.ports = self.patch(upgrade_windows.windows, "hyperrig_ports", Mock(side_effect=[self.port, self.port, []]))
        self.roms = self.patch(upgrade_windows.windows, "discover_windows_rom_disks", Mock(side_effect=[[], [], [{"path": "ROM"}]]))
        self.patch(upgrade_windows.windows, "RomDiskAttestation", SimpleNamespace(from_discovery=lambda _: self.attestation))
        self.patch(upgrade_windows.windows, "QuietBufferedRomTransport", Transport)
        self.patch(upgrade_windows.windows, "MiniMediaChangePause", Pause)
        self.patch(self.backend, "_claim_host_session", Mock())
        self.patch(upgrade_windows.handshake.host.HostOpenTransport, "open", Mock(return_value=self.transport))
        self.identify = self.patch(upgrade_windows.handshake, "identify", Mock(
            return_value=(None, {"lines": [upgrade_windows.PONG]}, [{}])))
        self.patch(upgrade_windows.time, "time", self.clock.now)
        self.patch(upgrade_windows.time, "monotonic", self.clock.now)
        self.patch(upgrade_windows.time, "sleep", self.clock.sleep)
        Transport.created = []

    def patch(self, owner, name, value):
        return self.stack.enter_context(patch.object(owner, name, value))

    def enter(self):
        return self.backend.enter_hyperrig_rom("COM3", self.release, self.store)

    def test_exact_identity_single_command_and_fresh_ROM_attestation(self):
        self.enter()
        self.transport.write.assert_called_once_with(b"UBOOT\n")
        self.transport.close.assert_called_once()
        self.assertIs(self.backend.attestation, self.attestation)
        self.assertTrue(Transport.created[0].closed)
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.enter()
        self.assertEqual(self.transport.write.call_count, 1)

    def test_wrong_identity_closes_serial_without_UBOOT(self):
        self.identify.return_value = (None, {"lines": ["PONG tankg_fw"]}, [{}])
        with self.assertRaisesRegex(ValueError, "PONG"):
            self.enter()
        self.transport.write.assert_not_called()
        self.transport.close.assert_called_once()
        self.assertFalse(Transport.created)

    def test_journal_failure_prevents_UBOOT(self):
        self.store.fail_event = "hyperrig_to_rom_intent"
        with self.assertRaises(OSError):
            self.enter()
        self.transport.write.assert_not_called()
        self.transport.close.assert_called_once()

    def test_changed_selection_prevents_UBOOT(self):
        self.ports.side_effect = [self.port, []]
        with self.assertRaisesRegex(ValueError, "selection changed"):
            self.enter()
        self.transport.write.assert_not_called()

    def test_short_write_stops_without_ROM_open_or_retry(self):
        self.transport.write.return_value = 3
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            self.enter()
        self.transport.write.assert_called_once()
        self.assertFalse(Transport.created)

    def test_write_detach_error_requires_fresh_ROM_instead_of_resending(self):
        self.transport.write.side_effect = OSError("detached during reset")
        self.enter()
        self.transport.write.assert_called_once()
        self.assertIs(self.backend.attestation, self.attestation)

    def test_old_arrival_cannot_start_reader(self):
        self.attestation.last_arrival_filetime -= 300_000_000
        with self.assertRaisesRegex(ValueError, "predates"):
            self.enter()
        self.assertIsNone(self.backend.mcn)
        self.assertEqual(Transport.created[0].calls, [])

    def test_missing_ROM_is_bounded_and_does_not_resend(self):
        self.roms.side_effect = None
        self.roms.return_value = []
        before = self.clock.now()
        with self.assertRaisesRegex(ValueError, "not observed"):
            self.enter()
        self.assertLess(self.clock.now() - before, 47)
        self.transport.write.assert_called_once()
        self.assertFalse(Transport.created)


if __name__ == "__main__":
    unittest.main()
