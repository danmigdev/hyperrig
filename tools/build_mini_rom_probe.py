"""Build RAM-only ROM diagnostics; no transport, MMIO or firmware installation."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dot_machine import DotProgram
from head_machine import HeadProgram
from rechannel_machine import RechannelProgram


def sha(data):
    return hashlib.sha256(data).hexdigest()


def words(values):
    return struct.pack('<' + 'i' * len(values), *values)


def golden():
    d16, d32, head, expand = DotProgram(16), DotProgram(32), HeadProgram(), RechannelProgram()
    small = [-3, -1, 0, 1, 3]
    dot = d16.execute(small, [1], 5, shift=1)
    dot += d32.execute(small, [1], 5, shift=1)
    dot += d16.execute([2147483647, -2147483648], [2], 2)
    dot += d32.execute([-2147483648] * 2, [-2147483648] * 2, 1)
    dot += d16.execute([1, 2, 3, 4], [2, -1], 2, 2, 3)
    dot += d32.execute(small, [1], 5, shift=-1)
    h, history, position = head.execute([1, 0, 0, 2, 0, 0, -3, 0, 0, 5, 0, 0],
                                       [2, 0, 0, 4, 0, 0], [0] * 384, 63, 1, 0)
    dry, expanded, ep = expand.execute([-3, -1, 1, 3], [1, 2, -1], [0] * 399, 68, 1)
    return {'dot': zlib.crc32(words(dot)),
            'head': zlib.crc32(words(h + history) + struct.pack('<I', position)),
            'rechannel': zlib.crc32(words(dry + expanded) + struct.pack('<I', ep)),
            'cases': 8, 'source': 'interpreted original UltraRig G v2 kernels, not HyperRig C output',
            'original_kernel_sha256': {str(p.start): sha(p.raw) for p in (d16, d32, head, expand)}}


def inspect_rom_elf(raw, base):
    if raw[:7] != b'\x7fELF\x01\x01\x01': raise ValueError('not ELF32 LE')
    h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    if h[:4] != (2, 0xf1, 1, base) or h[8] != 32 or h[10] != 40:
        raise ValueError('wrong target/header/ROM entry')
    segments, symbols = [], {}
    for i in range(h[9]):
        p = struct.unpack_from('<8I', raw, h[4] + i * h[8])
        if p[0] != 1: continue
        _, offset, va, pa, size, memory, flags, align = p
        if not (base <= va == pa <= base + 32768 and size <= memory <= base + 32768 - va and
                offset + size <= len(raw) and align and align & (align - 1) == 0 and offset % align == va % align):
            raise ValueError('ELF leaves ROM slot or has invalid load range')
        segments.append(p)
    if len(segments) != 1 or segments[0][2] != base or not segments[0][6] & 1:
        raise ValueError('expected one contiguous executable ROM slot')
    sections = [struct.unpack_from('<10I', raw, h[5] + i * h[10]) for i in range(h[11])]
    for section in sections:
        if section[2] & 2 and not (base <= section[3] <= base + 32768 and section[5] <= base + 32768 - section[3]):
            raise ValueError('allocated section outside slot')
        if section[1] != 2: continue
        table = sections[section[6]]
        names = raw[table[4]:table[4] + table[5]]
        for off in range(section[4], section[4] + section[5], 16):
            name, value, size, info, other, index = struct.unpack_from('<IIIBBH', raw, off)
            if not name: continue
            text = names[name:names.index(0, name)].decode('ascii')
            if not index and info >> 4 in (1, 2): raise ValueError('undefined symbol: ' + text)
            if index: symbols[text] = value
    for name in ('hyperrig_rom_entry', 'hyperrig_rom_record', '__slot_start', '__slot_end', '__bss_end'):
        if name not in symbols: raise ValueError('missing linker symbol: ' + name)
    if symbols['__slot_start'] != base or symbols['__slot_end'] != base + 32768:
        raise ValueError('wrong slot contract')
    p = segments[0]
    if not base <= symbols['hyperrig_rom_record'] <= base + p[5] - 64:
        raise ValueError('record outside initialized state')
    payload = raw[p[1]:p[1] + p[4]]
    return payload, {'base': base, 'span': 32768, 'entry': base, 'payload_bytes': len(payload),
                     'memory_bytes': p[5], 'record_address': symbols['hyperrig_rom_record'],
                     'record_bytes': 64, 'elf_sha256': sha(raw), 'payload_sha256': sha(payload)}


def main():
    out = ROOT / 'build/mini-rom'
    out.mkdir(parents=True, exist_ok=True)
    expected = golden()
    source_paths = sorted((ROOT / 'firmware/mini/rom_probe').glob('*'))
    build_tag = int(sha(b''.join(p.read_bytes() for p in source_paths if p.is_file()))[:8], 16)
    header = ''.join(f'#define HYPERRIG_ROM_{name.upper()}_CRC UINT32_C(0x{expected[name]:08x})\n'
                     for name in ('dot', 'head', 'rechannel'))
    header += f'#define HYPERRIG_ROM_BUILD_TAG UINT32_C(0x{build_tag:08x})\n'
    (out / 'golden.h').write_text(header, encoding='utf-8', newline='\n')
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
    def run(args):
        result = subprocess.run(prefix + args, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            print(result.stdout + result.stderr, file=sys.stderr)
            result.check_returncode()
        return result.stdout
    vendor = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    common = ['-std=c99', '-Wall', '-Wextra', '-Werror', '-Ifirmware/include',
              '-Ifirmware/mini/rom_probe', '-Ibuild/mini-rom']
    sources = ['firmware/mini/rom_probe/rom_probe.c'] + [f'firmware/src/hyperrig_{n}.c' for n in ('dot', 'head', 'rechannel', 'a2l')]
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         *sources, 'firmware/mini/rom_probe/host_test.c', '-o', 'build/mini-rom/host-sanitize'])
    host = json.loads(run(['build/mini-rom/host-sanitize']))
    objects = []
    for source in ['firmware/mini/rom_probe/entry.c', *sources, 'firmware/mini/boot/runtime.c']:
        target = 'build/mini-rom/' + Path(source).stem + '.o'
        run([vendor + 'clang', '-target', 'pi32v2', '-mcpu=r3', *common, '-Os', '-ffreestanding',
             '-fno-builtin', '-DHYPERRIG_ROM_TARGET', '-c', source, '-o', target])
        objects.append(target)
    artifacts = []
    for base in (0x1c20000, 0x1c28000):
        name = f'build/mini-rom/hyperrig-rom-probe-{base:08x}'
        run([vendor + 'ld', '-z', 'max-page-size=0x20', '-z', 'common-page-size=0x20',
             '--defsym', f'PROBE_ADDRESS={base}', '-T', 'firmware/mini/rom_probe/probe.ld',
             *objects, '-o', name + '.elf'])
        data, item = inspect_rom_elf((ROOT / (name + '.elf')).read_bytes(), base)
        (ROOT / (name + '.bin')).write_bytes(data)
        item.update(file=name + '.bin', elf=name + '.elf')
        artifacts.append(item)
        (ROOT / (name + '.asm')).write_text(run([vendor + 'objdump', '-d', name + '.elf']), encoding='utf-8', newline='\n')
    tracked = source_paths + [ROOT / p for p in sources[1:]] + [ROOT / 'firmware/mini/boot/runtime.c', Path(__file__)]
    report = {'project': 'HyperRig', 'type': 'AC791N ROM RAM diagnostics', 'build_tag': build_tag,
              'golden': expected, 'host': {**host, 'asan': True, 'ubsan': True}, 'artifacts': artifacts,
              'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in tracked if p.is_file()},
              'hardware_execution_verified': False, 'hardware_peripheral_actions': False,
              'firmware_installation_package': False, 'complete_flash_backup': False,
              'abi_reference': 'm-bootloader/docs/SPEC.md 10.1 and pi32v2-isa/tools/hwtest/runner.S',
              'limits': ['ROM upload/ABI and slot allocations must be observed on this MINI.',
                         'Eight primitive kernel cases are not the complete A2 engine or audio path.',
                         'No SPI or flash reader; FD61 exposes only this plug-in slot.',
                         'Send callback return/error semantics are unknown; host must validate transfer status.']}
    (ROOT / 'research/mini-rom-probe.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'host': host, 'artifacts': artifacts}, indent=2))


if __name__ == '__main__':
    main()
