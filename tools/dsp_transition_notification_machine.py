"""Execute the installed transition callback and its original gain mixer."""
from __future__ import annotations
import re
import struct

from dsp_transition_machine import (DspTransitionProgram,DspTransitionMachine,
    REGIONS as TRANSITION_REGIONS,MAPPED as PRIOR_MAPPED,INPUT,PRODUCER,
    DspAudioPathMachine,ROOT,region_bytes,STACK,FILTERS)
from dsp_audio_path_machine import REGIONS as AUDIO_REGIONS,INITIALIZATION_REGIONS
from dot_machine import DotMachine,MASK32,signed
from pi32v2isa import codec,table

REGIONS={"notify":(0x0201A9EA,0x0201AA08)}
GAIN_REGIONS={"clamp":(0x02007ECE,0x02007EE2),"scale":(0x02007EE2,0x02007EF2),
    "mix":(0x02007EF2,0x02007F3A),"set_gain":(0x02007F3A,0x02007F50)}
STATE,GAIN_TABLE,GAIN_BYTES=0x01C26890,0x02033BC8,196
MAPPED=(*PRIOR_MAPPED,(STATE,280),(INPUT,12))
NOTIFICATION=REGIONS["notify"][0]


class DspTransitionNotificationProgram(DspTransitionProgram):
    def __init__(self):
        super().__init__()
        self.pre_notification_code=set(self.code);self.notification_regions={}
        app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes();instructions=table.load()
        self.gain_table=region_bytes(app,GAIN_TABLE,GAIN_TABLE+GAIN_BYTES)
        for name,(start,end) in {**REGIONS,**{f"gain_{k}":v for k,v in GAIN_REGIONS.items()}}.items():
            raw=self.notification_regions[name]=region_bytes(app,start,end);cursor=0
            while cursor<len(raw):
                decoded=codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError(f"undecoded notification instruction at {start+cursor:#x}")
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        field=instruction.block[kind];spec=instruction.fields[field]
                        counts[i]=fields[field]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError("notification instruction crosses complete body")
                item=codec.format(instruction,fields),size,*counts
                if start+cursor in self.code and self.code[start+cursor]!=item:raise ValueError("inconsistent reused gain instruction")
                self.code[start+cursor]=item;cursor+=size

    def execute(self,memory,operation,samples=(),*arguments,boundary=None):
        arities={"notify":1,"mix":1,"set_gain":2,"request":2,"startup":0,"process":0}
        if (operation not in arities or len(arguments)!=arities[operation]
            or tuple(map(len,memory))!=tuple(n for _,n in MAPPED)
            or any(not 0<=value<=MASK32 for value in arguments)
            or len(samples)>128 or (samples and operation!="process")
            or any(not -(1<<31)<=value<(1<<31) for value in samples)):
            raise ValueError("outside borrowed transition comparison domain")
        if ((operation=="request" and not memory[4][28]) or (operation=="startup" and not memory[1][0])):
            if any(not -1280<=value<=1280 for value in struct.unpack_from("<5h",memory[4],218)):
                raise ValueError("disabled-bank reset outside prior parameter domain")
        return DspTransitionNotificationMachine(self,memory,operation,samples,arguments,boundary).run()


