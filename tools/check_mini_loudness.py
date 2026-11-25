"""Run the measure of loudness of a product build (mini/product/loudness.c) in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of a built firmware, by its console words: the memory it takes and gives back, what it
records of an input, a stroke that is sent and played, and what it measures at the end of a chain that stands here in Python: clean,
compressed, clipped, with two channels. The reference is BS.1770 in Python, in double precision, on the same samples. Then the two places
in the audio task, what ends a measure (a footswitch in both layouts, silence of the editor), what comes back, and the gains that are
written into a stored preset. Nothing of this is a hardware or audio test: the time of the pedal, its flash and its sound are not simulated.

Usage, from the repository root:
    python -B tools/check_mini_loudness.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product."""
from __future__ import annotations

import copy
import json
import math
import random
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_panel as harness  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402
import make_loudness_tables as tables  # noqa: E402

sim = harness.sim
RATE, BLOCK, SLICE, WINDOW, FULL = 48077, 128, 512, 0.4 * 48077, 2.0 ** 26
HEAD, RING, CODES, STROKE_WORDS = 32, 1024, 8192, 1408                  # words before the data of REC, and of codes; codes; halfwords of a stroke
REC, STROKE, BUFFER, FRAME = 0x01C66000, 0x01C68000, 0x01C71000, 0x01C73000
S_ENGINE, S_STAGE, S_MEMORY, G_SCENE = 280, 25, 456, 88
TICK, CYCLES = 6, 2.1                               # cycles of a tick; cycles an instruction takes, as the firmware's own costs have it
STEPS, MOVES = (16, 17, 19, 21, 23, 25, 27, 29), (-1, -1, -1, -1, 2, 4, 6, 8)


# The reference, from the Recommendation and from docs/MINI_LOUDNESS.md, and not from the firmware's code.
def weighted(x):
    out = x
    for b, a in (tables.at_rate(tables.SHELF), tables.at_rate(tables.HIGH)):
        y, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
        for v in out:
            w = b[0] * v + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
            x1, x2, y1, y2 = v, x1, w, y1
            y.append(w)
        out = y
    return out


def lufs(mean):
    return -0.691 + 10 * math.log10(mean + 1e-20)


def momentary(channels, hop=BLOCK):
    """The loudest 400 ms of samples of full scale 1, and where it begins; the mean of the channels."""
    energy = [sum(v) / len(channels) for v in zip(*([w * w for w in weighted(x)] for x in channels))]
    total, sums = 0.0, [0.0]
    for e in energy:
        total += e
        sums.append(total)
    n = round(WINDOW)
    return max((lufs((sums[i + n] - sums[i]) / n), i) for i in range(0, len(energy) - n + 1, hop))


