"""Execute complete startup-input and four-section processing bodies offline.

Original instructions perform every coefficient, filter and ramp operation.
There are no synthetic services in these entries. The surrounding audio task,
hardware configuration and scheduling are not represented by this model.
"""
from __future__ import annotations
import re
import struct
import sys

from dsp_dynamics_machine import (DspDynamicsProgram, DspDynamicsMachine,
    REGIONS as DYNAMICS_REGIONS, INITIALIZATION_REGIONS, MAPPED as DSP_MAPPED,
    ROOT, CONFIGURATION, CONTROL, CALLBACKS, PLATFORM_INPUT, DYNAMICS_CONFIGURE,
    TABLE, MATH_REGIONS, PRIOR_REGIONS, PRIOR_TABLE, RESET_CONFIGURATION, region_bytes)
from dsp_initialization_machine import FILTERS, STACK
from biquad_machine import BiquadProgram
from biquad_coefficients_machine import FLOAT, load_semantics
from dot_machine import DotMachine, MASK32, MASK64, signed
from pi32v2isa import codec, table

sys.path.insert(0, str(ROOT/"upstream/pi32v2-isa/tools/hwtest"))
ARITHMETIC = load_semantics("r")
REGIONS = {
    "cached": (0x01C01058, 0x01C010A6),
    "input": (0x01C010A6, 0x01C010E4),
    "update": (0x01C053BC, 0x01C05406),
    "block": (0x01C05406, 0x01C054A6),
    "process": (0x01C054A6, 0x01C0558C),
    "ramp": (0x01C19D36, 0x01C19EDE),
}
PLATFORM, CACHE, STAGED, TRANSITION = 0x01C1F1AC, 0x01C26A88, 0x01C330E0, 0x01C33190
MAPPED = (*DSP_MAPPED, (PLATFORM, 12), (CACHE, 8), (STAGED, 176), (TRANSITION, 176))
BUFFER = 0x31000000
ARITIES = {"cached": 0, "input": 0, "startup": 0, "update": 0,
           "block": 1, "ramp": 2, "process": 0}
STATIC = {"four_section_call": (0x01C02632, 0x01C0263C),
          "five_section_call": (0x01C026DA, 0x01C026E4)}


