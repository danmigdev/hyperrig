"""Join three original parameter construction calls on one native memory image."""
from __future__ import annotations
import re
from effect_resource_ownership_machine import (EffectResourceOwnershipProgram,
    EffectResourceOwnershipMachine, REGIONS as OWNERSHIP, ENTRY_POINTS, ARITIES,
    MAPPED, STACK, ROOT, PRIVATE, region_bytes)
from effect_parameters_machine import EffectParametersMachine
from effect_model_construction_machine import (EffectModelConstructionProgram,
    EffectModelConstructionMachine, REGIONS as MODELS, REUSED as MODEL_REUSED)
from dot_machine import MASK32

DIRECT_JOINS={0x0202f37c:0x0202cf62,0x0202f970:0x0202cf62,0x0202f7ba:0x0202cd32}
REGIONS={**OWNERSHIP,**{'construction_'+k:v for k,v in (MODELS|MODEL_REUSED).items()}}

class EffectParameterConstructionProgram(EffectResourceOwnershipProgram):
    def __init__(self):
        super().__init__();self.construction=EffectModelConstructionProgram()
        before=set(self.code);self.construction_code=set(self.construction.code)
        for pc,record in self.construction.code.items():
            if pc in self.code and self.code[pc]!=record:raise ValueError('construction instruction overlap changed')
            self.code[pc]=record
        added=set(self.code)-before;incoming={}
        for pc in before:
            text,size,*_=self.code[pc]
            match=re.fullmatch(r'call (-?\d+)',text.removesuffix('  #'))
            if match and pc+size+int(match[1]) in added:incoming[pc]=pc+size+int(match[1])
        if incoming!=DIRECT_JOINS:raise ValueError(f'unreviewed constructor incoming edges: {incoming}')
        self.support_code=set(self.construction.support_code)
        self.parallel_seconds|=self.construction.parallel_seconds
        self.regular_code|=self.construction_code
        for name,bounds in self.construction.static_regions.items():
            same=[k for k,v in self.static_regions.items() if v==bounds]
            if same:
                if any(self.data[k]!=self.construction.data[name] for k in same):raise ValueError('constructor table overlap changed')
            else:
                self.static_regions['construction_'+name]=bounds
                self.data['construction_'+name]=self.construction.data[name]
        self.regions.update({'construction_'+k:v for k,v in self.construction.regions.items()})
        self.joined_code={pc for pc in self.code if any(a<=pc<b for a,b in REGIONS.values())}
        if len(self.code)!=20072 or len(REGIONS)!=107:raise ValueError('unexpected parameter construction closure')

    def execute(self,memory,entry,arguments=(),boundary=None,mmio=None,stop_extra_overread=False):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid construction memory views')
        name=entry if isinstance(entry,str) else next((k for k,v in ENTRY_POINTS.items() if v==entry),None)
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=v<=MASK32 for v in arguments):
            raise ValueError('invalid construction caller entry or ABI words')
        return EffectParameterConstructionMachine(self,memory,name,arguments,boundary,mmio,stop_extra_overread).run()

class EffectParameterConstructionMachine(EffectResourceOwnershipMachine):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.construction_sites=[];self.construction_view=None
        self.math_calls=[];self.production_calls=[];self.normalization_calls=[]
        self.coefficient_requests=[];self.exp_arguments=[]

    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc in DIRECT_JOINS:
            self.construction_sites.append((self.pc,DIRECT_JOINS[self.pc],self.value('r0')))
        # The two shared support routines already execute through the caller's
        # original ISA handler, retaining its live private flag and byte map.
        if self.pc not in self.program.construction_code or self.pc in self.program.support_code:
            return super().step()
        view=self.construction_view
        if view is None:
            view=object.__new__(EffectModelConstructionMachine);self.construction_view=view
        view.__dict__.update(self.__dict__)
        view.read=lambda address,size:EffectParametersMachine.read(view,address,size)
        view.write=lambda address,value,size:EffectParametersMachine.write(view,address,value,size)
        view.snapshot=lambda:EffectParametersMachine.snapshot(view)
        result=EffectModelConstructionMachine.step(view)
        for name,value in view.__dict__.items():
            if name not in ('read','write','snapshot','construction_view'):
                self.__dict__[name]=value
        return result

    def run(self):
        result=super().run();result['construction_sites']=self.construction_sites
        result['coefficient_requests']=self.coefficient_requests;result['exp_arguments']=self.exp_arguments
        return result
