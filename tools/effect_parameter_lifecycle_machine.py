"""Join original parameter and resource bodies on one register/stack/RAM image.

No native function is added. Direct calls execute decoded resource instructions;
indirect callbacks retain their original call-site ABI even when tokens collide.
Only the live four-byte allocation output is exposed through a canonical view.
"""
from __future__ import annotations
import re
from effect_parameters_machine import (EffectParametersProgram, EffectParametersMachine,
    REGIONS as PARAMETER_REGIONS, REUSED as PARAMETER_REUSED, SERVICES as PARAMETER_SERVICES,
    PROCESSING_SERVICES, SCENE_SERVICES, SUPPORT_REGIONS, ENTRY_POINTS, ARITIES, MAPPED,
    RAM, RAM_BYTES, ARENA, ARENA_BYTES, SAMPLES, SAMPLE_BYTES, STACK, ROOT, PRIVATE, ALLOCATE,
    region_bytes)
from effect_parameter_resources_machine import (EffectParameterResourcesProgram,
    EffectParameterResourcesMachine, REGIONS as RESOURCE_REGIONS, REUSED as RESOURCE_REUSED,
    STATIC as RESOURCE_STATIC, INDIRECT_ARITIES, SERVICES as RESOURCE_SERVICES)
from dot_machine import MASK32

REGIONS = {**{'parameter_'+k:v for k,v in PARAMETER_REGIONS.items()},
           **{'resource_'+k:v for k,v in RESOURCE_REGIONS.items()}}
DIRECT_RESOURCES = {RESOURCE_REGIONS[k][0] for k in ('mode_callback','allocate_delay',
    'migrate','allocate_extra','fingerprint','change_mode','ir_state','ir_length')}


class EffectParameterLifecycleProgram(EffectParametersProgram):
    def __init__(self):
        super().__init__()
        self.resources = EffectParameterResourcesProgram()
        for pc in self.code.keys() & self.resources.code.keys():
            if self.code[pc] != self.resources.code[pc]:
                raise ValueError('joined resource instruction disagrees with frozen caller dependency')
        self.code.update(self.resources.code)
        self.parallel_seconds |= self.resources.parallel_seconds
        self.regular_code |= set(self.resources.code)
        for name,bounds in RESOURCE_STATIC.items():
            key='resource_'+name
            self.static_regions[key]=bounds;self.data[key]=self.resources.data[name]
        self.regions.update({'resource_'+name:raw for name,raw in self.resources.regions.items()})
        self.resource_code=set(self.resources.code)
        self.joined_code={pc for pc in self.code if any(a<=pc<b for a,b in REGIONS.values())}

    def execute(self,memory,entry,arguments=(),boundary=None,mmio=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid lifecycle memory views')
        name=entry if isinstance(entry,str) else next((k for k,v in ENTRY_POINTS.items() if v==entry),None)
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=x<=MASK32 for x in arguments):
            raise ValueError('invalid lifecycle entry or native ABI words')
        return EffectParameterLifecycleMachine(self,memory,name,arguments,boundary,mmio).run()


class EffectParameterLifecycleMachine(EffectParametersMachine,EffectParameterResourcesMachine):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.resource_sites=[];self.flag_return_pending=False

    def private_snapshot(self):
        if self.private_address is None:return ()
        if self.private_written!=set(range(self.private_address,self.private_address+4)):
            return ()
        return ((PRIVATE,bytes(self.read(self.private_address+i,1) for i in range(4))),)

    def external(self,target,arguments,count):
        if self.boundary is None:raise ValueError(f'explicit lifecycle service required {target:#x}')
        args=tuple(arguments[:count])+(0,)*(12-count)
        before=self.snapshot();private_before=self.private_snapshot()
        preserved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
        value=self.boundary(target,args,self)&MASK32
        if preserved!={k:self.value(k) for k in preserved}:
            raise ValueError('lifecycle service changed callee-saved registers')
        self.calls.append((target,args,before,self.snapshot(),private_before,self.private_snapshot()))
        self.service_sites.append((self.pc,target,count))
        return value

    def single_step(self):
        self.visited.add(self.pc)
        text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if self.pc==0x0202F1F0 and self.flag_return_pending:
            if not self.private_snapshot():raise ValueError('resource allocator did not initialize its output flag')
            self.private_events.append((0x0202F1EC,self.private_snapshot()))
            self.flag_return_pending=False
        if match:=re.fullmatch(r'call (r\d+|-?\d+)',text):
            indirect=match[1].startswith('r');target=self.value(match[1]) if indirect else next_pc+int(match[1])
            installed_clear=indirect and self.pc==0x01C0656E and target==0x0201A9DC
            if target in self.program.code and (not indirect or installed_clear):
                if not indirect and target in DIRECT_RESOURCES:
                    self.resource_sites.append((self.pc,target))
                if self.pc==0x0202F1EC:
                    if target!=ALLOCATE or self.private_address is not None:
                        raise ValueError('unexpected nested allocation flag lifetime')
                    self.private_address=self.value('r2');self.private_written=set();self.flag_return_pending=True
                    if not self.value('sp')<=self.private_address<=self.private_address+4<=STACK:
                        raise ValueError('allocation flag is not on the active original stack')
                self.real_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            if indirect:
                if self.pc in INDIRECT_ARITIES:count=INDIRECT_ARITIES[self.pc]
                elif self.pc==0x0202F2AA:count=1
                elif any(a<=self.pc<b for a,b in SUPPORT_REGIONS.values()):count=2
                elif self.pc==0x01C10824:count=0
                else:raise ValueError(f'unreviewed indirect lifecycle call {self.pc:#x}')
            else:
                count=(PARAMETER_SERVICES|PROCESSING_SERVICES|SCENE_SERVICES|RESOURCE_SERVICES).get(target)
                if count is None:raise ValueError(f'unreviewed lifecycle service {self.pc:#x}/{target:#x}')
            args=tuple(self.value(f'r{i}') if i<4 else self.read(self.value('sp')+4*(i-4),4) for i in range(count))
            value=self.external(target,args,count)
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        consume_flag=self.pc in (0x0202F1FE,0x0202F244)
        result=super().single_step()
        if consume_flag:
            if self.private_address is None or self.flag_return_pending:
                raise ValueError('caller consumed an absent allocation flag')
            self.private_address=None;self.private_written=set()
        return result

    def run(self):
        result=super().run()
        if self.flag_return_pending:raise ValueError('unfinished allocation flag return')
        result['resource_sites']=self.resource_sites
        return result
