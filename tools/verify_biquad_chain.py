"""Compare the complete five-section caller with original instructions and kernels."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct

from biquad_chain_machine import (BiquadChainProgram, REGIONS, ROOT, MAPPED, STAGED, ACTIVE,
    CLOCK, AVERAGE, TOTAL, PENDING, ACTIVITY, BUFFER)
from verify_biquad import State, ram_bytes

PINNED_IMAGE = "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
MINI_IMAGE = "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
SOURCES = (
    "firmware/src/hyperrig_biquad.c", "firmware/include/hyperrig/hyperrig_biquad.h",
    "firmware/src/hyperrig_biquad_chain.c", "firmware/include/hyperrig/hyperrig_biquad_chain.h",
    "tools/biquad_machine.py", "tools/biquad_chain_machine.py", "tools/verify_biquad.py",
    "tools/verify_biquad_chain.py", "tools/build_biquad_chain.py", "tools/dot_machine.py",
    "tests/test_biquad_chain_machine.py", "tests/biquad_chain_sanitize.c",
    "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
    "upstream/pi32v2-isa/isa/pi32v2.toml", "research/input-manifest.json",
)


class Section(ctypes.Structure):
    _fields_ = [("filter", State), ("enabled", ctypes.c_uint8), ("residual", ctypes.c_uint8),
                ("reserved", ctypes.c_uint8 * 2)]


class Runtime(ctypes.Structure):
    _fields_ = [("staged", Section * 5), ("active", Section * 5),
                ("clock_token", ctypes.c_uint32), ("elapsed_average", ctypes.c_uint32),
                ("elapsed_total", ctypes.c_uint32), ("pending", ctypes.c_uint8 * 5),
                ("activity", ctypes.c_uint8), ("reserved", ctypes.c_uint8 * 2)]


class GuardedRuntime(ctypes.Structure):
    _fields_ = [("before", ctypes.c_uint32), ("runtime", Runtime), ("after", ctypes.c_uint32)]


CLOCK_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32)


class IO(ctypes.Structure):
    _fields_ = [("clock", CLOCK_CALLBACK), ("opaque", ctypes.c_void_p)]


def baseline():
    sections = bytearray()
    for i in range(5):
        sections.extend(struct.pack("<9iIBBBB", 1 << 28, 0, 0, 0, 0,
                                    i+1, i+2, i+3, i+4, 0x12345678+i, 0, 0, 0xAB, 0xCD))
    staged = bytearray(sections)
    for i in range(5):
        struct.pack_into("<i", staged, i*44, 1 << 27)
    return (staged, sections, bytearray(4), bytearray(struct.pack("<I", 100)),
            bytearray(struct.pack("<I", 0xFFFFFFF0)), bytearray(5), bytearray([0xA5]))


class Clock:
    def __init__(self, script=((100, ()), (500, ()))):
        self.script, self.index = script, 0

    def call(self, _token, view):
        if self.index >= len(self.script):
            raise ValueError("unexpected clock call")
        result, writes = self.script[self.index]
        self.index += 1
        for address, value, width in writes:
            view.mutate(address, value, width)
        return result


class CState:
    def __init__(self, memory, samples):
        runtime = Runtime.from_buffer_copy(b"".join(memory) + b"\xE6\xF7")
        self.guarded = GuardedRuntime(0x12345678, runtime, 0x89ABCDEF)
        self.runtime = self.guarded.runtime
        self.samples = (ctypes.c_int32 * (len(samples)+2))(0x55667788, *samples, 0x11223344)
        self.count = len(samples)
        self.pointer = ctypes.cast(ctypes.byref(self.samples, 4), ctypes.POINTER(ctypes.c_int32))
        self.parts = [(base, size, ctypes.addressof(self.runtime) + offset)
                      for (base, size), offset in zip(MAPPED, (0, 220, 440, 444, 448, 452, 457))]
        self.parts.append((BUFFER, len(samples)*4, ctypes.addressof(self.samples)+4))

    def snapshot(self):
        return tuple(ctypes.string_at(pointer, size) for _, size, pointer in self.parts[:-1])

    def sample_values(self):
        return list(self.samples)[1:-1]

    def mutate(self, address, value, size):
        for base, length, pointer in self.parts:
            if base <= address and address + size <= base + length:
                ctypes.memmove(pointer + address-base, (value & ((1 << (size*8))-1)).to_bytes(size, "little"), size)
                return
        raise ValueError("C clock mutation escaped chain/sample memory")

    def guards_ok(self):
        return ((self.guarded.before, self.guarded.after, self.samples[0], self.samples[-1]) ==
                (0x12345678, 0x89ABCDEF, 0x55667788, 0x11223344) and bytes(self.runtime.reserved) == b"\xE6\xF7")


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
    original = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
    if hashlib.sha256(original.read_bytes()).hexdigest() != PINNED_IMAGE:
        raise ValueError("unreviewed original image")
    library = ctypes.CDLL(str(args.library.resolve()))
    update = library.hyperrig_biquad_chain_update
    update.argtypes, update.restype = [ctypes.POINTER(Runtime), ctypes.c_uint], ctypes.c_int
    process = library.hyperrig_biquad_chain_process
    process.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32, ctypes.POINTER(IO)]
    process.restype = ctypes.c_int
    program, rng = BiquadChainProgram(), random.Random(0x51A251F0)
    counts, coverage, filter_calls = {"update": 0, "process": 0}, set(), set()
    mutated, sequences = 0, 0
    digest = hashlib.sha256()

    def compare(memory, samples, operation="process", section=0, script=((100, ()), (500, ())), sequence=False):
        nonlocal mutated, sequences
        native_clock, c_clock = Clock(script), Clock(script)
        expected = program.execute(memory, samples, operation, section, native_clock.call)
        state, calls, errors = CState(memory, samples), [], []
        def callback(_opaque, token):
            try:
                calls.append((token, state.snapshot(), state.sample_values()))
                return c_clock.call(token, state)
            except Exception as error:
                errors.append(error)
                return 0
        clock = CLOCK_CALLBACK(callback)
        io = IO(clock, None)
        if operation == "update":
            result = update(ctypes.byref(state.runtime), section)
        else:
            result = process(ctypes.byref(state.runtime), state.pointer, len(samples), ctypes.byref(io))
        if errors:
            raise errors[0]
        if (result != 0 or state.snapshot() != expected["memory"] or state.sample_values() != expected["samples"]
                or calls != expected["calls"] or not state.guards_ok()):
            changed = [i for i, (a, b) in enumerate(zip(state.snapshot(), expected["memory"])) if a != b]
            raise AssertionError((operation, section, len(samples), result, changed, calls == expected["calls"],
                                  state.sample_values()[:8], expected["samples"][:8]))
        counts[operation] += 1
        coverage.update(expected["visited"])
        filter_calls.update((mode, index) for mode, index, _ in expected["kernel_calls"])
        mutated += any(writes for _, writes in script)
        sequences += sequence
        digest.update(b"".join(expected["memory"]))
        digest.update(struct.pack("<" + "i"*len(samples), *expected["samples"]))
        return expected

    # Every byte flag value is admitted; updates must preserve history/residue.
    for section in range(5):
        for flag in range(256):
            memory = baseline()
            memory[0][:] = rng.randbytes(220)
            memory[0][section*44+40:section*44+42] = bytes((flag, 255-flag))
            memory[1][:] = rng.randbytes(220)
            memory[5][section] = flag
            compare(memory, [1, -2, 3], "update", section)
    print("Section update comparisons passed.", flush=True)
    # All 3^5 effective section configurations: disabled, rounded, residual.
    for modes in itertools.product(range(3), repeat=5):
        for length in (0, 1, 7):
            memory = baseline()
            for i, mode in enumerate(modes):
                memory[1][i*44+40:i*44+42] = bytes((int(mode != 0), int(mode == 2)))
            struct.pack_into("<I", memory[2], 0, 0x12345678)
            compare(memory, [1, -3, 5, -(1 << 31), (1 << 31)-1, 17, -19][:length])
    for pending in range(32):
        memory = baseline()
        for i in range(5):
            memory[5][i] = 255 if pending & (1 << i) else 0
            memory[0][i*44+40:i*44+42] = bytes((1, i % 2))
            memory[1][i*44+40:i*44+42] = bytes((1, 1-i % 2))
        struct.pack_into("<I", memory[2], 0, 0x12345678)
        compare(memory, [-7, 9, -11])
    for length in range(129):
        memory = baseline()
        for i in range(5):
            memory[1][i*44:i*44+40] = rng.randbytes(40)
            memory[1][i*44+40:i*44+42] = bytes((255, i % 2))
        compare(memory, [rng.randrange(-(1 << 31), 1 << 31) for _ in range(length)])
    print("Full chain configurations, pending masks and all block lengths passed.", flush=True)
    for previous in (0, 1, 100, 0x80000000, 0xFFFFFFFF):
        for start in (0, 100, 0xFFFFFFF0):
            for elapsed in (0, 1, 99, 100, 101, 0x80000000, 0xFFFFFFFF):
                memory = baseline()
                memory[1][40] = 1
                struct.pack_into("<I", memory[2], 0, 0x12345678)
                struct.pack_into("<I", memory[3], 0, previous)
                compare(memory, [], script=((start, ()), ((start+elapsed) & 0xFFFFFFFF, ())))
    mutations = [((CLOCK, 0, 4),), ((CLOCK, 0x87654321, 4),), ((ACTIVE+40, 0, 1),),
                 ((ACTIVE+41, 255, 1),), ((ACTIVE, 1 << 27, 4),), ((ACTIVE+20, 0xFFFFFFFF, 4),),
                 ((ACTIVE+36, 0xFFFFFFFF, 4),), ((ACTIVE+84, 1, 1),), ((PENDING+2, 255, 1),),
                 ((AVERAGE, 777, 4),), ((TOTAL, 0xFFFFFFF0, 4),), ((BUFFER, 12345, 4),),
                 ((ACTIVITY, 77, 1),)]
    for event in (0, 1):
        for changes in mutations:
            memory = baseline()
            memory[1][40] = 1
            struct.pack_into("<I", memory[2], 0, 0x12345678)
            script = [(100, ()), (500, ())]
            script[event] = (script[event][0], changes)
            compare(memory, [1, -2, 3], script=script)
    for trial in range(24):
        memory = baseline()
        for i in range(5):
            memory[1][i*44:i*44+40] = rng.randbytes(40)
            memory[1][i*44+40:i*44+42] = bytes((1, (i+trial) % 2))
        values = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(16)]
        whole = compare(memory, values)
        current, joined, cursor = memory, [], 0
        for length in (0, 1, 2, 5, 8):
            after = compare(current, values[cursor:cursor+length], sequence=True)
            current = after["memory"]
            joined.extend(after["samples"])
            cursor += length
        if joined != whole["samples"] or current != whole["memory"]:
            raise AssertionError("subdivision changed chain samples/history")

    state, observed = CState(baseline(), [123]), []
    clock = CLOCK_CALLBACK(lambda *args: observed.append(args) or 0)
    io, no_clock = IO(clock, None), IO(CLOCK_CALLBACK(), None)
    invalid = 0
    for pointer, section in ((None, 0), (ctypes.byref(state.runtime), 5), (ctypes.byref(state.runtime), 0xFFFFFFFF)):
        before = bytes(state.runtime)
        assert update(pointer, section) == -1 and bytes(state.runtime) == before
        invalid += 1
    state.runtime.clock_token = 1
    for runtime, samples, count, callbacks in (
        (None, state.pointer, 1, ctypes.byref(io)), (None, None, 0, None),
        (ctypes.byref(state.runtime), None, 1, ctypes.byref(io)),
        (ctypes.byref(state.runtime), state.pointer, 129, ctypes.byref(io)),
        (ctypes.byref(state.runtime), state.pointer, 0xFFFFFFFF, ctypes.byref(io)),
        (ctypes.byref(state.runtime), state.pointer, 1, None),
        (ctypes.byref(state.runtime), state.pointer, 1, ctypes.byref(no_clock)),
    ):
        before, before_samples = bytes(state.runtime), bytes(state.samples)
        assert process(runtime, samples, count, callbacks) == -1
        assert bytes(state.runtime) == before and bytes(state.samples) == before_samples and not observed
        invalid += 1
    state.runtime.clock_token = 0
    before = bytes(state.runtime)
    assert process(ctypes.byref(state.runtime), None, 0, None) == 0 and bytes(state.runtime) == before
    empty_null = 1

    new_code = set().union(*(set(p.code) for p in program.regions.values()))
    missing = sorted(set(program.code)-coverage)
    assert not missing, [hex(pc) for pc in missing]
    assert filter_calls == set(itertools.product(("rounded", "residual"), range(5)))
    mini_binding = None
    if args.mini_image:
        from hyperrig.jieli import unpack_app
        raw = args.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest() != MINI_IMAGE:
            raise ValueError("unreviewed MINI image")
        app = unpack_app(raw)[2]["app.bin"]
        for region in [*program.regions.values(), *program.kernels.values()]:
            assert ram_bytes(app, region.start, region.end) == region.raw
        mini_binding = {"image_sha256": MINI_IMAGE, "caller_update_and_both_kernels_byte_identical": True}
    report = {"schema": 1, "project": "HyperRig", "result": "pass", "original_image_sha256": PINNED_IMAGE,
        "functions": {name: {"start": p.start, "end_exclusive": p.end,
                              "bytes_sha256": hashlib.sha256(p.raw).hexdigest()} for name, p in program.regions.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()),
        "mutating_clock_cases": mutated, "sequence_block_subset": sequences,
        "invalid_api_checks": invalid, "empty_null_no_io_checks": empty_null,
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
                                 "combined_visited": len(coverage), "combined_decoded": len(program.code)},
        "executed_kernel_variants_per_section": {str(i): sorted(mode for mode, slot in filter_calls if slot == i) for i in range(5)},
        "outputs_and_state_sha256": digest.hexdigest(),
        "compared": ["all sample words", "staged and active section bytes", "pending flags and activity byte",
                     "clock token and timing counters", "clock call order/tokens and all mapped state/samples at each call",
                     "state/sample guards and reserved bytes"],
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
        "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["coefficient generation, reset policy and callback implementation remain external",
                        "no sample-rate, physical clock-unit, effect identity or latency claim",
                        "bounded buffers and synchronous callbacks; no concurrent mutation or re-entry"]}
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "total_comparisons", "comparisons", "instruction_coverage")}))


if __name__ == "__main__":
    main()
