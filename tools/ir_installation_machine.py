"""Execute original IR preparation/installation and slot reads without hardware.

Every added numerical body executes decoded original instructions. The prior IR
ownership model is unchanged; its install and slot service calls become internal.
"""
from __future__ import annotations
import re
from ir_loader_machine import (IrLoaderProgram, IrLoaderMachine, REGIONS as LOADER_REGIONS,
    ROOT, HEAP, CAPACITY, CALLBACK, SERVICES)
from biquad_generator_machine import region_bytes
from biquad_coefficients_machine import FLOAT, BRANCH
from dot_machine import signed, DotMachine
from pi32v2isa import codec, table

REGIONS = {
    "budget": (0x02029248, 0x02029268), "convert": (0x02029268, 0x0202928A),
    "limit": (0x0202928A, 0x020292EE), "effective": (0x020292EE, 0x0202930E),
    "trim": (0x020294CE, 0x0202957E), "configure": (0x0202957E, 0x020295D8),
    "slot": (0x020295D8, 0x02029604), "raw_length": (0x02029604, 0x0202962A),
    "read": (0x0201AD4C, 0x0201ADE8), "gain_clamp": (0x01C05EB0, 0x01C05EC6),
}
MATH_REGIONS = {"scaled_exp": (0x01C0516E, 0x01C05182), "exp": (0x020285D4, 0x02028646)}
DSP, GAIN, STACK = 0x01C32DB0, 0x01C1F7DC, 0x30001000
EXTRA = ((DSP+60, 24), (GAIN, 4))
ARITIES = {"budget": 1, "convert": 3, "limit": 5, "effective": 2, "raw_length": 2,
           "trim": 2, "configure": 4, "slot": 2, "read": 3,
           "attach": 4, "refresh": 0, "load": 2}

class IrInstallationProgram(IrLoaderProgram):
    def __init__(self):
        super().__init__()
        self.pre_installation_code = set(self.code)
        self.installation_regions, self.math_regions = {}, {}
        app = (ROOT / 'analysis/firmware/m571_g_app/app.bin').read_bytes()
        instructions = table.load()
        for mapping, destination in ((REGIONS, self.installation_regions), (MATH_REGIONS, self.math_regions)):
            for name, (start, end) in mapping.items():
                raw = region_bytes(app, start, end)
                destination[name] = raw
                offset = 0
                while offset < len(raw):
                    decoded = codec.decode(instructions, raw, offset)
                    if decoded is None: raise ValueError(f'unsupported IR installation encoding at {start+offset:#x}')
                    instruction, fields, size = decoded
                    counts = [0, 0]
                    if instruction.block:
                        for i, kind in enumerate(('then', 'else')):
                            spec = instruction.fields[instruction.block[kind]]
                            counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                    if start + offset + size > end: raise ValueError('IR installation boundary crossed')
                    self.code[start+offset] = codec.format(instruction, fields), size, *counts
                    offset += size
        for pc in set(self.code) - self.pre_installation_code:
            text, size, _, _ = self.code[pc]
            if text.endswith('  #'):
                following, b_size, _, _ = self.code[pc+size]
                if not re.match(r'r\d+ =', text) or b_size != 2 or '[' not in following:
                    raise ValueError('unreviewed IR installation parallel packet')
                self.parallel_seconds.add(pc+size)

    def execute(self, memory, operation, *args, reader=None, boundary=None, stack_byte=0xA7):
        if (operation not in ARITIES or len(args) != ARITIES[operation] or len(memory) != 19
                or tuple(len(x) for i, x in enumerate(memory) if i != 2) !=
                    (272,1860,4,2,20,48,16,256,40,1490,1490,16,12,4,4,CAPACITY,24,4)
                or not 0 <= memory[2] <= 255 or not 0 <= stack_byte <= 255
                or any(not 0 <= x <= 0xFFFFFFFF for x in args)
                or operation == 'load' and any(x > 10 for x in memory[4])):
            raise ValueError('outside IR installation verifier domain')
        if operation in ('trim', 'configure', 'attach') and (args[0] not in (0, HEAP) or args[0] and args[1] > 4076):
            raise ValueError('unmapped or oversized IR sample storage')
        if operation == 'read' and args[2] > 4076:
            raise ValueError('oversized IR read destination')
        return IrInstallationMachine(self, memory, operation, args, reader, boundary, stack_byte).run()

