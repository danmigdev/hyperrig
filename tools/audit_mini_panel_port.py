"""Pinned, offline panel adaptation for the integral UltraRig G -> MINI port.

No transport is imported. The exported patches are not an installation image.
The MINI stock image supplies pin evidence only; G's event/action engine stays.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.audit_mini_ultrarig_port import BinaryPatch, G_PATH, G_SHA, MINI_PATH, MINI_SHA
from tools.disassemble import codec, relative_target, table

BASE = 0x02000000
G_PLAIN_SHA = '2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334'
RAM_SOURCE, RAM_BASE, RAM_SIZE = 0x02056780, 0x01C00000, 131852
GLOBAL, STATE = 0x01C1F180, 0x01C26890
WRITER, CACHE = 0x02015858, GLOBAL + 136
MAP_VMA, MAP_LMA = GLOBAL + 116, 0x02075974
IRQ_LIMIT_VMA, IRQ_LIMIT_LMA = 0x01C03338, 0x02059AB8
ISA = table.load()
INS = {i.id: i for i in ISA.insns}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(name, **fields):
    data = codec.encode(INS[name], fields)
    decoded = codec.decode(ISA, data)
    require(decoded is not None and decoded[0].id == name and decoded[1] == fields,
            'instruction encoding did not roundtrip: ' + name)
    return data


def fragment(blob, start, end, *, mapped_base=BASE):
    rows = []
    while start < end:
        got = codec.decode(ISA, blob, start - mapped_base)
        require(got is not None, f'undecodable instruction at {start:#x}')
        ins, fields, size = got
        require(start + size <= end, 'fragment ends inside instruction')
        text = codec.format(ins, fields)
        row = {'address': start, 'bytes': blob[start-mapped_base:start-mapped_base+size].hex(),
               'instruction': ins.id, 'fields': fields, 'assembly': text}
        target = relative_target(start, size, text)
        if target is not None:
            row['direct_target'] = target
        rows.append(row)
        start += size
    return rows


def _limit_patch(g, name, address, runtime_address, register, target):
    before = g[address-BASE:address-BASE+4]
    ins, fields, size = codec.decode(ISA, before)
    require(ins.id == 'bne.ri' and size == 4 and fields['i'] == 5 and fields['r'] == register,
            name + ': loop contract changed')
    require(relative_target(runtime_address, size, codec.format(ins, fields)) == target,
            name + ': branch target changed')
    after_fields = dict(fields, i=3)
    return BinaryPatch(name, address, before, encode(ins.id, **after_fields),
                       'Limit the same loop to three physical MINI switches; retain branch/register fields.')


def panel_patches(g: bytes) -> tuple[BinaryPatch, ...]:
    """Return equal-length BinaryPatch objects for compose_candidate().

    Addresses of copied RAM/data are their FLASH LOAD addresses. No patch
    changes the original RTOS, DSP, app protocol or four-slot action storage.
    Call with the untouched, decoded, pinned G application area.
    """
    require(sha(g) == G_PLAIN_SHA, 'panel source must be untouched pinned G decoded app area')
    require(MAP_LMA == MAP_VMA - RAM_BASE + RAM_SOURCE, 'map relocation mismatch')
    require(IRQ_LIMIT_LMA == IRQ_LIMIT_VMA - RAM_BASE + RAM_SOURCE, 'IRQ relocation mismatch')
    # Cache the requested frame, as the original caller expects, without GPIO.
    # r1 is caller-saved; no stack or special-register modification is needed.
    stub = (encode('li.u32', r=1, n=CACHE) + encode('st.w', d=0, b=1, n=0)
            + encode('rts') + encode('nop'))
    patches = [
        BinaryPatch('mini_panel_serial_writer_disabled', WRITER,
                    bytes.fromhex('7704c3ff80f1c101d0ec3818'), stub,
                    'Replace entry by RAM-cache store and normal return; no PA0..3 access. LED driver is pending.'),
        BinaryPatch('mini_panel_input_banks', 0x020365D0,
                    struct.pack('<3I', *([0x501C0] * 3)), struct.pack('<3I', *([0x50000] * 3)),
                    'First three physical inputs use port A; inaccessible G slots 3/4 are retained in the file.'),
        BinaryPatch('mini_panel_input_bits', 0x020359F0, bytes((6, 7, 8)), bytes((10, 0, 3)),
                    'MINI stock scan order PA10, PA0, PA3; active low. Physical label order is unmeasured.'),
        _limit_patch(g, 'mini_panel_init_three', 0x0201599C, 0x0201599C, 0, 0x02015964),
        _limit_patch(g, 'mini_panel_poll_three', 0x02015AD0, 0x02015AD0, 4, 0x02015A6A),
        _limit_patch(g, 'mini_panel_irq_three', IRQ_LIMIT_LMA, IRQ_LIMIT_VMA, 4, 0x01C032BE),
        BinaryPatch('mini_panel_logical_default', MAP_LMA, bytes((4, 3, 1, 0)), bytes((0, 1, 2, 3)),
                    'Logical A/B/C map to physical scan indices 0/1/2; D maps to an inactive, valid state slot 3.'),
        BinaryPatch('mini_panel_restore_fixed_map', 0x02003F32,
                    bytes.fromhex('d8ee0021'), encode('mov.rr', x=2, y=1) + encode('nop'),
                    'Configuration restore uses its index as mapping value; a persisted G permutation cannot replace MINI wiring.'),
        BinaryPatch('mini_panel_skip_G_analog_init', 0x020159C2,
                    bytes.fromhex('bfeabaf5'), encode('goto.l', n=(0x020159FC-0x020159C6)//2),
                    'Skip G PB1/PC6..8 initialization and initial ADC samples; preserve prior RAM initialization and following epilogue.'),
        BinaryPatch('mini_panel_G_analog_scan_disabled', 0x02015A00,
                    bytes.fromhex('4121'), encode('li.u8', r=1, n=0),
                    'Keep state+832 zero: gates panel ADC/mux block and CE8E -> CDE0 initialization path. Knobs/expression pending.'),
    ]
    covered = set()
    for p in patches:
        require(len(p.before) == len(p.after), p.name + ': unequal length')
        off = p.address - BASE
        require(g[off:off+len(p.before)] == p.before, p.name + ': preimage mismatch')
        indices = set(range(off, off + len(p.before)))
        require(not covered & indices, 'overlapping panel patches')
        covered |= indices
    return tuple(patches)


def apply_for_check(g, patches):
    result = bytearray(g)
    for p in patches:
        off = p.address - BASE
        require(result[off:off+len(p.before)] == p.before, p.name + ': check preimage')
        result[off:off+len(p.before)] = p.after
    return bytes(result)


def direct_reference_candidates(g, targets):
    """Linear decoded candidates in both load regions, not a whole-program CFG.

    Positive sites used as evidence are then decoded in their function context.
    Embedded data and computed branches prevent a claim of exhaustive callers.
    """
    first = [(i, i.mask >> (i.nbits-16), i.value >> (i.nbits-16)) for i in ISA.insns]
    cache = {}
    found = []
    for data, base in ((g[0x120:RAM_SOURCE-BASE], BASE+0x120),
                       (g[RAM_SOURCE-BASE:RAM_SOURCE-BASE+RAM_SIZE], RAM_BASE)):
        off = 0
        while off < len(data)-1:
            word = int.from_bytes(data[off:off+2], 'little')
            if word not in cache:
                cache[word] = SimpleNamespace(insns=[i for i, mask, value in first if word & mask == value])
            got = codec.decode(cache[word], data, off)
            size = got[2] if got else 2
            if got:
                text = codec.format(got[0], got[1])
                target = relative_target(base+off, size, text)
                if target in targets:
                    found.append({'address': base+off, 'target': target, 'assembly': text,
                                  'bytes': data[off:off+size].hex()})
            off += size
    return found


def _mini_machine(blob, start, stop, registers, memory, *, step_limit=500):
    """Execute only the simple instructions in three audited patch fragments.

    Memory is a Python dictionary. No real MMIO occurs. Unsupported instructions
    fail; this is not an emulator of the firmware, IRQ scheduling or peripherals.
    """
    regs = list(registers)
    writes, reads = [], []
    pc = start
    for steps in range(1, step_limit+1):
        if pc == stop:
            return regs, memory, writes, reads, steps-1
        got = codec.decode(ISA, blob, pc-BASE)
        require(got is not None, 'model decode failure')
        ins, f, size = got
        text = codec.format(ins, f)
        next_pc = pc+size

        def read(addr, width):
            reads.append((addr, width))
            return sum(memory.get(addr+j, 0) << (8*j) for j in range(width))

        def write(addr, value, width):
            writes.append((addr, value & ((1 << (8*width))-1), width))
            for j in range(width):
                memory[addr+j] = (value >> (8*j)) & 255

        if ins.id == 'nop':
            pass
        elif ins.id == 'rts':
            return regs, memory, writes, reads, steps
        elif ins.id in ('li.u8', 'li.u32', 'li.s16', 'li.neg5'):
            match = re.fullmatch(r'r(\d+) = (-?\d+)', text)
            require(match is not None, 'model immediate')
            regs[int(match[1])] = int(match[2]) & 0xFFFFFFFF
        elif ins.id == 'mov.rr':
            regs[f['x']] = regs[f['y']]
        elif (m := re.fullmatch(r'r(\d+) = r(\d+) \+ (\d+)', text)):
            regs[int(m[1])] = (regs[int(m[2])] + int(m[3])) & 0xFFFFFFFF
        elif (m := re.fullmatch(r'r(\d+) = r(\d+) \+ r(\d+)', text)):
            regs[int(m[1])] = (regs[int(m[2])] + regs[int(m[3])]) & 0xFFFFFFFF
        elif (m := re.fullmatch(r'r(\d+) \+= (\d+)', text)):
            regs[int(m[1])] = (regs[int(m[1])] + int(m[2])) & 0xFFFFFFFF
        elif (m := re.fullmatch(r'r(\d+) = r(\d+) << r(\d+)', text)):
            regs[int(m[1])] = (regs[int(m[2])] << (regs[int(m[3])] & 31)) & 0xFFFFFFFF
        elif (m := re.fullmatch(r'r(\d+) = \[r(\d+)\+r(\d+)<<2\]', text)):
            regs[int(m[1])] = read(regs[int(m[2])] + 4*regs[int(m[3])], 4)
        elif (m := re.fullmatch(r'r(\d+) = b\[r(\d+)\+r(\d+)\] \(u\)', text)):
            regs[int(m[1])] = read(regs[int(m[2])] + regs[int(m[3])], 1)
        elif (m := re.fullmatch(r'r(\d+) = b\[r(\d+)\+(\d+)\] \(u\)', text)):
            regs[int(m[1])] = read(regs[int(m[2])] + int(m[3]), 1)
        elif (m := re.fullmatch(r'\[r(\d+)\+r(\d+)<<2\] = r(\d+)', text)):
            write(regs[int(m[1])] + 4*regs[int(m[2])], regs[int(m[3])], 4)
        elif (m := re.fullmatch(r'\[r(\d+)\+(\d+)\] = r(\d+)', text)):
            write(regs[int(m[1])] + int(m[2]), regs[int(m[3])], 4)
        elif (m := re.fullmatch(r'\[r(\d+)\+(\d+)\] (\|=|&=) (?:~\()?1 << r(\d+)\)?', text)):
            addr, bit = regs[int(m[1])]+int(m[2]), 1 << (regs[int(m[4])] & 31)
            old = read(addr, 4)
            write(addr, old | bit if m[3] == '|=' else old & ~bit, 4)
        elif ins.id == 'bne.ri':
            if regs[f['r']] != f['i']:
                next_pc = relative_target(pc, size, text)
        elif ins.id == 'if.ne.rr':
            require(f['t'] == 0 and f['e'] == 0, 'model only accepts one-instruction conditional block')
            if regs[f['r']] == regs[f['s']]:
                following = codec.decode(ISA, blob, next_pc-BASE)
                require(following is not None, 'conditional block decode failure')
                next_pc += following[2]
        elif ins.id in ('goto', 'goto.l') or text.startswith('goto '):
            next_pc = relative_target(pc, size, text)
        else:
            raise ValueError(f'model unsupported instruction at {pc:#x}: {text}')
        pc = next_pc
    raise ValueError('patch-fragment model instruction budget exceeded')


def self_check(g, patches):
    out = apply_for_check(g, patches)
    by_name = {p.name: p for p in patches}
    # Execute the actual replacement bytes, including arbitrary r0 bit patterns.
    for frame in (0, 1, 0x1FFFFFFF, 0xFFFFFFFF, 0x12345678):
        regs = [0xA0000000+i for i in range(16)]
        regs[0] = frame
        actual, _, writes, reads, _ = _mini_machine(out, WRITER, WRITER+12, regs, {})
        require(writes == [(CACHE, frame, 4)] and not reads, 'writer stub touches unexpected memory')
        require(actual[0] == frame and actual[2:] == regs[2:], 'writer stub violates register contract')
    # Actual init fragment; fake MMIO starts nonzero to expose collateral bits.
    mmio_cases = (0, 0xFFFFFFFF, 0x55555555, 0xAAAAAAAA)
    for pattern in mmio_cases:
        memory = {BASE+i: v for i, v in enumerate(out)}
        for offset in (8, 12, 16, 20):
            for j in range(4):
                memory[0x50000+offset+j] = (pattern >> (8*j)) & 255
        regs = [0]*16
        regs[13], regs[15] = STATE, 0x02035810
        _, memory, writes, _, _ = _mini_machine(out, 0x0201595A, 0x020159A0, regs, memory)
        require({a for a, _, _ in writes if 0x50000 <= a < 0x50200} ==
                {0x50008, 0x5000C, 0x50010, 0x50014}, 'init escaped port-A input registers')
        mask = (1 << 10) | 1 | (1 << 3)
        for offset in (8, 12, 16, 20):
            actual = sum(memory[0x50000+offset+j] << (8*j) for j in range(4))
            expected = pattern & ~mask if offset == 20 else pattern | mask
            require(actual == expected, 'input init alters non-switch bits')
            require((actual ^ pattern) & ((1 << 1) | (1 << 2)) == 0, 'input init alters codec pins')
        for i, bit in enumerate((10, 0, 3)):
            ptr = sum(memory[STATE+1964+4*i+j] << (8*j) for j in range(4))
            bits = sum(memory[STATE+1984+4*i+j] << (8*j) for j in range(4))
            require((ptr, bits) == (0x50004, 1 << bit), 'IRQ cached table mismatch')
    # The three branch conditions keep their original targets and register ABI.
    for name, vma, target in (
        ('mini_panel_init_three', 0x0201599C, 0x02015964),
        ('mini_panel_poll_three', 0x02015AD0, 0x02015A6A),
        ('mini_panel_irq_three', IRQ_LIMIT_VMA, 0x01C032BE),
    ):
        p = by_name[name]
        ins, fields, size = codec.decode(ISA, p.after)
        require(fields['i'] == 3 and relative_target(vma, size, codec.format(ins, fields)) == target,
                name + ': modified loop escaped')
    # All 8 simultaneous physical states, unrelated input bits varied 4 ways.
    # This tests the table/ownership model, not interrupt scheduling or debounce.
    for pressed in range(8):
        for noise in mmio_cases:
            raw = noise
            for i, pin in enumerate((10, 0, 3)):
                raw = (raw & ~(1 << pin)) if pressed & (1 << i) else (raw | (1 << pin))
            observed = sum((0 if raw & (1 << bit) else 1) << i
                           for i, bit in enumerate(out[0x359F0:0x359F3]))
            require(observed == pressed, 'physical button order/polarity mismatch')
            physical = [bool(observed & (1 << i)) for i in range(3)] + [False, False]
            logical = [physical[index] for index in out[MAP_LMA-BASE:MAP_LMA-BASE+4]]
            require(logical == physical[:4], 'logical D must have no physical source')
    # Execute the replacement config-load instruction for every serialized byte.
    for index in range(4):
        for persisted in range(256):
            regs = [0]*16
            regs[0], regs[1] = 0x100000, index
            actual, _, writes, reads, _ = _mini_machine(
                out, 0x02003F32, 0x02003F36, regs, {0x100000+index: persisted})
            require(actual[2] == index and not reads and not writes, 'G config remapping was not suppressed')
    # Execute the original G physical -> logical lookup, with original and new
    # RAM initialization bytes. In particular, MINI physical index 2 must now
    # resolve to C: in the unmodified G default it matched no logical switch.
    for mapping, expected in ((bytes((4,3,1,0)), (3,2,-1,1,0)),
                              (out[MAP_LMA-BASE:MAP_LMA-BASE+4], (0,1,2,3,-1))):
        for physical, logical in enumerate(expected):
            regs = [0]*16
            regs[0] = physical
            memory = {MAP_VMA+i: value for i, value in enumerate(mapping)}
            actual, _, writes, _, _ = _mini_machine(out, 0x02014C28, 0x02014C4C, regs, memory)
            require(actual[5] == logical & 0xFFFFFFFF and not writes, 'original dispatcher logical lookup mismatch')
    # Guard init branch target and flag store without emulating unreachable ADC.
    rows = fragment(out, 0x020159C2, 0x020159C6)
    require(rows[0].get('direct_target') == 0x020159FC, 'analog initialization skip target')
    require(fragment(out, 0x02015A00, 0x02015A02)[0]['assembly'] == 'r1 = 0', 'analog gate enabled')
    inverse = bytearray(out)
    for p in patches:
        inverse[p.address-BASE:p.address-BASE+len(p.before)] = p.before
    require(bytes(inverse) == g, 'inverse panel patches do not recover all original G bytes')
    bad = bytearray(g)
    bad[0x1599C] ^= 1
    rejected = 0
    for invalid in (bytes(bad), g[:-1], b''):
        try:
            panel_patches(invalid)
        except ValueError:
            rejected += 1
    require(rejected == 3, 'wrong source was accepted')
    return {'writer_byte_execution_cases': 5, 'input_init_byte_execution_cases': 4,
            'physical_state_table_cases': 32, 'config_restore_byte_execution_cases': 1024,
            'original_dispatcher_byte_execution_cases': 10,
            'loop_target_checks': 3, 'negative_source_cases': rejected,
            'full_original_byte_inverse': True, 'IRQ_or_RTOS_execution_emulated': False,
            'real_GPIO_accessed': False}


def main():
    raw, fwsc = (ROOT/G_PATH).read_bytes(), (ROOT/MINI_PATH).read_bytes()
    require(sha(raw) == G_SHA and sha(fwsc) == MINI_SHA, 'pinned container identity')
    g, _, _ = unpack_app(raw)
    _, contents = unpack_fwsc(fwsc)
    mini, _, _ = unpack_app(contents['flash.bin'][0x4000:])
    patches = panel_patches(g)
    verification = self_check(g, patches)
    refs = direct_reference_candidates(g, {WRITER, 0x020158C2, 0x02014C04,
        0x0201453A, 0x02014578, 0x0200CC1A, 0x0200CC40, 0x0200CDE0})
    writer_refs = [r for r in refs if r['target'] == WRITER]
    require([r['address'] for r in writer_refs] == [0x02017568], 'serial writer direct references changed')
    sdk = ROOT/'upstream/ac79-sdk-reference/include_lib/driver/cpu/wl82/asm/WL82.h'
    sdk_sha = '6f5a44f39282f66203d837a1c74c9d8197d2856547356fce8ed0d191318ff645'
    require(sha(sdk.read_bytes()) == sdk_sha, 'GPIO register reference changed')
    patched = apply_for_check(g, patches)
    report = {
        'project': 'HyperRig', 'scope': 'Whole original UltraRig-G application port: physical panel adaptation only',
        'sources': {'G_container_path': G_PATH, 'G_container_sha256': G_SHA, 'G_decoded_sha256': sha(g),
                    'MINI_fwsc_path': MINI_PATH, 'MINI_fwsc_sha256': MINI_SHA, 'MINI_decoded_sha256': sha(mini),
                    'GPIO_header_path': sdk.relative_to(ROOT).as_posix(), 'GPIO_header_sha256': sdk_sha,
                    'GPIO_header_url': 'https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/WL82.h'},
        'address_note': 'Patch CPU addresses are FLASH LOAD addresses in decoded app area. Copied IRQ/data also list their runtime VMA; raw NOR is encrypted.',
        'patches': [p.record() for p in patches],
        'patched_decoded_area_sha256_for_test_only': sha(patched),
        'copied_RAM': {'source': RAM_SOURCE, 'destination': RAM_BASE, 'bytes': RAM_SIZE,
            'IRQ_limit_VMA': IRQ_LIMIT_VMA, 'IRQ_limit_LMA': IRQ_LIMIT_LMA,
            'logical_map_VMA': MAP_VMA, 'logical_map_LMA': MAP_LMA},
        'original_startup_zeroing': {'start': 0x01C2030C, 'bytes': 97604,
            'end_exclusive': 0x01C2030C+97604,
            'inactive_raw_slots': [STATE+1552+3, STATE+1552+4, STATE+1567+3, STATE+1567+4],
            'evidence': fragment(g, 0x0200019C, 0x020001B2)},
        'serial_writer': {'entry': WRITER, 'end_exclusive': 0x020158C2, 'data_bits': 29,
            'signal_roles_inferred': {'PA0': 'latch', 'PA1': 'active-low enable', 'PA2': 'clock', 'PA3': 'serial data'},
            'chip_is_74HC595_electrically_proven': False,
            'known_MINI_conflict': 'PA1 codec SDA and PA2 codec SCL; PA0 and PA3 MINI switches',
            'caller': fragment(g, 0x0201755C, 0x02017570),
            'original': fragment(g, WRITER, 0x020158C2),
            'replacement': fragment(patched, WRITER, WRITER+12),
            'return_value_used_by_proven_caller': False, 'cache_word': CACHE,
            'replacement_mutations': ['one ordinary RAM word store', 'caller-saved r1'],
            'remaining_original_body_unreachable_from_entry': True},
        'inputs': {'G_bank_table': 0x020365D0, 'G_bit_table': 0x020359F0,
            'G_pins': ['PH6','PH7','PH8','PH9','PA10'], 'MINI_stock_scan_order': ['PA10','PA0','PA3'],
            'active_low_derived_from_stock_and_G': True, 'MINI_board_label_order_verified': False,
            'policy_logical_A_B_C': ['PA10','PA0','PA3'], 'logical_D': 'state slot 3, initially released, no physical scanner',
            'G_default_logical_map': [4,3,1,0], 'new_logical_map': [0,1,2,3],
            'four_action_slots_and_protocol_shape_retained': True,
            'config_restore_forces_identity_mapping': True,
            'init': fragment(g, 0x0201595A, 0x020159A0),
            'main_poll': fragment(g, 0x02015A58, 0x02015AD4),
            'irq_poll': fragment(g[RAM_SOURCE-BASE:RAM_SOURCE-BASE+RAM_SIZE], 0x01C032A6, 0x01C0333C, mapped_base=RAM_BASE),
            'dispatcher': fragment(g, 0x02014C04, 0x02014C50),
            'config_restore': fragment(g, 0x02003F28, 0x02003F48),
            'MINI_stock_init': fragment(mini, 0x02006096, 0x020060BA),
            'MINI_stock_read': fragment(mini, 0x0200A060, 0x0200A080),
            'debounce_original_G': {'main_different_samples': 4, 'IRQ_different_samples': 30, 'timings_measured': False}},
        'G_analog_controls': {'status': 'disabled pending MINI knob/expression mapping',
            'pins': ['PB1','PC6','PC7','PC8','PC9'], 'enable_byte': STATE+832,
            'init_bypassed': [0x020159C2,0x020159FC], 'scan_block_guard': 0x02015CC6,
            'other_call_guard': 0x0200CEAC, 'other_guarded_callee': 0x0200CDE0,
            'known_gpio_writers': [0x0201453A,0x02014578,0x0200CC1A,0x0200CC40],
            'knob_gate_other_writes_found': False,
            'proof_scope': 'Decoded selected paths and direct-reference survey; not a full binary alias/indirect-call proof.'},
        'direct_reference_candidates': refs,
        'callgraph_scope': 'Selected direct calls and verified local control flow. A linear decoder includes data and cannot prove absence of all computed calls.',
        'other_GPIO_ownership': [
            {'site': 0x020053A4, 'pins': ['PC0','PC1','PC5','PA9'], 'owner': 'audio port pre/post-start hook'},
            {'site': 0x0201D40E, 'operation': 'generic low-power port save/reconfigure',
             'status': 'must be qualified with power management; not neutralized by panel patches'},
            {'site': 0x0201D95A, 'operation': 'generic GPIO restore',
             'status': 'must preserve MINI codec and switch ownership; not a panel-specific writer'},
            {'site': 0x02004998, 'operation': 'shared GPIO-output helper used with dynamic pins',
             'status': 'not globally replaced; whole-program callers remain an integration audit'}],
        'verification': verification,
        'pending': ['LED electrical mapping and driver', 'MINI knob/expression mapping',
                    'physical switch label order', 'all indirect GPIO writers and low-power transition qualification',
                    'hardware debounce/action behavior and concurrent codec operation'],
        'app_panel_capability_enabled': False, 'hardware_verified': False, 'flashable': False,
        'device_accessed': False, 'verifier_sha256': sha(Path(__file__).read_bytes()),
    }
    report_path = ROOT/'research/mini-panel-port.json'
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'patch_count': len(patches), 'changed_spans_bytes': sum(len(p.before) for p in patches),
                      'verification': verification, 'report': report_path.relative_to(ROOT).as_posix(),
                      'hardware_verified': False, 'flashable': False}, indent=2))


if __name__ == '__main__':
    main()
