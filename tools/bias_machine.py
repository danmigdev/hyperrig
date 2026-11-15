"""Execute two original A2L-parser fragments, not a whole-parser emulation.

The entry registers and the raw bias at r8 are supplied as parser preconditions.
Only shifts 0..31 accepted by the original conv/head parser are exercised.
Byte extraction and bit tests below extend the existing restricted interpreter.
"""
import re

from dot_machine import DotMachine, NativeProgram, signed


class BiasMachine(DotMachine):
    def __init__(self, program, bias, shift):
        if not -(1 << 63) <= bias < 1 << 63 or not 0 <= shift <= 31:
            raise ValueError("outside parser bias domain")
        self.program = program
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs["sp"] = 0x30001000
        self.memory = {}
        self.carry, self.steps, self.pc = 0, 0, program.start
        if program.kind == "head":
            self.set("r1", shift)
            self.set_pair("r5_r4", bias)
        else:
            self.set("r9", shift)
            self.set("r8", 0x32000000)
            self.write(0x32000000, bias, 8)

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if match := re.fullmatch(r"(r\d+) = sextra\((r\d+), p:0, l:8\)", text):
            self.set(match[1], signed(self.value(match[2]) & 255, 8))
        elif match := re.fullmatch(r"(r\d+) = (r\d+)\.b0 \((s|u)\)", text):
            value = self.value(match[2]) & 255
            self.set(match[1], signed(value, 8) if match[3] == "s" else value)
        elif match := re.fullmatch(r"if \(\((r\d+) & (0x[0-9A-Fa-f]+|\d+)\) == 0\) goto (-?\d+)", text):
            if not self.value(match[1]) & int(match[2], 0):
                self.pc += int(match[3])
        else:
            return super().step()
        self.pc += size
        return True

    def run(self):
        while self.pc != self.program.end and self.steps < 256:
            if self.pc not in self.program.code:
                raise ValueError(f"bias fragment escaped at {self.pc:#x}")
            self.steps += 1
            if not self.step():
                raise ValueError("unexpected return in parser fragment")
        if self.pc != self.program.end:
            raise ValueError("bias fragment instruction budget exceeded")
        return signed(self.pair("r5_r4"), 64) if self.program.kind == "head" else signed(self.value("r2"))


class BiasProgram(NativeProgram):
    def __init__(self, kind):
        if kind not in ("head", "conv"):
            raise ValueError("expected head or conv bias fragment")
        self.kind = kind
        super().__init__(kind + "_bias")

    def execute(self, bias, shift):
        return BiasMachine(self, bias, shift).run()
