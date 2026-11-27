"""Build the HyperRig MINI application area from source, offline.

1. The application: firmware/ultrarig/ with TARGET_MINI, assembled as tools/build_ultrarig_app.py does and linked
   alone once. That link gives the addresses the appended code needs before it is compiled; a name the application
   uses and only the appended code defines (a C function a MINI change calls) gets a placeholder address there.
2. The code the MINI image appends after the application, compiled with JieLi's toolchain (WSL):
   - the audio shim v2 and the any-one-footswitch entry guard, from the copies in the tree's mini/shims (of
     firmware/mini; see firmware/ultrarig/mini/shims/README.md). The places of the application they use
     (functions, data, stack tops, the start-up resume point) are listed in mini/bindings.json: their addresses
     go to the compiler (-D) or the linker (--defsym), so this code follows the application when it moves;
   - every .c and .S file of the tree's mini/c (see firmware/ultrarig/mini/c/README.md);
   - with --product, every .c and .S file of the tree's mini/product as well, and the changes of the application under
     .if MINI_PRODUCT: HyperRig as it is meant to be used on the pedal. Its version is mini/product/VERSION, and its
     build id the first 16 digits of a SHA-256 over every source file; the firmware says both (console word HRID).
     Without --product the MINI target stays v4.
   A fixed address in any of these objects (an li.u32 load that no relocation fills) that points into the image
   and is no binding is reported (unbound_application_constants) with a warning: it would not follow a move.
3. One link of everything: app.ld, then mini/append.ld, which places the appended code right after the
   application's trailing table, word aligned: the audio shim (its code, then its constants), the guard, then the
   code and constants of mini/c. The data of mini/c goes into the RAM image and its zeroed data into the bss
   (app.ld). The MINI changes of the application call the appended entries by name, and the code of mini/c calls
   the application by the names of the source; a name the application does not make global is given to the link
   from the first link (--defsym). If the link moves an application address that the appended code was given,
   it is compiled and linked again with the new addresses. The upstream linker makes the link, and JieLi's ld
   makes it again: both must give the same bytes.
4. The embedded capture must be intact: the application checks its CRC at start-up and, if it does not hold, never
   starts its audio engine. The build stops when the bytes its source pointer names fail that check.
5. The application area: the JLFS directory of mini/area.json, app.bin at 0x120, cfg_tool.bin (mini/cfg_tool.hex)
   after it, the CRCs, the SFC encoding of the used part, 0xFF up to the 516,096-byte application partition.

No image is read. The unchanged source gives the MINI v4 application area,
d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2 (--expect): there the application ends at
0x02076AAC, where v4 places the audio shim.

Offline: this tool installs nothing and is not a hardware or audio test. Whether an area may be installed is decided
by the installer's own review, not by this build.

Usage, from the repository root:
    python -B tools/build_hyperrig_mini_image.py --output build/hyperrig-mini-source-NN [--expect SHA256]
        [--product] [--source firmware/ultrarig] [--compare AREA] [--distro Ubuntu]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'upstream/pi32v2-isa'))
from build_ultrarig_app import BASE, SECTIONS, UNITS, build as build_app, image_of, layout_of, moved_labels  # noqa
from hyperrig.jieli import crc16, sfc, unpack_app  # noqa: E402
from pi32v2isa.ld import link as upstream_link, parse_args  # noqa: E402

TOOLCHAIN = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
SOURCE = ROOT / 'firmware/ultrarig'
REFERENCE = ROOT / 'build/hyperrig-mini-audio-v4/hyperrig-mini.app-area.bin'   # the MINI v4 area, for the report
SHIMS, C_DIR = 'mini/shims', 'mini/c'      # in the source tree
PRODUCT_DIR, PRODUCT_OPTION = 'mini/product', 'MINI_PRODUCT'
AUDIO_SOURCES = ('audio_port_v2/pre_pc5.c', 'audio_port_v2/audio_port.c', 'audio_port/g_bindings.c',
                 'codec/hyperrig_mini_codec.c', 'codec/spin_pi32v2.S', 'audio_port_v2/pc5_hd.S')
GUARD_SOURCES = ('entry_recovery_v2/prefix.S', 'entry_recovery_one/check.S', 'entry_recovery/reset.S')
C_FLAGS = ['-std=c11', '-Wall', '-Wextra', '-Werror', '-Os', '-ffreestanding', '-fno-builtin']
FAST = {'acoustic.c': ['-O2']}              # product sources that run for every block of sound: for speed, not size
SMALL = ('cab.c', 'hyperrig.c', 'irlive.c', 'loader_entry.c', 'midi.c', 'pairs.c', 'replace.c', 'scenes.c', 'swap.c', 'tuner.c')   # and those that never do: for size alone
APP_OBJECTS = tuple(f'{name}.o' for name in UNITS)
ENTRIES = ('hyperrig_mini_g_audio_pre_current_clock', 'hyperrig_mini_g_audio_post', 'hyperrig_mini_entry_guard_v2',
           'hyperrig_mini_append_end')


# The embedded capture's source pointer and length in the RAM data: word 60 of the state at L01c1f180.
CAPTURE_STATE, CAPTURE_OFFSET = 'L01c1f180', 60
LINKED = ('.flash', '.ram', '.bss', '.tail', '.append')   # the output sections app.ld and mini/append.ld define
APPLICATION = ('.flash', '.ram', '.bss', '.tail')


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Toolchain:
    def __init__(self, distro):
        self.prefix = ['wsl.exe', '--distribution', distro, '--exec'] if os.name == 'nt' else []

    def run(self, args, cwd=None):
        """Run a JieLi tool; paths are relative to cwd (default the repository root)."""
        rel = (cwd or ROOT).relative_to(ROOT).as_posix()
        command = ' '.join(shlex.quote(a) for a in args)
        done = subprocess.run(self.prefix + ['sh', '-c', f'cd {shlex.quote(rel)} && {command}'], cwd=ROOT,
                              capture_output=True, text=True, timeout=300)
        if done.returncode:
            raise SystemExit(f'{Path(args[0]).name} failed: {done.stdout}{done.stderr}')


def symbols_of(elf_data, sections):
    """{name: address} of the named symbols defined in the given output sections (local ones too); a name defined
    twice at different addresses is left out."""
    elf = ELFFile(io.BytesIO(elf_data))
    index = {i: s.name for i, s in enumerate(elf.iter_sections())}
    found, twice = {}, set()
    for symbol in elf.get_section_by_name('.symtab').iter_symbols():
        where = symbol['st_shndx']
        if not symbol.name or not isinstance(where, int) or index.get(where) not in sections:
            continue
        if found.setdefault(symbol.name, symbol['st_value']) != symbol['st_value']:
            twice.add(symbol.name)
    return {k: v for k, v in found.items() if k not in twice}


def bindings_of(source, elf_data):
    """{name: {address, kind, original}} of mini/bindings.json: each address is its symbol in the linked
    application plus its offset."""
    spec = json.loads((source / 'mini/bindings.json').read_bytes())
    symbols = {}
    for symbol in ELFFile(io.BytesIO(elf_data)).get_section_by_name('.symtab').iter_symbols():
        if symbol.name and symbol['st_shndx'] not in ('SHN_UNDEF', 'SHN_ABS'):
            symbols.setdefault(symbol.name, set()).add(symbol['st_value'])
    out = {}
    for item in spec['bindings']:
        values = symbols.get(item['symbol'], set())
        if len(values) != 1:
            raise SystemExit(f"binding {item['name']}: the application has {len(values) or 'no'} "
                             f"symbol(s) {item['symbol']}")
        out[item['name']] = {'address': min(values) + item['offset'], 'kind': item['kind'],
                             'original': int(item['original'], 16)}
    return out


def literal_loads(data, relocated):
    """(offset, value) of the li.u32 loads in data (first byte 0xc0..0xcf, second 0xff, then the 32-bit value) that
    no relocation fills. JieLi's clang and the upstream assembler put the relocation of such a load
    (R_PI32V2_MOV_ABS32) at the start of the instruction; one at its value is accepted as well."""
    return [(i, struct.unpack_from('<I', data, i + 2)[0]) for i in range(len(data) - 5)
            if data[i] & 0xF0 == 0xC0 and data[i + 1] == 0xFF and i not in relocated and i + 2 not in relocated]


def unbound_constants(link, objects, bounds, bindings):
    """The literal li.u32 values of the appended objects that point into the image (flash from BASE to the end of the
    appended code, RAM from 0x01C00000 to the heap end) at no binding: a fixed address that would not follow the
    application. A value the linker fills (a name) is not literal."""
    flash_end, heap_end = bounds
    bound = {b['address'] for b in bindings.values()}
    found = []
    for obj in objects:
        elf = ELFFile(io.BytesIO((link / obj).read_bytes()))
        relocated = {}
        for section in elf.iter_sections():
            if isinstance(section, RelocationSection):
                offsets = relocated.setdefault(section['sh_info'], set())
                offsets.update(r['r_offset'] for r in section.iter_relocations())
        for index, section in enumerate(elf.iter_sections()):
            if not section['sh_flags'] & 2 or section['sh_type'] == 'SHT_NOBITS':
                continue
            for offset, value in literal_loads(section.data(), relocated.get(index, ())):
                if (BASE <= value < flash_end or 0x01C00000 <= value < heap_end) and value not in bound:
                    found.append({'at': f'{obj}:{section.name}+0x{offset:x}', 'value': f'0x{value:08x}'})
    return found


def product_identity(source, sources):
    """(version, build id) of a product build: the id is over the path in the tree and the SHA-256 of every source."""
    version = (source / PRODUCT_DIR / 'VERSION').read_text(encoding='ascii').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+(-[a-z0-9.]+)?', version) or len(version) > 24:
        raise SystemExit(f'not a version: {version!r}')
    text = ''.join(f'{name} {digest}\n' for name, digest in sorted(sources.items()))
    return version, sha(text.encode('utf-8'))[:16]


def compile_appended(tools, source, link, bindings, product=None):
    """Compile the appended code into link/audio, link/guard and link/c; the object paths relative to link, in
    link order: the audio shim, the guard, then the files of mini/c, and of mini/product for a product build, by
    name. product: (version, build id) or None."""
    rel = lambda p: p.relative_to(ROOT).as_posix()
    shims, extra = source / SHIMS, source / C_DIR
    defines = [f"-D{name}=0x{b['address']:08x}{'u' if b['kind'] == 'c' else ''}"
               for name, b in sorted(bindings.items()) if b['kind'] in ('c', 'asm')]
    jobs = []
    for name in AUDIO_SOURCES:
        rename = ['-Dhyperrig_mini_g_audio_pre_current_clock=hyperrig_mini_g_audio_pre_current_clock_v1'] \
            if name.endswith('g_bindings.c') else []
        jobs.append(('audio', shims / name, [*C_FLAGS, *rename]))
    jobs += [('guard', shims / name, []) for name in GUARD_SOURCES]
    added = sorted(p for p in extra.glob('*') if p.suffix in ('.c', '.S')) if extra.is_dir() else []
    jobs += [('c', path, [*C_FLAGS, f'-I{rel(extra)}']) for path in added]
    if product:
        own = source / PRODUCT_DIR
        identity = [f'-DHYPERRIG_VERSION="{product[0]}"', f'-DHYPERRIG_BUILD="{product[1]}"']
        jobs += [('c', path, [*C_FLAGS, *FAST.get(path.name, ['-Oz'] if path.name in SMALL else []), f'-I{rel(own)}', *identity]) for path in sorted(own.glob('*'))
                 if path.suffix in ('.c', '.S')]
    objects = []
    for group, path, flags in jobs:
        obj = f'{group}/{path.stem}.o'
        if obj in objects:
            raise SystemExit(f'two sources give {obj}')
        (link / group).mkdir(parents=True, exist_ok=True)
        tools.run([TOOLCHAIN + 'clang', '-target', 'pi32v2', '-mcpu=r3', *flags, *defines, '-c', rel(path),
                   '-o', rel(link / obj)])
        objects.append(obj)
    return objects


def imports_of(link, objects, application):
    """{name: address} of the symbols the appended code uses, does not define itself and finds among the
    application's names (local labels too). Other names are left to the link: the symbols of the linker scripts,
    or an undefined reference."""
    defined, used = set(), set()
    for obj in objects:
        for symbol in ELFFile(io.BytesIO((link / obj).read_bytes())).get_section_by_name('.symtab').iter_symbols():
            if not symbol.name or symbol['st_info']['type'] in ('STT_FILE', 'STT_SECTION'):
                continue
            (used if symbol['st_shndx'] == 'SHN_UNDEF' else defined).add(symbol.name)
    wanted = used - defined
    return {name: application[name] for name in sorted(wanted) if name in application}


def link_upstream(link, objects, symbols):
    """The ELF of one link of the application objects and the appended code, by the upstream linker."""
    defsyms = [f'--defsym={k}=0x{v:08x}' for k, v in sorted(symbols.items())]
    here = os.getcwd()
    os.chdir(link)
    try:
        linker, data = upstream_link(parse_args(['-T', 'app.ld', '-T', 'append.ld', *defsyms,
                                                 *APP_OBJECTS, *objects, '-o', 'app.elf', '-Map', 'app.map']))
    finally:
        os.chdir(here)
    if data is None:
        raise SystemExit('link failed: ' + '; '.join(linker.errors[:10]))
    (link / 'app.elf').write_bytes(data)
    return data


def link_jieli(tools, link, objects, symbols):
    """The same link by JieLi's ld."""
    defsyms = [f'--defsym={k}=0x{v:08x}' for k, v in sorted(symbols.items())]
    up = '../' * len(link.relative_to(ROOT).parts)
    tools.run([up + TOOLCHAIN + 'ld', '-T', 'app.ld', '-T', 'append.ld', *defsyms, *APP_OBJECTS, *objects,
               '-o', 'jieli.elf'], cwd=link)
    return (link / 'jieli.elf').read_bytes()


