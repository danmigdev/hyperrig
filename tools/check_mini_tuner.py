"""Open and close the tuner of a built product firmware when there is little memory, in the pi32v2 simulator. Offline; no device is opened.

The main task's own lines run from the bytes of the firmware, with the application's own pools: the memory from the heap, from the effects' memory
in one piece, from the effects' memory in pieces, from the second memory, and none at all; what is in the other blocks, where they are told to have
moved, how often the sound is paused, what TUNE answers, and where the memory goes when the tuner is closed. The heap, the pause of the sound and the
effects that own the blocks are stood for here. Nothing of this is a hardware or audio test.

Usage, from the repository root:
    python -B tools/check_mini_tuner.py BUILD [--before BUILD]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. --before: a build that did not put the memory together, which must be
refused where this one is not."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_panel as harness  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402

sim, codec = scenes.sim, scenes.codec
STATE, SETTINGS = 'L01c26890', 'L01c1f180'
POOL, SECOND, SECOND_THERE, TUNER, NONE, MEMORY, TAKEN, PAUSED, STOPPED, ENGINE = 2452, 2488, 416, 52, 54, 1016, 1020, 20, 21, 280
FIRST_AT, SECOND_AT, HEAP_AT, NEED = 0x01D00000, 0x01D40000, 0x01D80000, 7168
ONCE = ['pause', 'hold', 'go', 'resume']
OPEN, GOT, NOT, CLOSE = 'L020186ae', 'L020186fe', 'L0201938e', 'L02018698'


class Board(scenes.Pedal):
    def __init__(self, build):
        super().__init__(build)
        self.heap, self.freed, self.sound, self.fixed, self.moved = 0, [], [], set(), []
        w = self.where
        self.at[w['heap_access_vendor_allocate_wrapper']] = lambda a: self.heap
        self.at[w['L0203d218']] = lambda a: self.freed.append(a[0]) or 0
        self.at[w['audio_pause_pause_audio']] = lambda a: self.pause(1)
        self.at[w['audio_pause_resume_audio']] = lambda a: self.pause(0)
        self.at[w['dispatch_helpers_audio_hold']] = lambda a: self.hold(a[0])
        self.at[w['effect_relocation_relocate']] = self.relocate
        self.state(ENGINE, 2, 4)
        self.state(TUNER, 1, 1)

    def state(self, at, value=None, size=4):
        form = {1: 'B', 4: 'I'}[size]
        if value is not None:
            self.mem.write(self.where[STATE] + at, struct.pack('<' + form, value))
        return struct.unpack('<' + form, self.mem.read(self.where[STATE] + at, size))[0]

    def pause(self, on):
        self.sound.append('pause' if on else 'resume')
        self.state(PAUSED, on, 1)
        self.state(STOPPED, on, 1)
        return 0

    def hold(self, on):
        self.sound.append('hold' if on else 'go')
        self.state(328, on)
        self.state(332, on)
        return 0

    def relocate(self, a):
        old, new, done = a[:3]
        if old in self.fixed:
            return 0
        if done:
            self.moved.append((old, new))
        return 1

    def pool(self, which, base, size):
        self.run('ir_reload_and_leaves_pool_setup', self.where[STATE] + which, base, size)

    def take(self, which, size):
        at = self.run('block_pool_allocate', self.where[STATE] + which, size)
        if at:
            self.mem.write(at, bytes((at >> 4) + k & 255 for k in range(size)))
        return at

    def give(self, which, at):
        self.run('block_pool_release', self.where[STATE] + which, at)

    def free(self, which):
        return self.state(which + 4) - self.state(which + 8)

    def lines(self, start, stops, *, memory=0):
        """The main task's lines from one label to another, with the registers it keeps."""
        cpu = self.cpu
        stops = {self.where[s] for s in stops}
        cpu.R[14], cpu.R[13], cpu.R[9], cpu.R[7], cpu.R[1] = self.where[STATE], self.where[SETTINGS], 0, 1, memory
        cpu.sp, cpu.pc, first = sim.STACK_TOP, self.where[start], cpu.steps
        while cpu.pc not in stops:
            own = self.at.get(cpu.pc)
            if own:
                cpu.R[0] = own(list(cpu.R[:4])) & sim.M
                cpu.pc = cpu.rets
                continue
            insn, raw, size = cpu.decode(cpu.pc)
            if codec.format(insn, raw) in ('lockset', 'csync'):
                cpu.pc += size
                continue
            cpu.step()
            assert cpu.steps - first < 3_000_000, 'too many steps'
        return next(s for s in (GOT, NOT, CLOSE) if self.where[s] == cpu.pc)

    def open(self):
        self.sound.clear()
        self.moved.clear()
        self.lines(OPEN, (GOT, NOT))
        return self.state(MEMORY)

    def close(self):
        self.freed.clear()
        self.lines(CLOSE, (NOT,), memory=self.state(MEMORY))
        return self.state(MEMORY)

    def intact(self, blocks):
        """Each block holds what was written into it, at the place it was told to have moved to."""
        places = dict(blocks)
        for old, new in self.moved:
            for first, now in list(places.items()):
                if now[0] == old:
                    places[first] = (new, now[1])
        return all(self.mem.read(at, size) == bytes((first >> 4) + k & 255 for k in range(size)) for first, (at, size) in places.items())


