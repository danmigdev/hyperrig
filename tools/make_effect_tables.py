"""Write the numbers of the product effects (firmware/ultrarig/mini/product/effects_tables.h). Offline; needs nothing but Python.

All of them follow from what is written here: the coefficients of one-pole low-passes, and the low-pass of the reverse
delay, which keeps one sample of three. Nothing was measured on a device or taken from others' code. docs/EFFECT_PLUGINS.md says what
each effect does with them; tools/effects_reference.py is the same arithmetic in Python.

Usage, from the repository root:
    python -B tools/make_effect_tables.py [--check]
With --check nothing is written; the exit code is 1 when the file differs.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'firmware/ultrarig/mini/product/effects_tables.h'
FS = 48077.0                                # the rate the pedal runs at
POINTS = 11                                 # a knob of 0 to 100 has a table of eleven points, straight lines between them


def onepole(hz):
    """The part of the way that a one-pole low-pass goes with each sample, in 1/65536."""
    return round(65536 * (1 - math.exp(-2 * math.pi * hz / FS)))


def between(first, last):
    """Eleven values from first to last, each the same times the one before."""
    return [first * (last / first) ** (i / (POINTS - 1)) for i in range(POINTS)]


# The octaver: the low-passes of the two octaves below and of the one above, and how hard the fuzz is pushed. The makeup is what keeps
# the level of a signal a quarter of the full one, so a knob that adds fuzz does not add volume.
SUB_LOW = [onepole(hz) for hz in between(220.0, 2200.0)]
SUB_LOWER = [onepole(hz) for hz in between(130.0, 1100.0)]
UP_TONE = [onepole(hz) for hz in between(900.0, 9000.0)]
DRIVES = between(1.0, 80.0)
DRIVE = [round(256 * d) for d in DRIVES]


def soft(v):
    """The curve of the fuzz: straight in the middle, level at 1."""
    v = max(-1.5, min(1.5, v))
    return v - 4 / 27 * v ** 3


MAKEUP = [min(65535, round(65536 * soft(0.06) / soft(0.06 * d))) for d in DRIVES]

# The swell: how far below the full level the gate opens, in fours, and how much louder than the last quarter of a second an attack has to be.
SWELL_FLOOR = [round(8388608 / 4 * 10 ** (db / 20)) for db in (-36, -39, -42, -45, -48, -51, -54, -57, -60, -63, -66)]
SWELL_RATIO = [round(256 * 10 ** (db / 20)) for db in (6.0, 5.2, 4.4, 3.8, 3.2, 2.7, 2.4, 2.1, 1.9, 1.7, 1.5)]

# The reverse delay: one sample of three is kept.
KEEP, TAPS = 3, 24
CUT_HZ = 6900.0


def lowpass(n, cut):
    """A low-pass of n taps under a Hamming window, its sum 1."""
    out = []
    for i in range(n):
        t = i - (n - 1) / 2
        x = 2 * cut / FS
        ideal = x if t == 0 else math.sin(math.pi * x * t) / (math.pi * t)
        out.append(ideal * (0.54 - 0.46 * math.cos(2 * math.pi * (i + 0.5) / n)))
    total = sum(out)
    return [v / total for v in out]


FIR = [round(32768 * v) for v in lowpass(TAPS, CUT_HZ)]
FIR[TAPS // 2 - 1] += (32768 - sum(FIR)) // 2
FIR[TAPS // 2] = FIR[TAPS // 2 - 1]
# The way back: for each of the three samples, eight of the taps, three times as high and their sum 1 for each.
BACK = []
for phase in range(KEEP):
    row = [KEEP * FIR[phase + KEEP * k] for k in range(TAPS // KEEP)]
    row[TAPS // KEEP // 2 - (phase == 0)] += 32768 - sum(row)
    BACK.append(row)
DAMPING = [onepole(hz) for hz in between(700.0, 7000.0)]
FADE = 128                                  # kept samples, 8 ms


def rows(values, per=12):
    return ',\n'.join('    ' + ', '.join(str(v) for v in values[i:i + per]) for i in range(0, len(values), per))


def text():
    out = ['/* The numbers of the product effects. Made by tools/make_effect_tables.py, which says where they come from: do not edit by hand. */']
    for name, values in (('sub_low', SUB_LOW), ('sub_lower', SUB_LOWER), ('up_tone', UP_TONE), ('drive', DRIVE), ('makeup', MAKEUP),
                         ('swell_floor', SWELL_FLOOR), ('swell_ratio', SWELL_RATIO), ('damping', DAMPING)):
        out.append(f'#define {name.upper()}_VALUES \\\n' + rows(values).replace('\n', ' \\\n'))
    out.append(f'enum {{ KEEP = {KEEP}, TAPS = {TAPS}, FADE = {FADE} }};')
    out.append('#define FIR_VALUES \\\n' + rows(FIR[:TAPS // 2]))
    out.append('#define BACK_VALUES \\\n' + ', \\\n'.join('    { ' + ', '.join(str(v) for v in row) + ' }' for row in BACK))
    return '\n'.join(out) + '\n'


def main(argv=None):
    if (argv or sys.argv[1:]) == ['--check']:
        return 0 if OUTPUT.is_file() and OUTPUT.read_bytes() == text().encode('ascii') else 1
    OUTPUT.write_bytes(text().encode('ascii'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
