"""Execute native capture loading with the real parser and memory reset bodies."""
from __future__ import annotations
import re
from capture_parser_machine import CaptureParserProgram, CaptureParserMachine, REGIONS as PARSER_REGIONS, CONFIG
from capture_reset_machine import CaptureResetProgram, CaptureResetMachine, REGIONS as RESET_REGIONS
from capture_dispatch_machine import (CaptureDispatchMachine, REGIONS as DISPATCH_REGIONS,
    LENGTHS, ARITIES, PARSER, RESET, CONTEXT, ARENA, LOADER, ROOT)

ARENA_BYTES = 131072
EXTRA = ((ARENA, ARENA_BYTES), (CONFIG, 4))
REGIONS = {**DISPATCH_REGIONS, **PARSER_REGIONS, **RESET_REGIONS}
OPERATIONS = ("size", "probe", "load_context", "load", "cleanup", "install", "slot")


class CaptureNativeProgram(CaptureParserProgram):
    def __init__(self):
        super().__init__()
        reset = CaptureResetProgram()
        self.reset_regions = reset.reset_regions
        for pc in set(reset.code) - reset.pre_reset_code:
            self.code[pc] = reset.code[pc]
        self.native_regions = {**self.dispatch_regions, **self.parser_regions, **self.reset_regions}

    def execute(self, memory, operation, *arguments, reader=None, boundary=None):
        lengths = LENGTHS + (ARENA_BYTES, 4)
        if (len(memory) != len(lengths)
                or any(len(memory[i]) != n for i, n in enumerate(lengths) if n is not None)
                or not 0 <= memory[2] <= 255 or operation not in OPERATIONS
                or len(arguments) != ARITIES[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation == "install" and arguments[2] not in (0, LOADER))):
            raise ValueError("outside the native capture integration domain")
        return CaptureNativeMachine(self, memory, operation, arguments, reader, boundary).run()


class CaptureNativeMachine(CaptureParserMachine, CaptureResetMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary):
        CaptureDispatchMachine.__init__(self, program, memory[:27], operation, arguments, reader, boundary, None)
        for (base, _), data in zip(EXTRA, memory[27:]):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.operation, self.parser_entries, self.reset_entries, self.reset_words = operation, [], 0, 0

    def snapshot(self):
        return CaptureDispatchMachine.snapshot(self) + tuple(
            bytes(self.memory[base + i] for i in range(size)) for base, size in EXTRA)

    def write(self, address, value, size):
        if RESET <= self.pc < RESET_REGIONS["reset"][1]:
            if size != 4 or value != 0:
                raise ValueError("unexpected integrated reset write")
            self.reset_words += 1
        return CaptureDispatchMachine.write(self, address, value, size)

    def single_step(self):
        text, size, _, _ = self.program.code[self.pc]
        match = re.fullmatch(r"call (-?\d+)", text)
        if match:
            target = self.pc + size + int(match[1])
            if target in (PARSER, RESET, PARSER_REGIONS["read64"][0]):
                if target == PARSER:
                    context, ledger, source, length = (self.value(f"r{i}") for i in range(4))
                    self.parser_entries.append((context == CONTEXT, tuple(self.read(ledger + i * 4, 4) for i in range(3)), source, length))
                elif target == RESET:
                    if self.value("r0") != CONTEXT:
                        raise ValueError("unreviewed integrated reset context")
                    self.reset_entries += 1
                self.visited.add(self.pc)
                self.returns.append(self.pc + size)
                self.pc = target
                return True
        return CaptureParserMachine.single_step(self)

    def run(self):
        while self.steps < 50000000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced native capture integration")
                return {"result": self.value("r0"), "memory": self.snapshot(), "calls": self.calls,
                        "visited": self.visited, "steps": self.steps, "parser_entries": self.parser_entries,
                        "reset_entries": self.reset_entries, "reset_words": self.reset_words}
        raise ValueError("native capture instruction budget exceeded")
