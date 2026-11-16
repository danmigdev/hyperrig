"""Exercise archive trust boundaries and release version validation without hardware."""
import io
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools.build_release import archive_files, bundle, code, load_inputs, version
from tools.create_release_inputs import APK_ASSETS, native_template, zip_bytes


class ReleaseInputsTests(unittest.TestCase):
    def test_native_shell_preserves_services_and_removes_old_ui_and_signatures(self):
        original = {n: b"native asset" for n in APK_ASSETS}
        original.update({"classes.dex": b"dex", **{f"classes{i}.dex": b"dex" for i in range(2, 9)}})
        original.update({"META-INF/services/example": b"native.Service", "META-INF/LICENSE": b"notice",
                         "META-INF/OLD.RSA": b"old signature", "META-INF/MANIFEST.MF": b"old digest",
                         "assets/public/index.html": b"old editor", "assets/old-report.json": b"old report"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "original.apk"
            path.write_bytes(zip_bytes(original))
            raw, dex = native_template(path)
        result = archive_files(raw)
        self.assertEqual(result["META-INF/services/example"], b"native.Service")
        self.assertEqual(result["META-INF/LICENSE"], b"notice")
        self.assertEqual(len(dex), 8)
        self.assertTrue(APK_ASSETS <= result.keys())
        for name in ("META-INF/OLD.RSA", "META-INF/MANIFEST.MF", "assets/public/index.html", "assets/old-report.json"):
            self.assertNotIn(name, result)

    def test_archive_hash_and_each_file_are_required(self):
        raw = zip_bytes({"public.txt": b"reviewed"})
        pins = {"public.txt": {"bytes": 8, "sha256": bundle.sha(b"reviewed")}}
        self.assertEqual(archive_files(raw, pins), {"public.txt": b"reviewed"})
        with self.assertRaisesRegex(ValueError, "Input file differs"):
            archive_files(zip_bytes({"public.txt": b"modified"}), pins)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inputs.zip"
            path.write_bytes(b"tampered archive")
            with patch("tools.build_release.read_lock", return_value={"sha256": bundle.sha(raw)}):
                with self.assertRaisesRegex(ValueError, "archive hash differs"):
                    load_inputs(path)

    def test_extra_private_files_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "inventory differs"):
            archive_files(zip_bytes({"public.txt": b"okay", "signing.p12": b"private"}),
                          {"public.txt": {"bytes": 4, "sha256": bundle.sha(b"okay")}})

    def test_unsafe_paths_are_rejected(self):
        for name in ("../outside", "/absolute", "drive:outside", "dir\\outside", "dir/../outside", "dir//outside"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                raw = io.BytesIO()
                with zipfile.ZipFile(raw, "w") as archive:
                    entry = zipfile.ZipInfo("safe")
                    # ZipInfo normalizes backslashes on Windows at construction.
                    entry.filename = name
                    archive.writestr(entry, b"x")
                archive_files(raw.getvalue())

    def test_symlinks_and_duplicate_names_are_rejected(self):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as archive:
            item = zipfile.ZipInfo("link")
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(item, "target")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            archive_files(raw.getvalue())
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as archive:
            archive.writestr("same", "a")
            with self.assertWarns(UserWarning):
                archive.writestr("same", "b")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            archive_files(raw.getvalue())

    def test_release_version_cannot_be_a_path_or_shell_expression(self):
        self.assertEqual(version("0.1.0-preview.1"), "0.1.0-preview.1")
        for value in ("v0.1.0", "0.1.0", "../preview", "0.1.0-preview.1\n", "$(id)", "0.1.0-preview.0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                version(value)
        self.assertEqual(code("10001"), 10001)
        for value in ("1", "0", "-1", "2100000001", "x"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                code(value)


if __name__ == "__main__":
    unittest.main()
