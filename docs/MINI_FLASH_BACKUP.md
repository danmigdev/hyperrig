# RAM-resident MINI NOR reader

`firmware/mini/recovery_reader/` contains a plugin for the normal AC791N ROM
USB callback. It reads NOR through SPI PIO, without DMA, display, P33, efuse
access, clock changes, reset, flash programming, or flash erasure.
**Loading the plugin alone does not access peripherals:** it registers its
handler and returns control to ROM. SPI access occurs only when the client
requests `FC72`.

The plugin should be used after verifying the ROM ABI on the MINI with a probe
that does not use SPI. The builder report describes offline checks; physical
observations are recorded separately.

**Complete backup succeeded on 15 November 2026:** two identical 1,048,576-byte
files, SHA-256
`72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180`.
All 4,096 reads of 512 bytes had verified status and counters. Boot,
configuration, and application CRCs are valid; the entire prefix `[0,0x82000)`
matches stock 009 byte for byte. VM, BTIF, USR, and key_mac also match between
the two acquisitions. The files are in
`artifacts/my-mini-flash/20261115-paced-resume/`, excluded from Git. The pedal
then returned to `TANK MINI_009` with unchanged presets.

The physical test of 15 November 2026 is recorded separately in
[mini-hardware-rom.json](../research/mini-hardware-rom.json): the MINI ran the
reader in slot `0x01C28000`, responded with `HYRN`, and returned JEDEC `EB6014`
(1 MiB), `SYS_DIV=0`, and `CLK_CON2=0x80` in ROM. In the first attempt, 260
512-byte blocks matched stock, totaling 133,120 bytes; the next command, at
offset `0x20800`, failed with Windows error 31. Of that partial read, 131,072
bytes were persisted. The old trace does not measure the error's duration and
therefore does not establish its cause. The subsequent RAM reset returned the
pedal to `TANK MINI_009` with the same presets. No NOR write command was sent.
The subsequent complete attempt succeeded after a hub reset for a new
enumeration error and with a 5 ms pause before commands. The first error's cause
has not been isolated: these results do not demonstrate that pacing alone
resolved it. No command was automatically retried, and no ambiguous jump was repeated.

## Compilation

```
python tools/verify_mini_recovery_reader.py
```

The command does not open devices. It compiles and runs ASan/UBSan host tests,
then generates the following in `build/mini-flash-reader/`:

* `hyperrig-reader-01c20000.{elf,bin,map,asm}`;
* `hyperrig-reader-01c28000.{elf,bin,map,asm}`.

Each flat binary contains 2,308 bytes; code, data, and private state occupy
2,884 bytes of a single 32 KiB slot. Entry is the flat binary's first byte.
The linker and ELF audit reject unresolved symbols, runtime relocations, and
allocations outside the slot. No new stack is initialized: the ROM stack,
IRQs, and C return are preserved. Only private state is cleared.

Exact hashes and results are in `research/mini-flash-reader.json`. These are
not application images, FWSC packages, or bootloaders.

## HYRN v1 protocol

The entry ABI is a structure of three 32-bit target pointers:
`send(data,count)`, `receive(data,count)`, and a pointer to the handler slot.
The handler receives the 31-byte USB CBW and a 16-byte answer; it returns `1`
for handled commands. All four HYRN commands are IN only, with a 16-byte CDB
and LUN0. The client must verify identity and slot before enabling any SPI request.

| CDB | Response/action |
|---|---|
| `FC70` | 16 bytes: echoed op at 0..1, `HYRN` at 2..5, version 1 at 6, flags 3=RO\|PIO at 7, BE32 slot at 8, BE32 slot size at 12. No MMIO. |
| `FC72` | Initializes SPI once and reads JEDEC. 16-byte response: echoed op, error at 2, initialized at 3, JEDEC at 4..6, baud 15 at 7, BE32 capacity at 8, zero at 12..15. |
| `FD71` | BE32 NOR offset at CDB+2, BE16 length at CDB+6. CBW requested length must match, between 1 and 512. Returns exactly those bytes. |
| `FC73` | 16-byte status: echoed op, first error at 2, initialized at 3, BE32 SYS_DIV snapshot at 4, BE32 CLK_CON2 at 8, BE32 successful-read byte counter at 12. No new MMIO. |

Errors are sticky: `1` clock, `2` SPI timeout, `3` JEDEC/capacity, `4` framing,
`5` range, `6` reader not initialized, `7` USB callback, `8` forbidden private
command. The plugin provides no command to clear them. An error during `FD71`
returns `FF` to maintain the data phase and does not increment the counter.
**The client must query FC73 after every block, require error 0, and require a
counter increase exactly equal to the requested length.** Returned bytes alone
do not establish a read.

