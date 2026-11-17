"""Compare resource ownership, history packing and IR parameter arithmetic offline."""
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
from effect_parameter_resources_machine import (EffectParameterResourcesProgram,REGIONS,REUSED,
    STATIC,TABLES,ARITIES,MAPPED,RAM,ARENA,ROOT,region_bytes)
# Complete transitive link inputs are local source declarations, independent of
# earlier generated manifests or another milestone's comparison driver.
SOURCES=tuple(f'firmware/src/hyperrig_{name}.c' for name in (
    'controls','control_actions','selection','preset_storage','preset_assets',
    'capture_loader','capture_container','capture_dispatch','capture_reset',
    'dot','head','a2l','rechannel','capture_processing','capture_warmup',
    'biquad','biquad_coefficients','biquad_generator','dsp_initialization',
    'dsp_dynamics','dsp_audio_path','dsp_dynamics_processing','biquad_chain',
    'audio_task','dsp_stage','ir_loader','ir_installation','ir_convolution',
    'ir_processing','effect_resampling','effect_enable','effect_processing',
    'effect_parameter_support','effect_parameter_resources'))
EFFECT,CONTROL,CALLBACKS=0x01c2c220,0x01c32db0,0x01c34190
ALLOCATOR,RELEASE,MODE=0x12345010,0x12345020,0x12345030
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
    raise ValueError(f'unmapped resource fixture {address:#x}/{size}')
def initial(seed=0):
    memory=[bytearray(n) for _,n in MAPPED]
    memory[1][:]=bytes([0xa7])*len(memory[1])
    for address,value,width in ((CONTROL+52,ALLOCATOR,4),(CONTROL+56,RELEASE,4),
        (CALLBACKS+4,0x0201a9dc,4),(EFFECT,5,1),(EFFECT+1,1,1),(EFFECT+2,1,1),
        (EFFECT+84,OLD,4),(EFFECT+88,128,4),(OUT,0xa5a5a5a5,4)):
        setword(memory,address,value,width)
    rng=random.Random(seed)
    for i in range(16):setword(memory,SOURCE+4*i,rng.getrandbits(32))
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
            arguments=tuple(args[i] for i in range(12));before=self.snapshot()
            value=self.script(target,arguments,self)
            self.calls.append((target,arguments,before,self.snapshot(),value));self.sites.append((target,count))
            return value
        except Exception as exc:self.errors.append(str(exc));return 0

