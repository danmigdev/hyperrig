"""Run the eight scenes of a product build in the pi32v2 simulator, and the pairs of switches that reach them. Offline; no device is opened.

The application's own code runs from the bytes of a built firmware: the console words of the scenes, the records and names of eight of them, the
form that is stored and the one that is read back, with the storage itself simulated (one record, in memory). With --before, a build from before
eight scenes: a preset that uses four at most must be stored with the same bytes by both. With --copy, a whole copy of a pedal's flash: every preset
in it is read by both builds and must give the same working preset, scenes and names. Nothing of this is a hardware test.

Usage, from the repository root:
    python -B tools/check_mini_scenes.py BUILD [--before BUILD] [--copy FLASH]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product."""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), *[str(ROOT / 'upstream/pi32v2-isa' / d) for d in ('tools/llvm', 'tools/hwtest', '')]]
import check_mini_effect_block as block  # noqa: E402
import check_mini_panel as harness  # noqa: E402

STATE, WORKING, TAG, HEADER = 'L01c26890', 'L01c24790', 0x51474B54, 0x01C76000
FLASH_AT, SCRATCH, LIMIT = 0xBF000, 0x01C78000, 1880
sim, codec = harness.sim, harness.codec


class Pedal(block.Check):
    """One build; the storage of presets is one record in memory, the sector writer takes what it is given."""

    def __init__(self, build):
        harness.RECORDED.pop('the_allocator', None)          # of another build's, put back by the next line
        super().__init__((ROOT / build).resolve())
        self.stored, self.written, self.refused = None, None, None
        p = self.panel
        self.kept = dict(harness.RECORDED)
        for n in ('text_commands_text_command', 'console_commands_console_command', 'console_dispatch_console_dispatch', 'preset_application_effect_type',
                  'preset_application_effect_enabled', 'slot_commands_enable_command'):
            harness.RECORDED.pop(n, None)
        self.python = {n: f for n, f in {
            'preset_storage_preparation_prepare': lambda a: 0, 'tempo_slot_services_priority_nest': lambda a: 0,
            'preset_storage_address': lambda a: FLASH_AT, 'storage_control_read': self.read, 'preset_storage_preparation_replace_pair': self.pair,
            'preset_storage_preparation_record_copy': lambda a: 0, 'preset_loader_elapsed': lambda a: 0, 'storage_platform_clock': lambda a: 0,
            'storage_coordination_notify': lambda a: 0, 'preset_storage_preparation_invalidate': lambda a: 0, 'L0203c15c': lambda a: SCRATCH,
            'L0203d218': lambda a: 0, 'audio_pause_pause_audio': lambda a: 0, 'audio_pause_resume_audio': lambda a: 0}.items() if n in self.where}
        self.at = {self.where[n]: f for n, f in self.python.items()}
        p.run = self.run_with
        self.mem.write(self.where['L01c32db0'] + 48, struct.pack('<I', 400_000))
        self.allocator(True)

    def run(self, name, *args, limit=3_000_000):
        return self.run_with(name, list(args), limit)

    def run_with(self, name, args, limit=3_000_000, stop=None):
        panel, cpu = self.panel, self.cpu
        stop = sim.RETURN if stop is None else stop
        recorded = {panel.where[n]: n for n in harness.RECORDED if n in panel.where}
        cpu.R[:len(args)] = [a & sim.M for a in args]
        cpu.rets, cpu.pc, start, cpu.sp = sim.RETURN, panel.where[name], cpu.steps, sim.STACK_TOP
        while cpu.pc != stop:
            own = self.at.get(cpu.pc)
            if own:
                cpu.R[0] = own(list(cpu.R[:4])) & sim.M
                cpu.pc = cpu.rets
                continue
            service = recorded.get(cpu.pc)
            if service:
                answer = harness.RECORDED[service]
                if service == 'preset_storage_available':
                    answer = 1
                elif service == 'link_and_print_send_line':
                    panel.lines.append(self.mem.read(cpu.R[0], cpu.R[1]).decode('ascii'))
                panel.calls.append((service, *cpu.R[:3]))
                cpu.R[0] = answer & sim.M
                cpu.pc = cpu.rets
                continue
            insn, raw, size = cpu.decode(cpu.pc)
            text = codec.format(insn, raw)
            if text in ('lockset', 'csync') or re.fullmatch(r'r\d+ = cnum', text):
                if text.endswith('cnum'):
                    cpu.R[int(text[1:text.index(' ')])] = 0
                cpu.pc += size
                continue
            cpu.step()
            if cpu.steps - start > limit:
                raise RuntimeError(f'{name}: too many steps')
        return cpu.R[0]

    def read(self, a):
        data = (self.stored or b'')[a[0] - FLASH_AT:][:a[2]]
        if len(data) < a[2]:
            data += b'\xff' * (a[2] - len(data))
        self.mem.write(a[1], data)
        return 0

    def pair(self, a):
        """replace_pair(sector, first, its length, second, its length on the stack): the preset 0 is the first."""
        self.written = self.mem.read(a[1], a[2])
        self.stored = bytes(self.written)
        return 0

    def say(self, line):
        self.panel.lines.clear()
        self.panel.console(line)
        return [x.rstrip('\n') for x in ''.join(self.panel.lines).split('\n') if x]

    def scenes(self, n=8):
        base = self.where.get('hyperrig_scenes', self.where[STATE] + 11936)
        names = self.where.get('hyperrig_scene_names', self.where[STATE] + 3248)
        return [self.mem.read(base + 260 * k, 259) for k in range(n)], [self.mem.read(names + 16 * k, 16) for k in range(n)]

    def wipe(self, n=8):
        base = self.where.get('hyperrig_scenes', self.where[STATE] + 11936)
        names = self.where.get('hyperrig_scene_names', self.where[STATE] + 3248)
        self.mem.write(base, bytes(260 * n))
        self.mem.write(names, bytes(16 * n))

    def setting(self, offset, value=None):
        at = self.where['L01c1f180'] + offset
        if value is not None:
            self.mem.write(at, struct.pack('<i', value))
        return struct.unpack('<i', self.mem.read(at, 4))[0]

    def load(self, record):
        """Read a record as a preset change does, with every effect in the slot of its place; (result, working preset, scenes, names)."""
        self.stored = record
        self.wipe(8 if 'hyperrig_scenes' in self.where else 4)
        result = self.run('preset_preflight_preflight', 0, HEADER)
        working = self.mem.read(self.where[WORKING], 1490)
        if result:
            return result, working, None, None
        self.mem.write(HEADER + 64, bytes(range(16)))
        self.run('scene_import_import_scenes', HEADER + 64)
        return (0, working, *self.scenes(8 if 'hyperrig_scenes' in self.where else 4))


