# TANK MINI audio clock

The stock branch labelled **48 kHz does not establish an exact 48,000 Hz rate**. The
reconstructed code selects an ALNK family; the SDK divisor names suggest about
**48,076.923 Hz**. The MINI bootloader already enables the PLL output required by
that branch. There is no need to infer a new PLL programming sequence from the
shutdown routine at `0x01C03352`.

The [hyperrig_mini_clock.c](../firmware/mini/clock/hyperrig_mini_clock.c) component
calculates plans and analyses caller-supplied values. **It does not access MMIO,
send records to the codec, or grant audio readiness.** Frequencies in this document
are nominal hypotheses or measurement targets, never measurements from the pedal.
Reproducible evidence is in [mini-clock.json](../research/mini-clock.json).

## Reconstructed startup chain

The sample is `TANK-MINI.fwsc`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.

1. The bootloader applies the MINI profile `OSC=0/24 MHz`, `SYS_CLK=360 MHz`,
   `HSB_DIV=1`, `LSB_DIV=2`, `SDRAM=0`. At `0x01C0434E..435A` it builds
   `PLL_CON1 = 0x3F503000 | (480000000/reference - 2)`. At `0x01C0438A/4394`
   it enables the two low bits of `PLL_CON0`. The special branch that bypasses
   this sequence requires `OSC=3` and reference=1: that is not the MINI profile.
   This proves that bit25 is programmed, not that the analogue PLL has locked.
2. Application entry `0x02000120` copies the RAM code and configures the caches;
   `0x02003140` calls `0x02002D40`. The section `0x02002D76..2EC8` reads the
   inherited clocks and updates nominal values in RAM. Subsequent instructions
   configure UART/HUSB and other services. They do not set a new ALNK frequency.
3. The application task calls `0x020071FE`. This function drives **PA9 low**,
   waits for a loop of 100,000 iterations, calls `0x0200717C`, waits for another
   identical loop, and drives **PA9 high**. PA9's electrical function and the
   duration of these loops remain unknown.
4. `0x0200717C` calls initialisation of the 22 codec records at `0x02006DEC`,
   writes the initial countdown, then starts ALNK through `0x0200715C`.
   `0x02006F70` applies the configuration; `0x02006E58` selects the rate;
   `0x02007146` enables ALNK. The stock configuration table requests 44100.

The bootloader payload has SHA-256
`fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d`.
The configuration occupies 699 bytes in flash at `0x38D0`, with CRC16 `70D5` and SHA-256
`0952afd96f533dd0fba72a8fab9cb4a4336f55424a1a89eecb13ff8a51a0eff0`.
The profile and bootloader handover checks are documented separately in
[mini-handover.json](../research/mini-handover.json).

`0x01C03352` belongs to function `0x01C03296..33EC`, called by suspend/shutdown
paths. It waits for the cache and SFC, disables SFC, changes divisors and the main
source, then re-enables SFC. **It is not audio initialisation**; it has neither
been ported nor called. Executing it from XIP code would interrupt the mechanism
that supplies that code.

## ALNK families and frequencies

Stock function `0x02006E36` preserves the other bits of `CLK_CON2` at `0x10014`
and changes nibble `[11:8]`. With the MINI master configuration:

| Requested label | `CLK_CON2 & 0xF00` | `ALNK_CON3` | Behaviour |
|---|---:|---:|---|
| 44100 | `0x000` | `0x83` | Stock configuration |
| 48000 | `0x500` | `0x83` | Branch present in stock code |
| Unsupported, including 96000 | `0x000` | `0x83` | Silent stock fallback to 44100 |

The `hyperrig_mini_clock_stock_plan()` API also reproduces the other nine
recognised rates and slave behaviour, explicitly reporting fallback.
The plan does not apply writes or change the codec configuration.

