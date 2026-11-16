"""Execute complete original IR convolution construction with real numerical bodies."""
from __future__ import annotations
import re
from ir_installation_machine import (IrInstallationProgram, IrInstallationMachine, ROOT, DSP, HEAP,
    CAPACITY, FLOAT, BRANCH, region_bytes, STACK)
from pi32v2isa import codec, table
from dot_machine import DotMachine, signed

REGIONS = {
    'size':(0x01C123FA,0x01C12414), 'reset':(0x01C12414,0x01C12446),
    'prepare':(0x0202962A,0x02029728), 'sample':(0x020313DC,0x02031404),
    'resample':(0x02031404,0x02031542), 'produce':(0x02031542,0x020315B8),
    'copy':(0x020315B8,0x020315C8), 'cosine':(0x020315C8,0x02031626),
    'sine':(0x02031626,0x0203167A), 'phase':(0x0203167A,0x020316F4),
    'fft128':(0x020316F4,0x020317C8), 'real256':(0x020317C8,0x0203187C),
    'q31':(0x0203187C,0x020318A8), 'construct':(0x020318A8,0x02031BF8),
}
REUSED = {'window_cosine':(0x02028646,0x02028676)}
EFFECTS, STATUS, FLAGS, TAPS = 0x01C2C220,0x01C343D8,0x01C1FA14,0x0203BE2C
OBJECT, OBJECT_BYTES = 0x33000000,73296
WORK, WORK_BYTES, COPY, COPY_BYTES, PARAMETERS = 0x34000000,16384,0x35000000,16384,0x36000000
TWIDDLES, PERMUTATION, REAL_TWIDDLES = WORK+0x400,WORK+0x600,WORK+0x700
OUTPUT, SCRATCH = WORK+0xC00,WORK+0x1400
ALLOCATE, FREE = 0x0F000100,0x0F000104
ARITIES = {'size':1,'reset':1,'prepare':2,'sample':2,'resample':3,'produce':2,'copy':2,
           'cosine':1,'sine':1,'phase':2,'fft128':0,'real256':0,'q31':1,'construct':3}
MAPPED = ((DSP+52,8),(FLAGS,4),(None,384),(STATUS,64),(OBJECT,OBJECT_BYTES),
          (WORK,WORK_BYTES),(COPY,COPY_BYTES),(PARAMETERS,12))

def effect_address(index):
    effect,offset=divmod(index,24)
    return EFFECTS+480*effect+(76+offset if offset<16 else 288+offset-16)

