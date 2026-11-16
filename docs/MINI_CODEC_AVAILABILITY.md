# MINI codec availability: evidence after HYC1

The first HYC1 NACK neither identifies the codec nor proves its absence.
The [mini-codec-availability.json](../research/mini-codec-availability.json)
report preserves hashes, preimages, and the analysis limits. HYC1 and the v1
audio shim remained unchanged. The physical test of 15 November 2026 is documented
in `analysis/hardware/mini-codec-run.json`: the first address byte receives a NACK,
with ACK=0, no received data, one SDA sample, and 35 waits. The report verifies
the stack, PA1/PA2 restoration, return to MINI_009, and unchanged presets; no codec
register was identified.

Executed HYC1 payload: SHA256
`084ca247eeb53c5ab165dec62059ca0a0022ab7719c9975a5efd3db97da184fa`.
Record128: SHA256
`9736667745a0c7b8ad5628f694a0dd8df0979b151b9e4b09d6f710dc76381ca8`.

`0x02006DD6` loads **decimal 54 = 0x36**, then calls transmitter
`0x02006C6A`: no address shift. The transmitter uses mask
`0x80 >> bit_index`, so the wire byte is `00110110`, seven-bit address
`0x1B`. Independent interpretation of the stock bytes and the executed HYC1
payload confirms the same START, the same eight bits, and SDA release before
the ninth clock. Sampling takes place with SCL high. The 57 normalised operations
up to that sample match; trace hash
`07059f8581420830b4431cb832f02c72dccd55d1ef2ca3af195d7847fd5309f1`.
Normalisation removes only consecutive identical OUT writes and compares wait
units, without simulating duration, electrical GPIO behaviour, or interrupts.

Stock repeats an OUT(SCL,0) while SCL is already low before the ACK. After sampling,
it takes SDA back as an output; read16 leaves it released for reading and attempts
STOP even on error. These later differences do not explain the first NACK.

Durations do differ: stock uses
`units * floor(sys_hz / (SFCbit0 ? 8000000 : 4000000))`; HYC1 used
`units * 1024`. At a nominal 360 MHz, stock uses 45 or 90 iterations per unit.
We have not measured physical edges. Table 13 of the
[Nuvoton rev3.1 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.1.pdf)
also specifies maximum DATA hold and rise/fall limits: slowing down does not
automatically establish timing qualification.

The power-up sequence documented in the
[rev2.7 datasheet, §2.1–2.2](https://www.nuvoton.com/export/resource-files/DS_NAU88L21_DataSheet_EN_Rev2.7.pdf)
places I²C configuration before I²S clocks are applied. It therefore does not
support the hypothesis that MCLK is required for the first ACK.
Stock MINI calls the codec table at `0x02007188` and opens ALNK only at
`0x020071E6`; this does not prove that no clock was already inherited from boot.
Nuvoton's sources describe a compatible candidate: the physical identity of the
MINI's chip remains unknown.

PC5 is initialised before the codec, in the chain
`020071FE → 020067F2 → 020060D0 → 02005BCE`. The final fragment, 148 bytes,
has SHA256 `216b7f3a3e475bafaecd0e2eccddad0655f4aa8275cd841b38ae991e42c4b733`.
It touches only GPIO37/PC5 and the original APIs' RAM/IRQ locks:

| Order | Register | PC5 operation |
|---|---|---|
| 1 | DIE `0x5008C` | sets bit5 |
| 2 | OUT `0x50080` | sets bit5 |
| 3 | DIR `0x50088` | clears bit5, output |
| 4 | HD `0x5009C` | clears bit5 |
| 5 | HD0 `0x50098` | clears bit5 |

PU, PD, and DIEH remain unchanged. The only direct caller of initialisation is
`0x020060D2`. After panel configuration, `0x02007218` drives PA9 low;
a 100000-iteration loop and an RTOS `delay(10)` follow before the codec table.
The time unit of that delay is not reconstructed here.

**PC5 is not a demonstrated audio power rail.** Writer `0x0200AF46` drives it high
with a zero argument and low otherwise. Task `0x0200BDEC` calls it at
`0x0200BF78`, alternating thresholds 13/26 or 25/51; the inactivity branch
`0x0200B6DA` forces it high and continues the application. The behaviour is
consistent with an indicator, as an inference. No poweroff/storage commands
were found in the PC5 fragments. Boot uses PORTD `0x500C0` for NOR/SPI0,
so PC5 is not part of that bus; this does not replace a schematic or exclude
every possible external connection. This audit has not exhausted the generic
port sleep/restore paths.

The other immediately adjacent setups concern PC9/ADC8, PC0/ADC6,
PA10/PA0/PA3 as inputs, PB7 as an input, and PC10/SPI1. They were not included
in a minimal probe without a demonstrated audio dependency.

For the main clock, the **active** branch of
[clock_hw.h pinned to the SDK commit](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h)
defines `CLK_CON0[8:6]`: RC=0, BTOSC=4, reserved=5, RTOSC_L=6, PLL=7.
`TEST_SEL[3:2]=0` selects the normal input.
MINI boot at `0x01C04582` sets `0xC0`, then at `0x01C045B6` sets `0x100`,
after preparing the PLL and divisors: final selector 7. This resolves the mux
meaning without turning a nominal value derived from registers into a measurement.

A **separate HYC2 diagnostic** is therefore reasonable: snapshot-only first,
then a single explicit read with PC5/PA9 in the observed stock state.
The implementation and schema are in
[rom_codec_board/rom_codec.h](../firmware/mini/rom_codec_board/rom_codec.h);
[build_mini_rom_codec_board.py](../tools/build_mini_rom_codec_board.py) produces
the [mini-rom-codec-board.json](../research/mini-rom-codec-board.json) manifest.
It changes neither PLL, USB, NOR, nor codec data. If the source/reference is not
recognised, it stops at the snapshot. It restores all touched GPIO bits, including
PC5 HD/HD0. It reproduces the 100000-iteration loop and the bus arithmetic scale;
this does not make the RTOS delay, RAM overhead, or electrical edges equivalent
to stock. No HYC2 execution is attested here.

A future revision of the complete G shim must preserve the observed PC5 setup
separately, rather than removing it together with the G PC0/PC1 outputs that are
unsuitable for MINI. v1 remains frozen, and this recommendation promises neither
ACK, 48 kHz, mute, nor working audio startup.
