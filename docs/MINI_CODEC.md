# TANK MINI codec bus and control

The component in `firmware/mini/codec/` reconstructs the MINI_009 firmware bus
and compiles for pi32v2. Successful transactions are compared with original
instructions interpreted on the PC. **It has not run on the pedal**:
the physical codec identity, electrical timing, clocks and analog mute remain
unverified.

Register correspondence identifies a **map compatible with the Nuvoton
NAU88L21**. This does not certify the fitted component or board revision.
An important discrepancy also emerged: interpreted through this map, the stock
configuration exceeds Nuvoton's published converter-clock limit.
A switch to 48 kHz therefore cannot be declared ready solely from replaying
the original script.

## Original evidence and bus

Sample: `artifacts/tank-mini/TANK-MINI.fwsc`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
The verifier checks and decodes the container, then compares the image with
`analysis/tank-mini/app_area.dec.bin`. Region hashes and results are in
[mini-codec.json](../research/mini-codec.json).

| Stock function | CPU address | Observed behavior |
|---|---|---|
| GPIO configuration | `0x02006960` | PA1/PA2, digital inputs and pull-ups enabled |
| START | `0x020069BC` | SDA falls while SCL is high |
| GPIO read | `0x02006AC4` | The used path reads PA1 from PORTA IN |
| ACK | `0x02006B8C` | SDA becomes an input; low means ACK |
| Byte send | `0x02006C6A` | Eight bits, most significant first, then ACK |
| Buffer send | `0x02006D1E` | Stops at the first NACK and returns the ACK count |
| STOP | `0x02006D3A` | SDA rises while SCL is high |
| Record send | `0x02006DCE` | START, `0x36`, four bytes, STOP only if all ACK |
| Codec initialization | `0x02006DEC` | Configures GPIO and attempts all 22 records |

These transitions establish **PA1 = SDA, PA2 = SCL**. The GPIOs are in PORTA
at `0x50000`: OUT `+0`, IN `+4`, DIR `+8`, DIE `+12`, PU `+16`,
PD `+20`, with 32-bit accesses. Stock helper `0x02004F86` sets OUT and
selects output; the driver preserves the bank's other bits. The initial sequence is:

1. PA2: DIR=0, PD=0, DIE=1, OUT=0.
2. PA1: DIR=0, PD=0, DIE=1, OUT=1.
3. PA2 OUT=1; PU=1 for PA2 and PA1.

Stock firmware **also drives the high level** and releases SDA only during ACK.
It does not read SCL or handle clock stretching, arbitration or other masters.
This reconstruction covers the observed private bus; voltages, external
resistors and electrical compatibility are not inferred from code.

## Reconstructed delays

Before every wait, stock firmware reads bit 0 of register `0x40200` and
global value `0x01C1E32C`. The latter is the nominal system clock maintained
by stock routines; the new code receives a value owned by its board support,
without using that original firmware RAM address.

```text
divisor = (register_40200 & 1) ? 8000000 : 4000000
n = integer_division(system_clock, divisor)
iterations = n * units                  // units = 3 or 6
```

Stock firmware multiplies by -3/-6 and increments the counter to zero,
executing `nop` each iteration. `spin_pi32v2.S` provides a leaf callback
with the same loop structure. Calls, GPIO helpers, cache, bus and interrupts
add time: **these counts are not calibrated microseconds** and do not
establish SCL frequency. The mode bit's timing meaning is not inferred beyond
the observed divisor selection.

| Phase | Wait sequence, in units |
|---|---|
| START | SDA=1 → 3; SCL=1 → 6; SDA=0 → 3; SCL=0 → 3 |
| Each bit | SDA=data → 3; SCL=1 → 6; SCL=0 → 3 |
| ACK | SDA input; SCL=0 → 3; SCL=1 → 3; read SDA → 3; SCL=0 → 3; SDA output at 0 |
| STOP | SDA=0 → 3; SCL=1 → 6; SDA=1 → 3 |

The MMIO adapter rereads mode and clock at every wait. It rejects zero clocks,
negative values represented as unsigned, or values below the divisor:
stock firmware would produce zero or pathological waits. Board support must
keep clocks stable and guarantee exclusive GPIO-bank ownership throughout
the transaction. The component does not implement stock operating-system
locks and does not change interrupt state.

## Identifying the codec map

