"""Compare asset/application dependencies with original instructions, using synthetic reads."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from preset_assets_machine import (PresetAssetsProgram, REGIONS, EXTRA, ROOT,
    WORKING, PLACEMENT, BRANCHES, RESULT, HEADER_BUFFER, PAYLOAD_BUFFER)
from preset_storage_machine import REGIONS as STORAGE_REGIONS, READ
from verify_preset_preflight import (baseline as preflight_baseline, CState as PreflightState,
    CMemory as PreflightMemory, IO, SERVICE_CALLBACK, READ_CALLBACK)

MARKER = 0x2144DF1C


def baseline():
    return preflight_baseline() + (bytearray([0xD1] * 16), bytearray([0xE2] * 12),
                                  bytearray(struct.pack("<I", 0xAABBCCDD)))


def header(tag=0x4A474B54, size=8152, marker=MARKER):
    return struct.pack("<III", tag, size, marker) + bytes(range(28))


class Reads:
    """Scripted original read-wrapper outcomes, with optional synchronous writes."""
    def __init__(self, script=()):
        self.script, self.requests = script, []

    def read(self, address, size, view):
        self.requests.append((address, size))
        index = len(self.requests) - 1
        if index >= len(self.script):
            raise ValueError("unexpected synthetic asset read")
        status, data, mutations = self.script[index]
        if len(data) > size or (status == 0 and len(data) != size):
            raise ValueError("invalid synthetic read result")
        for destination, value, width in mutations:
            view.write(destination, value, width)
        return status, data


class CState(PreflightState):
    def __init__(self, memory):
        super().__init__(memory[:12])
        self.placement = (ctypes.c_uint8 * 16).from_buffer_copy(memory[12])
        self.branches = (ctypes.c_uint8 * 12).from_buffer_copy(memory[13])
        self.result = ctypes.c_uint32.from_buffer_copy(memory[14])

    def snapshot(self):
        return super().snapshot() + (bytes(self.placement), bytes(self.branches), bytes(self.result))

    def target(self, pointer, size):
        if size == 4:
            return "local_tail", 0
        return super().target(pointer, size)


class CMemory(PreflightMemory):
    def __init__(self, state):
        super().__init__(state)
        arrays = (state.placement, state.branches,
                  (ctypes.c_uint8 * 4).from_buffer(state.result))
        for (base, _), array in zip(EXTRA, arrays):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def configure(library):
    u32, pointer = ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)
    output, io = ctypes.POINTER(u32), ctypes.POINTER(IO)
    signatures = {
        "header": [u32, pointer, u32, output, io], "extended": [u32, u32],
        "identity": [u32, u32, pointer, output], "resolve": [u32, pointer, output, io],
        "mode": [pointer], "layout": [pointer, pointer, pointer],
        "matches": [pointer, u32, u32, u32, u32], "state416": [pointer], "clamp": [u32],
    }
    functions = {}
    for name, arguments in signatures.items():
        function = getattr(library, "hyperrig_asset_" + name)
        function.argtypes = arguments
        function.restype = u32 if name == "clamp" else ctypes.c_int
        functions[name] = function
    return functions


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = PresetAssetsProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage = dict.fromkeys(functions, 0), set()
    mutated = 0
    rng = random.Random(0x6F3A7B9C)

    def compare(memory, operation, *arguments, script=()):
        nonlocal mutated
        native_reads, c_reads = Reads(script), Reads(script)
        original = program.execute(memory, operation, *arguments, reader=native_reads.read)
        state, calls, errors = CState(memory), [], []
        def service_callback(*args):
            errors.append(ValueError("unexpected service callback"))
            return 0
        def read_callback(_opaque, address, destination, size):
            try:
                label, offset = state.target(destination, size)
                calls.append((READ, (address, label, offset, size), state.snapshot()))
                status, data = c_reads.read(address, size, CMemory(state))
                if data:
                    ctypes.memmove(destination, data, len(data))
                return status
            except Exception as error:
                errors.append(error)
                return 1
        call, read = SERVICE_CALLBACK(service_callback), READ_CALLBACK(read_callback)
        io = IO(call, read, None)
        function = functions[operation]
        if operation == "header":
            actual = function(arguments[0], state.header, arguments[1], ctypes.byref(state.result), ctypes.byref(io))
        elif operation == "resolve":
            actual = function(arguments[0], state.header, ctypes.byref(state.result), ctypes.byref(io))
        elif operation == "identity":
            temporary = ctypes.c_uint32(0xDEADBEEF)
            assert function(*arguments, state.payload, ctypes.byref(temporary)) == 0
            actual = temporary.value
        elif operation == "mode":
            actual = function(state.runtime.working)
        elif operation == "layout":
            assert function(state.runtime.working, state.placement, state.branches) == 0
            actual = original["result"]  # Original function has no semantic return value.
        elif operation == "matches":
            actual = function(state.payload, *arguments)
        elif operation == "state416":
            actual = function(state.runtime.storage.selection.controls.controls.state)
        else:
            actual = function(*arguments)
        if errors:
            raise errors[0]
        if ((actual & 0xFFFFFFFF) != original["result"] or state.snapshot() != original["memory"]
                or calls != original["calls"] or native_reads.requests != c_reads.requests):
            changed = [i for i, (a, b) in enumerate(zip(state.snapshot(), original["memory"])) if a != b]
            raise AssertionError((operation, arguments, actual, original["result"], changed,
                                  calls == original["calls"], c_reads.requests, native_reads.requests))
        counts[operation] += 1
        coverage.update(original["visited"])
        mutated += any(row[2] for row in script)
        return original

    for version in range(256):
        memory = baseline()
        memory[11][0:2] = bytes((version, 16))
        for i in range(16):
            memory[11][12 + 18*i] = i % 3
            memory[11][15 + 18*i] = i % 4
        compare(memory, "layout")
        memory[11][1347] = version
        compare(memory, "mode")
    for version in (0, 1, 2, 3, 4, 5, 255):
        for count in range(256):
            memory = baseline()
            memory[11][:] = rng.randbytes(1490)
            memory[11][0:2] = bytes((version, count))
            for i in range(16):
                memory[11][12 + 18*i] = rng.choice((0, 1, 2, 255))
                memory[11][15 + 18*i] = rng.choice((0, 1, 2, 3, 255))
            compare(memory, "layout")
    for flag in range(256):
        memory = baseline()
        memory[10][:16] = struct.pack("<BB2xIII", flag, flag, 0x80000000, 0xFFFFFFFF, 0x12345678)
        compare(memory, "matches", 0x80000000, 0xFFFFFFFF, 0x12345678, flag)
    for word_index in range(4):
        for different in (0, 1, 0xFF, 0x100, 0x80000000, 0xFFFFFFFF):
            memory = baseline()
            memory[10][:16] = struct.pack("<BB2xIII", 1, 2, 3, 4, 5)
            args = [3, 4, 5, 2]
            args[word_index] = different
            compare(memory, "matches", *args)
    for value in [0, 1, 399, 400, 401, 2999, 3000, 3001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF] + [rng.getrandbits(32) for _ in range(128)]:
        compare(baseline(), "clamp", value)
        memory = baseline()
        struct.pack_into("<I", memory[1], 416, value)
        compare(memory, "state416")
    for marker in (0, 1, MARKER, MARKER - 1, MARKER + 1, 0xFFFFFFFF):
        for size in (0, 1, 4, 7, 8, 9, 8152, 0x80000000, 0xFFFFFFFF):
            compare(baseline(), "extended", marker, size)
            for tail in (0, 0x01020304, 0x80000000, 0xFFFFFFFF):
                memory = baseline()
                struct.pack_into("<I", memory[10], 0, tail)
                compare(memory, "identity", marker, size)
    print("Layout, descriptors, flag and arithmetic comparisons passed.", flush=True)
    for slot in (0, 1, 7, 8, 14, 15, 0x7FFFF, 0x80000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for maximum in (0, 8152, 0xFFFFFFFF):
            for tag in (0x4A474B54, 0x49474B54, 0, 0x43474B54):
                for size in (0, 8152, 8153, 0xFFFFFFFF):
                    data = header(tag, size)
                    accepted_j = tag == 0x4A474B54 and size <= maximum
                    script = [(0, data, ())] if accepted_j else [(0, data, ()), (0, data, ())]
                    compare(baseline(), "header", slot, maximum, script=script)
    for prefix in (0, 1, 4, 8, 39, 40):
        for fail_second in (False, True):
            for first_code in (1, 0xFFFFFFFF):
                data = header(0x49474B54, 16)
                second = (1, data[:prefix], ()) if fail_second else (0, data, ())
                compare(baseline(), "header", 3, 8152,
                        script=[(first_code, header()[:prefix], ()), second])
    # Reads can change output format synchronously; acceptance overwrites it only for J.
    for tag in (0x4A474B54, 0x49474B54, 0):
        data = header(tag, 10)
        script = [(0, data, ((RESULT, 37, 4),))]
        if tag != 0x4A474B54:
            script.append((0, data, ((RESULT, 55, 4),)))
        compare(baseline(), "header", 0, 8152, script=script)
    for slot in (0, 1, 7, 8, 14, 15, 0x7FFFF, 0x80000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for size in (0, 7, 8, 9, 8152, 0x80000000, 0xFFFFFFFF):
            for marker in (MARKER, MARKER + 1, 0):
                memory = baseline()
                memory[9][:] = header(0x43474B54, size, marker)
                script = [(0, b"\x01\x23\x45\x67", ())] if marker == MARKER and size > 7 else []
                compare(memory, "resolve", slot, script=script)
    for prefix in range(5):
        memory = baseline()
        memory[9][:] = header()
        compare(memory, "resolve", 8, script=[(0xFFFFFFFF, b"\x01\x23\x45\x67"[:prefix], ())])
    for new_size in (0, 7, 8, 8152, 0xFFFFFFFF):
        for new_marker in (MARKER, 0, 0x87654321):
            memory = baseline()
            memory[9][:] = header()
            mutations = ((HEADER_BUFFER + 4, new_size, 4), (HEADER_BUFFER + 8, new_marker, 4))
            compare(memory, "resolve", 8, script=[(0, b"\x01\x23\x45\x67", mutations)])
    print("Header fallback, trailer reads, failures and callback mutation comparisons passed.", flush=True)

    state, calls = CState(baseline()), []
    call = SERVICE_CALLBACK(lambda *args: calls.append(args) or 0)
    read = READ_CALLBACK(lambda *args: calls.append(args) or 0)
    io = IO(call, read, None)
    no_call, no_read = IO(SERVICE_CALLBACK(), read, None), IO(call, READ_CALLBACK(), None)
    invalid = [
        ("header", (0, None, 0, ctypes.byref(state.result), ctypes.byref(io)), -1),
        ("header", (0, state.header, 0, None, ctypes.byref(io)), -1),
        ("header", (0, state.header, 0, ctypes.byref(state.result), None), -1),
        ("header", (0, state.header, 0, ctypes.byref(state.result), ctypes.byref(no_call)), -1),
        ("header", (0, state.header, 0, ctypes.byref(state.result), ctypes.byref(no_read)), -1),
        ("resolve", (0, None, ctypes.byref(state.result), ctypes.byref(io)), -2),
        ("resolve", (0, state.header, None, ctypes.byref(io)), -2),
        ("resolve", (0, state.header, ctypes.byref(state.result), None), -2),
        ("resolve", (0, state.header, ctypes.byref(state.result), ctypes.byref(no_read)), -2),
        ("identity", (0, 0, None, ctypes.byref(state.result)), -1),
        ("identity", (0, 0, state.payload, None), -1),
        ("layout", (None, state.placement, state.branches), -1),
        ("layout", (state.runtime.working, None, state.branches), -1),
        ("layout", (state.runtime.working, state.placement, None), -1),
        ("mode", (None,), -1), ("matches", (None, 0, 0, 0, 0), -1),
        ("state416", (None,), -1),
    ]
    for operation, args, expected in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == expected, operation
        assert not calls and state.snapshot() == before, operation

    new_code = set(program.code) - program.pre_assets_code
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
            assert app[start - 0x02000120:end - 0x02000120] == program.assets_regions[name]
        start, end = STORAGE_REGIONS["header"]
        assert app[start - 0x02000120:end - 0x02000120] == program.storage_regions["header"]
        mini_binding = {"image_sha256": digest, "all_nine_regions_and_shared_header_byte_identical": True}
    sources = [f"tools/{name}.py" for name in ("dot_machine", "control_machine", "control_action_machine",
        "selection_machine", "preset_storage_machine", "preset_preflight_machine", "preset_assets_machine",
        "verify_controls", "verify_control_actions", "verify_selection", "verify_preset_storage",
        "verify_preset_preflight", "verify_preset_assets", "build_preset_assets")]
    sources += ["tests/test_preset_assets_machine.py"]
    for name in ("controls", "control_actions", "selection", "preset_storage", "preset_assets", "preset_preflight"):
        sources += [f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"]
    sources += ["upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
                "upstream/pi32v2-isa/isa/pi32v2.toml"]
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "asset metadata, identities, reuse descriptors and working-preset routing helpers",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.assets_regions[name]).hexdigest()}
            for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()),
        "mutating_read_cases": mutated, "invalid_api_checks": len(invalid),
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": ["read"],
        "compared": ["semantic results", "all previous mapped bytes", "placement, branch and result bytes",
                     "ordered read addresses, destinations, sizes and mapped state at each call"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["top-level application and asset payload loading remain external",
            "read wrapper, flash range behavior, concurrency and persistence are not reconstructed here",
            "no claim of live routing application, payload CRC validation, timing units or musical semantics"]}
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
