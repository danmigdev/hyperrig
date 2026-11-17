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
from ir_effect_numerical_machine import (IrEffectNumericalProgram,REGIONS,REUSED,
    STATIC,ARITIES,ALL_REGIONS,MAPPED,RAM,ARENA,ROOT,region_bytes)
# Complete transitive link inputs are local source declarations, independent of
# earlier generated manifests or another milestone's comparison driver.
SOURCES=tuple('firmware/src/hyperrig_'+name+'.c' for name in (
    'ir_effect_numerical','ir_convolution','ir_installation','ir_loader','preset_assets','preset_storage',
    'selection','control_actions','controls','biquad_generator','biquad_coefficients','biquad_chain','biquad'))
EFFECT,CONTROL,CALLBACKS=0x01c2c220,0x01c32db0,0x01c34190
RELEASE,REPLACEMENT=0x12345020,0x12345030
ALLOCATE,READ,MODE=0x12345040,0x12345050,0x12345060
PREPARE,CONSTRUCT,READER,GAIN=0x0202962a,0x020318a8,0x01c3441c,0x01c1f7dc
OUT,SOURCE,OLD,NEW=ARENA+250000,ARENA+200000,ARENA+8192,ARENA+16384
TEMP,PARAMETERS,PRODUCER=ARENA+120000,ARENA+240000,0x12345070
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
        self.io=IO(MAP(self.map),CALL(self.call),None,10000,4000000)
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
        self.program=IrEffectNumericalProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.execute=self.library.hyperrig_ir_effect_numerical_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.fixtures=fixtures;self.counts={};self.visited=set();self.steps=0;self.real={};self.services={}
        self.mutating=0;self.carried=0;self.digest=hashlib.sha256();self.replays=0;self.guard_prefixes=[]
        self.chain=0;self.backend=None;self.alignment=0;self.service_sites={}
    def compare(self,label,memory,name,args=(),returns=None,mutations=(),alignment=0,carried=False,
            services=10000,work=4000000,stop=None):
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
    paths=set(SOURCES)|{'tools/verify_ir_effect_numerical.py','tools/build_ir_effect_numerical.py',
        'tests/test_ir_effect_numerical_machine.py','tests/ir_effect_numerical_sanitize.c',
        'firmware/src/hyperrig_ir_effect_lifecycle.c',
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


def check_derivative():
    original=ROOT/'firmware/src/hyperrig_ir_effect_lifecycle.c'
    if hashlib.sha256(original.read_bytes()).hexdigest()!='8ef50c48fe209632bb18f4cac8dcb2959a5f0a3f4e81aa6f0ac9d942f3a5a995':
        raise ValueError('frozen lifecycle derivative input differs')
    expected=original.read_text().replace('hyperrig_ir_effect_lifecycle','hyperrig_ir_effect_numerical')
    replacements=(
        ('#include "hyperrig/hyperrig_biquad_generator.h"',
         '#include "hyperrig/hyperrig_biquad_generator.h"\n#include "hyperrig/hyperrig_ir_convolution.h"'),
        ('} Access;','} Access;\nstatic uint32_t numerical_prepare(Access *,uint32_t,uint32_t);\nstatic uint32_t numerical_construct(Access *,uint32_t,uint32_t,uint32_t,uint32_t,const uint32_t *);'),
        ('service(a,UINT32_C(0x0202962a),2,effect,mode,0,0)','numerical_prepare(a,effect,mode)'),
        ('service(a,UINT32_C(0x0202962a),2,effect,0,0,0)','numerical_prepare(a,effect,0)'),
        ('service(&a,UINT32_C(0x020318a8),4,p[0],p[2],UINT32_C(0x020315b8),p[1])',
         'numerical_construct(&a,p[0],p[2],UINT32_C(0x020315b8),p[1],0)'),
        ('    default:return -200;',
         '    case UINT32_C(0x0202962a):value=numerical_prepare(&a,p[0],p[1]);break;\n'
         '    case UINT32_C(0x020318a8):value=numerical_construct(&a,p[0],p[1],p[2],p[3],0);break;\n'
         '    default:return -200;'))
    for before,after in replacements:
        if expected.count(before)!=1:raise ValueError('ambiguous lifecycle derivative substitution')
        expected=expected.replace(before,after)
    source=(ROOT/'firmware/src/hyperrig_ir_effect_numerical.c').read_text()
    marker='/* Mapped numerical closure. The preceding lifecycle derivative is mechanically checked. */'
    if source.count(marker)!=1 or source.split(marker)[0]!=expected+'\n':
        raise ValueError('lifecycle derivative changed outside declared plumbing/direct calls')
    return {'frozen_lifecycle_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'direct_call_replacements':3,
        'native_sites':[0x02029744,0x02029762,0x02031c10],'indirect_service_implementation_unchanged':True}


def smoke_cases(c):
    for name,args,returns in (
        ('prepare',(EFFECT,1),{ALLOCATE:NEW}),
        ('prepare',(EFFECT,0),{ALLOCATE:NEW}),
        ('construct_copy',(NEW,SOURCE,16),{}),
        ('mode_prepare',(EFFECT,),{ALLOCATE:NEW}),
        ('temporary',(EFFECT,SOURCE,16,12,0x3f800000,1,0,0),{ALLOCATE:NEW}),
        ('assign',(0,SOURCE,16,0,1,0,0),{ALLOCATE:(TEMP,NEW)}),
        ('assign',(0,SOURCE,16,0,1,3,44),{ALLOCATE:NEW}),
        ('select_source',(EFFECT,),{ALLOCATE:NEW}),
        ('construct',(NEW,0xffffffff,0x020315b8,SOURCE),{})):
        c.compare('joined numerical '+name,initial(),name,args,returns)


def sample_data(m,count=512,source=SOURCE):
    for i in range(count):setword(m,(source+2*i)&0xffffffff,32767 if i==0 else -12345 if i%19==0 else 0,2)
def window_setup(m,count=257,format_=1,tail=0,budget=1):
    sample_data(m);setword(m,CONTROL+60,SOURCE);setword(m,CONTROL+64,count)
    setword(m,CONTROL+68,format_);setword(m,CONTROL+80,tail);setword(m,GAIN,0x3f800000)
    setword(m,EFFECT+76,budget,2);setword(m,0x01c1fa14,1)

def count_cases(c):
    for count in (0,1,127,128,129,257,4097,0xffffff80,0xffffff81,0xfffffffe,0xffffffff):
        m=initial()
        for i in range(4096):setword(m,SOURCE+4*i,0x3f800000 if i%127==0 else 0)
        object_=0xffff0000 if count==4097 else NEW
        c.compare(f'copy construction raw count {count:#x}',m,'construct_copy',(object_,SOURCE,count),alignment=count%4)
    for count in (0,1,4076,4077,8192,0x7fffffff,0x80000000,0xffffffff):
        m=initial();window_setup(m,count)
        c.compare(f'signed source count {count:#x}',m,'prepare',(EFFECT,1),{ALLOCATE:NEW})
    for mode,format_,tail,budget in ((1,0,0,1),(1,1,17,1),(1,0,17,1),(1,1,128,0),
            (1,1,256,0),(1,1,0,64),(2,0,129,0),(0,0,17,1),(0,1,129,1),(0,1,0,0)):
        m=initial();window_setup(m,257,format_,tail,budget)
        c.compare('real format conversion and fade',m,'prepare',(EFFECT,mode),{ALLOCATE:NEW})
    for effect in (EFFECT-1,EFFECT+1,EFFECT+480*17):
        m=initial();window_setup(m,16);setword(m,effect+76,1,2);setword(m,effect+84,0)
        c.compare('actual effect address and signed status quotient',m,'prepare',(effect,1),{ALLOCATE:NEW})
    for length,fade,mode in ((128,0,0),(128,16,0),(128,0,1),(128,129,1),(0,0xffffffff,1),(0x80000000,0,0)):
        m=initial();window_setup(m,257)
        for i,v in enumerate((length,fade,mode)):setword(m,PARAMETERS+4*i,v)
        c.compare('actual WINDOW producer raw parameter words',m,'construct',(NEW,128,0x02031542,PARAMETERS))
    for metadata in (-60000,20000,-1000000,1000000):
        m=initial();window_setup(m,16);setword(m,EFFECT+60,metadata)
        c.compare('gain result carried into real construction',m,'select_source',(EFFECT,),{ALLOCATE:NEW})

def overlap_cases(c):
    for source in (NEW,NEW+548,NEW+552,NEW+556,NEW+4680):
        m=initial();window_setup(m,128);setword(m,CONTROL+60,source)
        c.compare('window source overlaps constructed storage',m,'prepare',(EFFECT,1),{ALLOCATE:NEW},alignment=1)
    for object_ in (GAIN-552,CONTROL+64-552,CONTROL+68-552,NEW+1,0xfffff000):
        m=initial();window_setup(m,128);setword(m,0,32767,2)
        c.compare('object overlaps globals or wraps across zero',m,'prepare',(EFFECT,1),{ALLOCATE:object_},alignment=3)
    for displacement in (-4,0,4):
        m=initial();source=NEW+552+displacement
        for i in range(129):setword(m,source+4*i,0x3f000000+(i<<13))
        c.compare('copy producer forward overlap',m,'construct_copy',(NEW,source,129),alignment=1)
    # Public WINDOW parameters are reread after output, so this alias must not
    # become an eager host snapshot of length/fade.
    m=initial();window_setup(m,16);params=NEW+552
    for i,v in enumerate((16,8,1)):setword(m,params+4*i,v)
    c.compare('window parameters overlap coefficient output',m,'construct',(NEW,16,0x02031542,params))

def mutation_cases(c):
    fields=((CONTROL+64,0x80000000,4),(CONTROL+60,NEW+552,4),(GAIN,0x7f800000,4),
        (CONTROL+68,0,4),(CONTROL+80,4,4),(EFFECT+84,OLD+4096,4),
        (CONTROL+56,REPLACEMENT,4),(0x01c1fa14,0,4))
    for address,value,width in fields:
        m=initial();window_setup(m,257,1,17,1)
        c.compare('allocation mutation before numerical reload',m,'prepare',(EFFECT,1),{ALLOCATE:NEW},
            ((ALLOCATE,0,address,value,width),))
    m=initial();window_setup(m,16);setword(m,EFFECT+84,OLD+4096)
    c.compare('old object freed before publication',m,'prepare',(EFFECT,1),{ALLOCATE:NEW},
        tuple((RELEASE,0,a,v,4) for a,v in ((EFFECT+84,0x11223344),(EFFECT+88,17),
            (EFFECT+288,0x55667788),(EFFECT+292,19),(0x01c343d8,0xffffffff))))
    for target,address in ((0x0202962a,CONTROL+52),(0x020318a8,CONTROL+52),
            (0x02031542,CONTROL+52),(0x020318a8,CONTROL+56),(0x0202962a,0x01c34458)):
        m=initial();window_setup(m,16);setword(m,EFFECT+84,OLD+4096);setword(m,address,target)
        c.compare('numerical token remains external at other callback site',m,'mode_prepare',(EFFECT,),
            {ALLOCATE:NEW,target:NEW if address==CONTROL+52 else 0})
    for change in ((),((PRODUCER,0,NEW+20,NEW+24,4),),((PRODUCER,0,NEW+4,0,4),),
            ((PRODUCER,0,NEW+40,NEW+6724,4),),((PRODUCER,0,NEW+48,NEW+4,4),)):
        m=initial()
        c.compare('unknown producer remains explicit with late header reloads',m,'construct',
            (NEW,16,PRODUCER,PARAMETERS),mutations=change)
    for target in (PREPARE,CONSTRUCT,REGIONS['assign'][0]):
        c.compare('unknown producer token collides with a loaded body',initial(),'construct',
            (NEW,16,target,PARAMETERS))

def lifecycle_cases(c):
    for prepared in (0,NEW):
        for stored in (0,3):
            m=initial();window_setup(m,16)
            c.compare('actual assignment allocation failure or success',m,'assign',
                (0,SOURCE,16,1000,1,stored,77),{ALLOCATE:(TEMP,prepared) if not stored else prepared})
    for plan in ((0,0),(0,NEW),(NEW,)):
        m=initial();window_setup(m,16)
        c.compare('actual prepare mode fallback allocations',m,'mode_prepare',(EFFECT,),{ALLOCATE:plan})
    m=initial();window_setup(m,16)
    c.compare('temporary read constructs then restores source globals',m,'temporary',
        (EFFECT,0,16,12,0x3f800000,1,3,77),{ALLOCATE:(TEMP,NEW)},
        ((READ,0,TEMP,32767,2),(ALLOCATE,1,GAIN,0x40000000,4)))
    m=initial();window_setup(m,16);setword(m,EFFECT+48,0);setword(m,EFFECT+69,0,1);setword(m,CONTROL+60,0)
    c.compare('global stored source reaches real constructor',m,'refresh',(0,),{ALLOCATE:(TEMP,NEW)},
        ((READ,0,TEMP,32767,2),))
    for seed in range(3):
        m=initial(seed);window_setup(m,17);alignment=seed
        for i,(stored,allocation) in enumerate(((0,NEW),(3,NEW+12000),(0,0),(0,NEW))):
            m=c.compare('retained actual construction and rollback',m,'assign',
                (0,SOURCE,17,(i*1000-2000)&0xffffffff,1,stored,seed),
                {ALLOCATE:(TEMP,allocation) if not stored else allocation},alignment=alignment,carried=i!=0)
            m=c.compare('retained ownership after numerical install',m,'owns',(0,),alignment=alignment,carried=True)
        m=c.compare('retained relocating constructed object',m,'relocate',(NEW,NEW-4096),alignment=alignment,carried=True)
    # These old entry guards remain unchanged in the checked derivative.
    for name,args in (('assign_direct',(0,SOURCE,16,0,1)),('refresh',(16,)),('owns',(16,)),
            ('temporary',(EFFECT,SOURCE,0,0,0,0,0,0)),('construct_copy',(NEW,0,17))):
        m=initial();window_setup(m,16)
        c.compare('preserved wrapper entry behavior',m,name,args,{ALLOCATE:(TEMP,NEW)})

def api_checks(c):
    checks=0
    for name,args,work,services,expected in (
        ('prepare',(EFFECT,1),0,100,-203),('prepare',(EFFECT,1),1000000,0,-203),
        ('construct',(0x30000ff0,1,0x020315b8,SOURCE),1000000,100,-202),
        ('construct',(0xfffffffd,1,0x020315b8,SOURCE),1000000,100,-201),
        ('construct',(0x40000000,1,0x020315b8,SOURCE),1000000,100,-201),
        ('construct',(NEW,128,0x020315b8,SOURCE),800,100,-203),
        ('construct',(NEW,128,0x020315b8,SOURCE),1400,100,-203),
        ('construct',(NEW,128,0x020315b8,SOURCE),2000,100,-203)):
        b=Backend(c.program,initial(),Script());b.io.work=work;b.io.services=services;out=(U32*2)(0xdeadbeef,0xcafebabe)
        assert c.execute(REGIONS[name][0],(U32*12)(*args),out,ctypes.byref(b.io))==expected
        assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    assert c.execute(0,None,None,None)==-200;checks+=1
    return checks
PARTS={'smoke':smoke_cases,'counts':count_cases,'overlap':overlap_cases,
    'mutations':mutation_cases,'lifecycle':lifecycle_cases}


def report(c,guards,mini_image,sources):
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    from hyperrig.jieli import unpack_app
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code
    windows={hex(pc):{'start':pc,'end_exclusive':pc+v[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+v[1])).hexdigest()} for pc,v in sorted(code.items())}
    static={name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(a,b) in STATIC.items()}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for item in (*windows.values(),*static.values()):
            a,b=item['start'],item['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    return {'schema':1,'project':'HyperRig','component':'reconstructed-ir-effect-numerical','result':'pass',
        'integration_only':True,'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'callback_mutation_cases':c.mutating,'carried_calls':c.carried,'retained_allocation_chains':c.chain,
        'original_guard_prefix_comparisons':len(c.guard_prefixes),'native_prefix_observations':c.guard_prefixes,
        'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,'functions':{},
        'reused_functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.visited),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.visited]} for name,(a,b) in ALL_REGIONS.items()},
        'instruction_coverage':{'new_decoded':0,'new_visited':0,'unvisited_new':[],
            'all_decoded':len(code),'all_visited':len(c.visited),'unvisited_all':sorted(set(code)-c.visited)},
        'bound_instruction_windows':windows,'mini_v4_binding':binding,'static_data':static,
        'lifecycle_derivative':check_derivative(),
        'external_call_sites':[{'pc':pc,'target':target,'argument_words':n,'calls':count}
            for (pc,target,n),count in sorted(c.service_sites.items())],
        'real_calls':{hex(k):v for k,v in sorted(c.real.items())},'external_services':{hex(k):v for k,v in sorted(c.services.items())},
        'outputs_state_ordered_services_sha256':c.digest.hexdigest(),'source_sha256':sources,
        'hardware_test':False,'audio_test':False,'flashable':False,'firmware_changed':False,
        'limitations':['This joins existing bodies; functions is empty and no new data exclusion or original function entry is claimed.',
            'Original mode/allocation/reader/free and unknown producer callbacks remain explicit by PC, including target collisions.',
            'Mapped native source/object/control aliases, signed source counts and wrapped count partition arithmetic are preserved.',
            'Constructor-derived FFT spans are disjoint; the unchanged real256/fft128 code executes on staged private arrays with no callbacks inside.',
            'C-only map/work guards around staged FFT operations do not establish identical arbitrary native failure prefixes; stops are not resumable.',
            'All remaining unvisited inherited instruction addresses are reported. Corpus coverage is not a firmware completion percentage.',
            'Allocator implementation, physical storage, concurrency, runtime convolution, audio and hardware remain outside this evidence.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--part',choices=PARTS,action='append');p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if args.output and (args.output.exists() or args.part):p.error('final report requires every corpus and a fresh path')
    check_derivative()
    f=args.fixtures.open('xb') if args.fixtures else None;c=Corpus(args.library,f)
    from hyperrig.jieli import unpack_app
    sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()} if args.output else {}
    if f:
        f.write(b'HRIRN001');f.write(struct.pack('<3I',0,len(MAPPED),0))
        for a,n in MAPPED:f.write(struct.pack('<2I',a,n))
    for name in args.part or PARTS:
        PARTS[name](c);print(name,sum(c.counts.values()),'comparisons',flush=True)
    guards=api_checks(c)
    if f:f.seek(8);f.write(struct.pack('<I',c.replays));f.close()
    result=report(c,guards,args.mini_image,sources) if args.output else {'result':'development-pass','comparisons':c.counts,
        'original_instruction_steps':c.steps,'c_only_guard_checks':guards,'new_visited':0,'all_visited':len(c.visited),
        'missing':[hex(pc) for pc in sorted(set(c.program.code)-c.visited)]}
    if args.output:
        assert sources=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},'inputs changed during comparison'
        result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in result if k in ('result','total_comparisons','comparisons','original_instruction_steps','c_only_guard_checks','new_visited','all_visited','missing')}))


if __name__=='__main__':main()
