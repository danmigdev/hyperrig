"""Portable planner tests using public firmware and synthetic private tails.

Generated release artifacts must be available from the normal local build.
No private unit dump, device, transport, subprocess, or historical plan is used.
"""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hyperrig.installer import core
from hyperrig.jieli import unpack_fwsc

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_STOCK = ROOT / "artifacts/tank-mini/TANK-MINI.fwsc"
INPUTS = {
    "firmware": "build/hyperrig-mini-audio-v3/hyperrig-mini.app-area.bin",
    "writer": "build/mini-app-writer-operational/hyperrig-writer-operational-01c20000.bin",
    "writer_elf": "build/mini-app-writer-operational/hyperrig-writer-operational-01c20000.elf",
    "reader": "build/mini-flash-reader/hyperrig-reader-01c28000.bin",
    "reader_elf": "build/mini-flash-reader/hyperrig-reader-01c28000.elf",
    "reset": "build/mini-rom-reset/hyperrig-reset-01c20000.bin",
    "reset_elf": "build/mini-rom-reset/hyperrig-reset-01c20000.elf",
}
ONE_SWITCH_INPUT = ROOT / "build/hyperrig-mini-audio-v4/hyperrig-mini.app-area.bin"
ONE_SWITCH_SHA256 = "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
ONE_SWITCH_QUALIFICATION = ("direct_stock_to_v4", "cold_boot_recovery", "interrupted_write_recovery")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class PortableCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [str(p) for p in [PUBLIC_STOCK, *(ROOT / p for p in INPUTS.values())] if not p.is_file()]
        if missing:
            raise unittest.SkipTest("Build the public MINI release fixtures first: " + ", ".join(missing))
        stock_raw = PUBLIC_STOCK.read_bytes()
        if sha(stock_raw) != core.STOCK_FWSC_SHA256:
            raise AssertionError("Public stock fixture hash differs")
        _, files = unpack_fwsc(stock_raw)
        cls.stock = files["flash.bin"]
        cls.payloads = {name: (ROOT / path).read_bytes() for name, path in INPUTS.items()}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / "release"
        assets = self.bundle / "assets"
        assets.mkdir(parents=True)
        for key, raw in self.payloads.items():
            (assets / key).write_bytes(raw)
        self.manifest = {
            "schema": 1, "project": "HyperRig", "target": "tank-mini",
            "stock_identity": "TANK MINI_009", "stock_usb": [0x4C4A, 0xC755],
            "rom_usb": [0x4C4A, 0x8057], "jedec_hex": "eb6014",
            "application_range": [0x4000, 0x82000],
            "qualification": {key: False for key in core.QUALIFICATION_FLAGS},
        }
        for key in ("firmware", "writer", "reader", "reset"):
            raw = self.payloads[key]
            self.manifest[key] = {"path": "assets/" + key, "bytes": len(raw), "sha256": sha(raw)}
        for key, slot in (("writer", core.WRITER_SLOT), ("reader", core.READER_SLOT), ("reset", core.RESET_SLOT)):
            self.manifest[key].update(slot=slot, elf_path="assets/" + key + "_elf",
                                      elf_sha256=sha(self.payloads[key + "_elf"]))
        self.manifest["writer"]["build_tag"] = core.WRITER_BUILD_TAG
        self.write_manifest()
        self.backup = self.unit_backup(37)

    def write_manifest(self):
        (self.bundle / "release.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def unit_backup(self, seed):
        # Exact public SPL and application; only non-code, unit-specific areas vary.
        tail = bytes((seed + i * 13 + (i >> 8)) & 255 for i in range(core.CAPACITY - len(self.stock)))
        return self.stock + tail

    def prepare(self, backup=None):
        raw = self.backup if backup is None else backup
        return core.plan_install(core.load_release(self.bundle), raw, bytes(bytearray(raw)),
                                 identity=core.STOCK_IDENTITY, jedec_hex=core.JEDEC_HEX)

    def use_one_switch_release(self):
        if not ONE_SWITCH_INPUT.is_file():
            self.skipTest("Build the separate v4 any-one-footswitch candidate first")
        payload = ONE_SWITCH_INPUT.read_bytes()
        self.assertEqual(sha(payload), ONE_SWITCH_SHA256)
        self.assertEqual(core.ONE_SWITCH_FIRMWARE_SHA256, ONE_SWITCH_SHA256)
        (self.bundle / "assets/firmware").write_bytes(payload)
        self.manifest["firmware"].update(bytes=len(payload), sha256=ONE_SWITCH_SHA256)
        self.manifest["qualification"] = {key: False for key in ONE_SWITCH_QUALIFICATION}
        self.write_manifest()
        return payload

    def test_public_stock_pins_and_release_ELF_validation(self):
        from tools import build_mini_app_writer_operational as validator
        self.assertEqual(len(self.stock), core.APP_END)
        self.assertEqual(sha(self.stock[:core.APP_START]), core.STOCK_SPL_SHA256)
        self.assertEqual(sha(self.stock[core.APP_START:]), core.STOCK_APP_SHA256)
        with patch.object(validator, "inspect_operational_elf", wraps=validator.inspect_operational_elf) as inspect:
            release = core.load_release(self.bundle)
        inspect.assert_called_once_with(self.payloads["writer_elf"], core.WRITER_SLOT)
        self.assertEqual(release.firmware, self.payloads["firmware"])
        self.assertEqual(release.reset_contract["slot"], core.RESET_SLOT)
        self.assertEqual(release.reset_contract["elf_sha256"], sha(release.reset_elf))
        self.assertEqual(release.root, self.bundle.resolve())

    def test_different_units_preserve_their_own_complete_external_regions(self):
        from tools.install_mini_app import Installation
        a, b = self.prepare(), self.prepare(self.unit_backup(103))
        self.assertIsInstance(a.installation, Installation)
        self.assertNotEqual(a.installation.backup_sha256, b.installation.backup_sha256)
        self.assertNotEqual(a.installation.plan_sha256, b.installation.plan_sha256)
        self.assertEqual(a.installation.preimage, b.installation.preimage)
        for prepared in (a, b):
            self.assertEqual(prepared.expected_full[:core.APP_START], prepared.backup[:core.APP_START])
            self.assertEqual(prepared.expected_full[core.APP_END:], prepared.backup[core.APP_END:])
            self.assertEqual(prepared.expected_full[0xB7000:0xBD000], prepared.backup[0xB7000:0xBD000])
            self.assertEqual(prepared.expected_full[core.APP_START:core.APP_END], self.payloads["firmware"])
            self.assertTrue(core.validate_completed(prepared, prepared.expected_full)["verified"])

    def test_exact_changed_sectors_header_sector_and_page_last(self):
        prepared = self.prepare()
        expected = [a for a in range(core.APP_START, core.APP_END, 4096)
                    if prepared.backup[a:a + 4096] != prepared.expected_full[a:a + 4096]]
        self.assertEqual(prepared.installation.sector_order, tuple(expected[1:] + [core.APP_START]))
        self.assertEqual(len(set(prepared.installation.sector_order)), len(expected))
        self.assertEqual(prepared.record["sectors"][-1]["page_order"], list(range(0x4100, 0x5000, 256)) + [0x4000])
        self.assertEqual(prepared.record["installation"], prepared.installation.summary())
        for sector in prepared.record["sectors"][:-1]:
            self.assertEqual(sector["page_order"], list(range(sector["address"], sector["address"] + 4096, 256)))

    def test_two_identical_complete_backups_required(self):
        release = core.load_release(self.bundle)
        cases = [self.backup[:-1], self.backup + b"x", bytearray(self.backup), self.unit_backup(38)]
        for other in cases:
            with self.subTest(length=len(other), kind=type(other).__name__):
                with self.assertRaises(ValueError):
                    core.plan_install(release, self.backup, other, identity=core.STOCK_IDENTITY, jedec_hex=core.JEDEC_HEX)

    def test_unknown_identity_NOR_and_common_firmware_are_rejected(self):
        release = core.load_release(self.bundle)
        for identity, jedec in (("TANK MINI_008", core.JEDEC_HEX), ("TANK-G", core.JEDEC_HEX),
                                (core.STOCK_IDENTITY, "ef4014"), (core.STOCK_IDENTITY, "eb6015")):
            with self.subTest(identity=identity, jedec=jedec), self.assertRaises(ValueError):
                core.plan_install(release, self.backup, self.backup, identity=identity, jedec_hex=jedec)
        for address in (0, 0x38D0, 0x3FFF, 0x4000, 0x20000, 0x81FFF):
            changed = bytearray(self.backup)
            changed[address] ^= 1
            with self.subTest(address=address), self.assertRaises(ValueError):
                core.plan_install(release, bytes(changed), bytes(changed),
                                  identity=core.STOCK_IDENTITY, jedec_hex=core.JEDEC_HEX)

    def test_artifact_tampering_rejected_for_payloads_and_ELFs(self):
        for key, original in self.payloads.items():
            path = self.bundle / "assets" / key
            path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            with self.subTest(key=key), self.assertRaises(ValueError):
                core.load_release(self.bundle)
            path.write_bytes(original)

    def test_editing_manifest_hash_does_not_approve_new_firmware_or_plugins(self):
        for key in ("firmware", "writer", "reader", "reset"):
            original = self.manifest[key]["sha256"]
            for invalid in ("0" * 64, [], {"sha256": original}):
                self.manifest[key]["sha256"] = invalid
                self.write_manifest()
                with self.subTest(key=key, hash_type=type(invalid).__name__), self.assertRaisesRegex(ValueError, "Unapproved"):
                    core.load_release(self.bundle)
            self.manifest[key]["sha256"] = original
        for key in ("writer", "reader", "reset"):
            original = self.manifest[key]["elf_sha256"]
            self.manifest[key]["elf_sha256"] = "1" * 64
            self.write_manifest()
            with self.subTest(key=key + "_elf"), self.assertRaisesRegex(ValueError, "Unapproved"):
                core.load_release(self.bundle)
            self.manifest[key]["elf_sha256"] = original

    def test_asset_paths_reject_traversal_absolute_and_windows_aliases(self):
        for name in ("../firmware", "/assets/firmware", "C:/firmware", "assets\\firmware",
                     "assets/../firmware", "assets//firmware", "./assets/firmware", "assets/firmware:stream"):
            self.manifest["firmware"]["path"] = name
            self.write_manifest()
            with self.subTest(path=name), self.assertRaises(ValueError):
                core.load_release(self.bundle)
        self.manifest["firmware"]["path"] = "assets/firmware"
        self.manifest["writer"]["elf_path"] = "../writer_elf"
        self.write_manifest()
        with self.assertRaises(ValueError):
            core.load_release(self.bundle)

    def test_symlink_escape_is_rejected_if_platform_allows_symlinks(self):
        outside = Path(self.temp.name) / "outside.bin"
        outside.write_bytes(self.payloads["firmware"])
        link = self.bundle / "outside-link"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Creating symlinks is unavailable to this test process")
        self.manifest["firmware"]["path"] = "outside-link"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "leaves"):
            core.load_release(self.bundle)

    def test_true_or_missing_qualification_is_not_accepted(self):
        for key in core.QUALIFICATION_FLAGS:
            for value in (True, 0, None, "false"):
                self.manifest["qualification"][key] = value
                self.write_manifest()
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    core.load_release(self.bundle)
            del self.manifest["qualification"][key]
            self.write_manifest()
            with self.assertRaises(ValueError):
                core.load_release(self.bundle)
            self.manifest["qualification"][key] = False

    def test_manifest_framing_types_sizes_slots_and_build_tag(self):
        release_file = self.bundle / "release.json"
        good = release_file.read_bytes()
        for raw in (b'{"schema":1,"schema":1}', b"[]", b"\xff", b" " * 65537):
            release_file.write_bytes(raw)
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                core.load_release(self.bundle)
        release_file.write_bytes(good)
        for key, value in (("schema", True), ("application_range", [0, 0x100000]),
                           ("stock_usb", [0x4C4A, 0x8057]), ("rom_usb", [0x4C4A, 0xC755])):
            original = self.manifest[key]
            self.manifest[key] = value
            self.write_manifest()
            with self.subTest(key=key), self.assertRaises(ValueError):
                core.load_release(self.bundle)
            self.manifest[key] = original
        for key, field, value in (("writer", "slot", core.READER_SLOT), ("reader", "slot", core.WRITER_SLOT),
                                   ("reset", "slot", core.READER_SLOT), ("writer", "build_tag", 0),
                                   ("firmware", "bytes", 1), ("reset", "bytes", True)):
            original = self.manifest[key][field]
            self.manifest[key][field] = value
            self.write_manifest()
            with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                core.load_release(self.bundle)
            self.manifest[key][field] = original

    def test_existing_validator_still_rejects_gate_zero_ELF(self):
        from tools import build_mini_app_writer_operational as validator
        raw = self.payloads["writer_elf"]
        offset = validator._gate_location(raw)
        changed = raw[:offset] + bytes(4) + raw[offset + 4:]
        (self.bundle / "assets/writer_elf").write_bytes(changed)
        self.manifest["writer"]["elf_sha256"] = sha(changed)
        self.write_manifest()
        # Isolate structural validation after the independent artifact hash gate.
        with patch.object(core, "WRITER_ELF_SHA256", sha(changed)):
            with self.assertRaisesRegex(ValueError, "constant gate1"):
                core.load_release(self.bundle)

    def test_no_private_plan_or_build_inputs_are_consulted(self):
        from tools import install_mini_app, build_mini_app_writer_operational
        with patch.object(install_mini_app, "prepare_installation", side_effect=AssertionError("historical plan")), \
             patch.object(build_mini_app_writer_operational, "checked_inputs", side_effect=AssertionError("private input")):
            prepared = self.prepare()
            record = json.dumps(prepared.record)
            self.assertNotIn("my-mini-flash", record)
            self.assertNotIn("unit_backup", record)
            self.assertNotIn("artifacts/", record)
            self.assertEqual(prepared.record["backup_a_sha256"], sha(self.backup))
            self.assertFalse(prepared.record["physical_backup_acquisition_verified"])

    def test_manifests_and_records_are_copies_not_mutable_authority(self):
        prepared = self.prepare()
        release_view = prepared.release.manifest
        release_view["qualification"]["direct_stock_to_v3"] = True
        record_view = prepared.record
        record_view["backup_a_sha256"] = "0" * 64
        self.assertFalse(prepared.release.manifest["qualification"]["direct_stock_to_v3"])
        self.assertEqual(prepared.record["backup_a_sha256"], sha(self.backup))
        altered = replace(prepared.release, firmware=bytes(len(prepared.release.firmware)))
        with self.assertRaises(ValueError):
            core.plan_install(altered, self.backup, self.backup, identity=core.STOCK_IDENTITY, jedec_hex=core.JEDEC_HEX)

    def test_final_read_requires_exact_application_and_every_external_byte(self):
        prepared = self.prepare()
        for address in (0, 0x3FFF, 0x4000, 0x819FF, 0x82000, 0xB7000, 0xBCFFF,
                        0xBE000, 0xBF000, 0xFEFFF, 0xFF000, 0xFFFFF):
            changed = bytearray(prepared.expected_full)
            changed[address] ^= 1
            with self.subTest(address=address), self.assertRaises(ValueError):
                core.validate_completed(prepared, bytes(changed))
        for raw in (prepared.expected_full[:-1], prepared.expected_full + b"x", bytearray(prepared.expected_full)):
            with self.assertRaises(ValueError):
                core.validate_completed(prepared, raw)

    def test_final_validation_does_not_promote_boot_audio_or_recovery(self):
        prepared = self.prepare()
        result = core.validate_completed(prepared, prepared.expected_full)
        self.assertTrue(result["application_exact"])
        self.assertTrue(result["external_regions_unchanged"])
        self.assertEqual(result["full_after_sha256"], sha(prepared.expected_full))
        self.assertEqual(result["qualification"], {key: False for key in core.QUALIFICATION_FLAGS})
        for key in ("device_access_performed", "boot_verified", "audio_verified"):
            self.assertIs(result[key], False)
        self.assertEqual(result["validation_scope"], "supplied-full-read-bytes-only")

    def test_forged_expected_image_or_plan_record_is_rejected(self):
        prepared = self.prepare()
        changed = prepared.expected_full[:-1] + bytes([prepared.expected_full[-1] ^ 1])
        with self.assertRaises(ValueError):
            core.validate_completed(replace(prepared, expected_full=changed), changed)
        record = prepared.record
        record["expected_full_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            core.validate_completed(replace(prepared, _record_raw=json.dumps(record).encode()), prepared.expected_full)

    def test_optional_reader_ELF_and_additive_release_metadata(self):
        self.manifest["kind"] = "hyperrig-mini-installer-preview"
        self.manifest["editor"] = {"entry": "editor/web/tankmini.html"}
        self.manifest["provenance"] = {"description": "Public artifacts only"}
        del self.manifest["reader"]["elf_path"]
        del self.manifest["reader"]["elf_sha256"]
        self.write_manifest()
        release = core.load_release(self.bundle)
        self.assertIsNone(release.reader_elf)
        self.assertEqual(release.manifest["kind"], "hyperrig-mini-installer-preview")

    def test_v4_release_plan_and_final_application_use_the_actual_new_artifact(self):
        payload = self.use_one_switch_release()
        release = core.load_release(self.bundle)
        self.assertEqual(release.firmware, payload)
        prepared = self.prepare()
        self.assertEqual(prepared.record["kind"], "portable-stock-to-v4-plan")
        self.assertEqual(prepared.record["candidate_sha256"], ONE_SWITCH_SHA256)
        self.assertEqual(prepared.installation.candidate, payload)
        self.assertEqual(prepared.expected_full[core.APP_START:core.APP_END], payload)
        self.assertEqual(prepared.installation.sector_order[-1], core.APP_START)
        self.assertEqual(prepared.record["sectors"][-1]["page_order"][-1], core.APP_START)
        self.assertEqual(prepared.record["qualification"], {key: False for key in ONE_SWITCH_QUALIFICATION})
        result = core.validate_completed(prepared, prepared.expected_full)
        self.assertTrue(result["verified"])
        self.assertEqual(result["full_after_sha256"], sha(prepared.expected_full))

    def test_v4_two_synthetic_units_keep_their_distinct_complete_external_bytes(self):
        payload = self.use_one_switch_release()
        prepared_a = self.prepare(self.unit_backup(21))
        prepared_b = self.prepare(self.unit_backup(187))
        self.assertNotEqual(prepared_a.installation.backup_sha256, prepared_b.installation.backup_sha256)
        self.assertNotEqual(prepared_a.installation.plan_sha256, prepared_b.installation.plan_sha256)
        self.assertNotEqual(sha(prepared_a.expected_full), sha(prepared_b.expected_full))
        for prepared in (prepared_a, prepared_b):
            self.assertEqual(prepared.expected_full[core.APP_START:core.APP_END], payload)
            self.assertEqual(prepared.expected_full[:core.APP_START], prepared.backup[:core.APP_START])
            self.assertEqual(prepared.expected_full[core.APP_END:], prepared.backup[core.APP_END:])
            for region in prepared.record["preserved_regions"]:
                start, end = region["range"]
                self.assertEqual(region["sha256"], sha(prepared.backup[start:end]))
                self.assertEqual(prepared.expected_full[start:end], prepared.backup[start:end])
            self.assertTrue(core.validate_completed(prepared, prepared.expected_full)["external_regions_unchanged"])

    def test_v4_rejects_legacy_or_mixed_qualification_labels(self):
        self.use_one_switch_release()
        variants = ({key: False for key in core.QUALIFICATION_FLAGS},
                    {key: False for key in (*ONE_SWITCH_QUALIFICATION, "direct_stock_to_v3")},
                    {"direct_stock_to_v4": False, "cold_boot_recovery": False})
        for qualification in variants:
            self.manifest["qualification"] = qualification
            self.write_manifest()
            with self.subTest(qualification=qualification), self.assertRaisesRegex(ValueError, "qualification"):
                core.load_release(self.bundle)

    def test_v4_rejects_falsely_promoted_or_non_boolean_qualification(self):
        self.use_one_switch_release()
        for key in ONE_SWITCH_QUALIFICATION:
            for value in (True, 0, None, "false"):
                self.manifest["qualification"] = {name: False for name in ONE_SWITCH_QUALIFICATION}
                self.manifest["qualification"][key] = value
                self.write_manifest()
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, "qualification"):
                    core.load_release(self.bundle)

    def test_v4_manifest_does_not_accept_v3_payload_or_swapped_Release_bytes(self):
        payload = self.use_one_switch_release()
        release = core.load_release(self.bundle)
        (self.bundle / "assets/firmware").write_bytes(self.payloads["firmware"])
        with self.assertRaisesRegex(ValueError, "firmware"):
            core.load_release(self.bundle)
        with self.assertRaisesRegex(ValueError, "firmware"):
            core.plan_install(replace(release, firmware=self.payloads["firmware"]), self.backup, self.backup,
                              identity=core.STOCK_IDENTITY, jedec_hex=core.JEDEC_HEX)
        # The opposite mismatch must not silently select v4 either.
        (self.bundle / "assets/firmware").write_bytes(payload)
        self.manifest["firmware"]["sha256"] = core.FIRMWARE_SHA256
        self.manifest["qualification"] = {key: False for key in core.QUALIFICATION_FLAGS}
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "firmware"):
            core.load_release(self.bundle)

    def test_v4_completed_validation_rejects_v3_and_never_claims_hardware_success(self):
        self.use_one_switch_release()
        prepared = self.prepare()
        old_image = prepared.backup[:core.APP_START]+self.payloads["firmware"]+prepared.backup[core.APP_END:]
        with self.assertRaisesRegex(ValueError, "application"):
            core.validate_completed(prepared, old_image)
        damaged = bytearray(prepared.expected_full)
        damaged[0xB7000] ^= 1
        with self.assertRaisesRegex(ValueError, "preserved region"):
            core.validate_completed(prepared, bytes(damaged))
        result = core.validate_completed(prepared, prepared.expected_full)
        self.assertEqual(result["validation_scope"], "supplied-full-read-bytes-only")
        self.assertEqual(result["qualification"], {key: False for key in ONE_SWITCH_QUALIFICATION})
        for key in ("boot_verified", "audio_verified", "device_access_performed"):
            self.assertIs(result[key], False)
        self.assertFalse(prepared.record["physical_backup_acquisition_verified"])
        self.assertFalse(prepared.record["device_access_performed"])
        self.assertFalse(prepared.record["power_loss_atomicity_proven"])


if __name__ == "__main__":
    unittest.main()
