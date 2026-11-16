"""Assembled any-one policy, exact v3 reversal and full application layout."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from firmware.mini.entry_recovery_one import verify
from hyperrig.jieli import crc16, sfc, unpack_app
from tools import build_mini_entry_recovery_one as builder
from tools.audit_mini_ultrarig_port import repack_header


class AnyOneRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(dir=builder.ROOT/"build", prefix="TEST-any-one-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)/"candidate"
        cls.report = builder.build(cls.output)
        cls.baseline = builder.load_baseline()
        cls.image = (cls.output/"hyperrig-mini.app-area.bin").read_bytes()
        cls.guard = (cls.output/"guard/entry-recovery-one.bin").read_bytes()
        cls.elf = (cls.output/"guard/entry-recovery-one.elf").read_bytes()
        cls.recovery = json.loads((cls.output/"entry-recovery-manifest.json").read_text(encoding="utf-8"))

    def test_assembled_model_covers_all_subsets_faults_and_release_positions(self):
        model = self.recovery["model_tests"]
        self.assertEqual(model["cases"], 1038)
        self.assertEqual(model["constant_levels"], 512)
        self.assertEqual(model["configuration_faults"], 64)
        self.assertEqual(model["all_released_at_each_sample"], 448)
        self.assertEqual(model["changing_held_subset"], 14)
        self.assertEqual(model["maximum_stack_bytes"], 100)
        self.assertEqual(model["SP_alias_models"], 2)
        self.assertTrue(model["all_GPRs_PSR_RETS_RETI_restored_on_resume"])
        self.assertTrue(model["foreign_GPIO_bits_preserved"])
        self.assertTrue(model["selected_direction_remains_input"])

    def test_individual_switches_recover_but_one_all_released_sample_resumes(self):
        _, symbols, _ = verify.inspect_elf(self.elf, self.baseline["v2"]["guard_bytes"])
        rows = verify.original.instructions(self.guard, verify.ADDRESS, verify.ADDRESS, verify.NEW_END)
        gp, _, _ = unpack_app(self.baseline["g"])
        hook = builder.guard_v2.patches(gp, verify.ADDRESS)[0]
        entry = verify.original.instructions(hook.after, verify.original.HOOK,
                                             verify.original.HOOK, verify.original.RESUME)
        code = {row["address"]: row for row in rows+entry}
        names = {name: value["address"] for name, value in symbols.items()}
        for pin in (0, 3, 10):
            low = verify.original.MASK ^ (1 << pin)
            with self.subTest(pin=pin, held=True):
                machine = verify.previous.PolicyMachine(code, names, verify.ADDRESS, 2, [low], 0)
                self.assertEqual(machine.run(), "reset_wait")
                self.assertEqual(machine.samples, 32)
                self.assertEqual(machine.delay_iterations, 3300000)
                machine.check_gpio_restore()
            with self.subTest(pin=pin, released_at_last=True):
                machine = verify.previous.PolicyMachine(code, names, verify.ADDRESS, 2,
                                                         [low]*31+[verify.original.MASK], 0)
                self.assertEqual(machine.run(), "startup_resume")
                self.assertEqual(machine.samples, 32)
                self.assertEqual(machine.delay_iterations, 3200000)
                self.assertFalse(any(address == verify.original.RESET for address, _ in machine.writes))

    def test_only_sample_predicate_and_required_branch_relocations_change_guard(self):
        delta = verify.verify_minimal_delta(self.baseline["v2"]["guard_bytes"], self.guard)
        self.assertEqual(delta["predicate"]["before"]["bytes"], "8049")
        self.assertEqual(delta["predicate"]["after"]["bytes"], "05e80900")
        self.assertEqual(delta["predicate"]["after"]["target"], 0x0207748A)
        self.assertEqual(len(delta["relocations"]), 7)
        self.assertEqual(self.guard[-54:], self.baseline["v2"]["guard_bytes"][-54:])
        self.assertTrue(self.recovery["vendor_disassembly_matches_independent_decoder"])

    def test_wrong_predicate_gpio_mask_and_reset_instructions_are_rejected(self):
        offset = verify.SAMPLE_BRANCH-verify.ADDRESS
        for label, at, xor in (("not_equal_predicate", offset, 0x80),
                               ("GPIO_mask", 0x02077406-verify.ADDRESS, 1),
                               ("reset_marker", len(self.guard)-46, 1),
                               ("foreign_policy_instruction", 0x020773E4-verify.ADDRESS, 1)):
            with self.subTest(label=label):
                changed = bytearray(self.guard)
                changed[at] ^= xor
                with self.assertRaises(ValueError):
                    verify.verify_minimal_delta(self.baseline["v2"]["guard_bytes"], bytes(changed))
        with self.assertRaises(ValueError):
            verify.verify_minimal_delta(self.guard, self.guard)
        with self.assertRaises(ValueError):
            verify.verify_minimal_delta(self.baseline["v2"]["guard_bytes"], self.guard[:-2])

    def test_ELF_entry_LMA_BSS_permissions_and_payload_tampering_are_rejected(self):
        phoff = struct.unpack_from("<I", self.elf, 28)[0]
        fileoff = struct.unpack_from("<I", self.elf, phoff+4)[0]
        mutations = (("entry", 24, verify.ADDRESS+4),
                     ("LMA", phoff+12, verify.ADDRESS+4),
                     ("BSS", phoff+20, len(self.guard)+4),
                     ("permissions", phoff+24, 7))
        for label, offset, value in mutations:
            with self.subTest(label=label):
                changed = bytearray(self.elf)
                struct.pack_into("<I", changed, offset, value)
                with self.assertRaises(ValueError):
                    verify.inspect_elf(bytes(changed), self.baseline["v2"]["guard_bytes"])
        changed = bytearray(self.elf)
        changed[fileoff+verify.SAMPLE_BRANCH-verify.ADDRESS] ^= 0x80
        with self.assertRaises(ValueError):
            verify.inspect_elf(bytes(changed), self.baseline["v2"]["guard_bytes"])

    def test_complete_image_crc_extents_and_exact_two_sector_delta(self):
        plain, entries, files = unpack_app(self.image)
        old_plain, old_entries, old_files = unpack_app(self.baseline["image"])
        audit = self.report["validation"]
        self.assertEqual(len(self.image), 0x7E000)
        self.assertEqual(builder.sha(self.image), "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2")
        self.assertEqual([row["physical_address"] for row in audit["changed_sectors_vs_v3"]], [0x4000, 0x7B000])
        self.assertEqual([row["changed_bytes"] for row in audit["changed_sectors_vs_v3"]], [14, 360])
        self.assertEqual(entries[1].size, old_entries[1].size+2)
        self.assertEqual(entries[2].offset, old_entries[2].offset+2)
        self.assertEqual(entries[0].size, old_entries[0].size+2)
        self.assertEqual(entries[2].offset, 0x774F4)
        self.assertEqual(entries[0].size, 0x77673)
        self.assertEqual(audit["SFC_encoding_end_unchanged"], 0x77680)
        self.assertEqual(files["cfg_tool.bin"], old_files["cfg_tool.bin"])
        self.assertEqual([row.to_dict() for row in entries[3:]], [row.to_dict() for row in old_entries[3:]])
        self.assertEqual(plain[0x67E:0x684], bytes.fromhex("c1fff4740702"))
        self.assertEqual(plain[0x1B8:0x1BE], old_plain[0x1B8:0x1BE])
        self.assertEqual(plain[0x1DC:0x1E2], old_plain[0x1DC:0x1E2])

    def test_actual_original_application_and_audio_ranges_are_identical(self):
        _, _, old_files = unpack_app(self.baseline["image"])
        _, _, files = unpack_app(self.image)
        for row in self.report["validation"]["unchanged_executable_ranges"]:
            start, end = row["cpu_start"]-builder.ENTRY, row["cpu_end_exclusive"]-builder.ENTRY
            self.assertEqual(files["app.bin"][start:end], old_files["app.bin"][start:end])
            self.assertEqual(builder.sha(files["app.bin"][start:end]), row["sha256"])
        audio = self.baseline["v2"]["audio_bytes"]
        self.assertEqual(len(audio), 2332)
        self.assertEqual(files["app.bin"][0x2076AAC-builder.ENTRY:verify.ADDRESS-builder.ENTRY], audio)

    def test_inverse_recomputes_headers_and_encryption_to_exact_v3(self):
        self.assertEqual(builder.reverse_revision(self.image, self.baseline), self.baseline["image"])
        self.assertTrue(self.report["validation"]["inverse_headers_CRC_and_SFC_recovers_complete_v3_image"])
        # A different original instruction with repaired JLFS CRCs is still
        # rejected: CRC validity alone must never be treated as a narrow patch.
        plain, entries, _ = unpack_app(self.image)
        changed = bytearray(plain)
        changed[0x300] ^= 1
        app = changed[entries[1].offset:entries[1].offset+entries[1].size]
        changed[32:64] = repack_header(changed[32:64], data_crc=crc16(app))
        changed[:32] = repack_header(changed[:32], data_crc=crc16(changed[32:entries[0].size]))
        end = (entries[0].size+31) & ~31
        encoded = sfc(bytes(changed[:end]))+bytes(changed[end:])
        unpack_app(encoded)  # Deliberately valid CRCs; the inverse must reject.
        with self.assertRaises(ValueError):
            builder.reverse_revision(encoded, self.baseline)

    def test_report_changed_ranges_exactly_cover_encoded_and_decoded_differences(self):
        old_plain, _, _ = unpack_app(self.baseline["image"])
        plain, _, _ = unpack_app(self.image)
        for key, before, after in (("encoded_changed_ranges", self.baseline["image"], self.image),
                                    ("decoded_changed_ranges", old_plain, plain)):
            covered = set()
            for row in self.report["validation"][key]:
                start = row["area_offset"]
                end = start+row["bytes"]
                self.assertEqual(before[start:end].hex(), row["before_hex"])
                self.assertEqual(after[start:end].hex(), row["after_hex"])
                self.assertEqual(row["physical_start"], start+0x4000)
                self.assertFalse(covered.intersection(range(start, end)))
                covered.update(range(start, end))
            self.assertEqual(covered, {i for i, (a, b) in enumerate(zip(before, after)) if a != b})

    def test_stale_baseline_audio_or_patch_metadata_is_rejected(self):
        for fault in ("image", "audio", "end", "original_source", "patch"):
            data = copy.deepcopy(self.baseline)
            with self.subTest(fault=fault):
                if fault == "image":
                    data["image"] = data["image"][:-1]+b"\0"
                elif fault == "audio":
                    data["v2"]["audio_bytes"] = b"\0"+data["v2"]["audio_bytes"][1:]
                elif fault == "end":
                    data["composition"]["head_end"] += 2
                elif fault == "original_source":
                    data["g"] = data["g"][:-1]+b"\0"
                else:
                    data["v2"]["integration"]["composition"]["patches"][-1]["after_hex"] = "00"
                with self.assertRaises(ValueError):
                    builder.compose_revision(data, self.guard)

    def test_manifest_preserves_historical_qualification_and_never_grants_v4_writes(self):
        manifest = json.loads((self.output/"firmware-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["image_sha256"], builder.sha(self.image))
        self.assertEqual(manifest["revision"], 4)
        self.assertEqual(manifest["entry_recovery"]["policy"], builder.POLICY)
        self.assertFalse(manifest["hardware_verified"] or manifest["flashable"])
        self.assertFalse(manifest["capabilities"]["write"] or manifest["capabilities"]["panel"])
        self.assertEqual(manifest["command_capabilities"], {})
        self.assertEqual(manifest["family_capabilities"], {})
        self.assertFalse(self.report["cold_boot_recovery_verified"])
        self.assertFalse(self.report["boot_verified_on_mini"] or self.report["audio_verified_on_mini"])
        self.assertFalse(self.report["installer_approved_firmware_changed"])
        self.assertFalse(self.recovery["USB_enumeration_verified"])
        self.assertTrue(builder.POLICY["held_subset_may_change_between_samples"])
        for name, digest in self.report["frozen_input_sha256"].items():
            self.assertEqual(builder.sha((builder.ROOT/name).read_bytes()), digest)

    def test_existing_or_outside_output_is_rejected_without_overwriting(self):
        before = (self.output/"integration-report.json").read_bytes()
        for output in (self.output, builder.ROOT/builder.BASELINE, builder.ROOT/"firmware/forbidden"):
            with self.subTest(output=output), self.assertRaises(ValueError):
                builder.build(output)
        self.assertEqual((self.output/"integration-report.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
