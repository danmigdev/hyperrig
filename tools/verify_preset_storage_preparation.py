"""Compare preset preparation against complete decoded original instructions."""
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
from preset_storage_preparation_machine import (PresetStoragePreparationProgram,REGIONS,REUSED,
 ARITIES,MAPPED,STATE,GLOBAL,CACHE,ARENA,STACK,ROOT,check_derivatives,region_bytes)
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app

SOURCES=tuple('firmware/src/hyperrig_'+n+'.c' for n in ('preset_storage_preparation','controls',
 'control_actions','selection','preset_storage','preset_preflight','preset_loader',
 'capture_metadata','capture_journal','effect_enable','effect_parameter_support'))
U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class Borrowed(ctypes.Structure):_fields_=[('map',MAP),('opaque',ctypes.c_void_p)]
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32,ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):_fields_=[('map',MAP),('call',CALL),('opaque',ctypes.c_void_p),('work',U32),('services',U32)]
READ,PROGRAM,ERASE,ALLOCATE,FREE,CLOCK=0x02002810,0x02002ef2,0x02002b80,0x0203c15c,0x0203d218,0x01c04862
FLASH,FLASH_BYTES=0xbf000,0x40000
HEAP,INPUT,OTHER=ARENA,ARENA+8192,ARENA+12288
PINNED='2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
DECODED='4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
MINI='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
def setword(memory,address,value,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:
            data[address-base:address-base+size]=(value&((1<<(size*8))-1)).to_bytes(size,'little');return
    raise ValueError(f'unmapped fixture {address:#x}/{size}')
def getword(memory,address,size=4):
    for (base,n),data in zip(MAPPED,memory):
        if base<=address<=address+size<=base+n:return int.from_bytes(data[address-base:address-base+size],'little')
    raise ValueError('unmapped fixture read')
def initial(ready=True):
    memory=[bytearray(n) for _,n in MAPPED]
    memory[1][:]=bytes([0xa7])*len(memory[1]);setword(memory,GLOBAL+44,288)
    setword(memory,STATE+712,int(ready),1);setword(memory,STATE+716,int(ready),1)
    for i in range(16):setword(memory,STATE+3476+i,255,1)
    for i in range(18):setword(memory,STATE+3440+i,1,1)
    setword(memory,STATE+3492,1)
    return memory
def block(i):return FLASH+4096*i if i<16 else 0xdd000 if i==16 else 0xde000
def flash_word(flash,address,value,size=4):
    offset=address-FLASH;flash[offset:offset+size]=(value&((1<<(size*8))-1)).to_bytes(size,'little')
def record(size=8,seed=0):
    data=bytearray((i*37+seed)&255 for i in range(size+40));struct.pack_into('<III',data,0,0x51474b54,size,0)
    return data
def write_data(memory,address,data):
    for i,v in enumerate(data):setword(memory,address+i,v,1)

class Script:
    def __init__(self,flash=None,returns=None,mutations=(),read_prefix=None,program_prefix=None):
        self.flash=bytearray(flash if flash is not None else bytes([255])*FLASH_BYTES)
        self.returns=returns or {};self.mutations=mutations;self.seen={};self.events=[]
        self.read_prefix=read_prefix or {};self.program_prefix=program_prefix or {}
    def __call__(self,target,args,m):
        occurrence=self.seen.get(target,0);self.seen[target]=occurrence+1
        values=self.returns.get(target)
        specified=(values[min(occurrence,len(values)-1)] if isinstance(values,(list,tuple)) else values)
        event={'target':target,'args':args,'reads':[],'writes':[]}
        def read(a,n):
            data=bytes(m.read(a+i,1) for i in range(n));event['reads'].append((a,data));return data
        def write(a,data):
            event['writes'].append((a,bytes(data)))
            for i,v in enumerate(data):m.write(a+i,v,1)
        if target==READ:
            address,destination,size=args[:3]
            result=0 if FLASH<=address<=address+size<=FLASH+FLASH_BYTES else 0xffffffff
            if specified is not None:result=specified
            amount=self.read_prefix.get(occurrence,size if result==0 else 0)
            if amount:
                if not FLASH<=address<=address+amount<=FLASH+FLASH_BYTES:raise ValueError('fixture read beyond physical array')
                write(destination,self.flash[address-FLASH:address-FLASH+amount])
        elif target==PROGRAM:
            _,source,size,address=args[:4];data=read(source,size)
            result=size if specified is None else specified;amount=min(size,self.program_prefix.get(occurrence,size if result==size else 0))
            if amount:
                if not FLASH<=address<=address+amount<=FLASH+FLASH_BYTES:raise ValueError('fixture program beyond physical array')
                for i in range(amount):self.flash[address-FLASH+i]&=data[i]
        elif target==ERASE:
            address=args[2]
            if specified is None or specified==0:
                self.flash[address-FLASH:address-FLASH+4096]=bytes([255])*4096
            result=0 if specified is None else specified
        elif target==ALLOCATE:result=HEAP if specified is None else specified
        elif target==CLOCK:result=100000+occurrence*997 if specified is None else specified
        else:result=0 if specified is None else specified
        for at,which,address,value,width in self.mutations:
            if at==target and (which<0 or occurrence==which):write(address,(value&((1<<(width*8))-1)).to_bytes(width,'little'))
        event['result']=result&0xffffffff;self.events.append(event);return result&0xffffffff

class Backend:
    def __init__(self,memory,script,alignment=0):
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory];self.arrays=[]
        for allocation,data in zip(self.allocations,memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment);array[:]=data;self.arrays.append(array)
        self.script=script;self.calls=[];self.errors=[];self.borrowed=None
        self.io=IO(MAP(self.map),CALL(self.call),None,4000000,10000)
    def map(self,opaque,address,size,writable):
        for (base,n),array in zip(MAPPED,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(array)+address-base
        return None
    def read(self,address,size):
        p=self.borrowed.map(self.borrowed.opaque,address,size,0) if self.borrowed else self.map(None,address,size,0)
        if p is None:raise ValueError(f'unmapped/uninitialized callback read {address:#x}/{size}')
        return int.from_bytes(ctypes.string_at(p,size),'little')
    def write(self,address,value,size):
        p=self.borrowed.map(self.borrowed.opaque,address,size,1) if self.borrowed else self.map(None,address,size,1)
        if p is None:raise ValueError(f'unmapped callback write {address:#x}/{size}')
        ctypes.memmove(p,(value&((1<<(size*8))-1)).to_bytes(size,'little'),size)
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)
    def call(self,opaque,target,args,count,borrowed):
        try:
            arguments=tuple(args[i] for i in range(count))+(0,)*(12-count)
            before=hashlib.sha256(b''.join(self.snapshot())).hexdigest();self.borrowed=borrowed.contents
            value=self.script(target,arguments,self);self.borrowed=None
            after=hashlib.sha256(b''.join(self.snapshot())).hexdigest()
            self.calls.append((target,arguments,before,after,value));return value
        except Exception as exc:self.errors.append(str(exc));self.borrowed=None;return 0

