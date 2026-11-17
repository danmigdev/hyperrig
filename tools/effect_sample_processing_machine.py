"""Original sample engines, exact direct caller joins and separate construction.

The numerical oracle executes decoded original instructions. It never calls the
portable C or substitutes coefficient, sample or state values.
"""
from __future__ import annotations
import re
from effect_processing_machine import (EffectProcessingProgram, EffectProcessingMachine,
    REGIONS as PROCESSING_REGIONS, ENTRIES as PROCESSING_ENTRIES, ARITIES as PROCESSING_ARITIES,
    STATIC as PROCESSING_STATIC, SERVICES, boundary_digest, RAM, RAM_BYTES, SAMPLES,
    ARENA, ARENA_BYTES, ROOT, STACK, offset)
from effect_model_construction_machine import (EffectModelConstructionProgram,
    EffectModelConstructionMachine, REGIONS as CONSTRUCTION_REGIONS,
    REUSED as CONSTRUCTION_REUSED)
from effect_parameter_support_machine import EffectParameterSupportMachine
from audio_task_machine import AudioTaskProgram, AudioTaskMachine
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {
    'cascade': (0x01c08b3e, 0x01c08c76), 'transition': (0x01c0b5d6, 0x01c0ba14),
    'mixer': (0x01c0ba14, 0x01c0bbce), 'width': (0x01c0bbce, 0x01c0bd8c),
    'update': (0x01c0bd8c, 0x01c0be92), 'ring': (0x01c18f90, 0x01c19448),
    'correlation': (0x01c19448, 0x01c1958e),
}
ARITIES = {**PROCESSING_ARITIES, 'cascade': 9, 'transition': 1, 'mixer': 8,
           'width': 4, 'update': 1, 'ring': 1, 'correlation': 1}
ENTRIES = {**PROCESSING_ENTRIES, **{name: a for name, (a, _) in REGIONS.items()}}
STATIC = {**PROCESSING_STATIC, 'correlation_weights': (0x0203b7e0, 0x0203b880)}
DIRECT_SITES = {
    0x01c0e6a2: 0x01c08b3e, 0x01c0e706: 0x01c08b3e,
    0x01c0f2e2: 0x01c18f90, 0x01c0f37c: 0x01c18f90,
    0x01c0f3ae: 0x01c0b5d6, 0x01c0f45c: 0x01c0ba14,
    0x01c0f4f4: 0x01c0ba14, 0x01c0f480: 0x01c0bbce,
    0x01c0f492: 0x01c0bbce, 0x01c0f630: 0x01c0bd8c,
}
# These inherited indirect sites are clocks, independently of their numeric
# callback token. The portable caller keeps its previously declared clock-token
# domain; a native-model collision must never become a sample-engine call.
INDIRECT_CLOCK_SITES = {0x01c0527c, 0x01c05368, 0x01c10824, 0x01c10ff2,
    0x01c115d0, 0x01c118e2, 0x01c0f940, 0x01c10100, 0x01c101ac,
    0x01c1041a, 0x01c10632, 0x01c10796}
MAPPED = ((RAM, RAM_BYTES), (SAMPLES, 65536), (ARENA, ARENA_BYTES),
          (0, 8192), (0xffff0000, 65536))
CONSTRUCTOR = 0x0202cf62


def _decode(program, name, start, end):
    raw = program.regions[name] = program.app[offset(start):offset(end)]
    isa = table.load(); pc = start
    while pc < end:
        found = codec.decode(isa, raw, pc-start)
        if found is None: raise ValueError(f'undecoded sample instruction {pc:#x}')
        instruction, fields, size = found; counts = [0, 0]
        if instruction.block:
            for i, kind in enumerate(('then', 'else')):
                field = instruction.fields[instruction.block[kind]]
                counts[i] = fields[instruction.block[kind]]*field.scale+field.add
        if pc+size > end: raise ValueError('sample instruction crosses whole function')
        program.code[pc] = codec.format(instruction, fields), size, *counts; pc += size


