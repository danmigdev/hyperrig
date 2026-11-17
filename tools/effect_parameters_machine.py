"""Execute complete original parameter changes against borrowed native storage.

The seven new bodies are decoded independently of their portable C. Primitive
arithmetic, metadata/reset helpers, processing estimators, stage execution and
scene transitions execute existing original-instruction models. Remaining
effect/allocation services have explicit mutable boundaries. Only EDB8's private
four-byte output pointer is normalized, without reading uninitialized padding.
"""
from __future__ import annotations
import hashlib
import re
from effect_parameter_support_machine import (EffectParameterSupportProgram,
    EffectParameterSupportMachine, REGIONS as SUPPORT_REGIONS, STATIC as SUPPORT_STATIC)
from effect_processing_machine import (EffectProcessingProgram, EffectProcessingMachine,
    REGIONS as PROCESSING_REGIONS, STATIC as PROCESSING_STATIC, SERVICES as PROCESSING_SERVICES,
    MAPPED, RAM, RAM_BYTES, SAMPLES, SAMPLE_BYTES, ARENA, ARENA_BYTES, STACK, ROOT)
from scene_application_machine import (SceneApplicationProgram, SceneApplicationMachine,
    REGIONS as SCENE_REGIONS, REUSED as SCENE_REUSED, MAPPED as SCENE_MAPPED,
    SERVICES as SCENE_SERVICES)
from dsp_stage_machine import REGIONS as STAGE_REGIONS
from dsp_initialization_machine import TABLE as INITIALIZATION_TABLE, PRIOR_TABLE
from dsp_transition_notification_machine import GAIN_TABLE, GAIN_BYTES
from effect_enable_machine import region_bytes
from ir_processing_machine import FLOAT
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {'commit':(0x0202F07E,0x0202F46C), 'section_kind':(0x0202F4E8,0x0202F502),
    'word_kind':(0x0202F502,0x0202F6B4), 'auxiliary_index':(0x0202F6B4,0x0202F6D4),
    'fast':(0x0202F6D4,0x0202FBA6), 'fast_wrapper':(0x0202FBA6,0x0202FBD6),
    'probe':(0x0202FD18,0x0202FE58)}
REUSED = {'metadata':(0x0202921E,0x02029248), 'reset_slot':(0x020290CC,0x02029112),
          'counter':(0x01C05160,0x01C0516E)}
TABLE_START,TABLE_END = 0x0202F518,0x0202F566
STATIC = {'word_kind_branches':(TABLE_START,TABLE_END),
          'parameter_metadata':(0x0203A614,0x0203B334),
          'scene_coefficient_selector':(PRIOR_TABLE,PRIOR_TABLE+10),
          'scene_initialization_coefficients':INITIALIZATION_TABLE,
          'scene_gain_table':(GAIN_TABLE,GAIN_TABLE+GAIN_BYTES)}
PRIVATE, ALLOCATE = 0x31005000, 0x0202EDB8
EFFECTS, CONFIG, CONTROL, CALLBACKS = 0x01C2C220,0x01C1F7D4,0x01C32DB0,0x01C34190
ROUTES = 0x01C2E5A0
ARITIES = {'commit':3,'section_kind':2,'word_kind':2,'auxiliary_index':2,
    'fast':4,'fast_wrapper':4,'probe':3,'metadata':2,'reset_slot':1,'counter':0,
    'stage':3,'scene_inner':1,'scene_apply':1,'scene_report':2,'scene_select':1,'scene_flush':0}
ENTRY_POINTS = {name:a for name,(a,_) in REGIONS.items()} | {name:a for name,(a,_) in REUSED.items()}
ENTRY_POINTS.update(stage=STAGE_REGIONS['stage'][0],
    scene_inner=SCENE_REGIONS['inner'][0],scene_apply=SCENE_REGIONS['apply'][0],
    scene_report=SCENE_REGIONS['report'][0],scene_select=SCENE_REUSED['select'][0],
    scene_flush=SCENE_REUSED['flush'][0])
# These arities describe complete direct callees, not incidental scratch values.
SERVICES = {0x01C05EC6:1, 0x0202EDB8:3, 0x0202EE3C:5, 0x0202EEBA:1,
    0x0202E328:1, 0x0202EEFA:1, 0x0202EFE2:2, 0x0202CF62:1,
    0x0202F014:1, 0x0202F02E:3, 0x0202983A:1, 0x02028CB2:2,
    0x02028DE8:0, 0x0202CD32:1, 0x0202EC30:0}

