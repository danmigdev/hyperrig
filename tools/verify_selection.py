"""Compare recovered selection C with original instructions and explicit I/O scripts."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from selection_machine import (SelectionProgram, REGIONS, LEAF_SERVICES, ROOT,
                               GLOBAL, STATE, EFFECTS, EXTRA_ADDRESSES)
from control_action_machine import REGIONS as ACTION_REGIONS
from verify_control_actions import (Runtime, SERVICE_CALLBACK, CMemory as ControlMemory,
                                    runtime_from as control_from, snapshot as control_snapshot)

EXISTS, LOAD, CLOCK, APPLY, REPORT, SET_EFFECT = (
    0x0200CF88, 0x0200CA7E, 0x01C04862, 0x0200A1D6, 0x0200A228, 0x0200D060)


class Selection(ctypes.Structure):
    _fields_ = [("controls", Runtime), ("scenes", ctypes.c_uint8 * 4),
                ("counts", ctypes.c_uint8 * 2), ("order", ctypes.c_uint8 * 20),
                ("headers", ctypes.c_uint8 * 48)]


def baseline():
    globals_, state = bytearray(272), bytearray(1860)
    globals_[116:120] = bytes(range(4))
    state[74] = 1
    return globals_, state, 0, bytearray((1, 1, 1, 1)), bytearray(2), bytearray(20), bytearray(48)


def from_memory(memory):
    arrays = [(ctypes.c_uint8 * size).from_buffer_copy(value)
              for size, value in zip((4, 2, 20, 48), memory[3:])]
    return Selection(control_from(memory[:3]), *arrays)


def snapshot(context):
    return control_snapshot(context.controls) + tuple(bytes(getattr(context, field))
                                                     for field in ("scenes", "counts", "order", "headers"))


class CMemory(ControlMemory):
    def __init__(self, selection):
        super().__init__(selection.controls)
        self.extra = {address: (getattr(selection, field), i)
                      for field, addresses in zip(("scenes", "counts", "order", "headers"), EXTRA_ADDRESSES)
                      for i, address in enumerate(addresses)}

    def write(self, address, value, size):
        for i, byte in enumerate(value.to_bytes(size, "little")):
            if address + i in self.extra:
                array, index = self.extra[address + i]
                array[index] = byte
            else:
                super().write(address + i, byte, 1)


def scripted(plan, service, arguments, memory):
    """Supplied leaf behavior only; callbacks do not model the recovered code."""
    result, writes = plan.get((service, arguments[0]), plan.get(service, (0, ())))
    for address, value, width in writes:
        memory.write(address(arguments) if callable(address) else address,
                     value(arguments) if callable(value) else value, width)
    return result(arguments) if callable(result) else result


def preset_plan(available=0xFFFFFFFF, failed=0):
    return {EXISTS: (lambda args: int(args[0] < 32 and bool(available & (1 << args[0]))), ()),
            LOAD: (lambda args: int(args[0] >= 32 or bool(failed & (1 << args[0]))), ())}


def configure(library):
    functions = {}
    signatures = {"preset_step": ("step_preset", [ctypes.c_uint32]),
                  "scene_flush": ("flush_scenes", []), "scene": ("scene", [ctypes.c_uint32]),
                  "action": ("action", [ctypes.c_uint, ctypes.c_uint]),
                  "tick": ("tick", [ctypes.c_uint32]),
                  "edge": ("edge", [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint32, ctypes.c_uint32]),
                  "resolve": ("resolve_effect", [ctypes.c_uint])}
    for operation, (name, arguments) in signatures.items():
        function = getattr(library, "hyperrig_selection_" + name)
        function.argtypes = [ctypes.POINTER(Selection), *arguments]
        if operation != "resolve":
            function.argtypes += [SERVICE_CALLBACK, ctypes.c_void_p]
        function.restype = ctypes.c_int
        functions[operation] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    native = SelectionProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts = {name: 0 for name in functions}
    coverage, service_coverage = set(), set()
    subsets = {"sequence_steps": 0, "scripted_mutation_cases": 0}
    rng = random.Random(0x14952499)

    def compare(memory, operation, *arguments, plan=None, sequence=False):
        plan = plan or {}
        original = native.execute(*memory, operation, *arguments,
            boundary=lambda service, args, view: scripted(plan, service, args, view))
        context = from_memory(memory)
        calls, errors = [], []
        def callback(_opaque, service, a, b, c):
            try:
                calls.append((service, (a, b, c), snapshot(context)))
                return scripted(plan, service, (a, b, c), CMemory(context))
            except Exception as error:
                errors.append(error)
                return 0
        record = SERVICE_CALLBACK(callback)
        args = [ctypes.byref(context), *arguments]
        if operation != "resolve":
            args += [record, None]
        actual = functions[operation](*args)
        if errors:
            raise errors[0]
        expected_result = original["result"] if operation == "resolve" else 0
        if ((actual & 0xFFFFFFFF) != expected_result or snapshot(context) != original["memory"]
                or calls != original["calls"]):
            raise AssertionError(f"Selection mismatch: {counts}, {operation}, {arguments}; "
                                 f"result={actual}/{expected_result}; "
                                 f"memory_equal={snapshot(context) == original['memory']}; "
                                 f"C calls={[item[:2] for item in calls]}; "
                                 f"native calls={[item[:2] for item in original['calls']]}")
        counts[operation] += 1
        subsets["sequence_steps"] += int(sequence)
        subsets["scripted_mutation_cases"] += int(any(writes for _, writes in plan.values()))
        coverage.update(original["visited"])
        service_coverage.update(call[0] for call in calls)
        return snapshot(context)

    # Every current/target pair in both normal directions; only that target exists.
    for current in range(32):
        for target in range(32):
            for step in (1, 0xFFFFFFFF):
                memory = baseline()
                struct.pack_into("<I", memory[0], 92, current)
                compare(memory, "preset_step", step, plan=preset_plan(1 << target))
    # Empty/sparse/full availability, failed loads, fallback and wrapped signed math.
    for current in (0, 15, 31, 32, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for step in (0, 1, 2, 31, 32, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            for available, failed in ((0, 0), (0xFFFFFFFF, 0xFFFFFFFF), (0x80000003, 3),
                                      (0xAAAAAAAA, 0x88888888)):
                memory = baseline()
                struct.pack_into("<I", memory[0], 92, current)
                compare(memory, "preset_step", step, plan=preset_plan(available, failed))

    # All scene availability masks, including no current scene and both directions.
    steps = (-64, -5, -4, -2, -1, 0, 1, 2, 4, 5, 64)
    for mask in range(16):
        for current in (0, 1, 2, 3, 0xFFFFFFFF, 0x80000000):
            for step in steps:
                for suppressed in (0, 255):
                    memory = baseline()
                    memory[3][:] = bytes((mask >> i) & 1 for i in range(4))
                    memory[1][740] = suppressed
                    struct.pack_into("<I", memory[0], 88, current)
                    struct.pack_into("<I", memory[1], 956, step & 0xFFFFFFFF)
                    compare(memory, "scene_flush", plan={CLOCK: (0xFFFFFFFE, ()),
                            APPLY: (0xABCDEF12, ()), REPORT: (0x12345678, ())})
        for scene in (0, 1, 2, 3, 4, 255, 0xFFFFFFFF):
            memory = baseline()
            memory[3][:] = bytes((mask >> i) & 1 for i in range(4))
            compare(memory, "scene", scene)
    for step in (0x7FFFFFFF, 0x80000000, 0x80000001):
        memory = baseline()
        memory[3][:] = bytes(4)
        struct.pack_into("<I", memory[1], 956, step)
        compare(memory, "scene_flush")

    # Full two-chain view includes repeated types, missing headers and invalid IDs.
    def populated():
        memory = baseline()
        memory[4][:] = bytes((10, 10))
        memory[5][:] = bytes((0, 1, 2, 255, 3, 4, 5, 6, 7, 8,
                             9, 10, 11, 12, 13, 14, 15, 0, 1, 2))
        for index in range(16):
            memory[6][3 * index:3 * index + 3] = bytes((5 if index % 2 else 7, index & 1, int(index != 4)))
        return memory
    for record in range(236, 270, 3):
        for argument in range(256):
            for auxiliary in (0, 255):
                memory = populated()
                memory[0][record:record + 3] = bytes((8, argument, auxiliary))
                compare(memory, "resolve", record)
    for occurrence in range(256):
        memory = populated()
        memory[0][269:272] = bytes((8, 5, occurrence))
        compare(memory, "resolve", 269)
    for first in range(11):
        for second in range(11):
            for argument, auxiliary in ((0, 0), (5, 1), (0, 255), (15, 255), (16, 255)):
                memory = populated()
                memory[4][:] = bytes((first, second))
                memory[0][236:239] = bytes((8, argument, auxiliary))
                compare(memory, "resolve", 236)

    # Independent randomized RAM protects unrelated state and exercises integration.
    operations = tuple(counts)
    for case in range(2100):
        memory = list(baseline())
        memory[0] = bytearray(rng.randbytes(272))
        memory[1] = bytearray(rng.randbytes(1860))
        memory[2] = rng.randrange(256)
        memory[3][:] = bytes(rng.choice((0, 1, 255)) for _ in range(4))
        memory[4][:] = bytes(rng.randrange(11) for _ in range(2))
        memory[5][:] = bytes(rng.choice((*range(16), 16, 255)) for _ in range(20))
        memory[6][:] = rng.randbytes(48)
        struct.pack_into("<I", memory[0], 88, rng.choice((0, 1, 2, 3, 0xFFFFFFFF)))
        struct.pack_into("<I", memory[1], 956, rng.randrange(-8, 9) & 0xFFFFFFFF)
        memory[0][116:120] = bytes(rng.randrange(5) for _ in range(4))
        memory[1][74] = int(case % 9 != 0)
        memory[1][740] = rng.randrange(2)
        for logical in range(4):
            for event in range(3):
                record = 236 + logical * 9 + event * 3
                memory[0][record:record + 3] = bytes((rng.randrange(11), rng.randrange(16), rng.choice((0, 1, 3, 255))))
            for flag in (932, 960, 964, 1567):
                memory[1][flag + logical] = rng.randrange(2)
        operation = operations[case % len(operations)]
        arguments = {"preset_step": (rng.choice((1, 0xFFFFFFFF)),), "scene_flush": (),
                     "scene": (rng.randrange(6),), "resolve": (236 + 3 * rng.randrange(12),),
                     "action": (rng.randrange(4), rng.randrange(3)), "tick": (rng.getrandbits(32),),
                     "edge": (rng.randrange(5), rng.randrange(2), rng.getrandbits(32), rng.getrandbits(32))}[operation]
        plan = preset_plan(rng.getrandbits(32), rng.getrandbits(32))
        plan.update({CLOCK: (rng.getrandbits(32), ()), APPLY: (rng.getrandbits(32), ()),
                     REPORT: (rng.getrandbits(32), ()), 0x0200733E: (case % 2, ()), 0x02008CA2: (1, ())})
        compare(memory, operation, *arguments, plan=plan)

    # Re-read suppression after apply; preserve the original clock across callbacks.
    for suppressed in (0, 1):
        memory = baseline()
        memory[1][740] = 1 - suppressed
        compare(memory, "scene", 2, plan={CLOCK: (77, ()),
                APPLY: (31, ((STATE + 740, suppressed, 1), (GLOBAL + 88, 2, 4))),
                REPORT: (0xF00, ((STATE + 740, 0, 1),))})
    # A failed load cannot replace the navigator's locally captured candidate.
    memory = baseline()
    compare(memory, "preset_step", 1, plan={EXISTS: (1, ()),
            LOAD: (lambda args: int(args[0] != 3), ((GLOBAL + 92, 17, 4),))})

    # Consecutive controls use handler-supplied state updates. These updates are
    # test scripts, not proof of deserialization, storage writes or DSP application.
    plan = preset_plan()
    plan[LOAD] = (0, ((GLOBAL + 92, lambda args: args[0], 4),))
    plan[APPLY] = (13, ((GLOBAL + 88, lambda args: args[0], 4),))
    plan[SET_EFFECT] = (0, ((lambda args: EFFECTS + 480 * args[0] + 1, lambda args: args[1], 1),))
    for mode in range(4):
        memory = populated()
        memory[4][:] = bytes((2, 2))
        memory[5][:] = bytes(20)
        for logical, action in enumerate((3, 4, 5, 8)):
            memory[0][236 + logical * 9:245 + logical * 9] = bytes((action, 0, 255, 1, 1, 0, 6, 0, 0))
        memory[0][11] = 15 if mode & 1 else 0
        for i in range(256):
            memory = list(memory)
            memory[0] = bytearray(memory[0])
            struct.pack_into("<I", memory[0], 24, i * 10)
            if i % 3 == 0:
                memory = compare(memory, "tick", (1, 301, 1000)[(i // 3) % 3], plan=plan, sequence=True)
            else:
                memory = compare(memory, "edge", (i // 8) % 4, i % 2, i * 100, i * 100, plan=plan, sequence=True)

    # Large counters use the proven active-scene cycle reduction in C. The
    # original instruction loop is intentionally not accelerated in the oracle.
    # Hand-calculated cases separately check the saturated INT32_MIN magnitude.
    extreme_cases = [(0x7FFFFFFF, (1, 1, 1, 1), 3), (0x80000000, (1, 1, 1, 1), 1),
                     (0x80000001, (1, 1, 1, 1), 1), (0x80000000, (1, 1, 0, 1), 3)]
    for steps, scenes, expected in extreme_cases:
        memory = baseline()
        memory[3][:] = bytes(scenes)
        struct.pack_into("<I", memory[1], 956, steps)
        context, calls = from_memory(memory), []
        callback = SERVICE_CALLBACK(lambda _opaque, service, a, b, c: calls.append((service, a, b, c)) or 0)
        assert functions["scene_flush"](ctypes.byref(context), callback, None) == 0
        assert next(call[1] for call in calls if call[0] == APPLY) == expected
        assert bytes(context.controls.controls.state[956:960]) == bytes(4)

    invalid_checks = 0
    valid_arguments = {"preset_step": (1,), "scene_flush": (), "scene": (0,), "resolve": (236,),
                       "action": (0, 0), "tick": (1,), "edge": (0, 1, 0, 0)}
    for operation, arguments in valid_arguments.items():
        for bad in ("null", "chain0", "chain1", "scene"):
            memory = baseline()
            if bad.startswith("chain"):
                memory[4][int(bad[-1])] = 11
            if bad == "scene":
                struct.pack_into("<I", memory[0], 88, 4)
            context = from_memory(memory)
            before, calls = snapshot(context), []
            callback = SERVICE_CALLBACK(lambda *args: calls.append(args) or 0)
            params = [None if bad == "null" else ctypes.byref(context), *arguments]
            if operation != "resolve":
                params += [callback, None]
            assert functions[operation](*params) == (-2 if operation == "resolve" else -1)
            assert snapshot(context) == before and not calls
            invalid_checks += 1
        if operation != "resolve":
            context = from_memory(baseline())
            before = snapshot(context)
            assert functions[operation](ctypes.byref(context), *arguments, SERVICE_CALLBACK(), None) == -1
            assert snapshot(context) == before
            invalid_checks += 1
    for operation, arguments in (("action", (4, 0)), ("action", (0, 3)),
                                 ("edge", (5, 1, 0, 0)), ("edge", (0, 2, 0, 0)),
                                 ("resolve", (235,)), ("resolve", (237,)), ("resolve", (270,))):
        context = from_memory(baseline())
        before, calls = snapshot(context), []
        callback = SERVICE_CALLBACK(lambda *args: calls.append(args) or 0)
        params = [ctypes.byref(context), *arguments]
        if operation != "resolve":
            params += [callback, None]
        assert functions[operation](*params) == (-2 if operation == "resolve" else -1)
        assert snapshot(context) == before and not calls
        invalid_checks += 1

    new_code = set(native.code) - native.previous_code
    missing = sorted(new_code - coverage)
    assert not missing, [hex(address) for address in missing]
    assert service_coverage == set(LEAF_SERVICES), [hex(address) for address in set(LEAF_SERVICES) - service_coverage]
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI input is not the reviewed v4 application")
        app = unpack_app(raw)[2]["app.bin"]
        for regions, raw_regions in ((REGIONS, native.selection_regions), (ACTION_REGIONS, native.raw_regions)):
            for name, (start, end) in regions.items():
                if app[start - 0x02000120:end - 0x02000120] != raw_regions[name]:
                    raise ValueError(f"MINI {name} differs from the G reference")
        for region in (native.controls.transition, native.controls.immediate):
            if app[region.start - 0x02000120:region.end - 0x02000120] != region.raw:
                raise ValueError("MINI transition/policy differs")
        mini_binding = {"image_sha256": digest, "all_fourteen_regions_byte_identical": True}
    sources = ["firmware/src/hyperrig_selection.c", "firmware/include/hyperrig/hyperrig_selection.h",
               "tools/selection_machine.py", "tools/verify_selection.py", "tools/build_selection.py",
               "tests/test_selection_machine.py", "tools/control_action_machine.py", "tools/control_machine.py",
               "tools/dot_machine.py", "tools/verify_control_actions.py", "tools/verify_controls.py",
               "firmware/src/hyperrig_control_actions.c", "firmware/include/hyperrig/hyperrig_control_actions.h",
               "firmware/src/hyperrig_controls.c", "firmware/include/hyperrig/hyperrig_controls.h",
               "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
               "upstream/pi32v2-isa/isa/pi32v2.toml", "upstream/pi32v2-isa/tools/hwtest/semantics/q.py",
               "upstream/pi32v2-isa/tools/hwtest/semantics/s.py"]
    report = {
        "schema": 1, "result": "pass", "project": "HyperRig",
        "scope": "preset navigation, scene selection, effect binding and integrated controls with scripted I/O leaves",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
                      "bytes_sha256": hashlib.sha256(native.selection_regions[name]).hexdigest()}
                      for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "subsets": subsets,
        "invalid_api_checks": invalid_checks, "hand_calculated_extreme_counter_checks": len(extreme_cases),
        "instruction_coverage": {"new_visited": len(coverage & new_code), "new_decoded": len(new_code),
                                 "all_visited": len(coverage), "all_decoded": len(native.code),
                                 "unvisited_new": missing},
        "external_services_visited": [LEAF_SERVICES[address][0] for address in sorted(service_coverage)],
        "compared": ["272 global bytes", "1860 state bytes", "repeat owner", "4 scene availability bytes",
                     "2 chain counts and 20 order bytes", "48 effect header bytes", "binding result",
                     "ordered semantic leaf arguments and all mapped bytes at each call"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["restricted instruction semantics", "storage/availability/load and scene application remain I/O leaves",
                        "no preset deserialization, persistence, DSP application, IRQs or hardware execution",
                        "scene loops compared for bounded magnitudes; extreme active-scene counters checked separately",
                        "chain counts above ten and nonnegative current scenes above three rejected at new API boundary",
                        "four logical controls retained; Alpha 13 and three-switch bank changes not implemented"],
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "total_comparisons", "comparisons", "instruction_coverage")}))
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
