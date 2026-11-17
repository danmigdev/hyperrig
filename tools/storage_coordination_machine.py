"""Decode complete storage-coordination bodies with explicit CPU observations."""
from __future__ import annotations
import hashlib
import json
import re
import struct
from effect_ownership_machine import EffectOwnershipMachine
from effect_enable_machine import CounterRegion,region_bytes,ROOT
from dot_machine import DotMachine,MASK32
from pi32v2isa import codec,table

REGIONS={'ready_threshold':(0x020028f2,0x02002920),'wait_ready':(0x02002920,0x0200294e),
 'poll_forward':(0x02002bec,0x02002bf6),'gate_core':(0x02002bf6,0x02002d06),
 'gate':(0x02002d06,0x02002d10),'notify':(0x02002d10,0x02002d70),'event':(0x02002d70,0x02002d9e),
 'irq_enter':(0x01c00e2e,0x01c00e46),'irq_leave':(0x01c00e46,0x01c00e62)}
REUSED={'rate':(0x02002bd8,0x02002bec)}
ARITIES=dict(ready_threshold=1,wait_ready=0,poll_forward=0,gate_core=2,gate=1,notify=3,event=3,irq_enter=0,irq_leave=0)
VOID=set(ARITIES)-{'ready_threshold'}
GLOBAL,STATE,IRQ_COUNTS,RECORDS,STACK=0x01c1f180,0x01c26890,0x01c1fc54,0x01c2a0d0,0x30001000
MAPPED=((GLOBAL,0x01c344b4-GLOBAL),(0,256),(0xffffff00,256))
BARRIER,CLI,STI,CNUM,TESTSET=3,5,6,7,8
CLOCK,YIELD,POLL=0x01c04862,0x0203feb8,0x0203ea6e
SERVICES={CLOCK:0,YIELD:1,POLL:0}
DIRECT_SITES={0x02002940:(YIELD,1),0x02002bee:(POLL,0),0x02002c2e:(CLOCK,0),0x02002c3c:(CLOCK,0),
 0x02002c68:(YIELD,1),0x02002c7c:(YIELD,1),0x02002cd4:(CLOCK,0),0x02002ce6:(CLOCK,0),0x02002d78:(CLOCK,0)}
ISA_SITES={0x02002d30:'testset.b',0x02002d32:'bc.eq',0x01c00e2e:'cli',0x01c00e30:'mov.r_sr',0x01c00e5e:'sti'}
INITIAL_COUNTERS=(IRQ_COUNTS,IRQ_COUNTS+8,'af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc')
ISA_RECORD_SHA256={
 '0x2002d30':'58a8309bdef2a4381ea7815ca30ad2b636a000f6a9d1cd8f6b46b64ab15864be',
 '0x2002d32':'ce1e6bda6e2c86ca7013f074a95af16da363605e436e16ae6d02a5b11e3d1a2d',
 '0x1c00e2e':'6e7ec874c2902d32ad705a7b05ffc762bf45d9bf802d428ec530732caa437412',
 '0x1c00e30':'1d54e052c2a0213eab323479d7973744f67f21c15e157db4def336f08a7dfc8d',
 '0x1c00e5e':'864f15571e33e214e973e089ef6071d325403f5da9d0d39eac8f0c5dfed1cd6c'}
def validate_cpu_evidence(program):
    if set(program.isa_records)!=set(ISA_RECORD_SHA256):raise ValueError('CPU evidence set changed')
    for key,digest in ISA_RECORD_SHA256.items():
        value=program.isa_records[key]
        if hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=digest:
            raise ValueError('CPU ISA record changed')
        if program.code[int(key,16)][0]!=value['decoded']:raise ValueError('CPU decoded site differs from evidence')


class StorageCoordinationProgram:
    def __init__(self):
        CounterRegion('counter');app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();isa=table.load()
        self.code,self.regions,self.parallel_seconds,self.service_sites,self.isa_records={},{},set(),{},{}
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);pc=start
            while pc<end:
                found=codec.decode(isa,raw,pc-start)
                if found is None:raise ValueError('undecoded storage coordination instruction')
                ins,fields,size=found;counts=[0,0]
                if ins.block:
                    for i,k in enumerate(('then','else')):
                        f=ins.fields[ins.block[k]];counts[i]=fields[ins.block[k]]*f.scale+f.add
                if pc+size>end:raise ValueError('storage coordination instruction crosses body')
                self.code[pc]=codec.format(ins,fields),size,*counts
                if pc in ISA_SITES:
                    if ins.id!=ISA_SITES[pc]:raise ValueError('CPU observation opcode changed')
                    self.isa_records[hex(pc)]={'id':ins.id,'decoded':codec.format(ins,fields),'summary':ins.summary,
                        'notes':ins.notes,'status':ins.status,'sources':ins.sources}
                pc+=size
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                if self.code[pc+size][1]!=2 or '[' not in self.code[pc+size][0]:raise ValueError('coordination parallel packet changed')
                self.parallel_seconds.add(pc+size)
            if m:=re.fullmatch(r'call (-?\d+)',text):
                target=pc+size+int(m[1])
                if target not in self.code:
                    if target not in SERVICES:raise ValueError('unknown coordination platform target')
                    self.service_sites[pc]=(target,SERVICES[target])
            elif text.startswith('call '):raise ValueError('unreviewed coordination indirect call')
        validate_cpu_evidence(self)
        if self.service_sites!=DIRECT_SITES:raise ValueError('coordination platform call sites changed')
        s,e,digest=INITIAL_COUNTERS;self.initial_counters=region_bytes(app,s,e)
        if hashlib.sha256(self.initial_counters).hexdigest()!=digest:raise ValueError('IRQ initial RAM witness changed')
    def execute(self,memory,name,args=(),cpu=(0,0x01090700),boundary=None,events=None,service_budget=10000,event_budget=10000,step_budget=4000000):
        if name not in ARITIES or len(args)!=ARITIES[name] or tuple(map(len,memory))!=tuple(n for _,n in MAPPED):
            raise ValueError('coordination call domain')
        if len(cpu)!=2 or any(not 0<=v<=MASK32 for v in (*args,*cpu)):raise ValueError('coordination CPU/argument words')
        return StorageCoordinationMachine(self,memory,name,args,cpu,boundary,events,service_budget,event_budget,step_budget).run()

