"""Execute bounded prefixes of the complete original nonreturning audio task."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from dsp_dynamics_processing_machine import DspDynamicsProcessingProgram, DspDynamicsProcessingMachine, ROOT
from biquad_chain_machine import BiquadChainProgram, REGIONS as CHAIN_REGIONS
from capture_warmup_machine import CaptureWarmupProgram
from capture_processing_machine import TABLE_START, TABLE_END
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

TASK, POLL, WAIT_CALL, AFTER_WAIT = 0x01C01E5E, 0x01C02D42, 0x01C02D74, 0x01C02D7A
FATAL = (0x01C02DA2, 0x01C02DBA)
STATE, CONTROL = 0x01C26890, 0x01C1F180
RAM, RAM_BYTES = CONTROL, 0x01C344B4-CONTROL
RECORD, PLAY, ARENA = 0x35000000, 0x35010000, 0x32040000
MAPPED = ((RAM, RAM_BYTES), (RECORD, 8192), (PLAY, 512), (ARENA, 131072))
STACK = 0x30001000
REGIONS = {
    "task": (TASK, 0x01C02DBC), "fir": (0x01C01234, 0x01C01292),
    "tap": (0x01C01292, 0x01C012D8), "warmup": (0x01C04C42, 0x01C04CD8),
    "effect_scan": (0x01C05118, 0x01C05160), "set_input": (0x01C05D40, 0x01C05D4A),
}
STATIC = {"recording_taps9": (0x020364D6, 0x020364E0),
          "recording_taps19": (0x02036F24, 0x02036F38)}
SERVICES = {
    0x01C012D8: 1, 0x01C0158A: 1, 0x01C01690: 1, 0x01C01722: 2,
    0x01C0174E: 2, 0x01C0179E: 3, 0x01C01800: 1, 0x01C0198A: 1,
    0x01C019D8: 2, 0x01C01DE4: 5, 0x01C04862: 0, 0x01C048A4: 0,
    0x01C04CDA: 2, 0x01C10E06: 3, 0x01C11B00: 0, 0x01C11BFA: 2,
    0x01C11C66: 0, 0x01C11C7E: 2, 0x01C11D06: 1, 0x01C1245C: 0,
    0x01C19EFA: 3, 0x02002D10: 3, 0x0201AAEA: 2, 0x0201AB28: 0,
    0x02040D34: 2,
}


def image_offset(address):
    return address-0x02000120 if address>=0x02000000 else 0x02056780-0x02000120+address-0x01C00000


class AudioTaskProgram(DspDynamicsProcessingProgram):
    def __init__(self):
        super().__init__()
        self.pre_task_code = set(self.code)
        self.chain, self.capture = BiquadChainProgram(), CaptureWarmupProgram()
        for inherited in (self.chain, self.capture):
            for pc in self.code.keys() & inherited.code.keys():
                if self.code[pc] != inherited.code[pc]:
                    raise ValueError("inconsistent inherited audio instruction")
            self.code.update(inherited.code)
        app = (ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.task_regions = {}
        self.task_data = {name: app[image_offset(start):image_offset(end)] for name,(start,end) in STATIC.items()}
        instructions = table.load()
        for name,(start,end) in REGIONS.items():
            raw = self.task_regions[name] = app[image_offset(start):image_offset(end)]
            cursor = 0
            while cursor<len(raw):
                decoded = codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError(f"undecoded audio-task instruction at {start+cursor:#x}")
                instruction,fields,size = decoded
                counts = [0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        field = instruction.block[kind];spec = instruction.fields[field]
                        counts[i] = fields[field]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError("audio-task instruction crosses its region")
                self.code[start+cursor] = codec.format(instruction,fields),size,*counts
                cursor += size
        self.parallel_seconds = set()
        for pc,(text,size,_,_) in self.code.items():
            if text.endswith("  #"):
                following,second_size,_,_ = self.code[pc+size]
                if not re.match(r"r\d+(?:_r\d+)? (?:=|\+=|\^=|\*=|>>>=)",text) or second_size!=2 or "[" not in following:
                    raise ValueError(f"unreviewed task parallel packet at {pc:#x}")
                self.parallel_seconds.add(pc+size)
        self.table = self.capture.table
        self.kernel_starts = self.capture.kernel_starts

    def machine(self,memory,boundary=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):
            raise ValueError("invalid audio-task comparison map")
        return AudioTaskMachine(self,memory,boundary)

    def execute_helper(self,memory,name,arguments=(),boundary=None):
        if name not in REGIONS or name=="task":raise ValueError("unknown task helper")
        arities={"fir":5,"tap":2,"warmup":0,"effect_scan":1,"set_input":1}
        if len(arguments)!=arities[name] or any(not 0<=v<=0xFFFFFFFF for v in arguments):
            raise ValueError("invalid helper arguments")
        machine=self.machine(memory,boundary);machine.pc=REGIONS[name][0]
        for i,value in enumerate(arguments):
            if i<4:machine.regs[f"r{i}"]=value
            else:DotMachine.write(machine,STACK+4*(i-4),value,4)
        while machine.steps<50000000:
            machine.steps+=1
            if not machine.step():break
        else:raise ValueError("task helper instruction budget exceeded")
        if machine.frames or machine.returns or machine.else_skips or machine.value("sp")!=STACK:
            raise ValueError("unbalanced task helper ABI")
        return {"value":machine.value("r0"),"memory":machine.snapshot(),"calls":machine.calls,
            "real_calls":machine.real_calls,"visited":machine.visited,"steps":machine.steps}


class AudioTaskMachine(DspDynamicsProcessingMachine):
    def __init__(self,program,memory,boundary):
        self.program,self.boundary = program,boundary
        self.regs = {f"r{i}":0 for i in range(16)};self.regs["sp"] = STACK
        self.memory = {base+i:value for (base,_),data in zip(MAPPED,memory) for i,value in enumerate(data)}
        self.public_memory=[bytearray(data) for data in memory]
        for name,(start,end) in STATIC.items():
            self.memory.update({start+i:value for i,value in enumerate(program.task_data[name])})
        self.pc,self.carry,self.steps = TASK,0,0
        self.frames,self.returns,self.calls,self.writes = [],[],[],[]
        self.visited,self.else_skips,self.written = set(),{},set()
        self.waits,self.completed_frames,self.fatal_site = 0,0,0
        self.real_calls = []
        self.frame_active = False

    def snapshot(self):
        return tuple(map(bytes,self.public_memory))

    def state_digest(self):
        digest = hashlib.sha256()
        for data in self.snapshot():digest.update(data)
        return digest.hexdigest()

    def read(self,address,size):
        if 0x30000000<=address<STACK and not self.value("sp")<=address<=address+size<=STACK:
            raise ValueError("task read escaped allocated stack")
        return DotMachine.read(self,address,size)

    def write(self,address,value,size):
        if 0x30000000<=address<STACK:
            if not self.value("sp")<=address<=address+size<=STACK:raise ValueError("task write escaped allocated stack")
        elif not any(base<=address<=address+size<=base+n for base,n in MAPPED):
            raise ValueError(f"task write escaped mapped RAM at {address:#x}")
        for (base,n),data in zip(MAPPED,self.public_memory):
            if base<=address<=address+size<=base+n:
                data[address-base:address-base+size]=(value&((1<<(size*8))-1)).to_bytes(size,"little")
                break
        self.writes.append((address,value&((1<<(size*8))-1),size))
        DotMachine.write(self,address,value,size)

    def address(self,expression):
        if match:=re.fullmatch(r"\+\+(r\d+)=(r\d+|-?\d+)",expression):
            self.set(match[1],self.value(match[1])+self.value(match[2]));return self.value(match[1])
        return super().address(expression)

    def single_step(self):
        text,size,then,otherwise = self.program.code[self.pc]
        text=text.removesuffix("  #");next_pc=self.pc+size
        self.visited.add(self.pc)
        if match:=re.fullmatch(r"call (-?\d+|r\d+)",text):
            target=self.value(match[1]) if match[1].startswith("r") else next_pc+int(match[1])
            if target in self.program.code:
                self.real_calls.append((target,tuple(self.value(f"r{i}") for i in range(4))))
                self.returns.append(next_pc);next_pc=target
            else:
                if target not in SERVICES:raise ValueError(f"unreviewed task service {target:#x}")
                count=SERVICES[target]
                args=tuple(self.value(f"r{i}") if i<4 else self.read(self.value("sp"),4) for i in range(count))
                self.calls.append((target,args,self.state_digest()))
                result=self.boundary(target,args,self) if self.boundary else 0
                for register in ("r0","r1","r2","r3"):self.set(register,0xBAD0C0DE)
                self.set("r0",result)
                if self.pc==WAIT_CALL:self.waits+=1
        elif match:=re.fullmatch(r"(r\d+) = sp \+ (\d+)",text):
            self.set(match[1],self.value("sp")+int(match[2]))
        elif match:=re.fullmatch(r"(r\d+_r\d+) = d\[(.+)\]",text):
            self.set_pair(match[1],self.read(self.address(match[2]),8))
        elif match:=re.fullmatch(r"d\[(.+)\] = (r\d+_r\d+)",text):
            self.write(self.address(match[1]),self.pair(match[2]),8)
        elif match:=re.fullmatch(r"\[(.+)\] \+= (r\d+|-?\d+|0x[0-9a-fA-F]+)",text):
            address=self.address(match[1]);self.write(address,self.read(address,4)+self.value(match[2]),4)
        elif match:=re.fullmatch(r"if \(\((r\d+) & (r\d+|0x[0-9a-fA-F]+|\d+)\) (==|!=) 0\) (?:goto (-?\d+)|(\{))",text):
            condition=bool(self.value(match[1])&self.value(match[2]))==(match[3]=="!=")
            if match[4]:
                if condition:next_pc+=int(match[4])
            else:
                end=self.skip(next_pc,then)
                if not condition:next_pc=end
                elif otherwise:self.else_skips[end]=self.skip(end,otherwise)
        elif match:=re.fullmatch(r"(r\d+) = (r\d+)\.b0 \(u\)",text):
            self.set(match[1],self.value(match[2])&255)
        elif match:=re.fullmatch(r"(r\d+_r\d+) >>= (\d+)",text):
            self.set_pair(match[1],self.pair(match[1])>>(int(match[2])&63))
        elif match:=re.fullmatch(r"(r\d+_r\d+) \+= (r\d+) \* (r\d+) \(s\)",text):
            self.set_pair(match[1],self.pair(match[1])+signed(self.value(match[2]))*signed(self.value(match[3])))
        elif match:=re.fullmatch(r"rep (\d+) (\d+) \{",text):
            length,count=int(match[1]),int(match[2]);body=next_pc
            for _ in range(count):
                self.pc=body
                while self.pc<body+length:
                    if not self.step():raise ValueError("REP body returned")
                    self.steps+=1
                if self.pc!=body+length:raise ValueError("REP escaped task block")
            next_pc=body+length
        elif match:=re.fullmatch(r"tbb \[(r\d+)\]",text):
            index=self.value(match[1])
            if self.pc!=TABLE_START-2 or index>=4:raise ValueError("invalid capture dispatch")
            next_pc=TABLE_START+2*self.program.table[index]
        elif match:=re.fullmatch(r"(r\d+) = (r\d+) & (r\d+)",text):
            self.set(match[1],self.value(match[2])&self.value(match[3]))
        elif match:=re.fullmatch(r"(r\d+) &= (r\d+)",text):
            self.set(match[1],self.value(match[1])&self.value(match[2]))
        elif match:=re.fullmatch(r"(r\d+) = (r\d+) \| (r\d+|0x[0-9A-Fa-f]+)",text):
            self.set(match[1],self.value(match[2])|self.value(match[3]))
        elif match:=re.fullmatch(r"(r\d+) = ([us])(max|min)\((r\d+), (r\d+)\)",text):
            a,b=self.value(match[4]),self.value(match[5])
            if match[2]=="s":a,b=signed(a),signed(b)
            self.set(match[1],(max if match[3]=="max" else min)(a,b))
        elif match:=re.fullmatch(r"h\[(.+)\] = (r\d+)",text):
            self.write(self.address(match[1]),self.value(match[2]),2)
        elif match:=re.fullmatch(r"(r\d+) <= insert\((r\d+), p:(\d+), l:(\d+)\)",text):
            position,length=int(match[3]),int(match[4]);mask=((1<<length)-1)<<position
            self.set(match[1],(self.value(match[1])&~mask)|((self.value(match[2])<<position)&mask))
        elif match:=re.fullmatch(r"\[(.+)\] = (0x[0-9A-Fa-f]+)",text):
            self.write(self.address(match[1]),int(match[2],16),4)
        elif match:=re.fullmatch(r"(r\d+_r\d+) = (r\d+_r\d+) \+ (r\d+_r\d+)",text):
            self.set_pair(match[1],self.pair(match[2])+self.pair(match[3]))
        elif match:=re.fullmatch(r"(r\d+_r\d+) \+= h\[(r\d+) \+\+= 2\]\*(r\d+) \(s\)",text):
            self.set_pair(match[1],self.pair(match[1])+signed(self.read(self.value(match[2]),2),16)*signed(self.value(match[3])))
            self.set(match[2],self.value(match[2])+2)
        elif text=="r1_r0 += h[r6 ++= 2]*[r4 ++= 4] (s)":
            self.set_pair("r1_r0",self.pair("r1_r0")+signed(self.read(self.value("r6"),2),16)*signed(self.read(self.value("r4"),4)))
            self.set("r6",self.value("r6")+2);self.set("r4",self.value("r4")+4)
        elif match:=re.fullmatch(r"(r\d+) >>= (r\d+)",text):
            self.set(match[1],self.value(match[1])>>(self.value(match[2])&31))
        else:return super().single_step()
        self.pc=next_pc;return True

    def resume(self,wait_budget=1,frame_budget=1):
        if wait_budget<1 or frame_budget<1:raise ValueError("task budgets must be positive")
        waits,frames=self.waits,self.completed_frames
        while self.steps<50000000:
            if self.pc in FATAL:
                self.fatal_site=self.pc
                self.steps+=1;self.step()
                if self.pc!=self.fatal_site:raise ValueError("fatal branch did not spin")
                reason=2;break
            if self.pc==POLL and self.frame_active:
                self.completed_frames+=1;self.frame_active=False
                if self.completed_frames-frames>=frame_budget:reason=1;break
            if self.pc==AFTER_WAIT and self.waits-waits>=wait_budget:reason=0;break
            if self.pc==0x01C01EBC:self.frame_active=True
            self.steps+=1
            if not self.step():raise ValueError("nonreturning task unexpectedly returned")
        else:raise ValueError("audio-task instruction budget exceeded")
        phase=3 if reason==2 else 1 if reason==0 else 2
        return {"reason":reason,"task":(phase,self.waits,self.completed_frames,self.fatal_site),
            "memory":self.snapshot(),"calls":list(self.calls),"real_calls":list(self.real_calls),
            "visited":set(self.visited),"steps":self.steps,"pc":self.pc}
