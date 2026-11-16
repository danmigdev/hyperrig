# Audio hardware for the complete G → MINI port

The port retains the UltraRig G application's DSP, scheduler, IRQs, and
protocol. Stock MINI firmware is used as a board reference: it is not the final
firmware's backend. The offline audit identifies two sites for adapting G
M5.71 v2 audio startup to the MINI codec. It applies no patches and does not
declare the image ready to flash.

```powershell
python -B -X utf8 tools/audit_mini_audio_port.py
```

[mini-audio-port.json](../research/mini-audio-port.json) preserves hashes of
both original containers, decoded instructions, preimages, and requirements
for each intervention point. Preimages belong to the **decoded** app area:
app-area offset = CPU address − `0x02000000`; `app.bin` offset = CPU −
`0x02000120`; logical flash offset = app-area offset + `0x4000`. These are not
bytes to write directly into encrypted NOR.

## Shared ALNK path

| Field | G and MINI |
|---|---|
| Controller / IRQ | ALNK0 `0x12E00`, IRQ 11 |
| Clock / TX / RX | PA4–PA6 / PA7 channel 0 / PA8 channel 1 |
| Controller format | I²S, 24-bit data in 32-bit slots |
| Buffer per channel / processed half | 1024 bytes / 64 frames |
| LEN / CON0 before enable / active CON1 / CON3 | 128 / `0x180` / `0xD5` / `0x83` |

G uses index 0 of its table at `0x02035360`, ordered data then clocks; MINI
uses index 1 of the table at `0x02035E20`, ordered clocks then data. Both rows
select the same pins: there is no need to replace the G table with the MINI
table or change its index. G register values are derived from configuration
and instructions, not read from the device.

G selects nominal 48000 at `0x02005148..5194`. It enables `PLL_CON1 bit25`
and writes `CLK_CON2 = (old | 0x100) & ~0x200`. MINI's 48000 branch writes
`(old & ~0xF00) | 0x500`. **Both set ALNK0 bits 8/9 identically**. Bits 10/11
belong to ALNK1, which MINI updates together with ALNK0. This difference does
not justify patching the G selector. Field names are in the
[pinned SDK clock_hw.h](https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h),
in `#if 0` declarations corroborated by `iis_set_sample_rate` instructions in
the pinned `cpu.a`. The exact physical frequency still needs measurement;
the nominal family may be approximately 48076.923 Hz, as explained in
[MINI_CLOCK.md](MINI_CLOCK.md).

## Board sequence to adapt

The G preamble at `0x020053A4..53C6` drives PC0, PC1, and PC5 high and PA9 low.
These are four calls to `0x02004998`, with GPIO numbers 32, 33, 37, and 9.
The G resolver table at `0x0203A2A4` confirms PORTA=`0x50000` and
PORTC=`0x50080`. The electrical roles of the three PC pins on MINI are unproven:
copying their writes is not a verified adaptation.

MINI drives PA9 low, waits 100000 iterations of a loop containing `nop`,
initializes the codec and ALNK, waits another 100000 iterations, and drives
PA9 high. PA9's electrical function and the loops' duration in microseconds
remain unknown; the final high transition is nevertheless observable in MINI
code `0x0200723A..7242` and is absent from the analyzed G section.

The MINI codec receives 22 four-byte records from table `0x02035E35`, preceded
by address byte `0x36`. The bus uses PA1=SDA and PA2=SCL; stock also drives high
levels and releases SDA for ACKs. The complete records and table hash are in
the report. The table does not appear in the G image, not even its eight-byte
prefix; this replay is absent from the decoded G audio-startup path. A pattern
search does not prove the absence of every possible other codec path in G firmware.

The register map is compatible with NAU88L21/NAU88L21C; it does not physically
identify the component. Stock replay sets OSR256. The inconsistencies between
datasheet sections already documented in MINI_CLOCK remain: no silent OSR
change is introduced, and clock validity is not inferred from an ACK.

| G site | Preimage in report | Required adaptation |
|---|---:|---|
| `0x020053A4` | 34 bytes | MINI board-initialization hook: PA9 low, bus, and codec records. Also preserve the original `r6=1` assignment. |
| `0x0200541E` | 4 bytes, call to `0x02005194` | Preserve G channel startup; add the final delay and PA9 transition only after successful configuration. |
| `0x02005148` | 76 bytes | Clock inspection site; no automatic patch required for the ALNK0 mux. |

The audit records sites and preimages. The subsequent
[audio_port module](../firmware/mini/audio_port/README.md) produces linked hooks:
2068 XIP bytes at `0x02076AAC`, no new static RAM, and two patches of 34 and
four bytes. A small preamble stub preserves RETS/r4 to also check the post-hook
result; errors jump to `0x02005436` before success flags. The bus uses G getter
`0x020057C6` in MHz with checked conversion, not the old MINI global at `0x01C1E32C`.

Before a bootable candidate is ready, PA1/PA2 ownership across all G tasks,
the GPIO locks to preserve, and the physical MINI panel still need reconstruction.
Logical knob and switch IDs in the app do not identify pins. Actual clocks,
codec configuration, analog mute, and levels also remain to be qualified. This
audit includes no operation on hardware, flash, or pedal configuration.

One conflict is already proven: `0x02015858..158C2` configures PA0..PA3 as
outputs, serializes 29 bits with PA2 clock and inverted PA3 data, then drives
PA0 high and PA1 low. Caller `0x02017568` has preimage `BF EA 76 F1`; the return
value is unused, and the pattern is compared with cache `0x01C1F208`. This G
task would interfere with PA1=SDA/PA2=SCL even after codec initialization. It
must be adapted in the [panel port](MINI_PANEL_PORT.md); filtering app commands
does not prevent these firmware writes.

The [codec diagnostic read](../firmware/mini/codec_probe/README.md) prepares
verification of actual registers without applying audio records. Read fields
can confirm configuration and bus responses, but do not measure clocks or
automatically distinguish NAU88L21 from NAU88L21C.
