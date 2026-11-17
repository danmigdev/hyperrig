"""Original effect creation, resource setup and tempo instructions on shared RAM.

The registry contains complete bodies. Callback ABI belongs to the call site;
loading another original body never converts an indirect token into a call.
"""
from __future__ import annotations
import re
from effect_parameter_construction_machine import (
    EffectParameterConstructionProgram, EffectParameterConstructionMachine,
    REGIONS as PARAMETER_REGIONS, ENTRY_POINTS as PARAMETER_ENTRIES,
    ARITIES as PARAMETER_ARITIES, MAPPED, STACK, ROOT, region_bytes)
from effect_parameters_machine import EffectParametersMachine, SERVICES
from ir_effect_numerical_machine import (IrEffectNumericalProgram, IrEffectNumericalMachine,
    ALL_REGIONS as IR_REGIONS, INDIRECT_ARITIES as IR_INDIRECT, STATIC as IR_STATIC)
from dot_machine import DotMachine, MASK32
from pi32v2isa import codec, table

REGIONS = {
    'create':(0x0202e710,0x0202ea90),'create_disabled':(0x0202ea90,0x0202eabc),
    'tempo':(0x0202f46c,0x0202f4e8),'demand':(0x0202def2,0x0202df04),
    'allocate':(0x0202e4c2,0x0202e710),'refresh29':(0x0202e328,0x0202e346),
    'initialize29':(0x0202dfe4,0x0202e328),'refresh30':(0x0202e3ce,0x0202e3f6),
    'initialize30':(0x0202e346,0x0202e3ce),'pool_claim':(0x0202e3f6,0x0202e432),
    'pool_attach':(0x0202e432,0x0202e4c2),'demand_by_type':(0x0202a00a,0x0202a076),
    'partition_sizes':(0x0202a1be,0x0202a226),'partition_pack':(0x0202a250,0x0202a2a4),
    'object_count':(0x02029c22,0x02029c3e),'object_segment':(0x02029ed4,0x02029f8e),
    'segment_bytes':(0x02029f8e,0x02029f98),'object_total':(0x02029f98,0x02029fc8),
    'object_extra':(0x02029e3c,0x02029e54),'buffer_selector':(0x01c065a4,0x01c065b4),
    'layout29':(0x01c05f1c,0x01c05ff2),'saturating_double':(0x0202df9a,0x0202dfb6),
    'phase_pair':(0x0202dfb6,0x0202dfe4),'route_insert':(0x0202ddfc,0x0202de50),
    'base_cost':(0x0202a664,0x0202a680),'insertion_cost':(0x0202a5de,0x0202a664),
    'neighbor_group':(0x0202a50a,0x0202a5de),'default_mode':(0x01c05d92,0x01c05dcc),
    'has_mode':(0x01c05d78,0x01c05d92),'mode_cost':(0x01c05dcc,0x01c05e14),
    'next_mode':(0x01c06088,0x01c06098),'pool_full':(0x01c06038,0x01c0604e),
    'stereo_extra_cost':(0x01c06098,0x01c060e6),'group_eligible':(0x01c0604e,0x01c0606e),
    'group_fixed':(0x01c0606e,0x01c06088),'total_cost':(0x02028de8,0x02028e46),
    'slot_cost':(0x02028cb2,0x02028cf8),'route_cost':(0x02028cf8,0x02028d8a),
    'branch_cost':(0x02028c0c,0x02028c5c),'filter_cost':(0x02028db0,0x02028de8),
    'filter_enabled':(0x02028d8a,0x02028db0),'estimate_slot':(0x01c05d02,0x01c05d40),
    'type_cost':(0x0202930e,0x0202936c),'ir_partition_cost':(0x01c05d4a,0x01c05d6a),
    'ir_fallback_cost':(0x01c05d6a,0x01c05d78),
}
REUSED = {**{'parameter_'+k:v for k,v in PARAMETER_REGIONS.items()},
    **{'ir_'+k:v for k,v in IR_REGIONS.items()},'convert_effect':(0x0202a452,0x0202a50a),
    'neighbors':(0x0202de8c,0x0202def2)}
STATIC = {'stereo_branches':(0x01c060a6,0x01c060c9),
    'stereo_alignment':(0x01c060c9,0x01c060ca),'group_flags':(0x0203b940,0x0203b97c),
    'object1_short_lengths':(0x0203b4ae,0x0203b4b6)}
