"""Run the harmonizer block that HyperRig adds at the id 24 of a product build, in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of a built firmware: the list of the effects as the console sends it, the tables, the life of
the block (added, with the memory it asks for and without any; its parameters; off and on; scenes; a preset stored and read; taken away) and
its sound, which must be that of tools/harmonizer_model.py, sample by sample: notes, a bend, a chord, what is too loud, silence, parameters
that move, parts of a block. Then what the compiled code takes against the cost the firmware counts, and that no instruction is of the form
that resets the processor. Nothing of this is a hardware or audio test: it says nothing of how it sounds, or of the time the pedal needs.

Usage, from the repository root:
    python -B tools/check_mini_harmonizer.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. It takes about ten minutes.
"""
from __future__ import annotations

import json
import math
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), *[str(ROOT / 'upstream/pi32v2-isa' / d) for d in ('tools/llvm', 'tools/hwtest', '')]]
from elftools.elf.elffile import ELFFile  # noqa: E402
import check_mini_effect_block as block  # noqa: E402
import check_mini_panel as harness  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402
import harmonizer_model as model  # noqa: E402

ID, PARAMETERS, MEMORY, STATE, SAMPLES, HEAP = 24, 70, 84, 288, block.SAMPLES, block.HEAP
ROWS = [(0, 11, 0, 'key'), (0, 10, 0, 'scale'), (-7, 7, 2, 'voice1'), (-7, 7, 0, 'voice2'), (0, 100, 50, 'balance_pct'), (0, 100, 50, 'mezcla_pct'),
        (-12, 12, 0, 'nivel_db')]
COST, SECOND, CYCLES, TICK = 11000, 2500, block.CYCLES, block.TICK         # what the firmware counts, and more for a second voice
RATE, CHECKS, TUNED_TO = 48077, 34, 144              # where the settings have the tuner's A


def strings(events, blocks):
    """Plucked strings: (block, pitch, semitones it is bent by, level); a new note stops the one before."""
    out = [0.0] * (128 * blocks)
    events = [*events, (blocks, 0, 0, 0)]
    for (at, pitch, bend, level), (until, *_) in zip(events, events[1:]):
        phase = 0.0
        for i in range(128 * (until - at)):
            t = i / RATE
            hertz = 440 * 2 ** ((pitch + bend * 0.5 * (1 - math.cos(math.pi * min(max((t - 0.03) / 0.04, 0), 1))) - 69) / 12)
            phase += 2 * math.pi * hertz / RATE
            out[128 * at + i] += level * (1 - math.exp(-t * 1500)) * sum(math.sin(k * phase + 0.4 * k) * math.exp(-t * (1 + k)) / k for k in range(1, 9))
    return [round(v * 2 ** 21) for v in out]


