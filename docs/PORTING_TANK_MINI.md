# Porting HyperRig to TANK MINI

The target is defined in `firmware/targets/tank-mini.json`. Its actual status
is `port-in-progress-not-flashable`: no installable HyperRig binary exists yet.
Offline results allow a target-specific port to begin; they do not justify
labeling a G/B image compatible.

## Parts already adapted or reconstructed

1. Official MINI update parser, SFC decoding, and JLFS checks.
2. Target-specific memory map, entry address, and RAM code copy.
3. MINI USB-MIDI protocol, distinct from UltraRig's text CDC protocol.
4. Reading and interpretation of its 21 92-byte presets.
5. CLI to identify the model before reads and compare two preset-bank copies;
   successful BLE and USB backups on our unit.
6. AC79 SDK headers for studying GPIO, ADC, and DAC registers.
7. A2-Lite Float64 model executable on the PC and compared with the original
   converter. It is a numerical reference, not the firmware's integer runtime.
8. Three-channel/int32 A2-Lite capture engine reconstructed in C and compiled
   for pi32v2: loader, bias, input, dilated layers, activations, residuals, and
   head. 7,509 comparisons against interpreted instructions, including all 23
   A2 layers. Memory checked with ASan/UBSan. The original parser and scheduler
   are not emulated; the C coordinator is an independent implementation.
9. MINI ALNK0 audio path, configuration table, IRQ, callback, buffers, and task
   reconstructed. See [TANK_MINI_AUDIO.md](TANK_MINI_AUDIO.md).
10. Successful BLE identification: the unit responds with `TANK MINI_009`.
11. MINI ALNK driver and Q23/QFin/QFout conversion compiled and tested offline:
    [MINI_AUDIO_DRIVER.md](MINI_AUDIO_DRIVER.md). DMA startup is conditional on
    actual clock/codec, IRQ, cache, and analog-path readiness.
12. Startup/linker and two diagnostic ELFs with RAM-copy/BSS simulation:
    [MINI_BOOT.md](MINI_BOOT.md). ELF/container validator and ten tests against
    inconsistent layouts, segments, and copies: [MINI_IMAGE.md](MINI_IMAGE.md).
13. Platform, codec, and runtime components reconstructed in parallel:
    [MINI_PLATFORM.md](MINI_PLATFORM.md), [MINI_CODEC.md](MINI_CODEC.md),
    [MINI_RUNTIME.md](MINI_RUNTIME.md). The `--bringup` probe links the three
    components and tests the worker on the PC with the A2 engine and dummy RAM.
14. Experimental MINI application area composed from the ELF with verified
    CRCs, preserving region directories and `cfg_tool.bin`. It is not a FWSC.
15. A 1,942-byte BLE preset backup acquired and validated through two identical reads.
16. **HyperRig probe executed in RAM on the MINI:** 8 DSP primitive vectors
    passed, with verified record and CRCs. See [MINI_ROM_PROBE.md](MINI_ROM_PROBE.md).
17. USB entry into ROM and return to stock firmware verified, with unchanged
    presets. PIO NOR reader started, JEDEC `EB6014`, declared capacity 1 MiB.
    Complete backup acquired through two identical 1 MiB reads, with valid
    CRCs and a firmware prefix matching stock 009.
    [MINI_RECOVERY.md](MINI_RECOVERY.md), [MINI_FLASH_BACKUP.md](MINI_FLASH_BACKUP.md).
18. Bootloader handover and XIP variants, clock selector, and OSR64 codec
    candidate reconstructed offline. [MINI_HANDOVER.md](MINI_HANDOVER.md),
    [MINI_CLOCK.md](MINI_CLOCK.md). Physical audio frequency has not been measured.

## Three candidate footswitch inputs

In stock firmware 009, the function at CPU address `0x0200A060` reads
`0x00050004` three times. In header `WL82.h`, `PORTA_BASE=0x50000` and the `IN`
register is at offset 4. The immediately following code extracts:

```c
/* Reconstructed expressions, NOT a validated driver. */
input_0 = (porta_in >> 10) & 1;  /* PA10 candidate */
input_1 = (porta_in << 1) & 2;   /* PA0 candidate  */
input_2 = (porta_in >> 1) & 4;   /* PA3 candidate  */
```

Function `0x02006096` also configures pins 10, 0, and 3 through `0x02006074`
with argument 1 and registers scanning with interval 10. The time unit and
parameter semantics still need verification.

A state machine with three elements and combinations follows. Interpreting
this as scanning the three footswitches is an **inference**. A/B/C assignment,
polarity, pull-ups, LEDs, and debounce timing remain to be confirmed. The
profile does not invent values for these fields.

## Required firmware changes

| Part | Why MINI needs specific work |
|---|---|
| Board support | Three footswitches; physical mapping and LEDs unverified |
| Audio | ALNK0, PA4–PA8, and DMA reconstructed; clocks/codec need adaptation from 44.1 to 48 kHz, mute needs confirmation |
| Linker and memory | MINI linker and probes verified offline; handover, budgets, and physical boot remain to be tested |
| Storage | MINI BTIF occupies the area called OTP in G/B images |
| DSP | Complete three-channel/int32 capture path within the verified domain; frontend, other profiles, IR, and effects remain |
| Clock and performance | 396 MHz in UltraRig metadata does not certify MINI |
| Installation | Identity, JEDEC, and complete backup verified; recovery from corrupted flash and installation still need validation |

The A2L1 format and NAM converter are already available for development, but
this does not make stock MINI firmware capable of running the UltraRig engine.

## Concrete completion sequence

1. Use the verified full backup of the unit to design and test recovery
   independent of the application. Return from RAM to intact stock succeeded;
   erased or corrupted flash has not been restored.
2. Complete GPIO, switches, and mute; verify the reconstructed ALNK path and
   48 kHz clock/codec sequence on the device.
3. Reconstruct the necessary DSP functions or implement them from available
   sources; numerically validate capture results, saturation, and precision.
4. Integrate the already compiled components and probes into a MINI application
   with verified clocks, codec, IRQs, and audio scheduling. Then add the
   capture/IR engine and effects chain; diagnostic ELFs alone are not installable firmware.
5. Measure underruns, latency, RAM, stable clock, power consumption, and boot behavior.
6. Only after these checks, prepare and test installation and restoration.

Device identification and preset reads over BLE succeeded. A new connection
overcame the previous subscription error and returned two identical banks:
1,942 bytes, SHA-256
`c6216783618016998488515ecf4272a78ace8e82ca22e3a27a42bc2d76100427`.
RtMidi still does not expose the MINI; no usable USB interface has been
identified. Full backup and ROM recovery remain to be verified. No HyperRig
code has been executed on the pedal.

```powershell
python -m hyperrig port-status
```
