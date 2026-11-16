"""Compare complete audio-task prefixes and helpers with pinned instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import sys
from pathlib import Path

from audio_task_machine import (AudioTaskProgram,MAPPED,REGIONS,STATIC,STATE,CONTROL,
    RAM,RECORD,PLAY,ARENA,ROOT,TASK,STACK,image_offset)
from verify_capture_warmup import SOURCES as WARM_SOURCES
from build_dsp_dynamics_processing import SOURCES as DYNAMICS_SOURCES
from verify_dsp_dynamics_processing import SOURCES as DYNAMICS_SOURCE_FILES

SOURCES=tuple(dict.fromkeys((*WARM_SOURCES,*(Path(p).stem.removeprefix("hyperrig_") for p in DYNAMICS_SOURCES),
    "biquad_chain","audio_task")))
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32)
class IO(ctypes.Structure):_fields_=[("map",MAP),("call",CALL),("opaque",ctypes.c_void_p)]
class Task(ctypes.Structure):_fields_=[(name,U32) for name in ("phase","waits","frames","fatal_site")]


def put(data,offset,value,size=4):data[offset:offset+size]=(value&((1<<(8*size))-1)).to_bytes(size,"little")
def word(data,offset):return int.from_bytes(data[offset:offset+4],"little")


def baseline(seed=1,mode=2):
    memory=[bytearray(n) for _,n in MAPPED];r=memory[0];s=STATE-RAM;p=CONTROL-RAM
    for offset,value in ((280,mode),(380,1),(272,1<<24),(596,0),(620,0),(624,1)):
        put(r,s+offset,value)
    for offset,value in ((24,10),(28,65536),(32,65536),(36,65536),(44,3),(68,10),(72,65536),
        (76,65536),(80,65536),(148,1024),(152,1<<24),(196,0),(200,256)):
        put(r,p+offset,value)
    put(r,0x01C340CC-RAM+20,26);put(r,0x01C340CC-RAM+24,26)
    put(r,0x01C1F7D4-RAM,65536)
    generator=random.Random(seed)
    for base,count in ((0x01C234A8,512),(0x01C224A8,512),(0x01C22CA8,512),(0x01C23CA8,352),
        (0x01C33030,44),(0x01C33320,55),(0x01C341C4,128)):
        for i in range(count):put(r,base-RAM+4*i,generator.randrange(-1<<25,1<<25))
    # Disabled sections retain deliberately nonzero histories and coefficients.
    for base,count in ((0x01C33030,4),(0x01C33320,5)):
        for i in range(count):r[base-RAM+44*i+40:base-RAM+44*i+44]=b"\0\0\0\0"
    for i in range(256):put(memory[2],i*2,generator.randrange(-32768,32768),2)
    return memory


def capture_fixture(layers=2,taps=6,residual=0):
    from verify_capture_warmup import baseline as warm_baseline
    from capture_processing_machine import ARENA as OLD_ARENA,SCRATCH
    context,arena,scratch,*_=warm_baseline(layers=layers,taps=taps,residual=residual)
    for offset in (60,68,80,92):put(context,offset,word(context,offset)+ARENA-OLD_ARENA)
    put(context,84,3)
    for layer in range(layers):
        for offset in (32,36,44,68):put(arena,layer*80+offset,word(arena,layer*80+offset)+ARENA-OLD_ARENA)
    memory=baseline();memory[3][:]=arena
    memory[0][0x01C2C03C-RAM:0x01C2C03C-RAM+228]=context
    length=min(len(scratch),len(memory[0])-(SCRATCH-RAM))
    memory[0][SCRATCH-RAM:SCRATCH-RAM+length]=scratch[:length]
    # Keep unrelated task routing/clock controls coherent after the broad
    # numerical scratch fixture is copied into its original shared addresses.
    for address in (0x01C34198,0x01C34444,0x01C34470,0x01C34488,0x01C3448C):put(memory[0],address-RAM,0)
    put(memory[0],0x01C1F7C8-RAM,1)
    return memory


class Script:
    """Explicit external-service fixture; recovered DSP never enters this class."""
    def __init__(self,clock=10000,step=137,ready=0,mutations=()):
        self.clock,self.step,self.ready=clock,step,ready
        self.mutations=list(mutations);self.counts={}
    def __call__(self,target,args,memory):
        self.counts[target]=self.counts.get(target,0)+1
        result=0
        if target==0x01C04862:result=self.clock;self.clock=(self.clock+self.step)&0xFFFFFFFF
        elif target==0x01C048A4:result=self.ready
        elif target==0x01C01DE4:
            # Synthetic output service owns its entire boundary. This is not
            # claimed as recovered output gain arithmetic or physical audio.
            for i in range(128):memory.write(args[0]+4*i,memory.read(args[1]+4*i,4),4)
            result=20000
        elif target==0x01C04CDA:
            for i in range(128):memory.write(args[1]+4*i,memory.read(args[0]+4*i,4)^0x12345,4)
        elif target==0x01C0198A:result=123456
        elif target==0x01C019D8:result=3
        for expected,nth,address,value,size in self.mutations:
            if target==expected and self.counts[target]==nth:memory.write(address,value,size)
        return result


class Memory:
    def __init__(self,program,memory):
        self.arrays=[(ctypes.c_uint8*len(data)).from_buffer_copy(data) for data in memory]
        self.static=[(ctypes.c_uint8*len(program.task_data[name])).from_buffer_copy(program.task_data[name]) for name in STATIC]
        self.mapped=[*zip(MAPPED,self.arrays),*zip(((start,end-start) for start,end in STATIC.values()),self.static)]
    def mapping(self,address,size):
        for (base,n),array in self.mapped:
            if base<=address<=address+size<=base+n:return ctypes.addressof(array)+address-base
        return None
    def read(self,address,size):
        p=self.mapping(address,size)
        if p is None:raise ValueError(f"unmapped fixture read {address:#x}")
        return int.from_bytes(ctypes.string_at(p,size),"little")
    def write(self,address,value,size):
        p=self.mapping(address,size)
        if p is None:raise ValueError(f"unmapped fixture write {address:#x}")
        ctypes.memmove(p,(value&((1<<(8*size))-1)).to_bytes(size,"little"),size)
    def snapshot(self):return tuple(bytes(a) for a in self.arrays)
    def digest(self):return hashlib.sha256(b"".join(self.snapshot())).hexdigest()


def configure(lib):
    lib.hyperrig_audio_task_resume.argtypes=[ctypes.POINTER(Task),U32,U32,ctypes.POINTER(IO)]
    lib.hyperrig_audio_task_resume.restype=ctypes.c_int
    for name,count in (("tap",2),("warmup",0),("effect_scan",1),("set_input",1)):
        fn=getattr(lib,"hyperrig_audio_task_"+name);fn.argtypes=[U32]*count+[ctypes.POINTER(IO)];fn.restype=ctypes.c_int
    lib.hyperrig_audio_task_fir.argtypes=[U32]*5+[ctypes.POINTER(U32),ctypes.POINTER(IO)]
    lib.hyperrig_audio_task_fir.restype=ctypes.c_int
    lib.hyperrig_audio_task_recovered.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
    lib.hyperrig_audio_task_recovered.restype=ctypes.c_int
    return lib


def c_machine(lib,program,memory,script=None):
    state=Memory(program,memory);calls=[];errors=[];task=Task();script=script or Script()
    state.calls=calls
    def mapping(_opaque,address,size,writable):return state.mapping(address,size)
    def call(_opaque,target,args,count):
        try:
            arguments=tuple(args[i] for i in range(count));calls.append((target,arguments,state.digest()))
            return script(target,arguments,state)
        except Exception as error:errors.append(error);return 0
    io=IO(MAP(mapping),CALL(call),None)
    def resume(wait_budget=1,frame_budget=1):
        result=lib.hyperrig_audio_task_resume(ctypes.byref(task),wait_budget,frame_budget,ctypes.byref(io))
        if errors:raise errors[0]
        return {"reason":result,"task":tuple(getattr(task,k) for k,_ in Task._fields_),"memory":state.snapshot(),"calls":list(calls)}
    return resume,state,task,io


def invalid_checks(lib,program):
    state=Memory(program,baseline());task=Task();result=U32(123);args=(U32*5)(0x01C234A8,128,0,0,0);count=0
    callback=CALL(lambda *_:0);mapping=MAP(lambda _o,p,n,_w:state.mapping(p,n));io=IO(mapping,callback,None)
    before=state.snapshot()
    for args0 in ((None,1,1,ctypes.byref(io)),(ctypes.byref(task),0,1,ctypes.byref(io)),
        (ctypes.byref(task),1,0,ctypes.byref(io)),(ctypes.byref(task),1,1,None),
        (ctypes.byref(task),1,1,ctypes.byref(IO(MAP(),callback,None))),
        (ctypes.byref(task),1,1,ctypes.byref(IO(mapping,CALL(),None)))):
        assert lib.hyperrig_audio_task_resume(*args0)==-200;count+=1
    task.phase=4;assert lib.hyperrig_audio_task_resume(ctypes.byref(task),1,1,ctypes.byref(io))==-200;count+=1
    for name,arguments in (("tap",(1,0x01C234A8)),("warmup",()),("effect_scan",(0x01C234A8,)),("set_input",(1,))):
        assert getattr(lib,"hyperrig_audio_task_"+name)(*arguments,None)==-200;count+=1
    for taps,mask,ring in ((0,15,STATE+3312),(9,31,STATE+3312),(19,15,STATE+3312),(9,15,STATE+3313)):
        assert lib.hyperrig_audio_task_fir(0x020364D6,taps,ring,0,mask,ctypes.byref(result),ctypes.byref(io))==-202;count+=1
    assert lib.hyperrig_audio_task_fir(0x020364D6,9,STATE+3312,0,15,None,ctypes.byref(io))==-200;count+=1
    for target,arguments,destination in ((0,args,ctypes.byref(result)),(0x01C051F0,None,ctypes.byref(result)),(0x01C051F0,args,None)):
        assert lib.hyperrig_audio_task_recovered(target,arguments,destination,ctypes.byref(io))==-200;count+=1
    args[1]=129
    for target in (0x01C051F0,0x01C054A6):
        assert lib.hyperrig_audio_task_recovered(target,args,ctypes.byref(result),ctypes.byref(io))==-202;count+=1
    assert state.snapshot()==before
    missing=IO(MAP(lambda *_:None),callback,None);task=Task()
    assert lib.hyperrig_audio_task_resume(ctypes.byref(task),1,1,ctypes.byref(missing))==-201;count+=1
    assert lib.hyperrig_audio_task_fir(0x020364D6,9,STATE+3312,0,15,ctypes.byref(result),ctypes.byref(missing))==-201;count+=1
    assert lib.hyperrig_audio_task_warmup(ctypes.byref(missing))==-201;count+=1
    unaligned=0
    for target,blocked in ((0x01C054A6,0x01C33030),(0x01C051F0,0x01C33320),(0x01C051F0,0x01C234A8)):
        fresh=baseline();fresh[0][0x01C32DB0-RAM+28]=1;fresh[0][0x01C33320-RAM+40]=1
        state=Memory(program,fresh);padding=(ctypes.c_uint8*1024)()
        io=IO(MAP(lambda _o,p,n,_w:ctypes.addressof(padding)+1 if p==blocked else state.mapping(p,n)),callback,None)
        args[1]=128
        assert lib.hyperrig_audio_task_recovered(target,args,ctypes.byref(result),ctypes.byref(io))==-202
        unaligned+=1
    clock_guards=0
    for token in (1,0x01C01058,0xFFFFFFFF):
        fresh=baseline();fresh[0][0x01C33320-RAM+40]=1;put(fresh[0],0x01C34198-RAM,token)
        state=Memory(program,fresh);io=IO(MAP(lambda _o,p,n,_w:state.mapping(p,n)),callback,None)
        assert lib.hyperrig_audio_task_recovered(0x01C051F0,args,ctypes.byref(result),ctypes.byref(io))==-202
        clock_guards+=1
    fresh=baseline();fresh[0][0x01C33320-RAM+40]=1;put(fresh[0],0x01C34198-RAM,0x01C04862)
    state=Memory(program,fresh);called=[]
    def mutate_clock(_opaque,target,arguments,count):
        called.append(target);state.write(0x01C34198,0x01C01058,4);return 100
    io=IO(MAP(lambda _o,p,n,_w:state.mapping(p,n)),CALL(mutate_clock),None)
    assert lib.hyperrig_audio_task_recovered(0x01C051F0,args,ctypes.byref(result),ctypes.byref(io))==-202
    assert called==[0x01C04862];clock_guards+=1
    return {"invalid_api_or_mapping":count,"unaligned_typed_mapping":unaligned,"unreviewed_clock_token":clock_guards}


def verify(library,output=None,mini_image=None,smoke=False):
    if not __debug__:raise RuntimeError("verification requires Python assertions")
    original=ROOT/"artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
    original_sha=hashlib.sha256(original.read_bytes()).hexdigest()
    assert original_sha=="2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
    program=AudioTaskProgram();lib=configure(ctypes.CDLL(str(library.resolve())))
    counts={};coverage=set();steps=0;real_calls={};digest=hashlib.sha256()
    def compare_helper(name,memory,arguments=(),script=None):
        nonlocal steps
        expected=program.execute_helper(memory,name,arguments,Script(**(script or {})))
        run,state,task,io=c_machine(lib,program,memory,Script(**(script or {})))
        result=U32(0xA5A5A5A5)
        args=[*arguments,*([ctypes.byref(result)] if name=="fir" else []),ctypes.byref(io)]
        status=getattr(lib,"hyperrig_audio_task_"+name)(*args)
        actual={"memory":state.snapshot()}
        assert status==0,(name,status)
        if name=="fir":assert result.value==expected["value"],(name,result.value,expected["value"])
        assert actual["memory"]==expected["memory"],(name,[(hex(base+i),x,y) for (base,n),xv,yv in zip(MAPPED,actual["memory"],expected["memory"])
            for i,(x,y) in enumerate(zip(xv,yv)) if x!=y][:12])
        # The helper callback log is exposed by observing the already-completed
        # C state without invoking the task runner.
        assert state.calls==expected["calls"],name
        coverage.update(expected["visited"]);steps+=expected["steps"]
        for target,args in expected["real_calls"]:real_calls[target]=real_calls.get(target,0)+1
        counts["helper-"+name]=counts.get("helper-"+name,0)+1
        digest.update(json.dumps((name,arguments,expected["calls"])).encode())
        for data in actual["memory"]:digest.update(data)
    def compare(name,memory,segments=((1,1),(1,1)),script=None):
        nonlocal steps
        make=lambda:Script(**(script or {}))
        native=program.machine(memory,make());c,state,task,io=c_machine(lib,program,memory,make())
        previous_steps=0;previous_calls=0
        for segment in segments:
            expected=native.resume(*segment);actual=c(*segment)
            for key in ("reason","task","memory","calls"):
                if expected[key]!=actual[key]:
                    if key=="memory":detail=[(hex(base+i),x,y) for (base,n),a,b in zip(MAPPED,actual[key],expected[key])
                        for i,(x,y) in enumerate(zip(a,b)) if x!=y][:16]
                    elif key=="calls":detail=(len(actual[key]),len(expected[key]),next(((i,x,y) for i,(x,y) in enumerate(zip(actual[key],expected[key])) if x!=y),None))
                    else:detail=(actual[key],expected[key])
                    raise AssertionError((name,segment,key,detail))
            coverage.update(expected["visited"]);steps+=expected["steps"]-previous_steps;previous_steps=expected["steps"]
            for target,args in expected["real_calls"][previous_calls:]:real_calls[target]=real_calls.get(target,0)+1
            previous_calls=len(expected["real_calls"])
            counts[name]=counts.get(name,0)+1;digest.update(json.dumps((name,segment,actual["task"],actual["calls"])).encode())
            for data in actual["memory"]:digest.update(data)
        if sum(counts.values())%20<3:print("Compared audio-task corpus through",name,flush=True)
        return expected
    compare("bypass",baseline(mode=0));compare("dry",baseline())
    if not smoke:
        for mode in (1,3,0xFFFFFFFF):compare(f"mode-{mode}",baseline(mode=mode))
        def altered(*changes,mode=2,seed=1):
            memory=baseline(seed,mode)
            for address,value,size in changes:put(memory[0],address-RAM,value,size)
            return memory
        for tick in (0,199,201,202,401,402,0xFFFFFFFF):
            compare(f"watchdog-{tick}",altered((STATE+204,1,4),(CONTROL+24,tick,4),(STATE+380,0,4)))
        compare("poll-fatal",altered((STATE+380,2,4),mode=0),((1,1),(1,1),(1,1)),
            {"mutations":((0x01C04862,3,STATE+204,1,4),(0x01C04862,3,CONTROL+24,500,4))})
        for index,backlog in ((0,0),(1,3),(2,4),(3,0xFFFFFFFF),(0xFFFFFFFF,4)):
            compare(f"queue-{index}-{backlog}",altered((STATE+384,index,4),(STATE+380,(index+2)&0xFFFFFFFF,4),
                (STATE+540,index,4),(STATE+536,(index-backlog)&0xFFFFFFFF,4)),((1,1),(1,2),(1,1)))
        for mode in (1,2,255):
            for count,gain in ((1,0),(2,1),(7,2),(256,128),(7,0xFFFFFFFF)):
                compare(f"diagnostic-{mode}-{count}-{gain}",altered((STATE+18,mode,1),(STATE+312,PLAY,4),
                    (STATE+316,count,4),(STATE+320,count-1,4),(STATE+324,gain,4)))
        for index in (0,1,0xFFFFFFFE,0xFFFFFFFF):
            compare(f"recording-{index}",altered((STATE+52,1,1),(STATE+976,RECORD,4),
                *((STATE+offset,index,4) for offset in (980,988,992,996,1000,1004))))
        for mute in (0,1):
            for gain in (0,1,127,128,896,1024,2048,0xFFFFFFFF):
                compare(f"fade-{mute}-{gain}",altered((STATE+52,1,1),(CONTROL+16,mute,1),(CONTROL+148,gain,4)))
        for current,prior in ((0,1),(1,0),(1,1),(255,255)):
            for stereo in (0,1):compare(f"manual-{current}-{prior}-{stereo}",altered((STATE+34,current,1),(STATE+35,prior,1),
                (0x01C3448D,stereo,1)))
        for source in (1,255):compare(f"source-{source}",altered((STATE+20,source,1)))
        for gain,prior in ((0,0),(12345,54321),(0xFFFFFFFF,0x80000000),(0x80000000,0x7FFFFFFF)):
            compare(f"input-gain-{gain}-{prior}",altered((CONTROL+28,gain,4),(CONTROL+76,prior,4),(CONTROL+36,gain,4),
                (CONTROL+72,prior,4),(CONTROL+32,prior,4)))
        for enabled,old,cleanup,pending in ((0,0,0,0),(0,1,0,0),(1,1,0,0),(1,0,0,0),(1,0,1,0),(1,1,0,1)):
            compare(f"capture-{enabled}-{old}-{cleanup}-{pending}",altered((CONTROL+2,enabled,1),(CONTROL+3,1,1),
                (STATE+28,old,1),(STATE+416,cleanup,4),(STATE+328,pending,4)))
        for stereo,old,prior in ((0,0,0),(1,0,0),(1,1,0),(1,1,1),(0,1,1)):
            compare(f"dynamics-{stereo}-{old}-{prior}",altered((0x01C3448C,1,1),(0x01C3448D,stereo,1),
                (STATE+27,old,1),(STATE+33,prior,1)))
        for seed in range(12):
            memory=altered((CONTROL+2,1,1),(CONTROL+3,1,1),(STATE+28,1,1),(0x01C32DB0+28,1,1),
                (0x01C32DB0+1,seed&1,1),(0x01C3448D,1,1),(0x01C3448C,seed%3==0,1),seed=seed)
            r=memory[0]
            for base,n in ((0x01C33030,4),(0x01C33320,5),(0x01C33240,5)):
                for j in range(n):
                    for k,value in enumerate((1<<28,(seed+1)*65536,0,0,-32768)):put(r,base-RAM+44*j+4*k,value)
                    r[base-RAM+44*j+40]=(j+seed)%2;r[base-RAM+44*j+41]=j&1
            for j in range(5):r[0x01C32E54-RAM+j]=(seed+j)%3==0
            put(r,0x01C34198-RAM,0x01C04862 if seed&1 else 0)
            for base in (0x01C330E0,0x01C33190):
                for j in range(20):put(r,base-RAM+4*j,(1<<28) if j%5==0 else -4096)
                for j in range(20):put(r,base-RAM+80+4*j,1024)
                put(r,base-RAM+160,65536);put(r,base-RAM+164,0xFFFFFFFF)
                r[base-RAM+168:base-RAM+172]=bytes((1,1,1,1));put(r,base-RAM+172,seed%6)
            put(r,0x01C32DB0-RAM+32,seed%6)
            compare(f"real-filter-chain-{seed}",memory,((1,1),(1,1),(1,1)),
                {"mutations":((0x01C04862,6,0x01C34488,1,1),)} if seed==11 else None)
        for stage,count,limit,destination in ((0,0,128,RECORD),(1,0,0,RECORD),(1,8,7,RECORD),
            (1,0,129,0),(1,0,1,RECORD),(1,3,130,RECORD),(1,4,200,RECORD),(1,0,128,0x01C234AC)):
            memory=altered((STATE+25,1,1),(STATE+456,destination,4),(STATE+460,count,4),(STATE+464,limit,4))
            compare_helper("tap",memory,(stage,0x01C234A8))
        for slot in (0,7,15):
            for field in (1,8,9,10):
                memory=baseline();address=0x01C2C220-RAM+480*slot
                memory[0][address]=28;memory[0][address+2]=1;memory[0][address+field]=255
                compare_helper("effect_scan",memory,(0x01C234A8,))
        compare_helper("effect_scan",baseline(),(0x01C234A8,))
        for value in (0,1,0x80000000,0xFFFFFFFF):compare_helper("set_input",baseline(),(value,))
        for taps,mask,offset in ((9,15,0),(19,31,2638)):
            for position in (0,1,15,31,0xFFFFFFFF):
                memory=baseline();ring=STATE+3312
                for i in range(mask+1):put(memory[0],ring-RAM+4*i,(0x7FFFFFFF,0x80000000,0xFFFFFFFF,0)[i%4])
                compare_helper("fir",memory,(0x020364D6+offset,taps,ring,position,mask))
        for layers,taps,residual in ((1,1,0),(2,6,0),(3,15,1),(2,3,-31)):
            memory=capture_fixture(layers,taps,residual)
            compare_helper("warmup",memory)
            memory[0][CONTROL-RAM+2]=memory[0][CONTROL-RAM+3]=1
            memory[0][STATE-RAM+28]=memory[0][STATE-RAM+604]=1
            compare(f"real-warmup-{layers}-{taps}",memory)
        compare_helper("warmup",baseline())
        for flags in (0,1):
            for immediate in (0,1):
                compare(f"capture-gain-{flags}-{immediate}",altered((STATE+276,1,4),(STATE+272,0x7FFFFFFF,4),(STATE+16,immediate,1),
                    (STATE+17,flags,1),(STATE+288,1124,4),(CONTROL+4,flags,1),(0x01C3448A,flags,1)))
        for first in (0,1,8,15):
            memory=altered((STATE+22,first,1),(STATE+23,7,1),(STATE+400,8000,4),(STATE+396,5000,4))
            compare(f"overrun-{first}",memory,script={"clock":100000})
        for n in (0,1,7,8,0xFFFFFFFF):
            memory=altered((STATE+616,n,4),(STATE+612,63 if n<2 else 127,4),(STATE+620,511,4),
                (STATE+624,512,4),(STATE+628,2,4),(STATE+4088,7,4),(STATE+632,7,4))
            for j in range(8):put(memory[0],STATE-RAM+2388+4*j,(5000,1,4000,1000,6000,3000,2000,9000)[j])
            compare(f"statistics-{n}",memory)
        for ready in (0,1):
            compare(f"bypass-ready-{ready}",altered((STATE+328,1,4),mode=0),script={"ready":ready})
            compare(f"capture-ready-{ready}",altered((STATE+328,1,4)),script={"ready":ready})
        for mode,pending,cleanup,flag in ((2,0,0,0),(2,0,0,1),(2,0,1,0),(2,1,0,0),(1,0,0,0)):
            compare(f"fully-muted-{mode}-{pending}-{cleanup}-{flag}",altered((STATE+52,1,1),(CONTROL+16,1,1),
                (STATE+32,1,1),(CONTROL+3,1,1),(STATE+328,pending,4),(STATE+416,cleanup,4),(STATE+600,flag,1),mode=mode))
        compare("nonpositive-delay",altered((STATE+1764,10001,4),(CONTROL+52,5000,4)))
        for flag in (0,1):
            compare(f"muted-transition-{flag}",altered((STATE+32,1,1),(CONTROL+3,1,1),(STATE+600,flag,1),(STATE+15,1,1)))
        compare("capture-gain-and-shifts",altered((CONTROL+2,1,1),(CONTROL+3,1,1),(STATE+28,1,1),
            (STATE+1500,1,4),(0x01C340CC+20,20,4),(0x01C340CC+24,25,4)))
        for mode,cooldown in ((1,0),(0,1),(0,2)):
            compare(f"timing-mode-{mode}-{cooldown}",altered((CONTROL+5,mode,1),(CONTROL+7,cooldown,1)))
        compare("capture-statistics",altered((CONTROL+2,1,1),(CONTROL+3,1,1),(STATE+28,1,1),
            (CONTROL+5,1,1),(CONTROL+6,1,1),(STATE+612,63,4)))
        compare("dynamics-low-scale",altered((0x01C3448C,1,1),(CONTROL+32,0,4),(CONTROL+80,0,4)))
        for mute in (0,1):
            for gain in (0,128):compare(f"stereo-fade-{mute}-{gain}",altered((0x01C3448D,1,1),
                (STATE+52,1,1),(CONTROL+16,mute,1),(CONTROL+148,gain,4)))
        memory=capture_fixture(layers=1,taps=1);put(memory[0],0x01C2BFF0-RAM+144,0)
        compare_helper("warmup",memory)
    new={pc for pc in program.code if any(lo<=pc<hi for lo,hi in REGIONS.values())}
    missing=sorted(new-coverage)
    if not smoke:assert not missing,[hex(pc) for pc in missing]
    guards=invalid_checks(lib,program)
    paths=set(DYNAMICS_SOURCE_FILES)
    paths.update(f"firmware/{part}/hyperrig_{name}.{extension}" for name in SOURCES
        for part,extension in (("src","c"),("include/hyperrig","h")))
    paths.update(("tools/audio_task_machine.py","tools/verify_audio_task.py","tools/build_audio_task.py",
        "tests/test_audio_task_machine.py","tests/audio_task_sanitize.c","tools/capture_warmup_machine.py",
        "tools/capture_processing_machine.py","tools/verify_capture_processing.py","tools/verify_capture_warmup.py",
        "tools/biquad_chain_machine.py","tools/build_dsp_dynamics_processing.py",
        "tools/control_action_machine.py","tools/control_machine.py","tools/dot_machine.py",
        "research/input-manifest.json","hyperrig/jieli.py","third_party/ultrarig/LICENSE.md"))
    # Bind every imported repository-owned Python module as well as the explicit
    # source list. This captures the inherited decoder/ISA semantics transitively.
    for module in list(sys.modules.values()):
        path=getattr(module,"__file__",None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(ROOT) and path.suffix==".py":paths.add(path.relative_to(ROOT).as_posix())
    app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
    static={name:{"start":lo,"end_exclusive":hi,"sha256":hashlib.sha256(program.task_data[name]).hexdigest()}
        for name,(lo,hi) in STATIC.items()}
    from dsp_audio_path_machine import TABLE,PRIOR_TABLE,RESET_CONFIGURATION
    extra_static={"capture_kernel_dispatch":(0x01C12BF2,0x01C12BF6),"initialization_gain_table":TABLE,
        "coefficient_selector_table":(PRIOR_TABLE,PRIOR_TABLE+10),"reset_configuration":RESET_CONFIGURATION,
        "task_registration":(0x02005250,0x0200525E)}
    bound_static={name:{"start":lo,"end_exclusive":hi,"sha256":hashlib.sha256(app[image_offset(lo):image_offset(hi)]).hexdigest()}
        for name,(lo,hi) in extra_static.items()}
    windows={f"0x{pc:08x}":{"start":pc,"end_exclusive":pc+record[1],
        "sha256":hashlib.sha256(app[image_offset(pc):image_offset(pc)+record[1]]).hexdigest()}
        for pc,record in sorted(program.code.items())}
    mini_binding=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert sha=="d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
        mini=unpack_app(raw)[2]["app.bin"]
        for record in (*windows.values(),*static.values(),*bound_static.values()):
            lo,hi=record["start"],record["end_exclusive"]
            assert mini[image_offset(lo):image_offset(hi)]==app[image_offset(lo):image_offset(hi)],hex(lo)
        mini_binding={"image_sha256":sha,"identical_decoded_instruction_windows":len(windows),
            "identical_static_windows":list(static)+list(bound_static)}
    from audio_task_machine import SERVICES
    from biquad_machine import BiquadProgram
    from capture_processing_machine import KERNELS
    numerical={lo for lo,hi in (BiquadProgram.REGIONS|KERNELS).values()}|{0x01C19D36,0x01C1A636}
    report={"schema":1,"project":"HyperRig","result":"pass","component":"reconstructed-audio-task",
        "scope":"Complete nonreturning task observed at waits, queue boundaries and fatal spins; five complete direct helpers",
        "original_image_sha256":original_sha,
        "decoded_image_sha256":hashlib.sha256(app).hexdigest(),
        "functions":{name:{"start":lo,"end_exclusive":hi,"bytes_sha256":hashlib.sha256(program.task_regions[name]).hexdigest(),
            "decoded":sum(lo<=pc<hi for pc in new),"visited":sum(lo<=pc<hi for pc in coverage)} for name,(lo,hi) in REGIONS.items()},
        "static_data":static,"bound_static_data":bound_static,"bound_instruction_windows":windows,
        "total_comparisons":sum(counts.values()),"comparisons":counts,"native_steps":steps,
        "real_callee_entries":{f"0x{target:08x}":count for target,count in sorted(real_calls.items())},
        "actual_numerical_kernel_entries":sum(count for target,count in real_calls.items() if target in numerical),
        "scripted_recovered_kernel_replacements":0,
        "scripted_sample_service_boundaries":[f"0x{target:08x}" for target in
            (0x01C012D8,0x01C0158A,0x01C01690,0x01C01722,0x01C0174E,0x01C0179E,
             0x01C01800,0x01C0198A,0x01C019D8,0x01C01DE4,0x01C04CDA,0x01C10E06,0x01C11D06,0x01C19EFA)],
        "external_services":{f"0x{target:08x}":{"argument_words":n} for target,n in SERVICES.items() if target not in program.code},
        "instruction_coverage":{"new_decoded":len(new),"new_visited":len(new&coverage),"unvisited_new":missing,
            "all_decoded":len(program.code),"all_visited":len(coverage),"unvisited_all":sorted(set(program.code)-coverage),
            "missing_classification":{},"inherited_gap_scope":"All inherited regions are bound; only paths required by these task/helper cases execute. Prior module branch coverage is not added to this corpus."},
        "c_only_guards":guards,"source_sha256":{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)},
        "library_sha256":hashlib.sha256(library.read_bytes()).hexdigest(),"mini_v4_binding":mini_binding,
        "outputs_state_and_ordered_service_snapshots_sha256":digest.hexdigest(),
        "compared":["all four mapped buffers, including untouched bytes and retained sample/filter state",
            "adapter observation state and reason against original wait/poll/fatal locations",
            "ordered external target/argument words and SHA-256 of all mapped bytes at each call",
            "actual recovered numerical computations with no scripted replacement for the available kernels"],
        "limitations":["resumable C API is new; the original task has no return instruction",
            "OS waits, clock, events, input/output services, asynchronous capture04cda and effect19efa remain explicit scripted boundaries",
            "synthetic external service outputs test orchestration; they are not reconstructed DSP or accelerator execution",
            "pure synchronous mapping/callback domain; no concurrency, interrupts, hardware timing or physical audio validation",
            "the five-section indirect clock token is restricted to0 or0x01c04862 at both reads; other callback targets are not inventoried or compared",
            "persistent busy warm-up timeout is exercised in ASan C and its original counter edge in a focused instruction test; full original four-million-iteration timeout is not replayed",
            "fatal observation executes one self-loop iteration; unbounded spins are not simulated",
            "three recording decimation stages are each factor two; physical sample rates and latency remain unproven"],
        "hardware_test":False,"audio_test":False,"firmware_changed":False,"flashable":False}
    if output:
        if output.exists():raise ValueError("preserve prior verification reports")
        output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("total_comparisons","native_steps","actual_numerical_kernel_entries","c_only_guards")}|
        {"new_decoded":len(new),"new_visited":len(new&coverage),"all_decoded":len(program.code),"all_visited":len(coverage)}))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--library",type=Path,required=True)
    parser.add_argument("--output",type=Path);parser.add_argument("--mini-image",type=Path);parser.add_argument("--smoke",action="store_true")
    args=parser.parse_args();result=verify(args.library,args.output,args.mini_image,args.smoke)


if __name__=="__main__":main()
