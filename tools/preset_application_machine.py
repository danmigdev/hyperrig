"""Original complete preset application with explicit downstream service boundaries."""
from __future__ import annotations
import re
from preset_assets_machine import PresetAssetsProgram, PresetAssetsMachine, REGIONS as ASSET_REGIONS, ROOT
from preset_storage_machine import REGIONS as STORAGE_REGIONS
from selection_machine import REGIONS as SELECTION_REGIONS
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

REGIONS={
    'apply':(0x020092FA,0x02009DD0), 'mode':(0x02007348,0x02007352),
    'parameter_order':(0x020091C0,0x020091D6), 'notify':(0x020092E4,0x020092FA),
    'metadata':(0x0202921E,0x02029248), 'parameter':(0x02030948,0x0203097C),
    'placement':(0x02030A9A,0x02030AB6),
}
REUSED={**{f'asset_{k}':v for k,v in ASSET_REGIONS.items()},
        'header':(0x02006F14,0x02006F3A),
        **{k:SELECTION_REGIONS[k] for k in ('chain_read','effect_type','effect_enabled')},
        'rate':(0x02002BD8,0x02002BEC)}
GLOBAL,STATE,WORKING,EFFECTS,CONTROL,CONFIG,CALLBACKS=0x01C1F180,0x01C26890,0x01C24790,0x01C2C220,0x01C32DB0,0x01C1F7D4,0x01C34190
LOCAL,OUTPUT,PRIVATE,STACK=0x30000ECC,0x31004000,0x31005000,0x30001000
TABLE,TABLE_BYTES=0x0203A614,3360
MAPPED=((GLOBAL,272),(STATE,4100),(WORKING,1490),(EFFECTS,7680),(CONTROL,640),(CONFIG,68),(CALLBACKS,768),(OUTPUT,8))
SERVICES={
    0x01C04862:0,0x01C05E7E:0,0x02002786:1,0x020027E4:0,0x02002810:3,
    0x02002BEC:0,0x02002BF6:2,0x02002D10:3,0x020038FA:0,0x020039E0:0,0x020054A8:1,
    0x02008586:4,0x020087CC:1,0x020089F2:0,0x02008A62:2,0x02008CA2:1,
    0x02008CEE:1,0x02008D4C:1,0x02008DE2:2,0x02008E2E:2,0x02008EAC:1,
    0x0200907A:0,0x02009082:2,0x020090C4:1,0x020091D6:1,
    0x02028A34:2,0x02028DE8:0,0x02028EB2:1,0x0202902A:2,0x02029AFC:1,
    0x0202E710:3,0x0202EA90:3,0x0202EB4C:1,0x0202ED2E:0,0x0202ED7E:0,
    0x0202F07E:3,0x0202F46C:1,0x0202FBD6:1,0x0202FEE4:5,0x02030068:2,
    0x02030110:1,0x02030602:2,0x0203060A:2,0x020306EE:1,0x0203071A:3,
    0x0203076C:1,0x0203086A:0,0x02030906:1,0x02030A92:2,
    0x02030B66:5,0x02030C64:4,
}

def buffers(target,args,memory):
    """Only initialized pointee inputs/outputs, never incidental stack padding."""
    ranges=[]
    if target==0x0202FEE4:ranges=[(args[1],14)]
    elif target==0x02028A34:ranges=[(args[0],12)]
    elif target==0x02008EAC:ranges=[(args[0],min(memory.read(WORKING+1,1),16))]
    elif target==0x02030068:ranges=[(args[1],4)]
    return tuple((address,bytes(memory.read(address+i,1) for i in range(n))) for address,n in ranges)

