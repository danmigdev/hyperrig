"""Build and simulate startup of diagnostic MINI ELFs. Never flash/package them.

The simulation stops before C entry: it verifies RAM copying, BSS clearing,
stack addresses and preservation of the observed boot descriptor fields. It
does not emulate the boot ROM, clock/cache state, interrupts or target DSP.
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
from hyperrig.jieli import unpack_app, unpack_fwsc
from check_mini_image import inspect_elf
from dot_machine import DotMachine
from pi32v2isa import codec, table

STOCK_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
RAM_BASE, RAM_END, FLASH_BASE, FLASH_END = 0x01C00000, 0x01C80000, 0x02000000, 0x0207E000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_recorded_hashes(expected, root=ROOT):
    """Refuse linking old target objects while host tests use newer sources."""
    if not isinstance(expected, dict) or not expected:
        raise ValueError("component report has no recorded inputs")
    for name, digest in expected.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or sha(path.read_bytes()) != digest:
            raise ValueError(f"component input changed or missing: {name}; rerun its verifier/build")


def check_dependencies(dsp, bringup):
    specs = []
    if dsp:
        specs += [("analysis/native/verification.json", "reconstruction_source_sha256", None,
                   {"build/native/hyperrig_dsp.pi32v2.o": "pi32v2_object_sha256"}),
                  ("research/mini-audio-driver.json", "sources_sha256", "tools/verify_mini_audio.py",
                   {"build/mini-audio/hyperrig_mini_audio.pi32v2.o": "pi32v2_object_sha256"})]
    if bringup:
        specs += [("research/mini-platform.json", "sources_sha256", "tools/verify_mini_platform.py",
                   {"build/mini-platform/hyperrig_mini_platform.pi32v2.o": "pi32v2_object_sha256"}),
                  ("research/mini-runtime.json", "sources_sha256", "tools/verify_mini_runtime.py",
                   {"build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o": "component_sha256"}),
                  ("research/mini-codec.json", "sources_sha256", "tools/verify_mini_codec.py", {})]
    checked = {}
    for report_path, source_key, verifier, objects in specs:
        raw = (ROOT / report_path).read_bytes()
        report = json.loads(raw)
        expected = dict(report[source_key])
        if verifier:
            expected[verifier] = report["verifier_sha256"]
        expected.update({path: report[key] for path, key in objects.items()})
        if report_path.endswith("mini-codec.json"):
            expected.update({"build/mini-codec/" + name: data["sha256"]
                             for name, data in report["target_objects"].items()})
        verify_recorded_hashes(expected)
        checked[report_path] = {"sha256": sha(raw), "verified_sources_and_objects": len(expected)}
    return checked


def elf_layout(raw):
    header = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    phdrs = [struct.unpack_from("<8I", raw, header[4] + header[8] * i) for i in range(header[9])]
    sections = [struct.unpack_from("<10I", raw, header[5] + header[10] * i) for i in range(header[11])]
    symbols = {}
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        names = raw[strings[4]:strings[4] + strings[5]]
        for off in range(section[4], section[4] + section[5], section[9]):
            name, value, size, info, other, index = struct.unpack_from("<IIIBBH", raw, off)
            if name and index:
                text = names[name:names.index(0, name)].decode()
                symbols[text] = (value, size)
    return phdrs, symbols


class StartupMachine(DotMachine):
    def __init__(self, raw, null_descriptor):
        phdrs, self.symbols = elf_layout(raw)
        self.flash = bytearray([0xA5]) * (FLASH_END - FLASH_BASE)
        self.ram = bytearray([0xA5]) * (RAM_END - RAM_BASE)
        for kind, offset, vma, lma, size, memory, flags, alignment in phdrs:
            if kind == 1 and size:
                self.flash[lma - FLASH_BASE:lma - FLASH_BASE + size] = raw[offset:offset + size]
        start, size = self.symbols["_start"]
        code, cursor = {}, start
        instructions = table.load()
        while cursor < start + size:
            result = codec.decode(instructions, self.flash, cursor - FLASH_BASE)
            if result is None:
                raise ValueError(f"unsupported startup encoding at {cursor:#x}")
            instruction, fields, length = result
            if instruction.block:
                raise ValueError("startup probe unexpectedly uses a predicate block")
            text = codec.format(instruction, fields)
            if text.endswith("  #"):
                raise ValueError("startup probe unexpectedly uses parallel issue")
            code[cursor] = text, length, 0, 0
            cursor += length
        self.program = SimpleNamespace(start=start, code=code)
        self.pc, self.steps, self.carry = start, 0, 0
        self.regs = {f"r{i}": 0 for i in range(16)}
        self.regs.update(sp=0, ssp=0)
        self.interrupts_disabled, self.synchronized = False, False
        descriptor, pointed = 0x01C7FD80, 0x01C7FDC0
        self.write(descriptor, pointed, 4)
        for i, value in enumerate((0x11112222, 0x33334444, 0x55667788, 0x99AABBCC, 0xDDEEFF00), 1):
            self.write(descriptor + 4 * i, value, 4)
        self.write(pointed + 8, 0x10203040, 4)
        self.write(pointed + 13, 0x5A, 1)
        self.regs["r0"] = 0 if null_descriptor else descriptor
        self.expected_ram = bytearray(self.ram)
        context = self.symbols["__hyperrig_boot_context"][0]

        def expect(address, data):
            self.expected_ram[address - RAM_BASE:address - RAM_BASE + len(data)] = data

        if not null_descriptor:
            expect(context, b"\x5a")
            expect(context + 16, struct.pack("<II", 0x11112222, 0x33334444))
            expect(context + 24, struct.pack("<I", 0x10203040))
            expect(context + 28, struct.pack("<III", 0x55667788, 0x99AABBCC, 0xDDEEFF00))
        bss_start, bss_end = self.symbols["__bss_start"][0], self.symbols["__bss_end"][0]
        expect(bss_start, bytes(bss_end - bss_start))
        load_start, load_end = self.symbols["__ram_load_start"][0], self.symbols["__ram_load_end"][0]
        expect(self.symbols["__ram_start"][0], self.flash[load_start - FLASH_BASE:load_end - FLASH_BASE])

    def read(self, address, size):
        if RAM_BASE <= address and address + size <= RAM_END:
            return int.from_bytes(self.ram[address - RAM_BASE:address - RAM_BASE + size], "little")
        if FLASH_BASE <= address and address + size <= FLASH_END:
            return int.from_bytes(self.flash[address - FLASH_BASE:address - FLASH_BASE + size], "little")
        raise ValueError(f"startup read outside mapped memory: {address:#x}")

    def write(self, address, value, size):
        if not RAM_BASE <= address or address + size > RAM_END:
            raise ValueError(f"startup write outside RAM: {address:#x}")
        self.ram[address - RAM_BASE:address - RAM_BASE + size] = value.to_bytes(size, "little")

    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if text == "cli":
            self.interrupts_disabled = True
        elif text == "csync":
            self.synchronized = True
        elif match := re.fullmatch(r"(sp|ssp) = (\d+)", text):
            self.set(match[1], int(match[2]))
        elif match := re.fullmatch(r"(r\d+_r\d+) = d\[(.+)\]", text):
            self.set_pair(match[1], self.read(self.address(match[2]), 8))
        elif match := re.fullmatch(r"d\[(.+)\] = (r\d+_r\d+)", text):
            self.write(self.address(match[1]), self.pair(match[2]), 8)
        elif match := re.fullmatch(r"(r\d+) = b\[(.+)\] \(u\)", text):
            self.set(match[1], self.read(self.address(match[2]), 1))
        elif match := re.fullmatch(r"b\[(.+)\] = (r\d+)", text):
            self.write(self.address(match[1]), self.value(match[2]) & 255, 1)
        else:
            return super().step()
        self.pc += size
        return True

    def run(self):
        entry = self.symbols["hyperrig_mini_boot_main"][0]
        while self.pc != entry:
            if self.pc not in self.program.code or self.steps >= 1_000_000:
                raise ValueError(f"startup escaped/budget exceeded at {self.pc:#x}")
            self.step()
            self.steps += 1
        if self.ram != self.expected_ram:
            raise ValueError("startup memory result differs from ELF/boot-context contract")
        if (not self.interrupts_disabled or not self.synchronized or
                self.value("sp") != self.symbols["__stack_top"][0] or
                self.value("ssp") != self.symbols["__ssp_top"][0] or
                self.value("r0") != self.symbols["__hyperrig_boot_context"][0]):
            raise ValueError("startup register/control-state contract failed")
        return {"steps": self.steps, "whole_ram_result_sha256": sha(self.ram),
                "stopped_before_c_entry": True, "irq_disabled": True}


def stock_evidence():
    raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
    if sha(raw) != STOCK_SHA:
        raise ValueError("MINI package differs from pinned stock 009")
    _, files = unpack_fwsc(raw)
    _, _, app_files = unpack_app(files["flash.bin"][0x4000:0x82000])
    app = app_files["app.bin"]
    if app != (ROOT / "analysis/tank-mini/app.bin").read_bytes():
        raise ValueError("decoded MINI app differs from verified package")
    ranges = {"reset": (0x02000120, 0x020001B8), "boot_descriptor": (0x020001E6, 0x02000218),
              "irq_registration": (0x02001756, 0x020017DC), "heap_bounds": (0x02040C40, 0x02040C96),
              "cpu1_launch": (0x0204462C, 0x0204466E)}
    return {"package_sha256": STOCK_SHA, "application_sha256": sha(app),
            "fragments": {name: {"start": start, "end_exclusive": end,
                                     "sha256": sha(app[start - 0x02000120:end - 0x02000120])}
                          for name, (start, end) in ranges.items()},
            "entry": 0x02000120, "initial_sp": 0x01C1899C, "initial_ssp": 0x01C1999C,
            "ram_copy": {"source": 0x0206ED20, "destination": 0x01C00000, "bytes": 0xE018},
            "bss_clear": [0x01C0E018, 0x01C1F414], "heap": [0x01C1F420, 0x01C7FD30],
            "boot_context": 0x01C7FD50, "irq_table": 0x01C7FE00,
            "cpu0_irq_controller": 0x01EEF100, "cpu1_irq_controller": 0x01EEF300,
            "cpu1_entry_slot": 0x01C7FFF8, "cpu1_stock_entry": 0x020001B8,
            "cpu1_stock_usp": 0x01C19C9C, "cpu1_stock_sp": 0x01C1AC9C,
            "cpu1_stock_reti": 0x01C020AA,
            "cache_ram_data": {"source": 0x0207CD38, "destination": 0x01F28000, "bytes": 32}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distro", default="Ubuntu")
    parser.add_argument("--dsp", action="store_true", help="also link DSP/audio/A2 and run the RAM-only C probe on the host")
    parser.add_argument("--bringup", action="store_true",
                        help="also link platform/codec/runtime and verify runtime-to-DSP with fake DMA; no MMIO")
    args = parser.parse_args()
    args.dsp = args.dsp or args.bringup
    dependency_reports = check_dependencies(args.dsp, args.bringup)
    evidence = stock_evidence()
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    linker = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/ld"
    objdump = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/objdump"
    directory = ROOT / "build/mini-boot"
    directory.mkdir(parents=True, exist_ok=True)

    def run(command):
        result = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout

    sources = ["startup.S", "boot_probe.c", "runtime.c", "irq.c"]
    if args.dsp:
        sources += ["capture.S", "dsp_probe.c"]
        capture = (ROOT / "analysis/firmware/m571_g_app/embedded-0.a2l").read_bytes()
        if sha(capture) != "86f5ea91f8069180e30612bcaad5820b14a94dd6c2552290ca09253082238c47":
            raise ValueError("DSP probe capture differs from pinned A2 fixture")
    for name in sources:
        run([compiler, "-target", "pi32v2", "-mcpu=r3", "-std=c99", "-Os", "-ffreestanding", "-fno-builtin",
             "-Wall", "-Wextra", "-Werror", "-Ifirmware/mini/boot", "-Ifirmware/mini/audio", "-Ifirmware/include", "-c",
             "firmware/mini/boot/" + name, "-o", "build/mini-boot/" + name + ".o"])
    if args.bringup:
        for name in ("runtime_probe.c", "dsp_probe.c"):
            run([compiler, "-target", "pi32v2", "-mcpu=r3", "-std=c99", "-Os", "-ffreestanding", "-fno-builtin",
                 "-Wall", "-Wextra", "-Werror", "-mllvm", "-pi32v2-large-program", "-DHYPERRIG_MINI_RUNTIME_PROBE",
                 "-Ifirmware/mini/boot", "-Ifirmware/mini/audio", "-Ifirmware/include", "-c",
                 "firmware/mini/boot/" + name, "-o", "build/mini-boot/bringup-" + name + ".o"])
    artifacts = []
    variants = ["boot"] + (["dsp"] if args.dsp else []) + (["bringup"] if args.bringup else [])
    bringup_objects = ["build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o",
                       "build/mini-platform/hyperrig_mini_platform.pi32v2.o",
                       "build/mini-codec/hyperrig_mini_codec.pi32v2.o", "build/mini-codec/spin_pi32v2.o"]
    for variant in variants:
        dsp = variant != "boot"
        name = {"boot": "hyperrig-mini-boot-probe", "dsp": "hyperrig-mini-dsp-link-probe",
                "bringup": "hyperrig-mini-bringup-probe"}[variant]
        relative = "build/mini-boot/" + name
        objects = ["build/mini-boot/" + name + ".o" for name in sources[:4]]
        if dsp:
            probe = "bringup-dsp_probe.c.o" if variant == "bringup" else "dsp_probe.c.o"
            objects += ["build/mini-boot/capture.S.o", "build/mini-boot/" + probe,
                        "build/native/hyperrig_dsp.pi32v2.o", "build/mini-audio/hyperrig_mini_audio.pi32v2.o"]
        if variant == "bringup":
            objects += ["build/mini-boot/bringup-runtime_probe.c.o", *bringup_objects]
        # Vendor ld defaults to p_align=0x500, which violates standard ELF.
        # Explicit power-of-two pages also make offset/VMA congruence auditable.
        run([linker, "-z", "max-page-size=0x20", "-z", "common-page-size=0x20", "-T", "firmware/mini/boot/mini.ld",
             "-Map", relative + ".map", *objects, "-o", relative + ".elf"])
        raw = (ROOT / (relative + ".elf")).read_bytes()
        checked = inspect_elf(raw)
        simulations = {"boot_descriptor": StartupMachine(raw, False).run(),
                       "null_debug_descriptor": StartupMachine(raw, True).run()}
        (ROOT / (relative + ".asm")).write_text(run([objdump, "-d", relative + ".elf"]), encoding="utf-8", newline="\n")
        artifacts.append({"file": relative + ".elf", "sha256": sha(raw), "elf_check": checked,
                          "startup_simulations": simulations, "target_c_executed": False,
                          "dsp_linked": dsp, "audio_adapter_linked": dsp,
                          "runtime_worker_linked": variant == "bringup",
                          "platform_codec_linked_but_inactive": variant == "bringup", "flashable": False})
        print(f"{name}: linked; ELF layout + two startup instruction simulations passed.", flush=True)
    report = {"project": "HyperRig", "target": "TANK MINI", "stock": evidence, "artifacts": artifacts,
              "checked_dependency_reports": dependency_reports,
              "source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p.read_bytes())
                                for p in sorted((ROOT / "firmware/mini/boot").iterdir()) if p.is_file()},
              "boot_validated_on_device": False, "flashable": False,
              "unimplemented": ["boot-ROM handover validation", "on-device clock/watchdog/board init", "DMA cache coherence",
                                "peripheral pin/codec/mute validation", "CPU1 scheduler/start", "recovery installation"]}
    if args.dsp:
        report["dsp_object_sha256"] = sha((ROOT / "build/native/hyperrig_dsp.pi32v2.o").read_bytes())
        report["audio_object_sha256"] = sha((ROOT / "build/mini-audio/hyperrig_mini_audio.pi32v2.o").read_bytes())
        report["dsp_probe_expected_crc32"] = "f10b5e4c"
        report["audio_probe_expected_tx_crc32"] = "f0a44a06"
        report["dsp_probe_expected_source"] = "original kernels interpreted, A2 reset then 64 zero input samples"
        report["audio_probe_expected_source"] = "original-kernel output shifted right 8, masked to low24, duplicated into 128 LE TX slots"
        native_sources = ["firmware/src/hyperrig_" + name + ".c" for name in
                          ("dot", "head", "a2l", "rechannel", "layer", "engine")]
        host_sources = ["firmware/mini/boot/probe_host.c", "firmware/mini/boot/dsp_probe.c",
                        "firmware/mini/boot/capture.S", "firmware/mini/audio/hyperrig_mini_audio.c", *native_sources]
        run(["gcc", "-std=c99", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
             "-Ifirmware/mini/boot", "-Ifirmware/mini/audio", "-Ifirmware/include",
             "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-Wl,-z,noexecstack",
             *host_sources, "-o", "build/mini-boot/probe-host-sanitize"])
        report["host_c_probe"] = json.loads(run(["build/mini-boot/probe-host-sanitize"]))
        report["host_c_probe"].update({"address_sanitizer": True, "undefined_behavior_sanitizer": True,
                                       "target_c_executed": False, "mmio_called": False,
                                       "executable_sha256": sha((directory / "probe-host-sanitize").read_bytes())})
        print("Host C probe: ASan/UBSan passed; DSP CRC f10b5e4c, RAM audio TX CRC f0a44a06.", flush=True)
        if args.bringup:
            host_runtime_sources = ["firmware/mini/boot/runtime_probe.c",
                                    "firmware/mini/runtime/hyperrig_mini_runtime.c"]
            run(["gcc", "-std=c99", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                 "-DHYPERRIG_MINI_RUNTIME_PROBE", "-Ifirmware/mini/boot", "-Ifirmware/mini/audio", "-Ifirmware/include",
                 "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-Wl,-z,noexecstack",
                 *host_sources, *host_runtime_sources, "-o", "build/mini-boot/bringup-host-sanitize"])
            report["host_runtime_c_probe"] = json.loads(run(["build/mini-boot/bringup-host-sanitize"]))
            report["host_runtime_c_probe"].update({"address_sanitizer": True, "undefined_behavior_sanitizer": True,
                "target_c_executed": False, "mmio_called": False, "hardware_irq_entered": False,
                "ram_event_worker_dsp_path": True, "completed_blocks": 1,
                "ownership_callbacks": "private RAM arrays, never claimed for real DMA",
                "executable_sha256": sha((directory / "bringup-host-sanitize").read_bytes())})
            report["bringup_objects_sha256"] = {path: sha((ROOT / path).read_bytes()) for path in bringup_objects}
            print("Host runtime probe: event -> worker -> A2 -> TX CRC f0a44a06; ASan/UBSan passed, no MMIO.", flush=True)
    report["source_sha256"]["tools/build_mini_boot.py"] = sha(Path(__file__).read_bytes())
    (ROOT / "research/mini-boot.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Evidence: research/mini-boot.json. No boot on a device or flashable image is claimed.")


if __name__ == "__main__":
    main()
