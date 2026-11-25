"""The harmonizer block (firmware/ultrarig/mini/product/harmonizer.c) in Python, sample by sample. Offline; needs nothing but Python.

It shares no code with the block: tools/check_mini_harmonizer.py runs the compiled one in the simulator and wants the same samples. What it
is made of and why is in docs/MINI_HARMONIZER.md.

Usage, from the repository root:
    python -B tools/harmonizer_model.py IN.wav OUT.wav [KEY SCALE VOICE1 VOICE2 BALANCE MIX LEVEL]
for one channel of 16, 24 or 32 bits at 48 kHz, which the pedal takes as 48,077 Hz.
"""
from __future__ import annotations

import sys
import wave
from operator import mul
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_harmonizer_tables as numbers  # noqa: E402

CHUNK, RING, BEFORE, AFTER, LOOK, BACK = 32, 2048, 24, 4, 32, 340
SHORTEST, LONGEST, WIDE, OCTAVE, HALF, ONE = 8, 168, 84, 3072, 128, 1 << 16
NEAR, FAR, MASK = 3 << 16, 1900 << 16, 0xFFFFFFFF
QUARTER, IS = numbers.quarter(), dict(numbers.constants())
DEFAULTS = (0, 0, 2, 0, 50, 50, 0)


def part(a, b):
    """a / b as C has it, towards zero."""
    return -(-a // b) if a < 0 else a // b


def signed(v):
    v &= MASK
    return v - (1 << 32) if v >> 31 else v


def within(v, lo, hi):
    return min(max(v, lo), hi)


def away(start, to):
    return (to - start + OCTAVE // 2) % OCTAVE - OCTAVE // 2


def note_of(lag):
    log = lag.bit_length() - 1
    lag <<= 31 - log
    for _ in range(12):
        lag *= lag
        high = lag >> 63
        log, lag = 2 * log + high, lag >> (31 + high)
    return IS['REFERENCE'] - ((3 * log + 2) >> 2)


def speed_of(interval):
    n, rest, v = interval >> 8, interval & 255, ONE
    for _ in range(abs(n)):
        v = v * IS['DOWN' if n < 0 else 'UP'] >> 16
    return v + (((v * IS['UP'] >> 16) - v) * rest >> 8)


def dip(lag, a, b, c):
    if a < b or c < b:
        return lag << 8
    bend, tilt = ((a - b) >> 1) + ((c - b) >> 1), (a >> 1) - (c >> 1)
    s = (bend | 1).bit_length() - 22
    if s > 0:
        bend, tilt = bend >> s, tilt >> s
    return (lag << 8) + (part(tilt * 128, bend) if bend else 0)


def climb(scale, start, steps):
    """Semitones from a note to the one of a scale that is so many steps away."""
    way, v = -1 if steps < 0 else 1, 0
    for _ in range(abs(steps)):
        v += way
        while (start + v) % 12 not in scale:
            v += way
    return v


def semitones(kind, here, steps):
    """From a note (counted from the key) to its harmony."""
    scale, way = numbers.SCALES[kind][1], -1 if steps < 0 else 1
    if kind >= numbers.FIXED:
        return way * climb(scale, 0, abs(steps))
    if abs(steps) == 7:
        return 12 * way
    v = climb(scale, here, steps)
    if here not in scale:
        w = climb(scale, here, steps + way)
        if abs(7 * w - 12 * steps) < abs(7 * v - 12 * steps):
            v = w
    return v


def between(p):
    """The weights of the four samples around a place, p 64ths after the second."""
    b, d, e = p + 64, p - 64, p - 128
    return [-(p * d * e // 96), b * d * e // 32, b * p * -e // 32, -(b * p * -d // 96)]


BETWEEN = [between(p) for p in range(64)]


class Settings:
    def __init__(self, parameters):
        key, kind, one, two, balance, mix, level = parameters
        key, kind = within(key, 0, 11), within(kind, 0, len(numbers.SCALES) - 1)
        self.key = key
        self.notes = {(n + key) % 12 for n in numbers.SCALES[kind][1]} if kind < numbers.FIXED else set(range(12))
        self.steps = [[semitones(kind, (n - key) % 12, within(v, -7, 7)) for n in range(12)] for v in (one, two)]
        loud = 16384
        for _ in range(abs(within(level, -12, 12))):
            loud = loud * IS['LOUDER' if level > 0 else 'SOFTER'] >> 15
        much = lambda v, percent: v * within(percent, 0, 50) // 50
        self.dry = much(loud, 100 - mix)
        wet = much(loud, mix) * numbers.LOUDNESS // 100
        self.wet = [much(wet, 100 - balance) if one else 0, much(wet, balance) if two else 0]

    def words(self):
        """As the firmware keeps them."""
        out = [sum(1 << n for n in self.notes) | self.key << 16, self.dry, *self.wet]
        for row in self.steps:
            for i in range(0, 12, 4):
                out.append(int.from_bytes(bytes(v & 255 for v in row[i:i + 4]), 'little'))
        return out


class Head:
    def __init__(self, at=0, step=0):
        self.at, self.step = at, step


class Voice:
    def __init__(self):
        self.a, self.b = Head(), Head()
        self.step = self.left = self.fade = self.jump = self.interval = 0


class Harmonizer:
    def __init__(self, parameters=DEFAULTS):
        self.settings = Settings(parameters)
        self.line = [0] * (BEFORE + RING + AFTER)
        self.slow = [0] * (BACK + LOOK)
        self.unlike, self.power, self.wide = [0] * (LONGEST + 2), [0] * (LONGEST + 2), [0] * WIDE
        self.voices, self.gain = [Voice(), Voice()], [0, 0, 0]
        self.now = self.at = self.turn = self.started = self.deep = self.soft = self.most = 0
        self.age = self.note = self.lag = self.pitch = self.mean = self.other = self.lost = self.waiting = 0
        self.since = self.doubt = self.chord = self.home = self.held = self.jump = 0

    # the listening

    def listen_anew(self):
        self.unlike, self.power = [0] * (LONGEST + 2), [0] * (LONGEST + 2)
        self.age = self.note = self.other = self.chord = self.since = self.doubt = 0
        self.waiting = 1

    def note_starts(self, lag, pitch):
        self.note, self.lag, self.pitch, self.mean = 1, lag, pitch, pitch
        self.other = self.waiting = self.chord = self.held = 0
        self.home = ((pitch + HALF) >> 8) % 12
        for steps, v in zip(self.settings.steps, self.voices):
            if abs(steps[self.home] * 256 - v.interval) > 16:
                v.interval, v.jump = steps[self.home] * 256, 1

    def note_goes_on(self):
        notes = self.settings.notes
        by, n = away(self.mean, self.pitch), (self.pitch + HALF) >> 8
        off, n = abs(self.pitch - n * 256), n % 12
        if self.note < numbers.EARLY:
            self.note += 1
            self.mean = self.pitch
            if off < 100:
                self.home = n
        else:
            self.mean = (self.mean + OCTAVE + (by >> 2 if abs(by) > HALF else (by + 8) >> 4)) % OCTAVE
            k = ((self.mean + HALF) >> 8) % 12
            if k == self.home:
                self.held = 0
            else:
                self.held += (2 if n == k and off < 77 else 1) << (k in notes)
                if self.held > numbers.HELD:
                    self.held, self.home = 0, k
        while True:
            off = away(self.home * 256, self.mean)
            way = -1 if off < 0 else 1
            gap = next((g for g in range(1, 12) if (self.home + way * g) % 12 in notes), 12)
            following, span = (self.home + way * gap) % 12, gap * 256 - IS['NEARLY']
            if abs(off) < span:
                break
            self.home = following
        x = max(0, abs(off) - IS['STILL'])
        for steps, v, gain in zip(self.settings.steps, self.voices, self.gain):
            goal = steps[self.home] * 256
            goal += part((steps[following] * 256 - goal) * x, span - IS['STILL'])
            v.interval = v.interval + ((goal - v.interval + 4) >> 3) if gain else goal

    def listen_wide(self):
        mine, w = self.slow[BACK:BACK + LOOK:2], self.wide
        here, best = sum(map(mul, mine, mine)), 1
        for i in range(WIDE):
            place = BACK - (LONGEST + 2 + 2 * i)
            then = self.slow[place:place + LOOK:2]
            w[i] += ((here + sum(map(mul, then, then)) - 2 * sum(map(mul, mine, then))) >> 8) - (w[i] >> 3)
            if self.age < 11:
                w[i] = 0
            if 0 < i < WIDE - 1 and w[i] < w[best]:
                best = i
        if self.age >= 11:
            self.jump = (((LONGEST + 2) << 8) + 2 * dip(best, *w[best - 1:best + 2])) << 10

    def listen(self):
        u, p, mine = self.unlike, self.power, self.slow[BACK:]
        here, least, level, mark = sum(map(mul, mine, mine)), MASK, 0, self.lag >> 8
        loud = here >> 8
        self.age = min(self.age + 1, 100)
        end = LOOK * self.age if self.age < 6 else LONGEST + 1
        for lag in range(SHORTEST - 1, end + 1):
            then = self.slow[BACK - lag:BACK - lag + LOOK]
            both = here + sum(map(mul, then, then))
            high, low = both >> 8, (both - 2 * sum(map(mul, mine, then))) >> 8
            if mark <= lag <= mark + 1:
                least, level = min(least, low), high
            k = (lag > numbers.ONCE) + (lag > 4 * numbers.ONCE)
            p[lag] += high - (p[lag] >> k)
            u[lag] += low - (u[lag] >> k)
        if self.age > 3 and loud > numbers.QUIET and loud // numbers.RISE > self.most:
            self.listen_anew()
        elif self.age > 2 and loud > numbers.QUIET and self.note and level:
            level = max(level, p[mark] >> ((mark > numbers.ONCE) + (mark > 4 * numbers.ONCE)))
            if least > (level >> 8) * IS['CHANGE']:
                if self.note > 6:
                    self.listen_anew()
                else:
                    self.note = self.other = 0
                    self.waiting = self.since
                    self.doubt += numbers.DOUBT
        u, p = self.unlike, self.power
        self.most = max(loud, numbers.QUIET, self.most - (self.most >> 3))
        self.since += 1
        self.doubt = max(0, self.doubt - 1)
        top, lag, sure, kept = min(28 * self.age, LONGEST), 0, False, 0
        if loud <= numbers.QUIET:
            self.note = self.waiting = top = 0
        mid = (self.lag + 128) >> 8
        for i in range(SHORTEST, top):
            if u[i] >= u[i - 1] or u[i] > u[i + 1]:
                continue
            if u[i] < (p[i] >> 8) * IS['DEEP']:
                lag, sure = i, u[i] < (p[i] >> 8) * IS['SURE']
                break
            if self.note and abs(i - mid) <= 2 and u[i] < (p[i] >> 8) * IS['KEEP']:
                kept = i
        lag = lag or kept
        if lag:
            place = dip(lag, *u[lag - 1:lag + 2])
            pitch = note_of(place)
            again = self.other and abs(away(self.other, pitch)) < HALF
            self.lost = 0
            if self.note and abs(away(self.pitch, pitch)) < HALF:
                self.pitch, self.lag, self.other = pitch, place, 0
            elif (again and sure) if self.doubt else (again or sure and not self.note):
                self.note_starts(place, pitch)
            else:
                self.other = pitch
        else:
            self.other = 0
            self.lost += 1
            if self.lost > 6:
                self.note = 0
        if self.waiting:
            self.waiting += 1
            if self.waiting > numbers.PATIENCE:
                self.waiting, self.chord = 0, 1
        if self.note:
            self.note_goes_on()
            n = (72 * 256 + self.lag - 1) // self.lag
            while ((n * self.lag + 128) >> 8) + 2 >= end and n > 1:
                n -= 1
            mid = (n * self.lag + 128) >> 8
            near = [i for i in range(mid - 2, mid + 3) if SHORTEST <= i < end]
            if near:
                best = min(near, key=lambda i: u[i])
                self.jump = dip(best, *u[best - 1:best + 2]) << 10
        else:
            self.listen_wide()
        for v in self.voices:
            v.step = speed_of(v.interval)
        self.slow = self.slow[LOOK:] + [0] * LOOK

    # the sound

    def take(self, samples):
        line, at = self.line, self.at
        line[BEFORE + at:BEFORE + at + CHUNK] = samples
        if at == 0:
            line[BEFORE + RING:] = line[BEFORE:BEFORE + AFTER]
        if at == RING - CHUNK:
            line[:BEFORE] = line[RING:RING + BEFORE]
        for i in range(CHUNK // 4):
            start = BEFORE + at + 4 * i + 3 - 23
            v = (sum(map(mul, QUARTER, line[start:start + 24])) >> 15) - (self.deep >> 6)
            self.deep += v
            self.soft += ((v - self.soft) * 3) >> 3
            self.slow[BACK + self.turn * (CHUNK // 4) + i] = within(self.soft >> 4, -32767, 32767)

    @staticmethod
    def nearest(step):
        return NEAR + max(0, step - ONE) * CHUNK

    def read_line(self, head):
        at, out = head.at, []
        if signed(self.now - at) < self.nearest(head.step):
            at = self.now - self.nearest(head.step)
        for _ in range(CHUNK):
            x = BEFORE - 1 + ((at >> 16) & (RING - 1))
            out.append(sum(map(mul, BETWEEN[(at >> 10) & 63], self.line[x:x + 4])) >> 14)
            at += head.step
        head.at = at & MASK
        return out

    def sing(self, v):
        if not v.left:
            drift, late = v.step - ONE, signed(self.now - v.a.at)
            v.b.step, v.fade = v.step, 7
            if v.jump or late > FAR:
                v.jump, v.left = 0, 4
                v.b.at = (self.now - self.nearest(v.step) - max(0, drift) * 4 * CHUNK) & MASK
            else:
                v.a.step = v.step
                v.fade = 7 if self.note else 8
                if drift > 0 and late - drift * CHUNK < NEAR + (drift << v.fade) or drift < 0 and late - self.jump > NEAR:
                    v.left = 1 << (v.fade - 5)
                    v.b.at = (v.a.at + (-self.jump if drift > 0 else self.jump)) & MASK
        out = self.read_line(v.a)
        if v.left:
            more = self.read_line(v.b)
            w = (1 << v.fade) - v.left * CHUNK
            out = [a + ((((b - a) >> 2) * (w + i)) >> (v.fade - 2)) for i, (a, b) in enumerate(zip(out, more))]
            v.left -= 1
            if not v.left:
                v.a = Head(v.b.at, v.b.step)
        return out

    def run(self, samples):
        """The sound of some samples, 32 or a multiple of it."""
        s, out = self.settings, []
        if not self.started:
            self.started = 1
            self.listen_anew()
            self.jump = 288 << 16
            self.gain = [0, 0, s.dry]
            for steps, v in zip(s.steps, self.voices):
                v.a.step, v.jump, v.left = ONE, 1, 0
                v.interval = steps[s.key] * 256
                v.step = speed_of(v.interval)
        for start in range(0, len(samples) - CHUNK + 1, CHUNK):
            chunk = samples[start:start + CHUNK]
            self.take(chunk)
            self.turn += 1
            if self.turn == 4:
                self.listen()
                self.turn = 0
            sounds, gains, slopes = [], list(self.gain), []
            for k, goal in enumerate([*s.wet, s.dry]):
                if k < 2 and (self.waiting or self.chord):
                    goal = (goal * IS['DUCK' if self.waiting else 'CHORD']) >> 8
                slopes.append((goal - gains[k]) >> 6)
                self.gain[k] = goal if abs(goal - gains[k]) < 64 else gains[k] + slopes[k] * CHUNK
                if k < 2:
                    if gains[k] or self.gain[k]:
                        sounds.append(self.sing(self.voices[k]))
                    else:
                        self.voices[k].jump = 1
                        sounds.append([0] * CHUNK)
            for i, x in enumerate(chunk):
                v = (x * (gains[2] + slopes[2] * i) + sounds[0][i] * (gains[0] + slopes[0] * i) + sounds[1][i] * (gains[1] + slopes[1] * i)) >> 14
                w = abs(v) - 6291456
                if w > 0:
                    w = 8388607 if w >= 4194304 else 6291456 + w - ((w * w) >> 23)
                    v = -w if v < 0 else w
                out.append(v)
            self.now = (self.now + (CHUNK << 16)) & MASK
            self.at = (self.at + CHUNK) & (RING - 1)
        return out


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) not in (2, 9):
        raise SystemExit(__doc__)
    with wave.open(argv[0], 'rb') as f:
        width, raw = f.getsampwidth(), f.readframes(f.getnframes())
        if f.getnchannels() != 1 or width not in (2, 3, 4):
            raise SystemExit('one channel of 16, 24 or 32 bits')
        rate = f.getframerate()
    x = [int.from_bytes(raw[i:i + width], 'little', signed=True) for i in range(0, len(raw), width)]
    x = [v << 8 if width == 2 else v if width == 3 else v >> 8 for v in x]
    block = Harmonizer(tuple(int(v) for v in argv[2:]) or DEFAULTS)
    out = block.run(x[:len(x) // CHUNK * CHUNK])
    with wave.open(argv[1], 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(3)
        f.setframerate(rate)
        f.writeframes(b''.join(v.to_bytes(3, 'little', signed=True) for v in out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
