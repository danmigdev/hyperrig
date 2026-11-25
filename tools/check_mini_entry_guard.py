"""Run the recovery guard of a built MINI application from its first instruction, in the pi32v2 simulator. Offline.

The guard is the first thing a HyperRig application does on the pedal: while any of the three footswitches is held it
asks for the ROM's update mode instead of starting, so an application that hangs later can still be replaced. It runs here
from the bytes of app.bin, from the entry the bootloader jumps to, with port A simulated (PA10, PA0 and PA3, low when
pressed, high through the pull-up), for every combination of switches, for switches released too early, and for pins left
as outputs. Checked: what is held for the whole time leads to the update mode and nothing else does; the start-up goes on
with the bootloader's registers untouched and the pins as they were found; no other register is written.

The two delay loops are run for two turns only: their length on the pedal is not known from here. Reading the special
registers, which the simulator does not keep, gives zero. This is no hardware test.

Usage, from the repository root:
    python -B tools/check_mini_entry_guard.py BUILD [BUILD ...]
BUILD is an output directory of tools/build_hyperrig_mini_image.py. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/pi32v2-isa'), str(ROOT / 'upstream/pi32v2-isa/tools/llvm'),
                str(ROOT / 'upstream/pi32v2-isa/tools/hwtest')]
import mini_sim as sim  # noqa: E402
from pi32v2isa import codec  # noqa: E402

BASE, RESUME, RESUME_OFFSET = 0x02000120, 'phase3_p14_chip_entry', 12
PORT, RESET, MAILBOX = 0x50000, 0x10000, 0x01C7FD80
OUT, IN, DIR, DIE, PU, PD = range(0, 24, 4)
PINS = {'left': 1 << 10, 'middle': 1 << 0, 'right': 1 << 3}
MASK = 0x409
MARKER = b'usb_update_mode\0'
SAMPLES = 32
FOUND = {OUT: 0x1234, DIR: 0xFFFF, DIE: 0xF0F0, PU: 0x0F00, PD: 0x00F8}


class Reset(Exception):
    pass


class Board(sim.Memory):
    """Port A and the reset bit; any other peripheral register is refused."""

    def __init__(self, held, direction):
        super().__init__()
        self.port = dict(FOUND) | {DIR: direction}
        self.held, self.reads, self.reset, self.written = held, 0, False, set()

    def read(self, a, n):
        if 0x10000 <= a < 0x100000:
            assert n == 4, (hex(a), n)
            if a == PORT + IN:
                pressed = self.held(self.reads)
                self.reads += 1
                # a pin is seen only as a digital input, and high only through its pull-up
                seen = self.port[DIR] & self.port[DIE] & self.port[PU] & ~self.port[PD]
                return (seen & MASK & ~sum(PINS[p] for p in pressed)).to_bytes(4, 'little')
            if PORT <= a < PORT + 24:
                return self.port[a - PORT].to_bytes(4, 'little')
            if a == RESET:
                return (0x40).to_bytes(4, 'little')
            raise AssertionError(f'reads {a:#x}')
        return super().read(a, n)

    def write(self, a, data):
        if 0x10000 <= a < 0x100000:
            value = int.from_bytes(data, 'little')
            assert len(data) == 4, hex(a)
            self.written.add(a)
            if a == RESET:
                assert value == 0x50, hex(value)
                raise Reset
            assert a in (PORT + DIR, PORT + DIE, PORT + PU, PORT + PD), f'writes {a:#x}'
            before = self.port[a - PORT]
            assert (before ^ value) & ~MASK == 0, f'changes other bits of {a:#x}'
            self.port[a - PORT] = value
            return
        super().write(a, data)


def enter(app, resume, held, direction=0xFFFF):
    """One power-on: ('rom' or 'start', board, registers)."""
    board = Board(held, direction)
    cpu = sim.CPU()
    cpu.mem = board
    board.write(BASE, app)
    registers = [0x01C7FE08, *range(0x11110001, 0x11110010)]
    cpu.R[:16] = registers
    cpu.pc, cpu.sp, cpu.rets = BASE, 0x01C09000, 0x01C05301
    try:
        while cpu.pc != resume:
            insn, raw, size = cpu.decode(cpu.pc)
            text = codec.format(insn, raw)
            # the delay loops: a nop with its counter in r2
            if text == 'nop' and cpu.R[2] > 2:
                cpu.R[2] = 2
            if special(cpu, text, size):
                continue
            cpu.step()
            if cpu.steps > 200_000:
                raise RuntimeError('does not end')
    except Reset:
        return 'rom', board, cpu
    return 'start', board, cpu


def special(cpu, text, size):
    """The moves of special registers, which the simulator has no models for."""
    if text.startswith('ssp = '):
        pass
    elif text.startswith('sp = ') and text[5:].isdigit():
        cpu.sp = int(text[5:])
    elif text in ('[--sp] = {psr, rets, reti}', '[--sp] = {reti, rets, psr}'):
        cpu.sp -= 12
        cpu.mem.write(cpu.sp, bytes(8) + cpu.rets.to_bytes(4, 'little'))
        cpu.saved_rets = cpu.rets
    elif text in ('{psr, rets, reti} = [sp++]', '{reti, rets, psr} = [sp++]'):
        cpu.sp += 12
        cpu.rets = cpu.saved_rets
    else:
        return False
    cpu.pc += size
    return True


def check(app, resume):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    always = lambda pressed: lambda n: pressed
    for count in range(4):
        for pressed in itertools.combinations(PINS, count):
            where, board, cpu = enter(app, resume, always(pressed))
            left = {k: v for k, v in board.port.items()}
            name = ' and '.join(pressed) or 'no switch'
            if pressed:
                row(f'{name} held: the update mode', where == 'rom' and cpu.mem.read(MAILBOX, 16) == MARKER and
                    board.reads == SAMPLES, (where, board.reads))
            else:
                row('no switch: the start-up goes on, pins and registers as they were', where == 'start' and
                    cpu.R[:16] == [0x01C7FE08, *range(0x11110001, 0x11110010)] and cpu.rets == 0x01C05301 and
                    left == FOUND and RESET not in board.written and cpu.mem.read(MAILBOX, 16) == bytes(16),
                    (where, [hex(r) for r in cpu.R[:16]], hex(cpu.rets), left))
    for released in (0, 1, 15, SAMPLES - 1):
        where, board, cpu = enter(app, resume, lambda n, r=released: ('middle',) if n < r else ())
        row(f'middle released before sample {released + 1} of {SAMPLES}: the start-up goes on', where == 'start' and
            {k: v for k, v in board.port.items()} == FOUND, where)
    where, board, cpu = enter(app, resume, lambda n: (list(PINS)[n % 3],))
    row('the pressed switch may change during the hold', where == 'rom', where)
    # pins found as outputs are made inputs first, and stay inputs
    where, board, cpu = enter(app, resume, always(()), direction=0xFFFF & ~MASK)
    row('pins found as outputs end as inputs, and the start-up goes on', where == 'start' and
        board.port[DIR] & MASK == MASK, (where, hex(board.port[DIR])))
    where, board, cpu = enter(app, resume, always(('right',)), direction=0xFFFF & ~MASK)
    row('a switch held with the pins found as outputs leads to the update mode', where == 'rom', where)
    return rows


def run(build):
    manifest = json.loads((build / 'build-manifest.json').read_bytes())
    with (build / 'link/app.elf').open('rb') as elf:
        found = {s['st_value'] for s in ELFFile(elf).get_section_by_name('.symtab').iter_symbols() if s.name == RESUME}
    if len(found) != 1:
        raise SystemExit(f'{RESUME} found {len(found)} times')
    rows = check((build / 'app.bin').read_bytes(), min(found) + RESUME_OFFSET)
    return {'build': build.as_posix(), 'area_sha256': manifest['area_sha256'], 'checks': rows, 'held': all(r['held'] for r in rows)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('builds', type=Path, nargs='+', metavar='BUILD')
    args = parser.parse_args(argv)
    results = [run(build) for build in args.builds]
    for result in results:
        print(result['build'], result['area_sha256'][:16])
        for r in result['checks']:
            print('  ', 'ok  ' if r['held'] else 'FAIL', r['check'], '' if r['held'] else r['seen'])
    print(json.dumps({'held': all(r['held'] for r in results), 'hardware_test': False}))
    return 0 if all(r['held'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
