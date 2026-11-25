"""Build the UltraRig application file app.bin from its source tree, without reading any image.

firmware/ultrarig/ holds the source: flash.s, ram.s and tail.s with the pieces they include, and the linker script
app.ld. Each unit is assembled by tools/pi32v2_form_asm.py (the upstream pi32v2-isa assembler with form hints) and
linked by the upstream linker; app.bin is the flash text, the RAM image and the trailing table, each at its load
address (app.ld places them one after the other, so a change of size moves what follows). --expect requires a
SHA-256 for app.bin: the source as generated rebuilds the original G alpha11 v2/M5.71 app.bin,
4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e. --jieli-ld links the same objects with JieLi's ld as
well (WSL) and requires the same bytes.

Offline: app.bin is the application file of the JLFS area, not a flashable package, and nothing here is a hardware
or audio test.

Usage, from the repository root:
    python -B tools/build_ultrarig_app.py --output build/ultrarig-app-01 [--source firmware/ultrarig]
        [--target g|mini] [--expect SHA256] [--jieli-ld] [--distro Ubuntu]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from pi32v2_form_asm import FormAssembler  # noqa: E402
from pi32v2isa.asm import AsmError  # noqa: E402
from pi32v2isa.ld import link, parse_args  # noqa: E402

UNITS = ('flash', 'ram', 'tail')
BASE = 0x02000120                # the load address of app.bin: the start of the flash text
LAYOUT = ('flash_text_end', 'ram_image_load', 'ram_image_size', 'bss_start', 'bss_size', 'heap_start', 'heap_end',
          'app_end')
SECTIONS = ('.flash', '.ram', '.tail')
TOOLCHAIN = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def assemble(path, target='g', fallbacks=None, options=()):
    """The ELF object of one unit; its .include files are found next to it. The MINI target assembles a wrapper
    that sets TARGET_MINI, and each name of options (MINI_PRODUCT), and includes the unit, so that the unit's line
    numbers stay those of its file. fallbacks,
    a list, receives the hinted lines that no longer fit their form (tools/pi32v2_form_asm.py)."""
    assembler = FormAssembler(include=[str(path.parent)])
    if target == 'mini':
        sets = ''.join(f'.set {name}, 1\n' for name in ('TARGET_MINI', *options))
        assembler.assemble(f'{sets}.include "{path.name}"\n', str(path.parent / 'target-mini.s'))
    else:
        assembler.assemble(path.read_bytes().decode('utf-8'), str(path))
    data = assembler.finish()
    if fallbacks is not None:
        fallbacks.extend(assembler.fallbacks)
    return data


def moved_labels(elf_data):
    """Where the code starts to differ from the original: each L<address> label is named after its original
    address. {labels: n, moved: m, first_moved: original address, its shift}."""
    elf = ELFFile(io.BytesIO(elf_data))
    moved, total = [], 0
    for symbol in elf.get_section_by_name('.symtab').iter_symbols():
        name = symbol.name
        if len(name) == 9 and name[0] == 'L' and all(c in '0123456789abcdef' for c in name[1:]):
            total += 1
            original = int(name[1:], 16)
            if symbol['st_value'] != original:
                moved.append((original, symbol['st_value'] - original))
    first = min(moved) if moved else None
    return {'labels': total, 'moved': len(moved),
            'first_moved': f'0x{first[0]:08x}' if first else None, 'first_shift': first[1] if first else 0}


def image_of(elf_data, sections=SECTIONS):
    """app.bin of a linked ELF: .flash, .ram and .tail (or the given sections) at their load addresses from the
    first, gaps zero."""
    elf = ELFFile(io.BytesIO(elf_data))
    loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD' and s['p_filesz']]
    parts = []
    for name in sections:
        sec = elf.get_section_by_name(name)
        seg = next(s for s in loads if s['p_vaddr'] <= sec['sh_addr'] < s['p_vaddr'] + s['p_filesz'])
        parts.append((seg['p_paddr'] + sec['sh_addr'] - seg['p_vaddr'], sec.data()))
    base, out = parts[0][0], bytearray()
    for lma, data in parts:
        if lma - base < len(out):
            raise SystemExit(f'sections overlap at load address 0x{lma:08x}')
        out += bytes(lma - base - len(out)) + data
    return bytes(out)


def layout_of(elf_data):
    """The bounds app.ld defines (ultrarig_*), and the size of the heap between the bss and its fixed end."""
    elf = ELFFile(io.BytesIO(elf_data))
    found = {s.name[len('ultrarig_'):]: s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()
             if s.name.startswith('ultrarig_') and s['st_shndx'] != 'SHN_UNDEF'
             and s.name[len('ultrarig_'):] in LAYOUT}
    out = {name: f'0x{found[name]:08x}' if 'size' not in name else found[name] for name in LAYOUT if name in found}
    if 'heap_start' in found and 'heap_end' in found:
        out['heap_bytes'] = found['heap_end'] - found['heap_start']
    return out


def outside_names(out):
    """The names the units use that no unit and no assignment of app.ld defines: code linked with the application
    in the MINI image (tools/build_hyperrig_mini_image.py), such as a C function that a MINI change calls."""
    defined, used = set(), set()
    for name in UNITS:
        for symbol in ELFFile(io.BytesIO((out / f'{name}.o').read_bytes())).get_section_by_name('.symtab') \
                .iter_symbols():
            if symbol.name and symbol['st_info']['type'] not in ('STT_FILE', 'STT_SECTION'):
                (used if symbol['st_shndx'] == 'SHN_UNDEF' else defined).add(symbol.name)
    script = (out / 'app.ld').read_bytes().decode('utf-8')
    assigned = set(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*=[^=]', script))
    return sorted(used - defined - assigned)


def build(source, out, target='g', symbols=None, fallbacks=None, placeholder=None, options=()):
    """Assemble the units of a source tree for a target (g or mini) into out, link them and return app.bin.
    symbols: {name: address} defined for the link (--defsym), such as the entries of the code the MINI image
    appends; app.ld provides defaults. fallbacks: a list that receives the hint fallbacks of the units.
    placeholder: an address given to every name outside the application (outside_names), for a link of the
    application alone whose only use is its own addresses; without it such a name fails the link.
    options: the options of the MINI target to set (assemble)."""
    out.mkdir(parents=True, exist_ok=True)
    for name in UNITS:
        (out / f'{name}.o').write_bytes(assemble(source / f'{name}.s', target, fallbacks, options))
    shutil.copyfile(source / 'app.ld', out / 'app.ld')
    symbols = dict(symbols or {})
    if placeholder is not None:
        symbols.update({name: placeholder for name in outside_names(out) if name not in symbols})
    defsyms = [f'--defsym={k}=0x{v:08x}' for k, v in sorted(symbols.items())]
    linker, data = link(parse_args(['-T', str(out / 'app.ld'), *defsyms, *(str(out / f'{n}.o') for n in UNITS),
                                    '-o', str(out / 'app.elf'), '-Map', str(out / 'app.map')]))
    if data is None:
        raise SystemExit('link failed: ' + '; '.join(linker.errors[:10]))
    (out / 'app.elf').write_bytes(data)
    return image_of(data)


def jieli_link(out, distro, symbols=None):
    """app.bin from the same objects linked by JieLi's ld."""
    rel = out.relative_to(ROOT).as_posix()
    up = '../' * len(Path(rel).parts)
    defsyms = ' '.join(f'--defsym={k}=0x{v:08x}' for k, v in sorted((symbols or {}).items()))
    step = f'{up}{TOOLCHAIN}ld -T app.ld {defsyms} {" ".join(f"{n}.o" for n in UNITS)} -o jieli.elf'
    prefix = ['wsl.exe', '--distribution', distro, '--exec'] if os.name == 'nt' else []
    done = subprocess.run(prefix + ['sh', '-c', f'cd {rel} && {step}'], cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        raise SystemExit(f'JieLi link failed: {done.stdout}{done.stderr}')
    return image_of((out / 'jieli.elf').read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=Path('firmware/ultrarig'))
    parser.add_argument('--target', choices=('g', 'mini'), default='g',
                        help='g: the original application; mini: with the HyperRig MINI changes (TARGET_MINI)')
    parser.add_argument('--expect', help='required SHA-256 of app.bin')
    parser.add_argument('--jieli-ld', action='store_true', help="also link with JieLi's ld and compare")
    parser.add_argument('--distro', default='Ubuntu')
    args = parser.parse_args()
    out, source = (ROOT / args.output).resolve(), (ROOT / args.source).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        parser.error('use a fresh directory under build/')
    files = sorted(p for p in source.rglob('*') if p.is_file())
    # The upstream assembler reads included files in the platform's default encoding: the source stays ASCII.
    wide = [p.relative_to(ROOT).as_posix() for p in files if not p.read_bytes().isascii()]
    if wide:
        raise SystemExit(f'source files must be ASCII: {wide[:5]}')
    before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in files}
    fallbacks = []
    try:
        app = build(source, out, args.target, fallbacks=fallbacks)
    except AsmError as error:
        raise SystemExit(f'assembly failed: {error}')
    for item in fallbacks:
        print(f"warning: {item['line']}: the hinted form {item['hinted_form']} no longer fits; "
              "assembled without the hint", file=sys.stderr)
    (out / 'app.bin').write_bytes(app)
    after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(source.rglob('*')) if p.is_file()}
    if after != before:
        raise SystemExit('the source tree changed during the build')
    manifest = {'component': 'ultrarig-app', 'target': args.target, 'flashable': False, 'device_access': False, 'hardware_test': False,
                'audio_test': False, 'app_bin_bytes': len(app), 'app_bin_sha256': sha(app),
                'layout': layout_of((out / 'app.elf').read_bytes()),
                'moved': moved_labels((out / 'app.elf').read_bytes()), 'form_hint_fallbacks': fallbacks,
                'source_files': len(before), 'source_sha256': before}
    if args.jieli_ld:
        manifest['jieli_ld_identical'] = jieli_link(out, args.distro) == app
    (out / 'build-manifest.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in manifest.items() if k != 'source_sha256'}, indent=2))
    if args.expect and sha(app) != args.expect.lower():
        raise SystemExit(f'app.bin SHA-256 {sha(app)} differs from the expected {args.expect}')
    if args.jieli_ld and not manifest['jieli_ld_identical']:
        raise SystemExit("JieLi's ld gives other bytes")


if __name__ == '__main__':
    main()
