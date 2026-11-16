"""Exact v3-to-v4 upgrade, preserving data from two fresh complete reads.

This development workflow is separate from the stock installer. It reuses its
writer and state machine without changing sealed releases or historical proof.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from . import core
from .service import InstallWorkflow

SECTOR_ORDER = (0x7B000, core.APP_START)
require, sha = core._require, core._sha


@dataclass(frozen=True)
class PreparedUpgrade:
    release: core.Release
    installation: object
    backup: bytes
    expected_full: bytes
    _record_raw: bytes

    @property
    def record(self):
        return json.loads(self._record_raw)


def plan_upgrade(release, first, second, *, jedec_hex):
    manifest = core._validate_release(release, inspect_elf=True)
    require(manifest["firmware"]["sha256"] == core.ONE_SWITCH_FIRMWARE_SHA256,
            "The upgrade target must be the exact one-switch v4 release")
    require(jedec_hex == core.JEDEC_HEX, "Unsupported NOR JEDEC identity")
    for raw in (first, second):
        require(type(raw) is bytes and len(raw) == core.CAPACITY,
                "Two complete immutable 1 MiB backups are required")
        require(sha(raw[:core.APP_START]) == core.STOCK_SPL_SHA256,
                "Unknown SPL/boot configuration")
        require(sha(raw[core.APP_START:core.APP_END]) == core.FIRMWARE_SHA256,
                "The installed application must be the exact v3 image")
    require(first == second, "The two complete backups differ")
    expected = first[:core.APP_START] + release.firmware + first[core.APP_END:]
    changed = [a for a in range(core.APP_START, core.APP_END, core.SECTOR_BYTES)
               if first[a:a + core.SECTOR_BYTES] != expected[a:a + core.SECTOR_BYTES]]
    require(changed == sorted(SECTOR_ORDER), "Unexpected changed sectors in the v3-to-v4 upgrade")
    from tools.install_mini_app import Installation
    from tools.build_mini_app_writer_operational import page_order

    record = {
        "schema": 1, "project": "HyperRig", "target": "tank-mini",
        "kind": "mini-v3-to-v4-one-switch-upgrade",
        "release_sha256": release.manifest_sha256,
        "preimage_app_sha256": core.FIRMWARE_SHA256,
        "candidate_sha256": core.ONE_SWITCH_FIRMWARE_SHA256,
        "backup_a_sha256": sha(first), "backup_b_sha256": sha(second),
        "expected_full_sha256": sha(expected), "jedec_hex": jedec_hex,
        "application_range": [core.APP_START, core.APP_END],
        "changed_sectors": len(SECTOR_ORDER), "sector_order": list(SECTOR_ORDER),
        "sectors": [{"address": a, "bytes": core.SECTOR_BYTES,
                     "preimage_sha256": sha(first[a:a + core.SECTOR_BYTES]),
                     "candidate_sha256": sha(expected[a:a + core.SECTOR_BYTES]),
                     "page_order": page_order(a)} for a in SECTOR_ORDER],
        "preserved_regions": core._preserved(first),
        "header_sector_last": True, "header_page_last": True,
        "power_loss_atomicity_proven": False, "device_access_performed": False,
        "automatic_reset": False, "automatic_rollback": False,
        "qualification": manifest["qualification"],
    }
    spec = Installation(
        slot=core.WRITER_SLOT, build_tag=core.WRITER_BUILD_TAG,
        image=release.writer, image_sha256=core.WRITER_SHA256,
        elf_sha256=core.WRITER_ELF_SHA256, manifest_sha256=release.manifest_sha256,
        plan_sha256=sha(core._canonical(record)), candidate=release.firmware,
        preimage=first[core.APP_START:core.APP_END], backup_sha256=sha(first),
        sector_order=SECTOR_ORDER, fresh_full_read_sha256=sha(first))
    record.update(plan_sha256=spec.plan_sha256, installation=spec.summary())
    return PreparedUpgrade(release, spec, first, expected, core._canonical(record))


def validate_completed(prepared, after):
    require(isinstance(prepared, PreparedUpgrade), "A prepared v3-to-v4 upgrade is required")
    rebuilt = plan_upgrade(prepared.release, prepared.backup, prepared.backup,
                           jedec_hex=core.JEDEC_HEX)
    require(prepared == rebuilt, "The prepared upgrade was changed")
    require(type(after) is bytes and len(after) == core.CAPACITY, "Final full 1 MiB read required")
    for name, start, end in core.PRESERVED_REGIONS:
        require(after[start:end] == prepared.backup[start:end], "Changed preserved region: " + name)
    require(after == prepared.expected_full, "Final application differs from the exact v4 target")
    return {"kind": "mini-v3-to-v4-completed-byte-validation", "verified": True,
            "plan_sha256": prepared.installation.plan_sha256,
            "release_sha256": prepared.release.manifest_sha256,
            "candidate_sha256": core.ONE_SWITCH_FIRMWARE_SHA256,
            "full_after_sha256": sha(after), "bytes": len(after),
            "application_exact": True, "external_regions_unchanged": True,
            "device_access_performed": False, "boot_verified": False,
            "audio_verified": False, "cold_boot_recovery_verified": False}


class UpgradeWorkflow(InstallWorkflow):
    """Keep backup, installation, complete verification, and boot separate."""

    def backup(self, selection):
        def run():
            require(self.release.manifest["firmware"]["sha256"] == core.ONE_SWITCH_FIRMWARE_SHA256,
                    "The upgrade target must be v4")
            self._phase("identifying", "Identifying HyperRig before one ROM-entry request")
            self.backend.enter_hyperrig_rom(selection, self.release, self.store)
            self._phase("backing_up", "Reading two complete copies of the current pedal")
            first = self.backend.read_full(self.release, self.store, self.progress, "backup-a")
            self.store.save_bytes("v3-flash-a.bin", first)
            second = self.backend.read_full(self.release, self.store, self.progress, "backup-b")
            self.store.save_bytes("v3-flash-b.bin", second)
            self.prepared = plan_upgrade(self.release, first, second, jedec_hex=self.backend.jedec_hex)
            self.store.save_json("installation-plan.json", self.prepared.record)
            self._phase("backed_up", "Matching v3 backups verified; two-sector upgrade ready")
            return self.prepared.record
        return self._action({"created"}, run)

    def install(self):
        def run():
            require(self.prepared == plan_upgrade(self.release, self.prepared.backup,
                    self.prepared.backup, jedec_hex=self.backend.jedec_hex), "Upgrade plan changed")
            self._phase("checking_preimage", "Checking the current flash against both backups")
            fresh = self.backend.read_full(self.release, self.store, self.progress, "pre-install")
            self.store.save_bytes("full-before.bin", fresh)
            require(fresh == self.prepared.backup, "Flash changed after backup; no erase is allowed")
            self._phase("installing", "Writing the two approved application sectors")
            self.backend.write_application(self.prepared.installation, self.store, self.progress)
            self._phase("verifying", "Reading the full flash and checking all preserved bytes")
            after = self.backend.read_full(self.release, self.store, self.progress, "full-after")
            self.store.save_bytes("full-after.bin", after)
            result = validate_completed(self.prepared, after)
            self.store.save_json("verification.json", result)
            self._phase("verified", "Exact v4 image and preserved data verified; boot is a separate action")
            return result
        return self._action({"backed_up"}, run)

    def cancel_to_stock(self):
        raise ValueError("This workflow upgrades HyperRig; stock restoration is a separate procedure")
