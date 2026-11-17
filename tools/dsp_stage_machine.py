"""Original stage/branch instructions with explicit unrecovered effect services."""
from __future__ import annotations
import hashlib
import re
from ir_processing_machine import IrProcessingMachine
from biquad_chain_machine import BiquadChainProgram
from dot_machine import DotMachine, ROOT, signed
from pi32v2isa import codec, table
from audio_task_machine import AudioTaskProgram,AudioTaskMachine

REGIONS = {
    "capability":(0x01c0558c,0x01c055a8), "active":(0x01c055d2,0x01c05618),
    "route_mask":(0x01c05618,0x01c05860), "clock":(0x01c10818,0x01c1082c),
    "stereo_prepare":(0x01c1082c,0x01c10968), "swap":(0x01c10968,0x01c10984),
    "branch_filters":(0x01c10984,0x01c10a4a), "branch_prepare":(0x01c10a4a,0x01c10b58),
    "mix_ramp":(0x01c10b58,0x01c10cac), "mix_select":(0x01c10cac,0x01c10cdc),
    "stereo_finish":(0x01c10cdc,0x01c10de8), "clear":(0x01c10de8,0x01c10e06),
    "stage":(0x01c10e06,0x01c11b00), "ir_delay":(0x01c11f66,0x01c11f76),
    "copy":(0x01c1a14c,0x01c1a182), "mix":(0x01c1a182,0x01c1a2c4),
}
ARITIES={"capability":2,"active":1,"route_mask":4,"clock":0,"stereo_prepare":4,
    "swap":2,"branch_filters":5,"branch_prepare":5,"mix_ramp":5,"mix_select":5,
    "stereo_finish":5,"clear":1,"stage":3,"ir_delay":1,"copy":3,"mix":1}
RAM,RAM_BYTES=0x01c1f180,0x01c344b4-0x01c1f180
SAMPLES,SAMPLE_BYTES,ARENA,ARENA_BYTES=0x35010000,1024,0x33000000,131072
MAPPED=((RAM,RAM_BYTES),(SAMPLES,SAMPLE_BYTES),(ARENA,ARENA_BYTES))
STACK=0x30001000
STATIC={"effect_capabilities":(0x0203b480,0x0203b4a8)}
SERVICES={0x01c04862:0,0x01c0f678:3,0x01c10446:4}

def offset(address):
    return address-0x02000120 if address>=0x02000000 else 0x02056780-0x02000120+address-0x01c00000

class DspStageProgram:
    def __init__(self):
        inherited=BiquadChainProgram();self.code=dict(inherited.code)
        self.inherited_code=set(self.code);self.regions={}
        app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.data={name:app[offset(start):offset(end)] for name,(start,end) in STATIC.items()}
        instructions=table.load()
        for name,(start,end) in REGIONS.items():
            raw=self.regions[name]=app[offset(start):offset(end)];cursor=0
            while cursor<len(raw):
                result=codec.decode(instructions,raw,cursor)
                if result is None:raise ValueError(f"undecoded stage instruction {start+cursor:#x}")
                instruction,fields,size=result;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        field=instruction.block[kind];spec=instruction.fields[field]
                        counts[i]=fields[field]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError("stage instruction crosses boundary")
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts;cursor+=size
        self.parallel_seconds=set()
        for pc,(text,size,_,_) in self.code.items():
            if text.endswith("  #"):
                following,second_size,_,_=self.code[pc+size]
                if second_size!=2 or "[" not in following:raise ValueError(f"unreviewed stage packet {pc:#x}")
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,name,arguments=(),boundary=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError("invalid stage memory")
        if name not in ARITIES or len(arguments)!=ARITIES[name]:raise ValueError("invalid stage entry")
        m=DspStageMachine(self,memory,boundary);m.pc=REGIONS[name][0]
        for i,v in enumerate(arguments):
            if not 0<=v<=0xffffffff:raise ValueError("invalid ABI word")
            if i<4:m.set(f"r{i}",v)
            else:DotMachine.write(m,STACK+4*(i-4),v,4)
        while m.steps<2000000:
            m.steps+=1
            if not m.step():break
        else:raise ValueError("stage instruction budget exhausted")
        if m.frames or m.returns or m.else_skips or m.value("sp")!=STACK:raise ValueError("unbalanced stage ABI")
        return {"value":m.value("r0"),"memory":m.snapshot(),"calls":m.calls,"real_calls":m.real_calls,
            "visited":m.visited,"steps":m.steps}

