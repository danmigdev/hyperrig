"""Compare complete ownership, routing and teardown bodies offline."""
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
from effect_ownership_machine import (EffectOwnershipProgram,REGIONS,REUSED,
    STATIC,ARITIES,MAPPED,RAM,ARENA,ROOT,region_bytes)
# Complete transitive link inputs are local source declarations, independent of
# earlier generated manifests or another milestone's comparison driver.
SOURCES=('firmware/src/hyperrig_effect_ownership.c',)
EFFECT,CONTROL,CALLBACKS=0x01c2c220,0x01c32db0,0x01c34190
RELEASE,REPLACEMENT=0x12345020,0x12345030
OUT,SOURCE,OLD,NEW=ARENA+120000,ARENA+119000,ARENA,ARENA+60000
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):_fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),('services',U32),('work',U32)]

def setword(memory,address,value,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:
            data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');return
    raise ValueError(f'unmapped ownership fixture {address:#x}/{size}')
def initial(seed=0):
    memory=[bytearray(n) for _,n in MAPPED]
    memory[1][:]=bytes([0xa7])*len(memory[1])
    for address,value,width in ((CONTROL+56,RELEASE,4),(EFFECT,27,1),
        (EFFECT+1,1,1),(EFFECT+2,1,1),(EFFECT+3,1,1),(EFFECT+5,1,1),
        (EFFECT+7,3,1),(EFFECT+8,0x1234,2),(EFFECT+84,OLD,4),(EFFECT+88,128,4),
        (EFFECT+48,ARENA+256,4),(EFFECT+52,77,4),(EFFECT+56,88,4),(EFFECT+64,99,4),
        (EFFECT+69,1,1),(EFFECT+288,0x01c2fa38,4),(CONTROL+6,255,1),
        (0x01c34468,seed,4),(OUT,0xa5a5a5a5,4)):
        setword(memory,address,value,width)
    for i in range(3):
        setword(memory,EFFECT+92+4*i,ARENA+512+64*i)
        setword(memory,EFFECT+104+2*i,32+i,2)
    return memory

class Script:
    def __init__(self,returns=None,mutations=()):self.returns=returns or {};self.mutations=mutations;self.seen={}
    def __call__(self,target,args,m):
        occurrence=self.seen.get(target,0);self.seen[target]=occurrence+1
        values=self.returns.get(target,0)
        result=values[min(occurrence,len(values)-1)] if isinstance(values,(list,tuple)) else values
        for at,which,address,value,width in self.mutations:
            if at==target and (which<0 or which==occurrence):m.write(address,value,width)
        return result&0xffffffff

class Backend:
    def __init__(self,program,memory,script,alignment=0):
        self.allocations=[(ctypes.c_ubyte*(len(data)+alignment))() for data in memory]
        self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            view=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment)
            view[:]=data;self.arrays.append(view)
        self.tables={name:(ctypes.c_ubyte*len(data)).from_buffer_copy(data) for name,data in program.data.items()}
        self.script=script;self.calls=[];self.sites=[];self.errors=[]
        self.io=IO(MAP(self.map),CALL(self.call),None,10000,1000000)
    def map(self,opaque,address,size,writable):
        for (base,n),array in zip(MAPPED,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(array)+address-base
        if not writable:
            for name,(base,end) in STATIC.items():
                if base<=address<=address+size<=end:return ctypes.addressof(self.tables[name])+address-base
        return None
    def read(self,address,size):
        p=self.map(None,address,size,0)
        if p is None:raise ValueError('unmapped callback read')
        return int.from_bytes(ctypes.string_at(p,size),'little')
    def write(self,address,value,size):
        p=self.map(None,address,size,1)
        if p is None:raise ValueError('unmapped callback write')
        ctypes.memmove(p,(value&((1<<(8*size))-1)).to_bytes(size,'little'),size)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def call(self,opaque,target,args,count,borrowed):
        try:
            arguments=tuple(args[i] for i in range(count))+(0,)*(12-count);before=self.snapshot()
            value=self.script(target,arguments,self)
            self.calls.append((target,arguments,before,self.snapshot(),value));self.sites.append((target,count))
            return value
        except Exception as exc:self.errors.append(str(exc));return 0

class Corpus:
    def __init__(self,library,fixtures=None):
        self.program=EffectOwnershipProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.execute=self.library.hyperrig_effect_ownership_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.fixtures=fixtures;self.counts={};self.visited=set();self.steps=0;self.real={};self.services={}
        self.mutating=0;self.carried=0;self.digest=hashlib.sha256();self.replays=0;self.guard_prefixes=0
    def compare(self,label,memory,name,args=(),returns=None,mutations=(),alignment=0,carried=False,stop_extra_overread=False):
        try:original=self.program.execute(memory,name,args,Script(returns,mutations),stop_extra_overread=stop_extra_overread)
        except Exception as exc:raise AssertionError(f'{label}: original execution: {exc}') from exc
        c=Backend(self.program,memory,Script(returns,mutations),alignment);result=(U32*2)(0xdeadbeef,0xcafebabe)
        status=self.execute(REGIONS[name][0],(U32*12)(*args),result,ctypes.byref(c.io))
        if status!=original['status'] or c.errors:raise AssertionError((label,'C/native status',status,original['status'],c.errors))
        expected=(0xdeadbeef,0xcafebabe) if status else original['result']
        if tuple(result)!=expected:raise AssertionError((label,'C/original result',tuple(result),expected))
        if c.snapshot()!=original['memory']:
            changes=[(hex(base+i),x,y) for (base,_),left,right in zip(MAPPED,original['memory'],c.snapshot())
                for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            raise AssertionError((label,'native/C memory',changes[:32]))
        if c.calls!=original['calls']:raise AssertionError((label,'callback trace mismatch',
            [(hex(t),args[:3],v) for t,args,_,_,v in original['calls']],[(hex(t),args[:3],v) for t,args,_,_,v in c.calls]))
        if c.sites!=[(t,n) for _,t,n in original['service_sites']]:raise AssertionError((label,'callback arity'))
        self.counts[name]=self.counts.get(name,0)+1;self.visited|=original['visited'];self.steps+=original['steps']
        self.mutating+=bool(mutations);self.carried+=bool(carried)
        self.guard_prefixes+=bool(status)
        for pc in original['internal_calls']:self.real[pc]=self.real.get(pc,0)+1
        for target,*_ in original['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*result))
        for data in original['memory']:self.digest.update(data)
        for target,words,before,after,value in original['calls']:
            self.digest.update(struct.pack('<14I',target,*words,value))
            for data in (*before,*after):self.digest.update(data)
        if self.fixtures:self.write_fixture(memory,name,args,original,alignment)
        return original['memory']
    def write_fixture(self,memory,name,args,original,alignment):
        expected=(0xdeadbeef,0xcafebabe) if original['status'] else original['result']
        f=self.fixtures;f.write(struct.pack('<17I',REGIONS[name][0],alignment,*(tuple(args)+(0,)*(12-len(args))),
            *expected,original['status']&0xffffffff))
        for data in memory:f.write(data)
        f.write(struct.pack('<I',len(original['calls'])))
        for (_,_,arity),(target,arguments,before,after,value) in zip(original['service_sites'],original['calls']):
            changes=[(base+i,y) for (base,_),left,right in zip(MAPPED,before,after)
                for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            f.write(struct.pack('<16I',target,arity,*arguments,value,len(changes)))
            for address,value in changes:f.write(struct.pack('<IB',address,value))
        # FNV-1a gives the sanitizer harness a compact complete-state witness.
        h=14695981039346656037
        for data in original['memory']:
            for value in data:h=((h^value)*1099511628211)&0xffffffffffffffff
        f.write(struct.pack('<Q',h));self.replays+=1

def source_paths():
    paths=set(SOURCES)|{'tools/verify_effect_ownership.py','tools/build_effect_ownership.py',
        'tests/test_effect_ownership_machine.py','tests/effect_ownership_sanitize.c',
        'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md','research/input-manifest.json'}
    modules=list(sys.modules.values())
    for module in list(modules):
        filename=getattr(module,'__file__',None)
        if filename and Path(filename).resolve().is_relative_to(ROOT):
            modules.extend(v for v in vars(module).values() if getattr(v,'__file__',None))
    for module in modules:
        filename=getattr(module,'__file__',None)
        if filename:
            p=Path(filename).resolve()
            if p.is_relative_to(ROOT) and p.suffix=='.py':paths.add(p.relative_to(ROOT).as_posix())
    pending=[ROOT/path for path in SOURCES];scanned=set()
    while pending:
        p=pending.pop().resolve()
        if p in scanned:continue
        scanned.add(p)
        for include in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',p.read_text(),re.M):
            for q in (p.parent/include,ROOT/'firmware/include'/include):
                if q.is_file():q=q.resolve();paths.add(q.relative_to(ROOT).as_posix());pending.append(q);break
    return sorted(paths)


def routes(memory,first=(),second=()):
    for chain,values in enumerate((first,second)):
        for i,value in enumerate(values):setword(memory,CONTROL+348+10*chain+i,value,1)
        setword(memory,CONTROL+14+chain,len(values),1)


def route_cases(c):
    for slot in (*range(17),255,0x80000000,0xffffffff):
        for output in (0,OUT,CONTROL+14,CONTROL+348,CONTROL+358,CONTROL+13):
            memory=initial();routes(memory,(3,7,3,0),(9,15,7,1))
            c.compare(f'lookup output alias {slot}/{output}',memory,'lookup',(slot,output))
    for count in (0,1,2,9,10,11,127,255):
        for chain in (0,1):
            values=[i%16 for i in range(count)]
            for slot in (0,7,15,255):
                memory=initial();routes(memory,values if chain==0 else (),values if chain else ())
                c.compare(f'long lookup {count}/{chain}/{slot}',memory,'lookup',(slot,OUT))
                c.compare(f'detach first occurrence {count}/{chain}/{slot}',memory,'detach',(slot,))
    for found in (0,1):
        for caller in (0,1,255,0xffffffff):
            for index in (0,1,2):
                for left,right in ((0,0),(1,0),(0,2),(128,255)):
                    memory=initial();row=[2,3,4];row[index]=0
                    routes(memory,row if found==0 else (),row if found else ())
                    setword(memory,(CONTROL+14+caller)&0xffffffff,3,1)
                    for i in range(3):
                        setword(memory,(CONTROL+348+10*caller+i)&0xffffffff,row[i],1)
                    for slot in (2,3,4):setword(memory,EFFECT+480*slot+4,left if slot==row[0] else right,1)
                    setword(memory,EFFECT+4,77,1)
                    c.compare(f'neighbor chain/index/flags {found}/{caller}/{index}/{left}/{right}',memory,'neighbors',(caller,0))
    memory=initial();routes(memory,(1,2,3),())
    c.compare('neighbors absent target',memory,'neighbors',(0,9))
    for pattern in range(256):
        for chain in (0,1):
            memory=initial();row=list(range(8));routes(memory,row if chain==0 else (),row if chain else ())
            for slot in range(8):setword(memory,EFFECT+480*slot+4,(1+(slot*31)%255) if pattern>>slot&1 else 0,1)
            c.compare(f'all eight group flags {pattern}/{chain}',memory,'groups',(chain,))
    for count in (0,1,15,16,127,255):
        for pattern in (0,1,0x55,0xaa,0xff):
            memory=initial();routes(memory,[i%8 for i in range(count)],())
            for slot in range(8):setword(memory,EFFECT+480*slot+4,pattern>>slot&1,1)
            c.compare(f'long group scan {count}/{pattern}',memory,'groups',(0,))


def release_cases(c):
    for count in range(4):
        for main in (0,OLD):
            for mask in range(8):
                for callback in (0,RELEASE):
                    memory=initial();setword(memory,EFFECT+7,count,1);setword(memory,EFFECT+84,main)
                    setword(memory,CONTROL+56,callback)
                    for i in range(3):setword(memory,EFFECT+92+4*i,OLD+512+64*i if mask>>i&1 else 0)
                    c.compare(f'cached releases {count}/{main}/{mask}/{callback}',memory,'release',(EFFECT,))
    for effect in (0,0xffffff80,0xffffffc0,ARENA+1,ARENA+2,ARENA+3):
        memory=initial()
        for offset,value,width in ((7,3,1),(84,OLD,4),(88,256,4),(92,NEW,4),(96,NEW+16,4),(100,NEW+32,4)):
            setword(memory,(effect+offset)&0xffffffff,value,width)
        c.compare(f'raw wrapped effect token {effect:#x}',memory,'release',(effect,),alignment=effect&3)
    for offset in (5,7,84,88,92,96,100,104,106,108):
        effect=CONTROL+56-offset;memory=initial()
        for off,value,width in ((7,3,1),(84,OLD,4),(92,NEW,4),(96,NEW+16,4),(100,NEW+32,4)):
            setword(memory,effect+off,value,width)
        # Install the callback last; this may intentionally alter count/pointer
        # bytes when effect fields alias the callback slot.
        setword(memory,CONTROL+56,RELEASE)
        c.compare(f'callback slot aliases cleared field {offset}',memory,'release',(effect,),stop_extra_overread=True)
    for first,second in ((0,0),(0,1),(1,0),(1,1),(255,128)):
        memory=initial();setword(memory,CONTROL+3,first,1);setword(memory,0x01c34489,second,1)
        c.compare(f'refresh gates {first}/{second}',memory,'refresh')


def capture_cases(c):
    for type_ in range(256):
        memory=initial();setword(memory,EFFECT,type_,1)
        c.compare(f'capture type {type_}',memory,'capture',(EFFECT,))
    offsets=(-2147483648,-28417,-28416,-27528,-889,-888,-887,-1,0,1,887,888,889,6216,7104,27528,28416,2147483647)
    for type_ in (27,31,32,33,34,35):
        for i,offset in enumerate(offsets):
            memory=initial();setword(memory,EFFECT,type_,1)
            setword(memory,EFFECT+288,(0x01c2fa38+offset)&0xffffffff)
            setword(memory,CONTROL+6,(0,1,128,255)[i%4],1)
            c.compare(f'capture signed index {type_}/{offset}',memory,'capture',(EFFECT,))
        memory=initial();setword(memory,EFFECT,type_,1);setword(memory,EFFECT+288,0)
        c.compare(f'capture absent pointer {type_}',memory,'capture',(EFFECT,))


def mutation_cases(c):
    tokens=sorted({a for a,b in (REGIONS|REUSED).values()}|{0,0x02028eb2})
    for token in tokens:
        memory=initial();setword(memory,CONTROL+56,token)
        c.compare(f'indirect release token collision {token:#x}',memory,'remove',(0,),
            mutations=((token,0,EFFECT+48,NEW,4),(token,0,EFFECT+288,0x01c2fa38+888*3,4)))
    for occurrence in range(4):
        for next_token in (0,REPLACEMENT,REGIONS['release'][0]):
            memory=initial()
            c.compare(f'callback replacement {occurrence}/{next_token:#x}',memory,'remove',(0,),
                mutations=((RELEASE,occurrence,CONTROL+56,next_token,4),))
    for occurrence in range(5):
        memory=initial();routes(memory,(1,0,2,0),(3,0,4))
        for i,value in enumerate((0,1,0,2,0)):setword(memory,CONTROL+88+i,value,1)
        setword(memory,CONTROL+8,5,1)
        changes=((RELEASE,occurrence,EFFECT+7,255,1),(RELEASE,occurrence,EFFECT+92,NEW+400,4),
            (RELEASE,occurrence,EFFECT+96,NEW+500,4),(RELEASE,occurrence,EFFECT+100,NEW+600,4),
            (RELEASE,occurrence,EFFECT+48,NEW,4),(RELEASE,occurrence,EFFECT+52,500,4),
            (RELEASE,occurrence,EFFECT,31,1),(RELEASE,occurrence,EFFECT+288,0x01c2fa38+1776,4),
            (RELEASE,occurrence,CONTROL+6,255,1),(RELEASE,occurrence,EFFECT+2,1,1),
            (RELEASE,occurrence,CONTROL+88,0,1),(RELEASE,occurrence,CONTROL+8,1,1))
        c.compare(f'cached buffers and later mutable resource fields {occurrence}',memory,'remove',(0,),mutations=changes)
    memory=initial()
    c.compare('zero callback token replaces itself for subsequent cached buffers',memory,'release',(EFFECT,),
        mutations=((RELEASE,0,CONTROL+56,0,4),(0,0,CONTROL+56,REPLACEMENT,4),
            (REPLACEMENT,0,EFFECT+92,NEW,4)))
    memory=initial();setword(memory,CONTROL+3,0,1);setword(memory,0x01c34489,0,1)
    c.compare('refresh callback mutates future gates',memory,'refresh',mutations=(
        (0x02028eb2,0,CONTROL+3,255,1),(0x02028eb2,0,0x01c34489,128,1)))


def removal_cases(c):
    for slot in (*range(16),16,255,0x80000000,0xffffffff):
        for live in (0,1):
            memory=initial(0xffffffff)
            if slot<16:setword(memory,EFFECT+480*slot+2,live,1)
            c.compare(f'remove live/index {slot}/{live}',memory,'remove',(slot,))
    for count in (0,1,2,9,10,16,127,255):
        for queued in (0,1):
            memory=initial();routes(memory,[i%4 for i in range(count)],(0,7,0))
            setword(memory,EFFECT+3,queued,1);setword(memory,CONTROL+8,count,1)
            for i in range(count):setword(memory,CONTROL+88+i,(0,1,0,2,3)[i%5],1)
            for i in range(8):
                setword(memory,CONTROL+210+i,1,1);setword(memory,0x01c2e5a0+448*i+1,i%2,1)
                setword(memory,0x01c2e5a0+448*i+4,255,1)
            c.compare(f'queue compaction and route duplicate {count}/{queued}',memory,'remove',(0,))
    for pointer in (0,OLD+256):
        for callback in (0,RELEASE):
            memory=initial();setword(memory,EFFECT+48,pointer);setword(memory,CONTROL+56,callback)
            c.compare(f'final IR source release {pointer}/{callback}',memory,'remove',(0,))
    memory=initial();routes(memory,(0,1,2),(0,3));setword(memory,CONTROL+8,3,1)
    setword(memory,CONTROL+88,0x000100,3)
    for i in range(4):memory=c.compare(f'carried repeat removal {i}',memory,'remove',(0,),carried=bool(i))


def overread_cases(c):
    for count in (4,5,127,255):
        for mask in (0,1,3,7):
            for callback in (0,RELEASE):
                memory=initial();setword(memory,EFFECT+7,count,1);setword(memory,CONTROL+56,callback)
                for i in range(3):setword(memory,EFFECT+92+4*i,NEW+16*i if mask>>i&1 else 0)
                c.compare(f'lazy fourth read {count}/{mask}/{callback}',memory,'release',(EFFECT,),stop_extra_overread=True)
    for callback in (0,RELEASE):
        memory=initial();setword(memory,EFFECT+7,255,1);setword(memory,CONTROL+56,callback)
        c.compare(f'complete removal fourth-read prefix {callback}',memory,'remove',(0,),stop_extra_overread=True)
    memory=initial();setword(memory,EFFECT+7,4,1)
    c.compare('fourth read follows callbacks that zero current count and token',memory,'remove',(0,),
        mutations=((RELEASE,0,EFFECT+7,0,1),(RELEASE,0,CONTROL+56,0,4)),stop_extra_overread=True)


def api_checks(c):
    n=0;args=(U32*12)(EFFECT);out=(U32*2)(0xdeadbeef,0xcafebabe)
    b=Backend(c.program,initial(),Script())
    def check(status,expected):
        nonlocal n
        assert status==expected,('ownership API guard',n,status,expected);assert tuple(out)==(0xdeadbeef,0xcafebabe);n+=1
    check(c.execute(0,args,out,None),-200);check(c.execute(0,None,out,ctypes.byref(b.io)),-200)
    check(c.execute(0,args,None,ctypes.byref(b.io)),-200);check(c.execute(0,args,out,ctypes.byref(b.io)),-200)
    bad=IO(MAP(),b.io.call,None,1000,1000);check(c.execute(0,args,out,ctypes.byref(bad)),-200)
    absent=IO(MAP(lambda *_:None),b.io.call,None,1000,1000)
    check(c.execute(REGIONS['release'][0],args,out,ctypes.byref(absent)),-201)
    for token,status in ((0x30000000,-202),(0xffffffaa,-201)):
        check(c.execute(REGIONS['release'][0],(U32*12)(token),out,ctypes.byref(b.io)),status)
    for work in (0,1,2,3):
        memory=initial(7);b=Backend(c.program,memory,Script());b.io.work=work
        check(c.execute(REGIONS['remove'][0],(U32*12)(0),out,ctypes.byref(b.io)),-203)
        assert b.read(0x01c34468,4)==(8 if work==3 else 7)
    for services in (0,1,2):
        b=Backend(c.program,initial(),Script());b.io.services=services
        check(c.execute(REGIONS['release'][0],args,out,ctypes.byref(b.io)),-203)
        assert len(b.calls)==services and not b.read(EFFECT+84,4) and not b.read(EFFECT+7,1)
    b=Backend(c.program,initial(),Script());missing=IO(b.io.map,CALL(),None,10000,1000000)
    check(c.execute(REGIONS['release'][0],args,out,ctypes.byref(missing)),-200)
    assert not b.read(EFFECT+84,4) and not b.read(EFFECT+92,4)
    memory=initial();routes(memory,(0,),());b=Backend(c.program,memory,Script())
    check(c.execute(REGIONS['lookup'][0],(U32*12)(0,0xfffffffe),out,ctypes.byref(b.io)),-201)
    return n


PARTS={'routes':route_cases,'release':release_cases,'capture':capture_cases,
       'mutations':mutation_cases,'removal':removal_cases,'overread':overread_cases}


def report(c,guards,mini_image,sources):
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    from hyperrig.jieli import unpack_app
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code;new={pc for pc in code if any(a<=pc<b for a,b in REGIONS.values())}
    if new-c.visited:raise ValueError(f'ownership instructions unvisited: {[hex(x) for x in sorted(new-c.visited)]}')
    windows={hex(pc):{'start':pc,'end_exclusive':pc+v[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+v[1])).hexdigest()} for pc,v in sorted(code.items())}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for item in windows.values():
            a,b=item['start'],item['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':0}
    return {'schema':1,'project':'HyperRig','component':'reconstructed-effect-ownership','result':'pass',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'callback_mutation_cases':c.mutating,'carried_calls':c.carried,'original_fourth_read_prefix_comparisons':c.guard_prefixes,
        'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.visited),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.visited]} for name,(a,b) in REGIONS.items()},
        'reused_functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest()}
            for name,(a,b) in REUSED.items()},
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':sorted(new-c.visited),
            'all_decoded':len(code),'all_visited':len(c.visited),'unvisited_all':sorted(set(code)-c.visited)},
        'bound_instruction_windows':windows,'mini_v4_binding':binding,'static_data':{},
        'real_calls':{hex(k):v for k,v in sorted(c.real.items())},'external_services':{hex(k):v for k,v in sorted(c.services.items())},
        'outputs_state_ordered_services_sha256':c.digest.hexdigest(),'source_sha256':sources,
        'hardware_test':False,'audio_test':False,'flashable':False,'firmware_changed':False,
        'limitations':['Allocation/free platform effects and global refresh 0x02028eb2 remain explicit synchronous services.',
            'Counts up to255 are preserved; only a reached fourth private extra-pointer read stops at its exact original instruction prefix.',
            'Csync is modeled as no additional synchronous byte-memory effect; no hardware/inter-core ordering equivalence is asserted.',
            'Mapped bytes, callback ABI and finite budgets bound the offline API; original allocator ownership and concurrency remain outside this evidence.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--part',choices=PARTS,action='append');p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if args.output and (args.output.exists() or args.part):p.error('final report requires every corpus and a fresh path')
    f=args.fixtures.open('xb') if args.fixtures else None;c=Corpus(args.library,f)
    from hyperrig.jieli import unpack_app
    sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()} if args.output else {}
    if f:
        f.write(b'HROWN002');f.write(struct.pack('<3I',0,len(MAPPED),len(STATIC)))
        for a,n in MAPPED:f.write(struct.pack('<2I',a,n))
    for name in args.part or PARTS:
        PARTS[name](c);print(name,sum(c.counts.values()),'comparisons',flush=True)
    guards=api_checks(c)
    if f:f.seek(8);f.write(struct.pack('<I',c.replays));f.close()
    result=report(c,guards,args.mini_image,sources) if args.output else {'result':'development-pass','comparisons':c.counts,
        'original_instruction_steps':c.steps,'c_only_guard_checks':guards,'new_visited':sum(any(a<=pc<b for a,b in REGIONS.values()) for pc in c.visited),
        'missing':[hex(pc) for pc in sorted(set(c.program.code)-c.visited)]}
    if args.output:
        assert sources=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},'inputs changed during comparison'
        result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in result if k in ('result','total_comparisons','comparisons','original_instruction_steps','c_only_guard_checks','new_visited','missing')}))


if __name__=='__main__':main()
