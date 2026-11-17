"""Execute the original storage callers, driver and CPU coordination together.

The checked C derivatives add only explicit joins, private leases and shared
boundary accounting. The oracle executes original decoded packets in one CPU.
"""
from __future__ import annotations
import hashlib
import re
import struct
from preset_storage_preparation_machine import (PresetStoragePreparationProgram, PresetStoragePreparationMachine,
    REGIONS as PREPARATION, REUSED, ARITIES, VOID, ROOT, STATE, GLOBAL, ARENA, STACK, region_bytes)
from storage_control_machine import (StorageControlProgram, StorageControlMachine, REGIONS as CONTROL,
    STATIC, MMIO, DEVICE, READ, WRITE, BARRIER, FLUSH, mmio_span)
from storage_coordination_machine import (StorageCoordinationProgram, StorageCoordinationMachine,
    REGIONS as COORDINATION, CLI, STI, CNUM, TESTSET)
from dot_machine import DotMachine, MASK32

REGIONS = {}
ALL_REGIONS = {**{'preparation_'+n:v for n,v in PREPARATION.items()},
    **{'reused_'+n:v for n,v in REUSED.items()}, **{'control_'+n:v for n,v in CONTROL.items()},
    **{'coordination_'+n:v for n,v in COORDINATION.items()}}
MAPPED = ((GLOBAL,0x01c344b4-GLOBAL),(DEVICE,82),(ARENA,65568),(0,256),(0xffffff00,256))
JOINS = {
    0x02002876:(0x02002810,3),0x02002dc2:(0x02002772,0),0x02002dc6:(0x02002bcc,0),
    0x02002dd2:(0x02002786,1),0x02002de4:(0x02002b80,3),0x02002df2:(0x02002786,1),
    0x02002f36:(0x02002772,0),0x02002f3a:(0x02002bcc,0),0x02002f40:(0x02002786,1),
    0x02002f74:(0x02002ef2,4),0x02002fa2:(0x02002786,1),
    0x02002dcc:(0x02002d06,1),0x02002dee:(0x02002d70,3),0x02002e02:(0x02002d06,1),
    0x02002e12:(0x02002920,0),0x02002f9a:(0x02002d70,3),
    0x020034bc:(0x02002d10,3),0x0200795c:(0x02002d10,3),
}
PARENTS = {
    'firmware/src/hyperrig_preset_storage_preparation.c':'553d68066bc3337883cb02025c139dcdedc59f4649c60dba98e0e2629b8257cf',
    'firmware/src/hyperrig_storage_control.c':'7a7fdf7fcfb6bb4af30101694f0dd4a5dfd613661c9a097e59f3aeba0b026238',
    'firmware/src/hyperrig_storage_coordination.c':'8b38e68971db73c27c54eae0fbfe6daf6fef59c1c335c9780d0f713cf0db5aa3',
}


def insert_block(text, first, last):
    a=text.index(first); b=text.index(last,a)+len(last)
    if text.count(first)!=1 or text.count(last)!=1:raise ValueError('ambiguous owned bridge block')
    return text[a:b]


