"""Run the built MINI application's own capture probe on its embedded A2 capture, in the pi32v2 simulator. Offline.

The application starts its audio engine only after it accepts the embedded capture: at start-up, dsp_start calls
capture_dispatch_probe on it (the source pointer and length at 0x01c1f1bc), and the answer is what `LVL` reports as
`am`. MINI v4 answers 118,688 (the parser's 118,664 bytes + 8 + 16). A capture the parser refuses gives 16, and the
engine stays off: `m=0`, `MODEL ''`, no audio. This is how the first moved builds failed on the pedal on 23 November
2026: a weight of the capture had been taken for an address and followed the move.

The probe runs here from the bytes of app.bin alone: the flash code at 0x02000120, and the RAM image copied to
0x01c00000 from where the start-up code copies it. Every instruction is executed; nothing of it is replaced. The
addresses come from the linked application (link/app.elf of tools/build_hyperrig_mini_image.py).

This is no hardware or audio test: it says that this build's code accepts this build's capture.

Usage, from the repository root:
    python -B tools/check_mini_embedded_capture.py BUILD [BUILD ...]
BUILD is an output directory of tools/build_hyperrig_mini_image.py. The exit code is 1 when a build is refused.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/pi32v2-isa'), str(ROOT / 'upstream/pi32v2-isa/tools/llvm'),
                str(ROOT / 'upstream/pi32v2-isa/tools/hwtest')]
import mini_sim as sim  # noqa: E402

BASE, RAM = 0x02000120, 0x01C00000
PROBE, SOURCE = 'capture_dispatch_probe', 'L01c1f180'     # the source pointer and length are at SOURCE + 60
SOURCE_OFFSET = 60
EXPECTED = 118664 + 8 + 16
REFUSED = 16


def symbols(elf, names):
    found = {}
    for symbol in ELFFile(elf).get_section_by_name('.symtab').iter_symbols():
        if symbol.name in names:
            found.setdefault(symbol.name, set()).add(symbol['st_value'])
    wrong = {n: found.get(n) for n in names if len(found.get(n, ())) != 1}
    if wrong:
        raise SystemExit(f'symbols not found once: {wrong}')
    return {n: min(v) for n, v in found.items()}


def probe(app, ram_load, ram_size, where):
    """(answer, source address, length, steps) of the application's probe on its own embedded capture."""
    cpu = sim.CPU()
    cpu.mem.write(BASE, app)
    at = ram_load - BASE
    cpu.mem.write(RAM, app[at:at + ram_size])
    source = int.from_bytes(cpu.mem.read(where[SOURCE] + SOURCE_OFFSET, 4), 'little')
    length = int.from_bytes(cpu.mem.read(where[SOURCE] + SOURCE_OFFSET + 4, 4), 'little')
    answer, _ = cpu.call(where[PROBE], [source, length], limit=20_000_000)
    return answer, source, length, cpu.steps


def check(build):
    manifest = json.loads((build / 'build-manifest.json').read_bytes())
    layout = manifest['application_layout']
    with (build / 'link/app.elf').open('rb') as elf:
        where = symbols(elf, (PROBE, SOURCE))
    app = (build / 'app.bin').read_bytes()
    answer, source, length, steps = probe(app, int(layout['ram_image_load'], 16), layout['ram_image_size'], where)
    return {'build': build.as_posix(), 'area_sha256': manifest['area_sha256'], 'capture_at': f'0x{source:08x}',
            'capture_bytes': length, 'am': answer, 'accepted': answer == EXPECTED, 'instructions': steps}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('builds', type=Path, nargs='+', metavar='BUILD')
    args = parser.parse_args(argv)
    results = [check(build) for build in args.builds]
    print(json.dumps({'expected_am': EXPECTED, 'refused_am': REFUSED, 'results': results, 'hardware_test': False},
                     indent=1))
    return 0 if all(r['accepted'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
