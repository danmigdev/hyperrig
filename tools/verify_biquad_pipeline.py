"""Compare generated coefficients, pending updates and numerical sample blocks."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from biquad_pipeline_machine import BiquadPipelineProgram, GETTER, STATIC
from biquad_generator_machine import MAPPED, REGIONS as MATH_REGIONS, PRIOR_REGIONS, ROOT, region_bytes
from biquad_chain_machine import ACTIVE, CLOCK, AVERAGE, TOTAL, BUFFER, REGIONS as CHAIN_REGIONS
from verify_biquad_generator import initial, SOURCES as GENERATOR_SOURCES
from verify_biquad_coefficients import Control, GuardedControl, Runtime, PINNED_IMAGE, MINI_IMAGE
from verify_biquad_chain import CState as ChainState, CLOCK_CALLBACK, IO

SOURCES = (*GENERATOR_SOURCES,
    "firmware/src/hyperrig_biquad.c", "firmware/src/hyperrig_biquad_chain.c",
    "firmware/include/hyperrig/hyperrig_biquad_pipeline.h", "firmware/src/hyperrig_biquad_pipeline.c",
    "tools/biquad_pipeline_machine.py", "tools/verify_biquad_pipeline.py", "tools/build_biquad_pipeline.py",
    "tests/test_biquad_pipeline_machine.py", "tests/biquad_pipeline_sanitize.c")


class Change(ctypes.Structure):
    _fields_ = [("section", ctypes.c_uint32), ("parameter", ctypes.c_int32)]


class CState(ChainState):
    def __init__(self, memory, samples):
        super().__init__(memory[:7], samples)
        control = Control.from_buffer_copy(bytes(memory[7]) + bytes(memory[8]) + b"\xC1\xD2\xE3")
        self.guarded_control = GuardedControl(0x12345678, control, 0x9ABCDEF0)
        self.control = self.guarded_control.control
        self.divisor = int.from_bytes(memory[9], "little")

    def snapshot(self):
        return super().snapshot() + (struct.pack("<I", self.control.requests),
                                    bytes(self.control.parameters), struct.pack("<I", self.divisor))

    def guards_ok(self):
        return (super().guards_ok() and (self.guarded_control.before, self.guarded_control.after) ==
                (0x12345678, 0x9ABCDEF0) and bytes(self.control.reserved) == b"\xC1\xD2\xE3")


def clocked(divisor=48077):
    memory = initial(divisor)
    memory[2][:] = struct.pack("<I", 1)
    return memory


DEFAULT_CLOCK = ((100, (), ()), (500, (), ()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing reports; use a new output file")
    if not __debug__:
        raise RuntimeError("run without Python optimization")
    library = ctypes.CDLL(str(args.library.resolve()))
    block = library.hyperrig_biquad_pipeline_block
    block.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(Control), ctypes.c_uint32,
                      ctypes.POINTER(Change), ctypes.c_uint32, ctypes.POINTER(ctypes.c_int32),
                      ctypes.c_uint32, ctypes.POINTER(IO)]
    block.restype = ctypes.c_int
    parameter = library.hyperrig_biquad_pipeline_parameter
    parameter.argtypes, parameter.restype = [ctypes.POINTER(Control), ctypes.c_uint32, ctypes.POINTER(ctypes.c_int32)], ctypes.c_int
    stage = library.hyperrig_biquad_generate_stage
    stage.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(Control), ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32]
    stage.restype = ctypes.c_int
    program, rng = BiquadPipelineProgram(), random.Random(0x2892051F0)
    coverage, digest = set(), hashlib.sha256()
    counts = {"parameter": 0, "block": 0}
    stage_calls = kernel_calls = clock_calls = samples_compared = carried_blocks = callback_requests = 0
    frame_lengths, variants = set(), set()

    def get(memory, index):
        state, value = CState(memory, []), ctypes.c_int32(0x76543210)
        expected = program.generator.parameter(memory, index)
        result = parameter(ctypes.byref(state.control), index, ctypes.byref(value))
        if result or value.value != expected["value"] or state.snapshot() != expected["memory"] or not state.guards_ok():
            raise AssertionError("parameter getter mismatch")
        coverage.update(expected["visited"])
        counts["parameter"] += 1
        digest.update(struct.pack("<Ii", index, value.value))

    def compare(memory, samples, changes=(), script=DEFAULT_CLOCK, carried=False):
        nonlocal stage_calls, kernel_calls, clock_calls, samples_compared, carried_blocks, callback_requests
        expected = program.execute(memory, samples, changes, script)
        state, events, errors, index = CState(memory, samples), [], [], 0
        array = (Change * (len(changes)+2))()
        array[0], array[-1] = Change(0x12345678, 0x11223344), Change(0x87654321, 0x55667788)
        for i, (section, value) in enumerate(changes):
            array[i+1] = Change(section, value)
        saved_array = bytes(array)
        change_pointer = ctypes.cast(ctypes.byref(array, ctypes.sizeof(Change)), ctypes.POINTER(Change)) if changes else None

        def callback(token_opaque, token):
            nonlocal index
            try:
                if index >= len(script):
                    raise AssertionError("unexpected C pipeline clock")
                clock, requests, writes = script[index]
                index += 1
                before, before_samples = state.snapshot(), state.sample_values()
                for section, value in requests:
                    result = stage(ctypes.byref(state.runtime), ctypes.byref(state.control), section, value, state.divisor)
                    assert result == (1 if section >= 5 else 0)
                for address, value, width in writes:
                    state.mutate(address, value, width)
                events.append((token, before, before_samples, state.snapshot(), state.sample_values()))
                return clock
            except Exception as error:
                errors.append(error)
                return 0

        clock = CLOCK_CALLBACK(callback)
        io = IO(clock, None)
        result = block(ctypes.byref(state.runtime), ctypes.byref(state.control), state.divisor,
                       change_pointer, len(changes), state.pointer if samples else None, len(samples),
                       ctypes.byref(io) if script else None)
        if errors:
            raise errors[0]
        if (result or state.snapshot() != expected["memory"] or state.sample_values() != expected["samples"]
                or events != expected["clocks"] or index != expected["consumed_clock_entries"]
                or bytes(array) != saved_array or not state.guards_ok()):
            raise AssertionError(f"pipeline mismatch: frames={len(samples)}, changes={changes}, divisor={state.divisor}")
        counts["block"] += 1
        coverage.update(expected["visited"])
        stage_calls += len(expected["stages"])
        kernel_calls += len(expected["kernel_calls"])
        clock_calls += len(events)
        callback_requests += sum(origin == "clock" for origin, _, _ in expected["stages"])
        carried_blocks += int(carried)
        samples_compared += len(samples)
        frame_lengths.add(len(samples))
        variants.update((kind, section) for kind, section, _ in expected["kernel_calls"])
        digest.update(json.dumps((changes, samples, expected["samples"]), separators=(",", ":")).encode())
        for part in state.snapshot():
            digest.update(part)
        return tuple(bytearray(part) for part in state.snapshot())

    for section in range(5):
        for value in range(256):
            memory = initial(48077)
            memory[8][section] = value
            get(memory, section)
    for section in (5, 6, 255, 256, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        get(initial(), section)

    for section in range(5):
        for value in range(-12, 13):
            compare(clocked(), [1 << 28, 0, -1, 0, 1, -10000, 10000, 0], [(section, value)])
    for frames in range(129):
        samples = [rng.randint(-(1 << 30), (1 << 30)-1) for _ in range(frames)]
        compare(clocked(), samples, [(i, (i+1)*2 if i % 2 else -(i+1)*2) for i in range(5)])
    for mask in range(32):
        changes = [(i, (i+1) if mask & (1 << i) else 0) for i in range(5)]
        compare(clocked(), [0x7FFFFFFF, -0x80000000, 0, 1, -1]*3, changes)
    for divisor in (0, 1, 8000, 44100, 48000, 48077, 96000, 0xFFFFFFFF):
        memory = clocked(divisor)
        for i in range(5):
            struct.pack_into("<4iI", memory[1], 44*i+20, 0x7FFFFFFF, -0x80000000,
                             0x7FFFFFFF, -0x80000000, 0xFFFFFFFF)
        compare(memory, [0x7FFFFFFF, -0x80000000, 0, 1, -1]*5, [(i, 12 if i % 2 else -12) for i in range(5)])

    memory = compare(clocked(), [100000, -100000, 0], [(i, 6) for i in range(5)])
    for changes in ([(0, -12), (0, 12), (0, 0)], [(0, 0x7FFFFFFF), (1, -0x80000000)],
                    [(5, 1), (0xFFFFFFFF, -1)], [(i % 5, i-8) for i in range(16)]):
        memory = compare(memory, [1000000, 0, -1000000, 0], changes, carried=True)
    for i in range(75):
        changes = [(rng.randrange(7), rng.randrange(-20, 21)) for _ in range(rng.randrange(6))]
        frames = rng.randrange(33)
        samples = [rng.randint(-0x80000000, 0x7FFFFFFF) for _ in range(frames)]
        script = (((0xFFFFFF00 + i*17) & 0xFFFFFFFF, (), ()),
                  ((0xFFFFFF30 + i*19) & 0xFFFFFFFF, (), ()))
        memory = compare(memory, samples, changes, script, carried=True)

    # Synchronous clock-boundary requests must wait for a later active update.
    memory = compare(clocked(), [1 << 26, 0, 0], [(0, 6), (1, -6)])
    for at_end in (False, True):
        for section in range(5):
            action = ((1000, ((section, -12),), ()), (1600, (), ()))
            if at_end:
                action = ((1000, (), ()), (1600, ((section, 12),), ()))
            memory = compare(memory, [1000000, 0, 0, 0], (), action, carried=True)
            assert memory[5][section] == 1
            memory = compare(memory, [0, 0, 0, 0], (), DEFAULT_CLOCK, carried=True)
            assert not any(memory[5])

    # Stress the previously defined clock mutation boundary with real generated
    # coefficients. These flag mutations are test scripts, not observed firmware
    # behavior. They cover both numeric kernel calls at every caller position.
    for residual in (0, 1):
        writes = tuple((ACTIVE+44*i+41, residual, 1) for i in range(5))
        compare(clocked(), [0x7FFFFFFF, -0x80000000, 1, -1]*4, [(i, 12) for i in range(5)],
                ((100, (), writes), (500, (), ())))
    seeded = compare(clocked(), [100000, 0], [(i, 6) for i in range(5)])
    for previous, elapsed in ((0, 100), (100, 101), (100, 104), (100, 99), (100, 96), (100, 100),
                              (0xFFFFFFFF, 1), (1, 0xFFFFFFFF)):
        compare(seeded, [0, 0], (), ((0, (), ()), (elapsed, (), ((AVERAGE, previous, 4),))))
    compare(seeded, [1, -1], (), ((100, ((0, -6),), ((CLOCK, 0, 4),)),))
    compare(seeded, [1, -1], (), ((100, (), ((CLOCK, 7, 4),)), (500, ((1, 3),), ((TOTAL, 0xFFFFFFFF, 4),))))
    compare(initial(48077), [], (), ())
    compare(initial(48077), [1, 2], [(0, 0)], ())
    compare(initial(48077), [1, 2], [(0, 6)], ())

    state, invalid_count = CState(clocked(), [1, 2]), 0
    one_change = Change(0, 6)
    value = ctypes.c_int32(0x12345678)
    callback = CLOCK_CALLBACK(lambda *_: 0)
    io, empty_io = IO(callback, None), IO()
    before, before_samples = state.snapshot(), state.sample_values()
    attempts = [lambda: parameter(None, 0, ctypes.byref(value)),
                lambda: parameter(ctypes.byref(state.control), 0, None),
                lambda: block(None, ctypes.byref(state.control), 48077, None, 0, None, 0, ctypes.byref(io)),
                lambda: block(ctypes.byref(state.runtime), None, 48077, None, 0, None, 0, ctypes.byref(io)),
                lambda: block(ctypes.byref(state.runtime), ctypes.byref(state.control), 48077, ctypes.byref(one_change), 17, None, 0, ctypes.byref(io)),
                lambda: block(ctypes.byref(state.runtime), ctypes.byref(state.control), 48077, None, 1, None, 0, ctypes.byref(io)),
                lambda: block(ctypes.byref(state.runtime), ctypes.byref(state.control), 48077, ctypes.byref(one_change), 1, state.pointer, 129, ctypes.byref(io)),
                lambda: block(ctypes.byref(state.runtime), ctypes.byref(state.control), 48077, ctypes.byref(one_change), 1, None, 1, ctypes.byref(io)),
                lambda: block(ctypes.byref(state.runtime), ctypes.byref(state.control), 48077, ctypes.byref(one_change), 1, state.pointer, 2, None),
                lambda: block(ctypes.byref(state.runtime), ctypes.byref(state.control), 48077, ctypes.byref(one_change), 1, state.pointer, 2, ctypes.byref(empty_io))]
    for attempt in attempts:
        assert attempt() == -1 and state.snapshot() == before and state.sample_values() == before_samples
        assert value.value == 0x12345678 and state.guards_ok()
        invalid_count += 1
    # Only the seven getter instructions are new; integration reuses prior bytes.
    new_code = {pc for pc in program.code if GETTER[0] <= pc < GETTER[1]}
    if not new_code <= coverage:
        raise AssertionError("parameter getter did not receive full instruction coverage")

    all_regions = {**PRIOR_REGIONS, **MATH_REGIONS, **CHAIN_REGIONS,
                   **{name: (body.start, body.end) for name, body in program.chain.kernels.items()},
                   "parameter": GETTER}
    app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
    region_report = {name: {"start": f"0x{start:08x}", "end_exclusive": f"0x{end:08x}",
                           "sha256": hashlib.sha256(region_bytes(app, start, end)).hexdigest(),
                           "decoded": sum(start <= pc < end for pc in program.code),
                           "visited": sum(start <= pc < end for pc in coverage)}
                     for name, (start, end) in all_regions.items()}
    static = {name: {"start": f"0x{start:08x}", "end_exclusive": f"0x{end:08x}",
                     "sha256": hashlib.sha256(program.static[name]).hexdigest(), "executed": False}
              for name, (start, end) in STATIC.items()}
    mini_check = None
    if args.mini_image:
        raw = args.mini_image.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == MINI_IMAGE
        from hyperrig.jieli import unpack_app
        mini = unpack_app(raw)[2]["app.bin"]
        for name, bounds in {**all_regions, **STATIC}.items():
            assert region_bytes(mini, *bounds) == region_bytes(app, *bounds), name
        assert region_bytes(mini, 0x0203A55C, 0x0203A566) == program.generator.table
        mini_check = {"sha256": MINI_IMAGE, "executed_regions_identical": list(all_regions),
                      "static_windows_identical": list(STATIC), "table_identical": True}
    report = {"result": "pass", "device_access": False, "hardware_test": False, "audio_test": False,
        "original_image_sha256": PINNED_IMAGE, "mini_image": mini_check,
        "comparisons": counts, "total_comparisons": sum(counts.values()),
        "new_instructions_decoded": len(new_code), "new_instructions_visited": len(new_code & coverage),
        "combined_instructions_decoded": len(program.code), "combined_instructions_visited": len(coverage),
        "unvisited_inherited_instructions": [f"0x{pc:08x}" for pc in sorted(set(program.code)-coverage)],
        "staging_calls": stage_calls, "numerical_kernel_calls": kernel_calls, "clock_calls": clock_calls,
        "samples_compared": samples_compared, "carried_blocks": carried_blocks,
        "requests_inside_clock_callbacks": callback_requests, "frame_lengths": sorted(frame_lengths),
        "kernel_variants_and_positions": sorted(variants), "invalid_api_checks": invalid_count,
        "divisor_evidence": {"reset_word": 48000, "startup_argument": 48077,
                             "writer_address": "0x0202911a", "initializer_call": "0x0200250a",
                             "physical_unit_validated": False, "writer_scan_exhaustive": False},
        "regions": region_report, "static_evidence": static, "outputs_and_state_sha256": digest.hexdigest(),
        "sources_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "boundaries": ["batch orchestration is a new adapter over separate original entry points",
                       "all coefficient math and both numerical kernels execute decoded original instructions",
                       "clock service and its synchronous test mutations remain scripted",
                       "global initializer/caller windows are static evidence, not executed initialization",
                       "no physical rate, audio device, full firmware, timing or stability validation"]}
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(f"Pipeline: {sum(counts.values())} comparisons, {samples_compared} samples, {stage_calls} staged requests, "
          f"{kernel_calls} kernel calls; instructions {len(coverage)}/{len(program.code)}.")


if __name__ == "__main__":
    main()
