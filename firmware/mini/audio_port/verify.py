"""Compile/inspect an append-only G board shim and generate offline hook patches."""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.audit_mini_ultrarig_port import G_PATH, G_SHA, MINI_PATH, MINI_SHA
from tools.disassemble import codec, relative_target
from tools.verify_mini_codec import target_metadata
from firmware.mini.audio_port.patches import (
    ISA, audio_patches, decoded_patches, require, verify_control_flow)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(raw, base, limit):
    meta, _ = target_metadata(raw)
    h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    require(h[0] == 2 and h[1] == 0xf1 and h[8] == 32 and h[10] == 40, 'unexpected ELF ABI')
    loads = []
    for index in range(h[9]):
        p = struct.unpack_from('<8I', raw, h[4]+index*h[8])
        if p[0] == 1:
            loads.append(p)
    require(len(loads) == 1, 'audio shim requires one load segment')
    p = loads[0]
    require(p[2] == p[3] == base and p[4] == p[5] and p[6] == 5,
            'audio shim must be a read-only executable append with no RAM copy')
    require(p[1]+p[4] <= len(raw) and base+p[4] <= limit, 'ELF append bounds')
    require(not meta['undefined_symbols'], 'undefined target symbols')
    require(not meta['section_bytes'].get('.bss', 0) and not meta['section_bytes'].get('.data', 0),
            'audio shim cannot assume extra application BSS/data')
    sections = [struct.unpack_from('<10I', raw, h[5]+i*h[10]) for i in range(h[11])]
    symbols = {}
    for s in sections:
        if s[2] & 2 and s[5]:
            require(s[1] != 8 and base <= s[3] <= s[3]+s[5] <= base+p[4], 'allocated section bounds')
            require(s[4] == p[1]+s[3]-base and s[4]+s[5] <= len(raw), 'section LMA mapping')
            require(not s[2] & 1, 'writable allocated section in XIP shim')
        if s[1] != 2:
            continue
        st = sections[s[6]]
        strings = raw[st[4]:st[4]+st[5]]
        require(s[9] == 16, 'symbol table entry size')
        for offset in range(s[4], s[4]+s[5], s[9]):
            name, value, size, info, _, section = struct.unpack_from('<IIIBBH', raw, offset)
            if name and section:
                text = strings[name:strings.index(0, name)].decode()
                if text.startswith('hyperrig_'):
                    symbols[text] = value
    for name in ('hyperrig_mini_g_audio_pre_current_clock', 'hyperrig_mini_g_audio_post'):
        require(base <= symbols.get(name, 0) < base+p[4], 'missing hook function '+name)
    require(h[3] == symbols['hyperrig_mini_g_audio_pre_current_clock'], 'unexpected ELF entry')
    return raw[p[1]:p[1]+p[4]], dict(meta, address=base, bytes=p[4], end=base+p[4],
                                      entry=h[3], symbols=symbols)


def evidence(g):
    specs = (
        ('gpio_output', 0x02004998, 0x02004a70, '[r2+8] &= ~r0'),
        ('gpio_direction_input', 0x02004ad6, 0x02004b48, '[r3+8] |= 1 << r0'),
        ('gpio_digital', 0x0200187c, 0x02001916, '[r3+12] |= r0'),
        ('gpio_pull_down', 0x02004bac, 0x02004c48, '[r3+20] |= r0'),
        ('gpio_pull_up', 0x02004c9a, 0x02004d36, '[r3+16] |= r0'),
        ('original_channel_start', 0x02005194, 0x020051fc, 'r1 = 2'),
        ('original_cpu_mhz_getter', 0x020057c6, 0x0200580c, 'r0 = r0 / r1 (u)'),
        ('original_driver_ready_state', 0x020050f6, 0x02005124, 'b[r0+0] = r1'),
    )
    result = []
    for name, start, end, required in specs:
        data = g[start-0x02000000:end-0x02000000]
        rows = []
        address = start
        while address < end:
            decoded = codec.decode(ISA, g, address-0x02000000)
            require(decoded is not None, 'undecodable evidence '+name)
            ins, fields, size = decoded
            require(address+size <= end, 'evidence instruction boundary')
            text = codec.format(ins, fields)
            row = {'address': address, 'assembly': text}
            target = relative_target(address, size, text)
            if target is not None:
                row['direct_target'] = target
            rows.append(row)
            address += size
        require(required in [row['assembly'] for row in rows], 'native binding semantic changed '+name)
        if name.startswith('gpio_'):
            targets = [row.get('direct_target') for row in rows]
            require(0x01c00e2e in targets and 0x01c00e46 in targets, 'missing G GPIO critical protocol')
            require(any('testset' in row['assembly'] for row in rows), 'missing G GPIO bank lock')
        result.append({'name': name, 'start': start, 'end_exclusive': end,
                       'sha256': sha(data), 'preimage_hex': data.hex(), 'instructions': rows})
    return result


