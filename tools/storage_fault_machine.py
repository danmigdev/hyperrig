"""Decode complete diagnostic-record and register-control bodies offline."""
from __future__ import annotations
import hashlib
import json
import re
from storage_coordination_machine import StorageCoordinationMachine,ObservationStop
from effect_enable_machine import CounterRegion,region_bytes,ROOT
from dot_machine import DotMachine,MASK32
from pi32v2isa import codec,table

REGIONS={'tag':(0x02000730,0x02000758),'record_count':(0x02000758,0x0200077c),
 'append':(0x0200077c,0x02000800),'checksum':(0x02000800,0x02000830),
 'decode':(0x02000830,0x0200088e),'encode':(0x0200088e,0x020008ee),
 'update':(0x020008ee,0x02000952),'once':(0x02000952,0x0200096e),
 'fatal':(0x0200096e,0x020009ca),'acquire':(0x01c00e86,0x01c00e9c),
 'exchange':(0x01c00e9c,0x01c00eb6),'release':(0x01c00eb6,0x01c00ec8),
 'read_register':(0x01c00ec8,0x01c00f0c),'write_register':(0x01c00f0c,0x01c00f4a),
 'masked_register':(0x01c00f4a,0x01c00f72)}
REUSED={'irq_enter':(0x01c00e2e,0x01c00e46),'irq_leave':(0x01c00e46,0x01c00e62)}
ARITIES=dict(tag=1,record_count=0,append=1,checksum=3,decode=1,encode=1,update=2,once=1,
 fatal=0,acquire=0,exchange=1,release=0,read_register=1,write_register=2,masked_register=4)
SCALAR={'tag','record_count','checksum','decode','exchange','read_register'}
DIRECT_SITES={0x02000782:0x02000730,0x02000786:0x02000758,0x02000846:0x02000800,
 0x020008e2:0x02000800,0x020008f6:0x02000830,0x0200090e:0x0200088e,0x0200096a:0x020008ee,
 0x0200097e:0x0200077c,0x02000984:0x02000952,0x020009c2:0x01c00f4a,
 0x01c00e88:0x01c00e2e,0x01c00ec4:0x01c00e46,0x01c00ece:0x01c00e86,
 0x01c00ef0:0x01c00e9c,0x01c00ef6:0x01c00e9c,0x01c00efa:0x01c00e9c,
 0x01c00f06:0x01c00eb6,0x01c00f14:0x01c00e86,0x01c00f32:0x01c00e9c,
 0x01c00f38:0x01c00e9c,0x01c00f3c:0x01c00e9c,0x01c00f46:0x01c00eb6,
 0x01c00f62:0x01c00ec8,0x01c00f6e:0x01c00f0c}
GLOBAL,STATE,IRQ_COUNTS,LOCK,HEADER,RECORDS,METADATA,CURRENT,STACK=(
 0x01c1f180,0x01c26890,0x01c1fc54,0x01c1fa2c,0x01c7fba0,0x01c7fba4,0x01c7fbd4,0x01c7fdd8,0x30001000)
MAPPED=((GLOBAL,0x01c1fca0-GLOBAL),(STATE,112),(0x01c7fb80,0x280),(0x33000000,512),(0,256),(0xffffff00,256))
CONTROL,DATA=0x13e08,0x13e0c
MMIO=((CONTROL,DATA+4),(0x01eef07c,0x01eef080),(0x01eef27c,0x01eef280))
READ,WRITE,BARRIER,CLI,STI,CNUM,TESTSET,RETS=1,2,3,5,6,7,8,17
HALT=0x020009c8
INCOMING=(0x02002b7a,0x02002b7e,0x0200096e)
INITIAL_LOCK=(LOCK,LOCK+4,'df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119')
ISA_SITES={0x0200096e:'mov.r_sr',0x02000972:'mov.r_sr',0x01c00e2e:'cli',0x01c00e30:'mov.r_sr',
 0x01c00e5e:'sti',0x01c00e92:'testset.b',0x01c00e94:'bc.eq',
 0x01c00ecc:'ext.l.s',0x01c00f12:'ext.l.s',0x01c00ea4:'rmw.or.modimm',
 0x01c00eda:'rmw.and.nmodimm',0x01c00ee4:'rmw.or.r',0x01c00f00:'rmw.and.r'}
