"""Compare stage routing C with original instructions; no device or audio test."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import re
import sys
import struct
from pathlib import Path
from dsp_stage_machine import DspStageProgram,DspStageAudioProgram,REGIONS,STATIC,MAPPED,RAM,SAMPLES,ARENA,ROOT,offset
from verify_ir_processing import SOURCE_FILES as IR_SOURCE_FILES
from verify_audio_task import SOURCES as AUDIO_SOURCES

SOURCES=tuple(dict.fromkeys((*AUDIO_SOURCES,"biquad","biquad_chain","biquad_coefficients","biquad_generator","dsp_stage")))
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32)
class IO(ctypes.Structure):_fields_=[("map",MAP),("call",CALL),("opaque",ctypes.c_void_p)]
CONTROL,EFFECTS,CONFIG,AUTOMATION=0x01c32db0,0x01c2c220,0x01c1f7f0,0x01c2e5a0
SCALAR={"capability","active","route_mask","clock","ir_delay"}

def put(data,offset,value,size=4):data[offset:offset+size]=(value&((1<<(size*8))-1)).to_bytes(size,"little")
def baseline(seed=1):
    memory=[bytearray(n) for _,n in MAPPED];r=memory[0];rng=random.Random(seed)
    def set(p,v,n=4):put(r,p-RAM,v,n)
    for i in range(6):set(CONTROL+180+i,255,1)
    for p,v in ((CONTROL+7,0),(CONTROL+20,1),(CONTROL+21,2),(CONTROL+12,0),(CONFIG+6,1),(CONFIG+7,2)):
        set(p,v,1)
    for p,v in ((0x01c34198,0),(CONFIG+20,14),(CONFIG+40,0x01c341c4),(CONTROL+96,100),(CONTROL+156,0)):
        set(p,v)
    for i in range(16):
        for p,v in ((0,7),(1,1),(2,1),(4,0),(6,0)):
            set(EFFECTS+480*i+p,v,1)
    for i in range(256):put(memory[1],4*i,rng.randrange(-(1<<28),1<<28))
    for p,n in ((0x01c321ac,6*128),(0x01c341c4,128)):
        for i in range(n):set(p+4*i,rng.randrange(-(1<<28),1<<28))
    for i in range(6):
        for j in range(4):
            p=0x01c2f3a0+i*256+j*44;set(p,1<<28)
            for k in range(20,40,4):set(p+k,rng.randrange(1<<24))
            set(p+41,j&1,1)
        for off,v in ((0,16384),(4,16384),(48,32768),(52,0),(96,4096),(100,0xfffff000)):
            set(0x01c32fa0+i*8+off,v)
    return memory

class Script:
    def __init__(self,mutations=(),returns=()):self.mutations=mutations;self.returns=returns;self.index=0
    def __call__(self,target,args,backend):
        self.index+=1
        for at,address,value,width in self.mutations:
            if at==self.index or at==-target:backend.write(address,value,width)
        if target==0x01c04862:return (0xfffffe00+137*self.index)&0xffffffff
        if target==0x01c10446:backend.write(CONTROL+100,len(args) if not self.returns else self.returns[self.index%len(self.returns)]&15,4)
        return self.returns[(self.index-1)%len(self.returns)] if self.returns else 0xffffffff

class CBackend:
    def __init__(self,program,memory,script):
        self.arrays=[(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for data in memory]
        self.tables={name:(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for name,data in program.data.items()}
        self.script,self.calls,self.errors=script,[],[]
        self.io=IO(MAP(self.map),CALL(self.call),None)
    def map(self,opaque,address,size,writable):
        for (base,n),data in zip(MAPPED,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(data)+address-base
        if not writable:
            for name,(base,end) in STATIC.items():
                if base<=address<=address+size<=end:return ctypes.addressof(self.tables[name])+address-base
        return None
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def write(self,address,value,width):
        p=self.map(None,address,width,1)
        if p is None:raise ValueError("script escaped C memory")
        ctypes.memmove(p,(value&((1<<(width*8))-1)).to_bytes(width,"little"),width)
    def read(self,address,width):
        p=self.map(None,address,width,0)
        if p is None:raise ValueError("script read escaped C memory")
        return int.from_bytes(ctypes.string_at(p,width),"little")
    def call(self,opaque,target,args,count):
        try:
            words=tuple(args[i] for i in range(count));self.calls.append((target,words,hashlib.sha256(b"".join(self.snapshot())).hexdigest()))
            return self.script(target,words,self)
        except Exception as error:self.errors.append(str(error));return 0

class Corpus:
    def __init__(self,library,replay=None):
        self.program=DspStageProgram();self.lib=ctypes.CDLL(str(library.resolve()));self.cases=0;self.visited=set();self.steps=0;self.real_calls={};self.service_calls=0
        self.lib.hyperrig_dsp_stage_run.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.lib.hyperrig_dsp_stage_helper.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.replay=replay;self.digest=hashlib.sha256();self.mutating_cases=0;self.carried_cases=0
    def compare(self,label,memory,name,args=(),mutations=(),returns=()):
        try:native=self.program.execute(memory,name,args,Script(mutations,returns))
        except Exception as error:raise AssertionError(f"{label}: native {error}") from error
        c=CBackend(self.program,memory,Script(mutations,returns));value=U32()
        if name=="stage":status=self.lib.hyperrig_dsp_stage_run(*args,ctypes.byref(c.io))
        else:status=self.lib.hyperrig_dsp_stage_helper(REGIONS[name][0],(U32*5)(*args),ctypes.byref(value),ctypes.byref(c.io))
        if status or c.errors:raise AssertionError(f"{label}: C status {status}, callback {c.errors}")
        if name in SCALAR and value.value!=native["value"]:raise AssertionError(f"{label}: scalar {value.value:#x} != {native['value']:#x}")
        for (base,_),expected,actual in zip(MAPPED,native["memory"],c.snapshot()):
            if expected!=actual:
                bad=[hex(base+i) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
                first=int(bad[0],16)-base
                raise AssertionError(f"{label}: memory {bad[:18]} native={expected[first:first+16].hex()} C={actual[first:first+16].hex()}")
        if native["calls"]!=c.calls:raise AssertionError(f"{label}: callback order/state differs: {native['calls']} / {c.calls}")
        self.cases+=1;self.visited|=native["visited"];self.steps+=native["steps"];self.service_calls+=len(native["calls"])
        for target in native["real_calls"]:self.real_calls[target]=self.real_calls.get(target,0)+1
        self.digest.update(json.dumps((label,args,native['calls'])).encode())
        for data in native['memory']:self.digest.update(data)
        self.mutating_cases+=bool(mutations);self.carried_cases+=label.startswith('carried ')
        if self.replay:
            # Replay inputs and complete expected memory, not C-produced output.
            self.replay.write(struct.pack('<10I',REGIONS[name][0],*args,*([0]*(5-len(args))),int(name in SCALAR),native['value'] if name in SCALAR else 0,len(mutations),len(returns)))
            for data in memory:self.replay.write(data)
            for change in mutations:self.replay.write(struct.pack('<qIII',*change))
            for value0 in returns:self.replay.write(struct.pack('<I',value0))
            for data in native['memory']:self.replay.write(data)
        return c.snapshot()

def corpus(c):
    for stage in (0,1):
        for count in (0,1,3,4,127,128,129,256):
            memory=baseline(count+stage);c.compare(f"empty {stage}/{count}",memory,"stage",(stage,SAMPLES,count))
    for i in range(40):
        for active in (0,1):
            memory=baseline(i);put(memory[0],EFFECTS-RAM,i,1)
            c.compare(f"capability {i}/{active}",memory,"capability",(EFFECTS,active))
            c.compare(f"active {i}/{active}",memory,"active",(EFFECTS,))
    for target,name,args in ((0,"ir_delay",(0,)),(1,"ir_delay",(ARENA,)),(2,"clear",(0x01c2f3a0,)),
        (3,"swap",(SAMPLES,SAMPLES+20)),(4,"clock",())):
        c.compare(f"helper {target}",baseline(),name,args)
    for count in (0,1,2,3,4,5,127,128,256):
        c.compare(f"copy {count}",baseline(),"copy",(SAMPLES+4,SAMPLES,count if count<256 else 255))
    rng=random.Random(714)
    for case in range(100):
        memory=baseline(case);r=memory[0];stage=case&1;n=case%11
        put(r,CONTROL-RAM+14+stage,n,1)
        put(r,0x01c34198-RAM,0x01c04862 if case%3 else 0)
        put(r,CONFIG-RAM,case%18,1);put(r,CONTROL-RAM+2,case%18,1)
        for i in range(n):
            put(r,CONTROL-RAM+348+10*stage+i,i,1)
            for off,v in ((0,rng.choice([3,7,9,10,14,18,20,21,23,25,36])),(4,rng.randrange(3)),(6,rng.randrange(4))):put(r,EFFECTS-RAM+480*i+off,v,1)
        for i in range(6):
            put(r,CONTROL-RAM+174+i,case%3,1);put(r,CONTROL-RAM+192+i,case%2,1)
            put(r,CONTROL-RAM+230+2*i,case%3,2)
        c.compare(f"stage routes {case}",memory,"stage",(stage,SAMPLES,(1,4,127,128,129)[case%5]),returns=(0xffffffff,90,0))
    for mode in range(10):
        for remaining in (1,2,3):
            memory=baseline(mode);r=memory[0];record=AUTOMATION-RAM
            for off,v in ((0,remaining),(1,0),(2,mode&1),(3,8),(4,27)):
                put(r,record+off,v,1)
            for i in range(8):
                put(r,record+5+i,i,1);put(r,record+45+i,mode,1);put(r,record+85+i,8+i,1)
                put(r,record+128+4*i,(0x3f800000,0xbf800000,0x7f800000,0x7fc12345,0x80000000,1,0x7fffffff,0xffffffff)[i])
                put(r,record+288+4*i,(0x3e800000,0xbe800000,0xff800000,0,0x80000000,0xffffffff,77,0x80000001)[i])
                put(r,EFFECTS-RAM+288+4*i,(0x3f000000,0x7f800000,0x3f800000,0x7f800001,0,1,0xfffffff0,0x7fffffff)[i])
                put(r,EFFECTS-RAM+320+4*i,(0,1,2,4,1024,0xffffffff,0x80000000,0x7fffffff)[i])
            c.compare(f"automation {mode}/{remaining}",memory,"stage",(0,SAMPLES,128))
    for case in range(80):
        memory=baseline(case);r=memory[0];n=case%11
        put(r,CONTROL-RAM+15,n,1)
        for i in range(n):
            put(r,CONTROL-RAM+358+i,i,1)
            for off,v in ((0,rng.randrange(40)),(1,rng.randrange(2)),(2,rng.randrange(2)),(4,rng.randrange(3)),(10,rng.randrange(2))):
                put(r,EFFECTS-RAM+480*i+off,v,1)
            put(r,EFFECTS-RAM+480*i+8,rng.randrange(2),2)
        put(r,0x01c33320-RAM+40,case%2,1)
        c.compare(f"route masks {case}",memory,"route_mask",(n,case%2,rng.randrange(65536),ARENA))
    for case in range(60):
        memory=baseline(case);r=memory[0];desc=memory[2];count=(0,1,2,3,4,5,7,16,127,128)[case%10]
        spans=(SAMPLES,SAMPLES if case%3==0 else SAMPLES+4 if case%3==1 else SAMPLES+512,count,SAMPLES+512,128-count,
            (0,32768,0x7fffffff,0x80000000,0xffffffff,65536)[case%6],(32768,0,0x7fffffff,0x80000001,3,65536)[case%6])
        for i,v in enumerate(spans):put(desc,4*i,v)
        c.compare(f"mixer {case}",memory,"mix",(ARENA,))
        c.compare(f"ramp mixer {case}",memory,"mix_ramp",(ARENA,case%4,case%2,case%3,case%3+1))
    for case in range(40):
        memory=baseline(case);r=memory[0];stage=case&1;branch=case%3;entry=stage*3+branch
        put(r,CONTROL-RAM+230+entry*2,case%5,2);put(r,CONTROL-RAM+198+entry,case%3,1)
        if case%2:
            put(r,CONTROL-RAM+144,SAMPLES);put(r,CONTROL-RAM+148,SAMPLES+512)
        c.compare(f"branch preparation {case}",memory,"branch_prepare",(stage,branch,SAMPLES,SAMPLES+512,(0,1,3,4,127,128)[case%6]))
    for case in range(24):
        memory=baseline(case);r=memory[0];stage=case&1;branch=case%3;side=case%3;entry=stage*3+branch
        put(r,0x01c34198-RAM,0x01c04862);put(r,CONTROL-RAM+9,1,1);put(r,0x01c34488-RAM,case%2,1)
        put(r,CONTROL-RAM+192+entry,case%2,1);put(r,CONTROL-RAM+256+4*branch,13 if case%4 else 1)
        c.compare(f"stereo preparation {case}",memory,"stereo_prepare",(stage,branch,side,SAMPLES))
        put(r,CONTROL-RAM+180+entry,0,1);put(r,CONTROL-RAM+22,case%2,1);put(r,CONTROL-RAM+152,SAMPLES+512)
        put(r,0x01c32dac-RAM,case&1,1);put(r,0x01c32dac-RAM+1,(case>>1)&1,1)
        for i,v in enumerate((SAMPLES,SAMPLES+512,case%129,SAMPLES+512,128-case%129,16384,16384)):put(memory[2],4*i,v)
        c.compare(f"stereo finish {case}",memory,"stereo_finish",(ARENA,SAMPLES,stage,branch,side))
    for case in range(8):
        memory=baseline(case);r=memory[0]
        put(r,0x01c34198-RAM,0x01c04862);put(r,CONTROL-RAM+9,1,1);put(r,CONTROL-RAM+192+case%3,1,1)
        put(r,0x01c34488-RAM,case&1,1);put(r,CONTROL-RAM+256+4*(case%3),13 if case<4 else 3)
        c.compare(f"stereo warm/copy {case}",memory,"stereo_prepare",(0,case%3,case%3,SAMPLES))
    for case in range(12):
        memory=baseline(case);r=memory[0];put(r,0x01c34198-RAM,0x01c04862)
        put(r,0x01c32dac-RAM,1,1);put(r,0x01c32dac-RAM+1,1,1);put(r,CONTROL-RAM+152,SAMPLES+512)
        put(r,CONTROL-RAM+180,0,1)
        for i,v in enumerate((SAMPLES,SAMPLES+512,64,SAMPLES+512,64,16384,16384)):put(memory[2],4*i,v)
        changes=((1,ARENA+4,SAMPLES+4*(case%16),4),(1,ARENA+8,case+1,4),(1,ARENA+16,127-case,4),
            (1,ARENA+20,case*1001,4),(1,ARENA+24,32768-case*1001,4),(2,ARENA+4,SAMPLES+44,4),
            (2,ARENA+12,SAMPLES+144,4),(2,ARENA+20,0x1357,4),(2,CONTROL+156,0xfffffff0,4))
        c.compare(f"borrowed descriptor mutation {case}",memory,"stereo_finish",(ARENA,SAMPLES,0,0,0),mutations=changes)
    effect_mutations=tuple((-target,0x01c34488,1,1) for target in (0x01c0f678,0x01c10446))
    for case in range(48):
        memory=baseline(case);r=memory[0];stage=1
        put(r,CONTROL-RAM+15,4,1);put(r,CONTROL-RAM+8,2,1)
        put(r,CONTROL-RAM+88,4,1);put(r,CONTROL-RAM+89,5,1)
        put(r,0x01c34198-RAM,0x01c04862 if case%2 else 0)
        for off,v in ((2,(0,1,15,16,127,255)[case%6]),(13,(0,16,1,127)[case%4])):put(r,CONTROL-RAM+off,v,1)
        put(r,CONFIG-RAM,(0,1,15,16,127,255)[case%6],1)
        for i in range(4):
            put(r,CONTROL-RAM+358+i,i,1);put(r,EFFECTS-RAM+i*480+4,(i%2+1) if case%3 else 0,1)
            put(r,EFFECTS-RAM+i*480+288,ARENA);put(r,EFFECTS-RAM+i*480+1,case%2,1)
        put(memory[2],0,case%2)
        for i in range(6):put(r,CONTROL-RAM+192+i,1,1)
        for i in range(3):put(r,CONTROL-RAM+268+4*i,13 if case%2 else 4)
        result=c.compare(f"active stereo {case}",memory,"stage",(stage,SAMPLES,(0,1,3,127,128,129)[case%6]),mutations=effect_mutations,returns=(0xffffffff,9,0))
        if case%6==4:
            for block in range(3):result=c.compare(f"carried stereo {case}/{block}",result,"stage",(stage,SAMPLES,128),mutations=effect_mutations,returns=(0xffffffff,9,0))
    for case in range(24):
        memory=baseline(case);r=memory[0];put(r,CONTROL-RAM+14,8,1)
        for i in range(8):
            put(r,CONTROL-RAM+348+i,i,1)
            for off,v in ((0,7 if case<12 else 9+i%2),(1,case%2),(4,1 if i<7 else 2),(6,0 if case<12 else 1)):
                put(r,EFFECTS-RAM+i*480+off,v,1)
            put(r,EFFECTS-RAM+i*480+288,ARENA)
        for i in range(6):put(r,CONTROL-RAM+180+i,case%3-1,1)
        for i in range(2):put(r,CONTROL-RAM+16+i,case&1,1);put(r,CONTROL-RAM+18+i,2,1)
        c.compare(f"long/grouped branches {case}",memory,"stage",(0,SAMPLES,128))
    for case in range(4):
        memory=baseline(case);r=memory[0];put(r,EFFECTS-RAM,25 if case<2 else 14,1)
        put(r,EFFECTS-RAM+420,case&1,1)
        for i in range(7):put(r,EFFECTS-RAM+70+2*i,case&1,2)
        c.compare(f"active inversion {case}",memory,"active",(EFFECTS,))
    memory=baseline();put(memory[0],AUTOMATION-RAM,1,1)
    c.compare("empty automation record",memory,"stage",(0,SAMPLES,128))
    for i,v in enumerate((SAMPLES,SAMPLES,0,SAMPLES,0,0,0)):put(memory[2],4*i,v)
    c.compare("empty ramp",memory,"mix_ramp",(ARENA,0,0,0,1))
    for kind in (2,4,5,14,27,31,33,36,39):
        for case in range(4):
            memory=baseline();r=memory[0];put(r,CONTROL-RAM+15,4,1);put(r,CONTROL-RAM+2,1,1);put(r,CONFIG-RAM,1,1)
            for i in range(4):
                put(r,CONTROL-RAM+358+i,i,1);put(r,EFFECTS-RAM+i*480,kind,1);put(r,EFFECTS-RAM+i*480+4,(0,1,2,0)[i],1)
                for j in range(7):put(r,EFFECTS-RAM+i*480+70+2*j,case&1,2)
            c.compare(f"capability routes {kind}/{case}",memory,"stage",(1,SAMPLES,128))
    for case in range(12):
        memory=baseline(case);r=memory[0]
        put(r,CONTROL-RAM+15,4,1);put(r,CONTROL-RAM+2,1,1);put(r,CONFIG-RAM,1,1)
        put(r,0x01c34198-RAM,0x01c04862)
        put(r,CONTROL-RAM+256,14);put(r,CONTROL-RAM+195,1,1);put(r,CONTROL-RAM+404,0xffffffff if case%2 else 1)
        for i in range(4):
            put(r,CONTROL-RAM+358+i,i,1);put(r,EFFECTS-RAM+i*480+4,i%2+1,1)
        c.compare(f"stereo warm stage {case}",memory,"stage",(1,SAMPLES,128),mutations=effect_mutations,
            returns=(0xffffffff,0,90))
    for branch in (1,2):
        for enabled in (0,1):
            memory=baseline();r=memory[0];put(r,CONTROL-RAM+14,4,1)
            for i in range(4):
                put(r,CONTROL-RAM+348+i,i,1)
                for off,v in ((0,9+i%2),(1,enabled),(4,branch),(6,1)):put(r,EFFECTS-RAM+480*i+off,v,1)
            c.compare(f"complete grouped cost {branch}/{enabled}",memory,"stage",(0,SAMPLES,128))

def joined_corpus(c):
    import verify_audio_task as audio
    program=DspStageAudioProgram();c.lib.hyperrig_dsp_stage_audio_resume.argtypes=[ctypes.POINTER(audio.Task),U32,U32,ctypes.POINTER(audio.IO)]
    joined_entries=0;segments=0
    class JoinedScript(audio.Script):
        def __call__(self,target,args,memory):
            if target in (0x01c0f678,0x01c10446):
                if target==0x01c10446:memory.write(CONTROL+100,1,4)
                memory.write(0x01c34488,1,1);return 0xffffffff
            return super().__call__(target,args,memory)
    for case in range(8):
        memory=audio.baseline(case,mode=case%2+1);r=memory[0];stage=baseline(case)[0]
        for start,size in ((EFFECTS,7680),(AUTOMATION,3584),(CONTROL,416),(CONFIG,56),(0x01c2f3a0,1536),(0x01c32fa0,144)):
            r[start-RAM:start-RAM+size]=stage[start-RAM:start-RAM+size]
        for i in range(2):
            put(r,CONTROL-RAM+14+i,case%4,1)
            for j in range(case%4):
                put(r,CONTROL-RAM+348+i*10+j,j,1);put(r,EFFECTS-RAM+480*j+4,(j%2+1) if case%2 else 0,1)
        put(r,0x01c34198-RAM,0x01c04862 if case%2 else 0)
        native=program.machine(memory,JoinedScript());state=audio.Memory(program,memory);task=audio.Task();calls=[];errors=[];script=JoinedScript()
        arrays=[]
        for name,(start,end) in STATIC.items():
            array=(ctypes.c_ubyte*(end-start)).from_buffer_copy(program.stage.data[name]);arrays.append(array);state.mapped.append(((start,end-start),array))
        def mapping(_o,p,n,_w):return state.mapping(p,n)
        def service(_o,target,args,count):
            try:
                words=tuple(args[i] for i in range(count));calls.append((target,words,state.digest()));return script(target,words,state)
            except Exception as error:errors.append(str(error));return 0
        io=audio.IO(audio.MAP(mapping),audio.CALL(service),None);previous_steps=0
        for segment in range(3):
            expected=native.resume(1,1);status=c.lib.hyperrig_dsp_stage_audio_resume(ctypes.byref(task),1,1,ctypes.byref(io))
            if errors or status!=expected["reason"]:raise AssertionError(("joined stage",case,segment,status,expected["reason"],errors))
            assert tuple(getattr(task,k) for k,_ in audio.Task._fields_)==expected["task"],("joined control",case,segment)
            if state.snapshot()!=expected["memory"]:
                differences=[(hex(base+i),x,y) for (base,_),a,b in zip(audio.MAPPED,state.snapshot(),expected["memory"]) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
                raise AssertionError(("joined memory",case,segment,differences[:16]))
            assert calls==expected["calls"],("joined callbacks",case,segment,calls,expected["calls"])
            c.cases+=1;c.visited|=expected["visited"];c.steps+=expected["steps"]-previous_steps;previous_steps=expected["steps"];segments+=1
            c.digest.update(json.dumps(('joined',case,segment,expected['task'],expected['calls'])).encode())
            for data in expected['memory']:c.digest.update(data)
        joined_entries+=sum((call[0] if isinstance(call,tuple) else call)==REGIONS["stage"][0] for call in native.real_calls)
    if not joined_entries:raise AssertionError("joined corpus never entered original stage")
    c.joined_program=program;return {"observation_segments":segments,"original_stage_entries":joined_entries}

def api_checks(c):
    count=0;b=CBackend(c.program,baseline(),Script());args=(U32*5)(ARENA,0,0,0,0);result=U32()
    def rejected(status,expected):
        nonlocal count
        if status!=expected:raise AssertionError(('API guard',count,status,expected))
        count+=1
    rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,None),-200)
    rejected(c.lib.hyperrig_dsp_stage_helper(0,args,ctypes.byref(result),ctypes.byref(b.io)),-202)
    rejected(c.lib.hyperrig_dsp_stage_helper(REGIONS['mix'][0],None,ctypes.byref(result),ctypes.byref(b.io)),-200)
    rejected(c.lib.hyperrig_dsp_stage_helper(REGIONS['mix'][0],args,None,ctypes.byref(b.io)),-200)
    for io in (IO(MAP(),b.io.call,None),IO(b.io.map,CALL(),None)):
        rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(io)),-200)
    for stage,samples,count0 in ((2,SAMPLES,128),(0,SAMPLES+1,128),(0,SAMPLES,257)):
        rejected(c.lib.hyperrig_dsp_stage_run(stage,samples,count0,ctypes.byref(b.io)),-202)
    for address,value,width in ((CONTROL+14,11,1),(CONTROL+8,9,1),(EFFECTS,40,1),(EFFECTS+4,3,1),(CONTROL+180,2,1)):
        b=CBackend(c.program,baseline(),Script());b.write(address,value,width)
        rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(b.io)),-202)
    b=CBackend(c.program,baseline(),Script());b.write(CONTROL+14,1,1);b.write(CONTROL+348,16,1)
    rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(b.io)),-202)
    for target,p in ((REGIONS['copy'][0],(SAMPLES,SAMPLES,257)),(REGIONS['route_mask'][0],(11,0,0,ARENA)),
        (REGIONS['route_mask'][0],(0,0,65536,ARENA)),(REGIONS['stereo_prepare'][0],(2,0,0,0)),
        (REGIONS['branch_prepare'][0],(0,3,0,0,128)),(REGIONS['branch_prepare'][0],(0,0,0,0,129)),
        (REGIONS['mix_ramp'][0],(ARENA,0,0,3,1)),(REGIONS['stereo_finish'][0],(ARENA,SAMPLES,0,0,1))):
        b=CBackend(c.program,baseline(),Script());rejected(c.lib.hyperrig_dsp_stage_helper(target,(U32*5)(*p),ctypes.byref(result),ctypes.byref(b.io)),-202)
    for token in (1,0x1c01058,0xffffffff):
        b=CBackend(c.program,baseline(),Script());b.write(0x01c34198,token,4)
        rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(b.io)),-202)
    memory=baseline();put(memory[0],0x01c34198-RAM,0x01c04862);put(memory[0],CONTROL-RAM+14,1,1);put(memory[0],EFFECTS-RAM+4,1,1)
    for change in ((0x01c34198,1,4),(CONTROL+14,255,1),(EFFECTS,255,1)):
        b=CBackend(c.program,memory,Script(((1,*change),)))
        rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(b.io)),-202)
    b=CBackend(c.program,baseline(),Script());missing=IO(MAP(lambda *_:None),b.io.call,None)
    rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(missing)),-201)
    padding=(ctypes.c_ubyte*1024)();unaligned=IO(MAP(lambda *_:ctypes.addressof(padding)+1),b.io.call,None)
    rejected(c.lib.hyperrig_dsp_stage_run(0,SAMPLES,128,ctypes.byref(unaligned)),-202)
    for target in ('mix','mix_ramp','mix_select','stereo_finish'):
        b=CBackend(c.program,baseline(),Script());b.write(ARENA,ARENA,4);b.write(ARENA+8,1,4)
        rejected(c.lib.hyperrig_dsp_stage_helper(REGIONS[target][0],args,ctypes.byref(result),ctypes.byref(b.io)),-202)
    return count

def source_paths():
    paths=set(IR_SOURCE_FILES)
    for name in SOURCES:
        paths.add(f'firmware/src/hyperrig_{name}.c');paths.add(f'firmware/include/hyperrig/hyperrig_{name}.h')
    paths.update(('tools/dsp_stage_machine.py','tools/verify_dsp_stage.py','tools/build_dsp_stage.py',
        'tests/test_dsp_stage_machine.py','tests/dsp_stage_sanitize.c','tools/audio_task_machine.py','tools/verify_audio_task.py'))
    # These modules are loaded with exec_module without sys.modules entries.
    from biquad_coefficients_machine import FLOAT,BRANCH
    from dsp_audio_path_machine import ARITHMETIC
    for module in (FLOAT,BRANCH,ARITHMETIC):paths.add(Path(module.__file__).resolve().relative_to(ROOT).as_posix())
    pending=[ROOT/p for p in paths if p.endswith(('.c','.h'))];scanned=set()
    while pending:
        path=pending.pop().resolve()
        if path in scanned:continue
        scanned.add(path)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',path.read_text(),re.M):
            for header in (path.parent/name,ROOT/'firmware/include'/name):
                if header.is_file():
                    header=header.resolve();paths.add(header.relative_to(ROOT).as_posix());pending.append(header);break
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
    return sorted(paths)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--library",type=Path,required=True);parser.add_argument("--output",type=Path);parser.add_argument("--mini-image",type=Path);parser.add_argument("--sanitizer-corpus",type=Path);args=parser.parse_args()
    if args.output and args.output.exists():parser.error('choose a new verification report')
    replay=args.sanitizer_corpus.open('xb') if args.sanitizer_corpus else None
    c=Corpus(args.library,replay)
    # Instantiate both corpora before hashing their transitive decoder imports.
    DspStageAudioProgram()
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths()}
    corpus(c)
    if replay:replay.close()
    replay_count=c.cases;joined=joined_corpus(c);guards=api_checks(c)
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();code=c.joined_program.code
    new={p for start,end in REGIONS.values() for p in code if start<=p<end}
    unreachable={0x01c11530,0x01c11532,0x01c11536,0x01c11538,0x01c1153a,0x01c1172e,0x01c11730}
    assert new-c.visited==unreachable,'unexpected missing stage coverage'
    static={name:{'start':start,'end_exclusive':end,'sha256':hashlib.sha256(app[offset(start):offset(end)]).hexdigest()} for name,(start,end) in STATIC.items()}
    from audio_task_machine import STATIC as AUDIO_STATIC
    from dsp_audio_path_machine import TABLE,PRIOR_TABLE,RESET_CONFIGURATION
    inherited_static=dict(AUDIO_STATIC)|{'capture_dispatch':(0x01c12bf2,0x01c12bf6),'gain_table':TABLE,
        'coefficient_selector':(PRIOR_TABLE,PRIOR_TABLE+10),'reset_configuration':RESET_CONFIGURATION,'task_registration':(0x02005250,0x0200525e)}
    bound_static={name:{'start':start,'end_exclusive':end,'sha256':hashlib.sha256(app[offset(start):offset(end)]).hexdigest()} for name,(start,end) in inherited_static.items()}
    windows={hex(pc):{'start':pc,'end_exclusive':pc+record[1],'sha256':hashlib.sha256(app[offset(pc):offset(pc)+record[1]]).hexdigest()} for pc,record in sorted(code.items())}
    mini_binding=None
    if args.mini_image:
        from hyperrig.jieli import unpack_app
        raw=args.mini_image.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert sha=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        mini=unpack_app(raw)[2]['app.bin']
        for record in (*windows.values(),*static.values(),*bound_static.values()):
            start,end=record['start'],record['end_exclusive'];assert mini[offset(start):offset(end)]==app[offset(start):offset(end)],hex(start)
        mini_binding={'image_sha256':sha,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)+len(bound_static)}
    from audio_task_machine import SERVICES as AUDIO_SERVICES
    services=dict(AUDIO_SERVICES)|{0x01c0f678:3,0x01c10446:4}
    original=ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin';original_sha=hashlib.sha256(original.read_bytes()).hexdigest()
    assert original_sha=='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    report={'schema':1,'project':'HyperRig','component':'reconstructed-dsp-stage','result':'pass',
        'scope':'Complete stage/branch scheduling and actual Q28 filters/mixer, joined to the original audio task',
        'original_image_sha256':original_sha,'decoded_image_sha256':hashlib.sha256(app).hexdigest(),
        'total_comparisons':c.cases,'original_instruction_steps':c.steps,'sanitizer_replay_cases':replay_count,'service_calls':c.service_calls,
        'c_only_guard_checks':guards,'joined_audio_task':joined,'mutating_callback_cases':c.mutating_cases,'carried_stage_calls':c.carried_cases,
        'outputs_state_and_ordered_services_sha256':c.digest.hexdigest(),
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':sorted(new-c.visited),
            'all_decoded':len(code),'all_visited':len(c.visited),'unvisited_all':sorted(set(code)-c.visited),
            'missing_classification':{hex(p):'Empty branch-group fallback: valid route scan produces length >=1; the preserved callee-saved group length cannot reach the negative/zero test.' for p in sorted(unreachable)},
            'note':'Joined audio-task and inherited numerical paths are counted once; prior corpus coverage is not added.'},
        'functions':{name:{'start':start,'end_exclusive':end,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(start<=p<end for p in code),'visited':sum(start<=p<end for p in c.visited),
            'unvisited':[p for p in code if start<=p<end and p not in c.visited]} for name,(start,end) in REGIONS.items()},
        'static_data':static,'bound_static_data':bound_static,'bound_instruction_windows':windows,
        'source_sha256':sources,'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),'mini_v4_binding':mini_binding,
        'standalone_external_services':{'0x01c04862':0,'0x01c0f678':3,'0x01c10446':4},
        'joined_external_services':{hex(p):n for p,n in services.items() if p not in code},
        'standalone_actual_q28_entries':sum(c.real_calls.get(p,0) for p in (0x01c15dec,0x01c15fdc)),
        'scripted_recovered_kernel_replacements':0,'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['Individual/grouped effect wrappers remain scripted; their effect outputs are not reconstructed arithmetic.',
            'The type-7 IR numerical dispatcher route is traced, but this corpus does not execute the dispatcher or installation/ownership wrappers.',
            'Clock and inherited audio-task platform/sample services remain explicit synchronous scripts; no timing or hardware claims.',
            'Route/capability domains and descriptor/sample disjointness are explicit API guards; partial effects survive guard failures.',
            'Complete bodies are reconstructed within declared domains; unvisited original addresses are listed rather than called verified.',
            'ASan replay covers standalone stage/helper original-comparison fixtures; joined task cases run in the host UBSan library.']}
    assert sources=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'sources changed during verification'
    if args.output:args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ('result','total_comparisons','original_instruction_steps','c_only_guard_checks','joined_audio_task')}|
        {key:report['instruction_coverage'][key] for key in ('new_decoded','new_visited','all_decoded','all_visited')}))

if __name__=="__main__":main()
