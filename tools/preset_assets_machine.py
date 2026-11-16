"""Execute original asset identities and working-preset routing dependencies."""
from __future__ import annotations

import re

from preset_preflight_machine import (PresetPreflightProgram, PresetPreflightMachine,
    ROOT, WORKING, HEADER_BUFFER, PAYLOAD_BUFFER, PAYLOAD_MAX)
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

REGIONS = {
    "header": (0x02006F3A, 0x02006F70),
    "extended": (0x02006F70, 0x02006F8E),
    "identity": (0x02006F8E, 0x02006FB0),
    "resolve": (0x02006FB0, 0x02007008),
    "mode": (0x02007B88, 0x02007B9C),
    "layout": (0x02007B9C, 0x02007C6A),
    "matches": (0x02007C6A, 0x02007C94),
    "state416": (0x02007C94, 0x02007CA6),
    "clamp": (0x02007CA6, 0x02007CBA),
}
PLACEMENT, BRANCHES, RESULT = 0x31002000, 0x31003000, 0x31004000
EXTRA = ((PLACEMENT, 16), (BRANCHES, 12), (RESULT, 4))


class PresetAssetsProgram(PresetPreflightProgram):
    def __init__(self):
        super().__init__()
        self.pre_assets_code = set(self.code)
        self.assets_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.assets_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported asset instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses an asset function boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_assets_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ (?:=|<=)", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed asset instruction packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, reader=None):
        arities = {"header": 2, "extended": 2, "identity": 2, "resolve": 1,
                   "mode": 0, "layout": 0, "matches": 4, "state416": 0, "clamp": 1}
        if (len(memory) != 15 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, PAYLOAD_MAX, PAYLOAD_MAX, 16, 12, 4)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the asset verifier's call domain")
        return PresetAssetsMachine(self, memory, operation, arguments, reader).run()


class PresetAssetsMachine(PresetPreflightMachine):
    def __init__(self, program, memory, operation, arguments, reader):
        super().__init__(program, memory[:12], "preflight", (0,), None, None)
        self.reader = (lambda address, count: reader(address, count, self)) if reader else None
        for (base, _), data in zip(EXTRA, memory[12:]):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.pc = REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments)))})
        if operation == "header":
            self.regs.update(r0=arguments[0], r1=HEADER_BUFFER, r2=arguments[1], r3=RESULT)
        elif operation == "identity":
            self.regs["r2"] = PAYLOAD_BUFFER
        elif operation == "resolve":
            self.regs.update(r1=HEADER_BUFFER, r2=RESULT)
        elif operation == "layout":
            self.regs.update(r0=PLACEMENT, r1=BRANCHES)
        elif operation == "matches":
            self.regs.update(r0=PAYLOAD_BUFFER, r1=arguments[0], r2=arguments[1], r3=arguments[2])
            DotMachine.write(self, 0x30001000, arguments[3], 4)

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size))
                                          for base, size in EXTRA)

    def target(self, address, size):
        if size == 4 and address == self.value("sp"):
            return "local_tail", 0
        return super().target(address, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if text == "[--sp] = {rets, r5, r4}":
            self.frames.append(({name: self.value(name) for name in ("r4", "r5")}, self.value("sp")))
            self.set("sp", self.value("sp") - 12)
        elif text == "{pc, r5, r4} = [sp++]":
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"\[(.+)\] = (0x[0-9a-fA-F]+)", text):
            self.write(self.address(match[1]), int(match[2], 16), 4)
        elif match := re.fullmatch(r"(r\d+_r\d+) = 0", text):
            self.set_pair(match[1], 0)
        elif match := re.fullmatch(r"(r\d+) \^= (\d+)", text):
            self.set(match[1], self.value(match[1]) ^ int(match[2]))
        elif match := re.fullmatch(r"(r\d+) <= insert\((r\d+), p:(\d+), l:(\d+)\)", text):
            position, length = int(match[3]), int(match[4])
            mask = (1 << length) - 1
            self.set(match[1], (self.value(match[1]) & ~(mask << position)) |
                     ((self.value(match[2]) & mask) << position))
        elif match := re.fullmatch(r"(r\d+) = smin\((r\d+), (r\d+)\)", text):
            self.set(match[1], min(signed(self.value(match[2])), signed(self.value(match[3]))))
        elif self.pc in (0x02007BAC, 0x02007BB2, 0x02007BE8):
            expected = {0x02007BAC: ("rep 2 16 {", ("b[r4++=1] = r2",), 16),
                        0x02007BB2: ("rep 2 12 {", ("b[r4++=1] = r2",), 12),
                        0x02007BE8: ("rep 4 12 {", ("r2 = b[r0++=1] (u)", "b[r1++=1] = r2"), 12)}
            instruction, body, count = expected[self.pc]
            if text != instruction or tuple(self.program.code[next_pc + 2*i][0] for i in range(len(body))) != body:
                raise ValueError("unreviewed layout REP body")
            for _ in range(count):
                self.pc = next_pc
                for _ in body:
                    if not self.step():
                        raise ValueError("unexpected return inside layout REP")
                    self.steps += 1
            next_pc += 2 * len(body)
        else:
            return super().single_step()
        self.pc = next_pc
        return True
