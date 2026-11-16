"""Compare capture container installation and real record reading with original code."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib

from capture_container_machine import (CaptureContainerProgram, REGIONS, SLOT_REGIONS, ROOT, SERVICES,
    EXTRA, BUFFERS, CAPACITY, KIND, HEAP, SOURCE, CACHED, EMBEDDED, REQUEST, METADATA,
    ALLOCATE, FREE, GATE, MODE, PRIORITY_GET, PRIORITY_SET, PROBE, COMPACT, PREPARE,
    PROCESS_LOAD, CAPABILITIES, CLEANUP, ACTIVITY, NOTIFY, PRIORITY, POLL, LOADER)
from preset_storage_machine import READ, REGIONS as STORAGE_REGIONS
from preset_assets_machine import REGIONS as ASSET_REGIONS
from control_machine import STATE, GLOBAL
from verify_capture_loader import baseline as capture_baseline, Reads, MARKER, METADATA_CALLBACK
from verify_preset_assets import CState as AssetState, CMemory as AssetMemory
from verify_preset_storage import Storage, READ_CALLBACK

U32 = ctypes.c_uint32
BYTE_POINTER = ctypes.POINTER(ctypes.c_uint8)
SERVICE = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, U32, U32, U32, U32)
MAPPING = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, U32, U32, U32)


class Runtime(ctypes.Structure):
    _fields_ = [("storage", Storage), ("kind", ctypes.c_uint8 * 4)]


class IO(ctypes.Structure):
    _fields_ = [("call", SERVICE), ("read", READ_CALLBACK), ("map", MAPPING),
                ("metadata", METADATA_CALLBACK), ("opaque", ctypes.c_void_p)]


def baseline():
    memory = capture_baseline()
    struct.pack_into("<I", memory[0], 24, 0x12345670)
    struct.pack_into("<II", memory[0], 60, CACHED, 321)
    for offset, value in ((204, 0xDEADBEEF), (280, 2), (416, 0), (436, 0xCAFE0001), (676, CACHED)):
        struct.pack_into("<I", memory[1], offset, value)
    memory[1][500] = 7
    return memory + (bytearray(struct.pack("<I", 0xDEADBEEF)), bytearray(17),
        bytearray([0xA6] * CAPACITY), bytearray(b"A2L1" + bytes([0xB7] * (CAPACITY - 4))),
        bytearray(b"A2L1" + bytes([0xC8] * (CAPACITY - 4))), bytearray(b"A2L1" + bytes([0xD9] * (CAPACITY - 4))))


def record(payload=b"A2L1test", *, tag=0x43474B54, size=None, crc=None):
    return struct.pack("<III", tag, len(payload) if size is None else size,
                       zlib.crc32(payload) if crc is None else crc) + bytes(range(28))


def identity(payload):
    crc = zlib.crc32(payload)
    return struct.unpack_from("<I", payload, len(payload) - 4)[0] if len(payload) >= 8 and crc == MARKER else crc


def request(payload=b"A2L1test", slot=2, valid=1):
    return struct.pack("<IIIIB", slot, len(payload), zlib.crc32(payload), identity(payload), valid)


def record_reads(payload=b"A2L1test"):
    return [(0, record(payload), ()), (0, payload, ())]


def slot_reads(payload=b"A2L1test", *, reuse=False):
    reads = [(0, record(payload), ())]
    if len(payload) >= 8 and zlib.crc32(payload) == MARKER:
        reads.append((0, payload[-4:], ()))
    if not reuse:
        reads.append((0, (payload + bytes(4))[:4], ()))
        reads.extend(record_reads(payload))
    return reads


class CState(AssetState):
    def __init__(self, memory, capacity=CAPACITY):
        super().__init__(memory[:15])
        self.container = Runtime(self.storage, (ctypes.c_uint8 * 4).from_buffer_copy(memory[15]))
        self.storage = self.container.storage
        self.request = (ctypes.c_uint8 * 17).from_buffer_copy(memory[16])
        self.buffers = [(ctypes.c_uint8 * CAPACITY).from_buffer_copy(data) for data in memory[17:]]
        self.allocation_size = capacity

    def snapshot(self):
        return super().snapshot() + (bytes(self.container.kind), bytes(self.request)) + tuple(bytes(x) for x in self.buffers)

    def target(self, pointer, size):
        address = ctypes.cast(pointer, ctypes.c_void_p).value
        for (_, label), array in zip(BUFFERS, self.buffers):
            base = ctypes.addressof(array)
            if base <= address <= address + size <= base + CAPACITY:
                return label, address - base
        return super().target(pointer, size)

    def mapping(self, address, count, writable):
        for (base, _), array in zip(BUFFERS, self.buffers):
            if base <= address <= address + count <= base + CAPACITY:
                if (base == EMBEDDED and writable) or (base == HEAP and address + count > base + self.allocation_size):
                    return None
                return ctypes.addressof(array) + address - base
        return None


class CMemory(AssetMemory):
    def __init__(self, state):
        super().__init__(state)
        arrays = [state.container.kind, state.request, *state.buffers]
        for (base, _), array in zip(EXTRA, arrays):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


class Script:
    def __init__(self, plan=None):
        self.plan, self.counts = plan or {}, {}

    def __call__(self, service, args, view):
        index = self.counts.get(service, 0)
        self.counts[service] = index + 1
        default = {ALLOCATE: HEAP, PROBE: 0x1234, CAPABILITIES: 1, PRIORITY_GET: 20}.get(service, 0)
        value, writes = self.plan.get((service, index), self.plan.get(service, (default, ())))
        for address, word, size in writes:
            view.write(address, word, size)
        return value & 0xFFFFFFFF


def configure(library):
    result = {}
    for name, arguments in {
        "install": [ctypes.POINTER(Runtime), U32, U32, U32, BYTE_POINTER, ctypes.POINTER(IO)],
        "read": [U32, U32, BYTE_POINTER, ctypes.POINTER(IO)],
        "slot": [ctypes.POINTER(Runtime), U32, ctypes.POINTER(IO)],
    }.items():
        function = getattr(library, "hyperrig_capture_container_" + name)
        function.argtypes, function.restype = arguments, ctypes.c_int
        result[name] = function
    return result


def c_run(functions, memory, operation, arguments, reads=(), plan=None, missing_map=False):
    state = CState(memory, arguments[0] if operation == "read" else CAPACITY)
    calls, errors, flash, script = [], [], Reads(reads), Script(plan)
    def service(_opaque, svc, a, b, c, d):
        try:
            args = a, b, c, d
            calls.append((svc, args, state.snapshot()))
            result = script(svc, args, CMemory(state))
            if svc == ALLOCATE:
                state.allocation_size = a if result else 0
            return result
        except Exception as error:
            errors.append(error)
            return 1
    def read(_opaque, address, destination, size):
        try:
            label, offset = state.target(destination, size)
            calls.append((READ, (address, label, offset, size), state.snapshot()))
            result, data = flash.read(address, size, CMemory(state))
            if data:
                ctypes.memmove(destination, data, len(data))
            return result
        except Exception as error:
            errors.append(error)
            return 1
    def metadata(_opaque, slot, supplied_header, resolved):
        try:
            args = slot, ctypes.string_at(supplied_header, 40), resolved, 0
            calls.append((METADATA, args, state.snapshot()))
            return script(METADATA, args, CMemory(state))
        except Exception as error:
            errors.append(error)
            return 1
    def mapping(_opaque, address, count, writable):
        return None if missing_map else state.mapping(address, count, writable)
    call_cb, read_cb, metadata_cb, map_cb = SERVICE(service), READ_CALLBACK(read), METADATA_CALLBACK(metadata), MAPPING(mapping)
    io = IO(call_cb, read_cb, map_cb, metadata_cb, None)
    if operation == "install":
        result = functions[operation](ctypes.byref(state.container), *arguments, state.request, ctypes.byref(io))
    elif operation == "slot":
        result = functions[operation](ctypes.byref(state.container), *arguments, ctypes.byref(io))
    else:
        result = functions[operation](HEAP, arguments[0], state.request, ctypes.byref(io))
    if errors:
        raise errors[0]
    return {"result": result & 0xFFFFFFFF, "memory": state.snapshot(), "calls": calls, "reads": flash.requests}


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = CaptureContainerProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, services, moves = dict.fromkeys(functions, 0), set(), set(), 0
    mutated = 0
    rng = random.Random(0x85861ACD8)

    def compare(memory, operation, *arguments, reads=(), plan=None):
        nonlocal moves, mutated
        flash = Reads(reads)
        original = program.execute(memory, operation, *arguments, reader=flash.read, boundary=Script(plan))
        actual = c_run(functions, memory, operation, arguments, reads, plan)
        if any(actual[key] != original[key] for key in ("result", "memory", "calls")) or actual["reads"] != flash.requests:
            diffs = {i: [(j, a, b) for j, (a, b) in enumerate(zip(left, right)) if a != b][:12]
                     for i, (left, right) in enumerate(zip(actual["memory"], original["memory"])) if i != 2 and left != right}
            mismatch = next((i for i, (a, b) in enumerate(zip(actual["calls"], original["calls"])) if a != b), None)
            raise AssertionError((operation, arguments, actual["result"], original["result"], diffs, mismatch,
                actual["calls"][mismatch][:2] if mismatch is not None else len(actual["calls"]),
                original["calls"][mismatch][:2] if mismatch is not None else len(original["calls"])))
        assert len(flash.requests) == len(reads), "unused scripted read"
        counts[operation] += 1
        coverage.update(original["visited"])
        services.update(row[0] for row in original["calls"])
        moves += len(original["library_calls"])
        mutated += bool(plan and any(row[1] for row in plan.values())) or any(row[2] for row in reads)
        return original

    for source in (0, SOURCE, CACHED, EMBEDDED):
        for size in (0, 1, 3, 4, 7, 64, 8192, 8193, 0xFFFFFFFF):
            compare(baseline(), "install", source, size, 0,
                    plan={PROBE: (0 if source == 0 else 0x1234, ())})
    for signature in (b"A2L1", b"A2L0", b"A2X1", b"AXL1", b"AM2\0", b"AM3\0", b"AM4\0", b"AM1\0", b"AM5\0", b"AM2x", b"xxxx"):
        for size in (3, 4, 63, 64, 6144, 7808):
            memory = baseline()
            memory[18][:4] = signature
            compare(memory, "install", SOURCE, size, 0)
    for old_mode in (0, 1, 2, 0xFFFFFFFF):
        for priority in (0, 26, 27, 0xFFFFFFFF):
            for restored in (0, -7):
                memory = baseline()
                struct.pack_into("<I", memory[1], 280, old_mode)
                compare(memory, "install", SOURCE, 8, 0,
                        plan={PRIORITY_GET: (priority, ()), (MODE, 1): (restored, ())})
    for old_pointer in (0, CACHED):
        for source in (SOURCE, EMBEDDED, old_pointer):
            memory = baseline()
            struct.pack_into("<I", memory[1], 676, old_pointer)
            compare(memory, "install", source, 8, 0, plan={PROBE: (0x1234, ())})
    for service in (ALLOCATE, PROBE, COMPACT, PREPARE, PROCESS_LOAD, CAPABILITIES):
        for outcome in (0, 1, 0xFFFFFFFF):
            memory = baseline()
            struct.pack_into("<I", memory[1], 416, 1)
            value = HEAP if service == ALLOCATE and outcome else outcome
            compare(memory, "install", SOURCE, 8, 0, plan={service: (value, ())})
    print("Container signatures, ownership, setup failures and mode/priority comparisons passed.", flush=True)

    for size in (0, 1, 3, 4, 7, 8, 64, 255, 256, 257, 513, 8152):
        payload = rng.randbytes(size)
        memory = baseline()
        memory[16][:] = request(payload)
        compare(memory, "read", CAPACITY, reads=record_reads(payload))
    for body in (b"A2L1", b"A2L1data", b"A2L1" + bytes(range(64))):
        payload = body + struct.pack("<I", zlib.crc32(body))
        assert zlib.crc32(payload) == MARKER
        for present in (0, 1, 255):
            memory = baseline()
            memory[16][:] = request(payload, valid=present)
            if not present:
                struct.pack_into("<I", memory[16], 12, 0xDEADBEEF)
            compare(memory, "read", CAPACITY, reads=record_reads(payload))
            compare(memory, "install", 0, len(payload), LOADER, reads=record_reads(payload))
        compare(baseline(), "slot", 2, reads=slot_reads(payload))
    for slot in (0, 7, 8, 14, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        memory = baseline()
        memory[16][:] = request(slot=slot)
        compare(memory, "read", CAPACITY, reads=record_reads())
        compare(baseline(), "slot", slot, reads=slot_reads())
    for index in (4, 8, 12):
        memory = baseline()
        memory[16][:] = request()
        memory[16][index] ^= 1
        compare(memory, "read", CAPACITY, reads=record_reads())
        compare(memory, "install", 0, 8, LOADER, reads=record_reads())
    for prefix in (0, 1, 4, 8, 39, 40):
        memory = baseline()
        memory[16][:] = request()
        compare(memory, "read", CAPACITY, reads=[(1, record()[:prefix], ())])
        compare(memory, "install", 0, 8, LOADER, reads=[(1, record()[:prefix], ())])
    for tag, size in ((0, 8), (0x43474B54, 8153)):
        compare(baseline(), "read", CAPACITY, reads=[(0, record(tag=tag, size=size), ())])
    for prefix in (0, 1, 7, 8):
        memory = baseline()
        memory[16][:] = request()
        reads = [(0, record(), ()), (1, b"A2L1test"[:prefix], ())]
        compare(memory, "read", CAPACITY, reads=reads)
        compare(memory, "install", 0, 8, LOADER, reads=reads)
    memory = baseline()
    memory[16][:] = request()
    compare(memory, "read", CAPACITY, reads=[(0, record(), ()), (0, b"bad data", ())])
    compare(memory, "install", 0, 8, LOADER, reads=[(0, record(), ()), (0, b"bad data", ())])
    for service, outcome in ((PREPARE, -2), (PROCESS_LOAD, -3), (CAPABILITIES, 0), (COMPACT, -110)):
        memory = baseline()
        struct.pack_into("<I", memory[1], 416, 1)
        compare(memory, "slot", 2, reads=slot_reads(), plan={service: (outcome, ())})
    compare(baseline(), "slot", 2, reads=slot_reads()[:2], plan={ALLOCATE: (0, ())})
    memory = baseline()
    memory[0][9] = 2
    compare(memory, "slot", 2, reads=slot_reads(reuse=True))
    print("Full reader/CRC, extended identity, failures and slot integration comparisons passed.", flush=True)

    for service in (ALLOCATE, NOTIFY, ACTIVITY, GATE, MODE, PRIORITY_GET, PRIORITY_SET,
                    PROBE, COMPACT, PREPARE, PROCESS_LOAD, CAPABILITIES, FREE, CLEANUP):
        for index in range(2 if service in (NOTIFY, MODE, PRIORITY_SET) else 1):
            memory = baseline()
            struct.pack_into("<I", memory[1], 416, 1)
            writes = ((GLOBAL + 24, 0xFFFFFFF0, 4), (STATE + 280, 3, 4),
                      (STATE + 436, 0x98765432, 4), (STATE + 676, SOURCE, 4),
                      (STATE + 500, 99, 1), (KIND, 0xABCDEF01, 4))
            default = {ALLOCATE: HEAP, PROBE: 0x1234, CAPABILITIES: 1, PRIORITY_GET: 20}.get(service, 0)
            plan = {(service, index): (default, writes)}
            if service == CLEANUP:
                plan[PROCESS_LOAD] = (-3, ())
            compare(memory, "install", SOURCE, 8, 0, plan=plan)
    for prefix in (b"AM2\0", b"A2L1"):
        memory = baseline()
        memory[18][:4] = prefix
        compare(memory, "install", SOURCE, 64, 0,
                plan={(ACTIVITY, 1): (0, ((SOURCE, int.from_bytes(b"A2L1", "little"), 4),))})
    # A CRC poll can change later payload bytes and request identity, and the reader
    # must observe them. Compute the header CRC for the final, changed payload.
    payload = b"A2L1" + bytes(508)
    changed = payload[:256] + b"x" + payload[257:]
    memory = baseline()
    memory[16][:] = request(changed, valid=0)
    compare(memory, "read", CAPACITY, reads=[(0, record(changed), ()), (0, payload, ())],
            plan={POLL: (0, ((HEAP + 256, ord("x"), 1), (REQUEST + 12, 123, 4)))})
    memory = baseline()
    memory[16][:] = request()
    reads = record_reads()
    reads[1] = (0, b"A2L1test", ((REQUEST + 4, 9, 4),))
    compare(memory, "read", CAPACITY, reads=reads)
    print("Synchronous service/read mutation comparisons passed.", flush=True)

    state, seen = CState(baseline()), []
    call_cb = SERVICE(lambda *args: seen.append(args) or 0)
    read_cb = READ_CALLBACK(lambda *args: seen.append(args) or 1)
    map_cb = MAPPING(lambda *args: seen.append(args) or None)
    metadata_cb = METADATA_CALLBACK(lambda *args: seen.append(args) or 0)
    io = IO(call_cb, read_cb, map_cb, metadata_cb, None)
    rt = ctypes.byref(state.container)
    invalid = [("install", (None, SOURCE, 8, 0, None, ctypes.byref(io))),
        ("install", (rt, SOURCE, 8, 123, state.request, ctypes.byref(io))),
        ("install", (rt, 0, 8, LOADER, None, ctypes.byref(io))),
        ("install", (rt, SOURCE, 8, 0, None, None)),
        ("read", (HEAP, CAPACITY, None, ctypes.byref(io))),
        ("read", (HEAP, CAPACITY + 1, state.request, ctypes.byref(io))),
        ("read", (HEAP, CAPACITY, state.request, None)),
        ("slot", (None, 0, ctypes.byref(io))), ("slot", (rt, 0, None))]
    for bad in (IO(SERVICE(), read_cb, map_cb, metadata_cb, None),
                IO(call_cb, READ_CALLBACK(), map_cb, metadata_cb, None),
                IO(call_cb, read_cb, MAPPING(), metadata_cb, None)):
        invalid.extend([("install", (rt, SOURCE, 8, 0, None, ctypes.byref(bad))),
                        ("read", (HEAP, CAPACITY, state.request, ctypes.byref(bad))),
                        ("slot", (rt, 0, ctypes.byref(bad)))])
    no_metadata = IO(call_cb, read_cb, map_cb, METADATA_CALLBACK(), None)
    invalid.append(("slot", (rt, 0, ctypes.byref(no_metadata))))
    for operation, args in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == -200
        assert not seen and state.snapshot() == before
    guards = 0
    memory = baseline()
    memory[16][:] = request()
    for op, args in (("read", (4,)), ("install", (0, 4, LOADER))):
        result = c_run(functions, memory, op, args, [(0, record(), ())])
        assert result["result"] == (-201) & 0xFFFFFFFF
        assert len(result["reads"]) == 1 and result["memory"][17] == memory[17]
        guards += 1
    result = c_run(functions, baseline(), "install", (SOURCE, 8, 0), missing_map=True)
    assert result["result"] == (-201) & 0xFFFFFFFF
    guards += 1

    new_code = set(program.code) - program.pre_container_code
    missing = sorted(new_code - coverage)
    assert not missing, [hex(pc) for pc in missing]
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI input is not the reviewed v4 application")
        app = unpack_app(raw)[2]["app.bin"]
        for regions, blobs in ((REGIONS, program.container_regions), (SLOT_REGIONS, program.capture_regions),
                               (ASSET_REGIONS, program.assets_regions), (STORAGE_REGIONS, program.storage_regions)):
            for name, (start, end) in regions.items():
                assert app[start - 0x02000120:end - 0x02000120] == blobs[name]
        mini_binding = {"image_sha256": digest, "both_regions_and_shared_dependencies_byte_identical": True}
    sources = [f"tools/{name}.py" for name in ("dot_machine", "control_machine", "control_action_machine",
        "selection_machine", "preset_storage_machine", "preset_preflight_machine", "preset_assets_machine", "capture_loader_machine", "capture_container_machine",
        "verify_controls", "verify_control_actions", "verify_selection", "verify_preset_storage", "verify_preset_preflight",
        "verify_preset_assets", "verify_capture_loader", "verify_capture_container", "build_capture_container")]
    sources += ["tests/test_capture_container_machine.py"]
    for name in ("controls", "control_actions", "selection", "preset_storage", "preset_assets", "preset_preflight", "capture_loader", "capture_container"):
        sources += [f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "capture container orchestration, actual record/CRC/identity reader, integrated slot loader",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.container_regions[name]).hexdigest()} for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "mutating_boundary_cases": mutated,
        "invalid_api_checks": len(invalid), "new_mapping_capacity_guard_checks": guards, "memmove_contract_calls": moves,
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": sorted(services),
        "compared": ["semantic results", "all 21 mapped memory regions", "ordered service arguments and all mapped state at each boundary",
                     "read addresses, destinations, counts and request identity updates", "copied payload and preserved buffer tails"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["parser/probe, compaction, preparation, DSP load, capability query and cleanup bodies remain scripted",
            "allocator, scheduler, mode/priority, physical read wrapper and metadata lookup remain external",
            "memmove is a bounded library contract; allocations are supplied mapped buffers",
            "no claim of durable storage, complete capture execution, real-time or target audio equivalence"]}
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