def main():
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
    out = ROOT / 'build/mini-audio-port'
    out.mkdir(parents=True, exist_ok=True)

    def run(args):
        result = subprocess.run(prefix+args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            print(result.stdout+result.stderr, file=sys.stderr)
            result.check_returncode()
        return result.stdout

    raw = (ROOT / G_PATH).read_bytes()
    require(sha(raw) == G_SHA, 'G container identity changed')
    g, _, files = unpack_app(raw)
    mini_raw = (ROOT / MINI_PATH).read_bytes()
    require(sha(mini_raw) == MINI_SHA, 'MINI evidence identity changed')
    _, mini_contents = unpack_fwsc(mini_raw)
    mini_plain, _, _ = unpack_app(mini_contents['flash.bin'][0x4000:])
    codec_records = mini_plain[0x35e35:0x35e8d]
    require(sha(codec_records) == '1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d',
            'original MINI codec records changed')
    base = 0x02000120+len(files['app.bin'])
    limit = 0x0207e000-383
    require(base == 0x02076aac, 'G append origin changed')
    proofs = evidence(g)
    native_sources = ['firmware/mini/audio_port/audio_port.c',
                      'firmware/mini/audio_port/g_bindings.c',
                      'firmware/mini/codec/hyperrig_mini_codec.c']
    common = ['-std=c11', '-Wall', '-Wextra', '-Werror']
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         native_sources[0], native_sources[2], 'firmware/mini/audio_port/test_audio_port.c',
         '-o', 'build/mini-audio-port/test-audio-port'])
    host = json.loads(run(['build/mini-audio-port/test-audio-port']))
    vendor = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    objects = []
    for source in native_sources:
        target = 'build/mini-audio-port/'+Path(source).stem+'.o'
        run([vendor+'clang', '-target', 'pi32v2', '-mcpu=r3', *common, '-Os', '-ffreestanding',
             '-fno-builtin', '-c', source, '-o', target])
        objects.append(target)
    run([vendor+'clang', '-target', 'pi32v2', '-mcpu=r3', '-c',
         'firmware/mini/codec/spin_pi32v2.S', '-o', 'build/mini-audio-port/spin_pi32v2.o'])
    objects.append('build/mini-audio-port/spin_pi32v2.o')
    name = 'build/mini-audio-port/hyperrig-mini-g-audio'
    run([vendor+'ld', '-z', 'max-page-size=0x20', '-z', 'common-page-size=0x20',
         '--defsym', f'AUDIO_PORT_ADDRESS={base}', '--defsym', f'AUDIO_PORT_LIMIT={limit}',
         '-T', 'firmware/mini/audio_port/audio_port.ld', *objects, '-o', name+'.elf'])
    elf = (ROOT/(name+'.elf')).read_bytes()
    payload, elf_info = inspect(elf, base, limit)
    require(payload.count(codec_records) == 1, 'target does not contain the exact stock codec script once')
    (ROOT/(name+'.bin')).write_bytes(payload)
    asm = run([vendor+'objdump', '-d', name+'.elf'])
    (ROOT/(name+'.asm')).write_text(asm, encoding='utf-8', newline='\n')
    patches = audio_patches(g, elf_info['symbols'])
    control_cases = verify_control_flow(patches, elf_info['symbols'])
    # Independent vendor disassembly of every generated hook byte. This is a
    # two-section validation ELF, NOT a firmware image or executable probe.
    for index, patch in enumerate(patches):
        (out/f'hook{index}.bin').write_bytes(patch.after)
    hook_source = ''.join(
        f'.section .hook{index},"ax",@progbits\n.global hook{index}\nhook{index}:\n'
        f'.incbin "build/mini-audio-port/hook{index}.bin"\n'
        for index in range(2))
    (out/'hooks.S').write_text(hook_source, encoding='utf-8', newline='\n')
    (out/'hooks.ld').write_text(
        'ENTRY(hook0)\nSECTIONS { .hook0 0x020053a4 : { *(.hook0) } '
        '.hook1 0x0200541e : { *(.hook1) } }\n', encoding='utf-8', newline='\n')
    run([vendor+'clang', '-target', 'pi32v2', '-mcpu=r3', '-c',
         'build/mini-audio-port/hooks.S', '-o', 'build/mini-audio-port/hooks.o'])
    run([vendor+'ld', '-T', 'build/mini-audio-port/hooks.ld', 'build/mini-audio-port/hooks.o',
         '-o', 'build/mini-audio-port/hooks.validation.elf'])
    vendor_hooks = run([vendor+'objdump', '-d', 'build/mini-audio-port/hooks.validation.elf'])
    (out/'hooks.vendor.asm').write_text(vendor_hooks, encoding='utf-8', newline='\n')
    vendor_rows = {}
    for line in vendor_hooks.splitlines():
        match = re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(.*)', line)
        if match:
            asm_text = match[3].split(' <', 1)[0].strip()
            vendor_rows[int(match[1], 16)] = (bytes.fromhex(match[2]), asm_text)
    for row in decoded_patches(patches):
        require(row['address'] in vendor_rows, 'vendor did not decode a hook instruction')
        raw_ins, text_ins = vendor_rows[row['address']]
        require(raw_ins.hex() == row['bytes'], 'vendor hook instruction length differs')
        require(re.sub(r'\s+', '', text_ins) == re.sub(r'\s+', '', row['assembly']),
                'vendor hook decode differs: '+text_ins+' / '+row['assembly'])
    # Negative tests cover source identity and allocation/file mapping.
    negative = []
    bad = bytearray(g); bad[0x53a4] ^= 1
    try: audio_patches(bytes(bad), elf_info['symbols'])
    except ValueError: negative.append('changed_G_identity')
    bad_elf = bytearray(elf)
    phoff = struct.unpack_from('<I', elf, 28)[0]
    struct.pack_into('<I', bad_elf, phoff+12, base+4)
    try: inspect(bytes(bad_elf), base, limit)
    except ValueError: negative.append('load_address_mismatch')
    bad_elf = bytearray(elf)
    struct.pack_into('<I', bad_elf, phoff+20, len(payload)+4)
    try: inspect(bytes(bad_elf), base, limit)
    except ValueError: negative.append('uninitialized_memory')
    require(len(negative) == 3, 'negative checks failed')
    paths = sorted(p for p in (ROOT/'firmware/mini/audio_port').glob('*') if p.is_file())
    paths += [ROOT/p for p in native_sources[2:]]
    paths += [ROOT/'firmware/mini/codec/hyperrig_mini_codec.h', ROOT/'firmware/mini/codec/spin_pi32v2.S',
              ROOT/'tools/audit_mini_ultrarig_port.py', ROOT/'tools/verify_mini_codec.py']
    report = {
        'project': 'HyperRig', 'scope': 'Codec/PA9 board shim for integral original G firmware',
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths},
        'G_container_sha256': G_SHA, 'G_decoded_sha256': sha(g),
        'codec_script': {'stock_MINI_container_sha256': MINI_SHA, 'original_table_cpu': 0x02035e35,
            'records': 22, 'bytes': 88, 'sha256': sha(codec_records),
            'stock_replay_byte_identical': True, 'osr_override': None,
            'conditional_NAU88L21_map_OSR': 256, 'additional_codec_writes': [],
            'hardware_48k_qualified': False},
        'host_asan_ubsan': host, 'hook_control_flow_cases': control_cases,
        'hook_vendor_disassembly_match': True,
        'hook_validation_elf_sha256': sha((out/'hooks.validation.elf').read_bytes()),
        'negative_checks': negative, 'original_G_binding_evidence': proofs,
        'elf': dict(elf_info, path=name+'.elf', sha256=sha(elf)),
        'payload': {'path': name+'.bin', 'bytes': len(payload), 'sha256': sha(payload),
                    'base': base, 'read_only_xip': True, 'extra_application_BSS_bytes': 0},
        'patches': [p.record() for p in patches], 'decoded_hook_instructions': decoded_patches(patches),
        'success_flow': ['G getter MHz -> checked Hz', 'PA9 low', '100000 spin iterations',
            'MINI bus GPIO init through original G locking helpers', '22 stock codec records',
            'original G IRQ/open/rate code unchanged', 'original G channel start',
            '100000 spin iterations', 'PA9 high'],
        'failure_flow': 'Both hooks branch to G0x02005436. PA9 remains low; no false success flag at0x02005426.',
        'preserved_code': ['G DSP', 'G RTOS', 'G IRQ registration', 'G ALNK open/rate/start'],
        'remaining_gates': ['Apply independent panel patch before codec bus use.',
            'Prove no other owner of PA1/2 and no clock transition while bitbanging.',
            'GPIO helpers retain original per-bank critical/testset protocol; no external bank lock is acquired.',
            'Stock OSR256 replay at G nominal48k is not yet hardware-qualified.',
            'PA9 function, physical clocks, analog silence and audio performance are unmeasured.',
            'Post failure holds PA9 low but does not roll back already executed G clock/open steps.',
            'Complete G boot contract, storage/radio calibration and recovery remain separate gates.'],
        'candidate_composed': False, 'hardware_accessed': False,
    }
    (out/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('host_asan_ubsan', 'hook_control_flow_cases', 'negative_checks',
                                             'payload', 'patches', 'candidate_composed', 'hardware_accessed')}, indent=2))


if __name__ == '__main__':
    main()
