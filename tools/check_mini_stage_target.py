"""Run the compiled HyperRig loader in the pi32v2 simulator, from the bootloader's call to a whole installation. Offline.

The bytes of stage.bin run unmodified from 0x01C0A800, as the pedal's bootloader calls them, with simulated registers: the
clocks as that bootloader leaves them, timer 0, the P33 bridge, the SPI controller with the flash behind it, and the USB
controller with a host that resets the bus, enumerates the device and exchanges bulk packets. The host speaks the loader's
messages over MIDI events, as a PC would: it identifies the loader, reads, installs an application and user sectors with the
header first erased and last written, repeats messages, sends damaged ones, and leaves. Checked as well: which registers are
written, that the watchdog is turned off and the update request cleared, and what happens when the bootloader found no
application, when the clocks are not the expected ones, and when nobody talks to the loader.

One shortcut: the checksum of whole sectors is computed here, after it was run instruction by instruction once. Nothing of
this is a test of a pedal: timing, the real USB controller and the real bootloader are not simulated.

Usage, from the repository root:
    python -B tools/check_mini_stage_target.py BUILD
BUILD is an output directory of tools/build_mini_stage.py.
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

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/pi32v2-isa'), str(ROOT / 'upstream/pi32v2-isa/tools/llvm'),
                str(ROOT / 'upstream/pi32v2-isa/tools/hwtest')]
import sim  # noqa: E402
from pi32v2isa import codec  # noqa: E402
import build_mini_stage  # noqa: E402
from hyperrig import jieli  # noqa: E402
import flash_simulator as fast  # noqa: E402

LOAD, CONTEXT, REQUEST, STATUS = 0x01C0A800, 0x01C05000, 0x01C7FD88, 0x01C7FD80
SECTOR, CHUNK = 4096, 1024
APP, APP_END, USER, USER_END = 0x4000, 0x82000, 0xBF000, 0xFF000
CON0, CON1, IO_CON0, RESET = 0x11800, 0x11804, 0x51000, 0x10000
KEY = 0x980F


class Nor(fast.Nor):
    """The flash of flash_simulator, with the loader's two windows (the application's up to app_end), and the one page RETIRE
    may reach."""
    retiring = None
    app_end = APP_END

    def finish(self, baud):
        op = self.first
        if op == 0x20 and self.n == 4:
            assert self.wel and self.addr % SECTOR == 0 and (APP <= self.addr < self.app_end or USER <= self.addr < USER_END), hex(self.addr)
            self.data[self.addr:self.addr + SECTOR] = b'\xff' * SECTOR
            self.wel, self.busy = False, 2
            self.erases.append(self.addr)
        elif op == 0x02 and self.n >= 5:
            assert self.wel and len(self.page) == 256 and self.addr % 256 == 0
            assert APP <= self.addr < self.app_end or USER <= self.addr < USER_END or self.addr == self.retiring, hex(self.addr)
            for i, byte in enumerate(self.page):
                self.data[self.addr + i] &= byte
            self.wel, self.busy = False, 1
            self.programs.append(self.addr)
        elif op == 0x06 and self.n == 1:
            self.wel = True
        self.n = 0


class Usb:
    """A MUSB device controller as the loader reaches it, and a USB host with a MIDI client behind it."""
    FADDR, INT_TX, INT_RX, INT_USB, INDEX = 0, 2, 4, 6, 14

    def __init__(self, memory):
        self.memory, self.con0, self.con1, self.io = memory, 0, 0, 0
        self.regs = {}
        self.addresses, self.counts = {}, {}
        self.index, self.faddr, self.interrupts = 0, 0, {2: 0, 4: 0, 6: 0}
        self.ep0_ready, self.setup_queue, self.ep0_in, self.ep0_state = False, [], b'', None
        self.rx_ready, self.out_packets, self.in_packets = False, [], []
        self.connected, self.done_control, self.stalls, self.log = False, [], 0, []

    # the device side
    def read(self, a):
        if a == CON0:
            return self.con0 & ~(1 << 13) | 4        # the line is ready; no frame-start pending
        if a == CON1:
            return self.con1
        if a == IO_CON0:
            return self.io
        return self.regs.get(a, 0)

    def write(self, a, v):
        if a == CON0:
            self.con0 = v
        elif a == CON1:
            self.sie(v)
        elif a == IO_CON0:
            self.io = v
            if v & 0x40 and not self.connected:
                self.connected = True
                self.interrupts[6] |= 4             # bus reset
            elif not v & 0x40:
                self.connected = False
        else:
            self.regs[a] = v
            if 0x11808 <= a <= 0x11814:
                self.counts[(a - 0x11808) // 4] = v

    def sie(self, v):
        if v == 0:
            self.con1 = 0
            return
        reg = v >> 8 & 0x3F
        if v & 0x4000:
            self.con1 = 0x8000 | self.get(reg)
        else:
            self.put(reg, v & 255)
            self.con1 = 0x8000

    def get(self, r):
        if r in (2, 4, 6):
            v, self.interrupts[r] = self.interrupts[r], 0
            if r == 2 and self.setup_queue and not self.ep0_ready and self.ep0_state is None:
                self.next_setup()
                v |= 1
            if r == 4 and self.out_packets and not self.rx_ready and self.configured:
                self.next_out()
                v |= 2
            return v
        if r == 17:
            if self.index == 0:
                return 1 if self.ep0_ready else 0
            return 0                                # the host takes an IN packet at once
        if r == 20:
            return 1 if self.rx_ready else 0
        if r == 22:
            return len(self.packet) & 255
        if r == 23:
            return 0
        return 0

    configured = False

    def put(self, r, v):
        if r == 0:
            self.faddr = v
        elif r == 14:
            self.index = v
        elif r == 17 and self.index == 0:
            if v & 0x40:
                self.ep0_ready = False
            if v & 0x20:
                self.stalls += 1
                self.finish_control(None)
                return
            if v & 2:
                self.ep0_in += self.memory.read(self.regs[0x11818], self.counts.get(0, 0))
                self.interrupts[2] |= 1
                if v & 8:
                    self.finish_control(self.ep0_in)
            elif v & 8:
                self.finish_control(b'')
                self.interrupts[2] |= 1
        elif r == 17 and self.index == 1:
            if v & 1:
                self.in_packets.append(self.memory.read(self.regs[0x1181C], self.counts[1]))
        elif r == 20 and self.index == 1 and v & 0x10:
            self.rx_ready = False

    # the host side
    def next_setup(self):
        packet = self.setup_queue[0]
        self.memory.write(self.regs[0x11818], packet)
        self.ep0_ready, self.ep0_in, self.ep0_state = True, b'', packet

    def finish_control(self, answer):
        self.done_control.append((self.setup_queue.pop(0), answer))
        self.ep0_state = None

    def next_out(self):
        self.packet = self.out_packets.pop(0)
        self.memory.write(self.regs[0x11820], self.packet)
        self.rx_ready = True


class Board(fast.Controller):
    """The registers the loader uses; a write anywhere else stops the run."""

    def __init__(self, nor, clocks):
        super().__init__(nor)
        self.usb, self.clocks, self.p33, self.p33_bytes, self.efuse = Usb(self), clocks, {0x80: 0x1F}, [], 0
        self.written, self.reset = set(), False

    @staticmethod
    def peripheral(a):
        return 0x10000 <= a < 0x60000

    def read(self, a, n):
        if not self.peripheral(a):
            return sim.Memory.read(self, a, n)
        assert n == 4, (hex(a), n)
        if a in self.clocks:
            v = self.clocks[a]
        elif a == 0x10400:
            v = 0x8000
        elif a == 0x10200:
            v = 0
        elif a == 0x13E08:
            v = self.regs.get(a, 0) & ~2
        elif a == 0x13E0C:
            v = self.p33_out
        elif a in (CON0, CON1, IO_CON0) or 0x11808 <= a <= 0x1183C:
            v = self.usb.read(a)
        else:
            return super().read(a, n)
        return (v & 0xFFFFFFFF).to_bytes(4, 'little')

    p33_out = 0

    def write(self, a, data):
        if not self.peripheral(a):
            return sim.Memory.write(self, a, data)
        assert len(data) == 4, hex(a)
        v = int.from_bytes(data, 'little')
        self.written.add(a)
        if a in (CON0, CON1, IO_CON0) or 0x11808 <= a <= 0x1183C:
            self.usb.write(a, v)
        elif a in (0x10400, 0x10404, 0x10408):
            pass
        elif a == 0x10010:
            assert v & ~3 == self.regs.get(a, 0) & ~3
        elif a == 0x13E08:
            if v & 1 and not self.regs.get(a, 0) & 1:
                self.p33_bytes = []
            self.regs[a] = v
            if v & 16:
                self.p33_byte()
                self.regs[a] &= ~16
        elif a == 0x13E0C:
            self.regs[a] = v
        elif a == RESET:
            assert v == 0x10
            self.reset = True
        elif a in self.clocks:
            raise AssertionError(f'the loader changes a clock register {a:#x}')
        else:
            super().write(a, data)

    def p33_byte(self):
        self.p33_bytes.append(self.regs[0x13E0C] & 255)
        if len(self.p33_bytes) < 3:
            return
        op, address = self.p33_bytes[0] & 0xE0, (self.p33_bytes[0] & 3) << 8 | self.p33_bytes[1]
        value, old = self.p33_bytes[2], self.p33.get(address, 0)
        if op == 0x80:
            if address == 0xB2:              # the efuse byte the last 0xB1 write chose
                value = (KEY << 8 >> 8 * (self.p33.get(0xB1, 0) >> 2 & 3)) & 255 if self.p33.get(0xB0) == 0x40 else 0
                self.p33_out = value
            else:
                self.p33_out = old
        else:
            self.p33[address] = value if op == 0 else old | value if op == 0x20 else old & value
        assert address in (0x80, 0xB0, 0xB1, 0xB2), hex(address)


class Loader(sim.CPU):
    def __init__(self, build, flash, *, app=True, clocks=None, request=True):
        super().__init__()
        self.mem = Board(Nor(flash), clocks or {0x10008: 0x10200, 0x10014: 0x06})
        whole = (build / 'stage-code.bin').read_bytes()         # with its filler, which reaches into what the loader clears
        assert whole.startswith((build / 'stage.bin').read_bytes())
        with (build / 'stage.elf').open('rb') as elf:
            self.symbols = {s.name: s['st_value'] for s in ELFFile(elf).get_section_by_name('.symtab').iter_symbols() if s.name}
        # what the bootloader leaves: its context, the retained words, RAM full of something
        for a in range(self.symbols['__bss_start'], self.symbols['__ram_end'], 64):
            self.mem.write(a, b'\xa5' * 64)
        self.mem.write(LOAD, whole)
        # without an application the bootloader's entry is what it read there, and only the place is zero
        self.mem.write(CONTEXT, struct.pack('<IIIHHII', 0x02000120 if app else 0x379B4D26, APP if app else 0, 0, KEY, 0, 0, 0))
        self.mem.write(STATUS, b'\x00' * 8 + (b'\x34\x12\x0d\x5a' + b'\x55' * 76 if request else bytes(80)))
        self.R[0], self.R[1], self.pc, self.rets, self.sp = CONTEXT, 0xB7000 + 7042, LOAD, 0x01C05301, 0x01C09000
        self.fast_crc, self.received, self.sequence = True, b'', random.Random(7).randrange(60000)

    def step(self):
        if self.pc == self.symbols['update'] and self.fast_crc and self.R[2] >= 256:
            data = self.mem.read(self.R[1], self.R[2])
            self.R[0] = (zlib.crc32(data, self.R[0] ^ 0xFFFFFFFF) ^ 0xFFFFFFFF) & 0xFFFFFFFF
            self.pc = self.rets
            return
        if self.pc == self.symbols['settle']:
            self.pc = self.rets                     # a delay of nops
            return
        insn, raw, size = self.decode(self.pc)
        if insn.id in ('mov.sr_r', 'mov.r_sr') or 'ssp' in (text := codec.format(insn, raw)):
            text = codec.format(insn, raw)
            if re.fullmatch(r'ssp = r\d+', text):
                pass
            elif m := re.fullmatch(r'sp = r(\d+)', text):
                self.sp = self.R[int(m.group(1))]
            else:
                raise RuntimeError(f'{self.pc:#x}: {text}')
            self.pc += size
            return
        if text in ('cli', 'csync', 'ssync', 'nop'):      # no interrupts and no pipeline here
            self.pc += size
            return
        super().step()

    def run(self, until, limit=40_000_000):
        start = self.steps
        while not until():
            self.step()
            if self.steps - start > limit:
                raise RuntimeError('the loader does not get there')

    # the host
    def control(self, setup):
        usb, before = self.mem.usb, len(self.mem.usb.done_control)
        usb.setup_queue.append(setup)
        self.run(lambda: len(usb.done_control) > before, 3_000_000)
        return usb.done_control[-1][1]

    def enumerate(self):
        usb = self.mem.usb
        self.run(lambda: usb.connected and usb.con0 & 1, 20_000_000)
        device = self.control(b'\x80\x06\x00\x01\x00\x00\x12\x00')
        assert device[:2] == b'\x12\x01' and len(device) == 18
        assert self.control(b'\x00\x05\x2a\x00\x00\x00\x00\x00') == b''
        self.run(lambda: usb.faddr == 0x2A, 3_000_000)
        head = self.control(b'\x80\x06\x00\x02\x00\x00\x09\x00')
        total = struct.unpack_from('<H', head, 2)[0]
        config = self.control(b'\x80\x06\x00\x02\x00\x00' + struct.pack('<H', total))
        assert len(config) == total == 101
        assert self.control(b'\x80\x06\x00\x03\x00\x00\xff\x00') == b'\x04\x03\x09\x04'
        name = self.control(b'\x80\x06\x01\x03\x09\x04\xff\x00')
        assert name[2:].decode('utf-16-le') == 'HyperRig Update', name
        assert self.control(b'\x80\x06\x09\x03\x09\x04\xff\x00') is None and usb.stalls == 1      # no such string
        assert self.control(b'\x00\x09\x01\x00\x00\x00\x00\x00') == b''
        usb.configured = True
        return {'vendor_product': device[8:12].hex(), 'configuration': len(config)}

    def send(self, message, *, junk=b''):
        """One message as MIDI events in bulk packets of 64 bytes."""
        bits = int.from_bytes(message, 'little')
        packed = bytes(bits >> 7 * i & 0x7F for i in range((len(message) * 8 + 6) // 7))
        stream = junk + b'\xf0\x7dHR' + packed + b'\xf7'
        events = b''
        while stream:
            part, stream = stream[:3], stream[3:]
            end = part.endswith(b'\xf7')
            code = {1: 5, 2: 6, 3: 7}[len(part)] if end else 4
            events += bytes([code]) + part.ljust(3, b'\0')
        self.mem.usb.out_packets += [events[i:i + 64] for i in range(0, len(events), 64)]

    def take(self):
        """A reply that arrived, unpacked; None when there is none yet."""
        usb = self.mem.usb
        while usb.in_packets:
            packet = usb.in_packets.pop(0)
            for i in range(0, len(packet), 4):
                self.received += packet[i + 1:i + 1 + {4: 3, 5: 1, 6: 2, 7: 3}[packet[i] & 15]]
        if not self.received.endswith(b'\xf7'):
            return None
        raw, self.received = self.received, b''
        assert raw.startswith(b'\xf0\x7dHR') and all(b < 0x80 for b in raw[1:-1])
        bits = sum(b << 7 * i for i, b in enumerate(raw[4:-1]))
        data = bits.to_bytes((len(raw) - 5) * 7 // 8 + 1, 'little')
        size = 8 + struct.unpack_from('<H', data, 6)[0]
        assert zlib.crc32(data[:size]) == struct.unpack_from('<I', data, size)[0]
        return data[:size]

    def frame(self, op, body=b''):
        self.sequence = (self.sequence + 1) & 0xFFFF
        head = struct.pack('<2sBBHH', b'HR', 1, op, self.sequence, len(body)) + body
        return head + struct.pack('<I', zlib.crc32(head))

    def ask(self, op, body=b'', *, frame=None, limit=40_000_000):
        frame = frame or self.frame(op, body)
        self.send(frame)
        got = []
        start = self.steps
        while not got:
            for _ in range(2000):
                self.step()
            reply = self.take()
            if reply is not None:
                got.append(reply)
            if self.steps - start > limit:
                raise RuntimeError('no answer')
        reply = got[0]
        assert reply[:3] == b'HR\x01' and reply[3] == frame[3] | 0x80 and reply[4:6] == frame[4:6]
        return reply[8], reply[9], reply[10:]

    def silent(self, message, junk=b'', turns=40):
        """Nothing is answered to this."""
        self.send(message, junk=junk)
        for _ in range(turns):
            for _ in range(2000):
                self.step()
            assert self.take() is None
        assert not self.mem.usb.out_packets

    def install(self, now, want, *, repeat=False, end=None):
        """With end, BEGIN widens the application's window up to it (a loader since 022)."""
        order = [a for a in range(APP + SECTOR, USER_END, SECTOR) if (a < (end or APP_END) or a >= USER) and now[a:a + SECTOR] != want[a:a + SECTOR]] + [APP]
        crc = lambda b: zlib.crc32(bytes(b))
        windows = 1 | (2 if any(a >= USER for a in order) else 0)
        begin = struct.pack('<IIHBI', crc(now), crc(want), len(order), windows, 0x214D5241) + (struct.pack('<I', end) if end else b'')
        results = [self.ask(0x10, begin)[:2],
                   self.ask(0x13, struct.pack('<I', crc(now[APP:APP + SECTOR])))[:2]]
        for a in order:
            for at in range(0, SECTOR, CHUNK):
                results.append(self.ask(0x11, struct.pack('<H', at) + bytes(want[a + at:a + at + CHUNK]))[:2])
            frame = self.frame(0x12, struct.pack('<III', a, crc(now[a:a + SECTOR]), crc(want[a:a + SECTOR])))
            results.append(self.ask(0x12, frame=frame)[:2])
            if repeat:
                count = len(self.mem.nor.erases) * 1000 + len(self.mem.nor.programs)
                assert self.ask(0x12, frame=frame)[:2] == results[-1]
                assert count == len(self.mem.nor.erases) * 1000 + len(self.mem.nor.programs)
        results.append(self.ask(0x14)[:2])
        return order, results


