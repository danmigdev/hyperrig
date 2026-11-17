"""Compare complete sample engines and constructor/caller joins offline."""
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
from effect_sample_processing_machine import (EffectSampleProcessingProgram, REGIONS, ENTRIES,
    STATIC, MAPPED, DIRECT_SITES, CONSTRUCTOR, RAM, SAMPLES, ARENA, ROOT, offset,
    carry_preparation_into_audio)
from verify_effect_processing import (SOURCES as PROCESSING_SOURCES, U32, MAP, CALL,
    Recording as ProcessingRecording, Script as ProcessingScript, put, EFFECTS, CONTROL, CONFIG, AUTOMATION,
    boundary_digest)
from verify_effect_model_construction import SOURCES as CONSTRUCTION_SOURCES
from verify_audio_task import Task

SOURCES = tuple(dict.fromkeys((*[x for x in PROCESSING_SOURCES if not x.endswith('/hyperrig_effect_processing.c')],
    *CONSTRUCTION_SOURCES, 'firmware/src/hyperrig_effect_sample_processing.c')))
FROZEN_PROCESSING = 'f4e475acc0f797673740ac0428811d3b83129b4356878606484c1b54c81421b2'
MARKER = '/* New mapped sample engines. The preceding caller derivative is mechanically checked. */'
SCALAR = {'capture_probe', 'cost', 'extra_cost', 'q16', 'exp', 'ir_active', 'ir_accelerated',
          'peak16', 'individual', 'grouped'}
INVARIANT_GAPS = {
    'The energy signed32 range test excludes [-0x7fffffff,0x7fffffff] before normalization; its exact unsigned64 magnitude is therefore at least 0x80000000, so the smaller-magnitude bypass cannot execute.':
        [0x01c0b718, 0x01c0b71c, 0x01c0b71e, 0x01c0b720, 0x01c0b724, 0x01c0b726],
    'The difference signed32 range test excludes [-0x7fffffff,0x7fffffff] before normalization; its exact unsigned64 magnitude is therefore at least 0x80000000, so the smaller-magnitude bypass cannot execute.':
        [0x01c0b800, 0x01c0b804, 0x01c0b806, 0x01c0b808, 0x01c0b80a, 0x01c0b80c, 0x01c0b812, 0x01c0b814],
    'The curvature signed32 range test excludes [-0x7fffffff,0x7fffffff] before normalization; its exact unsigned64 magnitude is therefore at least 0x80000000, so the smaller-magnitude bypass cannot execute.':
        [0x01c0b8ea, 0x01c0b8ee, 0x01c0b8f0, 0x01c0b8f4],
    'The full entry returns unless signed64 energy is at least positive 0x40000000 or 0x400000; its cached high word remains unchanged before the negative-energy sign flip.':
        [0x01c0b744],
    'A zero candidate makes the prior floating division/product nonfinite; pinned ftoi saturates to INTMIN or INTMAX, both rejected by the unsigned phase gate before this zero-candidate store.':
        [0x01c0ba0c],
}


class IO(ctypes.Structure):
    _fields_ = [('map', MAP), ('call', CALL), ('opaque', ctypes.c_void_p), ('work_budget', U32)]


def state_hash(memory):
    value = 14695981039346656037
    for data in memory:
        for byte in data: value = ((value ^ byte)*1099511628211)&0xffffffffffffffff
    return value


class Recording(ProcessingRecording):
    def __init__(self, script): super().__init__(script); self.hashes = []
    def __call__(self, target, args, backend):
        before = state_hash(backend.snapshot()); result = super().__call__(target, args, backend)
        self.hashes.append((before, state_hash(backend.snapshot()))); return result


class Replay:
    def __init__(self, path, program):
        self.file = path.open('xb'); self.count = 0
        self.file.write(b'HRSMP001'); self.words(0, len(program.static_regions)+1)
        for key, (a, b) in program.static_regions.items():
            self.words(a, b-a); self.file.write(program.data[key])
        self.words(0x02000120, len(program.app)); self.file.write(program.app)
    def words(self, *values):
        self.file.write(struct.pack('<'+'I'*len(values), *(v&0xffffffff for v in values)))
    def writes(self, changes):
        self.words(len(changes))
        for address, value, size in changes: self.words(address, value, value >> 32, size)
    def case(self, session, mode, entry, args, status, value, before, after, events, task_before, task_after):
        self.words(mode, entry, len(args), *args, *([0]*(12-len(args))), status, value,
                   session.backend.io.work_budget, session.chain, session.alignment,
                   *task_before, *task_after, len(session.mapped))
        for (base, size), old, new in zip(session.mapped, before, after):
            self.words(base, size); self.file.write(old); self.file.write(new)
        self.writes(session.pending); self.words(len(events))
        hashes = session.recording.hashes[-len(events):] if events else []
        for (target, arguments, result, writes), (old_hash, new_hash) in zip(events, hashes):
            self.words(target, len(arguments), *arguments, *([0]*(12-len(arguments))), result)
            self.file.write(struct.pack('<2Q', old_hash, new_hash)); self.writes(writes)
        self.count += 1
    def close(self): self.file.seek(8); self.words(self.count); self.file.close()


