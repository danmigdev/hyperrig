# HyperRig platform for TANK MINI

Reconstructed drivers are available for the P33 watchdog, whole-line cache
operations, and clock-state reading/decoding. They compile for pi32v2 and are
verified on the host. **They do not initialize the PLL, SFC, or MMU and do not
demonstrate boot on the MINI.** They do not set audio-readiness flags.

Sources are in `firmware/mini/platform/`; `tools/verify_mini_platform.py`
generates `build/mini-platform/hyperrig_mini_platform.pi32v2.o` and the
[mini-platform.json](../research/mini-platform.json) report.

## Evidence and boundaries

The sample is the original `TANK MINI_009` firmware, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Verification reopens the FWSC, checks container CRCs, and compares the extracted
`app.bin` with the copy used for disassembly.

| Observed function | CPU range, end exclusive |
|---|---|
| Watchdog feed and control OR | `0x02000974..0x0200098A` |
| Watchdog control write | `0x02002B88..0x02002B96` |
| Initial watchdog sequence | `0x02002D42..0x02002D6C` |
| P33 single-byte transmission | `0x01C00FC8..0x01C00FE2` |
| P33 write | `0x01C0104E..0x01C0108C` |
| Atomic OR in the P33 domain | `0x01C010B4..0x01C010FE` |
| Cache range flush/invalidate | `0x01C00D80..0x01C00DB2` |
| Global cache maintenance, not ported | `0x01C00DB2..0x01C00E8C` |
| Cache-way configuration at reset | `0x01C00E8C..0x01C00F9C` |
| Inherited clock read/decode | `0x02002D76..0x02002EC8` |
| SFC-protected clock change, in RAM | `0x01C03352..0x01C033EC` |

The report preserves fragment hashes. The new code neither calls stock
function addresses nor accesses locks/globals belonging to its scheduler.

The pinned AC79 SDK reference's
[P33](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/p33.h),
[watchdog](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/wdt.h),
and [cache](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/cache.h)
headers establish names, P33 addresses, and the 32-byte cache line. The actual
sequences come from the MINI bytes. The independent reference
[m-bootloader, SPEC §§2–3](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md)
corroborates several AC791N registers; its FM1/SMK37 tests are not MINI tests.

## Watchdog: separate feed and configuration

The P33 bridge uses word registers `SPI_CON=0x13E08`, `SPI_DAT=0x13E0C`.
With CS active for three bytes, each byte is written to DAT, then control bit 4
is set; this is followed by `csync`, waiting for bit 1 to clear, and reading
DAT. For the P33 addresses used here, control bit 8 stays zero. Write and OR
use command bytes `0x00` and `0x20`, respectively.

`hyperrig_mini_watchdog_feed` sends `20 80 40`: it sets bit 6 of P33 register
`0x80`, as stock does. It preserves the existing timeout and enable state.
It does not enable a disabled watchdog or guarantee a duration for the DSP self-test.

`hyperrig_mini_watchdog_init_stock_4s` reproduces this sequence in order:

| Operation | P33 register | Data |
|---|---:|---:|
| write | `0x80` | `0x00` |
| write | `0x80` | `0x0C` |
| OR | `0x80` | `0x20` |
| OR / feed | `0x80` | `0x40` |
| OR | `0x17` | `0x40` |
| OR / enable | `0x80` | `0x10` |

The SDK header names `0x0C` **WDT_4S**; its timeout has not been measured on
the MINI. P33 `0x17` is `P3_VLD_KEEP`, whose bit 6 is declared `WDT_EXPT_EN`.
The API stops at the first error without continuing the sequence.

The caller must own the bridge, serialize IRQ/other-CPU access, and supply a
nonzero polling limit. CS already active, RTC selection active, or a busy bridge
produce `-3` without writes. The MINI byte driver inherits bridge mode bits;
the independent AC791N reference uses bits 3:2=`11`. The API rejects another
mode (`-4`) without trying to configure it. This check is an added conservative
precondition, not a newly discovered MINI instruction.

