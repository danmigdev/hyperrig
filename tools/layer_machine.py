"""Execute the five original three-channel layer kernels with caller-built contexts.

The 200-byte context ABI is reconstructed from 0x01c12a54. This deliberately
does not emulate that wrapper or claim hardware timings. Unknown instructions
and reads outside initialized memory are rejected by the base interpreter.
"""
import re
from dot_machine import DotMachine, NativeProgram, signed


class LayerMachine(DotMachine):
    def __init__(self, program, p, history, position, dry, sums, output_history, output_position):
        self.program = program
        self.frames, self.samples = len(dry), len(sums)
        ring, out_ring = len(history) // 3 - 64, len(output_history) // 3 - 64
        k, dilation = p["kernel"], p["dilation"]
        if (not 1 <= self.frames <= 64 or self.samples != self.frames * 3 or not 1 <= k <= 15 or
                dilation < 1 or ring < (k - 1) * dilation + 64 or out_ring < 64 or
                not 0 <= position < ring or not 0 <= output_position < out_ring or
                any(not 1 <= p[key] <= 31 for key in ("conv_shift", "mix_shift", "linear_shift", "sum_shift")) or
                not 0 <= p["mix_shift"] - p["conv_shift"] <= 31 or not -31 <= p["residual_shift"] <= 31):
            raise ValueError("outside native layer verification domain")
        if program.kind != "generic":
            taps = 15 if "15" in program.kind else 6
            if k != taps or (program.kind.endswith("_shift") != (p["residual_shift"] != 0)):
                raise ValueError("wrong specialization for this layer")
        self.memory, self.regs = {}, {f"r{i}": 0 for i in range(16)}
        self.regs["sp"] = 0x30001000
        self.pc, self.steps, self.carry = program.start, 0, 0
        self.output, self.output_stride = 0x31000000, 1
        self.context, self.out_history = 0x35000000, 0x36000000
        self.history_words = len(output_history)
        weights = p["conv_weights"] + p["mix_weights"]
        for address, values, width in ((self.output, sums, 4), (0x32000000, dry, 4),
                                       (0x33000000, weights, 2), (0x34000000, history, 4),
                                       (self.out_history, output_history, 4),
                                       (0x37000000, p["linear_weights"], 2)):
            for i, value in enumerate(values):
                self.write(address + i * width, value, width)
        for offset in range(0, 200, 4):
            self.write(self.context + offset, 0, 4)
        for tap in range(k):
            index = (position - (k - 1 - tap) * dilation) % ring
            self.write(self.context + tap * 4, 0x34000000 + index * 12, 4)
        fields = {60: 0x34000000 + position * 12, 88: 0x33000000, 92: 0x32000000,
                  96: self.output, 100: self.out_history, 104: 0x37000000,
                  108: 1 << (p["conv_shift"] - 1), 112: p["conv_shift"],
                  116: p["conv_bias"][0], 120: p["conv_bias"][1], 124: p["conv_bias"][2],
                  128: p["slope_q24"], 132: p["sum_shift"], 136: p["sum_shift"] - 1,
                  140: p["linear_shift"], 144: p["residual_shift"],
                  148: p["mix_shift"] - p["conv_shift"], 152: output_position * 12,
                  156: out_ring * 12, 160: self.frames * 12, 164: k, 168: self.context + k * 4,
                  172: p["residual_shift"] - 1, 176: -p["residual_shift"],
                  180: p["residual_shift"] + 32, 184: 768, 196: 1}
        for offset, value in fields.items():
            self.write(self.context + offset, value, 4)
        for i, bias in enumerate(p["linear_bias"]):
            self.write(self.context + 64 + i * 8, bias + (1 << (p["linear_shift"] - 1)), 8)
        self.regs["r0"] = self.context

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if match := re.fullmatch(r"(r\d+_r\d+) = d\[(.+)\]", text):
            self.set_pair(match[1], self.read(self.address(match[2]), 8))
        elif match := re.fullmatch(r"(r\d+_r\d+) \+= h\[(r\d+) \+\+= 2\]\*(r\d+) \(s\)", text):
            weight = signed(self.read(self.value(match[2]), 2), 16)
            self.set_pair(match[1], self.pair(match[1]) + weight * signed(self.value(match[3])))
            self.set(match[2], self.value(match[2]) + 2)
        elif match := re.fullmatch(r"(r\d+_r\d+) >>>= (\d+)", text):
            self.set_pair(match[1], signed(self.pair(match[1]), 64) >> int(match[2]))
        elif match := re.fullmatch(r"(r\d+) >>= (r\d+)", text):
            self.set(match[1], self.value(match[1]) >> (self.value(match[2]) & 31))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) & (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.value(match[2]) & int(match[3], 0))
        else:
            return super().step()
        self.pc += size
        return True

    def run(self):
        sums = super().run()
        history = [signed(self.read(self.out_history + i * 4, 4)) for i in range(self.history_words)]
        return sums, history, self.read(self.context + 188, 4) // 12


class LayerProgram(NativeProgram):
    def __init__(self, kind="generic"):
        self.kind = kind
        super().__init__("layer_" + kind if kind == "generic" else "layer" + kind)

    def execute(self, parameters, history, position, dry, sums, output_history, output_position):
        return LayerMachine(self, parameters, history, position, dry, sums, output_history, output_position).run()