def pieces(b, which=POOL, base=FIRST_AT, size=40_000, block=5_000, fixed=()):
    """A pool with a hole after each block: much room, no large piece."""
    b.pool(which, base, size)
    taken = []
    while at := b.take(which, block):
        taken.append(at)
    kept = {at: (at, block) for at in taken[::2]}
    for at in taken[1::2]:
        b.give(which, at)
    b.fixed = {taken[k] for k in fixed}
    return kept


def check(build, before=None):
    rows = []

    def row(name, good, seen):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    b = Board(build)
    b.heap = HEAP_AT
    got = b.open()
    row('with room in the heap: from the heap, the sound not paused', (got, b.sound, b.state(NONE, size=1)) == (HEAP_AT, [], 0), [hex(got), b.sound])
    b.close()
    row('which takes it back', (b.freed, b.state(MEMORY)) == ([HEAP_AT], 0), b.freed)

    b = Board(build)
    b.pool(POOL, FIRST_AT, 20_000)
    other = {at: (at, 3_000) for at in [b.take(POOL, 3_000)]}
    got = b.open()
    row('with one piece of the memory of the effects: from there', FIRST_AT < got < FIRST_AT + 20_000 and b.sound == ONCE and b.intact(other),
        [hex(got), b.sound])
    room = b.free(POOL)
    b.close()
    row('which takes it back, not the heap', (b.freed, b.state(MEMORY)) == ([], 0) and b.free(POOL) >= room + NEED, [b.freed, room, b.free(POOL)])

    b = Board(build)
    other = pieces(b)
    room = b.free(POOL)
    got = b.open()
    row('with the room in pieces: put together, nothing lost, the sound paused once',
        FIRST_AT < got < FIRST_AT + 40_000 and b.sound == ONCE and b.moved and b.intact(other) and b.state(NONE, size=1) == 0,
        [hex(got), room, b.sound, len(b.moved)])
    b.mem.write(got, b'\x5a' * NEED)
    row('its memory is nobody else\'s', b.intact(other), None)
    b.close()
    row('and is given back', b.free(POOL) == room and b.freed == [], [b.free(POOL), room])
    if before:
        old = Board(before)
        pieces(old)
        row('the build before was refused there', old.open() == 0 and old.state(NONE, size=1) == 1, None)

    b = Board(build)
    other = pieces(b, fixed=(2,))
    got = b.open()
    row('a block that cannot move stays where it is', got and b.intact(other) and all(old not in b.fixed for old, _ in b.moved), [hex(got), len(b.moved)])

    b = Board(build)
    b.pool(POOL, FIRST_AT, 20_000)
    other = {}
    while at := b.take(POOL, 3_000):
        other[at] = (at, 3_000)
    seen = []
    for _ in range(3):
        seen.append((b.open(), list(b.sound), b.state(NONE, size=1)))
    row('with no room: none, asked once while the tuner is open', seen == [(0, ONCE, 1), (0, [], 1), (0, [], 1)] and b.intact(other), seen)
    said = b.say('TUNE')
    row('and TUNE says so', len(said) == 1 and said[0].startswith('TUNE - ') and said[0].endswith(' nomem'), said)
    b.heap = HEAP_AT
    row('the heap is asked in every turn', b.open() == HEAP_AT and b.state(NONE, size=1) == 0, None)
    b.close()
    b.heap = 0
    b.state(TUNER, 0, 1)
    b.panel.turns(1)
    b.state(TUNER, 1, 1)
    row('opened again it asks again', (b.open(), b.sound) == (0, ONCE), b.sound)

    b = Board(build)
    b.pool(POOL, FIRST_AT, 9_000)
    b.take(POOL, 6_000)
    other = pieces(b, SECOND, SECOND_AT)
    row('a second memory that is not in use is not asked', b.open() == 0, None)
    b = Board(build)
    b.pool(POOL, FIRST_AT, 9_000)
    b.take(POOL, 6_000)
    other = pieces(b, SECOND, SECOND_AT)
    b.state(SECOND_THERE, 1)
    room, got = b.free(SECOND), b.open()
    row('the second memory, when it is in use', SECOND_AT < got < SECOND_AT + 40_000 and b.intact(other), hex(got))
    b.close()
    row('which takes it back, not the heap', b.free(SECOND) == room and b.freed == [] and b.state(MEMORY) == 0, [b.free(SECOND), room, b.freed])
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--before', type=Path)
    args = parser.parse_args(argv)
    rows = check(args.build, args.before)
    for r in rows:
        print('ok  ' if r['held'] else 'FAIL', r['check'], '' if r['held'] else r['seen'])
    held = all(r['held'] for r in rows)
    print(json.dumps({'held': held, 'checks': len(rows), 'hardware_test': False}))
    return 0 if held else 1


if __name__ == '__main__':
    sys.exit(main())