class IrConvolutionProgram(IrInstallationProgram):
    def __init__(self):
        super().__init__()
        self.pre_convolution_code=set(self.code)
        self.convolution_regions,self.reused_regions={},{}
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.taps=region_bytes(app,TAPS,TAPS+36)
        instructions=table.load()
        for regions,destination in ((REGIONS,self.convolution_regions),(REUSED,self.reused_regions)):
            for name,(start,end) in regions.items():
                raw=region_bytes(app,start,end);destination[name]=raw
                offset=0
                while offset<len(raw):
                    decoded=codec.decode(instructions,raw,offset)
                    if decoded is None:raise ValueError(f'undecoded convolution instruction at {start+offset:#x}')
                    instruction,fields,size=decoded;counts=[0,0]
                    if instruction.block:
                        for i,kind in enumerate(('then','else')):
                            spec=instruction.fields[instruction.block[kind]]
                            counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                    if offset+size>len(raw):raise ValueError('convolution instruction crosses its function boundary')
                    self.code[start+offset]=codec.format(instruction,fields),size,*counts
                    offset+=size
        for pc in set(self.code)-self.pre_convolution_code:
            text,size,_,_=self.code[pc]
            if text.endswith('  #'):
                following,bsize,_,_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|\+=|\^=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed convolution parallel packet at {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,operation,*args,boundary=None):
        if (operation not in ARITIES or len(args)!=ARITIES[operation] or len(memory)!=27
                or tuple(len(x) for i,x in enumerate(memory) if i!=2) !=
                (272,1860,4,2,20,48,16,256,40,1490,1490,16,12,4,4,CAPACITY,24,4,
                 8,4,384,64,OBJECT_BYTES,WORK_BYTES,COPY_BYTES,12)
                or not 0<=memory[2]<=255 or any(not 0<=x<=0xFFFFFFFF for x in args)):
            raise ValueError('outside the IR convolution comparison domain')
        count=int.from_bytes(memory[17][4:8],'little')
        token=int.from_bytes(memory[17][:4],'little')
        if operation in ('sample','resample','produce','prepare','construct') and (count>4076 or count and token!=HEAP):
            raise ValueError('unmapped convolution signed16 source')
        if operation in ('resample','produce','copy') and (args[0]>4096 or args[1]>4096-args[0]):
            raise ValueError('coefficient production range exceeds the reviewed bound')
        if operation in ('produce','construct'):
            length,fade=(int.from_bytes(memory[26][i:i+4],'little') for i in (0,4))
            if length>4096 or fade>length:raise ValueError('unbounded convolution fade parameters')
        if operation=='phase' and not args[1]:raise ValueError('zero phase denominator')
        if operation=='prepare' and args[0]>=16:raise ValueError('invalid effect slot')
        if operation=='construct' and (args[0]>4096 or args[1] not in (0,REGIONS['produce'][0],REGIONS['copy'][0])
                or args[2] not in (0,OBJECT)):
            raise ValueError('unreviewed convolution constructor call')
        if operation=='reset':
            partitions=int.from_bytes(memory[23][4:8],'little')
            frequency=int.from_bytes(memory[23][24:28],'little')
            history=int.from_bytes(memory[23][48:52],'little')
            if (args[0]!=OBJECT or not 1<=partitions<=32 or frequency!=OBJECT+2616+partitions*1032
                    or history!=OBJECT+5696+partitions*2064):
                raise ValueError('reset requires a coherent constructor layout')
        return IrConvolutionMachine(self,memory,operation,args,boundary).run()

