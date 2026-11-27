"""The effects of HyperRig from the id 40 on: their numbers, their descriptions, and what the reference makes of a few sounds. The compiled code is
compared with the reference in tools/check_mini_effects.py."""
import json
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import build_mini_dev_editor as editor  # noqa: E402
import check_mini_effects as check  # noqa: E402
import effects_reference as reference  # noqa: E402
import make_effect_tables as tables  # noqa: E402

SOURCE = ROOT / 'firmware/ultrarig'
PRODUCT = SOURCE / 'mini/product'
FRAME = (PRODUCT / 'effects.c').read_text(encoding='ascii')
HEADER = (PRODUCT / 'effects.h').read_text(encoding='ascii')
NAMES = list(reference.EFFECTS)
CODE = {n: (PRODUCT / f'fx_{n}.c').read_text(encoding='ascii') for n in NAMES}
MIXED = (SOURCE / 'flash/0203343e_mixed.s').read_text(encoding='ascii')
LIKE = {k: int(v) for k, v in re.findall(r'(LIKE_\w+) = (\d+)', HEADER)}
FS = 48077


def sine(hertz, n, size=0.3):
    return [int(8388607 * size * math.sin(2 * math.pi * hertz * i / FS)) for i in range(n)]


def level(x, hertz):
    """The size of one frequency in a sound, a tone of full level being 1."""
    n = len(x)
    c = sum(v * math.cos(2 * math.pi * hertz * i / FS) * (0.5 - 0.5 * math.cos(2 * math.pi * i / n)) for i, v in enumerate(x))
    s = sum(v * math.sin(2 * math.pi * hertz * i / FS) * (0.5 - 0.5 * math.cos(2 * math.pi * i / n)) for i, v in enumerate(x))
    return 4 * math.hypot(c, s) / n / 8388607


