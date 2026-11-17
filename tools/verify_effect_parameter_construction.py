"""Compare the three direct parameter construction joins against original instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import re
import sys
from pathlib import Path
import verify_effect_resource_ownership as ownership
import verify_effect_parameter_lifecycle as lifecycle
import verify_effect_model_construction as models
from verify_effect_resource_ownership import (U32,MAP,CALL,IO,Backend,Script,initial,setword,
    EFFECTS,CONTROL,CONFIG,AUTOMATION,OLD,NEW,RESTORED,ALLOCATOR,RELEASE,MODE,
    PINNED,DECODED,MINI,teardown_fixture,RAM,SAMPLES,ARENA)
from effect_parameter_construction_machine import (EffectParameterConstructionProgram,
    DIRECT_JOINS,REGIONS,ENTRY_POINTS,MAPPED,ROOT,PRIVATE,region_bytes)
from hyperrig.jieli import unpack_app

PARENT='firmware/src/hyperrig_effect_resource_ownership_lifecycle.c'
PARENT_SHA='6c988de86e765ecec79cb72141b9af0d88994b8519caa76e7779a95fb6c322a2'
SOURCE='firmware/src/hyperrig_effect_parameter_construction.c'
SOURCES=tuple(dict.fromkeys((*[p for p in ownership.SOURCES if p!=PARENT],*models.SOURCES,SOURCE)))
BRIDGE='''/* PARAMETER_CONSTRUCTION_BRIDGE_BEGIN
 * These three direct native sites are distinct from numeric callback tokens. */
static void construction(parameter_access *a,uint32_t entry,uint32_t effect)
{
    uint32_t args[12]={effect,0,0,0,0,0,0,0,0,0,0,0},out[2];int status;
    hyperrig_effect_model_construction_io io={borrowed_map,a,a->work};
    if(a->error)return;
    status=hyperrig_effect_model_construction_execute(entry,args,out,&io);
    if(status&&!a->error)a->error=status;
}
/* PARAMETER_CONSTRUCTION_BRIDGE_END */

'''
SUBSTITUTIONS=(
    ('(void)CALL1(a,0x0202cf62,effect);','construction(a,0x0202cf62,effect);'),
    ('(void)CALL1(a,0x0202cf62,PROPOSED);','construction(a,0x0202cf62,PROPOSED);'),
    ('(void)CALL1(a,0x0202cd32,effect);','construction(a,0x0202cd32,effect);'))

def derivative(parent):
    if hashlib.sha256(parent.encode()).hexdigest()!=PARENT_SHA:raise ValueError('frozen ownership lifecycle input changed')
    value=parent.replace('hyperrig_effect_resource_ownership_lifecycle','hyperrig_effect_parameter_construction')
    value=value.replace('#include "hyperrig/hyperrig_effect_resource_ownership.h"',
        '#include "hyperrig/hyperrig_effect_parameter_construction.h"',1)
    anchor='/* 0x0202f4e8: classify an unsigned word offset within one eleven-word section. */'
    if value.count(anchor)!=1:raise ValueError('constructor bridge insertion anchor changed')
    value=value.replace(anchor,BRIDGE+anchor)
    for before,after in SUBSTITUTIONS:
        if value.count(before)!=1:raise ValueError('ambiguous direct constructor substitution')
        value=value.replace(before,after)
    return value

def check_derivative(source=None):
    expected=derivative((ROOT/PARENT).read_text())
    actual=(ROOT/SOURCE).read_text() if source is None else source
    if actual!=expected:raise ValueError('parameter construction derivative differs outside three direct joins')
    return {'parent':PARENT,'parent_sha256':PARENT_SHA,'derived':SOURCE,
        'direct_sites':[{'site':pc,'target':target,'argument_words':1} for pc,target in sorted(DIRECT_JOINS.items())],
        'permitted_changes':['public lifecycle prefix/header','one borrowed constructor bridge','three exact direct call substitutions'],
        'resource_ownership_numerical_and_guarded_scene_sources_unchanged':True}

class Corpus(ownership.Corpus):
    def __init__(self,library,replay=None):
        self.program=EffectParameterConstructionProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        for name in ('execute','scene','stage'):
            setattr(self.lib,'hyperrig_effect_parameters_'+name,getattr(self.lib,'hyperrig_effect_parameter_construction_'+name))
        self.lib.hyperrig_effect_parameters_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_scene.argtypes=[U32,U32,ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_parameters_stage.argtypes=[U32,U32,U32,ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_resource_ownership_execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.prefixes=0;self.ownership_sites={};self.last=None;self.replay=replay;self.counts={};self.steps=0
        self.coverage=set();self.real_calls={};self.resource_sites={};self.services={}
        self.carried=self.mutating=self.private=self.replays=0;self.digest=hashlib.sha256()
        self.construction_sites={};self.coefficients=0;self.exp_calls=0;self.live_aliases=0
    def compare(self,*args,**kwargs):
        result=super().compare(*args,**kwargs)
        for site,target,token in self.last['construction_sites']:
            key=(site,target);self.construction_sites[key]=self.construction_sites.get(key,0)+1
        self.coefficients+=len(self.last['coefficient_requests']);self.exp_calls+=len(self.last['exp_arguments'])
        self.live_aliases+=args[0].startswith(('live signature object overlap','live object writes adjacent fields'))
        return result

def fixture(kind=1,seed=0):
    memory=initial(kind,seed);source=models.initial(kind,seed)
    memory[0][:]=source[0];memory[2][:len(source[1])]=source[1]
    for a,v,n in ((EFFECTS+1,1,1),(EFFECTS+2,1,1),(EFFECTS+3,1,1),(EFFECTS+5,1,1),
        (EFFECTS+7,0,1),(EFFECTS+48,0,4),(EFFECTS+52,0,4),(EFFECTS+69,0,1),
        (CONTROL+52,ALLOCATOR,4),(CONTROL+56,RELEASE,4),(CONTROL+48,100000,4),
        (0x01c34458,MODE,4),(0x01c34194,0x0201a9dc,4)):
        setword(memory,a,v,n)
    setword(memory,ARENA+8192+632,1 if kind==33 else 2 if kind==34 else 0,1)
    for i in range(9):setword(memory,ARENA+8192+80+4*i,3000)
    if kind==30:setword(memory,ARENA,0x53525631)
    for i in range(6):setword(memory,CONTROL+180+i,255,1)
    return memory

def smoke(c):
    for kind,name,index,value in ((1,'commit',0,30),(1,'fast',0,30),(31,'fast',0,30)):
        m=fixture(kind)
        if kind==31:setword(m,ARENA+8192+628,1)
        c.compare(f'three-site smoke {kind}/{name}',m,name,(0,index,value)+((8,) if name=='fast' else ()))

def constructor_cases(c):
    for kind in range(1,40):
        for value in (-100,0,50,100):
            m=fixture(kind,kind)
            c.compare(f'live constructor type {kind} value {value}',m,'commit',(0,0,value&0xffffffff))
        for duration in (1,2,255):
            m=fixture(kind,kind);setword(m,ARENA+8192+628,1)
            c.compare(f'proposed constructor type {kind} duration {duration}',m,'fast',(0,0,25,duration))
    for kind in (27,31,32,33,34,35):
        for ready in (0,1):
            for present in (0,1):
                m=fixture(kind);setword(m,ARENA+8192+628,ready)
                setword(m,EFFECTS+84,ARENA if present else 0)
                c.compare(f'direct object builder gates {kind}/{ready}/{present}',m,'fast',(0,0,30,7))

def retained_cases(c):
    for kind in (1,2,5,13,16,19,21,23,25,26,29,31,33,34,36,37,38,39):
        m=fixture(kind);setword(m,ARENA+8192+628,1)
        for step in range(3):
            m=c.compare(f'carried live constructor {kind}/{step}',m,'commit',(0,1,10+20*step),carried=step!=0)
            m=c.compare(f'carried actual proposed words {kind}/{step}',m,'fast',(0,0,15+20*step,3),carried=True)
    for kind in (1,2,13,16,25):
        m=fixture(kind)
        # Publish a valid serial route and processing control fields. The
        # coefficient/history words are still produced by the real constructor.
        for address,value,width in ((EFFECTS+4,0,1),(EFFECTS+5,0,1),(EFFECTS+8,0,2),
                (EFFECTS+10,0,1),(EFFECTS+11,0,1),(EFFECTS+12,0,1),(EFFECTS+13,0,1),
                (EFFECTS+46,0,1),(CONTROL+20,1,1),(CONTROL+21,2,1),(CONFIG+6,1,1),
                (CONFIG+7,2,1),(CONFIG+40,0x01c341c4,4),(CONTROL+14,1,1),(CONTROL+348,0,1)):
            setword(m,address,value,width)
        for i in range(3):
            m=c.compare(f'actual coefficients before stage {kind}/{i}',m,'fast',(0,0,5+10*i,3),carried=i!=0)
            for frame in range(4):
                m=c.compare(f'actual stage consumes produced words {kind}/{i}/{frame}',m,'stage',(0,SAMPLES,128),carried=True)
                assert 0x01c0f678 in c.last['real_calls'],'processing route did not execute'
    # The original PROPOSED copy contains the same live object pointer. Its
    # constructor writes must remain visible outside the 480-byte copied record.
    for kind in (25,29,39):
        for delta in (0,4,64):
            m=fixture(kind);setword(m,EFFECTS+84,EFFECTS+480+delta)
            c.compare(f'proposed live pointer alias {kind}/{delta}',m,'fast',(0,0,25,5))

def recovery_cases(c):
    for count in (0,15,16,31,32,65):
        for plan in ((NEW,),(0,NEW),(0,0,NEW),(0,0,0,RESTORED),(0,0,0,0)):
            m=teardown_fixture();setword(m,CONFIG+36,48000)
            setword(m,EFFECTS+324,count);setword(m,EFFECTS+288,min(15,count))
            c.compare(f'ownership recovery before real construction {count}/{plan}',m,'commit',(0,0,100),{ALLOCATOR:plan})
    for field,value,width in ((EFFECTS+72,17,2),(CONFIG+8,44100,4),(CONTROL+56,MODE,4),
            (PRIVATE,1,4),(EFFECTS+480,31,1)):
        m=teardown_fixture();setword(m,CONFIG+36,48000)
        c.compare('nested release mutation before constructor',m,'commit',(0,0,100),{ALLOCATOR:(0,0,NEW)},
            ((RELEASE,1,field,value,width),))
    ownership.prefix_cases(c)

def alias_cases(c):
    # Signature construction reaches through PROPOSED's copied pointer into
    # the adjacent live effect records and later scratch RAM. This is a real
    # writer, unlike a presence-only buffer alias.
    for delta in (0,4,64):
        for name in ('commit','fast'):
            m=fixture(30);pointer=EFFECTS+480+delta
            setword(m,EFFECTS+84,pointer);setword(m,pointer,0x53525631)
            setword(m,pointer+64,0xdeadbeef)
            after=c.compare(f'live signature object overlap {name}/{delta}',m,name,
                (0,0,25)+((5,) if name=='fast' else ()))
            offset=pointer+64-RAM
            assert after[0][offset:offset+4]==bytes(4)
            assert any(pc==(0x0202f970 if name=='fast' else 0x0202f37c)
                for pc,_,_ in c.last['construction_sites'])
            offset=pointer+17328-RAM
            assert after[0][offset:offset+1028]!=m[0][offset:offset+1028]
    for kind in (31,33,34):
        for name in ('commit','fast'):
            m=fixture(kind);pointer=EFFECTS+480
            setword(m,EFFECTS+288,pointer);setword(m,pointer+628,1)
            setword(m,pointer+632,1 if kind==33 else 2 if kind==34 else 0,1)
            for i in range(9):setword(m,pointer+80+4*i,3000)
            after=c.compare(f'live object writes adjacent fields {kind}/{name}',m,name,
                (0,0,25)+((5,) if name=='fast' else ()))
            offset=pointer-RAM
            assert after[0][offset:offset+824]!=m[0][offset:offset+824],(kind,name)

def collision_cases(c):
    for target in (0x0202cf62,0x0202cd32):
        for role,address in (('free',CONTROL+56),('mode',0x01c34458),('clear',0x01c34194)):
            m=teardown_fixture();setword(m,CONFIG+36,48000);setword(m,address,target)
            c.compare(f'{role} token equals constructor {target:x}',m,'commit',(0,0,100),{ALLOCATOR:(0,0,NEW)})
            if not any(t==target for _,t,_ in c.last['service_sites']):raise AssertionError('collision did not reach callback')
        m=teardown_fixture();setword(m,CONFIG+36,48000);setword(m,CONTROL+52,target)
        c.compare('allocator token equals constructor',m,'commit',(0,0,100),{target:(0,0,NEW)})
        m=teardown_fixture();setword(m,CONFIG+36,48000)
        c.compare('free token changes to constructor after first release',m,'commit',(0,0,100),
            {ALLOCATOR:(0,0,NEW)},((RELEASE,0,CONTROL+56,target,4),))

def scene_fixture(kind=1,fallback=False,notification=0):
    m=fixture(kind);state=0x01c26890;scene=state+11936
    for a,v,n in ((RAM+8,1,1),(RAM+44,24,4),(state+280,2,4),(CONTROL+28,1,1),
        (scene,1,1),(scene+2,1,2),(scene+22,20,2),(RAM+88,0,4),(state+956,1,4)):
        setword(m,a,v,n)
    if fallback:
        for i in range(8):setword(m,CONTROL+210+i,1,1);setword(m,AUTOMATION+448*i+1,1,1)
    if notification:
        setword(m,scene+258,1,1);setword(m,scene+256,25,2);setword(m,0x01c3446c,notification)
    return m

def scene_cases(c):
    for name in ('scene_inner','scene_apply','scene_select','scene_flush'):
        for kind in (1,16,25,31):
            for fallback in (False,True):
                m=scene_fixture(kind,fallback);setword(m,ARENA+8192+628,1)
                c.compare(f'scene real constructor {name}/{kind}/{fallback}',m,name,() if name=='scene_flush' else (0,))
        for token in (0x0202cf62,0x0202cd32):
            m=scene_fixture(notification=token)
            c.compare('scene notification constructor token collision',m,name,() if name=='scene_flush' else (0,))
            if not any(t==token and n==1 for _,t,n in c.last['service_sites']):raise AssertionError('notification collision not reached')

def source_paths():
    paths=set(ownership.source_paths())|set(models.source_paths())|set(SOURCES)|{
        PARENT,SOURCE,'tools/effect_parameter_construction_machine.py','tools/verify_effect_parameter_construction.py',
        'tools/build_effect_parameter_construction.py','tests/test_effect_parameter_construction_machine.py',
        'tests/effect_parameter_construction_sanitize.c'}
    pending=[ROOT/path for path in SOURCES];seen=set()
    while pending:
        p=pending.pop().resolve()
        if p in seen:continue
        seen.add(p)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',p.read_text(),re.M):
            for child in (p.parent/name,ROOT/'firmware/include'/name):
                if child.is_file():
                    child=child.resolve();paths.add(child.relative_to(ROOT).as_posix());pending.append(child);break
    return sorted(paths)

PARTS={'smoke':smoke,'constructors':constructor_cases,'retained':retained_cases,'aliases':alias_cases,
    'recovery':recovery_cases,'collisions':collision_cases,'scenes':scene_cases}

def api_checks(c):
    checks=0;out=(U32*2)(0xdeadbeef,0xcafebabe);args=(U32*12)(0,0,20)
    execute=c.lib.hyperrig_effect_parameters_execute
    b=ownership.parent.Backend(c.program,fixture(),Script())
    for entry,p,result,io,expected in ((0,args,out,None,-200),(0,None,out,ctypes.byref(b.io),-200),
        (0,args,None,ctypes.byref(b.io),-200),(0,args,out,ctypes.byref(b.io),-202)):
        assert execute(entry,p,result,io)==expected;checks+=1
    for budget in (0,1,2,8,24,32):
        b=ownership.parent.Backend(c.program,fixture(),Script());b.io.work=budget
        assert execute(ENTRY_POINTS['commit'],args,out,ctypes.byref(b.io))==(-200 if not budget else -203)
        assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    # Preserve the frozen caller's zero-cap nested-helper result. This occurs
    # before the parameter write and before any new constructor join.
    b=ownership.parent.Backend(c.program,fixture(16),Script());b.io.work=16
    before=b.read(EFFECTS+70,2)
    assert execute(ENTRY_POINTS['commit'],args,out,ctypes.byref(b.io))==-200
    assert b.read(EFFECTS+70,2)==before and tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    # A reached zero-rate numerical domain fault is portable, not a native
    # firmware return. Check immediate propagation through each scene wrapper.
    for kind in (1,16,31):
        for name in ('scene_inner','scene_apply','scene_select','scene_flush'):
            m=scene_fixture(kind,True);setword(m,CONFIG+8,0);setword(m,ARENA+8192+628,1)
            b=ownership.parent.Backend(c.program,m,Script())
            status=c.lib.hyperrig_effect_parameters_scene(ENTRY_POINTS[name],0,out,ctypes.byref(b.io))
            assert status==-202 and not b.errors and b.read(0x01c34489,1)==1
            assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    class MissingOutput(ownership.parent.Backend):
        def map(self,opaque,address,size,writable):
            # Inject failure of the constructor's word request, after the
            # enclosing scene has obtained its cached larger byte view.
            if writable and address==EFFECTS+292 and size==4:return None
            return super().map(opaque,address,size,writable)
    for name in ('scene_inner','scene_apply','scene_select','scene_flush'):
        m=scene_fixture(1,True);b=MissingOutput(c.program,m,Script())
        untouched=b.read(EFFECTS+292,4);later=b.read(EFFECTS+296,4)
        status=c.lib.hyperrig_effect_parameters_scene(ENTRY_POINTS[name],0,out,ctypes.byref(b.io))
        assert status==-201 and not b.errors and b.read(0x01c34489,1)==1
        assert b.read(EFFECTS+288,4)==0x04000000 and b.read(EFFECTS+292,4)==untouched
        assert b.read(EFFECTS+296,4)==later and tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    return checks

def report(c,guards,mini_image):
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==PINNED and hashlib.sha256(app).hexdigest()==DECODED
    assert unpack_app(original)[2]['app.bin']==app
    if set(c.construction_sites)!=set(DIRECT_JOINS.items()):raise ValueError('all three actual constructor edges must execute')
    if not c.ownership_sites or not c.private or not c.prefixes:raise ValueError('resource/ownership lifetime evidence absent')
    code=c.program.code;joined=c.program.joined_code
    windows={hex(pc):{'start':pc,'end_exclusive':pc+item[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+item[1])).hexdigest()} for pc,item in sorted(code.items())}
    static={name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(a,b) in c.program.static_regions.items()}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI;body=unpack_app(raw)[2]['app.bin']
        for item in (*windows.values(),*static.values()):
            a,b=item['start'],item['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    return {'schema':1,'project':'HyperRig','component':'joined-effect-parameter-construction','result':'pass',
        'original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'integration_only':True,'new_original_functions':0,'functions':{},'new_static_data_ranges':[],
        'joined_bodies':{name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'decoded':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.coverage),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.coverage]} for name,(a,b) in REGIONS.items()},
        'instruction_coverage':{'new_decoded':0,'new_visited':0,'unvisited_new':[],
            'joined_decoded':len(joined),'joined_visited':len(joined&c.coverage),'unvisited_joined':sorted(joined-c.coverage),
            'all_decoded':len(code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(code)-c.coverage)},
        'derivative_provenance':check_derivative(),'static_data':static,'bound_instruction_windows':windows,'mini_v4_binding':binding,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'direct_construction_sites':[{'site':pc,'target':target,'calls':count} for (pc,target),count in sorted(c.construction_sites.items())],
        'direct_ownership_sites':[{'site':pc,'target':target,'calls':count} for (pc,target),count in sorted(c.ownership_sites.items())],
        'direct_resource_sites':[{'site':pc,'target':target,'calls':count} for (pc,target),count in sorted(c.resource_sites.items())],
        'actual_coefficient_requests':c.coefficients,'actual_exponential_calls':c.exp_calls,
        'actual_calls':{hex(k):v for k,v in sorted(c.real_calls.items())},'external_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'carried_calls':c.carried,'callback_mutation_cases':c.mutating,'native_private_flag_lifetimes':c.private,
        'live_object_alias_comparisons':c.live_aliases,
        'original_fourth_read_prefix_comparisons':c.prefixes,'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,
        'outputs_state_services_sha256':c.digest.hexdigest(),'hardware_test':False,'audio_test':False,'flashable':False,
        'limitations':['No new original function or static data exclusion; all 107 joined declarations were independently reconstructed earlier.',
            'All three direct construction calls execute original numerical bodies; allocator, free, mode and other remaining service sites stay explicit.',
            'Nested local numerical work caps and outer mapped-access budgets do not form a single native timing or arithmetic-operation counter.',
            'Original PROPOSED copies preserve native pointed-object aliases; no detached constructor runtime supplies output fixtures.',
            'The ownership fourth private-pointer read retains its previously established original prefix boundary.',
            'Zero-rate constructor scene faults and arbitrary budget/mapping guards are C-only checks; no new native fault-prefix equivalence is claimed.',
            'Loaded and joined instruction gaps remain explicit; this corpus does not reproduce every earlier standalone branch or establish full-firmware coverage.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--part',choices=tuple(PARTS)+('all',),default='all')
    p.add_argument('--output',type=Path);p.add_argument('--sanitizer-corpus',type=Path);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if args.output and (args.output.exists() or args.part!='all'):p.error('final report needs a fresh path and every corpus')
    check_derivative();replay=args.sanitizer_corpus.open('xb') if args.sanitizer_corpus else None;c=Corpus(args.library,replay)
    sources={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()} if args.output else {}
    for name in PARTS if args.part=='all' else (args.part,):
        PARTS[name](c);print(name,sum(c.counts.values()),'comparisons',flush=True)
    if replay:replay.close()
    guards=api_checks(c)
    if args.output:
        result=report(c,guards,args.mini_image)
        assert sources=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},'comparison source changed during run'
        result['source_sha256']=sources;result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',c.counts,'steps',c.steps,'construction sites',c.construction_sites)

if __name__=='__main__':main()
