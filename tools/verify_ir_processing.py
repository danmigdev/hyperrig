"""Independent original-instruction comparisons for integer IR runtime processing."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
from ir_processing_machine import (IrProcessingProgram,REGIONS,ARITIES,ROOT,OBJECT,OBJECT_BYTES,WORK,COPY,
    GLOBALS,DESCRIPTOR,AUDIO,MMIO,READ,WRITE,SYNC,EXTRA,DESCRIPTORS,INDICES,CONSTRUCTION_REGIONS,region_bytes)
from verify_ir_convolution import (baseline as previous_baseline,CState as PreviousState,CMemory as PreviousMemory,
    configure as configure_constructor,SERVICE,put,words,float_word,pointer,SOURCE_FILES as CONSTRUCTION_SOURCE_FILES)
from ir_convolution_machine import REUSED,TAPS
from ir_installation_machine import REGIONS as INSTALLATION_REGIONS

SOURCE_FILES=CONSTRUCTION_SOURCE_FILES+('firmware/src/hyperrig_ir_processing.c',
    'firmware/include/hyperrig/hyperrig_ir_processing.h','tools/ir_processing_machine.py',
    'tools/verify_ir_processing.py','tools/build_ir_processing.py','tests/test_ir_processing_machine.py',
    'tests/ir_processing_sanitize.c')

KERNELS=('input','fft64','merge','forward','multiply','inverse','output','mix','crossfade',
         'hardware_input','hardware_forward','hardware_scale','hardware_output')
CALL=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32)
P=ctypes.POINTER(ctypes.c_uint8);U=ctypes.c_uint32
class Runtime(ctypes.Structure):_fields_=[('globals',ctypes.c_uint8*16),('descriptor',ctypes.c_uint8*16)]
class IO(ctypes.Structure):_fields_=[('call',CALL),('opaque',ctypes.c_void_p)]
class View(ctypes.Structure):_fields_=[('object',P),('object_capacity',U),('object_token',U),('audio',P),('audio_capacity',U)]
class Buffers(ctypes.Structure):_fields_=[('data',P*4),('capacity',U*4)]

def baseline(samples=(),fmt=1):
    memory=previous_baseline(samples,fmt)+(bytearray(16),bytearray([0x82]*16),bytearray([0x91]*512))
    put(memory[20],0,0);return memory
def permutation(index):return ((((index*8)&48)|((index>>1)&12)|((index>>5)&3))<<3)|((index*512)&512)
def put_permutation(data,offset=0):put(data,offset+1024,*map(permutation,range(128)))

class CState(PreviousState):
    def __init__(self,memory):
        super().__init__(memory[:27]);self.processing=Runtime((ctypes.c_uint8*16).from_buffer_copy(memory[27]),
            (ctypes.c_uint8*16).from_buffer_copy(memory[28]));self.audio=(ctypes.c_uint8*512).from_buffer_copy(memory[29])
    def snapshot(self):return super().snapshot()+(bytes(self.processing.globals),bytes(self.processing.descriptor),bytes(self.audio))
    def view(self,token=OBJECT):return View(self.object,OBJECT_BYTES,token,self.audio,512)
class CMemory(PreviousMemory):
    def __init__(self,state):
        super().__init__(state)
        for (base,_),data in zip(EXTRA,(state.processing.globals,state.processing.descriptor,state.audio)):
            self.extra.update({base+i:(data,i) for i in range(len(data))})
    def resolve(self,address):
        if not address:return P(),0
        data,offset=self.extra[address];return pointer(data,offset),len(data)-offset

class Trace:
    def __init__(self,*,timeout_launch=None,writes=None):
        self.timeout_launch=timeout_launch;self.writes=writes or {};self.launches=0;self.events=0
        self.digest=hashlib.sha256();self.previous_snapshot=None;self.state_digest=None;self.prefix=[]
        self.reads=0;self.counts={}
    def __call__(self,operation,address,value,view):
        snapshot=view.snapshot() if hasattr(view,'snapshot') else view.state.snapshot()
        if snapshot is not self.previous_snapshot and snapshot!=self.previous_snapshot:
            h=hashlib.sha256()
            for i,data in enumerate(snapshot):h.update(bytes((data,)) if i==2 else data)
            self.state_digest=h.digest();self.previous_snapshot=snapshot
        self.digest.update(struct.pack('<III',operation,address,value));self.digest.update(self.state_digest)
        if len(self.prefix)<12:self.prefix.append((operation,address,value,self.state_digest.hex()))
        self.events+=1;key=(operation,address);index=self.counts.get(key,0)+1;self.counts[key]=index
        if operation==READ:self.reads+=1
        if operation==WRITE and address==MMIO and value==257:self.launches+=1
        for where,word,size in self.writes.get((operation,address,index),()):view.write(where,word,size)
        return 0 if operation!=READ or self.launches==self.timeout_launch else 128
    def summary(self):return self.events,self.reads,self.launches,self.digest.hexdigest()

class CTraceMemory(CMemory):
    def __init__(self,state):super().__init__(state);self.state=state

def configure(library):
    functions={};rt=ctypes.POINTER(Runtime);io=ctypes.POINTER(IO)
    specs={'run':[rt,ctypes.POINTER(View),U,U,U,io],'wait':[rt,io],'start':[rt,U,U,U,U,io],
        'kernel':[U,ctypes.POINTER(Buffers),ctypes.POINTER(U),ctypes.POINTER(U)]}
    for name,args in specs.items():
        function=getattr(library,'hyperrig_ir_processing_'+name);function.argtypes=args;function.restype=ctypes.c_int;functions[name]=function
    return functions

class Comparison:
    def __init__(self,library):
        self.program=IrProcessingProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.functions=configure(self.library);self.constructor=configure_constructor(self.library)
        self.counts=dict.fromkeys(ARITIES,0);self.coverage=set();self.steps=0;self.entries={};self.mmio_events=0
        self.constructed={};self.carried=0;self.mutations=0;self.timeouts=0
    def compare(self,memory,operation,*arguments,buffers=None,trace=None):
        trace=trace or {};nt,ct=Trace(**trace),Trace(**trace)
        if operation in KERNELS:
            addresses=tuple(buffers or (WORK,COPY,WORK+4096,OBJECT));a=tuple(arguments)+(0,)*(4-len(arguments))
            if operation=='input':native_args=addresses
            elif operation=='fft64':native_args=(addresses[0],addresses[1]|a[0])
            elif operation=='merge':native_args=addresses[:2]
            elif operation=='forward':native_args=(addresses[0],addresses[1]+a[1]*8,addresses[2],a[0])
            elif operation=='multiply':native_args=(addresses[0],addresses[1],a[0]|a[1]<<16,addresses[2])
            elif operation in ('inverse','output'):native_args=(*addresses[:3],a[0])
            elif operation=='mix':native_args=(*addresses[:3],a[0])
            elif operation=='crossfade':native_args=(*addresses[:3],*a)
            elif operation=='hardware_input':native_args=addresses[:2]
            elif operation=='hardware_forward':native_args=(addresses[0],addresses[1]+a[1]*8,a[0])
            elif operation=='hardware_scale':native_args=(addresses[0],a[0])
            else:native_args=(*addresses[:2],a[0])
        else:native_args=arguments
        native=self.program.execute(memory,operation,*native_args,mmio=nt)
        state=CState(memory);cm=CTraceMemory(state);out=U(0xAABBCCDD);errors=[]
        def call(_opaque,op,address,value):
            try:return ct(op,address,value,cm)
            except Exception as error:errors.append(error);return 0
        callback=CALL(call);io=IO(callback,None);rt=ctypes.byref(state.processing)
        actual=native['result']
        if operation in KERNELS:
            arrays,capacities=zip(*(cm.resolve(address) for address in addresses))
            view=Buffers((P*4)(*arrays),(U*4)(*capacities));args=(U*4)(*a)
            status=self.functions['kernel'](KERNELS.index(operation),ctypes.byref(view),args,ctypes.byref(out))
            assert status==0,(operation,arguments,status)
            if operation=='multiply':actual=out.value
            else:assert out.value==0xAABBCCDD,('void kernel changed result',operation)
        elif operation=='process':
            view=state.view(arguments[0]);status=self.functions['run'](rt,ctypes.byref(view),*arguments[1:],ctypes.byref(io))
            assert status==0,('processing API',status)
        elif operation=='construct':
            call_constructor=SERVICE(lambda *args:0);constructor_io=state.io(call_constructor,arguments[2])
            assert self.constructor['construct'](ctypes.byref(state.convolution),*arguments[:2],state.parameters,
                ctypes.byref(constructor_io),ctypes.byref(out))==0;actual=out.value
        else:actual=self.functions[operation](rt,*arguments,ctypes.byref(io))
        if errors:raise errors[0]
        snapshot=state.snapshot()
        if actual&0xFFFFFFFF!=native['result'] or snapshot!=native['memory'] or nt.summary()!=ct.summary():
            differences=[]
            for index,(left,right) in enumerate(zip(snapshot,native['memory'])):
                if index!=2 and left!=right:
                    offset=next(i for i,(a,b) in enumerate(zip(left,right)) if a!=b)&~3
                    differences.append((index,offset,left[offset:offset+24].hex(),right[offset:offset+24].hex()))
            raise AssertionError((operation,arguments,actual,native['result'],differences,'MMIO',nt.summary(),ct.summary(),nt.prefix,ct.prefix))
        self.counts[operation]+=1;self.coverage.update(native['visited']);self.steps+=native['steps'];self.mmio_events+=nt.events
        self.mutations+=bool(trace.get('writes'));self.timeouts+=nt.reads>=200001
        for address,count in native['entries'].items():self.entries[address]=self.entries.get(address,0)+count
        return native

def corpus(check):
    rng=random.Random(0x1C12064);compare=check.compare
    for case in range(4):
        memory=baseline()
        for index in (23,24,25,29):
            values=([0]*(len(memory[index])//4) if case==0 else [0x7FFFFFFF]*(len(memory[index])//4) if case==1 else
                [0x80000000]*(len(memory[index])//4) if case==2 else [rng.getrandbits(32) for _ in range(len(memory[index])//4)])
            put(memory[index],0,*values)
        put_permutation(memory[25]);put_permutation(memory[23])
        compare(memory,'input',buffers=(WORK,WORK+512,WORK+1024,COPY))
        for skip in (0,1):compare(memory,'fft64',skip)
        compare(memory,'merge')
        for partitions,current in ((1,0),(2,0),(2,1),(32,0),(32,31)):
            compare(memory,'forward',partitions,current,buffers=(WORK,OBJECT,COPY,0))
            compare(memory,'multiply',partitions,current,buffers=(OBJECT,OBJECT+33032,WORK,0))
            compare(memory,'hardware_forward',partitions,current,buffers=(WORK,OBJECT,0,0))
        for shift in (0,1,8,31,38,63):
            compare(memory,'inverse',shift,buffers=(WORK,COPY,WORK+4096,0))
            compare(memory,'hardware_scale',shift)
        for shift in (-31,-1,0,1,30):
            compare(memory,'output',shift&0xFFFFFFFF)
            compare(memory,'hardware_output',shift&0xFFFFFFFF)
        for gains in (0,1,0x8000,0x80008000,0xFFFFFFFF):
            compare(memory,'mix',gains)
            compare(memory,'mix',gains,buffers=(WORK,COPY,0,0))
        for gains in ((0,32768,32768,0),(32768,0,0,32768),(0xFFFFFFFF,1,0x80000000,0x7FFFFFFF)):
            compare(memory,'crossfade',*gains)
            compare(memory,'crossfade',*gains,buffers=(WORK,WORK,COPY,0))
            compare(memory,'crossfade',*gains,buffers=(COPY,WORK,COPY,0))
        for destination in (WORK,COPY):compare(memory,'mix',0xFFFFFFFF,buffers=(WORK,destination,COPY,0))
        for partitions,current in ((3,0),(3,1),(3,2),(17,16)):
            compare(memory,'multiply',partitions,current,buffers=(OBJECT,OBJECT+33032,WORK,0))
        compare(memory,'hardware_input')
        print(f'Integer IR numerical stages agree for fixture {case}.',flush=True)
    for count in (1,129,4096):
        memory=baseline([32767]+[0]*min(count-1,4075));put(memory[26],0,count,0,1)
        memory=compare(memory,'construct',count,CONSTRUCTION_REGIONS['produce'][0],OBJECT)['memory']
        check.constructed[count]=memory
        gains=((0x3F800000,0),(0x3F000000,0x3F000000),(0x40800000,0),(0,0x3F800000),(0x7FC00000,0),
               (0x3F800000,0),(0x3F800000,0),(0x40800000,0),(0x40800000,0),
               (0x7F800000,0x3F800000),(0xFF800000,0x3F800000),(0x80000000,1))
        for block in range(35 if count==4096 else 12):
            memory=tuple(bytearray(x) if i!=2 else x for i,x in enumerate(memory))
            put(memory[29],0,*[rng.getrandbits(32) for _ in range(128)])
            wet,dry=gains[block%len(gains)]
            memory=compare(memory,'process',OBJECT,128,wet,dry)['memory']
            check.carried+=1
        print(f'Original constructor and carried IR processing agree for {count} coefficients.',flush=True)
    memory=baseline();put(memory[25],0,0);put(memory[26],0,1,0,1)
    memory=compare(memory,'construct',1,CONSTRUCTION_REGIONS['copy'][0],OBJECT)['memory']
    for wet,dry in ((0x3F000000,0x3F000000),(0x3F000000,0x3F000000),(0x3F000000,0),(0x3F000000,0)):
        memory=compare(memory,'process',OBJECT,128,wet,dry)['memory'];check.carried+=1
    for size in (0,1,255,256,512,768,1024,1280,1536,1792,2048,0xFFFFFFFF):
        for reverse in (0,1,255):compare(baseline(),'start',size,reverse,0x12345678,0x89ABCDEF)
    compare(baseline(),'wait')
    memory=baseline();put(memory[27],12,1);compare(memory,'wait')
    compare(memory,'start',256,1,WORK,COPY)
    # Mutation occurs at an actual MMIO boundary, after its complete-state witness.
    mutations={(SYNC,0,1):((GLOBALS+4,0xFFFFFFFF,4),(DESCRIPTOR+12,0x10203040,4)),
        (WRITE,MMIO+4,1):((GLOBALS+4,0xFFFFFFFE,4),),
        (READ,MMIO,1):((GLOBALS+8,0xFFFFFFFF,4),(DESCRIPTOR+8,0x76543210,4)),
        (SYNC,0,2):((GLOBALS+12,0xFF,4),(GLOBALS,0xFFFFFFFF,4))}
    compare(memory,'start',512,0,WORK,COPY,trace={'writes':mutations})
    compare(memory,'wait',trace={'writes':mutations})
    compare(memory,'wait',trace={'timeout_launch':0,'writes':mutations})
    compare(memory,'start',256,0,WORK,COPY,trace={'timeout_launch':0,'writes':mutations})
    for token,count,active in ((0,128,1),(OBJECT,0,1),(OBJECT,127,1),(OBJECT,129,1),(OBJECT,128,0)):
        memory=baseline();put(memory[23],0,active);compare(memory,'process',token,count,0x3F800000,0)
    for count in (1,129,4096):
        memory=tuple(bytearray(x) if i!=2 else x for i,x in enumerate(check.constructed[count]))
        put(memory[23],548,1);put(memory[29],0,*[rng.getrandbits(32) for _ in range(128)])
        work=words(memory[23],32)[0]
        writes={(WRITE,MMIO,2):tuple((OBJECT+552+i*4,rng.getrandbits(32),4) for i in range(258)),
                (WRITE,MMIO,5):tuple((work+i*4,rng.getrandbits(32),4) for i in range(256))}
        for wet,dry in ((0x3F800000,0),(0x3F000000,0x3F000000),(0x40800000,0),(0x40800000,0)):
            memory=compare(memory,'process',OBJECT,128,wet,dry,trace={'writes':writes})['memory'];check.carried+=1
        if count==129:
            for timeout in (1,2):
                failed=compare(memory,'process',OBJECT,128,0x3F800000,0,
                    trace={'timeout_launch':timeout,'writes':writes})['memory']
                compare(failed,'process',OBJECT,128,0x3F800000,0);check.carried+=1
        print(f'Synthetic accelerator controls and actual software fallback agree for {count} coefficients.',flush=True)

def api_checks(check):
    invalid=guards=0;f=check.functions
    memory=tuple(bytearray(x) if i!=2 else x for i,x in enumerate(check.constructed[1]))
    callback=CALL(lambda *args:128);io=IO(callback,None);empty_io=IO(CALL(),None)
    for operation in ('start','wait'):
        for invalid_runtime,invalid_io in ((True,False),(False,True),(False,'empty')):
            state=CState(memory);before=state.snapshot();args=() if operation=='wait' else (256,0,WORK,COPY)
            selected=None if invalid_io is True else ctypes.byref(empty_io if invalid_io else io)
            assert f[operation](None if invalid_runtime else ctypes.byref(state.processing),*args,selected)==-200
            assert state.snapshot()==before;invalid+=1
    cases=('runtime','view','object','object_short','token_alignment','token_overflow','audio','audio_short',
           'partitions_zero','partitions_large','current','half','exponent','permutation','hardware_io','hardware_callback')
    for condition in cases+tuple(f'pointer_{offset}' for offset in range(20,56,4)):
        state=CState(memory);view=state.view();selected=ctypes.byref(io)
        if condition=='object':view.object=P()
        elif condition=='object_short':view.object_capacity=3
        elif condition=='token_alignment':view.object_token+=1
        elif condition=='token_overflow':view.object_token=0xFFFFF000
        elif condition=='audio':view.audio=P()
        elif condition=='audio_short':view.audio_capacity=511
        elif condition=='partitions_zero':put(state.object,4,0)
        elif condition=='partitions_large':put(state.object,4,33)
        elif condition=='current':put(state.object,8,1)
        elif condition=='half':put(state.object,12,2)
        elif condition=='exponent':put(state.object,16,49)
        elif condition=='permutation':put(state.object,words(state.object,36)[0]-OBJECT,0xFFFFFFFF)
        elif condition.startswith('pointer_'):put(state.object,int(condition.split('_')[1]),0)
        elif condition in ('hardware_io','hardware_callback'):
            put(state.object,548,1);selected=None if condition=='hardware_io' else ctypes.byref(empty_io)
        before=state.snapshot()
        status=f['run'](None if condition=='runtime' else ctypes.byref(state.processing),
                       None if condition=='view' else ctypes.byref(view),128,0x3F800000,0,selected)
        assert status==-200,(condition,status);assert state.snapshot()==before;invalid+=1
    for offset,value in ((4,0),(20,0),(36,0)):
        state=CState(memory);put(state.object,548,1);cm=CTraceMemory(state);calls=[]
        def mutate(_opaque,operation,address,value_,offset=offset,value=value):
            calls.append((operation,address,value_))
            if operation==SYNC:cm.write(OBJECT+offset,value,4)
            return 128
        changed_callback=CALL(mutate);changed_io=IO(changed_callback,None);view=state.view()
        assert f['run'](ctypes.byref(state.processing),ctypes.byref(view),128,0x3F800000,0,ctypes.byref(changed_io))==-201
        assert state.snapshot()[29]==memory[29] and calls;guards+=1
    for operation in range(len(KERNELS)):
        state=CState(memory);cm=CMemory(state);put_permutation(state.object);put_permutation(state.copy)
        addresses=(WORK,COPY,WORK+4096,OBJECT);arguments=(0,0,0,0)
        capacities=(512,512,512,0)
        if operation==0:capacities=(512,512,512,1536)
        elif operation==1:capacities=(512,480,0,0)
        elif operation==2:capacities=(1024,512,0,0)
        elif operation==3:capacities=(1024,2064,1032,0);arguments=(2,1,0,0)
        elif operation==4:capacities=(2072,2072,2064,0);arguments=(2,1,0,0)
        elif operation==5:capacities=(2064,1536,1032,0);arguments=(1,0,0,0)
        elif operation==6:capacities=(1024,512,512,0)
        elif operation==9:capacities=(1024,512,0,0)
        elif operation==10:capacities=(1032,2064,0,0);arguments=(2,1,0,0)
        elif operation==11:capacities=(2064,0,0,0)
        elif operation==12:capacities=(512,512,0,0)
        arrays=[cm.resolve(address)[0] for address in addresses]
        def rejected(view,args,output,op=operation):
            nonlocal invalid
            before=state.snapshot();sentinel=output.value if output is not None else None
            assert f['kernel'](op,ctypes.byref(view) if view is not None else None,args,
                               ctypes.byref(output) if output is not None else None)==-200
            assert state.snapshot()==before and (output is None or output.value==sentinel);invalid+=1
        original=Buffers((P*4)(*arrays),(U*4)(*capacities));args=(U*4)(*arguments);out=U(0xACBD3412)
        if operation==0:
            rejected(None,args,out);rejected(original,None,out);rejected(original,args,None);rejected(original,args,out,13)
        for i,capacity in enumerate(capacities):
            if capacity:
                changed=Buffers((P*4)(*arrays),(U*4)(*capacities));changed.capacity[i]-=1;rejected(changed,args,out)
                if not(operation==7 and i==2):
                    changed=Buffers((P*4)(*arrays),(U*4)(*capacities));changed.data[i]=P();rejected(changed,args,out)
        bad=[]
        if operation==1:bad=[(2,0,0,0)]
        elif operation in (3,4,10):bad=[(0,0,0,0),(33,0,0,0),(2,2,0,0)]
        elif operation in (5,11):bad=[(64,0,0,0)]
        elif operation in (6,12):bad=[(31,0,0,0),(0xFFFFFFE0,0,0,0)]
        for values in bad:rejected(original,(U*4)(*values),out)
        if operation in (0,5):
            put(state.object if operation==0 else state.copy,1024,4);rejected(original,args,out)
    return invalid,guards

def verify(library,output,mini_image=None):
    if not __debug__:raise RuntimeError('run without Python optimization')
    sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(SOURCE_FILES)}
    check=Comparison(library);corpus(check);invalid,guards=api_checks(check)
    new={pc for lo,hi in REGIONS.values() for pc in check.program.code if lo<=pc<hi}
    assert not new-check.coverage,('unvisited runtime instructions',list(map(hex,sorted(new-check.coverage))))
    dependencies={name:INSTALLATION_REGIONS[name] for name in ('budget','convert','limit','effective','raw_length')}
    groups=((REGIONS,check.program.processing_regions),(CONSTRUCTION_REGIONS,check.program.convolution_regions),
        (REUSED,check.program.reused_regions),({'installation_'+name:bounds for name,bounds in dependencies.items()},
            {'installation_'+name:check.program.installation_regions[name] for name in dependencies}))
    joined={pc for regions,_ in groups for start,end in regions.values() for pc in check.program.code if start<=pc<end}
    assert check.coverage<=joined,'an executed transitive body is missing its explicit byte binding'
    mini_binding=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        app=unpack_app(raw)[2]['app.bin']
        for regions,originals in groups:
            for name,(start,end) in regions.items():assert region_bytes(app,start,end)==originals[name],name
        assert region_bytes(app,TAPS,TAPS+36)==check.program.taps
        assert region_bytes(app,DESCRIPTORS,INDICES+32)==check.program.accelerator_tables
        mini_binding={'image_sha256':digest,'byte_identical_function_regions':sum(len(regions) for regions,_ in groups),
                      'byte_identical_resampling_bytes':36,'byte_identical_accelerator_table_bytes':64}
    tables=check.program.accelerator_tables
    report={'schema':1,'project':'HyperRig','result':'pass',
        'scope':'Complete original integer IR runtime, software FFT/convolution and synthetic accelerator controls',
        'original_image_sha256':'2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059',
        'total_comparisons':sum(check.counts.values()),'comparisons':check.counts,
        'original_instruction_steps':check.steps,'carried_state_calls':check.carried,
        'mutating_mmio_cases':check.mutations,'timeout_cases':check.timeouts,'mmio_events':check.mmio_events,
        'invalid_api_checks':invalid,'api_guard_checks':guards,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&check.coverage),'unvisited_new':sorted(new-check.coverage),
            'joined_decoded':len(joined),'joined_visited':len(joined&check.coverage),'unvisited_joined':sorted(joined-check.coverage),
            'all_decoded':len(check.program.code),'all_visited':len(check.coverage)},
        'entries':{hex(pc):count for pc,count in sorted(check.entries.items())},
        'functions':{name:{'start':start,'end_exclusive':end,'bytes_sha256':hashlib.sha256(raws[name]).hexdigest(),
            'instructions':sum(start<=pc<end for pc in check.program.code)} for regions,raws in groups for name,(start,end) in regions.items()},
        'accelerator_tables':{'start':DESCRIPTORS,'end_exclusive':INDICES+32,'sha256':hashlib.sha256(tables).hexdigest(),
            'commands':list(struct.unpack('<8I',tables[:32])),'size_indices':list(struct.unpack('<8I',tables[32:]))},
        'resampling_coefficients':{'start':TAPS,'end_exclusive':TAPS+36,'sha256':hashlib.sha256(check.program.taps).hexdigest(),
                                  'signed_words':list(struct.unpack('<9i',check.program.taps))},
        'source_sha256':sources,'mini_v4_binding':mini_binding,'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),
        'external_services':['synthetic 32-bit register reads/writes at 0x01ee0400 and 0x01ee0404','synthetic csync boundary'],
        'compared':['semantic returns and API statuses','all 30 mapped state and storage regions',
            'all object bytes including reserved regions','ordered register operations and complete state at every boundary',
            'actual constructor output carried through software processing and failure recovery'],
        'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'limitations':['accelerator transform results are explicitly supplied synthetic data; hardware arithmetic and timing were not executed',
            'active objects require the coherent constructor layout, 1..32 partitions, canonical permutation and exactly 128 signed32 samples',
            'integer operations wrap as documented and saturation is symmetric around zero; physical ISA corner behavior is represented by the pinned semantic model',
            'object structural fields, tables, view and IO remain stable across callbacks; post-MMIO rejection is a domain guard, not arbitrary relocation support',
            'only synchronous data/global/descriptor mutations are supported; storage is distinct except the declared complete-span mixing aliases',
            'no asynchronous execution, USB/audio scheduling, DSP peripheral emulation or acoustic validation',
            'inherited construction, ownership and selection bodies are not all reached by this runtime corpus; no global completion percentage is claimed']}
    assert sources=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},'sources changed during verification'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('result','total_comparisons','comparisons','instruction_coverage')}))
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mini-image',type=Path);args=parser.parse_args()
    if args.output.exists():parser.error('choose a fresh output path')
    verify(args.library,args.output,args.mini_image)
