"""Original loader, binding and report instructions integrated with preflight."""
from __future__ import annotations

import re
import struct

from preset_preflight_machine import (PresetPreflightProgram, PresetPreflightMachine,
                                     ROOT, MOVE, HEADER_BUFFER, PAYLOAD_BUFFER, PAYLOAD_MAX)
from selection_machine import GLOBAL, STATE, PRESET_STEP
from control_action_machine import EMIT, TICK, TRANSITION
from pi32v2isa import codec, table

LOAD, SNAPSHOT, REBIND, BINDING = 0x0200CA7E, 0x02003A4E, 0x0200C9F4, 0x0200C7CE
RATE, ELAPSED, REPORT, COMPARE = 0x02002BD8, 0x020031BE, 0x02009DD0, 0x020282BC
APPLY = 0x020092FA
SAVED, COUNTER = STATE + 4012, STATE + 4092
REGIONS = {"load": (LOAD, 0x0200CB3C), "snapshot": (SNAPSHOT, 0x02003AAA),
           "rebind": (REBIND, LOAD), "binding": (BINDING, 0x0200C806),
           "rate": (RATE, 0x02002BEC), "elapsed": (ELAPSED, 0x020031D4),
           "report": (REPORT, 0x02009E14), "compare": (COMPARE, 0x020282F4)}
ENTRIES = {name: start for name, (start, _) in REGIONS.items()} | {
    "preset_step": PRESET_STEP, "action": EMIT, "tick": TICK, "edge": TRANSITION}


class PresetLoaderProgram(PresetPreflightProgram):
    def __init__(self):
        super().__init__()
        self.pre_loader_code = set(self.code)
        self.loader_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.loader_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported loader encoding at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a loader boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        if any(self.code[pc][0].endswith("  #") for pc in set(self.code) - self.pre_loader_code):
            raise ValueError("unreviewed loader parallel packet")

    def execute(self, memory, operation, *arguments, boundary=None, reader=None, application_outputs=(0, 0)):
        arities = {"load": 1, "snapshot": 0, "rebind": 0, "binding": 1, "rate": 0,
                   "elapsed": 1, "report": 4, "compare": 3, "preset_step": 1,
                   "action": 2, "tick": 1, "edge": 4}
        if (len(memory) != 14 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, PAYLOAD_MAX, PAYLOAD_MAX, 36, 4)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the loader verifier's domain")
        if operation not in ("snapshot", "rate", "binding", "compare"):
            if any(value > 10 for value in memory[4]) or struct.unpack_from("<i", memory[0], 88)[0] > 3:
                raise ValueError("outside the selection domain")
        raw_rate = ((struct.unpack_from("<I", memory[0], 44)[0] * 1000) & 0xFFFFFFFF) // 6
        if operation in ("load", "preset_step", "action", "tick", "edge") and raw_rate < 1000:
            raise ValueError("outside the loader calibration domain")
        if operation in ("elapsed", "report") and not raw_rate:
            raise ValueError("outside the elapsed calibration domain")
        if operation == "binding" and memory[10][0] > 16:
            raise ValueError("outside the type-list domain")
        if operation == "compare" and (arguments[0] > 3 or arguments[1] > 3 or arguments[2] > 36):
            raise ValueError("outside the bounded comparison domain")
        if operation == "action" and (arguments[0] > 3 or arguments[1] > 2):
            raise ValueError("outside the action domain")
        if operation == "edge" and (arguments[0] > 4 or arguments[1] > 1):
            raise ValueError("outside the edge domain")
        if (len(application_outputs) != 2 or
                any(value is not None and not 0 <= value <= 0xFFFFFFFF for value in application_outputs)):
            raise ValueError("outside the application-output domain")
        return PresetLoaderMachine(self, memory, operation, arguments, boundary, reader, application_outputs).run()


class PresetLoaderMachine(PresetPreflightMachine):
    def __init__(self, program, memory, operation, arguments, boundary, reader, application_outputs):
        super().__init__(program, memory[:12], "preflight", (0,), boundary, reader)
        for base, data in ((SAVED, memory[12]), (COUNTER, memory[13])):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.pc = ENTRIES[operation]
        self.application_outputs = application_outputs
        for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments))):
            self.regs[f"r{i}"] = value
        if operation == "snapshot":
            self.regs["r0"] = HEADER_BUFFER
        elif operation == "binding":
            self.regs.update(r0=PAYLOAD_BUFFER, r1=arguments[0], r2=HEADER_BUFFER, r3=HEADER_BUFFER + 1)
        elif operation == "compare":
            self.regs.update(r0=HEADER_BUFFER + arguments[0], r1=PAYLOAD_BUFFER + arguments[1], r2=arguments[2])

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size))
                                          for base, size in ((SAVED, 36), (COUNTER, 4)))

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target == APPLY:
                preset, first, second = (self.value(f"r{i}") for i in range(3))
                if (first, second) != (self.value("sp") + 4, self.value("sp")):
                    raise ValueError("unexpected application output pointers")
                args = (preset, 4, 0)
                self.calls.append((APPLY, args, self.snapshot()))
                result = self.boundary(APPLY, args, self) if self.boundary else 0
                for pointer, value in zip((first, second), self.application_outputs):
                    if value is not None:
                        self.write(pointer, value, 4)
                for register in ("r0", "r1", "r2", "r3"):
                    self.set(register, 0xBAD0C0DE)
                self.set("r0", result)
            elif target == MOVE and self.pc in (0x0200CA2A, 0x0200CA6E):
                destination, source, count = (self.value(f"r{i}") for i in range(3))
                expected = (self.value("sp") + 36, GLOBAL + 236, 36)
                if self.pc == 0x0200CA6E:
                    expected = (expected[1], expected[0], 36)
                if (destination, source, count) != expected:
                    raise ValueError("unreviewed action-record memmove")
                data = bytes(self.read(source + i, 1) for i in range(count))
                for i, byte in enumerate(data):
                    self.write(destination + i, byte, 1)
                self.library_calls.append((MOVE, "actions_to_stack" if self.pc == 0x0200CA2A else "stack_to_actions", 36))
                for register in ("r0", "r1", "r2", "r3"):
                    self.set(register, 0xBAD0C0DE)
                self.set("r0", destination)
            else:
                return super().single_step()
        elif match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(u\)", text):
            divisor = self.value(match[3])
            if not divisor:
                raise ValueError("unreviewed unsigned division by zero")
            self.set(match[1], self.value(match[2]) // divisor)
        elif match := re.fullmatch(r"(r\d+) = umin\((r\d+), (r\d+)\)", text):
            self.set(match[1], min(self.value(match[2]), self.value(match[3])))
        elif match := re.fullmatch(r"if \(\((r\d+) & (0x[0-9a-fA-F]+)\) == 0\) goto (-?\d+)", text):
            if not (self.value(match[1]) & int(match[2], 16)):
                next_pc += int(match[3])
        else:
            return super().single_step()
        self.pc = next_pc
        return True
