"""Check MINI clock plans against stock instructions and primary SDK; offline only."""
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
from hyperrig.jieli import crc16, enc, unpack_app, unpack_fwsc
from verify_mini_platform import decode, StockClockMachine
from pi32v2isa import codec, table

FIRMWARE_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
SDK_COMMIT = "ffbb2a8d925682ba6880d643a83a63ee0691ec09"
SDK_PATH = ROOT / "upstream/ac79-sdk-reference/cpu/wl82/liba/cpu.a"
SDK_SHA = "00cea21d3c8d99487821f2c2b203f2c5a04b2cc8421bc05e9b875a0d70e42c62"
SDK_URL = f"https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/{SDK_COMMIT}/cpu/wl82/liba/cpu.a"
SUPPORTED = (3000, 8000, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000, 88200)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class Plan(c.Structure):
    _fields_ = [(x, c.c_uint32) for x in "clk_con2 con3 selected_label used_stock_fallback".split()]


class Snapshot(c.Structure):
    _fields_ = [(x, c.c_uint32) for x in "clk_con2 pll_con0 pll_con1 alnk_con0 alnk_con3".split()]


class Audit(c.Structure):
    _fields_ = [(x, c.c_uint32) for x in "flags nominal_numerator mclk_denominator lrck_denominator expected_pll_output_mask observed_pll_output_mask".split()]


class Measurement(c.Structure):
    _fields_ = [(x, c.c_uint32) for x in "lrck_millihz bclk_hz mclk_hz uncertainty_ppm".split()]


class StockRateMachine(StockClockMachine):
    """Only 0x02006e36..6f6e; memory-backed clock/ALNK, no hardware model."""
    def __init__(self, program, app, rate, slave, clk, con3):
        self.program, self.app = program, app
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(r0=rate & 0xffffffff, rets=0xffffffff)
        self.memory, self.skip_else, self.saved_returns = {}, {}, []
        self.pc, self.steps, self.carry = 0x02006e58, 0, 0
        self.trace, self.recording = [], False
        self.write(0x10014, clk, 4)
        self.write(0x12e0c, con3, 1)
        self.write(0x1c1b1b8, 0x30000000, 4)
        self.write(0x30000000 + 72, slave, 4)
        self.recording = True

    def write(self, address, value, width):
        if getattr(self, "recording", False):
            check((address, width) in ((0x10014, 4), (0x12e0c, 1)), "unexpected stock MMIO write")
            self.trace.append([hex(address), width, value & ((1 << (width * 8)) - 1)])
        super().write(address, value, width)

    def single(self):
        instruction, size, _, _ = self.program.code[self.pc]
        next_pc = self.pc + size
        if instruction == "[--sp] = rets":
            self.saved_returns.append(self.regs["rets"])
        elif instruction == "pc = [sp++]":
            self.pc = self.saved_returns.pop()
            return
        elif instruction == "rts":
            self.pc = self.regs["rets"]
            return
        elif match := re.fullmatch(r"call (-?\d+)", instruction):
            self.regs["rets"] = next_pc
            self.pc = next_pc + int(match[1])
            check(self.pc == 0x02006e36, "unexpected rate helper call")
            return
        elif match := re.fullmatch(r"(r\d+) \|= (r\d+|\d+)", instruction):
            self.set(match[1], self.value(match[1]) | self.value(match[2]))
        elif match := re.fullmatch(r"(r\d+) = (r\d+) \| (0x[0-9A-Fa-f]+)", instruction):
            self.set(match[1], self.value(match[2]) | int(match[3], 0))
        else:
            super().single()
            return
        self.pc = next_pc

    def run(self):
        while self.pc != 0xffffffff:
            check(self.pc in self.program.code and self.steps < 100, "rate interpreter escaped")
            check(not self.program.code[self.pc][0].endswith("  #"), "unexpected parallel rate instruction")
            self.single()
            self.steps += 1
        check(not self.saved_returns, "unbalanced stock return stack")
        return self.read(0x10014, 4), self.read(0x12e0c, 1)