class EffectParametersProgram:
    def __init__(self):
        self.support=EffectParameterSupportProgram();self.processing=EffectProcessingProgram()
        self.scene=SceneApplicationProgram();self.code={};self.parallel_seconds=set()
        for inherited in (self.support,self.processing,self.scene):
            for pc in self.code.keys()&inherited.code.keys():
                if self.code[pc]!=inherited.code[pc]:raise ValueError('inconsistent joined parameter instruction')
            self.code.update(inherited.code);self.parallel_seconds|=inherited.parallel_seconds
        self.inherited_code=set(self.code);self.regions={};self.raw_regions=self.regions
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();self.app=app
        self.static_regions={**{'support_'+k:v for k,v in SUPPORT_STATIC.items()},
            **{'processing_'+k:v for k,v in PROCESSING_STATIC.items()},**STATIC}
        self.data={name:region_bytes(app,*bounds) for name,bounds in self.static_regions.items()}
        instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);pc=start
            while pc<end:
                if pc==TABLE_START:pc=TABLE_END;continue
                decoded=codec.decode(instructions,raw,pc-start)
                if decoded is None:raise ValueError(f'undecoded parameter instruction {pc:#x}')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError('parameter instruction crosses whole-function boundary')
                item=codec.format(instruction,fields),size,*counts
                if pc in self.code and self.code[pc]!=item:raise ValueError('different reused parameter instruction')
                self.code[pc]=item;pc+=size
        self.parameter_code={pc for pc in self.code if any(a<=pc<b for a,b in (REGIONS|REUSED).values())}
        self.regular_code=set(self.support.code)|set(self.processing.code)|self.parameter_code
        for pc in self.parameter_code:
            text,size,*_=self.code[pc]
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|\^=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed parameter parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)
        branches=self.data['word_kind_branches']
        if len(branches)!=78 or any(TABLE_START+2*int.from_bytes(branches[i:i+2],'little') not in self.code
                                   for i in range(0,len(branches),2)):
            raise ValueError('unreviewed parameter TBH table')

    def __getattr__(self,name):
        # Frozen scene numeric adapters use their original immutable program fields.
        for inherited in (self.scene,self.processing,self.support):
            if hasattr(inherited,name):return getattr(inherited,name)
        raise AttributeError(name)

    def execute(self,memory,entry,arguments=(),boundary=None,mmio=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('invalid parameter memory views')
        name=entry if isinstance(entry,str) else next((k for k,v in ENTRY_POINTS.items() if v==entry),None)
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=x<=MASK32 for x in arguments):
            raise ValueError('invalid parameter entry or original ABI words')
        return EffectParametersMachine(self,memory,name,arguments,boundary,mmio).run()

