"""Compare original diagnostic-record and control bodies with portable C."""
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
from storage_fault_machine import (StorageFaultProgram,REGIONS,REUSED,ARITIES,SCALAR,DIRECT_SITES,INCOMING,
 MAPPED,GLOBAL,STATE,IRQ_COUNTS,LOCK,HEADER,RECORDS,METADATA,CURRENT,STACK,CONTROL,DATA,ROOT,READ,WRITE,
 BARRIER,CLI,STI,CNUM,TESTSET,RETS,HALT,INITIAL_LOCK,region_bytes)
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app
U32,U64=ctypes.c_uint32,ctypes.c_uint64
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
EVENT=ctypes.CFUNCTYPE(U64,ctypes.c_void_p,U32,U32,U32,U64,ctypes.POINTER(Borrowed))
class CPU(ctypes.Structure):_fields_=[('cnum',U32),('icfg',U32)]
class IO(ctypes.Structure):_fields_=[('map',MAP),('event',EVENT),('opaque',ctypes.c_void_p),('events',U32),('work',U32)]
SOURCES=tuple('firmware/src/hyperrig_'+s+'.c' for s in ('storage_fault','storage_coordination','controls','control_actions','selection','preset_storage','preset_preflight','preset_loader'))
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'

def setword(memory,a,v,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:data[a-base:a-base+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little');return
    raise ValueError(f'fault fixture write {a:#x}/{n}')
def getword(memory,a,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:return int.from_bytes(data[a-base:a-base+n],'little')
    raise ValueError(f'fault fixture read {a:#x}/{n}')
def initial():
    m=[bytearray((i*17+j*13+5)&255 for i in range(n)) for j,(_,n) in enumerate(MAPPED)]
    setword(m,LOCK,0,1)
    for a in range(IRQ_COUNTS,IRQ_COUNTS+16,4):setword(m,a,0)
    setword(m,STATE+8,0,1);setword(m,STATE+104,0);setword(m,HEADER,0)
    for a in range(METADATA,METADATA+12):setword(m,a,0,1)
    return m
def packed_metadata(memory,counters=(0,0,0,0),mode=0,tail=1,first=0x12345678):
    second=counters[0]|(counters[1]<<8)|(counters[2]<<16)|(counters[3]<<20)|(mode<<24)
    value=(first^(second*0x9e3779b1)^(tail*0x85ebca6b)^0x7c1f0b5d)&0xffffffff
    value^=value>>15;value=(value*0x2c1b3c6d)&0xffffffff;value^=value>>12
    for a,v in ((METADATA,first),(METADATA+4,second),(METADATA+8,tail|((value&65535)<<16))):setword(memory,a,v)

class Script:
    def __init__(self,returns=None,mutations=(),probes=(),control=0,event_return=0):
        self.returns=returns or {};self.mutations=mutations;self.probes=probes;self.seen={};self.actions=[]
        self.event_return=event_return;self.registers={CONTROL:control,DATA:0x5a,0x01eef07c:0x12345678,0x01eef27c:0x87654321}
    def event(self,op,a,n,v,m):
        key=(op,a);index=self.seen.get(key,0);self.seen[key]=index+1;ops=[]
        value=self.returns.get(key,self.registers.get(a,0) if op==READ else self.event_return)
        result=(value[min(index,len(value)-1)] if isinstance(value,(tuple,list)) else value)&((1<<64)-1)
        if op==WRITE:self.registers[a]=v&((1<<(n*8))-1)
        for at,which,address,value,size in self.mutations:
            if at==key and (which<0 or index==which):m.write(address,value,size);ops.append((1,address,size,value))
        for at,which,address,size,writable in self.probes:
            if at==key and (which<0 or index==which):
                if m.public_probe(address,size,writable):raise ValueError('expected fault borrowed-view rejection')
                ops.append((2,address,size,writable))
        self.actions.append((op,a,n,v,result,ops));return result

class Backend:
    def __init__(self,memory,cpu,script,alignment=0,events=10000,work=4000000):
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory];self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment);array[:]=data;self.arrays.append(array)
        self.cpu=CPU(*cpu);self.script=script;self.events=[];self.timeline=[];self.errors=[];self.borrowed=None
        self.io=IO(MAP(self.map),EVENT(self.event),None,events,work)
    def map(self,opaque,a,n,writable):
        for (base,size),data in zip(MAPPED,self.arrays):
            if base<=a<=a+n<=base+size:return ctypes.addressof(data)+a-base
        return None
    def public_probe(self,a,n,writable=0):return bool(self.borrowed.map(self.borrowed.opaque,a,n,writable))
    def read(self,a,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,0) if self.borrowed else self.map(None,a,n,0)
        if p is None:raise ValueError('fault callback unavailable read')
        return int.from_bytes(ctypes.string_at(p,n),'little')
    def write(self,a,v,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,1) if self.borrowed else self.map(None,a,n,1)
        if p is None:raise ValueError('fault callback unavailable write')
        ctypes.memmove(p,(v&((1<<(8*n))-1)).to_bytes(n,'little'),n)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def cpu_words(self):return self.cpu.cnum,self.cpu.icfg
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())+struct.pack('<II',*self.cpu_words())).hexdigest()
    def event(self,opaque,op,a,n,v,borrowed):
        try:
            before=self.digest();self.borrowed=borrowed.contents;value=self.script.event(op,a,n,v,self);self.borrowed=None
            self.events.append((op,a,n,v,value,before,self.digest()));self.timeline.append(('event',len(self.events)-1));return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library):
        self.program=StorageFaultProgram();self.library=ctypes.CDLL(str(Path(library).resolve()))
        self.execute=self.library.hyperrig_storage_fault_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(CPU),U32,ctypes.POINTER(IO)]
        self.visited=set();self.steps=0;self.records=[];self.counts={};self.digest=hashlib.sha256()
    def compare(self,label,memory,name,args=(),cpu=(0,0x01090700),caller=INCOMING[1],alignment=0,events=10000,**script_args):
        before=tuple(map(bytes,memory));first=Script(**script_args)
        try:r=self.program.execute(memory,name,args,cpu,caller,first.event,events)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        second=Script(**script_args);b=Backend(memory,cpu,second,alignment,events)
        out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=self.execute(REGIONS[name][0],(U32*12)(*args),out,ctypes.byref(b.cpu),caller,ctypes.byref(b.io))
        expected=(0xdeadbeef,0xcafebabe) if r['status'] else r['result']
        if status!=r['status'] or tuple(out)!=expected or b.errors:raise AssertionError((label,'status/result',status,r['status'],tuple(out),expected,b.errors[:3]))
        for key,actual in (('events',b.events),('timeline',b.timeline)):
            if actual!=r[key]:
                mismatch=next(((i,a,z) for i,(a,z) in enumerate(zip(actual,r[key])) if a!=z),None)
                raise AssertionError((label,key,len(actual),len(r[key]),mismatch))
        if b.cpu_words()!=r['cpu']:raise AssertionError((label,'CPU',b.cpu_words(),r['cpu']))
        if b.snapshot()!=r['memory']:
            diff=[(hex(base+i),a,z) for (base,_),aa,zz in zip(MAPPED,b.snapshot(),r['memory']) for i,(a,z) in enumerate(zip(aa,zz)) if a!=z]
            raise AssertionError((label,'RAM',diff[:20]))
        if first.actions!=second.actions or first.registers!=second.registers:raise AssertionError((label,'bus effects'))
        self.visited|=r['visited'];self.steps+=r['steps'];self.counts[name]=self.counts.get(name,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<i4I',status,*out,*r['cpu']))
        for data in r['memory']:self.digest.update(data)
        self.records.append((label,before,name,args,cpu,caller,status,tuple(out),r['cpu'],r['memory'],first.actions,events))
        return r

def basic_cases(c):
    rng=random.Random(714315)
    for value in (0,1,0xffffffff,0x80000000,0xa5e00000,0xa5efffff,0xd0600000,0xd06fffff,0xe7c00000,0xe7cfffff,0xa5dfffff):
        c.compare(f'tag/{value:x}',initial(),'tag',(value,))
    for i in range(160):c.compare(f'checksum/{i}',initial(),'checksum',tuple(rng.getrandbits(32) for _ in range(3)))
    for prefix in (0,0xc7a5,0xc7a4):
        for count in (0,1,2,3,255,65535):
            m=initial();setword(m,HEADER,(prefix<<16)|count)
            c.compare(f'count/{prefix}/{count}',m,'record_count')
            for source in (CURRENT,RECORDS,RECORDS+24,HEADER,0x33000001):
                for tag in (0,0xa5e00000,0xd0600000,0xe7c00000):
                    mm=list(map(bytearray,m));setword(mm,source,tag)
                    c.compare(f'append/{prefix}/{count}/{source:x}/{tag:x}',mm,'append',(source,),alignment=count&3)
    for mode in (0,1,2,3,4,5,6,255):
        for source in (0x33000001,METADATA,METADATA+1,METADATA-3,RECORDS):
            m=initial()
            for i in range(11):setword(m,source+i,rng.randrange(256),1)
            setword(m,source+8,mode,1)
            c.compare(f'encode/{mode}/{source:x}',m,'encode',(source,),alignment=1)
    for mode in (0,1,4,5,6,255):
        for tail in (0,1,15,16,255,0xff01):
            for output in (0,0x33000001,METADATA,METADATA+1,METADATA-3):
                m=initial();packed_metadata(m,(0x23,0x9f,7,11),mode,tail)
                c.compare(f'decode/{mode}/{tail}/{output:x}',m,'decode',(output,),alignment=1)
    for kind in (0,1,2,3,0xffffffff):
        for alternate in (0,1,0xffffffff):
            for x in (0,14,15,254,255):
                m=initial();packed_metadata(m,(x,x,min(x,15),min(x,15)),5,1)
                c.compare(f'update/{kind}/{alternate}/{x}',m,'update',(kind,alternate))
                setword(m,STATE+104,0x800 if alternate else 0)
                c.compare(f'once/{kind}/{alternate}/{x}',m,'once',(kind,))
    for invalid in (0,1):
        m=initial()
        if not invalid:packed_metadata(m)
        for done in (0,1,255):
            setword(m,STATE+8,done,1);c.compare(f'once validity/{invalid}/{done}',m,'once',(1,))

def peripheral_cases(c):
    for number in (0,1,2,0xffffffff,0x40000000):
        for old in (0,1,2,0xffffffff):
            m=initial();setword(m,IRQ_COUNTS,old)
            c.compare(f'lock/{number}/{old}',m,'acquire',cpu=(number,0x300))
            c.compare(f'unlock/{number}/{old}',m,'release',cpu=(number,0x300))
    for identifier in (0,1,160,255,256,511,0x8000,0xffff,0xffffffff):
        for control in (0,0x100,0x80000100):
            c.compare(f'register read/{identifier}/{control}',initial(),'read_register',(identifier,),control=control)
            c.compare(f'register write/{identifier}/{control}',initial(),'write_register',(identifier,0xfedcba98),control=control)
        for start,width,value in ((0,0,0),(0,1,1),(4,1,1),(7,5,31),(31,31,0xffffffff),(32,32,1),(0xffffffff,0xffffffff,0xffffffff)):
            c.compare(f'masked/{identifier}/{start}/{width}',initial(),'masked_register',(identifier,start,width,value))
    for value in (0,1,255,256,0x80000000,0xffffffff):
        c.compare(f'exchange/{value}',initial(),'exchange',(value,),returns={(READ,DATA):0x123456ab})
    for number in (0,1,2,0xffffffff,0x40000000):
        for done in (0,1):
            for caller in (0,INCOMING[1],0x12345679,0xffffffff):
                m=initial();packed_metadata(m,(7,8,9,10));setword(m,STATE+8,done,1)
                setword(m,STATE+104,0x800);setword(m,CURRENT,0xa5e00123);setword(m,HEADER,0xc7a50002)
                c.compare(f'fatal/{number}/{done}/{caller}',m,'fatal',cpu=(number,0x300),caller=caller)

def mutation_cases(c):
    for old in (1,4,5,15,255):
        m=initial();setword(m,LOCK,old,1)
        c.compare(f'lock old flags/{old}',m,'acquire',mutations=(((TESTSET,LOCK),0,LOCK,0,1),))
    for delay in (1,2,7):
        c.compare(f'busy exchange/{delay}',initial(),'exchange',(0xaabbccdd,),returns={(READ,CONTROL):[0]+[2]*delay+[0]})
    for op,address,which,target,value,size in (
        (RETS,0,0,CURRENT,0xe7c01234,4),(CNUM,0,0,HEADER,0xc7a50002,4),
        (RETS,0,0,STATE+104,0x800,4),(RETS,0,0,STATE+8,1,1),
        (CLI,0,0,LOCK,4,1),(TESTSET,LOCK,0,LOCK,0,1),
        (READ,0x01eef27c,0,CURRENT,0x11223344,4),(WRITE,DATA,0,CURRENT+12,0x99887766,4)):
        m=initial();packed_metadata(m);setword(m,CURRENT,0xa5e01234)
        mutations=(((op,address),which,target,value,size),)
        if op==CLI:mutations+=(((TESTSET,LOCK),0,LOCK,0,1),)
        c.compare(f'fatal callback/{op}/{address}/{target}',m,'fatal',mutations=mutations)
    for at in (LOCK,HEADER,CURRENT,0,0xfffffffc,STACK-24,CONTROL):
        number=((at-IRQ_COUNTS)&0xffffffff)>>2
        c.compare(f'raw counter mapping/{at}',initial(),'acquire',cpu=(number,0x300),events=50,
            mutations=(((TESTSET,LOCK),-1,LOCK,0,1),))
    m=initial();packed_metadata(m)
    for entry,args in (('encode',(STACK-24,)),('decode',(STACK-24,)),('append',(STACK-24,)),
            ('decode',(0xffffffff,)),('encode',(0xfffffffe,)),('append',(0x40000000,))):
        c.compare(f'reached object guard/{entry}/{args[0]}',m,entry,args)
    for offset in (1,2,4,5,9,10):
        for entry in ('decode','encode','append'):
            c.compare(f'partial object/{entry}/{offset}',m,entry,(0x33000200-offset,))
    m=initial();packed_metadata(m)
    for i,(entry,args) in enumerate((('once',(1,)),('once',(2,)),('update',(2,0)),('acquire',()),('release',()),('fatal',()),('fatal',()))):
        r=c.compare(f'carried/{i}',m,entry,args);m=r['memory']

def prefix_cases(c):
    for entry,args in (('acquire',()),('release',()),('exchange',(1,)),('read_register',(160,)),('write_register',(160,1)),('masked_register',(160,4,1,1)),('fatal',())):
        for events in range(75):
            m=initial();packed_metadata(m);setword(m,CURRENT,0xa5e00123)
            c.compare(f'event prefix/{entry}/{events}',m,entry,args,events=events)
    for entry,args,script in (('acquire',(),{'mutations':(((CLI,0),0,LOCK,255,1),)}),('exchange',(1,),{'returns':{(READ,CONTROL):2}})):
        for events in (0,1,2,7,31):c.compare(f'held loop/{entry}/{events}',initial(),entry,args,events=events,**script)
    for op,address in ((RETS,0),(CLI,0),(TESTSET,LOCK),(WRITE,DATA),(READ,DATA)):
        for target,n in ((STACK-24,1),(STACK+63,2),(CONTROL,4),(0x40000000,4),(0xffffffff,4)):
            c.compare(f'borrow guard/{op}/{target}',initial(),'fatal',probes=(((op,address),0,target,n,1),))
    for first,second in ((STACK-24,0x40000000),(0x40000000,STACK-24)):
        c.compare(f'first callback fault/{first}',initial(),'fatal',
            probes=(((RETS,0),0,first,1,0),((RETS,0),0,second,1,0)))

def source_paths():
    names=set(SOURCES)|{'tools/storage_fault_machine.py','tools/verify_storage_fault.py','tools/build_storage_fault.py',
        'tests/test_storage_fault_machine.py','tests/storage_fault_sanitize.c','research/input-manifest.json',
        'analysis/firmware/m571_g_app/memory-layout.json','third_party/ultrarig/LICENSE.md'}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            p=Path(filename).resolve()
            if p.is_relative_to(ROOT) and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    for folder in ('upstream/pi32v2-isa/isa','upstream/pi32v2-isa/tools/hwtest/semantics'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.toml'))
    pending=list(SOURCES)+['tests/storage_fault_sanitize.c']
    while pending:
        name=pending.pop()
        for include in re.findall(r'^#include\s+"([^"]+)"',(ROOT/name).read_text(),re.M):
            match=next((p.resolve() for p in ((ROOT/name).parent/include,ROOT/'firmware/include'/include) if p.is_file()),None)
            if match is None:raise ValueError('unresolved fault C include')
            child=match.relative_to(ROOT).as_posix()
            if child not in names:names.add(child);pending.append(child)
    return sorted(names)

def guard_checks(c):
    checks=[]
    for missing in ('input','output','cpu','io','map','event'):
        b=Backend(initial(),(0,0x300),Script());out=(U32*2)(0xdeadbeef,0xcafebabe)
        if missing=='map':b.io.map=MAP()
        if missing=='event':b.io.event=EVENT()
        status=c.execute(REGIONS['fatal'][0],None if missing=='input' else (U32*12)(),None if missing=='output' else out,
            None if missing=='cpu' else ctypes.byref(b.cpu),INCOMING[1],None if missing=='io' else ctypes.byref(b.io))
        if status!=-200 or tuple(out)!=(0xdeadbeef,0xcafebabe) or b.events or b.cpu_words()!=(0,0x300):
            raise AssertionError(('fault invalid API',missing,status))
        checks.append({'label':'missing '+missing,'status':status})
    for entry in (0,REGIONS['tag'][0]+2,REUSED['irq_enter'][0],HALT):
        b=Backend(initial(),(0,0x300),Script());out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=c.execute(entry,(U32*12)(),out,ctypes.byref(b.cpu),INCOMING[1],ctypes.byref(b.io))
        if status!=-200 or tuple(out)!=(0xdeadbeef,0xcafebabe):raise AssertionError(('fault entry guard',entry,status))
        checks.append({'label':'invalid entry '+hex(entry),'status':status})
    for work in (0,1,2,3,5,8,12,32):
        for entry in ('acquire','exchange'):
            m=initial();setword(m,LOCK,255,1)
            b=Backend(m,(0,0x300),Script(returns={(READ,CONTROL):2}),work=work)
            out=(U32*2)(0xdeadbeef,0xcafebabe)
            status=c.execute(REGIONS[entry][0],(U32*12)(),out,ctypes.byref(b.cpu),INCOMING[1],ctypes.byref(b.io))
            if status!=-203 or tuple(out)!=(0xdeadbeef,0xcafebabe) or b.errors:raise AssertionError(('fault work guard',entry,work,status))
            checks.append({'label':entry+' portable work '+str(work),'status':status})
    class ExhaustThenPrivate(Script):
        def event(self,op,a,n,v,m):
            for _ in range(100):
                if not m.public_probe(HEADER,1,0):break
            else:raise AssertionError('portable work ceiling not reached')
            if m.public_probe(STACK-24,1,0):raise AssertionError('private view after first fault')
            return 0
    b=Backend(initial(),(0,0x300),ExhaustThenPrivate(),work=20);out=(U32*2)(0xdeadbeef,0xcafebabe)
    status=c.execute(REGIONS['fatal'][0],(U32*12)(),out,ctypes.byref(b.cpu),INCOMING[1],ctypes.byref(b.io))
    if status!=-203 or tuple(out)!=(0xdeadbeef,0xcafebabe) or len(b.events)!=1 or b.errors:
        raise AssertionError(('fault first work error',status,b.errors))
    checks.append({'label':'callback work fault survives subsequent private probe','status':status})
    return checks

def write_fixtures(path,records):
    def words(f,*values):f.write(struct.pack('<'+'I'*len(values),*(v&0xffffffff for v in values)))
    with path.open('wb') as f:
        words(f,0x31465453,len(records),len(MAPPED))
        for base,size in MAPPED:words(f,base,size)
        for label,before,name,args,cpu,caller,status,result,final_cpu,after,actions,events in records:
            raw=label.encode();words(f,len(raw));f.write(raw)
            words(f,REGIONS[name][0],*(tuple(args)+(0,)*(12-len(args))),*cpu,caller,status,*result,*final_cpu,events,len(actions))
            for raw in before:f.write(raw)
            for op,address,width,value,ret,mutations in actions:
                words(f,op,address,width);f.write(struct.pack('<QQ',value,ret));words(f,len(mutations))
                for kind,a,n,v in mutations:
                    words(f,kind,a,n)
                    if kind==2:words(f,v)
                    else:f.write((v&((1<<(8*n))-1)).to_bytes(n,'little'))
            for raw in after:f.write(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path)
    p.add_argument('--part',choices=('all','basic','peripheral','mutation','prefix'),default='all');a=p.parse_args();c=Corpus(a.library)
    before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    library_hash=hashlib.sha256(a.library.read_bytes()).hexdigest()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    packed=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    if hashlib.sha256(packed).hexdigest()!=PINNED or hashlib.sha256(app).hexdigest()!=DECODED or unpack_app(packed)[2]['app.bin']!=app:
        raise ValueError('fault original input changed')
    for name,run in (('basic',basic_cases),('peripheral',peripheral_cases),('mutation',mutation_cases),('prefix',prefix_cases)):
        if a.part in ('all',name):run(c)
    new={pc for pc in c.program.code if any(s<=pc<e for s,e in REGIONS.values())};gaps=sorted(set(c.program.code)-c.visited)
    def bodies(registry):
        return {name:{'start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(s<=pc<e for pc in c.program.code),'visited_instructions':sum(s<=pc<e for pc in c.visited)} for name,(s,e) in registry.items()}
    report={'result':'pass','component':'storage-fault','original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'functions':bodies(REGIONS),'reused_functions':bodies(REUSED),'new_original_functions':15,'new_data_exclusions':[],
        'comparisons':len(c.records),'counts':c.counts,'steps':c.steps,'visited':[hex(pc) for pc in sorted(c.visited)],
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(c.visited&new),'unvisited_new':[hex(pc) for pc in gaps if pc in new],
            'all_decoded':len(c.program.code),'all_visited':len(c.visited),'unvisited_all':[hex(pc) for pc in gaps]},
        'gap_instructions':{hex(pc):c.program.code[pc][0] for pc in gaps},
        'direct_sites':{hex(pc):{'target':hex(target),'visited':pc in c.visited} for pc,target in DIRECT_SITES.items()},
        'indirect_sites':{},
        'loaded_instruction_windows':{hex(pc):{'bytes':n,'sha256':hashlib.sha256(region_bytes(app,pc,pc+n)).hexdigest()}
            for pc,(_,n,*_) in c.program.code.items()},
        'isa_primary_evidence':c.program.isa_records,
        'incoming_storage_call':{'start':hex(INCOMING[0]),'end_exclusive':hex(INCOMING[1]),'target':hex(INCOMING[2]),
            'instruction':c.program.incoming_instruction,'sha256':hashlib.sha256(c.program.incoming_bytes).hexdigest(),
            'arity':0,'decoded_bytes':4,'caller_executed_in_this_module':False},
        'auxiliary_initial_state':{'start':hex(INITIAL_LOCK[0]),'end_exclusive':hex(INITIAL_LOCK[1]),
            'sha256':INITIAL_LOCK[2],'classification':'mutable initialized lock word, not immutable data'},
        'portable_failure_cases':sum(row[6]<0 for row in c.records),
        'fatal_observations':sum(row[6]==1 for row in c.records),
        'outputs_state_ordered_events_sha256':c.digest.hexdigest(),
        'limitations':[
            'Fifteen complete bodies and two unchanged IRQ helpers are compared offline; the four-byte incoming storage call is bound but no frozen caller or storage-runtime integration is executed.',
            'Fatal success observes the native self-loop at 0x020009c8; it is not a native return, restart, durable write or hardware reset.',
            'The lock and MMIO busy loops are unbounded in the original. Explicit completion fixtures and finite event/work guards do not establish fairness, inter-core atomicity, implicit ordering or timing.',
            'Event callbacks may synchronously mutate public RAM but cannot modify supplied CPU/bookkeeping, borrow private frames, retain views or reenter. No original indirect function call is substituted.',
            'Public maps preserve aliases and raw uint32 address arithmetic; each access must fit without wrapping. The original header validation returns zero for counts above two; no portable count ceiling replaces it.',
            'The private metadata buffer has twelve bytes; only eleven are initialized and read. Private address tokens cannot be supplied as public arguments or borrowed by event callbacks.',
            'Source-operation work ceilings have child-local IRQ limits and are not arbitrary original instruction-prefix or cycle equivalence; matched event-limit and mapping-fault prefixes are separate evidence.',
            'Diagnostic records in upper RAM are supplied runtime state outside the initialized application; this evidence does not identify a physical nonvolatile storage device or guarantee retention.',
            'The initialized lock word is auxiliary mutable evidence. No immutable table or data exclusion is added.'],
        'hardware_test':False,'device_access':False,'audio_test':False,'firmware_changed':False}
    if a.part=='all':
        if gaps:raise ValueError('fault full corpus missed a complete-body instruction')
        report['invalid_api_checks']=guard_checks(c)
    if a.mini_image:
        raw=a.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=MINI:raise ValueError('reviewed MINI image changed')
        mini=unpack_app(raw)[2]['app.bin']
        for s,e in [*(REGIONS|REUSED).values(),INITIAL_LOCK[:2],INCOMING[:2]]:
            if region_bytes(app,s,e)!=region_bytes(mini,s,e):raise ValueError('MINI fault bytes differ')
        report['mini_binding']={'sha256':MINI,'complete_regions':17,'instructions':332,'auxiliary_mutable_bytes':4,'incoming_call_bytes':4}
    if a.fixtures:write_fixtures(a.fixtures,c.records)
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    if report['source_sha256']!=before or hashlib.sha256(a.library.read_bytes()).hexdigest()!=library_hash:
        raise ValueError('fault source/library bytes changed during comparison')
    report['library_sha256']=library_hash
    if a.output:a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'comparisons':len(c.records),'steps':c.steps,'visited':len(c.visited),'new_visited':len(c.visited&new),
        'gaps':list(map(hex,gaps)),'portable_failure_cases':report['portable_failure_cases'],'fatal_observations':report['fatal_observations']}))
if __name__=='__main__':main()