def check_derivative():
    old_path = ROOT/'firmware/src/hyperrig_effect_processing.c'
    if hashlib.sha256(old_path.read_bytes()).hexdigest() != FROZEN_PROCESSING:
        raise ValueError('frozen processing input changed')
    old = old_path.read_text()
    old = old.replace('"hyperrig/hyperrig_effect_processing.h"',
        '"hyperrig/hyperrig_effect_sample_processing.h"\n#include "hyperrig/hyperrig_effect_model_construction.h"')
    for suffix in ('io', 'execute', 'stage', 'audio_resume'):
        old = old.replace('hyperrig_effect_processing_'+suffix, 'hyperrig_effect_sample_processing_'+suffix)
    old = old.replace('uint32_t sp;', 'uint32_t sp,remaining;')
    old = old.replace('} access;', '} access;\nstatic void sample_engine(access *,uint32_t,const uint32_t *);')
    old = old.replace('a.io=io;a.error=0;a.sp=', 'a.io=io;a.error=0;a.remaining=io->work_budget;a.sp=')
    changes = {
        'CALL1(a,UINT32_C(0x01c18f90),primary)': 'sample_engine(a,UINT32_C(0x01c18f90),(const uint32_t[1]){primary})',
        'CALL1(a,UINT32_C(0x01c18f90),secondary)': 'sample_engine(a,UINT32_C(0x01c18f90),(const uint32_t[1]){secondary})',
        'CALL1(a,UINT32_C(0x01c0b5d6),effect)': 'sample_engine(a,UINT32_C(0x01c0b5d6),(const uint32_t[1]){effect})',
        'service(a,UINT32_C(0x01c0ba14),(uint32_t[8]){samples,dest,count,saved_a,step_a,0,0,2},8)':
            'sample_engine(a,UINT32_C(0x01c0ba14),(uint32_t[8]){samples,dest,count,saved_a,step_a,0,0,2})',
        'service(a,UINT32_C(0x01c0ba14),(uint32_t[8]){samples,dest,count,saved_a,step_a,gain_a,gain_b,secondary_live},8)':
            'sample_engine(a,UINT32_C(0x01c0ba14),(uint32_t[8]){samples,dest,count,saved_a,step_a,gain_a,gain_b,secondary_live})',
        'CALL4(a,UINT32_C(0x01c0bbce),old_width,secondary_live,a->sp+164,a->sp+160)':
            'sample_engine(a,UINT32_C(0x01c0bbce),(uint32_t[4]){old_width,secondary_live,a->sp+164,a->sp+160})',
        'CALL4(a,UINT32_C(0x01c0bbce),new_width&255,secondary_live,a->sp+156,a->sp+152)':
            'sample_engine(a,UINT32_C(0x01c0bbce),(uint32_t[4]){new_width&255,secondary_live,a->sp+156,a->sp+152})',
        'CALL1(a,UINT32_C(0x01c0bd8c),effect)': 'sample_engine(a,UINT32_C(0x01c0bd8c),(uint32_t[1]){effect})',
        'service(a,UINT32_C(0x01c08b3e),args,9)': 'sample_engine(a,UINT32_C(0x01c08b3e),args)',
    }
    for before, after in changes.items():
        if old.count(before) != 1: raise ValueError('processing join replacement not unique: '+before)
        old = old.replace(before, after)
    old = old.replace('default:return -202;',
        'case UINT32_C(0x01c08b3e):case UINT32_C(0x01c0b5d6):case UINT32_C(0x01c0ba14):\n'
        '    case UINT32_C(0x01c0bbce):case UINT32_C(0x01c0bd8c):case UINT32_C(0x01c18f90):case UINT32_C(0x01c19448):\n'
        '        sample_engine(&a,entry,arguments);break;\n    default:return -202;')
    old = old.replace('*result=value;return a.error;', 'if(!a.error)*result=value;\n    return a.error;')
    actual = (ROOT/'firmware/src/hyperrig_effect_sample_processing.c').read_text().split(MARKER)[0].rstrip()
    if old.rstrip() != actual:
        import difflib
        raise ValueError('processing derivative differs outside joins:\n'+''.join(difflib.unified_diff(
            old.rstrip().splitlines(True), actual.splitlines(True)))[:4000])
    return {'frozen_sha256': FROZEN_PROCESSING, 'native_direct_sites': len(DIRECT_SITES),
            'textual_replacements': len(changes), 'result': 'pass'}


def setword(memory, address, value, size=4, *, mapped=MAPPED):
    for (base, n), data in zip(mapped, memory):
        if base <= address <= address+size <= base+n:
            put(data, address-base, value, size); return
    raise ValueError(f'fixture write outside mapped sample bytes {address:#x}')


def baseline(seed=1, *, mapped=MAPPED):
    rng = random.Random(seed); memory = [bytearray(n) for _, n in mapped]
    for (base, _), data in zip(mapped, memory):
        if base in (SAMPLES, ARENA):
            for i in range(0, len(data), 4): put(data, i, rng.getrandbits(32))
    return memory


class Script(ProcessingScript):
    def __init__(self, mutations=(), returns=(), clocks=(), audio=False):
        super().__init__(mutations, returns, clocks); self.audio = audio
        from verify_audio_task import Script as AudioScript
        self.platform = AudioScript()
    def __call__(self, target, args, memory):
        from effect_processing_machine import SERVICES
        if self.audio and (target not in SERVICES or target == 0x01c04862):
            return self.platform(target, args, memory)
        return super().__call__(target, args, memory)


class Backend:
    def __init__(self, program, memory, mapped, script, alignment=0, holes=()):
        self.program = program; self.mapped = mapped; self.holes = holes
        self.allocations = [(ctypes.c_uint8*(len(data)+alignment))() for data in memory]
        self.arrays = []
        for allocation, data in zip(self.allocations, memory):
            array = (ctypes.c_uint8*len(data)).from_address(ctypes.addressof(allocation)+alignment)
            array[:] = data; self.arrays.append(array)
        self.tables = {key: (ctypes.c_uint8*len(raw)).from_buffer_copy(raw) for key, raw in program.data.items()}
        self.rom = (ctypes.c_uint8*len(program.app)).from_buffer_copy(program.app)
        self.script = script; self.calls = []; self.errors = []; self.borrowed = None
        self.io = IO(MAP(self.map), CALL(self.call), None, 1000000)
    def map(self, opaque, address, size, writable):
        if any(address < b and address+size > a for a, b in self.holes): return None
        for (base, n), data in zip(self.mapped, self.arrays):
            if base <= address <= address+size <= base+n: return ctypes.addressof(data)+address-base
        if not writable:
            for key, (base, end) in self.program.static_regions.items():
                if base <= address <= address+size <= end: return ctypes.addressof(self.tables[key])+address-base
            if 0x02000120 <= address <= address+size <= 0x02000120+len(self.rom):
                return ctypes.addressof(self.rom)+address-0x02000120
        return None
    def locate(self, address, size, writable):
        pointer = self.map(None, address, size, writable)
        if pointer is None and self.borrowed:
            pointer = self.borrowed.contents.map(self.borrowed.contents.opaque, address, size, writable)
        if pointer is None: raise ValueError(f'callback escaped sample map {address:#x}/{size}')
        return pointer
    def read(self, address, size): return int.from_bytes(ctypes.string_at(self.locate(address, size, 0), size), 'little')
    def write(self, address, value, size):
        ctypes.memmove(self.locate(address, size, 1), (value&((1 << (8*size))-1)).to_bytes(size, 'little'), size)
    def snapshot(self): return tuple(bytes(data) for data in self.arrays)
    def call(self, opaque, target, args, count, borrowed):
        try:
            self.borrowed = borrowed; words = tuple(args[i] for i in range(count))
            self.calls.append((target, words, boundary_digest(target, words, self,
                hashlib.sha256(b''.join(self.snapshot())).hexdigest())))
            value = self.script(target, words, self)&0xffffffff; self.borrowed = None; return value
        except Exception as exc:
            self.errors.append(str(exc)); self.borrowed = None; return 0


