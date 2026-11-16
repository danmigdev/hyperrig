"""Compare preset preflight and legacy conversion with original instructions."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from preset_preflight_machine import (PresetPreflightProgram, REGIONS, LIBRARY_REGIONS,
                                     WORKING, CURVE, ROOT, PAYLOAD_MAX)
from preset_storage_machine import (REGIONS as STORAGE_REGIONS, PREPARE, PRIORITY, POLL,
                                   READ, MAP, HEADER_BUFFER, STORAGE_LEAVES)
from selection_machine import REGIONS as SELECTION_REGIONS
from control_action_machine import REGIONS as ACTION_REGIONS
from verify_preset_storage import (Storage, IO, SERVICE_CALLBACK, READ_CALLBACK, TAG,
    baseline as storage_baseline, record, Flash, CState as StorageState,
    CMemory as StorageMemory, scripted)


class Runtime(ctypes.Structure):
    _fields_ = [("storage", Storage), ("working", ctypes.c_uint8 * PAYLOAD_MAX)]


def baseline():
    return storage_baseline() + (bytearray([0x77] * PAYLOAD_MAX),)


def payload_case(size, version, count=0, *, types=(), seed=0):
    data = bytearray(random.Random(seed).randbytes(size))
    if size:
        data[0] = version
    if size > 1:
        data[1] = count
    stride = 16 if version < 5 else 18
    for slot in range(16):
        offset = 13 + stride * slot
        if offset < size:
            data[offset] = types[slot % len(types)] if types else 0
    return data


class CState(StorageState):
    def __init__(self, memory):
        super().__init__(memory[:11])
        self.runtime = Runtime(self.storage, (ctypes.c_uint8 * PAYLOAD_MAX).from_buffer_copy(memory[11]))
        self.storage = self.runtime.storage

    def snapshot(self):
        return super().snapshot() + (bytes(self.runtime.working),)

    def target(self, pointer, size):
        address = ctypes.cast(pointer, ctypes.c_void_p).value
        base = ctypes.addressof(self.runtime.working)
        if base <= address and address + size <= base + PAYLOAD_MAX:
            return "working", address - base
        return super().target(pointer, size)


class CMemory(StorageMemory):
    def __init__(self, state):
        super().__init__(state)
        self.extra.update({WORKING + i: (state.runtime.working, i) for i in range(PAYLOAD_MAX)})


def configure(library):
    u32, pointer = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)
    result = {}
    for operation, arguments, returned in (
        ("preflight", [ctypes.POINTER(Runtime), u32, pointer, ctypes.POINTER(IO)], ctypes.c_int),
        ("needs_conversion", [u32], ctypes.c_int),
        ("convert_effect", [u32, pointer], u32),
    ):
        function = getattr(library, "hyperrig_preset_" + operation)
        function.argtypes, function.restype = arguments, returned
        result[operation] = function
    return result


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = PresetPreflightProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts = dict.fromkeys(functions, 0)
    coverage, services, library_services = set(), set(), set()
    subsets = {"stateful_preflights": 0, "mutating_boundary_cases": 0}
    rng = random.Random(0x79F6A452)

    def compare(memory, operation, *arguments, regions=(), failures=None, plan=None, sequence=False):
        plan = plan or {}
        native_flash, c_flash = Flash(regions, failures), Flash(regions, failures)
        native = program.execute(memory, operation, *arguments, reader=native_flash.read,
            boundary=lambda service, args, view: scripted(plan, service, args, view))
        state, calls, errors = CState(memory), [], []
        def service_callback(_opaque, service, a, b, c):
            try:
                calls.append((service, (a, b, c), state.snapshot()))
                return scripted(plan, service, (a, b, c), CMemory(state))
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
        call, read = SERVICE_CALLBACK(service_callback), READ_CALLBACK(read_callback)
        io = IO(call, read, None)
        if operation == "preflight":
            actual = functions[operation](ctypes.byref(state.runtime), arguments[0], state.header, ctypes.byref(io))
        elif operation == "convert_effect":
            actual = functions[operation](arguments[0], state.payload if arguments[1] else None)
        else:
            actual = functions[operation](arguments[0])
        if errors:
            raise errors[0]
        if ((actual & 0xFFFFFFFF) != native["result"] or state.snapshot() != native["memory"]
                or calls != native["calls"] or c_flash.requests != native_flash.requests):
            changed = [(i, next((j for j, (a, b) in enumerate(zip(left, right)) if a != b), None))
                       for i, (left, right) in enumerate(zip(state.snapshot(), native["memory"]))
                       if left != right and i != 2]
            raise AssertionError(f"Preflight mismatch {counts} {operation} {arguments}: "
                f"result {actual}/{native['result']}, memory fields/first bytes {changed}, "
                f"C calls {[item[:2] for item in calls]}, original {[item[:2] for item in native['calls']]}")
        counts[operation] += 1
        coverage.update(native["visited"])
        services.update(call[0] for call in calls)
        library_services.update(call[0] for call in native["library_calls"])
        subsets["stateful_preflights"] += int(sequence)
        subsets["mutating_boundary_cases"] += int(any(writes for _, writes in plan.values()))
        return state.snapshot(), actual & 0xFFFFFFFF

    # IDs include every serialized byte and unsigned extremes outside that domain.
    for type_id in (*range(256), 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        compare(baseline(), "needs_conversion", type_id)
        compare(baseline(), "convert_effect", type_id, 0)
        if type_id not in (6, 24):
            compare(baseline(), "convert_effect", type_id, 1)
    signed_edges = (-32768, -101, -1, 0, 1, 9, 10, 27, 28, 49, 50, 69, 70, 99, 100, 101, 32767)
    for value in range(101):
        memory = baseline()
        struct.pack_into("<hhh", memory[10], 0, value, value, value)
        compare(memory, "convert_effect", 6, 1)
    for field in range(3):
        for value in signed_edges:
            memory = baseline()
            struct.pack_into("<hhh", memory[10], 0, 49, 70, 99)
            struct.pack_into("<h", memory[10], 2 * field, value)
            compare(memory, "convert_effect", 6, 1)
    for value in (*range(-1, 130), -32768, -1024, 32767):
        memory = baseline()
        struct.pack_into("<h", memory[10], 8, value)
        compare(memory, "convert_effect", 24, 1)
    for case in range(256):
        memory = baseline()
        memory[10][:14] = rng.randbytes(14)
        compare(memory, "convert_effect", 6 if case % 2 else 24, 1)
    print("Effect predicate, signed clamps and conversion comparisons passed.", flush=True)

    for preset in range(32):
        address = 0xBF000 + 2048 * preset
        compare(baseline(), "preflight", preset, regions=((address, record(b"\x05")),))
    for preset in (32, 255, 0x80000000, 0xFFFFFFFF):
        compare(baseline(), "preflight", preset)
    for mapping in (16, 17, 127, 128, 255):
        for preset in (0, 1):
            memory = baseline()
            memory[7][0] = mapping
            address = (0xDD000 if mapping == 16 else 0xDE000) + 2048 * preset
            compare(memory, "preflight", preset, regions=((address, record(b"\x05")),))
    for version in range(256):
        compare(baseline(), "preflight", 0, regions=((0xBF000,
            record(payload_case(32, version, seed=version))),))
    print("Preset IDs, mappings and all version-byte comparisons passed.", flush=True)

    lengths = (0, 1, 2, 11, 12, 28, 29, 267, 268, 299, 300, 1199, 1200, 1201,
               1360, 1423, 1424, 1473, 1474, 1475, 1489, 1490)
    for version in (4, 5):
        for size in lengths:
            compare(baseline(), "preflight", 0, regions=((0xBF000,
                record(payload_case(size, version, seed=size))),))
    for size, version in ((1200, 4), (1474, 5), (1490, 6)):
        for count in (0, 1, 15, 16, 17, 255):
            compare(baseline(), "preflight", 0, regions=((0xBF000,
                record(payload_case(size, version, count, types=(6, 24, 27, 29), seed=count))),))
    for slot in (0, 1, 7, 15):
        for type_id in (6, 24):
            for size, version in ((1200, 4), (1490, 5)):
                types = [0] * 16
                types[slot] = type_id
                compare(baseline(), "preflight", 0, regions=((0xBF000,
                    record(payload_case(size, version, 16, types=types, seed=slot))),))
    print("Layout sizes, overlapping migration and effect/scene conversion comparisons passed.", flush=True)

    for malformed in (record(b"", tag=0), record(b"", size=1491), record(b"", size=0xFFFFFFFF)):
        compare(baseline(), "preflight", 0, regions=((0xBF000, malformed),))
    good_payload = payload_case(1490, 5, 16, types=(6, 24), seed=10)
    regions = ((0xBF000, record(good_payload)),)
    for read_number, prefix in ((1, 0), (1, 1), (1, 12), (1, 39), (1, 40),
                                (2, 0), (2, 1), (2, 257), (2, 1489), (2, 1490)):
        compare(baseline(), "preflight", 0, regions=regions,
                failures={read_number: (0xFFFFFFFE, prefix)})
    for size in (0, 1200, 1474, 1490):
        compare(baseline(), "preflight", 0, regions=((0xBF000,
            record(payload_case(size, 4, seed=size), crc=0xBAD)),))

    # Preparation sees cleared working bytes; release precedes migration and can
    # change the length/version consumed by conversion without another CRC check.
    compare(baseline(), "preflight", 0, regions=((0xDD000, record(b"\x05")),),
        plan={PREPARE: (0, ((MAP, 16, 1), (WORKING + 1489, 0xAA, 1)))})
    compare(baseline(), "preflight", 0, regions=regions,
        plan={(PRIORITY, 0): (0, ((WORKING, 4, 1),))})
    compare(baseline(), "preflight", 0, regions=regions,
        plan={(PRIORITY, 0): (0, ((HEADER_BUFFER + 4, 1474, 4),))})
    compare(baseline(), "preflight", 0, regions=((0xBF000, record(b"\x05")),),
        plan={(PRIORITY, 0): (0, ((HEADER_BUFFER + 4, 1200, 4), (WORKING, 4, 1)))})
    compare(baseline(), "preflight", 0, regions=regions,
        plan={POLL: (0, ((WORKING + 1489, 0x3A, 1),))})
    for case in range(32):
        size, version = rng.choice(((1200, 4), (1474, 5), (1490, 6), (rng.randrange(64), rng.randrange(256))))
        data = payload_case(size, version, rng.randrange(256), types=(0, 6, 24, 27, 29, 255), seed=case)
        compare(baseline(), "preflight", 0, regions=((0xBF000, record(data)),))
    old = ((0xBF000, record(payload_case(1200, 4, 16, types=(6, 24), seed=42))),)
    memory, _ = compare(baseline(), "preflight", 0, regions=old, sequence=True)
    repeated, _ = compare(memory, "preflight", 0, regions=old, sequence=True)
    assert memory == repeated
    failed, status = compare(repeated, "preflight", 0, failures={1: (1, 0)}, sequence=True)
    assert status == 0xFFFFFFFF and failed[11] == bytes(PAYLOAD_MAX)
    print("Read/CRC failures, callback mutation and consecutive preflight comparisons passed.", flush=True)

    state, seen = CState(baseline()), []
    call = SERVICE_CALLBACK(lambda *args: seen.append(args) or 0)
    read = READ_CALLBACK(lambda *args: seen.append(args) or 0)
    io = IO(call, read, None)
    invalid = [(None, 0, state.header, ctypes.byref(io)),
               (ctypes.byref(state.runtime), 0, None, ctypes.byref(io)),
               (ctypes.byref(state.runtime), 0, state.header, None)]
    for args in invalid:
        before = state.snapshot()
        assert functions["preflight"](*args) == -5
        assert state.snapshot() == before and not seen
    for bad in (IO(SERVICE_CALLBACK(), read, None), IO(call, READ_CALLBACK(), None)):
        before = state.snapshot()
        assert functions["preflight"](ctypes.byref(state.runtime), 0, state.header, ctypes.byref(bad)) == -5
        assert state.snapshot() == before and not seen

    new_code = set(program.code) - program.pre_preflight_code
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
        for regions, originals in ((REGIONS, program.preflight_regions), (LIBRARY_REGIONS, program.library_regions),
                (STORAGE_REGIONS, program.storage_regions), (SELECTION_REGIONS, program.selection_regions),
                (ACTION_REGIONS, program.raw_regions)):
            for name, (start, end) in regions.items():
                assert app[start - 0x02000120:end - 0x02000120] == originals[name], name
        for region in (program.controls.transition, program.controls.immediate):
            assert app[region.start - 0x02000120:region.end - 0x02000120] == region.raw
        assert app[CURVE - 0x02000120:CURVE - 0x02000120 + 11] == program.curve
        mini_binding = {"image_sha256": digest, "all_twenty_four_function_regions_byte_identical": True,
                        "both_library_regions_and_curve_byte_identical": True}

    sources = [f"tools/{name}.py" for name in ("dot_machine", "control_machine", "control_action_machine",
        "selection_machine", "preset_storage_machine", "preset_preflight_machine", "verify_controls",
        "verify_control_actions", "verify_selection", "verify_preset_storage", "verify_preset_preflight",
        "build_preset_preflight")]
    sources += ["tests/test_preset_preflight_machine.py"]
    for component in ("controls", "control_actions", "selection", "preset_storage", "preset_preflight"):
        sources += [f"firmware/src/hyperrig_{component}.c", f"firmware/include/hyperrig/hyperrig_{component}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
                "upstream/pi32v2-isa/isa/pi32v2.toml", "upstream/pi32v2-isa/hw/fm1-2026-10-24-v3/README.md"]
    report = {
        "schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "preset preflight, two layout migrations and legacy effect parameter conversion",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.preflight_regions[name]).hexdigest()}
            for name, (start, end) in REGIONS.items()},
        "curve": {"start": CURVE, "bytes": 11, "sha256": hashlib.sha256(program.curve).hexdigest()},
        "library_contracts_not_interpreted": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.library_regions[name]).hexdigest()}
            for name, (start, end) in LIBRARY_REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "subsets": subsets,
        "invalid_api_checks": len(invalid) + 2,
        "instruction_coverage": {"new_visited": len(coverage & new_code), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": ["read" if address == READ else STORAGE_LEAVES[address][0]
                                      for address in sorted(services)],
        "library_contracts_visited": sorted(library_services),
        "compared": ["return values", "all previously mapped storage/control/public buffer bytes",
                     "1490 working bytes", "ordered semantic read/service arguments and mapped state at each call"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["memset and memmove use explicit bounded library contracts, not their original instruction bodies",
                        "storage preparation, priority, polling and physical read wrapper remain external",
                        "preflight conversion is not full preset schema validation or DSP application",
                        "top-level loader and current-preset commit remain outside the reconstructed component",
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
