"""Assemble pi32v2 source like JieLi's assembler, except where a line names the encoding it must keep.

The firmware build assembles code that the original toolchain encoded in forms JieLi's assembler does not
choose for the same text (the 6-byte call between flash and RAM, a long stack access, the other flavour of a
compare-with-constant block). A line keeps such a form with a hint in its comment, the form identifier of the pi32v2
instruction table:

    call A01c00cc0  ; @call.xl

JieLi's assembler ignores the comment and picks its own form; this one keeps only the readings of that form, and
fails if the line has none. Lines without a hint are assembled exactly as upstream/pi32v2-isa's assembler does, which
chooses encodings like JieLi's (its docs/ASSEMBLER.md). The upstream package is used unchanged.

Usage: python -B tools/pi32v2_form_asm.py IN.s -o OUT.o
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from pi32v2isa import codec  # noqa: E402
from pi32v2isa.asm import TIE, AsmError, Assembler  # noqa: E402

HINT = re.compile(r';\s*@([A-Za-z0-9_.]+)\s*$')


class FormAssembler(Assembler):
    """The upstream assembler with per-line form hints."""

    def collect_hints(self, text, filename):
        self.hints.update({(filename, n): m.group(1) for n, line in enumerate(text.split('\n'), 1)
                           if (m := HINT.search(line))})

    def assemble(self, text, filename='<input>'):
        self.hints, self.used_hints, self.read_lines = {}, set(), set()
        self.unhinted, self.fallbacks = {}, []
        self.collect_hints(text, filename)
        super().assemble(text, filename)

    def layout(self):
        """As upstream; but when no reading of a hinted line fits any longer (a change moved a branch target out of
        reach of the kept short form), that line takes the readings it would have without its hint, and the
        fallback is recorded in self.fallbacks. Without the hint the original bytes were not needed there."""
        while True:
            try:
                return super().layout()
            except AsmError as error:
                loc = str(error).split(': no encoding fits', 1)[0]
                if ': no encoding fits' not in str(error) or loc not in self.unhinted:
                    raise
                item = next(i for sec in self.order for i in sec.items if getattr(i, 'loc', None) == loc
                            and getattr(i, 'cands', None))
                form = item.cands[0].insn.id
                cands = self.unhinted.pop(loc)
                if not item.fixed_const:          # as upstream: a symbolic constant takes the 32-bit form
                    cands = [c for c in cands if self.isa.abs32.get(c.insn.id)] or cands
                item.cands = sorted(cands, key=lambda c: (c.size, c.alias, TIE.get(c.insn.id.removesuffix('.p'), 0),
                                                          c.order))
                item.cur, item.chosen = item.cands[0].size, item.cands[0]
                self.fallbacks.append({'line': loc, 'hinted_form': form})

    def d_include(self, rest):
        """As upstream (the file is found the same way), collecting the hints of the included file first."""
        from pi32v2isa.asm import parse_string
        path = self._find(parse_string(rest).decode())
        if path is not None:
            with open(path, encoding='utf-8') as f:
                self.collect_hints(f.read(), path)
        super().d_include(rest)

    def statement(self, line):
        """As upstream; records the lines read, so that a hint in a branch of .if that is not assembled is not
        reported as stray."""
        filename, number = self.loc.rsplit(':', 1)
        self.read_lines.add((filename, int(number)))
        super().statement(line)

    def parsed_candidates(self, line):
        good, err = super().parsed_candidates(line)
        filename, number = self.loc.rsplit(':', 1)
        key = (filename, int(number))
        form = self.hints.get(key)
        if form is None:
            return good, err
        kept = [c for c in good if c.insn.id == form]
        if not kept:
            return [], AsmError(f'{self.loc}: no reading of the line has the form {form}')
        self.used_hints.add(key)
        self.unhinted[self.loc] = good
        return kept, err

    def encode_cand(self, item, cand, off):
        """As upstream, but a call.xl kept by a hint may reach a symbol of another section: the 6-byte call between
        flash and RAM code, with relocation type 4 (R_PI32V2_EXTEND_CALL_32M2, docs/ELF.md), which JieLi's linker
        and the upstream linker resolve. JieLi's assembler never writes it from source; the compiler does."""
        if cand.insn.id == 'call.xl':
            field = self.isa.branch['call.xl']
            self.variant = None
            sym, add = self.ev(cand.ops[field].node, item.loc)
            pos = self.sym_pos(sym) if sym is not None else None
            if sym is not None and not (pos and pos[0] is item.sec and sym.kind != 'undef'):
                values = {name: op for name, op in cand.ops.items() if name != field}
                values[field] = 0
                return bytes(codec.encode(cand.insn, values)), (4, self.reloc_symbol(sym), add)
        return super().encode_cand(item, cand, off)

    def finish(self):
        data = super().finish()
        unused = sorted((set(self.hints) & self.read_lines) - self.used_hints)
        if unused:
            raise AsmError(f'form hints on lines that are not instructions: {unused[:10]}')
        return data


def assemble(text, filename='<input>'):
    """The ELF relocatable object of one source text, as bytes."""
    assembler = FormAssembler()
    assembler.assemble(text, filename)
    return assembler.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input', type=Path)
    parser.add_argument('-o', '--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        data = assemble(args.input.read_bytes().decode('utf-8'), str(args.input))
    except AsmError as error:
        raise SystemExit(f'error: {error}')
    args.output.write_bytes(data)


if __name__ == '__main__':
    main()