A timeout returns `-2`, releases CS, and leaves command completion **uncertain**:
it does not authorize a retry, DMA, or continuation as though feeding succeeded.
The limit counts register reads, not microseconds. The feed loop and its
relationship to maximum DSP time still need to be designed and measured on
the target. A watchdog test in the probe must be an explicit option; it is
not part of the default offline self-test.

## Clocks: preserving flash access

`hyperrig_mini_clock_read_snapshot` reads 17 words: dividers and selectors,
main/secondary PLLs, HUSB, SFC, cache, and SDRAM/PSRAM controls. It writes no
registers. The caller must exclude clock changes during the read; this is not
an atomic hardware capture. Stock reads the SFC BAUD register even though the
SDK header labels it write-only.

`hyperrig_mini_clock_decode` replicates the supported stock arithmetic:

- Nominal oscillator of 40 MHz if bits 27:26 of `0x119A0` equal 2, otherwise
  24 MHz.
- Secondary PLL: divide by `(DIVN+2)` before multiplying by `(FBD+2)`, retaining
  the processor's unsigned32 semantics.
- System selectors 0–4: 192, 137, 320, 480, or 107 MHz, divided through stock
  tables `[1,3,5,7]` and `[1,2,4,8]`.
- Selectors 5–7: derived from the secondary PLL; 8–9: derived from the HUSB
  multiplier. Selectors 10–15 are rejected: the stock nominal 480 MHz fallback
  is not used.
- HSB divides sys by `SYS_DIV[17:16]+1`; LSB divides HSB by `SYS_DIV[10:8]+1`;
  SFC divides HSB by `BAUD+1`.

Fields `sys_hz`, `hsb_hz`, and `lsb_hz` correspond to stock globals
`0x01C1E32C`, `0x01C1E338`, and `0x01C1E334`. They are **calculated nominal
values**, not measurements. `main_selector` separately reports the CPU path
selected in `CLK_CON0`: the stock calculation does not prove that the calculated
source is actually clocking the CPU. These values are not used to attest to
deadlines, codec delays, or PLL lock.

The stock clock-change routine executes from RAM: it waits for cache idle
(`0x01EEE008`, bit 14), waits for SFC not busy (`0x40200`, bit 31), disables
SFC bit 0, applies clocks/dividers and delays, then restores SFC. The SFC timing
field is also recalculated. Transferring only the clock writes into code
executing from flash can remove instruction access. **This transition is
neither ported nor invoked.** The platform preserves inherited SFC, PLL,
dividers, XIP encryption, voltages, and pinmux.

For ALNK, `alnk_mux=0x500` is the observed selection for the 48 kHz family in
`CLK_CON2` bits 11:8, already reconstructed by the audio driver. It does not
establish the source clock or pin frequency. Codec work requires verification
of 12.288 MHz MCLK and 3.072 MHz BCLK for the 48 kHz I2S32 profile, in addition
to 48 kHz LRCLK; codec profile, physical clocks, and analog path must agree
before DMA is enabled. `clock_rate=48000` is not inferred from the mux alone.

## Cache, MMU, and DMA ownership

`hyperrig_mini_cache_range` accepts only 32-byte lines entirely within
`[0x01C00000,0x01C7FD20)`, excluding the reserved boot tail. It does not round
into adjacent allocations. For each line, it waits for idle bit 14, issues
`csync; flush/flushinv; csync`, and waits again. Flush/invalidate follows the
original loop `0x01C00D80`; the clean variant uses the `flush` instruction
observed, among other places, at `0x01C00E1E`. A timeout after one line does
not establish completion of the range and does not set readiness.

