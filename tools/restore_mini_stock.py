"""Prepare an explicit app-only stock restoration from a retained fresh NOR read.

Import and CLI perform local file operations only. A separate runner owns the
fresh full-read evidence, ROM/slot lifecycle, operational transport and journal.
The reusable session restores the app and remains in ROM; it never resets,
retries, writes other regions or claims that historical presets were restored.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import install_mini_app as installer
from tools.audit_mini_ultrarig_port import BACKUP_PATH, BACKUP_SHA

APP_START, APP_END = installer.APP_START, installer.APP_END
CAPACITY, SECTOR = 0x100000, 4096
sha, require = installer.sha, installer.require
PRESERVED = (
    ("factory_SPL_and_boot_configuration", 0, APP_START),
    ("VM_including_factory_staged_updater", APP_END, 0xBE000),
    ("BTIF", 0xBE000, 0xBF000),
    ("USR", 0xBF000, 0xFF000),
    ("key_mac", 0xFF000, CAPACITY),
)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(value):
    require(isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value), "explicit lowercase SHA256 required")
    return value


def retained_file(path):
    path = installer.frozen.workspace_file(path)
    data = path.read_bytes()
    return data, {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(data), "bytes": len(data)}


def region_evidence(current, stock, name, start, end):
    present, original = current[start:end], stock[start:end]
    changed = [a for a in range(start, end, SECTOR)
               if current[a:a + SECTOR] != stock[a:a + SECTOR]]
    return {"name": name, "range": [start, end], "bytes": end - start,
            "fresh_sha256": sha(present), "stock_backup_sha256": sha(original),
            "differs_from_stock_backup": present != original,
            "differing_bytes": sum(a != b for a, b in zip(present, original)),
            "differing_sector_addresses": changed, "write_allowed": False,
            "expected_after_sha256": sha(present)}


@dataclass(frozen=True)
class StockRestoration:
    installation: installer.Installation
    full_preimage: bytes
    stock_backup: bytes
    plan_bytes: bytes

    def __post_init__(self):
        require(type(self.full_preimage) is bytes and type(self.stock_backup) is bytes
                and len(self.full_preimage) == len(self.stock_backup) == CAPACITY,
                "immutable complete 1MiB preimage and stock backup required")
        require(sha(self.stock_backup) == BACKUP_SHA, "wrong unit stock backup")
        spec = self.installation
        require(isinstance(spec, installer.Installation) and spec.purpose == "restore-stock"
                and spec.fresh_full_read_sha256 == sha(self.full_preimage)
                and spec.backup_sha256 == BACKUP_SHA, "restoration identity/provenance differs")
        require(spec.candidate == self.stock_backup[APP_START:APP_END]
                and spec.preimage == self.full_preimage[APP_START:APP_END],
                "restoration application bytes differ")
        require(self.full_preimage[:APP_START] == self.stock_backup[:APP_START],
                "SPL/configuration differs; this app-only restoration cannot repair it")
        require(self.full_preimage[0xFF000:] == self.stock_backup[0xFF000:],
                "key_mac differs; same-unit restoration cannot be established")
        require(type(self.plan_bytes) is bytes and sha(self.plan_bytes) == spec.plan_sha256,
                "canonical restoration plan hash differs")
        plan = json.loads(self.plan_bytes)
        require(canonical(plan) == self.plan_bytes and plan.get("kind") == "mini-stock-app-restoration"
                and plan.get("fresh_full_read", {}).get("sha256") == sha(self.full_preimage)
                and plan.get("stock_backup", {}).get("sha256") == BACKUP_SHA
                and plan.get("preimage_app_sha256") == sha(spec.preimage)
                and plan.get("target_app_sha256") == sha(spec.candidate)
                and plan.get("sector_order") == list(spec.sector_order)
                and plan.get("physical_write_allowlist") == [APP_START, APP_END],
                "restoration plan contents differ")

    def plan(self):
        """Return a detached JSON value; changing it cannot change the plan."""
        return json.loads(self.plan_bytes)

    def expected_full_readback(self):
        return self.full_preimage[:APP_START] + self.installation.candidate + self.full_preimage[APP_END:]

    def summary(self):
        plan = self.plan()
        return {"kind": plan["kind"], "installation": self.installation.summary(),
                "fresh_full_read": plan["fresh_full_read"], "stock_backup": plan["stock_backup"],
                "preserved_regions": plan["preserved_regions"],
                "factory_OTA_regions": plan["factory_OTA_regions"],
                "expected_full_readback_sha256": sha(self.expected_full_readback()),
                "expected_full_readback_equals_historical_backup": self.expected_full_readback() == self.stock_backup,
                "hardware_freshness_attested_by_this_tool": False,
                "device_io": False, "automatic_reset": False, "automatic_retry": False}

    def retain_plan(self, path):
        """Persist exact review bytes to a NEW workspace file; never overwrite."""
        path = Path(path).resolve()
        require(path.is_relative_to(ROOT) and path.parent.is_dir(), "new plan must stay inside the workspace")
        with path.open("xb") as stream:
            stream.write(self.plan_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(self.plan_bytes)}


def prepare_stock_restoration(fresh_dump_path, *, expected_sha256,
        stock_backup_path=ROOT / BACKUP_PATH, plan_path=installer.builder.DEFAULT_PLAN,
        manifest_path=installer.builder.REPORT, slot=installer.RAM_SLOTS[0]):
    """Freeze current app bytes and this unit's stock destination, offline.

    The fresh dump may contain an incomplete/unbootable application. Its app
    CRC/header is deliberately not a prerequisite for recovery. The runner must
    prove the hardware origin and recency of the supplied read; a path/hash
    alone cannot establish either. Full SPL/configuration and key_mac must
    match the pinned unit backup. VM/BTIF/USR differences are described and kept.
    """
    digest(expected_sha256)
    current, fresh_reference = retained_file(fresh_dump_path)
    require(len(current) == CAPACITY and sha(current) == expected_sha256,
            "fresh full NOR extent/hash differs")
    stock, stock_reference = retained_file(stock_backup_path)
    require(len(stock) == CAPACITY and sha(stock) == BACKUP_SHA, "pinned same-unit stock backup required")
    require(current[:APP_START] == stock[:APP_START],
            "SPL/configuration differs; app-only restoration is insufficient")
    require(current[0xFF000:] == stock[0xFF000:], "key_mac differs from this unit's backup")
    base = installer.prepare_installation(plan_path, manifest_path, slot=slot)
    require(base.backup_sha256 == BACKUP_SHA and base.preimage == stock[APP_START:APP_END],
            "operational writer reference uses another stock preimage")
    old, target = current[APP_START:APP_END], stock[APP_START:APP_END]
    sectors = []
    for address in range(APP_START, APP_END, SECTOR):
        offset = address - APP_START
        before, after = old[offset:offset + SECTOR], target[offset:offset + SECTOR]
        sectors.append({"physical_address": address, "bytes": SECTOR,
                        "fresh_sha256": sha(before), "stock_sha256": sha(after),
                        "preimage_crc32": installer.crc(before), "target_crc32": installer.crc(after),
                        "differs": before != after,
                        "program_page_order": installer.builder.page_order(address)})
    changed = [s["physical_address"] for s in sectors if s["differs"]]
    order = [a for a in changed if a != APP_START] + ([APP_START] if APP_START in changed else [])
    expected = current[:APP_START] + target + current[APP_END:]
    plan = {"schema": 1, "kind": "mini-stock-app-restoration", "target": "tank-mini",
            "offline_only": True, "device_access_performed": False,
            "fresh_full_read": fresh_reference, "stock_backup": stock_reference,
            "hardware_freshness_attested_by_this_tool": False,
            "preimage_app_sha256": sha(old), "target_app_sha256": sha(target),
            "application_bytes": APP_END - APP_START, "physical_write_allowlist": [APP_START, APP_END],
            "sector_order": order, "changed_sectors": len(order), "sectors": sectors,
            "header_sector_last": True, "header_page_last": True, "initial_header_invalidation": False,
            "preserved_regions": [region_evidence(current, stock, *r) for r in PRESERVED],
            "factory_OTA_regions": [region_evidence(current, stock, "staged_OTA_payload_and_padding", 0xB7000, 0xBC000),
                                    region_evidence(current, stock, "OTA_request_and_metadata_sector", 0xBC000, 0xBD000)],
            "expected_full_readback_sha256": sha(expected),
            "expected_full_readback_equals_historical_backup": expected == stock,
            "writer": {"slot": base.slot, "build_tag": base.build_tag,
                       "payload_sha256": base.image_sha256, "elf_sha256": base.elf_sha256,
                       "manifest_sha256": base.manifest_sha256, "reference_install_plan_sha256": base.plan_sha256},
            "automatic_retry": False, "automatic_reset": False,
            "power_loss_atomicity_proven": False, "stock_OTA_fallback_qualified": False,
            "post_operation": "Remain in ROM. Independently read the full NOR and compare before a separately reviewed stock boot.",
            "limits": ["Only the stock application is restored; VM, OTA, BTIF, USR and unit data are preserved from the fresh read.",
                       "Historical presets, full historical flash contents and stock runtime behavior are not established by an app-only write.",
                       "The installed header may remain valid while the body is replaced; interruption recovery is not guaranteed."]}
    plan_bytes = canonical(plan)
    spec = replace(base, purpose="restore-stock", fresh_full_read_sha256=sha(current),
                   candidate=target, preimage=old, sector_order=tuple(order), plan_sha256=sha(plan_bytes))
    return StockRestoration(spec, current, stock, plan_bytes)


def validate_restored_full(restoration, readback):
    """Validate a separately acquired full read without any device access."""
    require(isinstance(restoration, StockRestoration), "verified restoration required")
    require(type(readback) is bytes and len(readback) == CAPACITY, "immutable complete 1MiB readback required")
    app_ok = readback[APP_START:APP_END] == restoration.installation.candidate
    differing = [name for name, start, end in PRESERVED
                 if readback[start:end] != restoration.full_preimage[start:end]]
    require(app_ok and not differing,
            "restoration readback differs: " + ", ".join(([] if app_ok else ["application"]) + differing))
    return {"stock_application_verified": True, "application_sha256": sha(readback[APP_START:APP_END]),
            "all_external_regions_equal_fresh_preimage": True, "full_readback_sha256": sha(readback),
            "whole_NOR_equals_historical_stock_backup": readback == restoration.stock_backup,
            "historical_presets_restored_claimed": False, "stock_boot_verified": False,
            "device_access_performed_by_validator": False}


class MiniStockRestorationSession(installer.MiniAppInstallerSession):
    """Explicit stock-direction session; all bounded transport behavior is reused."""
    def __init__(self, transport, restoration, *, journal, known_free_slot=False,
                 known_uploaded_unstarted=False):
        require(isinstance(restoration, StockRestoration), "verified stock restoration required")
        self.restoration = restoration
        super().__init__(transport, restoration.installation, journal=journal,
                         known_free_slot=known_free_slot, known_uploaded_unstarted=known_uploaded_unstarted)
        self._event("stock_restoration_plan", plan=restoration.plan(), plan_sha256=sha(restoration.plan_bytes))

    def restore_application(self):
        result = super().install_application()
        result = {**result, "stock_application_restored": True,
                  "fresh_full_read_sha256": sha(self.restoration.full_preimage),
                  "external_regions_verified_after_write": False,
                  "whole_NOR_equals_historical_stock_backup": None,
                  "historical_presets_restored_claimed": False}
        self.last_result = result
        try:
            self._event("stock_application_verified", **result)
        except Exception as error:
            self._fail(error)
            raise
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-dump", type=Path)
    parser.add_argument("--sha256", help="expected SHA256 of the retained fresh full-NOR read")
    parser.add_argument("--stock-backup", type=Path, default=ROOT / BACKUP_PATH)
    parser.add_argument("--plan", type=Path, default=installer.builder.DEFAULT_PLAN)
    parser.add_argument("--manifest", type=Path, default=installer.builder.REPORT)
    parser.add_argument("--slot", type=lambda value: int(value, 0), default=installer.RAM_SLOTS[0])
    parser.add_argument("--report", type=Path, help="retain the canonical plan to a new local file")
    args = parser.parse_args(argv)
    result = {"device_io": False, "enumerated": False, "CLI_executes_restoration": False,
              "automatic_retry": False, "automatic_reset": False}
    if args.fresh_dump is not None:
        require(args.sha256 is not None, "--fresh-dump requires --sha256")
        prepared = prepare_stock_restoration(args.fresh_dump, expected_sha256=args.sha256,
            stock_backup_path=args.stock_backup, plan_path=args.plan, manifest_path=args.manifest, slot=args.slot)
        result["restoration"] = prepared.summary()
        if args.report is not None:
            result["retained_plan"] = prepared.retain_plan(args.report)
    else:
        require(args.sha256 is None and args.report is None, "--sha256/--report require --fresh-dump")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
