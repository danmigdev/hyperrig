"""Execute original effect construction and its actual coefficient arithmetic.

Only six larger type-specific builders remain explicit services. Instruction
semantics come from the pinned ISA model, independently of the portable C.
"""
from __future__ import annotations
import re
from effect_enable_machine import CounterRegion, region_bytes, ROOT
from biquad_generator_machine import BiquadGeneratorMachine, REGIONS as MATH
from biquad_coefficients_machine import REGIONS as COEFFICIENTS, FLOAT, BRANCH
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {
    'mode_shift':(0x01c060fa,0x01c0610a), 'packed_bias':(0x01c0610a,0x01c0611a),
    'signature':(0x01c06514,0x01c06526), 'tail_pointer':(0x01c06526,0x01c06554),
    'size':(0x02029fc8,0x0202a00a), 'rate_exp':(0x0202a680,0x0202a6aa),
    'q30':(0x0202a6aa,0x0202a6ca), 'logarithm':(0x0202a6ca,0x0202a75e),
    'tempo_samples':(0x0202a76c,0x0202a7a8), 'onepole':(0x0202a7b2,0x0202a7f6),
    'tempo_parameter':(0x0202a7f6,0x0202a814), 'tempo_value':(0x0202a814,0x0202a872),
    'type26':(0x0202beb2,0x0202bffc), 'construct':(0x0202cf62,0x0202ddfc),
}
REUSED = {**MATH, 'q28':COEFFICIENTS['q28'], 'normalize':COEFFICIENTS['normalize'],
    'q16':(0x01c0539c,0x01c053bc), 'tempo_selector':(0x0202a75e,0x0202a76c),
    'logical_size':(0x0202a7a8,0x0202a7b2)}
TABLES = {'construct_branches':(0x0202cfac,0x0202cffa),
          'tempo_branches':(0x0202a802,0x0202a808)}
STATIC = {**TABLES, 'frequencies36':(0x0203a550,0x0203a55c),
    'frequencies37_seven':(0x0203b608,0x0203b616), 'widths37_seven':(0x0203b618,0x0203b634),
    'limits37_five':(0x0203b634,0x0203b639), 'frequencies37_five':(0x0203b63a,0x0203b644),
    'widths37_five':(0x0203b644,0x0203b658), 'tempo':(0x0203b658,0x0203b672)}
ABI_REGIONS = {'builder16':(0x0202b838,0x0202b87e), 'builder25':(0x0202b87e,0x0202ba56),
    'builder29':(0x0202ba90,0x0202beb2), 'builder39':(0x0202a872,0x0202ab98),
    'builder_object':(0x0202cd32,0x0202cdba), 'builder_signature':(0x0202cf5a,0x0202cf62),
    'signature_implementation':(0x0202cde4,0x0202cf5a)}
SERVICES = {0x0202b838:1,0x0202b87e:1,0x0202ba90:1,0x0202a872:1,0x0202cd32:1,0x0202cf5a:2}
ARITIES = {name:1 for name in REGIONS}; ARITIES['tempo_value']=2
VOID = {'construct','type26'}
RAM, RAM_BYTES, ARENA, ARENA_BYTES, STACK = 0x01c1f180,0x01c344b4-0x01c1f180,0x33000000,65536,0x30001000
MAPPED = ((RAM,RAM_BYTES),(ARENA,ARENA_BYTES),(0,256),(0xffffff00,256))

