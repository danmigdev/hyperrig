"""Offline contract tests; no mock NOR/runtime is claimed by these tests."""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools import build_mini_app_writer as contract


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((ROOT / contract.DEFAULT_PLAN).read_text(encoding="utf-8"))
        cls.data = [contract.workspace_file(cls.plan[key]["path"]).read_bytes()
                    for key in ("candidate", "unit_backup", "rollback")]
        cls.protocol = json.loads((ROOT / contract.PROPOSAL).read_text(encoding="utf-8"))

    def test_complete_current_plan(self):
        sectors = contract.validate_plan(self.plan, *self.data)
        self.assertEqual(len(sectors), 126)
        self.assertEqual(sum(len(s["pages"]) for s in sectors), 2016)
        self.assertEqual(sectors[0]["physical_address"], 0x4000)
        self.assertEqual(sectors[-1]["pages"][-1]["physical_address"], 0x81F00)
        self.assertEqual(contract.crc(b"123456789"), 0xCBF43926)

    def test_range_boundaries_and_overflow(self):
        valid = [(0x4000, 4096, 4096), (0x81000, 4096, 4096), (0x81F00, 256, 256),
                 (0x81FFF, 1, 1), (0x4000, 0x7E000, 1)]
        invalid = [(0x3FFF, 1, 1), (0x4001, 4096, 4096), (0x82000, 1, 1),
                   (0x81F00, 257, 256), (0x4000, 0, 1), (0x4000, -1, 1),
                   (0xFFFFFFFF, 0x100000001, 1), (0x02004000, 256, 1),
                   (True, 1, 1), (0x4000, True, 1), (0x4000, 256, 0)]
        for a, n, align in valid:
            with self.subTest(a=a, n=n, align=align):
                self.assertTrue(contract.app_range(a, n, alignment=align))
        for a, n, align in invalid:
            with self.subTest(a=a, n=n, align=align):
                self.assertFalse(contract.app_range(a, n, alignment=align))

    def test_duplicate_missing_reordered_outside_sector(self):
        for operation in (lambda p: p["sectors"].pop(),
                          lambda p: p["sectors"].__setitem__(1, p["sectors"][0]),
                          lambda p: p["sectors"].reverse(),
                          lambda p: p["sectors"][-1].update(physical_address=0x82000),
                          lambda p: p["physical_write_allowlist"].__setitem__(0, 0)):
            plan = copy.deepcopy(self.plan)
            operation(plan)
            with self.assertRaises(ValueError):
                contract.validate_plan(plan, *self.data)

    def test_tampered_candidate_or_rollback(self):
        for index in (0, 1, 2):
            data = list(self.data)
            altered = bytearray(data[index])
            altered[len(altered) // 2] ^= 1
            data[index] = bytes(altered)
            with self.assertRaises(ValueError):
                contract.validate_plan(self.plan, *data)

    def test_tampered_preimage_sector_hash(self):
        plan = copy.deepcopy(self.plan)
        plan["sectors"][0]["backup_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            contract.validate_plan(plan, *self.data)

    def test_preserved_region_missing_or_hash_changed(self):
        for operation in (lambda p: p["preserved_regions"].pop(),
                          lambda p: p["preserved_regions"][1]["range"].__setitem__(0, 0x83000),
                          lambda p: p["preserved_regions"][3].update(sha256="0" * 64),
                          lambda p: p.update(factory_OTA_preserved=False)):
            plan = copy.deepcopy(self.plan)
            operation(plan)
            with self.assertRaises(ValueError):
                contract.validate_plan(plan, *self.data)

    def test_plan_cannot_claim_ready_or_atomic(self):
        for name in ("execution_ready", "power_loss_atomicity_proven", "device_access_performed", "write_commands_emitted"):
            plan = copy.deepcopy(self.plan)
            plan[name] = True
            with self.assertRaises(ValueError):
                contract.validate_plan(plan, *self.data)

    def test_protocol_unique_bounded_fields(self):
        contract.validate_protocol(self.protocol)
        for operation in (lambda p: p["commands"].append(p["commands"][0]),
                          lambda p: p["commands"][2]["fields"].append([12, 4, "overlap"]),
                          lambda p: p["commands"][4].update(transfer_bytes=512),
                          lambda p: p["commands"][4].update(direction="in"),
                          lambda p: p["nor_commands_mutating_proposed"].append("c7"),
                          lambda p: p["status_guards"].update(writes_to_status_registers=True)):
            proposal = copy.deepcopy(self.protocol)
            operation(proposal)
            with self.assertRaises(ValueError):
                contract.validate_protocol(proposal)

    def test_locked_elf_rejects_mutation_flag_and_invalid_entry(self):
        path=ROOT/"build/mini-app-writer/hyperrig-writer-locked-01c20000.elf"
        if not path.is_file():self.skipTest("run --build-locked to produce ELF negative controls")
        import struct
        raw=path.read_bytes();_flat,item=contract.inspect_writer_elf(raw,0x1C20000)
        h=struct.unpack_from("<HHIIIIIHHHHHH",raw,16)
        p=struct.unpack_from("<8I",raw,h[4])
        altered=bytearray(raw);offset=p[1]+item["mutation_gate_address"]-0x1C20000
        struct.pack_into("<I",altered,offset,1)
        with self.assertRaisesRegex(ValueError,"gate"):contract.inspect_writer_elf(bytes(altered),0x1C20000)
        altered=bytearray(raw);struct.pack_into("<I",altered,24,0x1C20004)
        with self.assertRaises(ValueError):contract.inspect_writer_elf(bytes(altered),0x1C20000)

    def test_audit_record_disallows_mutation_claim_from_locked_target(self):
        path=ROOT/"build/mini-app-writer/host-stage-locked.bin"
        if not path.is_file():self.skipTest("run --build-locked for host record fixture")
        import struct
        raw=path.read_bytes();tag=struct.unpack_from("<I",raw,12)[0]
        result=contract.validate_audit_record(raw,base=0x1C20000,build_tag=tag)
        self.assertEqual(result["staged"],1);self.assertEqual(result["echoed"],1)
        for offset in (68,72,76,116):
            changed=bytearray(raw);struct.pack_into("<I",changed,offset,1)
            struct.pack_into("<I",changed,120,contract.crc(changed[:120]))
            with self.assertRaises(ValueError):contract.validate_audit_record(bytes(changed),base=0x1C20000,build_tag=tag)

    def test_no_target_artifact_or_readiness_in_report(self):
        report = contract.build_contract(ROOT / contract.DEFAULT_PLAN)
        self.assertEqual(report["executable_artifacts"], [])
        for flag in ("execution_ready", "flashable", "hardware_qualified", "device_access_performed",
                     "target_mutations_enabled", "nvm_write_operations_executed"):
            self.assertIs(report[flag], False)
        self.assertIs(report["nvm_write_operations_implemented"], True)
        self.assertFalse(any(report["qualification_gates"].values()))
        self.assertIsNone(report["receive_evidence"]["return_value_interpretation"])

    def test_import_and_default_cli_do_not_write_files(self):
        watched = [ROOT / contract.REPORT, ROOT / contract.DEFAULT_PLAN]
        before = {p: p.read_bytes() if p.exists() else None for p in watched}
        self.assertIs(importlib.reload(contract), contract)
        process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/build_mini_app_writer.py")],
                                 cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertIs(json.loads(process.stdout)["report_written"], False)
        for path, content in before.items():
            self.assertEqual(path.read_bytes() if path.exists() else None, content)


if __name__ == "__main__":
    unittest.main()