class Corpus:
    def __init__(self,library,fixtures=None):
        self.program=EffectParameterResourcesProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.execute=self.library.hyperrig_effect_parameter_resources_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.fixtures=fixtures;self.counts={};self.visited=set();self.steps=0;self.real={};self.services={}
        self.mutating=0;self.carried=0;self.digest=hashlib.sha256();self.replays=0
    def compare(self,label,memory,name,args=(),returns=None,mutations=(),alignment=0,carried=False):
        try:original=self.program.execute(memory,name,args,Script(returns,mutations))
        except Exception as exc:raise AssertionError(f'{label}: original execution: {exc}') from exc
        c=Backend(self.program,memory,Script(returns,mutations),alignment);result=(U32*2)(0xdeadbeef,0xcafebabe)
        status=self.execute(REGIONS[name][0],(U32*12)(*args),result,ctypes.byref(c.io))
        if status or c.errors:raise AssertionError((label,'C status',status,c.errors))
        if tuple(result)!=original['result']:raise AssertionError((label,'C/original result',tuple(result),original['result']))
        if c.snapshot()!=original['memory']:
            changes=[(hex(base+i),x,y) for (base,_),left,right in zip(MAPPED,original['memory'],c.snapshot())
                for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            raise AssertionError((label,'native/C memory',changes[:32]))
        if c.calls!=original['calls']:raise AssertionError((label,'callback trace mismatch',
            [(hex(t),args[:3],v) for t,args,_,_,v in original['calls']],[(hex(t),args[:3],v) for t,args,_,_,v in c.calls]))
        if c.sites!=[(t,n) for _,t,n in original['service_sites']]:raise AssertionError((label,'callback arity'))
        self.counts[name]=self.counts.get(name,0)+1;self.visited|=original['visited'];self.steps+=original['steps']
        self.mutating+=bool(mutations);self.carried+=bool(carried)
        for pc in original['internal_calls']:self.real[pc]=self.real.get(pc,0)+1
        for target,*_ in original['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*result))
        for data in original['memory']:self.digest.update(data)
        if self.fixtures:self.write_fixture(memory,name,args,original,alignment)
        return original['memory']
    def write_fixture(self,memory,name,args,original,alignment):
        f=self.fixtures;f.write(struct.pack('<16I',REGIONS[name][0],alignment,*(tuple(args)+(0,)*(12-len(args))),*original['result']))
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

def codec_cases(c):
    edges=(0,1,0xffffffff,32767,32768,0xffff8000,0xffff7fff,0x7fffffff,0x80000000,0x80000001)
    for value in edges:
        for shift in (0,1,15,16,31,32,255):
            memory=initial();setword(memory,OLD+6,value,2);setword(memory,OLD+128,shift,1)
            c.compare(f'decode {value}/{shift}',memory,'decode_sample',(OLD,64,3))
    rng=random.Random(810)
    vectors=[(value,)*16 for value in edges]
    vectors += [tuple((1<<(s+15))-1 if i%2 else -(1<<(s+15)) for i in range(16)) for s in range(17)]
    vectors += [tuple(rng.getrandbits(32) for _ in range(16)) for _ in range(80)]
    for index,values in enumerate(vectors):
        for block in (0,1,2,3,4,7):
            memory=initial()
            for i,value in enumerate(values):setword(memory,SOURCE+4*i,value)
            c.compare(f'encode {index}/{block}',memory,'encode_group',(OLD,128,block,SOURCE),alignment=index%4)
    for offset in (-32,-16,-4,0,4,16,32,60,64):
        memory=initial(15);source=OLD+512
        for i in range(16):setword(memory,source+4*i,rng.getrandbits(32))
        c.compare(f'encode alias {offset}',memory,'encode_group',(source+offset,16,0,source))
    memory=initial();setword(memory,0xfffffffe,0x8001,2);setword(memory,0,4,1)
    c.compare('decode wrapped addresses',memory,'decode_sample',(0xfffffffe,1,0))
    memory=initial(77)
    for block in range(12):
        memory=c.compare(f'carried codec {block}',memory,'encode_group',(OLD,256,block,SOURCE),carried=block>0)
        memory=c.compare(f'carried decode {block}',memory,'decode_sample',(OLD,256,16*block),carried=True)

def migration_cases(c):
    for count in (0,1,7,15,16,17,31,32,33,48,64,65,127):
        for cursor in sorted({0,max(0,count-1),count//2,16 if count>16 else 0}):
            for overlap in (False,True):
                memory=initial(count+cursor)
                for i in range(count):setword(memory,OLD+2*i,(i*599-17000)&65535,2)
                for i in range((count+15)//16):setword(memory,OLD+2*count+i,i%9,1)
                for i in range(16):setword(memory,EFFECT+328+4*i,0x7fffffff-i*12345)
                setword(memory,EFFECT+288,cursor)
                c.compare(f'migrate {count}/{cursor}/{overlap}',memory,'migrate',
                    (EFFECT,OLD,count,OLD if overlap else NEW,256))
    memory=initial(20);setword(memory,EFFECT+288,5)
    for i in range(80):setword(memory,OLD+2*i,i*31-1000,2)
    for i in range(5):setword(memory,OLD+160+i,i,1)
    for i in range(16):setword(memory,EFFECT+328+4*i,i*333)
    memory=c.compare('migration first carried resize',memory,'migrate',(EFFECT,OLD,80,NEW,128))
    setword(memory:=list(map(bytearray,memory)),EFFECT+288,80)
    c.compare('migration second carried resize',memory,'migrate',(EFFECT,NEW,128,OLD,256),carried=True)

def property_cases(c):
    rng=random.Random(407)
    for type_ in range(40):
        for flavor in range(5):
            memory=initial(type_)
            for i in range(480):setword(memory,EFFECT+i,rng.randrange(256),1)
            setword(memory,EFFECT,type_,1)
            for offset in (308,324,352,408,412,416,464,472,476):
                setword(memory,EFFECT+offset,(0,1,65536,0xffffffff,0x80000000)[flavor])
            for offset in (420,421):setword(memory,EFFECT+offset,(0,1,100,255,2)[flavor],1)
            for name in ('fingerprint','sum3','sum4','fingerprint36','fingerprint37','delay_state'):
                c.compare(f'{name} type {type_}/{flavor}',memory,name,(EFFECT,))
            c.compare(f'reset type {type_}/{flavor}',memory,'reset',(EFFECT,))
        for mode in (0,1,2,3,255,0x12345678,0xffffffff):
            memory=initial(type_);setword(memory,EFFECT,type_,1)
            c.compare(f'mode {type_}/{mode}',memory,'change_mode',(EFFECT,mode))
    c.compare('fixed extra size',initial(),'extra_size')

def ownership_cases(c):
    for callback in (0,ALLOCATOR,0x0201a9dc,0x0202eb4c,0x0202df04):
        for size in (0,1,2,3,16,127,0xfffffff0):
            memory=initial();setword(memory,CONTROL+52,callback)
            pointer=OLD if size!=0xfffffff0 else 16
            c.compare(f'allocator callback {callback}/{size}',memory,'allocate',(size,),{callback:pointer})
    for callback in (0,MODE,0x0201a9dc,0x0202ed7e):
        memory=initial();setword(memory,0x01c34458,callback)
        c.compare(f'mode callback {callback}',memory,'mode_callback',(0x87654321,),{callback:0x12345678})
    paths=((NEW,),(0,NEW),(0,0,NEW),(0,0,0,OLD),(0,0,0,0))
    for path in paths:
        for release in (0,RELEASE,0x0201a9dc,0x0202eb4c):
            for flag in (OUT,EFFECT+84,EFFECT+88):
                memory=initial();setword(memory,CONTROL+56,release)
                for i in range(2):setword(memory,CONTROL+88+i,i,1)
                setword(memory,CONTROL+8,2,1)
                c.compare(f'allocate path {path}/{release}/{flag}',memory,'allocate_delay',(EFFECT,256,flag),{ALLOCATOR:path})
    for path in ((NEW,),(0,NEW),(0,0)):
        memory=initial();setword(memory,CONTROL+8,2,1);setword(memory,CONTROL+88,0x100,2)
        c.compare(f'extra {path}',memory,'allocate_extra',(EFFECT,),{ALLOCATOR:path})
    for offset in (1,2,3):
        c.compare(f'unaligned native extra buffer {offset}',initial(),'allocate_extra',(EFFECT,),{ALLOCATOR:NEW+offset})
    for length in (0,1,3,16,255):
        memory=initial();setword(memory,CONTROL+8,length,1)
        for i in range(length):setword(memory,CONTROL+88+i,i%16,1)
        c.compare(f'flush length {length}',memory,'flush')
    memory=initial();setword(memory,CONTROL+8,3,1)
    for i in range(3):setword(memory,CONTROL+88+i,i,1)
    c.compare('flush callback shrinks list',memory,'flush',mutations=((0x0202eb4c,0,CONTROL+8,1,1),))
    c.compare('flush callback grows and replaces list',memory,'flush',mutations=(
        (0x0202eb4c,0,CONTROL+8,4,1),(0x0202eb4c,0,CONTROL+89,7,1),
        (0x0202eb4c,2,CONTROL+91,15,1)))
    for at in (ALLOCATOR,RELEASE,0x0202eb4c):
        memory=initial();setword(memory,CONTROL+8,1,1)
        c.compare(f'ownership mutation {at}',memory,'allocate_delay',(EFFECT,256,OUT),
            {ALLOCATOR:(0,0,0,OLD+2048)},((at,0,EFFECT+88,64,4),(at,0,EFFECT+84,OLD+4096,4),
            (at,0,EFFECT+5,77,1),(at,0,OUT,0x12345678,4)))
    memory=initial();setword(memory,CALLBACKS+4,0x0202df04)
    c.compare('alternate clear target collides with loaded allocator',memory,'allocate_extra',(EFFECT,),
        {ALLOCATOR:NEW},((0x0202df04,0,EFFECT+92,0xbad,4),))
    memory=initial()
    c.compare('allocator callback replaces its own token',memory,'allocate_delay',(EFFECT,256,OUT),
        {ALLOCATOR:0,0x0202df04:NEW},((ALLOCATOR,0,CONTROL+52,0x0202df04,4),))
    memory=initial();setword(memory,EFFECT+88,2048);setword(memory,CALLBACKS+4,0x0202edb8)
    c.compare('restore clear mutates the published effect',memory,'allocate_delay',(EFFECT,4096,OUT),
        {ALLOCATOR:(0,0,0,OLD)},((0x0202edb8,0,EFFECT+84,NEW,4),(0x0202edb8,0,EFFECT+88,9,4)))
    memory=initial();setword(memory,CONTROL+52,0)
    c.compare('allocation without allocator',memory,'allocate_delay',(EFFECT,128,OUT))

def ir_cases(c):
    for object_ in (0,OLD):
        for enabled in (0,1,2,0xffffffff):
            memory=initial();setword(memory,EFFECT+288,object_);setword(memory,OLD,enabled)
            setword(memory,0x01c1f7d0,enabled)
            c.compare(f'IR state {object_}/{enabled}',memory,'ir_state',(EFFECT,))
    rng=random.Random(191)
    edges=(0,1,63,64,65,127,128,129,4095,4096,4097,0x7fffffff,0x80000000,0xffffffff)
    for i in range(210):
        count=edges[i%len(edges)];tail=rng.choice(edges);format_=i%3;mode=(0,1,2,0xffffffff)[i%4]
        desired=rng.choice(edges);memory=initial();direct=i%2
        for off,val in ((48,OLD if direct else 0),(52,count),(56,tail)):setword(memory,EFFECT+off,val)
        setword(memory,EFFECT+68,format_,1);setword(memory,EFFECT+69,i%5==0,1)
        for off,val in ((60,0 if i%3==0 else OLD),(64,count),(68,format_),(72,i%3),(80,tail)):
            setword(memory,CONTROL+off,val)
        setword(memory,0x01c3441c,i%7!=0)
        c.compare(f'IR length {i}',memory,'ir_length',(EFFECT,mode,desired))
    for mode in (0,1):
        for callback in (0,0x12345678):
            memory=initial();setword(memory,CONTROL+64,4096);setword(memory,CONTROL+72,1)
            setword(memory,0x01c3441c,callback)
            c.compare(f'IR global slot callback gate {mode}/{callback}',memory,'ir_length',(EFFECT,mode,8))

def api_checks(c):
    b=Backend(c.program,initial(),Script());p=(U32*12)();out=(U32*2)(0xdeadbeef,0xcafebabe);n=0
    def check(value,expected):
        nonlocal n
        assert value==expected,(n,value,expected);n+=1
    check(c.execute(0,p,out,None),-200);check(c.execute(0,None,out,ctypes.byref(b.io)),-200)
    check(c.execute(0,p,None,ctypes.byref(b.io)),-200);check(c.execute(0,p,out,ctypes.byref(b.io)),-202)
    missing=IO(MAP(),b.io.call,None,1000,1000);check(c.execute(0,p,out,ctypes.byref(missing)),-200)
    absent=IO(MAP(lambda *_:None),b.io.call,None,1000,1000)
    check(c.execute(REGIONS['allocate'][0],p,out,ctypes.byref(absent)),-201)
    for work in (0,1,2):
        io=IO(b.io.map,b.io.call,None,1000,work)
        check(c.execute(REGIONS['allocate_delay'][0],(U32*12)(EFFECT,128,OUT),out,ctypes.byref(io)),-200 if not work else -203)
    io=IO(b.io.map,CALL(),None,1000,1000)
    check(c.execute(REGIONS['allocate'][0],p,out,ctypes.byref(io)),-200)
    io=IO(b.io.map,b.io.call,None,0,1000)
    check(c.execute(REGIONS['allocate'][0],p,out,ctypes.byref(io)),-203)
    check(c.execute(REGIONS['decode_sample'][0],(U32*12)(0xffffffff,0,0),out,ctypes.byref(b.io)),-201)
    check(c.execute(REGIONS['decode_sample'][0],(U32*12)(0x30000f90,0,0),out,ctypes.byref(b.io)),-202)
    assert tuple(out)==(0xdeadbeef,0xcafebabe)
    return n

def source_paths():
    paths=set(SOURCES)|{'tools/verify_effect_parameter_resources.py','tools/build_effect_parameter_resources.py',
        'tests/test_effect_parameter_resources_machine.py','tests/effect_parameter_resources_sanitize.c',
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

PARTS={'codec':codec_cases,'migration':migration_cases,'properties':property_cases,
       'ownership':ownership_cases,'ir':ir_cases}
def report(c,guards,mini):
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    from hyperrig.jieli import unpack_app
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code;new={pc for pc in code if any(a<=pc<b for a,b in REGIONS.values())}
    if new-c.visited:raise ValueError(f'new resource instructions still unvisited: {sorted(new-c.visited)}')
    expected_gaps={0x01c055da,0x01c055de,0x01c055e2,0x01c055e4,0x01c055e6,0x01c055e8,0x01c11f62,0x01c11f64}
    if set(code)-c.visited!=expected_gaps:raise ValueError('unclassified inherited resource instruction gap')
    windows={hex(pc):{'start':pc,'end_exclusive':pc+v[1],'sha256':hashlib.sha256(region_bytes(app,pc,pc+v[1])).hexdigest()}
        for pc,v in sorted(code.items())}
    static={name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(a,b) in STATIC.items()}
    binding=None
    if mini:
        raw=mini.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for record in (*windows.values(),*static.values()):
            a,b=record['start'],record['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    return {'schema':1,'project':'HyperRig','component':'reconstructed-effect-parameter-resources','result':'pass',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,'total_comparisons':sum(c.counts.values()),
        'comparisons':c.counts,'original_instruction_steps':c.steps,'callback_mutation_cases':c.mutating,
        'carried_calls':c.carried,'sanitizer_replay_cases':c.replays,'c_only_guard_checks':guards,
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.visited),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.visited]} for name,(a,b) in REGIONS.items()},
        'reused_functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest()}
            for name,(a,b) in REUSED.items()},
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':sorted(new-c.visited),
            'all_decoded':len(code),'all_visited':len(c.visited),'unvisited_all':sorted(set(code)-c.visited)},
        'inherited_gap_reasons':{hex(pc):('Type25 returns directly from fingerprint without calling the inherited active helper.'
            if pc<0x01c10000 else 'IR state calls the inherited IR-active helper only with a nonzero object token.')
            for pc in sorted(expected_gaps)},
        'static_data':static,'bound_instruction_windows':windows,'mini_v4_binding':binding,
        'real_calls':{hex(k):v for k,v in sorted(c.real.items())},'service_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'outputs_state_services_sha256':c.digest.hexdigest(),
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths()},
        'hardware_test':False,'audio_test':False,'flashable':False,'firmware_changed':False,
        'limitations':['Slot removal 0x0202eb4c and installed allocation/release/mode/alternate-clear callbacks remain explicit services.',
            'Successful allocation tokens require mapped capacity including the native sixteen-byte canary trailer.',
            'Migration intentionally drops an incomplete final sixteen-sample group while publishing the original old count.',
            'No device scheduling, allocator ownership enforcement, audio or hardware behavior is established.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--part',choices=PARTS,action='append');p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if args.output and (args.output.exists() or args.part):p.error('final report needs all cases and a fresh path')
    f=args.fixtures.open('xb') if args.fixtures else None;c=Corpus(args.library,f)
    if f:
        f.write(b'HRPRES01');f.write(struct.pack('<3I',0,len(MAPPED),len(STATIC)))
        for a,n in MAPPED:f.write(struct.pack('<2I',a,n))
        for name,(a,b) in STATIC.items():f.write(struct.pack('<2I',a,b-a));f.write(c.program.data[name])
    for name in args.part or PARTS:
        PARTS[name](c);print(name,sum(c.counts.values()),'comparisons',flush=True)
    guards=api_checks(c)
    if f:f.seek(8);f.write(struct.pack('<I',c.replays));f.close()
    if args.output:args.output.write_text(json.dumps(report(c,guards,args.mini_image),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'pass','comparisons':c.counts,'steps':c.steps,'guards':guards,'visited':len(c.visited)}))
if __name__=='__main__':main()
