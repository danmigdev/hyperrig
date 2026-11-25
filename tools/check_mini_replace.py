"""Put a block in the place of another (FXC) in a built product firmware, in the pi32v2 simulator. Offline; no device is opened.

The application's own code runs from the bytes of the firmware: the console word, its sums of the processor, the making and the taking away of
blocks, the scenes. What stands for the pool of memory is a list of its own here, of a size that the check chooses: first fit, and a block that is
given back twice, or was never taken, is an error. The pause of the sound is recorded, and memory is filled at once.

Every place of a chain, branches, a full section and sixteen blocks; what does not fit (processor, memory, no IR): then every byte of the blocks, the
chain, the scenes and what was measured is compared, or all but the memory that was given back and taken again; the switch in every scene, knobs of
scenes, stored and read again; every type in the place of another. Nothing of this is a hardware or audio test.

Usage, from the repository root (about ten minutes, two processes):
    python -B tools/check_mini_replace.py BUILD [--part NAME]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_effect_block as block  # noqa: E402
import check_mini_panel as harness  # noqa: E402
import check_mini_scenes as scenes  # noqa: E402

sim, codec = scenes.sim, scenes.codec
GIVE, POOL, ROOM = 0x01C60010, 0x01D00000, 260_000
BLOCKS, CHAIN, COSTS, METERS, GLIDES = 'L01c2c220', 'L01c32db0', 'L01c343d8', 'L01c2e074', 'L01c2e5a0'
PLENTY = 400_000
ON, LANE, MODE, KNOBS, MEMORY = 1, 4, 6, 70, 84
ONCE = ['pause', 'resume']


class Board(scenes.Pedal):
    def __init__(self, build, room=ROOM):
        super().__init__(build)
        self.room, self.taken, self.wrong, self.sound, self.kinds = room, {}, [], [], {}
        self.at[block.ALLOCATOR] = lambda a: self.take(a[0])
        self.at[GIVE] = lambda a: self.give(a[0])
        self.at[self.where['effect_parameter_support_clear_halfwords']] = lambda a: self.mem.write(a[0], bytes(a[1] + 1 >> 1 << 2)) or 0
        for name in ('audio_pause_pause_audio', 'audio_pause_resume_audio'):
            self.at[self.where[name]] = lambda a, name=name: self.sound.append(name.split('_')[2]) or 0
        self.mem.write(self.where[CHAIN] + 56, struct.pack('<I', GIVE))
        self.names = {k: self.text(self.word(self.where[block.NAMES] + 4 * k)) for k in range(40)}
        self.setting(harness.G_PRESET, -1)
        self.setting(88, -1)
        self.wipe()
        self.budget(PLENTY)

    def kind(self, pc, recorded):
        if pc in self.at:
            return 'own', None
        if pc in recorded:
            return 'service', recorded[pc]
        insn, raw, size = self.cpu.decode(pc)
        text = codec.format(insn, raw)
        if text in ('lockset', 'csync'):
            return 'pass', size
        if re.fullmatch(r'r\d+ = cnum', text):
            return 'core', (size, int(text[1:text.index(' ')]))
        return 'step', None

    def run_with(self, name, args, limit=3_000_000, stop=None):
        """As Pedal's, but what is at an address is looked at once."""
        cpu, panel = self.cpu, self.panel
        stop = sim.RETURN if stop is None else stop
        recorded = {panel.where[n]: n for n in harness.RECORDED if n in panel.where}
        cpu.R[:len(args)] = [a & sim.M for a in args]
        cpu.rets, cpu.pc, start, cpu.sp = sim.RETURN, panel.where[name], cpu.steps, sim.STACK_TOP
        while cpu.pc != stop:
            pc = cpu.pc
            if pc not in self.kinds:
                self.kinds[pc] = self.kind(pc, recorded)
            what, more = self.kinds[pc]
            if what == 'step':
                cpu.step()
                if cpu.steps - start > limit:
                    raise RuntimeError(f'{name}: too many steps')
            elif what == 'own':
                cpu.R[0] = self.at[pc](list(cpu.R[:4])) & sim.M
                cpu.pc = cpu.rets
            elif what == 'service':
                answer = 1 if more == 'preset_storage_available' else harness.RECORDED[more]
                if more == 'link_and_print_send_line':
                    panel.lines.append(self.mem.read(cpu.R[0], cpu.R[1]).decode('ascii'))
                panel.calls.append((more, *cpu.R[:3]))
                cpu.R[0] = answer & sim.M
                cpu.pc = cpu.rets
            elif what == 'pass':
                cpu.pc += more
            else:
                cpu.R[more[1]] = 0
                cpu.pc += more[0]
        return cpu.R[0]

    # the pool
    def take(self, n):
        n, at = n + 15 & ~15, 0
        for start, size in sorted(self.taken.items()):
            if start - at >= n:
                break
            at = start + size
        if at + n > self.room:
            return 0
        self.taken[at] = n
        return POOL + at

    def give(self, address):
        if self.taken.pop(address - POOL, None) is None:
            self.wrong.append(hex(address))
        return 0

    def budget(self, ticks):
        self.mem.write(self.where[CHAIN] + 48, struct.pack('<I', ticks))

    def total(self):
        return self.run('effect_setup_total_cost')

    # blocks
    def new(self, section, name):
        answer = self.say(f'FXA {section} 99 {name}')
        m = answer and re.match(r'FXA id=(\d+)', answer[0])
        assert m, (section, name, answer)
        return int(m.group(1))

    def name_of(self, kind):
        """The name of an effect: the application's table, and the list of the console for those that HyperRig adds."""
        if kind not in self.names:
            self.names.update({int(m[1]): m[2] for x in self.say('FXT') for m in [re.match(r'FXT (\d+) (\S+) cost=', x)] if m})
        return self.names[kind]

    def chain(self):
        """{section: [(id, type, on, lane, group, knobs)]}, as FXS lists it."""
        out, at = {}, self.where[CHAIN]
        for n, s in enumerate('PQ'):
            out[s], group, last = [], -1, 0
            for slot in self.mem.read(at + 348 + 10 * n, self.mem.read(at + 14 + n, 1)[0]):
                record = self.mem.read(self.object(slot), 84)
                lane = record[LANE]
                group, last = group + (1 if lane and not last else 0), lane
                out[s].append((slot, self.name_of(record[0]) if record[2] else None, record[ON], lane, group if lane else -1, struct.unpack_from('<7h', record, KNOBS)))
        return out

    def knob(self, slot, k=0):
        return struct.unpack('<h', self.mem.read(self.object(slot) + KNOBS + 2 * k, 2))[0]

    def on(self, slot):
        return self.mem.read(self.object(slot) + ON, 1)[0]

    def clear(self):
        for section in self.chain().values():
            for x in section:
                self.say(f'FXR {x[0]}')

    def ir(self, n=256):
        data = struct.pack(f'<{n}h', *[1000 if k < 40 else 0 for k in range(n)])
        for line in (f'IRBEGIN {n} 0 48', *(f'IRB {k} {data[k:k + 64].hex()}' for k in range(0, len(data), 64)), 'IREND %08x' % zlib.crc32(data)):
            answer = self.say(line)
        return answer[0].startswith('IR ok')

    def levels(self):
        """The levels and the frequencies of the groups, where FXMIX and FXXO keep them."""
        return self.mem.read(self.where[CHAIN] + 160, 108) + self.mem.read(self.where[CHAIN] + 368, 48)

    def everything(self):
        """Every byte that a block has anywhere."""
        read = lambda name, n: self.mem.read(self.where[name], n)
        return {'blocks': read(BLOCKS, 16 * 480), 'chain': read(CHAIN, 640), 'costs': read(COSTS, 64), 'meters': read(METERS, 15 * 88 + 4), 'glides': read(GLIDES, 8 * 448),
                'scenes': self.scenes(), 'memory': dict(self.taken), 'contents': {a: self.mem.read(POOL + a, n) for a, n in self.taken.items()}}

    def change(self, slot, wanted, preset=-1, now=None):
        """FXC; (its answer, what the sound did)."""
        now = now or next(x[1] for s in self.chain().values() for x in s if x[0] == slot)
        self.sound.clear()
        return self.say(f'FXC {preset} {slot} {now} {wanted}'), list(self.sound)


