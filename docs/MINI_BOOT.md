# HyperRig startup and linker for TANK MINI

**Three verification ELF files for pi32v2** are available, with an entry point,
RAM copy, BSS clearing, and dedicated stacks. The second also links the HyperRig
capture engine, the original A2 capture, and the audio adapter. The third adds
platform, codec, and worker components, with a RAM self-test of the audio path.
They have not been booted on the pedal and are not installable packages.
`research/mini-boot.json` explicitly retains
`boot_validated_on_device=false` and `flashable=false`.

## Contract observed in the stock firmware

Sample: `TANK MINI_009`, FWSC SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
The build rechecks SHA, FWSC/JLFS CRCs, and equality of the decoded `app.bin`.
The report preserves addresses and hashes of original fragments used as evidence.

| Item | Stock evidence |
|---|---|
| Application entry | CPU `0x02000120`, first bytes of `app.bin` |
| Initial CPU0 SP | `0x01C1899C` at `0x02000124` |
| Initial CPU0 SSP | `0x01C1999C` at `0x0200012A` |
| Cleared BSS | `[0x01C0E018, 0x01C1F414)`, loop `0x02000136` |
| RAM copy | flash `0x0206ED20` → RAM `0x01C00000`, `0xE018` bytes |
| Initial heap | `0x01C1F420`, loaded at `0x02040C52` |
| Heap limit | `0x01C7FD30`, comparison at `0x02040C5A` |
| Boot information | fields saved from `0x020001E6` into region `0x01C7FD50` |
| IRQ handler table | `0x01C7FE00`, write at `0x02001786` |
| CPU0/CPU1 IRQ controller | `0x01EEF100` / `0x01EEF300` |
| CPU1 startup slot | `0x01C7FFF8`, written by `0x0204462C` |
| Stock CPU1 entry | `0x020001B8`: USP `0x01C19C9C`, SP `0x01C1AC9C`, RETI `0x01C020AA`, `rti` |

These addresses come from the software sample. They are not measurements of
free RAM or the physical geometry of the connected unit.

The MINI physical application area is `[0x4000, 0x82000)`, corresponding to the
CPU flash range `[0x02000000, 0x0207E000)`. The entry is `0x120` bytes from the
area's start. The first `0x120` bytes belong to the JLFS container, not the ELF
code. VM, BTIF, and USR remain outside the application linker's contract.

Before clearing RAM, stock code preserves these fields from the descriptor in
`r0`: eight bytes from `r0+4` to context+16, the word at `*(r0)+8` to context+24,
the byte at `*(r0)+13` to context+0, four bytes from `r0+12` to context+28, and
eight bytes from `r0+16` to context+32. The new startup preserves the same fields
without assigning unproven meanings. For debugger tests, it also accepts
`r0=0`, skipping the descriptor read.

## New layout and checks

`firmware/mini/boot/mini.ld` uses RAM `[0x01C00000, 0x01C7FD30)` and leaves the
high region `[0x01C7FD30, 0x01C80000)` reserved for boot/IRQ untouched. It does
not incorporate pointers, tasks, heap, or callback tables from the stock application.

- `.text` starts exactly at `0x02000120`.
- `.ram` contains initialized data and any RAM code, with an explicit flash LMA
  and symbols `__ram_load_start/end`, `__ram_start/end`.
- `.bss` is separate from `.noinit`; `.dma` and `.dma32` sections are collected
  with 32-byte alignment. This alignment does not establish DMA/cache coherence.
- The 8 KiB normal stack `[0x01C7CD30, 0x01C7ED30)` and 4 KiB SSP
  `[0x01C7ED30, 0x01C7FD30)` are HyperRig choices. They are not based on measured
  interrupt or engine requirements.
- Linker assertions prevent overlap with the stacks/high reserved area and
  exceeding the MINI flash limit.

By default, the JieLi linker produced `p_align=0x500`, which does not satisfy
the ELF power-of-two constraint. The build explicitly sets
`-z max-page-size=0x20 -z common-page-size=0x20`: segment offsets and VMAs now
respect alignment and pass the independent validator `tools/check_mini_image.py`.
BSS/stack segments with `p_filesz=0` are not interpreted as flash data.

`startup.S` keeps IRQs disabled, sets both stacks, saves the boot context,
clears BSS, copies `.ram`, executes `csync`, and enters the C function. The
software loops also handle zero-length sections without depending on `REP 0`
semantics.

The limited simulation decodes **the instructions of the newly linked ELF**,
initializes RAM with a pattern, and compares the entire final RAM area with
the ELF contract. It checks copying, BSS clearing, preservation of boot fields,
unaffected regions, SP, SSP, and disabled IRQs. It tests both a valid descriptor
and a null descriptor. It stops before the C entry: it neither executes nor
simulates the boot ROM, peripherals, or target DSP engine.

## C probe and capture engine

The minimal probe writes `hyperrig_mini_probe` in `.noinit`: magic, phase,
context address, and results of checks on an initialized word and a BSS word.
Without an additional application, it reports status `-100` and remains in a
loop with IRQs disabled. The marker is intended for a possible debugger; it
is not an indication visible through LEDs, USB, or Bluetooth.

With `--dsp`, the reconstructed engine, A2 capture, audio driver, and local
freestanding `memcpy`/`memset` implementations are added. No unresolved symbols
remain. The probe reserves 16 KiB for the model and 192 KiB for the runtime
arena, and checks the required sizes before initialization. These are reserved
test capacities, not measured minimum requirements.

