"""Validate the portable C loader and the native parser's arithmetic fragments.

Layout/format checks use the separate Python packer-derived decoder. Bias and
loaded-head comparisons execute pinned original instructions. This does NOT
execute the complete original parser or the missing layer DSP stack.
"""
import ctypes as c
import hashlib
import random
import struct
import zlib

from bias_machine import BiasProgram
from dot_machine import ROOT
from head_machine import HeadProgram
from rechannel_machine import RechannelProgram
from hyperrig.a2l import inspect


class Layer(c.Structure):
    _fields_ = [("dilation", c.c_uint16), ("kernel", c.c_uint8),
                *[(key, c.c_int8) for key in ("activation_fraction", "residual_fraction",
                                             "conv_fraction", "mix_fraction", "linear_fraction")],
                ("slope_q24", c.c_int32),
                *[(key, c.c_int) for key in ("conv_shift", "mix_shift", "linear_shift",
                                            "residual_shift", "sum_shift")],
                *[(key, c.POINTER(c.c_int16)) for key in ("conv_weights", "mix_weights", "linear_weights")],
                ("conv_bias_raw", c.POINTER(c.c_int64)), ("conv_bias", c.POINTER(c.c_int32)),
                ("linear_bias", c.POINTER(c.c_int64))]


class Model(c.Structure):
    _fields_ = [*[(key, c.c_uint8) for key in ("weight_bits", "activation_bits", "channels", "head_kernel")],
                ("layer_count", c.c_uint16),
                *[(key, c.c_uint32) for key in ("sample_rate", "crc32", "receptive_field")],
                *[(key, c.c_int8) for key in ("input_fraction", "initial_residual_fraction", "head_sum_fraction",
                                             "output_fraction", "rechannel_fraction", "head_fraction")],
                ("name", c.c_char * 17), ("rechannel_shift", c.c_int), ("head_shift", c.c_int),
                ("rechannel_weights", c.POINTER(c.c_int16)), ("head_weights", c.POINTER(c.c_int16)),
                ("head_bias_raw", c.c_int64), ("head_bias", c.c_int64),
                ("layers", c.POINTER(Layer)), ("arena_used", c.c_size_t)]


def checked(condition, message):
    if not condition:
        raise AssertionError(message)