class EffectParametersMachine(EffectParameterSupportMachine,EffectProcessingMachine):
    def __init__(self,program,memory,operation,arguments,boundary=None,mmio=None):
        self.program,self.operation,self.boundary,self.mmio=program,operation,boundary,mmio
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.public_memory=list(map(bytearray,memory))
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        for name,(start,end) in program.static_regions.items():
            self.memory.update({start+i:v for i,v in enumerate(program.data[name])})
        self.pc=ENTRY_POINTS[operation];self.carry=self.flags=self.steps=0
        self.frames=[];self.returns=[];self.calls=[];self.real_calls=[];self.internal_calls=self.real_calls
        self.mmio_events=[];self.visited=set();self.else_skips={};self.written=set();self.entries={};self.writes=[]
        self.service_sites=[];self.private_address=None;self.private_written=set();self.private_events=[]
        self.scene_view=None
        for i,value in enumerate(arguments):
            if i<4:self.set(f'r{i}',value)
            else:DotMachine.write(self,STACK+4*(i-4),value,4)

    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def state_digest(self):return hashlib.sha256(b''.join(self.snapshot())).hexdigest()
    def read(self,address,size):
        if PRIVATE<=address<PRIVATE+4:
            if self.private_address is None or address+size>PRIVATE+4:raise ValueError('private parameter pointer lifetime')
            address=self.private_address+address-PRIVATE
        if self.private_address is not None and self.private_address<=address<self.private_address+4:
            if any(p not in self.private_written for p in range(address,address+size)):
                raise ValueError('read of uninitialized private parameter output')
        if 0x30000000<=address<STACK and not self.value('sp')<=address<=address+size<=STACK:
            raise ValueError('parameter read escaped active stack')
        return EffectProcessingMachine.read(self,address,size)
    def write(self,address,value,size):
        if PRIVATE<=address<PRIVATE+4:
            if self.private_address is None or address+size>PRIVATE+4:raise ValueError('private parameter pointer lifetime')
            address=self.private_address+address-PRIVATE
        if self.private_address is not None and self.private_address<=address<self.private_address+4:
            if address+size>self.private_address+4:raise ValueError('private output write exceeds four bytes')
            self.private_written.update(range(address,address+size))
        self.writes.append((address,value&((1<<(8*size))-1),size))
        EffectProcessingMachine.write(self,address,value,size)
    def mutate(self,address,value,size):self.write(address,value,size)

    def external(self,target,arguments,count):
        if self.boundary is None:raise ValueError(f'explicit parameter service required {target:#x}')
        args=list(arguments[:count])+[0]*(12-count);before=self.snapshot();private_before=();private_after=()
        private_call=target==ALLOCATE and count==3 and self.pc==0x0202F1EC
        if private_call:
            self.private_address=args[2];self.private_written=set()
            if not self.value('sp')<=self.private_address<=self.private_address+4<=STACK:
                raise ValueError('EDB8 output does not belong to live native stack')
            args[2]=PRIVATE
        preserved={f'r{i}':self.value(f'r{i}') for i in range(4,16)}
        value=self.boundary(target,tuple(args),self)&MASK32
        if preserved!={k:self.value(k) for k in preserved}:raise ValueError('service changed callee-saved registers')
        if private_call:
            if self.private_written!=set(range(self.private_address,self.private_address+4)):
                raise ValueError('EDB8 callback must initialize all four output bytes')
            private_after=((PRIVATE,bytes(self.read(self.private_address+i,1) for i in range(4))),)
            self.private_events.append((self.pc,private_after))
            self.private_address=None;self.private_written=set()
        self.calls.append((target,tuple(args),before,self.snapshot(),private_before,private_after))
        self.service_sites.append((self.pc,target,count))
        return value

    def scene_step(self):
        if self.scene_view is None:
            memory=[]
            for base,n in SCENE_MAPPED:memory.append(bytes(self.memory[base+i] for i in range(n)))
            view=SceneApplicationMachine(self.program,memory,'inner',(0,),self.boundary)
            # Every inherited immutable byte must already have an explicit
            # table declaration. Firmware RAM keeps the caller's supplied state.
            immutable={a:v for a,v in view.memory.items() if 0x02000000<=a<0x03000000}
            if any(self.memory.get(a)!=v for a,v in immutable.items()):
                raise ValueError('undeclared or inconsistent inherited scene table')
            self.scene_view=view
        view=self.scene_view;view.__dict__.update(self.__dict__)
        view.read=lambda address,size:EffectParametersMachine.read(view,address,size)
        view.write=lambda address,value,size:EffectParametersMachine.write(view,address,value,size)
        view.snapshot=lambda:EffectParametersMachine.snapshot(view)
        view.external=lambda target,args:EffectParametersMachine.external(view,target,args,
            1 if view.pc==0x02028A9E else SCENE_SERVICES.get(target,1))
        result=SceneApplicationMachine.step(view)
        for name,value in view.__dict__.items():
            if name not in ('read','write','snapshot','external','scene_view'):self.__dict__[name]=value
        return result

    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        if self.pc not in self.program.regular_code:return self.scene_step()
        return super().step()

    def single_step(self):
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #')
        next_pc=self.pc+size
        if match:=re.fullmatch(r'call (r\d+|-?\d+)',text):
            indirect=match[1].startswith('r');target=self.value(match[1]) if indirect else next_pc+int(match[1])
            installed_clear=indirect and self.pc==0x01C0656E and target==0x0201A9DC
            if target in self.program.code and (not indirect or installed_clear):
                self.real_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            if indirect:
                if self.pc==0x0202F2AA:count=1
                elif any(a<=self.pc<b for a,b in SUPPORT_REGIONS.values()):count=2
                elif self.pc==0x01C10824:count=0
                else:raise ValueError(f'unreviewed indirect parameter call at {self.pc:#x}')
            else:
                count=(SERVICES|PROCESSING_SERVICES|SCENE_SERVICES).get(target)
                if count is None:raise ValueError(f'unreviewed parameter service {target:#x}')
            arguments=tuple(self.value(f'r{i}') if i<4 else self.read(self.value('sp')+4*(i-4),4) for i in range(count))
            result=self.external(target,arguments,count)
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',result);self.pc=next_pc;return True
        if re.fullmatch(r'tb[bh] \[r\d+\]',text) and self.pc!=0x01C06A48:
            # The frozen enable handler is specific to its fade TBB. Other
            # original tables belong to the joined processing/parameter bodies.
            return EffectProcessingMachine.single_step(self)
        if match:=re.fullmatch(r'(r\d+_r\d+) = (r\d+_r\d+) / (r\d+) \(s\)',text):
            value=self.pair(match[2]);registers={0:value&MASK32,1:value>>32,2:self.value(match[3])}
            output,self.flags=FLOAT.divide(True,True)(registers,self.flags,{'s':0,'t':2,'r':4})
            self.set_pair(match[1],output[4]|output[5]<<32);self.pc=next_pc;return True
        return super().single_step()

    def run(self):
        while self.steps<8000000:
            self.steps+=1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value('sp')!=STACK or self.private_address is not None:
                    raise ValueError('unbalanced parameter execution')
                return {'value':self.value('r0'),'high':0,'result':(self.value('r0'),0),
                    'memory':self.snapshot(),'calls':self.calls,'real_calls':self.real_calls,
                    'visited':self.visited,'steps':self.steps,'service_sites':self.service_sites,
                    'private_events':self.private_events,'mmio_events':self.mmio_events,
                    'real_notifications':getattr(self,'real_notifications',[])}
        raise ValueError('parameter instruction budget exhausted')
