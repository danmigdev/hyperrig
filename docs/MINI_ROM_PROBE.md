# HyperRig ROM probe on TANK MINI

On **15 November 2026**, TANK MINI executed the HyperRig probe from RAM
through the AC791N ROM. The image was read back and verified before jumping;
the plugin returned a 64-byte record with **8 successful DSP cases** and CRCs
matching results obtained by interpreting the original TANK-G kernels.

Physical evidence is summarised in
[mini-hardware-rom.json](../research/mini-hardware-rom.json). The original local
record is `analysis/hardware/mini-ram-bundle-run.json`, fields `probe_session`
and `probe_record`, session started at `17:20:43 UTC`. This test covers
the RAM plugin, return to ROM, and its USB commands. It does not validate
application boot from flash, the complete A2 engine, or audio input/output.
NOR backup and return to stock firmware have separate evidence and are not
attested by this document.

## Build and executed image

Sources are in [firmware/mini/rom_probe](../firmware/mini/rom_probe/).
The following command builds and checks artifacts offline; it does not open
the pedal:

```powershell
python -B -X utf8 tools/build_mini_rom_probe.py
```

The [build manifest](../research/mini-rom-probe.json) preserves source hashes,
golden values derived from original instructions, and host results:
33 protocol cases, 8 DSP cases, ASan, and UBSan. Its
`hardware_execution_verified=false` fields describe the builder's scope and
remain separate from the report of the subsequent physical test.

| Executed build property | Value |
|---|---|
| Flat file | `build/mini-rom/hyperrig-rom-probe-01c20000.bin` |
| Entry and slot start | `0x01C20000` |
| Exclusive slot end | `0x01C28000` |
| Uploaded payload | 4928 bytes |
| Usage with BSS | 6672 bytes, up to but excluding `0x01C21A10` |
| Record | `0x01C219D0`, 64 bytes |
| Internal build tag | `0x498A1779` |
| Payload and ROM-readback SHA-256 | `2f72aa15c30b99a1034ab027d9c92fae369a7dcd4db787e33c9f05360d7e2189` |
| ELF SHA-256 | `f86d34f7b8f66f4aeb69a80e5ae8203e410d59c0292a8431ac9ba06af883c4e8` |
| SHA-256 of manifest used in the session | `640e931497bd309ffda1cba2ea057139867abfe08c7bad58df9f9b609a864817` |

The builder also produces an image for slot `0x01C28000`. The physical probe
result documented here concerns only slot `0x01C20000`.

## ABI and callback lifetime

ROM calls the payload's first byte as a normal C function.
`r0` points to three 32-bit words: send callback, receive callback, and the
address of the ROM variable containing the handler pointer. The probe copies
the send callback by value, clears its own state, runs the selftest, publishes
the handler with `csync`, and returns zero to ROM. It does not retain the
temporary pointer to the services structure or change the ROM stack,
interrupt state, or clocks.

The handler receives a 31-byte CBW and a writable 16-byte response buffer.
It returns 1 for handled commands and 0 to leave them to ROM. Command `FC60`
reruns the selftest and sends an `HYR1` response; `FD61` reads only the
plugin's slot, using the ROM callback in chunks of at most 512 bytes.
The probe does not initialise SPI and contains no flash-write operations.
Transfer framing and transformation are described in
[MINI_RECOVERY.md](MINI_RECOVERY.md).

In the physical test, the jump response was
`fb080000000000000000000000000000`; the `FC60` response was
`fc600000000848595231000000000001`: eight cases, zero status, version one.
The subsequent record confirms execution of the primitives on the processor.
The test determines neither the ROM callback's error-return semantics nor
behaviour under partial transfers.

## Record verified on the pedal

All record words are little endian; markers are ASCII bytes.