class Corpus:
    def __init__(self,library):
        self.program=PresetStoragePreparationProgram();self.library=ctypes.CDLL(str(Path(library).resolve()))
        self.execute=self.library.hyperrig_preset_storage_preparation_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.visited=set();self.steps=0;self.counts={};self.records=[];self.digest=hashlib.sha256()
    def compare(self,label,memory,name,args=(),alignment=0,**script_args):
        first=Script(**script_args)
        try:original=self.program.execute(memory,name,args,first)
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        second=Script(**script_args);backend=Backend(memory,second,alignment)
        out=(U32*2)(0xdeadbeef,0xcafebabe);status=self.execute(REGIONS[name][0],(U32*12)(*args),out,ctypes.byref(backend.io))
        if status or backend.errors:raise AssertionError((label,'portable status',status,backend.errors[:3]))
        if tuple(out)!=original['result']:raise AssertionError((label,'result',tuple(out),original['result']))
        if backend.calls!=original['calls']:
            mismatch=next(((i,a,b) for i,(a,b) in enumerate(zip(backend.calls,original['calls'])) if a!=b),None)
            raise AssertionError((label,'calls',len(backend.calls),len(original['calls']),mismatch))
        if backend.snapshot()!=original['memory']:
            changes=[(hex(base+i),a,b) for (base,_),aa,bb in zip(MAPPED,backend.snapshot(),original['memory'])
                     for i,(a,b) in enumerate(zip(aa,bb)) if a!=b]
            raise AssertionError((label,'memory',changes[:30]))
        if first.flash!=second.flash or first.events!=second.events:raise AssertionError((label,'storage or borrowed buffer events'))
        self.visited|=original['visited'];self.steps+=original['steps'];self.counts[name]=self.counts.get(name,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*out));self.digest.update(first.flash)
        for data in original['memory']:self.digest.update(data)
        self.records.append((label,memory,REGIONS[name][0],args,original['result'],original['memory'],first.events))
        return original['memory'],first.flash

