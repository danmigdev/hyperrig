"""Execute original effect routing, teardown and ownership instructions.

The model follows decoded packets and shared byte memory. Only release callbacks
and the global refresh service remain explicit. An optional fourth-extra-pointer
stop records the real prefix before the original would read saved caller state.
"""
from __future__ import annotations
import re
from effect_parameter_resources_machine import (EffectParameterResourcesMachine,
    CounterRegion, ROOT, region_bytes, MAPPED, RAM, ARENA, STACK)
from dot_machine import DotMachine, MASK32
from pi32v2isa import codec, table

REGIONS = {
    'lookup':(0x0202de50,0x0202de8c), 'neighbors':(0x0202de8c,0x0202def2),
    'release':(0x0202df38,0x0202df9a), 'detach':(0x0202eabc,0x0202eb0c),
    'capture':(0x0202eb0c,0x0202eb4c), 'remove':(0x0202eb4c,0x0202ebe2),
    'groups':(0x0202ebe2,0x0202ec30), 'refresh':(0x0202ec30,0x0202ec54),
}
REUSED = {'reset_slot':(0x020290cc,0x02029112), 'counter':(0x01c05160,0x01c0516e)}
STATIC = {}
ARITIES = dict(lookup=2,neighbors=2,release=1,detach=1,capture=1,remove=1,groups=1,refresh=0)
VOID = {'neighbors','release','detach','capture','refresh'}
INDIRECT_ARITIES = {0x0202df84:1,0x0202df90:1,0x0202ebcc:1}
SERVICES = {0x02028eb2:1}

class EffectOwnershipProgram:
    def __init__(self):
        CounterRegion('counter')
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.code,self.regions,self.parallel_seconds,self.data={},{},set(),{}
        instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);cursor=0
            while cursor<len(raw):
                found=codec.decode(instructions,raw,cursor)
                if found is None:raise ValueError(f'undecoded ownership instruction {start+cursor:#x}')
                instruction,fields,size=found;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if start+cursor+size>end:raise ValueError('ownership instruction crosses complete region')
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts;cursor+=size
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? =',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed ownership parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,name,arguments=(),boundary=None,stop_extra_overread=False):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid ownership memory views')
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=x<=MASK32 for x in arguments):
            raise ValueError('invalid ownership ABI words')
        return EffectOwnershipMachine(self,memory,name,arguments,boundary,stop_extra_overread).run()

class EffectOwnershipMachine(EffectParameterResourcesMachine):
    def __init__(self,program,memory,name,arguments,boundary=None,stop_extra_overread=False):
        self.program,self.operation,self.boundary=program,name,boundary
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory))
        self.pc=REGIONS[name][0];self.carry=self.flags=self.steps=0
        self.frames,self.returns,self.calls,self.internal_calls,self.service_sites=[],[],[],[],[]
        self.writes,self.visited,self.else_skips=[],set(),{}
        self.written,self.entries=set(),{}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[]
        self.stop_extra_overread=stop_extra_overread;self.guard=0
        for i,value in enumerate(arguments):self.set(f'r{i}',value)

    def single_step(self):
        if self.pc==0x0202df8a and self.value('r6')>=self.value('sp')+12:
            if not self.stop_extra_overread:raise ValueError('extra count reads beyond three cached pointers')
            self.guard=-202;return False
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #')
        next_pc=self.pc+size
        if text=='csync':
            # Its single-threaded register/byte-memory state is unchanged.
            # No peripheral or inter-core ordering guarantee is modeled.
            self.pc=next_pc;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+) & ~\(1 << (r\d+)\)',text):
            # Pinned and.invbit.rrr semantics select the low five index bits.
            self.set(match[1],self.value(match[2])&~(1<<(self.value(match[3])&31)))
            self.pc=next_pc;return True
        if match:=re.fullmatch(r'call (r\d+|-?\d+)',text):
            indirect=match[1].startswith('r');target=self.value(match[1]) if indirect else next_pc+int(match[1])
            if not indirect and target in self.program.code:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            count=INDIRECT_ARITIES.get(self.pc) if indirect else SERVICES.get(target)
            if count is None or self.boundary is None:raise ValueError(f'unreviewed ownership service {self.pc:#x}/{target:#x}')
            args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=self.snapshot();preserved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
            value=self.boundary(target,args,self)&MASK32
            if any(self.value(r)!=v for r,v in preserved.items()):raise ValueError('ownership callback changed saved registers')
            self.calls.append((target,args,before,self.snapshot(),value));self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        return super().single_step()

    def run(self):
        while self.steps<4000000:
            self.steps+=1
            if not self.step():
                if not self.guard and (self.frames or self.returns or self.else_skips or self.value('sp')!=STACK):
                    raise ValueError('unbalanced ownership execution')
                return {'result':(0 if self.operation in VOID else self.value('r0'),0),
                    'status':self.guard,'memory':self.snapshot(),'calls':self.calls,'service_sites':self.service_sites,
                    'visited':set(self.visited),'steps':self.steps,'internal_calls':self.internal_calls,
                    'writes':self.writes,'stop_pc':self.pc}
        raise ValueError('ownership native instruction budget exhausted')
