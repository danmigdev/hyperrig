"""Compare complete parameter primitives against decoded original instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import random
import re
import struct
import sys
from pathlib import Path
from effect_parameter_support_machine import (EffectParameterSupportProgram, REGIONS,
    REUSED, STATIC, ARITIES, MAPPED, CONFIG, CONTROL, CALLBACKS, ARENA, ROOT, region_bytes)
from dot_machine import signed, MASK32, MASK64

PINNED = '2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
MINI = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
U8, U32 = ctypes.c_uint8, ctypes.c_uint32
MAP = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, U32, U32, ctypes.c_int)
class Borrowed(ctypes.Structure):
    _fields_ = [('map', MAP), ('opaque', ctypes.c_void_p)]
CALL = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, ctypes.POINTER(U32), U32, ctypes.POINTER(Borrowed))
class IO(ctypes.Structure):
    _fields_ = [('map', MAP), ('call', CALL), ('opaque', ctypes.c_void_p), ('service_budget', U32), ('work_budget', U32)]

def put(data, offset, value, size=4):
    data[offset:offset+size] = (value & ((1 << (8*size))-1)).to_bytes(size, 'little')

def initial(seed=0):
    memory = [bytearray(((i*29+seed*17+7)&255 for i in range(n))) for _, n in MAPPED]
    put(memory[0], 28, 100, 1); put(memory[0], 36, 48077); put(memory[0], 40, 12000)
    memory[1][3] = 0; put(memory[1], 40, 0xffffffff); put(memory[2], 4, 0)
    return memory

def fnv(memory):
    value = 14695981039346656037
    for data in memory:
        for byte in data: value = (value ^ byte)*1099511628211 & MASK64
    return value

class Script:
    def __init__(self, mutations=()): self.mutations = mutations
    def __call__(self, target, args, memory):
        for address, value, size in self.mutations: memory.write(address, value, size)
        return 0x89abcdef

class Memory:
    def __init__(self, memory, program, alignment=0):
        self.regions = [(*bounds, False) for bounds in MAPPED]
        self.regions += [(a, b-a, True) for a, b in STATIC.values()]
        source = [*memory, *program.data.values()]
        self.storage = [(U8*(len(data)+alignment))() for data in source]
        self.addresses = [ctypes.addressof(data)+alignment for data in self.storage]
        for address, data in zip(self.addresses, source): ctypes.memmove(address, bytes(data), len(data))
    def pointer(self, address, size, writable=0):
        for (base, n, readonly), pointer in zip(self.regions, self.addresses):
            if base <= address <= address+size <= base+n:
                if writable and readonly: raise ValueError('immutable support table write')
                return pointer+address-base
        raise ValueError(f'unmapped support span {address:#x}/{size}')
    def write(self, address, value, size):
        ctypes.memmove(self.pointer(address, size, 1), (value&((1 << (8*size))-1)).to_bytes(size, 'little'), size)
    def snapshot(self): return tuple(ctypes.string_at(pointer, n) for (_, n), pointer in zip(MAPPED, self.addresses))

def load_library(path):
    library = ctypes.CDLL(str(path.resolve()))
    library.hyperrig_effect_parameter_support_execute.argtypes = [U32, ctypes.POINTER(U32), ctypes.POINTER(U32), ctypes.POINTER(IO)]
    library.hyperrig_effect_parameter_support_execute.restype = ctypes.c_int
    return library

class Comparison:
    def __init__(self, library, fixtures=None):
        self.library, self.program, self.fixtures = library, EffectParameterSupportProgram(), fixtures
        self.counts, self.coverage, self.internal = {}, set(), {}
        self.steps = self.carried = self.mutating = self.calls = self.fixture_count = 0
        self.digest = hashlib.sha256()
        if fixtures:
            fixtures.write(b'HRPSUP01'+struct.pack('<I', 0))
            for name in STATIC: fixtures.write(self.program.data[name])
    def run(self, label, memory, operation, arguments, *, mutations=(), carried=False, alignment=0):
        native = self.program.execute(memory, operation, *arguments, boundary=Script(mutations))
        mapped = Memory(memory, self.program, alignment); errors, calls = [], []
        def mapping(_, address, size, writable):
            try: return mapped.pointer(address, size, writable)
            except Exception as exc: errors.append(exc); return None
        def service(_, target, raw, count, borrowed):
            try:
                assert count == 2
                args = tuple(raw[i] for i in range(12)); before = mapped.snapshot()
                for address, value, size in mutations:
                    pointer = borrowed.contents.map(borrowed.contents.opaque, address, size, 1)
                    assert pointer
                    ctypes.memmove(pointer, (value&((1 << (8*size))-1)).to_bytes(size, 'little'), size)
                calls.append((target, args, before, mapped.snapshot()))
                return 0x89abcdef
            except Exception as exc: errors.append(exc); return 0
        map_cb, call_cb = MAP(mapping), CALL(service)
        io = IO(map_cb, call_cb, None, 10000, 200000)
        args = (U32*12)(*arguments); result = (U32*2)(0xdeadbeef, 0xdeadbeef)
        status = self.library.hyperrig_effect_parameter_support_execute(REGIONS[operation][0], args, result, ctypes.byref(io))
        assert status == 0 and not errors, (label, status, errors)
        assert tuple(result) == native['result'], (label, tuple(result), native['result'])
        assert mapped.snapshot() == native['memory'], (label, 'complete mapped memory mismatch')
        assert calls == native['calls'], (label, 'service order/arguments/mutation mismatch')
        self.counts[operation] = self.counts.get(operation, 0)+1
        self.coverage.update(native['visited']); self.steps += native['steps']
        self.carried += bool(carried); self.mutating += bool(mutations); self.calls += len(calls)
        for target in native['internal_calls']: self.internal[target] = self.internal.get(target, 0)+1
        for data in native['memory']: self.digest.update(data)
        self.digest.update(struct.pack('<II', *native['result']))
        if self.fixtures:
            record = [REGIONS[operation][0], alignment, *arguments, *([0]*(12-len(arguments))),
                      *native['result'], len(mutations), len(calls)]
            self.fixtures.write(struct.pack('<'+'I'*len(record), *record))
            for address, value, size in mutations: self.fixtures.write(struct.pack('<III', address, value, size))
            for target, args, *_ in calls: self.fixtures.write(struct.pack('<III', target, args[0], args[1]))
            for data in memory: self.fixtures.write(data)
            self.fixtures.write(struct.pack('<Q', fnv(native['memory']))); self.fixture_count += 1
        return native
    def finish(self):
        if self.fixtures:
            self.fixtures.seek(8); self.fixtures.write(struct.pack('<I', self.fixture_count)); self.fixtures.flush()

def corpus(c):
    run = c.run; edges = (0, 1, 2, 3, 9, 10, 20, 21, 23, 24, 32, 33, 34, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff)
    for operation in ('selector', 'clamp3', 'clamp2', 'tempo_selector', 'logical_size'):
        for value in (*range(40), *edges): run('raw-selector', initial(), operation, (value,))
    for value in range(40): run('capability', initial(), 'capability', (value,))
    for first in (0, 1, 2, 3, 65535):
        for second in (0, 1, 2, 3, 65535):
            for output in (ARENA+128, ARENA+8, ARENA+12, ARENA+13):
                m = initial(); put(m[3], 8, first, 2); put(m[3], 12, second, 2); m[3][10] = 77
                run('pack-native-alias', m, 'pack', (ARENA, output, ARENA+129), alignment=first&3)
    for primary in (0, ARENA, 0xfffffff0):
        for separate in (0, 1, 255):
            for count in (0, 32335, 32336, 32351, 32352, 0xffffffff):
                m = initial(); put(m[3], 84, primary); m[3][7] = separate; put(m[3], 88, count); put(m[3], 92, 0x12345678)
                run('extra-state', m, 'extra', (ARENA,))
    for value in edges:
        m = initial(); put(m[3], 12280, value); run('active-word', m, 'active_word', (ARENA,))
    for disabled in (0, 1, 255):
        for global_value in (0, 1, 100, 255):
            for local in (0, 1, 100, 0xffffffff):
                for mode in (0, 1, 0xffffffff):
                    for index in (0, 31, 32, 0xffffffff):
                        m = initial(); m[1][3] = disabled; m[0][28] = global_value
                        put(m[1], 40, 0x80000001)
                        run('time-rule', m, 'time_rule', (local, mode, index))
    for scale in (0, 1, 1000, 48000, 48077, 0x7fffffff, 0x80000000, 0xffffffff):
        for value in edges:
            for operation in ('size_base', 'size_extra'):
                m = initial(); put(m[0], 36, scale); run('size-wrap', m, operation, (value,))
    for id_ in (*range(14), 0xffffffff):
        for divisor in (0, 1, 2, 100, 12000, 0x20000000, 0x80000000, 0xffffffff):
            m = initial(); put(m[0], 40, divisor)
            run('tempo', m, 'tempo', (id_, divisor)); run('tempo-global', m, 'tempo_global', (id_,))
    print('Selectors, parameter packing aliases, state pointers, size and tempo primitives compared.', flush=True)
    # Four native copy alignment combinations in each direction, with overlap,
    # exact self-copy, short loops and unaligned four-byte assembly packets.
    for count in (*range(17), 31, 32, 33, 127, 128, 129, 1023):
        for source_alignment in range(4):
            for destination_alignment in range(4):
                for direction in (-1, 0, 1):
                    source = ARENA+2048+source_alignment
                    destination = source if not direction else ARENA+2048+direction*9+destination_alignment
                    run('memmove-overlap', initial(), 'memmove', (destination, source, count), alignment=count&3)
    for alignment in range(4):
        for count in (0, 1, 2, 3, 1023, 1024, 1025, 4095, 0xffffffff):
            for callback in (0, 0x0201a9dc, 0x12345678, REGIONS['selector'][0]):
                if count == 0xffffffff and callback == 0: pass  # Native wrapped count becomes zero.
                m = initial(); put(m[2], 4, callback)
                mutations = ((CALLBACKS+4, 0, 4), (ARENA+32760, 0x98765432, 4)) if callback not in (0,0x0201a9dc) else ()
                run('clear-halfwords', m, 'clear_halfwords', (ARENA+8192+alignment, count),
                    mutations=mutations, alignment=alignment)
    # Scalar clear can overwrite the callback table itself; it is never reread.
    m = initial(); put(m[2], 4, 0x0201a9dc)
    run('clear-callback-alias', m, 'clear_halfwords', (CALLBACKS, 32))
    state = initial()
    for index in range(20):
        native = run('carried-move', state, 'memmove', (ARENA+1024+(index%5), ARENA+1020+(index%7), 135), carried=True)
        state = [bytearray(data) for data in native['memory']]
    print('Complete memmove and actual installed clear bodies compared, including overlap and carried state.', flush=True)
    wide_edges = (0, 1, 2, 3, 0xffffffff, 0x100000000, 0x100000001, 0x80000000,
                  0x7fffffffffffffff, 0x8000000000000000, 0xffffffff00000000, 0xffffffffffffffff)
    pairs = [(n, d) for n in wide_edges for d in wide_edges]
    rng = random.Random(0x331ec)
    pairs += [(rng.getrandbits(64), rng.getrandbits(64)) for _ in range(128)]
    pairs += [(rng.getrandbits(64), (1 << bit)+offset) for bit in range(64) for offset in (-1, 0, 1) if (1 << bit)+offset <= MASK64]
    for index, (numerator, divisor) in enumerate(pairs):
        args = (numerator&MASK32, numerator>>32, divisor&MASK32, divisor>>32)
        for signed_ in (False, True):
            operation = 'signed_divide' if signed_ else 'unsigned_divide'
            native = run('complete-divide', initial(), operation, args if signed_ else args+(ARENA+3 if index&1 else 0,), alignment=index&3)
            a, b = (signed(numerator,64), signed(divisor,64)) if signed_ else (numerator, divisor)
            expected = (0 if not b else abs(a)//abs(b)*(-1 if (a<0)!=(b<0) else 1))&MASK64
            assert native['result'] == (expected&MASK32, expected>>32)
            if not signed_ and index&1:
                remainder = (numerator if numerator>>32 == 0 else 0) if not divisor else numerator%divisor
                assert int.from_bytes(native['memory'][3][3:11], 'little') == remainder
    run('zero-divisor-high-numerator-remainder', initial(), 'unsigned_divide', (7,1,0,0,ARENA+3))
    for numerator in (*wide_edges, *(rng.getrandbits(64) for _ in range(48))):
        for divisor in (0, 1, 2, 3, 0x7fffffff, 0x80000000, 0xffffffff):
            run('signed-ratio', initial(), 'ratio', (numerator&MASK32, numerator>>32, divisor))
    print('Complete signed/unsigned division, optional remainders and signed Q16 ratio compared.', flush=True)
    return c

def source_files():
    names = {'firmware/src/hyperrig_effect_parameter_support.c', 'tools/effect_parameter_support_machine.py',
        'tools/verify_effect_parameter_support.py', 'tools/build_effect_parameter_support.py',
        'tests/test_effect_parameter_support_machine.py', 'tests/effect_parameter_support_sanitize.c',
        'firmware/src/hyperrig_effect_enable.c', 'research/input-manifest.json', 'upstream/pi32v2-isa/isa/pi32v2.toml'}
    names.update('upstream/pi32v2-isa/tools/hwtest/semantics/'+name+'.py' for name in ('s','b2','r','_r_util','v3'))
    for module in tuple(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path:
            path = Path(path).resolve()
            if path.suffix == '.py' and path.is_relative_to(ROOT): names.add(path.relative_to(ROOT).as_posix())
    pending = [ROOT/name for name in names if name.endswith('.c')]
    while pending:
        path = pending.pop()
        for include in re.findall(r'^\s*#\s*include\s+"([^"]+)"', path.read_text(), re.M):
            options = (path.parent/include, ROOT/'firmware/include'/include)
            header = next((p.resolve() for p in options if p.is_file()), None)
            if header is None: raise ValueError(f'unresolved repository C include {include}')
            name = header.relative_to(ROOT).as_posix()
            if name not in names: names.add(name); pending.append(header)
    return sorted(names)

def guards(library, program):
    memory = Memory(initial(), program); execute = library.hyperrig_effect_parameter_support_execute
    result = (U32*2)(0xdeadbeef, 0xdeadbeef); args = (U32*12)(ARENA, 1)
    def mapping(_, address, size, writable):
        try: return memory.pointer(address, size, writable)
        except ValueError: return None
    callback = MAP(mapping); io = IO(callback, CALL(), None, 1, 1000); count = 0
    for target, a, out, context in ((0,args,result,ctypes.byref(io)),
        (REGIONS['selector'][0],None,result,ctypes.byref(io)),
        (REGIONS['selector'][0],args,None,ctypes.byref(io)),
        (REGIONS['selector'][0],args,result,None),
        (REGIONS['selector'][0],args,result,ctypes.byref(IO()))):
        assert execute(target,a,out,context) == -200; count += 1
    args[0] = 40; assert execute(REGIONS['capability'][0],args,result,ctypes.byref(io)) == -202; count += 1
    args[0] = 0xffffffff; assert execute(REGIONS['pack'][0],args,result,ctypes.byref(io)) == -201; count += 1
    args[0] = 3; io.work_budget = 0
    assert execute(REGIONS['selector'][0],args,result,ctypes.byref(io)) == -203; count += 1
    args[0] = 1; args[1] = 0; args[2] = 2; io.work_budget = 2
    assert execute(REGIONS['signed_divide'][0],args,result,ctypes.byref(io)) == -203; count += 1
    args[0] = ARENA; args[1] = 1024; io.work_budget = 10000; memory.write(CALLBACKS+4,0x12345678,4)
    assert execute(REGIONS['clear_halfwords'][0],args,result,ctypes.byref(io)) == -200; count += 1
    io.service_budget = 0
    assert execute(REGIONS['clear_halfwords'][0],args,result,ctypes.byref(io)) == -203; count += 1
    assert tuple(result) == (0xdeadbeef,0xdeadbeef)
    return count

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--fixtures', type=Path); p.add_argument('--mini-image', type=Path)
    args = p.parse_args()
    if args.output.exists() or args.fixtures and args.fixtures.exists(): p.error('use fresh output paths')
    fixtures = args.fixtures.open('w+b') if args.fixtures else None
    try:
        c = corpus(Comparison(load_library(args.library), fixtures)); c.finish()
    finally:
        if fixtures: fixtures.close()
    invalid = guards(c.library, c.program); code = set(c.program.code)
    new = {pc for pc in code if any(a <= pc < b for a,b in REGIONS.values())}
    missing = sorted(new-c.coverage)
    if missing: raise AssertionError(('unclassified parameter-support gaps', [hex(pc) for pc in missing]))
    app = (ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes(); mini_binding = None
    if args.mini_image:
        from hyperrig.jieli import unpack_app
        raw = args.mini_image.read_bytes(); assert hashlib.sha256(raw).hexdigest() == MINI
        mini = unpack_app(raw)[2]['app.bin']
        for a,b in (REGIONS|REUSED|STATIC).values(): assert region_bytes(mini,a,b) == region_bytes(app,a,b)
        mini_binding = {'image_sha256':MINI,'all_complete_functions_and_tables_identical':True}
    report = {'schema':1,'project':'HyperRig','result':'pass','original_image_sha256':PINNED,
        'scope':'complete parameter support, actual signed/unsigned64 division, memmove and installed clear',
        'functions':{name:{'start':a,'end_exclusive':b,'bytes_sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            'instructions':sum(a <= pc < b for pc in code),'visited':sum(a <= pc < b for pc in c.coverage)}
            for name,(a,b) in (REGIONS|REUSED).items()},
        'static_data':{name:{'start':a,'end_exclusive':b,'sha256':hashlib.sha256(region_bytes(app,a,b)).hexdigest()}
            for name,(a,b) in STATIC.items()},
        'comparisons':c.counts,'total_comparisons':sum(c.counts.values()),'original_instruction_packets':c.steps,
        'instruction_coverage':{'new_decoded':len(new),'new_visited':len(new&c.coverage),'unvisited_new':missing,
            'all_decoded':len(code),'all_visited':len(code&c.coverage),'unvisited_all':sorted(code-c.coverage)},
        'actual_internal_entries':{hex(k):v for k,v in sorted(c.internal.items())},
        'carried_calls':c.carried,'callback_mutation_cases':c.mutating,'external_clear_calls':c.calls,
        'api_guard_checks':invalid,'sanitizer_fixture_count':c.fixture_count,
        'outputs_and_state_sha256':c.digest.hexdigest(),'mini_v4_binding':mini_binding,
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files()},
        'library_sha256':hashlib.sha256(args.library.read_bytes()).hexdigest(),
        'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'limitations':['alternate clear callbacks remain explicit mutable platform services',
            'REP uses the pinned model count including zero; no new processor measurement is claimed',
            'capability indices are bounded to the authenticated40-byte table',
            'work budgets count portable accesses and division iterations, not native cycles',
            'scalar arithmetic accepts every raw input pattern, while mapped spans determine memory validity']}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('result','total_comparisons','instruction_coverage')}),flush=True)

if __name__ == '__main__': main()