def made(answer, name):
    """The id of the new block, or None."""
    m = len(answer) == 2 and re.fullmatch(rf'FXC id=(\d+) {name}', answer[0])
    return int(m.group(1)) if m and re.match(r'FX cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+ B$', answer[1]) else None


def differs(a, b):
    """Where two states differ, in a few words."""
    return [k if not isinstance(a[k], bytes) else f'{k} {[i for i in range(len(a[k])) if a[k][i] != b[k][i]][:12]}' for k in a if a[k] != b[k]]


def replaced(before, after, old, new, name):
    """after is before with the block old become new, and nothing else."""
    if new is None:
        return False
    want = {s: [(new, name, *x[2:5]) if x[0] == old else x[:5] for x in before[s]] for s in before}
    return {s: [x[:5] for x in after[s]] for s in after} == want and all(a[5] == b[5] for s in before for a, b in zip(before[s], after[s]) if a[0] != old)


def words(build, row):
    p = Board(build)
    ids = [p.new('P', x) for x in ('boost', 'comp', 'eq')]
    before, out, usage = p.everything(), [], 'ERR FXC <preset> <id> <type> <new type>'
    p.sound.clear()
    for line, want in (('FXC', usage), ('FXC -1 1 comp', usage), ('FXC -1 1 comp ts9 x', usage), ('FXC x 1 comp ts9', usage), ('FXC -1 1  ts9', usage), ('FXC -1 1 comp ' + 'x' * 60, usage),
                       ('FXC 4 1 comp ts9', 'ERR FXC another preset'), ('FXC -1 1 eq ts9', 'ERR FXC another block'), ('FXC -1 1 nothing ts9', 'ERR FXC another block'),
                       ('FXC -1 9 comp ts9', 'ERR FXC another block'), ('FXC -1 16 comp ts9', 'ERR FXC another block'), ('FXC -1 -1 comp ts9', 'ERR FXC another block'),
                       ('FXC -1 1 comp laser', 'ERR FXC unknown effect'), ('FXC -1 1 comp 9', 'ERR FXC unknown effect')):
        answer = p.say(line)
        if answer != [want]:
            out.append([line, answer])
    row('what is not a block of this preset, or not an effect, is refused', not out and ids == [0, 1, 2], out)
    row('then nothing was touched, and the sound was not paused', p.sound == [] and not differs(before, p.everything()), [p.sound, differs(before, p.everything())])
    p.setting(harness.G_PRESET, 4)
    answer, sound = p.change(1, 'ts9', preset=4)
    row('with a preset on the pedal, its number', made(answer, 'ts9') == 3 and sound == ONCE, [answer, sound])


