"""Run the acoustic block that HyperRig adds at the id 6 of a product build, in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of a built firmware: the list of the effects as the console sends it, the tables, and
the life of a block as the console makes it: added (where the old id was converted into another effect), with the memory it asks for
and without any; its parameters changed the slow way and the fast way that a knob takes, up to the audio side of it; off and on, and
taken away. Then its sound, from the compiled code: silence, what is too loud, what is heard of a low note with 6 and with 12 strings,
and the instructions a block of 128 samples takes, against the cost the firmware counts. The other old id, 24, is the harmonizer, which has
a check of its own (tools/check_mini_harmonizer.py).
Nothing of this is a hardware or audio test: it says nothing of how it sounds, or of the time the pedal needs.

Usage, from the repository root:
    python -B tools/check_mini_effect_block.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product.
"""
from __future__ import annotations

import cmath
import json
import math
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), *[str(ROOT / 'upstream/pi32v2-isa' / d) for d in ('tools/llvm', 'tools/hwtest', '')]]
from elftools.elf.elffile import ELFFile  # noqa: E402
import check_mini_panel as harness  # noqa: E402

ID, PARAMETERS, MEMORY, STATE, SAMPLES = 6, 70, 84, 288, 0x01C70000
NAMES, METADATA = 'L0203a574', 'effect_parameter_metadata'
ROWS = [(0, 1, 0, 'strings'), (0, 100, 70, 'body_pct'), (-12, 12, 0, 'top_db'), (0, 100, 60, 'decay_pct'), (0, 100, 25, 'air_pct'),
        (0, 100, 60, 'doubles_pct'), (-12, 12, 0, 'nivel_db')]
ALLOCATOR, HEAP = 0x01C60000, 0x01C64000            # what stands for the allocator, and what it gives
TICK, CYCLES = 6, 2.1                               # cycles of a tick; cycles an instruction takes, as the firmware's own costs have it
RATE = 48077
# What a footswitch of live mode takes the first of: 0 reverb, 1 delay, 2 modulation (A, B and C); the others are of other pedals. By the id of the effect.
KINDS = {1: 5, 5: 1, 7: 4, 8: 6, 11: 2, 12: 2, 13: 2, 14: 2, 15: 2, 21: 3, 22: 3, 23: 3, 24: 2, 25: 2, 27: 0, 28: 5, 29: 2, 30: 0, 31: 0, 32: 0, 33: 0, 34: 0, 35: 0, 39: 2}


