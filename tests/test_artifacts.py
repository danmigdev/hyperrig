"""Integration checks against the actual downloaded, hashed firmware images."""
from pathlib import Path
import json
import unittest

from hyperrig.jieli import sha256, unpack_app, unpack_fwsc

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT / "artifacts/alpha11/release.json").exists(), "fetch release artifacts first")
class FirmwareEvidenceTests(unittest.TestCase):
    def test_all_four_release_images(self):
        images = list((ROOT / "artifacts/alpha11").rglob("*_app.bin"))
        self.assertEqual(len(images), 4)
        for path in images:
            with self.subTest(path=path.name):
                raw = path.read_bytes()
                meta = json.loads(path.with_suffix(".json").read_text())
                self.assertEqual(sha256(raw), meta["sha256"])
                plain, entries, files = unpack_app(raw)
                self.assertEqual(entries[0].offset, 0x02000120)
                self.assertEqual(len(files["cfg_tool.bin"]), 383)
                self.assertIn(meta["version"].encode(), plain)
                self.assertEqual(next(e.offset for e in entries if e.name == "VM"), 0x7B000)

    def test_payload_tamper_is_detected(self):
        path = next((ROOT / "artifacts/alpha11").rglob("*_app.bin"))
        raw = bytearray(path.read_bytes())
        raw[0x200] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            unpack_app(raw)

    def test_wrong_key_rejected(self):
        path = next((ROOT / "artifacts/alpha11").rglob("*_app.bin"))
        with self.assertRaises(ValueError):
            unpack_app(path.read_bytes(), 0xFFFF)

    def test_mini_has_its_own_flash_map(self):
        raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
        meta, contents = unpack_fwsc(raw)
        self.assertEqual(meta["chip"], "AC791N")
        plain, entries, files = unpack_app(contents["flash.bin"][0x4000:])
        self.assertIn(b"TANK MINI_009", plain)
        addresses = {e.name: e.offset for e in entries}
        self.assertEqual(addresses["VM"], 0x82000)
        self.assertEqual(addresses["BTIF"], 0xBE000)
        self.assertNotIn("OTP", addresses)
        self.assertEqual(len(files["app.bin"]), 511032)

    def test_truncated_vendor_package_rejected(self):
        raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
        with self.assertRaises(ValueError):
            unpack_fwsc(raw[:-1])


if __name__ == "__main__":
    unittest.main()
