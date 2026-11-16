"""Original preset cache/header/CRC instructions with a scripted read boundary."""
from __future__ import annotations

import re
import struct

from selection_machine import SelectionProgram, SelectionMachine, ROOT, STATE, LEAF_SERVICES
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

AVAILABLE, ADDRESS, BLOCK = 0x0200CF88, 0x0200777A, 0x020026BA
HEADER, UPDATE, CHECKSUM, RECORD = 0x02006F14, 0x020028C2, 0x0200704E, 0x020079BC
READ, PREPARE, PRIORITY, POLL = 0x02002810, 0x020031D4, 0x020054A8, 0x020027E4
HEADER_BUFFER, PAYLOAD_BUFFER = 0x31000000, 0x31001000
PAYLOAD_MAX = 1490
MAP, SCRATCH = STATE + 3476, STATE + 5812
REGIONS = {"available": (AVAILABLE, 0x0200D060), "address": (ADDRESS, 0x020077AA),
           "block": (BLOCK, 0x020026D6), "header": (HEADER, 0x02006F3A),
           "crc_update": (UPDATE, 0x020028F2), "checksum": (CHECKSUM, 0x020070A4),
           "record": (RECORD, 0x020079F6)}
NEW_SERVICES = {PREPARE: ("prepare", 0), PRIORITY: ("priority", 1), POLL: ("poll", 0)}
STORAGE_LEAVES = {key: value for key, value in LEAF_SERVICES.items() if key != AVAILABLE} | NEW_SERVICES
EXTRA = ((MAP, 16), (SCRATCH, 256), (HEADER_BUFFER, 40), (PAYLOAD_BUFFER, PAYLOAD_MAX))


class PresetStorageProgram(SelectionProgram):
    def __init__(self):
        super().__init__()
        self.pre_storage_code = set(self.code)
        self.storage_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.storage_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported storage encoding at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        field = instruction.block[kind]
                        spec = instruction.fields[field]
                        counts[i] = fields[field] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a storage boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_storage_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ =", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed storage packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, boundary=None, reader=None):
        arities = {"available": 1, "address": 1, "block": 1, "header": 3, "record": 3,
                   "crc_update": 2, "checksum": 1, "preset_step": 1,
                   "action": 2, "tick": 1, "edge": 4}
        if (len(memory) != 11 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, PAYLOAD_MAX)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the storage verifier's call domain")
        if operation in ("crc_update", "checksum") and arguments[-1] > PAYLOAD_MAX:
            raise ValueError("outside the bounded CRC domain")
        if operation == "record" and arguments[2] > PAYLOAD_MAX:
            raise ValueError("outside the record buffer domain")
        if operation in ("preset_step", "action", "tick", "edge"):
            if any(value > 10 for value in memory[4]) or struct.unpack_from("<i", memory[0], 88)[0] > 3:
                raise ValueError("outside the integrated selection domain")
            if operation == "action" and (arguments[0] > 3 or arguments[1] > 2):
                raise ValueError("outside the action domain")
            if operation == "edge" and (arguments[0] > 4 or arguments[1] > 1):
                raise ValueError("outside the edge domain")
        return PresetStorageMachine(self, memory, operation, arguments, boundary, reader).run()


class PresetStorageMachine(SelectionMachine):
    def __init__(self, program, memory, operation, arguments, boundary, reader):
        inherited = operation in ("preset_step", "action", "tick", "edge")
        super().__init__(program, *memory[:7], operation if inherited else "scene",
                         arguments if inherited else (0,), boundary)
        for (base, _), values in zip(EXTRA, memory[7:]):
            self.memory.update({base + i: value for i, value in enumerate(values)})
        self.reader = reader
        if not inherited:
            self.pc = REGIONS[operation][0]
            args = list(arguments) + [0] * (4 - len(arguments))
            for i, value in enumerate(args):
                self.regs[f"r{i}"] = value
            if operation in ("header", "record"):
                self.regs["r3"] = HEADER_BUFFER
            if operation == "record":
                # Fifth original ABI argument is at the caller's stack top.
                DotMachine.write(self, 0x30001000, PAYLOAD_BUFFER, 4)
            if operation == "crc_update":
                self.regs.update(r1=PAYLOAD_BUFFER, r2=arguments[1])
            if operation == "checksum":
                self.regs.update(r0=PAYLOAD_BUFFER, r1=arguments[0])

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size))
                                          for base, size in EXTRA)

    def target(self, address, size):
        for base, capacity, label in ((SCRATCH, 256, "scratch"), (HEADER_BUFFER, 40, "header"),
                                      (PAYLOAD_BUFFER, PAYLOAD_MAX, "payload")):
            if base <= address and address + size <= base + capacity:
                return label, address - base
        if self.value("sp") <= address < 0x30001000 and size == 40 and address + size <= 0x30001000:
            return "local_header", 0
        raise ValueError("read boundary escaped a reviewed destination")

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target == READ:
                address, destination, count = (self.value(f"r{i}") for i in range(3))
                label, offset = self.target(destination, count)
                self.calls.append((READ, (address, label, offset, count), self.snapshot()))
                if self.reader is None:
                    raise ValueError("no read boundary supplied")
                result, payload = self.reader(address, count)
                if len(payload) > count or (result == 0 and len(payload) != count):
                    raise ValueError("read boundary violated its buffer contract")
                for i, value in enumerate(payload):
                    self.write(destination + i, value, 1)
            elif target in NEW_SERVICES:
                count = NEW_SERVICES[target][1]
                args = tuple(self.value(f"r{i}") if i < count else 0 for i in range(3))
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else 0
            else:
                return super().single_step()
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif match := re.fullmatch(r"(r\d+_r\d+) = (r\d+_r\d+)", text):
            self.set_pair(match[1], self.pair(match[2]))
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \(s\)", text):
            self.set(match[1], signed(self.read(self.address(match[2]), 1), 8))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) (&|\^|\+) (~?)(r\d+|0x[0-9a-fA-F]+)", text):
            left, right = self.value(match[2]), self.value(match[5])
            if match[4]:
                right = ~right
            value = {"&": lambda: left & right,
                     "^": lambda: left ^ right, "+": lambda: left + right}[match[3]]()
            self.set(match[1], value)
        elif match := re.fullmatch(r"(r\d+) (\^=|&=) (r\d+)", text):
            left, right = self.value(match[1]), self.value(match[3])
            self.set(match[1], left ^ right if match[2] == "^=" else left & right)
        elif match := re.fullmatch(r"\[(.+)\] \|= (r\d+)", text):
            address = self.address(match[1])
            self.write(address, self.read(address, 4) | self.value(match[2]), 4)
        elif match := re.fullmatch(r"if \(\((r\d+) & (r\d+)\) == 0\) goto (-?\d+)", text):
            if not (self.value(match[1]) & self.value(match[2])):
                next_pc += int(match[3])
        elif match := re.fullmatch(r"(r\d+) = umax\((r\d+), (r\d+)\)", text):
            self.set(match[1], max(self.value(match[2]), self.value(match[3])))
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        while self.steps < 4000000:
            self.steps += 1
            if not self.step():
                if self.frames or self.returns or self.else_skips or self.value("sp") != 0x30001000:
                    raise ValueError("unbalanced storage execution")
                return {"memory": self.snapshot(), "calls": self.calls, "writes": self.writes,
                        "visited": self.visited, "steps": self.steps, "result": self.value("r0")}
        raise ValueError("storage instruction budget exceeded")
