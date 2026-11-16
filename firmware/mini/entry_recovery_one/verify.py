"""Offline checks for the condition-only, any-footswitch application guard.

The decoder/model evaluates emitted pi32v2 instructions and fake MMIO. It is
not an electrical, timing, cold-boot or USB enumeration qualification.
"""
from __future__ import annotations

import hashlib
import struct

from firmware.mini.entry_recovery import verify as original
from tools import build_mini_entry_recovery_v2 as previous

ADDRESS = 0x020773C8
SAMPLE_BRANCH = 0x02077474
OLD_END = 0x020774F2
NEW_END = OLD_END + 2
OLD_SHA = "fed49e2b7df48f652b791d3bf52c851fae9d02ce3b21363996cd28e75ac99291"
NAMES = (
    "hyperrig_mini_entry_guard_v2",  # Frozen prefix, not a new ABI.
    "hyperrig_mini_entry_recovery_check",
    "hyperrig_mini_entry_recovery_to_rom",
    "hyperrig_mini_g_startup_resume",
)
require = original.require
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def moved(address: int) -> int:
    return address + (2 if SAMPLE_BRANCH < address < OLD_END else 0)


def verify_minimal_delta(old: bytes, new: bytes) -> dict:
    """Require one new predicate and exactly the resulting branch relocations."""
    require(sha(old) == OLD_SHA and len(old) == 298, "not the frozen v3 guard")
    require(len(new) == 300, "the any-one guard must grow by exactly two bytes")
    before = original.instructions(old, ADDRESS, ADDRESS, OLD_END)
    after = original.instructions(new, ADDRESS, ADDRESS, NEW_END)
    require(len(before) == len(after), "guard instruction count changed")
    relocations = []
    predicate = None
    for a, b in zip(before, after):
        require(b["address"] == moved(a["address"]), "unexpected instruction relocation")
        if a["address"] == SAMPLE_BRANCH:
            require(a["id"] == "bnez" and a["fields"] == {"r": 0, "n": 9},
                    "old sample branch preimage differs")
            require(b["id"] == "beq.rr" and b["size"] == 4 and
                    {k: v for k, v in b["fields"].items() if k != "n"} == {"r": 0, "s": 5} and
                    b["target"] == moved(a["target"]), "wrong any-one sample predicate")
            predicate = {"before": a, "after": b}
        elif "target" in a:
            require(b["id"] == a["id"] and b["size"] == a["size"] and
                    b.get("target") == moved(a["target"]) and
                    {k: v for k, v in a["fields"].items() if k != "n"} ==
                    {k: v for k, v in b["fields"].items() if k != "n"},
                    "branch semantics changed beyond relocation")
            if a["bytes"] != b["bytes"]:
                relocations.append({"before": a, "after": b})
        else:
            require(a["bytes"] == b["bytes"] and a["text"] == b["text"],
                    "non-branch guard instruction changed")
    require(predicate is not None, "sample predicate missing")
    require(new[-54:] == old[-54:] and sha(new[-54:]) == previous.RESET_CODE_SHA,
            "reset body changed")
    return {"predicate": predicate, "relocations": relocations,
            "old_payload_sha256": sha(old), "new_payload_sha256": sha(new),
            "growth_bytes": 2, "reset_body_byte_identical": True,
            "all_other_instruction_semantics_unchanged": True}


def inspect_elf(raw: bytes, old: bytes) -> tuple[bytes, dict, dict]:
    def read(fmt, offset):
        require(0 <= offset <= len(raw)-struct.calcsize(fmt), "truncated any-one ELF")
        return struct.unpack_from(fmt, raw, offset)

    require(raw[:7] == b"\x7fELF\x01\x01\x01", "ELF32 little-endian required")
    h = read("<HHIIIIIHHHHHH", 16)
    require(h[:4] == (2, 0xF1, 1, ADDRESS) and h[7:11] == (52, 32, 1, 40),
            "any-one ELF header/entry differs")
    p = read("<8I", h[4])
    require(p[0] == 1 and p[2] == p[3] == ADDRESS and p[4] == p[5] == 300 and p[6] == 5,
            "one initialized 300-byte RX segment required")
    require(p[1] <= len(raw)-p[4] and p[7] > 0 and not (p[7] & (p[7]-1)) and
            p[1] % p[7] == ADDRESS % p[7], "ELF segment mapping/alignment")
    sections = [read("<10I", h[5]+40*i) for i in range(h[11])]
    symbols, regions = {}, []
    for section in sections:
        _, kind, flags, start, offset, size, link, _, align, stride = section
        require(kind == 8 or 0 <= offset <= len(raw)-size, "ELF section outside file")
        if flags & 2 and size:
            require(kind == 1 and flags == 6 and ADDRESS <= start and start+size <= NEW_END and
                    offset == p[1]+start-ADDRESS and (not align or start % align == 0),
                    "unexpected allocated section or BSS")
            regions.append((start, start+size))
        if kind != 2:
            continue
        require(stride == 16 and size % 16 == 0 and link < len(sections), "symbol geometry")
        ns = sections[link]
        require(ns[1] == 3, "symbol names section")
        names = raw[ns[4]:ns[4]+ns[5]]
        for off in range(offset, offset+size, 16):
            name, value, length, info, _, ndx = read("<IIIBBH", off)
            if not name:
                continue
            require(name < len(names) and b"\0" in names[name:], "symbol name bounds")
            label = names[name:names.index(0, name)].decode("ascii")
            require(ndx and label not in symbols, "undefined or duplicate symbol")
            symbols[label] = {"address": value, "bytes": length, "type": info & 15}
    regions.sort()
    require(regions and regions[0][0] == ADDRESS and regions[-1][1] == NEW_END and
            all(a[1] == b[0] for a, b in zip(regions, regions[1:])), "payload coverage")
    expected = ((ADDRESS, 54), (ADDRESS+54, 192), (NEW_END-54, 54), (original.RESUME, 0))
    for name, (address, size) in zip(NAMES, expected):
        require(name in symbols and symbols[name]["address"] == address and
                symbols[name]["bytes"] == size, "unexpected symbol layout: "+name)
    payload = raw[p[1]:p[1]+p[4]]
    return payload, symbols, verify_minimal_delta(old, payload)


