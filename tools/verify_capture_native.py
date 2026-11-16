"""Compare native capture loading with real parser/reset execution and state."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import zlib

from capture_native_machine import CaptureNativeProgram, REGIONS, EXTRA, ARENA, ARENA_BYTES, CONFIG, ROOT
from capture_dispatch_machine import PARSER, RESET, CONTEXT, image_offset
from capture_container_machine import (SOURCE, CACHED, EMBEDDED, HEAP, LOADER, ALLOCATE, FREE,
    METADATA, COMPACT, MODE, PRIORITY_GET, GATE, KIND)
from control_machine import STATE, GLOBAL
from preset_storage_machine import READ, POLL
from verify_capture_dispatch import (CState as DispatchState, CMemory as DispatchMemory, Runtime as DispatchRuntime,
    ContainerIO, SERVICE, MAPPING, READ_CALLBACK, METADATA_CALLBACK, U32, BYTE_POINTER,
    Script, Reads, heap_first, baseline as dispatch_baseline, slot_reads, record_reads, request)
from verify_capture_parser import fixture, crc_blob


class Runtime(ctypes.Structure):
    _fields_ = [("dispatch", DispatchRuntime), ("configuration", ctypes.c_uint8 * 4)]


def put(memory, offset, value, width=4):
    memory[offset:offset + width] = (value & ((1 << (width * 8)) - 1)).to_bytes(width, "little")


def baseline(blob=None, configuration=12):
    blob = fixture() if blob is None else blob
    if len(blob) > 8192:
        raise ValueError("native loading fixture exceeds container domain")
    memory = dispatch_baseline() + (bytearray([0xB7] * ARENA_BYTES), bytearray(struct.pack("<I", configuration)))
    for index in (17, 18, 19):
        memory[index][:len(blob)] = blob
    embedded = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
    memory[20][:len(embedded)] = embedded
    put(memory[0], 64, len(blob))
    put(memory[1], 440, ARENA_BYTES)
    memory[16][:] = request(blob)
    return memory


class CState(DispatchState):
    def __init__(self, memory):
        super().__init__(memory[:27])
        self.native = Runtime(self.dispatch, (ctypes.c_uint8 * 4).from_buffer_copy(memory[28]))
        self.dispatch = self.native.dispatch
        self.container = self.dispatch.container
        self.storage = self.container.storage
        self.arena = (ctypes.c_uint8 * ARENA_BYTES).from_buffer_copy(memory[27])

    def snapshot(self):
        return super().snapshot() + (bytes(self.arena), bytes(self.native.configuration))

    def mapping(self, address, count, writable):
        if ARENA <= address <= address + count <= ARENA + ARENA_BYTES:
            return ctypes.addressof(self.arena) + address - ARENA
        return super().mapping(address, count, writable)


class CMemory(DispatchMemory):
    def __init__(self, state):
        super().__init__(state)
        for (base, _), array in zip(EXTRA, (state.arena, state.native.configuration)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def configure(library):
    rt, io = ctypes.POINTER(Runtime), ctypes.POINTER(ContainerIO)
    signatures = {"size": [rt, U32, U32, ctypes.POINTER(U32), io],
        "probe": [rt, U32, U32, ctypes.POINTER(U32), io],
        "load_context": [rt, U32, U32, U32, U32, io], "load": [rt, U32, U32, U32, U32, io],
        "cleanup": [rt, io], "install": [rt, U32, U32, U32, BYTE_POINTER, io], "slot": [rt, U32, io]}
    functions = {}
    for name, signature in signatures.items():
        fn = getattr(library, "hyperrig_capture_native_" + name)
        fn.argtypes, fn.restype = signature, ctypes.c_int
        functions[name] = fn
    return functions


def c_run(functions, memory, operation, arguments=(), reads=(), plan=None, blocked=None):
    state, calls, errors, flash = CState(memory), [], [], Reads(reads)
    script = Script(plan, heap_first=heap_first(operation, arguments))
    view = CMemory(state)
    def service(_opaque, svc, a, b, c, d):
        try:
            if svc in (PARSER, RESET):
                raise AssertionError("parser/reset escaped to a synthetic service")
            args = a, b, c, d
            calls.append((svc, args, state.snapshot()))
            value = script(svc, args, view)
            if svc == ALLOCATE and value == HEAP:
                state.allocation_size = a
            return value
        except Exception as error:
            errors.append(error)
            return 1
    def read(_opaque, address, destination, size):
        try:
            label, offset = state.target(destination, size)
            calls.append((READ, (address, label, offset, size), state.snapshot()))
            value, data = flash.read(address, size, view)
            if data:
                ctypes.memmove(destination, data, len(data))
            return value
        except Exception as error:
            errors.append(error)
            return 1
    def metadata(_opaque, slot, header, identity):
        try:
            args = slot, ctypes.string_at(header, 40), identity, 0
            calls.append((METADATA, args, state.snapshot()))
            return script(METADATA, args, view)
        except Exception as error:
            errors.append(error)
            return 1
    def mapping(_opaque, address, size, writable):
        return None if blocked and blocked(address, size, writable) else state.mapping(address, size, writable)
    callbacks = SERVICE(service), READ_CALLBACK(read), MAPPING(mapping), METADATA_CALLBACK(metadata)
    io = ContainerIO(*callbacks, None)
    rt, iop, out = ctypes.byref(state.native), ctypes.byref(io), U32(0xDEADBEEF)
    if operation in ("size", "probe"):
        api_status = functions[operation](rt, *arguments, ctypes.byref(out), iop)
        value = out.value
    elif operation == "install":
        api_status = functions[operation](rt, *arguments, state.request, iop)
        value = api_status
    else:
        api_status = functions[operation](rt, *arguments, iop)
        value = api_status
    if errors:
        raise errors[0]
    return {"result": value & 0xFFFFFFFF, "api_status": api_status, "memory": state.snapshot(),
            "calls": calls, "reads": flash.requests}


def compare_one(program, functions, memory, operation, arguments=(), reads=(), plan=None):
    flash = Reads(reads)
    original = program.execute(memory, operation, *arguments, reader=flash.read,
        boundary=Script(plan, heap_first=heap_first(operation, arguments)))
    actual = c_run(functions, memory, operation, arguments, reads, plan)
    if operation in ("size", "probe"):
        assert actual["api_status"] == 0
    if any(actual[key] != original[key] for key in ("result", "memory", "calls")) or actual["reads"] != flash.requests:
        diffs = {i: [(j, a, b) for j, (a, b) in enumerate(zip(left, right)) if a != b][:10]
                 for i, (left, right) in enumerate(zip(actual["memory"], original["memory"])) if i != 2 and left != right}
        mismatch = next((i for i, (a, b) in enumerate(zip(actual["calls"], original["calls"])) if a != b), None)
        raise AssertionError((operation, arguments, actual["result"], original["result"], diffs, mismatch,
            len(actual["calls"]), len(original["calls"])))
    assert len(flash.requests) == len(reads), "unused synthetic read"
    assert not any(service in (PARSER, RESET) for service, _, _ in original["calls"])
    return original


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run without Python optimization")
    program = CaptureNativeProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, digest = {}, set(), hashlib.sha256()
    parser_entries = reset_entries = reset_words = steps = 0
    def compare(memory, operation, *arguments, reads=(), plan=None):
        nonlocal parser_entries, reset_entries, reset_words, steps
        result = compare_one(program, functions, memory, operation, arguments, reads, plan)
        counts[operation] = counts.get(operation, 0) + 1
        coverage.update(result["visited"])
        parser_entries += len(result["parser_entries"])
        reset_entries += result["reset_entries"]
        reset_words += result["reset_words"]
        steps += result["steps"]
        digest.update(struct.pack("<I", result["result"]))
        for i, data in enumerate(result["memory"]):
            digest.update(bytes([data]) if i == 2 else data)
        return result

    blob = fixture()
    for operation in ("size", "probe", "load_context", "load", "install", "cleanup", "slot"):
        arguments = {"size": (SOURCE, len(blob)), "probe": (SOURCE, len(blob)),
            "load_context": (ARENA, ARENA_BYTES, SOURCE, len(blob)), "load": (ARENA, ARENA_BYTES, SOURCE, len(blob)),
            "install": (SOURCE, len(blob), 0), "cleanup": (), "slot": (2,)}[operation]
        compare(baseline(blob), operation, *arguments, reads=slot_reads(blob) if operation == "slot" else ())
    print("Native parser/reset through size, load, recovery, installation and slot loading passed.", flush=True)

    valid_shapes = [(channels, abits, kernel, head, layers)
        for channels in (1, 2, 3, 4, 16) for abits in (16, 32)
        for kernel, head, layers in ((1, 1, 1), (6, 3, 2), (15, 64, 1), (16, 2, 1))]
    for channels, abits, kernel, head, layers in valid_shapes:
        payload = fixture(channels=channels, abits=abits, kernel=kernel, head=head, layers=layers)
        if len(payload) > 8192:
            continue
        memory = baseline(payload)
        compare(memory, "load", ARENA, ARENA_BYTES, SOURCE, len(payload))
        compare(memory, "install", SOURCE, len(payload), 0)
    for layers in (16, 64, 65):
        payload = fixture(channels=1, kernel=1, head=1, layers=layers)
        compare(baseline(payload), "load", ARENA, ARENA_BYTES, SOURCE, len(payload))
    for configuration in (0, 1, 2, 3, 12, 0xFFFFFFFF):
        payload = fixture(layers=3)
        compare(baseline(payload, configuration), "install", SOURCE, len(payload), 0)
    print("Native shapes, capability failures, configuration and real recovery passed.", flush=True)

    size = compare(baseline(blob), "size", SOURCE, len(blob))["result"] - 8
    for offset in range(8):
        for capacity in (0, 1, 7, size - 1, size, size + 7):
            compare(baseline(blob), "load_context", ARENA + offset, capacity, SOURCE, len(blob))
    compare(baseline(blob), "load", 0, ARENA_BYTES, SOURCE, len(blob))
    malformed = [blob[:length] for length in (0, 1, 3, 4, 43, 44, len(blob) - 1)]
    bad = bytearray(blob); bad[-1] ^= 1
    malformed.append(bytes(bad))
    for offset, value in ((0, ord("X")), (4, 2), (6, 8), (7, 8), (12, 0), (14, 0), (14, 17), (15, 0)):
        body = bytearray(blob[:-4]); body[offset] = value
        malformed.append(crc_blob(body))
    malformed.extend(crc_blob(blob[:length]) for length in (40, 46, 54, len(blob) - 8))
    malformed.append(crc_blob(blob[:-4] + b"tail"))
    for payload in malformed:
        memory = baseline()
        memory[18][:len(payload)] = payload
        for operation in ("size", "probe", "load", "install"):
            arguments = {"size": (SOURCE, len(payload)), "probe": (SOURCE, len(payload)),
                "load": (ARENA, ARENA_BYTES, SOURCE, len(payload)), "install": (SOURCE, len(payload), 0)}[operation]
            compare(memory, operation, *arguments)
    # No source bytes are read on the original short-input branch.
    for length in (0, 1, 43):
        compare(baseline(), "probe", 0, length)
    print("Aligned and insufficient arenas, malformed input, partial writes and fallback passed.", flush=True)

    for source in (SOURCE, CACHED):
        for old_arena, capacity in ((0, 0), (ARENA, 0), (ARENA, size + 24), (ARENA, ARENA_BYTES)):
            memory = baseline(blob)
            put(memory[1], 436, old_arena); put(memory[1], 440, capacity)
            compare(memory, "install", source, len(blob), 0)
    compare(baseline(blob), "install", SOURCE, len(blob), 0, plan={ALLOCATE: (0, ())})
    memory = baseline(blob); put(memory[1], 440, 0)
    compare(memory, "install", SOURCE, len(blob), 0, plan={(ALLOCATE, 1): (0, ())})
    for compact_result, writes in ((-17, ()), (0, ()), (0, ((STATE + 416, 0, 4),))):
        memory = baseline(blob); put(memory[1], 416, 1)
        compare(memory, "install", SOURCE, len(blob), 0, plan={COMPACT: (compact_result, writes)})
    for mode, priority, restored in ((0, 20, 0), (2, 26, -7), (2, 27, 0), (2, 0xFFFFFFFF, -7)):
        memory = baseline(blob); put(memory[1], 280, mode)
        compare(memory, "install", SOURCE, len(blob), 0,
                plan={PRIORITY_GET: (priority, ()), (MODE, 1): (restored, ())})
    # Configuration changes after query can make the original load capacity stale.
    payload = fixture(layers=3)
    memory = baseline(payload); put(memory[1], 440, 0)
    compare(memory, "install", SOURCE, len(payload), 0, plan={(FREE, 0): (0, ((CONFIG, 0, 4),))})
    memory = baseline(blob); put(memory[0], 64, 0)
    compare(memory, "cleanup")
    memory = baseline(blob); memory[19][0] ^= 1
    compare(memory, "cleanup")
    print("Allocation, busy-state handling, mode restoration and boundary mutations passed.", flush=True)

    for slot in (0, 2, 7, 8, 14, 15, 0x80000000, 0xFFFFFFFF):
        compare(baseline(blob), "slot", slot, reads=slot_reads(blob), plan={METADATA: (0x01006403, ())})
    for index in range(len(slot_reads(blob))):
        reads = slot_reads(blob)
        _, data, _ = reads[index]
        reads[index] = (1, data[:min(3, len(data))], ())
        # Identity-trailer and signature failures retain their native fallback;
        # initial/reloaded header and payload failures terminate the read path.
        if index == 0 or index >= len(reads) - 2:
            reads = reads[:index + 1]
        compare(baseline(blob), "slot", 2, reads=reads)
    # Compare carried state after successful install, real recovery and slot reuse.
    carried = compare(baseline(blob), "slot", 2, reads=slot_reads(blob))["memory"]
    carried = tuple(bytearray(data) if i != 2 else data for i, data in enumerate(carried))
    compare(carried, "slot", 2, reads=slot_reads(blob, reuse=True))
    compare(carried, "cleanup")

    embedded = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
    for configuration in (12, 0xFFFFFFFF):
        for operation in ("size", "probe", "load_context", "load", "install", "slot"):
            memory = baseline(embedded, configuration)
            args = {"size": (EMBEDDED, len(embedded)), "probe": (EMBEDDED, len(embedded)),
                "load_context": (ARENA, ARENA_BYTES, EMBEDDED, len(embedded)),
                "load": (ARENA, ARENA_BYTES, EMBEDDED, len(embedded)),
                "install": (EMBEDDED, len(embedded), 0), "slot": (2,)}[operation]
            compare(memory, operation, *args, reads=slot_reads(embedded) if operation == "slot" else ())
    print("Stored records, carried state and the pinned embedded capture passed.", flush=True)

    invalid, guards = 0, 0
    state = CState(baseline())
    io = ContainerIO()
    out = U32()
    arguments = {"size": (SOURCE, len(blob), ctypes.byref(out)), "probe": (SOURCE, len(blob), ctypes.byref(out)),
        "load_context": (ARENA, ARENA_BYTES, SOURCE, len(blob)), "load": (ARENA, ARENA_BYTES, SOURCE, len(blob)),
        "cleanup": (), "install": (SOURCE, len(blob), 0, state.request), "slot": (2,)}
    for operation, args in arguments.items():
        for runtime, iop in ((None, ctypes.byref(io)), (ctypes.byref(state.native), None),
                              (ctypes.byref(state.native), ctypes.byref(io))):
            before = state.snapshot()
            assert functions[operation](runtime, *args, iop) == -200 and state.snapshot() == before
            invalid += 1
    for operation in ("size", "probe", "load", "install", "cleanup", "slot"):
        args = {"size": (SOURCE, len(blob)), "probe": (SOURCE, len(blob)),
            "load": (ARENA, ARENA_BYTES, SOURCE, len(blob)), "install": (SOURCE, len(blob), 0),
            "cleanup": (), "slot": (2,)}[operation]
        actual = c_run(functions, baseline(), operation, args,
            reads=slot_reads(blob) if operation == "slot" else (), blocked=lambda address, n, w: n == len(blob) and not w)
        assert actual["api_status"] == -201
        if operation in ("install", "slot"):
            assert actual["memory"][0][60:68] == baseline()[0][60:68]
            assert actual["memory"][1][676:680] == baseline()[1][676:680]
        guards += 1
    for operation in ("load_context", "load", "install", "cleanup", "slot"):
        args = {"load_context": (ARENA, ARENA_BYTES, SOURCE, len(blob)),
            "load": (ARENA, ARENA_BYTES, SOURCE, len(blob)), "install": (SOURCE, len(blob), 0),
            "cleanup": (), "slot": (2,)}[operation]
        actual = c_run(functions, baseline(), operation, args,
            reads=slot_reads(blob) if operation == "slot" else (), blocked=lambda address, n, w: address == ARENA and n == 80)
        assert actual["api_status"] == -201
        guards += 1

    inherited = [json.loads((ROOT / f"build/reverse-capture-{name}/verification.json").read_text())
                 for name in ("reset-03", "parser-03")]
    sources = set().union(*(r["source_sha256"] for r in inherited))
    sources.update(("firmware/src/hyperrig_capture_native.c", "firmware/include/hyperrig/hyperrig_capture_native.h",
        "tools/capture_native_machine.py", "tools/verify_capture_native.py", "tools/build_capture_native.py",
        "tests/test_capture_native_machine.py", "tests/capture_native_sanitize.c"))
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        assert sha == "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
        app = unpack_app(raw)[2]["app.bin"]
        for name, (start, end) in REGIONS.items():
            assert app[image_offset(start):image_offset(end)] == program.native_regions[name]
        assert struct.unpack_from("<I", app, image_offset(CONFIG))[0] == 12
        assert app[image_offset(EMBEDDED):image_offset(EMBEDDED) + len(embedded)] == embedded
        mini_binding = {"image_sha256": sha, "all_joined_regions_byte_identical": True,
                        "reset_configuration": 12, "embedded_capture_byte_identical": True}
    joined = {pc for pc in program.code if any(start <= pc < end for start, end in REGIONS.values())}
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "original_image_sha256": inherited[0]["original_image_sha256"],
        "scope": "real native parser/reset through capture size/load/cleanup/container/slot paths",
        "newly_reconstructed_original_functions": 0,
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.native_regions[name]).hexdigest(), "rts_only": name.startswith("noop_"),
            "decoded": sum(start <= pc < end for pc in program.code),
            "visited": sum(start <= pc < end for pc in coverage)} for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()),
        "parser_entries": parser_entries, "reset_entries": reset_entries, "reset_words": reset_words,
        "native_steps": steps, "result_digest": digest.hexdigest(), "invalid_api_checks": invalid, "mapping_guard_checks": guards,
        "instruction_coverage": {"new_decoded": 0, "new_visited": 0, "unvisited_new": [],
            "all_decoded": len(program.code), "all_visited": len(coverage),
            "joined_decoded": len(joined), "joined_visited": len(joined & coverage), "unvisited_joined": sorted(joined - coverage)},
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(sources)},
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(), "mini_v4_binding": mini_binding,
        "compared": ["results", "all 29 mapped regions and untouched arena bytes", "ordered service arguments and snapshots", "physical-read request order"],
        "limitations": ["new adapters join existing bodies; no new original function entries",
            "sources and parser configuration immutable during each parse; mapping pure and all mapped objects disjoint",
            "131072 mapped arena bytes and 8192 bytes per source/storage buffer",
            "allocator, metadata lookup, physical storage, scheduling, mode and priority services remain explicit boundaries",
            "no capture sample processing, target execution, hardware/audio or power-loss validation"],
        "hardware_test": False, "audio_test": False, "firmware_changed": False}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "total_comparisons", "parser_entries", "reset_entries", "reset_words", "native_steps", "invalid_api_checks", "mapping_guard_checks")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    verify(args.library, args.output, args.mini_image)