def basic_cases(c):
    for preset in (0,1,15,16,31,32,0xffffffff):
        m=initial();setword(m,STATE+708,0xa5a5a5a5);c.compare(f'invalidate/{preset}',m,'invalidate',(preset,))
    for n in (0,1,2,39,40,41,127,128,129,255,256,257,1490,1920):
        m=initial();data=record(max(n,1),n);write_data(m,INPUT,data)
        c.compare(f'write/{n}',m,'ordered_write',(FLASH+31,INPUT,n),alignment=n%4)
        f=bytearray([255])*FLASH_BYTES;f[17:17+len(data)]=data
        c.compare(f'readback/{n}',m,'readback',(FLASH+17,INPUT,n),flash=f)
    for n in (0,1,40,1490,1880,1881):
        f=bytearray([255])*FLASH_BYTES;data=record(n);f[:len(data)]=data
        c.compare(f'record copy/{n}',initial(),'record_copy',(FLASH,INPUT),flash=f)
    for index in (0,15,16,17,18,255):c.compare(f'erase/{index}',initial(),'erase_block',(index,))
    for pair in (0,15,16,0xffffffff):
        m=initial();write_data(m,INPUT,record(8));write_data(m,OTHER,record(17))
        c.compare(f'pair/{pair}',m,'replace_pair',(pair,INPUT,48,OTHER,57))
    for n in (0,1,39,40,41,1920,1921,0xffffffff):
        m=initial();write_data(m,INPUT,record(1880));c.compare(f'pair size/{n}',m,'replace_pair',(0,INPUT,n,0,0))
    c.compare('prepare cache',initial(),'prepare')
    c.compare('prepare fresh',initial(False),'prepare')
    for calibration in (0,0x20000000,288):
        m=initial();setword(m,STATE+712,0,1);setword(m,GLOBAL+44,calibration)
        for i in range(16):setword(m,STATE+3476+i,i,1)
        c.compare(f'prepare cached scan/{calibration}',m,'prepare')
    for preset in (0,1,31,32):
        m=initial();data=record(12);write_data(m,INPUT,data)
        c.compare(f'preset/{preset}',m,'preset_write',(preset,INPUT,INPUT+40,12))

def populated_flash():
    f=bytearray([255])*FLASH_BYTES
    for i in range(16):
        flash_word(f,block(i)+4080,0xffffffff);flash_word(f,block(i)+4092,1129335636)
        for odd in (0,1):
            data=record(8+i,i+odd);offset=block(i)+2048*odd-FLASH;f[offset:offset+len(data)]=data
    return f
def pending_flash(left_bytes=48,right_bytes=57,pair=3,corrupt=False):
    import zlib
    f=populated_flash();left=bytes((i*5+3)&255 for i in range(left_bytes));right=bytes((i*7+11)&255 for i in range(right_bytes))
    h=struct.pack('<4I',1246776148,pair,left_bytes,right_bytes)
    h+=struct.pack('<I',zlib.crc32(h[4:]+left+right)^(1 if corrupt else 0))
    offset=0xde000-FLASH;f[offset:offset+20]=h
    f[offset+32:offset+32+left_bytes]=left;f[offset+1952:offset+1952+right_bytes]=right
    return f