class Descriptions(unittest.TestCase):
    def test_the_tables_are_as_made(self):
        self.assertEqual(tables.OUTPUT.read_bytes().decode('ascii'), tables.text())

    def test_the_list_and_the_files(self):
        listed = re.findall(r'X\((\w+)\)', re.search(r'#define EFFECTS\(X\) (.*)', FRAME).group(1))
        self.assertEqual(listed, NAMES)
        self.assertEqual(sorted(p.stem[3:] for p in PRODUCT.glob('fx_*.c')), sorted(NAMES))
        self.assertEqual(check.NAMES, NAMES)

    def test_the_descriptions(self):
        groups = re.findall(r'    \.long (\w+)  ; "(\w+)"|    (\.byte 0x00,0x00,0x00,0x00)', MIXED[MIXED.index('L0203b3e0:'):MIXED.index('effect_stage_capabilities:')])
        for name, code in CODE.items():
            text = code[code.index(f'EFFECT hyperrig_fx_{name} = {{'):]
            self.assertIn(f'.name = "{name}"', text)
            rows = [(int(a), int(b), int(c), n.strip('"').lower()) for a, b, c, n in re.findall(r'\{ (-?\d+), (-?\d+), (-?\d+), 0, ("\w+"|[A-Z_]+) \}', text)]
            self.assertEqual(rows, reference.EFFECTS[name].ROWS)
            self.assertEqual(int(re.search(r'\.cost = (\d+)', text).group(1)), check.COSTS[name])
            like = LIKE[re.search(r'\.like = (\w+)', text).group(1)]
            self.assertEqual((like, groups[like][1]), (check.LIGHTS[name], check.GROUPS[name]))
            self.assertRegex(name, r'^[a-z][a-z0-9]{1,14}$')
            self.assertTrue(rows and len(rows) <= 7 and all(a <= c <= b for a, b, c, _ in rows))

    def test_there_is_room_for_their_ids_in_the_table_of_the_stages(self):
        part = MIXED[MIXED.index('effects of HyperRig, of one channel, ids 40 to 63'):]
        zeros = re.search(r'\.byte ([0-9a-fx,]+)', part).group(1).split(',')
        self.assertEqual(zeros, ['0x00'] * 24)
        self.assertLessEqual(len(NAMES), 24)

    def test_a_hook_in_a_small_function_keeps_the_registers(self):
        """The application was compiled with each function knowing which registers the small ones it calls leave alone."""
        for name, function in (('02029204_console_reports', 'hyperrig_effect_name'), ('0202921e_preset_application', 'hyperrig_effect_rows'), ('02030f6e_slot_queries', 'hyperrig_effect_like')):
            text = re.sub(r' *;.*', '', (SOURCE / f'flash/{name}.s').read_text(encoding='ascii'))
            lines = [line.strip() for line in text.splitlines()]
            at = lines.index(f'call {function}')
            before = [line for line in lines[at - 2:at] if line != 'r0 = r1'][-1]
            self.assertEqual(before, '[--sp] = {rets, r3-r1}', name)
            self.assertIn(lines[at + 1], ('{pc, r3-r1} = [sp++]', '{rets, r3-r1} = [sp++]'), name)

    def test_what_runs_with_the_sound_is_in_the_ram(self):
        for name, code in CODE.items():
            functions = re.findall(r'(?m)^((?:SOUND )?)static (?:inline )?(?:void|int32_t) (\w+)\(', code)
            self.assertIn(('', 'set'), functions)
            self.assertTrue(all(sound for sound, f in functions if f != 'set'), functions)
            for line in re.findall(r'(?m)^(.*)static const u?int16_t (\w+)\[', code):
                if line[1] in ('fir', 'back'):
                    self.assertTrue(line[0].startswith('TABLE'))
        for f in ('hyperrig_effect_process', 'hyperrig_effect_cost'):
            self.assertRegex(FRAME, rf'(?m)^SOUND \w+ {f}\(')
        self.assertEqual(len(re.findall(r'static inline __attribute__\(\(always_inline\)\)', HEADER)), len(re.findall(r'static inline', HEADER)))

    def test_what_glides_is_small_enough_to(self):
        """A step of the frame is the way that is left times the samples of a chunk."""
        for name, e in reference.EFFECTS.items():
            glides = re.search(r'\.glides = ([^,]+),', CODE[name]).group(1)
            self.assertEqual(len(glides.split('|')), bin(e.GLIDED).count('1'), name)
            for which in (0, 1):
                kept = [r[which] for r in e.ROWS] + [0] * (7 - len(e.ROWS))
                settings = e().set(kept)
                self.assertEqual(len(settings), int(re.search(r'SETTINGS = (\d+)', HEADER).group(1)))
                self.assertTrue(all(abs(v) < 1 << 24 for k, v in enumerate(settings) if e.GLIDED >> k & 1 or k < reference.OWN), (name, settings))
                self.assertTrue(all(abs(v) < 1 << 31 for v in settings))

    def test_the_lines_are_long_enough(self):
        r = reference.Reverse
        longest, shortest = (r.ROWS[0][k] * 16026 // 1000 for k in (1, 0))
        self.assertLessEqual(2 * longest + 1, r.LINE)
        self.assertGreater(shortest, 2 * tables.FADE)
        s = reference.Swell
        self.assertLess(s.LATE, s.LINE)
        self.assertLess(s.WHOLE // s.SHUT, s.LATE)
        self.assertEqual(sum(tables.FIR), 32768)
        self.assertEqual([sum(row) for row in tables.BACK], [32768] * 3)
        self.assertEqual(tables.FIR, tables.FIR[::-1])

    def test_the_editor_knows_each(self):
        looks = json.loads((ROOT / 'app/mini/effects.json').read_bytes())
        self.assertEqual(list(looks['effects']), NAMES)
        for name, look in looks['effects'].items():
            own = [r[3] for r in reference.EFFECTS[name].ROWS]
            self.assertTrue(set(look['tips']) <= set(own), name)
            self.assertTrue(set(own) - set(look['tips']) <= {'nivel_db'}, name)
            self.assertRegex(look['colour'], r'^#[0-9a-f]{6}$')
            self.assertNotIn('</', look['icon'].replace('/>', ''))
        for old, new in editor.effect_patches(looks):
            self.assertIn(old.rstrip('; }') if old.startswith('doubler') else old, new)


class Sounds(unittest.TestCase):
    def test_octaves_of_a_note(self):
        for hertz, wanted, parameters in ((110, 55, {'down1_pct': 100}), (110, 27.5, {'down1_pct': 0, 'down2_pct': 100}), (220, 440, {'down1_pct': 0, 'up_pct': 100})):
            out = reference.Block('octaver', limpio_pct=0, **parameters).run(sine(hertz, 24000))[9600:]
            self.assertGreater(level(out, wanted), 0.1)
            self.assertLess(level(out, hertz), level(out, wanted) / 10, (hertz, wanted))

    def test_the_octaver_at_its_defaults_keeps_the_sound(self):
        out = reference.Block('octaver').run(sine(110, 24000))[9600:]
        self.assertGreater(level(out, 110), 0.25)
        self.assertGreater(level(out, 55), 0.05)

    def test_a_note_grows_out_of_nothing(self):
        x = [0] * 4800 + sine(196, 48000)
        out = reference.Block('swell', ataque_ms=500).run(x)
        peak = lambda a, b: max(abs(v) for v in out[a:b])
        self.assertLess(peak(0, 4800 + 480), 8388607 * 0.3 / 500)
        self.assertLess(peak(4800, 4800 + 4800), 8388607 * 0.3 * 0.1)
        self.assertGreater(peak(4800 + 28000, 4800 + 33000), 8388607 * 0.3 * 0.95)
        levels = [peak(4800 + k * 2400, 4800 + (k + 1) * 2400) for k in range(10)]
        self.assertEqual(levels, sorted(levels))

    def test_depth_0_is_the_sound_itself_a_little_later(self):
        x = sine(196, 4800)
        out = reference.Block('swell', prof_pct=0).run(x)
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(out[reference.Swell.LATE:], x)))

    def test_a_piece_comes_out_backwards(self):
        """A tone that goes up comes out going down: the piece of the input, turned round, is in the output."""
        n, ms = 48000, 200
        x = [int(8388607 * 0.3 * math.sin(2 * math.pi * (200 * (i / FS) + 400 * (i / FS) ** 2))) for i in range(n)]
        out = reference.Block('reverse', tiempo_ms=ms, realim_pct=0, mezcla_pct=100, amort_pct=0).run(x)
        piece = FS * ms // 1000
        start = 2 * (piece - 3 * tables.FADE)                     # the third piece: what is played is what came in before it
        best = 0
        for late in range(0, 90, 3):
            a = out[start + 1500 + late:start + 6000 + late:7]
            b = [x[start - 1500 - k] for k in range(0, 4500, 7)]
            dot = sum(p * q for p, q in zip(a, b))
            best = max(best, abs(dot) / math.sqrt(sum(p * p for p in a) * sum(q * q for q in b)))
        self.assertGreater(best, 0.95)

    def test_the_ensemble_keeps_the_level_and_goes_out_of_tune(self):
        """A chord through it is as loud as before, at every mix; a tone is spread around its pitch, and without depth it is not."""
        x = [a + b + c for a, b, c in zip(sine(196, 40000, 0.1), sine(247, 40000, 0.1), sine(294, 40000, 0.1))]
        power = lambda y: math.sqrt(sum(v * v for v in y[8000:]) / len(y[8000:]))
        for mix in (0, 25, 50, 75, 100):
            out = reference.Block('ensemble', mezcla_pct=mix).run(list(x))
            self.assertLess(abs(20 * math.log10(power(out) / power(x))), 2.5, mix)
        self.assertEqual(reference.Block('ensemble', mezcla_pct=0).run(list(x)), x)
        still = reference.Block('ensemble', mezcla_pct=100, prof_pct=0, tono_pct=100).run(sine(440, 40000))[16000:]
        deep = reference.Block('ensemble', mezcla_pct=100, prof_pct=100, tono_pct=100).run(sine(440, 40000))[16000:]
        self.assertGreater(level(still, 440), 0.3)
        self.assertLess(level(deep, 440), level(still, 440) / 2)

    def test_the_repeats_of_the_vintage_delay(self):
        """They come at their time, each softer and darker than the one before, go out of tune with the waver, and full feedback stays within."""
        ms, at = 200, FS * 200 // 1000
        x = [int(8388607 * 0.2 * (math.sin(2 * math.pi * 400 * i / FS) + math.sin(2 * math.pi * 2000 * i / FS)) * math.sin(math.pi * i / 2400) ** 2) if i < 2400 else 0 for i in range(50000)]
        out = reference.Block('vintage', tiempo_ms=ms, realim_pct=80, mezcla_pct=100, amort_pct=50, prof_pct=0).run(list(x))
        peaks = [max(abs(v) for v in out[k * at - 200:k * at + 2600]) for k in range(1, 5)]
        self.assertFalse(any(abs(v) > 2000 for v in out[:at - 300]))
        self.assertTrue(all(b < a for a, b in zip(peaks, peaks[1:])) and peaks[3] > 8388607 * 0.01, peaks)
        bright = lambda k: level(out[k * at - 200:k * at + 2600], 2000) / level(out[k * at - 200:k * at + 2600], 400)
        self.assertLess(bright(3), bright(2) / 1.5)
        self.assertLess(bright(2), bright(1) / 1.5)
        x = sine(330, 24000) + [0] * 72000
        out = reference.Block('vintage', tiempo_ms=150, realim_pct=100, mezcla_pct=100, amort_pct=0, prof_pct=100).run(x)
        self.assertLess(max(abs(v) for v in out[60000:]), 8388607 * 1.2)
        wet = reference.Block('vintage', mezcla_pct=0).run(sine(330, 4000))
        self.assertEqual(wet, sine(330, 4000))

    def test_silence_stays_silence_and_the_loudest_stays_within(self):
        for name in NAMES:
            self.assertFalse(any(reference.Block(name).run([0] * 512)))
            out = reference.Block(name, **{r[3]: r[1] for r in reference.EFFECTS[name].ROWS}).run([2 ** 31 - 1 if i // 60 % 2 else -2 ** 31 for i in range(4096)])
            self.assertLessEqual(max(abs(v) for v in out), reference.LIMIT)


if __name__ == '__main__':
    unittest.main()
