"""Offline package boundaries; synthetic manifests never authorize hardware."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import build_mini_installer_bundle as bundle


class PackageTests(unittest.TestCase):
    VARIANT = "v3"

    @classmethod
    def setUpClass(cls):
        cls.editor_files, cls.editor_info = bundle.editor_assets(bundle.DEFAULT_EDITOR, variant=cls.VARIANT)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="hyperrig-package-test-")
        self.root = Path(self.temporary.name)
        spec = bundle.release_variant(self.VARIANT)
        files = {name: b"synthetic package test file\n" for name in bundle.expected_files(variant=self.VARIANT)}
        files.update(self.editor_files)
        for source, destination, digest in spec["assets"]:
            files[destination] = (bundle.ROOT / source).read_bytes()
            self.assertEqual(bundle.sha(files[destination]), digest)
        for name, raw in files.items():
            bundle.write_file(self.root, name, raw)
        self.manifest = {"schema": 1, "kind": bundle.KIND, "variant": self.VARIANT,
                         "firmware": {"path": spec["assets"][0][1], "sha256": spec["image_sha256"]},
                         "runtime": {"executable": None}, "editor": self.editor_info,
                         "qualification": bundle.qualification_flags(spec),
                         "files": {name: bundle.sha(raw) for name, raw in files.items()}}
        self.publish()

    def tearDown(self):
        self.temporary.cleanup()

    def publish(self):
        raw = bundle.encoded(self.manifest)
        bundle.write_file(self.root, "release.json", raw)
        bundle.write_file(self.root, "release.sha256", (bundle.sha(raw) + "\n").encode())

    def check(self):
        return bundle.check_bundle(self.root, isolated=False)

    def test_inventory_contains_only_explicit_release_files(self):
        result = self.check()
        self.assertEqual(result["files"], len(bundle.expected_files(variant=self.VARIANT)))
        self.assertFalse(result["device_io"])
        self.assertFalse(result["hardware_qualified"])
        self.assertFalse(result["isolated_check"])
        for name in bundle.expected_files(variant=self.VARIANT):
            self.assertFalse(name.startswith(("analysis/", "research/", "artifacts/", "build/")))

    def test_unlisted_private_file_is_rejected(self):
        (self.root / "private-backup.bin").write_bytes(b"private")
        with self.assertRaisesRegex(ValueError, "Unexpected or missing"):
            self.check()

    def test_adding_private_file_to_manifest_does_not_expand_allowlist(self):
        (self.root / "private-backup.bin").write_bytes(b"private")
        self.manifest["files"]["private-backup.bin"] = bundle.sha(b"private")
        self.publish()
        with self.assertRaisesRegex(ValueError, "explicit allowlist"):
            self.check()

    def test_known_payload_cannot_be_changed_by_resealing_manifest(self):
        name = "assets/writer-a.bin"
        raw = (self.root / name).read_bytes()
        changed = raw[:-1] + bytes((raw[-1] ^ 1,))
        (self.root / name).write_bytes(changed)
        self.manifest["files"][name] = bundle.sha(changed)
        self.publish()
        with self.assertRaisesRegex(ValueError, "Known payload pin"):
            self.check()

    def test_changed_runtime_file_or_missing_file_is_rejected(self):
        p = self.root / "hyperrig/installer/core.py"
        p.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            self.check()
        p.unlink()
        with self.assertRaisesRegex(ValueError, "Unexpected or missing"):
            self.check()

    def test_incomplete_manifest_seal_is_rejected(self):
        (self.root / "release.sha256").write_text("0" * 64 + "\n", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "seal differs"):
            self.check()

    def test_resealing_a_wider_editor_policy_is_rejected(self):
        name = "editor/web/mini-profile.js"
        raw = b"/* forbidden wider policy */"
        (self.root / name).write_bytes(raw)
        self.manifest["files"][name] = bundle.sha(raw)
        self.publish()
        with self.assertRaisesRegex(ValueError, "Protected editor policy"):
            self.check()

    def test_resealing_a_blanket_write_profile_is_rejected(self):
        name = "editor/profile.json"
        value = json.loads((self.root / name).read_bytes())
        value["capabilities"]["write"] = True
        raw = bundle.encoded(value)
        (self.root / name).write_bytes(raw)
        self.manifest["files"][name] = bundle.sha(raw)
        self.publish()
        with self.assertRaisesRegex(ValueError, "capability scope"):
            self.check()

    def test_no_preview_hardware_promotion(self):
        for key in self.manifest["qualification"]:
            with self.subTest(key=key):
                self.manifest["qualification"][key] = True
                self.publish()
                with self.assertRaisesRegex(ValueError, "qualification flags"):
                    self.check()
                self.manifest["qualification"][key] = False

    def test_paths_are_relative_canonical_and_without_reparse_points(self):
        for name in ("../release.json", "/release.json", "C:/release.json", "x\\release.json",
                     "./release.json", "x/../release.json", "x//release.json"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                bundle.safe_file(self.root, name)
        original = Path.lstat
        def reparse(path):
            info = original(path)
            if path.name == "release.json":
                return type("Reparse", (), {"st_mode": info.st_mode, "st_file_attributes": 0x400})()
            return info
        with patch.object(Path, "lstat", reparse), self.assertRaisesRegex(ValueError, "Reparse"):
            bundle.safe_file(self.root, "release.json")

    def test_launch_scripts_do_not_elevate_or_add_implicit_install(self):
        for option in ("", "--editor", "--check-only"):
            text = bundle.launch_script(option).decode("ascii")
            self.assertIn("--bundle", text)
            self.assertIn("python -B -X utf8", text)
            self.assertNotIn("--admin", text)
            self.assertNotIn("--install", text)
            self.assertNotIn("powershell", text.lower())
            self.assertNotIn("curl", text.lower())


class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.info = bundle.editor_assets(bundle.DEFAULT_EDITOR)
        cls.profile = json.loads(cls.files["editor/profile.json"])

    def test_editor_reuses_policy_and_preserves_the_eight_families(self):
        self.assertEqual(self.profile["family_capabilities"], {"usb-cdc": bundle.FAMILIES})
        self.assertEqual(self.profile["capabilities"], {"identity": True, "read": True, "write": False, "panel": False})
        for name in ("mini-profile.js", "mini-fx-ui.js", "nam2chip.js"):
            self.assertEqual(self.files["editor/web/" + name], (bundle.DEFAULT_EDITOR / "app/web" / name).read_bytes())
        for name in ("LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md"):
            self.assertEqual(self.files["editor/" + name], (bundle.DEFAULT_EDITOR / "app" / name).read_bytes())

    def test_private_provenance_does_not_ship_in_profile_or_scope(self):
        for name in ("editor/profile.json", "editor/qualification.json"):
            raw = self.files[name].decode()
            for text in ("analysis/hardware", "artifacts/my-mini", "build/", "COM3", "PONG ", "Preset 1A", "timestamp"):
                self.assertNotIn(text, raw)
        reference = self.profile["family_validation"]["usb-cdc"]
        self.assertEqual(reference, [{"path": "editor/qualification.json", "sha256": bundle.sha(self.files["editor/qualification.json"])}])

    def test_timeout_install_is_once_after_original_editor_with_no_connect(self):
        html = self.files["editor/web/tankmini.html"].decode("utf-8")
        self.assertEqual(html.count('<script src="serial-open-timeout.js"></script>'), 1)
        self.assertEqual(html.count('<script src="portable-startup.js"></script>'), 1)
        self.assertLess(html.index('<script src="mini-fx-ui.js">'), html.index('<script src="portable-startup.js">'))
        startup = self.files["editor/web/portable-startup.js"].decode()
        self.assertIn("installMiniSerialOpenTimeout(SerialTransport)", startup)
        self.assertNotIn(".open(", startup)
        self.assertNotIn("requestPort", startup)
        self.assertNotIn("Pedal.cmd", startup)

    def test_packaged_timeout_matches_the_actual_english_serial_method(self):
        html = self.files["editor/web/tankmini.html"].decode("utf-8")
        methods = re.findall(r"async open\(known\) \{[\s\S]*?\n    this\.readLoop\(\);\n  \}", html)
        self.assertEqual(len(methods), 1)
        script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const x=JSON.parse(fs.readFileSync(0,'utf8'));
globalThis.SerialTransport=eval('({port:null,'+x.method+'})');
globalThis.navigator=new Proxy({}, {get(){throw Error('No device/browser access allowed')}});
vm.runInThisContext(x.helper);vm.runInThisContext(x.startup);
assert.equal(HYPERRIG_PORTABLE_SERIAL_TIMEOUT.timeout_ms,30000);
assert.equal(HYPERRIG_PORTABLE_SERIAL_TIMEOUT.native_open_unchanged,true);
assert.equal(SerialTransport.port,null);
assert.match(SerialTransport.open.toString(),/\)\), 30000\);/);
process.stdout.write('pass');
"""
        result = subprocess.run(["node", "-e", script], input=json.dumps({"method": methods[0],
            "helper": self.files["editor/web/serial-open-timeout.js"].decode(),
            "startup": self.files["editor/web/portable-startup.js"].decode()}),
            text=True, capture_output=True, timeout=15)
        self.assertEqual((result.returncode, result.stdout), (0, "pass"), result.stderr)


