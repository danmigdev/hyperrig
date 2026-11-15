"""Build the separate HYW1 operational RAM target; no transport/device I/O.

Default validates local inputs. --build runs host fault tests and emits target
gate-one artifacts. These artifacts contain NOR mutation code; they do not
assert installation readiness and are never uploaded or executed by this tool.
The frozen gate-zero writer is a checked input and is never modified.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import build_mini_app_writer as frozen

sha,crc,require,workspace_file=frozen.sha,frozen.crc,frozen.require,frozen.workspace_file
APP_START,APP_END,SECTOR_BYTES,PAGE_BYTES=frozen.APP_START,frozen.APP_END,frozen.SECTOR_BYTES,frozen.PAGE_BYTES
BASES=(0x1C20000,0x1C28000)
DEFAULT_PLAN=ROOT/"build/mini-install-plan-v2/install-plan.json"
OUT=ROOT/"build/mini-app-writer-operational"
REPORT=ROOT/"research/mini-app-writer-operational.json"
FROZEN_REPORT="research/mini-app-writer.json"
FROZEN_SHA="de8b7629eebaa39bb39dea55a4a7173f94d48250dfa7bf1347ca121cf85d0a64"
ORIGINAL_BLOCK="""#ifdef HYPERRIG_WRITER_HOST_MUTATIONS
const uint32_t hyperrig_writer_mutations_enabled=1;
#else
const uint32_t hyperrig_writer_mutations_enabled=0;
#endif"""
OPERATIONAL_BLOCK="""#if defined(HYPERRIG_WRITER_OPERATIONAL_TARGET) && !defined(HYPERRIG_WRITER_TARGET)
#error Operational target switch requires the target ABI
#endif
#if defined(HYPERRIG_WRITER_HOST_MUTATIONS) || defined(HYPERRIG_WRITER_OPERATIONAL_TARGET)
const uint32_t hyperrig_writer_mutations_enabled=1;
#else
const uint32_t hyperrig_writer_mutations_enabled=0;
#endif"""
PIO_DELAY_OLD="p->io.settle(p->io.user,256);"
PIO_DELAY_NEW="p->io.settle(p->io.user,768);"


def page_order(sector):
    require(frozen.app_range(sector,4096,alignment=4096),"unaligned/outside MINI application sector")
    indices=list(range(1,16))+[0] if sector==APP_START else list(range(16))
    return [sector+i*PAGE_BYTES for i in indices]


def derive_core(source):
    text=source.decode("utf-8").replace("\r\n","\n")
    require(text.count(ORIGINAL_BLOCK)==1,"frozen mutation-switch preimage differs")
    derived=text.replace(ORIGINAL_BLOCK,OPERATIONAL_BLOCK)
    require(derived.replace(OPERATIONAL_BLOCK,ORIGINAL_BLOCK)==text,"source derivation not reversible")
    return derived.encode("utf-8")


def derive_pio(source):
    text=source.decode("utf-8").replace("\r\n","\n")
    require(text.count(PIO_DELAY_OLD)==1,"frozen PIO poll-delay preimage differs")
    result=text.replace(PIO_DELAY_OLD,PIO_DELAY_NEW)
    require(result.replace(PIO_DELAY_NEW,PIO_DELAY_OLD)==text,"PIO derivation not reversible")
    return result.encode("utf-8")


def observer_evidence():
    name="analysis/hardware/mini-writer-observer-resume-run.json"
    raw=workspace_file(name).read_bytes()
    require(sha(raw)=="5ee727367385c855140ef19dd03674a4603847fd1be5d9a6de5ed4128dafc777","completed gate-zero run differs")
    run=json.loads(raw)
    require(run["phase"]=="complete" and run["observation_passed"] is True and run["stock_return_verified"] is True
            and run["presets_unchanged"] is True and run["firmware_write"] is False,"observer did not complete without NVM mutation")
    require(run["observation"]["manifest_sha256"]==FROZEN_SHA,"observer executed a different gate-zero writer")
    for source in ("tools/probe_mini_app_writer.py","tools/build_mini_app_writer.py"):
        require(sha(workspace_file(source).read_bytes())==run["source_pins"][source],"executed observer source changed: "+source)
    pins={name:sha(raw)};audits=[]
    for index in range(13):
        name=f"analysis/hardware/mini-writer-observer-audit-{index:02}.bin";raw=workspace_file(name).read_bytes()
        item=frozen.validate_audit_record(raw,base=0x1C20000,build_tag=run["observation"]["build_tag"])
        require(item["error"]==0 and item["rx_guards_ok"]==item["stack_guards_ok"]==1,"observer audit error/guard")
        require(item==run["writer_final_state"]["audit_records"][index],"raw audit differs from completed pinned run")
        pins[name]=sha(raw);audits.append(item)
    require(audits[-1]["read_bytes"]==8192 and audits[-1]["raw_receive_return"]==260
            and audits[-1]["staged"]==audits[-1]["echoed"]==1,"observer final stage/echo differs")
    for name,key in (("analysis/hardware/mini-writer-observer-preimage.bin","preimage_sha256"),
                     ("analysis/hardware/mini-writer-observer-echo.bin","page_sha256")):
        raw=workspace_file(name).read_bytes();require(sha(raw)==run["observation"][key],"observer bytes differ: "+name);pins[name]=sha(raw)
    return {"source_sha256":pins,"verified_raw_audits":len(audits),"final_audit":audits[-1],
            "hardware_gate_zero_pass":True,"hardware_erase_program_qualified":False,
            "observed_candidate_sha256":run["observation"]["candidate_sha256"],
            "operational_candidate_is_a_different_image":True}


