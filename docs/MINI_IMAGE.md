# TANK MINI image contract

`tools/check_mini_image.py` validates the stock package and ELF files produced
for the MINI offline. Validation checks format, CRCs, addresses and memory
initialization. The report retains `flashable: false` and
`boot_verified_on_device: false`: a consistent ELF does not prove physical
boot, audio availability or device recoverability.

## Verified original package

The pinned source is `artifacts/tank-mini/TANK-MINI.fwsc`, embedded version
`TANK MINI_009`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Checks cover package identity, the AC791N chip, the main `flash.bin`
container CRC, JLFS-area CRCs and application-file CRCs.

| Content | Range/size |
|---|---|
| FWSC package | 557,044 bytes |
| `flash.bin` payload | `[0, 0x82000)`, 532,480 bytes |
| Prefix before the application | `[0, 0x4000)` |
| MINI application area | Physical flash `[0x4000, 0x82000)` |
| Corresponding CPU window | `[0x02000000, 0x0207E000)` |
| `app.bin` start / entry | Area offset `0x120` / CPU `0x02000120` |
| Stock `app.bin` | 511,032 bytes |
| Stock `cfg_tool.bin` | 383 bytes |
| VM | `[0x82000, 0xBE000)` |
| BTIF | `[0xBE000, 0xBF000)` |
| USR | `[0xBF000, 0xFF000)` |

The `flash.bin` payload ends at the start of VM. It contains none of the
unit's VM, BTIF or USR and is not a complete backup.
The candidate key/MAC area `[0xFF000, 0x100000)` is also outside that payload;
flash geometry and individual data still require verification by reading
the device. The report distinguishes this evidence from merely possessing
the manufacturer's file.

Prefix `[0, 0x4000)` is separately identified by hash
`d9f43191777656de01c7bed4f9e9ba2e34e94832c5d2ed02c3fc7ab7a6d9bd67`.
The tool neither generates nor modifies this prefix.
G/B directories have VM at `0x7B000` and BTIF at `0xBD000`:
they are rejected even if the file is extended to the expected MINI size.

Three FWSC auxiliaries (`isd_config.ini`, `script.ver`, `blimit.bin`)
do not match the CRC computed over raw bytes. The pinned package is intact
according to its SHA; these records remain opaque and may use further
encoding. The validator does not present them as corrupt or decoded.
The `ota.bin` record contains the name `usb_hid_ota.bin`:
this is a clue about the update path, not verification of the pedal's HID protocol.

## ELF for the MINI

The contract is shared with [MINI_BOOT.md](MINI_BOOT.md). Requirements are:

- Little-endian ELF32, pi32v2 machine `0xF1`, executable type and entry
  `0x02000120`. A relocatable DSP-only object is rejected.
- Flash segments within `[0x02000120, 0x0207E000)` and RAM segments within
  `[0x01C00000, 0x01C7FD30)`, without overlaps or truncated payloads.
- RAM initialization bytes present in flash and described by copy symbols
  `__ram_start/end` and `__ram_load_start/end`. **Every byte** of the span
  must be covered: increasing both ends without adding payload does not pass.
- Zeroing symbols `__bss_start/end`, preserved memory
  `__noinit_start/end`, and two stacks `__stack_bottom/top`,
  `__ssp_bottom/top`. Every allocated NOBITS section must lie within its
  declared region.
- General region `__ram_region_start/end` and boot reservation
  `__boot_reserved_start/end = [0x01C7FD30, 0x01C80000)`. The latter includes
  the boot context, IRQ-handler table and CPU1 entry slot identified through
  stock analysis.
- No unresolved global or weak symbols, no dynamic interpreter/linker, and
  a `__flash_image_end` consistent with loadable segments.

The first JieLi linker trial produced `p_align = 0x500`, rejected by the
validator. The MINI build now uses `-z max-page-size=0x20` and
`-z common-page-size=0x20`: probe segments satisfy ELF alignment without
postprocessing the file.

## Execution and tests

```powershell
python tools/build_mini_boot.py
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf
python -m unittest tests.test_mini_image -v
```

To retain evidence for both probes together, after building the DSP probe:

```powershell
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf --elf build/mini-boot/hyperrig-mini-dsp-link-probe.elf --report research/mini-image.json
```

The ten tests cover truncated ELF files, incorrect type/CPU/entry,
out-of-bounds ranges, overlaps, unresolved runtime symbols, RAM copies without
source bytes, BSS that cannot be zeroed, overlapping noinit, stock CRCs and
misuse of G/B images. Results for real files, including hashes, segments
and symbols, are in [mini-image.json](../research/mini-image.json).

## Remaining requirements for device boot

The validator checks the file contract; actual bootloader-to-application
handover, clock configuration and device IRQ/audio/DSP integration remain
unproven. The composer described below covers the application area;
update metadata and transport still need separate verification.

Recovered bytecode from the original installer (`parse_identify` in
`recovered/installer/tankg_install.constants.json`) accepts TANK-G/TANK-B
and contains checks specific to their revisions and maps.
Renaming it HyperRig does not introduce MINI support in those paths.
The BLE connection that read `TANK MINI_009` did not verify bootloader entry
or acquire a complete backup. Update transport, per-unit backup and restoration
still require specific device trials.

## Composing the experimental application area

`tools/package_mini_probe.py` composes only physical slice
`[0x4000,0x82000)` from an ELF that passes validation and the MINI 009 package
pinned in the manifest. It contains neither the bootloader nor unit-specific
data and is not an FWSC file. Valid layout does not prove boot or recoverability.

```powershell
python tools/package_mini_probe.py --elf build/mini-boot/hyperrig-mini-bringup-probe.elf --output build/mini-boot/hyperrig-mini-bringup-probe.app-area.bin --report research/mini-package.json
```

ELF-segment bytes are placed at their **flash LMA addresses**, including the
source of initialized RAM data. BSS, the noinit mailbox and stacks are not
serialized. Gaps and the entire replaced portion of the stock executable
are filled with `FF`, so old code is not left behind the new program.

`cfg_tool.bin` stays at original offset `0x7CD58`; its bytes and every MINI
region record are identical to stock. A program overlapping it is rejected.
Only the application file's length/CRC and area CRC change.
The SFC transformation uses the stock package's key, not a key read from
the unit. The report explicitly states this provenance.

The verifier reopens the written file, checks every CRC, compares all segments
with the ELF, and verifies preserved bytes and fills.
Nine additional tests cover LMA addresses, NOBITS, padding, corruption,
configuration overlap (even with formally valid ELF and CRCs), and an altered
executable whose CRCs are still valid.
Results and hashes are in [mini-package.json](../research/mini-package.json).
