"""Original storage-control bodies with explicit synthetic MMIO/platform events.

This executes decoded original instructions. Physical flash, cache coherency,
interrupts and OS behavior are not emulated or asserted.
"""
from __future__ import annotations
import hashlib
import re
from effect_ownership_machine import EffectOwnershipMachine
from effect_enable_machine import CounterRegion,region_bytes,ROOT
from dot_machine import DotMachine,MASK32
from pi32v2isa import codec,table

REGIONS={
 'power2':(0x020026d6,0x020026e8),'initialize':(0x020026e8,0x02002772),
 'ensure':(0x02002772,0x02002786),'activity':(0x02002786,0x020027e4),
 'poll':(0x020027e4,0x02002806),'raw_read':(0x02002806,0x02002810),
 'read':(0x02002810,0x02002874),'range':(0x02002994,0x020029b0),
 'reject':(0x020029b0,0x020029be),'control':(0x020029be,0x02002b80),
 'ioctl':(0x02002b80,0x02002bcc),'mode':(0x02002bcc,0x02002bd8),
 'program_pages':(0x02002e6a,0x02002ef2),'program':(0x02002ef2,0x02002f16),
 'bus_enter':(0x01c00000,0x01c00072),'delay':(0x01c00072,0x01c00088),
 'chip_select':(0x01c00088,0x01c000a8),'transfer_wait':(0x01c000a8,0x01c000d8),
 'send_byte':(0x01c000d8,0x01c000f0),'leave_continuous':(0x01c000f0,0x01c0012e),
 'receive_byte':(0x01c0012e,0x01c0014c),'send_address':(0x01c0014c,0x01c00170),
 'receive_fast':(0x01c00170,0x01c00184),'receive_buffer':(0x01c00184,0x01c00204),
 'send_fast':(0x01c00204,0x01c00214),'send_buffer':(0x01c00214,0x01c00290),
 'transfer_read':(0x01c00290,0x01c003d4),'restore_read':(0x01c003d4,0x01c003e8),
 'bus_leave':(0x01c003e8,0x01c0044c),'identify':(0x01c0044c,0x01c004d0),
 'status_read':(0x01c004d0,0x01c0050a),'status_capture':(0x01c0050a,0x01c00536),
 'bank_enter':(0x01c00536,0x01c0056e),'bank_leave':(0x01c0056e,0x01c005a4),
 'device_read':(0x01c005a4,0x01c005d0),'write_enable':(0x01c005d0,0x01c005e6),
 'translate':(0x01c005e6,0x01c005f6),'cache_forward':(0x01c005f6,0x01c00600),
 'busy_wait':(0x01c00600,0x01c00640),'device_erase':(0x01c00640,0x01c006d2),
 'status_write':(0x01c006d2,0x01c0079e),'status_apply':(0x01c0079e,0x01c00822),
 'cache_region':(0x01c00822,0x01c00840),'device_program':(0x01c00840,0x01c008b4),
 'cache_lines':(0x01c00b80,0x01c00bb2),
}
TABLES={
 'control200':(0x02002a2a,0x02002a32,7,0x02002a28,'9836f1b872721858b1192da003e69649c3bbab55c3d27b6278eb8d944a7fac43'),
 'control100':(0x02002a42,0x02002a46,4,0x02002a40,'eb9d350e3bbbcf98dd77f5b8e02bd5c3b4ade52eb0d62f588a2f8033bf25fa3b'),
 'ioctl200':(0x02002b90,0x02002b96,5,0x02002b8e,'aa61f01dbc3bcf924f704acc5d907ff0a4775c9adf338f1ad979a90315f07dce'),
 'read_modes':(0x01c002bc,0x01c002c4,8,0x01c002ba,'d42e5576b24bc188b82926ddcc9f94ca173cce8ae306c8bff3714b1001c3d406'),
 'erase200':(0x01c0065a,0x01c00660,5,0x01c00658,'9dd98328868b63a856fcc63cf57942f4d7cf52619e525dfda5e4db2876e97145'),
}
STATIC={name:value[:2] for name,value in TABLES.items()}
TABLE_PROOFS={
 'control200':{0x020029e0:'r0 = r7 + -200',0x020029ec:'if (r0 <= 6) goto 56',0x02002a28:'tbb [r0]'},
 'control100':{0x020029f0:'r0 = r7 + -100',0x020029f4:'if (r0 <= 3) goto 72',0x02002a40:'tbb [r0]'},
 'ioctl200':{0x02002b84:'r0 = r4 + -200',0x02002b8a:'if (r0 > 4) goto 14',0x02002b8e:'tbb [r0]'},
 'read_modes':{0x01c002ae:'r0 = sextra(r5, p:8, l:4)',0x01c002b2:'ifs (r0 < 0) goto 34',
               0x01c002b6:'r0 = uextra(r5, p:8, l:4)',0x01c002ba:'tbb [r0]'},
 'erase200':{0x01c00642:'r2 = r0 + -200',0x01c00648:'if (r2 > 4) goto 130',0x01c00658:'tbb [r2]'},
}
DIRECT_SITES={0x0200271e:(0x020005ac,4),0x0200272c:(0x020005ac,4),0x02002736:(0x0203fb92,1),
 0x0200278a:(0x01c04862,0),0x0200282e:(0x01c04862,0),0x020027fe:(0x0203ea6e,0),
 0x020029d0:(0x02040614,1),0x02002e8e:(0x02040614,1),0x01c0000c:(0x02040614,1),
 0x02002b6a:(0x0204074c,1),0x02002ee8:(0x0204074c,1),0x01c00444:(0x0204074c,1),
 0x02002b74:(0x0203e742,0),0x02002b7a:(0x0200096e,0),0x01c0002a:(0x01c01108,2),0x01c00430:(0x01c011da,0)}