class IrConvolutionMachine(IrInstallationMachine):
    def __init__(self,program,memory,operation,args,boundary):
        self.written=None
        super().__init__(program,memory[:19],'trim',(0,0),None,None,0xA7)
        for (base,_),data in zip(MAPPED,memory[19:]):
            self.memory.update({(effect_address(i) if base is None else base+i):value for i,value in enumerate(data)})
        self.memory.update({TAPS+i:value for i,value in enumerate(program.taps)})
        self.boundary=boundary
        self.pc=REGIONS[operation][0]
        self.regs.update({f'r{i}':value for i,value in enumerate(list(args[:4])+[0]*(4-min(4,len(args))))})
        self.object_limit=OBJECT_BYTES
        self.producer_calls=[]
        if operation=='prepare':self.regs.update(r0=EFFECTS+args[0]*480,r1=args[1])
        elif operation=='phase':self.regs.update(r0=WORK,r1=args[0],r2=args[1])
        elif operation=='resample':self.regs.update(r0=WORK,r1=args[0],r2=args[1],r3=args[2])
        elif operation=='produce':self.regs.update(r0=PARAMETERS,r1=WORK,r2=args[0],r3=args[1])
        elif operation=='copy':self.regs.update(r0=COPY,r1=WORK,r2=args[0],r3=args[1])
        elif operation=='fft128':self.regs.update(r0=PERMUTATION,r1=TWIDDLES,r2=WORK)
        elif operation=='real256':
            self.regs.update(r0=PERMUTATION,r1=TWIDDLES,r2=REAL_TWIDDLES,r3=WORK)
            DotMachine.write(self,STACK,OUTPUT,4);DotMachine.write(self,STACK+4,SCRATCH,4)
        elif operation=='construct':
            self.regs.update(r0=args[2],r1=args[0],r2=args[1],r3=COPY if args[1]==REGIONS['copy'][0] else PARAMETERS)

    def set(self,register,value):
        if self.written is not None:self.written.add(register)
        super().set(register,value)

    def snapshot(self):
        return super().snapshot()+tuple(bytes(self.memory[effect_address(i) if base is None else base+i]
                                             for i in range(size)) for base,size in MAPPED)

    def read(self,address,size):
        if OBJECT<=address<OBJECT+OBJECT_BYTES and address+size>OBJECT+self.object_limit:
            raise ValueError('original convolution read exceeds allocation')
        return super().read(address,size)

    def write(self,address,value,size):
        if TAPS<=address<TAPS+36:raise ValueError('attempt to mutate immutable filter taps')
        if OBJECT<=address<OBJECT+OBJECT_BYTES and address+size>OBJECT+self.object_limit:
            raise ValueError('original convolution write exceeds allocation')
        super().write(address,value,size)

    def address(self,expression):
        if match:=re.fullmatch(r'\+\+(r\d+)=(r\d+)',expression):
            self.set(match[1],self.value(match[1])+self.value(match[2]));return self.value(match[1])
        return super().address(expression)

    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.code or self.pc in self.program.parallel_seconds:
            raise ValueError('convolution execution escaped an instruction packet')
        if not self.program.code[self.pc][0].endswith('  #'):return self.single_step()
        before,carry=dict(self.regs),self.carry
        self.written=set()
        if not self.single_step():raise ValueError('unexpected parallel control transfer')
        first={key:self.regs[key] for key in self.written};after_carry=self.carry
        self.regs,self.carry,self.written=before,carry,set()
        if not self.single_step():raise ValueError('unexpected parallel control transfer')
        self.regs.update(first);self.carry=after_carry;self.written=None
        return True

    def single_step(self):
        self.visited.add(self.pc)
        text,size,_,_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if match:=re.fullmatch(r'call (r\d+)',text):
            target=self.value(match[1])
            if target in (REGIONS['produce'][0],REGIONS['copy'][0]) and self.pc==0x02031A00:
                self.producer_calls.append(tuple(self.value(f'r{i}') for i in range(4)))
                self.returns.append(next_pc);next_pc=target
            elif self.pc in (0x02029670,0x020296E8,0x02029722):
                if not target:raise ValueError('original convolution calls a null allocation service')
                argument=self.value('r0');self.calls.append((target,argument,self.snapshot()))
                result=self.boundary(target,argument,self) if self.boundary else (OBJECT if self.pc==0x02029670 else 0)
                if self.pc==0x02029670:
                    if result not in (0,OBJECT) or argument>OBJECT_BYTES:raise ValueError('invalid synthetic convolution allocation')
                    self.object_limit=argument if result else 0
                for reg in ('r0','r1','r2','r3'):self.set(reg,0xBAD0C0DE)
                self.set('r0',result)
            else:raise ValueError(f'unreviewed convolution callback at {self.pc:#x}')
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) - (r\d+) \(f\)',text):
            self.set(match[1],FLOAT.arithmetic(self.value(match[2]),self.value(match[3]),'sub'))
        elif match:=re.fullmatch(r'(r\d+) = (utof|ftoi)\((r\d+)\)(?: \((trunc)\))?',text):
            result,_=FLOAT.convert(match[2],match[4] or 'even')({0:self.value(match[3])},0,{'s':0,'r':1})
            self.set(match[1],result[1])
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(u\)',text):
            denominator=self.value(match[3])
            if not denominator:raise ValueError('unbounded zero integer divisor')
            self.set(match[1],self.value(match[2])//denominator)
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) \^ (0x[0-9a-fA-F]+)',text):
            self.set(match[1],self.value(match[2])^int(match[3],16))
        elif match:=re.fullmatch(r'if \(\((r\d+) & (\d+)\) != 0\) goto (-?\d+)',text):
            if self.value(match[1])&int(match[2]):next_pc+=int(match[3])
        else:return super().single_step()
        self.pc=next_pc;return True

    def run(self):
        result=super().run();result['producer_calls']=self.producer_calls
        return result
