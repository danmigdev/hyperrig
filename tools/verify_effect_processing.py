"""Compare complete effect callers against decoded original instructions offline."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import struct
import subprocess
import re
import sys
from pathlib import Path
from effect_processing_machine import (EffectProcessingProgram,EffectProcessingAudioProgram,REGIONS,ENTRIES,ARITIES,STATIC,MAPPED,boundary_digest,
    RAM,SAMPLES,ARENA,ROOT,offset)
from verify_dsp_stage import SOURCES as STAGE_SOURCES
from build_ir_processing import SOURCES as IR_SOURCES

SOURCES=tuple(dict.fromkeys((*[f'firmware/src/hyperrig_{name}.c' for name in STAGE_SOURCES],
    *IR_SOURCES,'firmware/src/hyperrig_effect_resampling.c','firmware/src/hyperrig_effect_enable.c','firmware/src/hyperrig_effect_processing.c')))
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):_fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p)]
EFFECTS,CONTROL,CONFIG,AUTOMATION=0x01c2c220,0x01c32db0,0x01c1f7f0,0x01c2e5a0
SCALAR={'capture_probe','cost','extra_cost','q16','exp','ir_active','ir_accelerated','peak16','individual','grouped'}
def put(data,offset,value,size=4):data[offset:offset+size]=(value&((1<<(size*8))-1)).to_bytes(size,'little')
def baseline(seed=1):
    memory=[bytearray(n) for _,n in MAPPED];rng=random.Random(seed)
    for i in range(len(memory[1])//4):put(memory[1],i*4,rng.getrandbits(32))
    return memory
def setword(memory,address,value,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:put(data,address-base,value,size);return
    raise ValueError('fixture write outside original-address storage')

class Script:
    def __init__(self,mutations=(),returns=(),clocks=()):
        self.mutations,self.returns,self.index=mutations,returns,0
        self.clocks,self.clock_index=clocks,0
    def __call__(self,target,args,backend):
        self.index+=1
        for at,address,value,width in self.mutations:
            if at==self.index or at==-target:backend.write(address,value,width)
        if target==0x01c04862:
            self.clock_index+=1
            return self.clocks[(self.clock_index-1)%len(self.clocks)] if self.clocks else (0xffffff00+137*self.index)&0xffffffff
        if 0xffff0000<=target<=0xffff0002:return 128 if target==0xffff0000 else 0
        if target==0x01c0bbce:
            backend.write(args[2],(args[0]*655+17)&0xffffffff,4);backend.write(args[3],(65536-args[0]*413)&0xffffffff,4)
        if target==0x01c18f90:
            p=args[0];n=backend.read(p+52,4);delta=backend.read(p+16,4)
            for off,change in ((8,n*16),(12,n*16*delta),(32,n*4*backend.read(p+40,4)),(36,n*4*backend.read(p+44,4))):
                backend.write(p+off,backend.read(p+off,4)+change,4)
        if target==0x01c0b4b8:
            p=args[0]+288
            for off,change in ((0,args[2]),(4,args[2]*31),(12,args[2]*17)):
                backend.write(p+off,backend.read(p+off,4)+change,4)
        if target==0x01c0b524:backend.write(args[4],backend.read(args[4],4)+args[1]*19,4)
        return self.returns[(self.index-1)%len(self.returns)] if self.returns else 0

class Recording:
    def __init__(self,script):self.script,self.events=script,[]
    def __call__(self,target,args,backend):
        writes=[]
        class View:
            def __getattr__(self,name):return getattr(backend,name)
            def write(self,address,value,size):
                writes.append((address,value&((1<<(8*size))-1),size));backend.write(address,value,size)
        result=self.script(target,args,View())&0xffffffff
        self.events.append((target,args,result,writes));return result

class Replay:
    def __init__(self,path,program):
        self.file=path.open('w+b');self.count=0;self.file.write(b'HRFXP001');self.words(0,len(STATIC))
        for name,(start,end) in STATIC.items():self.words(start,end-start);self.file.write(program.data[name])
    def words(self,*values):self.file.write(struct.pack('<'+'I'*len(values),*(v&0xffffffff for v in values)))
    def case(self,mode,entry,args,expected_status,value,before,after,events,*,mapped=MAPPED,task_before=(0,0,0,0),task_after=(0,0,0,0)):
        self.words(mode,entry,len(args),*args,*([0]*(12-len(args))),expected_status,value,*task_before,*task_after,len(mapped))
        for (base,size),old,new in zip(mapped,before,after):self.words(base,size);self.file.write(old);self.file.write(new)
        self.words(len(events))
        for target,arguments,result,writes in events:
            self.words(target,len(arguments),*arguments,*([0]*(12-len(arguments))),result,len(writes))
            for address,data,width in writes:self.words(address,data&0xffffffff,data>>32,width)
        self.count+=1
    def close(self):self.file.seek(8);self.words(self.count);self.file.close()

class CBackend:
    def __init__(self,program,memory,script):
        self.arrays=[(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for data in memory]
        self.tables={name:(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for name,data in program.data.items()}
        self.script,self.calls,self.errors,self.borrowed=script,[],[],None
        self.io=IO(MAP(self.map),CALL(self.call),None)
    def map(self,opaque,address,size,writable):
        for (base,n),data in zip(MAPPED,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(data)+address-base
        if not writable:
            for name,(base,end) in STATIC.items():
                if base<=address<=address+size<=end:return ctypes.addressof(self.tables[name])+address-base
        return None
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def locate(self,address,size,writable):
        p=self.map(None,address,size,writable)
        if p is None and self.borrowed:p=self.borrowed.contents.map(self.borrowed.contents.opaque,address,size,writable)
        if p is None:raise ValueError(f'callback escaped mapped storage {address:#x}')
        return p
    def read(self,address,size):return int.from_bytes(ctypes.string_at(self.locate(address,size,0),size),'little')
    def write(self,address,value,size):ctypes.memmove(self.locate(address,size,1),(value&((1<<(size*8))-1)).to_bytes(size,'little'),size)
    def call(self,opaque,target,args,count,borrowed):
        try:
            self.borrowed=borrowed;words=tuple(args[i] for i in range(count))
            self.calls.append((target,words,boundary_digest(target,words,self,hashlib.sha256(b''.join(self.snapshot())).hexdigest())))
            result=self.script(target,words,self);self.borrowed=None;return result
        except Exception as error:self.errors.append(str(error));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectProcessingProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        self.lib.hyperrig_effect_processing_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_processing_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.cases,self.steps=0,0;self.visited=set();self.real_calls={};self.digest=hashlib.sha256()
        self.replay=Replay(replay,self.program) if replay else None;self.labels=[]
    def compare(self,label,memory,name,args=(),mutations=(),returns=(),clocks=()):
        recording=Recording(Script(mutations,returns,clocks))
        try:native=self.program.execute(memory,name,args,recording)
        except Exception as error:raise AssertionError(f'{label}: original {error}') from error
        c=CBackend(self.program,memory,Script(mutations,returns,clocks));value=U32()
        status=self.lib.hyperrig_effect_processing_stage(*args,ctypes.byref(c.io)) if name=='stage' else self.lib.hyperrig_effect_processing_execute(ENTRIES[name],(U32*12)(*args),ctypes.byref(value),ctypes.byref(c.io))
        if status or c.errors:raise AssertionError(f'{label}: C status {status}, callback {c.errors}')
        if name in SCALAR and value.value!=native['value']:raise AssertionError(f'{label}: scalar C={value.value:#x}, original={native["value"]:#x}')
        for (base,_),expected,actual in zip(MAPPED,native['memory'],c.snapshot()):
            if expected!=actual:
                bad=[i for i,(x,y) in enumerate(zip(expected,actual)) if x!=y];i=bad[0]&~3
                raise AssertionError(f'{label}: memory at {base+i:#x} original={expected[i:i+16].hex()} C={actual[i:i+16].hex()} ({len(bad)} bytes)')
        if native['calls']!=c.calls:raise AssertionError(f'{label}: callback order/state differs: {native["calls"]} / {c.calls}')
        self.cases+=1;self.steps+=native['steps'];self.visited|=native['visited']
        self.labels.append(label)
        for entry in native['real_calls']:self.real_calls[entry]=self.real_calls.get(entry,0)+1
        self.digest.update(json.dumps((label,args,native['calls'])).encode())
        for data in native['memory']:self.digest.update(data)
        if self.replay and (self.cases%4==0 or name in ('stage','individual','grouped')):
            self.replay.case(name=='stage',ENTRIES[name],args,0,value.value,memory,native['memory'],recording.events)
        return c.snapshot()

def helper_corpus(c):
    rng=random.Random(7751)
    for kind in range(40):
        for mode in range(4):
            memory=baseline(kind+mode);r=memory[0]
            for i in range(288,480,4):setword(memory,EFFECTS+i,rng.getrandbits(32))
            for p,v,n in ((EFFECTS,kind,1),(EFFECTS+6,mode,1),(EFFECTS+288,ARENA if mode&1 else 0,4),
                          (EFFECTS+84,ARENA,4),(EFFECTS+88,32768,4),(ARENA,mode&1,4),(ARENA+548,mode>>1,4)):
                setword(memory,p,v,n)
            c.compare(f'cost {kind}/{mode}',memory,'cost',(EFFECTS,mode&1))
            c.compare(f'extra cost {kind}/{mode}',memory,'extra_cost',(EFFECTS,mode&1,100 if mode&2 else 40,1,1,mode&1))
    for case in range(80):
        memory=baseline(case);p=ARENA if case&1 else 0
        if p:setword(memory,p,case%3);setword(memory,p+548,case%4)
        c.compare(f'active {case}',memory,'ir_active',(p,));c.compare(f'accelerated {case}',memory,'ir_accelerated',(p,))
        x=rng.getrandbits(32);y=rng.getrandbits(32)
        c.compare(f'q16 {case}',memory,'q16',(x,y));c.compare(f'exp {case}',memory,'exp',(x,))
        c.compare(f'peak16 {case}',memory,'peak16',(SAMPLES,))
        c.compare(f'ramp16 {case}',memory,'ramp16',(SAMPLES,x,y));c.compare(f'wrap16 {case}',memory,'wrap16',(SAMPLES,x,y))
    for n in (0,1,2,3,4,7,15,16,17,31,32,127,128,255,256,512):
        for pattern in range(4):
            memory=baseline(n+pattern);previous=rng.getrandbits(64);wanted=rng.getrandbits(64)
            if pattern==0:previous=wanted=0
            if pattern==1:previous=0;wanted=0x01234567
            if pattern==2:previous=0xFFFFFFFF81234567;wanted=0xFFFFFFFF89ABCDEF
            c.compare(f'peak fade {n}/{pattern}',memory,'peak_fade',(SAMPLES,n,previous&0xffffffff,previous>>32,wanted&0xffffffff,wanted>>32))
    for quarter in range(4):
        for mode in range(1,9):
            memory=baseline(quarter+mode);setword(memory,AUTOMATION+3,4,1)
            for i in range(4):
                setword(memory,AUTOMATION+5+i,i,1);setword(memory,AUTOMATION+45+i,mode,1)
                setword(memory,AUTOMATION+85+i,i+4,1);setword(memory,AUTOMATION+288+i*4,rng.getrandbits(32))
                setword(memory,EFFECTS+288+i*4,rng.getrandbits(32));setword(memory,EFFECTS+304+i*4,rng.getrandbits(32))
            c.compare(f'automation {mode}/{quarter}',memory,'automation',(AUTOMATION,EFFECTS+288,quarter))

def dispatch_corpus(c,start=0):
    rng=random.Random(221)
    for kind in range(start,40):
        for stereo in (0,1,2,3):
            for count in (0,1,16,31,32,128):
                memory=baseline(kind+stereo+count);p=EFFECTS+288
                setword(memory,EFFECTS,kind,1);setword(memory,CONTROL+10,stereo,1)
                setword(memory,CONTROL+9,63,1);setword(memory,CONFIG+44,SAMPLES+2048)
                setword(memory,EFFECTS+84,ARENA);setword(memory,EFFECTS+88,32768)
                setword(memory,p,65536 if kind==2 else 0)
                if kind==25:
                    for off,val in ((4,0x80000000),(16,100000),(20,100000),(24,100000),(28,100000),(32,1000),(36,1000),(48,64000),(52,30000),(56,65000),(60,32000)):
                        setword(memory,p+off,val)
                    setword(memory,EFFECTS+420,50,1);setword(memory,EFFECTS+421,1,1)
                if kind in (4,26):
                    for j in range(3 if kind==4 else 4):
                        setword(memory,p+j*44,1<<28);setword(memory,p+j*44+40,1,1);setword(memory,p+j*44+41,j&1,1)
                if kind in (36,37):setword(memory,EFFECTS+464,65536);setword(memory,EFFECTS+468,40000)
                c.compare(f'dispatch {kind}/{stereo}/{count}',memory,'dispatch',(EFFECTS,SAMPLES,count,1))

def wrapper_corpus(c):
    for kind in (2,3,5,6,7,11,14,25,28,38,39):
        for phase in range(6):
            for state in range(4):
                for enabled in (0,1):
                    memory=baseline(kind+phase+state);p=EFFECTS+288;count=128
                    for address,value,width in ((EFFECTS,kind,1),(EFFECTS+1,enabled,1),(EFFECTS+2,1,1),
                        (EFFECTS+10,phase,1),(EFFECTS+11,1,1),(EFFECTS+12,state,1),(EFFECTS+13,1,1),
                        (CONFIG+40,SAMPLES+2048,4),(CONFIG+44,SAMPLES+2048,4),(CONTROL+9,64,1),
                        (p,65536 if kind==2 else 0,4)):
                        setword(memory,address,value,width)
                    c.compare(f'individual {kind}/{phase}/{state}/{enabled}',memory,'individual',(0,SAMPLES,count))
    for mode in range(8):
        memory=baseline(mode);count=32;setword(memory,ARENA,0x020100,4)
        for slot in range(3):
            p=EFFECTS+slot*480
            for address,value,width in ((p,2,1),(p+1,1 if mode&1 else slot==0,1),(p+2,1,1),
                (p+6,1,1),(p+288,65536,4),(p+292,65000,4)):
                setword(memory,address,int(value),width)
        if mode&2:setword(memory,0x01c34198,0x01c04862);setword(memory,0x01c34444,0x7fffffff)
        if mode&4:setword(memory,EFFECTS+47,2,1)
        setword(memory,CONFIG+40,SAMPLES+2048);setword(memory,CONFIG+44,SAMPLES+2048)
        c.compare(f'group {mode}',memory,'grouped',(ARENA,3,SAMPLES,count))

def numerical_dispatch_corpus(c,start=0):
    rng=random.Random(281731)
    for kind in (8,14,25,38):
        if kind<start:continue
        for case in range(120):
            memory=baseline(case);p=EFFECTS+288;n=(0,1,16,31,32,127,128)[case%7]
            for off in range(0,192,4):setword(memory,p+off,rng.getrandbits(32))
            for address,value,width in ((EFFECTS,kind,1),(CONTROL+10,case%4,1),(CONTROL+9,case%101,1),
                (CONFIG+44,SAMPLES+2048,4),(CONFIG+20,100,4),(EFFECTS+84,ARENA,4)):
                setword(memory,address,value,width)
            if kind==14:setword(memory,p+24,(98,99,100)[case%3])
            if kind==25:
                for off,value in ((4,(0,0x7fffffff,0x80000000,0xffffffff)[case%4]),(8,(-100,0,100)[case%3]),
                    (20,500000),(24,500000),(28,500000),(32,1000000),(36,1000000),(48,64000),(52,50000),(56,65000),(60,51000)):
                    setword(memory,p+off,value)
                for address,value,width in ((EFFECTS+404,0,1),(EFFECTS+405,0,1),(EFFECTS+406,case%3,1),
                    (EFFECTS+407,case%4,1),(EFFECTS+408,case%26,1),(EFFECTS+412,123456,4),(EFFECTS+416,99,4),
                    (EFFECTS+420,100,1),(EFFECTS+421,case%2,1),(EFFECTS+424,(0,50,100)[case%3],1),
                    (EFFECTS+425,case%2,1),(EFFECTS+426,0,1),(CONTROL+40,case%2,4)):
                    setword(memory,address,value,width)
            c.compare(f'numerical dispatch {kind}/{case}',memory,'dispatch',(EFFECTS,SAMPLES,n,1))

def stage_corpus(c):
    from verify_dsp_stage import baseline as stage_baseline
    for case in range(48):
        memory=baseline(case);old=stage_baseline(case);memory[0][:]=old[0];memory[1][:len(old[1])]=old[1]
        stage=case%2;n=(0,1,16,31,32,127,128)[case%7];slots=case%5
        setword(memory,CONTROL+14+stage,slots,1)
        for slot in range(slots):
            p=EFFECTS+480*slot;kind=(2,4,9,14,26,38)[(case+slot)%6]
            setword(memory,CONTROL+348+stage*10+slot,slot,1);setword(memory,p,kind,1)
            setword(memory,p+4,(slot%2+1) if case%3 else 0,1);setword(memory,p+6,case%2 if kind==9 else 0,1)
            if kind==2:setword(memory,p+288,65536);setword(memory,p+292,65000)
        if n==0 and case%2:n=16
        c.compare(f'joined stage {case}',memory,'stage',(stage,SAMPLES,n))

def timing_corpus(c):
    for kind in (2,7,11,25,28,38):
        for state in range(4):
            for mode in range(12):
                memory=baseline(kind+state+mode);p=EFFECTS+288
                for address,value,width in ((EFFECTS,kind,1),(EFFECTS+1,mode&1,1),(EFFECTS+2,1,1),
                    (EFFECTS+8,1500,2),(EFFECTS+10,mode%6,1),(EFFECTS+11,mode%5,1),
                    (EFFECTS+12,state,1),(EFFECTS+13,(0,1,2,32)[mode%4],1),(p,65536 if kind==2 else 0,4),
                    (0x01c34198,0x01c04862,4),(0x01c343d8,5000,4),(CONTROL+96,100,4),
                    (0x01c34444,5100-(-1,0,1,625,626,5000)[mode%6],4),
                    (CONFIG+40,SAMPLES+2048,4),(CONFIG+44,SAMPLES+2048,4),(CONTROL+9,50,1)):
                    setword(memory,address,value,width)
                mutations=((-0x01c04862,0x01c343d8,2345,4),(-0x01c04862,CONTROL+132,mode&1,1)) if mode%3==2 else ()
                c.compare(f'timing {kind}/{state}/{mode}',memory,'individual',(0,SAMPLES,128),mutations=mutations)
    for case in range(48):
        kind=(2,5,11,14,25,38)[case%6];memory=baseline(case);p=EFFECTS+288;n=(1,16,31,128)[case%4]
        for address,value,width in ((EFFECTS,kind,1),(EFFECTS+1,1,1),(EFFECTS+2,1,1),(EFFECTS+10,case%3,1),
            (EFFECTS+11,case%4,1),(p,65000 if kind==2 else 0,4),(EFFECTS+84,ARENA,4),
            (CONFIG+40,SAMPLES+2048,4),(CONFIG+44,SAMPLES+2048,4),(CONTROL+9,50,1),
            (CONTROL+268,25,1),(CONTROL+284,48,1),(CONTROL+300,70,1),(0x01c34488,case&1,1)):
            setword(memory,address,value,width)
        target=0x01c08f80 if kind==5 else 0x01c0b4b8 if kind==11 else 0x01c1ee40 if kind==38 else 0x01c18f90
        if kind==25:setword(memory,p+4,0x80000000)
        mutations=((-target,p+68,0x13578,4),(-target,p+72,0xabcdef,4),(-target,CONFIG+20,99,4))
        c.compare(f'stereo mutations {kind}/{case}',memory,'individual',(0,SAMPLES,n),mutations=mutations)

def audio_corpus(c):
    import verify_audio_task as audio
    from verify_dsp_stage import baseline as stage_baseline
    from effect_processing_machine import SERVICES
    program=EffectProcessingAudioProgram()
    c.lib.hyperrig_effect_processing_audio_resume.argtypes=[ctypes.POINTER(audio.Task),U32,U32,ctypes.POINTER(IO)]
    class JoinedScript(audio.Script):
        def __init__(self):super().__init__();self.effects=Script()
        def __call__(self,target,args,memory):
            if target in SERVICES and target!=0x01c04862:return self.effects(target,args,memory)
            return super().__call__(target,args,memory)
    entries=private_entries=0
    for case in range(10):
        memory=audio.baseline(case,mode=case%2+1);r=memory[0];stage=stage_baseline(case)[0]
        for start,size in ((EFFECTS,7680),(AUTOMATION,3584),(CONTROL,416),(CONFIG,56),(0x01c2f3a0,1536),(0x01c32fa0,144)):
            r[start-RAM:start-RAM+size]=stage[start-RAM:start-RAM+size]
        for side in range(2):
            put(r,CONTROL-RAM+14+side,3,1)
            for slot in range(3):
                p=EFFECTS-RAM+slot*480;put(r,CONTROL-RAM+348+side*10+slot,slot,1)
                kind=(2,4,25 if case>=8 else 14)[slot]
                put(r,p,kind,1);put(r,p+4,0 if case<4 else slot%2+1,1)
                if slot==0:put(r,p+288,65536);put(r,p+292,60000)
                if kind==25:
                    put(r,p+84,audio.MAPPED[-1][0]+100000);put(r,p+292,0x80000000)
                    for off,value in ((304,100000),(308,100000),(312,100000),(316,100000),(320,100000),(324,100000),
                        (336,64000),(340,32000),(344,65000),(348,30000)):
                        put(r,p+off,value)
                    put(r,p+420,50,1);put(r,p+421,1,1);put(r,p+425,1,1)
        put(r,0x01c34198-RAM,0x01c04862 if case%2 else 0)
        recording=Recording(JoinedScript());native=program.machine(memory,recording);state=audio.Memory(program,memory);task=audio.Task();calls=[];errors=[];script=JoinedScript();tables=[]
        for name,(start,end) in STATIC.items():
            array=(ctypes.c_ubyte*(end-start)).from_buffer_copy(program.effects.data[name]);tables.append(array);state.mapped.append(((start,end-start),array))
        def mapping(_o,p,n,_w):return state.mapping(p,n)
        def service(_o,target,args,count,borrowed):
            try:
                class View:
                    def __getattr__(self,name):return getattr(state,name)
                    def locate(self,address,size,writable):
                        p=state.mapping(address,size)
                        if p is None:p=borrowed.contents.map(borrowed.contents.opaque,address,size,writable)
                        if p is None:raise ValueError('audio callback escaped borrowed storage')
                        return p
                    def read(self,address,size):return int.from_bytes(ctypes.string_at(self.locate(address,size,0),size),'little')
                    def write(self,address,value,size):ctypes.memmove(self.locate(address,size,1),(value&((1<<(8*size))-1)).to_bytes(size,'little'),size)
                view=View();words=tuple(args[i] for i in range(count))
                calls.append((target,words,boundary_digest(target,words,view,state.digest())));return script(target,words,view)
            except Exception as error:errors.append(str(error));return 0
        io=IO(MAP(mapping),CALL(service),None);previous_steps=0
        for segment in range(3):
            before=state.snapshot();task_before=tuple(getattr(task,k) for k,_ in audio.Task._fields_);event_start=len(recording.events)
            expected=native.resume(1,1);status=c.lib.hyperrig_effect_processing_audio_resume(ctypes.byref(task),1,1,ctypes.byref(io))
            if errors or status!=expected['reason']:raise AssertionError(('audio status',case,segment,status,expected['reason'],errors))
            assert tuple(getattr(task,k) for k,_ in audio.Task._fields_)==expected['task'],('audio control',case,segment)
            if state.snapshot()!=expected['memory']:
                differences=[(hex(base+i),x,y) for (base,_),a,b in zip(audio.MAPPED,state.snapshot(),expected['memory']) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
                raise AssertionError(('audio memory',case,segment,differences[:16]))
            if calls!=expected['calls']:raise AssertionError(('audio services',case,segment,calls,expected['calls']))
            c.cases+=1;c.visited|=expected['visited'];c.steps+=expected['steps']-previous_steps;previous_steps=expected['steps']
            c.digest.update(json.dumps(('audio',case,segment,expected['task'],expected['calls'])).encode())
            for data in expected['memory']:c.digest.update(data)
            if c.replay:c.replay.case(2,0,(1,1),status,0,before,expected['memory'],recording.events[event_start:],mapped=audio.MAPPED,
                task_before=task_before,task_after=expected['task'])
        entries+=sum((call[0] if isinstance(call,tuple) else call)==REGIONS['dispatch'][0] for call in native.real_calls)
        private_entries+=sum(target==0x01c18f90 for target,_,_ in calls)
    if not entries:raise AssertionError('audio never entered effect dispatcher')
    if not private_entries:raise AssertionError('audio never reached the borrowed dual descriptor')
    c.audio_program=program;c.audio_entries=entries;c.audio_private_entries=private_entries

def ir_corpus(c):
    from verify_ir_processing import Comparison as ConstructorComparison,baseline as ir_baseline,CONSTRUCTION_REGIONS,OBJECT
    from verify_dsp_stage import baseline as stage_baseline
    previous=ConstructorComparison(Path(c.lib._name));rng=random.Random(331)
    c.constructed_cases=0
    for count in (1,129,513):
        fixture=ir_baseline([32767]+[0]*(count-1))
        original=previous.compare(fixture,'construct',count,CONSTRUCTION_REGIONS['produce'][0],OBJECT)
        c.cases+=1;c.constructed_cases+=1;c.visited|=original['visited'];c.steps+=original['steps']
        for accelerated in (0,1):
            memory=baseline(count);memory[0][:]=stage_baseline(count)[0];memory[2][:len(original['memory'][23])]=original['memory'][23]
            setword(memory,ARENA+548,accelerated);setword(memory,CONTROL+14,1,1);setword(memory,CONTROL+348,0,1)
            setword(memory,EFFECTS+288,ARENA);setword(memory,EFFECTS+292,count)
            for block in range(8):
                memory=list(map(bytearray,memory));wet,dry=((0x3f800000,0),(0x3f000000,0x3f000000),(0x40800000,0),(0x7fc00000,0))[block%4]
                setword(memory,EFFECTS+296,wet);setword(memory,EFFECTS+300,dry)
                for i in range(128):setword(memory,SAMPLES+4*i,rng.getrandbits(32))
                mutations=((-0xffff0002,0x01c34494,0xfffffffe,4),) if accelerated and block==3 else ()
                memory=c.compare(f'constructed IR stage {count}/{accelerated}/{block}',memory,'stage',(0,SAMPLES,128),mutations=mutations)
    c.constructed_program=previous.program

def boundary_corpus(c):
    for case in range(16):
        m=baseline();setword(m,EFFECTS+84,ARENA if case&1 else 0);setword(m,EFFECTS+7,(case>>1)&1,1)
        setword(m,EFFECTS+88,2021*16 if case&4 else 2021*16-1);setword(m,EFFECTS+92,ARENA+20000 if case&8 else 0)
        setword(m,ARENA+8192+40,case&8);setword(m,ARENA+20040,case&4)
        c.compare(f'capture probe {case}',m,'capture_probe',(EFFECTS,))
    for kind in range(40):
        for case in range(6):
            m=baseline();p=EFFECTS+288;setword(m,EFFECTS,kind,1);setword(m,EFFECTS+6,case%4,1);setword(m,EFFECTS+46,2,1)
            for off in (312,344,408,412,416,460,476):setword(m,EFFECTS+off,case&1)
            for off in (328,372,416,460):setword(m,EFFECTS+off,case&1,1)
            setword(m,EFFECTS+352,4135+case);setword(m,EFFECTS+76,case,2);setword(m,EFFECTS+82,case&1,2)
            setword(m,EFFECTS+84,ARENA);setword(m,EFFECTS+88,32768);setword(m,EFFECTS+472,(0,1,7,63,0xffffffff,8)[case]);setword(m,EFFECTS+464,65536 if case&1 else 0)
            setword(m,p,ARENA if case&1 else 0);setword(m,p+4,(0,1,127,128,4096,0xffffffff)[case]);setword(m,p+20,65536 if case&1 else 65535)
            setword(m,ARENA,case&2);setword(m,ARENA+548,case&1);setword(m,ARENA+8192+40,1);setword(m,ARENA+8192+12280,case&2)
            setword(m,0x01c1f7d0,case&2);setword(m,0x01c1fa14,case&1);setword(m,0x01c1f7d8,case&1)
            setword(m,EFFECTS+420,100 if case&1 else 50,1);setword(m,EFFECTS+421,case&2,1)
            c.compare(f'timing boundary cost {kind}/{case}',m,'cost',(EFFECTS,case&1))
            c.compare(f'timing boundary extra {kind}/{case}',m,'extra_cost',(EFFECTS,case&1,100 if case&1 else 50,1,1,1))
    for initial in (0,1,7,255):
        m=baseline();setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+44,initial,1);setword(m,EFFECTS+45,254,1)
        setword(m,EFFECTS+32,1234);setword(m,0x01c343d8,3456)
        for i in range(10):
            m=list(map(bytearray,m));setword(m,CONTROL+92,100 if i<7 else 1300)
            m=c.compare(f'warning carried {initial}/{i}',m,'warning',(EFFECTS,0,i&1))
    for kind in (5,27,30):
        for result in (0,2047,2048,0xffffffff):
            m=baseline();setword(m,EFFECTS,kind,1);setword(m,EFFECTS+8,0,2)
            c.compare(f'tail result {kind}/{result}',m,'dispatch',(EFFECTS,SAMPLES,16,0),returns=(result,))
    for kind in (11,12,15):
        for case in range(8):
            m=baseline(case);p=EFFECTS+288;setword(m,EFFECTS,kind,1);setword(m,EFFECTS+84,ARENA)
            setword(m,CONTROL+10,1,1);setword(m,CONTROL+9,65,1);setword(m,CONFIG+44,SAMPLES+2048);setword(m,CONFIG+20,100)
            for off,val in ((0,10),(4,1000),(12,2000),(32,33000),(36,case&1),(40,1),(44,4000),(48,5000),(52,98+case%3),(56,6000)):setword(m,p+off,val)
            c.compare(f'stereo delay postfilter {kind}/{case}',m,'dispatch',(EFFECTS,SAMPLES,(0,1,31,128)[case%4],1))
    for case in range(48):
        m=baseline(case);p=EFFECTS+288;setword(m,EFFECTS,25,1);setword(m,EFFECTS+84,ARENA)
        setword(m,CONTROL+10,1,1);setword(m,CONTROL+9,100,1);setword(m,CONTROL+40,1);setword(m,CONFIG+44,SAMPLES+2048);setword(m,CONFIG+20,100)
        for off,val in ((0,0),(4,(0,0x7fffffff,0x80000000,0xffffffff)[case%4]),(8,(-100,0,100)[case%3]),
            (16,100000),(20,500000),(24,500000),(28,500000),(32,1000000),(36,1000000),(48,30000),(52,32000),(56,30000),(60,32000)):
            setword(m,p+off,val)
        setword(m,EFFECTS+416,100 if case<24 else 99);setword(m,EFFECTS+420,100,1);setword(m,EFFECTS+421,case&1,1)
        setword(m,EFFECTS+424,(0,50,100)[case%3],1);setword(m,EFFECTS+425,case&1,1);setword(m,EFFECTS+426,0,1)
        if case>=24:
            setword(m,EFFECTS+404,1,1);setword(m,p+24,0);setword(m,p+28,(0,1,32768,0x80000000)[case%4]);setword(m,EFFECTS+400,0x3f800000)
        c.compare(f'dual descriptor transition {case}',m,'dispatch',(EFFECTS,SAMPLES,(16,31,128)[case%3],1))
    for case in range(10):
        m=baseline();p=ARENA+256;setword(m,EFFECTS,2,1);setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+2,1,1)
        setword(m,EFFECTS+5,1,1);setword(m,EFFECTS+7,case>=8,1);setword(m,EFFECTS+84,ARENA);setword(m,EFFECTS+88,128);setword(m,EFFECTS+288,65536)
        for j,magic in enumerate((0xc0de5eed,0xc0de5eec,0xc0de5eef,0xc0de5eee)):setword(m,p+j*4,magic^(1 if case==j else 0))
        c.compare(f'sentinel {case}',m,'individual',(0,SAMPLES,16),returns=(case&1,))
    for kind in (2,11,12,15,28,29,39):
        for case in range(4):
            m=baseline();setword(m,EFFECTS,kind,1);setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+2,1,1)
            setword(m,EFFECTS+10,3,1);setword(m,EFFECTS+11,case,1);setword(m,EFFECTS+84,ARENA);setword(m,EFFECTS+88,128);setword(m,EFFECTS+288,case)
            setword(m,0x01c34198,0x01c04862)
            c.compare(f'priming history {kind}/{case}',m,'individual',(0,SAMPLES,(0,1,16,128)[case]))
    for kind in (1,2,3,4,5,8,9,11,14,16,23,36,37,38,39):
        m=baseline();setword(m,EFFECTS,kind,1);setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+2,1,1)
        setword(m,CONTROL+316,1,1);setword(m,CONTROL+332,4,1);setword(m,AUTOMATION+4,4,1);setword(m,AUTOMATION+1,0,1)
        setword(m,AUTOMATION+3,1,1);setword(m,AUTOMATION+5,0,1);setword(m,AUTOMATION+45,1,1);setword(m,AUTOMATION+288,100)
        setword(m,EFFECTS+288,65536 if kind==2 else 0);setword(m,CONFIG+40,SAMPLES+2048);setword(m,CONFIG+44,SAMPLES+2048)
        c.compare(f'actual quarter automation {kind}',m,'individual',(0,SAMPLES,128))

def transition_corpus(c):
    def fixture(kind=2):
        m=baseline(kind);setword(m,EFFECTS,kind,1);setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+2,1,1)
        setword(m,CONFIG+40,SAMPLES+2048);setword(m,CONFIG+44,SAMPLES+2048);setword(m,CONFIG+20,100)
        if kind==2:setword(m,EFFECTS+288,65536);setword(m,EFFECTS+292,65536)
        return m
    for case in range(4):
        m=fixture(7);setword(m,EFFECTS+288,ARENA);setword(m,ARENA,1);setword(m,EFFECTS+292,case&1)
        c.compare(f'zero partition timing {case}',m,'cost',(EFFECTS,1))
        m=fixture(29);setword(m,EFFECTS+82,1,2);setword(m,0x01c1f7d8,case&1)
        c.compare(f'capture fallback timing {case}',m,'cost',(EFFECTS,1))
        m=fixture(3);setword(m,EFFECTS+312,0);setword(m,EFFECTS+6,case,1)
        c.compare(f'zero extra timing {case}',m,'cost',(EFFECTS,1))
    for kind in range(40):
        m=fixture(kind)
        c.compare(f'extra timing disabled mask {kind}',m,'extra_cost',(EFFECTS,1,100,1,1,0))
    for kind in (4,26):
        for residual in (0,1):
            for n in (0,1,32):
                m=fixture(kind)
                for j in range(3 if kind==4 else 4):
                    setword(m,EFFECTS+288+j*44,1<<28);setword(m,EFFECTS+328+j*44,1,1);setword(m,EFFECTS+329+j*44,residual,1)
                c.compare(f'filter cascade variants {kind}/{residual}/{n}',m,'dispatch',(EFFECTS,SAMPLES,n,1))
    for kind in (8,11,12,13,15):
        for n in (0,1,31,128):
            m=fixture(kind);setword(m,EFFECTS+84,ARENA);setword(m,EFFECTS+320,33000);setword(m,EFFECTS+324,100)
            setword(m,EFFECTS+308,65536 if kind==8 else 500);setword(m,EFFECTS+476,100)
            c.compare(f'mono postfilter and full wet {kind}/{n}',m,'dispatch',(EFFECTS,SAMPLES,n,1))
    for case in range(24):
        m=fixture(38);p=EFFECTS+288
        for off,value in ((16,case&1),(40,(0,256,65536,0x40000000)[case%4]),(48,0),(52,0),(56,1),
            (60,0),(64,0),(68,100000),(72,500000),(76,200000),(80,(0,2000,6000)[case%3]),
            (84,0),(88,65536),(92,-100000),(96,0),(100,0x40000000),(120,0),(124,0)):
            setword(m,p+off,value)
        for i in range(32):setword(m,SAMPLES+4*i,0)
        c.compare(f'envelope control limits {case}',m,'dispatch',(EFFECTS,SAMPLES,32,1))
    for case in range(32):
        m=fixture(25);p=EFFECTS+288;setword(m,EFFECTS+84,ARENA);setword(m,CONTROL+10,1,1)
        setword(m,CONTROL+9,10,1);setword(m,CONTROL+40,case&1)
        for off,value in ((4,0x80000000),(8,0),(16,100000),(20,100000),(24,100000),(28,100000),
            (32,100000),(36,100000),(48,65536),(52,32000),(56,65536),(60,32000)):
            setword(m,p+off,value)
        if case<8:setword(m,p+28,200000)
        setword(m,EFFECTS+416,(0,99,100,98)[case%4]);setword(m,EFFECTS+420,100,1)
        setword(m,EFFECTS+421,case%3,1);setword(m,EFFECTS+424,(0,50,100,99)[case%4],1)
        setword(m,EFFECTS+425,case%3,1);setword(m,EFFECTS+426,case%4,1)
        c.compare(f'dual stereo history and hold {case}',m,'dispatch',(EFFECTS,SAMPLES,32,1))
    for kind in (2,5,6,7,11,14,25,29,39):
        for case in range(12):
            m=fixture(kind);count=(0,1,16,128)[case%4]
            setword(m,EFFECTS+84,ARENA if kind in (11,25,29) else 0)
            setword(m,CONTROL+9,50,1);setword(m,CONTROL+268,64 if case&1 else 25,1);setword(m,CONTROL+284,64,1)
            setword(m,CONTROL+300,0 if case<8 else 50,1);setword(m,0x01c34488,1,1)
            setword(m,EFFECTS+10,(0,1,2)[case//4],1);setword(m,EFFECTS+11,case&3,1)
            if kind==25:setword(m,EFFECTS+420,50,1);setword(m,CONTROL+40,1);setword(m,EFFECTS+292,0x80000000)
            if kind in (5,11):
                setword(m,CONTROL+316,1,1);setword(m,CONTROL+332,1,1);setword(m,AUTOMATION+4,1,1)
                setword(m,AUTOMATION+1,0,1)
            c.compare(f'stereo transition {kind}/{case}',m,'individual',(0,SAMPLES,count))
    for kind in (2,5,6,7,11,25,29,39):
        for case in range(16):
            m=fixture(kind);setword(m,0x01c34198,0x01c04862);setword(m,CONTROL+96,100)
            setword(m,0x01c343d8,0 if case<8 else 5000);setword(m,0x01c34444,100000)
            setword(m,EFFECTS+12,2,1);setword(m,EFFECTS+13,0,1);setword(m,EFFECTS+36,100)
            setword(m,EFFECTS+1,case&1,1);setword(m,EFFECTS+8,1500,2);setword(m,CONTROL+3,case&2,1)
            setword(m,CONFIG,50,1);setword(m,CONTROL+36,1);setword(m,CONTROL+40,1);setword(m,CONTROL+44,1)
            if kind==25:setword(m,EFFECTS+84,ARENA);setword(m,EFFECTS+292,0x80000000)
            c.compare(f'deadline retry resume {kind}/{case}',m,'individual',(0,SAMPLES,16),clocks=(300,500))
    for kind in (2,5,6,14):
        for case in range(24):
            m=fixture(kind);setword(m,0x01c34198,0x01c04862);setword(m,CONTROL+96,100)
            setword(m,0x01c343d8,5000);setword(m,0x01c34444,5100-100);setword(m,EFFECTS+12,1,1)
            setword(m,EFFECTS+10,case%3,1);setword(m,EFFECTS+11,case%4,1);setword(m,0x01c34488,1,1)
            setword(m,CONTROL+9,50,1);setword(m,CONTROL+268,64 if case&1 else 0,1);setword(m,CONTROL+284,64 if case&1 else 0,1)
            setword(m,CONTROL+300,50,1)
            if case>=12:setword(m,EFFECTS+11,255,1)
            for i in range(32):setword(m,SAMPLES+4*i,0x80000000 if case&1 else 0x7fffffff);setword(m,SAMPLES+2048+4*i,0x7fffffff if case&1 else 0x80000000)
            if kind==2:setword(m,EFFECTS+288,0x7fffffff);setword(m,EFFECTS+292,0x7fffffff)
            c.compare(f'overrun stereo crossfade {kind}/{case}',m,'individual',(0,SAMPLES,32),clocks=(200,))
    for enabled in (0,1):
        for auxiliary in (0,1):
            m=fixture(5);setword(m,EFFECTS+1,enabled,1);setword(m,EFFECTS+10,1,1);setword(m,EFFECTS+11,0,1)
            setword(m,EFFECTS+12,3,1);setword(m,EFFECTS+13,2,1);setword(m,EFFECTS+8,1500,2)
            setword(m,CONTROL+9,64,1);setword(m,CONTROL+268,64,1);setword(m,CONTROL+284,64,1)
            setword(m,CONTROL+300,auxiliary*50,1)
            c.compare(f'restore secondary history {enabled}/{auxiliary}',m,'individual',(0,SAMPLES,16))
    for enabled in (0,1):
        m=fixture(27);setword(m,EFFECTS+1,enabled,1);setword(m,EFFECTS+8,1500,2);setword(m,EFFECTS+10,5,1)
        c.compare(f'tail auxiliary publication {enabled}',m,'individual',(0,SAMPLES,16))
    for partitions in (1,32):
        m=fixture(7);setword(m,0x01c34198,0x01c04862);setword(m,EFFECTS+12,2,1);setword(m,EFFECTS+13,32,1)
        setword(m,EFFECTS+288,ARENA);setword(m,ARENA,1);setword(m,ARENA+4,partitions)
        setword(m,ARENA+24,ARENA+1024);setword(m,ARENA+48,ARENA+40000)
        for i in range(partitions*258):setword(m,ARENA+1024+4*i,0x12345678+i)
        for i in range(256):setword(m,ARENA+40000+4*i,0x89abcdef-i)
        for block in range(3):
            m=c.compare(f'actual guarded IR reset {partitions}/{block}',m,'individual',(0,SAMPLES,128),clocks=(500,))
    for case in range(8):
        m=fixture();setword(m,ARENA,0x020100)
        for slot in range(3):
            p=EFFECTS+480*slot;setword(m,p,2,1);setword(m,p+1,1,1);setword(m,p+2,1,1)
            setword(m,p+6,1,1);setword(m,p+288,65536);setword(m,p+292,65000);setword(m,p+46,(case+slot)%3,1)
            setword(m,0x01c343d8+slot*4,5000)
        setword(m,0x01c34198,0x01c04862);setword(m,0x01c34444,1000000);setword(m,CONTROL+96,100)
        mutations=((1,ARENA+1,2,1),(1,ARENA+2,1,1),(1,CONTROL+124,123,4),(1,CONTROL+128,1 if case&2 else 456,4),
            (2,EFFECTS+480+1,0,1),(2,EFFECTS+960+12,case%4,1))
        if case&1:mutations+=((1,0x01c34198,0,4),)
        c.compare(f'group clock callback mutation {case}',m,'grouped',(ARENA,3,SAMPLES,32),mutations=mutations,clocks=(200,300,400,500,600))
    for case in range(64):
        m=fixture();setword(m,ARENA,0x020100);n=(0,1,31,32)[case%4]
        length=(0,1,3,3)[case%4];active_count=(case//4)%4
        for slot in range(3):
            p=EFFECTS+480*slot;setword(m,p,2,1);setword(m,p+1,slot<active_count,1);setword(m,p+2,1,1)
            setword(m,p+6,1,1);setword(m,p+288,65536);setword(m,p+292,65000)
            setword(m,p+46,(case+slot)%3,1);setword(m,0x01c343d8+4*slot,100 if case&1 else 50000)
            if case>=48:setword(m,p+12,2,1);setword(m,p+13,2,1);setword(m,p+8,2,2)
        setword(m,EFFECTS+47,3,1);setword(m,0x01c34198,0x01c04862);setword(m,CONTROL+96,100)
        setword(m,0x01c34444,100000 if case&2 else 100);setword(m,CONTROL+124,10000 if case&4 else 0)
        setword(m,CONTROL+128,10000 if case&8 else 0)
        c.compare(f'group timing transitions {case}',m,'grouped',(ARENA,length,SAMPLES,n),clocks=(200,300,400,500,600))
    for kind in (8,38):
        for value in (1,127,255):
            m=fixture(kind);p=EFFECTS+288;setword(m,p+(24 if kind==8 else 40),value)
            if kind==38:setword(m,p+120,127);setword(m,p+124,126);setword(m,p+16,1)
            c.compare(f'small logarithm and approach {kind}/{value}',m,'dispatch',(EFFECTS,SAMPLES,16,1))
    m=fixture();setword(m,CONTROL+10,3,1);setword(m,0x01c2e020+84,99)
    c.compare('previous frame stereo cache',m,'dispatch',(EFFECTS,SAMPLES,16,1))
    for n in (128,256):
        m=fixture(25);setword(m,EFFECTS+84,ARENA);setword(m,EFFECTS+292,0x80000000);setword(m,CONTROL+10,1,1)
        setword(m,EFFECTS+320,124518400);setword(m,EFFECTS+324,124518400);setword(m,EFFECTS+412,1000000)
        setword(m,EFFECTS+416,99);setword(m,EFFECTS+420,50,1);setword(m,EFFECTS+421,1,1);setword(m,EFFECTS+425,1,1)
        setword(m,EFFECTS+424,50,1);setword(m,CONTROL+40,1);setword(m,CONTROL+9,100,1)
        c.compare(f'dual large count and offset reflection {n}',m,'dispatch',(EFFECTS,SAMPLES,n,1))
    m=fixture();setword(m,EFFECTS+1,0,1);setword(m,EFFECTS+10,2,1);setword(m,EFFECTS+12,2,1)
    setword(m,0x01c34198,0x01c04862)
    c.compare('disabled retry clears transition',m,'individual',(0,SAMPLES,16))
    for phase in (1,2):
        for counter in (0,4,127,255):
            m=fixture(6);setword(m,EFFECTS+10,phase,1);setword(m,EFFECTS+11,counter,1);setword(m,0x01c34488,1,1)
            for i in range(16):setword(m,SAMPLES+4*i,0x7fffffff);setword(m,SAMPLES+2048+4*i,0x80000000)
            c.compare(f'wrapped normal fade saturation {phase}/{counter}',m,'individual',(0,SAMPLES,16))

def api_checks(c):
    n=0;memory=baseline();setword(memory,EFFECTS,2,1);setword(memory,EFFECTS+288,65536)
    def check(expected,entry=REGIONS['dispatch'][0],args=(EFFECTS,SAMPLES,16,1),data=None,mapper=None,call=True,odd_storage=None):
        nonlocal n
        b=CBackend(c.program,data or memory,Script());result=U32(0x1234)
        if mapper is not None:b.io.map=MAP(mapper)
        if odd_storage is not None:
            def misaligned(_o,address,size,writable):
                value=b.map(_o,address,size,writable)
                return value+1 if value is not None and odd_storage[0]<=address<odd_storage[1] else value
            b.io.map=MAP(misaligned)
        if not call:b.io.call=CALL()
        status=c.lib.hyperrig_effect_processing_execute(entry,(U32*12)(*args),ctypes.byref(result),ctypes.byref(b.io))
        assert status==expected,(hex(entry),args,status,expected);n+=1
    check(-202,0);check(-202,args=(EFFECTS,SAMPLES,513,1));check(-202,args=(EFFECTS,SAMPLES+1,16,1))
    check(-202,odd_storage=(SAMPLES,SAMPLES+4096))
    check(-201,mapper=lambda *_:None)
    check(-202,REGIONS['individual'][0],(16,SAMPLES,128));check(-202,REGIONS['grouped'][0],(ARENA,17,SAMPLES,16))
    m=baseline();setword(m,EFFECTS,4,1);setword(m,EFFECTS+328,1,1);check(-202,args=(EFFECTS,SAMPLES+1,16,1),data=m)
    check(-202,data=m,odd_storage=(EFFECTS+288,EFFECTS+328))
    check(-202,args=(EFFECTS,SAMPLES+2,16,1),data=m)
    m=baseline();setword(m,EFFECTS+1,4,1);setword(m,EFFECTS+329,1,1);check(-202,args=(EFFECTS+1,SAMPLES,16,1),data=m)
    m=baseline();setword(m,EFFECTS,5,1);check(-200,data=m,call=False)
    m=baseline();setword(m,EFFECTS,2,1);setword(m,EFFECTS+1,1,1);setword(m,EFFECTS+2,1,1);setword(m,0x01c34198,0x1234)
    check(-202,REGIONS['individual'][0],(0,SAMPLES,16),data=m)
    m=baseline();setword(m,EFFECTS,7,1);setword(m,EFFECTS+288,ARENA);setword(m,ARENA,1);setword(m,ARENA+4,33)
    check(-202,args=(EFFECTS,SAMPLES,128,1),data=m)
    m=baseline();setword(m,AUTOMATION+3,41,1);check(-202,REGIONS['automation'][0],(AUTOMATION,EFFECTS+288,0),data=m)
    b=CBackend(c.program,memory,Script());value=U32();args=(U32*12)()
    for argument,result,io in ((None,ctypes.byref(value),ctypes.byref(b.io)),(args,None,ctypes.byref(b.io)),(args,ctypes.byref(value),None)):
        assert c.lib.hyperrig_effect_processing_execute(REGIONS['dispatch'][0],argument,result,io)==-200;n+=1
    return n

def source_paths():
    from verify_dsp_stage import source_paths as old_paths
    paths=set(old_paths())|set(SOURCES)|{'tools/effect_processing_machine.py','tools/verify_effect_processing.py','tools/build_effect_processing.py',
        'tests/test_effect_processing_machine.py','tests/effect_processing_sanitize.c','upstream/pi32v2-isa/isa/pi32v2.toml'}
    pending=[ROOT/p for p in paths if p.endswith(('.c','.h'))];seen=set()
    while pending:
        path=pending.pop().resolve()
        if path in seen:continue
        seen.add(path)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',path.read_text(),re.M):
            for header in (path.parent/name,ROOT/'firmware/include'/name):
                if header.is_file():paths.add(header.resolve().relative_to(ROOT).as_posix());pending.append(header);break
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
    return sorted(paths)

def report(c,args,sources):
    from effect_processing_machine import TABLES,SERVICES
    from audio_task_machine import SERVICES as AUDIO_SERVICES
    from dsp_audio_path_machine import TABLE,PRIOR_TABLE,RESET_CONFIGURATION
    app=c.program.app;code=dict(c.program.code)
    for other in (getattr(c,'audio_program',None),getattr(c,'constructed_program',None)):
        if other:code.update(other.code)
    new={pc for pc in code if any(start<=pc<end for start,end in REGIONS.values()) and not any(start<=pc<end for start,end in TABLES.values())}
    inherited={'capture_dispatch':(0x01c12bf2,0x01c12bf6),'gain_table':TABLE,'coefficient_selector':(PRIOR_TABLE,PRIOR_TABLE+10),
        'reset_configuration':RESET_CONFIGURATION,'task_registration':(0x02005250,0x0200525e),'resampling_taps':(0x0203be2c,0x0203be50)}
    def binding(start,end):return {'start':start,'end_exclusive':end,'sha256':hashlib.sha256(app[offset(start):offset(end)]).hexdigest()}
    static={name:binding(*bounds) for name,bounds in (dict(STATIC)|inherited).items()}
    windows={hex(pc):binding(pc,pc+record[1]) for pc,record in sorted(code.items())}
    mini=None
    if args.mini_image:
        from hyperrig.jieli import unpack_app
        raw=args.mini_image.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        mini_app=unpack_app(raw)[2]['app.bin']
        for item in (*static.values(),*windows.values()):
            start,end=item['start'],item['end_exclusive'];assert mini_app[offset(start):offset(end)]==app[offset(start):offset(end)],hex(start)
        mini={'image_sha256':sha,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    original_raw=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    original=hashlib.sha256(original_raw).hexdigest()
    assert original=='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    from hyperrig.jieli import unpack_app
    assert unpack_app(original_raw)[2]['app.bin']==app,'decoded input differs from pinned original image'
    missing=new-c.visited
    invariant_gaps={
        'The declared type range is 0..39. Types 0..4 have capability 0 or 3 in both immutable table fields, so they return before the type-5 dispatch; types 5..39 cannot take its out-of-range edge.':[0x01c05ce4,0x01c05ce6,0x01c05ce8],
        'The type38 outer loop begins only for positive remaining count and advances by32; its bounded inner count cannot be zero at the peak scan.':[0x01c0e816],
        'The stereo setup block is entered only with a positive selected mode1,2 or3; its saved mode is reloaded without an intervening service or aliased write before the nonpositive fallback.':[0x01c0fcac],
    }
    classified={pc for group in invariant_gaps.values() for pc in group}
    result={'schema':1,'project':'HyperRig','component':'reconstructed-effect-processing','result':'pass',
        'original_image_sha256':original,'decoded_image_sha256':hashlib.sha256(app).hexdigest(),
        'total_comparisons':c.cases,'original_instruction_steps':c.steps,'c_only_guard_checks':api_checks(c),
        'sanitizer_replay_cases':c.replay.count if c.replay else 0,'source_sha256':sources,
        'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),'mini_v4_binding':mini,
        'outputs_state_and_ordered_services_sha256':c.digest.hexdigest(),'standalone_original_entries':{hex(p):n for p,n in sorted(c.real_calls.items())},
        'actual_audio_dispatch_entries':getattr(c,'audio_entries',0),'actual_audio_private_descriptor_entries':getattr(c,'audio_private_entries',0),
        'actual_constructor_comparisons':getattr(c,'constructed_cases',0),
        'functions':{name:binding(start,end)|{'instructions':sum(start<=pc<end for pc in new),
            'visited':sum(start<=pc<end for pc in c.visited),'unvisited':sorted(pc for pc in new-c.visited if start<=pc<end)} for name,(start,end) in REGIONS.items()},
        'static_data':static,'bound_instruction_windows':windows,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':sorted(new-c.visited),
            'all_decoded':len(code),'all_visited':len(set(code)&c.visited),'unvisited_all':sorted(set(code)-c.visited),
            'unvisited_by_entry_invariant':{reason:[pc for pc in addresses if pc in missing] for reason,addresses in invariant_gaps.items()},
            'unclassified_unvisited':sorted(missing-classified),
            'note':'Only actual execution in this corpus is counted; inherited prior-report coverage is not added.'},
        'external_effect_services':{hex(p):n for p,n in SERVICES.items()},
        'inherited_audio_services':{hex(p):n for p,n in AUDIO_SERVICES.items() if p not in code},
        'scripted_recovered_kernel_replacements':0,'synthetic_mmio_operation_tokens':{'read':0xffff0000,'write':0xffff0001,'sync':0xffff0002},
        'constructor_fixture_handoff':['The actual original and C constructors agree before the resulting object bytes are carried into the shared arena.',
            'The corpus publishes the resulting object token in effect+288 and writes the accelerator selector; the enclosing installation/enable caller is not executed here.'],
        'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['Effect-specific numerical leaves remain explicit synchronous services, including their audited stack arguments and temporary descriptors.',
            'MMIO scripts exercise software sequencing only; they are not physical accelerator results.',
            'Loaded but unvisited code and all new unvisited instructions remain explicitly listed.',
            'Borrowed typed Q28/ramp storage must have aligned tokens and compatible C types; callbacks preserve structural IR layout and platform contracts.']}
    assert sources=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'sources changed during comparison'
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--development-rebuild',action='store_true');parser.add_argument('--suite',default='all');parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--output',type=Path);parser.add_argument('--mini-image',type=Path);parser.add_argument('--sanitizer-corpus',type=Path)
    args=parser.parse_args()
    if args.development_rebuild:
        if args.library.parent.name!='reverse-effect-processing-development-01':parser.error('development rebuild is restricted to the unfrozen development directory')
        subprocess.run(['gcc','-std=c11','-O2','-g','-shared','-fPIC','-Ifirmware/include',*SOURCES,'-o',str(args.library)],check=True)
    if args.output and args.output.exists():parser.error('choose a fresh report path')
    if args.sanitizer_corpus and args.sanitizer_corpus.exists():parser.error('choose a fresh replay path')
    c=Corpus(args.library,args.sanitizer_corpus)
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths()} if args.output else {}
    if args.suite=='helpers':helper_corpus(c)
    elif args.suite=='dispatch':dispatch_corpus(c,args.start)
    elif args.suite=='numerical':numerical_dispatch_corpus(c,args.start)
    elif args.suite=='stage':stage_corpus(c)
    elif args.suite=='timing':timing_corpus(c)
    elif args.suite=='audio':audio_corpus(c)
    elif args.suite=='ir':ir_corpus(c)
    elif args.suite=='boundaries':boundary_corpus(c)
    elif args.suite=='transitions':transition_corpus(c)
    elif args.suite=='wrappers':wrapper_corpus(c)
    elif args.suite=='all':
        for suite in (helper_corpus,dispatch_corpus,wrapper_corpus,numerical_dispatch_corpus,timing_corpus,boundary_corpus,transition_corpus,stage_corpus,audio_corpus,ir_corpus):
            suite(c);print(f'{suite.__name__}: {c.cases} comparisons passed.',flush=True)
    else:parser.error('unknown suite')
    if c.replay:c.replay.close()
    if args.output:
        result=report(c,args,sources);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result['instruction_coverage']|{'unvisited_all':len(result['instruction_coverage']['unvisited_all'])}))
    else:print(json.dumps({'result':'pass','comparisons':c.cases,'steps':c.steps,'visited':len(c.visited),'digest':c.digest.hexdigest()}))
if __name__=='__main__':main()
