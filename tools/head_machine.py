"""Execute the original three-channel head helper in a bounded memory model.

The head uses one register-count REP with a single MAC instruction. Positive
count/decrement semantics are backed by pi32v2-isa's FM1 hardware report v3;
zero counts are deliberately excluded. This remains an interpreter, not a
claim that the recovered code has executed on this user's Tank Mini.
"""
from dot_machine import DotMachine, NativeProgram, signed


class HeadMachine(DotMachine):
    def __init__(self, program, inputs, weights, history, position, shift, bias):
        self.program = program
        self.samples = len(inputs) // 3
        self.ring_frames = len(history) // 3 - 64
        kernel_frames = len(weights) // 3
        if (len(inputs) % 3 or len(weights) % 3 or len(history) % 3 or
                not 1 <= self.samples <= 64 or not 1 <= shift <= 31 or
                not 1 <= kernel_frames <= min(65, self.ring_frames) or
                self.ring_frames < 64 or not 0 <= position < self.ring_frames):
            raise ValueError("outside the recovered head's verification domain")
        self.memory = {}
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs["sp"] = 0x30001000
        self.pc, self.steps, self.carry = program.start, 0, 0
        self.output, self.output_stride = 0x31000000, 1
        self.history, self.context = 0x34000000, 0x35000000
        self.history_words = len(history)
        for address, values, width in ((0x32000000, inputs, 4),
                                        (0x33000000, weights, 2),
                                        (self.history, history, 4),
                                        (self.output, [0x5A5A5A5A] * self.samples, 4)):
            for i, value in enumerate(values):
                self.write(address + i * width, value, width)
        fields = (0x32000000, self.history, position * 12, self.ring_frames * 12,
                  64 * 12, (kernel_frames - 1) * 12, 0x33000000, self.output,
                  self.samples, len(weights), (1 << (shift - 1)) - 1, shift,
                  bias & 0xFFFFFFFF, (bias >> 32) & 0xFFFFFFFF)
        for i, value in enumerate(fields):
            self.write(self.context + i * 4, value, 4)
        self.regs["r0"] = self.context

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if text == "rep 4 r2 {":
            if not 1 <= self.value("r2") <= 195:
                raise ValueError("unsupported REP count")
            body = self.pc + size
            body_text, body_size, _, _ = self.program.code[body]
            if body_size != 4 or body_text != "r1_r0 += h[r6 ++= 2]*[r4 ++= 4] (s)":
                raise ValueError("unsupported REP body")
            while self.value("r2"):
                self.pc = body
                self.step()
                self.steps += 1
                self.set("r2", self.value("r2") - 1)
            self.pc = body + body_size
            return True
        if text == "r1_r0 += h[r6 ++= 2]*[r4 ++= 4] (s)":
            weight = signed(self.read(self.value("r6"), 2), 16)
            value = signed(self.read(self.value("r4"), 4))
            self.set_pair("r1_r0", self.pair("r1_r0") + weight * value)
            self.set("r6", self.value("r6") + 2)
            self.set("r4", self.value("r4") + 4)
            self.pc += size
            return True
        return super().step()

    def run(self):
        output = super().run()
        history = [signed(self.read(self.history + i * 4, 4)) for i in range(self.history_words)]
        position = self.read(self.context + 8, 4) // 12
        return output, history, position


class HeadProgram(NativeProgram):
    def __init__(self):
        super().__init__("head3")

    def execute(self, inputs, weights, history, position, shift, bias):
        return HeadMachine(self, inputs, weights, history, position, shift, bias).run()