def checked_inputs(plan_path=DEFAULT_PLAN):
    report_raw=workspace_file(FROZEN_REPORT).read_bytes()
    require(sha(report_raw)==FROZEN_SHA,"frozen gate-zero report changed")
    base=json.loads(report_raw)
    for name,digest in base["source_sha256"].items():
        require(sha(workspace_file(name).read_bytes())==digest,"frozen writer source changed: "+name)
    plan_path=workspace_file(plan_path);plan_raw=plan_path.read_bytes();plan=json.loads(plan_raw)
    data={key:workspace_file(plan[key]["path"]).read_bytes() for key in ("candidate","unit_backup","rollback")}
    sectors=frozen.validate_plan(plan,data["candidate"],data["unit_backup"],data["rollback"])
    core=workspace_file("firmware/mini/app_writer/writer.c").read_bytes();derived=derive_core(core)
    return {"plan":plan,"plan_path":plan_path.relative_to(ROOT).as_posix(),"plan_sha256":sha(plan_raw),
            "data":data,"sectors":sectors,"core":derived,"frozen_report":base,
            "pio":derive_pio(workspace_file("firmware/mini/app_writer/nor_pio.c").read_bytes()),"observer_evidence":observer_evidence()}


def _gate_location(raw):
    require(raw[:7]==b"\x7fELF\x01\x01\x01" and len(raw)>=52,"expected little-endian ELF32")
    h=struct.unpack_from("<HHIIIIIHHHHHH",raw,16)
    require(h[8]==32 and h[10]==40 and h[11]>0,"ELF table stride differs")
    require(h[4]+h[8]*h[9]<=len(raw) and h[5]+h[10]*h[11]<=len(raw),"ELF tables truncated")
    loads=[struct.unpack_from("<8I",raw,h[4]+i*32) for i in range(h[9])]
    loads=[p for p in loads if p[0]==1];require(len(loads)==1,"one load segment required")
    p=loads[0]
    sections=[struct.unpack_from("<10I",raw,h[5]+i*40) for i in range(h[11])]
    found=[]
    for section in sections:
        if section[1]!=2:continue
        require(section[9]==16 and not section[5]%16 and section[6]<len(sections),"bad symbol table")
        strings=sections[section[6]]
        require(strings[1]==3 and strings[4]+strings[5]<=len(raw) and section[4]+section[5]<=len(raw),"symbols truncated")
        names=raw[strings[4]:strings[4]+strings[5]]
        for at in range(section[4],section[4]+section[5],16):
            name,address,size,info,other,index=struct.unpack_from("<IIIBBH",raw,at)
            require(name<len(names) and b"\0" in names[name:],"invalid symbol string")
            if names[name:names.index(0,name)]==b"hyperrig_writer_mutations_enabled":
                require(index and size==4 and p[2]<=address<=p[2]+p[4]-4,"gate symbol extent differs")
                found.append(p[1]+address-p[2])
    require(len(found)==1 and found[0]<=len(raw)-4,"single initialized mutation gate required")
    return found[0]


def inspect_operational_elf(raw,base):
    """Require actual gate1, then reuse frozen layout checks on a memory copy.

    Only four gate-data bytes in the temporary validator input are normalized.
    The emitted ELF/payload always retain the checked value1 and original hash.
    """
    offset=_gate_location(raw)
    require(raw[offset:offset+4]==b"\1\0\0\0","operational ELF must contain constant gate1")
    normalized=raw[:offset]+bytes(4)+raw[offset+4:]
    payload,item=frozen.inspect_writer_elf(normalized,base)
    relative=item["mutation_gate_address"]-base
    actual=payload[:relative]+b"\1\0\0\0"+payload[relative+4:]
    item.update(elf_sha256=sha(raw),payload_sha256=sha(actual),mutation_gate_value=1,
                physical_NVM_write_enabled=True,hardware_executed=False)
    return actual,item


