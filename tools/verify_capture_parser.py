"""Compare native-layout C parsing with the complete original parser instructions."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib

from capture_parser_machine import CaptureParserProgram, REGIONS, ROOT, CONTEXT, LEDGER, SOURCE, ARENA, CONFIG, image_offset

U32, U8 = ctypes.c_uint32, ctypes.c_uint8
MAP = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, U32, U32)


class IO(ctypes.Structure):
    _fields_ = [("map", MAP), ("opaque", ctypes.c_void_p)]


def fixture(*, channels=3, layers=1, kernel=6, dilation=3, head=3, abits=32,
            fractions=(16, 16, 12, 12), rechannel=15, activation=16, residual=16,
            conv=15, mix=16, linear=15, final=15, bias=None, seed=1):
    rng = random.Random(seed)
    data = bytearray(struct.pack("<4sHBBIHBB4B16s", b"A2L1", 1, 16, abits, 48000,
        layers, channels, head, *[x & 255 for x in fractions], b"HyperRig native"))
    def weights(n):
        return struct.pack("<" + "h" * n, *[rng.randrange(-32768, 32768) for _ in range(n)])
    def biases(n):
        return struct.pack("<" + "q" * n, *[rng.randrange(-(1 << 63), 1 << 63) if bias is None else bias for _ in range(n)])
    data += bytes([rechannel & 255]) + weights(channels)
    for index in range(layers):
        data += struct.pack("<BHBBI", kernel, dilation, activation & 255, residual & 255, 0xFEDCBA00 + index)
        data += bytes([conv & 255]) + weights(channels * channels * kernel) + biases(channels)
        data += bytes([mix & 255]) + weights(channels)
        data += bytes([linear & 255]) + weights(channels * channels) + biases(channels)
    data += bytes([final & 255]) + weights(channels * head) + biases(1)
    return crc_blob(data)


def crc_blob(body):
    return bytes(body) + struct.pack("<I", zlib.crc32(body))


def initial():
    return bytearray((i * 17 + 0xA5) & 255 for i in range(228))


def configure(library):
    fn = library.hyperrig_capture_parser
    fn.argtypes = [ctypes.POINTER(U8), ctypes.POINTER(U32), ctypes.POINTER(U8), U32, U32, ctypes.POINTER(IO)]
    fn.restype = ctypes.c_int
    return fn


def c_run(function, context, ledger, source, arena, configuration=0xFFFFFFFF, *, missing_map=False):
    context_storage = (U8 * 260)(*([0xEE] * 260))
    context_view = (U8 * 228).from_buffer(context_storage, 16)
    context_view[:] = context
    ledger_storage = (U32 * 11)(*([0xEEEEEEEE] * 11))
    ledger_view = (U32 * 3).from_buffer(ledger_storage, 16)
    ledger_view[:] = ledger
    source_storage = (U8 * max(1, len(source))).from_buffer_copy(source or b"\0")
    arena_storage = (U8 * (len(arena) + 32))(*([0xDD] * (len(arena) + 32)))
    arena_view = (U8 * len(arena)).from_buffer(arena_storage, 16)
    arena_view[:] = arena
    def mapping(_opaque, address, size):
        if not missing_map and ARENA <= address <= address + size <= ARENA + len(arena):
            return ctypes.addressof(arena_storage) + 16 + address - ARENA
        return None
    cb = MAP(mapping)
    io = IO(cb, None)
    result = function(context_view, ledger_view, source_storage, len(source), configuration, ctypes.byref(io))
    assert bytes(context_storage[:16]) + bytes(context_storage[-16:]) == bytes([0xEE] * 32)
    assert list(ledger_storage[:4]) + list(ledger_storage[-4:]) == [0xEEEEEEEE] * 8
    assert bytes(arena_storage[:16]) + bytes(arena_storage[-16:]) == bytes([0xDD] * 32)
    assert bytes(source_storage)[:len(source)] == source
    return {"result": result & 0xFFFFFFFF, "memory": (bytes(context_view), bytes(ledger_view), bytes(source), bytes(arena_view), struct.pack("<I", configuration))}


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program = CaptureParserProgram()
    app = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
    configuration_bytes = app[image_offset(CONFIG):image_offset(CONFIG) + 4]
    reset_configuration = struct.unpack("<I", configuration_bytes)[0]
    assert reset_configuration == 12
    function = configure(ctypes.CDLL(str(library_path.resolve())))
    coverage, counts, statuses = set(), {}, {}
    total_steps = 0
    digest = hashlib.sha256()
    def compare(blob, *, capacity=0, used=0, configuration=0xFFFFFFFF, query=True, arena_size=None, category="format"):
        nonlocal total_steps
        context = initial()
        arena = bytes([0xB7] * (arena_size if arena_size is not None else capacity))
        ledger = [0 if query else ARENA, used, capacity]
        original = program.execute(context, ledger, blob, arena, configuration)
        actual = c_run(function, context, ledger, blob, arena, configuration)
        if original["result"] != actual["result"] or original["memory"] != actual["memory"]:
            diff = {i: [(j, a, b) for j, (a, b) in enumerate(zip(x, y)) if a != b][:15]
                    for i, (x, y) in enumerate(zip(actual["memory"], original["memory"])) if x != y}
            raise AssertionError((category, len(blob), ledger, configuration, actual["result"], original["result"], diff))
        coverage.update(original["visited"])
        counts[category] = counts.get(category, 0) + 1
        statuses[str(original["result"])] = statuses.get(str(original["result"]), 0) + 1
        total_steps += original["steps"]
        digest.update(struct.pack("<I", actual["result"]))
        for data in actual["memory"]:
            digest.update(data)
        return original

    small = fixture(channels=1, kernel=1, head=1)
    for length in range(44):
        compare(small[:length])
    for length in range(40, len(small) - 4):
        compare(crc_blob(small[:length]), query=False, capacity=4096, category="truncation")
    three = fixture()
    for length in range(40, 47):
        compare(crc_blob(three[:length]), query=False, capacity=4096, category="truncation")
    for channels in (1, 3, 16):
        compare(fixture(channels=channels, kernel=1, head=1, abits=16),
                query=False, capacity=16384, category="activation16")
    for offset, value in ((14, 0), (14, 17), (15, 0), (15, 65)):
        body = bytearray(small[:-4])
        body[7], body[offset] = 16, value
        compare(crc_blob(body), query=False, capacity=4096, category="activation16")
    for offset, values in ((0, (0, ord("X"))), (4, (0, 2)), (6, (0, 8, 32)), (7, (0, 8, 64)),
                            (12, (0, 2, 65, 255)), (14, (0, 17, 255)), (15, (0, 65, 255))):
        for value in values:
            body = bytearray(small[:-4])
            body[offset] = value
            compare(crc_blob(body), query=False, capacity=4096)
    bad = bytearray(small)
    for offset in (0, 20, len(bad) - 1):
        bad[offset] ^= 1
        compare(bytes(bad))
        bad[offset] ^= 1
    compare(crc_blob(small[:-4] + b"extra"), query=False, capacity=4096)
    for offset in (39, 40, 41):
        body = bytearray(small[:-4])
        body[offset] = 0
        compare(crc_blob(body), query=False, capacity=4096)
    print("Native parser minimum size, CRC, format and truncation comparisons passed.", flush=True)

    for channels in (1, 2, 3, 4, 16):
        for kernel, head in ((1, 1), (6, 3), (15, 64), (16, 2), (255, 1)):
            blob = fixture(channels=channels, kernel=kernel, head=head)
            result = compare(blob, category="layout_query")
            needed = struct.unpack_from("<I", result["memory"][1], 4)[0]
            if needed <= 0x200000:
                compare(blob, query=False, capacity=needed, category="layout_load")
    for layers in (2, 3, 16, 64, 65):
        blob = fixture(channels=1, layers=layers, kernel=1, head=1)
        result = compare(blob, category="layers")
        needed = struct.unpack_from("<I", result["memory"][1], 4)[0]
        compare(blob, query=False, capacity=needed, category="layers")
    for configuration in (0, 1, 2, 3, 0xFFFFFFFF):
        compare(fixture(layers=3), query=False, capacity=16384, configuration=configuration, category="configuration")
    print("Native descriptors, packed weights, large dimensions and configuration comparisons passed.", flush=True)

    blob = fixture(channels=3, kernel=6, head=3)
    needed = struct.unpack_from("<I", compare(blob, category="capacity")["memory"][1], 4)[0]
    for capacity in (0, 1, 79, 80, 81, 85, 86, 87, 88, 103, 104, 127, 128, needed - 1, needed, needed + 1, 0xFFFFFFFF):
        compare(blob, query=False, capacity=capacity, arena_size=needed + 16, category="capacity")
    for used in (*range(8), 255, 256, 0xFFFFFFF0, 0xFFFFFFF8, 0xFFFFFFFC, 0xFFFFFFFF):
        compare(small, used=used, category="allocation_wrap")
    for dilation in (1, 64, 65535):
        compare(fixture(channels=3, kernel=255, dilation=dilation), query=False, capacity=8192, category="large_history")
    edges = (-128, -63, -62, -32, -31, -1, 0, 1, 30, 31, 32, 62, 63, 127)
    for name in ("rechannel", "activation", "residual", "conv", "mix", "linear", "final"):
        for value in edges:
            compare(fixture(channels=1, kernel=1, head=1, **{name: value}), query=False, capacity=4096, category="fractions")
    for index in range(4):
        for value in edges:
            fractions = [16, 16, 12, 12]
            fractions[index] = value
            compare(fixture(channels=1, kernel=1, head=1, fractions=fractions), query=False, capacity=4096, category="fractions")
    for shift in (0, 1, 15, 31):
        for bias in (-(1 << 63), -(1 << 31) - 1, -(1 << 31), -1, 0, 1, (1 << 31) - 1, 1 << 31, (1 << 63) - 1):
            compare(fixture(channels=3, kernel=1, head=1, conv=shift, final=shift, bias=bias),
                    query=False, capacity=4096, category="biases")
    embedded = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
    embedded_offset = app.find(embedded)
    assert embedded_offset >= 0 and app.find(embedded, embedded_offset + 1) == -1
    result = compare(embedded, category="embedded")
    needed = struct.unpack_from("<I", result["memory"][1], 4)[0]
    compare(embedded, query=False, capacity=needed, category="embedded")
    result = compare(embedded, configuration=reset_configuration, category="embedded_reset_configuration")
    reset_needed = struct.unpack_from("<I", result["memory"][1], 4)[0]
    assert (needed, reset_needed) == (117896, 118664)
    for capacity in (reset_needed - 1, reset_needed):
        compare(embedded, query=False, capacity=capacity, configuration=reset_configuration,
                category="embedded_reset_configuration")
    print("Capacity, unsigned allocation wrap, signed shifts, biases and embedded capture comparisons passed.", flush=True)

    context, ledger, source = (U8 * 228)(*initial()), (U32 * 3)(0, 0, 0), (U8 * len(small)).from_buffer_copy(small)
    seen = []
    mapping = MAP(lambda *args: seen.append(args) or None)
    io, bad = IO(mapping, None), IO(MAP(), None)
    invalid = ((None, ledger, source, len(small), 0, ctypes.byref(io)), (context, None, source, len(small), 0, ctypes.byref(io)),
               (context, ledger, None, 1, 0, ctypes.byref(io)), (context, ledger, source, len(small), 0, None),
               (context, ledger, source, len(small), 0, ctypes.byref(bad)))
    for args in invalid:
        before = bytes(context), bytes(ledger)
        assert function(*args) == -200 and not seen
        assert before == (bytes(context), bytes(ledger))
    guard = c_run(function, initial(), [ARENA, 0, 4096], small, bytes(4096), missing_map=True)
    assert guard["result"] == (-201) & 0xFFFFFFFF
    new = set(program.code) - program.pre_parser_code
    missing = sorted(new - coverage)
    unreachable = {
        "minimum_length_protects_header": [pc for pc in missing if 0x02031D50 <= pc < 0x02031F06],
        "minimum_length_protects_rechannel_fraction": [pc for pc in missing if 0x02032016 <= pc < 0x02032020],
        "validated_nonzero_channels": [pc for pc in missing if pc == 0x020322E0],
        "validated_convolution_shift_0_through_31": [pc for pc in missing if 0x020325CA <= pc < 0x02032606],
        "validated_nonzero_layer_count": [pc for pc in missing if 0x02032716 <= pc < 0x0203271A],
    }
    classified = {pc for group in unreachable.values() for pc in group}
    assert classified == set(missing), [hex(pc) for pc in set(missing) - classified]
    mini_binding = None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw = mini_image.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI image is not the reviewed v4 input")
        app = unpack_app(raw)[2]["app.bin"]
        for name, (start, end) in REGIONS.items():
            assert app[image_offset(start):image_offset(end)] == program.parser_regions[name]
        assert app[image_offset(CONFIG):image_offset(CONFIG) + 4] == configuration_bytes
        assert app[embedded_offset:embedded_offset + len(embedded)] == embedded
        mini_binding = {"image_sha256": sha, "whole_parser_and_read64_byte_identical": True,
                        "reset_configuration_byte_identical": True, "embedded_capture_byte_identical": True}
    machines = ("dot", "control", "control_action", "selection", "preset_storage", "preset_preflight", "preset_assets", "capture_loader", "capture_container", "capture_dispatch", "capture_parser")
    sources = {f"tools/{name}_machine.py" for name in machines}
    sources.update(("tools/verify_capture_parser.py", "tools/build_capture_parser.py", "tests/test_capture_parser_machine.py",
        "tests/capture_parser_sanitize.c", "firmware/src/hyperrig_capture_parser.c", "firmware/include/hyperrig/hyperrig_capture_parser.h",
        "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py", "upstream/pi32v2-isa/isa/pi32v2.toml"))
    report = {"schema": 1, "project": "HyperRig", "result": "pass", "scope": "complete native capture parser and read64 helper",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {name: {"start": start, "end_exclusive": end, "bytes_sha256": hashlib.sha256(program.parser_regions[name]).hexdigest()} for name, (start, end) in REGIONS.items()},
        "reset_copy_configuration": {"address": CONFIG, "value": reset_configuration,
            "bytes_sha256": hashlib.sha256(configuration_bytes).hexdigest(), "runtime_writers_traced": False},
        "embedded_capture": {"path": "analysis/firmware/m571_g_app/embedded-0.a2l", "size": len(embedded),
            "sha256": hashlib.sha256(embedded).hexdigest(), "decoded_app_offset": embedded_offset,
            "arena_bytes_configuration_uint32_max": needed, "arena_bytes_reset_configuration_12": reset_needed},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "native_steps": total_steps, "status_counts": statuses,
        "instruction_coverage": {"new_visited": len(new & coverage), "new_decoded": len(new), "unvisited_new": missing,
            "unvisited_by_entry_invariant": unreachable, "unclassified_unvisited": []},
        "invalid_api_checks": len(invalid), "new_mapping_guard_checks": 1, "result_digest": digest.hexdigest(),
        "compared": ["original status", "all context and ledger bytes", "complete mapped arena and preserved padding", "source/configuration preservation"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(sources)},
        "mini_v4_binding": mini_binding, "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["direct pure parser domain: source/context/ledger/arena/configuration do not alias",
            "native model maps at most 1 MiB source and 2 MiB arena; larger calculated requirements can be queried without arena storage",
            "unvisited instructions are reported and classified by dominating entry invariants; no exhaustive input-coverage claim",
            "history reset, sample processing, allocation platform and complete firmware integration are separate components"]}
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