class Check(scenes.Pedal):
    def __init__(self, build):
        super().__init__(build)
        self.build = Path(build)
        self.rows = []
        self.halfwords = self.word(self.where['hyperrig_harmonizer_memory'])
        self.steps = []

    def row(self, name, good, seen=None):
        self.rows.append({'check': name, 'held': bool(good), 'seen': seen})

    def field(self, slot, offset, form):
        return block.Check.at(self, slot, offset, form)

    def words(self, slot):
        return list(struct.unpack('<10I', self.mem.read(self.object(slot) + STATE, 40)))

    def commit(self, slot, *values):
        for k, v in enumerate(values):
            self.run('effect_parameter_lifecycle_parameter_commit', slot, k, v & 0xFFFFFFFF, limit=4_000_000)

    def listing(self):
        self.panel.lines.clear()
        self.run('console_reports_effect_table', limit=6_000_000)
        lines = ''.join(self.panel.lines).split('\n')
        types = [x for x in lines if re.match(r'FXT [0-9]+ ', x)]
        i = next((k for k, x in enumerate(lines) if x.startswith('FXT 24 ')), None)
        seen = lines[i:i + 9] if i is not None else []
        want = [f'FXT 24 harmonizer cost={COST} cat=mod mem={2 * self.halfwords + 16}'] + [f'FXT  {k} {n} {a}..{b} ({d})' for k, (a, b, d, n) in enumerate(ROWS)]
        self.row('the list of the effects: 39 of the application, this one among them with its parameters, and the end',
                 sum(int(re.match(r'FXT (\d+)', x)[1]) < 40 for x in types) == 39 and lines[-2] == 'FXT end' and seen[:8] == want and seen[8].startswith('FXT 25 doubler '), {'types': len(types), 'lines': seen})

    def tables(self):
        name = self.text(self.word(self.where[block.NAMES] + 4 * ID))
        self.row('the name of the id', name == 'harmonizer', name)
        self.row('no conversion of the block, or of any other', not any(self.run('preset_preflight_needs_conversion', k) for k in range(40)))
        after = [struct.unpack('<hhh', self.mem.read(self.where[block.METADATA] + 25 * 84 + p * 12, 6)) for p in range(3)]
        before = [struct.unpack('<hhh', self.mem.read(self.where[block.METADATA] + 23 * 84 + p * 12, 6)) for p in (5, 6)]
        self.row('the parameters of the ids around it', after == [(5, 40, 20), (-20, 20, 7), (0, 100, 50)] and before == [(-30, 6, -8), (0, 3, 3)], [before, after])
        raw = {}
        with (self.build / 'link/app.elf').open('rb') as elf:
            for s in ELFFile(elf).get_section_by_name('.symtab').iter_symbols():
                if s['st_info']['type'] == 'STT_FUNC':
                    raw[s.name] = (s['st_value'], s['st_size'])
        start, end = sum(raw['hyperrig_acoustic_process']), self.where['ultrarig_ram_code_end']
        told = self.mem.read(self.where['phase3_p3_debug_init'], 264).count(b'\xc0\xff' + struct.pack('<I', end))
        inside = all(start <= raw[n][0] and sum(raw[n]) <= end for n in ('hyperrig_harmonizer_run', 'hyperrig_harmonizer_process'))
        self.row('the sound code is in the RAM, within what the start-up code lets run there', told == 1 and inside, {'end': hex(end), 'from': hex(start)})
        forms, at = [], start
        while at < sum(raw['hyperrig_harmonizer_process']):
            insn, bits, size = self.cpu.decode(at)
            forms.append(harness.codec.format(insn, bits))
            at += size
        products = [x for x in forms if '*[' in x or ']*' in x]
        self.row('its products are of the form the application has too, none of the one that resets the processor',
                 len(products) > 40 and all(re.search(r'\+= h\[r\d+ \+\+= [24]\]\*\[r\d+ \+\+= [48]\] \(s\)$', x) for x in products), [len(products), sorted(set(products))[:4]])

    def settings(self):
        wrong, at = [], 0x01C78400
        for kind in range(11):
            for steps in range(-7, 8):
                p = ((kind * 5 + steps) % 12, kind, steps, -steps, (kind * 37 + steps) % 101, (steps * 41 + kind) % 101, (kind + steps) % 25 - 12)
                self.mem.write(at + 64, struct.pack('<7h', *p))
                self.run('hyperrig_harmonizer_settings', at, at + 64, limit=400_000)
                got = list(struct.unpack('<10I', self.mem.read(at, 40)))
                if got != model.Settings(p).words():
                    wrong.append([p, got, model.Settings(p).words()])
        self.row('every scale and interval, in some key: the intervals of the twelve notes are those of the model', not wrong, wrong[:2])
        c = model.Settings((0, 0, 2, 0, 50, 50, 0)).steps[0]
        self.row('a third above in C major: E E F G G A A B B C D D', [(n + v) % 12 for n, v in enumerate(c)] == [4, 4, 5, 7, 7, 9, 9, 11, 11, 0, 2, 2], c)

    def life(self):
        self.allocator(False)
        self.row('without memory it is not made', self.add(ID) == -3)
        self.allocator(True)
        self.mem.write(HEAP, b'\x5a' * (2 * self.halfwords + 16))
        self.panel.calls.clear()
        boost, slot, comp = self.add(2), self.add(ID), self.add(8)
        asked = [c[1] for c in self.panel.calls if c[0] == 'the_allocator']
        self.row('a block is added as itself, not converted', (boost, slot, comp) == (0, 1, 2) and self.field(1, 0, 'B') == ID and self.field(1, 1, 'B') == 1, [boost, slot, comp])
        self.row('its memory: asked for once, given, cleared', len(asked) == 1 and asked[0] >= 2 * self.halfwords and self.field(1, MEMORY, 'I') == HEAP and
                 self.mem.read(HEAP, 2 * self.halfwords) == bytes(2 * self.halfwords), {'asked': asked, 'halfwords': self.halfwords})
        parameters = [self.field(1, PARAMETERS + 2 * k, 'h') for k in range(7)]
        self.row('it starts at its defaults', parameters == [r[2] for r in ROWS] and self.words(1) == model.Settings(parameters).words(), parameters)
        wrong = []
        for k, (lo, hi, default, name) in enumerate(ROWS):
            for value, kept in ((hi + 30, hi), (lo - 30, lo), (default, default)):
                self.run('effect_parameter_lifecycle_parameter_commit', 1, k, value & 0xFFFFFFFF, limit=4_000_000)
                if self.field(1, PARAMETERS + 2 * k, 'h') != kept:
                    wrong.append([name, value])
        self.row('every parameter, kept within its ends, the slow way', not wrong and self.words(1) == model.Settings(parameters).words(), wrong)
        answers = []
        for k, value in ((0, 9), (1, 1), (2, 4), (3, -3), (4, 30), (5, 60), (6, -6)):
            answers.append(self.run('effect_parameter_lifecycle_parameter_fast_wrapper', 1, k, value & 0xFFFFFFFF, 10, limit=4_000_000))
            for _ in range(12):
                self.ramps()
        moved = [self.field(1, PARAMETERS + 2 * k, 'h') for k in range(7)]
        self.row('every parameter, the fast way, up to the audio', not any(answers) and moved == [9, 1, 4, -3, 30, 60, -6] and self.words(1) == model.Settings(moved).words() and
                 self.mem.read(self.where['L01c2e5a0'], 1) == b'\0', [answers, moved])
        kept = harness.RECORDED.pop('preset_application_effect_type', None)
        self.run('panel_inputs_switch_targets', limit=2_000_000)
        if kept is not None:
            harness.RECORDED['preset_application_effect_type'] = kept
        taken = self.mem.read(self.where[harness.STATE] + 1590, 7)
        self.row('live mode: a footswitch takes it as the first modulation of the chain', taken[2] == 1 and taken[0] == taken[1] == 0xFF, taken.hex())

    def play(self, samples, count=128):
        out = []
        for k in range(0, len(samples), count):
            self.mem.write(SAMPLES, struct.pack(f'<{count}i', *samples[k:k + count]))
            a = self.cpu.steps
            self.run('effect_processing_dispatch', self.object(1), SAMPLES, count, limit=4_000_000)
            self.steps.append(self.cpu.steps - a)
            out += struct.unpack(f'<{count}i', self.mem.read(SAMPLES, 4 * count))
        return out

    def fresh(self, *parameters, a=440.0):
        self.mem.write(HEAP, bytes(2 * self.halfwords))
        self.mem.write(self.object(1) + 10, bytes(2))
        self.mem.write(self.where[harness.SETTINGS] + TUNED_TO, struct.pack('<f', a))
        self.commit(1, *parameters)
        self.steps.clear()
        return model.Harmonizer(parameters, a)

    def same(self, name, mine, samples, count=128, and_also=lambda out: True):
        out = self.play(samples, count)
        want = mine.run(samples)
        bad = [i for i, (a, b) in enumerate(zip(out, want)) if a != b]
        self.row(name, not bad and and_also(out), {'different': len(bad), 'first': bad[:1], 'loudest': max(map(abs, out))})

    def sound(self):
        parameters = (9, 1, 2, -3, 40, 60, 2)
        mine = self.fresh(*parameters)
        self.same('silence stays silence', mine, [0] * 512, and_also=lambda out: not any(out))
        x = strings([(0, 64, 0, 0.8), (22, 45, 0, 1.0), (46, 62, 2, 0.7)], 88)
        heard = []
        for k in range(0, len(x), 1408):                                                # eleven blocks at a time, for what the listening says
            out, want = self.play(x[k:k + 1408]), mine.run(x[k:k + 1408])
            heard.append([out == want, mine.note > 0, round(mine.pitch / 256, 1), round(mine.voices[0].interval / 256, 1), round(mine.voices[1].interval / 256, 1)])
        self.row('three notes and a bend are those of the model', all(h[0] for h in heard), heard)
        self.row('they are heard as E, A and a D that is bent to E, with the thirds and the fourths of A minor',
                 [h[1:] for h in (heard[1], heard[3], heard[7])] == [[True, 64.0, 3.0, -5.0], [True, 45.0, 3.0, -5.0], [True, 64.0, 3.0, -5.0]], heard)
        self.steps.clear()
        chord = [sum(round(2 ** 20 * math.sin(2 * math.pi * f * i / RATE)) for f in (110.0, 164.8, 220.0, 277.2)) for i in range(128 * 44)]
        self.same('a chord is that of the model', mine, chord, and_also=lambda out: mine.chord == 1 and not mine.note)
        two = max(self.steps)
        # the interval of a chord is that of its root, whatever the note before it was; in C major a third above
        for name, root, shape in (('a power chord on E', 40, (0, 7)), ('a power chord on F, with the octave', 41, (0, 7, 12)), ('a power chord on B, after a note', 47, (0, 7))):
            mine = self.fresh(0, 0, 2, 0, 50, 50, 0)
            before = strings([(0, 64 if root == 41 else 65, 0, 0.8)], 10)
            tones = [(440 * 2 ** ((root + s - 69) / 12), 1 / (1 + s / 12)) for s in shape]
            x = before + [round(2 ** 20 * (1 - math.exp(-i / 60)) * sum(a * math.sin(2 * math.pi * k * f * i / RATE) / k for f, a in tones for k in (1, 2, 3, 4, 5))) for i in range(128 * 36)]
            want = mine.settings.steps[0][root % 12]
            self.same(f'{name}: the interval of its root', mine, x, and_also=lambda out: mine.chord == 1 and mine.home == root % 12 and mine.voices[0].interval == want * 256)
        # the tuner's A: the same note is in tune with another one, and what is no number for one is 440
        for a, note in ((432.0, 57), (445.5, 64), (0.0, 57)):
            mine = self.fresh(0, 0, 2, 0, 50, 50, 0, a=a)
            x = [round(v * 2 ** 21) for v in (math.sin(2 * math.pi * (a or 440) * 2 ** ((note - 69) / 12) * i / RATE) * (1 - math.exp(-i / 60)) for i in range(128 * 20))]
            self.same(f'the tuner at {a or "nothing"}: {note} is heard as it is', mine, x, and_also=lambda out: mine.note > 0 and abs(mine.pitch - note * 256) < 6)
        mine = self.fresh(*parameters)
        self.play(chord[:128 * 4])
        mine.run(chord[:128 * 4])
        self.same('what is too loud stays within 24 bits', mine, [8388607 if i // 109 % 2 else -8388608 for i in range(1280)], and_also=lambda out: max(map(abs, out)) <= 8388607)
        # parameters that move while it sounds
        self.commit(1, 4, 0, 7, -7, 50, 100, 0)
        mine.settings = model.Settings((4, 0, 7, -7, 50, 100, 0))
        self.same('a change of every parameter while it sounds', mine, strings([(0, 57, 0, 1.0)], 14))
        self.same('quarters of a block give the same sound', mine, strings([(0, 69, 0, 1.0)], 6), 32)
        # off and on as the audio does it, with a fade of four blocks: when it comes on, what it remembers is old
        mine, seen = self.fresh(*parameters), []
        for i in range(14):
            if i in (2, 8):
                self.run('effect_enable_commit', 1, int(i == 8), limit=2_000_000)
                mine.started = int(i == 2)
            part = x[128 * i:128 * i + 128]
            self.mem.write(SAMPLES, struct.pack('<128i', *part))
            self.run('effect_processing_individual', 1, SAMPLES, 128, limit=4_000_000)
            out = list(struct.unpack('<128i', self.mem.read(SAMPLES, 512)))
            want = part if i in (6, 7) else mine.run(part)
            seen.append(out == want)
        self.row('off and on, with the fades of the application: off it goes by, and on it is as started anew',
                 seen == [True] * 2 + [False] * 4 + [True] * 2 + [False] * 4 + [True] * 2, seen)
        self.mem.write(self.object(1) + 10, bytes(2))
        self.mem.write(self.object(1) + MEMORY, bytes(4))
        out = self.play(list(range(128)))
        self.row('without memory, as when it is off and memory is short, the sound goes by', out == list(range(128)))
        self.mem.write(self.object(1) + MEMORY, struct.pack('<I', HEAP))
        worst = {2: two}
        for one, count in ((2, 1), (0, 0)):
            mine = self.fresh(0, 0, one, 0, 50, 50, 0)
            self.play(chord[:128 * 24])
            worst[count] = max(self.steps)
        costs = {}
        for count, values in ((0, (0, 0, 0, 0)), (1, (0, 0, 0, 5)), (2, (0, 0, 3, 5))):
            self.commit(1, *values, 50, 50, 0)
            costs[count] = self.run('effect_processing_cost', self.object(1))
        ticks = {k: round(v * CYCLES / TICK) for k, v in worst.items()}
        self.row('the cost the firmware counts is what the code takes, with some to spare', costs == {0: COST, 1: COST, 2: COST + SECOND} and all(costs[k] >= ticks[k] for k in costs),
                 {'counted_by_the_firmware': costs, 'most_steps_of_a_block': worst, 'ticks_of_the_steps': ticks})

    def preserved(self):
        """Scenes and a stored preset keep it, with its parameters."""
        self.setting(harness.G_PRESET, -1)
        self.setting(88, -1)
        self.wipe()
        first, second = (4, 1, 2, 4, 50, 50, 0), (7, 3, -5, 0, 20, 80, -3)
        self.commit(1, *first)
        self.say('SNAPSAVE 0')
        self.commit(1, *second)
        self.say('SNAPSAVE 1')
        seen = []
        for k in (0, 1, 0):
            self.say(f'SNAP {k}')
            for _ in range(30):
                self.ramps()
            seen.append((tuple(self.field(1, PARAMETERS + 2 * i, 'h') for i in range(7)), self.words(1) == model.Settings((first, second, first)[k if k < 2 else 0]).words()))
        self.row('scenes keep its parameters', seen == [(first, True), (second, True), (first, True)], seen)
        self.setting(harness.G_PRESET, 0)
        self.stored = scenes.record(b'\5' + bytes(1423))
        self.say('PSAVE 0 Harmony')
        payload = self.written[40:] if self.written else b''
        result, working, *_ = self.load(self.written) if self.written else (None, b'', None, None)
        pack = struct.pack('<7h', *first)
        self.row('a stored preset has it, and it is read as itself with its parameters', result == 0 and payload.count(pack) >= 1 and working.count(pack) >= 1, [result, len(payload)])
        self.run('effect_ownership_remove', 1, limit=2_000_000)
        self.row('taken away, with the others left', [self.field(k, 2, 'B') for k in range(3)] == [1, 0, 1], [self.field(k, 2, 'B') for k in range(3)])

    def report(self):
        for part in (self.listing, self.tables, self.settings, self.life, self.sound, self.preserved):
            try:
                part()
            except (Exception, SystemExit) as error:
                self.row(f'{part.__name__} goes to its end', False, f'{type(error).__name__}: {error}')
        return {'build': self.manifest['product'], 'area_sha256': self.manifest['area_sha256'], 'device_io': False, 'hardware_test': False,
                'checks': self.rows, 'held': all(r['held'] for r in self.rows) and len(self.rows) == CHECKS}


def main(argv=None):
    if len(argv or sys.argv[1:]) != 1:
        raise SystemExit(__doc__)
    build = (ROOT / (argv or sys.argv[1:])[0]).resolve()
    check = Check(build)
    report = check.report()
    print(json.dumps(report, indent=1))
    return 0 if report['held'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
