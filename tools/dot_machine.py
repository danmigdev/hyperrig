"""Restricted instruction interpreter for recovered UltraRig DSP helpers.

This executes the decoded firmware instructions, not the reconstructed C
formula. It is NOT a general pi32v2 emulator or a hardware validation.
Only the explicitly listed code regions are accepted; unknown instructions,
escaping branches, uninitialized reads and dependent parallel pairs fail.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "upstream/pi32v2-isa"))
from pi32v2isa import codec, table

MASK32 = (1 << 32) - 1
MASK64 = (1 << 64) - 1


def signed(value, bits=32):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


class NativeProgram:
    REGIONS = {
        "dot_i16": (0x01C12608, 0x01C126F4),
        "dot_i32": (0x01C126F4, 0x01C127DE),
        "head3": (0x01C130B4, 0x01C1318E),
        "rechannel3": (0x01C1453C, 0x01C145FE),
        "conv_bias": (0x02032586, 0x02032618),
        "head_bias": (0x020327DE, 0x0203280C),
        "layer6": (0x01C1318E, 0x01C1349C),
        "layer6_shift": (0x01C1349C, 0x01C13822),
        "layer15": (0x01C13822, 0x01C13D16),
        "layer15_shift": (0x01C13D16, 0x01C14282),
        "layer_generic": (0x01C14282, 0x01C1452A),
    }

    def __init__(self, name):
        self.start, self.end = self.REGIONS[name]
        image = ROOT / "analysis/firmware/m571_g_app/app.bin"
        raw = image.read_bytes()
        original = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
        expected = json.loads((ROOT / "research/input-manifest.json").read_text())["firmware_images"]
        entry = next(item for item in expected if item["file"] == original.name)
        if hashlib.sha256(original.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("original firmware does not match the pinned sample")
        # Require the decoded copy to be the actual pinned application, too.
        sys.path.insert(0, str(ROOT))
        from hyperrig.jieli import unpack_app
        if unpack_app(original.read_bytes())[2]["app.bin"] != raw:
            raise ValueError("decoded application differs from pinned firmware")
        if self.start >= 0x02000120:
            offset = self.start - 0x02000120
        else:
            offset = 0x02056780 - 0x02000120 + self.start - 0x01C00000
        self.raw = raw[offset:offset + self.end - self.start]
        instructions = table.load()
        self.code = {}
        cursor = 0
        while cursor < len(self.raw):
            result = codec.decode(instructions, self.raw, cursor)
            if result is None:
                raise ValueError(f"unsupported encoding at {self.start + cursor:#x}")
            instruction, fields, size = result
            text = codec.format(instruction, fields)
            then = otherwise = 0
            if instruction.block and "then" in instruction.block:
                def count(kind):
                    field_name = instruction.block[kind]
                    spec = instruction.fields[field_name]
                    return fields[field_name] * spec.scale + spec.add
                then, otherwise = count("then"), count("else")
            self.code[self.start + cursor] = (text, size, then, otherwise)
            cursor += size
        for pc, (text, size, _, _) in self.code.items():
            if text.endswith("  #"):
                following = self.code[pc + size][0]
                match = re.match(r"(r\d+) = ", text)
                if not match or re.search(r"\b" + match[1] + r"\b", following):
                    raise ValueError("interpreter cannot serialize a dependent parallel pair")


class DotProgram(NativeProgram):
    def __init__(self, weight_bits):
        if weight_bits not in (16, 32):
            raise ValueError("only 16/32-bit weight helpers are supported")
        self.weight_bits = weight_bits
        super().__init__(f"dot_i{weight_bits}")

    def execute(self, inputs, weights, samples, input_stride=1, output_stride=1, shift=0):
        return DotMachine(self, inputs, weights, samples, input_stride, output_stride, shift).run()


class DotMachine:
    def __init__(self, program, inputs, weights, samples, input_stride, output_stride, shift):
        if not -62 <= shift <= 62 or min(input_stride, output_stride, samples) < 0:
            raise ValueError("outside verifier's supported call domain")
        self.program = program
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs["sp"] = 0x30001000
        self.memory = {}
        self.carry = 0
        self.pc, self.steps = program.start, 0
        self.samples, self.output_stride = samples, output_stride
        self.output = 0x31000000
        input_address, weight_address = 0x32000000, 0x33000000
        for index, value in enumerate(inputs):
            self.write(input_address + index * 4, value, 4)
        width = program.weight_bits // 8
        for index, value in enumerate(weights):
            self.write(weight_address + index * width, value, width)
        for index in range(max(1, samples * output_stride)):
            self.write(self.output + index * 4, 0x5A5A5A5A, 4)
        self.regs.update(r0=self.output, r1=output_stride, r2=input_address, r3=input_stride)
        for i, value in enumerate((weight_address, len(weights), samples, shift)):
            self.write(self.regs["sp"] + 4 * i, value, 4)

    def read(self, address, size):
        try:
            return int.from_bytes(bytes(self.memory[address + i] for i in range(size)), "little")
        except KeyError as error:
            raise ValueError(f"uninitialized emulated memory {address:#x}") from error

    def write(self, address, value, size):
        for i, byte in enumerate((value & ((1 << (8 * size)) - 1)).to_bytes(size, "little")):
            self.memory[address + i] = byte

    def value(self, token):
        return self.regs[token] if token in self.regs else int(token, 0) & MASK32

    def set(self, register, value):
        self.regs[register] = value & MASK32

    def pair(self, token):
        high, low = token.split("_")
        return (self.regs[high] << 32) | self.regs[low]

    def set_pair(self, token, value):
        high, low = token.split("_")
        self.set(high, value >> 32)
        self.set(low, value)

    def address(self, expression):
        match = re.fullmatch(r"(r\d+)\+\+=(\d+)", expression)
        if match:
            before = self.value(match[1])
            self.set(match[1], before + int(match[2]))
            return before
        match = re.fullmatch(r"(r\d+|sp)\+(r\d+)<<(\d+)", expression)
        if match:
            return (self.value(match[1]) + (self.value(match[2]) << int(match[3]))) & MASK32
        match = re.fullmatch(r"(r\d+|sp)(?:\+(-?\d+))?", expression)
        if match:
            return (self.value(match[1]) + int(match[2] or 0)) & MASK32
        raise ValueError("unsupported memory address: " + expression)

    def binary(self, a, operator, b, carry=0):
        if operator == "+":
            result = a + b + carry
            self.carry = int(result > MASK32)
        elif operator == "-":
            result = a - b - carry
            self.carry = int(a >= b + carry)
        elif operator == "*":
            result = a * b
        elif operator == "|":
            result = a | b
        elif operator == "<<":
            result = a << (b & 31)
        elif operator == ">>":
            result = a >> (b & 31)
        elif operator == ">>>":
            result = signed(a) >> (b & 31)
        else:
            raise ValueError("unsupported operation: " + operator)
        return result & MASK32

    def skip(self, pc, count):
        for _ in range(count):
            pc += self.program.code[pc][1]
        return pc

    def step(self):
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if text == "[--sp] = {rets, r15-r4}":
            # Only this prologue is accepted. Saved registers are never read by
            # the helper; stack arguments retain their measured ABI addresses.
            self.set("sp", self.value("sp") - 52)
        elif text == "{pc, r15-r4} = [sp++]":
            return False
        elif match := re.fullmatch(r"goto (-?\d+)", text):
            next_pc += int(match[1])
        elif match := re.fullmatch(r"(if|ifs) \((--)?(r\d+) (==|!=|<=|>=|<|>) (r\d+|-?\d+)\) (?:goto (-?\d+)|(\{))", text):
            if match[2]:
                self.set(match[3], self.value(match[3]) - 1)
            a, b = self.value(match[3]), self.value(match[5])
            if match[1] == "ifs":
                a, b = signed(a), signed(b)
            condition = {"==": a == b, "!=": a != b, "<=": a <= b,
                         ">=": a >= b, "<": a < b, ">": a > b}[match[4]]
            if match[6]:
                if condition:
                    next_pc += int(match[6])
            else:
                if otherwise:
                    raise ValueError("else blocks are outside these two helpers")
                if not condition:
                    next_pc = self.skip(next_pc, then)
        elif match := re.fullmatch(r"\[(.+)\] = (r\d+)", text):
            self.write(self.address(match[1]), self.value(match[2]), 4)
        elif match := re.fullmatch(r"(r\d+) = (h)?\[(.+)\](?: \((s|u)\))?", text):
            width = 2 if match[2] else 4
            value = self.read(self.address(match[3]), width)
            if match[4] == "s":
                value = signed(value, width * 8)
            self.set(match[1], value)
        elif match := re.fullmatch(r"(r\d+_r\d+) \+= (r\d+) \* (r\d+) \(s\)", text):
            self.set_pair(match[1], self.pair(match[1]) + signed(self.value(match[2])) * signed(self.value(match[3])))
        elif match := re.fullmatch(r"(r\d+_r\d+) (<<=|>>>=) (r\d+)", text):
            value, amount = self.pair(match[1]), self.value(match[3]) & 63
            value = value << amount if match[2] == "<<=" else signed(value, 64) >> amount
            self.set_pair(match[1], value & MASK64)
        elif match := re.fullmatch(r"(r\d+|sp) (\+=|\*=|<<=) (r\d+|-?\d+)", text):
            self.set(match[1], self.binary(self.value(match[1]), match[2][:-1], self.value(match[3])))
        elif match := re.fullmatch(r"(r\d+) = (r\d+|0x[0-9A-Fa-f]+|-?\d+)(?: (>>>|>>|<<|\+|-|\*|\|) (r\d+|-?\d+)(?: (\+ c|- !c))?)?", text):
            value = self.value(match[2])
            if match[3]:
                carry = self.carry if match[5] == "+ c" else 1 - self.carry if match[5] == "- !c" else 0
                value = self.binary(value, match[3], self.value(match[4]), carry)
            self.set(match[1], value)
        else:
            raise ValueError(f"unimplemented instruction at {self.pc:#x}: {text}")
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 1_000_000:
            self.steps += 1
            if not self.step():
                return [signed(self.read(self.output + i * self.output_stride * 4, 4)) for i in range(self.samples)]
        raise ValueError("instruction budget exceeded")
