"""Compare complete joined storage execution against original instruction packets."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from storage_runtime_machine import (StorageRuntimeProgram,PREPARATION,ALL_REGIONS,JOINS,MAPPED,
    STATE,GLOBAL,DEVICE,ARENA,ROOT,READ,WRITE,MMIO,STATIC,PARENTS,region_bytes)
from verify_storage_coordination import U32,U64,MAP,CALL,EVENT,CPU,Borrowed

class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',CALL),('event',EVENT),('opaque',ctypes.c_void_p),('work',U32),('services',U32),('events',U32)]
SOURCES=tuple('firmware/src/hyperrig_'+n+'.c' for n in ('storage_runtime','storage_runtime_control','storage_coordination',
    'controls','control_actions','selection','preset_storage','preset_preflight','preset_loader',
    'capture_metadata','capture_journal','effect_enable','effect_parameter_support'))
FLASH,FLASH_BYTES=0xbf000,0x40000
HEAP,INPUT,OTHER=ARENA,ARENA+8192,ARENA+12288
ALLOCATE,FREE,CLOCK=0x0203c15c,0x0203d218,0x01c04862
SERVICES={}
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app


def setword(memory,a,v,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:data[a-base:a-base+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little');return
    raise ValueError('fixture outside memory')
def getword(memory,a,n=4):
    for (base,size),data in zip(MAPPED,memory):
        if base<=a<=a+n<=base+size:return int.from_bytes(data[a-base:a-base+n],'little')
    raise ValueError('fixture read outside memory')
def initial(ready=True,cold=False,mode=0):
    m=[bytearray(n) for _,n in MAPPED];m[2][:]=bytes((i*37+11)&255 for i in range(len(m[2])))
    setword(m,GLOBAL+44,288);setword(m,GLOBAL+24,0x12345678)
    setword(m,STATE+712,int(ready),1);setword(m,STATE+716,int(ready),1)
    for i in range(16):setword(m,STATE+3476+i,255,1)
    for i in range(18):setword(m,STATE+3440+i,1,1)
    setword(m,STATE+3492,1);setword(m,STATE+4076,200)
    setword(m,DEVICE+16,not cold,1);setword(m,DEVICE+24,0 if cold else 0x100000)
    setword(m,DEVICE+28,0 if cold else 0x123416);setword(m,DEVICE+64,0x1029)
    setword(m,DEVICE+52,0x10000000);setword(m,0x01c24228,not cold,1)
    return m
def block(i):return FLASH+4096*i if i<16 else 0xdd000 if i==16 else 0xde000
def flash_word(f,a,v,n=4):f[a-FLASH:a-FLASH+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little')
def record(size=8,seed=0):
    data=bytearray((i*37+seed)&255 for i in range(size+40));struct.pack_into('<III',data,0,0x51474b54,size,0);return data
def data(memory,a,raw):
    for i,b in enumerate(raw):setword(memory,a+i,b,1)
def populated_flash():
    f=bytearray([255])*FLASH_BYTES
    for i in range(18):
        flash_word(f,block(i)+4080,i%16);flash_word(f,block(i)+4084,0);flash_word(f,block(i)+4092,1129335636)
        for odd in (0,1):
            raw=record(8+i,i+odd);start=block(i)+2048*odd-FLASH;f[start:start+len(raw)]=raw
    return f


class Script:
    """Synthetic serial-flash fixture driven only by actual MMIO observations.

    This test device is deterministic protocol state, not physical flash or a
    claim that the recovered driver's reported lengths imply durability.
    """
    def __init__(self,flash=None,mode=0,returns=None,mutations=(),registers=None,reads=None,probes=(),ignore_program=False):
        self.flash=bytearray([255])*FLASH_BYTES if flash is None else bytearray(flash)
        self.registers={};self.returns=returns or {};self.mutations=mutations;self.reads=reads or {};self.seen={};self.actions=[];self.probes=probes
        self.selected=False;self.command=None;self.address_bytes=[];self.payload=[];self.index=0;self.read_index=0
        self.status=0;self.extended=False;self.mode=mode;self.last_read=0xeb if mode&1 else 0xbb
        self.transactions=[];self.pending=None
        self.ignore_program=ignore_program
        for a,v in ({0x11c00:0x1029,0x40200:mode<<8,0x01eee008:0x4000,0x500c0:1}|(registers or {})).items():self.register(a,v,4)
    def register(self,a,v,n):
        for j in range(n):self.registers[a+j]=(v>>(8*j))&255
    def value(self,a,n):return sum(self.registers.get(a+j,0)<<(8*j) for j in range(n))
    @staticmethod
    def pick(v,index,default):return default if v is None else v[min(index,len(v)-1)] if isinstance(v,(list,tuple)) else v
    def count(self,key):i=self.seen.get(key,0);self.seen[key]=i+1;return i
    def mutate(self,key,index,m):
        writes=[]
        for target,which,a,v,n in self.mutations:
            if target==key and (which<0 or which==index):m.write(a,v,n);writes.append((1,a,n,v))
        for target,which,a,n,writable in self.probes:
            if target==key and (which<0 or which==index):
                if m.public_probe(a,n,writable):raise AssertionError('forbidden private view accepted')
                writes.append((2,a,n,writable))
        return writes
    def address(self):
        value=0
        for b in self.address_bytes:value=((value<<8)|b)&0xffffffff
        return value
    def transmit(self,v):
        v&=255
        if not self.selected:return
        if self.command is None:
            if self.mode in (6,7) and v!=255:
                self.command=self.last_read;self.address_bytes.append(v);return
            self.command=v;return
        needed=3 if self.command in (0xbb,0xeb) else 4 if self.extended else 3
        if self.command in (3,11,59,107,0xbb,0xeb,2,32,216,129,199) and len(self.address_bytes)<needed:
            self.address_bytes.append(v)
        else:self.payload.append(v)
    def receive(self):
        command=self.command;index=self.read_index;self.read_index+=1
        if command==159:return (0x12,0x34,0x16)[index%3]
        if command==75:return (index*17+9)&255
        if command==5:return self.status&255
        if command==53:return self.status>>8
        if command in (3,11,59,107,0xbb,0xeb):
            dummy={3:0,11:1,59:2,107:4,0xbb:0,0xeb:2}[command]
            if index<dummy:return 0
            address=self.address()+index-dummy
            return self.flash[address-FLASH] if FLASH<=address<FLASH+FLASH_BYTES else 255
        return 0
    def finish(self):
        command=self.command;address=self.address();payload=bytes(self.payload)
        if command==2 and not self.ignore_program:
            for i,v in enumerate(payload):
                if FLASH<=address+i<FLASH+FLASH_BYTES:self.flash[address+i-FLASH]&=v
        elif command in (32,216,129,199):
            size={32:4096,216:65536,129:256,199:0x100000}[command];start=address&-size
            lo=max(start,FLASH);hi=min(start+size,FLASH+FLASH_BYTES)
            if lo<hi:self.flash[lo-FLASH:hi-FLASH]=bytes([255])*(hi-lo)
        elif command==1 and payload:self.status=(self.status&0xff00)|payload[0]
        if command==1 and len(payload)>1:self.status=(self.status&255)|(payload[1]<<8)
        if command==49 and payload:self.status=(self.status&255)|(payload[0]<<8)
        if command==183:self.extended=True
        if command==233:self.extended=False
        self.transactions.append((command,address,payload,self.read_index))
    def call(self,target,args,m):
        i=self.count(('call',target));default=HEAP if target==ALLOCATE else 100000+997*i if target==CLOCK else 0
        value=self.pick(self.returns.get(target),i,default)&0xffffffff;writes=self.mutate(('call',target),i,m)
        self.actions.append((0,target,SERVICES[target],0,value,args,writes));return value
    def event(self,op,a,n,v,m):
        i=self.count((op,a));result=0
        if op==WRITE:
            old=self.value(a,n);self.register(a,v,n)
            if a==0x500c0:
                if old&1 and not v&1:
                    self.selected=True;self.command=None;self.address_bytes=[];self.payload=[];self.read_index=0
                elif not old&1 and v&1 and self.selected:self.finish();self.selected=False
            if a==0x11c08:
                if self.value(0x11c00,4)&0x1000:self.register(a,self.receive(),4)
                else:self.transmit(v)
        elif op==READ:
            default=self.value(a,n)
            if a==0x11c00:default|=0x8000
            result=self.pick(self.reads.get(a),i,default)
        writes=self.mutate((op,a),i,m)
        if op==WRITE and a==0x11c08 and self.command==2 and len(self.payload)==1:
            index=self.count(('program_data',0));writes+=self.mutate(('program_data',0),index,m)
        self.actions.append((op,a,n,v,result,(0,)*12,writes));return result
    def retained(self):
        return (bytes(self.flash),dict(self.registers),self.selected,self.command,tuple(self.address_bytes),bytes(self.payload),
            self.read_index,self.status,self.extended,tuple(self.transactions))


class Backend:
    def __init__(self,memory,cpu,script,services=100000,events=1000000,work=20000000,alignment=0):
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory];self.arrays=[]
        for allocation,raw in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(raw)).from_address(ctypes.addressof(allocation)+alignment);array[:]=raw;self.arrays.append(array)
        self.cpu=CPU(*cpu);self.script=script;self.calls=[];self.events=[];self.timeline=[];self.errors=[];self.borrowed=None
        self.io=IO(MAP(self.map),CALL(self.call),EVENT(self.event),None,work,services,events)
    def map(self,opaque,a,n,writable):
        for (base,size),array in zip(MAPPED,self.arrays):
            if base<=a<=a+n<=base+size:return ctypes.addressof(array)+a-base
        return None
    def read(self,a,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,0) if self.borrowed else self.map(None,a,n,0)
        if p is None:raise ValueError('callback read denied')
        return int.from_bytes(ctypes.string_at(p,n),'little')
    def write(self,a,v,n):
        p=self.borrowed.map(self.borrowed.opaque,a,n,1) if self.borrowed else self.map(None,a,n,1)
        if p is None:raise ValueError('callback write denied')
        ctypes.memmove(p,(v&((1<<(8*n))-1)).to_bytes(n,'little'),n)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def public_probe(self,a,n,writable=0):
        if self.borrowed is None:raise ValueError('probe outside callback')
        return self.borrowed.map(self.borrowed.opaque,a,n,writable) is not None
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())+struct.pack('<II',self.cpu.cnum,self.cpu.icfg)).hexdigest()
    def call(self,opaque,target,args,count,borrowed):
        try:
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
        self.program=StorageRuntimeProgram();SERVICES.update({t:n for t,n in self.program.service_sites.values()})
        self.library=ctypes.CDLL(str(Path(library).resolve()));self.execute=self.library.hyperrig_storage_runtime_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(CPU),ctypes.POINTER(IO)]
        self.visited=set();self.steps=0;self.records=[];self.join_counts={};self.counts={}
    def compare(self,label,memory,name,args=(),cpu=(0,0x01090700),services=100000,events=1000000,alignment=0,**kwargs):
        first=Script(**kwargs)
        try:r=self.program.execute(memory,name,args,cpu,first.call,first.event,services,events)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        second=Script(**kwargs);b=Backend(memory,cpu,second,services,events,alignment=alignment);out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=self.execute(PREPARATION[name][0],(U32*12)(*args),out,ctypes.byref(b.cpu),ctypes.byref(b.io))
        if status!=r['status'] or b.errors:raise AssertionError((label,'status',status,r['status'],hex(r['stop_pc']),b.errors[:3]))
        expected=(0xdeadbeef,0xcafebabe) if status else r['result']
        if tuple(out)!=expected:raise AssertionError((label,'result',tuple(out),expected))
        for key,actual in (('calls',b.calls),('events',b.events),('timeline',b.timeline)):
            if actual!=r[key]:
                diff=next(((i,a,z) for i,(a,z) in enumerate(zip(actual,r[key])) if a!=z),None)
                raise AssertionError((label,key,len(actual),len(r[key]),diff))
        if (b.cpu.cnum,b.cpu.icfg)!=r['cpu']:raise AssertionError((label,'CPU'))
        if b.snapshot()!=r['memory']:
            diff=[(hex(base+i),a,z) for (base,_),x,y in zip(MAPPED,b.snapshot(),r['memory']) for i,(a,z) in enumerate(zip(x,y)) if a!=z]
            raise AssertionError((label,'RAM',diff[:20]))
        if first.retained()!=second.retained() or first.actions!=second.actions:raise AssertionError((label,'synthetic serial state/actions'))
        self.visited|=r['visited'];self.steps+=r['steps'];self.counts[name]=self.counts.get(name,0)+1
        for pc,n in r['join_counts'].items():self.join_counts[pc]=self.join_counts.get(pc,0)+n
        self.records.append((label,tuple(map(bytes,memory)),name,args,cpu,status,tuple(out),r['cpu'],r['memory'],first.actions,services,events))
        r['flash']=bytes(first.flash)
        print(label,status,len(first.actions),len(r['visited']),flush=True)
        return r


def smoke_cases(c):
    m=initial();data(m,INPUT,record(12))
    c.compare('cached prepare',m,'prepare')
    c.compare('invalidate',m,'invalidate',(3,))
    for size in (0,1,4):
        c.compare(f'read/{size}',m,'read_forward',(FLASH,INPUT,size))
        c.compare(f'write/{size}',m,'write_forward',(FLASH,INPUT,size))
    c.compare('record private header',m,'record_copy',(FLASH,INPUT),flash=populated_flash())
    c.compare('readback private',m,'readback',(FLASH,INPUT,40),flash=populated_flash())
    c.compare('invalid read mode private',m,'record_copy',(FLASH,INPUT),mode=8)
    c.compare('read destination wraps between byte stores',m,'read_forward',(FLASH,0xffffffff,2),flash=populated_flash())


def transaction_cases(c):
    m=initial();data(m,INPUT,record(700));data(m,OTHER,record(17))
    for size in (0,1,39,40,41,127,128,129,255,256,257):
        c.compare(f'ordered/page boundary/{size}',m,'ordered_write',(FLASH+251,INPUT,size),alignment=size%4)
    for size in (0,1,8,1880,1881):
        f=bytearray([255])*FLASH_BYTES;raw=record(size);f[:len(raw)]=raw
        c.compare(f'record size/{size}',m,'record_copy',(FLASH,OTHER),flash=f)
    for pair,left,right in ((0,0,0),(0,48,57),(15,48,0),(16,48,57),(0,1921,0)):
        c.compare(f'pair transaction/{pair}/{left}/{right}',m,'replace_pair',(pair,INPUT,left,OTHER,right))
    c.compare('erase and confirm full block',m,'erase_block',(0,))
    c.compare('cold discovery populated',initial(False,True),'prepare',flash=populated_flash())
    c.compare('ready scan allocation failure',initial(False),'prepare',flash=populated_flash(),returns={ALLOCATE:0})
    for preset in (0,1,31,32):
        c.compare(f'preset full transaction/{preset}',m,'preset_write',(preset,INPUT,INPUT+40,12))
    for mode in (1,2,3,4,5):
        c.compare(f'real read transfer mode/{mode}',m,'record_copy',(FLASH,OTHER),flash=populated_flash(),mode=mode)


def mutation_cases(c):
    for destination in (INPUT+1,STATE+22,STATE+66,DEVICE+56):
        c.compare(f'public read overlap/{destination:x}',initial(),'read_forward',(FLASH,destination,4),flash=populated_flash(),alignment=3)
    for source in (INPUT+1,STATE+3436,STATE+3476):
        m=initial();data(m,source,record(17))
        c.compare(f'public program overlap/{source:x}',m,'write_forward',(FLASH+255,source,57),alignment=1)
    for target,at,n,v in (((WRITE,0x11c08),INPUT+1,1,37),(('call',0x02040614),STATE+280,4,1),
        (('call',CLOCK),GLOBAL+44,4,0),((WRITE,0x11c08),STATE+708,4,0x12345678)):
        m=initial();data(m,INPUT,record(12))
        c.compare(f'public synchronous mutation/{target}/{at}',m,'write_forward',(FLASH,INPUT,52),mutations=((target,0,at,v,n),))
    for mode in (8,9,15):
        c.compare(f'unwritten private header/{mode}',initial(),'record_copy',(FLASH,INPUT),mode=mode)
    for kind in ('call','event'):
        target=('call',0x02040614) if kind=='call' else (READ,0x11c00)
        for address,n in ((0x30000000,1),(0x30000fc8,40),(0x30000ff0,1),(0x3000103f,1)):
            c.compare(f'public-only callback during lease/{kind}/{address:x}',initial(),'record_copy',(FLASH,INPUT),
                probes=((target,0,address,n,1),))
    m=initial()
    c.compare('read-only private footer program callback',m,'replace_pair',(0,0,0,0,0),
        probes=((('program_data',0),0,0x30000fc4,8,1),))
    c.compare('expired lease at free callback',initial(False),'prepare',flash=populated_flash(),
        probes=((('call',FREE),0,0x30000fc4,4,0),))
    c.compare('TESTSET callback guard retains CPU and lock',m,'write_forward',(FLASH,INPUT,1),
        probes=(((8,STATE+55),0,0x30000fc4,1,0),))
    m=initial();setword(m,STATE+712,0,1)
    c.compare('allocator mapping fault precedes private return',m,'prepare',returns={ALLOCATE:0x30000000},
        probes=((('call',ALLOCATE),0,0x40000000,1,0),))
    m=initial();data(m,INPUT,record(12));cpu=(0,0x01090700);f=populated_flash()
    for i,(name,args) in enumerate((('prepare',()),('preset_write',(0,INPUT,INPUT+40,12)),('preset_write',(1,INPUT,INPUT+40,12)),
        ('readback',(block(2),INPUT,52)),('invalidate',(0,)))):
        if i==0:m=initial(False)
        if i in (1,2):data(m,INPUT,record(12,i))
        r=c.compare(f'carried original storage/{i}',m,name,args,cpu=cpu,flash=f)
        m=[bytearray(x) for x in r['memory']];cpu=r['cpu'];f=r['flash']


def prefix_cases(c):
    for budget in (0,1,2,3,4,5,6,7,8,12):
        c.compare(f'shared services/read/{budget}',initial(),'record_copy',(FLASH,INPUT),services=budget)
        c.compare(f'shared services/write/{budget}',initial(),'write_forward',(FLASH,INPUT,4),services=budget)
    for budget in (0,1,2,3,4,5,10,20,40,80,120,180,200,250):
        c.compare(f'shared events/read/{budget}',initial(),'record_copy',(FLASH,INPUT),events=budget)
        c.compare(f'shared events/write/{budget}',initial(),'write_forward',(FLASH,INPUT,4),events=budget)
    for budget in (0,2,4,8,20):
        m=initial();setword(m,STATE+280,2);setword(m,STATE+29,1,1)
        c.compare(f'coordination-to-driver event budget/{budget}',m,'erase_block',(0,),events=budget)


def recovery_cases(c):
    import zlib
    for left,right,corrupt in ((12,13,False),(0,0,False),(12,13,True)):
        m=initial();setword(m,STATE+712,0,1)
        for i in range(16):setword(m,STATE+3476+i,i,1);setword(m,STATE+3440+i,3,1)
        setword(m,STATE+3457,4,1)
        f=populated_flash();off=0xde000-FLASH;f[off:off+4096]=bytes([255])*4096
        if not left:f[block(16)-FLASH:block(16)-FLASH+4096]=bytes([255])*4096
        a=bytes((i*5+3)&255 for i in range(left));b=bytes((i*7+11)&255 for i in range(right))
        header=struct.pack('<4I',1246776148,3,left,right)
        header+=struct.pack('<I',zlib.crc32(header[4:]+a+b)^(1 if corrupt else 0))
        f[off:off+20]=header;f[off+32:off+32+left]=a;f[off+1952:off+1952+right]=b
        c.compare(f'actual recovery/{left}/{right}/{corrupt}',m,'prepare',flash=f)
    m=initial();data(m,INPUT,record(12));setword(m,DEVICE+24,FLASH+8)
    c.compare('capacity return fails journal',m,'write_forward',(FLASH,INPUT,52))
    c.compare('two failed pair attempts',m,'replace_pair',(0,INPUT,52,0,0))
    m=initial();data(m,INPUT,record(12))
    c.compare('reported program length without readback persistence',m,'replace_pair',(0,INPUT,52,0,0),ignore_program=True)


def source_paths():
    names=set(SOURCES)|set(PARENTS)|{'tools/storage_runtime_machine.py','tools/verify_storage_runtime.py','tools/build_storage_runtime.py',
        'tests/test_storage_runtime_machine.py','tests/storage_runtime_sanitize.c','research/input-manifest.json',
        'analysis/firmware/m571_g_app/memory-layout.json','third_party/ultrarig/LICENSE.md'}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    for directory in ('upstream/pi32v2-isa/isa','upstream/pi32v2-isa/tools/hwtest/semantics'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.suffix in ('.py','.toml'))
    pending=list(SOURCES)+['tests/storage_runtime_sanitize.c']
    while pending:
        name=pending.pop()
        for include in re.findall(r'^#include\s+"([^"]+)"',(ROOT/name).read_text(),re.M):
            match=next((p.resolve() for p in ((ROOT/name).parent/include,ROOT/'firmware/include'/include) if p.is_file()),None)
            if match is None:raise ValueError('unresolved runtime C include')
            child=match.relative_to(ROOT).as_posix()
            if child not in names:names.add(child);pending.append(child)
    return sorted(names)


def guard_checks(c):
    checks=[]
    for missing in ('arguments','result','cpu','io','map','call','event'):
        b=Backend(initial(),(0,0),Script());out=(U32*2)(0xdeadbeef,0xcafebabe)
        if missing=='map':b.io.map=MAP()
        if missing=='call':b.io.call=CALL()
        if missing=='event':b.io.event=EVENT()
        status=c.execute(PREPARATION['prepare'][0],None if missing=='arguments' else (U32*12)(),None if missing=='result' else out,
            None if missing=='cpu' else ctypes.byref(b.cpu),None if missing=='io' else ctypes.byref(b.io))
        if status!=-200:raise AssertionError(('missing '+missing,status))
        checks.append({'label':'missing '+missing,'status':status})
    def run(label,name,args=(),expected=-200,work=20000000,script=None,memory=None,setup=None):
        b=Backend(initial() if memory is None else memory,(0,0x01090700),script or Script(),work=work)
        if setup:setup(b)
        out=(U32*2)(0xdeadbeef,0xcafebabe)
        status=c.execute(PREPARATION[name][0] if isinstance(name,str) else name,(U32*12)(*args),out,ctypes.byref(b.cpu),ctypes.byref(b.io))
        if status!=expected or tuple(out)!=(0xdeadbeef,0xcafebabe) or b.errors:raise AssertionError((label,status,tuple(out),b.errors))
        checks.append({'label':label,'status':status,'result_untouched':True})
    run('unknown preparation entry',0x020031d6)
    run('zero work','prepare',expected=-203,work=0)
    for work in (1,2,5,10,25,100):run(f'portable work/{work}','record_copy',(FLASH,INPUT),expected=-203,work=work)
    def deny(b):b.io.map=MAP(lambda *v:None)
    run('missing public state','prepare',expected=-201,setup=deny)
    run('external private destination','read_forward',(FLASH,0x30000ff0,1),expected=-202)
    run('crossing public mapped extent','read_forward',(FLASH,0x01c344b3,2),expected=-201)
    for name,(a,bound) in ALL_REGIONS.items():
        if name.startswith('preparation_') or name=='control_read':
            run('immutable code/'+name,'read_forward',(FLASH,a,1),expected=-201)
    m=initial();setword(m,STATE+712,0,1)
    run('allocator work fault precedes private return','prepare',expected=-203,work=5,memory=m,
        script=Script(returns={ALLOCATE:0x30000000},probes=((('call',ALLOCATE),0,STATE,1,0),)))
    return checks


def write_fixtures(path,records):
    def words(f,*v):f.write(struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
    with path.open('wb') as f:
        words(f,0x31525453,len(records),len(MAPPED))
        for base,size in MAPPED:words(f,base,size)
        for label,before,name,args,cpu,status,result,final_cpu,after,actions,services,events in records:
            raw=label.encode();words(f,len(raw));f.write(raw)
            words(f,PREPARATION[name][0],*(tuple(args)+(0,)*(12-len(args))),*cpu,status,*result,*final_cpu,services,events,len(actions))
            for raw in before:f.write(raw)
            for op,address,width,value,ret,argv,writes in actions:
                words(f,op,address,width);f.write(struct.pack('<QQ',value,ret));words(f,*argv,len(writes))
                for kind,a,n,v in writes:
                    words(f,kind,a,n)
                    if kind==2:words(f,v)
                    else:f.write((v&((1<<(8*n))-1)).to_bytes(n,'little'))
            for raw in after:f.write(raw)


def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--fixtures',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--mini-image',type=Path)
    p.add_argument('--part',choices=('all','smoke','transactions','mutation','prefix','recovery'),default='all');a=p.parse_args();c=Corpus(a.library)
    before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    library_before=hashlib.sha256(a.library.read_bytes()).hexdigest()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    packed=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    if hashlib.sha256(app).hexdigest()!=DECODED or hashlib.sha256(packed).hexdigest()!=PINNED or unpack_app(packed)[2]['app.bin']!=app:
        raise ValueError('runtime original image binding changed')
    for name,run in (('smoke',smoke_cases),('transactions',transaction_cases),('mutation',mutation_cases),('prefix',prefix_cases),('recovery',recovery_cases)):
        if a.part in ('all',name):run(c)
    gaps=sorted(set(c.program.code)-c.visited)
    functions={n:{'start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'bytes_sha256':hashlib.sha256(c.program.regions[n]).hexdigest(),
        'instructions':sum(s<=pc<e for pc in c.program.code),'visited_instructions':sum(s<=pc<e for pc in c.visited)} for n,(s,e) in ALL_REGIONS.items()}
    report={'result':'pass','component':'storage-runtime','original_image_sha256':PINNED,'decoded_image_sha256':DECODED,
        'functions':{},'reused_functions':functions,'new_original_functions':0,'new_data_exclusions':[],
        'comparisons':len(c.records),'counts':c.counts,'steps':c.steps,'visited':[hex(pc) for pc in sorted(c.visited)],
        'instruction_coverage':{'new_decoded':0,'new_visited':0,'unvisited_new':[],
            'joined_decoded':len(c.program.code),'joined_visited':len(c.visited),'unvisited_joined':[hex(pc) for pc in gaps],
            'all_decoded':len(c.program.code),'all_visited':len(c.visited),'unvisited_all':[hex(pc) for pc in gaps]},
        'gap_instructions':{hex(pc):c.program.code[pc][0] for pc in gaps},
        'gap_functions':{n:{'unvisited':[hex(pc) for pc in gaps if s<=pc<e],
            'classification':'existing complete parent body; these raw-entry branches are not reached by this joined corpus'}
            for n,(s,e) in ALL_REGIONS.items() if any(s<=pc<e for pc in gaps)},
        'direct_joins':{hex(pc):{'target':hex(t),'arity':n,'calls':c.join_counts.get(pc,0)} for pc,(t,n) in JOINS.items()},
        'service_sites':{hex(pc):{'target':hex(t),'arity':n} for pc,(t,n) in c.program.service_sites.items()},
        'derivation':c.program.derivation,
        'loaded_instruction_windows':{hex(pc):{'bytes':size,'sha256':hashlib.sha256(region_bytes(app,pc,pc+size)).hexdigest()}
            for pc,(_,size,*_) in c.program.code.items()},
        'bound_static_data':{n:{'start':hex(s),'end_exclusive':hex(e),'sha256':hashlib.sha256(region_bytes(app,s,e)).hexdigest()}
            for n,(s,e) in STATIC.items()},
        'cpu_primary_evidence':c.program.coordination.isa_records,
        'auxiliary_reset_witness':{'start':'0x0200019c','end_exclusive':'0x020001b2',
            'sha256':hashlib.sha256(c.program.control.bss_witness).hexdigest(),'classification':'existing auxiliary startup instructions, not data'},
        'auxiliary_initial_state':{'start':'0x01c1fc54','end_exclusive':'0x01c1fc5c',
            'sha256':hashlib.sha256(c.program.coordination.initial_counters).hexdigest(),'classification':'existing mutable initial IRQ words, not immutable data'},
        'portable_failure_cases':sum(row[5]!=0 for row in c.records),
        'private_initialization_contract':'Only completed internal stores mark private bytes. MMIO/platform callback maps never expose private leases. Native private reads lacking proven payload bytes stop without invented data.',
        'limitations':[
            'Zero new original functions or data exclusions: this joins 75 existing complete bodies at 18 authenticated direct sites.',
            'The 35 remaining direct platform sites, synthetic serial-flash fixture, MMIO/cache observations and CPU events do not prove physical transfer completion, durability, interrupt delivery, atomicity, scheduling or inter-core ordering.',
            'Complete parent bodies remain loaded, including raw control commands not reachable from the eleven preparation APIs; joined coverage is reported separately from prior standalone coverage.',
            'The original fatal self-loop remains a fixed-PC observation and is not reached by this preparation corpus. Full 50000000 transfer and 5000000 busy timeout outcomes remain unexecuted.',
            'Service/event budgets are shared and compare exact observed prefixes. Preparation/map work accounting and per-child local work ceilings are portable limits, not native cycles or arbitrary matched prefixes.',
            'Read-mode8..15 can report success without writing a private destination; the first unavailable payload read is a portable knowledge guard, not an original I/O failure or native return.',
            'The private CPU save-stack is abstractly preserved by the existing instruction models; saved-register bytes are not exposed as arbitrary public payload or newly proven initialized private data.',
            'Typed journal rewrite/append callers and new physical device operations are outside this integration.'],
        'device_access':False,'hardware_test':False,'audio_test':False,'firmware_changed':False}
    if a.part=='all':
        if set(c.join_counts)!=set(JOINS):raise ValueError('joined corpus missed a direct edge')
        report['invalid_api_checks']=guard_checks(c)
    if a.mini_image:
        raw=a.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=MINI:raise ValueError('reviewed MINI whole-image hash changed')
        mini=unpack_app(raw)[2]['app.bin']
        for s,e in (*ALL_REGIONS.values(),*STATIC.values(),(0x0200019c,0x020001b2),(0x01c1fc54,0x01c1fc5c)):
            if region_bytes(mini,s,e)!=region_bytes(app,s,e):raise ValueError('MINI runtime dependency differs')
        report['mini_binding']={'sha256':MINI,'complete_regions':75,'instructions':2283,'existing_branch_data_bytes':32,'auxiliary_bytes':30}
    if a.fixtures:write_fixtures(a.fixtures,c.records)
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths()}
    if report['source_sha256']!=before:raise ValueError('runtime source set/bytes changed during verification')
    if hashlib.sha256(a.library.read_bytes()).hexdigest()!=library_before:raise ValueError('runtime host library changed')
    report['library_sha256']=library_before
    if a.output:a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'comparisons':len(c.records),'steps':c.steps,'visited':len(c.visited),'loaded':len(c.program.code),
        'joined_sites':len(c.join_counts),'gaps':len(gaps)}))
if __name__=='__main__':main()