def record(payload, name=b'A preset'):
    return struct.pack('<IIII', TAG, len(payload), zlib.crc32(payload), 0) + name.ljust(24, b'\0') + payload


def stored_presets(flash):
    """The records of presets in a copy of a flash, by the form alone."""
    for sector in [*range(0xBF000, 0xCF000, 0x1000), 0xDD000, 0xDE000]:
        for at in (sector, sector + 0x800):
            tag, n, crc, _ = struct.unpack_from('<IIII', flash, at)
            if tag == TAG and n <= LIMIT and zlib.crc32(flash[at + 40:at + 40 + n]) == crc:
                yield at, flash[at:at + 40 + n]


def check(build, before=None, copy=None):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    p = Pedal(build)
    p.setting(harness.G_PRESET, -1)
    p.setting(88, -1)
    p.wipe()
    slots = [p.add(2), p.add(8), p.add(4)]                                  # boost, compressor, equalizer
    row('three blocks', slots == [0, 1, 2], slots)
    row('SNAPS says eight', p.say('SNAPS') == ['SNAPS 00000000 current=-1'], p.say('SNAPS'))
    # eight scenes with their own knob and name, in the memory, with no preset
    values = [3, 9, 1, 12, 5, 7, 2, 11]
    seen = []
    for k, v in enumerate(values):
        p.run('effect_parameter_lifecycle_parameter_commit', 0, 0, v)
        p.run('effect_enable_command', 1, k & 1) if 'effect_enable_command' in p.where else None
        seen += p.say(f'SNAPSAVE {k}') + p.say(f'SNAPNAME {k} Scene {k + 1} x')
    row('SNAPSAVE and SNAPNAME of eight', seen == [x for k in range(8) for x in (f'SNAPSAVE ok {k} preset=-1', f"SNAPNAME ok {k} 'Scene {k + 1} x' preset=-1")], seen)
    row('SNAPS and the names', p.say('SNAPS') == ['SNAPS 11111111 current=7'] and p.say('SNAPNAME') == [f"SNAPNAME {k} 'Scene {k + 1} x'" for k in range(8)] + ['SNAPNAME end'],
        [p.say('SNAPS'), p.say('SNAPNAME')])
    row('a ninth is refused', all(x[0].startswith('ERR') for x in (p.say('SNAPSAVE 8'), p.say('SNAP 8'), p.say('SNAPNAME 8 x'), p.say('SNAPDEL 8'))),
        [p.say('SNAPSAVE 8'), p.say('SNAP 8')])
    went = []
    for k in (7, 0, 5, 3, 4, 1, 6, 2):
        answer = p.say(f'SNAP {k}')
        went.append((k, answer[0].split(' missing')[0] if answer else None, struct.unpack('<h', p.mem.read(p.object(0) + 70, 2))[0], p.setting(88)))
    row('SNAP brings back the knob of each', went == [(k, f'SNAP ok {k}', values[k], k) for k in (7, 0, 5, 3, 4, 1, 6, 2)], went)
    stepped = []
    for step in (1, 1, 1, -1, -1):
        p.mem.write(p.where[STATE] + 956, struct.pack('<i', step))
        p.run('scene_application_flush')
        stepped.append(p.setting(88))
    row('the next and the previous scene, around the eight', stepped == [3, 4, 5, 4, 3], stepped)
    p.setting(88, 7)
    p.mem.write(p.where[STATE] + 956, struct.pack('<i', 1))
    p.run('scene_application_flush')
    row('after the eighth the first', p.setting(88) == 0, p.setting(88))
    # stored and read again
    records, names = p.scenes()
    p.setting(harness.G_PRESET, 0)
    p.stored = record(b'\5' + bytes(1423))
    answer = p.say('PSAVE 0 Eight')
    payload = p.written[40:] if p.written else b''
    length, crc = struct.unpack_from('<II', p.written, 4) if p.written else (0, 0)
    row('PSAVE writes the packed form', bool(answer) and answer[0].startswith("PSAVE ok 0 'Eight'") and payload[:1] == b'\6' and length == len(payload) >= 1492 and zlib.crc32(payload) == crc,
        [answer, len(payload), payload[:1].hex()])
    result, working, again, again_names = p.load(p.written) if p.written else (None,) * 4
    row('read again: the eight scenes and their names', result == 0 and again == records and again_names == names,
        [result, [k for k in range(8) if again and again[k] != records[k]], again_names])
    row('the working preset is of version 5, with eight in its mask', bool(working) and working[0] == 5 and working[7] == 0xFF, working[:12].hex() if working else None)
    damaged = bytearray(p.written)
    damaged[41] = 200
    struct.pack_into('<I', damaged, 8, zlib.crc32(bytes(damaged[40:])))
    row('a damaged packed record is refused', p.load(bytes(damaged))[0] not in (0, None), None)
    long5 = record(b'\5' + bytes(1600))
    row('a record of version 5 longer than the form is refused', p.load(long5)[0] not in (0, None), None)
    # a block that is added later: each scene has its own values of it, whichever scene one comes from; stored and read again; removed, its slot starts anew
    for stored in (False, True):
        f = Pedal(build)
        f.setting(harness.G_PRESET, -1)
        f.setting(88, -1)
        f.wipe()
        knob = lambda slot=0: struct.unpack('<h', f.mem.read(f.object(slot) + 70, 2))[0]
        masks = lambda: [struct.unpack('<H', x[2:4])[0] for x in f.scenes()[0]]
        turn = lambda slot, value: f.run('effect_parameter_lifecycle_parameter_commit', slot, 0, value)
        for k in (0, 1, 2, 3, 6):
            f.say(f'SNAPSAVE {k}')
        first = masks()
        slot = f.add(2)
        was = knob()
        f.say('SNAPSAVE 3')
        if stored:
            f.setting(harness.G_PRESET, 0)
            f.stored = record(b'\5' + bytes(1423))
            f.say('PSAVE 0 Later')
            seen = [f.load(f.written)[0] if f.written else None, masks()]
            row('a block added after the scenes is in all of them, stored and read again', first == [0] * 8 and slot == 0 and seen == [0, [1, 1, 1, 1, 0, 0, 1, 0]], [first, seen])
            continue
        f.say('SNAP 0')
        turn(0, 5)
        f.say('SNAPSAVE 0')
        went = []
        for k in (1, 2, 3, 6, 2, 1, 0, 1, 2, 3, 0, 6):
            f.say(f'SNAP {k}')
            went.append((k, knob()))
        row('a block added after the scenes has in each of them values of its own', was != 5 and first == [0] * 8 and masks() == [1, 1, 1, 1, 0, 0, 1, 0] and went == [(k, 5 if k == 0 else was) for k, _ in went],
            [first, masks(), went])
        other = f.add(4)
        turn(other, 7)
        f.run('effect_enable_command', other, 0) if 'effect_enable_command' in f.where else None
        on = f.mem.read(f.object(other) + 1, 1)[0]
        f.say('SNAP 2')
        kept = [(x[6 + other], struct.unpack('<h', x[22 + 14 * other:24 + 14 * other])[0]) for x in f.scenes()[0] if x[0]]
        row('what it was when the scene was left is in the others, on or off too', other == 1 and kept == [(on, knob(other))] * 5 and masks() == [3, 3, 3, 3, 0, 0, 3, 0], [other, on, kept, masks()])
        f.say(f'FXR {other}')
        gone, again = masks(), f.add(8)
        f.say('SNAP 1')
        seen = [struct.unpack('<7h', x[22 + 14 * again:36 + 14 * again]) for x in f.scenes()[0] if x[0]]
        own = struct.unpack('<7h', struct.pack('<7H', *(f.run('preset_application_parameter', again, k) & 0xFFFF for k in range(7))))
        row('a block removed leaves the scenes, and another in its slot starts anew', gone == [1, 1, 1, 1, 0, 0, 1, 0] and again == other and masks() == [3, 3, 3, 3, 0, 0, 3, 0] and len(set(seen)) == 1
            and seen[0] == own, [gone, again, seen])
    # four at most: the same bytes as before
    q = Pedal(before) if before else None
    if q:
        both = []
        for x in (p, q):
            x.setting(harness.G_PRESET, -1)
            x.wipe(8 if x is p else 4)
            x.setting(88, -1)
            for slot in (0, 1, 2):
                x.run('effect_parameter_lifecycle_parameter_commit', 0, 0, 4) if x is p else None
            if x is q:
                x.add(2), x.add(8), x.add(4)
                x.run('effect_parameter_lifecycle_parameter_commit', 0, 0, 4)
            for k in range(4):
                x.run('effect_parameter_lifecycle_parameter_commit', 0, 0, 2 + k)
                x.say(f'SNAPSAVE {k}')
                x.say(f'SNAPNAME {k} N{k}')
            x.run('effect_parameter_lifecycle_parameter_commit', 0, 0, 4)
            x.setting(harness.G_PRESET, 0)
            x.stored = record(b'\5' + bytes(1423))
            x.written = None
            x.say('PSAVE 0 Four')
            both.append(x.written)
        row('a preset with four scenes is stored with the same bytes as before', both[0] is not None and both[0] == both[1], [both[0] and both[0][40:56].hex(), both[1] and both[1][40:56].hex()])
        refused = q.load(record(payload))[0] if payload else None
        row('the build before takes the packed form as no preset', refused not in (0, None), refused)
    if q and copy:
        found = list(stored_presets(Path(copy).read_bytes()))
        wrong = []
        for at, data in found:
            a, b = p.load(data), q.load(data)
            same = a[0] == b[0] and a[1] == b[1] and (a[0] or (a[2][:4] == b[2] and a[3][:4] == b[3] and not any(x[0] for x in a[2][4:]) and not any(any(x) for x in a[3][4:])))
            if not same:
                wrong.append(hex(at))
        row(f'the {len(found)} presets of the copy are read as before, with no other scenes', found and not wrong, wrong)
    # no room: sixteen blocks, every knob of every scene different
    r = Pedal(build)
    r.setting(harness.G_PRESET, -1)
    r.setting(88, -1)
    r.wipe()
    made = [r.run('effect_setup_create', bank, 99, 36) for bank in (0, 1) for _ in range(8)]                 # sixteen of the block with seven knobs
    made = [m - (1 << 32) if m & 0x80000000 else m for m in made]
    put = []
    for k in range(8):
        if made.count(-1) or min(made) < 0:
            break
        for s in range(len(made)):
            for j in range(7):
                r.mem.write(r.object(s) + 70 + 2 * j, struct.pack('<h', (k * 37 + s * 5 + j * 3) % 90 + 1 + 100 * (k & 1)))
        put.append(r.say(f'SNAPSAVE {k}')[0])
    held, there = [x for x in put if 'ok' in x], r.say('SNAPS')[0]
    row('what does not fit is refused, and the scenes that are there stay', min(made) >= 0 and 4 <= len(held) < 8 and all(x == 'ERR SNAPSAVE no room for these scenes: take a block or a scene away' for x in put[len(held):]) and
        there.split()[1] == '1' * len(held) + '0' * (8 - len(held)), [len(made), put, there])
    return rows


