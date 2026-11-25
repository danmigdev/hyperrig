"""The measure of loudness: its numbers, and the editor's arithmetic against a reference in Python. What the firmware does is in
tools/check_mini_loudness.py, and the window in tools/check_mini_dev_editor.py."""
import json
import math
import random
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_loudness as check  # noqa: E402
import make_loudness_tables as tables  # noqa: E402

CODE = (ROOT / 'firmware/ultrarig/mini/product/loudness.c').read_text(encoding='ascii')
EDITOR = (ROOT / 'app/mini/product-loudness.js').read_text(encoding='utf-8')
WINDOW = (ROOT / 'app/mini/product-loudness-ui.js').read_text(encoding='utf-8')
LOW = check.RATE / 4


def node(script, payload):
    """What the script returns, with the editor's numbers as L and the payload as d."""
    program = ('const d = JSON.parse(require("fs").readFileSync(0, "utf8")); require("vm").runInThisContext(d.code); const L = globalThis.HyperRigLoudness; '
               f'console.log(JSON.stringify((() => {{ {script} }})()));')
    done = subprocess.run(['node', '-e', program], input=json.dumps({'code': EDITOR, **payload}), capture_output=True, text=True, encoding='utf-8', timeout=60)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


def chain(kind, x):
    if kind == 'clean':
        return [0.7 * v for v in x]
    if kind == 'clipped':
        return [max(-0.22, min(0.28, 40 * v)) for v in x]
    level, out = 0.0, []
    for v in x:
        level = max(abs(v), level * 0.9995)
        out.append(v * (0.02 + level) ** -0.7 * 0.12)
    return out


