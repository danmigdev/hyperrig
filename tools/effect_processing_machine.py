"""Complete original effect callers with explicit unresolved model services."""
from __future__ import annotations
import hashlib
import re
from dsp_stage_machine import (DspStageProgram,DspStageMachine,DspStageAudioProgram,
    DspStageAudioMachine,STATIC as STAGE_STATIC,offset,ROOT,STACK)
from ir_processing_machine import IrProcessingProgram,MMIO,READ,WRITE,SYNC
from effect_resampling_machine import EffectResamplingProgram,STATIC as RESAMPLING_STATIC
from effect_enable_machine import EffectEnableProgram
from dsp_audio_path_machine import DspAudioPathProgram
from audio_task_machine import AudioTaskProgram,AudioTaskMachine,STATIC as AUDIO_STATIC
from dot_machine import DotMachine,signed
from pi32v2isa import codec,table

REGIONS={
    'capture_probe':(0x01c0588e,0x01c058bc),
    'cost':(0x01c058bc,0x01c05c08),'extra_cost':(0x01c05c08,0x01c05d02),
    'warning':(0x01c0735e,0x01c07400),'peak_fade':(0x01c07400,0x01c07588),
    'automation':(0x01c07588,0x01c0767e),
    'q16':(0x01c08b34,0x01c08b3e),'exp':(0x01c08c76,0x01c08c98),
    'dispatch':(0x01c0deb6,0x01c0f678),'individual':(0x01c0f678,0x01c10446),
    'grouped':(0x01c10446,0x01c10818),
    'ir_active':(0x01c11f56,0x01c11f66),'ir_accelerated':(0x01c12446,0x01c1245c),
    'peak16':(0x01c19bee,0x01c19c98),'ramp16':(0x01c19c98,0x01c19d36),
    'wrap16':(0x01c19ede,0x01c19efa),
}
ARITIES={'capture_probe':1,'cost':2,'extra_cost':6,'warning':3,'peak_fade':6,
    'automation':3,'q16':2,'exp':1,'dispatch':4,'individual':3,'grouped':4,
    'ir_active':1,'ir_accelerated':1,'peak16':1,'ramp16':3,'wrap16':3}
ENTRIES={name:start for name,(start,end) in REGIONS.items()}|{'stage':0x01c10e06}
ARITIES['stage']=3
TABLES={'cost_branches':(0x01c058e2,0x01c0592a),
    'extra_cost_branches':(0x01c05ca2,0x01c05cc6),
    'dispatch_branches':(0x01c0e0a8,0x01c0e0f6),
    'individual_branches':(0x01c10204,0x01c1023e)}
STATIC={**TABLES,'state_copy':(0x0203b7b0,0x0203b7c8),
    'costs':(0x0203b340,0x0203b3e0),'oversampling_costs':(0x0203b8e0,0x0203b934),
    'capture_costs':(0x0203bdc0,0x0203bdc8),**STAGE_STATIC,
    'accelerator_tables':(0x0203be50,0x0203be90),**RESAMPLING_STATIC,**AUDIO_STATIC}
RAM,RAM_BYTES=0x01c1f180,0x01c344b4-0x01c1f180
SAMPLES,SAMPLE_BYTES,ARENA,ARENA_BYTES=0x35010000,4096,0x33000000,131072
MAPPED=((RAM,RAM_BYTES),(SAMPLES,SAMPLE_BYTES),(ARENA,ARENA_BYTES))
# Arities are independently checked against complete callee incoming-register
# and incoming-stack uses. Leaf implementations remain explicit boundaries.
SERVICES={0x01c04862:0,0x01c06b2c:1,0x01c06b82:1,0x01c06f84:3,
    0x01c0767e:3,0x01c089e8:3,0x01c08b3e:9,0x01c08f80:4,
    0x01c0a7aa:4,0x01c0b3b0:4,0x01c0b4b8:3,0x01c0b524:5,
    0x01c0b5d6:1,0x01c0ba14:8,0x01c0bbce:4,0x01c0bd8c:1,
    0x01c0ddae:3,0x01c18f90:1,0x01c1958e:3,0x01c19a8a:3,0x01c1ee40:3}

def boundary_digest(target,arguments,backend,public_digest):
    """Bind initialized private descriptor inputs as well as public memory."""
    spans=((arguments[0],68),) if target==0x01c18f90 else ((arguments[4],4),) if target==0x01c0b524 else ()
    if not spans:return public_digest
    digest=hashlib.sha256(bytes.fromhex(public_digest))
    for address,size in spans:
        digest.update(address.to_bytes(4,'little'));digest.update(size.to_bytes(4,'little'))
        for i in range(0,size,4):digest.update(backend.read(address+i,4).to_bytes(4,'little'))
    return digest.hexdigest()

