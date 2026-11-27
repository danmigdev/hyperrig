"""The product effects in Python, sample for sample what firmware/ultrarig/mini/product/effects.c and fx_*.c do. Offline.

Whole numbers only, as in the firmware: tools/check_mini_effects.py runs the compiled code in the simulator and wants the same samples.
With a WAV file it renders one, so that an effect can be listened to before it is on a pedal. That is no hardware or audio test.

Usage, from the repository root:
    python -B tools/effects_reference.py EFFECT IN.wav OUT.wav [parameter=value ...]
IN.wav is taken as one channel (the first) at the rate of the pedal, 48 kHz.
"""
from __future__ import annotations

import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import make_effect_tables as tables  # noqa: E402

CHUNK, GLIDE, LIMIT = 32, 256, (1 << 27) - 1
DRY, WET, OWN, SETTINGS = 0, 1, 2, 10
UNITY = 65536


def held(v, low, high):
    return low if v < low else high if v > high else v


def toward(v, n):
    """v / n as C divides: towards zero."""
    return v // n if v >= 0 else -(-v // n)


def knob(values, percent):
    """The value of a knob of 0 to 100: eleven points and straight lines between them."""
    i, rest = divmod(held(percent, 0, 100), 10)
    return values[i] + toward((values[i + 1] - values[i]) * rest, 10) if rest else values[i]


def decibels(db):
    """A gain, decibel by decibel."""
    v = UNITY
    for _ in range(abs(db)):
        v = (v * (73533 if db > 0 else 58409)) >> 16
    return v


