"""Execute nine original IR lifecycle bodies and six recovered helpers.

Native instructions, call-site ABI, parallel packets and shared byte memory
supply the independent reference. Prepare, construct and platform callbacks
remain explicit; no C reconstruction supplies native expected results.
"""
from __future__ import annotations
import re
from effect_parameter_resources_machine import (EffectParameterResourcesMachine,
    CounterRegion, ROOT, region_bytes, MAPPED, RAM, ARENA, STACK)
from dot_machine import DotMachine, MASK32, signed
from effect_construction_machine import EffectConstructionMachine
from pi32v2isa import codec, table

REGIONS = {
    'mode_prepare':(0x02029728,0x0202976a), 'temporary':(0x0202976a,0x0202983a),
    'select_source':(0x0202983a,0x020298ce), 'refresh':(0x020298ce,0x02029920),
    'assign':(0x02029920,0x02029ae6), 'assign_direct':(0x02029ae6,0x02029afc),
    'owns':(0x02029afc,0x02029b2e), 'construct_copy':(0x02031bf8,0x02031c16),
    'relocate':(0x02031c16,0x02031c64),
}
REUSED = {'mode_callback':(0x01c05ec6,0x01c05ed6), 'clamp':(0x01c05eb0,0x01c05ec6),
    'trim':(0x020294ce,0x0202957e), 'counter':(0x01c05160,0x01c0516e),
    'scaled_exp':(0x01c0516e,0x01c05182), 'exp':(0x020285d4,0x02028646)}
STATIC = {}
ARITIES = dict(mode_prepare=1,temporary=8,select_source=1,refresh=1,assign=7,
    assign_direct=5,owns=1,construct_copy=3,relocate=2)
VOID = {'relocate'}
INDIRECT_ARITIES = {0x01c05ed2:1,0x020297ac:1,0x020297c8:4,0x020297d2:1,
    0x02029996:1,0x02029ac8:1,0x02029ad6:1}
SERVICES = {0x0202962a:2,0x020318a8:4}
ABI_REGIONS = {'prepare':(0x0202962a,0x02029728),'construct':(0x020318a8,0x02031bf8)}

class ObservationStop(Exception):
    """An explicit native PC observation, independent of portable budgets."""

class IrEffectLifecycleProgram:
    def __init__(self):
        CounterRegion('counter')
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.code,self.regions,self.parallel_seconds,self.data={},{},set(),{}
        instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);cursor=0
            while cursor<len(raw):
                found=codec.decode(instructions,raw,cursor)
                if found is None:raise ValueError(f'undecoded IR lifecycle instruction {start+cursor:#x}')
                instruction,fields,size=found;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if start+cursor+size>end:raise ValueError('IR lifecycle instruction crosses complete region')
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts;cursor+=size
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? =',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed IR lifecycle parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,name,arguments=(),boundary=None,stop=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid IR lifecycle memory views')
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=x<=MASK32 for x in arguments):
            raise ValueError('invalid IR lifecycle ABI words')
        return IrEffectLifecycleMachine(self,memory,name,arguments,boundary,stop).run()