def places(build, row):
    p, out = Board(build), []
    for s, names in (('P', ('boost', 'comp', 'eq')), ('Q', ('gate', 'klon', 'delay', 'rat'))):
        for x in names:
            p.new(s, x)
    for s, k, name in (('P', 0, 'ts9'), ('P', 1, 'chorus'), ('P', 2, 'gate'), ('Q', 0, 'reverb2'), ('Q', 1, 'boost'), ('Q', 2, 'hybrid'), ('Q', 3, 'muff')):
        before = p.chain()
        old = before[s][k][0]
        answer, sound = p.change(old, name)
        if sound != ONCE or not replaced(before, p.chain(), old, made(answer, name), name):
            out.append([s, k, name, answer, sound, before, p.chain()])
    row('first, between and last, before the amp and after it: the place, the section and the others stay', not out, out)
    old = p.chain()['Q'][1][0]
    p.say(f'FXE {old} 0')
    before = p.chain()
    answer, sound = p.change(old, 'geq')
    row('a block that is off gives one that is off', before['Q'][1][2] == 0 and sound == ONCE and replaced(before, p.chain(), old, made(answer, 'geq'), 'geq'), [answer, p.chain()])
    p.clear()
    row('when all are taken away the pool is empty, and nothing was given back twice', not p.taken and not p.wrong, [p.taken, p.wrong])


def branches(build, row):
    p, out = Board(build), []
    for s in 'PQ':
        ids = [p.new(s, x) for x in ('boost', 'comp', 'eq', 'gate', 'klon', 'tremolo', 'rat', 'geq')]
        for k, lane in ((1, 1), (2, 2), (4, 1), (6, 2), (7, 1)):
            p.say(f'FXL {ids[k]} {lane}')
        for g in range(3):
            p.say(f'FXMIX {s} {g} {-100 * g - 100} {-100 * g - 150}')
    groups, mix, held = [x[4] for x in p.chain()['Q']], p.say('FXMIX'), p.levels()
    row('three groups in a section, one of a single block', groups == [-1, 0, 0, -1, 1, -1, 2, 2] and len(mix) == 7, [groups, mix])
    for s in 'PQ':
        for k, name in enumerate(('ds1', 'ts9', 'chorus', 'bd2', 'fuzzface', 'vibrato', 'plate', 'delay')):
            before = p.chain()
            old = before[s][k][0]
            answer, sound = p.change(old, name)
            if sound != ONCE or not replaced(before, p.chain(), old, made(answer, name), name) or p.levels() != held:
                out.append([s, k, name, answer, before[s], p.chain()[s], [i for i in range(len(held)) if p.levels()[i] != held[i]]])
    row('in a branch, alone in it, beside it, between two groups: the branch, the groups and their levels stay', not out and p.say('FXMIX') == mix, out[:2])
    p.clear()
    row('the pool is empty afterwards', not p.taken and not p.wrong, [p.taken, p.wrong])


