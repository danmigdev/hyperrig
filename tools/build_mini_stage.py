"""Build the HyperRig loader of the TANK-MINI (firmware/mini_stage) and test its engine on the host. No device is opened.

The engine's tests run with sanitizers: every message, every refusal, every flash fault, and the power cut at each flash
operation of an installation, forwards and back. Then the loader is compiled for the pedal and linked where the pedal's
bootloader puts M-VAVE's loader, no larger than that one, and packed into the form that bootloader stores and decompresses
(ota.bin: a file record, a compression header, LZ4 blocks), which is read back as the bootloader reads it. Filler after the code
makes that form exactly as long as M-VAVE's ota.bin, so that the stock firmware does the same flash work as for an official
update, and its CRC-16 the one by which the loader knows its own kind. The package holds this ota.bin and nothing else.

Usage, from the repository root:
    python -B tools/build_mini_stage.py --output build/mini-stage-NN [--distro Ubuntu]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'upstream/m-bootloader/tools')]
from fwsc import STORED_MAX, UPDATER_LOAD, UPDATER_MAX, updater_code, updater_stream  # noqa: E402
from hyperrig.jieli import crc16, enc  # noqa: E402

SOURCE = 'firmware/mini_stage'
VENDOR = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
RAM_END = 0x01C16800
STOCK_OTA_BYTES = 19958                       # ota.bin of TANK MINI_009 and 011
LOADER_CRC = 0x4852
OWN = ('start.S', 'stage.c', 'engine.c', 'platform.c', 'usb_midi.c')
SHARED = ('firmware/mini_fast/nor.c', 'firmware/mini/boot/runtime.c')
HEADERS = ('engine.h', 'platform.h', 'usb_midi.h', 'stage.ld', 'test_engine.c')
INPUTS = [f'{SOURCE}/{name}' for name in OWN + HEADERS] + list(SHARED) + ['firmware/mini_fast/fast.h', 'tools/build_mini_stage.py']
FLAGS = ['-std=c99', '-Wall', '-Wextra', '-Werror', f'-I{SOURCE}']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def padded(code, wanted=STOCK_OTA_BYTES):
    """The code with filler whose stored form has the wanted size, and whose CRC-16 is LOADER_CRC."""
    noise = b''.join(hashlib.sha256(b'HyperRig loader filler %d' % i).digest() for i in range(1024))
    undo = {crc16(x.to_bytes(2, 'big')): x for x in range(65536)}

    def make(n, plain):
        body = code + bytes(-len(code) % 4) + noise[:n] + b'\0' * plain
        return body + (crc16(body) ^ undo[LOADER_CRC]).to_bytes(2, 'big')

    low, high = 0, UPDATER_MAX - len(code) - 8
    while low < high:                         # the most noise that does not exceed it
        middle = (low + high + 1) // 2
        low, high = (middle, high) if len(updater_stream(make(middle, 0))) <= wanted else (low, middle - 1)
    for n in range(low, max(low - 64, 0), -1):
        for plain in range(0, 300):
            out = make(n, plain)
            if len(out) <= UPDATER_MAX and len(updater_stream(out)) == wanted:
                require(crc16(out) == LOADER_CRC, 'the filler does not give the checksum')
                return out
    raise ValueError('no filler gives the wanted size')


def package(stream):
    """The image the stock firmware is given: a header, a list of one file, and ota.bin."""
    at, entry, head = 0x400, bytearray(80), bytearray(64)
    total = at + (len(stream) + 31 & ~31)
    struct.pack_into('<HHHxxII', entry, 0, 0x64, 0, crc16(stream), at, len(stream))
    struct.pack_into('<I', entry, 16, len(stream) + 31 & ~31)
    entry[64:71] = b'ota.bin'
    stored = enc(bytes(entry))
    struct.pack_into('<HIHHH', head, 2, crc16(stored), total, 1, 4, 0x200)
    head[16:22] = b'AC791N'
    struct.pack_into('<H', head, 0, crc16(bytes(head[2:])))
    out = bytearray(total)
    out[:64], out[64:144], out[at:at + len(stream)] = enc(bytes(head)), stored, stream
    return bytes(out)


def stored(flash, stream, place=0xB7000, record=0xBCF00, name=b'ota-TANK MINI_011'):
    """What the stock firmware leaves in the flash for its bootloader: the loader with its file record, and the update record."""
    head = bytearray(32)
    struct.pack_into('<HIIBBH', head, 2, 0xFFFF, place, len(stream), 0x41, 0xFF, 0xFFFF)
    head[16:27] = b'LOADER.BIN\0'
    struct.pack_into('<H', head, 0, crc16(bytes(head[2:])))
    body = bytearray(80)
    struct.pack_into('<HHH', body, 2, 0x5A0D, 0x5A01, 0x5441)
    body[8:8 + len(name)] = name
    struct.pack_into('<I', body, 72, place)
    struct.pack_into('<H', body, 0, crc16(bytes(body[2:])))
    flash[place:place + 32], flash[place + 32:place + len(stream)] = head, stream[32:]
    flash[record:record + 80] = body


def inspect(elf):
    """The facts of the linked loader; refuses one the bootloader could not start."""
    file = ELFFile(io.BytesIO(elf))
    symbols = {s.name: s['st_value'] for s in file.get_section_by_name('.symtab').iter_symbols() if s.name}
    require(file['e_entry'] == symbols['stage_entry'] == UPDATER_LOAD, 'the entry is not the first byte')
    for section in file.iter_sections():
        require(not (section['sh_type'] in ('SHT_REL', 'SHT_RELA') and section['sh_size']), 'relocations remain')
    require(symbols['__ram_end'] <= RAM_END, 'the loader and its buffers leave the loader RAM')
    return {'load': UPDATER_LOAD, 'payload_bytes': symbols['__payload_end'] - UPDATER_LOAD, 'ram_end': symbols['__ram_end'],
            'ram_limit': RAM_END}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--distro', default='Ubuntu')
    args = parser.parse_args(argv)
    out = (ROOT / args.output).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        parser.error('use a fresh directory under build/')
    out.mkdir(parents=True)
    rel = out.relative_to(ROOT).as_posix()
    prefix = ['wsl.exe', '--distribution', args.distro, '--exec'] if os.name == 'nt' else []

    def run(command):
        done = subprocess.run(prefix + command, cwd=ROOT, capture_output=True, text=True)
        if done.returncode:
            raise SystemExit(f"{' '.join(command)}\n{done.stdout}{done.stderr}")
        return done.stdout

    hashes = {name: sha((ROOT / name).read_bytes()) for name in INPUTS}
    build = 'HRS1-' + sha(''.join(f'{k} {v}\n' for k, v in sorted(hashes.items())).encode())[:11]
    run(['gcc', *FLAGS, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all', f'{SOURCE}/engine.c',
         f'{SOURCE}/test_engine.c', '-o', f'{rel}/test_engine'])
    tests = run([f'{rel}/test_engine']).strip().splitlines()
    objects = []
    for source in [f'{SOURCE}/{name}' for name in OWN] + list(SHARED):
        obj = f'{rel}/{Path(source).stem}.o'
        extra = ['-DHYPERRIG_FAST_TARGET', '-Ifirmware/mini_fast'] if source.startswith('firmware/mini_fast') else []
        run([VENDOR + 'clang', '-target', 'pi32v2', '-mcpu=r3', *([] if source.endswith('.S') else FLAGS), '-Os', '-ffreestanding',
             '-fno-builtin', '-fno-common', '-ffunction-sections', '-fdata-sections', f'-DHYPERRIG_STAGE_BUILD="{build}"', *extra,
             '-c', source, '-o', obj])
        objects.append(obj)
    run([VENDOR + 'ld', '-T', f'{SOURCE}/stage.ld', *objects, '-Map', f'{rel}/stage.map', '-o', f'{rel}/stage.elf'])
    run([VENDOR + 'objcopy', '-O', 'binary', '-j', '.text', f'{rel}/stage.elf', f'{rel}/stage.bin'])
    (out / 'stage.asm').write_text(run([VENDOR + 'objdump', '-d', f'{rel}/stage.elf']), encoding='utf-8', newline='\n')
    facts = inspect((out / 'stage.elf').read_bytes())
    code = (out / 'stage.bin').read_bytes()
    require(len(code) == facts['payload_bytes'] <= UPDATER_MAX, 'the payload is not the linked one, or too large')
    whole = padded(code)
    stream = updater_stream(whole)
    require(updater_code(stream) == whole and len(stream) == STOCK_OTA_BYTES <= STORED_MAX, 'the stored form does not read back')
    (out / 'stage-code.bin').write_bytes(whole)
    (out / 'stage-ota.bin').write_bytes(stream)
    (out / 'stage-package.bin').write_bytes(package(stream))
    report = {'kind': 'hyperrig-mini-loader', 'build': build, **facts, 'stored_bytes': len(stream), 'stored_limit': STORED_MAX,
              'code_sha256': sha(code), 'padded_bytes': len(whole), 'padded_sha256': sha(whole), 'stored_sha256': sha(stream),
              'package_sha256': sha(package(stream)), 'writable': [[0x4000, 0x82000], [0xBF000, 0xFF000]], 'application_widened_by_begin_up_to': 0xA0000,
              'host_tests': tests, 'source_sha256': hashes, 'device_access_performed': False, 'hardware_tested': False}
    (out / 'report.json').write_bytes((json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in report.items() if k != 'source_sha256'}, indent=2))
    return report


if __name__ == '__main__':
    main()
