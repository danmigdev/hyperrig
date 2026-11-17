"""Execute complete original parameter primitives and 64-bit division bodies.

Only alternate installed-clear callbacks remain explicit services. Code/data
comes from the pinned application. This is bounded instruction execution, not
a CPU/peripheral model or hardware validation.
"""
from __future__ import annotations
import re
from effect_enable_machine import (EffectEnableMachine, CounterRegion, region_bytes,
    ROOT, REGIONS as ENABLE_REGIONS)
from dot_machine import DotMachine, signed, MASK32, MASK64
from pi32v2isa import codec, table

REGIONS = {
    'selector': (0x01c060e6, 0x01c060fa),
    'pack': (0x01c06466, 0x01c06490),
    'clear_halfwords': (0x01c06554, 0x01c06582),
    'extra': (0x01c06582, 0x01c065a4),
    'clamp3': (0x01c065b4, 0x01c065c4),
    'clamp2': (0x01c065c4, 0x01c065d0),
    'capability': (0x01c065d0, 0x01c065e2),
    'active_word': (0x01c067e0, 0x01c067ea),
    'ratio': (0x01c06926, 0x01c0696a),
    'time_rule': (0x01c0696a, 0x01c069b0),
    'size_base': (0x02029e12, 0x02029e32),
    'size_extra': (0x02029e32, 0x02029e3c),
    'tempo_selector': (0x0202a75e, 0x0202a76c),
    'logical_size': (0x0202a7a8, 0x0202a7b2),
    'tempo': (0x0202ed38, 0x0202ed70),
    'tempo_global': (0x0202ed70, 0x0202ed7e),
    'memmove': (0x02032b2e, 0x02032bf0),
    'signed_divide': (0x02033172, 0x020331ce),
    'unsigned_divide': (0x020331ec, 0x02033412),
}
REUSED = {name: ENABLE_REGIONS[name] for name in ('clear', 'memset')}
STATIC = {'selector': (0x0203b880, 0x0203b8d4),
          'tempo': (0x0203b658, 0x0203b672),
          'capabilities': (0x0203b480, 0x0203b4a8)}
ARITIES = dict(selector=1, pack=3, clear_halfwords=2, extra=1, clamp3=1,
    clamp2=1, capability=1, active_word=1, ratio=3, time_rule=3,
    size_base=1, size_extra=1, tempo_selector=1, logical_size=1, tempo=2,
    tempo_global=1, memmove=3, signed_divide=4, unsigned_divide=5)
VOID = {'pack', 'clear_halfwords'}
WIDE = {'ratio', 'signed_divide', 'unsigned_divide'}
CONFIG, CONTROL, CALLBACKS, ARENA, STACK = 0x01c1f7d4, 0x01c32db0, 0x01c34190, 0x33000000, 0x30001000
MAPPED = ((CONFIG, 68), (CONTROL, 640), (CALLBACKS, 768), (ARENA, 32768))