# Raw helpers have no caller-count guard. These two bytes are authenticated
# only for explicit above-count witnesses, not added to inventory exclusions.
AUXILIARY_STATIC={'raw_object1_index13':(0x0203b4b6,0x0203b4b8)}
ARITIES = dict.fromkeys(REGIONS,1)
ARITIES.update(create=3,create_disabled=3,allocate=2,initialize30=2,pool_claim=0,
    pool_attach=2,demand_by_type=3,partition_sizes=4,partition_pack=4,object_segment=2,
    segment_bytes=2,buffer_selector=2,layout29=2,phase_pair=4,route_insert=3,
    insertion_cost=4,neighbor_group=6,mode_cost=2,pool_full=0,group_eligible=2,
    group_fixed=2,total_cost=0,slot_cost=2,branch_cost=2,filter_cost=0,ir_partition_cost=2,estimate_slot=2)
VOID = {'refresh29','refresh30','initialize29','initialize30','phase_pair','route_insert'}
PARAMETER_JOINS = {0x0202f338:0x0202e328,0x0202f412:0x02028cb2,
    0x0202f44a:0x02028de8,0x0202fda0:0x02028cb2,0x0202fe48:0x02028de8}
CREATION_JOINS = {0x0202e9ae:0x0202cf62,0x0202e9d4:0x0202cf62,
    0x0202e92a:0x0202983a,0x0202f4ba:0x0202f07e,0x0202f4cc:0x0202f07e}
INDIRECT_ARITIES = dict.fromkeys((0x0202e798,0x0202e810,0x0202e834,0x0202e94a,
    0x0202e9ee,0x0202ea1e,0x0202ea4e,0x0202ea84),3)
INDIRECT_ARITIES.update({0x0202e616:0,0x0202e6c4:0,0x0202e70c:1})
ENTRY_POINTS = {k:v[0] for k,v in REGIONS.items()} | {
    'parameter_'+k:v for k,v in PARAMETER_ENTRIES.items() if k in
    ('commit','probe','fast','fast_wrapper','section_kind','word_kind','auxiliary_index')}
ARITIES.update({'parameter_'+k:PARAMETER_ARITIES[k] for k in PARAMETER_ENTRIES if 'parameter_'+k in ENTRY_POINTS})

class EffectSetupProgram(EffectParameterConstructionProgram):
    def __init__(self):
        super().__init__();prior=set(self.code);self.ir=IrEffectNumericalProgram()
        self.ir_code=set(self.ir.code);self.setup_code=set();isa=table.load()
        for pc,item in self.ir.code.items():
            if pc in self.code and self.code[pc]!=item:raise ValueError('IR setup instruction mismatch')
            self.code[pc]=item
        self.parallel_seconds|=self.ir.parallel_seconds
        self.regions.update({'ir_'+k:v for k,v in self.ir.regions.items()})
        for key,bounds in (STATIC|IR_STATIC|AUXILIARY_STATIC).items():
            self.static_regions['setup_'+key]=bounds;self.data['setup_'+key]=region_bytes(self.app,*bounds)
        for name,(start,end) in (REGIONS|{k:REUSED[k] for k in ('convert_effect','neighbors')}).items():
            raw=self.regions['setup_'+name]=region_bytes(self.app,start,end);pc=start
            while pc<end:
                if pc==0x01c060a6:pc=0x01c060ca;continue
                found=codec.decode(isa,raw,pc-start)
                if found is None:raise ValueError(f'undecoded setup body {pc:#x}')
                instruction,fields,size=found;counts=[0,0]
                if instruction.block:
                    for i,kind in enumerate(('then','else')):
                        spec=instruction.fields[instruction.block[kind]]
                        counts[i]=fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size>end:raise ValueError('setup body crosses endpoint')
                record=codec.format(instruction,fields),size,*counts
                if pc in self.code and self.code[pc]!=record:raise ValueError('setup overlap mismatch')
                self.code[pc]=record;self.setup_code.add(pc);pc+=size
        self.regular_code|=self.setup_code|self.ir_code
        for pc in self.setup_code:
            text,size,*_=self.code[pc]
            if text.endswith('  #'):
                following,bsize,*_=self.code[pc+size]
                if bsize!=2 or '[' not in following:raise ValueError('setup parallel packet')
                self.parallel_seconds.add(pc+size)
        if self.data['setup_stereo_alignment']!=b'\0':raise ValueError('stereo alignment')
        if any(0x01c060a6+2*v not in self.code for v in self.data['setup_stereo_branches']):
            raise ValueError('stereo branch target')
        self.added_code=set(self.code)-prior
        self.blocked_incoming={}
        for pc in prior:
            text,size,*_=self.code[pc];match=re.fullmatch(r'call (-?\d+)',text.removesuffix('  #'))
            if match and pc+size+int(match[1]) in self.added_code and pc not in PARAMETER_JOINS:
                self.blocked_incoming[pc]=pc+size+int(match[1])
        for pc,target in (PARAMETER_JOINS|CREATION_JOINS).items():
            text,size,*_=self.code[pc]
            if text!=f'call {target-pc-size}':raise ValueError('setup direct join changed')
        self.new_code={pc for pc in self.code if any(a<=pc<b for a,b in REGIONS.values())}
        if len(self.new_code)!=1759:raise ValueError('setup new instruction count')

    def execute(self,memory,entry,arguments=(),boundary=None,mmio=None):
        name=entry if isinstance(entry,str) else next((k for k,v in ENTRY_POINTS.items() if v==entry),None)
        if name not in ARITIES or len(arguments)!=ARITIES[name] or any(not 0<=v<=MASK32 for v in arguments):
            raise ValueError('setup entry/ABI words')
        if tuple(map(len,memory))!=tuple(n for _,n in MAPPED):raise ValueError('setup memory views')
        return EffectSetupMachine(self,memory,name,arguments,boundary,mmio).run()

