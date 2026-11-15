"""ELF/linker contract and cross-board application checks, without devices."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_mini_image import (APP_END, APP_START, BOOT_RESERVED_END, ENTRY, FLASH_END,
                              RAM_END, RAM_START, inspect_application, inspect_elf, inspect_stock)


def elf_fixture(*, symbols=None, undefined=None):
    """Two PT_LOADs: flash text and initialized RAM followed by 16 B BSS."""
    values = {"__ram_start": RAM_START, "__ram_end": RAM_START + 16,
              "__ram_load_start": ENTRY + 16, "__ram_load_end": ENTRY + 32,
              "__bss_start": RAM_START + 16, "__bss_end": RAM_START + 32,
              "__stack_bottom": RAM_END - 0x2000, "__stack_top": RAM_END - 0x1000,
              "__ssp_bottom": RAM_END - 0x1000, "__ssp_top": RAM_END,
              "__boot_reserved_start": RAM_END, "__boot_reserved_end": BOOT_RESERVED_END,
              "__flash_image_end": ENTRY + 32,
              "__noinit_start": RAM_START + 32, "__noinit_end": RAM_START + 32,
              "__ram_region_start": RAM_START, "__ram_region_end": RAM_END}
    values.update(symbols or {})
    strings, symbols_raw = bytearray(b"\0"), bytearray(16)
    for name, value in values.items():
        if value is None:
            continue
        offset = len(strings)
        strings.extend(name.encode() + b"\0")
        symbols_raw.extend(struct.pack("<IIIBBH", offset, value, 0, 0x10, 0, 0xFFF1))
    if undefined:
        offset = len(strings)
        strings.extend(undefined.encode() + b"\0")
        symbols_raw.extend(struct.pack("<IIIBBH", offset, 0, 0, 0x10, 0, 0))
    blob = bytearray(0x120)
    blob[0x100:0x120] = bytes(range(32))
    symbol_offset = len(blob)
    blob.extend(symbols_raw)
    string_offset = len(blob)
    blob.extend(strings)
    while len(blob) % 4:
        blob.append(0)
    shoff = len(blob)
    sections = [(0,) * 10,
                (0, 1, 6, ENTRY, 0x100, 16, 0, 0, 4, 0),
                (0, 1, 3, RAM_START, 0x110, 16, 0, 0, 4, 0),
                (0, 8, 3, RAM_START + 16, 0, 16, 0, 0, 4, 0),
                (0, 2, 0, 0, symbol_offset, len(symbols_raw), 5, 1, 4, 16),
                (0, 3, 0, 0, string_offset, len(strings), 0, 0, 1, 0)]
    for section in sections:
        blob.extend(struct.pack("<10I", *section))
    blob[:16] = b"\x7fELF\x01\x01\x01" + bytes(9)
    struct.pack_into("<HHIIIIIHHHHHH", blob, 16, 2, 0xF1, 1, ENTRY, 52, shoff, 0, 52, 32, 2, 40, len(sections), 5)
    struct.pack_into("<8I", blob, 52, 1, 0x100, ENTRY, ENTRY, 16, 16, 5, 4)
    struct.pack_into("<8I", blob, 84, 1, 0x110, RAM_START, ENTRY + 16, 16, 32, 6, 4)
    return blob


class MiniElfTests(unittest.TestCase):
    def test_linked_layout_passes_without_claiming_boot_or_flashability(self):
        result = inspect_elf(bytes(elf_fixture()))
        self.assertTrue(result["layout_valid"])
        self.assertFalse(result["flashable"])
        self.assertFalse(result["boot_verified_on_device"])
        self.assertEqual(result["file_backed_flash_bytes"], 32)

    def test_relocatable_and_wrong_cpu_rejected(self):
        for offset, value, message in ((16, 1, "linked executable"), (18, 40, "pi32v2")):
            raw = elf_fixture()
            struct.pack_into("<H", raw, offset, value)
            with self.assertRaisesRegex(ValueError, message):
                inspect_elf(raw)

    def test_segment_escape_truncation_and_overlap_rejected(self):
        mutations = ((84 + 8, RAM_END - 16, "VMA"),
                     (84 + 12, FLASH_END - 4, "flash LMA"),
                     (84 + 4, 0xFFFFFFF0, "outside ELF"),
                     (84 + 16, 64, "exceed memory"),
                     (84 + 12, ENTRY, "overlapping.*LMAs"))
        for offset, value, message in mutations:
            with self.subTest(message=message):
                raw = elf_fixture()
                struct.pack_into("<I", raw, offset, value)
                with self.assertRaisesRegex(ValueError, message):
                    inspect_elf(raw)

    def test_boot_contract_and_unresolved_runtime_rejected(self):
        cases = (({"__ram_load_end": ENTRY + 36}, "lengths differ"),
                 ({"__bss_start": RAM_START}, "erase initialized"),
                 ({"__stack_top": RAM_END}, "stack ranges overlap"),
                 ({"__ssp_top": BOOT_RESERVED_END}, "stack leaves"),
                 ({"__boot_reserved_start": RAM_END + 4}, "boot-reserved"),
                 ({"__flash_image_end": ENTRY + 4}, "flash image end"),
                 ({"__ram_start": None}, "missing MINI linker"))
        for symbols, message in cases:
            with self.subTest(symbols=symbols):
                with self.assertRaisesRegex(ValueError, message):
                    inspect_elf(elf_fixture(symbols=symbols))
        with self.assertRaisesRegex(ValueError, "unresolved symbols: memcpy"):
            inspect_elf(elf_fixture(undefined="memcpy"))

    def test_truncated_headers_sections_and_wrong_entry_rejected(self):
        for length in (0, 16, 51, 100, 300):
            with self.assertRaises(ValueError):
                inspect_elf(elf_fixture()[:length])
        raw = elf_fixture()
        struct.pack_into("<I", raw, 24, ENTRY + 4)
        with self.assertRaisesRegex(ValueError, "entry is not"):
            inspect_elf(raw)

    def test_ram_copy_cannot_extend_beyond_actual_load_bytes(self):
        # Both sizes still match and every individual segment is inside them;
        # the final four bytes nevertheless have no ELF source payload.
        raw = elf_fixture(symbols={"__ram_end": RAM_START + 20, "__ram_load_end": ENTRY + 36})
        with self.assertRaisesRegex(ValueError, "not fully backed"):
            inspect_elf(raw)

    def test_nobits_cannot_escape_startup_clear_or_noinit_contract(self):
        raw = elf_fixture(symbols={"__bss_end": RAM_START + 28})
        with self.assertRaisesRegex(ValueError, "NOBITS.*initialization contract"):
            inspect_elf(raw)
        raw = elf_fixture(symbols={"__noinit_start": RAM_START + 20, "__noinit_end": RAM_START + 24})
        with self.assertRaisesRegex(ValueError, "noinit overlaps"):
            inspect_elf(raw)


STOCK = ROOT / "artifacts/tank-mini/TANK-MINI.fwsc"


@unittest.skipUnless(STOCK.exists(), "fetch the pinned stock firmware first")
class MiniPackageTests(unittest.TestCase):
    def test_pinned_stock_crc_and_incomplete_flash_backup(self):
        result = inspect_stock(STOCK.read_bytes())
        self.assertTrue(result["pinned_stock_verified"])
        self.assertEqual(result["flash_bytes_in_package"], APP_END)
        self.assertFalse(result["complete_device_flash_backup"])
        self.assertEqual(result["ota_payload_name"], "usb_hid_ota.bin")
        self.assertEqual(result["opaque_auxiliary_raw_crc_mismatches"], ["isd_config.ini", "script.ver", "blimit.bin"])

    def test_flash_payload_corruption_is_rejected(self):
        data = bytearray(STOCK.read_bytes())
        data[1044 + APP_START + 512] ^= 1
        with self.assertRaisesRegex(ValueError, "flash.bin CRC"):
            inspect_stock(data)

    def test_g_image_cannot_be_used_as_mini_application_even_if_padded(self):
        g = ROOT / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
        if not g.exists():
            self.skipTest("fetch pinned G firmware first")
        data = g.read_bytes()
        with self.assertRaisesRegex(ValueError, "MINI.*size"):
            inspect_application(data)
        data += b"\xff" * (APP_END - APP_START - len(data))
        with self.assertRaisesRegex(ValueError, "VM differs from the MINI memory map"):
            inspect_application(data)


if __name__ == "__main__":
    unittest.main()
