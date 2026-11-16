"""Execute complete dynamics sample callers/kernel against original instructions.

The retained configuration/startup model supplies real coefficient arithmetic.
No numerical, memory-copy, scheduler or notification callback is scripted here.
"""
from __future__ import annotations
import re
import struct

from dsp_audio_path_machine import (DspAudioPathProgram, DspAudioPathMachine,
    REGIONS as AUDIO_REGIONS, MAPPED as AUDIO_MAPPED, DYNAMICS_REGIONS,
    INITIALIZATION_REGIONS, MATH_REGIONS, PRIOR_REGIONS, ROOT, CONTROL,
    CONFIGURATION, TABLE, PRIOR_TABLE, RESET_CONFIGURATION, STATIC,
    region_bytes, BiquadProgram, BUFFER)
from dsp_dynamics_machine import OUTPUT
from dsp_initialization_machine import STACK
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS={"reset":(0x01C11B00,0x01C11BFA), "single":(0x01C11BFA,0x01C11C66),
    "clone":(0x01C11C66,0x01C11C7E), "dual":(0x01C11C7E,0x01C11D06),
    "kernel":(0x01C1A636,0x01C1AB40)}
DEPENDENCIES={"copy_words":(0x01C1A14C,0x01C1A182)}
STATES=0x01C1F820
MAPPED=(*AUDIO_MAPPED,(STATES,500))
ARITIES={"reset":0,"single":1,"clone":0,"dual":1,"kernel":3,
    "startup":0,"configure":3,"get":0,"meter":1}


class DspDynamicsProcessingProgram(DspAudioPathProgram):
    def __init__(self):
        super().__init__()
        self.pre_processing_code=set(self.code)
        self.processing_regions,self.dependencies={},{}
        app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions=table.load()
        for name,(start,end) in (REGIONS|DEPENDENCIES).items():
            raw=region_bytes(app,start,end)
            (self.processing_regions if name in REGIONS else self.dependencies)[name]=raw
            cursor=0
            while cursor<len(raw):
                decoded=codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError(f"unsupported dynamics-processing instruction {start+cursor:#x}")
                instruction,fields,size=decoded
                counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError("instruction crosses dynamics-processing function boundary")
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts
                cursor+=size
        self.new_code={pc for pc in self.code if any(lo<=pc<hi for lo,hi in REGIONS.values())}
        for pc in set(self.code)-self.pre_processing_code:
            text,size,_,_=self.code[pc]
            if text.endswith("  #"):
                following,second,_,_=self.code[pc+size]
                if not re.match(r"r\d+ = ",text) or second!=2 or "[" not in following:
                    raise ValueError("unreviewed dynamics-processing parallel packet")
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,operation,work=(),*arguments):
        if (tuple(map(len,memory))!=tuple(n for _,n in MAPPED) or operation not in ARITIES
            or len(arguments)!=ARITIES[operation] or any(not 0<=v<=MASK32 for v in arguments)
            or len(work)!=(176 if operation in ("kernel","single","dual") else 0)
            or any(not -(1<<31)<=v<(1<<31) for v in work)
            or (operation=="kernel" and arguments[0]>1)
            or (operation=="meter" and arguments[0]>3)):
            raise ValueError("outside dynamics-processing call domain")
        if operation=="configure" and not int.from_bytes(memory[0][36:40],"little"):
            raise ValueError("zero configuration divisor does not terminate original float producer")
        if operation=="startup" and not memory[1][0]:
            if any(not -1280<=v<=1280 for v in struct.unpack_from("<5h",memory[4],218)):
                raise ValueError("startup parameters outside inherited domain")
        return DspDynamicsProcessingMachine(self,memory,operation,work,arguments).run()


class DspDynamicsProcessingMachine(DspAudioPathMachine):
    def __init__(self,program,memory,operation,work,arguments):
        super().__init__(program,memory[:len(AUDIO_MAPPED)],"startup",(),())
        self.memory.update({STATES+i:byte for i,byte in enumerate(memory[-1])})
        self.samples=len(work)
        for i,value in enumerate(work):DotMachine.write(self,BUFFER+4*i,value,4)
        self.processing_calls=[]
        self.pc=(REGIONS|DYNAMICS_REGIONS|{"startup":INITIALIZATION_REGIONS["startup"]})[operation][0]
        self.regs.update(r0=BUFFER,r1=arguments[0] if arguments else 0,r2=0,r3=0)
        if operation=="kernel":self.regs.update(r0=STATES+256*arguments[0],r1=BUFFER,r2=arguments[1],r3=arguments[2])
        elif operation=="configure":self.regs.update({f"r{i}":v for i,v in enumerate(arguments)})
        elif operation=="get":self.regs.update(r0=OUTPUT,r1=OUTPUT+4,r2=OUTPUT+8)
        elif operation=="meter":self.regs.update(r0=OUTPUT if arguments[0]&1 else 0,r1=OUTPUT+4 if arguments[0]&2 else 0)

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(n)) for base,n in MAPPED)

    def write(self,address,value,size):
        if 0x30000000<=address<STACK:
            if not self.value("sp")<=address<=address+size<=STACK:
                raise ValueError("dynamics-processing stack write escaped frame")
        elif not any(base<=address and address+size<=base+n for base,n in (*MAPPED,(BUFFER,self.samples*4),(OUTPUT,12))):
            raise ValueError(f"dynamics-processing write escaped public state {address:#x}")
        self.writes.append((address,value&((1<<(8*size))-1),size))
        DotMachine.write(self,address,value,size)

    def single_step(self):
        text,size,_,_=self.program.code[self.pc]
        text=text.removesuffix("  #");next_pc=self.pc+size
        if m:=re.fullmatch(r"call (-?\d+)",text):
            target=next_pc+int(m[1])
            if target in {lo for lo,hi in (REGIONS|DEPENDENCIES).values()}:
                self.processing_calls.append((target,tuple(self.value(f"r{i}") for i in range(4))))
        self.visited.add(self.pc)
        if m:=re.fullmatch(r"(r\d+) = smax\((r\d+), (r\d+)\)",text):
            self.set(m[1],max(signed(self.value(m[2])),signed(self.value(m[3]))))
        elif m:=re.fullmatch(r"(r\d+) = (r\d+) \^ (r\d+)",text):
            self.set(m[1],self.value(m[2])^self.value(m[3]))
        elif m:=re.fullmatch(r"(r\d+) \^= (r\d+)",text):
            self.set(m[1],self.value(m[1])^self.value(m[2]))
        elif m:=re.fullmatch(r"rep (\d+) (r\d+) \{",text):
            count=self.value(m[2]);body,end=next_pc,next_pc+int(m[1])
            if not 1<=count<=255:raise ValueError("outside positive bounded REP semantics")
            while self.value(m[2]):
                self.pc=body
                while self.pc<end:
                    self.steps+=1
                    if not self.step():raise ValueError("REP body returned")
                if self.pc!=end:raise ValueError("REP body escaped its byte length")
                self.set(m[2],self.value(m[2])-1)
            next_pc=end
        else:return super().single_step()
        self.pc=next_pc
        return True

    def run(self):
        result=super().run()
        result["processing_calls"]=self.processing_calls
        return result
