"""Break the loader's engine in one place at a time and see that its tests notice. Offline.

firmware/mini_stage/test_engine.c passes on the engine as it is. Each line below takes one rule out of a copy of engine.c;
the tests must then fail (or the sanitizers stop them). A rule that can be taken out unnoticed is a rule nobody checks.

Usage, from the repository root:
    python -B tools/check_mini_stage_engine.py --output build/mini-stage-mutations-NN [--distro Ubuntu]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'firmware/mini_stage'
MUTATIONS = [
    ('the header may be written at any time', 'if (s.windows & HRS_WINDOW_APP ? (a == HRS_APP) != (s.done + 1 == s.sectors) : s.done >= s.sectors) return HRS_E_STATE;', ''),
    ('the header page is written first', 'page = a == HRS_APP ? (i + 1) % (HRS_SECTOR / HRS_PAGE) : i;', 'page = i;'),
    ('OPEN erases nothing', 'if ((e = erase(HRS_APP))) return e;', ''),
    ('OPEN takes any header', 'if (hrs_crc32(s.work, HRS_SECTOR) != get32(b)) return HRS_E_PREIMAGE;', ''),
    ('OPEN in any phase', 'if (s.phase != HRS_ARMED || s.done || !(s.windows & HRS_WINDOW_APP)) return HRS_E_STATE;', ''),
    ('a whole application is opened without a way back', 'if (s.unit.app_valid && !ours) return HRS_E_NO_RETURN;', ''),
    ('nothing may be opened without a way back, even with nothing to lose', 'if (s.unit.app_valid && !ours) return HRS_E_NO_RETURN;', 'if (!ours) return HRS_E_NO_RETURN;'),
    ('a record without its mark counts', 'get16(s.work + 6) == HRS_RECORD_MARK && ', ''),
    ('a record with a wrong checksum counts', ' && crc16(s.work + 2, HRS_RECORD - 2) == get16(s.work)', ''),
    ('a record with no type counts', '!get16(s.work) || !get16(s.work + 2) || ', '!get16(s.work) || '),
    ('a record with checksum zero counts', '!get16(s.work) || !get16(s.work + 2) || ', '!get16(s.work + 2) || '),
    ('a record that leads anywhere counts', ' || !inside(a, 64, HRS_APP_END, HRS_USER)) return HRS_OK;', ') return HRS_OK;'),
    ('a file record of another place counts', 'get32(s.work + 4) == a && ', ''),
    ('an empty loader counts', 'get32(s.work + 8) > 64 && ', ''),
    ('a loader that leaves its place counts', 'inside(a, get32(s.work + 8), HRS_APP_END, HRS_USER) &&\n', '\n'),
    ('a damaged compression header counts', 'crc16(s.work + 34, 30) == get16(s.work + 32) && ', ''),
    ('any loader counts', ' && get16(s.work + 34) == HRS_LOADER_CRC', ''),
    ('a loader of no size counts', 'get32(s.work + 36) && get32(s.work + 36) <= HRS_LOADER_MAX', 'get32(s.work + 36) <= HRS_LOADER_MAX'),
    ('a loader of any size counts', 'get32(s.work + 36) && get32(s.work + 36) <= HRS_LOADER_MAX', 'get32(s.work + 36)'),
    ('a loader for another place counts', ' && get32(s.work + 40) == HRS_LOADER_AT', ''),
    ('records are looked for from the bottom', 'for (*at = 0; boundary > HRS_SECTOR; boundary -= HRS_SECTOR)', 'for (*at = 0, boundary = 2 * HRS_SECTOR; boundary < HRS_CAPACITY; boundary += HRS_SECTOR)'),
    ('RETIRE in any phase', "    if (s.phase != HRS_READY) return HRS_E_STATE;\n    if ((e = quiet()) || (e = look_back(&at, &ours))) return e;\n    if (!at", "    if ((e = quiet()) || (e = look_back(&at, &ours))) return e;\n    if (!at"),
    ('RETIRE of any place', '!at || at != get32(b) || ours || ', '!at || ours || '),
    ('RETIRE of our own record', '!at || at != get32(b) || ours || ', '!at || at != get32(b) || '),
    ('RETIRE outside the VM', ' || ours || !inside(at, HRS_PAGE, HRS_APP_END, HRS_USER)) return HRS_E_RANGE;', ' || ours) return HRS_E_RANGE;'),
    ('RETIRE with another loader below', "    if (!ours) return HRS_E_NO_RETURN;\n    for", '    for'),
    ('RETIRE clears more', 'i == 6 || i == 7 ? 0 : 0xff', 'i == 6 || i == 7 || i == 9 ? 0 : 0xff'),
    ('the retired page stays open to writing', '        s.retiring = 0;' if False else '    s.retiring = 0;\n    if (e', '    if (e'),
    ('RETIRE is not checked', 'return at == next && ours ? HRS_OK : fail(HRS_E_READBACK);', 'return HRS_OK;'),
    ('OPEN without the application window', 's.phase != HRS_ARMED || s.done || !(s.windows & HRS_WINDOW_APP)', 's.phase != HRS_ARMED'),
    ('a sector that changed meanwhile is overwritten', 'if (hrs_crc32(s.work, HRS_SECTOR) != get32(b + 4) && !(was_blank && a == HRS_APP)) return HRS_E_PREIMAGE;', ''),
    ('what was sent is not compared with what was meant', 'if (hrs_crc32(s.sector, HRS_SECTOR) != get32(b + 8)) return HRS_E_CRC;', ''),
    ('BEGIN without the whole backup', 'if (crc != get32(b)) return HRS_E_BACKUP;', ''),
    ('BEGIN without its magic', ' || get32(b + 11) != HRS_MAGIC', ''),
    ('BEGIN twice', "    windows = b[10];\n    if (s.phase != HRS_READY) return HRS_E_STATE;", '    windows = b[10];'),
    ('BEGIN with any window', '!windows || windows > 3 || ', ''),
    ('BEGIN with any count', '!get16(b + 8) || get16(b + 8) > HRS_MAX_SECTORS', '0'),
    ('a repeated message is carried out again', 's.have_last = 1;', ''),
    ('a damaged message is answered', 'if (crc != get32(in + HRS_HEAD + size)) return 0;', ''),
    ('a cut message is answered', 'if (size != length - HRS_HEAD - 4) return 0;', 'size = length - HRS_HEAD - 4;'),
    ('the application window reaches into the boot area', 'inside(a, n, HRS_APP, s.app_end) ||', 'inside(a, n, HRS_APP - 0x1000, s.app_end) ||'),
    ('the application window reaches past its end', 'inside(a, n, HRS_APP, s.app_end) ||', 'inside(a, n, HRS_APP, s.app_end + 0x1000) ||'),
    ('a sector of the wide window counts as the user area', 'static int is_app(uint32_t a) { return inside(a, HRS_SECTOR, HRS_APP, s.app_end); }', 'static int is_app(uint32_t a) { return inside(a, HRS_SECTOR, HRS_APP, HRS_APP_END); }'),
    ('a session starts without a window', '    s.app_end = HRS_APP_END;\n    make_table();', '    make_table();'),
    ('BEGIN keeps the old window', '    s.app_end = end;\n', ''),
    ('BEGIN of any length', '(n != 15 && n != 19)', '(n < 15)'),
    ('BEGIN of 19 bytes keeps the old window', 'end = n == 19 ? get32(b + 15) : HRS_APP_END;', 'end = HRS_APP_END;'),
    ('the window is widened without a look', '    if ((e = widen(end))) return e;\n', ''),
    ('the window ends anywhere in a sector', '(end & (HRS_SECTOR - 1)) || ', ''),
    ('the window ends before the old one', ' || end < HRS_APP_END || ', ' || '),
    ('the window ends anywhere above', ' || end > HRS_APP_END_MAX) return HRS_E_RANGE;', ') return HRS_E_RANGE;'),
    ('the window is widened with another loader first', 'if (!ours || at < end || s.loader_at < end)', 'if (at < end || s.loader_at < end)'),
    ('the window covers the record of the way back', 'if (!ours || at < end || s.loader_at < end)', 'if (!ours || s.loader_at < end)'),
    ('the window covers the loader of the way back', 'if (!ours || at < end || s.loader_at < end)', 'if (!ours || at < end)'),
    ('the directory is not read', '    return partitions(end);\n}', '    return HRS_OK;\n}'),
    ('a blank header needs the key', '    if (i == HRS_PAGE) return HRS_OK;\n', ''),
    ('a header is read without the key', '    if (!s.unit.key) return HRS_E_RANGE;\n', ''),
    ('the directory is read as it is stored', '            s.work[o + i] ^= (uint8_t)key;\n', ''),
    ('a record with a wrong CRC counts', '        if (crc16(r + 2, 30) != get16(r)) continue;\n', ''),
    ('the VM may start elsewhere', 'said &= get32(r + 4) == end && get32(r + 8) == HRS_VM_END - end;', 'said &= get32(r + 8) == HRS_VM_END - end;'),
    ('the VM may be of any length', 'said &= get32(r + 4) == end && get32(r + 8) == HRS_VM_END - end;', 'said &= get32(r + 4) == end;'),
    ('PRCT may start anywhere', 'said &= !get32(r + 4) && get32(r + 8) == end;', 'said &= get32(r + 8) == end;'),
    ('PRCT may end anywhere', 'said &= !get32(r + 4) && get32(r + 8) == end;', 'said &= !get32(r + 4);'),
    ('HELLO does not say the window', '    put32(o + 31 + HRS_BUILD_TEXT, s.app_end);', ''),
    ('the user window starts at the radio data', 'inside(a, n, HRS_USER, HRS_USER_END);', 'inside(a, n, HRS_USER - 0x1000, HRS_USER_END);'),
    ('the user window reaches the last sector', 'inside(a, n, HRS_USER, HRS_USER_END);', 'inside(a, n, HRS_USER, HRS_USER_END + 0x1000);'),
    ('an unaligned sector is written', '(a & (HRS_SECTOR - 1)) || !hrs_writable(a, HRS_SECTOR) ||\n', '!hrs_writable(a, HRS_SECTOR) ||\n'),
    ('a sector of a window BEGIN did not name', '(s.windows & (is_app(a) ? HRS_WINDOW_APP : HRS_WINDOW_USER))', '1'),
    ('WRITE before OPEN', "    a = get32(b);\n    if (s.phase != (s.windows & HRS_WINDOW_APP ? HRS_OPENED : HRS_ARMED)) return HRS_E_STATE;", '    a = get32(b);'),
    ('DATA in any phase', 'if (n < 3 || s.phase != (s.windows & HRS_WINDOW_APP ? HRS_OPENED : HRS_ARMED)) return n < 3 ? HRS_E_FRAME : HRS_E_STATE;', 'if (n < 3) return HRS_E_FRAME;'),
    ('DATA past the sector', 'offset >= HRS_SECTOR || n > HRS_SECTOR - offset || ', ''),
    ('a sector is not erased first', 'if (!was_blank && (e = erase(a))) return e;', ''),
    ('an erase is not checked', 'return blank() ? HRS_OK : fail(HRS_E_READBACK);', 'return HRS_OK;'),
    ('a written sector is not checked', 'if (!equal()) return fail(HRS_E_READBACK);', ''),
    ('the whole flash is not checked at the end', 'if (crc != s.target_crc) return fail(HRS_E_READBACK);', ''),
    ('FINISH before the last sector', '|| s.done != s.sectors) return HRS_E_STATE;', ') return HRS_E_STATE;'),
    ('FINISH says nothing of the application', 'if (s.windows & HRS_WINDOW_APP) s.unit.app_valid = 1;', ''),
    ('the application is started half written', 's.unit.app_valid && !s.touched)', 's.unit.app_valid)'),
    ('the application is started though there is none', '!(s.phase == HRS_DONE ? s.unit.app_valid : s.unit.app_valid && !s.touched)', '!(s.phase == HRS_DONE ? 1 : !s.touched)'),
    ('LEAVE with any mode', ' || b[0] < HRS_START_APP || b[0] > HRS_RESTART', ''),
    ('an erase is forgotten', "    s.touched = 1;\n    if (s.nor.erase4k", '    if (s.nor.erase4k'),
    ('a program is forgotten', '            s.touched = 1;\n', ''),
    ('an error does not end the session', 's.error = error; s.phase = HRS_FAILED; return error;', 's.error = error; return error;'),
    ('a protected flash is written', 'if ((s.sr1 & 0x7c) || (s.sr2 & 0x40)) return fail(HRS_E_PROTECTED);', ''),
    ('a busy flash is used', 'if (s.sr1 & 1) return fail(HRS_E_BUSY);', ''),
    ('a write enable left on is ignored', 'if (s.sr1 & 2) return fail(HRS_E_WEL);', ''),
    ('a write enable that did not take is ignored', 'return (s.sr1 & 3) == 2 ? HRS_OK : fail(HRS_E_WEL);', 'return HRS_OK;'),
    ('a flash that stays busy is waited for without end', 'return fail(HRS_E_TIMEOUT);', 'return HRS_OK;'),
    ('another flash is accepted', 'if (u.jedec != HRS_JEDEC) (void)fail(HRS_E_JEDEC);', ''),
    ('USB is not served during long work', '        s.nor.idle(s.nor.user);\n', ''),
    ('READ beyond the flash', '!inside(a, n, 0, HRS_CAPACITY) || ', ''),
    ('READ of more than a chunk', ' || n > HRS_CHUNK) status = HRS_E_RANGE;', ') status = HRS_E_RANGE;'),
    ('CRC beyond the flash', 'else if (!inside(get32(b), get32(b + 4), 0, HRS_CAPACITY)) status = HRS_E_RANGE;', ''),
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--distro', default='Ubuntu')
    args = parser.parse_args(argv)
    out = (ROOT / args.output).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        parser.error('use a fresh directory under build/')
    out.mkdir(parents=True)
    prefix = ['wsl.exe', '--distribution', args.distro, '--exec'] if os.name == 'nt' else []
    engine = (ROOT / SOURCE / 'engine.c').read_bytes().decode('utf-8')

    def outcome(number, old, new):
        if engine.count(old) != 1:
            return f'the place is found {engine.count(old)} times'
        folder = out / f'{number:02}'
        folder.mkdir()
        (folder / 'engine.c').write_bytes(engine.replace(old, new).encode('utf-8'))
        rel = folder.relative_to(ROOT).as_posix()
        done = subprocess.run(prefix + ['gcc', '-std=c99', '-Wno-unused', f'-I{SOURCE}', '-O1', '-fsanitize=address,undefined',
                                        '-fno-sanitize-recover=all', f'{rel}/engine.c', f'{SOURCE}/test_engine.c', '-o', f'{rel}/test'],
                              cwd=ROOT, capture_output=True, text=True)
        if done.returncode:
            return 'does not compile: ' + done.stderr[-300:]
        try:
            done = subprocess.run(prefix + ['timeout', '120', f'{rel}/test'], cwd=ROOT, capture_output=True, text=True)
        except subprocess.SubprocessError as error:
            return f'not run: {error}'
        return 'not noticed' if done.returncode == 0 else 'noticed: ' + (done.stdout + done.stderr).strip().splitlines()[-1][:100]

    with ThreadPoolExecutor(8) as pool:
        control = pool.submit(outcome, 99, engine[:40], engine[:40])
        results = list(pool.map(lambda item: outcome(item[0], *item[1][1:]), enumerate(MUTATIONS)))
    report = {'kind': 'mini-stage-engine-mutations', 'control': control.result(),
              'mutations': {name: result for (name, _, _), result in zip(MUTATIONS, results)}}
    report['held'] = report['control'] == 'not noticed' and all(r.startswith('noticed') for r in results)
    (out / 'report.json').write_bytes((json.dumps(report, indent=1) + '\n').encode('utf-8'))
    for name, result in report['mutations'].items():
        if not result.startswith('noticed'):
            print(f'{name}: {result}')
    print(f"{sum(r.startswith('noticed') for r in results)} of {len(results)} noticed; unchanged engine: {report['control']}")
    return 0 if report['held'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
