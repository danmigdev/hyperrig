"""Execute original integer IR processing with explicit synthetic MMIO boundaries."""
from __future__ import annotations
import re
from ir_convolution_machine import (IrConvolutionProgram,IrConvolutionMachine,ROOT,OBJECT,OBJECT_BYTES,
    WORK,COPY,WORK_BYTES,COPY_BYTES,CAPACITY,HEAP,REGIONS as CONSTRUCTION_REGIONS,region_bytes,STACK,FLOAT,DotMachine,signed)
from pi32v2isa import codec,table

REGIONS={
    'crossfade':(0x01C11FAA,0x01C12064),'process':(0x01C12064,0x01C123FA),
    'wait':(0x01C1245C,0x01C124A8),'start':(0x01C124A8,0x01C12556),
    'input':(0x01C145FE,0x01C1477E),'fft64':(0x01C1477E,0x01C1508C),
    'merge':(0x01C1508C,0x01C15148),'forward':(0x01C15148,0x01C1533E),
    'multiply':(0x01C1533E,0x01C154A4),'inverse':(0x01C154A4,0x01C15A42),
    'output':(0x01C15A42,0x01C15BC8),'mix':(0x01C15BC8,0x01C15C8C),
    'hardware_input':(0x01C15C8C,0x01C15CF2),'hardware_forward':(0x01C15CF2,0x01C15D3A),
    'hardware_scale':(0x01C15D3A,0x01C15D7E),'hardware_output':(0x01C15D7E,0x01C15DEC)}
ARITIES={'crossfade':7,'process':4,'wait':0,'start':4,'input':4,'fft64':2,'merge':2,
    'forward':4,'multiply':4,'inverse':4,'output':4,'mix':4,'hardware_input':2,
    'hardware_forward':3,'hardware_scale':2,'hardware_output':3,'construct':3}
GLOBALS,DESCRIPTOR,AUDIO=0x01C34490,0x01C339D0,0x37000000
MMIO,DESCRIPTORS,INDICES=0x01EE0400,0x0203BE50,0x0203BE70
READ,WRITE,SYNC=0,1,2
EXTRA=((GLOBALS,16),(DESCRIPTOR,16),(AUDIO,512))

class IrProcessingProgram(IrConvolutionProgram):
    def __init__(self):
        super().__init__();self.pre_processing_code=set(self.code);self.processing_regions={}
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();instructions=table.load()
        self.accelerator_tables=region_bytes(app,DESCRIPTORS,INDICES+32)
        for name,(start,end) in REGIONS.items():
            raw=region_bytes(app,start,end);self.processing_regions[name]=raw;offset=0
            while offset<len(raw):
                decoded=codec.decode(instructions,raw,offset)
                if decoded is None:raise ValueError(f'undecoded IR processing instruction at {start+offset:#x}')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]];counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if offset+size>len(raw):raise ValueError('IR processing instruction crosses function boundary')
                self.code[start+offset]=codec.format(instruction,fields),size,*counts;offset+=size
        for pc in set(self.code)-self.pre_processing_code:
            text,size,_,_=self.code[pc]
            if text.endswith('  #'):
                following,bsize,_,_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|\+=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed IR processing packet at {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,operation,*args,mmio=None):
        if (len(memory)!=30 or tuple(len(x) for i,x in enumerate(memory) if i!=2)!=
                (272,1860,4,2,20,48,16,256,40,1490,1490,16,12,4,4,CAPACITY,24,4,
                 8,4,384,64,OBJECT_BYTES,WORK_BYTES,COPY_BYTES,12,16,16,512) or not 0<=memory[2]<=255 or
                operation not in ARITIES or len(args)!=ARITIES[operation] or any(not 0<=x<=0xFFFFFFFF for x in args)):
            raise ValueError('outside IR processing call domain')
        def word(index,offset=0):return int.from_bytes(memory[index][offset:offset+4],'little')
        def span(address,size):
            if address&3:raise ValueError('unaligned numerical input')
            for base,capacity,index in ((OBJECT,OBJECT_BYTES,23),(WORK,WORK_BYTES,24),(COPY,COPY_BYTES,25),(AUDIO,512,29)):
                if base<=address and address+size<=base+capacity:return index,address-base
            raise ValueError('unmapped numerical input')
        def perm(address,count):
            index,offset=span(address,1536)
            for i in range(count):
                expected=((((i*8)&48)|((i>>1)&12)|((i>>5)&3))<<3)|((i*512)&512)
                if word(index,offset+1024+i*4)!=expected:raise ValueError('noncanonical runtime permutation')
        if operation=='construct':
            if (args[0]>4096 or args[1] not in (0,CONSTRUCTION_REGIONS['produce'][0],CONSTRUCTION_REGIONS['copy'][0]) or
                    args[2] not in (0,OBJECT) or word(17,4)>4076 or word(17,4) and word(17)!=HEAP or
                    word(26)>4096 or word(26,4)>word(26)):
                raise ValueError('outside constructor domain')
        elif operation=='process':
            if args[0] not in (0,OBJECT):raise ValueError('unmapped runtime object')
            if args[0] and args[1]==128 and word(23):
                p=word(23,4);h=2616+p*2064
                expected=(OBJECT+2616,OBJECT+2616+p*1032,OBJECT+552,OBJECT+h,OBJECT+h+1024,
                          OBJECT+h+1536,OBJECT+h+2048,OBJECT+h+3080,OBJECT+h+4104)
                if (not 1<=p<=32 or word(23,8)>=p or word(23,12)>1 or word(23,16)>48 or
                        tuple(word(23,i) for i in range(20,56,4))!=expected):raise ValueError('incoherent runtime object')
                perm(OBJECT+h,128)
        elif operation=='input':
            for address in args[:3]:span(address,512)
            perm(args[3],32)
        elif operation=='fft64':span(args[0],512);span(args[1]&~1,480)
        elif operation=='merge':span(args[0],1024);span(args[1],512)
        elif operation in ('forward','hardware_forward'):
            p=args[-1]
            if not 1<=p<=32:raise ValueError('invalid partition count')
            span(args[0],1024 if operation=='forward' else 1032);span(args[1],128*p*8+8)
            if operation=='forward':span(args[2],1032)
        elif operation=='multiply':
            p,current=args[2]&65535,args[2]>>16
            if not 1<=p<=32 or current>=p:raise ValueError('invalid convolution ring')
            span(args[0],p*1032+8);span(args[1],p*1032+8);span(args[3],2064)
        elif operation in ('inverse','hardware_scale'):
            if args[-1]>63:raise ValueError('invalid accumulator shift')
            span(args[0],2064)
            if operation=='inverse':perm(args[1],128);span(args[2],1032)
        elif operation in ('output','hardware_output'):
            if not -31<=signed(args[-1])<=30:raise ValueError('invalid output shift')
            span(args[0],1024 if operation=='output' else 512);span(args[1],512)
            if operation=='output':span(args[2],512)
        elif operation in ('mix','crossfade'):
            for address in args[:3]:
                if address or operation=='crossfade':span(address,512)
        elif operation=='hardware_input':span(args[0],1024);span(args[1],512)
        return IrProcessingMachine(self,memory,operation,args,mmio).run()

