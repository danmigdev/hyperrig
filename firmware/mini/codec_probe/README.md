# MINI codec diagnostic reads

`read16.c` adds bounded reads to the reconstructed bus. It sends no values
to codec registers: the write phase contains only the device and register
addresses. The caller owns PA1/PA2, configures the bus, and provides callbacks
with bounded duration. MCLK, ALNK, reset, and mute are not changed.

```powershell
python -B -X utf8 firmware/mini/codec_probe/verify.py
```

This produces `build/mini-codec-probe/read16.pi32v2.o` and `manifest.json`.
The host decoder observes GPIO edges, transmitted bytes, two STARTs,
four slave ACKs, two received bytes, master ACK/NACK, and STOP. It verifies
all 65536 possible values under ASan/UBSan, every allowlisted register,
and every possible timing/read error in the transaction. These are software
tests; they do not simulate voltages, electrical delays, or the physical component.

The allowlist includes `01,03,1C,1D,2B,2C,31,32,58,59`. The protocol is
`START 36 reg_hi reg_lo repeated-START 37 data_hi ACK data_lo NACK STOP`,
most significant byte first. The value is published only after two complete
bytes and successful STOP; it remains unchanged on error. The result
retains the primary error, cleanup error, ACK count, bytes, and samples.
SDA remains released after the read-address ACK and during the final NACK.
There are no retries or loops waiting for the codec; there are at most
20 SDA reads and 193 delay callbacks. A callback that does not return remains
the caller's responsibility. Cleanup after an error is an attempt, not proof
of an electrical STOP.

The sequence is documented by Nuvoton,
[NAU88L21 rev.3.1, §7.4 page 35](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.1.pdf).
The [NAU88L21C rev.1.6 datasheet, page 69](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.6.pdf)
defines `0x58` as read-only ID/status and `0x59` as read-only RAM/mute status.
The component does not access IRQ-clear, fuse, OTP, or test registers.
The software-ID constant `00` appears in both L21 and L21C documentation:
it is not used to distinguish them.
The [Nuvoton/Linux v6.12 driver](https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.h)
confirms KEYDET bit 7, MICDET bit 6, and software-ID bits 1:0 for `0x58`.
These are documentary sources; the verifier neither downloads nor requires the PDFs.

A NACK in ROM **does not prove the absence of the codec**: power, reset,
and MCLK are inherited. Reading clock fields neither measures MCLK/BCLK/LRCK
nor verifies 48 kHz. The component contains no USB/ROM plugin; the wrapper
must handle snapshots and restoration of only the GPIOs it owns and retain
raw values and errors. These tests claim no physical identity or audio test.
