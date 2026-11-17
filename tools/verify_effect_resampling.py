"""Compare complete native resampling output, preserved history and guards."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys
from effect_resampling_machine import EffectResamplingProgram, REGIONS, STATIC, ROOT, offset, ORIGINAL_SHA, MINI_SHA
from dot_machine import signed

U32=ctypes.c_uint32
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
class IO(ctypes.Structure):
    _fields_=[('map',MAP),('call',ctypes.c_void_p),('opaque',ctypes.c_void_p)]
SOURCE,OUTPUT=0x31000100,0x32000100

def parameters(name,count,selector):
    down=name.startswith('down');wrapper=name in ('up','down')
    if wrapper and count&3 and count>>31:return down,0,0,0
    mode=(selector if count&3 else (2 if selector==2 else 0)) if wrapper else (2 if name.endswith('4') else 0)
    taps=(5,3,4)[mode];prefix=4*taps-2 if down else 2*taps-1
    return down,taps,prefix,count*2-1 if down else count

def fixture(name,count,selector,words):
    down,taps,prefix,n=parameters(name,count,selector)
    if not taps:return ((SOURCE,bytes(16)),(OUTPUT,bytes(16)))
    assert len(words)==prefix+n
    return ((SOURCE-prefix*4,struct.pack('<'+'i'*len(words),*words)),
        (OUTPUT,bytes([0xa5])*(count*(4 if down else 8))))

class Memory:
    def __init__(self,memory,unaligned=False,missing=False,alias=False):
        self.alloc=[];self.spans=[];self.calls=[];self.unaligned=unaligned
        for base,data in memory:
            buf=(ctypes.c_ubyte*(len(data)+16+int(unaligned)))()
            ctypes.memset(ctypes.addressof(buf),0x5a,len(buf));start=8+int(unaligned)
            ctypes.memmove(ctypes.addressof(buf)+start,data,len(data))
            self.alloc.append(buf);self.spans.append((base,len(data),ctypes.addressof(buf)+start))
        def mapping(_,address,n,writable):
            self.calls.append((address,n,writable))
            if missing:return None
            for base,length,pointer in self.spans:
                if base<=address<=address+n<=base+length:
                    return self.spans[0][2] if alias and writable else pointer+address-base
            return None
        self.callback=MAP(mapping);self.io=IO(self.callback,None,None)
    def snapshot(self):return tuple((base,ctypes.string_at(pointer,n)) for base,n,pointer in self.spans)
    def guards(self):
        return all(bytes(buf[:8+int(self.unaligned)])==b'\x5a'*(8+int(self.unaligned)) and bytes(buf[-8:])==b'\x5a'*8 for buf in self.alloc)

def source_paths():
    paths={'firmware/src/hyperrig_effect_resampling.c','firmware/include/hyperrig/hyperrig_effect_resampling.h',
        'tools/effect_resampling_machine.py','tools/verify_effect_resampling.py','tools/build_effect_resampling.py',
        'tests/test_effect_resampling_machine.py','tests/effect_resampling_sanitize.c',
        'research/input-manifest.json','third_party/ultrarig/LICENSE.md','third_party/ultrarig/NOTICE.md',
        'upstream/pi32v2-isa/isa/pi32v2.toml'}
    # Preserve the explicit ISA semantic sources from the outset, including
    # files which other model adapters load outside sys.modules.
    for name in ('b2.py','r.py','s.py','v3.py','_r_util.py'):
        paths.add('upstream/pi32v2-isa/tools/hwtest/semantics/'+name)
    pending=[ROOT/p for p in paths if p.endswith(('.c','.h'))];seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path)
        for name in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]',path.read_text(),re.M):
            for candidate in (path.parent/name,ROOT/'firmware/include'/name):
                if candidate.is_file():
                    candidate=candidate.resolve();paths.add(candidate.relative_to(ROOT).as_posix());pending.append(candidate);break
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
    return sorted(paths)

class Corpus:
    def __init__(self,library,replay=None):
        self.program=EffectResamplingProgram();self.library=ctypes.CDLL(str(library.resolve()))
        self.run=self.library.hyperrig_effect_resampling_run;self.run.argtypes=[U32]*5+[ctypes.POINTER(IO)];self.run.restype=ctypes.c_int
        self.replay=replay;self.visited=set();self.steps=0;self.cases=0;self.counts={name:0 for name in REGIONS}
        self.calls={};self.digest=hashlib.sha256();self.carried=0
    def compare(self,name,count,selector,words=None,memory=None,unaligned=False,carried=False,
        source=SOURCE,output=OUTPUT,state=None):
        memory=state.snapshot() if state is not None else fixture(name,count,selector,words) if memory is None else memory
        result=self.program.execute(memory,name,source,output,count,selector)
        native=state if state is not None else Memory(memory,unaligned);entry=REGIONS[name][0]
        status=self.run(entry,source,output,count,selector,ctypes.byref(native.io))
        assert status==0,(name,count,selector,status)
        actual=native.snapshot()
        assert actual==result['memory'],(name,count,selector,[(i,a,b) for i,(a,b) in enumerate(zip(actual[1][1],result['memory'][1][1])) if a!=b][:16])
        assert native.guards() and actual[0]==memory[0]
        self.cases+=1;self.counts[name]+=1;self.steps+=result['steps'];self.visited.update(result['visited']);self.carried+=carried
        for target,_ in result['calls']:self.calls[target]=self.calls.get(target,0)+1
        for base,data in actual:self.digest.update(struct.pack('<I',base)+data)
        if self.replay:
            self.replay.write(struct.pack('<6I',entry,source,output,count,selector,len(memory)))
            for (base,data),(other,expected) in zip(memory,actual):
                assert base==other;self.replay.write(struct.pack('<2I',base,len(data))+data+expected)
        return result

def corpus(c):
    rng=random.Random(0x1c07986)
    # Every current/history position, all-bit patterns, all scalar modes, and
    # mode1's deliberate switch to five taps at positive multiples of four.
    for name in REGIONS:
        lengths=(1,2,3,4,5,7,8,15,16,31,32,63,64,127,128,129,255,256) if name in ('up','down') else (4,8,16,64,128,256)
        for count in lengths:
            selectors=(0,1,2,3,0xffffffff) if name in ('up','down') and count%4==0 else (0,1,2) if name in ('up','down') else (0,)
            for selector in selectors:
                down,taps,prefix,n=parameters(name,count,selector);length=prefix+n
                patterns=[[value]*length for value in (0,1,-1,0x7fffffff,-0x80000000)]
                patterns += [[signed(rng.getrandbits(32)) for _ in range(length)],
                    [(-0x80000000 if i&1 else 0x7fffffff) for i in range(length)]]
                for index,words in enumerate(patterns):c.compare(name,count,selector,words,unaligned=index==5)
        for selector in ((0,1,2) if name in ('up','down') else (0,)):
            count=7 if name in ('up','down') else 8
            _,_,prefix,n=parameters(name,count,selector)
            for position in range(prefix+n):
                words=[0]*(prefix+n);words[position]=0x7fffffff if position&1 else -0x80000000
                c.compare(name,count,selector,words)
    # Force both overflow directions in every unrolled lane and scalar path.
    coefficient_rows=((670538396,-191090179,82421978,-34042030,11421924),
        (642179087,-126556346,21758483),(665320397,-177530276,65670763,-20310474))
    for name in REGIONS:
        for selector in ((0,1,2) if name in ('up','down') else (0,)):
            count=7 if name in ('up','down') else 8
            down,taps,prefix,n=parameters(name,count,selector)
            mode=(selector if count%4 else 2 if selector==2 else 0) if name in ('up','down') else 2 if name.endswith('4') else 0
            for lane in range(count):
                for polarity in (1,-1):
                    words=[0]*(prefix+n);center=prefix+(2*lane if down else lane)-(2*taps if down else taps)
                    if down:words[center+1]=polarity*0x7fffffff
                    for j,coefficient in enumerate(coefficient_rows[mode]):
                        value=polarity*(0x7fffffff if coefficient>0 else -0x7fffffff)
                        words[center+(2 if down else 1)+(2*j if down else j)]=value
                        words[center-(2*j if down else j)]=value
                    c.compare(name,count,selector,words)
    # Reuse the same mapped C storage and every prior original output byte.
    # Advancing the source token preserves real caller-owned history, including
    # selector1's switch between scalar three-tap and unrolled five-tap paths.
    for name in ('up','down'):
        for selector in (0,1,2):
            down=name=='down';prefix=18 if down else 9;counts=(31,32,7,8)*3
            stream=[signed(rng.getrandbits(32)) for _ in range(prefix+sum(counts)*(2 if down else 1))]
            memory=((SOURCE-prefix*4,struct.pack('<'+'i'*len(stream),*stream)),
                (OUTPUT,b'\xa5'*(max(counts)*(4 if down else 8))))
            state=Memory(memory);advance=0;previous=memory
            for count in counts:
                assert state.snapshot()==previous
                result=c.compare(name,count,selector,source=SOURCE+advance*4,state=state,carried=True)
                previous=result['memory'];advance+=count*(2 if down else 1)
    for name in ('up','down'):
        for count in (0xffffffff,0x80000001,0xfffffffe):
            c.compare(name,count,0xffffffff,memory=((SOURCE,b'\xa5'*16),(OUTPUT,b'\x5a'*16)))

def guards(c):
    memory=fixture('up',4,0,[0]*13);checks=0
    for entry,src,dst,count,selector,expected in [
        (0,SOURCE,OUTPUT,4,0,-202),(REGIONS['up'][0],SOURCE,OUTPUT,0,0,-202),
        (REGIONS['up'][0],SOURCE,OUTPUT,0x80000000,0,-202),
        (REGIONS['up'][0],SOURCE,OUTPUT,0xfffffffc,0,-202),
        (REGIONS['up5'][0],SOURCE,OUTPUT,3,0,-202),
        (REGIONS['up'][0],SOURCE,OUTPUT,3,3,-202),
        (REGIONS['up'][0],SOURCE+1,OUTPUT,4,0,-202),
        (REGIONS['up'][0],SOURCE,OUTPUT+2,4,0,-202),
        (REGIONS['up'][0],4,OUTPUT,4,0,-202),
        (REGIONS['up'][0],SOURCE,SOURCE,4,0,-202),
        (REGIONS['up'][0],0xfffffffc,OUTPUT,4,0,-202),
        (REGIONS['up'][0],SOURCE,0xfffffffc,4,0,-202),
        (REGIONS['up'][0],SOURCE,OUTPUT,0x40000000,0,-202)]:
        state=Memory(memory);before=state.snapshot()
        assert c.run(entry,src,dst,count,selector,ctypes.byref(state.io))==expected
        assert state.snapshot()==before and state.guards();checks+=1
    state=Memory(memory)
    assert c.run(REGIONS['up'][0],SOURCE,OUTPUT,4,0,None)==-200;checks+=1
    empty=IO(MAP(),None,None)
    assert c.run(REGIONS['up'][0],SOURCE,OUTPUT,4,0,ctypes.byref(empty))==-200;checks+=1
    for options,status in (({'missing':True},-201),({'alias':True},-202)):
        state=Memory(memory,**options);before=state.snapshot()
        assert c.run(REGIONS['up'][0],SOURCE,OUTPUT,4,0,ctypes.byref(state.io))==status
        assert state.snapshot()==before and state.guards();checks+=1
    return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mini-image',type=Path,required=True)
    parser.add_argument('--sanitizer-corpus',type=Path,required=True);args=parser.parse_args()
    if args.output.exists() or args.sanitizer_corpus.exists():parser.error('choose fresh evidence paths')
    with args.sanitizer_corpus.open('xb') as replay:
        c=Corpus(args.library,replay)
        sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths()}
        corpus(c)
    guard_count=guards(c);missing=set(c.program.code)-c.visited
    assert not missing,sorted(hex(x) for x in missing)
    app=c.program.app
    records=lambda regions:{name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(app[offset(a):offset(b)]).hexdigest()} for name,(a,b) in regions.items()}
    functions=records(REGIONS)
    for name,(a,b) in REGIONS.items():functions[name].update(instructions=sum(a<=pc<b for pc in c.program.code),visited=sum(a<=pc<b for pc in c.visited))
    raw=args.mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI_SHA
    from hyperrig.jieli import unpack_app
    mini=unpack_app(raw)[2]['app.bin']
    for a,b in (*REGIONS.values(),*STATIC.values()):assert mini[offset(a):offset(b)]==app[offset(a):offset(b)]
    report={'schema':1,'project':'HyperRig','result':'pass','component':'reconstructed-effect-resampling',
        'original_image_sha256':ORIGINAL_SHA,'decoded_image_sha256':hashlib.sha256(app).hexdigest(),
        'functions':functions,'static_data':records(STATIC),'total_comparisons':c.cases,'comparison_counts':c.counts,
        'carried_history_calls':c.carried,'actual_kernel_calls':{hex(p):n for p,n in sorted(c.calls.items())},
        'original_instruction_steps':c.steps,'state_output_sha256':c.digest.hexdigest(),'c_only_guard_checks':guard_count,
        'instruction_coverage':{'new_decoded':len(c.program.code),'new_visited':len(c.visited),'unvisited_new':[],
            'all_decoded':len(c.program.code),'all_visited':len(c.visited)},
        'mini_v4_binding':{'image_sha256':MINI_SHA,'identical_regions':len(REGIONS),'identical_static_windows':len(STATIC)},
        'source_sha256':sources,'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),
        'sanitizer_replay_cases':c.cases,'external_services':[],'scripted_numerical_dependencies':0,
        'device_access':False,'hardware_test':False,'audio_test':False,'firmware_changed':False,'flashable':False,
        'limitations':['Original-address and host source/output spans must be disjoint; aliasing cases are rejected before writes.',
            'Counts entering unbounded native zero/negative-multiple loops are guarded, not compared as terminating executions.',
            'Callers own retained history; enclosing effect orchestration and sample-rate clock configuration are not executed here.',
            'Saved callee registers are modeled with their original ABI stack footprint; saved bytes are never read by these bodies.']}
    assert sources=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('result','total_comparisons','original_instruction_steps','instruction_coverage','c_only_guard_checks')}))

if __name__=='__main__':main()
