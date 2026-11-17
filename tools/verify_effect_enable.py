"""Compare borrowed effect-enable state with complete decoded original bodies."""
from __future__ import annotations
import argparse, ctypes, hashlib, json, random, struct, sys
from pathlib import Path
from effect_enable_machine import (EffectEnableProgram, REGIONS, REUSED, ARITIES, VOID,
    MAPPED, EFFECTS, CONFIG, CONTROL, CALLBACKS, ARENA, SERVICES, ABI_REGIONS,
    TABLE_START, TABLE_END, ALIGNMENT_END, ROOT, region_bytes)
U8, U32 = ctypes.c_uint8, ctypes.c_uint32
MAP = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, U32, U32, ctypes.c_int)
CALL = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, ctypes.POINTER(U32), U32)
class IO(ctypes.Structure):
    _fields_ = [('map', MAP), ('call', CALL), ('opaque', ctypes.c_void_p),
                ('call_budget', U32), ('bulk_store_budget', U32)]
PINNED = '2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
MINI = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
INSTALLED, ALTERNATE = 0x0201A9DC, 0x12345678

def put(data, offset, value, size=4):
    data[offset:offset+size] = (value & ((1 << (8*size))-1)).to_bytes(size, 'little')

def initial(type_=0, *, seed=0):
    rng = random.Random(seed)
    memory = [bytearray(rng.randbytes(n)) for _, n in MAPPED]
    e, cfg, ctl, callbacks, arena = memory
    for slot in range(16):
        p = slot*480; e[p] = type_; e[p+1:p+3] = b'\0\1'; put(e, p+8, 0, 2)
        e[p+10:p+12] = b'\0\0'; put(e, p+84, ARENA+4096); put(e, p+88, 4)
        for off in (288, 304, 308, 320, 324, 332, 400): put(e, p+off, 0)
        e[p+369] = 0
    put(cfg, 16, 0); put(ctl, 48, 1000); put(callbacks, 4, 0); put(callbacks, 728, 0)
    put(arena, 0, 1); put(arena, 4, 1); put(arena, 24, ARENA+1024); put(arena, 48, ARENA+2048)
    return memory

class Script:
    def __init__(self, plan=None, mutations=None):
        self.plan = plan or {}; self.mutations = mutations or {}; self.seen = {}
    def __call__(self, target, args, m):
        index = self.seen.get(target, 0); self.seen[target] = index+1
        value = self.plan.get(target, 0)
        if isinstance(value, list): value = value[min(index, len(value)-1)]
        if callable(value): value = value(args, m, index)
        for address, replacement, size in self.mutations.get((target, index), ()):
            m.write(address, replacement, size)
        return value & 0xffffffff

class CMemory:
    def __init__(self, memory):
        self.buffers = [(U8*len(data)).from_buffer_copy(data) for data in memory]
    def pointer(self, address, size):
        for (base, n), data in zip(MAPPED, self.buffers):
            if base <= address <= base+n and size <= base+n-address:
                return ctypes.addressof(data)+address-base
        raise ValueError(f'unmapped enable C address {address:#x}/{size}')
    def read(self, address, size): return int.from_bytes(ctypes.string_at(self.pointer(address, size), size), 'little')
    def write(self, address, value, size):
        ctypes.memmove(self.pointer(address, size), (value & ((1 << (8*size))-1)).to_bytes(size, 'little'), size)
    def snapshot(self): return tuple(bytes(b) for b in self.buffers)

def load_library(path):
    library = ctypes.CDLL(str(path.resolve()))
    library.hyperrig_effect_enable_execute.argtypes = [U32, ctypes.POINTER(U32), ctypes.POINTER(U32), ctypes.POINTER(IO)]
    library.hyperrig_effect_enable_execute.restype = ctypes.c_int
    library.hyperrig_effect_enable_ir_reset.argtypes = [U32, ctypes.POINTER(IO)]
    library.hyperrig_effect_enable_ir_reset.restype = ctypes.c_int
    return library

