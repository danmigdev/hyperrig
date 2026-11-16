"""Execute original selection instructions with sparse RAM and explicit I/O leaves."""
from __future__ import annotations

import re
import struct

from control_action_machine import (ControlActionProgram, ControlActionMachine, GLOBAL,
                                    STATE, OWNER, ROOT, SERVICES)
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

PRESET_STEP, SCENE_FLUSH, SCENE, RESOLVE = 0x02014952, 0x020148BA, 0x02014366, 0x0201499C
ROUTING, EFFECTS = 0x01C32DB0, 0x01C2C220
REGIONS = {
    "preset_step": (PRESET_STEP, RESOLVE),
    "scene_flush": (SCENE_FLUSH, PRESET_STEP),
    "scene": (SCENE, 0x020143AE),
    "effect_resolve": (RESOLVE, 0x020149B6),
    "effect_match": (0x0200C846, 0x0200C89A),
    "effect_flatten": (0x0200C77A, 0x0200C7CE),
    "chain_read": (0x0203089A, 0x020308CC),
    "effect_type": (0x020308CC, 0x020308EA),
    "effect_enabled": (0x020308EA, 0x02030906),
}
NEW_SERVICES = {0x01C04862: ("clock", 0), 0x0200A1D6: ("apply_scene", 1),
                0x0200A228: ("scene_report", 2)}
LEAF_SERVICES = {key: value for key, value in SERVICES.items()
                 if key not in {start for start, _ in REGIONS.values()}} | NEW_SERVICES


def extra_addresses():
    """Address order matches scenes, counts, chain order and effect headers."""
    return ([STATE + 11936 + 260 * i for i in range(4)],
            [ROUTING + 14 + i for i in range(2)],
            [ROUTING + 348 + 10 * i + j for i in range(2) for j in range(10)],
            [EFFECTS + 480 * i + j for i in range(16) for j in range(3)])


EXTRA_ADDRESSES = extra_addresses()


class SelectionProgram(ControlActionProgram):
    def __init__(self):
        super().__init__()
        self.previous_code = set(self.code)
        self.selection_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.selection_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported selection encoding at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a selection boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.previous_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ =", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed selection parallel packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, globals_, state, owner, scenes, counts, order, headers,
                operation, *arguments, boundary=None):
        arities = {"action": 2, "tick": 1, "edge": 4, "preset_step": 1,
                   "scene_flush": 0, "scene": 1, "resolve": 1}
        if (tuple(map(len, (globals_, state, scenes, counts, order, headers))) != (272, 1860, 4, 2, 20, 48)
                or not 0 <= owner <= 255 or any(value > 10 for value in counts)
                or operation not in arities or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the selection verifier's call domain")
        current_scene = struct.unpack_from("<i", globals_, 88)[0]
        if current_scene > 3:
            raise ValueError("outside the current-scene call domain")
        if operation == "action" and (arguments[0] >= 4 or arguments[1] >= 3):
            raise ValueError("outside the selection action domain")
        if operation == "edge" and (arguments[0] >= 5 or arguments[1] > 1):
            raise ValueError("outside the selection edge domain")
        if operation == "resolve" and arguments[0] not in range(236, 270, 3):
            raise ValueError("outside the selection record domain")
        return SelectionMachine(self, globals_, state, owner, scenes, counts, order, headers,
                                operation, arguments, boundary).run()


class SelectionMachine(ControlActionMachine):
    def __init__(self, program, globals_, state, owner, scenes, counts, order, headers,
                 operation, arguments, boundary):
        inherited = operation in ("action", "tick", "edge")
        super().__init__(program, globals_, state, owner, operation if inherited else "tick",
                         arguments if inherited else (0,), boundary)
        for addresses, values in zip(EXTRA_ADDRESSES, (scenes, counts, order, headers)):
            self.memory.update(zip(addresses, values))
        if not inherited:
            self.pc = {"preset_step": PRESET_STEP, "scene_flush": SCENE_FLUSH,
                       "scene": SCENE, "resolve": RESOLVE}[operation]
            self.regs["r0"] = arguments[0] if arguments else 0
            if operation == "resolve":
                self.regs["r0"] += GLOBAL

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[address] for address in addresses)
                                          for addresses in EXTRA_ADDRESSES)

    def read(self, address, size):
        if 0x30000000 <= address < 0x30001000 and address < self.value("sp"):
            raise ValueError("read from released stack storage")
        return super().read(address, size)

    def write(self, address, value, size):
        if 0x30000000 <= address < 0x30001000:
            if address < self.value("sp") or address + size > 0x30001000:
                raise ValueError("selection stack write escaped allocated storage")
            # Locals begin uninitialized; reads still require a prior write.
            return DotMachine.write(self, address, value, size)
        return super().write(address, value, size)

    def address(self, expression):
        if match := re.fullmatch(r"(r\d+)\+\+=(r\d+)", expression):
            before = self.value(match[1])
            self.set(match[1], before + self.value(match[2]))
            return before
        return super().address(expression)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if text == "[--sp] = rets":
            self.frames.append(({}, self.value("sp")))
            self.set("sp", self.value("sp") - 4)
        elif text == "pc = [sp++]":
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"sp \+= (-?\d+)", text):
            after = self.value("sp") + int(match[1])
            if not 0x30000000 <= after <= 0x30001000:
                raise ValueError("selection stack pointer escaped its arena")
            if int(match[1]) < 0:
                for address in range(after, self.value("sp")):
                    self.memory.pop(address, None)
            self.set("sp", after)
        elif match := re.fullmatch(r"(r\d+) = sp \+ (\d+)", text):
            self.set(match[1], self.value("sp") + int(match[2]))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(s\)", text):
            numerator, denominator = signed(self.value(match[2])), signed(self.value(match[3]))
            if denominator == 0 or (numerator == -0x80000000 and denominator == -1):
                raise ValueError("unreviewed signed division exception")
            quotient = abs(numerator) // abs(denominator)
            self.set(match[1], -quotient if (numerator < 0) != (denominator < 0) else quotient)
        elif match := re.fullmatch(r"(r\d+) = abs\((r\d+)\)", text):
            self.set(match[1], min(abs(signed(self.value(match[2]))), 0x7FFFFFFF))
        elif match := re.fullmatch(r"(r\d+) \|= (\d+)", text):
            self.set(match[1], self.value(match[1]) | int(match[2]))
        elif match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target not in NEW_SERVICES:
                return super().single_step()
            count = NEW_SERVICES[target][1]
            args = tuple(self.value(f"r{i}") if i < count else 0 for i in range(3))
            self.calls.append((target, args, self.snapshot()))
            result = self.boundary(target, args, self) if self.boundary else 0
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 200000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced selection execution")
                return {"memory": self.snapshot(), "calls": self.calls, "writes": self.writes,
                        "visited": self.visited, "steps": self.steps, "result": self.value("r0")}
        raise ValueError("selection instruction budget exceeded")
