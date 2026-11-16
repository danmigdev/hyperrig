# RAM codec diagnostic

On November 15, 2026, the MINI ran the `HYC1` diagnostic. Upload and
readback of the 3,376 bytes succeeded; the program completed the first
transaction and restored the PA1/PA2 GPIO bits. The codec returned
**NACK on the first byte, address `0x36`**, while reading register `0x58`.
No value was obtained. The other nine reads were skipped,
without retrying or changing power or clocks.

The [physical observations](../research/mini-codec-hardware.json) retain hashes,
the complete record, GPIO state, and return to stock. The private stack showed
256 modified bytes, with intact guards. The pedal returned to `TANK MINI_009`;
two preset reads matched the previous backup. The diagnostic did not
write the flash.

A NACK in ROM does not identify the component or demonstrate a fault. The
power, reset, and MCLK state in this mode has not been qualified.
The program does not apply the firmware's audio initialization sequence.

## Sources and protocol

```powershell
python -B -X utf8 tools/build_mini_rom_codec.py
python -B -X utf8 -m unittest tests.test_mini_codec_protocol
```

The [builder](../tools/build_mini_rom_codec.py) does not open devices. It builds
the 32 KiB RAM slots at `0x01C20000` and `0x01C28000`. Code and state
occupy 7,704 bytes, including 4 KiB of private stack. The build uses only
four functions from the codec component: bus initialization, the allowlist,
reading, and bounded waiting. Codec register writes and reset are excluded
from the link. The [manifest](../research/mini-rom-codec.json) retains the offline
tests separately from the physical trial.

| Command | IN phase | Effect |
|---|---:|---|
| `FC64` | 16 bytes | `HYC1` identity, version, and slot; no GPIO access |
| `FC65 reg_BE16` | 16 bytes | One read, with PA1/PA2 snapshot and restoration |
| `FD66` | 128 bytes | Record of the last transaction; no new GPIO access |

The CDBs are 16 bytes long with exact `FF` padding. Reads are limited to
`01,03,1C,1D,2B,2C,31,32,58,59`. The selection phase sends only
`36 reg_hi reg_lo`, then a repeated START and `37`; two bytes are then read,
followed by STOP. No configuration data is sent to the codec. Each read
preserves five GPIO registers and restores only bits 1/2, leaving the
other pins in their current state. Waits are bounded to `units × 1024` iterations,
without assigning them a duration in microseconds.

The [probe_mini_codec.py](../tools/probe_mini_codec.py) client verifies the reply,
sequence, register, build tag, CRC, counters, and restoration. A lost
or inconsistent reply invalidates the session and is not retried. A complete
NACK is recorded as such. The `ram-codec` USB profile rejects other
diagnostic commands and has no flash write commands.

The ASan/UBSan tests cover protocol guards, all excluded registers,
NACK at each of the four positions, failed restoration, and reentry during an
operation. The independent bus-transition decoder tests all 65,536 return
values and 221 errors. These checks do not replace an electrical test
or qualify the 48 kHz audio path.

## Second trial: HYC2 and the ROM clock

The separate HYC2 diagnostic also ran on November 15, 2026:
5,856 bytes uploaded and read back, build tag `0x71A0F2B7`. The first snapshot
of the 17 registers is stable, and the 512-byte record passes validation.
The private stack shows 472 modified bytes and intact guards.

The configuration `CLK_CON0=0x1C1`, `CLK_CON2=0x80`,
`PLL_CON0=0x0940022B`, `PLL_CON1=0x3F5030EE` does not satisfy the
PLL reference check based on application boot. HYC2 returns
`gate=4`, `status=-3`; no `FC69` command was sent.
There were no GPIO operations or codec transactions. These values
are observed registers, not a frequency measurement.

Return to MINI_009 and preset equality were verified for the
fifth time. The [HYC2 physical report](../research/mini-codec-board-hardware.json)
retains the record, pinned sources, and logs; the
[offline manifest](../research/mini-rom-codec-board.json) remains separate.
The trial clarifies the ROM context but does not resolve the HYC1 NACK or
qualify audio, codec identity, or booting the complete candidate.

The third trial, HYC3, subsequently accepted the nominal 48 MHz ROM profile but
again received NACK at the first address, with GPIO restored and return
to stock verified. The result and its distinction from complete application
startup are described in [MINI_ROM_CODEC_CLOCK.md](MINI_ROM_CODEC_CLOCK.md).