def contract(inputs):
    plan=inputs["plan"]
    return {"schema":1,"project":"HyperRig","target":"tank-mini","kind":"bounded-app-writer-operational",
        "protocol":"HYW1","offline_only":True,"device_access_performed":False,"execution_ready":False,
        "target_mutations_enabled":True,"hardware_mutations_executed":False,
        "frozen_observer_manifest":{"path":FROZEN_REPORT,"sha256":FROZEN_SHA},
        "derivation":{"source":"firmware/mini/app_writer/writer.c","source_sha256":sha(workspace_file("firmware/mini/app_writer/writer.c").read_bytes()),
                      "derived_sha256":sha(inputs["core"]),"normalizes_line_endings_only_outside_one_reversible_macro_block":True,
                      "preimage":ORIGINAL_BLOCK,"replacement":OPERATIONAL_BLOCK},
        "pio_derivation":{"source":"firmware/mini/app_writer/nor_pio.c","source_sha256":sha(workspace_file("firmware/mini/app_writer/nor_pio.c").read_bytes()),
                          "derived_sha256":sha(inputs["pio"]),"preimage":PIO_DELAY_OLD,"replacement":PIO_DELAY_NEW},
        "observer_evidence":inputs["observer_evidence"],
        "install_plan":{"path":inputs["plan_path"],"sha256":inputs["plan_sha256"],
                        **{key:plan[key] for key in ("candidate","unit_backup","rollback","changed_sectors","proposed_sector_order")}},
        "physical_write_allowlist":[APP_START,APP_END],"jedec_hex":"eb6014","sector_bytes":4096,"page_bytes":256,
        "sectors":[{**sector,"program_page_order":page_order(sector["physical_address"])} for sector in inputs["sectors"]],
        "header_sector_last":True,"header_page_last":True,"separate_early_header_invalidation":False,
        "power_loss_atomicity_proven":False,"stock_OTA_fallback_qualified":False,
        "power_loss_gap":"Old valid header can execute mixed code while earlier sectors are being replaced, before the final guard is installed.",
        "post_install_state":"ROM USB remains active; no automatic reset, boot, retry or rollback",
        "timeout_semantics":"Finite target loops; physical elapsed-time upper bound not qualified. Any host timeout is terminal and ambiguous.",
        "timing_model":{"clock_source":"research/mini-rom-clock.json:stock_replay.nominal", "cpu_nominal_hz":48000000,
            "SPI_clock_inference":"upstream/m-bootloader/docs/SPEC.md:81; source/(baud+1), 48MHz/16=3MHz",
            "WIP_polls":65536,"busy_settle_iterations":768,"CS_settle_iterations_per_status_pair":160,
            "settle_ELF_loop":"nop; if (--r1 != 0) goto -6", "assumed_cycles_per_iteration":[2,3,4],
            "delay_CS_and_SPI_seconds_at_48MHz":[65536*((768+160)*n/48000000+32/3000000) for n in (2,3,4)],
            "additional_callback_MMIO_poll_CPU_overhead_not_counted":True,
            "upstream_comparison":"platform.c:ready(): 30000 polls with hal_delay_us(100), about3 seconds plus status overhead",
            "nominal_order_of_magnitude":"a few seconds at48MHz; not a measured upper bound",
            "host_SPTD_timeout_seconds":10,"stuck_transfer_can_exceed_host_timeout":True,
            "calibrated":False,"NOR_datasheet_max_erase_time_asserted":False},
        "qualification_gates":{"physical_observer_gate0_pass":True,"physical_erase_program_pass":False,
                               "exact_candidate_first_boot_pass":False,"independent_recovery_from_valid_image_hang":False},
        "executable_artifacts":[]}


