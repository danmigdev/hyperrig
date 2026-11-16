"""Run two original control routines with bounded RAM and an action-call recorder.

No peripherals or transports. The action executor is an explicit boundary:
record its arguments and state, do not claim execution of its side effects.
The existing restricted interpreter supplies arithmetic/conditional semantics.
"""
from __future__ import annotations

import re
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from dot_machine import DotMachine, NativeProgram

GLOBAL = 0x01C1F180
STATE = 0x01C26890
OWNER = 0x01C26864
GLOBAL_BYTES = 270
STATE_BYTES = 1860
TRANSITION = 0x02014C04
IMMEDIATE = 0x0200C9C2
EMIT = 0x020149B6


class ControlProgram(NativeProgram):
    REGIONS = {"transition": (TRANSITION, 0x02014D44), "immediate": (IMMEDIATE, 0x0200C9F4)}


class ControlsProgram:
    def __init__(self):
        original = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
        if hashlib.sha256(original.read_bytes()).hexdigest() != "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059":
            raise ValueError("control reference is not the reviewed G v2 M5.71 image")
        self.transition = ControlProgram("transition")
        self.immediate = ControlProgram("immediate")
        self.code = self.transition.code | self.immediate.code
        self.start = TRANSITION

    def execute(self, globals_, state, owner, physical, pressed, stamp_a=0, stamp_b=0,
                *, immediate=False):
        if (len(globals_) != GLOBAL_BYTES or len(state) != STATE_BYTES
                or not 0 <= owner <= 255 or not 0 <= physical < (4 if immediate else 5)
                or pressed not in (0, 1)):
            raise ValueError("outside the control verifier's call domain")
        machine = ControlMachine(self, globals_, state, owner, physical, pressed,
                                 stamp_a, stamp_b, immediate=immediate)
        return machine.run()


class ControlMachine(DotMachine):
    def __init__(self, program, globals_, state, owner, physical, pressed, a, b, *, immediate):
        self.program = program
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(sp=0x30001000, r0=physical, r1=pressed,
                         r2=a & 0xFFFFFFFF, r3=b & 0xFFFFFFFF)
        self.memory = {GLOBAL + i: value for i, value in enumerate(globals_)}
        self.memory.update({STATE + i: value for i, value in enumerate(state)})
        self.memory[OWNER] = owner
        self.pc = IMMEDIATE if immediate else TRANSITION
        self.carry = self.steps = 0
        self.calls, self.frames, self.returns, self.visited = [], [], [], set()
        self.writes = []

    def write(self, address, value, size):
        if any(address + i not in self.memory for i in range(size)):
            raise ValueError("control write escaped initialized RAM")
        self.writes.append((address, value & ((1 << (8 * size)) - 1), size))
        super().write(address, value, size)

    def snapshot(self):
        return (bytes(self.memory[GLOBAL + i] for i in range(GLOBAL_BYTES)),
                bytes(self.memory[STATE + i] for i in range(STATE_BYTES)), self.memory[OWNER])

    def address(self, expression):
        match = re.fullmatch(r"(r\d+)\+(r\d+)", expression)
        if match:
            return (self.value(match[1]) + self.value(match[2])) & 0xFFFFFFFF
        return super().address(expression)

    def step(self):
        if self.pc not in self.program.code:
            raise ValueError("control execution escaped decoded function boundaries")
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if text in ("[--sp] = {rets, r9-r4}", "[--sp] = {rets, r4}"):
            last = 9 if "r9-r4" in text else 4
            saved = {f"r{i}": self.value(f"r{i}") for i in range(4, last + 1)}
            self.frames.append((saved, self.value("sp")))
            self.set("sp", self.value("sp") - 4 * (len(saved) + 1))
        elif text in ("{pc, r9-r4} = [sp++]", "{pc, r4} = [sp++]"):
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target == IMMEDIATE:
                self.returns.append(next_pc)
                next_pc = target
            elif target == EMIT:
                self.calls.append((self.value("r0"), self.value("r1"), self.snapshot()))
                # No instruction after this boundary reads caller-saved values.
                for register in ("r0", "r1", "r2", "r3"):
                    self.set(register, 0xBAD0C0DE)
            else:
                raise ValueError("unreviewed external control call")
        elif match := re.fullmatch(r"(r\d+) = (r\d+)\.b0 \(u\)", text):
            self.set(match[1], self.value(match[2]) & 255)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) \* (0x[0-9A-Fa-f]+)", text):
            self.set(match[1], self.value(match[2]) * int(match[3], 16))
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \(u\)", text):
            self.set(match[1], self.read(self.address(match[2]), 1))
        elif match := re.fullmatch(r"(b|h)\[(.+)\] = (r\d+)", text):
            self.write(self.address(match[2]), self.value(match[3]), 1 if match[1] == "b" else 2)
        elif match := re.fullmatch(r"if \(\((r\d+) & (r\d+)\) == 0\) \{", text):
            if self.value(match[1]) & self.value(match[2]):
                then, otherwise = self.program.code[self.pc][2:]
                if otherwise:
                    raise ValueError("unreviewed conditional else block")
                next_pc = self.skip(next_pc, then)
        else:
            return super().step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 1000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced control ABI frame")
                return {"memory": self.snapshot(), "calls": self.calls, "writes": self.writes,
                        "visited": self.visited, "result": self.value("r0"), "steps": self.steps}
        raise ValueError("control instruction budget exceeded")
