"""Cold ROM attachment tests with fake PnP, clock, and INQUIRY transports."""
from contextlib import ExitStack
from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from hyperrig.installer import cold_rom
from tests.test_mini_installer_windows import Store, Transport, Pause


class ColdRomTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.now = 1_800_000_000.0
        self.observed = {"path": "fake-ROM"}
        self.evidence = {"requested_utc": datetime.fromtimestamp(self.now - 10, timezone.utc).isoformat(),
                         "user_acknowledged_sequence": True, "hyperrig_ports": [], "stock_devices": [],
                         "rom_disks": [self.observed]}
        self.backend = cold_rom.ColdRomBackend(self.evidence)
        self.addCleanup(self.backend.close)
        self.store = Store()
        self.attestation = SimpleNamespace(last_arrival_filetime=int((self.now + 11644473600) * 10_000_000),
                                           summary=lambda: {"arrival": "fresh"})
        self.patch(cold_rom.time, "time", lambda: self.now)
        self.patch(cold_rom.windows, "is_admin", lambda: True)
        self.apps = self.patch(cold_rom.windows, "hyperrig_ports", Mock(return_value=[]))
        self.patch(cold_rom.windows, "stock_devices", Mock(return_value=[]))
        self.discover = self.patch(cold_rom.windows, "discover_windows_rom_disks", Mock(return_value=[self.observed]))
        self.patch(cold_rom.windows, "RomDiskAttestation", SimpleNamespace(from_discovery=lambda _: self.attestation))
        self.patch(cold_rom.windows, "QuietBufferedRomTransport", Transport)
        self.patch(cold_rom.windows, "MiniMediaChangePause", Pause)
        self.patch(self.backend, "_claim_host_session", Mock())
        Transport.created = []

    def patch(self, owner, name, value):
        return self.stack.enter_context(patch.object(owner, name, value))

    def attach(self):
        self.backend.enter_hyperrig_rom("user-confirmed-cold-rom", None, self.store)

    def test_fresh_observed_ROM_attaches_once_without_any_boot_command(self):
        self.attach()
        self.assertIs(self.backend.attestation, self.attestation)
        self.assertIsNone(self.backend.live_slot)
        self.assertFalse(self.backend.jump_unknown)
        self.assertFalse(self.store.events[-1]["software_UBOOT_sent"])
        self.assertTrue(Transport.created[0].closed)
        self.assertEqual(Transport.created[0].calls, [])
        with self.assertRaises(ValueError):
            self.attach()

    def test_absent_user_ack_or_ambiguous_snapshot_is_rejected(self):
        for changed in ({"user_acknowledged_sequence": False}, {"rom_disks": []},
                        {"rom_disks": [self.observed, self.observed]}, {"hyperrig_ports": ["COM3"]}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                cold_rom.ColdRomBackend({**self.evidence, **changed})

    def test_old_observation_stops_before_device_discovery(self):
        self.now += 1900
        with self.assertRaisesRegex(ValueError, "too old"):
            self.attach()
        self.discover.assert_not_called()
        self.assertFalse(Transport.created)

    def test_changed_ROM_identity_stops_before_open(self):
        self.discover.return_value = [{"path": "other-ROM"}]
        with self.assertRaisesRegex(ValueError, "changed"):
            self.attach()
        self.assertFalse(Transport.created)

    def test_preexisting_ROM_arrival_stops_before_any_RAM_upload(self):
        self.attestation.last_arrival_filetime -= 300_000_000
        with self.assertRaisesRegex(ValueError, "predates"):
            self.attach()
        self.assertEqual(Transport.created[0].calls, [])
        self.assertIsNone(self.backend.mcn)

    def test_present_application_stops_before_ROM_open(self):
        self.apps.return_value = ["COM3"]
        with self.assertRaisesRegex(ValueError, "Application USB"):
            self.attach()
        self.assertFalse(Transport.created)


if __name__ == "__main__":
    unittest.main()
