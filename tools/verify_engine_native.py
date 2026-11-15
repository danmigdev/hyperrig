"""Differential layer and complete capture checks against original kernel bytes.

The orchestrator and wrapper/context setup are reconstructed, not emulated.
Each signal-processing stage of the oracle executes its pinned native kernel.
"""
import ctypes as c
import hashlib
import random
import struct
import zlib

from dot_machine import ROOT
from layer_machine import LayerProgram
from bias_machine import BiasProgram
from rechannel_machine import RechannelProgram
from head_machine import HeadProgram
from verify_a2l_native import Model, Layer, checked
from hyperrig.a2l import inspect


class LayerState(c.Structure):
    _fields_ = [("parameters", c.POINTER(Layer)), ("input_history", c.POINTER(c.c_int32)),
                ("input_ring", c.c_uint32), ("input_position", c.c_uint32),
                ("output_history", c.POINTER(c.c_int32)),
                ("output_ring", c.c_uint32), ("output_position", c.c_uint32)]


def bind(library, input_type, head_type):
    class Engine(c.Structure):
        _fields_ = [("model", c.POINTER(Model)), ("layers", c.POINTER(LayerState)),
                    ("input", input_type), ("head", head_type), ("frames", c.c_uint64),
                    ("arena_used", c.c_size_t), ("dry", c.c_int32 * 64), ("sum", c.c_int32 * 192)]
    library.hyperrig_layer3_process.argtypes = [c.POINTER(LayerState), c.POINTER(c.c_int32), c.POINTER(c.c_int32), c.c_uint32]
    library.hyperrig_layer3_process.restype = c.c_int
    library.hyperrig_a2l3_size.argtypes = [c.POINTER(Model), c.POINTER(c.c_size_t)]
    library.hyperrig_a2l3_init.argtypes = [c.POINTER(Engine), c.POINTER(Model), c.c_void_p, c.c_size_t]
    library.hyperrig_a2l3_process.argtypes = [c.POINTER(Engine), c.POINTER(c.c_int32), c.POINTER(c.c_int32), c.c_uint32]
    library.hyperrig_a2l3_reset.argtypes = [c.POINTER(Engine)]
    for name in ("hyperrig_a2l3_size", "hyperrig_a2l3_init", "hyperrig_a2l3_reset", "hyperrig_a2l3_process"):
        getattr(library, name).restype = c.c_int
    return Engine


def guarded(values):
    storage = (c.c_int32 * (len(values) + 2))(0x5A5A5A5A, *values, 0x5A5A5A5A)
    return storage, c.cast(c.byref(storage, 4), c.POINTER(c.c_int32))


