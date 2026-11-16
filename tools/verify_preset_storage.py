"""Compare recovered preset validation with original instructions and synthetic I/O."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib

from preset_storage_machine import (PresetStorageProgram, REGIONS, STORAGE_LEAVES, READ, PREPARE,
    PRIORITY, POLL, MAP, SCRATCH, HEADER_BUFFER, PAYLOAD_BUFFER, PAYLOAD_MAX, ROOT, STATE)
from selection_machine import REGIONS as SELECTION_REGIONS
from control_action_machine import REGIONS as ACTION_REGIONS
from verify_selection import (Selection, baseline as selection_baseline, from_memory as selection_from,
                             snapshot as selection_snapshot, CMemory as SelectionMemory, scripted,
                             SERVICE_CALLBACK, GLOBAL, LOAD)

TAG = 0x51474B54
READ_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                                ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint32)


class Storage(ctypes.Structure):
    _fields_ = [("selection", Selection), ("mapping", ctypes.c_uint8 * 16),
                ("scratch", ctypes.c_uint8 * 256)]


class IO(ctypes.Structure):
    _fields_ = [("call", SERVICE_CALLBACK), ("read", READ_CALLBACK), ("opaque", ctypes.c_void_p)]


def baseline():
    return selection_baseline() + (bytearray(range(16)), bytearray([0xA5] * 256),
                                  bytearray([0xC3] * 40), bytearray([0x5A] * PAYLOAD_MAX))


def record(payload, *, tag=TAG, size=None, crc=None):
    header = struct.pack("<III", tag, len(payload) if size is None else size,
                         zlib.crc32(payload) if crc is None else crc) + bytes(range(28))
    return header + payload


class Flash:
    """Synthetic read outcomes at the original wrapper boundary, never a device."""
    def __init__(self, regions=(), failures=None):
        self.data = {address + i: byte for address, payload in regions for i, byte in enumerate(payload)}
        self.failures = failures or {}
        self.requests = []

    def read(self, address, size):
        self.requests.append((address, size))
        # A simple test environment, not an implementation of the omitted driver.
        if address < 0xBF000 or address + size > 0xFF000:
            return 0xFFFFFFFF, b""
        data = bytes(self.data.get(address + i, 255) for i in range(size))
        if len(self.requests) in self.failures:
            code, prefix = self.failures[len(self.requests)]
            return code, data[:min(size, prefix)]
        return 0, data


class CState:
    def __init__(self, memory):
        self.storage = Storage(selection_from(memory[:7]),
            (ctypes.c_uint8 * 16).from_buffer_copy(memory[7]),
            (ctypes.c_uint8 * 256).from_buffer_copy(memory[8]))
        self.header = (ctypes.c_uint8 * 40).from_buffer_copy(memory[9])
        self.payload = (ctypes.c_uint8 * PAYLOAD_MAX).from_buffer_copy(memory[10])

    def snapshot(self):
        return selection_snapshot(self.storage.selection) + (
            bytes(self.storage.mapping), bytes(self.storage.scratch), bytes(self.header), bytes(self.payload))

    def target(self, pointer, size):
        address = ctypes.cast(pointer, ctypes.c_void_p).value
        for array, label in ((self.storage.scratch, "scratch"), (self.header, "header"), (self.payload, "payload")):
            base = ctypes.addressof(array)
            if base <= address and address + size <= base + ctypes.sizeof(array):
                return label, address - base
        if size == 40:
            return "local_header", 0
        raise ValueError("unrecognized C read destination")


class CMemory(SelectionMemory):
    def __init__(self, state):
        super().__init__(state.storage.selection)
        for base, array in ((MAP, state.storage.mapping), (SCRATCH, state.storage.scratch),
                            (HEADER_BUFFER, state.header), (PAYLOAD_BUFFER, state.payload)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def configure(library):
    u32, pointer, io = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(IO)
    storage = ctypes.POINTER(Storage)
    signatures = {
        "block": ("block_address", [u32]), "address": ("preset_address", [storage, u32]),
        "available": ("available", [storage, u32, io]),
        "header": ("header", [u32, u32, u32, pointer, io]),
        "record": ("record", [u32, u32, u32, pointer, pointer, u32, io]),
        "crc_update": ("crc_update", [u32, pointer, u32, ctypes.POINTER(u32)]),
        "checksum": ("checksum", [pointer, u32, ctypes.POINTER(u32), io]),
        "preset_step": ("step_preset", [storage, u32, io]),
        "action": ("action", [storage, ctypes.c_uint, ctypes.c_uint, io]),
        "tick": ("tick", [storage, u32, io]),
        "edge": ("edge", [storage, ctypes.c_uint, ctypes.c_uint, u32, u32, io]),
    }
    functions = {}
    for operation, (name, arguments) in signatures.items():
        function = getattr(library, "hyperrig_storage_" + name)
        function.argtypes = arguments
        function.restype = u32 if operation in ("block", "address") else ctypes.c_int
        functions[operation] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    native = PresetStorageProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts = {name: 0 for name in functions}
    coverage, services = set(), set()
    rng = random.Random(0xCF8879BC)
    subsets = {"stateful_queries": 0, "mutating_boundary_cases": 0}
    crc_reference_checks = 0

    def compare(memory, operation, *arguments, regions=(), failures=None, plan=None, sequence=False):
        plan = plan or {}
        original_flash, c_flash = Flash(regions, failures), Flash(regions, failures)
        original = native.execute(memory, operation, *arguments, reader=original_flash.read,
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
        callback, read = SERVICE_CALLBACK(service_callback), READ_CALLBACK(read_callback)
        io, result = IO(callback, read, None), ctypes.c_uint32(0xDEADBEEF)
        if operation == "block":
            actual = functions[operation](*arguments)
        elif operation == "address":
            actual = functions[operation](ctypes.byref(state.storage), *arguments)
        elif operation == "header":
            actual = functions[operation](*arguments, state.header, ctypes.byref(io))
        elif operation == "record":
            actual = functions[operation](*arguments, state.header, state.payload, PAYLOAD_MAX, ctypes.byref(io))
        elif operation == "crc_update":
            assert functions[operation](arguments[0], state.payload, arguments[1], ctypes.byref(result)) == 0
            actual = result.value
        elif operation == "checksum":
            assert functions[operation](state.payload, arguments[0], ctypes.byref(result), ctypes.byref(io)) == 0
            actual = result.value
        else:
            actual = functions[operation](ctypes.byref(state.storage), *arguments, ctypes.byref(io))
        if errors:
            raise errors[0]
        expected = 0 if operation in ("preset_step", "action", "tick", "edge") else original["result"]
        if ((actual & 0xFFFFFFFF) != expected or state.snapshot() != original["memory"]
                or calls != original["calls"] or c_flash.requests != original_flash.requests):
            raise AssertionError(f"Storage mismatch: {counts}, {operation}, {arguments}; result={actual}/{expected}; "
                f"memory_equal={state.snapshot() == original['memory']}; "
                f"C calls={[item[:2] for item in calls]}; original calls={[item[:2] for item in original['calls']]}")
        counts[operation] += 1
        subsets["stateful_queries"] += int(sequence)
        subsets["mutating_boundary_cases"] += int(any(writes for _, writes in plan.values()))
        coverage.update(original["visited"])
        services.update(call[0] for call in calls)
        return state.snapshot(), actual & 0xFFFFFFFF

    for block in (*range(256), 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        compare(baseline(), "block", block)
    for preset in (0, 1, 30, 31):
        for mapping in range(256):
            memory = baseline()
            memory[7][preset >> 1] = mapping
            compare(memory, "address", preset)
    for preset in (*range(32), 32, 255, 0x80000000, 0xFFFFFFFF):
        compare(baseline(), "address", preset)

    for byte in range(256):
        for initial in (0, 0xFFFFFFFF):
            memory = baseline()
            memory[10][0] = byte
            _, actual = compare(memory, "crc_update", initial, 1)
            assert actual == zlib.crc32(bytes((byte,)), initial ^ 0xFFFFFFFF) ^ 0xFFFFFFFF
            crc_reference_checks += 1
    lengths = (0, 1, 2, 7, 31, 255, 256, 257, 511, 512, 513, 1474, 1489, 1490)
    for length in lengths:
        memory = baseline()
        data = rng.randbytes(length)
        memory[10][:length] = data
        for initial in (0xFFFFFFFF, 0x12345678):
            _, actual = compare(memory, "crc_update", initial, length)
            assert actual == zlib.crc32(data, initial ^ 0xFFFFFFFF) ^ 0xFFFFFFFF
            crc_reference_checks += 1
        _, actual = compare(memory, "checksum", length)
        assert actual == zlib.crc32(data)
        crc_reference_checks += 1
    print("Address and CRC comparisons passed.", flush=True)

    for expected_tag in (0, TAG, 0xFFFFFFFF):
        for actual_tag in (TAG, 0xFFFFFFFF):
            for declared in (0, 1, 1490, 1491, 0xFFFFFFFF):
                for maximum in (0, 1490, 0xFFFFFFFF):
                    compare(baseline(), "header", 0xBF000, expected_tag, maximum,
                            regions=((0xBF000, record(b"", tag=actual_tag, size=declared)),))
    for prefix in (0, 1, 12, 39, 40):
        compare(baseline(), "header", 0xBF000, TAG, 1490,
                regions=((0xBF000, record(b"abc")),), failures={1: (0xFFFFFFFE, prefix)})

    # Cache masks are independent bits. A checked bit wins even when bytes differ.
    for preset in range(32):
        address = 0xBF000 + (preset // 2) * 4096 + (preset % 2) * 2048
        for checked, available in ((0, 0), (0, 1), (1, 0), (1, 1)):
            memory = baseline()
            bit = 1 << preset
            struct.pack_into("<I", memory[1], 708, (0xA5A55A5A & ~bit) | (bit if checked else 0))
            struct.pack_into("<I", memory[1], 732, (0x5A5AA5A5 & ~bit) | (bit if available else 0))
            compare(memory, "available", preset, regions=((address, record(bytes(range(preset % 17)))),))
    for preset in (32, 255, 0x80000000, 0xFFFFFFFF):
        compare(baseline(), "available", preset)
    for mapping in (16, 17, 127, 128, 255):
        memory = baseline()
        memory[7][0] = mapping
        address = 0xDD800 if mapping == 16 else 0xDE800
        compare(memory, "available", 1, regions=((address, record(b"mapped")),))

    for length in (0, 1, 255, 256, 257, 511, 512, 513, 1474, 1490):
        payload = rng.randbytes(length)
        for corrupt in (0, 1):
            regions = ((0xBF000, record(payload, crc=zlib.crc32(payload) ^ corrupt)),)
            compare(baseline(), "available", 0, regions=regions)
            compare(baseline(), "record", 0xBF000, TAG, 1490, regions=regions)
    regions = ((0xBF000, record(rng.randbytes(1490))),)
    for failed_read in range(1, 8):
        compare(baseline(), "available", 0, regions=regions,
                failures={failed_read: (0xFFFFFFFE, (failed_read * 17) % 256)})
    for stage, prefix in ((1, 0), (1, 17), (2, 0), (2, 257), (2, 1490)):
        compare(baseline(), "record", 0xBF000, TAG, 1490, regions=regions,
                failures={stage: (0xFFFFFFFF, prefix)})
    for malformed in (record(b"abc", tag=0), record(b"", size=1491), record(b"", size=0xFFFFFFFF)):
        compare(baseline(), "available", 0, regions=((0xBF000, malformed),))
        compare(baseline(), "record", 0xBF000, TAG, 1490, regions=((0xBF000, malformed),))
    for address in (0, 0xBEFFF, 0xFF000, 0xFFFFFFFF):
        compare(baseline(), "record", address, TAG, 1490)
    print("Header, availability and record error-path comparisons passed.", flush=True)

    # Preparation may refresh the mapping or invalidate a previously cached result.
    memory = baseline()
    struct.pack_into("<I", memory[1], 708, 1)
    compare(memory, "available", 0, regions=((0xDD000, record(b"refresh")),),
            plan={PREPARE: (0, ((STATE + 708, 0, 4), (MAP, 16, 1)))})
    compare(baseline(), "available", 0, plan={PREPARE: (0, ((STATE + 708, 1, 4), (STATE + 732, 1, 4)))})
    compare(baseline(), "available", 0, regions=((0xBF000, record(b"pass")),),
            plan={(PRIORITY, 0): (0, ((STATE + 708, 0x80000000, 4), (STATE + 732, 0xAAAAAAAA, 4)))})
    compare(baseline(), "available", 0,
            plan={(PRIORITY, 0): (0, ((STATE + 708, 0x80000000, 4), (STATE + 732, 0xFFFFFFFF, 4)))})

    # Polling can change not-yet-checksummed bytes; the checksum is not a snapshot.
    memory = baseline()
    memory[10][:513] = bytes(513)
    compare(memory, "checksum", 513, plan={POLL: (0, ((PAYLOAD_BUFFER + 256, 0x77, 1),))})
    payload = bytes(513)
    mutated = payload[:256] + b"\x77" + payload[257:]
    compare(baseline(), "record", 0xBF000, TAG, 1490,
            regions=((0xBF000, record(payload)),),
            plan={POLL: (0, ((PAYLOAD_BUFFER + 256, 0x77, 1), (HEADER_BUFFER + 8, zlib.crc32(mutated), 4)))})

    # A transient failure remains cached until preparation invalidates that bit.
    good = ((0xBF000, record(b"valid")),)
    memory, _ = compare(baseline(), "available", 0, regions=good, failures={1: (1, 0)}, sequence=True)
    memory, cached = compare(memory, "available", 0, regions=good, sequence=True)
    assert cached == 0
    memory, restored = compare(memory, "available", 0, regions=good, sequence=True,
                               plan={PREPARE: (0, ((STATE + 708, 0, 4),))})
    assert restored == 1
    _, stale = compare(memory, "available", 0, sequence=True)
    assert stale == 1

    for case in range(120):
        length = rng.randrange(97)
        payload = rng.randbytes(length)
        preset = rng.randrange(32)
        address = 0xBF000 + (preset // 2) * 4096 + (preset % 2) * 2048
        memory = baseline()
        memory[1][:] = rng.randbytes(1860)
        struct.pack_into("<I", memory[1], 708, rng.getrandbits(32) & ~(1 << preset))
        memory[8][:] = rng.randbytes(256)
        operation = "available" if case % 2 else "record"
        args = (preset,) if operation == "available" else (address, TAG, 1490)
        compare(memory, operation, *args, regions=((address, record(payload,
            tag=TAG if case % 7 else 0, crc=zlib.crc32(payload) ^ (case % 3 == 0))),),
            failures={2: (1, rng.randrange(length + 1))} if case % 5 == 0 else None)

    for target in (0, 1, 15, 31):
        address = 0xBF000 + (target // 2) * 4096 + (target % 2) * 2048
        regions = ((address, record(b"navigation")),)
        for step in (1, 0xFFFFFFFF):
            compare(baseline(), "preset_step", step, regions=regions)
        memory = baseline()
        memory[0][236:239] = bytes((2, target, 3))
        compare(memory, "action", 0, 0, regions=regions)
    memory = baseline()
    memory[0][236] = 3
    regions = ((0xC0000, record(b"next")),)
    compare(memory, "edge", 0, 1, 100, 200, regions=regions)
    memory = baseline()
    memory[0][239:242] = bytes((2, 2, 255))
    memory[1][1567] = 1
    compare(memory, "tick", 1000, regions=regions)
    compare(baseline(), "preset_step", 1,
            regions=((0xBF800, record(b"load fails")), (0xC0000, record(b"load succeeds"))),
            plan={(LOAD, 1): (1, ()), (LOAD, 2): (0, ((GLOBAL + 92, 2, 4),))})
    print("Stateful cache and integrated navigation comparisons passed.", flush=True)

    # New API invalid inputs must leave outputs and callbacks untouched.
    state = CState(baseline())
    seen = []
    call = SERVICE_CALLBACK(lambda *args: seen.append(args) or 0)
    read = READ_CALLBACK(lambda *args: seen.append(args) or 0)
    io = IO(call, read, None)
    untouched_result = ctypes.c_uint32(0xDEADBEEF)
    invalid = [
        ("available", (None, 0, ctypes.byref(io)), -1),
        ("available", (ctypes.byref(state.storage), 0, None), -1),
        ("header", (0xBF000, TAG, 1490, None, ctypes.byref(io)), -1),
        ("record", (0xBF000, TAG, 1491, state.header, state.payload, 1491, ctypes.byref(io)), -4),
        ("record", (0xBF000, TAG, 1490, state.header, state.payload, 1489, ctypes.byref(io)), -4),
        ("record", (0xBF000, TAG, 0, state.header, None, 0, ctypes.byref(io)), -4),
        ("crc_update", (0, None, 1, ctypes.byref(untouched_result)), -1),
        ("crc_update", (0, state.payload, 1491, ctypes.byref(untouched_result)), -1),
        ("crc_update", (0, state.payload, 0, None), -1),
        ("checksum", (None, 1, ctypes.byref(untouched_result), ctypes.byref(io)), -1),
        ("checksum", (state.payload, 1491, ctypes.byref(untouched_result), ctypes.byref(io)), -1),
        ("action", (ctypes.byref(state.storage), 4, 0, ctypes.byref(io)), -1),
        ("action", (ctypes.byref(state.storage), 0, 3, ctypes.byref(io)), -1),
        ("edge", (ctypes.byref(state.storage), 5, 1, 0, 0, ctypes.byref(io)), -1),
        ("edge", (ctypes.byref(state.storage), 0, 2, 0, 0, ctypes.byref(io)), -1),
    ]
    for operation, arguments, expected in invalid:
        before = state.snapshot()
        assert functions[operation](*arguments) == expected
        assert state.snapshot() == before and not seen and untouched_result.value == 0xDEADBEEF
    for bad_io in (IO(SERVICE_CALLBACK(), read, None), IO(call, READ_CALLBACK(), None)):
        before = state.snapshot()
        assert functions["available"](ctypes.byref(state.storage), 0, ctypes.byref(bad_io)) == -1
        assert state.snapshot() == before and not seen
    empty_result = ctypes.c_uint32(123)
    assert functions["crc_update"](0x12345678, None, 0, ctypes.byref(empty_result)) == 0
    assert empty_result.value == 0x12345678
    assert functions["checksum"](None, 0, ctypes.byref(empty_result), ctypes.byref(io)) == 0
    assert empty_result.value == 0 and not seen

    new_code = set(native.code) - native.pre_storage_code
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
        for regions, raw_regions in ((REGIONS, native.storage_regions), (SELECTION_REGIONS, native.selection_regions),
                                      (ACTION_REGIONS, native.raw_regions)):
            for name, (start, end) in regions.items():
                if app[start - 0x02000120:end - 0x02000120] != raw_regions[name]:
                    raise ValueError(f"MINI {name} region differs")
        for region in (native.controls.transition, native.controls.immediate):
            if app[region.start - 0x02000120:region.end - 0x02000120] != region.raw:
                raise ValueError("MINI transition/policy differs")
        mini_binding = {"image_sha256": digest, "all_twenty_one_regions_byte_identical": True}
    previous_sources = ["tools/selection_machine.py", "tools/control_action_machine.py", "tools/control_machine.py",
                        "tools/dot_machine.py", "tools/verify_selection.py", "tools/verify_control_actions.py", "tools/verify_controls.py"]
    sources = previous_sources + ["tools/preset_storage_machine.py", "tools/verify_preset_storage.py",
        "tools/build_preset_storage.py", "tests/test_preset_storage_machine.py"]
    for component in ("controls", "control_actions", "selection", "preset_storage"):
        sources += [f"firmware/src/hyperrig_{component}.c", f"firmware/include/hyperrig/hyperrig_{component}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
                "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {
        "schema": 1, "result": "pass", "project": "HyperRig",
        "scope": "preset addresses, header/record checks, CRC and availability cache integrated with selection",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
                      "bytes_sha256": hashlib.sha256(native.storage_regions[name]).hexdigest()}
                      for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "subsets": subsets,
        "zlib_reference_checks": crc_reference_checks, "invalid_api_checks": len(invalid) + 2,
        "null_data_empty_crc_checks": 2,
        "instruction_coverage": {"new_visited": len(coverage & new_code), "new_decoded": len(new_code),
                                 "all_visited": len(coverage), "all_decoded": len(native.code), "unvisited_new": missing},
        "external_services_visited": ["read" if address == READ else STORAGE_LEAVES[address][0] for address in sorted(services)],
        "compared": ["all previous runtime bytes", "16 pair mappings", "256 scratch bytes",
                     "40 public header bytes", "1490 public payload bytes", "return/result values",
                     "ordered semantic service/read arguments, destinations and mapped bytes at each call"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["scripted original read-wrapper boundary; no flash hardware access",
                        "storage preparation, priority and polling remain external",
                        "record validation does not deserialize, migrate, apply or persist a preset",
                        "CRC comparison and new record APIs bounded to 1490 payload bytes",
                        "no concurrency, three-switch bank change or Alpha 13 implementation"],
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