class IrInstallationMachine(IrLoaderMachine):
    def __init__(self, program, memory, operation, args, reader, boundary, stack_byte):
        inherited = operation in ('attach', 'refresh', 'load')
        super().__init__(program, memory[:17], operation if inherited else 'pending', args if inherited else (), reader, boundary)
        for (base, _), data in zip(EXTRA, memory[17:]):
            self.memory.update({base+i: x for i, x in enumerate(data)})
        self.allocated = CAPACITY if operation != 'load' else None
        self.stack_byte = stack_byte
        if not inherited:
            self.pc = REGIONS[operation][0]
            self.regs.update({f'r{i}': value for i, value in enumerate(list(args[:4])+[0]*(4-min(4,len(args))))})
        if operation == 'read': self.regs.update(r0=args[0], r1=args[1], r2=HEAP, r3=args[2])
        if operation == 'limit': DotMachine.write(self, STACK, args[4], 4)

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base+i] for i in range(size)) for base,size in EXTRA)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text, next_pc = text.removesuffix('  #'), self.pc+size
        if self.pc == 0x0201AD4E:
            # Original failed header reads can leave this private frame unwritten.
            # The incidental length load cannot affect a rejected-header result.
            after = self.value('sp')-44
            for address in range(after, self.value('sp')): self.memory[address] = self.stack_byte
            self.set('sp', after)
        elif (match := re.fullmatch(r'call (-?\d+)', text)) and next_pc+int(match[1]) in self.program.code:
            self.returns.append(next_pc)
            next_pc += int(match[1])
        elif match := re.fullmatch(r'(r\d+) = (r\d+) ([+*/]) (r\d+) \(f\)', text):
            self.set(match[1], FLOAT.arithmetic(self.value(match[2]), self.value(match[4]), {'+':'add','*':'mul','/':'div'}[match[3]]))
        elif match := re.fullmatch(r'(r\d+) = itof\((r\d+)\)', text):
            result, _ = FLOAT.convert('itof', 'even')({0:self.value(match[2])}, 0, {'s':0,'r':1})
            self.set(match[1], result[1])
        elif match := re.fullmatch(r'iff \((r\d+) (u?<=|u?>=|u?<|u?>|==|!=) (r\d+)\) (?:goto (-?\d+)|(\{))', text):
            relation = {'<':'lt','>':'gt','<=':'le','>=':'ge','==':'eq','!=':'ne'}[match[2].removeprefix('u')]
            if match[2].startswith('u'): relation = 'u'+relation
            condition = bool(BRANCH.compare(relation, floating=True)({0:self.value(match[1]),1:self.value(match[3])},0,{'r':0,'s':1},None)['exit'])
            if match[4]:
                if condition: next_pc += int(match[4])
            elif not condition: next_pc = self.skip(next_pc, then)
            elif otherwise: self.else_skips[self.skip(next_pc,then)] = self.skip(self.skip(next_pc,then),otherwise)
        elif match := re.fullmatch(r'(r\d+) = psr', text):
            self.set(match[1], self.carry << 1)
        elif match := re.fullmatch(r'(r\d+) = sextra\((r\d+), p:(\d+), l:(\d+)\)', text):
            length = int(match[4])
            self.set(match[1], signed((self.value(match[2]) >> int(match[3])) & ((1<<length)-1), length))
        elif match := re.fullmatch(r'if \(\((r\d+) & (r\d+)\) (==|!=) 0\) \{', text):
            condition = bool(self.value(match[1]) & self.value(match[2])) == (match[3] == '!=')
            if not condition: next_pc = self.skip(next_pc, then)
            elif otherwise: self.else_skips[self.skip(next_pc,then)] = self.skip(self.skip(next_pc,then),otherwise)
        elif match := re.fullmatch(r'(r\d+_r\d+) >>= (\d+)', text):
            self.set_pair(match[1], self.pair(match[1]) >> (int(match[2]) & 63))
        elif match := re.fullmatch(r'(r\d+) >>= (r\d+)', text):
            self.set(match[1], self.value(match[1]) >> (self.value(match[2]) & 31))
        elif match := re.fullmatch(r'(r\d+) = umin\((r\d+), (r\d+)\)', text):
            self.set(match[1], min(self.value(match[2]), self.value(match[3])))
        elif match := re.fullmatch(r'(r\d+) = (r\d+|0x[0-9a-fA-F]+) ([+-]) (r\d+|0x[0-9a-fA-F]+)(?: (\+ c|- !c))?', text):
            # Preserve carry here: the inherited storage convenience ALU path
            # does not need flags, but the IR energy accumulator does.
            carry = self.carry if match[5] == '+ c' else 1-self.carry if match[5] == '- !c' else 0
            self.set(match[1], self.binary(self.value(match[2]),match[3],self.value(match[4]),carry))
        else:
            return super().single_step()
        self.pc = next_pc
        return True
