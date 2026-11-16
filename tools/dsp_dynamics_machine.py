"""Execute dynamics configuration/getters and startup with one platform boundary."""
from __future__ import annotations
import re

from dsp_initialization_machine import (DspInitializationProgram, DspInitializationMachine,
    REGIONS as INITIALIZATION_REGIONS, MAPPED, ROOT, DIVISOR, CONFIGURATION,
    CONTROL, CALLBACKS, PLATFORM_INPUT, DYNAMICS_CONFIGURE, TABLE,
    MATH_REGIONS, PRIOR_REGIONS, PRIOR_TABLE, region_bytes)
from dot_machine import DotMachine, MASK32, signed
from pi32v2isa import codec, table

REGIONS = {"configure": (0x02030F8E, 0x0203104E),
           "get": (0x0203104E, 0x0203106C), "meter": (0x0203106C, 0x0203108E)}
OUTPUT = 0x31010000
RESET_CONFIGURATION = (0x01C1F7F0, 0x01C1F818)
ARITIES = {"configure": 3, "get": 0, "meter": 1, "startup": 0}


class DspDynamicsProgram(DspInitializationProgram):
    def __init__(self):
        super().__init__()
        self.pre_dynamics_code, self.dynamics_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.reset_configuration = region_bytes(app, *RESET_CONFIGURATION)
        if self.reset_configuration.hex() != "6400fdff6400010280bb0000b00400003700000002000000ffff7f00010000000000000180bb0000":
            raise ValueError("unreviewed dynamics reset-copy configuration")
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            raw = region_bytes(app, start, end)
            self.dynamics_regions[name] = raw
            cursor = 0
            while cursor < len(raw):
                decoded = codec.decode(instructions, raw, cursor)
                if decoded is None:
                    raise ValueError(f"unsupported dynamics instruction at {start+cursor:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if cursor + size > len(raw):
                    raise ValueError("dynamics instruction crosses function boundary")
                self.code[start+cursor] = codec.format(instruction, fields), size, *counts
                cursor += size
        for pc in set(self.code) - self.pre_dynamics_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, second_size, _, _ = self.code[pc+size]
                if not re.match(r"r\d+ = ", text) or second_size != 2 or "[" not in following:
                    raise ValueError("unreviewed dynamics parallel packet")
                self.parallel_seconds.add(pc+size)

    def execute(self, memory, operation, *arguments, boundary=None):
        if (tuple(map(len, memory)) != tuple(size for _, size in MAPPED) or operation not in ARITIES
                or len(arguments) != ARITIES[operation] or any(not 0 <= x <= MASK32 for x in arguments)):
            raise ValueError("outside the dynamics call domain")
        if operation == "configure" and not int.from_bytes(memory[0][36:40], "little"):
            raise ValueError("zero divisor lies outside the terminating dynamics domain")
        if operation == "meter" and arguments[0] > 3:
            raise ValueError("invalid optional-output mask")
        if operation == "startup" and not memory[1][0]:
            import struct
            if boundary is None or any(not -1280 <= x <= 1280 for x in struct.unpack_from("<5h", memory[4], 218)):
                raise ValueError("startup requires valid parameters and its platform boundary")
        return DspDynamicsMachine(self, memory, operation, arguments, boundary).run()


class DspDynamicsMachine(DspInitializationMachine):
    def __init__(self, program, memory, operation, arguments, boundary):
        super().__init__(program, memory, "startup", (), boundary)
        self.dynamics_calls = []
        self.pc = INITIALIZATION_REGIONS["startup"][0] if operation == "startup" else REGIONS[operation][0]
        for i in range(3):
            DotMachine.write(self, OUTPUT+4*i, 0xA5A5A500+i, 4)
        self.regs.update({f"r{i}": value for i, value in enumerate(arguments)})
        if operation == "get":
            self.regs.update(r0=OUTPUT, r1=OUTPUT+4, r2=OUTPUT+8)
        elif operation == "meter":
            self.regs.update(r0=OUTPUT if arguments[0] & 1 else 0, r1=OUTPUT+4 if arguments[0] & 2 else 0)

    def write(self, address, value, size):
        if OUTPUT <= address and address+size <= OUTPUT+12:
            self.writes.append((address, value & ((1 << (size*8))-1), size))
            DotMachine.write(self, address, value, size)
            return
        return super().write(address, value, size)

    def single_step(self):
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc+size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target == DYNAMICS_CONFIGURE:
                self.visited.add(self.pc)
                self.dynamics_calls.append((tuple(self.value(f"r{i}") for i in range(3)), self.snapshot()))
                self.returns.append(next_pc)
                self.pc = target
                return True
        if match := re.fullmatch(r"(r\d+) = smin\((r\d+), (r\d+)\)", text):
            self.visited.add(self.pc)
            self.set(match[1], min(signed(self.value(match[2])), signed(self.value(match[3]))))
            self.pc = next_pc
            return True
        if match := re.fullmatch(r"(r\d+) = (r\d+) & (r\d+)", text):
            self.visited.add(self.pc)
            self.set(match[1], self.value(match[2]) & self.value(match[3]))
            self.pc = next_pc
            return True
        return super().single_step()

    def run(self):
        result = super().run()
        result.update(outputs=tuple(self.read(OUTPUT+4*i, 4) for i in range(3)), dynamics_calls=self.dynamics_calls)
        return result
