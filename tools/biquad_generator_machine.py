"""Execute the complete bounded coefficient producer and its original math helpers.

All mathematical calls execute decoded original instructions. The previous
scripted 0x02028734 boundary is replaced by an internal call in this new module;
the earlier verifier and report remain unchanged.
"""
from __future__ import annotations

import re

from biquad_coefficients_machine import (BiquadCoefficientsProgram, BiquadCoefficientsMachine,
    REGIONS as PRIOR_REGIONS, MAPPED as PRIOR_MAPPED, ROOT, FLOAT, BRANCH, PRODUCER,
    STAGED, STACK, MASK32, DotMachine)
from pi32v2isa import codec, table

REGIONS = {
    "scaled_exp": (0x01C0516E, 0x01C05182),
    "exp": (0x020285D4, 0x02028646),
    "cosine": (0x02028646, 0x02028676),
    "sine": (0x02028676, 0x020286A0),
    "square_root": (0x0202870A, 0x02028734),
    "generate": PRODUCER,
}
DIVISOR = 0x01C1F7F8
MAPPED = (*PRIOR_MAPPED, (DIVISOR, 4))


def region_bytes(app, start, end):
    offset = start - 0x02000120 if start >= 0x02000120 else 0x02056780 - 0x02000120 + start - 0x01C00000
    return app[offset:offset + end - start]


class BiquadGeneratorProgram(BiquadCoefficientsProgram):
    def __init__(self):
        super().__init__()
        self.prior_code = set(self.code)
        self.math_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            raw = region_bytes(app, start, end)
            self.math_regions[name] = raw
            cursor = 0
            while cursor < len(raw):
                decoded = codec.decode(instructions, raw, cursor)
                if decoded is None:
                    raise ValueError("unsupported coefficient-generator instruction")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if start + cursor + size > end:
                    raise ValueError("generator instruction crosses a function boundary")
                self.code[start + cursor] = codec.format(instruction, fields), size, *counts
                cursor += size
        for pc in set(self.code) - self.prior_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, second_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ = ", text) or second_size != 2 or "[" not in following:
                    raise ValueError("unreviewed generator parallel packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, section=0, value=0, request=None):
        if (operation not in (*REGIONS, "setup", "stage")
                or tuple(map(len, memory)) != tuple(size for _, size in MAPPED)
                or not 0 <= section <= MASK32 or not 0 <= value <= MASK32
                or (operation in ("setup", "generate") and section >= 5)
                or (operation == "exp" and (value & 0x7FFFFFFF) > 0x41800000)
                or (operation == "scaled_exp" and (value & 0x7FFFFFFF) > 0x43000000)
                or (operation == "generate" and (request is None or len(request) != 4
                    or any(not 0 <= word <= MASK32 for word in request)
                    or (request[2] & 0x7FFFFFFF) > 0x43000000))):
            raise ValueError("outside the bounded coefficient-generator verifier domain")
        return BiquadGeneratorMachine(self, memory, operation, section, value, request).run()


class BiquadGeneratorMachine(BiquadCoefficientsMachine):
    def __init__(self, program, memory, operation, section, value, request):
        prior = operation if operation in ("setup", "stage") else "q28"
        super().__init__(program, memory[:len(PRIOR_MAPPED)], prior, section, value, None, None)
        for i, byte in enumerate(memory[-1]):
            self.memory[DIVISOR+i] = byte
        if operation in REGIONS:
            self.pc = REGIONS[operation][0]
        self.math_calls, self.production_calls, self.normalization_calls = [], [], []
        if operation == "generate":
            self.regs.update(r0=STAGED+44*section, r1=request[0], r2=request[1], r3=request[2])
            DotMachine.write(self, STACK, request[3], 4)
            self.production_calls.append((section, tuple(request), self.snapshot()))

    def snapshot(self):
        return super().snapshot() + (bytes(self.memory[DIVISOR+i] for i in range(4)),)

    def single_step(self):
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            for name, (start, _) in REGIONS.items():
                if target == start:
                    self.math_calls.append((name, self.value("r0")))
            if target == PRODUCER[0]:
                section, offset = divmod(self.value("r0") - STAGED, 44)
                if offset or not 0 <= section < 5:
                    raise ValueError("unexpected generator destination")
                request = (self.value("r1"), self.value("r2"), self.value("r3"), self.read(self.value("sp"), 4))
                self.production_calls.append((section, request, self.snapshot()))
                self.visited.add(self.pc)
                self.returns.append(next_pc)
                self.pc = target
                return True
            if target == PRIOR_REGIONS["normalize"][0]:
                words = (self.value("r1"), self.value("r2"), self.value("r3"),
                         *(self.read(self.value("sp")+4*i, 4) for i in range(5)))
                self.normalization_calls.append((self.value("r0"), words))
        if match := re.fullmatch(r"iff \((r\d+) (u?<=|u?>=|u?<|u?>|==|!=) (r\d+)\) (?:goto (-?\d+)|(\{))", text):
            self.visited.add(self.pc)
            relation = {"<": "lt", ">": "gt", "<=": "le", ">=": "ge", "==": "eq", "!=": "ne"}[match[2].removeprefix("u")]
            if match[2].startswith("u"):
                relation = "u" + relation
            condition = bool(BRANCH.compare(relation, floating=True)(
                {0: self.value(match[1]), 1: self.value(match[3])}, 0, {"r": 0, "s": 1}, None)["exit"])
            if match[4]:
                if condition:
                    next_pc += int(match[4])
            else:
                else_start = self.skip(next_pc, then)
                if not condition:
                    next_pc = else_start
                elif otherwise:
                    self.else_skips[else_start] = self.skip(else_start, otherwise)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) - (r\d+) \(f\)", text):
            self.visited.add(self.pc)
            self.set(match[1], FLOAT.arithmetic(self.value(match[2]), self.value(match[3]), "sub"))
        elif match := re.fullmatch(r"(r\d+) = fmax\((r\d+), (r\d+)\)", text):
            self.visited.add(self.pc)
            result, _ = FLOAT.minmax(True)({0: self.value(match[2]), 1: self.value(match[3])}, 0, {"r": 2, "s": 0, "t": 1})
            self.set(match[1], result[2])
        elif match := re.fullmatch(r"(r\d+) = (r\d+) \^ (0x[0-9A-Fa-f]+)", text):
            self.visited.add(self.pc)
            self.set(match[1], self.value(match[2]) ^ int(match[3], 16))
        elif text == "[--sp] = rets":
            self.visited.add(self.pc)
            self.frames.append(({}, self.value("sp")))
            self.set("sp", self.value("sp")-4)
        elif text == "pc = [sp++]":
            self.visited.add(self.pc)
            saved, sp = self.frames.pop()
            if saved or self.value("sp") != sp-4:
                raise ValueError("unbalanced scaled-exponential frame")
            self.set("sp", sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        result = super().run()
        result.update(value=result["value"] & MASK32, math_calls=self.math_calls,
                      production_calls=self.production_calls, normalization_calls=self.normalization_calls)
        if result["calls"]:
            raise ValueError("a scripted mathematical boundary was unexpectedly reached")
        return result