class EffectParameterSupportProgram:
    def __init__(self):
        CounterRegion('counter')
        app = (ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.code, self.regions, self.parallel_seconds = {}, {}, set()
        self.data = {name: region_bytes(app, *bounds) for name, bounds in STATIC.items()}
        instructions = table.load()
        for name, (start, end) in (REGIONS | REUSED).items():
            raw = self.regions[name] = region_bytes(app, start, end)
            cursor = 0
            while cursor < len(raw):
                decoded = codec.decode(instructions, raw, cursor)
                if decoded is None: raise ValueError(f'unsupported parameter primitive {start+cursor:#x}')
                instruction, fields, size = decoded; counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(('then', 'else')):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]]*spec.scale + spec.add
                if cursor+size > len(raw): raise ValueError('primitive crosses complete region')
                self.code[start+cursor] = codec.format(instruction, fields), size, *counts
                cursor += size
        for pc, (text, size, _, _) in self.code.items():
            if text.endswith('  #'):
                following, bsize, _, _ = self.code[pc+size]
                if not re.match(r'r\d+(?:_r\d+)? (?:=|<=)', text) or bsize != 2 or '[' not in following:
                    raise ValueError(f'unreviewed support parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)

    def execute(self, memory, operation, *arguments, boundary=None):
        if (tuple(map(len, memory)) != tuple(n for _, n in MAPPED) or operation not in ARITIES
            or len(arguments) != ARITIES[operation] or any(not 0 <= a <= MASK32 for a in arguments)):
            raise ValueError('outside parameter-support ABI domain')
        if operation == 'capability' and arguments[0] >= 40: raise ValueError('unbound capability type')
        return EffectParameterSupportMachine(self, memory, operation, arguments, boundary).run()

class EffectParameterSupportMachine(EffectEnableMachine):
    def __init__(self, program, memory, operation, arguments, boundary=None):
        self.program, self.operation, self.boundary = program, operation, boundary
        self.regs = {f'r{i}': 0 for i in range(16)}; self.regs['sp'] = STACK
        self.memory = {base+i: v for (base, _), data in zip(MAPPED, memory) for i, v in enumerate(data)}
        for name, (base, _) in STATIC.items():
            self.memory.update({base+i: v for i, v in enumerate(program.data[name])})
        for i, value in enumerate(arguments):
            if i < 4: self.set(f'r{i}', value)
            else: DotMachine.write(self, STACK+4*(i-4), value, 4)
        self.pc = REGIONS[operation][0]
        self.carry = self.flags = self.steps = 0
        self.calls, self.frames, self.returns, self.writes, self.internal_calls = [], [], [], [], []
        self.visited, self.else_skips = set(), {}

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(n)) for base, n in MAPPED)

    def read(self, address, size):
        if 0x30000000 <= address < STACK and not self.value('sp') <= address <= address+size <= STACK:
            raise ValueError('support read escaped active stack')
        return DotMachine.read(self, address, size)

    def write(self, address, value, size):
        if 0x30000000 <= address < STACK:
            if not self.value('sp') <= address <= address+size <= STACK: raise ValueError('support stack escape')
        elif not any(a <= address <= address+size <= a+n for a, n in MAPPED):
            raise ValueError(f'support write escaped mapped memory {address:#x}/{size}')
        self.writes.append((address, value & ((1 << (size*8))-1), size))
        DotMachine.write(self, address, value, size)

    def address(self, expression):
        if match := re.fullmatch(r'\+\+(r\d+)=(-?\d+)', expression):
            self.set(match[1], self.value(match[1])+int(match[2])); return self.value(match[1])
        return super().address(expression)

    def binary(self, a, operator, b, carry=0):
        result = super().binary(a, operator, b, carry)
        if operator in ('+', '-'):
            exact = signed(a)+signed(b)+carry if operator == '+' else signed(a)-signed(b)-carry
            self.flags = int(not -(1 << 31) <= exact < (1 << 31)) | self.carry << 1 | int(result == 0) << 2 | result >> 31 << 3
        return result

    def single_step(self):
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix('  #'); next_pc = self.pc+size
        if match := re.fullmatch(r'call (r\d+|-?\d+)', text):
            indirect = match[1].startswith('r')
            target = self.value(match[1]) if indirect else next_pc+int(match[1])
            if not indirect or target == REUSED['clear'][0]:
                if target not in self.program.code: raise ValueError(f'unrecovered support dependency {target:#x}')
                self.internal_calls.append(target); self.returns.append(next_pc); self.pc = target; return True
            if self.boundary is None: raise ValueError('alternate clear requires explicit boundary')
            args = (self.value('r0'), self.value('r1'))+(0,)*10
            before = self.snapshot(); value = self.boundary(target, args, self)
            self.calls.append((target, args, before, self.snapshot()))
            for i in range(4): self.set(f'r{i}', 0xbad0c0de)
            self.set('r0', value)
        elif match := re.fullmatch(r'rep (\d+) (r\d+) \{', text):
            body, end, remaining = next_pc, next_pc+int(match[1]), self.value(match[2])
            # REP has a hidden loop count. Some native memcpy bodies overwrite
            # its source register with loaded bytes; the remaining count wins.
            while remaining:
                if self.steps >= 4000000: raise ValueError('support REP instruction budget')
                self.pc = body
                while self.pc < end:
                    self.steps += 1
                    if not self.step(): raise ValueError('support REP body returned')
                if self.pc != end: raise ValueError('support REP escaped body')
                remaining -= 1; self.set(match[2], remaining)
            next_pc = end
        elif match := re.fullmatch(r'(r\d+) = psr', text): self.set(match[1], self.flags)
        elif match := re.fullmatch(r'(r\d+) = clz\((r\d+)\)', text):
            self.set(match[1], 32-self.value(match[2]).bit_length())
        elif match := re.fullmatch(r'(r\d+_r\d+) (<<=|>>=|>>>=) (\d+)', text):
            value, amount = self.pair(match[1]), int(match[3]) & 63
            self.set_pair(match[1], value << amount if match[2] == '<<=' else
                          (signed(value, 64) if match[2] == '>>>=' else value) >> amount)
        elif match := re.fullmatch(r'(r\d+) = (r\d+) / (r\d+) \(u\)', text):
            a, b = self.value(match[2]), self.value(match[3]); value = a//b if b else 0
            self.set(match[1], value); self.flags = self.flags & 3 | int(value == 0) << 2 | value >> 31 << 3
        elif match := re.fullmatch(r'(r\d+) = (r\d+) (\+|-) (r\d+) (\+ c|- !c)', text):
            carry = self.carry if match[3] == '+' else 1-self.carry
            self.set(match[1], self.binary(self.value(match[2]), match[3], self.value(match[4]), carry))
        elif match := re.fullmatch(r'(r\d+|sp) = (r\d+|0x[0-9a-fA-F]+|-?\d+) (\+|-) (r\d+|0x[0-9a-fA-F]+|-?\d+)', text):
            self.set(match[1], self.binary(self.value(match[2]), match[3], self.value(match[4])))
        elif match := re.fullmatch(r'(r\d+|sp) (\+=|-=) (r\d+|-?\d+)', text):
            self.set(match[1], self.binary(self.value(match[1]), match[2][0], self.value(match[3])))
        elif match := re.fullmatch(r'(r\d+) = (r\d+) (\^|&|\|) (~?r\d+)', text):
            a, b = self.value(match[2]), self.value(match[4].removeprefix('~'))
            if match[4].startswith('~'): b ^= MASK32
            self.set(match[1], {'^': a ^ b, '&': a & b, '|': a | b}[match[3]])
        elif match := re.fullmatch(r'(r\d+) \|= (r\d+)', text):
            self.set(match[1], self.value(match[1]) | self.value(match[2]))
        elif match := re.fullmatch(r'(r\d+) <<= (r\d+)', text):
            self.set(match[1], self.value(match[1]) << (self.value(match[2]) & 31))
        elif match := re.fullmatch(r'd\[(.+)\] = (r\d+_r\d+)', text):
            self.write(self.address(match[1]), self.pair(match[2]), 8)
        elif match := re.fullmatch(r'(r\d+_r\d+) = d\[(.+)\]', text):
            self.set_pair(match[1], self.read(self.address(match[2]), 8))
        else: return super().single_step()
        self.pc = next_pc; return True

    def run(self):
        while self.steps < 4000000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value('sp') != STACK:
                    raise ValueError('unbalanced parameter-support execution')
                result = (0, 0) if self.operation in VOID else (self.value('r0'), self.value('r1') if self.operation in WIDE else 0)
                return {'result': result, 'memory': self.snapshot(), 'calls': self.calls,
                        'writes': self.writes, 'visited': self.visited, 'steps': self.steps,
                        'internal_calls': self.internal_calls}
        raise ValueError('support instruction budget exceeded')