def failure_cases(c):
    for index in (0,16,17,0xffffffff):
        for strikes in (0,1,2,254,255):
            m=initial();setword(m,STATE+3458+index if index!=0xffffffff else STATE+3457,strikes,1)
            f=bytearray([0])*FLASH_BYTES
            c.compare(f'erase not blank/{index}/{strikes}',m,'erase_block',(index,),flash=f,returns={ERASE:1})
    for stage in range(5):
        m=initial();write_data(m,INPUT,record(1880));write_data(m,OTHER,record(12))
        c.compare(f'pair program fault/{stage}',m,'replace_pair',(0,INPUT,1920,OTHER,52),
            returns={PROGRAM:[None]*stage+[0]*30},program_prefix={stage:7})
    for position in (0,1,2,3,4,8,14,15,16,17):
        m=initial();write_data(m,INPUT,record(12));write_data(m,OTHER,record(17))
        for i in range(18):setword(m,STATE+3440+i,2 if i==position else 3,1)
        setword(m,STATE+3476,5,1)
        c.compare(f'pair erase fallback/{position}',m,'replace_pair',(0,INPUT,52,OTHER,57))
    for kind in (0,3,4,5,255):
        m=initial()
        for i in range(18):setword(m,STATE+3440+i,kind,1)
        c.compare(f'pair no capacity/{kind}',m,'replace_pair',(0,0,0,0,0))
    for failures in ((1,),(1,0),(0,1),(0,0,1),(0,0,0,1)):
        m=initial();write_data(m,INPUT,record(12));write_data(m,OTHER,record(17))
        c.compare(f'pair read fault/{failures}',m,'replace_pair',(0,INPUT,52,OTHER,57),returns={READ:failures})
    for part in ('header','payload','magic','mismatch'):
        f=populated_flash();m=initial();data=record(8);write_data(m,INPUT,data)
        if part=='magic':flash_word(f,FLASH,0)
        c.compare(f'record fault/{part}',m,'record_copy',(FLASH,INPUT),flash=f,
            returns={READ:([1] if part=='header' else [0,1] if part=='payload' else [0])},read_prefix={0:9,1:7} if part in ('header','payload') else {})
        if part=='mismatch':
            setword(m,INPUT+2,0,1);c.compare('readback mismatch',m,'readback',(FLASH,INPUT,48),flash=f)
    for target in (ALLOCATE,READ):
        c.compare(f'prepare service failure/{target:x}',initial(False),'prepare',returns={target:0 if target==ALLOCATE else 1})

def discovery_cases(c):
    f=bytearray([255])*FLASH_BYTES;f[0]=0
    c.compare('discover nonblank untagged block',initial(False),'prepare',flash=f)
    c.compare('discover second-scan read error',initial(False),'prepare',returns={READ:[0]*18+[1,0]})
    f=populated_flash();c.compare('discover factory pairs',initial(False),'prepare',flash=f)
    for generation in (0,1,2,0xfffffffe,0xffffffff):
        f=populated_flash();flash_word(f,block(16)+4080,0);flash_word(f,block(16)+4084,generation)
        flash_word(f,block(16)+4092,1129335636)
        c.compare(f'duplicate generation/{generation}',initial(False),'prepare',flash=f)
    for pair in (15,16,0xffffffff):
        f=populated_flash();flash_word(f,block(16)+4080,pair);flash_word(f,block(16)+4084,7);flash_word(f,block(16)+4092,1129335636)
        c.compare(f'footer pair/{pair}',initial(False),'prepare',flash=f)
    for bad in ('magic','marker'):
        f=populated_flash()
        if bad=='magic':flash_word(f,FLASH+4092,0)
        else:flash_word(f,FLASH+4088,0)
        c.compare(f'footer callback classification/{bad}',initial(False),'prepare',flash=f,
            mutations=((READ,0,STATE+3440,5,1),))
    for left,right in ((0,0),(1,0),(0,1),(48,57),(1920,1920)):
        c.compare(f'recovery/{left}/{right}',initial(False),'prepare',flash=pending_flash(left,right))
    c.compare('recovery bad crc',initial(False),'prepare',flash=pending_flash(corrupt=True))
    for field,value in ((4,16),(8,1921),(12,1921),(4088,0)):
        f=pending_flash();flash_word(f,0xde000+field,value)
        c.compare(f'recovery invalid header/{field}',initial(False),'prepare',flash=f)
    for offset in range(4):
        m=initial();setword(m,STATE+712,0,1);setword(m,STATE+3457,4,1)
        for i in range(16):setword(m,STATE+3476+i,i,1)
        c.compare(f'recovery read failure/{offset}',m,'prepare',flash=pending_flash(),
            returns={READ:[0]*offset+[1]*20},read_prefix={offset:3})
    for failure in (0,1,2,3,4,5,6):
        m=initial();setword(m,STATE+712,0,1);setword(m,STATE+3457,4,1)
        for i in range(16):setword(m,STATE+3476+i,i,1)
        c.compare(f'recovery program failure/{failure}',m,'prepare',flash=pending_flash(),
            returns={PROGRAM:[None]*failure+[0]*30})

