"""Write the numbers of the loudness meter (firmware/ultrarig/mini/product/loudness_tables.h). Offline; needs nothing but Python.

- the K weighting of Recommendation ITU-R BS.1770: its two filters are given there for 48 kHz; here they are the same filters at the
  rate of the pedal, by way of the bilinear transform, each with a first coefficient of 1 and what that leaves out in one factor;
- the half-band low-pass between a half and a quarter of the rate, for the strokes that are recorded and played back: a windowed sine.

Usage, from the repository root:
    python -B tools/make_loudness_tables.py [--check]
With --check nothing is written; the exit code is 1 when the file differs.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'firmware/ultrarig/mini/product/loudness_tables.h'
RATE = 48077.0                              # the rate the pedal runs at
GIVEN = 48000.0                             # the one BS.1770 gives its numbers for
SHELF = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
HIGH = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])
FULL = 1 << 26                              # full scale at the end of the chain
PAIRS, BETA, ONE = 6, 3.6, 1 << 15


def at_rate(filter_, rate=RATE):
    """The filter (b, a) of GIVEN at another rate: z1 = (1 + u) / (1 - u) with u = (rate / GIVEN) (1 - 1/z) / (1 + 1/z)."""
    k = rate / GIVEN
    plus, minus = (1 + k, 1 - k), (1 - k, 1 + k)        # 1 + u and 1 - u over (1 + 1/z), as polynomials of 1/z

    def product(p, q):
        return [p[0] * q[0], p[0] * q[1] + p[1] * q[0], p[1] * q[1]]

    def put(c):
        terms = [product(plus, plus), product(plus, minus), product(minus, minus)]
        return [sum(c[j] * terms[j][i] for j in range(3)) for i in range(3)]

    b, a = put(filter_[0]), put(filter_[1])
    return [v / a[0] for v in b], [v / a[0] for v in a]


def bessel(x):
    total = term = 1.0
    for n in range(1, 40):
        term *= (x / (2 * n)) ** 2
        total += term
    return total


def halfband():
    """What the sample between two others is made of: the weight of the nearest pair first. Whole numbers; with both ends they are ONE."""
    weights = []
    for k in range(PAIRS):
        t = k + 0.5
        sine = math.sin(math.pi * t) / (math.pi * t)
        weights.append(sine * bessel(BETA * math.sqrt(1 - (t / PAIRS) ** 2)) / bessel(BETA))
    total = 2 * sum(weights)
    out = [round(ONE * v / total) for v in weights]
    out[0] += ONE // 2 - sum(out)
    return out


def number(v):
    text = f'{v:.9g}'
    return text + ('f' if '.' in text or 'e' in text else '.0f')


def weighting():
    """The two filters with a first coefficient of 1, and the factor of the energy of samples that are FULL at full scale."""
    (b, a), (hb, ha) = at_rate(SHELF), at_rate(HIGH)
    return {'SHELF_B1': b[1] / b[0], 'SHELF_B2': b[2] / b[0], 'SHELF_A1': a[1], 'SHELF_A2': a[2], 'HIGH_A1': ha[1], 'HIGH_A2': ha[2],
            'ENERGY': (b[0] * hb[0] / FULL) ** 2}


def text():
    lines = ['/* The numbers of loudness.c. Made by tools/make_loudness_tables.py, which says where they come from: do not edit by hand. */']
    lines += [f'#define {n} {number(v)}' for n, v in weighting().items()]
    lines += [f'enum {{ PAIRS = {PAIRS} }};', f'TABLE static const int16_t halfband[PAIRS] = {{ {", ".join(map(str, halfband()))} }};', '']
    return '\n'.join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv not in ([], ['--check']):
        raise SystemExit(__doc__)
    if argv:
        return 0 if OUTPUT.is_file() and OUTPUT.read_bytes() == text().encode('ascii') else 1
    OUTPUT.write_bytes(text().encode('ascii'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
