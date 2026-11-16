"""Execute original preset preflight with bounded memory-library contracts."""
from __future__ import annotations

import re

from preset_storage_machine import (PresetStorageProgram, PresetStorageMachine, ROOT,
    HEADER_BUFFER, PAYLOAD_BUFFER, PAYLOAD_MAX)
from pi32v2isa import codec, table

PREFLIGHT, NEEDS_CONVERSION, CONVERT_EFFECT = 0x020079F6, 0x0202A43C, 0x0202A452
WORKING, CURVE = 0x01C24790, 0x0203B334
CLEAR, MOVE = 0x02033412, 0x02032B2E
REGIONS = {"preflight": (PREFLIGHT, 0x02007B88),
           "needs_conversion": (NEEDS_CONVERSION, CONVERT_EFFECT),
           "convert_effect": (CONVERT_EFFECT, 0x0202A50A)}
LIBRARY_REGIONS = {"memset_contract": (CLEAR, 0x0203343E),
                   "memmove_contract": (MOVE, 0x02032BF0)}


class PresetPreflightProgram(PresetStorageProgram):
    def __init__(self):
        super().__init__()
        self.pre_preflight_code = set(self.code)
        self.preflight_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.preflight_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported preflight encoding at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a preflight boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        self.library_regions = {name: app[start - 0x02000120:end - 0x02000120]
                                for name, (start, end) in LIBRARY_REGIONS.items()}
        self.curve = app[CURVE - 0x02000120:CURVE - 0x02000120 + 11]
        for pc in set(self.code) - self.pre_preflight_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ =", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed preflight packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, boundary=None, reader=None):
        arities = {"preflight": 1, "needs_conversion": 1, "convert_effect": 2}
        if (len(memory) != 12 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, PAYLOAD_MAX, PAYLOAD_MAX)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the preflight verifier's domain")
        if operation == "convert_effect" and arguments[1] not in (0, 1):
            raise ValueError("parameter buffer must be absent or present")
        return PresetPreflightMachine(self, memory, operation, arguments, boundary, reader).run()


class PresetPreflightMachine(PresetStorageMachine):
    def __init__(self, program, memory, operation, arguments, boundary, reader):
        super().__init__(program, memory[:11], "block", (0,), boundary, reader)
        self.memory.update({WORKING + i: byte for i, byte in enumerate(memory[11])})
        self.memory.update({CURVE + i: byte for i, byte in enumerate(program.curve)})
        self.library_calls = []
        self.pc = REGIONS[operation][0]
        self.regs["r0"] = arguments[0]
        self.regs["r1"] = (HEADER_BUFFER if operation == "preflight" else
                           PAYLOAD_BUFFER if operation == "convert_effect" and arguments[1] else 0)

    def snapshot(self):
        return super().snapshot() + (bytes(self.memory[WORKING + i] for i in range(PAYLOAD_MAX)),)

    def target(self, address, size):
        if WORKING <= address and address + size <= WORKING + PAYLOAD_MAX:
            return "working", address - WORKING
        return super().target(address, size)

    def address(self, expression):
        if match := re.fullmatch(r"(r\d+)\+\+=(-\d+)", expression):
            before = self.value(match[1])
            self.set(match[1], before + int(match[2]))
            return before
        if match := re.fullmatch(r"\+\+(r\d+)=(r\d+)", expression):
            self.set(match[1], self.value(match[1]) + self.value(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def write(self, address, value, size):
        if address < CURVE + 11 and address + size > CURVE:
            raise ValueError("write to the immutable conversion table")
        return super().write(address, value, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target not in (CLEAR, MOVE):
                return super().single_step()
            destination, source, count = (self.value(f"r{i}") for i in range(3))
            if not WORKING <= destination <= destination + count <= WORKING + PAYLOAD_MAX:
                raise ValueError("library destination escaped the working buffer")
            if target == CLEAR:
                if (destination, source, count) != (WORKING, 0, PAYLOAD_MAX):
                    raise ValueError("unreviewed memset call")
                data = bytes(count)
            else:
                if (count not in (14, 16) or not WORKING <= source <= source + count <= WORKING + PAYLOAD_MAX
                        or destination < source):
                    raise ValueError("unreviewed memmove call")
                data = bytes(self.read(source + i, 1) for i in range(count))
            # These are explicit library contracts, not interpreted helper bodies.
            self.library_calls.append((target, destination - WORKING,
                                       source - WORKING if target == MOVE else source, count))
            for i, byte in enumerate(data):
                self.write(destination + i, byte, 1)
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", destination)
        elif text == "rep 4 5 {" and self.pc == 0x02007AAC:
            # The sole immediate REP copies five words. No nested REP or branch.
            if self.program.code[next_pc][0] != "r2 = [r1++=4]" or self.program.code[next_pc + 2][0] != "[r0++=4] = r2":
                raise ValueError("unreviewed immediate REP body")
            for _ in range(5):
                self.pc = next_pc
                for _ in range(2):
                    if not self.step():
                        raise ValueError("unexpected return inside REP")
                    self.steps += 1
            next_pc += 4
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        result = super().run()
        result["library_calls"] = self.library_calls
        return result
