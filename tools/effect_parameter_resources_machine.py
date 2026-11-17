"""Execute complete resource bodies and their real packed-history arithmetic.

Only slot removal and explicitly installed platform callbacks remain services.
The original code and tables are decoded from the pinned M5.71 image; portable
C is never used to produce the original-instruction reference result.
"""
from __future__ import annotations
import re
from effect_parameter_support_machine import (EffectParameterSupportMachine,
    CounterRegion, region_bytes, ROOT, REGIONS as SUPPORT, REUSED as CLEAR,
    STATIC as SUPPORT_STATIC)
from effect_processing_machine import EffectProcessingMachine, REGIONS as PROCESSING
from dsp_stage_machine import REGIONS as STAGE
from ir_installation_machine import REGIONS as IR
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {
    'mode_callback':(0x01c05ec6,0x01c05ed6), 'extra_size':(0x01c05ff2,0x01c05ffa),
    'decode_sample':(0x01c065e2,0x01c065f6), 'encode_group':(0x01c065f6,0x01c067e0),
    'sum3':(0x01c067ea,0x01c06808), 'fingerprint36':(0x01c06808,0x01c06846),
    'fingerprint37':(0x01c06846,0x01c0688c), 'sum4':(0x01c0688c,0x01c068b6),
    'delay_state':(0x01c068b6,0x01c068e0), 'reset':(0x01c068e0,0x01c06926),
    'allocate':(0x0202df04,0x0202df38), 'flush':(0x0202ed7e,0x0202edb8),
    'allocate_delay':(0x0202edb8,0x0202ee3c), 'migrate':(0x0202ee3c,0x0202eeba),
    'allocate_extra':(0x0202eeba,0x0202eefa), 'fingerprint':(0x0202eefa,0x0202efe2),
    'change_mode':(0x0202efe2,0x0202f014), 'ir_state':(0x0202f014,0x0202f02e),
    'ir_length':(0x0202f02e,0x0202f07e),
}
REUSED = {**{name:SUPPORT[name] for name in ('selector','clear_halfwords')},
    **CLEAR, **{name:IR[name] for name in ('budget','convert','limit','effective')},
    'active':STAGE['active'], 'ir_active':PROCESSING['ir_active']}
TABLES = {'reset_branches':(0x01c068ee,0x01c06904),
    'fingerprint_high_branches':(0x0202ef12,0x0202ef22),
    'fingerprint_low_branches':(0x0202ef3e,0x0202ef48)}
STATIC = {**TABLES, **{name:SUPPORT_STATIC[name] for name in ('selector','capabilities')}}
ARITIES = dict(mode_callback=1,extra_size=0,decode_sample=3,encode_group=4,
    sum3=1,fingerprint36=1,fingerprint37=1,sum4=1,delay_state=1,reset=1,
    allocate=1,flush=0,allocate_delay=3,migrate=5,allocate_extra=1,fingerprint=1,
    change_mode=2,ir_state=1,ir_length=3)
VOID = {'mode_callback','encode_group','reset','flush','migrate','change_mode'}
RAM, RAM_BYTES, ARENA, ARENA_BYTES, STACK = 0x01c1f180,0x01c344b4-0x01c1f180,0x33000000,131072,0x30001000
MAPPED = ((RAM,RAM_BYTES),(ARENA,ARENA_BYTES),(0,256),(0xffffff00,256))
INDIRECT_ARITIES = {0x01c05ed2:1,0x0202df16:1,0x0202edfc:1,0x01c0656e:2}
SERVICES = {0x0202eb4c:1}

class EffectParameterResourcesProgram:
    def __init__(self):
        CounterRegion('counter')
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.code,self.regions,self.parallel_seconds={}, {},set()
        self.data={name:region_bytes(app,*bounds) for name,bounds in STATIC.items()}
        instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);cursor=0
            while cursor<len(raw):
                data_end=next((b for a,b in TABLES.values() if start+cursor==a),None)
                if data_end is not None:cursor=data_end-start;continue
                found=codec.decode(instructions,raw,cursor)
                if found is None:raise ValueError(f'undecoded resource instruction {start+cursor:#x}')
                instruction,fields,size=found;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if start+cursor+size>end:raise ValueError('resource instruction crosses complete region')
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts;cursor+=size
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|\^=|\|=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed resource parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)
        for name,entries in (('reset_branches',21),('fingerprint_high_branches',15),('fingerprint_low_branches',10)):
            start,end=TABLES[name];raw=self.data[name]
            if any(start+2*x not in self.code for x in raw[:entries]) or any(raw[entries:]):
                raise ValueError('resource jump table or zero alignment padding changed')

    def execute(self,memory,name,arguments=(),boundary=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid resource memory views')
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=x<=MASK32 for x in arguments):
            raise ValueError('invalid resource ABI words')
        return EffectParameterResourcesMachine(self,memory,name,arguments,boundary).run()