class Corpus:
    def __init__(self, library, replay=None):
        self.program = EffectSampleProcessingProgram(); self.lib = ctypes.CDLL(str(Path(library).resolve()))
        self.lib.hyperrig_effect_sample_processing_execute.argtypes = [U32, ctypes.POINTER(U32), ctypes.POINTER(U32), ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_sample_processing_prepare.argtypes = [U32, ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_sample_processing_stage.argtypes = [U32, U32, U32, ctypes.POINTER(IO)]
        self.lib.hyperrig_effect_sample_processing_audio_resume.argtypes = [ctypes.POINTER(Task), U32, U32, ctypes.POINTER(IO)]
        self.cases = self.chains = self.steps = self.preparations = self.carried = 0
        self.visited = set(); self.real = {}; self.rom_reads = set(); self.labels = []; self.services = {}
        self.digest = hashlib.sha256(); self.replay = Replay(replay, self.program) if replay else None
    def session(self, memory, *, mapped=MAPPED, alignment=0, mutations=(), returns=(), clocks=(), audio=False):
        self.chains += 1
        return Session(self, memory, mapped, alignment, mutations, returns, clocks, audio)


class Session:
    def __init__(self, corpus, memory, mapped, alignment, mutations, returns, clocks, audio):
        self.corpus = corpus; self.mapped = mapped; self.chain = corpus.chains; self.alignment = alignment
        self.native = list(map(bytearray, memory)); self.pending = []; self.invocations = 0
        self.backend = Backend(corpus.program, memory, mapped, Script(mutations, returns, clocks, audio), alignment)
        self.recording = Recording(Script(mutations, returns, clocks, audio)); self.task = Task(); self.audio = None
    def write(self, address, value, size=4):
        setword(self.native, address, value, size, mapped=self.mapped); self.backend.write(address, value, size)
        self.pending.append((address, value&((1 << (8*size))-1), size))
        if self.audio: carry_preparation_into_audio(self.audio, self.native)
    def invoke(self, label, name, args, *, budget=1000000):
        c = self.corpus; b = self.backend; b.io.work_budget = budget
        before = b.snapshot(); call_start = len(b.calls); event_start = len(self.recording.events)
        task_before = tuple(getattr(self.task, key) for key, _ in Task._fields_); value = U32(0)
        if name == 'prepare':
            paused = None if self.audio is None else (self.audio.pc, dict(self.audio.regs),
                list(self.audio.returns), repr(self.audio.frames), dict(self.audio.else_skips))
            expected = c.program.prepare(self.native, args[0], mapped=self.mapped)
            status = c.lib.hyperrig_effect_sample_processing_prepare(args[0], ctypes.byref(b.io)); mode = 0; entry = CONSTRUCTOR
            c.preparations += 1; calls = expected['calls']; real = expected['internal_calls']
            if self.audio:
                carry_preparation_into_audio(self.audio, expected['memory'])
                assert paused == (self.audio.pc, dict(self.audio.regs), list(self.audio.returns),
                                  repr(self.audio.frames), dict(self.audio.else_skips)), (label, 'paused private control')
        elif name == 'audio':
            if self.audio is None: self.audio = c.program.audio.machine(self.native, self.recording)
            old_calls = len(self.audio.calls); old_steps = self.audio.steps
            old_real = len(self.audio.real_calls); old_internal = len(self.audio.internal_calls)
            expected = self.audio.resume(*args)
            status = c.lib.hyperrig_effect_sample_processing_audio_resume(ctypes.byref(self.task), *args, ctypes.byref(b.io))
            expected['status'] = expected['reason']; expected['steps'] -= old_steps
            calls = expected['calls'][old_calls:]; real = self.audio.real_calls[old_real:]+self.audio.internal_calls[old_internal:]
            mode = 3; entry = 0
            assert tuple(getattr(self.task, key) for key, _ in Task._fields_) == expected['task'], (label, 'task control')
        else:
            expected = c.program.execute(self.native, name, args, self.recording, mapped=self.mapped)
            if name == 'stage':
                status = c.lib.hyperrig_effect_sample_processing_stage(*args, ctypes.byref(b.io)); mode = 2
            else:
                status = c.lib.hyperrig_effect_sample_processing_execute(ENTRIES[name], (U32*12)(*args), ctypes.byref(value), ctypes.byref(b.io)); mode = 1
            entry = ENTRIES[name]; calls = expected['calls']; real = expected['real_calls']
            if name in SCALAR: assert value.value == expected['value'], (label, 'scalar')
        assert status == expected.get('status', 0) and not b.errors, (label, 'status', status, expected.get('status', 0), b.errors)
        if b.snapshot() != expected['memory']:
            difference = [(hex(base+i), x, y) for (base, _), left, right in zip(self.mapped, expected['memory'], b.snapshot())
                          for i, (x, y) in enumerate(zip(left, right)) if x != y]
            raise AssertionError((label, 'public memory', difference[:32]))
        assert calls == b.calls[call_start:], (label, 'service order/state', calls, b.calls[call_start:])
        for old, new in zip(self.native, expected['memory']): old[:] = new
        c.cases += 1; c.steps += expected['steps']; c.visited |= expected['visited']; c.labels.append(label)
        c.rom_reads |= expected.get('rom_reads', set()); c.carried += self.invocations != 0; self.invocations += 1
        for target in real:
            target = target[0] if isinstance(target, tuple) else target; c.real[target] = c.real.get(target, 0)+1
        for target, *_ in calls: c.services[target] = c.services.get(target, 0)+1
        c.digest.update(json.dumps((label, name, args, status, calls)).encode())
        for data in expected['memory']: c.digest.update(data)
        if c.replay:
            c.replay.case(self, mode, entry, args, status, value.value, before, expected['memory'],
                self.recording.events[event_start:], task_before, tuple(getattr(self.task, key) for key, _ in Task._fields_))
        self.pending = []
        return expected


def basic_cases(corpus):
    for width in (0, 1, 25, 50, 75, 100, 101, 0xffffffff):
        for mode in (0, 1, 2):
            corpus.session(baseline(width), alignment=mode&1).invoke(f'width {width}/{mode}', 'width', (width, mode, ARENA, ARENA+4))
    for count in (0, 1, 2, 3, 4, 7, 16, 513):
        for mode in (0, 1, 2, 3):
            corpus.session(baseline(count)).invoke(f'mixer {count}/{mode}', 'mixer',
                (SAMPLES, SAMPLES+8192, count, 65536, -157&0xffffffff, 32768, 16384, mode))
    for stride in (3, 4, 5):
        for count in (0, 1, 2, 7, 32, 513):
            for residual in (0, 3):
                memory = baseline(count+stride)
                for i in range(16): setword(memory, ARENA+i*4, 0)
                for i in range(2): setword(memory, ARENA+i*stride*4, 1 << 28)
                corpus.session(memory, alignment=1).invoke(f'cascade {stride}/{count}/{residual}', 'cascade',
                    (SAMPLES+4, count, ARENA, stride, ARENA+256, ARENA+512, 2, 3, residual))
    for mode in (0, 1, 255):
        memory = baseline(mode)
        for off, value in enumerate((ARENA+8192, ARENA+4096, 4000, 17, 20, mode)):
            setword(memory, ARENA+4*off, value)
        corpus.session(memory, alignment=1).invoke(f'correlation {mode}', 'correlation', (ARENA,))
    for index in (0, 1, 2, 255):
        memory = baseline(index)
        setword(memory, EFFECTS+84, ARENA+8192); setword(memory, EFFECTS+288, 23)
        setword(memory, EFFECTS+308, 23 << 17); setword(memory, EFFECTS+396, 123)
        setword(memory, EFFECTS+407, index, 1)
        corpus.session(memory, alignment=1).invoke(f'update {index}', 'update', (EFFECTS,))
    for phase in (0, 0x40000000, 0x80000000, 0xc0000000):
        for weight in (0, 0x20000000, 0x40000000):
            memory = baseline(phase+weight)
            values = (SAMPLES, ARENA+8192, 2015, phase, 123456, 23 << 17, 60 << 16, 1 << 16,
                      40000, 20000, -7&0xffffffff, 11, weight, 2, 0, 1 << 30, 65536)
            for i, v in enumerate(values): setword(memory, ARENA+4*i, v)
            corpus.session(memory, alignment=1).invoke(f'ring {phase}/{weight}', 'ring', (ARENA,))
    for mode in (0, 1):
        for energy in (0, 0x3fffff, 0x400000, 0x40000000, 0x7fffffffffffffff):
            memory = baseline(mode)
            for i, v in enumerate((1234567, 9876543, -7654321&0xffffffffffffffff, energy)):
                setword(memory, EFFECTS+364+8*i, v, 8)
            for off, v in ((308, 40 << 17), (328, 10 << 17), (332, 100 << 17),
                           (292, 0x80000000), (300, 0x20000001), (320, 0x20000000), (400, 0x3f000000)):
                setword(memory, EFFECTS+off, v)
            setword(memory, EFFECTS+409, mode, 1)
            corpus.session(memory, alignment=1).invoke(f'transition {mode}/{energy}', 'transition', (EFFECTS,))


def alias_cases(corpus):
    # A whole native Q28 call caches coefficients and all four histories. Its
    # output can overwrite both those bytes and a later section's inputs.
    for stride in (3, 4, 5):
        for coefficient_offset, history_offset, residue_offset in (
            (0, 2048, 3072), (16, 40, 68), (2048, 4, 3072),
            (2048, 2048+80, 12), (64, 128, 192)):
            for residual in (0, 7):
                memory = baseline(100+stride+history_offset)
                corpus.session(memory, alignment=1).invoke(
                    f'cached cascade alias {stride}/{coefficient_offset}/{history_offset}/{residue_offset}/{residual}',
                    'cascade', (SAMPLES+4, 31, SAMPLES+4+coefficient_offset, stride,
                                SAMPLES+4+history_offset, SAMPLES+4+residue_offset, 3, 7, residual))
    for sections, enabled in ((0, 0xffffffff), (1, 0), (33, 0), (34, 0x80000001)):
        corpus.session(baseline(sections)).invoke(f'section-bit wrap {sections}/{enabled}', 'cascade',
            (SAMPLES+4, 4, ARENA, 5, ARENA+4096, ARENA+8192, sections, enabled, 0xffffffff))
    for count in (0, 0x40000000, 0x40000001, 0x80000002, 0xffffffff):
        memory = baseline(count)
        corpus.session(memory, alignment=1).invoke(f'raw wrapped capture count {count}', 'cascade',
            (4, count, ARENA, 5, ARENA+4096, ARENA+8192, 0, 0, 0))
    for count in (1, 2, 3, 7):
        memory = baseline(count)
        for address, value in ((0xfffffffc, 0x81234567), (0, 0x7fffffff), (4, 0x12345678),
                               (8, 0xfedcba98), (12, 0x80000000), (16, 0x13579bdf), (20, 0x2468ace0)):
            setword(memory, address, value)
        session = corpus.session(memory, alignment=1)
        session.invoke(f'cascade sample pointer wrap {count}', 'cascade',
            (0xfffffffc, count, ARENA, 5, ARENA+4096, ARENA+8192, 2, 3, 1))
        session.invoke(f'mixer sample pointer wrap {count}', 'mixer',
            (0xfffffffc, ARENA+16384, count, 0xf0000000, 0x70000000, 0x7fffffff, 0x80000000, count%3))
    for offset in (0, 4, -4, 12):
        for mode in (0, 1, 2, 255):
            corpus.session(baseline(offset+mode), alignment=1).invoke(f'mixer overlap {offset}/{mode}', 'mixer',
                (SAMPLES+16, SAMPLES+16+offset, 35, 0x7fffffff, 0x80000000, 0xffffffff, 0x80000000, mode))
    for width in (0, 1, 37, 100, 0xffffffff):
        for mode in (0, 1):
            corpus.session(baseline(width), alignment=1).invoke(f'width aliased outputs {width}/{mode}',
                'width', (width, mode, ARENA+1, ARENA+1))
    for samples, ring, index, blocks in ((ARENA, ARENA+8192, 2039, 2),
        (SAMPLES, ARENA, 0, 2), (ARENA, ARENA, 0, 3), (SAMPLES, ARENA+8192, 3000, 1)):
        memory = baseline(index)
        values = (samples, ring, index, 0x87654321, 0x07ffffff, 0x80001234, 0xfedcba98, 0x80005555,
                  0xffffffff, 0x80000000, 0x7fffffff, 0xffffffff, 0x81234567, blocks, 0x80000000, 0x7fffffff, 0xffffffff)
        for i, value in enumerate(values): setword(memory, ARENA+4*i, value)
        corpus.session(memory, alignment=1).invoke(f'ring descriptor/input alias {samples}/{ring}/{index}/{blocks}', 'ring', (ARENA,))
    for mode in (0, 1):
        for count in (2, 4, 18, 20, 514):
            memory = baseline(count+mode)
            values = (ARENA+8192, ARENA+24, 10000, 0xffffffff, count, mode)
            for i, value in enumerate(values): setword(memory, ARENA+4*i, value)
            corpus.session(memory, alignment=1).invoke(f'correlation delayed/output alias {mode}/{count}', 'correlation', (ARENA,))
    for index in (0, 1, 2, 255):
        memory = baseline(index)
        setword(memory, EFFECTS+84, EFFECTS-1024); setword(memory, EFFECTS+288, 97)
        setword(memory, EFFECTS+308, 0xffffffff); setword(memory, EFFECTS+396, 0x80000001)
        setword(memory, EFFECTS+407, index, 1)
        corpus.session(memory, alignment=1).invoke(f'update effect/ring alias {index}', 'update', (EFFECTS,))


def numerical_cases(corpus):
    rng = random.Random(0x5710814)
    for case in range(96):
        memory = baseline(case); mode = case%3
        energy = (0x40000000, 0x7fffffff, 0x80000000, 0x100000000,
                  0x7fffffffffffffff, 0xffffffffffffffff)[case%6]
        correlations = [rng.getrandbits(64) for _ in range(3)]
        if case%4 == 0: correlations = [rng.randrange(1 << 28) for _ in range(3)]
        if case%8 == 1: correlations[1] = sum(correlations[::2])//2
        for i, value in enumerate((*correlations, energy)): setword(memory, EFFECTS+364+8*i, value, 8)
        period = (40 << 17, 0, 0xffffffff, 10 << 17, 100 << 17, 0x80000000)[case%6]
        values = ((308, period), (328, (0, 10 << 17, 0x80000000)[case%3]),
                  (332, (100 << 17, 0, 0x7fffffff)[case%3]),
                  (292, (0, 0x80000000, 0x76000000, 0x8a000000)[case%4]),
                  (300, (0, 0x40000000)[case%2]), (320, rng.getrandbits(32)),
                  (400, (0x3f000000, 0xbf800000, 0x7f7fffff, 0x00800000)[case%4]))
        for off, value in values: setword(memory, EFFECTS+off, value)
        setword(memory, EFFECTS+409, mode, 1)
        corpus.session(memory, alignment=case%4).invoke(f'wide transition {case}', 'transition', (EFFECTS,))
    for case in range(24):
        memory = baseline(case); descriptor = ARENA+1
        values = [SAMPLES+1, ARENA+8193, rng.randrange(2048), rng.getrandbits(32),
                  rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32),
                  rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32),
                  rng.getrandbits(32), (1, 2, 33)[case%3], rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32)]
        if case%4 == 0:
            values[3] = values[4] = values[12] = 0; values[14] = 0; values[15] = 1 << 30; values[16] = 65536
        if case%4 == 1:
            values[3] = 0x7fffffff; values[4] = 0; values[12] = 1 << 30
            values[14] = 0; values[15] = 1 << 30; values[16] = 131072
        for i, value in enumerate(values): setword(memory, descriptor+4*i, value)
        session = corpus.session(memory, alignment=case%4)
        session.invoke(f'raw ring arithmetic {case}', 'ring', (descriptor,))
        session.write(descriptor+40, rng.getrandbits(32))
        session.invoke(f'carried raw ring arithmetic {case}', 'ring', (descriptor,))
    for case in range(24):
        memory = baseline(case)
        count = (1, 3, 4, 31, 128, 1025)[case%6]
        stride = (3, 4, 5, 2, 6, 0)[case%6]
        session = corpus.session(memory, alignment=case%4)
        session.invoke(f'raw cascade arithmetic {case}', 'cascade',
            (SAMPLES+4, count, ARENA+1, stride, ARENA+1025, ARENA+2049, case%7, rng.getrandbits(32), rng.getrandbits(32)))
        session.invoke(f'raw mixer arithmetic {case}', 'mixer',
            (SAMPLES+4, SAMPLES+8196, count, rng.getrandbits(32), rng.getrandbits(32),
             rng.getrandbits(32), rng.getrandbits(32), case%4))


