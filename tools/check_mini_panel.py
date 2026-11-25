"""Press the switches of a built MINI application in the pi32v2 simulator and check what it does with them. Offline.

The application's own switch scan and switch event run from the bytes of app.bin, in the factory layout: presses, holds
and pairs of the three switches, with their times. What lies behind them is replaced by recorders: the preset store (which
presets there are), loading and saving a preset, the Bluetooth calls, the notifications to the editor. The console line
handler runs too, with the application's own formatting, up to the send of the line. So does the part of the control scan
that watches two switches held for Bluetooth, and, in a product build, the turn that reads the volume wheel and the battery,
with the converter's answers given.

Two descriptions are checked, the one the build manifest names:
- a product build (tools/build_hyperrig_mini_image.py --product): banks of three, A+B the bank before and B+C the next, as
  printed on the TANK-MINI, A+B held Bluetooth (2.5 s on and pairing, 6 s off), B+C held the tuner, the wheel the volume,
  the battery, HRID, HRST and STAGE on the console, the last up to the restart into the loader;
- the MINI v4 application: banks of four, A+B the bank before, B+C preset or live mode, B+C held the tuner and Bluetooth,
  no HRID.

This is no hardware test: the pins, the debounce and the time base of the pedal are not simulated.

Usage, from the repository root:
    python -B tools/check_mini_panel.py BUILD [BUILD ...]
BUILD is an output directory of tools/build_hyperrig_mini_image.py. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/pi32v2-isa'), str(ROOT / 'upstream/pi32v2-isa/tools/llvm'),
                str(ROOT / 'upstream/pi32v2-isa/tools/hwtest')]
import build_mini_stage  # noqa: E402
import mini_sim as sim  # noqa: E402
from hyperrig.jieli import crc16  # noqa: E402
from pi32v2isa import codec  # noqa: E402

BASE, RAM = 0x02000120, 0x01C00000
STATE, SETTINGS = 'L01c26890', 'L01c1f180'
SCAN, LINE = 'panel_inputs_switch_scan', 'tuner_and_control_records_console_line'
# Services of the switch event and of the console line: recorded, with what they answer.
RECORDED = {'preset_storage_available': None, 'storage_coordination_notify': 0, 'preset_loader_load': 0,
            'footswitch_events_preset_save': 0, 'panel_inputs_event_queue': 0, 'console_helpers_ble_advertise': 0,
            'console_helpers_ble_drop': 0, 'footswitch_events_reload_preset': 0, 'slot_commands_enable_command': 0,
            'preset_application_effect_type': 0, 'preset_application_effect_enabled': 0, 'slot_commands_requested': 0,
            'preset_band_controls_request_reserve': 0, 'panel_inputs_change_mark': 0, 'panel_inputs_change_check': 0,
            'record_helpers_pack_tag': 0, 'text_commands_text_command': 0, 'console_commands_console_command': 0,
            'calibration_commands_global_save': 0, 'console_dispatch_console_dispatch': 0, 'link_and_print_send_line': 0,
            'storage_coordination_irq_enter': 0, 'storage_coordination_irq_leave': 0, 'console_helpers_key_open': 0,
            'console_helpers_now_ms': None, 'L0204c744': 0, 'footswitch_events_adc_read': None, 'phase3_p5_gpio_set_die': 0,
            'L02004ad6': 0, 'phase3_p5_gpio_set_pull_up': 0, 'phase3_p5_gpio_set_pull_down': 0,
            'phase3_p8_norflash_read': None, 'L0203feb8': 0}
HOLD, HOLD_END = 'L02015b6c', 'L02015cba'    # in the control scan: two switches held, for Bluetooth
TURN = 'hyperrig_panel_turn'
S_TUNER, S_LAYOUT, S_MODE, S_BANK, S_BYPASS, S_LINK, S_SCAN_ON, S_LEVEL = 52, 74, 75, 76, 77, 82, 280, 1567
S_BLE_READY, S_BLE_OFF, S_FLASH_GOOD, S_FLASH_TIME = 60, 1536, 49, 920
G_PRESET, G_FLASH_SWITCH, G_VOLUME_ON, G_VOLUME = 92, 13, 14, 36
WHEEL, BATTERY = 8, 6                        # converter channels
A, B, C = 0, 1, 2


class Panel:
    """One application in the simulator, its memory as the start-up code leaves it."""

    def __init__(self, app, layout, where):
        self.where, self.app, self.layout = where, app, layout
        self.cpu = sim.CPU()
        self.cpu.mem.write(BASE, app)
        self.reset()

    def reset(self, presets=range(32)):
        at = int(self.layout['ram_image_load'], 16) - BASE
        self.cpu.mem.write(RAM, self.app[at:at + self.layout['ram_image_size']])
        self.cpu.mem.write(int(self.layout['bss_start'], 16), bytes(self.layout['bss_size']))
        self.cpu.cache = {k: v for k, v in self.cpu.cache.items() if k >= BASE}
        self.presets, self.calls, self.lines, self.now = set(presets), [], [], 10_000
        self.flash, self.restarted = b'', False
        self.cpu.mem.write(0x10000, bytes(4))
        self.cpu.mem.write(0x01C7FD80, b'\xa5' * 96)
        self.analog = {}
        self.byte(STATE, S_MODE, 0)
        self.cpu.mem.write(self.where[STATE] + S_SCAN_ON, b'\1\0\0\0')
        self.cpu.mem.write(self.where[SETTINGS] + G_PRESET, b'\0\0\0\0')

    def byte(self, base, offset, value=None):
        address = self.where[base] + offset
        if value is not None:
            self.cpu.mem.write(address, bytes([value]))
        return self.cpu.mem.read(address, 1)[0]

    def text(self, address):
        out = b''
        while len(out) < 400:
            c = self.cpu.mem.read(address + len(out), 1)
            if c == b'\0':
                break
            out += c
        return out.decode('ascii')

    def run(self, name, args, limit=400_000, stop=sim.RETURN):
        cpu, names = self.cpu, {self.where[n]: n for n in RECORDED if n in self.where}
        cpu.R[:len(args)] = [a & sim.M for a in args]
        cpu.rets, cpu.pc, start = sim.RETURN, self.where[name], cpu.steps
        cpu.sp = sim.STACK_TOP
        while cpu.pc != stop:
            service = names.get(cpu.pc)
            if service:
                a = cpu.R[:4]
                answer = RECORDED[service]
                if service == 'preset_storage_available':
                    answer = int(a[0] in self.presets)
                elif service == 'phase3_p8_norflash_read':
                    cpu.mem.write(a[0], bytes(self.flash[a[2]:a[2] + a[1]]))
                    answer = a[1]
                elif service == 'link_and_print_send_line':
                    self.lines.append(cpu.mem.read(a[0], a[1]).decode('ascii'))
                elif service == 'console_helpers_now_ms':
                    answer = self.now
                elif service == 'footswitch_events_adc_read':
                    value = self.analog.get(a[0])
                    answer = int(value is not None)
                    if answer:
                        cpu.mem.write(a[3], value.to_bytes(4, 'little'))
                elif service == 'console_dispatch_console_dispatch':
                    self.calls.append((service, self.text(a[0]), self.text(a[1])))
                elif service == 'preset_loader_load':
                    cpu.mem.write(self.where[SETTINGS] + G_PRESET, (a[0] & sim.M).to_bytes(4, 'little'))
                    answer = 1
                if service not in ('preset_storage_available', 'console_dispatch_console_dispatch'):
                    self.calls.append((service, a[0], a[1], a[2]))
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
            if int.from_bytes(cpu.mem.read(0x10000, 4), 'little') & 0x10:
                self.restarted = True
                return None
            if cpu.steps - start > limit:
                raise RuntimeError(f'{name}: too many steps')
        return cpu.R[0]

    # the panel
    def hold(self, switches, ms, step=10):
        """Keep the given switches pressed (and the others free) for ms milliseconds."""
        for index in range(3):
            self.byte(STATE, S_LEVEL + index, int(index in switches))
        for _ in range(max(1, ms // step)):
            self.now += step
            self.run(SCAN, [step, 0, self.now])

    def press(self, *switches, ms=120, gap=20):
        """Press the switches one after the other, gap apart, keep them, and release them."""
        for count in range(1, len(switches)):
            self.hold(switches[:count], gap)
        self.hold(switches, ms)
        self.hold((), 60)

    def hold_for_bluetooth(self, switches, ms, step=10):
        """The part of the control scan that watches two switches held, turn after turn."""
        for index in range(3):
            self.byte(STATE, S_LEVEL + index, int(index in switches))
        for _ in range(ms // step):
            self.now += step
            cpu = self.cpu
            cpu.R[13], cpu.R[14], cpu.R[11] = self.where[STATE], self.where[SETTINGS], self.now
            cpu.mem.write(sim.STACK_TOP + 36, step.to_bytes(4, 'little'))
            self.run(HOLD, [], stop=self.where[HOLD_END])

    def turns(self, count, step=10):
        for _ in range(count):
            self.now += step
            self.run(TURN, [self.now])

    def word(self, base, offset):
        return int.from_bytes(self.cpu.mem.read(self.where[base] + offset, 4), 'little')

    def took(self, service):
        return [c for c in self.calls if c[0] == service]

    def console(self, line):
        at = 0x01C70800
        self.cpu.mem.write(at, line.encode('ascii') + b'\0')
        self.run(LINE, [at], limit=3_000_000)


def check(panel, product, identity):
    """The list of (name, held, what happened) of the checks."""
    rows = []

    def row(name, good, seen):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})

    per, banks = (3, 11) if product else (4, 8)
    # a tap loads the preset of the bank
    loads = {}
    for bank in range(banks):
        for switch in (A, B, C):
            panel.reset()
            panel.cpu.mem.write(panel.where[SETTINGS] + G_PRESET, (0xFFFFFFFF).to_bytes(4, 'little'))
            panel.byte(STATE, S_BANK, bank)
            panel.press(switch)
            loads[bank, switch] = [c[1] for c in panel.took('preset_loader_load')]
    wanted = {(b, s): [b * per + s] if b * per + s < 32 else [] for b in range(banks) for s in (A, B, C)}
    row(f'a tap loads the preset of its bank of {per}', loads == wanted,
        {f'{b + 1}{"ABC"[s]}': v for (b, s), v in loads.items() if v != wanted[b, s]})
    # pairs
    for name, pair, step in (('A+B the bank before', (A, B), -1), ('B+A the bank before', (B, A), -1),
                             ('B+C the next bank', (B, C), 1), ('C+B the next bank', (C, B), 1)):
        went = []
        for bank in range(banks):
            panel.reset()
            panel.byte(STATE, S_BANK, bank)
            panel.press(*pair)
            went.append((panel.byte(STATE, S_BANK), panel.byte(STATE, S_MODE), len(panel.took('footswitch_events_preset_save'))))
        if product or step < 0:
            row(name, went == [((b + step) % banks, 0, 0) for b in range(banks)], went)
        else:
            # v4: B+C changes between preset and live mode, and takes the bank of the preset (0) back
            row(name.replace('the next bank', 'preset or live mode'), all(w[1] == 1 for w in went), went)
    panel.reset()
    panel.press(A, C)
    row('A and C together are no pair', panel.byte(STATE, S_BANK) == 0 and panel.byte(STATE, S_TUNER) == 0,
        [c[:2] for c in panel.calls if c[0].startswith('preset_loader')])
    # a hold saves
    saves = {}
    for bank in range(banks):
        for switch in (A, B, C):
            panel.reset()
            panel.byte(STATE, S_BANK, bank)
            panel.press(switch, ms=1200)
            saves[bank, switch] = [c[1] & 0xFFFFFFFF for c in panel.took('footswitch_events_preset_save')]
    row('a switch held a second saves to the preset of its bank',
        all(v == [b * per + s] for (b, s), v in saves.items()), {f'{b}{s}': v for (b, s), v in saves.items() if v != [b * per + s]})
    # pairs held
    panel.reset()
    panel.press(B, C, ms=1200)
    tuner = panel.byte(STATE, S_TUNER)
    saved = len(panel.took('footswitch_events_preset_save'))
    panel.press(A)
    row('B+C held a second opens the tuner, a tap closes it, nothing is saved',
        (tuner, saved, panel.byte(STATE, S_TUNER)) == (1, 0, 0), (tuner, saved, panel.byte(STATE, S_TUNER)))
    if product:            # the editor mutes the pedal with its tuner while a preset that is tried is loading (app/mini/product-try.js)
        quiet = {}
        for switches, ms in (((A,), 120), ((B,), 120), ((C,), 120), ((A,), 1300), ((C,), 1300), ((A, B), 120), ((B, C), 120)):
            panel.reset()
            panel.byte(STATE, S_TUNER, 1)
            panel.press(*switches, ms=ms)
            quiet[f'{switches} {ms}'] = [c[0] for c in panel.calls if c[0] in ('preset_loader_load', 'footswitch_events_preset_save', 'footswitch_events_reload_preset')]
        row('with the tuner on no switch loads or saves a preset', not any(quiet.values()), quiet)
    panel.reset()
    panel.press(A, B, ms=1200)
    row('A+B held a second changes nothing yet', (panel.byte(STATE, S_BANK), panel.byte(STATE, S_TUNER),
        len(panel.took('footswitch_events_preset_save'))) == (0, 0, 0), [c[:2] for c in panel.calls])
    panel.reset()
    panel.press(A, B, ms=700)
    row('A+B for 0.7 s is a short press', panel.byte(STATE, S_BANK) == banks - 1, panel.byte(STATE, S_BANK))
    if product:
        # live mode: a footswitch switches the first block of its kind (S + 1590 and on: the slot of each kind), and the rest is as in preset mode
        took = {}
        for switch in (A, B, C):
            for kind in range(7):
                panel.reset()
                panel.byte(STATE, S_MODE, 1)
                panel.cpu.mem.write(panel.where[STATE] + 1590, bytes(3 if k == kind else 0xFF for k in range(7)))
                panel.press(switch)
                for call in panel.took('slot_commands_enable_command'):
                    took.setdefault('ABC'[switch], []).append((kind, call[1]))
        row('live mode: A switches the first reverb, B the first delay, C the first modulation', took == {'A': [(0, 3)], 'B': [(1, 3)], 'C': [(2, 3)]}, took)
        went, saved = [], []
        for pair in ((A, B), (B, C)):
            panel.reset()
            panel.byte(STATE, S_MODE, 1)
            panel.press(*pair)
            went.append((panel.byte(STATE, S_BANK), panel.byte(STATE, S_MODE), len(panel.took('slot_commands_enable_command'))))
        for switch in (A, B, C):
            panel.reset()
            panel.byte(STATE, S_MODE, 1)
            panel.press(switch, ms=1200)
            saved.append([c[1] for c in panel.took('footswitch_events_preset_save')])
        row('live mode: the pairs change the bank, a hold saves', went == [(banks - 1, 1, 0), (1, 1, 0)] and saved == [[0], [1], [2]], (went, saved))
    # Bluetooth, two switches held
    seen = {}
    for name, pair in (('A+B', (A, B)), ('B+C', (B, C)), ('A+C', (A, C)), ('B', (B,))):
        for ms in (2400, 2700, 6300):
            panel.reset()
            panel.byte(STATE, S_BLE_READY, 1)
            panel.hold_for_bluetooth((), 30)
            panel.hold_for_bluetooth(pair[:1], 20)
            panel.hold_for_bluetooth(pair, ms)
            panel.hold_for_bluetooth((), 30)
            seen[name, ms] = (len(panel.took('console_helpers_key_open')), len(panel.took('console_helpers_ble_advertise')),
                              panel.byte(STATE, S_BLE_OFF), [c[1:4] for c in panel.took('L0204c744')])
    on, off = (1, 1, 0, []), (1, 1, 1, [(1, 1, 0)])
    right = 'A+B' if product else 'B+C'
    wanted = {(n, ms): {2400: (0, 0, 0, []), 2700: on, 6300: off}[ms] if n == right else (0, 0, 0, [])
              for n in ('A+B', 'B+C', 'A+C', 'B') for ms in (2400, 2700, 6300)}
    row(f'{right} held 2.5 s turns Bluetooth on and accepts a phone, 6 s turns it off; no other pair does', seen == wanted,
        {k: v for k, v in seen.items() if v != wanted[k]})
    if product:
        wheel_and_battery(panel, row)
    if product:
        # what the pedal says it is when it is plugged in: the vendor number of its chip, with HyperRig's product
        panel.reset()
        panel.run('phase3_p13_get_device_descriptor', [0x01C70000])
        said = panel.cpu.mem.read(0x01C70000, 18)
        row('the USB numbers are 4C4A:5155', said[:2] == b'' and (int.from_bytes(said[8:10], 'little'), int.from_bytes(said[10:12], 'little')) == (0x4C4A, 0x5155), said.hex())
    # the console
    panel.reset()
    panel.console('HRID')
    if product:
        row('HRID says the build', panel.lines == [identity], panel.lines)
        panel.lines.clear()
        panel.console('HRST')
        first = panel.lines[:]
        panel.analog = {WHEEL: 512, BATTERY: 600}
        panel.turns(1000)
        panel.lines.clear()
        panel.console('HRST')
        row('HRST says the wheel and the battery', (first, panel.lines) ==
            (['HRST wheel=-1 level=-1 volume=65536 battery=-1 raw=0\n'],
             ['HRST wheel=512 level=60 volume=15344 battery=53 raw=600\n']), (first, panel.lines))
        if 'hyperrig_restart_with' in panel.where:
            way_to_the_loader(panel, row)
    else:
        row('HRID is not known', panel.lines == [] and [c[1] for c in panel.took('console_dispatch_console_dispatch')] == ['HRID'],
            panel.calls)
    panel.reset()
    for line in ('PING', 'HRIDX', 'HRI', 'BLE adv 0'):
        panel.console(line)
    row('other words reach the original dispatcher', [c[1:] for c in panel.took('console_dispatch_console_dispatch')] ==
        [('PING', ''), ('HRIDX', ''), ('HRI', ''), ('BLE', 'adv 0')] and not panel.lines,
        [c[1:] for c in panel.took('console_dispatch_console_dispatch')])
    return rows


def way_to_the_loader(panel, row):
    """STAGE, with the flash as the stock firmware leaves it and spoiled in each place the bootloader or the loader looks at."""
    code = bytes(range(256)) * 20
    stream = build_mini_stage.updater_stream(code)
    head = bytearray(stream[32:64])
    struct.pack_into('<H', head, 2, build_mini_stage.LOADER_CRC)
    struct.pack_into('<H', head, 0, crc16(bytes(head[2:])))
    stream = stream[:32] + bytes(head) + stream[64:]

    def flash(place=0xB7000, record=0xBCF00):
        out = bytearray(b'\xff' * 0x100000)
        build_mini_stage.stored(out, stream, place=place, record=record)
        return out

    def seal(out, at, n):
        struct.pack_into('<H', out, at, crc16(bytes(out[at + 2:at + n])))

    def ask(image, line='STAGE'):
        panel.reset()
        panel.flash = image
        panel.console(line)
        return panel.lines, panel.restarted
    seen = {}
    for place, record in ((0xB7000, 0xBCF00), (0xB9000, 0xBDF00), (0xA9000, 0xB5F00)):
        seen[f'{record:x}'] = ask(flash(place, record))
    row('STAGE says where the record of a stored loader is', all(v == ([f'STAGE 1 {k}\n'], False) for k, v in seen.items()), seen)
    spoiled = {'no record': b'\xff' * 0x100000}
    for name, at, value, size, sealed in (
            ('mark', 0xBCF06, 0x5442, 2, (0xBCF00, 80)), ('checksum', 0xBCF10, 0, 1, None), ('type', 0xBCF02, 0, 2, (0xBCF00, 80)),
            ('place below', 0xBCF48, 0x7F000, 4, (0xBCF00, 80)), ('place above', 0xBCF48, 0xBDFFC, 4, (0xBCF00, 80)),
            ('place not a word', 0xBCF48, 0xB7002, 4, (0xBCF00, 80)), ('file record', 0xB7004, 0xB7020, 4, None), ('header', 0xB7032, 0x55, 1, None),
            ('another loader', 0xB7022, 0x1234, 2, (0xB7020, 32)), ('no size', 0xB7024, 0, 4, (0xB7020, 32)), ('size', 0xB7024, 0x5B1D, 4, (0xB7020, 32)),
            ('load address', 0xB7028, 0x01C0A804, 4, (0xB7020, 32))):
        out = flash()
        out[at:at + size] = value.to_bytes(size, 'little')
        if sealed:
            seal(out, *sealed)
        spoiled[name] = out
    above = flash()
    build_mini_stage.stored(above, bytes(64) + bytes(300), place=0x90000, record=0xBDF00)
    spoiled['another record above'] = above
    seen = {name: (ask(image), ask(image, 'STAGE GO')) for name, image in spoiled.items()}
    row('a loader the bootloader would not start, or not HyperRig\'s, is none, and nothing restarts',
        all(v == ((['STAGE 0\n'], False), (['STAGE ERR\n'], False)) for v in seen.values()),
        {k: v for k, v in seen.items() if v != ((['STAGE 0\n'], False), (['STAGE ERR\n'], False))})
    seen = {w: ask(flash(), 'STAGE ' + w) for w in ('GOX', 'go', 'G', 'GO now', '1')}
    row('STAGE with other words does nothing', all(v == (['STAGE ERR\n'], False) for v in seen.values()), seen)
    image = flash()
    lines, restarted = ask(image, 'STAGE GO')
    mem = panel.cpu.mem
    waited = [c[1] for c in panel.took('L0203feb8')]
    row('STAGE GO gives the record to the bootloader and restarts, after its answer has left',
        (lines, restarted, mem.read(0x01C7FD80, 8), mem.read(0x01C7FD88, 80), mem.read(0x01C7FDD8, 8), waited) ==
        (['STAGE GO\n'], True, bytes(8), bytes(image[0xBCF00:0xBCF50]), b'\xa5' * 8, [10]) and
        [c[0] for c in panel.calls if c[0] in ('L0203feb8', 'storage_coordination_irq_enter', 'link_and_print_send_line')][-2:] == ['L0203feb8', 'storage_coordination_irq_enter'],
        (lines, restarted, mem.read(0x01C7FD80, 16).hex(), waited, [c[0] for c in panel.calls][-4:]))
    row('nothing else was read than records and one loader', all(c[2] in (80, 64) for c in panel.took('phase3_p8_norflash_read')), len(panel.took('phase3_p8_norflash_read')))


def wheel_and_battery(panel, row):
    """The turn of a product build, with the converter's answers given."""
    def volume():
        return panel.word(SETTINGS, G_VOLUME)

    panel.reset()
    panel.turns(1)
    pins = [c for c in panel.calls if c[0] != 'footswitch_events_adc_read']
    wanted = [(f, pin) for pin in (41, 32) for f in ('phase3_p5_gpio_set_die', 'L02004ad6', 'phase3_p5_gpio_set_pull_up',
                                                     'phase3_p5_gpio_set_pull_down')]
    row('the first turn makes PC9 and PC0 analog inputs and reads nothing',
        [c[:2] for c in pins] == wanted and all(c[2] == 0 for c in pins if c[0] != 'L02004ad6') and
        not panel.took('footswitch_events_adc_read'), pins)
    panel.turns(50)
    row('no answer of the converter leaves full volume', volume() == 0x10000, volume())
    # the whole travel, up and down: the stock level 124 - value / 8, squared; the first value counts at once
    wrong = []
    for value in (0, 1, 7, 8, 100, 248, 496, 512, 700, 900, 983, 984, 992, 1000, 1023):
        panel.reset()
        panel.turns(1)
        panel.analog = {WHEEL: value}
        panel.turns(1)
        level = max(0, 124 - value // 8)
        if volume() != level * level * 65536 // (124 * 124):
            wrong.append((value, volume()))
    row('the wheel at rest gives the stock level, squared', not wrong, wrong)
    panel.reset()
    panel.analog = {WHEEL: 1023}
    panel.turns(3)
    seen = []
    for value in (*range(1023, -1, -31), 0):
        panel.analog = {WHEEL: value}
        panel.turns(20)
        seen.append(volume())
    panel.turns(200)
    seen.append(volume())
    row('turning it up never lowers the volume, from silence to full', seen[0] == 0 and seen[-1] == 0x10000 and seen == sorted(seen), seen)
    down = []
    for value in (*range(0, 1024, 31), 1023):
        panel.analog = {WHEEL: value}
        panel.turns(20)
        down.append(volume())
    panel.turns(200)
    down.append(volume())
    row('turning it down never raises it, back to silence', down == sorted(down, reverse=True) and down[-1] == 0, down)
    panel.reset()
    panel.analog = {WHEEL: 500}
    panel.turns(50)
    still = {volume()}
    for k in range(300):
        panel.analog = {WHEEL: 500 + (k * 7919 % 5) - 2}
        panel.turns(1)
        still.add(volume())
    row('noise of two steps does not move the volume', len(still) == 1, still)
    panel.byte(SETTINGS, G_VOLUME_ON, 0)
    panel.turns(1)
    off = volume()
    panel.byte(SETTINGS, G_VOLUME_ON, 1)
    panel.turns(1)
    row('KNOB off gives full volume, on gives the wheel back', (off, volume()) == (0x10000, min(still)), (off, volume()))
    del panel.analog[WHEEL]
    panel.turns(100)
    row('a converter that stops answering keeps the last volume', volume() == min(still), volume())
    # the battery
    seen = {}
    for raw in (0, 100, 300, 558, 560, 565, 570, 600, 640, 800):
        panel.reset()
        panel.analog = {WHEEL: 0, BATTERY: raw}
        panel.cpu.mem.write(panel.where[SETTINGS] + G_PRESET, (7).to_bytes(4, 'little'))
        flashes, last = 0, 0
        for _ in range(26):
            panel.turns(100)
            at = panel.word(STATE, S_FLASH_TIME)
            flashes, last = flashes + (at != last), at
        seen[raw] = (flashes, panel.byte(SETTINGS, G_FLASH_SWITCH) if flashes else None, panel.byte(STATE, S_FLASH_GOOD))
    low = {300, 558, 560, 565}
    row('a battery under a tenth flashes the light of the preset every 8 s; a pin that is no battery does not',
        all((v[0] in (2, 3) and v[1] == 7 % 3) if k in low else v[0] == 0 for k, v in seen.items()) and
        all(v[2] == 0 for v in seen.values()), seen)


def load(build):
    manifest = json.loads((build / 'build-manifest.json').read_bytes())
    wanted = {STATE, SETTINGS, SCAN, LINE, HOLD, HOLD_END, 'hyperrig_restart_with', *RECORDED}
    if manifest.get('product'):
        wanted |= {TURN, 'phase3_p13_get_device_descriptor'}
    found = {}
    with (build / 'link/app.elf').open('rb') as elf:
        for symbol in ELFFile(elf).get_section_by_name('.symtab').iter_symbols():
            if symbol.name in wanted:
                found.setdefault(symbol.name, set()).add(symbol['st_value'])
    optional = {'phase3_p8_norflash_read', 'L0203feb8', 'hyperrig_restart_with'}      # of the builds with STAGE
    wrong = {n: found.get(n) for n in wanted if len(found.get(n, ())) != 1 and not (n in optional and n not in found)}
    if wrong:
        raise SystemExit(f'symbols not found once: {wrong}')
    return manifest, (build / 'app.bin').read_bytes(), {n: min(v) for n, v in found.items()}


def run(build):
    manifest, app, where = load(build)
    product = manifest.get('product')
    identity = f"HRID 1 {product['version']} {product['build_id']} banks=3\n" if product else None
    rows = check(Panel(app, manifest['application_layout'], where), bool(product), identity)
    return {'build': build.as_posix(), 'area_sha256': manifest['area_sha256'], 'product': product, 'checks': rows,
            'held': all(r['held'] for r in rows)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('builds', type=Path, nargs='+', metavar='BUILD')
    args = parser.parse_args(argv)
    results = [run(build) for build in args.builds]
    for result in results:
        print(result['build'], result['area_sha256'][:16], 'product' if result['product'] else 'v4')
        for r in result['checks']:
            print('  ', 'ok  ' if r['held'] else 'FAIL', r['check'], '' if r['held'] else r['seen'])
    print(json.dumps({'held': all(r['held'] for r in results), 'hardware_test': False}))
    return 0 if all(r['held'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
