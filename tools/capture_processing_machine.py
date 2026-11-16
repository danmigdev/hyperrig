"""Execute pinned capture orchestration and its actual three-channel kernels."""
from __future__ import annotations
import re
from pathlib import Path
from control_action_machine import ControlActionMachine
from dot_machine import NativeProgram, DotMachine, signed
from pi32v2isa import codec, table

ROOT=Path(__file__).resolve().parents[1]
REGIONS={"rechannel":(0x01C129DC,0x01C12A54),"layer":(0x01C12A54,0x01C12C32),
    "iterate":(0x01C12C32,0x01C12CC2),"head":(0x01C12CC2,0x01C12D34),
    "process":(0x01C12D34,0x01C12F20),"zero":(0x01C1452A,0x01C1453C)}
KERNELS={name:NativeProgram.REGIONS[name] for name in
    ("rechannel3","head3","layer6","layer6_shift","layer15","layer15_shift","layer_generic")}
TABLE_START,TABLE_END=0x01C12BF2,0x01C12BF6
CONTEXT,ARENA,ARENA_BYTES=0x31000000,0x32000000,0x20000
SCRATCH,SCRATCH_BYTES=0x01C33A00,0xB00
ARITIES={"rechannel":3,"layer":8,"iterate":6,"head":3,"process":3,"zero":2}


def image_offset(address):
    return 0x02056780-0x02000120+address-0x01C00000


class CaptureProcessingProgram:
    def __init__(self):
        # Existing loader authenticates the exact original and decoded extraction.
        self.reference=NativeProgram("head3")
        app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions=table.load()
        self.code,self.raw_regions,self.kernel_regions={},{},{}
        for name,(start,end) in (REGIONS|KERNELS).items():
            raw=app[image_offset(start):image_offset(end)]
            (self.raw_regions if name in REGIONS else self.kernel_regions)[name]=raw
            pc=start
            while pc<end:
                if pc==TABLE_START:
                    pc=TABLE_END
                    continue
                decoded=codec.decode(instructions,app,image_offset(pc))
                if decoded is None:raise ValueError(f"undecoded processing instruction {pc:#x}")
                instruction,fields,size=decoded
                counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError("processing instruction crosses region")
                self.code[pc]=codec.format(instruction,fields),size,*counts
                pc+=size
        self.table=app[image_offset(TABLE_START):image_offset(TABLE_END)]
        if self.table!=bytes((2,26,14,20)):raise ValueError("unexpected numerical dispatch table")
        self.parallel_seconds=set()
        for pc,(text,size,_,_) in self.code.items():
            if text.endswith("  #"):
                following,bsize,_,_=self.code[pc+size]
                if not re.match(r"r\d+(?:_r\d+)? =",text) or bsize!=2 or "[" not in following:
                    raise ValueError(f"unreviewed processing packet {pc:#x}")
                self.parallel_seconds.add(pc+size)
        self.new_code={pc for pc in self.code if any(lo<=pc<hi for lo,hi in REGIONS.values())}
        self.kernel_starts={lo for lo,hi in KERNELS.values()}

    def execute(self,memory,operation,*arguments,kernel=None):
        if (operation not in ARITIES or len(arguments)!=ARITIES[operation] or
            tuple(map(len,memory))!=(228,ARENA_BYTES,SCRATCH_BYTES) or
            any(not 0<=v<=0xFFFFFFFF for v in arguments)):
            raise ValueError("outside processing verifier API domain")
        return CaptureProcessingMachine(self,memory,operation,arguments,kernel).run()


