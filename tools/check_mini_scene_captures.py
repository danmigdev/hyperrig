"""A capture for each scene (mini/product/scenes.c, SNAPCAP), in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of app.bin, with the flash, the pause of the sound and the engine's start and stop of
tools/check_mini_swap.py, and the storage of presets in memory. Checked: what SNAPCAP says and refuses; that choosing a scene puts its capture
into the engine, and only when it is another; that a preset keeps its own capture while that of a scene plays, and is stored with it; the stored
form, that a preset without such a scene is stored byte for byte as before, and that a firmware from before takes the new form as an empty place;
that a preset starts with the capture of its scene, loaded once; a scene that is kept, deleted or new; another capture that is loaded by hand,
one that is gone, and the memory lent to the effects.

Usage, from the repository root:
    python -B tools/check_mini_scene_captures.py BUILD [--before BUILD]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_swap as swap  # noqa: E402

PRESETS, HALF = 0xBF000, 0x800
SET_CAPTURE, SET_SCENE, SET_PRESET = 9, 88, 92
RECORD, REC_CAPTURE = 260, 259


class Pedal(swap.Pedal):
    ALLOCATE, RELEASE, POOL, POOL_END = 0x01C60000, 0x01C60010, 0x01D00000, 0x01F00000

    def restart(self):
        super().restart()
        self.stored = getattr(self, 'stored', {})
        self.next = self.POOL
        self.services[self.ALLOCATE] = self.allocate
        self.services[self.RELEASE] = lambda a: 0
        engine = self.where['L01c32db0']
        self.cpu.mem.write(engine + 48, (400_000).to_bytes(4, 'little'))
        self.cpu.mem.write(engine + 52, self.ALLOCATE.to_bytes(4, 'little') + self.RELEASE.to_bytes(4, 'little'))
        for name, answer in (('preset_storage_preparation_prepare', 0), ('preset_storage_preparation_record_copy', 0), ('preset_storage_preparation_invalidate', 0),
                             ('preset_loader_elapsed', 0), ('storage_platform_clock', 0), ('preset_storage_available', 1)):
            if name in self.where:
                self.services[self.where[name]] = lambda a, answer=answer: answer
        self.services[self.where['preset_storage_address']] = lambda a: PRESETS + HALF * a[0]
        self.services[self.where['storage_control_read']] = self.preset_read
        self.services[self.where['preset_storage_preparation_replace_pair']] = self.pair

    def allocate(self, a):
        at = self.next
        if at + a[0] > self.POOL_END:
            return 0
        self.next = at + a[0] + 63 & ~63
        return at

    def preset_read(self, a):
        where = divmod(a[0] - PRESETS, HALF)
        data = self.stored[where[0]][where[1]:][:a[2]] if where[0] in self.stored else bytes(self.flash[a[0]:a[0] + a[2]])
        self.cpu.mem.write(a[1], data + b'\xff' * (a[2] - len(data)))
        self.events.append(('read', a[2], self.cpu.steps))
        return 0

    def pair(self, a):
        second = int.from_bytes(self.cpu.mem.read(self.cpu.sp, 4), 'little')
        sector = a[0] if a[0] < 64 else (a[0] - PRESETS) // 0x1000
        if a[2]:
            self.stored[2 * sector] = self.cpu.mem.read(a[1], a[2])
        if second and second < 0x1000:
            self.stored[2 * sector + 1] = self.cpu.mem.read(a[3], second)
        return 0

    def setting(self, at, form='i'):
        return struct.unpack('<' + form, self.cpu.mem.read(self.where['L01c1f180'] + at, struct.calcsize(form)))[0]

    def says(self, *lines):
        """The first line of each answer; what SNAPCAP says of the preset's own capture is kept apart."""
        self.events.clear()
        out = []
        for line in lines:
            answer, _, own = (self.line(line, limit=200_000_000) or [''])[0].partition(' preset=')
            if answer.startswith('SNAPCAP'):
                self.own = int(own)
            out.append(answer + (' preset=' + own if own and not answer.startswith('SNAPCAP') else ''))
        return out

    def now(self):
        """The capture that plays, and how many were put in since the last line."""
        return self.setting(SET_CAPTURE, 'B'), sum(n == 'quiet' or n in ('audio_pause_pause_audio', 'mode_and_settings_mode_service') and (n[0] == 'm' or self.held(i))
                                                   for i, (n, _, _) in enumerate(self.events))

    def held(self, i):
        return i + 1 < len(self.events) and self.events[i + 1][0] == 'dispatch_helpers_audio_hold'

    def payload(self, preset):
        return self.stored[preset][40:]


