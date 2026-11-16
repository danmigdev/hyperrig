"""Compare DSP initialization with decoded instructions and synthetic startup services."""
from __future__ import annotations

import argparse
import ctypes
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import struct

from dsp_initialization_machine import (DspInitializationProgram, REGIONS, MAPPED,
    CONFIGURATION, GUARD, SLOTS, ROUTES, CONTROL, FILTERS, CALLBACKS, TABLE,
    PLATFORM_INPUT, DYNAMICS_CONFIGURE, MATH_REGIONS, PRIOR_REGIONS,
    PRIOR_TABLE, ROOT, DIVISOR, region_bytes)
from biquad_coefficients_machine import FLOAT
from dot_machine import signed
from verify_biquad_coefficients import Section, PINNED_IMAGE, MINI_IMAGE
from verify_biquad_generator import SOURCES as GENERATOR_SOURCES

SOURCES = tuple(dict.fromkeys((*GENERATOR_SOURCES,
    "firmware/include/hyperrig/hyperrig_dsp_initialization.h", "firmware/src/hyperrig_dsp_initialization.c",
    "tools/dsp_initialization_machine.py", "tools/verify_dsp_initialization.py", "tools/build_dsp_initialization.py",
    "tests/test_dsp_initialization_machine.py", "tests/dsp_initialization_sanitize.c")))
U8, U32, I32 = ctypes.c_uint8, ctypes.c_uint32, ctypes.c_int32


class Runtime(ctypes.Structure):
    _fields_ = [("configuration", U8*68), ("guard", U8*4), ("slots", U8*(16*480)),
        ("routes", U8*(8*448)), ("control", U8*640), ("filters", Section*4), ("callbacks", U8*768)]


class GuardedRuntime(ctypes.Structure):
    _fields_ = [("before", U32*4), ("runtime", Runtime), ("after", U32*4)]


SERVICE = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, U32, U32, U32)


class IO(ctypes.Structure):
    _fields_ = [("call", SERVICE), ("opaque", ctypes.c_void_p)]


def baseline(divisor=48000, parameters=(0, 0, 0, 0, 0), seed=1):
    memory = tuple(bytearray((i*37 + region*53 + seed*17) & 255 for i in range(size))
                   for region, (_, size) in enumerate(MAPPED))
    struct.pack_into("<I", memory[0], 36, divisor)
    memory[1][0] = 0
    struct.pack_into("<5h", memory[4], 218, *parameters)
    for i in range(8):
        memory[4][210+i] = 1
        memory[3][448*i+1] = 2*i
        memory[3][448*i+4] = (255+i) & 255
    return memory


class CState:
    def __init__(self, memory):
        self.guarded = GuardedRuntime()
        for i in range(4):
            self.guarded.before[i], self.guarded.after[i] = 0x12345678+i, 0x9ABCDEF0+i
        self.runtime = self.guarded.runtime
        for (name, _), data in zip(Runtime._fields_, memory):
            ctypes.memmove(ctypes.addressof(getattr(self.runtime, name)), bytes(data), len(data))

    def snapshot(self):
        return tuple(bytes(getattr(self.runtime, name)) for name, _ in Runtime._fields_)

    def guards_ok(self):
        return (list(self.guarded.before) == [0x12345678+i for i in range(4)] and
                list(self.guarded.after) == [0x9ABCDEF0+i for i in range(4)])

    def mutate(self, address, value, size):
        for (base, length), (name, _) in zip(MAPPED, Runtime._fields_):
            if base <= address and address+size <= base+length:
                data = (value & ((1 << (size*8))-1)).to_bytes(size, "little")
                ctypes.memmove(ctypes.addressof(getattr(self.runtime, name))+address-base, data, size)
                return
        raise ValueError("C startup mutation escaped mapped runtime")


class StartupScript:
    def __init__(self, values=None, mutations=None):
        self.values = values or {PLATFORM_INPUT: 0x12345678, DYNAMICS_CONFIGURE: 0xBADDCAFE}
        self.mutations, self.calls = mutations or {}, []

    def __call__(self, service, args, view):
        self.calls.append((service, args))
        for address, value, size in self.mutations.get(service, ()):
            view.mutate(address, value, size)
        return self.values.get(service, 0)


