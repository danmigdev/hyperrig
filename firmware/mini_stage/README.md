# HyperRig's loader for the TANK-MINI

A small program in RAM that replaces the pedal's application over USB MIDI: no
download mode, no switch to hold, no administrator rights on the PC. The pedal's
own bootloader starts it, as it starts M-VAVE's update loader, when an update was
asked for, or when it finds no application. It ran on one TANK-MINI: installations
from 011, updates, and the original brought back byte for byte.

## How it gets there

The stock firmware's update service takes a package over MIDI, stores the package's
`ota.bin` at the end of its settings store (VM), writes an update record for the
bootloader, and restarts. HyperRig's package holds `ota.bin` and nothing else. Filler
makes it exactly as long as M-VAVE's, so that the stock firmware does the same flash
work as for an official update; two more bytes give the code the CRC-16 by which the
loader knows its own kind in the flash. Where it is stored depends on how full the VM
is: nothing here assumes a place.

`tools/check_mini_boot.py` runs the update service of 009 and 011 and the pedal's
bootloader, from the person's own copy of M-VAVE's packages, in the simulator: the
package is accepted, the loader stored and started, and started again when the power
went at any flash operation of an installation.

## What it can change

Whole sectors of two windows of the flash: the application, 0x4000 to 0x82000,
and the user area, 0xBF000 to 0xFF000. Since 022, BEGIN may widen the application's
window up to where the pedal's VM begins (0x95000 on a TANK-MINI with 011), never
above 0xA0000: only as the pedal's own directory says (its VM and PRCT records, read
with the chip's key and checked by their own CRC), and only with the way back above
it, the first update record the bootloader finds and the loader it leads to. A header
with no directory, as after an installation cut while it was erased, leaves that to the
bounds and the way back. It never writes the boot area, the place it is stored
in, its update record, the radio data, the last sector, or the flash's protection
bits. `hrs_writable` in `engine.c` is the one place that says so, and both the engine
and the flash driver ask it. The one exception is RETIRE: it clears the mark of an
older update record in the VM, which the bootloader would find before ours.

## An installation

1. The host reads the whole flash and keeps it (READ, checked with CRC).
2. BEGIN: the host gives the checksum of the whole flash. It is right only when
   the host has read all of it, and nothing changed since. It also gives the
   checksum the whole flash shall have at the end.
3. OPEN: the application's header sector is erased. From here on the bootloader
   finds no application and starts this loader again, also after a loss of power.
   A whole application is opened only if that is so: the first update record the
   bootloader finds must lead to a HyperRig loader. Without any record the
   bootloader would reset for ever.
4. For every sector that changes: DATA, DATA, ..., WRITE. Each WRITE names the
   checksum of what the sector holds now and of what it shall hold. The sector is
   erased, found blank, programmed and read back. The header sector is the last
   one, and its first page the last page.
5. FINISH: the whole flash is read and compared with what BEGIN announced.
6. LEAVE: the application starts. It is refused while the application is not whole.

Power lost at any moment leads back to the loader, and the same host run completes
the installation, or goes back to what was there. `test_engine.c` does this for
every single flash operation of an installation.

## Messages

Over USB MIDI ("HyperRig Update") as SysEx: `F0 7D 48 52`, the message with seven
bits to a byte (lowest first), `F7`. A message is

    'H' 'R' 1 op  seq:u16  length:u16  body[length]  crc32:u32      (little endian)

with at most 1,024 data bytes. The reply has the same seq, op + 0x80, and a body of
status, phase and data. A damaged message gets no reply; the host sends it again.
The same message again gets the same reply and is not carried out twice.

| op | body | reply data |
|---|---|---|
| 01 HELLO | | "HRS1", chunk u16, capacity u32, JEDEC u32, chip key u16, status 1, status 2, fast, application found, done u16, sectors u16, touched, windows, build[16], way back, record u32, since 022 the application's window end u32 |
| 02 READ | address u32, length u16 | the bytes |
| 03 CRC | address u32, length u32 | crc32 u32 |
| 10 BEGIN | now crc32, then crc32, sectors u16, windows u8 (1 application, 2 user), "ARM!", since 022 optionally the application's window end u32 | |
| 13 OPEN | crc32 of the header sector | |
| 11 DATA | offset u16, bytes | |
| 12 WRITE | address u32, now crc32, then crc32 | |
| 14 FINISH | | |
| 15 RETIRE | address u32 of the first record the bootloader finds, which is not ours | |
| 20 LEAVE | 1 start the application, 2 the ROM's download mode, 3 restart | |

Phases: 0 ready, 1 armed, 2 opened, 3 done, 4 failed. Status 1 to 8 (message, range,
order, checksum, backup, what the sector holds, no application, no way back) changed
nothing; 9 and above (flash does not answer, another flash, protected, busy, write enable, too long,
wrong read back) end the session, and only LEAVE, HELLO, READ and CRC remain.

With a whole application, nothing touched and no message for five minutes the loader
goes back to the application by itself.

## Building and checking

    python -B tools/build_mini_stage.py --output build/mini-stage-NN
    python -B tools/check_mini_stage_engine.py --output build/mini-stage-mutations-NN
    python -B tools/check_mini_stage_target.py build/mini-stage-NN
    python -B tools/check_mini_boot.py build/mini-stage-NN --package TANK-MINI.fwsc [--package ...]
    python -B tools/check_installer.py build/mini-stage-NN

The first builds it and runs the engine's tests with sanitizers. The second takes one
rule at a time out of the engine: the tests must notice each time. The third runs the
compiled loader in the pi32v2 simulator, with a simulated flash, USB controller and
host. The fourth runs the stock update service and the bootloader. The fifth runs the
installer (`app/installer`) against the engine, natively (`host_server.c`), which can
also answer as a loader from before 022 did (its HELLO and its BEGIN), for the update
that goes once through the original. None of them is a test of a pedal. Give the fourth
both packages, 009 and 011: with 011 last it also cuts an installation whose window is
widened to 011's VM.

The flash driver is `firmware/mini_fast/nor.c`, unchanged; it ran on a TANK-MINI under
the ROM's clocks. `stage.c` lets it run only under the clocks the bootloader sets.

USB: 4C4A:4852. The vendor number is the one of the chip, which the original firmware shows
too (4C4A:C755); the product is the loader's own, and so is HyperRig's (4C4A:5155), so that
no computer takes one for the other or for the original. Neither number is registered to
HyperRig. Loaders and builds before the released 0.2.0 have 1209:0002, 3654:4852 and
3654:5155. Nothing looks for a loader by
these numbers: it is known by its mark in the flash and by asking it, and one that is on a
pedal stays there when HyperRig is updated.
