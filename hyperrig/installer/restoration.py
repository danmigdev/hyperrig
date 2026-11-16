"""Restore this development MINI's stock application with sealed release tools.

The historical restoration planner binds old documentation hashes. This
separate adapter validates the shipped writer ELF/payload and reuses the frozen
StockRestoration contract and full-read validator without changing old pins.
"""
from __future__ import annotations

from . import core
from .service import InstallWorkflow
from tools.install_mini_app import Installation
from tools import restore_mini_stock as frozen

require, sha = core._require, core._sha


def prepare_restoration(release, first, second, stock, *, jedec_hex):
    core._validate_release(release, inspect_elf=True)
    require(release.manifest["firmware"]["sha256"] == core.ONE_SWITCH_FIRMWARE_SHA256,
            "The restoration transport package must be the pinned v4 release")
    require(jedec_hex == core.JEDEC_HEX, "Unsupported NOR JEDEC identity")
    require(type(stock) is bytes and len(stock) == core.CAPACITY and sha(stock) == frozen.BACKUP_SHA,
            "This MINI's exact original full backup is required")
    require(sha(stock[:core.APP_START]) == core.STOCK_SPL_SHA256
            and sha(stock[core.APP_START:core.APP_END]) == core.STOCK_APP_SHA256,
            "Original backup does not contain the approved stock application")
    for raw in (first, second):
        require(type(raw) is bytes and len(raw) == core.CAPACITY, "Two complete immutable backups required")
        require(raw[:core.APP_START] == stock[:core.APP_START] and raw[0xFF000:] == stock[0xFF000:],
                "Current SPL or key/MAC does not match the original unit backup")
        require(sha(raw[core.APP_START:core.APP_END]) == core.ONE_SWITCH_FIRMWARE_SHA256,
                "The fresh application must be the exact installed v4 image")
    require(first == second, "The two current full backups differ")
    target = stock[core.APP_START:core.APP_END]
    expected = first[:core.APP_START] + target + first[core.APP_END:]
    addresses = [a for a in range(core.APP_START, core.APP_END, 4096)
                 if first[a:a + 4096] != expected[a:a + 4096]]
    order = tuple(a for a in addresses if a != core.APP_START) + ((core.APP_START,) if core.APP_START in addresses else ())
    from tools.build_mini_app_writer_operational import page_order
    record = {
        "schema": 1, "kind": "mini-stock-app-restoration", "target": "tank-mini",
        "planner": "sealed-release-v4-to-same-unit-stock-v1",
        "release_sha256": release.manifest_sha256,
        "fresh_full_read": {"sha256": sha(first), "bytes": len(first)},
        "second_full_read": {"sha256": sha(second), "bytes": len(second)},
        "stock_backup": {"path": frozen.BACKUP_PATH, "sha256": frozen.BACKUP_SHA, "bytes": len(stock)},
        "preimage_app_sha256": core.ONE_SWITCH_FIRMWARE_SHA256,
        "target_app_sha256": core.STOCK_APP_SHA256,
        "physical_write_allowlist": [core.APP_START, core.APP_END],
        "sector_order": list(order), "changed_sectors": len(order),
        "sectors": [{"address": a, "preimage_sha256": sha(first[a:a + 4096]),
                     "target_sha256": sha(expected[a:a + 4096]), "page_order": page_order(a)} for a in order],
        "preserved_regions": [frozen.region_evidence(first, stock, *region) for region in core.PRESERVED_REGIONS],
        "factory_OTA_regions": [frozen.region_evidence(first, stock, "factory_staged_OTA", 0xB7000, 0xBD000)],
        "expected_full_readback_sha256": sha(expected),
        "expected_full_readback_equals_historical_backup": expected == stock,
        "writer_sha256": core.WRITER_SHA256, "writer_ELF_sha256": core.WRITER_ELF_SHA256,
        "header_sector_last": True, "header_page_last": True,
        "historical_presets_restored_claimed": False, "device_access_performed": False,
        "automatic_reset": False, "automatic_rollback": False, "power_loss_atomicity_proven": False,
    }
    raw = frozen.canonical(record)
    spec = Installation(
        slot=core.WRITER_SLOT, build_tag=core.WRITER_BUILD_TAG, image=release.writer,
        image_sha256=core.WRITER_SHA256, elf_sha256=core.WRITER_ELF_SHA256,
        manifest_sha256=release.manifest_sha256, plan_sha256=sha(raw),
        candidate=target, preimage=first[core.APP_START:core.APP_END],
        backup_sha256=frozen.BACKUP_SHA, sector_order=order, purpose="restore-stock",
        fresh_full_read_sha256=sha(first))
    return frozen.StockRestoration(spec, first, stock, raw)


class RestorationWorkflow(InstallWorkflow):
    def __init__(self, release, backend, destination, stock, *, notify=None):
        require(type(stock) is bytes and sha(stock) == frozen.BACKUP_SHA, "Original unit backup required")
        self.stock = stock
        super().__init__(release, backend, destination, notify=notify)

    def backup(self, selection):
        def run():
            self._phase("identifying", "Identifying HyperRig before entering ROM")
            self.backend.enter_hyperrig_rom(selection, self.release, self.store)
            self._phase("backing_up", "Saving two complete copies of the current HyperRig flash")
            first = self.backend.read_full(self.release, self.store, self.progress, "backup-a")
            self.store.save_bytes("hyperrig-flash-a.bin", first)
            second = self.backend.read_full(self.release, self.store, self.progress, "backup-b")
            self.store.save_bytes("hyperrig-flash-b.bin", second)
            self.prepared = prepare_restoration(self.release, first, second, self.stock,
                                                jedec_hex=self.backend.jedec_hex)
            self.store.save_bytes("restoration-plan.json", self.prepared.plan_bytes)
            self._phase("backed_up", "Matching backups verified; stock restoration ready")
            return self.prepared.summary()
        return self._action({"created"}, run)

    def install(self):
        def run():
            rebuilt = prepare_restoration(self.release, self.prepared.full_preimage,
                self.prepared.full_preimage, self.stock, jedec_hex=self.backend.jedec_hex)
            require(self.prepared == rebuilt, "Prepared restoration changed")
            self._phase("checking_preimage", "Checking current flash against both saved backups")
            before = self.backend.read_full(self.release, self.store, self.progress, "pre-install")
            self.store.save_bytes("full-before.bin", before)
            require(before == self.prepared.full_preimage, "Flash changed after backup; no erase is allowed")
            self._phase("installing", "Restoring the original M-VAVE application")
            self.backend.write_application(self.prepared.installation, self.store, self.progress)
            self._phase("verifying", "Verifying the full stock application and preserved unit data")
            after = self.backend.read_full(self.release, self.store, self.progress, "full-after")
            self.store.save_bytes("full-after.bin", after)
            result = frozen.validate_restored_full(self.prepared, after)
            self.store.save_json("verification.json", result)
            self._phase("verified", "Stock application and preserved data verified; boot is a separate step")
            return result
        return self._action({"backed_up"}, run)

    def boot(self):
        def run():
            self._phase("booting", "Starting the original M-VAVE firmware")
            result = self.backend.boot(self.release, self.store, expected="stock")
            self.store.save_json("boot-observation.json", result)
            self._phase("stock_usb_detected", "Stock USB detected; stock identity remains to be checked")
            return result
        return self._action({"verified"}, run)

    def cancel_to_stock(self):
        raise ValueError("Stock boot is available only after verified restoration")
