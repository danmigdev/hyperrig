"""Compare reconstructed capture runtime with decoded original instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
from capture_processing_machine import (CaptureProcessingProgram,REGIONS,KERNELS,ROOT,
    CONTEXT,ARENA,ARENA_BYTES,SCRATCH,SCRATCH_BYTES,ARITIES,TABLE_START,TABLE_END,image_offset)

LAYERS=ARENA
INPUT,OUTPUT,DRY,SUM=ARENA+0x18000,ARENA+0x19000,ARENA+0x17000,ARENA+0x16000
HEAD_RING,HEAD_WEIGHTS,RECHANNEL_WEIGHTS=ARENA+0x11000,ARENA+0x10000,ARENA+0x10800
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
KERNEL=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,U32,U32)
POINTER=ctypes.POINTER(ctypes.c_uint8)


class IO(ctypes.Structure):
    _fields_=[("map",MAP),("kernel",KERNEL),("opaque",ctypes.c_void_p)]


def put(data,offset,value,size=4):
    data[offset:offset+size]=(value&((1<<(size*8))-1)).to_bytes(size,"little")


def baseline(layers=2,taps=6,kind=None,residual=0,position=0,seed=1,shift=13,dilation=2):
    rng=random.Random(seed)
    context=bytearray(228); arena=bytearray([0xA7])*ARENA_BYTES; scratch=bytearray([0x39])*SCRATCH_BYTES
    context[1:4]=bytes((32,3,5)); context[56]=15;context[57]=14
    put(context,8,layers,2)
    for offset,value in ((60,RECHANNEL_WEIGHTS),(68,HEAD_WEIGHTS),(72,0),(76,0),
        (80,HEAD_RING),(84,127),(88,position),(92,LAYERS)):put(context,offset,value)
    length=64+(taps-1)*dilation
    for layer in range(max(layers,1)):
        d=layer*80; ring=ARENA+0x1000+layer*0x2000; coefficient=ARENA+0xC000+layer*0x800
        arena[d:d+80]=bytes(80)
        arena[d]=taps;put(arena,d+2,dilation,2)
        arena[d+6]=shift;arena[d+8]=min(31,shift+1);arena[d+9]=residual&255;arena[d+10]=4
        arena[d+11]=(1 if taps==6 else 3 if taps==15 else 0)+(1 if residual and taps in (6,15) else 0) if kind is None else kind
        arena[d+64]=1
        for offset,value in ((12,0x19999A),(32,coefficient+0x340),(36,coefficient+0x300),
            (44,coefficient),(52,-123),(56,4321),(60,0x12345678),(68,ring),(76,length)):
            put(arena,d+offset,value)
        values=[rng.randrange(-0x1000000,0x1000000) for _ in range(length*3)]
        values+=values[:192]
        for i,v in enumerate(values):put(arena,ring-ARENA+i*4,v)
        for i in range(taps*9+3):put(arena,coefficient-ARENA+i*2,rng.randrange(-32768,32768),2)
        for i in range(9):put(arena,coefficient-ARENA+0x340+i*2,rng.randrange(-300,301),2)
        for i in range(3):put(arena,coefficient-ARENA+0x300+i*8,rng.randrange(-2**40,2**40),8)
    for i in range(3):put(arena,RECHANNEL_WEIGHTS-ARENA+i*2,(32767,-20000,12345)[i],2)
    for i in range(15):put(arena,HEAD_WEIGHTS-ARENA+i*2,rng.randrange(-32768,32768),2)
    for i in range((128+64)*3):put(arena,HEAD_RING-ARENA+i*4,0)
    for i in range(256):put(arena,INPUT-ARENA+i*4,rng.randrange(-2**31,2**31))
    for i in range(64):put(arena,DRY-ARENA+i*4,rng.randrange(-2**31,2**31))
    for i in range(192):put(arena,SUM-ARENA+i*4,rng.randrange(-2**31,2**31))
    return context,arena,scratch


class Memory:
    def __init__(self,memory):
        self.arrays=[(ctypes.c_uint8*len(data)).from_buffer_copy(data) for data in memory]
    def snapshot(self):return tuple(bytes(a) for a in self.arrays)
    def mapping(self,address,size):
        for base,array in zip((CONTEXT,ARENA,SCRATCH),self.arrays):
            offset=address-base
            if 0<=offset and offset+size<=len(array):return ctypes.addressof(array)+offset
        return None


def configure(library):
    result={}
    for name,arity in ARITIES.items():
        fn=getattr(library,"hyperrig_capture_processing_"+name)
        fn.argtypes=([POINTER] if name!="zero" else [])+[U32]*arity+[ctypes.POINTER(IO)]
        fn.restype=ctypes.c_int;result[name]=fn
    fn=library.hyperrig_capture_processing_kernel
    fn.argtypes=[U32,U32,ctypes.POINTER(IO)];fn.restype=ctypes.c_int;result["kernel"]=fn
    return result


def c_run(functions,memory,operation,*arguments,blocked=None,scripted=False):
    state=Memory(memory);calls=[];errors=[]
    def mapping(_opaque,address,size,writable):
        return None if blocked and blocked(address,size,writable) else state.mapping(address,size)
    def kernel(_opaque,target,parameters):
        try:
            calls.append((target,parameters,state.snapshot()))
            return 0 if scripted else functions["kernel"](target,parameters,ctypes.byref(io))
        except Exception as error:errors.append(error);return -202
    io=IO(MAP(mapping),KERNEL(kernel),None)
    args=([state.arrays[0]] if operation!="zero" else [])+list(arguments)+[ctypes.byref(io)]
    result=functions[operation](*args)
    if errors:raise errors[0]
    return {"result":result,"memory":state.snapshot(),"calls":calls}


def verify(library_path,output,mini_image=None,smoke=False):
    if not __debug__:raise RuntimeError("verification requires assertions")
    program=CaptureProcessingProgram();functions=configure(ctypes.CDLL(str(library_path.resolve())))
    counts=dict.fromkeys(ARITIES,0);coverage=set();numeric_calls=0;scripted_cases=0;native_steps=0
    result_digest=hashlib.sha256()
    def compare(memory,operation,*arguments,scripted=False):
        nonlocal numeric_calls,scripted_cases,native_steps
        native=program.execute(memory,operation,*arguments,kernel=(lambda *_:None) if scripted else None)
        actual=c_run(functions,memory,operation,*arguments,scripted=scripted)
        assert actual["result"]==0,(operation,arguments,actual["result"])
        for key in ("memory","calls"):
            if actual[key]!=native[key]:
                if key=="memory":
                    detail=[(i,[(j,a,b) for j,(a,b) in enumerate(zip(x,y)) if a!=b][:12])
                        for i,(x,y) in enumerate(zip(actual[key],native[key])) if x!=y]
                else:
                    detail=(len(actual[key]),len(native[key]),next((i for i,(x,y) in enumerate(zip(actual[key],native[key])) if x!=y),None))
                raise AssertionError((operation,arguments,key,detail))
        counts[operation]+=1;coverage.update(native["visited"])
        numeric_calls+=0 if scripted else len(native["calls"]);scripted_cases+=int(scripted)
        native_steps+=native["steps"]
        result_digest.update(json.dumps((operation,arguments,scripted)).encode())
        for data in native["memory"]:result_digest.update(data)
        for target,parameters,snapshot in native["calls"]:
            result_digest.update(target.to_bytes(4,"little")+parameters.to_bytes(4,"little"))
            for data in snapshot:result_digest.update(data)
        return native
    compare(baseline(),"zero",SUM,192)
    compare(baseline(),"rechannel",INPUT,DRY,0)
    compare(baseline(),"layer",0,DRY,0,64,SUM,ARENA+0x3000,74,0)
    compare(baseline(),"head",SUM,0,OUTPUT)
    compare(baseline(layers=1),"iterate",0,1,DRY,0,SUM,0)
    compare(baseline(layers=2),"process",INPUT,OUTPUT,64)
    if not smoke:
        for kind,taps,residual in ((0,1,0),(0,3,-3),(0,15,5),(1,6,0),(2,6,1),(2,6,-31),(3,15,0),(4,15,31),(4,15,-2),(255,6,0)):
            for position in (0,1,63,64,0xFFFFFFF0):
                memory=baseline(taps=taps,kind=kind,residual=residual,position=position,seed=position+kind+9)
                compare(memory,"layer",0,DRY,position,64,SUM,0x01C33F10,1,position&1)
                if position in (0,63):compare(memory,"process",INPUT,OUTPUT,128)
        for count in (0,1,63,64,65,127,128,129,192):
            compare(baseline(layers=1,position=0xFFFFFFE0),"process",INPUT,OUTPUT,count)
            for bad in (0,1,2,3):
                memory=baseline()
                if bad==0:put(memory[0],8,0,2)
                elif bad==1:put(memory[0],92,0)
                else:put(memory[1],76 if bad==2 else 68,0)
                compare(memory,"process",INPUT,OUTPUT,count)
        for first,end in ((0,0),(1,1),(2,3),(3,4),(0,1),(1,2),(0,10)):
            for selector in (0,1,2,0xFFFFFFFF):compare(baseline(),"iterate",first,end,DRY,73,SUM,selector)
        for frames in (4,8,16,32,63,64):
            for residual in (-31,0,31):
                memory=baseline(taps=3,residual=residual,seed=frames+residual)
                compare(memory,"layer",1,DRY,71,frames,SUM,ARENA+0x5000,97,1)
        for position in (1,63,64,127,128,0xFFFFFFFF):
            compare(baseline(),"rechannel",INPUT,DRY,position)
            compare(baseline(),"head",SUM,position,OUTPUT)
        for words in (4,5,7,8,12,191,192,193,512,1020,1023):compare(baseline(),"zero",SUM,words)
        for shift in (1,2,30,31):
            memory=baseline();memory[0][56]=shift
            for i in range(64):put(memory[1],INPUT-ARENA+i*4,(0x7FFFFFFF,0x80000000,0xFFFFFFFF,0)[i%4])
            compare(memory,"rechannel",INPUT,DRY,73)
        for taps in (1,5,65):
            for shift in (1,31):
                for bias in (0,2**63-1,-2**63):
                    memory=baseline();memory[0][3]=taps;memory[0][57]=shift;put(memory[0],72,bias,8)
                    for i in range(taps*3):put(memory[1],HEAD_WEIGHTS-ARENA+i*2,32767 if i%2 else -32768,2)
                    compare(memory,"head",SUM,127,OUTPUT)
        for kind,taps in ((1,6),(3,15)):
            for sign in (-1,1):
                memory=baseline(taps=taps,kind=kind,shift=1)
                memory[1][8]=1
                for i in range(3):put(memory[1],0xC300+i*8,sign*(2**60),8)
                compare(memory,"layer",0,DRY,61,64,SUM,0x01C33F10,1,0)
        for frames in (2,3,5):compare(baseline(taps=3),"layer",0,DRY,0,frames,SUM,ARENA+0x5000,64,0)
        for count in (1,5,64,129):
            compare(baseline(layers=0),"process",INPUT,INPUT+4,count)
        # Scripted calls isolate all dispatch selectors and preserve their exact
        # parameter-block construction; they are counted separately from DSP.
        for kind in (0,1,2,3,4,5,255):
            compare(baseline(kind=kind),"layer",1,DRY,67,64,SUM,ARENA+0x5000,97,1,scripted=True)
    guards={"invalid_api":0,"mapping":0,"numerical_domain":0}
    if not smoke:
        state=Memory(baseline())
        callback=MAP(lambda _o,address,size,_w:state.mapping(address,size))
        io=IO(callback,KERNEL(),None);bad_io=IO(MAP(),KERNEL(),None)
        examples={"rechannel":(INPUT,DRY,0),"layer":(0,DRY,0,64,SUM,ARENA+0x5000,64,0),
            "iterate":(0,2,DRY,0,SUM,0),"head":(SUM,0,OUTPUT),"process":(INPUT,OUTPUT,64),"zero":(SUM,192)}
        for name,args in examples.items():
            prefix=[] if name=="zero" else [state.arrays[0]]
            for bad in (None,ctypes.byref(bad_io)):
                assert functions[name](*prefix,*args,bad)==-200
                guards["invalid_api"]+=1
            if name!="zero":
                assert functions[name](None,*args,ctypes.byref(io))==-200
                guards["invalid_api"]+=1
        for bad in (None,ctypes.byref(bad_io)):
            assert functions["kernel"](0x01C1453C,0x01C33D00,bad)==-200;guards["invalid_api"]+=1
        for address in (LAYERS+76,LAYERS+68,INPUT,0x01C33F78,ARENA+0x1000,RECHANNEL_WEIGHTS,
            ARENA+0xC000,ARENA+0xC340,ARENA+0xC300,0x01C33A00,HEAD_WEIGHTS,HEAD_RING,OUTPUT):
            memory=baseline()
            actual=c_run(functions,memory,"process",INPUT,OUTPUT,64,
                blocked=lambda start,size,_w,target=address:start<=target<start+size)
            assert actual["result"]==-201,(hex(address),actual["result"])
            assert actual["memory"][1][INPUT-ARENA:INPUT-ARENA+256]==memory[1][INPUT-ARENA:INPUT-ARENA+256]
            guards["mapping"]+=1
        for shift in (0,32,255):
            for name,offset,args in (("rechannel",56,(INPUT,DRY,0)),("head",57,(SUM,0,OUTPUT))):
                memory=baseline();memory[0][offset]=shift
                assert c_run(functions,memory,name,*args)["result"]==-202;guards["numerical_domain"]+=1
        for kind,taps,residual in ((3,6,0),(1,15,0),(2,6,0),(1,6,3),(4,15,0),(3,15,-1)):
            memory=baseline(taps=taps,kind=kind,residual=residual)
            assert c_run(functions,memory,"layer",1,DRY,0,64,SUM,ARENA+0x5000,64,0)["result"]==-202
            guards["numerical_domain"]+=1
        for words in (0,1,2,3,1024,0xFFFFFFFF):
            actual=c_run(functions,baseline(),"zero",SUM,words)
            assert actual["result"]==-202;guards["numerical_domain"]+=1
        for frames in (0,65):
            assert c_run(functions,baseline(),"layer",1,DRY,0,frames,SUM,ARENA+0x5000,64,0)["result"]==-202
            guards["numerical_domain"]+=1
        # The older portable head and new layer adapter share a deliberately
        # bounded signed-index domain. These coherent synthetic blocks exceed
        # that bound and must fail before any output or scratch-cursor write.
        for operation,args,field in (("head",(SUM,0,OUTPUT),12),
            ("layer",(1,DRY,0,64,SUM,ARENA+0x5000,64,0),156)):
            prepared=c_run(functions,baseline(),operation,*args,scripted=True)
            target,parameters,_=prepared["calls"][0]
            memory=tuple(bytearray(x) for x in prepared["memory"])
            put(memory[2],parameters-SCRATCH+field,0x80000004)
            state=Memory(memory)
            callback=MAP(lambda _o,address,size,_w:state.mapping(address,size))
            bounded_io=IO(callback,KERNEL(),None)
            assert functions["kernel"](target,parameters,ctypes.byref(bounded_io))==-202
            assert state.snapshot()==tuple(map(bytes,memory))
            guards["numerical_domain"]+=1
        assert functions["kernel"](0,0,ctypes.byref(io))==-202;guards["numerical_domain"]+=1
    missing=sorted(set(program.code)-coverage)
    if not smoke:assert missing==[0x01C12F1E],missing
    report={"schema":1,"project":"HyperRig","result":"pass",
        "component":"reconstructed-capture-processing","flashable":False,"hardware_test":False,
        "audio_test":False,"firmware_changed":False,
        "comparisons":sum(counts.values()),"total_comparisons":sum(counts.values()),
        "cases_by_entry":counts,"actual_numerical_calls":numeric_calls,"native_steps":native_steps,
        "result_digest":result_digest.hexdigest(),
        "scripted_numerical_cases":scripted_cases,"c_only_guards":guards,
        "instruction_coverage":{"all_visited":len(coverage),"all_decoded":len(program.code),
            "new_visited":len(coverage&program.new_code),"new_decoded":len(program.new_code),
            "unvisited_new":sorted(program.new_code-coverage),"unvisited_all":missing,
            "missing_classification":{"0x01c12f1e":"Redundant process loop fall-through: the final index branches to head at 0x01c12ee8 before this jump; count is preserved by callee ABI."}},
        "functions":{name:{"start":lo,"end_exclusive":hi,"bytes_sha256":hashlib.sha256(program.raw_regions[name]).hexdigest(),
            "instructions":sum(lo<=pc<hi for pc in program.code)} for name,(lo,hi) in REGIONS.items()},
        "table":{"start":f"0x{TABLE_START:08x}","end":f"0x{TABLE_END:08x}","hex":program.table.hex()},
        "reused_kernel_regions":{name:{"start":lo,"end_exclusive":hi,"bytes_sha256":hashlib.sha256(program.kernel_regions[name]).hexdigest()}
            for name,(lo,hi) in KERNELS.items()}}
    sources=["firmware/include/hyperrig/hyperrig_capture_processing.h","firmware/src/hyperrig_capture_processing.c",
        "tools/capture_processing_machine.py","tools/verify_capture_processing.py","tools/build_capture_processing.py",
        "tests/test_capture_processing_machine.py","tests/capture_processing_sanitize.c",
        "tools/dot_machine.py","tools/control_machine.py","tools/control_action_machine.py"]
    sources += [f"firmware/{directory}/hyperrig_{name}.{suffix}" for directory,suffix in (("src","c"),) for name in ("dot","head","rechannel","a2l","layer")]
    sources += [f"firmware/include/hyperrig/hyperrig_{name}.h" for name in ("dot","head","rechannel","a2l","layer")]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py","upstream/pi32v2-isa/pi32v2isa/table.py",
        "upstream/pi32v2-isa/isa/pi32v2.toml","research/input-manifest.json","hyperrig/jieli.py"]
    report["source_sha256"]={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    original=ROOT/"artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
    report["original_image_sha256"]=hashlib.sha256(original.read_bytes()).hexdigest()
    report["decoded_sha256"]=hashlib.sha256((ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()).hexdigest()
    report["library_sha256"]=hashlib.sha256(library_path.read_bytes()).hexdigest()
    if mini_image:
        from hyperrig.jieli import unpack_app
        mini_sha256=hashlib.sha256(mini_image.read_bytes()).hexdigest()
        assert mini_sha256=="d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2","unreviewed MINI image"
        decoded=unpack_app(mini_image.read_bytes())[2]["app.bin"]
        for name,(lo,hi) in (REGIONS|KERNELS).items():
            expected=(program.raw_regions|program.kernel_regions)[name]
            assert decoded[image_offset(lo):image_offset(hi)]==expected,name
        report["mini_v4_binding"]={"image":mini_image.relative_to(ROOT).as_posix(),"image_sha256":mini_sha256,
            "identical_regions":list(REGIONS|KERNELS)}
    if output:output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("comparisons","actual_numerical_calls","scripted_numerical_cases")}|
        {"instruction_coverage":{k:v for k,v in report["instruction_coverage"].items() if not k.startswith("unvisited")}}))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--library",type=Path,required=True)
    p.add_argument("--output",type=Path);p.add_argument("--mini-image",type=Path);p.add_argument("--smoke",action="store_true")
    args=p.parse_args();verify(args.library,args.output,args.mini_image.resolve() if args.mini_image else None,args.smoke)
