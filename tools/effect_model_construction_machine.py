"""Execute original model builders and their complete algorithmic dependencies.

All six previously explicit main-constructor calls execute actual original
instructions here. No numerical result, service return or state update is
supplied by a fixture. Portable C is deliberately not used by this model.
"""
from __future__ import annotations
import re
from effect_construction_machine import (EffectConstructionProgram,
    EffectConstructionMachine, REGIONS as CONSTRUCTION, REUSED as CONSTRUCTION_REUSED,
    STATIC as CONSTRUCTION_STATIC, TABLES as CONSTRUCTION_TABLES, MAPPED, STACK)
from effect_parameter_support_machine import (EffectParameterSupportProgram,
    EffectParameterSupportMachine, REGIONS as SUPPORT)
from effect_enable_machine import region_bytes, ROOT
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {
    'object_mode': (0x01c05ed6, 0x01c05eec),
    'object_record': (0x01c06004, 0x01c06028),
    'percent': (0x01c0611a, 0x01c0612a),
    'level_exp': (0x01c0612a, 0x01c06148),
    'curve_setup': (0x01c06148, 0x01c061ce),
    'pole_exp': (0x01c061ce, 0x01c06230),
    'curve_state': (0x01c06230, 0x01c0625a),
    'curve_sample': (0x01c0625a, 0x01c062d2),
    'curve20_setup': (0x01c062d2, 0x01c0636e),
    'frequency_response': (0x01c0636e, 0x01c0644a),
    'finite_clamp': (0x01c0644a, 0x01c06466),
    'pitch_curve': (0x01c06490, 0x01c064d2),
    'pitch_increment': (0x01c064d2, 0x01c064fe),
    'pitch_limit_valid': (0x01c064fe, 0x01c06514),
    'object_duration': (0x02029e54, 0x02029e7c),
    'object_limit': (0x02029e7c, 0x02029e98),
    'object_length': (0x02029e98, 0x02029ec8),
    'object_extra': (0x02029ec8, 0x02029ed4),
    'build39': (0x0202a872, 0x0202ab98),
    'pole_clamp': (0x0202ab98, 0x0202abaa),
    'build16': (0x0202abaa, 0x0202ac80),
    'build17': (0x0202ac80, 0x0202ad60),
    'build18': (0x0202ad60, 0x0202ae22),
    'build19': (0x0202ae22, 0x0202af48),
    'build20': (0x0202af48, 0x0202b01e),
    'tone_polynomial': (0x0202b01e, 0x0202b420),
    'tone_response': (0x0202b420, 0x0202b484),
    'tone_setup': (0x0202b484, 0x0202b5ac),
    'tone_parameters': (0x0202b5ac, 0x0202b616),
    'build21': (0x0202b616, 0x0202b69e),
    'build22': (0x0202b69e, 0x0202b762),
    'build23': (0x0202b762, 0x0202b838),
    'build16_to23': (0x0202b838, 0x0202b87e),
    'build25': (0x0202b87e, 0x0202ba56),
    'pitch_ratio': (0x0202ba56, 0x0202ba90),
    'build29': (0x0202ba90, 0x0202beb2),
    'object_filter': (0x0202bffc, 0x0202c0f6),
    'odd_length': (0x0202c0f6, 0x0202c11c),
    'object_feedback': (0x0202c11c, 0x0202c1e2),
    'object_mix': (0x0202c1e2, 0x0202c248),
    'object_mode1': (0x0202c248, 0x0202c5a2),
    'object_mode2': (0x0202c5a2, 0x0202c836),
    'object_mode0': (0x0202c836, 0x0202cc9c),
    'object_reset': (0x0202cc9c, 0x0202cd32),
    'build_object': (0x0202cd32, 0x0202cdba),
    'square_root30': (0x0202cdba, 0x0202cde4),
    'signature_coefficients': (0x0202cde4, 0x0202cf5a),
    'build_signature': (0x0202cf5a, 0x0202cf62),
    'unsigned_quotient': (0x020331da, 0x020331ec),
}
REUSED = {**CONSTRUCTION, **CONSTRUCTION_REUSED,
          'pack': SUPPORT['pack'], 'unsigned_divide': SUPPORT['unsigned_divide']}
