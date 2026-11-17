"""Actual original construction followed by signal execution on retained bytes.

No native function is added. Separate synchronous entries share public state;
their private invocation stacks are kept separate, including paused audio tasks.
"""
from __future__ import annotations
import re
from effect_signal_machine import (EffectSignalProgram,EffectSignalAudioProgram,
    REGIONS as SIGNAL_REGIONS,ENTRIES,MAPPED,STATIC as SIGNAL_STATIC,ROOT,offset)
from effect_construction_machine import (EffectConstructionProgram,EffectConstructionMachine,
    REGIONS as CONSTRUCTION_REGIONS,REUSED,STATIC as CONSTRUCTION_STATIC,SERVICES,STACK)
from dot_machine import DotMachine,MASK32

STATIC=dict(SIGNAL_STATIC)|{'construction_'+name:bounds for name,bounds in CONSTRUCTION_STATIC.items()}
CONSTRUCTOR=0x0202cf62

class EffectConfiguredSignalProgram:
    def __init__(self):
        self.signal=EffectSignalProgram();self.construction=EffectConstructionProgram()
        self.audio=EffectSignalAudioProgram();self.app=self.signal.app
        self.code=dict(self.audio.code)
        for pc,record in self.construction.code.items():
            if pc in self.code and self.code[pc]!=record:raise ValueError('constructor/signal instruction disagreement')
            self.code[pc]=record
        self.data=dict(self.signal.data)|{'construction_'+key:value for key,value in self.construction.data.items()}
        self.external_sites={}
        for pc,(text,size,*_) in self.construction.code.items():
            match=re.fullmatch(r'call (-?\d+)',text.removesuffix('  #'))
            if not match:continue
            target=pc+size+int(match[1])
            if target not in self.construction.code:
                if target not in SERVICES:raise ValueError('unreviewed constructor call site')
                self.external_sites[pc]=(target,SERVICES[target])

    def prepare(self,memory,effect,boundary=None,*,mapped=MAPPED):
        if tuple(map(len,memory))!=tuple(n for _,n in mapped):raise ValueError('invalid retained constructor maps')
        if not 0<=effect<=MASK32:raise ValueError('invalid original effect word')
        machine=ConfiguredConstructionMachine(self,memory,effect,boundary,mapped)
        result=machine.run();result['status']=0;return result

    def execute(self,memory,name,args,boundary=None,*,block_budget=100000):
        return self.signal.execute(memory,name,args,boundary,block_budget=block_budget)

class ConfiguredConstructionMachine(EffectConstructionMachine):
    def __init__(self,owner,memory,effect,boundary,mapped):
        self.program,self.owner,self.operation,self.boundary=owner.construction,owner,'construct',boundary
        self.mapped=tuple(mapped);self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(mapped,memory) for i,v in enumerate(data)}
        for key,(base,_) in CONSTRUCTION_STATIC.items():
            self.memory.update({base+i:v for i,v in enumerate(self.program.data[key])})
        self.public_memory=list(map(bytearray,memory));self.pc=CONSTRUCTOR
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set()
        self.math_calls=[];self.production_calls=[];self.normalization_calls=[]
        self.coefficient_requests=[];self.exp_arguments=[];self.set('r0',effect)

    def write(self,address,value,size):
        if address+size>1<<32:raise ValueError('constructor write crosses address wrap')
        if 0x30000000<=address<STACK:
            if not self.value('sp')<=address<=address+size<=STACK:raise ValueError('constructor private stack escape')
        else:
            for (base,n),data in zip(self.mapped,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');break
            else:raise ValueError(f'constructor escaped retained public storage {address:#x}')
        self.writes.append((address,value&((1<<(8*size))-1),size));DotMachine.write(self,address,value,size)

    def external(self,target,args,count):
        if self.owner.external_sites.get(self.pc)!=(target,count):raise ValueError('constructor external ABI/site mismatch')
        return super().external(target,args,count)

def carry_preparation_into_audio(machine,prepared):
    """Publish only completed original public bytes, keeping paused CPU state."""
    from audio_task_machine import MAPPED as AUDIO_MAPPED
    if tuple(map(len,prepared))!=tuple(size for _,size in AUDIO_MAPPED):raise ValueError('invalid prepared audio storage')
    # Public mappings are stable. A separate constructor invocation has its own
    # original private stack, so none of those stack writes enter this task.
    for (base,_),data,existing in zip(AUDIO_MAPPED,prepared,machine.public_memory):
        existing[:]=data
        for i,value in enumerate(data):machine.memory[base+i]=value
