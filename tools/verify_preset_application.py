"""Compare reconstructed application orchestration with complete original instructions."""
from __future__ import annotations
import argparse, ctypes, hashlib, json, random, re, struct, sys
from pathlib import Path
from preset_application_machine import (PresetApplicationProgram,REGIONS,REUSED,MAPPED,
    GLOBAL,STATE,WORKING,EFFECTS,CONTROL,CONFIG,CALLBACKS,LOCAL,OUTPUT,PRIVATE,TABLE,TABLE_BYTES,ROOT,buffers)
from build_preset_application import C_NAMES

U8,U32=ctypes.c_uint8,ctypes.c_uint32
class Runtime(ctypes.Structure):
    _fields_=[(name,U8*n) for name,(_,n) in zip(('globals','state','working','effects','control','configuration','callbacks'),MAPPED)]
class View(ctypes.Structure):
    _fields_=[('runtime',ctypes.POINTER(Runtime)),('scratch',ctypes.POINTER(U8)),
              ('outputs',ctypes.POINTER(U32)),('borrowed',ctypes.POINTER(U8)),('borrowed_bytes',U32)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),ctypes.POINTER(View))
class IO(ctypes.Structure):
    _fields_=[('call',CALL),('opaque',ctypes.c_void_p),('call_budget',U32)]