def bind(library, head_type, rechannel_type):
    library.hyperrig_a2l_size.argtypes = [c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
    library.hyperrig_a2l_load.argtypes = [c.POINTER(Model), c.c_void_p, c.c_size_t, c.c_void_p, c.c_size_t]
    library.hyperrig_a2l_head3_init.argtypes = [c.POINTER(head_type), c.POINTER(Model), c.POINTER(c.c_int32), c.c_size_t]
    library.hyperrig_a2l_rechannel3_init.argtypes = [c.POINTER(rechannel_type), c.POINTER(Model),
                                                   c.POINTER(c.c_int32), c.c_size_t, c.c_uint32]
    for name in ("hyperrig_a2l_size", "hyperrig_a2l_load", "hyperrig_a2l_head3_init", "hyperrig_a2l_rechannel3_init"):
        getattr(library, name).restype = c.c_int
    library.hyperrig_a2l_bias64.argtypes = library.hyperrig_a2l_bias32.argtypes = [c.c_int64, c.c_uint]
    library.hyperrig_a2l_bias64.restype = c.c_int64
    library.hyperrig_a2l_bias32.restype = c.c_int32


def verify_bias(library, rng):
    results = []
    cases = []
    for shift in range(32):
        values = [-(1 << 63), -(1 << 63) + 1, -(1 << 32), -(1 << 31) - 1,
                  -3, -1, 0, 1, 3, (1 << 31) - 1, 1 << 31, (1 << 32) - 1,
                  (1 << 63) - 2, (1 << 63) - 1]
        if shift:
            half = 1 << (shift - 1)
            values += [-half - 1, -half, -half + 1, half - 1, half, half + 1]
        cases += [(bias, shift) for bias in values]
    cases += [(rng.randrange(-(1 << 63), 1 << 63), rng.randrange(32)) for _ in range(512)]
    for kind, bits in (("head", 64), ("conv", 32)):
        program = BiasProgram(kind)
        function = getattr(library, f"hyperrig_a2l_bias{bits}")
        digest = hashlib.sha256()
        for bias, shift in cases:
            actual, expected = function(bias, shift), program.execute(bias, shift)
            checked(actual == expected, f"{kind} bias mismatch for {bias}, shift={shift}: {actual} != {expected}")
            digest.update(struct.pack("<q", actual))
        results.append({"name": kind + "_bias", "cpu_address": f"0x{program.start:08x}",
                        "cpu_end_exclusive": f"0x{program.end:08x}", "scope": "parser fragment, shifts 0..31",
                        "original_fragment_sha256": hashlib.sha256(program.raw).hexdigest(),
                        "cases": len(cases), "outputs_sha256": digest.hexdigest()})
        print(f"{kind} bias: {len(cases)} original-instruction comparisons passed", flush=True)
    return results


def fixture(rng, channels, layers, kernel, head_kernel, activation_bits=32):
    # Choose fractions before serialization; do not use the C loader to create fixtures.
    data = bytearray(struct.pack("<4sHBBIHBB4b16s", b"A2L1", 1, 16, activation_bits, 48000,
                                 layers, channels, head_kernel, 16, 16, 16, 16, b"HyperRig test"))
    data += struct.pack("<b", 15)

    def weights(count):
        return struct.pack("<" + "h" * count, *[rng.randrange(-32768, 32768) for _ in range(count)])

    def biases(count):
        return struct.pack("<" + "q" * count, *[rng.randrange(-(1 << 63), 1 << 63) for _ in range(count)])

    data += weights(channels)
    for i in range(layers):
        data += struct.pack("<BHbbi", kernel, (1, 17, 65535)[i % 3], 16, 16, -1234567 + i)
        data += struct.pack("<b", i % 32) + weights(channels * channels * kernel) + biases(channels)
        data += struct.pack("<b", -62 if i % 2 else 62) + weights(channels)
        data += struct.pack("<b", 62 if i % 2 else -62) + weights(channels * channels) + biases(channels)
    data += struct.pack("<b", 15) + weights(channels * head_kernel) + biases(1)
    return bytes(data + struct.pack("<I", zlib.crc32(data)))


def verify_loader(library, rng, head_type, rechannel_type):
    embedded = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
    fixtures = [embedded]
    for channels in (1, 2, 3, 16):
        for kernel, head_kernel in ((1, 1), (6, 16), (15, 64)):
            fixtures.append(fixture(rng, channels, 3, kernel, head_kernel,
                                    16 if channels % 2 else 32))
    fixtures.append(fixture(rng, 1, 64, 1, 1))
    conv_program, bias_program, head_program = BiasProgram("conv"), BiasProgram("head"), HeadProgram()
    digest = hashlib.sha256()
    layouts = bias_checks = 0
    loaded_embedded = None
    for data in fixtures:
        expected = inspect(data)
        blob = c.create_string_buffer(data)
        required = c.c_size_t()
        checked(library.hyperrig_a2l_size(blob, len(data), c.byref(required)) == 0, "size query failed")
        for alignment in range(8):
            # 16-byte guard on either side; deliberately exercise unaligned arenas.
            arena = (c.c_ubyte * (required.value + 40))(*([0xA5] * (required.value + 40)))
            start = 16 + alignment
            ptr = c.byref(arena, start)
            model = Model()
            status = library.hyperrig_a2l_load(c.byref(model), ptr, required.value, blob, len(data))
            checked(status == 0, f"load failed: {status}")
            checked(model.arena_used <= required.value, "load exceeded size estimate")
            checked(bytes(arena[:start]) == bytes([0xA5]) * start, "arena underflow")
            checked(bytes(arena[start + model.arena_used:]) == bytes([0xA5]) * (len(arena) - start - model.arena_used),
                    "arena overflow")
            checked(model.name.decode() == expected["name"] and model.layer_count == expected["layers"], "name/layers")
            checked(model.crc32 == int(expected["crc32"], 16), "crc field")
            for key in ("weight_bits", "activation_bits", "channels", "head_kernel", "sample_rate", "receptive_field",
                        "input_fraction", "initial_residual_fraction", "head_sum_fraction", "output_fraction",
                        "rechannel_fraction", "head_fraction"):
                checked(getattr(model, key) == expected[key], key)
            checked(tuple(model.rechannel_weights[:model.channels]) == expected["rechannel_weights"], "rechannel weights")
            checked(model.rechannel_shift == expected["rechannel_fraction"] + expected["input_fraction"] -
                    expected["initial_residual_fraction"], "rechannel shift")
            n, previous = model.channels, expected["initial_residual_fraction"]
            for i, source in enumerate(expected["layer_parameters"]):
                layer = model.layers[i]
                for key in ("kernel", "dilation", "activation_fraction", "residual_fraction", "slope_q24",
                            "conv_fraction", "mix_fraction", "linear_fraction"):
                    checked(getattr(layer, key) == source[key], "layer " + key)
                shifts = (source["conv_fraction"] + previous - source["activation_fraction"],
                          source["mix_fraction"] + expected["input_fraction"] - source["activation_fraction"],
                          source["linear_fraction"] + source["activation_fraction"] - source["residual_fraction"],
                          previous - source["residual_fraction"], source["activation_fraction"] - expected["head_sum_fraction"])
                checked(tuple(getattr(layer, k) for k in ("conv_shift", "mix_shift", "linear_shift", "residual_shift", "sum_shift"))
                        == shifts, "layer shifts")
                previous = source["residual_fraction"]
                for out in range(n):
                    for inp in range(n):
                        for tap in range(layer.kernel):
                            checked(layer.conv_weights[(tap * n + inp) * n + out] ==
                                    source["conv_weights"][(out * n + inp) * layer.kernel + tap], "conv transposition")
                checked(tuple(layer.mix_weights[:n]) == source["mix_weights"], "mix weights")
                checked(c.addressof(layer.mix_weights.contents) == c.addressof(layer.conv_weights.contents) +
                        n * n * layer.kernel * 2, "mix weights must follow conv weights")
                checked(tuple(layer.linear_weights[:n * n]) == source["linear_weights"], "linear weights")
                checked(tuple(layer.conv_bias_raw[:n]) == source["conv_bias"], "conv raw bias")
                checked(tuple(layer.linear_bias[:n]) == source["linear_bias"], "linear raw bias")
                for j in range(n):
                    expected_bias = conv_program.execute(source["conv_bias"][j], layer.conv_shift)
                    checked(layer.conv_bias[j] == expected_bias, "loaded conv bias")
                    digest.update(struct.pack("<i", layer.conv_bias[j]))
                    bias_checks += 1
            for channel in range(n):
                for tap in range(model.head_kernel):
                    checked(model.head_weights[tap * n + channel] == expected["head_weights"][channel * model.head_kernel + tap],
                            "head transposition")
            checked(model.head_shift == expected["head_fraction"] + expected["head_sum_fraction"] - expected["output_fraction"],
                    "head shift")
            checked(model.head_bias_raw == expected["head_bias"], "head raw bias")
            checked(model.head_bias == bias_program.execute(expected["head_bias"], model.head_shift), "head converted bias")
            digest.update(struct.pack("<q", model.head_bias))
            bias_checks += 1
            layouts += 1
            if data is embedded and alignment == 7:
                # Arena objects kept alive; source blob intentionally discarded later.
                loaded_embedded = (model, arena)
                c.memset(blob, 0, len(data))
    model, arena = loaded_embedded
    source = inspect(embedded)
    # Exercise the real A2 head across a ring boundary with independently converted source values.
    raw_weights = source["head_weights"]
    expected_weights = [raw_weights[ch * model.head_kernel + tap] for tap in range(model.head_kernel) for ch in range(3)]
    expected_bias = bias_program.execute(source["head_bias"], model.head_shift)
    history = (c.c_int32 * 386)(*([0x5A5A5A5A] * 386))
    history_ptr = c.cast(c.byref(history, 4), c.POINTER(c.c_int32))
    state = head_type()
    checked(library.hyperrig_a2l_head3_init(c.byref(state), c.byref(model), history_ptr, 384) == 0, "head init")
    expected_history, position = [0] * 384, 0
    for samples in (1, 63, 64, 7, 31):
        values = [rng.randrange(-(1 << 24), 1 << 24) for _ in range(samples * 3)]
        expected_output, expected_history, position = head_program.execute(
            values, expected_weights, expected_history, position, model.head_shift, expected_bias)
        input_array, output_array = (c.c_int32 * len(values))(*values), (c.c_int32 * samples)()
        checked(library.hyperrig_head3_process(c.byref(state), input_array, output_array, samples) == 0, "loaded head process")
        checked(list(output_array) == expected_output and list(history)[1:-1] == expected_history and state.position == position,
                "loaded A2 head differs from original instructions")
        digest.update(struct.pack("<" + "i" * samples, *output_array))
    checked(history[0] == history[-1] == 0x5A5A5A5A, "head history overflow")
    snapshot = bytes(state), bytes(history)
    checked(library.hyperrig_a2l_head3_init(c.byref(state), c.byref(model), history_ptr, 383) == -5, "small head history")
    checked((bytes(state), bytes(history)) == snapshot, "failed head init changed state")
    shift = model.head_shift
    model.head_shift = 0
    checked(library.hyperrig_a2l_head3_init(c.byref(state), c.byref(model), history_ptr, 384) == -4, "zero shift head")
    checked((bytes(state), bytes(history)) == snapshot, "unsupported head changed state")
    model.head_shift = shift
    # Loaded input stage; first A2 layer needs 5 past frames plus a 64-frame block.
    rechannel_program = RechannelProgram()
    ring = (model.layers[0].kernel - 1) * model.layers[0].dilation + 64
    words = (ring + 64) * 3
    rechannel_history = (c.c_int32 * (words + 2))(*([0x5A5A5A5A] * (words + 2)))
    rechannel_ptr = c.cast(c.byref(rechannel_history, 4), c.POINTER(c.c_int32))
    rechannel_state = rechannel_type()
    checked(library.hyperrig_a2l_rechannel3_init(c.byref(rechannel_state), c.byref(model), rechannel_ptr, words, ring) == 0,
            "loaded rechannel init")
    expected_history, position = [0] * words, 0
    for samples in (1, 63, 64, 7, 31):
        values = [rng.randrange(-(1 << 30), 1 << 30) for _ in range(samples)]
        expected_dry, expected_history, position = rechannel_program.execute(
            values, source["rechannel_weights"], expected_history, position, model.rechannel_shift)
        inputs, dry = (c.c_int32 * samples)(*values), (c.c_int32 * samples)()
        checked(library.hyperrig_rechannel3_process(c.byref(rechannel_state), inputs, dry, samples) == 0, "loaded input stage")
        checked(list(dry) == expected_dry and list(rechannel_history)[1:-1] == expected_history and
                rechannel_state.position == position, "loaded input stage differs from original")
        digest.update(struct.pack("<" + "i" * words, *expected_history))
    checked(rechannel_history[0] == rechannel_history[-1] == 0x5A5A5A5A, "loaded rechannel overflow")
    snapshot = bytes(rechannel_state), bytes(rechannel_history)
    for available, frames, error in ((words - 1, ring, -5), (words, ring - 1, -4)):
        checked(library.hyperrig_a2l_rechannel3_init(c.byref(rechannel_state), c.byref(model), rechannel_ptr,
                                                    available, frames) == error, "bad rechannel history accepted")
        checked((bytes(rechannel_state), bytes(rechannel_history)) == snapshot, "failed rechannel init changed state")

    # Corrupt structure while preserving CRC, so checks reach beyond the CRC gate.
    invalid = []
    corrupt = bytearray(embedded)
    corrupt[100] ^= 1
    invalid.append((bytes(corrupt), -3))
    for offset, value, status in ((0, 0, -2), (4, 2, -2), (6, 32, -2), (7, 8, -2),
                                  (12, 0, -4), (12, 65, -4), (14, 0, -4), (14, 17, -4),
                                  (15, 0, -4), (15, 65, -4), (36, 127, -4),
                                  (43, 0, -4), (43, 16, -4), (52, 127, -4),
                                  (4783, 127, -4)):
        corrupt = bytearray(embedded[:-4])
        corrupt[offset] = value
        invalid.append((bytes(corrupt) + struct.pack("<I", zlib.crc32(corrupt)), status))
    # Full truncation sweep, recomputing CRC so truncated readers are exercised.
    for length in range(len(embedded) - 4):
        prefix = embedded[:length]
        invalid.append((prefix + struct.pack("<I", zlib.crc32(prefix)), None))
    extra = embedded[:-4] + b"extra"
    invalid.append((extra + struct.pack("<I", zlib.crc32(extra)), -1))
    for data, expected_status in invalid:
        required = c.c_size_t(0x5A5A5A5A)
        blob = c.create_string_buffer(data)
        status = library.hyperrig_a2l_size(blob, len(data), c.byref(required))
        checked(status != 0 and (expected_status is None or status == expected_status),
                f"invalid model accepted/wrong error: length={len(data)}, status={status}, expected={expected_status}")
        checked(required.value == 0x5A5A5A5A, "failed query changed size")
        destination = Model()
        c.memset(c.byref(destination), 0xA5, c.sizeof(destination))
        storage = (c.c_ubyte * 32)(*([0xA5] * 32))
        before = bytes(destination), bytes(storage)
        checked(library.hyperrig_a2l_load(c.byref(destination), storage, 32, blob, len(data)) == status, "query/load status mismatch")
        checked((bytes(destination), bytes(storage)) == before, "invalid load changed destination")
    # All alignments with exactly one byte less than the measured requirement.
    blob, required = c.create_string_buffer(embedded), c.c_size_t()
    checked(library.hyperrig_a2l_size(blob, len(embedded), c.byref(required)) == 0, "query")
    for alignment in range(8):
        storage = (c.c_ubyte * (required.value + 8))(*([0xA5] * (required.value + 8)))
        destination = Model()
        ptr = c.byref(storage, alignment)
        checked(library.hyperrig_a2l_load(c.byref(destination), ptr, required.value, blob, len(embedded)) == 0, "query alignment")
        actual_bytes = destination.arena_used
        c.memset(storage, 0xA5, len(storage))
        before = bytes(destination), bytes(storage)
        checked(library.hyperrig_a2l_load(c.byref(destination), ptr, actual_bytes - 1, blob, len(embedded)) == -5, "small arena accepted")
        checked((bytes(destination), bytes(storage)) == before, "small arena changed destination")
    print(f"A2L loader: {layouts} layouts, {bias_checks} native bias checks, 5 head + 5 input blocks, "
          f"{len(invalid)} rejected inputs", flush=True)
    return {"fixtures": len(fixtures), "layout_checks": layouts, "loaded_bias_instruction_comparisons": bias_checks,
            "loaded_head_instruction_comparisons": 5, "invalid_inputs_rejected": len(invalid),
            "loaded_rechannel_instruction_comparisons": 5,
            "outputs_sha256": digest.hexdigest(), "embedded_capture_sha256": hashlib.sha256(embedded).hexdigest(),
            "host_abi": {"pointer_bytes": c.sizeof(c.c_void_p), "model_bytes": c.sizeof(Model),
                         "layer_bytes": c.sizeof(Layer), "embedded_arena_bytes": model.arena_used},
            "full_original_parser_emulated": False}


def verify(library, head_type, rechannel_type):
    bind(library, head_type, rechannel_type)
    rng = random.Random(0x41324C31)
    return verify_bias(library, rng), verify_loader(library, rng, head_type, rechannel_type)