def full(build, row):
    p, out = Board(build, 400_000), []
    for k in range(10):
        p.new('Q', ('boost', 'comp', 'eq', 'gate', 'klon')[k % 5])
    answer = p.say('FXA Q 99 boost')
    row('an eleventh block of a section is refused', answer == ['ERR FXA bank full'], answer)
    for k in (0, 4, 9):
        before = p.chain()
        answer, sound = p.change(before['Q'][k][0], 'ts9')
        if sound != ONCE or not replaced(before, p.chain(), before['Q'][k][0], made(answer, 'ts9'), 'ts9'):
            out.append([k, answer, p.chain()])
    row('a block of a full section', not out, out)
    out = []
    p.ir()
    for name in ('delay', 'rat', 'ir', 'muff', 'gate', 'geq'):
        p.new('P', name)
    answer = p.say('FXA P 99 boost')
    row('a seventeenth is refused', answer == ['ERR FXA bank full'], answer)
    for s, k, name in (('P', 0, 'reverb2'), ('P', 5, 'boost'), ('Q', 9, 'hybrid'), ('P', 2, 'comp'), ('Q', 0, 'acoustic'), ('P', 0, 'ir')):
        before = p.chain()
        answer, sound = p.change(before[s][k][0], name)
        if made(answer, name) != before[s][k][0] or sound != ONCE or not replaced(before, p.chain(), before[s][k][0], before[s][k][0], name):
            out.append([s, k, name, answer, p.chain()])
    row('one of sixteen: the new block is in its slot', not out, out)
    p.budget(p.total() - 1)
    out, before = [], p.everything()
    for s, k in (('P', 0), ('Q', 9), ('Q', 5)):
        answer, sound = p.change(p.chain()[s][k][0], 'acoustic')
        if answer != ['ERR FXC not enough CPU'] or sound != ONCE or differs(before, p.everything()):
            out.append([s, k, answer, differs(before, p.everything())])
    row('one of sixteen, and not enough processor: every byte is as before', not out, out)
    p.budget(PLENTY)
    p.clear()
    row('the pool is empty afterwards', not p.taken and not p.wrong, [p.taken, p.wrong])


def processor(build, row):
    p = Board(build)
    ids = [p.new('Q', x) for x in ('boost', 'delay', 'klon', 'reverb2')]
    p.say(f'FXL {ids[1]} 1')
    p.say('FXMIX Q 0 -120 -240')
    for k in range(3):
        p.say(f'SNAPSAVE {k}')
    p.say('SNAP 1')
    p.mem.write(POOL + 4, b'\x11' * 64)
    p.budget(p.total() + 200)
    before, out = p.everything(), []
    for slot, name in ((ids[0], 'hybrid'), (ids[1], 'acoustic'), (ids[2], 'acoustic'), (ids[3], 'acoustic')):
        answer, sound = p.change(slot, name)
        if answer != ['ERR FXC not enough CPU'] or sound != ONCE or differs(before, p.everything()):
            out.append([slot, name, answer, sound, differs(before, p.everything())])
    row('not enough processor: refused, and every byte is as before: blocks, what is in their memory, chain, scenes', not out, out)
    p.say(f'FXE {ids[0]} 0')
    was = p.chain()
    answer, _ = p.change(ids[0], 'acoustic')
    new = made(answer, 'acoustic')
    row('a block that is off needs no processor', replaced(was, p.chain(), ids[0], new, 'acoustic'), [answer, p.chain()])
    answer = p.say(f'FXE {new} 1')
    row('switched on it says that there is none', answer == ['ERR FXE not enough CPU'], answer)
    answer, _ = p.change(new, 'hybrid')
    row('again in the place of one that is off', made(answer, 'hybrid') is not None and p.chain()['Q'][0][1:3] == ('hybrid', 0), [answer, p.chain()['Q']])
    # antialiasing is lowered as when a block is added, with what a branch of its own takes counted
    q = Board(build)
    ids = [q.new('Q', x) for x in ('boost', 'comp', 'eq')]
    q.say(f'FXL {ids[1]} 1')
    answer, _ = q.change(ids[1], 'klon')
    slot = made(answer, 'klon')
    most, usual, seen = q.total(), q.mem.read(q.object(slot) + MODE, 1)[0], []
    for spare in (0, -1, -600, -1500, -2500, -4000, -6000):
        q.budget(PLENTY)
        q.change(slot, 'comp')
        slot = q.chain()['Q'][1][0]
        q.budget(max(0, most + spare))
        answer, _ = q.change(slot, 'klon')
        if made(answer, 'klon') is None:
            seen.append((spare, None, answer == ['ERR FXC not enough CPU']))
        else:
            slot = made(answer, 'klon')
            seen.append((spare, q.mem.read(q.object(slot) + MODE, 1)[0], q.total() <= most + spare))
    modes = [m for _, m, _ in seen if m is not None]
    row('antialiasing is lowered to what fits, its branch counted, and never more is used than there is',
        usual and modes and modes[0] == usual and modes == sorted(modes, reverse=True) and min(modes) < usual and seen[-1][1] is None and all(x[2] for x in seen), [most, usual, seen])