The self-test is prepared to process 64 zeros after reset and compare the
little-endian output CRC32 with `f10b5e4c`. The expected result comes from
interpreting the original G kernels, not from the HyperRig C code. If the code
is executed, the mailbox will preserve the CRC, processed frames, and status;
`-104` would indicate a failed comparison.

The probe then clears engine state and calls `hyperrig_mini_audio_process_half`
on two dummy 1024-byte RAM arrays, aligned to 32 and collected in `.dma32`.
The callback runs the engine with Q30 input and Q31 output. It verifies CRC
`f0a44a06` over the first half's 128 TX slots, in low24 format duplicated into
both channels, and checks that the second half retains its initial pattern.
It does not call `prepare`, `start`, the codec, IRQs, or MMIO. The mailbox adds
`audio_status`, `audio_frames`, and `tx_checksum`; `-105` indicates a different
TX CRC, `-106` a write to the other half, and `-107` that the audio test was not reached.

The same `hyperrig_mini_application_probe` was **executed on a Linux host under
ASan/UBSan** through `probe_host.c`, with the capture, engine, and adapter:
status zero, 64 frames for each test, and the two expected CRCs. The host harness
replaces only the mailbox definition and excludes boot main and pi32v2 startup.
The target simulation stops before the C entry; **the target C self-test has
not been executed on the MINI**.

In the verified build, the DSP probe comprises 11,984 bytes loaded from flash
(capture included), 216,768 BSS bytes, 52 `.noinit` bytes, four initialized-data
bytes, and 12 KiB of reserved stacks. Space remains in the layout, but latency,
actual stack usage, and target behavior have not been measured.

## Integrated audio-worker probe

`--bringup` adds a third ELF, `hyperrig-mini-bringup-probe.elf`, linking the
IRQ/worker runtime, platform, and codec. Its self-test uses the same zero input
and CRCs as the DSP probe, routing the audio test through
`hyperrig_mini_runtime_ready` and `hyperrig_mini_runtime_work`. The A2 engine
runs in the worker; the simulated event does not enter the IRQ11 hardware wrapper.

`runtime_probe.c` supplies controlled callbacks for exclusion, buffer ownership,
and synchronization of **private RAM arrays without a DMA peripheral**. It
verifies one event, one completed block, two RX/TX transactions, balanced
callbacks, and no pending work. Those callbacks are not a solution for real
DMA coherence and cannot be used to enable it.

This C application also runs on the host under ASan/UBSan. Its expected TX CRC
remains `f0a44a06`; the result and host executable hash are in the report.
Platform and codec objects are linked, but none of their MMIO operations are
called. The probe does not initialize the PLL, watchdog, codec, or analog path.

The build rejects sources or objects that differ from the component reports'
hashes, preventing an updated host test from accompanying stale target code.
Units crossing the flash/RAM boundary use `-mllvm -pi32v2-large-program`:
the toolchain's ordinary call does not always span the distance between
`0x0200....` and `0x01C0....`. Extended `call.xl` calls resolve the link without
arbitrarily relocating RAM or stacks.

The new ELF contains `.ramtext` functions copied by startup. The simulation
verifies the copied bytes but does not establish visibility of the new
instructions to the processor caches. Cache/MMU handover and execution from
RAM must be verified before treating this program as bootable on the MINI.

## IRQ and cache: reconstructed behavior

`irq.c` exposes registration and removal only for physical IRQs 0–65. The code
comes from `0x02001756` and removal at `0x020148B4`: handlers in the high table,
controller word `index>>3`, nibble `(index&7)*4`, value `(priority<<1)|1`. It
preserves ICFG on completion, removes any previous routes on both CPUs, and
requires external serialization between CPUs. The probe does not call these
hooks or enable interrupts. Number 126 is not exposed: the corresponding table
word coincides with the observed CPU1 startup slot.

The [SFC linker from the pinned AC79 SDK reference](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/cpu/wl82/sdk_ld_sfc.c)
confirms the RAM/boot-info separation and the use of cache ways as additional
RAM. In particular, `0x01F28000` is `.cache_ram_data`, not the IRQ table. Stock
reset configures seven free D-cache ways and copies 32 bytes containing SDK
callbacks there. HyperRig does not use that region or copy those pointers.
The [SDK IRQ contract](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/hwi.h)
confirms ALNK at index 11; hardware handlers require the pi32v2 compiler's
interrupt ABI, not an ordinary C function.

Boot ROM handover, cache/MMU state, watchdog, clocks, GPIO/codec/mute drivers,
DMA coherence, actual IRQ handling, and installation/restoration on the
individual unit remain to be verified. The new startup does not clone the
stock scheduler or second-core startup and does not claim to replace them.

## Reproduction

```powershell
python tools/build_native.py
python tools/verify_mini_audio.py
python tools/build_mini_boot.py --dsp
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf --elf build/mini-boot/hyperrig-mini-dsp-link-probe.elf
```

For the third probe:

```powershell
python tools/verify_mini_platform.py
python tools/verify_mini_codec.py
python tools/verify_mini_runtime.py
python tools/build_mini_boot.py --bringup
```

WSL Ubuntu, the JieLi toolchain already pinned by bootstrap, decoded firmware,
and the local ISA table are required. Artifacts are in `build/mini-boot/`;
the versioned report is [mini-boot.json](../research/mini-boot.json). The commands
do not open transports to the pedal or generate FWSC files or ready-to-flash images.
