"""Compile/check the CPU0 MINI event runtime offline; never open a device.

Host sanitizers exercise real runtime/audio C with fake DMA arrays. The target
checks independently decode the interrupt frame and critical-section objects;
they do not emulate an interrupt controller or prove real-time DMA deadlines.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.disassemble import codec, table

STOCK_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
SDK_URL = "https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/hwi.h"
FAR_CALL_FLAGS = ["-mllvm", "-pi32v2-large-program"]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def elf(path):
    raw = path.read_bytes()
    check(raw[:6] == b"\x7fELF\x01\x01", "ELF32 little-endian required")
    header = struct.unpack_from("<HHIIIIIHHHHHH", raw, 16)
    check(header[0] == 1 and header[1] == 0xF1, "relocatable pi32v2 required")
    sections = [struct.unpack_from("<10I", raw, header[5] + header[10] * i) for i in range(header[11])]
    symbols, indexed = {}, {}
    for si, section in enumerate(sections):
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        names = raw[strings[4]:strings[4] + strings[5]]
        for index, off in enumerate(range(section[4], section[4] + section[5], section[9])):
            name, value, size, info, other, target = struct.unpack_from("<IIIBBH", raw, off)
            name = names[name:names.index(0, name)].decode() if name else ""
            item = dict(name=name, value=value, size=size, info=info, section=target)
            indexed[si, index] = item
            if name:
                symbols[name] = item
    relocations = []
    for section in sections:
        if section[1] not in (4, 9):
            continue
        for off in range(section[4], section[4] + section[5], section[9]):
            offset, info = struct.unpack_from("<II", raw, off)
            relocations.append(dict(section=section[7], offset=offset, type=info & 255,
                                    symbol=indexed[section[6], info >> 8]["name"]))
    return raw, sections, symbols, relocations


def symbol_bytes(path, name):
    raw, sections, symbols, relocations = elf(path)
    symbol = symbols[name]
    section = sections[symbol["section"]]
    start = section[4] + symbol["value"]
    return raw[start:start + symbol["size"]], symbol, relocations


def decode(data, allow_blocks=False):
    instructions = table.load()
    result, offset = [], 0
    while offset < len(data):
        item = codec.decode(instructions, data, offset)
        check(item is not None, f"unknown opcode at {offset:#x}")
        instruction, fields, size = item
        check(allow_blocks or not instruction.block, "unexpected predicate block")
        result.append((offset, size, codec.format(instruction, fields)))
        offset += size
    return result


def stock_evidence():
    raw = (ROOT / "artifacts/tank-mini/TANK-MINI.fwsc").read_bytes()
    check(sha(raw) == STOCK_SHA, "MINI firmware differs from pinned 009 sample")
    _, files = unpack_fwsc(raw)
    app, _, _ = unpack_app(files["flash.bin"][0x4000:])
    check(app == (ROOT / "analysis/tank-mini/app_area.dec.bin").read_bytes(), "decoded MINI differs")
    def region(start, end):
        offset = 0x6ED20 + start - 0x01C00000
        return app[offset:offset + end - start]
    prologue = [item[2] for item in decode(region(0x01C0374A, 0x01C03750))]
    epilogue = [item[2] for item in decode(region(0x01C037D2, 0x01C037DC))]
    check(prologue == ["[--sp] = {psr, rets, reti}", "[--sp] = {r5-r0}"], "stock ISR prologue")
    check(epilogue == ["{r5-r0} = [sp++]", "{psr, rets, reti} = [sp++]", "csync", "rti"], "stock ISR epilogue")
    callback = decode(region(0x01C03EEE, 0x01C03F24))
    check(callback[1][2] == "r1 = 29471276" and callback[2][2] == "b[r1+0] = r0", "stock half mailbox")
    calls = [0x01C03EEE + off + size + int(text.split()[1]) for off, size, text in callback if text.startswith("call ")]
    check(calls == [0x02044D44], "stock callback semaphore post")
    regions = {"irq11": (0x01C0374A, 0x01C037DC), "half_callback": (0x01C03EEE, 0x01C03F24),
               "audio_task": (0x01C03F24, 0x01C03FB4)}
    return {"package_sha256": STOCK_SHA, "sdk_irq_mapping_source": SDK_URL,
            "fragments": {name: {"start": hex(start), "end_exclusive": hex(end),
                                   "sha256": sha(region(start, end))} for name, (start, end) in regions.items()},
            "stock_irq_frame_instructions": prologue + epilogue,
            "stock_half_mailbox": "0x01c1b22c", "stock_semaphore_post": "0x02044d44",
            "stock_semaphore_wait": "0x020456f8", "stock_dsp_task_call": "0x01c03a18"}


def target_checks(out):
    data, symbol, relocations = symbol_bytes(out / "irq11_pi32v2.o", "hyperrig_mini_irq11_entry")
    instructions = [item[2] for item in decode(data)]
    check(instructions == ["[--sp] = {psr, rets, reti}", "[--sp] = {r15-r0}", "call 0",
                           "{r15-r0} = [sp++]", "{psr, rets, reti} = [sp++]", "csync", "rti"], "target ISR ABI changed")
    check(relocations == [{"section": symbol["section"], "offset": 6, "type": 2,
                           "symbol": "hyperrig_mini_irq11_dispatch"}], "IRQ dispatch relocation changed")
    reference, reference_symbol, reference_relocations = symbol_bytes(out / "compiler_irq_reference.o", "compiler_irq_abi_reference")
    reference_ops = [i[2] for i in decode(reference)]
    check(reference_ops == ["[--sp] = {psr, rets, reti}", "[--sp] = {r3-r0}", "call 0",
                            "{r3-r0} = [sp++]", "{psr, rets, reti} = [sp++]", "rti"], "vendor interrupt attribute ABI changed")
    check(reference_relocations == [{"section": reference_symbol["section"], "offset": 4, "type": 4,
                                     "symbol": "hyperrig_mini_irq11_dispatch"}], "vendor reference call target changed")
    # There is no established generic preservation rule for hidden loop/coproc
    # state. Audit the known call graph; future wake hooks remain outside this
    # check and interrupt delivery during foreground hardware loops is unproven.
    known_isr = {}
    for filename, names in (("hyperrig_mini_runtime_component.pi32v2.o",
                             ["hyperrig_mini_irq11_dispatch", "hyperrig_mini_runtime_ready", "fault_locked",
                              "hyperrig_mini_runtime_enter_cpu0", "hyperrig_mini_runtime_leave_cpu0"]),
                            ("audio_dependency.pi32v2.o", ["hyperrig_mini_audio_irq"])):
        for name in names:
            fragment, _, _ = symbol_bytes(out / filename, name)
            listing = [i[2] for i in decode(fragment, allow_blocks=True)]
            unsupported = re.compile(r"\b(?:rep|copex|cexe|sr\d+|uspn|sspn|icfgn|icfgs|rete|retx|cnum|usp|ssp|cc)\b")
            check(not any(unsupported.search(text) for text in listing), f"new special/loop state in {name}")
            known_isr[name] = {"bytes": len(fragment), "instructions": len(listing), "sha256": sha(fragment)}
    # State model of this exact verified save/call/restore sequence, with a C
    # callback clobbering all GPRs and special saved registers. Not CPU emulation.
    rng = random.Random(0x49525131)
    for _ in range(256):
        before = {name: rng.getrandbits(32) for name in ["psr", "rets", "reti"] + [f"r{i}" for i in range(16)]}
        registers, stack = dict(before), []
        for group in (["psr", "rets", "reti"], [f"r{i}" for i in range(16)]):
            stack.append({name: registers[name] for name in group})
        registers = {name: rng.getrandbits(32) for name in registers}
        while stack:
            registers.update(stack.pop())
        check(registers == before, "interrupt-frame state model mismatch")
    entry, _, _ = symbol_bytes(out / "critical_pi32v2.o", "hyperrig_mini_runtime_enter_cpu0")
    leave, _, _ = symbol_bytes(out / "critical_pi32v2.o", "hyperrig_mini_runtime_leave_cpu0")
    entry_ops, leave_ops = [i[2] for i in decode(entry)], [i[2] for i in decode(leave)]
    check(entry_ops == ["r0 = icfg", "r1 = r0 & 0xFFFFFEFF", "icfg = r1", "csync", "rts"], "ICFG save/mask changed")
    check(leave_ops == ["csync", "icfg = r1", "rts"], "ICFG exact restore changed")
    for _ in range(256):
        flags = rng.getrandbits(32)
        masked = flags & ~256
        check(not masked & 256 and masked & ~256 == flags & ~256, "ICFG model lost flags")
    _, _, sizes, _ = elf(out / "abi_probe.o")
    _, sections, component, component_relocations = elf(out / "hyperrig_mini_runtime_component.pi32v2.o")
    branches = [item for item in component_relocations if item["type"] in (2, 4)]
    check(all(item["symbol"] == "hyperrig_mini_irq11_dispatch" for item in branches if item["type"] == 2),
          "unexpected short cross-section runtime call")
    check(any(item["symbol"] == "hyperrig_mini_audio_irq" and item["type"] == 4 for item in branches),
          "RAM dispatcher must use an extended flash call")
    unresolved = sorted(name for name, item in component.items() if not item["section"] and item["info"] >> 4)
    check(unresolved == ["hyperrig_mini_audio_irq", "hyperrig_mini_audio_rx_q", "hyperrig_mini_audio_tx_q", "memcpy"],
          f"unexpected runtime dependencies: {unresolved}")
    return {"context_bytes": sizes["context_bytes"]["size"], "ops_bytes": sizes["ops_bytes"]["size"],
            "snapshot_bytes": sizes["snapshot_bytes"]["size"], "interrupt_wrapper_bytes": len(data),
            "interrupt_stack_bytes_excluding_c_calls": 76, "interrupt_frame_state_cases": 256,
            "critical_flag_state_cases": 256, "interrupt_instructions": instructions,
            "compiler_interrupt_attribute_instructions": reference_ops,
            "compiler_call_flags": FAR_CALL_FLAGS, "cross_section_branch_relocations": branches,
            "known_isr_callgraph_audit": known_isr,
            "future_wake_hook_included_in_audit": False,
            "hardware_loop_interrupt_delivery_verified": False,
            "hidden_special_state_preservation_verified": False,
            "critical_enter_instructions": entry_ops, "critical_leave_instructions": leave_ops,
            "unresolved_component_symbols": unresolved,
            "component_alloc_bytes": sum(section[5] for section in sections if section[2] & 2)}


def main():
    out = ROOT / "build/mini-runtime"
    out.mkdir(parents=True, exist_ok=True)
    prefix = ["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []
    def run(args):
        result = subprocess.run(prefix + args, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout
    vendor = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    directory = "firmware/mini/runtime/"
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror"]
    objects = []
    for source, output in (("hyperrig_mini_runtime.c", "hyperrig_mini_runtime.pi32v2.o"),
                           ("irq_dispatch.c", "irq_dispatch.pi32v2.o"),
                           ("critical_pi32v2.c", "critical_pi32v2.o"),
                           ("irq11_pi32v2.S", "irq11_pi32v2.o")):
        target = "build/mini-runtime/" + output
        flags = common + ["-Os", "-ffreestanding", "-fno-builtin", *FAR_CALL_FLAGS] if source.endswith(".c") else []
        run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", *flags, "-c", directory + source, "-o", target])
        objects.append(target)
    run([vendor + "ld", "-r", *objects, "-o", "build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o"])
    (out / "compiler_irq_reference.c").write_text('extern unsigned hyperrig_mini_irq11_dispatch(void);\n'
        '__attribute__((interrupt)) void compiler_irq_abi_reference(void) { (void)hyperrig_mini_irq11_dispatch(); }\n', encoding="utf-8")
    run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin", *FAR_CALL_FLAGS, "-c",
         "build/mini-runtime/compiler_irq_reference.c", "-o", "build/mini-runtime/compiler_irq_reference.o"])
    run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin", "-c",
         "firmware/mini/audio/hyperrig_mini_audio.c", "-o", "build/mini-runtime/audio_dependency.pi32v2.o"])
    (out / "abi_probe.c").write_text('#include "hyperrig_mini_runtime.h"\n'
        'unsigned char context_bytes[sizeof(hyperrig_mini_runtime)];\n'
        'unsigned char ops_bytes[sizeof(hyperrig_mini_runtime_ops)];\n'
        'unsigned char snapshot_bytes[sizeof(hyperrig_mini_runtime_snapshot)];\n', encoding="utf-8")
    run([vendor + "clang", "-target", "pi32v2", "-mcpu=r3", *common, "-I" + directory, "-c",
         "build/mini-runtime/abi_probe.c", "-o", "build/mini-runtime/abi_probe.o"])
    run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
         directory + "hyperrig_mini_runtime.c", directory + "irq_dispatch.c",
         "firmware/mini/audio/hyperrig_mini_audio.c", directory + "tests/runtime_test.c",
         "-o", "build/mini-runtime/sanitize"])
    host = json.loads(run(["build/mini-runtime/sanitize"]))
    report = {"stock": stock_evidence(), "host": host, "target": target_checks(out),
              "hardware_execution_verified": False, "real_dma_ownership_verified": False,
              "dma_cache_coherence_verified": False, "interrupt_latency_measured": False,
              "dsp_deadline_measured": False, "flashable": False,
              "component": "build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o",
              "component_sha256": sha((out / "hyperrig_mini_runtime_component.pi32v2.o").read_bytes()),
              "sources_sha256": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                                  for p in sorted((ROOT / directory).rglob("*")) if p.is_file()},
              "audio_dependency_sha256": sha((ROOT / "firmware/mini/audio/hyperrig_mini_audio.c").read_bytes()),
              "verifier_sha256": sha(Path(__file__).read_bytes())}
    (ROOT / "research/mini-runtime.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"host": host, "target": report["target"]}, indent=2))
    print("MINI runtime verified offline. No physical MMIO, device commands or firmware image produced.")


if __name__ == "__main__":
    main()