def initialize(memory, effect, kind, seed=1, rate=48000, mode=0, *, mapped=MAPPED):
    rng = random.Random(seed)
    def store(off, value, size=4): setword(memory, effect+off, value, size, mapped=mapped)
    for off in range(288, 480, 4): store(off, rng.getrandbits(32))
    for off, value, width in ((0, kind, 1), (1, 1, 1), (2, 1, 1), (4, 0, 1), (6, mode, 1),
                             (10, 0, 1), (11, 0, 1), (12, 0, 1), (13, 0, 1),
                             (84, ARENA+8192, 4), (88, 2048, 4), (476, 0, 4)):
        store(off, value, width)
    for off, value in ((8, rate), (12, 1200), (36, rate), (40, SAMPLES+8192), (44, SAMPLES+8192)):
        setword(memory, CONFIG+off, value, mapped=mapped)
    params = {25: (0, 0, 50, 25, 0, 0, 50), 36: (0, 0, 0, 0, 0, 0, 0), 37: (0, 0, 0, 0, 0, 0, 0)}[kind]
    for i, value in enumerate(params): store(70+2*i, value, 2)
    if kind == 25:
        # Existing stream history and ownership fields are fixture state; every
        # newly calculated parameter/coefficient is produced by the constructor.
        for off, value in ((288, 0), (292, 0x80000000), (300, 0), (336, 65536), (340, 32768),
                           (344, 65536), (348, 32768), (352, 0), (356, 0), (360, 0),
                           (364, 0), (368, 0), (372, 0), (376, 0), (380, 0), (384, 0),
                           (388, 0), (392, 0), (396, 0), (412, 0), (416, 0)):
            store(off, value)
        for off, value in ((404, 0), (405, 0), (406, 0), (407, 0), (408, 0), (409, 0),
                           (420, 50), (421, 0), (424, 50), (425, 0), (426, 0)):
            store(off, value, 1)


