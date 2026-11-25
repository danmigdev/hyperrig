"""Run the USB device of a product build in the pi32v2 simulator: the serial port of the editor, and the MIDI port beside it. Offline.

The application's own code runs from the bytes of a built firmware: the start of the USB device, its interrupt, its answers on
endpoint 0, the bulk endpoint of the serial port and that of the MIDI port, and the turn of the main task that takes MIDI packets and
sends them. Simulated are the controller, as far as that code uses it, and a computer: it resets the bus, enumerates, configures both
functions, and exchanges packets with both at once. The computer keeps the data toggles and a packet that is not taken is offered
again. Checked as well: that nothing of the MIDI port is there unless it is wanted (with --before, a build without it: the same
descriptors, byte for byte), requests that are not for it, floods, resets in the middle of everything, the cable out and in again, and
the two guards: a computer that does not take the description, and an editor that does not come back.

No device is opened and this is no hardware test: the real controller, its timing, and real computers are not simulated.

Usage, from the repository root:
    python -B tools/check_mini_usb.py BUILD [--before BUILD]
BUILD is an output directory of tools/build_hyperrig_mini_image.py --product.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import struct
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), *[str(ROOT / 'upstream/pi32v2-isa' / d) for d in ('tools/llvm', 'tools/hwtest', '')]]
import mini_sim as sim  # noqa: E402
from pi32v2isa import codec  # noqa: E402

BASE, RAM = 0x02000120, 0x01C00000
CON0, CON1, IO_CON0, TIMER = 0x11800, 0x11804, 0x51000, 0x10704
COUNT = {0: 0x11808, 1: 0x1180C, 2: 0x11810, 3: 0x11814, 4: 0x11834}
TADR = {1: 0x1181C, 2: 0x11824, 3: 0x1182C, 4: 0x11838}
RADR = {1: 0x11820, 2: 0x11828, 3: 0x11830, 4: 0x1183C}
EP0_ADR = 0x11818
STATE, SETTINGS = 'L01c26890', 'L01c1f180'
CLASS_CDC, CDC, MIDI = 16, 2, 1
S_PRESENT, S_CONFIGURED, S_RX = 1, 3, 4
PORTS = ('off', 'waiting', 'on', 'refused')
# What is not the USB device's: recorded, with an answer.
OTHERS = {'storage_platform_register': 0, 'L0203fb92': 0, 'L02040614': 0, 'L0204074c': 0, 'L0203feb8': 0, 'phase3_p5_gpio_set_die': 0,
          'link_and_print_link_pause': None, 'link_and_print_link_resume': None, 'selection_effect_flatten': None, 'preset_storage_available': 1,
          'preset_loader_load': 0, 'scene_application_select': 0, 'scene_application_flush': 0, 'slot_commands_enable_command': 0, 'slot_commands_requested': 0,
          'preset_band_controls_request_reserve': 0, 'footswitch_events_reload_preset': 0, 'preset_application_effect_type': 0,
          'preset_application_effect_enabled': 0, 'tap_tempo_tap_tempo': 0, 'tempo_slot_services_tempo_command': 0, 'storage_coordination_notify': 0,
          'panel_inputs_event_queue': 0, 'bond_records_and_prints_print_b': 0}


class Memory(sim.Memory):
    """The controller's registers, and the few others its code writes."""
    wire = None

    def read(self, a, n):
        if 0x10000 <= a < 0x60000:
            return (self.wire.register(a & ~3) >> 8 * (a & 3)).to_bytes(8, 'little')[:n]
        return sim.Memory.read(self, a, n)

    def write(self, a, data):
        if 0x10000 <= a < 0x60000:
            assert len(data) == 4 and not a & 3, hex(a)
            return self.wire.set_register(a, int.from_bytes(data, 'little'))
        return sim.Memory.write(self, a, data)


class CPU(sim.CPU):
    """With the frame of an interrupt."""

    def special_list(self, insn, raw, size):
        mask = raw.get('m', raw.get('n'))
        if mask >> 0 & 1 and not insn.id.startswith('push'):               # {psr, rets, reti}
            at = self.sp
            for r in (k for k in range(16) if mask >> k & 1):
                value = self.mem_word(at)
                at += 4
                if r == 3:
                    self.rets = value & 0x07FFFFFE
                elif r == 5:
                    self.flags = value & 0xF
            self.sp, self.pc = at, self.pc + size
            self.steps += 1
            return
        if mask >> 0 & 1:
            kept = {3: self.rets, 5: self.flags, 0: 0x02000000}
            registers = [k for k in range(16) if mask >> k & 1]
            self.sp -= 4 * len(registers)
            for k, r in enumerate(registers):
                self.mem.write(self.sp + 4 * k, struct.pack('<I', kept[r] & sim.M))
            self.pc += size
            self.steps += 1
            return
        super().special_list(insn, raw, size)


