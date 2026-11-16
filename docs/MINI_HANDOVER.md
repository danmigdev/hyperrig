# MINI handover and entirely XIP probes

Linker `firmware/mini/handover/mini_xip.ld` produces two diagnostics with
**all instructions in mapped flash**. This removes the need to make newly
copied RAM code visible to the CPU. It configures no cache, MMU, PLL, codec
or peripherals. These are applications entered from the stock bootloader,
not programs to load through the ROM USB ABI.

`python tools/verify_mini_handover.py` rechecks MINI 009 firmware, reconstructs
bootloader fragments, compiles through JieLi/WSL and writes
`research/mini-handover.json`. It opens no devices and produces no update
packages. These ELF files have not been executed on the MINI.

## Evidence in the original bootloader

The `uboot.boot` container is extracted from `flash.bin` in the verified FWSC;
header and payload are decrypted separately with ENC FFFF.
Directory, container and both BANKCB-part CRCs are checked.
The payload is `0x3820` bytes long, loaded at `0x01C02000`, with SHA256
`fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d`.
Header CRC `BCF5`, payload CRC `81A2` and container CRC `71C8` match the
AC791N reference format, but the evidence here uses MINI bytes.

| MINI instructions | Observed effect |
|---|---|
| `0x01C02000..2046` | ROM entry in exception context: saves r0 on the inherited stack, zeros private BSS, `rete=0`, `reti=0x01C02036`, `rti`; then private SSP/SP. |
| `0x01C024E4..2532` | Clears bits 8/9 of `0x01EEE008`, zeros four internal ranges, restores bits 8/9. |
| `0x01C032E4..32F6` | Writes the key to `0x13004` and `0x40304`. |
| `0x01C050C6..51A2` | Disables SPI0, selects SFC, clears/configures SFC and baud, sets the application's physical base. |
| `0x01C051BE` | Calls cache clearing `0x01C024E4` again. |
| `0x01C051C2..51D8` | `cli`, waits for cache bit 14, ENC control `0x40300=1`, cache control OR `0x300`. |
| `0x01C05284..528E` | Loads entry from the descriptor, prepares `r0=0x01C7FE08`, executes `call r1`. |
| `0x0200019E` | After copying RAM, stock application reset calls RAM `0x01C00E8C`. |

The original loop trace verifies exactly 6,402 word stores: two to the
control register and 6,400 to the following areas, zeroing 25,600 bytes:

* `[0x01F00000,0x01F04000)`;
* `[0x01F08000,0x01F0A000)`;
* `[0x01F0A000,0x01F0A200)`;
* `[0x01F0B000,0x01F0B200)`.

The trace proves addresses, order, width and write values with two different
initial control values; it does not simulate the physical cache.
The listing limited to identified fragments is
`build/mini-handover/stock-handover.asm`.

Stock application reset does not explicitly publish instructions between
the RAM copy and that first call. This indicates dependence on the previously
prepared context; it does not establish a general I-cache invalidation
operation or MMU state at every possible entry. HyperRig's `csync` alone
is not presented as such an operation.

## Compiled variants

| ELF in `build/mini-handover/` | Loadable bytes | Functions in XIP | RAM copy |
|---|---:|---:|---:|
| `hyperrig-mini-xip-minimal.elf` | 476 | 7 | 4 data bytes |
| `hyperrig-mini-xip-runtime.elf` | 13,624 | 63 | 4 data bytes |

The runtime variant also moves 234 bytes of the runtime component's
`.ramtext` sections into flash. It includes the simulated-event → worker
→ A2 → TX-conversion path already verified on the host. Ownership callbacks
remain those for private buffers; no real IRQs are registered, DMA is not
started, and ALNK/codec configuration functions are not called.
Hardware platform/codec components are not linked. The old table replay
present in the audio object remains inactive.

The audit requires all executable segments and sections within
`[0x02000120,0x0207E000)`, and all ELF `STT_FUNC` symbols in the same
region. RAM segments are RW. Reset copies no instructions.
Existing ELF constraints, upper RAM reservations and both reset simulations
are retained. The simulations stop before C.

Probe sources are the already verified sources, unchanged:
the report checks their hashes and those of core/audio/runtime objects.
It reports the existing host ASan/UBSan evidence with DSP CRC `f10b5e4c`
and TX CRC `f0a44a06`, without attributing it to execution of the new ELF
on the target.

## Sequence and limits

1. Normal application entry from the stock bootloader is required:
   mapped/decrypted SFC, prepared cache and valid `r0` as described above.
2. HyperRig reset disables IRQs, copies the descriptor before clearing RAM,
   sets private stacks, zeros BSS and copies one data word.
3. The minimal marker writes the mailbox at `0x01C00020` and ends in the
   diagnostic loop with hook status `-100`. The runtime variant uses the
   mailbox at `0x01C35580`, expecting application/audio status `0` and
   the two stated CRCs.
4. SFC, ENC, PLL, cache partition and MMU are unchanged. Stock clock-change
   routine `0x01C03352`, which disables SFC, is incompatible with this XIP
   path and must not be added to the linker for invocation.

Still to be demonstrated on the device: actual entry and a transport to
observe the mailbox, MMU/RAM-alias state, CPU1, watchdog duration, IRQ/DMA
and audio timing. The bootloader clears watchdog enable at the beginning
of initialization; this does not replace measuring probe duration on every
possible path. A ROM USB program must instead preserve the ROM's stack,
return and callbacks and confine memory to its slots: it cannot reuse this
reset, which occupies application RAM.

Software reset is also established on the MINI at `0x01C028F4..28FE`:
`0x10000 |= 0x10`, then a loop. This is not an NVM write.
The RAM marker `usb_update_mode` can change the next boot;
this analysis does not prove that the marker is already cleared at ROM
entry and provides no automatic hardware return procedure.

Independent reference:
[m-bootloader, SPEC §§3.6 and 4.1](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md).
Its test hardware is FM1/SMK37; no physical-boot claim is transferred to the MINI.
