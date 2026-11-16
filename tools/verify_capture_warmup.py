"""Compare capture warm-up with original instructions and actual dependencies."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
from capture_warmup_machine import (CaptureWarmupProgram,REGIONS,RESET_REGION,ROOT,
    CONTEXT,ARENA,ARENA_BYTES,SCRATCH,SCRATCH_BYTES,ZERO_PAGE_BYTES,WRAP,WRAP_BYTES,image_offset)
from capture_processing_machine import REGIONS as PROCESSING_REGIONS,KERNELS
from verify_capture_processing import (Memory as ProcessingMemory,IO,MAP,KERNEL,POINTER,U32,
    baseline as processing_baseline,configure as configure_processing,put,INPUT,OUTPUT,HEAD_RING)

WORK=0x01C33ED0
SOURCES=("controls","control_actions","selection","preset_storage","preset_assets","capture_loader",
    "capture_container","capture_dispatch","capture_reset","dot","head","a2l","rechannel",
    "capture_processing","capture_warmup")


def baseline(*args,**kwargs):
    memory=processing_baseline(*args,**kwargs)
    memory[0][164]=1
    return memory+(bytearray(ZERO_PAGE_BYTES),bytearray([0xB9])*WRAP_BYTES)


def long_chain(layers,taps):
    """Pack up to sixteen disjoint descriptor/coefficient/history objects."""
    memory=baseline(layers=1,taps=taps)
    descriptor=bytes(memory[1][:80]);coefficients=bytes(memory[1][0xC000:0xC400])
    size=(64+(taps-1)*2+64)*12;history=bytes(memory[1][0x1000:0x1000+size])
    assert 1<=layers<=16 and size<=0x900
    put(memory[0],8,layers,2)
    for i in range(layers):
        d=i*80;coefficient=0xC000+i*0x400;ring=0x1000+i*0x900
        memory[1][d:d+80]=descriptor;memory[1][coefficient:coefficient+0x400]=coefficients
        memory[1][ring:ring+size]=history
        for offset,value in ((32,ARENA+coefficient+0x340),(36,ARENA+coefficient+0x300),
            (44,ARENA+coefficient),(68,ARENA+ring)):put(memory[1],d+offset,value)
    return memory


class Memory(ProcessingMemory):
    def mapping(self,address,size):
        for base,array in zip((CONTEXT,ARENA,SCRATCH,0,WRAP),self.arrays):
            offset=address-base
            if 0<=offset and offset+size<=len(array) and address+size<=0x100000000:
                return ctypes.addressof(array)+offset
        return None


def configure(library):
    functions=configure_processing(library)
    fn=library.hyperrig_capture_warmup
    fn.argtypes=[POINTER,U32,ctypes.POINTER(IO)];fn.restype=ctypes.c_int
    functions["warmup"]=fn
    return functions


def c_run(functions,memory,output=0,*,scripted=False,blocked=None,kernel_error=0,operation="warmup",samples=64):
    state=Memory(memory);calls=[];errors=[]
    def mapping(_opaque,address,size,writable):
        return None if blocked and blocked(address,size,writable) else state.mapping(address,size)
    def kernel(_opaque,target,parameters):
        try:
            calls.append((target,parameters,state.snapshot()))
            return kernel_error or (0 if scripted else functions["kernel"](target,parameters,ctypes.byref(io)))
        except Exception as error:errors.append(error);return -202
    io=IO(MAP(mapping),KERNEL(kernel),None)
    args=(state.arrays[0],output,ctypes.byref(io)) if operation=="warmup" else (state.arrays[0],INPUT,OUTPUT,samples,ctypes.byref(io))
    result=functions[operation](*args)
    if errors:raise errors[0]
    return {"result":result,"memory":state.snapshot(),"calls":calls}


def verify(library_path,output,mini_image=None,smoke=False):
    if not __debug__:raise RuntimeError("run without Python optimization")
    program=CaptureWarmupProgram();functions=configure(ctypes.CDLL(str(library_path.resolve())))
    counts={"warmed":0,"reset_fallback":0,"scripted_numerical":0,"carried_state":0,"processing_continuations":0}
    coverage=set();steps=numeric_calls=reset_entries=0;digest=hashlib.sha256()
    def compare(memory,output=0,*,scripted=False,carried=False):
        nonlocal steps,numeric_calls,reset_entries
        native=program.execute(memory,output,kernel=(lambda *_:None) if scripted else None)
        actual=c_run(functions,memory,output,scripted=scripted)
        for key in ("result","memory","calls"):
            if native[key]!=actual[key]:
                if key=="memory":detail=[(i,[(j,a,b) for j,(a,b) in enumerate(zip(x,y)) if a!=b][:10])
                    for i,(x,y) in enumerate(zip(actual[key],native[key])) if x!=y]
                elif key=="calls":detail=(len(actual[key]),len(native[key]),next((i for i,(x,y) in enumerate(zip(actual[key],native[key])) if x!=y),None))
                else:detail=(actual[key],native[key])
                raise AssertionError((output,key,detail))
        assert native["reset_entries"]==int(native["result"]==0)
        counts["warmed" if native["result"] else "reset_fallback"]+=1
        counts["scripted_numerical"]+=int(scripted);counts["carried_state"]+=int(carried)
        coverage.update(native["visited"]);steps+=native["steps"];reset_entries+=native["reset_entries"]
        numeric_calls+=0 if scripted else len(native["calls"])
        digest.update(json.dumps((output,scripted,native["result"])).encode())
        for data in native["memory"]:digest.update(data)
        for target,parameters,snapshot in native["calls"]:
            digest.update(target.to_bytes(4,"little")+parameters.to_bytes(4,"little"))
            for data in snapshot:digest.update(data)
        return native["memory"]
    compare(baseline(layers=1),OUTPUT)
    compare(baseline(layers=3),OUTPUT)
    memory=baseline();memory[0][164]=0;compare(memory,OUTPUT)
    if not smoke:
        for kind,taps,residual in ((0,1,0),(0,3,-3),(0,15,5),(1,6,0),(2,6,1),(2,6,-31),(3,15,0),(4,15,31),(4,15,-2),(255,6,0)):
            for layers in (1,2,3):
                for span in (0,3,63,127):
                    memory=baseline(layers=layers,taps=taps,kind=kind,residual=residual,position=0xFFFFFFE0,seed=kind+span+layers+5)
                    put(memory[0],84,span)
                    compare(memory,0 if span&1 else OUTPUT)
        for span in (1,2,31,62,64,65,511,0xFFFFFFBF,0xFFFFFFC0,0xFFFFFFFE,0xFFFFFFFF):
            memory=baseline(layers=2);put(memory[0],84,span);compare(memory,OUTPUT)
        for layers in (4,8,16):
            for taps in (1,6,15):compare(long_chain(layers,taps),OUTPUT)
        for length in (0xFFFFFFC0,0xFFFFFFC1,0xFFFFFFC2,0xFFFFFFFE,0xFFFFFFFF):
            for ring in (ARENA+0x1000,WRAP):
                memory=baseline(layers=1,taps=1);put(memory[1],76,length);put(memory[1],68,ring)
                compare(memory,OUTPUT)
        for output_token in (WORK+12,WORK+16,WORK+20,HEAD_RING,ARENA+20,ARENA+0xC000,WRAP+8):
            compare(baseline(),output_token)
        for invalid in ("layers","table","length","ring","channels0","channels1","channels2","channels4","flag","bits0","bits16","bits64"):
            memory=baseline()
            if invalid=="layers":put(memory[0],8,0,2)
            elif invalid=="table":put(memory[0],92,0)
            elif invalid in ("length","ring"):put(memory[1],76 if invalid=="length" else 68,0)
            elif invalid.startswith("channels"):memory[0][2]=int(invalid[8:])
            elif invalid=="flag":memory[0][164]=0
            else:memory[0][1]=int(invalid[4:])
            compare(memory,OUTPUT)
        for channels in (0,1,2,3,4):
            for span in (0,63,0xFFFFFFBF,0xFFFFFFFF):
                memory=baseline(layers=1,taps=1);memory[0][164]=0;memory[0][2]=channels;put(memory[0],84,span)
                compare(memory,OUTPUT)
        # Exercise the inherited reset's auxiliary loop through warm-up fallback.
        for length in (0,1,0xFFFFFFC0,0xFFFFFFC1):
            memory=baseline();memory[0][164]=0
            put(memory[0],140,ARENA+0x1A000);put(memory[0],144,ARENA+0x1A100)
            put(memory[0],148,ARENA+0x1B000);put(memory[0],152,length)
            for i in range(2):
                put(memory[1],0x1A000+i*4,ARENA+0x1B400+i*0x400)
                put(memory[1],0x1A100+i*4,length)
            compare(memory,OUTPUT)
        # The next-history count wraps to zero for this synthetic descriptor.
        # Its huge output-ring geometry exceeds the numerical adapter's domain;
        # this case deliberately scripts numerical calls and labels them below.
        memory=baseline(layers=2,taps=1);put(memory[1],80+76,0xFFFFFFC1)
        compare(memory,OUTPUT,scripted=True)
        for kind,taps in ((1,6),(3,15)):
            for sign in (-1,1):
                memory=baseline(layers=2,taps=taps,kind=kind,shift=1)
                for layer in range(2):
                    memory[1][layer*80+8]=1
                    for i in range(3):put(memory[1],0xC300+layer*0x800+i*8,sign*2**60,8)
                compare(memory,OUTPUT)
        # Complete byte state is carried through normal processing, repeated
        # warm-up and fallback, rather than recreating empty histories.
        for taps,residual in ((1,0),(6,-3),(15,0)):
            memory=baseline(layers=2,taps=taps,residual=residual)
            for _ in range(2):
                from capture_processing_machine import CaptureProcessingMachine
                machine=CaptureProcessingMachine(program,memory[:3],"process",(INPUT,OUTPUT,128),None)
                original=machine.run();actual=c_run(functions,memory,operation="process",samples=128)
                assert actual["result"]==0 and actual["memory"][:3]==original["memory"]
                assert actual["memory"][3:]==tuple(map(bytes,memory[3:]))
                assert [(a,b,s[:3]) for a,b,s in actual["calls"]]==original["calls"]
                counts["processing_continuations"]+=1;steps+=original["steps"]
                coverage.update(original["visited"]);numeric_calls+=len(original["calls"])
                digest.update(b"processing-continuation")
                for data in actual["memory"]:digest.update(data)
                memory=tuple(bytearray(x) for x in actual["memory"])
                memory=compare(memory,OUTPUT,carried=True)
                memory=tuple(bytearray(x) for x in memory)
            memory[0][164]=0;compare(memory,OUTPUT,carried=True)
    guards={"invalid_api":0,"mapping":0,"numerical_domain":0,"callback_error":0}
    if not smoke:
        state=Memory(baseline());mapping=MAP(lambda _o,address,size,_w:state.mapping(address,size))
        io=IO(mapping,KERNEL(),None);bad_io=IO(MAP(),KERNEL(),None)
        for ctx,options in ((None,ctypes.byref(io)),(state.arrays[0],None),(state.arrays[0],ctypes.byref(bad_io))):
            assert functions["warmup"](ctx,0,options)==-200;guards["invalid_api"]+=1
        for address in (ARENA+76,ARENA+68,ARENA+0x1000,WORK,WORK+16,ARENA+0xC000,ARENA+0xC300,
            ARENA+0xC340,ARENA+0x3000,HEAD_RING,OUTPUT,OUTPUT+4,OUTPUT+8):
            result=c_run(functions,baseline(),OUTPUT,blocked=lambda start,size,_w,target=address:start<=target<start+size)
            assert result["result"]==-201,(hex(address),result["result"]);guards["mapping"]+=1
        memory=baseline();memory[0][164]=0
        result=c_run(functions,memory,OUTPUT,blocked=lambda address,_n,_w:address==HEAD_RING)
        assert result["result"]==-201;guards["mapping"]+=1
        for shift in (0,32):
            memory=baseline();memory[1][6]=shift
            assert c_run(functions,memory,OUTPUT)["result"]==-202;guards["numerical_domain"]+=1
        result=c_run(functions,baseline(),OUTPUT,kernel_error=-277)
        assert result["result"]==-277 and len(result["calls"])==1;guards["callback_error"]+=1
    missing=sorted(program.warmup_code-coverage)
    if not smoke:assert missing==[0x01C12FF0],missing
    report={"schema":1,"project":"HyperRig","result":"pass","component":"reconstructed-capture-warmup",
        "functions":{name:{"start":lo,"end_exclusive":hi,"bytes_sha256":hashlib.sha256(program.warmup_regions[name]).hexdigest()}
            for name,(lo,hi) in REGIONS.items()},
        "total_comparisons":counts["warmed"]+counts["reset_fallback"]+counts["processing_continuations"],"comparisons":counts,
        "actual_numerical_calls":numeric_calls,"actual_reset_entries":reset_entries,"native_steps":steps,
        "result_digest":digest.hexdigest(),"c_only_guards":guards,
        "instruction_coverage":{"new_decoded":len(program.warmup_code),"new_visited":len(coverage&program.warmup_code),
            "all_decoded":len(program.code),"all_visited":len(coverage),"unvisited_new":missing,
            "unvisited_all":sorted(set(program.code)-coverage),
            "missing_classification":{"0x01c12ff0":"Redundant loop fall-through: the final index branches at 0x01c12fa0 to the final layer call and then the head-history fill; the saved layer count is unchanged."},
            "unvisited_reused_by_region":{name:sorted(pc for pc in set(program.code)-coverage if lo<=pc<hi)
                for name,(lo,hi) in ({"reset":RESET_REGION}|PROCESSING_REGIONS|KERNELS).items()},
            "reused_gap_scope":"Earlier complete regions are loaded for numerical/reset dependencies and carried processing; this corpus does not re-exercise every earlier branch."},
        "hardware_test":False,"audio_test":False,"firmware_changed":False,"flashable":False}
    paths=[f"firmware/src/hyperrig_{name}.c" for name in SOURCES]
    paths += [f"firmware/include/hyperrig/hyperrig_{name}.h" for name in SOURCES]
    paths += ["tools/capture_warmup_machine.py","tools/verify_capture_warmup.py","tools/build_capture_warmup.py",
        "tests/test_capture_warmup_machine.py","tests/capture_warmup_sanitize.c",
        "tools/capture_processing_machine.py","tools/verify_capture_processing.py","tools/dot_machine.py",
        "tools/control_machine.py","tools/control_action_machine.py","research/input-manifest.json","hyperrig/jieli.py",
        "upstream/pi32v2-isa/pi32v2isa/codec.py","upstream/pi32v2-isa/pi32v2isa/table.py","upstream/pi32v2-isa/isa/pi32v2.toml"]
    report["source_sha256"]={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    original=ROOT/"artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
    report["original_image_sha256"]=hashlib.sha256(original.read_bytes()).hexdigest()
    report["library_sha256"]=hashlib.sha256(library_path.read_bytes()).hexdigest()
    regions=REGIONS|{"reset":RESET_REGION}|PROCESSING_REGIONS|KERNELS
    raw_regions=program.raw_regions|program.kernel_regions|program.warmup_regions
    report["bound_regions"]={name:{"start":lo,"end_exclusive":hi,"bytes_sha256":hashlib.sha256(raw_regions[name]).hexdigest()}
        for name,(lo,hi) in regions.items()}
    if mini_image:
        from hyperrig.jieli import unpack_app
        digest=hashlib.sha256(mini_image.read_bytes()).hexdigest()
        assert digest=="d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
        decoded=unpack_app(mini_image.read_bytes())[2]["app.bin"]
        for name,(lo,hi) in regions.items():assert decoded[image_offset(lo):image_offset(hi)]==raw_regions[name],name
        report["mini_v4_binding"]={"image_sha256":digest,"identical_regions":list(regions)}
    if output:output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("total_comparisons","comparisons","actual_numerical_calls","actual_reset_entries")}|
        {"instruction_coverage":{k:v for k,v in report["instruction_coverage"].items() if k!="unvisited_all"}}))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--library",type=Path,required=True)
    p.add_argument("--output",type=Path);p.add_argument("--mini-image",type=Path);p.add_argument("--smoke",action="store_true")
    args=p.parse_args();verify(args.library,args.output,args.mini_image.resolve() if args.mini_image else None,args.smoke)