The caller must own every line, exclude concurrent writes from both CPUs, and
synchronize the DMA phase. For RX, clean/invalidate before handing the buffer
to DMA; do not write it from the CPU during DMA ownership. A later flush/invalidate
of a dirty, stale CPU line could overwrite newly received RX data. For TX,
publish samples with the appropriate clean before DMA reads them. The API
provides primitives; it does not automatically solve the producer/consumer
protocol or overruns.

The stock cache-reset function frees seven D-cache ways and no I-cache ways,
rewrites way registers, clears internal arrays, and uses `0x01F28000` as extra
RAM. HyperRig does not use that region or copy stock callbacks. The new API
does not change ways or enable bits and does not perform that clearing.

These primitives concern **D-cache**. They do not establish visibility of
`.ramtext` instructions after flash→RAM copying: a verified handover/I-cache
contract is required before executing that code. Stock has a global routine
at `0x01C00DB2` that disables cache and SFC, traverses D-cache tags, and
invalidates I-cache tags at `0x01F08000` by clearing bit 15, then restores
SFC/cache. It has not been ported as a generic primitive, and no separate
range-based I-cache routine with proven prerequisites has been found.

The SDK linker reserves the initial 8192 bytes when `CONFIG_MMU_ENABLE` is
active. Stock MINI instead copies RAM to `0x01C00000`, consistent with the SDK
layout without that reservation. This is layout evidence, **not proof of the
entry MMU state**, DMA mapping/aliases, or actual cache geometry. These matters,
including second-core ownership, remain to be verified.

## Sequence for future integration

1. With IRQs disabled, preserve the boot descriptor; set up stacks, BSS, and
   the RAM copy, including `.ramtext`. The MINI linker already collects the
   section; visibility of copied instructions still needs verification.
2. Build `hyperrig_mini_platform_io` using `target_io`: this function assigns
   callbacks and does not access registers. Preserve inherited SFC/PLL/MMU.
3. Capture the clock/cache snapshot and store it in the diagnostic mailbox,
   without turning nominal frequencies into hardware attestations.
4. Only with verified P33 ownership, apply the selected watchdog policy:
   feed the existing state, or use stock initialization with a periodic feed
   plan. Treat busy/unsupported/timeout outcomes as explicit errors.
5. Prepare buffers and the IRQ/worker protocol. Invoke cache primitives only
   after verifying DMA mapping, alignment, and line ownership.
6. Verify pin clocks, codec profile, mute/analog path, and the IRQ11 wrapper
   before declaring readiness and starting ALNK.

This sequence has not been executed on hardware. State at the probe's C entry,
whether the watchdog is already enabled, PLL lock, and operation durations on
the MINI have not yet been observed.

## Reproducible verification

```powershell
python tools/verify_mini_platform.py
```

It requires the decoded MINI firmware, local ISA, and project-pinned JieLi
toolchain; on Windows it uses WSL Ubuntu. It opens no transport to the pedal.

Verification executes 640 clock-register combinations in the original MINI
instructions, using register values from before the first result in parallel
pairs, and compares the C decoder. It also runs ASan/UBSan over P33 traces,
sequence interruption at each of 18 timeout points, 65 cache timeout points,
buffer boundaries, and absence of writes during the snapshot. The fake bus
is not a physical or timing model of the chip.

The verified target object contains 572 `.text` bytes, 606 `.ramtext` bytes,
and 20 `.rodata` bytes, with no unresolved external symbols. The listing
confirms `flush`, `flushinv`, and RAM placement of critical callbacks. The
report explicitly keeps all hardware attestations false.

Both target platform units are compiled with `-mllvm -pi32v2-large-program`:
calls to symbols resolved at link time use `R_PI32V2_EXTEND_CALL_32M2` instead
of the variant limited to approximately ±4 MiB. This spans flash/RAM boundaries
without thunks or artificial pointers; publishing RAM instructions remains a
prerequisite distinct from linking. In the current platform, boundaries already
use callbacks and local calls remain in the same section: the flag does not
change the verified object's bytes or footprint, but establishes future
compilation behavior.