class DspTransitionNotificationMachine(DspTransitionMachine):
    def initialize_notification_state(self):
        """For a shared-memory derived VM: preserve registers, frames and RAM.

        Invoke after the inherited DSP machine has initialized its fields. This
        adds only immutable gain-table bytes and notification audit counters.
        Derived VMs provide snapshot/write/mutate and their external callback
        through transition_boundary; the installed callback never uses it.
        """
        self.memory.update({GAIN_TABLE+i:value for i,value in enumerate(self.program.gain_table)})
        self.real_notifications=[];self.pending_notifications=[];self.gain_calls=[]

    def __init__(self,program,memory,operation,samples,arguments,boundary):
        DspAudioPathMachine.__init__(self,program,memory[:len(PRIOR_MAPPED)],"process",samples,())
        for (base,_),data in zip(MAPPED[len(PRIOR_MAPPED):],memory[len(PRIOR_MAPPED):]):
            self.memory.update({base+i:value for i,value in enumerate(data)})
        self.initialize_notification_state()
        self.operation=operation;self.transition_boundary=boundary;self.notification_calls=[]
        self.parameter_token=arguments[0] if operation=="request" else INPUT
        if operation=="startup":self.pc=INITIALIZATION_REGIONS["startup"][0]
        elif operation=="process":self.pc=AUDIO_REGIONS["process"][0]
        elif operation=="request":self.pc=TRANSITION_REGIONS["request"][0]
        elif operation in REGIONS:self.pc=REGIONS[operation][0]
        else:self.pc=GAIN_REGIONS[operation][0]
        if operation not in ("startup","process"):
            self.regs.update({f"r{i}":value for i,value in enumerate(arguments)})

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(size)) for base,size in MAPPED)

    def write(self,address,value,size):
        if GAIN_TABLE<=address<GAIN_TABLE+GAIN_BYTES:raise ValueError("write to immutable capture gain table")
        if any(base<=address and address+size<=base+length for base,length in MAPPED[len(PRIOR_MAPPED):]):
            self.writes.append((address,value&((1<<(8*size))-1),size));DotMachine.write(self,address,value,size)
        else:super().write(address,value,size)

    def mutate(self,address,value,size):
        if not any(base<=address and address+size<=base+length for base,length in MAPPED):
            raise ValueError("notification mutation escaped shared map")
        self.write(address,value,size)

    def single_step(self):
        text,size,_,_=self.program.code[self.pc];text=text.removesuffix("  #");next_pc=self.pc+size
        if match:=re.fullmatch(r"call (-?\d+)",text):
            target=next_pc+int(match[1])
            if target in {lo for lo,_ in GAIN_REGIONS.values()}:
                self.gain_calls.append((target,self.value("r0"),self.snapshot()))
            if target==PRODUCER[0] and self.value("sp")<=self.value("r0")<STACK:
                destination=self.value("r0")
                if destination+44>STACK:raise ValueError("generated local section crosses live stack")
                request=(self.value("r1"),self.value("r2"),self.value("r3"),self.read(self.value("sp"),4))
                self.production_calls.append(("local",destination,request,self.snapshot()))
                self.math_calls.append(("generate",destination));self.visited.add(self.pc)
                self.returns.append(next_pc);self.pc=target;return True
        if self.pc==0x02028A9E and text=="call r1" and self.value("r1")==NOTIFICATION:
            self.pending_notifications.append((next_pc,signed(self.value("r0")),self.snapshot()))
            self.visited.add(self.pc);self.returns.append(next_pc);self.pc=NOTIFICATION;return True
        if self.pc==0x0201AA06 and self.pending_notifications:
            resume,value,before=self.pending_notifications.pop()
            if not self.returns or self.returns[-1]!=resume:raise ValueError("unbalanced real notification")
            self.real_notifications.append((NOTIFICATION,value,before,self.snapshot()))
        self.visited.add(self.pc)
        if text=="[--sp] = {rets, r9, r8, r6-r4}":
            self.frames.append(({f"r{i}":self.value(f"r{i}") for i in (4,5,6,8,9)},self.value("sp")))
            self.set("sp",self.value("sp")-24)
        elif text=="{pc, r9, r8, r6-r4} = [sp++]":
            saved,sp=self.frames.pop()
            if self.value("sp")!=sp-24:raise ValueError("unbalanced gain mixer frame")
            self.regs.update(saved,sp=sp)
            if not self.returns:return False
            next_pc=self.returns.pop()
        elif match:=re.fullmatch(r"(r\d+_r\d+) >>= (\d+)",text):
            self.set_pair(match[1],self.pair(match[1])>>(int(match[2])&63))
        elif match:=re.fullmatch(r"\[(r\d+\+-?\d+)\] \+= (-?\d+)",text):
            address=self.address(match[1]);self.write(address,self.read(address,4)+int(match[2]),4)
        else:return super().single_step()
        self.pc=next_pc;return True

    def run(self):
        result=DspAudioPathMachine.run(self)
        if self.pending_notifications:raise ValueError("unfinished real notification")
        result.update(real_notifications=self.real_notifications,notification_calls=self.notification_calls,gain_calls=self.gain_calls)
        return result
