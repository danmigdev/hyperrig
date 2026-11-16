"""Execute original capture reset loops and the unchanged installation callers."""
from __future__ import annotations
import re

from capture_dispatch_machine import (CaptureDispatchProgram, CaptureDispatchMachine,
    ROOT, LENGTHS, ARITIES, RESET, CONTEXT, ARENA, LOADER, image_offset)
from pi32v2isa import codec, table

REGIONS = {"reset": (RESET, 0x01C1296C)}
ARENA_BYTES, WRAP, WRAP_BYTES = 65536, 0xFFFFFFFC, 4096
EXTRA = ((ARENA, ARENA_BYTES), (WRAP, WRAP_BYTES))


class CaptureResetProgram(CaptureDispatchProgram):
    def __init__(self):
        super().__init__()
        self.pre_reset_code, self.reset_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.reset_regions[name] = app[image_offset(start):image_offset(end)]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, image_offset(pc))
                if decoded is None:
                    raise ValueError("unsupported reset instruction")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                text = codec.format(instruction, fields)
                if pc + size > end or text.endswith("  #"):
                    raise ValueError("unreviewed reset boundary or parallel packet")
                self.code[pc] = text, size, *counts
                pc += size

    def execute(self, memory, operation, *arguments, reader=None, boundary=None, parser=None):
        lengths = LENGTHS + (ARENA_BYTES, WRAP_BYTES)
        arities = {"reset": 0, **{name: ARITIES[name] for name in ("load_context", "load", "cleanup", "install", "slot")}}
        if (len(memory) != len(lengths)
                or any(len(memory[i]) != n for i, n in enumerate(lengths) if n is not None)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation == "install" and arguments[2] not in (0, LOADER))):
            raise ValueError("outside the reset verifier's call domain")
        return CaptureResetMachine(self, memory, operation, arguments, reader, boundary, parser).run()


class CaptureResetMachine(CaptureDispatchMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary, parser):
        super().__init__(program, memory[:27], operation if operation != "reset" else "load",
                         arguments if operation != "reset" else (0, 0, 0, 0), reader, boundary, parser)
        for (base, _), data in zip(EXTRA, memory[27:]):
            self.memory.update({(base + i) & 0xFFFFFFFF: byte for i, byte in enumerate(data)})
        self.reset_entries, self.clears, self.operation = int(operation == "reset"), [], operation
        if operation == "reset":
            self.pc, self.regs["r0"] = RESET, CONTEXT

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[(base + i) & 0xFFFFFFFF] for i in range(size)) for base, size in EXTRA)

    def address(self, expression):
        match = re.fullmatch(r"\+\+(r\d+)=(\d+)", expression)
        if match:
            self.set(match[1], self.value(match[1]) + int(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def write(self, address, value, size):
        if RESET <= self.pc < REGIONS["reset"][1] and address != CONTEXT + 88:
            if size != 4 or value:
                raise ValueError("unexpected reset write")
            self.clears.append((address, self.read(address, 4)))
        return super().write(address, value, size)

    def single_step(self):
        text, size, _, _ = self.program.code[self.pc]
        match = re.fullmatch(r"call (-?\d+)", text)
        if match and self.pc + size + int(match[1]) == RESET:
            if self.value("r0") != CONTEXT:
                raise ValueError("unreviewed reset context")
            self.visited.add(self.pc)
            self.returns.append(self.pc + size)
            self.pc = RESET
            self.reset_entries += 1
            return True
        return super().single_step()

    def run(self):
        while self.steps < 1_000_000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced reset ABI execution")
                return {"result": 0 if self.operation == "reset" else self.value("r0"),
                        "memory": self.snapshot(), "calls": self.calls, "visited": self.visited,
                        "clears": self.clears, "reset_entries": self.reset_entries, "steps": self.steps}
        raise ValueError("reset verifier instruction budget exceeded")
