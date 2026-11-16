"""Compare the complete capture command against decoded original instructions offline."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib

from capture_command_machine import (CaptureCommandProgram, REGIONS, STATIC, original_bytes,
    ROOT, PAYLOAD, ERROR_WORD, ALLOCATE, FREE, PRINT, REPORT, GAIN_NAMES, GAIN_REGIONS,
    GAIN_TABLE, GAIN_BYTES)
from capture_journal_machine import (REGIONS as JOURNAL_REGIONS, PROGRAM, RAW_READ, WRAPPED_READ,
    ERASE_SECTOR, CLOCK, ELAPSED, NOTIFY, EVENT, PREPARE, ACTIVITY)
from capture_metadata_machine import REGIONS as METADATA_REGIONS, CACHE
from preset_storage_machine import REGIONS as STORAGE_REGIONS
from preset_assets_machine import REGIONS as ASSET_REGIONS
from control_machine import STATE, GLOBAL
from verify_capture_journal import (baseline as journal_baseline, SyntheticStorage, JournalRuntime,
    CState as JournalState, CMemory as JournalMemory, IO as JournalIO, U32, POINTER,
    PROGRAM_CALLBACK, READ_CALLBACK, SERVICE_CALLBACK)
from verify_capture_metadata import slot_address, capacity, record, journal

ALLOC_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, U32)
FREE_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, POINTER)
TEXT_CALLBACK = ctypes.CFUNCTYPE(U32, ctypes.c_void_p, U32, ctypes.POINTER(U32), U32)


def baseline():
    memory = journal_baseline() + (bytearray.fromhex("78563412"),)
    memory[0][9] = 2
    for offset, value in ((696, 3), (700, -47), (704, 1), (264, 3), (268, -2), (276, 0xFFFFFFFE)):
        struct.pack_into("<I", memory[1], offset, value & 0xFFFFFFFF)
    return memory


def fixture(slot=2, size=64, metadata=3, entries=(), extended=False):
    payload = bytes((i * 29 + 7) & 255 for i in range(size))
    identity = zlib.crc32(payload)
    header = struct.pack("<IIII", 0x43474B54, size, 0x2144DF1C if extended else identity, metadata) + bytes(range(24))
    address = slot_address(slot)
    return [(address, header), (address + 40, payload), *journal(size, entries, address)]


class Environment(SyntheticStorage):
    def __init__(self, replacements=None, **kwargs):
        super().__init__(**kwargs)
        self.replacements = replacements or {}

    def __call__(self, service, args, view):
        index = self.counts.get(service, 0)
        result = super().__call__(service, args, view)
        if service in (RAW_READ, WRAPPED_READ) and (service, index) in self.replacements:
            data = self.replacements[(service, index)]
            if len(data) != args[-1]:
                raise ValueError("replacement does not fill its read")
            return 0, data
        if service in (ALLOCATE, FREE, PRINT, REPORT):
            default = 1 if service == ALLOCATE else 0 if service == FREE else 0x10293847
            return self.results.get((service, index), default) & 0xFFFFFFFF
        return result


class CommandRuntime(ctypes.Structure):
    _fields_ = [("journal", JournalRuntime), ("error_word", U32)]


class IO(ctypes.Structure):
    _fields_ = [("journal", JournalIO), ("allocate", ALLOC_CALLBACK),
                ("release", FREE_CALLBACK), ("text", TEXT_CALLBACK)]


class CState(JournalState):
    def __init__(self, memory):
        super().__init__(memory[:19])
        self.command = CommandRuntime(self.journal, int.from_bytes(memory[19], "little"))
        self.journal, self.metadata = self.command.journal, self.command.journal.metadata
        self.allocated, self.live, self.allocations, self.releases = 0, False, 0, 0

    def snapshot(self):
        return super().snapshot() + (struct.pack("<I", self.command.error_word),)


class CMemory(JournalMemory):
    def write(self, address, value, size):
        if address == ERROR_WORD and size == 4:
            self.state.command.error_word = value
        else:
            super().write(address, value, size)

    def __init__(self, state):
        super().__init__(state)
        self.state = state


def configure(library):
    functions = {}
    signatures = {"execute": [ctypes.POINTER(CommandRuntime), POINTER, U32, ctypes.POINTER(U32), ctypes.POINTER(IO)],
        "tenths": [POINTER, U32, ctypes.POINTER(U32)],
        "decimal": [POINTER, U32, ctypes.POINTER(U32), ctypes.POINTER(U32), ctypes.POINTER(U32)],
        "pack": [U32, U32, U32]}
    for name, arguments in signatures.items():
        function = getattr(library, "hyperrig_capture_command_" + name)
        function.argtypes, function.restype = arguments, U32 if name == "pack" else ctypes.c_int
        functions[name] = function
    return functions


def callbacks(state, environment):
    calls, errors = [], []

    def invoke(service, args):
        calls.append((service, args, state.snapshot()))
        return environment(service, args, CMemory(state))

    def service(_opaque, token, a, b, c):
        try:
            return invoke(token, (a, b, c))
        except Exception as error:
            errors.append(error)
            return 0

    def program(_opaque, address, source, size):
        try:
            return invoke(PROGRAM, (address, "source", 0, ctypes.string_at(source, size)))
        except Exception as error:
            errors.append(error)
            return 0

    def read(_opaque, token, address, destination, size):
        try:
            pointer, first = ctypes.cast(destination, ctypes.c_void_p).value, ctypes.addressof(state.data)
            if first <= pointer < first + 8192 and (not state.live or pointer + size > first + state.allocated):
                raise ValueError("C reload exceeded its live allocation request")
            status, data = invoke(token, (address, "read_buffer", 0, size))
            if data:
                ctypes.memmove(destination, data, len(data))
            return status
        except Exception as error:
            errors.append(error)
            return 1

    def allocate(_opaque, size):
        try:
            assert not state.live and 4 <= size <= 8152
            success = invoke(ALLOCATE, (size,))
            if success:
                state.live, state.allocated = True, size
                state.allocations += 1
                return ctypes.addressof(state.data)
            return None
        except Exception as error:
            errors.append(error)
            return None

    def release(_opaque, pointer):
        try:
            assert state.live and ctypes.cast(pointer, ctypes.c_void_p).value == ctypes.addressof(state.data)
            invoke(FREE, (PAYLOAD,))
            state.live = False
            state.releases += 1
        except Exception as error:
            errors.append(error)

    def text(_opaque, token, words, count):
        try:
            assert (token == REPORT and count == 10) or (token == PRINT and 1 <= count <= 3)
            return invoke(token, tuple(words[i] for i in range(count)))
        except Exception as error:
            errors.append(error)
            return 0

    io = IO(JournalIO(SERVICE_CALLBACK(service), PROGRAM_CALLBACK(program), READ_CALLBACK(read), None),
            ALLOC_CALLBACK(allocate), FREE_CALLBACK(release), TEXT_CALLBACK(text))
    return io, calls, errors


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program, functions = CaptureCommandProgram(), configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, service_counts = dict.fromkeys(("command", "tenths", "decimal", "pack"), 0), set(), {}
    mutations = allocations = frees = carried = 0
    output_hash = hashlib.sha256()

    def compare(operation, text=b"", arguments=(), memory=None, sequence=False, **script):
        nonlocal mutations, allocations, frees, carried
        memory = baseline() if memory is None else memory
        native_env, c_env = Environment(**script), Environment(**script)
        original = program.execute(memory, operation, text, arguments, native_env)
        state, value, end = CState(memory), U32(0xC0DEC0DE), U32(0xFACEFACE)
        data = (ctypes.c_uint8 * (len(text) + 1)).from_buffer_copy(text + b"\0")
        io, calls, errors = callbacks(state, c_env)
        if operation == "command":
            api = functions["execute"](ctypes.byref(state.command), data, len(data), ctypes.byref(value), ctypes.byref(io))
            assert api == 0, (text, api)
            actual = value.value
        elif operation == "pack":
            actual = functions["pack"](*arguments)
        elif operation == "tenths":
            actual = functions["tenths"](data, len(data), ctypes.byref(value))
            assert value.value == original["output"], (text, value.value, original["output"])
        else:
            error = U32(state.command.error_word)
            assert functions["decimal"](data, len(data), ctypes.byref(value), ctypes.byref(end), ctypes.byref(error)) == 0
            state.command.error_word = error.value
            actual = value.value
            assert end.value == original["end"], (text, end.value, original["end"])
        if errors:
            raise errors[0]
        if ((actual & 0xFFFFFFFF) != original["result"] or state.snapshot() != original["memory"] or
                calls != original["calls"] or c_env.data != native_env.data or state.live or
                state.allocations != original["allocations"] or state.releases != original["releases"]):
            changed = {i: [(j, a, b) for j, (a, b) in enumerate(zip(left, right)) if a != b][:8]
                for i, (left, right) in enumerate(zip(state.snapshot(), original["memory"])) if i != 2 and left != right}
            mismatch = next((i for i, (a, b) in enumerate(zip(calls, original["calls"])) if a != b), None)
            raise AssertionError((operation, text, arguments, actual, original["result"], changed,
                "first_call_mismatch", mismatch, [(x[0], x[1]) for x in calls],
                [(x[0], x[1]) for x in original["calls"]], "storage_equal", c_env.data == native_env.data))
        for key in ("reads", "results", "mutations", "replacements"):
            for service, index in script.get(key, {}):
                assert index < native_env.counts.get(service, 0), (key, service, index, text)
        for index in script.get("programs", {}):
            assert index < native_env.counts.get(PROGRAM, 0), ("program", index, text)
        assert bytes(data) == text + b"\0"
        counts[operation] += 1
        coverage.update(original["visited"])
        for token, count in native_env.counts.items():
            service_counts[token] = service_counts.get(token, 0) + count
        mutations += bool(script.get("mutations"))
        allocations += original["allocations"]
        frees += original["releases"]
        carried += sequence
        output_hash.update(struct.pack("<I", actual & 0xFFFFFFFF))
        for row in original["memory"]:
            output_hash.update(bytes([row]) if isinstance(row, int) else row)
        return original, native_env

    syntax = [b"", b"live", b"live   ", b"LIVE", b"livel", b"live\t0", b" ", b"-1", b"15", b"999999999999999999",
        b"live 0", b"live 12", b"live -12.0", b"live +0.5", b"live 12.5", b"live -12.5", b"live 0.1",
        b"live .5", b"live 1.", b"live 1.00", b"live 1.5x", b"live 1.5\t", b"live 100001", b"live --1",
        b"live 1 -", b"live 1 - ", b"live 1 -200", b"live 1 400", b"live 1 401", b"live 1 -201",
        b"live 1 +20", b"live 1 20 ", b"live 1 \t20", b"live 1 --20", b"live 1 2147483648", b"live 1 -2147483649"]
    for text in syntax:
        compare("command", text)
    for slot in (0, 2, 7, 8, 14):
        for current_slot in (slot, 255):
            memory = baseline(); memory[0][9] = current_slot
            for suffix in (b"", b" 1.5", b" 2.5 30", b" 2.5 -"):
                compare("command", str(slot).encode() + suffix, memory=memory, regions=fixture(slot))
    for text in (b" 2 +1.0", b"2+1.0", b"2-1.0", b"2x", b"2.0"):
        compare("command", text, regions=fixture())
    for metadata in (0, 0x010190FE, 0x01FF3818, 0xFFFFFFFF, 0x02000000):
        for text in (b"2", b"2 2.5", b"2 2.5 -"):
            compare("command", text, regions=fixture(metadata=metadata))
    for half in range(-24, 25):
        text = f"live {half / 2:.1f}".encode()
        compare("command", text)
    for value in (0, 1, 127, 255):
        memory = baseline(); memory[0][9] = value
        compare("command", b"", memory=memory)
        compare("command", b"live", memory=memory)
    print("Command syntax, current/slot queries and live gain paths compared.", flush=True)

    numeric = [b"", b"0", b"-0", b"+1", b"2147483647", b"2147483648", b"-2147483648", b"-2147483649",
        b"999999999999999999999999", b"-999999999999999999999999", b" 12x", b"\t\n\r\v\f-17", b"+", b"-", b"x", b"1.5"]
    for text in numeric:
        compare("decimal", text)
        compare("tenths", text)
    for byte in range(1, 256):
        compare("decimal", bytes([byte]) + b"12")
        compare("tenths", b"1" + bytes([byte]))
    for whole in (0, 1, 12, 24, 99999, 100000, 100001):
        for sign in (b"", b"+", b"-"):
            for suffix in (b"", b".0", b".5", b".9", b".55", b" ", b".5 next"):
                compare("tenths", sign + str(whole).encode() + suffix)
    for gain in (-2147483648, -25, -24, -1, 0, 1, 24, 25, 2147483647):
        for present in (0, 1, 0xFFFFFFFF):
            for aux in (-2147483648, -201, -200, -1, 0, 400, 401, 2147483647):
                compare("pack", arguments=(gain & 0xFFFFFFFF, present, aux & 0xFFFFFFFF))
    print("Native gain/decimal parsing and packed metadata helpers compared.", flush=True)

    # A small payload leaves 249 records and exercises several scanner chunks.
    regions = fixture()
    # Scan read counts derive from the fixture layout, not from the C implementation.
    chunks = (capacity(64) + 15) // 16
    second_header = 1 + chunks
    second_scan = second_header + 1
    append_read = second_scan + chunks
    for failed in (0, second_header, 1, second_scan):
        compare("command", b"2 2.5", regions=regions, reads={(WRAPPED_READ, failed): (1, 0, None)})
    for reads in ({(WRAPPED_READ, append_read): (1, 0, None)},
                  {(WRAPPED_READ, append_read): (0, 16, 0)},
                  {(WRAPPED_READ, append_read): (1, 8, None), (WRAPPED_READ, append_read + 1): (0, 16, 1)}):
        compare("command", b"2 2.5", regions=regions, reads=reads)
    for programs in ({0: (0, 0)}, {0: (0, 8), 1: (0, 0)}, {0: (17, 16)}):
        compare("command", b"2 2.5", regions=regions, programs=programs)
    for size in (0, 1, 3, 4, 255, 256, 257, 4056, 4096, 8000, 8152):
        layout = fixture(size=size)
        # Fill every available record with non-erased invalid tags to force compaction.
        layout += journal(size, [(i, bytes(16)) for i in range(capacity(size))], slot_address(2))
        compare("command", b"2 2.5", regions=layout)
    full = fixture(size=8152)
    for result in (0,):
        compare("command", b"2 2.5", regions=full, results={(ALLOCATE, 0): result})
    # A full slot has no scanner reads: header1, header2, reload-header, reload-payload.
    for failed in (2, 3):
        compare("command", b"2 2.5", regions=full, reads={(WRAPPED_READ, failed): (1, 0, None)})
    compare("command", b"2 2.5", regions=full, reads={(WRAPPED_READ, 3): (0, 8152, 17)})
    for programs in ({0: (0, 0)}, {0: (0, 0), 1: (0, 0)}, {32: (0, 0)}):
        compare("command", b"2 2.5", regions=full, programs=programs)
    for failure in ((0xFFFFFFFF, 0, None), (0, 40, 0), (1, 40, None)):
        compare("command", b"2 2.5", regions=full, reads={(RAW_READ, 0): failure})
    compare("command", b"2 2.5", regions=full, reads={(RAW_READ, 1): (0, 256, 100), (RAW_READ, 3): (0, 256, 7)})
    print("Append retry, allocation, reload and complete rewrite retry paths compared.", flush=True)

    for slot in (2, 8, 14):
        layout = fixture(slot, extended=True)
        for failed in (None, 1):
            compare("command", str(slot).encode(), regions=layout,
                    reads={} if failed is None else {(WRAPPED_READ, failed): (1, 0, None)})
        compare("command", str(slot).encode() + b" 2.5", regions=layout)
    # The second extended identity failure maps to the command's -2 report.
    compare("command", b"2 2.5", regions=fixture(extended=True), reads={(WRAPPED_READ, chunks + 3): (1, 0, None)})
    for service, index, plan in (
        (WRAPPED_READ, 0, ((GLOBAL + 9, 8, 1),)),
        (CLOCK, 0, ((GLOBAL + 9, 2, 1), (STATE + 268, 24, 4))),
        (PROGRAM, 0, ((GLOBAL + 9, 255, 1),)),
        (NOTIFY, 0, ((STATE + 276, 0xFFFFFFFF, 4),)),
        (REPORT, 0, ((STATE + 704, 0, 4),)),
        (PRINT, 0, ((ERROR_WORD, 77, 4),)),
        (ALLOCATE, 0, ((GLOBAL + 9, 2, 1),)),
        (FREE, 0, ((STATE + 268, 0, 4),))):
        text = b"bad" if service == PRINT else b"2 2.5"
        compare("command", text, regions=full if service in (ALLOCATE, FREE) else regions,
                mutations={(service, index): plan})
    memory, stored = baseline(), fixture()
    for text in (b"2 2.5", b"2", b"2 -3.5 100", b"live -1 -", b"2", b"2 -3.5 -"):
        result, env = compare("command", text, memory=memory, regions=stored, sequence=True)
        memory = result["memory"]
        stored = [(address, bytes([byte])) for address, byte in env.data.items()]

    invalid, guard = check_invalid_and_growth(functions)
    new_code = set(program.code) - program.pre_command_code
    command_code = {pc for pc in program.code if REGIONS["command"][0] <= pc < REGIONS["command"][1]}
    missing_command = sorted(command_code - coverage)
    assert not missing_command, [hex(pc) for pc in missing_command]
    mini_binding = bind_mini(program, mini_image) if mini_image else None
    source_paths = source_files()
    report = {"schema": 1, "project": "HyperRig", "result": "pass",
        "scope": "complete capture metadata text command with native parsing and storage dependencies",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "regions": {name: {"start": start, "end_exclusive": end,
            "sha256": hashlib.sha256(program.command_regions[name]).hexdigest(),
            "decoded": sum(start <= pc < end for pc in program.code),
            "visited": sum(start <= pc < end for pc in coverage)} for name, (start, end) in REGIONS.items()},
        "static_evidence": {name: {"start": start, "end_exclusive": end,
            "sha256": hashlib.sha256(program.static[name]).hexdigest()} for name, (start, end) in STATIC.items()},
        "comparisons": counts, "total_comparisons": sum(counts.values()), "mutating_cases": mutations,
        "carried_commands": carried, "successful_allocations": allocations, "matching_releases": frees,
        "invalid_api_checks": invalid, "allocation_growth_guards": guard,
        "instruction_coverage": {"new_visited": len(coverage & new_code), "new_decoded": len(new_code),
            "command_visited": len(coverage & command_code), "command_decoded": len(command_code),
            "all_visited": len(coverage), "all_decoded": len(program.code),
            "unvisited_new": [f"0x{pc:08x}" for pc in sorted(new_code - coverage)]},
        "external_service_counts": {f"0x{key:08x}": value for key, value in sorted(service_counts.items())},
        "outputs_and_state_sha256": output_hash.hexdigest(), "mini_v4_binding": mini_binding,
        "compared": ["terminal report/print argument words and raw return", "all 20 mapped regions at every service boundary",
            "program bytes and read requests", "allocation sizes, free order and exact ownership",
            "final synthetic storage bytes", "native parser outputs/end offsets/errno"],
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths},
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "physical_writes": False, "firmware_changed": False,
        "limitations": ["text formatting/report helper and physical transport remain external",
            "allocator, physical storage, clock, notifications and scheduler are scripted",
            "decimal conversion uses only base ten and the pinned locale table/pointers",
            "new allocation-growth rejection has no original-instruction equivalence claim",
            "synthetic byte writes do not establish durable flash behavior or power-loss atomicity"]}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("result", "comparisons", "total_comparisons", "instruction_coverage")}))
    return report


def check_invalid_and_growth(functions):
    state, env = CState(baseline()), Environment()
    io, calls, errors = callbacks(state, env)
    data = (ctypes.c_uint8 * 2)(ord('x'), 0)
    value, end, error = U32(0xC0DEC0DE), U32(0xFACEFACE), U32(0x12345678)
    runtime, output, config = ctypes.byref(state.command), ctypes.byref(value), ctypes.byref(io)
    invalid = [("execute", (None, data, 2, output, config)), ("execute", (runtime, None, 2, output, config)),
        ("execute", (runtime, data, 0, output, config)), ("execute", (runtime, data, 257, output, config)),
        ("execute", (runtime, data, 1, output, config)), ("execute", (runtime, data, 2, None, config)),
        ("execute", (runtime, data, 2, output, None)), ("tenths", (None, 2, output)),
        ("tenths", (data, 0, output)), ("tenths", (data, 257, output)), ("tenths", (data, 1, output)),
        ("tenths", (data, 2, None)), ("decimal", (data, 2, None, ctypes.byref(end), ctypes.byref(error))),
        ("decimal", (data, 2, output, None, ctypes.byref(error))), ("decimal", (data, 2, output, ctypes.byref(end), None))]
    for name in ("allocate", "release", "text"):
        bad = IO.from_buffer_copy(io)
        setattr(bad, name, dict(allocate=ALLOC_CALLBACK, release=FREE_CALLBACK, text=TEXT_CALLBACK)[name]())
        invalid.append(("execute", (runtime, data, 2, output, ctypes.byref(bad))))
    for name in ("call", "program", "read"):
        bad = IO.from_buffer_copy(io)
        setattr(bad.journal, name, dict(call=SERVICE_CALLBACK, program=PROGRAM_CALLBACK, read=READ_CALLBACK)[name]())
        invalid.append(("execute", (runtime, data, 2, output, ctypes.byref(bad))))
    for operation, arguments in invalid:
        before = state.snapshot()
        assert functions[operation](*arguments) == -200
        assert state.snapshot() == before and value.value == 0xC0DEC0DE and end.value == 0xFACEFACE and not calls
    # First length zero allocates four bytes; a reload header grows to five.
    regions = fixture(size=0)
    regions += journal(0, [(i, bytes(16)) for i in range(capacity(0))], slot_address(2))
    chunks = (capacity(0) + 15) // 16
    reload_index = 2 + 2*chunks
    growing = fixture(size=5)[0][1]
    state, env = CState(baseline()), Environment(regions=regions, replacements={(WRAPPED_READ, reload_index): growing})
    io, calls, errors = callbacks(state, env)
    text = (ctypes.c_uint8 * 6).from_buffer_copy(b"2 2.5\0")
    value = U32(0xC0DEC0DE)
    assert functions["execute"](ctypes.byref(state.command), text, 6, ctypes.byref(value), ctypes.byref(io)) == -201
    assert not errors and not state.live and state.allocations == state.releases == 1 and value.value == 0xC0DEC0DE
    assert calls[-1][0] == FREE and env.counts[WRAPPED_READ] == reload_index + 1
    return len(invalid), 1


def bind_mini(program, path):
    from hyperrig.jieli import unpack_app
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
        raise ValueError("MINI input is not the reviewed v4 application")
    app = unpack_app(raw)[2]["app.bin"]
    regions = {f"command_{name}": region for name, region in REGIONS.items()}
    regions.update({f"journal_{name}": region for name, region in JOURNAL_REGIONS.items()})
    regions.update({f"metadata_{name}": region for name, region in METADATA_REGIONS.items()})
    regions.update({f"gain_{name}": GAIN_REGIONS[name] for name in GAIN_NAMES})
    regions.update({f"storage_{name}": STORAGE_REGIONS[name] for name in ("header", "record", "crc_update", "checksum")})
    regions.update({f"asset_{name}": ASSET_REGIONS[name] for name in ("resolve", "identity", "extended")})
    original = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
    for region in (*regions.values(), *STATIC.values(), (GAIN_TABLE, GAIN_TABLE + GAIN_BYTES)):
        assert original_bytes(app, *region) == original_bytes(original, *region)
    return {"image_sha256": digest, "all_executed_dependency_regions_identical": sorted(regions),
            "static_configuration_and_gain_table_identical": True}


def source_files():
    names = ("dot_machine", "control_machine", "control_action_machine", "selection_machine", "preset_storage_machine",
        "preset_preflight_machine", "preset_assets_machine", "capture_metadata_machine", "capture_journal_machine",
        "capture_loader_machine", "capture_command_machine", "verify_controls", "verify_control_actions",
        "verify_selection", "verify_preset_storage", "verify_preset_preflight", "verify_preset_assets",
        "verify_capture_metadata", "verify_capture_journal", "verify_capture_command", "build_capture_command")
    paths = {f"tools/{name}.py" for name in names}
    paths.update(("tests/test_capture_command_machine.py", "tests/capture_command_sanitize.c", "research/input-manifest.json",
        "hyperrig/jieli.py", "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
        "upstream/pi32v2-isa/isa/pi32v2.toml"))
    for name in ("controls", "control_actions", "selection", "preset_storage", "preset_assets",
                 "capture_loader", "capture_metadata", "capture_journal", "capture_command"):
        paths.update((f"firmware/src/hyperrig_{name}.c", f"firmware/include/hyperrig/hyperrig_{name}.h"))
    return sorted(paths)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve completed reports; choose a new output path")
    verify(args.library, args.output, args.mini_image)
