"""Extend the frozen application inventory with the verified stage capability table.

Only the exact forty-byte table is excluded. Each selected module retains its
declared regions, loaded-model gaps and explicit external execution boundaries.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from inventory_reverse import ROOT,REFERENCE_SHA,address,hex_address,local,sha
from inventory_reverse_application import ApplicationInventory

TABLE=(0x0203B480,0x0203B4A8)
TABLE_SHA="ad42fb64992b7995f180484ba717298b55c46909537d0e9a01ee333cf4662362"
CONSUMERS={
    "capability":{
        "bounds":(0x01C0558C,0x01C055A8),
        "sites":((0x01C0558C,2,"r0 = b[r0+0] (u)"),
            (0x01C0558E,6,"r2 = 33797248"),
            (0x01C05594,4,"r0 = b[r0+r2] (u)"),
            (0x01C0559E,2,"r1 = r2 << 1"),
            (0x01C055A0,2,"r0 >>= r1"),
            (0x01C055A2,4,"r0 = r0 & 0x3"))},
    "active":{
        "bounds":(0x01C055D2,0x01C05618),
        "sites":((0x01C055D4,2,"r3 = b[r0+0] (u)"),
            (0x01C055EA,6,"r1 = 33797248"),
            (0x01C055F0,4,"r1 = b[r3+r1] (u)"),
            (0x01C055F4,2,"r4 = r1 >> 5"),
            (0x01C05604,4,"r0 = h[r0+r4<<1] (u)"))},
}


def table_evidence(report,raw,consumer_raw,decoded):
    """Bind data bytes, complete consumers and their original table accesses."""
    if report.get("result")!="pass" or report.get("original_image_sha256")!=REFERENCE_SHA:
        raise ValueError("stage table requires passing evidence for the pinned image")
    try:
        item=report["static_data"]["effect_capabilities"]
        bounds=address(item["start"]),address(item["end_exclusive"])
        digest=item["sha256"]
        functions=report["functions"]
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError("missing or malformed stage capability evidence") from error
    if bounds!=TABLE or len(raw)!=TABLE[1]-TABLE[0] or sha(raw)!=TABLE_SHA or digest!=TABLE_SHA:
        raise ValueError("stage capability range or bytes differ from the pinned table")
    consumers={}
    for name,spec in CONSUMERS.items():
        try:
            item=functions[name]
            bounds=address(item["start"]),address(item["end_exclusive"])
            data=consumer_raw[name]
            instructions=decoded[name]
        except (KeyError,TypeError,ValueError) as error:
            raise ValueError("missing complete stage capability consumer") from error
        if (bounds!=spec["bounds"] or item.get("bytes_sha256",item.get("sha256"))!=sha(data)
            or not all(site in instructions for site in spec["sites"])):
            raise ValueError("stage table lacks its complete consumer and decoded index sites")
        consumers[name]={"start":hex_address(bounds[0]),"end_exclusive":hex_address(bounds[1]),
            "sha256":sha(data),"instruction_sites":[{"address":hex_address(pc),"size":size,
                "instruction":text} for pc,size,text in spec["sites"]]}
    return {"start":hex_address(TABLE[0]),"end_exclusive":hex_address(TABLE[1]),
        "bytes":len(raw),"sha256":TABLE_SHA,"kind":"effect_stage_capabilities",
        "table_bytes":list(raw),"type_index_domain":[0,39],"consumers":consumers}


class StageInventory(ApplicationInventory):
    def __init__(self,parser_report,processing_report,ir_report,application_report,
                 ir_processing_report,audio_report,stage_report,additional_reports=()):
        self.stage_report=local(stage_report).relative_to(ROOT).as_posix()
        self.stage_table={}
        super().__init__(parser_report,processing_report,ir_report,application_report,
            ir_processing_report,audio_report,[self.stage_report,*additional_reports])

    def add_known_data(self):
        super().add_known_data()
        evidence=table_evidence(json.loads(self.read(self.stage_report)),self.raw(*TABLE),
            {name:self.raw(*spec["bounds"]) for name,spec in CONSUMERS.items()},
            {name:self.decode(*spec["bounds"]) for name,spec in CONSUMERS.items()})
        if any(lo<TABLE[1] and TABLE[0]<hi for lo,hi,_ in self.data_ranges):
            raise ValueError("stage capability table overlaps a prior data exclusion")
        evidence["report"]=self.stage_report
        self.stage_table=evidence
        self.data_ranges.append((*TABLE,"effect_stage_capabilities"))

    def run(self):
        report=super().run()
        self.read("tools/inventory_reverse_stage.py")
        report["schema"]=6
        report["stage_inventory_adapter"]="tools/inventory_reverse_stage.py"
        report["stage_capability_table"]=self.stage_table
        report["audits"]["stage_table_bytes_full_consumers_and_original_index_sites_verified"]=True
        report["scope_policy"].append(
            "only the exact forty-byte stage capability table is excluded as data; "
            "its compared type index domain is 0..39, not an inferred bound on arbitrary firmware state")
        report["input_sha256"]=dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject altered bindings and check both exact exclusion endpoints."""
    app=local("analysis/firmware/m571_g_app/app.bin").read_bytes()
    raw=app[TABLE[0]-0x02000120:TABLE[1]-0x02000120]
    consumer_raw={name:("self-test "+name).encode("ascii") for name in CONSUMERS}
    decoded={name:spec["sites"] for name,spec in CONSUMERS.items()}
    valid={"result":"pass","original_image_sha256":REFERENCE_SHA,
        "static_data":{"effect_capabilities":{"start":TABLE[0],"end_exclusive":TABLE[1],"sha256":TABLE_SHA}},
        "functions":{name:{"start":spec["bounds"][0],"end_exclusive":spec["bounds"][1],
            "sha256":sha(consumer_raw[name])} for name,spec in CONSUMERS.items()}}
    evidence=table_evidence(valid,raw,consumer_raw,decoded)
    assert evidence["bytes"]==40 and evidence["table_bytes"]==list(raw)
    checks=1
    mutations=[((),"result","fail"),((),"original_image_sha256","0"*64),
        (("static_data","effect_capabilities"),"start",TABLE[0]+2),
        (("static_data","effect_capabilities"),"end_exclusive",TABLE[1]-2),
        (("static_data","effect_capabilities"),"sha256","0"*64),
        (("static_data",),"effect_capabilities",{}),((),"functions",{})]
    for name,spec in CONSUMERS.items():
        mutations.extend([(("functions",name),"start",spec["bounds"][0]+2),
            (("functions",name),"end_exclusive",spec["bounds"][1]-2),
            (("functions",name),"sha256","0"*64)])
    for path,key,value in mutations:
        bad=copy.deepcopy(valid);node=bad
        for part in path:node=node[part]
        node[key]=value
        try:table_evidence(bad,raw,consumer_raw,decoded)
        except ValueError:checks+=1
        else:raise AssertionError("altered stage table report accepted")
    invalid=[(raw[:-1],consumer_raw,decoded),(bytes(40),consumer_raw,decoded)]
    for name,spec in CONSUMERS.items():
        bad=dict(consumer_raw);bad[name]=b"wrong"
        invalid.append((raw,bad,decoded))
        for site in spec["sites"]:
            bad=dict(decoded);bad[name]=tuple(item for item in spec["sites"] if item!=site)
            invalid.append((raw,consumer_raw,bad))
    for arguments in invalid:
        try:table_evidence(valid,*arguments)
        except ValueError:checks+=1
        else:raise AssertionError("unbound stage table or consumer accepted")
    inventory=object.__new__(StageInventory)
    inventory.flash_start,inventory.flash_end=0x02000120,0x02080000
    inventory.ram_source,inventory.ram_size=0x02056780,0x2030C
    inventory.ram_start,inventory.ram_end=0x01C00000,0x01C2030C
    inventory.data_ranges=[(*TABLE,"effect_stage_capabilities")]
    for pc,expected in ((TABLE[0]-2,"flash_outside_known_data"),
        (TABLE[0],"effect_stage_capabilities"),(TABLE[1]-1,"effect_stage_capabilities"),
        (TABLE[1],"flash_outside_known_data")):
        assert inventory.classification(pc)==expected;checks+=1
    print(json.dumps({"self_test_checks":checks,"result":"pass"}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    names=("parser-report","processing-report","ir-report","application-report",
        "ir-processing-report","audio-report","stage-report")
    for name in names:parser.add_argument("--"+name)
    parser.add_argument("--add-report",action="append",default=[])
    parser.add_argument("--output",type=Path);parser.add_argument("--check",action="store_true")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args();required=tuple(getattr(args,name.replace("-","_")) for name in names)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report:parser.error("--self-test is a separate read-only operation")
        self_test();return
    if bool(args.output)==bool(args.check) or not all(required):
        parser.error("choose --output or --check and provide all seven required reports")
    output=args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/"build")):
        parser.error("use a new output directory under build/")
    report=StageInventory(*required,args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/"inventory.json").write_bytes((json.dumps(report,indent=2)+"\n").encode("utf-8"))
        manifest={"component":"stage-reverse-engineering-inventory","device_access":False,
            "files":{"inventory.json":sha((output/"inventory.json").read_bytes())}}
        (output/"build-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"summary":report["summary"],"audits":report["audits"],
        "instruction_coverage_limits":report["instruction_coverage_limits"]},indent=2))


if __name__=="__main__":main()
