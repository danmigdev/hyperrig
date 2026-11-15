"""Compare host C against instruction-level execution of original firmware bytes."""
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from dot_machine import DotProgram, ROOT
from head_machine import HeadProgram
from rechannel_machine import RechannelProgram


class HeadState(ctypes.Structure):
    _fields_ = [("history", ctypes.POINTER(ctypes.c_int32)),
                ("ring_frames", ctypes.c_uint32), ("position", ctypes.c_uint32),
                ("weights", ctypes.POINTER(ctypes.c_int16)),
                ("kernel_frames", ctypes.c_uint32), ("shift", ctypes.c_int),
                ("bias", ctypes.c_int64)]


class RechannelState(ctypes.Structure):
    _fields_ = [("history", ctypes.POINTER(ctypes.c_int32)),
                ("ring_frames", ctypes.c_uint32), ("position", ctypes.c_uint32),
                ("weights", ctypes.POINTER(ctypes.c_int16)), ("shift", ctypes.c_uint)]


def verify_rechannel(library, rng):
    program = RechannelProgram()
    function = library.hyperrig_rechannel3_process
    function.argtypes = [ctypes.POINTER(RechannelState), ctypes.POINTER(ctypes.c_int32),
                         ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32]
    function.restype = ctypes.c_int
    cases = []
    digest = hashlib.sha256()
    for shift in range(1, 32):
        cases.append(([-(1 << 31), -3, -1, 0, 1, 3, (1 << 31) - 1],
                      [-32768, -1, 32767], [0] * 399, 68, shift))
    for _ in range(256):
        ring, samples = rng.choice((64, 69, 128, 256)), rng.choice((1, 7, 31, 64))
        history = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(ring * 3)]
        history += history[:192]
        values = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(samples)]
        weights = [rng.randrange(-32768, 32768) for _ in range(3)]
        cases.append((values, weights, history, rng.choice((0, 63, ring - 1)), rng.randrange(1, 32)))

    def compare(values, weights, history, position, shift):
        expected, expected_history, expected_position = program.execute(values, weights, history, position, shift)
        inputs, weights_array = (ctypes.c_int32 * len(values))(*values), (ctypes.c_int16 * 3)(*weights)
        storage = (ctypes.c_int32 * (len(history) + 2))(0x5A5A5A5A, *history, 0x5A5A5A5A)
        history_ptr = ctypes.cast(ctypes.byref(storage, 4), ctypes.POINTER(ctypes.c_int32))
        dry = (ctypes.c_int32 * (len(values) + 2))(*([0x5A5A5A5A] * (len(values) + 2)))
        dry_ptr = ctypes.cast(ctypes.byref(dry, 4), ctypes.POINTER(ctypes.c_int32))
        state = RechannelState(history_ptr, len(history) // 3 - 64, position, weights_array, shift)
        if (function(ctypes.byref(state), inputs, dry_ptr, len(values)) != 0 or
                list(dry)[1:-1] != expected or list(storage)[1:-1] != expected_history or state.position != expected_position):
            raise AssertionError(f"rechannel mismatch at shift={shift}, position={position}")
        if not dry[0] == dry[-1] == storage[0] == storage[-1] == 0x5A5A5A5A:
            raise AssertionError("rechannel wrote outside a buffer")
        digest.update(struct.pack("<" + "i" * len(storage), *storage))
        digest.update(struct.pack("<I", state.position))
        return expected_history, expected_position

    for case in cases:
        compare(*case)
    for _ in range(16):
        history, position = [0] * 399, 0
        weights = [rng.randrange(-32768, 32768) for _ in range(3)]
        for samples in (1, 63, 64, 31, 64):
            values = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(samples)]
            history, position = compare(values, weights, history, position, 15)
    count = len(cases) + 80
    print(f"rechannel3: {count} original-instruction comparisons passed", flush=True)
    return {"name": "rechannel3", "cpu_address": f"0x{program.start:08x}",
            "original_function_sha256": hashlib.sha256(program.raw).hexdigest(),
            "cases": count, "outputs_and_state_sha256": digest.hexdigest()}