class Comparison:
    def __init__(self, library):
        self.library = library; self.program = EffectEnableProgram(); self.coverage = set()
        self.counts = {}; self.steps = 0; self.internal = {}; self.services = {}
        self.service_sites = set()
        self.carried = self.mutating = 0; self.digest = hashlib.sha256()
    def run(self, label, memory, operation, args, *, plan=None, mutations=None, carried=False):
        native = self.program.execute(memory, operation, *args, boundary=Script(plan, mutations))
        m = CMemory(memory); script = Script(plan, mutations); calls = []; errors = []
        def mapped(_, address, size, writable):
            try: return m.pointer(address, size)
            except Exception as exc: errors.append(exc); return None
        def call(_, target, raw, count):
            try:
                _, expected_target, expected = native['service_sites'][len(calls)]
                assert (target,count) == (expected_target,expected), (target,count,expected_target,expected)
                a = tuple(raw[i] for i in range(6)); before = m.snapshot()
                value = script(target, a, m); calls.append((target, a, before, m.snapshot())); return value
            except Exception as exc: errors.append(exc); return 0
        map_cb, call_cb = MAP(mapped), CALL(call)
        io = IO(map_cb, call_cb, None, 10000, 100000)
        arguments = (U32*3)(*(tuple(args)+(0,)*(3-len(args)))); result = U32(0xdeadbeef)
        status = self.library.hyperrig_effect_enable_execute((REGIONS | REUSED)[operation][0],
            arguments, ctypes.byref(result), ctypes.byref(io))
        assert status == 0 and not errors, (label, status, errors)
        assert result.value == native['result'], (label, 'result', hex(result.value), hex(native['result']))
        if m.snapshot() != native['memory']:
            differences = [(hex(base+i), a, b) for (base, _), left, right in zip(MAPPED, m.snapshot(), native['memory'])
                           for i, (a, b) in enumerate(zip(left, right)) if a != b]
            raise AssertionError((label, 'memory', differences[:12]))
        assert calls == native['calls'], (label, 'service call/order/state mismatch', [(hex(t), a) for t,a,*_ in calls],
                                         [(hex(t), a) for t,a,*_ in native['calls']])
        self.coverage.update(native['visited']); self.steps += native['steps']
        self.service_sites.update(native['service_sites'])
        self.counts[operation] = self.counts.get(operation, 0)+1
        self.carried += bool(carried); self.mutating += bool(mutations)
        for target in native['internal_calls']: self.internal[target] = self.internal.get(target, 0)+1
        for target, *_ in calls: self.services[target] = self.services.get(target, 0)+1
        for data in native['memory']: self.digest.update(data)
        self.digest.update(struct.pack('<I', result.value))
        return native

