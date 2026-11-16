"""Compare the complete bounded mathematical producer with original instructions."""
from __future__ import annotations

import argparse
import ctypes
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import struct

from biquad_generator_machine import BiquadGeneratorProgram, REGIONS, PRIOR_REGIONS, ROOT, FLOAT, DIVISOR, region_bytes
from verify_biquad_coefficients import (CState as PriorState, Input, Request, Control, Runtime,
    Section, initial as prior_initial, PINNED_IMAGE, MINI_IMAGE, SOURCES as PRIOR_SOURCES)

SOURCES = (*PRIOR_SOURCES,
    "firmware/include/hyperrig/hyperrig_biquad_generator.h", "firmware/src/hyperrig_biquad_generator.c",
    "tools/biquad_generator_machine.py", "tools/verify_biquad_generator.py", "tools/build_biquad_generator.py",
    "tests/test_biquad_generator_machine.py", "tests/biquad_generator_sanitize.c")


def initial(divisor=48000):
    return (*prior_initial(), bytearray(struct.pack("<I", divisor)))


class CState(PriorState):
    def __init__(self, memory):
        self.divisor = struct.unpack("<I", memory[-1])[0]
        super().__init__(memory[:-1])

    def snapshot(self):
        return super().snapshot() + (struct.pack("<I", self.divisor),)