def mutation_cases(c):
    for preset in (0,1,30,31):
        for mode in ('edit','replace','delete'):
            m=initial();f=populated_flash()
            for i in range(16):setword(m,STATE+3476+i,i,1);setword(m,STATE+3440+i,3,1)
            write_data(m,INPUT,record(16,77))
            args=(preset,0 if mode=='delete' else INPUT,INPUT+40 if mode=='replace' else 0,16)
            c.compare(f'preset mode/{preset}/{mode}',m,'preset_write',args,flash=f,alignment=preset%4)
    for preset in (0,1,32):
        for return_ in (0,1):
            m=initial();write_data(m,INPUT,record(16))
            c.compare(f'edit missing/{preset}/{return_}',m,'preset_write',(preset,INPUT,0,16),returns={ALLOCATE:HEAP if return_ else 0})
    for failure in (0,1,2,3):
        m=initial();f=populated_flash();setword(m,STATE+3476,0,1);write_data(m,INPUT,record(12))
        c.compare(f'edit read failure/{failure}',m,'preset_write',(0,INPUT,0,12),flash=f,returns={READ:[0]*failure+[1]*20})
    for field,width,value in ((3496,1,17),(3492,4,0xffffffff),(3476,1,9),(280,4,1),(708,4,0x12345678),(732,4,0x87654321)):
        m=initial();write_data(m,INPUT,record(44));write_data(m,OTHER,record(13))
        c.compare(f'pair callback state/{field}',m,'replace_pair',(0,INPUT,84,OTHER,53),
            mutations=((PROGRAM,0,STATE+field,value,width),))
    for source in (CACHE,CACHE+15,STATE+3436,STATE+3476,INPUT+1):
        m=initial();write_data(m,source,record(17))
        c.compare(f'write native source alias/{source:x}',m,'write_forward',(0xdf000,source,57),alignment=3)
    for allocator in (HEAP,INPUT,INPUT-40):
        m=initial();write_data(m,INPUT,record(13))
        c.compare(f'preset allocation alias/{allocator:x}',m,'preset_write',(0,INPUT,INPUT+40,13),returns={ALLOCATE:allocator})
    for alignment in range(4):
        for delta in (-17,-1,1,3,17):
            m=initial();source=INPUT+alignment;write_data(m,source,record(17))
            c.compare(f'preset byte overlap/{alignment}/{delta}',m,'preset_write',(0,source,source+40,17),
                returns={ALLOCATE:source+delta},alignment=alignment)
    m=initial();setword(m,STATE+280,1);write_data(m,INPUT,record(700))
    c.compare('journal yields between pages',m,'write_forward',(FLASH+3,INPUT,740))
    m=initial(False);f=populated_flash()
    for step in range(6):
        m=[bytearray(x) for x in m];write_data(m,INPUT,record(19+step,step))
        if step==3:setword(m,STATE+712,0,1);setword(m,STATE+716,0,1)
        m,f=c.compare(f'carried persistent pair/{step}',m,'preset_write',(step&1,INPUT,INPUT+40,19+step),flash=f)

def source_paths():
    names=set(SOURCES)|{'tools/preset_storage_preparation_machine.py','tools/verify_preset_storage_preparation.py',
        'tools/build_preset_storage_preparation.py','tests/test_preset_storage_preparation_machine.py',
        'tests/preset_storage_preparation_sanitize.c','research/input-manifest.json',
        'analysis/firmware/m571_g_app/memory-layout.json',
        'upstream/pi32v2-isa/tools/hwtest/semantics/s.py','upstream/pi32v2-isa/tools/hwtest/semantics/r.py'}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    for directory in ('upstream/pi32v2-isa/isa','upstream/pi32v2-isa/tools/hwtest/semantics'):
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.suffix in ('.py','.toml'))
    pending=list(SOURCES)
    while pending:
        path=pending.pop()
        for include in re.findall(r'^#include\s+"([^"]+)"',(ROOT/path).read_text(),re.M):
            candidates=((ROOT/path).parent/include,ROOT/'firmware/include'/include)
            match=next((x.resolve() for x in candidates if x.is_file()),None)
            if match is None:raise ValueError('unresolved local C header')
            name=match.relative_to(ROOT).as_posix()
            if name not in names:names.add(name);pending.append(name)
    return sorted(names)

