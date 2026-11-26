"""The low cut and the high cut of the cab block of a built product firmware, in the pi32v2 simulator. Offline; no device is opened.

The audio task runs whole blocks of 128 samples from the bytes of the firmware, with a cab in the chain, and the control scan's own turn moves the
filters. Looked at: the two knobs in the list of effects; that both off change nothing, against a build from before; the level at many frequencies
against the filters they are meant to be; that the sound has no step and no pause while a knob is turned, switched on or off, and by a scene; that a
preset has them at once; two cabs, stereo, blocks that are no cabs; the instructions they take; that nothing else uses their part of the block's
object; and a cab of its own that is made where there is no room for two. Nothing of this is a hardware or audio test.

Usage, from the repository root:
    python -B tools/check_mini_cab.py BUILD [--before BUILD]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product; --before: one from before the cuts."""
from __future__ import annotations

import argparse
import bisect
import cmath
import json
import math
import random
import re
import struct
import sys
import zlib
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_library as library  # noqa: E402
import check_mini_places as places  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402

RATE, SIZE = places.RATE, places.BLOCK
LOW, HIGH, TOP, LENGTH, SLOT = 4, 5, 20000, 3, 2
PARAMETERS, CUTS, CUT, FADE = 70, 304, 72, 8
FULL = 1 << 21                                     # a fourth of full level


class Cabs(places.Places):
    def __init__(self, build, stereo=0, response=None, cabs=1):
        super().__init__(build, stereo)
        self.pauses = []
        for name in ('audio_pause_pause_audio', 'audio_pause_resume_audio'):
            self.at[self.where[name]] = lambda a, name=name: self.pauses.append(name) or 0
        if response is not None:
            data = struct.pack(f'<{len(response)}h', *response)
            self.say(f'IRBEGIN {len(response)} 0 48')
            for k in range(0, len(data), 64):
                self.say(f'IRB {k} {data[k:k + 64].hex()}')
            self.say(f'IREND {zlib.crc32(data):08x}')
        self.ids = [self.fxa('Q', 'ir') for _ in range(cabs)]
        self.pauses.clear()

    def knob(self, k, row, value):
        return self.say(f'FXP {self.ids[k]} {row} {value}')

    def turn(self, count=1):
        for _ in range(count):
            self.run('hyperrig_cab_turn')

    def settle(self):
        """Until nothing moves any more."""
        for _ in range(4):
            self.turn(20)
            for k in range(len(self.ids)):
                self.cut([0] * SIZE * 6 * FADE, k)

    def sound(self, samples):
        """Whole blocks of the audio task; the left side."""
        out = []
        for k in range(0, len(samples) - SIZE + 1, SIZE):
            out += self.frame(samples[k:k + SIZE])[0]
        return out

    def cuts(self, k=0):
        at = self.object(self.ids[k]) + CUTS
        rows = [struct.unpack('<10iiHBB5iB3x', self.mem.read(at + CUT * n, CUT)) for n in (0, 1)]
        return [{'part': r[10], 'hz': r[11], 'on': r[12], 'moving': r[13], 'there': r[:5] == r[14:19]} for r in rows]

    def cut(self, samples, k=0, turns=False):
        """The filters alone, block by block, as the audio task calls them behind the convolution; a turn of the control scan after every fourth."""
        out, at = [], 0x01D90000
        for n in range(0, len(samples) - SIZE + 1, SIZE):
            self.mem.write(at, struct.pack(f'<{SIZE}i', *samples[n:n + SIZE]))
            self.run('hyperrig_cab_sound', self.object(self.ids[k]), at, SIZE)
            out += struct.unpack(f'<{SIZE}i', self.mem.read(at, 4 * SIZE))
            if turns and n // SIZE % 4 == 3:
                self.turn()
        return out

    def took(self, samples):
        first = self.cpu.steps
        self.cut(samples)
        return self.cpu.steps - first


def tones(hz, count, first=0, level=FULL):
    return [round(level * math.sin(2 * math.pi * hz * n / RATE)) for n in range(first, first + count)]


def level(samples, hz):
    """Of one frequency, over whole periods."""
    n = len(samples) - len(samples) % max(1, round(RATE / hz))
    return abs(sum(x * cmath.exp(-2j * math.pi * hz * i / RATE) for i, x in enumerate(samples[:n]))) * 2 / n


