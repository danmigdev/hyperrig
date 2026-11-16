"""Execute complete DSP initialization/reset/startup bodies and original math.

The two startup services remain explicit synthetic boundaries. No peripheral,
physical rate or audio scheduling behavior is inferred from these comparisons.
"""
from __future__ import annotations

import re
import struct

from biquad_generator_machine import (BiquadGeneratorProgram, BiquadGeneratorMachine,
    REGIONS as MATH_REGIONS, PRIOR_REGIONS, MAPPED as GENERATOR_MAPPED,
    ROOT, DIVISOR, region_bytes)
from biquad_coefficients_machine import TABLE as PRIOR_TABLE, PRODUCER
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {
    "q16": (0x01C0539C, 0x01C053BC),
    "gain": (0x02028968, 0x0202898E),
    "setup": (0x0202898E, 0x020289D4),
    "reset_filters": (0x020289D4, 0x02028A34),
    "reset_slot": (0x020290CC, 0x02029112),
    "initialize": (0x02029112, 0x020291F8),
    "bind": (0x020291F8, 0x02029204),
    "startup": (0x020024EC, 0x020025CA),
}
CONFIGURATION, GUARD, SLOTS, ROUTES = 0x01C1F7D4, 0x01C2249C, 0x01C2C220, 0x01C2E5A0
CONTROL, FILTERS, CALLBACKS = 0x01C32DB0, 0x01C33030, 0x01C34190
MAPPED = ((CONFIGURATION, 68), (GUARD, 4), (SLOTS, 16*480), (ROUTES, 8*448),
          (CONTROL, 640), (FILTERS, 4*44), (CALLBACKS, 768))
TABLE = (0x0203A566, 0x0203A570)
STACK = 0x30001000
PLATFORM_INPUT, DYNAMICS_CONFIGURE = 0x01C010A6, 0x02030F8E
SERVICES = {PLATFORM_INPUT: 0, DYNAMICS_CONFIGURE: 3}
ARITIES = {"q16": 1, "gain": 1, "setup": 3, "reset_filters": 0,
           "reset_slot": 1, "initialize": 2, "bind": 2, "startup": 0}


