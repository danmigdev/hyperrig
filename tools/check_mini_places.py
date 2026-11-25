"""Run the two sections of the chain of a product build in the pi32v2 simulator, without a capture between them. Offline; no device is opened.

The firmware holds ten blocks before the AMP block (P) and ten after it (Q), sixteen in all. With the capture taken out (AMPX 0) the editor shows
one chain and uses both sections for it. That is right only when a block sounds the same in both. Here the application's own audio task runs
from the bytes of a built firmware, whole blocks of 128 samples from the input to the output, with the same blocks in P and in Q:

- effects   each effect by itself, mono: the same samples, and the same state of the effect and of its memory, so the same afterwards too;
- stereo    each effect by itself, in stereo, which only Q has: which ones are not the same;
- chains    chains divided at each place, and drives with oversampling side by side, which are worked as one within a section;
- parallel  paths with levels, a crossover and blocks of another latency; a knob that moves, a block off and on, the tempo, a scene;
- limits    what the firmware answers, and the last moment of a block that may be started in each section;
- tails     the sound of a delay and of a reverb that goes on after a preset change fades at the end;
- stored    sixteen blocks stored and read again, also while the sound of the preset before still rings.

With --before, another build: a preset of ten blocks must be stored with the same bytes by both. Nothing of this is a hardware or audio test.

Usage, from the repository root (some 20 minutes):
    python -B tools/check_mini_places.py BUILD [--before BUILD] [--only PART ...]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product."""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_panel as harness  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402

HEAP, RATE, BLOCK = 0x01D00000, 48077, 128
EFFECTS, CONTROL, STATE, SETTINGS, POOL = 'L01c2c220', 'L01c32db0', 'L01c26890', 'L01c1f180', 'L01c2fa38'
INPUT, LEFT, RIGHT, STEREO, DEADLINE = 'L01c234a8', 'L01c224a8', 'L01c22ca8', 'L01c1f7f0', 'L01c34444'
WAIT = 'L02040d34'                               # the audio task waits for samples
TEN = ['comp', 'boost', 'eq', 'ts9', 'phaser', 'klon', 'tremolo', 'delay', 'reverb2', 'flanger']
SIXTEEN = ['comp', 'boost', 'eq', 'ts9', 'phaser', 'tremolo', 'klon', 'flanger', 'rat', 'geq', 'muff', 'vibrato', 'basseq', 'chorus', 'envfilter', 'delay']
PARTS = ('effects', 'stereo', 'chains', 'parallel', 'limits', 'tails', 'stored')
DECODED = {}


class Done(Exception):
    pass


