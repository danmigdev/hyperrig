"""Packaging of tools/build_hyperrig_mini_image.py: the area decodes back to its parts with valid CRCs, keeps the
stock partition records verbatim, and refuses an application that does not fit. The bindings of the appended code
are read from the linked application, every binding of the tree resolves, and a fixed address of the appended code at
no binding is reported."""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from build_hyperrig_mini_image import BASE, bindings_of, literal_loads, package, unbound_constants  # noqa: E402
from hyperrig.jieli import unpack_app  # noqa: E402
from pi32v2_form_asm import assemble  # noqa: E402

AREA = json.loads((ROOT / 'firmware/ultrarig/mini/area.json').read_bytes())


class Packaging(unittest.TestCase):
    def test_round_trip(self):
        app, cfg = bytes(range(256)) * 10 + b'\x01\x02', b'cfg-tool' * 3
        raw, layout = package(app, cfg, AREA)
        decoded, entries, files = unpack_app(raw)
        self.assertEqual(len(raw), AREA['partition_bytes'])
        self.assertEqual((files['app.bin'], files['cfg_tool.bin']), (app, cfg))
        self.assertEqual(layout['head_end'], AREA['app_offset'] + len(app) + len(cfg))
        self.assertEqual([e.name for e in entries], [r['name'] for r in AREA['records']])
        self.assertTrue(all(b == 0xFF for b in raw[layout['encoded_end']:]))

    def test_partition_records_kept_verbatim(self):
        raw, _ = package(b'\0\0' * 64, b'c', AREA)
        plain, _, _ = unpack_app(raw)
        for r in AREA['records']:
            if 'record_hex' in r:
                self.assertEqual(plain[r['header_offset']:r['header_offset'] + 32].hex(), r['record_hex'])

    def test_application_too_large_is_refused(self):
        with self.assertRaises(SystemExit):
            package(b'\0' * AREA['partition_bytes'], b'c', AREA)


class Bindings(unittest.TestCase):
    def test_each_binding_is_its_symbol_plus_its_offset(self):
        elf = assemble('.text\nfirst:\n    nop\n    nop\nsecond:\n    rts\n')
        spec = {'bindings': [
            {'name': 'A', 'symbol': 'second', 'offset': 0, 'original': '0x4', 'kind': 'c'},
            {'name': 'B', 'symbol': 'second', 'offset': 2, 'original': '0x6', 'kind': 'asm'},
            {'name': 'C', 'symbol': 'first', 'offset': 0, 'original': '0x0', 'kind': 'ld'}]}
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'mini').mkdir()
            (Path(directory) / 'mini/bindings.json').write_text(json.dumps(spec), encoding='utf-8')
            found = bindings_of(Path(directory), elf)
            self.assertEqual({k: v['address'] for k, v in found.items()}, {'A': 4, 'B': 6, 'C': 0})
            spec['bindings'][0]['symbol'] = 'missing'
            (Path(directory) / 'mini/bindings.json').write_text(json.dumps(spec), encoding='utf-8')
            with self.assertRaises(SystemExit):
                bindings_of(Path(directory), elf)

    def test_the_tree_lists_every_original_address_once(self):
        spec = json.loads((ROOT / 'firmware/ultrarig/mini/bindings.json').read_bytes())
        names = [b['name'] for b in spec['bindings']]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(b['kind'] in ('c', 'asm', 'ld') for b in spec['bindings']))
        shims = ROOT / 'firmware/ultrarig/mini/shims'
        text = '\n'.join(p.read_text(encoding='ascii') for p in shims.rglob('*') if p.suffix in ('.c', '.S', '.ld'))
        for b in spec['bindings']:
            self.assertIn(b['name'], text)
            self.assertNotIn(b['original'], text.lower())

    def test_literal_loads_skip_the_fields_a_relocation_fills(self):
        load = lambda value: b'\xc2\xff' + struct.pack('<I', value)
        code = load(0x02004998) + b'\x00\x00' + load(0x01C278DC)
        self.assertEqual(literal_loads(code, set()), [(0, 0x02004998), (8, 0x01C278DC)])
        self.assertEqual(literal_loads(code, {8}), [(0, 0x02004998)])
        self.assertEqual(literal_loads(code, {2}), [(8, 0x01C278DC)])

    def test_a_fixed_address_at_no_binding_is_reported_and_a_name_is_not(self):
        bound = {'G': {'address': 0x02004998, 'kind': 'c', 'original': 0x02004998}}
        obj = assemble('.text\n    r2 = 0x02004998\n    r3 = 0x02005194\n    r4 = somewhere\n'
                       '    r5 = 0x01c278dc\n    r6 = 0x00050000\n    r7 = 0x01c7fd80\n    rts\n')
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'c').mkdir()
            (Path(directory) / 'c/x.o').write_bytes(obj)
            found = unbound_constants(Path(directory), ['c/x.o'], (0x020774F4, 0x01C7FBA0), bound)
        self.assertEqual([f['value'] for f in found], ['0x02005194', '0x01c278dc'])
        self.assertTrue(found[0]['at'].startswith('c/x.o:.text+0x'))
        self.assertGreaterEqual(BASE, 0x02000120)


if __name__ == '__main__':
    unittest.main()