def check_sections(elf_data):
    """Every loaded byte of the link is in a section app.ld or mini/append.ld places."""
    stray = [s.name for s in ELFFile(io.BytesIO(elf_data)).iter_sections()
             if s['sh_flags'] & 2 and s['sh_size'] and s.name not in LINKED]
    if stray:
        raise SystemExit(f'sections that no linker script places (an orphan would land anywhere): {stray}')


def appended_record(elf_data):
    """Where each part of the appended code is, from the symbols mini/append.ld defines."""
    elf = ELFFile(io.BytesIO(elf_data))
    found = {s.name: s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()
             if s.name.startswith('hyperrig_mini_') and s['st_shndx'] != 'SHN_UNDEF'}
    data = elf.get_section_by_name('.append').data()
    start = elf.get_section_by_name('.append')['sh_addr']
    part = lambda a, b: {'address': found[a], 'bytes': found[b] - found[a],
                         'sha256': sha(data[found[a] - start:found[b] - start])}
    return {'audio': part('hyperrig_mini_audio_start', 'hyperrig_mini_audio_end'),
            'padding_bytes': found['hyperrig_mini_guard_start'] - found['hyperrig_mini_audio_end'],
            'guard': part('hyperrig_mini_guard_start', 'hyperrig_mini_guard_end'),
            'c': part('hyperrig_mini_c_start', 'hyperrig_mini_c_end')}


