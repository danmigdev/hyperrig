"""The harmonizer of the product build: its numbers, its names, where its code may run, and what its model does. The compiled code against the
model is in tools/check_mini_harmonizer.py."""
import math
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'tests')]
import harmonizer_model as model  # noqa: E402
import make_harmonizer_tables as tables  # noqa: E402
from test_mini_acoustic import MIXED, SOURCE, product_part  # noqa: E402

CODE = (SOURCE / 'mini/product/harmonizer.c').read_text(encoding='ascii')
RATE = 48077


def sine(hertz, blocks, level=0.25, bend=0.0, start=0):
    """A string that is picked: a sine with some partials; bend: semitones it goes up by in a fifth of a second, after a tenth."""
    out, phase = [], 0.0
    for i in range(128 * blocks):
        t = i / RATE
        phase += 2 * math.pi * hertz * 2 ** (bend * min(max((t - 0.1) / 0.2, 0), 1) / 12) / RATE
        v = sum(math.sin(k * phase) / k for k in (1, 2, 3))
        out.append(round(level * 2 ** 22 * v * (1 - math.exp(-t * 2000)) * math.exp(-t)))
    return out


def heard(block, samples):
    """What a block says after some samples: the note it hears and the intervals of the voices, in semitones."""
    block.run(samples)
    return block.note > 0, block.pitch / 256, [v.interval / 256 for v in block.voices]


class Numbers(unittest.TestCase):
    def test_the_tables_are_as_made(self):
        self.assertEqual(tables.OUTPUT.read_bytes().decode('ascii'), tables.text())

    def test_the_filters_let_a_constant_through(self):
        self.assertEqual(sum(tables.quarter()), 32768)
        self.assertEqual(len(tables.quarter()), 24)                     # the code takes six times four
        for p, row in enumerate(model.BETWEEN):
            self.assertTrue(16381 <= sum(row) <= 16384 and all(-32768 <= v <= 32767 for v in row), [p, row])
            self.assertEqual(row, model.BETWEEN[64 - p][::-1] if p else [0, 16384, 0, 0])

    def test_the_scales_have_seven_notes_that_rise(self):
        for name, scale in tables.SCALES:
            self.assertEqual(len(scale), 7, name)
            self.assertTrue(scale[0] == 0 and all(a < b < 12 for a, b in zip(scale, scale[1:])), name)

    def test_what_the_code_and_the_model_have_in_common(self):
        for name in ('CHUNK', 'RING', 'BEFORE', 'AFTER', 'SHORTEST', 'LONGEST', 'WIDE', 'LOOK', 'BACK'):
            self.assertEqual(int(re.search(rf'\b{name} = (\d+)', CODE).group(1)), getattr(model, name), name)
        # the longest lag that is compared, and the one after it, is within what is kept
        self.assertLessEqual(model.LONGEST + 2 + 2 * (model.WIDE - 1) + 2, model.BACK)
        # the longest step, with the fades and the reach of the reading, is within the line
        self.assertLess(4 * (model.LONGEST + 2 * model.WIDE) + 2 * 256, model.FAR >> 16)
        self.assertLess((model.FAR >> 16) + 64 + model.CHUNK, model.RING)
        self.assertEqual(int(re.search(r'FAR = (\d+) << 16', CODE).group(1)), model.FAR >> 16)


class Names(unittest.TestCase):
    def test_the_rows_of_the_parameters(self):
        names = re.findall(r'const char hyperrig_harmonizer_p(\d)\[\] = "(\w+)"', CODE)
        self.assertEqual([n for _, n in names], ['key', 'scale', 'voice1', 'voice2', 'balance_pct', 'mezcla_pct', 'nivel_db'])
        part = product_part(MIXED, '; HyperRig MINI, product option: the harmonizer')
        rows = re.findall(r'\.byte ([0-9a-fx,]+)\n\s+\.long hyperrig_harmonizer_p(\d)', part)
        self.assertEqual([int(i) for _, i in rows], list(range(7)))
        seen = [struct.unpack('<4h', bytes(int(v, 16) for v in row.split(','))) for row, _ in rows]
        self.assertEqual(seen, [(0, 11, 0, 0), (0, len(tables.SCALES) - 1, 0, 0), (-7, 7, 2, 0), (-7, 7, 0, 0), (0, 100, 50, 0), (0, 100, 50, 0), (-12, 12, 0, 0)])
        self.assertEqual(tuple(r[2] for r in seen), model.DEFAULTS)
        self.assertEqual(len(re.findall(r'\.(?:byte|long)', part)), 14)

    def test_the_editor_names_every_choice(self):
        page = (ROOT / 'tools/build_mini_dev_editor.py').read_text(encoding='utf-8')
        count = lambda unit: len(re.findall(r'"[^"]+"', re.search(unit + r': \{ first: -?\d+, names: \[([^\]]+)\]', page).group(1)))
        self.assertEqual([count(u) for u in ('hrkey', 'hrscale', 'hrvoice')], [12, len(tables.SCALES), 15])

    def test_its_sound_runs_in_the_ram(self):
        functions = re.findall(r'(?m)^((?:SOUND )?)(?:static )?(?:ONCE_ONLY |inline )?(?:void|int|int32_t|int64_t) (\w+)\(', CODE)
        outside = [name for sound, name in functions if not sound]
        self.assertEqual(outside, ['climb', 'held', 'much', 'hyperrig_harmonizer_settings', 'hyperrig_harmonizer_construct'])
        self.assertGreater(len(functions), 20)
        self.assertRegex(tables.text(), r'(?m)^TABLE static const int16_t quarter\[')

    def test_no_product_of_two_halfwords(self):
        """That form resets the processor; the application has the one of a halfword and a word."""
        for text in re.findall(r'__asm__\((.*)', CODE):
            self.assertRegex(text, r'\+= h\[%1 \+\+= \d\]\*\[%2 \+\+= \d\] \(s\)')
        self.assertNotRegex(CODE, r'\]\*h\[')


