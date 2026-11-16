"""Compare IR installation C against decoded original instructions offline."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib
from ir_installation_machine import (IrInstallationProgram, REGIONS, MATH_REGIONS, ROOT,
    HEAP, CAPACITY, DSP, GAIN, EXTRA, ARITIES, region_bytes)
from ir_loader_machine import (REGIONS as LOADER_REGIONS, SERVICES, ALLOCATE, FREE, LOCK, UNLOCK,
    INSTALL, INSTALL_SLOT, OWNS, REFRESH, NOTIFY, PRIORITY, POLL, READ, ACTIVITY, STATE, GLOBAL)
from verify_ir_loader import (baseline as previous_baseline, CState as PreviousState,
    CMemory as PreviousMemory, Runtime as LoaderRuntime, IO as LoaderIO, SERVICE,
    READ_CALLBACK, Reads, Script, record, load_reads)

class Runtime(ctypes.Structure):
    _fields_ = [('loader', LoaderRuntime), ('dsp', ctypes.c_uint8 * 24), ('gain', ctypes.c_uint8 * 4)]
class IO(ctypes.Structure):
    _fields_ = [('services', LoaderIO), ('token', ctypes.c_uint32)]

def baseline(samples=()):
    memory = previous_baseline() + (bytearray([0xC3]*24), bytearray([0xD4]*4))
    if samples: memory[16][:2*len(samples)] = struct.pack('<'+'h'*len(samples), *samples)
    struct.pack_into('<IIIIII', memory[17], 0, 0, len(samples), 0, 0, 0, len(samples))
    return memory

def read_script(payload, tag=0x4A474B54, identity=None):
    head = record(payload, tag, crc=identity)
    return [(0,head,())]*(2 if tag == 0x49474B54 else 1) + [(0,payload[i:i+2048],()) for i in range(0,len(payload),2048)]

class CState(PreviousState):
    def __init__(self, memory):
        super().__init__(memory[:17])
        self.installation = Runtime(self.ir, (ctypes.c_uint8*24).from_buffer_copy(memory[17]),
                                    (ctypes.c_uint8*4).from_buffer_copy(memory[18]))
        self.ir = self.installation.loader
        self.storage = self.ir.storage
    def snapshot(self):
        return super().snapshot() + (bytes(self.installation.dsp), bytes(self.installation.gain))
class CMemory(PreviousMemory):
    def __init__(self, state):
        super().__init__(state)
        for (base,_), data in zip(EXTRA, (state.installation.dsp,state.installation.gain)):
            self.extra.update({base+i:(data,i) for i in range(len(data))})

def configure(library):
    u32, rt, io = ctypes.c_uint32, ctypes.POINTER(Runtime), ctypes.POINTER(IO)
    out, pointer = ctypes.POINTER(u32), ctypes.POINTER(ctypes.c_uint8)
    signatures = {'budget':[u32], 'convert':[u32]*3, 'limit':[u32]*5, 'gain':[u32],
        'trim':[pointer,u32,u32,out], 'length':[rt,u32,u32,u32,out],
        'configure':[rt,u32,u32,u32,u32,io], 'slot':[rt,u32,u32], 'read':[rt,u32,u32,u32,io],
        'attach':[rt,u32,u32,u32,u32,io], 'refresh':[rt,io], 'load':[rt,u32,u32,io]}
    functions = {}
    for name, args in signatures.items():
        f = getattr(library,'hyperrig_ir_installation_'+name)
        f.argtypes, f.restype = args, u32 if name in ('budget','convert','limit','gain') else ctypes.c_int
        functions[name] = f
    return functions

def verify(library_path, output, mini_image=None):
    if not __debug__: raise RuntimeError('run without Python optimization')
    program, functions = IrInstallationProgram(), configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, external = dict.fromkeys(ARITIES,0), set(), set()
    rng, mutations, carried, sample_checks = random.Random(0x2957E1AD), 0, 0, 0
    def compare(memory, operation, *args, reads=(), plan=None, sequence=False, stack_byte=0xA7):
        nonlocal mutations, carried, sample_checks
        nr, cr, ns, cs = Reads(reads), Reads(reads), Script(plan), Script(plan)
        native = program.execute(memory,operation,*args,reader=nr.read,boundary=ns,stack_byte=stack_byte)
        state, calls, errors = CState(memory), [], []
        def service(_o,svc,a,b,c,d):
            try:
                calls.append((svc,(a,b,c,d),state.snapshot()))
                return cs(svc,(a,b,c,d),CMemory(state))
            except Exception as error: errors.append(error); return 0
        def read(_o,address,destination,size):
            try:
                label,offset = state.target(destination,size)
                calls.append((READ,(address,label,offset,size),state.snapshot()))
                status,data = cr.read(address,size,CMemory(state))
                if data: ctypes.memmove(destination,data,len(data))
                return status
            except Exception as error: errors.append(error); return 1
        sc,rc = SERVICE(service),READ_CALLBACK(read)
        io = IO(LoaderIO(sc,rc,None,state.allocation,CAPACITY),HEAP)
        rt,out = ctypes.byref(state.installation),ctypes.c_uint32(0xAABBCCDD)
        if operation in ('budget','convert','limit'):
            actual = functions[operation](*args)
        elif operation == 'trim':
            assert functions['trim'](state.allocation if args[0] else None,args[1],CAPACITY,ctypes.byref(out)) == 0
            actual = out.value
            sample_checks += args[1] if args[0] else 0
        elif operation in ('effective','raw_length'):
            assert functions['length'](rt,*args,operation=='effective',ctypes.byref(out)) == 0
            actual = out.value
        elif operation == 'slot': actual = functions[operation](rt,*args)
        else:
            actual = functions[operation](rt,*args,ctypes.byref(io))
            if operation in ('configure','attach','refresh'):
                assert actual == 0
                actual = native['result'] # Original void result register is incidental.
        if errors: raise errors[0]
        if ((actual & 0xFFFFFFFF) != native['result'] or state.snapshot() != native['memory']
                or calls != native['calls'] or cr.requests != nr.requests):
            diffs=[(i,next((j for j,(a,b) in enumerate(zip(x,y)) if a!=b),None))
                   for i,(x,y) in enumerate(zip(state.snapshot(),native['memory'])) if i!=2 and x!=y]
            mismatch=next((i for i,(a,b) in enumerate(zip(calls,native['calls'])) if a!=b),None)
            raise AssertionError((operation,args,actual,native['result'],diffs,'calls',mismatch,
                calls[mismatch][:2] if mismatch is not None else len(calls),
                native['calls'][mismatch][:2] if mismatch is not None else len(native['calls'])))
        assert len(cr.requests) == len(reads), 'unused read fixture'
        assert not ({INSTALL,INSTALL_SLOT} & {row[0] for row in calls}), 'numerical install escaped as a service'
        counts[operation]+=1;coverage.update(native['visited']);external.update(row[0] for row in calls)
        mutations += bool(plan and any(writes for _,writes in plan.values())) or any(row[2] for row in reads)
        carried += sequence
        return native

    for count in (0,1,2,3,33,129,511,1024,4076):
        for kind in range(6):
            samples = ([0]*count if kind==0 else [32767]+[0]*(count-1) if kind==1 and count else
                       [-32768]*count if kind==2 else [1]*count if kind==3 else
                       [32767 if i%2 else -32768 for i in range(count)] if kind==4 else
                       [rng.randint(-32768,32767) if i<count//2 else 0 for i in range(count)])
            compare(baseline(samples),'trim',HEAP,count)
    for samples in ([32767,10],[32767,11],[31620,10],[31619,10],[1024,1],[1023,1],[32767]+[1]*1100):
        compare(baseline(samples),'trim',HEAP,len(samples))
    for _ in range(64):
        samples=[rng.randint(-32768,32767) for _ in range(rng.randrange(512))]
        compare(baseline(samples),'trim',HEAP,len(samples))
    for count in (0,1,4076,0xFFFFFFFF): compare(baseline(),'trim',0,count)
    metadata = (-2147483648,-60001,-60000,-59999,-3000,-1,0,1,999,6000,19999,20000,20001,2147483647)
    for gain in metadata:
        for direct in (0,HEAP):
            for fmt in (0,1,255):
                compare(baseline([32767]+[0]*63),'configure',direct,64,gain&0xFFFFFFFF,fmt)
    for count in (0,1,0xFFFFFFFF): compare(baseline(),'configure',0,count,0,0)
    compare(baseline(),'configure',HEAP,0,0,1)
    edges=(0,1,2,63,64,127,128,255,4095,4096,4076,0x5555555,0x7FFFFFFF,0x80000000,0xFFFFFFFF)
    for value in (*range(100),*edges,*(rng.getrandbits(32) for _ in range(64))):
        compare(baseline(),'budget',value)
    for value in edges:
        for source in (0,1,0xFFFFFFFF):
            for destination in (0,1,0xFFFFFFFF): compare(baseline(),'convert',value,source,destination)
    for count in edges:
        for fmt in (0,1):
            for mode in (0,1):
                for tail in (0,1,count):
                    compare(baseline(),'limit',count,tail,fmt,mode,21)
    for _ in range(180):
        compare(baseline(),'limit',*(rng.getrandbits(32) for _ in range(5)))
    for mode in (0,1,255):
        for budget in (0,1,21,0xFFFFFFFF):
            for fmt in (0,1,255):
                memory=baseline();struct.pack_into('<I',memory[17],4,4076);struct.pack_into('<I',memory[17],8,fmt)
                struct.pack_into('<I',memory[17],20,129)
                for operation in ('effective','raw_length'): compare(memory,operation,mode,budget)
    for callback in (0,0x0201AD4C,0xFFFFFFFF):
        for count in (0,1,4076):
            for slot in (0,1,8,9,0xFFFFFFFF):
                memory=baseline();struct.pack_into('<I',memory[15],0,callback);struct.pack_into('<I',memory[17],4,count)
                compare(memory,'slot',slot,0x87654321)
    print('IR numerical preparation and state setters agree with original instructions.',flush=True)

    for size in (0,2,254,256,258,2046,2048,2050,4096,8152):
        payload=bytes(rng.randrange(256) for _ in range(size))
        for tag in (0x4A474B54,0x49474B54):
            compare(baseline(),'read',8,zlib.crc32(payload),size//2,reads=read_script(payload,tag))
        if size:
            script=read_script(payload,identity=0x12345678)
            compare(baseline(),'read',1,0x12345678,size//2,reads=script)
            for failed in range(1,len(script)):
                reads=script[:failed]+[(1,script[failed][1][:1],())]
                compare(baseline(),'read',2,0x12345678,size//2,reads=reads)
    for slot in (0,9,0xFFFFFFFF): compare(baseline(),'read',slot,0,0)
    for seed in (0,0xA7,255):
        for prefix in (0,4,7,8,40):
            compare(baseline(),'read',1,0,0,reads=[(1,record()[:prefix],())]*2,stack_byte=seed)
    for header in (record(b'1234',crc=55),record(b'12',crc=0),record(bytes(8154)),record(b'12',tag=0)):
        script=[(0,header,())]*(1 if struct.unpack_from('<II',header)[0]==0x4A474B54 and len(header)==40 and struct.unpack_from('<I',header,4)[0]<=8152 else 2)
        compare(baseline(),'read',1,0,2,reads=script)
    payload=bytes(range(256))*12
    for service,address in ((PRIORITY,GAIN),(POLL,HEAP),(POLL,HEAP+512),(POLL,DSP+64)):
        compare(baseline(),'read',3,zlib.crc32(payload),len(payload)//2,reads=read_script(payload),
                plan={(service,1):(0,((address,0x12345678,4),))})
    for index in (0,1,2):
        script=read_script(payload)
        status,data,_=script[index];script[index]=(status,data,((DSP+72,7,4),))
        compare(baseline(),'read',2,zlib.crc32(payload),len(payload)//2,reads=script)

    for previous in (0,HEAP,0x12340000):
        for direct in (0,HEAP):
            memory=baseline([32767,0,0]);struct.pack_into('<I',memory[1],164,previous)
            compare(memory,'attach',direct,3,0,1)
    for service in (LOCK,UNLOCK,FREE):
        memory=baseline([32767,0,0]);struct.pack_into('<I',memory[1],164,0x12340000)
        compare(memory,'attach',HEAP,3,0,1,plan={(service,1):(0,((GAIN,0x40000000,4),(HEAP+4,32767,2)))})
    for slot in (0,7,255):
        for present in (0,1):
            for count in (0,3):
                memory=baseline([32767,0,0]);memory[0][10]=slot;memory[1][160]=present
                struct.pack_into('<I',memory[17],4,count);struct.pack_into('<I',memory[1],164,HEAP)
                compare(memory,'refresh')
    for size in (0,2,3,256,2050,8152):
        payload=bytes(rng.randrange(256) for _ in range(size))
        for tag in (0x4A474B54,0x49474B54):
            for refresh in (0,1):
                compare(baseline(),'load',2,refresh,reads=load_reads(payload,tag,-3000&0xFFFFFFFF))
    for svc in (PRIORITY,ACTIVITY,ALLOCATE,NOTIFY,LOCK,UNLOCK,OWNS,REFRESH,FREE):
        compare(baseline(),'load',2,1,reads=load_reads(),plan={(svc,1):(HEAP if svc==ALLOCATE else 0,
            ((DSP+64,128,4),(STATE+744,0x87654321,4),(GAIN,0x40000000,4)))})
    compare(baseline(),'load',0,0,reads=[(0,record(),())],plan={ALLOCATE:(0,())})
    for error in ('header','read','crc'):
        script=load_reads()
        if error=='header': script=script[:1]+[(1,b'',())]
        elif error=='read': script[-1]=(1,b'\0',())
        else: script[-1]=(0,bytes(4),())
        compare(baseline(),'load',0,0,reads=script)
    payload=struct.pack('<hhhh',32767,0,0,0)
    memory=compare(baseline(),'load',3,0,reads=load_reads(payload))['memory']
    memory=compare(memory,'effective',1,0,sequence=True)['memory']
    memory=compare(memory,'refresh',sequence=True)['memory']
    memory=compare(memory,'read',4,zlib.crc32(payload),4,reads=read_script(payload),sequence=True)['memory']
    compare(memory,'configure',HEAP,4,(-6000)&0xFFFFFFFF,1,sequence=True)
    print('IR reads, ownership composition and carried load/defer/read sequence agree.',flush=True)

    state, seen = CState(baseline()), []
    sc=SERVICE(lambda *args: seen.append(args) or 0); rc=READ_CALLBACK(lambda *args: seen.append(args) or 0)
    io=IO(LoaderIO(sc,rc,None,state.allocation,CAPACITY),HEAP)
    rt,out=ctypes.byref(state.installation),ctypes.c_uint32(99)
    invalid=[('trim',(state.allocation,4077,CAPACITY,ctypes.byref(out))),
        ('trim',(state.allocation,2,3,ctypes.byref(out))),('trim',(None,0,0,None)),
        ('length',(None,0,0,0,ctypes.byref(out))),('length',(rt,0,0,0,None)),
        ('configure',(None,0,0,0,0,None)),('configure',(rt,HEAP,1,0,0,None)),
        ('configure',(rt,HEAP+2,1,0,0,ctypes.byref(io))),('configure',(rt,HEAP,4077,0,0,ctypes.byref(io))),
        ('slot',(None,0,0)),('read',(None,1,0,0,ctypes.byref(io))),('read',(rt,1,0,0,None)),
        ('read',(rt,1,0,4077,ctypes.byref(io))),('attach',(None,0,0,0,0,ctypes.byref(io))),
        ('attach',(rt,HEAP,1,0,0,None)),('refresh',(None,ctypes.byref(io))),('refresh',(rt,None)),
        ('load',(None,0,0,ctypes.byref(io))),('load',(rt,0,0,None))]
    for op,args in invalid:
        before=state.snapshot()
        assert functions[op](*args)==-200 and state.snapshot()==before and not seen and out.value==99
    for bad in (IO(LoaderIO(SERVICE(),rc,None,state.allocation,CAPACITY),HEAP),
                IO(LoaderIO(sc,READ_CALLBACK(),None,state.allocation,CAPACITY),HEAP),
                IO(LoaderIO(sc,rc,None,None,CAPACITY),HEAP),
                IO(LoaderIO(sc,rc,None,state.allocation,CAPACITY-1),HEAP)):
        before=state.snapshot()
        assert functions['read'](rt,1,0,4076,ctypes.byref(bad))==-200 and not seen and state.snapshot()==before
    # Guard checks are API policy, excluded from original-instruction equivalence.
    guard_checks=0
    for bad_token,growth in ((True,False),(False,True)):
        state=CState(baseline()); services=[]; data=iter((record(b'12'),record(b'1234')))
        def guarded_call(_o,svc,a,b,c,d):
            services.append(svc)
            return (HEAP+4 if bad_token else HEAP) if svc==ALLOCATE else 0
        def guarded_read(_o,addr,dest,size):
            assert size==40;ctypes.memmove(dest,next(data),40);return 0
        gc,gr=SERVICE(guarded_call),READ_CALLBACK(guarded_read)
        gi=IO(LoaderIO(gc,gr,None,state.allocation,CAPACITY),HEAP)
        assert functions['load'](ctypes.byref(state.installation),0,0,ctypes.byref(gi))==-201
        assert state.snapshot()[17:]==baseline()[17:] and INSTALL not in services
        guard_checks+=1

    new={pc for start,end in REGIONS.values() for pc in program.code if start<=pc<end}
    added=set(program.code)-program.pre_installation_code
    missing=sorted(new-coverage)
    assert not missing,[hex(pc) for pc in missing]
    mini_binding=None
    groups=((REGIONS,program.installation_regions),(MATH_REGIONS,program.math_regions),(LOADER_REGIONS,program.ir_regions))
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        app=unpack_app(raw)[2]['app.bin']
        for regions,originals in groups:
            for name,(start,end) in regions.items(): assert region_bytes(app,start,end)==originals[name],name
        mini_binding={'image_sha256':digest,'byte_identical_regions':sum(len(x[0]) for x in groups)}
    prior=json.loads((ROOT/'build/reverse-ir-loader-02/verification.json').read_text())
    math=json.loads((ROOT/'build/reverse-biquad-generator-01/verification.json').read_text())
    sources=set(prior['source_sha256'])|set(math['sources_sha256'])
    sources.update(['firmware/src/hyperrig_ir_installation.c','firmware/include/hyperrig/hyperrig_ir_installation.h',
        'tools/ir_installation_machine.py','tools/verify_ir_installation.py','tools/build_ir_installation.py',
        'tests/test_ir_installation_machine.py','tests/ir_installation_sanitize.c'])
    report={'schema':1,'project':'HyperRig','result':'pass','scope':'IR installation, numerical preparation, slot reads and ownership composition',
        'original_image_sha256':prior['original_image_sha256'],
        'functions':{name:{'start':start,'end_exclusive':end,'bytes_sha256':hashlib.sha256(raws[name]).hexdigest()}
                     for regions,raws in groups for name,(start,end) in regions.items()},
        'comparisons':counts,'total_comparisons':sum(counts.values()),'sample_inputs_checked':sample_checks,
        'mutating_service_cases':mutations,'carried_state_calls':carried,
        'invalid_api_checks':len(invalid)+4,'api_guard_checks':guard_checks,
        'instruction_coverage':{'new_visited':len(new&coverage),'new_decoded':len(new),
            'added_with_reused_math_visited':len(added&coverage),'added_with_reused_math_decoded':len(added),
            'all_visited':len(coverage),'all_decoded':len(program.code),'unvisited_new':missing},
        'external_services_visited':['read' if svc==READ else SERVICES[svc][0] for svc in sorted(external)],
        'compared':['semantic returns','all 19 mapped state/storage regions','ordered service/read arguments and state at every boundary'],
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(sources)},
        'mini_v4_binding':mini_binding,'library_sha256':hashlib.sha256(library_path.read_bytes()).hexdigest(),
        'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'limitations':['physical reads, allocation/free, locks, scheduler/activity/notification remain synthetic services',
            'effect ownership/refresh and convolution construction/kernel execution remain external',
            'one opaque backing allocation, at most 4076 signed16 samples; no concurrent reentry or overlapping runtime storage',
            'failed-header private frame initialized with arbitrary fixtures; unused original local length is not observable',
            'binary32 ISA behavior uses pinned independent semantics, without a new physical float/CPU measurement']}
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('result','total_comparisons','comparisons','instruction_coverage')}))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args()
    if args.output.exists(): parser.error('preserve completed reports; choose a new output path')
    verify(args.library,args.output,args.mini_image)
