"""Execute the original five-section caller and its two numerical kernels."""
from __future__ import annotations

import re

from biquad_machine import BiquadProgram
from dot_machine import DotMachine, NativeProgram, MASK64, ROOT, signed

REGIONS = {"update": (0x01C051A2, 0x01C051F0), "process": (0x01C051F0, 0x01C0539C)}
STAGED, ACTIVE = 0x01C33240, 0x01C33320
CLOCK, AVERAGE, TOTAL, PENDING, ACTIVITY = 0x01C34198, 0x01C32DC8, 0x01C34470, 0x01C32E54, 0x01C34488
BUFFER, STACK = 0x31000000, 0x30001000
MAPPED = ((STAGED, 220), (ACTIVE, 220), (CLOCK, 4), (AVERAGE, 4),
          (TOTAL, 4), (PENDING, 5), (ACTIVITY, 1))


class ChainRegion(NativeProgram):
    REGIONS = REGIONS


class BiquadChainProgram:
    def __init__(self):
        self.regions = {name: ChainRegion(name) for name in REGIONS}
        self.kernels = {name: BiquadProgram(name) for name in BiquadProgram.REGIONS}
        self.code = {}
        for program in [*self.regions.values(), *self.kernels.values()]:
            self.code.update(program.code)
        if any(text.endswith("  #") for text, _, _, _ in self.code.values()):
            raise ValueError("unreviewed parallel packet in filter chain")

    def execute(self, memory, samples, operation="process", section=0, clock=None):
        if (len(memory) != len(MAPPED) or tuple(map(len, memory)) != tuple(size for _, size in MAPPED)
                or len(samples) > 128 or operation not in REGIONS
                or (operation == "update" and not 0 <= section < 5)
                or any(not -(1 << 31) <= value < (1 << 31) for value in samples)):
            raise ValueError("outside the filter-chain verifier domain")
        return BiquadChainMachine(self, memory, samples, operation, section, clock).run()