def test_layers(library, rng, programs):
    results = []
    for kind, program in programs.items():
        count = 80 if kind == "generic" else 40
        digest = hashlib.sha256()
        for case in range(count):
            k = rng.choice((1, 2, 3, 6, 15)) if kind == "generic" else 15 if "15" in kind else 6
            dilation = rng.choice((1, 3, 17, 67))
            ring, out_ring = (k - 1) * dilation + rng.choice((64, 80)), rng.choice((64, 69, 128))
            position, out_position = rng.choice((0, 63, ring - 1)), rng.choice((0, 63, out_ring - 1))
            samples = rng.choice((1, 2, 7, 31, 64))
            limit = (1 << 31) if case % 2 else 32
            values = lambda n: [rng.randrange(-limit, limit) for _ in range(n)]
            history, out_history = values(ring * 3), values(out_ring * 3)
            history += history[:192]
            out_history += out_history[:192]
            dry, sums = values(samples), values(samples * 3)
            shift = rng.choice((1, 2, 15, 30, 31))
            residual_shift = rng.choice((-31, -2, -1, 0, 1, 2, 31))
            if kind != "generic":
                residual_shift = rng.choice((-31, -2, -1, 1, 2, 31)) if kind.endswith("_shift") else 0
            p = {"kernel": k, "dilation": dilation, "conv_shift": shift, "mix_shift": rng.randrange(shift, 32),
                 "linear_shift": rng.choice((1, 2, 15, 31)), "sum_shift": rng.choice((1, 2, 15, 31)),
                 "residual_shift": residual_shift, "slope_q24": rng.choice((0, 1, 1 << 23, 1 << 24, -(1 << 31), (1 << 31) - 1)),
                 "conv_weights": [rng.randrange(-32768, 32768) for _ in range(k * 9)],
                 "mix_weights": [rng.randrange(-32768, 32768) for _ in range(3)],
                 "conv_bias": values(3), "linear_weights": [rng.randrange(-32768, 32768) for _ in range(9)],
                 "linear_bias": [rng.choice((-(1 << 63), (1 << 63) - 1, rng.randrange(-(1 << 63), 1 << 63))) for _ in range(3)]}
            expected_sum, expected_history, expected_position = program.execute(p, history, position, dry, sums, out_history, out_position)
            layer = Layer()
            keep = []
            for key, value in p.items():
                if isinstance(value, list):
                    typ = c.c_int64 if key == "linear_bias" else c.c_int32 if key == "conv_bias" else c.c_int16
                    array = (typ * len(value))(*value)
                    keep.append(array)
                    setattr(layer, key, array)
                else:
                    setattr(layer, key, value)
            h, hp = guarded(history)
            o, op = guarded(out_history)
            d, dp = guarded(dry)
            s, sp = guarded(sums)
            state = LayerState(c.pointer(layer), hp, ring, position, op, out_ring, out_position)
            checked(library.hyperrig_layer3_process(c.byref(state), dp, sp, samples) == 0, "C layer rejected case")
            checked(list(s)[1:-1] == expected_sum and list(o)[1:-1] == expected_history and
                    state.output_position == expected_position and state.input_position == (position + samples) % ring,
                    f"{kind} case {case}: C differs from original kernel")
            checked(list(h)[1:-1] == history and list(d)[1:-1] == dry, "layer changed input")
            checked(all(a[0] == a[-1] == 0x5A5A5A5A for a in (h, o, d, s)), "layer wrote beyond a buffer")
            before = bytes(state), bytes(o), bytes(s)
            checked(library.hyperrig_layer3_process(c.byref(state), dp, sp, 65) == -1, "oversized layer block accepted")
            checked((bytes(state), bytes(o), bytes(s)) == before, "rejected layer changed state")
            digest.update(struct.pack("<" + "i" * len(expected_sum), *expected_sum))
            digest.update(struct.pack("<" + "i" * len(expected_history), *expected_history))
        print(f"layer {kind}: {count} original-kernel comparisons passed", flush=True)
        results.append({"name": "layer" + kind, "cpu_address": f"0x{program.start:08x}", "cases": count,
                        "original_function_sha256": hashlib.sha256(program.raw).hexdigest(),
                        "outputs_and_state_sha256": digest.hexdigest()})
    return results


def synthetic(rng):
    data = bytearray(struct.pack("<4sHBBIHBB4b16sb3h", b"A2L1", 1, 16, 32, 48000,
                                 3, 3, 4, 24, 24, 20, 24, b"HyperRig test", 12, 4096, -2048, 1024))
    for k, dilation, residual in ((1, 1, 24), (6, 3, 25), (15, 7, 23)):
        data += struct.pack("<BHbbib", k, dilation, 24, residual, 1 << 23, 12)
        data += struct.pack("<" + "h" * (k * 9), *[rng.randrange(-512, 512) for _ in range(k * 9)])
        data += struct.pack("<3qb3hb9h3q", *[rng.randrange(-(1 << 30), 1 << 30) for _ in range(3)],
                            16, 234, -567, 890, 12, *[rng.randrange(-512, 512) for _ in range(9)], 1234567, -2345678, 3456789)
    data += struct.pack("<b12hq", 12, *[rng.randrange(-512, 512) for _ in range(12)], -1234567890)
    return bytes(data + struct.pack("<I", zlib.crc32(data)))


