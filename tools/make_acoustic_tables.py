"""Write the numbers of the acoustic block (firmware/ultrarig/mini/product/acoustic_tables.h). Offline; needs nothing but Python.

Where they come from (docs/MINI_ACOUSTIC.md):
- the resonances of the body and the tone were fitted to the relation between a pickup on the strings and a microphone in front of an
  acoustic guitar, both recorded at once in GuitarSet (Xi, Bittner, Pauwels, Ye and Bello, ISMIR 2018, https://zenodo.org/records/3371780,
  CC BY 4.0): 72 excerpts of 6 players. What is here are the fitted numbers; no recording is in HyperRig;
- the fall of the notes was set to the slopes measured there, against those of an electric guitar recorded directly in Guitar-TECHS
  (https://zenodo.org/records/14963133, CC BY 4.0);
- the octave is every band's phase doubled (a known method of polyphonic octave pedals, written here anew): the bands follow the width
  of the bands of hearing, and each is turned back by its own delay so that neighbours add up.

Usage, from the repository root:
    python -B tools/make_acoustic_tables.py [--check]
With --check nothing is written; the exit code is 1 when the file differs.
"""
from __future__ import annotations

import cmath
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'firmware/ultrarig/mini/product/acoustic_tables.h'
FS = 48077.0                                # the rate the pedal runs at

# resonances: hertz, Q, and how much of the resonance is added to the sound
MODES = [(108.1, 16.00, 3.563), (195.8, 9.16, 3.208), (306.4, 11.22, 0.437), (370.3, 6.16, 0.445), (491.2, 4.43, 0.460), (480.0, 0.50, -0.850), (1106.9, 4.97, 0.591), (1781.4, 16.00, 0.074)]
SHELF_HZ, END_HZ, TOP, LEVEL_DB, HIGHPASS_HZ = 5664.8, 18000.0, 7.000, -0.12, 50.0

# the bands of the notes: where they part, and how each is made to fall
SPLIT_LOW, SPLIT_HIGH = 640.0, 2600.0
RISE_MS, FALL_MS, FORGET_DB_S = (2.5, 1.2, 0.6), (30.0, 14.0, 8.0), (4.0, 4.0, 4.0)
SHAPE, FLOOR_DB = (1.5, 0.5, 1.9), (14.0, 10.0, 28.0)
CHUNK = 16

# 12 strings
BANDS, LOWEST, HIGHEST, WIDTH, LEAST_HZ = 37, 72.0, 1900.0, 0.66, 17.0
TAPS, OCTAVE_TAPS = 28, 6
OCTAVE, SECOND, DETUNE_CENTS, NEAR_MS, SPAN_MS, SHARP_HZ = 0.8, 0.8, 6.0, 0.4, 5.0, 0.7
THIN_HZ = 300.0                             # under it there is no second string, only the octave
BRIGHTER, SOFTER = 1.5, 0.82                # what 12 strings have more of the top, and less in all
ECHOES = (113, 233, 401)


def biquad(kind, hz, q=math.sqrt(0.5)):
    w = 2 * math.pi * hz / FS
    al, c = math.sin(w) / (2 * q), math.cos(w)
    if kind == 'low':
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]
    elif kind == 'high':
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    else:
        b = [al, 0.0, -al]
    a0 = 1 + al
    return [v / a0 for v in b] + [-2 * c / a0, (1 - al) / a0]


def lowpass_taps(n, cut):
    """A low-pass of n taps, windowed (Kaiser-like by a raised cosine), gain 1. cut is a part of the rate."""
    out = []
    for i in range(n):
        x = i - (n - 1) / 2
        s = 2 * cut if x == 0 else math.sin(2 * math.pi * cut * x) / (math.pi * x)
        out.append(s * (0.42 - 0.5 * math.cos(2 * math.pi * (i + 0.5) / n) + 0.08 * math.cos(4 * math.pi * (i + 0.5) / n)))
    total = sum(out)
    return [v / total for v in out]


def bands():
    """Rows of the octave's bands at a quarter of the rate: pole (real, imaginary), gain of a stage, and the turn of the doubled phase."""
    fs = FS / 4
    erb = lambda f: 21.4 * math.log10(1 + 0.00437 * f)
    inverse = lambda e: (10 ** (e / 21.4) - 1) / 0.00437
    lo, hi = erb(LOWEST), erb(HIGHEST)
    centres = [inverse(lo + (hi - lo) * k / (BANDS - 1)) for k in range(BANDS)]
    poles, gains = [], []
    for k, f in enumerate(centres):
        space = (centres[min(k + 1, BANDS - 1)] - centres[max(k - 1, 0)]) / (2 if 0 < k < BANDS - 1 else 1)
        r = math.exp(-2 * math.pi * max(space * WIDTH, LEAST_HZ) / fs)      # of one stage: half the band, as a pole counts it
        poles.append(r * cmath.exp(2j * math.pi * f / fs))
        gains.append(1 - r)

    def response(k, f):                                    # of the two stages
        return (gains[k] / (1 - poles[k] * cmath.exp(-2j * math.pi * f / fs))) ** 2

    def phase(k, f):
        return 2 * cmath.phase(gains[k] / (1 - poles[k] * cmath.exp(-2j * math.pi * f / fs)))

    turns = [0.0]                                          # each band agrees with the one before where the two meet
    for k in range(1, BANDS):
        mid = math.sqrt(centres[k - 1] * centres[k])
        turns.append(turns[-1] + 2 * phase(k, mid) - 2 * phase(k - 1, mid))
    def heard(f):                                          # of a sine: how much comes out
        return abs(sum(response(k, f) ** 2 / abs(response(k, f)) * cmath.exp(-1j * turns[k]) for k in range(BANDS))) / 2

    # a band counts for less where many share a place, so that a sine is as loud wherever it is: of the sines around it
    around = [sum(heard(f * 2 ** (n / 24)) for n in range(-4, 5)) / 9 for f in (min(max(c, 90.0), 1500.0) for c in centres)]
    rows = []
    for k, f in enumerate(centres):
        # what is heard of the octave of a band: all of a low string, less of what only thin strings have
        g = OCTAVE / around[k] * (1.0 if f < 420 else (420 / f) ** 0.7)
        g *= gains[k] ** 2                                 # of the two stages, which have none in the code
        rows.append([poles[k].real, poles[k].imag, 2 * g * math.cos(turns[k]), 4 * g * math.sin(turns[k])])    # 2: the root of the sum over the four of a chunk
    return rows