def verify_head(library, rng):
    program = HeadProgram()
    function = library.hyperrig_head3_process
    function.argtypes = [ctypes.POINTER(HeadState), ctypes.POINTER(ctypes.c_int32),
                        ctypes.POINTER(ctypes.c_int32), ctypes.c_uint32]
    function.restype = ctypes.c_int
    digest = hashlib.sha256()
    cases = []
    shifts = (1, 7, 15, 23, 30, 31)
    for shift in shifts:
        for bias in (-(1 << 63), -(1 << 31) - 1, -1, 0, 1, 1 << 31, (1 << 63) - 1):
            values = [value for x in (-(1 << 31), -7, -3, -2, -1, 0, 1, 2, 3, 7, (1 << 31) - 1)
                      for value in (x, 0, 0)]
            cases.append((values, [1, 0, 0], [0] * 384, 63, shift, bias))
    for _ in range(192):
        ring = rng.choice((64, 128, 256))
        kernel = rng.choice([n for n in (1, 2, 16, 32, 65) if n <= ring])
        samples = rng.choice((1, 7, 31, 64))
        small = rng.choice((True, False))
        limit = 32 if small else (1 << 31)
        history = [rng.randrange(-limit, limit) for _ in range(ring * 3)]
        history += history[:64 * 3]
        values = [rng.randrange(-limit, limit) for _ in range(samples * 3)]
        weight_limit = 16 if small else (1 << 15)
        weights = [rng.randrange(-weight_limit, weight_limit) for _ in range(kernel * 3)]
        position = rng.choice((0, 63, ring - 1, rng.randrange(ring)))
        bias = rng.randrange(-(1 << 63), 1 << 63) if not small else rng.randrange(-128, 128)
        cases.append((values, weights, history, position, rng.choice(shifts), bias))

    def compare(values, weights, history, position, shift, bias):
        expected, expected_history, expected_position = program.execute(
            values, weights, history, position, shift, bias)
        history_array = (ctypes.c_int32 * len(history))(*history)
        weights_array = (ctypes.c_int16 * len(weights))(*weights)
        input_array = (ctypes.c_int32 * len(values))(*values)
        samples = len(values) // 3
        output_array = (ctypes.c_int32 * (samples + 2))(*([0x5A5A5A5A] * (samples + 2)))
        output_pointer = ctypes.cast(ctypes.byref(output_array, 4), ctypes.POINTER(ctypes.c_int32))
        state = HeadState(history_array, len(history) // 3 - 64, position,
                          weights_array, len(weights) // 3, shift, bias)
        result = function(ctypes.byref(state), input_array, output_pointer, samples)
        actual = list(output_array)[1:-1]
        if (result != 0 or actual != expected or list(history_array) != expected_history or
                state.position != expected_position):
            raise AssertionError(f"head3: output/history/position mismatch, shift={shift}, position={position}")
        if output_array[0] != 0x5A5A5A5A or output_array[-1] != 0x5A5A5A5A:
            raise AssertionError("head3 wrote outside output")
        digest.update(struct.pack("<" + "i" * (samples + len(history)), *actual, *history_array))
        digest.update(struct.pack("<I", state.position))
        return list(history_array), state.position

    for case in cases:
        compare(*case)
    # Stateful calls cross both ring and block boundaries with the same kernel.
    streams, blocks = 24, 7
    for _ in range(streams):
        weights = [rng.randrange(-200, 200) for _ in range(48)]
        history, position = [0] * (192 * 3), 0
        for block in range(blocks):
            samples = (1, 63, 7, 64, 31, 64, 64)[block]
            values = [rng.randrange(-32768, 32768) for _ in range(samples * 3)]
            history, position = compare(values, weights, history, position, 15, -31)
    count = len(cases) + streams * blocks
    print(f"head3: {count} instruction-level comparisons passed (output, history and position)", flush=True)
    return {"name": "head3", "cpu_address": f"0x{program.start:08x}",
            "original_function_sha256": hashlib.sha256(program.raw).hexdigest(),
            "cases": count, "outputs_and_state_sha256": digest.hexdigest()}


def main():
    library = ctypes.CDLL(str(ROOT / "build/native/libhyperrig_dsp.so"))
    rng = random.Random(0x48595045)
    results = []
    total = 0
    for bits in (16, 32):
        program = DotProgram(bits)
        weight_type = ctypes.c_int16 if bits == 16 else ctypes.c_int32
        function = getattr(library, f"hyperrig_dot_i{bits}")
        function.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.c_int,
                            ctypes.POINTER(ctypes.c_int32), ctypes.c_int,
                            ctypes.POINTER(weight_type), ctypes.c_int, ctypes.c_int, ctypes.c_int]
        function.restype = ctypes.c_int
        cases = []
        shifts = [-62, -33, -32, -31, -1, 0, 1, 2, 15, 30, 31, 32, 62]
        # Half-way signs, saturation boundaries and zero-length dot products.
        for shift in shifts:
            for value in [-2147483648, -2147483647, -3, -1, 0, 1, 3, 2147483647]:
                cases.append(([value], [1], 1, 1, 1, shift))
            cases.append(([0], [], 3, 0, 2, shift))
        low, high = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        for _ in range(512):
            samples, taps = rng.randint(1, 5), rng.randint(0, 12)
            ins, outs = rng.randint(1, 4), rng.randint(1, 4)
            values = [rng.randint(-(1 << 31), (1 << 31) - 1)
                      for _ in range(max(1, (samples - 1) * ins + taps))]
            weights = [rng.randint(low, high) for _ in range(taps)]
            cases.append((values, weights, samples, ins, outs, rng.choice(shifts)))
        digest = hashlib.sha256()
        for index, (values, weights, samples, ins, outs, shift) in enumerate(cases):
            original = program.execute(values, weights, samples, ins, outs, shift)
            input_array = (ctypes.c_int32 * len(values))(*values)
            weight_array = (weight_type * max(1, len(weights)))(*weights)
            output_array = (ctypes.c_int32 * (samples * outs))(*([0x5A5A5A5A] * (samples * outs)))
            result = function(output_array, outs, input_array, ins, weight_array, len(weights), samples, shift)
            actual = [output_array[i * outs] for i in range(samples)]
            if result != 0 or original != actual:
                raise AssertionError(f"i{bits} case {index}, shift {shift}: original={original}, C={actual}")
            if any(value != 0x5A5A5A5A for i, value in enumerate(output_array) if i % outs):
                raise AssertionError("C wrote outside output stride")
            digest.update(struct.pack("<" + "i" * samples, *actual))
        results.append({"weights_bits": bits, "cpu_address": f"0x{program.start:08x}",
                        "original_function_sha256": hashlib.sha256(program.raw).hexdigest(),
                        "cases": len(cases), "outputs_sha256": digest.hexdigest()})
        total += len(cases)
        print(f"i{bits}: {len(cases)} instruction-level comparisons passed", flush=True)
    head_result = verify_head(library, rng)
    results.append(head_result)
    total += head_result["cases"]
    rechannel_result = verify_rechannel(library, rng)
    results.append(rechannel_result)
    total += rechannel_result["cases"]
    from verify_a2l_native import verify as verify_a2l
    bias_results, loader_result = verify_a2l(library, HeadState, RechannelState)
    results.extend(bias_results)
    total += sum(item["cases"] for item in bias_results)
    total += loader_result["loaded_bias_instruction_comparisons"] + loader_result["loaded_head_instruction_comparisons"]
    total += loader_result["loaded_rechannel_instruction_comparisons"]
    target = (ROOT / "build/native/hyperrig_dsp.pi32v2.o").read_bytes()
    if target[:5] != b"\x7fELF\x01" or target[5] != 1:
        raise ValueError("target object is not little-endian ELF32")
    if int.from_bytes(target[18:20], "little") != 0xF1:
        raise ValueError("target object does not use the JieLi pi32v2 ELF machine ID")
    report = {"sample": "UltraRig alpha11 M5.71 TANK-G v2", "comparisons": total,
              "native_functions": results, "a2l_loader": loader_result,
              "host_undefined_behavior_sanitizer": True,
              "a2l_memory_checks": json.loads((ROOT / "analysis/native/a2l-sanitizers.json").read_text()),
              "pi32v2_object_sha256": hashlib.sha256(target).hexdigest(),
              "elf_machine": int.from_bytes(target[18:20], "little"),
              "reconstruction_source_sha256": {
                  str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted([*(ROOT / "firmware/src").glob("*.c"),
                                      *(ROOT / "firmware/include/hyperrig").glob("*.h")])},
              "hardware_execution_verified": False,
              "limitation": "restricted CPU interpreter; not full DSP or pedal execution"}
    path = ROOT / "analysis/native/verification.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence: {path}")


if __name__ == "__main__":
    main()
