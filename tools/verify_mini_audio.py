"""Build and check the MINI ALNK component entirely offline; never access hardware."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.disassemble import codec, table

READY = c.CFUNCTYPE(None, c.c_void_p, c.c_uint)
PROCESS = c.CFUNCTYPE(c.c_int, c.c_void_p, c.POINTER(c.c_int32), c.POINTER(c.c_int32), c.c_uint32)
CODEC_WRITE = c.CFUNCTYPE(c.c_int, c.c_void_p, c.c_uint8, c.POINTER(c.c_uint8))


class Alnk(c.Structure):
    _fields_ = [("con0", c.c_uint16), ("reserved0", c.c_uint16), ("con1", c.c_uint16), ("reserved1", c.c_uint16),
                ("con2", c.c_uint8), ("reserved2", c.c_uint8 * 3), ("con3", c.c_uint8), ("reserved3", c.c_uint8 * 3),
                ("adr", c.c_uint32 * 4), ("length", c.c_uint16), ("reserved8", c.c_uint16)]


class Port(c.Structure):
    _fields_ = [(name, c.c_uint32) for name in ("out", "input", "direction", "digital", "pull_up", "pull_down")]


class Device(c.Structure):
    _fields_ = [("alnk", c.POINTER(Alnk)), ("clock", c.POINTER(c.c_uint32)), ("mux", c.POINTER(c.c_uint32)),
                ("porta", c.POINTER(Port)), ("ready", READY), ("user", c.c_void_p),
                ("prepared", c.c_uint), ("configured_rate", c.c_uint32)]


class Readiness(c.Structure):
    _fields_ = [(name, c.c_uint32) for name in ("clock_rate", "codec_rate", "irq_installed", "dma_coherent", "analog_path_ready")]


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def evidence():
    manifest = json.loads((ROOT / "research/input-manifest.json").read_text(encoding="utf-8"))
    raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    check(checksum == manifest["tank_mini"]["sha256"], "Mini sample hash differs")
    _, files = unpack_fwsc(raw)
    app, _, _ = unpack_app(files["flash.bin"][0x4000:])
    check(app == (ROOT / "analysis/tank-mini/app_area.dec.bin").read_bytes(), "decoded Mini image differs")
    isa = table.load()
    # The input fragment is three stock instructions: load, wrapping32 shl8, asr7.
    base, source = 0x01C03A52, 0x0206ED20 - 0x02000000 + 0x3A52
    fragment, decoded, offset = app[source:source + 6], [], 0
    while offset < len(fragment):
        ins, fields, size = codec.decode(isa, fragment, offset)
        decoded.append(codec.format(ins, fields))
        offset += size
    check(decoded == ["r4 = [r5+0]", "r4 = r4 << 8", "r6 = r4 >>> 7"], "stock RX fragment changed")
    config = struct.unpack_from("<24I", app, 0x35E90)
    check(config[:9] == (1, 1, 0, 0x01C1B230, 0, 1, 1, 0x01C1B630, 0x01C03EEE), "channel configuration changed")
    check(config[17:] == (1, 0, 0, 1, 1, 1024, 44100), "common audio configuration changed")
    check(struct.unpack_from("<4I", app, 0x3FED8) == (0x12E10, 0x12E14, 0x12E18, 0x12E1C), "DMA register table")
    records = app[0x35E35:0x35E35 + 88]
    regions = {}
    for name, start, end in (("clock_family_and_rate", 0x02006E36, 0x02006F70),
                              ("configure", 0x02006F70, 0x0200708C),
                              ("configure_channel", 0x0200708C, 0x02007146),
                              ("enable", 0x02007146, 0x0200715C),
                              ("codec_init", 0x02006DCE, 0x02006E08),
                              ("irq", 0x01C0374A, 0x01C037DC)):
        offset = start - 0x02000000 if start >= 0x02000000 else 0x6ED20 + start - 0x01C00000
        regions[name] = {"cpu_start": hex(start), "cpu_end_exclusive": hex(end),
                         "sha256": hashlib.sha256(app[offset:offset + end - start]).hexdigest()}
    return {"original_mini_sha256": checksum, "native_regions": regions,
            "stock_rx_fragment": {"address": hex(base), "bytes": fragment.hex(),
            "sha256": hashlib.sha256(fragment).hexdigest(), "instructions": decoded},
            "configuration_sha256": hashlib.sha256(app[0x35E90:0x35EF0]).hexdigest(),
            "codec_table_sha256": hashlib.sha256(records).hexdigest()}, records


def test(library):
    lib = c.CDLL(str(library))
    u32p, i32p = c.POINTER(c.c_uint32), c.POINTER(c.c_int32)
    for name in ("hyperrig_mini_audio_stock_rx", "hyperrig_mini_audio_rx_q"):
        getattr(lib, name).argtypes = [c.c_uint32] + ([c.c_uint] if name.endswith("_q") else [])
        getattr(lib, name).restype = c.c_int32
    lib.hyperrig_mini_audio_tx_q.argtypes, lib.hyperrig_mini_audio_tx_q.restype = [c.c_int32, c.c_uint], c.c_uint32
    lib.hyperrig_mini_audio_unpack.argtypes = [u32p, c.c_uint, c.c_uint, i32p]
    lib.hyperrig_mini_audio_pack.argtypes = [i32p, c.c_uint, u32p, c.c_uint]
    lib.hyperrig_mini_audio_process_half.argtypes = [u32p, u32p, c.c_uint, c.c_uint, c.c_uint, PROCESS, c.c_void_p]
    lib.hyperrig_mini_audio_prepare.argtypes = [c.POINTER(Device), c.c_uint32, c.c_uint32, c.c_uint32]
    lib.hyperrig_mini_audio_start.argtypes = [c.POINTER(Device), c.POINTER(Readiness)]
    lib.hyperrig_mini_audio_stop.argtypes = [c.POINTER(Device)]
    lib.hyperrig_mini_audio_irq.argtypes = [c.POINTER(Device)]
    lib.hyperrig_mini_codec_replay_stock.argtypes = [CODEC_WRITE, c.c_void_p]
    report, expected_records = evidence()
    rng = random.Random(0x4D494E49)
    digest = hashlib.sha256()
    words = [0, 1, 0x7FFFFF, 0x800000, 0xFFFFFF, 0xFFFFFFFF, 0xAA800000, 0x557FFFFF]
    words += [rng.getrandbits(32) for _ in range(512)]
    for word in words:
        # Execute the verified native instructions in order, with explicit32-bit register width.
        r4 = word
        r4 = (r4 << 8) & 0xFFFFFFFF
        r6 = signed(r4, 32) >> 7
        check(lib.hyperrig_mini_audio_stock_rx(word) == r6, "stock RX instruction mismatch")
        digest.update(struct.pack("<i", r6))
    conversions = 0
    for fraction in range(32):
        for word in words:
            pcm = signed(word & 0xFFFFFF, 24)
            expected = pcm << (fraction - 23) if fraction >= 23 else pcm >> (23 - fraction)
            check(lib.hyperrig_mini_audio_rx_q(word, fraction) == expected, "normalized RX scaling")
            value = signed(word, 32)
            expected_tx = value >> (fraction - 23) if fraction >= 23 else value << (23 - fraction)
            expected_tx = min(0x7FFFFF, max(-0x800000, expected_tx)) & 0xFFFFFF
            check(lib.hyperrig_mini_audio_tx_q(value, fraction) == expected_tx, "normalized TX clipping/scaling")
            conversions += 2

    packing = 0
    for half in (0, 1):
        for fraction in (0, 16, 23, 24, 30, 31):
            rx = (c.c_uint32 * 256)(*[rng.getrandbits(32) for _ in range(256)])
            tx = (c.c_uint32 * 258)(*([0x5A5A5A5A] * 258))
            mono = (c.c_int32 * 66)(*([0x5A5A5A5A] * 66))
            tx_ptr, mono_ptr = c.cast(c.byref(tx, 4), u32p), c.cast(c.byref(mono, 4), i32p)
            check(lib.hyperrig_mini_audio_unpack(rx, half, fraction, mono_ptr) == 0, "unpack")
            expected = [lib.hyperrig_mini_audio_rx_q(rx[half * 128 + i * 2], fraction) for i in range(64)]
            check(list(mono)[1:-1] == expected and mono[0] == mono[-1] == 0x5A5A5A5A, "mono span/left channel")
            check(lib.hyperrig_mini_audio_pack(mono_ptr, fraction, tx_ptr, half) == 0, "pack")
            for i in range(256):
                value = lib.hyperrig_mini_audio_tx_q(expected[(i % 128) // 2], fraction) if i // 128 == half else 0x5A5A5A5A
                check(tx[i + 1] == value, "wrong TX half or stereo placement")
            check(tx[0] == tx[-1] == 0x5A5A5A5A, "TX overflow")
            before = bytes(mono), bytes(tx)
            check(lib.hyperrig_mini_audio_unpack(rx, 2, fraction, mono_ptr) == -1, "invalid half")
            check(lib.hyperrig_mini_audio_pack(mono_ptr, 32, tx_ptr, half) == -1, "invalid fraction")
            check((bytes(mono), bytes(tx)) == before, "invalid conversion wrote data")
            packing += 1
    callbacks = []
    @PROCESS
    def process(_user, input_data, output_data, frames):
        callbacks.append(frames)
        for i in range(frames): output_data[i] = input_data[i]
        return 0
    @PROCESS
    def fail(_user, _input, _output, _frames): return -7
    rx, tx = (c.c_uint32 * 256)(*[rng.getrandbits(32) for _ in range(256)]), (c.c_uint32 * 256)()
    check(lib.hyperrig_mini_audio_process_half(rx, tx, 1, 23, 23, process, None) == 0, "process adapter")
    check(callbacks == [64] and list(tx)[:128] == [0] * 128, "process contract")
    check(list(tx)[128:] == [v for i in range(64) for v in [rx[128 + i * 2] & 0xFFFFFF] * 2], "round trip")
    before = list(tx)
    check(lib.hyperrig_mini_audio_process_half(rx, tx, 0, 30, 31, fail, None) == -7, "DSP error propagation")
    check(list(tx)[:128] == [0] * 128 and list(tx)[128:] == before[128:], "DSP failure half silence")

    ready_events, mmio_cases = [], 0
    @READY
    def ready(_user, half): ready_events.append(half)
    for rate in (44100, 48000):
        for _ in range(128):
            registers = Alnk()
            c.memset(c.byref(registers), 0xA5, c.sizeof(registers))
            registers.con0 = rng.getrandbits(16) & ~0x800
            porta = Port(*[rng.getrandbits(32) for _ in range(6)])
            clock, mux = c.c_uint32(rng.getrandbits(32)), c.c_uint32(rng.getrandbits(32))
            d = Device(c.pointer(registers), c.pointer(clock), c.pointer(mux), c.pointer(porta), ready, None, 0, 0)
            initial = {name: getattr(porta, name) for name, _ in Port._fields_}
            old_clock, old_mux = clock.value, mux.value
            check(lib.hyperrig_mini_audio_prepare(c.byref(d), 0x1C10000, 0x1C10400, rate) == 0, "prepare")
            check((registers.con0, registers.con1, registers.con2, registers.con3, registers.length) ==
                  (0x180, 0xD5, 0, 0x83, 128), "stock register snapshot")
            check(list(registers.adr) == [0x1C10000, 0x1C10400, 0xA5A5A5A5, 0xA5A5A5A5], "DMA addresses/unrelated channels")
            check(registers.reserved0 == registers.reserved1 == registers.reserved8 == 0xA5A5 and
                  list(registers.reserved2) == list(registers.reserved3) == [0xA5] * 3, "MMIO write width")
            expected_port = {"out": initial["out"] | 0xF0, "input": initial["input"],
                             "direction": (initial["direction"] & ~0xF0) | 0x100,
                             "digital": initial["digital"] | 0x100, "pull_up": initial["pull_up"] | 0x100,
                             "pull_down": initial["pull_down"] & ~0x100}
            check(all(getattr(porta, k) == v for k, v in expected_port.items()), "GPIO register preservation")
            check(clock.value == (old_clock & ~0xF00) | (0x500 if rate == 48000 else 0), "clock family")
            check(mux.value == (old_mux & ~0xC0) | 0x40, "pin group")
            prerequisites = Readiness(rate, rate, 1, 1, 1)
            for key, _ctype in Readiness._fields_:
                value = getattr(prerequisites, key)
                setattr(prerequisites, key, 0)
                check(lib.hyperrig_mini_audio_start(c.byref(d), c.byref(prerequisites)) == -1 and registers.con0 == 0x180,
                      "start without actual board readiness")
                setattr(prerequisites, key, value)
            check(lib.hyperrig_mini_audio_start(c.byref(d), c.byref(prerequisites)) == 0 and registers.con0 == 0x980, "enable")
            snapshot = bytes(registers), bytes(d)
            check(lib.hyperrig_mini_audio_prepare(c.byref(d), 0x1C10000, 0x1C10400, rate) == -2, "running reconfiguration")
            check((bytes(registers), bytes(d)) == snapshot, "running reconfiguration changed registers")
            check(lib.hyperrig_mini_audio_stop(c.byref(d)) == 0 and registers.con0 == 0x180, "disable")
            for tx_bus, rx_bus, invalid_rate in ((0x1C10001, 0x1C10400, rate), (0x1C10000, 0x1C10300, rate),
                                                (0xFFFFFFFC, 0x1C10400, rate), (0x1C10000, 0x1C10400, 96000)):
                snapshot = bytes(registers), bytes(porta), clock.value, mux.value, bytes(d)
                check(lib.hyperrig_mini_audio_prepare(c.byref(d), tx_bus, rx_bus, invalid_rate) == -1, "invalid configuration")
                check((bytes(registers), bytes(porta), clock.value, mux.value, bytes(d)) == snapshot, "invalid MMIO mutation")
            mmio_cases += 1
    for pending in range(16):
        for phase in (0, 1):
            ready_events.clear()
            registers.con2, registers.con0 = pending << 4, 0x180 | (phase << 13)
            check(lib.hyperrig_mini_audio_irq(c.byref(d)) == pending, "IRQ pending mask")
            check(ready_events == ([1 - phase] if pending & 2 else []), "RX phase/dispatch")
            check(registers.con2 & 15 == pending, "IRQ acknowledge mask")
    records = []
    @CODEC_WRITE
    def writer(_user, address, record):
        check(address == 0x36, "codec address byte")
        records.append(bytes(record[:4]))
        return 0
    check(lib.hyperrig_mini_codec_replay_stock(writer, None) == 0 and b"".join(records) == expected_records, "codec table order/data")
    failed_writes = []
    @CODEC_WRITE
    def failing_writer(_user, address, record):
        failed_writes.append(bytes(record[:4]))
        return -9 if len(failed_writes) == 7 else 0
    check(lib.hyperrig_mini_codec_replay_stock(failing_writer, None) == -9 and len(failed_writes) == 7, "codec failure continuation")
    report.update(stock_rx_instruction_cases=len(words), normalized_conversion_cases=conversions,
                  dma_half_cases=packing, mmio_snapshot_cases=mmio_cases, irq_phase_cases=32,
                  stock_rx_output_sha256=digest.hexdigest(), codec_records_matched=22,
                  hardware_execution_verified=False, clock_48000_measured=False,
                  limitation="host shadow MMIO is not a cycle-accurate peripheral model; normalized Q/stereo routing is HyperRig policy")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-only", action="store_true")
    args = parser.parse_args()
    out = ROOT / "build/mini-audio"
    out.mkdir(parents=True, exist_ok=True)
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    def run(command, **options):
        return subprocess.run(prefix + command, cwd=ROOT, check=True, **options)
    source = "firmware/mini/audio/hyperrig_mini_audio.c"
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/mini/audio"]
    if not args.test_only:
        run(["gcc", *common, "-O2", "-shared", "-fPIC", "-fsanitize=undefined", "-fno-sanitize-recover=all",
             source, "-o", "build/mini-audio/libhyperrig_mini_audio.so"])
        compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
        run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin",
             "-c", source, "-o", "build/mini-audio/hyperrig_mini_audio.pi32v2.o"])
        run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", source,
             "firmware/mini/audio/tests/sanitize.c", "-o", "build/mini-audio/sanitize"])
        result = run(["build/mini-audio/sanitize"], capture_output=True, text=True)
        (out / "sanitizers.json").write_text(result.stdout, encoding="utf-8", newline="\n")
        if os.name == "nt":
            run(["python3", "tools/verify_mini_audio.py", "--test-only"])
            return
    report = test(out / "libhyperrig_mini_audio.so")
    report["sanitizers"] = json.loads((out / "sanitizers.json").read_text())
    target = (out / "hyperrig_mini_audio.pi32v2.o").read_bytes()
    check(target[:6] == b"\x7fELF\x01\x01" and int.from_bytes(target[18:20], "little") == 0xF1, "pi32v2 ELF target")
    report["pi32v2_object_sha256"] = hashlib.sha256(target).hexdigest()
    report["sources_sha256"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted((ROOT / "firmware/mini/audio").rglob("*")) if p.is_file()}
    report["verifier_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (ROOT / "research/mini-audio-driver.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k.endswith("cases") or k == "sanitizers"}, indent=2))
    print("MINI audio component compiled and verified offline; no hardware was accessed.")


if __name__ == "__main__":
    main()
