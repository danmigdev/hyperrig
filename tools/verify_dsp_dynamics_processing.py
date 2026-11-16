"""Compare dynamics history, gain slots, cached thresholds and shared meters."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from dsp_dynamics_processing_machine import (DspDynamicsProcessingProgram,REGIONS,DEPENDENCIES,
    AUDIO_REGIONS,DYNAMICS_REGIONS,INITIALIZATION_REGIONS,MATH_REGIONS,PRIOR_REGIONS,
    MAPPED,ROOT,STATES,CONFIGURATION,CONTROL,TABLE,PRIOR_TABLE,RESET_CONFIGURATION,
    STATIC,region_bytes,BiquadProgram)
from verify_dsp_audio_path import (SOURCES as AUDIO_SOURCES, Runtime as AudioRuntime,
    DspRuntime,baseline as audio_baseline,U8,U32,I32,PINNED_IMAGE,MINI_IMAGE)
from dot_machine import signed

SOURCES=tuple(dict.fromkeys((*AUDIO_SOURCES,
    "upstream/pi32v2-isa/tools/hwtest/semantics/v3.py",
    "firmware/include/hyperrig/hyperrig_dsp_dynamics_processing.h",
    "firmware/src/hyperrig_dsp_dynamics_processing.c",
    "tools/dsp_dynamics_processing_machine.py","tools/verify_dsp_dynamics_processing.py",
    "tools/build_dsp_dynamics_processing.py","tests/test_dsp_dynamics_processing_machine.py",
    "tests/dsp_dynamics_processing_sanitize.c")))
UNITY=0x1000000


class Runtime(ctypes.Structure):
    _fields_=[("audio",AudioRuntime),("states",U8*500)]


class GuardedRuntime(ctypes.Structure):
    _fields_=[("before",U32*4),("runtime",Runtime),("after",U32*4)]


class View(ctypes.Structure):
    _fields_=[("configuration",ctypes.POINTER(U8)),("control",ctypes.POINTER(U8)),("states",ctypes.POINTER(U8))]


class CState:
    def __init__(self,memory,work):
        self.guarded=GuardedRuntime();self.runtime=self.guarded.runtime
        for i in range(4):self.guarded.before[i],self.guarded.after[i]=0x12345678+i,0x9ABCDEF0+i
        self.regions=[getattr(self.runtime.audio.dsp,name) for name,_ in DspRuntime._fields_]
        self.regions += [getattr(self.runtime.audio,name) for name,_ in AudioRuntime._fields_[1:]]+[self.runtime.states]
        for dest,raw in zip(self.regions,memory):ctypes.memmove(ctypes.addressof(dest),bytes(raw),len(raw))
        self.view=View(self.runtime.audio.dsp.configuration,self.runtime.audio.dsp.control,self.runtime.states)
        self.storage=(I32*(len(work)+2))();self.storage[0],self.storage[-1]=0x12345678,-0x12345678
        for i,value in enumerate(work):self.storage[i+1]=value
        self.work=ctypes.cast(ctypes.byref(self.storage,4),ctypes.POINTER(I32)) if work else None

    def snapshot(self):return tuple(bytes(region) for region in self.regions)
    def sample_values(self):return tuple(self.storage[1:-1])
    def guards_ok(self):
        return (tuple(self.guarded.before)==tuple(0x12345678+i for i in range(4))
            and tuple(self.guarded.after)==tuple(0x9ABCDEF0+i for i in range(4))
            and self.storage[0]==0x12345678 and self.storage[-1]==-0x12345678)


def configure(library):
    functions={}
    signatures={"reset":[ctypes.POINTER(View)],"clone":[ctypes.POINTER(View)],
        "single":[ctypes.POINTER(View),ctypes.POINTER(I32),U32],
        "dual":[ctypes.POINTER(View),ctypes.POINTER(I32),U32],
        "kernel":[ctypes.POINTER(U8),ctypes.POINTER(I32),U32,U32]}
    for name,args in signatures.items():
        f=getattr(library,"hyperrig_dsp_dynamics_processing_"+name);f.argtypes,f.restype=args,ctypes.c_int;functions[name]=f
    for name,args in {"configure":[ctypes.POINTER(DspRuntime),U32,U32,U32],
        "get":[ctypes.POINTER(DspRuntime),ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(U32)],
        "meter":[ctypes.POINTER(DspRuntime),ctypes.POINTER(U32),ctypes.POINTER(U32)]}.items():
        f=getattr(library,"hyperrig_dsp_dynamics_"+name);f.argtypes,f.restype=args,ctypes.c_int;functions[name]=f
    f=library.hyperrig_dsp_audio_path_startup;f.argtypes,f.restype=[ctypes.POINTER(AudioRuntime)],ctypes.c_int;functions["startup"]=f
    return functions


def initial(seed=1):
    memory=audio_baseline(seed)+tuple([bytearray((i*17+seed)&255 for i in range(500))])
    for bank in (0,256):
        for i in range(48):struct.pack_into("<i",memory[-1],bank+4*i,(i-24)*(seed+1))
        struct.pack_into("<9I",memory[-1],bank+192,*([UNITY]*9))
        struct.pack_into("<4I",memory[-1],bank+228,seed,0,0x12345678,0xABCDEF01)
    struct.pack_into("<3I",memory[0],52,8388607,3511,UNITY)
    struct.pack_into("<3I",memory[4],108,0,0,0)
    return memory


def block(values):
    values=list(values)
    assert len(values)==128
    return tuple([-123456789]*48+values)


def verify(library_path,output,mini_image=None):
    if not __debug__:raise RuntimeError("verification requires assertions enabled")
    program=DspDynamicsProcessingProgram();functions=configure(ctypes.CDLL(str(library_path.resolve())))
    counts=dict.fromkeys(("reset","clone","kernel","single","dual","configure","get","meter","startup"),0)
    coverage=set();digest=hashlib.sha256();rng=random.Random(0x1C1A636)
    kernel_calls=copy_calls=producer_calls=carried_calls=samples=maximum_steps=0

    def compare(memory,operation,work=(),*arguments,carried=False):
        nonlocal kernel_calls,copy_calls,producer_calls,carried_calls,samples,maximum_steps
        expected=program.execute(memory,operation,work,*arguments)
        state=CState(memory,work);view=ctypes.byref(state.view)
        outputs=[U32(0xA5A5A500+i) for i in range(3)]
        if operation=="kernel":
            pointer=ctypes.cast(ctypes.byref(state.runtime.states,256*arguments[0]),ctypes.POINTER(U8))
            result=functions[operation](pointer,state.work,*arguments[1:])
        elif operation in ("single","dual"):result=functions[operation](view,state.work,*arguments)
        elif operation in ("reset","clone"):result=functions[operation](view)
        elif operation=="startup":result=functions[operation](ctypes.byref(state.runtime.audio))
        elif operation=="configure":result=functions[operation](ctypes.byref(state.runtime.audio.dsp),*arguments)
        elif operation=="get":result=functions[operation](ctypes.byref(state.runtime.audio.dsp),*(ctypes.byref(x) for x in outputs))
        else:result=functions[operation](ctypes.byref(state.runtime.audio.dsp),
            ctypes.byref(outputs[0]) if arguments[0]&1 else None,ctypes.byref(outputs[1]) if arguments[0]&2 else None)
        assert result==(expected["value"] if operation in ("configure","meter") else 0),(operation,result,expected["value"])
        differences=[(j,[(i,a,b) for i,(a,b) in enumerate(zip(left,right)) if a!=b][:12])
            for j,(left,right) in enumerate(zip(state.snapshot(),expected["memory"])) if left!=right]
        assert not differences and state.sample_values()==expected["samples"] and state.guards_ok(),(
            operation,arguments,differences,[(i,a,b) for i,(a,b) in enumerate(zip(state.sample_values(),expected["samples"])) if a!=b][:12])
        assert tuple(x.value for x in outputs)==expected["outputs"]
        assert not expected["boundary_calls"]
        counts[operation]+=1;coverage.update(expected["visited"])
        kernel_calls+=operation=="kernel";kernel_calls+=sum(pc==REGIONS["kernel"][0] for pc,_ in expected["processing_calls"])
        copy_calls+=sum(pc==DEPENDENCIES["copy_words"][0] for pc,_ in expected["processing_calls"])
        producer_calls+=len(expected["production_calls"]);carried_calls+=carried;samples+=len(work)
        maximum_steps=max(maximum_steps,expected["steps"])
        digest.update(operation.encode()+b"\0")
        for region in expected["memory"]:digest.update(region)
        digest.update(struct.pack(f"<{len(work)}i",*expected["samples"]))
        digest.update(struct.pack("<3I",*(x.value for x in outputs)))
        return expected

    for seed in range(12):
        compare(initial(seed),"reset")
        compare(initial(seed),"clone")
    # Fast no-gain path and every potential peak location, including INT_MIN.
    for bank in (0,1):
        for threshold in (0,1,255,UNITY,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
            for value in (0,1,-1,0x7FFFFFFF,-0x80000000):
                compare(initial(),"kernel",block([value]*128),bank,threshold,3511)
    for position in range(128):
        values=[0]*128;values[position]=-0x80000000 if position&1 else 0x7FFFFFFF
        compare(initial(position),"kernel",block(values),position&1,0x1FFFFF,3511)
    # Raw gain/ring state, signed minima and all-bit-pattern arithmetic remain
    # admitted; these witnesses intentionally go beyond configured gain state.
    for seed in range(160):
        memory=initial(seed);bank=(seed&1)*256
        struct.pack_into("<12I",memory[-1],bank+192,*(rng.getrandbits(32) for _ in range(12)))
        work=tuple(signed(rng.getrandbits(32)) for _ in range(176))
        compare(memory,"kernel",work,seed&1,rng.getrandbits(32),rng.getrandbits(32))
    for gain in (0,1,UNITY-1,UNITY,UNITY+1,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
        for release in (0,1,3511,0x100000,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
            memory=initial();struct.pack_into("<I",memory[-1],224,gain);struct.pack_into("<I",memory[-1],232,1)
            compare(memory,"kernel",block([0]*128),0,0,release)
    print("Original fixed-block kernel, every peak location, INT_MIN and raw arithmetic extremes compared.",flush=True)

    for mode in ("single","dual"):
        for scale in (0,1,2,255,256,257,32768,65536,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
            for cached in (scale,(scale+1)&0xFFFFFFFF):
                memory=initial();struct.pack_into("<3I",memory[4],108,cached,0xFFFFFFF0,0x100000)
                compare(memory,mode,block([0x7FFFFFFF,-0x80000000]*64),scale)
        for level in (0,1,255,256,0x7FFFFF,0xFFFFFF,0x1000000,0x1000001,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
            memory=initial();struct.pack_into("<I",memory[0],52,level)
            compare(memory,mode,block([123456789,-987654321]*64),1)
    # Configure and startup use their actual complete original math. Subsequent
    # state and meters are carried; reset/clone are original entries as well.
    for seed,(threshold,time) in enumerate(((-200,10),(-120,100),(-3,100),(0,2000))):
        memory=compare(initial(seed),"startup")["memory"]
        memory=compare(memory,"reset",carried=True)["memory"]
        memory=compare(memory,"clone",carried=True)["memory"]
        memory=compare(memory,"configure",(),1,threshold&0xFFFFFFFF,time,carried=True)["memory"]
        memory=compare(memory,"get",carried=True)["memory"]
        for index in range(24):
            values=[signed(rng.getrandbits(32)) if index<8 else 0 for _ in range(128)]
            scale=(256,32768,65536,256)[index//6]
            memory=compare(memory,"single",block(values),scale,carried=True)["memory"]
            memory=compare(memory,"dual",block(reversed(values)),scale,carried=True)["memory"]
            if index%4==3:memory=compare(memory,"meter",(),index%4,carried=True)["memory"]
        for mask in range(4):memory=compare(memory,"meter",(),mask,carried=True)["memory"]
    print("Real startup/configure/reset/clone/sample/meter chains and threshold-cache paths compared.",flush=True)
    invalid=invalid_checks(functions)
    new=program.new_code;missing=sorted(new-coverage)
    assert not missing,[hex(pc) for pc in missing]
    groups={**{f"processing_{k}":v for k,v in REGIONS.items()},**DEPENDENCIES,
        **{f"audio_{k}":v for k,v in AUDIO_REGIONS.items()},**{f"biquad_{k}":v for k,v in BiquadProgram.REGIONS.items()},
        **{f"dynamics_{k}":v for k,v in DYNAMICS_REGIONS.items()},**{f"initialization_{k}":v for k,v in INITIALIZATION_REGIONS.items()},
        **{f"math_{k}":v for k,v in MATH_REGIONS.items()},**{f"coefficients_{k}":v for k,v in PRIOR_REGIONS.items()}}
    app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes();mini_binding=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI_IMAGE
        mini=unpack_app(raw)[2]["app.bin"]
        for start,end in (*groups.values(),*STATIC.values(),TABLE,(PRIOR_TABLE,PRIOR_TABLE+10),RESET_CONFIGURATION):
            assert region_bytes(mini,start,end)==region_bytes(app,start,end)
        mini_binding={"image_sha256":MINI_IMAGE,"all_loaded_regions_identical":sorted(groups),
            "tables_reset_configuration_and_prior_caller_windows_identical":True}
    report={"schema":1,"project":"HyperRig","result":"pass","scope":"complete dynamics sample kernel and direct reset/copy/callers with real configuration",
        "original_image_sha256":PINNED_IMAGE,
        "regions":{name:{"start":lo,"end_exclusive":hi,"sha256":hashlib.sha256(program.processing_regions[name]).hexdigest(),
            "decoded":sum(lo<=pc<hi for pc in new),"visited":sum(lo<=pc<hi for pc in coverage)} for name,(lo,hi) in REGIONS.items()},
        "dependencies":{name:{"start":lo,"end_exclusive":hi,"sha256":hashlib.sha256(program.dependencies[name]).hexdigest(),
            "decoded":sum(lo<=pc<hi for pc in program.code),"visited":sum(lo<=pc<hi for pc in coverage)} for name,(lo,hi) in DEPENDENCIES.items()},
        "comparisons":counts,"total_comparisons":sum(counts.values()),"actual_dynamics_kernel_calls":kernel_calls,
        "actual_copy_calls":copy_calls,"complete_coefficient_producer_calls":producer_calls,
        "work_words_checked":samples,"carried_calls":carried_calls,"maximum_instruction_packets":maximum_steps,
        "invalid_api_checks":invalid,"instruction_coverage":{"new_visited":len(new&coverage),"new_decoded":len(new),
            "all_visited":len(coverage),"all_decoded":len(program.code),"unvisited_new":missing},
        "compared":["all twelve runtime memory regions","all176 working words per sample call","native configuration/meter results and optional outputs",
            "actual startup/configuration through carried reset/copy/single/dual/meter entries"],
        "outputs_and_state_sha256":digest.hexdigest(),"mini_v4_binding":mini_binding,
        "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "library_sha256":hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test":False,"audio_test":False,"firmware_changed":False,
        "limitations":["fixed176-word working buffer;128 input words at+48 and128 output words at0",
            "buffers and borrowed view must be disjoint; no concurrent mutation or re-entry",
            "all raw integer state/arguments admitted; inherited float configuration requires positive divisor",
            "enclosing audio scheduler, notification callback and physical timing/units are outside this milestone",
            "retains pinned ISA binary32/arithmetic/positive REP semantics; no new hardware measurement"]}
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("result","comparisons","total_comparisons","instruction_coverage")}))
    return report


def invalid_checks(functions):
    memory=initial();state=CState(memory,block([0]*128));before=state.snapshot();work=state.sample_values();count=0
    for name in ("reset","clone","single","dual"):
        for view in (None,ctypes.byref(View(None,state.view.control,state.view.states)),
            ctypes.byref(View(state.view.configuration,None,state.view.states)),ctypes.byref(View(state.view.configuration,state.view.control,None))):
            args=[view]+([state.work,256] if name in ("single","dual") else [])
            assert functions[name](*args)==-1;count+=1
        if name in ("single","dual"):
            assert functions[name](ctypes.byref(state.view),None,256)==-1;count+=1
    for args in ((None,state.work,0,0),(state.view.states,None,0,0),(None,None,0,0)):
        assert functions["kernel"](*args)==-1;count+=1
    assert state.snapshot()==before and state.sample_values()==work and state.guards_ok()
    return count


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--library",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--mini-image",type=Path);args=p.parse_args()
    if args.output.exists():p.error("verification output must be new")
    verify(args.library,args.output,args.mini_image)


if __name__=="__main__":main()
