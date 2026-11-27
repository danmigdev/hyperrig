"""Put another capture into the engine without a stop (mini/product/swap.c), in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of app.bin: the console lines, the loader, the parser, the heap, the engine. Replaced are the
flash, the pause of the sound, the hold of the second processor, the start and stop of the engine, which are recorded, and the sound task's
answer at the gate (it leaves the capture alone when asked). Checked: after the short way the engine's memory is, byte by byte, what the long
way leaves, and it plays the same samples; the capture is read before the gate is asked, and what is done while the capture is left alone is
counted; the sound is not paused; without an answer of the sound task the application's pause is taken; what does not fit, is damaged or
cannot be read goes the application's way, or leaves what played as it was; and the gate is always opened again.

This is no hardware or audio test: the gap that is heard, the fades and the processor's time are not simulated. Instructions are counted.

Usage, from the repository root:
    python -B tools/check_mini_swap.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_library as library  # noqa: E402

sim = library.sim
MODE, LENT, ARENA, ARENA_BYTES, GOOD, SOURCE = 280, 416, 436, 440, 500, 676
IDLE, ASKED, QUIET, BACK = range(4)                     # the gate of swap.c
IN, OUT = 0x01C70000, 0x01C71000
ORDER = ('audio_pause_pause_audio', 'audio_pause_resume_audio', 'dispatch_helpers_audio_hold', 'mode_and_settings_mode_service', 'audio_task_warmup')


class Pedal(library.Pedal):
    """One pedal with two captures in its slots, the engine's state as while it runs."""

    def __init__(self, build):
        super().__init__(build, bytearray(b'\xff' * 0x100000))
        self.shortcuts()

    def restart(self):
        super().restart()
        self.events = []
        for name in ORDER:
            if name != 'audio_task_warmup':
                self.services[self.where[name]] = lambda a, n=name: self.events.append((n, a[0], self.cpu.steps)) or 0
        inner = self.read

        def read(a):
            self.events.append(('read', a[2], self.cpu.steps))
            return inner(a)
        self.services[self.where['storage_control_device_read']] = read

    def answered(self):
        self.events.append(('quiet', None, self.cpu.steps))

    def gate(self):
        return self.cpu.mem.read(self.where['hyperrig_gate'], 1)[0]

    def call(self, name, *args, limit=80_000_000):
        cpu = self.cpu
        cpu.R[:len(args)] = [a & sim.M for a in args]
        cpu.rets, cpu.pc, cpu.sp, start = sim.RETURN, self.where[name], sim.STACK_TOP, cpu.steps
        while cpu.pc != sim.RETURN:
            service = self.services.get(cpu.pc)
            if service:
                cpu.R[0] = (service(list(cpu.R[:4])) or 0) & sim.M
                cpu.pc = cpu.rets
                continue
            cpu.step()
            if cpu.steps - start > limit:
                raise RuntimeError(f'{name}: too many steps')
        return cpu.R[0]

    def state(self, at, value=None, form='I'):
        address = self.where['L01c26890'] + at
        if value is not None:
            self.cpu.mem.write(address, struct.pack('<' + form, value))
        return struct.unpack('<' + form, self.cpu.mem.read(address, struct.calcsize(form)))[0]

    def running(self, on=True):
        self.state(MODE, 2 if on else 0)

    def engine(self):
        """What the capture is in the engine: the context and its arena."""
        arena, size = self.state(ARENA), self.state(ARENA_BYTES)
        return self.cpu.mem.read(self.where['L01c2bff0'] + 76, 240), self.cpu.mem.read(arena, size)

    def play(self, count=6):
        out = []
        for k in range(count):
            block = [round(4_000_000 * math.sin(2 * math.pi * 110 * (128 * k + i) / 48077)) for i in range(128)]
            self.cpu.mem.write(IN, struct.pack('<128i', *block))
            self.call('capture_live_process', self.where['L01c2bff0'] + 76, IN, OUT, 128)
            out += struct.unpack('<128i', self.cpu.mem.read(OUT, 512))
        return out

    def load(self, line):
        if self.gate() == BACK:                          # the sound task's next block has faded the capture in
            self.cpu.mem.write(self.where['hyperrig_gate'], bytes([IDLE]))
        self.events.clear()
        answer = self.line(line, limit=200_000_000)
        self.end = self.cpu.steps
        return answer, [(n, v) for n, v, _ in self.events]

    def alone(self):
        """Steps and reads from the sound task's answer at the gate to the end of the line."""
        a = [s for m, v, s in self.events if m == 'quiet'][0]
        return self.end - a, sum(v for m, v, s in self.events if m == 'read' and s >= a)


def other(data, at=1000, by=1):
    """The same capture with a number changed, and its checksum."""
    body = bytearray(data[:-4])
    body[at] ^= by
    return bytes(body) + struct.pack('<I', zlib.crc32(body))


