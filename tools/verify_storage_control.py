"""Compare storage control against original instructions and explicit event streams."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from storage_control_machine import (StorageControlProgram,REGIONS,STATIC,TABLES,BSS_WITNESS,
 ARITIES,VOID,SERVICES,MAPPED,STATE,GLOBAL,DEVICE,ARENA,MMIO,ROOT,READ,WRITE,BARRIER,FLUSH,region_bytes)
U32,U64=ctypes.c_uint32,ctypes.c_uint64
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
EVENT=ctypes.CFUNCTYPE(U64,ctypes.c_void_p,U32,U32,U32,U64,ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('event',EVENT),('opaque',ctypes.c_void_p),
              ('services',U32),('events',U32),('work',U32)]
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
SOURCES=('firmware/src/hyperrig_storage_control.c',)
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app

def setword(memory,a,v,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:data[a-base:a-base+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little');return
    raise ValueError(f'fixture write {a:#x}/{n}')
def getword(memory,a,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:return int.from_bytes(data[a-base:a-base+n],'little')
    raise ValueError(f'fixture read {a:#x}/{n}')
def initial(mode=0):
    m=[bytearray(size) for _,size in MAPPED]
    m[2][:]=bytes((i*37+11)&255 for i in range(len(m[2])))
    setword(m,DEVICE+16,1,1);setword(m,DEVICE+24,0x100000);setword(m,DEVICE+28,0x123416)
    setword(m,DEVICE+56,mode<<8);setword(m,DEVICE+64,0x1029);setword(m,0x01c24228,1,1)
    setword(m,DEVICE+52,0x10000000)
    return m

class Script:
    """Deterministic external services; register reads do not assert hardware behavior."""
    def __init__(self,registers=None,reads=None,returns=None,mutations=()):
        self.registers={};self.reads=reads or {};self.returns=returns or {};self.mutations=mutations;self.seen={};self.actions=[]
        for a,v in ({0x11c00:0x1029,0x40200:0,0x01eee008:0x4000}|(registers or {})).items():
            for i,b in enumerate((v&0xffffffff).to_bytes(4,'little')):self.registers[a+i]=b
    def count(self,key):
        i=self.seen.get(key,0);self.seen[key]=i+1;return i
    @staticmethod
    def pick(value,index,default):
        if value is None:return default
        return value[min(index,len(value)-1)] if isinstance(value,(list,tuple)) else value
    def mutate(self,key,index,m):
        writes=[]
        for at,which,a,v,n in self.mutations:
            if at==key and (which<0 or which==index):m.write(a,v,n);writes.append((a,n,v))
        return writes
    def call(self,target,args,m):
        key=('call',target);i=self.count(key)
        value=self.pick(self.returns.get(target),i,100000+i*997 if target==0x01c04862 else 0)
        writes=self.mutate(key,i,m);value&=0xffffffff
        self.actions.append((0,target,SERVICES[target],0,value,args,writes));return value
    def event(self,op,a,n,v,m):
        key=(op,a);i=self.count(key);result=0
        if op==READ:
            default=sum(self.registers.get(a+j,0)<<(8*j) for j in range(n))
            if a==0x11c00:default|=0x8000
            if a==0x11c08:default=0
            result=self.pick(self.reads.get(a),i,default)
        elif op==WRITE:
            for j,b in enumerate(v.to_bytes(n,'little')):self.registers[a+j]=b
        writes=self.mutate(key,i,m);self.actions.append((op,a,n,v,result,(0,)*12,writes));return result

class Backend:
    def __init__(self,memory,script,alignment=0,event_budget=1000000):
        self.allocations=[(ctypes.c_ubyte*(len(data)+alignment))() for data in memory];self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment);array[:]=data;self.arrays.append(array)
        self.script=script;self.calls=[];self.events=[];self.errors=[];self.borrowed=None;self.timeline=[]
        self.io=IO(MAP(self.map),CALL(self.call),EVENT(self.event),None,10000,event_budget,8000000)
    def map(self,opaque,a,n,writable):
        for (base,size),array in zip(MAPPED,self.arrays):
            if base<=a<=a+n<=base+size:return ctypes.addressof(array)+a-base
        return None
    def read(self,a,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,0) if self.borrowed else self.map(None,a,n,0)
        if p is None:raise ValueError(f'callback read {a:#x}/{n}')
        return int.from_bytes(ctypes.string_at(p,n),'little')
    def write(self,a,v,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,1) if self.borrowed else self.map(None,a,n,1)
        if p is None:raise ValueError(f'callback write {a:#x}/{n}')
        ctypes.memmove(p,(v&((1<<(n*8))-1)).to_bytes(n,'little'),n)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())).hexdigest()
    def call(self,opaque,target,args,count,borrowed):
        try:
            words=tuple(args[i] for i in range(count))+(0,)*(12-count);before=self.digest();self.borrowed=borrowed.contents
            result=self.script.call(target,words,self);self.borrowed=None
            self.calls.append((target,words,before,self.digest(),result));self.timeline.append(('call',len(self.calls)-1));return result
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0
    def event(self,opaque,op,a,n,v,borrowed):
        try:
            before=self.digest();self.borrowed=borrowed.contents;result=self.script.event(op,a,n,v,self);self.borrowed=None
            self.events.append((op,a,n,v,result,before,self.digest()));self.timeline.append(('event',len(self.events)-1));return result
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library):
        self.program=StorageControlProgram();self.library=ctypes.CDLL(str(Path(library).resolve()))
        self.execute=self.library.hyperrig_storage_control_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.visited=set();self.steps=0;self.counts={};self.records=[];self.digest=hashlib.sha256()
    def compare(self,label,memory,name,args=(),alignment=0,event_budget=1000000,**script_args):
        first=Script(**script_args)
        try:original=self.program.execute(memory,name,args,first.call,first.event,event_budget)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        second=Script(**script_args);b=Backend(memory,second,alignment,event_budget)
        out=(U32*2)(0xdeadbeef,0xcafebabe);status=self.execute(REGIONS[name][0],(U32*12)(*args),out,ctypes.byref(b.io))
        if status!=original['status'] or b.errors:raise AssertionError((label,'status',status,original['status'],b.errors[:3]))
        expected=(0xdeadbeef,0xcafebabe) if status else original['result']
        if tuple(out)!=expected:raise AssertionError((label,'result',tuple(out),expected))
        for key,actual in (('calls',b.calls),('events',b.events),('timeline',b.timeline)):
            wanted=original[key]
            if actual!=wanted:
                mismatch=next(((i,a,w) for i,(a,w) in enumerate(zip(actual,wanted)) if a!=w),None)
                raise AssertionError((label,key,len(actual),len(wanted),mismatch))
        if b.snapshot()!=original['memory']:
            changes=[(hex(base+i),a,z) for (base,_),aa,zz in zip(MAPPED,b.snapshot(),original['memory']) for i,(a,z) in enumerate(zip(aa,zz)) if a!=z]
            raise AssertionError((label,'memory',changes[:30]))
        if first.registers!=second.registers:raise AssertionError((label,'MMIO retained register state'))
        self.visited|=original['visited'];self.steps+=original['steps'];self.counts[name]=self.counts.get(name,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<i2I',status,*out))
        for data in original['memory']:self.digest.update(data)
        self.records.append((label,tuple(map(bytes,memory)),name,args,status,tuple(out),original['memory'],original['calls'],original['events'],original['timeline'],first.actions,event_budget))
        original['register_words']={base+i:sum(first.registers.get(base+i+j,0)<<(8*j) for j in range(4))
            for base,size in MMIO for i in range(0,size,4)}
        return original

def smoke_cases(c):
    arguments=dict(power2=(4,),activity=(1,),raw_read=(ARENA,0xbf000,3),read=(0xbf000,ARENA,3),
      range=(0xbf000,0x40000),reject=(17,),control=(101,ARENA),ioctl=(0,101,ARENA),
      program_pages=(ARENA,3,0xbf001),program=(0,ARENA,3,0xbf001),delay=(3,),chip_select=(1,),
      send_byte=(0x83,),send_address=(0x12345678,),receive_buffer=(ARENA,3),send_fast=(0x83,),send_buffer=(ARENA,3),
      transfer_read=(ARENA,0xbf000,3,0),bus_leave=(0,),bank_enter=(0x1000000,),bank_leave=(0x1000000,),
      device_read=(ARENA,0xbf000,3),translate=(0xbf000,),cache_forward=(0xbf000,31),device_erase=(204,0xbf000),
      status_write=(0,),status_apply=(0x10000,),cache_region=(0xbf000,31),device_program=(ARENA,0xbf000,3),cache_lines=(0xbf000,31))
    for name in REGIONS:
        c.compare('smoke/'+name,initial(),name,arguments.get(name,()))

def scalar_cases(c):
    for exponent in (0,1,2,15,16,31,32,33,63,255,0x80000000,0xffffffff):
        c.compare(f'power/{exponent}',initial(),'power2',(exponent,))
    for address in (0,0xbefff,0xbf000,0xfefff,0xff000,0xff001,0xffffff00,0xffffffff):
        for n in (0,1,256,0x40000,0x40001,0xffffffff):
            c.compare(f'range/{address}/{n}',initial(),'range',(address,n))
    for depth in (0,1,3,4,255):
        for value in (0,1,255,256,0xffffffff):
            m=initial();setword(m,STATE+22,depth,1)
            for i in range(255):setword(m,STATE+392+i,i,1);setword(m,STATE+1732+4*i,100+i)
            c.compare(f'activity/{depth}/{value}',m,'activity',(value,))
    for gate,left,right in ((0,1,2),(1,1,2),(1,2,2),(0xffffffff,0xffffffff,0)):
        m=initial();setword(m,STATE+280,gate);setword(m,STATE+380,left);setword(m,STATE+384,right)
        c.compare(f'poll/{gate}/{left}/{right}',m,'poll')
    for address,origin,mapped in ((0,0,0),(0xffffffff,1,0),(0,1,0xffffffff),(0x12345678,0x87654321,0x76543210)):
        m=initial();setword(m,DEVICE+48,origin);setword(m,DEVICE+52,mapped)
        c.compare(f'translate/{address}/{origin}/{mapped}',m,'translate',(address,))
    for n in (0,1,9,31,32,33,63,64,65,0x7fffffe1,0x80000000,0xffffffe0,0xffffffff):
        c.compare(f'cache/{n}',initial(),'cache_lines',(0xfffffff1,n),event_budget=31)
    for ready,capacity in ((0,0),(0,0x100000),(1,0),(255,0x100000)):
        m=initial();setword(m,DEVICE+16,ready,1);setword(m,DEVICE+24,capacity)
        c.compare(f'initialize/{ready}/{capacity}',m,'initialize')
        setword(m,0x01c24228,0,1);c.compare(f'ensure/{ready}/{capacity}',m,'ensure')

def mode_cases(c):
    for mode in range(16):
        for name,args in (('leave_continuous',()),('transfer_read',(ARENA,0x12345678,3,0)),
                         ('receive_buffer',(ARENA+1,3)),('send_buffer',(ARENA+1,3))):
            c.compare(f'mode/{mode}/{name}',initial(mode),name,args,alignment=mode%4,registers={0x40200:mode<<8})
        if mode in (6,7):
            c.compare(f'command mode/{mode}',initial(mode),'transfer_read',(ARENA,0x1000001,5,1),reads={0x11c08:[17,34,51,68,85,102,119]})
    for name in ('receive_buffer','send_buffer','transfer_read'):
        for n in (0,1,2,4,31,256,0x10000,0x10001,0xffff0002):
            args=(ARENA,0xbf000,n,0) if name=='transfer_read' else (ARENA,n)
            c.compare(f'buffer count/{name}/{n}',initial(5),name,args,registers={0x40200:0x500})
    for cap in (0,0x1000000,0x1000001,0xffffffff):
        for address in (0xffffff,0x1000000,0xffffffff):
            for flag in (0,1):
                m=initial();setword(m,DEVICE+24,cap);setword(m,DEVICE+80,flag,1)
                for name in ('bank_enter','bank_leave'):c.compare(f'bank/{name}/{cap}/{address}/{flag}',m,name,(address,))
    for ext in (0,1):
        m=initial();setword(m,DEVICE+80,ext,1);c.compare(f'address/{ext}',m,'send_address',(0x89abcdef,))
    for flag in (0,1,255):
        m=initial(6);setword(m,DEVICE+17,flag,1);setword(m,STATE+67,255,1)
        entered=c.compare(f'bus enter/{flag}',m,'bus_enter',registers={0x40200:0x600})
        c.compare(f'bus leave/{flag}',entered['memory'],'bus_leave',(0x123,),registers={0x40200:0})
    for name,args in (('identify',()),('status_capture',()),('device_read',(ARENA,0xfffffe,5)),
                      ('device_program',(ARENA,0xfffffe,5)),('device_erase',(204,0x1000000))):
        m=initial(6);setword(m,DEVICE+24,0x2000000)
        c.compare(f'continuous/{name}',m,name,args,registers={0x40200:0x600})

def control_cases(c):
    for command in (0,10,11,12,13,47,48,99,100,101,102,103,104,199,200,201,202,203,204,205,206,207,401,402,403,404,0xffffffff):
        m=initial();argument=0xbf000 if command in (200,201,202,203,204,403,404) else ARENA
        if command==13:argument=0
        if command==205:
            for i,v in enumerate((0,0xbf000,16,17,0xbf000,0x10000000,33)):setword(m,ARENA+4*i,v)
        if command==11:argument=0x106
        for name,args in (('control',(command,argument)),('ioctl',(0xabcdef01,command,argument))):
            c.compare(f'control/{name}/{command}',m,name,args)
    for bit in (0,1,2,4,8,16,32,64,128,256,512,0xffffffff):
        for flag in (0,2):c.compare(f'configure/{bit}/{flag}',initial(),'control',(11,bit|flag))
    for command in (100,103,402):
        m=initial();setword(m,DEVICE+24,0);setword(m,DEVICE+28,0)
        c.compare(f'discover/{command}',m,'control',(command,ARENA),reads={0x11c08:[0x12,0x34,0x16]+list(range(16))+[0]})
    for command in (47,205):c.compare(f'null control/{command}',initial(),'control',(command,0))
    for command in (200,201,204,202,403,404):
        for a in (0xbefff,0xbf000,0xfefff,0xff000,0xffffffff):
            c.compare(f'ioctl bounds/{command}/{a}',initial(),'ioctl',(0,command,a))
    for command in (199,200,201,202,203,204,205,0xffffffff):
        m=initial();setword(m,DEVICE+24,0x1000)
        for address in (0,0x1000,0x2000):c.compare(f'erase native/{command}/{address}',m,'device_erase',(command,address))
    for name,args in (('control',(206,DEVICE+33)),('control',(206,DEVICE+31)),('control',(402,DEVICE+1)),
                      ('control',(205,DEVICE+28)),('control',(101,DEVICE+24)),('control',(47,DEVICE+68))):
        c.compare(f'control alias/{args}',initial(),name,args)

def transfer_cases(c):
    for n in (0,1,2,255,256,257,511,513):
        for address in (0xbf000,0xbf0ff):
            for name,args in (('read',(address,ARENA,n)),('program',(0,ARENA,n,address)),('program_pages',(ARENA,n,address))):
                c.compare(f'transfer/{name}/{address}/{n}',initial(),name,args)
    for address,n in ((0,0),(0xbefff,1),(0xff000,0),(0xff000,1),(0xffffffff,2),(0xffffff00,256)):
        c.compare(f'read bounds/{address}/{n}',initial(),'read',(address,ARENA,n),event_budget=200)
        c.compare(f'program bounds/{address}/{n}',initial(),'program',(0,ARENA,n,address),event_budget=200)
    for n in (0,1,0x10000,0x10001):
        c.compare(f'device read count/{n}',initial(8),'device_read',(ARENA,0xbf000,n),registers={0x40200:0x800})
    for cap in (0,1,0xbf000,0xbf001,0xffffffff):
        m=initial();setword(m,DEVICE+24,cap);c.compare(f'program capacity/{cap}',m,'program_pages',(ARENA,1,0xbf000))
    for n in (0x7fffffff,0x80000000,0xffffff00,0xffffffff):
        m=initial();setword(m,DEVICE+24,0xffffffff)
        c.compare(f'program prefix/{n}',m,'program_pages',(ARENA,n,1),event_budget=100)
    for value in (0,4,0x10000,0x20000,0x30000,0x40000,0x50000,0x70000,0x741fc):
        for name in ('status_write','status_apply'):c.compare(f'status/{name}/{value}',initial(),name,(value,))
    c.compare('busy becomes ready',initial(),'busy_wait',reads={0x11c08:[1,3,0]})
    m=initial();setword(m,DEVICE+64,0);c.compare('default configured bus word',m,'bus_enter')
    c.compare('nonzero status ioctl',initial(),'control',(13,0x10000))
    c.compare('status apply restores continuous mode',initial(6),'status_apply',(0x10000,),registers={0x40200:0x600})
    c.compare('status nonzero response',initial(),'status_read',reads={0x11c08:[0xa5,0x5a]})
    c.compare('status immediate match',initial(),'status_apply',(0x141fc,),reads={0x11c08:[0xfc,0x41]})
    c.compare('delayed transfer ready',initial(),'transfer_wait',reads={0x11c00:[0,1,0x8000]})
    c.compare('delayed cache ready',initial(),'cache_lines',(0xfffffff1,64),reads={0x01eee008:[0,0,0x4000]})
    c.compare('delayed XIP ready',initial(),'bus_enter',reads={0x40200:[0,0,0x80000000,0x80000000,0]})

def mutation_cases(c):
    cases=(
      ('initialize',(),('call',0x0203fb92),0,DEVICE+24,0x2000000,4),
      ('activity',(1,),('call',0x01c04862),0,STATE+22,3,1),
      ('bus_enter',(),('call',0x02040614),0,STATE+67,127,1),
      ('bus_enter',(),('call',0x01c01108),0,DEVICE+64,0x1ff9,4),
      ('bus_enter',(),(READ,0x40200),0,DEVICE+64,0x1555,4),
      ('bus_leave',(0,),('call',0x01c011da),0,STATE+67,127,1),
      ('bus_leave',(0,),(READ,0x40200),0,DEVICE+56,0x700,4),
      ('identify',(),(READ,0x11c08),1,DEVICE+28,0x5a005a,4),
      ('device_program',(ARENA,0xbf000,3),(WRITE,0x11c08),0,ARENA+1,0xe1,1),
      ('device_read',(DEVICE+56,0xbf000,3),(READ,0x11c08),0,DEVICE+80,1,1),
      ('control',(205,ARENA),(READ,0x40300),0,DEVICE+36,0xbe000,4),
      ('control',(205,ARENA),(WRITE,0x4030c),0,DEVICE+36,0xbd000,4),
      ('control',(101,ARENA),('call',0x02040614),0,STATE+67,255,1),
      ('program_pages',(ARENA,257,0xbf000),('call',0x0204074c),0,ARENA+256,0xee,1),
      ('cache_lines',(0xfffffff1,33),(FLUSH,0xffffffe0),0,STATE+1232,0x12345678,4),
    )
    for index,(name,args,key,occ,a,v,n) in enumerate(cases):
        m=initial()
        if name=='initialize':setword(m,DEVICE+16,0,1)
        if name=='control' and args[0]==205:
            for i,vv in enumerate((0,0xbf000,16,17,0xbf000,0x10000000,33)):setword(m,ARENA+4*i,vv)
        c.compare(f'callback mutation/{index}',m,name,args,mutations=((key,occ,a,v,n),))
    for name,args,reads in (
      ('transfer_wait',(),{0x11c00:0}),('busy_wait',(),{0x11c08:1}),
      ('bus_enter',(),{0x40200:0x80000000}),('bus_leave',(0,),{0x40200:0x80000000}),
      ('cache_lines',(ARENA,32),{0x01eee008:0}),('status_write',(0x70000,),{0x11c08:1}),
      ('device_program',(ARENA,3,4),{}),('read',(0xbf000,ARENA,513),{})):
        for budget in (0,1,2,5,17,64):
            c.compare(f'event prefix/{name}/{budget}',initial(),name,args,event_budget=budget,reads=reads)

def carried_cases(c):
    memory=initial();registers={0x40200:0x600}
    for i,v in enumerate((0,0xbf000,16,17,0xbf000,0x10000000,33)):setword(memory,ARENA+4*i,v)
    for index,(name,args) in enumerate((('control',(205,ARENA)),('control',(11,0x82)),
        ('read',(0xbf000,ARENA+128,7)),('program',(0,ARENA+128,7,0xbf0fd)),
        ('control',(204,0xbf000)),('status_capture',()),('control',(47,ARENA+256)))):
        result=c.compare(f'carried storage/{index}',memory,name,args,registers=registers)
        memory=result['memory'];registers=result['register_words']

def run_cases(c):
    for group in (smoke_cases,scalar_cases,mode_cases,control_cases,transfer_cases,mutation_cases):
        group(c);print(group.__name__,len(c.records),len(c.visited),flush=True)

def source_paths():
    names=set(SOURCES)|{'tools/storage_control_machine.py','tools/verify_storage_control.py',
        'tools/build_storage_control.py','tests/test_storage_control_machine.py','tests/storage_control_sanitize.c',
        'research/input-manifest.json','analysis/firmware/m571_g_app/memory-layout.json'}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    for directory in ('upstream/pi32v2-isa/isa','upstream/pi32v2-isa/tools/hwtest/semantics'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.suffix in ('.py','.toml'))
    pending=list(SOURCES)
    while pending:
        name=pending.pop()
        for include in re.findall(r'^#include\s+"([^"]+)"',(ROOT/name).read_text(),re.M):
            candidates=((ROOT/name).parent/include,ROOT/'firmware/include'/include)
            match=next((p.resolve() for p in candidates if p.is_file()),None)
            if match is None:raise ValueError('unresolved storage-control C include')
            child=match.relative_to(ROOT).as_posix()
            if child not in names:names.add(child);pending.append(child)
    return sorted(names)

def guard_checks(c):
    checks=[]
    def run(label,name,args=(),expected=-200,work=10000,services=100,events=10000,setup=None,script=None):
        b=Backend(initial(),script or Script());b.io.work=work;b.io.services=services;b.io.events=events
        argv=(U32*12)(*args);out=(U32*2)(0xdeadbeef,0xcafebabe)
        if setup:setup(b)
        status=c.execute(REGIONS[name][0] if isinstance(name,str) else name,argv,out,ctypes.byref(b.io))
        if status!=expected or (status and tuple(out)!=(0xdeadbeef,0xcafebabe)):raise AssertionError((label,status,tuple(out)))
        checks.append({'label':label,'status':status,'result_untouched':bool(status)})
        return b
    for missing in ('arguments','result','io','map','call','event'):
        b=Backend(initial(),Script());argv=(U32*12)();out=(U32*2)(0xdeadbeef,0xcafebabe)
        if missing=='map':b.io.map=MAP()
        if missing=='call':b.io.call=CALL()
        if missing=='event':b.io.event=EVENT()
        status=c.execute(REGIONS['control'][0],None if missing=='arguments' else argv,None if missing=='result' else out,
            None if missing=='io' else ctypes.byref(b.io))
        if status!=-200:raise AssertionError((missing,status))
        checks.append({'label':'null '+missing,'status':status})
    run('unknown complete entry',0x020026d8)
    run('zero work','power2',(1,),expected=-203,work=0)
    run('zero platform budget','control',(101,ARENA),expected=-203,services=0)
    run('zero MMIO budget','transfer_wait',expected=-203,events=0)
    for work in (1,2,5,20,50):run(f'finite work/{work}','send_buffer',(ARENA,32),expected=-203,work=work)
    run('absent output map','control',(101,0x31000000),expected=-201)
    run('private output map','control',(101,0x30000fc0),expected=-202)
    run('wrapped output map','control',(101,0xfffffffe),expected=-201)
    run('straddling MMIO output','control',(101,0x11bff),expected=-201)
    for name,(start,_) in REGIONS.items():
        run('immutable code/'+name,'control',(101,start),expected=-201)
    for name,(start,_) in STATIC.items():run('immutable table/'+name,'control',(101,start),expected=-201)
    class BadBorrow(Script):
        def __init__(self,address,size,event):super().__init__();self.address=address;self.size=size;self.on_event=event;self.denied=0
        def check(self,m):
            p=m.borrowed.map(m.borrowed.opaque,self.address,self.size,1)
            if p is not None:raise AssertionError('forbidden borrowed view accepted')
            self.denied+=1
        def call(self,t,args,m):
            if not self.on_event:self.check(m)
            return 0
        def event(self,op,a,n,v,m):
            if self.on_event:self.check(m)
            return 0
    for address,size,expected in ((0x30000000,1,-202),(0x3000103f,1,-202),(0x11c00,4,-201),(0x11bff,2,-201),
                                  (0xffffffff,2,-201),(0x02002a2a,1,-201)):
        for event in (False,True):
            script=BadBorrow(address,size,event)
            run(f'borrowed domain/{address}/{size}/{event}','transfer_wait' if event else 'activity',() if event else (1,),
                expected=expected,script=script)
            if script.denied!=1:raise AssertionError('borrowed domain witness did not execute once')
    return checks

def write_fixtures(path,records):
    def words(f,*v):f.write(struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
    with path.open('wb') as f:
        words(f,0x31435453,len(records),len(MAPPED))
        for base,size in MAPPED:words(f,base,size)
        for label,before,name,args,status,result,after,calls,events,timeline,actions,event_budget in records:
            raw=label.encode();words(f,len(raw));f.write(raw)
            words(f,REGIONS[name][0],*(tuple(args)+(0,)*(12-len(args))),status,*result,event_budget,len(actions))
            for data in before:f.write(data)
            for op,address,width,value,ret,argv,writes in actions:
                words(f,op,address,width);f.write(struct.pack('<QQ',value,ret));words(f,*argv,len(writes))
                for a,n,v in writes:words(f,a,n);f.write((v&((1<<(8*n))-1)).to_bytes(n,'little'))
            for data in after:f.write(data)

def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path);p.add_argument('--part',default='all',choices=('all','smoke','scalar','mode','control','transfer','mutation','carried'))
    a=p.parse_args();c=Corpus(a.library)
    before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    library_before=hashlib.sha256(a.library.read_bytes()).hexdigest()
    original=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    packed=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    if hashlib.sha256(original).hexdigest()!=DECODED or hashlib.sha256(packed).hexdigest()!=PINNED:raise ValueError('original storage image binding differs')
    for name,run in (('smoke',smoke_cases),('scalar',scalar_cases),('mode',mode_cases),('control',control_cases),('transfer',transfer_cases),('mutation',mutation_cases),('carried',carried_cases)):
        if a.part in ('all',name):run(c);print(name,len(c.records),len(c.visited),flush=True)
    gaps=sorted(set(c.program.code)-c.visited)
    from storage_control_machine import TABLE_PROOFS
    report={'result':'pass','component':'storage-control','original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
      'comparisons':len(c.records),'counts':c.counts,'steps':c.steps,'visited':[hex(x) for x in sorted(c.visited)],'digest':c.digest.hexdigest(),
      'functions':{n:{'start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'bytes_sha256':hashlib.sha256(c.program.regions[n]).hexdigest(),
         'instructions':sum(s<=pc<e for pc in c.program.code)} for n,(s,e) in REGIONS.items()},
      'instruction_coverage':{'new_decoded':len(c.program.code),'new_visited':len(c.visited),'unvisited_new':[hex(x) for x in gaps],
         'all_decoded':len(c.program.code),'all_visited':len(c.visited),'unvisited_all':[hex(x) for x in gaps]},
      'gap_instructions':{hex(x):c.program.code[x][0] for x in gaps},
      'gap_classification':{'0x02002b7e':'the fatal fixed-PC self-loop is observed before executing it; -204 is not a native return'},
      'branch_tables':{n:{'start':hex(s),'end_exclusive':hex(e),'sha256':digest,'active_bytes':count,'padding_bytes':e-s-count,
         'consumer':hex(consumer),'targets':[hex(s+2*x) for x in c.program.data[n][:count]],
         'index_proof':{hex(pc):text for pc,text in TABLE_PROOFS[n].items()}} for n,(s,e,count,consumer,digest) in TABLES.items()},
      'auxiliary_reset_witness':{'start':hex(BSS_WITNESS[0]),'end_exclusive':hex(BSS_WITNESS[1]),'sha256':BSS_WITNESS[2],
         'cleared_start':'0x01c2030c','cleared_end_exclusive':'0x01c38050','runtime_BSS_not_immutable_data':True},
      'service_sites':{hex(pc):{'target':hex(t),'arity':n} for pc,(t,n) in c.program.service_sites.items()},
      'mmio_windows':[{'start':hex(base),'end_exclusive':hex(base+n)} for base,n in MMIO],
      'platform_boundaries':'scripted synchronous IRQ registration, locking, cross-core critical sections, clock, scheduler and fatal/reset services',
      'event_boundaries':'synthetic MMIO READ/WRITE with exact widths and values; barrier/flush instruction events; no physical device, cache or inter-core ordering claim',
      'instruction_timeouts':{'transfer_wait':50000000,'busy_wait':5000000,'terminal_timeout_paths_executed':False},
      'device_access':False,'hardware_test':False,'audio_test':False,'firmware_changed':False}
    if a.part=='all':
        if gaps!=[0x02002b7e]:raise ValueError(f'unclassified storage instruction gaps {gaps}')
        report['invalid_api_checks']=guard_checks(c)
    if a.mini_image:
        raw=a.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=MINI:raise ValueError('MINI reviewed whole-image hash differs')
        body=unpack_app(raw)[2]['app.bin']
        for s,e in REGIONS.values():
            if region_bytes(body,s,e)!=region_bytes(original,s,e):raise ValueError('MINI storage body differs')
        for s,e in STATIC.values():
            if region_bytes(body,s,e)!=region_bytes(original,s,e):raise ValueError('MINI storage branch data differs')
        if region_bytes(body,*BSS_WITNESS[:2])!=c.program.bss_witness:raise ValueError('MINI storage reset witness differs')
        report['mini_binding']={'sha256':MINI,'regions':len(REGIONS),'instructions':len(c.program.code),'branch_data_bytes':32,'auxiliary_reset_witness_bytes':22}
    if a.fixtures:write_fixtures(a.fixtures,c.records)
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    if report['source_sha256']!=before:raise ValueError('source bytes/set changed during verification')
    if hashlib.sha256(a.library.read_bytes()).hexdigest()!=library_before:raise ValueError('host library changed during verification')
    report['library_sha256']=library_before
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':report['result'],'comparisons':len(c.records),'steps':c.steps,
        'visited':len(c.visited),'decoded':len(c.program.code),'unvisited':len(gaps),
        'gaps':report['gap_instructions'] if len(gaps)<=12 else 'see report'}))

if __name__=='__main__':main()
