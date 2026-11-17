"""Compare complete IR selection, assignment, rollback and relocation offline."""
from __future__ import annotations
import argparse
import ctypes
import functools
import hashlib
import json
import random
import re
import struct
import sys
from pathlib import Path
from ir_effect_lifecycle_machine import (IrEffectLifecycleProgram,REGIONS,REUSED,
    STATIC,ARITIES,ABI_REGIONS,MAPPED,RAM,ARENA,ROOT,region_bytes)
# Complete transitive link inputs are local source declarations, independent of
# earlier generated manifests or another milestone's comparison driver.
SOURCES=('firmware/src/hyperrig_ir_effect_lifecycle.c','firmware/src/hyperrig_biquad_generator.c',
    'firmware/src/hyperrig_biquad_coefficients.c','firmware/src/hyperrig_biquad_chain.c','firmware/src/hyperrig_biquad.c')
EFFECT,CONTROL,CALLBACKS=0x01c2c220,0x01c32db0,0x01c34190
RELEASE,REPLACEMENT=0x12345020,0x12345030
ALLOCATE,READ,MODE=0x12345040,0x12345050,0x12345060
PREPARE,CONSTRUCT,READER,GAIN=0x0202962a,0x020318a8,0x01c3441c,0x01c1f7dc
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
    raise ValueError(f'unmapped IR lifecycle fixture {address:#x}/{size}')
@functools.lru_cache(maxsize=128)
def state_hash(memory):
    h=14695981039346656037
    for data in memory:
        for value in data:h=((h^value)*1099511628211)&0xffffffffffffffff
    return h
