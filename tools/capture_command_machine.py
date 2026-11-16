"""Execute the complete capture metadata command with synthetic service boundaries."""
from __future__ import annotations
import re
import struct

from capture_journal_machine import (CaptureJournalProgram, CaptureJournalMachine, ROOT,
    PAYLOAD, RAW_READ, WRAPPED_READ, PROGRAM)
from capture_loader_machine import CaptureLoaderProgram, REGIONS as GAIN_REGIONS, GAIN_TABLE, GAIN_BYTES
from dot_machine import DotMachine, signed
from pi32v2isa import codec, table

REGIONS = {
    "command": (0x0200A888, 0x0200AD06), "gain_clamp": (0x0200A5E2, 0x0200A5F6),
    "pack": (0x0200A5F6, 0x0200A622), "tenths": (0x0200A7DE, 0x0200A868),
    "slot_parse": (0x020072EA, 0x02007324), "prefix": (0x020283B4, 0x020283CE),
    "decimal_core": (0x020283CE, 0x020284BE), "decimal": (0x020284BE, 0x020284D6),
    "status_text": (0x02007976, 0x020079BC),
}
GAIN_NAMES = ("valid", "gain_value", "aux", "clamp", "scale", "mix", "set_gain")
ALLOCATE, FREE, PRINT, REPORT = 0x0203C15C, 0x0203D218, 0x02007010, 0x0200A768
TEXT, ERROR_WORD, LOCALE_POINTERS, CTYPE, DEFAULT_DETAILS = 0x33000000, 0x01C1F3A4, 0x01C1F39C, 0x0203A343, 0x020362C4
PARSE_OUTPUT, PARSE_END = 0x34000000, 0x34000004
STATIC = {"locale_pointers": (LOCALE_POINTERS, LOCALE_POINTERS + 8),
          "ctype": (CTYPE, CTYPE + 257), "default_details": (DEFAULT_DETAILS, DEFAULT_DETAILS + 16),
          "live_token": (0x02035A18, 0x02035A1D)}
PRINT_COUNTS = {0x02036399: 1, 0x02037760: 1, 0x02036CED: 1, 0x02037440: 3, 0x02036120: 2}


def original_bytes(app, start, end):
    offset = start - 0x02000120 if start >= 0x02000120 else 0x02056780 - 0x02000120 + start - 0x01C00000
    return app[offset:offset + end - start]