TABLES = {'model_branches': (0x0202b846, 0x0202b84e)}
STATIC = {**TABLES,
    'object2_lengths': (0x0203b4a8, 0x0203b4ae),
    'object_records': (0x0203b4b8, 0x0203b608),
    'type19_records': (0x0203b674, 0x0203b6bc),
    'tone_records': (0x0203b6bc, 0x0203b710),
    'object1_routes': (0x0203b710, 0x0203b718),
    'feedback_levels': (0x0203b718, 0x0203b72c),
    'object0_lengths2': (0x0203b72c, 0x0203b74c),
    'object0_feedback2': (0x0203b75c, 0x0203b764),
    'object1_lengths': (0x0203bdc8, 0x0203bdd8),
    'type39_times': (0x0203bdd8, 0x0203bde8),
    'object1_lengths8': (0x0203bde8, 0x0203bdf8),
    'object2_feedback1_to3': (0x0203bdfc, 0x0203be08),
    'object0_lengths1': (0x0203be08, 0x0203be18),
    'object31_levels': (0x0203be18, 0x0203be28),
    'object2_counts1_to3': (0x0203be29, 0x0203be2c),
}
# Public arities include the audited incoming stack arguments. Void-result
# normalization is separate from internal original-instruction execution,
# which retains every actual caller-visible register value.
ARITIES = {name: 1 for name in REGIONS}
ARITIES.update(curve_setup=4, curve_sample=3, curve_state=3, curve20_setup=5,
    frequency_response=2, pitch_curve=4, tone_polynomial=5, tone_setup=5,
    tone_parameters=3, object_filter=7, object_feedback=6, object_mix=3,
    object_mode0=2, object_mode1=2, object_mode2=2,
    signature_coefficients=2, build_signature=2, unsigned_quotient=4)
ARITIES['pitch_limit_valid'] = 0
VOID = {name for name in REGIONS if name.startswith('build')} | {
    'curve_setup', 'curve20_setup', 'curve_state', 'pitch_increment', 'tone_polynomial',
    'tone_setup', 'tone_parameters', 'object_filter', 'object_mix', 'object_mode0',
    'object_mode1', 'object_mode2', 'object_reset', 'signature_coefficients'}
WIDE = {'unsigned_quotient'}
ARITIES['construct'] = 1; VOID.add('construct')


class EffectModelConstructionProgram:
    def __init__(self):
        previous = EffectConstructionProgram(); support = EffectParameterSupportProgram()
        self.code = dict(previous.code); self.regions = dict(previous.regions)
        self.parallel_seconds = set(previous.parallel_seconds)
        self.static_regions = {**CONSTRUCTION_STATIC, **STATIC}
        app = (ROOT/'analysis/firmware/m571_g_app/app.bin').read_bytes()
        self.data = {name: region_bytes(app, *span) for name, span in self.static_regions.items()}
        self.support_code = {pc for pc in support.code
                             if any(a <= pc < b for a, b in (SUPPORT['pack'], SUPPORT['unsigned_divide']))}
        for pc in self.support_code:
            self.code[pc] = support.code[pc]
        self.parallel_seconds |= support.parallel_seconds & self.support_code
        for name in ('pack', 'unsigned_divide'):
            self.regions[name] = support.regions[name]
        isa = table.load()
        for name, (start, end) in REGIONS.items():
            raw = self.regions[name] = region_bytes(app, start, end); pc = start
            while pc < end:
                data_end = next((b for a, b in TABLES.values() if pc == a), None)
                if data_end is not None: pc = data_end; continue
                found = codec.decode(isa, raw, pc-start)
                if found is None: raise ValueError(f'undecoded model-construction instruction {pc:#x}')
                instruction, fields, size = found; counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(('then', 'else')):
                        field = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]]*field.scale+field.add
                if pc+size > end: raise ValueError('model-construction instruction crosses a complete body')
                self.code[pc] = codec.format(instruction, fields), size, *counts; pc += size
        for pc, (text, size, *_) in self.code.items():
            if text.endswith('  #'):
                following, next_size, *_ = self.code[pc+size]
                if next_size != 2 or '[' not in following:
                    raise ValueError(f'unreviewed model-construction parallel packet {pc:#x}')
                self.parallel_seconds.add(pc+size)
        for name, (start, end) in TABLES.items():
            targets = [start+2*v for v in self.data[name]]
            if any(target not in self.code or target in self.parallel_seconds for target in targets):
                raise ValueError('model-construction branch target is not a packet start')
        for pc, (text, size, *_) in self.code.items():
            if match := re.fullmatch(r'call (-?\d+)', text):
                target = pc+size+int(match[1])
                if target not in self.code: raise ValueError(f'unclosed construction dependency {pc:#x}->{target:#x}')

    def execute(self, memory, name, arguments=()):
        if (tuple(map(len, memory)) != tuple(n for _, n in MAPPED) or name not in ARITIES
            or len(arguments) != ARITIES[name] or any(not 0 <= v <= MASK32 for v in arguments)):
            raise ValueError('model-construction entry ABI or mapped views')
        return EffectModelConstructionMachine(self, memory, name, arguments).run()