def initial(seed=0):
    memory=[bytearray(n) for _,n in MAPPED]
    memory[1][:]=bytes([0xa7])*len(memory[1])
    for address,value,width in ((EFFECT,7,1),(EFFECT+2,1,1),(EFFECT+48,OLD,4),
        (EFFECT+52,16,4),(EFFECT+56,12,4),(EFFECT+60,0,4),(EFFECT+64,73,4),
        (EFFECT+68,1,1),(EFFECT+69,0,1),(CONTROL+52,ALLOCATE,4),(CONTROL+56,RELEASE,4),
        (CONTROL+60,SOURCE,4),(CONTROL+64,8,4),(CONTROL+68,7,4),(CONTROL+72,3,4),
        (CONTROL+76,53,4),(CONTROL+80,6,4),(READER,READ,4),(GAIN,0x3f000000,4),
        (0x01c34458,MODE,4),(0x01c1f7d0,1,4),(0x01c34468,seed,4)):
        setword(memory,address,value,width)
    for i in range(32):setword(memory,SOURCE+2*i,32767 if i==0 else 0,2)
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
        self.program=IrEffectLifecycleProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.execute=self.library.hyperrig_ir_effect_lifecycle_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.fixtures=fixtures;self.counts={};self.visited=set();self.steps=0;self.real={};self.services={}
        self.mutating=0;self.carried=0;self.digest=hashlib.sha256();self.replays=0;self.guard_prefixes=[]
        self.chain=0;self.backend=None;self.alignment=0;self.service_sites={}
    def compare(self,label,memory,name,args=(),returns=None,mutations=(),alignment=0,carried=False,
            services=10000,work=1000000,stop=None):
        try:original=self.program.execute(memory,name,args,Script(returns,mutations),stop=stop)
        except Exception as exc:raise AssertionError(f'{label}: original execution: {exc}') from exc
        edits=[]
        if carried:
            if self.backend is None or alignment!=self.alignment:raise ValueError('missing coherent retained allocation')
            c=self.backend
            for (base,_),old,new in zip(MAPPED,c.snapshot(),memory):
                for i,(x,y) in enumerate(zip(old,new)):
                    if x!=y:c.write(base+i,y,1);edits.append((base+i,y))
            c.script=Script(returns,mutations);c.calls=[];c.sites=[];c.errors=[]
        else:
            self.chain+=1;c=Backend(self.program,memory,Script(returns,mutations),alignment)
        self.backend,self.alignment=c,alignment;c.io.services=services;c.io.work=work
        result=(U32*2)(0xdeadbeef,0xcafebabe)
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
        if status:self.guard_prefixes.append({'label':label,'stop_pc':original['stop_pc'],
            'stop_occurrence':stop[1],'work_budget':work,'service_budget':services})
        for site,target,count in original['service_sites']:
            key=(site,target,count);self.service_sites[key]=self.service_sites.get(key,0)+1
        for pc in original['internal_calls']:self.real[pc]=self.real.get(pc,0)+1
        for target,*_ in original['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*result))
        for data in original['memory']:self.digest.update(data)
        for target,words,before,after,value in original['calls']:
            self.digest.update(struct.pack('<14I',target,*words,value))
            for data in (*before,*after):self.digest.update(data)
        if self.fixtures:self.write_fixture(memory,name,args,original,alignment,services,work,edits)
        return original['memory']
    def write_fixture(self,memory,name,args,original,alignment,services,work,edits):
        expected=(0xdeadbeef,0xcafebabe) if original['status'] else original['result']
        f=self.fixtures;f.write(struct.pack('<20I',REGIONS[name][0],alignment,self.chain,services,work,
            *(tuple(args)+(0,)*(12-len(args))),
            *expected,original['status']&0xffffffff))
        for data in memory:f.write(data)
        f.write(struct.pack('<I',len(edits)))
        for address,value in edits:f.write(struct.pack('<IB',address,value))
        f.write(struct.pack('<I',len(original['calls'])))
        for (_,_,arity),(target,arguments,before,after,value) in zip(original['service_sites'],original['calls']):
            changes=[(base+i,y) for (base,_),left,right in zip(MAPPED,before,after)
                for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            f.write(struct.pack('<16I',target,arity,*arguments,value,len(changes)))
            f.write(struct.pack('<2Q',state_hash(before),state_hash(after)))
            for address,value in changes:f.write(struct.pack('<IB',address,value))
        # FNV-1a gives the sanitizer harness a compact complete-state witness.
        f.write(struct.pack('<Q',state_hash(original['memory'])));self.replays+=1

def source_paths():
    paths=set(SOURCES)|{'tools/verify_ir_effect_lifecycle.py','tools/build_ir_effect_lifecycle.py',
        'tests/test_ir_effect_lifecycle_machine.py','tests/ir_effect_lifecycle_sanitize.c',
        'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md','research/input-manifest.json',
        'upstream/pi32v2-isa/tools/hwtest/semantics/s.py','upstream/pi32v2-isa/tools/hwtest/semantics/b2.py',
        'upstream/pi32v2-isa/tools/hwtest/semantics/r.py'}
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


def basic_cases(c):
    returns={ALLOCATE:NEW,PREPARE:0,CONSTRUCT:NEW}
    for name,args in (('mode_prepare',(EFFECT,)),('temporary',(EFFECT,SOURCE,8,6,0x3f800000,1,3,9)),
        ('temporary',(EFFECT,0,8,6,0x3f800000,1,3,9)),('select_source',(EFFECT,)),
        ('refresh',(0,)),('assign',(0,SOURCE,8,0,1,0,0)),('assign',(0,SOURCE,8,0,1,3,77)),
        ('assign_direct',(0,SOURCE,8,0,1)),('owns',(0,)),('construct_copy',(NEW,SOURCE,128)),
        ('relocate',(NEW,OLD))):
        memory=initial();c.compare(f'basic {name}',memory,name,args,returns)


def mode_cases(c):
    for mode in (0,1,2,0xffffffff):
        for callback in (0,MODE):
            for responses in ((0,),(-1,),(-3,0),(-3,-3),(-3,19)):
                m=initial();setword(m,0x01c1f7d0,mode);setword(m,0x01c34458,callback)
                c.compare(f'mode {mode}/{callback}/{responses}',m,'mode_prepare',(EFFECT,),{PREPARE:responses})
    for target,occurrence,address,value in ((MODE,0,0x01c1f7d0,0),(MODE,0,0x01c1f7d0,1),
            (PREPARE,0,0x01c1f7d0,0),(PREPARE,0,0x01c1f7d0,1),(PREPARE,0,0x01c34458,REPLACEMENT),
            (MODE,0,0x01c34458,0)):
        c.compare('mode callback reload',initial(),'mode_prepare',(EFFECT,),{PREPARE:(-3,11)},
            ((target,occurrence,address,value,4),),alignment=1)

def temporary_cases(c):
    args=(EFFECT,0,17,0xabcdef01,0x7f800001,255,0x11223344,0xa1b2c3d4)
    for change in ({2:0},{6:0},{1:SOURCE},{1:0xffffffff},{2:0x80000000},{2:0xffffffff}):
        values=list(args)
        for i,v in change.items():values[i]=v
        c.compare(f'temporary raw arguments {change}',initial(),'temporary',values,{ALLOCATE:NEW})
    for address in (READER,CONTROL+52):
        m=initial();setword(m,address,0);c.compare('missing temporary callback',m,'temporary',args)
    for allocated in (0,NEW):
        for read in (0,1,0xffffffff):
            for prepared in (0,-1,-3,17):
                c.compare(f'temporary services {allocated}/{read}/{prepared}',initial(),'temporary',args,
                    {ALLOCATE:allocated,READ:read,PREPARE:prepared},alignment=3)
    controls=((CONTROL+60,0x11223344),(CONTROL+64,0x55667788),(CONTROL+80,0xaabbccdd),
        (GAIN,0x80000000),(CONTROL+68,0xabcdef01))
    for stage in (READ,PREPARE):
        mutations=tuple((stage,0,a,v,4) for a,v in controls)+((stage,0,CONTROL+56,REPLACEMENT,4),)
        c.compare('temporary snapshot/restore around callback',initial(),'temporary',args,
            {ALLOCATE:NEW,PREPARE:-7},mutations)
    for address in (CONTROL+52,READER,CONTROL+56,0x01c34458):
        c.compare('temporary token reload after mode',initial(),'temporary',args,
            {ALLOCATE:NEW,REPLACEMENT:NEW},((MODE,0,address,REPLACEMENT,4),))
    c.compare('temporary indirect zero allocator after check',initial(),'temporary',args,
        {0:NEW},((MODE,0,CONTROL+52,0,4),))
    c.compare('temporary reader failure reloads zero release',initial(),'temporary',args,
        {ALLOCATE:NEW,READ:1},((READ,0,CONTROL+56,0,4),))

def routing_cases(c):
    for slot in (0,1,15,16,255,0x80000000,0xffffffff):
        for active,type_ in ((0,7),(1,6),(1,7),(255,7)):
            m=initial()
            if slot<=15:
                p=EFFECT+480*slot
                for a,v,w in ((p,type_,1),(p+2,active,1),(p+48,0,4),(p+69,3,1),(p+52,16,4)):
                    setword(m,a,v,w)
            for name in ('refresh','owns'):
                c.compare(f'{name} slot/active/type {slot}/{active}/{type_}',m,name,(slot,),{ALLOCATE:NEW})
    for source,slot in ((0,0),(OLD,0),(0,3),(OLD,3)):
        for global_source,global_count,global_slot,reader in ((0,0,0,0),(0,8,0,READ),
                (0,8,3,0),(0,8,3,READ),(SOURCE,8,0,0),(SOURCE,0,3,READ)):
            m=initial()
            for a,v,w in ((EFFECT+48,source,4),(EFFECT+69,slot,1),(CONTROL+60,global_source,4),
                    (CONTROL+64,global_count,4),(CONTROL+72,global_slot,4),(READER,reader,4)):
                setword(m,a,v,w)
            for name,args in (('select_source',(EFFECT,)),('refresh',(0,)),('owns',(0,))):
                c.compare(f'{name} local/global routing',m,name,args,{ALLOCATE:NEW})

def gain_cases(c):
    values=(-2147483648,-2147483647,-100000000,-1000000,-900000,-90000,-60001,-60000,
        -5432,-1,0,1,4342,4343,19999,20000,20001,770000,780000,900000,1000000,100000000,
        2147483646,2147483647)
    for metadata in values:
        m=initial();setword(m,EFFECT+60,metadata)
        c.compare(f'raw signed gain {metadata}',m,'select_source',(EFFECT,),alignment=1)
    rng=random.Random(0x29728)
    for i in range(24):
        m=initial();setword(m,EFFECT+60,rng.randint(-250000,250000))
        c.compare(f'gain rounding {i}',m,'select_source',(EFFECT,))

def samples(memory,source,count,pattern):
    rng=random.Random(count+pattern)
    for i in range(count):
        value=(0 if pattern==0 else 32767 if i==0 else 0) if pattern<2 else (
            (32767 if i==0 else -32768 if i==1 else rng.randint(-32768,32767)) if pattern==2 else
            (32767 if i==0 else 1 if i==count-1 else 0))
        setword(memory,(source+2*i)&0xffffffff,value,2)

def assignment_cases(c):
    for slot in (16,255,0xffffffff):
        c.compare('assign invalid slot',initial(),'assign',(slot,SOURCE,8,0,1,0,0))
    for active,type_ in ((0,7),(1,0),(1,255)):
        m=initial();setword(m,EFFECT+2,active,1);setword(m,EFFECT,type_,1)
        c.compare('assign invalid effect',m,'assign',(0,SOURCE,8,0,1,0,0))
    for count in (0,1,2,3,15,16,17,127,128,255,256,512,513,1024,4096):
        for stored in (0,3):
            for pattern in (0,1,2,3):
                m=initial();samples(m,SOURCE,count,pattern)
                c.compare(f'assign samples {count}/{stored}/{pattern}',m,'assign',
                    (0,SOURCE,count,1234,255,stored,0x87654321),{ALLOCATE:NEW},alignment=pattern%4)
    for slot in (0,1,255,256,0x80000000,0xffffffff):
        for reader in (0,READ):
            for metadata in (-2147483648,-60001,-60000,0,20000,20001,2147483647):
                m=initial();setword(m,READER,reader)
                c.compare('stored eligibility and signed clamp',m,'assign',
                    (0,SOURCE,8,metadata&0xffffffff,0,slot,0xaabbccdd),{ALLOCATE:NEW})
    for global_source,count,slot,reader in ((0,0,0,0),(0,8,0,READ),(0,8,3,0),
            (0,8,3,READ),(SOURCE,8,0,0)):
        m=initial()
        for a,v in ((CONTROL+60,global_source),(CONTROL+64,count),(CONTROL+72,slot),(READER,reader)):
            setword(m,a,v)
        c.compare('assign clears local ownership to global source',m,'assign',
            (0,0,0xffffffff,0xffffffff,0xffffffff,255,0xffffffff),{ALLOCATE:NEW})
    for count in (1,2,3,0x7fffffff,0x80000000,0x80000001,0xffffffff):
        for allocator in (0,ALLOCATE):
            m=initial();setword(m,CONTROL+52,allocator)
            c.compare('allocation size wrap and failure',m,'assign',(0,SOURCE,count,0,1,0,0))
    for prepared in (0,-1,-3,91):
        for free in (0,RELEASE):
            m=initial();setword(m,CONTROL+56,free)
            c.compare('assign commit/rollback and optional free',m,'assign',(0,SOURCE,8,0,1,0,0),
                {ALLOCATE:NEW,PREPARE:prepared})
    for old in (0,NEW):
        m=initial();setword(m,EFFECT+48,old)
        c.compare('assignment cached old source',m,'assign',(0,SOURCE,8,0,1,0,0),{ALLOCATE:NEW})

def alias_mutation_cases(c):
    for source in (SOURCE,SOURCE+1,0xfffffff0):
        for displacement in (-2,0,2):
            m=initial();samples(m,source,16,2);allocated=(source+displacement)&0xffffffff
            c.compare(f'forward sample copy alias {source}/{displacement}',m,'assign',
                (0,source,16,0,1,0,0),{ALLOCATE:allocated},alignment=3)
    for source in (EFFECT+40,CONTROL+48):
        # Source aliases public fields that assignment writes before trimming.
        m=initial()
        c.compare('sample metadata aliases after copy',m,'assign',(0,source,16,0,1,0,0),{ALLOCATE:NEW})
    fields=((EFFECT+48,OLD+256,4),(EFFECT+52,73,4),(EFFECT+60,1432,4),
        (EFFECT+68,123,1),(EFFECT+69,99,1),(EFFECT+64,0xabcdef01,4),(EFFECT+56,71,4))
    for stage in (MODE,PREPARE):
        for prepared in (0,-1):
            changes=tuple((stage,0,a,v,w) for a,v,w in fields)
            c.compare('assignment snapshot/rollback reloads',initial(),'assign',(0,SOURCE,8,0,1,0,0),
                {ALLOCATE:NEW,PREPARE:prepared},changes,alignment=1)
    for prepared in (0,-1):
        c.compare('assignment release and counter callback mutation',initial(),'assign',(0,SOURCE,8,0,1,0,0),
            {ALLOCATE:NEW,PREPARE:prepared},((PREPARE,0,CONTROL+56,REPLACEMENT,4),
                (REPLACEMENT,0,0x01c34468,0xffffffff,4),(REPLACEMENT,0,EFFECT+52,19,4)))
    for target,_ in (REGIONS|REUSED).values():
        for address in (0x01c34458,CONTROL+52,CONTROL+56,READER):
            m=initial();setword(m,address,target)
            c.compare('callback token collides with loaded code',m,'temporary',
                (EFFECT,0,8,5,0x3f800000,1,3,44),{ALLOCATE:NEW,target:NEW if address==CONTROL+52 else 0})
    for target in (PREPARE,CONSTRUCT):
        m=initial();setword(m,0x01c34458,target)
        c.compare('indirect token collides with explicit direct service',m,'mode_prepare',(EFFECT,))

def object_cases(c):
    for destination in (0,NEW,0xfffffffd):
        for source in (0,SOURCE,0xffffffff):
            for count in (0,1,129,0x80000000,0xffffffff):
                c.compare('copy constructor argument forwarding',initial(),'construct_copy',
                    (destination,source,count),{CONSTRUCT:0x87654321},alignment=1)
    for object_ in (NEW,NEW+1,0xfffffff0,0):
        for previous in (0,OLD,0xffffffff,object_):
            for active in (0,1,0xffffffff):
                m=initial();setword(m,object_,active)
                for i,offset in enumerate(range(20,56,4)):
                    setword(m,(object_+offset)&0xffffffff,(0x87654321*i)&0xffffffff)
                c.compare('relocation wraps every pointer independently',m,'relocate',(object_,previous),alignment=3)
    c.compare('construct publishes callback mutation',initial(),'construct_copy',(NEW,SOURCE,1024),{CONSTRUCT:NEW},
        ((CONSTRUCT,0,NEW,1,4),(CONSTRUCT,0,NEW+20,SOURCE,4)))

def carried_cases(c):
    for seed in range(8):
        m=initial(seed);alignment=seed%4
        for i,(source,stored,prepared) in enumerate(((SOURCE,0,0),(SOURCE,3,0),(SOURCE,0,-1),(0,0,0),(SOURCE,0,0))):
            m=c.compare('retained install, stored, rollback, global, reinstall',m,'assign',
                (0,source,8,(i*1000-2000)&0xffffffff,i&1,stored,seed),{ALLOCATE:NEW,PREPARE:prepared},
                alignment=alignment,carried=i!=0)
            m=c.compare('retained ownership query',m,'owns',(0,),alignment=alignment,carried=True)
            m=c.compare('retained refresh',m,'refresh',(0,),{ALLOCATE:NEW},alignment=alignment,carried=True)

def prefix_cases(c):
    # Native observation PCs follow independently decoded loop bodies. The C
    # budgets here only choose a portable stop with the same public prefix.
    for count in (16,0xffffffff):
        c.compare('three forward copies before finite work stop',initial(),'assign',
            (0,SOURCE,count,0,1,0,0),{ALLOCATE:NEW},work=11,stop=(0x020299a4,3))
    c.compare('mode notification before denied preparation service',initial(),'mode_prepare',(EFFECT,),
        services=1,stop=(0x02029744,0))

def api_checks(c):
    checks=0;args=(U32*12)(NEW,OLD);result=(U32*2)(0xdeadbeef,0xcafebabe)
    b=Backend(c.program,initial(),Script());fn=c.execute
    for arguments,output,io in ((None,result,ctypes.byref(b.io)),(args,None,ctypes.byref(b.io)),(args,result,None)):
        assert fn(REGIONS['relocate'][0],arguments,output,io)==-200;checks+=1
    for entry,values,services,work,call,map_,expected in (
        (0,(0,),10000,1000000,True,True,-200),
        (REGIONS['relocate'][0],(NEW,OLD),10000,0,True,True,-203),
        (REGIONS['relocate'][0],(NEW,OLD),10000,1000000,True,False,-200),
        (REGIONS['relocate'][0],(0x40000000,OLD),10000,1000000,True,True,-201),
        (REGIONS['relocate'][0],(0xfffffffd,OLD),10000,1000000,True,True,-201),
        (REGIONS['relocate'][0],(0x30000ffe,OLD),10000,1000000,True,True,-202),
        (REGIONS['mode_prepare'][0],(EFFECT,),10000,1000000,False,True,-200),
        (REGIONS['mode_prepare'][0],(EFFECT,),0,1000000,True,True,-203)):
        b=Backend(c.program,initial(),Script());before=b.snapshot();b.io.services=services;b.io.work=work
        if not call:b.io.call=CALL()
        if not map_:b.io.map=MAP()
        result=(U32*2)(0xdeadbeef,0xcafebabe)
        assert fn(entry,(U32*12)(*values),result,ctypes.byref(b.io))==expected
        assert tuple(result)==(0xdeadbeef,0xcafebabe) and b.snapshot()==before;checks+=1
    m=initial();setword(m,EFFECT+60,0x7fffffff)
    b=Backend(c.program,m,Script());before=b.snapshot();b.io.work=100
    result=(U32*2)(0xdeadbeef,0xcafebabe)
    assert fn(REGIONS['select_source'][0],(U32*12)(EFFECT),result,ctypes.byref(b.io))==-203
    assert tuple(result)==(0xdeadbeef,0xcafebabe) and b.snapshot()==before and not b.calls;checks+=1
    return checks

PARTS={'basic':basic_cases,'mode':mode_cases,'temporary':temporary_cases,'routing':routing_cases,
    'assignment':assignment_cases,'alias_mutation':alias_mutation_cases,'objects':object_cases,
    'carried':carried_cases,'prefix':prefix_cases,'gain':gain_cases}


def report(c,guards,mini_image,sources):
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    from hyperrig.jieli import unpack_app
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code;new={pc for pc in code if any(a<=pc<b for a,b in REGIONS.values())}
    if new-c.visited:raise ValueError(f'IR lifecycle instructions unvisited: {[hex(x) for x in sorted(new-c.visited)]}')
    windows={hex(pc):{'start':pc,'end_exclusive':pc+v[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+v[1])).hexdigest()} for pc,v in sorted(code.items())}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for item in windows.values():
            a,b=item['start'],item['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        for a,b in ABI_REGIONS.values():assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':0,
            'identical_unexecuted_abi_regions':len(ABI_REGIONS)}
    return {'schema':1,'project':'HyperRig','component':'reconstructed-ir-effect-lifecycle','result':'pass',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'callback_mutation_cases':c.mutating,'carried_calls':c.carried,'retained_allocation_chains':c.chain,
        'original_guard_prefix_comparisons':len(c.guard_prefixes),'native_prefix_observations':c.guard_prefixes,
        'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.visited),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.visited]} for name,(a,b) in REGIONS.items()},
        'reused_functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest()}
            for name,(a,b) in REUSED.items()},
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':sorted(new-c.visited),
            'all_decoded':len(code),'all_visited':len(c.visited),'unvisited_all':sorted(set(code)-c.visited)},
        'bound_instruction_windows':windows,'mini_v4_binding':binding,'static_data':{},
        'unexecuted_callee_abi_evidence':{name:{'start':a,'end_exclusive':b,
            'sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest()} for name,(a,b) in ABI_REGIONS.items()},
        'external_call_sites':[{'pc':pc,'target':target,'argument_words':n,'calls':count}
            for (pc,target,n),count in sorted(c.service_sites.items())],
        'real_calls':{hex(k):v for k,v in sorted(c.real.items())},'external_services':{hex(k):v for k,v in sorted(c.services.items())},
        'outputs_state_ordered_services_sha256':c.digest.hexdigest(),'source_sha256':sources,
        'hardware_test':False,'audio_test':False,'flashable':False,'firmware_changed':False,
        'limitations':['Prepare 0x0202962a and construct 0x020318a8 remain explicit direct services; their earlier numerical evidence is not joined here.',
            'Mode, allocation, sample-reader and free callbacks remain synchronous scripted services at audited original indirect call sites, including colliding tokens.',
            'All signed32 gain metadata is accepted; exact original repeated binary32 reduction/scaling may consume a finite work budget. No arbitrary sample-count limit is imposed.',
            'Native sample/pointer arithmetic wraps modulo 2^32; each individual access must fit mapped stable bytes and exclude the private native stack.',
            'Three explicit native PC observations prove selected public prefixes only. Other API/mapping checks are C-only; stops are not resumable.',
            'Successful comparisons preserve callback state and order, public aliases and retained allocations; no concurrency, allocator implementation, audio or hardware validation is claimed.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--part',choices=PARTS,action='append');p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if args.output and (args.output.exists() or args.part):p.error('final report requires every corpus and a fresh path')
    f=args.fixtures.open('xb') if args.fixtures else None;c=Corpus(args.library,f)
    from hyperrig.jieli import unpack_app
    sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()} if args.output else {}
    if f:
        f.write(b'HRIRL002');f.write(struct.pack('<3I',0,len(MAPPED),len(STATIC)))
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
