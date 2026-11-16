"""Carry original native loading state directly into original block processing."""
from __future__ import annotations
import re
from capture_native_machine import (CaptureNativeProgram, CaptureNativeMachine,
    OPERATIONS, LENGTHS, ARITIES, ARENA_BYTES, LOADER, ROOT)
from capture_dispatch_machine import CONTEXT, STATS, FORCE
from capture_processing_machine import (CaptureProcessingProgram, CaptureProcessingMachine,
    REGIONS as PROCESSING_REGIONS, KERNELS, SCRATCH, SCRATCH_BYTES)
from capture_warmup_machine import CaptureWarmupProgram, WARMUP, RESET

INPUT, OUTPUT, SAMPLE_BYTES = 0x36000000, 0x36010000, 4096
# Preserve the single native storage for statistics and the force word inside
# the larger processing scratch address span. No duplicated/translated state.
EXTRA = ((SCRATCH, STATS - SCRATCH), (STATS + 72, FORCE - STATS - 72),
         (FORCE + 4, SCRATCH + SCRATCH_BYTES - FORCE - 4),
         (INPUT, SAMPLE_BYTES), (OUTPUT, SAMPLE_BYTES))
LIVE_LENGTHS = LENGTHS + (ARENA_BYTES, 4) + tuple(n for _, n in EXTRA)


class CaptureLiveProgram:
    def __init__(self):
        self.native = CaptureNativeProgram()
        self.processing = CaptureProcessingProgram()
        self.warmup = CaptureWarmupProgram()
        self.code = self.native.code | self.warmup.code
        for pc in self.native.code.keys() & self.warmup.code.keys():
            if self.native.code[pc] != self.warmup.code[pc]:
                raise ValueError("inconsistent inherited instruction decoding")

    def execute(self, memory, operation, *arguments, reader=None, boundary=None):
        arity = {"process": 3, "head_kernel": 1, "warmup": 1}.get(operation, ARITIES.get(operation))
        if (operation not in (*OPERATIONS, "process", "head_kernel", "warmup") or len(arguments) != arity
                or len(memory) != len(LIVE_LENGTHS)
                or any(len(memory[i]) != n for i, n in enumerate(LIVE_LENGTHS) if n is not None)
                or not 0 <= memory[2] <= 255
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)
                or (operation == "install" and arguments[2] not in (0, LOADER))):
            raise ValueError("outside the live capture comparison domain")
        if operation in ("process", "head_kernel"):
            return LiveProcessingMachine(self, memory, operation, arguments).run()
        if operation == "warmup":
            return LiveWarmupMachine(self, memory, arguments[0]).run()
        return LiveNativeMachine(self.native, memory, operation, arguments, reader, boundary).run()


class LiveNativeMachine(CaptureNativeMachine):
    def __init__(self, program, memory, operation, arguments, reader, boundary):
        super().__init__(program, memory[:29], operation, arguments, reader, boundary)
        for (base, _), data in zip(EXTRA, memory[29:]):
            if any(base + i in self.memory for i in range(len(data))):
                raise ValueError("overlapping live capture memory regions")
            self.memory.update({base + i: byte for i, byte in enumerate(data)})

    def snapshot(self):
        return super().snapshot() + tuple(bytes(self.memory[base + i] for i in range(n)) for base, n in EXTRA)


class LiveProcessingMachine(CaptureProcessingMachine):
    def __init__(self, program, memory, operation, arguments):
        # Bootstrap only the exact address map. No loading operation is run and
        # no context, pointer or sample is converted before original processing.
        view = LiveNativeMachine(program.native, memory, "size", (0, 0), None, None)
        self.__dict__.update(view.__dict__)
        self.view, self.program, self.kernel = view, program.processing, None
        if operation == "process":
            self.regs.update(r0=CONTEXT, r1=arguments[0], r2=arguments[1], r3=arguments[2])
            self.pc = PROCESSING_REGIONS["process"][0]
        else:
            self.regs.update(r0=arguments[0], r1=0, r2=0, r3=0)
            self.pc = KERNELS["head3"][0]

    def snapshot(self):
        return self.view.snapshot()

    def read(self, address, size):
        self.view.regs = self.regs
        return self.view.read(address, size)

    def write(self, address, value, size):
        # The view shares the same byte map; retain immutable-source/allocation
        # guards while using the numerical machine's instruction semantics.
        self.view.pc = self.pc
        self.view.regs = self.regs
        return self.view.write(address, value, size)

    def run(self):
        result = super().run()
        result.update(result=0, parser_entries=[], reset_entries=0, reset_words=0)
        return result


class LiveWarmupMachine(LiveProcessingMachine):
    def __init__(self, program, memory, output):
        super().__init__(program, memory, "process", (0, 0, 0))
        self.program, self.pc = program.warmup, WARMUP
        self.regs.update(r0=CONTEXT, r1=output, r2=0, r3=0)
        self.reset_entries = 0

    def single_step(self):
        text, size, _, _ = self.program.code[self.pc]
        if match := re.fullmatch(r"call (-?\d+)", text):
            if self.pc + size + int(match[1]) == RESET:
                if self.value("r0") != CONTEXT:
                    raise ValueError("unreviewed live reset context")
                self.visited.add(self.pc)
                self.returns.append(self.pc + size)
                self.pc = RESET
                self.reset_entries += 1
                return True
        return super().single_step()

    def run(self):
        result = super().run()
        result.update(result=self.value("r0"), reset_entries=self.reset_entries, reset_words=self.view.reset_words)
        return result