class IrEffectLifecycleMachine(EffectConstructionMachine):
    def __init__(self,program,memory,name,arguments,boundary=None,stop=None):
        self.program,self.operation,self.boundary=program,name,boundary
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory))
        self.pc=REGIONS[name][0];self.carry=self.flags=self.steps=0
        self.frames,self.returns,self.calls,self.internal_calls,self.service_sites=[],[],[],[],[]
        self.writes,self.visited,self.else_skips=[],set(),{}
        self.written,self.entries=set(),{}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[]
        self.guard=0
        self.stop,self.stop_visits=stop,0
        for i,value in enumerate(arguments):
            if i<4:self.set(f'r{i}',value)
            else:DotMachine.write(self,STACK+4*(i-4),value,4)

    read=EffectParameterResourcesMachine.read
    write=EffectParameterResourcesMachine.write
    snapshot=EffectParameterResourcesMachine.snapshot

    def single_step(self):
        if self.stop and self.pc==self.stop[0]:
            occurrence=self.stop_visits;self.stop_visits+=1
            if occurrence==self.stop[1]:raise ObservationStop
        self.visited.add(self.pc);text,size,then,otherwise=self.program.code[self.pc];text=text.removesuffix('  #')
        next_pc=self.pc+size
        if match:=re.fullmatch(r'call (r\d+|-?\d+)',text):
            indirect=match[1].startswith('r');target=self.value(match[1]) if indirect else next_pc+int(match[1])
            if not indirect and target in self.program.code:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            count=INDIRECT_ARITIES.get(self.pc) if indirect else SERVICES.get(target)
            if count is None or self.boundary is None:raise ValueError(f'unreviewed IR lifecycle service {self.pc:#x}/{target:#x}')
            args=tuple(self.value(f'r{i}') if i<4 else self.read(self.value('sp')+4*(i-4),4) for i in range(count))+(0,)*(12-count)
            before=self.snapshot();preserved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
            value=self.boundary(target,args,self)&MASK32
            if any(self.value(r)!=v for r,v in preserved.items()):raise ValueError('IR lifecycle callback changed saved registers')
            self.calls.append((target,args,before,self.snapshot(),value));self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if match:=re.fullmatch(r'h\[(.+)\] = (r\d+)',text):
            self.write(self.address(match[1]),self.value(match[2]),2)
        elif match:=re.fullmatch(r'(r\d+) = abs\((r\d+)\)',text):
            self.set(match[1],abs(signed(self.value(match[2]))))
        elif match:=re.fullmatch(r'(r\d+) = (umax|umin)\((r\d+), (r\d+)\)',text):
            self.set(match[1],(max if match[2]=='umax' else min)(self.value(match[3]),self.value(match[4])))
        elif match:=re.fullmatch(r'(r\d+) (\+=|-=) (r\d+|-?\d+)',text):
            self.set(match[1],self.binary(self.value(match[1]),match[2][0],self.value(match[3])))
        elif match:=re.fullmatch(r'(r\d+) = psr',text):
            self.set(match[1],self.carry<<1)
        elif match:=re.fullmatch(r'(r\d+) = sextra\((r\d+), p:(\d+), l:(\d+)\)',text):
            length=int(match[4]);self.set(match[1],signed(self.value(match[2])>>int(match[3])&((1<<length)-1),length))
        elif match:=re.fullmatch(r'if \(\((r\d+) & (r\d+)\) (==|!=) 0\) \{',text):
            condition=bool(self.value(match[1])&self.value(match[2]))==(match[3]=='!=')
            if not condition:next_pc=self.skip(next_pc,then)
            elif otherwise:self.else_skips[self.skip(next_pc,then)]=self.skip(self.skip(next_pc,then),otherwise)
        elif match:=re.fullmatch(r'(r\d+_r\d+) >>= (\d+)',text):
            self.set_pair(match[1],self.pair(match[1])>>(int(match[2])&63))
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) ([+-]) (r\d+)(?: (\+ c|- !c))?',text):
            carry=self.carry if match[5]=='+ c' else 1-self.carry if match[5]=='- !c' else 0
            self.set(match[1],self.binary(self.value(match[2]),match[3],self.value(match[4]),carry))
        else:return super().single_step()
        self.pc=next_pc;return True

    def run(self):
        while self.steps<12000000:
            self.steps+=1
            try:running=self.step()
            except ObservationStop:self.guard=-203;running=False
            if not running:
                if not self.guard and (self.frames or self.returns or self.else_skips or self.value('sp')!=STACK):
                    raise ValueError('unbalanced IR lifecycle execution')
                return {'result':(0 if self.operation in VOID else self.value('r0'),0),
                    'status':self.guard,'memory':self.snapshot(),'calls':self.calls,'service_sites':self.service_sites,
                    'visited':set(self.visited),'steps':self.steps,'internal_calls':self.internal_calls,
                    'writes':self.writes,'stop_pc':self.pc}
        raise ValueError('IR lifecycle native instruction budget exhausted')