def constructed_cases(corpus):
    for kind in (25, 36, 37):
        for case in range(6):
            memory = baseline(kind+case)
            initialize(memory, EFFECTS, kind, case, (24000, 44100, 48000, 48077, 96000, 192000)[case], case%3)
            session = corpus.session(memory)
            session.invoke(f'constructor produced type {kind}/{case}', 'prepare', (EFFECTS,))
            for step in range(3):
                if step:
                    session.write(EFFECTS+70+2*((case+step)%7), (step*13 if kind == 25 else step*3), 2)
                    session.invoke(f'changed constructor type {kind}/{case}/{step}', 'prepare', (EFFECTS,))
                session.invoke(f'constructed dispatcher {kind}/{case}/{step}', 'dispatch',
                    (EFFECTS, SAMPLES, (16, 32, 128)[step], 1))
                session.invoke(f'constructed individual {kind}/{case}/{step}', 'individual',
                    (0, SAMPLES, (16, 32, 128)[step]))


def routing_cases(corpus, cases=range(6)):
    from verify_dsp_stage import baseline as stage_baseline
    for case in cases:
        memory = baseline(case); memory[0][:] = stage_baseline(case)[0]
        for side in range(2):
            setword(memory, CONTROL+14+side, 3, 1)
            for slot, kind in enumerate((25, 36, 37)):
                setword(memory, CONTROL+348+side*10+slot, slot, 1)
                initialize(memory, EFFECTS+480*slot, kind, case)
                setword(memory, EFFECTS+480*slot+4, slot%2+1 if case%2 else 0, 1)
        mutations = ((-0x01c04862, EFFECTS+72, 17, 2), (-0x01c04862, EFFECTS+480+72, 3, 2)) if case%2 else ()
        if mutations:
            setword(memory, 0x01c34198, 0x01c04862); setword(memory, 0x01c34444, 1000000)
        session = corpus.session(memory, mutations=mutations)
        for slot in range(3): session.invoke(f'routed preparation {case}/{slot}', 'prepare', (EFFECTS+480*slot,))
        for step in range(3):
            session.invoke(f'actual stage left {case}/{step}', 'stage', (0, SAMPLES, 128))
            session.invoke(f'actual stage right {case}/{step}', 'stage', (1, SAMPLES, 128))
            session.write(EFFECTS+480*step+72, 3+step*2, 2)
            session.invoke(f'routed changed preparation {case}/{step}', 'prepare', (EFFECTS+480*step,))