class EffectSampleProcessingProgram(EffectProcessingProgram):
    def __init__(self):
        super().__init__(); self.previous_code = set(self.code); self.support_code = set()
        self.construction = EffectModelConstructionProgram()
        self.static_regions = {**STATIC, **self.construction.static_regions}
        self.data = {name: self.app[offset(a):offset(b)]
                     for name, (a, b) in self.static_regions.items()}
        for name, (a, b) in REGIONS.items(): _decode(self, name, a, b)
        self.sample_code = set(self.code)-self.previous_code
        if len(self.sample_code) != 1324: raise ValueError('changed seven-body instruction registry')
        for pc in self.sample_code:
            text, size, *_ = self.code[pc]
            if text.endswith('  #'):
                following, n, *_ = self.code[pc+size]
                if n != 2 or '[' not in following: raise ValueError(f'unreviewed sample packet {pc:#x}')
                self.parallel_seconds.add(pc+size)
        for pc, target in DIRECT_SITES.items():
            text, size, *_ = self.code[pc]
            if text != f'call {target-pc-size}': raise ValueError('sample incoming direct-call binding')
        allowed = {**DIRECT_SITES, 0x01c08c22: 0x01c15fdc, 0x01c08c38: 0x01c15dec,
                   0x01c0be30: 0x01c19448}
        for pc in self.sample_code:
            text, size, *_ = self.code[pc]
            if match := re.fullmatch(r'call (-?\d+)', text):
                if allowed.get(pc) != pc+size+int(match[1]):
                    raise ValueError('unexpected sample numerical dependency')
        self._audio = None

    @property
    def audio(self):
        if self._audio is None: self._audio = SampleAudioProgram(self)
        return self._audio

    def machine(self, memory, name, arguments=(), boundary=None, *, mapped=MAPPED):
        if (tuple(map(len, memory)) != tuple(n for _, n in mapped) or name not in ARITIES
            or len(arguments) != ARITIES[name] or any(not 0 <= v <= MASK32 for v in arguments)):
            raise ValueError('sample entry ABI or mapped spans')
        machine = EffectSampleProcessingMachine(self, memory, boundary, mapped=mapped)
        machine.pc = ENTRIES[name]
        for i, value in enumerate(arguments):
            if i < 4: machine.set(f'r{i}', value)
            else: DotMachine.write(machine, STACK+4*(i-4), value, 4)
        return machine

    def execute(self, memory, name, arguments=(), boundary=None, *, mapped=MAPPED, instruction_budget=8000000):
        machine = self.machine(memory, name, arguments, boundary, mapped=mapped)
        while machine.steps < instruction_budget:
            machine.steps += 1
            if not machine.step(): break
        else: raise ValueError('sample original-instruction budget exhausted')
        if machine.frames or machine.returns or machine.else_skips or machine.value('sp') != STACK:
            raise ValueError('unbalanced sample original ABI')
        return {'value': machine.value('r0'), 'memory': machine.snapshot(), 'calls': machine.calls,
                'real_calls': machine.real_calls+machine.internal_calls, 'visited': machine.visited,
                'steps': machine.steps, 'rom_reads': machine.rom_reads}

    def prepare(self, memory, effect, *, mapped=MAPPED):
        machine = SampleConstructionMachine(self, memory, effect, mapped)
        result = machine.run(); result['rom_reads'] = machine.rom_reads
        return result


def _initialize_public(machine, program, memory, mapped):
    machine.mapped = mapped
    machine.memory = {base+i: byte for (base, _), data in zip(mapped, memory) for i, byte in enumerate(data)}
    machine.public_memory = list(map(bytearray, memory)); machine.rom_reads = set()
    for key, (start, _) in program.static_regions.items():
        machine.memory.update({start+i: byte for i, byte in enumerate(program.data[key])})


def mapped_read(machine, address, size):
    if address < 0 or address+size > 1 << 32: raise ValueError('sample read span wraps')
    if 0x30000000 <= address < STACK and not machine.value('sp') <= address <= address+size <= STACK:
        raise ValueError('sample read outside active original stack')
    # Direct raw updater indices can read adjacent immutable original ROM.
    # Those exact reached bytes are reported separately from the weight table.
    if any(address+i not in machine.memory for i in range(size)):
        app = machine.program.app
        if 0x02000120 <= address <= address+size <= 0x02000120+len(app):
            machine.rom_reads.add((address, size))
            return int.from_bytes(app[address-0x02000120:address-0x02000120+size], 'little')
    return DotMachine.read(machine, address, size)


