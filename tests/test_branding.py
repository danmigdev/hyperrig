"""Verify renamed binary structures without starting the recovered programs."""
import hashlib
import importlib.util
import json
import marshal
from pathlib import Path
import struct
import types
import unittest
import zipfile
import zlib

from hyperrig.branding import (archive_entries, rename_code, rename_fixed,
                              rename_text, rebrand_firmware, rewrite_pyz)
from hyperrig.jieli import unpack_app

ROOT = Path(__file__).resolve().parents[1]


class BrandingTests(unittest.TestCase):
    def test_text_case_and_external_destinations(self):
        self.assertEqual(rename_text("UltraRig ultrarig ULTRARIG Ultra<i>Rig"),
                         "HyperRig hyperrig HYPERRIG Hyper<i>Rig")
        self.assertEqual(rename_text("https://ultrarig.app/latest.json"),
                         "https://hyperrig.invalid/latest.json")
        self.assertEqual(rename_text("https://www.m-vave.com/download"),
                         "https://www.m-vave.com/download")

    def test_binary_string_offsets_are_unchanged(self):
        raw = b"\x12UltraRig\0\xabULTRARIG\0" + "ultrarig".encode("utf-16le")
        expected = b"\x12HyperRig\0\xabHYPERRIG\0" + "hyperrig".encode("utf-16le")
        self.assertEqual(rename_fixed(raw), expected)
        self.assertEqual(len(rename_fixed(raw)), len(raw))

    def test_marshalled_code_changes_names_and_constants_without_opcodes(self):
        code = compile("def ultrarig_label():\n return 'UltraRig'\n", "ultrarig.py", "exec")
        changed = rename_code(code)
        self.assertEqual(changed.co_code, code.co_code)
        self.assertEqual(changed.co_consts[0].co_code, code.co_consts[0].co_code)
        self.assertEqual(changed.co_consts[0].co_name, "hyperrig_label")
        self.assertEqual(changed.co_consts[0].co_consts[-1], "HyperRig")
        self.assertEqual(changed.co_filename, "hyperrig.py")

    def test_pyz_rebuild_updates_offsets_and_module_names(self):
        payload = zlib.compress(marshal.dumps(compile("title='UltraRig'", "ultrarig.py", "exec")))
        raw = b"PYZ\0" + importlib.util.MAGIC_NUMBER + struct.pack("!I", 12 + len(payload))
        raw += payload + marshal.dumps([("ultrarig_demo", (0, 12, len(payload)))])
        result, _ = rewrite_pyz(raw)
        offset = struct.unpack_from("!I", result, 8)[0]
        [(name, (_, at, size))] = marshal.loads(result[offset:])
        self.assertEqual(name, "hyperrig_demo")
        self.assertLessEqual(at + size, offset)
        code = marshal.loads(zlib.decompress(result[at:at + size]))
        self.assertIn("HyperRig", code.co_consts)


@unittest.skipUnless((ROOT / "artifacts/alpha11/release.json").is_file(), "fetch original packages first")
class FirmwareBrandingTests(unittest.TestCase):
    def test_all_images_round_trip_without_moving_payloads(self):
        manifest = json.loads((ROOT / "research/input-manifest.json").read_text(encoding="utf-8"))
        for item in manifest["firmware_images"]:
            with self.subTest(file=item["file"]):
                raw = (ROOT / item["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
                _, entries, original = unpack_app(raw)
                changed, replacements = rebrand_firmware(raw)
                _, after_entries, after = unpack_app(changed)
                self.assertTrue(replacements)
                self.assertEqual(len(changed), len(raw))
                self.assertEqual([(e.name, e.offset, e.size) for e in entries],
                                 [(e.name, e.offset, e.size) for e in after_entries])
                for name in original:
                    self.assertEqual(after[name], rename_fixed(original[name]))
                broken = bytearray(changed)
                broken[0x220] ^= 1
                with self.assertRaisesRegex(ValueError, "CRC"):
                    unpack_app(broken)


@unittest.skipUnless((ROOT / "build/hyperrig/rebranding-report.json").is_file(), "build branded packages first")
class RebuiltApplicationTests(unittest.TestCase):
    def test_windows_code_opcodes_and_licenses_are_preserved(self):
        def codes(executable):
            _, _, entries = archive_entries(executable)
            result = {}
            for name, kind, _, data in entries:
                if kind in (b"s", b"m", b"M"):
                    result[rename_text(name)] = marshal.loads(data)
                elif kind == b"z":
                    offset = struct.unpack_from("!I", data, 8)[0]
                    toc = marshal.loads(data[offset:])
                    for module, (typ, at, size) in toc.items() if isinstance(toc, dict) else toc:
                        if typ in (0, 1):
                            result[rename_text(module)] = marshal.loads(zlib.decompress(data[at:at + size]))
            return result

        def equal_code(before, after):
            self.assertEqual(before.co_code, after.co_code)
            self.assertEqual(before.co_exceptiontable, after.co_exceptiontable)
            self.assertEqual(before.co_stacksize, after.co_stacksize)
            self.assertEqual(len(before.co_consts), len(after.co_consts))
            for a, b in zip(before.co_consts, after.co_consts):
                if isinstance(a, types.CodeType):
                    equal_code(a, b)
                else:
                    self.assertEqual(rename_code(a), b)

        before_root = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win"
        after_root = ROOT / "build/hyperrig/windows/HyperRig-alpha11-v2-win"
        before = codes((before_root / "UltraRig-Installer.exe").read_bytes())
        after = codes((after_root / "HyperRig-Installer.exe").read_bytes())
        self.assertEqual(before.keys(), after.keys())
        for key in before:
            equal_code(before[key], after[key])
        for name in ("LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md"):
            self.assertEqual((before_root / name).read_bytes(), (after_root / name).read_bytes())

    def test_android_dex_checksums_and_product_strings(self):
        apk = ROOT / "build/hyperrig/HyperRig-local-android.apk"
        if not apk.exists():
            self.skipTest("Android derivative not built")
        with zipfile.ZipFile(apk) as archive:
            for name in archive.namelist():
                if name.endswith(".dex"):
                    data = archive.read(name)
                    self.assertEqual(data[12:32], hashlib.sha1(data[32:]).digest())
                    self.assertEqual(struct.unpack_from("<I", data, 8)[0], zlib.adler32(data[12:]) & 0xFFFFFFFF)
                    self.assertNotIn(b"ultrarig", data.lower())
            config = json.loads(archive.read("assets/capacitor.config.json"))
            self.assertEqual(config["appId"], "com.hyperrig.app")
            self.assertEqual(config["appName"], "HyperRig")
            self.assertIn("assets/hyperrig-licenses/NOTICE.md", archive.namelist())
            html = archive.read("assets/public/index.html").decode()
            self.assertNotIn("ultrarig", html.lower())
            self.assertIn("Hyper<i>Rig", html)


if __name__ == "__main__":
    unittest.main()
