"""Compare reconstructed loader orchestration with original instructions."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from preset_loader_machine import (PresetLoaderProgram, REGIONS, APPLY, SAVED, COUNTER,
                                  GLOBAL, STATE, ROOT)
from preset_preflight_machine import REGIONS as PREFLIGHT_REGIONS, LIBRARY_REGIONS, CURVE
from preset_storage_machine import REGIONS as STORAGE_REGIONS, STORAGE_LEAVES, READ, PREPARE, PRIORITY
from selection_machine import REGIONS as SELECTION_REGIONS
from control_action_machine import REGIONS as ACTION_REGIONS
from verify_preset_preflight import (Runtime as PresetRuntime, CState as PreflightState,
    CMemory as PreflightMemory, baseline as preflight_baseline, record, payload_case, Flash,
    IO as StorageIO, SERVICE_CALLBACK, READ_CALLBACK, scripted)

CLOCK, NOTIFY = 0x01C04862, 0x02002D10
APPLY_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                                ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32))


class Runtime(ctypes.Structure):
    _fields_ = [("preset", PresetRuntime), ("saved", ctypes.c_uint8 * 36), ("counter", ctypes.c_uint8 * 4)]


class IO(ctypes.Structure):
    _fields_ = [("storage", StorageIO), ("apply", APPLY_CALLBACK)]


def baseline():
    memory = preflight_baseline() + (bytearray(36), bytearray(4))
    struct.pack_into("<I", memory[0], 44, 240)
    memory[10][0] = 0
    return memory


def route(memory, ids, types=None, second=()):
    memory[4][:] = bytes((len(ids), len(second)))
    memory[5][:len(ids)] = bytes(ids)
    memory[5][10:10 + len(second)] = bytes(second)
    for slot, type_id in (types or {i: 6 if i % 2 else 24 for i in range(16)}).items():
        memory[6][3 * slot:3 * slot + 3] = bytes((type_id, 1, 1))


class Script:
    """Per-call service fixtures; no implementation of the application service."""
    def __init__(self, plan=None, clocks=(100, 500, 600, 1000)):
        self.plan, self.clocks, self.counts = plan or {}, clocks, {}

    def __call__(self, service, args, memory):
        ordinal = self.counts.get(service, 0) + 1
        self.counts[service] = ordinal
        selected = self.plan.get((service, "call", ordinal))
        if selected is not None:
            return scripted({service: selected}, service, args, memory)
        if service == CLOCK and service not in self.plan and (service, args[0]) not in self.plan:
            return self.clocks[ordinal - 1] if ordinal <= len(self.clocks) else (self.clocks[-1] + 1000 * (ordinal - len(self.clocks))) & 0xFFFFFFFF
        return scripted(self.plan, service, args, memory)


class CState(PreflightState):
    def __init__(self, memory):
        super().__init__(memory[:12])
        self.loader = Runtime(self.runtime, (ctypes.c_uint8 * 36).from_buffer_copy(memory[12]),
                              (ctypes.c_uint8 * 4).from_buffer_copy(memory[13]))
        self.runtime = self.loader.preset
        self.storage = self.runtime.storage

    def snapshot(self):
        return super().snapshot() + (bytes(self.loader.saved), bytes(self.loader.counter))


class CMemory(PreflightMemory):
    def __init__(self, state):
        super().__init__(state)
        for base, array in ((SAVED, state.loader.saved), (COUNTER, state.loader.counter)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def pointer(array, offset=0):
    return ctypes.cast(ctypes.byref(array, offset), ctypes.POINTER(ctypes.c_uint8))


def configure(library):
    u32, byte = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)
    runtime, io = ctypes.POINTER(Runtime), ctypes.POINTER(IO)
    signatures = {
        "load": ("load", [runtime, u32, io]), "snapshot": ("snapshot", [runtime, byte]),
        "rebind": ("rebind", [runtime]), "binding": ("binding", [byte, u32, byte, byte]),
        "rate": ("rate", [u32]), "elapsed": ("elapsed", [runtime, u32, ctypes.POINTER(u32), io]),
        "report": ("report", [runtime, u32, u32, u32, u32, io]),
        "compare": ("compare", [byte, byte, u32]), "preset_step": ("step_preset", [runtime, u32, io]),
        "action": ("action", [runtime, ctypes.c_uint, ctypes.c_uint, io]),
        "tick": ("tick", [runtime, u32, io]),
        "edge": ("edge", [runtime, ctypes.c_uint, ctypes.c_uint, u32, u32, io]),
    }
    result = {}
    for operation, (name, arguments) in signatures.items():
        function = getattr(library, "hyperrig_loader_" + name)
        function.argtypes = arguments
        function.restype = u32 if operation == "rate" else ctypes.c_int
        result[operation] = function
    return result


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = PresetLoaderProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts = dict.fromkeys(functions, 0)
    coverage, services = set(), set()
    subsets = {"sequence_steps": 0, "mutating_boundary_cases": 0}
    rng = random.Random(0xCA7EC9F4)

    def compare(memory, operation, *arguments, regions=(), failures=None, plan=None,
                clocks=(100, 500, 600, 1000), application_outputs=(0x12345678, 0x87654321), sequence=False):
        native_flash, c_flash = Flash(regions, failures), Flash(regions, failures)
        native = program.execute(memory, operation, *arguments, reader=native_flash.read,
            boundary=Script(plan, clocks), application_outputs=application_outputs)
        state, calls, errors, script = CState(memory), [], [], Script(plan, clocks)
        def service_callback(_opaque, service, a, b, c):
            try:
                calls.append((service, (a, b, c), state.snapshot()))
                return script(service, (a, b, c), CMemory(state))
            except Exception as error:
                errors.append(error)
                return 0
        def read_callback(_opaque, address, destination, size):
            try:
                label, offset = state.target(destination, size)
                calls.append((READ, (address, label, offset, size), state.snapshot()))
                code, data = c_flash.read(address, size)
                if data:
                    ctypes.memmove(destination, data, len(data))
                return code
            except Exception as error:
                errors.append(error)
                return 1
        def apply_callback(_opaque, preset, first, second):
            try:
                assert ctypes.addressof(first.contents) != ctypes.addressof(second.contents)
                args = (preset, 4, 0)
                calls.append((APPLY, args, state.snapshot()))
                value = script(APPLY, args, CMemory(state))
                for destination, word in zip((first, second), application_outputs):
                    if word is not None:
                        destination[0] = word
                return value
            except Exception as error:
                errors.append(error)
                return 0
        call, read, apply = SERVICE_CALLBACK(service_callback), READ_CALLBACK(read_callback), APPLY_CALLBACK(apply_callback)
        io = IO(StorageIO(call, read, None), apply)
        runtime = ctypes.byref(state.loader)
        if operation == "snapshot":
            actual = functions[operation](runtime, state.header)
        elif operation == "rebind":
            actual = functions[operation](runtime)
        elif operation == "binding":
            actual = functions[operation](state.payload, arguments[0], pointer(state.header), pointer(state.header, 1))
        elif operation == "rate":
            actual = functions[operation](struct.unpack_from("<I", memory[0], 44)[0])
        elif operation == "compare":
            actual = functions[operation](pointer(state.header, arguments[0]), pointer(state.payload, arguments[1]), arguments[2])
        elif operation == "elapsed":
            value = ctypes.c_uint32(0xDEADBEEF)
            assert functions[operation](runtime, arguments[0], ctypes.byref(value), ctypes.byref(io)) == 0
            actual = value.value
        else:
            actual = functions[operation](runtime, *arguments, ctypes.byref(io))
        if errors:
            raise errors[0]
        expected = 0 if operation in ("snapshot", "binding", "report", "preset_step", "action", "tick", "edge") else native["result"]
        if ((actual & 0xFFFFFFFF) != expected or state.snapshot() != native["memory"]
                or calls != native["calls"] or c_flash.requests != native_flash.requests):
            changed = [(i, next((j for j, (a, b) in enumerate(zip(left, right)) if a != b), None))
                       for i, (left, right) in enumerate(zip(state.snapshot(), native["memory"]))
                       if left != right and i != 2]
            raise AssertionError(f"Loader mismatch {counts}, {operation}, {arguments}: result {actual}/{expected}; "
                f"memory fields/first bytes {changed}; C calls {[x[:2] for x in calls]}; original {[x[:2] for x in native['calls']]}")
        counts[operation] += 1
        coverage.update(native["visited"])
        services.update(call[0] for call in calls)
        subsets["sequence_steps"] += int(sequence)
        subsets["mutating_boundary_cases"] += int(any(writes for _, writes in (plan or {}).values()))
        return state.snapshot(), actual & 0xFFFFFFFF

    for calibration in (*range(301), 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 4294967, 4294968):
        memory = baseline()
        struct.pack_into("<I", memory[0], 44, calibration)
        compare(memory, "rate")
    for offset_a in range(4):
        for offset_b in range(4):
            for size in (0, 1, 3, 4, 5, 35, 36):
                memory = baseline()
                data = rng.randbytes(size)
                memory[9][offset_a:offset_a + size] = data
                memory[10][offset_b:offset_b + size] = data
                compare(memory, "compare", offset_a, offset_b, size)
                if size:
                    memory[10][offset_b + size - 1] ^= 255
                    compare(memory, "compare", offset_a, offset_b, size)
    for difference in (0, 1, 3, 4, 15, 31, 35):
        for first, second in ((0, 255), (255, 0)):
            memory = baseline()
            memory[9][:36] = bytes(36)
            memory[10][:36] = bytes(36)
            memory[9][difference], memory[10][difference] = first, second
            compare(memory, "compare", 0, 0, 36)
    for record_index in range(12):
        for auxiliary in range(256):
            memory = baseline()
            memory[0][236 + record_index * 3:239 + record_index * 3] = bytes((8, 19, auxiliary))
            compare(memory, "snapshot")
    for type_id in range(256):
        memory = baseline()
        memory[0][236:239] = bytes((type_id, 77, 2))
        compare(memory, "snapshot")
    for count in range(17):
        for position in (*range(18), 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            memory = baseline()
            memory[10][:17] = bytes((count,)) + bytes(i % 3 for i in range(16))
            compare(memory, "binding", position)
    print("Rate, byte comparison, snapshots and binding conversion passed.", flush=True)

    for first_count, second_count in ((0, 0), (1, 0), (0, 1), (10, 0), (0, 10), (10, 6), (10, 10)):
        for position in (0, 1, 9, 10, 15, 16, 255):
            memory = baseline()
            route(memory, list(range(first_count)), second=list(range(6, 6 + second_count)))
            for record_index in range(12):
                memory[0][236 + 3 * record_index:239 + 3 * record_index] = bytes((8, position, 255))
            compare(memory, "rebind")
    for case in range(128):
        memory = baseline()
        route(memory, [rng.randrange(20) for _ in range(rng.randrange(11))],
              second=[rng.randrange(20) for _ in range(rng.randrange(11))])
        memory[6][:] = rng.randbytes(48)
        for record_index in range(12):
            memory[0][236 + 3 * record_index:239 + 3 * record_index] = bytes((
                rng.choice((0, 2, 8)), rng.randrange(20), rng.choice((0, 1, 255))))
        compare(memory, "rebind")
    compare(baseline(), "rebind")

    for calibration in (1, 6, 7, 239, 240, 241, 4294967, 4294968, 0xFFFFFFFF):
        for start, now in ((0, 0), (0, 0xFFFFFFFF), (0xFFFFFFF0, 20), (1234, 1233), (100, 40000)):
            memory = baseline()
            struct.pack_into("<I", memory[0], 44, calibration)
            compare(memory, "elapsed", start, clocks=(now,))
    for counter, previous in ((0, 0), (32766, 0), (32767, 0), (32768, 0), (0, 1), (4, 0xFFFFFFFE)):
        for now in (0, 166 * 65534, 166 * 65535, 166 * 65536, 0xFFFFFFFF):
            memory = baseline()
            struct.pack_into("<I", memory[0], 44, 1)
            struct.pack_into("<I", memory[13], 0, counter)
            compare(memory, "report", 31, 0xFFFFFFFE, 0, previous, clocks=(now,))
    memory = baseline()
    struct.pack_into("<I", memory[13], 0, 10)
    compare(memory, "report", 0xFFFFFFFF, 0x01000000, 0, 5, clocks=(80000,),
            plan={CLOCK: (80000, ((GLOBAL + 44, 480, 4), (COUNTER, 1000, 4)))})
    print("Rebinding, elapsed arithmetic and packed report boundaries passed.", flush=True)

    good = ((0xBF000, record(b"\x05")),)
    for preset in (*range(32), 32, 255, 0xFFFFFFFF):
        compare(baseline(), "load", preset, regions=((0xBF000 + 2048 * preset, record(b"\x05")),)
                if preset < 32 else ())
    for encoded in (record(b"", tag=0), record(b"", size=1491), record(b"\x05", crc=0xBAD),
                    record(payload_case(1201, 4)), record(payload_case(1474, 4))):
        compare(baseline(), "load", 0, regions=((0xBF000, encoded),))
    for failed_read, prefix in ((1, 0), (1, 12), (2, 0), (2, 1)):
        compare(baseline(), "load", 0, regions=good, failures={failed_read: (1, prefix)})
    for size, version in ((0, 0), (1200, 4), (1474, 5), (1490, 6)):
        compare(baseline(), "load", 0, regions=((0xBF000,
            record(payload_case(size, version, 16, types=(6, 24), seed=size))),))
    for tracking in (0, 1, 255):
        for same in (False, True):
            for position in (0, 15, 255):
                for application_result in (0, 1, 0xFFFFFFFF):
                    memory = baseline()
                    route(memory, (2, 3, 2))
                    memory[0][236:239] = bytes((8, position, 255))
                    memory[1][736] = tracking
                    if same:
                        memory[12][:] = memory[0][236:272]
                    compare(memory, "load", 0, regions=good,
                        plan={APPLY: (application_result, ((GLOBAL + 92, 19, 4), (COUNTER, 7, 4)))})
    for suppressed in (0, 1, 255):
        for report_suppression in (0, 1):
            memory = baseline()
            memory[1][740] = suppressed
            compare(memory, "load", 0, regions=good,
                plan={(NOTIFY, 26): (0xFFFFFFFF, ((STATE + 740, report_suppression, 1),))})
    compare(baseline(), "load", 0, regions=good, application_outputs=(None, None),
        clocks=(0xFFFFFF00, 0x100, 0x200, 0x500),
        plan={(CLOCK, "call", 3): (0x200, ((GLOBAL + 44, 480, 4), (COUNTER, 0xFFFFFFFE, 4))),
              APPLY: (0x80000000, ((COUNTER, 3, 4), (GLOBAL + 269, 8, 1),
                                 (GLOBAL + 270, 0, 1), (GLOBAL + 271, 255, 1))),
              (CLOCK, "call", 4): (0x500, ((COUNTER, 123, 4),))})
    for case in range(32):
        memory = baseline()
        route(memory, (0, 1, 0), second=(15, 14))
        memory[0][236:272] = rng.randbytes(36)
        memory[1][736], memory[1][740] = case & 1, (case >> 1) & 1
        memory[12][:] = rng.randbytes(36)
        compare(memory, "load", 0, regions=good, clocks=tuple(rng.getrandbits(32) for _ in range(4)),
                plan={APPLY: (rng.getrandbits(32), ((COUNTER, rng.getrandbits(32), 4),))})
    print("Loader failures, commit ordering, application results and notification paths passed.", flush=True)

    regions = ((0xBF800, record(b"\x05")), (0xC0000, record(b"\x05")), (0xCE800, record(b"\x05")))
    for step in (0, 1, 2, 0xFFFFFFFF, 0x80000000):
        compare(baseline(), "preset_step", step, regions=regions)
    compare(baseline(), "preset_step", 1, regions=((0xBF800, record(payload_case(1201, 4))),
                                                  (0xC0000, record(b"\x05"))))
    compare(baseline(), "preset_step", 1, regions=regions, failures={3: (1, 0)})
    for logical in range(4):
        for event in range(3):
            memory = baseline()
            memory[0][236 + 9 * logical + 3 * event:239 + 9 * logical + 3 * event] = bytes((2, 1, 3))
            compare(memory, "action", logical, event, regions=regions)
    memory = baseline()
    memory[0][236:239] = bytes((3, 0, 0))
    compare(memory, "edge", 0, 1, 100, 200, regions=regions)
    memory = baseline()
    memory[0][239:242] = bytes((2, 2, 255))
    memory[1][1567] = 1
    compare(memory, "tick", 1000, regions=regions)
    memory = baseline()
    for step in (1, 1, 0xFFFFFFFF, 1, 0xFFFFFFFF, 0xFFFFFFFF):
        memory, _ = compare(memory, "preset_step", step, regions=regions, sequence=True)
    print("Integrated preset navigation, actions, edges and timers passed.", flush=True)

    # Invalid API is distinguished from original preflight failure. Dynamic
    # calibration rejection has partial side effects and is not oracle equivalence.
    state, seen = CState(baseline()), []
    call = SERVICE_CALLBACK(lambda *args: seen.append(args) or 0)
    read = READ_CALLBACK(lambda *args: seen.append(args) or 1)
    apply = APPLY_CALLBACK(lambda *args: seen.append(args) or 0)
    io = IO(StorageIO(call, read, None), apply)
    runtime = ctypes.byref(state.loader)
    out = ctypes.c_uint32(0xDEADBEEF)
    invalid = [("load", (None, 0, ctypes.byref(io)), -2), ("load", (runtime, 0, None), -2),
        ("snapshot", (runtime, None), -1), ("rebind", (None,), -1),
        ("binding", (None, 0, pointer(state.header), pointer(state.header, 1)), -1),
        ("binding", (state.payload, 0, None, pointer(state.header, 1)), -1),
        ("compare", (None, state.payload, 1), -256), ("compare", (state.header, state.payload, 37), -256),
        ("elapsed", (runtime, 0, None, ctypes.byref(io)), -2),
        ("action", (runtime, 4, 0, ctypes.byref(io)), -2),
        ("action", (runtime, 0, 3, ctypes.byref(io)), -2),
        ("edge", (runtime, 5, 0, 0, 0, ctypes.byref(io)), -2),
        ("edge", (runtime, 0, 2, 0, 0, ctypes.byref(io)), -2)]
    for operation, args, expected in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == expected
        assert state.snapshot() == before and not seen
    invalid_extra = 0
    for bad in (IO(StorageIO(SERVICE_CALLBACK(), read, None), apply),
                IO(StorageIO(call, READ_CALLBACK(), None), apply), IO(io.storage, APPLY_CALLBACK())):
        before = state.snapshot()
        assert functions["load"](runtime, 0, ctypes.byref(bad)) == -2
        assert state.snapshot() == before and not seen
        invalid_extra += 1
    for offset, value in ((44, 0), (44, 1), (88, 4)):
        state = CState(baseline())
        CMemory(state).write(GLOBAL + offset, value, 4)
        before = state.snapshot()
        assert functions["load"](ctypes.byref(state.loader), 0, ctypes.byref(io)) == -2
        assert state.snapshot() == before and not seen
        invalid_extra += 1
    state = CState(baseline())
    state.storage.selection.counts[0] = 11
    before = state.snapshot()
    assert functions["rebind"](ctypes.byref(state.loader)) == -1
    assert state.snapshot() == before
    invalid_extra += 1
    state = CState(baseline())
    state.payload[0] = 17
    before = state.snapshot()
    assert functions["binding"](state.payload, 0, pointer(state.header), pointer(state.header, 1)) == -1
    assert state.snapshot() == before
    invalid_extra += 1
    assert functions["compare"](None, None, 0) == 0
    state = CState(baseline())
    def break_calibration(_opaque, service, a, b, c):
        seen.append((service, a, b, c))
        CMemory(state).write(GLOBAL + 44, 0, 4)
        return 1000
    broken_call = SERVICE_CALLBACK(break_calibration)
    broken_io = IO(StorageIO(broken_call, read, None), apply)
    assert functions["elapsed"](ctypes.byref(state.loader), 0, ctypes.byref(out), ctypes.byref(broken_io)) == -3
    assert out.value == 0xDEADBEEF and seen == [(CLOCK, 0, 0, 0)]

    new_code = set(program.code) - program.pre_loader_code
    missing = sorted(new_code - coverage)
    assert not missing, [hex(address) for address in missing]
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI input is not the reviewed v4 application")
        app = unpack_app(raw)[2]["app.bin"]
        for regions_, originals in ((REGIONS, program.loader_regions), (PREFLIGHT_REGIONS, program.preflight_regions),
                (LIBRARY_REGIONS, program.library_regions), (STORAGE_REGIONS, program.storage_regions),
                (SELECTION_REGIONS, program.selection_regions), (ACTION_REGIONS, program.raw_regions)):
            for name, (start, end) in regions_.items():
                assert app[start - 0x02000120:end - 0x02000120] == originals[name], name
        for region in (program.controls.transition, program.controls.immediate):
            assert app[region.start - 0x02000120:region.end - 0x02000120] == region.raw
        assert app[CURVE - 0x02000120:CURVE - 0x02000120 + 11] == program.curve
        mini_binding = {"image_sha256": digest, "all_thirty_two_function_regions_byte_identical": True,
                        "both_library_regions_and_curve_byte_identical": True}

    sources = [f"tools/{name}.py" for name in ("dot_machine", "control_machine", "control_action_machine",
        "selection_machine", "preset_storage_machine", "preset_preflight_machine", "preset_loader_machine",
        "verify_controls", "verify_control_actions", "verify_selection", "verify_preset_storage",
        "verify_preset_preflight", "verify_preset_loader", "build_preset_loader")]
    sources += ["tests/test_preset_loader_machine.py"]
    for component in ("controls", "control_actions", "selection", "preset_storage", "preset_preflight", "preset_loader"):
        sources += [f"firmware/src/hyperrig_{component}.c", f"firmware/include/hyperrig/hyperrig_{component}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
                "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {
        "schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "loader sequence, bindings, snapshots and arithmetic reports integrated with controls and preflight",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.loader_regions[name]).hexdigest()}
            for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "subsets": subsets,
        "invalid_api_checks": len(invalid) + invalid_extra, "empty_null_compare_checks": 1,
        "dynamic_calibration_guard_checks": 1,
        "instruction_coverage": {"new_visited": len(coverage & new_code), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": ["apply_preset" if a == APPLY else "read" if a == READ
                                      else STORAGE_LEAVES[a][0] for a in sorted(services)],
        "application_boundary": {"address": APPLY, "output_word_offsets_relative_to_caller_sp": [4, 0],
                                 "output_words_unused_by_loader": True, "implementation_executed": False},
        "library_contracts_not_interpreted": ["memset working buffer", "memmove migration and 36 action bytes"],
        "compared": ["return/results", "all previous mapped bytes", "36 saved action bytes", "4 counter bytes",
                     "ordered semantic read/service/application arguments and mapped state at each call"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["application/DSP handler remains scripted; no claim of live state application",
            "storage preparation, priority, polling and physical read wrapper remain external",
            "no physical time units or hardware division-by-zero semantics claimed",
            "private stack bytes and application output words are not compared as persistent state",
            "no concurrency, persistence writes, three-switch bank change or Alpha 13 implementation"],
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