def compare(image, app, reference_path):
    """Report only: how this area differs from a reference area (by default MINI v4). The sectors that differ are
    the ones an installation over the reference would rewrite."""
    if not reference_path.is_file():
        return {'reference': reference_path.relative_to(ROOT).as_posix(), 'available': False}
    reference = reference_path.read_bytes()
    _, _, files = unpack_app(reference)
    sectors = [offset for offset in range(0, max(len(image), len(reference)), 4096)
               if image[offset:offset + 4096] != reference[offset:offset + 4096]]
    return {'reference': reference_path.relative_to(ROOT).as_posix(), 'available': True,
            'reference_sha256': sha(reference), 'identical': image == reference,
            'sectors_differing': len(sectors), 'sectors_total': len(image) // 4096,
            'first_differing_sector_offset': f'0x{sectors[0]:05x}' if sectors else None,
            'app_bin_bytes_change': len(app) - len(files['app.bin'])}


def embedded_capture(app, layout, state):
    """Where the embedded capture is and whether the check the application's parser makes first holds: at least 44
    bytes, and the CRC-32 of all but the last four in those four. state is the address of CAPTURE_STATE."""
    at = int(layout['ram_image_load'], 16) - BASE + state - 0x01C00000 + CAPTURE_OFFSET
    source, size = struct.unpack_from('<II', app, at)
    data = app[source - BASE:source - BASE + size] if BASE <= source else b''
    intact = 44 <= size == len(data) and zlib.crc32(data[:-4]) == struct.unpack('<I', data[-4:])[0]
    return {'address': f'0x{source:08x}', 'bytes': size, 'sha256': sha(data), 'intact': intact}