class CaptureProcessingMachine(ControlActionMachine):
    def __init__(self,program,memory,operation,arguments,kernel):
        self.program,self.kernel=program,kernel
        self.regs={f"r{i}":0 for i in range(16)}
        self.regs["sp"]=0x30001000
        self.memory={0x30000000+i:0 for i in range(0x1100)}
        for base,data in zip((CONTEXT,ARENA,SCRATCH),memory):
            self.memory.update({base+i:byte for i,byte in enumerate(data)})
        args=list(arguments) if operation=="zero" else [CONTEXT,*arguments]
        for i,value in enumerate(args):
            if i<4:self.regs[f"r{i}"]=value
            else:DotMachine.write(self,self.value("sp")+(i-4)*4,value,4)
        self.pc=REGIONS[operation][0]
        self.carry=self.steps=0
        self.calls,self.frames,self.returns,self.visited,self.writes=[],[],[],set(),[]
        self.else_skips={}

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(n)) for base,n in
            ((CONTEXT,228),(ARENA,ARENA_BYTES),(SCRATCH,SCRATCH_BYTES)))

    def address(self,expression):
        if m:=re.fullmatch(r"\+\+(r\d+)=(r\d+)",expression):
            self.set(m[1],self.value(m[1])+self.value(m[2]))
            return self.value(m[1])
        return super().address(expression)

    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.code or self.pc in self.program.parallel_seconds:
            raise ValueError("processing execution escaped decoded packet boundary")
        text,size,_,_=self.program.code[self.pc]
        if not text.endswith("  #"):return self.single_step()
        pc,before=self.pc,dict(self.regs)
        destinations=re.match(r"(r\d+(?:_r\d+)?) =",text)[1].split("_")
        self.pc=pc+size
        if not self.single_step():raise ValueError("parallel B returned")
        after_b,end=dict(self.regs),self.pc
        self.regs,self.pc=dict(before),pc
        if not self.single_step():raise ValueError("parallel A returned")
        for dest in destinations:after_b[dest]=self.regs[dest]
        self.regs,self.pc=after_b,end
        return True

    def single_step(self):
        self.visited.add(self.pc)
        text,size,_,_=self.program.code[self.pc]
        text=text.removesuffix("  #")
        next_pc=self.pc+size
        if m:=re.fullmatch(r"call (-?\d+)",text):
            target=next_pc+int(m[1])
            if target in self.program.kernel_starts:
                self.calls.append((target,self.value("r0"),self.snapshot()))
                if self.kernel:
                    self.kernel(target,self.value("r0"),self)
                    for reg in ("r0","r1","r2","r3"):self.set(reg,0xBAD0C0DE)
                else:
                    self.returns.append(next_pc)
                    next_pc=target
            elif target in {lo for lo,hi in REGIONS.values()}:
                self.returns.append(next_pc)
                next_pc=target
            else:raise ValueError(f"unreviewed processing callee {target:#x}")
        elif m:=re.fullmatch(r"tbb \[(r\d+)\]",text):
            index=self.value(m[1])
            if self.pc!=TABLE_START-2 or index>=4:raise ValueError("bad processing table index")
            next_pc=TABLE_START+2*self.program.table[index]
        elif m:=re.fullmatch(r"(r\d+) = b\[(.+)\] \(s\)",text):
            self.set(m[1],signed(self.read(self.address(m[2]),1),8))
        elif m:=re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(u\)",text):
            if not self.value(m[3]):raise ValueError("undefined division by zero")
            self.set(m[1],self.value(m[2])//self.value(m[3]))
        elif m:=re.fullmatch(r"(r\d+) = (r\d+) & (r\d+|0x[0-9A-Fa-f]+)",text):
            self.set(m[1],self.value(m[2])&self.value(m[3]))
        elif m:=re.fullmatch(r"(r\d+_r\d+) = (r\d+_r\d+) \+ (r\d+_r\d+)",text):
            self.set_pair(m[1],self.pair(m[2])+self.pair(m[3]))
        elif m:=re.fullmatch(r"d\[(.+)\] = (r\d+_r\d+)",text):
            self.write(self.address(m[1]),self.pair(m[2]),8)
        elif m:=re.fullmatch(r"\[(.+)\] = (0x[0-9A-Fa-f]+)",text):
            self.write(self.address(m[1]),int(m[2],16),4)
        elif m:=re.fullmatch(r"\[(.+)\] \+= (0x[0-9A-Fa-f]+)",text):
            address=self.address(m[1]);self.write(address,self.read(address,4)+int(m[2],16),4)
        elif m:=re.fullmatch(r"(r\d+_r\d+) \+= h\[(r\d+) \+\+= 2\]\*(r\d+) \(s\)",text):
            self.set_pair(m[1],self.pair(m[1])+signed(self.read(self.value(m[2]),2),16)*signed(self.value(m[3])))
            self.set(m[2],self.value(m[2])+2)
        elif m:=re.fullmatch(r"(r\d+_r\d+) >>>= (\d+)",text):
            self.set_pair(m[1],signed(self.pair(m[1]),64)>>int(m[2]))
        elif m:=re.fullmatch(r"(r\d+) >>= (r\d+)",text):
            self.set(m[1],self.value(m[1])>>(self.value(m[2])&31))
        elif text in ("rep 4 r2 {","rep 8 r1 {"):
            register="r2" if text=="rep 4 r2 {" else "r1"
            count=self.value(register)
            if not 1<=count<=255:raise ValueError("unreviewed REP count")
            body,end=next_pc,next_pc+(4 if text=="rep 4 r2 {" else 8)
            while self.value(register):
                self.pc=body
                while self.pc<end:
                    if not self.step():raise ValueError("REP body returned")
                    self.steps+=1
                if self.pc!=end:raise ValueError("REP body escaped")
                self.set(register,self.value(register)-1)
            next_pc=end
        elif text=="r1_r0 += h[r6 ++= 2]*[r4 ++= 4] (s)":
            self.set_pair("r1_r0",self.pair("r1_r0")+signed(self.read(self.value("r6"),2),16)*signed(self.read(self.value("r4"),4)))
            self.set("r6",self.value("r6")+2);self.set("r4",self.value("r4")+4)
        else:return super().single_step()
        self.pc=next_pc
        return True

    def run(self):
        while self.steps<2000000:
            self.steps+=1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp")!=0x30001000:
                    raise ValueError("unbalanced processing ABI")
                return {"memory":self.snapshot(),"calls":self.calls,"visited":self.visited,"steps":self.steps}
        raise ValueError("processing instruction budget exceeded")
