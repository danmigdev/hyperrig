"""Form hints of tools/pi32v2_form_asm.py: a hint keeps its form, a wrong or stray hint fails, a hinted call.xl may
reach another section through relocation type 4, and hints work in included files."""
import io
import sys
import tempfile
import unittest
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from pi32v2_form_asm import FormAssembler, assemble  # noqa: E402
from pi32v2isa import codec, table  # noqa: E402
from pi32v2isa.asm import AsmError  # noqa: E402

INSTRUCTIONS = table.load()


def text_section(obj, name='.text'):
    return ELFFile(io.BytesIO(obj)).get_section_by_name(name).data()


def forms(data):
    out, cursor = [], 0
    while cursor < len(data):
        instruction, fields, size = codec.decode(INSTRUCTIONS, data, cursor)
        out.append((instruction.id, size))
        cursor += size
    return out


class FormHints(unittest.TestCase):
    def test_default_form_without_a_hint(self):
        self.assertEqual(forms(text_section(assemble('.text\n    r2 += 1\n'))), [('add.rri', 2)])

    def test_hint_keeps_its_form(self):
        self.assertEqual(forms(text_section(assemble('.text\n    r2 += 1  ; @add.ri.u5\n'))), [('add.ri.u5', 2)])

    def test_a_hinted_short_branch_out_of_reach_falls_back_with_a_record(self):
        near = '.text\n    goto far  ; @goto.s\n    .space 64\nfar:\n    rts\n'
        far = near.replace('.space 64', '.space 8192')
        self.assertEqual(forms(text_section(assemble(near))[:2]), [('goto.s', 2)])
        assembler = FormAssembler()
        assembler.assemble(far, 'far.s')
        data = text_section(assembler.finish())
        self.assertEqual(forms(data[:4]), [('goto.l', 4)])
        self.assertEqual(assembler.fallbacks, [{'line': 'far.s:2', 'hinted_form': 'goto.s'}])
        none = FormAssembler()
        none.assemble(near, 'near.s')
        none.finish()
        self.assertEqual(none.fallbacks, [])

    def test_long_stack_store_kept(self):
        data = text_section(assemble('.text\n    [sp+24] = r15  ; @st.w.sp.l\n'))
        self.assertEqual(forms(data), [('st.w.sp.l', 4)])

    def test_hint_that_the_line_cannot_have_fails(self):
        with self.assertRaises(AsmError):
            assemble('.text\n    r2 += 1  ; @call.xl\n')

    def test_hint_on_a_line_that_is_not_an_instruction_fails(self):
        with self.assertRaises(AsmError):
            assemble('.text\nhere:  ; @add.ri.u5\n    nop\n')

    def test_hinted_call_xl_to_another_section_gets_relocation_type_4(self):
        obj = assemble('.section .a,"ax",@progbits\n    call far  ; @call.xl\n'
                       '.section .b,"ax",@progbits\n.global far\nfar:\n    rts\n')
        elf = ELFFile(io.BytesIO(obj))
        self.assertEqual(forms(elf.get_section_by_name('.a').data()), [('call.xl', 6)])
        relocations = list(elf.get_section_by_name('.rela.a').iter_relocations())
        self.assertEqual([(r['r_offset'], r['r_info_type']) for r in relocations], [(0, 4)])

    def test_unhinted_call_to_another_section_is_the_4_byte_form(self):
        obj = assemble('.section .a,"ax",@progbits\n    call far\n'
                       '.section .b,"ax",@progbits\n.global far\nfar:\n    rts\n')
        self.assertEqual(forms(text_section(obj, '.a')), [('call.l', 4)])

    def test_hint_in_a_branch_that_is_not_assembled_is_ignored(self):
        source = '.text\n.set T, {}\n.if T\n    r2 += 1  ; @add.ri.u5\n.else\n    r2 += 1\n.endif\n'
        self.assertEqual(forms(text_section(assemble(source.format(0)))), [('add.rri', 2)])
        self.assertEqual(forms(text_section(assemble(source.format(1)))), [('add.ri.u5', 2)])

    def test_hints_in_an_included_file(self):
        with tempfile.TemporaryDirectory() as directory:
            piece = Path(directory) / 'piece.s'
            piece.write_bytes(b'    r2 += 1  ; @add.ri.u5\n    r3 += 1\n')
            master = Path(directory) / 'master.s'
            master.write_bytes(b'.text\n.include "piece.s"\n')
            assembler = FormAssembler(include=[directory])
            assembler.assemble(master.read_text(encoding='utf-8'), str(master))
            data = text_section(assembler.finish())
        self.assertEqual(forms(data), [('add.ri.u5', 2), ('add.rri', 2)])


if __name__ == '__main__':
    unittest.main()
