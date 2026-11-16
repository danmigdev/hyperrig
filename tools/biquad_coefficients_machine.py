"""Execute original staging/normalization with an explicit mathematical boundary.

No device access. The 0x02028734 producer is supplied by a script and is never
reported as executed. Floating instructions use the pinned ISA's measured,
exact-rational semantics, independently of the reconstructed C integer code.
"""
from __future__ import annotations

import importlib.util
import re

from biquad_chain_machine import MAPPED as CHAIN_MAPPED, STAGED, PENDING, AVERAGE, STACK
from dot_machine import DotMachine, NativeProgram, ROOT, signed, MASK32
from pi32v2isa import codec, table

REGIONS = {
    "counter": (0x01C05160, 0x01C0516E),
    "q28": (0x01C05182, 0x01C051A2),
    "normalize": (0x020286A0, 0x0202870A),
    "setup": (0x02028892, 0x020288D6),
    "stage": (0x020288D6, 0x02028920),
}
PRODUCER = (0x02028734, 0x02028892)
REQUESTS, PARAMETERS, TABLE = 0x01C34468, 0x01C32E59, 0x0203A55C
MAPPED = (*CHAIN_MAPPED, (REQUESTS, 4), (PARAMETERS, 5))
ISA_SEMANTICS = ROOT / "upstream/pi32v2-isa/tools/hwtest/semantics"