def impulse(build, row):
    p = Board(build)
    ids = [p.new('P', x) for x in ('boost', 'delay')]
    before = p.everything()
    answer, sound = p.change(ids[1], 'ir')
    row('no IR is loaded: refused, and every byte is as before', answer == ['ERR FXC no IR loaded'] and sound == [] and not differs(before, p.everything()), [answer, differs(before, p.everything())])
    p.say(f'FXE {ids[1]} 0')
    before = p.everything()
    answer, _ = p.change(ids[1], 'ir')
    row('off too', answer == ['ERR FXC no IR loaded'] and not differs(before, p.everything()), answer)
    p.say(f'FXE {ids[1]} 1')
    row('an IR is loaded', p.ir(), None)
    was = p.chain()
    answer, _ = p.change(ids[1], 'ir')
    cab = made(answer, 'ir')
    row('then it is there', replaced(was, p.chain(), ids[1], cab, 'ir'), [answer, p.chain()])
    # an IR of its own, in the memory; with slots left and with sixteen blocks
    n, parts = 128, lambda r: (r[:8], r[46:84], r[88:92], r[108:288])
    for sixteen in (False, True):
        p = Board(build)
        p.ir()
        cab = p.new('P', 'ir')
        for s in 'PPPPPPPPPQQQQQQ' if sixteen else '':
            p.new(s, 'gate')
        p.mem.write(0x01C7A000, struct.pack(f'<{n}h', *[900 if k < 20 else 0 for k in range(n)]))
        p.mem.write(sim.STACK_TOP, struct.pack('<I', 48))
        own = p.run('ir_effect_lifecycle_assign_direct', cab, 0x01C7A000, n, 0)
        record, what = p.mem.read(p.object(cab), 480), ', of sixteen' if sixteen else ''
        samples = struct.unpack_from('<I', record, 48)[0]
        row(f'an IR of its own{what}', own == 0 and POOL <= samples and len(p.taken) == 2, [own, hex(samples), p.taken])
        p.room = sum(p.taken.values()) + 2000
        held, was = {k: p.mem.read(POOL + k, v) for k, v in p.taken.items()}, p.chain()
        answer, _ = p.change(cab, 'cloud')
        after = p.mem.read(p.object(cab), 480)
        row(f'it stays with its IR when the other does not fit{what}', answer[0].startswith('ERR FXC out of memory') and p.chain() == was and parts(after) == parts(record) and after[84:88] != bytes(4) and
            after[288:292] != bytes(4) and sorted(p.taken.values()) == sorted(len(v) for v in held.values()) and p.mem.read(samples, 2 * n) == held[samples - POOL][:2 * n] and not p.wrong,
            [answer, p.taken, [i for i in range(480) if after[i] != record[i]]])
        p.room = ROOM
        answer, _ = p.change(cab, 'hybrid')
        row(f'replaced, its own IR is given back too{what}', made(answer, 'hybrid') is not None and len(p.taken) == 1 and not p.wrong, [answer, p.taken, p.wrong])


