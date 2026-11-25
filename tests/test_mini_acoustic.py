"""The acoustic block of the product build: its numbers, its names, and where its code may run. What it does is in tools/check_mini_effect_block.py."""
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import make_acoustic_tables as tables  # noqa: E402

SOURCE = ROOT / 'firmware/ultrarig'
CODE = (SOURCE / 'mini/product/acoustic.c').read_text(encoding='ascii')
MIXED = (SOURCE / 'flash/0203343e_mixed.s').read_text(encoding='ascii')


def product_part(text, after):
    """What is between the .if MINI_PRODUCT after a text and its .else or .endif."""
    i = text.index('.if MINI_PRODUCT\n', text.index(after)) + len('.if MINI_PRODUCT\n')
    return text[i:min(text.index('.else\n', i), text.index('.endif\n', i))]


class Acoustic(unittest.TestCase):
    def test_the_tables_are_as_made(self):
        self.assertEqual(tables.OUTPUT.read_bytes().decode('ascii'), tables.text())

    def test_the_resonances_and_bands_are_stable(self):
        for hz, q, _ in tables.MODES:
            self.assertTrue(40 < hz < 6000 and 0.4 < q < 20)
            b = tables.biquad('band', hz, q)
            self.assertLess(b[4], 1.0)
        rows = tables.bands()
        self.assertEqual(len(rows), tables.BANDS)
        self.assertTrue(all(row[0] ** 2 + row[1] ** 2 < 1 for row in rows))
        self.assertEqual(len(tables.MODES) % 2, 0)                      # the code works two at a time

    def test_the_lines_fit_where_they_are(self):
        """Every echo is shorter than its line; the places of the second string are behind the chunk that is written, and within the ring."""
        for late, line in zip(tables.ECHOES, (128, 256, 512)):
            self.assertTrue(0 < late < line)
        ring = int(re.search(r'RING = (\d+)', CODE).group(1))
        self.assertTrue(tables.NEAR_MS * tables.FS / 1000 > tables.CHUNK)
        self.assertLess((tables.NEAR_MS + tables.SPAN_MS) * tables.FS / 1000 + tables.CHUNK + 2, ring)
        self.assertEqual(int(re.search(r'CHUNK = (\d+)', CODE).group(1)), tables.CHUNK)

    def test_the_rows_of_the_parameters(self):
        names = re.findall(r'const char hyperrig_acoustic_p(\d)\[\] = "(\w+)"', CODE)
        self.assertEqual([n for _, n in names], ['strings', 'body_pct', 'top_db', 'decay_pct', 'air_pct', 'doubles_pct', 'nivel_db'])
        part = product_part(MIXED, '; HyperRig MINI, product option: the acoustic block')
        rows = re.findall(r'\.byte ([0-9a-fx,]+)\n\s+\.long hyperrig_acoustic_p(\d)', part)
        self.assertEqual([int(i) for _, i in rows], list(range(7)))
        seen = [struct.unpack('<4h', bytes(int(v, 16) for v in row.split(','))) for row, _ in rows]
        self.assertEqual(seen, [(0, 1, 0, 0), (0, 100, 70, 0), (-12, 12, 0, 0), (0, 100, 60, 0), (0, 100, 25, 0), (0, 100, 60, 0), (-12, 12, 0, 0)])
        self.assertEqual(len(re.findall(r'\.(?:byte|long)', part)), 14)

    def test_only_a_product_build_uses_it(self):
        own = ('hyperrig_acoustic', 'hyperrig_name_acoustic', 'Lhr_', 'ultrarig_ram_code_end')
        used = 0
        for path in sorted(SOURCE.glob('*/*.s')):
            stack = []
            for line in path.read_text(encoding='ascii').splitlines():
                word = line.split(';')[0].split()
                if word[:1] in (['.if'], ['.ifndef']):
                    stack.append(word[1:] == ['MINI_PRODUCT'])
                elif word[:1] == ['.else']:
                    stack[-1] = False
                elif word[:1] == ['.endif']:
                    stack.pop()
                elif any(name in line.split(';')[0] for name in own):
                    self.assertTrue(any(stack), f'{path.name}: {line}')
                    used += 1
        self.assertGreater(used, 15)

    def test_its_sound_runs_in_the_ram_and_may(self):
        """Every function of the sound is in the RAM, the end of which the start-up code tells the processor in a product build."""
        sound = ['octave', 'strings', 'notes', 'body', 'air', 'diffuse', 'log2_of', 'exp2_of', 'inverse_root', 'hyperrig_acoustic_run', 'hyperrig_acoustic_process']
        for name in sound:
            self.assertRegex(CODE, rf'(?m)^SOUND (?:static )?(?:inline )?(?:void|float) {name}\(')
        self.assertNotIn('static const', re.sub(r'TABLE static const', '', tables.text()))
        self.assertIn('r0 = ultrarig_ram_code_end', product_part((SOURCE / 'flash/02000604_phase3_p3.s').read_text(encoding='ascii'), 'phase3_p3_debug_init:'))
        script = (SOURCE / 'app.ld').read_text(encoding='ascii')
        self.assertLess(script.index('*(.ram_text .ram_text.*)'), script.index('ultrarig_ram_code_end = .;'))
        self.assertLess(script.index('ultrarig_ram_code_end = .;'), script.index('*(.data .data.*'))


if __name__ == '__main__':
    unittest.main()