class IrProcessingMachine(IrConvolutionMachine):
    def __init__(self,program,memory,operation,args,mmio):
        self.flags=0;self._snapshot_cache=None;self.mmio=mmio;self.mmio_events=0;self.entries={}
        super().__init__(program,memory[:27],operation if operation=='construct' else 'size',args if operation=='construct' else (0,),None)
        for (base,_),data in zip(EXTRA,memory[27:]):self.memory.update({base+i:value for i,value in enumerate(data)})
        self.memory.update({DESCRIPTORS+i:value for i,value in enumerate(program.accelerator_tables)})
        if operation!='construct':
            self.pc=REGIONS[operation][0]
            if operation=='process':args=(args[0],AUDIO,args[1],args[2],args[3])
            for i,value in enumerate(args):
                if i<4:self.set(f'r{i}',value)
                else:DotMachine.write(self,STACK+(i-4)*4,value,4)
        if operation=='process' and args[0] and args[2]==128 and self.read(args[0],4):
            self.object_limit=7248+self.read(args[0]+4,4)*2064
        self._snapshot_cache=None

    def snapshot(self):
        if self._snapshot_cache is None:
            self._snapshot_cache=super().snapshot()+tuple(bytes(self.memory[base+i] for i in range(size)) for base,size in EXTRA)
        return self._snapshot_cache

    def io(self,operation,address,value):
        if self.mmio is None:raise ValueError('MMIO reached without an explicit synthetic script')
        self.mmio_events+=1
        return self.mmio(operation,address,value,self)

    def read(self,address,size):
        if address in (MMIO,MMIO+4):
            if size!=4:raise ValueError('unreviewed MMIO read width')
            return self.io(READ,address,0)
        return super().read(address,size)

    def write(self,address,value,size):
        if address in (MMIO,MMIO+4):
            if size!=4:raise ValueError('unreviewed MMIO write width')
            self.io(WRITE,address,value&0xFFFFFFFF);return
        if DESCRIPTORS<=address<INDICES+32:raise ValueError('immutable accelerator table write')
        if not 0x30000000<=address<0x30002000:self._snapshot_cache=None
        super().write(address,value,size)

    def binary(self,a,operator,b,carry=0):
        result=super().binary(a,operator,b,carry)
        if operator in ('+','-'):
            exact=signed(a)+signed(b)+carry if operator=='+' else signed(a)-signed(b)-carry
            self.flags=(int(not -(1<<31)<=exact<(1<<31)) | self.carry<<1 | int(result==0)<<2 | (result>>31)<<3)
        return result

    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.code or self.pc in self.program.parallel_seconds:
            raise ValueError('IR processing escaped a decoded instruction packet')
        if self.pc in {bounds[0] for bounds in REGIONS.values()}:
            self.entries[self.pc]=self.entries.get(self.pc,0)+1
        if not self.program.code[self.pc][0].endswith('  #'):return self.single_step()
        before,carry,flags=dict(self.regs),self.carry,self.flags;self.written=set()
        if not self.single_step():raise ValueError('unexpected parallel control transfer')
        first={key:self.regs[key] for key in self.written};after_carry,after_flags=self.carry,self.flags
        self.regs,self.carry,self.flags,self.written=before,carry,flags,set()
        if not self.single_step():raise ValueError('unexpected parallel control transfer')
        self.regs.update(first);self.carry,self.flags=after_carry,after_flags;self.written=None;return True

    def single_step(self):
        self.visited.add(self.pc);text,size,_,_=self.program.code[self.pc]
        text=text.removesuffix('  #');next_pc=self.pc+size
        if text=='csync':self.io(SYNC,0,0)
        elif m:=re.fullmatch(r'(r\d+) = psr',text):self.set(m[1],self.flags)
        elif m:=re.fullmatch(r'(r\d+) = ftou\((r\d+)\) \(trunc\)',text):
            result,_=FLOAT.convert('ftou','trunc')({0:self.value(m[2])},0,{'s':0,'r':1});self.set(m[1],result[1])
        elif m:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(s\)',text):
            result,flags=FLOAT.divide(False,True)({0:self.value(m[2]),1:self.value(m[3])},self.flags,{'s':0,'t':1,'r':2})
            self.set(m[1],result[2]);self.flags=flags
        elif m:=re.fullmatch(r'(r\d+) = (smin|smax)\((r\d+), (r\d+)\)',text):
            self.set(m[1],(min if m[2]=='smin' else max)(signed(self.value(m[3])),signed(self.value(m[4]))))
        elif m:=re.fullmatch(r'(r\d+) = ~(r\d+)',text):self.set(m[1],~self.value(m[2]))
        elif m:=re.fullmatch(r'(r\d+) = (r\d+)\.b0 \(s\)',text):self.set(m[1],signed(self.value(m[2])&255,8))
        elif m:=re.fullmatch(r'(r\d+_r\d+) (-=|=) (r\d+) \* (r\d+) \(s\)',text):
            product=signed(self.value(m[3]))*signed(self.value(m[4]))
            self.set_pair(m[1],self.pair(m[1])-product if m[2]=='-=' else product)
        elif m:=re.fullmatch(r'(r\d+_r\d+) (>>>=|>>=) (r\d+|\d+)',text):
            value=self.pair(m[1]);shift=self.value(m[3])&63
            self.set_pair(m[1],(signed(value,64) if m[2]=='>>>=' else value)>>shift)
        elif m:=re.fullmatch(r'(r\d+) = (r\d+) (\^|&|\|) (~?r\d+)',text):
            a=self.value(m[2]);b=self.value(m[4].removeprefix('~'))
            if m[4].startswith('~'):b^=0xFFFFFFFF
            self.set(m[1],{'^':a^b,'&':a&b,'|':a|b}[m[3]])
        elif m:=re.fullmatch(r'(r\d+) = (r\d+) <> (\d+)',text):
            value=self.value(m[2]);shift=int(m[3])&31;self.set(m[1],value>>shift | value<<((32-shift)&31))
        elif m:=re.fullmatch(r'\[(.+)\] (\|=|=) (0x[0-9a-fA-F]+)',text):
            address=self.address(m[1]);value=int(m[3],16)
            if m[2]=='|=':value|=self.read(address,4)
            self.write(address,value,4)
        elif m:=re.fullmatch(r'if \(\((r\d+) & (r\d+|\d+)\) (==|!=) 0\) goto (-?\d+)',text):
            if bool(self.value(m[1])&self.value(m[2]))==(m[3]=='!='):next_pc+=int(m[4])
        elif m:=re.fullmatch(r'rep (14|24) (r\d+) \{',text):
            if not 1<=self.value(m[2])<=129:raise ValueError('outside reviewed positive REP count')
            body,end=next_pc,next_pc+int(m[1])
            while self.value(m[2]):
                self.pc=body
                while self.pc<end:
                    self.steps+=1
                    if not self.step():raise ValueError('REP body returned')
                if self.pc!=end:raise ValueError('REP body escaped')
                self.set(m[2],self.value(m[2])-1)
            next_pc=end
        else:return super().single_step()
        self.pc=next_pc;return True

    def run(self):
        result=super().run();result.update(mmio_events=self.mmio_events,entries=self.entries)
        return result
