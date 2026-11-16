"""Compare dynamics setup/getters/startup against original instructions offline."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from dsp_dynamics_machine import (DspDynamicsProgram, REGIONS, INITIALIZATION_REGIONS,
    MAPPED, ROOT, CONFIGURATION, CONTROL, CALLBACKS, PLATFORM_INPUT, DYNAMICS_CONFIGURE,
    TABLE, MATH_REGIONS, PRIOR_REGIONS, PRIOR_TABLE, RESET_CONFIGURATION, region_bytes)
from verify_dsp_initialization import (Runtime, CState, IO, SERVICE, U32, baseline,
    SOURCES as INITIALIZATION_SOURCES)
from verify_biquad_coefficients import PINNED_IMAGE, MINI_IMAGE

SOURCES = tuple(dict.fromkeys((*INITIALIZATION_SOURCES,
    "firmware/include/hyperrig/hyperrig_dsp_dynamics.h", "firmware/src/hyperrig_dsp_dynamics.c",
    "tools/dsp_dynamics_machine.py", "tools/verify_dsp_dynamics.py", "tools/build_dsp_dynamics.py",
    "tests/test_dsp_dynamics_machine.py", "tests/dsp_dynamics_sanitize.c")))


def configure(library):
    runtime, word = ctypes.POINTER(Runtime), ctypes.POINTER(U32)
    signatures = {"configure": [runtime, U32, U32, U32], "get": [runtime, word, word, word],
                  "meter": [runtime, word, word], "startup": [runtime, ctypes.POINTER(IO)]}
    functions = {}
    for name, arguments in signatures.items():
        function = getattr(library, "hyperrig_dsp_dynamics_"+name)
        function.argtypes, function.restype = arguments, ctypes.c_int
        functions[name] = function
    return functions


class Platform:
    def __init__(self, result=0x12345678, mutations=()):
        self.result, self.mutations = result, mutations

    def __call__(self, service, arguments, view):
        assert service == PLATFORM_INPUT and arguments == (0, 0, 0)
        for address, value, size in self.mutations:
            view.mutate(address, value, size)
        return self.result


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = DspDynamicsProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, digest = dict.fromkeys(functions, 0), set(), hashlib.sha256()
    rng = random.Random(0x2030F8E)
    platform_calls = internal_dynamics_calls = producer_calls = carried_calls = mutating_cases = max_steps = 0
    threshold_levels = {}

    def compare(memory, operation, *arguments, platform_result=0x12345678, mutations=(), carried=False):
        nonlocal platform_calls, internal_dynamics_calls, producer_calls, carried_calls, mutating_cases, max_steps
        native_platform, c_platform = Platform(platform_result, mutations), Platform(platform_result, mutations)
        expected = program.execute(memory, operation, *arguments, boundary=native_platform)
        state, calls, errors = CState(memory), [], []
        outputs = [U32(0xA5A5A500+i) for i in range(3)]
        def callback(_opaque, service, a, b, c):
            try:
                before = state.snapshot()
                result = c_platform(service, (a, b, c), state)
                calls.append((service, (a, b, c), before, state.snapshot()))
                return result
            except Exception as error:
                errors.append(error)
                return 0
        callback_ref = SERVICE(callback)
        io = IO(callback_ref, None)
        if operation == "startup":
            result = functions[operation](ctypes.byref(state.runtime), ctypes.byref(io))
            assert result == 0
        elif operation == "get":
            result = functions[operation](ctypes.byref(state.runtime), *(ctypes.byref(word) for word in outputs))
            assert result == 0
        elif operation == "meter":
            result = functions[operation](ctypes.byref(state.runtime),
                ctypes.byref(outputs[0]) if arguments[0] & 1 else None,
                ctypes.byref(outputs[1]) if arguments[0] & 2 else None)
            assert result == expected["value"] == 48
        else:
            result = functions[operation](ctypes.byref(state.runtime), *arguments)
            assert result == expected["value"] == bool(arguments[0])
        if errors:
            raise errors[0]
        if (state.snapshot() != expected["memory"] or tuple(word.value for word in outputs) != expected["outputs"]
                or calls != expected["boundary_calls"] or not state.guards_ok()):
            differences = [(region, [(i, a, b) for i, (a, b) in enumerate(zip(left, right)) if a != b][:12])
                for region, (left, right) in enumerate(zip(state.snapshot(), expected["memory"])) if left != right]
            raise AssertionError((operation, arguments, differences, tuple(word.value for word in outputs),
                                  expected["outputs"], calls == expected["boundary_calls"], state.guards_ok()))
        counts[operation] += 1
        coverage.update(expected["visited"])
        platform_calls += len(calls)
        internal_dynamics_calls += len(expected["dynamics_calls"])
        producer_calls += len(expected["production_calls"])
        carried_calls += carried
        mutating_cases += bool(mutations)
        max_steps = max(max_steps, expected["steps"])
        digest.update(operation.encode()+b"\0")
        digest.update(struct.pack("<I", expected["value"]))
        digest.update(struct.pack("<3I", *expected["outputs"]))
        for row in expected["memory"]:
            digest.update(row)
        return expected

    initial = baseline(48077)
    # Every post-clamp threshold is executed, independently establishing the
    # bound that dominates the native 1024 lower-saturation branch.
    for threshold in range(-200, 1):
        expected = compare(initial, "configure", (threshold+200) % 3, threshold & 0xFFFFFFFF, 100)
        threshold_levels[threshold] = struct.unpack_from("<I", expected["memory"][0], 52)[0]
    assert min(threshold_levels.values()) == 838860 and max(threshold_levels.values()) == 8388607
    for duration in range(10, 2001):
        compare(initial, "configure", duration & 1, 0xFFFFFFFD, duration)
    print("All clamped thresholds and time values compared.", flush=True)
    extremes = (0x80000000, 0xFFFFFFFF, 0, 1, 9, 10, 11, 1999, 2000, 2001, 0x7FFFFFFF)
    for threshold in (0x80000000, 0xFFFFFF37, 0xFFFFFF38, 0xFFFFFF39, 0xFFFFFFFF, 0, 1, 0x7FFFFFFF):
        for duration in extremes:
            compare(initial, "configure", rng.getrandbits(32), threshold, duration)
    rates = (1, 2, 3, 9, 10, 11, 99, 100, 101, 8000, 44100, 48000, 48077, 96000,
             0x7FFFFF, 0x800000, 0xFFFFFF, 0x1000000, 0x1000001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)
    for divisor in rates:
        for duration in (10, 100, 2000):
            compare(baseline(divisor, seed=duration), "configure", divisor & 1, 0xFFFFFFFD, duration)
    for _ in range(128):
        compare(baseline(rng.randrange(1, 1 << 32), seed=rng.randrange(1000)), "configure",
                rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32))
    print("Signed clamps, low-divisor range reduction and binary32 boundaries compared.", flush=True)

    for value in (0, 1, 127, 255):
        for first, second in ((0, 0), (0x7FFF, 0x8000), (0x8000, 0x7FFF), (0xFFFF, 0xFFFF), (0xFF38, 2000)):
            memory = baseline(seed=value)
            memory[6][764] = value
            struct.pack_into("<HH", memory[0], 30, first, second)
            compare(memory, "get")
    for _ in range(128):
        memory = baseline(seed=rng.randrange(1000))
        struct.pack_into("<HH", memory[0], 30, rng.getrandbits(16), rng.getrandbits(16))
        memory[6][764] = rng.getrandbits(8)
        compare(memory, "get")
    for mask in range(4):
        for value in (0, 1, 0xFFFFFF, 0x1000000, 0x80000000, 0xFFFFFFFF):
            memory = baseline(seed=value)
            struct.pack_into("<I", memory[0], 60, value)
            struct.pack_into("<I", memory[4], 112, value ^ 0x89ABCDEF)
            compare(memory, "meter", mask)
    print("Raw stored getters and all optional meter-output paths compared.", flush=True)

    for guard in range(1, 256):
        memory = baseline(0)
        memory[1][0] = guard
        struct.pack_into("<5h", memory[4], 218, 32767, -32768, 2000, -2000, 1290)
        compare(memory, "startup")
    for i in range(16):
        parameters = tuple(rng.randrange(-1280, 1281) for _ in range(5))
        compare(baseline(rng.getrandbits(32), parameters, i), "startup", platform_result=rng.getrandbits(32))
    for mutations in (
        ((CONTROL+218, (-120) & 0xFFFF, 2), (CONTROL+220, 120, 2), (CONFIGURATION+36, 0, 4)),
        ((CONTROL+108, 0xDEADBEEF, 4), (CALLBACKS+764, 255, 1), (CONTROL+112, 0x10203040, 4)),
        ((CONFIGURATION+60, 0x01020304, 4), (CONTROL+210, 0, 1), (CONTROL+276, 0xFFFFFFFF, 4))):
        compare(baseline(), "startup", mutations=mutations)
    memory = baseline()
    for operation, arguments in (("configure", (0, 0xFFFFFF38, 2000)), ("get", ()), ("meter", (3,)),
        ("startup", ()), ("get", ()), ("meter", (2,)), ("meter", (2,)),
        ("configure", (0xFFFFFFFF, 1, 0)), ("get", ()), ("startup", ())):
        memory = compare(memory, operation, *arguments, carried=True)["memory"]
    print("Guarded startup adapter, callback mutations and carried state compared.", flush=True)

    invalid = invalid_checks(functions)
    new = set(program.code) - program.pre_dynamics_code
    missing = sorted(new - coverage)
    assert missing == [0x02030FEE], [hex(pc) for pc in missing]
    mini_binding = None
    all_regions = {**{f"dynamics_{k}": v for k, v in REGIONS.items()},
        **{f"initialization_{k}": v for k, v in INITIALIZATION_REGIONS.items()},
        **{f"math_{k}": v for k, v in MATH_REGIONS.items()},
        **{f"coefficients_{k}": v for k, v in PRIOR_REGIONS.items()}}
    app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == MINI_IMAGE
        mini = unpack_app(raw)[2]["app.bin"]
        for start, end in (*all_regions.values(), TABLE, (PRIOR_TABLE, PRIOR_TABLE+10), RESET_CONFIGURATION):
            assert region_bytes(mini, start, end) == region_bytes(app, start, end)
        mini_binding = {"image_sha256": MINI_IMAGE, "all_loaded_regions_identical": sorted(all_regions),
                        "both_coefficient_tables_and_dynamics_reset_copy_identical": True}
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "complete dynamics configuration/getters and integrated guarded startup",
        "original_image_sha256": PINNED_IMAGE,
        "regions": {name: {"start": start, "end_exclusive": end,
            "sha256": hashlib.sha256(program.dynamics_regions[name]).hexdigest(),
            "decoded": sum(start <= pc < end for pc in program.code),
            "visited": sum(start <= pc < end for pc in coverage)} for name, (start, end) in REGIONS.items()},
        "reset_configuration": {"start": RESET_CONFIGURATION[0], "end_exclusive": RESET_CONFIGURATION[1],
            "sha256": hashlib.sha256(program.reset_configuration).hexdigest(),
            "threshold_halfword": -3, "time_halfword": 100, "divisor_word": 48000,
            "threshold_word": 8388607, "coefficient_word": 1, "meter_word": 16777216,
            "runtime_default_claim": False},
        "comparisons": counts, "total_comparisons": sum(counts.values()),
        "platform_calls": platform_calls, "internal_dynamics_calls": internal_dynamics_calls,
        "complete_coefficient_producer_calls": producer_calls, "mutating_cases": mutating_cases,
        "carried_calls": carried_calls, "maximum_instruction_packets": max_steps, "invalid_api_checks": invalid,
        "instruction_coverage": {"new_visited": len(new & coverage), "new_decoded": len(new),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing,
            "unvisited_reason": "threshold clamp yields 201 values; exhaustive native level results are 838860..8388607, above 1024"},
        "threshold_exhaustion": {"count": len(threshold_levels), "minimum": min(threshold_levels.values()),
            "maximum": max(threshold_levels.values()), "levels_sha256": hashlib.sha256(struct.pack("<201I", *threshold_levels.values())).hexdigest()},
        "compared": ["all seven mapped runtime regions", "configuration return and meter return",
            "all three getter output words", "only-platform callback arguments/order/before-and-after runtime",
            "carried state across configuration/getter/meter/startup calls"],
        "outputs_and_state_sha256": digest.hexdigest(), "mini_v4_binding": mini_binding,
        "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["positive divisor domain; zero would feed negative infinity to the native exp reduction loop",
            "platform-input service and callback tokens remain external/opaque",
            "configuration and meter state access only; no dynamics sample-processing reconstruction claim",
            "existing binary32/ISA semantics remain shared assumptions, not a new hardware measurement",
            "getter/startup C APIs return status instead of the native terminal register value"]}
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "comparisons", "total_comparisons", "instruction_coverage")}))
    return report


def invalid_checks(functions):
    state, calls = CState(baseline()), []
    callback = SERVICE(lambda *_: calls.append(1) or 0)
    io = IO(callback, None)
    out = [U32(0xA5A5A500+i) for i in range(3)]
    runtime = ctypes.byref(state.runtime)
    invalid = [("configure", (None, 1, 0, 10)), ("get", (None, *(ctypes.byref(x) for x in out))),
        ("meter", (None, None, None)), ("startup", (None, ctypes.byref(io))),
        ("startup", (runtime, None)), ("startup", (runtime, ctypes.byref(IO(SERVICE(), None))))]
    for i in range(3):
        pointers = [ctypes.byref(x) for x in out]
        pointers[i] = None
        invalid.append(("get", (runtime, *pointers)))
    for name, arguments in invalid:
        before = state.snapshot()
        assert functions[name](*arguments) == -1
        assert state.snapshot() == before and not calls and [x.value for x in out] == [0xA5A5A500+i for i in range(3)]
    count = len(invalid)
    for value in (0,):
        state.mutate(CONFIGURATION+36, value, 4)
        before = state.snapshot()
        assert functions["configure"](runtime, 1, 0, 10) == -1 and state.snapshot() == before
        count += 1
    for index in range(5):
        for parameter in (-32768, -1281, 1281, 32767):
            state = CState(baseline())
            state.mutate(CONTROL+218+2*index, parameter & 0xFFFF, 2)
            before = state.snapshot()
            assert functions["startup"](ctypes.byref(state.runtime), ctypes.byref(io)) == -1
            assert state.snapshot() == before and not calls
            count += 1
    state.runtime.guard[0] = 1
    before = state.snapshot()
    assert functions["startup"](ctypes.byref(state.runtime), None) == 0 and state.snapshot() == before and not calls
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve completed reports; choose a new output path")
    verify(args.library, args.output, args.mini_image)
