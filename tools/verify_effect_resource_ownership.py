"""Compare actual resource recovery, slot teardown and parameter lifecycle joins."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
import verify_effect_parameter_lifecycle as lifecycle
import verify_effect_parameters as parent
from verify_effect_parameter_lifecycle import (U32,MAP,CALL,IO,Backend,Script,initial,setword,put,
    EFFECTS,CONTROL,CONFIG,AUTOMATION,OLD,NEW,RESTORED,ALLOCATOR,RELEASE,MODE,delay_fixture,
    PINNED,DECODED,MINI)
from effect_resource_ownership_machine import (EffectResourceOwnershipProgram,REGIONS,
    ENTRY_POINTS,RESOURCE_REGIONS,OWNED_CLOSURE,OWNERSHIP_REGIONS,FLUSH_CALL,REMOVE,
    MAPPED,ROOT,PRIVATE,region_bytes,DIRECT_RESOURCES)
from effect_parameter_lifecycle_machine import RAM,SAMPLES,ARENA,PARAMETER_REGIONS
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app
SOURCES=tuple(p for p in lifecycle.SOURCES if p not in (
    'firmware/src/hyperrig_effect_parameter_resources.c','firmware/src/hyperrig_effect_parameter_lifecycle.c'))+(
    'firmware/src/hyperrig_effect_ownership.c','firmware/src/hyperrig_effect_resource_ownership.c',
    'firmware/src/hyperrig_effect_resource_ownership_lifecycle.c',
    'firmware/src/hyperrig_effect_resource_ownership_scene.c')
RESOURCE_SOURCE='firmware/src/hyperrig_effect_parameter_resources.c'
RESOURCE_SHA='856f0d4de80949a3e83fdb91c0e25bc16746ba29a308fb07d5f3a640f49480e7'
LIFECYCLE_SOURCE='firmware/src/hyperrig_effect_parameter_lifecycle.c'
LIFECYCLE_SHA='a5b3d20f5bdf214b7be0982b4bfff1e7de088a7a391636be4c4d3f0ffa159226'
SCENE_SOURCE='firmware/src/hyperrig_scene_application.c'
SCENE_SHA='22063984cc299b97bfc1bf4dd103ce76d251ac7a521e4fbfcf432e493b5ae717'
SCENE_GUARD='''    {
        uint32_t result=c->io->call(c->io->opaque,target,arguments,count);
        if(c->io->outer_error&&*c->io->outer_error)c->fault=-203;
        return result;
    }'''
RESOURCE_BRIDGE='/* RESOURCE_OWNERSHIP_BRIDGE_BEGIN\n * Only the original direct flush call joins recovered ownership. Token-equal\n * platform callbacks continue through forward unchanged. */\nstatic uint32_t remove_slot(access *a,uint32_t slot)\n{\n    uint32_t args[12]={slot,0,0,0,0,0,0,0,0,0,0,0},out[2]={0,0};int status;\n    hyperrig_effect_ownership_io io={borrow,forward,a,a->services,a->work};\n    if(a->error)return 0;\n    status=hyperrig_effect_ownership_execute(UINT32_C(0x0202eb4c),args,out,&io);\n    if(status&&!a->error)a->error=status;\n    return out[0];\n}\n/* RESOURCE_OWNERSHIP_BRIDGE_END */\n\n'

def check_derivatives(resource=None,joined=None,lifecycle_source=None,lifecycle_joined=None,scene_source=None,scene_joined=None):
    resource=(ROOT/RESOURCE_SOURCE).read_text() if resource is None else resource
    lifecycle_source=(ROOT/LIFECYCLE_SOURCE).read_text() if lifecycle_source is None else lifecycle_source
    if hashlib.sha256(resource.encode()).hexdigest()!=RESOURCE_SHA:raise ValueError('frozen resource input changed')
    if hashlib.sha256(lifecycle_source.encode()).hexdigest()!=LIFECYCLE_SHA:raise ValueError('frozen lifecycle input changed')
    marker='static uint32_t support(access *a,uint32_t entry,uint32_t p0,uint32_t p1)\n'
    if resource.count(marker)!=1 or resource.count('(void)call(a,0x0202eb4c,slot);')!=1:
        raise ValueError('direct resource bridge anchor changed')
    expected=resource.replace('hyperrig_effect_parameter_resources','hyperrig_effect_resource_ownership')
    expected=expected.replace(marker,RESOURCE_BRIDGE+marker).replace('(void)call(a,0x0202eb4c,slot);','(void)remove_slot(a,slot);')
    joined=(ROOT/'firmware/src/hyperrig_effect_resource_ownership.c').read_text() if joined is None else joined
    if joined!=expected:raise ValueError('resource derivative has unapproved changes')
    expected=lifecycle_source.replace('hyperrig_effect_parameter_lifecycle','hyperrig_effect_resource_ownership_lifecycle')
    expected=expected.replace('#include "hyperrig/hyperrig_effect_resource_ownership_lifecycle.h"',
        '#include "hyperrig/hyperrig_effect_resource_ownership.h"')
    expected=expected.replace('hyperrig_effect_parameter_resources','hyperrig_effect_resource_ownership')
    expected=expected.replace('hyperrig_scene_application_io joined','hyperrig_effect_resource_ownership_scene_io joined')
    for name in ('inner','apply','select','flush'):
        expected=expected.replace('hyperrig_scene_application_'+name+'(', 'hyperrig_effect_resource_ownership_scene_'+name+'(')
    expected=expected.replace('joined.call_budget=io->service_budget;','joined.call_budget=io->service_budget;joined.outer_error=&a.error;')
    lifecycle_joined=(ROOT/'firmware/src/hyperrig_effect_resource_ownership_lifecycle.c').read_text() if lifecycle_joined is None else lifecycle_joined
    if lifecycle_joined!=expected:raise ValueError('lifecycle derivative has unapproved changes')
    scene_source=(ROOT/SCENE_SOURCE).read_text() if scene_source is None else scene_source
    if hashlib.sha256(scene_source.encode()).hexdigest()!=SCENE_SHA:raise ValueError('frozen scene input changed')
    expected=scene_source.replace('hyperrig_scene_application','hyperrig_effect_resource_ownership_scene')
    expected=expected.replace('#include "hyperrig/hyperrig_effect_resource_ownership_scene.h"',
        '#include "hyperrig/hyperrig_effect_resource_ownership.h"')
    old='    return c->io->call(c->io->opaque,target,arguments,count);'
    if expected.count(old)!=1:raise ValueError('scene service guard anchor changed')
    expected=expected.replace(old,SCENE_GUARD)
    scene_joined=(ROOT/'firmware/src/hyperrig_effect_resource_ownership_scene.c').read_text() if scene_joined is None else scene_joined
    if scene_joined!=expected:raise ValueError('scene derivative has unapproved changes')
    return {'resource_parent':RESOURCE_SOURCE,'resource_parent_sha256':RESOURCE_SHA,
        'lifecycle_parent':LIFECYCLE_SOURCE,'lifecycle_parent_sha256':LIFECYCLE_SHA,
        'scene_parent':SCENE_SOURCE,'scene_parent_sha256':SCENE_SHA,
        'original_direct_flush_call':FLUSH_CALL,'original_removal_entry':REMOVE,
        'permitted_resource_changes':['public symbol/header/type prefix','one exact ownership bridge','one direct flush call substitution'],
        'permitted_lifecycle_changes':['public symbol/header/type prefix','existing resource bridge API rebinding',
            'guard-aware scene API rebinding with a pointer to the current outer error'],
        'permitted_scene_changes':['public symbol/header/type prefix','one immediate outer-error observation after a service returns'],
        'new_original_functions':0,'frozen_input_bodies_preserved':True}

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectResourceOwnershipProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        for name in ('execute','scene','stage'):
            setattr(self.lib,'hyperrig_effect_parameters_'+name,getattr(self.lib,'hyperrig_effect_resource_ownership_lifecycle_'+name))
        self.lib.hyperrig_effect_parameters_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_scene.argtypes=[U32,U32,ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_resource_ownership_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.prefixes=0;self.ownership_sites={};self.last=None;self.replay=replay;self.counts={};self.steps=0;self.coverage=set();self.real_calls={};self.resource_sites={}
        self.services={};self.carried=self.mutating=self.private=self.replays=0;self.digest=hashlib.sha256()
    def compare(self,label,memory,name,args,plan=None,mutations=(),carried=False,argument_address=None,stop_extra_overread=False):
        script=Script(plan,mutations)
        try:native=self.program.execute(memory,name,args,boundary=script,stop_extra_overread=stop_extra_overread)
        except Exception as error:raise AssertionError(f'{label}: native execution {error}') from error
        c=Backend(self.program,memory,Script(plan,mutations),native['calls']);out=(U32*2)(0xdeadbeef,0xcafebabe)
        entry=ENTRY_POINTS[name]
        if name.startswith('resource_'):
            status=self.lib.hyperrig_effect_resource_ownership_execute(entry,(U32*12)(*args),out,ctypes.byref(c.io))
        elif name=='stage':status=self.lib.hyperrig_effect_parameters_stage(*args,ctypes.byref(c.io));out[:]=[0,0]
        elif name.startswith('scene_'):
            status=self.lib.hyperrig_effect_parameters_scene(entry,args[0] if args else 0,out,ctypes.byref(c.io))
            if not status:out[1]=0
        else:
            words=ctypes.cast(c.locate(argument_address,48,0),ctypes.POINTER(U32)) if argument_address else (U32*12)(*args)
            status=self.lib.hyperrig_effect_parameters_execute(entry,words,out,ctypes.byref(c.io))
        if status!=native['status'] or c.errors:raise AssertionError((label,'C status',status,native['status'],c.errors))
        scalar=name not in ('stage','scene_select','scene_flush')
        if status:
            if name!='stage' and tuple(out)!=(0xdeadbeef,0xcafebabe):raise AssertionError((label,'guard results changed',tuple(out)))
        elif out[1] or scalar and out[0]!=native['value']:raise AssertionError((label,'result',hex(out[0]),hex(native['value'])))
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
        self.prefixes+=bool(status);self.last=native
        for site,target in native['ownership_sites']:self.ownership_sites[(site,target)]=self.ownership_sites.get((site,target),0)+1
        if status and native['private_at_stop']:
            assert native['calls'][-1][5]==native['private_at_stop'],(label,'retained flag prefix')
        self.carried+=bool(carried);self.mutating+=bool(mutations);self.private+=len(native['private_events'])
        for target in native['real_calls']:self.real_calls[target]=self.real_calls.get(target,0)+1
        for site,target in native['resource_sites']:self.resource_sites[(site,target)]=self.resource_sites.get((site,target),0)+1
        for target,*_ in native['calls']:self.services[target]=self.services.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<3I',status&0xffffffff,*out))
        for data in native['memory']:self.digest.update(data)
        for target,words,before,after,p0,p1 in native['calls']:
            self.digest.update(struct.pack('<13I',target,*words))
            for data in (*before,*after):self.digest.update(data)
            for address,data in (*p0,*p1):self.digest.update(struct.pack('<I',address));self.digest.update(data)
        if self.replay:self.write_replay(memory,name,args,native,script.responses,scalar,argument_address);self.replays+=1
        return native['memory']
    def write_replay(self,memory,name,args,native,responses,scalar,argument_address):
        stream=self.replay
        stream.write(struct.pack('<20I',int(name.startswith('resource_')),native['status']&0xffffffff,ENTRY_POINTS[name],*(tuple(args)+(0,)*(12-len(args))),int(scalar),
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


def teardown_fixture(count=3,extra=3,route_count=6):
    memory=delay_fixture()
    for slot in (1,2,3):
        effect=EFFECTS+480*slot
        for off,value,width in ((0,27+slot,1),(1,1,1),(2,1,1),(3,1,1),(5,1,1),
            (7,extra,1),(8,0x1234,2),(48,ARENA+8192+slot*64,4),(52,128,4),
            (64,11,4),(69,1,1),(84,ARENA+4096+slot*256,4),(88,128,4),
            (288,0x01c2fa38+888*slot,4)):
            setword(memory,effect+off,value,width)
        for i in range(3):
            setword(memory,effect+92+4*i,ARENA+10000+slot*512+64*i)
            setword(memory,effect+104+2*i,32+i,2)
    setword(memory,CONTROL+6,255,1)
    setword(memory,CONTROL+8,count,1)
    for i in range(count):setword(memory,CONTROL+88+i,1+i%3,1)
    for chain in range(2):
        setword(memory,CONTROL+14+chain,route_count,1)
        for i in range(route_count):setword(memory,CONTROL+348+10*chain+i,1+i%3,1)
    return memory


def smoke(c):
    c.compare('direct flush actual teardown',teardown_fixture(),'resource_flush',())
    c.compare('allocation failure flush actual teardown',teardown_fixture(),'commit',(0,0,100),{ALLOCATOR:(0,0,NEW)})


def resource_cases(c):
    for count in (0,1,2,3,4,15,16,31,127,255):
        for extra in range(4):
            memory=teardown_fixture(count,extra)
            c.compare(f'flush count {count} extra {extra}',memory,'resource_flush',())
    for count in (0,1,2,9,10,11,127,255):
        c.compare(f'flush route count {count}',teardown_fixture(3,3,count),'resource_flush',())
    for release in (0,RELEASE):
        for active in (0,1):
            memory=teardown_fixture();setword(memory,CONTROL+56,release)
            for slot in (1,2,3):setword(memory,EFFECTS+480*slot+1,active,1)
            c.compare(f'flush active {active} release {release}',memory,'resource_flush',())
    paths=((NEW,),(0,NEW),(0,0,NEW),(0,0,0,RESTORED),(0,0,0,0))
    for path in paths:
        for flag_alias in (ARENA+120000,EFFECTS+480+7,EFFECTS+480+84,CONTROL+8):
            memory=teardown_fixture()
            c.compare(f'direct allocation {path} output {flag_alias:#x}',memory,
                'resource_allocate_delay',(EFFECTS,512,flag_alias),{ALLOCATOR:path})
    for path in ((NEW,),(0,NEW),(0,0)):
        c.compare(f'extra recovery {path}',teardown_fixture(),'resource_allocate_extra',(EFFECTS,),{ALLOCATOR:path})
    memory=teardown_fixture()
    for index in range(3):memory=c.compare(f'carried flush {index}',memory,'resource_flush',(),carried=bool(index))


def caller_cases(c):
    for count in (0,1,15,16,17,31,32,47,64,65,96):
        for path in ((NEW,),(0,NEW),(0,0,NEW),(0,0,0,RESTORED),(0,0,0,0)):
            memory=teardown_fixture();setword(memory,EFFECTS+324,count)
            setword(memory,EFFECTS+288,min(15,count))
            c.compare(f'parameter recovery {count}/{path}',memory,'commit',(0,0,100),{ALLOCATOR:path})
    for kind in (29,37):
        for path in ((NEW,),(0,NEW),(0,0)):
            memory=teardown_fixture();setword(memory,EFFECTS,kind,1);setword(memory,EFFECTS+369,255,1)
            c.compare(f'parameter extra recovery {kind}/{path}',memory,'commit',(0,6,2),{ALLOCATOR:path})
    # Frozen fast, probe, IR, reset and fingerprint paths remain available on
    # this derivative, including paths which do not need resource eviction.
    lifecycle.mode_ir_cases(c)
    lifecycle.integration(c)
    for mode in ('fast','fallback'):
        memory=teardown_fixture();state=0x01c26890;scene=state+11936
        for address,value,width in ((RAM+8,1,1),(RAM+44,24,4),(state+280,2,4),(CONTROL+28,1,1),
            (scene,1,1),(scene+2,1,2),(scene+22,100,2),(RAM+88,0,4),(state+956,1,4)):
            setword(memory,address,value,width)
        if mode=='fallback':
            for i in range(8):setword(memory,CONTROL+210+i,1,1);setword(memory,AUTOMATION+448*i+1,1,1)
        c.compare(f'scene actual eviction {mode}',memory,'scene_inner',(0,),{ALLOCATOR:(0,0,NEW)})


def collision_cases(c):
    tokens=sorted({a for a,_ in OWNERSHIP_REGIONS.values()}|DIRECT_RESOURCES|{0x0202df04,0x0201a9dc,0x0202f07e})
    for token in tokens:
        memory=teardown_fixture();setword(memory,CONTROL+56,token)
        c.compare(f'ownership free token collision {token:#x}',memory,'commit',(0,0,100),
            {ALLOCATOR:(0,0,NEW)},((token,1,EFFECTS+480+48,ARENA+7776,4),))
        memory=teardown_fixture();setword(memory,CONTROL+52,token)
        c.compare(f'ownership allocator token collision {token:#x}',memory,'commit',(0,0,100),{token:(0,0,NEW)})
        memory=teardown_fixture();setword(memory,0x01c34458,token)
        c.compare(f'ownership mode token collision {token:#x}',memory,'commit',(0,0,100),{ALLOCATOR:(0,0,NEW)})
    for token in (0,0x0202eb4c,0x0202eefa,RELEASE+4):
        memory=teardown_fixture()
        c.compare(f'ownership release replaced with {token:#x}',memory,'commit',(0,0,100),
            {ALLOCATOR:(0,0,NEW)},((RELEASE,1,CONTROL+56,token,4),))


def mutation_cases(c):
    victim=EFFECTS+480
    changes=(
        ((RELEASE,1,CONTROL+8,1,1),),
        ((RELEASE,1,CONTROL+8,4,1),(RELEASE,1,CONTROL+89,15,1),(RELEASE,1,CONTROL+91,3,1)),
        ((RELEASE,1,victim+7,0,1),(RELEASE,1,victim+92,NEW,4),(RELEASE,1,victim+96,NEW+32,4)),
        ((RELEASE,1,victim+48,NEW+64,4),(RELEASE,1,victim,31,1),(RELEASE,1,victim+288,0x01c2fa38,4)),
        ((RELEASE,1,CONTROL+14,1,1),(RELEASE,1,CONTROL+348,3,1),(RELEASE,1,EFFECTS+960+1,0,1)),
        ((RELEASE,1,EFFECTS+324,64,4),(RELEASE,1,EFFECTS+288,31,4)),
    )
    for index,edits in enumerate(changes):
        c.compare(f'nested callback mutation {index}',teardown_fixture(),'commit',(0,0,100),
            {ALLOCATOR:(0,0,NEW)},edits)
    for value in (0,1,0x80000000,0xffffffff):
        for path in ((0,0,NEW),(0,0,0,RESTORED),(0,0,0,0)):
            c.compare(f'flag inside actual teardown {value}/{path}',teardown_fixture(),'commit',(0,0,100),
                {ALLOCATOR:path},((RELEASE,1,PRIVATE,value,4),))
    for mode in (0,1):
        memory=teardown_fixture();setword(memory,0x01c34194,0x0202eb4c)
        c.compare(f'flag after recovery before consume {mode}',memory,'commit',(0,0,100),
            {ALLOCATOR:(0,0,NEW) if mode else (0,0,0,RESTORED)},
            ((0x0202eb4c,0,PRIVATE,1,4),) if mode else ((MODE,1,PRIVATE,0,4),))
    lifecycle.mutation_cases(c)


def prefix_cases(c):
    for extra in (4,5,127,255):
        for mask in (0,1,3,7):
            memory=teardown_fixture(3,extra)
            for i in range(3):
                if not mask&(1<<i):setword(memory,EFFECTS+480+92+4*i,0)
            c.compare(f'flush fourth-read prefix {extra}/{mask}',memory,'resource_flush',(),stop_extra_overread=True)
            c.compare(f'caller fourth-read prefix {extra}/{mask}',memory,'commit',(0,0,100),
                {ALLOCATOR:(0,0,NEW)},stop_extra_overread=True)
    memory=teardown_fixture(3,255);setword(memory,CONTROL+56,0)
    c.compare('no callback no fourth-read prefix',memory,'resource_flush',(),stop_extra_overread=True)
    memory=teardown_fixture(3,4)
    c.compare('callback clears cached count but prefix persists',memory,'commit',(0,0,100),
        {ALLOCATOR:(0,0,NEW)},((RELEASE,1,EFFECTS+480+7,0,1),(RELEASE,1,PRIVATE,0x76543210,4)),
        stop_extra_overread=True)
    c.compare('extra allocation retains teardown prefix',teardown_fixture(3,4),'resource_allocate_extra',
        (EFFECTS,),{ALLOCATOR:(0,NEW)},stop_extra_overread=True)
    memory=teardown_fixture(3,4);state=0x01c26890;scene=state+11936
    for address,value,width in ((RAM+8,1,1),(RAM+44,24,4),(state+280,2,4),(CONTROL+28,1,1),
        (scene,1,1),(scene+2,1,2),(scene+22,100,2),(RAM+88,0,4),(state+956,1,4)):
        setword(memory,address,value,width)
    for i in range(8):setword(memory,CONTROL+210+i,1,1);setword(memory,AUTOMATION+448*i+1,1,1)
    c.compare('scene fallback retains allocator teardown prefix',memory,'scene_inner',(0,),
        {ALLOCATOR:(0,0,NEW)},stop_extra_overread=True)
    if c.last['status']!=-202:raise ValueError('scene prefix fixture did not reach ownership guard')


PARTS={'smoke':smoke,'resources':resource_cases,'callers':caller_cases,
    'collisions':collision_cases,'mutations':mutation_cases,'prefixes':prefix_cases}


def api_checks(c):
    checks=lifecycle.api_checks(c)
    entry=ENTRY_POINTS['resource_flush'];words=(U32*12)();out=(U32*2)(0xdeadbeef,0xcafebabe)
    memory=teardown_fixture();b=parent.Backend(c.program,memory,Script())
    execute=c.lib.hyperrig_effect_resource_ownership_execute
    for arguments,result,io,expected in ((None,out,ctypes.byref(b.io),-200),
        (words,None,ctypes.byref(b.io),-200),(words,out,None,-200)):
        assert execute(entry,arguments,result,io)==expected;checks+=1
    no_map=IO(MAP(),b.io.call,None,100000,1000000)
    assert execute(entry,words,out,ctypes.byref(no_map))==-200;checks+=1
    assert execute(0,words,out,ctypes.byref(b.io))==-202;checks+=1
    assert tuple(out)==(0xdeadbeef,0xcafebabe)
    for services in (0,1,2,3):
        b=parent.Backend(c.program,teardown_fixture(),Script());b.io.services=services
        assert execute(entry,words,out,ctypes.byref(b.io))==-203
        assert len(b.calls)==services and b.read(EFFECTS+480+84,4)==0
        assert b.read(EFFECTS+480+48,4)==ARENA+8256 and b.read(CONTROL+8,1)==3
        assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    b=parent.Backend(c.program,teardown_fixture(),Script());no_call=IO(b.io.map,CALL(),None,100000,1000000)
    assert execute(entry,words,out,ctypes.byref(no_call))==-200
    assert b.read(EFFECTS+480+84,4)==0 and b.read(CONTROL+8,1)==3;checks+=1
    for work in (0,1,2,4,8):
        b=parent.Backend(c.program,teardown_fixture(),Script());b.io.work=work
        assert execute(entry,words,out,ctypes.byref(b.io))==(-200 if not work else -203)
        assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    return checks


def source_paths():
    paths=set(lifecycle.source_paths())|set(SOURCES)|{
        'tools/effect_resource_ownership_machine.py','tools/verify_effect_resource_ownership.py',
        'tools/build_effect_resource_ownership.py','tests/test_effect_resource_ownership_machine.py',
        'tests/effect_resource_ownership_sanitize.c','tools/effect_ownership_machine.py'}
    pending=[ROOT/path for path in SOURCES];scanned=set()
    while pending:
        path=pending.pop().resolve()
        if path in scanned:continue
        scanned.add(path)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',path.read_text(),re.M):
            for child in (path.parent/name,ROOT/'firmware/include'/name):
                if child.is_file():
                    child=child.resolve();paths.add(child.relative_to(ROOT).as_posix());pending.append(child);break
    return sorted(paths)


def report(c,guards,mini_image):
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code;joined=c.program.joined_code
    expected_sites=set()
    for pc,(text,size,*_) in code.items():
        match=re.fullmatch(r'call (-?\d+)',text)
        if match and any(a<=pc<b for a,b in PARAMETER_REGIONS.values()):
            target=pc+size+int(match[1])
            if target in DIRECT_RESOURCES:expected_sites.add((pc,target))
    if set(c.resource_sites)!=expected_sites:raise ValueError('not every direct parameter resource call site executed')
    if set(c.ownership_sites)!={(FLUSH_CALL,REMOVE)}:raise ValueError('actual resource ownership call not observed')
    windows={hex(pc):{'start':pc,'end_exclusive':pc+v[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+v[1])).hexdigest()} for pc,v in sorted(code.items())}
    static={name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(a,b) in c.program.static_regions.items()}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for item in (*windows.values(),*static.values()):
            a,b=item['start'],item['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    return {'schema':1,'project':'HyperRig','component':'joined-effect-resource-ownership','result':'pass',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,'new_original_functions':0,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.coverage),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.coverage]} for name,(a,b) in REGIONS.items()},
        'instruction_coverage':{'new_decoded':0,'new_visited':0,'unvisited_new':[],
            'joined_decoded':len(joined),'joined_visited':len(joined&c.coverage),'unvisited_joined':sorted(joined-c.coverage),
            'all_decoded':len(code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(code)-c.coverage)},
        'derivative_provenance':check_derivatives(),'static_data':static,'bound_instruction_windows':windows,'mini_v4_binding':binding,
        'real_calls':{hex(k):v for k,v in sorted(c.real_calls.items())},
        'direct_resource_call_sites':[{'site':pc,'target':target,'calls':count} for (pc,target),count in sorted(c.resource_sites.items())],
        'direct_ownership_call_sites':[{'site':pc,'target':target,'calls':count} for (pc,target),count in sorted(c.ownership_sites.items())],
        'external_service_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'carried_calls':c.carried,'callback_mutation_cases':c.mutating,'native_private_flag_lifetimes':c.private,
        'original_fourth_read_prefix_comparisons':c.prefixes,'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,
        'outputs_state_services_sha256':c.digest.hexdigest(),'hardware_test':False,'audio_test':False,
        'firmware_changed':False,'flashable':False,
        'limitations':['Construction 0x0202cf62 and remaining coefficient/sample/platform services remain explicit mutable boundaries.',
            'Allocator/free/mode and alternate-clear callbacks retain their original call-site ABI even for recovered numeric target tokens.',
            'Only the exact flush call joins ownership; other ownership helpers not required by removal remain outside this integration.',
            'The fourth cached pointer read is an observed native prefix; the model does not claim a firmware guard return or completed caller stack.',
            'Private stack bytes are excluded from public snapshots; initialized allocation flags are compared at each exposed callback and retained prefix.',
            'Joined instruction coverage belongs to this integration corpus; existing standalone coverage and numerical domain limits are unchanged.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--part',choices=tuple(PARTS)+('all',),default='all')
    parser.add_argument('--output',type=Path);parser.add_argument('--sanitizer-corpus',type=Path);parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args()
    if args.output and (args.output.exists() or args.part!='all'):parser.error('final report needs a fresh output and all cases')
    check_derivatives();replay=args.sanitizer_corpus.open('xb') if args.sanitizer_corpus else None
    c=Corpus(args.library,replay)
    sources={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()} if args.output else {}
    for name in (PARTS if args.part=='all' else (args.part,)):
        PARTS[name](c);print(name,sum(c.counts.values()),'comparisons',flush=True)
    if replay:replay.close()
    guards=api_checks(c)
    if args.output:
        result=report(c,guards,args.mini_image)
        assert sources=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},'source inputs changed during run'
        result['source_sha256']=sources;result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',c.counts,'steps',c.steps,'prefixes',c.prefixes,'guards',guards,'joined',len(c.coverage&c.program.joined_code),len(c.program.joined_code))


if __name__=='__main__':main()
