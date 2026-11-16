"""Execute the complete original native capture parser and its read64 helper."""
from __future__ import annotations
import re
import struct

from capture_dispatch_machine import CaptureDispatchProgram, CaptureDispatchMachine, ROOT, image_offset
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

REGIONS = {"parse": (0x02031C64, 0x0203291C), "read64": (0x01C127DE, 0x01C12850)}
CONTEXT, LEDGER, SOURCE, ARENA, CONFIG = 0x01C2C03C, 0x31007000, 0x34000000, 0x35000000, 0x01C1FA18


class CaptureParserProgram(CaptureDispatchProgram):
    def __init__(self):
        super().__init__()
        self.pre_parser_code, self.parser_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.parser_regions[name] = app[image_offset(start):image_offset(end)]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, image_offset(pc))
                if decoded is None:
                    raise ValueError(f"unsupported parser instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a parser function boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_parser_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+(?:_r\d+)? (?:=|<=|\+=|\*=)", text) or b_size != 2 or "[" not in following:
                    raise ValueError(f"unreviewed parser instruction packet at {pc:#x}")
                self.parallel_seconds.add(pc + size)
        # Cache instruction classification, not results or loops. Every original
        # instruction still executes and contributes to the execution trace.
        patterns = (
            ("load", r"(r\d+) = (b|h)?\[(.+)\](?: \((u|s)\))?"),
            ("store", r"(b|h)?\[(.+)\] = (r\d+|0x[0-9a-fA-F]+)"),
            ("unary", r"(r\d+) = ~(r\d+)"),
            ("binary", r"(r\d+) = (r\d+|0x[0-9a-fA-F]+|-?\d+)(?: (>>>|>>|<<|\+|-|\*|\||&|\^) (r\d+|0x[0-9a-fA-F]+|-?\d+)(?: (\+ c|- !c))?)?"),
            ("compound", r"(r\d+) (\+=|\*=|&=|\^=|<<=|>>=) (r\d+|-?\d+)"),
            ("branch", r"(if|ifs) \((--)?(r\d+) (==|!=|<=|>=|<|>) (r\d+|-?\d+)\) goto (-?\d+)"),
            ("jump", r"goto (-?\d+)"),
            ("field", r"(r\d+) = (r\d+)\.(b0|l) \((u|s)\)"),
            ("insert", r"(r\d+) <= insert\((r\d+), p:(\d+), l:(\d+)\)"),
        )
        self.parser_ops = {}
        for pc in set(self.code) - self.pre_parser_code:
            text = self.code[pc][0].removesuffix("  #")
            for kind, pattern in patterns:
                if match := re.fullmatch(pattern, text):
                    self.parser_ops[pc] = kind, match.groups()
                    break

    def execute(self, context, ledger, source, arena, configuration=0xFFFFFFFF, *, arena_base=ARENA):
        if (len(context) != 228 or len(ledger) != 3 or len(source) > 0x100000 or len(arena) > 0x200000
                or any(not 0 <= x <= 0xFFFFFFFF for x in (*ledger, configuration, arena_base))
                or not ARENA <= arena_base <= arena_base + len(arena) <= ARENA + 0x1000000):
            raise ValueError("outside the parser verifier's mapped domain")
        return CaptureParserMachine(self, context, ledger, source, arena, configuration, arena_base).run()


