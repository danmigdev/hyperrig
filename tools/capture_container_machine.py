"""Execute capture installation and its reader; parser/platform bodies stay external."""
from __future__ import annotations

import re

from capture_loader_machine import (CaptureLoaderProgram, CaptureLoaderMachine, REGIONS as SLOT_REGIONS,
    ACTIVITY, NOTIFY, METADATA, INSTALL, LOADER, REQUEST, ROOT)
from preset_storage_machine import PRIORITY, POLL
from preset_preflight_machine import MOVE
from control_machine import STATE
from pi32v2isa import codec, table

REGIONS = {"install": (INSTALL, 0x020087CC), "read": (LOADER, 0x0201AD4C)}
ALLOCATE, FREE = 0x0203C15C, 0x0203D218
GATE, MODE, PRIORITY_GET, PRIORITY_SET = 0x02002D06, 0x020051FC, 0x02040850, 0x020408D6
PROBE, COMPACT, PREPARE = 0x01C04A7A, 0x020083D6, 0x020025CA
PROCESS_LOAD, CAPABILITIES, CLEANUP = 0x01C04A8E, 0x01C04BAC, 0x02002634
KIND, HEAP, SOURCE, CACHED, EMBEDDED, CAPACITY = STATE + 4120, 0x32000000, 0x32010000, 0x32020000, 0x02033C8C, 8192
BUFFERS = ((HEAP, "allocation"), (SOURCE, "source"), (CACHED, "cached"), (EMBEDDED, "embedded"))
EXTRA = ((KIND, 4), (REQUEST, 17)) + tuple((base, CAPACITY) for base, _ in BUFFERS)
SERVICES = {ACTIVITY: 1, NOTIFY: 3, ALLOCATE: 1, FREE: 1, GATE: 1, MODE: 1,
            PRIORITY_GET: 0, PRIORITY_SET: 1, PROBE: 2, COMPACT: 0, PREPARE: 1,
            PROCESS_LOAD: 4, CAPABILITIES: 0, CLEANUP: 0, PRIORITY: 1, POLL: 0}


class CaptureContainerProgram(CaptureLoaderProgram):
    def __init__(self):
        super().__init__()
        self.pre_container_code, self.container_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.container_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported container instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a container function boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_container_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ (?:=|\+=)", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed container instruction packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, reader=None, boundary=None):
        arities = {"install": 3, "read": 1, "slot": 1}
        if (len(memory) != 21 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4, 4, 17, 8192, 8192, 8192, 8192)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation == "install" and arguments[2] not in (0, LOADER))
                or (operation == "read" and arguments[0] > CAPACITY)):
            raise ValueError("outside the container verifier's call domain")
        return CaptureContainerMachine(self, memory, operation, arguments, reader, boundary).run()


class CaptureContainerMachine(CaptureLoaderMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary):
        super().__init__(program, memory[:15], "mix", (0,), reader, boundary)
        for (base, _), data in zip(EXTRA, memory[15:]):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.allocation_size = arguments[0] if operation == "read" else CAPACITY
        self.pc = SLOT_REGIONS["load"][0] if operation == "slot" else REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments)))})
        if operation == "read":
            self.regs.update(r0=HEAP, r1=REQUEST)
        elif operation == "install":
            self.regs["r3"] = REQUEST

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size)) for base, size in EXTRA)

    def read(self, address, size):
        if HEAP <= address <= HEAP + CAPACITY and address + size > HEAP + self.allocation_size:
            raise ValueError("capture read exceeds the allocated request")
        return super().read(address, size)

    def write(self, address, value, size):
        if EMBEDDED <= address < EMBEDDED + CAPACITY:
            raise ValueError("write to the read-only embedded source")
        if HEAP <= address <= HEAP + CAPACITY and address + size > HEAP + self.allocation_size:
            raise ValueError("capture write exceeds the allocated request")
        return super().write(address, value, size)

    def target(self, address, size):
        for base, label in BUFFERS:
            if base <= address <= address + size <= base + CAPACITY:
                if base == HEAP and address + size > HEAP + self.allocation_size:
                    raise ValueError("capture payload exceeds the allocated request")
                if base == EMBEDDED:
                    raise ValueError("read destination is embedded source")
                return label, address - base
        return super().target(address, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        match = re.fullmatch(r"call (-?\d+)", text)
        if match or text == "call r4":
            target = self.value("r4") if text == "call r4" else next_pc + int(match[1])
            if target in (INSTALL, LOADER):
                self.returns.append(next_pc)
                self.pc = target
                return True
            if target == MOVE:
                destination, source, count = (self.value(f"r{i}") for i in range(3))
                if not HEAP <= destination <= destination + count <= HEAP + self.allocation_size:
                    raise ValueError("memmove exceeds the allocated request")
                if not any(base <= source <= source + count <= base + CAPACITY for base, _ in BUFFERS):
                    raise ValueError("memmove source outside mapped domain")
                data = bytes(self.read(source + i, 1) for i in range(count))
                self.library_calls.append((MOVE, destination, source, count))
                for i, byte in enumerate(data):
                    self.write(destination + i, byte, 1)
                result = destination
            elif target in SERVICES:
                count = SERVICES[target]
                args = tuple(self.value(f"r{i}") if i < count else 0 for i in range(4))
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else 0
                if target == ALLOCATE:
                    if args[0] > CAPACITY or result not in (0, HEAP):
                        raise ValueError("unreviewed allocation result")
                    self.allocation_size = args[0] if result else 0
            else:
                return super().single_step()
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) \* (0x[0-9a-fA-F]+)", text):
            self.set(match[1], self.value(match[2]) * int(match[3], 16))
        else:
            return super().single_step()
        self.pc = next_pc
        return True
