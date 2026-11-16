"""Execute capture journal/cache instructions; physical reads remain scripted."""
from __future__ import annotations
import re

from preset_assets_machine import PresetAssetsProgram, PresetAssetsMachine, ROOT, HEADER_BUFFER, PAYLOAD_BUFFER
from dot_machine import DotMachine
from pi32v2isa import codec, table

REGIONS = {"capacity": (0x02007CBA, 0x02007CE0), "scan": (0x02007CE0, 0x02007DBE),
           "lookup": (0x02007DBE, 0x02007E62), "erased": (0x020034DA, 0x020034F2),
           "crc": (0x020034F2, 0x02003502), "read_adapter": (0x0200A878, 0x0200A888)}
CACHE, DETAILS, CONTEXT = 0x01C2422C, 0x31005000, 0x31006000
ARITIES = {"capacity": 1, "scan": 2, "lookup": 3, "erased": 1, "crc": 1}


class CaptureMetadataProgram(PresetAssetsProgram):
    def __init__(self):
        super().__init__()
        self.pre_metadata_code, self.metadata_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.metadata_regions[name] = app[start - 0x02000120:end - 0x02000120]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, pc - 0x02000120)
                if decoded is None:
                    raise ValueError(f"unsupported capture metadata instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a metadata function boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_metadata_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+ (?:=|\+=)", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed metadata instruction packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, reader=None):
        if (len(memory) != 17 or tuple(len(value) for i, value in enumerate(memory) if i != 2)
                != (272, 1860, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4, 300, 16)
                or not 0 <= memory[2] <= 255 or operation not in ARITIES
                or len(arguments) != ARITIES[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation in ("erased", "crc") and arguments[0] > 256)
                or (operation == "lookup" and arguments[2] not in (0, 1))):
            raise ValueError("outside the capture metadata call domain")
        return CaptureMetadataMachine(self, memory, operation, arguments, reader).run()


class CaptureMetadataMachine(PresetAssetsMachine):
    def __init__(self, program, memory, operation, arguments, reader):
        super().__init__(program, memory[:15], "mode", (), reader)
        for base, data in ((CACHE, memory[15]), (DETAILS, memory[16])):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.pc = REGIONS[operation][0]
        self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments)))})
        if operation in ("erased", "crc"):
            self.regs.update(r0=PAYLOAD_BUFFER, r1=arguments[0])
        elif operation == "scan":
            for i, value in enumerate((REGIONS["read_adapter"][0], 0x0200A868, CONTEXT + 12, arguments[0])):
                DotMachine.write(self, CONTEXT + 4*i, value, 4)
            self.regs.update(r0=CONTEXT, r1=HEADER_BUFFER, r2=arguments[1], r3=DETAILS)
        elif operation == "lookup":
            self.regs.update(r0=arguments[0], r1=HEADER_BUFFER, r2=arguments[1], r3=DETAILS if arguments[2] else 0)

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size))
                                          for base, size in ((CACHE, 300), (DETAILS, 16)))

    def target(self, address, size):
        # The scanner's 256-byte local chunk begins at sp+20; the read adapter
        # has pushed one return word while reaching the physical read boundary.
        if address == self.value("sp") + 24 and 0 < size <= 256 and size % 16 == 0:
            return "journal_chunk", 0
        return super().target(address, size)

    def address(self, expression):
        if match := re.fullmatch(r"\+\+(r\d+)=(r\d+)", expression):
            self.set(match[1], self.value(match[1]) + self.value(match[2]))
            return self.value(match[1])
        return super().address(expression)

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if text == "call r6" and self.pc == 0x02007D3E:
            target = self.value("r6")
            if target != REGIONS["read_adapter"][0]:
                raise ValueError("unreviewed journal read callback")
            self.returns.append(next_pc)
            next_pc = target
        elif text == "[r4+] = {r8, r0}" and self.pc == 0x02007D94:
            # Confirmed stm.post1 ordering: lower register at lower address,
            # with no base writeback.
            address = self.value("r4")
            self.write(address, self.value("r0"), 4)
            self.write(address + 4, self.value("r8"), 4)
        elif match := re.fullmatch(r"(r\d+) = ~(r\d+)", text):
            self.set(match[1], ~self.value(match[2]))
        elif self.pc in (0x02007D50, 0x02007D58):
            expected = {0x02007D50: ("r3 = b[r1++=1] (u)", "b[r0++=1] = r3"),
                        0x02007D58: ("r1 = b[r0++=1] (u)", "b[r2++=1] = r1")}
            if text != "rep 4 8 {" or tuple(self.program.code[next_pc + 2*i][0] for i in range(2)) != expected[self.pc]:
                raise ValueError("unreviewed journal REP body")
            for _ in range(8):
                self.pc = next_pc
                for _ in range(2):
                    if not self.step():
                        raise ValueError("unexpected return inside journal REP")
                    self.steps += 1
            next_pc += 4
        else:
            return super().single_step()
        self.pc = next_pc
        return True
