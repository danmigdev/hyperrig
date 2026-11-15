"""Compile and compare MINI codec bus traces offline; never access hardware."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.disassemble import codec, table
from tools.dot_machine import DotMachine, MASK32, signed

GPIO = c.CFUNCTYPE(None, c.c_void_p, c.c_uint, c.c_uint, c.c_uint)
SAMPLE = c.CFUNCTYPE(c.c_int, c.c_void_p, c.c_uint)
DELAY = c.CFUNCTYPE(c.c_int, c.c_void_p, c.c_uint)
SPIN = c.CFUNCTYPE(None, c.c_void_p, c.c_uint32)
U8P = c.POINTER(c.c_uint8)


class Bus(c.Structure):
    _fields_ = [("gpio", GPIO), ("sample", SAMPLE), ("delay", DELAY),
                ("user", c.c_void_p), ("initialized", c.c_uint)]


class Result(c.Structure):
    _fields_ = [("acknowledged", c.c_uint), ("stop_attempted", c.c_uint),
                ("status", c.c_int), ("cleanup_status", c.c_int)]


class Control(c.Structure):
    _fields_ = [("bus", c.POINTER(Bus)), ("map", c.c_uint),
                ("mute_known", c.c_uint), ("mute_shadow", c.c_uint16)]


class Plan(c.Structure):
    _fields_ = [(n, c.c_uint32) for n in ("sample_rate", "mclk_hz", "bclk_hz", "converter_clock_hz")]
    _fields_ += [("osr", c.c_uint), ("records", (c.c_uint8 * 4) * 3)]


class Port(c.Structure):
    _fields_ = [(n, c.c_uint32) for n in ("out", "input", "direction", "digital", "pull_up", "pull_down")]


class Mmio(c.Structure):
    _fields_ = [("porta", c.POINTER(Port)), ("delay_mode", c.POINTER(c.c_uint32)),
                ("system_clock_hz", c.POINTER(c.c_uint32)), ("spin", SPIN), ("spin_user", c.c_void_p)]


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class StockBusProgram:
    """Decode the actual pinned MINI bus functions, retaining predicate metadata."""
    RANGES = ((0x02006960, 0x02006A7C), (0x02006B8C, 0x02006E08))

    def __init__(self):
        raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
        manifest = json.loads((ROOT / "research/input-manifest.json").read_text(encoding="utf-8"))
        check(sha(raw) == manifest["tank_mini"]["sha256"], "unexpected MINI container")
        _, files = unpack_fwsc(raw)
        app, _, _ = unpack_app(files["flash.bin"][0x4000:])
        check(app == (ROOT / "analysis/tank-mini/app_area.dec.bin").read_bytes(), "decoded MINI differs")
        self.app, self.code = app, {}
        self.records = app[0x35E35:0x35E35 + 88]
        check(sha(self.records) == "1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d", "codec table")
        isa = table.load()
        for start, end in self.RANGES:
            cursor = start
            while cursor < end:
                result = codec.decode(isa, app, cursor - 0x02000000)
                check(result is not None, f"undecoded stock opcode {cursor:#x}")
                ins, fields, size = result
                then = otherwise = 0
                if ins.block and "then" in ins.block:
                    def count(kind):
                        name = ins.block[kind]
                        field = ins.fields[name]
                        return fields[name] * field.scale + field.add
                    then, otherwise = count("then"), count("else")
                self.code[cursor] = codec.format(ins, fields), size, then, otherwise
                cursor += size
            check(cursor == end, "bus code boundary")
        # Serial execution is valid only for these independent parallel pairs.
        for pc, (text, size, _, _) in self.code.items():
            if text.endswith("  #"):
                check(text == "r0 = r6  #" and self.code[pc + size][0] == "r1 = [r7+0]", "unexpected parallel pair")
        self.evidence = {
            "original_mini_sha256": sha(raw),
            "codec_table_address": "0x02035e35", "codec_table_sha256": sha(self.records),
            "bus_regions": [{"start": hex(a), "end_exclusive": hex(b),
                             "sha256": sha(app[a - 0x02000000:b - 0x02000000])} for a, b in self.RANGES],
        }


class StockBusMachine(DotMachine):
    """Instruction interpreter with GPIO helper hooks, not a peripheral emulator.

    Signed division, predicate then/else, calls, saves/restores and counted
    loops execute from stock opcodes. Only GPIO helpers are substituted by
    trace operations; helper timing/locks/electrical behavior are not modeled.
    """
    HELPERS = {0x02004F86: 0, 0x02005CA8: 1, 0x02005B16: 2,
               0x02005EAC: 3, 0x02005DA2: 4}

    def __init__(self, program, start, payload=b"", nack=-1, clocks=((0, 8000000),)):
        self.program = program
        self.pc, self.steps, self.carry = start, 0, 0
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(sp=0x30001000, rets=0xFFFFFFFF, r0=0x31000000)
        self.memory, self.trace, self.skips = {}, [], {}
        self.nack, self.ack_index, self.delay_index = nack, 0, 0
        self.clocks, self.selected_clock = clocks, clocks[0][1]
        for i, byte in enumerate(payload):
            self.write(0x31000000 + i, byte, 1)

    def read(self, address, size):
        if address == 0x40200 and size == 4:
            mode, self.selected_clock = self.clocks[self.delay_index % len(self.clocks)]
            self.delay_index += 1
            return mode
        if address == 0x1C1E32C and size == 4:
            return self.selected_clock
        if 0x02000000 <= address and address + size <= 0x02000000 + len(self.program.app):
            offset = address - 0x02000000
            return int.from_bytes(self.program.app[offset:offset + size], "little")
        return super().read(address, size)

    def address(self, expression):
        match = re.fullmatch(r"(r\d+)\+(r\d+)", expression)
        if match:
            return (self.value(match[1]) + self.value(match[2])) & MASK32
        return super().address(expression)

    @staticmethod
    def register_list(text):
        names = []
        for name in text.strip("{}").split(", "):
            match = re.fullmatch(r"r(\d+)-r(\d+)", name)
            if match:
                names.extend(f"r{i}" for i in range(int(match[1]), int(match[2]) - 1, -1))
            else:
                names.append(name)
        return names

    def condition(self, expression):
        match = re.fullmatch(r"\((r\d+) & (r\d+|0x[0-9a-f]+)\) (==|!=) 0", expression)
        if match:
            condition = bool(self.value(match[1]) & self.value(match[2]))
            return condition if match[3] == "!=" else not condition
        match = re.fullmatch(r"(r\d+) (==|!=) (-?\d+)", expression)
        check(match, "unexpected predicate " + expression)
        equal = self.value(match[1]) == self.value(match[3])
        return equal if match[2] == "==" else not equal

    def step(self):
        if self.pc in self.skips:
            self.pc = self.skips.pop(self.pc)
        text, size, then, otherwise = self.program.code[self.pc]
        text = text.removesuffix("  #")
        next_pc = self.pc + size
        if match := re.fullmatch(r"\[--sp\] = (rets|\{.+\})", text):
            names = self.register_list(match[1])
            self.set("sp", self.value("sp") - 4 * len(names))
            for i, name in enumerate(names):
                self.write(self.value("sp") + i * 4, self.value(name), 4)
        elif match := re.fullmatch(r"(pc|\{pc, .+\}) = \[sp\+\+\]", text):
            names = self.register_list(match[1])
            for i, name in enumerate(names):
                value = self.read(self.value("sp") + i * 4, 4)
                if name == "pc":
                    next_pc = value
                else:
                    self.set(name, value)
            self.set("sp", self.value("sp") + 4 * len(names))
        elif match := re.fullmatch(r"call (-?\d+)", text):
            target = next_pc + int(match[1])
            if target in self.HELPERS:
                pin, level = self.value("r0"), self.value("r1")
                check(pin in (1, 2) and level in (0, 1), "unexpected stock GPIO arguments")
                self.trace.append(("gpio", self.HELPERS[target], pin, level))
                self.set("r0", 0)
            elif target == 0x02006AC4:
                check(self.value("r0") == 1, "stock samples a non-SDA pin")
                level = int(self.ack_index == self.nack)
                self.ack_index += 1
                self.trace.append(("sample", 1, level))
                self.set("r0", level)
            else:
                check(target in self.program.code, f"stock escaped to {target:#x}")
                self.set("rets", next_pc)
                next_pc = target
        elif match := re.fullmatch(r"if \((.+)\) \{", text):
            end_then = self.skip(next_pc, then)
            end_else = self.skip(end_then, otherwise)
            if self.condition(match[1]):
                if otherwise:
                    self.skips[end_then] = end_else
            else:
                next_pc = end_then
        elif match := re.fullmatch(r"(r\d+) = (r\d+) / (r\d+) \(s\)", text):
            numerator, denominator = signed(self.value(match[2])), signed(self.value(match[3]))
            check(numerator >= 0 and denominator > 0, "clock outside interpreted domain")
            self.set(match[1], numerator // denominator)
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \(u\)", text):
            self.set(match[1], self.read(self.address(match[2]), 1))
        elif match := re.fullmatch(r"r0 \*= (r\d+)", text):
            multiplier = signed(self.value(match[1]))
            check(multiplier in (-3, -6), "unexpected delay multiplier")
            count = self.value("r0") * -multiplier
            self.trace.append(("delay", count))
            self.set("r0", -count)
        elif text == "nop":
            pass
        else:
            return super().step()
        self.pc = next_pc
        return self.pc != 0xFFFFFFFF

    def run_trace(self):
        while self.pc != 0xFFFFFFFF:
            check(self.pc in self.program.code and self.steps < 3000000, f"stock escaped/budget at {self.pc:#x}")
            self.steps += 1
            if not self.step():
                break
        check(self.value("sp") == 0x30001000 and not self.skips, "stock stack/predicate imbalance")
        return self.trace


class HostBus:
    def __init__(self, lib, nack=-1, clocks=((0, 8000000),), read_error=None,
                 delay_error=-1, persistent_delay_error=False):
        self.trace, self.samples, self.delays = [], 0, 0
        self.callback_errors = []
        self.clocks = clocks
        @GPIO
        def gpio(_user, op, pin, value):
            self.trace.append(("gpio", op, pin, value))
        @SAMPLE
        def sample(_user, pin):
            level = int(self.samples == nack) if read_error is None else read_error
            self.samples += 1
            self.trace.append(("sample", pin, level))
            return level
        @DELAY
        def delay(_user, units):
            index = self.delays
            self.delays += 1
            if index == delay_error or (persistent_delay_error and index > delay_error >= 0):
                self.trace.append(("delay_error", units))
                return -31
            mode, hz = clocks[index % len(clocks)]
            iterations = c.c_uint32(0)
            status = lib.hyperrig_mini_codec_delay_iterations(hz, mode, units, c.byref(iterations))
            if status:
                self.callback_errors.append(status)
                return status
            self.trace.append(("delay", iterations.value))
            return 0
        self.callbacks = gpio, sample, delay
        self.bus = Bus(gpio, sample, delay, None, 0)
        check(lib.hyperrig_mini_codec_bus_init(c.byref(self.bus)) == 0, "host bus init")


def bind_library(library):
    lib = c.CDLL(str(library))
    args = {
        "bus_init": [c.POINTER(Bus)], "write": [c.POINTER(Bus), U8P, c.POINTER(Result)],
        "write_adapter": [c.c_void_p, c.c_uint8, U8P],
        "stock_record": [c.c_uint], "apply_stock": [c.POINTER(Bus), c.POINTER(c.c_uint)],
        "encode": [c.c_uint16, c.c_uint16, U8P],
        "control_init": [c.POINTER(Control), c.POINTER(Bus), c.c_uint],
        "control_apply_stock": [c.POINTER(Control), c.POINTER(c.c_uint)],
        "soft_mute": [c.POINTER(Control), c.c_uint, c.c_uint],
        "plan_128": [c.c_uint32, c.POINTER(Plan)],
        "delay_iterations": [c.c_uint32, c.c_uint32, c.c_uint, c.POINTER(c.c_uint32)],
        "bind_mmio": [c.POINTER(Bus), c.POINTER(Mmio)],
    }
    for name, arguments in args.items():
        getattr(lib, "hyperrig_mini_codec_" + name).argtypes = arguments
    lib.hyperrig_mini_codec_stock_record.restype = U8P
    lib.hyperrig_mini_codec_encode.restype = None
    return lib


def test(library):
    lib, program = bind_library(library), StockBusProgram()
    expected_init = StockBusMachine(program, 0x02006960).run_trace()
    check(HostBus(lib).trace == expected_init, "bus init differs from stock instruction trace")
    check(b"".join(bytes(lib.hyperrig_mini_codec_stock_record(i)[:4]) for i in range(22)) == program.records,
          "C codec table differs from pinned table")
    check(not lib.hyperrig_mini_codec_stock_record(22), "out-of-bounds stock table")
    rng = random.Random(0x434F4445)
    records = [program.records[i:i + 4] for i in range(0, 88, 4)]
    # Every possible byte is transmitted in each payload position.
    records += [bytes((i, i ^ 0xA5, (i + 71) & 255, 255 - i)) for i in range(256)]
    digest = hashlib.sha256()
    trace_cases = 0
    schedules = (((0, 8000000),), ((1, 16000000),), ((0xA4, 11999999), (0xA5, 24000001)))
    for index, record in enumerate(records):
        clocks = schedules[index % len(schedules)]
        host = HostBus(lib, clocks=clocks)
        payload, result = (c.c_uint8 * 4).from_buffer_copy(record), Result()
        check(lib.hyperrig_mini_codec_write(c.byref(host.bus), payload, c.byref(result)) == 0, "ACK transaction")
        expected = StockBusMachine(program, 0x02006DCE, record, clocks=clocks).run_trace()
        check(host.trace == expected_init + expected, f"trace mismatch for record {record.hex()}")
        check(bytes(payload) == record and tuple(getattr(result, n) for n, _ in Result._fields_) == (5, 1, 0, 0),
              "transaction result/payload mutation")
        check(not host.callback_errors, "unexpected delay callback error")
        digest.update(json.dumps(host.trace, separators=(",", ":")).encode())
        trace_cases += 1
    # NACK at each address/payload byte. Stock omits STOP; the new driver adds
    # exactly a stock STOP and reports how many bytes were acknowledged.
    nack_cases = 0
    expected_stop = StockBusMachine(program, 0x02006D3A).run_trace()
    for record in records[:22]:
        for nack in range(5):
            host = HostBus(lib, nack=nack)
            payload, result = (c.c_uint8 * 4).from_buffer_copy(record), Result()
            check(lib.hyperrig_mini_codec_write(c.byref(host.bus), payload, c.byref(result)) == -2, "NACK status")
            original = StockBusMachine(program, 0x02006DCE, record, nack=nack).run_trace()
            check(host.trace == expected_init + original + expected_stop, "NACK cleanup trace")
            check((result.acknowledged, result.stop_attempted, result.cleanup_status, host.samples) ==
                  (nack, 1, 0, nack + 1) and host.bus.initialized, "NACK continuation/result")
            nack_cases += 1
    host, complete = HostBus(lib), c.c_uint(999)
    check(lib.hyperrig_mini_codec_apply_stock(c.byref(host.bus), c.byref(complete)) == 0 and complete.value == 22,
          "stock replay")
    check(host.trace == StockBusMachine(program, 0x02006DEC).run_trace(), "full 22-record trace")
    for nack in range(110):
        host, complete = HostBus(lib, nack=nack), c.c_uint(999)
        check(lib.hyperrig_mini_codec_apply_stock(c.byref(host.bus), c.byref(complete)) == -2, "replay error")
        check(complete.value == nack // 5 and host.samples == nack + 1, "replay must stop at first NACK")

    # Errors at every timing phase, including ACK release and STOP itself.
    payload = (c.c_uint8 * 4)(0x00, 0x31, 0x10, 0x04)
    for failure in range(147):
        host, result = HostBus(lib, delay_error=failure), Result()
        check(lib.hyperrig_mini_codec_write(c.byref(host.bus), payload, c.byref(result)) == -31, "delay error propagation")
        check(result.stop_attempted and not host.bus.initialized, "timing failure must invalidate bus")
        check(host.trace[-2] == ("gpio", 0, 1, 1), "cleanup must restore SDA high")
    host, result = HostBus(lib, nack=0, delay_error=32, persistent_delay_error=True), Result()
    check(lib.hyperrig_mini_codec_write(c.byref(host.bus), payload, c.byref(result)) == -2 and
          result.cleanup_status == -31 and not host.bus.initialized, "keep NACK and failed STOP distinct")
    for level in (-77, 7):
        host, result = HostBus(lib, read_error=level), Result()
        check(lib.hyperrig_mini_codec_write(c.byref(host.bus), payload, c.byref(result)) == (level if level < 0 else -5),
              "read failure status")
        check(host.samples == 1 and not host.bus.initialized, "read failure continuation")
    host = HostBus(lib)
    previous = list(host.trace)
    host.bus.initialized = 0
    check(lib.hyperrig_mini_codec_write(c.byref(host.bus), payload, None) == -4, "uninitialized write")
    check(lib.hyperrig_mini_codec_write_adapter(c.byref(host.bus), 0x1B, payload) == -1, "7-bit address confused with wire byte")
    check(lib.hyperrig_mini_codec_write(None, payload, None) == -1 and
          lib.hyperrig_mini_codec_write(c.byref(host.bus), None, None) == -1 and host.trace == previous,
          "invalid call touched bus")

    delay_cases = 0
    for hz in (0, 1, 3999999, 4000000, 7999999, 8000000, 11999999, 24000000,
               48000000, 96000000, 240000000, 320000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        for mode in (0, 1, 0xA4, 0xA5):
            for units in (0, 3, 6, 9):
                out = c.c_uint32(0x12345678)
                divisor = 8000000 if mode & 1 else 4000000
                valid = divisor <= hz <= 0x7FFFFFFF and units in (3, 6)
                result = lib.hyperrig_mini_codec_delay_iterations(hz, mode, units, c.byref(out))
                check(result == (0 if valid else -3), "delay domain")
                check(out.value == ((hz // divisor) * units if valid else 0x12345678), "delay count/error mutation")
                delay_cases += 1

    # Shadow MMIO verifies preservation of non-bus pins and absence of writes
    # on binding. Changes of clock/mode are re-read on each individual wait.
    mmio_cases = 0
    for _ in range(128):
        port = Port(*(rng.getrandbits(32) for _ in Port._fields_))
        before = {name: getattr(port, name) for name, _ in Port._fields_}
        mode, hz, spins = c.c_uint32(0), c.c_uint32(24000000), []
        @SPIN
        def spin(_user, iterations):
            spins.append(iterations)
        mmio, bus = Mmio(c.pointer(port), c.pointer(mode), c.pointer(hz), spin, None), Bus()
        check(lib.hyperrig_mini_codec_bind_mmio(c.byref(bus), c.byref(mmio)) == 0 and not bus.initialized,
              "bind MMIO")
        check(all(getattr(port, n) == v for n, v in before.items()) and not spins, "binding touched MMIO")
        check(lib.hyperrig_mini_codec_bus_init(c.byref(bus)) == 0, "MMIO init")
        expected = dict(before, out=before["out"] | 6, direction=before["direction"] & ~6,
                        digital=before["digital"] | 6, pull_up=before["pull_up"] | 6,
                        pull_down=before["pull_down"] & ~6)
        check(all(getattr(port, n) == v for n, v in expected.items()), "GPIO init/preservation")
        for new_mode, new_hz in ((0, 24000000), (1, 24000000), (1, 32000000)):
            mode.value, hz.value = new_mode, new_hz
            check(bus.delay(bus.user, 3) == 0 and spins[-1] == (new_hz // (8000000 if new_mode else 4000000)) * 3,
                  "MMIO delay did not refresh its inputs")
        port.input &= ~2
        check(lib.hyperrig_mini_codec_write(c.byref(bus), payload, None) == 0, "MMIO ACK path")
        check(port.out & 6 == 6 and port.direction & 6 == 0, "MMIO bus idle")
        check(all((getattr(port, n) & ~6) == (v & ~6) for n, v in before.items()), "unrelated GPIO changed")
        mmio_cases += 1

    mute_cases = 0
    for mapping in (0, 1):
        host, control = HostBus(lib), Control()
        check(lib.hyperrig_mini_codec_control_init(c.byref(control), c.byref(host.bus), mapping) == 0, "control init")
        check(lib.hyperrig_mini_codec_soft_mute(c.byref(control), 1, 1) == -4, "mute without known shadow")
        check(lib.hyperrig_mini_codec_control_apply_stock(c.byref(control), None) == 0, "control apply")
        if not mapping:
            previous = list(host.trace)
            check(lib.hyperrig_mini_codec_soft_mute(c.byref(control), 1, 1) == -4 and host.trace == previous,
                  "opaque codec got semantic mute writes")
            continue
        for adc, dac in ((1, 1), (0, 1), (1, 0), (0, 0)):
            previous = len(host.trace)
            expected_value = 0x1004 | (adc << 1) | (dac << 9)
            check(lib.hyperrig_mini_codec_soft_mute(c.byref(control), adc, dac) == 0 and
                  control.mute_shadow == expected_value and control.mute_known, "mute shadow")
            record = struct.pack(">HH", 0x31, expected_value)
            check(host.trace[previous:] == StockBusMachine(program, 0x02006DCE, record).run_trace(), "mute record encoding")
            mute_cases += 1
        for nack in range(5):
            failed = HostBus(lib, nack=nack)
            control.bus = c.pointer(failed.bus)
            control.mute_known = 1
            previous_shadow = control.mute_shadow
            check(lib.hyperrig_mini_codec_soft_mute(c.byref(control), 1, 1) == -2 and
                  not control.mute_known and control.mute_shadow == previous_shadow, "failed mute invalidation")
            previous = len(failed.trace)
            check(lib.hyperrig_mini_codec_soft_mute(c.byref(control), 0, 0) == -4 and
                  len(failed.trace) == previous, "unknown mute shadow reused")
            mute_cases += 1

    plans = []
    for rate in (44100, 48000):
        plan = Plan()
        check(lib.hyperrig_mini_codec_plan_128(rate, c.byref(plan)) == 0, "clock plan")
        check((plan.mclk_hz, plan.bclk_hz, plan.converter_clock_hz, plan.osr) ==
              (256 * rate, 64 * rate, 128 * rate, 128), "clock ratios")
        check(plan.converter_clock_hz <= 6144000 and rate * 256 > 6144000, "stock OSR conflict lost")
        check(bytes(plan.records) == bytes.fromhex("00030050002b0002002c0082"), "derived clock plan records")
        plans.append({"sample_rate": rate, "mclk_hz": plan.mclk_hz, "bclk_hz": plan.bclk_hz,
                      "converter_clock_hz": plan.converter_clock_hz, "hardware_verified": False})
    plan = Plan()
    before = bytes(plan)
    check(lib.hyperrig_mini_codec_plan_128(96000, c.byref(plan)) == -1 and bytes(plan) == before, "unsupported rate mutation")

    report = program.evidence
    report.update(ack_trace_cases=trace_cases, nack_trace_cases=nack_cases,
                  replay_nack_cases=110, timing_error_cases=148, read_error_cases=2,
                  delay_arithmetic_cases=delay_cases, gpio_mmio_cases=mmio_cases, mute_cases=mute_cases,
                  ack_trace_sha256=digest.hexdigest(), decoded_stock_instruction_count=len(program.code),
                  derived_clock_plans=plans)
    return report


def target_metadata(raw):
    check(raw[:6] == b"\x7fELF\x01\x01" and int.from_bytes(raw[18:20], "little") == 0xF1, "not ELF32 pi32v2")
    header = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    sections = [struct.unpack_from("<10I", raw, header[5] + header[10] * i) for i in range(header[11])]
    names_section = sections[header[12]]
    names = raw[names_section[4]:names_section[4] + names_section[5]]
    sizes, text = {}, b""
    for section in sections:
        name = names[section[0]:names.index(0, section[0])].decode()
        if name in (".text", ".rodata", ".bss", ".data"):
            sizes[name] = section[5]
        if name == ".text":
            text = raw[section[4]:section[4] + section[5]]
    undefined = []
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        symbols = raw[strings[4]:strings[4] + strings[5]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name, value, size, info, other, index = struct.unpack_from("<IIIBBH", raw, offset)
            if name and index == 0:
                undefined.append(symbols[name:symbols.index(0, name)].decode())
    return {"sha256": sha(raw), "section_bytes": sizes, "undefined_symbols": undefined}, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-only", action="store_true")
    args = parser.parse_args()
    out = ROOT / "build/mini-codec"
    out.mkdir(parents=True, exist_ok=True)
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    def run(command, **options):
        return subprocess.run(prefix + command, cwd=ROOT, check=True, **options)
    source = "firmware/mini/codec/hyperrig_mini_codec.c"
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/mini/codec"]
    if not args.test_only:
        run(["gcc", *common, "-O2", "-shared", "-fPIC", "-fsanitize=undefined", "-fno-sanitize-recover=all",
             source, "-o", "build/mini-codec/libhyperrig_mini_codec.so"])
        compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
        run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin",
             "-c", source, "-o", "build/mini-codec/hyperrig_mini_codec.pi32v2.o"])
        run([compiler, "-target", "pi32v2", "-mcpu=r3", "-c", "firmware/mini/codec/spin_pi32v2.S",
             "-o", "build/mini-codec/spin_pi32v2.o"])
        run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", source,
             "firmware/mini/codec/tests/sanitize.c", "-o", "build/mini-codec/sanitize"])
        result = run(["build/mini-codec/sanitize"], capture_output=True, text=True)
        (out / "sanitizers.json").write_text(result.stdout, encoding="utf-8", newline="\n")
        if os.name == "nt":
            run(["python3", "tools/verify_mini_codec.py", "--test-only"])
            return
    report = test(out / "libhyperrig_mini_codec.so")
    report["sanitizers"] = json.loads((out / "sanitizers.json").read_text())
    report["target_objects"] = {}
    for name in ("hyperrig_mini_codec.pi32v2.o", "spin_pi32v2.o"):
        metadata, text = target_metadata((out / name).read_bytes())
        check(not metadata["undefined_symbols"], "native codec has unresolved functions")
        report["target_objects"][name] = metadata
        if name == "spin_pi32v2.o":
            isa, offset, decoded = table.load(), 0, []
            while offset < len(text):
                ins, fields, size = codec.decode(isa, text, offset)
                decoded.append(codec.format(ins, fields))
                offset += size
            check(decoded == ["r1 = 0x0 - r1", "goto 4", "nop", "r1 = r1 + 1", "if (r1 != 0) goto -6", "rts"],
                  "native spin is not the expected stock loop body")
            metadata["instructions"] = decoded
    report.update(
        bus={"sda": "PA1", "scl": "PA2", "address_byte": "0x36", "i2c_7bit_address": "0x1b",
             "electrical_mode": "stock drives high/low; releases SDA only for ACK",
             "clock_stretching": False, "multi_master": False,
             "delay_formula": "floor(sys_hz / ((mode40200 & 1) ? 8000000 : 4000000)) * units; units in {3,6}",
             "delay_microseconds_verified": False},
        codec_identity={"register_map_match": "Nuvoton NAU88L21", "physical_identity_verified": False,
                        "distinctive_registers": ["0x34 DACR_CTRL", "0x35 ADC_DGAIN_CTRL1", "0x4b CLASSG_CTRL", "0x7e PGA_GAIN"],
                        "i2s": "slave, I2S, 32-bit words according to matched register map",
                        "stock_adc_osr": 256, "stock_dac_osr": 256,
                        "stock_rate_conflict": "OSR256 at 44100/48000 exceeds published 6144000 Hz converter limit"},
        primary_sources=[
            {"url": "https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.h",
             "sha256": "d6b09cf9face0517f528abd0805091f227001b17e857c5c097ac5b2cea38899c",
             "used_for": "Nuvoton-authored register fields, 16-bit addressing/data, I2S and mute masks"},
            {"url": "https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.c",
             "sha256": "91320977f58094a8dafe1ff31364324349c935f95ce6c5bc898b8f92ebd99309",
             "used_for": "OSR encodings/divisors and maximum converter clock; no Linux driver code copied"},
            {"url": "https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.7.pdf",
             "used_for": "manufacturer section6 pp28-30: MCLK256fs, CLK_ADC<=6.144MHz; revision3.7,2026-02-09"},
            {"url": "https://www.nuvoton.com.cn/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.5.pdf",
             "used_for": "manufacturer section7.3 p34: 7-bit0x1b, MSB-first 16-bit register/value"}],
        deliberate_policy_changes=["STOP attempted on NACK/error", "replay stops at first error",
                                   "zero/negative-equivalent delay clocks rejected", "mute shadow invalidated on failed write"],
        hardware_execution_verified=False, clock_48000_measured=False, analog_mute_verified=False,
        limitations=["physical codec ID/board revision unconfirmed", "GPIO helper timing and locking not emulated",
                     "loop trip counts are not calibrated microseconds", "stock converter-clock discrepancy unresolved",
                     "OSR128 plan changes filters/latency and is never automatically sent",
                     "digital mute ACK does not prove analog output or ramp settling", "no readback or clock stretching"])
    report["sources_sha256"] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                                for p in sorted((ROOT / "firmware/mini/codec").rglob("*")) if p.is_file()}
    report["verifier_sha256"] = sha(Path(__file__).read_bytes())
    (ROOT / "research/mini-codec.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k.endswith("cases") or k == "sanitizers"}, indent=2))
    print("MINI codec component compiled and verified offline; no hardware was accessed.")


if __name__ == "__main__":
    main()