class OneSwitchTests(PackageTests):
    VARIANT = "v4"

    def reseal_file(self, name, value):
        raw = bundle.encoded(value)
        (self.root / name).write_bytes(raw)
        self.manifest["files"][name] = bundle.sha(raw)
        self.publish()

    def test_v4_cannot_relabel_hardware_or_enable_families(self):
        profile = json.loads((self.root / "editor/profile.json").read_bytes())
        self.assertIs(profile["hardware_verified"], False)
        self.assertEqual(profile["family_capabilities"], {})
        self.assertEqual(profile["family_validation"], {})
        profile["hardware_verified"] = True
        self.reseal_file("editor/profile.json", profile)
        with self.assertRaisesRegex(ValueError, "V4 editor must remain read-only"):
            self.check()

    def test_v3_label_cannot_be_used_for_v4_artifact(self):
        self.manifest["variant"] = "v3"
        self.publish()
        with self.assertRaisesRegex(ValueError, "variant/firmware binding"):
            self.check()

    def test_v4_preserves_static_vs_hardware_provenance(self):
        qualification = json.loads((self.root / "editor/qualification.json").read_bytes())
        self.assertEqual(qualification["source_image_sha256"], bundle.IMAGE_SHA)
        self.assertEqual(qualification["image_sha256"], bundle.ONE_SWITCH_IMAGE_SHA)
        self.assertIs(qualification["source_observations_apply_to_target_image"], False)
        self.assertIs(qualification["current_image_mutations_physically_retested"], False)
        self.assertEqual(qualification["enabled_families"], [])
        self.assertEqual(qualification["static_inheritance"]["report_sha256"], bundle.ONE_SWITCH_REPORT_SHA)
        qualification["current_image_mutations_physically_retested"] = True
        self.reseal_file("editor/qualification.json", qualification)
        with self.assertRaisesRegex(ValueError, "V4 editor must remain read-only"):
            self.check()

    def test_actual_v4_policy_permits_reads_and_denies_every_write_path(self):
        profile = (self.root / "editor/profile.json").read_text("utf-8")
        source = (self.root / "editor/web/mini-profile.js").read_text("utf-8")
        script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const x=JSON.parse(fs.readFileSync(0,'utf8'));