class EffectSetupMachine(EffectParameterConstructionMachine):
    def __init__(self,program,memory,name,arguments,boundary,mmio):
        super().__init__(program,memory,'commit',(0,0,0),boundary,mmio,False)
        self.operation=name;self.pc=ENTRY_POINTS[name];self.setup_sites=[];self.ir_view=None
        self.producer_calls=[];self.guard=0;self.stop=None;self.stop_visits=0
        self.estimate_words=[];self.type30_outputs=[]
        for i,value in enumerate(arguments):
            if i<4:self.set(f'r{i}',value)
            else:DotMachine.write(self,STACK+4*(i-4),value,4)

    def external_call(self,target,count,size):
        args=tuple(self.value(f'r{i}') if i<4 else self.read(self.value('sp')+4*(i-4),4) for i in range(count))
        value=self.external(target,args,count)
        for i in range(4):self.set(f'r{i}',0xbad0c0de)
        self.set('r0',value);self.visited.add(self.pc);self.pc+=size;return True

    def step(self):
        if self.pc in self.else_skips:self.pc=self.else_skips.pop(self.pc)
        pc=self.pc;text,size,*_=self.program.code[pc];plain=text.removesuffix('  #')
        if pc==0x01c05d08:self.estimate_words.append((self.value('r0'),self.value('r1')))
        if pc==0x0202e3aa:self.type30_outputs.append((self.value('r4'),self.value('r0')))
        if pc in PARAMETER_JOINS|CREATION_JOINS:
            self.setup_sites.append((pc,(PARAMETER_JOINS|CREATION_JOINS)[pc]))
        if pc in self.program.blocked_incoming:
            target=self.program.blocked_incoming[pc]
            return self.external_call(target,SERVICES.get(target,1),size)
        if pc in self.program.setup_code or pc in self.program.ir_code:
            if match:=re.fullmatch(r'call (r\d+|-?\d+)',plain):
                indirect=match[1].startswith('r');target=self.value(match[1]) if indirect else pc+size+int(match[1])
                producer=indirect and pc==0x02031a00 and target in (0x02031542,0x020315b8)
                if not indirect or producer:
                    if target not in self.program.code:raise ValueError(f'unclosed setup call {pc:#x}/{target:#x}')
                    self.visited.add(pc);self.real_calls.append(target);self.returns.append(pc+size);self.pc=target
                    if producer:self.producer_calls.append((target,tuple(self.value(f'r{i}') for i in range(4))))
                    return True
                count=(INDIRECT_ARITIES|IR_INDIRECT).get(pc)
                if count is None:raise ValueError(f'unreviewed setup callback {pc:#x}')
                return self.external_call(target,count,size)
        if pc in self.program.ir_code and pc not in self.program.setup_code:
            if self.ir_view is None:self.ir_view=object.__new__(IrEffectNumericalMachine)
            view=self.ir_view;view.__dict__.update(self.__dict__)
            view.read=lambda a,n:EffectParametersMachine.read(view,a,n)
            view.write=lambda a,v,n:EffectParametersMachine.write(view,a,v,n)
            view.snapshot=lambda:EffectParametersMachine.snapshot(view)
            result=IrEffectNumericalMachine.step(view)
            for key,value in view.__dict__.items():
                if key not in ('read','write','snapshot','ir_view'):self.__dict__[key]=value
            return result
        return super().step()

    def single_step(self):
        text,size,*_=self.program.code[self.pc];plain=text.removesuffix('  #')
        if self.pc==0x01c060a4:
            index=self.value('r1')
            if index>=35:raise ValueError('stereo TBB index')
            self.visited.add(self.pc);self.pc=0x01c060a6+2*self.program.data['setup_stereo_branches'][index];return True
        return super().single_step()

    def run(self):
        try:result=super().run()
        except Exception as error:
            raise ValueError(f'{error}; setup PC {self.pc:#x}: {self.program.code.get(self.pc)}') from error
        result['setup_sites']=self.setup_sites
        result['estimate_words']=self.estimate_words
        result['type30_outputs']=self.type30_outputs
        if self.operation in VOID:result['value']=0;result['result']=(0,0)
        return result
