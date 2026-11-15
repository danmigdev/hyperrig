"""Restricted execution of the original mono-to-three-channel input kernel."""
import re
from dot_machine import DotMachine, NativeProgram, signed


class RechannelMachine(DotMachine):
    def __init__(self, program, inputs, weights, history, position, shift):
        self.program, self.samples = program, len(inputs)
        self.ring_frames = len(history) // 3 - 64
        if (not 1 <= self.samples <= 64 or len(weights) != 3 or len(history) % 3 or
                self.ring_frames < 64 or not 0 <= position < self.ring_frames or not 1 <= shift <= 31):
            raise ValueError("outside rechannel verification domain")
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs["sp"] = 0x30001000
        self.memory = {}
        self.pc, self.steps, self.carry = program.start, 0, 0
        self.output, self.output_stride = 0x31000000, 1
        self.history, self.context = 0x34000000, 0x35000000
        self.history_words = len(history)
        for address, values in ((0x32000000, inputs), (self.history, history),
                                (self.output, [0x5A5A5A5A] * self.samples)):
            for i, value in enumerate(values):
                self.write(address + i * 4, value, 4)
        half = 1 << (shift - 1)
        fields = (0x32000000, self.output, self.history + position * 12, 0x32000000 + self.samples * 4,
                  *weights, shift, half, 0, self.history + 64 * 12, self.ring_frames * 12,
                  self.history + self.ring_frames * 12, self.history)
        for i, value in enumerate(fields):
            self.write(self.context + i * 4, value, 4)
        self.regs["r0"] = self.context

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if match := re.fullmatch(r"(r\d+_r\d+) = d\[(.+)\]", text):
            self.set_pair(match[1], self.read(self.address(match[2]), 8))
            self.pc += size
            return True
        return super().step()

    def run(self):
        dry = super().run()
        history = [signed(self.read(self.history + i * 4, 4)) for i in range(self.history_words)]
        return dry, history, (self.value("r2") - self.history) // 12


class RechannelProgram(NativeProgram):
    def __init__(self):
        super().__init__("rechannel3")

    def execute(self, inputs, weights, history, position, shift):
        return RechannelMachine(self, inputs, weights, history, position, shift).run()