class NativeEngine:
    def __init__(self, data, programs):
        m = inspect(data)
        self.model, self.programs = m, programs
        self.input, self.head = RechannelProgram(), HeadProgram()
        conv_bias, head_bias = BiasProgram("conv"), BiasProgram("head")
        self.parameters, previous = [], m["initial_residual_fraction"]
        for p in m["layer_parameters"]:
            k = p["kernel"]
            shifts = {"conv_shift": p["conv_fraction"] + previous - p["activation_fraction"],
                      "mix_shift": p["mix_fraction"] + m["input_fraction"] - p["activation_fraction"],
                      "linear_shift": p["linear_fraction"] + p["activation_fraction"] - p["residual_fraction"],
                      "sum_shift": p["activation_fraction"] - m["head_sum_fraction"],
                      "residual_shift": previous - p["residual_fraction"]}
            native = dict(p, **shifts)
            native["conv_weights"] = [p["conv_weights"][(out * 3 + inp) * k + tap]
                                      for tap in range(k) for inp in range(3) for out in range(3)]
            native["mix_weights"] = list(p["mix_weights"])
            native["conv_bias"] = [conv_bias.execute(v, shifts["conv_shift"]) for v in p["conv_bias"]]
            self.parameters.append(native)
            previous = p["residual_fraction"]
        self.rings = [(p["kernel"] - 1) * p["dilation"] + 64 for p in self.parameters] + [64]
        self.histories = [[0] * ((ring + 64) * 3) for ring in self.rings]
        self.head_history, self.frames = [0] * 384, 0
        self.head_shift = m["head_fraction"] + m["head_sum_fraction"] - m["output_fraction"]
        self.head_bias = head_bias.execute(m["head_bias"], self.head_shift)
        self.head_weights = [m["head_weights"][ch * m["head_kernel"] + tap] for tap in range(m["head_kernel"]) for ch in range(3)]

    def process(self, values):
        m, n = self.model, len(values)
        dry, self.histories[0], _ = self.input.execute(values, m["rechannel_weights"], self.histories[0],
            self.frames % self.rings[0], m["rechannel_fraction"] + m["input_fraction"] - m["initial_residual_fraction"])
        summed = [0] * (n * 3)
        for i, p in enumerate(self.parameters):
            kind = str(p["kernel"]) + ("_shift" if p["residual_shift"] else "") if p["kernel"] in (6, 15) else "generic"
            summed, self.histories[i + 1], _ = self.programs[kind].execute(
                p, self.histories[i], self.frames % self.rings[i], dry, summed, self.histories[i + 1], self.frames % self.rings[i + 1])
        output, self.head_history, _ = self.head.execute(summed, self.head_weights, self.head_history,
                                                        self.frames % 64, self.head_shift, self.head_bias)
        self.frames += n
        return output, summed