class EffectConstructionProgram:
    def __init__(self):
        CounterRegion('counter')
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.code,self.regions,self.parallel_seconds={},{},set()
        self.data={name:region_bytes(app,*span) for name,span in STATIC.items()}
        instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);pc=start
            while pc<end:
                data_end=next((b for a,b in TABLES.values() if pc==a),None)
                if data_end is not None:pc=data_end;continue
                found=codec.decode(instructions,raw,pc-start)
                if found is None:raise ValueError(f'undecoded construction instruction {pc:#x}')
                instruction,fields,size=found;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError('construction instruction crosses whole function')
                self.code[pc]=codec.format(instruction,fields),size,*counts;pc+=size
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|\^=|\|=|\*=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed construction packet {pc:#x}')
                self.parallel_seconds.add(pc+size)
        for name,width,count in (('construct_branches',2,39),('tempo_branches',1,5)):
            start,end=TABLES[name];raw=self.data[name]
            if any(start+2*int.from_bytes(raw[i*width:(i+1)*width],'little') not in self.code for i in range(count)):
                raise ValueError('construction table target not decoded')
            if any(raw[width*count:]):raise ValueError('construction alignment changed')

    def execute(self,memory,name,arguments=(),boundary=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('construction memory views')
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=v<=MASK32 for v in arguments):
            raise ValueError('construction ABI arguments')
        return EffectConstructionMachine(self,memory,name,arguments,boundary).run()

class EffectConstructionMachine(BiquadGeneratorMachine):
    def __init__(self,program,memory,name,arguments,boundary=None):
        self.program,self.operation,self.boundary=program,name,boundary
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        for key,(base,_) in STATIC.items():self.memory.update({base+i:v for i,v in enumerate(program.data[key])})
        self.public_memory=list(map(bytearray,memory));self.pc=REGIONS[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={}
        self.written=set()
        self.math_calls=[];self.production_calls=[];self.normalization_calls=[]
        self.coefficient_requests=[];self.exp_arguments=[]
        for i,v in enumerate(arguments):self.set(f'r{i}',v)

    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def address(self,expression):
        if match:=re.fullmatch(r'(r\d+)\+(r\d+)',expression):
            return (self.value(match[1])+self.value(match[2]))&MASK32
        return super().address(expression)
    def read(self,address,size):
        if address+size>1<<32:raise ValueError('construction read crosses wrap')
        if 0x30000000<=address<STACK and not self.value('sp')<=address<=address+size<=STACK:
            raise ValueError('construction read outside active stack')
        return DotMachine.read(self,address,size)
    def write(self,address,value,size):
        if address+size>1<<32:raise ValueError('construction write crosses wrap')
        if 0x30000000<=address<STACK:
            if not self.value('sp')<=address<=address+size<=STACK:raise ValueError('construction stack escape')
        else:
            for (base,n),data in zip(MAPPED,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(8*size))-1)).to_bytes(size,'little');break
            else:raise ValueError(f'construction write escaped map {address:#x}/{size}')
        self.writes.append((address,value&((1<<(8*size))-1),size));DotMachine.write(self,address,value,size)

    def external(self,target,args,count):
        before=self.snapshot();saved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
        value=self.boundary(target,args,self)&MASK32
        if any(self.value(r)!=v for r,v in saved.items()):raise ValueError('constructor callee-save mutation')
        self.calls.append((target,args,before,self.snapshot(),value));self.service_sites.append((self.pc,target,count))
        return value

    def single_step(self):
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #')
        next_pc=self.pc+size
        if match:=re.fullmatch(r'call (-?\d+)',text):
            target=next_pc+int(match[1])
            if target in self.program.code:
                if target==0x02028734:
                    if not hasattr(self,'coefficient_requests'):self.coefficient_requests=[]
                    self.coefficient_requests.append(tuple(self.value(f'r{i}') for i in range(4))+(self.read(self.value('sp'),4),))
                if target==0x020285d4:
                    if not hasattr(self,'exp_arguments'):self.exp_arguments=[]
                    self.exp_arguments.append(self.value('r0'))
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            count=SERVICES.get(target)
            if count is None or self.boundary is None:raise ValueError(f'unreviewed constructor service {target:#x}')
            args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            value=self.external(target,args,count)
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if match:=re.fullmatch(r'tb([bh]) \[(r\d+)\]',text):
            width=1 if match[1]=='b' else 2
            target=next_pc+2*self.read(next_pc+self.value(match[2]),width)
            if target not in self.program.code:raise ValueError('constructor dispatch escaped code')
            self.pc=target;return True
        if text=='[--sp] = {rets, r5, r4}':
            self.frames.append(({r:self.value(r) for r in ('r4','r5')},self.value('sp')))
            self.set('sp',self.value('sp')-12)
        elif text=='{pc, r5, r4} = [sp++]':
            saved,sp=self.frames.pop()
            if self.value('sp')!=sp-12:raise ValueError('unbalanced logarithm frame')
            self.regs.update(saved,sp=sp)
            if not self.returns:return False
            next_pc=self.returns.pop()
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(([su])\)',text):
            a,b=self.value(match[2]),self.value(match[3])
            if match[4]=='s':a,b=signed(a),signed(b)
            value=0 if not b else (abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)
            self.set(match[1],value)
        elif match:=re.fullmatch(r'(r\d+_r\d+) = (r\d+) \* (r\d+) \(u\)',text):
            self.set_pair(match[1],self.value(match[2])*self.value(match[3]))
        elif match:=re.fullmatch(r'(r\d+_r\d+) = (r\d+_r\d+) / (r\d+) \(([su])\)',text):
            a,b=self.pair(match[2]),self.value(match[3])
            if match[4]=='s':a,b=signed(a,64),signed(b)
            q=0 if not b else abs(a)//abs(b)*(-1 if (a<0)!=(b<0) else 1)
            self.set_pair(match[1],q)
        elif match:=re.fullmatch(r'(r\d+) = uextra\((r\d+), p:(\d+), l:(\d+)\)',text):
            self.set(match[1],self.value(match[2])>>int(match[3])&((1<<int(match[4]))-1))
        elif match:=re.fullmatch(r'(r\d+) ([&|^])= (r\d+)',text):
            a,b=self.value(match[1]),self.value(match[3])
            self.set(match[1],{'&':a&b,'|':a|b,'^':a^b}[match[2]])
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) ([&|^]) (r\d+|0x[0-9A-Fa-f]+)',text):
            a,b=self.value(match[2]),self.value(match[4])
            self.set(match[1],{'&':a&b,'|':a|b,'^':a^b}[match[3]])
        elif match:=re.fullmatch(r'(r\d+) = (r\d+) - (0x[0-9A-Fa-f]+)',text):
            self.set(match[1],self.value(match[2])-int(match[3],16))
        elif match:=re.fullmatch(r'(r\d+) = (smax|smin)\((r\d+), (r\d+)\)',text):
            self.set(match[1],(max if match[2]=='smax' else min)(signed(self.value(match[3])),signed(self.value(match[4]))))
        elif match:=re.fullmatch(r'(r\d+) = (ftou)\((r\d+)\) \((trunc)\)',text):
            result,_=FLOAT.convert(match[2],match[4])({0:self.value(match[3])},0,{'s':0,'r':1})
            self.set(match[1],result[1])
        elif match:=re.fullmatch(r'(r\d+) = (r\d+)\.l \(s\)',text):
            self.set(match[1],signed(self.value(match[2])&65535,16))
        elif match:=re.fullmatch(r'\[(.+)\] = (0x[0-9A-Fa-f]+)',text):
            self.write(self.address(match[1]),int(match[2],16),4)
        elif match:=re.fullmatch(r'(r\d+_r\d+) = 0',text):self.set_pair(match[1],0)
        elif match:=re.fullmatch(r'(r\d+) = sp \+ (\d+)',text):self.set(match[1],self.value('sp')+int(match[2]))
        elif match:=re.fullmatch(r'if \(\((r\d+) & (0x[0-9A-Fa-f]+)\) == 0\) \{',text):
            if self.value(match[1])&int(match[2],16):next_pc=self.skip(next_pc,self.program.code[self.pc][2])
        else:return super().single_step()
        self.pc=next_pc;return True

    def run(self):
        while self.steps<8000000:
            self.steps+=1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value('sp')!=STACK:
                    raise ValueError('unbalanced constructor execution')
                return {'result':(0 if self.operation in VOID else self.value('r0'),0),
                    'memory':self.snapshot(),'calls':self.calls,'service_sites':self.service_sites,
                    'internal_calls':self.internal_calls,'writes':self.writes,'visited':self.visited,'steps':self.steps,
                    'coefficient_requests':self.coefficient_requests,'exp_arguments':self.exp_arguments}
        raise ValueError('constructor instruction budget exhausted')

