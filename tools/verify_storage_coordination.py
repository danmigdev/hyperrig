"""Compare coordination CPU observations and shared state to original instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from storage_coordination_machine import (StorageCoordinationProgram,REGIONS,REUSED,ARITIES,MAPPED,GLOBAL,STATE,
 IRQ_COUNTS,RECORDS,ROOT,BARRIER,CLI,STI,CNUM,TESTSET,CLOCK,YIELD,POLL,SERVICES,INITIAL_COUNTERS,region_bytes,
 ISA_RECORD_SHA256)
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app
U32,U64=ctypes.c_uint32,ctypes.c_uint64
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
EVENT=ctypes.CFUNCTYPE(U64,ctypes.c_void_p,U32,U32,U32,U64,ctypes.POINTER(Borrowed))
class CPU(ctypes.Structure):_fields_=[('cnum',U32),('icfg',U32)]
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('event',EVENT),('opaque',ctypes.c_void_p),('services',U32),('events',U32),('work',U32)]
SOURCES=tuple('firmware/src/hyperrig_'+s+'.c' for s in ('storage_coordination','controls','control_actions','selection','preset_storage','preset_preflight','preset_loader'))
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'

def setword(memory,a,v,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:data[a-base:a-base+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little');return
    raise ValueError(f'fixture write {a:#x}/{n}')
def getword(memory,a,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:return int.from_bytes(data[a-base:a-base+n],'little')
    raise ValueError(f'fixture read {a:#x}/{n}')
def initial():
    m=[bytearray(n) for _,n in MAPPED];setword(m,GLOBAL+44,6);setword(m,GLOBAL+24,0x12345678)
    for i in range(2048):setword(m,RECORDS+i,(i*29+7)&255,1)
    return m

class Script:
    def __init__(self,returns=None,mutations=(),event_return=0):
        self.returns=returns or {};self.mutations=mutations;self.event_return=event_return;self.seen={};self.actions=[]
    def mutate(self,key,m):
        occurrence=self.seen.get(key,0);self.seen[key]=occurrence+1;writes=[]
        for at,which,a,v,n in self.mutations:
            if at==key and (which<0 or occurrence==which):m.write(a,v,n);writes.append((a,n,v))
        return occurrence,writes
    def call(self,target,args,m):
        occurrence,writes=self.mutate(('call',target),m);value=self.returns.get(target)
        if isinstance(value,(list,tuple)):value=value[min(occurrence,len(value)-1)]
        if value is None:value=100000+occurrence*997 if target==CLOCK else 0
        value&=0xffffffff;self.actions.append((0,target,SERVICES[target],0,value,args,writes));return value
    def event(self,op,a,n,v,m):
        _,writes=self.mutate((op,a),m);self.actions.append((op,a,n,v,self.event_return,(0,)*12,writes));return self.event_return

class Backend:
    def __init__(self,memory,cpu,script,alignment=0,services=10000,events=10000):
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory];self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment);array[:]=data;self.arrays.append(array)
        self.cpu=CPU(*cpu);self.script=script;self.calls=[];self.events=[];self.timeline=[];self.errors=[];self.borrowed=None
        self.io=IO(MAP(self.map),CALL(self.call),EVENT(self.event),None,services,events,4000000)
    def map(self,opaque,a,n,writable):
        for (base,size),array in zip(MAPPED,self.arrays):
            if base<=a<=a+n<=base+size:return ctypes.addressof(array)+a-base
        return None
    def read(self,a,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,0) if self.borrowed else self.map(None,a,n,0)
        if p is None:raise ValueError('callback read outside domain')
        return int.from_bytes(ctypes.string_at(p,n),'little')
    def write(self,a,v,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,1) if self.borrowed else self.map(None,a,n,1)
        if p is None:raise ValueError('callback write outside domain')
        ctypes.memmove(p,(v&((1<<(8*n))-1)).to_bytes(n,'little'),n)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def cpu_words(self):return self.cpu.cnum,self.cpu.icfg
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())+struct.pack('<II',*self.cpu_words())).hexdigest()
    def call(self,opaque,target,args,count,borrowed):
        try:
            words=tuple(args[i] for i in range(count))+(0,)*(12-count);before=self.digest();self.borrowed=borrowed.contents
            value=self.script.call(target,words,self);self.borrowed=None
            self.calls.append((target,words,before,self.digest(),value));self.timeline.append(('call',len(self.calls)-1));return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0
    def event(self,opaque,op,a,n,v,borrowed):
        try:
            before=self.digest();self.borrowed=borrowed.contents;value=self.script.event(op,a,n,v,self);self.borrowed=None
            self.events.append((op,a,n,v,before,self.digest()));self.timeline.append(('event',len(self.events)-1));return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library):
        self.program=StorageCoordinationProgram();self.library=ctypes.CDLL(str(Path(library).resolve()))
        self.execute=self.library.hyperrig_storage_coordination_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(CPU),ctypes.POINTER(IO)]
        self.visited=set();self.steps=0;self.records=[];self.counts={};self.digest=hashlib.sha256()
    def compare(self,label,memory,name,args=(),cpu=(0,0x01090700),alignment=0,services=10000,events=10000,**script_args):
        first=Script(**script_args)
        try:r=self.program.execute(memory,name,args,cpu,first.call,first.event,services,events)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        second=Script(**script_args);b=Backend(memory,cpu,second,alignment,services,events);out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=self.execute(REGIONS[name][0],(U32*12)(*args),out,ctypes.byref(b.cpu),ctypes.byref(b.io))
        if status!=r['status'] or b.errors:raise AssertionError((label,'status',status,r['status'],b.errors[:3]))
        expected=(0xdeadbeef,0xcafebabe) if status else r['result']
        if tuple(out)!=expected:raise AssertionError((label,'result',tuple(out),expected))
        for key,actual in (('calls',b.calls),('events',b.events),('timeline',b.timeline)):
            if actual!=r[key]:
                mismatch=next(((i,a,z) for i,(a,z) in enumerate(zip(actual,r[key])) if a!=z),None)
                raise AssertionError((label,key,len(actual),len(r[key]),mismatch))
        if b.cpu_words()!=r['cpu']:raise AssertionError((label,'CPU state',b.cpu_words(),r['cpu']))
        if b.snapshot()!=r['memory']:
            diff=[(hex(base+i),a,z) for (base,_),aa,zz in zip(MAPPED,b.snapshot(),r['memory']) for i,(a,z) in enumerate(zip(aa,zz)) if a!=z]
            raise AssertionError((label,'RAM',diff[:20]))
        if first.actions!=second.actions:raise AssertionError((label,'external event effects'))
        self.visited|=r['visited'];self.steps+=r['steps'];self.counts[name]=self.counts.get(name,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<i4I',status,*out,*r['cpu']))
        for data in r['memory']:self.digest.update(data)
        self.records.append((label,tuple(map(bytes,memory)),name,args,cpu,status,tuple(out),r['cpu'],r['memory'],first.actions,services,events))
        return r

def scalar_cases(c):
    for threshold in (0,1,149,150,151,0x7fffffff,0xffffffff):
        for current,start in ((0,0),(113,0),(114,0),(0,1),(0xffffffff,0),(0xffffffff,0xffffff00),(0x1000000,7)):
            m=initial();setword(m,STATE+4076,current);setword(m,STATE+404,start)
            c.compare(f'threshold/{threshold}/{current}/{start}',m,'ready_threshold',(threshold,))
    for current in (0,112,113,114,0xffffffff):
        m=initial();setword(m,STATE+4076,current);c.compare(f'wait/{current}',m,'wait_ready')
    c.compare('poll forwarding',initial(),'poll_forward')
    for cnum in (0,1,2,0xffffffff,0x40000000):
        for old in (0,1,2,0xffffffff):
            for icfg in (0,0x200,0x01090700,0xffffffff):
                m=initial();at=(IRQ_COUNTS+(cnum<<2))&0xffffffff;setword(m,at,old)
                for name in ('irq_enter','irq_leave'):
                    c.compare(f'IRQ/{name}/{cnum}/{old}/{icfg}',m,name,cpu=(cnum,icfg))

def notification_cases(c):
    for sequence in (0,1,126,127,128,0xffffffff):
        for kind in (0,24,0xffff,0x10000,0xffffffff):
            m=initial();setword(m,STATE+1196,sequence);setword(m,GLOBAL+24,0xffffffff)
            c.compare(f'notify/{sequence}/{kind}',m,'notify',(kind,0x12345678,0x87654321),alignment=kind%4)
    for byte in (*range(16),0x74,0x80,0xff):
        m=initial();setword(m,STATE+55,byte,1)
        c.compare(f'testset byte/{byte}',m,'notify',(0x5555,1,2),
            mutations=(((TESTSET,STATE+55),0,STATE+55,0,1),))
    for calibration in (0,1,5,6,288,0x20000000,0xffffffff):
        for kind,address,stamp in ((0,0,0),(1,0xbf000,99999),(255,0xffffffff,0xffffffff),(256,0x12345678,0)):
            m=initial();setword(m,GLOBAL+44,calibration)
            c.compare(f'event/{calibration}/{kind}/{address}',m,'event',(kind,address,stamp))
    for at in (STATE+1196,RECORDS+16,RECORDS+20,RECORDS+24,RECORDS+28,STATE+336,STATE+52,GLOBAL+24,0,0xfffffffc):
        cnum=((at-IRQ_COUNTS)&0xffffffff)>>2;m=initial()
        c.compare(f'IRQ counter alias/{at}',m,'notify',(7,5,9),cpu=(cnum,0x300))

def gate_cases(c):
    for depth in (0,1,2,254,255):
        for enter in (0,1,2,0xffffffff):
            for mode in (0,1,2):
                m=initial();setword(m,STATE+37,depth,1);setword(m,STATE+280,mode);setword(m,STATE+29,1,1)
                c.compare(f'gate depth/{depth}/{enter}/{mode}',m,'gate_core',(enter,1))
    for final_wait in (0,1,0xffffffff):
        for ack in (0,1,255):
            m=initial();setword(m,STATE+280,2);setword(m,STATE+29,1,1);setword(m,STATE+36,ack,1)
            c.compare(f'gate acknowledgement/{final_wait}/{ack}',m,'gate_core',(1,final_wait))
    for calibration in (0,1,6,288,0x20000000,0xffffffff):
        m=initial();setword(m,GLOBAL+44,calibration);setword(m,STATE+280,2);setword(m,STATE+29,1,1)
        c.compare(f'gate rate/{calibration}',m,'gate',(1,),services=40)
    for fault in ('none','same','mode','ready','global2','global3','busy'):
        m=initial();setword(m,STATE+37,1,1);setword(m,STATE+336,7);setword(m,STATE+664,3)
        setword(m,STATE+280,2);setword(m,STATE+29,1,1);setword(m,GLOBAL+2,1,1);setword(m,GLOBAL+3,1,1)
        if fault=='same':setword(m,STATE+336,3)
        if fault=='mode':setword(m,STATE+280,1)
        if fault=='ready':setword(m,STATE+29,0,1)
        if fault=='global2':setword(m,GLOBAL+2,0,1)
        if fault=='global3':setword(m,GLOBAL+3,0,1)
        if fault=='busy':setword(m,STATE+328,1)
        c.compare(f'gate release condition/{fault}',m,'gate_core',(0,1))

def mutation_cases(c):
    for occurrence in (0,1,2,28,29):
        c.compare(f'wait mutation/{occurrence}',initial(),'wait_ready',
            mutations=((('call',YIELD),occurrence,STATE+4076,200,4),(('call',YIELD),occurrence,GLOBAL+24,19,4)))
    for target,occurrence in ((CLOCK,0),(CLOCK,1),(POLL,0),(YIELD,0),(YIELD,3)):
        m=initial();setword(m,STATE+280,2);setword(m,STATE+29,1,1)
        c.compare(f'gate callback/{target}/{occurrence}',m,'gate_core',(1,1),
            mutations=((('call',target),occurrence,STATE+36,1,1),))
    for target in (POLL,YIELD):
        m=initial();setword(m,STATE+280,2);setword(m,STATE+29,1,1)
        c.compare(f'gate desired-byte callback/{target}',m,'gate_core',(1,1),
            mutations=((('call',target),0,STATE+34,0,1),))
    m=initial();setword(m,STATE+280,2);setword(m,STATE+29,1,1)
    c.compare('gate clock mutates calibration',m,'gate_core',(1,1),mutations=((('call',CLOCK),0,GLOBAL+44,0,4),))
    for delta in (0,1,2,3,0xffffffff):
        m=initial();setword(m,STATE+37,1,1);setword(m,STATE+336,7);setword(m,STATE+664,3)
        setword(m,STATE+280,2);setword(m,STATE+29,1,1);setword(m,GLOBAL+2,1,1);setword(m,GLOBAL+3,1,1)
        setword(m,STATE+4084,0xffffffff)
        c.compare(f'release counter mutation/{delta}',m,'gate',(0,),
            mutations=((('call',POLL),0,STATE+4084,(0xffffffff+delta)&0xffffffff,4),))
    for op,which,a,v,n in ((CLI,0,GLOBAL+24,0x55555555,4),(CNUM,0,IRQ_COUNTS,127,4),
        (TESTSET,0,STATE+1196,127,4),(BARRIER,3,IRQ_COUNTS,3,4),(STI,0,STATE+55,0x74,1)):
        address=STATE+55 if op==TESTSET else 0
        c.compare(f'notification callback/{op}',initial(),'notify',(0x12345678,0xaabbccdd,0x88776655),
            mutations=(((op,address),which,a,v,n),))
    c.compare('CPU event return ignored',initial(),'notify',(3,5,7),event_return=0xfedcba9876543210)
    for budget in range(16):
        c.compare(f'CPU event prefix/{budget}',initial(),'notify',(3,4,5),events=budget)
    for budget in (0,1,2,3,7,19):
        m=initial();setword(m,STATE+55,0xff,1)
        c.compare(f'held lock prefix/{budget}',m,'notify',(1,2,3),events=budget)
        setword(m,STATE+280,2);setword(m,STATE+29,1,1)
        c.compare(f'gate service prefix/{budget}',m,'gate',(1,),services=budget,returns={CLOCK:123})
    m=initial();cpu=(1,0);setword(m,STATE+280,2);setword(m,STATE+29,1,1)
    for i,(name,args) in enumerate((('gate',(1,)),('notify',(4,5,6)),('gate',(1,)),('event',(2,0xbf000,17)),('gate',(0,)),('gate',(0,)))):
        result=c.compare(f'carried coordination/{i}',m,name,args,cpu=cpu);m=result['memory'];cpu=result['cpu']

def source_paths():
    names=set(SOURCES)|{'tools/storage_coordination_machine.py','tools/verify_storage_coordination.py',
        'tools/build_storage_coordination.py','tests/test_storage_coordination_machine.py','tests/storage_coordination_sanitize.c',
        'research/input-manifest.json','analysis/firmware/m571_g_app/memory-layout.json','third_party/ultrarig/LICENSE.md'}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    for directory in ('upstream/pi32v2-isa/isa','upstream/pi32v2-isa/tools/hwtest/semantics'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.suffix in ('.py','.toml'))
    pending=list(SOURCES)+['tests/storage_coordination_sanitize.c']
    while pending:
        name=pending.pop()
        for include in re.findall(r'^#include\s+"([^"]+)"',(ROOT/name).read_text(),re.M):
            candidates=((ROOT/name).parent/include,ROOT/'firmware/include'/include)
            match=next((p.resolve() for p in candidates if p.is_file()),None)
            if match is None:raise ValueError('unresolved coordination C include')
            child=match.relative_to(ROOT).as_posix()
            if child not in names:names.add(child);pending.append(child)
    return sorted(names)


def guard_checks(c):
    checks=[]
    def run(label,name,args=(),expected=-200,work=10000,services=100,events=100,setup=None,script=None,cpu=(0,0x01090700)):
        b=Backend(initial(),cpu,script or Script(),services=services,events=events);b.io.work=work
        if setup:setup(b)
        out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=c.execute(REGIONS[name][0] if isinstance(name,str) else name,(U32*12)(*args),out,ctypes.byref(b.cpu),ctypes.byref(b.io))
        if status!=expected or b.errors or (status and tuple(out)!=(0xdeadbeef,0xcafebabe)):
            raise AssertionError((label,status,tuple(out),b.errors))
        checks.append({'label':label,'status':status,'result_untouched':bool(status)})
        return b
    for missing in ('arguments','result','cpu','io','map','call','event'):
        b=Backend(initial(),(0,0),Script());argv=(U32*12)();out=(U32*2)(0xdeadbeef,0xcafebabe)
        if missing=='map':b.io.map=MAP()
        if missing=='call':b.io.call=CALL()
        if missing=='event':b.io.event=EVENT()
        status=c.execute(REGIONS['notify'][0],None if missing=='arguments' else argv,None if missing=='result' else out,
            None if missing=='cpu' else ctypes.byref(b.cpu),None if missing=='io' else ctypes.byref(b.io))
        if status!=-200:raise AssertionError((missing,status))
        checks.append({'label':'null '+missing,'status':status})
    run('unknown complete entry',0x020028f4)
    run('zero work','ready_threshold',(1,),expected=-203,work=0)
    run('zero platform budget','poll_forward',expected=-203,services=0)
    run('zero CPU event budget','irq_enter',expected=-203,events=0)
    for work in (1,2,5,9,20):run(f'finite work/{work}','notify',(1,2,3),expected=-203,work=work)
    run('unmapped core counter','irq_enter',expected=-201,cpu=(0x12345678,0x200))
    run('private core counter','irq_enter',expected=-202,cpu=(((0x30000000-IRQ_COUNTS)&0xffffffff)>>2,0x200))
    def deny(b):b.io.map=MAP(lambda *args:None)
    run('missing state','ready_threshold',(0,),expected=-201,setup=deny)
    class BadBorrow(Script):
        def __init__(self,address,size,event):super().__init__();self.address=address;self.size=size;self.on_event=event;self.denied=0
        def check(self,m):
            if m.borrowed.map(m.borrowed.opaque,self.address,self.size,1) is not None:raise AssertionError('forbidden borrowed view accepted')
            self.denied+=1
        def call(self,t,args,m):
            if not self.on_event:self.check(m)
            return 0
        def event(self,op,a,n,v,m):
            if self.on_event:self.check(m)
            return 0
    rejected=((0x30000000,1,-202),(0x3000103f,1,-202),(0x2fffffff,2,-202),
        (0xffffffff,2,-201),(0x40000000,1,-201),(0x01c344b3,2,-201))
    rejected+=tuple((start,1,-201) for start,_ in (REGIONS|REUSED).values())
    for address,size,expected in rejected:
        for event in (False,True):
            script=BadBorrow(address,size,event)
            b=run(f'borrowed domain/{address}/{size}/{event}','irq_enter' if event else 'poll_forward',expected=expected,script=script)
            if script.denied!=1:raise AssertionError('borrowed domain witness did not execute once')
            if event and b.cpu.icfg!=0x01090500:raise AssertionError('CLI effect before borrowed guard was lost')
    return checks


def write_fixtures(path,records):
    def words(f,*v):f.write(struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
    with path.open('wb') as f:
        words(f,0x314f4353,len(records),len(MAPPED))
        for base,size in MAPPED:words(f,base,size)
        for label,before,name,args,cpu,status,result,final_cpu,after,actions,services,events in records:
            raw=label.encode();words(f,len(raw));f.write(raw)
            words(f,REGIONS[name][0],*(tuple(args)+(0,)*(12-len(args))),*cpu,status,*result,*final_cpu,services,events,len(actions))
            for data in before:f.write(data)
            for op,address,width,value,ret,argv,writes in actions:
                words(f,op,address,width);f.write(struct.pack('<QQ',value,ret));words(f,*argv,len(writes))
                for a,n,v in writes:words(f,a,n);f.write((v&((1<<(8*n))-1)).to_bytes(n,'little'))
            for data in after:f.write(data)


def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path)
    p.add_argument('--part',default='all',choices=('all','scalar','notify','gate','mutation'))
    a=p.parse_args();c=Corpus(a.library)
    before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    library_before=hashlib.sha256(a.library.read_bytes()).hexdigest()
    original=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    packed=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    if hashlib.sha256(original).hexdigest()!=DECODED or hashlib.sha256(packed).hexdigest()!=PINNED:
        raise ValueError('coordination original image binding differs')
    if unpack_app(packed)[2]['app.bin']!=original:raise ValueError('decoded original image differs from packed image')
    for n,run in (('scalar',scalar_cases),('notify',notification_cases),('gate',gate_cases),('mutation',mutation_cases)):
        if a.part in ('all',n):run(c);print(n,len(c.records),len(c.visited),flush=True)
    new={pc for pc in c.program.code if any(s<=pc<e for s,e in REGIONS.values())}
    gaps=sorted(set(c.program.code)-c.visited)
    regions={n:{'start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'bytes_sha256':hashlib.sha256(c.program.regions[n]).hexdigest(),
        'instructions':sum(s<=pc<e for pc in c.program.code)} for n,(s,e) in (REGIONS|REUSED).items()}
    report={'result':'pass','component':'storage-coordination','original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
      'comparisons':len(c.records),'counts':c.counts,'steps':c.steps,'visited':[hex(x) for x in sorted(c.visited)],'digest':c.digest.hexdigest(),
      'functions':{n:regions[n] for n in REGIONS},'reused_functions':{n:regions[n] for n in REUSED},
      'instruction_coverage':{'new_decoded':len(new),'new_visited':len(c.visited&new),'unvisited_new':[hex(x) for x in gaps if x in new],
        'all_decoded':len(c.program.code),'all_visited':len(c.visited),'unvisited_all':[hex(x) for x in gaps]},
      'gap_instructions':{hex(x):c.program.code[x][0] for x in gaps},'new_data_exclusions':[],
      'service_sites':{hex(pc):{'target':hex(t),'arity':n} for pc,(t,n) in c.program.service_sites.items()},
      'cpu_primary_evidence':{'records':c.program.isa_records,'canonical_record_sha256':ISA_RECORD_SHA256,
         'semantics':'TESTSET replaces one byte with FF; old low four bits supply flags and bit2 controls the native backedge. CLI/STI clear/set ICFG bit9, preserving other bits. CNUM is a supplied retained context word.'},
      'auxiliary_initial_state':{'start':hex(INITIAL_COUNTERS[0]),'end_exclusive':hex(INITIAL_COUNTERS[1]),'sha256':INITIAL_COUNTERS[2],
         'bytes':8,'meaning':'two initially zero RAM IRQ nesting words; mutable runtime state, not immutable table or BSS reset execution'},
      'bounded_event_and_service_prefix_cases':sum('prefix/' in r[0] for r in c.records),
      'limitations':[
        'Offline instruction/C comparisons do not prove atomicity, IRQ delivery, scheduler progress, real-time behavior or inter-core memory ordering.',
        'CLOCK, YIELD and scheduler polling remain explicit synchronous platform services at nine authenticated direct call sites.',
        'CPU events permit public-RAM mutations after the reported instruction effect. CPU, IO and API storage must remain disjoint and cannot be mutated by callbacks.',
        'CNUM accepts arbitrary uint32 values only where its wrapped native counter address resolves to mapped RAM; physical core identities are not inferred.',
        'Finite event/service guards compare exact observed prefixes and are not native returns. Portable work guards do not claim exact original instruction-prefix equivalence.',
        'No storage-control/preparation integration or private-buffer lease is claimed in this standalone coordination module.'],
      'device_access':False,'hardware_test':False,'audio_test':False,'firmware_changed':False}
    if a.part=='all':
        if gaps:raise ValueError(f'unclassified coordination instruction gaps {gaps}')
        report['invalid_api_checks']=guard_checks(c)
    if a.mini_image:
        raw=a.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=MINI:raise ValueError('MINI reviewed whole-image hash differs')
        body=unpack_app(raw)[2]['app.bin']
        for s,e in (REGIONS|REUSED).values():
            if region_bytes(body,s,e)!=region_bytes(original,s,e):raise ValueError('MINI coordination body differs')
        if region_bytes(body,*INITIAL_COUNTERS[:2])!=c.program.initial_counters:raise ValueError('MINI initial IRQ state differs')
        report['mini_binding']={'sha256':MINI,'regions':len(REGIONS)+len(REUSED),'instructions':len(c.program.code),
            'immutable_data_bytes':0,'auxiliary_mutable_initial_state_bytes':8}
    if a.fixtures:write_fixtures(a.fixtures,c.records)
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    if report['source_sha256']!=before:raise ValueError('source bytes/set changed during coordination verification')
    if hashlib.sha256(a.library.read_bytes()).hexdigest()!=library_before:raise ValueError('host library changed during verification')
    report['library_sha256']=library_before
    if a.output:a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'result':report['result'],'comparisons':len(c.records),'steps':c.steps,
        'new_visited':len(c.visited&new),'new_decoded':len(new),'all_visited':len(c.visited),'all_decoded':len(c.program.code),'gaps':report['gap_instructions']}))
if __name__=='__main__':main()