class EffectParameterResourcesMachine(EffectParameterSupportMachine,EffectProcessingMachine):
    def __init__(self,program,memory,name,arguments,boundary=None):
        self.program,self.operation,self.boundary=program,name,boundary
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        for name,(base,_) in STATIC.items():self.memory.update({base+i:v for i,v in enumerate(program.data[name])})
        self.public_memory=list(map(bytearray,memory))
        self.pc=REGIONS[self.operation][0];self.carry=self.flags=self.steps=0
        self.frames,self.returns,self.calls,self.internal_calls,self.service_sites=[],[],[],[],[]
        self.writes,self.visited,self.else_skips=[],set(),{}
        self.written,self.entries=set(),{}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[]
        for i,value in enumerate(arguments):
            if i<4:self.set(f'r{i}',value)
            else:DotMachine.write(self,STACK+4*(i-4),value,4)

    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def address(self,expression):
        if match:=re.fullmatch(r'\+\+(r\d+)=(r\d+)',expression):
            self.set(match[1],self.value(match[1])+self.value(match[2]));return self.value(match[1])
        return super().address(expression)
    def read(self,address,size):
        if address+size>1<<32:raise ValueError('resource read crosses address wrap')
        if 0x30000000<=address<STACK and not self.value('sp')<=address<=address+size<=STACK:
            raise ValueError('resource read escaped active stack')
        return DotMachine.read(self,address,size)
    def write(self,address,value,size):
        if address+size>1<<32:raise ValueError('resource write crosses address wrap')
        if 0x30000000<=address<STACK:
            if not self.value('sp')<=address<=address+size<=STACK:raise ValueError('resource stack escape')
        else:
            for (base,n),data in zip(MAPPED,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');break
            else:raise ValueError(f'resource write escaped map {address:#x}/{size}')
        self.writes.append((address,value&((1<<(8*size))-1),size));DotMachine.write(self,address,value,size)

    def single_step(self):
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #')
        next_pc=self.pc+size
        if match:=re.fullmatch(r'call (r\d+|-?\d+)',text):
            indirect=match[1].startswith('r');target=self.value(match[1]) if indirect else next_pc+int(match[1])
            actual_clear=indirect and self.pc==0x01c0656e and target==0x0201a9dc
            if (not indirect and target in self.program.code) or actual_clear:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            count=INDIRECT_ARITIES.get(self.pc) if indirect else SERVICES.get(target)
            if count is None or self.boundary is None:raise ValueError(f'unreviewed resource service {self.pc:#x}/{target:#x}')
            args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=self.snapshot();preserved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
            value=self.boundary(target,args,self)&MASK32
            if any(self.value(r)!=v for r,v in preserved.items()):raise ValueError('resource service changed callee-saved registers')
            self.calls.append((target,args,before,self.snapshot(),value));self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if match:=re.fullmatch(r'tbb \[(r\d+)\]',text):
            start=self.pc+size;target=start+2*self.read(start+self.value(match[1]),1)
            if target not in self.program.code:raise ValueError('resource branch target outside decoded code')
            self.pc=target;return True
        if match:=re.fullmatch(r'(r\d+) >>>= (r\d+)',text):
            self.set(match[1],signed(self.value(match[1]))>>(self.value(match[2])&31))
            self.pc=next_pc;return True
        return super().single_step()

    def run(self):
        while self.steps<4000000:
            self.steps+=1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value('sp')!=STACK:
                    raise ValueError('unbalanced resource execution')
                return {'result':(0 if self.operation in VOID else self.value('r0'),0),
                    'memory':self.snapshot(),'calls':self.calls,'service_sites':self.service_sites,
                    'internal_calls':self.internal_calls,'writes':self.writes,
                    'visited':self.visited,'steps':self.steps}
        raise ValueError('resource instruction budget exhausted')
