"""Compile and inspect the normal-call stack bridge. No device or USB access.

The instruction simulation assumes a conforming C callback; it does not emulate
the DSP callback, interrupts, mode switching, the ROM, or physical RAM/cache.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from pi32v2isa import codec, table

NAME = 'hyperrig_mini_rom_run_on_stack'
SLOTS = (0x01C20000, 0x01C28000)
SPAN, STACK, GUARD = 0x8000, 4096, 32
EXPECTED = ['[--sp] = {rets, r4}', 'r4 = sp', 'r3 = r0', 'sp = r2',
            'r0 = r1', 'call r3', 'sp = r4', '{rets, r4} = [sp++]', 'rts']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def elf(raw):
    check(raw[:7] == b'\x7fELF\x01\x01\x01', 'expected ELF32 little endian')
    h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    check(h[1] == 0xf1 and h[10] == 40, 'wrong machine or section size')
    sections = [struct.unpack_from('<10I', raw, h[5] + i * 40) for i in range(h[11])]
    symbols = {}
    for sec in sections:
        check(sec[1] != 4 or sec[5] == 0, 'bridge unexpectedly has relocations')
        if sec[1] != 2:
            continue
        names_sec = sections[sec[6]]
        names = raw[names_sec[4]:names_sec[4] + names_sec[5]]
        for off in range(sec[4], sec[4] + sec[5], sec[9]):
            key, address, size, info, other, index = struct.unpack_from('<IIIBBH', raw, off)
            if not key:
                continue
            name = names[key:names.index(0, key)].decode('ascii')
            check(index or info >> 4 not in (1, 2), 'unresolved symbol ' + name)
            if index:
                symbols[name] = (address, size, index)
    address, size, section_index = symbols[NAME]
    section = sections[section_index]
    start = section[4] + address - section[3]
    code = raw[start:start + size]
    check(len(code) == size == 24, 'unexpected bridge extent')
    return h, sections, symbols, code


def decode(raw):
    instructions, offset, rows = table.load(), 0, []
    while offset < len(raw):
        decoded = codec.decode(instructions, raw, offset)
        check(decoded is not None, 'unknown instruction encoding')
        instruction, fields, length = decoded
        text = codec.format(instruction, fields)
        check(not instruction.block and not text.endswith('  #'), 'unexpected parallel or block form')
        rows.append({'offset': offset, 'length': length, 'id': instruction.id,
                     'text': text, 'hex': raw[offset:offset + length].hex()})
        offset += length
    check([r['text'] for r in rows] == EXPECTED, 'bridge instruction contract changed')
    return rows


def validate_stack_layout(base, code_end, guard, bottom, top):
    """Reusable static contract for a guarded 4 KiB stack in either ROM slot."""
    check(base in SLOTS, 'unproven ROM slot')
    check(base <= code_end <= guard, 'stack overlaps code/data/BSS')
    check(guard + GUARD == bottom and bottom + STACK == top, 'wrong guard or stack size')
    check(guard % 8 == 0 and bottom % 8 == 0 and top % 8 == 0, 'stack alignment')
    check(base <= guard < bottom < top <= base + SPAN, 'stack leaves its ROM slot')


def simulate(rows, base, incoming_sp, depth, result, active_stack, seed):
    """Interpret the nine decoded instructions; callback effect is an ABI model."""
    rng = random.Random(seed)
    regs = {f'r{i}': rng.getrandbits(32) for i in range(16)}
    top, bottom = base + SPAN, base + SPAN - STACK
    callback, argument = base + 0x100, rng.getrandbits(32)
    regs.update(r0=callback, r1=argument, r2=top, sp=incoming_sp,
                rets=0x00102244, ssp=0x01c01000, usp=0x01c01200,
                icfg=rng.getrandbits(32), psr=rng.getrandbits(32),
                reti=0x00104466, retx=0x00106688, rete=0x001088aa)
    regs[active_stack] = incoming_sp
    before = dict(regs)
    memory, writes = {}, []

    def write(address, value):
        check(address % 4 == 0, 'unaligned stack access')
        check(incoming_sp - 8 <= address < incoming_sp or bottom <= address <= top - 4,
              'stack write outside owned bounds')
        memory[address] = value & 0xffffffff
        writes.append(address)

    def move(destination, source):
        regs[destination] = regs[source]
        if destination == 'sp':
            regs[active_stack] = regs[source]

    for row in rows:
        ins = row['text']
        if ins == '[--sp] = {rets, r4}':
            write(regs['sp'] - 4, regs['rets'])
            write(regs['sp'] - 8, regs['r4'])
            regs['sp'] -= 8
            regs[active_stack] = regs['sp']
        elif ins == 'call r3':
            check(regs['r3'] == callback and regs['r0'] == argument, 'callback/argument corrupted')
            check(regs['sp'] == top, 'callback did not receive private top')
            regs['rets'] = base + row['offset'] + row['length']
            check(depth % 4 == 0, 'callback model depth must be a word multiple')
            # Assumed callback obeys C ABI: r4..r15 survive; r0..r3 may change.
            # Fill every word it uses, then return without leaking its frame.
            for address in range(top - depth, top, 4):
                write(address, rng.getrandbits(32))
            for i in range(4):
                regs[f'r{i}'] = rng.getrandbits(32)
            regs['r0'] = result & 0xffffffff
            # Ordinary C callbacks may change the arithmetic condition flags.
            regs['psr'] = (regs['psr'] & ~15) | rng.randrange(16)
        elif ins == '{rets, r4} = [sp++]':
            regs['r4'] = memory[regs['sp']]
            regs['rets'] = memory[regs['sp'] + 4]
            regs['sp'] += 8
            regs[active_stack] = regs['sp']
        elif ins == 'rts':
            regs['pc'] = regs['rets']
        else:
            destination, source = ins.split(' = ')
            move(destination, source)
    check(all(regs[f'r{i}'] == before[f'r{i}'] for i in range(4, 16)), 'saved GPR corrupted')
    for name in ('sp', 'rets', 'ssp', 'usp', 'icfg', 'reti', 'retx', 'rete'):
        check(regs[name] == before[name], name + ' not restored in the model')
    check(regs['psr'] & ~15 == before['psr'] & ~15, 'callback model changed execution mode')
    check(regs['pc'] == before['rets'] and regs['r0'] == result & 0xffffffff,
          'return address/result changed')
    check(set(writes) - set(range(bottom, top, 4)) == {incoming_sp - 8, incoming_sp - 4},
          'bridge touched more than the 8-byte incoming save frame')


def main():
    out = ROOT / 'build/mini-rom-stack'
    out.mkdir(parents=True, exist_ok=True)
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
    vendor = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'

    def run(args):
        p = subprocess.run(prefix + args, cwd=ROOT, capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(p.stdout + p.stderr)
        return p.stdout

    source = 'firmware/mini/rom_stack/rom_stack_pi32v2.S'
    obj = 'build/mini-rom-stack/rom_stack.o'
    run([vendor + 'clang', '-target', 'pi32v2', '-mcpu=r3', '-c', source, '-o', obj])
    _, _, _, code = elf((ROOT / obj).read_bytes())
    rows = decode(code)
    (out / 'rom_stack.asm').write_text(run([vendor + 'objdump', '-d', obj]), encoding='utf-8')
    fixture = '''/* Compiler evidence only: not linked into a ROM payload. */
int dynamic_frame(int (*fn)(void *), void *arg, unsigned n) {
    volatile unsigned *p = __builtin_alloca(n * sizeof(*p));
    p[0] = n;
    int result = fn(arg);
    return result + (int)p[0];
}
'''
    (out / 'abi_frame.c').write_text(fixture, encoding='utf-8')
    run([vendor + 'clang', '-target', 'pi32v2', '-mcpu=r3', '-O2', '-ffreestanding',
         '-fno-builtin', '-c', 'build/mini-rom-stack/abi_frame.c', '-o', 'build/mini-rom-stack/abi_frame.o'])
    evidence = run([vendor + 'objdump', '-d', 'build/mini-rom-stack/abi_frame.o'])
    check('r7 = sp' in evidence and 'sp = r7' in evidence and 'call r' in evidence,
          'vendor compiler no longer uses saved-frame SP restoration')
    (out / 'abi_frame.asm').write_text(evidence, encoding='utf-8')
    script = '''/* Audit fixture, not a ROM service entry and not uploaded. */
ENTRY(hyperrig_mini_rom_run_on_stack)
MEMORY { SLOT (rwx) : ORIGIN = AUDIT_BASE, LENGTH = 0x8000 }
PHDRS { image PT_LOAD FLAGS(7); }
SECTIONS {
 .text ORIGIN(SLOT) : { *(.text*) . = ALIGN(8); __code_end = .; } > SLOT :image
 .stack ORIGIN(SLOT) + LENGTH(SLOT) - 0x1020 (NOLOAD) : {
  __guard = .; . += 32; __bottom = .; . += 4096; __top = .;
 } > SLOT :image
 ASSERT(__code_end <= __guard, "stack overlap")
 ASSERT(__top == ORIGIN(SLOT) + LENGTH(SLOT), "stack leaves slot")
 /DISCARD/ : { *(.comment .note* .eh_frame* .llvm_addrsig) }
}
'''
    (out / 'audit.ld').write_text(script, encoding='utf-8')
    layouts = []
    for base in SLOTS:
        path = f'build/mini-rom-stack/audit-{base:08x}.elf'
        run([vendor + 'ld', '-z', 'max-page-size=0x20', '-z', 'common-page-size=0x20',
             '--defsym', f'AUDIT_BASE={base}', '-T', 'build/mini-rom-stack/audit.ld', obj, '-o', path])
        raw = (ROOT / path).read_bytes()
        h, sections, symbols, linked = elf(raw)
        check(h[0] == 2 and h[3] == base and linked == code, 'link changed bridge or entry')
        addresses = [symbols[n][0] for n in ('__code_end', '__guard', '__bottom', '__top')]
        validate_stack_layout(base, *addresses)
        for sec in sections:
            if sec[2] & 2:
                check(base <= sec[3] <= base + SPAN and sec[5] <= base + SPAN - sec[3],
                      'allocated section outside slot')
        layouts.append({'elf': path, 'sha256': sha(raw), 'slot': base,
                        'code_end': addresses[0], 'guard': addresses[1],
                        'stack_bottom': addresses[2], 'stack_top': addresses[3]})
    cases = 0
    for base in SLOTS:
        for active in ('ssp', 'usp'):
            for offset in (0, 4, 8, 60):
                for depth in (0, 4, 1228, 2048, 4096):
                    for result in (0, -1, 0x12345678):
                        simulate(rows, base, 0x1c01800 + offset, depth, result, active, cases)
                        cases += 1
    rejected = 0
    for mutation in ((0x1c30000, 0x1c30018, 0x1c36fe0, 0x1c37000, 0x1c38000),
                     (SLOTS[0], SLOTS[0] + 0x7000, SLOTS[0] + 0x6fe0, SLOTS[0] + 0x7000, SLOTS[0] + 0x8000),
                     (SLOTS[0], SLOTS[0] + 24, SLOTS[0] + 0x6fe4, SLOTS[0] + 0x7004, SLOTS[0] + 0x8004),
                     (SLOTS[0], SLOTS[0] + 24, SLOTS[0] + 0x7020, SLOTS[0] + 0x7040, SLOTS[0] + 0x8040)):
        try:
            validate_stack_layout(*mutation)
        except ValueError:
            rejected += 1
        else:
            raise ValueError('invalid stack layout accepted')
    try:
        simulate(rows, SLOTS[0], 0x1c01800, 4100, 0, 'ssp', 0)
    except ValueError:
        rejected += 1
    else:
        raise ValueError('callback overflow was not detected by bounded model')
    sources = [ROOT / source, ROOT / 'firmware/mini/rom_stack/rom_stack.h', Path(__file__),
               ROOT / 'upstream/pi32v2-isa/docs/ABI.md', ROOT / 'upstream/pi32v2-isa/docs/ISA.md',
               ROOT / 'upstream/pi32v2-isa/tools/hwtest/runner.S', ROOT / 'upstream/m-bootloader/docs/SPEC.md']
    report = {
        'project': 'HyperRig', 'type': 'pi32v2 normal-call private-stack bridge',
        'api': 'int hyperrig_mini_rom_run_on_stack(int (*fn)(void *), void *arg, void *top)',
        'object': obj, 'object_sha256': sha((ROOT / obj).read_bytes()),
        'code_bytes': len(code), 'code_sha256': sha(code), 'instructions': rows,
        'incoming_stack_bytes': 8, 'own_callback_stack_bytes': STACK,
        'static_fixture_guard_bytes': GUARD, 'static_fixture_layouts': layouts,
        'instruction_simulation': {'passed': True, 'cases': cases, 'rejections': rejected,
                                   'callback_is_assumed_abi_model': True, 'hardware_emulation': False},
        'compiler_dynamic_frame_evidence': {'source': 'build/mini-rom-stack/abi_frame.c',
                                           'source_sha256': sha(fixture.encode()),
                                           'disassembly_sha256': sha(evidence.encode())},
        'additional_ram_proven_free_while_returning_to_rom': [],
        'hardware_execution_verified': False,
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources},
        'limits': ['Callback must obey the normal C ABI and return normally; no ROM callback while on private stack.',
                   'Arithmetic condition flags and caller-clobbered r1..r3 are not preserved across the callback.',
                   'The assembly does not check pointers, overlap, bounds, recursion or stack overflow.',
                   '4096 bytes is a reservation, not a proof of the complete DSP call-chain worst-case depth.',
                   'No explicit SSP/USP/ICFG, interrupt-enable, clock, MMIO or cache instruction is emitted.',
                   'SP may alias SSP or USP in the inherited mode. The simulation checks either alias; hardware mode semantics are not established.',
                   'Interrupt nesting and hidden CPU state are not simulated; inherited IRQ stack consumption remains unmeasured.',
                   'Audit ELF files are not ROM plug-ins and must not be sent to the device.',
                   'm-bootloader SPEC 2.1 and 13 do not establish exact ROM-owned RAM bounds. Larger stage/app RAM contracts require a different lifecycle.']}
    (ROOT / 'research/mini-rom-stack.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'code_bytes': len(code), 'instruction_cases': cases, 'negative_cases': rejected,
                      'layouts': layouts, 'hardware_execution': False}, indent=2))


if __name__ == '__main__':
    main()
