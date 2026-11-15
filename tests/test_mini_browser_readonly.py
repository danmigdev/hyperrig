"""Browser policy checks; no browser, ports, Bluetooth or USB are opened."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools import probe_mini_browser_readonly as browser


class BrowserReadonlyTests(unittest.TestCase):
    def test_chooser_matches_exact_COM_not_substrings(self):
        prompt = {"id": "prompt", "devices": [{"id": "a", "name": "USB serial (COM12)"},
                    {"id": "b", "name": "HyperRig (COM2)"}]}
        self.assertEqual(browser.select_device(prompt, "COM2"), {"id": "prompt", "deviceId": "b"})
        self.assertEqual(browser.select_device(prompt, "COM12"), {"id": "prompt", "deviceId": "a"})

    def test_chooser_never_selects_first_or_ambiguous_device(self):
        for devices in ([], [{"id": "a", "name": "HyperRig"}],
                        [{"id": "a", "name": "COM2"}, {"id": "b", "name": "COM2"}],
                        [{"id": "a", "name": "XCOM2"}]):
            with self.subTest(devices=devices), self.assertRaises(ValueError):
                browser.select_device({"id": "p", "devices": devices}, "COM2")
        self.assertIsNone(browser.select_device({"id": "p", "devices": []}, "COM2", allow_missing=True))

    def evidence(self):
        return {"schema": 1, "target": "tank-mini", "transport": "usb-cdc", "vid": 0x3654,
                "pid": 0x5155, "com": "COM12", "image_sha256": browser.IMAGE_SHA,
                "serial_port_closed": True, "pong": "PONG tankm_fw M5.71 rel ble Nov 15 2026 20:00:00",
                "observed_utc": "2026-11-15T22:00:00Z"}

    def check_evidence(self, item, expected_hash=None):
        with tempfile.TemporaryDirectory(prefix="mini-browser-policy-", dir=browser.ROOT / "build") as folder:
            folder = Path(folder).resolve()
            self.assertTrue(folder.is_relative_to((browser.ROOT / "build").resolve()))
            path = folder / "evidence.json"
            raw = json.dumps(item).encode()
            path.write_bytes(raw)
            return browser.load_evidence(path, expected_hash or browser.sha(raw))

    def test_exact_evidence_and_hash(self):
        self.assertEqual(self.check_evidence(self.evidence()), self.evidence())
        with self.assertRaises(ValueError):
            self.check_evidence(self.evidence(), "0" * 64)

    def test_wrong_board_image_open_port_or_pong_rejected(self):
        changes = {"target": "tank-g", "transport": "ble-nus", "vid": 1, "pid": 0x4155,
                   "com": "COM0", "serial_port_closed": False, "image_sha256": "0" * 64,
                   "pong": "PONG tankg_fw M5.71 rel ble Nov 15 2026", "observed_utc": "later"}
        for field, value in changes.items():
            item = deepcopy(self.evidence()); item[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check_evidence(item)
        item = self.evidence(); item["pong"] += "\nGSAVE"
        with self.assertRaises(ValueError):
            self.check_evidence(item)

    def test_javascript_guard_uses_only_fake_serial(self):
        executable = shutil.which("node")
        self.assertIsNotNone(executable, "existing Node required; no automatic installation")
        result = subprocess.run([executable, str(browser.ROOT / "tests/mini_browser_guard_test.js"),
                                 str(browser.GUARD)], capture_output=True, text=True, check=True)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["result"], "pass")
        self.assertGreaterEqual(parsed["checks"], 40)
        self.assertFalse(parsed["device_io"])


if __name__ == "__main__":
    unittest.main()
