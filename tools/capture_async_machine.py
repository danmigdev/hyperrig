"""Original asynchronous capture bodies with explicit scheduled platform events."""
from __future__ import annotations
import re
from audio_task_machine import (AudioTaskProgram,AudioTaskMachine,MAPPED,ROOT,STACK,
    TASK,STATIC,image_offset,DotMachine,signed)
from pi32v2isa import codec,table

DSP,BANK,HISTORY,RESULT,CHECK=0x01C2BFF0,0x01C2B4E0,0x01C2A8E0,0x01C2BEE8,0x01C2C120
MMIO,TIMER,ENGINE,DESCRIPTOR=0x01EE0400,0x00010704,0x01C3449C,0x01C339E0
READ,WRITE,SYNC,CLI,STI=range(5)
WORKER_STACK=0x30003000
POLL,HANDSHAKE,WORKER_END=0x01C04666,0x01C04688,0x01C04774
REGIONS={"run":(0x01C04CDA,0x01C05118),"worker":(0x01C04588,WORKER_END),
         "submit":(0x01C12556,0x01C12608),"command_noop":(0x01C13080,0x01C13082)}
REUSED={"wait":(0x01C1245C,0x01C124A8),"clear0":(0x01C13082,0x01C13084),
        "clear1":(0x01C13084,0x01C13086),"clear2":(0x01C13086,0x01C13088),
        "clear3":(0x01C1308C,0x01C1308E),"dot_i16":(0x01C12608,0x01C126F4)}
CALLBACK=0x01C02DBC
# These four decoded instructions dominate the 4,000,001-poll fallback test.
# Dispatch them without a regular-expression search; each original instruction
# still executes, reads the platform, updates registers and counts separately.
POLL_WORDS={0x01C04D98:('r0 = [r13+8]',4),0x01C04D9C:('if (r0 == 0) goto 8',2),
    0x01C04D9E:('r1 = r1 + 1',2),0x01C04DA0:('if (r1 <= r14) goto -12',4)}


