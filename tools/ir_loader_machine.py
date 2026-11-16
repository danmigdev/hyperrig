"""Execute original IR loading/ownership with bounded allocation and DSP services."""
from __future__ import annotations

import re

from preset_assets_machine import PresetAssetsProgram, PresetAssetsMachine, ROOT, HEADER_BUFFER
from preset_storage_machine import READ, PRIORITY, POLL
from control_machine import GLOBAL, STATE
from pi32v2isa import codec, table

REGIONS = {"attach": (0x02008972, 0x020089C4), "pending": (0x020089C4, 0x020089DA),
           "query": (0x020089DA, 0x020089F2), "refresh": (0x020089F2, 0x02008A62),
           "load": (0x02008A62, 0x02008C28)}
ACTIVITY, ALLOCATE, FREE = 0x02002786, 0x0203C15C, 0x0203D218
LOCK, UNLOCK, INSTALL, INSTALL_SLOT = 0x020038FA, 0x020039E0, 0x0202957E, 0x020295D8
OWNS, REFRESH, NOTIFY = 0x02029AFC, 0x020298CE, 0x02002D10
CALLBACK, HEAP, CAPACITY = 0x01C3441C, 0x32000000, 8152
SERVICES = {ACTIVITY: ("activity", 1), ALLOCATE: ("allocate", 1), FREE: ("free", 1),
            LOCK: ("lock", 0), UNLOCK: ("unlock", 0), INSTALL: ("install", 4),
            INSTALL_SLOT: ("install_slot", 2), OWNS: ("effect_owns", 1), REFRESH: ("effect_refresh", 1),
            NOTIFY: ("notify", 3), PRIORITY: ("priority", 1), POLL: ("poll", 0)}


class IrLoaderProgram(PresetAssetsProgram):
    def __init__(self):
        super().__init__()
        self.pre_ir_code, self.ir_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.ir_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported IR encoding at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses an IR boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_ir_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ =", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed IR parallel packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, reader=None, boundary=None):
        arities = {"attach": 4, "pending": 0, "query": 0, "refresh": 0, "load": 2}
        if (len(memory) != 17 or tuple(len(x) for i, x in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4, 4, CAPACITY)
                or not 0 <= memory[2] <= 255 or operation not in arities
                or len(arguments) != arities[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation == "load" and any(count > 10 for count in memory[4]))):
            raise ValueError("outside the IR verifier's domain")
        return IrLoaderMachine(self, memory, operation, arguments, reader, boundary).run()


class IrLoaderMachine(PresetAssetsMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary):
        super().__init__(program, memory[:15], "mode", (), reader)
        self.boundary, self.allocated = boundary, None
        for base, data in ((CALLBACK, memory[15]), (HEAP, memory[16])):
            self.memory.update({base + i: value for i, value in enumerate(data)})
        self.pc = REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments)))})
        if operation == "query":
            self.regs.update(r0=HEADER_BUFFER, r1=HEADER_BUFFER + 4)

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size))
                                          for base, size in ((CALLBACK, 4), (HEAP, CAPACITY)))

    def read(self, address, size):
        if HEAP <= address < HEAP + CAPACITY and (self.allocated is None or address + size > HEAP + self.allocated):
            raise ValueError("IR read exceeds the allocated request")
        return super().read(address, size)

    def target(self, address, size):
        if HEAP <= address and address + size <= HEAP + CAPACITY:
            if self.allocated is None or address + size > HEAP + self.allocated:
                raise ValueError("IR payload exceeds the allocated request")
            return "allocation", address - HEAP
        return super().target(address, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target not in SERVICES:
                return super().single_step()
            count = SERVICES[target][1]
            args = tuple(self.value(f"r{i}") if i < count else 0 for i in range(4))
            self.calls.append((target, args, self.snapshot()))
            result = self.boundary(target, args, self) if self.boundary else (HEAP if target == ALLOCATE else 0)
            if target == ALLOCATE:
                if args[0] > CAPACITY or result not in (0, HEAP):
                    raise ValueError("unreviewed IR allocator result")
                self.allocated = args[0] if result else None
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif text == "[r5+] = {r7, r4}":
            # ISA stm.post1: ascending register order, base unchanged.
            address = self.value("r5")
            self.write(address, self.value("r4"), 4)
            self.write(address + 4, self.value("r7"), 4)
        elif match := re.fullmatch(r"(r\d+) = uextra\((r\d+), p:(\d+), l:(\d+)\)", text):
            self.set(match[1], (self.value(match[2]) >> int(match[3])) & ((1 << int(match[4])) - 1))
        else:
            return super().single_step()
        self.pc = next_pc
        return True
