"""Execute complete preset preparation and pair-transaction instructions.

The original instruction reference uses shared registers, stack and byte maps.
Physical storage, allocation and platform coordination remain explicit services.
No portable C is used to produce the original result.
"""
from __future__ import annotations
import hashlib
import re
from effect_ownership_machine import EffectOwnershipMachine
from effect_enable_machine import CounterRegion,region_bytes,ROOT
from effect_parameter_support_machine import REGIONS as SUPPORT
from dot_machine import DotMachine,MASK32
from pi32v2isa import codec,table

REGIONS={
 'prepare':(0x020031d4,0x020034ce),'replace_pair':(0x02003040,0x020031be),
 'erase_block':(0x02002e08,0x02002e6a),'read_forward':(0x02002874,0x0200287a),
 'erased':(0x0200287a,0x020028c2),'write_forward':(0x02002fae,0x02002fb4),
 'ordered_write':(0x02002fb4,0x02002ff6),'readback':(0x02002ff6,0x02003040),
 'record_copy':(0x020077aa,0x020077ec),'preset_write':(0x020077ec,0x02007966),
 'invalidate':(0x02007966,0x02007976),
}
REUSED={'block':(0x020026ba,0x020026d6),'crc':(0x020028c2,0x020028f2),
 'address':(0x0200777a,0x020077aa),'cache_invalidate':(0x0200294e,0x02002994),
 'journal_write':(0x02002f16,0x02002fae),'journal_erase':(0x02002d9e,0x02002e08),
 'compare':(0x020282bc,0x020282f4),'rate':(0x02002bd8,0x02002bec),
 'elapsed':(0x020031be,0x020031d4),'memmove':SUPPORT['memmove']}
STATIC={}
ARITIES=dict(prepare=0,replace_pair=5,erase_block=1,read_forward=3,erased=1,
 write_forward=3,ordered_write=3,readback=3,record_copy=2,preset_write=4,invalidate=1)
VOID={'prepare','invalidate'}
GLOBAL,STATE,CACHE,ARENA,STACK=0x01c1f180,0x01c26890,0x01c2422c,0x33000000,0x30001000
MAPPED=((GLOBAL,0x01c344b4-GLOBAL),(ARENA,16384),(0,256),(0xffffff00,256))
SERVICES={0x02002810:3,0x02002ef2:4,0x02002b80:3,0x0203c15c:1,
 0x0203d218:1,0x01c04862:0,0x02002d10:3,0x02002772:0,0x02002bcc:0,
 0x02002786:1,0x02002d06:1,0x02002d70:3,0x02002920:0,0x0203feb8:1}
JOURNAL='firmware/src/hyperrig_capture_journal.c'
JOURNAL_SHA='a3517ca130212467a049d0948cc4c77cf1288f86fb8d8e5bc062b35a21a5e78b'

def body(text,name):
    start=text.index('int '+name+'(');brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]

