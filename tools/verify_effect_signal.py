"""Independent original-instruction comparisons for recovered signal leaves."""
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
from effect_signal_machine import (EffectSignalProgram,EffectSignalAudioProgram,REGIONS,ENTRIES,
    MAPPED,STATIC,ROOT,offset)
from verify_effect_processing import (SOURCES as PROCESSING_SOURCES,CBackend,Script,Recording,
    U32,MAP,CALL,baseline,setword,put,EFFECTS,CONTROL,CONFIG,SAMPLES,ARENA,RAM,AUTOMATION,boundary_digest)

SOURCES=(*PROCESSING_SOURCES,'firmware/src/hyperrig_effect_signal.c')
class IO(ctypes.Structure):_fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),('block_budget',U32)]

class Replay:
    def __init__(self,path,program):
        self.file=path.open('xb');self.count=0;self.file.write(b'HRFXS001');self.words(0,len(STATIC))
        for name,(start,end) in STATIC.items():self.words(start,end-start);self.file.write(program.data[name])
    def words(self,*values):self.file.write(struct.pack('<'+'I'*len(values),*(v&0xffffffff for v in values)))
    def case(self,mode,entry,args,status,value,before,after,events,*,budget=100000,mapped=MAPPED,
             task_before=(0,0,0,0),task_after=(0,0,0,0)):
        self.words(mode,entry,len(args),*args,*([0]*(12-len(args))),status,value,budget,*task_before,*task_after,len(mapped))
        for (base,size),old,new in zip(mapped,before,after):self.words(base,size);self.file.write(old);self.file.write(new)
        self.words(len(events))
        for target,arguments,result,writes in events:
            self.words(target,len(arguments),*arguments,*([0]*(12-len(arguments))),result,len(writes))
            for address,data,width in writes:self.words(address,data&0xffffffff,data>>32,width)
        self.count+=1
    def close(self):self.file.seek(8);self.words(self.count);self.file.close()

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectSignalProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        self.lib.hyperrig_effect_signal_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_signal_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.cases=self.steps=self.blocks=0;self.visited=set();self.real_calls={};self.digest=hashlib.sha256()
        self.replay=Replay(replay,self.program) if replay else None;self.labels=[];self.service_counts={}
    def compare(self,label,memory,name,args,*,budget=100000,mutations=(),returns=(),clocks=()):
        script=Recording(Script(mutations,returns,clocks))
        try:r=self.program.execute(memory,name,args,script,block_budget=budget)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        b=CBackend(self.program,memory,Script(mutations,returns,clocks));io=IO(b.io.map,b.io.call,None,budget);out=U32()
        status=self.lib.hyperrig_effect_signal_stage(*args,ctypes.byref(io)) if name=='stage' else self.lib.hyperrig_effect_signal_execute(ENTRIES[name],(U32*12)(*args),ctypes.byref(out),ctypes.byref(io))
        if status!=r['status'] or b.errors:raise AssertionError((label,'status',status,r['status'],b.errors))
        if not status and name in ('individual','grouped') and out.value!=r['value']:raise AssertionError((label,'scalar'))
        for (base,_),expected,actual in zip(MAPPED,r['memory'],b.snapshot()):
            if expected!=actual:
                differences=[i for i,(x,y) in enumerate(zip(expected,actual)) if x!=y];i=differences[0]&~3
                raise AssertionError((label,'memory',hex(base+i),expected[i:i+16].hex(),actual[i:i+16].hex(),len(differences)))
        if r['calls']!=b.calls:raise AssertionError((label,'callbacks',r['calls'],b.calls))
        self.cases+=1;self.steps+=r['steps'];self.blocks+=len(r['blocks']);self.visited|=r['visited']
        self.labels.append(label)
        for pc in r['real_calls']:self.real_calls[pc]=self.real_calls.get(pc,0)+1
        for target,*_ in r['calls']:self.service_counts[target]=self.service_counts.get(target,0)+1
        self.digest.update(json.dumps((label,args,budget,r['status'],r['calls'])).encode())
        for data in r['memory']:self.digest.update(data)
        if self.replay:self.replay.case(name=='stage',ENTRIES[name],args,status,out.value,memory,r['memory'],script.events,budget=budget)
        return r['memory']

