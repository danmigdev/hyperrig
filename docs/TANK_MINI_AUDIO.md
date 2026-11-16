# TANK MINI 009 audio path and differences from UltraRig G

Call-chain reconstruction identifies **ALNK0/I²S as the main audio path in
both samples**. Internal ADC/DAC drivers present in MINI firmware are not
sufficient to identify the path actually used. Identification here comes
from initialization, the configuration table, IRQ, callback, and task consuming
the same buffers.

These results are static. No frequencies or voltages were measured, and the
connected pedal's configuration was not changed.

## Reproducing the evidence

```powershell
python tools/map_audio.py
```

The script checks original hashes before decoding, reads tables, and checks
key call destinations using the ISA table. It generates
`analysis/native/audio-map.json`; a copy of the results is versioned in
[audio-map.json](../research/audio-map.json). Cited addresses are CPU addresses.
SDK headers `WL82.h`, `gpio.h`, and `iis.h` are pinned in the lock.

## MINI chain

`0x020071CA` loads the name `usr_audio_task`; `0x020071D4` passes RAM function
`0x01C03F24` to task creation. `0x020071E6` calls initialization `0x0200715C`,
which passes configuration `0x02035E90` to `0x02006F70`. The latter clears/
configures ALNK0, base `0x00012E00`, and registers IRQ 11 with RAM handler
`0x01C0374A`.

The configuration contains four 16-byte channel records followed by common
parameters. The two enabled channels are:

| Field | Channel 0 | Channel 1 |
|---|---|---|
| Reconstructed direction | output | input |
| Direction code | 0 | 1 |
| Buffer | `0x01C1B230` | `0x01C1B630` |
| Callback | null | `0x01C03EEE` |
| Data GPIO | PA7 | PA8 |

Each buffer occupies 1024 bytes. The channel 1 callback saves the ready-half
index and wakes the task with a semaphore. The task selects offsets with
`indice << 9`, clears 512 output bytes, and calls `0x01C03A18` with 64 frames.
This corresponds to two 32-bit slots per frame. At the DSP path's input, a
`word << 8` transformation followed by an arithmetic right shift of 7 is also
observed: the port must respect this packing and scaling.

The GPIO group selected by MINI is index 1 in its own table:
`[4,5,6,7,8,9,10]`, ordered as three clocks and four data signals. G selects
index 0 in its table: `[7,8,9,10,4,5,6]`, ordered as four data signals and three
clocks. Selector numbers therefore **must not be copied between structures**,
even though the result is the same PA4–PA8 pin set for the channels used.
Electrical correspondence on the board still needs measurement.

## Frequency and codec initialization

| Observed parameter | Stock MINI 009 | UltraRig G M5.71 v2 |
|---|---|---|
| Nominal sample rate | 44100, config +92 | 48000, instruction `0x0200514C` |
| ALNK LEN register | 128 | 128 |
| Period processed by task/model | 64 frames | 64 frames for A2-Lite |
| DMA buffer per channel | 1024 bytes | 128 × 8 bytes |
| Input / output channel | 1 / 0 | 1 / 0 |

MINI setter `0x02006E58` contains an explicit branch for 48000. Branch
`0x02006F2E` selects the clock family through `0x02006E36` and updates ALNK
CON3. **This proves that the code exists, not that our unit's codec is already
configured or validated at 48 kHz.** The A2-Lite port will need to reconstruct
the entire clock/codec sequence or include verified sample-rate conversion;
changing only the nominal field is not evidence.

Before the audio task, `0x02006DEC` initializes the bus and sends 22 4-byte
records from table `0x02035E35`. Routine `0x02006DCE` first sends address byte
`0x36`; candidate bus GPIOs are PA1/PA2. The exact codec model has not been
identified. The report preserves the table hash; originals remain in local samples.

## Consequences for HyperRig

The port can retain the 64-frame processing boundary also observed in MINI.
It requires a target-specific ALNK driver and codec configuration, with
management of both buffers and correct sample conversion. The three
reconstructed C kernels are peripheral-independent and can compile for the
same ISA; a complete engine connecting them is still missing.

Analog mute, levels, actual frequencies, startup order, IRQ/task concurrency,
and underrun behavior remain open. No G callback or buffer address is proposed
as a valid address for the new port.