def audio_cases(corpus, cases=range(4)):
    import verify_audio_task as task
    from audio_task_machine import ARENA as AUDIO_ARENA
    from verify_dsp_stage import baseline as stage_baseline
    for case in cases:
        memory = task.baseline(case, mode=case%2+1); ram = memory[0]; stage = stage_baseline(case)[0]
        for start, size in ((EFFECTS, 7680), (AUTOMATION, 3584), (CONTROL, 416),
                            (CONFIG, 56), (0x01c2f3a0, 1536), (0x01c32fa0, 144)):
            ram[start-RAM:start-RAM+size] = stage[start-RAM:start-RAM+size]
        for slot, kind in enumerate((25, 36, 37)):
            initialize(memory, EFFECTS+480*slot, kind, case, mapped=task.MAPPED)
            setword(memory, EFFECTS+480*slot+84, AUDIO_ARENA+8192, mapped=task.MAPPED)
        for side in range(2):
            setword(memory, CONTROL+14+side, 3, 1, mapped=task.MAPPED)
            for slot in range(3): setword(memory, CONTROL+348+side*10+slot, slot, 1, mapped=task.MAPPED)
        setword(memory, CONFIG+40, 0x01c341c4, mapped=task.MAPPED)
        setword(memory, CONFIG+44, 0x01c321ac, mapped=task.MAPPED)
        for i in range(2048): setword(memory, AUDIO_ARENA+8192+4*i, (i*0x354673)^0x81573921, mapped=task.MAPPED)
        session = corpus.session(memory, mapped=task.MAPPED, audio=True)
        for slot in range(3): session.invoke(f'audio real preparation {case}/{slot}', 'prepare', (EFFECTS+480*slot,))
        for step in range(4):
            session.invoke(f'actual sample task {case}/{step}', 'audio', (1, 1))
            if step < 3:
                session.write(EFFECTS+480*step+72, 3+step*2, 2)
                session.invoke(f'paused task coefficient change {case}/{step}', 'prepare', (EFFECTS+480*step,))


def dispatcher_edges(corpus):
    # Keep true constructor-produced controls distinct from mutable stream and
    # stereo routing history. These cases select the ten exact incoming sites.
    for width in (0, 50, 100):
        for secondary in (0, 1):
            for count in (1, 17, 31, 128):
                memory = baseline(width+secondary+count); initialize(memory, EFFECTS, 25)
                session = corpus.session(memory)
                session.invoke(f'stereo edge preparation {width}/{secondary}/{count}', 'prepare', (EFFECTS,))
                for address, value, size in ((CONTROL+10, 1, 1), (CONTROL+9, 100, 1),
                    (CONTROL+40, 1, 4), (CONFIG+20, 23, 4), (EFFECTS+416, 23, 4),
                    (EFFECTS+424, width, 1), (EFFECTS+425, secondary, 1),
                    (EFFECTS+421, secondary, 1), (EFFECTS+426, 0, 1)):
                    session.write(address, value, size)
                session.invoke(f'stereo exact sample joins {width}/{secondary}/{count}', 'dispatch',
                    (EFFECTS, SAMPLES, count, 1))
    for pitch in (-12, 12):
        memory = baseline(pitch); initialize(memory, EFFECTS, 25)
        setword(memory, EFFECTS+72, pitch, 2)
        session = corpus.session(memory)
        session.invoke(f'correlation transition preparation {pitch}', 'prepare', (EFFECTS,))
        # Two actual correlation bodies produce all four accumulators and the
        # iteration byte. Only the stream phase is positioned at its boundary.
        session.invoke(f'caller starts actual correlation {pitch}', 'dispatch', (EFFECTS, SAMPLES, 32, 1))
        session.invoke(f'second actual correlation {pitch}', 'update', (EFFECTS,))
        delta = session.backend.read(EFFECTS+296, 4)
        session.write(EFFECTS+292, 0x7fffffff if delta < 0x80000000 else 0)
        session.invoke(f'actual phase-boundary transition {pitch}', 'dispatch', (EFFECTS, SAMPLES, 32, 1))
    for kind in (36, 37):
        for alias in (288, 308, 352, 416):
            memory = baseline(alias); initialize(memory, EFFECTS, kind)
            session = corpus.session(memory)
            session.invoke(f'constructed alias preparation {kind}/{alias}', 'prepare', (EFFECTS,))
            session.invoke(f'constructed public coefficient/history alias {kind}/{alias}', 'dispatch',
                (EFFECTS, EFFECTS+alias, 32, 1))


def transition_edges(corpus):
    for magnitude in (1 << 31, (1 << 31)+1, 1 << 32, 1 << 46, (1 << 46)+1):
        for negative in (False, True):
            memory = baseline(magnitude)
            correlations = (4*magnitude, 0, 0) if negative else (0, 0, 4*magnitude)
            for i, value in enumerate((*correlations, 1 << 47)):
                setword(memory, EFFECTS+364+8*i, value, 8)
            for off, value in ((308, 40 << 17), (328, 10 << 17), (332, 100 << 17),
                               (292, 0), (300, 0), (320, 1 << 27), (400, 0x3f000000)):
                setword(memory, EFFECTS+off, value)
            corpus.session(memory, alignment=1).invoke(f'transition normalization threshold {magnitude}/{negative}',
                'transition', (EFFECTS,))
    for period in (10 << 17, 20 << 17):
        memory = baseline()
        for i, value in enumerate((1 << 30, 0, 0, 1 << 30)):
            setword(memory, EFFECTS+364+8*i, value, 8)
        for off, value in ((308, period), (328, 10 << 17), (332, 100 << 17),
                           (292, 0), (300, 0), (320, 1 << 27), (400, 0x3f000000)):
            setword(memory, EFFECTS+off, value)
        corpus.session(memory).invoke(f'transition lower-bound toggle {period}', 'transition', (EFFECTS,))
    for period in (0, 1, 0xffffffff):
        for phase in (0, 1):
            memory = baseline()
            for i, value in enumerate((0, 1 << 30, 0, 1 << 30)):
                setword(memory, EFFECTS+364+8*i, value, 8)
            for off, value in ((308, period), (328, 0), (332, 0), (292, phase),
                               (300, 0), (296, 0x13579bdf), (320, 1 << 27), (400, 0x3f000000)):
                setword(memory, EFFECTS+off, value)
            result = corpus.session(memory).invoke(f'zero candidate rejected by nonfinite phase {period}/{phase}',
                'transition', (EFFECTS,))
            assert 0x01c0b9d2 in result['visited'] and 0x01c0b9da in result['visited']
            assert 0x01c0b9f4 not in result['visited']


