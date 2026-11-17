"""Decode complete original scene application and its actual selection callers."""
from __future__ import annotations
import re
from preset_application_machine import (PresetApplicationProgram,REGIONS as APP_REGIONS,
    TABLE,TABLE_BYTES,GLOBAL,STATE,EFFECTS,CONFIG,CALLBACKS,CONTROL,STACK,ROOT)
from preset_assets_machine import PresetAssetsMachine
from selection_machine import REGIONS as SELECTION_REGIONS
from dot_machine import DotMachine
from dsp_transition_notification_machine import (DspTransitionNotificationProgram,
    DspTransitionNotificationMachine,PRIOR_MAPPED,DspAudioPathMachine)
from preset_storage_machine import PresetStorageMachine
from pi32v2isa import codec,table

REGIONS={'inner':(0x02009E14,0x0200A1D6),'apply':(0x0200A1D6,0x0200A228),
         'report':(0x0200A228,0x0200A256)}
REUSED={**{k:APP_REGIONS[k] for k in ('parameter_order','metadata','parameter','notify')},
    **{k:SELECTION_REGIONS[k] for k in ('effect_type','effect_enabled')},
    'rate':(0x02002BD8,0x02002BEC),'select':SELECTION_REGIONS['scene'],
    'flush':SELECTION_REGIONS['scene_flush']}
FILTERS,STAGED=0x01C33030,0x01C330E0
MAPPED=((GLOBAL,272),(STATE,12976),(EFFECTS,7680),(CONFIG,68),(CONTROL,640),
        (CALLBACKS,768),(FILTERS,176),(STAGED,176))
SERVICES={0x020027E4:0,0x02008CA2:1,0x0202FD18:3,0x0202FBA6:4,0x020305F8:2,
    0x02002BF6:2,0x020038FA:0,0x0202F07E:3,0x02030530:2,0x020039E0:0,
    0x020091D6:1,0x02008DE2:2,0x02028A34:2,0x02028EB2:1,0x02028F96:0,
    0x02002D10:3,0x01C04862:0}

