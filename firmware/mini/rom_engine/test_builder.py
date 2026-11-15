"""Fault-injection checks for the offline ELF/record validation boundary."""
import json
from pathlib import Path
import re
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from build_mini_rom_engine import inspect_elf, stack_audit, validate_record


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'research/mini-rom-engine.json').read_text())
        cls.item = cls.report['artifacts'][0]
        cls.raw = (ROOT / cls.item['elf']).read_bytes()
        cls.base = cls.item['base']
        cls.header = struct.unpack_from('<HHIIIIIHHHHHH', cls.raw, 16)
        cls.expected = cls.report['golden']

    def test_both_linked_images_and_stack_bounds(self):
        for item in self.report['artifacts']:
            raw = (ROOT / item['elf']).read_bytes()
            payload, symbols, layout = inspect_elf(raw, item['base'])
            self.assertEqual(payload, (ROOT / item['file']).read_bytes())
            self.assertEqual(layout['memory_bytes'], item['memory_bytes'])
            audit = stack_audit((ROOT / item['assembly']).read_text(), symbols)
            self.assertEqual(audit['core_direct_call_bound_bytes'], item['core_direct_call_stack_bound_bytes'])
            self.assertLess(audit['core_direct_call_bound_bytes'], item['private_stack_bytes'])

    def test_reject_corrupt_elf_bounds_and_mapping(self):
        ph = self.header[4]
        for offset, value in ((18, 0), (24, self.base + 4), (ph + 4, len(self.raw)),
                              (ph + 8, self.base - 4), (ph + 12, self.base + 4),
                              (ph + 16, 32769), (ph + 20, 32769), (ph + 24, 6), (ph + 28, 3)):
            with self.subTest(offset=offset):
                damaged = bytearray(self.raw)
                struct.pack_into('<I', damaged, offset, value)
                with self.assertRaises(ValueError):
                    inspect_elf(damaged, self.base)
        for length in (0, 7, 51, self.header[5] + 16):
            with self.assertRaises(ValueError):
                inspect_elf(self.raw[:length], self.base)
        for i in range(self.header[11]):
            off = self.header[5] + i * 40
            section = struct.unpack_from('<10I', self.raw, off)
            if section[1] == 8 and section[2] & 2:
                damaged = bytearray(self.raw)
                struct.pack_into('<I', damaged, off + 12, self.base)
                with self.assertRaises(ValueError):
                    inspect_elf(damaged, self.base)
            if section[1] == 1 and section[2] & 2 and section[5]:
                damaged = bytearray(self.raw)
                struct.pack_into('<I', damaged, off + 16, section[4] + 1)
                with self.assertRaises(ValueError):
                    inspect_elf(damaged, self.base)

    def record(self):
        raw = bytearray(128)
        raw[:4], raw[124:] = b'HYE1', b'DONE'
        final = self.expected['block_results'][-1]
        fields = {4: 1, 8: self.base, 12: 32768, 16: 2, 20: 0, 24: 230, 28: 6, 32: 3,
                  36: final['output'], 40: final['sum'], 44: final['history'],
                  48: self.expected['replay_output_crc'], 52: 895, 56: 9135, 60: 888, 64: 9128,
                  68: self.item['record_address'], 72: 128, 76: self.report['build_tag'],
                  80: self.expected['fixture_crc32'], 84: 4096, 88: 1288, 92: 1,
                  96: self.expected['replay_history_crc'], 100: 14, 104: 230, 108: 1, 112: 0, 116: 1}
        for offset, value in fields.items():
            struct.pack_into('<I', raw, offset, value)
        struct.pack_into('<I', raw, 120, zlib.crc32(raw[:120]))
        return raw

    def validate(self, raw, runs=2):
        return validate_record(raw, self.expected, self.report['build_tag'], self.base,
                               self.item['record_address'], runs=runs)

    def test_semantic_record_corruption_even_with_valid_crc(self):
        raw = self.record()
        self.assertTrue(self.validate(raw)['verified'])
        for offset in range(4, 120, 4):
            if offset == 88:
                continue  # Stack high-water is observed, not a golden constant.
            damaged = bytearray(raw)
            damaged[offset] ^= 1
            struct.pack_into('<I', damaged, 120, zlib.crc32(damaged[:120]))
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.validate(damaged)
        for value in (0, 4097, 0xffffffff):
            damaged = bytearray(raw)
            struct.pack_into('<I', damaged, 88, value)
            struct.pack_into('<I', damaged, 120, zlib.crc32(damaged[:120]))
            with self.assertRaises(ValueError):
                self.validate(damaged)
        for offset in (0, 36, 120, 124):
            damaged = bytearray(raw)
            damaged[offset] ^= 1
            with self.assertRaises(ValueError):
                self.validate(damaged)
        with self.assertRaises(ValueError):
            self.validate(raw, runs=3)
        for length in (0, 64, 127):
            with self.assertRaises(ValueError):
                self.validate(raw[:length])

    def test_stack_audit_rejects_unknown_core_effects(self):
        _, symbols, _ = inspect_elf(self.raw, self.base)
        assembly = (ROOT / self.item['assembly']).read_text()
        address = symbols['core']['address']
        for instruction in ('call r3', 'sp = r2'):
            damaged, count = re.subn(r'(^\s*' + format(address, 'x') + r':\s+(?:[0-9a-f]{2}\s+)+).*$',
                                    r'\g<1>' + instruction, assembly, count=1, flags=re.M)
            self.assertEqual(count, 1)
            with self.assertRaises(ValueError):
                stack_audit(damaged, symbols)


if __name__ == '__main__':
    unittest.main(verbosity=2)
