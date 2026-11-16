"""Compare native loading and numerical processing with carried original state."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys

from capture_live_machine import CaptureLiveProgram, EXTRA, INPUT, OUTPUT, SAMPLE_BYTES, ROOT
from capture_native_machine import REGIONS as NATIVE_REGIONS, ARENA, ARENA_BYTES, CONFIG
from capture_dispatch_machine import DSP, STATS, FORCE, PARSER, RESET, CONTEXT, image_offset
from capture_processing_machine import REGIONS as PROCESSING_REGIONS, KERNELS, TABLE_START, TABLE_END, SCRATCH
from capture_warmup_machine import REGIONS as WARMUP_REGIONS
from capture_loader_machine import GAIN_TABLE, GAIN_BYTES
from preset_preflight_machine import CURVE
from control_action_machine import TABLE_START as ACTION_TABLE, TABLE_END as ACTION_TABLE_END
from capture_container_machine import SOURCE, CACHED, HEAP, EMBEDDED, ALLOCATE, METADATA, FREE
from preset_storage_machine import READ
from control_machine import STATE
from verify_capture_native import (CState as NativeState, CMemory as NativeMemory, Runtime,
    configure as configure_native, baseline as native_baseline, put, fixture, crc_blob,
    ContainerIO, SERVICE, READ_CALLBACK, MAPPING, METADATA_CALLBACK, U32, BYTE_POINTER,
    Reads, Script, heap_first, slot_reads)
from verify_capture_processing import IO as ProcessingIO, MAP, KERNEL

C_NAMES = ("controls", "control_actions", "selection", "preset_storage", "preset_assets",
    "capture_loader", "capture_container", "capture_dispatch", "capture_reset", "capture_parser",
    "capture_native", "dot", "head", "a2l", "rechannel", "capture_processing", "capture_warmup", "capture_live")
HEAD, SUM, HEAD_RING, HEAD_WEIGHTS = 0x01C33F40, SCRATCH, ARENA + 0x14000, ARENA + 0x18000


def head_fixture(ring=4, kernel=3, position=0, shift=15, bias=0, seed=1):
    memory = baseline(seed=seed)
    rng = random.Random(seed)
    p = HEAD - SCRATCH
    for offset, value in ((0, SUM), (4, HEAD_RING), (8, position * 12), (12, ring * 12),
        (16, 768), (20, kernel * 12 - 12), (24, HEAD_WEIGHTS), (28, OUTPUT), (32, 64),
        (36, kernel * 3), (40, (1 << (shift - 1)) - 1), (44, shift), (48, bias), (52, bias >> 32)):
        put(memory[29], p + offset, value)
    values = [rng.randrange(-2**31, 2**31) for _ in range(ring * 3)]
    values += values[:min(ring, 64) * 3]
    for i, value in enumerate(values):
        put(memory[27], HEAD_RING - ARENA + i * 4, value)
    for i in range(kernel * 3):
        put(memory[27], HEAD_WEIGHTS - ARENA + i * 2, rng.randrange(-32768, 32768), 2)
    for i in range(192):
        put(memory[29], i * 4, rng.randrange(-2**31, 2**31))
    return memory


def baseline(blob=None, configuration=12, seed=1):
    memory = native_baseline(blob, configuration)
    added = [bytearray([0x39] * n) for _, n in EXTRA]
    rng = random.Random(seed)
    for i in range(SAMPLE_BYTES // 4):
        put(added[3], i * 4, rng.randrange(0x100000000))
    return memory + tuple(added)


def mutable(memory):
    return tuple(value if i == 2 else bytearray(value) for i, value in enumerate(memory))


class CState(NativeState):
    def __init__(self, memory):
        super().__init__(memory[:29])
        self.live = [(ctypes.c_uint8 * len(data)).from_buffer_copy(data) for data in memory[29:]]

    def snapshot(self):
        return super().snapshot() + tuple(bytes(array) for array in self.live)

    def mapping(self, address, size, writable):
        for (base, _), array in zip(EXTRA, self.live):
            if base <= address <= address + size <= base + len(array):
                return ctypes.addressof(array) + address - base
        for base, array in ((DSP, self.dispatch.dsp), (STATS, self.dispatch.statistics),
                            (FORCE, self.dispatch.force), (CONFIG, self.native.configuration)):
            if base <= address <= address + size <= base + len(array):
                return ctypes.addressof(array) + address - base
        return super().mapping(address, size, writable)


class CMemory(NativeMemory):
    def __init__(self, state):
        super().__init__(state)
        for (base, _), array in zip(EXTRA, state.live):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


def configure(library):
    functions = configure_native(library)
    fn = library.hyperrig_capture_live_process
    fn.argtypes = [ctypes.POINTER(Runtime), U32, U32, U32, ctypes.POINTER(ProcessingIO)]
    fn.restype = ctypes.c_int
    functions["process"] = fn
    fn = library.hyperrig_capture_live_warmup
    fn.argtypes, fn.restype = [ctypes.POINTER(Runtime), U32, ctypes.POINTER(ProcessingIO)], ctypes.c_int
    functions["warmup"] = fn
    fn = library.hyperrig_capture_live_kernel
    fn.argtypes, fn.restype = [U32, U32, ctypes.POINTER(ProcessingIO)], ctypes.c_int
    functions["kernel"] = fn
    return functions


def c_run(functions, memory, operation, arguments=(), reads=(), plan=None, blocked=None, observe=True):
    state, calls, errors, flash = CState(memory), [], [], Reads(reads)
    script = Script(plan, heap_first=heap_first(operation, arguments))
    view = CMemory(state)
    def service(_opaque, svc, a, b, c, d):
        try:
            assert svc not in (PARSER, RESET), "native body escaped to a synthetic service"
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
    def kernel(_opaque, target, parameters):
        try:
            calls.append((target, parameters, state.snapshot()))
            return functions["kernel"](target, parameters, ctypes.byref(processing_io))
        except Exception as error:
            errors.append(error)
            return -202
    io = ContainerIO(SERVICE(service), READ_CALLBACK(read), MAPPING(mapping), METADATA_CALLBACK(metadata), None)
    processing_io = ProcessingIO(MAP(mapping), KERNEL(kernel) if observe else KERNEL(), None)
    rt, out = ctypes.byref(state.native), U32(0xDEADBEEF)
    if operation == "head_kernel":
        code = functions["kernel"](KERNELS["head3"][0], *arguments, ctypes.byref(processing_io))
        value = code
    elif operation in ("process", "warmup"):
        code = functions[operation](rt, *arguments, ctypes.byref(processing_io))
        value = code
    elif operation in ("size", "probe"):
        code = functions[operation](rt, *arguments, ctypes.byref(out), ctypes.byref(io))
        value = out.value
    elif operation == "install":
        code = functions[operation](rt, *arguments, state.request, ctypes.byref(io))
        value = code
    else:
        code = functions[operation](rt, *arguments, ctypes.byref(io))
        value = code
    if errors:
        raise errors[0]
    return {"result": value & 0xFFFFFFFF, "api_status": code, "memory": state.snapshot(),
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
    return original


def source_names():
    # Bind the actually imported repository modules, explicit build/test inputs,
    # ISA data and recursive C headers. No previous build report is required.
    names = set()
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.suffix == ".py":
                names.add(path.relative_to(ROOT).as_posix())
    names.update(("tools/build_capture_live.py", "tests/test_capture_live_machine.py",
        "tests/capture_live_sanitize.c", "research/input-manifest.json",
        "upstream/pi32v2-isa/isa/pi32v2.toml", "upstream/pi32v2-isa/docs/SOURCES.md"))
    pending = [ROOT / f"firmware/src/hyperrig_{name}.c" for name in C_NAMES]
    while pending:
        path = pending.pop()
        name = path.relative_to(ROOT).as_posix()
        if name in names:
            continue
        names.add(name)
        for include in re.findall(r'^#include "([^"]+)"', path.read_text(), re.M):
            target = path.parent / include
            pending.append(target if target.is_file() else ROOT / "firmware/include" / include)
    return sorted(names)


def verify(library_path, output, mini_image=None, smoke=False):
    if not __debug__:
        raise RuntimeError("verification requires assertions")
    program = CaptureLiveProgram()
    functions = configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, digest = {}, set(), hashlib.sha256()
    steps = numerical = parsers = resets = reset_words = null_callback = carried = 0
    def compare(memory, operation, *args, reads=(), plan=None):
        nonlocal steps, numerical, parsers, resets, reset_words
        result = compare_one(program, functions, memory, operation, args, reads, plan)
        counts[operation] = counts.get(operation, 0) + 1
        coverage.update(result["visited"])
        steps += result["steps"]
        numerical += len(result["calls"]) if operation in ("process", "warmup") else int(operation == "head_kernel")
        parsers += len(result["parser_entries"])
        resets += result["reset_entries"]
        reset_words += result["reset_words"]
        digest.update(json.dumps((operation, args, result["result"])).encode())
        for i, data in enumerate(result["memory"]):
            digest.update(bytes([data]) if i == 2 else data)
        return result
    def load(blob, operation="load", configuration=12, **kwargs):
        args = {"load": (ARENA, ARENA_BYTES, SOURCE, len(blob)),
                "install": (SOURCE, len(blob), 0), "slot": (2,)}[operation]
        result = compare(baseline(blob, configuration), operation, *args,
                         reads=slot_reads(blob) if operation == "slot" else (), **kwargs)
        assert result["result"] == 0, (operation, result["result"])
        assert result["memory"][22][76 + 164] == 1, "fixture not eligible for optimized processing"
        return result["memory"]
    blob = fixture()
    loaded = load(blob)
    compare(loaded, "process", INPUT, OUTPUT, 64)
    warmed = compare(loaded, "warmup", OUTPUT)
    assert warmed["result"] == 1
    compare(warmed["memory"], "process", INPUT, OUTPUT, 64)
    compare(head_fixture(), "head_kernel", HEAD)
    print("Native loader handoff and small-head numerical processing passed.", flush=True)
    if not smoke:
        for head in range(1, 65):
            data = fixture(head=head, seed=head)
            memory = load(data, "slot" if head % 3 == 0 else "install" if head % 3 == 1 else "load")
            result = compare(memory, "process", INPUT, OUTPUT, 128 + head % 64)
            assert struct.unpack_from("<I", result["memory"][22], 76 + 88)[0] == 128
            assert result["memory"][33][512:] == memory[33][512:]
            if head in (1, 2, 3, 7, 16, 31, 32, 33, 64):
                direct = c_run(functions, memory, "process", (INPUT, OUTPUT, 128 + head % 64), observe=False)
                assert direct["result"] == 0 and direct["memory"] == result["memory"] and not direct["calls"]
                null_callback += 1
        print("Every parser head size 1..64 reached actual processing; remainder and null-callback checks passed.", flush=True)
        for kernel in (1, 3, 6, 15):
            for layers in (1, 2, 4):
                for residual in (15, 16, 17):
                    data = fixture(kernel=kernel, layers=layers, residual=residual, seed=kernel + layers + residual)
                    memory = load(data, "install")
                    for count in (64, 65):
                        memory = compare(memory, "process", INPUT, OUTPUT, count)["memory"]
                        carried += 1
        for count in (0, 1, 63, 64, 65, 127, 128, 129, 192, 256, 1024):
            result = compare(loaded, "process", INPUT, OUTPUT, count)
            assert result["memory"][33][(count // 64) * 256:] == loaded[33][(count // 64) * 256:]
            bypass = baseline(); bypass[22][76:] = bytes(228)
            for destination in (OUTPUT, INPUT + 4, INPUT):
                if destination == INPUT + 4 and count == 1024:
                    continue
                compare(bypass, "process", INPUT, destination, count)
        for position in (1, 63, 64, 0xFFFFFFC0, 0xFFFFFFF0, 0xFFFFFFFF):
            memory = mutable(loaded); put(memory[22], 76 + 88, position)
            result = compare(memory, "process", INPUT, OUTPUT, 128)
            assert struct.unpack_from("<I", result["memory"][22], 76 + 88)[0] == (position + 128) & 0xFFFFFFFF
        print("Loaded kernel selection, carried histories, block boundaries, bypass and position wrap passed.", flush=True)
        for ring in (1, 2, 3, 4, 8, 16, 32, 63, 64, 65, 127):
            for kernel in sorted({1, min(ring, 3), min(ring, 65)}):
                for shift in (1, 15, 31):
                    for bias in (0, 2**63 - 1, -2**63):
                        compare(head_fixture(ring, kernel, ring - 1, shift, bias, seed=ring + shift), "head_kernel", HEAD)
        for offset in range(8):
            result = compare(baseline(blob), "load", ARENA + offset, ARENA_BYTES - offset, SOURCE, len(blob))
            assert result["result"] == 0
            compare(result["memory"], "process", INPUT, OUTPUT, 64)
        for configuration in (0, 1, 2, 3, 12, 0xFFFFFFFF):
            memory = load(fixture(layers=3), "install", configuration)
            compare(memory, "process", INPUT, OUTPUT, 128)
        print("Small and large head rings, rounding/bias limits, alignment and parser configuration passed.", flush=True)
        memory = load(blob, "slot")
        memory = compare(memory, "process", INPUT, OUTPUT, 128)["memory"]
        reused = compare(memory, "slot", 2, reads=slot_reads(blob, reuse=True))
        assert reused["memory"][22] == memory[22] and reused["memory"][27] == memory[27]
        compare(reused["memory"], "process", INPUT, OUTPUT, 64); carried += 3
        recovered = compare(memory, "cleanup")
        after = compare(recovered["memory"], "process", INPUT, OUTPUT, 64)
        initial = compare(load(blob, "slot"), "process", INPUT, OUTPUT, 64)
        assert after["memory"][33][:256] == initial["memory"][33][:256]
        carried += 2
        bad = mutable(memory); bad[18][len(blob) - 1] ^= 1
        failed = compare(bad, "load", ARENA, ARENA_BYTES, SOURCE, len(blob))
        assert failed["result"] == 0xFFFFFFFD and failed["memory"][22] == memory[22]
        compare(failed["memory"], "process", INPUT, OUTPUT, 64); carried += 2
        # Failed installation must execute real recovery before processing resumes.
        for candidate in (fixture(channels=1), fixture()[:-1], b"invalid"):
            # Keep the old owned source in CACHED. This corpus has one candidate
            # heap; allocating it over a still-live old HEAP would violate the
            # allocator contract and destroy the source needed for recovery.
            installed = compare(baseline(blob), "install", CACHED, len(blob), 0)
            assert installed["result"] == 0
            data = mutable(installed["memory"])
            data = mutable(compare(data, "process", INPUT, OUTPUT, 64)["memory"])
            data[18][:len(candidate)] = candidate
            failed = compare(data, "install", SOURCE, len(candidate), 0)
            assert failed["result"] != 0 and failed["memory"][1][500] == 1
            compare(failed["memory"], "process", INPUT, OUTPUT, 64); carried += 2
        embedded = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
        for operation in ("load", "install", "slot"):
            memory = load(embedded, operation)
            warmed = compare(memory, "warmup", OUTPUT)
            assert warmed["result"] == 1
            memory = warmed["memory"]
            for count in (64, 128):
                memory = compare(memory, "process", INPUT, OUTPUT, count)["memory"]
                carried += 1
        print("Storage reuse, parser failure, real recovery and embedded capture processing passed.", flush=True)
        for layers in (1, 2, 4, 8):
            for head in (1, 3, 16, 64):
                data = fixture(layers=layers, head=head, kernel=3, bias=0, seed=layers + head)
                memory = load(data, "slot")
                first = compare(memory, "warmup", OUTPUT)
                assert first["result"] == 1
                assert first["memory"][33][:12] == first["memory"][29][0x4e0:0x4ec]
                active = compare(first["memory"], "process", INPUT, OUTPUT, 128)
                repeated = compare(active["memory"], "warmup", 0)
                assert repeated["result"] == 1
                resumed = compare(repeated["memory"], "process", INPUT, OUTPUT, 128)
                assert resumed["memory"][33][:512] == active["memory"][33][:512]
                assert resumed["memory"][22] == active["memory"][22]
                assert resumed["memory"][27] == active["memory"][27]
                carried += 4
        fallback = mutable(loaded); fallback[22][76 + 164] = 0
        fallback = compare(fallback, "warmup", OUTPUT)
        assert fallback["result"] == 0 and fallback["reset_entries"] == 1
        compare(fallback["memory"], "process", INPUT, OUTPUT, 64)
        print("Real warm-up, repeat warm-up, reset fallback and carried processing passed.", flush=True)

    invalid = guards = domain_guards = 0
    state = CState(loaded)
    callback = MAP(lambda _o, address, size, writable: state.mapping(address, size, writable))
    io = ProcessingIO(callback, KERNEL(), None)
    for runtime, iop in ((None, ctypes.byref(io)), (ctypes.byref(state.native), None),
                        (ctypes.byref(state.native), ctypes.byref(ProcessingIO()))):
        before = state.snapshot()
        assert functions["process"](runtime, INPUT, OUTPUT, 64, iop) == -200 and state.snapshot() == before
        invalid += 1
        assert functions["warmup"](runtime, OUTPUT, iop) == -200 and state.snapshot() == before
        invalid += 1
    for address in (INPUT, OUTPUT, SCRATCH, HEAD, ARENA):
        actual = c_run(functions, loaded, "process", (INPUT, OUTPUT, 64),
                       blocked=lambda a, n, w, target=address: a <= target < a + n)
        assert actual["api_status"] == -201
        guards += 1
    for offset, value in ((12, 0), (12, 0x80000004), (8, 48), (36, 0), (36, 198),
                          (44, 0), (44, 32), (32, 63), (16, 767), (20, 0), (40, 0)):
        memory = head_fixture(); put(memory[29], HEAD - SCRATCH + offset, value)
        actual = c_run(functions, memory, "head_kernel", (HEAD,))
        assert actual["api_status"] == -202
        assert actual["memory"] == tuple(value if i == 2 else bytes(value) for i, value in enumerate(memory))
        domain_guards += 1
    regions = {**NATIVE_REGIONS, **PROCESSING_REGIONS, **KERNELS, **WARMUP_REGIONS}
    joined = {pc for pc in program.code if any(lo <= pc < hi for lo, hi in regions.values())}
    app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        mini = mini_image.resolve().read_bytes()
        assert hashlib.sha256(mini).hexdigest() == "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
        decoded = unpack_app(mini)[2]["app.bin"]
        for name, (lo, hi) in regions.items():
            assert decoded[image_offset(lo):image_offset(hi)] == app[image_offset(lo):image_offset(hi)], name
        # Bind all loaded transitive code, including inherited storage/assets,
        # rather than limiting this local check to the joined-region table.
        for pc, (_, size, _, _) in program.code.items():
            assert decoded[image_offset(pc):image_offset(pc) + size] == app[image_offset(pc):image_offset(pc) + size]
        data_ranges = ((GAIN_TABLE, GAIN_BYTES), (CURVE, 11), (ACTION_TABLE, ACTION_TABLE_END - ACTION_TABLE),
                       (TABLE_START, TABLE_END - TABLE_START), (CONFIG, 4))
        for start, size in data_ranges:
            assert decoded[image_offset(start):image_offset(start) + size] == app[image_offset(start):image_offset(start) + size]
        assert decoded[image_offset(CONFIG):image_offset(CONFIG) + 4] == struct.pack("<I", 12)
        embedded = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
        assert decoded[image_offset(EMBEDDED):image_offset(EMBEDDED) + len(embedded)] == embedded
        mini_binding = {"image_sha256": hashlib.sha256(mini).hexdigest(), "identical_regions": list(regions),
            "all_loaded_instruction_windows_identical": len(program.code),
            "data_ranges": [{"start": start, "bytes": size,
                "sha256": hashlib.sha256(app[image_offset(start):image_offset(start) + size]).hexdigest()} for start, size in data_ranges],
            "embedded_capture_identical": True, "reset_configuration": 12}
    report = {"schema": 1, "project": "HyperRig", "result": "pass", "component": "native-capture-live-processing",
        "scope": "native loading, warm-up and sequential processing with unchanged context, arena, source and original-address scratch",
        "newly_reconstructed_original_functions": 0, "total_comparisons": sum(counts.values()), "comparisons": counts,
        "actual_numerical_calls": numerical, "parser_entries": parsers, "reset_entries": resets, "reset_words": reset_words,
        "carried_steps": carried, "null_callback_comparisons": null_callback, "native_steps": steps,
        "result_digest": digest.hexdigest(), "invalid_api_checks": invalid, "mapping_guard_checks": guards,
        "numerical_domain_guard_checks": domain_guards,
        "functions": {name: {"start": lo, "end_exclusive": hi,
            "bytes_sha256": hashlib.sha256(app[image_offset(lo):image_offset(hi)]).hexdigest(),
            "decoded": sum(lo <= pc < hi for pc in program.code), "visited": sum(lo <= pc < hi for pc in coverage),
            "rts_only": name.startswith("noop_")} for name, (lo, hi) in regions.items()},
        "instruction_coverage": {"new_decoded": 0, "new_visited": 0, "unvisited_new": [],
            "all_decoded": len(program.code), "all_visited": len(coverage), "joined_decoded": len(joined),
            "joined_visited": len(joined & coverage), "unvisited_joined": sorted(joined - coverage)},
        "table": {"start": TABLE_START, "end": TABLE_END, "hex": program.processing.table.hex()},
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names()},
        "original_image_sha256": hashlib.sha256((ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin").read_bytes()).hexdigest(),
        "decoded_sha256": hashlib.sha256(app).hexdigest(),
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(), "mini_v4_binding": mini_binding,
        "compared": ["results", "all 34 mapped regions", "ordered external calls and numerical-entry snapshots", "read order"],
        "limitations": ["sequential native entries, not a recovered surrounding audio scheduler",
            "earlier native-loading and optimized three-channel numerical domains still apply",
            "sources and arena remain allocated; no concurrent mutation or arbitrary aliasing",
            "physical allocation/storage, metadata, scheduling and mode/priority bodies remain services",
            "single candidate heap; old owned source must be disjoint when allocating a replacement",
            "no target execution, hardware/audio, timing or complete firmware build"],
        "hardware_test": False, "audio_test": False, "firmware_changed": False}
    if output:
        if output.exists():
            raise ValueError("report output already exists")
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("total_comparisons", "actual_numerical_calls", "native_steps", "parser_entries", "reset_entries")}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mini-image", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    verify(args.library, args.output, args.mini_image, args.smoke)
