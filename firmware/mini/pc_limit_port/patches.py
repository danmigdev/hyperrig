"""Extend G's shared flash PC range to the exact appended application end.

This module produces one asserted binary patch, never an image or device I/O.
The two reset-copy source literals that happen to equal text_rodata_end stay
unchanged. Debug/stack/write protections and the RAM execution range stay on.
"""
from __future__ import annotations

import hashlib
import re
import struct

from hyperrig.jieli import unpack_app
from tools.audit_mini_boot_contract import instructions
from tools.audit_mini_ultrarig_port import BinaryPatch
from tools.disassemble import codec, table

BASE = 0x02000000
ENTRY = 0x02000120
ORIGINAL_END = 0x02056780
APPEND_START = 0x02076AAC
MAX_END = 0x0207DE80
PATCH_ADDRESS = 0x0200067E
BEFORE = bytes.fromhex('c1ff80670502')
G_SHA = '2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334'
COPY_SITES = (0x020001B8, 0x020001DC)
LIMIT_REGISTERS = (0x01EEE380, 0x01EEE384, 0x01EEE388, 0x01EEE38C)
DEBUG_RANGE = (0x02000628, 0x02000730)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_end(executable_end):
    require(type(executable_end) is int and not executable_end % 2 and
            APPEND_START < executable_end <= MAX_END,
            'executable end must be the bounded, even appended application end')
    return executable_end


def consumer_inventory(g_plain):
    require(sha(g_plain) == G_SHA, 'not the pinned original G plaintext')
    needle = struct.pack('<I', ORIGINAL_END)
    offsets, cursor = [], 0
    while (cursor := g_plain.find(needle, cursor)) >= 0:
        offsets.append(BASE + cursor)
        cursor += 1
    require(offsets == [site + 2 for site in (*COPY_SITES, PATCH_ADDRESS)],
            'original text-end literal consumers changed')
    for site in (*COPY_SITES, PATCH_ADDRESS):
        require(g_plain[site-BASE:site-BASE+6] == BEFORE,
                'text-end instruction preimage differs')
        row, = instructions(g_plain, BASE, site, site+6)
        require(row['id'] == 'li.u32' and row['fields'] == {'r': 1, 'n': ORIGINAL_END},
                'unexpected literal consumer instruction')
    return [
        {'instruction': COPY_SITES[0], 'literal': COPY_SITES[0]+2,
         'role': 'original RAM copy source', 'patch': False},
        {'instruction': COPY_SITES[1], 'literal': COPY_SITES[1]+2,
         'role': 'original RAM copy source', 'patch': False},
        {'instruction': PATCH_ADDRESS, 'literal': PATCH_ADDRESS+2,
         'role': 'shared PC_LIMIT0_H initialized by CPU1', 'patch': True},
    ]


def pc_limit_patches(g_plain: bytes, executable_end: int) -> tuple[BinaryPatch, ...]:
    """The composer must pass ENTRY + final app.bin size, including the guard."""
    consumer_inventory(g_plain)
    checked_end(executable_end)
    isa = table.load()
    ins = next(item for item in isa.insns if item.id == 'li.u32')
    after = codec.encode(ins, {'r': 1, 'n': executable_end})
    decoded, fields, size = codec.decode(isa, after)
    require(size == 6 and decoded.id == 'li.u32' and
            fields == {'r': 1, 'n': executable_end}, 'PC limit encoding roundtrip')
    return (BinaryPatch('mini_appended_flash_pc_limit', PATCH_ADDRESS, BEFORE, after,
        'Extend the shared flash execution range through the exact appended app/guard end. '
        'Preserve the original RAM-copy source, RAM execution range and all debug enables.'),)