class Places(scenes.Pedal):
    """One build without a capture, its audio task run one block at a time; the memory of the effects is given from one heap."""

    def __init__(self, build, stereo=0):
        super().__init__(build)
        self.cpu.cache = DECODED.setdefault(build, self.cpu.cache)             # the code is the same in all of them
        self.heap, self.waits, self.refused = HEAP, 0, []
        harness.RECORDED.pop('the_allocator', None)
        self.at[scenes.block.ALLOCATOR] = self.allocate
        self.at[self.where[WAIT]] = self.wait
        self.setting(harness.G_PRESET, -1)
        self.say('AMPX 0')
        self.mem.write(self.where[STATE] + 280, struct.pack('<I', 2))          # the audio runs
        self.mem.write(self.where[STEREO], bytes([stereo]))
        self.mem.write(self.where[CONTROL] + 2, bytes([stereo]))               # it moves there a step a block; here it has arrived

    def allocate(self, a):
        at, self.heap = self.heap, self.heap + (a[0] + 63 & ~63)
        return at

    def wait(self, a):
        self.waits += 1
        if self.waits > 1:
            raise Done
        return 0

    def peek(self, at):
        return struct.unpack('<I', self.mem.read(at, 4))[0]

    def frame(self, samples):
        """One block of the audio task, from the input to the output: (left, right), right the same as left when the block is mono."""
        s = self.where[STATE]
        n, out = self.peek(s + 384), self.peek(s + 540) & 3
        self.mem.write(self.where[INPUT] + 512 * (n & 3), struct.pack(f'<{BLOCK}i', *samples))
        self.mem.write(s + 380, struct.pack('<I', n + 1))
        self.waits = 0
        try:
            self.run('audio_task_task', limit=20_000_000)
        except Done:
            pass
        left = struct.unpack(f'<{BLOCK}i', self.mem.read(self.where[LEFT] + 512 * out, 512))
        two = self.mem.read(s + 580 + out, 1)[0]
        return left, struct.unpack(f'<{BLOCK}i', self.mem.read(self.where[RIGHT] + 512 * out, 512)) if two else left

    def play(self, blocks, first=0):
        left, right = [], []
        for k in range(first, first + blocks):
            a, b = self.frame(signal(k))
            left += a
            right += b
        return left, right

    def remembered(self):
        """What the effects remember: their slots, the objects of the reverbs, their memory."""
        return (self.mem.read(self.where[EFFECTS], 16 * 480), self.mem.read(self.where[POOL], 4 * 888), self.mem.read(HEAP, self.heap - HEAP))

    def fxa(self, bank, name, place=99):
        answer = self.say(f'FXA {bank} {place} {name}')
        if answer and answer[0].startswith('FXA id='):
            return int(answer[0].split('=')[1].split()[0])
        self.refused.append([bank, name, answer])
        return None

    def blocks(self, p=(), q=()):
        return [self.fxa('P', n) for n in p] + [self.fxa('Q', n) for n in q]

    def chain(self):
        out = {'P': [], 'Q': []}
        for line in self.say('FXS'):
            w = line.split()
            if w[0] == 'FX' and w[1][0] in 'PQ':
                out[w[1][0]].append(w[3])
        return out

    def cab(self):
        data = b''.join(struct.pack('<h', int(20000 * math.exp(-i / 20) * math.cos(i))) for i in range(200))
        self.say('IRBEGIN 200 -1500 48')
        for k in range(0, len(data), 64):
            self.say(f'IRB {k} {data[k:k + 64].hex()}')
        return self.say(f'IREND {zlib.crc32(data):08x}')

    def names(self):
        self.panel.lines.clear()
        self.run('console_reports_effect_table')
        return [x.split()[2] for x in ''.join(self.panel.lines).split('\n') if x.startswith('FXT ') and x[4:5].isdigit()]

    def apply(self, record):
        """A preset change, from a stored record: the application's own reading, and its own rebuilding of the chain; how many blocks it could not make."""
        self.stored = record
        if self.run('preset_preflight_preflight', 0, scenes.HEADER):
            return None
        return self.run('preset_application_apply', 0, scenes.HEADER + 512, scenes.HEADER + 516, limit=60_000_000)

    def save(self):
        self.setting(harness.G_PRESET, -1)
        answer = self.say('PSAVE 0 Kept')
        return self.stored if answer and answer[0].startswith('PSAVE ok') else None


def signal(k):
    """A block of something like plucked strings, with a new attack every four blocks."""
    out = []
    for i in range(BLOCK):
        n = BLOCK * k + i
        v = sum(a * math.sin(2 * math.pi * f * n / RATE) for a, f in ((1.0, 196.0), (0.5, 392.7), (0.3, 1180.0), (0.1, 5200.0)))
        out.append(int(2 ** 20 * v * math.exp(-(n % (4 * BLOCK)) / 600)) + ((n * 7919 >> 3) % 2049 - 1024))
    return out


def together(build, stereo, p, q, blocks):
    """The sound and what is remembered of one chain: the blocks p before and q after."""
    x = Places(build, stereo)
    x.blocks(p, q)
    return x.play(blocks), x.remembered(), x


