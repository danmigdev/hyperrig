"""Decode storage platform routines and the separate original peer interrupt.

The interrupt has a real special/general save frame and RTI completion. External
delivery, lock completion and MMIO values remain controlled observations.
"""
from __future__ import annotations
import hashlib
import json
import re
import struct
from storage_coordination_machine import StorageCoordinationMachine,ObservationStop
from effect_enable_machine import CounterRegion,region_bytes,ROOT
from dot_machine import DotMachine,MASK32
from pi32v2isa import codec,table

REGIONS={'gate_disable':(0x02000558,0x02000564),'gate_enable':(0x02000564,0x02000570),
 'register':(0x020005ac,0x02000604),'peer_stop':(0x01c010e4,0x01c01108),
 'enter':(0x01c01108,0x01c011c2),'peer_resume':(0x01c011c2,0x01c011da),
 'leave':(0x01c011da,0x01c01234),'interrupt':(0x01c041dc,0x01c04256),'clock':(0x01c04862,0x01c0486c)}
REUSED={'irq_enter':(0x01c00e2e,0x01c00e46),'irq_leave':(0x01c00e46,0x01c00e62)}
ARITIES=dict(gate_disable=0,gate_enable=0,register=4,peer_stop=1,enter=2,peer_resume=1,leave=0,interrupt=0,clock=0)
DIRECT_SITES={0x020005d0:0x02000558,0x02000600:0x02000564,0x01c0112e:0x01c00e2e,
 0x01c0117c:0x01c010e4,0x01c01188:0x01c00e2e,0x01c01208:0x01c011c2,0x01c0122c:0x01c00e46,
 0x01c041f4:0x01c00e2e,0x01c0424a:0x01c00e46}
INDIRECT_SITES={0x01c04230:1,0x01c04248:1}
GLOBAL,COMMAND,ACK,ARGUMENT,LOCK_COUNTS,IRQ_COUNTS,MODE,STACK=0x01c1f180,0x01c1fc40,0x01c1fc44,0x01c1fc48,0x01c1fc4c,0x01c1fc54,0x01c3748d,0x30001000
MAPPED=((GLOBAL,0x01c2030c-GLOBAL),(0x01c3743c,82),(0x01c7fc00,1024),(0x33000000,4096),(0,256),(0xffffff00,256))
MMIO=((0x10704,0x10708),(0x01eee000,0x01eee00c),(0x01eef100,0x01eef180),(0x01eef1a0,0x01eef1a8),(0x01eef300,0x01eef380))
READ,WRITE,BARRIER,CLI,STI,CNUM,TESTSET=1,2,3,5,6,7,8
ICFG_READ,ICFG_WRITE,LOCKSET,LOCKCLR,PUSH,POP,RTI=9,10,11,12,13,14,15
INITIAL_MAILBOX=(COMMAND,IRQ_COUNTS,'de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90')
ISA_SITES={0x02000558:'mov.r_sr',0x0200055e:'mov.sr_r',0x01c01150:'mov.r_sr',
 0x01c011a2:'lockset',0x01c0122a:'lockclr',0x01c041dc:'push.srl',0x01c041de:'push.rmask',
 0x01c0424e:'pop.rmask',0x01c04252:'pop.srl',0x01c04254:'rti',
 0x01c011c2:'if.ne.ri.s12',0x01c00e2e:'cli',0x01c00e5e:'sti'}