def loudest(slices, first=0, last=None):
    """The same from the energies of slices, as the editor makes it: 400 ms are 37 slices and a part of the next."""
    whole, part = int(WINDOW // SLICE), WINDOW / SLICE - WINDOW // SLICE
    last = len(slices) - whole - 1 if last is None else last
    return max(lufs((sum(slices[i:i + whole]) + part * max(slices[i - 1] if i else 0.0, slices[i + whole])) / (whole + part)) for i in range(first, last + 1))


class Codes:
    """The codes of a stroke: four bits a sample, at a quarter of the rate."""

    def __init__(self):
        self.guess = self.step = 0

    def size(self):
        return STEPS[self.step & 7] << (self.step >> 3)

    def sample(self, code):
        d = self.size() * (2 * (code & 7) + 1) >> 3
        self.guess = max(-30000, min(30000, self.guess + (-d if code & 8 else d)))
        self.step = max(0, min(87, self.step + MOVES[code & 7]))
        return self.guess

    def code(self, v):
        d = v - self.guess
        code = (8 if d < 0 else 0) | min(7, abs(d) * 4 // self.size())
        self.sample(code)
        return code


def decoded(codes):
    c = Codes()
    return [c.sample(v) for v in codes]


def encoded(samples):
    c = Codes()
    return [c.code(int(v)) for v in samples]


def pluck(hertz, seconds, peak, rate=RATE, seed=1):
    """A plucked string: partials that fall, the higher the faster, and the noise of the pick."""
    rng, n, out = random.Random(seed), int(seconds * rate), None
    phases = [rng.uniform(0, 2 * math.pi) for _ in range(24)]
    out = [0.0] * n
    for k in range(1, 25):
        f = hertz * k * math.sqrt(1 + 4e-5 * k * k)
        if f > 5000:
            break
        a, fall, w = math.sin(math.pi * k * 0.17) / k ** 0.9, 1.6 + 0.9 * k, 2 * math.pi * f / rate
        for i in range(n):
            out[i] += a * math.exp(-fall * i / rate) * math.sin(w * i + phases[k - 1])
    for i in range(int(0.004 * rate)):
        out[i] = out[i] * i / (0.004 * rate) + rng.uniform(-0.4, 0.4) * math.exp(-i / (0.002 * rate))
    top = max(abs(v) for v in out)
    return [peak * v / top for v in out]


def quarter(x):
    """What is at a quarter of the rate of samples of full scale 1, without what is above 5 kHz: a long low-pass."""
    taps, cut = 255, 5200 / RATE
    h = [(2 * cut if i == 127 else math.sin(2 * math.pi * cut * (i - 127)) / (math.pi * (i - 127))) * (0.42 - 0.5 * math.cos(2 * math.pi * i / 254) + 0.08 * math.cos(4 * math.pi * i / 254))
         for i in range(taps)]
    total = sum(h)
    return [sum(h[k] * x[n - k + 127] for k in range(taps) if 0 <= n - k + 127 < len(x)) / total for n in range(0, len(x), 4)]


class Meter(scenes.Pedal):
    def __init__(self, build):
        super().__init__(build)
        self.vendor, self.pool, self.events, self.gone, self.blocks = True, True, [], False, {}
        own = {'heap_access_vendor_allocate_wrapper': lambda a: self.take('vendor', a[0]), 'block_pool_allocate': lambda a: self.take('pool', a[1]),
               'block_pool_contains': lambda a: int(self.blocks.get(a[1], ('',))[0] == 'pool'), 'block_pool_release': lambda a: self.gave(a[1]),
               'L0203d218': lambda a: self.gave(a[0]), 'L0203feb8': lambda a: 0, 'dispatch_helpers_audio_hold': lambda a: 0, 'preset_loader_load': self.load_preset,
               'scene_application_apply': self.apply_scene, 'controls_transition': lambda a: self.events.append(('transition', a[0], a[1])) or 0}
        self.at.update({self.where[n]: f for n, f in own.items()})
        self.state(S_ENGINE, 2)
        self.setting(harness.G_PRESET, 3)
        self.setting(G_SCENE, 1)

    # services
    def take(self, whose, size):
        if not getattr(self, whose):
            return 0
        at = REC if REC not in self.blocks and not self.stroke_next else STROKE
        self.blocks[at] = (whose, size)
        self.mem.write(at, b'\x5a' * size)
        return at

    stroke_next = False

    def gave(self, address):
        self.events.append(('gave', 'stroke' if address == STROKE else 'memory', self.stage()))
        self.blocks.pop(address, None)
        return 0

    def load_preset(self, a):
        self.events.append(('preset', a[0], self.stage()))
        if self.gone:
            return 0xFFFFFFFF
        self.setting(harness.G_PRESET, a[0])
        self.setting(G_SCENE, -1)
        return 0

    def apply_scene(self, a):
        self.events.append(('scene', a[0], self.stage()))
        self.setting(G_SCENE, a[0])
        return 0

    # state
    def state(self, at, value=None, n=4):
        where = self.where[scenes.STATE] + at
        if value is not None:
            self.mem.write(where, value.to_bytes(n, 'little'))
        return int.from_bytes(self.mem.read(where, n), 'little')

    def stage(self):
        return self.state(S_STAGE, n=1)

    def turns(self, count):
        for _ in range(count):
            self.run('hyperrig_level_turn')

    # the audio: the tap of REC, and the hooks as the audio task calls them
    def input(self, samples):
        """A block of the input through the hook: 32-bit words of full scale 2**30."""
        if self.stage() < 5:
            return samples
        self.mem.write(BUFFER, struct.pack(f'<{BLOCK}i', *samples))
        before = self.cpu.steps
        self.run('hyperrig_level_input', BUFFER)
        self.input_steps = self.cpu.steps - before
        return list(struct.unpack(f'<{BLOCK}i', self.mem.read(BUFFER, 4 * BLOCK)))

    def output(self, left, right=None):
        if self.stage() < 6:
            return
        self.mem.write(BUFFER, struct.pack(f'<{BLOCK}i', *left))
        if right is not None:
            self.mem.write(self.where['L01c23f68'] + 192, struct.pack(f'<{BLOCK}i', *right))
        before = self.cpu.steps
        self.run('hyperrig_level_output', BUFFER, int(right is not None))
        self.output_steps = self.cpu.steps - before

    def memory(self, words):
        """REC 4, and the blocks that its own tap fills: then it is the measure's."""
        answer = self.say(f'REC 4 {words}')
        for _ in range(words // BLOCK + 1):
            self.run('audio_task_tap', 4, BUFFER)
        return answer[0].startswith('REC tap=4 ')

    def words(self, at, count):
        out = []
        while len(out) < count:
            line = self.say(f'RECD {at + len(out)}')[0]
            head = f'RECD {at + len(out)} '
            if not line.startswith(head) or len(line) == len(head):
                raise ValueError(line)
            out += [int(line[i:i + 8], 16) for i in range(len(head), len(line), 8)]
        return out[:count]

    def put(self, codes):
        """A stroke, as the editor sends it: two codes a byte, the first in its low half."""
        self.stroke_next = True
        made = self.say(f'INJBEGIN {STROKE_WORDS}') == [f'OK INJBEGIN {STROKE_WORDS}']
        self.stroke_next = False
        data = bytes(codes[i] | codes[i + 1] << 4 for i in range(0, len(codes), 2))
        return made and all(self.say(f'INJB {at} {data[at:at + 88].hex()}') == [f'OK INJB {at} {len(data[at:at + 88])}'] for at in range(0, len(data), 88))

    def measure(self, length, plays, before, total):
        return self.say('HRLV 06' + bytes((length, plays, before, total)).hex())

    def levels(self):
        done, peak, running = self.words(0, 3)
        return [struct.unpack('<f', struct.pack('<I', w))[0] for w in self.words(HEAD, done)] if done else [], done, peak, running

    def segment(self, start, stop, registers, limit=400_000):
        """The audio task's own instructions from a label to a service, with the registers it has there."""
        for r, v in registers.items():
            self.cpu.R[r] = v & sim.M
        self.mem.write(FRAME, struct.pack('<64I', *(0x7000 + i for i in range(64))))
        cpu, before = self.cpu, self.cpu.steps
        cpu.pc, cpu.sp, cpu.rets = self.where[start], FRAME, sim.RETURN
        own = {self.where[n]: n for n in ('storage_platform_clock', 'hyperrig_level_input', 'hyperrig_level_output')}
        called = []
        while cpu.pc != self.where.get(stop, stop):
            name = own.get(cpu.pc)
            if name:
                called.append((name, cpu.R[0], cpu.R[1]))
                cpu.R[0:4] = [0xDEAD0000 + k for k in range(4)]
                cpu.pc = cpu.rets
                continue
            cpu.step()
            if cpu.steps - before > limit:
                raise RuntimeError('too many steps')
        return called, cpu.steps - before


def check(build):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': copy.deepcopy(seen)})
        print('ok  ' if good else 'FAIL', name, '' if good else seen, file=sys.stderr, flush=True)     # it takes some minutes

    db = lambda a, b: 20 * math.log10((a + 1e-12) / (b + 1e-12))
    p = Meter(build)
    say = p.say
    row('the numbers are those of the tool', tables.main(['--check']) == 0)

    # the words, without memory and with it
    row('without memory nothing is recorded or measured, and it is said', [say('HRLV 05'), p.measure(8, 1, 0, 8)] == [['HRLV 5 -1'], ['HRLV 6 -1']] and p.stage() == 0, p.stage())
    say('HRLV 01')
    row('HRLV alone is an answer', say('HRLV') == ['HRLV 0 -1'])
    say('HRLV 01')
    p.memory(184)
    row('too little memory is refused: for the recording, and for more slices than it has room for', [say('HRLV 05')[0][:6], p.measure(176, 2, 64, 153)[0][:6], p.measure(176, 2, 64, 152)] == ['HRLV 5', 'HRLV 6', ['HRLV 0 0']] and
        p.stage() == 6, p.stage())
    p.events.clear()
    row('01 gives it back', say('HRLV 01') == ['HRLV 0 -1'] and p.events == [('gave', 'memory', 0)] and p.stage() == 0 and p.state(S_MEMORY) == 0, p.events)

    # what the editor looks at before it begins: the engine, the tuner, the bypass
    def seen():
        m = re.search(r' m=(\d) .* tu=(\d) .* fm=\d+,\d+,\d+,(\d)', say('LVL')[0])
        return m and m.groups()
    states = {'plays': seen()}
    for name, at, value, width in (('engine', S_ENGINE, 1, 4), ('tuner', 52, 1, 1), ('bypass', 77, 1, 1)):
        kept = p.state(at, n=width)
        p.state(at, value, width)
        states[name] = seen()
        p.state(at, kept, width)
    row('LVL says whether the engine runs, the tuner is open, and it is in bypass', states == {'plays': ('2', '0', '0'), 'engine': ('1', '0', '0'), 'tuner': ('2', '1', '0'), 'bypass': ('2', '0', '1')}, states)

    # what is recorded
    stroke = pluck(196.0, 0.3, 0.25)
    guitar = [0] * 5 * BLOCK + [round(v * 2 ** 30) for v in stroke]
    guitar = guitar[:len(guitar) // BLOCK * BLOCK]
    p.memory(HEAD + RING + 86)
    row('05 records', say('HRLV 05') == ['HRLV 0 0'] and p.stage() == 5)
    got, through = [], True
    for n in range(len(guitar) // BLOCK):
        block = guitar[n * BLOCK:(n + 1) * BLOCK]
        through = through and p.input(block) == block
        if n % 40 == 39 or n == len(guitar) // BLOCK - 1:
            there = int(say('HRLV')[0].split()[2])
            for w in p.words(HEAD + len(got) // 8, (there - len(got)) // 8):
                got += [w >> 4 * k & 15 for k in range(8)]
    record_steps = p.input_steps
    row('the player hears the guitar while it is recorded', through)
    row('RECD gives every code once, in order', len(got) == len(guitar) // 4, [len(got), len(guitar) // 4])
    heard, wanted, near = [v / 32768 for v in decoded(got)], None, None
    for late in range(20, 29):                                                      # in samples of the input
        want = quarter([0.0] * late + [v / 2 ** 30 for v in guitar])[:len(heard)]
        rest = sum((a - b) ** 2 for a, b in zip(heard, want))
        if near is None or rest < near[0]:
            near, wanted = (rest, late), want
    noise, energy = 10 * math.log10(sum(v * v for v in wanted) / near[0]), db(sum(v * v for v in heard) ** .5, sum(v * v for v in wanted) ** .5)
    row('what is recorded is the guitar, at a quarter of the rate: 22 dB over what differs, and the same energy', noise > 22 and abs(energy) < 0.1,
        {'signal_to_rest_db': round(noise, 1), 'late_by_samples': near[1], 'energy_db': round(energy, 3)})
    p.mem.write(REC, struct.pack('<I', CODES - 32))                                 # at the end of the ring, around it
    tail = [[round(2 ** 28 * math.sin((128 * n + i) / 20)) for i in range(BLOCK)] for n in range(3)]
    p.mem.write(REC + 4 * (HEAD + RING + 86), b'\x5a' * 4)
    for block in tail:
        p.input(block)
    row('the ring goes round within its memory', int(say('HRLV')[0].split()[2]) == CODES + 64 and p.mem.read(REC + 4 * (HEAD + RING + 86), 4) == b'\x5a' * 4, p.mem.read(REC + 4 * (HEAD + RING + 86), 4).hex())
    say('HRLV 05')
    for _ in range(6):
        p.input([2 ** 30 - 1 if i // 40 % 2 else -2 ** 30 for i in range(BLOCK)])
    loud = decoded([w >> 4 * k & 15 for w in p.words(HEAD, 24) for k in range(8)])
    row('a guitar that is too loud is held, and does not turn over', max(abs(v) for v in loud) <= 30000 and max(loud) > 20000 and min(loud) < -20000, [max(loud), min(loud)])
    p.events.clear()
    say('HRLV 01')
    row('the end of a recording gives its memory back, and neither holds the amp nor loads a preset', p.events == [('gave', 'memory', 0)] and p.stage() == 0, p.events)

    # a stroke that is played
    low = quarter(pluck(110.0, 0.47, 0.3, seed=3))
    codes = encoded(v * 32768 for v in low)
    codes = codes[:len(codes) // 32 * 32]
    p.memory(184)
    row('INJBEGIN and INJB take a stroke', p.put(codes))
    raw = p.mem.read(STROKE, len(codes) // 2)
    row('and keep it as it is', [raw[i // 2] >> (4 * (i & 1)) & 15 for i in range(len(codes))] == codes)
    blocks, lead, plays = len(codes) // 32, 4, 2
    slices = lead + (plays * blocks + 3) // 4 + 1
    row('06 plays it, and the output is silent', p.measure(blocks, plays, 4 * lead, slices) == ['HRLV 0 0'] and p.stage() == 6, p.stage())
    played, steps = [], []
    running = lambda: struct.unpack('<I', p.mem.read(REC + 8, 4))[0]
    for n in range(4 * slices):
        if not running():
            break
        played += p.input([round(2 ** 29 * math.sin(i)) for i in range(BLOCK)])
        steps.append(p.input_steps)
        p.output([v >> 4 for v in played[-BLOCK:]])
    for _ in range(2):
        rest = p.input([5] * BLOCK)
    row('a run is as long as it was told, and then the input is silence', n + 1 == 4 * slices and not running() and rest == [0] * BLOCK, [n + 1, 4 * slices])
    shape = [v / 2 ** 30 for v in played]
    silence = shape[:lead * SLICE]
    first, second = shape[lead * SLICE:lead * SLICE + blocks * BLOCK], shape[lead * SLICE + blocks * BLOCK:lead * SLICE + 2 * blocks * BLOCK]
    row('silence, and the guitar that is plugged in is not heard', max(abs(v) for v in silence) == 0)
    row('both plays are the same', max(abs(a - b) for a, b in zip(first[100:], second[100:])) < 2e-4, max(abs(a - b) for a, b in zip(first[100:], second[100:])))
    back = quarter(first)
    want = [v / 32768 for v in decoded(codes)]
    best = min((sum((a - b) ** 2 for a, b in zip(back[30 + d:], want[30:-30])), d) for d in range(0, 14))
    apart = 10 * math.log10(sum(v * v for v in want) / best[0])
    row('what is played is what was sent, 25 dB over what differs', apart > 25, {'signal_to_rest_db': round(apart, 1), 'late_by': best[1]})

    # what is measured: chains in Python on what was played, against the reference. Clean was measured in the run above.
    length, start = 48, lead * SLICE + blocks * BLOCK - 2 * SLICE                   # of the second play, with a little of the first

    def chain(kind):
        part = shape[start:start + length * SLICE]
        if kind == 'compressed':
            level, out = 0.0, []
            for v in part:
                level = max(abs(v), level * 0.9995)
                out.append(v * (0.02 + level) ** -0.7 * 0.12)
            return [out]
        if kind == 'clipped':
            return [[max(-0.22, min(0.28, 40 * v)) for v in part]]
        if kind == 'loud':                                                          # beyond full scale, before the output gain brings it down
            return [[6 * v for v in part]]
        left = [math.tanh(5 * v) * 0.3 for v in part]                               # two channels
        return [left, [0.0] * 9 + [0.5 * v for v in left[:-9]]]

    results, worst, mono_steps = {}, 0.0, p.output_steps
    for kind in ('clean', 'compressed', 'clipped', 'loud', 'stereo'):
        words = [[v >> 4 for v in played]] if kind == 'clean' else [[int(v * FULL) for v in x] for x in chain(kind)]
        count = len(words[0]) // SLICE
        if kind != 'clean':
            p.measure(blocks, 1, 0, count)
            for n in range(4 * count):
                p.output(words[0][n * BLOCK:(n + 1) * BLOCK], words[1][n * BLOCK:(n + 1) * BLOCK] if len(words) > 1 else None)
        energies, done, peak, still = p.levels()
        mine = loudest(energies)
        reference, where = momentary([[v / FULL for v in x] for x in words])
        whole = sum(sum(w * w for w in weighted([v / FULL for v in x])) for x in words) / len(words) / len(words[0])
        apart = 10 * math.log10(sum(energies) / len(energies) / whole)
        results[kind] = {'lufs': round(mine, 3), 'reference': round(reference, 3), 'all_of_it_db': round(apart, 4), 'peak_dbfs': round(20 * math.log10(peak / FULL), 2)}
        worst = max(worst, abs(mine - reference), abs(apart))
        row(f'{kind}: every slice, the peak, and done', (done, peak, still) == (count, max(abs(v) for x in words for v in x), 0) and len(energies) == count, [done, peak, still])
    stereo_steps = p.output_steps
    row('the loudest 400 ms of each are those of BS.1770 within 0.1 LU', worst < 0.1, results)
    # 997 Hz at full scale is -3.01 LUFS in one channel
    sine = [int((FULL - 1) * math.sin(2 * math.pi * 997 * i / RATE)) for i in range(48 * SLICE)]
    p.measure(blocks, 1, 0, 48)
    for n in range(192):
        p.output(sine[n * BLOCK:(n + 1) * BLOCK])
    energies = p.levels()[0]
    row('997 Hz at full scale: -3.01 LUFS', abs(loudest(energies, 5) + 3.01) < 0.03, round(loudest(energies, 5), 3))
    # a stroke that went through the codes is as loud as the stroke
    original = pluck(110.0, 0.47, 0.3, seed=3)
    a, b = momentary([original + [0.0] * 2000])[0], momentary([first + [0.0] * 2000])[0]
    row('a stroke through the codes is as loud as it was, within 0.2 LU', abs(a - b) < 0.2, [round(a, 3), round(b, 3)])
    p.say('INJ free')
    p.measure(blocks, 1, 0, 48)
    row('without a stroke it is silence that is played', [v for _ in range(3) for v in p.input([9] * BLOCK)] == [0] * 3 * BLOCK)

    # what ends it, and what comes back
    say('HRLV 01')
    p.events.clear()

    def measuring(preset=9, scene=2, start=(3, 1)):
        p.setting(harness.G_PRESET, start[0])
        p.setting(G_SCENE, start[1])
        say('HRLV')
        p.memory(184)
        p.put(codes[:64])
        p.measure(2, 1, 0, 40)
        p.turns(2)
        p.setting(harness.G_PRESET, preset)
        p.setting(G_SCENE, scene)
        p.events.clear()

    back = [('gave', 'stroke', 7), ('preset', 3, 7), ('scene', 1, 7), ('gave', 'memory', 0)]
    measuring()
    answer = say('HRLV 01')
    row('01: the preset and the scene of the beginning come back while it is silent, and the memory is given back', answer == ['HRLV 0 -1'] and p.events == back and p.stage() == 0, p.events)
    row('once is enough', say('HRLV 01') == ['HRLV 0 -1'] and p.events == back)
    measuring(3, 1)
    say('HRLV 01')
    row('nothing is loaded when the preset and the scene are those of the beginning', [e[:2] for e in p.events] == [('gave', 'stroke'), ('gave', 'memory')] and p.stage() == 0, p.events)
    measuring(3, 2)
    say('HRLV 01')
    row('another scene of the same preset: the preset comes back, and then its scene', p.events == back and p.stage() == 0, p.events)
    measuring(3, 2, (3, -1))
    say('HRLV 01')
    row('what the preset started with comes back without a scene', [e[:2] for e in p.events] == [('gave', 'stroke'), ('preset', 3), ('gave', 'memory')] and p.setting(G_SCENE) == -1, p.events)
    measuring()
    p.gone = True
    say('HRLV 01')
    p.gone = False
    row('a preset that cannot be loaded any more does not bring its scene', [e[0] for e in p.events] == ['gave', 'preset', 'gave'] and p.stage() == 0, p.events)
    measuring(start=(-1, -1), preset=-1, scene=-1)
    say('HRLV 01')
    row('a preset that is not stored stays', [e[0] for e in p.events] == ['gave', 'gave'] and p.setting(harness.G_PRESET) == -1, p.events)
    measuring()
    p.turns(397)
    early = list(p.events)
    p.turns(3)
    row('four seconds without a word end it', early == [] and p.events == back and p.stage() == 0, [early, p.events])
    measuring()
    for _ in range(8):
        p.turns(300)
        say('HRLV')
    row('a word keeps it', p.events == [] and p.stage() == 6, p.events)
    say('HRLV 01')
    p.memory(184)
    p.events.clear()
    p.turns(1000)
    row('REC and INJ by themselves are left alone', p.events == [] and p.state(S_MEMORY) != 0)
    say('REC free')
    # a footswitch, in both layouts
    for layout, name in ((0, 'factory'), (1, 'custom')):
        p.state(74, layout, 1)
        measuring()
        raw = p.mem.read(p.where['L01c1f180'] + 116, 1)[0]
        press = lambda level: p.run('hyperrig_transition', raw, level, 5000, 50_000)
        press(1)
        stopped, events = p.stage(), list(p.events)
        scan = lambda: [p.run('panel_inputs_switch_scan', 10, 0, 50_000) for _ in range(150)] if not layout else None
        p.events.clear()
        p.panel.calls.clear()
        kept = harness.RECORDED.copy()
        harness.RECORDED['preset_storage_available'] = 1
        scan()
        press(0)
        scan()
        harness.RECORDED.clear(), harness.RECORDED.update(kept)
        acted = [e for e in p.events if e[0] in ('preset', 'scene', 'transition')] + [c for c in p.panel.calls if c[0] in ('preset_loader_load', 'footswitch_events_preset_save', 'footswitch_events_reload_preset')]
        row(f'{name} layout: a press ends it, brings the preset back, and is nothing else, held or let go', stopped == 0 and events == back and acted == [], [stopped, events, acted])
        press(1), press(0)
        row(f'{name} layout: the next press is the footswitch again', [e[2] for e in p.events if e[0] == 'transition'] in ([1, 0], [1, 1, 0]) or layout, p.events)
    p.state(74, 0, 1)

    # the audio task's own instructions around the two places
    state, setting, calls = p.where[scenes.STATE], p.where['L01c1f180'], {}
    marks = {r: 0x1000 + r for r in range(4, 16)}
    for stage in range(8):
        p.state(S_STAGE, stage, 1)
        p.state(976, 0), p.state(52, 0, 1)
        p.mem.write(p.where['L01c3448c'], b'\0')
        registers = {**marks, 8: state, 9: BUFFER, 15: 0}
        called, _ = p.segment('L01c01fd6', 'L01c020f8', registers)
        calls[stage] = [c[:2] for c in called] + [all(p.cpu.R[r] == registers[r] for r in (4, 5, 8, 9, 10, 11, 12, 13, 14, 15))]
        registers = {**marks, 5: BUFFER, 8: state, 15: setting}
        called, _ = p.segment('L01c02862', 'L01c02902', registers)
        frame = struct.unpack('<64I', p.mem.read(FRAME, 256))
        calls[stage] += [c[0] if c[0] != 'hyperrig_level_output' else c for c in called] + [{i: v for i, v in enumerate(frame) if v != 0x7000 + i}, all(p.cpu.R[r] == registers[r] for r in (5, 8, 15))]
    p.state(S_STAGE, 0, 1)
    quiet = [True, 'storage_platform_clock', {}, True]
    loud = [('hyperrig_level_input', BUFFER), True, ('hyperrig_level_output', BUFFER, 0x7000 + 16), 'storage_platform_clock', {10: 0}, True]
    want = {**{k: quiet for k in range(5)}, 5: [('hyperrig_level_input', BUFFER)] + quiet, 6: loud, 7: loud}
    row('the audio task calls them in their stages only, with its registers kept, and the output gain of the block is 0 while it measures', calls == want, {k: c for k, c in calls.items() if c != want[k]})
    ticks = lambda steps: round(steps * CYCLES / TICK)
    idle = sum(p.segment(a, b, {8: state})[1] for a, b in (('L01c01fd6', 'Lhr_level_no_input'), ('L01c02862', 'Lhr_level_no_output')))
    spent = {'off': idle, 'record': record_steps, 'play': max(steps), 'measure_one_channel': mono_steps, 'measure_two_channels': stereo_steps}
    row('what it costs: four instructions a block when it is not used, at most 4,300 ticks while it measures two channels', idle == 4 and ticks(max(steps) + stereo_steps) < 4300 and ticks(record_steps) < 2000,
        {'instructions': spent, 'ticks': {k: ticks(v) for k, v in spent.items()}})

    # the gains of a stored preset
    gains = lambda preset, *values: 'HRLV 02' + bytes([preset] + [v & 0xFF for v in values]).hex()
    KEEP = 0x7F
    for many in (False, True):
        what = 'eight scenes' if many else 'three scenes'
        q = Meter(build)
        q.setting(harness.G_PRESET, -1)
        q.setting(G_SCENE, -1)
        q.wipe()
        q.add(2), q.add(8)
        for k in range(8 if many else 3):
            q.run('effect_parameter_lifecycle_parameter_commit', 0, 0, 3 + k)
            q.say(f'GAIN {k} {-k}')
            q.say(f'SNAPSAVE {k}')
            q.say(f'SNAPNAME {k} N{k}')
        q.setting(harness.G_PRESET, 0)
        q.stored = scenes.record(b'\5' + bytes(1423))
        q.say('PSAVE 0 Levels')
        before = q.written
        result, working, recs, names = q.load(before)
        q.written = None
        answer = q.say(gains(0, -8, -3, KEEP, 12, *[KEEP] * 5))
        after = q.written
        result2, working2, recs2, names2 = q.load(after) if after else (None,) * 4
        outs = lambda rs: [struct.unpack('b', r[5:6])[0] for r in rs if r[0]]
        same = lambda a, b: all(x[:5] + x[6:] == y[:5] + y[6:] for x, y in zip(a, b))
        good = answer == ['HRLV 0 -1'] and result2 == 0 and after[16:40] == before[16:40] and len(after) == len(before) and [i for i in range(len(working)) if working[i] != working2[i] and i < 300] == [5] and \
            struct.unpack('b', working2[5:6])[0] == -8 and outs(recs2)[:3] == [-3, -1, 12] and outs(recs2)[3:] == outs(recs)[3:] and same(recs, recs2) and names == names2 and \
            struct.unpack_from('<I', after, 8)[0] == zlib.crc32(after[40:])
        differ = [i for i in range(40, len(before)) if before[i] != after[i]] if after else None
        row(f'02 writes the output gains into a stored preset with {what}: three bytes, and the checksum', good and len(differ) == 3, [answer, outs(recs) if recs else None, outs(recs2) if recs2 else None, differ])
        q.written = None
        short = [q.say(x)[0] for x in ('HRLV 02', 'HRLV 0200', gains(0, *[1] * 8), gains(0, *[1] * 9)[:-1], gains(0, *[1] * 10), 'HRLV 027')]
        row(f'a line that is not whole is refused and writes nothing ({what})', q.written is None and all(x.startswith('HRLV 2 ') for x in short), short)
        q.say('HRLV 01')
        bad = [int(q.say(gains(32, *[1] * 9))[0].split()[1])]
        q.stored = b'\xff' * 2048
        bad.append(int(q.say(gains(0, *[1] * 9))[0].split()[1]))
        row(f'an empty place, or none, is refused ({what})', all(v < 0 for v in bad) and q.written is None, bad)
        q.stored = before
        q.say('PCOLOR 00ff00 save')
        colour = q.written
        row(f'the colour is changed as ever ({what})', bool(colour) and [i for i in range(40, len(before)) if before[i] != colour[i]] in ([50, 51], [50], [51]), colour and [i for i in range(40, len(before)) if before[i] != colour[i]])
    return rows, p.manifest


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        raise SystemExit(__doc__)
    rows, manifest = check(argv[0])
    print(json.dumps({'build': manifest['product'], 'area_sha256': manifest['area_sha256'], 'device_io': False, 'hardware_test': False, 'checks': rows, 'held': all(r['held'] for r in rows)}, indent=1))
    return 0 if all(r['held'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