def record(fields, offset, size, data_crc):
    raw = bytearray(struct.pack('<HHIIBBH16s', 0, data_crc, offset, size, fields['flags'], fields['reserved'],
                                fields['index'], bytes.fromhex(fields['name_field_hex'])))
    struct.pack_into('<H', raw, 0, crc16(bytes(raw[2:])))
    return bytes(raw)


def package(app, cfg, area):
    """The application area: directory, app.bin, cfg_tool.bin, CRCs, SFC encoding of the used part."""
    plain = bytearray(b'\xff' * area['partition_bytes'])
    app_at = area['app_offset']
    cfg_at = app_at + len(app)
    head_end = cfg_at + len(cfg)
    if head_end > len(plain):
        raise SystemExit('the application does not fit the MINI application partition')
    plain[app_at:cfg_at] = app
    plain[cfg_at:head_end] = cfg
    records = {r['name']: r for r in area['records']}
    for r in area['records']:
        if 'record_hex' in r:
            plain[r['header_offset']:r['header_offset'] + 32] = bytes.fromhex(r['record_hex'])
    plain[32:64] = record(records['app.bin'], app_at, len(app), crc16(app))
    plain[64:96] = record(records['cfg_tool.bin'], cfg_at, len(cfg), crc16(cfg))
    plain[0:32] = record(records['app_area_head'], records['app_area_head']['offset'], head_end,
                         crc16(bytes(plain[32:head_end])))
    end = (head_end + 31) & ~31
    raw = sfc(bytes(plain[:end]), area['sfc_key']) + bytes(plain[end:])
    decoded, entries, files = unpack_app(raw)
    if decoded != plain or files['app.bin'] != app or files['cfg_tool.bin'] != cfg:
        raise SystemExit('the application area does not decode back to its parts')
    return raw, {'bytes': len(raw), 'app_bytes': len(app), 'cfg_tool_offset': cfg_at, 'head_end': head_end,
                 'encoded_end': end, 'directory': [e.name for e in entries]}