ISA_RECORD_SHA256={
 '0x200096e':'8090ea6ed09d708b0ea9a0c1f76cbcedcab50a9769242f29756e781821908031',
 '0x2000972':'d424d7de3623e8607ff30e7a0a65ad801c598e98d2c351114a5124e19e0e0c57',
 '0x1c00e92':'690e07f7700b22f965e8ee6245800c96e51f72367eea607c544a9c1b381157e5',
 '0x1c00e94':'ce1e6bda6e2c86ca7013f074a95af16da363605e436e16ae6d02a5b11e3d1a2d',
 '0x1c00e2e':'6e7ec874c2902d32ad705a7b05ffc762bf45d9bf802d428ec530732caa437412',
 '0x1c00e30':'1d54e052c2a0213eab323479d7973744f67f21c15e157db4def336f08a7dfc8d',
 '0x1c00e5e':'864f15571e33e214e973e089ef6071d325403f5da9d0d39eac8f0c5dfed1cd6c',
 '0x1c00ecc':'54ad79f88cbc07550a9514f550e96b84bc834474cd2692e27d25ae1e177ba825',
 '0x1c00f12':'e0b965d897ba89d88149997939c84ff35c972ce98333bcb86533f405cfd2bdce',
 '0x1c00ea4':'92ae788ac2a6e4da934832099fb072dec4aa36132445c4e9d9185fbfefcd776d',
 '0x1c00eda':'311918e3125c8e8f67aa348287bfc409cca97a6c7e97331b4aa6f9b0cd64dffe',
 '0x1c00ee4':'d631f77a8197d5ed0a58a58bfbb5f83898a4b98d3b24d11b20c6d4f48c90b6a8',
 '0x1c00f00':'93cfcf9a47a056a8940c124886015749deea793608aeca84b1beac44a6dfd1bd'}

def bus_span(a,n):
    for x,y in MMIO:
        if a<y and a+n>x:return 1 if x<=a<=a+n<=y else -1
    return 0

def validate_cpu_evidence(p):
    if set(p.isa_records)!=set(ISA_RECORD_SHA256):raise ValueError('fault CPU evidence set changed')
    for key,digest in ISA_RECORD_SHA256.items():
        record=p.isa_records[key]
        if hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=digest:
            raise ValueError('fault CPU primary evidence changed')
        if p.code[int(key,16)][0]!=record['decoded']:raise ValueError('fault CPU decode changed')