| Offset | Size | Field | Observed value |
|---:|---:|---|---|
| 0 | 4 | Magic | `HYR1` |
| 4 | 4 | Version | 1 |
| 8 | 4 | Slot base | `0x01C20000` |
| 12 | 4 | Slot size | 32768 |
| 16 | 4 | Selftest runs | 2 |
| 20 | 4 | Errors | 0 |
| 24 | 4 | DSP cases | 8 |
| 28 | 4 | dot CRC32 | `D4B493B4` |
| 32 | 4 | head CRC32 | `53F332DC` |
| 36 | 4 | rechannel CRC32 | `1910AD87` |
| 40 | 4 | Record address | `0x01C219D0` |
| 44 | 4 | Record size | 64 |
| 48 | 4 | Build tag | `498A1779` |
| 52 | 4 | Audio/SPI/clock peripheral actions | 0 |
| 56 | 4 | CRC32 of bytes `[0,56)` | `E9AEFBA2` |
| 60 | 4 | Completion | `DONE` |

The two runs are the selftest during initialisation and the one requested by
`FC60`: they do not indicate two firmware boots. The host verified every
field, the record CRC, and all three DSP CRCs against the manifest.

SHA-256 of the 64 received bytes:
`7d66f4cc58ba174919f493ab505af478932a12a4706a5cc4288a65e0dd7de585`.

## Scope of the result

The cases exercise six vectors for 16/32-bit dot products, one for the
three-channel head with a ring buffer, and one for three-channel expansion.
Golden values come from the original-instruction interpreter, not HyperRig C
output on the PC. The physical comparison therefore verifies these primitives,
compiler-generated code, and the probe's communication path.

Loading and processing of a complete A2 model, streaming in 64-sample blocks,
ALNK/I2S, audio DMA, codec, and mute were not executed. Audio-clock, latency,
and signal-quality measurements are also missing. Clock work is documented
in [MINI_CLOCK.md](MINI_CLOCK.md); this test does not change its measurement
requirements.

## Next step and memory

The original 23-layer A2 capture does not fit in 32768-byte ROM slots.
Existing ELF `build/mini-boot/hyperrig-mini-dsp-link-probe.elf` contains
11980 bytes of code and constants, including the 4892-byte capture, plus
216768 bytes of BSS, 52 record bytes, and 12288 bytes reserved for stacks.
The [DSP probe](../firmware/mini/boot/dsp_probe.c) arenas are oversized;
reducing them is insufficient. The pi32v2 layouts of
[hyperrig_a2l.c](../firmware/src/hyperrig_a2l.c) and
[hyperrig_engine.c](../firmware/src/hyperrig_engine.c) give:

| Data, in bytes | Original A2 | Synthetic 3-layer fixture |
|---|---:|---:|
| Serialised capture | 4892 | 728 |
| Model arena, result of `hyperrig_a2l_size()` | 6503 | 895 |
| Engine arena, result of `hyperrig_a2l3_size()` | 115111 | 9135 |
| Sum of both queries | 121614 | 10030 |

Each query includes 7 bytes for possible initial alignment; already aligned
A2 arenas use 6496 and 115104 bytes. Input histories for the 23 layers alone
occupy 111300 bytes. These numbers are derived offline from target layout,
not read from the pedal; contexts add 84 bytes for the model and 1096 for
the engine.

The reduced candidate is `synthetic()` in
[verify_engine_native.py](../tools/verify_engine_native.py): kernels/dilations
`1/1`, `6/3`, `15/7`, a four-tap head, and a receptive field of 117 samples.
It traverses loading, rechannel, convolutions, activation, mix, residuals,
sum, and head. The host verifier compares it with original instructions on
six blocks of `1, 63, 64, 7, 31, 64` samples; it also checks reset and block
repartitioning. A new plugin requires pinned fixture bytes and their golden
values: the generator receives RNG state.

With the existing plugin, added layer/engine objects, and their buffers,
the preliminary budget is 21118 bytes before the new wrapper, alignments,
and stack. This is not the size of an already linked new ELF.
Existing assembly shows 1228 bytes of stack for the engine's internal
initialisation chain; callers, ROM, and interrupts must be added.
The plugin inherits the ROM stack, whose remaining capacity has not yet been
established. The reduced fixture is not the original A2 capture and does not
demonstrate its complete execution, real timing, or audio.