def each(build, stereo):
    """Every effect by itself, in P of one pedal and in Q of another: (name, the same samples, the same state, the same cost, two channels in P, in Q, its
    channels by the firmware's table)."""
    pair = [Places(build, stereo) for _ in 'PQ']
    for p in pair:
        p.cab()
    out, k = [], 0
    for name in pair[0].names():
        heap = pair[0].heap
        ids = [p.fxa(bank, name) for p, bank in zip(pair, 'PQ')]
        if None in ids or ids[0] != ids[1]:
            out.append((name, None, None, None, None, None, None))
            continue
        effect = pair[1].object(ids[1])
        kind = pair[1].run('dsp_stage_capability', effect, pair[1].run('dsp_stage_active', effect))
        x = [p.play(2, k) for p in pair]
        k += 2
        costs = [p.run('effect_setup_total_cost') for p in pair]
        for p, i in zip(pair, ids):          # the first word of the memory of HyperRig's own effects counts the blocks of sound, by which they see a pause: in Q it is one more
            if p.mem.read(p.object(i), 1)[0] >= 40:
                p.mem.write(int.from_bytes(p.mem.read(p.object(i) + 84, 4), 'little'), bytes(4))
        # mono: all that is remembered, also of the effects before; in stereo those before that made two channels left something else, so this one's own
        own = [p.remembered() if not stereo else (p.mem.read(p.object(i), 480), p.mem.read(heap, p.heap - heap)) for p, i in zip(pair, ids)]
        out.append((name, x[0] == x[1], own[0] == own[1], costs[0] == costs[1], x[0][0] != x[0][1], x[1][0] != x[1][1], kind))
        for p, i in zip(pair, ids):
            p.say(f'FXR {i}')
    return out, [p.refused for p in pair]


def effects(build, row):
    all_of_them, refused = each(build, 0)
    wrong = [x for x in all_of_them if x[1:4] != (True, True, True) or x[4] or x[5]]
    row('every effect, mono, before and after the AMP block that is not there: the same samples, state and cost', len(all_of_them) == 42 and not wrong,
        {'effects': len(all_of_them), 'wrong': wrong, 'refused': refused})


def stereo(build, row):
    all_of_them, refused = each(build, 100)
    makes = {x[0] for x in all_of_them if x[6] == 1}
    row('in stereo a block before the AMP block is mono', not any(x[4] for x in all_of_them) and not refused[0] and not refused[1], [x[0] for x in all_of_them if x[4]])
    differ = {x[0] for x in all_of_them if not (x[1] and x[2])}
    row('no effect is different but those that make two channels by the firmware\'s own table', len(all_of_them) == 42 and differ <= makes and any(x[5] for x in all_of_them),
        {'make two channels': sorted(makes), 'differ in two blocks': sorted(differ), 'two channels in Q': sorted(x[0] for x in all_of_them if x[5])})
    a, b = together(build, 100, ['chorus'], ['comp'], 4), together(build, 100, [], ['chorus', 'comp'], 4)
    row('one that makes two channels with a mono one after it: the same in both, in stereo too', a[:2] == b[:2])
    a, b = together(build, 100, ['comp', 'ts9', 'eq'], ['delay', 'chorus'], 4), together(build, 100, [], ['comp', 'ts9', 'eq', 'delay', 'chorus'], 4)
    row('mono ones in P and those that make two channels in Q: the same as all in Q, in stereo', a[:2] == b[:2] and a[0][0] != a[0][1])


def chains(build, row):
    heard, state, whole = together(build, 0, [], TEN, 4)
    wrong = [k for k in (1, 2, 5, 8, 10) if together(build, 0, TEN[:k], TEN[k:], 4)[:2] != (heard, state)]
    row('a chain of ten, divided anywhere: the same samples and the same state', not wrong and not whole.refused, [wrong, whole.refused])
    p = Places(build)
    p.mem.write(p.where[SETTINGS] + 2, b'\0')                                    # the amp that is not there was switched off before
    p.blocks(TEN[:4], TEN[4:])
    row('whether the amp that is not there was on or off', p.play(4) == heard)
    first, wrong = None, []
    for k in (6, 8, 10):
        *now, p = together(build, 0, SIXTEEN[:k], SIXTEEN[k:], 3)
        if p.chain() != {'P': SIXTEEN[:k], 'Q': SIXTEEN[k:]} or p.refused or first not in (None, now):
            wrong.append([k, p.chain(), p.refused])
        first = first or now
    row('sixteen blocks, with 6, 8 and 10 of them before: in their order, the same samples and the same state', not wrong, wrong)
    parted = [together(build, 0, p, q, 4) for p, q in ((['ts9', 'ds1'], []), ([], ['ts9', 'ds1']), (['ts9'], ['ds1']))]
    costs = [x[2].run('effect_setup_total_cost') for x in parted]
    heard = [x[0][0] for x in parted]
    late, rest = min(((k, sum((heard[1][i] - heard[2][i + k]) ** 2 for i in range(64, len(heard[1]) - 64))) for k in range(-40, 41)), key=lambda x: x[1])
    off = 10 * math.log10(max(1, rest) / sum(v * v for v in heard[1][64:-64]))
    row('two drives with oversampling side by side: the same in both sections', heard[0] == heard[1] and costs[0] == costs[1], costs)
    row('divided they are worked one by one: another sound, and more of the processor', heard[2] != heard[1] and costs[2] > costs[1], {'costs': costs, 'later by samples': late, 'difference_db': round(off, 1)})
    parted = [together(build, 0, p, q, 4)[:2] for p, q in (([], ['ts9', 'boost', 'ds1']), (['ts9'], ['boost', 'ds1']), (['ts9', 'boost'], ['ds1']))]
    row('with another block between them they may be divided', parted[0] == parted[1] == parted[2])