def fixture(name,seed):
    m=baseline(seed);rng=random.Random(seed);state=ARENA+4096
    for i in range(256):setword(m,state-256+i*4,rng.getrandbits(32))
    if name=='allpass':
        for i in range(33):setword(m,state+52+i*4,(i*0x02468acf-0x30000000)&0xffffffff)
    return m,state

def direct(c):
    for name in REGIONS:
        counts=(1,15,16,17,31,32,127,128,513,1024) if name!='variable_filter' else (4,8,16,28,32,128,516,1024,0x40000004,0x80000020,0xc0000080)
        for case in range(60):
            m,state=fixture(name,case);count=counts[case%len(counts)]
            if case%5==0:
                for i in range(1024):setword(m,SAMPLES+4*i,(0,0x80000000,0x7fffffff,1,-1)[case//5%5])
            c.compare(f'direct {name}/{case}',m,name,(SAMPLES,count,state))

def aliases(c):
    for name in REGIONS:
        for delta in (-64,-4,0,4,16,32,48,52,116,180,184):
            m,state=fixture(name,delta);samples=state+delta
            c.compare(f'overlap {name}/{delta}',m,name,(samples,32,state))
        m,state=fixture(name,891)
        for block in range(12):
            m=c.compare(f'carried {name}/{block}',m,name,(SAMPLES,(16,32,128)[block%3],state))
        for offset in (1,2,3):
            m,state=fixture(name,offset)
            c.compare(f'byte tokens {name}/{offset}',m,name,(SAMPLES+offset,32,state+offset))

def gate_edges(c):
    for gain in (0,32768,32769,65536):
        for level in (0,1000,1001,2000,2001,0x80000000):
            for smoothing in (0,65536):
                m,state=fixture('gate',level)
                for off,value in ((0,2000),(4,1000),(8,65536),(12,65536),(16,smoothing),(20,level),(24,gain)):
                    setword(m,state+off,value)
                for i in range(32):setword(m,SAMPLES+4*i,level)
                c.compare(f'gate threshold {gain}/{level}/{smoothing}',m,'gate',(SAMPLES,32,state))

def budgets(c):
    for name in REGIONS:
        for count in (0,1,3,16,129,513,0x40000000,0x80000000,0xfffffff0,0xfffffff1,0xffffffff):
            for budget in (0,1,3):
                m,state=fixture(name,count)
                c.compare(f'budget prefix {name}/{count}/{budget}',m,name,(SAMPLES,count,state),budget=budget)

def configure_effect(memory,slot,kind,seed):
    """Synthetic initialized parameters; this is not a constructor handoff."""
    r=memory[0];effect=EFFECTS+slot*480;p=effect+288;rng=random.Random(seed+kind)
    for i in range(48):put(r,p-RAM+4*i,rng.randrange(-1<<20,1<<20))
    for off,value in ((0,kind),(1,1),(2,1),(10,seed%3),(11,seed%4)):
        put(r,effect-RAM+off,value,1)
    if kind==1:
        fields={0:200000,4:100000,8:50000,12:12000,16:30000,20:1<<20,24:65536}
    elif kind==13:
        fields={0:seed*0x413f7391,4:0x01428600,8:0x10000000,12:15000,16:0,188:0}
        fields.update({52+i*4:0x08000000+i*0x01800000 for i in range(33)})
    else:
        fields={16:0,40:1<<20,44:0,48:1<<22,52:1<<21,56:4,60:40000,64:12000,
            68:1<<25,72:1<<26,76:1<<24,80:300,84:2000,88:50000,92:-300000,96:100000,100:1<<28,120:seed%3*1000}
    for off,value in fields.items():put(r,p-RAM+off,value)

def joined(c):
    for kind in (1,13,38):
        for case in range(24):
            m,state=fixture('allpass' if kind==13 else 'gate' if kind==1 else 'variable_filter',case)
            state_bytes=m[2][state-ARENA:state-ARENA+192]
            m[0][EFFECTS+288-MAPPED[0][0]:EFFECTS+480-MAPPED[0][0]]=state_bytes
            for address,value,width in ((EFFECTS,kind,1),(EFFECTS+1,1,1),(EFFECTS+2,1,1),
                (EFFECTS+10,case%3,1),(EFFECTS+11,case%4,1),(CONFIG+40,SAMPLES+2048,4),
                (CONFIG+44,SAMPLES+2048,4),(CONTROL+9,case%2*50,1),(CONTROL+268,50,1),(CONTROL+284,50,1)):
                setword(m,address,value,width)
            if kind==13:setword(m,EFFECTS+476,0);setword(m,EFFECTS+304,0)
            c.compare(f'actual individual {kind}/{case}',m,'individual',(0,SAMPLES,(16,32,128)[case%3]))
    from verify_dsp_stage import baseline as stage_baseline
    for case in range(12):
        m=baseline(case);m[0][:]=stage_baseline(case)[0]
        setword(m,CONTROL+14,3,1)
        for slot,kind in enumerate((1,13,38)):
            setword(m,CONTROL+348+slot,slot,1);setword(m,EFFECTS+slot*480,kind,1)
            setword(m,EFFECTS+slot*480+4,0,1)
            configure_effect(m,slot,kind,case)
        c.compare(f'actual stage {case}',m,'stage',(0,SAMPLES,128))
    for case in range(12):
        m=baseline(case);setword(m,ARENA,0x00020100)
        for slot,kind in enumerate((1,13,38)):
            configure_effect(m,slot,kind,case);setword(m,EFFECTS+slot*480+6,1,1)
        c.compare(f'actual resampling group {case}',m,'grouped',(ARENA,3,SAMPLES,(16,32,128)[case%3]))
    for kind in (1,13,38):
        for case in range(6):
            m=baseline(case);configure_effect(m,0,kind,case)
            setword(m,0x01c34198,0x01c04862);setword(m,0x01c34444,1000000)
            setword(m,CONFIG+40,SAMPLES+2048);setword(m,CONFIG+44,SAMPLES+2048)
            c.compare(f'callback parameter mutation {kind}/{case}',m,'individual',(0,SAMPLES,32),
                mutations=((1,EFFECTS+300,10000+case*2000,4),(2,EFFECTS+292,case*0x10ff0055,4)),clocks=(100,200,300))


def audio_corpus(c):
    import verify_audio_task as audio
    from verify_dsp_stage import baseline as stage_baseline
    from effect_processing_machine import SERVICES
    program=getattr(c,'audio_program',None) or EffectSignalAudioProgram()
    c.lib.hyperrig_effect_signal_audio_resume.argtypes=[ctypes.POINTER(audio.Task),U32,U32,ctypes.POINTER(IO)]
    class JoinedScript(audio.Script):
        def __init__(self):super().__init__();self.effects=Script()
        def __call__(self,target,args,memory):
            if target in SERVICES and target!=0x01c04862:return self.effects(target,args,memory)
            return super().__call__(target,args,memory)
    entries=private_entries=0
    for case in range(12):
        memory=audio.baseline(case,mode=case%2+1);r=memory[0];stage=stage_baseline(case)[0]
        for start,size in ((EFFECTS,7680),(AUTOMATION,3584),(CONTROL,416),(CONFIG,56),(0x01c2f3a0,1536),(0x01c32fa0,144)):
            r[start-RAM:start-RAM+size]=stage[start-RAM:start-RAM+size]
        for side in range(2):
            put(r,CONTROL-RAM+14+side,3,1)
            for slot in range(3):
                p=EFFECTS-RAM+slot*480;put(r,CONTROL-RAM+348+side*10+slot,slot,1)
                kind=(1,13,38)[slot]
                put(r,p,kind,1);put(r,p+4,0 if case<4 else slot%2+1,1)
                configure_effect(memory,slot,kind,case)
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
        io=IO(MAP(mapping),CALL(service),None,100000);previous_steps=0
        for segment in range(3):
            before=state.snapshot();task_before=tuple(getattr(task,k) for k,_ in audio.Task._fields_);event_start=len(recording.events)
            expected=native.resume(1,1);status=c.lib.hyperrig_effect_signal_audio_resume(ctypes.byref(task),1,1,ctypes.byref(io))
            if errors or status!=expected['reason']:raise AssertionError(('audio status',case,segment,status,expected['reason'],errors))
            assert tuple(getattr(task,k) for k,_ in audio.Task._fields_)==expected['task'],('audio control',case,segment)
            if state.snapshot()!=expected['memory']:
                differences=[(hex(base+i),x,y) for (base,_),a,b in zip(audio.MAPPED,state.snapshot(),expected['memory']) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
                raise AssertionError(('audio memory',case,segment,differences[:16]))
            if calls!=expected['calls']:raise AssertionError(('audio services',case,segment,calls,expected['calls']))
            c.cases+=1;c.labels.append(f'audio {case}/{segment}');c.visited|=expected['visited'];c.steps+=expected['steps']-previous_steps;previous_steps=expected['steps']
            c.digest.update(json.dumps(('audio',case,segment,expected['task'],expected['calls'])).encode())
            for data in expected['memory']:c.digest.update(data)
            if c.replay:c.replay.case(2,0,(1,1),status,0,before,expected['memory'],recording.events[event_start:],mapped=audio.MAPPED,
                task_before=task_before,task_after=expected['task'])
        entries+=sum((call[0] if isinstance(call,tuple) else call) in {bounds[0] for bounds in REGIONS.values()} for call in native.real_calls)
        c.blocks+=len(native.blocks)
        for target,*_ in calls:c.service_counts[target]=c.service_counts.get(target,0)+1
        private_entries+=sum(target==0x01c18f90 for target,_,_ in calls)
    if not entries:raise AssertionError('audio never entered a signal leaf')

    c.audio_program=program;c.audio_entries=entries;c.audio_private_entries=private_entries

def api_checks(c):
    """Only C API rejection is checked here, not invented native error returns."""
    count=0;m,state=fixture('gate',7);b=CBackend(c.program,m,Script());out=U32()
    args=(U32*12)(SAMPLES,16,state);io=IO(b.io.map,b.io.call,None,100)
    def check(expected,entry=ENTRIES['gate'],arguments=args,output=ctypes.byref(out),view=ctypes.byref(io)):
        nonlocal count
        status=c.lib.hyperrig_effect_signal_execute(entry,arguments,output,view)
        assert status==expected,(entry,status,expected);count+=1
    check(-200,arguments=None);check(-200,output=None);check(-200,view=None)
    missing_map=IO(MAP(),b.io.call,None,100);check(-200,view=ctypes.byref(missing_map))
    check(-202,entry=0xdeadbeef)
    for name in REGIONS:
        entry=ENTRIES[name]
        check(-201,entry,arguments=(U32*12)(SAMPLES,16,0x44440000))
        check(-202,entry,arguments=(U32*12)(SAMPLES,16,0x30000000))
        check(-202,entry,arguments=(U32*12)(SAMPLES,16,0xfffffff6 if name=='allpass' else 0xfffffffe))
        check(-202,entry,arguments=(U32*12)(0x30000000,16,state))
        check(-202,entry,arguments=(U32*12)(0xfffffffe,16,state))
    no_call=IO(b.io.map,CALL(),None,100)
    check(0,view=ctypes.byref(no_call))
    setword(m,EFFECTS,5,1);b2=CBackend(c.program,m,Script());no_call.map=b2.io.map
    check(-200,ENTRIES['dispatch'],arguments=(U32*12)(EFFECTS,SAMPLES,16,1),view=ctypes.byref(no_call))
    return count

def source_paths():
    from verify_effect_processing import source_paths as previous
    from hyperrig.jieli import unpack_app  # Imported before the initial manifest is captured.
    paths=set(previous())|set(SOURCES)|{
        'firmware/include/hyperrig/hyperrig_effect_signal.h','tools/effect_signal_machine.py',
        'tools/verify_effect_signal.py','tools/build_effect_signal.py',
        'tests/test_effect_signal_machine.py','tests/effect_signal_sanitize.c'}
    return sorted(paths)

def report(c,args,sources):
    from effect_processing_machine import SERVICES
    from dsp_audio_path_machine import TABLE,PRIOR_TABLE,RESET_CONFIGURATION
    from hyperrig.jieli import unpack_app
    app=c.program.app;code=dict(c.program.code)
    if hasattr(c,'audio_program'):code.update(c.audio_program.code)
    new={pc for pc in code if any(start<=pc<end for start,end in REGIONS.values())}
    def binding(start,end):return {'start':start,'end_exclusive':end,
        'sha256':hashlib.sha256(app[offset(start):offset(end)]).hexdigest()}
    inherited={'capture_dispatch':(0x01c12bf2,0x01c12bf6),'gain_table':TABLE,
        'coefficient_selector':(PRIOR_TABLE,PRIOR_TABLE+10),'reset_configuration':RESET_CONFIGURATION,
        'task_registration':(0x02005250,0x0200525e),'resampling_taps':(0x0203be2c,0x0203be50)}
    static={name:binding(*bounds) for name,bounds in (dict(STATIC)|inherited).items()}
    windows={hex(pc):binding(pc,pc+record[1]) for pc,record in sorted(code.items())}
    original=hashlib.sha256((ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()).hexdigest()
    assert original=='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    mini=None
    if args.mini_image:
        raw=args.mini_image.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert sha=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        mini_app=unpack_app(raw)[2]['app.bin']
        for item in (*static.values(),*windows.values()):
            start,end=item['start'],item['end_exclusive']
            assert mini_app[offset(start):offset(end)]==app[offset(start):offset(end)],hex(start)
        mini={'image_sha256':sha,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    result={'schema':1,'project':'HyperRig','component':'reconstructed-effect-signal','result':'pass',
        'original_image_sha256':original,'decoded_image_sha256':hashlib.sha256(app).hexdigest(),
        'total_comparisons':c.cases,'original_instruction_steps':c.steps,'original_signal_blocks':c.blocks,
        'c_only_guard_checks':api_checks(c),'sanitizer_replay_cases':c.replay.count if c.replay else 0,
        'source_sha256':sources,'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),
        'mini_v4_binding':mini,'outputs_state_and_ordered_services_sha256':c.digest.hexdigest(),
        'actual_audio_signal_entries':getattr(c,'audio_entries',0),
        'original_internal_entries':{hex(p):n for p,n in sorted(c.real_calls.items())},
        'observed_external_services':{hex(p):n for p,n in sorted(c.service_counts.items())},
        'functions':{name:binding(start,end)|{'instructions':sum(start<=pc<end for pc in new),
            'visited':sum(start<=pc<end for pc in c.visited),'unvisited':sorted(pc for pc in new-c.visited if start<=pc<end)}
            for name,(start,end) in REGIONS.items()},
        'static_data':static,'bound_instruction_windows':windows,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),'unvisited_new':sorted(new-c.visited),
            'all_decoded':len(code),'all_visited':len(set(code)&c.visited),'unvisited_all':sorted(set(code)-c.visited),
            'note':'Only actual execution in this corpus is counted. Previous report coverage is not added.'},
        'explicit_effect_service_abis':{hex(p):n for p,n in SERVICES.items() if p not in new},
        'scripted_recovered_kernel_replacements':0,'new_static_data_ranges':[],
        'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['The numerical leaves execute on synthetic mutable parameter/history bytes. Their constructors are not executed in this corpus.',
            'Audio task/stage/dispatcher joins execute original software; remaining platform, output and other numerical services stay explicit.',
            'The public block budget limits execution. Exhaustion compares the exact public-memory prefix, not a native return or resumable task observation.',
            'Missing-map errors preserve preceding C writes but are not claimed as native fault-prefix equivalence.',
            'All loaded but unvisited original instruction addresses remain listed; this is not an overall firmware completion percentage.']}
    assert sources=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'sources changed during comparison'
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--suite',default='all');p.add_argument('--development-rebuild',action='store_true')
    p.add_argument('--output',type=Path);p.add_argument('--mini-image',type=Path);p.add_argument('--sanitizer-corpus',type=Path);a=p.parse_args()
    if a.development_rebuild:
        if a.library.parent.name!='reverse-effect-signal-development-01':p.error('use the unfrozen signal development directory')
        a.library.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-g','-shared','-fPIC','-Ifirmware/include',*SOURCES,'-o',str(a.library)],check=True)
    if a.output and a.output.exists():p.error('choose a fresh report path')
    if a.sanitizer_corpus and a.sanitizer_corpus.exists():p.error('choose a fresh replay path')
    c=Corpus(a.library,a.sanitizer_corpus);c.audio_program=EffectSignalAudioProgram()
    sources={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()} if a.output else {}
    parts={'direct':direct,'aliases':aliases,'budgets':budgets,'gate_edges':gate_edges,'joined':joined,'audio':audio_corpus}
    if a.suite=='all':
        for name,part in parts.items():part(c);print(name,c.cases,flush=True)
    else:parts[a.suite](c)
    new={pc for pc in c.program.code if any(start<=pc<end for start,end in REGIONS.values())}
    if c.replay:c.replay.close()
    if a.output:a.output.write_text(json.dumps(report(c,a,sources),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pass':True,'comparisons':c.cases,'steps':c.steps,'blocks':c.blocks,'new_visited':len(new&c.visited),
        'new_decoded':len(new),'missing_new':len(new-c.visited)}))

if __name__=='__main__':main()