class EffectProcessingProgram:
    def __init__(self):
        self.stage=DspStageProgram();self.ir=IrProcessingProgram();self.resampling=EffectResamplingProgram()
        self.code={};self.parallel_seconds=set()
        for inherited in (self.stage,self.ir,self.resampling):
            for pc in self.code.keys()&inherited.code.keys():
                if self.code[pc]!=inherited.code[pc]:raise ValueError('inconsistent joined original instruction')
            self.code.update(inherited.code);self.parallel_seconds|=inherited.parallel_seconds
        for inherited,start,end in ((EffectEnableProgram(),0x01c11f76,0x01c11faa),(DspAudioPathProgram(),0x01c19d36,0x01c19ede)):
            self.code.update({pc:instruction for pc,instruction in inherited.code.items() if start<=pc<end})
            self.parallel_seconds|={pc for pc in inherited.parallel_seconds if start<=pc<end}
        self.inherited_code=set(self.code);self.regions={}
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();self.app=app
        self.data={name:app[offset(start):offset(end)] for name,(start,end) in STATIC.items()}
        instructions=table.load()
        for name,(start,end) in REGIONS.items():
            raw=self.regions[name]=app[offset(start):offset(end)];cursor=0
            while cursor<len(raw):
                found=next((b for a,b in TABLES.values() if a==start+cursor),None)
                if found is not None:cursor=found-start;continue
                decoded=codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError(f'undecoded effect instruction {start+cursor:#x}')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]];counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError('effect instruction crosses region')
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts;cursor+=size
        for pc,(text,size,_,_) in self.code.items():
            if text.endswith('  #'):
                following,bsize,_,_=self.code[pc+size]
                if bsize!=2 or '[' not in following:raise ValueError(f'unreviewed effect packet {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,name,arguments=(),boundary=None,mmio=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid effect memory')
        if name not in ARITIES or len(arguments)!=ARITIES[name]:raise ValueError('invalid effect entry')
        m=EffectProcessingMachine(self,memory,boundary,mmio);m.pc=ENTRIES[name]
        for i,v in enumerate(arguments):
            if not 0<=v<=0xffffffff:raise ValueError('invalid ABI word')
            if i<4:m.set(f'r{i}',v)
            else:DotMachine.write(m,STACK+4*(i-4),v,4)
        while m.steps<8000000:
            m.steps+=1
            if not m.step():break
        else:raise ValueError('effect instruction budget exhausted')
        if m.frames or m.returns or m.else_skips or m.value('sp')!=STACK:raise ValueError('unbalanced effect ABI')
        return {'value':m.value('r0'),'memory':m.snapshot(),'calls':m.calls,'real_calls':m.real_calls,
                'visited':m.visited,'steps':m.steps,'mmio_events':m.mmio_events}

