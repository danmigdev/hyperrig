# G → MINI boot contract

The audit identifies a concrete correction to G startup and a standalone OTA
path already present on the MINI. It does not yet prove that the complete G
application boots or that recovery works from a valid image that hangs.
It performs no pedal operations and produces no installable images.

Reproduce from the repository root:

```powershell
python -X utf8 tools/audit_mini_boot_contract.py
```

The command verifies pinned inputs, runs 1344 cases against the original clock
getter, compiles the 28-byte patch with the JieLi assembler, checks 64 cases
of writes staying within bounds, and compares the G/MINI syscfg readers.
Results are in [mini-boot-contract.json](../research/mini-boot-contract.json).
Compilation uses Ubuntu/WSL and the toolchain already pinned in the project.
Neither compilation nor host testing is presented as execution on the MINI.

## Clock and GPIO ABI for the codec

`0x020057C6` is a C getter with no arguments. It returns nominal MHz in `r0`;
it uses `r1`, writes no memory and acquires no lock:

```c
if (*(uint8_t *)(0x01C26890 + 680))
    return *(uint32_t *)0x01C1F1AC;
if ((*(uint32_t *)0x00010014 & 15) != 6)
    return 0;
return (((*(uint32_t *)0x000119AC & 4095) * 4) + 8) / 3;
```

The initial cached value is 396 MHz at LMA `0x0207592C`, but must not be used
as a port constant. Setter `0x020054F0` updates the cache at `0x0200557E` or
`0x0200577C`, calls RAM transition `0x01C0444E` at `0x0200566A`, and enables
the stored result at `0x020057B6`. The getter expresses an integer nominal
value, not a clock measurement.

The codec binding can multiply the result by 1000000 after rejecting zero
and values above 2147, the limit for the signed Hz used by the delay.
The getter does not prevent another task from changing the clock during a
transaction: a stable clock and exclusive ownership of PA1/PA2 remain
separate preconditions.

The G GPIO APIs already used by the binding hold the bank lock at
`0x01C25CE0`. Critical-section entry `0x01C00E2E` disables interrupts and
increments the counter for that core; `0x01C00E46` decrements it and enables
interrupts again when it reaches zero. Do not add the same bank lock around
the APIs: the protocol is not recursive.

## SPL context and extension patch

The MINI passes `r0=0x01C7FE08`. The 24-byte base block is compatible with
the G reader at `0x0200042E`:

| Offset | Preserved field |
|---:|---|
| 0 | Pointer to the decoded flash header |
| 4 | Physical app-area base, `0x4000` |
| 8 | Logical CPU base, `0x02000000` |
| 12 | 16-bit key/chip ID |
| 14 | 16-bit trim |
| 16 | Eight bytes for Bluetooth MAC and CRC |

The G also copies 8 bytes from context+80 to `0x01C7FD74` and 4 bytes from
context+88 to `0x01C7FD7C`. The types correspond to `SDRAM_CFG_INFO` and
`EX_APP_INFO` in the [pinned SDK boot.h](https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/system/boot.h).
The SDK documents sizes and fields; the copy locations are proven by the G bytes.

The MINI declares `ENABLE_SDRAM=0` and a single application area. In its SPL,
`0x01C04F9E..4FCE` skips extension initialization when the optional descriptor
is absent. The base transfer at `0x01C051DA` copies only 24 bytes.
It is therefore incorrect to assume that the additional 12 bytes are zero
because stock MINI firmware does not use them.

The patch replaces G range `[0x0200045C,0x02000478)` with:

```asm
r0 = 0x01c7fd74
r1 = 0
[r0+0] = r1
[r0+4] = r1
[r0+8] = r1
; seven nops to preserve all original addresses
```

It acts only on the G's private copies. It preserves the base block,
`r2..r15`, stack, interrupt state, key, trim and the mailbox beginning at
`0x01C7FD80`. It changes neither the bootloader nor incoming context bytes.
The vendor assembler produces exactly the bytes recorded by the verifier.

API for the integrated formatter:

```python
from tools.audit_mini_boot_contract import boot_patches
patches = boot_patches(g_plain)  # tuple[BinaryPatch, ...], one patch
```

The API requires the plaintext of the entire pinned original G area;
the patch includes the complete preimage. Do not apply it to different or
already modified firmware. Checking the three writes does not establish
the complete hardware handover, cache, IRQs or application stability.

## VM, BTIF, OTP and calibration

The G syscfg reader `0x02024A78..24B10` and MINI reader
`0x02003E3C..3ED2` have the same sequence after explicit normalization of
four addresses and local destinations. No registers, instructions or MMIO
masks are ignored. The special ID102 path verifies the context's MAC carrier
and its CRC before using it.

Backend order is RAM cache, VM, then configuration/BTIF. The VM covers
IDs 1..255. In the real backup, the following records have valid CRCs and
widths matching those requested by both applications:

| ID | Bytes | G request | MINI request |
|---:|---:|---|---|
| 106 | 2 | `0x02024B64` | `0x02023B2E` |
| 107 | 7 | `0x02024CB8` | `0x02023B74` |
| 108 | 20 | `0x02024F14` | `0x02023D6C` |
| 109 | 34 | `0x0205366A` | `0x0206873C` |

