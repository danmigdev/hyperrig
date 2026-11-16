"""Compare capture loading/gain C against original instructions and scripted services."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from capture_loader_machine import (CaptureLoaderProgram, REGIONS, ROOT, GAIN_TABLE,
    GAIN_BYTES, REQUEST, METADATA, INSTALL, LOADER, ACTIVITY, PRIORITY, NOTIFY)
from preset_storage_machine import READ, REGIONS as STORAGE_REGIONS
from preset_assets_machine import REGIONS as ASSET_REGIONS
from control_machine import STATE, GLOBAL
from verify_preset_assets import baseline as asset_baseline, header, Reads, CState, CMemory as AssetMemory, MARKER
from verify_preset_storage import IO, SERVICE_CALLBACK, READ_CALLBACK
from verify_control_actions import Runtime

U32, BYTE_POINTER = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)
METADATA_CALLBACK = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, BYTE_POINTER, U32)
INSTALL_CALLBACK = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, U32, U32, BYTE_POINTER)


class CaptureIO(ctypes.Structure):
    _fields_ = [("storage", IO), ("metadata", METADATA_CALLBACK), ("install", INSTALL_CALLBACK)]


class CMemory(AssetMemory):
    def __init__(self, state, request=None):
        super().__init__(state)
        if request is not None:
            array = (ctypes.c_uint8 * 17).from_address(ctypes.cast(request, ctypes.c_void_p).value)
            self.extra.update({REQUEST + i: (array, i) for i in range(17)})


class Script:
    """Only supplied service results and synchronous writes; no installed DSP model."""
    def __init__(self, plan=None):
        self.plan, self.counts = plan or {}, {}

    def __call__(self, service, args, view):
        index = self.counts.get(service, 0)
        self.counts[service] = index + 1
        result, writes = self.plan.get((service, index), self.plan.get(service, (0, ())))
        for address, value, size in writes:
            view.write(address, value, size)
        return result & 0xFFFFFFFF


def baseline():
    memory = asset_baseline()
    memory[0][9] = 255
    memory[0][18] = 19
    memory[1][1780:1796] = bytes.fromhex("00 ee a1 b2 10203040 50607080 90a0b0c0")
    struct.pack_into("<IIII", memory[1], 264, 2, 0, 1234, 10)
    struct.pack_into("<III", memory[1], 696, 2, 77, 1)
    return memory


def record(size=64, marker=0x12345678, tag=0x43474B54):
    return header(tag, size, marker)


def load_reads(size=64, marker=0x12345678, *, signature=b"A2L1", reuse=False, trailer_status=0):
    reads = [(0, record(size, marker), ())]
    if marker == MARKER and size >= 8:
        reads.append((trailer_status, b"\x01\x23\x45\x67", ()))
    if not reuse:
        reads.append((0, signature, ()))
    return reads


def configure(library):
    runtime, io = ctypes.POINTER(Runtime), ctypes.POINTER(IO)
    signatures = {
        "valid": [U32], "gain_value": [U32], "aux": [U32, ctypes.POINTER(U32)],
        "clamp": [U32], "scale": [U32], "mix": [runtime, U32],
        "set_gain": [runtime, U32, U32], "apply_metadata": [runtime, U32, U32],
        "signature": [U32, BYTE_POINTER, io], "load": [runtime, U32, ctypes.POINTER(CaptureIO)],
    }
    functions = {}
    for name, args in signatures.items():
        function = getattr(library, "hyperrig_capture_" + name)
        function.argtypes, function.restype = args, U32 if name == "scale" else ctypes.c_int
        functions[name] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = CaptureLoaderProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, services = dict.fromkeys(functions, 0), set(), set()
    mutations = 0
    rng = random.Random(0x7E6287CC)

    def compare(memory, operation, *arguments, reads=(), plan=None):
        nonlocal mutations
        native_reads, c_reads = Reads(reads), Reads(reads)
        original = program.execute(memory, operation, *arguments, reader=native_reads.read, boundary=Script(plan))
        state, calls, errors, script = CState(memory), [], [], Script(plan)
        def service_callback(_opaque, service, a, b, c):
            try:
                calls.append((service, (a, b, c), state.snapshot()))
                return script(service, (a, b, c), CMemory(state))
            except Exception as error:
                errors.append(error)
                return 1
        def read_callback(_opaque, address, destination, size):
            try:
                label, offset = state.target(destination, size)
                calls.append((READ, (address, label, offset, size), state.snapshot()))
                result, data = c_reads.read(address, size, CMemory(state))
                if data:
                    ctypes.memmove(destination, data, len(data))
                return result
            except Exception as error:
                errors.append(error)
                return 1
        def metadata_callback(_opaque, slot, supplied_header, identity):
            try:
                args = slot, ctypes.string_at(supplied_header, 40), identity, 0
                calls.append((METADATA, args, state.snapshot()))
                return script(METADATA, args, CMemory(state))
            except Exception as error:
                errors.append(error)
                return 1
        def install_callback(_opaque, source, size, loader, request):
            try:
                args = source, size, loader, ctypes.string_at(request, 17)
                calls.append((INSTALL, args, state.snapshot()))
                return script(INSTALL, args, CMemory(state, request))
            except Exception as error:
                errors.append(error)
                return 1
        call, read = SERVICE_CALLBACK(service_callback), READ_CALLBACK(read_callback)
        metadata, install = METADATA_CALLBACK(metadata_callback), INSTALL_CALLBACK(install_callback)
        io = CaptureIO(IO(call, read, None), metadata, install)
        runtime, function = ctypes.byref(state.storage.selection.controls), functions[operation]
        if operation == "load":
            actual = function(runtime, arguments[0], ctypes.byref(io))
        elif operation == "signature":
            actual = function(arguments[0], state.header, ctypes.byref(io.storage))
        elif operation == "aux":
            actual = function(arguments[0], ctypes.byref(state.result))
        elif operation in ("mix", "set_gain", "apply_metadata"):
            assert function(runtime, *arguments) == 0
            actual = original["result"]  # Original helpers have no semantic return value.
        else:
            actual = function(*arguments)
        if errors:
            raise errors[0]
        if ((actual & 0xFFFFFFFF) != original["result"] or state.snapshot() != original["memory"]
                or calls != original["calls"] or c_reads.requests != native_reads.requests):
            changed = {i: [(j, a, b) for j, (a, b) in enumerate(zip(left, right)) if a != b][:20]
                       for i, (left, right) in enumerate(zip(state.snapshot(), original["memory"]))
                       if i != 2 and left != right}
            raise AssertionError((operation, arguments, actual, original["result"], changed,
                [(x[0], x[1]) for x in calls], [(x[0], x[1]) for x in original["calls"]],
                calls == original["calls"]))
        assert len(c_reads.requests) == len(reads), "unused scripted read"
        counts[operation] += 1
        coverage.update(original["visited"])
        services.update(row[0] for row in calls)
        mutations += bool(plan and any(row[1] for row in plan.values())) or any(row[2] for row in reads)
        return original

    values = list(range(256)) + [0x01000000 | value for value in range(256)]
    values += [(version << 24) | ((aux & 65535) << 8) | (gain & 255)
               for version in (0, 1, 2, 255) for aux in (-32768, -201, -200, -1, 0, 1, 400, 401, 32767)
               for gain in (-25, -24, 0, 24, 25)]
    values += [rng.getrandbits(32) for _ in range(128)]
    for value in values:
        for op in ("valid", "gain_value", "aux"):
            compare(baseline(), op, value)
    gain_values = [value & 0xFFFFFFFF for value in range(-25, 26)] + [0x80000000, 0x7FFFFFFF, 0xFFFFFFFF]
    for value in gain_values:
        compare(baseline(), "clamp", value)
        compare(baseline(), "scale", value)
        for flag in (0, 1, 0xFFFFFFFF):
            compare(baseline(), "set_gain", value, flag)
    for first in range(-24, 25):
        for second in range(-24, 25):
            memory = baseline()
            struct.pack_into("<IIII", memory[1], 264, first & 0xFFFFFFFF, second & 0xFFFFFFFF, 0, 0xFFFFFFFF)
            compare(memory, "mix", (first + second) & 0xFFFFFFFF)
    for first, second in ((0x80000000, 0x7FFFFFFF), (0x7FFFFFFF, 0x80000000), (0, 0), (0xFFFFFFFF, 0)):
        memory = baseline()
        struct.pack_into("<II", memory[1], 264, first, second)
        compare(memory, "mix", 0)
    for value in values[::7]:
        compare(baseline(), "apply_metadata", value, value & 1)
    print("Packed metadata, signed clamps, lookup/mixing and update comparisons passed.", flush=True)

    signatures = (b"A2L1", b"A2L0", b"A2X1", b"AXL1", b"AM2\0", b"AM3\0", b"AM4\0", b"AM1\0", b"AM5\0", b"AM2x", b"xxxx")
    for slot in (0, 7, 8, 14, 0x80000000, 0xFFFFFFFF):
        for size in (0, 3, 4, 63, 64, 6144, 7808, 8152):
            for signature in signatures:
                memory = baseline()
                memory[9][:] = record(size)
                compare(memory, "signature", slot, reads=[(0, signature, ())])
    for prefix in range(5):
        memory = baseline()
        memory[9][:] = record()
        compare(memory, "signature", 8, reads=[(1, b"AM2\0"[:prefix], ())])

    for slot in (0, 7, 8, 14, 15, 0x7FFFF, 0x80000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for size in (0, 3, 4, 7, 8, 63, 64, 6144, 7808, 8152):
            for marker in (0x12345678, MARKER):
                compare(baseline(), "load", slot, reads=load_reads(size, marker), plan={METADATA: (0x01000103, ())})
    for result in (0, 1, -1, -2, -3, -100, -110, 0x80000000):
        for trailer_status in (0, 1):
            compare(baseline(), "load", 8, reads=load_reads(marker=MARKER, trailer_status=trailer_status),
                    plan={METADATA: (0x01019018, ()), INSTALL: (result, ())})
    for size in (3, 64, 6144, 7808):
        for signature in signatures:
            compare(baseline(), "load", 2, reads=load_reads(size, signature=signature))
    for tag, size in ((0, 64), (0x43474B54, 8153), (0x43474B54, 0xFFFFFFFF)):
        compare(baseline(), "load", 3, reads=[(0, record(size, tag=tag), ())])
    for prefix in (0, 1, 4, 8, 39, 40):
        compare(baseline(), "load", 3, reads=[(1, record()[:prefix], ())])
    for prefix in range(5):
        reads = load_reads()
        reads[-1] = (1, b"AM2\0"[:prefix], ())
        compare(baseline(), "load", 3, reads=reads)

    for slot in (0, 7, 8, 14, 255):
        for trailer_status in (0, 1):
            memory = baseline()
            memory[0][9] = slot
            compare(memory, "load", slot, reads=load_reads(marker=MARKER, reuse=True, trailer_status=trailer_status))
    for field in (None, 0, 1, 4, 8, 12):
        memory = baseline()
        memory[1][1780:1796] = struct.pack("<BB2xIII", 1, 0, 0x12345678, 64, 0)
        if field is not None:
            memory[1][1780 + field] ^= 1
        compare(memory, "load", 2, reads=load_reads(reuse=field is None))

    # The callback can modify the initialized request and runtime synchronously.
    for present in (0, 1, 255):
        for result in (0, -3):
            writes = ((REQUEST, 99, 4), (REQUEST + 4, 9000, 4), (REQUEST + 8, 0, 4),
                      (REQUEST + 12, 0x87654321, 4), (REQUEST + 16, present, 1),
                      (STATE + 268, 4, 4), (STATE + 696, 24, 4), (STATE + 700, 9, 4),
                      (STATE + 704, 0, 4), (STATE + 276, 0xFFFFFFFF, 4), (GLOBAL + 9, 77, 1))
            compare(baseline(), "load", 2, reads=load_reads(), plan={METADATA: (0x01FF3804, ()), INSTALL: (result, writes)})
    for service in (ACTIVITY, PRIORITY, METADATA, INSTALL, NOTIFY):
        for index in range(2 if service in (ACTIVITY, PRIORITY) else 1):
            writes = ((STATE + 264, 24, 4), (STATE + 268, 0xFFFFFFE8, 4),
                      (STATE + 276, 0xFFFFFFFF, 4), (STATE + 696, 0xFFFFFFFA, 4),
                      (STATE + 700, 0xFFFFFF38, 4), (STATE + 704, 0, 4), (GLOBAL + 18, 88, 1))
            compare(baseline(), "load", 2, reads=load_reads(), plan={(service, index): (0, writes)})
    compare(baseline(), "load", 2, reads=load_reads(reuse=True),
            plan={(PRIORITY, 1): (0, ((GLOBAL + 9, 2, 1),))})
    reads = load_reads()
    reads[0] = (0, record(), ((STATE + 268, 24, 4),))
    compare(baseline(), "load", 2, reads=reads)
    print("Signature, reuse, installation request, partial rollback and callback mutation comparisons passed.", flush=True)

    state, seen = CState(baseline()), []
    call = SERVICE_CALLBACK(lambda *args: seen.append(args) or 0)
    read = READ_CALLBACK(lambda *args: seen.append(args) or 0)
    metadata = METADATA_CALLBACK(lambda *args: seen.append(args) or 0)
    install = INSTALL_CALLBACK(lambda *args: seen.append(args) or 0)
    io = CaptureIO(IO(call, read, None), metadata, install)
    runtime = ctypes.byref(state.storage.selection.controls)
    missing_read = IO(call, READ_CALLBACK(), None)
    invalid = [("aux", (0, None)), ("mix", (None, 0)), ("set_gain", (None, 0, 0)),
               ("apply_metadata", (None, 0, 0)), ("signature", (0, None, ctypes.byref(io.storage))),
               ("signature", (0, state.header, None)), ("signature", (0, state.header, ctypes.byref(missing_read))),
               ("load", (None, 0, ctypes.byref(io))), ("load", (runtime, 0, None))]
    for bad in (CaptureIO(IO(SERVICE_CALLBACK(), read, None), metadata, install),
                CaptureIO(missing_read, metadata, install),
                CaptureIO(io.storage, METADATA_CALLBACK(), install),
                CaptureIO(io.storage, metadata, INSTALL_CALLBACK())):
        invalid.append(("load", (runtime, 0, ctypes.byref(bad))))
    for operation, args in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == -200
        assert state.snapshot() == before and not seen

    new_code = set(program.code) - program.pre_capture_code
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
        for regions, blobs in ((REGIONS, program.capture_regions), (ASSET_REGIONS, program.assets_regions),
                               ({"header": STORAGE_REGIONS["header"]}, program.storage_regions)):
            for name, (start, end) in regions.items():
                assert app[start - 0x02000120:end - 0x02000120] == blobs[name]
        assert app[GAIN_TABLE - 0x02000120:GAIN_TABLE - 0x02000120 + GAIN_BYTES] == program.gain_table
        mini_binding = {"image_sha256": digest, "all_ten_regions_gain_table_and_used_dependencies_byte_identical": True}
    sources = [f"tools/{name}.py" for name in ("dot_machine", "control_machine", "control_action_machine",
        "selection_machine", "preset_storage_machine", "preset_preflight_machine", "preset_assets_machine", "capture_loader_machine",
        "verify_controls", "verify_control_actions", "verify_selection", "verify_preset_storage", "verify_preset_preflight",
        "verify_preset_assets", "verify_capture_loader", "build_capture_loader")]
    sources += ["tests/test_capture_loader_machine.py"]
    for name in ("controls", "control_actions", "selection", "preset_storage", "preset_assets", "preset_preflight", "capture_loader"):
        sources += [f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "capture slot loading, packed gain metadata, table mixing and signature rejection",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.capture_regions[name]).hexdigest()}
            for name, (start, end) in REGIONS.items()},
        "gain_table": {"start": GAIN_TABLE, "bytes": GAIN_BYTES, "sha256": hashlib.sha256(program.gain_table).hexdigest()},
        "comparisons": counts, "total_comparisons": sum(counts.values()),
        "mutating_boundary_cases": mutations, "invalid_api_checks": len(invalid),
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": sorted(services),
        "compared": ["semantic results", "all 15 mapped memory regions", "ordered semantic callback arguments and mapped state at each call",
                     "40-byte metadata header and 17 initialized installation request bytes", "read addresses, destinations and sizes"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["metadata journal scan and container/DSP installation remain scripted service boundaries",
            "read wrapper, physical storage, scheduler and priority implementations remain external",
            "no claim of complete effect behavior, gain units, persistence, audio quality or hardware equivalence"]}
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