def derivative_sources():
    sources={}
    for name,digest in PARENTS.items():
        data=(ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('frozen storage parent changed')
        sources[name]=data.decode()
    name='firmware/src/hyperrig_storage_runtime_control.c';actual=(ROOT/name).read_text()
    text=sources['firmware/src/hyperrig_storage_control.c']
    text=text.replace('"hyperrig/hyperrig_storage_control.h"','"hyperrig/hyperrig_storage_runtime_internal.h"')
    text=text.replace('docs/STORAGE_CONTROL_RECONSTRUCTION.md','docs/STORAGE_RUNTIME_RECONSTRUCTION.md')
    text=text.replace('hyperrig_storage_control_io','hyperrig_storage_runtime_driver_io').replace('hyperrig_storage_control_execute','hyperrig_storage_runtime_driver_execute')
    text=text.replace('s->io->','s->io->platform.')
    for field in ('map','call','event','work_budget','service_budget'):
        text=text.replace('io->'+field,'io->platform.'+field)
    text=text.replace('if(a<UINT32_C(0x30001040)&&(uint64_t)a+n>UINT32_C(0x30000000)){s->status=-202;return NULL;}',
        '''if(a<UINT32_C(0x30001040)&&(uint64_t)a+n>UINT32_C(0x30000000)){
        p=s->io->private_map(s->io->platform.opaque,a,n,writable);
        if(!p)s->status=-202;
        return p;
    }''')
    extra=insert_block(actual,'/* BEGIN PUBLIC-ONLY DRIVER VIEW */','/* END PUBLIC-ONLY DRIVER VIEW */')
    text=text.replace('static uint64_t event(Access *s,',extra+'\nstatic uint64_t event(Access *s,')
    text=text.replace('view={map,s}','view={public_map,s}')
    text=text.replace('p=map(s,a,n,1);if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8u*i));',
        '''p=map(s,a,n,1);if(p){
        for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8u*i));
        if(a<UINT32_C(0x30001040)&&(uint64_t)a+n>UINT32_C(0x30000000))
            s->io->private_commit(s->io->platform.opaque,a,n);
    }''')
    text=text.replace('!io->platform.event)return -200;','!io->platform.event||!io->private_map||!io->private_commit)return -200;')
    if actual!=text:raise ValueError('driver derivative contains an unapproved substitution')
    name='firmware/src/hyperrig_storage_runtime.c';actual=(ROOT/name).read_text()
    text=sources['firmware/src/hyperrig_preset_storage_preparation.c']
    text=text.replace('"hyperrig/hyperrig_preset_storage_preparation.h"','"hyperrig/hyperrig_storage_runtime_internal.h"')
    text=text.replace('docs/PRESET_STORAGE_PREPARATION_RECONSTRUCTION.md','docs/STORAGE_RUNTIME_RECONSTRUCTION.md')
    text=text.replace('hyperrig_preset_storage_preparation_io','hyperrig_storage_runtime_io').replace('hyperrig_preset_storage_preparation_execute','hyperrig_storage_runtime_execute')
    text=text.replace('uint32_t sp,work,services,expose,expose_bytes;',
        'uint32_t sp,work,services,events,expose,expose_bytes;\n    hyperrig_storage_coordination_cpu *cpu;')
    text=text.replace('    if(!s->services){s->status=-203;return 0;}--s->services;\n','')
    a=text.index('static uint8_t *borrow(');b=text.index('static uint32_t service(',a)
    text=text[:a]+insert_block(actual,'/* BEGIN RUNTIME BRIDGE */','/* END RUNTIME BRIDGE */')+'\n'+text[b:]
    text=text.replace('view={borrow,s}','view={public_map,s}')
    text=text.replace('result=s->io->call(s->io->opaque,target,args,count,&view);',
        'if(!joined(s,site,target,args,&result))result=platform_call(s,target,args,count,&view);')
    text=text.replace('if(target==UINT32_C(0x0203c15c)&&result>=PRIVATE&&result<STACK+64u)s->status=-202;',
        'if(!s->status&&target==UINT32_C(0x0203c15c)&&result>=PRIVATE&&result<STACK+64u)s->status=-202;')
    text=text.replace('uint32_t result[2],const hyperrig_storage_runtime_io *io)',
        'uint32_t result[2],hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_runtime_io *io)')
    text=text.replace('!result||!io||!io->map||!io->call','!result||!cpu||!io||!io->map||!io->call||!io->event')
    text=text.replace('s.services=io->service_budget;s.status=0;',
        's.services=io->service_budget;s.events=io->event_budget;s.cpu=cpu;s.status=0;')
    if actual!=text:raise ValueError('preparation derivative contains an unapproved substitution')
    return {'parents':PARENTS,'checked_complete_derivatives':2,'unchanged_coordination_source':True,
        'allowed_changes':['distinct symbols and IO scaffolding','authenticated direct-call bridge',
            'active internal private lease','public-only callback views','completed-store initialization',
            'shared external service/event accounting and first-error propagation']}


class StorageRuntimeProgram:
    def __init__(self):
        self.derivation=derivative_sources()
        self.preparation=PresetStoragePreparationProgram();self.control=StorageControlProgram();self.coordination=StorageCoordinationProgram()
        self.code={};self.parallel_seconds=set();self.regions={};self.service_sites={}
        self.data=self.control.data;self.preparation_code=set(self.preparation.code);self.control_code=set(self.control.code)
        for module in (self.preparation,self.control,self.coordination):
            for pc,value in module.code.items():
                if pc in self.code and self.code[pc]!=value:raise ValueError('shared storage decoding differs')
                self.code[pc]=value
            self.parallel_seconds.update(module.parallel_seconds)
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        for name,(a,b) in ALL_REGIONS.items():self.regions[name]=region_bytes(app,a,b)
        if len(self.code)!=2283 or len(ALL_REGIONS)!=75:raise ValueError('storage runtime closure changed')
        for pc,(target,count) in JOINS.items():
            if self.preparation.service_sites.get(pc)!=(target,count):raise ValueError('storage incoming ABI changed')
            text,size,*_=self.code[pc]
            if text!=f'call {target-pc-size}' or target not in self.code:raise ValueError('storage direct join changed')
        for module in (self.preparation,self.control,self.coordination):
            for pc,value in module.service_sites.items():
                if pc not in JOINS:self.service_sites[pc]=value
        if len(self.service_sites)!=35:raise ValueError('storage platform closure changed')
    def execute(self,memory,name,args=(),cpu=(0,0x01090700),boundary=None,events=None,services=100000,event_budget=1000000,steps=20000000):
        if name not in ARITIES or len(args)!=ARITIES[name] or tuple(map(len,memory))!=tuple(n for _,n in MAPPED):
            raise ValueError('storage runtime ABI or mapped spans')
        if any(not 0<=v<=MASK32 for v in (*args,*cpu)) or len(cpu)!=2:raise ValueError('storage runtime uint32 inputs')
        return StorageRuntimeMachine(self,memory,name,args,cpu,boundary,events,services,event_budget,steps).run()


class RuntimeStop(Exception):pass


class StorageRuntimeMachine(StorageControlMachine,PresetStoragePreparationMachine,StorageCoordinationMachine):
    def __init__(self,p,memory,name,args,cpu,boundary,events,services,event_budget,steps):
        self.program,self.operation,self.boundary,self.events=p,name,boundary,events
        self.cpu=list(cpu);self.service_budget=services;self.event_budget=event_budget;self.step_budget=steps
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={a+i:v for (a,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        for name_,(a,b) in STATIC.items():self.memory.update({a+i:v for i,v in enumerate(p.data[name_])})
        self.public_memory=list(map(bytearray,memory));self.pc=PREPARATION[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set();self.entries={}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[];self.timeline=[];self.guard=0;self.stop_extra_overread=False
        self.callback=False;self.private_known=set();self.leases=[];self.join_returns=[];self.join_counts={}
        for i,v in enumerate(args):
            if i<4:self.set(f'r{i}',v)
            else:DotMachine.write(self,STACK+4*(i-4),v,4)
    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def digest(self):return hashlib.sha256(b''.join(self.snapshot())+struct.pack('<II',*self.cpu)).hexdigest()
    def stop(self,status):
        if not self.guard:self.guard=status
        raise RuntimeStop()
    def public_probe(self,a,n,writable=0):
        if 0x30000000<a+n and a<STACK+64:
            self.guard=self.guard or -202;return False
        if a+n>1<<32 or not any(base<=a<=a+n<=base+size for base,size in MAPPED):
            self.guard=self.guard or -201;return False
        return True
    def admit(self,event=True):
        if not (self.event_budget if event else self.service_budget):self.stop(-203)
        if event:self.event_budget-=1
        else:self.service_budget-=1
    def bus(self,op,a=0,n=0,value=0,admitted=False):
        if not admitted:self.admit()
        if self.events is None:raise ValueError('explicit runtime events required')
        before=self.digest();cpu=tuple(self.cpu);self.callback=True
        result=self.events(op,a,n,value,self)&((1<<64)-1);self.callback=False
        if tuple(self.cpu)!=cpu:raise ValueError('storage event mutated CPU state')
        self.mmio_events.append((op,a,n,value,result,before,self.digest()));self.timeline.append(('event',len(self.mmio_events)-1))
        if self.guard:raise RuntimeStop()
        return result
    def read(self,a,n):
        if self.callback:
            if not self.public_probe(a,n):self.stop(self.guard)
        elif mmio_span(a,n):return self.bus(READ,a,n)&((1<<(8*n))-1)
        if a+n>1<<32:self.stop(-201)
        if 0x30000000<=a<STACK:
            if self.pc in self.program.preparation_code and not all(a+i in self.private_known for i in range(n)):self.stop(-202)
            if self.pc in self.program.control_code and self.leases:
                lease=self.leases[-1]
                if a>=lease['sp'] and not (lease['a']<=a<=a+n<=lease['a']+lease['n']):self.stop(-202)
                if a>=lease['sp'] and not all(a+i in self.private_known for i in range(n)):self.stop(-202)
        try:return DotMachine.read(self,a,n)
        except ValueError:
            if 0x30000000<=a<STACK:self.stop(-202)
            self.stop(-201)
    def write(self,a,value,n):
        if self.callback:
            if not self.public_probe(a,n,1):self.stop(self.guard)
        elif mmio_span(a,n):self.bus(WRITE,a,n,value&((1<<(8*n))-1));return
        if a+n>1<<32:self.stop(-201)
        value&=(1<<(8*n))-1
        if 0x30000000<=a<=a+n<=STACK+64:
            if self.pc in self.program.preparation_code:self.private_known.update(range(a,a+n))
            elif self.pc in self.program.control_code and self.leases:
                lease=self.leases[-1]
                if a>=lease['sp']:
                    if not lease['write'] or not lease['a']<=a<=a+n<=lease['a']+lease['n']:self.stop(-202)
                    self.private_known.update(range(a,a+n))
        else:
            for (base,size),data in zip(MAPPED,self.public_memory):
                if base<=a<=a+n<=base+size:data[a-base:a-base+n]=value.to_bytes(n,'little');break
            else:self.stop(-201)
        self.writes.append((a,value,n));DotMachine.write(self,a,value,n)
    def single_step(self):
        if self.join_returns and self.pc==self.join_returns[-1][0] and len(self.returns)==self.join_returns[-1][1]:
            _,_,leased=self.join_returns.pop()
            if leased:self.leases.pop()
        text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if m:=re.fullmatch(r'call (-?\d+)',text):
            self.visited.add(self.pc);target=next_pc+int(m[1])
            if target in self.program.code:
                if self.pc in JOINS:
                    leased=target in (0x02002810,0x02002ef2)
                    self.join_returns.append((next_pc,len(self.returns),leased))
                    if leased:self.leases.append({'a':self.value('r1'),'n':self.value('r2'),'write':target==0x02002810,'sp':self.value('sp')})
                    self.join_counts[self.pc]=self.join_counts.get(self.pc,0)+1
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            expected,count=self.program.service_sites[self.pc]
            if expected!=target or self.boundary is None:raise ValueError('runtime platform site changed')
            self.admit(False);args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=self.digest();cpu=tuple(self.cpu);self.callback=True;value=self.boundary(target,args,self)&MASK32;self.callback=False
            if tuple(self.cpu)!=cpu:raise ValueError('storage platform mutated CPU state')
            self.calls.append((target,args,before,self.digest(),value));self.timeline.append(('call',len(self.calls)-1));self.service_sites.append((self.pc,target,count))
            if self.guard:raise RuntimeStop()
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if text in ('cli','sti') or text.endswith(' = cnum') or text.startswith('testset b[') or text.startswith('ifeq goto '):
            return StorageCoordinationMachine.single_step(self)
        if m:=re.fullmatch(r'sp \+= (-?\d+)',text):
            self.visited.add(self.pc);self.set('sp',self.value('sp')+int(m[1]));self.pc=next_pc;return True
        return super().single_step()
    def observation(self,op,address=0,width=0,value=0):self.bus(op,address,width,value,admitted=True)
    def run(self):
        try:
            while self.steps<self.step_budget:
                self.steps+=1
                if not self.step():break
            else:raise ValueError('storage runtime instruction budget exhausted')
        except RuntimeStop:pass
        if not self.guard and (self.frames or self.returns or self.else_skips or self.leases or self.join_returns or self.value('sp')!=STACK):
            raise ValueError('storage runtime unbalanced native return')
        return {'status':self.guard,'result':None if self.guard else (0 if self.operation in VOID else self.value('r0'),0),
            'memory':self.snapshot(),'cpu':tuple(self.cpu),'calls':self.calls,'events':self.mmio_events,'timeline':self.timeline,
            'visited':self.visited,'steps':self.steps,'stop_pc':self.pc,'join_counts':self.join_counts,
            'private_known':{hex(a):self.memory[a] for a in sorted(self.private_known)},'active_leases':self.leases,
            'services_remaining':self.service_budget,'events_remaining':self.event_budget}