def journal_derivatives():
    if hashlib.sha256((ROOT/JOURNAL).read_bytes()).hexdigest()!=JOURNAL_SHA:
        raise ValueError('frozen journal parent changed')
    source=(ROOT/JOURNAL).read_text()
    out=[]
    for name in ('invalidate','write','erase'):
        value=body(source,'hyperrig_capture_journal_'+name)
        value=value.replace('int hyperrig_capture_journal_'+name,'static uint32_t journal_'+name)
        value=value.replace('hyperrig_capture_journal_runtime *runtime','Preparation *s')
        value=value.replace('const uint8_t *source','uint32_t source')
        value=value.replace(', const hyperrig_capture_journal_io *io','')
        value=value.replace('if (!runtime) return -200;','if (s->status) return (uint32_t)s->status;')
        value=value.replace('runtime->metadata.cache[slot * 20 + 16] = 0;','put(s, CACHE + slot * 20 + 16, 0, 1);')
        value=value.replace('slot_base(slot)','(slot < 8 ? UINT32_C(0xdf000) + (slot << 13) : UINT32_C(0xcf000) + ((slot - 8) << 13))')
        value=value.replace('for (slot = 0; slot < 15; ++slot)', 'for (slot = 0; slot < 15 && spend(s); ++slot)')
        if name=='invalidate':out.append(value);continue
        value=value.replace('    if (!valid(runtime, io) || size > 8192 || (!source && size)) return -200;','    uint32_t frame = enter(s, 36);')
        value=value.replace('    if (!valid(runtime, io) || pages > 64) return -200;','    uint32_t frame = enter(s, 16);')
        value=value.replace('return -1;', '{ s->sp = frame; return UINT32_MAX; }')
        value=value.replace('hyperrig_capture_journal_invalidate(runtime,','journal_invalidate(s,')
        value=value.replace('word(runtime->controls.controls.state + 280)','get(s, STATE + 280, 4)')
        value=value.replace('while (complete && offset < size)', 'while (complete && offset < size && spend(s))')
        value=value.replace('current < end;', 'current < end && spend(s);')
        value=value.replace('io->program(io->opaque, at, source + offset, amount)',
            'service(s, UINT32_C(0x02002f74), UINT32_C(0x02002ef2), 0, source + offset, amount, at)')
        sites=(('PREPARE','0, 0, 0',0x02002f36 if name=='write' else 0x02002dc2,0x02002772),
          ('MODE','0, 0, 0',0x02002f3a if name=='write' else 0x02002dc6,0x02002bcc),
          ('ACTIVITY','2, 0, 0',0x02002f40,0x02002786),
          ('CLOCK','0, 0, 0',0x02002f44 if name=='write' else 0x02002dd6,0x01c04862),
          ('YIELD','1, 0, 0',0x02002f8c,0x0203feb8),
          ('EVENT','1, address, stamp',0x02002f9a,0x02002d70),
          ('ACTIVITY','0, 0, 0',0x02002fa2 if name=='write' else 0x02002df2,0x02002786),
          ('GATE','1, 0, 0',0x02002dcc,0x02002d06),
          ('ACTIVITY','3, 0, 0',0x02002dd2,0x02002786),
          ('ERASE_SECTOR','0, 200, current',0x02002de4,0x02002b80),
          ('EVENT','2, current, stamp',0x02002dee,0x02002d70),
          ('GATE','0, 0, 0',0x02002e02,0x02002d06))
        for token,args,site,target in sites:
            value=value.replace(f'call(io, HYPERRIG_JOURNAL_{token}, {args})',
                f'service(s, UINT32_C(0x{site:08x}), UINT32_C(0x{target:08x}), {args}, 0)')
        value=value.replace('    return complete ? 0 : -3;', '    s->sp = frame; return complete ? 0 : UINT32_C(0xfffffffd);')
        if name=='erase':value=value.replace('    return 0;', '    s->sp = frame; return 0;')
        out.append(value)
    return '\n\n'.join(out)+'\n'

def check_derivatives():
    source=(ROOT/'firmware/src/hyperrig_preset_storage_preparation.c').read_text()
    marker='/* BEGIN JOURNAL BYTE-VIEW DERIVATIVES */\n';end='/* END JOURNAL BYTE-VIEW DERIVATIVES */'
    actual=source.split(marker,1)[1].split(end,1)[0]
    if actual!=journal_derivatives():raise ValueError('journal mapped derivative differs from exact transformations')
    return {'parent':JOURNAL,'parent_sha256':hashlib.sha256((ROOT/JOURNAL).read_bytes()).hexdigest(),
      'bodies':['invalidate','write','erase'],'new_original_functions':0,
      'adaptations':['borrowed original-address byte accesses','actual direct service sites',
        'native stack depth for scoped private buffers','finite work guards','remove earlier typed-API bounds']}

class PresetStoragePreparationProgram:
    def __init__(self):
        CounterRegion('counter');app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();isa=table.load()
        self.code,self.regions,self.parallel_seconds,self.data={},{},set(),{}
        for name,(start,end) in (REGIONS|REUSED).items():
            raw=self.regions[name]=region_bytes(app,start,end);cursor=0
            while cursor<len(raw):
                found=codec.decode(isa,raw,cursor)
                if found is None:raise ValueError(f'undecoded storage preparation {start+cursor:#x}')
                ins,fields,size=found;counts=[0,0]
                if ins.block:
                    for i,k in enumerate(('then','else')):
                        f=ins.fields[ins.block[k]];counts[i]=fields[ins.block[k]]*f.scale+f.add
                if cursor+size>len(raw):raise ValueError('storage instruction crosses complete body')
                self.code[start+cursor]=codec.format(ins,fields),size,*counts;cursor+=size
        self.service_sites={}
        for pc,(text,size,*_) in self.code.items():
            if text.endswith('  #'):
                if self.code[pc+size][1]!=2 or '[' not in self.code[pc+size][0]:raise ValueError('unreviewed storage packet')
                self.parallel_seconds.add(pc+size)
            if m:=re.fullmatch(r'call (-?\d+)',text):
                target=pc+size+int(m[1])
                if target not in self.code:
                    if target not in SERVICES:raise ValueError(f'unclosed storage dependency {pc:#x}->{target:#x}')
                    self.service_sites[pc]=(target,SERVICES[target])
            elif text.startswith('call '):raise ValueError('unexpected indirect storage call')
    def execute(self,memory,name,args=(),boundary=None):
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED) or name not in ARITIES or len(args)!=ARITIES[name]:
            raise ValueError('storage preparation call domain')
        return PresetStoragePreparationMachine(self,memory,name,args,boundary).run()

