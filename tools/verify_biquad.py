"""Compare reconstructed recursive filters with pinned original instructions."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

from biquad_machine import BiquadProgram
from dot_machine import ROOT

PINNED_IMAGE = "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
MINI_IMAGE = "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
CALLER = (0x01C05280, 0x01C05362)
SOURCES = (
    "firmware/src/hyperrig_biquad.c", "firmware/include/hyperrig/hyperrig_biquad.h",
    "tools/biquad_machine.py", "tools/verify_biquad.py", "tools/build_biquad.py",
    "tools/dot_machine.py", "tests/test_biquad_machine.py", "tests/biquad_sanitize.c",
    "upstream/pi32v2-isa/pi32v2isa/codec.py", "upstream/pi32v2-isa/pi32v2isa/table.py",
    "upstream/pi32v2-isa/isa/pi32v2.toml",
)


class State(ctypes.Structure):
    _fields_ = [("coefficients", ctypes.c_int32 * 5), ("history", ctypes.c_int32 * 4),
                ("residue", ctypes.c_uint32)]


class GuardedState(ctypes.Structure):
    _fields_ = [("before", ctypes.c_uint32), ("state", State), ("after", ctypes.c_uint32)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def state_words(state):
    return [*state.coefficients, *state.history, state.residue]


def ram_bytes(image, start, end):
    offset = 0x02056780 - 0x02000120 + start - 0x01C00000
    return image[offset:offset + end - start]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite an existing verification report")
    library = ctypes.CDLL(str(args.library.resolve()))
    rng = random.Random(0xB128DEC)
    counts, regions, coverage = {}, {}, {}
    digest = hashlib.sha256()
    invalid, empty_null, subdivisions = 0, 0, 0
    for variant in ("rounded", "residual"):
        program = BiquadProgram(variant)
        symbol = "hyperrig_biquad_q28" + ("_residual" if variant == "residual" else "") + "_process"
        function = getattr(library, symbol)
        function.argtypes = [ctypes.POINTER(State), ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32]
        function.restype = ctypes.c_int
        counts[variant] = 0

        def compare(values, initial):
            expected, expected_state = program.execute(values, initial)
            guard = GuardedState(0xC35A17E9, State((ctypes.c_int32 * 5)(*initial[:5]),
                                (ctypes.c_int32 * 4)(*initial[5:9]), initial[9]), 0x91AC572E)
            buffer = (ctypes.c_int32 * (len(values) + 2))(0x5A5A5A5A, *values, 0x5A5A5A5A)
            pointer = ctypes.cast(ctypes.byref(buffer, 4), ctypes.POINTER(ctypes.c_int32))
            status = function(ctypes.byref(guard.state), pointer, len(values))
            actual, actual_state = list(buffer)[1:-1], state_words(guard.state)
            if status != 0 or (actual, actual_state) != (expected, expected_state):
                raise AssertionError((variant, "C/instruction mismatch", values, initial,
                                      actual, expected, actual_state, expected_state))
            if (buffer[0], buffer[-1], guard.before, guard.after) != (0x5A5A5A5A, 0x5A5A5A5A, 0xC35A17E9, 0x91AC572E):
                raise AssertionError("filter wrote outside sample/state buffers")
            if actual_state[:5] != initial[:5] or (variant == "rounded" and actual_state[9] != initial[9]):
                raise AssertionError("immutable coefficients/residue changed")
            digest.update(struct.pack("<" + "I" * (len(actual) + 10),
                                      *[x & 0xFFFFFFFF for x in actual + actual_state]))
            counts[variant] += 1
            return actual, actual_state

        extrema = [-(1 << 31), -(1 << 31) + 1, -(1 << 28), -3, -1, 0, 1, 3,
                   (1 << 28) - 1, 1 << 28, (1 << 31) - 2, (1 << 31) - 1]
        # Every unroll/tail length, both signs of overflow, exact INT32_MIN,
        # and all five independent coefficient positions.
        for length in range(129):
            values = [extrema[i % len(extrema)] for i in range(length)]
            for coefficient in (1 << 28, 1 << 29, -(1 << 29)):
                compare(values, [coefficient, 0, 0, 0, 0, -7, 8, -9, 10, 0x13579BDF])
        for position in range(5):
            for coefficient in extrema:
                coefficients = [0] * 5
                coefficients[position] = coefficient
                compare(extrema, coefficients + [-2147483648, 2147483647, -1, 1, 0xFFFFFFFF])
        for coefficient_count in range(1, 6):
            compare([-(1 << 31)] * 7,
                    [-(1 << 31)] * coefficient_count + [0] * (5 - coefficient_count)
                    + [-(1 << 31)] * 4 + [0])
        for residue in (0, 1, (1 << 27) - 1, 1 << 27, (1 << 28) - 1,
                        1 << 28, (1 << 31), 0xFFFFFFFF):
            compare([1, -1, 3, -3, 0, 7, -7], [1 << 27, 0, 0, 0, 0, 0, 0, 0, 0, residue])
        for _ in range(256):
            length = rng.choice((0, 1, 2, 3, 4, 5, 7, 8, 31, 63, 64, 65, 127, 128))
            limit = rng.choice((8, 1 << 28, 1 << 31))
            values = [rng.randrange(-limit, limit) for _ in range(length)]
            initial = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(9)] + [rng.randrange(1 << 32)]
            compare(values, initial)
        # These cases carry both input/output history and fractional residue
        # across calls; every block is independently compared with instructions.
        for _ in range(24):
            initial = [rng.randrange(-(1 << 28), 1 << 28) for _ in range(9)] + [rng.randrange(1 << 32)]
            values = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(128)]
            whole = compare(values, initial)
            state, joined, cursor = initial, [], 0
            for length in (1, 2, 3, 4, 7, 15, 31, 65):
                output, state = compare(values[cursor:cursor + length], state)
                joined.extend(output)
                cursor += length
                subdivisions += 1
            if (joined, state) != whole:
                raise AssertionError("block subdivision changed output or state")

        original = State((ctypes.c_int32 * 5)(1, 2, 3, 4, 5), (ctypes.c_int32 * 4)(6, 7, 8, 9), 10)
        sentinel = (ctypes.c_int32 * 1)(12345)
        before = bytes(original)
        for state_ptr, sample_ptr, length in ((None, sentinel, 1), (None, None, 0),
                (ctypes.byref(original), None, 1), (ctypes.byref(original), sentinel, 129),
                (ctypes.byref(original), sentinel, 0xFFFFFFFF)):
            if function(state_ptr, sample_ptr, length) != -1 or bytes(original) != before or sentinel[0] != 12345:
                raise AssertionError("invalid API call wrote memory or did not reject")
            invalid += 1
        if function(ctypes.byref(original), None, 0) != 0 or bytes(original) != before:
            raise AssertionError("empty null-buffer call changed state")
        empty_null += 1
        missing = sorted(set(program.code) - program.visited)
        if missing:
            raise AssertionError((variant, "unvisited instructions", [hex(pc) for pc in missing]))
        regions[variant] = {"start": program.start, "end_exclusive": program.end, "bytes_sha256": sha(program.raw)}
        coverage[variant] = {"visited": len(program.visited), "decoded": len(program.code), "unvisited": []}
        print(f"{variant}: {counts[variant]} comparisons; {len(program.visited)} instructions visited", flush=True)

    raw = (ROOT / "analysis/firmware/m571_g_app/app.bin").read_bytes()
    caller = {"start": CALLER[0], "end_exclusive": CALLER[1], "bytes_sha256": sha(ram_bytes(raw, *CALLER)),
              "kind": "static five-section caller trace; not executed by this verifier"}
    mini_binding = None
    if args.mini_image:
        mini = args.mini_image.read_bytes()
        if sha(mini) != MINI_IMAGE:
            raise ValueError("MINI image does not match reviewed v4 reference")
        sys.path.insert(0, str(ROOT))
        from hyperrig.jieli import unpack_app
        mini_raw = unpack_app(mini)[2]["app.bin"]
        for region in [*regions.values(), caller]:
            if sha(ram_bytes(mini_raw, region["start"], region["end_exclusive"])) != region["bytes_sha256"]:
                raise AssertionError("MINI function/caller differs from original")
        mini_binding = {"image_sha256": MINI_IMAGE, "both_kernels_and_caller_byte_identical": True}
    report = {
        "schema": 1, "project": "HyperRig", "result": "pass", "original_image_sha256": PINNED_IMAGE,
        "functions": regions, "representative_caller": caller, "comparisons": counts,
        "total_comparisons": sum(counts.values()), "sequence_block_subset": subdivisions,
        "invalid_api_checks": invalid, "empty_null_buffer_checks": empty_null,
        "instruction_coverage": coverage, "outputs_and_state_sha256": digest.hexdigest(),
        "compared": ["all output samples", "five unchanged coefficient words", "four final history words",
                     "residue word", "guard words around samples and state"],
        "mini_v4_binding": mini_binding, "library_sha256": sha(args.library.read_bytes()),
        "source_sha256": {name: sha((ROOT / name).read_bytes()) for name in SOURCES},
        "hardware_test": False, "audio_test": False, "firmware_changed": False,
        "limitations": ["bounded to 0..128 samples; no coefficient stability or sample-rate guarantee",
                        "caller and coefficient generation remain outside executed scope",
                        "no complete effect, routing, IR or audio scheduler reconstruction",
                        "ABI saved-register frames represented by footprint; private stack not persistent state"],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
