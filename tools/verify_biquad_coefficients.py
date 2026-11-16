"""Compare coefficient conversion/staging with decoded original instructions."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from biquad_coefficients_machine import (BiquadCoefficientsProgram, REGIONS, PRODUCER,
    FLOAT, MAPPED, ROOT, STAGED, TABLE, PARAMETERS, REQUESTS, MASK32)
from verify_biquad_chain import CState as ChainState, Runtime, Section, baseline

PINNED_IMAGE = "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
MINI_IMAGE = "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
SOURCES = (
    "firmware/src/hyperrig_biquad_coefficients.c",
    "firmware/include/hyperrig/hyperrig_biquad_coefficients.h",
    "firmware/include/hyperrig/hyperrig_biquad_chain.h",
    "firmware/include/hyperrig/hyperrig_biquad.h",
    "tools/biquad_coefficients_machine.py", "tools/verify_biquad_coefficients.py",
    "tools/build_biquad_coefficients.py", "tools/dot_machine.py",
    "tools/biquad_chain_machine.py", "tools/biquad_machine.py",
    "tools/verify_biquad_chain.py", "tools/verify_biquad.py",
    "tests/test_biquad_coefficients_machine.py", "tests/biquad_coefficients_sanitize.c",
    "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
    "upstream/pi32v2-isa/isa/pi32v2.toml", "upstream/pi32v2-isa/tools/hwtest/semantics/s.py",
    "upstream/pi32v2-isa/tools/hwtest/semantics/b2.py", "research/input-manifest.json",
)


class Input(ctypes.Structure):
    _fields_ = [("numerator", ctypes.c_uint32 * 3), ("denominator", ctypes.c_uint32 * 3),
                ("enabled", ctypes.c_uint32), ("residual", ctypes.c_uint32)]


class Control(ctypes.Structure):
    _fields_ = [("requests", ctypes.c_uint32), ("parameters", ctypes.c_int8 * 5), ("reserved", ctypes.c_uint8 * 3)]


class GuardedControl(ctypes.Structure):
    _fields_ = [("before", ctypes.c_uint32), ("control", Control), ("after", ctypes.c_uint32)]


class Request(ctypes.Structure):
    _fields_ = [("mode", ctypes.c_uint32), ("table_value", ctypes.c_uint32),
                ("parameter", ctypes.c_uint32), ("width", ctypes.c_uint32)]


PRODUCE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(Section), ctypes.POINTER(Request))


class IO(ctypes.Structure):
    _fields_ = [("produce", PRODUCE), ("opaque", ctypes.c_void_p)]


class CState(ChainState):
    def __init__(self, memory):
        super().__init__(memory[:7], [])
        control = Control.from_buffer_copy(bytes(memory[7]) + bytes(memory[8]) + b"\xC1\xD2\xE3")
        self.guarded_control = GuardedControl(0x12345678, control, 0x9ABCDEF0)
        self.control = self.guarded_control.control

    def snapshot(self):
        return super().snapshot() + (struct.pack("<I", self.control.requests), bytes(self.control.parameters))

    def guards_ok(self):
        return (super().guards_ok() and (self.guarded_control.before, self.guarded_control.after) ==
                (0x12345678, 0x9ABCDEF0) and bytes(self.control.reserved) == b"\xC1\xD2\xE3")


def initial():
    return (*baseline(), bytearray(struct.pack("<I", 0xFFFFFFFE)), bytearray((1, 2, 3, 4, 5)))


def signed32(value):
    return value - (1 << 32) if value >> 31 else value


def image_bytes(app, start, end):
    offset = start - 0x02000120 if start >= 0x02000120 else 0x02056780 - 0x02000120 + start - 0x01C00000
    return app[offset:offset + end - start]


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
    divide, q28 = library.hyperrig_biquad_coefficients_divide, library.hyperrig_biquad_coefficients_q28
    divide.argtypes, divide.restype = [ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32
    q28.argtypes, q28.restype = [ctypes.c_uint32], ctypes.c_int32
    normalize = library.hyperrig_biquad_coefficients_normalize
    normalize.argtypes, normalize.restype = [ctypes.POINTER(Section), ctypes.POINTER(Input)], ctypes.c_int
    setup, stage = library.hyperrig_biquad_coefficients_setup, library.hyperrig_biquad_coefficients_stage
    setup.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(Control), ctypes.c_uint32, ctypes.POINTER(IO)]
    stage.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(Control), ctypes.c_uint32, ctypes.c_int32, ctypes.POINTER(IO)]
    setup.restype = stage.restype = ctypes.c_int
    program, rng = BiquadCoefficientsProgram(), random.Random(0x288D65182)
    counts = {name: 0 for name in ("q28", "normalize", "setup", "stage")}
    coverage, digest = set(), hashlib.sha256()
    primitive_count, callback_count, carried_count = 0, 0, 0
    preserved_history_count = 0

    def compare(operation, memory=None, section=0, value=0, words=None, noop=False, carried=False):
        nonlocal callback_count, carried_count, preserved_history_count
        memory = initial() if memory is None else memory
        words = words or [0x3F800000, 0, 0, 0x3F800000, 0, 0, 1, 1]
        state, calls, errors = CState(memory), [], []
        parameters = Input.from_buffer_copy(struct.pack("<8I", *words))

        def native_producer(index, request, machine):
            if not noop:
                machine.normalize_script(index, words)

        expected = program.execute(memory, operation, section=section, value=value,
                                   input_words=words, producer=native_producer)

        def c_producer(_opaque, destination, request):
            try:
                offset = ctypes.addressof(destination.contents) - ctypes.addressof(state.runtime.staged)
                if offset % 44 or not 0 <= offset < 220:
                    raise ValueError("C producer received an unexpected destination")
                calls.append((offset//44, tuple(getattr(request.contents, key) for key, _ in Request._fields_), state.snapshot()))
                if not noop and normalize(destination, ctypes.byref(parameters)):
                    raise ValueError("C producer normalization failed")
            except Exception as error:
                errors.append(error)

        producer = PRODUCE(c_producer)
        io = IO(producer, None)
        if operation == "q28":
            result = q28(value)
            correct = result == expected["value"]
        elif operation == "normalize":
            result = normalize(ctypes.byref(state.runtime.staged[section]), ctypes.byref(parameters))
            correct = result == 0
        elif operation == "setup":
            result = setup(ctypes.byref(state.runtime), ctypes.byref(state.control), section, ctypes.byref(io))
            correct = result == 0
        else:
            result = stage(ctypes.byref(state.runtime), ctypes.byref(state.control), section, signed32(value), ctypes.byref(io))
            correct = result == (1 if section >= 5 else 0)
        if errors:
            raise errors[0]
        if not correct or calls != expected["calls"] or state.snapshot() != expected["memory"] or not state.guards_ok():
            raise AssertionError(f"coefficient mismatch: {operation}, section={section}, value={value:#x}, words={words}, result={result}, expected={expected['value']}")
        counts[operation] += 1
        coverage.update(expected["visited"])
        callback_count += len(calls)
        carried_count += int(carried)
        if operation != "q28":
            # Every instruction/script call must leave every staged history and
            # reserved byte plus all active state unchanged.
            for index in range(5):
                start = 44*index
                assert state.snapshot()[0][start+20:start+40] == bytes(memory[0][start+20:start+40])
                assert state.snapshot()[0][start+42:start+44] == bytes(memory[0][start+42:start+44])
            assert state.snapshot()[1] == bytes(memory[1])
            preserved_history_count += 1
        digest.update(json.dumps((operation, section, value, words, result), separators=(",", ":")).encode())
        for part in state.snapshot():
            digest.update(part)
        return tuple(bytearray(part) for part in state.snapshot())

    special = [0, 1, 2, 3, 0x007FFFFF, 0x00800000, 0x00800001,
               0x30FFFFFF, 0x31000000, 0x31000001, 0x3EFFFFFF, 0x3F000000,
               0x3F7FFFFF, 0x3F800000, 0x3F800001, 0x40000000,
               0x40FFFFFF, 0x41000000, 0x41000001, 0x7F7FFFFF,
               0x7F800000, 0x7F800001, 0x7FC00000, 0x7FFFFFFF]
    signed_special = special + [word ^ 0x80000000 for word in special]
    values = set(signed_special)
    for exponent in range(256):
        for fraction in (0, 1, 0x3FFFFF, 0x400000, 0x7FFFFE, 0x7FFFFF):
            for sign in (0, 0x80000000):
                values.add(sign | exponent << 23 | fraction)
    from fractions import Fraction
    for integer in range(65):
        center = FLOAT.encode(Fraction(2*integer + 1, 1 << 29))
        for delta in (-2, -1, 0, 1, 2):
            values.add(center + delta)
            values.add((center + delta) ^ 0x80000000)
    values.update(rng.getrandbits(32) for _ in range(2048))
    for word in sorted(values):
        compare("q28", value=word)

    pairs = [(a, b) for a in signed_special for b in signed_special]
    pairs.extend((rng.getrandbits(32), rng.getrandbits(32)) for _ in range(4096))
    for exponent in range(256):
        pairs.extend(((exponent << 23 | 1, 0x40000000),
                      (0x00800000, exponent << 23 | 0x7FFFFF)))
    for a, b in pairs:
        expected = FLOAT.arithmetic(a, b, "div")
        result = divide(a, b)
        if result != expected:
            raise AssertionError(f"binary32 divide mismatch: {a:#x}/{b:#x} -> {result:#x}, expected {expected:#x}")
        primitive_count += 1
        digest.update(struct.pack("<III", a, b, result))

    for denominator in signed_special:
        for i, value in enumerate(signed_special):
            words = [value, signed_special[(i+1) % len(signed_special)], value ^ 0x80000000,
                     denominator, value, signed_special[(i+3) % len(signed_special)], i*259, i << 8]
            compare("normalize", section=i % 5, words=words)
    for _ in range(256):
        compare("normalize", section=rng.randrange(5), words=[rng.getrandbits(32) for _ in range(8)])

    for section in range(5):
        for parameter in range(256):
            memory = initial()
            memory[-1][section] = parameter
            memory[5][:] = bytes(rng.getrandbits(8) for _ in range(5))
            compare("setup", memory, section=section, noop=parameter % 2 == 0)
            compare("stage", memory, section=section, value=(parameter - 128) & MASK32,
                    words=[rng.choice(signed_special) for _ in range(6)] + [parameter, parameter << 8])
        for value in (0x80000000, 0x7FFFFFFF, 0xFFFFFFF3, 0xFFFFFFF4, 0xFFFFFFF5, 11, 12, 13):
            compare("stage", section=section, value=value)
    for section in (5, 6, 255, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for counter in (0, 1, 0xFFFFFFFE, 0xFFFFFFFF):
            memory = initial()
            memory[7][:] = struct.pack("<I", counter)
            compare("stage", memory, section=section, value=0x80000000)
    memory = initial()
    for i in range(125):
        memory = compare("stage", memory, section=i % 5, value=(i - 62) & MASK32, carried=True)

    state, invalid_count = CState(initial()), 0
    null_io = IO()
    callback = PRODUCE(lambda *_: None)
    io = IO(callback, None)
    parameters = Input()
    attempts = [
        lambda: normalize(None, ctypes.byref(parameters)),
        lambda: normalize(ctypes.byref(state.runtime.staged[0]), None),
        lambda: setup(None, ctypes.byref(state.control), 0, ctypes.byref(io)),
        lambda: setup(ctypes.byref(state.runtime), None, 0, ctypes.byref(io)),
        lambda: setup(ctypes.byref(state.runtime), ctypes.byref(state.control), 5, ctypes.byref(io)),
        lambda: setup(ctypes.byref(state.runtime), ctypes.byref(state.control), 0, None),
        lambda: setup(ctypes.byref(state.runtime), ctypes.byref(state.control), 0, ctypes.byref(null_io)),
        lambda: stage(None, ctypes.byref(state.control), 0, 0, ctypes.byref(io)),
        lambda: stage(ctypes.byref(state.runtime), None, 0, 0, ctypes.byref(io)),
        lambda: stage(ctypes.byref(state.runtime), ctypes.byref(state.control), 0, 0, None),
        lambda: stage(ctypes.byref(state.runtime), ctypes.byref(state.control), 0, 0, ctypes.byref(null_io)),
    ]
    before = state.snapshot()
    for attempt in attempts:
        assert attempt() == -1 and state.snapshot() == before and state.guards_ok()
        invalid_count += 1
    assert stage(ctypes.byref(state.runtime), ctypes.byref(state.control), 5, 0, None) == 1
    assert state.control.requests == 0xFFFFFFFF and state.snapshot()[:7] == before[:7]
    if coverage != set(program.code):
        raise AssertionError(f"unvisited coefficient instructions: {sorted(set(program.code) - coverage)}")

    original = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
    if hashlib.sha256(original.read_bytes()).hexdigest() != PINNED_IMAGE:
        raise ValueError("unreviewed original image")
    ranges = {name: {"start": f"0x{start:08x}", "end_exclusive": f"0x{end:08x}",
                     "sha256": hashlib.sha256(program.regions[name]).hexdigest(),
                     "decoded_instructions": sum(start <= pc < end for pc in program.code),
                     "visited_instructions": sum(start <= pc < end for pc in coverage)}
              for name, (start, end) in REGIONS.items()}
    static = {"producer": {"start": f"0x{PRODUCER[0]:08x}", "end_exclusive": f"0x{PRODUCER[1]:08x}",
                           "sha256": hashlib.sha256(program.producer).hexdigest(), "executed": False},
              "table": {"address": f"0x{TABLE:08x}", "sha256": hashlib.sha256(program.table).hexdigest(),
                        "uint16_values": list(struct.unpack("<5H", program.table))}}
    mini_check = None
    if args.mini_image:
        raw = args.mini_image.read_bytes()
        if hashlib.sha256(raw).hexdigest() != MINI_IMAGE:
            raise ValueError("unreviewed MINI image")
        from hyperrig.jieli import unpack_app
        app = unpack_app(raw)[2]["app.bin"]
        for name, (start, end) in REGIONS.items():
            if image_bytes(app, start, end) != program.regions[name]:
                raise ValueError("MINI coefficient region differs: " + name)
        if image_bytes(app, *PRODUCER) != program.producer or image_bytes(app, TABLE, TABLE+10) != program.table:
            raise ValueError("MINI static coefficient evidence differs")
        mini_check = {"sha256": MINI_IMAGE, "executed_regions_identical": list(REGIONS),
                      "static_regions_identical": ["producer", "table"]}
    report = {"result": "pass", "device_access": False, "hardware_test": False, "audio_test": False,
        "original_image_sha256": PINNED_IMAGE, "mini_image": mini_check,
        "instruction_comparisons": counts, "instruction_comparisons_total": sum(counts.values()),
        "binary32_division_primitive_comparisons": primitive_count,
        "all_new_instructions": len(program.code), "visited_new_instructions": len(coverage),
        "scripted_producer_calls": callback_count, "carried_stage_comparisons": carried_count,
        "history_and_active_preservation_comparisons": preserved_history_count,
        "invalid_api_checks": invalid_count, "valid_no_io_ignored_index_checks": 1,
        "regions": ranges, "static_evidence": static, "corpus_sha256": digest.hexdigest(),
        "sources_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES},
        "boundaries": ["0x02028734 mathematical producer is scripted, never decoded/executed",
                       "original normalization and conversion execute inside scripted producers",
                       "binary32 instruction semantics use pinned upstream exact-rational models",
                       "C uses integer binary32 operations; no host floating rounding dependency",
                       "no effect identity, frequency units, sample rate, stability or device/audio claim"]}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Coefficient instructions: {sum(counts.values())} comparisons; division primitive: {primitive_count}; instructions: {len(coverage)}/{len(program.code)}.")


if __name__ == "__main__":
    main()