def validate_registry(program):
    if program.service_sites!=DIRECT_SITES:raise ValueError('storage direct platform call sites changed')
    for name,(s,e,count,consumer,digest) in TABLES.items():
        raw=program.data[name]
        if len(raw)!=e-s or hashlib.sha256(raw).hexdigest()!=digest or any(raw[count:]):raise ValueError('storage table evidence changed')
        for pc,text in TABLE_PROOFS[name].items():
            if pc not in program.code or program.code[pc][0]!=text:raise ValueError('storage decoder/index proof changed')
        if consumer+program.code[consumer][1]!=s:raise ValueError('storage TBB base changed')
        if any(s<=pc<e for pc in program.code):raise ValueError('storage branch data decoded as instructions')
        if any(s+2*x not in program.code or s+2*x in program.parallel_seconds for x in raw[:count]):
            raise ValueError('storage branch target is not a packet start')

BSS_WITNESS=(0x0200019c,0x020001b2,'05221f085384369277a7fbdc7eefa5a1e46770c9c0f3ccb24b4d2e735267e930')
ARITIES=dict(power2=1,initialize=0,ensure=0,activity=1,poll=0,raw_read=3,read=3,
 range=2,reject=1,control=2,ioctl=3,mode=0,program_pages=3,program=4,
 bus_enter=0,delay=1,chip_select=1,transfer_wait=0,send_byte=1,leave_continuous=0,
 receive_byte=0,send_address=1,receive_fast=0,receive_buffer=2,send_fast=1,send_buffer=2,
 transfer_read=4,restore_read=0,bus_leave=1,identify=0,status_read=0,status_capture=0,
 bank_enter=1,bank_leave=1,device_read=3,write_enable=0,translate=1,cache_forward=2,
 busy_wait=0,device_erase=2,status_write=1,status_apply=1,cache_region=2,device_program=3,cache_lines=2)
VOID={'ensure','activity','poll','reject','bus_enter','delay','chip_select','send_address',
 'restore_read','bus_leave','identify','status_capture','bank_enter','bank_leave',
 'write_enable','cache_forward','cache_region','cache_lines'}
SERVICES={0x020005ac:4,0x0203fb92:1,0x01c04862:0,0x0203ea6e:0,
 0x02040614:1,0x0204074c:1,0x0203e742:0,0x0200096e:0,0x01c01108:2,0x01c011da:0}