def build(plan_path=DEFAULT_PLAN):
    inputs=checked_inputs(plan_path);report=contract(inputs)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"writer.c").write_bytes(inputs["core"])
    (OUT/"nor_pio.c").write_bytes(inputs["pio"])
    original_test=workspace_file("firmware/mini/app_writer/test_writer.c").read_text(encoding="utf-8")
    require(original_test.count("build/mini-app-writer/host-stage-")==2,"host fixture-output paths changed")
    test_source=original_test.replace("build/mini-app-writer/host-stage-","build/mini-app-writer-operational/host-stage-")
    (OUT/"test_writer_reference.c").write_text(test_source,encoding="utf-8",newline="\n")
    test_pio=workspace_file("firmware/mini/app_writer/test_pio.c").read_text(encoding="utf-8")
    require(test_pio.count("assert(n==40||n==256)")==1 and test_pio.count('    printf("{')==1,"PIO mock preimage changed")
    test_pio=test_pio.replace("assert(n==40||n==256)","assert(n==40||n==768)").replace('    printf("{','    nor.poll_delay(nor.user);\n    printf("{')
    (OUT/"test_pio_reference.c").write_text(test_pio,encoding="utf-8",newline="\n")
    source_names=["firmware/mini/app_writer/entry.c","firmware/mini/app_writer/nor_pio.c","firmware/mini/app_writer/writer.h",
        "firmware/mini/app_writer/writer.ld","firmware/mini/boot/runtime.c","firmware/mini/rom_stack/rom_stack_pi32v2.S",
        "firmware/mini/rom_stack/rom_stack.h","firmware/mini/app_writer_operational/test_order.c",
        "firmware/mini/app_writer_operational/README.md","tools/build_mini_app_writer_operational.py"]
    tag=int(sha(inputs["core"]+inputs["pio"]+b"".join(workspace_file(n).read_bytes() for n in source_names))[:8],16)
    (OUT/"build_tag.h").write_text(f"#define HYPERRIG_WRITER_BUILD_TAG UINT32_C(0x{tag:08x})\n",encoding="utf-8",newline="\n")
    rel=OUT.relative_to(ROOT).as_posix()
    prefix=["wsl.exe","--distribution","Ubuntu","--exec"] if os.name=="nt" else []
    def run(args):
        result=subprocess.run(prefix+args,cwd=ROOT,text=True,capture_output=True)
        if result.returncode:raise RuntimeError(" ".join(args)+"\n"+result.stdout+result.stderr)
        return result.stdout
    common=["-std=c99","-Wall","-Wextra","-Werror","-Ifirmware/mini/app_writer","-I"+rel]
    core=rel+"/writer.c";pio=rel+"/nor_pio.c";tests={}
    for name,flags,files in (("host-order",["-DHYPERRIG_WRITER_HOST_MUTATIONS"],[core,"firmware/mini/app_writer_operational/test_order.c"]),
                             ("host-pio",[],[core,pio,rel+"/test_pio_reference.c"])):
        exe=rel+"/"+name
        run(["gcc",*common,"-O1","-g","-fsanitize=address,undefined","-fno-sanitize-recover=all",*flags,*files,"-o",exe])
        tests[name]=[json.loads(line) for line in run([exe]).splitlines() if line.strip()]
    vendor="tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/";objects=[]
    for source in ("firmware/mini/app_writer/entry.c",core,pio,"firmware/mini/boot/runtime.c","firmware/mini/rom_stack/rom_stack_pi32v2.S"):
        obj=rel+"/"+Path(source).stem+".o"
        run([vendor+"clang","-target","pi32v2","-mcpu=r3",*common,"-Os","-ffreestanding","-fno-builtin",
             "-DHYPERRIG_WRITER_TARGET","-DHYPERRIG_WRITER_OPERATIONAL_TARGET","-c",source,"-o",obj]);objects.append(obj)
    artifacts=[]
    for base in BASES:
        stem=f"{rel}/hyperrig-writer-operational-{base:08x}"
        run([vendor+"ld","-z","max-page-size=0x20","-z","common-page-size=0x20","--defsym",f"PROBE_ADDRESS={base}",
             "-T","firmware/mini/app_writer/writer.ld",*objects,"-Map",stem+".map","-o",stem+".elf"])
        image,item=inspect_operational_elf((ROOT/(stem+".elf")).read_bytes(),base)
        (ROOT/(stem+".bin")).write_bytes(image)
        (ROOT/(stem+".asm")).write_text(run([vendor+"objdump","-d",stem+".elf"]),encoding="utf-8",newline="\n")
        artifacts.append({**item,"file":stem+".bin","elf":stem+".elf"})
    source_names.extend(("firmware/mini/app_writer/test_writer.c","firmware/mini/app_writer/test_pio.c",
                         "tools/build_mini_app_writer.py","tools/verify_mini_rom_stack.py","tools/install_mini_app.py",
                         "tools/probe_mini_app_writer.py","tests/test_mini_app_install.py","research/mini-rom-clock.json",
                         "upstream/m-bootloader/src/platform.c"))
    report.update(build_tag=tag,host_tests=tests,executable_artifacts=artifacts,
                  source_sha256={name:sha(workspace_file(name).read_bytes()) for name in source_names},
                  object_sha256={name:sha(workspace_file(name).read_bytes()) for name in objects})
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,default=DEFAULT_PLAN)
    parser.add_argument("--build",action="store_true",help="host tests + separate gate-one ELF; never uploads")
    args=parser.parse_args()
    result=build(args.plan) if args.build else contract(checked_inputs(args.plan))
    print(json.dumps({key:result[key] for key in ("kind","device_access_performed","execution_ready",
        "target_mutations_enabled","install_plan","header_page_last","power_loss_atomicity_proven","executable_artifacts")},indent=2))


if __name__=="__main__":main()
