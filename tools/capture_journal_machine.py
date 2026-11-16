"""Execute journal write/erase wrappers, rewrite helper and append continuation."""
from __future__ import annotations
import re
import struct

from capture_metadata_machine import CaptureMetadataProgram, CaptureMetadataMachine, ROOT, HEADER_BUFFER, DETAILS
from dot_machine import DotMachine
from pi32v2isa import codec, table

REGIONS = {"invalidate": (0x0200294E, 0x02002994), "write": (0x02002F16, 0x02002FAE),
    "erase": (0x02002D9E, 0x02002E08), "write_offset": (0x0200A868, 0x0200A878),
    "rewrite": (0x0200A622, 0x0200A72E), "compare": (0x020282BC, 0x020282F4),
    "append": (0x0200AB96, 0x0200AC36), "append_success": (0x0200ACB4, 0x0200ACDE)}
PAYLOAD, SCRATCH = 0x32000000, 0x01C24420
CLOCK, ELAPSED, PREPARE, MODE = 0x01C04862, 0x020031BE, 0x02002772, 0x02002BCC
ACTIVITY, GATE, EVENT, NOTIFY = 0x02002786, 0x02002D06, 0x02002D70, 0x02002D10
WAIT_READY, YIELD, ERASE_SECTOR = 0x02002920, 0x0203FEB8, 0x02002B80
RAW_READ, WRAPPED_READ, PROGRAM = 0x02002806, 0x02002810, 0x02002EF2
SERVICES = {CLOCK: 0, ELAPSED: 1, PREPARE: 0, MODE: 0, ACTIVITY: 1, GATE: 1,
            EVENT: 3, NOTIFY: 3, WAIT_READY: 0, YIELD: 1, ERASE_SECTOR: 3}
ARITIES = {"invalidate": 2, "write": 3, "write_offset": 4, "erase": 2,
           "rewrite": 3, "compare": 3, "append": 4}


class CaptureJournalProgram(CaptureMetadataProgram):
    def __init__(self):
        super().__init__()
        self.pre_journal_code, self.journal_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.journal_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported journal instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a journal region boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_journal_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ (?:=|\+=)", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed journal parallel packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, boundary=None):
        if (len(memory) != 19 or tuple(len(x) for i, x in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4, 300, 16, 8192, 256)
                or not 0 <= memory[2] <= 255 or operation not in ARITIES
                or len(arguments) != ARITIES[operation] or any(not 0 <= x <= 0xFFFFFFFF for x in arguments)):
            raise ValueError("outside the capture journal call domain")
        if operation in ("write", "write_offset"):
            size, offset = arguments[-2:]
            if size > 8192 or offset + size > 8192:
                raise ValueError("outside the journal payload domain")
        if operation == "rewrite" and arguments[2] > 8152:
            raise ValueError("outside the rewrite payload domain")
        if operation == "erase" and arguments[1] > 64:
            raise ValueError("outside the erase domain")
        if operation == "compare" and (arguments[2] > 256 or any(offset + arguments[2] > 8192 for offset in arguments[:2])):
            raise ValueError("outside the compare domain")
        if operation == "append" and (struct.unpack_from("<I", memory[9], 4)[0] > 8152 or
                any(value > 255 for value in struct.unpack_from("<II", memory[16], 8))):
            raise ValueError("outside the append continuation domain")
        return CaptureJournalMachine(self, memory, operation, arguments, boundary).run()


