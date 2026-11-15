"""Validate/build a MINI RAM writer with target mutations DISABLED.

Default checks the local plan only. --build-locked runs mock NOR tests and
builds two RAM artifacts whose mutation gate is a checked constant zero.
There is no transport, hardware operation, force switch or enabled target
build. General ROM receive semantics remain unqualified: immutable staging
and exact host echo are required independently of the observed return260.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
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
    require(spec.get("implementation_status") == "offline_tested_target_mutations_disabled"
            and spec.get("target_mutations_enabled") is False,
            "initial target must leave mutations disabled")
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
                "fc7e": ("in", 16), "fd7f": ("in", "n16 in [1,512]"), "fc80": ("in", 16),
                "fd87": ("in", 256), "fd88": ("in", 128)}
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
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/"firmware/mini/app_writer").iterdir()
              if p.is_file() and p.suffix in (".c",".h",".ld")]
    receive = receive_observation()
    paths += list(receive["source_sha256"])
    sources = {name: sha(workspace_file(name).read_bytes()) for name in paths}
    return {
        "schema": 1, "project": "HyperRig", "target": "tank-mini", "kind": "bounded-app-writer-design",
        "status": "offline_core_implemented_target_mutations_disabled", "offline_only": True,
        "device_access_performed": False, "nvm_write_operations_implemented": True,
        "target_mutations_enabled": False,
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
            "mini_receive_hardware_trace_available": True,
            "observed_success_length_and_return": 260,
            "return_value_interpretation": None, "partial_transfer_semantics": None,
            "callback_buffer_lifetime_qualified": False,
            "unknown_return_must_not_be_assumed_success": True,
            "observed_sample": receive,
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
            "Default validation does not execute build/tests; --build-locked records actual mock/ELF results.",
        ],
    }


def receive_observation():
    """Bind only the completed HYRX sample; no universal ABI claim follows."""
    from tools.build_mini_rom_receive import validate_record,poison
    names=["research/mini-rom-receive.json","tools/build_mini_rom_receive.py",
           "analysis/hardware/mini-receive-record-1.bin","analysis/hardware/mini-receive-record-2.bin"]
    blobs={name:workspace_file(name).read_bytes() for name in names}
    require(sha(blobs[names[0]])=="a2528e6019de515b9d06055127e93cfc01a3e6d6773fbbee4179e83290feed07",
            "HYRX executed manifest differs")
    manifest=json.loads(blobs[names[0]])
    payload=bytes(value^255 for value in poison(260,0x55))
    observed=[]
    for index,name in enumerate(names[2:],1):
        item=validate_record(blobs[name],base=0x1C20000,build_tag=manifest["build_tag"],sequence=1,
                             nonce=0x1234ABCD,payload=payload,seed=0x55)
        require(item["observed_complete_and_stable"] and item["raw_return"]==260 and item["sample_count"]==index,
                "HYRX successful260-byte sample changed")
        require(item["rom_pointer_observations"]=={"send":0x1E008E4,"receive":0x1E0089A,"handler_slot":0x1C01264},
                "observed ROM callback addresses differ")
        item.pop("record_hex");observed.append(item)
    a,b=(blobs[name] for name in names[2:])
    require(a[:92]+a[96:504]+a[508:]==b[:92]+b[96:504]+b[508:],"HYRX samples differ beyond counter/checksum")
    return {"successful_OUT_commands_observed":1,"length":260,"raw_return":260,"samples":observed,
            "general_return_error_lifetime_semantics_qualified":False,
            "source_sha256":{name:sha(raw) for name,raw in blobs.items()}}


def inspect_writer_elf(raw, base):
    from tools.verify_mini_rom_stack import decode,validate_stack_layout
    def read(fmt,off):
        require(0<=off<=len(raw)-struct.calcsize(fmt),"truncated ELF")
        return struct.unpack_from(fmt,raw,off)
    require(base in (0x1C20000,0x1C28000) and raw[:7]==b"\x7fELF\x01\x01\x01","bad ELF/slot")
    h=read("<HHIIIIIHHHHHH",16)
    require(h[:4]==(2,0xF1,1,base) and h[7]==52 and h[8]==32 and h[10]==40,"bad pi32v2 entry/header")
    loads=[read("<8I",h[4]+i*h[8]) for i in range(h[9])]
    loads=[p for p in loads if p[0]==1]
    require(len(loads)==1,"one RAM load segment required")
    p=loads[0]
    require(p[2]==p[3]==base and 0<p[4]<=p[5]<=32768 and p[6]==7 and p[1]<=len(raw)-p[4]
            and p[7]>0 and not p[7]&(p[7]-1) and p[1]%p[7]==base%p[7],"ELF mapping/slot invalid")
    sections=[read("<10I",h[5]+i*h[10]) for i in range(h[11])]
    symbols={};ranges=[]
    for s in sections:
        _,kind,flags,a,off,n,link,_,align,stride=s
        require(kind==8 or 0<=off<=len(raw)-n,"section outside file")
        if flags&2:
            require(kind in (1,8) and base<=a<=base+p[5] and n<=base+p[5]-a and (not align or not a%align),"allocated section outside slot")
            require(a>=base+p[4] if kind==8 else n==0 or (a<=base+p[4]-n and off==p[1]+a-base),"unmapped section bytes")
            if n:ranges.append((a,a+n))
        if kind!=2:continue
        require(stride==16 and not n%16 and link<len(sections),"invalid symbols")
        namesec=sections[link];require(namesec[1]==3,"bad string table")
        names=raw[namesec[4]:namesec[4]+namesec[5]]
        for pos in range(off,off+n,16):
            ni,value,size,info,_,index=read("<IIIBBH",pos)
            if not ni:continue
            require(ni<len(names) and b"\0" in names[ni:],"bad symbol name")
            name=names[ni:names.index(0,ni)].decode("ascii")
            require(index or info>>4 not in (1,2),"undefined symbol: "+name)
            if index:symbols[name]={"address":value,"bytes":size}
    ranges.sort();require(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])),"sections overlap")
    required=("hyperrig_writer_entry","hyperrig_writer_dispatch","hyperrig_writer_record","hyperrig_writer_mutations_enabled",
              "state","private_stack","hyperrig_mini_rom_run_on_stack","__slot_start","__slot_end","__image_file_end","__bss_start","__bss_end")
    require(all(n in symbols for n in required),"missing writer symbol")
    at=lambda n:symbols[n]["address"]
    require(at("hyperrig_writer_entry")==at("__slot_start")==base and at("__slot_end")==base+32768
            and at("__image_file_end")==at("__bss_start")==base+p[4] and at("__bss_end")==base+p[5],"linker extent mismatch")
    private=[]
    for name in ("state","private_stack","hyperrig_writer_record"):
        s=symbols[name];require(base+p[4]<=s["address"]<=base+p[5]-s["bytes"] and s["bytes"]>0,"private state outside BSS")
        private.append((s["address"],s["address"]+s["bytes"]))
    private.sort();require(all(a[1]<=b[0] for a,b in zip(private,private[1:])),"private state overlaps")
    require(symbols["private_stack"]["bytes"]==4160 and symbols["hyperrig_writer_record"]["bytes"]==128,"stack/record extent differs")
    validate_stack_layout(base,base+p[4],at("private_stack"),at("private_stack")+32,at("private_stack")+4128)
    payload=raw[p[1]:p[1]+p[4]]
    flag=at("hyperrig_writer_mutations_enabled")-base
    require(0<=flag<=len(payload)-4 and symbols["hyperrig_writer_mutations_enabled"]["bytes"]==4
            and payload[flag:flag+4]==bytes(4),"target mutation gate is not constant zero")
    bridge=symbols["hyperrig_mini_rom_run_on_stack"]
    decoded=decode(payload[bridge["address"]-base:bridge["address"]-base+bridge["bytes"]])
    return payload,{"base":base,"span":32768,"entry":base,"payload_bytes":len(payload),"memory_bytes":p[5],
                    "elf_sha256":sha(raw),"payload_sha256":sha(payload),"record_address":at("hyperrig_writer_record"),
                    "record_bytes":128,"mutation_gate_address":at("hyperrig_writer_mutations_enabled"),
                    "mutation_gate_value":0,"private_stack_bytes":4096,"private_stack_bottom":at("private_stack")+32,
                    "private_stack_top":at("private_stack")+4128,"bridge_instructions":decoded,
                    "hardware_executed":False,"physical_NVM_write_enabled":False}


def validate_audit_record(raw,*,base,build_tag,expected_mutations_enabled=False):
    require(len(raw)==128 and raw[:4]==b"HYW1" and raw[124:]==b"DONE","invalid HYW1 audit framing")
    require(crc(raw[:120])==int.from_bytes(raw[120:124],"little"),"HYW1 audit CRC differs")
    names=("version","base","build_tag","phase","error","token","sequence","sector","page",
           "preimage_crc32","target_crc32","page_crc32","last_crc32","jedec","sr1","sr2",
           "wren_attempts","erase_attempts","program_attempts","read_bytes","status_polls",
           "raw_receive_return","rx_guards_ok","page_bitmap","staged","echoed","stack_guards_ok",
           "stack_observed_bytes","mutations_enabled")
    item=dict(zip(names,struct.unpack_from("<29I",raw,4)))
    require(item["version"]==1 and item["base"]==base and base in (0x1C20000,0x1C28000)
            and item["build_tag"]==build_tag,"HYW1 audit identity differs")
    require(item["mutations_enabled"]==int(expected_mutations_enabled),"HYW1 mutation gate differs")
    require(item["phase"]<=6 and item["error"]<=17 and (item["phase"]==6)==bool(item["error"]),"HYW1 phase/error inconsistent")
    require(item["sr1"]<=255 and item["sr2"]<=255 and item["page_bitmap"]<=65535 and item["stack_observed_bytes"]<=4096,
            "HYW1 audit field out of range")
    require(all(item[k] in (0,1) for k in ("rx_guards_ok","staged","echoed","stack_guards_ok")),"invalid HYW1 flags")
    require(not item["echoed"] or item["staged"],"echo without staged page")
    if item["staged"]:
        require(item["phase"]==4 and item["token"] and item["sequence"]>1 and app_range(item["sector"],4096,alignment=4096)
                and app_range(item["page"],256,alignment=256) and item["sector"]<=item["page"]<item["sector"]+4096
                and item["raw_receive_return"]==260 and item["rx_guards_ok"],"invalid staged-page audit")
    if not expected_mutations_enabled:
        require(item["wren_attempts"]==item["erase_attempts"]==item["program_attempts"]==0,
                "locked target reports a mutation attempt")
    item["raw_receive_return"]=struct.unpack_from("<i",raw,88)[0]
    item.update(record_sha256=sha(raw),hardware_readiness_asserted=False)
    return item


def build_locked(report):
    out=ROOT/"build/mini-app-writer";out.mkdir(parents=True,exist_ok=True)
    sources=sorted(p for p in (ROOT/"firmware/mini/app_writer").iterdir() if p.is_file() and p.suffix in (".c",".h",".ld"))
    tag=int(sha(b"".join(p.read_bytes() for p in sources))[:8],16)
    (out/"build_tag.h").write_text(f"#define HYPERRIG_WRITER_BUILD_TAG UINT32_C(0x{tag:08x})\n",encoding="utf-8",newline="\n")
    prefix=["wsl.exe","--distribution","Ubuntu","--exec"] if os.name=="nt" else []
    def run(args):
        p=subprocess.run(prefix+args,cwd=ROOT,text=True,capture_output=True)
        if p.returncode:raise RuntimeError(" ".join(args)+"\n"+p.stdout+p.stderr)
        return p.stdout
    common=["-std=c99","-Wall","-Wextra","-Werror","-Ifirmware/mini/app_writer","-Ibuild/mini-app-writer"]
    core="firmware/mini/app_writer/writer.c";pio="firmware/mini/app_writer/nor_pio.c"
    tests={}
    for name,flags,files in (("host-write-tests",["-DHYPERRIG_WRITER_HOST_MUTATIONS"],[core,"firmware/mini/app_writer/test_writer.c"]),
                             ("host-locked-tests",[],[core,"firmware/mini/app_writer/test_writer.c"]),
                             ("host-pio-tests",[],[core,pio,"firmware/mini/app_writer/test_pio.c"])):
        exe="build/mini-app-writer/"+name
        run(["gcc",*common,"-O1","-g","-fsanitize=address,undefined","-fno-sanitize-recover=all",*flags,*files,"-o",exe])
        tests[name]=json.loads(run([exe]))
    samples={kind:validate_audit_record((out/f"host-stage-{kind}.bin").read_bytes(),base=0x1C20000,build_tag=tag,
                                       expected_mutations_enabled=kind=="mock") for kind in ("locked","mock")}
    vendor="tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    target_sources=["firmware/mini/app_writer/entry.c",core,pio,"firmware/mini/boot/runtime.c",
                    "firmware/mini/rom_stack/rom_stack_pi32v2.S"]
    objects=[]
    for source in target_sources:
        obj="build/mini-app-writer/"+Path(source).stem+".o"
        run([vendor+"clang","-target","pi32v2","-mcpu=r3",*common,"-Os","-ffreestanding","-fno-builtin",
             "-DHYPERRIG_WRITER_TARGET","-c",source,"-o",obj]);objects.append(obj)
    artifacts=[]
    for base in (0x1C20000,0x1C28000):
        stem=f"build/mini-app-writer/hyperrig-writer-locked-{base:08x}"
        run([vendor+"ld","-z","max-page-size=0x20","-z","common-page-size=0x20","--defsym",f"PROBE_ADDRESS={base}",
             "-T","firmware/mini/app_writer/writer.ld",*objects,"-Map",stem+".map","-o",stem+".elf"])
        flat,item=inspect_writer_elf((ROOT/(stem+".elf")).read_bytes(),base)
        (ROOT/(stem+".bin")).write_bytes(flat)
        (ROOT/(stem+".asm")).write_text(run([vendor+"objdump","-d",stem+".elf"]),encoding="utf-8",newline="\n")
        item.update(file=stem+".bin",elf=stem+".elf");artifacts.append(item)
    report.update(build_tag=tag,host_tests={"asan":True,"ubsan":True,**tests,"audit_records":samples},executable_artifacts=artifacts,
                  target_mutations_enabled=False,flashable=False,execution_ready=False)
    report["qualification_gates"]["writer_mock_nor_fault_suite"]=True
    report["qualification_gates"]["writer_target_elf_layout_and_bridge_bytes"]=True
    for path in target_sources+["firmware/mini/rom_stack/rom_stack.h","tools/verify_mini_rom_stack.py"]:
        report["source_sha256"][path]=sha(workspace_file(path).read_bytes())
    report["timeouts"]={"PIO_byte_poll_limit":32768,"WIP_status_poll_limit":65536,"poll_delay_busy_iterations":256,
                        "physical_time_calibration_verified":False,"host_transport_timeout_must_be_reviewed":True}
    report["NVM_enablement_policy"]="No enabled target option exists; root qualifies footswitch recovery and exact candidate before a separate reviewed build."
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / DEFAULT_PLAN)
    parser.add_argument("--write-report", action="store_true", help="write the design report only; never builds target code")
    parser.add_argument("--build-locked",action="store_true",help="run mock tests and build target with mutations disabled; implies --write-report")
    args = parser.parse_args()
    report = build_contract(args.plan)
    if args.build_locked:report=build_locked(report)
    if args.write_report or args.build_locked:
        (ROOT / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "execution_ready": False,
                      "executable_artifacts": len(report["executable_artifacts"]), "sectors_checked": len(report["sectors"]),
                      "pages_checked": sum(len(s["pages"]) for s in report["sectors"]),
                      "candidate_sha256": report["install_plan"]["candidate"]["sha256"],
                      "target_mutations_enabled":False,"report_written": args.write_report or args.build_locked}))


if __name__ == "__main__":
    main()