def guard_checks(c):
    checks=[]
    def run(label,entry,args=(),expected=-200,work=10000,services=100,setup=None,script=None):
        b=Backend(initial(),script or Script());b.io.work=work;b.io.services=services
        argv=(U32*12)(*args);out=(U32*2)(0xdeadbeef,0xcafebabe)
        if setup:setup(b)
        value=c.execute(entry,argv,out,ctypes.byref(b.io))
        if value!=expected or (expected and tuple(out)!=(0xdeadbeef,0xcafebabe)):
            raise AssertionError((label,value,tuple(out)))
        checks.append({'label':label,'status':value,'result_untouched':bool(expected)})
        return b,tuple(out)
    for missing in ('arguments','result','io','map','call'):
        b=Backend(initial(),Script());argv=(U32*12)();out=(U32*2)(0xdeadbeef,0xcafebabe)
        if missing=='map':b.io.map=MAP()
        if missing=='call':b.io.call=CALL()
        value=c.execute(REGIONS['prepare'][0],None if missing=='arguments' else argv,
            None if missing=='result' else out,None if missing=='io' else ctypes.byref(b.io))
        if value!=-200:raise AssertionError((missing,value))
        checks.append({'label':'null '+missing,'status':value})
    run('unknown complete entry',0x020031d6)
    run('zero work',REGIONS['prepare'][0],expected=-203,work=0)
    run('zero service budget',REGIONS['read_forward'][0],(FLASH,INPUT,4),expected=-203,services=0)
    for work in (1,2,3,5,10,40):
        run(f'finite write work/{work}',REGIONS['ordered_write'][0],(FLASH,INPUT,1920),expected=-203,work=work)
    def missing_map(b):b.io.map=MAP(lambda *_:None)
    run('absent checked-mask mapping',REGIONS['invalidate'][0],(0,),expected=-201,setup=missing_map)
    run('private read output below active frame',REGIONS['read_forward'][0],(FLASH,STACK-100,4),expected=-202)
    run('allocation returns private storage',REGIONS['preset_write'][0],(0,0,0,0),expected=-202,script=Script(returns={ALLOCATE:STACK-64}))
    # Deliberate boundary-contract violation: success without initialized data.
    run('successful read omitted private bytes',REGIONS['record_copy'][0],(FLASH,INPUT),expected=-202,
        script=Script(read_prefix={0:3}))
    for amount in (0,3,39):
        _,out=run(f'failed read retains initialized prefix/{amount}',REGIONS['record_copy'][0],
            (FLASH,INPUT),expected=0,script=Script(returns={READ:1},read_prefix={0:amount}))
        if out!=(0xfffffffe,0):raise AssertionError('failed partial read result')
    class ScopedRead(Script):
        def __init__(self,kind):super().__init__();self.kind=kind;self.denied=False
        def __call__(self,target,args,m):
            if target==READ:
                address=args[1]+args[2] if self.kind=='outside' else args[1]
                pointer=m.borrowed.map(m.borrowed.opaque,address,1,self.kind=='outside')
                self.denied=pointer is None
                return 0
            return super().__call__(target,args,m)
    for kind in ('outside','uninitialized'):
        script=ScopedRead(kind)
        run('borrowed READ '+kind,REGIONS['record_copy'][0],(FLASH,INPUT),expected=-202,script=script)
        if not script.denied:raise AssertionError('private READ scope was not rejected')
    class ReadOnlyProgram(Script):
        denied=False
        def __call__(self,target,args,m):
            if target==PROGRAM and 0x30000000<=args[1]<STACK:
                self.denied=m.borrowed.map(m.borrowed.opaque,args[1],1,1) is None
                return 0
            return super().__call__(target,args,m)
    script=ReadOnlyProgram()
    run('borrowed private PROGRAM is read only',REGIONS['replace_pair'][0],(0,0,0,0,0),
        expected=-202,script=script)
    if not script.denied:raise AssertionError('private PROGRAM write was not rejected')
    class NoClockExposure(Script):
        denied=False
        def __call__(self,target,args,m):
            if target==CLOCK:
                self.denied=m.borrowed.map(m.borrowed.opaque,STACK-52,1,1) is None
                return 0
            return super().__call__(target,args,m)
    script=NoClockExposure()
    run('clock does not expose private frame',REGIONS['preset_write'][0],(32,0,0,0),expected=-202,script=script)
    if not script.denied:raise AssertionError('non-buffer callback private access was not rejected')
    run('invalid native pair has precedence',REGIONS['replace_pair'][0],(16,0x30000000,1921,0,0),expected=0,services=0)
    return checks