def directory(flash, vm):
    """The partitions of a TANK-MINI at the head of its application, as the installer leaves them: the application's up to vm
    (PRCT), the VM from vm to 0xbe000. JieLi's encoding with the chip's key; each record with its own CRC-16."""
    page = bytearray(b'\xff' * 256)
    for k, (name, at, size) in enumerate((('app_area_head', 0x2000120, 0x1000), ('app.bin', 0x120, 0x1000), ('cfg_tool.bin', 0x240, 0x17f),
                                          ('VM', vm, 0xBE000 - vm), ('PRCT', 0, vm), ('BTIF', 0xBE000, SECTOR), ('USR', USER, USER_END - USER))):
        record = bytearray(struct.pack('<HHIIBBH16s', 0, 0xFFFF, at, size, 0x92, 0x81, 0, name.encode().ljust(16, b'\0')))
        record[0:2] = struct.pack('<H', jieli.crc16(bytes(record[2:])))
        page[32 * k:32 * k + 32] = record
    flash[APP:APP + 256] = jieli.sfc(bytes(page), KEY)


def images(build):
    rng = random.Random(1)
    now = bytearray(rng.randbytes(0x100000))
    build_mini_stage.stored(now, (build / 'stage-ota.bin').read_bytes())
    want = bytearray(now)
    for a in (0x4001, 0x5000, 0x81FFF, 0xBF010):
        want[a] ^= 0x5A
    return now, want


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    args = parser.parse_args(argv)
    now, want = images(args.build)
    report = {'kind': 'mini-stage-target-check', 'hardware_test': False, 'steps': {}}
    steps = report['steps']

    # started by the bootloader for an update, with a whole application in the flash
    loader = Loader(args.build, now)
    steps['usb'] = loader.enumerate()
    assert loader.mem.p33[0x80] == 0x0F, 'the watchdog was not turned off'
    assert loader.mem.read(REQUEST, 2) == b'\0\0' and loader.mem.read(REQUEST + 2, 2) == b'\x0d\x5a', 'the request was not cleared'
    status, phase, hello = loader.ask(0x01)
    steps['hello'] = {'status': status, 'phase': phase, 'magic': hello[:4].decode(), 'chunk': struct.unpack_from('<H', hello, 4)[0],
                      'jedec': hex(struct.unpack_from('<I', hello, 10)[0]), 'key': hex(struct.unpack_from('<H', hello, 14)[0]),
                      'fast': hello[18], 'app_valid': hello[19], 'build': hello[26:42].decode()}
    assert (status, phase, hello[:4], hello[18], hello[19]) == (0, 0, b'HRS1', 1, 1)
    assert hello[42] == 1 and struct.unpack_from('<I', hello, 43)[0] == 0xBCF00, 'the way back was not seen'
    assert steps['hello']['jedec'] == '0xeb6014' and steps['hello']['key'] == hex(KEY)
    for address, length in ((0, 1024), (0xFF000, 4096 // 4), (0x12345, 1), (0x81F00, 777)):
        status, _, data = loader.ask(0x02, struct.pack('<IH', address, length))
        assert status == 0 and data == bytes(now[address:address + length])
    loader.fast_crc = False
    status, _, data = loader.ask(0x03, struct.pack('<II', 0x3F00, 5000))
    assert status == 0 and struct.unpack('<I', data)[0] == zlib.crc32(now[0x3F00:0x3F00 + 5000])
    loader.fast_crc = True
    # what is not a message, or not a whole one
    good = loader.frame(0x02, struct.pack('<IH', 0, 16))
    for bad in (good[:-1], good + b'\0', bytes([good[0] ^ 1]) + good[1:], good[:9] + bytes([good[9] ^ 4]) + good[10:], b'', b'HR'):
        loader.silent(bad)
    loader.silent(b'HR', junk=b'\xf0\x7e\x7f\x06\x01\xf7')
    assert loader.ask(0x02, frame=good)[0] == 0
    assert loader.ask(0x12, bytes(12))[0] == 3 and not loader.mem.nor.erases                # nothing before BEGIN
    status, _, _ = loader.ask(0x10, struct.pack('<IIHBI', 1, 2, 3, 1, 0x214D5241))
    assert status == 5, 'a host without the backup was accepted'
    order, results = loader.install(now, want, repeat=True)
    assert all(r[0] == 0 for r in results) and results[-1][1] == 3, results
    assert bytes(loader.mem.nor.data) == bytes(want)
    assert loader.mem.nor.erases[0] == APP and order[-1] == APP and loader.mem.nor.programs[-1] == APP
    steps['install'] = {'sectors': len(order), 'messages': len(results), 'erases': len(loader.mem.nor.erases),
                        'programs': len(loader.mem.nor.programs), 'opcodes': sorted(hex(o) for o in loader.mem.nor.opcodes)}
    assert set(loader.mem.nor.opcodes) <= {0xFF, 0x9F, 0x03, 0x05, 0x35, 0x06, 0x20, 0x02}
    assert loader.ask(0x20, b'\x01')[0] == 0
    loader.run(lambda: loader.mem.reset, 30_000_000)
    assert loader.mem.read(STATUS, 16) == bytes(16) and not loader.mem.usb.connected
    steps['registers_written'] = sorted(hex(a) for a in loader.mem.written)

    # a whole application and no way back to the loader: it is not opened; an older record above ours is made void
    for change in ('none', 'above'):
        other = bytearray(now)
        if change == 'none':
            other[0xBCF06] ^= 1
        else:
            build_mini_stage.stored(other, bytes(64) + bytes(range(200)), place=0x90000, record=0xBDF00, name=b'ota-TANK MINI_009')
        loader = Loader(args.build, other)
        loader.enumerate()
        hello = loader.ask(0x01)[2]
        assert hello[42] == 0 and struct.unpack_from('<I', hello, 43)[0] == (0xBDF00 if change == 'above' else 0)
        assert loader.ask(0x10, struct.pack('<IIHBI', zlib.crc32(bytes(other)), 2, 3, 1, 0x214D5241))[0] == 0
        assert loader.ask(0x13, struct.pack('<I', zlib.crc32(bytes(other[APP:APP + SECTOR]))))[0] == 8 and not loader.mem.nor.erases
        assert loader.ask(0x20, b'\x01')[0] == 0
        if change == 'above':
            loader = Loader(args.build, other)
            loader.enumerate()
            assert loader.ask(0x15, struct.pack('<I', 0xBCF00))[0] == 2 and not loader.mem.nor.programs
            loader.mem.nor.retiring = 0xBDF00
            assert loader.ask(0x15, struct.pack('<I', 0xBDF00))[0] == 0 and loader.mem.nor.programs == [0xBDF00]
            other[0xBDF06:0xBDF08] = b'\0\0'
            assert bytes(loader.mem.nor.data) == bytes(other) and not loader.mem.nor.erases
            hello = loader.ask(0x01)[2]
            assert hello[42] == 1 and struct.unpack_from('<I', hello, 43)[0] == 0xBCF00 and hello[24] == 0
    steps['way_back'] = 'a whole application is opened only with one; an older record above ours can be made void'

    # the window widened up to the pedal's VM, as its directory says (0x95000, a TANK-MINI with 011); and refused on one whose
    # VM starts at 0x82000 (009), with nothing erased
    wide_now, wide_want = bytearray(now), bytearray(now)
    directory(wide_now, 0x95000)
    wide_want[:] = wide_now
    for a in (APP + 300, 0x82000, 0x88123, 0x94FFF, 0xBF010):
        wide_want[a] ^= 0x5A
    loader = Loader(args.build, wide_now)
    loader.mem.nor.app_end = 0x95000
    loader.enumerate()
    hello = loader.ask(0x01)[2]
    assert len(hello) == 51 and struct.unpack_from('<I', hello, 47)[0] == APP_END, 'a new loader says its window'
    order, results = loader.install(wide_now, wide_want, end=0x95000)
    assert all(r[0] == 0 for r in results) and results[-1][1] == 3 and bytes(loader.mem.nor.data) == bytes(wide_want), results
    assert {0x82000, 0x88000, 0x94000} <= set(order) and struct.unpack_from('<I', loader.ask(0x01)[2], 47)[0] == 0x95000
    other = bytearray(wide_now)
    directory(other, 0x82000)
    loader = Loader(args.build, other)
    loader.enumerate()
    begin = struct.pack('<IIHBII', zlib.crc32(bytes(other)), 2, 3, 1, 0x214D5241, 0x95000)
    assert loader.ask(0x10, begin)[:2] == (2, 0) and not loader.mem.nor.erases and not loader.mem.nor.programs
    steps['wide'] = {'sectors': len(order), 'up_to': '0x95000', 'refused_on_a_009_directory': True}

    # the bootloader found no application: the loader stays, and installs
    loader = Loader(args.build, now, app=False, request=False)
    loader.enumerate()
    assert loader.ask(0x01)[2][19] == 0 and loader.ask(0x20, b'\x01')[0] == 7
    order, results = loader.install(now, want)
    assert all(r[0] == 0 for r in results) and bytes(loader.mem.nor.data) == bytes(want) and loader.ask(0x20, b'\x01')[0] == 0
    loader = Loader(args.build, now, app=False)
    loader.enumerate()
    assert loader.ask(0x20, b'\x02')[0] == 0
    loader.run(lambda: loader.mem.reset, 30_000_000)
    assert loader.mem.read(STATUS, 16) == b'usb_update_mode\0'
    steps['no_application'] = 'stays, installs, or goes to the ROM when asked'

    # clocks that are not the bootloader's: the flash is not touched, reads are refused, leaving works
    loader = Loader(args.build, now, clocks={0x10008: 0, 0x10014: 0x80})
    loader.enumerate()
    status, phase, hello = loader.ask(0x01)
    assert phase == 4 and struct.unpack_from('<I', hello, 10)[0] == 0 and loader.ask(0x02, struct.pack('<IH', 0, 16))[0] != 0
    assert loader.ask(0x10, struct.pack('<IIHBI', 1, 2, 3, 1, 0x214D5241))[0] != 0 and not loader.mem.nor.opcodes
    assert loader.ask(0x20, b'\x01')[0] == 0
    steps['other_clocks'] = 'no flash access'

    # nobody talks to it: with a whole application it goes back by itself, without one it stays
    for app in (True, False):
        loader = Loader(args.build, now, app=app)
        loader.enumerate()
        turns = loader.symbols['turns']
        loader.mem.write(turns, (600000 - 3).to_bytes(4, 'little'))
        if app:
            loader.run(lambda: loader.mem.reset, 30_000_000)
        else:
            for _ in range(60_000):
                loader.step()
            assert not loader.mem.reset
    steps['nobody'] = 'back to the application when there is one, else it stays'
    report['held'] = True
    print(json.dumps(report, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
