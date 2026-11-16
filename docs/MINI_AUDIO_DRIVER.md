# HyperRig audio component for TANK MINI

`firmware/mini/audio/hyperrig_mini_audio.c` reconstructs the ALNK0 configuration
observed in the stock TANK MINI_009 firmware and provides an adapter between
the two DMA halves and a fixed-point mono engine. It compiles for pi32v2;
**it has not been run on the pedal and does not complete board startup**.
It contains no callback or buffer addresses taken from the TANK-G.

## Evidence and configuration

The FWSC sample has SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
The verifier rechecks the container and compares the decoded data with the
local copy before reading instructions or tables. Hashes of the analyzed
regions are in [mini-audio-driver.json](../research/mini-audio-driver.json).
The register layout is corroborated by the SDK header `WL82.h` pinned in the
lock, without incorporating the proprietary driver.

| Item | Evidence in MINI 009 | Reconstructed value |
|---|---|---|
| Global configuration | `0x02006F70`, table `0x02035E90` | ALNK0, pin group 1, master |
| ALNK0 registers | stock accesses and `WL82.h` | base `0x00012E00`, registers spaced 4 bytes apart |
| CON0 before start | table fields +72/+76/+84 | `0x0180` |
| CON1 after TX0/RX1 | `0x0200708C` | `0x00D5`, two 24-bit channels |
| CON3 | `0x02006E58` | `0x83` at nominal 44100 and 48000 |
| LEN | `0x02007048` | 128, or 1024 bytes per channel |
| DMA addresses | table `0x0203FED8` | ADR0 at `0x12E10`, ADR1 at `0x12E14` |
| Enable | `0x02007146` | CON0 bit 11 |
| Multiplexer | `0x02006FC4` | `0x51030`, bits 6–7 set to 1 |
| Output GPIO | `0x02006E08`, helper `0x02004F86` | PA4–PA7: OUT high, DIR output |
| Input GPIO | `0x02006E12` | PA8: DIR input, DIE=1, PU=1, PD=0 |

PA4–PA6 are the three clocks; PA7 carries TX0 data and PA8 RX1 data. The MINI
table has a different order from the UltraRig driver structure. The component
preserves other GPIO, mux, and clock bits. ALNK accesses use the stock widths:
16 bits for CON0/CON1/LEN, 8 bits for CON2/CON3, and 32 bits for ADR0/ADR1.
Offsets are also checked at compile time.

`prepare()` receives the bus addresses of buffers chosen by the new linker,
requires two distinct word-aligned 1024-byte ranges, and leaves DMA disabled.
It rejects reconfiguration while the start bit is active. GPIO operations are
grouped by register: the static result matches the observed one, but temporal
identity with the stock sequence is not claimed. It requires exclusive
peripheral ownership and disabled IRQs during setup.

## Clock, codec, and startup conditions

The stock setter distinguishes the two clock families through `0x02006E36`:
it preserves all bits of `0x10014` except 8–11, which become `0x0` at 44100
and `0x5` at 48000. At both rates, CON3 retains `0x83` in the MINI master
configuration. The driver reproduces these values; **it does not reconstruct
the preceding PLL configuration or measure the clocks**.

Before ALNK, the stock path calls `0x02006DEC`, which sends 22 4-byte records
from table `0x02035E35` through `0x02006DCE`. The bus address byte is `0x36`;
it is not reinterpreted as a 7-bit address. `hyperrig_mini_codec_replay_stock()`
replays the records to a caller-supplied bus callback and stops at the first
error. The records match the sample byte for byte. No codec-register semantics
are invented.

The replay covers the stock configuration at nominal 44100. It is not a verified
48000 codec sequence. Codec identity, actual clocks, analog mute, levels, timing,
and PA1/PA2 bus configuration remain to be determined. No verification tool
sends the codec script.

`start()` requires a `hyperrig_mini_audio_readiness` structure supplied by board
support, with clock and codec at the requested rate, the IRQ wrapper installed,
coherent DMA memory, and the analog/mute path prepared. The driver checks this
contract but cannot electrically verify what board support reports.
**These prerequisites have not been established on the physical device.**

## IRQ, memory, and deadline