class CaptureCommandProgram(CaptureJournalProgram):
    def __init__(self):
        super().__init__()
        gain = CaptureLoaderProgram()
        for name in GAIN_NAMES:
            start, end = GAIN_REGIONS[name]
            for pc, instruction in gain.code.items():
                if start <= pc < end:
                    self.code[pc] = instruction
            self.parallel_seconds.update(pc for pc in gain.parallel_seconds if start <= pc < end)
        self.gain_table = gain.gain_table
        self.pre_command_code, self.command_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.static = {name: original_bytes(app, *region) for name, region in STATIC.items()}
        if struct.unpack("<II", self.static["locale_pointers"]) != (CTYPE, ERROR_WORD):
            raise ValueError("unreviewed locale pointer configuration")
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.command_regions[name] = original_bytes(app, start, end)
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported command instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                row = codec.format(instruction, fields), size, *counts
                if pc + size > end or (pc in self.code and self.code[pc] != row):
                    raise ValueError("overlapping or crossing command instruction")
                self.code[pc] = row
                pc += size
        for pc in set(self.code) - self.pre_command_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ (?:=|\+=)", text) or b_size != 2 or "[" not in following:
                    raise ValueError(f"unreviewed command parallel packet at {pc:#x}")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, text=b"", arguments=(), boundary=None):
        if (len(memory) != 20 or tuple(len(row) for i, row in enumerate(memory) if i != 2) !=
                (272, 1860, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4, 300, 16, 8192, 256, 4)
                or not 0 <= memory[2] <= 255 or operation not in ("command", "tenths", "decimal", "pack")
                or len(text) > 255 or b"\0" in text or len(arguments) != (3 if operation == "pack" else 0)
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("outside the bounded command call domain")
        return CaptureCommandMachine(self, memory, operation, text, arguments, boundary).run()


class CaptureCommandMachine(CaptureJournalMachine):
    def __init__(self, program, memory, operation, text, arguments, boundary):
        super().__init__(program, memory[:19], "invalidate", (0, 0), boundary)
        self.operation = operation
        self.pc = REGIONS[operation][0]
        self.command_frame = 0x30001000 - 52 - 236
        self.allocation, self.allocated, self.allocations, self.releases = False, 0, 0, 0
        self.input_bytes = bytes(text) + b"\0"
        for name, (start, _) in STATIC.items():
            self.memory.update({start + i: byte for i, byte in enumerate(program.static[name])})
        self.memory.update({GAIN_TABLE + i: byte for i, byte in enumerate(program.gain_table)})
        self.memory.update({TEXT + i: byte for i, byte in enumerate(self.input_bytes)})
        self.memory.update({ERROR_WORD + i: byte for i, byte in enumerate(memory[-1])})
        DotMachine.write(self, PARSE_OUTPUT, 0xC0DEC0DE, 4)
        DotMachine.write(self, PARSE_END, 0xFACEFACE, 4)
        self.regs.update(r0=TEXT, r1=0, r2=0, r3=0)
        if operation == "tenths":
            self.regs["r1"] = PARSE_OUTPUT
        elif operation == "decimal":
            self.regs.update(r1=PARSE_END, r2=10)
        elif operation == "pack":
            self.regs.update({f"r{i}": value for i, value in enumerate(arguments)})

    def snapshot(self):
        return super().snapshot() + (bytes(self.memory[ERROR_WORD + i] for i in range(4)),)

    def read(self, address, size):
        if PAYLOAD <= address < PAYLOAD + 8192 and (not self.allocation or address + size > PAYLOAD + self.allocated):
            raise ValueError("payload access exceeds the live allocation request")
        return super().read(address, size)

    def write(self, address, value, size):
        if address in (PARSE_OUTPUT, PARSE_END, ERROR_WORD) and size == 4:
            return DotMachine.write(self, address, value, size)
        if PAYLOAD <= address < PAYLOAD + 8192:
            if not self.allocation or address + size > PAYLOAD + self.allocated:
                raise ValueError("payload write exceeds the live allocation request")
        for start, end in (*STATIC.values(), (GAIN_TABLE, GAIN_TABLE + GAIN_BYTES), (TEXT, TEXT + len(self.input_bytes))):
            if address < end and address + size > start:
                raise ValueError("write to immutable command input/configuration")
        return super().write(address, value, size)

    def source(self, address, size):
        if PAYLOAD <= address < PAYLOAD + 8192:
            if not self.allocation or address + size > PAYLOAD + self.allocated:
                raise ValueError("program source exceeds allocation")
        elif not (self.value("sp") <= address and address + size <= 0x30001000):
            raise ValueError("unknown command program source")
        return "source", 0

    def address(self, expression):
        if match := re.fullmatch(r"\+\+(r\d+)=(-?\d+)", expression):
            self.set(match[1], self.value(match[1]) + int(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def target(self, address, size):
        if PAYLOAD <= address < PAYLOAD + 8192:
            if not self.allocation or address + size > PAYLOAD + self.allocated:
                raise ValueError("reload exceeds allocation")
        elif not (self.value("sp") <= address and address + size <= 0x30001000) and not (0x01C24420 <= address and address + size <= 0x01C24520):
            raise ValueError("unknown command read destination")
        return "read_buffer", 0

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target in (ALLOCATE, FREE, PRINT, REPORT):
                if target == ALLOCATE:
                    args = (self.value("r0"),)
                    if self.allocation or not 4 <= args[0] <= 8152:
                        raise ValueError("invalid allocation lifecycle")
                elif target == FREE:
                    if not self.allocation or self.value("r0") != PAYLOAD:
                        raise ValueError("free outside live allocation")
                    args = (PAYLOAD,)
                elif target == PRINT:
                    count = PRINT_COUNTS.get(self.value("r0"))
                    if count is None:
                        raise ValueError("unreviewed print format")
                    args = tuple(self.value(f"r{i}") for i in range(count))
                else:
                    args = tuple(self.value(f"r{i}") for i in range(4)) + tuple(self.read(self.value("sp") + 4*i, 4) for i in range(6))
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else 0
                if target == ALLOCATE:
                    self.allocation = bool(result)
                    self.allocated = args[0] if result else 0
                    self.allocations += bool(result)
                    result = PAYLOAD if result else 0
                elif target == FREE:
                    self.allocation = False
                    self.releases += 1
                for register in ("r0", "r1", "r2", "r3"):
                    self.set(register, 0xBAD0C0DE)
                self.set("r0", result)
            elif target in self.program.code:
                self.returns.append(next_pc)
                next_pc = target
            else:
                return super().single_step()
        elif text == "{rets, r4} = [sp++]":
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
        elif text == "[--sp] = {rets, r9, r8, r6-r4}":
            self.frames.append(({f"r{i}": self.value(f"r{i}") for i in (4, 5, 6, 8, 9)}, self.value("sp")))
            self.set("sp", self.value("sp") - 24)
        elif text == "{pc, r9, r8, r6-r4} = [sp++]":
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        elif text == "{r6, r4} = [r0+]":
            if self.pc != 0x0200A8F4:
                raise ValueError("unreviewed register-mask load")
            address = self.value("r0")
            self.set("r4", self.read(address, 4))
            self.set("r6", self.read(address + 4, 4))
        elif match := re.fullmatch(r"(r\d+) = (r\d+)\.(b0|l) \((s|u)\)", text):
            bits = 8 if match[3] == "b0" else 16
            value = self.value(match[2]) & ((1 << bits) - 1)
            self.set(match[1], signed(value, bits) if match[4] == "s" else value)
        elif match := re.fullmatch(r"(r\d+_r\d+) >>= (\d+)", text):
            self.set_pair(match[1], self.pair(match[1]) >> (int(match[2]) & 63))
        elif match := re.fullmatch(r"d\[(.+)\] = (r\d+_r\d+)", text):
            self.write(self.address(match[1]), self.pair(match[2]), 8)
        elif match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(u\)", text):
            if not self.value(match[3]):
                raise ValueError("unsigned division by zero")
            self.set(match[1], self.value(match[2]) // self.value(match[3]))
        elif match := re.fullmatch(r"if \(\((r\d+) & (\d+)\) (==|!=) 0\) goto (-?\d+)", text):
            zero = not (self.value(match[1]) & int(match[2]))
            if zero == (match[3] == "=="):
                next_pc += int(match[4])
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        result = super().run()
        if self.allocation or self.allocations != self.releases:
            raise ValueError("command left an allocation live")
        result.update(output=self.read(PARSE_OUTPUT, 4), end=self.read(PARSE_END, 4),
                      allocations=self.allocations, releases=self.releases)
        if self.operation == "decimal":
            result["end"] = (result["end"] - TEXT) & 0xFFFFFFFF
        return result