def verify_flow(payload: bytes, symbols: dict, hook) -> dict:
    """Run all input subsets and releases against the assembled instructions."""
    rows = original.instructions(payload, ADDRESS, ADDRESS, NEW_END)
    entry = original.instructions(hook.after, original.HOOK, original.HOOK, original.RESUME)
    code = {row["address"]: row for row in rows+entry}
    names = {name: symbol["address"] for name, symbol in symbols.items()}
    cases = 0
    counts = {"constant_levels": 0, "configuration_faults": 0,
              "all_released_at_each_sample": 0, "changing_held_subset": 0}

    def check(levels, direction, seed, alias, held, *, samples=None, fault=None, group):
        nonlocal cases
        machine = previous.PolicyMachine(code, names, ADDRESS, seed, levels, direction,
                                         alias=alias, fault=fault)
        require(machine.run() == ("reset_wait" if held else "startup_resume"), "wrong recovery outcome")
        machine.check_gpio_restore()
        require(machine.stack_top-machine.min_sp == 100, "stack bound changed")
        require(machine.writes[19][0] == original.PORT+8 and machine.syncs[0] == 20,
                "input policy ordering changed")
        if samples is not None:
            require(machine.samples == samples, "sample termination count differs")
        if held:
            marker = b"".join(struct.pack("<I", machine.memory[original.MAILBOX+i]) for i in range(0, 16, 4))
            require(marker == b"usb_update_mode\0" and
                    machine.writes[-1] == (original.RESET, machine.reset_word | 16),
                    "ROM marker/reset changed")
            require(machine.samples == 32 and machine.delay_iterations == 3300000,
                    "held sample/loop count changed")
            require(machine.syncs[-2:] == [len(machine.writes)-1, len(machine.writes)], "reset barriers changed")
        else:
            for name in [*(f"r{i}" for i in range(16)), "psr", "rets", "reti"]:
                require(machine.regs[name] == machine.original_regs[name], "context lost: "+name)
            require((machine.regs["sp"], machine.regs["ssp"]) ==
                    (original.SSP if alias else original.SP, original.SSP), "startup stacks differ")
            require(not any(original.MAILBOX <= a < original.MAILBOX+16 or a == original.RESET
                            for a, _ in machine.writes), "ordinary startup writes recovery marker/reset")
        cases += 1
        counts[group] += 1

    pinmask = lambda bits: sum(((bits >> i) & 1) << pin for i, pin in enumerate((0, 3, 10)))
    for alias in (False, True):
        for direction in range(8):
            for levels in range(8):
                for seed in range(4):
                    check([pinmask(levels) | 0xA5000000], pinmask(direction), seed, alias, levels != 7,
                          samples=1 if levels == 7 else 32, group="constant_levels")
            for fault in original.CONFIG:
                check([0], pinmask(direction), 11, alias, False, samples=0, fault=fault,
                      group="configuration_faults")
        for subset in range(7):
            for position in range(32):
                check([pinmask(subset)]*position+[original.MASK]+[0]*32, 0, position, alias,
                      False, samples=position+1, group="all_released_at_each_sample")
            # A different nonempty pressed subset at every sample is accepted.
            # There need not be one physical input held throughout the window.
            check([pinmask((subset+i) % 7) for i in range(32)], 0, subset, alias, True,
                  samples=32, group="changing_held_subset")
    return {"cases": cases, **counts, "maximum_stack_bytes": 100,
            "initial_direction_combinations": 8, "input_level_combinations": 8,
            "SP_alias_models": 2, "all_GPRs_PSR_RETS_RETI_restored_on_resume": True,
            "foreign_GPIO_bits_preserved": True, "selected_direction_remains_input": True,
            "hardware_timing_or_electrical_simulation": False,
            "limits": ["Delay loops are counted, not timed.",
                       "Matched push/pop frames do not independently prove physical stack order.",
                       "PSR disturbance checks restoration, not CPU arithmetic-flag behavior.",
                       "A changing held subset is accepted; this is not same-pin debounce."]}
