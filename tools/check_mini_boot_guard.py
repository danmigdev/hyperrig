"""Run the start count of a built MINI application over several starts, in the pi32v2 simulator. Offline.

The application counts its starts in a word of RAM that a reset keeps (0x01C7FDF0). A start that gets healthy clears the
count: PING clears it, and so does the application itself once it runs. The third start in a row that does not, asks the ROM
for the update mode instead of starting; the watchdog, which this code starts, turns a hang into a reset and so into a counted
start. Nobody has to press anything. The code is UltraRig's, unchanged in every HyperRig build; it runs here from the bytes of
app.bin, with the reset registers, the record of the last clock and the two ways out recorded instead of run.

Whether the RAM of the TANK-MINI keeps the word over a watchdog reset is not known from here. This is no hardware test.

Usage, from the repository root:
    python -B tools/check_mini_boot_guard.py BUILD [BUILD ...]
BUILD is an output directory of tools/build_hyperrig_mini_image.py. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/pi32v2-isa'), str(ROOT / 'upstream/pi32v2-isa/tools/llvm'),
                str(ROOT / 'upstream/pi32v2-isa/tools/hwtest')]
import mini_sim as sim  # noqa: E402

BASE, RAM, COUNT = 0x02000120, 0x01C00000, 0x01C7FDF0
MAIN, CLEAR = 'phase3_p3_main', 'bond_records_and_prints_boot_clear'
START, UPDATE = 'phase3_p3_wdt_init', 'phase3_p7_go_mask_usb_updata'
RECORDED = ('storage_coordination_irq_enter', 'storage_fault_read_register', 'boundary_hooks_record_check',
            'boundary_hooks_record_pack', 'boundary_hooks_record_store')


class Retained(sim.Memory):
    """Plain memory; the one register this code reads (the reset cause) answers zero."""

    def read(self, a, n):
        if 0x10000 <= a < 0x100000:
            return bytes(n)
        return super().read(a, n)


class Pedal:
    def __init__(self, build):
        manifest = json.loads((build / 'build-manifest.json').read_bytes())
        self.layout, self.area = manifest['application_layout'], manifest['area_sha256']
        self.app = (build / 'app.bin').read_bytes()
        wanted, found = {MAIN, CLEAR, START, UPDATE, *RECORDED}, {}
        with (build / 'link/app.elf').open('rb') as elf:
            for symbol in ELFFile(elf).get_section_by_name('.symtab').iter_symbols():
                if symbol.name in wanted:
                    found.setdefault(symbol.name, set()).add(symbol['st_value'])
        wrong = {n: found.get(n) for n in wanted if len(found.get(n, ())) != 1}
        if wrong:
            raise SystemExit(f'symbols not found once: {wrong}')
        self.where = {n: min(v) for n, v in found.items()}
        self.kept = bytes(16)                # the retained words, zero after the power was off

    def power(self, kept):
        cpu = sim.CPU()
        cpu.mem = Retained()
        cpu.mem.write(BASE, self.app)
        at = int(self.layout['ram_image_load'], 16) - BASE
        cpu.mem.write(RAM, self.app[at:at + self.layout['ram_image_size']])
        cpu.mem.write(int(self.layout['bss_start'], 16), bytes(self.layout['bss_size']))
        cpu.mem.write(COUNT, kept)
        return cpu

    def start(self, healthy=False):
        """One start: 'start' when the application goes on (to its watchdog), 'update' when it asks for the update mode."""
        cpu = self.power(self.kept)
        services = {self.where[n] for n in RECORDED}
        cpu.rets, cpu.pc = sim.RETURN, self.where[MAIN]
        while cpu.pc not in (self.where[START], self.where[UPDATE]):
            if cpu.pc in services:
                cpu.R[0], cpu.pc = 0, cpu.rets
                continue
            cpu.step()
            if cpu.steps > 20_000:
                raise RuntimeError('the start does not get on')
        how = 'start' if cpu.pc == self.where[START] else 'update'
        if healthy:
            cpu.call(self.where[CLEAR], [])
        self.kept = cpu.mem.read(COUNT, 16)
        return how


def check(build):
    rows = []

    def row(name, starts, wanted):
        rows.append({'check': name, 'held': starts == wanted, 'seen': starts})

    pedal = Pedal(build)
    row('three starts in a row that do not get healthy: the third is the update mode', [pedal.start() for _ in range(3)],
        ['start', 'start', 'update'])
    row('after the update mode the count begins again', [pedal.start() for _ in range(3)], ['start', 'start', 'update'])
    pedal = Pedal(build)
    row('a healthy start clears the count', [pedal.start(), pedal.start(healthy=True), pedal.start(), pedal.start(), pedal.start()],
        ['start', 'start', 'start', 'start', 'update'])
    pedal = Pedal(build)
    row('healthy starts never lead to the update mode', [pedal.start(healthy=True) for _ in range(12)], ['start'] * 12)
    pedal = Pedal(build)
    seen = []
    for kept in (bytes(16), b'\xff' * 16, bytes(range(16)), b'\x00\x00\x9c\x7a' + b'\x05' * 12):
        pedal.kept = kept
        seen.append(pedal.start())
    row('a word that is no count (power was off) counts as a first start', seen, ['start'] * 4)
    return {'build': build.as_posix(), 'area_sha256': pedal.area, 'checks': rows, 'held': all(r['held'] for r in rows)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('builds', type=Path, nargs='+', metavar='BUILD')
    args = parser.parse_args(argv)
    results = [check(build) for build in args.builds]
    for result in results:
        print(result['build'], result['area_sha256'][:16])
        for r in result['checks']:
            print('  ', 'ok  ' if r['held'] else 'FAIL', r['check'], '' if r['held'] else r['seen'])
    print(json.dumps({'held': all(r['held'] for r in results), 'hardware_test': False}))
    return 0 if all(r['held'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