def configure(library):
    runtime = ctypes.POINTER(Runtime)
    specs = {"q16": ([U32], I32), "gain": ([I32, ctypes.POINTER(U32)], ctypes.c_int),
        "setup": ([ctypes.POINTER(Section), U32, I32, U32], ctypes.c_int),
        "reset_filters": ([runtime], ctypes.c_int), "reset_slot": ([runtime, U32], ctypes.c_int),
        "initialize": ([runtime, U32, U32], ctypes.c_int), "bind": ([runtime, U32, U32], ctypes.c_int),
        "startup": ([runtime, ctypes.POINTER(IO)], ctypes.c_int)}
    functions = {}
    for name, (arguments, result) in specs.items():
        function = getattr(library, "hyperrig_dsp_initialization_"+name)
        function.argtypes, function.restype = arguments, result
        functions[name] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    assert ctypes.sizeof(Runtime) == sum(size for _, size in MAPPED)
    program, functions = DspInitializationProgram(), configure(ctypes.CDLL(str(library_path.resolve())))
    rng, digest = random.Random(0x2911224EC), hashlib.sha256()
    counts, coverage = dict.fromkeys(functions, 0), set()
    production_calls = boundary_calls = mutating_cases = carried_calls = max_steps = 0

    def compare(memory, operation, *args, values=None, mutations=None, carried=False):
        nonlocal production_calls, boundary_calls, mutating_cases, carried_calls, max_steps
        native_script, c_script = StartupScript(values, mutations), StartupScript(values, mutations)
        expected = program.execute(memory, operation, *args, boundary=native_script)
        state, calls, errors = CState(memory), [], []
        def callback(_opaque, service, a, b, c):
            try:
                before = state.snapshot()
                result = c_script(service, (a, b, c), state)
                calls.append((service, (a, b, c), before, state.snapshot()))
                return result
            except Exception as error:
                errors.append(error)
                return 0
        call = SERVICE(callback)
        io, out = IO(call, None), U32(0xA5A5A5A5)
        function = functions[operation]
        if operation == "q16":
            assert function(*args) & 0xFFFFFFFF == expected["value"]
        elif operation == "gain":
            assert function(signed(args[0]), ctypes.byref(out)) == 0
            assert out.value == expected["value"]
        elif operation == "setup":
            assert function(ctypes.byref(state.runtime.filters[args[2]]), args[0], signed(args[1]),
                            struct.unpack_from("<I", memory[0], 36)[0]) == 0
        elif operation == "startup":
            assert function(ctypes.byref(state.runtime), ctypes.byref(io)) == 0
        else:
            assert function(ctypes.byref(state.runtime), *args) == 0
        if errors:
            raise errors[0]
        if state.snapshot() != expected["memory"] or calls != expected["boundary_calls"] or not state.guards_ok():
            differences = [(region, [(i, a, b) for i, (a, b) in enumerate(zip(left, right)) if a != b][:12])
                for region, (left, right) in enumerate(zip(state.snapshot(), expected["memory"])) if left != right]
            raise AssertionError((operation, args, differences, calls == expected["boundary_calls"], state.guards_ok()))
        counts[operation] += 1
        coverage.update(expected["visited"])
        production_calls += len(expected["production_calls"])
        boundary_calls += len(calls)
        mutating_cases += bool(mutations)
        carried_calls += carried
        max_steps = max(max_steps, expected["steps"])
        digest.update(operation.encode()+b"\0")
        digest.update(struct.pack("<"+"I"*len(args), *args))
        digest.update(struct.pack("<I", expected["value"]))
        for part in expected["memory"]:
            digest.update(part)
        return expected

    # Every binary32 exponent, both signs, special values and rounding edges.
    words = {0, 0x80000000, 0x7F800000, 0xFF800000, 0x7F800001, 0xFF800001,
             0x7FC00000, 0xFFC00000, 0x7FFFFFFF, 0xFFFFFFFF}
    for exponent in range(256):
        for mantissa in (0, 1, 0x3FFFFF, 0x7FFFFF):
            for sign in (0, 0x80000000):
                words.add(sign | exponent << 23 | mantissa)
    for integer in (0, 1, 2, 127, 128, 32767, 65535, 65536, 16777215, 2147483647):
        center = FLOAT.encode(Fraction(2*integer+1, 1 << 17))
        for delta in (-1, 0, 1):
            words.update(((center+delta) & 0xFFFFFFFF, ((center+delta) & 0xFFFFFFFF) ^ 0x80000000))
    words.update(rng.getrandbits(32) for _ in range(256))
    initial = baseline()
    for value in sorted(words):
        compare(initial, "q16", value)
    gain_parameters = set(range(-240, 121)) | {-1280, -1279, -1200, -1000, 1000, 1200, 1279, 1280}
    gain_parameters.update(rng.randrange(-1280, 1281) for _ in range(64))
    for parameter in sorted(gain_parameters):
        compare(initial, "gain", parameter & 0xFFFFFFFF)
    print("Q16 and bounded gain conversion comparisons passed.", flush=True)

    for index in range(1, 5):
        for parameter in range(-120, 121):
            compare(initial, "setup", index, parameter & 0xFFFFFFFF, (index+parameter) % 4)
        for divisor in (0, 1, 8000, 44100, 48000, 48077, 96000, 0xFFFFFFFF):
            for parameter in (-1280, -1279, 0, 1279, 1280):
                compare(baseline(divisor), "setup", index, parameter & 0xFFFFFFFF, index-1)
    print("Second-table setup executed the full coefficient producer.", flush=True)

    for slot in (*range(256), 0x80000000, 0xFFFFFFFF):
        memory = baseline(seed=slot & 255)
        for i in range(8):
            memory[3][448*i+1] = slot & 255 if i % 2 else (slot+1) & 255
            memory[4][210+i] = i % 3
            memory[3][448*i+4] = (254+i) & 255
        compare(memory, "reset_slot", slot)
    for divisor in (0, 1, 8000, 44100, 48000, 48077, 96000, 0xFFFFFFFF):
        for parameters in ((0,)*5, (-240, -120, 120, -120, 120), (-1280, -1279, 0, 1279, 1280),
                           (1280, 1280, 1280, 1280, 1280)):
            compare(baseline(divisor, parameters), "reset_filters")
            compare(baseline(48000, parameters), "initialize", divisor, divisor ^ 0xF0E1D2C3)
    for _ in range(48):
        parameters = tuple(rng.randrange(-1280, 1281) for _ in range(5))
        memory = baseline(rng.getrandbits(32), parameters, rng.randrange(256))
        for i in range(8):
            memory[3][448*i+1] = rng.randrange(32)
            memory[4][210+i] = rng.randrange(2)
        compare(memory, "initialize", rng.getrandbits(32), rng.getrandbits(32))
    for first, second in ((0, 0), (0xFFFFFFFF, 0x80000000), (0x0201A864, 0x0201A96A)):
        compare(baseline(), "bind", first, second)
    print("Full initializer, route resets, preserved bytes and filter histories compared.", flush=True)

    for guard in range(1, 256):
        memory = baseline()
        memory[1][0] = guard
        struct.pack_into("<5h", memory[4], 218, -32768, 32767, -32768, 32767, -32768)
        result = compare(memory, "startup")
        assert not result["boundary_calls"] and result["memory"] == tuple(bytes(part) for part in memory)
    for input_word in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        memory = baseline(48000, (12, -120, -1, 1, 120))
        result = compare(memory, "startup", values={PLATFORM_INPUT: input_word, DYNAMICS_CONFIGURE: 0xFFFFFFFF})
        assert struct.unpack_from("<I", result["memory"][0], 36)[0] == 48077
        assert struct.unpack_from("<I", result["memory"][4], 48)[0] == input_word
        assert [call[0] for call in result["boundary_calls"]] == [PLATFORM_INPUT, DYNAMICS_CONFIGURE]
        assert all(struct.unpack_from("<I", event[2][0], 36)[0] == 48077 for event in result["production_calls"])
        compare(result["memory"], "startup", carried=True)
    mutation_sets = (
        {PLATFORM_INPUT: ((GUARD, 0, 1), (DIVISOR, 123, 4), (CONTROL+220, 120, 2),
                          (ROUTES+4, 255, 1), (CALLBACKS+8, 0x12345678, 4))},
        {DYNAMICS_CONFIGURE: ((DIVISOR, 44100, 4), (CONTROL+48, 0x89ABCDEF, 4),
                             (CONTROL+52, 1, 4), (CALLBACKS+8, 0x12345678, 4), (GUARD, 7, 1))},
        {PLATFORM_INPUT: ((CONTROL+218, (-240) & 65535, 2), (CONTROL+222, 1280, 2)),
         DYNAMICS_CONFIGURE: ((FILTERS+20, 0xA1B2C3D4, 4), (CONTROL+180, 31, 1), (CALLBACKS+2, 0xABCD, 2))},
    )
    for mutations in mutation_sets:
        result = compare(baseline(48000, (10, 20, 30, 40, 50)), "startup", mutations=mutations)
        compare(result["memory"], "startup", carried=True)

    # Invalid APIs must fail before changing any caller storage or invoking IO.
    state, out, calls = CState(baseline()), U32(0xDEADBEEF), []
    service = SERVICE(lambda *args: calls.append(args) or 0)
    io, runtime = IO(service, None), ctypes.byref(state.runtime)
    invalid = [("gain", (0, None)), ("setup", (None, 1, 0, 48000)),
        ("reset_filters", (None,)), ("reset_slot", (None, 0)), ("initialize", (None, 48077, 0)),
        ("bind", (None, 0, 0)), ("startup", (None, ctypes.byref(io))),
        ("startup", (runtime, None)), ("startup", (runtime, ctypes.byref(IO(SERVICE(), None))))]
    for parameter in (-2147483648, -1281, 1281, 2147483647):
        invalid.extend((("gain", (parameter, ctypes.byref(out))),
                        ("setup", (ctypes.byref(state.runtime.filters[0]), 1, parameter, 48000))))
    for index in (0, 5, 0x80000000, 0xFFFFFFFF):
        invalid.append(("setup", (ctypes.byref(state.runtime.filters[0]), index, 0, 48000)))
    invalid_count = 0
    for operation, args in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == -1 and state.snapshot() == before and not calls and out.value == 0xDEADBEEF
        assert state.guards_ok()
        invalid_count += 1
    for offset in range(218, 228, 2):
        for parameter in (-32768, -1281, 1281, 32767):
            state = CState(baseline())
            state.mutate(CONTROL+offset, parameter, 2)
            before, runtime = state.snapshot(), ctypes.byref(state.runtime)
            for operation, args in (("initialize", (48077, 0)), ("reset_filters", ()), ("startup", (ctypes.byref(io),))):
                assert functions[operation](runtime, *args) == -1 and state.snapshot() == before and not calls
                assert state.guards_ok()
                invalid_count += 1
    state = CState(baseline())
    state.runtime.guard[0] = 1
    state.mutate(CONTROL+218, 32767, 2)
    before = state.snapshot()
    assert functions["startup"](ctypes.byref(state.runtime), None) == 0 and state.snapshot() == before
    new_code = set(program.code) - program.pre_initialization_code
    assert not new_code-coverage, [hex(pc) for pc in sorted(new_code-coverage)]

    ranges = {name: {"start": f"0x{start:08x}", "end_exclusive": f"0x{end:08x}",
                    "sha256": hashlib.sha256(program.initialization_regions[name]).hexdigest(),
                    "decoded": sum(start <= pc < end for pc in program.code),
                    "visited": sum(start <= pc < end for pc in coverage)}
              for name, (start, end) in REGIONS.items()}
    mini_binding = None
    if mini_image:
        raw = mini_image.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == MINI_IMAGE
        from hyperrig.jieli import unpack_app
        app = unpack_app(raw)[2]["app.bin"]
        for name, bounds in REGIONS.items():
            assert region_bytes(app, *bounds) == program.initialization_regions[name], name
        for name, bounds in MATH_REGIONS.items():
            assert region_bytes(app, *bounds) == program.math_regions[name], name
        for name, bounds in PRIOR_REGIONS.items():
            assert region_bytes(app, *bounds) == program.regions[name], name
        assert region_bytes(app, *TABLE) == program.initialization_table
        assert region_bytes(app, PRIOR_TABLE, PRIOR_TABLE+10) == program.table
        assert region_bytes(app, DIVISOR, DIVISOR+4) == program.divisor_reset
        mini_binding = {"sha256": MINI_IMAGE, "new_regions_identical": list(REGIONS),
            "all_loaded_math_and_conversion_regions_identical": True,
            "both_tables_and_reset_divisor_identical": True}
    report = {"result": "pass", "device_access": False, "hardware_test": False, "audio_test": False,
        "original_image_sha256": PINNED_IMAGE, "mini_image": mini_binding,
        "comparisons": counts, "total_comparisons": sum(counts.values()), "mutating_cases": mutating_cases,
        "carried_startup_calls": carried_calls, "coefficient_producer_calls": production_calls,
        "startup_boundary_calls": boundary_calls, "scripted_mathematical_producer_calls": 0,
        "new_decoded_instructions": len(new_code), "new_visited_instructions": len(coverage & new_code),
        "combined_decoded_instructions": len(program.code), "combined_visited_instructions": len(coverage),
        "maximum_executed_packets": max_steps, "invalid_api_checks": invalid_count,
        "guarded_null_io_noop_checked": True, "regions": ranges,
        "table": {"start": f"0x{TABLE[0]:08x}", "end_exclusive": f"0x{TABLE[1]:08x}",
                  "sha256": hashlib.sha256(program.initialization_table).hexdigest()},
        "reset_divisor": {"address": f"0x{DIVISOR:08x}", "value": 48000,
                          "sha256": hashlib.sha256(program.divisor_reset).hexdigest()},
        "mapped_memory": [{"base": f"0x{base:08x}", "size": size} for base, size in MAPPED],
        "corpus_sha256": digest.hexdigest(),
        "sources_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "boundaries": ["startup platform input 0x01c010a6 and dynamics configuration 0x02030f8e remain synthetic",
            "complete initializer and four-filter reset/setup/gain/Q16 bodies execute with original producer math",
            "stored signed parameters bounded to +/-1280; original setter clamps fall inside this domain",
            "callback tokens are recorded bytes, not host or device function calls",
            "no physical rate, startup scheduling, full-firmware, audio or hardware validation"]}
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "comparisons", "total_comparisons",
        "new_visited_instructions", "new_decoded_instructions", "combined_visited_instructions",
        "coefficient_producer_calls", "startup_boundary_calls")}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve completed reports; choose a new output file")
    verify(args.library, args.output, args.mini_image)