class CaptureJournalMachine(CaptureMetadataMachine):
    def __init__(self, program, memory, operation, arguments, boundary):
        self.append_frame = None
        self.aliases = ()
        super().__init__(program, memory[:17], "capacity", (0,), None)
        self.boundary, self.operation = boundary, operation
        for base, data in ((PAYLOAD, memory[17]), (SCRATCH, memory[18])):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.pc = REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments[:4]) + [0] * (4 - min(len(arguments), 4)))})
        if operation == "write":
            self.regs.update(r0=arguments[0], r1=PAYLOAD + arguments[2], r2=arguments[1])
        elif operation == "write_offset":
            DotMachine.write(self, 0x31007000, arguments[0], 4)
            self.regs.update(r0=0x31007000, r1=arguments[1], r2=PAYLOAD + arguments[3], r3=arguments[2])
        elif operation == "rewrite":
            self.regs.update(r0=arguments[0], r1=arguments[1], r2=HEADER_BUFFER, r3=PAYLOAD)
            DotMachine.write(self, 0x30001000, arguments[2], 4)
        elif operation == "compare":
            self.regs.update(r0=PAYLOAD + arguments[0], r1=PAYLOAD + arguments[1], r2=arguments[2])
        elif operation == "append":
            # Enter the already allocated command frame at the documented
            # continuation; parsing/header loading/scanning precede this scope.
            self.append_frame = 0x30001000 - 52 - 236
            self.regs.update(sp=self.append_frame, r4=arguments[0], r6=arguments[2],
                             r7=arguments[1], r8=0x10203040, r12=arguments[3])
            self.aliases = ((self.append_frame + 164, HEADER_BUFFER, 40), (self.append_frame + 128, DETAILS, 16))
            DotMachine.write(self, self.append_frame + 156, arguments[0], 4)

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size))
                                          for base, size in ((PAYLOAD, 8192), (SCRATCH, 256)))

    def aliased(self, address, size):
        for source, target, count in self.aliases:
            if source <= address and address + size <= source + count:
                return target + address - source
        return address

    def read(self, address, size):
        return super().read(self.aliased(address, size), size)

    def write(self, address, value, size):
        return super().write(self.aliased(address, size), value, size)

    def source(self, address, size):
        address = self.aliased(address, size)
        if HEADER_BUFFER <= address and address + size <= HEADER_BUFFER + 40:
            return "header", address - HEADER_BUFFER
        if PAYLOAD <= address and address + size <= PAYLOAD + 8192:
            return "payload", address - PAYLOAD
        if self.append_frame is not None and address == self.append_frame + 220 and size == 16:
            return "append_record", 0
        raise ValueError("program source escaped reviewed buffers")

    def target(self, address, size):
        if SCRATCH <= address and address + size <= SCRATCH + 256:
            return "verify_payload", address - SCRATCH
        if self.append_frame is not None and address == self.append_frame + 204 and size == 16:
            return "append_readback", 0
        if size == 40 and address == self.value("sp"):
            return "verify_header", 0
        return super().target(address, size)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target in SERVICES:
                args = tuple(self.value(f"r{i}") if i < SERVICES[target] else 0 for i in range(3))
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else 0
            elif target == PROGRAM:
                if self.value("r0") != 0:
                    raise ValueError("unreviewed page program mode")
                source, count, address = (self.value(f"r{i}") for i in (1, 2, 3))
                label, offset = self.source(source, count)
                data = bytes(self.read(source + i, 1) for i in range(count))
                args = address, label, offset, data
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else count
            elif target in (RAW_READ, WRAPPED_READ):
                if target == RAW_READ:
                    destination, address, count = (self.value(f"r{i}") for i in range(3))
                else:
                    address, destination, count = (self.value(f"r{i}") for i in range(3))
                label, offset = self.target(destination, count)
                args = address, label, offset, count
                self.calls.append((target, args, self.snapshot()))
                if self.boundary is None:
                    raise ValueError("no synthetic read boundary")
                result, data = self.boundary(target, args, self)
                rejected = bool(result & 0x80000000) if target == RAW_READ else bool(result)
                if len(data) > count or (not rejected and len(data) != count):
                    raise ValueError("synthetic read violated buffer contract")
                for i, byte in enumerate(data):
                    self.write(destination + i, byte, 1)
            else:
                return super().single_step()
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif match := re.fullmatch(r"(r\d+) = umin\((r\d+), (r\d+)\)", text):
            self.set(match[1], min(self.value(match[2]), self.value(match[3])))
        elif match := re.fullmatch(r"(r\d+) = uextra\((r\d+), p:(\d+), l:(\d+)\)", text):
            self.set(match[1], (self.value(match[2]) >> int(match[3])) & ((1 << int(match[4])) - 1))
        elif match := re.fullmatch(r"if \(\((r\d+) & (r\d+|0x[0-9a-fA-F]+)\) (==|!=) 0\) goto (-?\d+)", text):
            zero = not (self.value(match[1]) & self.value(match[2]))
            if zero == (match[3] == "=="):
                next_pc += int(match[4])
        else:
            return super().single_step()
        self.pc = next_pc
        return True

    def run(self):
        if self.operation != "append":
            return super().run()
        while self.steps < 4000000:
            if self.pc in (0x0200AC36, 0x0200ACDE):
                if self.frames or self.returns or self.else_skips or self.value("sp") != self.append_frame:
                    raise ValueError("unbalanced append continuation")
                return {"memory": self.snapshot(), "calls": self.calls, "writes": self.writes,
                        "visited": self.visited, "steps": self.steps,
                        "result": int(self.pc == 0x0200ACDE),
                        "allocation": self.value("r0") if self.pc == 0x0200AC36 else None}
            self.steps += 1
            if not self.step():
                raise ValueError("append returned outside its continuation exits")
        raise ValueError("append instruction budget exceeded")
