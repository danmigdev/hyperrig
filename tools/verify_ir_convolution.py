"""Compare complete IR construction against original instructions without hardware."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import random
import struct
from ir_convolution_machine import (IrConvolutionProgram, REGIONS, REUSED, ROOT, HEAP, DSP,
    CAPACITY, FLAGS, TAPS, STATUS, OBJECT, OBJECT_BYTES, WORK, WORK_BYTES, COPY, COPY_BYTES,
    PARAMETERS, TWIDDLES, PERMUTATION, REAL_TWIDDLES, OUTPUT, SCRATCH, ALLOCATE, FREE,
    ARITIES, MAPPED, effect_address, region_bytes)
from verify_ir_installation import (CState as PreviousState, CMemory as PreviousMemory,
    Runtime as InstallationRuntime, baseline as previous_baseline)
from build_ir_convolution import SOURCES

SOURCE_FILES=tuple(SOURCES)+tuple(source.replace('firmware/src/','firmware/include/hyperrig/').replace('.c','.h') for source in SOURCES)+(
    'firmware/include/hyperrig/hyperrig_biquad.h','firmware/include/hyperrig/hyperrig_biquad_chain.h',
    'tools/biquad_chain_machine.py','tools/biquad_coefficients_machine.py','tools/biquad_generator_machine.py',
    'tools/biquad_machine.py','tools/control_action_machine.py','tools/control_machine.py','tools/dot_machine.py',
    'tools/ir_convolution_machine.py','tools/ir_installation_machine.py','tools/ir_loader_machine.py',
    'tools/preset_assets_machine.py','tools/preset_preflight_machine.py','tools/preset_storage_machine.py',
    'tools/selection_machine.py','tools/verify_control_actions.py','tools/verify_controls.py',
    'tools/verify_ir_convolution.py','tools/verify_ir_installation.py','tools/verify_ir_loader.py',
    'tools/verify_preset_assets.py','tools/verify_preset_preflight.py','tools/verify_preset_storage.py',
    'tools/verify_selection.py','tools/build_ir_convolution.py','tests/test_ir_convolution_machine.py',
    'tests/ir_convolution_sanitize.c','research/input-manifest.json','hyperrig/jieli.py','hyperrig/__init__.py',
    'upstream/pi32v2-isa/pi32v2isa/__init__.py','upstream/pi32v2-isa/pi32v2isa/codec.py',
    'upstream/pi32v2-isa/pi32v2isa/table.py','upstream/pi32v2-isa/isa/pi32v2.toml',
    'upstream/pi32v2-isa/tools/hwtest/semantics/s.py','upstream/pi32v2-isa/tools/hwtest/semantics/b2.py',
    'third_party/ultrarig/NOTICE.md','third_party/ultrarig/LICENSE.md')

SERVICE = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32)
class Runtime(ctypes.Structure):
    _fields_ = [('installation', InstallationRuntime), ('allocation_callbacks',ctypes.c_uint8*8),
                ('flags',ctypes.c_uint8*4), ('effects',(ctypes.c_uint8*24)*16), ('status',ctypes.c_uint8*64)]
class IO(ctypes.Structure):
    _fields_ = [('call',SERVICE),('opaque',ctypes.c_void_p),('samples',ctypes.POINTER(ctypes.c_uint8)),
        ('sample_capacity',ctypes.c_uint32),('sample_token',ctypes.c_uint32),
        ('object',ctypes.POINTER(ctypes.c_uint8)),('object_capacity',ctypes.c_uint32),('object_token',ctypes.c_uint32),
        ('copy',ctypes.POINTER(ctypes.c_uint8)),('copy_capacity',ctypes.c_uint32)]

def words(data,offset=0,count=1):return struct.unpack_from('<'+'I'*count,data,offset)
def put(data,offset,*values):struct.pack_into('<'+'I'*len(values),data,offset,*values)
def float_word(value):return struct.unpack('<I',struct.pack('<f',value))[0]

def baseline(samples=(),fmt=1,gain=0x3F800000):
    memory=previous_baseline(samples)+(bytearray(struct.pack('<II',ALLOCATE,FREE)),bytearray(4),
        bytearray([0x91]*384),bytearray([0xB7]*64),bytearray([0xD6]*OBJECT_BYTES),
        bytearray([0xE3]*WORK_BYTES),bytearray([0xF4]*COPY_BYTES),bytearray(12))
    put(memory[17],0,HEAP if samples else 0,len(samples),fmt,0,0,len(samples));put(memory[18],0,gain)
    put(memory[20],0,1)
    for i in range(16):struct.pack_into('<h',memory[21],i*24,21);put(memory[21],i*24+8,0)
    put(memory[26],0,len(samples),0,fmt)
    return memory

def fft_fixture(memory,values=None):
    # Host trigonometry supplies arbitrary input words, never expected output.
    memory[24][PERMUTATION-WORK:PERMUTATION-WORK+128]=bytes(int(f'{i:07b}'[::-1],2) for i in range(128))
    for index,denominator,base in ((i,128,TWIDDLES) for i in range(64)):
        put(memory[24],base-WORK+index*8,float_word(math.cos(2*math.pi*index/denominator)),
            float_word(-math.sin(2*math.pi*index/denominator)))
    for i in range(129):put(memory[24],REAL_TWIDDLES-WORK+i*8,
        float_word(math.cos(2*math.pi*i/256)),float_word(-math.sin(2*math.pi*i/256)))
    values=values if values is not None else [0x3F800000]+[0]*255
    put(memory[24],0,*values)
    return memory

class CState(PreviousState):
    def __init__(self,memory):
        super().__init__(memory[:19])
        self.convolution=Runtime(self.installation,(ctypes.c_uint8*8).from_buffer_copy(memory[19]),
            (ctypes.c_uint8*4).from_buffer_copy(memory[20]),((ctypes.c_uint8*24)*16).from_buffer_copy(memory[21]),
            (ctypes.c_uint8*64).from_buffer_copy(memory[22]))
        self.installation=self.convolution.installation;self.ir=self.installation.loader;self.storage=self.ir.storage
        self.object=(ctypes.c_uint8*OBJECT_BYTES).from_buffer_copy(memory[23])
        self.work=(ctypes.c_uint8*WORK_BYTES).from_buffer_copy(memory[24])
        self.copy=(ctypes.c_uint8*COPY_BYTES).from_buffer_copy(memory[25])
        self.parameters=(ctypes.c_uint32*3).from_buffer_copy(memory[26])
    def arrays(self):
        return (self.convolution.allocation_callbacks,self.convolution.flags,
            (ctypes.c_uint8*384).from_buffer(self.convolution.effects),self.convolution.status,
            self.object,self.work,self.copy,(ctypes.c_uint8*12).from_buffer(self.parameters))
    def snapshot(self):return super().snapshot()+tuple(bytes(a) for a in self.arrays())
    def io(self,callback,token=OBJECT):
        return IO(callback,None,self.allocation,CAPACITY,HEAP,self.object,OBJECT_BYTES,token,self.copy,COPY_BYTES)

class CMemory(PreviousMemory):
    def __init__(self,state):
        super().__init__(state)
        for (base,_),data in zip(MAPPED,state.arrays()):
            self.extra.update({(effect_address(i) if base is None else base+i):(data,i) for i in range(len(data))})

class Script:
    def __init__(self,plan=None):self.plan,self.counts=plan or {},{}
    def __call__(self,target,argument,view):
        index=self.counts.get(target,0)+1;self.counts[target]=index
        result,writes=self.plan.get((target,index),self.plan.get(target,(OBJECT if target==ALLOCATE else 0,())))
        for address,value,size in writes:view.write(address,value,size)
        return result

def pointer(array,offset=0):return ctypes.cast(ctypes.byref(array,offset),ctypes.POINTER(ctypes.c_uint8))
def configure(library):
    u32=ctypes.c_uint32;ptr=ctypes.POINTER(ctypes.c_uint8);out=ctypes.POINTER(u32)
    rt,io=ctypes.POINTER(Runtime),ctypes.POINTER(IO)
    specs={'size':[u32],'cosine':[u32],'sine':[u32],'q31':[u32],'phase':[u32,u32,out],
        'sample':[rt,u32,u32,io,out],'resample':[rt,ptr,u32,u32,u32,u32,io],
        'produce':[rt,out,ptr,u32,u32,u32,io],'copy':[ptr,u32,ptr,u32,u32,u32],
        'fft128':[ptr,u32,ptr,u32,ptr,u32],'real256':[ptr,u32]*6,
        'construct':[rt,u32,u32,out,io,out],'reset':[ptr,u32,u32],'prepare':[rt,u32,u32,io]}
    functions={}
    for name,types in specs.items():
        f=getattr(library,'hyperrig_ir_convolution_'+name);f.argtypes=types
        f.restype=u32 if name in ('size','cosine','sine','q31') else ctypes.c_int;functions[name]=f
    return functions

class Comparison:
    def __init__(self,library):
        self.program=IrConvolutionProgram();self.functions=configure(ctypes.CDLL(str(library.resolve())))
        self.counts=dict.fromkeys(ARITIES,0);self.coverage=set();self.steps=0;self.producer_calls=0
        self.mutations=0;self.carried=0;self.external=set()
    def compare(self,memory,operation,*args,plan=None,carried=False):
        native=self.program.execute(memory,operation,*args,boundary=Script(plan))
        state,calls,errors=CState(memory),[],[];script=Script(plan)
        def service(_opaque,target,argument):
            try:
                calls.append((target,argument,state.snapshot()));return script(target,argument,CMemory(state))
            except Exception as error:errors.append(error);return 0
        callback=SERVICE(service);io=state.io(callback,args[2] if operation=='construct' else OBJECT)
        rt,out=ctypes.byref(state.convolution),ctypes.c_uint32(0xAABBCCDD)
        f=self.functions[operation];status=None
        if operation in ('size','cosine','sine','q31'):actual=f(*args)
        elif operation=='sample':status=f(rt,*args,ctypes.byref(io),ctypes.byref(out));actual=out.value
        elif operation=='phase':status=f(*args,ctypes.cast(state.work,ctypes.POINTER(ctypes.c_uint32)))
        elif operation=='resample':status=f(rt,state.work,WORK_BYTES,*args,ctypes.byref(io))
        elif operation=='produce':status=f(rt,state.parameters,state.work,WORK_BYTES,*args,ctypes.byref(io))
        elif operation=='copy':status=f(state.copy,COPY_BYTES,state.work,WORK_BYTES,*args)
        elif operation=='fft128':status=f(pointer(state.work,PERMUTATION-WORK),128,
            pointer(state.work,TWIDDLES-WORK),512,state.work,1024)
        elif operation=='real256':status=f(pointer(state.work,PERMUTATION-WORK),128,
            pointer(state.work,TWIDDLES-WORK),512,pointer(state.work,REAL_TWIDDLES-WORK),1032,
            state.work,1024,pointer(state.work,OUTPUT-WORK),1032,pointer(state.work,SCRATCH-WORK),1024)
        elif operation=='construct':
            status=f(rt,*args[:2],state.parameters,ctypes.byref(io),ctypes.byref(out));actual=out.value
        elif operation=='reset':status=f(state.object,OBJECT_BYTES,*args)
        else:actual=f(rt,*args,ctypes.byref(io))
        if errors:raise errors[0]
        if status is not None:
            assert status==0,(operation,args,'C API status',status)
            if operation not in ('sample','construct'):actual=native['result'] # Original void return is incidental.
        snapshot=state.snapshot()
        if actual&0xFFFFFFFF!=native['result'] or snapshot!=native['memory'] or calls!=native['calls']:
            diffs=[(i,next((j for j,(a,b) in enumerate(zip(x,y)) if a!=b),None))
                for i,(x,y) in enumerate(zip(snapshot,native['memory'])) if i!=2 and x!=y]
            detail=[]
            for i,offset in diffs:
                start=offset&~3;detail.append((i,start,snapshot[i][start:start+16].hex(),native['memory'][i][start:start+16].hex()))
            raise AssertionError((operation,args,actual,native['result'],detail,'calls',
                [(a,b) for a,b,_ in calls],[(a,b) for a,b,_ in native['calls']]))
        self.counts[operation]+=1;self.coverage.update(native['visited']);self.steps+=native.get('steps',0)
        self.producer_calls+=len(native['producer_calls']);self.external.update(a for a,_,_ in calls)
        self.mutations+=bool(plan and any(writes for _,writes in plan.values()));self.carried+=carried
        return native

def corpus(check):
    compare=check.compare;rng=random.Random(0x2962A315)
    for value in (0,1,127,128,129,3968,3969,4095,4096,4097,0x7FFFFFFF,0x80000000,0xFFFFFF80,0xFFFFFF81,0xFFFFFFFF,
                  *(rng.getrandbits(32) for _ in range(25))):compare(baseline(),'size',value)
    values=(0,0x80000000,1,0x80000001,0x3F000000,0xBF000000,0x3F7FFFFF,0x3F800000,0xBF800000,
            0xBF800001,0x3FC90FDB,0x40490FDB,0x7F800000,0xFF800000,0x7FC00000,0xFFC01234,0x7F812345,
            *(rng.getrandbits(32) for _ in range(40)))
    for operation in ('cosine','sine','q31'):
        for value in values:compare(baseline(),operation,value)
    for denominator in (1,3,64,128,256,0xFFFFFFFF):
        for value in (0,1,denominator//8,denominator//4,denominator//2,denominator-1,denominator,0xFFFFFFFF):
            compare(baseline(),'phase',value,denominator)
    for samples in ([],[-32768,0,32767,1,-1],[rng.randint(-32768,32767) for _ in range(4076)]):
        for index in (0,1,4,4075,4076,0x80000000,0xFFFFFFFF):
            for gain in (0x3F800000,0x38000000,0xC0000000,0x7FC00000):compare(baseline(samples),'sample',index,gain)
    print('IR size, phase polynomials, Q31 saturation and signed16 getter agree.',flush=True)
    for source_format in (0,1,255):
        for mode in (0,1,255):
            for start,count in ((0,0),(0,23),(1,18),(17,19),(4090,6)):
                compare(baseline([-32768,32767,1,-1,16384,-8192]*7,source_format),'resample',start,count,mode)
    for gain in (0,0x80000000,1,0xC0000000,0x7F800000,0x7FC01234):
        for mode in (0,1):compare(baseline([-32768,32767,1],1,gain),'resample',0,21,mode)
    for length,fade,start,count in ((0,0,0,0),(64,0,0,64),(64,32,0,64),(64,32,31,33),(4096,256,3968,128),(1,1,0,2)):
        memory=baseline([32767]*min(length+5,4076));put(memory[26],0,length,fade,1)
        compare(memory,'produce',start,count)
    memory=baseline();put(memory[25],0,*[rng.getrandbits(32) for _ in range(4096)])
    for start,count in ((0,0),(0,129),(3968,128),(4096,0)):compare(memory,'copy',start,count)
    for values in ([0]*256,[0x3F800000]+[0]*255,[float_word(math.sin(i*0.17)) for i in range(256)],
                   [rng.getrandbits(32) for _ in range(256)]):
        for op in ('fft128','real256'):compare(fft_fixture(baseline(),values),op)
    print('IR resampling, window producer and complete FFT/recombination agree.',flush=True)
    for count,producer,token in ((0,REGIONS['produce'][0],OBJECT),(1,0,OBJECT),(1,REGIONS['produce'][0],0)):
        compare(baseline([1]),'construct',count,producer,token)
    for count in (1,127,128,129,256,257,1024,3969,4096):
        for producer in (REGIONS['produce'][0],REGIONS['copy'][0]):
            samples=[rng.randint(-32768,32767) for _ in range(min(count,4076))]
            memory=baseline(samples);put(memory[26],0,count,min(64,count//2),1)
            put(memory[25],0,*[float_word(rng.uniform(-0.5,0.5)) for _ in range(count)])
            result=compare(memory,'construct',count,producer,OBJECT)
            if count in (1,129,4096):
                reset_memory=result['memory'];reset_memory=tuple(bytearray(x) if i!=2 else x for i,x in enumerate(reset_memory))
                object=reset_memory[23];put(object,8,71,93);frequency,history=words(object,24)[0]-OBJECT,words(object,48)[0]-OBJECT
                object[frequency:frequency+words(object,4)[0]*1032]=bytes([0x52])* (words(object,4)[0]*1032)
                object[history:history+1024]=bytes([0xA9])*1024
                compare(reset_memory,'reset',OBJECT,carried=True)
        print(f'IR constructor {count} samples agreed for both real producers.',flush=True)
    for kind in ('zero','impulse','nan','infinity','large'):
        memory=baseline([0]*129)
        value={'zero':0,'impulse':0x3F800000,'nan':0x7FC01234,'infinity':0x7F800000,'large':0x4F000000}[kind]
        put(memory[25],0,*([value]+[0]*128));compare(memory,'construct',129,REGIONS['copy'][0],OBJECT)
    for count,fmt,mode,budget in ((0,1,1,21),(1,1,0,21),(129,1,1,21),(129,0,1,21),(513,1,1,1),
                                (1024,1,1,0),(4076,0,1,21),(257,1,255,1),(17,1,1,-1)):
        memory=baseline([32767]+[0]*(count-1) if count else [],fmt);struct.pack_into('<h',memory[21],0,budget)
        put(memory[17],20,min(count,64));put(memory[21],8,0x12345678)
        compare(memory,'prepare',0,mode)
    for effect in (0,7,15):
        memory=baseline([32767]*65);put(memory[21],effect*24+8,0x12345678)
        compare(memory,'prepare',effect,1,plan={ALLOCATE:(0,())})
        memory[19][:4]=bytes(4);compare(memory,'prepare',effect,1)
    memory=baseline([32767]*513);put(memory[17],20,1)
    compare(memory,'prepare',0,1,plan={ALLOCATE:(OBJECT,((DSP+80,512,4),))})
    for address,value,size in ((FLAGS,0,4),(DSP+64,0,4),(DSP+80,1,4),(DSP+68,0,4),
                                (effect_address(8),0,4),(effect_address(8),0x98765432,4),(DSP+56,0,4)):
        memory=baseline([32767]*65);put(memory[21],8,0x12345678)
        compare(memory,'prepare',0,1,plan={ALLOCATE:(OBJECT,((address,value,size),))})
    for address,value in ((effect_address(8),0),(FLAGS,0),(STATUS,0x12345678),(DSP+64,0)):
        memory=baseline([32767]*65);put(memory[21],8,0x12345678)
        compare(memory,'prepare',0,1,plan={FREE:(0,((address,value,4),))})
    memory=compare(baseline([32767]*129),'prepare',3,1)['memory']
    compare(memory,'prepare',3,1,carried=True)
    print('IR allocation, construction, rollback, replacement and carried state agree.',flush=True)

def api_checks(check):
    state=CState(baseline([1]));calls=[];callback=SERVICE(lambda *args:calls.append(args) or OBJECT)
    io=state.io(callback);rt=ctypes.byref(state.convolution);ip=ctypes.byref(io);out=ctypes.c_uint32(99)
    f=check.functions;p=state.parameters;w=state.work;ob=state.object
    invalid=[('phase',(0,1,None)),('phase',(0,0,ctypes.byref(out))),
        ('sample',(None,0,0,ip,ctypes.byref(out))),('sample',(rt,0,0,None,ctypes.byref(out))),
        ('sample',(rt,0,0,ip,None)),('resample',(rt,None,4,0,1,1,ip)),
        ('resample',(rt,w,3,0,1,1,ip)),('resample',(rt,w,WORK_BYTES,4096,1,1,ip)),
        ('produce',(rt,None,w,4,0,1,ip)),('produce',(rt,p,w,3,0,1,ip)),
        ('copy',(state.copy,3,w,4,0,1)),('copy',(state.copy,COPY_BYTES,w,4,4096,1)),
        ('copy',(state.copy,COPY_BYTES,None,4,0,1)),
        ('fft128',(None,128,w,512,w,1024)),('fft128',(w,127,w,512,w,1024)),
        ('fft128',(w,128,w,511,w,1024)),('fft128',(w,128,w,512,w,1023)),
        ('real256',(w,128,w,512,w,1031,w,1024,w,1032,w,1024)),
        ('real256',(w,128,w,512,w,1032,w,1023,w,1032,w,1024)),
        ('real256',(w,128,w,512,w,1032,w,1024,w,1031,w,1024)),
        ('real256',(w,128,w,512,w,1032,w,1024,w,1032,w,1023)),
        ('reset',(None,OBJECT_BYTES,OBJECT)),('reset',(ob,55,OBJECT)),
        ('reset',(ob,OBJECT_BYTES,OBJECT)),('reset',(ob,OBJECT_BYTES,OBJECT+1)),
        ('construct',(rt,4097,REGIONS['copy'][0],p,ip,ctypes.byref(out))),
        ('construct',(rt,1,0x12345678,p,ip,ctypes.byref(out))),
        ('construct',(rt,1,REGIONS['produce'][0],None,ip,ctypes.byref(out))),
        ('construct',(rt,1,REGIONS['copy'][0],p,ip,None)),
        ('prepare',(rt,16,1,ip)),('prepare',(None,0,1,ip)),('prepare',(rt,0,1,None))]
    checked=0
    for operation,args in invalid:
        before=state.snapshot();assert f[operation](*args)==-200,(operation,args)
        assert state.snapshot()==before and not calls and out.value==99;checked+=1
    for member,value,operation in (('sample_capacity',1,'sample'),('sample_token',HEAP+2,'sample'),
        ('samples',None,'sample'),('object_capacity',9311,'construct'),('object_token',OBJECT+1,'construct'),
        ('object_token',0xFFFFF000,'construct'),('copy_capacity',3,'copy_construct'),('copy',None,'copy_construct'),
        ('call',SERVICE(),'prepare'),('object_capacity',9311,'prepare')):
        bad=state.io(callback);setattr(bad,member,value);before=state.snapshot()
        if operation=='sample':status=f['sample'](rt,0,0x3F800000,ctypes.byref(bad),ctypes.byref(out))
        elif operation=='prepare':status=f['prepare'](rt,0,1,ctypes.byref(bad))
        else:status=f['construct'](rt,1,REGIONS['copy' if operation=='copy_construct' else 'produce'][0],p,ctypes.byref(bad),ctypes.byref(out))
        assert status==-200 and state.snapshot()==before and not calls and out.value==99;checked+=1
    for values in ((4097,0,1),(1,2,1)):
        state.parameters[:]=values;before=state.snapshot()
        assert f['produce'](rt,p,w,4,0,1,ip)==-200 and state.snapshot()==before and not calls;checked+=1
    # Valid capacities with malformed permutation and history pointers are API guards.
    before=state.snapshot();assert f['fft128'](w,128,w,512,w,1024)==-200 and state.snapshot()==before;checked+=1
    for count,frequency,history in ((0,2616,5696),(1,0,7760),(1,3648,0),(33,36672,73808)):
        put(state.object,4,count);put(state.object,24,OBJECT+frequency);put(state.object,48,OBJECT+history)
        before=state.snapshot();assert f['reset'](ob,OBJECT_BYTES,OBJECT)==-200 and state.snapshot()==before;checked+=1
    guards=0
    for condition in ('allocation_token','source_growth','null_rollback'):
        state=CState(baseline([1]));events=[]
        if condition=='null_rollback':put(state.convolution.allocation_callbacks,4,0)
        def service(_opaque,target,argument):
            events.append((target,argument))
            if target==ALLOCATE:
                if condition=='source_growth':put(state.installation.dsp,4,4077)
                return OBJECT+4 if condition=='allocation_token' else OBJECT
            return 0
        cb=SERVICE(service);guarded=state.io(cb)
        assert f['prepare'](ctypes.byref(state.convolution),0,condition!='null_rollback',ctypes.byref(guarded))==-201
        assert len(events)==(2 if condition=='source_growth' else 1);guards+=1
    return checked,guards

def verify(library,output,mini_image=None):
    if not __debug__:raise RuntimeError('run without Python optimization')
    sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(SOURCE_FILES)}
    check=Comparison(library);corpus(check);invalid,guards=api_checks(check)
    new={pc for start,end in REGIONS.values() for pc in check.program.code if start<=pc<end}
    missing=sorted(new-check.coverage)
    assert missing==[0x020319BE],list(map(hex,missing))
    # The loop variable starts at 0 and increments by 1. At 128 the branch at
    # 0x0203199a jumps to the fixed Nyquist pair, so the bottom value never is 129.
    proof={0x02031996:'r14 = 0',0x0203199A:'if (r14 == 128) goto 34',
           0x020319AE:'r14 = r14 + 1',0x020319BA:'if (r14 != 129) goto -36',0x020319BE:'goto 22'}
    assert all(check.program.code[address][0]==text for address,text in proof.items())
    from ir_installation_machine import REGIONS as IR_REGIONS
    dependencies={name:IR_REGIONS[name] for name in ('budget','convert','limit','effective','raw_length')}
    groups=((REGIONS,check.program.convolution_regions),(REUSED,check.program.reused_regions),
        ({'installation_'+name:bounds for name,bounds in dependencies.items()},
         {'installation_'+name:check.program.installation_regions[name] for name in dependencies}))
    mini_binding=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        app=unpack_app(raw)[2]['app.bin']
        for regions,originals in groups:
            for name,(start,end) in regions.items():assert region_bytes(app,start,end)==originals[name],name
        assert region_bytes(app,TAPS,TAPS+36)==check.program.taps
        mini_binding={'image_sha256':digest,'byte_identical_function_regions':sum(len(regions) for regions,_ in groups),
                      'byte_identical_coefficient_bytes':36}
    joined={pc for regions,_ in groups for start,end in regions.values() for pc in check.program.code if start<=pc<end}
    report={'schema':1,'project':'HyperRig','result':'pass','scope':'Complete original IR convolution construction and numerical dependencies',
        'original_image_sha256':'2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059',
        'comparisons':check.counts,'total_comparisons':sum(check.counts.values()),'producer_calls':check.producer_calls,
        'mutating_service_cases':check.mutations,'carried_state_calls':check.carried,'original_instruction_steps':check.steps,
        'invalid_api_checks':invalid,'api_guard_checks':guards,
        'instruction_coverage':{'new_visited':len(new&check.coverage),'new_decoded':len(new),
            'joined_visited':len(joined&check.coverage),'joined_decoded':len(joined),'unvisited_joined':sorted(joined-check.coverage),
            'all_visited':len(check.coverage),'all_decoded':len(check.program.code),
            'unvisited_new':missing,'missing_classification':{'0x020319be':'unreachable from the complete constructor entry: index128 branches to the fixed Nyquist pair before index129'},
            'constructor_loop_proof':{hex(pc):text for pc,text in proof.items()}},
        'functions':{name:{'start':start,'end_exclusive':end,'bytes_sha256':hashlib.sha256(raws[name]).hexdigest(),
            'instructions':sum(start<=pc<end for pc in check.program.code)} for regions,raws in groups for name,(start,end) in regions.items()},
        'resampling_coefficients':{'start':TAPS,'end_exclusive':TAPS+36,'sha256':hashlib.sha256(check.program.taps).hexdigest(),
                                  'signed_words':list(struct.unpack('<9i',check.program.taps))},
        'source_sha256':sources,'mini_v4_binding':mini_binding,'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),
        'external_services':['synthetic allocation target','synthetic free target'],
        'compared':['semantic returns','all 27 mapped state and storage regions','all allocated object bytes including reserved regions',
            'ordered allocation/free targets, arguments and complete state at every boundary'],
        'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'limitations':['allocation/free use explicit synchronous services; no allocator implementation or hardware was executed',
            'constructor and producers are bounded to 4096 outputs and 4076 signed16 source samples; both original producer targets execute internally',
            'runtime, IO, parameters, outputs, source, copy and object storage are distinct; reset requires coherent constructor history pointers',
            'no asynchronous mutation, concurrent reentry, physical float measurement, convolution processing or USB/audio execution',
            '0x020319be is retained in the reconstruction scope but statically unreachable from the constructor entry',
            'loaded inherited functions are not all reached by this IR corpus; no global execution percentage is claimed']}
    assert sources=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},'input sources changed during verification'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('result','total_comparisons','comparisons','instruction_coverage')}))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args()
    if args.output.exists():parser.error('preserve reports; choose a new output path')
    verify(args.library,args.output,args.mini_image)