def parallel(build, row):
    pair = [Places(build) for _ in 'PQ']
    for p, bank in zip(pair, 'PQ'):
        ids = [p.fxa(bank, n) for n in ('comp', 'ts9', 'phaser', 'eq', 'boost')]
        for k, lane in ((1, 1), (2, 1), (3, 2)):
            p.say(f'FXL {ids[k]} {lane}')
        p.said = [p.say(f'FXMIX {bank} 0 -3 2'), p.say(f'FXXO {bank} 0 200 1')]
    x = [(p.play(5), p.remembered()) for p in pair]
    serial = together(build, 0, ['comp', 'ts9', 'phaser', 'eq', 'boost'], [], 5)[0]
    row('paths with levels, a crossover and blocks of another latency: the same samples and state', x[0] == x[1] and x[0][0] != serial and [p.said for p in pair] ==
        [[[f'FXMIX {b} 0 -3 2'], [f'FXXO {b} 0 200 1']] for b in 'PQ'], [p.said for p in pair])
    for p, bank in zip(pair, 'PQ'):
        p.chained = [line for line in p.say('FXS') if line.startswith('FX ') or line.startswith(('FXMIX', 'FXXO'))]
    row('and the same in the list of the chain', [line.replace('Q', 'P') for line in pair[1].chained] == pair[0].chained and len(pair[0].chained) == 7, pair[0].chained)
    pair = [Places(build) for _ in 'PQ']
    for p, bank in zip(pair, 'PQ'):
        ids = [p.fxa(bank, n) for n in ('boost', 'delay', 'eq')]
        out = [p.play(1)]
        p.say(f'FXP {ids[0]} 0 -6')
        out.append(p.play(2, 1))
        p.say(f'FXE {ids[1]} 0')
        out.append(p.play(2, 3))
        p.say(f'FXE {ids[1]} 1')
        p.say('BPM 900')
        out.append(p.play(2, 5))
        p.say('SNAPSAVE 0')
        p.say(f'FXP {ids[2]} 0 9')
        p.say('SNAPSAVE 1')
        out.append(p.play(1, 7))
        p.say('SNAP 0')
        out.append(p.play(2, 8))
        p.heard = out, p.remembered()
    row('a knob that moves, a block off and on, the tempo, a scene: the same samples and state', pair[0].heard == pair[1].heard and not pair[0].refused)
    a, b = together(build, 0, ['boost'], ['sgate'], 3), together(build, 0, [], ['boost', 'sgate'], 3)
    row('the gate that listens to the input does so in both', a[:2] == b[:2] and together(build, 0, ['boost', 'sgate'], [], 3)[:2] == a[:2])


