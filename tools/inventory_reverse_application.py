"""Extend the immutable DSP inventory with verified application/audio tables.

New whole-region evidence retains each report's own execution gaps. A resumed
audio-task prefix or an explicit service boundary is never whole-firmware proof.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import struct

from inventory_reverse import ROOT,REFERENCE_SHA,address,hex_address,local,sha
from inventory_reverse_dsp import DspInventory

METADATA=(0x0203A614,0x0203B334)
ACCELERATOR=(0x0203BE50,0x0203BE90)
TABLE_SPECS={
    "parameter_metadata_table":{
        "bounds":METADATA,"sha256":"a267e201259b804adc7dc0cafa79238b1aa20eed21c69a685a28d60099cd2cf4",
        "consumer":"metadata","consumer_bounds":(0x0202921E,0x02029248),
        "instructions":((0x0202922A,4,"r1 = r1 * 0xC"),(0x0202922E,4,"r0 = r0 * 0x54"),
            (0x02029234,6,"r1 = 33793556"),(0x0202923C,2,"r0 = [r1+8]")),
        "kind":"effect_parameter_metadata"},
    "accelerator_tables":{
        "bounds":ACCELERATOR,"sha256":"29d78b7fdaf7dc950d337ff76fa49dcd4651295036bfafffc375d883ffc748d3",
        "consumer":"start","consumer_bounds":(0x01C124A8,0x01C12556),
        "instructions":((0x01C124D2,6,"r9 = 33799792"),(0x01C1251A,6,"r0 = 33799760")),
        "kind":"ir_accelerator_commands_and_indices"},
}
FIR_CONSUMER=(0x01C01234,0x01C01292)
FIR_TASK=(0x01C01E5E,0x01C02DBC)
FIR_SITES=((0x01C01238,2,"r9 = r0"),(0x01C0123A,4,"r0 = r1 & 0xFFFFFFFE"),
    (0x01C0123E,4,"r0 = h[r9+r0] (s)"),(0x01C01246,4,"r10 = r1 >>> 1"),
    (0x01C0127A,4,"r6 = h[r9+r4<<1] (s)"),(0x01C01288,4,"ifs (r4 < r10) goto -38"))
FIR_TABLES={
    "recording_taps9":{"bounds":(0x020364D6,0x020364E0),"taps":9,"mask":15,
        "sha256":"70ffb0a83d0a4ad829ae9c2117ea2299fed1930728656903ba9fba7950f830ee",
        "instructions":((0x01C01E72,6,"r12 = 33776854"),(0x01C0200A,2,"r1 = 9"),
            (0x01C0200C,2,"r0 = 15"),(0x01C0200E,2,"r0 = r12"),
            (0x01C02010,2,"[sp] = r0"),(0x01C02012,4,"call -3554"))},
    "recording_taps19":{"bounds":(0x02036F24,0x02036F38),"taps":19,"mask":31,
        "sha256":"7d698bd9d77e2f411313a7a634b85c8dcb84cfbe752d1a516c5334ae519ba2ea",
        "instructions":((0x01C01E72,6,"r12 = 33776854"),(0x01C02066,2,"r1 = 19"),
            (0x01C02068,2,"r0 = 31"),(0x01C0206A,4,"r5 = r12 + 2638"),
            (0x01C0206E,2,"[sp] = r0"),(0x01C02070,2,"r0 = r5"),
            (0x01C02072,4,"call -3650"))},
}


def table_evidence(name,report,raw,consumer_raw,decoded):
    """Require exact pinned data, passing provenance and decoded consumer sites."""
    spec=TABLE_SPECS[name]
    if report.get("result")!="pass" or report.get("original_image_sha256")!=REFERENCE_SHA:
        raise ValueError("new data exclusion requires a passing pinned-image report")
    try:
        record=report[name]
        bounds=address(record["start"]),address(record["end_exclusive"])
        digest=record["sha256"]
        consumer=report.get("functions",report.get("regions"))[spec["consumer"]]
        consumer_bounds=address(consumer["start"]),address(consumer["end_exclusive"])
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError("missing or malformed application data-table evidence") from error
    if bounds!=spec["bounds"] or len(raw)!=bounds[1]-bounds[0] or sha(raw)!=spec["sha256"]:
        raise ValueError("unreviewed data-table range or original bytes")
    if digest!=sha(raw):raise ValueError("table report hash differs from pinned bytes")
    if (consumer_bounds!=spec["consumer_bounds"]
        or consumer.get("bytes_sha256",consumer.get("sha256"))!=sha(consumer_raw)
        or not all(item in decoded for item in spec["instructions"])):
        raise ValueError("table lacks its exact complete consumer and decoded address/arithmetic loads")
    evidence={"start":hex_address(bounds[0]),"end_exclusive":hex_address(bounds[1]),
        "bytes":len(raw),"sha256":sha(raw),"kind":spec["kind"],
        "consumer":list(map(hex_address,consumer_bounds)),"consumer_sha256":sha(consumer_raw),
        "consumer_instruction_sites":[{"address":hex_address(pc),"size":size,"instruction":text}
            for pc,size,text in spec["instructions"]]}
    if name=="parameter_metadata_table":
        presence=[sum(bool(struct.unpack_from("<I",raw,t*84+i*12+8)[0])<<i for i in range(7)) for t in range(1,40)]
        if record.get("presence_bits")!=presence:
            raise ValueError("reported metadata presence bits differ from original type1..39 records")
        evidence.update(record_bytes=12,type_stride=84,types=40,slots_per_type=7,presence_bits=presence)
    else:
        words=struct.unpack("<16I",raw)
        evidence.update(commands=list(words[:8]),indices=list(words[8:]))
    return evidence


def fir_table_evidence(name,report,raw,consumer_raw,task_raw,consumer_decoded,task_decoded):
    """Bind only the two exact symmetric coefficient spans, never their gap."""
    spec=FIR_TABLES[name]
    if report.get("result")!="pass" or report.get("original_image_sha256")!=REFERENCE_SHA:
        raise ValueError("FIR data exclusion requires a passing pinned-image report")
    try:
        record=report["static_data"][name]
        bounds=address(record["start"]),address(record["end_exclusive"])
        functions=report.get("functions",report.get("regions"))
        fir,task=functions["fir"],functions["task"]
        fir_bounds=address(fir["start"]),address(fir["end_exclusive"])
        task_bounds=address(task["start"]),address(task["end_exclusive"])
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError("missing or malformed FIR table evidence") from error
    if (bounds!=spec["bounds"] or len(raw)!=spec["taps"]+1
        or record.get("sha256")!=spec["sha256"] or sha(raw)!=spec["sha256"]):
        raise ValueError("FIR data-table bounds/hash differ from exact original bytes")
    if (fir_bounds!=FIR_CONSUMER or task_bounds!=FIR_TASK
        or fir.get("bytes_sha256",fir.get("sha256"))!=sha(consumer_raw)
        or task.get("bytes_sha256",task.get("sha256"))!=sha(task_raw)
        or not all(item in consumer_decoded for item in FIR_SITES)
        or not all(item in task_decoded for item in spec["instructions"])):
        raise ValueError("FIR table lacks complete consumer/caller and original pointer/tap loads")
    return {"start":hex_address(bounds[0]),"end_exclusive":hex_address(bounds[1]),
        "bytes":len(raw),"sha256":sha(raw),"kind":"audio_recording_fir_coefficients",
        "taps":spec["taps"],"ring_mask":spec["mask"],
        "signed_coefficients":list(struct.unpack("<"+"h"*(len(raw)//2),raw)),
        "consumer":list(map(hex_address,FIR_CONSUMER)),"consumer_sha256":sha(consumer_raw),
        "caller":list(map(hex_address,FIR_TASK)),"caller_sha256":sha(task_raw),
        "consumer_instruction_sites":[{"address":hex_address(pc),"size":size,"instruction":text} for pc,size,text in FIR_SITES],
        "caller_instruction_sites":[{"address":hex_address(pc),"size":size,"instruction":text} for pc,size,text in spec["instructions"]]}


class ApplicationInventory(DspInventory):
    def __init__(self,parser_report,processing_report,ir_report,application_report,ir_processing_report,audio_report,additional_reports=()):
        self.application_report=local(application_report).relative_to(ROOT).as_posix()
        self.ir_processing_report=local(ir_processing_report).relative_to(ROOT).as_posix()
        self.audio_report=local(audio_report).relative_to(ROOT).as_posix()
        self.application_tables={}
        self.audio_tables={}
        super().__init__(parser_report,processing_report,ir_report,
            [self.application_report,self.ir_processing_report,self.audio_report,*additional_reports])

    def add_known_data(self):
        super().add_known_data()
        for name,filename in (("parameter_metadata_table",self.application_report),("accelerator_tables",self.ir_processing_report)):
            spec=TABLE_SPECS[name];lo,hi=spec["bounds"];a,b=spec["consumer_bounds"]
            evidence=table_evidence(name,json.loads(self.read(filename)),self.raw(lo,hi),self.raw(a,b),self.decode(a,b))
            evidence["report"]=filename
            if any(start<hi and lo<end for start,end,_ in self.data_ranges):
                raise ValueError("new application table overlaps an existing data exclusion")
            self.data_ranges.append((lo,hi,spec["kind"]))
            self.application_tables[name]=evidence
        report=json.loads(self.read(self.audio_report))
        for name,spec in FIR_TABLES.items():
            lo,hi=spec["bounds"]
            evidence=fir_table_evidence(name,report,self.raw(lo,hi),self.raw(*FIR_CONSUMER),
                self.raw(*FIR_TASK),self.decode(*FIR_CONSUMER),self.decode(*FIR_TASK))
            evidence["report"]=self.audio_report
            if any(start<hi and lo<end for start,end,_ in self.data_ranges):
                raise ValueError("FIR table overlaps an existing data exclusion")
            self.data_ranges.append((lo,hi,evidence["kind"]))
            self.audio_tables[name]=evidence

    def run(self):
        report=super().run()
        self.read("tools/inventory_reverse_application.py")
        report["schema"]=5
        report["application_inventory_adapter"]="tools/inventory_reverse_application.py"
        report["application_data_tables"]=self.application_tables
        report["audio_fir_tables"]=self.audio_tables
        report["audits"].update({"metadata_and_accelerator_tables_match_pinned_bytes_and_reports":True,
            "metadata_record_strides_and_presence_load_verified":True,"accelerator_table_address_loads_verified":True,
            "fir_table_ranges_hashes_consumer_and_caller_sites_verified":True})
        report["scope_policy"].extend([
            "the exact 3360-byte metadata and 64-byte accelerator tables are data, excluded from linear call sources and targets",
            "only the exact 10-byte and 20-byte FIR coefficient ranges are data exclusions; intervening bytes retain their independent classification",
            "a complete decoded task region retains all unvisited suffix/branch gaps; resumed prefixes and scripted services do not prove full runtime or firmware execution"])
        report["input_sha256"]=dict(sorted(self.sources.items()))
        return report


def self_test():
    """Validate all new evidence bindings and source/target exclusion endpoints."""
    app=local("analysis/firmware/m571_g_app/app.bin").read_bytes()
    checks=0
    for name,spec in TABLE_SPECS.items():
        lo,hi=spec["bounds"];raw=app[lo-0x02000120:hi-0x02000120]
        consumer_raw=b"self-test consumer";a,b=spec["consumer_bounds"]
        valid={"result":"pass","original_image_sha256":REFERENCE_SHA,
            name:{"start":lo,"end_exclusive":hi,"sha256":sha(raw)},
            "functions":{spec["consumer"]:{"start":a,"end_exclusive":b,"sha256":sha(consumer_raw)}}}
        if name=="parameter_metadata_table":
            valid[name]["presence_bits"]=[sum(bool(struct.unpack_from("<I",raw,t*84+i*12+8)[0])<<i for i in range(7)) for t in range(1,40)]
        assert table_evidence(name,valid,raw,consumer_raw,spec["instructions"])["bytes"]==hi-lo;checks+=1
        mutations=[((),"result","fail"),((),"original_image_sha256","0"*64),
            ((name,),"start",lo+2),((name,),"end_exclusive",hi-2),((name,),"sha256","0"*64),
            (("functions",spec["consumer"]),"start",a+2),(("functions",spec["consumer"]),"end_exclusive",b-2),
            (("functions",spec["consumer"]),"sha256","0"*64),((),name,{})]
        if name=="parameter_metadata_table":mutations.append(((name,),"presence_bits",[0]*39))
        for path,key,value in mutations:
            bad=copy.deepcopy(valid);node=bad
            for part in path:node=node[part]
            node[key]=value
            try:table_evidence(name,bad,raw,consumer_raw,spec["instructions"])
            except ValueError:checks+=1
            else:raise AssertionError("invalid application table evidence accepted")
        for data,consumer,decoded in ((raw[:-1],consumer_raw,spec["instructions"]),
            (bytes(len(raw)),consumer_raw,spec["instructions"]),(raw,b"wrong",spec["instructions"]),
            (raw,consumer_raw,()),*( (raw,consumer_raw,tuple(x for x in spec["instructions"] if x!=item)) for item in spec["instructions"])):
            try:table_evidence(name,valid,data,consumer,decoded)
            except ValueError:checks+=1
            else:raise AssertionError("unbound original table bytes or consumer accepted")
    for name,spec in FIR_TABLES.items():
        lo,hi=spec["bounds"];raw=app[lo-0x02000120:hi-0x02000120]
        fir_raw,task_raw=b"self-test FIR consumer",b"self-test audio task"
        valid={"result":"pass","original_image_sha256":REFERENCE_SHA,
            "static_data":{name:{"start":lo,"end_exclusive":hi,"sha256":sha(raw)}},
            "functions":{
                "fir":{"start":FIR_CONSUMER[0],"end_exclusive":FIR_CONSUMER[1],"sha256":sha(fir_raw)},
                "task":{"start":FIR_TASK[0],"end_exclusive":FIR_TASK[1],"sha256":sha(task_raw)}}}
        assert fir_table_evidence(name,valid,raw,fir_raw,task_raw,FIR_SITES,spec["instructions"])["bytes"]==hi-lo;checks+=1
        mutations=[((),"result","fail"),((),"original_image_sha256","0"*64),
            (("static_data",name),"start",lo+2),(("static_data",name),"end_exclusive",hi-2),
            (("static_data",name),"sha256","0"*64),(("static_data",),name,{})]
        for function,bounds in (("fir",FIR_CONSUMER),("task",FIR_TASK)):
            mutations.extend([(("functions",function),"start",bounds[0]+2),
                (("functions",function),"end_exclusive",bounds[1]-2),
                (("functions",function),"sha256","0"*64)])
        for path,key,value in mutations:
            bad=copy.deepcopy(valid);node=bad
            for part in path:node=node[part]
            node[key]=value
            try:fir_table_evidence(name,bad,raw,fir_raw,task_raw,FIR_SITES,spec["instructions"])
            except ValueError:checks+=1
            else:raise AssertionError("invalid FIR table evidence accepted")
        invalid=[(raw[:-1],fir_raw,task_raw,FIR_SITES,spec["instructions"]),
            (bytes(len(raw)),fir_raw,task_raw,FIR_SITES,spec["instructions"]),
            (raw,b"wrong",task_raw,FIR_SITES,spec["instructions"]),
            (raw,fir_raw,b"wrong",FIR_SITES,spec["instructions"])]
        invalid.extend((raw,fir_raw,task_raw,tuple(x for x in FIR_SITES if x!=site),spec["instructions"]) for site in FIR_SITES)
        invalid.extend((raw,fir_raw,task_raw,FIR_SITES,tuple(x for x in spec["instructions"] if x!=site)) for site in spec["instructions"])
        for arguments in invalid:
            try:fir_table_evidence(name,valid,*arguments)
            except ValueError:checks+=1
            else:raise AssertionError("unbound FIR bytes, consumer or call site accepted")
    inventory=object.__new__(ApplicationInventory)
    inventory.flash_start,inventory.flash_end=0x02000120,0x02080000
    inventory.ram_source,inventory.ram_size=0x02056780,0x2030C
    inventory.ram_start,inventory.ram_end=0x01C00000,0x01C2030C
    specs=[*TABLE_SPECS.values(),*(dict(spec,kind="audio_recording_fir_coefficients") for spec in FIR_TABLES.values())]
    inventory.data_ranges=[(*spec["bounds"],spec["kind"]) for spec in specs]
    for spec in specs:
        lo,hi=spec["bounds"]
        for pc,expected in ((lo-2,"flash_outside_known_data"),(lo,spec["kind"]),
            (hi-1,spec["kind"]),(hi,"flash_outside_known_data")):
            if inventory.classification(pc)!=expected:raise AssertionError("new data exclusion boundary changed")
            checks+=1
    for pc in (FIR_TABLES["recording_taps9"]["bounds"][1],0x02036A00,FIR_TABLES["recording_taps19"]["bounds"][0]-2):
        if inventory.classification(pc)!="flash_outside_known_data":raise AssertionError("gap between FIR tables was excluded")
        checks+=1
    print(json.dumps({"self_test_checks":checks,"result":"pass"}))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("parser-report","processing-report","ir-report","application-report","ir-processing-report","audio-report"):
        p.add_argument("--"+name)
    p.add_argument("--add-report",action="append",default=[]);p.add_argument("--output",type=Path)
    p.add_argument("--check",action="store_true");p.add_argument("--self-test",action="store_true")
    args=p.parse_args();required=(args.parser_report,args.processing_report,args.ir_report,args.application_report,args.ir_processing_report,args.audio_report)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report:p.error("--self-test is a separate read-only operation")
        self_test();return
    if bool(args.output)==bool(args.check) or not all(required):p.error("choose --output or --check and provide all six required reports")
    output=args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/"build")):p.error("use a new output directory under build/")
    report=ApplicationInventory(*required,args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/"inventory.json").write_bytes((json.dumps(report,indent=2)+"\n").encode("utf-8"))
        manifest={"component":"application-reverse-engineering-inventory","device_access":False,
            "files":{"inventory.json":sha((output/"inventory.json").read_bytes())}}
        (output/"build-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"summary":report["summary"],"audits":report["audits"],
        "instruction_coverage_limits":report["instruction_coverage_limits"]},indent=2))


if __name__=="__main__":main()
