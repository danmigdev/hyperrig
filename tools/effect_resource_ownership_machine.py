"""Run the original resource/ownership/lifecycle bodies on shared native state.

No new original body is reconstructed. Only the exact direct flush call joins
the ownership closure. Indirect callbacks retain native call-site semantics.
"""
from __future__ import annotations
import re
from effect_parameter_lifecycle_machine import (EffectParameterLifecycleProgram,
    EffectParameterLifecycleMachine, REGIONS as LIFECYCLE_REGIONS, RESOURCE_REGIONS,
    ENTRY_POINTS as PARAMETER_ENTRIES, ARITIES as PARAMETER_ARITIES, MAPPED, STACK,
    ROOT, PRIVATE, region_bytes, DIRECT_RESOURCES)
from effect_parameter_resources_machine import ARITIES as RESOURCE_ARITIES, VOID as RESOURCE_VOID
from effect_ownership_machine import (EffectOwnershipProgram, REGIONS as OWNERSHIP_REGIONS,
    REUSED as OWNERSHIP_REUSED, INDIRECT_ARITIES as OWNERSHIP_INDIRECT)
from dot_machine import MASK32

FLUSH_CALL=0x0202edaa
REMOVE=0x0202eb4c
OWNED_CLOSURE={name:OWNERSHIP_REGIONS[name] for name in ('lookup','release','detach','capture','remove')}
REGIONS=LIFECYCLE_REGIONS|{'ownership_'+k:v for k,v in OWNED_CLOSURE.items()}
ENTRY_POINTS=PARAMETER_ENTRIES|{'resource_'+k:v[0] for k,v in RESOURCE_REGIONS.items()}
ARITIES=PARAMETER_ARITIES|{'resource_'+k:v for k,v in RESOURCE_ARITIES.items()}

class OwnershipPrefix(Exception):
    """Observation before the original fourth private pointer read."""

class EffectResourceOwnershipProgram(EffectParameterLifecycleProgram):
    def __init__(self):
        super().__init__();self.ownership=EffectOwnershipProgram()
        spans=OWNED_CLOSURE|OWNERSHIP_REUSED
        self.ownership_code={pc for pc in self.ownership.code if any(a<=pc<b for a,b in spans.values())}
        for pc in self.ownership_code:
            record=self.ownership.code[pc]
            if pc in self.code and self.code[pc]!=record:raise ValueError('joined ownership instructions disagree')
            self.code[pc]=record
        self.regular_code|=self.ownership_code
        self.parallel_seconds|=self.ownership.parallel_seconds&self.ownership_code
        self.regions.update({'ownership_'+k:self.ownership.regions[k] for k in spans})
        self.joined_code={pc for pc in self.code if any(a<=pc<b for a,b in REGIONS.values())}
        text,size,*_=self.code[FLUSH_CALL]
        if text!='call -610' or FLUSH_CALL+size-610!=REMOVE:
            raise ValueError('original direct slot-removal call changed')
        # This closure must introduce no accidental replacement of another
        # caller's explicit service merely because its target is now loaded.
        prior=set(super_code for super_code in self.code if super_code not in self.ownership_code)
        added=self.ownership_code-set(self.resources.code)-self.parameter_code-set(self.processing.code)
        incoming=[]
        for pc in prior:
            text,size,*_=self.code[pc]
            match=re.fullmatch(r'call (-?\d+)',text.removesuffix('  #'))
            if match and pc+size+int(match[1]) in added:incoming.append(pc)
        if incoming!=[FLUSH_CALL]:raise ValueError(f'unreviewed new ownership call sites {incoming}')

    def execute(self,memory,entry,arguments=(),boundary=None,mmio=None,stop_extra_overread=False):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid joined memory views')
        name=entry if isinstance(entry,str) else next((k for k,v in ENTRY_POINTS.items() if v==entry),None)
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=v<=MASK32 for v in arguments):
            raise ValueError('invalid joined entry or ABI words')
        return EffectResourceOwnershipMachine(self,memory,name,arguments,boundary,mmio,stop_extra_overread).run()

class EffectResourceOwnershipMachine(EffectParameterLifecycleMachine):
    def __init__(self,program,memory,name,arguments,boundary,mmio,stop_extra_overread):
        super().__init__(program,memory,'commit' if name.startswith('resource_') else name,arguments,boundary,mmio)
        self.operation=name;self.pc=ENTRY_POINTS[name]
        self.stop_extra_overread=stop_extra_overread;self.ownership_sites=[]

    def single_step(self):
        if self.pc==0x0202df8a and self.value('r6')>=self.value('sp')+12:
            if self.stop_extra_overread:raise OwnershipPrefix()
            raise ValueError('original fourth cached pointer is outside the supported stack domain')
        if self.pc==FLUSH_CALL:self.ownership_sites.append((self.pc,REMOVE))
        text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #')
        if self.pc in self.program.ownership_code:
            if text=='csync':self.visited.add(self.pc);self.pc+=size;return True
            match=re.fullmatch(r'(r\d+) = (r\d+) & ~\(1 << (r\d+)\)',text)
            if match:
                self.visited.add(self.pc)
                self.set(match[1],self.value(match[2])&~(1<<(self.value(match[3])&31)))
                self.pc+=size;return True
            if match:=re.fullmatch(r'call (r\d+)',text):
                self.visited.add(self.pc);count=OWNERSHIP_INDIRECT.get(self.pc)
                if count!=1:raise ValueError('unreviewed ownership indirect ABI')
                value=self.external(self.value(match[1]),(self.value('r0'),),count)
                for i in range(4):self.set(f'r{i}',0xbad0c0de)
                self.set('r0',value);self.pc+=size;return True
        return super().single_step()

    def run(self):
        try:
            result=super().run();result['status']=0
            if self.operation.startswith('resource_') and self.operation[9:] in RESOURCE_VOID:
                result['value']=0;result['result']=(0,0)
        except OwnershipPrefix:
            result={'value':self.value('r0'),'result':None,'status':-202,
                'memory':self.snapshot(),'calls':self.calls,'real_calls':self.real_calls,
                'visited':self.visited,'steps':self.steps,'service_sites':self.service_sites,
                'private_events':self.private_events,'mmio_events':self.mmio_events,
                'resource_sites':self.resource_sites}
        result['ownership_sites']=self.ownership_sites
        result['stop_pc']=self.pc;result['private_at_stop']=self.private_snapshot()
        result['pending_flag_at_stop']=self.flag_return_pending
        return result