class Sound(unittest.TestCase):
    def test_every_note_of_a_guitar_is_heard(self):
        wrong = []
        for note in range(40, 89, 3):
            seen, pitch, _ = heard(model.Harmonizer(), sine(440 * 2 ** ((note - 69) / 12), 30))
            if not seen or abs(pitch - note) > 0.06:
                wrong.append([note, seen, pitch])
        self.assertEqual(wrong, [])

    def test_a_scale_is_harmonized_in_its_key(self):
        """E minor, a third above and a sixth below: the notes of the voices are notes of the scale."""
        scale = {(4 + s) % 12 for s in tables.SCALES[1][1]}
        for note in (52, 54, 55, 57, 59, 60, 62, 64):
            _, _, intervals = heard(model.Harmonizer((4, 1, 2, -5, 50, 50, 0)), sine(440 * 2 ** ((note - 69) / 12), 24))
            self.assertTrue(all(abs(i - round(i)) < 0.05 and (note + round(i)) % 12 in scale for i in intervals), [note, intervals])
            self.assertIn(round(intervals[0]), (3, 4))
            self.assertIn(round(intervals[1]), (-8, -9))

    def test_every_scale_keeps_the_voices_in_it(self):
        for kind, (name, scale) in enumerate(tables.SCALES[:tables.FIXED]):
            for steps in range(-7, 8):
                for here in range(12):
                    v = model.semitones(kind, here, steps)
                    if abs(steps) == 7 or not steps:
                        self.assertEqual(abs(v), 12 if steps else 0 if here in scale else abs(v))
                    else:
                        self.assertIn((here + v) % 12, scale, [name, steps, here, v])
                    self.assertLessEqual(abs(v - steps * 12 / 7), 2.01, [name, steps, here, v])
        self.assertEqual({model.semitones(9, n, 2) for n in range(12)}, {4})
        self.assertEqual({model.semitones(10, n, -2) for n in range(12)}, {-3})

    def test_a_bend_goes_from_one_interval_to_the_next(self):
        """C bent to D in C major: the voice goes from E to F and hardly down."""
        block, x, notes = model.Harmonizer(), sine(440 * 2 ** ((60 - 69) / 12), 200, bend=2.0), []
        for k in range(0, len(x), 128):
            block.run(x[k:k + 128])
            if k > 128 * 20:
                notes.append(block.pitch / 256 + block.voices[0].interval / 256)
        self.assertAlmostEqual(notes[0], 64, delta=0.1)
        self.assertAlmostEqual(notes[-1], 65, delta=0.1)
        self.assertLess(max(notes), 65.35)
        self.assertGreater(min(b - a for a, b in zip(notes, notes[8:])), -0.25)

    def test_the_pitch_of_the_voice(self):
        """A at 220 Hz with the voice alone, a third above: 261.6 Hz, by its zero crossings."""
        out = model.Harmonizer((0, 0, 2, 0, 50, 100, 0)).run([round(2 ** 21 * math.sin(2 * math.pi * 220 * i / RATE)) for i in range(128 * 150)])
        part = out[128 * 60:]
        up = [i + a / (a - b) for i, (a, b) in enumerate(zip(part, part[1:])) if a < 0 <= b]
        self.assertAlmostEqual(RATE * (len(up) - 1) / (up[-1] - up[0]), 220 * 2 ** (3 / 12), delta=0.3)

    def test_a_chord_is_no_note(self):
        chord = [sum(round(2 ** 20 * math.sin(2 * math.pi * f * i / RATE)) for f in (110.0, 164.8, 220.0, 277.2, 329.6)) for i in range(128 * 60)]
        block = model.Harmonizer()
        block.run(chord)
        self.assertEqual((block.note, block.chord), (0, 1))

    def test_silence_and_what_is_too_loud(self):
        self.assertFalse(any(model.Harmonizer().run([0] * 1280)))
        for x in ([8388607] * 2560, [8388607 if i // 60 % 2 else -8388608 for i in range(2560)], [8388607 if i % 2 else -8388608 for i in range(2560)]):
            out = model.Harmonizer((3, 2, 7, -7, 50, 50, 12)).run(x)
            self.assertLessEqual(max(map(abs, out)), 8388607)

    def test_the_mix_the_balance_and_the_level(self):
        s = lambda *p: model.Settings(p)
        self.assertEqual((s(0, 0, 2, 4, 50, 0, 0).dry, s(0, 0, 2, 4, 50, 0, 0).wet), (16384, [0, 0]))
        self.assertEqual((s(0, 0, 2, 4, 50, 100, 0).dry, s(0, 0, 2, 0, 50, 100, 0).wet[1]), (0, 0))
        self.assertEqual(s(0, 0, 2, 4, 0, 50, 0).wet[1], 0)
        self.assertEqual(s(0, 0, 2, 4, 100, 50, 0).wet[0], 0)
        self.assertGreater(s(0, 0, 2, 4, 50, 50, 6).dry, s(0, 0, 2, 4, 50, 50, 0).dry)


if __name__ == '__main__':
    unittest.main()