class Octaver:
    """One and two octaves below, by turning over every second cycle of the sound, and one above, by turning over its lower half."""
    NAME, ROWS = 'octaver', [(0, 100, 70, 'down1_pct'), (0, 100, 0, 'down2_pct'), (0, 100, 0, 'up_pct'), (0, 100, 0, 'fuzz_pct'), (0, 100, 50, 'tono_pct'),
                             (0, 100, 100, 'limpio_pct'), (-12, 12, 0, 'nivel_db')]
    ONE, TWO, UP, DRIVE, LOW, LOWER, TONE, MAKEUP = range(OWN, OWN + 8)
    GLIDED = (1 << ONE) | (1 << TWO) | (1 << UP) | (1 << DRIVE) | (1 << LOW) | (1 << LOWER) | (1 << TONE) | (1 << MAKEUP)
    INPUT, UNIT, FLOOR, TURN, STEP = 1 << 24, 1 << 26, 21221, 16384, 512

    def __init__(self):
        self.start()

    def start(self):
        self.high = self.d1 = self.d2 = self.above = self.below = self.latch = self.b1 = self.b2 = self.p1 = self.p2 = self.q1 = self.q2 = self.mean = self.t1 = 0
        self.flip1 = self.flip2 = self.turn1 = self.turn2 = self.TURN

    def set(self, p):
        s, level = [0] * SETTINGS, decibels(p[6])
        s[DRY] = level * p[5] // 100
        s[WET] = level
        s[self.ONE] = p[0] * 1573              # 100 is 2.4 times
        s[self.TWO] = p[1] * 1966              # 3.0
        s[self.UP] = p[2] * 1311               # 2.0
        s[self.DRIVE], s[self.MAKEUP] = knob(tables.DRIVE, p[3]), knob(tables.MAKEUP, p[3])
        s[self.LOW], s[self.LOWER], s[self.TONE] = knob(tables.SUB_LOW, p[4]), knob(tables.SUB_LOWER, p[4]), knob(tables.UP_TONE, p[4])
        return s

    def run(self, s, x):
        one, two, up, drive, low, lower, tone, makeup = s[self.ONE:self.MAKEUP + 1]
        most = (self.UNIT + self.UNIT // 2) // drive * 256
        for i, v in enumerate(x):
            v = held(v, -self.INPUT, self.INPUT) << 3
            self.high += (v - self.high) >> 8
            v -= self.high
            # where a cycle begins: the low of the sound, over half of its last peaks and then under half of its last dips
            self.d1 += (v - self.d1) >> 5
            self.d2 += (self.d1 - self.d2) >> 5
            d = self.d2
            self.above -= self.above >> 11
            self.below -= self.below >> 11
            if d > self.above:
                self.above = d
            if -d > self.below:
                self.below = -d
            if not self.latch:
                if self.above > self.FLOOR and d > self.above >> 1:
                    self.latch = 1
                    self.flip1 = -self.flip1
                    if self.flip1 > 0:
                        self.flip2 = -self.flip2
            elif self.below > self.FLOOR and -d > self.below >> 1:
                self.latch = 0
            self.turn1 += held(self.flip1 - self.turn1, -self.STEP, self.STEP)
            self.turn2 += held(self.flip2 - self.turn2, -self.STEP, self.STEP)
            self.b1 += (v - self.b1) >> 4
            self.b2 += (self.b1 - self.b2) >> 3
            m = (self.b2 * self.turn1) >> 14
            self.p1 += ((m - self.p1) * low) >> 16
            self.p2 += ((self.p1 - self.p2) * low) >> 16
            m = (self.p2 * self.turn2) >> 14
            self.q1 += ((m - self.q1) * lower) >> 16
            self.q2 += ((self.q1 - self.q2) * lower) >> 16
            # the octave above, of the sound that the fuzz has pushed
            u = (held(self.b2, -most, most) * drive) >> 8
            c = (u * u) >> 26
            c = (c * u) >> 26
            u -= (c * 9709) >> 16
            if u < 0:
                u = -u
            self.mean += (u - self.mean) >> 9
            u = ((u - self.mean) * makeup) >> 15
            self.t1 += ((u - self.t1) * tone) >> 16
            x[i] = (self.p2 * one + self.q2 * two + self.t1 * up) >> 19


class Swell:
    """Every note grows out of nothing. The sound is four milliseconds late, so the gate is shut before an attack comes out."""
    NAME, ROWS = 'swell', [(20, 3000, 400, 'ataque_ms'), (0, 100, 50, 'sens_pct'), (0, 100, 100, 'prof_pct'), (-12, 12, 0, 'nivel_db')]
    RATE, RATIO, GATE, LEAST = range(OWN, OWN + 4)
    GLIDED = 1 << LEAST
    LINE, LATE, WHOLE, SHUT, WAIT = 256, 192, 1 << 30, 1 << 24, 2400

    def __init__(self):
        self.start()

    def start(self):
        self.line = [0] * self.LINE
        self.fast = self.slow = self.phase = self.wait = self.shutting = self.at = 0

    def set(self, p):
        s = [0] * SETTINGS
        s[WET] = decibels(p[3])
        s[self.RATE] = 22334212 // p[0]        # 2 ^ 30 / (48.077 ms)
        s[self.RATIO], s[self.GATE] = knob(tables.SWELL_RATIO, p[1]), knob(tables.SWELL_FLOOR, p[1]) * 4
        s[self.LEAST] = UNITY - p[2] * UNITY // 100
        return s

    def run(self, s, x):
        rate, ratio, gate, least = s[self.RATE:self.LEAST + 1]
        for i, v in enumerate(x):
            a = -v if v < 0 else v
            self.fast += (a - self.fast) >> 3 if a > self.fast else (a - self.fast) >> 10
            # an attack: over the gate, and louder than the sound has been
            if self.wait:
                self.wait -= 1
            elif self.fast > gate and self.fast * 256 > self.slow * ratio:
                self.shutting, self.wait = 1, self.WAIT
            self.slow += (self.fast - self.slow) >> 12 if self.fast < self.slow else (self.fast - self.slow) >> 8
            if self.shutting:
                self.phase -= self.SHUT
                if self.phase <= 0:
                    self.phase = self.shutting = 0
            elif self.fast > gate >> 1:
                self.phase += rate
                if self.phase > self.WHOLE:
                    self.phase = self.WHOLE
            else:
                self.phase -= self.phase >> 11
            g = (self.phase * self.phase) >> 44
            g = least + ((UNITY - least) * g >> 16)
            self.line[self.at & (self.LINE - 1)] = v
            x[i] = (self.line[(self.at - self.LATE) & (self.LINE - 1)] * g) >> 16
            self.at += 1


class Thirds:
    """One sample of three is kept, as sixteen bits: the low-pass before and the way back after (thirds.c)."""
    LINE, TAIL = 16384, 8

    def __init__(self):
        self.line = [0] * self.LINE
        self.start()

    def start(self):
        self.history = [0] * tables.TAPS
        self.wet = [0] * self.TAIL
        self.turn = self.written = self.known = 0

    def keep(self, v):
        self.line[self.written & (self.LINE - 1)] = held((v + 256) >> 9, -32768, 32767)
        self.written += 1
        if self.known < self.LINE:
            self.known += 1

    def run(self, s, x):
        for i, v in enumerate(x):
            self.history = self.history[1:] + [v]
            if self.turn == tables.KEEP - 1:
                total = sum(c * (self.history[k] + self.history[tables.TAPS - 1 - k]) for k, c in enumerate(tables.FIR[:tables.TAPS // 2]))
                self.wet = self.wet[1:] + [self.kept(total >> 15, s)]
            row = tables.BACK[(self.turn + 1) % tables.KEEP]
            x[i] = sum(c * self.wet[self.TAIL - 1 - k] for k, c in enumerate(row)) >> 15
            self.turn = (self.turn + 1) % tables.KEEP


class Reverse(Thirds):
    """A delay that plays each piece of the sound backwards."""
    NAME, ROWS = 'reverse', [(60, 500, 350, 'tiempo_ms'), (0, 90, 20, 'realim_pct'), (0, 100, 50, 'mezcla_pct'), (0, 100, 30, 'amort_pct'), (-12, 12, 0, 'nivel_db')]
    LENGTH, FEED, DAMP = range(OWN, OWN + 3)
    GLIDED = (1 << FEED) | (1 << DAMP)

    def start(self):
        super().start()
        self.damped = self.origin = self.at = self.valid = self.length = self.origin2 = self.valid2 = self.length2 = 0

    def set(self, p):
        s, level = [0] * SETTINGS, decibels(p[4])
        s[DRY] = level if p[2] <= 50 else level * (100 - p[2]) // 50
        s[WET] = level if p[2] >= 50 else level * p[2] // 50
        s[self.LENGTH] = p[0] * 16026 // 1000
        s[self.FEED] = p[1] * UNITY // 100
        s[self.DAMP] = knob(tables.DAMPING, 100 - p[3])
        return s

    def piece(self, origin, valid, t):
        return self.line[(origin - 1 - t) & (self.LINE - 1)] if t < valid else 0

    def kept(self, v, s):
        """One kept sample in, one out."""
        self.keep(v + ((self.damped * s[self.FEED]) >> 16))
        if not self.length:
            self.origin, self.valid, self.length, self.at = self.written, self.known, s[self.LENGTH], 0
        out, left = self.piece(self.origin, self.valid, self.at), self.length - self.at
        if left <= tables.FADE:
            if left == tables.FADE:
                self.origin2, self.valid2, self.length2 = self.written, self.known, s[self.LENGTH]
            new = self.piece(self.origin2, self.valid2, tables.FADE - left)
            out += ((new - out) * (tables.FADE - left)) >> 7
        self.at += 1
        if self.at == self.length:
            self.origin, self.valid, self.length, self.at = self.origin2, self.valid2, self.length2, tables.FADE
        self.damped += (((out << 9) - self.damped) * s[self.DAMP]) >> 16
        return self.damped


def signed16(phase):
    v = (phase >> 16) & 0xFFFF
    return v - 65536 if v >> 15 else v


def sine(phase):
    """A sine, nearly: 32768 either way, over a whole turn of 2 ^ 32."""
    t = signed16(phase)
    return (t * (32768 - abs(t))) >> 13


class Ensemble:
    """Three voices of the sound, a third of a cycle apart, each a little late and a little out of tune."""
    NAME, ROWS = 'ensemble', [(10, 200, 60, 'vel_chz'), (0, 100, 60, 'prof_pct'), (0, 100, 80, 'tono_pct'), (0, 100, 50, 'mezcla_pct'), (-12, 12, 0, 'nivel_db')]
    RATE, DEPTH, TONE = range(OWN, OWN + 3)
    GLIDED = (1 << RATE) | (1 << DEPTH) | (1 << TONE)
    LINE, THIRD, BASE, SHARE = 1024, 1431655765, 420 << 8, 37837

    def __init__(self):
        self.start()

    def start(self):
        self.line = [0] * self.LINE
        self.phase = self.fast = self.at = self.soft = 0
        self.place = [0] * 3

    def set(self, p):
        s, level = [0] * SETTINGS, decibels(p[4])
        s[DRY] = level * (250 - 2 * p[3] if p[3] <= 50 else 3 * (100 - p[3])) // 250
        s[WET] = level * (3 * p[3] if p[3] <= 50 else 2 * p[3] + 50) // 250
        s[self.RATE] = p[0] * 893              # 2 ^ 32 / 48077 / 100
        s[self.DEPTH] = p[1] * 492             # 192 samples in 1/256
        s[self.TONE] = knob(tables.UP_TONE, p[2])
        return s

    def run(self, s, x):
        rate, depth, tone = s[self.RATE:self.TONE + 1]
        self.phase = (self.phase + rate * len(x)) & 0xFFFFFFFF
        self.fast = (self.fast + 8 * rate * len(x)) & 0xFFFFFFFF
        step = []
        for voice in range(3):                 # to where each is after these samples, on a straight line
            p, q = (self.phase + voice * self.THIRD) & 0xFFFFFFFF, (self.fast + voice * self.THIRD) & 0xFFFFFFFF
            goal = (self.BASE + (((sine(p) + (sine(q) >> 3)) * depth) >> 15)) * 256
            self.place[voice] = self.place[voice] or goal
            step.append(toward(goal - self.place[voice], len(x)))
        for i, v in enumerate(x):
            self.line[self.at & (self.LINE - 1)] = v
            total = 0
            for voice in range(3):
                self.place[voice] += step[voice]
                place = self.place[voice]
                a, b = self.line[(self.at - (place >> 16)) & (self.LINE - 1)] >> 2, self.line[(self.at - (place >> 16) - 1) & (self.LINE - 1)] >> 2
                total += a + (((b - a) * (place & 65535)) >> 16)
            total = (total * self.SHARE) >> 14
            self.soft += ((total - self.soft) * tone) >> 16
            x[i] = self.soft
            self.at += 1


class Vintage(Thirds):
    """A delay whose repeats grow darker and softer, with a slow waver."""
    NAME, ROWS = 'vintage', [(40, 1000, 380, 'tiempo_ms'), (0, 100, 35, 'realim_pct'), (0, 100, 35, 'mezcla_pct'), (0, 100, 40, 'amort_pct'), (0, 100, 20, 'prof_pct'),
                             (-12, 12, 0, 'nivel_db')]
    TIME, FEED, DAMP, WAVER = range(OWN, OWN + 4)
    GLIDED = (1 << FEED) | (1 << DAMP) | (1 << WAVER)
    KNEE, SLOWLY, STEP = 3 << 21, 10, 214400

    def start(self):
        super().start()
        self.phase = self.time = self.dark = self.darker = 0

    def set(self, p):
        s, level = [0] * SETTINGS, decibels(p[5])
        s[DRY] = level if p[2] <= 50 else level * (100 - p[2]) // 50
        s[WET] = level if p[2] >= 50 else level * p[2] // 50
        s[self.TIME] = p[0] * 16026 // 1000
        s[self.FEED] = p[1] * UNITY // 100
        s[self.DAMP] = knob(tables.DAMPING, 100 - p[3])
        s[self.WAVER] = p[4] * 10
        return s

    def read(self, back):
        return self.line[(self.written - 1 - back) & (self.LINE - 1)] if back < self.known else 0

    def kept(self, v, s):
        """One kept sample in, one out."""
        self.phase = (self.phase + self.STEP) & 0xFFFFFFFF
        way = s[self.TIME] << 16
        self.time = self.time + ((way - self.time) >> self.SLOWLY) if self.time else way
        place = self.time + ((sine(self.phase) * s[self.WAVER]) >> 5)
        whole = place >> 16
        out = self.read(whole)
        out = (out << 9) + (((self.read(whole + 1) - out) * ((place >> 9) & 127)) << 2)
        self.dark += ((out - self.dark) * s[self.DAMP]) >> 16
        self.darker += ((self.dark - self.darker) * s[self.DAMP]) >> 16
        v += (self.darker * s[self.FEED]) >> 16
        a = abs(v)
        if a > self.KNEE:
            a = self.KNEE + ((a - self.KNEE) >> 2)
            v = -a if v < 0 else a
        self.keep(v)
        return self.darker


EFFECTS = {e.NAME: e for e in (Octaver, Swell, Reverse, Ensemble, Vintage)}


class Block:
    """An effect of the list in effects.c, with the frame around it: the settings that glide, the mix, the level."""

    def __init__(self, name, **parameters):
        self.effect = EFFECTS[name]()
        self.rows = self.effect.ROWS
        self.ready = False
        self.parameters = [r[2] for r in self.rows]
        self.set(**parameters)

    def set(self, **parameters):
        names = [r[3] for r in self.rows]
        for name, value in parameters.items():
            self.parameters[names.index(name)] = value
        kept = [held(v, r[0], r[1]) for v, r in zip(self.parameters, self.rows)]
        self.goal = self.effect.set(kept + [0] * (7 - len(kept)))

    def pause(self):
        """The block was off for a while."""
        self.ready = False

    def run(self, samples):
        if not self.ready:
            self.now, self.ready = list(self.goal), True
            self.effect.start()
        out = []
        for k in range(0, len(samples), CHUNK):
            source = [held(v, -LIMIT, LIMIT) for v in samples[k:k + CHUNK]]
            n = len(source)
            for j in range(OWN, SETTINGS):
                if self.effect.GLIDED >> j & 1:
                    step = toward((self.goal[j] - self.now[j]) * n, GLIDE)
                    self.now[j] = self.now[j] + step if step else self.goal[j]
                else:
                    self.now[j] = self.goal[j]
            x = list(source)
            self.effect.run(self.now, x)
            dry, wet = self.now[DRY], self.now[WET]
            by_dry, by_wet = toward(self.goal[DRY] - dry, GLIDE), toward(self.goal[WET] - wet, GLIDE)
            dry, wet = dry if by_dry else self.goal[DRY], wet if by_wet else self.goal[WET]
            for a, b in zip(source, x):
                dry += by_dry
                wet += by_wet
                out.append(held((a * dry + b * wet) >> 16, -LIMIT, LIMIT))
            self.now[DRY], self.now[WET] = dry, wet
        return out


def read(path):
    with wave.open(str(path), 'rb') as f:
        channels, width, frames = f.getnchannels(), f.getsampwidth(), f.getnframes()
        data = f.readframes(frames)
    step = channels * width
    if width not in (2, 3, 4):
        raise SystemExit('16, 24 or 32 bits')
    out = [int.from_bytes(data[i:i + width], 'little', signed=True) for i in range(0, len(data), step)]
    return [v << 8 for v in out] if width == 2 else out if width == 3 else [v >> 8 for v in out]


def write(path, samples):
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(3)
        f.setframerate(48000)
        f.writeframes(b''.join(struct.pack('<i', held(v, -8388608, 8388607))[:3] for v in samples))


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) < 3 or argv[0] not in EFFECTS:
        raise SystemExit(__doc__)
    block = Block(argv[0], **{a.split('=')[0]: int(a.split('=')[1]) for a in argv[3:]})
    write(argv[2], block.run(read(argv[1])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
