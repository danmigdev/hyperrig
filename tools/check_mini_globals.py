"""The settings for every preset and the calibration of the input, on a built MINI application in the pi32v2 simulator. Offline; no device is opened.

GEQ, HPF, LIM, SPILL, GLIDE, SPUR, CALIB and GSAVE run from the bytes of app.bin, from the console line to the record in a simulated flash, as in
tools/check_mini_library.py. Checked:
- every line that app/mini/mini-dev-rules.js permits is taken by the firmware as it is written, and what the firmware would clamp, pass over or
  refuse is not permitted: the rules run in node, on the same lines;
- the simulated pedal of the page check (tools/simulated_globals.py) answers as the firmware does, line by line;
- GSAVE keeps the values over a restart and what was not saved is gone; nothing but the settings sector is written, also with the power cut at each
  erase and program of a save, and over more saves than a sector holds;
- a stored preset is the same bytes with any of these settings, and reading one leaves them;
- what they do to the sound: the bands of the EQ, the high-pass, the ceiling of the limiter, from the application's own sound code, with the
  instructions each takes, and the room for blocks that the firmware counts for the EQ;
- what CALIB does: the readings of three seconds, the suggestion, its end by itself, and that it changes nothing else.

Shortcuts, for speed: the checksums of data are computed here, and the double arithmetic of the high-pass runs only where its sound is looked at.
This is no hardware or audio test: processor time, the running audio and a real flash are not simulated.

Usage, from the repository root (about ten minutes):
    python -B tools/check_mini_globals.py BUILD
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import cmath
import json
import math
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_library as library  # noqa: E402
import mini_sim as sim  # noqa: E402
import simulated_globals  # noqa: E402

RULES = ROOT / 'app/mini/mini-dev-rules.js'
STATE, SETTINGS, CONTROL, BLOCK = 'L01c26890', 'L01c1f180', 'L01c32db0', 0x01C70000
RATE, TICK, CYCLES = 48077, 6, 2.1            # cycles of a tick; cycles an instruction takes, as in tools/check_mini_effect_block.py
WORDS = ('GEQ', 'HPF', 'LIM', 'SPILL', 'GLIDE', 'SPUR', 'CALIB sens')
DEFAULTS = ['GEQ 0 0 0 0 0', 'HPF hz=55', 'LIM on=1 thr=-3 rel=100 lat=48 samples=0', 'SPILL 1 tails=0', 'GLIDE ms=42 blocks=16 snap=1',
            'SPUR 1 learned=0 blocks slow=0 pattern_rms=0 (Q30)', 'CALIB sens=12.0 dBu at 0 dBFS (GSAVE to keep)']
DOUBLES = ('L02032cda', 'L0203306a', 'L020331ce', 'L02033466', 'L02033776', 'L020337ca', 'L02033816', 'L02033872', 'butterworth_table_fixed_round')


class Pedal(library.Pedal):
    """The library's pedal, with the settings as the start-up code of the application leaves them."""

    quick = True

    def restart(self):
        super().restart()
        del self.services[self.where['calibration_commands_global_save']]
        self.shortcuts()
        if self.quick:
            self.services.update({self.where[n]: self.nothing for n in DOUBLES})
        self.call('dsp_initialization_startup')
        self.call('butterworth_table_butterworth_table', r0=55)
        self.call('settings_load_settings_load')
        self.programmed, self.erased = [], []

    def call(self, name, stop=sim.RETURN, limit=60_000_000, **registers):
        cpu, start = self.cpu, self.cpu.steps
        for register, value in registers.items():
            cpu.R[int(register[1:])] = value & sim.M
        cpu.rets, cpu.pc, cpu.sp = sim.RETURN, self.where[name], sim.STACK_TOP
        stop = self.where.get(stop, stop)
        while cpu.pc != stop:
            service = self.services.get(cpu.pc)
            if service:
                cpu.R[0] = (service(list(cpu.R[:4])) or 0) & sim.M
                cpu.pc = cpu.rets
                continue
            cpu.step()
            if cpu.steps - start > limit:
                raise RuntimeError(f'{name}: too many steps')
        return cpu.steps - start

    def word(self, name, offset, value=None):
        at = self.where[name] + offset
        if value is not None:
            self.cpu.mem.write(at, struct.pack('<i', value))
        return struct.unpack('<i', self.cpu.mem.read(at, 4))[0]

    def settings(self):
        return [self.line(w)[0] for w in WORDS]

    def blocks(self, name, blocks, lead=0, **registers):
        """The sound code of this name over blocks of 128 samples: the samples, and the most instructions a block took."""
        out, most = [], 0
        for b in blocks:
            self.cpu.mem.write(BLOCK + lead, struct.pack('<128i', *b))
            most = max(most, self.call(name, r0=BLOCK, **registers))
            out += struct.unpack('<128i', self.cpu.mem.read(BLOCK, 512))
        return out, most