class BiquadChainMachine(DotMachine):
    def __init__(self, program, memory, samples, operation, section, clock):
        self.program, self.clock = program, clock
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(sp=STACK, r0=BUFFER if operation == "process" else section, r1=len(samples))
        self.memory = {base + i: byte for (base, _), data in zip(MAPPED, memory) for i, byte in enumerate(data)}
        for i, value in enumerate(samples):
            DotMachine.write(self, BUFFER + i*4, value, 4)
        self.pc = REGIONS[operation][0]
        self.samples, self.output, self.output_stride = len(samples), BUFFER, 1
        self.steps = self.carry = 0
        self.frames, self.returns, self.calls, self.kernel_calls = [], [], [], []
        self.visited, self.else_skips = set(), {}

    def snapshot(self):
        return tuple(bytes(self.memory[base + i] for i in range(size)) for base, size in MAPPED)

    def sample_values(self):
        return [signed(self.read(BUFFER + i*4, 4)) for i in range(self.samples)]

    def mutate(self, address, value, size):
        if any(address + i not in self.memory for i in range(size)):
            raise ValueError("clock mutation escaped initialized chain/sample memory")
        if not any(base <= address and address + size <= base + length
                   for base, length in (*MAPPED, (BUFFER, self.samples*4))):
            raise ValueError("clock mutation escaped public chain/sample buffers")
        DotMachine.write(self, address, value, size)

    def read(self, address, size):
        if 0x30000000 <= address < STACK and not self.value("sp") <= address <= address + size <= STACK:
            raise ValueError("read from released filter stack")
        return super().read(address, size)

    def write(self, address, value, size):
        if 0x30000000 <= address < STACK:
            if not self.value("sp") <= address <= address + size <= STACK:
                raise ValueError("filter stack write escaped allocated frame")
        elif not any(base <= address and address + size <= base + length
                     for base, length in ((ACTIVE, 220), (AVERAGE, 4), (TOTAL, 4),
                                          (PENDING, 5), (ACTIVITY, 1), (BUFFER, self.samples*4))):
            raise ValueError("instruction wrote outside active chain/sample state")
        return super().write(address, value, size)

    def address(self, expression):
        if match := re.fullmatch(r"\+\+(r\d+)=(r\d+)", expression):
            self.set(match[1], self.value(match[1]) + self.value(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def step(self):
        if self.pc in self.else_skips:
            self.pc = self.else_skips.pop(self.pc)
        if self.pc not in self.program.code:
            raise ValueError("chain execution escaped decoded function regions")
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        next_pc = self.pc + size
        if match := re.fullmatch(r"\[--sp\] = \{rets, r(\d+)-r4\}", text):
            saved = {f"r{i}": self.value(f"r{i}") for i in range(4, int(match[1])+1)}
            self.frames.append((saved, self.value("sp")))
            self.set("sp", self.value("sp") - 4*(len(saved)+1))
        elif re.fullmatch(r"\{pc, r\d+-r4\} = \[sp\+\+\]", text):
            saved, sp = self.frames.pop()
            if self.value("sp") != sp - 4*(len(saved)+1):
                raise ValueError("unbalanced chain/kernel frame")
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target not in self.program.code:
                raise ValueError("unreviewed direct chain call")
            for name, kernel in self.program.kernels.items():
                if target == kernel.start:
                    offset = self.value("r2") - ACTIVE
                    if (self.value("r0"), self.value("r1")) != (BUFFER, self.samples) or offset not in range(0, 220, 44):
                        raise ValueError("unexpected filter-call ABI")
                    self.kernel_calls.append((name, offset//44, self.samples))
            self.returns.append(next_pc)
            next_pc = target
        elif text == "call r0" and self.pc in (0x01C0527C, 0x01C05368):
            token = self.value("r0")
            if not token or token != self.read(CLOCK, 4) or not self.clock:
                raise ValueError("unreviewed indirect clock call")
            self.calls.append((token, self.snapshot(), self.sample_values()))
            result = self.clock(token, self)
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif match := re.fullmatch(r"(if|ifs) \((r\d+) (==|!=|<=|>=|<|>) (r\d+|-?\d+)\) \{", text):
            a, b = self.value(match[2]), self.value(match[4])
            if match[1] == "ifs":
                a, b = signed(a), signed(b)
            condition = {"==": a == b, "!=": a != b, "<=": a <= b,
                         ">=": a >= b, "<": a < b, ">": a > b}[match[3]]
            else_start = self.skip(next_pc, then)
            if not condition:
                next_pc = else_start
            elif otherwise:
                self.else_skips[else_start] = self.skip(else_start, otherwise)
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \(u\)", text):
            self.set(match[1], self.read(self.address(match[2]), 1))
        elif match := re.fullmatch(r"b\[(.+)\] = (r\d+)", text):
            self.write(self.address(match[1]), self.value(match[2]), 1)
        elif match := re.fullmatch(r"sp \+= (-?\d+)", text):
            after = self.value("sp") + int(match[1])
            if not 0x30000000 <= after <= STACK:
                raise ValueError("chain stack pointer escaped its arena")
            if after < self.value("sp"):
                for address in range(after, self.value("sp")):
                    self.memory.pop(address, None)
            self.set("sp", after)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) \* (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.value(match[2])*int(match[3], 16))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) & (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.value(match[2]) & int(match[3], 16))
        elif match := re.fullmatch(r"(r\d+_r\d+) >>>= (\d+)", text):
            self.set_pair(match[1], (signed(self.pair(match[1]), 64) >> int(match[2])) & MASK64)
        else:
            return super().step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 1000000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != STACK:
                    raise ValueError("unbalanced chain execution")
                return {"memory": self.snapshot(), "samples": self.sample_values(),
                        "calls": self.calls, "kernel_calls": self.kernel_calls,
                        "visited": self.visited, "steps": self.steps}
        raise ValueError("chain instruction budget exceeded")