class EffectModelConstructionMachine(EffectConstructionMachine):
    def __init__(self, program, memory, name, arguments):
        # The parent only recognizes its own public entries. Initialization is
        # adapted after assigning one of those entries; no instruction executes.
        super().__init__(program, memory, 'construct', (), None)
        self.operation = name
        self.pc = CONSTRUCTION['construct'][0] if name == 'construct' else REGIONS[name][0]
        for key, (base, _) in program.static_regions.items():
            self.memory.update({base+i: v for i, v in enumerate(program.data[key])})
        for i, value in enumerate(arguments):
            if i < 4: self.set(f'r{i}', value)
            else: DotMachine.write(self, STACK+4*(i-4), value, 4)

    def address(self, expression):
        if match := re.fullmatch(r'\+\+(r\d+)=(r\d+)', expression):
            self.set(match[1], self.value(match[1])+self.value(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def binary(self, a, operator, b, carry=0):
        result = super().binary(a, operator, b, carry)
        if operator in ('+', '-'):
            exact = signed(a)+signed(b)+carry if operator == '+' else signed(a)-signed(b)-carry
            self.flags = int(not -(1 << 31) <= exact < (1 << 31)) | self.carry << 1 | int(result == 0) << 2 | result >> 31 << 3
        return result

    def single_step(self):
        if self.pc in self.program.support_code:
            view = getattr(self, 'support_view', None)
            if view is None:
                view = object.__new__(EffectParameterSupportMachine); self.support_view = view
            view.__dict__.update(self.__dict__)
            view.read = lambda address, size: EffectConstructionMachine.read(view, address, size)
            view.write = lambda address, value, size: EffectConstructionMachine.write(view, address, value, size)
            view.snapshot = lambda: EffectConstructionMachine.snapshot(view)
            view.set = self.set
            result = EffectParameterSupportMachine.single_step(view)
            for name, value in view.__dict__.items():
                if name not in ('read', 'write', 'snapshot', 'set', 'support_view'):
                    self.__dict__[name] = value
            return result
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix('  #'); next_pc = self.pc+size
        if match := re.fullmatch(r'\[--sp\] = \{rets, (.+)\}', text):
            registers = []
            for item in match[1].split(', '):
                part = re.fullmatch(r'r(\d+)(?:-r(\d+))?', item)
                if not part: raise ValueError('unreviewed saved-register list')
                high, low = int(part[1]), int(part[2] or part[1])
                registers.extend(f'r{i}' for i in range(low, high+1))
            saved = {r: self.value(r) for r in registers}
            self.frames.append((saved, self.value('sp')))
            self.set('sp', self.value('sp')-4*(len(saved)+1))
        elif re.fullmatch(r'\{pc, (.+)\} = \[sp\+\+\]', text):
            saved, sp = self.frames.pop()
            if self.value('sp') != sp-4*(len(saved)+1): raise ValueError('unbalanced model-construction frame')
            self.regs.update(saved, sp=sp)
            if not self.returns: return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r'h\[(.+)\] = (r\d+)', text):
            self.write(self.address(match[1]), self.value(match[2]), 2)
        elif match := re.fullmatch(r'(r\d+) = abs\((r\d+)\)', text):
            self.set(match[1], abs(signed(self.value(match[2]))))
        elif match := re.fullmatch(r'(r\d+) = psr', text):
            self.set(match[1], self.flags)
        elif match := re.fullmatch(r'(r\d+_r\d+) = (r\d+) \* (r\d+) \(s\)', text):
            self.set_pair(match[1], signed(self.value(match[2]))*signed(self.value(match[3])))
        elif match := re.fullmatch(r'(r\d+_r\d+) ([+-])= (r\d+) \* (r\d+) \(s\)', text):
            value = signed(self.value(match[3]))*signed(self.value(match[4]))
            self.set_pair(match[1], self.pair(match[1])+(value if match[2] == '+' else -value))
        elif match := re.fullmatch(r'(r\d+_r\d+) (<<=|>>=|>>>=) (\d+)', text):
            value, amount = self.pair(match[1]), int(match[3]) & 63
            self.set_pair(match[1], value << amount if match[2] == '<<=' else
                          (signed(value, 64) if match[2] == '>>>=' else value) >> amount)
        elif match := re.fullmatch(r'(r\d+) = u(min|max)\((r\d+), (r\d+)\)', text):
            self.set(match[1], (min if match[2] == 'min' else max)(self.value(match[3]), self.value(match[4])))
        elif match := re.fullmatch(r'(r\d+) = (r\d+) & \(1 << (r\d+)\)', text):
            self.set(match[1], self.value(match[2]) & (1 << (self.value(match[3]) & 31)))
        elif match := re.fullmatch(r'(r\d+) \|= (\d+)', text):
            self.set(match[1], self.value(match[1]) | int(match[2]))
        elif match := re.fullmatch(r'if \(\((r\d+) & (r\d+|0x[0-9a-fA-F]+)\) (==|!=) 0\) \{', text):
            condition = bool(self.value(match[1]) & self.value(match[2])) == (match[3] == '!=')
            alternative = self.skip(next_pc, then)
            if not condition: next_pc = alternative
            elif otherwise: self.else_skips[alternative] = self.skip(alternative, otherwise)
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        result = super().run()
        result['result'] = (0, 0) if self.operation in VOID else (
            self.value('r0'), self.value('r1') if self.operation in WIDE else 0)
        return result
