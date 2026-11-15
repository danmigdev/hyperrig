"""Build a synthetic three-layer ROM engine diagnostic, entirely offline.

This does not open a device or build an installable firmware image. Expected
signals and histories come from interpreted original G kernels, not this C.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from layer_machine import LayerProgram
from bias_machine import BiasProgram
from verify_engine_native import NativeEngine, synthetic
from verify_mini_rom_stack import decode as decode_stack_bridge, validate_stack_layout
from hyperrig.a2l import inspect as inspect_a2l

SEED = 0x48594531
BLOCKS = (1, 63, 64, 7, 31, 64)
FRAMES = sum(BLOCKS)
SPAN = 32768
STACK = 4096
BASES = (0x01C20000, 0x01C28000)
OUT = ROOT / 'build/mini-rom-engine'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def words(values):
    return struct.pack('<' + 'I' * len(values), *(v & 0xffffffff for v in values))


def input_at(index):
    value = (index * 1664525 + 1013904223) & 0xffffffff
    value ^= value >> 13
    return (value & 0x1fffffff) - 0x10000000 if index else 0


def history_crc(engine):
    crc = 0
    for i in range(len(engine.parameters)):
        crc = zlib.crc32(words(engine.histories[i]), crc)
        crc = zlib.crc32(words([engine.rings[i], engine.frames % engine.rings[i],
                               engine.rings[i + 1], engine.frames % engine.rings[i + 1]]), crc)
    crc = zlib.crc32(words(engine.histories[-1]), crc)
    crc = zlib.crc32(words(engine.head_history), crc)
    return zlib.crc32(words([engine.frames % engine.rings[0], engine.frames % 64,
                            engine.frames, engine.frames >> 32]), crc)


def golden():
    data = synthetic(random.Random(SEED))
    programs = {kind: LayerProgram(kind) for kind in ('generic', '6_shift', '15_shift')}
    engine = NativeEngine(data, programs)
    output_crc = sum_crc = 0
    outputs = []
    rows = []
    for count in BLOCKS:
        output, summed = engine.process([input_at(engine.frames + i) for i in range(count)])
        outputs += output
        output_crc = zlib.crc32(words(output), output_crc)
        sum_crc = zlib.crc32(words(summed), sum_crc)
        rows.append({'frames': engine.frames, 'output': output_crc,
                     'sum': sum_crc, 'history': history_crc(engine)})
    replay = NativeEngine(data, programs)
    replay_outputs, replay_blocks = [], 0
    while replay.frames < FRAMES:
        count = min(17, FRAMES - replay.frames)
        output, _ = replay.process([input_at(replay.frames + i) for i in range(count)])
        replay_outputs += output
        replay_blocks += 1
    if outputs != replay_outputs or history_crc(replay) != rows[-1]['history']:
        raise ValueError('original-kernel oracle differs after block repartition')
    sources = list(programs.values()) + [engine.input, engine.head, BiasProgram('conv'), BiasProgram('head')]
    return data, {
        'fixture_seed': SEED, 'fixture_bytes': len(data), 'fixture_sha256': sha(data),
        'fixture_crc32': zlib.crc32(data[:-4]), 'layers': 3, 'channels': 3,
        'kernel_dilation': [[1, 1], [6, 3], [15, 7]], 'receptive_field': 117,
        'input_algorithm': 'u32(index*1664525+1013904223), xor >>13, mask29 minus2^28; sample0=0',
        'input_sha256': sha(words([input_at(i) for i in range(FRAMES)])),
        'block_sizes': list(BLOCKS), 'frames': FRAMES, 'block_results': rows,
        'replay_block_size': 17, 'replay_blocks': replay_blocks,
        'replay_output_crc': zlib.crc32(words(replay_outputs)),
        'replay_history_crc': history_crc(replay), 'output_sha256': sha(words(outputs)),
        'signal_kernel_invocations': (len(BLOCKS) + replay_blocks) * 5,
        'source': 'interpreted original G instructions; scheduler/context setup reconstructed',
        'original_kernel_sha256': {f'0x{p.start:08x}': sha(p.raw) for p in sources},
        'original_A2_capture': False,
    }


def write_fixture(data, expected, tag):
    text = ['/* Generated fixture; deterministic synthetic model, not original A2. */',
            f'#define HYPERRIG_ENGINE_BUILD_TAG UINT32_C(0x{tag:08x})',
            f'#define HYPERRIG_ENGINE_FIXTURE_CRC UINT32_C(0x{expected["fixture_crc32"]:08x})',
            f'#define HYPERRIG_ENGINE_BLOCKS {len(BLOCKS)}',
            f'#define HYPERRIG_ENGINE_FRAMES {FRAMES}',
            f'static const uint8_t fixture[{len(data)}] = {{']
    text += ['    ' + ', '.join(f'0x{v:02x}' for v in data[i:i + 16]) + ',' for i in range(0, len(data), 16)]
    text += ['};', 'static const uint8_t block_sizes[] = {' + ', '.join(map(str, BLOCKS)) + '};']
    for name in ('output', 'sum', 'history'):
        text += [f'static const uint32_t expected_{name}_crc[] = {{' +
                 ', '.join(f'UINT32_C(0x{r[name]:08x})' for r in expected['block_results']) + '};']
    (OUT / 'fixture.h').write_text('\n'.join(text) + '\n', encoding='utf-8', newline='\n')
    (OUT / 'synthetic3.a2l').write_bytes(data)


def inspect_elf(raw, base):
    def read(fmt, offset):
        size = struct.calcsize(fmt)
        if offset < 0 or offset > len(raw) - size:
            raise ValueError('truncated ELF')
        return struct.unpack_from(fmt, raw, offset)

    if raw[:7] != b'\x7fELF\x01\x01\x01':
        raise ValueError('expected ELF32 little endian')
    h = read('<HHIIIIIHHHHHH', 16)
    if h[:4] != (2, 0xf1, 1, base) or h[7] != 52 or h[8] != 32 or h[10] != 40:
        raise ValueError('wrong target/entry/header')
    segments = []
    for i in range(h[9]):
        p = read('<8I', h[4] + i * h[8])
        if p[0] != 1:
            continue
        _, offset, va, pa, file_size, memory_size, flags, align = p
        if not (va == pa == base and 0 < file_size <= memory_size <= SPAN and
                offset <= len(raw) - file_size and flags == 7 and align and
                align & (align - 1) == 0 and offset % align == va % align):
            raise ValueError('invalid ROM slot load segment')
        segments.append(p)
    if len(segments) != 1:
        raise ValueError('expected one RAM load segment')
    segment = segments[0]
    sections = [read('<10I', h[5] + i * h[10]) for i in range(h[11])]
    symbols = {}
    allocated = []
    for section in sections:
        _, kind, flags, address, offset, size, link, _, alignment, entsize = section
        if kind != 8 and (offset > len(raw) or size > len(raw) - offset):
            raise ValueError('section outside ELF file')
        if flags & 2:
            if kind not in (1, 8):
                raise ValueError('unsupported allocated section type')
            if not (base <= address <= base + segment[5] and size <= base + segment[5] - address):
                raise ValueError('allocated section outside image memory')
            if kind != 8 and not (base <= address <= base + segment[4] and size <= base + segment[4] - address):
                raise ValueError('initialized section missing from payload')
            if kind != 8 and size and offset != segment[1] + address - base:
                raise ValueError('section load mapping differs from segment')
            if kind == 8 and address < base + segment[4]:
                raise ValueError('BSS overlaps file-backed payload')
            if alignment and address % alignment:
                raise ValueError('unaligned allocated section')
            if size:
                allocated.append((address, address + size))
        if kind != 2:
            continue
        if entsize != 16 or size % entsize or link >= len(sections):
            raise ValueError('malformed symbol table')
        table = sections[link]
        names = raw[table[4]:table[4] + table[5]]
        for off in range(offset, offset + size, 16):
            name, value, length, info, _, index = read('<IIIBBH', off)
            if not name:
                continue
            if name >= len(names) or b'\0' not in names[name:]:
                raise ValueError('malformed symbol name')
            key = names[name:names.index(0, name)].decode('ascii')
            if not index and info >> 4 in (1, 2):
                raise ValueError('undefined symbol: ' + key)
            if index:
                if key in symbols and symbols[key]['address'] != value:
                    key += '@' + hex(value)
                symbols[key] = {'address': value, 'bytes': length, 'type': info & 15}
    allocated.sort()
    if any(a[1] > b[0] for a, b in zip(allocated, allocated[1:])):
        raise ValueError('allocated ELF sections overlap')
    need = ['hyperrig_rom_engine_entry', 'hyperrig_rom_engine_record', '__slot_start', '__slot_end',
            '__image_file_end', '__bss_start', '__bss_end', 'private_stack', 'state', 'core',
            'hyperrig_mini_rom_run_on_stack', 'hyperrig_rom_engine_abi']
    if any(name not in symbols for name in need):
        raise ValueError('required ROM engine symbol missing')
    addr = lambda name: symbols[name]['address']
    if not (addr('__slot_start') == addr('hyperrig_rom_engine_entry') == base and
            addr('__slot_end') == base + SPAN and addr('__image_file_end') == base + segment[4] and
            addr('__bss_start') == base + segment[4] and addr('__bss_end') == base + segment[5]):
        raise ValueError('linker image bounds mismatch')
    for name in ('hyperrig_rom_engine_record', 'private_stack', 'state'):
        item = symbols[name]
        if not (base + segment[4] <= item['address'] <= base + segment[5] - item['bytes']):
            raise ValueError('private state outside BSS: ' + name)
    if symbols['hyperrig_rom_engine_record']['bytes'] != 128 or symbols['private_stack']['bytes'] != STACK + 64:
        raise ValueError('record/stack layout mismatch')
    stack_bottom = addr('private_stack') + 32
    if stack_bottom % 8:
        raise ValueError('private stack is not eight-byte aligned')
    validate_stack_layout(base, base + segment[4], addr('private_stack'), stack_bottom, stack_bottom + STACK)
    spans = sorted((symbols[n]['address'], symbols[n]['address'] + symbols[n]['bytes'])
                   for n in ('state', 'private_stack', 'hyperrig_rom_engine_record'))
    if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
        raise ValueError('private state objects overlap')
    payload = raw[segment[1]:segment[1] + segment[4]]
    return payload, symbols, {
        'base': base, 'span': SPAN, 'entry': base, 'payload_bytes': len(payload),
        'bss_bytes': segment[5] - segment[4], 'memory_bytes': segment[5],
        'slot_free_bytes': SPAN - segment[5], 'record_address': addr('hyperrig_rom_engine_record'),
        'record_bytes': 128, 'private_stack_bottom': stack_bottom,
        'private_stack_top': stack_bottom + STACK, 'private_stack_bytes': STACK,
        'state_bytes': symbols['state']['bytes'],
        'elf_sha256': sha(raw), 'payload_sha256': sha(payload),
    }


def stack_audit(assembly, symbols):
    """Conservative static direct-call bound; rejects unknown core stack effects.

    Not an interrupt/ROM bound or proof about compiler semantics. Register push
    sizes and explicit frame allocations are taken from final target assembly.
    """
    functions = {v['address']: (k, v['bytes']) for k, v in symbols.items() if v['type'] == 2 and v['bytes']}
    instructions = []
    for line in assembly.splitlines():
        match = re.match(r'\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\s*(.*)', line)
        if match:
            instructions.append((int(match[1], 16), match[2]))
    memo, active, rows = {}, set(), {}

    def visit(address):
        if address in memo:
            return memo[address]
        if address in active or address not in functions:
            raise ValueError('recursive/unknown core call at ' + hex(address))
        active.add(address)
        name, size = functions[address]
        frame, calls = 0, []
        for pc, code in instructions:
            if not address <= pc < address + size:
                continue
            push = re.search(r'\[--sp\] = \{([^}]+)\}', code)
            if push:
                for register in push[1].split(','):
                    register = register.strip()
                    span = re.fullmatch(r'r(\d+)-r(\d+)', register)
                    frame += 4 * (abs(int(span[1]) - int(span[2])) + 1 if span else 1)
            adjust = re.search(r'\bsp \+= -(\d+)', code)
            if adjust:
                frame += int(adjust[1])
            if re.search(r'\bsp\s*=(?!=)', code):
                raise ValueError('dynamic stack change in core graph: ' + name)
            is_call = re.search(r'\bcall\b', code)
            if is_call or code.startswith('goto '):
                target = re.search(r'<[^:]+:\s*([0-9a-f]+)\s*>', code)
                if not target:
                    raise ValueError('indirect/unknown core call: ' + name + ': ' + code)
                value = int(target[1], 16)
                if is_call or not address <= value < address + size:
                    calls.append(value)
        child = max((visit(c) for c in calls), default=0)
        active.remove(address)
        memo[address] = frame + child
        rows[name + '@' + hex(address)] = {'frame_bytes': frame, 'bound_bytes': memo[address],
                                           'calls': sorted(set(functions[c][0] for c in calls))}
        return memo[address]

    bound = visit(symbols['core']['address'])
    if bound + 256 > STACK:
        raise ValueError('insufficient private stack margin for synchronous core')
    return {'core_direct_call_bound_bytes': bound, 'private_stack_bytes': STACK,
            'static_core_margin_bytes': STACK - bound, 'functions': rows,
            'interrupt_stack_usage_included': False, 'hardware_high_water_measured': False}


def check_host_record(record, expected, tag):
    return validate_record(record, expected, tag, BASES[1],
                           struct.unpack_from('<I', record, 68)[0] if len(record) == 128 else 0,
                           runs=1, target=False)


def validate_record(record, expected, tag, base, record_address, *, runs, target=True):
    """Pure validator for saved records; performs no device access.

    Supply golden/build tag/address from the exact manifest used for upload.
    The caller must independently establish payload/readback identity.
    """
    if len(record) != 128 or record[:4] != b'HYE1' or record[124:] != b'DONE':
        raise ValueError('bad engine result record')
    u32 = lambda offset: struct.unpack_from('<I', record, offset)[0]
    if base not in BASES or runs < 1:
        raise ValueError('invalid expected slot/run contract')
    required = {4: 1, 8: base, 12: SPAN, 16: runs, 20: 0, 24: FRAMES, 28: len(BLOCKS), 32: 3,
                36: expected['block_results'][-1]['output'], 40: expected['block_results'][-1]['sum'],
                44: expected['block_results'][-1]['history'], 48: expected['replay_output_crc'],
                68: record_address, 72: 128, 76: tag, 80: expected['fixture_crc32'], 84: STACK, 92: 1,
                96: expected['replay_history_crc'], 100: expected['replay_blocks'], 104: FRAMES,
                108: int(target), 112: 0, 116: 1, 120: zlib.crc32(record[:120])}
    if target:
        required.update({52: 895, 56: 9135, 60: 888, 64: 9128})
        if not (base <= record_address <= base + SPAN - 128 and 0 < u32(88) <= STACK):
            raise ValueError('invalid target record address/stack observation')
    else:
        # GCC x86-64 ASan build: a separate ABI, explicitly not target evidence.
        required.update({52: 967, 56: 9167, 60: 960, 64: 9160, 88: 0})
    for offset, value in required.items():
        if u32(offset) != value:
            raise ValueError(f'engine record offset {offset}: expected {value:#x}, got {u32(offset):#x}')
    return {'verified': True, 'runs': runs, 'frames': FRAMES,
            'record_sha256': sha(record), 'private_stack_observed_bytes': u32(88)}


def target_layout(payload, symbols, base, data):
    item = symbols['hyperrig_rom_engine_abi']
    offset = item['address'] - base
    if item['bytes'] != 24 or offset < 0 or offset > len(payload) - 24:
        raise ValueError('missing target ABI metadata')
    pointer, size_t, model, layer, engine, layer_state = struct.unpack_from('<6I', payload, offset)
    if (pointer, size_t, model, layer, engine, layer_state) != (4, 4, 84, 56, 1096, 28):
        raise ValueError('pi32v2 ABI differs from reviewed arena contract')
    m = inspect_a2l(data)
    def take(used, count, width):
        return ((used + 7) & ~7) + count * width
    n = m['channels']
    used = take(take(0, m['layers'], layer), n, 2)
    runtime = take(0, m['layers'], layer_state)
    for p in m['layer_parameters']:
        for count, width in ((n * n * p['kernel'] + n, 2), (n, 8), (n, 4), (n * n, 2), (n, 8)):
            used = take(used, count, width)
        runtime = take(runtime, 128 + (p['kernel'] - 1) * p['dilation'], 12)
    used = take(used, n * m['head_kernel'], 2)
    runtime = take(take(runtime, 384, 4), 384, 4)
    if (used, runtime) != (888, 9128):
        raise ValueError('fixture arena layout changed')
    return {'model_query_bytes': used + 7, 'model_aligned_bytes': used,
            'engine_query_bytes': runtime + 7, 'engine_aligned_bytes': runtime,
            'model_context_bytes': model, 'engine_context_bytes': engine,
            'model_layer_bytes': layer, 'engine_layer_bytes': layer_state,
            'source': 'ABI sizes extracted from target ELF and allocator source; not a hardware reading'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data, expected = golden()
    native = [f'firmware/src/hyperrig_{n}.c' for n in ('dot', 'head', 'rechannel', 'a2l', 'layer', 'engine')]
    source = 'firmware/mini/rom_engine/rom_engine.c'
    trampoline = 'firmware/mini/rom_stack/rom_stack_pi32v2.S'
    paths = sorted((ROOT / 'firmware/mini/rom_engine').glob('*')) + [ROOT / p for p in native]
    paths += sorted((ROOT / 'firmware/include/hyperrig').glob('*.h'))
    paths += [ROOT / trampoline, ROOT / 'firmware/mini/rom_stack/rom_stack.h',
              ROOT / 'tools/verify_mini_rom_stack.py', ROOT / 'firmware/mini/boot/runtime.c', Path(__file__),
              ROOT / 'tools/verify_engine_native.py', ROOT / 'tools/verify_a2l_native.py',
              ROOT / 'tools/layer_machine.py', ROOT / 'tools/rechannel_machine.py',
              ROOT / 'tools/head_machine.py', ROOT / 'tools/bias_machine.py', ROOT / 'tools/dot_machine.py']
    hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths if p.is_file()}
    tag = int(sha(json.dumps(hashes, sort_keys=True).encode() + data + json.dumps(expected, sort_keys=True).encode())[:8], 16)
    write_fixture(data, expected, tag)
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []

    def run(command):
        result = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout

    common = ['-std=c99', '-Wall', '-Wextra', '-Werror', '-Ifirmware/include',
              '-Ifirmware/mini/rom_engine', '-Ibuild/mini-rom-engine']
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         source, *native, 'firmware/mini/rom_engine/host_test.c', '-o', 'build/mini-rom-engine/host-sanitize'])
    host = json.loads(run(['build/mini-rom-engine/host-sanitize']))
    check_host_record(bytes.fromhex(host.pop('record_hex')), expected, tag)
    vendor = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    objects = []
    for path in ['firmware/mini/rom_engine/entry.c', source, *native, 'firmware/mini/boot/runtime.c', trampoline]:
        target = 'build/mini-rom-engine/' + Path(path).stem + '.o'
        run([vendor + 'clang', '-target', 'pi32v2', '-mcpu=r3', *common, '-Os', '-ffreestanding',
             '-fno-builtin', '-DHYPERRIG_ROM_ENGINE_TARGET', '-c', path, '-o', target])
        objects.append(target)
    artifacts, audits = [], []
    bridge = None
    layout = None
    for base in BASES:
        name = f'build/mini-rom-engine/hyperrig-rom-engine-{base:08x}'
        run([vendor + 'ld', '-z', 'max-page-size=0x20', '-z', 'common-page-size=0x20',
             '--defsym', f'PROBE_ADDRESS={base}', '-T', 'firmware/mini/rom_engine/engine.ld',
             *objects, '-o', name + '.elf'])
        payload, symbols, item = inspect_elf((ROOT / (name + '.elf')).read_bytes(), base)
        layout = target_layout(payload, symbols, base, data)
        stub = symbols['hyperrig_mini_rom_run_on_stack']
        stub_offset = stub['address'] - base
        stub_bytes = payload[stub_offset:stub_offset + stub['bytes']]
        decoded_bridge = decode_stack_bridge(stub_bytes)
        bridge = {'code_bytes': len(stub_bytes), 'code_sha256': sha(stub_bytes),
                  'instructions': decoded_bridge, 'incoming_stack_bytes': 8,
                  'verification_report': 'research/mini-rom-stack.json',
                  'hardware_execution_verified': False}
        assembly = run([vendor + 'objdump', '-d', name + '.elf'])
        audit = stack_audit(assembly, symbols)
        audits.append(audit)
        (ROOT / (name + '.bin')).write_bytes(payload)
        (ROOT / (name + '.asm')).write_text(assembly, encoding='utf-8', newline='\n')
        item.update(file=name + '.bin', elf=name + '.elf', assembly=name + '.asm',
                    core_direct_call_stack_bound_bytes=audit['core_direct_call_bound_bytes'])
        artifacts.append(item)
    report = {
        'project': 'HyperRig', 'type': 'ROM synthetic three-layer A2L engine diagnostic',
        'build_tag': tag, 'golden': expected, 'host': {**host, 'asan': True, 'ubsan': True,
            'private_stack_trampoline_executed': False, 'record_verified_against_oracle': True},
        'artifacts': artifacts, 'stack_audit': audits[0], 'stack_bridge': bridge, 'source_sha256': hashes,
        'generated_fixture_header_sha256': sha((OUT / 'fixture.h').read_bytes()),
        'target_arena_layout': layout,
        'protocol': {'selftest': 'FC62', 'read_own_slot': 'FD63', 'record_magic': 'HYE1',
            'record_bytes': 128, 'record_crc_range': [0, 120], 'record_crc_offset': 120,
            'record_done_offset': 124, 'record_version': 1},
        'hardware_execution_verified': False, 'hardware_peripheral_actions': False,
        'firmware_installation_package': False, 'original_A2_capture_executed': False,
        'limits': [
            'Synthetic three-layer fixture is not the original 23-layer A2 capture.',
            'ROM primitive-probe ABI has prior device evidence; this new image has not executed on hardware.',
            'Private stack switches active SP; inherited interrupt handling/stack use is not measured.',
            'Host ASan uses its normal stack, not the target trampoline.',
            'No codec, I2S, DMA, flash access, clock setup or app protocol integration.',
            'ROM send callback return/partial-transfer semantics remain unknown.',
        ],
    }
    (ROOT / 'research/mini-rom-engine.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    checked = subprocess.run([sys.executable, '-B', '-X', 'utf8',
        str(ROOT / 'firmware/mini/rom_engine/test_builder.py')], cwd=ROOT, capture_output=True, text=True)
    if checked.returncode:
        sys.stderr.write(checked.stdout + checked.stderr)
        checked.check_returncode()
    report['offline_validation'] = {'passed': True,
        'source': 'firmware/mini/rom_engine/test_builder.py',
        'scope': 'ELF bounds/mapping corruption, record semantic corruption with valid CRC, core stack audit fail-closed'}
    (ROOT / 'research/mini-rom-engine.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'host': report['host'], 'artifacts': artifacts,
                      'core_stack_bound': audits[0]['core_direct_call_bound_bytes']}, indent=2))


if __name__ == '__main__':
    main()
