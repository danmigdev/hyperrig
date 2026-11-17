"""Compare capture wrapper/worker interleavings with original decoded instructions."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,random,re,sys
from pathlib import Path
from capture_async_machine import (CaptureAsyncProgram,CaptureAsyncMachine,REGIONS,REUSED,
    MAPPED,ROOT,STACK,WORKER_STACK,DSP,BANK,HISTORY,RESULT,CHECK,MMIO,TIMER,ENGINE,
    DESCRIPTOR,READ,WRITE,SYNC,CLI,STI,CALLBACK,image_offset,DotMachine)
from verify_audio_task import (SOURCES as AUDIO_SOURCES,Memory as AudioMemory,MAP,CALL,U32,
    Task,baseline,capture_fixture,put,word,RAM,STATE,CONTROL,RECORD,ARENA,STATIC,Script,DYNAMICS_SOURCE_FILES)

SOURCES=(*AUDIO_SOURCES,'capture_live','capture_async')
PLATFORM=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,U32,U32)
class IO(ctypes.Structure):_fields_=[('map',MAP),('platform',PLATFORM),('call',CALL),('opaque',ctypes.c_void_p)]
class Worker(ctypes.Structure):_fields_=[(name,U32) for name in ('phase','idle_count','iterations','control')]
INPUT,OUTPUT,WORKER_CONTROL=0x01C234A8,0x01C23D68,RECORD+8176


def fixture(layers=2,taps=6,hardware=0,split=1,head=3,seed=1):
    memory=capture_fixture(layers,taps);r=memory[0]
    for address,value,size in ((DSP+12,hardware,4),(DSP+52,0,4),(DSP+56,0,1),(DSP+60,0,1),
        (DSP+112,split,4),(DSP+79,head,1),(DSP+272,1,4),(DSP+8,0,4),(DSP+4,0,4),
        (0x01C340C0,0,4),(ENGINE,0,4),(ENGINE-4,0,4),(ENGINE-8,0,4),
        (DSP+68,0,4),(DSP+72,0,4),(0x01C3417C,0,4)):
        put(r,address-RAM,value,size)
    # Larger head histories are placed beyond every fixture layer allocation.
    head_frames=1<<(head-1).bit_length();head_token=ARENA+100000
    put(r,DSP+156-RAM,head_token);put(r,DSP+160-RAM,head_frames-1)
    rng=random.Random(seed)
    for i in range(128):put(r,INPUT-RAM+4*i,rng.randrange(-1<<26,1<<26))
    for i in range(3048//4):put(r,HISTORY-RAM+4*i,rng.randrange(-5000,5000))
    for offset in (56,60,64,68,72,76,80,84,136,140,160):put(r,0x01C340CC+offset-RAM,0)
    for address in (0x01C34170,0x01C34174,0x01C34178,0x01C3417C,0x01C34180,0x01C34184,0x01C34188,0x01C34190):put(r,address-RAM,0)
    put(memory[1],8176,1)
    return memory


class Memory(AudioMemory):
    def raw_read(self,address,size):return self.read(address,size)


def configure(lib):
    for name,count in (('run',2),('submit',7)):
        f=getattr(lib,'hyperrig_capture_async_'+name);f.argtypes=[U32]*count+[ctypes.POINTER(IO)];f.restype=ctypes.c_int
    lib.hyperrig_capture_async_wait.argtypes=[ctypes.POINTER(ctypes.c_int32),ctypes.POINTER(IO)];lib.hyperrig_capture_async_wait.restype=ctypes.c_int
    lib.hyperrig_capture_worker_resume.argtypes=[ctypes.POINTER(Worker),U32,U32,U32,ctypes.POINTER(IO)]
    lib.hyperrig_capture_worker_resume.restype=ctypes.c_int
    lib.hyperrig_capture_async_audio_resume.argtypes=[ctypes.POINTER(Task),U32,U32,ctypes.POINTER(IO)]
    lib.hyperrig_capture_async_audio_resume.restype=ctypes.c_int
    lib.hyperrig_dot_i16.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int,
        ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int];lib.hyperrig_dot_i16.restype=ctypes.c_int
    return lib


class Platform:
    def __init__(self,program,*,auto_worker=True,clock=1000,step=137,engine_delay=0,
                 engine_timeout=False,software_dot=True,mutations=(),stop_after=None,handshake_release=None):
        self.program=program;self.auto_worker=auto_worker;self.clock=clock;self.step=step
        self.engine_delay=engine_delay;self.engine_timeout=engine_timeout;self.software_dot=software_dot
        self.mutations=mutations;self.counts={};self.pending=False;self.engine_reads=0;self.status=0
        self.worker=None;self.in_worker=False;self.lib=None;self.io=None;self.state=None;self.errors=[]
        self.events=[];self.dot_machines=[];self.native_workers=[];self.dot_calls=0;self.stop_after=stop_after
        self.handshake_release=handshake_release;self.call_script=Script();self.calls=[]

    def record(self,item):
        if self.events and self.events[-1][0]==item:self.events[-1][1]+=1
        else:self.events.append([item,1])

    def event(self,operation,address,value,state):
        key=(operation,address);self.counts[key]=self.counts.get(key,0)+1
        # Repeated volatile polls compare their exact return/order/count. Full
        # mapped snapshots are additionally compared at every other boundary.
        digest=None if operation==READ and address in (DSP+8,DSP+4,MMIO) else hashlib.sha256(b''.join(state.snapshot())).hexdigest()
        for op,at,nth,destination,new,width in self.mutations:
            if (operation,address,self.counts[key])==(op,at,nth):state.write(destination,new,width)
        result=0
        if operation==READ:
            if address==TIMER:result=self.clock;self.clock=(self.clock+self.step)&0xFFFFFFFF
            elif address==MMIO:
                self.engine_reads+=1
                if not self.engine_timeout and self.engine_reads>self.engine_delay:
                    if self.pending and self.software_dot:self.complete_dot(state)
                    self.pending=False;self.status|=128
                result=self.status
            else:
                if address==DSP+4 and self.handshake_release is not None and self.counts[key]>=self.handshake_release:state.write(address,0,4)
                if address==DSP+8 and state.raw_read(address,4) and self.auto_worker and not self.in_worker:self.run_worker(state)
                if address==WORKER_CONTROL and self.stop_after is not None and self.counts[key]>=self.stop_after:state.write(address,0,4)
                result=state.raw_read(address,4)
        elif operation==WRITE and address==MMIO:
            self.status=value
            if value==329:self.pending=True;self.engine_reads=0;self.status=0
        self.record((operation,address,value,result,digest))
        return result

    def run_worker(self,state,budget=1,handshake=1):
        self.in_worker=True
        try:
            if self.lib:
                if self.worker is None:self.worker=Worker()
                result=self.lib.hyperrig_capture_worker_resume(ctypes.byref(self.worker),WORKER_CONTROL,budget,handshake,ctypes.byref(self.io))
                if result<0:raise AssertionError(('C worker guard',result))
            else:
                if self.worker is None:
                    self.worker=self.program.machine(state.snapshot(),self.call,self.event)
                    self.worker.memory=state.memory;self.worker.public_memory=state.public_memory
                    self.worker.worker_start(WORKER_CONTROL);self.native_workers.append(self.worker)
                result=self.worker.worker_resume(budget,handshake)
            return result
        finally:self.in_worker=False

    def worker_state(self):
        if self.worker is None:return None
        return tuple(getattr(self.worker,k) for k,_ in Worker._fields_) if self.lib else self.worker.worker_state()

    def call(self,target,args,state):
        self.calls.append((target,args,hashlib.sha256(b''.join(state.snapshot())).hexdigest()))
        return self.call_script(target,args,state)

    def complete_dot(self,state):
        packed=state.raw_read(DESCRIPTOR+16,4);taps=packed&4095;count=(packed>>12)&4095
        shift=(packed>>24);shift=shift-256 if shift&128 else shift
        stride=((state.raw_read(DESCRIPTOR+20,4)>>10)&1023)//4
        output=state.raw_read(DESCRIPTOR+12,4);source=state.raw_read(DESCRIPTOR+8,4);weights=state.raw_read(DESCRIPTOR+4,4)
        if self.lib:
            result=self.lib.hyperrig_dot_i16(state.mapping(output,count*4),1,state.mapping(source,((count-1)*stride+taps)*4),stride,
                state.mapping(weights,taps*2),taps,count,shift)
            if result:raise AssertionError(('software accelerator fixture',result))
        else:
            machine=self.program.machine(state.snapshot(),self.call,self.event)
            machine.memory=state.memory;machine.public_memory=state.public_memory
            machine.stack_top=0x30002000;machine.regs.update(sp=machine.stack_top,r0=output,r1=1,r2=source,r3=stride)
            for i,arg in enumerate((weights,taps,count,shift&0xFFFFFFFF)):DotMachine.write(machine,machine.stack_top+i*4,arg,4)
            machine.pc=REUSED['dot_i16'][0];machine.run_call();self.dot_machines.append(machine)
        self.dot_calls+=1


def c_environment(lib,program,memory,platform):
    state=Memory(program,memory);platform.state=state;platform.lib=lib
    def mapped(_o,p,n,_w):return state.mapping(p,n)
    def event(_o,operation,address,value):
        try:return platform.event(operation,address,value,state)
        except Exception as error:platform.errors.append(error);return 0
    def call(_o,target,args,count):
        try:return platform.call(target,tuple(args[i] for i in range(count)),state)
        except Exception as error:platform.errors.append(error);return 0
    io=IO(MAP(mapped),PLATFORM(event),CALL(call),None);platform.io=io
    return state,io


def invalid_checks(lib,program):
    count=0
    memory=fixture();p=Platform(program);state,io=c_environment(lib,program,memory,p)
    for operation,args in (('run',(INPUT,OUTPUT)),('submit',(RESULT,HISTORY,12,ARENA,9,64,14))):
        fn=getattr(lib,'hyperrig_capture_async_'+operation)
        for bad in (None,ctypes.byref(IO(MAP(),io.platform,io.call,None)),
                    ctypes.byref(IO(io.map,PLATFORM(),io.call,None)),ctypes.byref(IO(io.map,io.platform,CALL(),None))):
            assert fn(*args,bad)==-200;count+=1
    result=ctypes.c_int32(123)
    assert lib.hyperrig_capture_async_wait(None,ctypes.byref(io))==-200;count+=1
    assert lib.hyperrig_capture_async_wait(ctypes.byref(result),None)==-200;count+=1
    for args in ((INPUT+1,OUTPUT),(INPUT,OUTPUT+2)):
        assert lib.hyperrig_capture_async_run(*args,ctypes.byref(io))==-202;count+=1
    missing=IO(MAP(lambda *_:None),io.platform,io.call,None)
    assert lib.hyperrig_capture_async_run(INPUT,OUTPUT,ctypes.byref(missing))==-201;count+=1
    assert lib.hyperrig_capture_async_wait(ctypes.byref(result),ctypes.byref(missing))==-201;count+=1
    assert result.value==123
    padding=(ctypes.c_uint8*400)()
    unaligned=IO(MAP(lambda _o,a,n,_w:ctypes.addressof(padding)+1 if a==DSP+76 else state.mapping(a,n)),io.platform,io.call,None)
    assert lib.hyperrig_capture_async_run(INPUT,OUTPUT,ctypes.byref(unaligned))==-202;count+=1
    for bad_worker,budget,handshake,token in ((None,1,1,WORKER_CONTROL),(Worker(4,0,0,0),1,1,WORKER_CONTROL),
        (Worker(),0,1,WORKER_CONTROL),(Worker(),1,0,WORKER_CONTROL),(Worker(),1,1,WORKER_CONTROL+1),
        (Worker(1,0,0,WORKER_CONTROL+4),1,1,WORKER_CONTROL)):
        expected=-202 if token&3 else -200
        assert lib.hyperrig_capture_worker_resume(ctypes.byref(bad_worker) if bad_worker else None,token,budget,handshake,ctypes.byref(io))==expected
        count+=1
    assert state.snapshot()==tuple(memory)
    for address,value,size,worker in ((DSP+52,2,4,None),(DSP+79,0,1,Worker(1,0,0,WORKER_CONTROL)),
        (DSP+79,65,1,Worker(1,0,0,WORKER_CONTROL)),(0x01C340C0,1,4,Worker(1,1023,0,WORKER_CONTROL)),
        (DSP+36,1,4,Worker(1,0,0,WORKER_CONTROL))):
        memory=fixture(hardware=1);put(memory[0],address-RAM,value,size)
        if address==DSP+79:put(memory[0],DSP+8-RAM,252)
        if address==DSP+36:put(memory[0],DSP+16-RAM,1)
        p=Platform(program,auto_worker=False);state,io=c_environment(lib,program,memory,p)
        if worker:status=lib.hyperrig_capture_worker_resume(ctypes.byref(worker),WORKER_CONTROL,1,1,ctypes.byref(io))
        else:status=lib.hyperrig_capture_async_run(INPUT,OUTPUT,ctypes.byref(io))
        assert status==-202,(address,status);count+=1
    assert lib.hyperrig_capture_async_audio_resume(None,1,1,ctypes.byref(io))==-200;count+=1
    return {'invalid_api_mapping_or_domain':count}


def verify(library,output=None,mini_image=None,smoke=False):
    program=CaptureAsyncProgram();lib=configure(ctypes.CDLL(str(library.resolve())))
    coverage=set();steps=0;counts={};real={};digest=hashlib.sha256();dots=0;event_count=0
    def collect(native,platform):
        nonlocal steps,dots,event_count
        machines=[native,*platform.native_workers,*platform.dot_machines]
        for machine in machines:
            previous=getattr(machine,'collected_steps',0);steps+=machine.steps-previous;machine.collected_steps=machine.steps
            coverage.update(machine.visited);prior=getattr(machine,'collected_calls',0)
            for target,args in machine.real_calls[prior:]:real[target]=real.get(target,0)+1
            machine.collected_calls=len(machine.real_calls)
        dots+=platform.dot_calls-getattr(platform,'collected_dots',0);platform.collected_dots=platform.dot_calls
        event_count+=sum(n for _,n in platform.events)-getattr(platform,'collected_events',0)
        platform.collected_events=sum(n for _,n in platform.events)
    def check(name,native,state,np,cp):
        if cp.errors:raise cp.errors[0]
        assert state.snapshot()==native.snapshot(),(name,[(hex(base+i),a,b) for (base,n),x,y in zip(MAPPED,state.snapshot(),native.snapshot())
            for i,(a,b) in enumerate(zip(x,y)) if a!=b][:20])
        assert np.events==cp.events,(name,'events',len(np.events),len(cp.events),next(((i,x,y) for i,(x,y) in enumerate(zip(np.events,cp.events)) if x!=y),None))
        assert np.calls==cp.calls,(name,'calls',np.calls,cp.calls)
        assert np.worker_state()==cp.worker_state(),(name,'worker',np.worker_state(),cp.worker_state())
        collect(native,np);counts[name]=counts.get(name,0)+1
        digest.update(json.dumps((name,np.events,np.calls,np.worker_state())).encode());digest.update(b''.join(state.snapshot()))
    def compare(name,memory,operation='run',args=(INPUT,OUTPUT),iterations=1,**settings):
        np,cp=Platform(program,**settings),Platform(program,**settings)
        native=program.machine(memory,np.call,np.event);state,io=c_environment(lib,program,memory,cp)
        for _ in range(iterations):
            native.pc=(REGIONS|REUSED)[operation][0]
            for i,arg in enumerate(args):
                if i<4:native.regs[f'r{i}']=arg
                else:DotMachine.write(native,STACK+(i-4)*4,arg,4)
            native.run_call()
            if operation=='wait':
                result=ctypes.c_int32(123);status=lib.hyperrig_capture_async_wait(ctypes.byref(result),ctypes.byref(io))
                assert result.value==(native.value('r0') if native.value('r0')<0x80000000 else native.value('r0')-0x100000000)
            else:status=getattr(lib,'hyperrig_capture_async_'+operation)(*args,ctypes.byref(io))
            assert status==0,(name,status);check(name,native,state,np,cp)
        print('Compared async',name,flush=True)
        return native,state,np,cp
    def worker_case(name,memory,segments=((1,1),),**settings):
        np,cp=Platform(program,auto_worker=False,**settings),Platform(program,auto_worker=False,**settings)
        native=program.machine(memory,np.call,np.event);state,io=c_environment(lib,program,memory,cp)
        for budget,handshake in segments:
            expected=np.run_worker(native,budget,handshake);actual=cp.run_worker(state,budget,handshake)
            assert expected==actual,(name,'worker observation',expected,actual);check(name,native,state,np,cp)
        return native,state,np,cp
    def audio_case(name,memory,segments=((1,1),(1,1),(1,1)),**settings):
        np,cp=Platform(program,**settings),Platform(program,**settings)
        native=program.machine(memory,np.call,np.event);state,io=c_environment(lib,program,memory,cp);task=Task()
        for waits,frames in segments:
            expected=native.resume(waits,frames)
            actual=lib.hyperrig_capture_async_audio_resume(ctypes.byref(task),waits,frames,ctypes.byref(io))
            assert actual==expected['reason'],(name,actual,expected['reason'])
            assert tuple(getattr(task,k) for k,_ in Task._fields_)==expected['task'],name
            check(name,native,state,np,cp)
        assert any(target==REGIONS['run'][0] for target,args in native.real_calls),name
    compare('bypass',baseline())
    compare('software-pipeline',fixture(),iterations=3)
    compare('accelerator-software-fixture',fixture(hardware=1),iterations=3)
    if not smoke:
        for layers in (1,2,3):
            for split in range(layers+1):
                for hardware in (0,1):compare(f'split-{layers}-{split}-{hardware}',fixture(layers=layers,split=split,hardware=hardware),iterations=2)
        for taps in (1,6,15):
            for head in (1,3,15,64):compare(f'kernels-{taps}-{head}',fixture(taps=taps,hardware=1,head=head),iterations=2)
        for bias in (0,1,0x7FFFFFFF,0xFFFFFFFF80000000,0x100000000,0xFFFFFFFF00000000,0x7FFFFFFFFFFFFFFF,0x8000000000000000):
            memory=fixture(hardware=1);put(memory[0],DSP+148-RAM,bias&0xFFFFFFFF);put(memory[0],DSP+152-RAM,bias>>32)
            put(memory[0],DSP+60-RAM,1,1);put(memory[0],DSP+72-RAM,2);put(memory[0],0x01C3417C-RAM,3)
            for i in range(64):put(memory[0],RESULT-RAM+i*4,(0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF)[i%5])
            compare(f'bias-{bias:x}',memory,iterations=2)
        for offset,value in ((84,0),(168,0)):
            memory=fixture();put(memory[0],DSP+offset-RAM,value,2 if offset==84 else 4);compare(f'bypass-{offset}',memory)
        for offset in (68,76):
            memory=fixture();put(memory[3],offset,0);compare(f'bypass-descriptor-{offset}',memory)
        for command in (0,255,0x123401FE,252,508,251):
            memory=fixture(hardware=command&1);put(memory[0],DSP+8-RAM,command)
            worker_case(f'worker-command-{command}',memory,((1,1),(1,1)))
        memory=fixture();put(memory[0],DSP+8-RAM,251);put(memory[0],DSP+4-RAM,1)
        worker_case('worker-handshake',memory,((1,1),(1,2),(1,2)),handshake_release=4)
        for stop in (1,2,3):worker_case(f'worker-stop-{stop}',fixture(),((1,1),(2,1),(1,1)),stop_after=stop)
        for cancel in (False,True):
            memory=fixture();put(memory[0],DSP+36-RAM,CALLBACK);put(memory[0],DSP+40-RAM,123);put(memory[0],DSP+44-RAM,0xFFFFFF00)
            worker_case(f'worker-job-{cancel}',memory,((1,1),(1,1)),mutations=((READ,DSP+8,2,DSP+16,7,4),(READ,DSP+8,2,DSP+32,7 if cancel else 0,4)))
        memory=fixture();put(memory[0],0x01C340C0-RAM,CALLBACK)
        worker_case('worker-watchdog',memory,((1024,1),))
        for busy in (0,1):
            memory=fixture();put(memory[0],ENGINE-RAM,busy)
            compare(f'wait-{busy}',memory,'wait',(),engine_delay=3)
        memory=fixture();put(memory[0],ENGINE-RAM,1);put(memory[0],ENGINE-4-RAM,0xFFFFFFFF)
        compare('wait-timeout',memory,'wait',(),engine_timeout=True)
        for args in ((RESULT,HISTORY,12,ARENA,9,64,14),(0xFFFFFFFF,0,0xFFFFFFFF,1,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF)):
            compare('submit-packed',fixture(),'submit',args,software_dot=False)
        memory=fixture();put(memory[0],ENGINE-RAM,1)
        compare('submit-drains-timeout',memory,'submit',(RESULT,HISTORY,12,ARENA,9,64,14),engine_timeout=True,software_dot=False)
        for hardware in (0,1):
            memory=fixture(hardware=hardware);put(memory[0],0x01C340CC+84-RAM,0xFFFFFFFF)
            compare(f'callback-mode-switch-{hardware}',memory,iterations=2,clock=0xFFFFFF00,
                mutations=((READ,TIMER,3,DSP+12,hardware^1,4),(READ,TIMER,6,DSP+68,1,4),(READ,TIMER,6,DSP+272,0,4)))
        memory=fixture(hardware=1);put(memory[0],DSP+60-RAM,1,1);put(memory[0],ENGINE-RAM,1)
        compare('callback-bias-after-wait',memory,mutations=((READ,MMIO,1,DSP+148,0x80000000,4),(READ,MMIO,1,DSP+152,0xFFFFFFFF,4)))
        memory=fixture(hardware=1);put(memory[0],DSP+60-RAM,1,1);put(memory[0],ENGINE-RAM,1)
        compare('wrapper-accelerator-timeout',memory,engine_timeout=True,software_dot=False)
        memory=fixture(hardware=1);put(memory[0],0x01C3417C-RAM,2)
        compare('head-diagnostic-cold-start',memory,iterations=2)
        for hardware in (0,1):
            memory=fixture(hardware=hardware)
            put(memory[0],STATE+380-RAM,3)
            for address in (CONTROL+2,CONTROL+3,STATE+28):put(memory[0],address-RAM,1,1)
            audio_case(f'audio-task-capture-{hardware}',memory)
        memory=fixture();put(memory[0],DSP+8-RAM,252);put(memory[0],DSP+68-RAM,1);put(memory[0],DSP+272-RAM,0)
        compare('full-worker-timeout-fallback',memory,auto_worker=False)
    print('New coverage',len(coverage&{pc for pc in program.code if any(a<=pc<b for a,b in REGIONS.values())}),flush=True)
    report=make_report(program,library,coverage,counts,steps,real,dots,event_count,digest.hexdigest(),mini_image)
    report['c_only_guards']=invalid_checks(lib,program)
    if not smoke:assert not report['instruction_coverage']['unvisited_new'],[hex(pc) for pc in report['instruction_coverage']['unvisited_new']]
    if output:
        if output.exists():raise ValueError('preserve earlier reports')
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('total_comparisons','native_steps')}|
        {k:v for k,v in report['instruction_coverage'].items() if not k.startswith('unvisited')}|
        {'unvisited_new':[hex(pc) for pc in report['instruction_coverage']['unvisited_new']]}))
    return report


def make_report(program,library,coverage,counts,steps,real,dots,events,digest,mini_image):
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    original_sha=hashlib.sha256(original).hexdigest()
    assert original_sha=='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    paths={f'firmware/{part}/hyperrig_{name}.{ext}' for name in SOURCES for part,ext in (('src','c'),('include/hyperrig','h'))}
    # Several inherited ISA helpers execute source in an isolated namespace;
    # those files are absent from sys.modules. Keep their explicit declarations
    # and the instruction TOML binding independent of earlier build reports.
    paths.update(DYNAMICS_SOURCE_FILES)
    paths.update(('tools/build_capture_async.py','tests/test_capture_async_machine.py','tests/capture_async_sanitize.c',
        'research/input-manifest.json','third_party/ultrarig/LICENSE.md'))
    pending=[ROOT/path for path in paths if path.endswith(('.c','.h'))];seen=set()
    while pending:
        source=pending.pop()
        if source in seen:continue
        seen.add(source)
        for include in re.findall(r'#include\s+"([^"]+)"',source.read_text()):
            path=(ROOT/'firmware/include'/include if include.startswith('hyperrig/') else source.parent/include).resolve()
            if not path.is_relative_to(ROOT):raise ValueError('include escaped repository')
            paths.add(path.relative_to(ROOT).as_posix());pending.append(path)
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
    from dsp_audio_path_machine import TABLE,PRIOR_TABLE,RESET_CONFIGURATION
    bounds=dict(STATIC)|{'capture_dispatch':(0x01C12BF2,0x01C12BF6),'gain_table':TABLE,
        'coefficient_table':(PRIOR_TABLE,PRIOR_TABLE+10),'reset_configuration':RESET_CONFIGURATION,
        'task_registration':(0x02005250,0x0200525E),'watchdog_writer':(0x02005268,0x02005276)}
    records=lambda spans:{name:{'start':lo,'end_exclusive':hi,'sha256':hashlib.sha256(app[image_offset(lo):image_offset(hi)]).hexdigest()} for name,(lo,hi) in spans.items()}
    windows=records({f'0x{pc:08x}':(pc,pc+record[1]) for pc,record in sorted(program.code.items())});static=records(bounds)
    mini=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert sha=='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        data=unpack_app(raw)[2]['app.bin']
        for record in (*windows.values(),*static.values()):
            lo,hi=record['start'],record['end_exclusive'];assert data[image_offset(lo):image_offset(hi)]==app[image_offset(lo):image_offset(hi)]
        mini={'image_sha256':sha,'identical_decoded_instruction_windows':len(windows),'identical_static_windows':list(static)}
    new={pc for pc in program.code if any(lo<=pc<hi for lo,hi in REGIONS.values())}
    from capture_processing_machine import KERNELS
    from biquad_machine import BiquadProgram
    numerical={start for start,end in (KERNELS|BiquadProgram.REGIONS).values()}|{0x01C19D36,0x01C1A636}
    functions=records(REGIONS)
    for name,(lo,hi) in REGIONS.items():functions[name].update(decoded=sum(lo<=pc<hi for pc in new),visited=sum(lo<=pc<hi for pc in coverage))
    return {'schema':1,'project':'HyperRig','result':'pass','component':'reconstructed-capture-async',
        'original_image_sha256':original_sha,'decoded_image_sha256':hashlib.sha256(app).hexdigest(),'functions':functions,'reused_functions':records(REUSED),
        'bound_instruction_windows':windows,'bound_static_data':static,'mini_v4_binding':mini,
        'total_comparisons':sum(counts.values()),'comparisons':counts,'native_steps':steps,
        'real_callee_entries':{hex(k):v for k,v in sorted(real.items())},'software_dot_completions':dots,'platform_events':events,
        'actual_numerical_kernel_entries':sum(v for k,v in real.items() if k in numerical),
        'scripted_recovered_kernel_replacements':0,
        'remaining_sample_services':[hex(x) for x in (0x01C012D8,0x01C0158A,0x01C01690,0x01C01722,0x01C0174E,
            0x01C0179E,0x01C01800,0x01C0198A,0x01C019D8,0x01C01DE4,0x01C10E06,0x01C11D06,0x01C19EFA)],
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&coverage),'unvisited_new':sorted(new-coverage),
            'all_decoded':len(program.code),'all_visited':len(coverage),'unvisited_all':sorted(set(program.code)-coverage),
            'missing_classification':{},'inherited_gap_scope':'Inherited instructions outside the required caller/numerical cases remain unvisited; earlier report coverage is not added.'},
        'source_sha256':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sorted(paths)},
        'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'comparison_digest_sha256':digest,
        'hardware_test':False,'audio_test':False,'flashable':False,'firmware_changed':False,
        'limitations':['Controlled scheduling and MMIO are synthetic platform fixtures, not hardware execution.',
            'Software accelerator completion executes the recovered dot body; accelerator equivalence is not established.',
            'Worker observation statuses are new; only its stop flag produces an original return.',
            'Indirect worker callbacks are restricted to watchdog 0x01c02dbc; its body remains external.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path);parser.add_argument('--mini-image',type=Path);parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args();verify(args.library,args.output,args.mini_image,args.smoke)
if __name__=='__main__':main()
