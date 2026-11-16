"""Compare startup input and four-section processing with original instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from dsp_audio_path_machine import (DspAudioPathProgram, REGIONS, DYNAMICS_REGIONS,
    INITIALIZATION_REGIONS, MATH_REGIONS, PRIOR_REGIONS, RESET_CONFIGURATION,
    MAPPED, ROOT, PLATFORM, CACHE, STAGED, TRANSITION, CONTROL, CONFIGURATION,
    TABLE, PRIOR_TABLE, STATIC, region_bytes, BiquadProgram)
from verify_dsp_dynamics import SOURCES as DYNAMICS_SOURCES
from verify_dsp_initialization import Runtime as DspRuntime, baseline as dsp_baseline, U8, U32, I32
from verify_biquad_coefficients import PINNED_IMAGE, MINI_IMAGE
from dot_machine import signed

SOURCES = tuple(dict.fromkeys((*DYNAMICS_SOURCES,
    "firmware/src/hyperrig_biquad.c", "tools/biquad_machine.py",
    "upstream/pi32v2-isa/tools/hwtest/semantics/r.py",
    "upstream/pi32v2-isa/tools/hwtest/semantics/_r_util.py",
    "firmware/include/hyperrig/hyperrig_dsp_audio_path.h", "firmware/src/hyperrig_dsp_audio_path.c",
    "tools/dsp_audio_path_machine.py", "tools/verify_dsp_audio_path.py", "tools/build_dsp_audio_path.py",
    "tests/test_dsp_audio_path_machine.py", "tests/dsp_audio_path_sanitize.c")))


class Runtime(ctypes.Structure):
    _fields_ = [("dsp", DspRuntime), ("platform", U8*12), ("cache", U8*8),
                ("staged", U8*176), ("transition", U8*176)]


class GuardedRuntime(ctypes.Structure):
    _fields_ = [("before", U32*4), ("runtime", Runtime), ("after", U32*4)]


def baseline(seed=1, parameters=(0, 0, 0, 0, 0)):
    state = dsp_baseline(48000, parameters, seed)+tuple(bytearray((17*i+seed+31*j) & 255 for i in range(n))
        for j, (_, n) in enumerate(MAPPED[7:]))
    struct.pack_into("<3I", state[7], 0, 600, 0x12345678, 500)
    struct.pack_into("<2I", state[8], 0, 599, 0xA5A5A5A5)
    state[4][1], state[4][28] = 0, 1
    struct.pack_into("<I", state[4], 32, 0)
    struct.pack_into("<I", state[0], 0, 65536)
    for section in range(4):
        struct.pack_into("<5i4iI4B", state[5], section*44,
            1 << 28, 0, 0, 0, 0, 300+section, -200-section, 100+section, -50-section,
            0x23456789+section, 0, section & 1, 0xA5, 0x5A)
    return state


class CState:
    def __init__(self, memory, samples):
        self.guarded = GuardedRuntime()
        for i in range(4):
            self.guarded.before[i], self.guarded.after[i] = 0x12345678+i, 0x9ABCDEF0+i
        self.runtime = self.guarded.runtime
        self.regions = [getattr(self.runtime.dsp, name) for name, _ in DspRuntime._fields_]
        self.regions += [getattr(self.runtime, name) for name, _ in Runtime._fields_[1:]]
        for destination, raw in zip(self.regions, memory):
            ctypes.memmove(ctypes.addressof(destination), bytes(raw), len(raw))
        self.samples_count = len(samples)
        self.storage = (I32*(len(samples)+2))()
        self.storage[0], self.storage[-1] = 0x12345678, -0x12345678
        for i, value in enumerate(samples):
            self.storage[i+1] = value
        self.samples = ctypes.cast(ctypes.byref(self.storage, 4), ctypes.POINTER(I32)) if samples else None

    def snapshot(self):
        return tuple(bytes(region) for region in self.regions)

    def sample_values(self):
        return tuple(self.storage[1:-1])

    def guards_ok(self):
        return (tuple(self.guarded.before) == tuple(0x12345678+i for i in range(4))
                and tuple(self.guarded.after) == tuple(0x9ABCDEF0+i for i in range(4))
                and self.storage[0] == 0x12345678 and self.storage[-1] == -0x12345678)


def configure(library):
    runtime, samples, word = ctypes.POINTER(Runtime), ctypes.POINTER(I32), ctypes.POINTER(U32)
    signatures = {"cached": [runtime, word], "input": [runtime, word], "startup": [runtime],
        "update": [runtime], "ramp": [samples, U32, U32, U32],
        "block": [runtime, samples, U32, U32], "process": [runtime, samples, U32]}
    functions = {}
    for name, arguments in signatures.items():
        function = getattr(library, "hyperrig_dsp_audio_path_"+name)
        function.argtypes, function.restype = arguments, ctypes.c_int
        functions[name] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("verification requires assertions enabled")
    program = DspAudioPathProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, digest = dict.fromkeys(functions, 0), set(), hashlib.sha256()
    rng = random.Random(0x1C054A6)
    kernel_calls = ramp_calls = block_calls = platform_calls = dynamics_calls = producer_calls = 0
    samples_checked = carried_calls = mutations_between_calls = maximum_steps = 0

    def compare(memory, operation, samples=(), *arguments, carried=False, mutated=False):
        nonlocal kernel_calls, ramp_calls, block_calls, platform_calls, dynamics_calls, producer_calls
        nonlocal samples_checked, carried_calls, mutations_between_calls, maximum_steps
        expected = program.execute(memory, operation, samples, *arguments)
        state, out = CState(memory, samples), U32(0xA5A55A5A)
        runtime = ctypes.byref(state.runtime)
        if operation in ("cached", "input"):
            result = functions[operation](runtime, ctypes.byref(out))
            assert out.value == expected["value"], (operation, out.value, expected["value"])
        elif operation in ("startup", "update"):
            result = functions[operation](runtime)
        elif operation == "ramp":
            result = functions[operation](state.samples, len(samples), *arguments)
        else:
            result = functions[operation](runtime, state.samples, len(samples), *arguments)
        differences = [(region, [(i, a, b) for i, (a, b) in enumerate(zip(left, right)) if a != b][:12])
            for region, (left, right) in enumerate(zip(state.snapshot(), expected["memory"])) if left != right]
        assert result == 0 and not differences and state.sample_values() == expected["samples"] and state.guards_ok(), (
            operation, arguments, len(samples), result, differences,
            [(i,a,b) for i,(a,b) in enumerate(zip(state.sample_values(), expected["samples"])) if a != b][:12])
        assert not expected["boundary_calls"]
        counts[operation] += 1
        coverage.update(expected["visited"])
        kernel_calls += len(expected["kernel_calls"])
        for target, _ in expected["audio_calls"]:
            ramp_calls += target == REGIONS["ramp"][0]
            block_calls += target == REGIONS["block"][0]
            platform_calls += target == REGIONS["input"][0]
        dynamics_calls += len(expected["dynamics_calls"])
        producer_calls += len(expected["production_calls"])
        samples_checked += len(samples)
        carried_calls += carried
        mutations_between_calls += mutated
        maximum_steps = max(maximum_steps, expected["steps"])
        digest.update(operation.encode()+b"\0")
        if operation in ("cached", "input"):
            digest.update(struct.pack("<I", out.value))
        for region in expected["memory"]:
            digest.update(region)
        digest.update(struct.pack(f"<{len(samples)}i", *expected["samples"]))
        return expected

    edges = (0, 1, 2, 5, 6, 7, 359, 360, 600, 1000000, 0xFFFFFF, 0x1000000,
             0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF)
    for source in (*edges, *(rng.getrandbits(32) for _ in range(96))):
        state = baseline()
        struct.pack_into("<I", state[7], 0, source)
        struct.pack_into("<2I", state[8], 0, source ^ 1, 0xDEADBEEF)
        current = compare(state, "cached")["memory"]
        compare(current, "cached", carried=True)
        compare(current, "input", carried=True)
    for base in (0, 1, 154949, 154950, 154951, 154952, 85899345, 85899346,
                 86054295, 86054296, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for subtractand in (0, 1, (base-1)&0xFFFFFFFF, base, (base+1)&0xFFFFFFFF, 0xFFFFFFFF):
            state = baseline()
            struct.pack_into("<2I", state[8], 0, 600, base)
            struct.pack_into("<I", state[7], 8, subtractand)
            compare(state, "input")
    print("Cached integer input, saturation thresholds and wrapped products compared.", flush=True)

    for count in range(129):
        samples = tuple(signed(rng.getrandbits(32)) for _ in range(count))
        for gain, step in ((65536,0), (0x80000000,0), (0x7FFFFFFF,0), (0xFFFFFFFF,1),
                           (rng.getrandbits(32),rng.getrandbits(32))):
            compare(baseline(), "ramp", samples, gain, step)
    for sign in (-1, 1):
        for count in (1, 2, 3, 4, 5, 6, 7, 8, 9, 16):
            compare(baseline(), "ramp", (sign*0x7FFFFFFF,)*count, 0x7FFFFFFF, 0)
    compare(baseline(), "ramp", (-2147483648,2147483647), 65536, 0)
    print("All gain-kernel lengths, ramp wrap and positive/negative saturation lanes compared.", flush=True)

    for seed in range(24):
        state = baseline(seed)
        compare(state, "update")
    for count in range(1, 129):
        state = baseline(count)
        for i in range(4):
            state[5][44*i+40] = (count+i) % 3
            state[5][44*i+41] = (count+i) & 1
        gain = rng.choice((0, 65536, 131072, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF))
        struct.pack_into("<I", state[0], 0, rng.getrandbits(32))
        compare(state, "block", [signed(rng.getrandbits(32)) for _ in range(count)], gain)
    for mask in range(16):
        for residual in (0, 1, 255):
            state = baseline(mask)
            for i in range(4):
                state[5][44*i+40] = 255 if mask & (1 << i) else 0
                state[5][44*i+41] = residual
                struct.pack_into("<5I", state[5], 44*i, *(rng.getrandbits(32) for _ in range(5)))
            for count in (1, 2, 9):
                compare(state, "block", [signed(rng.getrandbits(32)) for _ in range(count)], 65536)
    for gain in (0, 1, 65535, 65536, 65537, 0x80000000, 0xFFFFFFFF):
        state = baseline()
        struct.pack_into("<I", state[0], 0, gain)
        compare(state, "block", (1,-1), gain)
    print("All four-section enable combinations, both kernels and bypass histories compared.", flush=True)

    for count in (0, 1, 2, 31, 32, 33, 63, 64, 65, 96, 127, 128):
        for gate in (0, 1, 2, 254, 255):
            for pending in (0, 1, 255):
                state = baseline(count)
                state[4][28], state[4][1] = gate, pending
                counter = rng.choice((0, 1, 2, 3, 4, 5, 0x80000000, 0xFFFFFFFF))
                for destination in (state[9], state[10]):
                    struct.pack_into("<I", destination, 172, counter)
                struct.pack_into("<I", state[4], 32, counter)
                compare(state, "process", [signed(rng.getrandbits(32)) for _ in range(count)])
    # Deliberate counters cover every chunk boundary, final exact copy, arbitrary
    # enable/residual bytes and wrapping coefficient/gain additions.
    for counter in (0, 1, 2, 3, 4, 5, 255, 1020, 0x80000000, 0xFFFFFFFF):
        for count in (1, 31, 32, 33, 63, 64, 65, 127, 128):
            state = baseline(counter)
            state[4][1] = 1
            for i in range(4):
                state[5][44*i+40], state[5][44*i+41] = i & 1, (i >> 1)*255
                state[9][168+i] = (0,1,2,255)[i]
            struct.pack_into("<I", state[9], 172, counter)
            compare(state, "process", [signed(rng.getrandbits(32)) for _ in range(count)])
    print("Pending copies, disabled gates and 32-sample transition boundaries compared.", flush=True)

    for guard in (0, 1, 127, 255):
        for source in edges:
            state = baseline(source, tuple(rng.randrange(-1280,1281) for _ in range(5)))
            state[1][0] = guard
            struct.pack_into("<I", state[7], 0, source)
            initialized = compare(state, "startup")["memory"]
            if not guard:
                compare(initialized, "process", [signed(rng.getrandbits(32)) for _ in range(128)], carried=True)
    for index in range(5):
        for parameter in (-1280, -120, -1, 0, 1, 120, 1280):
            parameters = [0]*5
            parameters[index] = parameter
            state = compare(baseline(parameters=parameters), "startup")["memory"]
            for count in (1, 33, 128):
                state = compare(state, "process", [signed(rng.getrandbits(32)) for _ in range(count)], carried=True)["memory"]
    state = compare(baseline(parameters=(10,-20,30,-40,50)), "startup")["memory"]
    for call_index in range(20):
        state = tuple(bytearray(part) for part in state)
        # Mutations occur between complete calls, never inside a native body.
        if call_index % 4 == 0:
            state[4][1] = 1
            state[9][:] = bytes(rng.getrandbits(8) for _ in range(176))
            struct.pack_into("<I", state[9], 172, 2)
        struct.pack_into("<I", state[7], 8, call_index*10000)
        state = compare(state, "input", carried=True, mutated=True)["memory"]
        state = compare(state, "process", [signed(rng.getrandbits(32)) for _ in range(65)], carried=True)["memory"]
    print("Native input-to-startup-to-sample sequences and carried transition state compared.", flush=True)

    invalid = invalid_checks(functions)
    new = {pc for start,end in REGIONS.values() for pc in program.code if start <= pc < end}
    missing = sorted(new-coverage)
    assert not missing, [hex(pc) for pc in missing]
    groups = {**{f"audio_{k}": v for k,v in REGIONS.items()},
        **{f"biquad_{k}": v for k,v in BiquadProgram.REGIONS.items()},
        **{f"dynamics_{k}": v for k,v in DYNAMICS_REGIONS.items()},
        **{f"initialization_{k}": v for k,v in INITIALIZATION_REGIONS.items()},
        **{f"math_{k}": v for k,v in MATH_REGIONS.items()},
        **{f"coefficients_{k}": v for k,v in PRIOR_REGIONS.items()}}
    app = (ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == MINI_IMAGE
        mini = unpack_app(raw)[2]["app.bin"]
        for start,end in (*groups.values(), *STATIC.values(), TABLE, (PRIOR_TABLE,PRIOR_TABLE+10), RESET_CONFIGURATION):
            assert region_bytes(mini,start,end) == region_bytes(app,start,end)
        mini_binding = {"image_sha256": MINI_IMAGE, "all_loaded_regions_identical": sorted(groups),
            "both_tables_reset_configuration_and_static_call_windows_identical": True}
    report = {"schema":1,"project":"HyperRig","result":"pass",
        "scope":"complete cached input, service-free startup and four-section sample-processing bodies",
        "original_image_sha256": PINNED_IMAGE,
        "regions": {name:{"start":start,"end_exclusive":end,"sha256":hashlib.sha256(program.audio_regions[name]).hexdigest(),
            "decoded":sum(start<=pc<end for pc in program.code),"visited":sum(start<=pc<end for pc in coverage)}
            for name,(start,end) in REGIONS.items()},
        "static_call_windows": {name:{"start":start,"end_exclusive":end,
            "sha256":hashlib.sha256(program.static[name]).hexdigest(),"executed":False} for name,(start,end) in STATIC.items()},
        "comparisons":counts,"total_comparisons":sum(counts.values()),"samples_checked":samples_checked,
        "kernel_calls":kernel_calls,"internal_gain_ramp_calls":ramp_calls,"internal_block_calls":block_calls,
        "internal_platform_input_calls":platform_calls,"internal_dynamics_calls":dynamics_calls,
        "complete_coefficient_producer_calls":producer_calls,"scripted_service_calls":0,
        "carried_calls":carried_calls,"between_call_mutations":mutations_between_calls,
        "maximum_instruction_packets":maximum_steps,"invalid_api_checks":invalid,
        "instruction_coverage":{"new_visited":len(new&coverage),"new_decoded":len(new),
            "all_visited":len(coverage),"all_decoded":len(program.code),"unvisited_new":missing},
        "compared":["all 11 runtime regions and sample words", "cached/input return words",
            "native startup then processing on identical carried state", "guards and rejection before writes"],
        "outputs_and_state_sha256":digest.hexdigest(),"mini_v4_binding":mini_binding,
        "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "library_sha256":hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test":False,"audio_test":False,"firmware_changed":False,
        "limitations":["0..128 samples; direct block requires 1..128; samples/runtime disjoint",
            "five stored startup parameters remain bounded to +/-1280 when guard is zero",
            "staged transition records are fixture inputs; their parameter-request producer is not executed here",
            "physical platform-word writers, audio task, dynamics sample processor and callback token execution remain outside scope",
            "existing ISA and binary32 semantics remain shared assumptions, not a new hardware measurement",
            "startup/process C status is new; incidental native return registers are not API results"]}
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("result","comparisons","total_comparisons","instruction_coverage")}))
    return report


def invalid_checks(functions):
    state = CState(baseline(), (1,-1))
    runtime, out = ctypes.byref(state.runtime), U32(0xA5A55A5A)
    invalid = [(name,(None,ctypes.byref(out))) for name in ("cached","input")]
    invalid += [(name,(runtime,None)) for name in ("cached","input")]
    invalid += [("startup",(None,)),("update",(None,)),("ramp",(None,1,0,0)),
        ("ramp",(state.samples,129,0,0)),("block",(None,state.samples,2,0)),
        ("block",(runtime,None,2,0)),("block",(runtime,state.samples,0,0)),
        ("block",(runtime,state.samples,129,0)),("process",(None,state.samples,2)),
        ("process",(runtime,None,1)),("process",(runtime,state.samples,129))]
    for name,args in invalid:
        before = state.snapshot()
        assert functions[name](*args) == -1 and state.snapshot() == before
        assert state.sample_values() == (1,-1) and out.value == 0xA5A55A5A and state.guards_ok()
    count = len(invalid)
    for index in range(5):
        for value in (-32768,-1281,1281,32767):
            memory = baseline()
            struct.pack_into("<h",memory[4],218+2*index,value)
            state = CState(memory,())
            assert functions["startup"](ctypes.byref(state.runtime)) == -1
            assert state.snapshot() == tuple(map(bytes,memory)) and state.guards_ok()
            count += 1
    assert functions["ramp"](None,0,0,0) == 0
    return count


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mini-image",type=Path)
    args=parser.parse_args()
    if args.output.exists(): parser.error("preserve completed reports; choose a new output path")
    verify(args.library,args.output,args.mini_image)
