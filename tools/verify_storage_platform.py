"""Compare complete platform bodies and explicit interrupt contexts offline."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from storage_platform_machine import (StoragePlatformProgram,REGIONS,REUSED,ARITIES,DIRECT_SITES,INDIRECT_SITES,
    MAPPED,MMIO,GLOBAL,COMMAND,ACK,ARGUMENT,LOCK_COUNTS,IRQ_COUNTS,MODE,STACK,ROOT,READ,WRITE,BARRIER,
    CLI,STI,CNUM,ICFG_READ,ICFG_WRITE,LOCKSET,LOCKCLR,PUSH,POP,RTI,INITIAL_MAILBOX,region_bytes)
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app
U32,U64=ctypes.c_uint32,ctypes.c_uint64
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
EVENT=ctypes.CFUNCTYPE(U64,ctypes.c_void_p,U32,U32,U32,U64,ctypes.POINTER(Borrowed))
class CPU(ctypes.Structure):_fields_=[('cnum',U32),('icfg',U32)]
class Context(ctypes.Structure):_fields_=[('registers',U32*16),('psr',U32),('rets',U32),('reti',U32)]
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('event',EVENT),('opaque',ctypes.c_void_p),('services',U32),('events',U32),('work',U32)]
SOURCES=tuple('firmware/src/hyperrig_'+s+'.c' for s in ('storage_platform','storage_coordination','controls','control_actions','selection','preset_storage','preset_preflight','preset_loader'))
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'

def setword(memory,a,v,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:data[a-base:a-base+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little');return
    raise ValueError(f'platform fixture write {a:#x}/{n}')
def getword(memory,a,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:return int.from_bytes(data[a-base:a-base+n],'little')
    raise ValueError(f'platform fixture read {a:#x}/{n}')
def initial(mode=0):
    m=[bytearray((i*17+j*13+5)&255 for i in range(n)) for j,(_,n) in enumerate(MAPPED)]
    for a in range(COMMAND,IRQ_COUNTS+16):setword(m,a,0,1)
    setword(m,MODE,mode,1);return m
def context(seed=0):return tuple((seed*0x04030201+i*0x1020304)&0xffffffff for i in range(16))+(seed&0xffffffff,0xf1234567^seed,0xe2345679^seed)
def ctx(words):return Context((U32*16)(*words[:16]),*words[16:])
def ctxwords(value):return tuple(value.registers)+(value.psr,value.rets,value.reti)

class Script:
    def __init__(self,returns=None,mutations=(),probes=(),auto_ack=True,clear_irq=True,event_return=0):
        self.returns=returns or {};self.mutations=mutations;self.probes=probes;self.auto_ack=auto_ack;self.clear_irq=clear_irq
        self.event_return=event_return;self.seen={};self.actions=[];self.sent=False
        self.registers={0x10704:0x12345678,0x01eee000:16,0x01eee004:16,0x01eee008:16384}
    def change(self,key,m):
        occurrence=self.seen.get(key,0);self.seen[key]=occurrence+1;ops=[]
        for at,which,a,v,n in self.mutations:
            if at==key and (which<0 or occurrence==which):m.write(a,v,n);ops.append((1,a,n,v))
        for at,which,a,n,w in self.probes:
            if at==key and (which<0 or occurrence==which):
                if m.public_probe(a,n,w):raise ValueError('expected borrowed-view rejection')
                ops.append((2,a,n,w))
        return occurrence,ops
    def value(self,key,index,default):
        value=self.returns.get(key,default)
        return value[min(index,len(value)-1)] if isinstance(value,(tuple,list)) else value
    def call(self,target,args,m):
        index,ops=self.change(('call',target),m);value=self.value(('call',target),index,0x76543210)&0xffffffff
        self.actions.append((0,target,1,0,value,args,ops));return value
    def event(self,op,a,n,v,m):
        key=(op,a);index=self.seen.get(key,0);ops=[]
        result=self.value(key,index,self.registers.get(a,0xa55aa55a) if op==READ else self.event_return)&((1<<64)-1)
        if op==WRITE:
            self.registers[a]=v&((1<<(n*8))-1)
            if a==0x01eef1a0:
                self.sent=True
                if self.auto_ack:m.write(ACK,1,1);ops.append((1,ACK,1,1))
        if op==BARRIER:
            if self.auto_ack and m.operation=='enter' and not self.sent and m.read(ACK,1)==1:
                m.write(ACK,0,1);ops.append((1,ACK,1,0))
            if self.clear_irq and m.operation=='interrupt' and m.read(ACK,1):
                m.write(ACK,0,1);ops.append((1,ACK,1,0))
        _,extra=self.change(key,m);ops.extend(extra)
        self.actions.append((op,a,n,v,result,(0,)*12,ops));return result

class Backend:
    def __init__(self,memory,cpu,script,name,alignment=0,services=10000,events=10000,work=4000000):
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory];self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment);array[:]=data;self.arrays.append(array)
        self.cpu=CPU(*cpu);self.operation=name;self.script=script;self.calls=[];self.events=[];self.timeline=[];self.errors=[];self.borrowed=None
        self.io=IO(MAP(self.map),CALL(self.call),EVENT(self.event),None,services,events,work)
    def map(self,opaque,a,n,writable):
        for (base,size),data in zip(MAPPED,self.arrays):
            if base<=a<=a+n<=base+size:return ctypes.addressof(data)+a-base
        return None
    def public_probe(self,a,n,writable=0):return bool(self.borrowed.map(self.borrowed.opaque,a,n,writable))
    def read(self,a,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,0) if self.borrowed else self.map(None,a,n,0)
        if p is None:raise ValueError('platform callback unavailable read')
        return int.from_bytes(ctypes.string_at(p,n),'little')
    def write(self,a,v,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,1) if self.borrowed else self.map(None,a,n,1)
        if p is None:raise ValueError('platform callback unavailable write')
        ctypes.memmove(p,(v&((1<<(8*n))-1)).to_bytes(n,'little'),n)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def cpu_words(self):return self.cpu.cnum,self.cpu.icfg
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())+struct.pack('<II',*self.cpu_words())).hexdigest()
    def call(self,opaque,target,args,count,borrowed):
        try:
            if count!=1:raise ValueError('platform indirect arity changed')
            words=tuple(args[i] for i in range(count))+(0,)*(12-count);before=self.digest();self.borrowed=borrowed.contents
            value=self.script.call(target,words,self);self.borrowed=None
            self.calls.append((target,words,before,self.digest(),value));self.timeline.append(('call',len(self.calls)-1));return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0
    def event(self,opaque,op,a,n,v,borrowed):
        try:
            before=self.digest();self.borrowed=borrowed.contents;value=self.script.event(op,a,n,v,self);self.borrowed=None
            self.events.append((op,a,n,v,value,before,self.digest()));self.timeline.append(('event',len(self.events)-1));return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library):
        self.program=StoragePlatformProgram();self.library=ctypes.CDLL(str(Path(library).resolve()))
        self.execute=self.library.hyperrig_storage_platform_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(CPU),ctypes.POINTER(IO)]
        self.interrupt=self.library.hyperrig_storage_platform_interrupt
        self.interrupt.argtypes=[ctypes.POINTER(Context),ctypes.POINTER(Context),ctypes.POINTER(CPU),ctypes.POINTER(IO)]
        self.visited=set();self.steps=0;self.records=[];self.counts={};self.digest=hashlib.sha256();self.indirect_sites=set()
    def compare(self,label,memory,name,args=(),cpu=(0,0x01090700),irq_context=None,alignment=0,services=10000,events=10000,**script_args):
        before_memory=tuple(map(bytes,memory));irq_context=context(15) if name=='interrupt' and irq_context is None else irq_context
        first=Script(**script_args)
        try:r=self.program.execute(memory,name,args,cpu,irq_context,first.call,first.event,services,events)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        second=Script(**script_args);b=Backend(memory,cpu,second,name,alignment,services,events)
        out=(U32*2)(0xdeadbeef,0xcafebabe);output=ctx((0xa5a5a5a5,)*19)
        if name=='interrupt':
            incoming=ctx(irq_context);status=self.interrupt(ctypes.byref(incoming),ctypes.byref(output),ctypes.byref(b.cpu),ctypes.byref(b.io))
            expected_context=(0xa5a5a5a5,)*19 if status else r['context']
            if ctxwords(output)!=expected_context or ctxwords(incoming)!=irq_context:raise AssertionError((label,'IRQ context',ctxwords(output),expected_context))
        else:
            status=self.execute(REGIONS[name][0],(U32*12)(*args),out,ctypes.byref(b.cpu),ctypes.byref(b.io));expected_context=(0xa5a5a5a5,)*19
            expected=(0xdeadbeef,0xcafebabe) if status else r['result']
            if tuple(out)!=expected:raise AssertionError((label,'result',tuple(out),expected))
        if status!=r['status'] or b.errors:raise AssertionError((label,'status',status,r['status'],b.errors[:3]))
        for key,actual in (('calls',b.calls),('events',b.events),('timeline',b.timeline)):
            if actual!=r[key]:
                mismatch=next(((i,a,z) for i,(a,z) in enumerate(zip(actual,r[key])) if a!=z),None)
                raise AssertionError((label,key,len(actual),len(r[key]),mismatch))
        if b.cpu_words()!=r['cpu']:raise AssertionError((label,'CPU',b.cpu_words(),r['cpu']))
        if b.snapshot()!=r['memory']:
            diff=[(hex(base+i),a,z) for (base,_),aa,zz in zip(MAPPED,b.snapshot(),r['memory']) for i,(a,z) in enumerate(zip(aa,zz)) if a!=z]
            raise AssertionError((label,'RAM',diff[:20]))
        if first.actions!=second.actions or first.registers!=second.registers:raise AssertionError((label,'bus effects'))
        self.visited|=r['visited'];self.steps+=r['steps'];self.counts[name]=self.counts.get(name,0)+1
        self.indirect_sites.update(pc for pc,_,_ in r['service_sites'])
        self.digest.update(label.encode());self.digest.update(struct.pack('<i4I',status,*out,*r['cpu']))
        for data in r['memory']:self.digest.update(data)
        self.records.append((label,before_memory,name,args,cpu,irq_context or (0,)*19,status,tuple(out),expected_context,r['cpu'],r['memory'],first.actions,services,events))
        return r

def basic_cases(c):
    for icfg in (0,0x100,0x200,0x300,0x01090700,0xffffffff,0x12345678):
        for name in ('gate_disable','gate_enable'):c.compare(f'gate/{name}/{icfg}',initial(),name,cpu=(0,icfg))
    for value in (0,1,0x7fffffff,0x80000000,0xffffffff):
        c.compare(f'clock/{value}',initial(),'clock',returns={(READ,0x10704):value})
    for bank in (0,1,2,0xffffffff):
        for name in ('peer_stop','peer_resume'):
            c.compare(f'peer/{name}/{bank}',initial(),name,(bank,))
    for number in (0,1,7,8,31,63,124,125,127):
        for core in (0,1,255,256,0xffffffff):
            for handler in (0,0x01c041dc):
                c.compare(f'register/{number}/{core}/{handler}',initial(),'register',(number,number*79,handler,core),cpu=(1,0),alignment=number%4)
    for mode in (0,1,2,255):
        for cpu in (0,1,2,0xffffffff,0x40000000):
            for token in (0,0x12345678):
                m=initial(mode);c.compare(f'enter/{mode}/{cpu}/{token}',m,'enter',(token,0xaabbccdd),cpu=(cpu,0x300))
                setword(m,COMMAND,token);c.compare(f'leave/{mode}/{cpu}/{token}',m,'leave',cpu=(cpu,0x300))
    for old in (0,1,2,0xffffffff):
        for number in (0,1):
            m=initial();setword(m,LOCK_COUNTS+4*number,old);setword(m,IRQ_COUNTS+4*number,old)
            c.compare(f'enter depth/{number}/{old}',m,'enter',(1,2),cpu=(number,0x12345678))
            c.compare(f'leave depth/{number}/{old}',m,'leave',cpu=(number,0x12345678))

def interrupt_cases(c):
    for mode in (0,1,2):
        for number in (0,1,2,0xffffffff,0x40000000):
            for flags in (0,1,4,15,0xffffffff):
                m=initial(mode);setword(m,ARGUMENT,0x89abcdef)
                c.compare(f'IRQ/{mode}/{number}/{flags}',m,'interrupt',cpu=(number,0x300),irq_context=context(flags))
    for mode in (0,1):
        for target in (*[a for a,_ in (REGIONS|REUSED).values()],0x12345679,0xffffffff):
            m=initial(mode);setword(m,COMMAND,target);setword(m,ARGUMENT,0x11223344)
            c.compare(f'indirect collision/{mode}/{target}',m,'interrupt',
                mutations=((('call',target),0,COMMAND,0x76543210,4),(('call',target),0,ARGUMENT,0x88776655,4)))

def mutation_cases(c):
    m=initial(1);setword(m,ACK,1,1)
    c.compare('initial busy ACK released at original spin',m,'enter',(1,2),auto_ack=False,
        mutations=(((BARRIER,0),1,ACK,0,1),((WRITE,0x01eef1a0),0,ACK,1,1)))
    m=initial(1);setword(m,ACK,2,1)
    c.compare('raw ACK2 does not enter ACK1 spin',m,'enter',(1,2))
    c.compare('CPU event return ignored',initial(),'enter',(1,2),event_return=0xfedcba9876543210)
    for number,at in ((0x62221e00,0x33000000),(0xffffffff,None),(128,None)):
        c.compare(f'raw IRQ index/{number}',initial(),'register',(number,0xffffffff,0,0))
    for which in (0,1,2,3):
        c.compare(f'delayed cache/{which}',initial(),'enter',(1,2),returns={(READ,0x01eee008):[0]*which+[16384]})
        c.compare(f'delayed peer stop/{which}',initial(),'peer_stop',(1,),returns={(READ,0x01eee004):[0]*(which+1)+[16]})
    for mode in (0,1):
        for op,a,which,at,v,n in (
            (CLI,0,0,COMMAND,7,4),(CNUM,0,0,IRQ_COUNTS,1,4),
            (BARRIER,0,0,MODE,mode^1,1),(BARRIER,0,2,COMMAND,0x12345678,4),
            (WRITE,0x01eef1a0,0,COMMAND,1,4),(READ,0x01eee008,0,ARGUMENT,99,4)):
            c.compare(f'enter mutation/{mode}/{op}/{a}/{which}',initial(mode),'enter',(0,8),mutations=(((op,a),which,at,v,n),))
        m=initial(mode);setword(m,COMMAND,0x12345678);setword(m,ARGUMENT,0x88776655)
        for op,which,at,value in ((BARRIER,1,COMMAND,0),(BARRIER,2,ARGUMENT,9),(CNUM,0,MODE,mode^1),
                (CLI,0,LOCK_COUNTS,0xffffffff),(POP,0,ACK,0)):
            n=1 if at in (MODE,ACK) else 4
            c.compare(f'IRQ mutation/{mode}/{op}/{which}',m,'interrupt',mutations=(((op,0 if op!=POP else STACK-32),which,at,value,n),))
    for at in (COMMAND,ACK,ARGUMENT,LOCK_COUNTS,IRQ_COUNTS,0,0xfffffffc,0x33000000):
        number=((at-IRQ_COUNTS)&0xffffffff)>>2;m=initial()
        # Both raw nesting words must remain mapped; their eight-byte relation
        # is retained, and a missing neighboring word is a matched map guard.
        c.compare(f'counter alias/{at}',m,'enter',(7,9),cpu=(number,0x300))
        c.compare(f'IRQ counter alias/{at}',m,'interrupt',cpu=(number,0x300))
    for at in (STACK-32,STACK-28,STACK-12,STACK-4,STACK,STACK+60):
        number=((at-IRQ_COUNTS)&0xffffffff)>>2
        for mode in (0,1):
            c.compare(f'private IRQ counter/{mode}/{at}',initial(mode),'interrupt',cpu=(number,0x300))
        # The original private stack remains reserved even before its IRQ frame
        # is populated. These are domain observations, not native returns.
        c.compare(f'private enter counter/{at}',initial(),'enter',(1,2),cpu=(number,0x300))
    m=initial();cpu=(1,0)
    for i,(name,args) in enumerate((('register',(124,7,0x01c041dc,1)),('enter',(0,0)),('enter',(5,7)),('interrupt',()),('leave',()),('leave',()),('clock',()))):
        r=c.compare(f'carried CPU/state/{i}',m,name,args,cpu=cpu);m=r['memory'];cpu=r['cpu']

def prefix_cases(c):
    for name,args,mode in (('register',(125,7,0x01c041dc,255),0),('enter',(0,0),0),('enter',(0,0),1),
            ('leave',(),0),('leave',(),1),('interrupt',(),0),('interrupt',(),1)):
        for budget in range(30):
            m=initial(mode);setword(m,COMMAND,0x12345678)
            c.compare(f'event prefix/{name}/{mode}/{budget}',m,name,args,events=budget)
    for name,args,mode,script in (('enter',(1,2),1,{'auto_ack':False}),('interrupt',(),1,{'clear_irq':False}),
            ('peer_stop',(0,),0,{'returns':{(READ,0x01eee000):0}}),('enter',(1,2),0,{'returns':{(READ,0x01eee008):0}})):
        for budget in (0,1,2,7,31):c.compare(f'held native wait/{name}/{budget}',initial(mode),name,args,events=budget,**script)
    for mode in (0,1):
        m=initial(mode);setword(m,COMMAND,0x01c04862);setword(m,ARGUMENT,0xabcdef01)
        c.compare(f'callback admission/{mode}',m,'interrupt',services=0)
        for at in (0x30000000,STACK-32,STACK+63,0x10704,0x40000000,0xffffffff):
            c.compare(f'callback forbidden map/{mode}/{at}',m,'interrupt',probes=((('call',0x01c04862),0,at,4,1),))
    for op,a in ((ICFG_WRITE,0),(CLI,0),(LOCKSET,0),(WRITE,0x01eef1a0),(PUSH,STACK-12),(RTI,context(15)[18]&0x07fffffe)):
        name='interrupt' if op in (PUSH,RTI) else 'register' if op==ICFG_WRITE else 'enter'
        args=(125,7,0x01c041dc,0) if name=='register' else (1,2) if name=='enter' else ()
        c.compare(f'event callback forbidden map/{op}',initial(),name,args,probes=(((op,a),0,STACK-4,4,0),))

def source_paths():
    names=set(SOURCES)|{'tools/storage_platform_machine.py','tools/verify_storage_platform.py','tools/build_storage_platform.py',
        'tests/test_storage_platform_machine.py','tests/storage_platform_sanitize.c','research/input-manifest.json',
        'analysis/firmware/m571_g_app/memory-layout.json','third_party/ultrarig/LICENSE.md'}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            p=Path(filename).resolve()
            if p.is_relative_to(ROOT) and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    for folder in ('upstream/pi32v2-isa/isa','upstream/pi32v2-isa/tools/hwtest/semantics'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.toml'))
    pending=list(SOURCES)+['tests/storage_platform_sanitize.c']
    while pending:
        name=pending.pop()
        for include in re.findall(r'^#include\s+"([^"]+)"',(ROOT/name).read_text(),re.M):
            match=next((p.resolve() for p in ((ROOT/name).parent/include,ROOT/'firmware/include'/include) if p.is_file()),None)
            if match is None:raise ValueError('unresolved platform C include')
            child=match.relative_to(ROOT).as_posix()
            if child not in names:names.add(child);pending.append(child)
    return sorted(names)

def guard_checks(c):
    checks=[]
    for operation in ('ordinary','interrupt'):
        for missing in ('input','output','cpu','io','map','call','event'):
            b=Backend(initial(),(0,0x300),Script(),'clock');out=(U32*2)(0xdeadbeef,0xcafebabe)
            incoming=ctx(context(7));output=ctx((0xa5a5a5a5,)*19)
            if missing=='map':b.io.map=MAP()
            if missing=='call':b.io.call=CALL()
            if missing=='event':b.io.event=EVENT()
            cpu=None if missing=='cpu' else ctypes.byref(b.cpu);io=None if missing=='io' else ctypes.byref(b.io)
            if operation=='ordinary':status=c.execute(REGIONS['clock'][0],None if missing=='input' else (U32*12)(),None if missing=='output' else out,cpu,io)
            else:status=c.interrupt(None if missing=='input' else ctypes.byref(incoming),None if missing=='output' else ctypes.byref(output),cpu,io)
            if status!=-200 or tuple(out)!=(0xdeadbeef,0xcafebabe) or ctxwords(output)!=(0xa5a5a5a5,)*19:
                raise AssertionError(('platform invalid API',operation,missing,status))
            checks.append({'label':operation+' missing '+missing,'status':status})
    for entry in (0,REGIONS['clock'][0]+2,REGIONS['interrupt'][0],REUSED['irq_enter'][0]):
        b=Backend(initial(),(0,0x300),Script(),'clock');out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=c.execute(entry,(U32*12)(),out,ctypes.byref(b.cpu),ctypes.byref(b.io))
        if status!=-200 or tuple(out)!=(0xdeadbeef,0xcafebabe):raise AssertionError(('platform entry guard',entry,status))
        checks.append({'label':'invalid ordinary entry '+hex(entry),'status':status})
    for work in (0,1,2,3,5,8,12):
        for operation in ('enter','interrupt'):
            b=Backend(initial(1),(0,0x300),Script(auto_ack=False,clear_irq=False),operation,work=work)
            out=(U32*2)(0xdeadbeef,0xcafebabe);incoming=ctx(context(7));output=ctx((0xa5a5a5a5,)*19)
            status=c.interrupt(ctypes.byref(incoming),ctypes.byref(output),ctypes.byref(b.cpu),ctypes.byref(b.io)) if operation=='interrupt' else c.execute(REGIONS[operation][0],(U32*12)(),out,ctypes.byref(b.cpu),ctypes.byref(b.io))
            if status!=-203 or tuple(out)!=(0xdeadbeef,0xcafebabe) or ctxwords(output)!=(0xa5a5a5a5,)*19 or b.errors:
                raise AssertionError(('platform work guard',operation,work,status,b.errors))
            checks.append({'label':operation+' portable work '+str(work),'status':status})
    return checks

def write_fixtures(path,records):
    def words(f,*values):f.write(struct.pack('<'+'I'*len(values),*(v&0xffffffff for v in values)))
    with path.open('wb') as f:
        words(f,0x31505453,len(records),len(MAPPED))
        for base,size in MAPPED:words(f,base,size)
        for label,before,name,args,cpu,incoming,status,result,context_out,final_cpu,after,actions,services,events in records:
            raw=label.encode();words(f,len(raw));f.write(raw)
            words(f,REGIONS[name][0],*(tuple(args)+(0,)*(12-len(args))),*cpu,*incoming,status,*result,*context_out,*final_cpu,services,events,len(actions))
            for raw in before:f.write(raw)
            for op,address,width,value,ret,argv,mutations in actions:
                words(f,op,address,width);f.write(struct.pack('<QQ',value,ret));words(f,*argv,len(mutations))
                for kind,a,n,v in mutations:
                    words(f,kind,a,n)
                    if kind==2:words(f,v)
                    else:f.write((v&((1<<(8*n))-1)).to_bytes(n,'little'))
            for raw in after:f.write(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path)
    p.add_argument('--part',choices=('all','basic','interrupt','mutation','prefix'),default='all');a=p.parse_args();c=Corpus(a.library)
    before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    library_hash=hashlib.sha256(a.library.read_bytes()).hexdigest()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    packed=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    if hashlib.sha256(packed).hexdigest()!=PINNED or hashlib.sha256(app).hexdigest()!=DECODED or unpack_app(packed)[2]['app.bin']!=app:
        raise ValueError('platform original input changed')
    for name,run in (('basic',basic_cases),('interrupt',interrupt_cases),('mutation',mutation_cases),('prefix',prefix_cases)):
        if a.part in ('all',name):run(c)
    new={pc for pc in c.program.code if any(s<=pc<e for s,e in REGIONS.values())};gaps=sorted(set(c.program.code)-c.visited)
    def bodies(registry):
        return {name:{'start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(s<=pc<e for pc in c.program.code),'visited_instructions':sum(s<=pc<e for pc in c.visited)} for name,(s,e) in registry.items()}
    report={'result':'pass','component':'storage-platform','original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'functions':bodies(REGIONS),'reused_functions':bodies(REUSED),'new_original_functions':9,'new_data_exclusions':[],
        'comparisons':len(c.records),'counts':c.counts,'steps':c.steps,'visited':[hex(pc) for pc in sorted(c.visited)],
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(c.visited&new),'unvisited_new':[hex(pc) for pc in gaps if pc in new],
            'all_decoded':len(c.program.code),'all_visited':len(c.visited),'unvisited_all':[hex(pc) for pc in gaps]},
        'gap_instructions':{hex(pc):c.program.code[pc][0] for pc in gaps},
        'direct_sites':{hex(pc):{'target':hex(target),'visited':pc in c.visited} for pc,target in DIRECT_SITES.items()},
        'indirect_sites':{hex(pc):{'arity':arity,'visited':pc in c.indirect_sites} for pc,arity in INDIRECT_SITES.items()},
        'loaded_instruction_windows':{hex(pc):{'bytes':n,'sha256':hashlib.sha256(region_bytes(app,pc,pc+n)).hexdigest()}
            for pc,(_,n,*_) in c.program.code.items()},
        'cpu_primary_evidence':c.program.isa_records,
        'auxiliary_initial_state':{'start':hex(INITIAL_MAILBOX[0]),'end_exclusive':hex(INITIAL_MAILBOX[1]),
            'sha256':INITIAL_MAILBOX[2],'classification':'mutable initialized mailbox and lock depths, not immutable data'},
        'portable_failure_cases':sum(row[6]!=0 for row in c.records),
        'outputs_state_ordered_events_sha256':c.digest.hexdigest(),
        'interrupt_context':'Separate supplied activation; actual native 32-byte PSR/RETS/RETI and r0..r4 frame, explicit RTI; portable output publishes only after completion.',
        'limitations':[
            'Nine complete bodies and two unchanged IRQ helpers are compared offline; no integration into frozen storage-runtime01 or new hardware operation is performed.',
            'MMIO values, lock completion and peer acknowledgment/callback completion are explicit synthetic fixtures. No physical interrupt delivery, scheduler, fairness, atomicity, implicit memory ordering or timing guarantee is inferred.',
            'The two native indirect sites always remain one-word external callbacks, including tokens equal to recovered entries; r4..r15 follow the preserved native callback ABI.',
            'Supplied interrupt context and ICFG describe entry explicitly. RTI returns to restored RETI; the comparison does not synthesize the hardware interrupt-entry transition or automatic vector dispatch.',
            'Portable private/map/work/service/event guards preserve earlier public RAM/ICFG and suppress returned words/IRQ context. Incomplete private GPR/PSR temporaries are not exposed as portable resumable CPU state.',
            'Each individual mapped access must not wrap; address calculations and core/index words remain raw uint32. Unchanged IRQ helpers require their counter addresses in ordinary mapped RAM.',
            'Source work allowance is a portable operation ceiling with child-local bounds, not native cycles or arbitrary instruction-prefix equivalence. Matched event/service prefixes are reported separately.',
            'Mailbox and lock bytes are mutable initial-state witnesses, not new immutable tables; the external vector table is supplied RAM and not contained in the application image.'],
        'hardware_test':False,'device_access':False,'audio_test':False,'firmware_changed':False}
    if a.part=='all':
        if gaps or c.indirect_sites!=set(INDIRECT_SITES):raise ValueError('platform full corpus missed an instruction or indirect site')
        report['invalid_api_checks']=guard_checks(c)
    if a.mini_image:
        raw=a.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=MINI:raise ValueError('reviewed MINI image changed')
        mini=unpack_app(raw)[2]['app.bin']
        for s,e in [*(REGIONS|REUSED).values(),INITIAL_MAILBOX[:2]]:
            if region_bytes(app,s,e)!=region_bytes(mini,s,e):raise ValueError('MINI platform bytes differ')
        report['mini_binding']={'sha256':MINI,'complete_regions':11,'instructions':217,'auxiliary_mutable_bytes':20}
    if a.fixtures:write_fixtures(a.fixtures,c.records)
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    if report['source_sha256']!=before or hashlib.sha256(a.library.read_bytes()).hexdigest()!=library_hash:
        raise ValueError('platform source/library bytes changed during comparison')
    report['library_sha256']=library_hash
    if a.output:a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'comparisons':len(c.records),'steps':c.steps,'visited':len(c.visited),'new_visited':len(c.visited&new),
        'gaps':list(map(hex,gaps)),'indirect_sites':list(map(hex,c.indirect_sites))}))
if __name__=='__main__':main()
