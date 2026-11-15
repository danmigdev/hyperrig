"""Reject stale or incomplete component evidence before target integration."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_mini_boot import verify_recorded_hashes


class ComponentInputsTests(unittest.TestCase):
    def test_changed_source_or_object_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = {}
            for name, data in (("driver.c", b"source"), ("driver.o", b"object")):
                (root / name).write_bytes(data)
                expected[name] = hashlib.sha256(data).hexdigest()
            verify_recorded_hashes(expected, root)
            for name in expected:
                previous = (root / name).read_bytes()
                (root / name).write_bytes(previous + b"changed")
                with self.assertRaisesRegex(ValueError, "changed or missing"):
                    verify_recorded_hashes(expected, root)
                (root / name).write_bytes(previous)

    def test_missing_input_and_empty_report_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for expected in ({"missing.o": "0" * 64}, {}):
                with self.assertRaises(ValueError):
                    verify_recorded_hashes(expected, root)


if __name__ == "__main__":
    unittest.main()