# A new adapter joins the frozen parameter caller without altering its model.
# The view shares the SAME registers, native stack, memory and return frames.
from effect_parameters_machine import EffectParametersProgram,EffectParametersMachine

class ConstructionParameterProgram(EffectParametersProgram):
    def __init__(self):
        super().__init__();self.construction=EffectConstructionProgram()
        for pc,ins in self.construction.code.items():
            if pc in self.code and self.code[pc]!=ins:raise ValueError('joined constructor code mismatch')
            self.code[pc]=ins
        self.construction_code=set(self.construction.code)
        self.parallel_seconds|=self.construction.parallel_seconds
        for name,span in STATIC.items():
            self.static_regions['construction_'+name]=span
            self.data['construction_'+name]=self.construction.data[name]
    def execute(self,memory,entry,arguments=(),boundary=None,mmio=None):
        machine=ConstructionParameterMachine(self,memory,entry,arguments,boundary,mmio)
        result=machine.run();result['construction_sites']=getattr(machine,'construction_sites',[])
        return result

class ConstructionParameterMachine(EffectParametersMachine):
    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc in (0x0202f37c,0x0202f970):
            if not hasattr(self,'construction_sites'):self.construction_sites=[]
            self.construction_sites.append(self.pc)
        if self.pc not in self.program.construction_code:return super().step()
        view=getattr(self,'construction_view',None)
        if view is None:
            view=object.__new__(EffectConstructionMachine);self.construction_view=view
        view.__dict__.update(self.__dict__)
        view.read=lambda address,size:EffectParametersMachine.read(view,address,size)
        view.write=lambda address,value,size:EffectParametersMachine.write(view,address,value,size)
        view.snapshot=lambda:EffectParametersMachine.snapshot(view)
        view.external=lambda target,args,count:EffectParametersMachine.external(view,target,args,count)
        result=EffectConstructionMachine.step(view)
        for name,value in view.__dict__.items():
            if name not in ('read','write','snapshot','external','construction_view'):self.__dict__[name]=value
        return result
