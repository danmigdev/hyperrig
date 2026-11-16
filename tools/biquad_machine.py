"""Execute two pinned Q28 filter kernels in a bounded instruction/memory model.

Uses the existing decoder and arithmetic interpreter without altering either.
Saved-register stack frames are represented by their ABI footprint; the kernel
does not inspect those saved bytes. No peripheral or external service is used.
"""
from __future__ import annotations

import re

from dot_machine import DotMachine, MASK64, NativeProgram, signed


class BiquadProgram(NativeProgram):
    REGIONS = {
        "rounded": (0x01C15DEC, 0x01C15FDC),
        "residual": (0x01C15FDC, 0x01C16222),
    }

    def __init__(self, name):
        if name not in self.REGIONS:
            raise ValueError("unknown filter kernel")
        self.name = name
        super().__init__(name)
        self.visited = set()
        if any(text.endswith("  #") for text, _, _, _ in self.code.values()):
            raise ValueError("parallel packets are outside this verifier")

    def execute(self, samples, state):
        return BiquadMachine(self, samples, state).run()


class BiquadMachine(DotMachine):
    BUFFER, CONTEXT, STACK = 0x31000000, 0x32000000, 0x30001000

    def __init__(self, program, samples, state):
        if len(samples) > 128 or len(state) != 10:
            raise ValueError("expected 0..128 samples and ten state words")
        if any(not -(1 << 31) <= value < (1 << 31) for value in [*samples, *state[:9]]):
            raise ValueError("sample, coefficient or history is outside int32")
        if not 0 <= state[9] <= 0xFFFFFFFF:
            raise ValueError("initial residue is outside uint32")
        self.program = program
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(sp=self.STACK, r0=self.BUFFER, r1=len(samples), r2=self.CONTEXT)
        self.memory = {}
        self.pc, self.steps, self.carry = program.start, 0, 0
        self.samples, self.output, self.output_stride = len(samples), self.BUFFER, 1
        self.initializing = True
        for address, words in ((self.BUFFER, samples), (self.CONTEXT, state)):
            for i, word in enumerate(words):
                self.write(address + i * 4, word, 4)
        self.initializing = False
        self.written = set()

    def write(self, address, value, size):
        if not self.initializing:
            ranges = ((self.BUFFER, self.BUFFER + self.samples * 4),
                      (self.CONTEXT + 20, self.CONTEXT + (40 if self.program.name == "residual" else 36)),
                      (self.STACK - 56, self.STACK - 52))
            if not any(start <= address and address + size <= end for start, end in ranges):
                raise ValueError(f"write outside filter-owned memory at {address:#x}")
            self.written.update(range(address, address + size))
        super().write(address, value, size)

    def step(self):
        if self.pc not in self.program.code:
            raise ValueError(f"instruction escaped filter region at {self.pc:#x}")
        self.program.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        if match := re.fullmatch(r"(r\d+) = (r\d+) & (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.value(match[2]) & self.value(match[3]))
        elif match := re.fullmatch(r"(r\d+_r\d+) >>>= (\d+)", text):
            self.set_pair(match[1], (signed(self.pair(match[1]), 64) >> int(match[2])) & MASK64)
        elif text == "{pc, r15-r4} = [sp++]":
            if self.value("sp") != self.STACK - 52:
                raise ValueError("filter stack frame was not restored")
            return False
        else:
            return super().step()
        self.pc += size
        return True

    def run(self):
        samples = super().run()
        words = [self.read(self.CONTEXT + i * 4, 4) for i in range(10)]
        state = [signed(word) for word in words[:9]] + words[9:]
        return samples, state
