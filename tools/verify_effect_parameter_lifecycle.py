"""Compare joined parameter/resource execution against complete original bodies."""
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
import verify_effect_parameters as parent
from verify_effect_parameters import (U32, MAP, CALL, IO, Borrowed, ROOT, PINNED, DECODED, MINI,
    initial, setword, put, EFFECTS, CONTROL, CONFIG, AUTOMATION, PROPOSED, PREVIOUS)
from effect_parameter_lifecycle_machine import (EffectParameterLifecycleProgram,
    REGIONS, PARAMETER_REGIONS, RESOURCE_REGIONS, DIRECT_RESOURCES, ENTRY_POINTS,
    MAPPED, RAM, SAMPLES, ARENA, PRIVATE, region_bytes)

SOURCES=tuple(path for path in parent.SOURCES if path!='firmware/src/hyperrig_effect_parameters.c')+(
    'firmware/src/hyperrig_effect_parameter_resources.c','firmware/src/hyperrig_effect_parameter_lifecycle.c')
ALLOCATOR, RELEASE, MODE = 0x41000100,0x41000104,0x41000108
OLD, NEW, RESTORED = ARENA,ARENA+32768,ARENA+98304
PARENT_SOURCE='firmware/src/hyperrig_effect_parameters.c'
PARENT_SOURCE_SHA='544d3eb301f8cc7c930ebe3cae9b4636edd20958620dda8024b894dad9b2af4b'
DERIVATIVE_SOURCE='firmware/src/hyperrig_effect_parameter_lifecycle.c'
DIRECT_SUBSTITUTIONS=((1,'01c05ec6'),(3,'0202edb8'),(5,'0202ee3c'),(1,'0202eeba'),
    (1,'0202eefa'),(2,'0202efe2'),(1,'0202f014'),(3,'0202f02e'))


def check_derivative(original=None,derived=None):
    original=(ROOT/PARENT_SOURCE).read_text() if original is None else original
    derived=(ROOT/DERIVATIVE_SOURCE).read_text() if derived is None else derived
    if hashlib.sha256(original.encode()).hexdigest()!=PARENT_SOURCE_SHA:
        raise ValueError('parameter03 source differs from the frozen derivative input')
    start='/* LIFECYCLE_RESOURCE_BRIDGE_BEGIN\n';end='/* LIFECYCLE_RESOURCE_BRIDGE_END */\n\n'
    if derived.count(start)!=1 or derived.count(end)!=1:raise ValueError('lifecycle bridge boundaries changed')
    a,b=derived.index(start),derived.index(end)+len(end)
    restored=(derived[:a]+derived[b:]).replace('hyperrig_effect_parameter_lifecycle','hyperrig_effect_parameters')
    counts={}
    for arity,target in DIRECT_SUBSTITUTIONS:
        old=f'CALL{arity}(a,0x{target},';new=f'RESOURCE{arity}(a,0x{target},'
        counts['0x'+target]=restored.count(new)
        if not counts['0x'+target] or original.count(old)!=counts['0x'+target]:
            raise ValueError('direct lifecycle substitution count changed')
        restored=restored.replace(new,old)
    if restored!=original:raise ValueError('lifecycle derivative differs beyond approved direct call substitutions')
    return {'frozen_parent_source':PARENT_SOURCE,'parent_source_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'derived_source':DERIVATIVE_SOURCE,'direct_call_substitutions':counts,
        'permitted_changes':['distinct public symbol/header/type names','one explicit resource bridge',
            'eight known direct resource targets at nineteen original call sites'],
        'original_semantic_bodies_unchanged':True}


class Script:
    """Only unresolved services are supplied; resource arithmetic executes for real."""
    def __init__(self,plan=None,mutations=()):
        self.plan=plan or {};self.mutations=mutations;self.seen={};self.responses=[]
    def __call__(self,target,args,m):
        occurrence=self.seen.get(target,0);self.seen[target]=occurrence+1
        if target==0x0202cf62:
            for index,value in self.plan.get('derived',()):m.write(args[0]+288+4*index,value,4)
        if target in (0x02028cb2,0x02028de8):value=1000
        elif target==0x01c04862:value=123456+137*sum(self.seen.values())
        else:value=0
        override=self.plan.get(target)
        if override is not None:value=override[min(occurrence,len(override)-1)] if isinstance(override,(tuple,list)) else override
        for at,n,address,replacement,width in self.mutations:
            if target==at and (n<0 or occurrence==n):m.write(address,replacement,width)
        value&=0xffffffff;self.responses.append(value);return value


