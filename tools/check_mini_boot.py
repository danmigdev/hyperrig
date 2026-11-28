"""Run the pedal's own update code and bootloader, in the pi32v2 simulator, with the HyperRig loader. Offline; no device is opened.

Two pieces of code decide whether the installer's way in and its way back exist, and neither is HyperRig's: the update service
of the stock firmware, which takes a package over MIDI and stores its ota.bin, and the bootloader (SPL), which starts what was
stored. This check takes both from M-VAVE's update packages, which the person has and which are not in this repository, and
runs their instructions:

1. The official packages, as a control: the stock code asks for the blocks recorded in a real update of this pedal, and
   stores their loader where this pedal's flash had it.
2. HyperRig's package (tools/build_mini_stage.py), which holds ota.bin only: accepted, stored, its checksum verified, the
   update record written to the flash and to the retained RAM. With the settings store (VM) holding little or much.
3. The bootloader with that flash: started for an update, after a loss of power with the application's header erased, with an
   older record above, with a damaged or missing one. It unpacks the loader, which is compared with the one that was built.
4. An installation by the loader's own engine, cut at each flash operation: after each cut the bootloader is run on what is
   left in the flash. It must start the application or the HyperRig loader, never anything else. On 011 a second one with
   the application's window widened to the pedal's VM (0x95000, as its own directory says), which writes past 0x82000.

Replaced are the calls that touch hardware: reading, erasing and programming the flash, the checksum unit, locks and delays.
Nothing of this is a test of a pedal.

Usage, from the repository root:
    python -B tools/check_mini_boot.py BUILD --package TANK-MINI.fwsc [--package ...] [--no-cuts]
BUILD is an output directory of tools/build_mini_stage.py; each package is the official one of TANK MINI_009 or _011.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'upstream/m-bootloader/tools')]
import build_mini_stage as stage  # noqa: E402
import fwsc  # noqa: E402
import mini_sim as sim  # noqa: E402
from hyperrig.jieli import crc16, enc, sfc  # noqa: E402

KEY, XIP, CAPACITY, SECTOR = 0x980F, 0x02000000, 0x100000, 4096
LOADER, STATUS, REQUEST = 0x01C0A800, 0x01C7FD80, 0x01C7FD88
BOOT_SHA256 = 'd9f43191777656de01c7bed4f9e9ba2e34e94832c5d2ed02c3fc7ab7a6d9bd67'
OPS, HEAP, TASK = 0x01D00000, 0x01D10000, 0x01D0E000
# Where each function is, and the places of its data: globals, the fields of it that moved, the VM's records.
VERSIONS = {
    'TANK MINI_011': dict(
        area='5a5c6f0f', prepare=0x20748DC, request=0x201A64A, notice=0x20072BE, G=0x01C22300, ops=480, task=464, told=568, vm=(1672, 1675, 1826),
        malloc=0x2048554, free=0x204969A, memset=0x203CFB6, memcpy=0x203C748, memcmp=0x203C710, strlen=0x203C976, strncmp=0x203C982,
        strcmp=0x203C868, read_raw=0x200607E, read_coded=0x2005FE6, read_wrap=0x20198B0, crc16=0x2003786, ioctl=0x200BA66, erase=0x200BC24,
        write=0x200BCD2, program=0x200BC4A, vm_state=0x2019C82, vm_start=0x95000,
        none=(0x2000982, 0x204CC80, 0x204CE1A, 0x201988E, 0x201994C, 0x20198DA, 0x204B84A, 0x2019B9A, 0x204B4D4, 0x204CF7C, 0x204C5C8)),
    'TANK MINI_009': dict(
        area='', prepare=0x206D364, request=0x201606A, notice=0x200762E, G=0x01C15790, ops=400, task=384, told=488, vm=(1625, 1628, 1779),
        malloc=0x2040CD0, free=0x2041E16, memset=0x2034BB8, memcpy=0x203437C, memcmp=0x2034344, strlen=0x2034578, strncmp=0x2034584,
        strcmp=0x203446A, read_raw=0x200668E, read_coded=0x20065F6, read_wrap=0x20152D0, crc16=0x2003E04, ioctl=0x2009CA8, erase=0x2009E66,
        write=0x2009F14, program=0x2009E8C, vm_state=0x20156A2, vm_start=0x82000,
        none=(0x2000982, 0x20453FC, 0x2045596, 0x20152AE, 0x201536C, 0x20152FA, 0x2043FC6, 0x20155BA, 0x2043C50, 0x20456F8, 0x2044D44)),
}
# The blocks a real update of this pedal asked for while 011 prepared the official 009 package (M-Upgrade's log, 19 November
# 2026): the first ones, and how many.
RECORDED = [(0, 512), (0x200, 512), (0x400, 512), (0x400, 512), (0x4400, 512), (0x400, 32), (0x400, 512), (0x4400, 32), (0x830E0, 512), (0x83100, 512)]
RECORDED_COUNT = 48


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def official(path):
    """(identity, image, {name: bytes}) of an official package."""
    identity, _, image = fwsc.unweave(Path(path).read_bytes())
    return identity, image, {e['name']: image[e['offset']:e['offset'] + e['size']] for e in fwsc.entries(image)}


class Stock(sim.CPU):
    """The stock firmware's update service with a host that serves a package."""

    def __init__(self, version, flash, package, used):
        super().__init__()
        self.v, self.flash, self.package = VERSIONS[version], bytearray(flash), package
        self.position, self.heap, self.state = 0, HEAP, 0
        self.reads, self.erased, self.programmed, self.notices = [], [], [], []
        v, g = self.v, self.v['G']
        self.mem.write(XIP, sfc(bytes(flash[0x4000:v['vm_start']])))
        ops = [0x01D0F000 + 16 * i for i in range(8)]
        for i, a in enumerate(ops):
            self.mem.write(OPS + 4 * i, struct.pack('<I', a))
        self.poke(g + v['ops'], OPS)
        self.poke(g + v['task'], TASK)
        self.poke(TASK + 96, v['notice'])
        self.mem.write(0x01C7FD50 + 28, struct.pack('<H', KEY))
        self.vm = (v['vm_start'], used)
        for place, value in zip(v['vm'], (v['vm_start'], v['vm_start'] + (0xBE000 - v['vm_start']) // 2, v['vm_start'] + used)):
            self.poke(g + 4 * place, value)
        self.hooks = {v['malloc']: self.malloc, v['free']: self.nothing, v['memset']: self.memset, v['memcpy']: self.memcpy, v['memcmp']: self.memcmp,
                      v['strlen']: lambda: len(self.text(self.R[0])), v['strncmp']: self.strncmp, v['strcmp']: self.strcmp,
                      v['read_raw']: lambda: self.load(self.R[0], self.R[1], self.R[2]), v['read_wrap']: lambda: self.load(self.R[0], self.R[1], self.R[2]),
                      v['read_coded']: lambda: self.load(self.R[0], self.R[2], self.R[1], True), v['crc16']: lambda: crc16(self.mem.read(self.R[0], self.R[1])),
                      v['ioctl']: self.ioctl, v['erase']: self.erase, v['write']: lambda: self.program(self.R[0], self.R[1], self.R[2]),
                      v['program']: lambda: self.program(self.R[0], self.R[2], self.R[1]), v['vm_state']: self.vm_state,
                      ops[1]: lambda: 1, ops[2]: self.host_read, ops[3]: self.host_seek, ops[4]: self.nothing, ops[5]: self.notify, ops[6]: self.nothing}
        self.hooks.update({a: self.nothing for a in v['none']})
        read, write = self.mem.read, self.mem.write

        def port_read(a, n):
            return struct.pack('<I', self.state)[:n] if a == 0x13504 else read(a, n)

        def port_write(a, data):
            if a == 0x13504:
                self.state = int.from_bytes(data, 'little') & 0xFFFF
            elif a == 0x13500:
                self.state = binascii.crc_hqx(bytes([data[0]]), self.state)
            else:
                write(a, data)
        self.mem.read, self.mem.write = port_read, port_write

    def poke(self, a, value):
        self.mem.write(a, struct.pack('<I', value))

    def peek(self, a):
        return struct.unpack('<I', self.mem.read(a, 4))[0]

    def nothing(self):
        return 0

    def malloc(self):
        a, self.heap = self.heap, self.heap + (self.R[0] + 63 & ~63)
        return a

    def memset(self):
        self.mem.write(self.R[0], bytes([self.R[1] & 255]) * self.R[2])
        return self.R[0]

    def memcpy(self):
        self.mem.write(self.R[0], self.mem.read(self.R[1], self.R[2]))
        return self.R[0]

    def memcmp(self):
        a, b = self.mem.read(self.R[0], self.R[2]), self.mem.read(self.R[1], self.R[2])
        return next((x - y for x, y in zip(a, b) if x != y), 0)

    def text(self, a):
        return self.mem.read(a, 256).split(b'\0')[0]

    def strncmp(self):
        return int(self.text(self.R[0])[:self.R[2]] != self.text(self.R[1])[:self.R[2]])

    def strcmp(self):
        return int(self.text(self.R[0]) != self.text(self.R[1]))

    def load(self, buffer, address, n, coded=False):
        data = bytes(self.flash[address:address + n])
        if coded and address + n <= 0x4000:          # what is read through the cache comes decoded with the chip's key
            data = enc(data, KEY)
        self.mem.write(buffer, data)
        return n

    def erase(self):
        size = {1: 0x10000, 2: 0x1000, 3: 0x100}[self.R[0]]
        address = self.R[1] & ~(size - 1)
        require(self.v['vm_start'] <= address and address + size <= 0xBE000, f'the stock code erases {address:#x}')
        self.flash[address:address + size] = b'\xff' * size
        self.erased.append(address)
        return 1

    def program(self, buffer, address, n):
        data = self.mem.read(buffer, n)
        require(self.v['vm_start'] <= address and address + n <= 0xBE000, f'the stock code programs {address:#x}')
        for i, byte in enumerate(data):
            self.flash[address + i] &= byte
        self.programmed.append((address, n))
        return n

    def ioctl(self):
        what, pointer = self.R[0], self.R[1]
        require(what in (103, 206), f'ioctl {what}')
        if what == 206:
            self.poke(pointer + 4, self.v['vm_start'])
            self.poke(pointer + 12, 0xBE000 - self.v['vm_start'])
        else:
            self.poke(pointer, CAPACITY)
        return 0

    def vm_state(self):
        if self.R[0]:
            self.poke(self.R[0], self.vm[0])
            self.poke(self.R[1], self.vm[1])
        return 0

    def host_read(self):
        n, data = self.R[2], self.package[self.position:self.position + self.R[2]]
        self.reads.append((self.position, n))
        self.mem.write(self.R[1], data + bytes(n - len(data)))
        self.position += n
        return n

    def host_seek(self):
        self.position = self.R[2]
        return 0

    def notify(self):
        self.notices.append((self.R[0], self.R[1]))
        return 0

    def step(self):
        hook = self.hooks.get(self.pc)
        if hook:
            self.R[0], self.pc = hook() & sim.M, self.rets
            return None
        require(not 0x01C00000 <= self.pc < 0x01C80000, f'code in RAM at {self.pc:#x}')
        return super().step()

    def call(self, function, *arguments, limit=20_000_000):
        for i, value in enumerate(arguments):
            self.R[i] = value
        self.pc, self.rets, self.sp = function, sim.RETURN, 0x01C7F000
        start = self.steps
        while self.pc != sim.RETURN:
            self.step()
            require(self.steps - start < limit, 'the stock code does not come back')
        return self.R[0]

    def update(self):
        """The update service from its first read to the record: (result, place of the loader, place of the record)."""
        result = self.call(self.v['prepare'], 0x5A0D)
        if result:
            return result, None, None
        place, record = self.peek(self.v['G'] + self.v['told']), self.peek(self.v['G'] + self.v['told'] + 4)
        self.call(self.v['request'], 0x5A0D)
        return result, place, record


class Spl(sim.CPU):
    """The pedal's bootloader, from where it has the flash to where it starts something."""
    GLOBALS, CONTEXT = 0x01C06460, 0x01C075E8

    def __init__(self, flash, request=b''):
        super().__init__()
        self.flash, self.key, self.outcome = flash, 0xFFFF, None
        head = enc(bytes(flash[0xA0:0xB0]))
        size, load = struct.unpack_from('<HI', head, 2)
        code = enc(bytes(flash[0xB0:0xB0 + size]))
        require(load == 0x01C02000 and crc16(code) == struct.unpack_from('<H', head, 12)[0], 'this is not the bootloader that is known')
        self.mem.write(load, code)
        self.mem.write(self.GLOBALS + 108, enc(bytes(flash[:32])))
        self.mem.write(self.GLOBALS + 52, struct.pack('<I', CAPACITY))
        self.mem.write(self.CONTEXT + 8, struct.pack('<I', 0x01C07600))
        self.mem.write(0x01C07600, struct.pack('<IIII', 0x180000, 0, 48000000, 0))
        self.mem.write(REQUEST, request)
        self.hooks = {0x1C0307A: self.read, 0x1C02048: lambda: crc16(self.mem.read(self.R[0], self.R[1])), 0x1C031C8: lambda: KEY << 8,
                      0x1C032E4: self.set_key, **{a: lambda: 0 for a in (0x1C024E4, 0x1C02D32, 0x1C03280, 0x1C02064, 0x1C020A6)}}
        self.R[15], self.R[12], self.R[11], self.R[13] = self.GLOBALS, self.CONTEXT, 0x10008, 0x80000000
        self.sp, self.pc = 0x01C05D40, 0x1C04C4A

    def set_key(self):
        self.key = self.R[0] & 0xFFFF
        return 0

    def read(self):
        buffer, address, n = self.R[0], self.R[1], self.R[2]
        data = bytes(self.flash[address:address + n])
        if self.mem.read(self.GLOBALS + 63, 1)[0] == 2:
            data = b''.join(enc(data[o:o + 32], self.key) for o in range(0, n, 32))
        self.mem.write(buffer, data)
        return n

    def step(self):
        if self.pc == 0x1C03310:
            self.key = 0xFFFF
        hook = self.hooks.get(self.pc)
        if hook:
            self.R[0], self.pc = hook() & sim.M, self.rets
            return None
        return super().step()

    def run(self):
        """'application', 'loader', 'download mode' or 'reset'."""
        while True:
            if self.pc == LOADER:
                return 'loader'
            if self.pc == 0x1C04F9E:
                return 'application'
            if self.pc == 0x1C027CA:
                return 'download mode' if self.mem.read(STATUS, 16) == b'usb_update_mode\0' else 'reset'
            self.step()
            require(self.steps < 8_000_000, 'the bootloader does not decide')

    def loaded(self, n):
        return self.mem.read(LOADER, n)


def unit_flash(files, version):
    """A whole flash as the official package leaves it; the rest blank, as the loader and the bootloader see it."""
    flash = bytearray(b'\xff' * CAPACITY)
    flash[:len(files['flash.bin'])] = files['flash.bin']
    require(hashlib.sha256(flash[:0x4000]).hexdigest() == BOOT_SHA256, 'the boot area of the package is another one')
    require(f'{version}\0'.encode() in sfc(bytes(flash[0x4000:VERSIONS[version]['vm_start']])), 'the package is not the version it says')
    return flash


class Engine:
    """The loader's engine, natively, with a simulated flash (firmware/mini_stage/host_server.c)."""

    def __init__(self, folder):
        self.prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
        folder.mkdir(parents=True, exist_ok=True)
        binary = f'{folder.relative_to(ROOT).as_posix()}/host_server'
        done = subprocess.run(self.prefix + ['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-Ifirmware/mini_stage', 'firmware/mini_stage/engine.c',
                                             'firmware/mini_stage/host_server.c', '-o', binary], cwd=ROOT, capture_output=True, text=True)
        require(done.returncode == 0, done.stderr)
        self.process = subprocess.Popen(self.prefix + [binary], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.sequence = 0

    def talk(self, kind, data=b''):
        self.process.stdin.write(kind + struct.pack('<I', len(data)) + data)
        self.process.stdin.flush()
        head = self.process.stdout.read(5)
        require(head[:1] == kind.lower(), head)
        return self.process.stdout.read(struct.unpack('<I', head[1:])[0])

    def ask(self, op, body=b''):
        self.sequence = (self.sequence + 1) & 0xFFFF
        head = struct.pack('<2sBBHH', b'HR', 1, op, self.sequence, len(body)) + body
        reply = self.talk(b'M', head + struct.pack('<I', zlib.crc32(head)))
        return (reply[8], reply[9], reply[10:-4]) if reply else (None, None, b'')

    def install(self, now, want, end=0x82000):
        crc = lambda b: zlib.crc32(bytes(b))
        order = [a for a in range(0x5000, 0xFF000, SECTOR) if (a < end or a >= 0xBF000) and now[a:a + SECTOR] != want[a:a + SECTOR]] + [0x4000]
        begin = struct.pack('<IIHBI', crc(now), crc(want), len(order), 3, 0x214D5241) + (struct.pack('<I', end) if end != 0x82000 else b'')
        for op, body in [(0x10, begin), (0x13, struct.pack('<I', crc(now[0x4000:0x5000])))]:
            status = self.ask(op, body)[0]
            if status != 0:
                return status
        for a in order:
            for at in range(0, SECTOR, 1024):
                status = self.ask(0x11, struct.pack('<H', at) + bytes(want[a + at:a + at + 1024]))[0]
                if status != 0:
                    return status
            status = self.ask(0x12, struct.pack('<III', a, crc(now[a:a + SECTOR]), crc(want[a:a + SECTOR])))[0]
            if status != 0:
                return status
        return self.ask(0x14)[0]

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=20)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--package', type=Path, action='append', required=True)
    parser.add_argument('--no-cuts', action='store_true')
    args = parser.parse_args(argv)
    code, stream, package = ((args.build / n).read_bytes() for n in ('stage-code.bin', 'stage-ota.bin', 'stage-package.bin'))
    report = {'kind': 'mini-boot-check', 'hardware_test': False, 'build': json.loads((args.build / 'report.json').read_text())['build'], 'versions': {}}
    packages = {}
    for path in args.package:
        identity, image, files = official(path)
        require(identity in VERSIONS, f'{identity} is not known here')
        packages[identity] = (image, files)
    last = None
    for version, (image, files) in packages.items():
        flash, steps = unit_flash(files, version), {}
        report['versions'][version] = steps
        # the control: the same package is refused as already installed, another one is stored as it was on the pedal
        result, _, _ = Stock(version, flash, image, 0x710).update()
        require(result == 1, f'{version} takes its own package')
        for other, (other_image, other_files) in packages.items():
            if other == version:
                continue
            m = Stock(version, flash, other_image, 0x710)
            result, place, record = m.update()
            require((result, place, record) == (0, 0xB7000, 0xBCF00), f'{version} with {other}: {result} {place} {record}')
            require(bytes(m.flash[place + 32:place + len(other_files['ota.bin'])]) == other_files['ota.bin'][32:], 'the official loader is not stored whole')
            if (version, other) == ('TANK MINI_011', 'TANK MINI_009'):
                require(m.reads[:10] == RECORDED and len(m.reads) == RECORDED_COUNT, f'not the blocks of the recorded update: {m.reads[:10]} {len(m.reads)}')
                steps['recorded update'] = f'{len(m.reads)} blocks asked for, the first ten and their number as recorded'
        # HyperRig's package, with the VM holding little or much
        for used in (0, 0x300, 0x710, 0x1200, 0x3000, 0x8000):
            m = Stock(version, flash, package, used)
            result, place, record = m.update()
            require(result == 0, f'{version} refuses the package: {result}, status {m.mem.read(m.v["G"] + (38 if version.endswith("011") else 32), 1).hex()}')
            require(m.reads[:3] == [(0, 512), (0x200, 512), (0x400, 512)] and all(a + n <= len(package) + 512 for a, n in m.reads), f'{m.reads}')
            require(bytes(m.flash[place + 32:place + len(stream)]) == stream[32:], 'the loader is not stored whole')
            require(bytes(m.flash[:m.v['vm_start']]) == bytes(flash[:m.v['vm_start']]) and bytes(m.flash[0xBE000:]) == bytes(flash[0xBE000:]), 'the stock code changed more than its VM')
            request = m.mem.read(REQUEST, 80)
            require(bytes(m.flash[record:record + 80]) == request and struct.unpack_from('<I', request, 72)[0] == place, 'the record and the request differ')
            require(Spl(m.flash, request).run() == 'loader', 'the bootloader does not start the loader that was asked for')
            erased = bytearray(m.flash)
            erased[0x4000:0x5000] = b'\xff' * SECTOR
            s = Spl(erased)
            require(s.run() == 'loader' and s.loaded(len(code)) == code, 'the bootloader does not come back to the loader')
            require(struct.unpack('<I', s.mem.read(s.CONTEXT + 4, 4))[0] == 0, 'the place of the application is not zero')
            steps[f'VM {used:#x}'] = {'loader': hex(place), 'record': hex(record), 'blocks': len(m.reads)}
            if used == 0x710:
                require((place, record) == (0xB7000, 0xBCF00), 'not where this pedal had the official one')
                last = (version, bytearray(m.flash), request, place, record)
        version, ready, request, place, record = last
        cases = {}

        def case(name, flash, request=b'', expected=None):
            s = Spl(bytearray(flash), request)
            got = s.run()
            require(got == expected, f'{name}: {got}, not {expected}')
            if got == 'loader':
                require(s.loaded(len(code)) == code and s.R[0] == s.CONTEXT, f'{name}: another loader')
                cases[name] = f"loader, context {s.mem.read(s.CONTEXT, 8).hex()}, stream end {s.R[1]:#x}"
            else:
                cases[name] = got
        erased = bytearray(ready)
        erased[0x4000:0x5000] = b'\xff' * SECTOR
        case('an update asked for, the application whole', ready, request, 'loader')
        case('nothing asked for, the application whole', ready, expected='application')
        case('the header erased', erased, expected='loader')
        case('the header erased and an update asked for', erased, request, 'loader')
        none = bytearray(erased)
        none[record + 6] ^= 1
        case('the header erased, no record: this must never be reached', none, expected='reset')
        broken = bytearray(erased)
        broken[place + 300] ^= 1
        case('the header erased, the loader damaged', broken, expected='download mode')
        case('an update asked for, the loader damaged, the application whole', bytes(broken[:0x4000]) + bytes(ready[0x4000:0x5000]) + bytes(broken[0x5000:]), request, 'application')
        above = bytearray(erased)
        stage.stored(above, next(iter(packages.values()))[1]['ota.bin'][:64] + bytes(100), place=0xB0000, record=0xBDF00)
        case('the header erased, the record of a loader that is gone above ours', above, expected='download mode')
        above[0xBDF06:0xBDF08] = b'\0\0'
        case('the same, with that record made void', above, expected='loader')
        steps['bootloader'] = cases
    if not args.no_cuts:
        version, ready, request, place, record = last
        engine = Engine(args.build.resolve() / 'host')
        try:
            for name, end, changes in (('power cut', 0x82000, (0x4000, 0x4010, 0x5123, 0x40000, 0x81FFF, 0xC0010)),
                                       ('power cut, the window widened to the VM', VERSIONS[version]['vm_start'], (0x4000, 0x5123, 0x81FFF, 0x82000, 0x8C123, 0x94FFF, 0xC0010))):
                if end == 0x82000 and name != 'power cut':
                    continue                                   # a VM that starts at 0x82000 (009): nothing to widen
                want = bytearray(ready)
                for a in changes:
                    want[a] ^= 0x5A
                want[0x4000:0x4020] = ready[0x4000:0x4020]
                want[0x4020] ^= 0x33
                outcomes, cut = {}, 0
                while True:
                    engine.talk(b'F', bytes(ready))
                    engine.talk(b'X', struct.pack('<I', cut + 1))
                    engine.talk(b'P', b'\1')
                    status = engine.install(ready, want, end)
                    left = engine.talk(b'G')
                    got = Spl(bytearray(left)).run()
                    outcomes[got] = outcomes.get(got, 0) + 1
                    header = left[0x4000:0x5000]
                    whole = header == bytes(want[0x4000:0x5000]) and left == bytes(want) or header == bytes(ready[0x4000:0x5000]) and left == bytes(ready)
                    require(got == 'loader' or got == 'application' and (whole or left[0x4000:0x4020] == bytes(want[0x4000:0x4020]) and left[0x5000:] == bytes(want[0x5000:])),
                            f'{name}, operation {cut + 1}: {got} with a flash that is not whole')
                    if status == 0:
                        break
                    require(status is None or status >= 9 or cut == 0, f'{name}: the loader refused ({status})')
                    cut += 1
                require(cut > 80 and bytes(engine.talk(b'G')) == bytes(want), f'{name}: too few operations, or not written')
                report[name] = {'operations': cut, 'the bootloader then started': outcomes, 'application up to': hex(end)}
        finally:
            engine.close()
    report['held'] = True
    print(json.dumps(report, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