def mapped_write(machine, address, value, size):
    if address < 0 or address+size > 1 << 32: raise ValueError('sample write span wraps')
    if 0x30000000 <= address < STACK:
        if not machine.value('sp') <= address <= address+size <= STACK:
            raise ValueError('sample write outside active original stack')
    else:
        for (base, n), data in zip(machine.mapped, machine.public_memory):
            if base <= address <= address+size <= base+n:
                data[address-base:address-base+size] = (value&((1 << (8*size))-1)).to_bytes(size, 'little')
                break
        else: raise ValueError(f'sample write escaped public map {address:#x}/{size}')
    if hasattr(machine, 'writes'): machine.writes.append((address, value&((1 << (8*size))-1), size))
    DotMachine.write(machine, address, value, size)


class SampleNumericalMachine(EffectModelConstructionMachine):
    def single_step(self):
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix('  #')
        if match := re.fullmatch(r'if \(\((r\d+) & (0x[0-9a-fA-F]+|r\d+|\d+)\) (==|!=) 0\) goto (-?\d+)', text):
            self.visited.add(self.pc)
            condition = bool(self.value(match[1]) & self.value(match[2])) == (match[3] == '!=')
            self.pc += size+(int(match[4]) if condition else 0); return True
        if match := re.fullmatch(r'\[--sp\] = \{r(\d+)-r4\}', text):
            self.visited.add(self.pc); saved = {f'r{i}': self.value(f'r{i}') for i in range(4, int(match[1])+1)}
            self.frames.append((saved, self.value('sp'))); self.set('sp', self.value('sp')-4*len(saved))
            self.pc += size; return True
        if re.fullmatch(r'\{r\d+-r4\} = \[sp\+\+\]', text):
            self.visited.add(self.pc); saved, sp = self.frames.pop()
            if self.value('sp') != sp-4*len(saved): raise ValueError('sample saved-register frame imbalance')
            self.regs.update(saved, sp=sp); self.pc += size; return True
        if match := re.fullmatch(r'(r\d+) = (r\d+)\.b0 \(u\)', text):
            self.visited.add(self.pc); self.set(match[1], self.value(match[2])&255)
            self.pc += size; return True
        if match := re.fullmatch(r'(r\d+) = sextra\((r\d+), p:(\d+), l:(\d+)\)', text):
            self.visited.add(self.pc); position, length = int(match[3]), int(match[4])
            self.set(match[1], signed((self.value(match[2]) >> position)&((1 << length)-1), length))
            self.pc += size; return True
        if match := re.fullmatch(r'(r\d+) = (r\d+) - (0x[0-9a-fA-F]+)', text):
            # This body reads carry/PSR immediately after subtraction. The old
            # construction helper's value-only hex-immediate shortcut is not
            # sufficient for these newly reached flag-dependent instructions.
            self.visited.add(self.pc)
            self.set(match[1], self.binary(self.value(match[2]), '-', int(match[3], 16)))
            self.pc += size; return True
        return super().single_step()


class EffectSampleProcessingMachine(EffectProcessingMachine):
    def __init__(self, program, memory, boundary, *, mapped=MAPPED):
        # The previous initializer supplies instruction-machine control fields;
        # all public bytes are then installed using the explicit borrowed map.
        super().__init__(program, memory, boundary)
        _initialize_public(self, program, memory, mapped)
        self.internal_calls = []; self.math_calls = []; self.production_calls = []
        self.normalization_calls = []; self.coefficient_requests = []; self.exp_arguments = []

    def read(self, address, size): return mapped_read(self, address, size)
    def write(self, address, value, size): return mapped_write(self, address, value, size)

    def single_step(self):
        text, size, *_ = self.program.code[self.pc]
        if text.startswith('call r'):
            target = self.value(text[5:])
            if target in {a for a, _ in REGIONS.values()}:
                if self.pc not in INDIRECT_CLOCK_SITES or self.boundary is None:
                    raise ValueError('unmodeled indirect sample-token service')
                self.visited.add(self.pc); count = 0
                args = tuple(self.value(f'r{i}') if i < 4 else self.read(self.value('sp')+4*(i-4), 4)
                             for i in range(count))
                self.calls.append((target, args, boundary_digest(target, args, self, self.state_digest())))
                value = self.boundary(target, args, self)
                for i in range(4): self.set(f'r{i}', 0xbad0c0de)
                self.set('r0', value); self.pc += size; return True
        return super().single_step()

    def step(self):
        if self.pc in self.else_skips: self.pc = self.else_skips.pop(self.pc)
        if self.pc not in self.program.sample_code: return super().step()
        if self.written is None: self.written = set()
        view = getattr(self, 'sample_view', None)
        if view is None:
            view = object.__new__(SampleNumericalMachine); self.sample_view = view
        view.__dict__.update(self.__dict__)
        view.read = self.read; view.write = self.write; view.snapshot = self.snapshot
        result = SampleNumericalMachine.step(view)
        for name, value in view.__dict__.items():
            if name not in ('read', 'write', 'snapshot', 'sample_view'): self.__dict__[name] = value
        return result