def put(data,offset,value,size=4):data[offset:offset+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little')
def initial(types=(),*,fast=False,seed=0):
    rng=random.Random(seed)
    memory=[bytearray(n) for _,n in MAPPED]
    memory[0][9:11]=b'\xff\xff';memory[2][2:4]=b'\xff\xff'
    memory[2][0]=4;memory[2][1]=len(types);memory[0][3]=1
    put(memory[1],280,2 if fast else 0);put(memory[0],44,24)
    memory[0][8]=1;memory[5][12]=17
    for i,t in enumerate(types):
        memory[2][12+18*i]=int(i>=10)
        memory[2][13+18*i]=t;memory[2][14+18*i]=i%2;memory[2][15+18*i]=i%3
        for j in range(7):put(memory[2],16+18*i+2*j,rng.randrange(-2000,2001),2)
        if fast:
            memory[3][480*i]=t;memory[3][480*i+1]=memory[2][14+18*i];memory[3][480*i+2]=1
            memory[3][480*i+4]=memory[2][15+18*i]
            memory[3][480*i+70:480*i+84]=memory[2][16+18*i:30+18*i]
            memory[4][348+10*(i>=10)+(i if i<10 else i-10)]=i
    if fast:memory[4][14:16]=bytes((min(len(types),10),max(len(types)-10,0)))
    return memory

class Script:
    """Synthetic downstream services. Their bodies are not reconstruction evidence."""
    def __init__(self,plan=None,records=None,mutations=None):
        self.plan=plan or {};self.records=records or {};self.mutations=mutations or {}
        self.seen={};self.clock=0;self.allocations=0
    def __call__(self,target,args,m):
        index=self.seen.get(target,0);self.seen[target]=index+1
        default=0
        if target==0x02002810:
            source,dest,count=args[:3];record=self.records.get(source)
            if record is None:default=1
            else:
                status,payload=record
                assert len(payload)<=count and (status or len(payload)==count)
                for i,b in enumerate(payload):m.write(dest+i,b,1)
                default=status
        elif target==0x01C04862:
            self.clock=(self.clock+50000)&0xffffffff;default=self.clock
        elif target==0x02030110:default=1
        elif target==0x0202ED2E:
            tempo=m.read(WORKING+8,2);tempo=tempo-65536 if tempo&32768 else tempo
            default=max(400,min(3000,tempo))
        elif target==0x02029AFC:
            p=args[0];value=m.read(EFFECTS+480*p+74,2) if p<16 else 0
            default=int(0<value<32768)
        elif target in (0x0202E710,0x0202EA90):
            default=self.allocations%16;self.allocations+=1
        entry=self.plan.get(target,default)
        if isinstance(entry,list):entry=entry[min(index,len(entry)-1)]
        if callable(entry):entry=entry(args,m,index)
        if isinstance(entry,tuple):
            value,writes=entry
            for address,bits,size in writes:m.write(address,bits,size)
        else:value=entry
        for callback in self.mutations.get((target,index),()):callback(args,m)
        return value&0xffffffff

class CMemory:
    def __init__(self,library,view):self.library,self.view=library,view
    def pointer(self,address,size):
        p=self.library.hyperrig_preset_application_map(self.view,address,size)
        if not p:raise ValueError(f'unmapped C address {address:#x}/{size}')
        return p
    def read(self,address,size):return int.from_bytes(ctypes.string_at(self.pointer(address,size),size),'little')
    def write(self,address,value,size):
        data=(value&((1<<(8*size))-1)).to_bytes(size,'little')
        ctypes.memmove(self.pointer(address,size),data,size)
    def snapshot(self):
        v=self.view.contents;r=v.runtime.contents
        return tuple(bytes(getattr(r,name)) for name,_ in Runtime._fields_)+(ctypes.string_at(v.outputs,8),)

def load_library(path):
    lib=ctypes.CDLL(str(path.resolve()))
    lib.hyperrig_preset_application_apply.argtypes=[ctypes.POINTER(Runtime),U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
    lib.hyperrig_preset_application_apply.restype=ctypes.c_int
    lib.hyperrig_preset_application_map.argtypes=[ctypes.POINTER(View),U32,U32]
    lib.hyperrig_preset_application_map.restype=ctypes.POINTER(U8)
    for name in ('parameter_order','parameter_metadata'):
        f=getattr(lib,'hyperrig_preset_application_'+name);f.argtypes=[U32,U32];f.restype=U32
    for name,count in (('parameter',2),('placement',1)):
        f=getattr(lib,'hyperrig_preset_application_'+name);f.argtypes=[ctypes.POINTER(Runtime)]+[U32]*count;f.restype=U32
    return lib

class Comparison:
    def __init__(self,lib):
        self.lib=lib;self.program=PresetApplicationProgram();self.coverage=set();self.steps=0
        self.counts={};self.services=set();self.internal=set();self.carried=0;self.mutating=0
        self.digest=hashlib.sha256()
    def run(self,label,memory,operation='apply',args=(0,),*,plan=None,records=None,mutations=None):
        native=self.program.execute(memory,operation,*args,boundary=Script(plan,records,mutations))
        r=Runtime()
        for (name,_),data in zip(Runtime._fields_,memory):getattr(r,name)[:]=data
        outputs=(U32*2).from_buffer_copy(memory[-1]);result=U32(0xdeadbeef);calls=[];errors=[]
        script=Script(plan,records,mutations)
        def callback(_,target,raw,view):
            try:
                a=tuple(raw[i] for i in range(5));m=CMemory(self.lib,view)
                before=m.snapshot();pointed=buffers(target,a,m);value=script(target,a,m)
                calls.append((target,a,before,pointed,m.snapshot(),buffers(target,a,m)))
                return value
            except Exception as exc:errors.append(exc);return 0
        cb=CALL(callback);io=IO(cb,None,100000)
        if operation=='apply':
            status=self.lib.hyperrig_preset_application_apply(ctypes.byref(r),args[0],outputs,ctypes.byref(result),ctypes.byref(io))
            assert status==0,(label,'API status',status,errors)
            value=result.value
        elif operation in ('parameter_order','metadata'):
            f=getattr(self.lib,'hyperrig_preset_application_'+('parameter_metadata' if operation=='metadata' else operation))
            value=f(*args)
        else:value=getattr(self.lib,'hyperrig_preset_application_'+operation)(ctypes.byref(r),*args)
        assert not errors,(label,errors)
        actual=tuple(bytes(getattr(r,name)) for name,_ in Runtime._fields_)+(bytes(outputs),)
        if calls!=native['calls']:
            for i,(a,b) in enumerate(zip(calls,native['calls'])):
                if a!=b:
                    if a[:2]!=b[:2]:raise AssertionError((label,'call',i,'C',a[:2],'native',b[:2]))
                    if a[3]!=b[3] or a[5]!=b[5]:raise AssertionError((label,'pointees',i,a[3],b[3],a[5],b[5]))
                    for when in (2,4):
                        for j,(x,y) in enumerate(zip(a[when],b[when])):
                            if x!=y:raise AssertionError((label,'call state',i,hex(a[0]),when,j,[(k,u,v) for k,(u,v) in enumerate(zip(x,y)) if u!=v][:16]))
            raise AssertionError((label,'call counts',len(calls),len(native['calls'])))
        assert value==native['result'],(label,'result',value,native['result'])
        if actual!=native['memory']:
            for j,(x,y) in enumerate(zip(actual,native['memory'])):
                if x!=y:raise AssertionError((label,'final memory',j,[(k,u,v) for k,(u,v) in enumerate(zip(x,y)) if u!=v][:16]))
        self.coverage|=native['visited'];self.steps+=native['steps'];self.counts[operation]=self.counts.get(operation,0)+1
        self.services|={c[0] for c in calls};self.internal|=set(native['internal_calls'])
        self.mutating+=bool(mutations)
        self.digest.update(json.dumps((operation,args,value)).encode())
        for data in actual:self.digest.update(data)
        return [bytearray(x) for x in actual]

def corpus(c):
    for preset in (0,1,31,126,127,255,0x7fffffff,0x80000000,0xffffffff):
        for fast in (False,True):c.run(('empty',preset,fast),initial(fast=fast),args=(preset,))
    for type_ in range(40):
        for fast in (False,True):c.run(('one',type_,fast),initial([type_],fast=fast,seed=type_))
    for n in range(17):
        for fast in (False,True):c.run(('many',n,fast),initial([(i%39)+1 for i in range(n)],fast=fast,seed=n))
    for type_ in (*range(41),0xff,0xffffffff,0x80000000):
        for index in (*range(9),0xffffffff,0x80000000):
            for operation in ('parameter_order','metadata'):
                c.run((operation,type_,index),initial(),operation,(type_,index))
    m=initial(list(range(1,17)),fast=True)
    for slot in (*range(18),0xffffffff,0x80000000):
        c.run(('placement',slot),m,'placement',(slot,))
        for index in (*range(8),0xffffffff):c.run(('parameter',slot,index),m,'parameter',(slot,index))
    # Each path starts at the real application entry; no mid-body coverage probes.
    for slot in range(15):
        for extended in (False,True):
            for reuse in (False,True):
                m=initial([5,7],fast=True,seed=slot);m[2][2]=slot
                header=bytearray(40);put(header,0,0x43474b54);put(header,4,8)
                put(header,8,0x2144df1c if extended else 0x12345678)
                base=(0xdf000+(slot<<13)) if slot<8 else 0xcf000+((slot-8)<<13)
                records={base:(0,header),base+44:(0,struct.pack('<I',0x87654321))}
                if reuse:
                    m[1][1780]=1;put(m[1],1784,0x87654321 if extended else 0x12345678);put(m[1],1788,8)
                c.run(('capture header',slot,extended,reuse),m,records=records)
    for slot in range(8):
        for format_ in (0,1):
            for reuse in (False,True):
                m=initial([1],fast=True);m[2][3]=slot
                header=bytearray(40);put(header,0,0x4a474b54 if format_ else 0x49474b54)
                put(header,4,8);put(header,8,1234);put(header,12,0xff800007)
                if reuse:
                    m[1][1796]=1;m[1][1797]=format_;put(m[1],1800,1234);put(m[1],1804,8);put(m[1],1808,0xff800007)
                c.run(('IR header',slot,format_,reuse),m,records={0xef000+(slot<<13):(0,header)})
    for status in (0,1,0xffffff91,0xffffff92,0xffffffff):
        for fallback in (0,1):
            for embedded in (False,True):
                m=initial([7,5]);m[2][2]=1;m[2][3]=2;put(m[0],60,0x02033c8c if embedded else 0)
                c.run(('load statuses',status,fallback,embedded),m,plan={0x020087cc:status,0x02008a62:status,0x02008586:fallback})
    for status in (0,1,0xfffffffe,0xfffffffd,0xfffffffc,0xffffffff,127,128,255):
        for fallback in (0,0xffffffff):
            c.run(('allocation',status,fallback),initial([7,5,1]),plan={0x0202e710:[status,0],0x0202ea90:fallback})
    for status in (0,1,0xffffffff):
        for types in ([1,7,5],[1],[7]):
            m=initial(types,fast=True);put(m[1],280,0)
            c.run(('rebuild reuse',types,status),m,plan={0x0203060a:[status,status],0x020091d6:status})
            m[2][13]=40
            c.run(('rebuild leftovers',types,status),m,plan={0x020090c4:status})
    for target in (0x0202fee4,0x02030110,0x02030906,0x02029afc,0x02030602,0x02030068,0x0202fbd6):
        for status in (0,1,0xffffffff,0xfffffffa):
            m=initial([7,5,1],fast=True,seed=9)
            m[2][14]=1;put(m[2],8,900,2)
            plan={target:status,0x0202ed2e:100,0x02030068:(1,((LOCAL+224,0x00800000,4),))}
            plan[target]=status
            c.run(('fast failure',hex(target),status),m,plan=plan)
    for cleanup in (0,1,2):
        m=initial([7,5,1],fast=True);put(m[1],416,1)
        c.run(('cleanup',cleanup),m,plan={0x0200907a:[int(cleanup!=0),int(cleanup==2)]})
    for counter_exit in (False,True):
        for calibration in (0,24,0xffffffff,0x80000000):
            m=initial();m[2][2]=1;put(m[1],280,1);m[1][29]=1;put(m[1],524,1)
            put(m[0],44,calibration);put(m[1],4084,0xfffffffe)
            def clock_mutation(a,view):view.write(STATE+4084,2,4)
            c.run(('polling',counter_exit,calibration),m,
                mutations={(0x01c04862,0 if counter_exit else 2):(clock_mutation,)})
    for mode in (0,1,2,255):
        for notification in (0,1,2,3,0xffffffff):
            m=initial([5,7]);m[2][1347]=mode<<7&255
            put(m[6],712,0x0f000100);put(m[6],24,0xfedcba98)
            c.run(('callbacks',mode,notification),m,plan={0x02028eb2:notification,0x02028de8:5,0x01c05e7e:1})
    m=initial([1,5],fast=True);m[4][14]=1
    c.run('short existing chain',m)
    m=initial([5],fast=True);m[2][1344]=1;m[0][8]=0
    c.run('fast resource compaction and single-step override',m,plan={0x0203086a:1,0x02028de8:5,0x01c05e7e:1})
    for fast in (False,True):
        for new_type in (1,5,7,39):
            def change_parameters(a,view,new_type=new_type):
                view.write(WORKING+13,new_type,1);view.write(WORKING+16,0x8001,2)
                view.write(WORKING+24,0x7fff,2);view.write(CONFIG+12,237,1)
            c.run(('poll mutation',fast,new_type),initial([7],fast=fast),
                mutations={(0x020027e4,0):(change_parameters,)})
    m=initial([5],fast=True);m[2][2:4]=b'\x01\x02'
    def change_slots(a,view):
        view.write(WORKING+2,3,1);view.write(WORKING+3,4,1);view.write(GLOBAL+10,4,1)
    c.run('priority mutation with captured and reloaded slots',m,mutations={(0x020054a8,0):(change_slots,)})
    for status in (0,1):
        m=initial();m[2][2]=1;header=bytearray(40)
        put(header,0,0x43474b54);put(header,4,8);put(header,8,0x2144df1c)
        def change_identity(a,view):view.write(LOCAL+148,0x10203040,4)
        c.run(('trailer read mutation',status),m,records={0xe1000:(0,header),0xe102c:(status,b'\x22\x33' if status else b'\x22\x33\x44\x55')},
              mutations={(0x02002810,1):(change_identity,)})
    for next_callback in (0,0x0f000104):
        m=initial([5]);put(m[6],712,0x0f000100)
        def change_callback(a,view):
            view.write(CALLBACKS+712,next_callback,4);view.write(CONFIG+12,99,1)
            view.write(WORKING+1424,0x7fff8000,4)
        c.run(('indirect callback replacement',next_callback),m,mutations={(0x0f000100,0):(change_callback,)})
    m=initial([0],fast=True);m[4][348]=255
    c.run('raw absent slot and shift masking',m,plan={0x0202fee4:1})
    m=initial([1,5,7],fast=True)
    for step in range(12):
        m=c.run(('carried application',step),m,args=(step,),plan={0x0202fee4:0 if step%3 else 1})
        m[2][14]^=1;c.carried+=1
    rng=random.Random(0x92fa)
    for case in range(240):
        n=rng.randrange(17);m=initial([rng.randrange(42) for _ in range(n)],fast=True,seed=case)
        m[2][0]=rng.randrange(7);m[2][1344]=rng.randrange(3);m[2][1346]=rng.randrange(3)
        m[2][1347]=rng.randrange(256);m[0][3]=rng.randrange(2);m[0][8]=rng.randrange(3)
        m[5][12]=rng.randrange(256);put(m[2],8,rng.choice((0,1,399,400,3000,3001,32767,32768,65535)),2)
        put(m[1],280,rng.choice((0,1,2,0xffffffff)));put(m[1],416,rng.randrange(2))
        m[2][1348:1360]=rng.randbytes(12)
        if n and case%3==0:m[2][13+18*rng.randrange(n)]=rng.randrange(42)
        if n and case%5==0:m[2][12+18*rng.randrange(n)]=3
        if case%7==0:m[4][14]=max(0,m[4][14]-1)
        if case%11==0:m[2][1]=255
        plan={0x0202fee4:rng.choice((0,1,0xffffffff)),0x02030906:rng.randrange(2),
              0x02030110:rng.randrange(2),0x0203060a:rng.choice((0,1)),0x02030602:rng.choice((0,1)),
              0x0200907a:rng.choice((0,1)),0x0202e710:rng.choice((0,15,0xfffffffe,0xfffffffd)),
              0x020091d6:rng.randrange(2),0x02028eb2:rng.randrange(4),0x0203086a:rng.randrange(2),
              0x02028de8:rng.randrange(3),0x01c05e7e:rng.randrange(3)}
        c.run(('random routing',case),m,plan=plan)
    return c

def api_checks(lib):
    r=Runtime();out=(U32*2)(111,222);result=U32(333);calls=[]
    cb=CALL(lambda *args:calls.append(args[1]) or 0);io=IO(cb,None,100)
    rp,op,qp,ip=ctypes.byref(r),out,ctypes.byref(result),ctypes.byref(io)
    before=bytes(r),bytes(out),result.value;invalid=0
    for args in ((None,0,op,qp,ip),(rp,0,None,qp,ip),(rp,0,op,None,ip),(rp,0,op,qp,None),
        (rp,0,op,qp,ctypes.byref(IO(CALL(),None,10))),(rp,0,op,qp,ctypes.byref(IO(cb,None,0)))):
        assert lib.hyperrig_preset_application_apply(*args)==-200
        assert (bytes(r),bytes(out),result.value)==before and not calls;invalid+=1
    for offset in (14,15):
        r.control[offset]=11;before_bad=bytes(r)
        assert lib.hyperrig_preset_application_apply(rp,0,op,qp,ip)==-200
        assert bytes(r)==before_bad and not calls;r.control[offset]=0;invalid+=1
    def invalid_callback(_,target,a,view):view.contents.runtime.contents.control[14]=11;return 0
    bad=CALL(invalid_callback)
    assert lib.hyperrig_preset_application_apply(rp,0,op,qp,ctypes.byref(IO(bad,None,100)))==-201
    assert r.control[14]==11;r.control[14]=0
    assert lib.hyperrig_preset_application_apply(rp,0,op,qp,ctypes.byref(IO(cb,None,1)))==-202
    scratch=(U8*256)();view=View(ctypes.pointer(r),scratch,out,ctypes.POINTER(U8)(),0)
    mapping=0
    for address,size in ((0,1),(0xffffffff,4),(TABLE,4),(GLOBAL-1,1),(GLOBAL+271,2),
                         (LOCAL+255,2),(OUTPUT+7,2),(PRIVATE,1)):
        assert not lib.hyperrig_preset_application_map(ctypes.byref(view),address,size);mapping+=1
    for base,n in MAPPED:
        assert lib.hyperrig_preset_application_map(ctypes.byref(view),base,n)
    return {'invalid_api_checks':invalid,'service_domain_checks':1,'budget_guard_checks':1,'mapping_rejections':mapping}

def source_names():
    names=set()
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    names.update(('tools/build_preset_application.py','tests/test_preset_application_machine.py',
        'tests/preset_application_sanitize.c','research/input-manifest.json',
        'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/docs/SOURCES.md'))
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
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mini-image',type=Path)
    args=p.parse_args()
    if not __debug__:raise RuntimeError('verification requires assertions')
    if args.output.exists():raise ValueError('use a new verification output')
    lib=load_library(args.library);c=corpus(Comparison(lib));guards=api_checks(lib)
    new={pc for pc in c.program.code if any(a<=pc<b for a,b in REGIONS.values())}
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();mini_binding=None
    functions={name:{'start':lo,'end_exclusive':hi,'bytes_sha256':hashlib.sha256(c.program.raw_regions[name]).hexdigest(),
        'decoded':sum(lo<=pc<hi for pc in c.program.code),'visited':sum(lo<=pc<hi for pc in c.coverage)}
        for name,(lo,hi) in (REGIONS|REUSED).items()}
    if args.mini_image:
        from hyperrig.jieli import unpack_app
        mini=args.mini_image.read_bytes();digest=hashlib.sha256(mini).hexdigest()
        assert digest=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        decoded=unpack_app(mini)[2]['app.bin']
        for name,(lo,hi) in (REGIONS|REUSED).items():
            assert decoded[lo-0x02000120:hi-0x02000120]==app[lo-0x02000120:hi-0x02000120],name
        for pc,(_,size,*_) in c.program.code.items():
            assert decoded[pc-0x02000120:pc-0x02000120+size]==app[pc-0x02000120:pc-0x02000120+size]
        assert decoded[TABLE-0x02000120:TABLE-0x02000120+TABLE_BYTES]==c.program.metadata
        mini_binding={'image_sha256':digest,'identical_regions':list(functions),
            'all_loaded_instruction_windows_identical':len(c.program.code),'metadata_table_identical':True}
    report={'schema':1,'project':'HyperRig','result':'pass','component':'reconstructed-preset-application',
        'scope':'complete preset application, reuse/rebuild decisions and actual asset/query dependencies; downstream services remain external',
        'device_access':False,'flashable':False,'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'native_steps':c.steps,
        'newly_reconstructed_original_functions':len(REGIONS),'carried_calls':c.carried,'mutating_cases':c.mutating,
        'functions':functions,'result_digest':c.digest.hexdigest(),**guards,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(c.coverage&new),'unvisited_new':sorted(new-c.coverage),
            'all_decoded':len(c.program.code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(c.program.code)-c.coverage)},
        'actual_internal_targets':sorted(c.internal),'external_targets_visited':sorted(c.services),
        'parameter_metadata_table':{'start':TABLE,'end_exclusive':TABLE+TABLE_BYTES,'sha256':hashlib.sha256(c.program.metadata).hexdigest(),
            'presence_bits':[sum(bool(struct.unpack_from('<I',c.program.metadata,t*84+i*12+8)[0])<<i for i in range(7)) for t in range(1,40)]},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_names()},
        'original_image_sha256':hashlib.sha256((ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()).hexdigest(),
        'decoded_sha256':hashlib.sha256(app).hexdigest(),'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),
        'mini_v4_binding':mini_binding,
        'compared':['original result and both output statuses','all seven public state regions',
            'ordered service targets and semantic arguments','state before and after each service','initialized service buffer arguments'],
        'limitations':['downstream effect/reconfiguration/capture/IR services are explicit scripted boundaries in this corpus',
            'physical storage, allocation, scheduler and clock bodies are not executed',
            'borrowed callback state; no re-entry, concurrent mutation, retained pointers or overlapping host objects',
            'chain counts at most ten each; original working effect count capped at sixteen',
            'positive external-call budget adds a host guard, not a native timeout status',
            'unused private stack bytes and incidental return registers are not persistent-state outputs',
            'host verification and relocatable pi32v2 objects; no target execution or complete firmware build']}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('total_comparisons','comparisons','native_steps','carried_calls','mutating_cases')}))
    print('Coverage',len(c.coverage&new),'/',len(new))

if __name__=='__main__':main()
