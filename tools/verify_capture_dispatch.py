"""Compare reconstructed capture DSP dispatch against the pinned original instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from capture_dispatch_machine import (CaptureDispatchProgram, REGIONS, ROOT, EXTRA, ARITIES,
    PARSER, RESET, DEFAULT_DOT, DSP, STATS, FORCE, CONTEXT, OUTPUT, LAYERS, ARENA, image_offset)
from capture_container_machine import (SOURCE, CACHED, EMBEDDED, HEAP, CAPACITY, ALLOCATE, FREE,
    COMPACT, PRIORITY_GET, METADATA, LOADER, KIND)
from control_machine import STATE, GLOBAL
from preset_storage_machine import READ
from verify_capture_container import (CState as ContainerState, CMemory as ContainerMemory,
    Runtime as ContainerRuntime, IO as ContainerIO, SERVICE, MAPPING, U32, BYTE_POINTER,
    READ_CALLBACK, METADATA_CALLBACK, Reads, baseline as container_baseline, slot_reads, request, record_reads)

PARSER_CALLBACK = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, BYTE_POINTER, ctypes.POINTER(U32), U32, U32)


class Runtime(ctypes.Structure):
    _fields_ = [("container", ContainerRuntime), ("diagnostics", ctypes.c_uint8 * 16),
                ("dsp", ctypes.c_uint8 * 304), ("statistics", ctypes.c_uint8 * 72), ("force", ctypes.c_uint8 * 4)]


class IO(ctypes.Structure):
    _fields_ = [("platform", ContainerIO), ("parse", PARSER_CALLBACK)]


def baseline():
    memory = container_baseline()
    struct.pack_into("<II", memory[1], 436, ARENA, 512)
    dsp = bytearray([0xA5] * 304)
    dsp[77], dsp[78], dsp[240] = 32, 3, 1
    struct.pack_into("<H", dsp, 84, 3)
    struct.pack_into("<I", dsp, 168, LAYERS)
    records = bytearray([0xC6] * 5120)
    for i in range(64):
        records[80 * i] = i % 16
    return memory + (bytearray([0xA1] * 16), dsp, bytearray([0xB2] * 72),
                     bytearray([0xC3] * 4), bytearray([0xD4] * 25), records)


class CState(ContainerState):
    def __init__(self, memory):
        super().__init__(memory[:21])
        self.dispatch = Runtime(self.container, *[(ctypes.c_uint8 * len(data)).from_buffer_copy(data) for data in memory[21:25]])
        self.container = self.dispatch.container
        self.storage = self.container.storage
        self.output = (ctypes.c_uint8 * 17).from_buffer_copy(memory[25][:17])
        self.layer_count = U32.from_buffer_copy(memory[25][17:21])
        self.channel_count = U32.from_buffer_copy(memory[25][21:25])
        self.records = (ctypes.c_uint8 * 5120).from_buffer_copy(memory[26])

    def snapshot(self):
        return super().snapshot() + (bytes(self.dispatch.diagnostics), bytes(self.dispatch.dsp), bytes(self.dispatch.statistics),
            bytes(self.dispatch.force), bytes(self.output) + bytes(self.layer_count) + bytes(self.channel_count), bytes(self.records))

    def mapping(self, address, count, writable):
        if LAYERS <= address <= address + count <= LAYERS + 5120:
            return ctypes.addressof(self.records) + address - LAYERS
        return super().mapping(address, count, writable)


class CMemory(ContainerMemory):
    def __init__(self, state):
        super().__init__(state)
        arrays = (state.dispatch.diagnostics, state.dispatch.dsp, state.dispatch.statistics, state.dispatch.force)
        for (base, _), array in zip(EXTRA, arrays):
            self.extra.update({base + i: (array, i) for i in range(len(array))})
        for base, array in ((OUTPUT, state.output), (OUTPUT + 17, (ctypes.c_uint8 * 4).from_buffer(state.layer_count)),
                            (OUTPUT + 21, (ctypes.c_uint8 * 4).from_buffer(state.channel_count)), (LAYERS, state.records)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


class Script:
    def __init__(self, plan=None, *, heap_first=False):
        self.plan, self.counts, self.heap_first = plan or {}, {}, heap_first

    def __call__(self, service, args, view):
        index = self.counts.get(service, 0)
        self.counts[service] = index + 1
        default = {ALLOCATE: HEAP if self.heap_first and index == 0 else ARENA, PRIORITY_GET: 20}.get(service, 0)
        value, writes = self.plan.get((service, index), self.plan.get(service, (default, ())))
        for address, word, size in writes:
            view.write(address, word, size)
        return value & 0xFFFFFFFF


class ParserScript:
    def __init__(self, plan=None):
        self.plan, self.index = plan or {}, 0

    def __call__(self, args, ledger, view):
        code, changes, writes = self.plan.get(self.index, (0, (None, 64, None), ()))
        self.index += 1
        for i, value in enumerate(changes):
            if value is not None:
                ledger[i] = value & 0xFFFFFFFF
        for address, word, size in writes:
            view.write(address, word, size)
        return code & 0xFFFFFFFF


def configure(library):
    rt, io, out = ctypes.POINTER(Runtime), ctypes.POINTER(IO), ctypes.POINTER(U32)
    signatures = {"prepare": [rt, U32, io], "cleanup": [rt, io], "size": [U32, U32, out, io],
        "probe": [rt, U32, U32, out, io], "load": [rt, U32, U32, U32, U32, io],
        "load_context": [rt, U32, U32, U32, U32, io], "select_dot": [rt, U32],
        "capabilities": [rt, BYTE_POINTER, out, out, io], "install": [rt, U32, U32, U32, BYTE_POINTER, io], "slot": [rt, U32, io]}
    result = {}
    for name, signature in signatures.items():
        fn = getattr(library, "hyperrig_capture_dispatch_" + name)
        fn.argtypes, fn.restype = signature, ctypes.c_int
        result[name] = fn
    return result


def heap_first(operation, arguments):
    return operation == "slot" or (operation == "install" and (arguments[2] or arguments[0] not in (CACHED, EMBEDDED)))


def c_run(functions, memory, operation, arguments, reads=(), plan=None, parses=None, missing_map=False, missing_layers=False):
    state, calls, errors, flash = CState(memory), [], [], Reads(reads)
    script, parser = Script(plan, heap_first=heap_first(operation, arguments)), ParserScript(parses)
    def service(_opaque, svc, a, b, c, d):
        try:
            args = a, b, c, d
            calls.append((svc, args, state.snapshot()))
            result = script(svc, args, CMemory(state))
            if svc == ALLOCATE and result == HEAP:
                state.allocation_size = a
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
    def metadata(_opaque, slot, header, identity):
        try:
            args = slot, ctypes.string_at(header, 40), identity, 0
            calls.append((METADATA, args, state.snapshot()))
            return script(METADATA, args, CMemory(state))
        except Exception as error:
            errors.append(error)
            return 1
    def parse(_opaque, context, ledger, source, length):
        try:
            address = ctypes.cast(context, ctypes.c_void_p).value
            label = CONTEXT if address == ctypes.addressof(state.dispatch.dsp) + 76 else "query"
            args = label, tuple(ledger[i] for i in range(3)), source, length
            calls.append((PARSER, args, state.snapshot()))
            return parser(args, ledger, CMemory(state))
        except Exception as error:
            errors.append(error)
            return 1
    def mapping(_opaque, address, count, writable):
        if missing_map or (missing_layers and LAYERS <= address < LAYERS + 5120):
            return None
        return state.mapping(address, count, writable)
    callbacks = SERVICE(service), READ_CALLBACK(read), MAPPING(mapping), METADATA_CALLBACK(metadata)
    io = IO(ContainerIO(*callbacks, None), PARSER_CALLBACK(parse))
    rt, iop, out = ctypes.byref(state.dispatch), ctypes.byref(io), U32(0xDEADBEEF)
    if operation in ("size", "probe"):
        values = ([rt] if operation == "probe" else []) + list(arguments) + [ctypes.byref(out), iop]
        assert functions[operation](*values) == 0
        result = out.value
    elif operation == "select_dot":
        assert functions[operation](rt, *arguments) == 0
        result = 0
    elif operation == "capabilities":
        result = functions[operation](rt, state.output, ctypes.byref(state.layer_count), ctypes.byref(state.channel_count), iop)
    elif operation == "install":
        result = functions[operation](rt, *arguments, state.request, iop)
    else:
        result = functions[operation](rt, *arguments, iop)
    if errors:
        raise errors[0]
    return {"result": result & 0xFFFFFFFF, "memory": state.snapshot(), "calls": calls, "reads": flash.requests}


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = CaptureDispatchProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, services = dict.fromkeys(functions, 0), set(), set()
    rng = random.Random(0x4A7A1296C)
    mutations = 0
    def compare(memory, operation, *arguments, reads=(), plan=None, parses=None):
        nonlocal mutations
        flash = Reads(reads)
        original = program.execute(memory, operation, *arguments, reader=flash.read,
            boundary=Script(plan, heap_first=heap_first(operation, arguments)), parser=ParserScript(parses))
        if operation == "select_dot":
            original["result"] = 0  # Original returns no semantic value.
        actual = c_run(functions, memory, operation, arguments, reads, plan, parses)
        if any(original[key] != actual[key] for key in ("result", "memory", "calls")) or actual["reads"] != flash.requests:
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
        mutations += bool(plan or parses)
        return original

    for busy in (0, 1, 0xFFFFFFFF):
        for arena in (0, ARENA):
            for capacity in (0, 1, 512, 0xFFFFFFFF):
                for requested in (0, 1, 511, 512, 513, 0xFFFFFF00, 0xFFFFFFFF):
                    memory = baseline()
                    struct.pack_into("<I", memory[1], 416, busy)
                    struct.pack_into("<II", memory[1], 436, arena, capacity)
                    for allocation in (0, ARENA, 0x87654321):
                        compare(memory, "prepare", requested, plan={ALLOCATE: (allocation, ())})
    for code in (0, 1, -1, -5, 0x80000000):
        for used in (0, 1, 64, 0xFFFFFFE8, 0xFFFFFFF8, 0xFFFFFFFF):
            for op in ("size", "probe"):
                compare(baseline(), op, SOURCE, 128, parses={0: (code, (ARENA, used, 0x1234), ())})
    print("Preparation, parser size query, status and unsigned wrap comparisons passed.", flush=True)

    for arena in (0, 0xFFFFFFF9, *range(ARENA, ARENA + 8)):
        for size in (0, 1, 6, 7, 8, 63, 64, 65, 512, 0xFFFFFFFF):
            for used in (0, 64, 0xFFFFFFFF):
                for op in ("load_context", "load"):
                    compare(baseline(), op, arena, size, SOURCE, 128,
                            parses={0: (0, (None, used, None), ())})
    for status in (0, 1, -1, -4, 0x80000000, 0xFFFFFFFF):
        for op in ("load_context", "load", "cleanup"):
            args = (ARENA, 128, SOURCE, 8) if op != "cleanup" else ()
            compare(baseline(), op, *args, parses={0: (status, (None, 64, None), ((CONTEXT + 32, 0xBAADF00D, 4),)),
                                                  1: (status, (None, 64, None), ())})
    for callback in (0, DEFAULT_DOT, 1, 0xFFFFFFFF):
        compare(baseline(), "select_dot", callback)
    for count in (0, 1, 2, 16, 64):
        for channels in (0, 1, 3, 255):
            for flag in (0, 1, 255):
                for kind in (0, 31, 32, 33, 255):
                    memory = baseline()
                    struct.pack_into("<H", memory[22], 84, count)
                    memory[22][78], memory[22][240], memory[22][77] = channels, flag, kind
                    compare(memory, "capabilities")
    for count in (1, 3, 64):
        for index in range(count):
            for bad in (15, 16, 255):
                memory = baseline()
                struct.pack_into("<H", memory[22], 84, count)
                memory[26][index * 80] = bad
                compare(memory, "capabilities")
    print("Arena alignment, load status, capability gates and descriptor scans passed.", flush=True)

    for _ in range(96):
        memory = baseline()
        memory[22][:] = rng.randbytes(304)
        compare(memory, "load", ARENA + rng.randrange(8), 512, SOURCE, rng.randrange(8193))
    for index in (0, 1):
        writes = ((CONTEXT + 108, 0x12345678, 4), (CONTEXT + 8, 17, 2), (CONTEXT + 10, 0x80, 1),
                  (CONTEXT + 13, 0xFF, 1), (CONTEXT + 32, 42, 4), (DSP + 64, 999, 4), (STATS + 68, 777, 4))
        compare(baseline(), "load", ARENA, 512, SOURCE, 128, plan={(RESET, index): (0xFFFFFFFF, writes)})
    for service in (FREE, ALLOCATE):
        memory = baseline()
        struct.pack_into("<II", memory[1], 436, 0, 0)
        compare(memory, "prepare", 100, plan={service: (ARENA if service == ALLOCATE else 0,
            ((STATE + 436, 7, 4), (STATE + 440, 9, 4), (STATE + 500, 99, 1)))})
    for length in (0, 8, 321):
        for changed in (0, 8, 321):
            memory = baseline()
            struct.pack_into("<I", memory[0], 64, length)
            compare(memory, "cleanup", parses={0: (0, (None, 64, None), ((GLOBAL + 64, changed, 4), (GLOBAL + 60, SOURCE, 4)))})
    for busy in (0, 1):
        memory = baseline()
        struct.pack_into("<I", memory[1], 416, busy)
        compare(memory, "cleanup")
    compare(baseline(), "cleanup", parses={1: (-17, (None, 64, None), ())})
    print("Statistics, repeated reset ordering and synchronous state mutation comparisons passed.", flush=True)

    for source in (SOURCE, CACHED, EMBEDDED):
        for length in (1, 3, 4, 8, 63, 64, 6144, 7808, 8192):
            compare(baseline(), "install", source, length, 0)
    for slot in (0, 2, 7, 8, 14):
        compare(baseline(), "slot", slot, reads=slot_reads())
    memory = baseline()
    memory[16][:] = request()
    compare(memory, "install", 0, 8, LOADER, reads=record_reads())
    for index in range(4):
        for code in (-2, -5):
            compare(baseline(), "install", SOURCE, 8, 0, parses={index: (code, (None, 64, None), ())})
    compare(baseline(), "install", SOURCE, 8, 0, parses={0: (0, (None, 0xFFFFFFE8, None), ())})
    memory = baseline()
    memory[22][78] = 1
    compare(memory, "install", SOURCE, 8, 0)
    for busy in (0, 1):
        memory = baseline()
        struct.pack_into("<I", memory[1], 416, busy)
        struct.pack_into("<II", memory[1], 436, 0, 0)
        compare(memory, "install", SOURCE, 8, 0, plan={COMPACT: (0, ((STATE + 416, 0, 4),))})
    print("Container/slot integration with real DSP dispatch comparisons passed.", flush=True)

    state, seen = CState(baseline()), []
    callbacks = SERVICE(lambda *args: seen.append(args) or 0), READ_CALLBACK(lambda *args: seen.append(args) or 1), MAPPING(lambda *args: seen.append(args) or None), METADATA_CALLBACK(lambda *args: seen.append(args) or 0)
    parser = PARSER_CALLBACK(lambda *args: seen.append(args) or 1)
    io = IO(ContainerIO(*callbacks, None), parser)
    rt, iop, out = ctypes.byref(state.dispatch), ctypes.byref(io), U32()
    good = {"prepare": (rt, 8, iop), "cleanup": (rt, iop), "size": (SOURCE, 8, ctypes.byref(out), iop),
        "probe": (rt, SOURCE, 8, ctypes.byref(out), iop), "load": (rt, ARENA, 64, SOURCE, 8, iop),
        "load_context": (rt, ARENA, 64, SOURCE, 8, iop), "select_dot": (rt, 0),
        "capabilities": (rt, state.output, ctypes.byref(state.layer_count), ctypes.byref(state.channel_count), iop),
        "install": (rt, SOURCE, 8, 0, state.request, iop), "slot": (rt, 0, iop)}
    invalid = []
    for op, args in good.items():
        if op != "size":
            invalid.append((op, (None, *args[1:])))
        if op != "select_dot":
            invalid.append((op, (*args[:-1], None)))
    invalid.extend([("size", (SOURCE, 8, None, iop)), ("probe", (rt, SOURCE, 8, None, iop)),
        ("capabilities", (rt, None, ctypes.byref(out), ctypes.byref(out), iop)),
        ("capabilities", (rt, state.output, None, ctypes.byref(out), iop)),
        ("capabilities", (rt, state.output, ctypes.byref(out), None, iop))])
    bad_ios = [IO(ContainerIO(*callbacks, None), PARSER_CALLBACK())]
    for index, cls in enumerate((SERVICE, READ_CALLBACK, MAPPING)):
        broken = list(callbacks)
        broken[index] = cls()
        bad_ios.append(IO(ContainerIO(*broken, None), parser))
    for bad in bad_ios:
        for op in ("prepare", "size", "load", "capabilities", "install", "slot"):
            invalid.append((op, (*good[op][:-1], ctypes.byref(bad))))
    for op, args in invalid:
        before = state.snapshot()
        assert functions[op](*args) == -200
        assert state.snapshot() == before and not seen
    guarded = c_run(functions, baseline(), "capabilities", (), missing_map=True)
    assert guarded["result"] == (-201) & 0xFFFFFFFF
    assert guarded["memory"][25][:17] == baseline()[22][90:107]
    guards = 1
    for operation, args, reads in (("install", (SOURCE, 8, 0), ()), ("slot", (2,), slot_reads())):
        before = baseline()
        guarded = c_run(functions, before, operation, args, reads, missing_layers=True)
        assert guarded["result"] == (-201) & 0xFFFFFFFF
        assert guarded["memory"][0][60:68] == before[0][60:68]
        assert guarded["memory"][1][676:680] == before[1][676:680]
        assert any(row[0] == FREE and row[1][0] == HEAP for row in guarded["calls"])
        if operation == "slot":
            assert guarded["memory"][0][9] == before[0][9]
            assert guarded["memory"][1][696:708] == before[1][696:708]
        guards += 1
    new_code = set(program.code) - program.pre_dispatch_code
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
            assert app[image_offset(start):image_offset(end)] == program.dispatch_regions[name]
        mini_binding = {"image_sha256": digest, "all_dispatch_regions_byte_identical": True}
    machines = ("dot", "control", "control_action", "selection", "preset_storage", "preset_preflight", "preset_assets", "capture_loader", "capture_container")
    sources = {f"tools/{name}_machine.py" for name in machines}
    for name in ("controls", "control_actions", "selection", "preset_storage", "preset_preflight", "preset_assets", "capture_loader", "capture_container"):
        sources.update((f"tools/verify_{name}.py", f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"))
    sources.update([f"tools/{name}.py" for name in ("capture_dispatch_machine", "verify_capture_dispatch", "build_capture_dispatch")])
    sources.update(("tests/test_capture_dispatch_machine.py", "firmware/src/hyperrig_capture_dispatch.c", "firmware/include/hyperrig/hyperrig_capture_dispatch.h"))
    sources.update(("upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"))
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "capture preparation, size/probe, DSP load wrappers, capability query, cleanup and container/slot integration",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end,
            "bytes_sha256": hashlib.sha256(program.dispatch_regions[name]).hexdigest(), "rts_only": name.startswith("noop_")}
            for name, (start, end) in REGIONS.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "scripted_cases": mutations,
        "invalid_api_checks": len(invalid), "new_mapping_guard_checks": guards,
        "instruction_coverage": {"new_visited": len(new_code & coverage), "new_decoded": len(new_code),
            "all_visited": len(coverage), "all_decoded": len(program.code), "unvisited_new": missing},
        "external_services_visited": sorted(services),
        "compared": ["semantic results", "all 27 mapped memory regions", "ordered service/parser arguments and complete mapped state at each boundary", "synthetic read requests"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(sources)},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["whole raw parser 0x02031c64 and memory reset 0x01c12878 remain synthetic services",
            "allocator, compaction, metadata lookup, scheduler, physical reads and mode/priority remain external",
            "size query private context is write-only; parser/allocator contracts are not native implementations",
            "mapped descriptor verifier domain is at most 64 records of 80 bytes; C mapping failure is a new guard",
            "no complete capture execution, real-time, peripheral or target audio equivalence claim"]}
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
