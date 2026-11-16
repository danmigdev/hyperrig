"""Execute original parameter requests, then the recovered four-section path.

The only optional service is the sixth-parameter notification. Every staged
coefficient/gain word is produced by original instructions, never a fixture.
"""
from __future__ import annotations
import re
import struct

from dsp_audio_path_machine import (DspAudioPathProgram,DspAudioPathMachine,
    REGIONS as AUDIO_REGIONS,MAPPED,ROOT,FLOAT,CONTROL,CONFIGURATION,CALLBACKS,
    TABLE,PRIOR_TABLE,RESET_CONFIGURATION,STATIC as AUDIO_STATIC,region_bytes,
    DYNAMICS_REGIONS,INITIALIZATION_REGIONS,MATH_REGIONS,PRIOR_REGIONS,BiquadProgram,
    BUFFER,FILTERS,STACK)
from biquad_coefficients_machine import PRODUCER
from dot_machine import DotMachine,MASK32,signed
from pi32v2isa import codec,table

REGIONS={"clamp":(0x02028936,0x02028968),"request":(0x02028A34,0x02028B6C)}
INPUT=0x31020000
CALLBACK=CALLBACKS+732
STATIC={"installed_callback":(0x0201A9EA,0x0201AA08)}


class DspTransitionProgram(DspAudioPathProgram):
    def __init__(self):
        super().__init__()
        self.pre_transition_code=set(self.code)
        self.transition_regions={}
        app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.transition_static={name:region_bytes(app,*bounds) for name,bounds in STATIC.items()}
        instructions=table.load()
        for name,(start,end) in REGIONS.items():
            raw=self.transition_regions[name]=region_bytes(app,start,end)
            cursor=0
            while cursor<len(raw):
                decoded=codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError(f"unsupported transition instruction at {start+cursor:#x}")
                instruction,fields,size=decoded
                counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError("transition instruction crosses function boundary")
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts
                cursor+=size
        if any(self.code[pc][0].endswith("  #") for pc in set(self.code)-self.pre_transition_code):
            raise ValueError("unreviewed transition parallel packet")

    def execute(self,memory,operation,samples=(),*arguments,parameters=None,boundary=None):
        if operation not in REGIONS:return super().execute(memory,operation,samples,*arguments)
        if (tuple(map(len,memory))!=tuple(size for _,size in MAPPED) or samples
                or len(arguments)!=(2 if operation=="clamp" else 1)
                or any(not 0<=x<=MASK32 for x in arguments)):
            raise ValueError("outside transition call domain")
        if operation=="request":
            if parameters is None or len(parameters)!=6 or any(not -32768<=x<=32767 for x in parameters):
                raise ValueError("request needs six signed16 parameters")
            if not memory[4][28] and any(not -1280<=x<=1280 for x in struct.unpack_from("<5h",memory[4],218)):
                raise ValueError("disabled-bank reset outside inherited parameter domain")
        return DspTransitionMachine(self,memory,operation,arguments,parameters,boundary).run()


class DspTransitionMachine(DspAudioPathMachine):
    def __init__(self,program,memory,operation,arguments,parameters,boundary):
        super().__init__(program,memory,"process",(),())
        self.transition_boundary,self.notification_calls=boundary,[]
        self.pc=REGIONS[operation][0]
        self.operation=operation
        if operation=="clamp":self.regs.update(r0=arguments[0],r1=arguments[1])
        else:
            self.regs.update(r0=INPUT,r1=arguments[0])
            for i,value in enumerate(parameters):DotMachine.write(self,INPUT+2*i,value,2)

    def mutate(self,address,value,size):
        if not any(base<=address and address+size<=base+length for base,length in MAPPED):
            raise ValueError("notification mutation escaped runtime")
        self.write(address,value,size)

    def single_step(self):
        text,size,_,_=self.program.code[self.pc]
        text=text.removesuffix("  #")
        next_pc=self.pc+size
        if match:=re.fullmatch(r"call (-?\d+)",text):
            target=next_pc+int(match[1])
            if target==PRODUCER[0] and self.value("r0")!=FILTERS and STACK-256<=self.value("r0")<STACK:
                destination=self.value("r0")
                if destination+44>STACK or destination<self.value("sp"):
                    raise ValueError("unreviewed transition coefficient local")
                request=(self.value("r1"),self.value("r2"),self.value("r3"),self.read(self.value("sp"),4))
                self.production_calls.append(("local",destination,request,self.snapshot()))
                self.math_calls.append(("generate",destination))
                self.visited.add(self.pc);self.returns.append(next_pc);self.pc=target
                return True
        self.visited.add(self.pc)
        if text=="call r1":
            if self.pc!=0x02028A9E or not self.value("r1") or not self.transition_boundary:
                raise ValueError("unreviewed sixth-parameter callback")
            token,value=self.value("r1"),self.value("r0")
            before=self.snapshot()
            self.transition_boundary(token,signed(value),self)
            self.notification_calls.append((token,signed(value),before,self.snapshot()))
            for register in ("r0","r1","r2","r3"):self.set(register,0xBAD0C0DE)
        elif match:=re.fullmatch(r"(r\d+) = (r\d+)\.l \(s\)",text):
            self.set(match[1],signed(self.value(match[2])&65535,16))
        elif match:=re.fullmatch(r"(r\d+) \|= (\d+)",text):
            self.set(match[1],self.value(match[1])|int(match[2]))
        elif match:=re.fullmatch(r"(r\d+) = sp \+ (-?\d+)",text):
            self.set(match[1],self.value("sp")+int(match[2]))
        else:return super().single_step()
        self.pc=next_pc
        return True

    def run(self):
        result=super().run()
        result.update(notification_calls=self.notification_calls,
            parameters=tuple(signed(self.read(INPUT+2*i,2),16) for i in range(6)) if self.operation=="request" else None)
        return result