ISA_RECORD_SHA256={
 '0x2000558':'96c39792fc117678a252a3bbdb0965b6fca1cc46f3ec9531dc996ec86df9f831',
 '0x200055e':'8948fcb2999e71b7151303e34ccf1eee146fdf3b68cfe36a56f6160b7e6c90b2',
 '0x1c01150':'5c4f83609cb9b2b891a97d08988aa3b4d10aaf4a360e7fa287d905e7e2f82abf',
 '0x1c011a2':'398eef4f8687d73b1c0b5a1016f6705ce8d27414cd30a6a7a4ced119a6dbe236',
 '0x1c011c2':'84cdd167cef234fb73ddffdb1fad7e6e97f1ea6d09eb0da3dcfc2f9e203b66a5',
 '0x1c0122a':'ba742d566bcd5641fa6a6ec08be54f0e29e6c089d0f9bde7ddb85b80b54a3a68',
 '0x1c041dc':'9bf1c736d8843c44c13c44774381dfed3fe35952b0480f89cb98896588e44638',
 '0x1c041de':'db0e62b92425325e40866fd2bf89d1958d00c9c2c89be8b1aa2c0fc24fd762a6',
 '0x1c0424e':'b09b0f282aaa3dd705e969cccd6a3314210da105201ae678915c27ef2349450b',
 '0x1c04252':'6d82692ede6b632f707ddab144f932edf785a66e9b0d58262c18586845abb73a',
 '0x1c04254':'60b30bb88c378ca30c6c9ac72312b0840171c70490b5da28d0a6f788cde824ee',
 '0x1c00e2e':'6e7ec874c2902d32ad705a7b05ffc762bf45d9bf802d428ec530732caa437412',
 '0x1c00e5e':'864f15571e33e214e973e089ef6071d325403f5da9d0d39eac8f0c5dfed1cd6c'}

def bus_span(a,n):
    for x,y in MMIO:
        if a<y and a+n>x:return 1 if x<=a<=a+n<=y else -1
    return 0

def validate_cpu_evidence(p):
    if set(p.isa_records)!=set(ISA_RECORD_SHA256):raise ValueError('platform CPU evidence set changed')
    for key,digest in ISA_RECORD_SHA256.items():
        record=p.isa_records[key]
        if hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=digest:
            raise ValueError('platform pinned CPU record changed')
        if p.code[int(key,16)][0]!=record['decoded']:raise ValueError('platform CPU decode differs')

class StoragePlatformProgram:
    def __init__(self,check_evidence=True):
        CounterRegion('counter');app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();isa=table.load()
        self.code,self.regions,self.parallel_seconds,self.isa_records={},{},set(),{}
        for name,(a,b) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,a,b);pc=a
            while pc<b:
                found=codec.decode(isa,raw,pc-a)
                if found is None:raise ValueError('unknown storage platform instruction')
                ins,fields,n=found;counts=[0,0]
                if ins.block:
                    for i,key in enumerate(('then','else')):
                        f=ins.fields[ins.block[key]];counts[i]=fields[ins.block[key]]*f.scale+f.add
                if pc+n>b:raise ValueError('storage platform instruction crosses body')
                self.code[pc]=codec.format(ins,fields),n,*counts
                if pc in ISA_SITES:
                    if ins.id!=ISA_SITES[pc]:raise ValueError('storage platform CPU opcode changed')
                    self.isa_records[hex(pc)]={'id':ins.id,'decoded':codec.format(ins,fields),'summary':ins.summary,
                        'notes':ins.notes,'status':ins.status,'sources':ins.sources}
                pc+=n
        actual={};indirect={}
        for pc,(text,n,*_) in self.code.items():
            if text.endswith('  #'):
                if self.code[pc+n][1]!=2 or '[' not in self.code[pc+n][0]:raise ValueError('platform parallel packet changed')
                self.parallel_seconds.add(pc+n)
            if m:=re.fullmatch(r'call (-?\d+)',text):actual[pc]=pc+n+int(m[1])
            elif text.startswith('call '):
                if text!='call r1':raise ValueError('platform indirect register changed')
                indirect[pc]=1
        if actual!=DIRECT_SITES or indirect!=INDIRECT_SITES:raise ValueError('platform complete call registry changed')
        if check_evidence:validate_cpu_evidence(self)
        a,b,digest=INITIAL_MAILBOX;self.initial_mailbox=region_bytes(app,a,b)
        if hashlib.sha256(self.initial_mailbox).hexdigest()!=digest:raise ValueError('platform mutable startup witness changed')
        if sum(len(v) for n,v in self.regions.items() if n in REGIONS)!=580 or len(self.code)!=217:
            raise ValueError('platform whole-body closure changed')
    def execute(self,memory,name,args=(),cpu=(0,0x01090700),context=None,boundary=None,events=None,
            services=10000,event_budget=10000,steps=4000000):
        if name not in ARITIES or len(args)!=ARITIES[name] or tuple(map(len,memory))!=tuple(n for _,n in MAPPED):
            raise ValueError('platform mapped ABI')
        if len(cpu)!=2 or any(not 0<=v<=MASK32 for v in (*args,*cpu)):raise ValueError('platform CPU/input words')
        if (context is None)!=(name!='interrupt') or context is not None and (len(context)!=19 or any(not 0<=v<=MASK32 for v in context)):
            raise ValueError('separate explicit interrupt context required')
        return StoragePlatformMachine(self,memory,name,args,cpu,context,boundary,events,services,event_budget,steps).run()

