"""Execute original capture preparation and DSP wrappers, with explicit parser/reset services."""
from __future__ import annotations
import re
from capture_container_machine import (CaptureContainerProgram, CaptureContainerMachine,
    ROOT, STATE, PREPARE, CLEANUP, PROBE, PROCESS_LOAD, CAPABILITIES, ALLOCATE, HEAP, CAPACITY, LOADER)
from pi32v2isa import codec, table

REGIONS = {
    "prepare": (PREPARE, 0x02002634), "cleanup": (CLEANUP, 0x0200268E),
    "probe": (PROBE, 0x01C04A8E), "size": (0x01C12850, 0x01C12878),
    "load": (PROCESS_LOAD, 0x01C04B34), "load_context": (0x01C1296C, 0x01C129CE),
    "capabilities": (CAPABILITIES, 0x01C04C42), "select_dot": (0x01C129CE, 0x01C129DC),
    "noop_a": (0x01C13082, 0x01C13084), "noop_b": (0x01C13084, 0x01C13086),
    "noop_c": (0x01C13086, 0x01C13088), "noop_d": (0x01C1308C, 0x01C1308E),
}
PARSER, RESET, DEFAULT_DOT = 0x02031C64, 0x01C12878, 0x01C12608
DSP, STATS, FORCE = 0x01C2BFF0, 0x01C340CC, 0x01C344A8
CONTEXT, OUTPUT, LAYERS, ARENA = DSP + 76, 0x31006000, 0x32030000, 0x32040000
EXTRA = ((STATE + 4128, 16), (DSP, 304), (STATS, 72), (FORCE, 4), (OUTPUT, 25), (LAYERS, 5120))
ARITIES = {"prepare": 1, "cleanup": 0, "probe": 2, "size": 2, "load": 4,
           "load_context": 4, "capabilities": 0, "select_dot": 1, "install": 3, "slot": 1}
LENGTHS = (272, 1860, None, 4, 2, 20, 48, 16, 256, 40, 1490, 1490, 16, 12, 4,
           4, 17, 8192, 8192, 8192, 8192, 16, 304, 72, 4, 25, 5120)


def image_offset(address):
    return (address - 0x02000120 if address >= 0x02000000 else
            0x02056780 - 0x02000120 + address - 0x01C00000)


class CaptureDispatchProgram(CaptureContainerProgram):
    def __init__(self):
        super().__init__()
        self.pre_dispatch_code, self.dispatch_regions = set(self.code), {}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        instructions = table.load()
        for name, (start, end) in REGIONS.items():
            self.dispatch_regions[name] = app[image_offset(start):image_offset(end)]
            pc = start
            while pc < end:
                decoded = codec.decode(instructions, app, image_offset(pc))
                if decoded is None:
                    raise ValueError(f"unsupported dispatch instruction at {pc:#x}")
                instruction, fields, size = decoded
                counts = [0, 0]
                if instruction.block:
                    for i, kind in enumerate(("then", "else")):
                        spec = instruction.fields[instruction.block[kind]]
                        counts[i] = fields[instruction.block[kind]] * spec.scale + spec.add
                if pc + size > end:
                    raise ValueError("instruction crosses a dispatch function boundary")
                self.code[pc] = codec.format(instruction, fields), size, *counts
                pc += size
        for pc in set(self.code) - self.pre_dispatch_code:
            text, size, _, _ = self.code[pc]
            if text.endswith("  #"):
                following, b_size, _, _ = self.code[pc + size]
                if not re.match(r"r\d+(?:_r\d+)? =", text) or b_size != 2 or "[" not in following:
                    raise ValueError("unreviewed dispatch instruction packet")
                self.parallel_seconds.add(pc + size)

    def execute(self, memory, operation, *arguments, reader=None, boundary=None, parser=None):
        if (len(memory) != len(LENGTHS) or any(len(memory[i]) != size for i, size in enumerate(LENGTHS) if size is not None)
                or not 0 <= memory[2] <= 255 or operation not in ARITIES or len(arguments) != ARITIES[operation]
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation == "install" and arguments[2] not in (0, LOADER))):
            raise ValueError("outside the dispatch verifier's call domain")
        return CaptureDispatchMachine(self, memory, operation, arguments, reader, boundary, parser).run()