def corpus(c):
    run = c.run
    for value in (*range(256), 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff):
        run(f'type-{value}', initial(), 'tail_type', (value,))
    for type_ in (*range(40), 255):
        memory = initial(type_); put(memory[0], 304, 0x01000000); put(memory[0], 308, 0x02000000)
        run(f'duration-type-{type_}', memory, 'duration', (EFFECTS,))
    edges = (0, 1, 0xffffffff, 0x7fffffff, 0x80000000, 0xffff0000, 0x007fffff, 0x00800000, 0x01000000)
    for type_ in (11, 12, 15, 25, 29, 39):
        for index, a in enumerate(edges):
            for b in edges:
                memory = initial(type_, seed=index)
                for off, value in ((304, a), (308, b), (320, a), (324, b), (332, a), (400, a)):
                    put(memory[0], off, value)
                run(f'duration-raw-{type_}-{a}-{b}', memory, 'duration', (EFFECTS,))
        for absent in ('buffer', 'type29_gate'):
            memory = initial(type_); put(memory[0], 304, 0x01000000)
            if absent == 'buffer': put(memory[0], 84, 0)
            else: memory[0][369] = 255
            run(f'duration-{absent}-{type_}', memory, 'duration', (EFFECTS,))
    print('Type predicate and signed/wrapped duration arithmetic compared.', flush=True)
    for type_ in range(256):
        for present in (False, True):
            memory = initial(type_, seed=type_); put(memory[0], 84, ARENA+4096 if present else 0)
            run(f'fade-type-{type_}-{present}', memory, 'fade', (EFFECTS, 1))
    for mode in (0, 1, 2, 3, 4, 5, 6, 255):
        for count in (0, 1, 2, 4, 5, 127, 255):
            for enabled in (0, 1, 0x80000000):
                memory = initial(11); memory[0][10:12] = bytes((mode, count))
                run(f'fade-mode-{mode}-{count}-{enabled}', memory, 'fade', (EFFECTS, enabled))
    for type_ in range(46):
        for enabled in (0, 1):
            memory = initial(type_); put(memory[0], 8, 65535, 2)
            run(f'fade-tail-{type_}-{enabled}', memory, 'fade', (EFFECTS, enabled))
    for type_ in (11, 12, 15, 29, 30, 38, 39):
        for length in (0, 1, 2, 3, 1023, 1024, 1025, 4095, 0x7fffffff, 0x80000000, 0xffffffff):
            for callback in (0, INSTALLED, ALTERNATE):
                if length in (0x7fffffff, 0x80000000) and callback == 0: continue
                memory = initial(type_); put(memory[0], 88, length); put(memory[3], 4, callback)
                run(f'fade-clear-{type_}-{length}-{callback}', memory, 'fade', (EFFECTS, 1))
    for alignment in range(4):
        for count in (0, 1, 2, 3, 4, 5, 7, 8, 9, 255, 256, 257, 1023, 1024, 1025, 8192):
            for fill in (0, 255, 0x12345678, 0xffffffff):
                run(f'memset-{alignment}-{count}-{fill}', initial(), 'memset', (ARENA+alignment, fill, count))
            run(f'clear-{alignment}-{count}', initial(), 'clear', (ARENA+alignment, count))
    print('Fade table, reversal states and actual installed clear/memset execution compared.', flush=True)
    for active in (0, 1, 0xffffffff):
        for count in (0, 1, 2, 7, pow(129, -1, 2**32)):
            memory = initial(); put(memory[4], 0, active); put(memory[4], 4, count)
            if count == 7: put(memory[4], 48, ARENA+12288)
            run(f'ir-reset-{active}-{count}', memory, 'ir_reset', (ARENA,))
    run('ir-reset-null', initial(), 'ir_reset', (0,))
    # Count is cached before spectral writes; the subsequent tail pointer is fresh.
    memory = initial(); put(memory[4], 4, pow(129, -1, 2**32)); put(memory[4], 24, ARENA+4)
    run('ir-reset-aliased-count', memory, 'ir_reset', (ARENA,))
    for callback in (0, INSTALLED):
        memory = initial(7); put(memory[0], 288, ARENA); put(memory[3], 4, callback)
        run('fade-real-ir-reset', memory, 'fade', (EFFECTS, 1))
    for operation in ('commit_core', 'fast_core', 'commit', 'fast', 'commit_unchecked', 'fast_unchecked'):
        for slot in (0, 15, 16, 0xffffffff):
            for enabled in (0, 1, 255, 0x80000000):
                for checked in ((0, 1) if operation.endswith('core') else (0,)):
                    memory = initial(0); put(memory[3], 728, 0xffffffff)
                    args = (slot, enabled, checked) if operation.endswith('core') else (slot, enabled)
                    run(f'{operation}-{slot}-{enabled}-{checked}', memory, operation, args)
        for present, old, tail, tails in ((0,0,0,0), (1,1,0,0), (1,255,0,1), (1,0,1,1), (1,1,1,1)):
            for enabled in (0, 1):
                for type_ in (5, 7, 11, 15, 27, 29, 31, 38, 39):
                    memory = initial(type_); memory[0][1:3] = bytes((old, present))
                    put(memory[0], 8, tail, 2); put(memory[1], 16, tails)
                    args = (0, enabled, 1) if operation.endswith('core') else (0, enabled)
                    run(f'{operation}-state-{present}-{old}-{tail}-{tails}-{enabled}-{type_}', memory, operation, args)
    for operation in ('commit', 'fast'):
        for cost, total, limit in ((0,0,0), (1,0,0), (100,900,1000), (100,901,1000),
                                  (0xffffffff,1,0), (0xffffffff,0,0xfffffffe), (0x80000000,0x80000000,0)):
            memory = initial(); put(memory[2], 48, limit)
            run(f'{operation}-resource-{cost}-{total}-{limit}', memory, operation, (0,1),
                plan={0x0203023C:cost, 0x02028DE8:total})
        for status in (0, 1, 0xfffffffa, 0xfffffffd, 0xffffffff):
            run(f'{operation}-construct-{status}', initial(), operation, (0,1), plan={0x0203033C:status})
    for type_ in (0, 7, 11):
        for demand in (0,1,0xffffffff):
            for buffer in (0, ARENA+4096):
                memory = initial(type_); put(memory[0],84,buffer)
                run('fast-availability', memory, 'fast', (0,1), plan={0x0202DEF2:demand})
    for value in (0, 1, 0xffffffff, 0xfffffffc): run('finish', initial(), 'finish', (value,), plan={0x0202EC30:17})
    run('counter-wrap', initial(), 'counter', ())
    print('Enable wrappers, resource order, raw booleans, failures and IR reset compared.', flush=True)
    mutations = [
        ('commit', 0x0203023C, [(CONTROL+48,0,4)], {0x0203023C:1}),
        ('commit', 0x02028DE8, [(CONTROL+48,0,4)], {0x0203023C:1}),
        ('commit', 0x0203033C, [(EFFECTS+1,255,1)], {}),
        ('commit', 0x0203033C, [(EFFECTS+8,1,2),(EFFECTS,31,1)], {}),
        ('commit', 0x0203033C, [(EFFECTS,7,1),(EFFECTS+288,ARENA,4)], {}),
        ('fast', 0x0202DEF2, [(EFFECTS+84,0,4)], {0x0202DEF2:1}),
        ('fast', 0x0202DEF2, [(EFFECTS+1,1,1)], {}),
        ('fast', 0x02028DE8, [(CONTROL+48,0,4)], {0x0203023C:1}),
        ('fast', 0x0203023C, [(CONTROL+48,0,4)], {0x0203023C:1}),
        ('fast', 0x0203023C, [(EFFECTS+8,1,2),(EFFECTS,31,1)], {}),
        ('fast', 0x0203023C, [(EFFECTS,7,1),(EFFECTS+288,ARENA,4)], {}),
        ('commit', 0x0202EC30, [(EFFECTS+1,0,1),(CALLBACKS+728,99,4)], {}),
    ]
    for index,(operation,target,writes,plan) in enumerate(mutations):
        run(f'mutation-{index}', initial(), operation, (0,1), plan=plan, mutations={(target,0):writes})
    for target, type_ in ((ALTERNATE,11),(0x0202E328,29),(0x0202E3CE,30)):
        for change in ([(EFFECTS+304,0x10000000,4)], [(EFFECTS,7,1),(EFFECTS+288,ARENA,4)],
                       [(EFFECTS+84,0,4)], [(EFFECTS+10,255,1),(EFFECTS+11,255,1)]):
            memory = initial(type_); put(memory[0],88,1024); put(memory[3],4,ALTERNATE)
            run('fade-callback-mutation', memory, 'fade', (EFFECTS,1), mutations={(target,0):change})
    # Actual installed clear can alias the same effect fields, with fresh duration reads.
    memory = initial(11); put(memory[0],84,EFFECTS); put(memory[0],88,1024); put(memory[3],4,INSTALLED)
    run('installed-clear-effect-alias', memory, 'fade', (EFFECTS,1))
    # Only the installed clear token is closed. A different token remains an
    # explicit ABI boundary even when another loaded function shares that address.
    memory=initial(11);put(memory[0],88,1024);put(memory[3],4,REGIONS['fast'][0])
    collision=run('alternate-clear-loaded-entry',memory,'fade',(EFFECTS,1))
    assert [(t,a[:2]) for t,a,*_ in collision['calls']]==[(REGIONS['fast'][0],(ARENA+4096,2048))]
    assert REGIONS['fast'][0] not in collision['internal_calls']
    put(memory[3],4,0x0203023c)
    collision=run('alternate-clear-direct-service-entry',memory,'fade',(EFFECTS,1))
    assert [(t,a[:2]) for t,a,*_ in collision['calls']]==[(0x0203023c,(ARENA+4096,2048))]
    assert collision['service_sites']==[(0x01c06af0,0x0203023c,2)]
    for type_ in (5,7,11,27,31,38):
        state = initial(type_); put(state[1],16,1)
        if type_ == 7: put(state[0],288,ARENA)
        for index in range(12):
            result = run('carried-enable-fade', state, 'commit' if index%3 else 'fast', (0,index%2), carried=True)
            state = [bytearray(b) for b in result['memory']]
    return c

