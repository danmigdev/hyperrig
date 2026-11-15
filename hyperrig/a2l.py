"""A2L1 capture parser reconstructed from the distributed nam2chip.js packer.

Required Notice: Copyright (c) 2026 Manuel Aguirre
https://polyformproject.org/licenses/noncommercial/1.0.0
See third_party/ultrarig/LICENSE.md and docs/PROVENIENZA.md.

Only parses and validates the model; it does not claim to reproduce the
firmware's fixed-point execution or its real-time DSP performance.
"""
import struct
import zlib


def inspect(data: bytes, allow_trailing=False) -> dict:
    offset = 0

    def take(fmt):
        nonlocal offset
        length = struct.calcsize("<" + fmt)
        if offset + length > len(data):
            raise ValueError("truncated A2L model")
        result = struct.unpack_from("<" + fmt, data, offset)
        offset += length
        return result

    magic, version, wbits, abits, rate, layers, channels, head_kernel, fin, fx0, fh, fout, name = take("4sHBBIHBB4b16s")
    if magic != b"A2L1" or version != 1 or wbits != 16 or abits not in (16, 32):
        raise ValueError("unsupported A2L header")
    if not 1 <= layers <= 64 or not 1 <= channels <= 16 or not 1 <= head_kernel <= 64:
        raise ValueError("A2L network dimensions out of bounds")
    rfrac, = take("b")
    rechannel = take(f"{channels}h")
    prev = fx0
    receptive_field = 1
    layers_info = []

    def shift(n):
        if not -62 <= n <= 62:
            raise ValueError("A2L shift outside decoder range")

    shift(rfrac + fin - fx0)
    for _ in range(layers):
        kernel, dilation, fz, fx, slope = take("BHbbi")
        if not 1 <= kernel <= 15 or not dilation:
            raise ValueError("invalid A2L kernel/dilation")
        cf, = take("b")
        conv_w = take(f"{channels * channels * kernel}h")
        conv_b = take(f"{channels}q")
        mf, = take("b")
        mix_w = take(f"{channels}h")
        lf, = take("b")
        linear_w = take(f"{channels * channels}h")
        linear_b = take(f"{channels}q")
        conv_shift = cf + prev - fz
        if not 0 <= conv_shift <= 31:
            raise ValueError("invalid A2L convolution shift")
        for n in (mf + fin - fz, lf + fz - fx, prev - fx, fz - fh):
            shift(n)
        receptive_field += (kernel - 1) * dilation
        layers_info.append({"kernel": kernel, "dilation": dilation, "activation_fraction": fz,
                            "residual_fraction": fx, "slope_q24": slope,
                            "conv_fraction": cf, "mix_fraction": mf, "linear_fraction": lf,
                            "conv_weights": conv_w, "conv_bias": conv_b, "mix_weights": mix_w,
                            "linear_weights": linear_w, "linear_bias": linear_b})
        prev = fx
    head_fraction, = take("b")
    head_weights = take(f"{channels * head_kernel}h")
    head_bias, = take("q")
    if not 0 <= head_fraction + fh - fout <= 31:
        raise ValueError("invalid A2L output shift")
    checksum, = take("I")
    if checksum != zlib.crc32(data[:offset - 4]):
        raise ValueError("A2L CRC32 mismatch")
    if not allow_trailing and offset != len(data):
        raise ValueError("unexpected bytes after A2L model")
    return {"format": "A2L1", "version": version, "bytes": offset,
            "name": name.split(b"\0", 1)[0].decode("utf-8", errors="replace"),
            "sample_rate": rate, "weight_bits": wbits, "activation_bits": abits,
            "layers": layers, "channels": channels, "head_kernel": head_kernel,
            "input_fraction": fin, "initial_residual_fraction": fx0,
            "head_sum_fraction": fh, "output_fraction": fout,
            "rechannel_fraction": rfrac, "rechannel_weights": rechannel,
            "receptive_field": receptive_field + head_kernel - 1,
            "layer_parameters": layers_info, "head_fraction": head_fraction,
            "head_weights": head_weights, "head_bias": head_bias,
            "crc32": f"{checksum:08x}"}