GLOBAL,STATE,DEVICE,ARENA,STACK=0x01c1f180,0x01c26890,0x01c3743c,0x33000000,0x30001000
MAPPED=((GLOBAL,0x01c344b4-GLOBAL),(DEVICE,82),(ARENA,65568),(0,256),(0xffffff00,256))
MMIO=((0x11c00,12),(0x500c0,12),(0x5101c,4),(0x40200,4),(0x40300,16),(0x01eee008,4))
READ,WRITE,BARRIER,FLUSH=1,2,3,4

def mmio_span(a,n):return any(base<=a<=a+n<=base+size for base,size in MMIO)

class StorageControlProgram:
    def __init__(self):
        CounterRegion('counter');app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();isa=table.load()
        self.code,self.regions,self.parallel_seconds,self.data={},{},set(),{}
        for name,(s,e,count,consumer,digest) in TABLES.items():
            raw=self.data[name]=region_bytes(app,s,e)
            if hashlib.sha256(raw).hexdigest()!=digest or any(raw[count:]):raise ValueError('storage branch data changed')
        s,e,digest=BSS_WITNESS;self.bss_witness=region_bytes(app,s,e)
        if hashlib.sha256(self.bss_witness).hexdigest()!=digest:raise ValueError('storage reset BSS witness changed')
        for name,(start,end) in REGIONS.items():
            raw=self.regions[name]=region_bytes(app,start,end);pc=start
            while pc<end:
                skip=next((e for s,e in STATIC.values() if s==pc),None)
                if skip:pc=skip;continue
                found=codec.decode(isa,raw,pc-start)
                if found is None:raise ValueError(f'undecoded storage control {pc:#x}')
                ins,fields,size=found;counts=[0,0]
                if ins.block:
                    for i,k in enumerate(('then','else')):
                        f=ins.fields[ins.block[k]];counts[i]=fields[ins.block[k]]*f.scale+f.add
                if pc+size>end:raise ValueError('storage instruction crosses body')
                self.code[pc]=codec.format(ins,fields),size,*counts;pc+=size
        self.service_sites={}
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                if self.code[pc+size][1]!=2 or '[' not in self.code[pc+size][0]:raise ValueError('storage parallel packet changed')
                self.parallel_seconds.add(pc+size)
            if m:=re.fullmatch(r'call (-?\d+)',text):
                target=pc+size+int(m[1])
                if target not in self.code:
                    if target not in SERVICES:raise ValueError(f'unknown storage platform target {target:#x}')
                    self.service_sites[pc]=(target,SERVICES[target])
            elif text.startswith('call '):raise ValueError('unreviewed storage indirect call')
        for name,(s,e,count,consumer,_) in TABLES.items():
            if self.code[consumer][0] not in ('tbb [r0]','tbb [r2]'):raise ValueError('storage table consumer differs')
            targets=[s+2*x for x in self.data[name][:count]]
            if any(t not in self.code or t in self.parallel_seconds for t in targets):raise ValueError('storage table enters non-packet code')
        validate_registry(self)
    def execute(self,memory,name,args=(),boundary=None,events=None,event_budget=1000000,step_budget=12000000):
        if name not in ARITIES or len(args)!=ARITIES[name] or tuple(map(len,memory))!=tuple(n for _,n in MAPPED):
            raise ValueError('storage control call domain')
        return StorageControlMachine(self,memory,name,args,boundary,events,event_budget,step_budget).run()

