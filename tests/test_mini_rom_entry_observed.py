"""Fresh ROM-entry orchestration and bounded post-command observation, offline."""
from unittest.mock import Mock, patch
import unittest

from hyperrig.installer import rom_entry_observed as observed
from tests import test_mini_one_switch_upgrade as earlier


class ObservedEntryTests(earlier.EntryTests):
    def setUp(self):
        super().setUp()
        self.backend = observed.ObservedRomEntryBackend()
        self.addCleanup(self.backend.close)
        self.patch(self.backend, "_claim_host_session", Mock())
        self.transport.read.side_effect = OSError("USB detached after UBOOT")

    def test_detach_is_observed_before_serial_close(self):
        events = []
        self.transport.read.side_effect = lambda size: events.append("read") or b"OK UBOOT\n"
        self.transport.close.side_effect = lambda: events.append("close")
        self.ports.side_effect = [self.port, self.port, [], []]
        self.enter()
        self.assertEqual(events, ["read", "close"])
        self.transport.write.assert_called_once_with(b"UBOOT\n")
        self.assertTrue(any(row["event"] == "cdc_absent_after_UBOOT" for row in self.store.events))

    def test_observation_timeout_never_sends_or_reopens_anything(self):
        self.transport.read.side_effect = None
        self.transport.read.return_value = b""
        self.ports.side_effect = None
        self.ports.return_value = self.port
        start = self.clock.now()
        observed.observe_detach(self.transport, "COM3", self.store, timeout=2)
        self.assertLess(self.clock.now() - start, 2.2)
        self.transport.write.assert_not_called()
        self.transport.close.assert_not_called()
        self.assertEqual(self.store.events[-1]["event"], "cdc_detach_not_observed_before_deadline")

    def test_excessive_post_command_bytes_terminate_observation(self):
        self.transport.read.side_effect = None
        self.transport.read.return_value = b"x" * 512
        self.ports.side_effect = None
        self.ports.return_value = self.port
        with self.assertRaisesRegex(ValueError, "bound"):
            observed.observe_detach(self.transport, "COM3", self.store)
        self.transport.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
