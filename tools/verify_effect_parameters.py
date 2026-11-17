"""Compare complete parameter callers, producer state and joined scene/stage execution."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import re
import struct
import sys
from pathlib import Path
from effect_parameters_machine import (EffectParametersProgram, REGIONS, REUSED, ENTRY_POINTS,
    ARITIES, MAPPED, RAM, SAMPLES, ARENA, ROOT, PRIVATE, ALLOCATE, region_bytes)
from verify_dsp_stage import SOURCES as STAGE_SOURCES
from build_ir_processing import SOURCES as IR_SOURCES
from build_scene_application import C_NAMES as SCENE_SOURCES

SOURCES=tuple(dict.fromkeys((*(f'firmware/src/hyperrig_{name}.c' for name in STAGE_SOURCES),*IR_SOURCES,
    'firmware/src/hyperrig_effect_resampling.c','firmware/src/hyperrig_effect_enable.c',
    'firmware/src/hyperrig_effect_processing.c',
    *(f'firmware/src/hyperrig_{name}.c' for name in SCENE_SOURCES),
    'firmware/src/hyperrig_effect_parameter_support.c','firmware/src/hyperrig_effect_parameters.c')))
EFFECTS,CONTROL,CONFIG,AUTOMATION=0x01c2c220,0x01c32db0,0x01c1f7f0,0x01c2e5a0
PROPOSED,PREVIOUS=0x01c33610,0x01c337f0
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),('services',U32),('work',U32)]

def put(data,offset,value,size=4):data[offset:offset+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little')
def setword(memory,address,value,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:put(data,address-base,value,size);return
    raise ValueError(f'fixture address outside native map {address:#x}')
def initial(type_=0,seed=1):
    memory=[bytearray(n) for _,n in MAPPED]
    memory[2][:]=bytes([0x5a])*len(memory[2])
    rng=random.Random(seed)
    for i in range(128):put(memory[1],4*i,rng.getrandbits(32))
    for address,value,width in ((EFFECTS,type_,1),(EFFECTS+1,1,1),(EFFECTS+2,1,1),
        (CONFIG+8,48000,4),(CONFIG+12,120,4),(CONTROL+48,100000,4),
        (0x01c34468,0xfffffffe,4),(0x01c343d8,0xcafebabe,4)):
        setword(memory,address,value,width)
    for i in range(6):setword(memory,CONTROL+180+i,255,1)
    return memory

class Script:
    """Explicit external effects; derived words are supplied, not claimed reconstructed."""
    def __init__(self,plan=None,mutations=()):
        self.plan=plan or {};self.mutations=mutations;self.seen={};self.responses=[]
    def __call__(self,target,args,m):
        occurrence=self.seen.get(target,0);self.seen[target]=occurrence+1
        if target==ALLOCATE and args[2]==PRIVATE:m.write(PRIVATE,self.plan.get('released',0),4)
        if target==0x0202cf62:
            for index,value in self.plan.get('derived',()):m.write(args[0]+288+4*index,value,4)
        if target==0x0202eefa:
            value=2166136261
            for i in range(14):value=((value^m.read(args[0]+70+i,1))*16777619)&0xffffffff
        elif target==0x0202f014:value=128
        elif target==0x0202f02e:value=self.plan.get('ir_length',128)
        elif target==0x02028cb2:value=1000
        elif target==0x02028de8:value=1000
        elif target==0x01c04862:value=123456+137*sum(self.seen.values())
        else:value=0
        override=self.plan.get(target)
        if override is not None:value=override[min(occurrence,len(override)-1)] if isinstance(override,(tuple,list)) else override
        for at,n,address,replacement,width in self.mutations:
            if at==target and (n<0 or n==occurrence):m.write(address,replacement,width)
        value&=0xffffffff;self.responses.append(value);return value

class Backend:
    def __init__(self,program,memory,script):
        self.arrays=[(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for data in memory]
        self.tables={name:(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for name,data in program.data.items()}
        self.static=program.static_regions;self.script=script;self.calls=[];self.errors=[];self.borrowed=None
        self.sites=[];self.io=IO(MAP(self.map),CALL(self.call),None,100000,1000000)
    def map(self,opaque,address,size,writable):
        for (base,n),data in zip(MAPPED,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(data)+address-base
        if not writable:
            for name,(base,end) in self.static.items():
                if base<=address<=address+size<=end:return ctypes.addressof(self.tables[name])+address-base
        return None
    def snapshot(self):return tuple(bytes(data) for data in self.arrays)
    def locate(self,address,size,writable):
        pointer=self.map(None,address,size,writable)
        if pointer is None and self.borrowed:
            pointer=self.borrowed.contents.map(self.borrowed.contents.opaque,address,size,writable)
        if pointer is None:raise ValueError(f'callback address unmapped {address:#x}/{size}')
        return pointer
    def read(self,address,size):return int.from_bytes(ctypes.string_at(self.locate(address,size,0),size),'little')
    def write(self,address,value,size):
        ctypes.memmove(self.locate(address,size,1),(value&((1<<(8*size))-1)).to_bytes(size,'little'),size)
    def call(self,opaque,target,arguments,count,borrowed):
        try:
            args=tuple(arguments[i] for i in range(count))+(0,)*(12-count)
            before=self.snapshot();self.borrowed=borrowed
            result=self.script(target,args,self);private=()
            if target==ALLOCATE and count==3:private=((PRIVATE,ctypes.string_at(self.locate(PRIVATE,4,0),4)),)
            self.calls.append((target,args,before,self.snapshot(),(),private));self.sites.append((target,count))
            self.borrowed=None;return result
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectParametersProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        self.lib.hyperrig_effect_parameters_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_scene.argtypes=[U32,U32,ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.replay=replay;self.replays=0;self.counts={};self.steps=0;self.coverage=set();self.real_calls={}
        self.services={};self.carried=0;self.mutating=0;self.digest=hashlib.sha256();self.private=0
    def compare(self,label,memory,name,args,plan=None,mutations=(),carried=False,argument_address=None):
        script=Script(plan,mutations)
        try:native=self.program.execute(memory,name,args,boundary=script)
        except Exception as exc:raise AssertionError(f'{label}: original execution {exc}') from exc
        c=Backend(self.program,memory,Script(plan,mutations));result=(U32*2)(0xdeadbeef,0xdeadbeef)
        entry=ENTRY_POINTS[name]
        if name=='stage':status=self.lib.hyperrig_effect_parameters_stage(*args,ctypes.byref(c.io));result[:]=[0,0]
        elif name.startswith('scene_'):
            status=self.lib.hyperrig_effect_parameters_scene(entry,args[0] if args else 0,result,ctypes.byref(c.io));result[1]=0
        else:
            arguments=ctypes.cast(c.locate(argument_address,48,0),ctypes.POINTER(U32)) if argument_address is not None else (U32*12)(*args)
            status=self.lib.hyperrig_effect_parameters_execute(entry,arguments,result,ctypes.byref(c.io))
        if status or c.errors:raise AssertionError((label,'C status',status,c.errors))
        scalar=name not in ('stage','scene_select','scene_flush')
        if result[1] or (scalar and result[0]!=native['value']):
            raise AssertionError((label,'result',hex(result[0]),hex(native['value'])))
        if c.snapshot()!=native['memory']:
            changes=[(hex(base+i),x,y) for (base,_),left,right in zip(MAPPED,native['memory'],c.snapshot())
                     for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            raise AssertionError((label,'memory native/C',changes[:24]))
        if c.calls!=native['calls']:
            brief=lambda calls:[(hex(t),tuple(hex(x) for x in args[:6]),hashlib.sha256(b''.join(before)).hexdigest()[:12],
                hashlib.sha256(b''.join(after)).hexdigest()[:12],p0,p1) for t,args,before,after,p0,p1 in calls]
            raise AssertionError((label,'call trace',brief(native['calls']),brief(c.calls)))
        if c.sites!=[(target,count) for _,target,count in native['service_sites']]:
            raise AssertionError((label,'call arity',c.sites,native['service_sites']))
        self.counts[name]=self.counts.get(name,0)+1;self.steps+=native['steps'];self.coverage|=native['visited']
        self.carried+=bool(carried);self.mutating+=bool(mutations);self.private+=len(native['private_events'])
        for target in native['real_calls']:self.real_calls[target]=self.real_calls.get(target,0)+1
        for target,*_ in native['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<I',result[0]))
        for data in native['memory']:self.digest.update(data)
        for target,arguments,before,after,private_before,private_after in native['calls']:
            self.digest.update(struct.pack('<13I',target,*arguments))
            for data in (*before,*after):self.digest.update(data)
            for address,data in (*private_before,*private_after):self.digest.update(struct.pack('<I',address));self.digest.update(data)
        if self.replay and name not in ('section_kind','word_kind','auxiliary_index'):
            self.write_replay(memory,name,args,native,script.responses,scalar,argument_address);self.replays+=1
        return native['memory']
    def write_replay(self,memory,name,args,native,responses,scalar,argument_address):
        # The replay records actual service mutations, never a second construction model.
        stream=self.replay
        stream.write(struct.pack('<18I',ENTRY_POINTS[name],*(tuple(args)+(0,)*(12-len(args))),int(scalar),
            native['value'] if scalar else 0,len(native['calls']),len(self.program.static_regions),argument_address or 0))
        for data in memory:stream.write(data)
        for key,(start,end) in self.program.static_regions.items():
            stream.write(struct.pack('<2I',start,end-start));stream.write(self.program.data[key])
        for (_,_,arity),call,value in zip(native['service_sites'],native['calls'],responses):
            target,arguments,before,after,_,private=call;changes=[]
            for (base,_),a,b in zip(MAPPED,before,after):
                changes.extend((base+i,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y)
            for base,data in private:changes.extend((base+i,x) for i,x in enumerate(data))
            stream.write(struct.pack('<16I',target,arity,*arguments,value,len(changes)))
            for address,replacement in changes:stream.write(struct.pack('<IB',address,replacement))
        for data in native['memory']:stream.write(data)

def classifiers(c):
    memory=initial()
    for first in (0,1,11,22,32,0xfffffffb,0xfffffff6,0xffffffff):
        for index in (0,1,4,10,11,32,0xffffffff,first,(first+4)&0xffffffff,(first+10)&0xffffffff):
            c.compare(f'section {first}/{index}',memory,'section_kind',(index,first))
    for type_ in (*range(40),0xffffffff):
        for index in (*range(49),0x80000000,0xfffffffc,0xffffffff):
            c.compare(f'kind {type_}/{index}',memory,'word_kind',(type_,index))
        for index in (0,1,3,4,15,16,39,0xffffffff):
            c.compare(f'auxiliary {type_}/{index}',memory,'auxiliary_index',(type_,index))

def basic(c):
    for name in ('commit','fast','fast_wrapper','probe'):
        for slot in (0,15,16,0x80000000,0xffffffff):
            args=(slot,0,1)+( (5,) if name in ('fast','fast_wrapper') else ())
            c.compare(f'invalid {name}/{slot}',initial(),name,args)
    for type_ in range(40):
        for index in (*range(7),7,0xffffffff):
            memory=initial(type_)
            for name in ('commit','fast','probe'):
                args=(0,index,1)+((5,) if name=='fast' else ())
                c.compare(f'basic {name}/{type_}/{index}',memory,name,args)

def limits(c):
    metadata=c.program.data['parameter_metadata']
    for type_ in range(1,40):
        for index in range(7):
            low,high=struct.unpack_from('<hh',metadata,type_*84+index*12)
            for value in (0x80000000,0x7fffffff,(low-1)&0xffffffff,(high+1)&0xffffffff):
                c.compare(f'clamp {type_}/{index}/{value}',initial(type_),'commit',(0,index,value))
    for tempo in range(10):
        for rate in (0,120,0xffffffff):
            memory=initial(5);setword(memory,CONFIG+12,rate);setword(memory,EFFECTS+78,tempo,2)
            for name,args in (('commit',(0,4,tempo)),('fast',(0,0,50,7)),('fast',(0,4,tempo,7))):
                c.compare(f'tempo {name}/{args}/{rate}',memory,name,args,{'derived':[(26,17),(27,31),(28,13)]})

def allocation(c):
    for released in (0,1):
        for success in (0,1):
            for old_count in (0,16,65,96):
                memory=initial(5);setword(memory,EFFECTS+84,ARENA);setword(memory,EFFECTS+88,64)
                setword(memory,EFFECTS+324,old_count);setword(memory,CONTROL+56,0x12345678)
                plan={'released':released,ALLOCATE:ARENA+32768 if success else 0}
                c.compare(f'allocation {released}/{success}/{old_count}',memory,'commit',(0,0,100),plan)
    for rate in (0,1,48000,0xffffffff):
        memory=initial(5);setword(memory,CONFIG+8,rate)
        for off,value in ((84,ARENA),(88,1),(324,0xffffffff)):setword(memory,EFFECTS+off,value)
        c.compare(f'allocation failure rate {rate}',memory,'commit',(0,0,100),{'released':1})
    for slot_type in (7,29,37):
        index=3 if slot_type==7 else 6
        for active in (0,1):
            for flag in (0,1):
                for return_ in (0,0xfffffffd):
                    memory=initial(slot_type);setword(memory,EFFECTS+1,active,1)
                    for off,value in ((84,ARENA),(88,100),(92,ARENA+32768),(288,ARENA+65536),(292,64)):
                        setword(memory,EFFECTS+off,value)
                    setword(memory,EFFECTS+7,flag,1);setword(memory,EFFECTS+369,255,1)
                    c.compare(f'resource {slot_type}/{active}/{flag}/{return_}',memory,'commit',(0,index,2),
                        {0x0202eeba:return_,0x0202983a:return_})

def automation(c):
    edges=(0,1,0xffffffff,0x7fffffff,0x80000000,0x3f800000,0xbf800000,0x7fc12345)
    for type_ in range(1,40):
        for duration in (0,1,2,5,255,256,0xffffffff):
            memory=initial(type_)
            changes=tuple((i,edges[(i+type_)%len(edges)]) for i in range(8))
            c.compare(f'automation {type_}/{duration}',memory,'fast_wrapper',(0,0,12,duration),{'derived':changes})
    for length in (0,1,39,40,41,48):
        c.compare(f'changed capacity {length}',initial(1),'fast',(0,0,0,3),{'derived':[(i,i+1) for i in range(length)]})
    for record in range(8):
        for progress in (0,1):
            memory=initial(5)
            for i in range(8):
                setword(memory,CONTROL+210+i,1,1);setword(memory,AUTOMATION+448*i+1,i+1,1)
            p=AUTOMATION+448*record
            for address,value,width in ((p+1,0,1),(p+2,progress,1),(p+3,3,1),(p+45,7,1),(p+4,255,1)):
                setword(memory,address,value,width)
            c.compare(f'reuse record {record}/{progress}',memory,'fast',(0,1,50,9),{'derived':[(26,17),(27,31),(28,13)]})
    memory=initial(2)
    for i in range(12):
        memory=c.compare(f'carried producer {i}',memory,'fast',(0,0,i%24,2+i),{'derived':[(0,0x7fffffff-i*1777)]},carried=i>0)

def probes(c):
    for type_ in (5,11,14,15,25):
        for index in range(7):
            for value in (0,1,2,0xffffffff):
                memory=initial(type_)
                setword(memory,CONFIG,100,1);setword(memory,CONTROL+40,0xffff)
                setword(memory,CONTROL+36,0xffff);setword(memory,CONTROL+44,0xffff)
                setword(memory,CONTROL+48,6000)
                c.compare(f'probe {type_}/{index}/{value}',memory,'probe',(0,index,value))

def mutation_cases(c):
    memory=initial(14);arguments=(0,4,1,2)
    for i,value in enumerate(arguments+(0,)*8):setword(memory,ARENA+4*i,value)
    c.compare('mutable argument storage retains native input registers',memory,'fast_wrapper',arguments,
        mutations=((0x0202eefa,0,ARENA+4,0,4),),argument_address=ARENA)
    for type_,index in ((1,0),(5,0),(5,4),(7,3),(14,3),(25,4),(29,6),(37,6),(39,3)):
        for target in (0x0202eefa,0x0202cf62,0x02028cb2,0x02028de8):
            for ordinal in (0,1):
                memory=initial(type_)
                changes=((target,ordinal,EFFECTS+70+2*index,7,2),
                    (target,ordinal,CONTROL+48,1200,4),
                    (target,ordinal,EFFECTS+1,1,1))
                c.compare(f'mutation commit {type_}/{target}/{ordinal}',memory,'commit',(0,index,2),mutations=changes)
                c.compare(f'mutation fast {type_}/{target}/{ordinal}',memory,'fast',(0,index,2,7),
                    {'derived':[(0,0x7fffffff),(1,0x80000000),(26,0x3f800000)]},changes)
                c.compare(f'mutation probe {type_}/{target}/{ordinal}',memory,'probe',(0,index,2),mutations=changes)
    for released in (0,1):
        for success in (0,1):
            memory=initial(5)
            for off,value in ((84,ARENA),(88,64),(324,32)):setword(memory,EFFECTS+off,value)
            plan={'released':released,ALLOCATE:ARENA+32768 if success else 0}
            changes=((ALLOCATE,0,EFFECTS+84,ARENA+4096,4),
                (ALLOCATE,0,EFFECTS+324,48,4),(ALLOCATE,0,CONTROL+56,0x12345678,4))
            c.compare(f'allocation mutations {released}/{success}',memory,'commit',(0,0,100),plan,changes)
    for callback in (ALLOCATE,0x0201a9dc,0x01c06554,0x0202f07e,0x01c0588e):
        memory=initial(5)
        for off,value in ((84,ARENA),(88,64),(324,32)):setword(memory,EFFECTS+off,value)
        setword(memory,CONTROL+56,callback)
        c.compare(f'one-argument free token collision {callback}',memory,'commit',(0,0,100),
            {ALLOCATE:ARENA+32768,'released':0})
    for type_,index in ((11,5),(14,4),(25,4)):
        memory=initial(type_);setword(memory,CONFIG,100,1);setword(memory,CONTROL+40,0xffff)
        for fresh in (11,14,25):
            changes=((0x02028cb2,0,EFFECTS,fresh,1),(0x02028cb2,0,CONTROL+36,0xffff,4),
                (0x02028cb2,0,CONTROL+44,0xffff,4),(0x02028de8,0,CONTROL+48,0,4))
            c.compare(f'probe fresh type {type_}/{fresh}',memory,'probe',(0,index,1),mutations=changes)

def integration(c):
    memory=initial(2)
    for i in range(5):
        memory=c.compare(f'producer before stage {i}',memory,'fast',(0,0,5+i,3),{'derived':[(0,1000+65536*i)]},carried=i>0)
        for frame in range(4):
            memory=c.compare(f'consumer stage {i}/{frame}',memory,'stage',(0,SAMPLES,128),carried=True)
    for name in ('scene_inner','scene_apply','scene_select','scene_flush'):
        memory=initial(1);scene=0x01c26890+11936
        setword(memory,scene,1,1);setword(memory,0x01c1f180+88,0)
        setword(memory,0x01c26890+956,1)
        c.compare(f'empty {name}',memory,name,() if name=='scene_flush' else (0,))
    for mode in ('fast','fallback','transition',0x0202f07e,0x0202f6d4,0x0202fba6,0x0202fd18,0x020305f8):
        for name in ('scene_inner','scene_apply','scene_select','scene_flush'):
            memory=initial(1);state=0x01c26890;scene=state+11936
            for address,value,width in ((RAM+8,1,1),(RAM+44,24,4),(state+280,2,4),(CONTROL+28,1,1),
                (scene,1,1),(scene+2,1,2),(scene+22,0xffffffe2,2),(RAM+88,0,4),(state+956,1,4)):
                setword(memory,address,value,width)
            if mode=='fallback':
                for i in range(8):setword(memory,CONTROL+210+i,1,1);setword(memory,AUTOMATION+448*i+1,1,1)
            if mode=='transition' or isinstance(mode,int):
                setword(memory,scene+258,1,1);setword(memory,scene+256,25,2)
                setword(memory,0x01c3446c,mode if isinstance(mode,int) else 0x0201a9ea)
            c.compare(f'actual parameter {name}/{mode}',memory,name,() if name=='scene_flush' else (0,),{'derived':[(0,700)]})
    memory=initial(1)
    memory=c.compare('stage route producer',memory,'fast',(0,0,0xffffffd3,7),{'derived':[(0,700)]})
    memory=list(map(bytearray,memory))
    for address,value,width in ((CONTROL+20,1,1),(CONTROL+21,2,1),(CONFIG+6,1,1),(CONFIG+7,2,1),
        (CONFIG+40,0x01c341c4,4),(CONTROL+14,1,1),(CONTROL+348,0,1)):
        setword(memory,address,value,width)
    for frame in range(8):memory=c.compare(f'actual stage/individual automation {frame}',memory,'stage',(0,SAMPLES,128),carried=True)

def edge_paths(c):
    memory=initial(5);setword(memory,0x01c34489,1,1)
    c.compare('delay global reset flag',memory,'commit',(0,1,1))
    memory=initial(29);setword(memory,EFFECTS+82,2,2)
    c.compare('capture mode disabled from prior mode',memory,'commit',(0,6,0))
    for active in (0,1):
        memory=initial(29)
        for address,value,width in ((EFFECTS+1,0,1),(EFFECTS+84,ARENA,4),(EFFECTS+88,32768,4),
            (EFFECTS+369,2,1),(ARENA+8192+40,active,4)):
            setword(memory,address,value,width)
        c.compare(f'capture mode existing IR active {active}',memory,'commit',(0,6,2))
    memory=initial(29);setword(memory,0x01c1f7d8,1)
    c.compare('mode refresh suppressed by global state',memory,'commit',(0,6,2))
    for type_,index in ((11,5),(15,3)):
        for limit in (3000,4000):
            memory=initial(type_);setword(memory,EFFECTS+70+2*index,1,2)
            setword(memory,CONFIG,100,1)
            for offset in (36,40,44):setword(memory,CONTROL+offset,1)
            setword(memory,CONTROL+48,limit)
            c.compare(f'increased processing cost {type_}/{limit}',memory,'probe',(0,index,0))
    # Resource-state gates exercise the complete producer, not a patched entry.
    for old,new in ((0,0),(2,2)):
        memory=initial(29);setword(memory,EFFECTS+82,old,2)
        c.compare(f'unchanged boolean mode {old}/{new}',memory,'fast',(0,6,new,7))
    for type_ in (27,31,32,33,34,35):
        for present in (0,1):
            for ready in (0,1):
                memory=initial(type_)
                setword(memory,EFFECTS+288,ARENA)
                setword(memory,EFFECTS+84,ARENA+4096 if present else 0)
                setword(memory,ARENA+628,ready)
                c.compare(f'capture object readiness {type_}/{present}/{ready}',memory,'fast',(0,0,1,7))
    for old in (0,1,2):
        for new in (0,1,2):
            memory=initial(37);setword(memory,EFFECTS+82,old,2)
            c.compare(f'IR enable polarity {old}/{new}',memory,'fast',(0,6,new,7))
    for index in (0,4):
        for capacity in (0,1,128,0xffffffff):
            for old in (1,100):
                memory=initial(5)
                setword(memory,EFFECTS+84,ARENA);setword(memory,EFFECTS+88,capacity)
                setword(memory,EFFECTS+70,old,2)
                c.compare(f'allocated delay capacity {index}/{capacity}/{old}',memory,'fast',
                    (0,index,100 if index==0 else 0,7),{'derived':[(0,123),(26,456)]})
    memory=initial(7);setword(memory,EFFECTS+292,128)
    c.compare('IR length unchanged permits automation',memory,'fast',(0,3,1,9),
        {'ir_length':128,'derived':[(2,0x3f800000)]})


def api_checks(c):
    count=0;b=Backend(c.program,initial(1),Script());args=(U32*12)(0,0,1);result=(U32*2)(0xdeadbeef,0xcafebabe)
    execute=c.lib.hyperrig_effect_parameters_execute
    def check(value,expected):
        nonlocal count
        assert value==expected,('parameter API guard',count,value,expected);count+=1
    check(execute(0,args,result,None),-200)
    check(execute(0,None,result,ctypes.byref(b.io)),-200)
    check(execute(0,args,None,ctypes.byref(b.io)),-200)
    check(execute(0,args,result,ctypes.byref(b.io)),-202)
    bad=IO(MAP(),b.io.call,None,10000,10000);check(execute(0,args,result,ctypes.byref(bad)),-200)
    absent=IO(MAP(lambda *_:None),b.io.call,None,10000,10000)
    check(execute(REGIONS['commit'][0],args,result,ctypes.byref(absent)),-201)
    bad=IO(b.io.map,b.io.call,None,10000,0);check(execute(0,args,result,ctypes.byref(bad)),-200)
    for budget in (1,2,3):
        b=Backend(c.program,initial(1),Script());b.io.work=budget
        check(execute(REGIONS['commit'][0],args,result,ctypes.byref(b.io)),-203)
        assert tuple(result)==(0xdeadbeef,0xcafebabe)
        assert b.read(0x01c34468,4)==(0xffffffff if budget==3 else 0xfffffffe)
    b=Backend(c.program,initial(1),Script());b.io.services=0
    check(execute(REGIONS['commit'][0],args,result,ctypes.byref(b.io)),-203)
    b=Backend(c.program,initial(1),Script());missing=IO(b.io.map,CALL(),None,10000,1000000)
    check(execute(REGIONS['commit'][0],args,result,ctypes.byref(missing)),-200)
    check(c.lib.hyperrig_effect_parameters_stage(0,SAMPLES,128,None),-200)
    check(c.lib.hyperrig_effect_parameters_scene(0,0,result,ctypes.byref(b.io)),-202)
    return count

def source_paths():
    paths=set(SOURCES)|{'tools/verify_effect_parameters.py','tools/build_effect_parameters.py',
        'tests/effect_parameters_sanitize.c','tests/test_effect_parameters_machine.py',
        'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md'}
    # Some ISA semantics are loaded with exec_module and omitted from sys.modules.
    modules=list(sys.modules.values())
    for module in list(modules):
        filename=getattr(module,'__file__',None)
        if filename and Path(filename).resolve().is_relative_to(ROOT):
            modules.extend(value for value in vars(module).values() if getattr(value,'__file__',None))
    for module in modules:
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
    pending=[ROOT/path for path in SOURCES];scanned=set()
    while pending:
        path=pending.pop().resolve()
        if path in scanned:continue
        scanned.add(path)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',path.read_text(),re.M):
            for candidate in (path.parent/name,ROOT/'firmware/include'/name):
                if candidate.is_file():
                    candidate=candidate.resolve();paths.add(candidate.relative_to(ROOT).as_posix());pending.append(candidate);break
    return sorted(paths)

def report(c,guards,mini_image):
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED
    assert hashlib.sha256(app).hexdigest()==DECODED
    from hyperrig.jieli import unpack_app
    assert unpack_app(original)[2]['app.bin']==app
    body=(ROOT/'firmware/src/hyperrig_effect_parameter_tables.inc').read_text().split('=',1)[1]
    actual=list(map(int,re.findall(r'-?\d+',body)))
    metadata=c.program.data['parameter_metadata'];expected=[]
    for type_ in range(40):
        for index in range(7):expected.extend(struct.unpack_from('<hh',metadata,type_*84+index*12))
    assert actual==expected,'C metadata bounds differ from original records'
    code=c.program.code;new={pc for pc in code if any(start<=pc<end for start,end in REGIONS.values())}
    missing=new-c.coverage
    assert missing=={0x0202f960},'parameter instruction gaps changed from the reviewed corpus'
    # The branch at f942 admits only r0==5; no intervening instruction changes
    # r0 before the contrary condition at f95c. The body still retains f960.
    invariants={'fast_type_five_guard_excludes_redundant_nonfive_assignment':sorted(missing)}
    windows={hex(pc):{'start':pc,'end_exclusive':pc+item[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+item[1])).hexdigest()} for pc,item in sorted(code.items())}
    static={name:{'start':start,'end_exclusive':end,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(start,end) in c.program.static_regions.items()}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI
        mini=unpack_app(raw)[2]['app.bin']
        for record in (*windows.values(),*static.values()):
            start,end=record['start'],record['end_exclusive'];assert region_bytes(mini,start,end)==region_bytes(app,start,end),hex(start)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    return {'schema':1,'project':'HyperRig','component':'reconstructed-effect-parameters','result':'pass',
        'scope':'Complete immediate/automated parameter changes and resource probe, with original scene/stage callers',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'functions':{name:{'start':start,'end_exclusive':end,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(start<=pc<end for pc in code),'visited':sum(start<=pc<end for pc in c.coverage),
            'unvisited':[pc for pc in sorted(code) if start<=pc<end and pc not in c.coverage]} for name,(start,end) in REGIONS.items()},
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.coverage),'unvisited_new':sorted(missing),
            'unvisited_by_entry_invariant':invariants,'unclassified_unvisited':[],
            'all_decoded':len(code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(code)-c.coverage)},
        'static_data':static,'bound_instruction_windows':windows,'mini_v4_binding':binding,
        'real_calls':{hex(k):v for k,v in sorted(c.real_calls.items())},
        'external_service_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'carried_calls':c.carried,'callback_mutation_cases':c.mutating,'private_output_calls':c.private,
        'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,'outputs_state_services_sha256':c.digest.hexdigest(),
        'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['Effect construction, resource estimation and allocation remain explicit mutable services.',
            'The native allocation flag is the only normalized private pointer; all four bytes must be initialized.',
            'The complete caller bodies retain unvisited addresses; this report does not imply unrestricted equivalence.',
            'Stage and scene integrations retain the documented domains of inherited numerical and callback adapters.']}

PARTS={'classifiers':classifiers,'basic':basic,'limits':limits,'allocation':allocation,'automation':automation,'probes':probes,
    'mutations':mutation_cases,'integration':integration,'edge_paths':edge_paths}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--part',choices=PARTS,action='append');parser.add_argument('--output',type=Path)
    parser.add_argument('--sanitizer-corpus',type=Path);parser.add_argument('--mini-image',type=Path);args=parser.parse_args()
    if args.output and (args.output.exists() or args.part):parser.error('final report requires every corpus and a new output')
    replay=args.sanitizer_corpus.open('xb') if args.sanitizer_corpus else None
    c=Corpus(args.library,replay)
    sources={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()} if args.output else {}
    for name in args.part or PARTS:
        PARTS[name](c);print(f'{name} comparisons passed: {sum(c.counts.values())}',flush=True)
    if replay:replay.close()
    guards=api_checks(c)
    result=report(c,guards,args.mini_image) if args.output else {'result':'development-pass','comparisons':c.counts,'steps':c.steps,
        'c_only_guard_checks':guards,'new_visited':sum(any(start<=pc<end for start,end in REGIONS.values()) for pc in c.coverage)}
    if args.output:
        assert sources=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},'inputs changed during verification'
        result['source_sha256']=sources;result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:result[k] for k in ('result','total_comparisons','original_instruction_steps')}|
            {k:result['instruction_coverage'][k] for k in ('new_decoded','new_visited','all_decoded','all_visited')}))
    else:print(json.dumps(result))

if __name__=='__main__':main()
