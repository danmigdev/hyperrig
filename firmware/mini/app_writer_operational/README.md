# HYW1 operational build

This is a separate build of the frozen HYW1 core. The builder checks the frozen
source hashes, derives a copy under `build/mini-app-writer-operational/`, and
changes the compile-time mutation switch and the explicit busy-poll delay. The operational target exports
gate `1`; the existing gate-zero source, payloads and report are never edited.

The ROM entry still performs no peripheral access. `FC79` explicitly initializes
PIO and checks exact JEDEC `EB6014`, WIP/WEL and protection bits. The target can
erase only 4 KiB sectors and program complete 256-byte pages in NOR
`[0x4000, 0x82000)`. It never writes status registers or erases the chip.

Every first erase requires a staged page and exact host echo. The host compares
the complete application with its accepted backup before beginning, checks each
sector again, stages and echoes each page, and verifies every result and the
complete application. Ambiguous completion ends the session without retry,
reset, rollback, or a second write. Returning from the installer leaves the ROM
USB session active; a separately reviewed runner owns any subsequent boot.

The final sector is `0x4000`; its page order is `0x4100..0x4F00`, then `0x4000`.
The host stages `0x4100` before erasing this sector. The old header remains valid
while earlier sectors change. A power interruption can therefore boot a mixture
of old and new code before the recovery guard exists. Header-last ordering is
not atomicity, and stock OTA fallback has not been qualified. No separate early
header invalidation is performed.

Host tests use an in-memory NOR. A successful build does not qualify erase or
program on hardware, the recovery guard, the candidate's audio, or first boot.
The operational Windows profile is separate from the frozen observer profile.

The WIP loop remains bounded to 65,536 status pairs. Its operational PIO copy
uses 768 `settle` iterations between busy replies, compared with the frozen
observer's 256. The ELF loop is `nop` then decrement/branch. At the saved nominal
48 MHz ROM clock, an assumed 2–4 cycles per iteration gives about 3.23–5.77 s
for the delay, CS waits and inferred 3 MHz SPI transfers, before callback/MMIO
overhead. This is a model, not a calibrated maximum. Upstream `ready()` uses
30,000 polls spaced by 100 microseconds, about 3 s plus overhead. A stuck byte
or unexpectedly slow CPU can exceed Windows' 10 s SPTD timeout; that case must
remain ambiguous and terminal, with ROM active and no reset or automatic retry.