class DspInitializationProgram(BiquadGeneratorProgram):
    def __init__(self):
        super().__init__()
        self.pre_initialization_code = set(self.code)
        self.initialization_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.initialization_table = region_bytes(app, *TABLE)
        self.divisor_reset = region_bytes(app, DIVISOR, DIVISOR+4)
        if struct.unpack("<5H", self.initialization_table) != (0, 150, 650, 2000, 4500):
            raise ValueError("unexpected initialization coefficient table")
        if struct.unpack("<I", self.divisor_reset)[0] != 48000:
            raise ValueError("unexpected reset-copy divisor")
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            raw = region_bytes(app, start, end)
            self.initialization_regions[name] = raw
            cursor = 0
            while cursor < len(raw):
                decoded = codec.decode(instructions, raw, cursor)
                if decoded is None:
                    raise ValueError(f"unsupported DSP initialization encoding at {start+cursor:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if cursor + size > len(raw):
                    raise ValueError("initialization instruction crosses a function boundary")
                self.code[start+cursor] = codec.format(instruction, fields), size, *counts
                cursor += size
        for pc in set(self.code) - self.pre_initialization_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, second_size, _, _ = self.code[pc+size]
                if not re.match(r"r\d+ = ", text) or second_size != 2 or "[" not in following:
                    raise ValueError("unreviewed initialization parallel packet")
                self.parallel_seconds.add(pc+size)

    def execute(self, memory, operation, *arguments, boundary=None):
        if (tuple(map(len, memory)) != tuple(size for _, size in MAPPED)
                or operation not in ARITIES or len(arguments) != ARITIES[operation]
                or any(not 0 <= value <= MASK32 for value in arguments)):
            raise ValueError("outside the DSP initialization call domain")
        if operation == "gain" and not -1280 <= signed(arguments[0]) <= 1280:
            raise ValueError("outside the bounded gain domain")
        if operation == "setup" and (not 1 <= arguments[0] <= 4 or
                not -1280 <= signed(arguments[1]) <= 1280 or arguments[2] >= 4):
            raise ValueError("outside the bounded second-table setup domain")
        if operation in ("initialize", "reset_filters") or (operation == "startup" and not memory[1][0]):
            if any(not -1280 <= value <= 1280 for value in struct.unpack_from("<5h", memory[4], 218)):
                raise ValueError("outside the stored-parameter domain")
        if operation == "startup" and not memory[1][0] and boundary is None:
            raise ValueError("startup requires both explicit service boundaries")
        return DspInitializationMachine(self, memory, operation, arguments, boundary).run()


class DspInitializationMachine(BiquadGeneratorMachine):
    def __init__(self, program, memory, operation, arguments, boundary):
        super().__init__(program, tuple(bytes(size) for _, size in GENERATOR_MAPPED), "exp", 0, 0, None)
        self.memory = {base+i: byte for (base, _), data in zip(MAPPED, memory) for i, byte in enumerate(data)}
        for base, data in ((PRIOR_TABLE, program.table), (TABLE[0], program.initialization_table)):
            self.memory.update({base+i: byte for i, byte in enumerate(data)})
        self.boundary, self.boundary_calls, self.internal_calls = boundary, [], []
        self.pc = REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(arguments[:4])})
        if operation == "setup":
            self.regs.update(r0=arguments[0], r1=arguments[1], r2=FILTERS+44*arguments[2])
        self.writes = []

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(size)) for base, size in MAPPED)

    def write(self, address, value, size):
        if 0x30000000 <= address < STACK:
            if not self.value("sp") <= address <= address+size <= STACK:
                raise ValueError("initialization stack write escaped allocated frame")
        elif not any(base <= address and address+size <= base+length for base, length in MAPPED):
            raise ValueError(f"initialization write escaped mapped public state: {address:#x}")
        self.writes.append((address, value & ((1 << (size*8))-1), size))
        DotMachine.write(self, address, value, size)

    def mutate(self, address, value, size):
        if not any(base <= address and address+size <= base+length for base, length in MAPPED):
            raise ValueError("startup callback mutation escaped public state")
        self.write(address, value, size)

    def address(self, expression):
        if match := re.fullmatch(r"(r\d+)\+(r\d+)", expression):
            return (self.value(match[1]) + self.value(match[2])) & MASK32
        return super().address(expression)

    def single_step(self):
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc+size
        if text == "[--sp] = {rets, r5, r4}":
            self.visited.add(self.pc)
            self.frames.append(({name: self.value(name) for name in ("r4", "r5")}, self.value("sp")))
            self.set("sp", self.value("sp")-12)
        elif text == "{pc, r5, r4} = [sp++]":
            self.visited.add(self.pc)
            saved, sp = self.frames.pop()
            if set(saved) != {"r4", "r5"} or self.value("sp") != sp-12:
                raise ValueError("unbalanced second-table setup frame")
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target in SERVICES:
                self.visited.add(self.pc)
                args = tuple(self.value(f"r{i}") if i < SERVICES[target] else 0 for i in range(3))
                before = self.snapshot()
                result = self.boundary(target, args, self)
                self.boundary_calls.append((target, args, before, self.snapshot()))
                for name in ("r0", "r1", "r2", "r3"):
                    self.set(name, 0xBAD0C0DE)
                self.set("r0", result)
            elif target == PRODUCER[0]:
                self.visited.add(self.pc)
                destination = self.value("r0")
                section, offset = divmod(destination-FILTERS, 44)
                if offset or not 0 <= section < 4:
                    raise ValueError("unreviewed initialization coefficient destination")
                request = (self.value("r1"), self.value("r2"), self.value("r3"), self.read(self.value("sp"), 4))
                self.production_calls.append((section, request, self.snapshot()))
                self.math_calls.append(("generate", destination))
                self.returns.append(next_pc)
                next_pc = target
            else:
                if target in {start for start, _ in REGIONS.values()}:
                    self.internal_calls.append((target, self.value("r0"), self.value("r1")))
                return super().single_step()
        elif match := re.fullmatch(r"h\[(.+)\] = (r\d+)", text):
            self.visited.add(self.pc)
            self.write(self.address(match[1]), self.value(match[2]), 2)
        elif match := re.fullmatch(r"\[(.+)\] = (0x[0-9a-fA-F]+)", text):
            self.visited.add(self.pc)
            self.write(self.address(match[1]), int(match[2], 16), 4)
        elif match := re.fullmatch(r"(r\d+_r\d+) = (0)", text):
            self.visited.add(self.pc)
            self.set_pair(match[1], 0)
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 100000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != STACK or self.calls:
                    raise ValueError("unbalanced initialization or scripted coefficient math")
                return {"memory": self.snapshot(), "value": self.value("r0"), "visited": self.visited,
                    "steps": self.steps, "boundary_calls": self.boundary_calls, "internal_calls": self.internal_calls,
                    "production_calls": self.production_calls, "normalization_calls": self.normalization_calls,
                    "math_calls": self.math_calls, "writes": self.writes}
        raise ValueError("initialization instruction budget exceeded")
