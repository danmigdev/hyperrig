"""Run what MIDI does in a product build in the pi32v2 simulator: every message in, every message out, the settings and how they are kept. Offline.

The application's own code runs from the bytes of a built firmware: the console word MIDI, the interrupt's handler that takes packets, the
turn of the control scan that does what they say and looks for what the player changed, the chain, the blocks with their switches and
knobs, the scenes, GSAVE and what the start reads, with the sector of the settings simulated in memory. Of the USB controller there is
what that handler asks of it (tools/check_mini_usb.py runs the port itself). Loading a preset, the amp's switch and the tempo are
recorded instead of run. With --before, a build from before MIDI: it must read and keep what this one wrote, and the lights in it are the
same bytes. No device is opened; nothing of this is a hardware test.

Usage, from the repository root:
    python -B tools/check_mini_midi.py BUILD [--before BUILD]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), *[str(ROOT / 'upstream/pi32v2-isa' / d) for d in ('tools/llvm', 'tools/hwtest', '')]]
import check_mini_scenes as scenes  # noqa: E402

STATE, SETTINGS, SCRATCH, PAGE = 'L01c26890', 'L01c1f180', 0x01C74000, 0x01C73000
S_PRESENT, S_CONFIGURED, S_TUNER, S_LAYOUT, S_BYPASS, S_ENGINE, G_SCENE, G_PRESET, G_VOLUME, G_RATE = 1, 3, 52, 74, 77, 280, 88, 92, 36, 44
SECTOR, SECTOR_AT, EP1_COUNT, OFF = 4096, 0xFE000, 0x1180C, 255
RATE = 320_000                                              # what the application counts its clock with: 320000 * 1000 / 6 a second
NAMES = ('clock', 'in', 'out', 'scene', 'bypass', 'tuner', 'tap', 'amp', 'volume', 'blocks')
AS_IT_COMES = bytes([1, 0, 1, 20, 21, 22, 23, 24, 7, 102] + [OFF, 0, 0, 0, 100] * 4)


class Player(scenes.Pedal):
    """A pedal with a chain, its MIDI port on, and what is at the other end of it."""

    def __init__(self, build, midi=True):
        super().__init__(build)
        scenes.harness.RECORDED.pop('calibration_commands_global_save', None)
        self.did, self.sent, self.queue, self.takes, self.left, self.hooks = [], [], [], True, True, {}
        self.sector, self.now, self.missing, self.amp, self.tempo = bytearray(b'\xff' * SECTOR), 50_000, set(), 0, 1200
        self.erased = 0
        step, cpu = self.cpu.step, self.cpu

        def step_with_barriers():
            insn, _, size = cpu.decode(cpu.pc)
            if insn.id != 'ssync':
                return step()
            cpu.pc += size
            cpu.steps += 1
            return None

        cpu.step = step_with_barriers
        for name, f in {'preset_loader_load': self.loads, 'preset_storage_available': lambda a: int(a[0] not in self.missing),
                        'footswitch_events_reload_preset': lambda a: self.note('reload'), 'slot_commands_requested': lambda a: self.amp,
                        'preset_band_controls_request_reserve': self.amps, 'tap_tempo_tap_tempo': lambda a: self.note('tap', *a[:2]),
                        'tempo_slot_services_tempo_command': self.tempos, 'preset_application_services_tempo': lambda a: self.tempo,
                        'panel_inputs_event_queue': lambda a: self.note('event', *a[:3]), 'storage_control_read': self.reads, 'capture_journal_write': self.writes,
                        'capture_journal_erase': self.erases, 'storage_coordination_wait_ready': lambda a: 0,
                        'L02005cb8': lambda a: 0, 'L02001b94': self.register, 'L02005d1c': self.acknowledge, 'L02006af8': self.transmit,
                        'sdk_usb_set_dma_taddr': lambda a: 0, 'phase3_p4_usb_g_ep_config': self.endpoint, 'L0201c442': lambda a: self.hook('interrupt', a[2]),
                        'L0201c202': lambda a: self.hook(f'asked{a[1]}', a[2]), 'L0201c220': lambda a: self.hook('reset', a[2]),
                        'phase3_p4_cdc_ready': lambda a: 0, 'storage_platform_clock': lambda a: struct.unpack('<I', self.mem.read(0x10704, 4))[0]}.items():
            if name in self.where:
                self.at[self.where[name]] = f
        self.mem.write(self.where[SETTINGS] + G_RATE, struct.pack('<I', RATE))
        self.setting(G_PRESET, 0)
        self.setting(G_SCENE, -1)
        self.wipe()
        self.time(50_000)
        if midi:
            self.load_page(self.page())
            self.start_port()

    # the port
    def page(self, settings=AS_IT_COMES, wanted=1):
        page = bytearray(128)
        page[:4], page[4], page[72], page[73], page[74:104] = b'TKGX', 64, ord('M'), wanted, settings
        return bytes(page)

    def load_page(self, page):
        self.mem.write(PAGE, bytes(page))
        self.run('hyperrig_settings_import', PAGE)

    def start_port(self):
        """The device starts with the function in its list, describes it, and the bus is reset."""
        self.run('hyperrig_usb_functions')
        self.where['the function'] = struct.unpack('<I', self.mem.read(self.where[STATE] + 3380, 4))[0]
        self.mem.write(SCRATCH, struct.pack('<I', 2))
        length = self.run('the function', 0, SCRATCH + 16, SCRATCH)
        assert length == 100 and self.mem.read(SCRATCH, 4) == struct.pack('<I', 4)
        self.where['the reset'] = self.hooks['reset']
        self.run('the reset', 0, 0)
        self.where['the interrupt'] = self.hooks['interrupt']
        self.connected(True)

    def connected(self, on):
        self.byte(S_PRESENT, int(on))
        self.byte(S_CONFIGURED, int(on))

    def hook(self, name, at):
        self.hooks[name] = at
        return 0

    def endpoint(self, a):
        self.hooks['sending' if a[1] & 0x80 else 'received'] = a[3]
        return 0

    def register(self, a):
        if a[0] == 20:
            return int(bool(self.queue))
        if a[0] == 22:
            packet = self.queue[0]
            self.mem.write(self.hooks['received'], packet + b'\xee' * (4 if len(packet) == 64 else 0))
            return len(packet)
        assert a[0] == 17, a[0]
        return int(not self.left)

    def acknowledge(self, a):
        assert a[1] == 1 and a[2] == 0x11, a[:3]
        self.queue.pop(0)
        return 0

    def transmit(self, a):
        assert a[1] == 1 and a[2] == 1 and self.left, 'a packet is put on one that has not left'
        n = struct.unpack('<I', self.mem.read(EP1_COUNT, 4))[0]
        data = self.mem.read(self.hooks['sending'], n)
        assert n and not n % 4 and n <= 64
        self.sent += [bytes(data[k + 1:k + 4]).hex() if data[k] == data[k + 1] >> 4 else ('code', data[k:k + 4].hex()) for k in range(0, n, 4)]
        self.left = self.takes
        return 0

    def reads_again(self):
        self.takes = self.left = True

    def packet(self, *events, ms=None):
        """A packet of the computer, at a time of its own: the interrupt takes it when there is room."""
        self.queue.append(b''.join(events))
        if ms is not None:
            self.mem.write(0x10704, struct.pack('<I', self.clock(ms)))
        self.pump()
        self.mem.write(0x10704, struct.pack('<I', self.clock(self.now)))

    def pump(self):
        while self.queue:
            n = len(self.queue)
            self.run('the interrupt')
            if len(self.queue) == n:
                return

    def stream(self, data):
        """Bytes as the events of a computer that does not look at them: code 15, one byte each."""
        data = bytes(data)
        for k in range(0, len(data), 16):
            self.packet(*[bytes([15, b, 0, 0]) for b in data[k:k + 16]])

    def midi(self, *message):
        self.packet(bytes([message[0] >> 4, *message]).ljust(4, b'\0'))

    # the pedal
    def note(self, *what):
        self.did.append(what)
        return 0

    def loads(self, a):
        self.note('preset', a[0])
        self.setting(G_PRESET, a[0])
        return 0

    def amps(self, a):
        self.note('amp', a[0])
        self.amp = a[0]
        return 0

    def tempos(self, a):
        self.note('tempo', a[0])
        self.tempo = a[0]
        return 0

    def reads(self, a):
        if a[0] >= SECTOR_AT:
            self.mem.write(a[1], bytes(self.sector[a[0] - SECTOR_AT:a[0] - SECTOR_AT + a[2]]))
            return 0
        return self.read(a)

    def writes(self, a):
        for k, b in enumerate(self.mem.read(a[1], a[2])):
            self.sector[a[0] - SECTOR_AT + k] &= b
        return 0

    def erases(self, a):
        self.sector[:] = b'\xff' * SECTOR
        self.erased += 1
        return 0

    def time(self, ms):
        self.now = ms
        self.mem.write(self.where[SETTINGS] + 24, struct.pack('<I', ms // 10))
        self.mem.write(0x10704, struct.pack('<I', self.clock(ms)))

    def clock(self, ms):
        return int(ms * RATE / 6) & 0xFFFFFFFF

    def turn(self, ms=10):
        self.time(self.now + ms)
        self.run('hyperrig_midi_turn', self.now, limit=2_000_000)
        self.pump()

    def turns(self, ms, step=50):
        for _ in range(ms // step):
            self.turn(step)

    def does(self, *messages, turns=3, settle=True):
        """What the messages, all before one turn, make it do in the turns after."""
        self.did.clear()
        self.sent.clear()
        for m in messages:
            self.midi(*m)
        for _ in range(turns):
            self.turn()
        out = list(self.did)
        if settle:
            self.turns(800)
        return out

    def byte(self, offset, value=None):
        at = self.where[STATE] + offset
        if value is not None:
            self.mem.write(at, bytes([value]))
        return self.mem.read(at, 1)[0]

    def on(self, slot):
        return self.run('preset_application_effect_enabled', slot)

    def parameter(self, slot, k):
        v = self.run('preset_application_parameter', slot, k)
        return v - (1 << 32) if v & 0x80000000 else v

    def volume(self):
        self.run('hyperrig_volume')
        return struct.unpack('<I', self.mem.read(self.where[SETTINGS] + G_VOLUME, 4))[0]

    # the settings
    def told(self, line='MIDI'):
        """The console: (the port, kept on, the settings, messages in, messages out), or the answer when it is not one line of that form."""
        answer = self.say(line)
        m = len(answer) == 1 and re.fullmatch(r'MIDI ([0-3]) ([01]) ([0-9a-f]{60}) (\d+) (\d+)', answer[0])
        return (int(m[1]), int(m[2]), bytes.fromhex(m[3]), int(m[4]), int(m[5])) if m else answer

    def change(self, **values):
        """Some of the settings: by name, and knob1 to knob4 as (controller, place, knob, from, to)."""
        s = bytearray(self.told()[2])
        for name, v in values.items():
            if name.startswith('knob'):
                at = 10 + 5 * (int(name[4:]) - 1)
                s[at:at + 5] = bytes(v)
            else:
                s[NAMES.index({'in_': 'in'}.get(name, name))] = v
        return self.told('MIDI =' + s.hex())[2] == bytes(s)


def without_events(did):
    return [d for d in did if d[0] != 'event']


def check(build, before=None):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})
        print('   ok  ' if good else '   FAIL', name, '' if good else json.dumps(seen, default=repr)[:900], flush=True)

    p = Player(build)
    row('MIDI says what it is', p.told() == (2, 1, AS_IT_COMES, 0, 0), p.told())
    slots = [p.add(2), p.add(8), p.add(4), p.add(5)]                # boost, compressor, equalizer, delay
    row('four blocks', slots == [0, 1, 2, 3], slots)
    p.turns(200)
    p.sent.clear()

    # presets
    seen = [p.does((0xC0, n)) for n in (0, 5, 31, 32, 127)]
    row('program change: presets 1 to 32, and no other', seen == [[('preset', 0)], [('preset', 5)], [('preset', 31)], [], []], seen)
    p.missing = {7}
    seen = [p.does((0xC0, 7)), p.does((0xC0, 8))]
    row('one that is not stored is left alone', seen == [[], [('preset', 8)]], seen)
    seen = p.does((0xC0, 1), (0xC0, 2), (0xC0, 3), turns=6)
    row('of several in a row the last', seen == [('preset', 3)], seen)

    # scenes
    for k in (0, 1, 2, 5):
        p.say(f'SNAPSAVE {k}')
    went = []
    for value in (2, 0, 5, 3, 7, 8, 8, 9, 10, 127, 1):
        p.does((0xB0, 20, value), turns=2)
        went.append(p.setting(G_SCENE))
    row('controller 20: scenes 0 to 7 that are there, 8 the next, 9 the one before', went == [2, 0, 5, 5, 5, 0, 1, 0, 0, 0, 1], went)
    p.setting(G_SCENE, 0)
    p.does((0xB0, 20, 8), (0xB0, 20, 8))
    row('two steps', p.setting(G_SCENE) == 2, p.setting(G_SCENE))

    # blocks
    state = lambda: [p.on(s) for s in slots]
    p.does(*[(0xB0, 102 + k, 127) for k in range(4)])
    was, seen = state(), []
    for m in ((0xB0, 103, 0), (0xB0, 102, 63), (0xB0, 105, 0), (0xB0, 102, 64), (0xB0, 103, 127), (0xB0, 105, 100), (0xB0, 117, 0), (0xB0, 110, 127)):
        p.does(m)
        seen.append(state())
    row('controllers 102 to 117: the blocks by their place in the chain, off below 64', was == [1, 1, 1, 1] and seen == [[1, 0, 1, 1], [0, 0, 1, 1], [0, 0, 1, 0], [1, 0, 1, 0], [1, 1, 1, 0],
        [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]], [was, seen])
    p.does(*[(0xB0, 102 + k, 0) for k in range(4)], turns=2)
    row('four at once', state() == [0, 0, 0, 0], state())
    p.does((0xB0, 102, 0), (0xB0, 102, 127))
    row('off and on again is on', state() == [1, 0, 0, 0], state())
    did = p.does((0xB0, 103, 127))
    row('the editor is told', did == [('event', 101, 1, 0)], did)
    did = p.does((0xB0, 103, 127))
    row('one that is on is not switched on', did == [], did)
    did = p.does((0xC0, 4), (0xB0, 104, 127), turns=1)
    row('a block behind a preset is of that preset', did == [('preset', 4), ('event', 101, 2, 0)] and state()[2] == 1, did)
    did = p.does((0xC0, 1), (0xB0, 20, 2), (0xC0, 4), turns=1, settle=False)
    first = [d for d in did if d[0] == 'preset'], p.setting(G_SCENE)
    p.did.clear()
    p.turn()
    row('a turn does a preset and its scene, and leaves what comes behind for the next', first == ([('preset', 1)], 2) and p.did == [('preset', 4)], [first, p.did])
    p.turns(800)

    # the amp, bypass, the tuner, taps
    seen = [p.does((0xB0, 24, v)) for v in (127, 127, 0)]
    row('controller 24: the amp', seen == [[('amp', 1)], [], [('amp', 0)]], seen)
    p.does(*[(0xB0, 102 + k, 127) for k in range(4)], (0xB0, 24, 127))
    did = p.does((0xB0, 21, 127))
    off = state(), p.amp, p.byte(S_BYPASS)
    again = p.does((0xB0, 21, 127))
    back = p.does((0xB0, 21, 0))
    row('controller 21: bypass switches everything off, and back is the preset as it is stored', off == ([0, 0, 0, 0], 0, 1) and without_events(again) == [] and back == [('reload',)] and p.byte(S_BYPASS) == 0,
        [did, off, again, back])
    p.byte(S_LAYOUT, 2)
    p.does((0xB0, 21, 127))
    p.run('slot_commands_enable_command', 1, 1)
    p.turns(600)
    row('outside the factory layout too, a block that is on again is no bypass', p.byte(S_BYPASS) == 0, p.byte(S_BYPASS))
    p.byte(S_LAYOUT, 0)
    seen = []
    for v in (127, 127, 0, 64, 63):
        p.does((0xB0, 22, v))
        seen.append(p.byte(S_TUNER))
    row('controller 22: the tuner', seen == [1, 1, 0, 1, 0], seen)
    p.did.clear()
    base = p.now
    for k in range(3):
        p.packet(bytes([0x0B, 0xB0, 23, 127]), ms=base + 100 + 500 * k)
        p.packet(bytes([0x0B, 0xB0, 23, 0]), ms=base + 150 + 500 * k)
    p.turn()
    row('controller 23: a tap, with the time it came', p.did == [('tap', p.clock(base + 100 + 500 * k), p.now) for k in range(3)], p.did)

    # the volume
    p.mem.write(p.where[SETTINGS] + 14, b'\0')                      # KNOB off: the wheel gives full volume
    seen = [p.volume()]
    for v in (127, 126, 64, 1, 0, 127):
        p.does((0xB0, 7, v), turns=1, settle=False)
        seen.append(p.volume())
    row('controller 7: the volume, a square, full at 127', seen == [0x10000, 0x10000, 126 * 126 * 0x10000 // 16129, 64 * 64 * 0x10000 // 16129, 0x10000 // 16129, 0, 0x10000], seen)

    # a knob of a block
    row('knobs are given controllers', p.change(knob1=(11, 0, 0, 0, 100), knob2=(12, 2, 2, 100, 0), knob3=(13, 8, 0, 0, 100), knob4=(14, 2, 0, 0, 100)), p.told())
    seen = []
    for v in (0, 127, 64, 32):
        p.does((0xB0, 11, v), (0xB0, 12, v))
        seen.append((p.parameter(0, 0), p.parameter(2, 2)))
    row('the gain of the boost over its whole way, the frequency of the equalizer the other way round', seen == [(-12, 5000), (24, 200), (6, 2581), (-3, 3791)], seen)
    seen = []
    for v in (0, 127, 64):
        p.does((0xB0, 14, v))
        seen.append(p.parameter(2, 0))
    row('a knob around zero', seen == [-15, 15, 0], seen)
    row('a place with no block does nothing', p.does((0xB0, 13, 50)) == [], p.did)
    p.change(knob1=(11, 0, 0, 25, 75))
    seen = []
    for v in (0, 127):
        p.does((0xB0, 11, v))
        seen.append(p.parameter(0, 0))
    row('over a part of its way', seen == [-3, 15], seen)
    row('a value it has is not set again', p.does((0xB0, 11, 127)) == [], p.did)
    did = p.does(*[(0xB0, 11, v) for v in range(0, 127, 3)], (0xB0, 11, 127), turns=8)
    row('a movement is followed to its end, eight steps in a turn', p.parameter(0, 0) == 15 and len(did) <= 64, [p.parameter(0, 0), len(did)])
    p.change(knob1=(OFF, 0, 0, 0, 100), knob2=(OFF, 0, 0, 0, 100), knob3=(200, 200, 9, 255, 255), knob4=(15, 1, 9, 0, 100))
    row('a knob that is none does nothing', p.does((0xB0, 15, 3)) == [], p.did)
    p.told('MIDI =' + AS_IT_COMES.hex())

    # the stream
    def stream(data, name, want):
        p.did.clear()
        p.stream(data)
        for _ in range(6):
            p.turn()
        got = without_events(p.did)
        row(name, got == want, got)
        p.turns(800)

    stream([0xC0, 1], 'a stream of single bytes', [('preset', 1)])
    stream([0xC0, 0xF8, 2], 'real time inside a message', [('preset', 2)])
    stream([0xC0, 0xFE, 0xF8, 3, 0xFA, 0xFC, 0xFF], 'and around it', [('preset', 3)])
    stream([0xB0, 22, 127, 22, 0, 0xF8, 22, 127, 22, 0xFE, 0], 'a status that stays in force', [])
    row('which turned the tuner on and off and on and off', p.byte(S_TUNER) == 0, p.byte(S_TUNER))
    stream([0xF0, 0x7D, 0x48, 0x52, *range(0, 128), 0xF7, 0xC0, 4], 'SysEx is passed over', [('preset', 4)])
    stream([0xF0, 1, 2, 3, 0xF8, 0xC0, 5], 'one that never ends is ended by the next status', [('preset', 5)])
    stream([0xF0, 1, 2, 3, 4, 5, 6, 7], 'one that stops', [])
    stream([8, 9, 10, 0xF7, 11, 12], 'data of nothing', [])
    stream([0xC0, 6, 0xF3, 7, 8, 0xF1, 9, 0xF2, 1, 2, 10], 'what is for all ends the status, and its data is passed over', [('preset', 6)])
    p.missing.clear()
    stream([0x90, 60, 100, 0x80, 60, 0, 0xA0, 60, 1, 0xD0, 5, 0xE0, 0, 64, 0xC0, 7], 'notes, pressure and bend are passed over', [('preset', 7)])
    stream([0xC0], 'half a message', [])
    stream([9], 'and its other half later', [('preset', 9)])
    codes = [b'\x04\xf0\x7d\x01', b'\x04\x02\x03\x04', b'\x05\xf7\x00\x00', b'\x06\xf0\xf7\x00', b'\x07\xf0\x01\xf7', b'\x02\xf1\x01\x00', b'\x03\xf2\x01\x02', b'\x05\xf6\x00\x00', b'\x00\xc0\x0a\x00',
             b'\x01\xc0\x0a\x00', b'\x1c\xc0\x0a\x00', b'\xfc\xc0\x0a\x00', b'\x0f\xf8\x00\x00', b'\x0c\xc0\x0c\x00', b'\x0d\xd0\x0a\x00']
    p.did.clear()
    p.packet(*codes)
    for _ in range(3):
        p.turn()
    row('the events of every code', p.did == [('preset', 12)], p.did)
    p.turns(800)

    # channels
    seen = {}
    for name, v in (('all', 0), ('7', 7), ('1', 1), ('off', OFF), ('a wrong one', 40)):
        p.change(in_=v)
        seen[name] = [bool(p.does((0xC0 | c, 1))) for c in (0, 6, 15)]
    p.change(in_=0)
    row('channels: all, one, none', seen == {'all': [True] * 3, '7': [False, True, False], '1': [True, False, False], 'off': [False] * 3, 'a wrong one': [False] * 3}, seen)

    # the engine off
    p.mem.write(p.where[STATE] + S_ENGINE, bytes(4))
    did = p.does((0xC0, 3), (0xB0, 103, 127))
    p.mem.write(p.where[STATE] + S_ENGINE, b'\1\0\0\0')
    p.did.clear()
    p.turn()
    row('while the engine is off it waits', did == [] and p.did[:1] == [('preset', 3)], [did, p.did])
    p.turns(800)

    # floods and garbage
    rng = random.Random(11)
    worst, wrong = 0, []
    for _ in range(60):
        p.queue.clear()
        for _ in range(12):
            p.packet(bytes(rng.randrange(256) for _ in range(64)))
        p.did.clear()
        start = p.cpu.steps
        p.time(p.now + 10)
        p.run('hyperrig_midi_turn', p.now, limit=2_000_000)
        worst = max(worst, p.cpu.steps - start)
        calls = without_events(p.did)
        if len([d for d in calls if d[0] in ('preset', 'reload')]) > 2 or any(d[0] == 'preset' and d[1] > 31 for d in calls) or len(p.did) > 12:
            wrong.append(p.did[:])
    row('60 turns of garbage: a preset and one thing more in a turn at most, none that is not', not wrong and worst < 250_000, [worst, wrong[:2]])
    row('and the settings are as they were', p.told()[2] == AS_IT_COMES, p.told())
    p.queue.clear()
    p.turns(600)
    seen = []
    for _ in range(5):
        for _ in range(8):
            p.packet(b''.join(bytes([0x0C, 0xC0, rng.randrange(32), 0]) for _ in range(16)))
        p.did.clear()
        p.turn()
        seen.append(len(p.did))
    row('a flood of 640 program changes loads five presets, one a turn', seen == [1] * 5, seen)
    p.packet(*[bytes([0x0B, 0xB0, 20, k % 8]) for k in range(16)])
    seen = []
    for _ in range(18):
        p.turn()
        seen.append(p.setting(G_SCENE))
    row('sixteen scenes in a packet: one a turn', seen[0] == 0 and seen[1] == 1 and seen[13] == 5 and seen[-1] == 5, seen)
    p.queue.clear()
    p.byte(S_TUNER, 0)
    p.byte(S_BYPASS, 0)
    p.turns(1000)

    # out
    q = Player(build)
    q.add(2), q.add(8), q.add(4)
    for k in (0, 1, 2):
        q.say(f'SNAPSAVE {k}')
    q.setting(G_SCENE, -1)
    for s in (0, 1, 2):
        q.run('slot_commands_enable_command', s, 1)
    q.turns(600)
    start = list(q.sent)

    def told(act, turns=4):
        q.sent.clear()
        act()
        for _ in range(turns):
            q.turn()
        out = list(q.sent)
        q.turns(600)
        return out

    row('nothing is sent at the start', start == [], start)
    row('a preset: program change', told(lambda: q.setting(G_PRESET, 12)) == ['c00c00'], q.sent)
    seen = told(lambda: q.say('SNAP 1'))
    row('a scene', seen == ['b01401'], seen)
    seen = [told(lambda: q.run('slot_commands_enable_command', 1, 0)), told(lambda: q.run('slot_commands_enable_command', 1, 1)), told(lambda: q.run('slot_commands_enable_command', 2, 0))]
    row('a block, by its place', seen == [['b06700'], ['b0677f'], ['b06800']], seen)
    seen = [told(lambda: q.byte(S_TUNER, 1)), told(lambda: q.byte(S_TUNER, 0))]
    row('the tuner', seen == [['b0167f'], ['b01600']], seen)
    q.amp = 1
    q.turn()
    q.turns(600)
    seen = [told(lambda: setattr(q, 'amp', 0)), told(lambda: setattr(q, 'amp', 1))]
    row('the amp', seen == [['b01800'], ['b0187f']], seen)

    def everything_off():
        for s in (0, 1, 2):
            q.run('slot_commands_enable_command', s, 0)
        q.amp = 0
        q.byte(S_BYPASS, 1)

    seen = told(everything_off)
    row('bypass: one message, not the blocks one by one', seen == ['b0157f'], seen)

    def new_preset():
        q.setting(G_PRESET, 20)
        q.setting(G_SCENE, 2)
        q.byte(S_BYPASS, 0)
        for s in (0, 1, 2):
            q.run('slot_commands_enable_command', s, 1)

    seen = told(new_preset)
    row('another preset with a scene: the preset first, and not its blocks', seen == ['c01400', 'b01402', 'b01500'], seen)
    seen = told(lambda: q.setting(G_PRESET, -1))
    row('no preset: nothing', seen == [], seen)
    q.setting(G_PRESET, 3)
    q.turns(700)
    seen = told(lambda: (q.add(8), q.run('slot_commands_enable_command', 3, 1)))
    row('a block that is added is not a switch', seen == [], seen)
    q.change(out=10, scene=OFF, blocks=30)
    seen = [told(lambda: q.setting(G_PRESET, 4)), told(lambda: q.say('SNAP 0')), told(lambda: q.run('slot_commands_enable_command', 0, 0))]
    row('on its channel, with its map; what is off in the map is not sent', seen == [['c90400'], [], ['b91e00']], seen)
    q.change(out=40, blocks=126)
    seen = told(lambda: (q.setting(G_PRESET, 8), q.run('slot_commands_enable_command', 0, 1)))
    row('numbers that are none make no message that is none', all(len(x) == 6 and x[0] in 'bc' and int(x[2:4], 16) < 128 for x in seen), seen)
    q.change(out=OFF)
    seen = told(lambda: q.setting(G_PRESET, 5))
    q.told('MIDI =' + AS_IT_COMES.hex())
    row('off', seen == [] and told(lambda: None) == [], seen)
    q.connected(False)
    seen = told(lambda: q.setting(G_PRESET, 6))
    q.connected(True)
    row('nothing while the port is not there, and nothing of it afterwards', seen == [] and told(lambda: None) == [], seen)

    # no loops
    for _ in range(2):
        q.turns(600)
    seen = {}
    for name, m in (('preset', (0xC0, 9)), ('scene', (0xB0, 20, 1)), ('block', (0xB0, 103, 0)), ('block on', (0xB0, 103, 127)), ('bypass', (0xB0, 21, 127)), ('bypass off', (0xB0, 21, 0)),
                    ('tuner', (0xB0, 22, 127)), ('tuner off', (0xB0, 22, 0)), ('amp', (0xB0, 24, 127)), ('next scene', (0xB0, 20, 8))):
        did = q.does(m, turns=8)
        seen[name] = list(q.sent)
    row('what came in is not sent back', not any(seen.values()), seen)
    q.sent.clear()
    q.setting(G_PRESET, 11)
    for _ in range(3):
        q.turn()
    sent = list(q.sent)
    did = q.does((0xC0, 11), settle=False)
    q.turns(600)
    later = q.does((0xC0, 11), settle=False)
    row('what was sent and comes straight back is not done; half a second later it is', sent[:1] == ['c00b00'] and did == [] and later == [('preset', 11)], [sent, did, later])
    q.turns(900)
    # the player and a controller at once
    q.change(knob1=(11, 0, 0, 0, 100))
    q.byte(S_BYPASS, 0)
    for s in (0, 1, 2):
        q.run('slot_commands_enable_command', s, 1)
    q.turns(900)
    q.sent.clear()
    for k in range(60):
        q.midi(0xB0, 11, 2 * k)
        if k == 30:
            q.run('slot_commands_enable_command', 1, 0)
        q.turn()
    row('a block the player switches while a controller moves a knob is told', q.sent == ['b06700'] and q.parameter(0, 0) == 21, [q.sent, q.parameter(0, 0)])
    q.told('MIDI =' + AS_IT_COMES.hex())
    # two pedals that tell each other
    a, b = Player(build), Player(build)
    for x in (a, b):
        x.add(2), x.add(8)
        for s in (0, 1):
            x.run('slot_commands_enable_command', s, 1)
        x.turns(600)
        x.sent.clear()
    passed = 0
    a.setting(G_PRESET, 7)
    for k in range(120):
        for x, y in ((a, b), (b, a)):
            x.turn()
            for m in x.sent:
                passed += 1
                y.midi(*bytes.fromhex(m)[:2 if m[0] == 'c' else 3])
            x.sent.clear()
        if k == 60:
            b.run('slot_commands_enable_command', 1, 0)
    row('two pedals that tell each other follow, and stop', passed == 2 and b.setting(G_PRESET) == 7 and a.on(1) == 0 and b.on(1) == 0, [passed, b.setting(G_PRESET), a.on(1)])
    # nobody reads
    q.takes = False
    for k in range(40):
        q.setting(G_PRESET, k % 32)
        q.turn()
    q.setting(G_PRESET, 17)
    q.setting(G_SCENE, 1)
    q.turns(3000)
    n = len(q.sent)
    q.sent.clear()
    q.reads_again()
    q.turn()
    q.turn()
    row('when nobody read, the state of now is what is sent', n > 0 and q.sent == ['c01100', 'b01401'], [n, q.sent])

    # MIDI clock
    def ticks(times):
        c.did.clear()
        for k, t in enumerate(times):
            if t > c.now:
                c.time(int(t))
            c.packet(b'\x0f\xf8\0\0', ms=t)
            if k % 2 == 0:
                c.run('hyperrig_midi_turn', c.now, limit=2_000_000)
        c.run('hyperrig_midi_turn', c.now, limit=2_000_000)
        return [d[1] for d in c.did if d[0] == 'tempo']

    def clock(bpm, beats, jitter=0.0, seed=1, gap=0):
        rng2, at = random.Random(seed), c.now
        out = ticks([at + k * 60_000 / bpm / 24 + rng2.uniform(0, jitter) for k in range(24 * beats + 1)])
        c.time(int(at + beats * 60_000 / bpm) + gap)
        return out

    c = Player(build)
    seen = {}
    for bpm in (40, 60, 90, 120, 174, 240, 300):
        c.tempo = 1000
        seen[bpm] = clock(bpm, 6, gap=1500)
    row('MIDI clock: the tempo after a beat, and it stays', all(v == [10 * k] for k, v in seen.items()), seen)
    c.tempo = 1200
    row('the tempo it has is not set again', clock(120, 8, gap=1500) == [], c.did)
    seen = {}
    for seed in range(6):
        c.tempo = 1000
        seen[seed] = clock(120, 12, jitter=2.5, seed=seed, gap=1500)
    row('packets up to 2.5 ms late: within half a beat a minute, and set three times at most', all(1 <= len(v) <= 3 and abs(v[-1] - 1200) <= 5 for v in seen.values()), seen)
    c.tempo = 1000
    first = clock(100, 4)
    second = clock(140, 5, gap=3000)
    row('another tempo, in the middle of a beat: followed at once, without one between', first == [] and second == [1400], [first, second])
    c.tempo, at = 1000, c.now
    seen = ticks([at + k * 500 / 24 + (25 if k in (96, 168) else 0) for k in range(24 * 12 + 1)])           # two beats come 25 ms late
    row('a beat that comes late does not move the tempo', seen == [1200], seen)
    c.time(c.now + 3000)
    c.tempo, at = 1000, c.now
    seen = ticks([at + k * 500 / 24 for k in range(24 * 4)] + [at + 400 + k * 500 / 24 for k in range(24 * 4, 24 * 9)])      # it stops for 400 ms
    row('nor a clock that stops for a moment', seen == [1200], seen)
    c.time(c.now + 3000)
    c.tempo = 1000
    seen = [clock(20, 3, gap=1500), clock(400, 8, gap=1500)]
    row('slower than 40 and faster than 300 is left alone', seen == [[], []], seen)
    c.change(clock=0)
    row('the clock off', clock(90, 5, gap=1500) == [], c.did)

    # the console
    s = Player(build)
    good = bytes([0, 16, 3, 0, 119, OFF, 1, OFF, 11, 104] + [4, 15, 6, 100, 0] * 4)
    row('the settings as digits', s.told('MIDI =' + good.hex()) == (2, 1, good, 0, 0), s.told())
    seen = [s.told(line)[2] == good for line in ('MIDI =' + AS_IT_COMES.hex()[:-2], 'MIDI =' + AS_IT_COMES.hex() + '00', 'MIDI =' + AS_IT_COMES.hex()[:-1], 'MIDI =', 'MIDI =x' + AS_IT_COMES.hex()[1:],
                                                     'MIDI = ' + AS_IT_COMES.hex(), 'MIDI =' + AS_IT_COMES.hex().upper(), 'MIDI x', 'MIDI')]
    row('anything else changes nothing', seen == [True] * 9, seen)
    s.told('MIDI =' + AS_IT_COMES.hex())
    s.did.clear()
    played = s.told('MIDI >cf05b0167f')
    row('MIDI >: as if these bytes had come', played[0] == 2 and played[3] == 2 and s.did == [('preset', 5)] and s.byte(S_TUNER) == 1, [played, s.did])
    s.turns(200)
    row('and it is not told', s.sent == [], s.sent)
    s.midi(0xC0, 3)
    s.setting(G_PRESET, 9)
    s.turn()
    row('the messages are counted', s.told()[3:] == (3, 1), s.told())
    plain = Player(build, midi=False)
    row('without the port the word answers, and the turn does nothing', plain.told() == (0, 0, AS_IT_COMES, 0, 0) and plain.run('hyperrig_midi_turn', 60_000) is not None, plain.told())
    plain.told('MIDI >c004')
    row('and bytes can be played without it', plain.did == [('preset', 4)], plain.did)

    # kept
    used = lambda x: [bytes(x.sector[n * 128:n * 128 + 128]) for n in range(30) if bytes(x.sector[n * 128:n * 128 + 128]) != b'\xff' * 128]
    lights = lambda x: [y for y in used(x) if y[:4] == b'TKGX']

    def saver(where, **more):
        x = Player(where, **more)
        x.mem.write(x.where['L01c27204'], bytes(32))
        x.run('mode_and_settings_block_import', 0, 0)
        return x

    k = saver(build, midi=False)
    answer = k.say('GSAVE')
    first = lights(k)
    n, crc = struct.unpack_from('<II', first[0], 4) if first else (0, 0)
    # 64 bytes with MIDI's item; 88 in a build that keeps the ramps behind it (mini/product/ramp.c): 'R' and 18 bytes, none set here
    row('GSAVE: the record of the lights, whole, with the settings behind them', answer and answer[0].startswith('GSAVE ok') and len(first) == 1 and n in (64, 88) and
        zlib.crc32(first[0][40:40 + n]) == crc and first[0][72:104] == b'M\0' + AS_IT_COMES and (n == 64 or first[0][104:128] == b'R' + bytes(23)),
        [answer, [x[:12].hex() for x in used(k)]])
    k.say('GSAVE')
    row('saved again: no second record', len(lights(k)) == 1, len(used(k)))
    k.told('MIDI =' + good.hex())
    k.say('GSAVE')
    last = lights(k)[-1]
    row('other settings: a second one', len(lights(k)) == 2 and last[72:104] == b'M\0' + good, last[72:104].hex())
    r = Player(build, midi=False)
    r.load_page(last)
    row('read again at the start: the same', r.told() == (0, 0, good, 0, 0), r.told())
    whole = Player(build, midi=False)
    whole.sector[:] = k.sector
    whole.run('mode_and_settings_record_scan')
    page = struct.unpack('<i', whole.mem.read(whole.where[SETTINGS] + 212, 4))[0]
    row('the scan of the start finds that record', page >= 0 and bytes(whole.sector[128 * page:128 * page + 128]) == last, page)
    for turn in range(40):
        k.change(scene=turn)
        k.say('GSAVE')
    last = lights(k)[-1]
    row('forty saves, the sector erased and written anew: the last is there', k.erased >= 1 and last[77] == 39, [k.erased, last[77]])
    w = saver(build)
    w.say('GSAVE')
    row('the port that is on is kept', lights(w)[-1][72:74] == b'M\1', lights(w)[-1][72:74].hex())
    if before:
        o = saver(before, midi=False)
        o.say('GSAVE')
        row('the lights are the same bytes as in the build before', lights(o)[-1][40:72] == first[0][40:72] and struct.unpack_from('<I', lights(o)[-1], 4)[0] == 32, lights(o)[-1][:12].hex())
        o = Player(before, midi=False)
        o.sector[:] = k.sector
        o.run('mode_and_settings_record_scan')
        page = struct.unpack('<i', o.mem.read(o.where[SETTINGS] + 212, 4))[0]
        found = bytes(o.sector[128 * page:128 * page + 128]) == last
        o.mem.write(PAGE, last)
        right = o.run('mode_and_settings_page_check', PAGE)
        o.run('mode_and_settings_block_import', PAGE + 40, struct.unpack_from('<I', last, 4)[0])
        o.mem.write(SCRATCH, bytes(64))
        o.run('mode_and_settings_block_export', SCRATCH)
        row('the build before finds this record, takes it for right and reads its lights', found and right == 1 and o.mem.read(SCRATCH, 32) == last[40:72], [page, right])
    seen = {}
    for name, change in (('the lights alone', (4, 32)), ('another letter', (72, 0x58)), ('shorter', (4, 63))):
        x = bytearray(last)
        x[change[0]] = change[1]
        r = Player(build, midi=False)
        r.load_page(x)
        seen[name] = r.told()[1:3] == (0, AS_IT_COMES)
    row('a record without the item leaves everything as it comes', all(seen.values()), seen)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build')
    parser.add_argument('--before')
    a = parser.parse_args(argv)
    rows = check(a.build, a.before)
    print(json.dumps({'held': all(r['held'] for r in rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(r['held'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