def global_names(link):
    """The names the application objects define as global: the link resolves these by itself."""
    names = set()
    for obj in APP_OBJECTS:
        for symbol in ELFFile(io.BytesIO((link / obj).read_bytes())).get_section_by_name('.symtab').iter_symbols():
            if symbol['st_info']['bind'] == 'STB_GLOBAL' and symbol['st_shndx'] != 'SHN_UNDEF':
                names.add(symbol.name)
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect', help='required SHA-256 of the application area')
    parser.add_argument('--distro', default='Ubuntu')
    parser.add_argument('--source', type=Path, default=SOURCE.relative_to(ROOT),
                        help='the application source tree (default firmware/ultrarig)')
    parser.add_argument('--compare', type=Path, default=REFERENCE.relative_to(ROOT),
                        help='an application area to compare with in the report (default: the MINI v4 area, '
                             'when present); it is only read for the report')
    parser.add_argument('--product', action='store_true',
                        help='the HyperRig product changes (MINI_PRODUCT and mini/product); without it the area is v4')
    args = parser.parse_args()
    out, source = (ROOT / args.output).resolve(), (ROOT / args.source).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        parser.error('use a fresh directory under build/')
    out.mkdir(parents=True)
    inputs = sorted(p for p in source.rglob('*') if p.is_file())
    before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in inputs}
    product = product_identity(source, {p.relative_to(source).as_posix(): sha(p.read_bytes()) for p in inputs}) \
        if args.product else None
    tools = Toolchain(args.distro)
    fallbacks = []
    build_app(source, out / 'app-first', 'mini', fallbacks=fallbacks, placeholder=BASE,
              options=(PRODUCT_OPTION,) if product else ())
    for item in fallbacks:
        print(f"warning: {item['line']}: the hinted form {item['hinted_form']} no longer fits; "
              "assembled without the hint", file=sys.stderr)
    first = (out / 'app-first' / 'app.elf').read_bytes()
    link = out / 'link'
    link.mkdir()
    for name in (*APP_OBJECTS, 'app.ld'):
        shutil.copyfile(out / 'app-first' / name, link / name)
    shutil.copyfile(source / 'mini/append.ld', link / 'append.ld')
    globals_ = global_names(link)
    bindings, application = bindings_of(source, first), symbols_of(first, APPLICATION)
    for attempt in range(3):
        for group in ('audio', 'guard', 'c'):
            shutil.rmtree(link / group, ignore_errors=True)
        objects = compile_appended(tools, source, link, bindings, product)
        imports = {k: v for k, v in imports_of(link, objects, application).items() if k not in globals_}
        given = {**imports, **{k: b['address'] for k, b in bindings.items() if b['kind'] == 'ld'}}
        elf = link_upstream(link, objects, given)
        now, application = bindings_of(source, elf), symbols_of(elf, APPLICATION)
        if now == bindings and all(application.get(k) == v for k, v in imports.items()):
            break
        bindings = now
    else:
        raise SystemExit('the addresses of the application do not settle when the appended code is linked')
    check_sections(elf)
    full = image_of(elf, SECTIONS + ('.append',))
    if image_of(link_jieli(tools, link, objects, given), SECTIONS + ('.append',)) != full:
        raise SystemExit("JieLi's ld gives other bytes than the upstream linker")
    app = image_of(elf)
    application_layout = layout_of(elf)
    found = {s.name: s['st_value'] for s in ELFFile(io.BytesIO(elf)).get_section_by_name('.symtab').iter_symbols()
             if s.name in ENTRIES and s['st_shndx'] != 'SHN_UNDEF'}
    entries = {name: found[name] for name in ENTRIES if name in found}
    missing = [name for name in ENTRIES if name not in entries]
    if missing:
        raise SystemExit(f'entries missing from the appended code: {missing}')
    unbound = unbound_constants(link, objects, (entries['hyperrig_mini_append_end'],
                                                int(application_layout['heap_end'], 16)), bindings)
    for item in unbound:
        print(f"warning: {item['at']} loads the fixed address {item['value']}, which is not in mini/bindings.json "
              "and will not follow the application: use a binding or a name", file=sys.stderr)
    state = symbols_of(elf, APPLICATION).get(CAPTURE_STATE)
    capture = embedded_capture(full, application_layout, state) if state else {'intact': False}
    if not capture['intact']:
        raise SystemExit(f'the embedded capture is damaged: the audio engine would not start ({capture})')
    area = json.loads((source / 'mini/area.json').read_bytes())
    cfg = bytes.fromhex(''.join(line.strip() for line in (source / 'mini/cfg_tool.hex').read_text(encoding='ascii')
                                .splitlines() if line.strip() and not line.startswith('#')))
    image, layout = package(full, cfg, area)
    if {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in inputs} != before:
        raise SystemExit('a source changed during the build')
    (out / 'app.bin').write_bytes(full)
    (out / 'hyperrig-mini.app-area.bin').write_bytes(image)
    manifest = {'component': 'hyperrig-mini-application-area', 'flashable': False, 'device_access': False,
                'hardware_test': False, 'audio_test': False,
                'product': {'version': product[0], 'build_id': product[1]} if product else None,
                'area_sha256': sha(image), 'area_bytes': len(image), 'app_bin_sha256': sha(full),
                'application_from_source_sha256': sha(app), 'linked_by': ['upstream ld', "JieLi's ld"],
                'link_passes': attempt + 1,
                'application_layout': application_layout, 'appended': appended_record(elf),
                'appended_entries': {k: f'0x{v:08x}' for k, v in entries.items()},
                'imports': {k: f'0x{v:08x}' for k, v in imports.items()},
                'c_sources': sorted(o.split('/', 1)[1] for o in objects if o.startswith('c/')),
                'bindings': {name: {'address': f"0x{b['address']:08x}", 'original': f"0x{b['original']:08x}"}
                             for name, b in bindings.items()},
                'bindings_moved': sorted(name for name, b in bindings.items() if b['address'] != b['original']),
                'unbound_application_constants': unbound, 'embedded_capture': capture,
                'room_left_bytes': area['partition_bytes'] - layout['head_end'],
                'moved': moved_labels(elf), 'form_hint_fallbacks': fallbacks,
                'comparison': compare(image, full, ROOT / args.compare) if args.compare else None,
                'layout': layout, 'source_sha256': before}
    (out / 'build-manifest.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('source_sha256', 'layout')}, indent=2))
    if args.expect and sha(image) != args.expect.lower():
        raise SystemExit(f'area SHA-256 {sha(image)} differs from the expected {args.expect}')


if __name__ == '__main__':
    main()