def memory(build, row):
    p = Board(build)
    ids = [p.new('Q', x) for x in ('boost', 'reverb2', 'eq')]
    p.room = sum(p.taken.values()) + 4000
    answer = p.say('FXA Q 99 shimmer')
    row('both do not fit', answer[0].startswith('ERR FXA out of memory'), answer)
    was = p.chain()
    answer, sound = p.change(ids[1], 'shimmer')
    row('the memory of the old block is there for the new one', sound == ONCE and replaced(was, p.chain(), ids[1], made(answer, 'shimmer'), 'shimmer') and len(p.taken) == 1 and not p.wrong, [answer, p.taken])
    # a delay that was made longer, its knobs, its branch and the scenes; then something larger, with slots left and with sixteen blocks
    for sixteen in (False, True):
        q = Board(build)
        ids = [q.new('Q', x) for x in ('boost', 'delay', 'eq')]
        if sixteen:
            ids += [q.new(s, 'gate') for s in 'PPPPPPPPPPQQQ']
        old = ids[1]
        q.say(f'FXL {old} 2')
        for k, v in ((0, 450), (1, 33), (2, 77)):
            q.say(f'FXP {old} {k} {v}')
        q.say('SNAPSAVE 0')
        q.say(f'FXP {old} 1 12')
        q.say(f'FXE {old} 0')
        q.say('SNAPSAVE 4')
        q.say(f'FXE {old} 1')
        q.say(f'FXP {old} 1 44')
        q.room = sum(q.taken.values()) + 3000
        before, was, record = q.everything(), q.chain(), q.mem.read(q.object(old), 480)
        answer, sound = q.change(old, 'cloud')
        after, now = q.everything(), q.mem.read(q.object(old), 480)
        others = lambda x: x['blocks'][:480 * old] + x['blocks'][480 * (old + 1):]
        if not sixteen:                                              # what was begun in the slot that was free is not a block
            free = 480 * max(ids) + 480
            others = lambda x, cut=free: x['blocks'][:480 * old] + x['blocks'][480 * (old + 1):cut]
        what = ', of sixteen' if sixteen else ''
        apart = [k for k in ('scenes', 'glides') if after[k] != before[k]] + ([] if others(after) == others(before) else ['others'])
        if sixteen:
            apart += [k for k in ('chain', 'costs', 'meters') if after[k] != before[k]]
        row(f'out of memory{what}: the old block is there with its knobs, its branch and its memory, in the scenes too',
            answer[0].startswith('ERR FXC out of memory') and sound == ONCE and q.chain() == was and not apart and now[:MEMORY] == record[:MEMORY] and now[88:92] == record[88:92] and now[104:110] == record[104:110] and
            POOL <= q.word(q.object(old) + MEMORY) < POOL + q.room and sorted(after['memory'].values()) == sorted(before['memory'].values()) and not q.wrong,
            [answer, apart, differs(before, after)[:6], [i for i in range(480) if now[i] != record[i]], q.taken, before['memory']])
        seen = []
        for k in (0, 4):
            q.say(f'SNAP {k}')
            seen.append((q.knob(old, 0), q.knob(old, 1), q.knob(old, 2), q.on(old)))
        row(f'and the scenes bring it back as before{what}', seen == [(450, 33, 77, 1), (450, 12, 77, 0)], seen)
        was = q.chain()
        answer, _ = q.change(old, 'cloud')
        new = made(answer, 'cloud')
        row(f'off it needs none{what}', was['Q'][1][2] == 0 and replaced(was, q.chain(), old, new, 'cloud') and q.word(q.object(new) + MEMORY) == 0, [answer, q.chain()['Q'][1]])
        answer = q.say(f'FXE {new} 1')
        row(f'switched on it says that there is none{what}', answer[0].startswith('ERR FXE out of memory'), answer)
    # the four states of the large reverbs
    r = Board(build, 2_000_000)
    ids = [r.new('Q', x) for x in ('boost', 'reverb2', 'plate', 'hybrid', 'cloud')]
    fifth, was = r.say('FXA Q 99 reverb2'), r.chain()
    answer, _ = r.change(ids[2], 'spring')
    row('a large reverb in the place of one of the four that there can be', fifth[0].startswith('ERR FXA out of memory') and replaced(was, r.chain(), ids[2], made(answer, 'spring'), 'spring'), [fifth, answer, r.chain()])
    before, was = r.everything(), r.chain()
    answer, _ = r.change(ids[0], 'plate')
    apart = [x for x in differs(before, r.everything()) if not x.startswith(('blocks', 'chain'))]
    row('a fifth one is refused, and the chain is as before', answer[0] == fifth[0].replace('FXA', 'FXC') and r.chain() == was and not apart, [answer, apart, r.chain()])
    # its memory is gone while it is out
    s = Board(build)
    ids = [s.new('Q', x) for x in ('boost', 'delay')]
    s.at[GIVE] = lambda a: s.give(a[0]) or setattr(s, 'room', 100) or 0
    was = s.chain()
    answer, _ = s.change(ids[1], 'cloud')
    now = s.chain()
    row('when its memory is gone meanwhile it stays, with its knobs, and is off', answer[0].startswith('ERR FXC out of memory') and now['Q'][0] == was['Q'][0] and now['Q'][1] == (*was['Q'][1][:2], 0, *was['Q'][1][3:]),
        [answer, now])


