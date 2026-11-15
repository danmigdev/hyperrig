"""Build a bounded, read-only codec ROM diagnostic entirely OFFLINE.

This script neither opens a device nor produces an installation image. The
linked target may access only PA1/PA2 when its explicit read command is called;
entry/identity must remain free of peripheral operations.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tools'))
from tools.verify_mini_rom_stack import decode as decode_stack_bridge, validate_stack_layout

OUT = ROOT/'build/mini-rom-codec'
BASES = (0x01C20000, 0x01C28000)
SPAN, STACK, RECORD_BYTES = 32768, 4096, 128
ALLOWED_REGISTERS = (0x01, 0x03, 0x1C, 0x1D, 0x2B, 0x2C, 0x31, 0x32, 0x58, 0x59)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def inspect_elf(raw, base):
    """Validate load/section/symbol coverage and extract the single RAM image."""
    def read(fmt, off):
        size = struct.calcsize(fmt)
        require(0 <= off <= len(raw)-size, 'truncated ELF structure')
        return struct.unpack_from(fmt, raw, off)

    require(base in BASES, 'unsupported ROM slot')
    require(raw[:7] == b'\x7fELF\x01\x01\x01', 'expected ELF32 little endian')
    h = read('<HHIIIIIHHHHHH', 16)
    require(h[:4] == (2, 0xF1, 1, base) and h[7] == 52 and h[8] == 32 and h[10] == 40,
            'wrong target, entry or ELF header')
    segments = []
    for i in range(h[9]):
        p = read('<8I', h[4]+i*h[8])
        if p[0] != 1:
            continue
        _, offset, va, pa, filesz, memsz, flags, align = p
        require(va == pa == base and 0 < filesz <= memsz <= SPAN,
                'load segment leaves the owned slot')
        require(offset <= len(raw)-filesz and flags == 7 and align > 0 and
                not align & (align-1) and offset % align == va % align,
                'invalid segment file range/flags/alignment')
        segments.append(p)
    require(len(segments) == 1, 'expected one ROM slot load segment')
    p = segments[0]
    sections = [read('<10I', h[5]+i*h[10]) for i in range(h[11])]
    symbols, allocated = {}, []
    for section in sections:
        _, kind, flags, address, offset, size, link, _, align, stride = section
        require(kind == 8 or 0 <= offset <= len(raw)-size, 'section outside ELF')
        if flags & 2:
            require(kind in (1, 8) and base <= address <= base+p[5] and
                    size <= base+p[5]-address, 'allocated section outside segment')
            require(not align or address % align == 0, 'unaligned allocated section')
            if kind == 8:
                require(address >= base+p[4], 'BSS overlaps uploaded bytes')
            elif size:
                require(address <= base+p[4]-size and offset == p[1]+address-base,
                        'section bytes missing or incorrectly mapped')
            if size:
                allocated.append((address, address+size))
        if kind != 2:
            continue
        require(stride == 16 and size % stride == 0 and link < len(sections), 'invalid symbol table')
        strings = sections[link]
        require(strings[1] == 3 and strings[4] <= len(raw)-strings[5], 'invalid symbol names')
        names = raw[strings[4]:strings[4]+strings[5]]
        for off in range(offset, offset+size, stride):
            name, value, count, info, _, index = read('<IIIBBH', off)
            if not name:
                continue
            require(name < len(names) and b'\0' in names[name:], 'invalid symbol name')
            text = names[name:names.index(0, name)].decode('ascii')
            require(index or info >> 4 not in (1, 2), 'undefined symbol: '+text)
            if index:
                if text in symbols and symbols[text]['address'] != value:
                    text += '@'+hex(value)
                symbols[text] = {'address': value, 'bytes': count, 'type': info & 15}
    allocated.sort()
    require(all(a[1] <= b[0] for a, b in zip(allocated, allocated[1:])), 'allocated sections overlap')
    required = ('hyperrig_rom_codec_entry', 'hyperrig_rom_codec_record',
                'hyperrig_rom_codec_initialize', 'hyperrig_rom_codec_dispatch',
                '__slot_start', '__slot_end', '__image_file_end', '__bss_start', '__bss_end',
                'private_stack', 'state', 'hyperrig_mini_rom_run_on_stack',
                'hyperrig_mini_codec_bus_init', 'hyperrig_mini_codec_read16',
                'hyperrig_mini_codec_probe_register_allowed', 'hyperrig_mini_codec_spin_pi32v2')
    require(all(n in symbols for n in required), 'required codec diagnostic symbol missing')
    addr = lambda n: symbols[n]['address']
    require(addr('__slot_start') == addr('hyperrig_rom_codec_entry') == base and
            addr('__slot_end') == base+SPAN and addr('__image_file_end') == base+p[4] and
            addr('__bss_start') == base+p[4] and addr('__bss_end') == base+p[5], 'linker bounds disagree')
    spans = []
    for name in ('private_stack', 'state', 'hyperrig_rom_codec_record'):
        item = symbols[name]
        require(base+p[4] <= item['address'] <= base+p[5]-item['bytes'], 'private state not inside BSS: '+name)
        spans.append((item['address'], item['address']+item['bytes']))
    spans.sort()
    require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'private state overlaps')
    require(symbols['hyperrig_rom_codec_record']['bytes'] == RECORD_BYTES and
            symbols['private_stack']['bytes'] == STACK+64, 'record/private stack size mismatch')
    bottom = addr('private_stack')+32
    require(bottom % 8 == 0, 'private stack alignment')
    validate_stack_layout(base, base+p[4], addr('private_stack'), bottom, bottom+STACK)
    allowed_codec = {'hyperrig_mini_codec_bus_init', 'hyperrig_mini_codec_read16',
                     'hyperrig_mini_codec_probe_register_allowed', 'hyperrig_mini_codec_spin_pi32v2'}
    linked_codec = {n for n in symbols if n.startswith('hyperrig_mini_codec_')}
    require(linked_codec == allowed_codec, 'unexpected linked codec functionality: '+repr(sorted(linked_codec-allowed_codec)))
    forbidden = ('stock_records', 'hyperrig_mini_codec_write', 'hyperrig_mini_codec_write_adapter',
                 'hyperrig_mini_codec_apply_stock', 'hyperrig_mini_codec_soft_mute',
                 'hyperrig_mini_codec_control_apply_stock', 'hyperrig_mini_codec_bind_mmio')
    require(not any(n in symbols for n in forbidden), 'write/reset/MMIO-binding codec routine linked')
    payload = raw[p[1]:p[1]+p[4]]
    bridge = symbols['hyperrig_mini_rom_run_on_stack']
    bridge_bytes = payload[bridge['address']-base:bridge['address']-base+bridge['bytes']]
    bridge_instructions = decode_stack_bridge(bridge_bytes)
    return payload, symbols, {
        'base': base, 'span': SPAN, 'entry': base, 'payload_bytes': len(payload),
        'bss_bytes': p[5]-p[4], 'memory_bytes': p[5], 'slot_free_bytes': SPAN-p[5],
        'record_address': addr('hyperrig_rom_codec_record'), 'record_bytes': RECORD_BYTES,
        'private_stack_bottom': bottom, 'private_stack_top': bottom+STACK, 'private_stack_bytes': STACK,
        'state_bytes': symbols['state']['bytes'], 'elf_sha256': sha(raw), 'payload_sha256': sha(payload),
        'linked_codec_functions': sorted(linked_codec), 'forbidden_codec_symbols_absent': True,
        'stack_bridge': {'bytes': len(bridge_bytes), 'sha256': sha(bridge_bytes),
                         'instructions': bridge_instructions, 'incoming_stack_bytes': 8,
                         'inherited_interrupt_stack_qualified': False},
    }


def negative_elf_checks(raw, base):
    tests = [raw[:20], raw[:-16]]
    bad = bytearray(raw)
    struct.pack_into('<I', bad, 24, base+2)
    tests.append(bytes(bad))
    h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    for field, value in ((12, base+SPAN), (20, SPAN+1), (16, len(raw)+1)):
        bad = bytearray(raw)
        struct.pack_into('<I', bad, h[4]+field, value)
        tests.append(bytes(bad))
    rejected = 0
    for bad in tests:
        try:
            inspect_elf(bad, base)
        except (ValueError, UnicodeError, struct.error):
            rejected += 1
    require(rejected == len(tests), 'invalid ELF accepted by slot validator')
    return rejected


def validate_record(record, *, base, build_tag, sequence, reg, target=True):
    """Pure validation of a saved HYC1 record, including diagnostic failures.

    A valid NACK/restore/guard failure is evidence of that failure, never codec
    readiness. The caller establishes the exact payload and transport identity.
    """
    require(len(record) == RECORD_BYTES and record[:4] == b'HYC1' and record[124:] == b'DONE',
            'invalid codec record framing')
    require(base in BASES and 1 <= sequence <= 65535 and reg in ALLOWED_REGISTERS,
            'invalid expected record contract')
    u32 = lambda off: struct.unpack_from('<I', record, off)[0]
    s32 = lambda off: struct.unpack_from('<i', record, off)[0]
    require(u32(4) == 1 and u32(8) == base and u32(12) == build_tag and
            u32(16) == sequence and u32(20) == reg, 'record identity/sequence mismatch')
    require(u32(120) == zlib.crc32(record[:120]), 'record CRC mismatch')
    status, read_status = s32(24), s32(108)
    restored, guards = u32(52), u32(116)
    require(restored in (0, 1) and guards in (0, 1) and read_status in (0, -2), 'unknown record result')
    expected_status = -7 if not guards else -6 if not restored else read_status
    require(status == expected_status, 'combined result disagrees with component failures')
    actual_restored = all(not ((u32(64+4*i) ^ u32(84+4*i)) & 6) for i in range(5))
    require(restored == int(actual_restored), 'GPIO restore flag disagrees with snapshots')
    require(u32(44) == 1 and u32(48) == 0 and 0 < u32(104) <= 193, 'STOP/delay diagnostics disagree')
    if read_status == 0:
        require(u32(28) <= 65535 and (u32(32), u32(36), u32(40), u32(104)) == (4, 2, 20, 193),
                'completed read lacks four ACKs/two bytes/twenty samples')
    else:
        require(u32(28) == 65535 and u32(32) < 4 and u32(36) == 0 and u32(40) == u32(32)+1,
                'NACK record contains invented data or inconsistent ACK progress')
    require((0 < u32(112) <= STACK) if target else u32(112) == 0, 'invalid stack observation')
    return {'record_valid': True, 'read_successful': status == 0, 'status': status,
            'read_status': read_status, 'sequence': sequence, 'register': reg, 'value': u32(28),
            'gpio_restored': bool(restored), 'stack_guards_ok': bool(guards),
            'stack_observed_bytes': u32(112), 'record_sha256': sha(record)}


def check_host_record(record, tag):
    expected = dict(base=BASES[1], build_tag=tag, sequence=1, reg=0x59, target=False)
    validated = validate_record(record, **expected)
    require(validated['read_successful'] and validated['value'] == 0x59, 'unexpected final host record')
    cases = [record[:-1], b'X'+record[1:]]
    for off in (4, 8, 12, 16, 20, 24, 32, 36, 40, 44, 48, 52, 84, 104, 108, 112, 116):
        bad = bytearray(record)
        struct.pack_into('<I', bad, off, struct.unpack_from('<I', bad, off)[0] ^ (2 if off == 84 else 1))
        struct.pack_into('<I', bad, 120, zlib.crc32(bad[:120]))
        cases.append(bytes(bad))
    bad = bytearray(record)
    bad[120] ^= 1
    cases.append(bytes(bad))
    rejected = 0
    for bad in cases:
        try:
            validate_record(bad, **expected)
        except ValueError:
            rejected += 1
    require(rejected == len(cases), 'malformed codec record accepted')
    return {**validated, 'negative_record_cases': rejected}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    native = ['firmware/mini/rom_codec/rom_codec.c',
              'firmware/mini/codec/hyperrig_mini_codec.c', 'firmware/mini/codec_probe/read16.c']
    bridge = 'firmware/mini/rom_stack/rom_stack_pi32v2.S'
    spin = 'firmware/mini/codec/spin_pi32v2.S'
    sources = ['firmware/mini/rom_codec/entry.c', *native,
               'firmware/mini/boot/runtime.c', bridge, spin]
    tracked = [ROOT/p for p in sources] + [
        ROOT/'firmware/mini/rom_codec/rom_codec.h', ROOT/'firmware/mini/rom_codec/host_test.c',
        ROOT/'firmware/mini/rom_codec/codec.ld', ROOT/'firmware/mini/codec/hyperrig_mini_codec.h',
        ROOT/'firmware/mini/codec_probe/read16.h', ROOT/'firmware/mini/codec_probe/test_read16.c',
        ROOT/'firmware/mini/rom_stack/rom_stack.h',
        ROOT/'tools/verify_mini_rom_stack.py', Path(__file__)]
    hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in tracked}
    tag = int(sha(json.dumps(hashes, sort_keys=True).encode())[:8], 16)
    (OUT/'build_tag.h').write_text(
        f'#define HYPERRIG_CODEC_BUILD_TAG UINT32_C(0x{tag:08x})\n', encoding='utf-8', newline='\n')
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []

    def run(args):
        result = subprocess.run(prefix+args, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout+result.stderr)
            result.check_returncode()
        return result.stdout

    common = ['-std=c99', '-Wall', '-Wextra', '-Werror',
              '-Ifirmware/mini/rom_codec', '-Ibuild/mini-rom-codec']
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         *native, 'firmware/mini/rom_codec/host_test.c', '-o', 'build/mini-rom-codec/host-sanitize'])
    host = json.loads(run(['build/mini-rom-codec/host-sanitize']))
    host_record = check_host_record(bytes.fromhex(host.pop('record_hex')), tag)
    # Independent GPIO-edge decoder asserts exactly 36/regHi/regLo/37 on the
    # wire; exhausts all returned 16-bit values and bounded fault positions.
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         'firmware/mini/codec_probe/read16.c', 'firmware/mini/codec_probe/test_read16.c',
         '-o', 'build/mini-rom-codec/wire-sanitize'])
    wire = json.loads(run(['build/mini-rom-codec/wire-sanitize']))
    vendor = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    objects = []
    for source in sources:
        target = 'build/mini-rom-codec/'+Path(source).stem+'.o'
        run([vendor+'clang', '-target', 'pi32v2', '-mcpu=r3', *common, '-Os',
             '-ffreestanding', '-fno-builtin', '-ffunction-sections', '-fdata-sections',
             '-DHYPERRIG_ROM_CODEC_TARGET', '-c', source, '-o', target])
        objects.append(target)
    artifacts = []
    negatives = 0
    for base in BASES:
        name = f'build/mini-rom-codec/hyperrig-rom-codec-{base:08x}'
        run([vendor+'ld', '-z', 'max-page-size=0x20', '-z', 'common-page-size=0x20',
             '--gc-sections', '--defsym', f'PROBE_ADDRESS={base}',
             '-T', 'firmware/mini/rom_codec/codec.ld', *objects, '-o', name+'.elf'])
        raw = (ROOT/(name+'.elf')).read_bytes()
        payload, symbols, item = inspect_elf(raw, base)
        negatives += negative_elf_checks(raw, base)
        (ROOT/(name+'.bin')).write_bytes(payload)
        assembly = run([vendor+'objdump', '-d', name+'.elf'])
        (ROOT/(name+'.asm')).write_text(assembly, encoding='utf-8', newline='\n')
        item.update(file=name+'.bin', elf=name+'.elf', assembly=name+'.asm')
        artifacts.append(item)
    report = {
        'project': 'HyperRig', 'type': 'ROM bounded read-only MINI codec diagnostic',
        'build_tag': tag, 'source_sha256': hashes,
        'generated_header_sha256': sha((OUT/'build_tag.h').read_bytes()),
        'host': {**host, 'record_validation': host_record, 'wire_state_test': wire,
                 'asan': True, 'ubsan': True, 'real_MMIO': False,
                 'target_stack_bridge_executed': False},
        'artifacts': artifacts, 'negative_ELF_cases': negatives,
        'protocol': {'identity': 'FC64', 'read_register': 'FC65', 'read_record': 'FD66',
                     'magic': 'HYC1', 'version': 1, 'record_bytes': RECORD_BYTES,
                     'padding': 'every unused CDB byte must be FF',
                     'register_allowlist': list(ALLOWED_REGISTERS)},
        'target_effects': {'entry_peripheral_access': False,
            'identity_peripheral_access': False, 'explicit_FC65_GPIO': ['PA1', 'PA2'],
            'snapshot_restore_mask': 6, 'codec_data_writes': False, 'codec_reset': False,
            'clock_or_MCLK_writes': False, 'NOR_access': False},
        'hardware_execution_verified': False, 'firmware_installation_package': False,
        'codec_identity_verified': False, 'calibrated_timing': False,
        'limits': ['Read-register transactions include address/register selection, but no codec register data writes.',
                   'PA1/PA2 ownership and ROM callback/interrupt environment require separate hardware qualification.',
                   'NACK cannot distinguish absent hardware from power/reset/MCLK state or timing.',
                   'The fixed finite spin count has no asserted microsecond calibration.',
                   'Private stack and ELF validation are offline; host ASan runs on the host stack.'],
    }
    (ROOT/'research/mini-rom-codec.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'host': host, 'artifacts': artifacts,
                      'hardware_execution_verified': False}, indent=2))


if __name__ == '__main__':
    main()
