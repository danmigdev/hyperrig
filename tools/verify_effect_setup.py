"""Compare original setup instructions, native aliases and service ordering."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import re
import struct
from pathlib import Path
import verify_effect_parameter_construction as previous
import verify_ir_effect_numerical as ir
from verify_effect_parameter_lifecycle import Backend, Script
from verify_effect_parameters import U32,IO,setword,Backend as RawBackend
from effect_setup_machine import (EffectSetupProgram,REGIONS,REUSED,STATIC,ARITIES,
    ENTRY_POINTS,MAPPED,ROOT,region_bytes,PARAMETER_JOINS,CREATION_JOINS,AUXILIARY_STATIC)

PARENT='firmware/src/hyperrig_effect_parameter_construction.c'
PARENT_SHA='b337edb670dc6585e331eaf9c1550bc03ce3f1367f34c8ef297fd3cf36c73033'
SOURCE='firmware/src/hyperrig_effect_setup_parameters.c'
SOURCES=tuple(dict.fromkeys((*[p for p in previous.SOURCES if p!=PARENT],
    *ir.SOURCES,'firmware/src/hyperrig_preset_preflight.c',SOURCE,'firmware/src/hyperrig_effect_setup.c')))
BRIDGE='''/* SETUP_PARAMETER_BRIDGE_BEGIN
 * Five direct native cost/refresh sites; numeric callback tokens remain services. */
static uint32_t setup_direct(parameter_access *a,uint32_t entry,uint32_t first,uint32_t second)
{
    uint32_t p[12]={first,second},out[2]={0,0};int status;
    hyperrig_effect_setup_io io={borrowed_map,forward_service,a,a->services,a->work};
    if(a->error)return 0;
    status=hyperrig_effect_setup_execute(entry,p,out,&io);
    if(status&&!a->error)a->error=status;
    return out[0];
}
/* SETUP_PARAMETER_BRIDGE_END */

'''
SUBSTITUTIONS=(
    ('current=CALL2(a,0x02028cb2,slot,1);','current=setup_direct(a,0x02028cb2,slot,1);'),
    ('total=CALL0(a,0x02028de8);','total=setup_direct(a,0x02028de8,0,0);'),
    ('cost=CALL2(a,0x02028cb2,slot,1);','cost=setup_direct(a,0x02028cb2,slot,1);'),
    ('(void)CALL1(a,0x0202e328,effect);','(void)setup_direct(a,0x0202e328,effect,0);'))

def derivative(parent):
    if hashlib.sha256(parent.encode()).hexdigest()!=PARENT_SHA:raise ValueError('frozen construction parent changed')
    value=parent.replace('hyperrig_effect_parameter_construction','hyperrig_effect_setup_parameters')
    value=value.replace('#include "hyperrig/hyperrig_effect_setup_parameters.h"','#include "hyperrig/hyperrig_effect_setup.h"',1)
    value=value.replace('hyperrig_effect_setup_parameters_io','hyperrig_effect_setup_io')
    anchor='/* 0x0202f4e8: classify an unsigned word offset within one eleven-word section. */'
    if value.count(anchor)!=1:raise ValueError('setup bridge insertion anchor')
    value=value.replace(anchor,BRIDGE+anchor)
    for old,new in SUBSTITUTIONS:
        if value.count(old)!=(2 if old.startswith('total=') else 1):raise ValueError('setup direct substitution count')
        value=value.replace(old,new)
    return value

def check_derivative():
    if (ROOT/SOURCE).read_text()!=derivative((ROOT/PARENT).read_text()):raise ValueError('unchecked setup derivative change')
    return {'parent':PARENT,'parent_sha256':PARENT_SHA,'derived':SOURCE,
        'direct_sites':[{'site':f'0x{pc:08x}','target':f'0x{target:08x}'} for pc,target in PARAMETER_JOINS.items()],
        'permitted_changes':['public prefix/header','one borrowed bridge','five exact direct calls'],
        'prior_numerical_resource_ownership_sources_unchanged':True}

RAM=MAPPED[0][0];ARENA=MAPPED[2][0];EFFECTS=0x01c2c220;CONTROL=0x01c32db0;CFG=0x01c1f7f0
ALLOC,FREE,MODE,PROGRESS,QUERY,NOTICE=range(0x41001000,0x41001018,4)

def initial(kind=0):
    memory=[bytearray(n) for _,n in MAPPED]
    for address,value,width in ((CFG+8,48000,4),(CFG+12,1200,4),(CFG+20,24,4),
        (CONTROL+48,100000,4),(CONTROL+52,ALLOC,4),(CONTROL+56,FREE,4),
        (0x01c34458,MODE,4),(0x01c34194,0x0201a9dc,4),(EFFECTS,kind,1)):
        setword(memory,address,value,width)
    return memory

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectSetupProgram();self.lib=ctypes.CDLL(str(library.resolve()))
        for name in ('hyperrig_effect_setup_execute','hyperrig_effect_setup_parameters_execute'):
            getattr(self.lib,name).argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.counts={};self.coverage=set();self.steps=0;self.last=None;self.calls={};self.sites={};self.mutations=0
        self.replay=replay;self.replays=0;self.carried=0;self.services={};self.service_sites={};self.digest=hashlib.sha256()
        self.estimate_words=set();self.private=0;self.type30_outputs=set()
        if replay:
            replay.write(b'HRESET01');replay.write(struct.pack('<2I',0,len(self.program.static_regions)))
            for key,(a,b) in self.program.static_regions.items():
                replay.write(struct.pack('<2I',a,b-a));replay.write(self.program.data[key])
    def compare(self,label,memory,name,args=(),plan=None,mutations=(),carried=False):
        script=Script(plan,mutations)
        try:native=self.program.execute(memory,name,args,boundary=script)
        except Exception as error:raise AssertionError((label,'native',str(error))) from error
        backend=Backend(self.program,memory,Script(plan,mutations),native['calls']);out=(U32*2)(0xdeadbeef,0xcafebabe)
        backend.io.work=20000000
        function=self.lib.hyperrig_effect_setup_parameters_execute if name.startswith('parameter_') else self.lib.hyperrig_effect_setup_execute
        status=function(ENTRY_POINTS[name],(U32*12)(*args),out,ctypes.byref(backend.io))
        if status or backend.errors:raise AssertionError((label,'C',status,backend.errors))
        if tuple(out)!=native['result']:raise AssertionError((label,'result',tuple(map(hex,out)),tuple(map(hex,native['result']))))
        if backend.snapshot()!=native['memory']:
            changes=[(hex(base+i),x,y) for (base,_),a,b in zip(MAPPED,native['memory'],backend.snapshot())
                for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            raise AssertionError((label,'memory native/C',changes[:25]))
        if backend.calls!=native['calls']:raise AssertionError((label,'service snapshots differ',[(hex(x[0]),x[1][:6]) for x in native['calls']],[(hex(x[0]),x[1][:6]) for x in backend.calls]))
        if backend.sites!=[(t,n) for _,t,n in native['service_sites']]:raise AssertionError((label,'callback ABI'))
        self.counts[name]=self.counts.get(name,0)+1;self.coverage|=native['visited'];self.steps+=native['steps'];self.last=native
        self.mutations+=bool(mutations)
        for target in native['real_calls']:self.calls[target]=self.calls.get(target,0)+1
        for site,target in native['setup_sites']:self.sites[site]=self.sites.get(site,0)+1
        self.carried+=bool(carried);self.estimate_words.update(native['estimate_words']);self.private+=len(native['private_events'])
        self.type30_outputs.update(native['type30_outputs'])
        for pc,target,count in native['service_sites']:
            self.services[target]=self.services.get(target,0)+1
            key=(pc,target,count);self.service_sites[key]=self.service_sites.get(key,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*out))
        for data in native['memory']:self.digest.update(data)
        for target,words,before,after,p0,p1 in native['calls']:
            self.digest.update(struct.pack('<13I',target,*words))
            for data in (*before,*after):self.digest.update(data)
            for a,data in (*p0,*p1):self.digest.update(struct.pack('<I',a));self.digest.update(data)
        if self.replay:self.write_replay(memory,name,args,native,script.responses);self.replays+=1
        return list(map(bytearray,native['memory']))

    def write_replay(self,memory,name,args,native,responses):
        f=self.replay
        f.write(struct.pack('<17I',int(name.startswith('parameter_')),ENTRY_POINTS[name],
            *(tuple(args)+(0,)*(12-len(args))),*native['result'],len(native['calls'])))
        for data in memory:write_sparse(f,data)
        for (_,_,count),call,value in zip(native['service_sites'],native['calls'],responses):
            target,words,before,after,p0,p1=call;changes=[]
            for (base,_),a,b in zip(MAPPED,before,after):
                changes.extend((base+i,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y)
            for base,data in p1:changes.extend((base+i,x) for i,x in enumerate(data))
            f.write(struct.pack('<18I',target,count,*words,value,len(changes),len(p0),
                int.from_bytes(p0[0][1],'little') if p0 else 0))
            for a,v in changes:f.write(struct.pack('<IB',a,v))
        for data in native['memory']:write_sparse(f,data)

def write_sparse(stream,data):
    ranges=[]
    for m in re.finditer(rb'[^\x00]+',data):
        if ranges and m.start()-ranges[-1][1]<=16:ranges[-1][1]=m.end()
        else:ranges.append([m.start(),m.end()])
    stream.write(struct.pack('<I',len(ranges)))
    for a,b in ranges:stream.write(struct.pack('<2I',a,b-a));stream.write(data[a:b])

def smoke(c):
    for name,args in [('tempo',(1200,)),('create',(0,0,1)),('create_disabled',(1,0,2)),
        ('demand_by_type',(33,0,0)),('layout29',(0,1)),('initialize30',(ARENA,EFFECTS+70)),
        ('initialize29',(ARENA,))]:
        c.compare('smoke '+name,initial(),name,args,{ALLOC:ARENA})

def helpers(c):
    names=('has_mode','default_mode','base_cost','type_cost','stereo_extra_cost','object_count','object_extra')
    for kind in range(40):
        m=initial(kind)
        for name in names:c.compare(f'{name}/{kind}',m,name,(kind,))
        for mode in (0,1,2,3,31,0xffffffff):
            for name in ('mode_cost','group_eligible','group_fixed'):c.compare(f'{name}/{kind}/{mode}',m,name,(kind,mode))
        c.compare(f'demand {kind}',m,'demand',(EFFECTS,))
    for value in (0,1,2,3,0x7fffffff,0x80000000,0xffffffff):
        c.compare(f'next mode {value}',initial(),'next_mode',(value,))
        c.compare(f'saturate {value}',initial(),'saturating_double',(value,))
        c.compare(f'IR fallback {value}',initial(),'ir_fallback_cost',(value,))
        for enabled in (0,1):c.compare(f'IR partitions {value}/{enabled}',initial(),'ir_partition_cost',(value,enabled))
    for kind in (27,31,32,33,34,35):
        m=initial(kind);n=13 if kind==33 else 3 if kind==34 else 20
        for index in range(n):
            for name in ('object_segment','segment_bytes'):c.compare(f'{name}/{kind}/{index}',m,name,(kind,index))
        c.compare(f'object total {kind}',m,'object_total',(kind,))
        c.compare(f'parts {kind}',m,'partition_sizes',(kind,1,ARENA,ARENA+512))
    for kind in (5,27,31,32,33,35):
        m=initial(kind)
        for flag in (0,1,2,0x80000000,0xffffffff):
            c.compare(f'forwarded estimate word {kind}/{flag}',m,'estimate_slot',(EFFECTS,flag))
            c.compare(f'forwarded slot word {kind}/{flag}',m,'slot_cost',(0,flag))

def create_cases(c):
    for kind in range(1,40):
        for chain in (0,1):
            m=initial();setword(m,0x01c343c4,PROGRESS)
            c.compare(f'create {kind}/{chain}',m,'create',(chain,0,kind),{ALLOC:ARENA})

def helper_edges(c):
    for mode in (0,1,2,0xffffffff):
        for pointer in (0,ARENA):c.compare('layout pointer/mode',initial(),'layout29',(pointer,mode))
    for mask in (0,1,3,7,15,16,17,31,255):
        m=initial();setword(m,CONTROL+6,mask,1)
        c.compare('pool exact mask',m,'pool_claim');c.compare('pool full mask',m,'pool_full')
    for kind in range(40):
        for extra in (0,1):
            for alias in (0,1):c.compare('partition output alias',initial(kind),'partition_sizes',
                (kind,extra,ARENA,ARENA if alias else ARENA+256))
    for n in (0,1,2,3,20,31,32,33,63,0xffffffff):
        for mask in (0,1,0xaaaaaaaa,0xffffffff):
            for capacity in (0,100,0x80000000,0xffffffff):
                m=initial()
                for i in range(63):setword(m,ARENA+4*i,(i*13+7) if i%3 else 0xffffff00)
                c.compare('greedy mask and wrapped sum',m,'partition_pack',(ARENA,n,mask,capacity))
    for kind,indices in ((33,(13,14,15,20,0xffffffff,0xfffffffe,0xfffffffc)),(34,(3,4,5,6)),(27,(20,21,25,29))):
        for index in indices:
            c.compare('raw segment above caller count',initial(kind),'object_segment',(kind,index))
    for kind in (27,31,32,33,34,35):
        for mask in (0,1,15):
            m=initial(kind);setword(m,CONTROL+6,mask,1)
            for i in range(21):setword(m,ARENA+4*i,ARENA+1024+1024*i)
            c.compare('pool native pointer publication',m,'pool_attach',(EFFECTS,ARENA))
    for phase in (0,255,256,511,512,1023,0xffffffff):
        for alias in (0,1,2):
            m=initial()
            for i in range(1024):setword(m,ARENA+3020+4*i,(i*9999997)&0xffffffff)
            first=ARENA+7000 if not alias else ARENA+3020+4*(phase&1023)
            second=first if alias==2 else ARENA+7004
            c.compare('phase output aliases source or output',m,'phase_pair',(ARENA,phase,first,second))

def routing_cases(c):
    for chain in (0,1):
        for pattern in ((0,), (1,1,0,2,0,3),(1,0,1,0,1,0,1)):
            m=initial();setword(m,CONTROL+14+chain,len(pattern),1)
            for i,branch in enumerate(pattern):
                setword(m,CONTROL+348+10*chain+i,i,1);setword(m,EFFECTS+480*i+4,branch,1)
            for cache in (0,100,0xfffffff0):
                for i in range(3):setword(m,CONTROL+392+12*chain+4*i,cache)
                for flag in (0,1):
                    for i in range(6):setword(m,CONTROL+186+3*chain+i,flag,1)
                    c.compare('routing runs and cache',m,'route_cost',(chain,))
            for position in (0,1,len(pattern),255):c.compare('route shift insertion',m,'route_insert',(chain,position,15))
    for stereo in (0,1,2,0xffffffff):
        for mask in (0,0x70000,0x7000000,0xffffffff):
            for flags in (0,1):
                m=initial()
                for i in range(6):setword(m,CONTROL+189+i,flags,1)
                c.compare('branch masks',m,'branch_cost',(stereo,mask))
    for which in (0,1):
        for n in range(6):
            for cached in (0,1234,0xfffffff0):
                m=initial();setword(m,CONTROL+24,cached)
                for i in range(5):
                    setword(m,CONTROL+164+i,which,1);setword(m,(0x01c33240 if which else 0x01c33320)+44*i+40,int(i<n),1)
                c.compare('filter selection and cost',m,'filter_cost')
    for kind in (5,27,31,32,33,35):
        observed=[]
        for enabled in (0,1,2,255):
            m=initial(kind);setword(m,EFFECTS+1,enabled,1);setword(m,EFFECTS+2,1,1);setword(m,EFFECTS+8,1,2)
            c.compare('total forwards stored enable byte',m,'total_cost');observed.append(c.last['value'])
            assert (EFFECTS,enabled) in c.last['estimate_words']
        assert observed[0]!=observed[1] and len(set(observed[1:]))==1
        # The progress callback writes this live flag before create computes
        # total cost. Both executions must forward the newly stored word.
        m=initial(kind);setword(m,EFFECTS+2,1,1);setword(m,EFFECTS+8,1,2);setword(m,0x01c343c4,PROGRESS)
        c.compare('earlier callback changes forwarded estimate',m,'create',(0,0,1),{ALLOC:ARENA},
            ((PROGRESS,0,EFFECTS+1,7,1),))
        assert (EFFECTS,7) in c.last['estimate_words']
    for kind in (5,27,31):
        for cache in (0,1,3000,0xfffffff0):
            for mode in (0,3):
                m=initial(kind);setword(m,0x01c343d8,cache);setword(m,EFFECTS+6,mode,1)
                for flag in (0,1):c.compare('slot cache versus actual',m,'slot_cost',(0,flag))

def allocation_cases(c):
    for kind in (5,25,27,29,30,31,32,33,34,35,39):
        m=initial(kind);setword(m,EFFECTS+82,1,2)
        c.compare('derive allocation demand',m,'demand',(EFFECTS,));capacity=c.last['value']
        for plan in ((ARENA,), (0,), (0,ARENA), (0,ARENA,ARENA+65536)):
            for query in (0,8192+24,65536):
                mm=list(map(bytearray,m));setword(mm,0x01c343d4,QUERY);setword(mm,0x01c34434,NOTICE)
                c.compare('allocator split/retry/rollback',mm,'allocate',(EFFECTS,capacity),{ALLOC:plan,QUERY:query})
    for kind in (29,30):
        for present in (0,1):
            for split in (0,1):
                for capacity in (0,10203,10204,32335,32336,0x80000000):
                    m=initial(kind);setword(m,EFFECTS+82,1,2);setword(m,EFFECTS+84,ARENA if present else 0)
                    setword(m,EFFECTS+88,capacity);setword(m,EFFECTS+7,split,1);setword(m,EFFECTS+92,ARENA+8192)
                    c.compare('pre-existing refresh pointer/length',m,'refresh29' if kind==29 else 'refresh30',(EFFECTS,))
    for offset in (0,70,200):
        m=initial(30)
        for i in range(7):setword(m,ARENA+offset+2*i,100+i,2)
        c.compare('type30 clears aliased parameters before reads',m,'initialize30',(ARENA,ARENA+offset))

def neighbor_cases(c):
    for chain in (0,1):
        for kinds in ((9,9,9),(3,9,9),(9,3,9),(1,9,9),(9,1,9)):
            for enabled in (0,1,2,4,7):
                for branch_mask in (0,7,5):
                    m=initial();setword(m,CONTROL+14+chain,3,1)
                    for i,kind in enumerate(kinds):
                        e=EFFECTS+480*i;setword(m,CONTROL+348+10*chain+i,i,1)
                        for off,value in ((0,kind),(1,(enabled>>i)&1),(4,(branch_mask>>i)&1),(6,1)):
                            setword(m,e+off,value,1)
                    for left,right in ((0xffffffff,0),(0,1),(1,2),(2,3)):
                        c.compare('six-word neighboring route',m,'neighbor_group',(chain,left,right,1,9,1))
                    for position in (0,1,2,3,0xffffffff):
                        c.compare('insertion group and branch decision',m,'insertion_cost',(chain,position,9,1))
    for mode in (0,2,3):
        c.compare('neighbor eligibility mode',initial(),'neighbor_group',(0,0xffffffff,0,0,9,mode))

def creation_edges(c):
    for chain,kind in ((2,1),(0,0),(0,40),(0,0xffffffff),(0xffffffff,1)):
        c.compare('creation validation side effects',initial(),'create',(chain,0,kind))
    for occupied,length in ((0,10),(16,0),(15,0),(0,9)):
        m=initial();setword(m,CONTROL+14,length,1)
        for i in range(occupied):setword(m,EFFECTS+480*i+2,1,1)
        c.compare('creation slot or chain limits',m,'create',(0,0xffffffff,1))
    for kind in (1,3,7,9,29,31,39):
        for limit in (0,100,1875,5000,100000,0xffffffff):
            for disabled in (False,True):
                m=initial();setword(m,CONTROL+48,limit);setword(m,CONTROL+6,15,1)
                c.compare('admission and disabled creation',m,'create_disabled' if disabled else 'create',
                    (1,0,kind),{ALLOC:ARENA})
    for kind in (5,29,30,31):
        for failure in (False,True):
            m=initial();setword(m,0x01c343c4,PROGRESS)
            c.compare('creation mode and allocation result',m,'create',(0,0,kind),{ALLOC:0 if failure else ARENA})
    for chain in (0,1):
        m=initial();setword(m,CFG,1,1)
        for kind in (5,11,15,27,29,30,34,39):
            c.compare('stereo creation admission cost',m,'create',(chain,0,kind),{ALLOC:ARENA})

def mutation_cases(c):
    # The progress token is reread at every site. Cached type, slot and phase
    # remain caller values while later public fields observe these writes.
    changes=((PROGRESS,0,CONTROL+48,0,4),(PROGRESS,0,CONTROL+84,1,1),
        (PROGRESS,1,EFFECTS+70,777,2),(PROGRESS,2,EFFECTS+1,7,1),
        (PROGRESS,3,EFFECTS,30,1),(PROGRESS,3,EFFECTS+82,1,2),
        (PROGRESS,4,EFFECTS+84,ARENA+1024,4),(PROGRESS,5,EFFECTS+7,0,1),
        (PROGRESS,6,CONTROL+14,2,1),(PROGRESS,0,0x01c343c4,0,4))
    for change in changes:
        m=initial();setword(m,0x01c343c4,PROGRESS)
        c.compare('progress cached/local versus mutable fields',m,'create',(0,0,29),{ALLOC:ARENA},(change,))
    # A callback may overwrite the published pointer/capacity or type. The
    # allocator computes its original local partition layout before callbacks.
    for kind in (5,29,30,31):
        for address,value,width in ((EFFECTS+84,ARENA+65536,4),(EFFECTS+88,1,4),
            (EFFECTS+5,9,1),(EFFECTS+82,0,2)):
            m=initial(kind);setword(m,EFFECTS+82,1,2);setword(m,0x01c34194,PROGRESS)
            c.compare('clear callback mutates publication fields',m,'allocate',(EFFECTS,32336),
                {ALLOC:ARENA},((PROGRESS,0,address,value,width),))
    for target in (0x0202e710,0x0202e4c2,0x0202f46c,0x0202f07e,0x0202cf62,0x01c05d02):
        for role,address in (('progress',0x01c343c4),('allocation',CONTROL+52),('mode',0x01c34458),('clear',0x01c34194)):
            m=initial();setword(m,address,target)
            c.compare('callback token collision '+role,m,'create',(0,0,5),{ALLOC:ARENA,target:ARENA if role=='allocation' else 0})
            assert any(t==target for _,t,_ in c.last['service_sites'])
    for target in (0x0202e4c2,0x0202f46c):
        m=initial(29);setword(m,EFFECTS+82,1,2);setword(m,0x01c343d4,target);setword(m,0x01c34434,target)
        c.compare('zero-word query and one-word notice collision',m,'allocate',(EFFECTS,32336),{ALLOC:0,target:0})

def parameter_cases(c):
    for kind in (1,5,11,13,15,16,25,29,30,31,33,34):
        m=previous.fixture(kind);setword(m,CFG+12,1200);setword(m,0x01c343d8,0)
        for name,args in (('parameter_probe',(0,0,35)),('parameter_commit',(0,0,35)),('parameter_fast',(0,0,35,5))):
            c.compare('real parameter setup cost/refresh',m,name,args,{previous.ALLOCATOR:ARENA+65536})
    for kind in (5,11,12,13,15):
        base=initial();setword(base,CFG+8,4800)
        base=c.compare('create actual state before tempo',base,'create',(0,0,kind),{ALLOC:ARENA})
        for identifier in (0,1,9,10,12,0xffff):
            m=list(map(bytearray,base));setword(m,CFG+12,1200)
            index=4 if kind==5 else {11:3,12:4,13:3,15:2}[kind]
            setword(m,EFFECTS+70+2*index,identifier,2)
            for desired in (0,399,400,1200,3000,3001,0x80000000,0xffffffff):
                c.compare(f'tempo actual parameter commit {kind}/{identifier}/{desired}',m,'tempo',(desired,),{ALLOC:ARENA+32768})
    m=initial()
    for i,(kind,offset) in enumerate(((1,0),(5,0),(29,32768),(30,40960),(31,65536))):
        m=c.compare('retained creations',m,'create',(0,i,kind),{ALLOC:ARENA+offset},carried=i!=0)
    c.compare('retained created total cost',m,'total_cost',carried=True)

def closing_cases(c):
    for selector in (0,1,2,3,0xffffffff):
        m=initial()
        for i in range(5):setword(m,EFFECTS+84+4*i,0x100+i)
        c.compare('raw selector wrapped address',m,'buffer_selector',(EFFECTS,selector))
    m=initial();setword(m,0x01c33320+44+40,1,1)
    c.compare('active filters with first disabled',m,'filter_cost')
    for query in ((56496,8208),(56496,0)):
        m=initial(29);setword(m,EFFECTS+82,1,2);setword(m,0x01c343d4,QUERY)
        c.compare('rotated split type29 and later empty query',m,'allocate',(EFFECTS,32336),
            {ALLOC:(0,ARENA,ARENA+65536),QUERY:query})
    for kind in (27,31,32,33,34,35):
        m=initial(kind)
        after=c.compare('derive multi-part allocation fixture',m,'partition_sizes',(kind,1,ARENA,ARENA+512))
        n=c.last['value'];sizes=list(struct.unpack_from('<'+str(n)+'I',after[2]));overhead=struct.unpack_from('<I',after[2],512)[0]
        remaining=set(range(n));queries=[]
        for _ in range(2):
            capacity=max(sizes[i] for i in remaining);queries.append(capacity+16+overhead);total=0
            while True:
                fitting=[i for i in remaining if sizes[i]+total<=capacity]
                if not fitting:break
                chosen=max(fitting,key=lambda i:(sizes[i],-i));remaining.remove(chosen);total+=sizes[chosen]
            if not remaining:break
        if remaining:queries.append(sum(sizes[i] for i in remaining)+16+overhead)
        setword(m,0x01c343d4,QUERY)
        c.compare('three allocations rotate all native selectors',m,'allocate',(EFFECTS,40000),
            {ALLOC:(0,ARENA,ARENA+50000,ARENA+85000),QUERY:tuple(queries)})
    source=MAPPED[1][0];reader=0x41001018
    for accelerated in (0,1):
        for stored in (False,True):
            for returned in (0,ARENA):
                for disabled in (False,True):
                    m=initial()
                    for a,v,n in ((CONTROL+60,0 if stored else source,4),(CONTROL+64,16,4),(CONTROL+68,1,4),
                        (CONTROL+72,1 if stored else 0,4),(0x01c3441c,reader,4),(0x01c1f7d0,accelerated,4),
                        (0x01c1fa14,1,4),(0x01c1f7dc,0x3f800000,4)):
                        setword(m,a,v,n)
                    setword(m,source,32767,2)
                    plan={ALLOC:(returned,returned+16384) if returned and stored else returned}
                    change=((reader,0,ARENA,32767,2),) if stored and returned else ()
                    c.compare('actual IR creation preparation/status/override',m,
                        'create_disabled' if disabled else 'create',(0,0,7),plan,change)
    for stored,readable in ((0,0),(1,0)):
        m=initial();setword(m,CONTROL+64,16);setword(m,CONTROL+72,stored);setword(m,0x01c3441c,readable)
        c.compare('IR source readiness gates',m,'create_disabled',(0,0,7))
    for split in (0,1):
        m=initial(29)
        for a,v,n in ((EFFECTS+1,1,1),(EFFECTS+2,1,1),(EFFECTS+84,ARENA,4),
            (EFFECTS+88,32336 if not split else 4096,4),(EFFECTS+7,split,1),(EFFECTS+92,ARENA+8192,4)):
            setword(m,a,v,n)
        c.compare('actual parameter temporary extra-object refresh',m,'parameter_commit',(0,6,1))
        assert 0x0202f338 in dict(c.last['setup_sites'])
    base=initial();setword(base,CFG+8,4800)
    base=c.compare('create live delay for tempo mutations',base,'create',(0,0,5),{ALLOC:ARENA})
    setword(base,EFFECTS+78,1,2)
    for change in ((MODE,0,CFG+12,777,4),(MODE,0,EFFECTS+2,0,1),(ALLOC,0,EFFECTS,11,1)):
        c.compare('tempo reload after actual allocation callback',base,'tempo',(400,),{ALLOC:ARENA+32768},(change,))

def final_join_cases(c):
    for kind in (5,11,14,15,25):
        for index in range(7):
            for value in (0,1,2,0xffffffff):
                m=initial(kind)
                for a,v,n in ((EFFECTS+1,1,1),(EFFECTS+2,1,1),(CFG,100,1),
                    (CONTROL+36,0xffff,4),(CONTROL+40,0xffff,4),(CONTROL+44,0xffff,4),(CONTROL+48,6000,4)):
                    setword(m,a,v,n)
                c.compare('probe reaches both real cost joins',m,'parameter_probe',(0,index,value))
    for kind in (27,31,33,34):
        for offset in (0,80,160):
            m=initial(kind)
            for i in range(222):setword(m,0x01c2fa38+4*i,0xa5000000+i)
            c.compare('claimed pool aliases input pointer array',m,'pool_attach',(EFFECTS,0x01c2fa38+offset))

PARTS={'smoke':smoke,'helpers':helpers,'helper_edges':helper_edges,'routing':routing_cases,
       'create':create_cases,'allocation':allocation_cases,'neighbors':neighbor_cases,
       'creation_edges':creation_edges,'mutations':mutation_cases,'parameters':parameter_cases,
       'closing':closing_cases,'final_joins':final_join_cases}

def source_paths():
    paths=set(previous.source_paths())|set(ir.source_paths())|set(SOURCES)|{
        PARENT,SOURCE,'tools/effect_setup_machine.py','tools/verify_effect_setup.py',
        'tools/build_effect_setup.py','tests/test_effect_setup_machine.py','tests/effect_setup_sanitize.c'}
    pending=[ROOT/path for path in SOURCES];seen=set()
    while pending:
        p=pending.pop().resolve()
        if p in seen:continue
        seen.add(p)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',p.read_text(),re.M):
            for child in (p.parent/name,ROOT/'firmware/include'/name):
                if child.is_file():
                    child=child.resolve();paths.add(child.relative_to(ROOT).as_posix());pending.append(child);break
    return sorted(paths)

def api_checks(c):
    checks=0;out=(U32*2)(0xdeadbeef,0xcafebabe);execute=c.lib.hyperrig_effect_setup_execute
    b=RawBackend(c.program,initial(),Script());args=(U32*12)(0)
    for entry,p,result,io in ((0,args,out,None),(0,None,out,ctypes.byref(b.io)),(0,args,None,ctypes.byref(b.io)),(0,args,out,ctypes.byref(b.io))):
        assert execute(entry,p,result,io)==-200;checks+=1
    for name,args,expected in (('phase_pair',(0x30000000,0,ARENA,ARENA+4),-202),
        ('initialize30',(0x31005000,EFFECTS+70),-202),('initialize30',(0xfffffffd,EFFECTS+70),-201),
        ('refresh29',(0x40000000,),-201)):
        b=RawBackend(c.program,initial(),Script());status=execute(ENTRY_POINTS[name],(U32*12)(*args),out,ctypes.byref(b.io))
        assert status==expected,(name,status,expected);assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    for work in (0,1,16,100,1000,20000):
        b=RawBackend(c.program,initial(),Script());b.io.work=work
        assert execute(ENTRY_POINTS['initialize29'],(U32*12)(ARENA),out,ctypes.byref(b.io))==-203
        assert tuple(out)==(0xdeadbeef,0xcafebabe);checks+=1
    class Missing(RawBackend):
        def map(self,opaque,address,size,writable):
            if writable and address==ARENA+12 and size==4:return None
            return super().map(opaque,address,size,writable)
    m=initial();m[2][:32]=bytes([0x55])*32;b=Missing(c.program,m,Script())
    assert execute(ENTRY_POINTS['initialize30'],(U32*12)(ARENA,EFFECTS+70),out,ctypes.byref(b.io))==-201
    assert b.snapshot()[2][:16]==bytes(12)+bytes([0x55])*4;checks+=1
    # Mutation to a larger type must not read uninitialized original private
    # partition pointers. Earlier pool/header writes remain visible.
    m=initial(30);setword(m,0x01c34194,PROGRESS)
    b=RawBackend(c.program,m,Script({ALLOC:ARENA},((PROGRESS,0,EFFECTS,31,1),)))
    assert execute(ENTRY_POINTS['allocate'],(U32*12)(EFFECTS,10204),out,ctypes.byref(b.io))==-202
    assert b.read(EFFECTS+288,4)==0x01c2fa38 and b.read(CONTROL+6,1)==1;checks+=1
    return checks

TABLE_PROOFS={
    'stereo_branches':{'consumers':{'stereo_extra_cost':REGIONS['stereo_extra_cost']},
        'sites':(0x01c06098,0x01c0609c,0x01c060a0,0x01c060a4),
        'rule':'Unsigned type-5 <= 34; byte offsets select base 01c060a6 plus twice the byte.'},
    'stereo_alignment':{'consumers':{'stereo_extra_cost':REGIONS['stereo_extra_cost']},
        'sites':(0x01c060a4,0x01c060ca),
        'rule':'One zero alignment byte after exactly 35 TBB bytes and before the first instruction target.'},
    'group_flags':{'consumers':{'group_fixed':REGIONS['group_fixed']},
        'sites':(0x01c0606e,0x01c06072,0x01c06074,0x01c06078,0x01c0607e),
        'rule':'Mode equals 1; unsigned type-9 <= 14; one word at base plus 4*(type-9).'},
    'object1_short_lengths':{'consumers':{'object_mode':(0x01c05ed6,0x01c05eec),
        'object_count':REGIONS['object_count'],'object_segment':REGIONS['object_segment'],
        'partition_sizes':REGIONS['partition_sizes'],'object_total':REGIONS['object_total'],'segment_bytes':REGIONS['segment_bytes']},
        'sites':(0x01c05ed6,0x01c05edc,0x01c05ee0,0x01c05ee4,0x01c05ee8,0x02029c22,0x02029c24,0x02029c2c,0x02029c34,
            0x02029f0a,0x02029f0e,0x02029f12,0x02029f16,0x02029f1a,0x02029f1e,
            0x02029f20,0x02029f24,0x02029f26,0x02029f2c,0x0202a1f4,0x0202a1fe,0x0202a202,0x0202a20a,0x0202a20c,
            0x02029fa6,0x02029fb4,0x02029fba,0x02029fbe,0x02029fc2,0x02029f90),
        'rule':'Object mode 1 is type 33 with 13 segments. Indices 9..12 select four halfwords at base 0203b4ae with stride 2; 0203b4b6..0203b4b8 remains unclassified.'}}

def report(c,guards,mini_image):
    from hyperrig.jieli import unpack_app
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()==previous.PINNED and hashlib.sha256(app).hexdigest()==previous.DECODED
    assert unpack_app(original)[2]['app.bin']==app
    code=c.program.code;new=c.program.new_code
    assert set(c.sites)==set(PARAMETER_JOINS|CREATION_JOINS),'all ten explicit direct joins must execute'
    windows={hex(pc):{'start':pc,'end_exclusive':pc+item[1],
        'sha256':hashlib.sha256(region_bytes(app,pc,pc+item[1])).hexdigest()} for pc,item in sorted(code.items())}
    static={name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(c.program.data[name]).hexdigest()}
        for name,(a,b) in c.program.static_regions.items()}
    def bodies(regions):
        return {name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.coverage),
            'unvisited':[pc for pc in sorted(code) if a<=pc<b and pc not in c.coverage]} for name,(a,b) in regions.items()}
    proofs={}
    for name,info in TABLE_PROOFS.items():
        a,b=STATIC[name];proofs[name]={'start':a,'end_exclusive':b,'sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'consumers':bodies(info['consumers']),'rule':info['rule'],'decoded_sites':[
                {'address':pc,'text':code[pc][0],'bytes_sha256':windows[hex(pc)]['sha256']} for pc in info['sites']]}
    binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==previous.MINI;body=unpack_app(raw)[2]['app.bin']
        for item in (*windows.values(),*static.values()):
            a,b=item['start'],item['end_exclusive'];assert region_bytes(body,a,b)==region_bytes(app,a,b),hex(a)
        binding={'image_sha256':previous.MINI,'identical_instruction_windows':len(windows),'identical_static_windows':len(static)}
    joined={pc for pc in code if any(a<=pc<b for a,b in (REGIONS|REUSED).values())}
    observations=sorted(c.type30_outputs)
    assert len(observations)==256 and [i for i,_ in observations]==list(range(256))
    assert all(0<=word<0x3f800000 for _,word in observations)
    missing_classification={}
    for pc in sorted(new-c.coverage):
        missing_classification[hex(pc)]={'kind':'fixed-input unreachable' if pc==0x0202e3b6 else 'not exercised',
            'reason':('The initializer visits all 256 constant indices; every observed original sine result is below 1.0. '
                'The argument sequence and recovered pure sine body do not depend on mapped state or callbacks, so the positive saturation assignment cannot execute.'
                if pc==0x0202e3b6 else 'This corpus has not executed the instruction; no runtime coverage is claimed.')}
    return {'schema':1,'project':'HyperRig','component':'reconstructed-effect-setup','result':'pass',
        'original_image_sha256':previous.PINNED,'decoded_image_sha256':previous.DECODED,
        'functions':bodies(REGIONS),'reused_functions':bodies(REUSED),
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.coverage),'unvisited_new':sorted(new-c.coverage),
            'joined_decoded':len(joined),'joined_visited':len(joined&c.coverage),'unvisited_joined':sorted(joined-c.coverage),
            'all_decoded':len(code),'all_visited':len(c.coverage),'unvisited_all':sorted(set(code)-c.coverage)},
        'derivative_provenance':check_derivative(),'static_data':static,'new_table_proofs':proofs,
        'auxiliary_raw_read_bindings':{name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'inventory_data_exclusion':False} for name,(a,b) in AUXILIARY_STATIC.items()},
        'bound_instruction_windows':windows,'mini_v4_binding':binding,
        'missing_classification':missing_classification,
        'type30_fixed_sine_observations':{'pc':0x0202e3aa,'index_register':'r4','value_register':'r0',
            'pairs':observations,'sha256':hashlib.sha256(b''.join(struct.pack('<2I',*x) for x in observations)).hexdigest()},
        'total_comparisons':sum(c.counts.values()),'comparisons':c.counts,'original_instruction_steps':c.steps,
        'direct_setup_sites':[{'site':pc,'target':(PARAMETER_JOINS|CREATION_JOINS)[pc],'calls':count} for pc,count in sorted(c.sites.items())],
        'actual_calls':{hex(k):v for k,v in sorted(c.calls.items())},
        'external_call_sites':[{'pc':pc,'target':target,'argument_words':n,'calls':count} for (pc,target,n),count in sorted(c.service_sites.items())],
        'external_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'estimate_slot_forwarded_words':sorted(c.estimate_words),'carried_calls':c.carried,'callback_mutation_cases':c.mutations,
        'native_private_flag_lifetimes':c.private,'c_only_guard_checks':guards,'sanitizer_replay_cases':c.replays,
        'outputs_state_services_sha256':c.digest.hexdigest(),'hardware_test':False,'audio_test':False,'flashable':False,
        'limitations':['Only the 45 declared complete setup bodies are newly reconstructed; inherited regions are not counted again.',
            'Allocation, release, progress, query, mode and other platform callbacks remain explicit by call site, including target collisions.',
            'Nested portable work caps and mapped-access charges are not original timing or one unified arithmetic-operation counter.',
            'Raw segment and partition helpers retain unbounded native arguments, signed tests and modulo-32 register-bit indexing; map/work guards remain portable boundaries.',
            'A callback type change cannot consume uninitialized original private partition-pointer entries; the portable guard retains prior writes.',
            'All arbitrary mapping/work/domain guards are C-only checks unless stated otherwise; stopped calls cannot resume.',
            'Outer preset application, hardware scheduling, device behavior and audio are not tested.']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--part',choices=tuple(PARTS)+('all',),default='all');parser.add_argument('--output',type=Path)
    parser.add_argument('--sanitizer-corpus',type=Path);parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args()
    if args.output and (args.output.exists() or args.part!='all'):parser.error('final report requires every corpus and a fresh output')
    check_derivative();replay=args.sanitizer_corpus.open('xb') if args.sanitizer_corpus else None;c=Corpus(args.library,replay)
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths()} if args.output else {}
    for name,fn in PARTS.items():
        if args.part in (name,'all'):fn(c);print(name,sum(c.counts.values()),flush=True)
    guards=api_checks(c)
    if replay:replay.seek(8);replay.write(struct.pack('<I',c.replays));replay.close()
    if args.output:
        result=report(c,guards,args.mini_image)
        assert sources=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'sources changed during comparison'
        result['source_sha256']=sources;result['library_sha256']=hashlib.sha256(args.library.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',sum(c.counts.values()),'comparisons',c.steps,'steps',len(c.coverage&c.program.new_code),'new instructions')
    print('Unvisited new:',[f'0x{x:08x}' for x in sorted(c.program.new_code-c.coverage)])

if __name__=='__main__':main()