class SceneApplicationProgram(DspTransitionNotificationProgram):
    def __init__(self):
        super().__init__()
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.metadata=app[TABLE-0x02000120:TABLE-0x02000120+TABLE_BYTES]
        previous=set(self.code);self.raw_regions={};instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=app[start-0x02000120:end-0x02000120];self.raw_regions[name]=raw;pc=start
            while pc<end:
                decoded=codec.decode(instructions,raw,pc-start)
                if decoded is None:raise ValueError(f'unsupported scene instruction at {pc:#x}')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError('instruction crosses scene function boundary')
                self.code[pc]=codec.format(instruction,fields),size,*counts;pc+=size
        for pc in set(self.code)-previous:
            text,size,*_=self.code[pc]
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+ (?:=|<=|&=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed scene parallel packet at {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,operation,*args,boundary=None):
        arity={'inner':1,'apply':1,'report':2,'select':1,'flush':0}
        if (tuple(map(len,memory))!=tuple(n for _,n in MAPPED) or operation not in arity
            or len(args)!=arity[operation] or any(not 0<=v<=0xffffffff for v in args)
            or (operation in ('inner','apply') and args[0]>3)):
            raise ValueError('outside scene comparison domain')
        if operation=='flush' and 3<int.from_bytes(memory[0][88:92],'little')<0x80000000:
            raise ValueError('outside current-scene flush domain')
        return SceneApplicationMachine(self,memory,operation,args,boundary).run()

class SceneControlFallback(PresetAssetsMachine):
    def step(self):
        # Numerical decoders fall back through the existing control opcodes.
        return PresetAssetsMachine.single_step(self)

class SceneApplicationMachine(DspTransitionNotificationMachine,SceneControlFallback):
    def __init__(self,program,memory,operation,args,boundary):
        DspAudioPathMachine.__init__(self,program,[bytearray(n) for _,n in PRIOR_MAPPED],"process",(),())
        self.memory.update({base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)})
        self.memory.update({TABLE+i:v for i,v in enumerate(program.metadata)})
        self.initialize_notification_state()
        self.pc=(REGIONS|REUSED)[operation][0];self.boundary=boundary;self.carry=self.steps=0
        self.calls=[];self.frames=[];self.returns=[];self.visited=set();self.writes=[];self.else_skips={}
        self.library_calls=[];self.internal_calls=[];self.notification_calls=[]
        self.transition_boundary=lambda token,value,m:self.external(token,(value&0xffffffff,0,0,0,0))
        for i,value in enumerate(args):self.regs[f'r{i}']=value

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(n)) for base,n in MAPPED)

    def run(self):
        result=PresetStorageMachine.run(self)
        if self.pending_notifications:raise ValueError('unfinished scene transition notification')
        result['internal_calls']=self.internal_calls;result['real_notifications']=self.real_notifications
        return result

    def mutate(self,address,value,size):
        if not any(a<=address and address+size<=a+n for a,n in MAPPED):
            raise ValueError('scene callback mutation escaped mapped state')
        self.write(address,value,size)

    def external(self,target,args):
        if self.boundary is None:raise ValueError('scene execution requires explicit services')
        before=self.snapshot();result=self.boundary(target,args,self)&0xffffffff
        self.calls.append((target,args,before,self.snapshot()))
        return result

    def read(self,address,size):
        if 0x30000000<=address<STACK and address<self.value('sp'):
            raise ValueError('read below active scene stack')
        return DotMachine.read(self,address,size)

    def write(self,address,value,size):
        if 0x30000000<=address<STACK:
            if address<self.value('sp') or address+size>STACK:raise ValueError('scene stack escape')
        elif not any(base<=address and address+size<=base+n for base,n in MAPPED):
            raise ValueError('scene write escaped mapped state')
        self.writes.append((address,value&((1<<(8*size))-1),size));DotMachine.write(self,address,value,size)

    def single_step(self):
        text,size,*_=self.program.code[self.pc];clean=text.removesuffix('  #');next_pc=self.pc+size
        if direct:=re.fullmatch(r'call (-?\d+)',clean):
            self.visited.add(self.pc);target=next_pc+int(direct[1])
            if target in self.program.code:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            if target not in SERVICES:raise ValueError(f'unknown scene service {target:#x}')
            n=SERVICES[target];args=tuple([self.value(f'r{i}') for i in range(n)]+[0]*(5-n))
            result=self.external(target,args)
            for i in range(4):self.set(f'r{i}',0xBAD0C0DE)
            self.set('r0',result);self.pc=next_pc;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(u\)',clean):
            self.visited.add(self.pc);divisor=self.value(match[3])
            self.set(match[1],self.value(match[2])//divisor if divisor else 0);self.pc=next_pc;return True
        if match:=re.fullmatch(r'(r\d+) = umin\((r\d+), (r\d+)\)',clean):
            self.visited.add(self.pc);self.set(match[1],min(self.value(match[2]),self.value(match[3])))
            self.pc=next_pc;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+) & \(1 << (r\d+)\)',clean):
            self.visited.add(self.pc);self.set(match[1],self.value(match[2])&(1<<(self.value(match[3])&31)))
            self.pc=next_pc;return True
        if match:=re.fullmatch(r'if \(\((r\d+) & (r\d+|0x[0-9a-fA-F]+)\) (==|!=) 0\) (?:goto (-?\d+)|(\{))',clean):
            self.visited.add(self.pc);then,otherwise=self.program.code[self.pc][2:]
            condition=bool(self.value(match[1])&self.value(match[2]))==(match[3]=='!=')
            if match[4]:
                if condition:next_pc+=int(match[4])
            else:
                else_start=self.skip(next_pc,then)
                if not condition:next_pc=else_start
                elif otherwise:self.else_skips[else_start]=self.skip(else_start,otherwise)
            self.pc=next_pc;return True
        return super().single_step()
