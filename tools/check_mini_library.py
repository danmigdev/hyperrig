"""Upload, save, read back, load and delete cab IRs and captures on a built MINI application, in the pi32v2 simulator. Offline.

The application's own console line handler runs from the bytes of app.bin, with its own commands, checks, heap, checksums and
flash guards, for the very lines the editor sends. Replaced are the flash itself (a simulated NOR behind the read, erase and
program calls that run from RAM), the audio pause, the audio engine's start and stop, and the task services, which need the
rest of the pedal. A capture is the one embedded in the application: its own loader checks it and prepares the model. The user area of
the simulated flash starts full of other data, as M-VAVE's firmware leaves it, or is taken from a dump with --flash.

Checked: what the pedal answers, what it holds afterwards, also after a restart, and that nothing outside the chosen slot is
erased or written: not the other slots, not the presets, not the settings sector behind the last IR slot. Wrong uploads are
refused without touching the flash, and power cut at each erase and program of a save leaves every other slot as it was. A
product build: an IR that is uploaded is heard by the cab blocks that play the loaded one, without a slot (irlive.c).

Two shortcuts, for speed: after one upload and save that ran instruction by instruction, the checksums of data are computed
here; and a power cut starts from a copy of the memory after one upload.

This is no hardware test: processor time, the sound, the engine's restart after a load, and the flash under running audio are
not simulated.

Usage, from the repository root:
    python -B tools/check_mini_library.py BUILD [--flash DUMP]
BUILD is an output directory of tools/build_hyperrig_mini_image.py. The exit code is 1 when a check fails.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import random
import re
import sys
import zlib
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import mini_sim as sim  # noqa: E402

BASE, RAM, LINE_AT = 0x02000120, 0x01C00000, 0x01C7E000
USER, USER_END, SETTINGS, SECTOR = 0xBF000, 0xFF000, 0xFE000, 4096
IR_BASE, IR_SLOTS, IR_SAMPLES, IR_LAST = 0xEF000, 8, 4076, 2028
CAPTURE_SLOTS, CAPTURE_MAX = 15, 8192 - 40
MAX_LINE = 190
LINE = 'tuner_and_control_records_console_line'
NOTHING = ('storage_coordination_notify', 'storage_coordination_irq_enter', 'storage_coordination_irq_leave',
           'storage_coordination_wait_ready', 'tempo_slot_services_priority_nest', 'heap_access_lock_enter',
           'heap_access_lock_leave', 'storage_control_ensure', 'storage_control_mode', 'storage_control_activity',
           'storage_control_poll', 'calibration_commands_global_save', 'L02040614', 'L0204074c',
           'mode_and_settings_mode_service', 'L020408d6')      # the engine's start and stop; the priority of a task
AUDIO = ('audio_pause_pause_audio', 'audio_pause_resume_audio')


class PowerCut(Exception):
    pass


class Memory(sim.Memory):
    """The simulator's memory, a page at a time."""

    def read(self, a, n):
        out = bytearray()
        while n:
            at = a & 0xFFF
            part = self._page(a)[at:at + min(n, 4096 - at)]
            out += part
            a, n = a + len(part), n - len(part)
        return bytes(out)

    def write(self, a, data):
        while data:
            at = a & 0xFFF
            part = data[:4096 - at]
            self._page(a)[at:at + len(part)] = part
            a, data = a + len(part), data[len(part):]


