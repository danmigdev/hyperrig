"""Build a RAM reset stub and audit every decoded store before any device use."""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
from types import SimpleNamespace

from dot_machine import DotMachine, ROOT
from pi32v2isa import codec, table


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ResetMachine(DotMachine):
    def __init__(self, code, base, rst):
        self.program = SimpleNamespace(start=base, code=code)
        self.pc, self.steps, self.carry = base, 0, 0
        self.regs = {f'r{i}': 0 for i in range(16)}
        self.rst, self.writes, self.syncs = rst, [], 0
    def read(self, address, size):
        if (address, size) != (0x10000, 4): raise ValueError('unexpected reset read')
        return self.rst
    def write(self, address, value, size):
        if size != 4 or address not in (0x1c7fd80, 0x10000): raise ValueError('unexpected reset write')
        self.writes.append((address, value))
    def step(self):
        text, size, _, _ = self.program.code[self.pc]
        if text == 'csync':
            self.syncs += 1
            self.pc += size
            return True
        if match := re.fullmatch(r'(r\d+) \|= (\d+)', text):
            self.set(match[1], self.value(match[1]) | int(match[2]))
            self.pc += size
            return True
        return super().step()
    def run(self):
        while self.program.code[self.pc][0] != 'goto -2':
            self.step()
            self.steps += 1
            if self.steps > 20: raise ValueError('reset stub escaped budget')
        if self.writes != [(0x1c7fd80, 0), (0x10000, self.rst | 16)] or self.syncs != 2:
            raise ValueError('reset writes differ from marker clear + stock reset bit')


def main():
    out = ROOT / 'build/mini-rom-reset'
    out.mkdir(parents=True, exist_ok=True)
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
    def run(args):
        r = subprocess.run(prefix + args, cwd=ROOT, text=True, capture_output=True)
        if r.returncode:
            print(r.stdout + r.stderr)
            r.check_returncode()
        return r.stdout
    vendor = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    run([vendor + 'clang', '-target', 'pi32v2', '-mcpu=r3', '-c', 'firmware/mini/rom_reset/startup.S',
         '-o', 'build/mini-rom-reset/startup.o'])
    isa, artifacts = table.load(), []
    for base in (0x1c20000, 0x1c28000):
        name = f'build/mini-rom-reset/hyperrig-reset-{base:08x}'
        run([vendor + 'ld', '-z', 'max-page-size=0x20', '-z', 'common-page-size=0x20',
             '--defsym', f'PROBE_ADDRESS={base}', '-T', 'firmware/mini/rom_reset/reset.ld',
             'build/mini-rom-reset/startup.o', '-o', name + '.elf'])
        raw = (ROOT / (name + '.elf')).read_bytes()
        h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
        if h[:4] != (2, 0xf1, 1, base) or h[9] != 1: raise ValueError('reset ELF contract changed')
        p = struct.unpack_from('<8I', raw, h[4])
        if p[0] != 1 or p[2] != base or p[3] != base or p[4] != p[5] or not 0 < p[4] <= 64:
            raise ValueError('reset requires one small file-backed RAM segment')
        data = raw[p[1]:p[1] + p[4]]
        instructions, cursor = {}, 0
        while cursor < len(data):
            item = codec.decode(isa, data, cursor)
            if item is None: raise ValueError('unrecognized reset instruction')
            ins, fields, length = item
            if ins.block: raise ValueError('unexpected reset predicate block')
            instructions[base + cursor] = (codec.format(ins, fields), length, 0, 0)
            cursor += length
        rng = random.Random(81)
        for rst in [0, 16, 0xffffffff] + [rng.randrange(1 << 32) for _ in range(253)]:
            ResetMachine(instructions, base, rst).run()
        (ROOT / (name + '.bin')).write_bytes(data)
        (ROOT / (name + '.asm')).write_text(run([vendor + 'objdump', '-d', name + '.elf']), encoding='utf-8', newline='\n')
        artifacts.append({'kind': 'mini-ram-reset', 'slot': base, 'entry': base,
                          'image_bytes': len(data), 'image_sha256': sha(data), 'elf_sha256': sha(raw),
                          'file': name + '.bin', 'elf': name + '.elf', 'no_flash_writes': True,
                          'decoded_instructions': [v[0] for v in instructions.values()],
                          'simulated_initial_reset_register_cases': 256})
    report = {'project': 'HyperRig', 'artifacts': artifacts, 'hardware_reset_verified': False,
              'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
                    [ROOT / 'firmware/mini/rom_reset/startup.S', ROOT / 'firmware/mini/rom_reset/reset.ld', Path(__file__)]},
              'writes': {'0x01c7fd80': 'zero first RAM marker word', '0x00010000': 'preserve other bits, set bit4'},
              'stock_evidence': 'MINI uboot reset at 0x01c028f4; recovery marker at 0x01c7fd80',
              'limits': ['A jump reply may be lost at reset; never retry automatically.',
                         'Successful return to stock requires fresh USB enumeration and identity verification.',
                         'Load only into a known nonexecuting slot; no application handoff is attempted.']}
    (ROOT / 'research/mini-rom-reset.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(artifacts, indent=2))


if __name__ == '__main__':
    main()