A nonnegative return from the ROM `send` callback is accepted; negative values
produce error 7. The exact meaning of a positive/zero value remains a ROM
property to observe. The client checks length, status, and counter regardless.

Standard SCSI operations and the three ROM RAM commands `FB06`, `FD07`, `FB08`
remain delegated to ROM. Other private commands, including old erase, write,
and display commands, are consumed and rejected: they are not delegated to
ROM. The client must keep a HYRN allowlist separate from M-Flasher's. A
malformed transfer exceeding 512 bytes is handled only up to 512 bytes; it may
require BOT/ROM recovery and must not be issued by the client.

## Prerequisites and transactions

Before any MMIO write, `FC72` captures:

* `SYS_DIV`, address `0x10008`, fields HSB17:16 and LSB10:8, mask `0x30700`;
* `CLK_CON2`, address `0x10014`, low8.

It accepts only `(CLK_CON2 low8, SYS_DIV mask)` pairs `(0x80,0)` and
`(0x40,0x100)`, recognized by the reference AC791N ROM loader. Every subsequent
read rechecks that these fields have not changed. An unknown case is rejected
before writing peripherals. The reader does not apply the clock transition
performed by `hal_clock_b`; it preserves the inherited state. Matching fields
does not measure a physical frequency. SPI baud is 15, and waits are instruction
counts, not claimed microsecond durations.

The SPI sequence uses pins attested by MINI `uboot.boot`:

| MINI evidence | Operation |
|---|---|
| `0x01C02CA6..2CC6` | Manual CS on PD0. |
| `0x01C02CD0..2D02` | SPI0 buffer `0x11C08`, direction bit 12, completion bit 15, clear bit 14. |
| `0x01C02D48..2DAE` | SFC disabled; SPI control `0x28`; mux `0x51020` bit 1 and `0x5101C` bit 5 cleared; PD4/5 output, PD4 drive; PD1 input; PD2/3 used for quad. |

The reader configures PD0 high, PD4/5 low, PD2/3 high, and PD1 as a digital
input without pulls; it disables SFC/peripheral ENC, enables SPI0, and sets
baud 15. These are volatile changes needed to read NOR; the entire plugin must
reside in RAM. Cache, MMU, PLL, and timers are untouched.

The only command transactions are `FF FF` under one CS to exit any continuous
read mode, `9F` for JEDEC, and `03` followed by the 24-bit address for reading.
There are no WREN, program, erase, or write-status operations, even as public
APIs. The FF sequence is corroborated by the reference AC791N ROM reader; SPI
PIO cycles are also verifiable in the MINI bootloader. Only manufacturer IDs
other than 00/FF and capacity exponent 20 (1 MiB) are accepted. The FWSC file
is not used to invent physical capacity.

Each byte waits for at most 32,768 reads of the completion bit. A timeout
releases CS, preserves the first error, and prevents further transactions.
The host test covers all 522 timeout points in initialization and a 512-byte
read, NOR boundaries, clock changes, framing, a negative USB response, and
rejection of nine legacy commands. It also checks every SPI command and an
allowlist of writable MMIO addresses. These tests cover software sequences
and termination; they do not simulate the physical device.

## Acquiring the backup

The separately maintained client must:

1. Verify USB ROM, ABI/slot, and the plugin hash before upload.
2. Check FC70 and then FC72, requiring success, plausible JEDEC, 1 MiB capacity,
   and baud 15.
3. Read `[0,0x100000)` in blocks of at most 512 bytes, checking FC73 after each.
4. Save the complete image and repeat the entire acquisition.
5. Require two identical images and preserve their hashes, JEDEC, clocks,
   counters, and device identification before any subsequent NVM work.

Offline content inspection is available through:

```powershell
python tools/inspect_mini_backup.py flash-a.bin --second flash-b.bin --report backup-inspection.json
python tools/inspect_mini_backup.py --self-test
```

Require both `backup_consistency_and_content_validated` and
`decoded_firmware_matches_stock_009`. The parser verifies CRCs for the BANKCB
bootloader, configuration, key prefix, and application directory/payloads.
The FWSC package covers only `[0,0x82000)`: VM, BTIF, USR, and key_mac must be
preserved and compared between the two reads, without inventing a stock
reference for those areas. Dumps contain pedal-specific data and remain in
the local `artifacts/` directory, excluded from Git.

This plugin has no command to install firmware or return to stock. Reset and
RAM markers are separate paths to test and manage in the coordinator, not
implicit effects of a backup.

Primary references for the ABI and ROM path: [m-bootloader, loader_target.c](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/src/loader_target.c)
and [platform.c](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/src/platform.c).
The reference has FM1/SMK37 hardware evidence; physical MINI compatibility is
not automatically inferred from those tests.
