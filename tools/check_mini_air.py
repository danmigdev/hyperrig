"""HyperRig's part of the Bluetooth link (mini/product/air.c), in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of app.bin; replaced are the end of a link (console_helpers_ble_drop), which is recorded, and
whether the pedal takes changes from the link (console_helpers_key_window), which the check sets. Checked: which of HyperRig's words a line
that came over Bluetooth may carry, always, with the key, or not at all; that a link on which no line came for 90 seconds is ended, and again
after as long, and that a line that came keeps it; that HRBYE ends it in the next turn; that the minute for letting a device in ends when the
link becomes one the pedal takes changes from, on that edge only, and again for another link.

This is no hardware test: the radio, the application's lists of words and the gate in the main task are not run here.

Usage, from the repository root:
    python -B tools/check_mini_air.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_swap as swap  # noqa: E402

LINE, LINK, MINUTE, SILENT = 0x01C70000, 82, 1532, 90000
ALWAYS = ['HRID', 'HRST', 'HRBYE', 'AMPK', 'MIDI', 'KNOB', 'HRLV', 'SNAPCAP']
WITH_KEY = ['MIDI on', 'KNOB off', 'HRLV 0612020c04', 'FXC 1 33', 'SNAPCAP 1 0', 'SNAPCAP 0 -1']
NEVER = ['STAGE', 'STAGE GO', 'REC 4 184', 'RECD 0', 'INJBEGIN 1408', 'INJB 0 00', 'HRID x', 'HRST now', 'AMPK 1', 'FXC', 'HRBYE now',
         'HRIDX', 'SNAPCAPS', 'SNAPCAP\t1', 'HRBT', 'UBOOT', '']


class Pedal(swap.Pedal):
    def restart(self):
        super().restart()
        self.dropped, self.window = [], 0
        self.services[self.where['console_helpers_ble_drop']] = lambda a: self.dropped.append(a[0]) or 0
        self.services[self.where['console_helpers_key_window']] = lambda a: self.window

    def air(self, line):
        self.cpu.mem.write(LINE, line.encode('ascii') + b'\0')
        return self.call('hyperrig_air', LINE)

    def link(self, handle=None):
        if handle is not None:
            self.state(LINK, handle, 'H')
        return self.state(LINK, form='H')

    def minute(self, value=None):
        return self.state(MINUTE, value, 'B')

    def turn(self, now):
        before = len(self.dropped)
        self.call('hyperrig_air_turn', now)
        return self.dropped[before:]


def check(build, row):
    p = Pedal(build)
    seen = {line: p.air(line) for line in ALWAYS + WITH_KEY + NEVER}
    row('HyperRig\'s words by themselves that only read: always', all(seen[w] == 2 for w in ALWAYS), {w: seen[w] for w in ALWAYS})
    row('with something after them: with the key', all(seen[w] == 1 for w in WITH_KEY), {w: seen[w] for w in WITH_KEY})
    row('the cable\'s words, other forms and other words: not over Bluetooth', all(seen[w] == 0 for w in NEVER),
        {w: seen[w] for w in NEVER if seen[w]})

    # silence
    p.link(0)
    row('without a link nothing is ended', p.turn(1000) == [] and p.turn(1000 + 10 * SILENT) == [], p.dropped)
    p.link(0x50)
    a = p.turn(2000)
    b = p.turn(2000 + SILENT - 1)
    c = p.turn(2000 + SILENT)
    d = p.turn(2000 + 2 * SILENT - 1)
    e = p.turn(2000 + 2 * SILENT)
    row('a link on which no line came is ended after 90 s, and again after as long', (a, b, c, d, e) == ([], [], [0x50], [], [0x50]), [a, b, c, d, e])
    t = 2000 + 2 * SILENT
    p.call('hyperrig_air_heard')
    f = p.turn(t + 50000)                                # the line is seen here: the 90 s count from now
    g = p.turn(t + 50000 + SILENT - 1)
    h = p.turn(t + 50000 + SILENT)
    row('a line that came keeps it for 90 s more', (f, g, h) == ([], [], [0x50]), [f, g, h])
    p.call('hyperrig_air_bye')
    i = p.turn(t + 50000 + SILENT + 10)
    j = p.turn(t + 50000 + SILENT + 20)
    row('HRBYE ends it in the next turn, once', (i, j) == ([0x50], []), [i, j])
    p.link(0)
    p.turn(t + 200000)
    p.link(0x51)
    k = p.turn(t + 200001)
    row('another link is counted from when it is seen', k == [] and p.turn(t + 200001 + SILENT) == [0x51], k)

    # the minute for letting a device in
    p.link(0)
    p.turn(1)
    p.link(0x52)
    p.window = 0
    p.minute(1)
    p.turn(10)
    m1 = p.minute()
    p.window = 1
    p.turn(20)
    m2 = p.minute()
    p.minute(1)                                          # opened again by a device that is in, for another one
    p.turn(30)
    m3 = p.minute()
    p.window = 0
    p.turn(40)
    p.window = 1
    p.turn(50)
    m4 = p.minute()
    row('the minute runs while the link is not let in, and ends when it is', (m1, m2) == (1, 0), [m1, m2])
    row('only on that edge: a device that is in may open it for another one', m3 == 1 and m4 == 0, [m3, m4])
    p.minute(1)
    p.link(0x53)
    p.turn(60)
    row('a new link that is let in ends it as well', p.minute() == 0, p.minute())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append(bool(good))
        print(('ok   ' if good else 'FAIL ') + name, '' if good else seen, flush=True)
    check(args.build.resolve(), row)
    print(json.dumps({'kind': 'mini-air-check', 'held': all(rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
