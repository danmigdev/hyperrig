"""Write the numbers of the harmonizer block (firmware/ultrarig/mini/product/harmonizer_tables.h). Offline; needs nothing but Python.

Where they come from (docs/MINI_HARMONIZER.md): the filter is a windowed sinc, the curves are the equal temperament of twelve, the scales
are the usual ones; the limits and times were set with strings made by a sum of partials, and with the solos of GuitarSet (Xi, Bittner,
Pauwels, Ye and Bello, ISMIR 2018, https://zenodo.org/records/3371780, CC BY 4.0) and their notes. No recording is in HyperRig.

Usage, from the repository root:
    python -B tools/make_harmonizer_tables.py [--check]
With --check nothing is written; the exit code is 1 when the file differs.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'firmware/ultrarig/mini/product/harmonizer_tables.h'
FS = 48077.0                                # the rate the pedal runs at

# the scales, in semitones from the key; from FIXED on, the intervals that all notes get
SCALES = [('major', (0, 2, 4, 5, 7, 9, 11)), ('minor', (0, 2, 3, 5, 7, 8, 10)), ('dorian', (0, 2, 3, 5, 7, 9, 10)), ('phrygian', (0, 1, 3, 5, 7, 8, 10)),
          ('lydian', (0, 2, 4, 6, 7, 9, 11)), ('mixolydian', (0, 2, 4, 5, 7, 9, 10)), ('locrian', (0, 1, 3, 5, 6, 8, 10)),
          ('harmonic minor', (0, 2, 3, 5, 7, 8, 11)), ('melodic minor', (0, 2, 3, 5, 7, 9, 11)),
          ('fixed, major', (0, 2, 4, 5, 7, 9, 11)), ('fixed, minor', (0, 2, 3, 5, 7, 8, 10))]
FIXED = 9

# the listening
QUARTER_TAPS, QUARTER_CUT = 24, 0.8 / 8     # the low-pass before every fourth sample is taken, as a part of the rate
DEEP, SURE, KEEP, CHANGE = 0.10, 0.05, 0.25, 0.45       # how unlike itself a sound may be a period ago: a note, a certain one, one that goes on; and what is another
QUIET = 450                                 # of the squares of 32 slow samples, over 256: -79 dB under full scale
RISE = 4                                    # an attack: so many times the power of the last some 13 ms
ONCE = 28                                   # lags that the last 32 slow samples are enough for; up to four times it, twice as many, and above, four times as many
DOUBT = 8                                   # how long a note that was none is doubted, in listenings
PATIENCE = 18                               # 48 ms without a note: a chord
HELD = 80                                   # another note than the one before: after 53 ms, 0.1 s if it is out of tune or not of the scale, 0.2 s if both
EARLY = 12                                  # 32 ms: at first a note is only about where it will be
STILL_CENTS, NEARLY_CENTS = 50, 15          # so far from a note the interval stays its own; so near the next one it is already the next one's
DUCK_DB, CHORD_DB, LOUDNESS = -10.0, -4.0, 80


def sinc(x):
    return 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)


def quarter():
    n = QUARTER_TAPS
    h = [sinc(2 * QUARTER_CUT * (i - (n - 1) / 2)) * (0.42 - 0.5 * math.cos(2 * math.pi * (i + 1) / (n + 1)) + 0.08 * math.cos(4 * math.pi * (i + 1) / (n + 1)))
         for i in range(n)]
    h = [round(v / sum(h) * 32768) for v in h]
    rest = 32768 - sum(h)
    h[n // 2 - 1] += rest // 2
    h[n // 2] += rest - rest // 2
    return h


def reference():
    """The note of a lag of one 256th of a slow sample."""
    return round(69 * 256 + 3072 * math.log2(FS / 4 * 256 / 440))


def constants():
    return [('SCALES', len(SCALES)), ('FIXED', FIXED), ('REFERENCE', reference()), ('UP', round(65536 * 2 ** (1 / 12))), ('DOWN', round(65536 * 2 ** (-1 / 12))),
            ('LOUDER', round(32768 * 10 ** (1 / 20))), ('SOFTER', round(32768 * 10 ** (-1 / 20))), ('STILL', round(STILL_CENTS * 2.56)), ('NEARLY', round(NEARLY_CENTS * 2.56)),
            ('QUIET', QUIET), ('RISE', RISE), ('DEEP', round(DEEP * 256)), ('SURE', round(SURE * 256)), ('KEEP', round(KEEP * 256)), ('CHANGE', round(CHANGE * 256)),
            ('ONCE', ONCE), ('DOUBT', DOUBT), ('PATIENCE', PATIENCE), ('HELD', HELD), ('EARLY', EARLY),
            ('DUCK', round(256 * 10 ** (DUCK_DB / 20))), ('CHORD', round(256 * 10 ** (CHORD_DB / 20))), ('LOUDNESS', LOUDNESS)]


def text():
    out = ['/* The numbers of harmonizer.c. Made by tools/make_harmonizer_tables.py, which says where they come from: do not edit by hand. */\n']
    each = [f'{name} = {value}' for name, value in constants()]
    out.append('enum { ' + ',\n       '.join(', '.join(each[i:i + 8]) for i in range(0, len(each), 8)) + ' };\n\n')
    out.append('/* a bit for each note of a scale */\n')
    out.append('static const uint16_t scales[SCALES] = {\n' + ',\n'.join(f'    /* {name} */ 0x{sum(1 << n for n in scale):03x}' for name, scale in SCALES) + '\n};\n')
    out.append(f'TABLE static const int16_t quarter[{QUARTER_TAPS}] = {{ {", ".join(map(str, quarter()))} }};\n')
    return ''.join(out)


def main(argv=None):
    made = text()
    if '--check' in (argv or sys.argv[1:]):
        good = OUTPUT.is_file() and OUTPUT.read_bytes().decode('ascii') == made
        print('the tables are as made' if good else 'the tables differ')
        return 0 if good else 1
    OUTPUT.write_bytes(made.encode('ascii'))
    print(f'{OUTPUT.relative_to(ROOT).as_posix()}: {len(made)} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
