"""Compare journal writes using synthetic byte storage, never physical devices."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from capture_journal_machine import (CaptureJournalProgram, REGIONS, PAYLOAD, SCRATCH, ROOT,
    PROGRAM, RAW_READ, WRAPPED_READ, ERASE_SECTOR, CLOCK, ELAPSED, PREPARE, MODE, ACTIVITY,
    GATE, EVENT, NOTIFY, WAIT_READY, YIELD, HEADER_BUFFER, DETAILS)
from capture_metadata_machine import CACHE, REGIONS as METADATA_REGIONS
from preset_storage_machine import REGIONS as STORAGE_REGIONS
from verify_capture_metadata import (baseline as metadata_baseline, CState as MetadataState,
    CMemory as MetadataMemory, MetadataRuntime)
from verify_control_actions import Runtime, SERVICE_CALLBACK, snapshot as control_snapshot
from control_machine import STATE

U32, POINTER = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)
PROGRAM_CALLBACK = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, POINTER, U32)
READ_CALLBACK = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, U32, POINTER, U32)


def baseline(size=64, cursor=0, capacity=4):
    memory = metadata_baseline(size) + (bytearray((i * 37 + 11) & 255 for i in range(8192)), bytearray([0xA6] * 256))
    for slot in range(15):
        memory[15][slot*20 + 16] = 1
    memory[16][:] = struct.pack("<IIII", 17, 0xFFFFFFFF, cursor, capacity)
    return memory


class SyntheticStorage:
    """RAM-only transfer script. Its byte updates do not model flash hardware."""
    def __init__(self, regions=(), programs=None, reads=None, results=None, mutations=None):
        self.data = {(address + i) & 0xFFFFFFFF: byte for address, data in regions for i, byte in enumerate(data)}
        self.programs, self.reads, self.results, self.mutations = programs or {}, reads or {}, results or {}, mutations or {}
        self.counts = {}

    def __call__(self, service, args, view):
        index = self.counts.get(service, 0)
        self.counts[service] = index + 1
        for address, value, width in self.mutations.get((service, index), ()):
            view.write(address, value, width)
        if service == PROGRAM:
            address, _, _, data = args
            result, committed = self.programs.get(index, (len(data), len(data)))
            for i, byte in enumerate(data[:committed]):
                self.data[(address + i) & 0xFFFFFFFF] = byte
            return result & 0xFFFFFFFF
        if service in (RAW_READ, WRAPPED_READ):
            address, _, _, size = args
            result, prefix, corrupt = self.reads.get((service, index), (0, size, None))
            data = bytearray(self.data.get((address + i) & 0xFFFFFFFF, 255) for i in range(min(size, prefix)))
            if corrupt is not None and corrupt < len(data):
                data[corrupt] ^= 1
            return result & 0xFFFFFFFF, bytes(data)
        if service == ERASE_SECTOR:
            for i in range(4096):
                self.data[(args[2] + i) & 0xFFFFFFFF] = 255
        default = 0x10000000 + 17*index if service == CLOCK else 0x12345678 if service == ELAPSED else 0
        return self.results.get((service, index), default) & 0xFFFFFFFF


class JournalRuntime(ctypes.Structure):
    _fields_ = [("controls", Runtime), ("metadata", MetadataRuntime), ("scratch", ctypes.c_uint8 * 256)]


class IO(ctypes.Structure):
    _fields_ = [("call", SERVICE_CALLBACK), ("program", PROGRAM_CALLBACK), ("read", READ_CALLBACK), ("opaque", ctypes.c_void_p)]


class CState(MetadataState):
    def __init__(self, memory):
        super().__init__(memory[:17])
        self.journal = JournalRuntime(self.storage.selection.controls, self.metadata,
            (ctypes.c_uint8 * 256).from_buffer_copy(memory[18]))
        self.metadata = self.journal.metadata
        self.data = (ctypes.c_uint8 * 8192).from_buffer_copy(memory[17])

    def snapshot(self):
        previous = super().snapshot()
        return control_snapshot(self.journal.controls) + previous[3:] + (bytes(self.data), bytes(self.journal.scratch))

    def source(self, pointer, size):
        address = ctypes.cast(pointer, ctypes.c_void_p).value
        for array, name in ((self.header, "header"), (self.data, "payload")):
            base = ctypes.addressof(array)
            if base <= address and address + size <= base + ctypes.sizeof(array):
                return name, address - base
        if size == 16:
            return "append_record", 0
        raise ValueError("unknown C program source")

    def target(self, pointer, size):
        address, base = ctypes.cast(pointer, ctypes.c_void_p).value, ctypes.addressof(self.journal.scratch)
        if base <= address and address + size <= base + 256:
            return "verify_payload", address - base
        if size == 16:
            return "append_readback", 0
        if size == 40:
            return "verify_header", 0
        raise ValueError("unknown C read destination")


class CMemory(MetadataMemory):
    def __init__(self, state):
        super().__init__(state)
        self.runtime = state.journal.controls
        for base, array in ((PAYLOAD, state.data), (SCRATCH, state.journal.scratch)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def configure(library):
    runtime, io, result = ctypes.POINTER(JournalRuntime), ctypes.POINTER(IO), ctypes.POINTER(U32)
    specs = {"invalidate": [runtime, U32, U32], "write": [runtime, U32, POINTER, U32, io],
        "write_offset": [runtime, U32, U32, POINTER, U32, io], "erase": [runtime, U32, U32, io],
        "compare": [POINTER, POINTER, U32, result], "rewrite": [runtime, U32, U32, POINTER, POINTER, U32, io],
        "append": [runtime, U32, POINTER, U32, U32, POINTER, U32, result, io]}
    functions = {}
    for operation, arguments in specs.items():
        function = getattr(library, "hyperrig_capture_journal_" + operation)
        function.argtypes, function.restype = arguments, ctypes.c_int
        functions[operation] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program, functions = CaptureJournalProgram(), configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, services = dict.fromkeys(functions, 0), set(), set()
    mutations = 0
    rng = random.Random(0xA622AB96)

    def compare(memory, operation, *args, **script):
        nonlocal mutations
        native_storage, c_storage = SyntheticStorage(**script), SyntheticStorage(**script)
        original = program.execute(memory, operation, *args, boundary=native_storage)
        state, calls, errors, value = CState(memory), [], [], U32(0xCAFEF00D)
        def service_callback(_opaque, service, a, b, c):
            try:
                argv = (a, b, c)
                calls.append((service, argv, state.snapshot()))
                return c_storage(service, argv, CMemory(state))
            except Exception as error:
                errors.append(error)
                return 0
        def program_callback(_opaque, address, source, size):
            try:
                label, offset = state.source(source, size)
                argv = address, label, offset, ctypes.string_at(source, size)
                calls.append((PROGRAM, argv, state.snapshot()))
                return c_storage(PROGRAM, argv, CMemory(state))
            except Exception as error:
                errors.append(error)
                return 0
        def read_callback(_opaque, service, address, destination, size):
            try:
                label, offset = state.target(destination, size)
                argv = address, label, offset, size
                calls.append((service, argv, state.snapshot()))
                result, data = c_storage(service, argv, CMemory(state))
                if data:
                    ctypes.memmove(destination, data, len(data))
                return result
            except Exception as error:
                errors.append(error)
                return 0xFFFFFFFF
        call, write, read = SERVICE_CALLBACK(service_callback), PROGRAM_CALLBACK(program_callback), READ_CALLBACK(read_callback)
        io = IO(call, write, read, None)
        runtime, function = ctypes.byref(state.journal), functions[operation]
        def pointer(offset):
            return ctypes.cast(ctypes.byref(state.data, offset), POINTER)
        if operation == "invalidate":
            assert function(runtime, *args) == 0
            actual = original["result"]  # Native invalidation has no semantic return value.
        elif operation == "write":
            actual = function(runtime, args[0], pointer(args[2]), args[1], ctypes.byref(io))
        elif operation == "write_offset":
            actual = function(runtime, args[0], args[1], pointer(args[3]), args[2], ctypes.byref(io))
        elif operation == "erase":
            actual = function(runtime, *args, ctypes.byref(io))
        elif operation == "compare":
            assert function(pointer(args[0]), pointer(args[1]), args[2], ctypes.byref(value)) == 0
            actual = value.value
        elif operation == "rewrite":
            actual = function(runtime, args[0], args[1], state.header, state.data, args[2], ctypes.byref(io))
        else:
            actual = function(runtime, args[0], state.header, args[1], args[2], state.details, args[3], ctypes.byref(value), ctypes.byref(io))
            assert value.value == (original["allocation"] if actual == 0 else 0xCAFEF00D)
        if errors:
            raise errors[0]
        for index in script.get("programs", {}):
            assert index < native_storage.counts.get(PROGRAM, 0), ("unreached program result", operation, args, index)
        if ((actual & 0xFFFFFFFF) != original["result"] or state.snapshot() != original["memory"] or
                calls != original["calls"] or c_storage.data != native_storage.data):
            changed = {i: [(j, a, b) for j, (a, b) in enumerate(zip(left, right)) if a != b][:12]
                       for i, (left, right) in enumerate(zip(state.snapshot(), original["memory"])) if i != 2 and left != right}
            raise AssertionError((operation, args, actual, original["result"], changed,
                [(x[0], x[1]) for x in calls], [(x[0], x[1]) for x in original["calls"]],
                calls == original["calls"], c_storage.data == native_storage.data))
        counts[operation] += 1
        coverage.update(original["visited"])
        services.update(row[0] for row in calls)
        mutations += bool(script.get("mutations"))
        return original

    for address in (0xBF000, 0xCF000, 0xDF000, 0xE1000, 0xED000, 0xEF000, 0xFF000, 0, 0xFFFFFFFF):
        for delta in (-1, 0, 1):
            for size in (0, 1, 4095, 4096, 8192, 65536, 0xFFFFFFFF):
                compare(baseline(), "invalidate", (address + delta) & 0xFFFFFFFF, size)
    for _ in range(64):
        compare(baseline(), "invalidate", rng.getrandbits(32), rng.getrandbits(32))
    for left in (0, 1, 2, 3):
        for right in (512, 513):
            for size in (0, 1, 2, 3, 4, 7, 16, 255, 256):
                memory = baseline()
                memory[17][right:right+size] = memory[17][left:left+size]
                compare(memory, "compare", left, right, size)
                if size:
                    memory[17][right + size - 1] ^= 1
                    compare(memory, "compare", left, right, size)
    print("Cache invalidation and decoded memcmp comparisons passed.", flush=True)

    for address in (0xBEFFF, 0xBF000, 0xCF0FF, 0xDF000, 0xFEFFF, 0xFF000, 0xFFFFFFF0):
        for size in (0, 1, 15, 16, 255, 256, 257, 8192):
            compare(baseline(), "write", address, size, 0)
    for offset in (0, 1, 15, 127, 255):
        for size in (1, 16, 257, 511):
            compare(baseline(), "write_offset", 0xDF000, offset, size, 3)
    compare(baseline(), "write_offset", 0xFFFF0000, 0xF0000, 16, 0)
    for reported in (0, 1, 255, 256, 257, 0xFFFFFFFF):
        for running in (0, 1):
            memory = baseline()
            struct.pack_into("<I", memory[1], 280, running)
            compare(memory, "write", 0xDF000, 600, 0, programs={0: (reported, min(reported, 256))})
    for address in (0xBE000, 0xBF000, 0xCF000, 0xDF000, 0xE0000, 0xFE000, 0xFF000, 0xDF001, 0xFFFFF000):
        for pages in (0, 1, 2, 64):
            compare(baseline(), "erase", address, pages, results={(ERASE_SECTOR, 0): 0xFFFFFFFF})
    print("Page splitting, short programs, erase wrappers and cache invalidation passed.", flush=True)

    for size in (0, 1, 3, 4, 15, 16, 255, 256, 257, 4096, 8152):
        compare(baseline(size), "rewrite", 0xDF000, 8192, size)
    for address in (0xBE000, 0xBF000, 0xDF001, 0xFE000, 0xFF000, 0xFFFFF000):
        for reservation in (0, 4095, 4096, 8192, 0x10000, 0xFFFFFFFF):
            compare(baseline(64), "rewrite", address, reservation, 64)
    for failed in (0, 1, 2):
        compare(baseline(600), "rewrite", 0xDF000, 8192, 600, programs={failed: (0, 0)})
    for read_index in (0, 1, 2, 3):
        for status, prefix, corrupt in ((0xFFFFFFFF, 0, None), (0x80000000, 16, None), (0, 256, 0), (1, 256, None)):
            compare(baseline(600), "rewrite", 0xDF000, 8192, 600,
                    reads={(RAW_READ, read_index): (status, prefix, corrupt)})
    for size in (0, 3, 64, 8000, 8152):
        for cursor, capacity in ((0, 0), (0, 1), (0, 2), (0, 255), (1, 1), (1, 2), (254, 255), (255, 255)):
            compare(baseline(size, cursor, capacity), "append", 0xDF000, 0x87654321, 0x01019018, 0x87654321)
    for cases in ({0: (0, 0)}, {0: (0, 8), 1: (0, 0)}, {0: (17, 16)}, {0: (0, 0), 1: (0xFFFFFFFF, 4)}):
        compare(baseline(), "append", 0xDF000, 0x87654321, 3, 0, programs=cases)
    for reads in ({(WRAPPED_READ, 0): (1, 0, None)}, {(WRAPPED_READ, 0): (0, 16, 15)},
                  {(WRAPPED_READ, 0): (1, 16, None), (WRAPPED_READ, 1): (1, 8, None)},
                  {(WRAPPED_READ, 0): (0, 16, 0), (WRAPPED_READ, 1): (0, 16, 4)}):
        compare(baseline(), "append", 0xDF000, 0x87654321, 0xFFFFFFFF, 0xFFFFFFFF, reads=reads)
    print("Rewrite verification and two-attempt append continuations passed.", flush=True)

    for service in (PREPARE, MODE, ACTIVITY, CLOCK, PROGRAM, EVENT, NOTIFY, ELAPSED, WAIT_READY, GATE, ERASE_SECTOR, RAW_READ):
        mutations_plan = {(service, 0): ((STATE + 280, 1, 4), (CACHE + 16, 77, 1))}
        compare(baseline(300), "rewrite", 0xDF000, 8192, 300, mutations=mutations_plan)
    # Mutate only at readback boundaries, after all borrowed program sources
    # have been released. Current/future comparisons observe changed bytes;
    # bytes in previously verified chunks are not compared again.
    for read_index, base, region, offset, expected, read_count, corrupt in (
            (0, HEADER_BUFFER, 9, 20, -3, 1, None),
            (0, PAYLOAD, 17, 0, -3, 2, None),
            (1, PAYLOAD, 17, 17, -3, 2, None),
            (2, PAYLOAD, 17, 256, -3, 3, None),
            (3, PAYLOAD, 17, 599, -3, 4, None),
            (1, HEADER_BUFFER, 9, 20, 0, 4, None),
            (2, PAYLOAD, 17, 0, 0, 4, None),
            (0, HEADER_BUFFER, 9, 20, 0, 4, 20),
            (1, PAYLOAD, 17, 17, 0, 4, 17)):
        memory = baseline(600)
        changed = memory[region][offset] ^ 1
        reads = {} if corrupt is None else {(RAW_READ, read_index): (0, 256, corrupt)}
        result = compare(memory, "rewrite", 0xDF000, 8192, 600, reads=reads,
            mutations={(RAW_READ, read_index): ((base + offset, changed, 1),)})
        assert result["result"] == expected & 0xFFFFFFFF
        assert len([row for row in result["calls"] if row[0] == RAW_READ]) == read_count
        assert result["memory"][region][offset] == changed
    for service in (PREPARE, PROGRAM, WRAPPED_READ, ELAPSED, NOTIFY):
        compare(baseline(), "append", 0xDF000, 0x87654321, 23, 0xFFFFFFF0,
            mutations={(service, 0): ((DETAILS, 99, 4), (DETAILS + 8, 250, 4), (DETAILS + 12, 0, 4),
                                     (HEADER_BUFFER + 4, 8000, 4), (CACHE + 17, 0x010203, 3))})
    compare(baseline(), "write", 0xDF000, 600, 0,
        mutations={(PROGRAM, 0): ((STATE + 280, 1, 4),), (YIELD, 0): ((STATE + 280, 0, 4),)})

    state, seen, value = CState(baseline()), [], U32(0xDEADBEEF)
    call = SERVICE_CALLBACK(lambda *args: seen.append(args) or 0)
    write = PROGRAM_CALLBACK(lambda *args: seen.append(args) or 0)
    read = READ_CALLBACK(lambda *args: seen.append(args) or 0)
    io, runtime = IO(call, write, read, None), ctypes.byref(state.journal)
    invalid = [("invalidate", (None, 0, 0)),
        ("write", (runtime, 0, None, 1, ctypes.byref(io))), ("write", (runtime, 0, state.data, 8193, ctypes.byref(io))),
        ("erase", (runtime, 0, 65, ctypes.byref(io))),
        ("compare", (None, state.data, 1, ctypes.byref(value))), ("compare", (state.data, None, 1, ctypes.byref(value))),
        ("compare", (state.data, state.data, 257, ctypes.byref(value))), ("compare", (state.data, state.data, 0, None)),
        ("rewrite", (runtime, 0, 0, None, state.data, 1, ctypes.byref(io))),
        ("rewrite", (runtime, 0, 0, state.header, None, 1, ctypes.byref(io))),
        ("rewrite", (runtime, 0, 0, state.header, state.data, 8153, ctypes.byref(io))),
        ("append", (runtime, 0, None, 0, 0, state.details, 0, ctypes.byref(value), ctypes.byref(io))),
        ("append", (runtime, 0, state.header, 0, 0, None, 0, ctypes.byref(value), ctypes.byref(io))),
        ("append", (runtime, 0, state.header, 0, 0, state.details, 0, None, ctypes.byref(io)))]
    for operation, args in (("write", (runtime, 0, state.data, 1)), ("erase", (runtime, 0, 1)),
                            ("rewrite", (runtime, 0, 0, state.header, state.data, 1)),
                            ("append", (runtime, 0, state.header, 0, 0, state.details, 0, ctypes.byref(value)))):
        invalid.append((operation, (None, *args[1:], ctypes.byref(io))))
        invalid.append((operation, (*args, None)))
        for bad in (IO(SERVICE_CALLBACK(), write, read, None), IO(call, PROGRAM_CALLBACK(), read, None), IO(call, write, READ_CALLBACK(), None)):
            invalid.append((operation, (*args, ctypes.byref(bad))))
    for operation, args in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == -200
        assert state.snapshot() == before and value.value == 0xDEADBEEF and not seen
    assert functions["compare"](None, None, 0, ctypes.byref(value)) == 0 and value.value == 0

    new_code = set(program.code) - program.pre_journal_code
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
        for name, (start, end) in REGIONS.items():
            assert app[start - 0x02000120:end - 0x02000120] == program.journal_regions[name]
        for name in ("crc", "read_adapter"):
            start, end = METADATA_REGIONS[name]
            assert app[start - 0x02000120:end - 0x02000120] == program.metadata_regions[name]
        start, end = STORAGE_REGIONS["crc_update"]
        assert app[start - 0x02000120:end - 0x02000120] == program.storage_regions["crc_update"]
        mini_binding = {"image_sha256": digest,
            "all_eight_regions_and_used_crc_and_read_adapter_dependencies_byte_identical": True,
            "read_adapter": {"start": METADATA_REGIONS["read_adapter"][0],
                "end_exclusive": METADATA_REGIONS["read_adapter"][1],
                "sha256": hashlib.sha256(program.metadata_regions["read_adapter"]).hexdigest()}}
    source_names = ("dot_machine", "control_machine", "control_action_machine", "selection_machine", "preset_storage_machine",
        "preset_preflight_machine", "preset_assets_machine", "capture_metadata_machine", "capture_journal_machine",
        "verify_controls", "verify_control_actions", "verify_selection", "verify_preset_storage", "verify_preset_preflight",
        "verify_preset_assets", "verify_capture_metadata", "verify_capture_journal", "build_capture_journal")
    sources = [f"tools/{name}.py" for name in source_names]
    sources += ["tests/test_capture_journal_machine.py", "tests/capture_journal_sanitize.c"]
    for name in ("controls", "control_actions", "selection", "preset_storage", "capture_metadata", "capture_journal"):
        sources += [f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {"schema": 1, "project": "HyperRig", "result": "pass", "scope": "journal append continuation, rewrite helper and storage/cache wrappers",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "regions": {name: {"start": start, "end_exclusive": end, "sha256": hashlib.sha256(program.journal_regions[name]).hexdigest()}
                    for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "mutating_cases": mutations,
        "invalid_api_checks": len(invalid), "empty_null_check": True,
        "all_scripted_program_results_reached": True,
        "instruction_coverage": {"new_visited": len(coverage & new_code), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": sorted(services), "mini_v4_binding": mini_binding,
        "compared": ["original statuses or explicit continuation exits", "all 19 mapped RAM regions",
            "ordered service calls, program bytes, read destinations/sizes and public state at each boundary",
            "final RAM-only synthetic storage contents", "fallback allocation request"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "physical_writes": False, "firmware_changed": False,
        "limitations": ["append is a bounded command continuation, not the complete text command",
            "allocation, payload reload, retrying fallback and active-gain application remain outside the continuation",
            "page programming, sector erase, physical reads, scheduler, clock and notification bodies are synthetic boundaries",
            "RAM byte storage is a scripted environment, not flash-device behavior, power-loss atomicity or durability"]}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "comparisons", "total_comparisons", "instruction_coverage")}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve completed reports; choose a new output path")
    verify(args.library, args.output, args.mini_image)