def in_scenes(build, row):
    for last in (3, 7):
        p = Board(build)
        ids, want = [p.new('Q', x) for x in ('boost', 'ts9', 'delay')], {}
        for k in range(last + 1):
            want[k] = 1 if k == 2 else k % 2
            p.say(f'FXE {ids[1]} {want[k]}')
            p.say(f'FXP {ids[0]} 0 {k + 1}')
            p.say(f'FXP {ids[2]} 1 {10 + k}')
            p.say(f'SNAPSAVE {k}')
        p.say('SNAP 1')
        answer, _ = p.change(ids[1], 'rat')
        new = made(answer, 'rat')
        p.say(f'FXP {new} 1 66')
        here, seen = p.on(new), {}
        for k in [*range(2, last + 1), 0, 1]:
            p.say(f'SNAP {k}')
            seen[k] = (p.on(new), p.knob(new, 1), p.knob(ids[0]), p.knob(ids[2], 1))
        row(f'{last + 1} scenes: in each the new block is on or off as the old one was, with the knobs it had when another scene was chosen, and the others are as they were',
            here == want[1] and seen == {k: (want[k], 66, k + 1, 10 + k) for k in want}, [seen, want])
        p.say('SNAP 2')
        p.say(f'FXP {new} 1 20')
        p.say('SNAPSAVE 2')
        p.say('SNAP 0')
        p.say('SNAP 2')
        own = [p.knob(new, 1)]
        p.say('SNAP 3')
        row('then each has its own', [*own, p.knob(new, 1)] == [20, 66], own)
    # stored before any scene is chosen, and read again
    q = Board(build)
    ids = [q.new('Q', x) for x in ('boost', 'ts9')]
    for k in (0, 1, 5):
        q.say(f'FXE {ids[1]} {k & 1}')
        q.say(f'SNAPSAVE {k}')
    q.say('SNAP 1')
    answer, _ = q.change(ids[1], 'klon')
    q.say(f'FXP {made(answer, "klon")} 0 71')
    q.setting(harness.G_PRESET, 0)
    q.stored = scenes.record(b'\5' + bytes(1423))
    answer = q.say('PSAVE 0 Replaced')
    loaded = q.load(q.written) if q.written else (None,) * 4
    kept = [(x[6 + 1], struct.unpack_from('<h', x, 22 + 14)[0]) for k, x in enumerate(loaded[2] or ()) if k in (0, 1, 5)]        # the second effect of the preset
    row('stored, and read again: the switch of each scene, and the knob', answer[0].startswith("PSAVE ok 0 'Replaced'") and loaded[0] == 0 and kept == [(0, 71), (1, 71), (1, 71)], [answer, loaded[0], kept])
    # twice without a scene between; a scene that does not know the old block
    r = Board(build)
    ids = [r.new('Q', x) for x in ('boost', 'ts9')]
    r.say(f'FXE {ids[1]} 0')
    r.say('SNAPSAVE 0')
    r.say(f'FXE {ids[1]} 1')
    r.say('SNAPSAVE 1')
    comp = r.new('Q', 'comp')
    b = made(r.change(made(r.change(ids[1], 'rat')[0], 'rat'), 'muff')[0], 'muff')
    c = made(r.change(comp, 'eq')[0], 'eq')
    r.say(f'FXE {c} 0')
    seen = []
    for k in (0, 1):
        r.say(f'SNAP {k}')
        seen.append((r.on(b), r.on(c)))
    row('replaced twice the switch is kept; in a scene that did not know the old block the new one is as it plays', seen == [(0, 0), (1, 0)], seen)
    # its slot is another block's later
    s = Board(build)
    ids = [s.new('Q', x) for x in ('boost', 'ts9')]
    s.say(f'FXE {ids[1]} 0')
    s.say('SNAPSAVE 0')
    s.say(f'FXE {ids[1]} 1')
    s.say('SNAPSAVE 1')
    new = made(s.change(ids[1], 'rat')[0], 'rat')
    s.say(f'FXR {new}')
    again = [s.new('Q', 'chorus') for _ in range(2)]
    s.say('SNAP 0')
    row('a block that is added in its slot later is not taken for it', new in again and [s.on(x) for x in again] == [1, 1], [new, again])


