"""The NOR chip and the SPI controller of the TANK-MINI at register level, for the check of the compiled loader
(check_mini_stage_target.py). A write to any register outside the ones the flash driver may use stops the run. Nothing here opens a device."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'upstream/pi32v2-isa'), str(ROOT / 'upstream/pi32v2-isa/tools/llvm'), str(ROOT / 'upstream/pi32v2-isa/tools/hwtest')]
import sim  # noqa: E402

CAPACITY, START, END, SECTOR = 0x100000, 0x4000, 0x82000, 4096
JEDEC = 0xEB6014
SPI, PD = 0x11C00, 0x500C0
WRITABLE = {0x40200, 0x13000, 0x51020, 0x5101C, PD, PD + 8, PD + 0x1C, PD + 12, PD + 16, PD + 20,
            SPI, SPI + 4, SPI + 8, SPI + 12, SPI + 16}


class Nor:
    """The NOR chip behind the SPI controller, one byte at a time."""

    def __init__(self, data):
        self.data, self.sel, self.n, self.first = bytearray(data), 1, 0, 0
        self.addr, self.page, self.wel, self.busy = 0, b'', False, 0
        self.erases, self.programs, self.baud_of_writes, self.opcodes = [], [], set(), set()

    def select(self, high, baud):
        if high and not self.sel and self.n:
            self.finish(baud)
        if not high and self.sel:
            self.n = 0
            self.page = b''
        self.sel = high

    def finish(self, baud):
        op = self.first
        if op == 0x06 and self.n == 1:
            self.wel = True
        if op == 0x20 and self.n == 4:
            assert self.wel and self.addr % SECTOR == 0 and START <= self.addr < END
            self.data[self.addr:self.addr + SECTOR] = b'\xff' * SECTOR
            self.wel, self.busy = False, 2
            self.erases.append(self.addr)
            self.baud_of_writes.add(baud)
        if op == 0x02 and self.n >= 5:
            assert self.wel and len(self.page) == 256 and self.addr % 256 == 0 and START <= self.addr < END
            for i, byte in enumerate(self.page):
                self.data[self.addr + i] &= byte
            self.wel, self.busy = False, 1
            self.programs.append(self.addr)
            self.baud_of_writes.add(baud)
        self.n = 0

    def shift(self, byte):
        out = 0xFF
        if self.n == 0:
            self.first = byte
            self.opcodes.add(byte)
        op = self.first
        if op == 0x9F and self.n:
            out = (JEDEC >> (16 - 8 * (self.n - 1))) & 255
        elif op == 0x05 and self.n:
            out = (2 if self.wel else 0) | (1 if self.busy else 0)
            self.busy = max(0, self.busy - 1)
        elif op == 0x35 and self.n:
            out = 0
        elif op in (0x03, 0x02, 0x20):
            if 1 <= self.n <= 3:
                self.addr = (byte << 16) if self.n == 1 else self.addr | byte << (8 * (3 - self.n))
            elif self.n >= 4 and op == 0x03:
                out = self.data[(self.addr + self.n - 4) % CAPACITY]
            elif self.n >= 4 and op == 0x02 and len(self.page) < 256:
                self.page += bytes([byte])
        self.n += 1
        return out


class Controller(sim.Memory):
    """Memory whose peripheral window is the SPI controller; every other register write is refused."""

    def __init__(self, nor):
        super().__init__()
        self.nor, self.regs, self.flag, self.receiving, self.baud, self.enc = nor, {}, False, False, 0, 0
        self.dma, self.ram_writes, self.transfers = 0, [], 0

    @staticmethod
    def peripheral(a):
        return 0x10000 <= a < 0x60000

    def read(self, a, n):
        if not self.peripheral(a):
            return super().read(a, n)
        if a == 0x10008:
            value = 0
        elif a == 0x10014:
            value = 0x80
        elif a == SPI:
            value = (self.regs.get(a, 0) & ~0xC000) | (0x8000 if self.flag else 0)
        elif a == 0x13000:
            value = self.enc
        else:
            value = self.regs.get(a, 0)
        return (value & 0xFFFFFFFF).to_bytes(4, 'little')[:n]

    def write(self, a, data):
        if not self.peripheral(a):
            return super().write(a, data)
        if a not in WRITABLE or len(data) != 4:
            raise RuntimeError(f'a write to register {a:#x}')
        value = int.from_bytes(data, 'little')
        if a == 0x13000:
            self.enc = value
        elif a == PD:
            self.nor.select(value & 1, self.baud)
            self.regs[a] = value
        elif a == SPI:
            self.receiving = bool(value >> 12 & 1)
            if value & 0x4000:
                self.flag = False
            self.regs[a] = value & ~0xC000
        elif a == SPI + 4:
            self.baud = value
            self.regs[a] = value
        elif a == SPI + 8:
            out = self.nor.shift(value & 255)
            self.regs[a] = out if self.receiving else 0xFF
            self.flag = True
        elif a == SPI + 12:
            self.dma = value
        elif a == SPI + 16:
            assert self.enc == 2 and self.receiving and 0 < value <= SECTOR and self.baud == 1 and self.nor.first == 3
            super().write(self.dma, bytes(self.nor.data[self.nor.addr:self.nor.addr + value]))
            self.nor.n += value
            self.transfers += 1
            self.flag = True
        else:
            self.regs[a] = value
