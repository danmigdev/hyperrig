"""Prepare a NEW HyperRig install plan from an explicitly accepted partial read.

No runtime/device I/O, retry, reset or command replay. The caller must acquire
and retain a fresh full NOR read, review its exact hash/modified sectors, prove
ROM/slot history, then explicitly use the existing bounded installer session.
Frozen writer, installer, restorer and first-attempt evidence are not changed.
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
from tools.restore_mini_stock import (BACKUP_PATH, BACKUP_SHA, PRESERVED,
    canonical, digest, retained_file, region_evidence)

APP_START, APP_END = installer.APP_START, installer.APP_END
CAPACITY, SECTOR, PAGE = 0x100000, 4096, 256
CANDIDATE_SHA = "3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff"
sha, require = installer.sha, installer.require


def modified_sectors(current, stock):
    return tuple(a for a in range(APP_START, APP_END, SECTOR)
                 if current[a:a + SECTOR] != stock[a:a + SECTOR])


def page_classification(current, stock, candidate, address):
    rows = []
    for at in range(address, address + SECTOR, PAGE):
        raw = current[at:at + PAGE]
        wanted = candidate[at - APP_START:at - APP_START + PAGE]
        rows.append({"physical_address": at, "sha256": sha(raw),
                     "matches_candidate": raw == wanted,
                     "matches_stock": raw == stock[at:at + PAGE],
                     "all_FF": raw == b"\xff" * PAGE})
    return rows


@dataclass(frozen=True)
class ResumePlan:
    installation: installer.Installation
    full_preimage: bytes
    stock_backup: bytes
    plan_bytes: bytes

    def __post_init__(self):
        require(type(self.full_preimage) is bytes and type(self.stock_backup) is bytes
                and len(self.full_preimage) == len(self.stock_backup) == CAPACITY,
                "immutable complete 1MiB inputs required")
        spec = self.installation
        require(isinstance(spec, installer.Installation) and spec.purpose == "install-candidate"
                and spec.fresh_full_read_sha256 == sha(self.full_preimage)
                and spec.backup_sha256 == sha(self.stock_backup) == BACKUP_SHA,
                "new installation input provenance differs")
        require(sha(spec.candidate) == CANDIDATE_SHA and spec.preimage == self.full_preimage[APP_START:APP_END],
                "candidate or current application preimage differs")
        require(all(self.full_preimage[a:b] == self.stock_backup[a:b] for _, a, b in PRESERVED),
                "external NOR regions differ from accepted stock backup")
        require(type(self.plan_bytes) is bytes and spec.plan_sha256 == sha(self.plan_bytes),
                "new plan hash differs")
        plan = json.loads(self.plan_bytes)
        require(canonical(plan) == self.plan_bytes and plan.get("kind") == "mini-install-from-reviewed-partial"
                and plan.get("fresh_full_read", {}).get("sha256") == sha(self.full_preimage)
                and plan.get("target_app_sha256") == CANDIDATE_SHA
                and plan.get("preimage_app_sha256") == sha(spec.preimage)
                and plan.get("physical_write_allowlist") == [APP_START, APP_END]
                and plan.get("sector_order") == list(spec.sector_order)
                and plan.get("accepted_modified_sectors_from_stock") == list(modified_sectors(self.full_preimage, self.stock_backup)),
                "new plan content differs")

    def plan(self):
        return json.loads(self.plan_bytes)

    def expected_full_readback(self):
        return self.full_preimage[:APP_START] + self.installation.candidate + self.full_preimage[APP_END:]

    def summary(self):
        plan = self.plan()
        return {"kind": plan["kind"], "installation": self.installation.summary(),
                "fresh_full_read": plan["fresh_full_read"],
                "accepted_modified_sectors_from_stock": plan["accepted_modified_sectors_from_stock"],
                "partial_sector_pages": plan["partial_sector_pages"],
                "external_regions_identical_to_stock": True,
                "expected_full_readback_sha256": sha(self.expected_full_readback()),
                "hardware_read_origin_or_freshness_attested": False,
                "automatic_resume": False, "automatic_retry": False,
                "automatic_reset": False, "device_io": False}

    def retain_plan(self, path):
        path = Path(path).resolve()
        require(path.is_relative_to(ROOT) and path.parent.is_dir(), "new plan must stay in the workspace")
        with path.open("xb") as stream:
            stream.write(self.plan_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(self.plan_bytes)}


def prepare_resume(fresh_dump_path, *, expected_partial_sha256, expected_modified_sectors,
        stock_backup_path=ROOT / BACKUP_PATH, plan_path=installer.builder.DEFAULT_PLAN,
        manifest_path=installer.builder.REPORT, slot=installer.RAM_SLOTS[0]):
    """Bind the exact current full read and reviewed sector set to a new plan.

    expected_modified_sectors is an explicit caller-reviewed tuple, not inferred
    permission from the failed operation's log. The actual bytes determine the
    new per-sector preimages; no erased/programmed-page state is resumed.
    """
    digest(expected_partial_sha256)
    require(type(expected_modified_sectors) is tuple
            and all(type(a) is int and APP_START <= a <= APP_END - SECTOR and a % SECTOR == 0
                    for a in expected_modified_sectors)
            and tuple(sorted(set(expected_modified_sectors))) == expected_modified_sectors,
            "explicit sorted unique modified-sector tuple required")
    current, reference = retained_file(fresh_dump_path)
    require(len(current) == CAPACITY and sha(current) == expected_partial_sha256,
            "reviewed partial full-read extent/hash differs")
    stock, backup_reference = retained_file(stock_backup_path)
    require(len(stock) == CAPACITY and sha(stock) == BACKUP_SHA, "pinned same-unit stock backup required")
    external = [region_evidence(current, stock, *r) for r in PRESERVED]
    require(all(not r["differs_from_stock_backup"] for r in external),
            "external regions changed: " + ", ".join(r["name"] for r in external if r["differs_from_stock_backup"]))
    actual_modified = modified_sectors(current, stock)
    require(actual_modified == expected_modified_sectors,
            "actual modified sectors differ from the explicitly reviewed partial input")
    base = installer.prepare_installation(plan_path, manifest_path, slot=slot)
    require(base.backup_sha256 == BACKUP_SHA and base.preimage == stock[APP_START:APP_END]
            and sha(base.candidate) == CANDIDATE_SHA, "only the reviewed first-install candidate is supported")
    old, target = current[APP_START:APP_END], base.candidate
    sectors = []
    for address in range(APP_START, APP_END, SECTOR):
        offset = address - APP_START
        before, after = old[offset:offset + SECTOR], target[offset:offset + SECTOR]
        sectors.append({"physical_address": address, "bytes": SECTOR,
                        "preimage_sha256": sha(before), "candidate_sha256": sha(after),
                        "preimage_crc32": installer.crc(before), "candidate_crc32": installer.crc(after),
                        "differs": before != after, "program_page_order": installer.builder.page_order(address)})
    changed = [s["physical_address"] for s in sectors if s["differs"]]
    order = [a for a in changed if a != APP_START] + ([APP_START] if APP_START in changed else [])
    plan = {"schema": 1, "kind": "mini-install-from-reviewed-partial", "target": "tank-mini",
            "offline_only": True, "device_access_performed": False,
            "fresh_full_read": reference, "stock_backup": backup_reference,
            "accepted_modified_sectors_from_stock": list(actual_modified),
            "partial_sector_pages": [{"physical_address": a,
                "pages": page_classification(current, stock, target, a)} for a in actual_modified],
            "physical_write_allowlist": [APP_START, APP_END], "application_bytes": APP_END - APP_START,
            "preimage_app_sha256": sha(old), "target_app_sha256": CANDIDATE_SHA,
            "sector_order": order, "changed_sectors": len(order), "sectors": sectors,
            "preserved_regions": external, "header_sector_last": True, "header_page_last": True,
            "initial_header_invalidation": False, "power_loss_atomicity_proven": False,
            "previous_session_tokens_or_bitmap_reused": False,
            "new_sector_erase_after_current_preimage_verification": True,
            "automatic_resume": False, "automatic_retry": False, "automatic_reset": False,
            "hardware_read_origin_or_freshness_attested": False,
            "writer": {"slot": base.slot, "build_tag": base.build_tag,
                       "payload_sha256": base.image_sha256, "elf_sha256": base.elf_sha256,
                       "manifest_sha256": base.manifest_sha256, "reference_plan_sha256": base.plan_sha256},
            "expected_full_readback_sha256": sha(current[:APP_START] + target + current[APP_END:]),
            "post_operation": "Remain in ROM; independently compare complete NOR before any separately reviewed boot."}
    raw = canonical(plan)
    spec = replace(base, preimage=old, sector_order=tuple(order), plan_sha256=sha(raw),
                   fresh_full_read_sha256=sha(current))
    return ResumePlan(spec, current, stock, raw)


def validate_completed_full(plan, readback):
    require(isinstance(plan, ResumePlan) and type(readback) is bytes and len(readback) == CAPACITY,
            "verified resume plan and immutable complete 1MiB readback required")
    app_ok = readback[APP_START:APP_END] == plan.installation.candidate
    altered = [name for name, a, b in PRESERVED if readback[a:b] != plan.full_preimage[a:b]]
    require(app_ok and not altered, "independent full readback differs: "
            + ", ".join(([] if app_ok else ["application"]) + altered))
    return {"application_verified": True, "candidate_sha256": CANDIDATE_SHA,
            "full_NOR_sha256": sha(readback), "external_regions_unchanged": True,
            "boot_attempted": False, "hardware_read_performed_by_validator": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-dump", type=Path)
    parser.add_argument("--sha256")
    parser.add_argument("--modified-sector", type=lambda text: int(text, 0), action="append")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--slot", type=lambda text: int(text, 0), default=installer.RAM_SLOTS[0])
    args = parser.parse_args(argv)
    result = {"device_io": False, "automatic_resume": False, "automatic_reset": False,
              "automatic_retry": False, "CLI_executes_installation": False}
    if args.fresh_dump is not None:
        require(args.sha256 is not None and args.modified_sector is not None,
                "fresh input requires an explicit SHA256 and modified-sector list")
        prepared = prepare_resume(args.fresh_dump, expected_partial_sha256=args.sha256,
                                  expected_modified_sectors=tuple(args.modified_sector), slot=args.slot)
        result["plan"] = prepared.summary()
        if args.report is not None:
            result["retained_plan"] = prepared.retain_plan(args.report)
    else:
        require(args.sha256 is None and args.modified_sector is None and args.report is None,
                "input hash, sector list and report require --fresh-dump")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