class StorageFaultProgram:
    def __init__(self,check_evidence=True):
        CounterRegion('counter');app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();isa=table.load()
        self.code,self.regions,self.parallel_seconds,self.isa_records={},{},set(),{}
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);pc=start
            while pc<end:
                found=codec.decode(isa,raw,pc-start)
                if found is None:raise ValueError('undecoded fault instruction')
                ins,fields,size=found;counts=[0,0]
                if ins.block:
                    for i,k in enumerate(('then','else')):
                        f=ins.fields[ins.block[k]];counts[i]=fields[ins.block[k]]*f.scale+f.add
                if pc+size>end:raise ValueError('fault instruction crosses complete body')
                self.code[pc]=codec.format(ins,fields),size,*counts
                if pc in ISA_SITES:
                    if ins.id!=ISA_SITES[pc]:raise ValueError('fault CPU opcode changed')
                    self.isa_records[hex(pc)]={'id':ins.id,'decoded':codec.format(ins,fields),'summary':ins.summary,
                        'notes':ins.notes,'status':ins.status,'sources':ins.sources}
                pc+=size
        actual={}
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                if self.code[pc+size][1]!=2 or '[' not in self.code[pc+size][0]:raise ValueError('fault parallel packet changed')
                self.parallel_seconds.add(pc+size)
            if m:=re.fullmatch(r'call (-?\d+)',text):actual[pc]=pc+size+int(m[1])
            elif text.startswith('call '):raise ValueError('unreviewed fault indirect call')
        if actual!=DIRECT_SITES:raise ValueError('fault direct call registry changed')
        if check_evidence:validate_cpu_evidence(self)
        a,b,target=INCOMING;self.incoming_bytes=region_bytes(app,a,b);ins,fields,size=codec.decode(isa,self.incoming_bytes,0)
        self.incoming_instruction=codec.format(ins,fields)
        if size!=b-a or self.incoming_instruction!=f'call {target-b}':raise ValueError('fault incoming storage edge changed')
        a,b,digest=INITIAL_LOCK;self.initial_lock=region_bytes(app,a,b)
        if hashlib.sha256(self.initial_lock).hexdigest()!=digest:raise ValueError('fault mutable lock evidence changed')
        if len(self.code)!=332 or sum(len(self.regions[n]) for n in REGIONS)!=902:raise ValueError('fault complete registry changed')
    def execute(self,memory,name,args=(),cpu=(0,0x01090700),caller=INCOMING[1],events=None,event_budget=10000,steps=4000000):
        if name not in ARITIES or len(args)!=ARITIES[name] or tuple(map(len,memory))!=tuple(n for _,n in MAPPED):
            raise ValueError('fault mapped ABI')
        if len(cpu)!=2 or any(not 0<=v<=MASK32 for v in (*args,*cpu,caller)):raise ValueError('fault CPU/input words')
        return StorageFaultMachine(self,memory,name,args,cpu,caller,events,event_budget,steps).run()