class Pedal:
    """One application and the flash it keeps its libraries in."""

    def __init__(self, build, flash):
        self.build = Path(build)
        manifest = json.loads((self.build / 'build-manifest.json').read_bytes())
        self.layout = manifest['application_layout']
        self.app = (self.build / 'app.bin').read_bytes()
        with (self.build / 'link/app.elf').open('rb') as elf:
            self.where = {s.name: s['st_value'] for s in ELFFile(elf).get_section_by_name('.symtab').iter_symbols() if s.name}
        self.flash = flash
        self.restart()

    def restart(self):
        """As the start-up code leaves the memory; the flash stays."""
        cpu = self.cpu = sim.CPU()
        cpu.mem = Memory()
        self.fast = getattr(self, 'fast', False)
        cpu.mem.write(BASE, self.app)
        at = int(self.layout['ram_image_load'], 16) - BASE
        cpu.mem.write(RAM, self.app[at:at + self.layout['ram_image_size']])
        cpu.mem.write(int(self.layout['bss_start'], 16), bytes(self.layout['bss_size']))
        cpu.mem.write(self.where['L01c3743c'] + 24, (0x100000).to_bytes(4, 'little'))    # the flash's size, as its driver finds it
        self.lines, self.erased, self.programmed, self.audio, self.operations, self.cut_at = [], [], [], [], 0, None
        self.services = {self.where[name]: self.nothing for name in NOTHING}
        self.services.update({self.where[name]: (lambda a, name=name: self.audio.append(name)) for name in AUDIO})
        self.services.update({self.where['storage_control_device_read']: self.read,
                              self.where['storage_control_device_erase']: self.erase,
                              self.where['storage_control_device_program']: self.program,
                              self.where['command_services_console_send']: self.send,
                              self.where['link_and_print_send_line']: self.send})
        if 'hyperrig_swap_wait' in self.where:
            self.services[self.where['hyperrig_swap_wait']] = self.sound_turn
        if self.fast:
            self.shortcuts()

    deaf = False

    def sound_turn(self, a):
        """The sound task at the end of a block of the capture, as the task that waits at the gate of mini/product/swap.c sees it: asked,
        it leaves the capture alone. Unless it is deaf: then the waiting task goes the application's way. What the gate says then."""
        gate = self.where['hyperrig_gate']
        if not self.deaf and self.cpu.mem.read(gate, 1) == b'\x01':
            self.cpu.mem.write(gate, b'\x02')
            self.answered()
        return self.cpu.mem.read(gate, 1)[0]

    def answered(self):
        pass

    def nothing(self, a):
        return 0

    def checksum(self, a):
        return zlib.crc32(self.cpu.mem.read(a[0], a[1]))

    def crc_update(self, a):
        return zlib.crc32(self.cpu.mem.read(a[1], a[2]), a[0] ^ 0xFFFFFFFF) ^ 0xFFFFFFFF

    def shortcuts(self):
        self.fast = True
        self.services.update({self.where['record_helpers_checksum']: self.checksum, self.where['preset_storage_checksum']: self.checksum,
                              self.where['preset_storage_crc_update']: self.crc_update})

    def send(self, a):
        self.lines += self.cpu.mem.read(a[0], a[1]).decode('utf-8', 'replace').splitlines()
        return a[1]

    def read(self, a):
        assert a[1] + a[2] <= len(self.flash)
        self.cpu.mem.write(a[0], bytes(self.flash[a[1]:a[1] + a[2]]))
        return a[2]

    def operation(self, address, size):
        assert USER <= address and address + size <= USER_END, f'the pedal writes {address:#x}'
        self.operations += 1
        return self.operations == self.cut_at

    def erase(self, a):
        address = a[1] & ~(SECTOR - 1)
        cut = self.operation(address, SECTOR)
        self.flash[address:address + (SECTOR // 2 if cut else SECTOR)] = b'\xff' * (SECTOR // 2 if cut else SECTOR)
        self.erased.append(address)
        if cut:
            raise PowerCut
        return 0

    def program(self, a):
        cut = self.operation(a[1], a[2])
        data = self.cpu.mem.read(a[0], a[2] // 2 if cut else a[2])
        assert (a[1] & 255) + a[2] <= 256, 'a program over a page boundary'
        for i, byte in enumerate(data):
            self.flash[a[1] + i] &= byte
        self.programmed.append((a[1], a[2]))
        if cut:
            raise PowerCut
        return a[2]

    def line(self, text, limit=60_000_000):
        """One console line; what the pedal answers."""
        raw = text.encode('utf-8')
        assert len(raw) <= MAX_LINE, len(raw)
        self.lines, self.erased, self.programmed, self.audio = [], [], [], []
        cpu = self.cpu
        cpu.mem.write(LINE_AT, raw + b'\0')
        cpu.R[0], cpu.rets, cpu.pc, cpu.sp, start = LINE_AT, sim.RETURN, self.where[LINE], sim.STACK_TOP, cpu.steps
        fatal = self.where['storage_fault_fatal']
        while cpu.pc != sim.RETURN:
            service = self.services.get(cpu.pc)
            if service:
                cpu.R[0] = (service(list(cpu.R[:4])) or 0) & sim.M
                cpu.pc = cpu.rets
                continue
            if cpu.pc == fatal:
                raise RuntimeError(f'{text[:40]}: the application stops itself, called from {cpu.rets:#x}')
            cpu.step()
            if cpu.steps - start > limit:
                raise RuntimeError(f'{text[:40]}: too many steps')
        return self.lines

    # as the editor does it
    def pieces(self, prefix, data):
        size = (MAX_LINE - len(prefix) - 2 - len(str(len(data)))) // 2
        for at in range(0, len(data), size):
            part = data[at:at + size]
            if self.line(f'{prefix} {at} {part.hex()}') != [f'OK {prefix} {at} {len(part)}']:
                return False
        return True

    def upload_ir(self, samples, gain=-1500, rate=48, crc=None):
        data = b''.join(s.to_bytes(2, 'little', signed=True) for s in samples)
        first = self.line(f'IRBEGIN {len(samples)} {gain} {rate}')
        if first != [f'OK IRBEGIN {len(samples)}'] or not self.pieces('IRB', data):
            return self.lines
        return self.line(f'IREND {zlib.crc32(data) if crc is None else crc:08x}')

    def upload_capture(self, data, crc=None):
        if self.line(f'LDBEGIN {len(data)}') != [f'OK LDBEGIN {len(data)}'] or not self.pieces('LDB', data):
            return self.lines
        return self.line(f'LDEND {zlib.crc32(data) if crc is None else crc:08x}', limit=200_000_000)

    def embedded(self):
        manifest = json.loads((self.build / 'build-manifest.json').read_bytes())['embedded_capture']
        at = int(manifest['address'], 16) - BASE
        return bytes(self.app[at:at + manifest['bytes']])

    def library(self, kind):
        got = {}
        for text in self.line(kind):
            m = re.match(r"(?:IRS|CAP) (\d+) (\d+) '(.*)'", text)
            if m:
                got[int(m.group(1))] = (int(m.group(2)), m.group(3))
        return got, self.lines[-1]

    def slot(self, command, slot):
        """The stored bytes of a slot, read as the editor reads them."""
        head = re.match(r"\S+ \d+ len=(\d+) crc=([0-9a-f]{8})", self.line(f'{command} {slot}')[0])
        if not head:
            return None
        data = b''
        while len(data) < int(head.group(1)):
            m = re.match(rf'{command} {slot} {len(data)} (\d+) ([0-9a-f]{{8}}) (\S+)$', self.line(f'{command} {slot} {len(data)}')[0])
            part = base64.b64decode(m.group(3))
            assert len(part) == int(m.group(1)) and zlib.crc32(part) == int(m.group(2), 16)
            data += part
        assert zlib.crc32(data) == int(head.group(2), 16)
        return data


def foreign_flash():
    """A flash whose user area holds what is not HyperRig's, with blank and half-blank sectors among it."""
    rng = random.Random(3)
    flash = bytearray(rng.randbytes(0x100000))
    for address in range(USER, USER_END, 3 * SECTOR):
        flash[address:address + SECTOR] = b'\xff' * SECTOR
    return flash


def wave(count, seed):
    rng = random.Random(seed)
    return [round(rng.uniform(-32767, 32767) * 0.9992 ** i) for i in range(count)]


def outside(now, before, *ranges):
    """The sectors that changed outside the given ranges."""
    return [hex(a) for a in range(0, len(now), SECTOR)
            if now[a:a + SECTOR] != before[a:a + SECTOR] and not any(lo <= a < hi for lo, hi in ranges)]


def ir_range(slot):
    return IR_BASE + slot * 2 * SECTOR, (IR_BASE + (slot + 1) * 2 * SECTOR if slot < 7 else SETTINGS)


def check_irs(build, flash, row):
    pedal = Pedal(build, flash)
    before = bytes(flash)
    had, end = pedal.library('ILIST')
    row('no IR at first', (had, end) == ({}, 'ILIST end current=-1 slots=8'), end)

    # one save instruction by instruction; from here on the checksums of data are computed here
    small = wave(150, 5)
    pedal.upload_ir(small)
    answer = pedal.line('ISAVE 5 Small')
    row('a short IR, every instruction of it', answer == ["ISAVE ok 5 'Small' 150 samples fs=48"] and
        pedal.slot('IREAD', 5) == b''.join(s.to_bytes(2, 'little', signed=True) for s in small), answer)
    pedal.line('IDEL 5')
    pedal.shortcuts()
    before = bytes(flash)
    samples = wave(IR_SAMPLES, 1)
    answer = pedal.upload_ir(samples)
    row('an IR of 4,076 samples is taken', answer == [f'IR ok {IR_SAMPLES} samples gain -1500 mdB fs 48'] and bytes(flash) == before, answer)
    answer = pedal.line('ISAVE 0 Cab one')
    lo, hi = ir_range(0)
    good = answer == [f"ISAVE ok 0 'Cab one' {IR_SAMPLES} samples fs=48"]
    row('it is saved in slot 1, and in no other place', good and pedal.erased == [lo, lo + SECTOR] and
        all(lo <= a and a + n <= hi for a, n in pedal.programmed) and not outside(flash, before, (lo, hi)), answer)
    row('its header is written last', pedal.programmed[-1] == (lo, 40) and all(a >= lo + 40 for a, _ in pedal.programmed[:-1]), pedal.programmed[-1])
    row('the audio pauses for it and runs again', pedal.audio == list(AUDIO) * (len(pedal.audio) // 2) and pedal.audio, len(pedal.audio))
    data = b''.join(s.to_bytes(2, 'little', signed=True) for s in samples)
    row('it reads back as it was sent', pedal.slot('IREAD', 0) == data, len(data))
    pedal.restart()
    listed = pedal.library('ILIST')[0]
    row('it is there after a restart', listed == {0: (len(data), 'Cab one')}, listed)
    row('it loads', pedal.line('ILOAD 0') == ['ILOAD ok 0'] and not pedal.erased and not pedal.programmed, pedal.lines)
    row('an empty slot does not', pedal.line('ILOAD 3')[0].startswith('ERR ILOAD'), pedal.lines)

    for slot in range(1, 7):
        mark = bytes(flash)
        lo, hi = ir_range(slot)
        pedal.upload_ir(wave(IR_SAMPLES, slot + 1), gain=-60000 + slot)
        answer = pedal.line(f'ISAVE {slot} {"Cab " + "x" * 18 + str(slot)}')
        row(f'slot {slot + 1}', answer[0].startswith(f'ISAVE ok {slot} ') and set(pedal.erased) == {lo, lo + SECTOR} and
            not outside(flash, mark, (lo, hi)), answer)
    mark = bytes(flash)
    answer = pedal.line('ISAVE 7 Too long')
    row('slot 8 refuses a long IR, untouched', answer[0].startswith('ERR ISAVE') and bytes(flash) == mark and not pedal.erased, answer)
    pedal.upload_ir(wave(IR_LAST, 9))
    answer = pedal.line('ISAVE 7 Short')
    lo, hi = ir_range(7)
    row('slot 8 takes 2,028 samples and leaves the settings behind it', answer == [f"ISAVE ok 7 'Short' {IR_LAST} samples fs=48"] and
        pedal.erased == [lo] and not outside(flash, mark, (lo, hi)) and flash[SETTINGS:USER_END] == mark[SETTINGS:USER_END], answer)
    listed = pedal.library('ILIST')
    row('all eight are listed', sorted(listed[0]) == list(range(8)) and listed[1] == 'ILIST end current=7 slots=8', listed[1])
    mark = bytes(flash)
    answer = pedal.line('IDEL 2')
    lo, hi = ir_range(2)
    row('deleting slot 3 erases its first sector only', answer == ['IDEL ok 2'] and pedal.erased == [lo] and not pedal.programmed and
        not outside(flash, mark, (lo, lo + SECTOR)) and sorted(pedal.library('ILIST')[0]) == [0, 1, 3, 4, 5, 6, 7], answer)
    data = b''.join(s.to_bytes(2, 'little', signed=True) for s in wave(IR_SAMPLES, 2))
    row('the others still read back', pedal.slot('IREAD', 1) == data and pedal.slot('IREAD', 2) is None, 'slots 2 and 3')
    pedal.upload_ir(wave(1000, 11))
    mark = bytes(flash)
    answer = pedal.line('ISAVE 4 Replaced')
    lo, hi = ir_range(4)
    row('a slot in use is replaced', answer[0].startswith("ISAVE ok 4 'Replaced'") and not outside(flash, mark, (lo, hi)) and
        pedal.library('ILIST')[0][4] == (2000, 'Replaced'), answer)

    # what is wrong is refused, and nothing is touched
    pedal.restart()
    mark = bytes(flash)
    refused = {}
    for text in ('IRBEGIN 4097 0 48', 'IRBEGIN -1 0 48', 'IRBEGIN 4 0 44', 'IRBEGIN 4 20001 48', 'IRBEGIN 4 -60001 48',
                 'IREND 00000000', 'ISAVE 8 x', 'ISAVE -1 x', 'ISAVE', 'IDEL 8', 'IDEL -1', 'ILOAD 8', 'ILOAD -1', 'IREAD 8', 'FXIR 0 0',
                 'ISAVE 0 nothing uploaded'):
        answer = pedal.line(text)
        refused[text] = answer
        if not (answer and answer[0].startswith('ERR')) or pedal.erased or pedal.programmed:
            row(f'refused: {text}', False, answer)
    row('wrong commands are refused', all(a and a[0].startswith('ERR') for a in refused.values()) and bytes(flash) == mark, len(refused))
    # a piece is answered with how many of its bytes were taken: the editor stops when that is not all of them
    wrong = []
    for text, taken in (('IRB 8 0000', 0), ('IRB 0 000', 1), ('IRB 0 zz', 0), ('IRB 6 00000000', 2), ('IRB 4000000000 0000', 0), ('IRB -2 0000', 0)):
        pedal.line('IRBEGIN 4 0 48')
        answer = pedal.line(text)
        wrong.append(answer[0].startswith('ERR') or answer[0].split()[-1] == str(taken) or answer)
    pedal.line('IRBEGIN 4 0 48')
    wrong.append(pedal.line('IREND 12345678')[0].startswith('ERR IREND crc') or pedal.lines)
    row('wrong pieces and checksums are refused', all(w is True for w in wrong) and bytes(flash) == mark, wrong)
    row('an upload is dropped on request', pedal.line('IRBEGIN 4 0 48') == ['OK IRBEGIN 4'] and pedal.line('IRBEGIN 0 0 48') == ['OK IRBEGIN 0'] and
        pedal.line('IRB 0 0000') == ['OK IRB 0 0'] and pedal.line('IREND 00000000')[0].startswith('ERR'), pedal.lines)

    # power cut at each operation of a save
    rest = {slot: pedal.slot('IREAD', slot) for slot in (0, 1, 3, 5, 6, 7)}
    total, cuts = None, 0
    source = Pedal(build, bytearray(mark))
    source.shortcuts()
    source.upload_ir(wave(IR_SAMPLES, 40))
    pages, state = copy.deepcopy(source.cpu.mem.pages), list(source.cpu.R)
    lo, hi = ir_range(4)
    for at in range(1, 100):
        trial = source
        trial.flash[:] = mark
        trial.restart()
        trial.cpu.mem.pages, trial.cpu.R[:] = copy.deepcopy(pages), state
        trial.cut_at, trial.operations = at, 0
        try:
            trial.line('ISAVE 4 Cut')
            total = trial.operations
            break
        except PowerCut:
            cuts += 1
        if outside(trial.flash, mark, (lo, hi)):
            row(f'power cut at operation {at}', False, outside(trial.flash, mark, (lo, hi)))
        trial.restart()
        listed = trial.library('ILIST')[0]
        whole = trial.slot('IREAD', 4) if 4 in listed else None
        if 4 in listed and listed[4][1] == 'Cut' and whole is None or sorted(set(listed) - {4}) != sorted(rest):
            row(f'power cut at operation {at}', False, listed)
        if at % 9 == 1 and any(trial.slot('IREAD', s) != d for s, d in rest.items()):
            row(f'power cut at operation {at}: another slot', False, listed)
    row('power cut at each operation of a save leaves the other slots', total == cuts and cuts > 30, f'{cuts} operations')


def capture_range(slot):
    base = 0xDF000 + slot * 2 * SECTOR if slot < 8 else 0xCF000 + (slot - 8) * 2 * SECTOR
    return base, base + 2 * SECTOR


def check_captures(build, flash, row):
    pedal = Pedal(build, flash)
    before = bytes(flash)
    capture = pedal.embedded()
    loaded = "LOAD rc=0 name='A2' layers=23 channels=3 audio=0 engine=A2L ms=0"
    had, end = pedal.library('CLIST')
    row('no capture at first', (had, end) == ({}, 'CLIST end current=-1 slots=15'), end)
    answer = pedal.upload_capture(capture)
    row('a capture is taken, checked and prepared', answer == [loaded] and bytes(flash) == before, answer)
    pedal.shortcuts()
    answer = pedal.line('CSAVE 0 My Amp')
    lo, hi = capture_range(0)
    row('it is saved in slot 1, and in no other place', answer == [f"CSAVE ok 0 'My Amp' {len(capture)} B"] and pedal.erased == [lo, lo + SECTOR] and
        not outside(flash, before, (lo, hi)), answer)
    row('its header is written last', pedal.programmed[-1] == (lo, 40) and all(lo + 40 <= a and a + n <= hi for a, n in pedal.programmed[:-1]),
        pedal.programmed[-1])
    row('it reads back as it was sent', pedal.slot('CREAD', 0) == capture, len(capture))
    pedal.restart()
    listed = pedal.library('CLIST')[0]
    row('it is there after a restart', listed == {0: (len(capture), 'My Amp')}, listed)
    row('it loads', pedal.line('CLOAD 0', limit=200_000_000) == ['CLOAD ok 0 audio=0'] and not pedal.erased and not pedal.programmed, pedal.lines)
    row('an empty slot does not', pedal.line('CLOAD 3')[0].startswith('ERR CLOAD'), pedal.lines)
    for slot in range(1, CAPTURE_SLOTS):
        mark = bytes(flash)
        lo, hi = capture_range(slot)
        answer = pedal.line(f'CSAVE {slot} Amp {slot}')
        row(f'slot {slot + 1}', answer == [f"CSAVE ok {slot} 'Amp {slot}' {len(capture)} B"] and set(pedal.erased) == {lo, lo + SECTOR} and
            not outside(flash, mark, (lo, hi)), answer)
    row('presets, their journal, IRs and settings are as they were', all(flash[a:b] == before[a:b] for a, b in
        ((0, 0xCF000), (0xDD000, 0xDF000), (IR_BASE, 0x100000))), 'four areas')
    listed = pedal.library('CLIST')
    row('all fifteen are listed', sorted(listed[0]) == list(range(CAPTURE_SLOTS)) and listed[1] == 'CLIST end current=14 slots=15', listed[1])
    mark = bytes(flash)
    lo, hi = capture_range(4)
    answer = pedal.line('CTRIM 4 -2.5')
    row('a trim is written into its own slot', answer[0].startswith('CTRIM ok slot=4 trim=-2.5 saved=1') and not pedal.erased and
        pedal.programmed and all(lo <= a and a + n <= hi for a, n in pedal.programmed) and not outside(flash, mark, (lo, hi)), answer)
    row('a trim of the one that plays is not written', pedal.line('CTRIM live 1.5')[0].startswith('CTRIM ok') and not pedal.programmed, pedal.lines)
    pedal.restart()
    row('the trim is kept', "CAP 4 4892 'Amp 4' trim=-2.5" in pedal.line('CLIST') and pedal.slot('CREAD', 4) == capture, pedal.lines[:1])
    mark = bytes(flash)
    answer = pedal.line('CDEL 6')
    lo, hi = capture_range(6)
    row('deleting slot 7 erases its first sector only', answer == ['CDEL ok 6'] and pedal.erased == [lo] and not pedal.programmed and
        not outside(flash, mark, (lo, lo + SECTOR)) and sorted(pedal.library('CLIST')[0]) == [k for k in range(15) if k != 6], answer)
    pedal.upload_capture(capture)
    mark = bytes(flash)
    lo, hi = capture_range(9)
    answer = pedal.line('CSAVE 9 Replaced')
    row('a slot in use is replaced', answer[0].startswith("CSAVE ok 9 'Replaced'") and not outside(flash, mark, (lo, hi)) and
        pedal.library('CLIST')[0][9] == (len(capture), 'Replaced'), answer)

    # what is wrong is refused, and nothing is touched
    mark = bytes(flash)
    wrong = []
    for text in ('LDBEGIN 0', 'LDBEGIN 8193', 'LDBEGIN -1', 'LDBEGIN', 'CSAVE 15 x', 'CSAVE -1 x', 'CSAVE', 'CLOAD 15', 'CLOAD -1', 'CDEL 15', 'CDEL -1',
                 'CREAD 15', 'CTRIM 15 0', 'CTRIM 6 0', 'CTRIM x 0', 'LDEND 00000000'):
        answer = pedal.line(text, limit=200_000_000)
        wrong.append(True if answer and answer[0].startswith('ERR') and not pedal.erased and not pedal.programmed else (text, answer))
    row('wrong commands are refused', all(w is True for w in wrong) and bytes(flash) == mark, [w for w in wrong if w is not True] or len(wrong))
    pedal.line(f'LDBEGIN {len(capture)}')
    taken = []
    for text, want in (('LDB 8192 0000', 0), ('LDB 0 000', 1), ('LDB 0 zz', 0), (f'LDB {len(capture) - 1} 0000', 1), ('LDB 4000000000 00', 0)):
        answer = pedal.line(text)
        taken.append(True if answer[0].startswith('ERR') or answer[0].split()[-1] == str(want) else (text, answer))
    row('pieces outside are not taken', all(w is True for w in taken), [w for w in taken if w is not True] or len(taken))
    bad = bytearray(capture)
    bad[200] ^= 1
    refusals = {'wrong checksum': pedal.upload_capture(capture, crc=1), 'a changed byte': pedal.upload_capture(bytes(bad)),
                'cut short': pedal.upload_capture(capture[:2000]), 'another file': pedal.upload_capture(random.Random(5).randbytes(3000)),
                'an AM2 capture': pedal.upload_capture(b'AM2\0' + bytes(6200)), 'four bytes': pedal.upload_capture(b'A2L1')}
    row('wrong captures are refused', all(a and ('rc=-' in a[0] or a[0].startswith('ERR')) for a in refusals.values()) and bytes(flash) == mark,
        {k: v for k, v in refusals.items()})
    row('and the pedal goes on', pedal.upload_capture(capture) == [loaded] and pedal.line('CLOAD 0', limit=200_000_000)[0].startswith('CLOAD ok 0'), pedal.lines)

    # power cut at each operation of a save
    rest = [k for k in range(15) if k not in (6, 9)]
    pedal.upload_capture(capture)
    pages, state = copy.deepcopy(pedal.cpu.mem.pages), list(pedal.cpu.R)
    lo, hi = capture_range(9)
    total, cuts = None, 0
    for at in range(1, 100):
        pedal.flash[:] = mark
        pedal.restart()
        pedal.cpu.mem.pages, pedal.cpu.R[:] = copy.deepcopy(pages), state
        pedal.cut_at, pedal.operations = at, 0
        try:
            pedal.line('CSAVE 9 Cut')
            total = pedal.operations
            break
        except PowerCut:
            cuts += 1
        if outside(pedal.flash, mark, (lo, hi)):
            row(f'power cut at operation {at}', False, outside(pedal.flash, mark, (lo, hi)))
        pedal.restart()
        listed = pedal.library('CLIST')[0]
        if sorted(set(listed) - {9}) != rest or 9 in listed and (listed[9][1] != 'Cut' or pedal.slot('CREAD', 9) != capture):
            row(f'power cut at operation {at}: the list', False, listed)
    row('power cut at each operation of a save leaves the other slots', total == cuts and cuts > 20, f'{cuts} operations')


class Playing(Pedal):
    """With the memory that blocks are made in, so that the cab blocks of a chain can be looked at."""
    ALLOCATE, RELEASE, ARENA, ARENA_END = 0x01C60000, 0x01C60010, 0x01D00000, 0x01F00000
    room = True

    def restart(self):
        super().restart()
        self.next, self.released = self.ARENA, []
        self.services.update({self.ALLOCATE: self.allocate, self.RELEASE: lambda a: self.released.append(a[0])})
        engine = self.where['L01c32db0']
        self.cpu.mem.write(engine + 48, (400_000).to_bytes(4, 'little'))          # the ticks of a block of sound: there is room here
        self.cpu.mem.write(engine + 52, self.ALLOCATE.to_bytes(4, 'little') + self.RELEASE.to_bytes(4, 'little'))

    def allocate(self, a):
        at = self.next
        if not self.room or at + a[0] > self.ARENA_END:
            return 0
        self.next = at + a[0] + 63 & ~63
        return at

    def block(self, number):
        """What a cab block plays: the length it uses of its IR, and the numbers made from it."""
        word = lambda at: int.from_bytes(self.cpu.mem.read(at, 4), 'little')
        base = self.where['L01c2c220'] + 480 * number
        made = word(base + 288)
        return word(base + 292), zlib.crc32(self.cpu.mem.read(made + 2616, 1032 * word(made + 4))) if made else None


def check_heard(build, flash, row):
    """An IR that is uploaded is heard at once by the cab blocks that play the loaded one, without a slot; and the one before comes back."""
    pedal = Playing(build, flash)
    pedal.shortcuts()
    mark = bytes(flash)
    first, second, short = wave(900, 21), wave(1200, 22), wave(300, 23)
    pedal.upload_ir(first)
    pedal.line('ISAVE 0 First')
    pedal.upload_ir(second)
    pedal.line('ISAVE 1 Second')
    mark = bytes(flash)
    pedal.restart()
    pedal.line('ILOAD 0')
    made = [pedal.line(text)[0] for text in ('FXA Q 99 ir', 'FXP 0 3 85', 'FXA P 99 ir', 'FXP 1 3 85', 'FXA Q 99 ir', 'FXP 2 3 85', 'FXIR 2 1', 'FXA Q 99 boost')]
    a = [pedal.block(k) for k in range(3)]
    row('three cab blocks: two with the loaded IR, one with its own', a[0] == a[1] != a[2] and (a[0][0], a[2][0]) == (900, 1200), [made, a])
    answer = pedal.upload_ir(short)
    b = [pedal.block(k) for k in range(3)]
    row('an uploaded IR is heard at once where the loaded one plays', answer[0].startswith('IR ok 300') and b[0] == b[1] and b[0][0] == 300, [answer, b])
    row('a block with its own IR keeps it', b[2] == a[2], b[2])
    row('it has no slot, and nothing is written', pedal.library('ILIST')[1] == 'ILIST end current=-1 slots=8' and bytes(flash) == mark, None)
    pedal.line('ILOAD 0')
    row('the one before comes back, the same numbers', [pedal.block(k) for k in range(3)] == a, [pedal.block(k) for k in range(3)])
    pedal.upload_ir(short)
    answer = pedal.line('FXIR 2 -1'), pedal.block(2)
    pedal.line('FXIR 2 1')
    row('a block with its own plays the uploaded one when it is told to, and its own again', answer == (['FXIR ok 2 -1'], b[0]) and pedal.block(2) == a[2], [answer, pedal.block(2)])
    pedal.line('ILOAD 0')
    pedal.upload_ir(second)
    c = pedal.block(0)
    pedal.line('ISAVE 2 Kept')
    row('it goes on when it is saved', c == pedal.block(0) and c[0] == 1200 and pedal.library('ILIST')[1].startswith('ILIST end current=2'), c)
    pedal.room = False
    answer = pedal.upload_ir(short)
    d = pedal.block(0)
    row('without memory for a second one it is made in the place of the one before', answer[0].startswith('IR ok') and d[0] == 300 and d[1] == b[0][1], [answer, d, b[0]])
    answer = pedal.upload_ir(second)
    row('one that is longer than that place: the block goes on as it was', answer[0].startswith('IR ok') and pedal.block(0) == d, [answer, pedal.block(0), d])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--flash', type=Path)
    parser.add_argument('--only', choices=('irs', 'captures', 'heard'))
    args = parser.parse_args(argv)
    rows = []

    def row(name, good, seen):
        rows.append({'check': name, 'held': bool(good), 'seen': str(seen)[:200]})

    product = json.loads((args.build / 'build-manifest.json').read_bytes()).get('product')
    for name, part in (('irs', check_irs), ('captures', check_captures), ('heard', check_heard)):
        if args.only in (None, name) and (name != 'heard' or product):
            part(args.build, bytearray(args.flash.read_bytes()) if args.flash else foreign_flash(), row)
    held = all(r['held'] for r in rows)
    print(json.dumps({'kind': 'mini-library-check', 'build': args.build.name, 'hardware_test': False, 'held': held, 'checks': rows}, indent=1))
    return 0 if held else 1


if __name__ == '__main__':
    raise SystemExit(main())
