# Observed ROM clock and HYC3 diagnostic

On 15 November 2026, HYC2 returned a stable TANK MINI snapshot but correctly
rejected the clock profile with `gate=4`. The session neither executed FC69
nor touched GPIO; return to stock firmware and unchanged presets are attested
in the separate hardware report. The original record has SHA256
`d5494ce5fe320b951f1470d0e896ccce214a6dce1fd48c2f138635c4bd225083`.
HYC2, its manifest, and its binaries remain immutable.

[audit_mini_rom_clock.py](../tools/audit_mini_rom_clock.py) rereads that record,
verifies its HYC2 contract, and interprets original MINI bytes
`0x02002D76..0x02002EC8` offline. After 67 instructions, the stock decoder
returns **a nominal 48 MHz for SYS, HSB, and LSB**, with SDRAM disabled.
The fragment has SHA256
`de019096c01b9801c0e23aea0ffdfe5d993bd25028277fd9a1d63590f896a9d3`.

The result is corroborated by `clk_early_init` extracted from `clock.c.o`
in the pinned SDK `cpu.a` and by the
[m-bootloader SPEC, §10.4](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#104-clock-dma-and-performance).
Branch `CLK_CON2[3:0]=0` uses a nominal 192 MHz; divisor fields select
1 and 4. `SYS_DIV=0` leaves HSB and LSB without further division.
The active SDK header identifies `CLK_CON0[8:6]=7` as PLL and `[3:2]=0`
as normal input. The acceleration code to 96 MHz described in the SPEC is
not executed, and the USB clock is unchanged.

| Register | Address | Observed value |
|---|---:|---:|
| SYS_DIV | `0x10008` | `0x00000000` |
| CLK_CON0 | `0x1000C` | `0x000001C1` |
| CLK_CON1 | `0x10010` | `0x00010000` |
| CLK_CON2 | `0x10014` | `0x00000080` |
| PLL_CON0 | `0x119A0` | `0x0940022B` |
| PLL_CON1 | `0x119A4` | `0x3F5030EE` |
| PLL2_CON0 | `0x119A8` | `0x00000000` |
| PLL2_CON1 | `0x119AC` | `0x00000000` |
| HUSB_CON0 | `0x16A00` | `0x00000000` |
| HUSB_CON2 | `0x16A08` | `0x00000000` |
| SFC_CON | `0x40200` | `0x01580034` |
| SFC_BAUD | `0x40204` | `0x00000001` |

The primary PLL configuration differs from the one prepared by application
boot. Divisor field 12 and multiplier 240 are consistent with
24 MHz / 12 × 240 = 480 MHz; this consistency is neither a measurement nor
the basis of the new gate. The SDK decoder's 24/40 MHz shortcut is not extended
to the ROM profile: it also produces an arithmetic value of 40 MHz for the
disabled secondary PLL, which **does not represent an enabled clock**.

The [mini-rom-clock.json](../research/mini-rom-clock.json) report preserves
the complete record, source hashes, and interpretation result. The included
record allows the audit to be reproduced without the private
`analysis/hardware` directory; it requires the SDK/stock dependencies already
declared in the repository and the vendor compiler to make the bitcode readable.

```sh
python -B tools/audit_mini_rom_clock.py
```

HYC3 is a separate payload in
[rom_codec_rom](../firmware/mini/rom_codec_rom/rom_codec.h). It accepts only an
exact match of the twelve values above; any difference leaves the diagnostic
at snapshot reading, without pin setup. The five additional
cache/SDRAM/PSRAM values are recorded but are not the clock-recognition
criterion. `gate=4` means an unrecognised ROM profile.

The distinct protocol uses `FC6B` for a snapshot, `FC6C` for a read
explicitly tied to the snapshot sequence, and `FD6D` for the 512-byte record.
Magic `HYC3`, version 3; record offsets are documented in the header.
CRC, build tag, slot, sequence, and consistent counters are required.
Each read consumes the snapshot authorisation, even on error.
No automatic retry is performed.

PC5/PA9 setup and restoration of PA1/PA2/PA9 and PC5 bits, including HD/HD0,
retain the already documented HYC2 operations. The nominal gate permits the
stock scale `48 MHz / 4 MHz = 12` iterations per unit, hence 36 or 72
iterations for waits of 3 or 6 units. The settling loop remains
100000 iterations. None of these figures measures actual edge timing,
callback overhead, interrupts, or the stock RTOS delay.

```sh
python -B tools/build_mini_rom_codec_rom.py
```

The builder runs ASan/UBSan host tests, verifies the record, and produces two
ELF/payload pairs in 32 KiB RAM slots. Manifest
[mini-rom-codec-rom.json](../research/mini-rom-codec-rom.json) attests only these
offline checks. The private stack and guards check the synchronous path;
the static bound does not qualify the stack inherited by ROM interrupts.
ROM USB callbacks are called after returning from the private stack.
No NOR access, PLL/USB modification, or codec-data write is included.
An ACK alone would not prove exclusive codec identity, 48 kHz audio, mute,
or startup of the complete HyperRig firmware.

## Physical HYC3 outcome

The test of 15 November 2026 is complete and preserved separately in
[mini-codec-rom-hardware.json](../research/mini-codec-rom-hardware.json).
Upload and readback of 5392 bytes succeeded. The snapshot accepted the
nominal 48 MHz ROM profile with scale 12, and the first explicit read applied
the intended PC5/PA9 setup.

The first byte `0x36` received a NACK: zero data bytes and zero ACKs,
with no codec value obtained. The other nine reads were omitted without retry.
Touched GPIO fields were restored, clocks remained unchanged, and the private
stack showed 576 modified bytes with intact guards. Return to MINI_009 and
unchanged presets are verified.

The ROM diagnostic does not release the SPL/application startup P33 latches.
It therefore neither identifies the electrical cause of the NACK nor replaces
startup of the complete port. The offline manifest remains unchanged.
