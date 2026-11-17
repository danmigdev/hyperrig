"""Compare complete scene application, selection and real transition bodies."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,random,re,struct,sys
from pathlib import Path
from build_scene_application import C_NAMES
from scene_application_machine import (SceneApplicationProgram,REGIONS,REUSED,MAPPED,
    GLOBAL,STATE,EFFECTS,CONFIG,CONTROL,CALLBACKS,FILTERS,STAGED,TABLE,TABLE_BYTES,SERVICES,ROOT)

U32,U8=ctypes.c_uint32,ctypes.c_uint8
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32)
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),('call_budget',U32)]

def put(data,offset,value,size=4):data[offset:offset+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little')

def initial(types=(),*,mode=2,seed=0,transition=False):
    rng=random.Random(seed);memory=[bytearray(rng.randbytes(n)) for _,n in MAPPED]
    g,s,e,c,control,callbacks,filters,staged=memory
    put(g,88,0);put(g,44,24);g[8]=1;put(s,280,mode);s[740]=0;put(s,956,0)
    put(c,36,48077);c[12]=17;control[28]=1;control[218:230]=bytes(12)
    put(callbacks,732,0x0201a9ea)
    for i in range(16):
        p=480*i;e[p]=types[i] if i<len(types) else 0;e[p+1]=i%2;e[p+2]=int(i<len(types))
        for j in range(7):put(e,p+70+2*j,rng.randrange(-32768,32768),2)
    for scene in range(4):
        p=11936+260*scene;s[p]=1;s[p+1]=scene;s[p+6:p+22]=bytes(i%2 for i in range(16))
        put(s,p+2,(1<<len(types))-1,2);s[p+258]=int(transition)
        for i in range(16):s[p+22+14*i:p+36+14*i]=e[480*i+70:480*i+84]
        for j in range(6):put(s,p+246+2*j,0,2)
    return memory

class Script:
    """Unrecovered effect/platform services; never substitutes transition math."""
    def __init__(self,plan=None,mutations=None):
        self.plan=plan or {};self.mutations=mutations or {};self.seen={};self.clock=0
    def __call__(self,target,args,m):
        index=self.seen.get(target,0);self.seen[target]=index+1
        default=0
        if target==0x01C04862:self.clock=(self.clock+50000)&0xffffffff;default=self.clock
        value=self.plan.get(target,default)
        if isinstance(value,list):value=value[min(index,len(value)-1)]
        if callable(value):value=value(args,m,index)
        value&=0xffffffff
        if target in (0x0202F07E,0x0202FBA6) and (target==0x0202F07E or value!=0xfffffffa):
            m.write(EFFECTS+480*args[0]+70+2*args[1],args[2],2)
        if target in (0x02030530,0x020305F8) and not value:
            m.write(EFFECTS+480*args[0]+1,args[1],1)
        for mutate in self.mutations.get((target,index),()):mutate(args,m)
        return value

class CMemory:
    def __init__(self,memory):
        self.buffers=[(U8*len(b)).from_buffer_copy(b) for b in memory]
    def pointer(self,address,size):
        for (base,n),buffer in zip(MAPPED,self.buffers):
            if base<=address<=base+n and size<=base+n-address:return ctypes.addressof(buffer)+address-base
        raise ValueError(f'unmapped scene C address {address:#x}/{size}')
    def read(self,address,size):return int.from_bytes(ctypes.string_at(self.pointer(address,size),size),'little')
    def write(self,address,value,size):
        ctypes.memmove(self.pointer(address,size),(value&((1<<(8*size))-1)).to_bytes(size,'little'),size)
    def snapshot(self):return tuple(bytes(b) for b in self.buffers)

def load_library(path):
    lib=ctypes.CDLL(str(path.resolve()))
    for name in ('inner','apply'):
        f=getattr(lib,'hyperrig_scene_application_'+name);f.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(IO)];f.restype=ctypes.c_int
    lib.hyperrig_scene_application_report.argtypes=[U32,U32,ctypes.POINTER(U32),ctypes.POINTER(IO)]
    lib.hyperrig_scene_application_select.argtypes=[U32,ctypes.POINTER(IO)]
    lib.hyperrig_scene_application_flush.argtypes=[ctypes.POINTER(IO)]
    return lib

class Comparison:
    def __init__(self,lib):
        self.lib=lib;self.program=SceneApplicationProgram();self.coverage=set();self.steps=0
        self.counts={};self.services=set();self.internal=[];self.carried=self.mutating=self.real_notifications=0
        self.digest=hashlib.sha256()
    def run(self,label,memory,operation='inner',args=(0,),*,plan=None,mutations=None):
        native=self.program.execute(memory,operation,*args,boundary=Script(plan,mutations))
        m=CMemory(memory);calls=[];errors=[];script=Script(plan,mutations);result=U32(0xdeadbeef)
        def mapped(_,address,size,writable):
            try:return m.pointer(address,size)
            except Exception as exc:errors.append(exc);return None
        def call(_,target,raw,count):
            try:
                assert count==SERVICES.get(target,1)
                a=tuple(raw[i] for i in range(5));before=m.snapshot();value=script(target,a,m)
                calls.append((target,a,before,m.snapshot()));return value
            except Exception as exc:errors.append(exc);return 0
        map_cb,call_cb=MAP(mapped),CALL(call);io=IO(map_cb,call_cb,None,100000)
        f=getattr(self.lib,'hyperrig_scene_application_'+operation)
        status=f(*args,ctypes.byref(result),ctypes.byref(io)) if operation in ('inner','apply','report') else f(*args,ctypes.byref(io))
        assert status==0,(label,'API',status,errors)
        assert not errors,(label,errors)
        if calls!=native['calls']:
            for i,(a,b) in enumerate(zip(calls,native['calls'])):
                if a[:2]!=b[:2]:raise AssertionError((label,'service',i,'C',a[:2],'native',b[:2]))
                for when in (2,3):
                    for k,(x,y) in enumerate(zip(a[when],b[when])):
                        if x!=y:raise AssertionError((label,'service state',i,hex(a[0]),when,k,[(j,u,v) for j,(u,v) in enumerate(zip(x,y)) if u!=v][:16]))
            raise AssertionError((label,'service counts',len(calls),len(native['calls'])))
        if operation in ('inner','apply','report'):
            assert result.value==native['result'],(label,'result',result.value,native['result'])
        actual=m.snapshot()
        if actual!=native['memory']:
            for i,(x,y) in enumerate(zip(actual,native['memory'])):
                if x!=y:raise AssertionError((label,'state',i,[(j,u,v) for j,(u,v) in enumerate(zip(x,y)) if u!=v][:16]))
        self.coverage|=native['visited'];self.steps+=native['steps'];self.counts[operation]=self.counts.get(operation,0)+1
        self.services|={x[0] for x in calls};self.internal+=native['internal_calls']
        self.real_notifications+=len(native['real_notifications']);self.mutating+=bool(mutations)
        self.digest.update(json.dumps((operation,args,result.value)).encode())
        for data in actual:self.digest.update(data)
        return [bytearray(x) for x in actual]

def corpus(c):
    for mode in (0,1,2,3,0xffffffff):
        for scene in range(4):
            for op in ('inner','apply','select'):
                c.run(('empty',mode,scene,op),initial(mode=mode,seed=scene),op,(scene,))
    for type_ in range(1,41):
        for mode in (0,2):
            m=initial([type_],mode=mode,seed=type_)
            for i in range(7):put(m[1],11936+22+2*i,37+i,2)
            m[1][11936+6]^=1
            c.run(('changed',type_,mode),m)
    # Callee review establishes the probe's third argument and both enable
    # services' second argument independently of the shared service table.
    def check_parameter(a,m,i):
        raw=m.read(STATE+11958+14*a[0]+2*a[1],2)
        expected=raw if raw<32768 else raw|0xffff0000
        assert a[2]==expected,('desired parameter argument',a,expected)
        return 0
    def check_enabled(a,m,i):
        assert a[1]==m.read(STATE+11942+a[0],1),('desired enabled argument',a)
        return 0
    for mode in (0,2):
        for desired in (-32768,-2345,-1,0,32767):
            m=initial([37],mode=mode)
            for i in range(7):put(m[1],11958+2*i,desired,2)
            c.run(('signed service argument',mode,desired),m,plan={
                0x0202FD18:check_parameter,0x0202FBA6:check_parameter,0x0202F07E:check_parameter})
        for enabled in (0,1,2,255):
            m=initial([37],mode=mode);m[2][1]=int(not enabled);m[1][11942]=enabled
            c.run(('enable service argument',mode,enabled),m,plan={
                0x020305F8:check_enabled,0x02030530:check_enabled})
    for selector in (0,1,2,3,0xffffffff):
        for probe in (0,1,0xffffffff):
            m=initial([7,5,37],seed=selector)
            m[1][11936+22:11936+64]=bytes(42)
            c.run(('selector',selector,probe),m,'apply',(0,),plan={0x02028EB2:selector,0x0202FD18:probe})
    for value in (0,1,0xffffffff,0x7fffffff,0x80000000):
        for start in (0,1,0xffffffff):
            m=initial();put(m[0],44,value)
            c.run(('report',value,start),m,'report',(0x1234abcd,start))
    for scene in (0,1,2,3,4,255,0xffffffff):c.run(('select range',scene),initial(),'select',(scene,))
    for steps in (-17,-4,-1,0,1,4,17):
        m=initial([7]);put(m[1],956,steps)
        c.run(('flush',steps),m,'flush',())
    for scene in range(4):
        m=initial([5,7],transition=True);p=11936+260*scene
        for i in range(6):put(m[1],p+246+2*i,10+i*5,2)
        c.run(('actual transition',scene),m,'inner',(scene,))
    # Native retries, fallback accounting and raw enable bytes, through entries.
    for fast in (0,1,0xfffffffa,0xffffffff):
        for enabled in (0,1,2,255):
            for mode in (0,2):
                m=initial([5,7,37],mode=mode,seed=enabled)
                m[1][11942:11945]=bytes([enabled]*3)
                m[1][11958:12000]=bytes(42)
                c.run(('fast results',fast,enabled,mode),m,
                    plan={0x0202FBA6:fast,0x020305F8:fast,0x02030530:fast,0x020091D6:fast})
    for probe in (1,0xffffffff):
        for selector in (0,1,2):
            m=initial([37,37],mode=0);m[1][11958:11986]=bytes(28)
            c.run(('fallback probe failures',probe,selector),m,'apply',(0,),
                plan={0x0202FD18:lambda a,m,i,p=probe:0 if i<14 else p,0x02028EB2:selector})
    for route in ([1,0],[1,1],[0xffffffff,0xffffffff]):
        c.run(('route retry',route),initial([7]),plan={0x02008CA2:route})
    for transition_flag in (0,1,255):
        for duration in (0,1,2,255):
            for bank_enabled in (0,1):
                m=initial([7],transition=True);m[0][8]=transition_flag;m[3][12]=duration;m[4][28]=bank_enabled
                for i,v in enumerate((-32768,-121,-1,1,121,32767)):put(m[1],11936+246+2*i,v,2)
                c.run(('duration/reset',transition_flag,duration,bank_enabled),m)
    for count in (0,1,4,10,16):
        for seed in range(6):
            rng=random.Random(0x5ce0+seed+count*17);types=[rng.randrange(40) for _ in range(count)]
            m=initial(types,mode=rng.choice([0,2]),seed=seed)
            scene=seed%4;p=11936+scene*260;put(m[1],p+2,rng.getrandbits(16),2)
            for slot in range(count):
                m[1][p+6+slot]=rng.choice([0,1,2,255])
                for i in range(7):put(m[1],p+22+14*slot+2*i,rng.randrange(-32768,32768),2)
            c.run(('random slots',count,seed),m,'apply',(scene,),plan={
                0x0202FD18:lambda a,m,i:int(i%11==4),0x0202FBA6:lambda a,m,i:0xfffffffa if i%3==0 else 0,
                0x020305F8:lambda a,m,i:(0,1,0xfffffffa)[i%3],0x02028EB2:seed%3})
    for current in (0,1,2,3,0xffffffff,0x80000000):
        for available in range(16):
            for steps in (-5,5):
                m=initial();put(m[0],88,current);put(m[1],956,steps)
                for i in range(4):m[1][11936+260*i]=int(bool(available&(1<<i)))
                c.run(('flush availability',current,available,steps),m,'flush',())
    for clock in (0,1,0x80000000,0xffffffff):
        for scale in (0,1,24,0x80000000,0xffffffff):
            for started in (0,0xffffffff):
                m=initial();put(m[0],44,scale)
                c.run(('report wrap/clamp',clock,scale,started),m,'report',(clock,started),plan={0x01C04862:clock})
    # Mutations occur at real external boundaries. The caller must reread only
    # the fields that the original actually reloads, keeping captured values.
    cases=[
        (0x020027E4,lambda a,m:m.write(STATE+280,0,4)),
        (0x020027E4,lambda a,m:m.write(CONFIG+12,1,1)),
        (0x020027E4,lambda a,m:m.write(GLOBAL+8,0,1)),
        (0x020027E4,lambda a,m:m.write(EFFECTS,7,1)),
        (0x020027E4,lambda a,m:m.write(EFFECTS+2,0,1)),
        (0x020027E4,lambda a,m:m.write(STATE+11938,0,2)),
        (0x0202FD18,lambda a,m:m.write(STATE+11958+2*a[1],-2345,2)),
        (0x0202FD18,lambda a,m:m.write(EFFECTS,37,1)),
        (0x02008CA2,lambda a,m:m.write(STATE+11938,0xffff,2)),
        (0x02008CA2,lambda a,m:m.write(EFFECTS+480+74,-32768,2)),
        (0x020038FA,lambda a,m:m.write(STATE+11958,1234,2)),
        (0x020039E0,lambda a,m:m.write(STATE+12194,1,1)),
        (0x02008DE2,lambda a,m:m.write(STATE+12192,25,2)),
        (0x02028EB2,lambda a,m:m.write(CALLBACKS+24,0x87654321,4)),
        (0x02002D10,lambda a,m:m.write(STATE+740,1,1)),
    ]
    for i,(target,mutate) in enumerate(cases):
        m=initial([5,7],mode=2,transition=True);m[1][11958:11986]=bytes(28)
        c.run(('boundary mutation',i),m,'apply',(0,),plan={0x0202FBA6:0xfffffffa,0x02028EB2:1},
            mutations={(target,0):[mutate]})
    alternate=0x02010000
    m=initial([7],transition=True);put(m[5],732,alternate);put(m[1],12192,35,2)
    def alternate_mutation(a,m):
        m.write(STATE+12192,-120,2);m.write(CONFIG+36,48000,4);m.write(FILTERS,0x80000000,4)
    c.run('alternate transition callback',m,mutations={(alternate,0):[alternate_mutation]})
    m=initial([7,5,37],transition=True)
    for i in range(12):
        scene=i%4;p=11936+260*scene;put(m[1],p+250,i*7-50,2);put(m[1],p+256,i*5-25,2)
        m=c.run(('carried scene',i),m,'select',(scene,),plan={0x02028EB2:1 if i%3==0 else 0});c.carried+=1
    return c

def api_checks(lib):
    memory=CMemory(initial([7],transition=True));result=U32(0xdeadbeef);guards=0
    missing=set();unaligned=False
    def mapped(_,address,size,writable):
        if address in missing:return None
        return memory.pointer(address,size)+(1 if unaligned and address==FILTERS else 0)
    map_cb=MAP(mapped);call_cb=CALL(lambda _,t,a,n:0);io=IO(map_cb,call_cb,None,10000)
    f=lib.hyperrig_scene_application_inner
    for scene,out,ptr in ((4,ctypes.byref(result),ctypes.byref(io)),(0,None,ctypes.byref(io)),(0,ctypes.byref(result),None)):
        assert f(scene,out,ptr)==-200;guards+=1
    bad=IO(MAP(),call_cb,None,10000);assert f(0,ctypes.byref(result),ctypes.byref(bad))==-200;guards+=1
    bad=IO(map_cb,CALL(),None,10000);assert f(0,ctypes.byref(result),ctypes.byref(bad))==-200;guards+=1
    bad=IO(map_cb,call_cb,None,0);assert f(0,ctypes.byref(result),ctypes.byref(bad))==-200;guards+=1
    for address in (GLOBAL,STATE,EFFECTS,CONFIG,CALLBACKS):
        missing.add(address);assert f(0,ctypes.byref(result),ctypes.byref(io))==-201;missing.clear();guards+=1
    for address in (CONTROL,FILTERS,STAGED):
        missing.add(address);assert f(0,ctypes.byref(result),ctypes.byref(io))==-203;missing.clear();guards+=1
    unaligned=True;assert f(0,ctypes.byref(result),ctypes.byref(io))==-203;unaligned=False;guards+=1
    memory.write(CONTROL+28,0,1);memory.write(CONTROL+218,1281,2)
    assert f(0,ctypes.byref(result),ctypes.byref(io))==-203;guards+=1
    memory.write(CONTROL+28,1,1);io.call_budget=1
    assert f(0,ctypes.byref(result),ctypes.byref(io))==-202;guards+=1
    memory.write(GLOBAL+88,4,4);io.call_budget=10000
    assert lib.hyperrig_scene_application_flush(ctypes.byref(io))==-200;guards+=1
    assert result.value==0xdeadbeef
    return {'invalid_api_mapping_or_dependency_checks':guards,'guard_output_preserved':True}

def source_names():
    names=set()
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    names.update(('tools/build_scene_application.py','tests/test_scene_application_machine.py',
        'tests/scene_application_sanitize.c','research/input-manifest.json',
        'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md'))
    # These inherited arithmetic models execute through importlib without
    # registering modules in sys.modules, so imported-module discovery misses them.
    names.update('upstream/pi32v2-isa/tools/hwtest/semantics/'+name
                 for name in ('s.py','b2.py','r.py','_r_util.py'))
    pending=[ROOT/f'firmware/src/hyperrig_{name}.c' for name in C_NAMES]
    while pending:
        path=pending.pop();name=path.relative_to(ROOT).as_posix()
        if name in names:continue
        names.add(name)
        for include in re.findall(r'^#include "([^"]+)"',path.read_text(),re.M):
            local=path.parent/include;pending.append(local if local.is_file() else ROOT/'firmware/include'/include)
    return sorted(names)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mini-image',type=Path);args=p.parse_args()
    if not __debug__:raise RuntimeError('verification requires assertions')
    if args.output.exists():raise ValueError('use a new report output')
    lib=load_library(args.library);c=corpus(Comparison(lib));guards=api_checks(lib)
    new={pc for pc in c.program.code if any(a<=pc<b for a,b in REGIONS.values())}
    from dsp_transition_notification_machine import region_bytes,GAIN_TABLE,GAIN_BYTES
    from dsp_audio_path_machine import PRIOR_TABLE,TABLE as INITIALIZATION_TABLE
    from hyperrig.jieli import unpack_app
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()=='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    assert unpack_app(original)[2]['app.bin']==app
    functions={name:{'start':lo,'end_exclusive':hi,'bytes_sha256':hashlib.sha256(c.program.raw_regions[name]).hexdigest(),
        'decoded':sum(lo<=pc<hi for pc in c.program.code),'visited':sum(lo<=pc<hi for pc in c.coverage)}
        for name,(lo,hi) in (REGIONS|REUSED).items()}
    spans={'parameter_metadata':(TABLE,TABLE+TABLE_BYTES),'gain_table':(GAIN_TABLE,GAIN_TABLE+GAIN_BYTES),
        'coefficient_selector':(PRIOR_TABLE,PRIOR_TABLE+10),'initialization_gain':INITIALIZATION_TABLE}
    static={name:{'start':lo,'end_exclusive':hi,'sha256':hashlib.sha256(region_bytes(app,lo,hi)).hexdigest()}
        for name,(lo,hi) in spans.items()}
    mini_binding=None
    if args.mini_image:
        mini=args.mini_image.read_bytes();digest=hashlib.sha256(mini).hexdigest()
        assert digest=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        decoded=unpack_app(mini)[2]['app.bin']
        for pc,(_,size,*_) in c.program.code.items():assert region_bytes(decoded,pc,pc+size)==region_bytes(app,pc,pc+size),hex(pc)
        for lo,hi in (REGIONS|REUSED).values():assert region_bytes(decoded,lo,hi)==region_bytes(app,lo,hi)
        for lo,hi in spans.values():assert region_bytes(decoded,lo,hi)==region_bytes(app,lo,hi)
        mini_binding={'image_sha256':digest,'identical_regions':list(functions),
            'all_loaded_instruction_windows_identical':len(c.program.code),'identical_static_data':list(static)}
    report={'schema':1,'project':'HyperRig','result':'pass','component':'reconstructed-scene-application',
        'scope':'complete scene inner/wrapper/report with original selection callers and real transition/gain execution',
        'device_access':False,'flashable':False,'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'native_steps':c.steps,
        'newly_reconstructed_original_functions':len(REGIONS),'carried_calls':c.carried,'mutating_cases':c.mutating,
        'functions':functions,'static_data':static,'result_digest':c.digest.hexdigest(),'c_only_guards':guards,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(c.coverage&new),'unvisited_new':sorted(new-c.coverage),
            'all_decoded':len(c.program.code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(c.program.code)-c.coverage)},
        'actual_internal_targets':sorted(set(c.internal)),'external_targets_visited':sorted(c.services),
        'actual_installed_notifications':c.real_notifications,'scripted_recovered_kernel_replacements':0,
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_names()},
        'original_image_sha256':hashlib.sha256(original).hexdigest(),'decoded_sha256':hashlib.sha256(app).hexdigest(),
        'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),'mini_v4_binding':mini_binding,
        'compared':['native inner/wrapper/report results','all eight mapped native windows including unchanged bytes',
            'ordered service targets and semantic arguments','state before and after each external service',
            'actual transition requests, generated coefficients and installed gain notification in shared RAM'],
        'limitations':['effect probe/set/toggle, routing, mode, scheduling, clock and notification services remain explicit synthetic boundaries',
            'selection/flush incidental native return registers are not portable API results',
            'no concurrency, interrupts, retained pointers or arbitrary host aliases between distinct native windows',
            'direct scenes0..3; current-scene flush domain0..3 or signed-negative; inherited transition reset parameters bounded to +/-1280',
            'extreme pending-counter loop reduction is exercised in C sanitizers; full billion-step original loops are not replayed',
            'per-report inherited execution gaps remain separate from new-body coverage; no complete firmware or hardware claim']}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('total_comparisons','comparisons','native_steps','actual_installed_notifications','c_only_guards')}))
    print('New instruction coverage',len(c.coverage&new),'/',len(new))

if __name__=='__main__':main()
