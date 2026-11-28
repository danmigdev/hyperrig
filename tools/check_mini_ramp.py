"""Hold a switch of a product build in the pi32v2 simulator and check the ramp it makes (mini/product/ramp.c). Offline; no device is opened.

The application's own code runs from the bytes of a built firmware: the console words FSA and RAMP, the transitions of the switches as the
control scan hands them on (with pairs.c), the tick that fires holds, the actions, and the record of the settings that GSAVE keeps. The
chain of the preset, the knobs and the setting of a knob are stand-ins that record what they are asked: a block of a kind in a place, a knob
with its way and its value. What a knob does to the sound is not run; whether a tremolo changes its speed smoothly is for the ear, on the
pedal. Nothing of this is a hardware test.

Usage, from the repository root:
    python -B tools/check_mini_ramp.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_scenes as scenes  # noqa: E402

A, B, C = 0, 1, 2
G_ACTIONS, S_HOLD_DONE, G_PRESET, G_SCENE = 236, 932, 92, 88
TREMOLO, BOOST, SPEED = 23, 2, 0              # stand-in kinds and the knob from 0
RANGES = 0x01C79000                           # where the stand-in ways of the knobs are, for preset_application_metadata
HEAD, KEPT_MIDI, KEPT = 40, 64, 88


class Hold(scenes.Feet):
    """The switches, and a chain of stand-ins: places of (slot, kind), knobs of (slot, knob) with their values."""

    def __init__(self, build):
        super().__init__(build)
        p = self.p
        self.chain = [(3, BOOST), (5, TREMOLO)]
        self.values = {(3, 0): 40, (5, SPEED): 100}
        self.ways = {(TREMOLO, SPEED): (0, 1000), (BOOST, 0): (-60, 60)}
        self.applied, self.told, self.kept = [], [], None
        own = {
            'selection_effect_flatten': self.flatten,
            'preset_application_effect_type': lambda a: dict(self.chain).get(a[0], 0),
            'preset_application_metadata': self.metadata,
            'preset_application_parameter': lambda a: self.values.get((a[0], a[1]), 0) & 0xFFFFFFFF,
            'dispatch_helpers_parameter_apply': self.apply,
            'panel_inputs_event_queue': lambda a: self.told.append((a[0], a[1], a[2], self.now)) or 0,
            'settings_store_record_store': self.store,
            'mode_and_settings_record_scan': lambda a: 0,
        }
        for name, f in own.items():
            p.at[p.where[name]] = f

    def flatten(self, a):
        self.p.mem.write(a[0], bytes([len(self.chain)] + [k for _, k in self.chain]))
        self.p.mem.write(a[1], bytes(s for s, _ in self.chain))
        return 0

    def metadata(self, a):
        way = self.ways.get((a[0], a[1]))
        if not way:
            return 0
        self.p.mem.write(RANGES, struct.pack('<hh', *way))
        return RANGES

    def apply(self, a):
        value = a[2] - (1 << 32) if a[2] >> 31 else a[2]
        self.applied.append((a[0], a[1], value, a[3], self.now))
        self.values[(a[0], a[1])] = value
        return 0

    def store(self, a):
        self.kept = self.p.mem.read(a[0], a[1])
        return 0

    def turns(self, ms):
        for _ in range(ms // 10):
            self.now += 10
            self.p.run('control_actions_tick', 10, 1, self.now)
            self.p.run('hyperrig_pairs_turn', self.now)
            self.p.run('hyperrig_ramp_turn', self.now)

    def table(self, f, gesture):
        return list(self.p.mem.read(self.p.where['L01c1f180'] + G_ACTIONS + 9 * f + 3 * gesture, 3))

    def ramp(self, f, kind, knob, target, rise_ms, fall_ms):
        """The RAMP line that sets switch f's ramp, the others as they are."""
        now = bytes.fromhex(self.p.say('RAMP')[0].split()[1])
        mine = struct.pack('<BBhBB', kind, knob, target, rise_ms // 50, fall_ms // 50)
        return self.p.say('RAMP =' + (now[:6 * f] + mine + now[6 * f + 6:]).hex())

    def speed(self):
        return self.values[(5, SPEED)]


def check(build):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    s = Hold(build)
    p = s.p
    p.say('FSMODE layout=custom')
    for f in range(3):
        for g, x in ((0, (1, f, 255)), (1, (0, 0, 255)), (2, (0, 0, 255))):
            p.say(f'FSA {f} {g} {x[0]} {x[1]} {x[2]}')
    took = [p.say('FSA 0 1 11 0 255'), s.table(A, 1), p.say('FSA 0 1 12 0 255'), s.table(A, 1), p.say('FSA 0 1 13 0 255'), s.table(A, 1)]
    row('FSA takes the ramp (11) and the ramp on and off (12), and nothing above them', took[1] == [11, 0, 255] and took[3] == [12, 0, 255]
        and took[5] == [12, 0, 255], took)
    p.say('FSA 0 1 11 0 255')
    p.say('FSA 1 1 3 0 255')                              # B: its hold is the next preset, as before
    s.there(*range(8))
    s.turns(50)

    seen = s.ramp(A, TREMOLO, SPEED, 900, 1000, 500)
    row('RAMP says what it was given', seen and seen[0].split()[1][:12] == struct.pack('<BBhBB', TREMOLO, SPEED, 900, 20, 10).hex(), seen)
    bad = p.say('RAMP =00')
    row('RAMP with too few digits leaves them as they were', bad[0].split()[1] == seen[0].split()[1], bad)

    # a tap
    s.applied.clear()
    did = s.press(A, ms=120)
    row('a tap of a switch with a ramp is its tap, and nothing ramps', did == [('application select', 0)] and not s.applied, [did, s.applied])
    on_press = p.mem.read(p.where['L01c1f180'] + 11, 1)[0] & 1
    s.did.clear()
    s.put(A, 1)
    s.turns(150)
    early = list(s.did)
    s.put(A, 0)
    s.turns(100)
    row('its tap waits for the release, also when the switch fires on the press', on_press == 1 and early == [] and s.did == [('application select', 0)],
        [on_press, early, s.did])

    # a hold, up and back
    s.applied.clear(), s.told.clear(), s.did.clear()
    s.put(A, 1)
    s.turns(190)
    before = list(s.applied)
    s.turns(20)
    started = list(s.applied)
    s.turns(490)
    half = s.speed()
    s.turns(600)
    top, top_at = s.speed(), len(s.applied)
    s.put(A, 0)
    s.turns(250)
    falling = s.speed()
    s.turns(400)
    back = s.speed()
    values = [v for _, _, v, _, _ in s.applied]
    row('nothing moves in the first 200 ms of a hold', before == [] and len(started) >= 1, [before, started])
    row('held, the knob goes to the target in the rise time, step by step', 450 <= half <= 560 and top == 900
        and all(b >= a for a, b in zip(values[:top_at], values[1:top_at])) and max(b - a for a, b in zip(values[:top_at], values[1:top_at])) <= 12,
        [half, top, values[:5]])
    row('let go, it goes back in the fall time, to the value of the preset exactly', 450 <= falling <= 560 and back == 100 and values[-1] == 100,
        [falling, back, values[-3:]])
    row('the hold fires no hold action and nothing on the release', s.did == [], s.did)
    row('each step glides a little, as MIDI\'s knobs', {g for *_, g, _ in s.applied} == {4}, sorted({g for *_, g, _ in s.applied}))
    params = [t for t in s.told if t[0] == 112]
    row('the editor hears of the knob every 100 ms or so, and at the end', 10 <= len(params) <= 24 and params[-1][3] >= s.applied[-1][4] - 10,
        [len(params), len(s.applied)])
    row('the knob is the first block of its kind in the chain', {(sl, k) for sl, k, *_ in s.applied} == {(5, SPEED)}, None)

    # let go half way, pressed again on the way back
    s.applied.clear()
    s.put(A, 1)
    s.turns(700)
    mid = s.speed()
    s.put(A, 0)
    s.turns(120)
    low = s.speed()
    s.put(A, 1)
    s.turns(210)
    again = list(s.applied[-3:])
    s.turns(300)
    up = s.speed()
    s.put(A, 0)
    s.turns(800)
    row('let go half way, it falls from there; held again, it goes on from where it is', 440 <= mid <= 560 and low < mid and up > low and s.speed() == 100,
        [mid, low, again, up, s.speed()])

    # a pair, another switch's hold, a preset without the block, another preset on the way
    s.applied.clear()
    group = s.byte(76)
    did = s.press(A, B, ms=120)
    row("A+B is the pair as before (the scenes before), with A's hold a ramp: no ramp, no scene", did == [] and s.byte(76) != group
        and not s.applied and s.speed() == 100, [did, group, s.byte(76), s.applied])
    s.applied.clear()
    did = s.press(A, B, ms=1200)
    row('A+B held: no ramp either', not s.applied and s.speed() == 100, [did, s.applied])
    s.byte(52, 1)
    s.applied.clear()
    did = s.press(A, ms=600)
    row('with the tuner on, a press of A closes it, and nothing ramps', s.byte(52) == 0 and not s.applied and did == [], [did, s.byte(52)])
    s.applied.clear()
    did = s.press(B, ms=1300)
    row('a hold without a ramp is the application\'s, as before', ('preset step', 1) in did and not s.applied, did)
    s.chain = [(3, BOOST)]
    s.applied.clear()
    did = s.press(A, ms=1300)
    row('a preset without that block: the hold does nothing at all', did == [] and not s.applied, [did, s.applied])
    s.chain = [(3, BOOST), (5, TREMOLO)]
    s.values[(5, SPEED)] = 100
    s.applied.clear()
    s.put(A, 1)
    s.turns(600)
    p.setting(G_PRESET, 5)
    s.values[(5, SPEED)] = 300                           # the new preset's
    n = len(s.applied)
    s.turns(300)
    s.put(A, 0)
    s.turns(800)
    row('another preset during a ramp ends it: its values stand', len(s.applied) == n and s.speed() == 300, [n, len(s.applied), s.speed()])
    s.values[(5, SPEED)] = 100
    p.setting(G_PRESET, 4)
    s.turns(20)

    # times and targets at the ends
    s.ramp(A, TREMOLO, SPEED, 5000, 0, 0)
    s.applied.clear()
    s.put(A, 1)
    s.turns(220)
    jumped = s.speed()
    s.put(A, 0)
    s.turns(20)
    row('no rise or fall time: at once; a target past the end of the way stops there', jumped == 1000 and s.speed() == 100, [jumped, s.speed()])
    s.ramp(A, TREMOLO, SPEED, 50, 12750, 12750)
    s.applied.clear()
    s.put(A, 1)
    s.turns(200 + 12750 // 2)
    slow = s.speed()
    s.put(A, 0)
    s.turns(12800)
    row('the longest times, 12.75 s, and a target below the value: it goes down and back', 70 <= slow <= 80 and s.speed() == 100, [slow, s.speed()])

    # a hold whose tap and double press do nothing: after a pair's wait
    s.ramp(A, TREMOLO, SPEED, 900, 1000, 500)
    p.say('FSA 0 0 0 0 255')
    s.applied.clear(), s.did.clear()
    s.put(A, 1)
    s.turns(40)
    before = list(s.applied)
    s.turns(20)
    started = list(s.applied)
    s.turns(1100)
    top = s.speed()
    s.put(A, 0)
    s.turns(600)
    row("a hold whose tap and double press do nothing ramps after 45 ms, a pair's wait", before == [] and len(started) >= 1 and top == 900
        and s.speed() == 100 and s.did == [], [before, started, top, s.speed(), s.did])
    s.applied.clear()
    did = s.press(A, B, ms=600)
    row('A+B within that wait is a pair still: no ramp', not s.applied and s.speed() == 100, [did, s.applied])

    # the tap is the ramp on and off
    p.say('FSA 0 0 12 0 255')
    s.applied.clear(), s.did.clear()

    def tap(ms=100, then=1100):
        s.put(A, 1)
        s.turns(ms)
        s.put(A, 0)
        s.turns(then)
        return s.speed()

    up, down, short = tap(), tap(then=700), tap(ms=30)
    row('a tap that is the ramp on and off: up, where it stays; the next goes back; one shorter than the wait counts as well; the application sees none',
        up == 900 and down == 100 and short == 900 and s.did == [], [up, down, short, s.did])
    p.setting(G_PRESET, 5)
    s.values[(5, SPEED)] = 300                           # the new preset's
    s.turns(50)
    stood = s.speed()
    again = tap()
    back = tap(then=700)
    row('another preset ends it, its value stands, and the next tap goes up again from there', stood == 300 and again == 900 and back == 300,
        [stood, again, back])
    s.values[(5, SPEED)] = 100
    p.setting(G_PRESET, 4)
    s.turns(20)
    s.byte(52, 1)
    s.applied.clear()
    did = s.press(A, ms=100)
    row('with the tuner on, a tap of it closes the tuner, and nothing ramps', s.byte(52) == 0 and not s.applied, [did, s.byte(52)])
    s.chain = [(3, BOOST)]
    nothing = tap()
    s.chain = [(3, BOOST), (5, TREMOLO)]
    first = tap()
    row('without its block the tap does nothing, and with it the next goes up', nothing == 100 and first == 900, [nothing, first])
    tap(then=700)
    p.say('FSA 0 0 1 0 255')

    # the factory layout
    p.say('FSMODE layout=factory')
    s.turns(20)
    s.applied.clear()
    s.put(A, 1)
    s.turns(1500)
    s.put(A, 0)
    s.turns(100)
    row('the factory layout (Presets) has no ramps', not s.applied, s.applied)
    p.say('FSMODE layout=custom')
    s.turns(20)

    # kept by GSAVE behind MIDI's settings
    s.ramp(B, BOOST, 0, -30, 500, 1500)
    ramps = bytes.fromhex(p.say('RAMP')[0].split()[1])
    s.kept = None
    p.run('hyperrig_settings_keep')
    rec = s.kept or b''
    length = struct.unpack('<I', rec[4:8])[0] if len(rec) >= 8 else None
    row('GSAVE keeps the ramps behind MIDI\'s settings, in what the application reads of a record (128 bytes)',
        len(rec) == 128 and length == KEPT and rec[HEAD + 32] == ord('M') and rec[HEAD + KEPT_MIDI] == ord('R')
        and rec[HEAD + KEPT_MIDI + 1:HEAD + KEPT_MIDI + 19] == ramps and not any(rec[HEAD + KEPT_MIDI + 19:HEAD + KEPT]),
        [len(rec), length])
    page = 0x01C79100
    p.mem.write(page, rec)
    good = p.run('mode_and_settings_page_check', page)
    row('the application takes the record as a whole one', good == 1, good)
    p.say('RAMP =' + '00' * 18)
    p.run('hyperrig_settings_import', page)
    row('read at the start, the ramps are back', bytes.fromhex(p.say('RAMP')[0].split()[1]) == ramps, None)
    old = bytearray(rec)
    old[4:8] = struct.pack('<I', KEPT_MIDI)
    p.mem.write(page, bytes(old))
    p.say('RAMP =' + '11' * 18)
    p.run('hyperrig_settings_import', page)
    row('a record from before the ramps leaves them as they are', bytes.fromhex(p.say('RAMP')[0].split()[1]) == b'\x11' * 18, None)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build')
    a = parser.parse_args(argv)
    rows = check(a.build)
    for r in rows:
        print('   ok  ' if r['held'] else '   FAIL', r['check'], '' if r['held'] else json.dumps(r['seen'], default=repr)[:600])
    print(json.dumps({'held': all(r['held'] for r in rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(r['held'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