class Wire:
    """The application's USB device on a simulated controller, and the computer at the other end."""

    def __init__(self, build):
        self.manifest = json.loads((build / 'build-manifest.json').read_bytes())
        self.app = (build / 'app.bin').read_bytes()
        self.where = {}
        with (build / 'link/app.elf').open('rb') as elf:
            for symbol in ELFFile(elf).get_section_by_name('.symtab').iter_symbols():
                if symbol.name:
                    self.where.setdefault(symbol.name, symbol['st_value'])
        self.has_midi = 'hyperrig_usb_functions' in self.where
        self.cpu = CPU()
        self.mem = self.cpu.mem = Memory()
        self.mem.wire = self
        self.mem.write(BASE, self.app)
        layout = self.manifest['application_layout']
        at = int(layout['ram_image_load'], 16) - BASE
        self.mem.write(RAM, self.app[at:at + layout['ram_image_size']])
        self.mem.write(int(layout['bss_start'], 16), bytes(layout['bss_size']))
        self.services = {self.where[n]: n for n in OTHERS if n in self.where}
        self.calls, self.lines, self.chain = [], [], []
        self.registers, self.clock, self.ms = {}, 0, 10_000
        self.depth, self.interrupts, self.interrupt_steps, self.longest = 0, 0, 0, 0
        self.word(SETTINGS, 44, 320_000)                    # the clock the application counts with
        self.word(STATE, 280, 1)                            # its engine is on
        self.set_ms(10_000)
        self.power_off()

    # the controller
    def power_off(self):
        self.index = self.faddr = self.con1 = 0
        self.pending = {2: 0, 4: 0, 6: 0}
        self.enabled = {'tx': 0, 'rx': 0, 'usb': 0}
        self.csr0, self.tx, self.rx = 0, {e: 0 for e in range(1, 5)}, {e: 0 for e in range(1, 5)}
        self.length = {e: 0 for e in range(5)}
        self.toggle = {'in': {e: 0 for e in range(5)}, 'out': {e: 0 for e in range(5)}}
        self.host_toggle = {'in': {e: 0 for e in range(5)}, 'out': {e: 0 for e in range(5)}}
        self.ep0_packets, self.stalled, self.ended, self.accesses = [], False, False, 0
        self.port_on = False
        self.registers[CON0] = 0xF << 20                    # the endpoints off, as the detection of the cable leaves them

    def register(self, a):
        if a == CON0:
            return self.registers.get(CON0, 0) | 4
        if a == CON1:
            return self.con1
        if a == TIMER:
            return self.clock & sim.M
        return self.registers.get(a, 0)

    def set_register(self, a, v):
        if a == CON1:
            return self.sie(v)
        assert CON0 <= a <= 0x1183C or a == IO_CON0 or a in (0x10700, 0x10704), hex(a)
        self.registers[a] = v
        if a == IO_CON0:
            self.port_on = bool(v & 0x40)

    def sie(self, v):
        if not v and not self.depth:                        # the start of the controller; inside the lock it is a zero for register 0
            self.con1 = 0
            return
        assert self.depth > 0, 'the window of the controller is used outside the lock'
        self.accesses += 1
        r = v >> 8 & 0x3F
        if v & 0x4000:
            self.con1 = 0x8000 | self.get(r)
        else:
            self.put(r, v & 255)
            self.con1 = 0x8000

    def get(self, r):
        if r in (2, 4, 6):
            v, self.pending[r] = self.pending[r], 0
            return v
        if r in (3, 5):
            return 0
        e = self.index
        return {7: self.enabled['tx'], 8: 0, 9: self.enabled['rx'], 10: 0, 11: self.enabled['usb'], 1: 0, 14: e,
                17: self.csr0 if e == 0 else self.tx[min(e, 4)], 20: self.rx[min(e, 4) or 1], 18: 0, 21: 0,
                22: self.length[e] & 255, 23: self.length[e] >> 8}[r] & 255

    def put(self, r, v):
        e = self.index
        if r == 0:
            self.faddr = v
        elif r == 14:
            assert v <= 4
            self.index = v
        elif r == 7:
            self.enabled['tx'] = v
        elif r == 9:
            self.enabled['rx'] = v
        elif r == 11:
            self.enabled['usb'] = v
        elif r == 17 and e == 0:
            self.ep0(v)
        elif r == 17:
            if v & 0x40:
                self.toggle['in'][e] = 0
            if v & 8:
                self.tx[e] &= ~1
            if v & 1 and not v & 8:
                assert COUNT[e] in self.registers
                self.tx[e] |= 1
        elif r == 20:
            if v & 0x80:
                self.toggle['out'][e] = 0
            if v & 0x10 or not v & 1:
                self.rx[e] &= ~1                             # the packet was taken
        else:
            assert r in (1, 8, 10, 15, 16, 18, 19, 21), r

    def ep0(self, v):
        if v & 0x40:
            self.csr0 &= ~1
        if v & 0x80:
            self.csr0 &= ~0x10
        if v & 0x20:
            self.stalled = True
            return
        if v & 2:
            self.ep0_packets.append(self.mem.read(self.registers[EP0_ADR], self.registers[COUNT[0]]) if self.registers[COUNT[0]] else b'')
        if v & 8:
            self.ended = True

    # the processor
    def set_ms(self, ms):
        self.ms = ms
        self.clock = ms * 320_000 // 6
        self.word(SETTINGS, 24, ms // 10)

    def word(self, base, offset, value=None):
        at = self.where[base] + offset
        if value is not None:
            self.mem.write(at, struct.pack('<I', value & sim.M))
        return struct.unpack('<I', self.mem.read(at, 4))[0]

    def byte(self, base, offset, value=None):
        at = self.where[base] + offset
        if value is not None:
            self.mem.write(at, bytes([value]))
        return self.mem.read(at, 1)[0]

    def service(self, name):
        cpu = self.cpu
        a = list(cpu.R[:4])
        answer = OTHERS[name]
        if name == 'link_and_print_link_pause':
            answer = 1 if self.byte(STATE, S_PRESENT) else 0
            self.paused = answer
        elif name == 'link_and_print_link_resume':
            answer = 0
            if a[0]:
                self.relink = True
        elif name == 'selection_effect_flatten':
            self.mem.write(a[0], bytes([len(self.chain)]) + bytes(2 for _ in self.chain))
            self.mem.write(a[1], bytes(self.chain))
            answer = 0
        elif name == 'bond_records_and_prints_print_b':
            self.printed, answer = (a[1], a[2], self.mem.read(a[3], 61)), 0
        if name not in ('selection_effect_flatten', 'slot_commands_requested', 'L0203fb92', 'L02040614', 'L0204074c'):
            self.calls.append((name, *a[:3]))
        cpu.R[0] = (answer or 0) & sim.M
        cpu.pc = cpu.rets

    relink = False

    def steps_to(self, stop, limit):
        cpu, start = self.cpu, self.cpu.steps
        while cpu.pc != stop:
            name = self.services.get(cpu.pc)
            if name:
                self.service(name)
                continue
            if cpu.pc == self.where['storage_coordination_irq_enter']:
                self.depth += 1
            elif cpu.pc == self.where['storage_coordination_irq_leave']:
                self.depth -= 1
                assert self.depth >= 0
            insn, raw, size = cpu.decode(cpu.pc)
            if insn.id in ('csync', 'ssync', 'nop') or (text := codec.format(insn, raw)) in ('csync', 'ssync', 'nop'):
                cpu.pc += size
                cpu.steps += 1
                cpu.check_then() if cpu.after_then is not None else None
                continue
            if text == 'rti':
                assert stop == 'rti'
                return cpu.steps - start
            m = re.fullmatch(r'(r\d+) = cnum', text)
            if m:
                cpu.R[int(m.group(1)[1:])] = 0
                cpu.pc += size
                continue
            cpu.step()
            if cpu.steps - start > limit:
                raise RuntimeError('too many steps')
        return cpu.steps - start

    def run(self, name, *args, limit=200_000):
        cpu = self.cpu
        assert self.depth == 0
        cpu.R[:len(args)] = [a & sim.M for a in args]
        cpu.rets, cpu.pc, cpu.sp = sim.RETURN, self.where[name], sim.STACK_TOP
        self.steps_to(sim.RETURN, limit)
        assert self.depth == 0 and self.word('L01c1fc4c', 0) == 0, 'the lock is left in another state'
        return cpu.R[0]

    def interrupt(self):
        """The interrupt of the controller, while there is cause for one."""
        for _ in range(50):
            cause = self.pending[2] & (self.enabled['tx'] | 0) or self.pending[4] & self.enabled['rx'] or self.pending[6] & self.enabled['usb']
            if not cause:
                return
            cpu = self.cpu
            kept = (list(cpu.R), cpu.rets, cpu.sp, cpu.flags, cpu.pc)
            cpu.R = [0xA5A50000 + k for k in range(16)]
            cpu.pc, cpu.sp = self.where['L0201c0be'], sim.STACK_TOP - 0x2000
            before, steps = self.depth, 0
            steps = self.steps_to('rti', 40_000)
            assert self.depth == before == 0 and cpu.sp == sim.STACK_TOP - 0x2000 and cpu.R == [0xA5A50000 + k for k in range(16)], 'the interrupt changed what it broke in on'
            cpu.R, cpu.rets, cpu.sp, cpu.flags, cpu.pc = kept
            self.interrupts += 1
            self.interrupt_steps += steps
            self.longest = max(self.longest, steps)
        raise RuntimeError('an interrupt that does not end')

    # the pedal
    def attach(self):
        self.byte(STATE, S_PRESENT, 1)
        self.run('phase3_p5_usb_device_mode', CLASS_CDC)
        self.mem.write(self.where['L01c37ee8'] + 20, struct.pack('<I', self.where['clock_record_and_usb_link_usb_ready']))
        return self

    def detach(self):
        self.run('phase3_p5_usb_device_mode', 0)
        self.byte(STATE, S_PRESENT, 0)
        self.byte(STATE, S_CONFIGURED, 0)
        self.power_off()

    def device_state(self):
        at = self.word('L01c26f08', 0)
        return self.mem.read(at + 20, 1)[0] if at else 0

    def turn(self, ms=10):
        """A turn of the main task, as far as this goes."""
        self.set_ms(self.ms + ms)
        self.byte(STATE, S_CONFIGURED, int(self.byte(STATE, S_PRESENT) == 1 and self.device_state() == 4))
        self.run('hyperrig_midi_turn', self.ms, limit=400_000)
        if self.relink:
            self.relink = False
            self.run('phase3_p5_usb_device_mode', 0)
            self.run('phase3_p4_usb_sie_close', 0)
            self.byte(STATE, S_CONFIGURED, 0)
            self.power_off()
            self.attach()
            return 'relinked'
        return None

    def turns(self, n):
        for _ in range(n):
            if self.turn():
                return 'relinked'
        return None

    def wait(self, ms, step=250):
        for _ in range(ms // step):
            if self.turn(step):
                return 'relinked'
        return None

    def console(self, text=''):
        """The console word MIDI: the port, whether it is kept, and the settings, as it prints them."""
        self.mem.write(0x01C73800, text.encode() + b'\0')
        self.run('hyperrig_midi_console', 0x01C73800)
        return self.printed

    def port(self):
        return PORTS[self.console()[0]]

    def kept(self):
        return self.console()[1]

    def want(self):
        """The record of the settings as it is read at the start, with the port wanted."""
        page = bytearray(128)
        page[4], page[72], page[73], page[74:104] = 64, 0x4D, 1, bytes.fromhex(self.console()[2].decode('ascii').strip('\0'))
        self.mem.write(0x01C73000, bytes(page))
        self.run('hyperrig_settings_import', 0x01C73000)
        return self

    # the computer
    def bus_reset(self):
        self.pending[6] |= 4
        self.toggle = {'in': {e: 0 for e in range(5)}, 'out': {e: 0 for e in range(5)}}
        self.host_toggle = {'in': {e: 0 for e in range(5)}, 'out': {e: 0 for e in range(5)}}
        self.faddr = 0
        self.interrupt()

    def control(self, setup, data=b''):
        """A control transfer: the data that came, b'' for one that was acknowledged, None for a stall."""
        self.stalled, self.ended, self.ep0_packets = False, False, []
        asked = struct.unpack_from('<H', setup, 6)[0]
        self.mem.write(self.registers[EP0_ADR], setup)
        self.csr0 |= 1
        self.length[0] = 8
        self.pending[2] |= 1
        self.interrupt()
        if setup[0] & 0x80:
            got = b''
            while not self.stalled:
                if not self.ep0_packets:
                    raise RuntimeError(f'no answer to {setup.hex()}')
                packet = self.ep0_packets.pop(0)
                got += packet
                if self.ended or len(packet) < 64 or len(got) >= asked:
                    self.pending[2] |= 1                     # the computer has ended it
                    self.interrupt()
                    return got
                self.pending[2] |= 1
                self.interrupt()
            return None
        if data and not self.stalled:
            self.mem.write(self.registers[EP0_ADR], data)
            self.csr0 |= 1
            self.length[0] = len(data)
            self.pending[2] |= 1
            self.interrupt()
        if self.stalled:
            return None
        if not self.ended:
            raise RuntimeError(f'not acknowledged: {setup.hex()}')
        self.pending[2] |= 1                                 # the status is done
        self.interrupt()
        return b''

    def off(self, endpoint):
        return bool(self.registers.get(CON0, 0) >> (19 + endpoint) & 1)

    def bulk_out(self, endpoint, data):
        """False when the packet was not taken."""
        assert not self.off(endpoint), 'the endpoint is off'
        if self.rx[endpoint] & 1:
            return False
        if self.toggle['out'][endpoint] != self.host_toggle['out'][endpoint]:
            self.host_toggle['out'][endpoint] ^= 1           # taken for one that came before: acknowledged and dropped
            return True
        self.toggle['out'][endpoint] ^= 1
        self.host_toggle['out'][endpoint] ^= 1
        at = self.registers[RADR[endpoint]]
        self.mem.write(at, data + b'\xee' * (4 if len(data) == 64 else 0))          # it writes past a full packet
        self.length[endpoint] = len(data)
        self.rx[endpoint] |= 1
        self.pending[4] |= 1 << endpoint
        self.interrupt()
        return True

    def bulk_in(self, endpoint):
        assert not self.off(endpoint), 'the endpoint is off'
        if not self.tx[endpoint] & 1:
            return None
        packet = self.mem.read(self.registers[TADR[endpoint]], self.registers[COUNT[endpoint]]) if self.registers[COUNT[endpoint]] else b''
        self.tx[endpoint] &= ~1
        good = self.toggle['in'][endpoint] == self.host_toggle['in'][endpoint]
        self.toggle['in'][endpoint] ^= 1
        if good:
            self.host_toggle['in'][endpoint] ^= 1
        self.pending[2] |= 1 << endpoint
        self.interrupt()
        return packet if good else b''

    def enumerate(self, address=0x2A, configure=True):
        self.bus_reset()
        device = self.control(b'\x80\x06\x00\x01\x00\x00\x40\x00')
        self.bus_reset()
        assert self.control(bytes([0, 5, address, 0, 0, 0, 0, 0])) == b'' and self.faddr == address
        head = self.control(b'\x80\x06\x00\x02\x00\x00\x09\x00')
        total = struct.unpack_from('<H', head, 2)[0]
        config = self.control(b'\x80\x06\x00\x02\x00\x00' + struct.pack('<H', total))
        strings = [self.control(bytes([0x80, 6, k, 3, 9 if k else 0, 4 if k else 0, 255, 0])) for k in range(6)]
        if configure:
            assert self.control(b'\x00\x09\x01\x00\x00\x00\x00\x00') == b'' and self.device_state() == 4
        return device, config, strings

    def open_serial(self):
        """The editor opens the port: 115200 8N1, DTR."""
        assert self.control(b'\x21\x20\x00\x00\x00\x00\x07\x00', struct.pack('<IBBB', 115200, 0, 0, 8)) == b''
        assert self.control(b'\x21\x22\x01\x00\x00\x00\x00\x00') == b''
        line = self.control(b'\xa1\x21\x00\x00\x00\x00\x07\x00')
        self.host_toggle['in'][CDC] = self.host_toggle['out'][CDC] = 0             # the application starts the endpoint anew with DTR
        self.toggle['in'][CDC] = self.toggle['out'][CDC] = 0
        return line, self.run('phase3_p4_cdc_ready')

    def serial_in(self, text):
        """A packet to the serial port, read by the main task's read."""
        assert self.bulk_out(CDC, text)
        marked = self.byte(STATE, S_RX)
        self.byte(STATE, S_RX, 0)
        n = self.run('L02005d84', 0x01C72000)
        return marked, self.mem.read(0x01C72000, min(n, 64))

    def serial_out(self, text):
        self.mem.write(0x01C72100, text)
        assert len(text) < 64
        n = self.run('phase3_p4_cdc_write_data', 0x01C72100, len(text))
        return n, self.bulk_in(CDC)

    def took(self, name):
        return [c[1:] for c in self.calls if c[0] == name]


def event(*message):
    code = message[0] >> 4 if message[0] < 0xF0 else 15
    return bytes([code, *message]).ljust(4, b'\0')


def descriptors(config):
    """The descriptors of a configuration, as (type, bytes); ValueError when a length does not fit."""
    out, at = [], 0
    while at < len(config):
        n = config[at]
        if n < 2 or at + n > len(config):
            raise ValueError(at)
        out.append((config[at + 1], config[at:at + n]))
        at += n
    return out


def check(build, before=None):
    rows = []

    def row(name, good, seen=None):
        rows.append({'check': name, 'held': bool(good), 'seen': seen})
        print('   ok  ' if good else '   FAIL', name, '' if good else repr(seen)[:700], flush=True)

    # without the setting: as ever
    plain = Wire(build).attach()
    device, config, strings = plain.enumerate()
    row('without the setting: the serial port alone, 4C4A:5155', device[8:12] == b'\x4a\x4c\x55\x51' and len(config) == 75 and config[4] == 2,
        [device.hex(), len(config)])
    plain.turns(3)
    row('the MIDI port is off, and its endpoint untouched', plain.port() == 'off' and not plain.enabled['rx'] & 2 and not plain.tx[MIDI] and plain.off(MIDI) and not plain.off(CDC), plain.enabled)
    line, ready = plain.open_serial()
    seen = [ready, plain.serial_in(b'PING\n'), plain.serial_out(b'PONG tankm_fw\n')]
    row('the serial port works', seen == [1, (1, b'PING\n'), (14, b'PONG tankm_fw\n')], seen)
    if before:
        old = Wire(before).attach()
        was = old.enumerate()
        row('the same bytes as the build before: device, configuration, strings', was == (device, config, strings), [len(was[1]), len(config)])
        first, second = [], []
        for wire, out in ((old, first), (plain, second)):
            for request in (b'\x81\x0a\x00\x00\x00\x00\x01\x00', b'\x01\x0b\x00\x00\x00\x00\x00\x00', b'\x01\x0b\x00\x00\x01\x00\x00\x00', b'\x02\x01\x00\x00\x82\x00\x00\x00',
                            b'\x82\x00\x00\x00\x02\x00\x02\x00', b'\x80\x06\x00\x06\x00\x00\x0a\x00', b'\x80\x06\x00\x0f\x00\x00\x05\x00', b'\x80\x00\x00\x00\x00\x00\x02\x00',
                            b'\xc0\x00\x00\x00\x00\x00\x08\x00', b'\x40\x99\x00\x00\x00\x00\x00\x00', b'\x81\x06\x00\x22\x02\x00\x40\x00', b'\x80\x08\x00\x00\x00\x00\x01\x00'):
                out.append(wire.control(request))
        row('and the same answers to twelve other requests', first == second, [first, second])

    # with it
    w = Wire(build).want().attach()
    device2, config2, strings2 = w.enumerate()
    row('the device and the strings are the same with it', device2 == device and strings2 == strings, device2.hex())
    row('the serial port comes first, unchanged', config2[9:75] == config[9:75] and config2[:2] == config[:2] and config2[5:9] == config[5:9], None)
    parts = descriptors(config2)
    interfaces = [d[2:8].hex() for t, d in parts if t == 4]
    endpoints = [(d[2], d[3], struct.unpack_from('<H', d, 4)[0]) for t, d in parts if t == 5]
    together = [d[2:6].hex() for t, d in parts if t == 11]
    row('four interfaces in two groups: serial 0 and 1, audio control 2, MIDI streaming 3', config2[4] == 4 and len(config2) == 175 == struct.unpack_from('<H', config2, 2)[0] and
        interfaces == ['000001020201', '0100020a0000', '020000010100', '030002010300'] and together == ['00020202', '02020101'], [interfaces, together])
    row('endpoints: the interrupt and bulk of the serial port, bulk of 64 in and out at 1', endpoints == [(0x86, 3, 8), (2, 2, 64), (0x82, 2, 64), (1, 2, 64), (0x81, 2, 64)], endpoints)
    audio = [d for t, d in parts if t == 0x24][4:]
    at = config2.index(audio[1])
    row('the class descriptors: the header names interface 3, the jacks fit together, the length is right', audio[0] == bytes([9, 0x24, 1, 0, 1, 9, 0, 1, 3]) and
        struct.unpack_from('<H', audio[1], 5)[0] == len(config2) - at and [d[2] for d in audio[1:]] == [1, 2, 2, 3, 3] and
        {d[4] for d in audio[2:]} == {1, 2, 3, 4} and audio[4][6] == 2 and audio[5][6] == 1 and [d for t, d in parts if t == 0x25] == [bytes([5, 0x25, 1, 1, 1]), bytes([5, 0x25, 1, 1, 3])],
        [d.hex() for d in audio])
    w.turn()
    row('configured: the MIDI port is on', w.port() == 'on', w.port())
    asked = {'setting 0 of interface 2': w.control(b'\x01\x0b\x00\x00\x02\x00\x00\x00'), 'of interface 3': w.control(b'\x01\x0b\x00\x00\x03\x00\x00\x00'),
             'setting 1': w.control(b'\x01\x0b\x01\x00\x03\x00\x00\x00'), 'which setting': w.control(b'\x81\x0a\x00\x00\x03\x00\x01\x00'),
             'state': w.control(b'\x81\x00\x00\x00\x02\x00\x02\x00'), 'a class request': w.control(b'\xa1\x81\x00\x01\x00\x02\x02\x00'),
             'a class request out': w.control(b'\x21\x01\x00\x01\x00\x02\x00\x00'), 'interface 4': w.control(b'\x01\x0b\x00\x00\x04\x00\x00\x00'),
             'interface 9': w.control(b'\x81\x00\x00\x00\x09\x00\x02\x00'), 'state of the endpoint': w.control(b'\x82\x00\x00\x00\x81\x00\x02\x00')}
    row('what is asked of its interfaces is answered, and what they do not have is refused', asked == {'setting 0 of interface 2': b'', 'of interface 3': b'', 'setting 1': None,
        'which setting': b'\0', 'state': b'\0\0', 'a class request': None, 'a class request out': None, 'interface 4': None, 'interface 9': None, 'state of the endpoint': b'\0\0'}, asked)
    line2, ready = w.open_serial()
    seen = [line2, ready, w.serial_in(b'PING\n'), w.serial_out(b'PONG tankm_fw\n')]
    row('the serial port works beside it', seen == [line, 1, (1, b'PING\n'), (14, b'PONG tankm_fw\n')], seen)

    # messages in
    w.calls.clear()
    assert w.bulk_out(MIDI, event(0xC0, 5))
    early = w.took('preset_loader_load')
    w.turn()
    row('a program change loads a preset, in the turn and not in the interrupt', early == [] and [c[0] for c in w.took('preset_loader_load')] == [5], [early, w.took('preset_loader_load')])
    w.calls.clear()
    w.bulk_out(MIDI, event(0xB0, 20, 3) + event(0xB0, 23, 127) + event(0x90, 60, 100))
    w.turns(2)
    row('a packet of several', [c[0] for c in w.took('scene_application_select')] == [3] and len(w.took('tap_tempo_tap_tempo')) == 1, w.calls)
    w.calls.clear()
    w.bulk_out(MIDI, event(0xB0, 20, 4)[:4] + b'\x1b\xb0\x14\x05' + b'\x00\x00\x00\x00' + b'\x0b\xb0')
    w.turn()
    row('another cable, an empty event and a torn one are passed over', [c[0] for c in w.took('scene_application_select')] == [4], w.calls)
    # both at once
    rng, scenes, text = random.Random(4), [], b''
    w.calls.clear()
    sent = []
    for k in range(60):
        n = rng.randrange(8)
        assert w.bulk_out(MIDI, event(0xB0, 20, n))
        line = f'GET {k}\n'.encode()
        marked, got = w.serial_in(line)
        n2, back = w.serial_out(b'A ' + line)
        sent.append(n)
        text += got
        if back != b'A ' + line or got != line or not marked:
            row('both at once', False, [k, got, back])
            break
        w.turn()
    row('sixty packets on both, none lost, none in the other', [c[0] for c in w.took('scene_application_select')] == sent and text == b''.join(b'GET %d\n' % k for k in range(60)), sent[:5])

    # messages out
    w.word(SETTINGS, 92, 5)
    w.word(SETTINGS, 88, -1)
    w.turns(60)
    while w.bulk_in(MIDI) is not None:
        w.turn()
    w.word(SETTINGS, 92, 7)
    w.turn()
    first = w.bulk_in(MIDI)
    w.word(SETTINGS, 88, 2)
    w.turn()
    second = w.bulk_in(MIDI)
    row('the player changes the preset and the scene: one packet each', first == event(0xC0, 7) and second == event(0xB0, 20, 2), [first, second])
    w.turns(40)
    w.chain = [4, 9]
    w.turns(2)
    row('nothing more is sent', w.bulk_in(MIDI) is None, None)

    # a computer that does not read
    w.word(SETTINGS, 92, 1)
    w.turns(3)
    for k in range(200):
        w.word(SETTINGS, 92, k % 32)
        w.turn()
    w.word(SETTINGS, 92, 3)
    w.word(SETTINGS, 88, 6)
    w.wait(1500, 100)
    old, after = w.bulk_in(MIDI), []
    for _ in range(5):
        w.turn()
        after.append(w.bulk_in(MIDI))
    row('a computer that has not read: one old packet, then the state of now, and no more', old == event(0xC0, 1) + event(0xB0, 20, 2) and after[0] == event(0xC0, 3) + event(0xB0, 20, 6) and after[1:] == [None] * 4,
        [old, after])

    # floods
    w.calls.clear()
    taken = 0
    for _ in range(100):
        taken += w.bulk_out(MIDI, b''.join(event(0xC0, k) for k in range(16)))
    before_turn = w.interrupts
    row('a flood: the row takes eight packets and the next waits; it costs no interrupt', taken == 9 and not w.bulk_out(MIDI, event(0xC0, 0)) and w.interrupts == before_turn, taken)
    marked, got = w.serial_in(b'PING\n')
    n2, back = w.serial_out(b'PONG\n')
    row('the serial port works while it waits', (marked, got, n2, back) == (1, b'PING\n', 5, b'PONG\n'), [marked, got, back])
    w.turn()
    loads = [c[0] for c in w.took('preset_loader_load')]
    row('a turn does one preset of it, the last', loads == [15], loads)
    row('and the packet that waited is taken', w.bulk_out(MIDI, event(0xC0, 31)), None)
    w.turn()
    w.calls.clear()
    w.turn()
    taken = sum(w.bulk_out(MIDI, event(0xFE) * 16) for _ in range(200))
    row('a flood of active sensing waits too', taken == 9, taken)
    w.turn()
    loads = w.took('preset_loader_load')
    row('and does nothing', loads == [], loads)
    worst, w.longest = w.longest, 0
    w.bulk_out(MIDI, b''.join(event(0xF8) for _ in range(16)))
    ticks, w.longest = w.longest, 0
    w.bulk_out(MIDI, b''.join(event(0xB0, 120, k) for k in range(16)))
    packet, w.longest = w.longest, 0
    w.bulk_out(CDC, b'P' * 64)
    serial = w.longest
    w.run('L02005d84', 0x01C72000)
    w.turn()
    numbers = {'longest interrupt, instructions': worst, 'of a packet of MIDI': packet, 'of sixteen ticks': ticks, 'of a packet of the serial port': serial}
    row('the longest interrupt', worst < 2500 and packet < 2000 and ticks < 2500, numbers)
    # garbage
    w.calls.clear()
    for k in range(150):
        n = rng.randrange(0, 65)
        data = bytes(rng.randrange(256) for _ in range(n))
        if not w.bulk_out(MIDI, data):
            w.turn()
            w.turn()
        if k % 5 == 0:
            w.control(bytes([rng.choice((0x01, 0x21, 0xA1, 0x81, 0x41, 0xC1)), rng.randrange(256), rng.randrange(256), rng.randrange(256), rng.choice((2, 3, 3, 2)), 0, 0, 0]))
        w.turn()
    marked, got = w.serial_in(b'PING\n')
    n2, back = w.serial_out(b'PONG\n')
    row('after 150 packets and 30 requests of garbage both work', (got, back) == (b'PING\n', b'PONG\n') and w.port() == 'on' and
        all(0 <= c[0] < 32 for c in w.took('preset_loader_load')) and all(c[0] < 8 for c in w.took('scene_application_select')), [got, back, w.port()])
    for _ in range(40):
        w.turn()
    # a halted endpoint, which the computer clears: both start at the same toggle again
    w.bulk_out(MIDI, event(0x90, 1, 1))
    w.turn()
    answer = [w.control(b'\x02\x01\x00\x00\x01\x00\x00\x00'), w.control(b'\x02\x01\x00\x00\x81\x00\x00\x00')]
    w.host_toggle['out'][MIDI] = w.host_toggle['in'][MIDI] = 0
    w.turns(40)
    while w.bulk_in(MIDI) is not None:
        w.turn()
    w.calls.clear()
    w.bulk_out(MIDI, event(0xC0, 9))
    w.turn()
    row('CLEAR FEATURE (halt) of its endpoint is answered, and the toggles agree again', answer == [b'', b''] and [c[0] for c in w.took('preset_loader_load')] == [9] and
        w.toggle['in'][MIDI] == w.host_toggle['in'][MIDI], [answer, w.took('preset_loader_load')])
    row('that of the serial port is refused, as ever', w.control(b'\x02\x01\x00\x00\x82\x00\x00\x00') is None, None)

    # resets in the middle of everything
    w.bulk_out(MIDI, b'\x04\xf0\x01\x02' + event(0xB0, 20, 1))
    for _ in range(9):
        w.bulk_out(MIDI, event(0xB0, 20, 1) * 2)
    again = w.enumerate(0x11)
    w.turns(30)
    line3, ready = w.open_serial()
    w.calls.clear()
    good = w.bulk_out(MIDI, event(0xC0, 4))
    w.turn()
    marked, got = w.serial_in(b'PING\n')
    n2, back = w.serial_out(b'PONG\n')
    row('a reset of the bus with everything full: enumerated again, and both work', again == (device2, config2, strings2) and ready == 1 and good and
        [c[0] for c in w.took('preset_loader_load')] == [4] and (got, back) == (b'PING\n', b'PONG\n'), [ready, good, w.took('preset_loader_load'), got, back])
    # the cable out, and in
    w.detach()
    w.wait(4000)
    off = w.port()
    w.attach()
    again = w.enumerate(0x12)
    w.turns(3)
    w.open_serial()
    w.calls.clear()
    w.bulk_out(MIDI, event(0xC0, 2))
    w.turn()
    row('the cable out and in again', off == 'waiting' and again == (device2, config2, strings2) and w.port() == 'on' and [c[0] for c in w.took('preset_loader_load')] == [2], [off, w.port()])

    # the guards
    g = Wire(build).want().attach()
    g.enumerate(configure=False)
    quiet = g.wait(14_000)
    took = g.wait(2000)
    row('a computer that reads the description and does not take it: after 15 seconds the link without it', quiet is None and took == 'relinked', [quiet, took])
    device3, config3, _ = g.enumerate(0x13)
    g.turns(3)
    line, ready = g.open_serial()
    row('which is the serial port as ever', config3 == config and ready == 1 and g.port() == 'refused' and g.serial_in(b'PING\n')[1] == b'PING\n', [len(config3), g.port()])
    row('and it is left so', g.wait(30_000) is None and g.port() == 'refused', g.port())
    g.detach()
    g.wait(4000)
    g.attach()
    _, config4, _ = g.enumerate(0x14)
    g.turns(3)
    row('until the cable was out for three seconds', config4 == config2 and g.port() == 'on', [len(config4), g.port()])
    g = Wire(build).want().attach()
    row('a charger, which reads nothing, is no such computer', g.wait(30_000) is None and g.port() == 'waiting', g.port())
    g.enumerate()
    row('and a computer that comes later is', g.wait(30_000) is None and g.port() == 'on', g.port())

    # a trial, from the console
    t = Wire(build).attach()
    t.enumerate()
    t.turns(2)
    t.open_serial()
    t.console('on')
    kept = [t.kept()]
    soon = t.turns(15)
    then = t.turns(10)
    row('turned on from the console: the answer leaves, then the link is restarted with it', soon is None and then == 'relinked', [soon, then])
    _, config5, _ = t.enumerate(0x15)
    t.turns(2)
    kept.append(t.kept())
    t.open_serial()
    t.turns(50)
    kept.append(t.kept())
    row('it is kept in the settings only when the editor is there over the link that has it', config5 == config2 and kept == [0, 0, 1] and t.port() == 'on', kept)
    row('and it stays', t.wait(60_000) is None and t.port() == 'on', t.port())
    t.console('off')
    t.turns(30)
    _, config6, _ = t.enumerate(0x16)
    t.turns(2)
    row('turned off: the serial port alone', config6 == config and t.port() == 'off' and t.kept() == 0, [len(config6), t.port()])
    for opens, configures in ((False, True), (False, False)):
        t = Wire(build).attach()
        t.enumerate()
        t.turns(2)
        t.open_serial()
        t.console('on')
        t.turns(30)
        t.enumerate(0x17, configure=configures)
        back = t.wait(50_000)
        _, config7, _ = t.enumerate(0x18)
        t.turns(2)
        _, ready = t.open_serial()
        row(f'a trial the editor does not come back from ({"configured" if configures else "not even configured"}): off again by itself',
            back == 'relinked' and config7 == config and ready == 1 and t.port() == 'refused' and t.kept() == 0, [back, len(config7), t.port()])
    return rows, numbers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--before', type=Path)
    a = parser.parse_args(argv)
    rows, numbers = check((ROOT / a.build).resolve(), a.before and (ROOT / a.before).resolve())
    print(json.dumps({'held': all(r['held'] for r in rows), 'checks': len(rows), **numbers, 'hardware_test': False}))
    return 0 if all(r['held'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
