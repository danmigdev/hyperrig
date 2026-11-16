"""Execute the original capture warm-up, reset fallback and numerical callees."""
from __future__ import annotations
import re
from capture_processing_machine import (CaptureProcessingProgram,CaptureProcessingMachine,
    ROOT,CONTEXT,ARENA,ARENA_BYTES,SCRATCH,SCRATCH_BYTES,image_offset)
from pi32v2isa import codec,table

WARMUP,RESET=0x01C12F20,0x01C12878
REGIONS={"warmup":(WARMUP,0x01C13072)}
RESET_REGION=(RESET,0x01C1296C)
ZERO_PAGE_BYTES,WRAP,WRAP_BYTES=4096,0xFFFFFFF0,16


class CaptureWarmupProgram(CaptureProcessingProgram):
    def __init__(self):
        super().__init__()
        self.pre_warmup_code=set(self.code);self.warmup_regions={}
        raw=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes();instructions=table.load()
        for name,(start,end) in (REGIONS|{"reset":RESET_REGION}).items():
            self.warmup_regions[name]=raw[image_offset(start):image_offset(end)]
            pc=start
            while pc<end:
                decoded=codec.decode(instructions,raw,image_offset(pc))
                if decoded is None:raise ValueError(f"undecoded warm-up instruction {pc:#x}")
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(("then","else")):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError("warm-up instruction crosses function boundary")
                self.code[pc]=codec.format(instruction,fields),size,*counts
                pc+=size
        for pc in set(self.code)-self.pre_warmup_code:
            text,size,_,_=self.code[pc]
            if text.endswith("  #"):
                following,bsize,_,_=self.code[pc+size]
                if not re.match(r"r\d+ =",text) or bsize!=2 or "[" not in following:
                    raise ValueError("unreviewed warm-up packet")
                self.parallel_seconds.add(pc+size)
        self.warmup_code={pc for pc in self.code if WARMUP<=pc<REGIONS["warmup"][1]}

    def execute(self,memory,output=0,*,kernel=None):
        if tuple(map(len,memory))!=(228,ARENA_BYTES,SCRATCH_BYTES,ZERO_PAGE_BYTES,WRAP_BYTES) or not 0<=output<=0xFFFFFFFF:
            raise ValueError("outside warm-up verifier API domain")
        return CaptureWarmupMachine(self,memory,output,kernel).run()


class CaptureWarmupMachine(CaptureProcessingMachine):
    def __init__(self,program,memory,output,kernel):
        super().__init__(program,memory[:3],"process",(0,0,0),kernel)
        for base,data in zip((0,WRAP),memory[3:]):
            self.memory.update({base+i:byte for i,byte in enumerate(data)})
        self.pc=WARMUP;self.regs.update(r0=CONTEXT,r1=output);self.reset_entries=0

    def snapshot(self):
        return super().snapshot()+tuple(bytes(self.memory[base+i] for i in range(n))
            for base,n in ((0,ZERO_PAGE_BYTES),(WRAP,WRAP_BYTES)))

    def single_step(self):
        text,size,_,_=self.program.code[self.pc]
        if m:=re.fullmatch(r"call (-?\d+)",text):
            if self.pc+size+int(m[1])==RESET:
                if self.value("r0")!=CONTEXT:raise ValueError("unreviewed reset context")
                self.visited.add(self.pc);self.returns.append(self.pc+size);self.pc=RESET
                self.reset_entries+=1;return True
        return super().single_step()

    def run(self):
        result=super().run()
        result.update(result=self.value("r0"),reset_entries=self.reset_entries)
        return result