def check(build, row):
    p = Pedal(build)
    first = p.embedded()
    second, third = other(first), other(first, 2000, 3)
    for slot, data, name in ((0, first, 'First'), (1, second, 'Second'), (2, third, 'Third')):
        p.upload_capture(data)
        p.line(f'CSAVE {slot} {name}')
    # the long way, with the engine stopped, and the network settled as at its start
    long_way, sounds = {}, {}
    for slot in (0, 1, 2):
        p.running(False)
        answer, events = p.load(f'CLOAD {slot}')
        p.call('audio_task_warmup')
        long_way[slot], sounds[slot] = p.engine(), None
    row('the engine is stopped when it does not run', answer == ['CLOAD ok 2 audio=0'] and [n for n, _ in events if n in ORDER] == ['mode_and_settings_mode_service'], events)
    for slot in (0, 1, 2):
        p.running(False)
        p.load(f'CLOAD {slot}')
        p.call('audio_task_warmup')
        sounds[slot] = p.play()
    row('the three captures sound different', len({tuple(s) for s in sounds.values()}) == 3, None)

    # the short way
    p.running(False)
    p.load('CLOAD 0')
    p.call('audio_task_warmup')
    p.running()
    p.play(3)                                            # what it was doing
    for slot in (1, 2, 0, 1):
        answer, events = p.load(f'CLOAD {slot}')
        order = [n for n, v in events if n != 'read']
        row(f'capture {slot + 1}: no pause, no hold, no stop: the sound task leaves the capture alone, then it is back', answer == [f'CLOAD ok {slot} audio=2'] and order == ['quiet']
            and p.gate() == BACK, [answer, order, p.gate()])
        steps, read = p.alone()
        row(f'capture {slot + 1}: nothing is read while it is left alone', read == 0, {'steps_while_alone': steps, 'ms_about': round(steps * 2.1 / 349e3, 2)})
        mine, want = p.engine(), long_way[slot]
        row(f'capture {slot + 1}: the engine is as after a stop', mine == want, [mine[0] == want[0], sum(a != b for a, b in zip(mine[1], want[1]))])
        row(f'capture {slot + 1}: it plays the same samples', p.play() == sounds[slot], None)
        source = p.cpu.mem.read(p.state(SOURCE), len(first)) if p.state(SOURCE) else b''
        row(f'capture {slot + 1}: the application has it as its own', source == (first, second, third)[slot], None)

    # a sound task that does not answer: the application's pause, and the gate is not left asked
    p.deaf = True
    answer, events = p.load('CLOAD 2')
    p.deaf = False
    order = [(n, v if n == 'dispatch_helpers_audio_hold' else None) for n, v in events if n != 'read']
    row('without an answer of the sound task: the pause of the application, and the gate is closed', answer == ['CLOAD ok 2 audio=2'] and order == [('audio_pause_pause_audio', None),
        ('dispatch_helpers_audio_hold', 1), ('dispatch_helpers_audio_hold', 0), ('audio_pause_resume_audio', None)] and p.gate() == IDLE, [answer, order, p.gate()])
    mine, want = p.engine(), long_way[2]
    row('and the engine is as after a stop', mine == want, None)

    # what does not go the short way
    p.load('CLOAD 0')
    p.state(LENT, 1)
    answer, events = p.load('CLOAD 1')
    row('not while its memory is lent to the effects', 'dispatch_helpers_audio_hold' not in [n for n, _ in events] and ('mode_and_settings_mode_service', 0) in events, [answer, events])
    p.state(LENT, 0)
    p.running(False)
    p.load('CLOAD 0')
    p.running()
    p.state(GOOD, 0, 'B')
    answer, events = p.load('CLOAD 1')
    row('not when none is in the engine', 'audio_pause_pause_audio' not in [n for n, _ in events], [answer, events])
    p.load('CLOAD 0')
    size = p.state(ARENA_BYTES)
    p.state(ARENA_BYTES, 1000)
    answer, events = p.load('CLOAD 1')
    row('not into less memory than it needs', 'audio_pause_pause_audio' not in [n for n, _ in events], [answer, events, size])

    # damaged in the flash, and no memory: what plays goes on
    p.running(False)
    p.load('CLOAD 2')
    p.call('audio_task_warmup')
    want = p.engine()                                    # its memory is another now
    p.load('CLOAD 0')
    p.call('audio_task_warmup')
    p.running()
    before = p.engine()
    lo = library.CAPTURE_SLOTS and 0xDF000 + 0x2000
    keep = p.flash[lo + 600]
    p.flash[lo + 600] ^= 0x10
    answer, events = p.load('CLOAD 1')
    row('a slot that is damaged is refused, and the sound is never paused nor the gate asked', answer[0].startswith('ERR') and not {'audio_pause_pause_audio', 'quiet'} & {n for n, _ in events}
        and p.gate() == IDLE, [answer, events])
    p.flash[lo + 600] = keep
    p.running(False)
    p.load('CLOAD 0')
    p.call('audio_task_warmup')
    p.running()
    p.services[p.where['L0203c15c']] = lambda a: 0
    answer, events = p.load('CLOAD 1')
    del p.services[p.where['L0203c15c']]
    row('without memory to read it nothing is paused nor asked', answer[0].startswith('ERR') and not {'audio_pause_pause_audio', 'quiet'} & {n for n, _ in events} and p.engine() == before,
        [answer, events])
    # refused by the loader after all: the one before comes back, and the pause is ended
    p.running()
    loader, calls = p.where['capture_dispatch_load'], []

    def refuse(a):
        calls.append(a)
        del p.services[loader]
        return -3
    p.services[loader] = refuse
    answer, events = p.load('CLOAD 1')
    names = [n for n, _ in events]
    row('refused by the loader after all: the capture is back at the gate, nothing was paused', bool(calls) and answer[0].startswith('ERR') and names.count('quiet') == 1
        and 'audio_pause_pause_audio' not in names and p.gate() == BACK, [answer, events, p.gate()])
    row('and the one before is in the engine', p.engine()[1] == before[1], None)
    answer, events = p.load('CLOAD 2')
    row('the next one goes the short way again', answer == ['CLOAD ok 2 audio=2'] and p.engine() == want and not {'mode_and_settings_mode_service', 'audio_pause_pause_audio'} & {n for n, _ in events},
        [answer, [e for e in events if e[0] != 'read']])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append(bool(good))
        print(('ok   ' if good else 'FAIL ') + name, '' if good and not isinstance(seen, dict) else seen, flush=True)
    check(args.build.resolve(), row)
    print(json.dumps({'kind': 'mini-swap-check', 'held': all(rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