def wanted(low, high, hz):
    """The level at a frequency in dB: Butterworth of the second order, with the frequencies as a digital filter has them."""
    t = lambda f: math.tan(math.pi * f / RATE)
    out = 0.0
    if low:
        out -= 10 * math.log10(1 + (t(low) / t(hz)) ** 4)
    if high:
        out -= 10 * math.log10(1 + (t(hz) / t(high)) ** 4)
    return out


def decibels(x):
    return 20 * math.log10(max(x, 1e-9))


def roughness(samples, hz):
    """The largest third difference: a tone of low frequency is taken down by it by far more than a step."""
    d = list(samples)
    for _ in range(3):
        d = [b - a for a, b in zip(d, d[1:])]
    return max(map(abs, d))


def impulse():
    return [30000] + [0] * 99


def check(build, before, row):
    p = Cabs(build, response=impulse())
    listing = p.say('FXT')
    at = next((i for i, x in enumerate(listing) if x.startswith('FXT 7 ir ')), None)
    rows = listing[at + 1:at + 8] if at is not None else []
    row('the list of the effects has the two knobs', rows[:6] == ['FXT  0 mezcla_pct 0..100 (100)', 'FXT  1 nivel_db -30..12 (0)', 'FXT  2 ir_slot 0..8 (0)',
        'FXT  3 largo_ms 0..85 (21)', 'FXT  4 lowcut_hz 0..800 (0)', 'FXT  5 hicut_hz 0..18000 (0)'] and rows[6].startswith('FXT 8 '), rows)

    r = random.Random(4)
    noise = [r.randrange(-FULL, FULL) for _ in range(SIZE * 2)]
    off = p.took(noise[:SIZE])
    if before:
        for name, response in (('an impulse', impulse()), ('a response', [round(9000 * math.exp(-n / 60) * math.cos(n * 1.3)) for n in range(600)])):
            a, b = Cabs(build, response=response), Cabs(before, response=response)
            x = a.sound(noise)
            row(f'both off: the samples of the build before, {name}', x == b.sound(noise) and any(x), '')

    # the level, at many frequencies
    worst, many = 0.0, (25, 40, 60, 80, 120, 200, 300, 600, 1000, 2000, 3000, 5000, 6000, 9000, 12000, 16000)
    plain = tones(440, SIZE * 2)
    row('off: the sound is let by', p.cut(plain) == plain, '')
    for low, high in ((100, 0), (800, 0), (20, 0), (0, 12000), (0, 18000), (0, 2000), (80, 5000), (800, 2000)):
        p.knob(0, LOW, low), p.knob(0, HIGH, TOP - high if high else 0)
        p.settle()
        seen, errors = p.cuts(), {}
        response = p.cut([1 << 26] + [0] * (SIZE * 64 - 1))
        for hz in many:
            want = wanted(low, high, hz)
            if want > -60:
                errors[hz] = round(decibels(abs(sum(x * cmath.exp(-2j * math.pi * hz * n / RATE) for n, x in enumerate(response))) / (1 << 26)) - want, 3)
        worst = max(worst, max(map(abs, errors.values())))
        row(f'low cut {low or "off"}, high cut {high or "off"}: the level they are meant to give', max(map(abs, errors.values())) < 0.1, errors)
        row(' the filters that are on, and at the frequency of the knob', [c['on'] for c in seen] == [int(low > 0), int(high > 0)] and
            all(not c['on'] or c['hz'] == hz and c['part'] == 1 << 16 and not c['moving'] and c['there'] for c, hz in zip(seen, (low, high))), seen)
    print(f'     the largest difference {worst:.3f} dB', flush=True)
    both = p.took(noise[:SIZE])
    p.knob(0, HIGH, 0)
    p.settle()
    one = p.took(noise[:SIZE])
    p.knob(0, LOW, 0)
    p.settle()
    none = p.took(noise[:SIZE])
    row('off again: the sound is let by', p.cut(noise) == noise and [c['on'] for c in p.cuts()] == [0, 0] and [c['part'] for c in p.cuts()] == [0, 0], p.cuts())
    row('what is off takes no time', none == off and none < one < both, [off, none, one, both])
    print(f'     instructions of a block: {none} without, {one - none} more for one, {both - none} more for both', flush=True)
    row('and nothing paused the sound for any of it', p.pauses == [], p.pauses[:4])
    row('within its limits', [p.knob(0, LOW, 900), p.knob(0, HIGH, 18001), p.knob(0, HIGH, -1)] is not None and
        all(0 <= v <= m for v, m in ((struct.unpack('<h', p.mem.read(p.object(p.ids[0]) + PARAMETERS + 2 * k, 2))[0], m) for k, m in ((LOW, 800), (HIGH, 18000)))), '')

    # a loud silence: what is on and gets nothing gives nothing after a while
    p.knob(0, LOW, 20), p.knob(0, HIGH, TOP - 2000)
    p.settle()
    p.cut(noise)
    tail = p.cut([0] * SIZE * 60)
    row('after the sound, silence', max(map(abs, tail[-SIZE:])) <= 2, max(map(abs, tail[-SIZE:])))
    loud = [((1 << 27) - 1) * (1 if n // 40 % 2 else -1) for n in range(SIZE * 4)]
    held = p.cut(loud)
    row('sound sixteen times over full level does not turn over', max(map(abs, held)) < 1 << 31 and all(abs(b - a) < 1 << 30 for a, b in zip(held, held[1:])), max(map(abs, held)))

    # no step: a tone while the knob is turned, switched on and off
    tone = 200
    for name, low, high in (('low cut', (40, 60, 110, 160, 300, 150, 60), (0,) * 7), ('high cut', (0,) * 7, (16000, 12000, 8000, 5000, 3000, 6000, 14000))):
        q = Cabs(build, response=impulse())
        out, count = q.cut(tones(tone, SIZE * 8)), SIZE * 4 * 3
        for a, b in [*zip(low, high), (0, 0), (0, 0)]:
            q.knob(0, LOW, a), q.knob(0, HIGH, TOP - b if b else 0)
            out += q.cut(tones(tone, count, len(out)), turns=True)
        # what a step of a hundredth of the sound would be, which is heard as a click: the third difference of it is as large as the step itself
        still, most = roughness(out[:SIZE * 8], tone), roughness(out, tone)
        row(f'{name}: no step in the sound while it is switched on, turned and switched off', most < FULL / 1000 and q.pauses == [] and max(map(abs, out[-SIZE:])) > FULL * .9,
            [still, most, round(FULL / 1000), q.pauses[:2]])
        print(f'     {name}: the largest third difference {most}, of the tone alone {still}, of a step of a thousandth {round(FULL / 1000)}', flush=True)
    q = Cabs(build, response=impulse())
    q.knob(0, LOW, 300)
    q.cut(tones(tone, SIZE * 4 * 4), turns=True)
    q.knob(0, LOW, 301)
    q.turn()
    row('the last step of one Hz is made too', q.cuts()[0]['hz'] == 301, q.cuts())
    q.settle()
    at = q.object(q.ids[0]) + CUTS
    q.mem.write(at, struct.pack('<i', struct.unpack('<i', q.mem.read(at, 4))[0] + 5000))      # the sound had said that it was there, and a new goal came
    still = q.cuts()[0]
    q.settle()
    row('a goal that came in the moment the sound arrived at the one before is not lost', not still['there'] and not still['moving'] and q.cuts()[0]['there'], [still, q.cuts()[0]])

    # scenes and presets
    q = Cabs(build, response=impulse())
    q.knob(0, LOW, 100), q.settle()
    q.say('SNAPSAVE 0')
    q.knob(0, LOW, 600), q.knob(0, HIGH, TOP - 4000), q.settle()
    q.say('SNAPSAVE 1')
    q.pauses.clear()
    q.say('SNAP 0')
    paused = list(q.pauses)
    middle = q.cuts()[0]['hz']
    q.settle()
    a = q.cuts()
    q.say('SNAP 1')
    q.settle()
    b = q.cuts()
    row('a scene has its own', [a[0]['hz'], a[1]['on'], b[0]['hz'], b[1]['hz'], b[1]['on']] == [100, 0, 600, 4000, 1], [a, b, paused])
    row('and it is not there with one step', middle != 100, middle)
    record = q.save()
    z = Cabs(build, response=impulse())
    same = z.apply(record)
    z.settle()
    c = z.cuts()
    row('a preset with the same blocks has its own, as a scene', same == 0 and [x['hz'] for x in c] == [600, 4000] and [x['part'] for x in c] == [1 << 16, 1 << 16], [same, c])
    z = Cabs(build, response=impulse(), cabs=0)
    z.fxa('Q', 'boost'), z.fxa('P', 'comp')
    failed = z.apply(record)
    z.ids = [i for i in range(16) if z.mem.read(z.object(i) + 2, 1)[0] and z.mem.read(z.object(i), 1)[0] == 7]
    c = z.cuts()
    row('a preset with others has its own at once', failed == 0 and [x['part'] for x in c] == [1 << 16, 1 << 16] and [x['hz'] for x in c] == [600, 4000], [failed, c])
    z.frame([0] * SIZE)
    again = z.cuts()
    z.turn(3)
    row('and stays there', z.cuts() == again == c, [c, z.cuts()])

    # two, stereo, others
    two = Cabs(build, response=impulse(), cabs=2)
    two.knob(1, LOW, 120)
    two.settle()
    row('two cabs: the one that was turned', [x['on'] for x in two.cuts(0)] == [0, 0] and [x['on'] for x in two.cuts(1)] == [1, 0], [two.cuts(0), two.cuts(1)])
    s, t = (Cabs(build, 100, response=impulse()) for _ in 'ab')
    s.knob(0, LOW, 200), s.settle()
    whole, less = t.sound(tones(100, SIZE * 14))[SIZE * 8:], s.sound(tones(100, SIZE * 14))[SIZE * 8:]
    got = decibels(level(less, 100) / level(whole, 100))
    row('in the sound of the whole audio task, in stereo', abs(got - wanted(200, 0, 100)) < 1, [got, wanted(200, 0, 100)])
    s = Cabs(build, 100, response=impulse(), cabs=0)
    s.fxa('Q', 'chorus')
    s.ids = [s.fxa('Q', 'ir')]
    calls, sound, decode = [], s.where['hyperrig_cab_sound'], s.cpu.decode

    def watch(pc):
        if pc == sound == s.cpu.pc and (not calls or calls[-1] != s.cpu.steps):
            calls.append(s.cpu.steps)
        return decode(pc)
    s.cpu.decode = watch
    for k in range(3):
        s.frame(places.signal(k))
    s.cpu.decode = decode
    row('and behind it: once a block, the cab being one sound', len(calls) == 3, len(calls))
    o = Cabs(build, response=impulse())
    other = o.fxa('Q', 'boost')
    kept = o.mem.read(o.object(other) + 288, 192)
    o.mem.write(o.object(other) + PARAMETERS + 2 * LOW, struct.pack('<2h', 55, 4000))
    o.turn(8)
    row('a block that is no cab is left alone', o.mem.read(o.object(other) + 288, 192) == kept, '')
    e = Cabs(build)
    e.turn(4)
    row('without a response there is no cab, and nothing to filter', e.ids == [None] and e.sound(noise)[-SIZE:] != [0] * SIZE, e.ids)

    # the part of the object that the filters have: nothing else of the firmware reads or writes it
    w = Cabs(build, response=impulse())
    w.knob(0, LOW, 90), w.knob(0, HIGH, TOP - 7000), w.settle()
    at, own, strange = w.object(w.ids[0]) + CUTS, {'hyperrig_cab_sound', 'hyperrig_cab_turn', 'hyperrig_cab_now', 'biquad_residual', 'cabs', 'follow', 'set', 'q28', 'move', 'prime'}, set()
    with (Path(build) / 'link/app.elf').open('rb') as elf:                     # with the names of the functions that are local to a file
        table = sorted((s['st_value'] & ~1, s.name) for s in ELFFile(elf).get_section_by_name('.symtab').iter_symbols()
                       if s.name and s['st_value'] and not re.match(r'L0[0-9a-f]{7}$|\.', s.name) and s['st_info']['type'] != 'STT_SECTION')
    keys = [v for v, _ in table]
    names = lambda pc: table[bisect.bisect_right(keys, pc) - 1][1]
    mem_read, mem_write, inside = w.mem.read, w.mem.write, [False]

    def noted(a, n, what):
        if inside[0] and a < at + 2 * CUT and at < a + n:
            strange.add((names(w.cpu.pc), what, a - at, n))
    w.mem.read = lambda a, n: (noted(a, n, 'r'), mem_read(a, n))[1]
    w.mem.write = lambda a, d: (noted(a, len(d), 'w'), mem_write(a, d))[1]
    inside[0] = True
    w.frame(noise[:SIZE])
    w.say('FXP 0 1 -3'), w.say('FXP 0 0 60'), w.say('FXE 0 0'), w.frame(noise[:SIZE]), w.say('FXE 0 1'), w.frame(noise[:SIZE]), w.say('FXP 0 3 60'), w.say('FXM 0 P 0'), w.frame(noise[:SIZE])
    inside[0] = False
    # a block that is moved to another place is copied whole, these with it (FXM)
    foreign = {x for x in strange if x[0] not in own and x[0] != 'effect_parameter_support_memmove'}
    row('nothing else of the firmware touches their part of the block', not foreign and strange, sorted(foreign)[:6])


class Tight(library.Playing):
    """With memory that ends: what was given back can be given again."""
    limit = 1 << 30

    def restart(self):
        self.held, self.wrong = {}, []
        super().restart()
        self.services[self.RELEASE] = self.release

    def allocate(self, a):
        if sum(self.held.values()) + a[0] > self.limit:
            return 0
        at = super().allocate(a)
        if at:
            self.held[at] = a[0]
        return at

    def release(self, a):
        if self.held.pop(a[0], None) is None:
            self.wrong.append(hex(a[0]))
        self.released.append(a[0])
        return 0

    def full(self, more=4096):
        self.limit = sum(self.held.values()) + more


def rooms(build, row, before=None):
    """Another cab where there is no room for a second convolution."""
    flash = library.foreign_flash()

    def made(what, shared=0):
        pedal = Tight(what, bytearray(flash))
        pedal.shortcuts()
        for k, (seed, count, name) in enumerate(((51, 1800, 'One'), (52, 1800, 'Two'), (53, 400, 'Short'))):
            pedal.upload_ir(library.wave(count, seed))
            pedal.line(f'ISAVE {k} {name}')
        pedal.line(f'ILOAD {shared}')
        pedal.line('FXA Q 99 ir')
        pedal.line('FXP 0 3 85')
        return pedal

    roomy = made(build)
    shared = roomy.block(0)
    first, taken = list(roomy.held), len(roomy.released)
    answer = roomy.line('FXIR 0 1')
    own = roomy.block(0)
    row('with room: a cab of its own, the one before given back when it is there', answer[-1].startswith('FXIR ok') and None not in own and own != shared and not roomy.wrong and
        len(roomy.held) == len(first), [answer, own, roomy.wrong])
    p = made(build)
    p.full()
    answer = p.line('FXIR 0 1')
    row('without: the same numbers, and no more memory than before', answer[-1].startswith('FXIR ok') and p.block(0) == own and sum(p.held.values()) <= p.limit and not p.wrong,
        [answer, p.block(0), own, p.wrong])
    answer = p.line('FXIR 0 -1')
    row('and back to the shared one', answer[-1].startswith('FXIR ok') and p.block(0) == shared and not p.wrong, [answer, p.block(0), shared])
    p.line('SNAPSAVE 0'), p.line('FXIR 0 1'), p.line('SNAPSAVE 1')
    seen = []
    for k in (0, 1, 0, 1):
        answer = p.line(f'SNAP {k}')
        seen.append((answer[-1].split(' ms=')[0], p.block(0) == (own if k else shared)))
    row('scenes with one and the other, there and back', seen == [(f'SNAP ok {k} missing=0', True) for k in (0, 1, 0, 1)] and not p.wrong, [seen, p.wrong])
    s = made(build, shared=2)
    s.full()
    kept = s.block(0)
    answer = s.line('FXIR 0 0')
    row('one that is longer than the place of the one before does not fit: that plays on', answer[-1].startswith('ERR') and s.block(0) == kept and None not in kept and not s.wrong,
        [answer, s.block(0), kept])
    s.limit = 1 << 30
    row('and is there as soon as there is room', s.line('FXIR 0 0')[-1].startswith('FXIR ok') and s.block(0)[0] == shared[0], s.block(0))
    if before:
        q = made(before)
        q.full()
        answer = q.line('FXIR 0 1')
        row('the build before did not: it kept the cab it had', not answer[-1].startswith('FXIR ok') and q.block(0) == shared, [answer, q.block(0)])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--only-rooms', action='store_true')
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append({'check': name, 'held': bool(good), 'seen': str(seen)[:260]})
        print('ok  ' if good else 'FAIL', name, '' if good else str(seen)[:260], flush=True)

    if not args.only_rooms:
        check(args.build, args.before, row)
    rooms(args.build, row, args.before)
    held = all(r['held'] for r in rows)
    print(json.dumps({'kind': 'mini-cab-check', 'held': held, 'checks': len(rows), 'hardware_test': False}))
    return 0 if held else 1


if __name__ == '__main__':
    sys.exit(main())