def node(source, payload):
    done = subprocess.run(['node', '-e', source], input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if done.returncode:
        raise RuntimeError(done.stderr)
    return json.loads(done.stdout)


def permitted(lines, answers):
    """What the rules permit of these lines on a product build that has said the answers; nothing before it has."""
    return node('const i = JSON.parse(require("fs").readFileSync(0, "utf8")); require("vm").runInThisContext(i.rules); const R = globalThis.HyperRigDevRules, p = {version: "1", build_id: "0123456789abcdef"};'
                'R.build(["HRID 1 1 0123456789abcdef banks=3"], p); const s = {}, before = i.lines.filter(x => x.split(" ")[0] !== "CALIB" && x.includes(" ") && R.rule(x, s, p));'
                'for (const [q, a] of i.answers) R.observe(q, [a], s);'
                'console.log(JSON.stringify({before, after: i.lines.map(x => R.rule(x, s, p) === true), other: i.lines.filter(x => R.rule(x, s, null) === true)}));',
                {'rules': RULES.read_text(encoding='utf-8'), 'lines': lines, 'answers': answers})


def simulated(lines):
    """What the simulated pedal of the page check answers to these lines, from the start."""
    return node(simulated_globals.GLOBALS + 'const g = makeGlobals(), live = {gain: 0, trim: 0, level: null, slot: -1, audio: 0};'
                'console.log(JSON.stringify(JSON.parse(require("fs").readFileSync(0, "utf8")).map(x => globalAnswer(g, live, x.split(" ")[0], x.split(" ").slice(1)))));', lines)


def corpus():
    """(line, whether the firmware takes it as it is written) of everything the page can write, and of what lies beside it."""
    lines = [(f'GEQ {b} {v}', 0 <= b <= 4 and -12 <= v <= 12) for b in range(-1, 7) for v in range(-14, 15)]
    lines += [(f'HPF {hz}', hz == 0 or 20 <= hz <= 120 and hz % 5 == 0) for hz in [*range(-1, 2), 5, 15, *range(19, 127), 255, 1000]]
    lines += [(f'LIM {on} {thr} {rel}', on in (0, 1) and -200 <= thr <= 0 and 10 <= rel <= 2000)
              for on in (-1, 0, 1, 2) for thr in (-1000, -201, -200, -100, -60, -30, -20, -10, -5, -3, -1, 0, 1, 30) for rel in (-1, 0, 9, 10, 25, 50, 100, 200, 500, 1000, 2000, 2001)]
    lines += [(f'{w} {v}', v in (0, 1)) for w in ('SPILL', 'SPUR') for v in (-1, 0, 1, 2)]
    lines += [(f'GLIDE {ms} {snap}', 0 <= ms <= 170 and snap in (0, 1)) for ms in (-1, 0, 1, 42, 43, 101, 169, 170, 171, 255) for snap in (-1, 0, 1, 2)]
    return lines


# Other spellings, words without all their numbers, and what stays blocked: some of it the firmware would take.
SPELLINGS = ['GEQ 0', 'GEQ 0 +3', 'GEQ 0 03', 'GEQ 0 -0', 'GEQ 00 1', 'GEQ 0  1', 'GEQ 0 1 ', 'GEQ 0 1 2', 'GEQ 0 1x', 'GEQ x 1', 'geq 0 1', 'HPF 055', 'HPF +55', 'HPF 55 ', 'HPF 55 1', 'HPF x',
             'HPF 5e1', 'LIM 1', 'LIM 1 -3', 'LIM 1 -3 100 1', 'LIM 01 -3 100', 'LIM 1 -03 100', 'LIM 1 -0 100', 'LIM 1 -3 0100', 'LIM on', 'SPILL', 'SPILL on', 'SPILL 01', 'SPUR 01', 'SPUR 1 1',
             'GLIDE 42', 'GLIDE 042 1', 'GLIDE 42 1 1', 'CALIB', 'CALIB status', 'CALIB 1', 'CALIB start now', 'CALIB sens', 'CALIB sens 12.0', 'CALIB sens -10', 'CALIB sens 31', 'GSAVE all', 'NOISE 1000']


def taken(line, answer, before):
    """The firmware took the line as it is written."""
    word, *n = line.split(' ')
    n, got = [int(x) for x in n], answer[0]
    if word == 'GEQ':
        want = list(before)
        if len(n) != 2 or not 0 <= n[0] <= 4:
            return False
        want[n[0]] = n[1]
        return got == 'GEQ ' + ' '.join(map(str, want))
    if word == 'GLIDE':                       # in blocks of 2.66 ms
        m = re.fullmatch(r'GLIDE ms=(\d+) blocks=(\d+) snap=([01])', got)
        return bool(m) and abs(int(m[1]) - n[0]) <= 3 and int(m[3]) == n[1]
    return bool({'HPF': lambda: got == f'HPF hz={n[0]}', 'LIM': lambda: re.fullmatch(rf'LIM on={n[0]} thr={n[1]} rel={n[2]} lat=48 samples=\d+', got),
                 'SPILL': lambda: got == f'SPILL {n[0]} tails=0', 'SPUR': lambda: got.startswith(f'SPUR {n[0]} ')}[word]())


def check_lines(build, flash, row):
    pedal = Pedal(build, flash)
    mark, at_first = bytes(flash), pedal.settings()
    row('what the firmware starts with, with no settings stored', at_first == DEFAULTS, at_first)
    lines = corpus()
    questions = [(w, pedal.line(w)[0]) for w in WORDS[:6]]
    ruled = permitted([x for x, _ in lines] + SPELLINGS, questions)
    row('nothing is permitted before the pedal has said what it has, and nothing on another build', ruled['before'] == [] and ruled['other'] == [], [ruled['before'][:5], ruled['other'][:5]])
    wrong, all_answers, written = [], [], 0
    for (line, want), rule in zip(lines, ruled['after']):
        before = [int(x) for x in pedal.line('GEQ')[0].split()[1:]] if line.startswith('GEQ') else None
        answer = pedal.line(line)
        all_answers.append(answer)
        written += len(pedal.programmed) + len(pedal.erased)
        good = len(answer) == 1 and not answer[0].startswith('ERR') and taken(line, answer, before)
        if not good == want == rule:
            wrong.append([line, answer, {'firmware': good, 'expected': want, 'rules': rule}])
    row('the rules permit a line exactly when the firmware takes it as it is written', not wrong, wrong[:8] or {'lines': len(lines), 'permitted': sum(ruled['after'])})
    others = [x for x, rule in zip(SPELLINGS, ruled['after'][len(lines):]) if rule]
    row('no other spelling is permitted, and no word that stays blocked', others == [], others or len(SPELLINGS))
    row('CALIB start and stop, and only they', permitted(['CALIB start', 'CALIB stop'], questions)['after'] == [True, True], None)
    again = []
    for ms in range(171):                     # the page writes back the time the pedal has said
        said = int(re.search(r'ms=(\d+)', pedal.line(f'GLIDE {ms} 1')[0])[1])
        if pedal.line(f'GLIDE {said} 0')[0].split()[1] != f'ms={said}' or said > 170:
            again.append(ms)
    row('the time of GLIDE that the pedal has said is taken back as it is', not again, again)
    row('none of these lines writes the flash', written == 0 and bytes(flash) == mark, written)
    # the simulated pedal of the page check: the same answers, all of the above and what is not a line of the page, from a fresh start
    pedal.restart()
    both = [x for x, _ in lines] + ['GEQ 0', 'GEQ', 'GEQ 1 3 4', 'HPF x', 'HPF 55 x', 'LIM 1', 'LIM 1 -5', 'LIM 0', 'LIM', 'LIM x', 'SPILL', 'SPILL x', 'SPUR x', 'GLIDE 42', 'GLIDE', 'GLIDE x', 'CALIB', 'CALIB stop',
                                  'CALIB start', 'CALIB xx', 'CALIB start now', 'CALIB sens', 'CALIB sens 12.5', 'CALIB sens 30', 'CALIB sens 30.1', 'CALIB sens -10', 'CALIB sens -10.1', 'CALIB', 'GSAVE', 'GSAVE', 'GSAVE']
    real, ours = [pedal.line(x) for x in both], simulated(both)
    page = lambda answer: [re.sub(r'slot=[0-9]+', 'slot=N', x) for x in answer]      # the first save writes the page of the lights and MIDI too, so the numbers are one apart
    differ = [[x, a, b] for x, a, b in zip(both, real, ours) if page(a) != page(b)]
    row("the simulated pedal of the page check answers as the firmware", not differ, differ[:8] or len(both))


NEW = ['GEQ 0 6', 'GEQ 1 -4', 'GEQ 2 12', 'GEQ 3 -12', 'GEQ 4 1', 'HPF 80', 'LIM 0 -60 500', 'SPILL 0', 'GLIDE 101 0', 'SPUR 0', 'FSA 2 0 7 0 255']
KEPT = ['GEQ 6 -4 12 -12 1', 'HPF hz=80', 'LIM on=0 thr=-60 rel=500 lat=48 samples=0', 'SPILL 0 tails=0', 'GLIDE ms=101 blocks=38 snap=0',
        'SPUR 0 learned=0 blocks slow=0 pattern_rms=0 (Q30)', DEFAULTS[6]]


def check_saving(build, flash, row):
    pedal = Pedal(build, flash)
    inside = (library.SETTINGS, library.USER_END)
    for line in NEW:
        pedal.line(line)
    pedal.restart()
    row('what is not saved is gone after a restart', pedal.settings() == DEFAULTS, pedal.settings())
    for line in NEW:
        pedal.line(line)
    mark = bytes(flash)
    answer = pedal.line('GSAVE')
    wrote = list(pedal.programmed)
    # the area was not HyperRig's: the first save makes it its own
    row('GSAVE says so, and writes nothing but the settings sector', bool(re.fullmatch(r'GSAVE ok slot=\d+/30', answer[0])) and len(answer) == 1 and all(inside[0] <= a < inside[1] for a, _ in wrote) and
        all(a == inside[0] for a in pedal.erased) and not library.outside(flash, mark, inside), [answer, wrote, pedal.erased])
    pedal.restart()
    row('after a restart everything saved is there, with the footswitches', pedal.settings() == KEPT and 'FSA 2 0 7 0 255' in pedal.line('FSA'), [pedal.settings(), pedal.line('FSA')[6:9]])
    # a change that is not saved, and another save
    for line in ('GEQ 0 -1', 'LIM 1 -3 100'):
        pedal.line(line)
    pedal.restart()
    row('a change after the save that is not saved is gone, the saved ones stay', pedal.settings() == KEPT, pedal.settings())

    def cut(stored, old):
        """The power cut at each operation of a save over this flash: how often the settings are then the old, the new or the first ones."""
        new, found = ['GEQ -7 -4 12 -12 1', 'HPF hz=25', *old[2:]], []
        for at in range(1, 60):
            trial = Pedal(build, bytearray(stored))
            for line in ('GEQ 0 -7', 'GEQ 1 -4', 'GEQ 2 12', 'GEQ 3 -12', 'GEQ 4 1', 'HPF 25'):
                trial.line(line)
            trial.cut_at, trial.operations = at, 0
            try:
                trial.line('GSAVE')
                return found
            except library.PowerCut:
                trial.restart()
            now = trial.settings()
            found.append('old' if now == old else 'new' if now == new else 'first' if now == DEFAULTS else now)
            if library.outside(trial.flash, stored, inside):
                found.append('outside')
        return found + ['no end']

    seen = cut(bytes(flash), KEPT)
    row('power cut at each operation of a save: the old settings or the new ones', seen and set(seen) <= {'old', 'new'}, seen)
    # more saves than a sector holds
    erased, refused, full, previous = 0, [], None, KEPT
    mark = bytes(flash)
    for k in range(70):
        pedal.line(f'GEQ {k % 5} {k % 25 - 12}')
        before, answer = bytes(flash), pedal.line('GSAVE')
        if pedal.erased and full is None:
            full = before, previous
        erased += len(pedal.erased)
        if not answer[0].startswith('GSAVE ok') or any(a != inside[0] for a in pedal.erased) or any(not inside[0] <= a < inside[1] for a, _ in pedal.programmed):
            refused.append([k, answer, pedal.erased])
        last = previous = pedal.settings()
    pedal.restart()
    row('seventy saves: a page each, the sector is erased when its thirty are used', not refused and 1 <= erased <= 4 and not library.outside(flash, mark, inside), refused or {'erased': erased})
    row('and the last one is what is read', pedal.settings() == last and last[0] != KEPT[0] and last[1:] == KEPT[1:], pedal.settings())
    # the firmware has one sector for them: with the power cut while that one is erased and written again, it starts as a new one, as it does for the footswitches
    seen = cut(*full)
    row('power cut while the sector is rewritten, one save in thirty: old, new or first settings, and nothing outside the sector', len(seen) >= 2 and set(seen) <= {'old', 'new', 'first'},
        {k: seen.count(k) for k in ('old', 'new', 'first')} if set(seen) <= {'old', 'new', 'first'} else seen)


def check_presets(build, flash, row):
    import check_mini_scenes as scenes
    p = scenes.Pedal(build)
    p.setting(scenes.harness.G_PRESET, 0)
    p.setting(88, -1)
    p.wipe()
    slots = [p.add(2), p.add(8)]
    p.stored = scenes.record(b'\5' + bytes(1423))
    plain, records = [], []
    for change in ([], ['GEQ 0 12', 'GEQ 3 -5', 'LIM 0 -100 10', 'SPILL 0', 'GLIDE 10 0', 'SPUR 0']):
        for line in change:
            plain.append(p.say(line)[0])
        answer = p.say('PSAVE 0 Same')
        records.append((answer[0].startswith("PSAVE ok 0 'Same'"), p.written[40:]))
    said = [p.say(w)[0] for w in ('GEQ', 'LIM', 'SPILL', 'GLIDE', 'SPUR')]
    row('a preset is stored with the same bytes, whatever these settings are', slots == [0, 1] and all(ok for ok, _ in records) and records[0][1] == records[1][1], [slots, plain, len(records[0][1])])
    load = p.load(p.stored)
    row('reading a preset and its scenes leaves them', load[0] == 0 and [p.say(w)[0] for w in ('GEQ', 'LIM', 'SPILL', 'GLIDE', 'SPUR')] == said and said[0] == 'GEQ 12 0 0 -5 0', said)


def level(samples, hz, full):
    w = -2j * math.pi * hz / RATE
    return 20 * math.log10(abs(sum(x * cmath.exp(w * i) for i, x in enumerate(samples) if x)) / full + 1e-12)


def check_sound(build, flash, row):
    Pedal.quick = False
    try:
        pedal = Pedal(build, flash)
    finally:
        Pedal.quick = True
    pedal.word('L01c34198', 0, 0)                  # no clock: the firmware then counts its own cost of a band
    silence, full = [[0] * 128] * 30, 1 << 24
    impulse = [[full] + [0] * 127] + [[0] * 128] * 23
    noise = [[((k * 7919 + i * 104729) * 65537 & 0xFFFFFFF) - 0x8000000 for i in range(128)] for k in range(3)]
    out, flat = pedal.blocks('biquad_chain_process', noise, r1=128)
    row('a flat EQ changes no sample', out == [x for b in noise for x in b], flat)
    seen, most, wrong = {}, {}, []

    def set_bands(values):
        for b, v in enumerate(values):
            pedal.line(f'GEQ {b} {v}')
        pedal.blocks('biquad_chain_process', silence, r1=128)

    def ideal(band, gain, hz):
        """The filters of the EQ as their method describes them: low shelf, three bells of Q 0.9, high shelf."""
        f = (100, 400, 1200, 3200, 7000)[band]
        a, w0 = 10 ** (gain / 40), 2 * math.pi * f / RATE
        s, c, z = math.sin(w0), math.cos(w0), cmath.exp(-2j * math.pi * hz / RATE)
        if 0 < band < 4:
            alpha = s / 1.8
            b0, b1, b2, a0, a1, a2 = 1 + alpha * a, -2 * c, 1 - alpha * a, 1 + alpha / a, -2 * c, 1 - alpha / a
        else:
            sign, beta = (1 if band else -1), 2 * math.sqrt(a) * s / 2 * math.sqrt(2)
            b0, b1, b2 = a * ((a + 1) + sign * (a - 1) * c + beta), -sign * 2 * a * ((a - 1) + sign * (a + 1) * c), a * ((a + 1) + sign * (a - 1) * c - beta)
            a0, a1, a2 = (a + 1) - sign * (a - 1) * c + beta, sign * 2 * ((a - 1) - sign * (a + 1) * c), (a + 1) - sign * (a - 1) * c - beta
        return 20 * math.log10(abs((b0 + b1 * z + b2 * z * z) / (a0 + a1 * z + a2 * z * z)))

    for band in range(5):
        for gain in (12, -12, 3):
            set_bands([gain if b == band else 0 for b in range(5)])
            out, steps = pedal.blocks('biquad_chain_process', impulse, r1=128)
            most[band] = max(steps, most.get(band, 0))
            for hz in (50, 100, 400, 1200, 3200, 7000, 12000):
                got = level(out, hz, full)
                if abs(got - ideal(band, gain, hz)) > 0.25:
                    wrong.append([band, gain, hz, round(got, 2), round(ideal(band, gain, hz), 2)])
            seen[f'{band} {gain:+d}'] = [round(level(out, hz, full), 1) for hz in (100, 400, 1200, 3200, 7000)]
    row('the five bands: a low shelf at 100 Hz, bells at 400, 1200 and 3200 Hz, a high shelf at 7000 Hz, within 0.25 dB', not wrong, wrong[:6] or seen)
    set_bands([12, -12, 12, -12, 12])
    pedal.cpu.mem.write(pedal.where['L01c34488'], b'\1')
    _, five = pedal.blocks('biquad_chain_process', impulse[:3], r1=128)
    mono = pedal.cpu.mem.read(pedal.where['L01c34488'], 1) == b'\0'
    set_bands([0] * 5)
    pedal.cpu.mem.write(pedal.where['L01c34488'], b'\1')
    pedal.blocks('biquad_chain_process', impulse[:3], r1=128)
    row('with a band in use the sound is one channel, flat it keeps two', mono and pedal.cpu.mem.read(pedal.where['L01c34488'], 1) == b'\1', None)
    ticks = round(five * CYCLES / TICK)
    row('instructions of a block: none of it flat, 1800 to 2100 for a band, about 9000 for five', flat < 40 and max(most.values()) < 2200 and five < 9500,
        {'flat': flat, 'bands': most, 'five': five, 'ticks of five, estimated': ticks})
    # the room for blocks
    pedal.word(CONTROL, 48, 22700)
    load = lambda: int(re.search(r'cpu=(\d+)/22700', next(x for x in pedal.line('FXS') if 'cpu=' in x))[1])
    counted = [load()]
    for b in range(5):
        pedal.line(f'GEQ {b} 6')
        counted.append(load())
    steps = [b - a for a, b in zip(counted, counted[1:])]
    row('the firmware counts 580 of 22,700 ticks, about 3 % of the room for blocks, for a band, and 55 more for the first', counted[0] == 0 and steps[0] == 635 and steps[1:] == [580] * 4, [counted, steps])
    pedal.word(CONTROL, 48, 2300)
    answers = [pedal.line(x)[0] for x in ('FXA Q 99 boost', 'GEQ 0 0', 'GEQ 1 0', 'FXA Q 99 boost', 'GEQ 0 3', 'GEQ 1 3', 'FXE 0 0', 'FXE 0 1')]
    row('a block without room is refused; a band is not, so the editor looks first', answers[0] == 'ERR FXA not enough CPU' and answers[3].startswith('FXA id=') and answers[4:6] == ['GEQ 3 0 6 6 6', 'GEQ 3 3 6 6 6'] and
        answers[7] == 'ERR FXE not enough CPU', answers)
    # the high-pass
    impulse = [[1 << 26] + [0] * 127] + [[0] * 128] * 99
    heard = {}
    for hz in (0, 20, 55, 120):
        pedal.line(f'HPF {hz}')
        pedal.blocks('switched_high_pass_switch', [[0] * 128] * 70)            # it glides there in 64 blocks
        out, steps = pedal.blocks('switched_high_pass_switch', impulse)
        heard[hz] = [round(level(out, f, 1 << 26), 2) for f in (hz / 2 or 27, hz or 55, 440)] + [steps]
    row('the high-pass: 3 dB less at its frequency, 24 an octave under it, nothing at 440 Hz; off it does nothing', heard[0][:3] == [0, 0, 0] and all(abs(heard[hz][1] + 3) < 0.15 and -25.5 < heard[hz][0] < -23 and abs(heard[hz][2]) < 0.1 for hz in (20, 55, 120)), heard)
    # the limiter: full scale is 2^26 here
    loud = [[int((1 << 27) * math.sin(2 * math.pi * 220 * (128 * k + i) / RATE)) for i in range(128)] for k in range(8)]
    held = {}
    for thr, rel in ((0, 100), (-3, 100), (-60, 50), (-200, 10)):
        pedal.line(f'LIM 1 {thr} {rel}')
        pedal.call('dsp_dynamics_processing_reset')
        out, steps = pedal.blocks('dsp_dynamics_processing_single', loud, lead=192, r1=65536)
        held[thr] = [round(20 * math.log10(max(abs(x) for x in out[384:]) / (1 << 26)), 2), steps]
    row('the limiter holds its ceiling, with a sound of twice full scale', all(abs(v[0] - thr / 10) < 0.02 for thr, v in held.items()), held)
    pedal.line('LIM 1 -3 100')
    pedal.call('dsp_dynamics_processing_reset')
    soft = [[x >> 6 for x in b] for b in loud]
    out, steps = pedal.blocks('dsp_dynamics_processing_single', soft, lead=192, r1=65536)
    row('a sound under the ceiling goes through as it is, 48 samples later', out[176:640] == [x for b in soft for x in b][128:592], steps)


def check_calibration(build, flash, row):
    pedal = Pedal(build, flash)
    mark, cpu = bytes(flash), pedal.cpu
    state, settings = pedal.where[STATE], pedal.where[SETTINGS]
    refused = pedal.line('CALIB start')
    row('without the audio it does not start', refused == ['ERR CALIB audio engine is not running (AUDIO A2L first)'], refused)
    pedal.word(STATE, 280, 2)
    pedal.word(SETTINGS, 24, 1000)

    def poll():
        pedal.lines = []
        pedal.call('L02018456', stop='L020184a8', r14=state, r15=pedal.where['L02035810'], r9=0)
        return list(pedal.lines)

    def listen(db, blocks=1125):
        """What the audio block does with the input while it listens: three seconds are 1125 blocks."""
        top = (1 << 30) * 10 ** (db / 20)
        cpu.mem.write(BLOCK, struct.pack('<128i', *[int(top * (-1) ** (i & 1)) for i in range(128)]))
        for _ in range(blocks):
            pedal.call('L01c021ec', stop='L01c0223c', r8=state, r9=BLOCK, r10=0, r15=settings)

    was = cpu.mem.read(settings, 1632), pedal.settings()
    live = cpu.mem.read(state, 16000)
    first = pedal.line('CALIB start')
    row('it starts, and says so', first == ['CALIB running=1 win=0 gain=0 sens=12.0 target=-18.0 suggest=none trim=0.0 slot=-1'], first)
    listen(-20, 1124)
    row('a reading is three seconds of the input', poll() == [], None)
    listen(-20, 1)
    heard = [poll()]
    for db in (-12, -30):
        listen(db)
        heard.append(poll())
    row('each reading is told by itself: its peak, its level, the loudest so far, and the trim that brings it to the target',
        heard == [['CALIB running=1 win=1 peak=-20.0 rms=-20.0 hold=-20.0 gain=0 sens=12.0 target=-18.0 suggest=+2.0 trim=0.0 slot=-1'],
                  ['CALIB running=1 win=2 peak=-12.0 rms=-12.0 hold=-12.0 gain=0 sens=12.0 target=-18.0 suggest=-6.0 trim=0.0 slot=-1'],
                  ['CALIB running=1 win=3 peak=-30.0 rms=-30.0 hold=-12.0 gain=0 sens=12.0 target=-18.0 suggest=-6.0 trim=0.0 slot=-1']], heard)
    row('and nothing is told twice', poll() == [], None)
    now = cpu.mem.read(state, 16000)
    changed = {k for k in range(16000) if now[k] != live[k]}
    own = {6, 17} | set(range(284, 292)) | set(range(748, 776)) | set(range(1600, 1608)) | set(range(1944, 1964)) | set(range(8728, 9240)) | {948, 949, 950, 951}
    row('it changes nothing but what it counts', changed <= own and (cpu.mem.read(settings, 1632), pedal.settings()) == was and bytes(flash) == mark and pedal.line('GAIN') == ['GAIN in=0 out=0 dB'],
        sorted(changed - own)[:20])
    pedal.line('GAIN 4 0')
    with_gain = pedal.line('CALIB status')
    row('the input gain of the preset is counted in', 'gain=4' in with_gain[0] and 'suggest=-10.0' in with_gain[0], with_gain)
    stopped = pedal.line('CALIB stop')
    listen(-1)
    row('stopped, it listens no more, and keeps what it found', stopped[0].startswith('CALIB running=0 win=3') and poll() == [] and pedal.line('CALIB status') == stopped, stopped)
    pedal.line('CALIB start')
    pedal.word(SETTINGS, 24, 19000)
    late = poll()
    pedal.word(SETTINGS, 24, 19001)
    row('after three minutes it stops by itself, also when nobody asks', [late, poll()] == [[], ['ERR CALIB stopped (timeout)']] and pedal.line('CALIB')[0].startswith('CALIB running=0'), late)
    pedal.line('CALIB start')
    pedal.word(STATE, 280, 0)
    row('and when the audio stops', poll() == ['ERR CALIB stopped (audio stopped)'], None)
    # the simulated pedal of the page check, over the same readings
    ours = node(simulated_globals.GLOBALS + 'const g = makeGlobals(), live = {gain: 0, trim: 0, level: null, slot: -1, audio: 2}, out = [globalAnswer(g, live, "CALIB", ["start"])[0]];'
                'for (const p of [-200, -120, -300]) out.push(calibWindow(g, live, p, p)); live.gain = 4; out.push(globalAnswer(g, live, "CALIB", ["status"])[0], globalAnswer(g, live, "CALIB", ["stop"])[0]);'
                'console.log(JSON.stringify(out));', None)
    row('the simulated pedal of the page check tells the same', ours == first + [x[0] for x in heard] + with_gain + stopped, [a for a, b in zip(ours, first + [x[0] for x in heard] + with_gain + stopped) if a != b])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--only', choices=('lines', 'saving', 'presets', 'sound', 'calibration'))
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})
        print('   ok  ' if good else '   FAIL', name, '' if good else json.dumps(seen, default=repr)[:900], flush=True)

    flash = library.foreign_flash()
    flash[library.SETTINGS:library.USER_END] = b'\xff' * library.SECTOR          # no settings stored: the other firmware's are in other checks
    for name, part in (('lines', check_lines), ('saving', check_saving), ('presets', check_presets), ('sound', check_sound), ('calibration', check_calibration)):
        if args.only in (None, name):
            part(args.build, bytearray(flash), row)
    held = all(r['held'] for r in rows)
    print(json.dumps({'kind': 'mini-globals-check', 'build': args.build.name, 'hardware_test': False, 'held': held, 'checks': rows}, default=repr))
    return 0 if held else 1


if __name__ == '__main__':
    raise SystemExit(main())
