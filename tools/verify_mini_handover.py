"""Audit the MINI stock handover and link all-XIP diagnostic applications.

Only local package bytes, ELF files and compilers are used. No device access,
reset, upload, packaging or flashing. XIP here is an application layout, not
a ROM USB-loader ABI. Cache-array interpretation checks address arithmetic;
it neither models cache hardware nor validates a boot on the MINI.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import crc16, enc, jlfs_entry, unpack_app, unpack_fwsc
from build_mini_boot import StartupMachine, check_dependencies, verify_recorded_hashes
from check_mini_image import inspect_elf
from dot_machine import DotMachine
from pi32v2isa import codec, table

STOCK_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
BOOT_SHA = "fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d"
FLASH_START, FLASH_END = 0x02000120, 0x0207e000
BOOT_LOAD, CACHE_CON = 0x01c02000, 0x01eee008
CACHE_RANGES = [(0x01f00000, 0x01f04000), (0x01f08000, 0x01f0a000),
                (0x01f0a000, 0x01f0a200), (0x01f0b000, 0x01f0b200)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(raw, base, start, end):
    """Decode bounded, independently identified instruction fragments."""
    require(base <= start <= end <= base + len(raw), "instruction range outside binary")
    isa, code, cursor = table.load(), {}, start
    while cursor < end:
        result = codec.decode(isa, raw, cursor - base)
        require(result is not None, f"unknown stock instruction at {cursor:#x}")
        instruction, values, size = result
        require(cursor + size <= end, "fragment ends inside an instruction")
        code[cursor] = (codec.format(instruction, values), size, 0, 0)
        cursor += size
    return SimpleNamespace(start=start, end=end, code=code)


class CacheStoreTrace(DotMachine):
    """Execute the original cache-array clearing loop with bounded word stores.

    CACHE_CON is a supplied word, not an emulated peripheral. Only the address,
    width, order and values of stores are asserted, not their physical effect.
    """
    def __init__(self, program, control):
        self.program, self.pc = program, program.start
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.memory, self.steps, self.carry, self.writes = {}, 0, 0, []
        DotMachine.write(self, CACHE_CON, control, 4)

    def write(self, address, value, size):
        require(size == 4 and address % 4 == 0, "non-word cache-array store")
        require(address == CACHE_CON or any(a <= address < b for a, b in CACHE_RANGES),
                f"unexpected cache clearing address {address:#x}")
        self.writes.append((address, value & 0xffffffff))
        super().write(address, value, size)

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if text == "rts":
            return False
        match = re.fullmatch(r"\[(.+)\] (&=|\|=) (0x[0-9A-F]+)", text)
        if match:
            address, mask = self.address(match[1]), int(match[3], 16)
            value = self.read(address, 4)
            self.write(address, value & mask if match[2] == "&=" else value | mask, 4)
            self.pc += size
            return True
        match = re.fullmatch(r"(r\d+) = (r\d+) \+ (0x[0-9A-F]+)", text)
        if match:
            self.set(match[1], self.value(match[2]) + int(match[3], 16))
            self.pc += size
            return True
        return super().step()

    def run(self, control):
        while self.steps < 20000:
            require(self.pc in self.program.code, "cache trace escaped its fragment")
            self.steps += 1
            if not self.step():
                expected = [(CACHE_CON, control & ~0x300)]
                expected += [(address, 0) for a, b in CACHE_RANGES for address in range(a, b, 4)]
                expected += [(CACHE_CON, control | 0x300)]
                require(self.writes == expected, "stock cache store trace differs")
                return {"instructions_executed": self.steps, "word_stores": len(self.writes),
                        "control_before": control, "control_after": self.read(CACHE_CON, 4),
                        "trace_sha256": sha(b"".join(struct.pack("<II", *w) for w in self.writes))}
        raise ValueError("cache trace instruction budget exceeded")


def stock_evidence(directory):
    package = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
    require(sha(package) == STOCK_SHA, "stock MINI package changed")
    _, files = unpack_fwsc(package)
    flash = files["flash.bin"]
    header = enc(flash[:32])
    require(crc16(header[2:]) == struct.unpack_from("<H", header)[0], "flash header CRC")
    records = {e.name: e for e in (jlfs_entry(enc(flash[o:o + 32]), 0) for o in range(32, 160, 32))}
    entry = records["uboot.boot"]
    require(entry.offset == 0xa0 and entry.size == 0x3830 and entry.flags == 0, "boot directory geometry")
    container = enc(flash[entry.offset:entry.offset + 16]) + enc(flash[entry.offset + 16:entry.offset + entry.size])
    banks, length, load, offset, payload_crc, header_crc = struct.unpack_from("<HHIIHH", container)
    require((banks, length, load, offset) == (1, 0x3820, BOOT_LOAD, 16), "BANKCB geometry")
    boot = container[16:]
    require(crc16(container[:14]) == header_crc and crc16(boot) == payload_crc and
            crc16(container) == entry.data_crc, "BANKCB CRCs")
    require(sha(boot) == BOOT_SHA, "stock bootloader payload changed")
    config_entry = records["isd_config.ini"]
    config = flash[config_entry.offset:config_entry.offset + config_entry.size]
    require(crc16(config) == config_entry.data_crc, "stock plain configuration CRC")
    config_values, cursor = {}, 34
    while cursor < len(config):
        length = config[cursor]
        cursor += 1
        if length in (0, 255):
            break
        end = config.index(0, cursor)
        name = config[cursor:end].decode("ascii")
        cursor = end + 1
        require(cursor + length <= len(config), "truncated configuration value")
        value = config[cursor:cursor + length]
        cursor += length
        if name in ("OSC_FREQ", "SYS_CLK", "HSB_DIV", "LSB_DIV", "ENABLE_SDRAM"):
            require(length == 4, "numeric config width")
            config_values[name] = struct.unpack("<I", value)[0]
        elif name in ("OSC", "SPI"):
            config_values[name] = value.decode("ascii")
    require(config_values == {"OSC_FREQ": 24000000, "SYS_CLK": 360000000, "HSB_DIV": 1,
                              "LSB_DIV": 2, "ENABLE_SDRAM": 0, "OSC": "OSC0", "SPI": "4_1_0_0"},
            "MINI configuration profile changed")
    _, _, app_files = unpack_app(flash[0x4000:0x82000])
    app = app_files["app.bin"]
    require(app == (ROOT / "analysis/tank-mini/app.bin").read_bytes(), "decoded MINI application changed")
    (directory / "stock-uboot.bin").write_bytes(boot)
    regions = {
        "rom_exception_entry": (0x01c02000, 0x01c02046),
        "clear_cache_arrays": (0x01c024e4, 0x01c02532),
        "core_reset": (0x01c028f4, 0x01c028fe),
        "spi_chip_select": (0x01c02ca6, 0x01c02cc6),
        "spi_byte_transactions": (0x01c02cc6, 0x01c02d02),
        "spi_pin_initialization": (0x01c02d32, 0x01c02db4),
        "program_enc_keys": (0x01c032e4, 0x01c032f6),
        "watchdog_disable_at_boot_start": (0x01c0381e, 0x01c0386c),
        "main_pll_configuration": (0x01c042fc, 0x01c04398),
        "sfc_setup": (0x01c050c6, 0x01c051a2),
        "application_cache_handoff": (0x01c051a2, 0x01c051ee),
        "application_call": (0x01c05284, 0x01c05292),
    }
    fragments, programs, listings = {}, {}, []
    for name, (start, end) in regions.items():
        programs[name] = decode(boot, BOOT_LOAD, start, end)
        fragments[name] = {"start": start, "end_exclusive": end,
                           "sha256": sha(boot[start - BOOT_LOAD:end - BOOT_LOAD])}
        listings.append("; " + name)
        for pc, (text, size, _, _) in programs[name].code.items():
            match = re.search(r"\b(?:goto|call) (-?\d+)$", text)
            target = f" ; target 0x{pc + size + int(match[1]):08x}" if match else ""
            listings.append(f"{pc:08x}  {boot[pc - BOOT_LOAD:pc - BOOT_LOAD + size].hex(' '):<18} {text}{target}")
    checks = {
        "application_cache_handoff": {
            0x01c051be: "call -11486", 0x01c051c2: "cli",
            0x01c051c4: "r0 = [r9+0]", 0x01c051c8: "if ((r0 & 16384) == 0) goto -8",
            0x01c051cc: "[r4+0] = 0x1", 0x01c051d4: "[r9+0] |= 0x300",
            0x01c051d0: "r0 = r10 + 136"},
        "application_call": {0x01c05284: "r1 = [r12+0]", 0x01c05288: "r0 = r10 + 136",
                             0x01c0528c: "call r1", 0x01c0528e: "[r14+0] = 0x0"},
        "sfc_setup": {0x01c050d2: "[r2+0] &= 0xFFFFFFFE", 0x01c050e0: "[r14+0] = 0xF00000",
                      0x01c050e4: "[r14+0] = 0x0", 0x01c0519e: "[r14+12] = r0"},
    }
    for name, expected in checks.items():
        for address, text in expected.items():
            require(programs[name].code[address][0] == text, f"handover instruction changed at {address:#x}")
    # Register provenance at the start of the identified boot path.
    provenance = [(0x01c0380c, 0x01c03812, "r12 = 29390312"),
                  (0x01c045c4, 0x01c045ca, "r9 = 32432136"),
                  (0x01c04daa, 0x01c04db0, "r14 = 262656"),
                  (0x01c04dc0, 0x01c04dc6, "r10 = 29883776"),
                  (0x01c04ff0, 0x01c04ff4, "r4 = r14 + 256")]
    for start, end, text in provenance:
        require(decode(boot, BOOT_LOAD, start, end).code[start][0] == text, "handover register provenance changed")
    # The application's first RAM function call follows its copy, without an
    # explicit cache publication operation in this bounded reset sequence.
    reset = decode(app, FLASH_START, 0x02000120, 0x020001b8)
    call_text, call_size, _, _ = reset.code[0x0200019e]
    require(call_text == f"call {0x01c00e8c - 0x0200019e - call_size}", "first RAM callee changed")
    cache_traces = [CacheStoreTrace(programs["clear_cache_arrays"], value).run(value)
                    for value in (0, 0xa5a5a5a5)]
    (directory / "stock-handover.asm").write_text("\n".join(listings) + "\n", encoding="utf-8", newline="\n")
    return {"package_sha256": STOCK_SHA, "flash_sha256": sha(flash),
            "boot_container_sha256": sha(container), "boot_payload_sha256": BOOT_SHA,
            "boot_load": load, "boot_payload_bytes": len(boot),
            "boot_header_crc16": f"{header_crc:04x}", "boot_payload_crc16": f"{payload_crc:04x}",
            "boot_container_crc16": f"{entry.data_crc:04x}", "application_sha256": sha(app),
            "configuration": {"offset": config_entry.offset, "bytes": len(config), "sha256": sha(config),
                              "crc16": f"{config_entry.data_crc:04x}", "values": config_values},
            "native_fragments": fragments, "cache_array_store_traces": cache_traces,
            "cache_array_ranges": CACHE_RANGES, "cache_array_bytes_written": sum(b - a for a, b in CACHE_RANGES),
            "cache_control_clear_mask": 0x300, "cache_control_enable_mask": 0x300,
            "cache_idle_bit": 14, "stock_handoff_descriptor": 0x01c7fe08,
            "stock_application_call": 0x01c0528c, "application_entry": FLASH_START,
            "application_first_ram_call": {"instruction": 0x0200019e, "destination": 0x01c00e8c,
                                             "preceding_reset_sha256": sha(app[:0x020001a4 - FLASH_START])},
            "cache_hardware_modeled": False, "mmu_state_proven": False}


def xip_audit(raw):
    """Require all executable segments/sections and every FUNC symbol in XIP."""
    checked = inspect_elf(raw)
    h = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    sections = [struct.unpack_from("<10I", raw, h[5] + h[10] * i) for i in range(h[11])]
    names_section = sections[h[12]]
    names = raw[names_section[4]:names_section[4] + names_section[5]]
    named = lambda name_table, n: name_table[n:name_table.index(0, n)].decode("utf-8")
    executable_sections, functions, symbols = [], [], {}
    for i in range(h[9]):
        p = struct.unpack_from("<8I", raw, h[4] + h[8] * i)
        if p[0] == 1 and p[6] & 1:
            require(FLASH_START <= p[2] < p[2] + p[5] <= FLASH_END and p[2] == p[3],
                    "executable PT_LOAD outside XIP or copied executable segment")
    for index, s in enumerate(sections):
        if s[2] & 6 == 6:
            require(FLASH_START <= s[3] < s[3] + s[5] <= FLASH_END,
                    "allocated executable section outside XIP")
            executable_sections.append({"name": named(names, s[0]), "address": s[3], "bytes": s[5]})
        if s[1] != 2:
            continue
        strings = sections[s[6]]
        string_data = raw[strings[4]:strings[4] + strings[5]]
        for pos in range(s[4], s[4] + s[5], s[9]):
            name, value, size, info, other, section = struct.unpack_from("<IIIBBH", raw, pos)
            if not name or not section:
                continue
            text = named(string_data, name)
            symbols[text] = value
            if info & 15 == 2:
                require(FLASH_START <= value < FLASH_END and value + size <= FLASH_END,
                        "function outside XIP: " + text)
                require(section < len(sections) and sections[section][2] & 6 == 6,
                        "function has no executable section: " + text)
                functions.append({"name": text, "address": value, "bytes": size})
    require(symbols["__ram_end"] - symbols["__ram_start"] == 4, "diagnostic now copies more than one data word")
    require(symbols["__xip_ramtext_start"] <= symbols["__xip_ramtext_end"] <= symbols["__xip_text_end"],
            "XIP RAMtext boundary symbols")
    forbidden = ("hyperrig_mini_watchdog_", "hyperrig_mini_cache_", "hyperrig_mini_clock_", "hyperrig_mini_codec_")
    # The audio adapter object also carries its older table replay callback;
    # it is not called here and is not the hardware codec component.
    require(not any(name.startswith(forbidden) and not name.startswith("hyperrig_mini_codec_replay_stock")
                    for name in symbols), "hardware platform/codec unexpectedly linked")
    return {"elf_check": checked, "executable_sections": executable_sections,
            "function_symbols_in_xip": len(functions), "functions": functions,
            "initialized_ram_bytes": 4, "copied_instruction_bytes": 0,
            "ramtext_bytes_placed_in_xip": symbols["__xip_ramtext_end"] - symbols["__xip_ramtext_start"],
            "probe_mailbox": symbols["hyperrig_mini_probe"], "all_ram_segments_non_executable": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distro", default="Ubuntu")
    args = parser.parse_args()
    directory = ROOT / "build/mini-handover"
    directory.mkdir(parents=True, exist_ok=True)
    stock = stock_evidence(directory)
    dependencies = check_dependencies(True, False)
    runtime_raw = (ROOT / "research/mini-runtime.json").read_bytes()
    runtime = json.loads(runtime_raw)
    runtime_expected = dict(runtime["sources_sha256"])
    runtime_expected["tools/verify_mini_runtime.py"] = runtime["verifier_sha256"]
    runtime_expected["build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o"] = runtime["component_sha256"]
    verify_recorded_hashes(runtime_expected)
    dependencies["research/mini-runtime.json"] = {"sha256": sha(runtime_raw), "verified_sources_and_objects": len(runtime_expected)}
    previous_raw = (ROOT / "research/mini-boot.json").read_bytes()
    previous = json.loads(previous_raw)
    verify_recorded_hashes(previous["source_sha256"])
    host = previous["host_runtime_c_probe"]
    require(host["host_c_probe_passed"] and host["application_status"] == 0 and host["audio_status"] == 0 and
            host["dsp_crc32"] == "f10b5e4c" and host["tx_crc32"] == "f0a44a06", "existing integrated host probe not passing")
    capture = ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l"
    require(sha(capture.read_bytes()) == "86f5ea91f8069180e30612bcaad5820b14a94dd6c2552290ca09253082238c47",
            "diagnostic capture changed")
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []
    toolbase = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"

    def run(command):
        result = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout

    common_sources = ["startup.S", "boot_probe.c", "runtime.c", "irq.c"]
    added_sources = ["capture.S", "dsp_probe.c", "runtime_probe.c"]
    source_hashes = {}
    for name in common_sources + added_sources:
        source = "firmware/mini/boot/" + name
        command = [toolbase + "clang", "-target", "pi32v2", "-mcpu=r3", "-std=c99", "-Os",
                   "-ffreestanding", "-fno-builtin", "-Wall", "-Wextra", "-Werror",
                   "-Ifirmware/mini/boot", "-Ifirmware/mini/audio", "-Ifirmware/include"]
        if name in ("dsp_probe.c", "runtime_probe.c"):
            command += ["-mllvm", "-pi32v2-large-program", "-DHYPERRIG_MINI_RUNTIME_PROBE"]
        run(command + ["-c", source, "-o", "build/mini-handover/" + name + ".o"])
        source_hashes[source] = sha((ROOT / source).read_bytes())
    artifacts = []
    for variant in ("minimal", "runtime"):
        base = "build/mini-handover/hyperrig-mini-xip-" + variant
        objects = ["build/mini-handover/" + name + ".o" for name in common_sources]
        if variant == "runtime":
            objects += ["build/mini-handover/" + name + ".o" for name in added_sources]
            objects += ["build/native/hyperrig_dsp.pi32v2.o", "build/mini-audio/hyperrig_mini_audio.pi32v2.o",
                        "build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o"]
        run([toolbase + "ld", "-z", "max-page-size=0x20", "-z", "common-page-size=0x20",
             "-T", "firmware/mini/handover/mini_xip.ld", "-Map", base + ".map", *objects, "-o", base + ".elf"])
        raw = (ROOT / (base + ".elf")).read_bytes()
        audit = xip_audit(raw)
        simulations = {"boot_descriptor": StartupMachine(raw, False).run(),
                       "null_debug_descriptor": StartupMachine(raw, True).run()}
        (ROOT / (base + ".asm")).write_text(run([toolbase + "objdump", "-d", base + ".elf"]), encoding="utf-8", newline="\n")
        artifacts.append({"file": base + ".elf", "sha256": sha(raw), "audit": audit,
                          "startup_simulations": simulations, "dsp_worker_linked": variant == "runtime",
                          "expected_application_status": 0 if variant == "runtime" else -100,
                          "target_c_executed": False, "real_irq_or_dma_enabled": False, "flashable": False})
        print(f"XIP {variant}: all functions in flash; only 4 data bytes copied; ELF/startup checks passed.", flush=True)
    for path in (ROOT / "firmware/mini/handover").iterdir():
        if path.is_file():
            source_hashes[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    source_hashes["tools/verify_mini_handover.py"] = sha(Path(__file__).read_bytes())
    report = {"project": "HyperRig", "target": "TANK MINI", "stock": stock, "artifacts": artifacts,
              "checked_dependency_reports": dependencies, "sources_sha256": source_hashes,
              "existing_host_runtime_test": {"report": "research/mini-boot.json", "report_sha256": sha(previous_raw),
                                             "result": host, "rerun_for_linker_only_change": False},
              "entry_contract": "stock bootloader application call, never ROM USB RAM-loader entry",
              "removed_prerequisite": "instruction visibility after copying application RAMtext",
              "preserved_hardware": ["SFC mapping and ownership", "ENC", "PLL and dividers", "cache partition/enables", "MMU"],
              "unproven": ["physical boot/handover on this MINI", "incoming MMU/control state and RAM aliases",
                           "CPU1 and retained ROM state", "watchdog lifetime", "mailbox observation transport",
                           "real IRQ/DMA cache coherence and deadlines", "48 kHz codec/board clocks"],
              "hardware_accessed": False, "hardware_boot_verified": False, "flashable": False}
    (ROOT / "research/mini-handover.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Stock handover evidence and XIP layouts written to research/mini-handover.json; no device accessed.")


if __name__ == "__main__":
    main()