class DspAudioPathProgram(DspDynamicsProgram):
    def __init__(self):
        super().__init__()
        self.pre_audio_code = set(self.code)
        self.audio_regions = {}
        app = (ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.static = {name: region_bytes(app, *bounds) for name, bounds in STATIC.items()}
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            raw = self.audio_regions[name] = region_bytes(app, start, end)
            cursor = 0
            while cursor < len(raw):
                decoded = codec.decode(instructions, raw, cursor)
                if decoded is None:
                    raise ValueError(f"unsupported audio-path instruction at {start+cursor:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if cursor+size > len(raw):
                    raise ValueError("audio-path instruction crosses function boundary")
                self.code[start+cursor] = codec.format(instruction, fields), size, *counts
                cursor += size
        self.kernels = {name: BiquadProgram(name) for name in BiquadProgram.REGIONS}
        for kernel in self.kernels.values():
            self.code.update(kernel.code)
        for pc in set(self.code)-self.pre_audio_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, second_size, _, _ = self.code[pc+size]
                if not re.match(r"r\d+ = ", text) or second_size != 2 or "[" not in following:
                    raise ValueError("unreviewed audio-path parallel packet")
                self.parallel_seconds.add(pc+size)

    def execute(self, memory, operation, samples=(), *arguments):
        if (tuple(map(len, memory)) != tuple(size for _, size in MAPPED)
                or operation not in ARITIES or len(arguments) != ARITIES[operation]
                or any(not 0 <= value <= MASK32 for value in arguments)
                or len(samples) > 128 or any(not -(1 << 31) <= value < (1 << 31) for value in samples)
                or (operation == "block" and not samples)):
            raise ValueError("outside the bounded audio-path call domain")
        if operation == "startup" and not memory[1][0]:
            if any(not -1280 <= value <= 1280 for value in struct.unpack_from("<5h", memory[4], 218)):
                raise ValueError("startup stored parameters outside inherited domain")
        return DspAudioPathMachine(self, memory, operation, samples, arguments).run()


class DspAudioPathMachine(DspDynamicsMachine):
    def __init__(self, program, memory, operation, samples, arguments):
        super().__init__(program, memory[:len(DSP_MAPPED)], "startup", (), None)
        for (base, _), data in zip(MAPPED[len(DSP_MAPPED):], memory[len(DSP_MAPPED):]):
            self.memory.update({base+i: byte for i, byte in enumerate(data)})
        self.samples = len(samples)
        for i, value in enumerate(samples):
            DotMachine.write(self, BUFFER+4*i, value, 4)
        self.pc = INITIALIZATION_REGIONS["startup"][0] if operation == "startup" else REGIONS[operation][0]
        self.regs.update(r0=BUFFER, r1=len(samples), r2=arguments[0] if arguments else 0,
                         r3=arguments[1] if len(arguments) > 1 else 0)
        self.audio_calls, self.kernel_calls = [], []

    def snapshot(self):
        return tuple(bytes(self.memory[base+i] for i in range(size)) for base, size in MAPPED)

    def sample_values(self):
        return tuple(signed(self.read(BUFFER+4*i, 4)) for i in range(self.samples))

    def write(self, address, value, size):
        if 0x30000000 <= address < STACK:
            if not self.value("sp") <= address <= address+size <= STACK:
                raise ValueError("audio-path stack write escaped frame")
        elif not any(base <= address and address+size <= base+length
                     for base, length in (*MAPPED, (BUFFER, self.samples*4))):
            raise ValueError(f"audio-path write escaped public memory at {address:#x}")
        self.writes.append((address, value & ((1 << (size*8))-1), size))
        DotMachine.write(self, address, value, size)

    def single_step(self):
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc+size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc+int(match[1])
            if target in {start for start, _ in REGIONS.values()}:
                self.audio_calls.append((target, tuple(self.value(f"r{i}") for i in range(4))))
            if target == PLATFORM_INPUT:
                self.visited.add(self.pc)
                self.returns.append(next_pc)
                self.pc = target
                return True
            for name, kernel in self.program.kernels.items():
                if target == kernel.start:
                    address, count, context = (self.value(f"r{i}") for i in range(3))
                    if (not BUFFER <= address <= address+count*4 <= BUFFER+self.samples*4
                            or (address-BUFFER) % 4 or context-FILTERS not in range(0, 176, 44)):
                        raise ValueError("unreviewed four-section kernel ABI")
                    self.kernel_calls.append((name, (context-FILTERS)//44, (address-BUFFER)//4, count))
        self.visited.add(self.pc)
        if match := re.fullmatch(r"\[--sp\] = \{r(\d+)-r4\}", text):
            saved = {f"r{i}": self.value(f"r{i}") for i in range(4, int(match[1])+1)}
            self.frames.append((saved, self.value("sp")))
            self.set("sp", self.value("sp")-4*len(saved))
        elif match := re.fullmatch(r"\{r(\d+)-r4\} = \[sp\+\+\]", text):
            saved, sp = self.frames.pop()
            if self.value("sp") != sp-4*len(saved) or len(saved) != int(match[1])-3:
                raise ValueError("unbalanced gain-ramp save area")
            self.regs.update(saved, sp=sp)
        elif match := re.fullmatch(r"(r\d+_r\d+) = (r\d+) \* (r\d+) \(([su])\)", text):
            writes, _ = ARITHMETIC.MODELS[f"mul.{match[4]}.prr"](
                {0: self.value(match[2]), 1: self.value(match[3])}, 0, {"r": 2, "s": 0, "t": 1})
            self.set_pair(match[1], writes[2] | writes[3] << 32)
        elif match := re.fullmatch(r"(r\d+_r\d+) = (r\d+_r\d+) / (r\d+) \(([su])\)", text):
            numerator = self.pair(match[2])
            writes, _ = FLOAT.divide(True, match[4] == "s")(
                {0: numerator & MASK32, 1: numerator >> 32, 2: self.value(match[3])},
                0, {"r": 3, "s": 0, "t": 2})
            self.set_pair(match[1], writes[3] | writes[4] << 32)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(([su])\)", text):
            writes, _ = FLOAT.divide(False, match[4] == "s")(
                {0: self.value(match[2]), 1: self.value(match[3])}, 0, {"r": 2, "s": 0, "t": 1})
            self.set(match[1], writes[2])
        elif match := re.fullmatch(r"(r\d+_r\d+) (<<=|>>>=) (\d+)", text):
            value, amount = self.pair(match[1]), int(match[3]) & 63
            self.set_pair(match[1], (value << amount if match[2] == "<<=" else signed(value, 64) >> amount) & MASK64)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) & (0x[0-9a-fA-F]+)", text):
            self.set(match[1], self.value(match[2]) & int(match[3], 16))
        elif match := re.fullmatch(r"(r\d+) \|= (r\d+)", text):
            self.set(match[1], self.value(match[1]) | self.value(match[2]))
        elif match := re.fullmatch(r"if \(\((r\d+) & (\d+)\) (==|!=) 0\) goto (-?\d+)", text):
            condition = bool(self.value(match[1]) & int(match[2]))
            if condition == (match[3] == "!="):
                next_pc += int(match[4])
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        result = super().run()
        result.update(samples=self.sample_values(), audio_calls=self.audio_calls, kernel_calls=self.kernel_calls)
        if result["boundary_calls"]:
            raise ValueError("audio-path comparison reached a scripted service")
        return result