def test_engines(library, rng, engine_type, programs):
    report, comparisons = [], 0
    for data in ((ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes(), synthetic(rng)):
        blob, required, model = c.create_string_buffer(data), c.c_size_t(), Model()
        checked(library.hyperrig_a2l_size(blob, len(data), c.byref(required)) == 0, "model size")
        model_arena = c.create_string_buffer(required.value)
        checked(library.hyperrig_a2l_load(c.byref(model), model_arena, required.value, blob, len(data)) == 0, "model load")
        checked(library.hyperrig_a2l3_size(c.byref(model), c.byref(required)) == 0, "engine size")
        storage = (c.c_ubyte * (required.value + 32))(*([0xA5] * (required.value + 32)))
        engine = engine_type()
        arena = c.byref(storage, 19)  # exercise a deliberately unaligned arena
        checked(library.hyperrig_a2l3_init(c.byref(engine), c.byref(model), arena, required.value) == 0, "engine init")
        initial_size = engine.arena_used
        oracle = NativeEngine(data, programs)
        digest = hashlib.sha256()
        stream = []
        output_stream = []
        for block, samples in enumerate((1, 63, 64, 7, 31, 64)):
            values = [rng.randrange(-(1 << 28), 1 << 28) for _ in range(samples)]
            if not block: values = [0]
            stream += values
            expected, summed = oracle.process(values)
            inputs, output = (c.c_int32 * samples)(*values), (c.c_int32 * samples)()
            checked(library.hyperrig_a2l3_process(c.byref(engine), inputs, output, samples) == 0, "engine process")
            checked(list(output) == expected and list(engine.sum)[:samples * 3] == summed, "complete capture output mismatch")
            output_stream += list(output)
            checked(engine.frames == oracle.frames, "engine frame counter")
            for i, layer in enumerate(engine.layers[:model.layer_count]):
                checked(list(layer.input_history[:len(oracle.histories[i])]) == oracle.histories[i], "input history mismatch")
                checked(list(layer.output_history[:len(oracle.histories[i + 1])]) == oracle.histories[i + 1], "output history mismatch")
                checked(layer.input_position == oracle.frames % oracle.rings[i] and
                        layer.output_position == oracle.frames % oracle.rings[i + 1], "layer position mismatch")
            checked(list(engine.head.history[:384]) == oracle.head_history, "head history mismatch")
            comparisons += model.layer_count + 2
            digest.update(struct.pack("<" + "i" * samples, *output))
            print(f"capture {model.name.decode()} block {block + 1}: all stages/state match", flush=True)
        checked(bytes(storage[:19]) == bytes([0xA5]) * 19 and
                bytes(storage[19 + initial_size:]) == bytes([0xA5]) * (len(storage) - 19 - initial_size), "engine arena overflow")
        # Repartition the same stream and compare output after reset.
        checked(library.hyperrig_a2l3_reset(c.byref(engine)) == 0, "engine reset")
        replay = []
        for start in range(0, len(stream), 17):
            values = stream[start:start + 17]
            inputs, output = (c.c_int32 * len(values))(*values), (c.c_int32 * len(values))()
            checked(library.hyperrig_a2l3_process(c.byref(engine), inputs, output, len(values)) == 0, "replay")
            replay += list(output)
        checked(replay == output_stream, "capture changes with block partitioning/reset")
        before = bytes(engine), bytes(storage)
        checked(library.hyperrig_a2l3_init(c.byref(engine), c.byref(model), arena, initial_size - 1) == -5, "small engine arena accepted")
        checked((bytes(engine), bytes(storage)) == before, "small engine arena changed state")
        saved_bits = model.activation_bits
        model.activation_bits = 16
        checked(library.hyperrig_a2l3_init(c.byref(engine), c.byref(model), arena, required.value) == -4, "unsupported model accepted")
        checked((bytes(engine), bytes(storage)) == before, "unsupported init changed state")
        model.activation_bits = saved_bits
        # Longer than A2's entire 6347-frame receptive field. This is a C-only
        # streaming invariant, explicitly separate from native comparisons.
        long_stream = [rng.randrange(-(1 << 28), 1 << 28) for _ in range(7001)]

        def render(parts):
            checked(library.hyperrig_a2l3_reset(c.byref(engine)) == 0, "long reset")
            rendered, cursor, block = [], 0, 0
            while cursor < len(long_stream):
                values = long_stream[cursor:cursor + parts[block % len(parts)]]
                inputs, output = (c.c_int32 * len(values))(*values), (c.c_int32 * len(values))()
                checked(library.hyperrig_a2l3_process(c.byref(engine), inputs, output, len(values)) == 0, "long process")
                rendered += list(output)
                cursor += len(values)
                block += 1
            checked(engine.frames == len(long_stream), "long frame count")
            return rendered, bytes(storage)

        long_output, long_state = render((64,))
        chunk_output, chunk_state = render((1, 31, 7, 63, 17))
        checked(long_output == chunk_output and long_state == chunk_state, "long stream depends on block partition")
        report.append({"capture": model.name.decode(), "sha256": hashlib.sha256(data).hexdigest(),
                       "layers": model.layer_count, "samples": len(stream), "blocks": 6,
                       "outputs_sha256": digest.hexdigest(), "host_engine_context_bytes": c.sizeof(engine),
                       "host_runtime_arena_bytes": initial_size, "reset_and_block_partition_invariant": True,
                       "long_stream_samples": len(long_stream), "long_stream_partition_invariant": True,
                       "long_stream_outputs_sha256": hashlib.sha256(struct.pack("<" + "i" * len(long_output), *long_output)).hexdigest()})
    return {"captures": report, "original_kernel_invocations": comparisons,
            "scope": "scalar scheduling compared stage-by-stage; original wrapper/RTOS not emulated"}


def verify(library, input_type, head_type):
    engine_type = bind(library, input_type, head_type)
    rng = random.Random(0x4C415945)
    programs = {kind: LayerProgram(kind) for kind in ("generic", "6", "6_shift", "15", "15_shift")}
    results = test_layers(library, rng, programs)
    return results, test_engines(library, rng, engine_type, programs)