def check(build, before, row):
    p = Pedal(build)
    first = p.embedded()
    for slot, data in ((0, first), (1, swap.other(first)), (2, swap.other(first, 2000, 3))):
        p.upload_capture(data)
        p.line(f'CSAVE {slot} Capture {slot}')
    p.running(False)
    p.says('PNEW', 'CLOAD 0')
    p.call('audio_task_warmup')
    p.running()
    none = 'SNAPCAP' + ' -1' * 8
    row('at first every scene has the preset\'s', p.says('SNAPCAP') == [none], p.lines)
    row('not for a scene that is not there, and nothing that is no scene or capture', all(a.startswith('ERR SNAPCAP') for a in p.says('SNAPCAP 0 1', 'SNAPCAP 8 1', 'SNAPCAP -1 1', 'SNAPCAP x 1', 'SNAPCAP 0 15')), p.lines)
    p.says('FXA P 99 boost', 'FXA Q 99 eq', 'SNAPSAVE 0', 'FXP 0 0 6', 'SNAPSAVE 1', 'FXP 0 0 9', 'SNAPSAVE 2')
    row('refused: no number, too large', all(a.startswith('ERR SNAPCAP') for a in p.says('SNAPCAP 0', 'SNAPCAP 0 15', 'SNAPCAP 0 -2', 'SNAPCAP 0 x', 'SNAPCAP 0 1 2', 'SNAPCAP 0 1x', 'SNAPCAP 0 100')) and p.says('SNAPCAP') == [none], p.lines)

    # another one for two of the three scenes
    a = p.says('SNAPCAP 1 1')
    row('for a scene that is not on: kept, and nothing is loaded', a == ['SNAPCAP -1 1 -1 -1 -1 -1 -1 -1'] and p.now() == (0, 0), [a, p.now()])
    a = p.says('SNAPCAP 2 2')
    row('for the scene that is on: loaded at once', a == ['SNAPCAP -1 1 2 -1 -1 -1 -1 -1'] and p.now() == (2, 1), [a, p.now()])
    went = []
    for scene, capture in ((0, 0), (1, 1), (2, 2), (1, 1), (1, 1), (0, 0)):
        a = p.says(f'SNAP {scene}')
        went.append((a[0].split(' missing')[0] == f'SNAP ok {scene}', p.now()[0] == capture, p.now()[1]))
    row('each scene brings its capture, and only when it is another', [w[:2] for w in went] == [(True, True)] * 6 and [w[2] for w in went] == [1, 1, 1, 1, 0, 1], went)
    knob = []
    for scene in (1, 2, 0):
        p.says(f'SNAP {scene}')
        knob.append(struct.unpack('<h', p.cpu.mem.read(p.where['L01c2c220'] + 70, 2))[0])
    row('and its knobs', knob[:2] == [6, 9], knob)
    owns = []
    for scene in (1, 2, 0):
        p.says(f'SNAP {scene}', 'SNAPCAP')
        owns.append(p.own)
    row('the preset\'s own capture is told whatever plays', owns == [0, 0, 0], owns)

    # stored and loaded
    p.says('SNAP 1')
    a = p.says('PSAVE 0 Three')
    body = p.payload(0)
    row('a preset is stored with its own capture while that of a scene plays', a[0].startswith('PSAVE ok 0') and body[2] == 0 and p.now() == (1, 0), [a, body[:8].hex()])
    row('in the form 7, with the numbers', body[0] == 7 and bytes([0, 2, 3, 0, 0, 0, 0, 0]) in body, body[:1].hex())
    p.says('SNAPCAP 1 -1')
    row('-1 is the preset\'s again', p.now()[0] == 0 and p.says('SNAPCAP') == ['SNAPCAP -1 -1 2 -1 -1 -1 -1 -1'] and p.own == 0, [p.now(), p.lines])
    p.says('SNAPCAP 2 -1')
    a = p.says('PSAVE 1 Plain')
    plain = p.payload(1)
    row('without such a scene it is stored as ever, in the form 5', plain[0] == 5 and len(plain) <= 1490, [plain[0], len(plain)])
    a = p.says('PLOAD 0')
    row('a preset starts with the capture of its scene, loaded once', p.now() == (1, 1) and p.setting(SET_SCENE) == 1 and p.says('SNAPCAP') == ['SNAPCAP -1 1 2 -1 -1 -1 -1 -1'], [a, p.now(), p.lines])
    a = p.says('SNAP 0')
    row('and its other scenes have the preset\'s', p.now() == (0, 1), [a, p.now()])
    p.says('SNAP 2')
    a = p.says('PLOAD 1')
    row('another preset has its own', p.now()[0] == 0 and p.says('SNAPCAP') == [none], [a, p.now(), p.lines])
    p.says('PLOAD 0', 'SNAP 2')
    again = (p.says('PSAVE 2 Copy'), p.payload(2))
    row('stored again from another scene: the same own capture and numbers', again[1][0] == 7 and again[1][2] == 0 and bytes([0, 2, 3, 0, 0, 0, 0, 0]) in again[1], again[1][:8].hex())

    # a scene that is kept, new, deleted
    p.says('SNAPSAVE 2')
    row('a scene that is kept keeps its capture', p.says('SNAPCAP') == ['SNAPCAP -1 1 2 -1 -1 -1 -1 -1'], p.lines)
    p.says('SNAPSAVE 3')
    row('a new scene has the one that plays', p.says('SNAPCAP') == ['SNAPCAP -1 1 2 2 -1 -1 -1 -1'] and p.now()[0] == 2, p.lines)
    p.says('SNAP 0', 'SNAPSAVE 4')
    row('or the preset\'s, when that plays', p.says('SNAPCAP') == ['SNAPCAP -1 1 2 2 -1 -1 -1 -1'], p.lines)
    p.says('SNAP 3', 'SNAPDEL 3')
    p.says('SNAPSAVE 3')
    p.says('PSAVE 2 Copy')
    row('after the scene that plays was deleted the preset has its own capture still', p.payload(2)[2] == 0, p.payload(2)[:8].hex())

    # by hand
    p.says('PLOAD 0', 'SNAP 1', 'CLOAD 2')
    a = p.says('SNAP 0')
    row('a capture that is loaded by hand is the preset\'s from then on', p.now()[0] == 2, [a, p.now()])
    a = p.says('SNAP 1')
    row('and the scene still has its own', p.now()[0] == 1, [a, p.now()])
    # as the editor does after a file was uploaded for this scene alone: what it had, and then the new one
    p.says('PLOAD 0', 'SNAP 1', 'CLOAD 2', 'SNAPCAP', 'CLOAD 1', 'SNAPCAP 1 2', 'SNAPCAP')
    row('the one it had loaded again by hand, and then another for it: the preset keeps its own', p.own == 0 and p.setting(SET_CAPTURE, 'B') == 2, [p.own, p.now()])
    p.says('PLOAD 0', 'SNAP 1', 'CLOAD 2', 'SNAP 0', 'SNAP 1')
    p.says('PSAVE 3 Hand')
    row('stored so', p.payload(3)[2] == 2, p.payload(3)[:8].hex())
    p.says('PLOAD 0', 'SNAP 2', 'PNEW')
    p.says('FXA P 99 boost', 'SNAPSAVE 0', 'PSAVE 4 New')
    row('a new preset has the capture that plays', p.payload(4)[0] == 5 and p.payload(4)[2] == p.setting(SET_CAPTURE, 'B'), [p.payload(4)[:4].hex(), p.now()])

    # one that is gone, and the memory lent
    p.says('PLOAD 0', 'SNAP 0', 'CDEL 1')
    a = p.says('SNAP 1')
    row('a capture that is gone: the scene comes with the one that plays', a[0].startswith('SNAP ok 1') and p.now()[0] == 0, [a, p.now()])
    p.says('PLOAD 0', 'SNAP 0')
    p.state(swap.LENT, 1)
    a = p.says('SNAP 2')
    row('not while its memory is lent to the effects', a[0].startswith('SNAP ok 2') and p.setting(SET_CAPTURE, 'B') == 0, [a, p.now()])
    p.state(swap.LENT, 0)

    if before:
        old = Pedal(before)
        old.upload_capture(first)
        old.line('CSAVE 0 Capture 0')
        old.running(False)
        old.says('PNEW', 'CLOAD 0')
        old.running()
        old.says('FXA P 99 boost', 'FXA Q 99 eq', 'SNAPSAVE 0', 'FXP 0 0 6', 'SNAPSAVE 1', 'FXP 0 0 9', 'SNAPSAVE 2', 'SNAP 1', 'PSAVE 1 Plain')
        row('the same preset without such a scene is stored by the build before with the same bytes', old.payload(1) == plain, sum(x != y for x, y in zip(old.payload(1), plain)))
        old.stored[5] = p.stored[0]
        answer = old.says('PLOAD 5')
        row('the build before takes the new form as an empty place', answer[0].startswith('ERR'), answer)
        old.stored[6] = p.stored[1]
        answer = old.says('PLOAD 6')
        row('and reads the others', answer[0].startswith('PLOAD ok 6'), answer)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--before', type=Path)
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append(bool(good))
        print(('ok   ' if good else 'FAIL ') + name, '' if good else seen, flush=True)
    check(args.build.resolve(), args.before and args.before.resolve(), row)
    print(json.dumps({'kind': 'mini-scene-captures-check', 'held': all(rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
