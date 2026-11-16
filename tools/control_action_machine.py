"""Bounded execution of original controls, timers and action selection instructions.

Leaf services are explicit scripted boundaries. This is not a CPU/peripheral
emulator or a claim that the downstream preset/effect handlers have executed.
"""
from __future__ import annotations

import re

from control_machine import (ControlMachine, ControlsProgram, ROOT, GLOBAL, STATE,
                             OWNER, TRANSITION, EMIT)
from dot_machine import signed
from pi32v2isa import codec, table

TICK = 0x02014B3C
CLOCK = 0x0200C996
GLOBAL_BYTES = 272
TABLE_START, TABLE_END = 0x02014A7C, 0x02014A86
REGIONS = {"action": (EMIT, TICK), "tick": (TICK, TRANSITION),
           "clock": (CLOCK, 0x0200C9A4)}

# Number of semantic arguments, excluding incidental caller-saved registers.
SERVICES = {
    0x02002D10: ("notify", 3), 0x020148BA: ("flush_pending", 0),
    0x02014366: ("scene", 1), 0x0200CF88: ("preset_exists", 1),
    0x0200CA7E: ("preset_load", 1), 0x02014952: ("preset_step", 1),
    0x0200A4B2: ("tap", 2), 0x0201499C: ("effect_resolve", 1),
    0x020308EA: ("effect_get", 1), 0x0200D060: ("effect_set", 2),
    0x0200733E: ("mode_get", 0), 0x02008CA2: ("mode_set", 1),
    0x020146AE: ("disabled_tick", 1),
}