class Feet:
    """Switches outside the factory layout: the transitions as the control scan hands them on, and its turns, every ten milliseconds."""

    def __init__(self, build):
        self.p = p = Pedal(build)
        p.setting(harness.G_PRESET, 4)
        p.setting(88, -1)
        p.wipe()
        self.now, self.did = 20_000, []
        for name in ('scene_application_select', 'selection_preset_step', 'slot_commands_enable_command', 'selection_effect_resolve'):
            p.at[p.where[name]] = lambda a, name=name: self.did.append((name.split('_')[1] + ' ' + name.split('_')[2], a[0] - (1 << 32) if a[0] >> 31 else a[0])) or 0

    def byte(self, at, value=None):
        where = self.p.where[STATE] + at
        if value is not None:
            self.p.mem.write(where, bytes([value]))
        return self.p.mem.read(where, 1)[0]

    def actions(self, kind, block=False):
        hold = (4, 0, 3) if kind == 1 else (0, 0, 0)             # as the editor makes them
        self.p.say('FSMODE layout=custom')
        for f in range(3):
            for g, x in ((0, (kind, f if kind == 1 else 2, 255 if kind == 1 else 0)), (1, (hold[f], 0, 255)), (2, (0, 0, 255))):
                self.p.say(f'FSA {f} {g} {x[0]} {x[1]} {x[2]}')

    def there(self, *scenes):
        base = self.p.where['hyperrig_scenes']
        for k in range(8):
            self.p.mem.write(base + 260 * k, bytes([int(k in scenes)]))

    def turns(self, ms):
        for _ in range(ms // 10):
            self.now += 10
            self.p.run('control_actions_tick', 10, 1, self.now)
            self.p.run('hyperrig_pairs_turn', self.now)

    def put(self, f, level):
        raw = self.p.mem.read(self.p.where['L01c1f180'] + 116 + f, 1)[0]
        self.p.run('hyperrig_transition', raw, level, self.now // 10, self.now)

    def press(self, *switches, ms=120, gap=20):
        """Down one after the other, kept, and up together; what the application was made to do."""
        self.did.clear()
        for f in switches:
            self.put(f, 1)
            self.turns(gap if f != switches[-1] else 0)
        self.turns(ms)
        for f in switches:
            self.put(f, 0)
        self.turns(400)
        return list(self.did)


def pairs(build):
    rows, A, B, C = [], 0, 1, 2

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    s = Feet(build)
    tap = lambda k: [('application select', k)]
    step = lambda n: [('preset step', n)]
    s.actions(1)
    s.there(*range(8))
    s.turns(50)
    seen = [s.press(A), s.press(B), s.press(C)]
    row('Scenes: the taps are the scenes 1, 2 and 3', seen == [tap(0), tap(1), tap(2)], seen)
    s.did.clear()
    s.put(A, 1)
    s.turns(40)
    early = list(s.did)
    s.turns(20)
    late = list(s.did)
    s.put(A, 0)
    s.turns(400)
    row('a press waits 45 ms for its neighbour, and is given once', early == [] and list(s.did) == tap(0), [early, late, s.did])
    s.did.clear()
    s.put(A, 1)
    s.turns(10)
    s.put(A, 0)
    row('a press shorter than that is given at the release', list(s.did) == tap(0), s.did)
    s.turns(400)
    seen = [s.press(B, C), s.byte(76), s.press(A), s.press(C), s.press(B, C), s.byte(76), s.press(A), s.press(B), s.press(B, C), s.byte(76), s.press(A, B), s.byte(76), s.press(B, A), s.byte(76), s.press(B)]
    row('B+C the next three, A+B the three before, around; the taps follow', seen == [[], 1, tap(3), tap(5), [], 2, tap(6), tap(7), [], 0, [], 2, [], 1, tap(4)], seen)
    s.there(0, 1, 2, 3)
    s.p.setting(88, 0)
    s.turns(20)
    seen = [s.byte(76), s.press(B, C), s.byte(76), s.press(A), s.press(B, C), s.byte(76)]
    row('groups without a scene are passed over', seen == [0, [], 1, tap(3), [], 0], seen)
    s.there(*range(8))
    s.p.setting(88, 7)
    s.turns(20)
    row('the group follows the scene that is chosen elsewhere', s.byte(76) == 2 and s.press(A) == tap(6), s.byte(76))
    seen = [s.press(B, C, ms=1300), s.byte(52), s.byte(76), s.press(A), s.byte(52), s.press(A)]
    row('B+C held a second is the tuner, a tap closes it, and no scene changes', seen == [[], 1, 2, [], 0, tap(6)], seen)
    seen = [s.press(A, B, ms=1300), s.byte(52), s.byte(76)]
    row('A+B held a second does nothing', seen == [[], 0, 2], seen)
    s.put(A, 1), s.turns(20), s.put(B, 1), s.turns(60)
    levels = [s.byte(1567 + s.p.mem.read(s.p.where['L01c1f180'] + 116 + f, 1)[0]) for f in (A, B, C)]
    s.put(A, 0), s.put(B, 0), s.turns(50)
    row('the levels of a pair stand where the Bluetooth gesture reads them', levels == [1, 1, 0] and [s.byte(1567 + k) for k in range(3)] == [0, 0, 0], levels)
    s.p.setting(88, 0)
    s.turns(20)
    seen = [s.press(A, ms=1200), s.press(B, ms=1200), s.press(C, ms=1200), s.press(A, C)]
    row('a hold of A and C is the preset before and after, behind the tap; A and C together are two taps',
        seen[:3] == [tap(0) + step(-1), tap(1), tap(2) + step(1)] and sorted(seen[3]) == sorted(tap(0) + tap(2)), seen)
    lit = [s.p.run('hyperrig_shown_scene', f) for f in range(3)]
    s.press(B, C)
    lit += [s.p.run('hyperrig_shown_scene', f) for f in range(3)]
    row('the lights are of the scenes of the group', lit == [0, 1, 2, 3, 4, 5], lit)
    s.actions(8)
    s.turns(50)
    seen = [s.press(A), s.press(A, B), s.press(B, C), s.press(B, C, ms=1300), s.byte(52)]
    s.byte(52, 0)
    row('Stomp: a tap is its block, the pairs the preset before and after, B+C held the tuner', [x[0] for x in seen[0]][:1] == ['effect resolve'] and seen[1:] == [step(-1), step(1), [], 1], seen)
    seen = {}
    for kind in (1, 8):
        s.actions(kind)
        s.turns(50)
        for press, ms in (((A,), 120), ((C,), 120), ((A,), 1300), ((C,), 1300), ((A, B), 120), ((B, C), 120)):
            s.byte(52, 1)
            seen[f'{kind} {press} {ms}'] = [len(press), s.press(*press, ms=ms), s.byte(52)]
    row('with the tuner on a switch closes it and does nothing else; of two at once the second is a tap, and no preset is chosen',
        all(on == 0 and (n == 2 or did == []) and not any(x[0] == 'preset step' for x in did) for n, did, on in seen.values()), seen)
    s.actions(8)
    s.turns(50)
    s.p.say('FSA 2 0 7 0 255')
    s.turns(20)
    s.did.clear()
    s.put(A, 1)
    at_once = list(s.did)
    s.turns(100)
    s.put(A, 0)
    s.turns(400)
    row('with other actions nothing waits, and pairs are two presses', [x[0] for x in (at_once or s.did)][:1] == ['effect resolve'] and not any(x[0] == 'preset step' for x in s.press(A, B)), [at_once, s.did])
    s.p.say('FSMODE layout=factory')
    s.turns(20)
    row('in the factory layout the bank is the preset\'s again', s.byte(76) == 4 // 3, s.byte(76))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build')
    parser.add_argument('--before')
    parser.add_argument('--copy', help='a whole copy of a pedal\'s flash; nothing of it is printed')
    a = parser.parse_args(argv)
    rows = check(a.build, a.before, a.copy) + pairs(a.build)
    for r in rows:
        print('   ok  ' if r['held'] else '   FAIL', r['check'], '' if r['held'] else json.dumps(r['seen'], default=repr)[:600])
    print(json.dumps({'held': all(r['held'] for r in rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(r['held'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