globalThis.HYPERRIG_MINI_BUILD=JSON.parse(x.profile);vm.runInThisContext(x.source);
const result=HyperRigMini.acceptPong('PONG tankm_fw M5.71 rel ble Jan  1 2000','usb-cdc');
assert.equal(result.ok,true);assert.equal(result.read,true);assert.equal(result.write,false);
for(const q of ['PING','MODEL','PLIST','FXT','FXS','LVL']) assert.equal(HyperRigMini.commandPolicy(q,'usb-cdc').allowed,true);
for(const q of ['GAIN 0 -1','PLOAD 0','PSAVE 1 Example','SNAPSAVE 0','FXA Q99 boost','FXP 0 0 -1','FXE 0 0','FXR 0'])
  assert.equal(HyperRigMini.commandPolicy(q,'usb-cdc').allowed,false);
assert.equal(HyperRigMini.familyWriteEnabled('usb-cdc'),false);
assert.equal(HyperRigMini.fullWriteEnabled(),false);assert.equal(HyperRigMini.scopedWriteEnabled(),false);
process.stdout.write('pass');
"""
        result = subprocess.run(["node", "-e", script], input=json.dumps({"profile": profile, "source": source}),
                                text=True, capture_output=True, timeout=15)
        self.assertEqual((result.returncode, result.stdout), (0, "pass"), result.stderr)

    def test_v4_instructions_state_one_switch_as_planned_and_untested(self):
        text = bundle.preview_readme(bundle.release_variant("v4"))
        self.assertIn("any ONE footswitch", text)
        self.assertIn("has not been verified on hardware", text)
        self.assertIn("stock-to-v4", text)
        self.assertIn("permits PING and read queries only", text)
        self.assertNotIn("The editor enables USB", text)


if __name__ == "__main__":
    unittest.main()
