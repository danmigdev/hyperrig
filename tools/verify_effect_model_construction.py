"""Compare model-construction C with the original decoded instruction stream."""
from __future__ import annotations
import ctypes
import hashlib
import random
import struct
import re
import sys
from pathlib import Path
from effect_model_construction_machine import (
    EffectModelConstructionProgram, EffectModelConstructionMachine, REGIONS, REUSED, STATIC, MAPPED, ARITIES, ROOT, region_bytes)
from effect_construction_machine import REGIONS as PREVIOUS
from verify_effect_construction import SOURCES as PREVIOUS_SOURCES, initial as previous_initial
from verify_effect_construction import setword, EFFECT, CFG, ARENA, MAP, U32
from verify_effect_construction import PINNED,DECODED,MINI,digest,source_paths as previous_source_paths

SOURCES = (*PREVIOUS_SOURCES, 'firmware/src/hyperrig_effect_model_construction.c')
class IO(ctypes.Structure):
    _fields_ = [('map', MAP), ('opaque', ctypes.c_void_p), ('work', U32)]

def initial(type_=16, seed=0):
    memory = previous_initial(type_, seed)
    setword(memory, CFG+36, 48000)
    setword(memory, EFFECT+288, ARENA+8192)
    for i, value in enumerate((50, 50, 50, 50, 50, 50, 0)):
        setword(memory, EFFECT+70+2*i, value, 2)
    return memory

class Backend:
    def __init__(self, program, memory, alignment=0,holes=()):
        self.program=program;self.holes=holes
        self.allocations=[(ctypes.c_ubyte*(len(x)+alignment))() for x in memory]
        self.arrays=[]
        for allocation, data in zip(self.allocations, memory):
            array=(ctypes.c_ubyte*len(data)).from_address(ctypes.addressof(allocation)+alignment)
            array[:]=data;self.arrays.append(array)
        self.tables={name:(ctypes.c_ubyte*len(data)).from_buffer_copy(data)
                     for name,data in program.data.items()}
        self.io=IO(MAP(self.map),None,1000000)
    def map(self, opaque, address, size, writable):
        if any(address<b and address+size>a for a,b in self.holes):return None
        for (base,n),array in zip(MAPPED,self.arrays):
            if base<=address<=address+size<=base+n:return ctypes.addressof(array)+address-base
        if not writable:
            for name,(base,end) in self.program.static_regions.items():
                if base<=address<=address+size<=end:return ctypes.addressof(self.tables[name])+address-base
        return None
    def snapshot(self):return tuple(bytes(x) for x in self.arrays)

