"""Compose original request/getter/chain entries with carried state and samples.

The orchestration is a new verifier adapter. No single native batch function is
invented. Each constituent original function executes decoded instructions;
only the existing indirect clock service is scripted.
"""
from __future__ import annotations

import struct

from biquad_generator_machine import (BiquadGeneratorProgram, BiquadGeneratorMachine,
    MAPPED, ROOT, DIVISOR, region_bytes)
from biquad_chain_machine import (BiquadChainProgram, BiquadChainMachine, MAPPED as CHAIN_MAPPED,
    BUFFER, CLOCK)
from dot_machine import NativeProgram, DotMachine, signed

GETTER = (0x02028920, 0x02028936)
STATIC = {
    "divisor_reset_word": (0x01C1F7F8, 0x01C1F7FC),
    "startup_call_window": (0x020024EC, 0x02002510),
    "global_initializer": (0x02029112, 0x020291F8),
    "block_caller_window": (0x01C026CE, 0x01C026E4),
}


class GetterRegion(NativeProgram):
    REGIONS = {"parameter": GETTER}


class PipelineGeneratorProgram(BiquadGeneratorProgram):
    def __init__(self):
        super().__init__()
        getter = GetterRegion("parameter")
        self.getter_raw = getter.raw
        self.code.update(getter.code)

    def parameter(self, memory, section):
        if tuple(map(len, memory)) != tuple(size for _, size in MAPPED) or not 0 <= section <= 0xFFFFFFFF:
            raise ValueError("outside the parameter-getter domain")
        machine = BiquadGeneratorMachine(self, memory, "exp", 0, 0, None)
        machine.pc, machine.regs["r0"] = GETTER[0], section
        result = machine.run()
        result["value"] = signed(result["value"])
        return result


class BiquadPipelineProgram:
    def __init__(self):
        self.generator, self.chain = PipelineGeneratorProgram(), BiquadChainProgram()
        overlap = set(self.generator.code) & set(self.chain.code)
        if overlap:
            raise ValueError("unexpected overlapping pipeline function regions")
        self.code = {**self.generator.code, **self.chain.code}
        app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
        self.static = {name: region_bytes(app, *bounds) for name, bounds in STATIC.items()}
        if struct.unpack("<I", self.static["divisor_reset_word"])[0] != 48000:
            raise ValueError("unexpected reset-copy divisor")

    def execute(self, memory, samples, changes=(), script=()):
        if (tuple(map(len, memory)) != tuple(size for _, size in MAPPED) or len(samples) > 128
                or len(changes) > 16 or any(not -(1 << 31) <= value < (1 << 31) for value in samples)
                or any(len(change) != 2 or not 0 <= change[0] <= 0xFFFFFFFF
                       or not -(1 << 31) <= change[1] < (1 << 31) for change in changes)
                or (int.from_bytes(memory[2], "little") and not script)):
            raise ValueError("outside the filter pipeline verifier domain")
        state = tuple(bytes(part) for part in memory)
        coverage, stage_events, clocks = set(), [], []
        math_calls, normalization_calls, steps = [], [], 0

        def request(current, change, origin):
            nonlocal steps
            section, parameter = change
            result = self.generator.execute(current, "stage", section=section, value=parameter & 0xFFFFFFFF)
            coverage.update(result["visited"])
            math_calls.extend(result["math_calls"])
            normalization_calls.extend(result["normalization_calls"])
            steps += result["steps"]
            stage_events.append((origin, change, result["memory"]))
            return result["memory"]

        for change in changes:
            state = request(state, change, "before_block")
        after_requests = state
        extras = state[len(CHAIN_MAPPED):]
        script_index = 0

        def clock(token, machine):
            nonlocal extras, script_index
            if script_index >= len(script):
                raise ValueError("unexpected pipeline clock call")
            value, requests, writes = script[script_index]
            script_index += 1
            before = machine.snapshot() + extras
            before_samples = machine.sample_values()
            current = before
            for change in requests:
                current = request(current, change, "clock")
            for (base, _), part in zip(CHAIN_MAPPED, current[:len(CHAIN_MAPPED)]):
                machine.memory.update({base+i: byte for i, byte in enumerate(part)})
            extras = current[len(CHAIN_MAPPED):]
            for address, word, width in writes:
                machine.mutate(address, word, width)
            clocks.append((token, before, before_samples, machine.snapshot()+extras, machine.sample_values()))
            return value

        processed = self.chain.execute(state[:len(CHAIN_MAPPED)], samples, clock=clock if script else None)
        coverage.update(processed["visited"])
        steps += processed["steps"]
        return {"memory": processed["memory"] + extras, "samples": processed["samples"],
                "after_requests": after_requests, "stages": stage_events, "clocks": clocks,
                "kernel_calls": processed["kernel_calls"], "math_calls": math_calls,
                "normalization_calls": normalization_calls, "visited": coverage, "steps": steps,
                "consumed_clock_entries": script_index}
