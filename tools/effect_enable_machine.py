"""Execute complete original effect-enable, fade and installed memory-clear bodies.

Remaining allocation, resource and effect-refresh calls are explicit services.
All decoded instructions are taken from the pinned original image. This is a
bounded comparison model, not a CPU/peripheral or hardware-validation claim.
"""
from __future__ import annotations
import re
from dot_machine import DotMachine, NativeProgram, ROOT, signed
from preset_assets_machine import PresetAssetsMachine
from pi32v2isa import codec, table

REGIONS = {
    'duration': (0x020303F4, 0x02030466),
    'commit_core': (0x02030466, 0x02030520),
    'finish': (0x02030520, 0x02030530),
    'commit': (0x02030530, 0x0203053A),
    'fast_core': (0x0203053A, 0x020305F8),
    'fast': (0x020305F8, 0x02030602),
    'fast_unchecked': (0x02030602, 0x0203060A),
    'commit_unchecked': (0x0203060A, 0x02030614),
    'tail_type': (0x01C069C6, 0x01C069E4),
    'fade': (0x01C069E4, 0x01C06B2C),
    'ir_reset': (0x01C11F76, 0x01C11FAA),
    'clear': (0x0201A9DC, 0x0201A9EA),
    'memset': (0x02033412, 0x0203343E),
}
REUSED = {'counter': (0x01C05160, 0x01C0516E)}
ARITIES = {'duration': 1, 'commit_core': 3, 'finish': 1, 'commit': 2,
    'fast_core': 3, 'fast': 2, 'fast_unchecked': 2, 'commit_unchecked': 2,
    'tail_type': 1, 'fade': 2, 'ir_reset': 1, 'counter': 0, 'clear': 2, 'memset': 3}
VOID = {'fade', 'ir_reset', 'counter'}
TABLE_START, TABLE_END, ALIGNMENT_END = 0x01C06A4A, 0x01C06A67, 0x01C06A68
EFFECTS, CONFIG, CONTROL, CALLBACKS = 0x01C2C220, 0x01C1F7D4, 0x01C32DB0, 0x01C34190
ARENA, STACK = 0x33000000, 0x30001000
MAPPED = ((EFFECTS, 7680), (CONFIG, 68), (CONTROL, 640), (CALLBACKS, 768), (ARENA, 32768))
SERVICES = {0x0203023C: 1, 0x02028DE8: 0, 0x0203033C: 1, 0x0202DEF2: 1,
            0x0202EC30: 0, 0x0202E328: 1, 0x0202E3CE: 1}
# Full direct-callee bodies are byte-bound ABI evidence, not executed functions.
ABI_REGIONS = {'cost': (0x0203023C, 0x020302C6), 'total': (0x02028DE8, 0x02028E46),
    'construct': (0x0203033C, 0x020303F4), 'demand': (0x0202DEF2, 0x0202DF04),
    'finish_service': (0x0202EC30, 0x0202EC54), 'refresh29': (0x0202E328, 0x0202E346),
    'refresh30': (0x0202E3CE, 0x0202E3F6), 'clear_writer': (0x0200254A, 0x02002558)}

def region_bytes(app, start, end):
    offset = start - 0x02000120 if start >= 0x02000120 else 0x02056780-0x02000120+start-0x01C00000
    return app[offset:offset+end-start]

class CounterRegion(NativeProgram):
    REGIONS = REUSED