class SampleConstructionMachine(EffectModelConstructionMachine):
    def __init__(self, owner, memory, effect, mapped):
        self.program = owner.construction; self.program.app = owner.app
        self.operation = 'construct'; self.boundary = None
        _initialize_public(self, self.program, memory, mapped)
        self.regs = {f'r{i}': 0 for i in range(16)}; self.regs['sp'] = STACK
        self.pc = CONSTRUCTOR; self.carry = self.flags = self.steps = 0
        self.frames = []; self.returns = []; self.calls = []; self.internal_calls = []
        self.service_sites = []; self.writes = []; self.visited = set(); self.else_skips = {}; self.written = set()
        self.math_calls = []; self.production_calls = []; self.normalization_calls = []
        self.coefficient_requests = []; self.exp_arguments = []; self.set('r0', effect)
        if self.read(effect, 1) not in (25, 36, 37): raise ValueError('constructor/sample join type')

    def read(self, address, size): return mapped_read(self, address, size)
    def write(self, address, value, size): return mapped_write(self, address, value, size)

    def single_step(self):
        if self.pc not in self.program.support_code: return super().single_step()
        view = getattr(self, 'sample_support_view', None)
        if view is None:
            view = object.__new__(EffectParameterSupportMachine); self.sample_support_view = view
        view.__dict__.update(self.__dict__)
        view.read = self.read; view.write = self.write; view.snapshot = self.snapshot; view.set = self.set
        result = EffectParameterSupportMachine.single_step(view)
        for name, value in view.__dict__.items():
            if name not in ('read', 'write', 'snapshot', 'set', 'sample_support_view'): self.__dict__[name] = value
        return result


class SampleAudioProgram(AudioTaskProgram):
    def __init__(self, effects):
        super().__init__(); self.effects = effects
        for pc in self.code.keys() & effects.code.keys():
            if self.code[pc] != effects.code[pc]: raise ValueError('sample/audio instruction mismatch')
        self.code.update(effects.code); self.parallel_seconds |= effects.parallel_seconds
        self.sample_code = effects.sample_code; self.support_code = set(); self.app = effects.app

    def machine(self, memory, boundary=None): return SampleAudioMachine(self, memory, boundary)


class SampleAudioMachine(AudioTaskMachine):
    def __init__(self, program, memory, boundary):
        super().__init__(program, memory, boundary)
        self.flags = 0; self.entries = {}; self.mmio_events = []; self.mmio = None
        self.internal_calls = []; self.math_calls = []; self.production_calls = []; self.rom_reads = set()
        self.normalization_calls = []; self.coefficient_requests = []; self.exp_arguments = []
        self.effect_view = object.__new__(EffectSampleProcessingMachine)
        for key, (a, _) in program.effects.static_regions.items():
            self.memory.update({a+i: byte for i, byte in enumerate(program.effects.data[key])})

    def step(self):
        if self.pc in self.else_skips: self.pc = self.else_skips.pop(self.pc)
        if self.pc not in self.program.effects.code: return super().step()
        view = self.effect_view; view.__dict__.update(self.__dict__)
        view.read = lambda address, size: AudioTaskMachine.read(view, address, size)
        view.write = lambda address, value, size: AudioTaskMachine.write(view, address, value, size)
        view.state_digest = lambda: self.state_digest()
        result = EffectSampleProcessingMachine.step(view)
        for name, value in view.__dict__.items():
            if name not in ('read', 'write', 'state_digest'): self.__dict__[name] = value
        if self.written is None: self.written = set()
        return result


def carry_preparation_into_audio(machine, memory):
    """Transfer public bytes only; retain the suspended task's private control."""
    from audio_task_machine import MAPPED as AUDIO_MAPPED
    if tuple(map(len, memory)) != tuple(n for _, n in AUDIO_MAPPED): raise ValueError('audio preparation maps')
    machine.public_memory = list(map(bytearray, memory))
    for (base, _), data in zip(AUDIO_MAPPED, memory):
        machine.memory.update({base+i: byte for i, byte in enumerate(data)})