class EffectProcessingMachine(DspStageMachine):
    def __init__(self,program,memory,boundary,mmio=None):
        self.program,self.boundary,self.mmio=program,boundary,mmio
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory))
        for name,(start,end) in STATIC.items():self.memory.update({start+i:v for i,v in enumerate(program.data[name])})
        # Bind every inherited read-only table as original bytes. Public maps
        # deliberately do not include program/data ROM as writable storage.
        self.pc,self.carry,self.flags,self.steps=0,0,0,0
        self.frames,self.returns,self.calls,self.real_calls,self.mmio_events=[],[],[],[],[]
        self.visited,self.else_skips,self.written,self.entries=set(),{},set(),{}

    def io(self,op,address,value=0):
        if self.mmio is None:
            if self.boundary is None:raise ValueError('unmodeled accelerator boundary')
            target=0xffff0000+op;args=(address,value);self.calls.append((target,args,self.state_digest()))
            result=self.boundary(target,args,self)&0xffffffff
        else:result=self.mmio(op,address,value,self)&0xffffffff
        self.mmio_events.append((op,address,value,result,self.state_digest()));return result
    def read(self,address,size):
        if MMIO<=address<MMIO+8:
            if size!=4:raise ValueError('unreviewed MMIO width')
            return self.io(READ,address)
        if 0x30000000<=address<STACK and not self.value('sp')<=address<=address+size<=STACK:
            raise ValueError('read escaped effect stack')
        return DotMachine.read(self,address,size)
    def write(self,address,value,size):
        if MMIO<=address<MMIO+8:
            if size!=4:raise ValueError('unreviewed MMIO width')
            self.io(WRITE,address,value&0xffffffff);return
        if 0x30000000<=address<STACK:
            if not self.value('sp')<=address<=address+size<=STACK:raise ValueError('write escaped effect stack')
        else:
            for (base,n),data in zip(MAPPED,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');break
            else:raise ValueError(f'write escaped mapped effect memory {address:#x}')
        DotMachine.write(self,address,value,size)
    def single_step(self):
        self.visited.add(self.pc);text,size,_,_=self.program.code[self.pc];text=text.removesuffix('  #')
        if text=='[--sp] = {r5, r4}':
            self.frames.append(({r:self.value(r) for r in ('r4','r5')},self.value('sp')))
            self.set('sp',self.value('sp')-8);self.pc+=size;return True
        if text=='{r5, r4} = [sp++]':
            saved,sp=self.frames.pop();self.regs.update(saved,sp=sp);self.pc+=size;return True
        if match:=re.fullmatch(r'(r\d+) ([&|^])= (\d+)',text):
            left=self.value(match[1]);right=int(match[3]);self.set(match[1],{'&':left&right,'|':left|right,'^':left^right}[match[2]])
            self.pc+=size;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+)\.l \(u\)',text):
            self.set(match[1],self.value(match[2])&65535);self.pc+=size;return True
        if match:=re.fullmatch(r'(r\d+) = clz\((r\d+)\)',text):
            self.set(match[1],32-self.value(match[2]).bit_length());self.pc+=size;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(([us])\)',text):
            numerator,denominator=self.value(match[2]),self.value(match[3])
            if match[4]=='s':numerator,denominator=signed(numerator),signed(denominator)
            quotient=abs(numerator)//abs(denominator) if denominator else 0
            if (numerator<0) != (denominator<0):quotient=-quotient
            self.set(match[1],quotient);value=quotient&0xffffffff
            self.flags=(self.flags&3)|(4 if not value else 0)|(8 if value>>31 else 0)
            self.pc+=size;return True
        if match:=re.fullmatch(r'(r\d+) <= insert\((r\d+), p:(\d+), l:(\d+)\)',text):
            position,length=int(match[3]),int(match[4]);mask=((1<<length)-1)<<position
            self.set(match[1],(self.value(match[1])&~mask)|((self.value(match[2])<<position)&mask));self.pc+=size;return True
        if text.startswith('call '):
            target=self.value(text[5:]) if text[5:].startswith('r') else self.pc+size+int(text[5:])
            if target in self.program.code:
                self.real_calls.append(target);self.returns.append(self.pc+size);self.pc=target;return True
            if target not in SERVICES or self.boundary is None:raise ValueError(f'unmodeled effect call {target:#x} at {self.pc:#x}')
            args=tuple(self.value(f'r{i}') if i<4 else self.read(self.value('sp')+4*(i-4),4) for i in range(SERVICES[target]))
            self.calls.append((target,args,boundary_digest(target,args,self,self.state_digest())));result=self.boundary(target,args,self)
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',result);self.pc+=size;return True
        if match:=re.fullmatch(r'tb([bh]) \[(r\d+)\]',text):
            base=self.pc+size;target=base+2*self.read(base+self.value(match[2]),1 if match[1]=='b' else 2)
            if target not in self.program.code:raise ValueError(f'invalid branch-table target {target:#x}')
            self.pc=target;return True
        return super().single_step()

class EffectProcessingAudioProgram(AudioTaskProgram):
    def __init__(self):
        super().__init__();self.effects=EffectProcessingProgram()
        for pc in self.code.keys()&self.effects.code.keys():
            if self.code[pc]!=self.effects.code[pc]:raise ValueError('inconsistent audio/effect instruction')
        self.code.update(self.effects.code);self.parallel_seconds|=self.effects.parallel_seconds
    def machine(self,memory,boundary=None):return EffectProcessingAudioMachine(self,memory,boundary)

class EffectProcessingAudioMachine(AudioTaskMachine):
    def __init__(self,program,memory,boundary):
        super().__init__(program,memory,boundary);self.flags=0;self.entries={};self.mmio_events=[];self.mmio=None
        self.effect_view=object.__new__(EffectProcessingMachine)
        for name,(start,end) in STATIC.items():self.memory.update({start+i:v for i,v in enumerate(program.effects.data[name])})
    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.effects.code:return super().step()
        view=self.effect_view;view.__dict__.update(self.__dict__)
        view.read=lambda address,size:AudioTaskMachine.read(view,address,size)
        view.write=lambda address,value,size:AudioTaskMachine.write(view,address,value,size)
        view.state_digest=lambda:self.state_digest()
        result=EffectProcessingMachine.step(view)
        for name,value in view.__dict__.items():
            if name not in ('read','write','state_digest'):self.__dict__[name]=value
        if self.written is None:self.written=set()
        return result