class StorageCoordinationMachine(EffectOwnershipMachine):
    def __init__(self,program,memory,name,args,cpu,boundary,events,service_budget,event_budget,step_budget):
        self.program,self.operation,self.boundary,self.events=program,name,boundary,events
        self.service_budget,self.event_budget,self.step_budget=service_budget,event_budget,step_budget
        self.cpu=list(cpu);self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory));self.pc=REGIONS[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set();self.entries={}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[];self.guard=0;self.stop_extra_overread=False;self.timeline=[]
        for i,v in enumerate(args):self.set(f'r{i}',v)
    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())+struct.pack('<II',*self.cpu)).hexdigest()
    def admit(self,event=True):
        if not (self.event_budget if event else self.service_budget):self.guard=-203;raise ObservationStop()
        if event:self.event_budget-=1
        else:self.service_budget-=1
    def observation(self,op,address=0,width=0,value=0):
        if self.events is None:raise ValueError('coordination requires explicit CPU events')
        before=self.digest();unchanged=tuple(self.cpu);self.events(op,address,width,value,self)
        if tuple(self.cpu)!=unchanged:raise ValueError('event callback modified CPU state')
        self.mmio_events.append((op,address,width,value,before,self.digest()));self.timeline.append(('event',len(self.mmio_events)-1))
    def read(self,a,n):return DotMachine.read(self,a,n)
    def write(self,a,v,n):
        if a+n>1<<32:raise ValueError('coordination map wraps')
        v&=(1<<(8*n))-1
        if not 0x30000000<=a<=a+n<=STACK+64:
            for (base,size),data in zip(MAPPED,self.public_memory):
                if base<=a<=a+n<=base+size:data[a-base:a-base+n]=v.to_bytes(n,'little');break
            else:raise ValueError(f'coordination public write unmapped {a:#x}/{n}')
        self.writes.append((a,v,n));DotMachine.write(self,a,v,n)
    def single_step(self):
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if text in ('cli','sti'):
            self.admit();self.cpu[1]=(self.cpu[1]&~0x200) if text=='cli' else self.cpu[1]|0x200
            self.observation(CLI if text=='cli' else STI,0,4,self.cpu[1]);self.pc=next_pc;return True
        if text=='csync':self.admit();self.observation(BARRIER);self.pc=next_pc;return True
        if m:=re.fullmatch(r'(r\d+) = cnum',text):
            self.admit();self.set(m[1],self.cpu[0]);self.observation(CNUM,0,4,self.cpu[0]);self.pc=next_pc;return True
        if m:=re.fullmatch(r'testset b\[(r\d+)\]',text):
            self.admit();address=self.value(m[1]);old=self.read(address,1);self.write(address,255,1)
            self.flags=old&15;self.carry=(old>>1)&1;self.observation(TESTSET,address,1,old);self.pc=next_pc;return True
        if m:=re.fullmatch(r'ifeq goto (-?\d+)',text):
            self.pc=next_pc+(int(m[1]) if self.flags&4 else 0);return True
        if m:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(u\)',text):
            divisor=self.value(m[3]);self.set(m[1],self.value(m[2])//divisor if divisor else 0);self.pc=next_pc;return True
        if m:=re.fullmatch(r'call (-?\d+)',text):
            target=next_pc+int(m[1])
            if target in self.program.code:self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            expected,count=self.program.service_sites[self.pc]
            if expected!=target or self.boundary is None:raise ValueError('coordination platform binding')
            self.admit(False);args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=self.digest();unchanged=tuple(self.cpu);value=self.boundary(target,args,self)&MASK32
            if tuple(self.cpu)!=unchanged:raise ValueError('platform callback modified CPU state')
            self.calls.append((target,args,before,self.digest(),value));self.timeline.append(('call',len(self.calls)-1))
            self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        return super().single_step()
    def run(self):
        try:
            while self.steps<self.step_budget:
                self.steps+=1
                if not self.step():break
            else:raise ValueError('coordination instruction budget exhausted')
        except ObservationStop:pass
        if not self.guard and (self.frames or self.returns or self.else_skips or self.value('sp')!=STACK):raise ValueError('coordination unbalanced return')
        return {'result':None if self.guard else (0 if self.operation in VOID else self.value('r0'),0),
            'status':self.guard,'memory':self.snapshot(),'cpu':tuple(self.cpu),'calls':self.calls,'events':self.mmio_events,
            'visited':self.visited,'steps':self.steps,'service_sites':self.service_sites,'timeline':self.timeline,
            'internal_calls':self.internal_calls,'stop_pc':self.pc}

class ObservationStop(Exception):pass
