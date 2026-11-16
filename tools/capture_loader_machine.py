"""Execute capture loading and gain helpers, with explicit journal/install boundaries."""
from __future__ import annotations

import hashlib
import re

from preset_assets_machine import PresetAssetsProgram, PresetAssetsMachine, ROOT, RESULT, HEADER_BUFFER
from preset_storage_machine import PRIORITY
from dot_machine import signed
from pi32v2isa import codec, table

REGIONS = {
    "valid": (0x02007E62, 0x02007E9E),
    "gain_value": (0x02007E9E, 0x02007EAC),
    "aux": (0x02007EAC, 0x02007ECE),
    "clamp": (0x02007ECE, 0x02007EE2),
    "scale": (0x02007EE2, 0x02007EF2),
    "mix": (0x02007EF2, 0x02007F3A),
    "set_gain": (0x02007F3A, 0x02007F50),
    "apply_metadata": (0x02007F50, 0x02007F7E),
    "signature": (0x02007F7E, 0x02008016),
    "load": (0x020087CC, 0x02008972),
}
ACTIVITY, NOTIFY = 0x02002786, 0x02002D10
METADATA, INSTALL, LOADER = 0x02007DBE, 0x02008586, 0x0201ACD8
GAIN_TABLE, GAIN_BYTES = 0x02033BC8, 196
REQUEST = 0x31005000
ARITIES = {name: (2 if name in ("set_gain", "apply_metadata") else 1) for name in REGIONS}


class CaptureLoaderProgram(PresetAssetsProgram):
    def __init__(self):
        super().__init__()
        self.pre_capture_code = set(self.code)
        self.capture_regions = {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.capture_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported capture instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a capture function boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        self.gain_table = app[GAIN_TABLE - 0x02000120:GAIN_TABLE - 0x02000120 + GAIN_BYTES]
        if hashlib.sha256(self.gain_table).hexdigest() != "cd539f2ab0183841f5adecc529273af02213eeb221c7723ef556f9229aa620da":
            raise ValueError("gain table differs from the reviewed input")
        for pc in set(self.code) - self.pre_capture_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ =", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed capture instruction packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, reader=None, boundary=None):
        if (len(memory) != 15 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4)
                or not 0 <= memory[2] <= 255 or operation not in ARITIES
                or len(arguments) != ARITIES[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the capture verifier's call domain")
        return CaptureLoaderMachine(self, memory, operation, arguments, reader, boundary).run()


class BoundaryView:
    """Expose the same 17-byte request alias to native and C callback scripts."""
    def __init__(self, machine, request=None):
        self.machine, self.request = machine, request

    def write(self, address, value, size):
        if REQUEST <= address < REQUEST + 17:
            if self.request is None or address + size > REQUEST + 17:
                raise ValueError("write outside the initialized request")
            address = self.request + address - REQUEST
        self.machine.write(address, value, size)


class CaptureLoaderMachine(PresetAssetsMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary):
        super().__init__(program, memory, "mode", (), reader)
        self.boundary = boundary
        self.pc = REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments)))})
        if operation == "aux":
            self.regs["r1"] = RESULT
        elif operation == "signature":
            self.regs["r1"] = HEADER_BUFFER
        self.memory.update({GAIN_TABLE + i: byte for i, byte in enumerate(program.gain_table)})

    def write(self, address, value, size):
        if address < GAIN_TABLE + GAIN_BYTES and address + size > GAIN_TABLE:
            raise ValueError("write to the immutable capture gain table")
        return super().write(address, value, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            request = None
            if target in (ACTIVITY, PRIORITY, NOTIFY):
                count = 3 if target == NOTIFY else 1
                args = tuple(self.value(f"r{i}") if i < count else 0 for i in range(3))
            elif target == METADATA:
                if self.value("r3") != 0:
                    raise ValueError("unreviewed metadata lookup argument")
                header = bytes(self.read(self.value("r1") + i, 1) for i in range(40))
                args = self.value("r0"), header, self.value("r2"), 0
            elif target == INSTALL:
                if (self.value("r0"), self.value("r2")) != (0, LOADER):
                    raise ValueError("unreviewed capture install request")
                request = self.value("r3")
                data = bytes(self.read(request + i, 1) for i in range(17))
                args = 0, self.value("r1"), LOADER, data
            else:
                return super().single_step()
            self.calls.append((target, args, self.snapshot()))
            result = self.boundary(target, args, BoundaryView(self, request)) if self.boundary else 0
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif text == "[--sp] = {rets, r9, r8, r6-r4}":
            self.frames.append(({f"r{i}": self.value(f"r{i}") for i in (4, 5, 6, 8, 9)}, self.value("sp")))
            self.set("sp", self.value("sp") - 24)
        elif text == "{pc, r9, r8, r6-r4} = [sp++]":
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif match := re.fullmatch(r"(r\d+) = (r\d+)\.(b0|l) \((s|u)\)", text):
            bits = 8 if match[3] == "b0" else 16
            value = self.value(match[2]) & ((1 << bits) - 1)
            self.set(match[1], signed(value, bits) if match[4] == "s" else value)
        elif match := re.fullmatch(r"(r\d+_r\d+) >>= (\d+)", text):
            self.set_pair(match[1], self.pair(match[1]) >> (int(match[2]) & 63))
        elif text == "{r11, r8} = [r0+]" and self.pc == 0x020088DC:
            # Register-mask loads use ascending register order; '+' does not write back.
            address = self.value("r0")
            self.set("r8", self.read(address, 4))
            self.set("r11", self.read(address + 4, 4))
        else:
            return super().single_step()
        self.pc = next_pc
        return True
