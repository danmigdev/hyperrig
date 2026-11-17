"""Join 35 existing original IR regions in one native byte address space.

No typed runtime conversion, fixed allocator token or source-count bound is
inherited from the earlier construction test harness. Only the exact declared
instruction closure is loaded; every producer/callback is resolved by site.
"""
from __future__ import annotations
import re
from ir_effect_lifecycle_machine import (IrEffectLifecycleProgram,IrEffectLifecycleMachine,
    REGIONS as LIFECYCLE,REUSED as LIFECYCLE_REUSED,ARITIES as LIFE_ARITIES,
    ROOT,region_bytes,RAM,ARENA,STACK,INDIRECT_ARITIES as LIFE_INDIRECT)
from ir_convolution_machine import IrConvolutionProgram,REGIONS as CONVOLUTION,REUSED as MATH
from ir_installation_machine import REGIONS as INSTALLATION
from biquad_coefficients_machine import FLOAT
from dot_machine import DotMachine,MASK32

REGIONS={**LIFECYCLE,'prepare':CONVOLUTION['prepare'],'construct':CONVOLUTION['construct']}
NUMERICAL={**CONVOLUTION,**MATH,**{n:INSTALLATION[n] for n in ('budget','convert','limit','effective','raw_length')}}
ALL_REGIONS={**{f'lifecycle_{n}':v for n,v in LIFECYCLE.items()},**LIFECYCLE_REUSED,**NUMERICAL}
REUSED=ALL_REGIONS
ARITIES={**LIFE_ARITIES,'prepare':2,'construct':4}
STATIC={'resampling_taps':(0x0203be2c,0x0203be50)}
MAPPED=((RAM,0x01c38000-RAM),(ARENA,262144),(0,8192),(0xffff0000,65536))
INDIRECT_ARITIES={**LIFE_INDIRECT,0x02029670:1,0x020296e8:1,0x02029722:1,0x02031a00:4}

class IrEffectNumericalProgram(IrEffectLifecycleProgram):
    def __init__(self):
        super().__init__();prior=IrConvolutionProgram();self.regions={}
        for name,(start,end) in ALL_REGIONS.items():
            self.regions[name]=region_bytes((ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes(),start,end)
        for pc,instruction in prior.code.items():
            if any(a<=pc<b for a,b in NUMERICAL.values()):
                if pc in self.code and self.code[pc]!=instruction:raise ValueError('IR instruction overlap differs')
                self.code[pc]=instruction
        self.parallel_seconds|={pc for pc in prior.parallel_seconds if pc in self.code}
        self.data={'resampling_taps':prior.taps}
        if len(self.code)!=1453 or len(ALL_REGIONS)!=35:raise ValueError('unexpected joined IR closure')
    def execute(self,memory,name,arguments=(),boundary=None,stop=None):
        if stop is not None:raise ValueError('native prefix observers are not declared for this joined module')
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('IR numerical memory views')
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=x<=MASK32 for x in arguments):
            raise ValueError('IR numerical original arguments')
        return IrEffectNumericalMachine(self,memory,name,arguments,boundary,stop).run()

class IrEffectNumericalMachine(IrEffectLifecycleMachine):
    def __init__(self,program,memory,name,arguments,boundary,stop):
        super().__init__(program,[bytearray(n) for _,n in __import__('ir_effect_lifecycle_machine').MAPPED],
            'relocate',(0,0),boundary,stop)
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory));self.operation=name;self.pc=REGIONS[name][0]
        for key,(base,_) in STATIC.items():self.memory.update({base+i:v for i,v in enumerate(program.data[key])})
        for i,value in enumerate(arguments):
            if i<4:self.set(f'r{i}',value)
            else:DotMachine.write(self,STACK+4*(i-4),value,4)
        self.producer_calls=[]
    def address(self,expression):
        if match:=re.fullmatch(r'\+\+(r\d+)=(r\d+)',expression):
            self.set(match[1],self.value(match[1])+self.value(match[2]));return self.value(match[1])
        return super().address(expression)
    def read(self,address,size):
        if address+size>1<<32:raise ValueError('IR numerical read crosses address wrap')
        if 0x30000000<=address<STACK and not self.value('sp')<=address<=address+size<=STACK:
            raise ValueError('IR numerical read escapes active private frame')
        return DotMachine.read(self,address,size)
    def write(self,address,value,size):
        if address+size>1<<32:raise ValueError('IR numerical write crosses address wrap')
        if 0x30000000<=address<STACK:
            if not self.value('sp')<=address<=address+size<=STACK:raise ValueError('IR numerical private write escape')
        else:
            for (base,n),data in zip(MAPPED,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');break
            else:raise ValueError(f'IR numerical unmapped write {address:#x}/{size}')
        self.writes.append((address,value&((1<<(8*size))-1),size));DotMachine.write(self,address,value,size)
    def single_step(self):
        text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if match:=re.fullmatch(r'call (r\d+)',text):
            target=self.value(match[1]);self.visited.add(self.pc)
            if self.pc==0x02031a00 and target in (0x02031542,0x020315b8):
                self.producer_calls.append((target,tuple(self.value(f'r{i}') for i in range(4))))
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            count=INDIRECT_ARITIES.get(self.pc)
            if count is None or self.boundary is None:raise ValueError(f'IR indirect call outside closure {self.pc:#x}')
            args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=self.snapshot();saved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
            value=self.boundary(target,args,self)&MASK32
            if any(self.value(r)!=v for r,v in saved.items()):raise ValueError('IR callback changed preserved registers')
            self.calls.append((target,args,before,self.snapshot(),value));self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+) - (r\d+) \(f\)',text):
            self.visited.add(self.pc);self.set(match[1],FLOAT.arithmetic(self.value(match[2]),self.value(match[3]),'sub'))
        elif match:=re.fullmatch(r'(r\d+) = (utof|ftoi)\((r\d+)\)(?: \((trunc)\))?',text):
            self.visited.add(self.pc);result,_=FLOAT.convert(match[2],match[4] or 'even')({0:self.value(match[3])},0,{'s':0,'r':1})
            self.set(match[1],result[1])
        elif match:=re.fullmatch(r'if \(\((r\d+) & (\d+)\) != 0\) goto (-?\d+)',text):
            self.visited.add(self.pc)
            if self.value(match[1])&int(match[2]):next_pc+=int(match[3])
        elif match:=re.fullmatch(r'(r\d+) >>= (r\d+)',text):
            self.visited.add(self.pc);self.set(match[1],self.value(match[1])>>(self.value(match[2])&31))
        elif match:=re.fullmatch(r'(r\d+) <= insert\((r\d+), p:(\d+), l:(\d+)\)',text):
            self.visited.add(self.pc);position,length=int(match[3]),int(match[4]);mask=(1<<length)-1
            self.set(match[1],self.value(match[1])&~(mask<<position)|(self.value(match[2])&mask)<<position)
        else:return super().single_step()
        self.pc=next_pc;return True