def api_checks(corpus):
    checks = []; lib = corpus.lib; program = corpus.program
    def check(label, entry, args, expected, *, budget=1000000, memory=None, holes=()):
        backend = Backend(program, baseline() if memory is None else memory, MAPPED, Script(), holes=holes)
        backend.io.work_budget = budget; result = U32(0xdeadbeef); before = backend.snapshot()
        status = lib.hyperrig_effect_sample_processing_execute(entry, (U32*12)(*args), ctypes.byref(result), ctypes.byref(backend.io))
        assert status == expected and not backend.errors, (label, status, expected, backend.errors)
        if status: assert result.value == 0xdeadbeef, (label, 'failed result publication')
        checks.append({'label': label, 'status': status, 'public_bytes_changed': before != backend.snapshot(),
                       'native_prefix_equivalence_claimed': False})
        return backend
    check('unknown raw entry', 0, (), -202)
    check('zero budget before width output', ENTRIES['width'], (0, 0, ARENA, ARENA+4), -203, budget=0)
    check('genuine zero-count mixer returns without mapping', ENTRIES['mixer'], (0xdead0000, 0xbad00000, 0, 0, 0, 0, 0, 0), 0, budget=0)
    check('private stack is not public sample storage', ENTRIES['cascade'],
          (0x30000004, 0, ARENA, 5, ARENA+256, ARENA+512, 0, 0, 0), -202)
    check('individual access cannot straddle address wrap', ENTRIES['mixer'],
          (0xfffffffe, ARENA, 1, 0, 0, 0, 0, 2), -201)
    check('width second mapping failure keeps earlier store', ENTRIES['width'],
          (50, 1, ARENA, ARENA+4), -201, holes=((ARENA+4, ARENA+8),))
    check('large raw mixer has a finite work stop', ENTRIES['mixer'],
          (SAMPLES, ARENA, 0xffffffff, 65536, 0, 0, 0, 2), -203, budget=17)
    memory = baseline()
    for i, value in enumerate((SAMPLES, ARENA+8192, 0, 0, 123, 1 << 20, 1 << 22, 65536,
        65536, 65536, 0, 0, 0, 0, 0, 1 << 30, 65536)):
        setword(memory, ARENA+4*i, value)
    check('raw zero-block ring is guarded after visible writes', ENTRIES['ring'], (ARENA,), -203, budget=150, memory=memory)
    for count in (0, 1, 3, 0xffffffff):
        memory = baseline()
        for i, value in enumerate((ARENA+8192, ARENA+4096, 0, 1, count, 0)): setword(memory, ARENA+4*i, value)
        check(f'correlation raw count {count} is guarded, not a no-op', ENTRIES['correlation'],
              (ARENA,), -203, budget=55, memory=memory)
    check('inherited dispatcher count domain', ENTRIES['dispatch'], (EFFECTS, SAMPLES, 513, 1), -202)
    memory = baseline(); initialize(memory, EFFECTS, 36)
    setword(memory, 0x01c34198, ENTRIES['cascade'])
    check('loaded numerical token does not bypass inherited clock guard', ENTRIES['individual'],
          (0, SAMPLES, 32), -202, memory=memory)
    backend = Backend(program, baseline(), MAPPED, Script()); result = U32(0xdeadbeef); args = (U32*12)()
    for label, arguments, output, io in (('null arguments', None, ctypes.byref(result), ctypes.byref(backend.io)),
        ('null result', args, None, ctypes.byref(backend.io)), ('null IO', args, ctypes.byref(result), None)):
        assert lib.hyperrig_effect_sample_processing_execute(ENTRIES['mixer'], arguments, output, io) == -200
        checks.append({'label': label, 'status': -200, 'native_prefix_equivalence_claimed': False})
    backend.io.map = MAP()
    assert lib.hyperrig_effect_sample_processing_execute(ENTRIES['mixer'], args, ctypes.byref(result), ctypes.byref(backend.io)) == -200
    checks.append({'label': 'missing mapper', 'status': -200, 'native_prefix_equivalence_claimed': False})
    backend = Backend(program, baseline(), MAPPED, Script())
    assert lib.hyperrig_effect_sample_processing_prepare(EFFECTS, ctypes.byref(backend.io)) == -202
    checks.append({'label': 'unsupported constructor/sample type', 'status': -202, 'native_prefix_equivalence_claimed': False})
    memory = baseline(); initialize(memory, EFFECTS, 25)
    backend = Backend(program, memory, MAPPED, Script()); backend.io.work_budget = 0
    assert lib.hyperrig_effect_sample_processing_prepare(EFFECTS, ctypes.byref(backend.io)) == -203
    checks.append({'label': 'delegated constructor work guard', 'status': -203, 'native_prefix_equivalence_claimed': False})
    return checks


def source_paths():
    from hyperrig.jieli import unpack_app
    paths = set(SOURCES) | {'tools/effect_sample_processing_machine.py',
        'tools/verify_effect_sample_processing.py', 'tools/build_effect_sample_processing.py',
        'tests/test_effect_sample_processing_machine.py', 'tests/effect_sample_processing_sanitize.c',
        'firmware/src/hyperrig_effect_processing.c', 'research/input-manifest.json',
        'upstream/pi32v2-isa/isa/pi32v2.toml', 'upstream/pi32v2-isa/docs/SOURCES.md'}
    for name in ('s.py', 'b2.py', 'r.py'): paths.add('upstream/pi32v2-isa/tools/hwtest/semantics/'+name)
    modules = list(sys.modules.values())
    for module in list(modules):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).resolve().is_relative_to(ROOT):
            modules.extend(value for value in vars(module).values() if getattr(value, '__file__', None))
    for module in modules:
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix == '.py': paths.add(path.relative_to(ROOT).as_posix())
    pending = [ROOT/path for path in SOURCES]; seen = set()
    while pending:
        path = pending.pop().resolve()
        if path in seen: continue
        seen.add(path)
        for include in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', path.read_text(), re.M):
            for candidate in (path.parent/include, ROOT/'firmware/include'/include):
                if candidate.is_file():
                    paths.add(candidate.resolve().relative_to(ROOT).as_posix()); pending.append(candidate); break
    return sorted(paths)