The stock table at `0x02035E35` contains 88 bytes, SHA-256
`1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d`.
Wire address `0x36` corresponds to 7-bit I²C address `0x1B` for a write.
The layout is a 16-bit register followed by a 16-bit value, both big-endian,
as Nuvoton describes in section 7.3 of the
[NAU88L21 datasheet, rev. 3.5](https://www.nuvoton.com.cn/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.5.pdf).

Distinctive registers `0x34`, `0x35`, `0x4B`, `0x7E` and values `0xCFCF`
match NAU88L21 in the
[Nuvoton-authored driver, Linux v6.12](https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.c)
and its
[register header](https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.h).
No Linux driver code is incorporated; these sources corroborate addresses
and fields. The verifier remains entirely offline and does not require local
copies of these documents. URLs and hashes of the consulted Linux files are
recorded in the report.

The 22 records are preserved byte for byte and in the same order. For fields
needed by the adaptation, the interpretation conditional on NAU88L21 is:

| Register | Stock | Interpretation from the NAU88L21 map |
|---|---|---|
| `0x03` | `0x0000` | Direct external MCLK; ADC and DAC divisors /1 |
| `0x1D` | `0x0002` | Slave audio interface; BCLK divisor field is 2 |
| `0x1C` | `0x000E` | I²S format, 32-bit words |
| `0x2B` | `0x0003` | ADC OSR 256 |
| `0x2C` | `0x0081` | DAC OSR 256, with other stock bits preserved |
| `0x31` | `0x1004` | ADC/DAC zero crossing enabled; ADC/DAC soft mute disabled |
| `0x32` | `0x0000` | Headphone-output mute bits are zero |

The codec's 32-bit words do not establish the electrical alignment of the
24 significant bits in ALNK buffers: packing reconstruction is described in
the [audio driver](MINI_AUDIO_DRIVER.md), but the serial frame must be measured.
Other analog values are replayed as original records; board gain, power
sequence, possible external mutes and settling times are not assumed known.

## Stock discrepancy and 48 kHz candidate

For the identified map, MCLK=256×Fs requires 11,289,600 Hz at 44.1 kHz and
12,288,000 Hz at 48 kHz. With two 32-bit slots, BCLK=64×Fs requires
2,822,400 and 3,072,000 Hz respectively. These are profile requirements,
**not MINI measurements**.

With OSR256 and /1 divisors, the stock script would imply an ADC/DAC clock
of 11.2896 MHz or 12.288 MHz.
[Nuvoton datasheet rev. 3.7, section 6, page 29](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.7.pdf)
limits CLK_ADC to 6.144 MHz; the Nuvoton driver applies this limit to both
ADC and DAC. The discrepancy remains unresolved: component confirmation,
measurements and understanding of the actual configuration are required
before qualifying stock operation at 44.1 kHz or a change to 48 kHz.

`hyperrig_mini_codec_plan_128()` computes a **candidate**, without sending anything:

| Field | Derived candidate |
|---|---|
| `0x03` | `0x0050`: ADC and DAC divisors /2, direct external MCLK |
| `0x2B` | `0x0002`: ADC OSR128 |
| `0x2C` | `0x0082`: DAC OSR128, other stock bit preserved |
| ADC/DAC clock | 5,644,800 Hz at 44.1 kHz; 6,144,000 Hz at 48 kHz |

The plan contains no live frequency-change sequence, configures no PLL/ALNK,
and does not declare the device ready. Changing OSR also changes filters and
latency. The code does not automatically update any audio-readiness state,
even after an ACK. The [platform component's](MINI_PLATFORM.md) clock decoder
provides nominal values from a snapshot, without proving MCLK frequency,
lock or clock consistency.

## API, errors and mute

`hyperrig_mini_codec_bind_mmio()` binds pointers and callbacks without reading
peripherals. `bus_init()` explicitly executes the GPIO sequence.
`write()` sends one record, reports the acknowledged-byte count, and
distinguishes the primary error from an error during STOP.
`write_adapter()` has the signature required by the audio driver's replay
and accepts only byte `0x36`, not `0x1B`.

Intentional differences from stock firmware are:

- On NACK, HyperRig attempts STOP; stock returns with the transaction left open.
- HyperRig replay stops at the first error; stock attempts every record.
- A read or timing error invalidates bus initialization. Cleanup attempts to
  return SDA/SCL high, but a failed delay cannot guarantee an electrically
  valid STOP.
- The number of completed records does not imply that a partial configuration
  is usable: responsibility for stopping startup remains with the board.

Semantic control is disabled for the default `OPAQUE` map.
If the caller explicitly selects `NAU88L21`, a fully acknowledged replay
retains the `0x1004` shadow of register `0x31`. `soft_mute()` changes only
ADC bit `0x0002` and DAC bit `0x0200`, preserving all others.
An error invalidates the shadow; the code does not continue changing a value
that is no longer known. Reset or writes through another path require
invalidation and reinitialization by the caller.

This function controls **digital mute**: it does not prove output silence,
ramp completion or absence of analog transients. The stock script ends with
mute disabled and provides no verified silent power-on sequence.
No GPIO address is invented for an external mute.

## Reproducible verification

```powershell
python tools/verify_mini_codec.py
```

This uses WSL Ubuntu/GCC and the JieLi toolchain already pinned in the project.
It produces:

- `build/mini-codec/hyperrig_mini_codec.pi32v2.o`, relocatable C component.
- `build/mini-codec/spin_pi32v2.o`, optional native wait callback.
- `research/mini-codec.json`, evidence, hashes, counts and limits.

The interpreter executes original bus-function bytes, including branches,
then/else predicates, signed divisions, loops and register saves.
Only GPIO helpers are replaced with trace events. The 278 ACK cases cover
all byte values in every payload position, the 22 original records, and
various clock/mode values. The 110 NACK traces demonstrate the cleanup
difference; another 110 cases verify replay interruption.

Also verified are 148 timing errors, two read errors, 240 delay-calculation
cases, 128 GPIO snapshots, nine mute cases and 1,536 transactions with exact
four-byte records under ASan/UBSan. Both objects are ELF32 pi32v2 and have
no unresolved function symbols. The assembly object's loop is decoded and
checked again.

These tests verify software sequences and host memory. They do not emulate
peripherals, helper timing, voltages, codec behavior, readback or real audio.
The tools open no pedal connections and transmit no records through USB,
Bluetooth or GPIO.
