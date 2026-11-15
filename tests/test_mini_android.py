"""Offline APK derivation checks; no Java build, phone or transport is started."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import build_mini_android as apk


class MiniAndroidTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.base, cls.audit = apk.audit_inputs()
        cls.manifest = apk.ROOT/"build/hyperrig-mini-integrated/firmware-manifest.json"
        cls.profile = apk.load_profile(cls.manifest)
        cls.html, _ = apk.derive_html(cls.original["assets/public/index.html"].decode("utf-8"), cls.profile)
        cls.config = apk.android_config(cls.base["assets/capacitor.config.json"])
        cls.profile_js = (apk.ROOT/"app/mini/mini-profile.js").read_bytes()
        cls.ui_js = (apk.ROOT/"app/mini/mini-ui.js").read_bytes()

    def test_original_android_editor_and_native_bridge_provenance(self):
        self.assertEqual(self.original["assets/public/index.html"], apk.checked(apk.SOURCE/"web/tankg.html",apk.SOURCE_SHA))
        self.assertTrue(self.audit["android_html_identical_to_desktop"])
        self.assertFalse(self.audit["native_usb_serial_plugin_present"])
        self.assertEqual(len(self.audit["dex"]), 8)
        self.assertEqual([p["pkg"] for p in self.audit["plugins"]], ["@capacitor-community/bluetooth-le","@capacitor/app"])
        self.assertTrue(self.audit["ble_pairing_may_persist_bond_state"])
        for token in ("HyperRigNative.saveFile", "HyperRigNative.shareLast", "const capBle =", "const BleTransport ="):
            self.assertIn(token, self.html)

    def test_derived_asset_policy_compiles_and_rejects_ble_mutations(self):
        result = apk.check_javascript(self.html, self.profile, self.profile_js, self.ui_js)
        self.assertGreaterEqual(result["inline_scripts_parsed"],5)
        self.assertTrue(result["ble_queries_require_matching_pong"])
        self.assertFalse(result["ble_mutations_enabled"] or result["device_io"])
        scoped = copy.deepcopy(self.profile)
        scoped.update(hardware_verified=True, command_validation={"path":"offline-fixture","sha256":"a"*64},
                      command_capabilities={"FXP":["FXP 1 0 51"],"PSAVE":["PSAVE 31 Scratch"]})
        self.assertFalse(apk.check_javascript(self.html, scoped, self.profile_js, self.ui_js)["ble_mutations_enabled"])

    def test_packaged_native_files_cannot_be_changed_dropped_or_added(self):
        candidate = dict(self.base)
        candidate.update({"assets/public/index.html":self.html.encode("utf-8"),
                          "assets/capacitor.config.json":self.config,
                          "assets/public/mini-profile.js":self.profile_js,"assets/public/mini-ui.js":self.ui_js})
        def verify(files):
            return apk.validate_payload(files,self.base,html=self.html,config=self.config,
                                        profile_js=self.profile_js,ui_js=self.ui_js)
        self.assertEqual(verify(candidate)["dex_files_byte_identical"],8)
        for name in ("classes8.dex","assets/native-bridge.js","assets/capacitor.plugins.json",
                     "assets/public/index.html","assets/public/mini-profile.js","assets/hyperrig-licenses/LICENSE.md"):
            bad = dict(candidate); bad[name] += b"unreviewed"
            with self.subTest(name=name), self.assertRaises(ValueError): verify(bad)
        bad = dict(candidate); bad["classes9.dex"] = candidate["classes8.dex"]
        with self.assertRaises(ValueError): verify(bad)
        bad = dict(candidate); del bad["classes8.dex"]
        with self.assertRaises(ValueError): verify(bad)

    def test_android_config_and_labels_keep_namespace_and_remove_g_b_guidance(self):
        import json
        value = json.loads(self.config)
        self.assertEqual(value["appId"],"com.hyperrig.app")
        self.assertEqual(value["appName"],"HyperRig MINI")
        message = value["plugins"]["BluetoothLe"]["displayStrings"]["noDeviceFound"]
        self.assertIn("tankm_fw",message)
        self.assertNotIn("Windows PC",message)
        strings = '<resources><string name="app_name">HyperRig</string><string name="title_activity_main">HyperRig</string></resources>'
        self.assertEqual(apk.mini_labels(strings).count('>HyperRig MINI</string>'),2)
        with self.assertRaises(ValueError): apk.mini_labels(strings.replace("HyperRig","Unknown",1))
        with self.assertRaises(ValueError): apk.android_config(self.config)  # MINI is not the pinned G/B base

    def test_signature_check_requires_alignment_schemes_and_exact_local_certificate(self):
        good = f"zipalign verified\nsignature verified [v2, v3]\nSHA256: {apk.CERTIFICATE_SHA} / SHA384withRSA\n0 errors"
        self.assertEqual(apk.verify_signature_log(good)["certificate_sha256"],apk.CERTIFICATE_SHA)
        for bad in (good.replace(apk.CERTIFICATE_SHA,"a"*64),good.replace("zipalign verified",""),
                    good.replace("[v2, v3]","[v1]"),good.replace("0 errors","1 errors")):
            with self.assertRaises(ValueError): apk.verify_signature_log(bad)

    def test_check_only_never_invokes_build_or_changes_g_b_apk(self):
        with patch.object(apk,"command",side_effect=AssertionError("Java build invoked")):
            result = apk.build(apk.ROOT/"build/hyperrig-mini-integrated/android",self.manifest,check_only=True)
        self.assertTrue(result["check_only"])
        self.assertFalse(result["installed_on_phone"] or result["device_io"] or result["native_usb_serial_added"])
        self.assertEqual(apk.sha(apk.BASE.read_bytes()),apk.BASE_SHA)
        for path in (apk.ROOT/"build/hyperrig",apk.ROOT/"build/android/subdir",apk.ROOT/"artifacts/new"):
            with self.subTest(path=path),self.assertRaises(ValueError): apk.build(path,self.manifest,check_only=True)


if __name__ == "__main__":
    unittest.main()
