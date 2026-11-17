"""Execute the six original resampling bodies with real decoded arithmetic."""
from __future__ import annotations
import hashlib
import re
import struct
import sys
from dot_machine import DotMachine, ROOT, MASK32, MASK64, signed
from pi32v2isa import codec, table

REGIONS={"up":(0x01c07986,0x01c07a4c),"down":(0x01c08a76,0x01c08b34),
    "up5":(0x01c1ae86,0x01c1b056),"down5":(0x01c1b056,0x01c1b23a),
    "up4":(0x01c1b23a,0x01c1b3d4),"down4":(0x01c1b3d4,0x01c1b582)}
STATIC={"coefficient_pointers":(0x0203b768,0x0203b774),
    "tap_counts":(0x0203b774,0x0203b780),"five_taps":(0x0203b780,0x0203b794),
    "three_taps":(0x0203b794,0x0203b7a0),"four_taps":(0x0203b7a0,0x0203b7b0)}
ORIGINAL_SHA="2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
MINI_SHA="d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
STACK=0x30001000

def offset(address):
    return address-0x02000120 if address>=0x02000000 else 0x02056780-0x02000120+address-0x01c00000

class EffectResamplingProgram:
    def __init__(self):
        original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
        if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:raise ValueError('wrong original image')
        sys.path.insert(0,str(ROOT))
        from hyperrig.jieli import unpack_app
        self.app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        if unpack_app(original)[2]['app.bin']!=self.app:raise ValueError('decoded image differs')
        self.code={};self.regions={};self.data={};instructions=table.load()
        for name,(start,end) in REGIONS.items():
            raw=self.regions[name]=self.app[offset(start):offset(end)];cursor=0
            while cursor<len(raw):
                decoded=codec.decode(instructions,raw,cursor)
                if decoded is None:raise ValueError(f'undecoded resampling instruction {start+cursor:#x}')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if cursor+size>len(raw):raise ValueError('instruction crosses function boundary')
                self.code[start+cursor]=codec.format(instruction,fields),size,*counts;cursor+=size
        for name,(start,end) in STATIC.items():self.data[name]=self.app[offset(start):offset(end)]
        self.parallel_seconds=set()
        for pc,(text,size,_,_) in self.code.items():
            if text.endswith('  #'):
                second,n,_,_=self.code[pc+size]
                if not re.match(r'r\d+ = ',text) or n!=2 or '[' not in second:
                    raise ValueError(f'unreviewed resampling packet {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,name,source,output,count,selector=0):
        if name not in REGIONS or any(not 0<=v<=MASK32 for v in (source,output,count,selector)):
            raise ValueError('invalid original ABI')
        wrapper=name in ('up','down')
        if not(wrapper and count&3 and count>>31):
            if not count or count>>31 or (not wrapper and count&3):raise ValueError('nonterminating count domain')
            if wrapper and count&3 and selector>2:raise ValueError('unmapped coefficient selector')
        m=EffectResamplingMachine(self,memory)
        m.pc=REGIONS[name][0];m.regs.update(r0=source,r1=output,r2=count,r3=selector)
        while m.steps<2000000:
            m.steps+=1
            if not m.step():break
        else:raise ValueError('resampling instruction budget exhausted')
        if m.frames or m.returns or m.value('sp')!=STACK:raise ValueError('unbalanced original ABI')
        return {'memory':m.snapshot(),'visited':m.visited,'steps':m.steps,'calls':m.calls,
            'reads':m.reads,'writes':m.writes}

class EffectResamplingMachine(DotMachine):
    def __init__(self,program,memory):
        self.program=program;self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={};self.spans=[]
        for start,raw in memory:
            if any(start<b+n and b<start+len(raw) for b,n in self.spans):raise ValueError('overlapping input mappings')
            self.spans.append((start,len(raw)));self.memory.update({start+i:v for i,v in enumerate(raw)})
        for name,(start,end) in STATIC.items():self.memory.update({start+i:v for i,v in enumerate(program.data[name])})
        self.pc=self.carry=self.steps=0;self.frames=[];self.returns=[];self.calls=[]
        self.visited=set();self.reads=[];self.writes=[]
    def snapshot(self):return tuple((base,bytes(self.memory[base+i] for i in range(n))) for base,n in self.spans)
    def read(self,address,size):
        if 0x30000000<=address<STACK and not self.value('sp')<=address<=address+size<=STACK:
            raise ValueError('read escaped allocated stack')
        value=super().read(address,size);self.reads.append((address,size));return value
    def write(self,address,value,size):
        if 0x30000000<=address<STACK:
            if not self.value('sp')<=address<=address+size<=STACK:raise ValueError('write escaped allocated stack')
        elif not any(base<=address<=address+size<=base+n for base,n in self.spans):
            raise ValueError(f'write escaped mapped RAM {address:#x}')
        self.writes.append((address,value&((1<<(size*8))-1),size));super().write(address,value,size)
    def address(self,expression):
        if m:=re.fullmatch(r'(r\d+)\+\+=(-?\d+)',expression):
            old=self.value(m[1]);self.set(m[1],old+int(m[2]));return old
        if m:=re.fullmatch(r'(r\d+)\+(r\d+)',expression):return (self.value(m[1])+self.value(m[2]))&MASK32
        return super().address(expression)
    def step(self):
        text,size,_,_=self.program.code[self.pc]
        if not text.endswith('  #'):return self.single_step()
        before=dict(self.regs);carry=self.carry
        self.single_step();first=dict(self.regs);first_carry=self.carry
        self.regs=dict(before);self.carry=carry;self.steps+=1
        result=self.single_step()
        for key,value in first.items():
            if value!=before[key]:
                if self.regs[key]!=before[key]:raise ValueError('parallel destination collision')
                self.regs[key]=value
        self.carry=first_carry
        return result
    def single_step(self):
        self.visited.add(self.pc);text,size,_,_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if text=='[--sp] = {rets, r15-r4}':
            self.frames.append(({f'r{i}':self.value(f'r{i}') for i in range(4,16)},self.value('sp')))
            self.set('sp',self.value('sp')-52)
        elif text=='{pc, r15-r4} = [sp++]':
            saved,sp=self.frames.pop()
            if self.value('sp')!=sp-52:raise ValueError('stack local imbalance')
            self.regs.update(saved,sp=sp)
            if not self.returns:return False
            next_pc=self.returns.pop()
        elif m:=re.fullmatch(r'call (-?\d+)',text):
            target=next_pc+int(m[1])
            if target not in self.program.code:raise ValueError('unrecovered resampling callee')
            self.calls.append((target,tuple(self.value(f'r{i}') for i in range(4))))
            self.returns.append(next_pc);next_pc=target
        elif m:=re.fullmatch(r'if \(\((r\d+) & (0x[0-9a-fA-F]+)\) (==|!=) 0\) goto (-?\d+)',text):
            if bool(self.value(m[1])&int(m[2],16))==(m[3]=='!='):next_pc+=int(m[4])
        elif m:=re.fullmatch(r'(r\d+_r\d+) = (r\d+) \* (r\d+) \(s\)',text):
            self.set_pair(m[1],signed(self.value(m[2]))*signed(self.value(m[3])))
        elif m:=re.fullmatch(r'(r\d+_r\d+) = (r\d+_r\d+)',text):
            self.set_pair(m[1],self.pair(m[2]))
        elif m:=re.fullmatch(r'(r\d+_r\d+) (<<=|>>>=) (\d+)',text):
            value=self.pair(m[1]);amount=int(m[3])
            self.set_pair(m[1],value<<amount if m[2]=='<<=' else signed(value,64)>>amount)
        elif m:=re.fullmatch(r'(r\d+) <= insert\((r\d+), p:(\d+), l:(\d+)\)',text):
            pos,length=int(m[3]),int(m[4]);mask=((1<<length)-1)<<pos
            self.set(m[1],(self.value(m[1])&~mask)|((self.value(m[2])<<pos)&mask))
        else:return super().step()
        self.pc=next_pc;return True