class Numbers(unittest.TestCase):
    def test_the_tables_are_as_made(self):
        self.assertEqual(tables.OUTPUT.read_bytes().decode('ascii'), tables.text())

    def test_the_weighting_is_that_of_bs1770(self):
        """Within a thousandth of a decibel of the filters the Recommendation gives for 48 kHz, up to 20 kHz; and 997 Hz is -3.01 LUFS."""
        def size(filter_, hertz, rate):
            z = complex(math.cos(2 * math.pi * hertz / rate), -math.sin(2 * math.pi * hertz / rate))
            (b, a) = filter_
            return abs((b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z))
        for hertz in (25, 38, 82, 110, 440, 997, 1682, 3000, 5000, 10000, 18000):
            given = size(tables.SHELF, hertz, 48000) * size(tables.HIGH, hertz, 48000)
            here = size(tables.at_rate(tables.SHELF), hertz, tables.RATE) * size(tables.at_rate(tables.HIGH), hertz, tables.RATE)
            self.assertLess(abs(20 * math.log10(here / given)), 1e-3, hertz)
        sine = [math.sin(2 * math.pi * 997 * i / check.RATE) for i in range(check.RATE)]
        self.assertAlmostEqual(check.lufs(sum(w * w for w in check.weighted(sine)[4000:]) / (check.RATE - 4000)), -3.01, delta=0.01)

    def test_the_half_band_passes_a_guitar(self):
        half = tables.halfband()
        self.assertEqual(sum(half), tables.ONE // 2)
        for hertz, least, most in ((200, -0.1, 0.1), (2000, -0.1, 0.1), (4500, -0.2, 0.2), (8000, -200, -40), (11000, -200, -40)):
            size = 0.5 + sum(v / tables.ONE * math.cos(2 * math.pi * hertz * (2 * k + 1) / (tables.RATE / 2)) for k, v in enumerate(half))
            self.assertTrue(least < 20 * math.log10(abs(size) + 1e-9) < most, hertz)

    def test_the_editor_and_the_firmware_have_the_same(self):
        for name, value in (('HEAD', 32), ('RING', 1024), ('LARGEST', 30000), ('LAST_STEP', 87), ('KEEP', 127), ('RECORD', 5)):
            self.assertEqual(int(re.search(rf'\b{name} = (\d+)', CODE).group(1)), value)
        self.assertIn('enum { NOTHING, END, GAINS, RECORD = 5, MEASURE, SILENT }', CODE)
        self.assertIn('const SET = 2, RECORD = 5, MEASURE = 6, HEAD = 32, RING = 1024, RECORDING = HEAD + RING + 86, MEASURING = HEAD + 152;', WINDOW)
        self.assertEqual(4 * tables.PAIRS - 2 + 2 * 32, 86)                     # what the recording needs behind its ring
        self.assertIn('steps[8] = { 16, 17, 19, 21, 23, 25, 27, 29 }', CODE)
        self.assertIn('moves[8] = { -1, -1, -1, -1, 2, 4, 6, 8 }', CODE)
        seen = node('return [L.STROKE, L.RATE, L.FULL, L.slices(2), L.slices(3), L.PLAYED, L.bytesOf("0123456789")];', {})
        self.assertEqual(seen, [5632, tables.RATE, tables.FULL, 108, 152, 44, '1032547698'])
        self.assertEqual(seen[0] % 128, 0)

    def test_nothing_of_the_audio_is_in_the_flash(self):
        """The functions that run for a block of sound, and their numbers, are in the RAM."""
        for name in ('step_on', 'half', 'weigh', 'hyperrig_level_input', 'hyperrig_level_output'):
            self.assertRegex(CODE, rf'\nSOUND (?:__attribute__\(\(noinline\)\) )?(?:static )?[a-z0-9_ ]+[ *]{name}\(')
        for name in ('steps', 'moves'):
            self.assertRegex(CODE, rf'\nTABLE static const \w+ {name}\[')
        self.assertIn('TABLE static const int16_t halfband', tables.text())


class Arithmetic(unittest.TestCase):
    def test_the_codes_are_those_of_the_reference(self):
        rng = random.Random(4)
        x = [0.4 * math.sin(i / 9) * math.exp(-i / 900) + 0.02 * rng.uniform(-1, 1) for i in range(2000)] + [1.5, -1.5] * 20
        seen = node('const c = L.encode(d.x); return [Array.from(c), Array.from(L.decode(c), v => Math.round(v * 32768))];', {'x': x})
        codes = check.encoded(max(-32768, min(32767, math.floor(v * 32768 + 0.5))) for v in x)
        self.assertEqual(seen, [codes, check.decoded(codes)])

    def test_the_loudest_400_ms_are_those_of_the_reference(self):
        """Of a clean, a compressed and a clipped sound: from slices as the pedal makes them, within 0.05 LU of BS.1770 on every sample."""
        stroke = check.pluck(110.0, 0.4687, 0.3, seed=3)
        x = [0.0] * (4 * 512) + stroke + [0.0] * (4 * 512)
        x = x[:len(x) // 512 * 512]
        for kind in ('clean', 'compressed', 'clipped'):
            y = chain(kind, x)
            w = check.weighted(y)
            slices = [sum(v * v for v in w[i:i + 512]) / 512 for i in range(0, len(w), 512)]
            self.assertLess(abs(node('return L.loudest(d.s, 0, d.s.length - 38);', {'s': slices}) - check.momentary([y], 32)[0]), 0.05, kind)
            self.assertAlmostEqual(node('return L.loudest(d.s, 0, d.s.length - 38);', {'s': slices}), check.loudest(slices), places=9)

    def test_a_run_is_judged_by_its_last_play(self):
        quiet, loud = 10 ** ((-30 + 0.691) / 10), 10 ** ((-20 + 0.691) / 10)
        run = [0.0] * 16 + [quiet] * 44 + [loud] * 48
        seen = node('return L.result(d.e, 2);', {'e': run})
        self.assertAlmostEqual(seen['level'], -20, places=2)
        self.assertGreater(seen['apart'], 5)
        self.assertLess(seen['before'], -100)
        steady = node('return L.result(d.e, 3);', {'e': [quiet / 10] * 16 + [loud] * 136})
        self.assertAlmostEqual(steady['level'], -20, places=6)
        self.assertAlmostEqual(steady['apart'], 0, places=6)
        self.assertAlmostEqual(steady['before'], -40, places=6)

    def test_strokes_are_heard_where_they_are(self):
        """Chords and notes, soft and hard, let ring, stopped and run into each other, over the noise of a pickup: they are found where they begin, and
        nothing else is. One that is drowned by the one before may be missed."""
        rng, at, x = random.Random(8), [], [0.0] * int(13 * LOW)
        t = 0.5
        for n in range(14):
            at.append(t)
            size, ring = 0.03 + 0.3 * rng.random(), rng.choice((2.0, 5.0, 14.0))
            chord = rng.choice(((82.4,), (110.0, 164.8, 220.0, 277.2), (196.0, 246.9), (329.6,)))
            for i in range(int(min(1.6, 9 / ring) * LOW)):
                k = int(t * LOW) + i
                if k >= len(x):
                    break
                s = i / LOW
                x[k] += size * min(1.0, s / 0.002) * math.exp(-ring * s) * sum(math.sin(2 * math.pi * f * s) + 0.4 * math.sin(4 * math.pi * f * s) + 0.15 * math.sin(8 * math.pi * f * s) for f in chord) / len(chord)
                x[k] += size * 0.3 * rng.uniform(-1, 1) * math.exp(-s / 0.003)
            t += rng.choice((0.45, 0.7, 1.0))
        x = [v + 3e-4 * rng.uniform(-1, 1) + 4e-4 * math.sin(2 * math.pi * 50 * i / LOW) for i, v in enumerate(x)]
        seen = node('return L.strokes(Float32Array.from(d.x));', {'x': x})
        want = [v for v in at if v * LOW + 5632 <= len(x)]
        near = [min(want, key=lambda v: abs(v - s['at'] / LOW)) for s in seen]
        self.assertTrue(all(abs(s['at'] / LOW - v) < 0.02 for s, v in zip(seen, near)), [[round(s['at'] / LOW, 2) for s in seen], want])
        self.assertEqual(len(set(near)), len(seen))
        self.assertGreaterEqual(len(seen), len(want) - 1)
        silence = [v * 3e-4 for v in (rng.uniform(-1, 1) for _ in range(int(3 * LOW)))]
        self.assertEqual(node('return L.strokes(Float32Array.from(d.x)).length;', {'x': silence}), 0)

    def test_three_strokes_are_chosen_as_they_are_played(self):
        levels = [-30, -28, -27, -26, -25, -24, -23, -22, -20]
        strokes = [{'at': i, 'level': v, 'gap': 0.6, 'peak': 0.2} for i, v in enumerate(levels)]
        self.assertEqual(node('return L.choose(d.s).map(s => s.level);', {'s': strokes}), [-25, -26, -24])
        for s in strokes[2:6]:
            s['gap'] = 0.2                                              # those run into the next one
        self.assertNotIn(-25, node('return L.choose(d.s).map(s => s.level);', {'s': strokes}))
        self.assertEqual(len(node('return L.choose(d.s);', {'s': strokes[:3]})), 3)
        self.assertEqual(len(node('return L.choose(d.s);', {'s': strokes[:2]})), 2)

    def test_the_built_in_strokes_have_the_level_that_is_asked_for(self):
        seen = node('return Object.entries(L.LEVELS).map(([k, v]) => [v, L.built(v).map(c => Array.from(L.decode(c)))]);', {})
        self.assertEqual([v for v, _ in seen], [-28, -23, -18])
        for level, strokes in seen:
            self.assertEqual(len(strokes), 3)
            for x in strokes:
                self.assertEqual(len(x), 5632)
                self.assertLess(max(map(abs, x)), 0.9)
                y = [v for a, b in zip(x, x[1:] + [0.0]) for v in (a, 0.75 * a + 0.25 * b, 0.5 * (a + b), 0.25 * a + 0.75 * b)]
                self.assertAlmostEqual(check.momentary([y])[0], level, delta=0.4)

    def test_the_gains(self):
        items = [{'level': -24.2, 'out': 4, 'peak': tables.FULL * 10 ** (-9 / 20)}, {'level': -13.0, 'out': -6, 'peak': tables.FULL * 10 ** (-4 / 20)}, {'level': -50.0, 'out': 0, 'peak': tables.FULL / 100}]
        seen = node('return [d.i.map(i => L.gainFor(i, -20)), d.i.map(i => L.roomOf(i, -3)), L.start(d.i, -3), L.start(d.i.slice(0, 2), -3), L.median([3, 1, 2]), L.median([4, 1, 2, 3])];', {'i': items})
        self.assertEqual(seen[0], [4, -7, 12])
        self.assertEqual([seen[1][0], seen[1][1]], [6, 1])
        self.assertEqual(seen[2:], [-38, -20, 2, 2.5])

    def test_the_window_writes_gains_and_nothing_else(self):
        """Of what it can send, only HRLV and GAIN change something that is kept; what loads a preset or a scene is what any page does."""
        sent = set(re.findall(r'(?:ask|operate|Pedal\.cmd)\(\(?[`"]([A-Z]{2,8})\b', WINDOW))
        self.assertEqual(sent - {'LIM', 'LVL', 'FXS', 'AMPEQ', 'SNAPS', 'SNAPNAME', 'RECD'}, {'HRLV', 'REC', 'INJBEGIN', 'INJB', 'GAIN', 'PLOAD', 'SNAP'})


if __name__ == '__main__':
    unittest.main()