def limits(build, row):
    p = Places(build)
    p.blocks(['boost'] * 10)
    said = [p.say('FXA P 99 boost')]
    p.blocks((), ['boost'] * 6)
    said += [p.say(x) for x in ('FXA Q 99 boost', 'FXA P 99 boost', 'FXM 10 P 0', 'FXM 0 P 9', 'FXM 1 Q 0', 'FXM 10 P 0', 'FXM 99 P 0', 'FXA X 99 boost')]
    order = [len(v) for v in p.chain().values()]
    row('ten in a section and sixteen in all', said[:7] == [['ERR FXA bank full']] * 3 + [['ERR FXM bank full'], ['FXM ok'], ['FXM ok'], ['FXM ok']] and order == [10, 6] and
        said[7] == ['ERR FXM bad argument'], [said, order])
    p = Places(build)
    p.blocks((), ['boost'] * 9)
    said = [p.say(f'FXL {i} {1 + (i % 4 == 2)}')[0] for i in (0, 2, 4, 6, 8)]
    full = 'too many parallel groups (max 3 per bank)'
    row('three parallel paths in a section', said == ['FXL ok 0 1', 'FXL ok 2 2', 'FXL ok 4 1', 'ERR FXL ' + full, 'ERR FXL ' + full], said)
    said = [p.say(x)[0] for x in ('FXM 0 P 0', 'FXL 6 1', 'FXM 0 Q 0')]
    row('and what is moved counts', said == ['FXM ok', 'FXL ok 6 1', 'ERR FXM ' + full] and [len(v) for v in p.chain().values()] == [1, 8], said)
    # the last moment of a block: what the stage is given when it starts with each section
    p = Places(build)
    p.blocks(['boost'], ['boost'])
    moments, stage, decode = [], p.where['dsp_stage_stage'], p.cpu.decode

    def watch(pc):
        if pc == stage == p.cpu.pc:
            moments.append((p.cpu.R[0], p.peek(p.where[DEADLINE])))
        return decode(pc)
    p.cpu.decode = watch
    p.frame(signal(0))
    p.cpu.decode = decode
    late, base = dict(moments), p.peek(p.where[SETTINGS] + 52)
    row('a block in P may be started until some time earlier than one in Q: what the rest of the audio takes, and the room of the effects is without it', sorted(late) == [0, 1] and
        late[1] - late[0] == base > 0, {'the rest': base, 'until': late})


def tails(build, row):
    """What goes on after a preset change fades at the end: the sound that a count of the blocks left gives, against the same with many left. The level of a
    delay is what it was afterwards; what is on does not fade; a delay and a reverb that end have no edge of their own."""
    LOW, HIGH, FADE = 0x1C00000, 0x1C80000, 500

    def ringing(name):
        p = Places(build)
        p.say('SPILL 1')
        p.blocks((), [name])
        if name == 'delay':
            for k, v in ((0, 40), (1, 80), (2, 80)):
                p.say(f'FXP 0 {k} {v}')
        for k in range(30):
            p.frame(signal(k))
        other = Places(build)
        other.blocks((), ['boost'])
        p.apply(other.save())
        return p, p.object(p.mem.read(p.where[CONTROL] + 88, 1)[0]), p.mem.read(p.where[CONTROL] + 8, 1)[0]

    def rms(x):
        return math.sqrt(sum(v * v for v in x) / len(x))

    def played(p, obj, saved, left, n=6):
        p.mem.write(LOW, saved[0])
        p.mem.write(HEAP, saved[1])
        p.mem.write(obj + 8, struct.pack('<H', left))
        out = [p.frame([0] * BLOCK)[0] for _ in range(n)]
        return out, struct.unpack('<I', p.mem.read(obj + 300, 4))[0]

    for name, expect, first in (('delay', lambda left: left / FADE, 0), ('reverb2', lambda left: (left - 1) / 512, 1)):
        p, obj, n = ringing(name)
        saved = (p.mem.read(LOW, HIGH - LOW), p.mem.read(HEAP, p.heap - HEAP))
        wet = struct.unpack('<I', p.mem.read(obj + 300, 4))[0]
        full, _ = played(p, obj, saved, 600)
        half, after = played(p, obj, saved, 300)
        more, _ = played(p, obj, saved, 1500)
        wrong = [[i, round(rms(half[i]) / max(1, rms(full[i])), 3), round(expect(300 - i), 3)] for i in range(first, 6) if abs(rms(half[i]) / max(1, rms(full[i])) - expect(300 - i)) > 0.03]
        row(f'the sound of a {name} that goes on fades with the blocks that are left', n == 1 and not wrong and [list(x) for x in full] == [list(x) for x in more], [n, wrong])
        if name == 'delay':
            row('the level of a delay is what it was afterwards', after == wet, [wet, after])
    p = Places(build)
    p.blocks((), ['delay'])
    p.say('FXP 0 0 40')
    for k in range(8):
        p.frame(signal(k))
    obj, saved = p.object(0), None
    saved = (p.mem.read(LOW, HIGH - LOW), p.mem.read(HEAP, p.heap - HEAP))
    on = [played(p, obj, saved, left, 3)[0] for left in (0, 5, 300)]
    row('a delay that is on does not fade, whatever the count says', all(list(a) == list(b) for x in on[1:] for a, b in zip(on[0], x)))


