"""Compare complete effect construction with independently decoded instructions."""
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
from effect_construction_machine import (EffectConstructionProgram,ConstructionParameterProgram,REGIONS,REUSED,STATIC,TABLES,
    ABI_REGIONS,ARITIES,MAPPED,RAM,ARENA,ROOT,region_bytes)
SOURCES=tuple(f'firmware/src/hyperrig_{name}.c' for name in (
    'controls','control_actions','selection','preset_storage','preset_assets',
    'capture_loader','capture_container','capture_dispatch','capture_reset',
    'dot','head','a2l','rechannel','capture_processing','capture_warmup',
    'biquad','biquad_coefficients','biquad_generator','dsp_initialization',
    'dsp_dynamics','dsp_audio_path','dsp_dynamics_processing','biquad_chain',
    'audio_task','dsp_stage','ir_loader','ir_installation','ir_convolution',
    'ir_processing','effect_resampling','effect_enable','effect_processing',
    'effect_parameter_support','preset_application','dsp_transition','dsp_transition_notification',
    'scene_application','effect_parameters','effect_construction'))
EFFECT,CFG=0x01c2c220,0x01c1f7f0
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):_fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),('services',U32),('work',U32)]

def setword(memory,address,value,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:
            data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');return
    raise ValueError(f'fixture address {address:#x}/{size}')
def initial(type_=0,seed=0):
    rng=random.Random(seed);memory=[bytearray(n) for _,n in MAPPED]
    for i in range(480):setword(memory,EFFECT+i,rng.randrange(256),1)
    for a,v,w in ((CFG+8,48000,4),(CFG+12,1200,4),(EFFECT,type_,1),(EFFECT+6,0,1),
        (EFFECT+84,ARENA,4),(EFFECT+88,2048,4),(EFFECT+476,0,4)):
        setword(memory,a,v,w)
    for i,v in enumerate((10,20,30,40,50,60,0)):setword(memory,EFFECT+70+2*i,v,2)
    return memory
class Script:
    def __init__(self,mutations=()):self.mutations=mutations;self.seen={}
    def __call__(self,target,args,m):
        count=self.seen.get(target,0);self.seen[target]=count+1
        for token,occurrence,address,value,width in self.mutations:
            if token==target and (occurrence<0 or count==occurrence):m.write(address,value,width)
        return 0x12345678
class Backend:
    def __init__(self,program,memory,script,alignment=0):
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory];self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment)
            array[:]=data;self.arrays.append(array)
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
    def write(self,address,value,size):
        p=self.map(None,address,size,1)
        if p is None:raise ValueError('unmapped callback mutation')
        ctypes.memmove(p,(value&((1<<(size*8))-1)).to_bytes(size,'little'),size)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def call(self,opaque,target,args,count,borrowed):
        try:
            arguments=tuple(args[i] for i in range(count))+(0,)*(12-count);before=self.snapshot()
            value=self.script(target,arguments,self)
            self.calls.append((target,arguments,before,self.snapshot(),value));self.sites.append((target,count));return value
        except Exception as exc:self.errors.append(str(exc));return 0