def glide(build, row):
    """A knob on its way, and the other does not fit: the knob is where it was going."""
    out = []
    for sixteen in (False, True):
        p = Board(build)
        old = p.new('Q', 'boost')
        for s in 'PPPPPPPPPPQQQQQ' if sixteen else '':
            p.new(s, 'gate')
        p.say(f'FXP {old} 0 10')
        still = p.mem.read(p.object(old) + 288, 16)
        p.say(f'FXP {old} 0 -20')
        p.run('effect_parameter_lifecycle_parameter_fast_wrapper', old, 0, 10, 10)
        going = sum(p.mem.read(p.where[GLIDES] + 448 * k, 1)[0] != 0 for k in range(8))
        p.room = 3000
        before = p.everything()
        answer, _ = p.change(old, 'cloud')
        after, sound = p.everything(), p.mem.read(p.object(old) + 288, 16)
        if not going or not answer[0].startswith('ERR FXC out of memory') or p.knob(old) != 10:
            out.append([sixteen, going, answer, p.knob(old)])
        if sixteen and sound != still or not sixteen and (after['glides'] != before['glides'] or after['blocks'][:480] != before['blocks'][:480]):
            out.append([sixteen, still.hex(), sound.hex(), differs(before, after)])
    row('a knob that is on its way meanwhile is not lost', not out, out)


def types(build, row):
    p, out = Board(build, 600_000), []
    p.ir()
    names = [x.split()[2] for x in p.say('FXT') if re.match(r'FXT \d+ \S+ cost=', x)]
    ids = [p.new('Q', x) for x in ('boost', 'comp', 'eq')]
    slot, now = ids[1], 'comp'
    for name in names:
        for wanted in (name, 'comp'):
            if wanted == now:
                continue
            before = p.chain()
            answer, sound = p.change(slot, wanted, now=now)
            if sound != ONCE or not replaced(before, p.chain(), slot, made(answer, wanted), wanted) or p.wrong:
                out.append([now, wanted, answer, p.wrong])
                break
            slot, now = made(answer, wanted), wanted
    row(f'every type ({len(names)}) in the place of another, and another in its place', not out and len(names) == 42, out)
    p.clear()
    row('the pool is empty afterwards', not p.taken and not p.wrong, [p.taken, p.wrong])


def types_stay(build, row):
    q, out, whole = Board(build, 600_000), [], 0
    q.ir()
    names = [x.split()[2] for x in q.say('FXT') if re.match(r'FXT \d+ \S+ cost=', x)]
    for name in names:
        slot = q.new('P', name)
        q.room = sum(q.taken.values()) + 500
        was, held, record = q.chain(), dict(q.taken), q.mem.read(q.object(slot), 480)
        answer, _ = q.change(slot, 'cloud' if name != 'cloud' else 'spectral', now=name)
        now = q.mem.read(q.object(slot), 480)
        if answer[0].startswith('FXC'):                              # its memory was enough for the other
            whole += 1
        elif not answer[0].startswith('ERR FXC out of memory') or q.chain() != was or q.taken != held or now[:108] != record[:108]:
            out.append([name, answer, q.taken, held, [i for i in range(480) if now[i] != record[i]]])
        q.room = 600_000
        q.clear()
        if q.taken or q.wrong:
            out.append([name, q.taken, q.wrong])
            q.taken.clear()
    row(f'every type is as it was when a larger one does not fit ({len(names) - whole} of {len(names)})', not out and len(names) - whole > 25, [whole, out[:4]])


PARTS = (words, places, branches, full, processor, impulse, memory, in_scenes, glide, types, types_stay)


def check(build, name):
    rows = []

    def row(text, good, seen=None):
        rows.append({'check': text, 'held': bool(good), 'seen': json.dumps(seen, default=repr)[:900]})

    try:
        next(p for p in PARTS if p.__name__ == name)(build, row)
    except Exception as e:                                           # what a build without the word does
        row(f'{name} ran to its end', False, repr(e)[:400])
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build')
    parser.add_argument('--part', choices=[p.__name__ for p in PARTS], help='only this part')
    a = parser.parse_args(argv)
    rows, parts = [], [p.__name__ for p in PARTS if a.part in (None, p.__name__)]
    with concurrent.futures.ProcessPoolExecutor(2) as pool:
        for part in pool.map(check, [a.build] * len(parts), parts):
            for r in part:
                print('   ok  ' if r['held'] else '   FAIL', r['check'], '' if r['held'] else r['seen'], flush=True)
            rows += part
    print(json.dumps({'held': all(r['held'] for r in rows), 'checks': len(rows), 'hardware_test': False}))
    return 0 if all(r['held'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
