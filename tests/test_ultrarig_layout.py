"""The linker script of firmware/ultrarig (app.ld) places every section after
the one before it, whatever their sizes: tiny units linked by the upstream linker, at the original sizes' residues and
grown by 2 bytes, and the app.bin of build_ultrarig_app.image_of."""
import io
import sys
import tempfile
import unittest
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from build_ultrarig_app import image_of, layout_of  # noqa: E402
from pi32v2_form_asm import assemble  # noqa: E402
from pi32v2isa.ld import link, parse_args  # noqa: E402


def unit(section, flags, body):
    return f'.section {section},"{flags}",@progbits\n{body}\n'


def layout(flash_bytes, ram_bytes, bss_bytes=64, elf_out=None):
    """Link units of the given sizes; ({symbol: value}, {section: (vma, lma)}, app.bin)."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        sources = {
            'flash': unit('.flash', 'ax', '.global start\nstart:\n    rts\n' + '    nop\n' * ((flash_bytes - 2) // 2)),
            'ram': unit('.ram', 'ax', '    rts\n' + '    nop\n' * ((ram_bytes - 2) // 2)) +
            f'.section .bss,"aw",@nobits\nfirst:\n    .space {bss_bytes}\n',
            'tail': unit('.tail', 'a', '    .long start'),
        }
        for name, text in sources.items():
            (d / f'{name}.o').write_bytes(assemble(text, f'{name}.s'))
        (d / 'app.ld').write_text((ROOT / 'firmware/ultrarig/app.ld').read_text(encoding='ascii'), encoding='ascii')
        linker, data = link(parse_args(['-T', str(d / 'app.ld'), *(str(d / f'{n}.o') for n in sources),
                                        '-o', str(d / 'app.elf')]))
        if data is None:
            raise AssertionError('; '.join(linker.errors))
    if elf_out is not None:
        elf_out.append(data)
    elf = ELFFile(io.BytesIO(data))
    syms = {s.name: s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s.name}
    sections = {}
    for name in ('.flash', '.ram', '.bss', '.tail'):
        sec = elf.get_section_by_name(name)
        seg = next((s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD' and
                    s['p_vaddr'] <= sec['sh_addr'] < s['p_vaddr'] + max(s['p_memsz'], 1)), None)
        sections[name] = (sec['sh_addr'], seg['p_paddr'] + sec['sh_addr'] - seg['p_vaddr'] if seg else None)
    return syms, sections, image_of(data)


class Layout(unittest.TestCase):
    def check(self, flash_bytes, ram_bytes):
        syms, sections, app = layout(flash_bytes, ram_bytes)
        flash_end = 0x02000120 + flash_bytes
        ram_load = (flash_end + 3) & ~3
        self.assertEqual(syms['ultrarig_flash_text_end'], flash_end)
        self.assertEqual(sections['.ram'], (0x01C00000, ram_load))
        self.assertEqual(syms['ultrarig_ram_image_load'], ram_load)
        self.assertEqual(syms['ultrarig_ram_image_size'], ram_bytes)
        bss = sections['.bss'][0]
        self.assertGreaterEqual(bss, 0x01C00000 + ram_bytes)
        self.assertLess(bss, 0x01C00000 + ram_bytes + 32)
        self.assertEqual(bss % 32, 0x0C, 'the bss keeps the original start modulo 32')
        self.assertEqual(syms['ultrarig_heap_start'], (bss + 64 + 31) & ~31)
        tail = (ram_load + ram_bytes + 3) & ~3
        self.assertEqual(sections['.tail'], (tail, tail))
        self.assertEqual(len(app), tail + 4 - 0x02000120)
        self.assertEqual(app[tail - 0x02000120:], (0x02000120).to_bytes(4, 'little'))
        self.assertEqual(app[flash_end - 0x02000120:ram_load - 0x02000120], bytes(ram_load - flash_end))

    def test_original_residues(self):
        # The original flash text and RAM image sizes modulo 32: 0x56660 and 0x2030C.
        self.check(0x60, 0x2C)

    def test_grown_by_two(self):
        self.check(0x62, 0x2E)

    def test_mini_entries_are_provided(self):
        syms, _, _ = layout(0x60, 0x2C)
        self.assertNotIn('hyperrig_mini_entry_guard_v2', syms)    # PROVIDE: only when referenced

    def test_layout_report_gives_the_heap(self):
        elf = []
        syms, _, _ = layout(0x60, 0x2E, elf_out=elf)
        report = layout_of(elf[0])
        self.assertEqual(report['heap_end'], '0x01c7fba0')
        self.assertEqual(report['ram_image_size'], 0x2E)
        self.assertEqual(report['heap_bytes'], 0x01C7FBA0 - syms['ultrarig_heap_start'])


if __name__ == '__main__':
    unittest.main()
