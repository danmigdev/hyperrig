"""The product option of the MINI image: its identity, and that it is off unless asked for."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/pi32v2-isa')]
from build_hyperrig_mini_image import PRODUCT_DIR, PRODUCT_OPTION, product_identity  # noqa: E402
from build_ultrarig_app import assemble  # noqa: E402
from check_mini_panel import RECORDED  # noqa: E402

SOURCE = ROOT / 'firmware/ultrarig'


class Identity(unittest.TestCase):
    def tree(self, version):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        (Path(directory.name) / PRODUCT_DIR).mkdir(parents=True)
        (Path(directory.name) / PRODUCT_DIR / 'VERSION').write_text(version, encoding='ascii')
        return Path(directory.name)

    def test_the_id_follows_every_source_and_not_their_order(self):
        tree = self.tree('0.2.0-beta.1\n')
        version, first = product_identity(tree, {'a.s': '11', 'b.s': '22'})
        self.assertEqual(version, '0.2.0-beta.1')
        self.assertRegex(first, '^[0-9a-f]{16}$')
        self.assertEqual(product_identity(tree, {'b.s': '22', 'a.s': '11'})[1], first)
        for other in ({'a.s': '11', 'b.s': '23'}, {'a.s': '11', 'c.s': '22'}, {'a.s': '11'}):
            self.assertNotEqual(product_identity(tree, other)[1], first)

    def test_a_version_that_would_not_fit_the_console_line_is_refused(self):
        for version in ('', 'beta', '1.2', '0.2.0 x', '0.2.0-beta_1', '0.2.0-' + 'a' * 30):
            with self.assertRaises(SystemExit):
                product_identity(self.tree(version), {})

    def test_the_tree_names_a_version(self):
        self.assertRegex(product_identity(SOURCE, {})[0], r'^\d+\.\d+\.\d+')


class Option(unittest.TestCase):
    def test_every_product_change_is_under_the_option(self):
        """The names only mini/product defines are used only between .if MINI_PRODUCT and its .else or .endif."""
        own = set()
        for path in sorted((SOURCE / PRODUCT_DIR).glob('*.[chS]')):
            text = re.sub(r'/\*.*?\*/|//[^\n]*|"[^"\n]*"', ' ', path.read_text(encoding='ascii'), flags=re.S)
            own |= set(re.findall(r'\bhyperrig_\w+', text))
        for name in ('hyperrig_console', 'hyperrig_volume', 'hyperrig_panel_turn', 'hyperrig_stage', 'hyperrig_restart_with', 'hyperrig_transition',
                     'hyperrig_pairs_turn', 'hyperrig_shown_scene', 'hyperrig_scene_base', 'hyperrig_pack', 'hyperrig_unpack', 'hyperrig_acoustic_process', 'hyperrig_take_ringing', 'hyperrig_harmonizer_process'):
            self.assertIn(name, own)
        self.assertFalse([name for name in own if name.startswith('hyperrig_mini_')])          # the port's own, with the option and without it
        a_name = re.compile(r'\b(?:' + '|'.join(sorted(own, key=len, reverse=True)) + r')\b')
        used = 0
        for path in sorted(SOURCE.glob('*/*.s')):
            stack = []
            for line in path.read_text(encoding='ascii').splitlines():
                word = line.split(';')[0].split()
                if word[:1] == ['.if'] or word[:1] == ['.ifndef']:
                    stack.append(word[1:] == [PRODUCT_OPTION])
                elif word[:1] == ['.else']:
                    stack[-1] = False
                elif word[:1] == ['.endif']:
                    stack.pop()
                elif a_name.search(line.split(';')[0]):
                    self.assertTrue(any(stack), f'{path.name}: {line}')
                    used += 1
            self.assertEqual(stack, [], path.name)
        self.assertEqual(used, 97)

    def test_the_way_to_the_loader_has_the_loaders_numbers(self):
        """STAGE looks for what the bootloader and the loader look for, writes no flash, and restarts as the stock firmware does."""
        entry = (SOURCE / PRODUCT_DIR / 'loader_entry.c').read_text(encoding='ascii')
        header = (ROOT / 'firmware/mini_stage/engine.h').read_text(encoding='utf-8')
        for mine, theirs in (('CAPACITY', 'HRS_CAPACITY'), ('RECORD', 'HRS_RECORD'), ('MARK', 'HRS_RECORD_MARK'), ('LOADER_AT', 'HRS_LOADER_AT'),
                             ('LOADER_MAX', 'HRS_LOADER_MAX'), ('LOADER_CRC', 'HRS_LOADER_CRC')):
            value = re.search(rf'\b{mine} = (\w+)', entry).group(1)
            wanted = re.search(rf'#define {theirs} (?:UINT32_C\()?(0x[0-9a-f]+|\d+)', header).group(1)
            self.assertEqual(int(value, 0), int(wanted, 0), mine)
        restart = (SOURCE / PRODUCT_DIR / 'restart.S').read_text(encoding='ascii')
        self.assertIn('r0 = 0x01c7fd80', restart)
        self.assertIn('r1 |= 0x10', restart)
        for word in ('write', 'erase', 'program'):
            self.assertNotIn('_' + word, entry)

    def test_the_option_reaches_the_assembler_only_when_given(self):
        with tempfile.TemporaryDirectory() as directory:
            unit = Path(directory) / 'unit.s'
            unit.write_bytes(b'.ifndef MINI_PRODUCT\n.set MINI_PRODUCT, 0\n.endif\n.if MINI_PRODUCT\n.byte 1,2,3,4\n.endif\n'
                             b'.byte 9\n')
            plain, product = assemble(unit, 'mini'), assemble(unit, 'mini', options=(PRODUCT_OPTION,))
            self.assertNotIn(b'\1\2\3\4\t', plain)
            self.assertIn(b'\1\2\3\4\t', product)
            self.assertEqual(assemble(unit, 'g', options=(PRODUCT_OPTION,)), assemble(unit, 'g'))

    def test_the_panel_check_replaces_only_services_outside_the_switch_event(self):
        for name in ('footswitch_events_switch_event', 'panel_inputs_switch_scan', 'panel_inputs_switch_status',
                     'footswitch_events_bank_of', 'panel_inputs_pedal_volume', 'hyperrig_console', 'hyperrig_volume',
                     'hyperrig_panel_turn'):
            self.assertNotIn(name, RECORDED)


if __name__ == '__main__':
    unittest.main()