class Corpus:
    def __init__(self, library,fixtures=None):
        self.program=EffectModelConstructionProgram();self.library=ctypes.CDLL(str(Path(library).resolve()))
        self.execute=self.library.hyperrig_effect_model_construction_execute
        self.execute.argtypes=[U32,ctypes.POINTER(U32),ctypes.POINTER(U32),ctypes.POINTER(IO)]
        self.counts={};self.visited=set();self.steps=0;self.calls={};self.digest=hashlib.sha256();self.fixtures=fixtures
        self.replays=0;self.sparse_cases=0;self.carried=0;self.aliases=0;self.exp_max=0;self.extended_exp=0
        if fixtures:
            fixtures.write(b'EMOD0001');fixtures.write(struct.pack('<I',len(self.program.static_regions)))
            for name,(a,b) in self.program.static_regions.items():
                fixtures.write(struct.pack('<2I',a,b-a));fixtures.write(self.program.data[name])
    def compare(self,label,memory,name,args,alignment=0,holes=()):
        try:
            machine=EffectModelConstructionMachine(self.program,memory,name,args)
            read=machine.read
            def sparse_read(a,n):
                if any(a<end and a+n>start for start,end in holes):raise ValueError('original accessed unmapped coefficient word')
                return read(a,n)
            if holes:machine.read=sparse_read
            original=machine.run()
        except Exception as exc:raise AssertionError((label,'original',str(exc))) from exc
        backend=Backend(self.program,memory,alignment,holes);out=(U32*2)(0xdeadbeef,0xcafebabe)
        entry=PREVIOUS['construct'][0] if name=='construct' else REGIONS[name][0]
        status=self.execute(entry,(U32*12)(*args),out,ctypes.byref(backend.io))
        if status:raise AssertionError((label,'status',status))
        if tuple(out)!=original['result']:raise AssertionError((label,'result',tuple(out),original['result']))
        if backend.snapshot()!=original['memory']:
            changes=[(hex(base+i),x,y) for (base,_),a,b in zip(MAPPED,original['memory'],backend.snapshot())
                     for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            raise AssertionError((label,'memory',changes[:32]))
        if original['calls']:raise AssertionError((label,'unresolved numerical calls'))
        self.counts[name]=self.counts.get(name,0)+1;self.visited|=original['visited'];self.steps+=original['steps']
        self.sparse_cases+=bool(holes);self.carried+='carried' in label;self.aliases+='alias' in label
        self.exp_max=max(self.exp_max,max((x&0x7fffffff for x in original['exp_arguments']),default=0))
        self.extended_exp+=sum((x&0x7fffffff)>0x41800000 for x in original['exp_arguments'])
        for target in original['internal_calls']:self.calls[target]=self.calls.get(target,0)+1
        self.digest.update(label.encode());self.digest.update(struct.pack('<2I',*out))
        for data in original['memory']:self.digest.update(data)
        if self.fixtures:
            spans=[]
            for base,size in MAPPED:
                ranges=[(base,base+size)]
                for left,right in holes:
                    divided=[]
                    for a,b in ranges:
                        if left>=b or right<=a:divided.append((a,b))
                        else:
                            if a<left:divided.append((a,left))
                            if right<b:divided.append((right,b))
                    ranges=divided
                spans.extend((a,b-a)for a,b in ranges)
            f=self.fixtures;f.write(struct.pack('<17I',entry,alignment,len(spans),*(tuple(args)+(0,)*(12-len(args))),*out))
            for base,size in spans:
                index=next(i for i,(a,n)in enumerate(MAPPED)if a<=base<base+size<=a+n);offset=base-MAPPED[index][0]
                f.write(struct.pack('<2I',base,size));f.write(memory[index][offset:offset+size])
                f.write(original['memory'][index][offset:offset+size])
            self.replays+=1
        return original['memory']

def word(value):return value&0xffffffff
def floating(value):return struct.unpack('<I',struct.pack('<f',value))[0]

def helper_cases(c):
    rng=random.Random(0x49)
    edges=(0,1,2,3,4,7,8,9,31,63,99,100,255,32767,32768,65535,65536,0x7fffffff,0x80000000,0xffffffff)
    floating_edges=(0,0x80000000,1,0x80000001,0x7fffff,0x800000,0x807fffff,0x80800000,
        0x3f000000,0xbf000000,0x3f800000,0xbf800000,0x40000000,0x47800000,
        0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7f800001,0x7fc00000,0xff800001)
    for name in ('object_mode','object_record','percent','object_duration','object_limit'):
        for x in (*range(40),*edges):c.compare(f'{name}/{x}',initial(),name,(x,))
    for name in ('finite_clamp','square_root30'):
        for x in (*floating_edges,*(rng.getrandbits(32) for _ in range(50))):
            c.compare(f'{name}/{x:08x}',initial(),name,(x,))
    for x in (*edges,*(rng.getrandbits(32) for _ in range(60))):
        args=(x,*(rng.getrandbits(32) for _ in range(3)))
        c.compare(f'pitch curve/{x}',initial(),'pitch_curve',args)
    for i in range(80):
        m=initial();values=[rng.getrandbits(32) for _ in range(4)]
        for j,x in enumerate(values):setword(m,ARENA+4*j,x)
        args=(ARENA,rng.getrandbits(32),rng.getrandbits(32))
        c.compare(f'curve sample/{i}',m,'curve_sample',args,i%4)
    for i in range(90):
        a=rng.getrandbits(64);b=0 if i%10==0 else rng.getrandbits(64-i%32)
        c.compare(f'unsigned quotient/{i}',initial(),'unsigned_quotient',(word(a),a>>32,word(b),b>>32))
    for name in ('curve_setup','curve20_setup'):
        for i,x in enumerate(floating_edges):
            for doubled in (0,1):
                args=(EFFECT,i%4,x,doubled)+(tuple([i&1])if name=='curve20_setup'else())
                c.compare(f'{name}/{i}/{doubled}',initial(),name,args,i%4)
    for x in (*range(30),99,100,255,65521,0xffffffff):c.compare(f'odd length/{x}',initial(),'odd_length',(x,))
    for x in (-32768,-1201,-1200,-1,0,1,1200,1201,32767):
        c.compare(f'pitch ratio/{x}',initial(),'pitch_ratio',(word(x),))
    for x in (-32768,-20,-1,0,5,6,7,32767):c.compare(f'level exp/{x}',initial(),'level_exp',(word(x),))
    for rate in (1,20,48000,48077,96000):
        for x in (-100,0,.5,1,20,1000,20000,100000):
            m=initial();setword(m,CFG+36,rate)
            for name in ('pole_exp','pole_clamp'):c.compare(f'{name}/{rate}/{x}',m,name,(floating(x),))
    for x in edges:
        m=initial();setword(m,CFG+16,x);c.compare(f'pitch valid/{x}',m,'pitch_limit_valid',())
        setword(m,EFFECT+308,x);setword(m,EFFECT+400,rng.getrandbits(32))
        c.compare(f'pitch increment/{x}',m,'pitch_increment',(EFFECT,))
    for x in range(8):c.compare(f'object length/{x}',initial(),'object_length',(x,))
    for x in range(0,256,7):
        m=initial();setword(m,ARENA+56,x,1);c.compare(f'object extra/{x}',m,'object_extra',(ARENA,))
    for i in range(16):
        m=initial()
        for j in range(3):setword(m,ARENA+72+4*j,rng.getrandbits(32))
        destination=ARENA+64 if i&1 else ARENA+256;threshold=destination+4*(i%4)
        c.compare(f'curve state alias/{i}',m,'curve_state',(ARENA,destination,threshold),i%4)
    for table in range(3):
        for i,x in enumerate((0,.25,.5,1,2,-1)):
            args=(0x0203b6bc+28*table,floating(x),floating(.5),floating(.25),ARENA)
            c.compare(f'tone polynomial/{table}/{i}',initial(),'tone_polynomial',args,i%4)
    for i in range(8):
        m=initial();coefficients=(.25,1,.5,.25,.125,-.5,.25)if i%2 else(0,0,0,0,0,0,0)
        for j,x in enumerate(coefficients):setword(m,ARENA+4*j,floating(x))
        c.compare(f'frequency response/{i}',m,'frequency_response',(ARENA,floating(i*.125)))
        c.compare(f'tone response/{i}',m,'tone_response',(ARENA,))
    for i in range(16):
        args=(floating(200+i*100),floating(.1+i*.25),floating(.1+i*.1),floating(24000),floating(.5),ARENA,ARENA+(0 if i%2 else 4))
        c.compare(f'object filter/{i}',initial(),'object_filter',args,i%4)
        args=(args[0],args[1],args[3],i*7,i*7,floating(-3))
        c.compare(f'object feedback/{i}',initial(),'object_feedback',args)
        c.compare(f'object mix/{i}',initial(),'object_mix',(ARENA,word(i*10-20),word(-i)))

def builder_cases(c):
    rng=random.Random(0x57149)
    for type_ in (*range(16,24),25,29,39):
        name=f'build{type_}'
        for iteration in range(16):
            memory=initial(type_,iteration)
            parameters=[rng.randrange(101) for _ in range(7)]
            for i,value in enumerate(parameters):setword(memory,EFFECT+70+2*i,value,2)
            setword(memory,CFG+8,(48000,48077,96000,24000)[iteration%4])
            setword(memory,CFG+36,(48000,48077,96000,24000)[iteration%4])
            c.compare(f'{name}/{iteration}',memory,name,(EFFECT,),iteration%4)
    for type_ in (27,30,31,32,33,34,35):
        for iteration in range(12):
            memory=initial(type_,iteration)
            for i,value in enumerate([rng.randrange(101) for _ in range(7)]):setword(memory,EFFECT+70+2*i,value,2)
            object_=ARENA+8192
            for i in range(9):setword(memory,object_+80+4*i,rng.randrange(400,3000))
            setword(memory,object_+632,1 if type_==33 else 2 if type_==34 else 0,1)
            setword(memory,object_+628,iteration&1)
            name='object_mode'+str(1 if type_==33 else 2 if type_==34 else 0)
            c.compare(f'{name}/{type_}/{iteration}',memory,name,(EFFECT,object_),iteration%4)
            c.compare(f'object wrapper/{type_}/{iteration}',memory,'build_object',(EFFECT,),iteration%4)
    for level in (-20,0,50,99,100,120):
        for shape in (0,50,100):
            memory=initial()
            for i,value in enumerate((level,shape,50)):setword(memory,EFFECT+70+2*i,value,2)
            c.compare(f'signature/{level}/{shape}',memory,'build_signature',(ARENA+8192,EFFECT+70))

def integration_cases(c):
    types=(*range(16,24),25,27,29,30,31,32,33,34,35,39)
    for type_ in types:
        memory=initial(type_)
        object_=ARENA+8192
        setword(memory,object_+632,1 if type_==33 else 2 if type_==34 else 0,1)
        for i in range(9):setword(memory,object_+80+4*i,3000)
        if type_==30:setword(memory,ARENA,0x53525631)
        for step in range(4):
            memory=[bytearray(x) for x in memory]
            for i,value in enumerate((10+step*20,20+step*10,30+step*5,40+step*5,50,step,0)):
                setword(memory,EFFECT+70+2*i,value,2)
            setword(memory,EFFECT+6,(0,1,4,0)[step],1)
            memory=c.compare(f'carried constructor/{type_}/{step}',memory,'construct',(EFFECT,),step)
    for type_ in (*range(16,24),0,15,24,255):
        c.compare(f'dispatch/{type_}',initial(type_),'build16_to23',(EFFECT,))
    for mode,type_ in ((0,27),(0,31),(0,32),(0,35),(1,33),(2,34)):
        for delta in (-200,64):
            memory=initial(type_);object_=EFFECT+delta
            setword(memory,EFFECT+288,object_);setword(memory,object_+628,0)
            setword(memory,object_+632,mode,1)
            c.compare(f'object input alias/{type_}/{delta}',memory,'build_object',(EFFECT,),1)
    for offset in (0,4,8):
        memory=initial();parameters=ARENA+8192+17328+offset
        for i,x in enumerate((50,50,50)):setword(memory,parameters+2*i,x,2)
        c.compare(f'signature input alias/{offset}',memory,'signature_coefficients',(ARENA+8192,parameters),offset%4)
    for effect in (EFFECT+1,EFFECT+2,EFFECT+3):
        memory=initial(25)
        # Copy one complete initial object, preserving byte-level native aliases.
        data=bytes(memory[0][EFFECT-MAPPED[0][0]:EFFECT-MAPPED[0][0]+480])
        for i,value in enumerate(data):setword(memory,effect+i,value,1)
        c.compare(f'unaligned native effect/{effect:x}',memory,'build25',(effect,),effect&3)

def boundary_cases(c):
    for pending in (0,1):
        for active in (0,1):
            m=initial(25);setword(m,EFFECT+308,pending);setword(m,EFFECT+405,active,1)
            c.compare(f'pitch25 cold/{pending}/{active}',m,'build25',(EFFECT,))
    for coarse,fine in ((-120,0),(-12,0),(-5,0),(-4,0),(-3,0),(0,-1),(0,0),(0,1),(3,0),(12,0),(120,0)):
        for limit in (0,20,54,55):
            m=initial(29);setword(m,CFG+16,limit)
            for i,x in enumerate((coarse,fine,50,0,1000,0,1)):setword(m,EFFECT+70+2*i,x,2)
            for offset in (365,366,371):setword(m,EFFECT+offset,0,1)
            m=c.compare(f'pitch29 cold/{coarse}/{fine}/{limit}',m,'build29',(EFFECT,))
            c.compare(f'pitch29 carried/{coarse}/{fine}/{limit}',m,'build29',(EFFECT,))
    for x in (0,-1):
        m=initial(39);setword(m,EFFECT+72,x,2);c.compare(f'model39 minimum/{x}',m,'build39',(EFFECT,))
    m=initial();c.compare('zero polynomial has no sign crossing',m,'tone_polynomial',(ARENA,0,0,0,ARENA+64))
    m=initial(19);setword(m,EFFECT+82,1,2);c.compare('model19 second record',m,'build19',(EFFECT,))
    for object_,buffer in ((0,ARENA),(ARENA+8192,0)):
        m=initial(27);setword(m,EFFECT+288,object_);setword(m,EFFECT+84,buffer)
        c.compare(f'missing object/{object_}/{buffer}',m,'build_object',(EFFECT,))
    for gate in (False,True):
        memory=initial()
        for i,x in enumerate((0,0,0x3f800000,0,0,0,0x7fc00000 if gate else 0)):setword(memory,ARENA+4*i,x)
        holes=((ARENA+4,ARENA+20 if gate else ARENA+8),)
        c.compare(f'sparse response/{gate}',memory,'frequency_response',(ARENA,floating(.5)),holes=holes)
        c.compare(f'sparse swept response/{gate}',memory,'tone_response',(ARENA,),holes=holes)

TABLE_PROOFS={
 'model_branches':('build16_to23',(0x0202b83a,0x0202b83c,0x0202b83e,0x0202b844),'Eight byte entries; type minus 16 is bounded to 0..7.'),
 'object2_lengths':('object_mode2',(0x0202c69e,0x0202c6a4,0x0202c6f4),'Three halfwords; index 0..2.'),
 'object_records':('object_record',(0x01c06004,0x01c06008,0x01c0600a,0x01c0600e,0x01c06010,0x01c06014,0x01c06018,0x01c0601a,0x01c0601e,0x01c06024),'Four 84-byte records. Complete mode0 consumer reads record fields through offset82.'),
 'type19_records':('build19',(0x0202ae2c,0x0202ae2e,0x0202ae32,0x0202ae34,0x0202ae38,0x0202ae3e,0x0202aef8),'Selector equals 1 or is replaced by 0; 36-byte stride and last word+32.'),
 'tone_records':('tone_setup',(0x0202b4a0,0x0202b4a4,0x0202b4c6),'Three 28-byte records; actual builders pass selectors 0, 1, 2. Public helper uses the same bounded domain.'),
 'object1_routes':('object_mode1',(0x0202c466,0x0202c494,0x0202c4ac),'Eight byte routes, index 0..7.'),
 'feedback_levels':('object_feedback',(0x0202c136,0x0202c13c,0x0202c13e,0x0202c144,0x0202c148),'Adjacent float words for intervals 0..3, five words total.'),
 'object0_lengths2':('object_mode0',(0x0202cafc,0x0202cb54,0x0202cb5c,0x0202cb84),'Pinned record groups are 0, 2, 0, 0; reached non-single group uses 16 halfwords. Unused suffix is excluded.'),
 'object0_feedback2':('object_mode0',(0x0202cb8c,0x0202cba6,0x0202cbe0,0x0202cbe6),'Pinned record groups 0, 2, 0, 0 admit two reached float words; unused third word is excluded.'),
 'object1_lengths':('object_length',(0x02029e98,0x02029e9e),'Eight halfwords; complete mode1 loop supplies 0..7; public helper bounds agree.'),
 'type39_times':('build39',(0x0202a902,0x0202a918,0x0202a93e,0x0202a940),'Four word loads with post-increment 4 and loop count 4.'),
 'object1_lengths8':('object_mode1',(0x0202c454,0x0202c476,0x0202c4ac),'Eight halfwords, index 0..7.'),
 'object2_feedback1_to3':('object_mode2',(0x0202c616,0x0202c61a,0x0202c61e,0x0202c622,0x0202c75c,0x0202c768),'Index clamps to 1..3; base 0x0203bdf8 word 0 is never read and remains excluded.'),
 'object0_lengths1':('object_mode0',(0x0202caf8,0x0202cb02,0x0202cb54,0x0202cb5c,0x0202cb84),'Statically identified eight-halfword consumer for groups==1; unreachable with the pinned records and not dynamically validated.'),
 'object31_levels':('object_mode0',(0x0202cbf6,0x0202cbfc,0x0202cc00,0x0202cc04,0x0202cc08,0x0202cc0c,0x0202cc0e,0x0202cc14),'Signed parameter clamps to 0..3, four float words.'),
 'object2_counts1_to3':('object_mode2',(0x0202c616,0x0202c61a,0x0202c61e,0x0202c622,0x0202c624,0x0202c62c),'Index clamps to 1..3; base 0x0203be28 byte 0 is never read and remains excluded.'),
}
MISSING={
 0x01c06216:'Negative rounding of 1-exp: unsigned rate and clamped positive frequency give a finite nonpositive exp argument in the admitted domain; the bounded original exponential is at most 1. The negative branch is not executed.',
 0x0202bb7c:'The window is at most 1300; the prior min bounds rounded count by trunc(1300*.4*.0625+.5)=33, so the signed >=48 branch is impossible.',
 0x0202cb02:'The four immutable records have group bytes 0, 2, 0, 0; this groups==1 table path is unreachable.',
 0x0202cb2e:'The four immutable records have group bytes 0, 2, 0, 0; this groups==1 level path is unreachable.',
 0x0202cb32:'Continuation of the same unreachable groups==1 level path.',
}

def source_paths():
    paths=set(previous_source_paths())|{
      'firmware/src/hyperrig_effect_model_construction.c','firmware/include/hyperrig/hyperrig_effect_model_construction.h',
      'tools/effect_model_construction_machine.py','tools/verify_effect_model_construction.py',
      'tools/build_effect_model_construction.py','tests/test_effect_model_construction_machine.py',
      'tests/effect_model_construction_sanitize.c'}
    pending=[ROOT/path for path in SOURCES];seen=set()
    while pending:
        file=pending.pop()
        if file in seen:continue
        seen.add(file)
        for include in re.findall(r'^\s*#include\s+"([^"]+)"',file.read_text(),re.M):
            target=next((p.resolve() for p in (file.parent/include,ROOT/'firmware/include'/include)if p.is_file()),None)
            if target is None:raise ValueError('unresolved recursive header '+include)
            paths.add(target.relative_to(ROOT).as_posix());pending.append(target)
    return sorted(paths)

def make_report(c,mini_image):
    from hyperrig.jieli import unpack_app
    original=(ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
    if digest(original)!=PINNED or digest(app)!=DECODED or unpack_app(original)[2]['app.bin']!=app:
        raise ValueError('original input binding')
    raw=mini_image.read_bytes()
    if digest(raw)!=MINI:raise ValueError('unreviewed MINI input')
    mini=unpack_app(raw)[2]['app.bin'];program=c.program
    def binding(a,b):
        value=region_bytes(app,a,b)
        if region_bytes(mini,a,b)!=value:raise ValueError(f'MINI mismatch {a:#x}..{b:#x}')
        return {'start':f'0x{a:08x}','end_exclusive':f'0x{b:08x}','sha256':digest(value)}
    functions={}
    for name,(a,b)in (REGIONS|REUSED).items():
        item=binding(a,b);item['bytes_sha256']=item.pop('sha256');pcs={pc for pc in program.code if a<=pc<b}
        item.update(instructions=len(pcs),visited=len(pcs&c.visited),new=name in REGIONS);functions[name]=item
    new={pc for pc in program.code if any(a<=pc<b for a,b in REGIONS.values())};missing=new-c.visited
    if missing-set(MISSING):raise ValueError('unclassified new instructions '+repr(sorted(missing-set(MISSING))))
    windows=[]
    for pc,(_,size,*_)in sorted(program.code.items()):
        if windows and windows[-1][1]==pc:windows[-1][1]=pc+size
        else:windows.append([pc,pc+size])
    proofs={}
    for name,(consumer,sites,explanation)in TABLE_PROOFS.items():
        a,b=REGIONS[consumer]
        if any(pc not in program.code or not a<=pc<b for pc in sites):raise ValueError('table consumer proof '+name)
        proofs[name]={'consumer':consumer,'consumer_binding':binding(a,b),'explanation':explanation,
          'sites':{f'0x{pc:08x}':program.code[pc][0]for pc in sites},
          'dynamically_reached':name!='object0_lengths1'}
    groups=[program.data['object_records'][i*84+58]for i in range(4)]
    if groups!=[0,2,0,0]:raise ValueError('object record invariant')
    return {'component':'reconstructed-effect-model-construction','result':'pass','flashable':False,'device_access':False,
      'original_sha256':PINNED,'decoded_sha256':DECODED,'mini_sha256':MINI,'functions':functions,
      'static_data':{name:binding(*span)for name,span in STATIC.items()},'table_proofs':proofs,'immutable_record_groups':groups,
      'loaded_instruction_windows':[binding(a,b)for a,b in windows],
      'loaded_static_data':{name:binding(*span)for name,span in program.static_regions.items()},
      'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.visited),
        'unvisited_new':[f'0x{x:08x}'for x in sorted(missing)],'all_decoded':len(program.code),
        'all_visited':len(set(program.code)&c.visited),'unvisited_inherited':[f'0x{x:08x}'for x in sorted(set(program.code)-new-c.visited)]},
      'missing_classification':{f'0x{x:08x}':MISSING[x]for x in sorted(missing)},
      'comparisons':sum(c.counts.values()),'comparisons_by_entry':c.counts,'original_steps':c.steps,
      'actual_calls':{f'0x{x:08x}':n for x,n in sorted(c.calls.items())},'sparse_mapping_cases':c.sparse_cases,
      'carried_cases':c.carried,'native_alias_cases':c.aliases,'extended_exp_calls':c.extended_exp,
      'largest_exp_magnitude_bits':f'0x{c.exp_max:08x}','sanitizer_replays':c.replays,
      'comparison_sha256':c.digest.hexdigest(),'source_sha256':{name:digest((ROOT/name).read_bytes())for name in source_paths()}}

def main():
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--part',choices=('helpers','builders','integration','boundaries','all'),default='all');parser.add_argument('--output',type=Path)
    parser.add_argument('--fixtures',type=Path);parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args();fixtures=args.fixtures.open('xb')if args.fixtures else None;c=Corpus(args.library,fixtures)
    for name,function in (('helpers',helper_cases),('builders',builder_cases),('integration',integration_cases),('boundaries',boundary_cases)):
        if args.part in (name,'all'):function(c);print(name,sum(c.counts.values()),flush=True)
    report={'comparisons':sum(c.counts.values()),'counts':c.counts,'steps':c.steps,
            'visited':[f'0x{x:08x}' for x in sorted(c.visited)],'digest':c.digest.hexdigest()}
    if fixtures:fixtures.close()
    if args.output:
        if args.mini_image:report=make_report(c,args.mini_image)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'comparisons':sum(c.counts.values()),'steps':c.steps,
                     'counts':c.counts,'comparison_sha256':c.digest.hexdigest()}))

if __name__=='__main__':main()