class StoragePlatformMachine(StorageCoordinationMachine):
    def __init__(self,p,memory,name,args,cpu,context,boundary,events,services,event_budget,steps):
        self.program,self.operation,self.boundary,self.events=p,name,boundary,events
        self.service_budget,self.event_budget,self.step_budget=services,event_budget,steps
        self.cpu=list(cpu);self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory));self.pc=REGIONS[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set();self.entries={}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[];self.guard=0;self.stop_extra_overread=False;self.timeline=[]
        self.callback=False;self.interrupt_context=context;self.rti=False;self.special={'rets':0,'reti':0}
        if context is not None:
            for i in range(16):self.set(f'r{i}',context[i])
            self.flags=context[16]&15;self.carry=(self.flags>>1)&1
            self.special={'rets':context[17]&0x07fffffe,'reti':context[18]&0x07fffffe}
        for i,v in enumerate(args):self.set(f'r{i}',v)
    def stop(self,status):
        if not self.guard:self.guard=status
        raise ObservationStop()
    def public_probe(self,a,n,writable=0):
        if a<STACK+64 and a+n>0x30000000:self.guard=self.guard or -202;return False
        if a+n>1<<32 or bus_span(a,n) or not any(x<=a<=a+n<=x+y for x,y in MAPPED):
            self.guard=self.guard or -201;return False
        return True
    def bus(self,op,a=0,n=0,value=0,admitted=False):
        if not admitted:self.admit()
        if self.events is None:raise ValueError('platform explicit events required')
        before=self.digest();unchanged=tuple(self.cpu);self.callback=True
        result=self.events(op,a,n,value,self)&((1<<64)-1);self.callback=False
        if tuple(self.cpu)!=unchanged:raise ValueError('platform callback mutated CPU')
        self.mmio_events.append((op,a,n,value,result,before,self.digest()));self.timeline.append(('event',len(self.mmio_events)-1))
        if self.guard:raise ObservationStop()
        return result
    def observation(self,op,address=0,width=0,value=0):self.bus(op,address,width,value,True)
    def read(self,a,n):
        if self.callback:
            if not self.public_probe(a,n):self.stop(self.guard)
        elif bus_span(a,n):
            if bus_span(a,n)<0 or self.pc in range(0x01c00e2e,0x01c00e62):self.stop(-201)
            return self.bus(READ,a,n)&((1<<(8*n))-1)
        if a+n>1<<32:self.stop(-201)
        # Actual IRQ PUSH/POP use DotMachine directly. Ordinary raw address
        # arithmetic must not borrow a populated saved frame as public RAM.
        if a<STACK+64 and a+n>0x30000000:self.stop(-202)
        try:return DotMachine.read(self,a,n)
        except ValueError:self.stop(-202 if 0x30000000<=a<STACK+64 else -201)
    def write(self,a,v,n):
        if self.callback:
            if not self.public_probe(a,n,1):self.stop(self.guard)
        elif bus_span(a,n):
            if bus_span(a,n)<0 or self.pc in range(0x01c00e2e,0x01c00e62):self.stop(-201)
            self.bus(WRITE,a,n,v&((1<<(8*n))-1));return
        if a+n>1<<32:self.stop(-201)
        if a<STACK+64 and a+n>0x30000000:self.stop(-202)
        v&=(1<<(8*n))-1
        if not 0x30000000<=a<=a+n<=STACK+64:
            for (base,size),data in zip(MAPPED,self.public_memory):
                if base<=a<=a+n<=base+size:data[a-base:a-base+n]=v.to_bytes(n,'little');break
            else:self.stop(-201)
        self.writes.append((a,v,n));DotMachine.write(self,a,v,n)
    def single_step(self):
        self.visited.add(self.pc);text,n,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+n
        if m:=re.fullmatch(r'(r\d+) = icfg',text):
            self.admit();self.set(m[1],self.cpu[1]);self.observation(ICFG_READ,0,4,self.cpu[1]);self.pc=next_pc;return True
        if m:=re.fullmatch(r'icfg = (r\d+)',text):
            self.admit();self.cpu[1]=self.value(m[1]);self.observation(ICFG_WRITE,0,4,self.cpu[1]);self.pc=next_pc;return True
        if text in ('lockset','lockclr'):
            self.bus(LOCKSET if text=='lockset' else LOCKCLR);self.pc=next_pc;return True
        if self.pc in (0x01c041dc,0x01c041de,0x01c0424e,0x01c04252):
            self.admit()
            if self.pc==0x01c041dc:
                at=self.value('sp')-12;self.set('sp',at)
                for i,v in enumerate((self.special['reti'],self.special['rets'],self.flags&15)):DotMachine.write(self,at+4*i,v,4)
                self.flags=self.carry=0;self.observation(PUSH,at,12,0x10029)
            elif self.pc==0x01c041de:
                at=self.value('sp')-20;self.set('sp',at)
                for i in range(5):DotMachine.write(self,at+4*i,self.value(f'r{i}'),4)
                self.observation(PUSH,at,20,31)
            elif self.pc==0x01c0424e:
                at=self.value('sp')
                for i in range(5):self.set(f'r{i}',DotMachine.read(self,at+4*i,4))
                self.set('sp',at+20);self.observation(POP,at,20,31)
            else:
                at=self.value('sp');self.special['reti']=DotMachine.read(self,at,4)&0x07fffffe
                self.special['rets']=DotMachine.read(self,at+4,4)&0x07fffffe
                self.flags=DotMachine.read(self,at+8,4)&15;self.carry=(self.flags>>1)&1
                self.set('sp',at+12);self.observation(POP,at,12,0x10029)
            self.pc=next_pc;return True
        if text=='rti':
            self.admit();self.observation(RTI,self.special['reti']);self.rti=True;self.pc=self.special['reti'];return False
        if m:=re.fullmatch(r'call (r\d+|-?\d+)',text):
            indirect=m[1].startswith('r');target=self.value(m[1]) if indirect else next_pc+int(m[1])
            self.special['rets']=next_pc&0x07fffffe
            if not indirect:
                if DIRECT_SITES.get(self.pc)!=target:raise ValueError('platform direct ABI changed')
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            if self.pc not in INDIRECT_SITES or self.boundary is None:raise ValueError('platform indirect site changed')
            self.admit(False);args=(self.value('r0'),)+(0,)*11;before=self.digest();cpu=tuple(self.cpu)
            preserved=tuple(self.value(f'r{i}') for i in range(4,16));self.callback=True
            value=self.boundary(target,args,self)&MASK32;self.callback=False
            if tuple(self.cpu)!=cpu:raise ValueError('platform service mutated CPU')
            if preserved!=tuple(self.value(f'r{i}') for i in range(4,16)):raise ValueError('platform callback changed callee-saved registers')
            self.calls.append((target,args,before,self.digest(),value));self.timeline.append(('call',len(self.calls)-1));self.service_sites.append((self.pc,target,1))
            if self.guard:raise ObservationStop()
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        return super().single_step()
    def run(self):
        try:
            while self.steps<self.step_budget:
                self.steps+=1
                if not self.step():break
            else:raise ValueError('platform native instruction budget exhausted')
        except ObservationStop:pass
        if not self.guard and (self.frames or self.returns or self.else_skips or self.value('sp')!=STACK):
            raise ValueError('unbalanced platform native completion')
        if not self.guard and self.rti!=(self.operation=='interrupt'):raise ValueError('IRQ return kind changed')
        context=None
        if self.rti:context=tuple(self.value(f'r{i}') for i in range(16))+(self.flags,self.special['rets'],self.special['reti'])
        return {'status':self.guard,'result':None if self.guard else (self.value('r0') if self.operation=='clock' else 0,0),
            'context':context,'memory':self.snapshot(),'cpu':tuple(self.cpu),'calls':self.calls,'events':self.mmio_events,'timeline':self.timeline,
            'visited':self.visited,'steps':self.steps,'service_sites':self.service_sites,'stop_pc':self.pc,
            'interrupt_frame':bytes(self.memory.get(a,0) for a in range(STACK-32,STACK)),
            'services_remaining':self.service_budget,'events_remaining':self.event_budget}