def simulate_limit_setup(plain: bytes, cpu: int) -> dict:
    """Execute only the decoded PC-limit setup fragment with fake MMIO.

    Entry values follow the preceding real instructions: r5=EMU_CON0 and
    r7=cnum. Both exits are checked. This is not an emulator of debug hardware.
    Parallel assignment/store pairs read the register values before the pair.
    """
    require(type(cpu) is int and cpu in (0, 1), 'only the two actual CPUs')
    rows = instructions(plain, BASE, 0x0200066C, 0x020006A2)
    code = {row['address']: row for row in rows}
    regs = {f'r{i}': 0xBAD00000+i for i in range(16)}
    regs.update(r4=0, r5=0x01EEF0D0, r7=cpu)
    pc, writes, visited = 0x0200066C, [], []

    def effect(row, source):
        text = row['text'].removesuffix('  #')
        if m := re.fullmatch(r'(r\d+) = (r\d+) \+ (-?\d+)', text):
            return (m[1], (source[m[2]] + int(m[3])) & 0xFFFFFFFF)
        if m := re.fullmatch(r'(r\d+) = (-?\d+)', text):
            return (m[1], int(m[2]) & 0xFFFFFFFF)
        if m := re.fullmatch(r'\[(r\d+)\+(\d+)\] = (r\d+)', text):
            writes.append({'instruction': row['address'],
                           'address': source[m[1]]+int(m[2]), 'value': source[m[3]]})
            return None
        raise ValueError('unsupported limit-setup instruction: '+text)

    for _ in range(24):
        if pc in (0x020006A0, 0x020006C8):
            return {'cpu': cpu, 'exit': pc, 'writes': writes, 'visited': visited,
                    'PC_limits': {str(w['address']): w['value'] for w in writes
                                  if w['address'] in LIMIT_REGISTERS}}
        require(pc in code, 'limit setup escaped the modeled fragment')
        row = code[pc]; visited.append(pc)
        text = row['text']; next_pc = pc+row['size']
        if row['id'] == 'beqz':
            require(row['fields']['r'] == 7 and row['target'] == 0x020006C8,
                    'CPU selector branch differs')
            if not regs['r7']: next_pc = row['target']
        elif text.endswith('  #'):
            source = dict(regs); update = effect(row, source)
            second = code[next_pc]
            require(second['id'] == 'st.w', 'unexpected parallel partner')
            require(effect(second, source) is None, 'parallel store mutates registers')
            visited.append(next_pc); next_pc += second['size']
            if update: regs[update[0]] = update[1]
        else:
            update = effect(row, regs)
            if update: regs[update[0]] = update[1]
        pc = next_pc
    raise ValueError('limit setup exceeded instruction budget')


def verify_candidate(raw: bytes, *, executable_end: int, g_plain: bytes) -> dict:
    """Reject stale/broad limits and require the current JLFS app end exactly."""
    patch, = pc_limit_patches(g_plain, executable_end)
    plain, _, files = unpack_app(raw)
    require(ENTRY+len(files['app.bin']) == executable_end,
            'PC high limit differs from actual final app.bin end')
    off = PATCH_ADDRESS-BASE
    require(plain[off:off+6] == patch.after, 'candidate PC-limit patch absent or stale')
    for site in COPY_SITES:
        require(plain[site-BASE:site-BASE+6] == BEFORE, 'RAM copy source was changed')
    lo, hi = DEBUG_RANGE
    reverted = bytearray(plain[lo-BASE:hi-BASE])
    reverted[PATCH_ADDRESS-lo:PATCH_ADDRESS-lo+6] = BEFORE
    require(reverted == g_plain[lo-BASE:hi-BASE], 'other debug/protection code changed')
    cases = [simulate_limit_setup(plain, cpu) for cpu in (0, 1)]
    require(cases[0]['PC_limits'] == {}, 'CPU0 unexpectedly programs PC ranges')
    require(cases[1]['PC_limits'] == dict(zip(map(str, LIMIT_REGISTERS),
                (executable_end, ENTRY, 0x01C1F088, 0x01C00000))),
            'decoded target PC limits differ')
    return {'image_sha256': sha(raw), 'executable_end': executable_end,
            'actual_app_end_matches_limit': True, 'patch': patch.record(),
            'decoded_setup': cases, 'RAM_copy_sources_unchanged': True,
            'debug_and_stack_protection_unchanged': True,
            'new_image_hardware_tested': False, 'audio_verified': False}