def report(corpus, args, sources):
    from hyperrig.jieli import unpack_app
    from dsp_audio_path_machine import TABLE, PRIOR_TABLE, RESET_CONFIGURATION
    c = corpus; app = c.program.app; code = dict(c.program.code)
    for program in (c.program.construction, c.program.audio):
        for pc in code.keys() & program.code.keys(): assert code[pc] == program.code[pc]
        code.update(program.code)
    def binding(a, b):
        return {'start': a, 'end_exclusive': b, 'sha256': hashlib.sha256(app[offset(a):offset(b)]).hexdigest()}
    inherited = {'capture_dispatch': (0x01c12bf2, 0x01c12bf6), 'gain_table': TABLE,
        'coefficient_selector': (PRIOR_TABLE, PRIOR_TABLE+10), 'reset_configuration': RESET_CONFIGURATION,
        'task_registration': (0x02005250, 0x0200525e), 'resampling_taps': (0x0203be2c, 0x0203be50)}
    static = {name: binding(*span) for name, span in (c.program.static_regions | inherited).items()}
    windows = {hex(pc): binding(pc, pc+record[1]) for pc, record in sorted(code.items())}
    rom_addresses = {a+i for a, n in c.rom_reads for i in range(n)}; auxiliary = []
    for address in sorted(rom_addresses):
        if auxiliary and auxiliary[-1][1] == address: auxiliary[-1][1] = address+1
        else: auxiliary.append([address, address+1])
    auxiliary = [binding(a, b) for a, b in auxiliary]
    original = (ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin').read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()
    assert original_hash == '2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059'
    assert unpack_app(original)[2]['app.bin'] == app
    mini = None
    if args.mini_image:
        raw = args.mini_image.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
        assert sha == 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
        payload = unpack_app(raw)[2]['app.bin']
        for item in (*windows.values(), *static.values(), *auxiliary):
            a, b = item['start'], item['end_exclusive']
            assert payload[offset(a):offset(b)] == app[offset(a):offset(b)], hex(a)
        mini = {'image_sha256': sha, 'identical_instruction_windows': len(windows),
                'identical_static_windows': len(static), 'identical_auxiliary_rom_windows': len(auxiliary)}
    new = c.program.sample_code; missing = new-c.visited
    classified = {pc for group in INVARIANT_GAPS.values() for pc in group}
    assert not classified & c.visited, 'an invariant-classified instruction executed'
    joined = {'constructor': (CONSTRUCTOR, 0x0202ddfc), 'type25_builder': (0x0202b87e, 0x0202ba56),
        'dispatch': (0x01c0deb6, 0x01c0f678), 'individual': (0x01c0f678, 0x01c10446),
        'grouped': (0x01c10446, 0x01c10818), 'stage': (0x01c10e06, 0x01c11b00),
        'task': (0x01c01e5e, 0x01c02dbc), 'q28': (0x01c15dec, 0x01c15fdc),
        'q28_residual': (0x01c15fdc, 0x01c16222)}
    guards = api_checks(c)
    result = {'schema': 1, 'project': 'HyperRig', 'component': 'reconstructed-effect-sample-processing',
        'result': 'pass', 'new_original_functions': 7, 'original_image_sha256': original_hash,
        'decoded_image_sha256': hashlib.sha256(app).hexdigest(), 'mini_v4_binding': mini,
        'total_comparisons': c.cases, 'original_instruction_steps': c.steps,
        'retained_allocation_chains': c.chains, 'carried_calls': c.carried,
        'actual_constructor_calls': c.preparations,
        'c_only_guard_checks': len(guards), 'guard_checks': guards,
        'sanitizer_replay_cases': c.replay.count if c.replay else 0,
        'source_sha256': sources, 'library_sha256': hashlib.sha256(args.library.read_bytes()).hexdigest(),
        'outputs_state_ordered_services_sha256': c.digest.hexdigest(),
        'caller_derivative': check_derivative(),
        'direct_dispatcher_joins': {hex(pc): {'target': target, 'visited': pc in c.visited} for pc, target in DIRECT_SITES.items()},
        'original_internal_entries': {hex(pc): count for pc, count in sorted(c.real.items())},
        'observed_external_services': {hex(pc): count for pc, count in sorted(c.services.items())},
        'functions': {name: binding(a, b) | {'instructions': sum(a <= pc < b for pc in new),
            'visited': sum(a <= pc < b for pc in new & c.visited),
            'unvisited': sorted(pc for pc in missing if a <= pc < b)} for name, (a, b) in REGIONS.items()},
        'joined_bodies': {name: binding(a, b) | {'decoded': sum(a <= pc < b for pc in code),
            'visited': sum(a <= pc < b for pc in set(code) & c.visited),
            'unvisited': sorted(pc for pc in set(code)-c.visited if a <= pc < b)} for name, (a, b) in joined.items()},
        'static_data': static, 'auxiliary_raw_updater_rom_reads': auxiliary,
        'auxiliary_rom_policy': 'Byte authentication for direct raw indices only; no additional weight-table or function classification.',
        'bound_instruction_windows': windows,
        'instruction_coverage': {'new_decoded': len(new), 'new_visited': len(new & c.visited),
            'unvisited_new': sorted(missing), 'unclassified_unvisited': sorted(missing-classified),
            'unvisited_by_entry_invariant': {reason: addresses for reason, addresses in INVARIANT_GAPS.items()},
            'all_decoded': len(code), 'all_visited': len(set(code) & c.visited),
            'unvisited_all': sorted(set(code)-c.visited),
            'note': 'Only execution in this original/C corpus is counted; focused tests and earlier reports do not inflate these totals.'},
        'scripted_new_sample_replacements': 0,
        'hardware_test': False, 'audio_test': False, 'firmware_changed': False, 'flashable': False,
        'limitations': [
            'Types 25, 36 and 37 use actual constructor-produced state. Preparation is a separate invocation, not a recovered scheduler or allocation edge.',
            'Only the ten pinned direct dispatcher sites join new sample bodies; no callback is resolved by its numerical target alone, and inherited callback target guards remain.',
            'Raw counts and pointer arithmetic retain original uint32 semantics; finite C work/mapping failures are not native error-return or arbitrary prefix equivalence.',
            'The ring consumes sixteen samples per raw block; correlation consumes pairs and zero/odd counts may require enormous or nonterminating native walks.',
            'The Q28 wrapper retains whole-call private coefficients/history/residue while each public sample write remains immediate; public history/residue publish at original final sites.',
            'Existing caller and numerical-library domains remain explicit. Raw byte-mapped helpers do not inherit a fixture-sized sample ceiling.',
            'Type29 and other unrecovered sample-specific leaves remain outside this numerical closure. Platform/output services are scripted, with no physical audio or timing claim.',
            'Loaded but unvisited code remains listed and is not an overall firmware completion denominator.']}
    assert sources == {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}, 'sources changed during comparisons'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True); parser.add_argument('--suite', default='all')
    parser.add_argument('--output', type=Path); parser.add_argument('--mini-image', type=Path)
    parser.add_argument('--sanitizer-corpus', type=Path); args = parser.parse_args()
    if args.output and args.output.exists(): parser.error('choose a fresh report path')
    if args.sanitizer_corpus and args.sanitizer_corpus.exists(): parser.error('choose a fresh replay path')
    check_derivative(); corpus = Corpus(args.library, args.sanitizer_corpus); corpus.program.audio
    sources = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    suites = {'basic': basic_cases, 'aliases': alias_cases, 'numerical': numerical_cases,
              'constructed': constructed_cases, 'routing': routing_cases, 'audio': audio_cases,
              'dispatcher_edges': dispatcher_edges, 'transition_edges': transition_edges}
    for name in suites if args.suite == 'all' else (args.suite,):
        suites[name](corpus); print(name, corpus.cases, 'comparisons passed', flush=True)
    if corpus.replay: corpus.replay.close()
    if args.output: args.output.write_text(json.dumps(report(corpus, args, sources), indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'result': 'pass', 'comparisons': corpus.cases, 'steps': corpus.steps,
        'new_decoded': len(corpus.program.sample_code), 'new_visited': len(corpus.program.sample_code & corpus.visited)}))


if __name__ == '__main__': main()