def load_semantics(name):
    spec = importlib.util.spec_from_file_location("coefficient_isa_" + name, ISA_SEMANTICS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FLOAT, BRANCH = load_semantics("s"), load_semantics("b2")


class Region(NativeProgram):
    REGIONS = {name: bounds for name, bounds in REGIONS.items() if name != "stage"}


class BiquadCoefficientsProgram:
    def __init__(self):
        # NativeProgram validates original manifest and complete decoded image.
        self.regions = {name: Region(name).raw for name in Region.REGIONS}
        self.code = {}
        self.parallel_seconds = set()
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.regions["stage"] = app[REGIONS["stage"][0] - 0x02000120:REGIONS["stage"][1] - 0x02000120]
        self.table = app[TABLE - 0x02000120:TABLE - 0x02000120 + 10]
        self.producer = app[PRODUCER[0] - 0x02000120:PRODUCER[1] - 0x02000120]
        instructions = table.load()
        for name, raw in self.regions.items():
            start, end = REGIONS[name]
            cursor = 0
            while cursor < len(raw):
                decoded = codec.decode(instructions, raw, cursor)
                if decoded is None:
                    raise ValueError("unsupported coefficient instruction")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if start + cursor + size > end:
                    raise ValueError("coefficient instruction crosses a function boundary")
                self.code[start + cursor] = codec.format(instruction, fields), size, *counts
                cursor += size
        for pc, (text, size, _, _) in self.code.items():
            if text.endswith("  #"):
                following, second_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ = ", text) or second_size != 2 or "[" not in following:
                    raise ValueError("unreviewed coefficient parallel packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, section=0, value=0, input_words=None, producer=None):
        if (operation not in ("q28", "normalize", "setup", "stage")
                or tuple(map(len, memory)) != tuple(size for _, size in MAPPED)
                or not 0 <= section <= MASK32 or not 0 <= value <= MASK32
                or (operation in ("normalize", "setup") and section >= 5)
                or (operation == "normalize" and (input_words is None or len(input_words) != 8
                    or any(not 0 <= word <= MASK32 for word in input_words)))
                or (operation in ("setup", "stage") and section < 5 and producer is None)):
            raise ValueError("outside the coefficient verifier domain")
        return BiquadCoefficientsMachine(self, memory, operation, section, value, input_words, producer).run()


class BiquadCoefficientsMachine(DotMachine):
    def __init__(self, program, memory, operation, section, value, input_words, producer):
        self.program, self.producer = program, producer
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs["sp"] = STACK
        self.memory = {base + i: byte for (base, _), data in zip(MAPPED, memory) for i, byte in enumerate(data)}
        self.memory.update({TABLE + i: byte for i, byte in enumerate(program.table)})
        self.pc, self.steps, self.carry = REGIONS[operation][0], 0, 0
        self.frames, self.returns, self.calls = [], [], []
        self.visited, self.else_skips, self.written = set(), {}, set()
        self.stack_argument_bytes = 20 if operation == "normalize" else 0
        if operation == "q28":
            self.regs["r0"] = value
        elif operation == "normalize":
            self.regs.update(r0=STAGED + 44*section, r1=input_words[0], r2=input_words[1], r3=input_words[2])
            for i, word in enumerate(input_words[3:]):
                DotMachine.write(self, STACK + 4*i, word, 4)
        elif operation == "setup":
            self.regs.update(r0=section, r1=STAGED + 44*section)
        else:
            self.regs.update(r0=section, r1=value)

    def snapshot(self):
        return tuple(bytes(self.memory[base + i] for i in range(size)) for base, size in MAPPED)

    def normalize_script(self, section, input_words):
        """A scripted producer can call the original normalizer, not a C formula."""
        result = self.program.execute(self.snapshot(), "normalize", section=section, input_words=input_words)
        for (base, _), data in zip(MAPPED, result["memory"]):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.visited.update(result["visited"])
        self.steps += result["steps"]

    def set(self, register, value):
        self.written.add(register)
        super().set(register, value)

    def read(self, address, size):
        if 0x30000000 <= address < STACK and not self.value("sp") <= address <= address + size <= STACK:
            raise ValueError("read from released coefficient stack")
        return super().read(address, size)

    def write(self, address, value, size):
        if 0x30000000 <= address < STACK:
            if not self.value("sp") <= address <= address + size <= STACK:
                raise ValueError("coefficient stack write escaped its frame")
        elif not any(base <= address and address + size <= base + length for base, length in
                     ((STAGED, 220), (PENDING, 5), (AVERAGE, 4), (REQUESTS, 4), (PARAMETERS, 5))):
            raise ValueError("instruction wrote outside coefficient state")
        return super().write(address, value, size)

    def address(self, expression):
        if match := re.fullmatch(r"\+\+(r\d+)=(\d+)", expression):
            self.set(match[1], self.value(match[1]) + int(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def skip(self, pc, count):
        for _ in range(count):
            text, size, _, _ = self.program.code[pc]
            pc += size
            if text.endswith("  #"):
                pc += self.program.code[pc][1]
        return pc

    def single_step(self):
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"\[--sp\] = \{rets, r(\d+)(?:-r4)?\}", text):
            saved = {f"r{i}": self.value(f"r{i}") for i in range(4, int(match[1])+1)}
            self.frames.append((saved, self.value("sp")))
            self.set("sp", self.value("sp") - 4*(len(saved)+1))
        elif re.fullmatch(r"\{pc, r\d+(?:-r4)?\} = \[sp\+\+\]", text):
            saved, sp = self.frames.pop()
            if self.value("sp") != sp - 4*(len(saved)+1):
                raise ValueError("unbalanced coefficient frame")
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif text == "rts":
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target == PRODUCER[0]:
                destination = self.value("r0")
                section, offset = divmod(destination - STAGED, 44)
                if offset or not 0 <= section < 5 or self.producer is None:
                    raise ValueError("unreviewed mathematical producer ABI")
                request = (self.value("r1"), self.value("r2"), self.value("r3"), self.read(self.value("sp"), 4))
                before = self.snapshot()
                self.calls.append((section, request, before))
                self.producer(section, request, self)
                after = self.snapshot()
                changed = {STAGED + 44*section + i for i in (*range(20), 40, 41)}
                for (base, _), a, b in zip(MAPPED, before, after):
                    if any(x != y and base + i not in changed for i, (x, y) in enumerate(zip(a, b))):
                        raise ValueError("scripted producer changed storage outside its boundary")
                for register in ("r0", "r1", "r2", "r3"):
                    self.set(register, 0xBAD0C0DE)
            elif target in self.program.code:
                self.returns.append(next_pc)
                next_pc = target
            else:
                raise ValueError("unreviewed coefficient direct call")
        elif match := re.fullmatch(r"(if|ifs|iff) \((r\d+) (u<|==|!=|<=|>=|<|>) (r\d+|-?\d+)\) (?:goto (-?\d+)|(\{))", text):
            a, b = self.value(match[2]), self.value(match[4])
            if match[1] == "iff":
                relation = {"u<": "ult", "==": "eq", "!=": "ne", "<": "lt", ">": "gt", "<=": "le", ">=": "ge"}[match[3]]
                condition = bool(BRANCH.compare(relation, floating=True)({0: a, 1: b}, 0, {"r": 0, "s": 1}, None)["exit"])
            else:
                if match[1] == "ifs":
                    a, b = signed(a), signed(b)
                condition = {"==": a == b, "!=": a != b, "<=": a <= b, ">=": a >= b, "<": a < b, ">": a > b}[match[3]]
            if match[5]:
                if condition:
                    next_pc += int(match[5])
            else:
                else_start = self.skip(next_pc, then)
                if not condition:
                    next_pc = else_start
                elif otherwise:
                    self.else_skips[else_start] = self.skip(else_start, otherwise)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) ([+*/]) (r\d+) \(f\)", text):
            operation = {"+": "add", "*": "mul", "/": "div"}[match[3]]
            self.set(match[1], FLOAT.arithmetic(self.value(match[2]), self.value(match[4]), operation))
        elif match := re.fullmatch(r"(r\d+) = (ftoi|utof|itof)\((r\d+)\)(?: \((trunc)\))?", text):
            result, _ = FLOAT.convert(match[2], match[4] or "even")({0: self.value(match[3])}, 0, {"s": 0, "r": 1})
            self.set(match[1], result[1])
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \((u|s)\)", text):
            value = self.read(self.address(match[2]), 1)
            self.set(match[1], signed(value, 8) if match[3] == "s" else value)
        elif match := re.fullmatch(r"b\[(.+)\] = (r\d+)", text):
            self.write(self.address(match[1]), self.value(match[2]), 1)
        elif match := re.fullmatch(r"(r\d+_r\d+) = (r\d+_r\d+)", text):
            self.set_pair(match[1], self.pair(match[2]))
        elif match := re.fullmatch(r"(r\d+) \^= (\d+)", text):
            self.set(match[1], self.value(match[1]) ^ int(match[2]))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) ([+*]) (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.binary(self.value(match[2]), match[3], int(match[4], 16)))
        elif match := re.fullmatch(r"sp \+= (-?\d+)", text):
            after = self.value("sp") + int(match[1])
            if not 0x30000000 <= after <= STACK:
                raise ValueError("coefficient stack pointer escaped its arena")
            if after < self.value("sp"):
                for address in range(after, self.value("sp")):
                    self.memory.pop(address, None)
            self.set("sp", after)
        else:
            return super().step()
        self.pc = next_pc
        return True

    def step(self):
        if self.pc in self.else_skips:
            self.pc = self.else_skips.pop(self.pc)
        if self.pc not in self.program.code or self.pc in self.program.parallel_seconds:
            raise ValueError("coefficient execution escaped an instruction packet")
        parallel = self.program.code[self.pc][0].endswith("  #")
        if not parallel:
            return self.single_step()
        before, carry = dict(self.regs), self.carry
        self.written = set()
        if not self.single_step():
            raise ValueError("control transfer in parallel A")
        writes_a = {key: self.regs[key] for key in self.written}
        after_carry = self.carry
        self.regs, self.carry, self.written = before, carry, set()
        if not self.single_step():
            raise ValueError("control transfer in parallel B")
        self.regs.update(writes_a)
        self.carry = after_carry
        return True

    def run(self):
        while self.steps < 10000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != STACK:
                    raise ValueError("unbalanced coefficient execution")
                return {"memory": self.snapshot(), "value": signed(self.value("r0")),
                        "calls": self.calls, "visited": self.visited, "steps": self.steps}
        raise ValueError("coefficient instruction budget exceeded")