In the [pinned AC79 SDK](https://github.com/amitv87/fw-AC79_AIoT_SDK/tree/ffbb2a8d925682ba6880d643a83a63ee0691ec09),
`cpu/wl82/liba/cpu.a` contains LLVM bitcode recoverable with the JieLi compiler.
The original `iis_set_sample_rate(48000)` function in `iis.c.o` sets
**`PLL_CON1 bit25`** and then selects the ALNK family. Stock MINI changes only
the mux, so it depends on the PLL output already enabled by the bootloader.
The verifier derives the IR from the pinned blob; that SDK code is not linked
into HyperRig firmware.

[clock_hw.h from the same SDK](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h)
names `192M/17` and `160M/13` (or the equivalent `480M/39`). **These declarations
are in debug/disabled branches**, so they do not independently prove the physical
frequency. Combined with the stock 256fs configuration, they yield this testable
hypothesis:

| Family | Nominal MCLK, Hz | Nominal BCLK, Hz | Nominal LRCK, Hz | Deviation from label |
|---|---:|---:|---:|---:|
| 44100 | `192000000/17` ≈ 11294117.647 | ≈ 2823529.412 | ≈ 44117.647 | +400.160 ppm |
| 48000 | `160000000/13` ≈ 12307692.308 | ≈ 3076923.077 | ≈ 48076.923 | +1602.564 ppm |

At `0x020071BA`, stock writes **44118** to `0x01C1BA50`. Audio path
`0x01C03ADE..3B18` subtracts 64 per block and keeps gain at zero until expiry:
690 blocks, 44160 samples. This is an initial countdown of about one second,
**not a sample-rate configuration variable**. Its rounded value corroborates
the 44117.647 hypothesis; it does not replace a measurement.

`hyperrig_mini_clock_audit()` distinguishes ALNK configuration, PLL control bits,
PLL output enabled, and ALNK running. No bit is called “lock”.
`hyperrig_mini_clock_measurement_flags()` compares operator-supplied frequencies
against:

- the exact frequency indicated by the label;
- the SDK family's nominal hypothesis;
- the ratios MCLK/LRCK=256 and BCLK/LRCK=64.

Tolerance is explicit, and supplied uncertainty reduces the available margin.
The examples in the report are synthetic. Distinguishing 44100 from 44117.647
requires uncertainty substantially below 400 ppm; distinguishing 48000 from
48076.923 requires less than 1603 ppm. Counting against a clock derived from the
same PLL is insufficient by itself to verify absolute frequency.

## Codec: discrepancy still to be measured

The stock records are `R03=0`, `R2B=3`, `R2C=0x81`. The NAU88L21 map interprets
them as ADC/DAC at OSR256 with undivided converter clocks. The **NAU88L21C variant
uses the same codes for these values**: changing only the component name does
not resolve the discrepancy. Its map adds other rates and filters, but compatible
shared fields do not identify the fitted chip. The encoding is documented on
pp. 22, 59, 60 of the
[NAU88L21C rev1.3 datasheet](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.3.pdf).

The manufacturer's sources are internally inconsistent: the initial features
state 48 kHz/OSR256, while the clock chapter imposes a 6.144 MHz maximum ADC clock.
The [Linux driver written by Nuvoton](https://github.com/torvalds/linux/blob/v6.12/sound/soc/codecs/nau8821.c)
also applies that limit. The earlier conflict documented in MINI_CODEC therefore
remains **a contradiction between the observed configuration and the published
limit**, not proof that the original pedal operates outside its specifications.
See [NAU88L21 rev3.7](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.7.pdf)
and [NAU88L21C rev1.6, p30](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.6.pdf).

The direct-reference search finds only one caller of the record writer, the
22-record loop, and only one caller of initialisation, audio startup. No later
OSR writes or absolute pointers to these two functions were found. The scan
does not exclude computed calls or other bus implementations; it is not complete
proof that no other writes occur.

The earlier OSR128 candidate requires care: under the 48076.923 Hz hypothesis,
the converter clock would be **6.153846 MHz**, slightly above the published limit.
A candidate that preserves 256fs and stays below that limit is OSR64:

| Register | Value from stock shadow | Meaning conditional on a compatible map |
|---|---:|---|
| `0x03` | `0x00A0` | ADC and DAC clocks divided by 4 |
| `0x2B` | `0x0001` | ADC OSR64 |
| `0x2C` | `0x0080` | DAC OSR64, other bits preserved |

This would give the converter about 3.076923 MHz for the nominal 48k family.
`hyperrig_mini_clock_osr64_candidate()` generates only these three records from
a supplied shadow; it rejects other clock modes. **It does not transmit them.**
Changing OSR changes filters and latency: the result must be measured and does
not equal stock behaviour.

## Minimum test path

1. Capture a real snapshot after the bootloader and check PLL_CON0/1, CLK_CON2,
   and ALNK. Preserve the inherited PLL and SFC. The snapshot alone still does
   not establish frequency.
2. Establish the physical codec map and PA9's analogue control function. Keep
   the output silent during configuration; the code does not present PA9 as
   a verified mute.
3. After that verification, assess the OSR64 candidate, 32-bit I2S slave and
   48k-family ALNK master, with zero-initialised buffers and blocks of 64.
   Require ACK, an installed IRQ, DMA coherence, and analogue control before enabling it.
4. Measure MCLK, BCLK, and LRCK against an independent reference. Record
   frequency, uncertainty, and ratios without automatically replacing the result
   with “48000”. Only then test bypass and measure its noise/latency.
5. Connect A2 after bypass. If the clock is 48076.923 Hz, explicitly assess
   adaptation/resampling or acceptance of the deviation; do not claim completion
   of an exact 48,000 Hz path.

This document proposes the path; this component does not execute it.

## Reproducible verification

```powershell
python -B -X utf8 tools/verify_mini_clock.py
```

The SDK dependency is pinned in `sources.lock.json`:
`upstream/ac79-sdk-reference/cpu/wl82/liba/cpu.a`, SHA-256
`00cea21d3c8d99487821f2c2b203f2c5a04b2cc8421bc05e9b875a0d70e42c62`.
The verifier requires no datasheet downloads and contains no device access.
It checks 6080 cases against the original rate-selector instructions,
2000 measurement comparisons using integer arithmetic, and 66560 ASan/UBSan
cases. It compiles `hyperrig_mini_clock.pi32v2.o`: 1152 bytes of code, with no
external symbols. The component does not duplicate the already verified bus
initialisation and does not enable clocks, the codec, or audio in existing probes.