class PresetApplicationProgram(PresetAssetsProgram):
    def __init__(self):
        super().__init__()
        app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.metadata=app[TABLE-0x02000120:TABLE-0x02000120+TABLE_BYTES]
        self.code={};self.parallel_seconds=set();self.raw_regions={};instructions=table.load()
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=app[start-0x02000120:end-0x02000120];self.raw_regions[name]=raw;pc=start
            while pc<end:
                decoded=codec.decode(instructions,raw,pc-start)
                if decoded is None:raise ValueError(f'unsupported application encoding at {pc:#x}')
                instruction,fields,size=decoded;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError('instruction crosses application boundary')
                self.code[pc]=codec.format(instruction,fields),size,*counts;pc+=size
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if not re.match(r'r\d+ (?:=|<=)',text) or bsize!=2 or '[' not in following:
                    raise ValueError(f'unreviewed application parallel packet at {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self,memory,operation,*args,boundary=None):
        arity={'apply':1,'parameter_order':2,'metadata':2,'parameter':2,'placement':1,'mode':0,'notify':2}
        if (operation not in arity or len(args)!=arity[operation] or len(memory)!=len(MAPPED)
            or any(len(data)!=size for data,(_,size) in zip(memory,MAPPED))
            or any(not 0<=v<=0xffffffff for v in args) or max(memory[4][14:16])>10):
            raise ValueError('outside application comparison domain')
        return PresetApplicationMachine(self,memory,operation,args,boundary).run()

class PresetApplicationMachine(PresetAssetsMachine):
    def __init__(self,program,memory,operation,args,boundary):
        self.program=program;self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:value for (base,_),data in zip(MAPPED,memory) for i,value in enumerate(data)}
        self.memory.update({TABLE+i:value for i,value in enumerate(program.metadata)})
        self.pc=REGIONS[operation][0];self.boundary=boundary;self.carry=self.steps=0
        self.calls=[];self.frames=[];self.returns=[];self.visited=set();self.writes=[];self.else_skips={}
        self.library_calls=[];self.alias=None;self.internal_calls=[]
        for i,value in enumerate(args):self.regs[f'r{i}']=value
        if operation=='apply':self.regs.update(r1=OUTPUT,r2=OUTPUT+4)

    def run(self):
        result=super().run();result['internal_calls']=self.internal_calls
        return result

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(n)) for base,n in MAPPED)

    def read(self,address,size):
        if self.alias and PRIVATE<=address and address-PRIVATE+size<=self.alias[1]:
            address=self.alias[0]+address-PRIVATE
        if 0x30000000<=address<STACK and address<self.value('sp'):
            raise ValueError('read below active application stack')
        return DotMachine.read(self,address,size)

    def write(self,address,value,size):
        if self.alias and PRIVATE<=address and address-PRIVATE+size<=self.alias[1]:
            address=self.alias[0]+address-PRIVATE
        if 0x30000000<=address<STACK:
            if address<self.value('sp') or address+size>STACK:raise ValueError('application stack escape')
        elif not any(base<=address and address+size<=base+n for base,n in MAPPED):
            raise ValueError('application write escaped mapped state')
        self.writes.append((address,value&((1<<(8*size))-1),size))
        DotMachine.write(self,address,value,size)

    def single_step(self):
        text,size,*_=self.program.code[self.pc];clean=text.removesuffix('  #');next_pc=self.pc+size
        direct=re.fullmatch(r'call (-?\d+)',clean);indirect=re.fullmatch(r'call (r\d+)',clean)
        if direct or indirect:
            self.visited.add(self.pc)
            target=next_pc+int(direct[1]) if direct else self.value(indirect[1])
            if direct and target in self.program.code:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            if direct and target not in SERVICES:raise ValueError(f'unknown application service {target:#x}')
            arity=SERVICES[target] if direct else 1
            args=[self.value(f'r{i}') if i<4 else self.read(self.value('sp'),4) for i in range(arity)]
            args+= [0]*(5-arity)
            if target==0x02002810 and not LOCAL<=args[1]<LOCAL+256:
                self.alias=(args[1],args[2]);args[1]=PRIVATE
            args=tuple(args);before=self.snapshot();pointed=buffers(target,args,self)
            if self.boundary is None:raise ValueError('application requires explicit service callback')
            result=self.boundary(target,args,self)&0xffffffff
            self.calls.append((target,args,before,pointed,self.snapshot(),buffers(target,args,self)))
            self.alias=None
            if self.read(CONTROL+14,1)>10 or self.read(CONTROL+15,1)>10:raise ValueError('service invalidated chain domain')
            for i in range(4):self.set(f'r{i}',0xBAD0C0DE)
            self.set('r0',result);self.pc=next_pc;return True
        if match:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(u\)',clean):
            divisor=self.value(match[3])
            if not divisor:raise ValueError('application unsigned division by zero')
            self.visited.add(self.pc);self.set(match[1],self.value(match[2])//divisor);self.pc=next_pc;return True
        if match:=re.fullmatch(r'if \(\((r\d+) & (r\d+)\) != 0\) \{',clean):
            self.visited.add(self.pc);then,otherwise=self.program.code[self.pc][2:]
            else_start=self.skip(next_pc,then)
            if not self.value(match[1])&self.value(match[2]):next_pc=else_start
            elif otherwise:self.else_skips[else_start]=self.skip(else_start,otherwise)
            self.pc=next_pc;return True
        return super().single_step()
