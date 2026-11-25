"""Run a NAM capture that keeps knobs (docs/PARAMETRIC_NAM.md) on a built MINI application, in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of app.bin: the console lines the editor sends, the loader and the parser, the heap, the
commands of the amp, the engine. The capture is the one embedded in the application with an extension made here, of every kind of number;
what each number must become is computed here too, a second time and apart from the firmware and from the editor's page
(tests/test_mini_parametric.py compares with the page). Checked: the plain part is loaded as ever; the knobs are told; the amp's controls move
the numbers of the engine to exactly the expected ones, bit by bit, and back; the filters and the gain stay flat where a knob is moved; the
way there, in the half blocks of the sound, and what it costs; the sound, against a plain capture with the same numbers; another capture,
no memory, damaged files.

This is no hardware or audio test. The processor's time is not simulated; what is counted is instructions.

Usage, from the repository root:
    python -B tools/check_mini_parametric.py BUILD [--quick]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. --quick leaves out the sound.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_library as library  # noqa: E402

sim = library.sim
MAGIC, TAIL, LAYERS, C, TAPS = 0x31503241, 0x5041, 23, 3, 16
CB, MIX, L1, RECH, HEAD, HB = 1, 2, 4, 8, 16, 32
TICK, CYCLES = 6, 2.1                               # cycles of a tick; cycles an instruction takes, as the firmware's own costs have it


# ---- the form, from docs/PARAMETRIC_NAM.md
def layout():
    """[(kind, layer, first, count)] and how many numbers move."""
    groups, n = [], 0
    for kind, layer, count in [(k, i, c) for i in range(LAYERS) for k, c in ((CB, 3), (MIX, 3), (L1, 9)) if not (k == L1 and i == LAYERS - 1)] + \
            [(RECH, 0, 3), (HEAD, 0, 48), (HB, 0, 1)]:
        groups.append((kind, layer, n, count))
        n += count
    return groups, n


GROUPS, NUMBERS = layout()


def rounded(v, shift):
    return (v + (1 << (shift - 1))) >> shift if shift > 0 else v << -shift


def place(knob, v):
    v = max(-120, min(120, v))
    way = (knob['mid'] - knob['lo'] if v < 0 else knob['hi'] - knob['mid']) * v
    return knob['mid'] + (abs(way) // 120 * (1 if way >= 0 else -1))


def rows(table, x):
    """Rows of (shift, bias, weights), of 16384."""
    return [rounded((bias << 14) + sum(w * v for w, v in zip(weights, x)), shift) for shift, bias, weights in table]


def coefficients(e, x):
    return rows(e['far'], [v * e['slope'] >> 10 if v < 0 else v for v in rows(e['units'], x)])


def change(e, tones):
    """The change of every number for the six values of AMPEQ."""
    c, out = coefficients(e, [place(k, tones[k['control']]) for k in e['knobs']]), [0] * NUMBERS
    for (kind, layer, first, count), shift in zip(GROUPS, e['shift']):
        for i in range(first, first + count):
            total = sum(a * b for a, b in zip(c, e['B'][i * e['r']:(i + 1) * e['r']]))
            out[i] = total >> shift if shift > 0 else total << -shift
    return out


def pack(plain, e):
    body = struct.pack('<IBBBBHH', MAGIC, e.get('version', 1), len(e['knobs']), len(e['units']), e['r'], e['slope'], 0)
    for k in e['knobs']:
        body += struct.pack('<B11sffhhh', k['control'], k['name'].encode(), k['min'], k['max'], k['lo'], k['mid'], k['hi'])
    body += struct.pack(f'<{len(e["shift"])}b', *e['shift'])
    for shift, bias, weights in e['units'] + e['far']:
        body += struct.pack(f'<Bh{len(weights)}h', shift, bias, *weights)
    body += struct.pack(f'<{len(e["B"])}b', *e['B'])
    data = plain + body + struct.pack('<HH', len(body) + 8, TAIL)
    return data + struct.pack('<I', zlib.crc32(data))


def unpack(data):
    if len(data) < 60 or struct.unpack_from('<H', data, len(data) - 6)[0] != TAIL:
        return None
    size, = struct.unpack_from('<H', data, len(data) - 8)
    at = len(data) - size
    magic, version, knobs, units, r, slope, _ = struct.unpack_from('<IBBBBHH', data, at)
    if magic != MAGIC:
        return None
    o, e = at + 12, {'r': r, 'slope': slope, 'knobs': [], 'plain': at, 'version': version}
    for _ in range(knobs):
        control, name, lo, hi, a, b, c = struct.unpack_from('<B11sffhhh', data, o)
        e['knobs'].append({'control': control, 'name': name.split(b'\0')[0].decode(), 'min': lo, 'max': hi, 'lo': a, 'mid': b, 'hi': c})
        o += 26
    e['shift'] = list(struct.unpack_from(f'<{len(GROUPS)}b', data, o))
    o += len(GROUPS)
    for key, many, ins in (('units', units, knobs), ('far', r, units)):
        e[key] = []
        for _ in range(many):
            shift, bias, *weights = struct.unpack_from(f'<Bh{ins}h', data, o)
            e[key].append((shift, bias, weights))
            o += 3 + 2 * ins
    e['B'] = list(struct.unpack_from(f'<{NUMBERS * r}b', data, o))
    return e if o + NUMBERS * r + 8 == len(data) else None


def example(seed, r=7, units=16, knobs=None, slope=10):
    """An extension of made-up numbers, small enough to stay within the words of any capture; its directions are at 0 in the middle of the knobs."""
    rng = random.Random(seed)
    knobs = knobs or [{'control': 5, 'name': 'Gain', 'min': 0.0, 'max': 10.0, 'lo': -16384, 'mid': 0, 'hi': 16384},
                      {'control': 3, 'name': 'Tone', 'min': -12.0, 'max': 12.0, 'lo': -16384, 'mid': 3277, 'hi': 16384}]
    shift = {CB: -4, MIX: 10, L1: 11, RECH: 10, HEAD: 10, HB: 2}
    e = {'r': r, 'slope': slope, 'knobs': knobs, 'shift': [shift[g[0]] + (g[1] % 3 - 1) for g in GROUPS],
         'units': [(13, rng.randint(-9000, 9000), [rng.randint(-9000, 9000) for _ in knobs]) for _ in range(units)], 'B': [rng.randint(-127, 127) for _ in range(NUMBERS * r)]}
    middle = [v * slope >> 10 if v < 0 else v for v in rows(e['units'], [k['mid'] for k in knobs])]
    e['far'] = []
    for k in range(r):
        weights = [rng.randint(-9000, 9000) for _ in range(units)]
        e['far'].append((17 + k % 2, max(-32768, min(32767, -((sum(w * v for w, v in zip(weights, middle)) + 8192) >> 14))), weights))
    return e


# ---- the pedal
class Pedal(library.Pedal):
    def __init__(self, build):
        super().__init__(build, library.foreign_flash())
        self.shortcuts()

    def restart(self):
        super().restart()
        self.put(self.where['L01c3446c'], 'I', self.where['dsp_transition_notification_notify'])      # as the start-up code of the sound installs it

    def call(self, name, *args, limit=40_000_000, stop=None, hook=None):
        cpu = self.cpu
        cpu.R[:len(args)] = [a & sim.M for a in args]
        cpu.rets, cpu.pc, cpu.sp, start = sim.RETURN, self.where[name] if isinstance(name, str) else name, sim.STACK_TOP, cpu.steps
        while cpu.pc != sim.RETURN and cpu.pc != stop:
            service = self.services.get(cpu.pc)
            if service:
                cpu.R[0] = (service(list(cpu.R[:4])) or 0) & sim.M
                cpu.pc = cpu.rets
                continue
            if hook:
                hook(cpu)
            cpu.step()
            if cpu.steps - start > limit:
                raise RuntimeError(f'{name}: too many steps')
        self.steps = cpu.steps - start
        return cpu.R[0]

    def get(self, address, form):
        return struct.unpack('<' + form, self.cpu.mem.read(address, struct.calcsize('<' + form)))

    def put(self, address, form, *values):
        self.cpu.mem.write(address, struct.pack('<' + form, *values))

    def context(self):
        return self.where['L01c2bff0'] + 76

    def words(self):
        """The numbers of the engine, in the order of the form."""
        context, out = self.context(), []
        table, = self.get(context + 92, 'I')
        for kind, layer, first, count in GROUPS:
            d = table + 80 * layer
            if kind == CB:
                out += self.get(d + 52, '3i')
            elif kind == MIX:
                packed, = self.get(d + 44, 'I')
                out += self.get(packed + 18 * self.get(d, 'B')[0], '3h')
            elif kind == L1:
                out += self.get(self.get(d + 32, 'I')[0], '9h')
            elif kind == RECH:
                out += self.get(self.get(context + 60, 'I')[0], '3h')
            elif kind == HEAD:
                out += self.get(self.get(context + 68, 'I')[0], '48h')
            else:
                out += self.get(context + 72, 'q')
        return out

    def others(self):
        """The weights of the convolutions, and the biases of the matrices: no knob may move them."""
        table, = self.get(self.context() + 92, 'I')
        out = []
        for layer in range(LAYERS):
            d = table + 80 * layer
            out += self.get(self.get(d + 44, 'I')[0], f'{9 * self.get(d, "B")[0]}h') + self.get(self.get(d + 36, 'I')[0], '3q')
        return out

    def turn(self, count=1):
        for _ in range(count):
            self.call('hyperrig_capture_turn')

    def tone(self, *tones):
        return self.line('AMPEQ ' + ' '.join(map(str, tones)))

    def flat(self):
        """What the filters of the amp and its gain are asked for: the four sections, the volume, the gain that was told."""
        base = self.where['L01c32fa0']
        return self.get(base + 320, '20i') + self.get(base + 480, 'i') + self.get(self.where['L01c26890'] + 268, 'i')

    def heap(self):
        return self.call('L0203c15c', 16)


def check(build, quick, row):
    pedal = Pedal(build)
    plain = pedal.embedded()
    loaded = re.compile(r"LOAD rc=0 name='A2' layers=23 channels=3 audio=0 engine=A2L ms=\d+$")
    e = example(1)
    data = pack(plain, e)
    again = unpack(data)
    row('the form packs and unpacks, and is at 0 in the middle', again and all(again[k] == e[k] for k in ('r', 'slope', 'shift', 'units', 'far', 'B')) and not any(change(e, [0] * 6)), len(data))

    # plain captures, as ever
    answer = pedal.upload_capture(plain)
    pedal.call('hyperrig_parametric_turn')
    stored, others = pedal.words(), pedal.others()
    row('a plain capture loads, and has no knobs', loaded.match(answer[0]) and pedal.line('AMPK') == ['AMPK end'], [answer, pedal.lines])
    pedal.tone(0, 0, 0, 0, 0, 0)
    flat = pedal.flat()
    pedal.tone(0, 40, 0, -60, 0, 35)
    shaped = pedal.flat()
    row('its controls are filters and a gain, and move no number of the engine', shaped[:20] != flat[:20] and shaped[21] == 7 and pedal.words() == stored,
        {'told': shaped[21]})
    pedal.tone(0, 40, 0, 0, 0, 0)
    bass_only = pedal.flat()

    # with knobs
    answer = pedal.upload_capture(data)
    row('a capture with knobs is taken, checked and prepared', loaded.match(answer[0]), answer)
    row('its plain part is in the engine', pedal.words() == stored and pedal.others() == others, len(stored))
    pedal.call('hyperrig_parametric_turn')
    want = [f'AMPK {data[4892 + 12 + 26 * k:][:26].hex()}' for k in range(2)] + ['AMPK end']
    row('it says which knobs it has', pedal.line('AMPK') == want, pedal.lines)
    pedal.tone(0, 0, 0, 0, 0, 0)
    pedal.turn(40)
    row('with the controls at 0 it is the capture as it was stored', pedal.words() == stored, None)
    wrong, most, seen = [], 0, 0
    for tones in ((0, 0, 0, 120, 0, 120), (0, 0, 0, -120, 0, -120), (0, 0, 0, 120, 0, -120), (0, 0, 0, 7, 0, 5), (0, 0, 0, -33, 0, 85), (0, 0, 0, 0, 0, 0), (30, 60, -20, 77, 15, -115)):
        answer = pedal.tone(*tones)
        for _ in range(40):
            pedal.turn()
            most = max(most, pedal.steps)
        expected = [a + b for a, b in zip(stored, change(e, tones))]
        got = pedal.words()
        seen = max(seen, max(abs(a - b) for a, b in zip(got, stored)))
        if got != expected:
            wrong.append((tones, sum(a != b for a, b in zip(got, expected)), next(((i, a, b) for i, (a, b) in enumerate(zip(got, expected)) if a != b), None)))
        if answer != [f'AMPEQ volume={tones[0]} bass={tones[1]} mid={tones[2]} treble={tones[3]} presence={tones[4]} drive={tones[5]}']:
            wrong.append((tones, answer))
    row('its controls bring every number of the engine where it must be, to the bit, and back', not wrong and seen > 1000, wrong or {'numbers': len(stored), 'largest_change': seen})
    row('the other numbers of the engine stay', pedal.others() == others, None)
    pedal.tone(0, 40, 0, -60, 0, 35)
    row('the filters and the gain are flat where a knob is moved, and work where not', pedal.flat() == bass_only, [pedal.flat()[21]])

    # the way there
    pedal.tone(0, 0, 0, 0, 0, 0)
    pedal.turn(40)
    pedal.tone(0, 0, 0, 120, 0, 120)
    target = [a + b for a, b in zip(stored, change(e, (0, 0, 0, 120, 0, 120)))]
    far = max(range(len(stored)), key=lambda i: abs(target[i] - stored[i]))
    path, steps = [], []
    for _ in range(50):
        pedal.turn()
        steps.append(pedal.steps)
        path.append(pedal.words()[far])
    arrived = next((i + 1 for i, v in enumerate(path) if v == target[far] and pedal.words() == target), None)
    jumps = [abs(b - a) for a, b in zip([stored[far]] + path, path)]
    whole = abs(target[far] - stored[far])
    row('it goes there in sixteen equal steps, 42 ms, and then rests', arrived and arrived <= 32 and max(jumps) <= whole / 15 and path[-1] == target[far], {'half_blocks': arrived, 'largest_step': round(max(jumps) / whole, 3)})
    ticks = lambda n: round(n * CYCLES / TICK)
    moving, resting = max(steps), min(steps)
    row('what it costs in each half block', resting <= 60 and 2 * ticks(moving) <= 2000, {'instructions_moving': moving, 'ticks_moving': ticks(moving), 'instructions_resting': resting})

    # kept in a slot and loaded again
    answer = pedal.line('CSAVE 2 Knobs')
    row('it is saved', answer == [f"CSAVE ok 2 'Knobs' {len(data)} B"], answer)
    row('and reads back', pedal.slot('CREAD', 2) == data, len(data))
    pedal.upload_capture(plain)
    pedal.line('CSAVE 3 Plain')
    pedal.call('hyperrig_parametric_turn')
    row('a plain capture after it: its numbers, no knobs, and the controls are filters again', pedal.words() == stored and pedal.line('AMPK') == ['AMPK end'] and
        pedal.get(pedal.where['L01c26890'] + 268, 'i')[0] == 24, pedal.lines)
    pedal.tone(0, 0, 0, 0, 0, 0)
    pedal.restart()
    pedal.shortcuts()
    answer = pedal.line('CLOAD 2', limit=200_000_000)
    pedal.call('hyperrig_parametric_turn')
    pedal.tone(0, 0, 0, -50, 0, 25)
    pedal.turn(40)
    row('after a restart it loads from its slot, with its knobs', answer == ['CLOAD ok 2 audio=0'] and pedal.words() == [a + b for a, b in zip(stored, change(e, (0, 0, 0, -50, 0, 25)))],
        answer)
    pedal.line('CLOAD 3', limit=200_000_000)
    pedal.call('hyperrig_parametric_turn')
    pedal.line('CLOAD 2', limit=200_000_000)
    pedal.call('hyperrig_parametric_turn')
    pedal.turn(40)
    row('the knobs stand where the controls are when it comes back', pedal.words() == [a + b for a, b in zip(stored, change(e, (0, 0, 0, -50, 0, 25)))], None)
    pedal.tone(0, 0, 0, 0, 0, 0)
    trims = [pedal.line(f'CTRIM 2 {v}', limit=200_000_000)[0] for v in (-2.5, 1.5, -1, 3, -0.5)]         # there is little room behind it: the slot is written anew
    row('trims of it are kept, and it is as it was', all(re.match(rf'CTRIM ok slot=2 trim={v:.1f} .*saved=1', t) for v, t in zip((-2.5, 1.5, -1, 3, -.5), trims)) and
        pedal.slot('CREAD', 2) == data and pedal.library('CLIST')[0][2] == (len(data), 'Knobs'), trims[-1])

    # the memory goes back
    for _ in range(2):
        pedal.line('CLOAD 3', limit=200_000_000)
        pedal.call('hyperrig_parametric_turn')
    before = pedal.heap()
    pedal.call('L0203d218', before)
    for _ in range(3):
        for slot in (2, 3):
            pedal.line(f'CLOAD {slot}', limit=200_000_000)
            pedal.call('hyperrig_parametric_turn')
    after = pedal.heap()
    pedal.call('L0203d218', after)
    row('three times there and back: the memory comes back', before == after, [hex(before), hex(after)])

    # without memory
    pedal.line('CLOAD 2', limit=200_000_000)
    pedal.services[pedal.where['L0203c15c']] = lambda a: 0
    pedal.call('hyperrig_parametric_turn')
    del pedal.services[pedal.where['L0203c15c']]
    pedal.tone(0, 40, 0, 0, 0, 35)
    pedal.turn(40)
    row('without memory it plays as it was stored, and its controls are filters', pedal.words() == stored and pedal.flat()[21] == 7 and pedal.line('AMPK') == ['AMPK end'],
        pedal.flat()[21])
    pedal.tone(0, 0, 0, 0, 0, 0)

    # damaged: refused as any other file that is not a capture, and what played goes on with its knobs
    pedal.restart()
    pedal.shortcuts()
    pedal.upload_capture(data)
    pedal.call('hyperrig_parametric_turn')
    pedal.tone(0, 0, 0, 60, 0, -60)
    pedal.turn(40)
    playing = pedal.words()
    bad = {}
    for name, change_of in (('another version', {'version': 2}), ('a control that is none', {'knobs': [dict(e['knobs'][0], control=6), e['knobs'][1]]}),
                            ('too many units', example(3, r=1, units=25)), ('too many knobs', example(3, r=1, knobs=e['knobs'] * 3)), ('no direction', {'r': 0, 'far': [], 'B': []})):
        bad[name] = pedal.upload_capture(pack(plain, dict(e, **change_of)))
    cut = data[:-9] + struct.pack('<I', zlib.crc32(data[:-9]))
    bad['cut short'] = pedal.upload_capture(cut)
    twisted = bytearray(data[:-4])
    twisted[300] ^= 4
    twisted = bytes(twisted) + struct.pack('<I', zlib.crc32(bytes(twisted)))
    bad['a changed byte of the plain part'] = pedal.upload_capture(twisted)
    row('damaged captures are refused', all(a and 'rc=-' in a[0] for a in bad.values()), bad)
    pedal.call('hyperrig_parametric_turn')
    pedal.turn(40)
    row('and what played goes on with its knobs', pedal.words() == playing and playing != stored and pedal.line('AMPK') == want, None)

    # five knobs, straight ones
    five = example(5, r=4, units=4, slope=1024, knobs=[{'control': c, 'name': n, 'min': 0.0, 'max': 1.0, 'lo': -16384, 'mid': 0, 'hi': 16384}
                                                       for c, n in ((1, 'Bass'), (2, 'Mid'), (4, 'Presence'), (3, 'Treble'), (5, 'Gain'))])
    answer = pedal.upload_capture(pack(plain, five))
    pedal.call('hyperrig_parametric_turn')
    pedal.tone(0, 0, 0, 0, 0, 0)
    pedal.turn(40)
    pedal.tone(-30, 100, -70, 55, 35, -15)
    pedal.turn(40)
    row('a capture with five knobs', loaded.match(answer[0]) and pedal.words() == [a + b for a, b in zip(stored, change(five, (-30, 100, -70, 55, 35, -15)))] and pedal.others() == others, None)

    if not quick:
        sound(pedal, plain, e, data, row)


def baked(plain, e, tones):
    """The plain capture whose own numbers are those the knobs make: the engine must sound the same with it."""
    delta, out, o = change(e, tones), bytearray(plain), 36
    at = {(g[0], g[1]): g[2] for g in GROUPS}

    def add16(where, count, first):
        for i in range(count):
            v, = struct.unpack_from('<h', out, where + 2 * i)
            struct.pack_into('<h', out, where + 2 * i, max(-32768, min(32767, v + delta[first + i])))
    fin, fx, fh, fout = struct.unpack_from('<4b', out, 16)
    prev = fx
    add16(o + 1, 3, at[RECH, 0])
    o += 7
    for i in range(LAYERS):
        k, dil, fz, fx3, lmul, cf = struct.unpack_from('<BHbbib', out, o)
        o += 10 + 18 * k
        for c in range(3):
            v, = struct.unpack_from('<q', out, o + 8 * c)
            shift = cf + prev - fz
            whole = rounded(v, shift) + delta[at[CB, i] + c]                  # what the parser makes of it, and the change
            struct.pack_into('<q', out, o + 8 * c, whole << shift)
        o += 25
        add16(o, 3, at[MIX, i])
        o += 7
        if i < LAYERS - 1:
            add16(o, 9, at[L1, i])
        o += 42
        prev = fx3
    hf, = struct.unpack_from('<b', out, o)
    o += 1
    for c in range(3):
        for t in range(TAPS):
            v, = struct.unpack_from('<h', out, o + 2 * (c * TAPS + t))
            struct.pack_into('<h', out, o + 2 * (c * TAPS + t), max(-32768, min(32767, v + delta[at[HEAD, 0] + 3 * t + c])))
    o += 96
    v, = struct.unpack_from('<q', out, o)
    shift = hf + fh - fout
    struct.pack_into('<q', out, o, (rounded(v, shift) + delta[at[HB, 0]]) << shift)
    out[-4:] = struct.pack('<I', zlib.crc32(bytes(out[:-4])))
    return bytes(out)


def sound(pedal, plain, e, data, row):
    """Two half blocks through the engine: with the knobs moved, and with the plain capture that has the same numbers. And the sound task's own way."""
    IN, OUT = 0x01C72000, 0x01C72400
    tones, rng = (0, 0, 0, 90, 0, -80), random.Random(2)
    wave = [rng.randint(-2 ** 22, 2 ** 22) for _ in range(128)]

    def play():
        pedal.call('capture_live_reset', pedal.context())
        pedal.put(IN, '128i', *wave)
        pedal.call('capture_live_process', pedal.context(), IN, OUT, 128, limit=80_000_000)
        return pedal.get(OUT, '128i')
    pedal.restart()
    pedal.shortcuts()
    pedal.upload_capture(data)
    pedal.call('hyperrig_parametric_turn')
    pedal.tone(0, 0, 0, 0, 0, 0)
    pedal.turn(40)
    middle = play()
    pedal.tone(*tones)
    pedal.turn(40)
    moved = play()
    pedal.upload_capture(plain)
    pedal.call('hyperrig_parametric_turn')
    pedal.tone(0, 0, 0, 0, 0, 0)
    as_stored = play()
    pedal.upload_capture(baked(plain, e, tones))
    pedal.call('hyperrig_parametric_turn')
    same = play()
    row('the sound at 0 is that of the plain capture', middle == as_stored and any(middle), None)
    row('the sound with the knobs moved is that of a capture with the same numbers', moved == same and moved != middle, sum(a != b for a, b in zip(moved, same)))

    # the sound task: its block of 128, with the second core's work done when it is asked for
    pedal.restart()
    pedal.shortcuts()
    pedal.upload_capture(data)
    pedal.call('hyperrig_parametric_turn')
    pedal.tone(*tones)
    block, at, places = pedal.where['L01c2bff0'], pedal.where['hyperrig_capture_turn'], []
    pedal.put(IN, '128i', *wave)
    pedal.put(block + 12, 'I', 0)                                             # the head by the second core
    pedal.put(block + 8, 'I', 0)

    def spy(cpu):
        if cpu.pc == at:
            places.append(pedal.get(block + 8, 'I')[0])
        elif cpu.pc == pedal.where['L01c04d98'] and pedal.get(block + 8, 'I')[0]:
            pedal.put(block + 8, 'I', 0)                                       # the second core is done
    words = pedal.words()
    pedal.call('capture_async_run', IN, OUT, limit=80_000_000, hook=spy)
    row('the sound task goes there twice in a block, when the second core has no work', places == [0, 0] and pedal.words() != words,
        places)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})
        print(('ok   ' if good else 'FAIL ') + name, '' if seen is None else json.dumps(seen, default=str)[:300], file=sys.stderr, flush=True)

    check(args.build, args.quick, row)
    held = all(r['held'] for r in rows)
    print(json.dumps({'kind': 'mini-parametric-check', 'build': args.build.name, 'hardware_test': False, 'held': held, 'checks': rows}, indent=1, default=str))
    return 0 if held else 1


if __name__ == '__main__':
    raise SystemExit(main())
