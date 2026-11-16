"""Compare reconstructed controls with original instructions and scripted leaves."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from control_action_machine import (ControlActionProgram, GLOBAL, STATE, OWNER,
                                    REGIONS, SERVICES, ROOT)
from verify_controls import Context, context_from


class Runtime(ctypes.Structure):
    _fields_ = [("controls", Context), ("tail", ctypes.c_uint8 * 2)]


SERVICE_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                                   ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32)


def runtime_from(memory):
    globals_, state, owner = memory
    return Runtime(context_from(globals_[:270], state, owner),
                   (ctypes.c_uint8 * 2).from_buffer_copy(globals_[270:]))


def snapshot(runtime):
    return (bytes(runtime.controls.global_) + bytes(runtime.tail),
            bytes(runtime.controls.state), runtime.controls.owner)


def baseline():
    globals_, state = bytearray(272), bytearray(1860)
    globals_[116:120] = bytes(range(4))
    state[74] = 1
    return globals_, state, 0


class CMemory:
    def __init__(self, runtime):
        self.runtime = runtime

    def write(self, address, value, size):
        for i, byte in enumerate(value.to_bytes(size, "little")):
            at = address + i
            if GLOBAL <= at < GLOBAL + 270:
                self.runtime.controls.global_[at - GLOBAL] = byte
            elif GLOBAL + 270 <= at < GLOBAL + 272:
                self.runtime.tail[at - GLOBAL - 270] = byte
            elif STATE <= at < STATE + 1860:
                self.runtime.controls.state[at - STATE] = byte
            elif at == OWNER:
                self.runtime.controls.owner = byte
            else:
                raise ValueError("scripted service escaped initialized RAM")


def scripted(plan, service, args, memory):
    # Same supplied boundary behavior on each side; no preset/effect simulation.
    result, writes = plan.get(service, (0, ()))
    for address, value, width in writes:
        memory.write(address, value, width)
    return result


def configure(library):
    signatures = {
        "action": [ctypes.c_uint, ctypes.c_uint],
        "tick": [ctypes.c_uint32],
        "edge": [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint32, ctypes.c_uint32],
    }
    functions = {}
    for name, args in signatures.items():
        function = getattr(library, "hyperrig_controls_" + name)
        function.argtypes = [ctypes.POINTER(Runtime), *args, SERVICE_CALLBACK, ctypes.c_void_p]
        function.restype = ctypes.c_int
        functions[name] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("verification must run without Python optimization")
    native = ControlActionProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts = {"action": 0, "tick": 0, "edge": 0, "sequence_steps": 0,
              "mutating_boundaries": 0, "invalid_api": 0}
    coverage, service_coverage = set(), set()
    rng = random.Random(0x149B614B)

    def compare(memory, operation, *args, plan=None, sequence=False):
        plan = plan or {}
        original = native.execute(*memory, operation, *args,
            boundary=lambda service, argv, machine: scripted(plan, service, argv, machine))
        runtime = runtime_from(memory)
        calls, errors = [], []
        def service_callback(_opaque, service, a, b, c):
            try:
                calls.append((service, (a, b, c), snapshot(runtime)))
                return scripted(plan, service, (a, b, c), CMemory(runtime))
            except Exception as error:
                errors.append(error)
                return 0
        callback = SERVICE_CALLBACK(service_callback)
        result = functions[operation](ctypes.byref(runtime), *args, callback, None)
        if errors:
            raise errors[0]
        if result != 0 or snapshot(runtime) != original["memory"] or calls != original["calls"]:
            differences = [[i for i, (a, b) in enumerate(zip(x, y)) if a != b][:16]
                           for x, y in zip(snapshot(runtime)[:2], original["memory"][:2])]
            raise AssertionError(f"Control action mismatch: {counts}, {operation}, {args}, "
                                 f"byte differences={differences}, "
                                 f"C calls={[x[:2] for x in calls]}, "
                                 f"native calls={[x[:2] for x in original['calls']]}")
        coverage.update(original["visited"])
        service_coverage.update(call[0] for call in calls)
        counts[operation] += 1
        counts["sequence_steps"] += int(sequence)
        counts["mutating_boundaries"] += int(any(writes for _, writes in plan.values()))
        return snapshot(runtime)

    # Every action byte, event and logical slot, including the two tail bytes.
    for logical in range(4):
        for event in range(3):
            for action in range(256):
                memory = baseline()
                globals_, state, _ = memory
                offset = 236 + logical * 9 + event * 3
                globals_[offset:offset + 3] = bytes((action, (action * 7) & 255, action & 3))
                struct.pack_into("<I", globals_, 24, 0xFFFFFFF0 + event)
                struct.pack_into("<I", state, 956, 1 if action & 1 else 0)
                struct.pack_into("<H", state, 1608 + logical * 2, 1000 if event == 1 else 0)
                struct.pack_into("<I", state, 1828 + logical * 4, 0x12345678)
                struct.pack_into("<I", state, 1844 + logical * 4, 0xFEDCBA98)
                compare(memory, "action", logical, event)

    # Control every leaf return branch and auxiliary-byte boundary.
    values = (0, 1, 3, 4, 255, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)
    for action in range(1, 11):
        for result in values:
            for auxiliary in (0, 3, 4, 255):
                for event in range(3):
                    globals_, state, owner = baseline()
                    offset = 236 + 27 + event * 3
                    globals_[offset:offset + 3] = bytes((action, 255, auxiliary))
                    state[52] = result & 255
                    plan = {service: (result, ()) for service in SERVICES}
                    compare((globals_, state, owner), "action", 3, event, plan=plan)

    # Timer cutoffs, 16-bit inputs, unsigned addition/capping and duplicate maps.
    timers = (0, 299, 300, 301, 998, 999, 1000, 59999, 60000, 65535)
    deltas = (0, 1, 2, 300, 301, 999, 1000, 60000, 0xFFFF0001, 0xFFFFFFFF)
    for initial in timers:
        for delta in deltas:
            for flags in range(16):
                globals_, state, owner = baseline()
                if flags & 8:
                    globals_[116:120] = bytes((0, 0, 0, 0))
                for logical in range(4):
                    globals_[239 + logical * 9] = (0, 7, 9, 255)[logical]
                    state[1567 + logical] = flags & 1
                    state[932 + logical] = (flags >> 1) & 1
                    state[964 + logical] = (flags >> 2) & 1
                    struct.pack_into("<H", state, 1608 + logical * 2, initial)
                    struct.pack_into("<H", state, 1616 + logical * 2, initial)
                compare((globals_, state, owner), "tick", delta)

    # Preserve unrelated initialized bytes, arbitrary mapping bytes and owners.
    for case in range(2400):
        globals_, state = bytearray(rng.randbytes(272)), bytearray(rng.randbytes(1860))
        globals_[116:120] = bytes(rng.choice((0, 1, 2, 3, 4, 255)) for _ in range(4))
        state[74] = int(case % 7 != 0)
        for logical in range(4):
            for flag in (932, 960, 964, 1567):
                state[flag + logical] = rng.randrange(2)
            for event in range(3):
                globals_[236 + logical * 9 + event * 3] = rng.randrange(11)
        operation = ("action", "tick", "edge")[case % 3]
        args = {"action": (rng.randrange(4), rng.randrange(3)),
                "tick": (rng.getrandbits(32),),
                "edge": (rng.randrange(5), rng.randrange(2), rng.getrandbits(32), rng.getrandbits(32))}[operation]
        plan = {service: (rng.choice(values), ()) for service in SERVICES}
        compare((globals_, state, rng.randrange(256)), operation, *args, plan=plan)

    # Callback writes test re-reads, captured pointers and snapshot ordering.
    scenarios = [
        (1, {0x02002D10: (0, ((GLOBAL + 24, 1234, 4), (GLOBAL + 236, 9, 1),
                             (STATE + 1828, 0xABCDEF01, 4), (STATE + 52, 9, 1)))}),
        (1, {0x020148BA: (0, ((STATE + 956, 0, 4), (GLOBAL + 236, 2, 1),
                             (GLOBAL + 237, 19, 1))), 0x0200CF88: (1, ())}),
        (2, {0x0200CF88: (1, ((GLOBAL + 237, 31, 1),)),
             0x0200CA7E: (0, ((GLOBAL + 238, 3, 1),))}),
        (8, {0x0201499C: (0xFFFFFFFF, ((GLOBAL + 237, 11, 1), (GLOBAL + 238, 255, 1)))}),
    ]
    for action, plan in scenarios:
        memory = baseline()
        memory[0][236:239] = bytes((action, 5, 4))
        struct.pack_into("<I", memory[1], 956, 1)
        compare(memory, "action", 0, 0, plan=plan)
    memory = baseline()
    memory[0][239] = 9
    memory[1][1567] = 1
    compare(memory, "tick", 1000, plan={0x02002D10: (0, (
        (STATE + 1567, 0, 1), (STATE + 964, 1, 1), (GLOBAL + 116, 1, 1)))})

    # Integrated edge -> timer -> dispatcher sequences, with prior state retained.
    for mode in range(8):
        memory = baseline()
        memory[0][11] = 15 if mode & 1 else 0
        for logical in range(4):
            memory[0][236 + logical * 9:245 + logical * 9] = bytes(
                (9, 0, 0, 7 if mode & 2 else 0, 0, 0, 8 if mode & 4 else 0, 0, 255))
        for i in range(256):
            globals_, state, owner = memory
            globals_ = bytearray(globals_)
            struct.pack_into("<I", globals_, 24, i * 10)
            memory = (globals_, state, owner)
            if i % 3 == 0:
                memory = compare(memory, "tick", (0, 300, 301, 999, 1000)[(i // 3) % 5], sequence=True)
            else:
                memory = compare(memory, "edge", (i // 8) % 4, i % 2, i * 100, i * 100, sequence=True)

    # Force both repeat-window outcomes, including wraparound and equality.
    for logical in range(4):
        for now, deadline in ((0xFFFFFFFE, 0), (100, 100), (99, 100), (101, 100)):
            memory = baseline()
            struct.pack_into("<I", memory[1], 1508, deadline)
            memory = memory[0], memory[1], logical + 1
            compare(memory, "edge", logical, 1, 33, now)

    callback = SERVICE_CALLBACK(lambda *_: 0)
    invalid = [("action", (4, 0)), ("action", (0, 3)), ("action", (0xFFFFFFFF, 0)),
               ("edge", (5, 0, 0, 0)), ("edge", (0, 2, 0, 0))]
    for operation, args in invalid:
        runtime = runtime_from(baseline())
        before = snapshot(runtime)
        calls = []
        recorder = SERVICE_CALLBACK(lambda *args: calls.append(args) or 0)
        assert functions[operation](ctypes.byref(runtime), *args, recorder, None) == -1
        assert snapshot(runtime) == before and not calls
        counts["invalid_api"] += 1
    for operation, args in (("action", (0, 0)), ("tick", (1,)), ("edge", (0, 1, 0, 0))):
        assert functions[operation](None, *args, callback, None) == -1
        runtime = runtime_from(baseline())
        before = snapshot(runtime)
        assert functions[operation](ctypes.byref(runtime), *args, SERVICE_CALLBACK(), None) == -1
        assert snapshot(runtime) == before
        counts["invalid_api"] += 2

    new_code = set(native.code) - set(native.controls.code)
    missing = sorted(new_code - coverage)
    assert not missing, [hex(address) for address in missing]
    assert service_coverage == set(SERVICES)
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        image = mini_image.read_bytes()
        image_hash = hashlib.sha256(image).hexdigest()
        if image_hash != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI input is not the reviewed v4 application")
        app = unpack_app(image)[2]["app.bin"]
        for name, (start, end) in REGIONS.items():
            if app[start - 0x02000120:end - 0x02000120] != native.raw_regions[name]:
                raise ValueError(f"MINI {name} region differs from the G reference")
        for region in (native.controls.transition, native.controls.immediate):
            if app[region.start - 0x02000120:region.end - 0x02000120] != region.raw:
                raise ValueError("MINI transition/policy region differs")
        mini_binding = {"image_sha256": image_hash, "all_five_regions_byte_identical": True}

    sources = ("firmware/src/hyperrig_control_actions.c", "firmware/include/hyperrig/hyperrig_control_actions.h",
               "firmware/src/hyperrig_controls.c", "firmware/include/hyperrig/hyperrig_controls.h",
               "tools/control_action_machine.py", "tools/control_machine.py", "tools/dot_machine.py",
               "tools/verify_control_actions.py", "tools/verify_controls.py", "tools/build_control_actions.py",
               "tests/test_control_action_machine.py", "upstream/pi32v2-isa/pi32v2isa/codec.py",
               "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml")
    report = {
        "schema": 1, "result": "pass", "project": "HyperRig",
        "scope": "action selection, timer worker and integrated transitions with scripted external services",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
                     "bytes_sha256": hashlib.sha256(native.raw_regions[name]).hexdigest()}
                     for name, (start, end) in REGIONS.items()},
        "comparisons": counts,
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
                                 "all_visited": len(coverage), "all_decoded": len(native.code),
                                 "unvisited_new": missing},
        "external_services_visited": [SERVICES[address][0] for address in sorted(service_coverage)],
        "compared": ["272 global bytes", "1860 state bytes", "repeat owner",
                     "ordered semantic service arguments and complete state at each boundary"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding,
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["restricted interpreter semantics", "scripted leaf services, not original leaf execution",
                        "no scheduling, IRQ concurrency, peripheral, transport or physical time-unit validation",
                        "four logical slots retained; no backport or three-switch bank change"],
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "pass", "comparisons": counts, "instruction_coverage": report["instruction_coverage"]}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing reports; choose a new output path")
    verify(args.library, args.output, args.mini_image)