class CaptureDispatchMachine(CaptureContainerMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary, parser):
        parent_operation = operation if operation in ("install", "slot") else "install"
        parent_arguments = arguments if operation in ("install", "slot") else (0, 0, 0)
        super().__init__(program, memory[:21], parent_operation, parent_arguments, reader, boundary)
        for (base, _), data in zip(EXTRA, memory[21:]):
            self.memory.update({base + i: byte for i, byte in enumerate(data)})
        self.parser = parser
        if operation in REGIONS:
            self.pc = REGIONS[operation][0]
            self.regs.update({f"r{i}": value for i, value in enumerate(list(arguments) + [0] * (4 - len(arguments)))})
        if operation == "load_context":
            self.regs.update(r0=CONTEXT, r1=arguments[0], r2=arguments[1], r3=arguments[2])
            for i, byte in enumerate(arguments[3].to_bytes(4, "little")):
                self.memory[self.value("sp") + i] = byte
        elif operation == "capabilities":
            self.regs.update(r0=OUTPUT, r1=OUTPUT + 17, r2=OUTPUT + 21)
        elif operation == "select_dot":
            self.regs.update(r0=CONTEXT, r1=arguments[0])

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(size)) for base, size in EXTRA)

    def step(self):
        if self.pc in self.else_skips:
            self.pc = self.else_skips.pop(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        pair = re.match(r"(r\d+_r\d+) =.*  #$", text)
        if not pair:
            return super().step()
        pc, before = self.pc, dict(self.regs)
        self.pc = pc + size
        if not self.single_step():
            raise ValueError("parallel B unexpectedly returned")
        after_b, end = dict(self.regs), self.pc
        self.regs, self.pc = dict(before), pc
        if not self.single_step():
            raise ValueError("parallel A unexpectedly returned")
        for name in pair[1].split("_"):
            after_b[name] = self.regs[name]
        self.regs, self.pc = after_b, end
        return True

    def single_step(self):
        self.visited.add(self.pc)
        text, size, _, _ = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        match = re.fullmatch(r"call (-?\d+)", text)
        if match:
            target = next_pc + int(match[1])
            if target in {start for start, _ in REGIONS.values()}:
                self.returns.append(next_pc)
                self.pc = target
                return True
            if target == PARSER:
                context, ledger_address, source, length = (self.value(f"r{i}") for i in range(4))
                query = context != CONTEXT
                if query and self.pc != 0x01C12866:
                    raise ValueError("unreviewed parser context")
                ledger = [self.read(ledger_address + 4 * i, 4) for i in range(3)]
                args = ("query" if query else CONTEXT, tuple(ledger), source, length)
                self.calls.append((PARSER, args, self.snapshot()))
                result = self.parser(args, ledger, self) if self.parser else 0
                for i, value in enumerate(ledger):
                    self.write(ledger_address + 4 * i, value, 4)
            elif target in (RESET, ALLOCATE):
                args = self.value("r0"), 0, 0, 0
                self.calls.append((target, args, self.snapshot()))
                result = self.boundary(target, args, self) if self.boundary else 0
                if target == ALLOCATE and self.pc == 0x020085C0:
                    if args[0] > CAPACITY or result not in (0, HEAP):
                        raise ValueError("unreviewed container allocation")
                    self.allocation_size = args[0] if result else 0
            else:
                return super().single_step()
            for register in ("r0", "r1", "r2", "r3"):
                self.set(register, 0xBAD0C0DE)
            self.set("r0", result)
        elif text == "[--sp] = rets":
            self.frames.append(({}, self.value("sp")))
            self.set("sp", self.value("sp") - 4)
        elif text == "pc = [sp++]":
            saved, sp = self.frames.pop()
            self.regs.update(saved, sp=sp)
            if not self.returns:
                return False
            next_pc = self.returns.pop()
        else:
            return super().single_step()
        self.pc = next_pc
        return True
