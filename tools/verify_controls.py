"""Compare recovered host C with original switch instruction execution, offline."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from control_machine import ControlsProgram, GLOBAL_BYTES, STATE_BYTES, IMMEDIATE, TRANSITION


class Context(ctypes.Structure):
    _fields_ = [("global_", ctypes.c_uint8 * GLOBAL_BYTES),
                ("state", ctypes.c_uint8 * STATE_BYTES), ("owner", ctypes.c_uint8)]


EMIT_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint)


def snapshot(context):
    return bytes(context.global_), bytes(context.state), context.owner


def context_from(globals_, state, owner):
    return Context((ctypes.c_uint8 * GLOBAL_BYTES).from_buffer_copy(globals_),
                   (ctypes.c_uint8 * STATE_BYTES).from_buffer_copy(state), owner)


def baseline(mapping=(0, 1, 2, 3)):
    globals_, state = bytearray(GLOBAL_BYTES), bytearray(STATE_BYTES)
    globals_[116:120] = bytes(mapping)
    state[74] = 1
    return globals_, state, 0


def verify(library_path, output, mini_image=None):
    native = ControlsProgram()
    mini_binding = None
    if mini_image is not None:
        sys.path.insert(0, str(ROOT))
        from hyperrig.jieli import unpack_app
        image = mini_image.read_bytes()
        image_sha = hashlib.sha256(image).hexdigest()
        if image_sha != "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI input is not the reviewed v4 application image")
        app = unpack_app(image)[2]["app.bin"]
        for program in (native.transition, native.immediate):
            if app[program.start - 0x02000120:program.end - 0x02000120] != program.raw:
                raise ValueError("MINI control function differs from the original G routine")
        mini_binding = {"image_sha256": image_sha, "both_function_regions_byte_identical": True}
    library = ctypes.CDLL(str(library_path.resolve()))
    transition = library.hyperrig_controls_transition
    transition.argtypes = [ctypes.POINTER(Context), ctypes.c_uint, ctypes.c_uint,
                           ctypes.c_uint32, ctypes.c_uint32, EMIT_CALLBACK, ctypes.c_void_p]
    transition.restype = ctypes.c_int
    immediate = library.hyperrig_controls_immediate
    immediate.argtypes = [ctypes.POINTER(Context), ctypes.c_uint]
    immediate.restype = ctypes.c_int
    counts = {"immediate_policy": 0, "transition": 0, "sequence_steps": 0, "invalid_api": 0}
    coverage, emitted = set(), {0: 0, 1: 0, 2: 0}
    rng = random.Random(0xC014C04)

    def compare(globals_, state, owner, physical, pressed, a, b, *, sequence=False):
        original = native.execute(globals_, state, owner, physical, pressed, a, b)
        context = context_from(globals_, state, owner)
        calls = []
        def record(_opaque, logical, event):
            calls.append((logical, event, snapshot(context)))
        callback = EMIT_CALLBACK(record)
        result = transition(ctypes.byref(context), physical, pressed, a, b, callback, None)
        if result != 0 or snapshot(context) != original["memory"] or calls != original["calls"]:
            raise AssertionError(f"Control comparison failed at case {counts}, physical={physical}, pressed={pressed}")
        coverage.update(original["visited"])
        for _, event, _ in calls:
            emitted[event] += 1
        counts["sequence_steps" if sequence else "transition"] += 1
        return snapshot(context)

    # Exhaust every immediate mask and logical slot with absent/nonzero actions.
    # All byte values of both action fields are covered, without assuming they
    # are booleans in the saved configuration.
    for logical in range(4):
        for mask in range(256):
            for action1, action2 in ((0, 0), (1, 0), (0, 1), (255, 255)):
                globals_, state, owner = baseline()
                globals_[11] = mask
                globals_[239 + 9 * logical] = action1
                globals_[242 + 9 * logical] = action2
                original = native.execute(globals_, state, owner, logical, 0, immediate=True)
                context = context_from(globals_, state, owner)
                actual = immediate(ctypes.byref(context), logical)
                assert actual == original["result"] and snapshot(context) == original["memory"]
                coverage.update(original["visited"])
                counts["immediate_policy"] += 1
        for value in range(256):
            for action1, action2 in ((value, 0), (1, value)):
                globals_, state, owner = baseline()
                globals_[11] = 0xFF
                globals_[239 + 9 * logical], globals_[242 + 9 * logical] = action1, action2
                original = native.execute(globals_, state, owner, logical, 0, immediate=True)
                context = context_from(globals_, state, owner)
                assert immediate(ctypes.byref(context), logical) == original["result"]
                counts["immediate_policy"] += 1

    # Exercise each transition exit and every flag combination for each slot.
    # Original mapping, MINI mapping, duplicates and missing slots are distinct.
    for mapping in ((4, 3, 1, 0), (0, 1, 2, 3), (0, 0, 0, 0), (255, 255, 255, 255)):
        for physical in range(5):
            for pressed in (0, 1):
                for flags in range(64):
                    globals_, state, owner = baseline(mapping)
                    state[74] = flags & 1
                    state[1567 + physical] = pressed if flags & 2 else 1 - pressed
                    globals_[11] = 0xFF if flags & 4 else 0
                    for logical in range(4):
                        state[932 + logical] = int(bool(flags & 8))
                        state[960 + logical] = int(bool(flags & 16))
                        state[964 + logical] = int(bool(flags & 32))
                        globals_[239 + 9 * logical] = logical + 1
                        globals_[242 + 9 * logical] = logical + 1 if flags & 4 else 0
                        struct.pack_into("<HH", state, 1608 + logical * 2, 0xABCD, 0xABCD)
                    compare(globals_, state, owner, physical, pressed, 0x12345678, 3000)

    # The native repeat window is a signed comparison of a wrapped difference.
    times = (0, 1, 2499, 2500, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF)
    for logical in range(4):
        for now in times:
            for deadline in times:
                for owner in (0, logical + 1, 255):
                    globals_, state, _ = baseline()
                    struct.pack_into("<I", state, 1508, deadline)
                    state[964 + logical] = 1
                    compare(globals_, state, owner, logical, 1, 0xFEDCBA98, now)

    # Randomized initialized RAM exposes accidentally overwritten unrelated
    # fields. Bias the map and flags so most cases enter the interesting paths.
    for case in range(4000):
        globals_, state = bytearray(rng.randbytes(GLOBAL_BYTES)), bytearray(rng.randbytes(STATE_BYTES))
        globals_[116:120] = bytes(rng.randrange(6) for _ in range(4))
        physical, pressed = rng.randrange(5), rng.randrange(2)
        state[74] = int(case % 11 != 0)
        state[1567 + physical] = rng.randrange(2)
        for logical in range(4):
            for offset in (932, 960, 964):
                state[offset + logical] = rng.randrange(2)
            for offset in (239, 242):
                globals_[offset + 9 * logical] = rng.choice((0, 1, 255))
        compare(globals_, state, rng.randrange(6), physical, pressed, rng.getrandbits(32), rng.getrandbits(32))

    # Consecutive edges use the previous output, including delayed/double edges.
    for mode in range(4):
        globals_, state, owner = baseline()
        globals_[11] = 0xF if mode == 1 else 0
        for logical in range(4):
            globals_[239 + 9 * logical] = int(mode > 0)
            globals_[242 + 9 * logical] = int(mode > 1)
        for i in range(512):
            globals_, state, owner = compare(globals_, state, owner, (i // 8) % 4,
                                             i % 2, i * 31, i * 10, sequence=True)

    # New C API validation must be side-effect-free; original unsafe calls are
    # deliberately not executed outside the reconstructed input domain.
    for physical, pressed in ((5, 0), (0xFFFFFFFF, 1), (0, 2), (0, 0xFFFFFFFF)):
        context = context_from(*baseline())
        before, calls = snapshot(context), []
        callback = EMIT_CALLBACK(lambda *_: calls.append(True))
        assert transition(ctypes.byref(context), physical, pressed, 0, 0, callback, None) == -1
        assert snapshot(context) == before and not calls
        counts["invalid_api"] += 1
    callback = EMIT_CALLBACK(lambda *_: None)
    assert transition(None, 0, 0, 0, 0, callback, None) == -1
    counts["invalid_api"] += 1

    # NULL event callbacks are permitted by the new API and must not change
    # transition state. The native action call is still recorded separately.
    memory = baseline()
    context = context_from(*memory)
    original = native.execute(*memory, 0, 1)
    assert transition(ctypes.byref(context), 0, 1, 0, 0, EMIT_CALLBACK(), None) == 0
    assert snapshot(context) == original["memory"]

    missing = sorted(set(native.code) - coverage)
    assert not missing, [hex(address) for address in missing]
    assert all(emitted.values()), emitted
    def digest(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    report = {
        "schema": 1, "result": "pass", "project": "HyperRig",
        "scope": "switch transition function and immediate-action policy; action executor is a recorded boundary",
        "original_image_sha256": "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059",
        "functions": {"transition": {"start": TRANSITION, "end_exclusive": native.transition.end,
                                    "bytes_sha256": hashlib.sha256(native.transition.raw).hexdigest()},
                      "immediate": {"start": IMMEDIATE, "end_exclusive": native.immediate.end,
                                    "bytes_sha256": hashlib.sha256(native.immediate.raw).hexdigest()}},
        "comparisons": counts, "event_counts": emitted,
        "instruction_coverage": {"visited": len(coverage), "decoded": len(native.code), "unvisited": missing},
        "compared": ["all initialized state/global bytes", "repeat owner", "event arguments and state at each callback"],
        "source_sha256": {name: digest(name) for name in (
            "firmware/src/hyperrig_controls.c", "firmware/include/hyperrig/hyperrig_controls.h",
            "tools/control_machine.py", "tools/verify_controls.py", "tools/dot_machine.py",
            "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
            "upstream/pi32v2-isa/isa/pi32v2.toml")},
        "mini_v4_binding": mini_binding,
        "null_callback_state_check": "pass",
        "library_sha256": hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["restricted interpreter semantics", "action-executor side effects are not executed",
                        "no timer worker, scheduler, IRQ concurrency, GPIO or protocol-parser execution",
                        "four logical slots retained; no three-slot bank behavior implemented"],
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "comparisons": counts, "instruction_coverage": report["instruction_coverage"]}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path, help="optional pinned MINI v4 application-area image")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing verification reports; use a new output path")
    verify(args.library, args.output, args.mini_image)
