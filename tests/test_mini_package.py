"""Experimental MINI image composition: memory spaces, CRCs and provenance."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from hyperrig.jieli import crc16, sfc, unpack_app
from package_mini_probe import build_application, flatten_elf, verify_application
from test_mini_image import elf_fixture, ENTRY, RAM_START

STOCK = ROOT / "artifacts/tank-mini/TANK-MINI.fwsc"


class FlattenTests(unittest.TestCase):
    def test_ram_data_uses_flash_lma_and_nobits_is_omitted(self):
        data, _ = flatten_elf(elf_fixture())
        self.assertEqual(data, bytes(range(32)))

    def test_alignment_tail_is_erased(self):
        data, _ = flatten_elf(elf_fixture(symbols={"__flash_image_end": ENTRY + 36}))
        self.assertEqual(data, bytes(range(32)) + b"\xff" * 4)

    def test_unlinked_and_wrong_entry_are_rejected(self):
        for offset, value, fmt in ((16, 1, "<H"), (24, ENTRY + 4, "<I")):
            raw = elf_fixture()
            struct.pack_into(fmt, raw, offset, value)
            with self.assertRaises(ValueError):
                flatten_elf(raw)


@unittest.skipUnless(STOCK.exists(), "fetch pinned MINI stock package first")
class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = STOCK.read_bytes()
        cls.elf = bytes(elf_fixture())
        cls.packed, cls.report = build_application(cls.elf, cls.stock)

    def test_layout_and_contents(self):
        plain, entries, files = unpack_app(self.packed)
        self.assertEqual(len(self.packed), 0x7E000)
        self.assertEqual(entries[0].offset, ENTRY)
        self.assertEqual(files["app.bin"], bytes(range(32)))
        self.assertEqual(plain[0x140:0x7CD58], b"\xff" * (0x7CD58 - 0x140))
        regions = {e.name: (e.offset, e.size) for e in entries}
        self.assertEqual(regions["VM"], (0x82000, 0x3C000))
        self.assertEqual(regions["BTIF"], (0xBE000, 0x1000))
        self.assertFalse(self.report["boot_verified_on_device"])
        self.assertFalse(self.report["installable_update_package"])
        self.assertTrue(all(self.report["checks"].values()))

    def test_cipher_and_header_corruption_rejected(self):
        for offset in (0, 16, 32, 0x120, 0x200, 0x7CD58):
            with self.subTest(offset=offset):
                bad = bytearray(self.packed)
                bad[offset] ^= 1
                with self.assertRaises(ValueError):
                    verify_application(bad, self.elf, self.stock)

    def test_crc_valid_but_different_program_rejected(self):
        plain, entries, _ = unpack_app(self.packed)
        plain = bytearray(plain)
        plain[0x123] ^= 1
        struct.pack_into("<H", plain, 34, crc16(plain[0x120:0x140]))
        struct.pack_into("<H", plain, 32, crc16(plain[34:64]))
        struct.pack_into("<H", plain, 2, crc16(plain[32:entries[0].size]))
        struct.pack_into("<H", plain, 0, crc16(plain[2:32]))
        cipher_end = (entries[0].size + 31) & ~31
        bad = sfc(bytes(plain[:cipher_end])) + bytes(plain[cipher_end:])
        unpack_app(bad)  # All container CRCs are valid; the ELF must still match.
        with self.assertRaisesRegex(ValueError, "differ from ELF"):
            verify_application(bad, self.elf, self.stock)

    def test_config_overlap_is_rejected(self):
        elf = elf_fixture(symbols={"__flash_image_end": 0x0207CD5C})
        with self.assertRaisesRegex(ValueError, "overlaps.*cfg_tool"):
            build_application(elf, self.stock)

    def test_crc_valid_app_config_overlap_is_rejected_by_verifier(self):
        plain, entries, files = unpack_app(self.packed)
        directory = {entry.name: entry for entry in entries}
        app, config, head = (directory[name] for name in ("app.bin", "cfg_tool.bin", "app_area_head"))
        # A valid monolithic flash segment includes the unchanged config bytes
        # at its tail. Both JLFS files then pass their CRCs while overlapping.
        program = files["app.bin"] + b"\xff" * (config.offset - app.offset - len(files["app.bin"]))
        program += files["cfg_tool.bin"]
        elf = elf_fixture(symbols={"__ram_end": RAM_START,
                                  "__ram_load_start": ENTRY, "__ram_load_end": ENTRY,
                                  "__bss_start": RAM_START,
                                  "__flash_image_end": ENTRY + len(program)})
        shoff = struct.unpack_from("<I", elf, 32)[0]
        payload_offset = (len(elf) + 3) & ~3
        struct.pack_into("<8I", elf, 52, 1, payload_offset, ENTRY, ENTRY,
                         len(program), len(program), 5, 4)
        # Keep the fixture's RAM span as NOBITS only, with an empty copy span.
        struct.pack_into("<8I", elf, 84, 1, 0, RAM_START, 0, 0, 32, 6, 4)
        struct.pack_into("<I", elf, shoff + 40 + 16, payload_offset)
        struct.pack_into("<I", elf, shoff + 80 + 4, 8)
        struct.pack_into("<I", elf, shoff + 80 + 16, 0)
        elf.extend(b"\0" * (payload_offset - len(elf)))
        elf.extend(program)
        self.assertEqual(flatten_elf(elf)[0], program)  # ELF/layout is valid.

        plain = bytearray(plain)
        plain[app.offset:app.offset + len(program)] = program
        struct.pack_into("<I", plain, app.header_offset + 8, len(program))
        struct.pack_into("<H", plain, app.header_offset + 2, crc16(program))
        struct.pack_into("<H", plain, app.header_offset,
                         crc16(plain[app.header_offset + 2:app.header_offset + 32]))
        struct.pack_into("<H", plain, 2, crc16(plain[32:head.size]))
        struct.pack_into("<H", plain, 0, crc16(plain[2:32]))
        cipher_end = (head.size + 31) & ~31
        packed = sfc(bytes(plain[:cipher_end])) + bytes(plain[cipher_end:])
        _, _, reparsed = unpack_app(packed)  # Header and both payload CRCs pass.
        self.assertEqual(reparsed["app.bin"], program)
        self.assertEqual(reparsed["cfg_tool.bin"], files["cfg_tool.bin"])
        with self.assertRaisesRegex(ValueError, "overlaps.*cfg_tool"):
            verify_application(packed, elf, self.stock)

    def test_stock_corruption_is_rejected(self):
        bad = bytearray(self.stock)
        bad[-1] ^= 1
        with self.assertRaises(ValueError):
            build_application(self.elf, bad)


if __name__ == "__main__":
    unittest.main()