def source_files():
    names = {'firmware/src/hyperrig_effect_enable.c', 'firmware/include/hyperrig/hyperrig_effect_enable.h',
        'tools/effect_enable_machine.py', 'tools/verify_effect_enable.py', 'tools/build_effect_enable.py',
        'tests/test_effect_enable_machine.py', 'tests/effect_enable_sanitize.c', 'research/input-manifest.json',
        'upstream/pi32v2-isa/isa/pi32v2.toml'}
    # Dynamic ISA helpers are not necessarily registered in sys.modules.
    names.update('upstream/pi32v2-isa/tools/hwtest/semantics/'+n+'.py' for n in ('s','b2','r','_r_util','v3'))
    for module in tuple(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if not file: continue
        path = Path(file).resolve()
        if path.suffix == '.py' and path.is_relative_to(ROOT): names.add(path.relative_to(ROOT).as_posix())
    return sorted(names)

def guards(lib):
    memory = CMemory(initial(11)); result = U32(0xdeadbeef); args = (U32*3)(EFFECTS,1,0); count=0
    cb = MAP(lambda _,a,n,w: memory.pointer(a,n) if any(b<=a and a+n<=b+s for b,s in MAPPED) else None)
    io = IO(cb, CALL(), None, 10, 10000)
    execute = lib.hyperrig_effect_enable_execute
    for target, a, out, context in ((0,args,ctypes.byref(result),ctypes.byref(io)),
        (REGIONS['fade'][0],None,ctypes.byref(result),ctypes.byref(io)),
        (REGIONS['fade'][0],args,None,ctypes.byref(io)),
        (REGIONS['fade'][0],args,ctypes.byref(result),None),
        (REGIONS['fade'][0],args,ctypes.byref(result),ctypes.byref(IO()))):
        assert execute(target,a,out,context)==-200;count+=1
    args[0]=0xffffffff
    assert execute(REGIONS['duration'][0],args,ctypes.byref(result),ctypes.byref(io))==-201;count+=1
    args[0]=0;args[1]=1
    assert execute(REGIONS['commit'][0],args,ctypes.byref(result),ctypes.byref(io))==-203;count+=1
    io.call_budget=0
    assert execute(REGIONS['commit'][0],args,ctypes.byref(result),ctypes.byref(io))==-202;count+=1
    args[0]=EFFECTS;io.bulk_store_budget=1
    assert execute(REGIONS['fade'][0],args,ctypes.byref(result),ctypes.byref(io))==-202;count+=1
    assert result.value==0xdeadbeef
    args[0]=ARENA;args[1]=0;args[2]=2;io.bulk_store_budget=0
    assert execute(REGIONS['memset'][0],args,ctypes.byref(result),ctypes.byref(io))==-202;count+=1
    assert lib.hyperrig_effect_enable_ir_reset(0,ctypes.byref(io))==0;count+=1
    return count

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args()
    if args.output.exists():parser.error('choose a fresh verification path')
    c=corpus(Comparison(load_library(args.library))); invalid=guards(c.library)
    code=set(c.program.code);new={pc for pc in code if any(a<=pc<b for a,b in REGIONS.values())}
    missing=sorted(new-c.coverage)
    if missing != [0x020304FC]:
        raise AssertionError(('unexpected enable coverage gaps', [hex(pc) for pc in missing]))
    app=(ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes();mini_binding=None
    if args.mini_image:
        from hyperrig.jieli import unpack_app
        raw=args.mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI
        mini=unpack_app(raw)[2]['app.bin']
        for a,b in (REGIONS|REUSED|ABI_REGIONS).values():assert region_bytes(mini,a,b)==region_bytes(app,a,b)
        mini_binding={'image_sha256':MINI,'all_decoded_regions_and_complete_abi_windows_identical':True}
    report={'schema':1,'project':'HyperRig','result':'pass','original_image_sha256':PINNED,
        'scope':'complete enable cores/wrappers, duration, tail/fade, IR reset and installed clear/memset',
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'instructions':sum(a<=pc<b for pc in code),'visited':sum(a<=pc<b for pc in c.coverage)}
            for name,(a,b) in (REGIONS|REUSED).items()},
        'static_data':{'fade_table':{'start':TABLE_START,'end_exclusive':TABLE_END,
            'sha256':hashlib.sha256(region_bytes(app,TABLE_START,TABLE_END)).hexdigest()},
            'fade_alignment':{'start':TABLE_END,'end_exclusive':ALIGNMENT_END,
            'sha256':hashlib.sha256(region_bytes(app,TABLE_END,ALIGNMENT_END)).hexdigest()}},
        'abi_evidence_not_executed':{name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest()}
            for name,(a,b) in ABI_REGIONS.items()},
        'external_service_arities':{hex(k):v for k,v in SERVICES.items()},
        'comparisons':c.counts,'total_comparisons':sum(c.counts.values()),'original_instruction_packets':c.steps,
        'actual_internal_entries':{hex(k):v for k,v in sorted(c.internal.items())},
        'external_service_calls':{hex(k):v for k,v in sorted(c.services.items())},
        'observed_external_call_sites':[{'site':pc,'target':target,'arity':arity}
            for pc,target,arity in sorted(c.service_sites)],
        'carried_calls':c.carried,'callback_mutation_cases':c.mutating,'api_guard_checks':invalid,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.coverage),'unvisited_new':missing,
            'all_decoded':len(code),'all_visited':len(code&c.coverage),'unvisited_all':sorted(code-c.coverage)},
        'missing_classification':{'0x020304fc':{
            'classification':'unreachable from a complete public entry with the preserved callback ABI',
            'reason':'The construct branch is entered only with nonzero desired r4. Calls preserve r4; '
                     'the preceding test at 0x020304fa therefore always skips this zero-only move.'}},
        'outputs_and_state_sha256':c.digest.hexdigest(),'mini_v4_binding':mini_binding,
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files()},
        'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),
        'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'limitations':['allocation/resource/refresh and alternate clear callbacks remain explicit mutable services',
            'REP executes pinned ISA modeled register counts; zero and large counts are not new hardware measurements',
            'mapped spans and budgets define terminating portable execution; invalid mappings retain prior writes',
            'byte-bound external ABI windows are provenance, not reconstructed/executed functions']}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('result','total_comparisons','instruction_coverage')}),flush=True)

if __name__=='__main__':main()