G record 106 also starts from hardware fields `0x11930` and applies the VM
value if the read returns two bytes. This reinforces the requirement to
preserve MINI calibration data. ID and width alone do not prove equivalent
meaning for every radio field or all other VM IDs.

The G opens BTIF by name at `0x0201FB00`; its content must remain the MINI's
data at `[0xBE000,0xBF000)`. The optional backend at BTIF+512 finds a zero
length in the backup: G code rejects it at `0x0201FB26` instead of treating
it as a valid table. Records 106..109 already exist in the VM, which precedes
this fallback.

The G partition named OTP would occupy the MINI's BTIF. The candidate uses
the MINI directory and omits it. The G app contains no null-terminated
`OTP` string, but this search does not rule out all computed or indirect
accesses. Directory OTP, SoC efuse and NOR OTP registers are different
objects. The report leaves full verification of OTP consumers open and
does not publish the pedal's MAC/calibration values.

## Recovery without the normal application

The complete backup confirms an updater separate from the MINI app:

| Object | Location | Evidence |
|---|---|---|
| `LOADER.BIN` | `[0xB7000,0xBBDF6)` | 19958 bytes, valid header |
| OTA request record | `0xBCF00`, 80 bytes | Marker `0x5441`, valid CRC16 |
| Record identity | `ota-TANK MINI_007` | Present in the backup, not inferred from the app version |
| Declared decompressed entry | `0x01C0A800` | Payload header |

Excluding the 32-byte outer header, the loader in the backup is identical to
`ota.bin` from the MINI_009 FWSC. Payload SHA256:
`4844e18e5bb70f3ab7d3bfbe26d9f66d3da43e2e181b00f7121218302cda84a0`.
The inner header declares 23324 decompressed bytes; this audit does not run
the decompressor or updater. Sector `0xBC000..0xBD000` also contains its
VM/metadata and must be preserved in full.

SPL at `0x01C03310` checks the application header. Failure can clear the app
base at `0x01C04D68`; before handover, the record scan from `0x01C04E26`
runs in sector steps, reading 80 bytes at sector−256. The backup record passes
those marker/CRC checks and leads to the standalone loader.
This is static evidence of a preserved OTA path, **not physical proof of recovery**.

Branch `0x01C0529A` copies the USB marker to the mailbox and requests reset,
but this is not the only outcome of a damaged app. If it finds no request,
`0x01C05322` clears a field and requests reset without writing that marker.
Therefore, do not claim “invalid header → ROM” as a universal rule.
The original UltraRig installer's bytecode also distinguishes M-VAVE OTA
fallback from the ROM UBOOT disk. Preserving SPL, the OTA area and unit-specific
data remains compatible with complete application replacement: they are boot
and recovery infrastructure, not stock MINI DSP code grafted into the port.

The [official MINI manual](https://manualf.oss-cn-hongkong.aliyuncs.com/manual/Combined-Effect-Pedals/TANK-MINI.pdf)
does not document a power-on button combination for recovery.
A+B and B+C are described for Bluetooth and tuner functions during use.
The SPL profile lacks `PORT_INPUT` and `BOOT_DELAY`.
`RESET=PB01_08_0` is converted into three metadata bytes at
`0x01C03AB6/3AC8/3ADC`: that fragment neither samples the pin nor jumps into
recovery. No footswitch→ROM chain was found in SPL; absence of every mask-ROM
recovery function has not been proven. The [official download](https://www.m-vave.com/download)
offers M-UPGRADE and the MINI FWSC, but does not establish an independent
trigger for a future valid G application that hangs.

## Required trial before installation

The software command that has already put the MINI into ROM requires a working
app. HYE1 RAM tests and the return to stock do not cover a hang of the entire
candidate. OTA's presence is insufficient to reach it if the G header is valid
and the app hangs after the jump.

The primary source [m-bootloader §4.3](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#43-recovery-independent-of-a-valid-boot-image)
documents USB_KEY `0x16EF` on AC791N/SMK-37: a ROM trigger before firmware.
It is not yet proven on the MINI. Before using it as rollback, it must be
tested on the intact MINI, observing ROM identity, a permitted RAM read and
a normal return with data unchanged. Flash corruption is unnecessary for this
initial trigger trial.

An alternative guard at the very first G entry could write
`usb_update_mode` and arm its watchdog, clearing the marker only after a
defined handshake. It is not implemented: SPL disables the WDT, and we cannot
assume a hang causes reset. First, a RAM trial must establish WDT reset with
mailbox retention, and the entry path must be verified. A marker protects only
against failures after it is written, followed by a reset that preserves RAM;
it does not protect against invalid entry/header data or loss of retained RAM.

The remaining concrete actions are therefore to test an independent trigger
on the intact MINI, verify OTA entry separately, and prepare a writer with
sector allowlisting/readback and exact restoration from this backup.
The complete build can progress while these gates remain open.
This audit neither authorizes nor performs an NVM write.
