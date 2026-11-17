"""Decode and execute three complete signal leaves and their frozen callers."""
from __future__ import annotations
from effect_processing_machine import (EffectProcessingProgram,EffectProcessingMachine,
    EffectProcessingAudioProgram,EffectProcessingAudioMachine,ENTRIES as PRIOR_ENTRIES,
    ARITIES as PRIOR_ARITIES,MAPPED,STATIC,STACK,ROOT,offset)
from audio_task_machine import AudioTaskProgram,AudioTaskMachine
from dot_machine import DotMachine
from pi32v2isa import codec,table

REGIONS={'allpass':(0x01c1958e,0x01c19a8a),'gate':(0x01c19a8a,0x01c19bee),
    'variable_filter':(0x01c1ee40,0x01c1f088)}
BLOCKS={0x01c195b8:16,0x01c19abc:16,0x01c1ee6e:4}
ENTRIES=PRIOR_ENTRIES|{name:start for name,(start,end) in REGIONS.items()}
ARITIES=PRIOR_ARITIES|{name:3 for name in REGIONS}

class BlockBudget(Exception):pass

class EffectSignalProgram(EffectProcessingProgram):
    def __init__(self):
        super().__init__();self.previous_code=set(self.code);instructions=table.load()
        self.signal_regions={}
        for name,(start,end) in REGIONS.items():
            raw=self.signal_regions[name]=self.app[offset(start):offset(end)];cursor=0
            while cursor<len(raw):
                decoded=codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError('undecoded signal instruction')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError('signal instruction crosses complete body')
                pc=start+cursor
                if pc in self.code:raise ValueError('signal body overlaps frozen instruction scope')
                self.code[pc]=codec.format(instruction,fields),size,*counts;cursor+=size
        for pc in self.code.keys()-self.previous_code:
            if self.code[pc][0].endswith('  #'):raise ValueError('new signal packet needs separate review')

    def execute(self,memory,name,arguments=(),boundary=None,mmio=None,block_budget=100000):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid signal memory')
        if name not in ARITIES or len(arguments)!=ARITIES[name]:raise ValueError('invalid signal ABI')
        if not 0<=block_budget<=0xffffffff:raise ValueError('invalid block budget')
        m=EffectSignalMachine(self,memory,boundary,mmio);m.pc=ENTRIES[name];m.remaining=block_budget
        for i,value in enumerate(arguments):
            if not 0<=value<=0xffffffff:raise ValueError('invalid ABI word')
            if i<4:m.set(f'r{i}',value)
            else:DotMachine.write(m,STACK+4*(i-4),value,4)
        status=0
        try:
            while m.steps<16000000:
                m.steps+=1
                if not m.step():break
            else:raise ValueError('signal instruction budget exhausted')
        except BlockBudget:status=-203
        if not status and (m.frames or m.returns or m.else_skips or m.value('sp')!=STACK):
            raise ValueError('unbalanced signal ABI')
        return {'status':status,'value':m.value('r0'),'memory':m.snapshot(),'calls':m.calls,
            'real_calls':m.real_calls,'visited':m.visited,'steps':m.steps,'blocks':m.blocks,
            'stop_pc':m.pc,'writes':m.signal_writes}

class EffectSignalMachine(EffectProcessingMachine):
    def __init__(self,program,memory,boundary,mmio=None):
        super().__init__(program,memory,boundary,mmio)
        self.remaining=0;self.blocks=[];self.signal_writes=[]
    def write(self,address,value,size):
        super().write(address,value,size)
        if any(start<=self.pc<end for start,end in REGIONS.values()) and not 0x30000000<=address<STACK:
            self.signal_writes.append((address,value&((1<<(8*size))-1),size))
    def single_step(self):
        if self.pc in BLOCKS:
            if not self.remaining:raise BlockBudget()
            self.remaining-=1;self.blocks.append((self.pc,BLOCKS[self.pc]))
        return super().single_step()

class EffectSignalAudioProgram(AudioTaskProgram):
    def __init__(self):
        super().__init__();self.effects=EffectSignalProgram()
        for pc in self.code.keys()&self.effects.code.keys():
            if self.code[pc]!=self.effects.code[pc]:raise ValueError('inconsistent audio/signal instruction')
        self.code.update(self.effects.code);self.parallel_seconds|=self.effects.parallel_seconds
    def machine(self,memory,boundary=None):return EffectSignalAudioMachine(self,memory,boundary)

class EffectSignalAudioMachine(EffectProcessingAudioMachine):
    def __init__(self,program,memory,boundary):
        super().__init__(program,memory,boundary);self.remaining=0;self.blocks=[];self.signal_writes=[]
        self.effect_view=object.__new__(EffectSignalMachine)
    def resume(self,wait_budget,frame_budget,block_budget=100000):
        self.remaining=block_budget
        try:return super().resume(wait_budget,frame_budget)
        except BlockBudget:raise ValueError('audio budget guard is not a resumable observation')
    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.effects.code:return AudioTaskMachine.step(self)
        view=self.effect_view;view.__dict__.update(self.__dict__)
        view.read=lambda address,size:AudioTaskMachine.read(view,address,size)
        view.write=lambda address,value,size:AudioTaskMachine.write(view,address,value,size)
        view.state_digest=lambda:self.state_digest()
        result=EffectSignalMachine.step(view)
        for name,value in view.__dict__.items():
            if name not in ('read','write','state_digest'):self.__dict__[name]=value
        if self.written is None:self.written=set()
        return result