class EffectEnableProgram:
    def __init__(self):
        CounterRegion('counter')  # Authenticates original and complete extracted application.
        self.code = {}; self.raw_regions = {}; self.parallel_seconds = set()
        app = (ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        instructions = table.load()
        for name, (start, end) in (REGIONS | REUSED).items():
            raw = region_bytes(app, start, end); self.raw_regions[name] = raw; pc = start
            while pc < end:
                if pc == TABLE_START: pc = ALIGNMENT_END; continue
                decoded = codec.decode(instructions, raw, pc-start)
                if decoded is None: raise ValueError(f'unsupported enable encoding {pc:#x}')
                instruction, fields, size = decoded; counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(('then', 'else')):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]]*spec.scale+spec.add
                if pc+size > end: raise ValueError('instruction crosses enable function boundary')
                self.code[pc] = codec.format(instruction, fields), size, *counts; pc += size
        self.table = region_bytes(app, TABLE_START, TABLE_END)
        if len(self.table) != 29 or region_bytes(app, TABLE_END, ALIGNMENT_END) != b'\0':
            raise ValueError('unreviewed fade table or alignment')
        if any(TABLE_START+2*v not in self.code for v in self.table):
            raise ValueError('fade table target is not executable code')
        for pc, (text, size, *_) in self.code.items():
            if text.endswith('  #'):
                following, bsize, *_ = self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|<=)', text) or bsize != 2 or '[' not in following:
                    raise ValueError(f'unreviewed enable parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self, memory, operation, *args, boundary=None):
        if (tuple(map(len, memory)) != tuple(n for _, n in MAPPED) or operation not in ARITIES
            or len(args) != ARITIES[operation] or any(not 0 <= a <= 0xffffffff for a in args)):
            raise ValueError('outside effect-enable comparison call domain')
        return EffectEnableMachine(self, memory, operation, args, boundary).run()

class EffectEnableMachine(PresetAssetsMachine):
    def __init__(self, program, memory, operation, args, boundary=None):
        self.program = program; self.operation = operation; self.boundary = boundary
        self.regs = {f'r{i}': 0 for i in range(16)}; self.regs['sp'] = STACK
        self.regs.update({f'r{i}': value for i, value in enumerate(args)})
        self.memory = {base+i: value for (base, _), data in zip(MAPPED, memory) for i, value in enumerate(data)}
        self.pc = (REGIONS | REUSED)[operation][0]; self.carry = self.steps = 0
        self.calls = []; self.frames = []; self.returns = []; self.visited = set()
        self.writes = []; self.else_skips = {}; self.internal_calls = []; self.service_sites = []

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(n)) for base, n in MAPPED)

    def read(self, address, size):
        if 0x30000000 <= address < STACK and address < self.value('sp'):
            raise ValueError('read below active enable stack')
        return DotMachine.read(self, address, size)

    def write(self, address, value, size):
        if 0x30000000 <= address < STACK:
            if address < self.value('sp') or address+size > STACK: raise ValueError('enable stack escape')
        elif not any(a <= address and address+size <= a+n for a, n in MAPPED):
            raise ValueError(f'enable write escaped initialized map {address:#x}/{size}')
        self.writes.append((address, value & ((1 << (8*size))-1), size))
        DotMachine.write(self, address, value, size)

    def step(self):
        if self.pc in self.else_skips: self.pc = self.else_skips.pop(self.pc)
        if self.pc in self.program.parallel_seconds: raise ValueError('entered parallel second half')
        if self.pc not in self.program.code: raise ValueError(f'enable escaped code {self.pc:#x}')
        text, size, *_ = self.program.code[self.pc]
        if not text.endswith('  #'): return self.single_step()
        pc, before = self.pc, dict(self.regs)
        destinations = re.match(r'(r\d+(?:_r\d+)?) ', text)[1].split('_')
        self.pc = pc+size
        if not self.single_step(): raise ValueError('parallel second half returned')
        after, end = dict(self.regs), self.pc
        self.regs, self.pc = dict(before), pc
        if not self.single_step(): raise ValueError('parallel first half returned')
        for destination in destinations: after[destination] = self.regs[destination]
        self.regs, self.pc = after, end
        return True

    def single_step(self):
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix('  #'); next_pc = self.pc+size
        if m := re.fullmatch(r'call (r\d+|-?\d+)', text):
            indirect = m[1].startswith('r')
            target = self.value(m[1]) if indirect else next_pc+int(m[1])
            if target in self.program.code and (not indirect or target == REGIONS['clear'][0]):
                self.internal_calls.append(target); self.returns.append(next_pc); self.pc = target; return True
            if not indirect and target not in SERVICES: raise ValueError(f'unreviewed service {target:#x}')
            if self.boundary is None: raise ValueError('explicit service callback required')
            count = 2 if indirect else SERVICES[target]
            args = tuple(self.value(f'r{i}') if i < count else 0 for i in range(6))
            before = self.snapshot(); value = self.boundary(target, args, self)
            self.calls.append((target, args, before, self.snapshot()))
            self.service_sites.append((self.pc, target, count))
            for i in range(4): self.set(f'r{i}', 0xbad0c0de)
            self.set('r0', value)
        elif m := re.fullmatch(r'tbb \[(r\d+)\]', text):
            index = self.value(m[1])
            if self.pc != TABLE_START-2 or index >= len(self.program.table): raise ValueError('fade table index')
            next_pc = TABLE_START+2*self.program.table[index]
        elif m := re.fullmatch(r'(r\d+) = smax\((r\d+), (r\d+)\)', text):
            self.set(m[1], max(signed(self.value(m[2])), signed(self.value(m[3]))))
        elif m := re.fullmatch(r'(r\d+) = (r\d+) & \(1 << (r\d+)\)', text):
            self.set(m[1], self.value(m[2]) & (1 << (self.value(m[3]) & 31)))
        elif m := re.fullmatch(r'(r\d+) = (r\d+) (>>|<<) (r\d+)', text):
            value, shift = self.value(m[2]), self.value(m[4]) & 31
            self.set(m[1], value >> shift if m[3] == '>>' else value << shift)
        elif m := re.fullmatch(r'(r\d+) = (r\d+) (\+|-|&) (0x[0-9a-fA-F]+)', text):
            a, b = self.value(m[2]), int(m[4], 16)
            self.set(m[1], a+b if m[3] == '+' else a-b if m[3] == '-' else a&b)
        elif m := re.fullmatch(r'if \(\((r\d+) & (0x[0-9a-fA-F]+)\) (==|!=) 0\) \{', text):
            condition = bool(self.value(m[1]) & int(m[2], 16)) == (m[3] == '!=')
            alternative = self.skip(next_pc, then)
            if not condition: next_pc = alternative
            elif otherwise: self.else_skips[alternative] = self.skip(alternative, otherwise)
        elif m := re.fullmatch(r'rep 2 (r\d+) \{', text):
            # Execute each original store, including zero-count bodies skipped by
            # the pinned ISA model. Large counts are bounded by the model budget.
            body, end = next_pc, next_pc+2
            while self.value(m[1]):
                if self.steps >= 4000000: raise ValueError('enable REP budget exceeded')
                self.pc = body; self.steps += 1
                if not self.step() or self.pc != end: raise ValueError('memset REP body escaped')
                self.set(m[1], self.value(m[1])-1)
            next_pc = end
        else: return super().single_step()
        self.pc = next_pc; return True

    def run(self):
        while self.steps < 4000000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value('sp') != STACK:
                    raise ValueError('unbalanced enable execution')
                return {'memory': self.snapshot(), 'calls': self.calls, 'writes': self.writes,
                    'visited': self.visited, 'steps': self.steps, 'internal_calls': self.internal_calls,
                    'service_sites': self.service_sites,
                    'result': 0 if self.operation in VOID else self.value('r0')}
        raise ValueError('enable instruction budget exceeded')