class PresetStoragePreparationMachine(EffectOwnershipMachine):
    def __init__(self,program,memory,name,args,boundary):
        self.program,self.operation,self.boundary=program,name,boundary
        self.regs={f'r{i}':0 for i in range(16)};self.regs['sp']=STACK
        self.memory={base+i:v for (base,_),data in zip(MAPPED,memory) for i,v in enumerate(data)}
        self.public_memory=list(map(bytearray,memory));self.pc=REGIONS[name][0]
        self.carry=self.flags=self.steps=0;self.frames=[];self.returns=[];self.calls=[];self.internal_calls=[]
        self.service_sites=[];self.writes=[];self.visited=set();self.else_skips={};self.written=set();self.entries={}
        self.real_calls=self.internal_calls;self.mmio=None;self.mmio_events=[];self.guard=0;self.stop_extra_overread=False
        for i,value in enumerate(args):
            if i<4:self.set(f'r{i}',value)
            else:DotMachine.write(self,STACK+4*(i-4),value,4)
    def snapshot(self):return tuple(map(bytes,self.public_memory))
    def read(self,address,size):return DotMachine.read(self,address,size)
    def write(self,address,value,size):
        if address+size>1<<32:raise ValueError('storage write crosses address wrap')
        if not 0x30000000<=address<=address+size<=STACK+64:
            for (base,n),data in zip(MAPPED,self.public_memory):
                if base<=address<=address+size<=base+n:
                    data[address-base:address-base+size]=(value&((1<<(size*8))-1)).to_bytes(size,'little');break
            else:raise ValueError(f'storage write outside mapped memory {address:#x}/{size}')
        self.writes.append((address,value&((1<<(size*8))-1),size));DotMachine.write(self,address,value,size)
    def single_step(self):
        self.visited.add(self.pc);text,size,*_=self.program.code[self.pc];text=text.removesuffix('  #');next_pc=self.pc+size
        if m:=re.fullmatch(r'call (-?\d+)',text):
            target=next_pc+int(m[1])
            if target in self.program.code:
                self.internal_calls.append(target);self.returns.append(next_pc);self.pc=target;return True
            expected,count=self.program.service_sites[self.pc]
            if expected!=target or self.boundary is None:raise ValueError('storage service site mismatch')
            args=tuple(self.value(f'r{i}') for i in range(count))+(0,)*(12-count)
            before=hashlib.sha256(b''.join(self.snapshot())).hexdigest();value=self.boundary(target,args,self)&MASK32
            after=hashlib.sha256(b''.join(self.snapshot())).hexdigest()
            self.calls.append((target,args,before,after,value));self.service_sites.append((self.pc,target,count))
            for i in range(4):self.set(f'r{i}',0xbad0c0de)
            self.set('r0',value);self.pc=next_pc;return True
        if m:=re.fullmatch(r'rep (\d+) (\d+) \{',text):
            body=next_pc;end=body+int(m[1])
            for _ in range(int(m[2])):
                self.pc=body
                while self.pc<end:
                    self.steps+=1
                    if not self.step():raise ValueError('constant REP body returned')
                if self.pc!=end:raise ValueError('constant REP escaped body')
            self.pc=end;return True
        if m:=re.fullmatch(r'\[(.+)\] &= ~\(1 << (r\d+)\)',text):
            address=self.address(m[1]);self.write(address,self.read(address,4)&~(1<<(self.value(m[2])&31)),4)
            self.pc=next_pc;return True
        if m:=re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(u\)',text):
            divisor=self.value(m[3]);self.set(m[1],self.value(m[2])//divisor if divisor else 0)
            self.pc=next_pc;return True
        return super().single_step()
    def run(self):
        while self.steps<12000000:
            self.steps+=1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value('sp')!=STACK:raise ValueError('unbalanced storage return')
                return {'result':(0 if self.operation in VOID else self.value('r0'),0),'memory':self.snapshot(),
                    'calls':self.calls,'service_sites':self.service_sites,'visited':self.visited,'steps':self.steps,
                    'internal_calls':self.internal_calls,'writes':self.writes}
        raise ValueError('storage instruction budget exhausted')