def stock_evidence():
    firmware = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
    check(sha(firmware) == FIRMWARE_SHA, "unexpected MINI firmware")
    _, files = unpack_fwsc(firmware)
    flash = files["flash.bin"]
    _, _, payloads = unpack_app(flash[0x4000:0x82000])
    app = payloads["app.bin"]
    # Fixed geometry is independently established by verify_mini_handover.py.
    # Pin the bytes here too, so the clock evidence needs no generated report.
    boot = enc(flash[0xb0:0x38d0])
    config = flash[0x38d0:0x3b8b]
    check(sha(boot) == "fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d", "stock boot payload changed")
    check(sha(config) == "0952afd96f533dd0fba72a8fab9cb4a4336f55424a1a89eecb13ff8a51a0eff0" and
          crc16(config) == 0x70d5, "stock clock profile changed")
    boot_isa = table.load()
    for address, expected in ((0x01c04304, "if (r0 != 3) goto 18"),
                              (0x01c0434e, "r4 = 1062219776"),
                              (0x01c0435a, "[r3+4] = r1"),
                              (0x01c0438a, "[r3+0] |= 0x1"),
                              (0x01c04394, "[r3+0] |= 0x2")):
        item = codec.decode(boot_isa, boot, address - 0x01c02000)
        check(item is not None and codec.format(item[0], item[1]) == expected, "boot PLL path changed")
    regions = {
        "alnk_rate": (0x02006e36, 0x02006f70),
        "codec_record_init": (0x02006dec, 0x02006e08),
        "audio_startup": (0x0200717c, 0x02007244),
        "initial_gain_countdown": (0x01c03ade, 0x01c03b18),
        "clock_read_decode": (0x02002d76, 0x02002ec8),
        "clock_post_decode": (0x02002ec8, 0x020030b0),
        "power_path_clock_switch": (0x01c03296, 0x01c033ec),
    }
    fingerprints = {}
    for name, (start, end) in regions.items():
        offset = start - 0x02000120 if start >= 0x02000120 else 0x6ec00 + start - 0x01c00000
        fingerprints[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": sha(app[offset:offset + end - start])}
    init = decode(app, 0x0200717c, 0x02007244)
    check(init.code[0x020071b4][0] == "r0 = 29473360", "countdown address changed")
    check(init.code[0x020071ba][0] == "r1 = 44118", "countdown constant changed")
    check(init.code[0x020071c0][0] == "[r0+0] = r1", "countdown store changed")
    countdown = decode(app, 0x01c03ade, 0x01c03b18)
    check(countdown.code[0x01c03af4][0] == "r1 += -64", "countdown is not a rate register")
    check(countdown.code[0x01c03af8][0] == "r0 = 0", "initial gain hold changed")
    # Verify PA9 order directly from decoded boot instructions, without calling
    # either the GPIO helper or the audio initialization.
    for pc, text in ((0x02007214, "r0 = 9"), (0x02007216, "r1 = 0"),
                     (0x0200723a, "r0 = 9"), (0x0200723c, "r1 = 1")):
        check(init.code[pc][0] == text, "PA9 startup sequence changed")
    records = app[0x02035e35 - 0x02000120:0x02035e35 - 0x02000120 + 88]
    decoded_records = [struct.unpack_from(">HH", records, i) for i in range(0, 88, 4)]
    check(sha(records) == "1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d", "codec records changed")
    check({r: v for r, v in decoded_records if r in (3, 0x2b, 0x2c)} == {3: 0, 0x2b: 3, 0x2c: 0x81}, "stock OSR fields changed")
    # Search call encodings at every halfword, then require matching targets.
    # This includes data/immediate candidates and is not a reachability proof.
    targets = {0x02006dce: [], 0x02006dec: [], 0x02006e58: [], 0x01c03296: []}
    isa = SimpleNamespace(insns=[i for i in table.load().insns if i.syntax.startswith("call ")])
    for base, raw in ((0x02000120, app[:0x6ec00]), (0x01c00000, app[0x6ec00:0x6ec00 + 0xe018])):
        for cursor in range(0, len(raw), 2):
            item = codec.decode(isa, raw, cursor)
            if item is None:
                continue
            instruction, fields, size = item
            if match := re.fullmatch(r"call (-?\d+)", codec.format(instruction, fields)):
                target = base + cursor + size + int(match[1])
                if target in targets:
                    targets[target].append(hex(base + cursor))
    check(targets[0x02006dce] == ["0x2006dfe"], "unexpected direct codec write references")
    check(targets[0x02006dec] == ["0x2007188"], "unexpected direct codec initialization references")
    check(targets[0x02006e58] == ["0x2007086"], "unexpected direct ALNK rate references")
    pointer_refs = {}
    for target in (0x02006dce, 0x02006dec):
        needle = struct.pack("<I", target)
        positions = [hex(0x02000120 + i) for i in range(len(app) - 3) if app[i:i+4] == needle]
        pointer_refs[hex(target)] = positions
        check(not positions, "unexpected absolute codec function pointer")
    return app, {
        "stock_sha256": FIRMWARE_SHA, "stock_application_sha256": sha(app),
        "boot_clock_evidence": {
            "boot_payload_sha256": sha(boot), "boot_payload_bytes": len(boot),
            "configuration_sha256": sha(config), "configuration_crc16": "70d5",
            "profile": {"OSC": "OSC0", "OSC_FREQ": 24000000, "SYS_CLK": 360000000,
                        "HSB_DIV": 1, "LSB_DIV": 2, "ENABLE_SDRAM": 0},
            "main_pll_fragment_start": "0x01c042fc", "main_pll_fragment_end_exclusive": "0x01c04398",
            "main_pll_fragment_sha256": sha(boot[0x22fc:0x2398]),
            "pll_con1_or_mask": "0x3f503000", "pll_con0_enable_mask": "0x3",
            "special_skip_branch_matches_mini_profile": False, "analog_lock_verified": False},
        "native_fragments": fingerprints, "codec_table_sha256": sha(records),
        "direct_call_scan": {hex(k): v for k, v in targets.items()},
        "absolute_codec_pointer_scan": pointer_refs,
        "call_scan_limit": "halfword-aligned call candidates; no reachability proof; excludes computed calls and alternate bus implementations",
        "stock_osr_records": {hex(r): hex(v) for r, v in decoded_records if r in (3, 0x2b, 0x2c)},
        "initial_gain_countdown_samples": 44118,
        "countdown_step_samples": 64,
        "initial_gain_hold_blocks": 690,
        "countdown_is_sample_rate_configuration": False,
        "pa9_startup": {"before_audio": 0, "after_audio": 1, "each_spin_iterations": 100000,
                        "electrical_function_verified": False, "duration_calibrated": False},
    }


def archive_members(data):
    check(data[:8] == b"!<arch>\n", "SDK archive format")
    offset, names, result = 8, b"", {}
    while offset + 60 <= len(data):
        header = data[offset:offset+60]
        size = int(header[48:58])
        name = header[:16].decode().strip()
        member = data[offset+60:offset+60+size]
        check(len(member) == size, "truncated SDK archive member")
        offset += 60 + size + (size & 1)
        if name == "//":
            names = member
        elif name.startswith("/") and name[1:].isdigit():
            name = names[int(name[1:]):].split(b"/\n")[0].decode()
        result[name.rstrip("/")] = member
    return result


def sdk_evidence(out):
    data = SDK_PATH.read_bytes()
    check(sha(data) == SDK_SHA, "SDK cpu.a differs from pinned source; run bootstrap")
    members = archive_members(data)
    ir = (out / "iis.ll").read_text()
    rate = ir.split("define i32 @iis_set_sample_rate(", 1)[1].split("\n}", 1)[0]
    label48 = re.search(r"i32 48000, label %([^\s]+)", rate)[1]
    label44 = re.search(r"i32 44100, label %([^\s]+)", rate)[1]
    rate48 = rate.split("\n" + label48 + ":", 1)[1].split("\n" + label44 + ":", 1)[0]
    check(re.search(r"load volatile i32, i32\* inttoptr \(i32 72100 to i32\*\).*?or i32 %[^,\n]+, 33554432.*?store volatile i32 %[^,\n]+, i32\* inttoptr \(i32 72100 to i32\*\)", rate48, re.S), "SDK 48k PLL output enable evidence changed")
    check("i32 65556 to i32*" in rate48 and re.search(r"or i32 %[^,\n]+, 256", rate48), "SDK ALNK family selector changed")
    # These disabled header enum names corroborate nominal divider arithmetic;
    # they are not elevated to active hardware declarations by this verifier.
    return {"sdk_archive": {"url": SDK_URL, "sha256": SDK_SHA,
                              "members_sha256": {n: sha(members[n]) for n in ("iis.c.o", "clock.c.o")}},
            "sdk_48000_path": {"pll_con1_address": "0x119a4", "or_mask": "0x02000000",
                                "clk_con2_address": "0x10014", "alnk0_select_or": "0x100"},
            "nominal_divider_scope": "clock_hw.h CLOCK_HAL_DEBUG/#if0 enum names, corroborated by stock countdown; not measured",
            "sdk_code_linked_into_hyperrig": False}


def instruction_tests(library, app):
    lib = c.CDLL(str(library))
    lib.hyperrig_mini_clock_stock_plan.argtypes = [c.c_int32, c.c_uint, c.c_uint32, c.c_uint, c.POINTER(Plan)]
    program = decode(app, 0x02006e36, 0x02006f70)
    rng, count, digest = random.Random(0x434c4b), 0, hashlib.sha256()
    rates = list(SUPPORTED) + [-(1 << 31), -1, 0, 1, 96000, (1 << 31) - 1]
    rates += [x + delta for x in SUPPORTED for delta in (-1, 1)]
    traces = {}
    for rate in rates:
        for slave in (0, 1):
            values = range(256) if rate in SUPPORTED else (0, 1, 2, 3, 0x7f, 0x80, 0x83, 0xff)
            for con3 in values:
                clk = rng.getrandbits(32)
                stock = StockRateMachine(program, app, rate, slave, clk, con3)
                expected = stock.run()
                actual = Plan()
                check(lib.hyperrig_mini_clock_stock_plan(rate, slave, clk, con3, c.byref(actual)) == 0, "rate plan rejected")
                check((actual.clk_con2, actual.con3) == expected, f"stock rate mismatch {rate}/{slave}/{con3}")
                check(actual.selected_label == (rate if rate in SUPPORTED else 44100), "rate fallback label")
                check(actual.used_stock_fallback == (rate not in SUPPORTED), "rate fallback reporting")
                digest.update(struct.pack("<iIII", rate, slave, *expected))
                count += 1
        if rate in (44100, 48000):
            stock = StockRateMachine(program, app, rate, 0, 0, 3)
            stock.run()
            traces[str(rate)] = stock.trace
    return {"stock_rate_instruction_cases": count, "stock_rate_instruction_count": len(program.code),
            "stock_rate_result_sha256": digest.hexdigest(), "stock_rate_write_traces": traces}


def measurement_tests(library):
    lib = c.CDLL(str(library))
    lib.hyperrig_mini_clock_measurement_flags.argtypes = [c.c_uint32, c.POINTER(Measurement), c.c_uint32, c.POINTER(c.c_uint32)]
    cases, rng = 0, random.Random(0x4d434c4b)
    examples = []
    for label, fs, bclk, mclk in ((44100, 44100000, 2822400, 11289600),
                                  (44100, 44117647, 2823529, 11294118),
                                  (48000, 48000000, 3072000, 12288000),
                                  (48000, 48076923, 3076923, 12307692)):
        flags = c.c_uint32()
        m = Measurement(fs, bclk, mclk, 5)
        check(lib.hyperrig_mini_clock_measurement_flags(label, c.byref(m), 100, c.byref(flags)) == 0, "measurement rejected")
        examples.append({"label": label, "lrck_millihz": fs, "bclk_hz": bclk, "mclk_hz": mclk,
                         "uncertainty_ppm": 5, "tolerance_ppm": 100, "flags": flags.value,
                         "synthetic_not_measured": True})
    # Independent integer oracle exercises rejected clock relationships and
    # boundaries. No floating-point rounding defines pass/fail.
    for _ in range(2000):
        label = rng.choice((44100, 48000))
        m = Measurement(rng.randrange(1, 192000001), rng.randrange(1, 25000001),
                        rng.randrange(1, 50000001), rng.randrange(100001))
        tolerance, expected = rng.randrange(100001), 0
        def fits(a, b, uncertainty):
            return uncertainty <= tolerance and abs(a - b) * 1000000 <= b * (tolerance - uncertainty)
        if fits(m.lrck_millihz, label * 1000, m.uncertainty_ppm): expected |= 64
        n, d = (160000000, 3328) if label == 48000 else (192000000, 4352)
        if fits(m.lrck_millihz * d, n * 1000, m.uncertainty_ppm): expected |= 128
        if fits(m.mclk_hz * 1000, m.lrck_millihz * 256, m.uncertainty_ppm * 2): expected |= 16
        if fits(m.bclk_hz * 1000, m.lrck_millihz * 64, m.uncertainty_ppm * 2): expected |= 32
        flags = c.c_uint32()
        check(lib.hyperrig_mini_clock_measurement_flags(label, c.byref(m), tolerance, c.byref(flags)) == 0, "measurement bounds")
        check(flags.value == expected, "measurement classification mismatch")
        cases += 1
    return {"measurement_integer_cases": cases, "synthetic_measurement_examples": examples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-only", action="store_true")
    args = parser.parse_args()
    out = ROOT / "build/mini-clock"
    out.mkdir(parents=True, exist_ok=True)
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    def run(command):
        result = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout
    source = "firmware/mini/clock/hyperrig_mini_clock.c"
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/mini/clock"]
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    target = "build/mini-clock/hyperrig_mini_clock.pi32v2.o"
    if not args.test_only:
        archive = SDK_PATH.read_bytes()
        check(sha(archive) == SDK_SHA, "SDK cpu.a hash mismatch")
        members = archive_members(archive)
        for name in ("iis", "clock"):
            (out / (name + ".bc")).write_bytes(members[name + ".c.o"])
            run([vendor + "clang", "-target", "pi32v2", "-S", "-emit-llvm", f"build/mini-clock/{name}.bc", "-o", f"build/mini-clock/{name}.ll"])
        run(["gcc", *common, "-O2", "-shared", "-fPIC", "-fsanitize=undefined", "-fno-sanitize-recover=all",
             source, "-o", "build/mini-clock/libclock.so"])
        run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin",
             "-mllvm", "-pi32v2-large-program", "-c", source, "-o", target])
        check(not run([vendor + "nm", "-u", target]).strip(), "target unresolved symbols")
        run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", source,
             "firmware/mini/clock/test_clock.c", "-o", "build/mini-clock/sanitize"])
        (out / "sanitizers.json").write_text(run(["build/mini-clock/sanitize"]), encoding="utf-8", newline="\n")
        if os.name == "nt":
            print(run(["python3", "tools/verify_mini_clock.py", "--test-only"]), end="")
            return
    app, report = stock_evidence()
    report.update(sdk_evidence(out))
    report.update(instruction_tests(out / "libclock.so", app))
    report.update(measurement_tests(out / "libclock.so"))
    report["sanitizers"] = json.loads((out / "sanitizers.json").read_text())
    report["sanitizers"].update(asan=True, ubsan=True)
    raw = (ROOT / target).read_bytes()
    check(raw[:6] == b"\x7fELF\x01\x01" and int.from_bytes(raw[18:20], "little") == 0xf1, "wrong target ELF")
    elf = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    sections = [struct.unpack_from("<10I", raw, elf[5] + elf[10] * i) for i in range(elf[11])]
    strings = sections[elf[12]]
    names = raw[strings[4]:strings[4] + strings[5]]
    report["target_object"] = {"path": target, "sha256": sha(raw), "undefined_symbols": [],
                               "allocated_section_bytes": {names[s[0]:names.index(0, s[0])].decode(): s[5] for s in sections if s[2] & 2}}
    report["conditional_nominal_rates"] = [
        {"label": 44100, "mclk_numerator": 192000000, "mclk_denominator": 17, "lrck_denominator": 4352,
         "fs_hz": 192000000 / 4352, "difference_ppm": (192000000 / 4352 / 44100 - 1) * 1e6},
        {"label": 48000, "mclk_numerator": 160000000, "mclk_denominator": 13, "lrck_denominator": 3328,
         "fs_hz": 160000000 / 3328, "difference_ppm": (160000000 / 3328 / 48000 - 1) * 1e6},
    ]
    report["codec_findings"] = {
        "physical_identity_verified": False,
        "matching_maps": ["NAU88L21", "NAU88L21C common fields"],
        "both_maps_stock_adc_osr": 256, "both_maps_stock_dac_osr": 256,
        "manufacturer_document_contradiction": "features advertise 48k/OSR256; clock section limits converters to 6.144MHz",
        "later_osr_write_identified": False,
        "candidate_osr64_records_from_stock_shadow": [[3, 160], [43, 1], [44, 128]],
        "candidate_transmitted": False,
        "osr128_at_conditional_48k_converter_hz": 160000000 / 13 / 2,
        "osr64_at_conditional_48k_converter_hz": 160000000 / 13 / 4,
    }
    report["primary_documentary_sources"] = [
        {"url": f"https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/{SDK_COMMIT}/include_lib/driver/cpu/wl82/clock_hw.h",
         "scope": "nominal ALNK divider names in disabled/debug declarations; not active source proof"},
        {"url": "https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.7.pdf",
         "scope": "features 48k/OSR256 and clock-section 6.144MHz ceiling disagree"},
        {"url": "https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.3.pdf",
         "scope": "pp22,59,60: ADC3=256, DAC1=256; ADC1/DAC0=64; p30 converter ceiling"},
        {"url": "https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.c",
         "sha256": "91320977f58094a8dafe1ff31364324349c935f95ce6c5bc898b8f92ebd99309",
         "scope": "Nuvoton-authored OSR/divider mapping and conservative 6.144MHz limit"},
    ]
    report["sources_sha256"] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                                for p in sorted((ROOT / "firmware/mini/clock").glob("*")) if p.is_file()}
    report["verifier_sha256"] = sha(Path(__file__).read_bytes())
    report.update(hardware_executed=False, clock_or_sfc_written=False, codec_written=False,
                  frequency_measured=False, physical_codec_identified=False, audio_readiness_granted=False,
                  limitations=["nominal divider model needs actual clock measurement",
                               "register bits do not prove PLL lock or waveform quality",
                               "countdown corroborates approximately 44118Hz but is not a frequency measurement",
                               "codec identity/revision and datasheet inconsistency unresolved",
                               "PA9 electrical function and delay durations unknown",
                               "candidate OSR64 alters filtering/latency and is never applied automatically",
                               "48k bypass needs IRQ, DMA, clock and analog-path validation before A2"])
    (ROOT / "research/mini-clock.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"stock_rate_instruction_cases": report["stock_rate_instruction_cases"],
                      "measurement_integer_cases": report["measurement_integer_cases"],
                      "sanitizers": report["sanitizers"], "target_object": report["target_object"]}, indent=2))
    print("MINI clock audit verified offline; no clock, codec, or device accessed.")


if __name__ == "__main__":
    main()