class ControlActionProgram:
    def __init__(self):
        # The previous loader verifies both the pinned original and extraction.
        self.controls = ControlsProgram()
        self.code = dict(self.controls.code)
        self.raw_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.raw_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                if pc == TABLE_START:
                    pc = TABLE_END
                    continue
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported encoding at {pc:#x}")
                instruction, fields, size = decoded
                text = codec.format(instruction, fields)
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a function boundary")
                self.code[pc] = text, size, *counts
                pc += size
        self.table = app[TABLE_START - 0x02000120:TABLE_END - 0x02000120]
        if any(TABLE_START + 2 * value not in self.code for value in self.table):
            raise ValueError("table branch does not target a decoded instruction")
        self.parallel_seconds = set()
        for pc, (text, size, _, _) in self.code.items():
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if (not re.match(r"r\d+ (?:=|\|=|\+=)", text)
                        or b_size != 2 or "[" not in following):
                    raise ValueError("unreviewed parallel packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, globals_, state, owner, operation, *arguments, boundary=None):
        arities = {"action": 2, "tick": 1, "edge": 4}
        if (len(globals_) != GLOBAL_BYTES or len(state) != 1860 or not 0 <= owner <= 255
                or operation not in arities or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the action verifier's call domain")
        if operation == "action" and (arguments[0] >= 4 or arguments[1] >= 3):
            raise ValueError("outside the action verifier's call domain")
        if operation == "edge" and (arguments[0] >= 5 or arguments[1] > 1):
            raise ValueError("outside the action verifier's call domain")
        return ControlActionMachine(self, globals_, state, owner, operation,
                                    arguments, boundary).run()


class ControlActionMachine(ControlMachine):
    def __init__(self, program, globals_, state, owner, operation, arguments, boundary):
        args = list(arguments) + [0] * (4 - len(arguments))
        super().__init__(program, globals_[:270], state, owner, *args, immediate=False)
        self.memory.update({GLOBAL + i: globals_[i] for i in range(270, GLOBAL_BYTES)})
        self.pc = {"action": EMIT, "tick": TICK, "edge": TRANSITION}[operation]
        self.boundary = boundary
        self.else_skips = {}

    def snapshot(self):
        return (bytes(self.memory[GLOBAL + i] for i in range(GLOBAL_BYTES)),
                bytes(self.memory[STATE + i] for i in range(1860)), self.memory[OWNER])

    def address(self, expression):
        if match := re.fullmatch(r"\+\+(r\d+)=(-?\d+)", expression):
            self.set(match[1], self.value(match[1]) + int(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def skip(self, pc, count):
        # Predication counts packets, not individual lines of a parallel pair.
        for _ in range(count):
            text, size, _, _ = self.program.code[pc]
            pc += size
            if text.endswith("  #"):
                pc += self.program.code[pc][1]
        return pc

    def step(self):
        if self.pc in self.else_skips:
            self.pc = self.else_skips.pop(self.pc)
        if self.pc in self.program.parallel_seconds:
            raise ValueError("branch entered the second half of a parallel packet")
        if self.pc not in self.program.code:
            raise ValueError("execution escaped decoded instructions")
        text, size, _, _ = self.program.code[self.pc]
        if not text.endswith("  #"):
            return self.single_step()
        # Both halves read pre-packet registers. Commit B, then A's destination;
        # A wins a shared register destination. These packets have ALU-only A.
        pc, before = self.pc, dict(self.regs)
        destination = re.match(r"(r\d+) ", text)[1]
        self.pc = pc + size
        if not self.single_step():
            raise ValueError("parallel B unexpectedly returned")
        after_b, end = dict(self.regs), self.pc
        self.regs, self.pc = dict(before), pc
        if not self.single_step():
            raise ValueError("parallel A unexpectedly returned")
        after_b[destination] = self.regs[destination]
        self.regs, self.pc = after_b, end
        return True

    def single_step(self):
        self.visited.add(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"\[--sp\] = \{rets, r(\d+)-r4\}", text):
            saved = {f"r{i}": self.value(f"r{i}") for i in range(4, int(match[1]) + 1)}
            self.frames.append((saved, self.value("sp")))
            self.set("sp", self.value("sp") - 4 * (len(saved) + 1))
        elif re.fullmatch(r"\{pc, r\d+-r4\} = \[sp\+\+\]", text):
            saved, sp = self.frames.pop()
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
            if target in self.program.code:
                self.returns.append(next_pc)
                next_pc = target
            elif target in SERVICES:
                count = SERVICES[target][1]
                args = tuple(self.value(f"r{i}") if i < count else 0 for i in range(3))
                if target == 0x0201499C:
                    args = (args[0] - GLOBAL, 0, 0)
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else 0
                for register in ("r0", "r1", "r2", "r3"):
                    self.set(register, 0xBAD0C0DE)
                self.set("r0", result)
            else:
                raise ValueError(f"unreviewed external call {target:#x}")
        elif match := re.fullmatch(r"(if|ifs) \((r\d+) (==|!=|<=|>=|<|>) (r\d+|-?\d+)\) \{", text):
            a, b = self.value(match[2]), self.value(match[4])
            if match[1] == "ifs":
                a, b = signed(a), signed(b)
            condition = {"==": a == b, "!=": a != b, "<=": a <= b,
                         ">=": a >= b, "<": a < b, ">": a > b}[match[3]]
            else_start = self.skip(next_pc, then)
            if not condition:
                next_pc = else_start
            elif otherwise:
                self.else_skips[else_start] = self.skip(else_start, otherwise)
        elif match := re.fullmatch(r"tbb \[(r\d+)\]", text):
            index = self.value(match[1])
            if self.pc != TABLE_START - 2 or index >= len(self.program.table):
                raise ValueError("table index outside the reviewed table")
            next_pc = TABLE_START + 2 * self.program.table[index]
        elif match := re.fullmatch(r"\[(.+)\] \+= (-?\d+)", text):
            address = self.address(match[1])
            self.write(address, self.read(address, 4) + int(match[2]), 4)
        elif match := re.fullmatch(r"(r\d+_r\d+) = d\[(.+)\]", text):
            self.set_pair(match[1], self.read(self.address(match[2]), 8))
        elif match := re.fullmatch(r"(r\d+) \|= (r\d+)", text):
            self.set(match[1], self.value(match[1]) | self.value(match[2]))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) \| (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.value(match[2]) | int(match[3], 16))
        else:
            return super().step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 5000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced control action execution")
                return {"memory": self.snapshot(), "calls": self.calls, "writes": self.writes,
                        "visited": self.visited, "steps": self.steps}
        raise ValueError("control action instruction budget exceeded")
