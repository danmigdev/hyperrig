"""Run the effects that HyperRig adds from the id 40 on in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of a built firmware: the list of the effects as the console sends it, names and numbers,
and the life of each effect: made without memory (refused) and with it, its defaults, every parameter to both ends the slow way and the
fast way that a knob takes, off and on, moved, taken away. Its sound is compared, sample for sample, with tools/effects_reference.py: a note with
every parameter at its ends while it plays, silence, the loudest there is, parts of a block, a pause, a call without memory. While it
plays, no instruction and no number may come from the flash. The instructions of a block are counted, against the ticks that the
firmware counts. A preset with all the effects and two scenes is stored, read and applied again. With --before, a build without these
effects: it must list the others as this one does, and leave out of the same preset what it does not know.
Nothing of this is a hardware or audio test: it says nothing of how it sounds, or of the time the pedal needs.

Usage, from the repository root:
    python -B tools/check_mini_effects.py BUILD [--before BUILD]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), *[str(ROOT / 'upstream/pi32v2-isa' / d) for d in ('tools/llvm', 'tools/hwtest', '')]]
import check_mini_effect_block as block  # noqa: E402
import check_mini_panel as harness  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402
import effects_reference as reference  # noqa: E402

FIRST, PARAMETERS, MEMORY, STATE, SAMPLES, HEAP = 40, 70, 84, 288, block.SAMPLES, block.HEAP
CLOCK = ('L01c1f7f0', 20)
NAMES = list(reference.EFFECTS)
COSTS = {'octaver': 8000, 'swell': 4000, 'reverse': 6500}
GROUPS = {'octaver': 'drive', 'swell': 'dynamics', 'reverse': 'delay'}
LIGHTS = {'octaver': 3, 'swell': 8, 'reverse': 5}
FULL, LOUDEST = 8388607, reference.LIMIT
sim, codec = harness.sim, harness.codec


class Pedal(scenes.Pedal):
    """A pedal on no preset, with a note of where the sound code and its numbers come from."""

    def __init__(self, build):
        super().__init__(build)
        self.setting(harness.G_PRESET, -1)
        self.setting(88, -1)
        self.wipe()
        self.heap = HEAP
        self.mem.write(CLOCK_AT(self), struct.pack('<I', 1000))

    def of(self, slot, offset, form):
        return struct.unpack('<' + form, self.mem.read(self.object(slot) + offset, struct.calcsize(form)))[0]

    def memory(self, size):
        """The next allocation is given here, filled with something."""
        self.mem.write(self.heap, b'\x5a' * size)

    def play(self, slot, samples, parts=(128,), clock=True):
        """Blocks of 128 samples, each in these parts; the samples that come out, and the instructions of each block."""
        out, steps = [], []
        for k in range(0, len(samples), 128):
            if clock:
                at = CLOCK_AT(self)
                self.mem.write(at, struct.pack('<I', self.word(at) + 1))
            i, before = k, self.cpu.steps
            for n in parts:
                self.mem.write(SAMPLES, struct.pack(f'<{n}i', *samples[i:i + n]))
                self.run('effect_processing_dispatch', self.object(slot), SAMPLES, n)
                out += struct.unpack(f'<{n}i', self.mem.read(SAMPLES, 4 * n))
                i += n
            steps.append(self.cpu.steps - before)
        return out, steps

    def turn(self, slot, index, value):
        self.run('effect_parameter_lifecycle_parameter_commit', slot, index, value & 0xFFFFFFFF)


def CLOCK_AT(p):
    return p.where[CLOCK[0]] + CLOCK[1]


def note(n, hertz=110.0, size=0.3, seed=1):
    r = random.Random(seed)
    return [int(FULL * size * math.exp(-i / 30000) * (math.sin(2 * math.pi * hertz * i / 48077) + 0.4 * math.sin(2 * math.pi * 3.01 * hertz * i / 48077)) / 1.4) + r.randint(-900, 900)
            for i in range(n)]


def check(build, before=None):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    p = Pedal(build)
    end = p.word(p.where['hyperrig_effect_end'])
    row('as many ids as effects', end == FIRST + len(NAMES), end)
    lines = p.say('FXT')
    at = {x.split()[2]: k for k, x in enumerate(lines) if re.match(r'FXT [0-9]+ ', x)}
    for k, name in enumerate(NAMES):
        need = 2 * p.run('hyperrig_effect_memory', FIRST + k)
        want = [f'FXT {FIRST + k} {name} cost={COSTS[name]} cat={GROUPS[name]} mem={need + 16}'] + [f'FXT  {j} {n} {a}..{b} ({d})' for j, (a, b, d, n) in enumerate(reference.EFFECTS[name].ROWS)]
        seen = lines[at[name]:at[name] + len(want)] if name in at else []
        row(f'{name}: how the console lists it', seen == want and (lines[at[name] + len(want)] + ' ').startswith(('FXT end', f'FXT {FIRST + k + 1} ')), seen)
    row('the list ends with them, and has 42', len(at) == 39 + len(NAMES) and lines[-1] == 'FXT end' and [x.split()[1] for x in lines if re.match(r'FXT [0-9]+ ', x)][-len(NAMES) - 1:] ==
        ['39'] + [str(FIRST + k) for k in range(len(NAMES))], len(at))
    numbers = []
    for word in (*NAMES, *(str(FIRST + k) for k in range(len(NAMES) + 1)), 'rotary', '39', '1', '0', '255', 'nothing'):
        p.mem.write(0x01C76400, word.encode() + b'\0')
        numbers.append(p.run('dispatch_helpers_effect_number', 0x01C76400))
    row('names and numbers', numbers == [40, 41, 42, 40, 41, 42, 0, 39, 39, 1, 0, 0, 0], numbers)
    beyond = [p.text(p.run('console_reports_type_name', k)) for k in (0, 43, 255)] + [p.text(p.run('slot_queries_type_name', 43))] + \
             [p.run(f, 43, 0) for f in ('preset_application_metadata', 'slot_queries_type_cost', 'slot_queries_type_demand', 'effect_setup_demand_by_type')] + \
             [p.run('preset_application_metadata', FIRST, 7), p.run('preset_application_metadata', FIRST + 1, 4), p.add(43), p.add(255)]
    row('ids that nothing has', beyond == ['?', '?', '?', 'other', 0, 0, 0, 0, 0, 0, -1, -1], beyond)
    kept = []
    for function, first_kept in (('console_reports_type_name', 2), ('preset_application_metadata', 3), ('slot_queries_type_name', 3)):
        for k in (*range(FIRST, end + 1), 255):
            p.run(function, k, 0, 0x1234, 0x5678)
            kept.append(p.cpu.R[first_kept:4] == [0x1234, 0x5678][first_kept - 2:])
    row('the small functions that the application counts on keep the registers they kept', all(kept), kept.count(False))
    row('their lights on a footswitch', [p.run('hyperrig_effect_like', FIRST + k) for k in range(len(NAMES))] == [LIGHTS[n] for n in NAMES] and p.run('hyperrig_effect_like', end) == 0, None)
    row('room for them by the size of the memory that is free', [p.run('slot_queries_type_fits', FIRST + 2, HEAP_SIZES(p, n), 1) for n in (30000, 40000)] == [0, 1], None)
    # what runs for every block is in the RAM
    first, last = 0x01C00000, p.where['ultrarig_ram_code_end']
    table = [p.where[f'hyperrig_fx_{n}'] for n in NAMES]
    code = [p.word(e + 104) for e in table]
    row('the descriptions are in the RAM, and what runs an effect', all(first <= e < 0x01C80000 for e in table) and all(first <= a < last for a in code), [hex(a) for a in code])
    for k, name in enumerate(NAMES):
        life(build, FIRST + k, name, row)
    stored(build, before, row)
    if before:
        old = Pedal(before)
        seen = old.say('FXT')
        mine = [x for x in lines if not re.match(r'FXT ', x)]
        kept, skip = [], False
        for x in lines:
            m = re.match(r'FXT ([0-9]+) ', x)
            skip = int(m.group(1)) >= FIRST if m else skip and x != 'FXT end'
            if not skip:
                kept.append(x)
        row('the build before lists the same but these', seen == kept and not mine, [len(seen), len(kept)])
    return rows


def HEAP_SIZES(p, n):
    p.mem.write(0x01C76800, struct.pack('<I', n))
    return 0x01C76800


class Watch:
    """Notes every instruction, and every number that the frame reads, that comes from the flash."""

    def __init__(self, p):
        self.p, self.seen, self.at = p, set(), 0

    def __enter__(self):
        cpu, (first, last) = self.p.cpu, (self.p.where['hyperrig_effect_process'], self.p.where['ultrarig_ram_code_end'])
        self.kept = kept_read, kept_step = cpu.mem.read, cpu.step

        def step():
            self.at = cpu.pc
            if 0x02000000 <= cpu.pc < 0x03000000:
                self.seen.add(('instruction', hex(cpu.pc)))
            return kept_step()

        def read(address, n):
            if 0x02000000 <= address < 0x03000000 and first <= self.at < last:
                self.seen.add((hex(self.at), hex(address)))
            return kept_read(address, n)

        cpu.mem.read, cpu.step = read, step
        return self

    def __exit__(self, *_):
        self.p.cpu.mem.read, self.p.cpu.step = self.kept


def life(build, ident, name, row):
    p = Pedal(build)
    rows_ = reference.EFFECTS[name].ROWS
    need = 2 * p.run('hyperrig_effect_memory', ident)
    p.allocator(False)
    row(f'{name}: without memory it is not made', p.add(ident) == -3)
    p.allocator(True)
    p.memory(need + 16)
    p.panel.calls.clear()
    comp, slot, boost = p.add(8), p.add(ident), p.add(2)
    asked = [c[1] for c in p.panel.calls if c[0] == 'the_allocator']
    row(f'{name}: made as itself between two others, its memory asked for once, given and cleared', (comp, slot, boost) == (0, 1, 2) and p.of(1, 0, 'B') == ident and p.of(1, 1, 'B') == 1 and
        asked == [need + 16] and p.of(1, MEMORY, 'I') == HEAP and p.mem.read(HEAP, need) == bytes(need), [comp, slot, boost, asked, need])
    if slot != 1:
        return
    defaults = [r[2] for r in rows_] + [0] * (7 - len(rows_))
    own = reference.Block(name)
    state = lambda: [p.of(1, STATE + 4 * k, 'i') for k in range(reference.SETTINGS)]
    row(f'{name}: it starts at its defaults', [p.of(1, PARAMETERS + 2 * k, 'h') for k in range(7)] == defaults and state() == own.goal, state())
    wrong = []
    for k, (low, high, default, parameter) in enumerate(rows_):
        for value, kept in ((high + 30, high), (low - 30, low)):
            p.turn(1, k, value)
            own.set(**{parameter: kept})
            if p.of(1, PARAMETERS + 2 * k, 'h') != kept or state() != own.goal:
                wrong.append([parameter, value, p.of(1, PARAMETERS + 2 * k, 'h')])
        p.turn(1, k, default)
        own.set(**{parameter: default})
    row(f'{name}: every parameter, kept within its ends, the slow way', not wrong and state() == own.goal, wrong)
    row(f'{name}: no parameter after its last', all(p.run('effect_parameter_lifecycle_parameter_commit', 1, k, 5) != 0 for k in range(len(rows_), 7)), None)
    # the fast way, up to the audio
    last = len(rows_) - 1
    answer = p.run('effect_parameter_lifecycle_parameter_fast_wrapper', 1, last, -6 & 0xFFFFFFFF, 10)
    for _ in range(12):
        end = p.where['L01c10fd2']
        for _ in range(2):
            end += p.cpu.decode(end)[2]
        p.run_with('L01c10e58', [0] * 12 + [p.where['L01c2e5a0']], 200_000, stop=end)
    own.set(**{rows_[last][3]: -6})
    row(f'{name}: a parameter, the fast way, up to the audio', answer == 0 and state() == own.goal and p.mem.read(p.where['L01c2e5a0'], 1) == b'\0', state())
    p.turn(1, last, rows_[last][2])
    own.set(**{rows_[last][3]: rows_[last][2]})
    # live mode: no footswitch takes it
    kept = harness.RECORDED.pop('preset_application_effect_type', None)
    p.run('panel_inputs_switch_targets')
    if kept is not None:
        harness.RECORDED['preset_application_effect_type'] = kept
    taken = p.mem.read(p.where[harness.STATE] + 1590, 7)
    row(f'{name}: no footswitch takes it in live mode', slot not in taken, taken.hex())
    # the sound: a note, every parameter at its ends while it plays, as the reference does
    most, wrong = 0, []
    x = note(128 * 8)
    with Watch(p) as watch:
        out, steps = p.play(1, x)
    row(f'{name}: while it plays nothing comes from the flash', not watch.seen, sorted(watch.seen)[:6])
    if out != own.run(x):
        wrong.append('defaults')
    most = max(most, *steps)
    seed = 2
    for k, (low, high, default, parameter) in enumerate(rows_):
        for value in (low, high, default):
            p.turn(1, k, value)
            own.set(**{parameter: value})
            x = note(128 * 6, 82.4 * 1.1 ** seed, 0.4, seed)
            seed += 1
            out, steps = p.play(1, x)
            most = max(most, *steps)
            if out != own.run(x):
                wrong.append([parameter, value])
    row(f'{name}: its samples are the reference\'s, with every parameter at its ends while it plays', not wrong, wrong)
    # all low, all high
    wrong = []
    for which in (0, 1):
        for k, r in enumerate(rows_):
            p.turn(1, k, r[which])
            own.set(**{r[3]: r[which]})
        for size, square in ((FULL, True), (LOUDEST, True), (2 ** 31 - 1, True), (FULL, False)):
            x = [size if (i // 109) % 2 else -size for i in range(128 * 5)] if square else [int(size * math.sin(i * i * 2e-5)) for i in range(128 * 5)]
            out, steps = p.play(1, x)
            most = max(most, *steps)
            if out != own.run(x) or max(abs(v) for v in out) > LOUDEST:
                wrong.append([which, size, max(abs(v) for v in out)])
    row(f'{name}: the loudest there is, with all parameters at one end and at the other: the reference\'s, and within 2 ^ 27', not wrong, wrong)
    for k, r in enumerate(rows_):
        p.turn(1, k, r[2])
        own.set(**{r[3]: r[2]})
    # parts of a block
    wrong = []
    for parts in ((32,) * 4, (1, 7, 33, 64, 23), (127, 1)):
        x = note(128 * 3, 147.0, 0.5, seed)
        seed += 1
        out, _ = p.play(1, x, parts)
        want, i = [], 0
        while i < len(x):
            for n in parts:
                want += own.run(x[i:i + n])
                i += n
        if out != want:
            wrong.append(parts)
    row(f'{name}: parts of a block', not wrong, wrong)
    # a pause: as if it were new, and silence stays silence
    p.mem.write(CLOCK_AT(p), struct.pack('<I', p.word(CLOCK_AT(p)) + 500))
    own.pause()
    x = [0] * 384
    out, _ = p.play(1, x)
    row(f'{name}: after a pause silence stays silence, also after something loud', out == own.run(x) and not any(out), max(abs(v) for v in out))
    x = note(128 * 4, 98.0, 0.5, seed)
    out, _ = p.play(1, x)
    row(f'{name}: and it goes on as the reference does', out == own.run(x))
    p.mem.write(p.object(1) + MEMORY, bytes(4))
    out, _ = p.play(1, list(range(-64, 64)))
    row(f'{name}: without memory, as when it is off and memory is short, the sound goes by', out == list(range(-64, 64)))
    p.mem.write(p.object(1) + MEMORY, struct.pack('<I', HEAP))
    counted, cost = round(most * block.CYCLES / block.TICK), p.run('effect_processing_cost', p.object(1))
    row(f'{name}: the ticks the firmware counts are what the code takes, with some to spare', counted <= cost == COSTS[name] == p.run('slot_queries_type_cost', ident),
        {'counted_by_the_firmware': cost, 'steps_of_a_block': most, 'ticks_of_the_steps': counted})
    p.run('effect_enable_commit', 1, 0)
    off = p.of(1, 1, 'B')
    p.run('effect_enable_commit', 1, 1)
    row(f'{name}: off and on', (off, p.of(1, 1, 'B')) == (0, 1), [off, p.of(1, 1, 'B')])
    p.run('effect_ownership_remove', 1)
    row(f'{name}: taken away, with the others left', [p.of(k, 2, 'B') for k in range(3)] == [1, 0, 1], [p.of(k, 2, 'B') for k in range(3)])


def stored(build, before, row):
    """A preset with all of them and two scenes, by the console: stored, read, applied, its scenes; and in the build before."""
    p = Pedal(build)
    ids = [p.say(f'FXA Q 99 {n}')[0] for n in ('boost', *NAMES)]
    row('added by the console', ids == ['FXA id=0 boost'] + [f'FXA id={k + 1} {n}' for k, n in enumerate(NAMES)], ids)
    if not ids[-1].startswith('FXA id='):
        return
    values, wanted = {}, {}
    for scene in (0, 1):
        for k, n in enumerate(NAMES):
            for j, (low, high, _, _) in enumerate(reference.EFFECTS[n].ROWS):
                v = low + (high - low) * (scene + j + k + 1) // 10
                p.say(f'FXP {k + 1} {j} {v}')
                values[k + 1, j] = v
            p.say(f'FXE {k + 1} {(scene + k) & 1}')
        wanted[scene] = p.say('FXS')[:len(NAMES) + 1]
        p.say(f'SNAPSAVE {scene}')
    moved = p.say('SNAP 0') + p.say('FXS')[:len(NAMES) + 1]
    row('a scene brings back their parameters and whether they are on', moved == ['SNAP ok 0 missing=0 ms=0'] + wanted[0], moved)
    p.setting(harness.G_PRESET, 0)
    p.stored = scenes.record(b'\5' + bytes(1423))
    answer, record = p.say('PSAVE 0 Own effects'), p.written
    types = list(record[40 + 13:40 + 13 + 18 * (len(NAMES) + 1):18]) if record else None
    row('stored in the form of version 5, with their ids', bool(record) and record[40] == 5 and types == [2] + [FIRST + k for k in range(len(NAMES))], [answer, types])
    if not record:
        return

    def back(b):
        q = Pedal(b)
        q.stored = record
        result = [q.run('preset_preflight_preflight', 0, scenes.HEADER), q.run('preset_application_apply', 0, scenes.HEADER + 64, scenes.HEADER + 68, limit=30_000_000)]
        return q, result

    q, result = back(build)
    chain = lambda x: [y for y in x.say('FXS') if y.startswith('FX ')]
    seen = [chain(q)]
    for scene in (0, 1):
        q.say(f'SNAP {scene}')
        seen.append(chain(q))
    row('read and applied: as it was stored, with its scenes', result == [0, 0] and seen == [wanted[0], wanted[0], wanted[1]] and q.say('SNAPS') == ['SNAPS 11000000 current=1'], [result, seen])
    if before:
        o, result = back(before)
        names = [x.split()[3] for x in chain(o)]
        after = o.say('SNAP 1')
        row('the build before leaves out what it does not know and keeps the rest and the scenes', result == [0, len(NAMES)] and names == ['boost'] and after[0].startswith('SNAP ok 1') and
            o.say('SNAPS') == ['SNAPS 11000000 current=1'], [result, names, after])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--before', type=Path)
    args = parser.parse_args(argv)
    rows = check(args.build, args.before)
    manifest = json.loads((ROOT / args.build / 'build-manifest.json').read_bytes())
    report = {'build': manifest['product'], 'area_sha256': manifest['area_sha256'], 'device_io': False, 'hardware_test': False, 'checks': rows, 'held': all(r['held'] for r in rows)}
    print(json.dumps(report, indent=1))
    return 0 if report['held'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
