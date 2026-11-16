"""Compare capture journal/cache C with original instructions and synthetic reads."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib

from capture_metadata_machine import CaptureMetadataProgram, REGIONS, CACHE, DETAILS, ROOT, HEADER_BUFFER, PAYLOAD_BUFFER
from preset_storage_machine import READ, REGIONS as STORAGE_REGIONS
from verify_preset_assets import baseline as asset_baseline, CState as AssetState, CMemory as AssetMemory
from verify_preset_storage import IO, SERVICE_CALLBACK, READ_CALLBACK

IDENTITY, RESOLVED = 0x12345678, 0x87654321
TAG = 0x54474B54
U32, POINTER = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)


def word(data, offset=0):
    return struct.unpack_from("<I", data, offset)[0]


def capacity(size):
    """Independent test-fixture layout, not the instruction reference."""
    if size > 8152:
        return 0
    end, start = (size + 4135) & ~4095, (size + 55) & ~15
    return max(0, (end - start) // 16)


def slot_address(slot):
    if 8 <= slot < 0x80000000:
        return (0xCF000 + ((slot - 8) << 13)) & 0xFFFFFFFF
    return (0xDF000 + (slot << 13)) & 0xFFFFFFFF


def baseline(size=8000, fallback=17):
    memory = asset_baseline() + (bytearray([0x9D] * 300), bytearray([0xB4] * 16))
    memory[9][:] = struct.pack("<IIII", 0x43474B54, size, IDENTITY, fallback) + bytes(range(24))
    for i in range(15):
        memory[15][i * 20 + 16] = 0
    return memory


def record(identity=RESOLVED, metadata=3, tag=TAG, corrupt=False):
    data = struct.pack("<III", tag, identity, metadata)
    return data + struct.pack("<I", zlib.crc32(data) ^ int(corrupt))


def journal(size, entries=(), base=0xDF000):
    start = (size + 55) & 0xFFFFFFF0
    return [((base + start + index * 16) & 0xFFFFFFFF, data) for index, data in entries]


class Flash:
    """Read script only: unspecified bytes are erased, and no writes persist."""
    def __init__(self, regions=(), failures=None, plan=None):
        self.data = {(address + i) & 0xFFFFFFFF: byte for address, data in regions for i, byte in enumerate(data)}
        self.failures, self.plan, self.requests = failures or {}, plan or {}, []

    def read(self, address, size, view):
        self.requests.append((address, size))
        index = len(self.requests) - 1
        for target, value, width in self.plan.get(index, ()):
            view.write(target, value, width)
        status, prefix = self.failures.get(index, (0, size))
        data = bytes(self.data.get((address + i) & 0xFFFFFFFF, 255) for i in range(min(size, prefix)))
        return status & 0xFFFFFFFF, data


class MetadataRuntime(ctypes.Structure):
    _fields_ = [("cache", ctypes.c_uint8 * 300)]


class CState(AssetState):
    def __init__(self, memory):
        super().__init__(memory[:15])
        self.metadata = MetadataRuntime((ctypes.c_uint8 * 300).from_buffer_copy(memory[15]))
        self.details = (ctypes.c_uint8 * 16).from_buffer_copy(memory[16])

    def snapshot(self):
        return super().snapshot() + (bytes(self.metadata.cache), bytes(self.details))

    def target(self, pointer, size):
        if 0 < size <= 256 and size % 16 == 0:
            return "journal_chunk", 0
        return super().target(pointer, size)


class CMemory(AssetMemory):
    def __init__(self, state):
        super().__init__(state)
        for base, array in ((CACHE, state.metadata.cache), (DETAILS, state.details)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def configure(library):
    io, output = ctypes.POINTER(IO), ctypes.POINTER(U32)
    signatures = {"capacity": [U32], "erased": [POINTER, U32], "crc": [POINTER, U32, output],
        "scan": [U32, POINTER, U32, POINTER, io],
        "lookup": [ctypes.POINTER(MetadataRuntime), U32, POINTER, U32, POINTER, output, io]}
    functions = {}
    for name, args in signatures.items():
        function = getattr(library, "hyperrig_capture_metadata_" + name)
        function.argtypes, function.restype = args, U32 if name == "capacity" else ctypes.c_int
        functions[name] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = CaptureMetadataProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage = dict.fromkeys(functions, 0), set()
    subsets = {"mutating_read_cases": 0, "stateful_lookups": 0, "crc_zlib_checks": 0}
    rng = random.Random(0x7CBA7DBE)

    def compare(memory, operation, *arguments, regions=(), failures=None, plan=None, sequence=False):
        native_flash, c_flash = Flash(regions, failures, plan), Flash(regions, failures, plan)
        original = program.execute(memory, operation, *arguments, reader=native_flash.read)
        state, calls, errors = CState(memory), [], []
        def read_callback(_opaque, address, destination, size):
            try:
                label, offset = state.target(destination, size)
                calls.append((READ, (address, label, offset, size), state.snapshot()))
                status, data = c_flash.read(address, size, CMemory(state))
                if data:
                    ctypes.memmove(destination, data, len(data))
                return status
            except Exception as error:
                errors.append(error)
                return 1
        read = READ_CALLBACK(read_callback)
        io, value = IO(SERVICE_CALLBACK(), read, None), U32(0xDEADBEEF)
        function = functions[operation]
        if operation == "capacity":
            actual = function(*arguments)
        elif operation == "erased":
            actual = function(state.payload, arguments[0])
        elif operation == "crc":
            assert function(state.payload, arguments[0], ctypes.byref(value)) == 0
            actual = value.value
            assert actual == zlib.crc32(memory[10][:arguments[0]])
            subsets["crc_zlib_checks"] += 1
        elif operation == "scan":
            actual = function(arguments[0], state.header, arguments[1], state.details, ctypes.byref(io))
        else:
            assert function(ctypes.byref(state.metadata), arguments[0], state.header, arguments[1],
                state.details if arguments[2] else None, ctypes.byref(value), ctypes.byref(io)) == 0
            actual = value.value
        if errors:
            raise errors[0]
        if ((actual & 0xFFFFFFFF) != original["result"] or state.snapshot() != original["memory"]
                or calls != original["calls"] or c_flash.requests != native_flash.requests):
            changed = {i: [(j, a, b) for j, (a, b) in enumerate(zip(left, right)) if a != b][:20]
                       for i, (left, right) in enumerate(zip(state.snapshot(), original["memory"]))
                       if i != 2 and left != right}
            raise AssertionError((operation, arguments, actual, original["result"], changed,
                [(x[0], x[1]) for x in calls], [(x[0], x[1]) for x in original["calls"]], calls == original["calls"]))
        counts[operation] += 1
        coverage.update(original["visited"])
        subsets["mutating_read_cases"] += bool(plan)
        subsets["stateful_lookups"] += sequence
        return original

    for size in list(range(8154)) + [0x7FFFFFFF, 0x80000000, 0xFFFFFFD0, 0xFFFFFFFF] + [rng.getrandbits(32) for _ in range(128)]:
        result = compare(baseline(), "capacity", size)
        assert result["result"] == capacity(size)
    for size in range(257):
        for pattern in (255, None):
            memory = baseline()
            memory[10][:size] = bytes([pattern] * size) if pattern is not None else rng.randbytes(size)
            compare(memory, "erased", size)
            compare(memory, "crc", size)
    for position in range(16):
        memory = baseline()
        memory[10][:16] = bytes([255] * 16)
        memory[10][position] = 254
        compare(memory, "erased", 16)
    print("Capacity domain, erased bytes and independent CRC checks passed.", flush=True)

    sizes = (0, 1, 8, 64, 3769, 3785, 4000, 4025, 4040, 4041, 4056, 4057, 4096, 8000, 8152, 8153, 0xFFFFFFFF)
    for size in sizes:
        compare(baseline(size), "scan", 0xDF000, RESOLVED)
        if capacity(size):
            last = capacity(size) - 1
            entries = ((0, record(metadata=0x01019018)), (last, record(IDENTITY, 0xFFFFFFFF)))
            compare(baseline(size), "scan", 0xDF000, RESOLVED, regions=journal(size, entries))
    variants = [bytes([255] * 16), record(), record(IDENTITY, 77), record(7), record(tag=TAG ^ 1),
                record(corrupt=True), bytes(16), record(metadata=0xDEADBEEF)]
    for first in variants:
        for last in variants:
            compare(baseline(), "scan", 0xDF000, RESOLVED,
                    regions=journal(8000, ((0, first), (3, record(metadata=18)), (8, last))))
    for trial in range(96):
        size = rng.choice((0, 64, 3769, 3785, 4000, 4025, 4057, 8000))
        amount = capacity(size)
        entries = [(i, rng.choice(variants)) for i in range(amount) if rng.randrange(3) == 0]
        compare(baseline(size, rng.getrandbits(32)), "scan", rng.choice((0, 0xDF000, 0xFFFFFFF0)), RESOLVED,
                regions=journal(size, entries, base=0xDF000) if trial % 2 else ())
    for size in (3769, 3785, 4000, 4025):
        chunks = (capacity(size) + 15) // 16
        for failed in range(chunks):
            for prefix in (0, 1, 15, 16, 255, 256):
                compare(baseline(size), "scan", 0xDF000, RESOLVED,
                    regions=journal(size, ((0, record(metadata=99)),)), failures={failed: (0x12345678, prefix)})
    print("Journal records, erased gaps, CRC rejection, chunking and read failures passed.", flush=True)

    for slot in (0, 1, 7, 8, 14, 15, 255, 0x7FFFF, 0x80000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for details in (0, 1):
            compare(baseline(), "lookup", slot, RESOLVED, details,
                    regions=journal(8000, ((8, record(metadata=31)),), base=slot_address(slot)))
    for slot in range(15):
        for field in (None, 0, 4, 8, 16):
            memory = baseline()
            memory[15][slot*20:slot*20+17] = struct.pack("<IIIIB", IDENTITY, 8000, RESOLVED, 123, 1)
            if field is not None:
                memory[15][slot*20 + field] ^= 1
            for details in (0, 1):
                compare(memory, "lookup", slot, RESOLVED, details,
                        regions=journal(8000, ((4, record(metadata=19)),), base=slot_address(slot)))
    for status in (1, 0xFFFFFFFF, 0x80000000):
        for details in (0, 1):
            first = compare(baseline(3769), "lookup", 8, RESOLVED, details,
                regions=journal(3769, ((0, record(metadata=23)),), base=slot_address(8)), failures={1: (status, 16)})
            second = compare(first["memory"], "lookup", 8, RESOLVED, 0, sequence=True)
            assert not second["calls"] and second["result"] == 17
            compare(second["memory"], "lookup", 8, RESOLVED, 1, sequence=True,
                    regions=journal(3769, ((16, record(metadata=88)),), base=slot_address(8)))

    # Synchronous changes affect late header reads, result state and cache writes.
    for result_status in (0, 1):
        for field, value in ((4, 4041), (8, 7), (12, 0xFEDCBA98)):
            plan = {0: ((HEADER_BUFFER + field, value, 4),)}
            for operation in ("scan", "lookup"):
                arguments = (0xDF000, RESOLVED) if operation == "scan" else (0, RESOLVED, 1)
                compare(baseline(), operation, *arguments, regions=journal(8000, ((8, record(7, 67)),)),
                        failures={0: (result_status, 144)}, plan=plan)
    for new_capacity in (0, 1, 8, 9, 16, 17):
        compare(baseline(), "scan", 0xDF000, RESOLVED,
                regions=journal(8000, ((0, record(metadata=41)), (16, record(metadata=43)))),
                plan={0: ((DETAILS + 12, new_capacity, 4),)})
    for word_offset in (0, 4, 8):
        compare(baseline(), "scan", 0xDF000, RESOLVED,
                plan={0: ((DETAILS + word_offset, 0x11223344, 4),)})
    for slot in (0, 14):
        compare(baseline(), "lookup", slot, RESOLVED, 0,
            plan={0: ((CACHE + slot*20, 0xAAAA5555, 4), (CACHE + slot*20 + 17, 0x010203, 3))})
    print("Cache matches, forced refresh, failure caching and callback mutation passed.", flush=True)

    state, seen = CState(baseline()), []
    read = READ_CALLBACK(lambda *args: seen.append(args) or 0)
    io, missing, output_value = IO(SERVICE_CALLBACK(), read, None), IO(), U32(0xAABBCCDD)
    runtime, value = ctypes.byref(state.metadata), ctypes.byref(output_value)
    invalid = [("erased", (None, 1)), ("erased", (state.payload, 257)),
        ("crc", (None, 1, value)), ("crc", (state.payload, 257, value)), ("crc", (state.payload, 1, None)),
        ("scan", (0, None, 0, state.details, ctypes.byref(io))),
        ("scan", (0, state.header, 0, None, ctypes.byref(io))),
        ("scan", (0, state.header, 0, state.details, None)),
        ("scan", (0, state.header, 0, state.details, ctypes.byref(missing))),
        ("lookup", (None, 0, state.header, 0, None, value, ctypes.byref(io))),
        ("lookup", (runtime, 0, None, 0, None, value, ctypes.byref(io))),
        ("lookup", (runtime, 0, state.header, 0, None, None, ctypes.byref(io))),
        ("lookup", (runtime, 0, state.header, 0, None, value, None)),
        ("lookup", (runtime, 0, state.header, 0, None, value, ctypes.byref(missing)))]
    for operation, args in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == -200
        assert state.snapshot() == before and output_value.value == 0xAABBCCDD and not seen
    assert functions["erased"](None, 0) == 1
    assert functions["crc"](None, 0, value) == 0 and output_value.value == 0

    new_code = set(program.code) - program.pre_metadata_code
    missing_code = sorted(new_code - coverage)
    assert not missing_code, [hex(pc) for pc in missing_code]
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI input is not the reviewed v4 application")
        app = unpack_app(raw)[2]["app.bin"]
        for name, (start, end) in REGIONS.items():
            assert app[start - 0x02000120:end - 0x02000120] == program.metadata_regions[name]
        start, end = STORAGE_REGIONS["crc_update"]
        assert app[start - 0x02000120:end - 0x02000120] == program.storage_regions["crc_update"]
        mini_binding = {"image_sha256": digest, "all_six_regions_and_crc_update_byte_identical": True}
    sources = [f"tools/{name}.py" for name in ("dot_machine", "control_machine", "control_action_machine",
        "selection_machine", "preset_storage_machine", "preset_preflight_machine", "preset_assets_machine", "capture_metadata_machine",
        "verify_controls", "verify_control_actions", "verify_selection", "verify_preset_storage", "verify_preset_preflight",
        "verify_preset_assets", "verify_capture_metadata", "build_capture_metadata")]
    sources += ["tests/test_capture_metadata_machine.py", "tests/capture_metadata_sanitize.c"]
    for name in ("controls", "control_actions", "selection", "preset_storage", "capture_metadata"):
        sources += [f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "capture journal capacity, erased detection, CRC, scan selection and cached metadata lookup",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.metadata_regions[name]).hexdigest()}
            for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "subsets": subsets,
        "invalid_api_checks": len(invalid), "null_empty_checks": 2,
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing_code},
        "external_services_visited": [READ],
        "compared": ["semantic results", "all 17 mapped memory regions", "ordered read addresses/destinations/sizes and state at every read",
                     "cache padding, externally supplied scan results and late callback mutations"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False, "flash_writes": False,
        "limitations": ["physical flash read wrapper and durable journal writes are not reconstructed",
            "read callbacks may mutate public buffers synchronously but must keep result capacity 0..255",
            "no re-entry, concurrent mutation, overlapping storage or retained pointers",
            "no packed gain validity is applied during journal selection; no live DSP/audio equivalence claim"]}
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