class Check:
    def __init__(self, build):
        self.manifest, app, where = harness.load(build)
        with (build / 'link/app.elf').open('rb') as elf:
            for symbol in ELFFile(elf).get_section_by_name('.symtab').iter_symbols():
                where.setdefault(symbol.name, symbol['st_value'])
        where['link_and_print_send_line'] = where['command_services_console_send']      # where the list of the effects goes out
        where['the_allocator'] = ALLOCATOR
        harness.RECORDED['the_allocator'] = HEAP
        self.where, self.panel = where, harness.Panel(app, self.manifest['application_layout'], where)
        self.cpu, self.mem = self.panel.cpu, self.panel.cpu.mem
        self.rows, self.steps = [], {}
        self.halfwords = self.word(where['hyperrig_acoustic_memory'])
        with (build / 'link/app.elf').open('rb') as elf:
            self.sizes = {s.name: s['st_size'] for s in ELFFile(elf).get_section_by_name('.symtab').iter_symbols() if s['st_info']['type'] == 'STT_FUNC'}

    def row(self, name, good, seen):
        self.rows.append({'check': name, 'held': bool(good), 'seen': seen})

    def word(self, address):
        return struct.unpack('<I', self.mem.read(address, 4))[0]

    def text(self, address):
        out = b''
        while len(out) < 40 and (c := self.mem.read(address + len(out), 1)) != b'\0':
            out += c
        return out.decode('ascii')

    def run(self, name, *args, limit=200_000):
        self.panel.run(name, list(args), limit=limit)
        return self.cpu.R[0]

    def object(self, slot=5):
        return self.where['L01c2c220'] + 480 * slot

    def at(self, slot, offset, form):
        return struct.unpack('<' + form, self.mem.read(self.object(slot) + offset, struct.calcsize(form)))[0]

    def allocator(self, there):
        self.mem.write(self.where['L01c32db0'] + 52, struct.pack('<I', ALLOCATOR if there else 0))

    def add(self, number):
        slot = self.run('effect_setup_create', 0, 99, number, limit=2_000_000)
        return slot - (1 << 32) if slot & 0x80000000 else slot

    def listing(self):
        self.panel.lines.clear()
        self.run('console_reports_effect_table', limit=3_000_000)
        lines = ''.join(self.panel.lines).split('\n')
        types = [x for x in lines if re.match(r'FXT [1-3]?[0-9] ', x)]      # those from 40 on are in tools/check_mini_effects.py
        i = next((k for k, x in enumerate(lines) if x.startswith('FXT 6 ')), None)
        seen = lines[i:i + 9] if i is not None else []
        want = [f'FXT 6 acoustic cost=12500 cat=other mem={2 * self.halfwords + 16}'] + [f'FXT  {k} {n} {a}..{b} ({d})' for k, (a, b, d, n) in enumerate(ROWS)]
        self.row('the list of the effects: 39, this one among them with its parameters, and the end', len(types) == 39 and lines[-2] == 'FXT end' and
                 seen[:8] == want and seen[8].startswith('FXT 7 ir '), {'types': len(types), 'lines': seen})
        self.row('the other old id is the harmonizer', any(x.startswith('FXT 24 harmonizer ') for x in lines), None)

    def tables(self):
        pointers = self.where[NAMES]
        name = lambda k: self.text(self.word(pointers + 4 * k))
        self.row('the name of the id', name(ID) == 'acoustic', name(ID))
        self.row('the other old id is a block of HyperRig too', name(24) == 'harmonizer' and self.run('preset_preflight_needs_conversion', 24) == 0, name(24))
        self.row('no conversion of the block', self.run('preset_preflight_needs_conversion', ID) == 0, None)
        neighbours = [struct.unpack('<hhh', self.mem.read(self.where[METADATA] + 7 * 84 + p * 12, 6)) for p in range(3)]
        self.row('the parameters of the next id', neighbours == [(0, 100, 100), (-30, 12, 0), (0, 8, 0)], neighbours)

    def limits(self):
        """The end of the code in the RAM, as the start-up code tells it to the processor, which faults beyond it."""
        start, end = self.where['phase3_p3_debug_init'], self.where['ultrarig_ram_code_end']
        told = self.mem.read(start, 264).count(b'\xc0\xff' + struct.pack('<I', end))
        code = {n: (self.where[n], self.sizes.get(n, 0)) for n in ('hyperrig_acoustic_process', 'hyperrig_acoustic_run')}
        self.row('the sound code is in the RAM, within what the start-up code lets run there', told == 1 and all(0x01C00000 <= a and a + n <= end and n for a, n in code.values()),
                 {'end': hex(end), 'code': {n: [hex(a), s] for n, (a, s) in code.items()}})

    def ramps(self):
        """The loop of the audio block over the parameters that are on their way: from its first instruction to the one after it."""
        end = self.where['L01c10fd2']
        for _ in range(2):
            end += self.cpu.decode(end)[2]
        self.panel.run('L01c10e58', [0] * 12 + [self.where['L01c2e5a0']], limit=200_000, stop=end)

    def life(self):
        self.mem.write(self.where['L01c32db0'] + 48, struct.pack('<I', 400_000))      # the ticks of a block: there is room here
        self.allocator(False)
        self.row('without memory it is not made', self.add(ID) == -3, None)
        self.allocator(True)
        self.mem.write(HEAP, b'\x5a' * (2 * self.halfwords + 16))
        boost, slot, comp = self.add(2), self.add(ID), self.add(8)
        self.row('a block is added as itself, not converted', slot == 1 and self.at(1, 0, 'B') == ID and self.at(1, 1, 'B') == 1,
                 [slot, self.at(1, 0, 'B') if slot >= 0 else None])
        if slot != 1:
            return False
        asked = [c[1] for c in self.panel.calls if c[0] == 'the_allocator']
        self.row('its memory: asked for once, given, cleared', len(asked) == 1 and asked[0] >= 2 * self.halfwords and self.at(1, MEMORY, 'I') == HEAP and
                 self.mem.read(HEAP, 2 * self.halfwords) == bytes(2 * self.halfwords), {'asked': asked, 'halfwords': self.halfwords})
        self.row('blocks around it are made as ever', (boost, comp) == (0, 2) and self.at(0, 0, 'B') == 2 and self.at(2, 0, 'B') == 8, [boost, comp])
        parameters = [self.at(1, PARAMETERS + 2 * k, 'h') for k in range(7)]
        self.row('it starts at its defaults, with 6 strings', parameters == [r[2] for r in ROWS] and self.at(1, STATE, 'i') == 0, parameters)
        # live mode: the chain is a boost, this block and a compressor; only the last is of a kind, and no footswitch of the MINI takes that one
        kinds = {t + 1: k for t, k in enumerate(struct.unpack('<39i', self.mem.read(self.where['L02034fe0'], 156))) if k >= 0}
        self.row('the kinds of the effects in live mode: this one has none, the others are as they were', kinds == KINDS,
                 {t: k for t, k in kinds.items() if KINDS.get(t) != k})
        kept = harness.RECORDED.pop('preset_application_effect_type')
        self.run('panel_inputs_switch_targets', limit=2_000_000)
        harness.RECORDED['preset_application_effect_type'] = kept
        taken = self.mem.read(self.where[harness.STATE] + 1590, 7)
        self.row('no footswitch takes it in live mode', taken == bytes([0xff] * 6 + [comp]), taken.hex())
        usual = [self.at(1, STATE + 4 * k, 'f') for k in range(7)]
        wrong = []
        for k, (lo, hi, default, name) in enumerate(ROWS):
            for value, kept in ((hi + 30, hi), (lo - 30, lo)):
                self.run('effect_parameter_lifecycle_parameter_commit', 1, k, value & 0xffffffff, limit=2_000_000)
                if self.at(1, PARAMETERS + 2 * k, 'h') != kept:
                    wrong.append([name, value])
            self.run('effect_parameter_lifecycle_parameter_commit', 1, k, default & 0xffffffff, limit=2_000_000)
        self.row('every parameter, kept within its ends, the slow way', not wrong and [self.at(1, STATE + 4 * k, 'f') for k in range(7)] == usual, wrong)
        answer = self.run('effect_parameter_lifecycle_parameter_fast_wrapper', 1, 6, -6 & 0xffffffff, 10, limit=2_000_000)
        before, after = self.at(1, STATE + 24, 'f'), []
        for _ in range(12):                                                             # what the audio does with it, block by block
            self.ramps()
            after.append(self.at(1, STATE + 24, 'f'))
        good = answer == 0 and self.at(1, PARAMETERS + 12, 'h') == -6 and all(abs(v / before - 10 ** (-6 / 20)) < 1e-4 for v in after)
        self.row('a parameter, the fast way, up to the audio', good and self.mem.read(self.where['L01c2e5a0'], 1) == b'\0', [before, after[0], after[-1]])
        self.run('effect_parameter_lifecycle_parameter_commit', 1, 6, 0, limit=2_000_000)
        return True

    def play(self, slot, samples, count=128):
        out, steps = [], []
        for k in range(0, len(samples), count):
            self.mem.write(SAMPLES, struct.pack(f'<{count}i', *samples[k:k + count]))
            a = self.cpu.steps
            self.run('effect_processing_dispatch', self.object(slot), SAMPLES, count, limit=2_000_000)
            steps.append(self.cpu.steps - a)
            out += struct.unpack(f'<{count}i', self.mem.read(SAMPLES, 4 * count))
        return out, steps

    def fresh(self, strings):
        self.mem.write(HEAP, bytes(2 * self.halfwords))
        self.run('effect_parameter_lifecycle_parameter_commit', 1, 0, strings, limit=2_000_000)

    def sound(self):
        for strings, name in ((0, '6'), (1, '12')):
            self.fresh(strings)
            out, steps = self.play(1, [0] * 384)
            self.row(f'{name} strings: silence stays silence', not any(out), max(abs(v) for v in out))
            full = 8388607
            out, _ = self.play(1, [full if i // 109 % 2 else -full for i in range(1024)])
            self.row(f'{name} strings: what is too loud stays within 24 bits', max(abs(v) for v in out) <= 8388607, max(abs(v) for v in out))
        self.mem.write(self.object(1) + MEMORY, bytes(4))
        out, _ = self.play(1, list(range(128)))
        self.row('without memory, as when it is off and memory is short, the sound goes by', out == list(range(128)), None)
        self.mem.write(self.object(1) + MEMORY, struct.pack('<I', HEAP))
        # a low note: what is heard of it and of its octave, after a tenth of a second
        blocks, hertz = 52, 220.0
        x = [int(2 ** 19 * math.sin(2 * math.pi * hertz * i / RATE)) for i in range(128 * blocks)]
        level = {}
        for strings in (0, 1):
            self.fresh(strings)
            out, steps = self.play(1, x)
            self.steps[12 if strings else 6] = steps[-1]
            part = out[-2185:]                                                          # ten periods
            level[strings] = [2 * abs(sum(v * cmath.exp(-2j * math.pi * h * hertz * i / RATE) for i, v in enumerate(part))) / len(part) / 2 ** 19 for h in (1, 2)]
        db = lambda v: 20 * math.log10(v + 1e-9)
        seen = {'6 strings': [round(db(v), 1) for v in level[0]], '12 strings': [round(db(v), 1) for v in level[1]]}
        self.row('a low note: heard with 6 strings, without its octave; with 12 strings, with it', db(level[0][0]) > -10 and db(level[0][1]) < -45 and -20 < db(level[1][1]) < 0 and
                 db(level[1][0]) > -12, seen)
        # a part of a block, as when a parameter moves
        self.fresh(1)
        a, _ = self.play(1, x[:1024])
        self.fresh(1)
        b, _ = self.play(1, x[:1024], 32)
        self.row('quarters of a block give the same sound', a == b, None)
        costs = {}
        for strings in (0, 1):
            self.fresh(strings)
            costs[12 if strings else 6] = self.run('effect_processing_cost', self.object(1))
        counted = {k: round(v * CYCLES / TICK) for k, v in self.steps.items()}
        self.row('the cost the firmware counts is what the code takes, with some to spare', costs == {6: 12500, 12: 32500} and all(costs[k] >= counted[k] for k in costs),
                 {'counted_by_the_firmware': costs, 'steps_of_a_block': self.steps, 'ticks_of_the_steps': counted})

    def end(self):
        self.run('effect_enable_commit', 1, 0, limit=2_000_000)
        off = self.at(1, 1, 'B')
        self.run('effect_enable_commit', 1, 1, limit=2_000_000)
        self.row('off and on', (off, self.at(1, 1, 'B')) == (0, 1), [off, self.at(1, 1, 'B')])
        self.run('effect_ownership_remove', 1, limit=2_000_000)
        self.row('taken away, with the others left', [self.at(k, 2, 'B') for k in range(3)] == [1, 0, 1], [self.at(k, 2, 'B') for k in range(3)])

    def report(self):
        self.listing()
        self.limits()
        self.tables()
        if self.life():
            self.sound()
            self.end()
        return {'build': self.manifest['product'], 'area_sha256': self.manifest['area_sha256'], 'device_io': False, 'hardware_test': False,
                'checks': self.rows, 'held': all(r['held'] for r in self.rows) and len(self.rows) == 26}


def main(argv=None):
    if len(argv or sys.argv[1:]) != 1:
        raise SystemExit(__doc__)
    report = Check((ROOT / (argv or sys.argv[1:])[0]).resolve()).report()
    print(json.dumps(report, indent=1))
    return 0 if report['held'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
