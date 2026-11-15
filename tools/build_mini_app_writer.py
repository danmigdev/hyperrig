"""Validate the offline MINI writer design and installation plan.

This deliberately builds NO executable writer. The ROM receive callback's
completion/error contract is unqualified. No target compiler, subprocess,
transport, hardware API or NVM command is called by this module. Import is
inert; the default CLI checks local files and prints a summary. --write-report
updates only research/mini-app-writer.json.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_START, APP_END = 0x4000, 0x82000
CAPACITY, SECTOR_BYTES, PAGE_BYTES = 0x100000, 4096, 256
APP_BYTES = APP_END - APP_START
BACKUP_SHA256 = "72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180"
UPSTREAM_COMMIT = "3ac7651a019fa44daba061b05654278496477b64"
PROPOSAL = "firmware/mini/app_writer/protocol-draft.json"
DESIGN = "firmware/mini/app_writer/DESIGN.md"
REPORT = "research/mini-app-writer.json"
DEFAULT_PLAN = "build/mini-install-plan/install-plan.json"
SOURCE_EVIDENCE = {
    "upstream/m-bootloader/docs/SPEC.md": "d86ae060b1db368a8aba421e21903b3b9c7517943bcf2667ee170a5a96a2863c",
    "upstream/m-bootloader/src/loader_target.c": "6d8cacc6c300a106b0f6ed175005782eb17a2d74d70084e9a6ee7b43c4ad6fec",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc(data: bytes) -> int:
    return binascii.crc32(data) & 0xFFFFFFFF


def app_range(address: int, length: int, *, alignment: int = 1) -> bool:
    """Model the checks required BEFORE address truncation/24-bit encoding."""
    return (type(address) is int and type(length) is int and type(alignment) is int
            and alignment > 0 and APP_START <= address < APP_END
            and 0 < length <= APP_END - address and address % alignment == 0)


def validate_protocol(spec: dict) -> None:
    require(spec.get("schema") == 1 and spec.get("protocol") == "HYW1", "unknown protocol draft")
    require(spec.get("implementation_status") == "design_only_receive_contract_unqualified",
            "draft cannot claim a qualified receive contract")
    require(spec.get("executable_artifacts") == [] and spec.get("transport_implemented") is False,
            "this design has no executable or transport implementation")
    require(spec.get("physical_app_range") == [APP_START, APP_END], "writer range must be the MINI app only")
    require(spec.get("nor_capacity") == CAPACITY and spec.get("jedec_hex") == "eb6014",
            "only this MINI's exact NOR identity is in scope")
    require(spec.get("sector_bytes") == SECTOR_BYTES and spec.get("page_bytes") == PAGE_BYTES,
            "sector/page geometry differs")
    require(spec.get("ram_slots") == [0x1C20000, 0x1C28000] and spec.get("slot_bytes") == 32768,
            "RAM slot contract differs")
    require(spec.get("cdb_bytes") == 16 and spec.get("unused_cdb_bytes") == 255, "CDB framing differs")
    require(spec.get("status_guards") == {"sr1_wip": 1, "sr1_wel": 2,
            "sr1_protection_mask": 0x7C, "sr2_cmp_mask": 0x40, "writes_to_status_registers": False},
            "protection must be inspected without status-register writes")
    require(spec.get("nor_commands_mutating_proposed") == ["06", "20", "02"],
            "proposal must not add chip/block erase or status writes")
    expected = {"fc78": ("in", 16), "fc79": ("in", 16), "fc7a": ("in", 16),
                "fc7b": ("in", 16), "fb7c": ("out", 260), "fc7d": ("in", 16),
                "fc7e": ("in", 16), "fd7f": ("in", "n16 in [1,512]"), "fc80": ("in", 16)}
    commands = spec.get("commands", [])
    require(len(commands) == len(expected), "missing or extra protocol command")
    seen = set()
    for command in commands:
        op = command.get("opcode")
        require(op in expected and op not in seen, "unknown/duplicate protocol command")
        seen.add(op)
        require((command.get("direction"), command.get("transfer_bytes")) == expected[op],
                f"{op}: direction/length differs")
        occupied = {0, 1}
        for offset, size, name in command.get("fields", []):
            require(type(offset) is int and type(size) is int and size in (1, 2, 4)
                    and 2 <= offset and offset + size <= 16 and isinstance(name, str),
                    f"{op}: invalid field")
            extent = set(range(offset, offset + size))
            require(not occupied.intersection(extent), f"{op}: overlapping fields")
            occupied.update(extent)


def validate_plan(plan: dict, candidate: bytes, backup: bytes, rollback: bytes) -> list[dict]:
    """Recheck exact bytes, geometry and preservation; produce CRC review data."""
    require(plan.get("target") == "tank-mini" and plan.get("offline_only") is True,
            "expected an offline MINI installation plan")
    require(plan.get("device_access_performed") is False and plan.get("write_commands_emitted") is False
            and plan.get("execution_ready") is False, "plan must not claim an installation")
    require(plan.get("physical_write_allowlist") == [APP_START, APP_END]
            and plan.get("sector_bytes") == SECTOR_BYTES, "plan exceeds MINI application scope")
    require(len(candidate) == APP_BYTES and len(rollback) == APP_BYTES and len(backup) == CAPACITY,
            "candidate, rollback or backup extent differs")
    for key, data in (("candidate", candidate), ("rollback", rollback), ("unit_backup", backup)):
        item = plan.get(key, {})
        require(item.get("sha256") == sha(data) and item.get("bytes") == len(data), f"{key} bytes/hash differ")
    require(sha(backup) == BACKUP_SHA256, "expected this MINI's verified complete backup")
    require(rollback == backup[APP_START:APP_END], "rollback does not reproduce this unit's app preimage")
    require(plan["unit_backup"].get("fresh_read_immediately_before_install_required") is True,
            "a stale backup cannot replace the immediate preimage check")
    sectors = plan.get("sectors", [])
    addresses = list(range(APP_START, APP_END, SECTOR_BYTES))
    require(len(sectors) == len(addresses) == 126, "expected exactly126 application sectors")
    result = []
    for address, item in zip(addresses, sectors):
        require(item.get("physical_address") == address and item.get("bytes") == SECTOR_BYTES,
                "missing, duplicated, reordered or misaligned sector")
        old = backup[address:address + SECTOR_BYTES]
        new = candidate[address - APP_START:address - APP_START + SECTOR_BYTES]
        require(item.get("backup_sha256") == sha(old) and item.get("candidate_sha256") == sha(new)
                and item.get("differs") is (old != new), f"sector {address:#x}: preimage/target differs")
        pages = []
        for offset in range(0, SECTOR_BYTES, PAGE_BYTES):
            page = new[offset:offset + PAGE_BYTES]
            pages.append({"physical_address": address + offset, "bytes": PAGE_BYTES,
                          "candidate_crc32": crc(page)})
        result.append({"physical_address": address, "bytes": SECTOR_BYTES,
                       "preimage_crc32": crc(old), "candidate_crc32": crc(new),
                       "preimage_sha256": sha(old), "candidate_sha256": sha(new),
                       "differs": old != new, "pages": pages})
    changed = [item["physical_address"] for item in result if item["differs"]]
    order = [address for address in changed if address != APP_START]
    if APP_START in changed:
        order.append(APP_START)
    require(plan.get("proposed_sector_order") == order and plan.get("changed_sectors") == len(order),
            "proposed order or changed-sector count differs")
    require(plan.get("application_header_sector_last") is True and plan.get("power_loss_atomicity_proven") is False,
            "ordering does not establish power-loss atomicity")
    expected_preserved = [(0, APP_START), (APP_END, 0xBE000), (0xBE000, 0xBF000),
                          (0xBF000, 0xFF000), (0xFF000, CAPACITY)]
    preserved = plan.get("preserved_regions", [])
    require(len(preserved) == len(expected_preserved), "preservation map differs")
    composed = backup[:APP_START] + candidate + backup[APP_END:]
    for item, (start, end) in zip(preserved, expected_preserved):
        require(item.get("range") == [start, end] and item.get("sha256") == sha(backup[start:end]),
                "preserved interval/hash differs")
        require(composed[start:end] == backup[start:end], "preserved bytes differ")
    require(plan.get("factory_OTA_preserved") is True and composed[0xB7000:0xBD000] == backup[0xB7000:0xBD000],
            "factory OTA/request must remain intact")
    require(plan.get("hypothetical_full_image_sha256") == sha(composed), "composed hash differs")
    return result


def workspace_file(value: str | Path) -> Path:
    path = (ROOT / value).resolve()
    require(path.is_relative_to(ROOT), "source path outside workspace")
    require(path.is_file(), f"source is not a file: {path}")
    return path


def build_contract(plan_path: Path) -> dict:
    plan_path = workspace_file(plan_path)
    plan_raw = plan_path.read_bytes()
    plan = json.loads(plan_raw)
    proposal_path = workspace_file(PROPOSAL)
    proposal = json.loads(proposal_path.read_bytes())
    validate_protocol(proposal)
    data = {key: workspace_file(plan[key]["path"]).read_bytes() for key in ("candidate", "unit_backup", "rollback")}
    sectors = validate_plan(plan, data["candidate"], data["unit_backup"], data["rollback"])
    for name, expected in SOURCE_EVIDENCE.items():
        require(sha(workspace_file(name).read_bytes()) == expected, f"pinned ABI evidence changed: {name}")
    paths = [PROPOSAL, DESIGN, "tools/build_mini_app_writer.py", "firmware/mini/app_writer/test_contract.py",
             "upstream/m-bootloader/docs/SPEC.md", "upstream/m-bootloader/src/loader_target.c",
             "upstream/m-bootloader/src/loader.c", "upstream/m-bootloader/src/platform.c",
             "firmware/mini/recovery_reader/reader.c", "firmware/mini/recovery_reader/reader.h",
             "firmware/mini/recovery_reader/entry.c", "tools/plan_mini_install.py"]
    sources = {name: sha(workspace_file(name).read_bytes()) for name in paths}
    return {
        "schema": 1, "project": "HyperRig", "target": "tank-mini", "kind": "bounded-app-writer-design",
        "status": "blocked_on_rom_receive_completion_contract", "offline_only": True,
        "device_access_performed": False, "nvm_write_operations_implemented": False,
        "nvm_write_operations_executed": False, "executable_artifacts": [], "execution_ready": False,
        "flashable": False, "hardware_qualified": False,
        "protocol_proposal": proposal,
        "install_plan": {"path": plan_path.relative_to(ROOT).as_posix(), "sha256": sha(plan_raw),
                         "candidate": plan["candidate"], "unit_backup": plan["unit_backup"],
                         "rollback": plan["rollback"], "changed_sectors": plan["changed_sectors"],
                         "proposed_sector_order": plan["proposed_sector_order"]},
        "crc_standard_vector": {"ascii": "123456789", "crc32": crc(b"123456789")},
        "sectors": sectors, "source_sha256": sources,
        "receive_evidence": {
            "repository": "https://github.com/jvitkauskas/m-bootloader", "commit": UPSTREAM_COMMIT,
            "signature": "params[1]: int (*receive)(void *, uint32_t)",
            "entry_reference": "src/loader_target.c:19",
            "call_reference": "src/loader.c:14-20: return discarded; unconditional pointer advance; chunks<=512",
            "limitation_reference": "docs/SPEC.md:835: return values and partial-transfer/error semantics unknown",
            "mini_receive_hardware_trace_available": False,
            "return_value_interpretation": None, "partial_transfer_semantics": None,
            "callback_buffer_lifetime_qualified": False,
            "unknown_return_must_not_be_assumed_success": True,
        },
        "status_register_reference": {"source": "upstream/m-bootloader/docs/SPEC.md:178",
                                      "jedec_hex": "eb6014", "sr1_reject_mask": 0x7C,
                                      "sr2_reject_mask": 0x40, "status_register_writes_allowed": False},
        "qualification_gates": {"rom_receive_complete_error_lifetime": False,
                                "writer_mock_nor_fault_suite": False,
                                "writer_target_elf_and_stack_review": False,
                                "independent_recovery_from_valid_image_hang": False,
                                "exact_candidate_codec_board_first_boot": False},
        "limitations": [
            "CRC/page tables are computed from local bytes; no device byte has been read by this tool.",
            "This report does not qualify or change any hardware/readiness gate in another report.",
            "CRC32 is not authentication and does not replace host SHA256 preimage/readback checks.",
            "A sector interrupted during erase/program can be partially changed; no automatic rollback is claimed.",
            "Mock NOR and target ELF tests are deferred because no writer runtime has been implemented.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / DEFAULT_PLAN)
    parser.add_argument("--write-report", action="store_true", help="write the design report only; never builds target code")
    args = parser.parse_args()
    report = build_contract(args.plan)
    if args.write_report:
        (ROOT / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "execution_ready": False,
                      "executable_artifacts": [], "sectors_checked": len(report["sectors"]),
                      "pages_checked": sum(len(s["pages"]) for s in report["sectors"]),
                      "candidate_sha256": report["install_plan"]["candidate"]["sha256"],
                      "report_written": args.write_report}))


if __name__ == "__main__":
    main()