def stored(build, row, before=None):
    p = Places(build)
    p.blocks(SIXTEEN[:6], SIXTEEN[6:])
    for k in range(5):
        p.say(f'FXP 0 0 {k}')
        p.say(f'SNAPSAVE {k}')
    record, want = p.save(), {'P': SIXTEEN[:6], 'Q': SIXTEEN[6:]}
    q = Places(build)
    q.blocks((), TEN)
    missed = q.apply(record) if record else None
    row('sixteen blocks with five scenes: stored, and read again over another chain', missed == 0 and q.chain() == want, [missed, q.chain()])
    for rings in (0, 1):
        q = Places(build)
        q.say(f'SPILL {rings}')
        q.blocks((), ['reverb2', 'delay', 'reverb2', 'delay'])
        q.play(1)
        missed = q.apply(record) if record else None
        row('sixteen blocks over a preset ' + ('whose sound still rings' if rings else 'that is cut off'), missed == 0 and q.chain() == want, [missed, q.chain()])
    thirteen, six = Places(build), Places(build)
    thirteen.blocks(SIXTEEN[:3], SIXTEEN[3:13])
    six.blocks((), TEN[:6])
    ringing = lambda x: x.mem.read(x.where[CONTROL] + 8, 1)[0]
    for n, other, rings in ((13, thirteen, ['reverb2', 'delay', 'reverb2']), (6, six, ['reverb2', 'delay'])):
        record = other.save()
        q = Places(build)
        q.say('SPILL 1')
        q.blocks((), rings)
        q.play(1)
        q.apply(record)
        if n == 6:
            row('what rings goes on when there are places for it', ringing(q) == 2 and q.chain()['Q'] == TEN[:6], [ringing(q), q.chain()])
            continue
        were = ringing(q)
        ids = [q.fxa('P', x) for x in ('boost', 'eq', 'geq')]
        row('a block is added while others ring, up to the sixteenth and no further', were == 3 and None not in ids and [len(v) for v in q.chain().values()] == [6, 10] and ringing(q) == 0 and
            q.say('FXA P 99 boost') == ['ERR FXA bank full'], [were, ids, ringing(q), q.refused])
    if before:
        records = []
        for b in (build, before):
            p = Places(b)
            p.blocks((), TEN)
            for k in range(4):
                p.say(f'FXP 0 0 {k}')
                p.say(f'SNAPSAVE {k}')
            records.append(p.save())
        row('a preset of ten blocks is stored with the same bytes as before', records[0] and records[0] == records[1], [len(x) if x else None for x in records])


def check(build, before=None, only=PARTS):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})
        print(('ok    ' if good else 'FAIL  ') + name, file=sys.stderr, flush=True)
    for part in only:
        globals()[part](build, row, *([before] if part == 'stored' else []))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--only', nargs='+', choices=PARTS, default=PARTS)
    a = parser.parse_args(argv)
    rows = check(a.build.as_posix(), a.before and a.before.as_posix(), a.only)
    manifest = json.loads((ROOT / a.build / 'build-manifest.json').read_bytes())
    held = all(r['held'] for r in rows)
    print(json.dumps({'build': manifest['product'], 'area_sha256': manifest['area_sha256'], 'device_io': False, 'hardware_test': False, 'parts': list(a.only), 'checks': rows, 'held': held}, indent=1))
    return 0 if held else 1


if __name__ == '__main__':
    raise SystemExit(main())