class Corpus:
    def __init__(self,library,fixtures=None):
        self.program=EffectConstructionProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.joined_program=ConstructionParameterProgram();self.fixtures=fixtures;self.replays=0
        self.execute=self.library.hyperrig_effect_construction_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.counts={};self.visited=set();self.steps=0;self.real={};self.services={};self.mutating=0;self.carried=0
        self.digest=hashlib.sha256()
        self.coefficient_requests=0;self.extended_exp=0;self.exp_max=0;self.joined_constructor_sites=[]
        if fixtures:
            spans={span:region_bytes(self.joined_program.app,*span) for span in self.joined_program.static_regions.values()}
            fixtures.write(b'ECON0001');fixtures.write(struct.pack('<I',len(spans)))
            for (base,end),data in sorted(spans.items()):fixtures.write(struct.pack('<2I',base,len(data)));fixtures.write(data)
    def compare(self,label,memory,name,args=(),mutations=(),alignment=0,carried=False):
        try:original=self.program.execute(memory,name,args,Script(mutations))
        except Exception as exc:raise AssertionError(f'{label}: original execution: {exc}') from exc
        c=Backend(self.program,memory,Script(mutations),alignment);result=(U32*2)(0xdeadbeef,0xcafebabe)
        status=self.execute(REGIONS[name][0],(U32*12)(*args),result,ctypes.byref(c.io))
        if status or c.errors:raise AssertionError((label,'C status',status,c.errors))
        if tuple(result)!=original['result']:raise AssertionError((label,'result',tuple(result),original['result']))
        if c.snapshot()!=original['memory']:
            changed=[(hex(base+i),x,y) for (base,_),left,right in zip(MAPPED,original['memory'],c.snapshot())
                for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            raise AssertionError((label,'native/C memory',changed[:24]))
        if c.calls!=original['calls']:raise AssertionError((label,'service mutations/order'))
        if c.sites!=[(target,count) for _,target,count in original['service_sites']]:raise AssertionError((label,'service arity'))
        self.counts[name]=self.counts.get(name,0)+1;self.visited|=original['visited'];self.steps+=original['steps']
        self.mutating+=bool(mutations);self.carried+=bool(carried)
        for pc in original['internal_calls']:self.real[pc]=self.real.get(pc,0)+1
        for target,*_ in original['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*result))
        for data in original['memory']:self.digest.update(data)
        self.coefficient_requests+=len(original['coefficient_requests'])
        self.extended_exp+=sum((x&0x7fffffff)>0x41800000 for x in original['exp_arguments'])
        self.exp_max=max(self.exp_max,max((x&0x7fffffff for x in original['exp_arguments']),default=0))
        if self.fixtures:self.write_fixture(0,REGIONS[name][0],args,memory,original,MAPPED,alignment)
        return original['memory']
    def write_fixture(self,kind,entry,args,memory,original,spans,alignment=0,responses=None):
        f=self.fixtures;f.write(struct.pack('<18I',kind,entry,alignment,len(spans),*(tuple(args)+(0,)*(12-len(args))),*original['result']))
        for (base,n),data in zip(spans,memory):f.write(struct.pack('<2I',base,n));f.write(data)
        f.write(struct.pack('<I',len(original['calls'])))
        for i,((_,_,arity),call) in enumerate(zip(original['service_sites'],original['calls'])):
            target,arguments,before,after=call[:4]
            changes=[(base+j,y) for (base,_),left,right in zip(spans,before,after)
                for j,(x,y) in enumerate(zip(left,right)) if x!=y]
            value=call[4] if kind==0 else responses[i]
            if kind:
                for base,data in call[5]:changes.extend((base+j,v) for j,v in enumerate(data))
            f.write(struct.pack('<16I',target,arity,value,*arguments,len(changes)))
            for address,byte in changes:f.write(struct.pack('<IB',address,byte))
        for data in original['memory']:f.write(data)
        self.replays+=1

def helper_cases(c):
    edges=(0,1,2,3,4,7,8,9,10,11,12,15,16,31,32,255,256,65535,65536,0x7fffffff,0x80000000,0xffffffff)
    for name in ('mode_shift','packed_bias','tempo_parameter'):
        for value in (*range(256),*edges):c.compare(f'{name} {value}',initial(),name,(value,))
    for type_ in range(256):c.compare(f'tail pointer {type_}',initial(type_),'tail_pointer',(EFFECT,))
    for value in (0,0x53525631,0x53525630,0xffffffff):
        for offset in (0,1,2,3):
            m=initial();setword(m,ARENA+offset,value)
            c.compare(f'signature {value}/{offset}',m,'signature',(ARENA+offset,),alignment=offset)
    rng=random.Random(1002)
    values=(0,0x80000000,1,0x80000001,0x7fffff,0x807fffff,0x800000,0x80800000,
        0x3effffff,0x3f000000,0xbf000000,0x3f7fffff,0x3f800000,0x3fb504f3,0x3fb504f4,
        0x3fffffff,0x40000000,0x47800000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,
        0x7f800001,0x7fc00000,0xff800001,0xffc00000)
    for name in ('q30','logarithm'):
        for value in (*values,*(rng.getrandbits(32) for _ in range(160))):
            c.compare(f'{name} bits {value:08x}',initial(),name,(value,))
    for rate in (0,1,48000,48077,96000,0x7fffffff,0x80000000,0xffffffff):
        for type_ in (*range(40),0xffffffff):
            m=initial();setword(m,CFG+8,rate);c.compare(f'size {type_}/{rate}',m,'size',(type_,))
    for rate,tempo in ((48000,1200),(1,1),(0xffffffff,0xffffffff),(0,0),(48077,0),(48077,0x80000000)):
        for selector in (*range(16),0xffffffff,0x80000000):
            m=initial();setword(m,CFG+8,rate);setword(m,CFG+12,tempo)
            c.compare(f'tempo samples {selector}/{rate}/{tempo}',m,'tempo_samples',(selector,))
    for type_ in (*range(16),0xffffffff):
        for stored in (-32768,-1,0,1,8,9,12,13,32767):
            m=initial()
            for i in range(7):setword(m,EFFECT+70+2*i,stored,2)
            c.compare(f'tempo value {type_}/{stored}',m,'tempo_value',(EFFECT+70,type_))
    for rate in (1,48000,0xffffffff):
        for value in (-2147483648,-32768,-1,0,1,2,100,1000):
            m=initial();setword(m,CFG+8,rate)
            c.compare(f'onepole {value}/{rate}',m,'onepole',(value&0xffffffff,))
        for value in (0x3f000000,0xbf000000,0x3f800000,0xbf800000,0x40000000,0xc0000000,0x47000000):
            m=initial();setword(m,CFG+8,rate)
            c.compare(f'rate_exp {value:08x}/{rate}',m,'rate_exp',(value,))
    for value in (0x7fffffff,0x7ffffffe):
        m=initial();setword(m,CFG+8,0xffffffff);c.compare(f'onepole large {value}',m,'onepole',(value,))
    for value in (0x3e7a0000,0xbe7a0000):
        m=initial();setword(m,CFG+8,1)
        c.compare(f'extended exp exact signed bound {value:08x}',m,'rate_exp',(value,))

def construction_cases(c):
    for type_ in range(256):c.compare(f'construct type {type_}',initial(type_),'construct',(EFFECT,))
    for type_ in range(1,40):
        for profile in (-128,-1,1,2,8,12,100,128):
            m=initial(type_,type_+profile)
            for i in range(7):setword(m,EFFECT+70+2*i,profile,2)
            c.compare(f'construct flat {type_}/{profile}',m,'construct',(EFFECT,),alignment=(profile&3))
    for type_ in (0,2,4,5,7,11,12,13,14,15,16,24,26,30,36,37,38):
        for mode in (1,2,3,4,7,15,31,32,255):
            m=initial(type_);setword(m,EFFECT+6,mode,1)
            c.compare(f'construct mode {type_}/{mode}',m,'construct',(EFFECT,))
    for rate in (24000,44100,48077,96000,0xffffffff):
        for type_ in (1,3,4,5,8,9,10,11,12,13,14,15,26,28,30,36,37,38):
            m=initial(type_);setword(m,CFG+8,rate)
            c.compare(f'construct rate {type_}/{rate}',m,'construct',(EFFECT,))
    # The seven-section mode includes two packed five-bit values and uses the
    # OLD r0 at 0202d12e/130 for the intervening full signed parameter.
    for mode in (1,15,16,31,32,255,1023,32767,32768,65535):
        for previous in (0,1,2,0xffffffff):
            m=initial(37);setword(m,EFFECT+82,mode,2);setword(m,EFFECT+476,previous)
            c.compare(f'filter37 mode {mode}/{previous}',m,'construct',(EFFECT,))
    for value in (-32768,-1,0,1,2,3,4,5,6,7,8,32767):
        m=initial(38);setword(m,EFFECT+80,value,2)
        c.compare(f'shape38 selector {value}',m,'construct',(EFFECT,))
    for count in (-32768,-1,0,1,2,3,4,5,32767):
        for frequency in (1,50,1000,6000,12000,24000,32767):
            m=initial(26);setword(m,EFFECT+70,frequency,2);setword(m,EFFECT+76,count,2)
            c.compare(f'type26 sections {count}/{frequency}',m,'type26',(EFFECT,))
    # State survives native calls; no synthetic coefficients are inserted.
    for type_ in (3,5,11,12,13,14,15,26,30,36,37,38):
        m=initial(type_)
        for step in range(6):
            m=list(map(bytearray,m));setword(m,EFFECT+70+2*(step%6),step*3+1,2)
            if type_==37:setword(m,EFFECT+82,step%2,2)
            m=c.compare(f'carried {type_}/{step}',m,'construct',(EFFECT,),carried=step>0)

def state_cases(c):
    for token,type_ in ((0x0202b838,17),(0x0202b87e,25),(0x0202ba90,29),
        (0x0202a872,39),(0x0202cd32,27),(0x0202cf5a,30)):
        for final_type in (3,9,19,24):
            m=initial(type_);setword(m,ARENA,0x53525631)
            mutations=((token,0,EFFECT,final_type,1),(token,0,EFFECT+78,0x8000,2),
                (token,0,EFFECT+80,32767,2),(token,0,CFG+8,48077,4))
            c.compare(f'builder mutations {token:x}/{final_type}',m,'construct',(EFFECT,),mutations)
    for history in (0,1,65536,0xffffffff):
        for second in (0,1):
            m=initial(30);setword(m,EFFECT+288,history);setword(m,EFFECT+296,second)
            c.compare(f'carried gain {history}/{second}',m,'construct',(EFFECT,))
    for capacity in (0,1,2,3,16,128,2048):
        for current,pending,count,active,buffer in ((0,0,0,0,0),(100,0,0,0,ARENA),
            (100,1,0,0,ARENA),(100,0,1,0,ARENA),(100,0,0,1,ARENA),(480,0,0,1,ARENA)):
            m=initial(5);setword(m,EFFECT+88,capacity)
            for offset,value in ((292,current),(396,pending),(400,count),(404,active),(84,buffer)):
                setword(m,EFFECT+offset,value)
            c.compare(f'delay transition {capacity}/{current}/{pending}/{count}/{active}/{buffer}',m,'construct',(EFFECT,))
    for type_,effect in ((2,CFG-252),(4,CFG-280),(36,CFG-280),(0,0xffffff80)):
        m=initial(type_);source=bytes(m[0][EFFECT-RAM:EFFECT-RAM+480])
        if effect<0xffffff00:
            for i,v in enumerate(source):setword(m,effect+i,v,1)
            setword(m,CFG+8,48000)
        else:setword(m,effect,type_,1);setword(m,effect+6,255,1)
        c.compare(f'native alias {type_}/{effect:x}',m,'construct',(effect,))
    for type_,offset in ((5,312),(11,300),(12,300),(13,296),(14,304),(15,300)):
        m=initial(type_);setword(m,EFFECT+offset,0)
        c.compare(f'zero carried state {type_}/{offset}',m,'construct',(EFFECT,))

def integration_cases(c):
    from verify_effect_parameters import (Backend as PriorBackend,Script as PriorScript,
        IO as PriorIO,U32 as PriorU32,initial as prior_initial,setword as prior_setword)
    from effect_parameters_machine import REGIONS as PRIOR_REGIONS,MAPPED as PRIOR_MAPPED
    program=c.joined_program;library=c.library
    native=library.hyperrig_effect_parameters_execute
    native.argtypes=[PriorU32,ctypes.POINTER(PriorU32),ctypes.POINTER(PriorU32),ctypes.POINTER(PriorIO)]
    class JoinedBackend(PriorBackend):
        def call(self,opaque,target,arguments,count,borrowed):
            if target==0x0202cf62 and count==1:
                result=(U32*2)();io=IO(MAP(lambda _,a,n,w:borrowed.contents.map(borrowed.contents.opaque,a,n,w)),
                    CALL(lambda _,t,p,n,b:self.call(None,t,p,n,ctypes.cast(b,type(borrowed)))),None,1000,1000000)
                status=c.execute(target,(U32*12)(arguments[0]),result,ctypes.byref(io))
                if status:self.errors.append(f'joined construction status {status}')
                return 0
            return super().call(opaque,target,arguments,count,borrowed)
    for type_ in (1,2,3,4,5,7,8,9,10,11,12,13,14,15,17,25,26,28,29,30,36,37,38,39):
        for entry,args in (('commit',(0,0,0)),('fast',(0,0,11,10)),('fast_wrapper',(0,0,12,1))):
            memory=prior_initial(type_)
            for i,value in enumerate((10,20,30,40,50,60,0)):prior_setword(memory,EFFECT+70+2*i,value,2)
            prior_setword(memory,EFFECT+84,ARENA);prior_setword(memory,EFFECT+88,2048)
            # This is a deliberately scoped test bridge, not a public joined C
            # API. No indirect platform callback is installed in these cases;
            # direct CF62 sites are independently recorded by the original VM.
            if any(memory[0][address-RAM:address-RAM+4]!=bytes(4) for address in (0x01c32de4,0x01c32de8,0x01c34458)):
                raise AssertionError('joined fixture unexpectedly installs a callback')
            script=PriorScript();original=program.execute(memory,entry,args,script)
            if any(call[0]==0x0202cf62 for call in original['calls']):
                raise AssertionError('test bridge encountered a construction-token callback')
            backend=JoinedBackend(program,memory,PriorScript());result=(PriorU32*2)(0xdeadbeef,0xcafebabe)
            status=native(PRIOR_REGIONS[entry][0],(PriorU32*12)(*args),result,ctypes.byref(backend.io))
            label=f'joined {type_}/{entry}'
            if status or backend.errors:raise AssertionError((label,status,backend.errors))
            if tuple(result)!=original['result']:raise AssertionError((label,'joined result',tuple(result),original['result']))
            if backend.snapshot()!=original['memory']:
                raise AssertionError((label,'joined complete state'))
            if backend.calls!=original['calls']:raise AssertionError((label,'joined service trace'))
            if backend.sites!=[(t,n) for _,t,n in original['service_sites']]:raise AssertionError((label,'joined arity'))
            c.counts['joined_'+entry]=c.counts.get('joined_'+entry,0)+1;c.visited|=original['visited'];c.steps+=original['steps']
            for pc in original['real_calls']:c.real[pc]=c.real.get(pc,0)+1
            c.joined_constructor_sites.extend(original['construction_sites'])
            if c.fixtures:c.write_fixture(1,PRIOR_REGIONS[entry][0],args,memory,original,PRIOR_MAPPED,responses=script.responses)
            c.digest.update(label.encode())
            for data in original['memory']:c.digest.update(data)

PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
def digest(data):return hashlib.sha256(data).hexdigest()
def source_paths():
    import verify_effect_parameters  # Load the immutable integration driver before source snapshots.
    paths=set(SOURCES)|{'tools/effect_construction_machine.py','tools/verify_effect_construction.py',
        'tools/build_effect_construction.py','tests/test_effect_construction_machine.py','tests/effect_construction_sanitize.c',
        'research/input-manifest.json','upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md'}
    for module in tuple(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            try:relative=Path(path).resolve().relative_to(ROOT).as_posix()
            except ValueError:continue
            if relative.endswith('.py') and relative.startswith(('tools/','hyperrig/','upstream/')):paths.add(relative)
    # These ISA semantics are loaded through importlib without registration.
    for name in ('s.py','b2.py','r.py'):
        paths.add('upstream/pi32v2-isa/tools/hwtest/semantics/'+name)
    pending=[ROOT/path for path in SOURCES];seen=set()
    while pending:
        file=pending.pop()
        if file in seen:continue
        seen.add(file)
        for include in re.findall(r'^\s*#include\s+"([^"]+)"',file.read_text(),re.M):
            candidates=(file.parent/include,ROOT/'firmware/include'/include)
            found=next((p.resolve() for p in candidates if p.is_file()),None)
            if found is None:raise ValueError(f'unresolved source header {include}')
            paths.add(found.relative_to(ROOT).as_posix());pending.append(found)
    return sorted(paths)
def make_report(c,mini_image=None):
    from hyperrig.jieli import unpack_app
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    if digest(original)!=PINNED or digest(app)!=DECODED or unpack_app(original)[2]['app.bin']!=app:
        raise ValueError('pinned original or decoded image mismatch')
    mini=None
    if mini_image:
        raw=mini_image.read_bytes()
        if digest(raw)!=MINI:raise ValueError('unreviewed MINI image')
        mini=unpack_app(raw)[2]['app.bin']
    program=c.joined_program;code=program.code
    windows=[]
    for pc,(_,size,*_) in sorted(code.items()):
        if windows and windows[-1][1]==pc:windows[-1][1]=pc+size
        else:windows.append([pc,pc+size])
    def binding(a,b):
        raw=region_bytes(app,a,b)
        if mini is not None and region_bytes(mini,a,b)!=raw:raise ValueError(f'MINI byte mismatch {a:#x}..{b:#x}')
        return {'start':f'0x{a:08x}','end_exclusive':f'0x{b:08x}','sha256':digest(raw)}
    functions={}
    for name,(a,b) in (REGIONS|REUSED).items():
        item=binding(a,b);item['bytes_sha256']=item.pop('sha256')
        pcs={pc for pc in c.program.code if a<=pc<b};item.update(instructions=len(pcs),visited=len(pcs&c.visited),new=name in REGIONS)
        functions[name]=item
    new={pc for pc in c.program.code if any(a<=pc<b for a,b in REGIONS.values())}
    missing=sorted(new-c.visited)
    if missing:raise ValueError(f'new constructor instructions remain unvisited: {missing}')
    return {'component':'reconstructed-effect-construction','result':'pass','flashable':False,'device_access':False,
        'original_sha256':PINNED,'decoded_sha256':DECODED,'mini_sha256':MINI if mini is not None else None,
        'functions':functions,'static_data':{name:binding(*span) for name,span in STATIC.items()},
        'abi_evidence':{name:binding(*span) for name,span in ABI_REGIONS.items()},
        'loaded_instruction_windows':[binding(a,b) for a,b in windows],
        'loaded_static_data':{name:binding(*span) for name,span in program.static_regions.items()},
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':[],
            'all_decoded':len(code),'all_visited':len(set(code)&c.visited),
            'unvisited_inherited':[f'0x{pc:08x}' for pc in sorted(set(code)-c.visited)]},
        'comparisons':sum(c.counts.values()),'comparisons_by_entry':c.counts,'original_steps':c.steps,
        'actual_calls':{f'0x{pc:08x}':n for pc,n in sorted(c.real.items())},'coefficient_requests':c.coefficient_requests,
        'extended_exp_calls':c.extended_exp,'largest_exp_magnitude_bits':f'0x{c.exp_max:08x}',
        'joined_parameter_comparisons':sum(n for name,n in c.counts.items() if name.startswith('joined_')),
        'joined_direct_constructor_calls':len(c.joined_constructor_sites),
        'joined_direct_constructor_sites':{f'0x{pc:08x}':c.joined_constructor_sites.count(pc) for pc in sorted(set(c.joined_constructor_sites))},
        'joined_boundary':'Test-only bridge; indirect callback slots are zero. Direct-site public integration remains separate.',
        'mutable_callback_cases':c.mutating,'carried_cases':c.carried,'sanitizer_replays':c.replays,
        'comparison_sha256':c.digest.hexdigest(),'source_sha256':{path:digest((ROOT/path).read_bytes()) for path in source_paths()}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',required=True,type=Path)
    p.add_argument('--part',choices=('helpers','construction','state','integration','all'),default='all')
    p.add_argument('--output',type=Path);p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path)
    args=p.parse_args();f=args.fixtures.open('xb') if args.fixtures else None;c=Corpus(args.library,f)
    for name,fn in (('helpers',helper_cases),('construction',construction_cases),('state',state_cases),('integration',integration_cases)):
        if args.part in ('all',name):fn(c);print(name,c.counts,flush=True)
    new={pc for pc in c.program.code if any(a<=pc<b for a,b in REGIONS.values())}
    print('coverage',len(new&c.visited),len(new),'gaps',[f'{pc:08x}' for pc in sorted(new-c.visited)[:40]])
    if f:f.close()
    if args.output:args.output.write_text(json.dumps(make_report(c,args.mini_image),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