class StorageFaultMachine(StorageCoordinationMachine):
    def __init__(self,p,memory,name,args,cpu,caller,events,event_budget,steps):
        self.program,self.operation,self.boundary,self.events=p,name,None,events
        self.service_budget,self.event_budget,self.step_budget=0,event_budget,steps
        self.cpu=list(cpu);self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory));self.pc=REGIONS[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set();self.entries={}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[];self.guard=0;self.stop_extra_overread=False;self.timeline=[]
        self.callback=False;self.rets=caller&0x07fffffe;self.fatal=False;self.codec_private=None
        for i,v in enumerate(args):self.set(f'r{i}',v)
    def stop(self,status):
        if not self.guard:self.guard=status
        raise ObservationStop()
    def public_probe(self,a,n,writable=0):
        if a+n>1<<32:self.guard=self.guard or -201;return False
        if a<STACK+64 and a+n>0x30000000:self.guard=self.guard or -202;return False
        if bus_span(a,n) or not any(x<=a<=a+n<=x+y for x,y in MAPPED):self.guard=self.guard or -201;return False
        return True
    def bus(self,op,a=0,n=0,value=0,admitted=False):
        if not admitted:self.admit()
        if self.events is None:raise ValueError('fault explicit events required')
        before=self.digest();unchanged=tuple(self.cpu);self.callback=True
        result=self.events(op,a,n,value,self)&((1<<64)-1);self.callback=False
        if tuple(self.cpu)!=unchanged:raise ValueError('fault callback mutated CPU')
        self.mmio_events.append((op,a,n,value,result,before,self.digest()));self.timeline.append(('event',len(self.mmio_events)-1))
        if self.guard:raise ObservationStop()
        return result
    def observation(self,op,address=0,width=0,value=0):self.bus(op,address,width,value,True)
    def private_access(self,a,n):
        text=self.program.code[self.pc][0]
        if '[sp' in text and 0x020008ee<=self.pc<0x02000952:return True
        if self.codec_private and any(s<=self.pc<e for s,e in (REGIONS['decode'],REGIONS['encode'])):
            x,y=self.codec_private;return x<=a<=a+n<=y
        return False
    def read(self,a,n):
        if self.callback:
            if not self.public_probe(a,n):self.stop(self.guard)
        elif bus_span(a,n):
            if bus_span(a,n)<0 or 0x01c00e2e<=self.pc<0x01c00e62:self.stop(-201)
            return self.bus(READ,a,n)&((1<<(8*n))-1)
        if a+n>1<<32:self.stop(-201)
        if a<STACK+64 and a+n>0x30000000 and not self.private_access(a,n):self.stop(-202)
        try:return DotMachine.read(self,a,n)
        except ValueError:self.stop(-202 if 0x30000000<=a<STACK+64 else -201)
    def write(self,a,v,n):
        if self.callback:
            if not self.public_probe(a,n,1):self.stop(self.guard)
        elif bus_span(a,n):
            if bus_span(a,n)<0 or 0x01c00e2e<=self.pc<0x01c00e62:self.stop(-201)
            self.bus(WRITE,a,n,v&((1<<(8*n))-1));return
        if a+n>1<<32:self.stop(-201)
        v&=(1<<(8*n))-1
        if a<STACK+64 and a+n>0x30000000:
            if not self.private_access(a,n):self.stop(-202)
        else:
            for (base,size),data in zip(MAPPED,self.public_memory):
                if base<=a<=a+n<=base+size:data[a-base:a-base+n]=v.to_bytes(n,'little');break
            else:self.stop(-201)
        self.writes.append((a,v,n));DotMachine.write(self,a,v,n)
    def single_step(self):
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if self.pc in (0x020008f8,0x02000910):self.codec_private=None
        if self.pc==HALT:self.fatal=True;return False
        if m:=re.fullmatch(r'(r\d+) = rets',text):
            self.admit();self.set(m[1],self.rets);self.observation(RETS,0,4,self.rets);self.pc=next_pc;return True
        if m:=re.fullmatch(r'(r\d+) = (r\d+)\.l \(s\)',text):
            value=self.value(m[2])&65535
            self.set(m[1],value-65536 if value&32768 else value)
            self.flags=(self.flags&3)|(8 if value&32768 else 0)|(4 if not value else 0)
            self.pc=next_pc;return True
        if m:=re.fullmatch(r'\[(r\d+)\+(-?\d+)\] ([&|])= (0x[0-9A-F]+|r\d+)',text):
            address=(self.value(m[1])+int(m[2]))&MASK32;value=self.read(address,4)
            mask=int(m[4],16) if m[4].startswith('0x') else self.value(m[4])
            self.write(address,value&mask if m[3]=='&' else value|mask,4);self.pc=next_pc;return True
        if m:=re.fullmatch(r'call (-?\d+)',text):
            target=next_pc+int(m[1])
            if DIRECT_SITES.get(self.pc)!=target:raise ValueError('fault direct site authentication failed')
            if self.pc in (0x020008f6,0x0200090e):self.codec_private=(self.value('r0'),self.value('r0')+12)
            self.rets=next_pc&0x07fffffe;self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
        return super().single_step()
    def run(self):
        try:
            while self.steps<self.step_budget:
                self.steps+=1
                if not self.step():break
            else:raise ValueError('fault original instruction budget exhausted')
        except ObservationStop:pass
        if not self.guard and not self.fatal and (self.frames or self.returns or self.else_skips or self.value('sp')!=STACK):
            raise ValueError('fault unbalanced native return')
        status=self.guard or (1 if self.fatal else 0)
        return {'status':status,'result':None if status else (self.value('r0') if self.operation in SCALAR else 0,0),
            'memory':self.snapshot(),'cpu':tuple(self.cpu),'calls':self.calls,'events':self.mmio_events,'timeline':self.timeline,
            'visited':self.visited,'steps':self.steps,'stop_pc':self.pc,'internal_calls':self.internal_calls,
            'events_remaining':self.event_budget,'fatal_observation':self.fatal}