class DspStageMachine(IrProcessingMachine):
    def __init__(self,program,memory,boundary):
        self.program,self.boundary=program,boundary
        self.regs={f"r{i}":0 for i in range(16)};self.regs["sp"]=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory))
        for name,(start,end) in STATIC.items():self.memory.update({start+i:v for i,v in enumerate(program.data[name])})
        self.pc,self.carry,self.flags,self.steps=0,0,0,0
        self.frames,self.returns,self.calls,self.real_calls=[],[],[],[]
        self.visited,self.else_skips,self.written,self.entries=set(),{},set(),{}

    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def state_digest(self):return hashlib.sha256(b"".join(self.snapshot())).hexdigest()
    def read(self,address,size):
        if 0x30000000<=address<STACK and not self.value("sp")<=address<=address+size<=STACK:
            raise ValueError("read escaped allocated stage stack")
        return DotMachine.read(self,address,size)
    def write(self,address,value,size):
        if 0x30000000<=address<STACK:
            if not self.value("sp")<=address<=address+size<=STACK:raise ValueError("write escaped stage stack")
        else:
            for (base,n),data in zip(MAPPED,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,"little");break
            else:raise ValueError(f"write escaped mapped stage RAM {address:#x}")
        DotMachine.write(self,address,value,size)
    def single_step(self):
        self.visited.add(self.pc);text,size,_,_=self.program.code[self.pc];text=text.removesuffix("  #")
        if match:=re.fullmatch(r"\[--sp\] = \{r(\d+)-r4\}",text):
            saved={f"r{i}":self.value(f"r{i}") for i in range(4,int(match[1])+1)}
            self.frames.append((saved,self.value("sp")));self.set("sp",self.value("sp")-len(saved)*4);self.pc+=size;return True
        if re.fullmatch(r"\{r\d+-r4\} = \[sp\+\+\]",text):
            saved,sp=self.frames.pop();self.regs.update(saved,sp=sp);self.pc+=size;return True
        if match:=re.fullmatch(r"rep (4|16) (r\d+) \{",text):
            body=self.pc+size;end=body+int(match[1])
            if not 1<=self.value(match[2])<=256:raise ValueError("invalid positive stage REP count")
            while self.value(match[2]):
                self.pc=body
                while self.pc<end:
                    self.steps+=1
                    if not self.step():raise ValueError("stage REP returned")
                if self.pc!=end:raise ValueError("stage REP escaped")
                self.set(match[2],self.value(match[2])-1)
            self.pc=end;return True
        if text.startswith("call "):
            target=self.value(text[5:]) if text[5:].startswith("r") else self.pc+size+int(text[5:])
            if target in self.program.code:
                self.real_calls.append(target);self.returns.append(self.pc+size);self.pc=target;return True
            if target not in SERVICES or self.boundary is None:raise ValueError(f"unmodeled stage call {target:#x}")
            args=tuple(self.value(f"r{i}") for i in range(SERVICES[target]))
            event=(target,args,self.state_digest());self.calls.append(event)
            value=self.boundary(target,args,self)
            for i in range(4):self.set(f"r{i}",0xbad0c0de)
            self.set("r0",value);self.pc+=size;return True
        if match:=re.fullmatch(r"(r\d+_r\d+) = (r\d+) \* (r\d+) \(u\)",text):
            self.set_pair(match[1],self.value(match[2])*self.value(match[3]));self.pc+=size;return True
        if match:=re.fullmatch(r"(r\d+_r\d+) <<= (\d+)",text):
            self.set_pair(match[1],self.pair(match[1])<<(int(match[2])&63));self.pc+=size;return True
        if match:=re.fullmatch(r"(r\d+_r\d+) = (r\d+_r\d+) / (r\d+) \(u\)",text):
            denominator=self.value(match[3])
            if not denominator:raise ValueError("zero transition divisor")
            self.set_pair(match[1],self.pair(match[2])//denominator);self.pc+=size;return True
        if match:=re.fullmatch(r"(r\d+) = (r\d+) ([&|]) \(1 << (r\d+)\)",text):
            bit=1<<(self.value(match[4])&31);value=self.value(match[2])
            self.set(match[1],value&bit if match[3]=='&' else value|bit);self.pc+=size;return True
        if match:=re.fullmatch(r"if \(\((r\d+) & (r\d+|0x[0-9A-Fa-f]+|\d+)\) (==|!=) 0\) (\{|goto (-?\d+))",text):
            mask=self.value(match[2]) if not match[2].startswith('0x') else int(match[2],16)
            condition=bool(self.value(match[1])&mask)==(match[3]=='!=');next_pc=self.pc+size
            if match[4]=='{':
                _,_,then,otherwise=self.program.code[self.pc];after=self.skip(next_pc,then)
                if not condition:next_pc=after
                elif otherwise:self.else_skips[after]=self.skip(after,otherwise)
            elif condition:next_pc+=int(match[5])
            self.pc=next_pc;return True
        return super().single_step()

class DspStageAudioProgram(AudioTaskProgram):
    def __init__(self):
        super().__init__();self.stage=DspStageProgram()
        for pc in self.code.keys()&self.stage.code.keys():
            if self.code[pc]!=self.stage.code[pc]:raise ValueError("inconsistent joined stage instruction")
        self.code.update(self.stage.code);self.parallel_seconds|=self.stage.parallel_seconds
    def machine(self,memory,boundary=None):return DspStageAudioMachine(self,memory,boundary)

class DspStageAudioMachine(AudioTaskMachine):
    def __init__(self,program,memory,boundary):
        AudioTaskMachine.__init__(self,program,memory,boundary);self.flags=0;self.entries={}
        self.stage_view=object.__new__(DspStageMachine)
        for name,(start,end) in STATIC.items():self.memory.update({start+i:v for i,v in enumerate(program.stage.data[name])})
    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.stage.code:return super().step()
        # Borrow the same registers, frames and mapped bytes for one original
        # instruction packet. This avoids changing either frozen ISA model.
        view=self.stage_view;view.__dict__.update(self.__dict__)
        view.read=lambda address,size:AudioTaskMachine.read(view,address,size)
        view.write=lambda address,value,size:AudioTaskMachine.write(view,address,value,size)
        result=DspStageMachine.step(view)
        for name,value in view.__dict__.items():
            if name not in ('read','write'):self.__dict__[name]=value
        if self.written is None:self.written=set()
        return result