def write_fixtures(path,records):
    def words(out,*values):out.write(struct.pack('<'+'I'*len(values),*values))
    with path.open('wb') as out:
        words(out,0x31505350,len(records),len(MAPPED))
        for base,size in MAPPED:words(out,base,size)
        for label,before,entry,args,result,after,events in records:
            encoded=label.encode();words(out,len(encoded));out.write(encoded)
            words(out,entry,*(tuple(args)+(0,)*(12-len(args))),*result,len(events))
            for data in before:out.write(data)
            for e in events:
                from preset_storage_preparation_machine import SERVICES
                count=SERVICES[e['target']]
                words(out,e['target'],count,*e['args'],e['result'],len(e['reads']),len(e['writes']))
                for address,data in e['reads']+e['writes']:words(out,address,len(data));out.write(data)
            for data in after:out.write(data)

def main():
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path)
    p.add_argument('--fixtures',type=Path);p.add_argument('--mini-image',type=Path)
    p.add_argument('--part',choices=('basic','failures','discovery','mutations','all'),default='all')
    a=p.parse_args();check_derivatives();c=Corpus(a.library)
    sources_before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    library_before=hashlib.sha256(a.library.read_bytes()).hexdigest()
    for name,run in (('basic',basic_cases),('failures',failure_cases),('discovery',discovery_cases),('mutations',mutation_cases)):
        if a.part in (name,'all'):run(c);print(name,sum(c.counts.values()),flush=True)
    new={pc for pc in c.program.code if any(x<=pc<y for x,y in REGIONS.values())}
    gaps=sorted(new-c.visited)
    report={'result':'pass','component':'preset-storage-preparation','original_image_sha256':PINNED,
        'decoded_image_sha256':DECODED,'comparisons':sum(c.counts.values()),'counts':c.counts,'steps':c.steps,
        'visited':[hex(pc) for pc in sorted(c.visited)],'digest':c.digest.hexdigest(),
        'functions':{name:{'start':hex(start),'end_exclusive':hex(end),'bytes':end-start,
            'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest(),
            'instructions':sum(start<=pc<end for pc in c.program.code)} for name,(start,end) in REGIONS.items()},
        'reused_functions':{name:{'start':hex(start),'end_exclusive':hex(end),
            'bytes_sha256':hashlib.sha256(c.program.regions[name]).hexdigest()} for name,(start,end) in REUSED.items()},
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),
            'unvisited_new':[hex(x) for x in gaps],'all_decoded':len(c.program.code),'all_visited':len(c.visited),
            'unvisited_all':[hex(x) for x in sorted(set(c.program.code)-c.visited)]},
        'gap_classification':{
            '0x02002e22':'erase_block passes an aligned in-range block address and one page; actual journal_erase cannot reject those arguments',
            '0x0200791c':'header-only editing resolves both members through the same pair map before any callback; a nonzero current address implies nonzero neighbor'},
        'journal_derivative':check_derivatives(),'service_sites':{hex(pc):{'target':hex(t),'arity':n} for pc,(t,n) in c.program.service_sites.items()},
        'platform_boundaries':'scripted byte storage, allocation/release, clock, notification and coordination; no physical driver or power-loss simulation',
        'private_memory':'only initialized bytes in scoped original-address argument buffers; callback write mappings initialize the whole requested span',
        'new_data_exclusions':[],'device_access':False,'hardware_test':False,'audio_test':False,'firmware_changed':False}
    if a.part=='all':
        if set(gaps)!={0x02002e22,0x0200791c}:raise ValueError(f'unclassified storage new instruction gaps: {gaps}')
        report['invalid_api_checks']=guard_checks(c)
    if a.mini_image:
        raw=a.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=MINI:raise ValueError('MINI differs from pinned reviewed v4')
        mini_body=unpack_app(raw)[2]['app.bin']
        original=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        for name,(start,end) in (REGIONS|REUSED).items():
            if region_bytes(mini_body,start,end)!=region_bytes(original,start,end):raise ValueError('MINI storage region differs')
        report['mini_binding']={'sha256':MINI,'regions':len(REGIONS)+len(REUSED),'instructions':len(c.program.code)}
    if a.fixtures:write_fixtures(a.fixtures,c.records)
    report['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    if report['source_sha256']!=sources_before:raise ValueError('source set or bytes changed during verification')
    if hashlib.sha256(a.library.read_bytes()).hexdigest()!=library_before:raise ValueError('host library changed during verification')
    report['library_sha256']=library_before
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('result','comparisons','counts','steps','instruction_coverage')}))
if __name__=='__main__':main()