class CaptureAsyncProgram(AudioTaskProgram):
    def __init__(self):
        super().__init__();self.pre_async_code=set(self.code);self.async_regions={}
        raw=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            self.async_regions[name]=raw[image_offset(start):image_offset(end)];pc=start
            while pc<end:
                instruction,fields,size=codec.decode(instructions,raw,image_offset(pc));counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]];counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError('async instruction crosses function boundary')
                decoded=(codec.format(instruction,fields),size,*counts)
                if pc in self.code and self.code[pc]!=decoded:raise ValueError('inconsistent reused decode')
                self.code[pc]=decoded;pc+=size
        self.async_code={pc for pc in self.code if any(start<=pc<end for start,end in (REGIONS|REUSED).values())}
        for pc in self.async_code:
            text,size,_,_=self.code[pc]
            if text.endswith('  #'):
                following,second,_,_=self.code[pc+size]
                if second!=2 or '[' not in following:raise ValueError('unreviewed async parallel packet')
                self.parallel_seconds.add(pc+size)
        for pc,expected in POLL_WORDS.items():
            if self.code[pc][:2]!=expected:raise ValueError('fallback poll encoding changed')

    def machine(self,memory,boundary=None,platform=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid async map')
        return CaptureAsyncMachine(self,memory,boundary,platform)

    def execute(self,memory,operation,args=(),boundary=None,platform=None):
        arities={'run':2,'submit':7,'wait':0,'command_noop':5}
        if operation not in arities or len(args)!=arities[operation] or any(not 0<=x<=0xFFFFFFFF for x in args):
            raise ValueError('invalid async operation arguments')
        machine=self.machine(memory,boundary,platform)
        machine.pc=(REGIONS|REUSED)[operation][0]
        for i,value in enumerate(args):
            if i<4:machine.regs[f'r{i}']=value
            else:DotMachine.write(machine,STACK+4*(i-4),value,4)
        return machine.run_call()


class CaptureAsyncMachine(AudioTaskMachine):
    def __init__(self,program,memory,boundary,platform):
        super().__init__(program,memory,boundary)
        self.platform,self.flags,self.stack_top=platform,0,STACK
        self.platform_events=0;self.worker_control=0;self.worker_iterations=0
        self.worker_returned=False;self.worker_loop_active=False;self.worker_idle=0

    def raw_read(self,address,size):return DotMachine.read(self,address,size)
    def event(self,operation,address=0,value=0):
        if self.platform is None:raise ValueError('explicit platform fixture required')
        self.platform_events+=1
        return self.platform(operation,address,value,self)&0xFFFFFFFF

    def read(self,address,size):
        if self.pc in self.program.async_code and (address in (TIMER,MMIO,MMIO+4,MMIO+8,DSP+8,DSP+4) or
                (self.worker_control and address==self.worker_control)):
            if size!=4:raise ValueError('unreviewed volatile width')
            return self.event(READ,address)
        if 0x30000000<=address<0x30004000:
            if not self.value('sp')<=address<=address+size<=self.stack_top+16:raise ValueError('private stack read escaped')
        return DotMachine.read(self,address,size)

    def write(self,address,value,size):
        if address in (MMIO,MMIO+4,MMIO+8):
            if size!=4:raise ValueError('unreviewed MMIO write width')
            self.event(WRITE,address,value&0xFFFFFFFF);return
        if 0x30000000<=address<0x30004000:
            if not self.value('sp')<=address<=address+size<=self.stack_top+16:raise ValueError('private stack write escaped')
            if self.worker_control and address==WORKER_STACK-56:self.worker_idle=value&0xFFFFFFFF
            DotMachine.write(self,address,value,size);return
        super().write(address,value,size)

    def binary(self,a,operator,b,carry=0):
        result=super().binary(a,operator,b,carry)
        if operator in ('+','-'):
            exact=signed(a)+signed(b)+carry if operator=='+' else signed(a)-signed(b)-carry
            self.flags=int(not -(1<<31)<=exact<(1<<31))|self.carry<<1|int(result==0)<<2|(result>>31)<<3
        return result

    def step(self):
        if self.pc in POLL_WORDS:
            pc=self.pc;self.visited.add(pc)
            if pc==0x01C04D98:self.set('r0',self.read(self.value('r13')+8,4));self.pc+=4
            elif pc==0x01C04D9C:self.pc+=10 if self.value('r0')==0 else 2
            elif pc==0x01C04D9E:self.set('r1',self.binary(self.value('r1'),'+',1));self.pc+=2
            else:self.pc+=-8 if self.value('r1')<=self.value('r14') else 4
            return True
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.code or self.pc in self.program.parallel_seconds:raise ValueError('async packet escape')
        if not self.program.code[self.pc][0].endswith('  #'):return self.single_step()
        before,carry,flags=dict(self.regs),self.carry,self.flags;self.written=set()
        if not self.single_step():raise ValueError('parallel control transfer')
        first={key:self.regs[key] for key in self.written};after_carry,after_flags=self.carry,self.flags
        self.regs,self.carry,self.flags,self.written=before,carry,flags,set()
        if not self.single_step():raise ValueError('parallel control transfer')
        self.regs.update(first);self.carry,self.flags=after_carry,after_flags;self.written=set();return True

    def single_step(self):
        text,size,then,otherwise=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        self.visited.add(self.pc)
        if text in ('csync','cli','sti') and self.pc in self.program.async_code:
            self.event({'csync':SYNC,'cli':CLI,'sti':STI}[text])
        elif m:=re.fullmatch(r'sp \+= (-?\d+)',text):
            after=self.value('sp')+int(m[1])
            if not self.stack_top-4096<=after<=self.stack_top:raise ValueError('async stack allocation escaped')
            if after<self.value('sp'):
                for address in range(after,self.value('sp')):self.memory.pop(address,None)
            self.set('sp',after)
        elif m:=re.fullmatch(r'(r\d+) = psr',text):self.set(m[1],self.flags)
        elif m:=re.fullmatch(r'(r\d+) = (s|u)extra\((r\d+), p:(\d+), l:(\d+)\)',text):
            bits=int(m[5]);value=(self.value(m[3])>>int(m[4]))&((1<<bits)-1)
            self.set(m[1],signed(value,bits) if m[2]=='s' else value)
        elif m:=re.fullmatch(r'(r\d+) = ~(r\d+)',text):self.set(m[1],~self.value(m[2]))
        elif m:=re.fullmatch(r'(r\d+) = (r\d+)\.b0 \(s\)',text):self.set(m[1],signed(self.value(m[2])&255,8))
        elif m:=re.fullmatch(r'(r\d+_r\d+) (<<=|>>>=) (\d+)',text):
            value=self.pair(m[1]);shift=int(m[3])&63
            self.set_pair(m[1],value<<shift if m[2]=='<<=' else signed(value,64)>>shift)
        elif m:=re.fullmatch(r'(r\d+) = (r\d+) (\^|&) (r\d+)',text):
            a,b=self.value(m[2]),self.value(m[4]);self.set(m[1],a^b if m[3]=='^' else a&b)
        elif m:=re.fullmatch(r'(r\d+) \|= (\d+)',text):self.set(m[1],self.value(m[1])|int(m[2]))
        elif m:=re.fullmatch(r'(r\d+) = (r\d+) - (0x[0-9a-fA-F]+)',text):
            self.set(m[1],self.binary(self.value(m[2]),'-',int(m[3],16)))
        elif m:=re.fullmatch(r'\[(.+)\] \|= (0x[0-9a-fA-F]+)',text):
            address=self.address(m[1]);self.write(address,self.read(address,4)|int(m[2],16),4)
        elif self.pc in (0x01C045DE,0x01C04616):
            target=self.value('r0' if self.pc==0x01C045DE else 'r1')
            if target!=CALLBACK:raise ValueError('unreviewed worker indirect target')
            args=() if self.pc==0x01C045DE else (self.value('r0'),)
            self.calls.append((target,args,self.state_digest()))
            result=self.boundary(target,args,self) if self.boundary else 0
            for register in ('r0','r1','r2','r3'):self.set(register,0xBAD0C0DE)
            self.set('r0',result)
        else:return super().single_step()
        self.pc=next_pc;return True

    def run_call(self):
        while self.steps<80000000:
            self.steps+=1
            if not self.step():break
        else:raise ValueError('async instruction budget exceeded')
        if self.frames or self.returns or self.else_skips or self.value('sp')!=self.stack_top:raise ValueError('unbalanced async ABI')
        return self.result()

    def result(self):
        return {'value':self.value('r0'),'memory':self.snapshot(),'calls':list(self.calls),
            'visited':set(self.visited),'steps':self.steps,'real_calls':list(self.real_calls),'platform_events':self.platform_events}

    def worker_start(self,control):
        self.pc=REGIONS['worker'][0];self.worker_control=control;self.stack_top=WORKER_STACK
        self.regs['sp']=WORKER_STACK;self.regs['r0']=control

    def worker_state(self):
        phase=3 if self.worker_returned else 2 if self.pc==HANDSHAKE else 1
        return phase,self.worker_idle,self.worker_iterations,self.worker_control

    def worker_resume(self,budget=1,handshake_budget=1):
        if budget<1 or handshake_budget<1:raise ValueError('positive worker budgets required')
        if self.worker_returned:return 1
        target=self.worker_iterations+budget;reads=0
        while self.steps<80000000:
            if self.pc==POLL:
                if self.worker_loop_active:
                    self.worker_iterations+=1;self.worker_loop_active=False
                if self.worker_iterations>=target:return 0
                self.worker_loop_active=True
            if self.pc==HANDSHAKE:
                if reads>=handshake_budget:return 2
                reads+=1
            self.steps+=1
            if not self.step():
                if self.worker_loop_active:self.worker_iterations+=1
                self.worker_returned=True;return 1
        raise ValueError('worker instruction budget exceeded')
