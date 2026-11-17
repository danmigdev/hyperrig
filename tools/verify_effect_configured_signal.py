"""Compare real constructor output carried into original signal/audio execution."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import re
import struct
import subprocess
import sys
from pathlib import Path
from effect_configured_signal_machine import (EffectConfiguredSignalProgram,carry_preparation_into_audio,
    STATIC,CONSTRUCTOR,CONSTRUCTION_REGIONS,SIGNAL_REGIONS,REUSED,ENTRIES,MAPPED,ROOT,offset)
from verify_effect_signal import SOURCES as SIGNAL_SOURCES
from verify_effect_processing import (U32,MAP,CALL,Recording,Script as EffectScript,
    baseline,setword,put,EFFECTS,CONTROL,CONFIG,SAMPLES,ARENA,RAM,AUTOMATION,boundary_digest)
from verify_audio_task import Task

SOURCES=(*SIGNAL_SOURCES,'firmware/src/hyperrig_effect_parameter_support.c',
    'firmware/src/hyperrig_effect_construction.c','firmware/src/hyperrig_effect_configured_signal.c')
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),
        ('construction_services',U32),('construction_work',U32),('signal_blocks',U32)]

def byte_digest(value):
    if not isinstance(value,bytes):raise TypeError('unsupported boundary digest value')
    return {'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}

class Script(EffectScript):
    def __init__(self,mutations=(),audio=False):
        super().__init__();self.audio=audio;self.edits=mutations;self.seen={}
        from verify_audio_task import Script as AudioScript
        self.platform=AudioScript()
    def __call__(self,target,args,memory):
        from effect_processing_machine import SERVICES
        self.seen[target]=self.seen.get(target,0)+1
        result=self.platform(target,args,memory) if self.audio and (target not in SERVICES or target==0x01c04862) else super().__call__(target,args,memory)
        for expected,nth,address,value,width in self.edits:
            if expected==target and (nth==0 or self.seen[target]==nth):memory.write(address,value,width)
        return result

class Backend:
    def __init__(self,program,memory,mapped,script,alignment=0):
        self.mapped=mapped;self.arrays=[];self.storage=[]
        for data in memory:
            storage=(ctypes.c_uint8*(len(data)+alignment))();self.storage.append(storage)
            view=(ctypes.c_uint8*len(data)).from_address(ctypes.addressof(storage)+alignment);view[:]=data;self.arrays.append(view)
        self.tables={key:(ctypes.c_uint8*len(raw)).from_buffer_copy(raw) for key,raw in program.data.items()}
        self.script=script;self.calls=[];self.errors=[];self.borrowed=None;self.preparing=False
        self.io=IO(MAP(self.map),CALL(self.call),None,10000,1000000,100000)
    def map(self,opaque,address,size,writable):
        for (base,n),data in zip(self.mapped,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(data)+address-base
        if not writable:
            for key,(base,end) in STATIC.items():
                if base<=address<=address+size<=end:return ctypes.addressof(self.tables[key])+address-base
        return None
    def locate(self,address,size,writable):
        pointer=self.map(None,address,size,writable)
        if pointer is None and self.borrowed:pointer=self.borrowed.contents.map(self.borrowed.contents.opaque,address,size,writable)
        if pointer is None:raise ValueError(f'callback outside mapped configured storage {address:#x}')
        return pointer
    def read(self,address,size):return int.from_bytes(ctypes.string_at(self.locate(address,size,0),size),'little')
    def write(self,address,value,size):ctypes.memmove(self.locate(address,size,1),(value&((1<<(size*8))-1)).to_bytes(size,'little'),size)
    def snapshot(self):return tuple(bytes(data) for data in self.arrays)
    def call(self,opaque,target,args,count,borrowed):
        try:
            self.borrowed=borrowed;words=tuple(args[i] for i in range(count));before=self.snapshot()
            signature=boundary_digest(target,words,self,hashlib.sha256(b''.join(before)).hexdigest())
            value=self.script(target,words,self)&0xffffffff
            self.calls.append((target,words+(0,)*(12-count),before,self.snapshot(),value) if self.preparing else (target,words,signature))
            self.borrowed=None;return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Replay:
    def __init__(self,path,program):
        self.file=path.open('xb');self.count=0;self.file.write(b'HRFCS001');self.words(0,len(STATIC))
        for key,(base,end) in STATIC.items():self.words(base,end-base);self.file.write(program.data[key])
    def words(self,*values):self.file.write(struct.pack('<'+'I'*len(values),*(v&0xffffffff for v in values)))
    def writes(self,changes):
        self.words(len(changes))
        for address,value,size in changes:self.words(address,value&0xffffffff,value>>32,size)
    def case(self,session,mode,entry,args,status,value,before,after,events,task_before,task_after):
        self.words(mode,entry,len(args),*args,*([0]*(12-len(args))),status,value,
            session.backend.io.construction_services,session.backend.io.construction_work,session.backend.io.signal_blocks,
            session.chain,session.alignment,*task_before,*task_after,len(session.mapped))
        for (base,size),old,new in zip(session.mapped,before,after):self.words(base,size);self.file.write(old);self.file.write(new)
        self.writes(session.pending)
        self.words(len(events))
        for target,arguments,result,writes in events:
            # Constructor hooks expose a padded register vector; their verified
            # direct call-site ABI controls the actual event arity.
            arity=len(arguments)
            if mode==0:
                from effect_construction_machine import SERVICES
                arity=SERVICES[target];arguments=arguments[:arity]
            self.words(target,arity,*arguments,*([0]*(12-len(arguments))),result);self.writes(writes)
        self.count+=1
    def close(self):self.file.seek(8);self.words(self.count);self.file.close()

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectConfiguredSignalProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        self.lib.hyperrig_effect_configured_signal_prepare.argtypes=[U32,ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_configured_signal_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_configured_signal_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_configured_signal_audio_resume.argtypes=[ctypes.POINTER(Task),U32,U32,ctypes.POINTER(IO)]
        self.cases=self.chains=self.steps=self.blocks=self.preparations=self.audio_preparations=0
        self.visited=set();self.real={};self.services={};self.labels=[];self.exp_arguments=[];self.constructor_sites=[]
        self.digest=hashlib.sha256();self.replay=Replay(replay,self.program) if replay else None
    def session(self,memory,*,mapped=MAPPED,alignment=0,mutations=(),audio=False):
        self.chains+=1;return Session(self,memory,mapped,alignment,mutations,audio)

class Session:
    def __init__(self,corpus,memory,mapped,alignment,mutations,audio):
        self.corpus,self.mapped,self.chain,self.alignment=corpus,mapped,corpus.chains,alignment
        self.native=list(map(bytearray,memory));self.backend=Backend(corpus.program,memory,mapped,Script(mutations,audio),alignment)
        self.recording=Recording(Script(mutations,audio));self.pending=[];self.task=Task();self.audio=None
    def write(self,address,value,size=4):
        for (base,n),data in zip(self.mapped,self.native):
            if base<=address<=address+size<=base+n:
                put(data,address-base,value,size);self.backend.write(address,value,size)
                self.pending.append((address,value&((1<<(size*8))-1),size));break
        else:raise ValueError('parameter/input mutation escaped public maps')
        if self.audio:
            for i,byte in enumerate((value&((1<<(size*8))-1)).to_bytes(size,'little')):self.audio.memory[address+i]=byte
            for (base,n),data in zip(self.mapped,self.audio.public_memory):
                if base<=address<=address+size<=base+n:put(data,address-base,value,size);break
    def invoke(self,label,name,args,*,budget=100000):
        c=self.corpus;b=self.backend;b.io.signal_blocks=budget;b.preparing=name=='prepare'
        before=b.snapshot();call_start=len(b.calls);event_start=len(self.recording.events)
        task_before=tuple(getattr(self.task,key) for key,_ in Task._fields_);value=U32()
        if name=='prepare':
            paused=None if self.audio is None else (self.audio.pc,dict(self.audio.regs),list(self.audio.returns),repr(self.audio.frames),dict(self.audio.else_skips))
            expected=c.program.prepare(self.native,args[0],self.recording,mapped=self.mapped)
            status=c.lib.hyperrig_effect_configured_signal_prepare(args[0],ctypes.byref(b.io));mode=0;entry=CONSTRUCTOR
            c.preparations+=1;c.exp_arguments+=expected['exp_arguments'];c.constructor_sites+=expected['service_sites']
            if self.audio:
                carry_preparation_into_audio(self.audio,expected['memory']);c.audio_preparations+=1
                assert paused==(self.audio.pc,dict(self.audio.regs),list(self.audio.returns),repr(self.audio.frames),dict(self.audio.else_skips))
            calls=expected['calls'];steps=expected['steps'];blocks=0;visited=expected['visited'];real=expected['internal_calls']
        elif name=='audio':
            if self.audio is None:self.audio=c.program.audio.machine(self.native,self.recording)
            old_calls=len(self.audio.calls);old_steps=self.audio.steps;old_blocks=len(self.audio.blocks);old_real=len(self.audio.real_calls)
            expected=self.audio.resume(*args,block_budget=budget)
            status=c.lib.hyperrig_effect_configured_signal_audio_resume(ctypes.byref(self.task),*args,ctypes.byref(b.io));mode=3;entry=0
            expected['status']=expected['reason'];calls=expected['calls'][old_calls:];steps=expected['steps']-old_steps
            blocks=len(self.audio.blocks)-old_blocks;visited=expected['visited'];real=self.audio.real_calls[old_real:]
            assert tuple(getattr(self.task,key) for key,_ in Task._fields_)==expected['task'],(label,'task control')
        else:
            expected=c.program.execute(self.native,name,args,self.recording,block_budget=budget)
            if name=='stage':status=c.lib.hyperrig_effect_configured_signal_stage(*args,ctypes.byref(b.io));mode=2
            else:status=c.lib.hyperrig_effect_configured_signal_execute(ENTRIES[name],(U32*12)(*args),ctypes.byref(value),ctypes.byref(b.io));mode=1
            entry=ENTRIES[name];calls=expected['calls'];steps=expected['steps'];blocks=len(expected['blocks']);visited=expected['visited'];real=expected['real_calls']
            if not expected['status'] and name in ('individual','grouped'):assert value.value==expected['value'],(label,'scalar')
        assert status==expected['status'] and not b.errors,(label,'status',status,expected['status'],b.errors)
        if b.snapshot()!=expected['memory']:
            diff=[(hex(base+i),x,y) for (base,_),left,right in zip(self.mapped,expected['memory'],b.snapshot()) for i,(x,y) in enumerate(zip(left,right)) if x!=y]
            raise AssertionError((label,'public memory',diff[:16]))
        assert calls==b.calls[call_start:],(label,'service order or boundary state',calls,b.calls[call_start:])
        for old,new in zip(self.native,expected['memory']):old[:]=new
        c.cases+=1;c.steps+=steps;c.blocks+=blocks;c.visited|=visited;c.labels.append(label)
        for target in real:
            target=target[0] if isinstance(target,tuple) else target;c.real[target]=c.real.get(target,0)+1
        for target,*_ in calls:c.services[target]=c.services.get(target,0)+1
        c.digest.update(json.dumps((label,name,args,status,calls),default=byte_digest).encode())
        for data in expected['memory']:c.digest.update(data)
        if c.replay:c.replay.case(self,mode,entry,args,status,value.value,before,expected['memory'],self.recording.events[event_start:],
            task_before,tuple(getattr(self.task,key) for key,_ in Task._fields_))
        self.pending=[];return expected

KINDS={1:'gate',13:'allpass',38:'variable_filter'}
PARAMETERS={1:(-24,25,0,0,0,0,0),13:(15,40,35,0,30,0,0),38:(50,300,2500,40,30,1,70)}

def initialize(memory,effect,kind,seed=1,rate=48000,mode=0):
    rng=random.Random(seed)
    for i in range(192):setword(memory,effect+288+i,rng.randrange(256),1)
    for off,val,width in ((0,kind,1),(1,1,1),(2,1,1),(4,0,1),(6,mode,1),(10,0,1),(11,0,1),
        (84,ARENA+32000,4),(88,1024,4)):
        setword(memory,effect+off,val,width)
    setword(memory,CONFIG+8,rate);setword(memory,CONFIG+12,1200)
    for i,v in enumerate(PARAMETERS[kind]):setword(memory,effect+70+2*i,v,2)
    # Existing histories are either cold zeroes or raw carried data; the
    # constructor itself produces every coefficient used by subsequent calls.
    if seed%2:
        for off in range(288,340,4):setword(memory,effect+off,0)
    if kind==13:setword(memory,effect+296,0)
    if kind==38:
        for off in range(304,328,4):setword(memory,effect+off,0)

def direct(c):
    for kind,name in KINDS.items():
        for case in range(16):
            m=baseline(case);initialize(m,EFFECTS,kind,case,(24000,44100,48000,48077,96000)[case%5],(0,1,2,3,4,32)[case%6])
            s=c.session(m,alignment=case%4 if kind!=38 else 0);s.invoke(f'prepare {kind}/{case}','prepare',(EFFECTS,))
            if kind==38:s.invoke(f'actual filter coefficients {case}','dispatch',(EFFECTS,SAMPLES,32,1))
            counts=(4,32,516,1024,0x40000004) if kind==38 else (1,17,32,513,1024)
            s.invoke(f'constructed direct {kind}/{case}',name,(SAMPLES,counts[case%5],EFFECTS+288))

def smoke(c):
    for kind,name in KINDS.items():
        m=baseline(kind);initialize(m,EFFECTS,kind)
        s=c.session(m);s.invoke(f'smoke prepare {kind}','prepare',(EFFECTS,))
        if kind==38:s.invoke('smoke filter coefficients','dispatch',(EFFECTS,SAMPLES,32,1))
        s.invoke(f'smoke direct {kind}',name,(SAMPLES,32,EFFECTS+288))

def carried(c):
    for kind in KINDS:
        for case in range(8):
            m=baseline(case);initialize(m,EFFECTS,kind,case)
            setword(m,CONFIG+40,SAMPLES+2048);setword(m,CONFIG+44,SAMPLES+2048)
            setword(m,CONTROL+9,case%3*40,1)
            s=c.session(m)
            for step in range(6):
                index=(0,1)[step%2] if kind==1 else (0,1,2,4)[step%4] if kind==13 else (0,1,2,3,5,6)[step]
                value=(-40+step*5 if index==0 else 5+step*20) if kind==1 else (5+step*13 if kind==13 else (150+step*100 if index in (1,2) else step*7))
                s.write(EFFECTS+70+index*2,value,2)
                s.write(EFFECTS+10,step%3,1);s.write(EFFECTS+11,(step+case)%4,1)
                s.invoke(f'carried prepare {kind}/{case}/{step}','prepare',(EFFECTS,))
                s.invoke(f'carried individual {kind}/{case}/{step}','individual',(0,SAMPLES,(16,32,128)[step%3]))

def aliases(c):
    for kind,name in KINDS.items():
        for delta in (-64,-4,0,16,52,116,180):
            m=baseline(delta);initialize(m,EFFECTS,kind,delta)
            s=c.session(m);s.invoke(f'alias prepare {kind}/{delta}','prepare',(EFFECTS,))
            if kind==38:s.invoke(f'alias filter coefficients {delta}','dispatch',(EFFECTS,SAMPLES,32,1))
            s.invoke(f'actual coefficient alias {kind}/{delta}',name,(EFFECTS+288+delta,32,EFFECTS+288))
    # The constructor's common CFG+36 write may alias an effect field. Here it
    # aliases existing history/output storage while parameters remain valid.
    for kind in KINDS:
        m=baseline(kind);effect=CONFIG-288
        initialize(m,effect,kind,1);setword(m,CONFIG+8,48000)
        s=c.session(m);s.invoke(f'constructor shared CFG alias {kind}','prepare',(effect,))
        s.invoke(f'raw shared CFG alias {kind}',KINDS[kind],(SAMPLES,32,effect+288))

def boundaries(c):
    for kind,name in KINDS.items():
        for raw in (0,1,0xfffffff1,0xffffffff):
            m=baseline(raw);initialize(m,EFFECTS,kind)
            s=c.session(m);s.invoke(f'budget prepare {kind}/{raw}','prepare',(EFFECTS,))
            if kind==38:s.invoke(f'budget filter coefficients {raw}','dispatch',(EFFECTS,SAMPLES,32,1))
            s.invoke(f'constructed budget {kind}/{raw}',name,(SAMPLES,raw,EFFECTS+288),budget=2)
        for raw in (-32768,-128,-1,0,128,32767):
            m=baseline(raw);initialize(m,EFFECTS,kind)
            setword(m,EFFECTS+(72 if kind==13 else 76 if kind==38 else 70),raw,2)
            s=c.session(m);s.invoke(f'parameter edge {kind}/{raw}','prepare',(EFFECTS,))
            s.invoke(f'edge dispatcher {kind}/{raw}','dispatch',(EFFECTS,SAMPLES,32,1))
    builder_boundaries(c)

def builder_boundaries(c):
    # These two larger constructors remain explicitly scripted. Their callback
    # changes the type; a SECOND real preparation then produces the coefficients
    # for the selected recovered signal path. No synthetic coefficients enter it.
    for source_kind,target,kind in ((17,0x0202b838,13),(39,0x0202a872,1)):
        m=baseline(source_kind);initialize(m,EFFECTS,kind);setword(m,EFFECTS,source_kind,1)
        s=c.session(m,mutations=((target,1,EFFECTS,kind,1),(target,1,EFFECTS+72,12,2)))
        s.invoke(f'explicit builder mutation {source_kind}','prepare',(EFFECTS,))
        s.invoke(f'real preparation after builder mutation {kind}','prepare',(EFFECTS,))
        s.invoke(f'recovered signal after builder mutation {kind}',KINDS[kind],(SAMPLES,32,EFFECTS+288))

def api_checks(c):
    n=0;m=baseline();initialize(m,EFFECTS,13);b=Backend(c.program,m,MAPPED,Script());out=U32()
    args=(U32*12)(SAMPLES,16,EFFECTS+288)
    def check(expected,status):
        nonlocal n
        assert status==expected,(status,expected);n+=1
    check(-200,c.lib.hyperrig_effect_configured_signal_prepare(EFFECTS,None))
    check(-200,c.lib.hyperrig_effect_configured_signal_execute(ENTRIES['allpass'],args,ctypes.byref(out),None))
    check(-200,c.lib.hyperrig_effect_configured_signal_stage(0,SAMPLES,128,None))
    check(-200,c.lib.hyperrig_effect_configured_signal_audio_resume(None,1,1,None))
    no_map=IO(MAP(),b.io.call,None,0,100000,100)
    check(-200,c.lib.hyperrig_effect_configured_signal_prepare(EFFECTS,ctypes.byref(no_map)))
    check(-201,c.lib.hyperrig_effect_configured_signal_prepare(0x44440000,ctypes.byref(b.io)))
    check(-202,c.lib.hyperrig_effect_configured_signal_prepare(0x30000000,ctypes.byref(b.io)))
    before=b.snapshot();b.io.construction_work=0
    check(-203,c.lib.hyperrig_effect_configured_signal_prepare(EFFECTS,ctypes.byref(b.io)));assert b.snapshot()==before
    # Compare delegated partial writes against the unchanged construction API.
    from verify_effect_construction import IO as ConstructionIO,CALL as ConstructionCall
    c.lib.hyperrig_effect_construction_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(ConstructionIO)]
    for budget in (1,4,20,100,300):
        left=Backend(c.program,m,MAPPED,Script());right=Backend(c.program,m,MAPPED,Script())
        left.io.construction_work=budget;native_io=ConstructionIO(right.io.map,ConstructionCall(),None,10000,budget)
        a=c.lib.hyperrig_effect_configured_signal_prepare(EFFECTS,ctypes.byref(left.io))
        z=(U32*2)(0xdeadbeef,0xcafebabe)
        bstatus=c.lib.hyperrig_effect_construction_execute(CONSTRUCTOR,(U32*12)(EFFECTS),z,ctypes.byref(native_io))
        check(bstatus,a);assert left.snapshot()==right.snapshot()
        assert (a==0 and tuple(z)==(0,0)) or (a==-203 and tuple(z)==(0xdeadbeef,0xcafebabe))
    # A zero rate reaches a nonfinite exponential input after earlier stores.
    m=baseline();initialize(m,EFFECTS,1);setword(m,CONFIG+8,0);b=Backend(c.program,m,MAPPED,Script())
    check(-202,c.lib.hyperrig_effect_configured_signal_prepare(EFFECTS,ctypes.byref(b.io)))
    return n

def source_paths():
    from hyperrig.jieli import unpack_app
    # Include every locally loaded module and the dynamically loaded ISA files.
    paths=set(SOURCES)|{'tools/effect_configured_signal_machine.py','tools/verify_effect_configured_signal.py',
        'tools/build_effect_configured_signal.py','tests/effect_configured_signal_sanitize.c',
        'tests/test_effect_configured_signal_machine.py','research/input-manifest.json',
        'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md'}
    for name in ('s.py','b2.py','r.py'):paths.add('upstream/pi32v2-isa/tools/hwtest/semantics/'+name)
    for module in tuple(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
    pending=[ROOT/path for path in SOURCES];seen=set()
    while pending:
        path=pending.pop().resolve()
        if path in seen:continue
        seen.add(path)
        for include in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',path.read_text(),re.M):
            for candidate in (path.parent/include,ROOT/'firmware/include'/include):
                if candidate.is_file():paths.add(candidate.resolve().relative_to(ROOT).as_posix());pending.append(candidate);break
    return sorted(paths)

def report(c,args,sources):
    from hyperrig.jieli import unpack_app
    from dsp_audio_path_machine import TABLE,PRIOR_TABLE,RESET_CONFIGURATION
    app=c.program.app;code=c.program.code
    def binding(start,end):return {'start':start,'end_exclusive':end,'sha256':hashlib.sha256(app[offset(start):offset(end)]).hexdigest()}
    inherited={'capture_dispatch':(0x01c12bf2,0x01c12bf6),'gain_table':TABLE,
        'coefficient_selector':(PRIOR_TABLE,PRIOR_TABLE+10),'reset_configuration':RESET_CONFIGURATION,
        'task_registration':(0x02005250,0x0200525e),'resampling_taps':(0x0203be2c,0x0203be50)}
    static={name:binding(*span) for name,span in (STATIC|inherited).items()}
    windows={hex(pc):binding(pc,pc+record[1]) for pc,record in sorted(code.items())}
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    original_hash=hashlib.sha256(original).hexdigest()
    assert original_hash=='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    assert unpack_app(original)[2]['app.bin']==app
    mini=None
    if args.mini_image:
        raw=args.mini_image.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert sha=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        payload=unpack_app(raw)[2]['app.bin']
        for item in (*windows.values(),*static.values()):
            start,end=item['start'],item['end_exclusive'];assert payload[offset(start):offset(end)]==app[offset(start):offset(end)]
        mini={'image_sha256':sha,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    regions={'constructor':CONSTRUCTION_REGIONS['construct'],**SIGNAL_REGIONS}
    exp_max=max((bits&0x7fffffff for bits in c.exp_arguments),default=0)
    assert exp_max<=0x47800000,'reached original exponential input exceeds the declared finite domain'
    result={'schema':1,'project':'HyperRig','component':'reconstructed-effect-configured-signal','result':'pass',
        'integration_only':True,'new_original_functions':0,'functions':{},
        'original_image_sha256':original_hash,'decoded_image_sha256':hashlib.sha256(app).hexdigest(),
        'total_comparisons':c.cases,'retained_allocation_chains':c.chains,'actual_constructor_calls':c.preparations,
        'preparations_between_audio_observations':c.audio_preparations,'original_instruction_steps':c.steps,
        'original_signal_blocks':c.blocks,'c_only_guard_and_delegation_checks':api_checks(c),
        'sanitizer_replay_cases':c.replay.count if c.replay else 0,'source_sha256':sources,
        'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),'mini_v4_binding':mini,
        'outputs_state_and_ordered_services_sha256':c.digest.hexdigest(),
        'original_internal_entries':{hex(pc):n for pc,n in sorted(c.real.items())},
        'observed_external_services':{hex(pc):n for pc,n in sorted(c.services.items())},
        'constructor_external_sites':{hex(pc):{'target':target,'arity':arity} for pc,(target,arity) in c.program.external_sites.items()},
        'observed_constructor_external_sites':c.constructor_sites,
        'actual_constructor_exp_calls':len(c.exp_arguments),'largest_exp_magnitude_bits':exp_max,
        'joined_bodies':{name:binding(start,end)|{'decoded':sum(start<=pc<end for pc in code),
            'visited':sum(start<=pc<end for pc in c.visited),
            'unvisited':sorted(pc for pc in set(code)-c.visited if start<=pc<end)} for name,(start,end) in regions.items()},
        'static_data':static,'bound_instruction_windows':windows,
        'instruction_coverage':{'new_decoded':0,'new_visited':0,'unvisited_new':[],
            'all_decoded':len(code),'all_visited':len(set(code)&c.visited),'unvisited_all':sorted(set(code)-c.visited),
            'note':'This adds no native functions. Only this integration corpus execution is counted; earlier coverage is not added.'},
        'scripted_recovered_kernel_replacements':0,'new_static_data_ranges':[],
        'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['Preparation and processing are separate original entries on retained public maps, not a claimed native scheduler or constructor-to-task call edge.',
            'Type38 constructor controls feed the real dispatcher coefficient update before the raw filter uses those resulting coefficients.',
            'Initial histories and input samples are fixtures; no generated coefficient is replaced or overwritten by the harness.',
            'Two boundary witnesses explicitly script unrecovered type17/type39 builders before a second real preparation for type13/type1; their numerical bodies remain unrecovered.',
            'Constructor work/domain errors are API/delegation checks, not native error-return or fault-prefix equivalence.',
            'Remaining audio/output/platform services stay explicit; no physical audio or timing result is asserted.']}
    assert sources=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},'source bytes changed during comparison'
    return result

def routed(c):
    from verify_dsp_stage import baseline as stage_baseline
    for case in range(8):
        m=baseline(case);m[0][:]=stage_baseline(case)[0]
        for side in range(2):
            setword(m,CONTROL+14+side,3,1)
            for slot,kind in enumerate(KINDS):
                setword(m,CONTROL+348+side*10+slot,slot,1)
                initialize(m,EFFECTS+480*slot,kind,case)
                setword(m,EFFECTS+480*slot+4,slot%2+1 if case%2 else 0,1)
        mutations=((0x01c04862,2,EFFECTS+70,65512,2),(0x01c04862,3,EFFECTS+480+70,23,2)) if case%2 else ()
        if mutations:setword(m,0x01c34198,0x01c04862);setword(m,0x01c34444,1000000)
        s=c.session(m,mutations=mutations)
        for slot in range(3):s.invoke(f'stage initial prepare {case}/{slot}','prepare',(EFFECTS+480*slot,))
        for step in range(3):
            s.invoke(f'constructed stage {case}/{step}/left','stage',(0,SAMPLES,128))
            s.invoke(f'constructed stage {case}/{step}/right','stage',(1,SAMPLES,128))
            slot=step;s.write(EFFECTS+480*slot+72,(10+step*15 if slot<2 else 350),2)
            s.invoke(f'stage changed prepare {case}/{step}','prepare',(EFFECTS+480*slot,))

def audio(c):
    import verify_audio_task as task
    from verify_dsp_stage import baseline as stage_baseline
    for case in range(6):
        memory=task.baseline(case,mode=case%2+1);r=memory[0];stage=stage_baseline(case)[0]
        for start,size in ((EFFECTS,7680),(AUTOMATION,3584),(CONTROL,416),(CONFIG,56),(0x01c2f3a0,1536),(0x01c32fa0,144)):
            r[start-RAM:start-RAM+size]=stage[start-RAM:start-RAM+size]
        for side in range(2):
            put(r,CONTROL-RAM+14+side,3,1)
            for slot,kind in enumerate(KINDS):
                put(r,CONTROL-RAM+348+side*10+slot,slot,1);initialize(memory,EFFECTS+480*slot,kind,case)
        s=c.session(memory,mapped=task.MAPPED,audio=True)
        for slot in range(3):s.invoke(f'audio initial prepare {case}/{slot}','prepare',(EFFECTS+480*slot,))
        for step in range(4):
            s.invoke(f'configured audio {case}/{step}','audio',(1,1))
            if step<3:
                s.write(EFFECTS+480*step+72,40+step*100,2)
                s.invoke(f'paused audio prepare {case}/{step}','prepare',(EFFECTS+480*step,))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--suite',default='all');p.add_argument('--development-rebuild',action='store_true')
    p.add_argument('--output',type=Path);p.add_argument('--mini-image',type=Path);p.add_argument('--sanitizer-corpus',type=Path);a=p.parse_args()
    if a.development_rebuild:
        if a.library.parent.name!='reverse-effect-configured-signal-development-01':p.error('use the unfrozen configured-signal development directory')
        a.library.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-g','-fPIC','-shared','-Ifirmware/include',*SOURCES,'-o',str(a.library)],check=True)
    if a.output and a.output.exists():p.error('choose a fresh report path')
    if a.sanitizer_corpus and a.sanitizer_corpus.exists():p.error('choose a fresh replay path')
    c=Corpus(a.library,a.sanitizer_corpus)
    # Import the delegate guard's ctypes schema before capturing sources.
    from verify_effect_construction import IO as ConstructionIO
    sources={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()} if a.output else {}
    parts={'smoke':smoke,'direct':direct,'carried':carried,'aliases':aliases,'boundaries':boundaries,'builders':builder_boundaries,'routed':routed,'audio':audio}
    if a.suite=='all':
        for name in ('direct','carried','aliases','boundaries','routed','audio'):parts[name](c);print(name,c.cases,flush=True)
    else:parts[a.suite](c)
    if c.replay:c.replay.close()
    if a.output:a.output.write_text(json.dumps(report(c,a,sources),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'pass','comparisons':c.cases,'preparations':c.preparations,'steps':c.steps,'blocks':c.blocks,'visited':len(c.visited)}))

if __name__=='__main__':main()