The stock handler `0x01C0374A` uses IRQ 11, priority 6, and checks CON2 bits 4–7.
The just-completed half for channel `c` is `(~(CON0 >> (12+c))) & 1`.
It then acknowledges through a read/OR/write of CON2 bit `c`. The new handler
replicates RX1 selection and acknowledgment of all four channels, but delegates
event queuing to the `ready()` callback.

The hardware wrapper must save and restore pi32v2 interrupt state;
`hyperrig_mini_audio_irq()` is the C body, not a vector the processor can invoke
directly. The IRQ table and installation depend on boot code. The callback must
signal a task; it must not run DSP inside the IRQ.

Each buffer contains 256 32-bit words, split into two halves of 128 words:
64 frames with two slots. The stock task selects both RX/TX halves with
`indice << 9` and invokes the processor with 64 frames (`0x01C03F24`). The new
adapter also uses the same half for RX and TX; phase correspondence must be
verified on the device. At 48 kHz, one half has a budget of approximately
1.333 ms, before allowing for IRQs, scheduling, and cache maintenance.

Buffers aligned to 32 bytes in the new linker's `.dma32` section are recommended.
The need for, and implementation of, flush/invalidate operations or barriers
toward ALNK remain board-support responsibilities: host tests do not establish
DMA coherence. No shared ISR/task queue is implemented; the caller must handle
overwrites, lost notifications, and missed deadlines.

## Sample conversion and engine integration

The three opcodes at `0x01C03A52` load the first slot, shift left by 8 with
32-bit wrapping, then perform an arithmetic right shift by 7. The result is
`sign_extend_24(slot) * 2`: only the low 24 bits are significant.
`hyperrig_mini_audio_stock_rx()` reproduces this operation exactly.

The HyperRig adapter uses a normalized convention: it interprets the 24-bit
sample as Q23, converts it to `model.input_fraction`, converts the output from
`model.output_fraction` to Q23, saturates to 24 bits, and duplicates the mono
sample into both slots. For A2, Q23→Q30 is multiplication by 128; Q31→Q23 is a
right shift by 8. Right shifts round toward negative infinity. The high TX byte
is zero; the useful data is in the low 24 bits.

This scaling and the dual-mono choice are **HyperRig adaptations**. They do not
reproduce the stock firmware's gains, stereo processing, soft mute, or final
LUT and have not been compared with the UltraRig G frontend. No sample-rate
conversion is introduced.

A task can connect the component to the reconstructed engine using this callback:

```c
static int capture_block(void *user, const int32_t *input,
                         int32_t *output, uint32_t frames)
{
    return hyperrig_a2l3_process((hyperrig_a2l3 *)user, input, output, frames);
}

/* After a valid RX event, cache readiness, and a deadline check: */
status = hyperrig_mini_audio_process_half(rx_dma, tx_dma, half,
    model.input_fraction, model.output_fraction, capture_block, &engine);
```

`process_half()` requires approximately 512 bytes of sample scratch space on
the task stack and does not allocate heap memory. Processing errors silence
only the current TX half without altering the other half. The application must
check that the capture sample rate matches the peripheral's actual rate.

## Reproducing the checks

```powershell
python tools/verify_mini_audio.py
```

The command uses WSL Ubuntu/GCC for host checks and the JieLi toolchain already
pinned in the project for `build/mini-audio/hyperrig_mini_audio.pi32v2.o`.
The object uses ELF32 pi32v2 and has no unresolved external functions; it remains
a relocatable component to link into the application. In this build, its `.text`
code occupies 948 bytes, plus an 88-byte codec table in `.rodata`.

Results: 520 comparisons with the original RX fragment, 33,280 normalized
conversions, 12 DMA-half cases, 256 register snapshots, 32 IRQ pending/phase
combinations, and 259 exact-sized-buffer cases under ASan/UBSan. Tests also
verify rejection of invalid addresses/parameters, preservation of other GPIOs,
blocking startup without prerequisites, and codec/DSP error propagation. Tests
write only to host-memory structures: **they do not access the pedal's peripherals
or Bluetooth/USB**.

Host registers do not emulate DMA timing or acknowledgment-bit autoclearing.
Only the three-instruction RX conversion is numerically compared with an
interpreted stock fragment; the complete configuration is a static
reconstruction checked through values and addresses.