class CaptureParserMachine(CaptureDispatchMachine):
    def __init__(self, program, context, ledger, source, arena, configuration, arena_base):
        self.program = program
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(sp=0x30001000, r0=CONTEXT, r1=LEDGER, r2=SOURCE, r3=len(source))
        self.memory = {}
        self.ranges = ((CONTEXT, len(context)), (LEDGER, 12), (SOURCE, len(source)),
                       (arena_base, len(arena)), (CONFIG, 4))
        for (base, _), data in zip(self.ranges, (context, struct.pack("<III", *ledger), source, arena, struct.pack("<I", configuration))):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.source_range = SOURCE, len(source)
        self.pc = REGIONS["parse"][0]
        self.carry = self.steps = 0
        self.calls, self.frames, self.returns, self.visited = [], [], [], set()
        self.writes, self.library_calls, self.else_skips = [], [], {}
        self.allocation_size = 0

    def snapshot(self):
        return tuple(bytes(self.memory[base + i] for i in range(size)) for base, size in self.ranges)

    def write(self, address, value, size):
        source, count = self.source_range
        if (address < source + count and address + size > source) or (address < CONFIG + 4 and address + size > CONFIG):
            raise ValueError("write to immutable parser input")
        return super().write(address, value, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if fast := self.program.parser_ops.get(self.pc):
            kind, g = fast
            if kind == "load":
                width = {"b": 1, "h": 2, None: 4}[g[1]]
                value = self.read(self.address(g[2]), width)
                self.set(g[0], signed(value, width * 8) if g[3] == "s" else value)
            elif kind == "store":
                self.write(self.address(g[1]), self.value(g[2]), {"b": 1, "h": 2, None: 4}[g[0]])
            elif kind == "unary":
                self.set(g[0], ~self.value(g[1]))
            elif kind == "binary":
                value = self.value(g[1])
                if g[2]:
                    other = self.value(g[3])
                    if g[2] in ("&", "^"):
                        value = value & other if g[2] == "&" else value ^ other
                    else:
                        carry = self.carry if g[4] == "+ c" else 1 - self.carry if g[4] == "- !c" else 0
                        value = self.binary(value, g[2], other, carry)
                self.set(g[0], value)
            elif kind == "compound":
                a, b, op = self.value(g[0]), self.value(g[2]), g[1][:-1]
                value = a & b if op == "&" else a ^ b if op == "^" else self.binary(a, op, b)
                self.set(g[0], value)
            elif kind == "branch":
                if g[1]:
                    self.set(g[2], self.value(g[2]) - 1)
                a, b = self.value(g[2]), self.value(g[4])
                if g[0] == "ifs":
                    a, b = signed(a), signed(b)
                if {"==": a == b, "!=": a != b, "<=": a <= b, ">=": a >= b, "<": a < b, ">": a > b}[g[3]]:
                    next_pc += int(g[5])
            elif kind == "jump":
                next_pc += int(g[0])
            elif kind == "field":
                bits = 8 if g[2] == "b0" else 16
                value = self.value(g[1]) & ((1 << bits) - 1)
                self.set(g[0], signed(value, bits) if g[3] == "s" else value)
            elif kind == "insert":
                position, length = int(g[2]), int(g[3])
                mask = (1 << length) - 1
                self.set(g[0], (self.value(g[0]) & ~(mask << position)) | ((self.value(g[1]) & mask) << position))
            else:
                raise AssertionError("unknown cached parser instruction")
        elif match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(u\)", text):
            denominator = self.value(match[3])
            if not denominator:
                raise ValueError("unexpected native parser division by zero")
            self.set(match[1], self.value(match[2]) // denominator)
        elif match := re.fullmatch(r"(r\d+) = sextra\((r\d+), p:0, l:8\)", text):
            self.set(match[1], signed(self.value(match[2]) & 255, 8))
        elif match := re.fullmatch(r"(r\d+_r\d+) (<<=|>>>=) (r\d+|\d+)", text):
            value, amount = self.pair(match[1]), self.value(match[3]) & 63
            self.set_pair(match[1], value << amount if match[2] == "<<=" else signed(value, 64) >> amount)
        elif match := re.fullmatch(r"if \(\((r\d+) & (0x[0-9A-Fa-f]+|\d+)\) == 0\) (?:goto (-?\d+)|(\{))", text):
            condition = not (self.value(match[1]) & int(match[2], 0))
            if match[3]:
                if condition:
                    next_pc += int(match[3])
            else:
                else_start = self.skip(next_pc, then)
                after_else = self.skip(else_start, otherwise)
                if condition and otherwise:
                    self.else_skips[else_start] = after_else
                elif not condition:
                    next_pc = else_start
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 50000000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced parser execution")
                return {"memory": self.snapshot(), "result": self.value("r0"), "visited": self.visited,
                        "steps": self.steps, "writes": self.writes}
        raise ValueError("parser instruction budget exceeded")