class Backend(parent.Backend):
    def __init__(self,program,memory,script,expected):
        super().__init__(program,memory,script);self.expected=expected
    def call(self,opaque,target,arguments,count,borrowed):
        try:
            args=tuple(arguments[i] for i in range(count))+(0,)*(12-count)
            expected=self.expected[len(self.calls)]
            if (target,args)!=(expected[0],expected[1]):raise ValueError('unexpected lifecycle service before callback')
            self.borrowed=borrowed;before=self.snapshot()
            private_before=tuple((address,ctypes.string_at(self.locate(address,len(data),0),len(data)))
                for address,data in expected[4])
            value=self.script(target,args,self)
            private_after=tuple((address,ctypes.string_at(self.locate(address,len(data),0),len(data)))
                for address,data in expected[5])
            self.calls.append((target,args,before,self.snapshot(),private_before,private_after));self.sites.append((target,count))
            self.borrowed=None;return value
        except Exception as error:self.errors.append(str(error));self.borrowed=None;return 0


class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectParameterLifecycleProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        for name in ('execute','scene','stage'):
            setattr(self.lib,'hyperrig_effect_parameters_'+name,getattr(self.lib,'hyperrig_effect_parameter_lifecycle_'+name))
        self.lib.hyperrig_effect_parameters_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_scene.argtypes=[U32,U32,ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.replay=replay;self.counts={};self.steps=0;self.coverage=set();self.real_calls={};self.resource_sites={}
        self.services={};self.carried=self.mutating=self.private=self.replays=0;self.digest=hashlib.sha256()
    def compare(self,label,memory,name,args,plan=None,mutations=(),carried=False,argument_address=None):
        script=Script(plan,mutations)
        try:native=self.program.execute(memory,name,args,boundary=script)
        except Exception as error:raise AssertionError(f'{label}: native execution {error}') from error
        c=Backend(self.program,memory,Script(plan,mutations),native['calls']);out=(U32*2)(0xdeadbeef,0xcafebabe)
        entry=ENTRY_POINTS[name]
        if name=='stage':status=self.lib.hyperrig_effect_parameters_stage(*args,ctypes.byref(c.io));out[:]=[0,0]
        elif name.startswith('scene_'):
            status=self.lib.hyperrig_effect_parameters_scene(entry,args[0] if args else 0,out,ctypes.byref(c.io));out[1]=0
        else:
            words=ctypes.cast(c.locate(argument_address,48,0),ctypes.POINTER(U32)) if argument_address else (U32*12)(*args)
            status=self.lib.hyperrig_effect_parameters_execute(entry,words,out,ctypes.byref(c.io))
        if status or c.errors:raise AssertionError((label,'C status',status,c.errors))
        scalar=name not in ('stage','scene_select','scene_flush')
        if out[1] or scalar and out[0]!=native['value']:raise AssertionError((label,'result',hex(out[0]),hex(native['value'])))
        if c.snapshot()!=native['memory']:
            changes=[(hex(base+i),x,y) for (base,_),a,b in zip(MAPPED,native['memory'],c.snapshot())
                for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            raise AssertionError((label,'memory native/C',changes[:24]))
        if c.calls!=native['calls']:
            brief=lambda calls:[(hex(t),args[:6],hashlib.sha256(b''.join(before)).hexdigest()[:12],
                hashlib.sha256(b''.join(after)).hexdigest()[:12],p0,p1) for t,args,before,after,p0,p1 in calls]
            raise AssertionError((label,'services native/C',brief(native['calls']),brief(c.calls)))
        if c.sites!=[(t,n) for _,t,n in native['service_sites']]:raise AssertionError((label,'service arity'))
        self.counts[name]=self.counts.get(name,0)+1;self.steps+=native['steps'];self.coverage|=native['visited']
        self.carried+=bool(carried);self.mutating+=bool(mutations);self.private+=len(native['private_events'])
        for target in native['real_calls']:self.real_calls[target]=self.real_calls.get(target,0)+1
        for site,target in native['resource_sites']:self.resource_sites[(site,target)]=self.resource_sites.get((site,target),0)+1
        for target,*_ in native['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<I',out[0]))
        for data in native['memory']:self.digest.update(data)
        for target,words,before,after,p0,p1 in native['calls']:
            self.digest.update(struct.pack('<13I',target,*words))
            for data in (*before,*after):self.digest.update(data)
            for address,data in (*p0,*p1):self.digest.update(struct.pack('<I',address));self.digest.update(data)
        if self.replay:self.write_replay(memory,name,args,native,script.responses,scalar,argument_address);self.replays+=1
        return native['memory']
    def write_replay(self,memory,name,args,native,responses,scalar,argument_address):
        stream=self.replay
        stream.write(struct.pack('<18I',ENTRY_POINTS[name],*(tuple(args)+(0,)*(12-len(args))),int(scalar),
            native['value'] if scalar else 0,len(native['calls']),len(self.program.static_regions),argument_address or 0))
        for data in memory:stream.write(data)
        for key,(start,end) in self.program.static_regions.items():
            stream.write(struct.pack('<2I',start,end-start));stream.write(self.program.data[key])
        for (_,_,arity),call,value in zip(native['service_sites'],native['calls'],responses):
            target,words,before,after,private_before,private_after=call;changes=[]
            for (base,_),a,b in zip(MAPPED,before,after):
                changes.extend((base+i,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y)
            for base,data in private_after:changes.extend((base+i,x) for i,x in enumerate(data))
            stream.write(struct.pack('<18I',target,arity,*words,value,len(changes),len(private_before),
                int.from_bytes(private_before[0][1],'little') if private_before else 0))
            for address,replacement in changes:stream.write(struct.pack('<IB',address,replacement))
        for data in native['memory']:stream.write(data)


def delay_fixture(count=32,cursor=0,capacity=256):
    memory=initial(5)
    for address,value in ((EFFECTS+84,OLD),(EFFECTS+88,capacity),(EFFECTS+324,count),(EFFECTS+288,cursor),
        (CONTROL+52,ALLOCATOR),(CONTROL+56,RELEASE),(0x01c34458,MODE),(0x01c34194,0x0201a9dc)):
        setword(memory,address,value)
    for i in range(max(count,256)):
        setword(memory,OLD+2*i,(i*713-17000)&65535,2)
    for i in range((max(count,256)+15)//16):setword(memory,OLD+2*count+i,i%17,1)
    for i in range(16):setword(memory,EFFECTS+328+4*i,(i*1277777-12345678)&0xffffffff)
    return memory


def delay_cases(c):
    paths=((NEW,),(0,NEW),(0,0,NEW),(0,0,0,RESTORED),(0,0,0,0))
    for count in (0,1,15,16,17,31,32,47,64,65,96):
        for cursor in (0,1,15,16,31):
            if (cursor&15)>count:continue
            for path in paths:
                memory=delay_fixture(count,cursor)
                setword(memory,CONTROL+8,2,1);setword(memory,CONTROL+88,0x0201,2)
                c.compare(f'full delay {count}/{cursor}/{path}',memory,'commit',(0,0,100),{ALLOCATOR:path})
    for release in (0,RELEASE):
        memory=delay_fixture();setword(memory,CONTROL+56,release)
        c.compare(f'delay allocator absent/release {release}',memory,'commit',(0,0,100))
    for rate in (0,1,48000,0xffffffff):
        memory=delay_fixture(96);setword(memory,CONFIG+8,rate)
        c.compare(f'delay failure divisor {rate}',memory,'commit',(0,0,100),{ALLOCATOR:0})
    memory=delay_fixture(32)
    for i,value in enumerate((100,110,90,120)):
        memory=c.compare(f'carried allocation {i}',memory,'commit',(0,0,value),
            {ALLOCATOR:(OLD if i==1 else NEW)},carried=bool(i))
    for tempo in (1,2,3,4,5,6,7,8,9):
        memory=delay_fixture();setword(memory,CONFIG+8,1000)
        c.compare(f'recursive tempo allocation {tempo}',memory,'commit',(0,4,tempo),{ALLOCATOR:NEW})


def mode_ir_cases(c):
    for type_ in range(40):
        for index in range(7):
            memory=initial(type_)
            c.compare(f'joined basic commit {type_}/{index}',memory,'commit',(0,index,1))
            c.compare(f'joined basic fast {type_}/{index}',memory,'fast',(0,index,1,7))
    for type_ in (3,5,7,11,13,14,16,23,25,29,36,37,38,39):
        for index in range(7):
            memory=initial(type_)
            for i in range(48):setword(memory,EFFECTS+288+4*i,0x7fffffff-i*171717)
            if type_ in (7,29,37):setword(memory,EFFECTS+288,OLD)
            for word,value in ((OLD,1),(OLD+628,1)):setword(memory,word,value)
            c.compare(f'mode clears and fingerprints {type_}/{index}',memory,'commit',(0,index,2))
    for path in ((NEW,),(0,NEW),(0,0)):
        for active in (0,1):
            memory=initial(29)
            for off,value in ((84,OLD),(88,256),(369,255)):
                setword(memory,EFFECTS+off,value,1 if off==369 else 4)
            setword(memory,EFFECTS+1,active,1)
            for address,value in ((CONTROL+52,ALLOCATOR),(0x01c34458,MODE),(0x01c34194,0x0201a9dc)):
                setword(memory,address,value)
            setword(memory,CONTROL+8,2,1);setword(memory,CONTROL+88,0x0201,2)
            c.compare(f'capture extra allocation {path}/{active}',memory,'commit',(0,6,2),{ALLOCATOR:path})
    for object_ in (0,OLD):
        for enabled in (0,1,2,0xffffffff):
            for requested in (0,1,2,8,32):
                memory=initial(7)
                for address,value in ((EFFECTS+288,object_),(EFFECTS+292,128),(OLD,enabled),
                    (0x01c1f7d0,enabled),(EFFECTS+48,OLD+4096),(EFFECTS+52,4096)):
                    setword(memory,address,value)
                for operation in ('commit','fast'):
                    c.compare(f'real IR {object_}/{enabled}/{requested}/{operation}',memory,operation,
                        (0,3,requested)+((7,) if operation=='fast' else ()))


def mutation_cases(c):
    for token in sorted(DIRECT_RESOURCES|{0x0201a9dc,0x01c06554,0x0202f07e,0x0202df04,0x0202eb4c}):
        memory=delay_fixture();setword(memory,CONTROL+56,token)
        c.compare(f'indirect free resource collision {token:#x}',memory,'commit',(0,0,100),{ALLOCATOR:NEW},
            ((token,0,EFFECTS+70,77,2),(token,0,CONTROL+48,87654,4)))
        memory=delay_fixture();setword(memory,0x01c34458,token)
        c.compare(f'indirect mode resource collision {token:#x}',memory,'commit',(0,0,100),{ALLOCATOR:NEW},
            ((token,0,EFFECTS+5,9,1),))
        memory=delay_fixture();setword(memory,CONTROL+52,token)
        c.compare(f'indirect allocate resource collision {token:#x}',memory,'commit',(0,0,100),{token:NEW},
            ((token,0,EFFECTS+320,55,4),))
        memory=delay_fixture();setword(memory,0x01c34194,token)
        c.compare(f'indirect clear resource collision {token:#x}',memory,'commit',(0,0,100),{ALLOCATOR:NEW},
            ((token,0,EFFECTS+320,55,4),))
    for target in (ALLOCATOR,RELEASE,MODE,0x0202eb4c):
        for occurrence in (0,1):
            memory=delay_fixture(48,15);setword(memory,CONTROL+8,2,1);setword(memory,CONTROL+88,0x0201,2)
            changes=((target,occurrence,EFFECTS+324,64,4),(target,occurrence,EFFECTS+288,31,4),
                (target,occurrence,CONTROL+48,70000,4))
            c.compare(f'ownership callback reload {target}/{occurrence}',memory,'commit',(0,0,100),
                {ALLOCATOR:(0,0,NEW)},changes)
    for flag in (0,1,0x80000000,0xffffffff):
        memory=delay_fixture()
        c.compare(f'borrowed private flag write {flag}',memory,'commit',(0,0,100),{ALLOCATOR:NEW},
            ((ALLOCATOR,0,PRIVATE,flag,4),))
    memory=delay_fixture()
    c.compare('private flag remains exposed to failure mode callback',memory,'commit',(0,0,100),{ALLOCATOR:0},
        ((MODE,1,PRIVATE,0,4),))
    memory=delay_fixture();setword(memory,0x01c34194,0x0202eefa)
    c.compare('private flag remains exposed to parent clear callback',memory,'commit',(0,0,100),{ALLOCATOR:NEW},
        ((0x0202eefa,0,PRIVATE,1,4),))
    memory=delay_fixture();setword(memory,CONTROL+8,3,1);setword(memory,CONTROL+88,0x030201,4)
    c.compare('flush callback edits count and later slots',memory,'commit',(0,0,100),{ALLOCATOR:(0,0,NEW)},
        ((0x0202eb4c,0,CONTROL+8,4,1),(0x0202eb4c,0,CONTROL+89,7,1),(0x0202eb4c,1,CONTROL+8,2,1)))
    memory=initial(14);arguments=(0,4,1,2)
    for i,value in enumerate(arguments+(0,)*8):setword(memory,ARENA+4*i,value)
    c.compare('mutable incoming ABI storage',memory,'fast_wrapper',arguments,
        mutations=((0x0202cf62,0,ARENA+4,0,4),),argument_address=ARENA)


def integration(c):
    parent.integration(c)
    parent.probes(c)
    for mode in ('fast','fallback'):
        memory=delay_fixture();state=0x01c26890;scene=state+11936
        for address,value,width in ((RAM+8,1,1),(RAM+44,24,4),(state+280,2,4),(CONTROL+28,1,1),
            (scene,1,1),(scene+2,1,2),(scene+22,100,2),(RAM+88,0,4),(state+956,1,4)):
            setword(memory,address,value,width)
        if mode=='fallback':
            for i in range(8):setword(memory,CONTROL+210+i,1,1);setword(memory,AUTOMATION+448*i+1,1,1)
        c.compare(f'scene delay ownership {mode}',memory,'scene_inner',(0,),{ALLOCATOR:NEW})


def api_checks(c):
    # The prior guard suite can call the distinctly named joined APIs through
    # aliases while its callback fixture remains an explicitly external boundary.
    count=parent.api_checks(c)
    entry=ENTRY_POINTS['commit'];arguments=(U32*12)(0,0,1)
    for pointer,expected in ((0x50000000,-201),(0x30000100,-202)):
        memory=delay_fixture(capacity=1);native_script=Script({ALLOCATOR:pointer})
        # Invalid mappings are portable guard witnesses, not firmware behavior.
        backend=parent.Backend(c.program,memory,native_script)
        out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=c.lib.hyperrig_effect_parameters_execute(entry,arguments,out,ctypes.byref(backend.io))
        assert status==expected,('lifecycle resource mapping guard',status,expected)
        assert tuple(out)==(0xdeadbeef,0xcafebabe)
        assert backend.read(EFFECTS+84,4)==OLD and backend.read(EFFECTS+88,4)==1
        assert backend.read(0x01c34468,4)==0xffffffff
        count+=1
    backend=parent.Backend(c.program,delay_fixture(capacity=1),Script())
    out=(U32*2)(0xdeadbeef,0xcafebabe)
    io=IO(backend.io.map,CALL(),None,10000,1000000)
    assert c.lib.hyperrig_effect_parameters_execute(entry,arguments,out,ctypes.byref(io))==-200
    assert tuple(out)==(0xdeadbeef,0xcafebabe);count+=1
    return count


def source_paths():
    paths=set(parent.source_paths())|set(SOURCES)|{'tools/effect_parameter_lifecycle_machine.py',
        'tools/verify_effect_parameter_lifecycle.py','tools/build_effect_parameter_lifecycle.py',
        'tests/test_effect_parameter_lifecycle_machine.py','tests/effect_parameter_lifecycle_sanitize.c'}
    # Recursively collect the new resource/bridge headers as well as the frozen
    # parent's dynamic ISA modules and TOML provenance.
    pending=[ROOT/path for path in SOURCES];scanned=set()
    while pending:
        p=pending.pop().resolve()
        if p in scanned:continue
        scanned.add(p)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',p.read_text(),re.M):
            for q in (p.parent/name,ROOT/'firmware/include'/name):
                if q.is_file():q=q.resolve();paths.add(q.relative_to(ROOT).as_posix());pending.append(q);break
    return sorted(paths)


def report(c,guards,mini_image):
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    from hyperrig.jieli import unpack_app
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code;joined=c.program.joined_code
    if {target for _,target in c.resource_sites}!=DIRECT_RESOURCES:
        raise ValueError('integration corpus did not execute every direct resource target')
    expected_sites=set()
    for pc,(text,size,*_) in code.items():
        match=re.fullmatch(r'call (-?\d+)',text)
        if match and any(a<=pc<b for a,b in PARAMETER_REGIONS.values()):
            target=pc+size+int(match[1])
            if target in DIRECT_RESOURCES:expected_sites.add((pc,target))
    if set(c.resource_sites)!=expected_sites:
        raise ValueError('integration corpus did not execute every original direct resource call site')
    windows={hex(pc):{'start':pc,'end_exclusive':pc+v[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+v[1])).hexdigest()} for pc,v in sorted(code.items())}
    static={name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(a,b) in c.program.static_regions.items()}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for record in (*windows.values(),*static.values()):
            a,b=record['start'],record['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    return {'schema':1,'project':'HyperRig','component':'joined-effect-parameter-lifecycle','result':'pass',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,'new_original_functions':0,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.coverage),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.coverage]} for name,(a,b) in REGIONS.items()},
        'instruction_coverage':{'new_decoded':0,'new_visited':0,'unvisited_new':[],
            'joined_decoded':len(joined),'joined_visited':len(joined&c.coverage),'unvisited_joined':sorted(joined-c.coverage),
            'all_decoded':len(code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(code)-c.coverage)},
        'derivative_provenance':check_derivative(),'static_data':static,'bound_instruction_windows':windows,'mini_v4_binding':binding,
        'real_calls':{hex(k):v for k,v in sorted(c.real_calls.items())},
        'direct_resource_call_sites':[{'site':pc,'target':target,'calls':count} for (pc,target),count in sorted(c.resource_sites.items())],
        'external_service_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'carried_calls':c.carried,'callback_mutation_cases':c.mutating,'native_private_flag_lifetimes':c.private,
        'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,'outputs_state_services_sha256':c.digest.hexdigest(),
        'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['Construction 0x0202cf62 and other unreconstructed services remain explicit mutable boundaries.',
            'Platform allocate/free/mode, alternate clear and slot removal callbacks remain external by original call site.',
            'Shared native code and portable C use real resource arithmetic; callback supplied construction outputs are not reconstructed coefficients.',
            'Private native stack bytes are excluded from public snapshots; the initialized four-byte flag is compared during its exact exposed lifetime.',
            'Joined coverage is this integration corpus only; previous complete function reports retain their separate coverage and limits.']}


PARTS={'delay':delay_cases,'mode_ir':mode_ir_cases,'mutations':mutation_cases,'integration':integration}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--part',choices=PARTS,action='append');p.add_argument('--output',type=Path)
    p.add_argument('--sanitizer-corpus',type=Path);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if args.output and (args.output.exists() or args.part):p.error('final report requires all cases and a fresh output')
    check_derivative();replay=args.sanitizer_corpus.open('xb') if args.sanitizer_corpus else None
    c=Corpus(args.library,replay);sources={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()} if args.output else {}
    for name in args.part or PARTS:
        PARTS[name](c);print(name,sum(c.counts.values()),'comparisons passed',flush=True)
    if replay:replay.close()
    guards=api_checks(c)
    result=report(c,guards,args.mini_image) if args.output else {'result':'development-pass','comparisons':c.counts,'steps':c.steps,'guards':guards}
    if args.output:
        assert sources=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},'inputs changed during verification'
        result['source_sha256']=sources;result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in result if k in ('result','total_comparisons','comparisons','original_instruction_steps','guards')}))


if __name__=='__main__':main()