def number(v):
    return f'{v:.9g}f' if ('.' in f'{v:.9g}' or 'e' in f'{v:.9g}') else f'{v:.9g}.0f'


def table(name, rows, width=None):
    if isinstance(rows[0], (list, tuple)):
        inner = ',\n'.join('    { ' + ', '.join(number(v) for v in r) + ' }' for r in rows)
        return f'TABLE static const float {name}[{len(rows)}][{len(rows[0])}] = {{\n{inner}\n}};\n'
    return f'TABLE static const float {name}[{len(rows)}] = {{ ' + ', '.join(number(v) for v in rows) + ' };\n'


def text():
    per_chunk = CHUNK / FS
    out = ['/* The numbers of acoustic.c. Made by tools/make_acoustic_tables.py, which says where they come from: do not edit by hand. */\n']
    out.append(f'enum {{ BANDS = {BANDS}, FIR_TAPS = {TAPS}, OCTAVE_TAPS = {OCTAVE_TAPS}, MODES = {len(MODES)},\n'
               f'       E0 = {ECHOES[0]}, E1 = {ECHOES[1]}, E2 = {ECHOES[2]} }};\n')
    for name, value in (('SECOND', SECOND), ('THIN', 1 - math.exp(-2 * math.pi * THIN_HZ / FS)), ('BRIGHTER', BRIGHTER), ('TURN_C', math.cos(2 * math.pi * SHARP_HZ * CHUNK / FS)), ('TURN_S', math.sin(2 * math.pi * SHARP_HZ * CHUNK / FS)), ('SOFTER', SOFTER), ('DETUNE', 2 ** (DETUNE_CENTS / 1200) - 1), ('NEAR', NEAR_MS * FS / 1000), ('SPAN', SPAN_MS * FS / 1000),
                        ('SHELF', 1 - math.exp(-2 * math.pi * SHELF_HZ / FS)), ('ENDS', 1 - math.exp(-2 * math.pi * END_HZ / FS)), ('DEEP', 1 - math.exp(-2 * math.pi * HIGHPASS_HZ / FS)),
                        ('LOW', 1 - math.exp(-2 * math.pi * SPLIT_LOW / FS)), ('HIGH', 1 - math.exp(-2 * math.pi * SPLIT_HIGH / FS)), ('TOP', TOP), ('LEVEL', 10 ** (LEVEL_DB / 20))):
        out.append(f'#define {name} {number(value)}\n')
    out.append('#define LEVELS ' + ', '.join(number(10 ** (d / 20)) for d in range(-12, 13)) + '\n\n')
    fir = lowpass_taps(TAPS, 0.5 / 4 * 0.86)
    out.append(table('fir', fir[:TAPS // 2]))                     # the same from both ends
    back = lowpass_taps(OCTAVE_TAPS * 4, 0.5 / 4 * 0.9)
    # sample n of a group of 4 uses the taps n, n+4, ... on the slow samples from the newest back; here the oldest first
    out.append(table('back', [[4 * back[4 * (OCTAVE_TAPS - 1 - k) + n] for k in range(OCTAVE_TAPS)] for n in range(4)]))
    out.append('/* the pole, and the turn of the doubled phase (the sine twice) */\n')
    out.append(table('band', bands()))
    out.append(table('rise', [1 - math.exp(-per_chunk / (v / 1000)) for v in RISE_MS]))
    out.append(table('fall', [1 - math.exp(-per_chunk / (v / 1000)) for v in FALL_MS]))
    out.append(table('forget', [10 ** (-v * per_chunk / 10) for v in FORGET_DB_S]))
    out.append(table('shape', list(SHAPE)))
    out.append(table('floor_of', [v / (10 * math.log10(2)) for v in FLOOR_DB]))
    rows = []
    for hz, q, k in MODES:
        b = biquad('band', hz, q)
        rows.append([b[0] * k, b[3], b[4]])
    out.append('/* how much of a resonance is added, and its two poles */\n')
    out.append(table('mode', rows))
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