def words(value):
    return struct.unpack("<8I", bytes(value))


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
    functions = {}
    for name in ("add", "multiply", "from_unsigned", "exp", "scaled_exp", "cosine", "sine", "square_root"):
        function = getattr(library, "hyperrig_biquad_math_" + name)
        if name in ("add", "multiply"):
            function.argtypes, function.restype = [ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32
        elif name in ("exp", "scaled_exp"):
            function.argtypes, function.restype = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)], ctypes.c_int
        else:
            function.argtypes, function.restype = [ctypes.c_uint32], ctypes.c_uint32
        functions[name] = function
    generate_input = library.hyperrig_biquad_generate_input
    generate_input.argtypes = [ctypes.POINTER(Input), ctypes.POINTER(Request), ctypes.c_uint32]
    generate_input.restype = ctypes.c_int
    generate = library.hyperrig_biquad_generate
    generate.argtypes, generate.restype = [ctypes.POINTER(Section), ctypes.POINTER(Request), ctypes.c_uint32], ctypes.c_int
    setup, stage = library.hyperrig_biquad_generate_setup, library.hyperrig_biquad_generate_stage
    setup.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(Control), ctypes.c_uint32, ctypes.c_uint32]
    stage.argtypes = [ctypes.POINTER(Runtime), ctypes.POINTER(Control), ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32]
    setup.restype = stage.restype = ctypes.c_int
    program, rng = BiquadGeneratorProgram(), random.Random(0x28734285D4)
    counts = {name: 0 for name in (*REGIONS, "setup", "stage")}
    primitives = {name: 0 for name in ("add", "multiply", "from_unsigned")}
    coverage, digest = set(), hashlib.sha256()
    raw_comparisons, carried_count, preserved_count, maximum_steps = 0, 0, 0, 0
    math_calls = {name: 0 for name in REGIONS}

    def compare(operation, memory=None, section=0, value=0, request=None, carried=False):
        nonlocal raw_comparisons, carried_count, preserved_count, maximum_steps
        memory = initial() if memory is None else memory
        expected = program.execute(memory, operation, section=section, value=value, request=request)
        state = CState(memory)
        if operation in ("exp", "scaled_exp"):
            output = ctypes.c_uint32(0xA5A5A5A5)
            assert functions[operation](value, ctypes.byref(output)) == 0
            result = output.value
        elif operation in ("cosine", "sine", "square_root"):
            result = functions[operation](value)
        elif operation == "generate":
            parameters = Request(*request)
            result = generate(ctypes.byref(state.runtime.staged[section]), ctypes.byref(parameters), state.divisor)
        elif operation == "setup":
            result = setup(ctypes.byref(state.runtime), ctypes.byref(state.control), section, state.divisor)
        else:
            result = stage(ctypes.byref(state.runtime), ctypes.byref(state.control), section,
                           ctypes.c_int32(value).value, state.divisor)
        if operation in ("generate", "setup", "stage"):
            wanted = 1 if operation == "stage" and section >= 5 else 0
        else:
            wanted = expected["value"]
        if result != wanted or state.snapshot() != expected["memory"] or not state.guards_ok():
            raise AssertionError(f"generator mismatch: {operation}, section={section}, value={value:#x}, request={request}, divisor={state.divisor}, got={result:#x}, expected={wanted:#x}")
        if len(expected["production_calls"]) != len(expected["normalization_calls"]):
            raise AssertionError("unexpected original mathematical call count")
        for (_, arguments, _), (destination, original_words) in zip(expected["production_calls"], expected["normalization_calls"]):
            parameters, raw = Request(*arguments), Input()
            assert generate_input(ctypes.byref(raw), ctypes.byref(parameters), state.divisor) == 0
            if words(raw) != original_words:
                raise AssertionError(f"pre-normalization mismatch: request={arguments}, divisor={state.divisor}, C={words(raw)}, original={original_words}")
            raw_comparisons += 1
            digest.update(struct.pack("<8I", *original_words))
        for name, _argument in expected["math_calls"]:
            math_calls[name] += 1
        counts[operation] += 1
        carried_count += int(carried)
        maximum_steps = max(maximum_steps, expected["steps"])
        coverage.update(expected["visited"])
        if operation in ("generate", "setup", "stage"):
            for index in range(5):
                start = 44*index
                assert state.snapshot()[0][start+20:start+40] == bytes(memory[0][start+20:start+40])
                assert state.snapshot()[0][start+42:start+44] == bytes(memory[0][start+42:start+44])
            assert state.snapshot()[1] == bytes(memory[1])
            preserved_count += 1
        digest.update(json.dumps((operation, section, value, request, result), separators=(",", ":")).encode())
        for part in state.snapshot():
            digest.update(part)
        return tuple(bytearray(part) for part in state.snapshot())

    special = [0, 1, 2, 3, 0x007FFFFF, 0x00800000, 0x00800001, 0x33800000,
               0x3EFFFFFF, 0x3F000000, 0x3F000001, 0x3F7FFFFF, 0x3F800000, 0x3F800001,
               0x40000000, 0x40C90FDB, 0x41800000, 0x43000000, 0x4B800000,
               0x7F7FFFFF, 0x7F800000, 0x7F800001, 0x7FC00000, 0x7FFFFFFF]
    signed_special = special + [value ^ 0x80000000 for value in special]
    pairs = [(a, b) for a in signed_special for b in signed_special]
    pairs.extend((rng.getrandbits(32), rng.getrandbits(32)) for _ in range(4096))
    for exponent in range(1, 255):
        base = exponent << 23
        for delta in (0, 1, 0x7FFFFE, 0x7FFFFF):
            value = base | delta
            pairs.append((value, value ^ 0x80000000))
            if value > 1:
                pairs.append((value, (value-1) ^ 0x80000000))
    for name, operation in (("add", "add"), ("multiply", "mul")):
        for a, b in pairs:
            expected = FLOAT.arithmetic(a, b, operation)
            result = functions[name](a, b)
            if result != expected:
                raise AssertionError(f"{name} mismatch: {a:#x}, {b:#x}: {result:#x} != {expected:#x}")
            primitives[name] += 1
            digest.update(struct.pack("<III", a, b, result))
    unsigneds = {0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF}
    for power in range(32):
        unsigneds.update(((1 << power) + delta) & 0xFFFFFFFF for delta in (-2, -1, 0, 1, 2, 3))
    unsigneds.update(rng.getrandbits(32) for _ in range(1024))
    for value in sorted(unsigneds):
        expected = FLOAT.encode(Fraction(value))
        result = functions["from_unsigned"](value)
        if result != expected:
            raise AssertionError(f"unsigned conversion mismatch: {value:#x}: {result:#x} != {expected:#x}")
        primitives["from_unsigned"] += 1
        digest.update(struct.pack("<II", value, result))

    exp_values = {FLOAT.encode(Fraction(i, 16)) for i in range(-256, 257)}
    for boundary in (0, 0x3F000000, 0x3F317218, 0x41800000):
        for delta in (-1, 0, 1):
            value = boundary + delta
            if 0 <= value <= 0x41800000:
                exp_values.update((value, value ^ 0x80000000))
    for value in sorted(exp_values):
        compare("exp", value=value)
    scaled_values = {FLOAT.encode(Fraction(i)) for i in range(-128, 129)}
    scaled_values.update((1, 0x80000001, 0x80000000, 0x42FFFFFF, 0xC2FFFFFF))
    for value in sorted(scaled_values):
        compare("scaled_exp", value=value)
    helper_values = set(signed_special)
    for exponent in range(256):
        helper_values.update((exponent << 23 | 1, 0x80000000 | exponent << 23 | 0x7FFFFF))
    helper_values.update(rng.getrandbits(32) for _ in range(128))
    for operation in ("cosine", "sine", "square_root"):
        for value in sorted(helper_values):
            compare(operation, value=value)

    # Every stored int8 parameter exercises the full setup/producer path.
    for section in range(5):
        for parameter in range(256):
            memory = initial()
            memory[-2][section] = parameter
            compare("setup", memory, section=section)
    # Every clamped parameter, each section, and boundary divisor words.
    for divisor in (0, 1, 8000, 44100, 48000, 96000, 0xFFFFFFFF):
        for section in range(5):
            for parameter in range(-12, 13):
                compare("stage", initial(divisor), section=section, value=parameter & 0xFFFFFFFF)
    for section in range(5):
        for parameter in (0x80000000, 0x7FFFFFFF, 0xFFFFFFF3, 13):
            compare("stage", section=section, value=parameter)
    for section in (5, 6, 0x80000000, 0xFFFFFFFF):
        memory = initial()
        memory[-3][:] = bytes.fromhex("ffffffff")
        compare("stage", memory, section=section, value=0x80000000)

    # Raw producer inputs cover all modes, unusual width/frequency words and
    # uint32-to-float divisor rounding independently of the fixed setup table.
    for mode in (0, 1, 2, 0xFFFFFFFF):
        for i, frequency in enumerate(signed_special):
            parameter = FLOAT.encode(Fraction((-128, -12, 0, 12, 128)[i % 5]))
            request = (mode, frequency, parameter, signed_special[(i+7) % len(signed_special)])
            compare("generate", section=i % 5, request=request)
        for divisor in (16777216, 16777217, 16777218, 16777219, 16777220, 0xFFFFFFFF):
            for parameter in (0, 0x80000000, 1, 0x80000001, 0x43000000, 0xC3000000):
                compare("generate", initial(divisor), request=(mode, 0x45DAC000, parameter, 0x3F666666))
    for _ in range(128):
        compare("generate", initial(rng.getrandbits(32)), section=rng.randrange(5),
                request=(rng.getrandbits(32), rng.getrandbits(32),
                         FLOAT.encode(Fraction(rng.randrange(-2048, 2049), 16)), rng.getrandbits(32)))
    memory = initial()
    for i in range(75):
        memory = compare("stage", memory, section=i % 5, value=(i-37) & 0xFFFFFFFF, carried=True)

    invalid_count = 0
    state = CState(initial())
    request, raw = Request(0, 0x42C80000, 0, 0x3F666666), Input()
    before = state.snapshot()
    attempts = [lambda: generate(None, ctypes.byref(request), 48000),
                lambda: generate(ctypes.byref(state.runtime.staged[0]), None, 48000),
                lambda: generate_input(None, ctypes.byref(request), 48000),
                lambda: generate_input(ctypes.byref(raw), None, 48000),
                lambda: setup(None, ctypes.byref(state.control), 0, 48000),
                lambda: setup(ctypes.byref(state.runtime), None, 0, 48000),
                lambda: setup(ctypes.byref(state.runtime), ctypes.byref(state.control), 5, 48000),
                lambda: stage(None, ctypes.byref(state.control), 0, 0, 48000),
                lambda: stage(ctypes.byref(state.runtime), None, 0, 0, 48000)]
    for attempt in attempts:
        assert attempt() == -1 and state.snapshot() == before
        invalid_count += 1
    for name, limit in (("exp", 0x41800000), ("scaled_exp", 0x43000000)):
        assert functions[name](0, None) == -1
        invalid_count += 1
        for value in (limit+1, (limit+1) | 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000, 0xFFC00000):
            output = ctypes.c_uint32(0xA5A5A5A5)
            assert functions[name](value, ctypes.byref(output)) == -1 and output.value == 0xA5A5A5A5
            invalid_count += 1
    for value in (0x43000001, 0xC3000001, 0x7F800000, 0xFF800000, 0x7FC00000, 0xFFC00000):
        request.parameter = value
        raw = Input.from_buffer_copy(bytes([0xA5])*32)
        assert generate_input(ctypes.byref(raw), ctypes.byref(request), 48000) == -1 and bytes(raw) == bytes([0xA5])*32
        assert generate(ctypes.byref(state.runtime.staged[0]), ctypes.byref(request), 48000) == -1
        assert state.snapshot() == before
        invalid_count += 2
    if coverage != set(program.code):
        raise AssertionError(f"unvisited generator instructions: {sorted(set(program.code)-coverage)}")

    original = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == PINNED_IMAGE
    ranges = {name: {"start": f"0x{start:08x}", "end_exclusive": f"0x{end:08x}",
                     "sha256": hashlib.sha256(program.math_regions[name]).hexdigest(),
                     "decoded_instructions": sum(start <= pc < end for pc in program.code),
                     "visited_instructions": sum(start <= pc < end for pc in coverage)}
              for name, (start, end) in REGIONS.items()}
    mini_check = None
    if args.mini_image:
        raw_image = args.mini_image.read_bytes()
        assert hashlib.sha256(raw_image).hexdigest() == MINI_IMAGE
        from hyperrig.jieli import unpack_app
        app = unpack_app(raw_image)[2]["app.bin"]
        for name, bounds in REGIONS.items():
            assert region_bytes(app, *bounds) == program.math_regions[name], name
        for name, bounds in PRIOR_REGIONS.items():
            assert region_bytes(app, *bounds) == program.regions[name], name
        assert region_bytes(app, 0x0203A55C, 0x0203A566) == program.table
        mini_check = {"sha256": MINI_IMAGE, "executed_new_regions_identical": list(REGIONS),
                      "executed_prior_regions_identical": list(PRIOR_REGIONS), "table_identical": True}
    report = {"result": "pass", "device_access": False, "hardware_test": False, "audio_test": False,
        "original_image_sha256": PINNED_IMAGE, "mini_image": mini_check,
        "instruction_comparisons": counts, "instruction_comparisons_total": sum(counts.values()),
        "binary32_primitive_comparisons": primitives, "primitive_comparisons_total": sum(primitives.values()),
        "new_decoded_instructions": len(program.code)-len(program.prior_code),
        "new_visited_instructions": len(coverage-program.prior_code),
        "combined_decoded_instructions": len(program.code), "combined_visited_instructions": len(coverage),
        "raw_pre_normalization_comparisons": raw_comparisons, "scripted_mathematical_calls": 0,
        "internal_mathematical_calls": math_calls, "maximum_executed_packets": maximum_steps,
        "carried_stage_comparisons": carried_count, "history_active_preservation_comparisons": preserved_count,
        "invalid_api_checks": invalid_count, "regions": ranges, "corpus_sha256": digest.hexdigest(),
        "sources_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "boundaries": ["exp input finite magnitude <=16; scaled-exp/producer parameter finite magnitude <=128",
                       "original uint32 divisor word is an explicit immutable input; initialization not recovered",
                       "all producer math, normalization, conversion and staging execute original instructions",
                       "no physical units, effect identity, sample-rate, stability, latency, hardware or audio claim"]}
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(f"Generator: {sum(counts.values())} instruction comparisons, {raw_comparisons} raw coefficient comparisons, "
          f"{sum(primitives.values())} primitive comparisons; instructions {len(coverage)}/{len(program.code)}.")


if __name__ == "__main__":
    main()