class StorageControlMachine(EffectOwnershipMachine):
    def __init__(self,program,memory,name,args,boundary,events,event_budget,step_budget):
        self.program,self.operation,self.boundary,self.events=program,name,boundary,events
        self.event_budget,self.step_budget=event_budget,step_budget;self.timeline=[]
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        for table_name,(base,_) in STATIC.items():self.memory.update({base+i:v for i,v in enumerate(program.data[table_name])})
        self.public_memory=list(map(bytearray,memory));self.pc=REGIONS[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set();self.entries={}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[];self.guard=0;self.stop_extra_overread=False
        for i,v in enumerate(args):self.set(f'r{i}',v)
    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def bus(self,op,address=0,width=0,value=0):
        if not self.event_budget:self.guard=-203;raise EventStop()
        self.event_budget-=1
        if self.events is None:raise ValueError('storage requires explicit synthetic MMIO')
        before=hashlib.sha256(b''.join(self.snapshot())).hexdigest()
        result=self.events(op,address,width,value,self)&((1<<64)-1)
        after=hashlib.sha256(b''.join(self.snapshot())).hexdigest()
        self.mmio_events.append((op,address,width,value,result,before,after));self.timeline.append(('event',len(self.mmio_events)-1));return result
    def read(self,a,n):
        if mmio_span(a,n):return self.bus(READ,a,n)&((1<<(8*n))-1)
        return DotMachine.read(self,a,n)
    def write(self,a,value,n):
        value&=(1<<(8*n))-1
        if mmio_span(a,n):self.bus(WRITE,a,n,value);return
        if a+n>1<<32:raise ValueError('storage map wraps')
        if not 0x30000000<=a<=a+n<=STACK+64:
            for (base,size),data in zip(MAPPED,self.public_memory):
                if base<=a<=a+n<=base+size:data[a-base:a-base+n]=value.to_bytes(n,'little');break
            else:raise ValueError(f'storage public write unmapped {a:#x}/{n}')
        self.writes.append((a,value,n));DotMachine.write(self,a,value,n)
    def single_step(self):
        if self.pc==0x02002b7e:self.guard=-204;return False
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if text=='nop':self.pc=next_pc;return True
        if m:=re.fullmatch(r'(r\d+) = (r\d+)\.l \(s\)',text):
            value=self.value(m[2])&65535;self.set(m[1],value if value<32768 else value-65536)
            self.pc=next_pc;return True
        if text=='csync':self.bus(BARRIER);self.pc=next_pc;return True
        if m:=re.fullmatch(r'\[(r\d+)\+(\d+)\] ([&|])= (r\d+|0x[0-9A-Fa-f]+)',text):
            address=(self.value(m[1])+int(m[2]))&MASK32
            operand=self.value(m[4]) if m[4].startswith('r') else int(m[4],16)
            old=self.read(address,4);self.write(address,old&operand if m[3]=='&' else old|operand,4)
            self.pc=next_pc;return True
        if m:=re.fullmatch(r'\[(r\d+)\+(\d+)\] >>= (\d+)',text):
            address=(self.value(m[1])+int(m[2]))&MASK32;self.write(address,self.read(address,4)>>int(m[3]),4)
            self.pc=next_pc;return True
        if m:=re.fullmatch(r'flushinv \[(r\d+)\]',text):self.bus(FLUSH,self.value(m[1]));self.pc=next_pc;return True
        if m:=re.fullmatch(r'call (-?\d+)',text):
            target=next_pc+int(m[1])
            if target in self.program.code:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            expected,count=self.program.service_sites[self.pc]
            if expected!=target or self.boundary is None:raise ValueError('storage platform binding')
            args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=hashlib.sha256(b''.join(self.snapshot())).hexdigest();value=self.boundary(target,args,self)&MASK32
            after=hashlib.sha256(b''.join(self.snapshot())).hexdigest()
            self.calls.append((target,args,before,after,value));self.timeline.append(('call',len(self.calls)-1));self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if m:=re.fullmatch(r'rep (\d+) (\d+) \{',text):
            body=next_pc;end=body+int(m[1])
            for _ in range(int(m[2])):
                self.pc=body
                while self.pc<end:
                    self.steps+=1
                    if not self.step():raise ValueError('storage constant REP returned')
                if self.pc!=end:raise ValueError('storage REP escaped')
            self.pc=end;return True
        return super().single_step()
    def run(self):
        try:
            while self.steps<self.step_budget:
                self.steps+=1
                if not self.step():break
            else:raise ValueError('storage instruction budget exhausted')
        except EventStop:pass
        if not self.guard and (self.frames or self.returns or self.else_skips or self.value('sp')!=STACK):raise ValueError('storage unbalanced return')
        return {'result':None if self.guard else (0 if self.operation in VOID else self.value('r0'),0),
            'status':self.guard,'memory':self.snapshot(),'calls':self.calls,'events':self.mmio_events,
            'visited':self.visited,'steps':self.steps,'service_sites':self.service_sites,
            'internal_calls':self.internal_calls,'stop_pc':self.pc,'timeline':self.timeline}

class EventStop(Exception):pass
